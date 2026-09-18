#!/usr/bin/env python3
"""Conservative file installation: create missing files; propose all differing files."""
import json
import os
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'packs/project/.agent/integrations'))
from harness_io import create_file, read_optional, safe_path, sha
from entry_policy import validate, physical_lines

STATE = {'PLAN.md', 'TEST.md', 'REVIEW.md', 'HANDOFF.md', 'HISTORY.md', 'WIKI.md', 'LEARNINGS.md'}


def payload():
    files = {str(p.relative_to(ROOT / 'packs/project')): p.read_bytes()
             for p in (ROOT / 'packs/project').rglob('*')
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    for p in sorted((ROOT / 'skills').glob('*/SKILL.md')):
        for host in ('.claude', '.agents'):
            files[f'{host}/skills/{p.parent.name}/SKILL.md'] = p.read_bytes()
    for name in ('scale', 'guardrails', 'optimize'):
        rel = f'.agents/skills/possibnow-{name}/SKILL.md'
        files[rel] = (ROOT / rel).read_bytes()
    keys = ['PROJECT_NAME', 'TEAM_OR_OWNER', 'PRIMARY_COMMAND', 'TEST_COMMAND',
            'LINT_COMMAND', 'TYPECHECK_COMMAND', 'BUILD_COMMAND']
    for rel in ('AGENTS.md', 'CLAUDE.md', '.agent/TEST.md'):
        for key in keys:
            files[rel] = files[rel].replace(f'<{key}>'.encode(), os.environ.get(key, 'UNCONFIRMED').encode())
    for rel in ('AGENTS.md', 'CLAUDE.md'):
        validate(files[rel], rel)
    return files


def install(target, dry_run=False):
    target = Path(target).resolve()
    version = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())['version']
    base = f'.harness/releases/{version}'
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = bool(subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--', 'packs', 'scripts', 'skills', '.agents', '.claude-plugin']).strip())
    files = payload()
    # A release snapshot keeps current policy reachable even if customized routes remain old.
    def candidate_path(rel):
        suffix = '.candidate' if Path(rel).name in ('AGENTS.md', 'CLAUDE.md', 'SKILL.md') else ''
        return f'{base}/{rel}{suffix}'
    bundled = {candidate_path(rel): data for rel, data in files.items()}
    for name in ('rollback.py', 'entry_policy.py'):
        bundled[f'{base}/tools/{name}'] = (ROOT / 'scripts' / name).read_bytes()
    bundled[f'{base}/tools/harness_io.py'] = (ROOT / 'packs/project/.agent/integrations/harness_io.py').read_bytes()
    bundled[f'{base}/VERSION.json'] = (json.dumps({'version': version, 'commit': commit, 'source_dirty': dirty}, sort_keys=True) + '\n').encode()
    planned = {}
    pending = []
    observed = {}
    # Preflight every destination, including nested symlinks, before making directories.
    for rel, data in {**files, **bundled}.items():
        p = safe_path(target, rel)
        if p.exists() and not p.is_file():
            raise ValueError(f'not a regular file: {p}')
        old = read_optional(p)
        observed[rel] = old
        if old is None:
            planned[rel] = data
        elif old != data:
            if rel in bundled:
                raise ValueError(f'release snapshot differs: {rel}; preserve it and reconcile before updating')
            if not (rel.startswith('.agent/') and Path(rel).name in STATE):
                item = {'path': rel, 'expected_sha256': sha(old), 'candidate': candidate_path(rel),
                        'candidate_sha256': sha(data),
                        'action': 'Review and merge project-specific policy; never replace wholesale'}
                if rel in ('AGENTS.md', 'CLAUDE.md'):
                    item['existing_lines'] = physical_lines(old)
                pending.append(item)
    receipt_rel = f'{base}/INSTALL.json'
    receipt_path = safe_path(target, receipt_rel)
    old_receipt = read_optional(receipt_path)
    if old_receipt is not None and planned:
        raise ValueError('partial/changed same-version installation; use its receipt to reconcile or rollback first')
    ignored = []
    for rel in files:
        if rel.startswith('.agent/') or rel.startswith('.harness/'):
            result = subprocess.run(['git', '-C', str(target), 'check-ignore', '-q', rel], capture_output=True)
            if result.returncode == 0:
                ignored.append(rel)
    for rel in bundled:
        if subprocess.run(['git', '-C', str(target), 'check-ignore', '-q', rel], capture_output=True).returncode == 0:
            ignored.append(rel)
    receipt = {'schema': 1, 'version': version, 'commit': commit,
               'created': {rel: sha(data) for rel, data in sorted(planned.items())},
               'pending': pending, 'ignored': sorted(ignored)}
    print(f'Harness {version}; source commit {commit}; source_dirty={str(dirty).lower()}')
    for item in pending:
        size = f" ({item['existing_lines']} physical lines)" if 'existing_lines' in item else ''
        print(f"PENDING: preserve {item['path']}{size}; compare with {item['candidate']}")
    for rel in ignored:
        print(f'PENDING: shared harness/continuity file is ignored: {rel}; review the ignore rule')
    print(f'Current optimization policy: {base}/docs/workflows/optimization.md')
    print(f'Installation receipt: {receipt_rel}; downloading is not completing pending migration.')
    if dry_run:
        print(f'DRY_RUN: {len(planned)} missing files would be created; no target writes')
        return
    # Recheck the entire plan before writes. Exclusive creation also catches new competing files.
    for rel, before in observed.items():
        if read_optional(safe_path(target, rel)) != before:
            raise ValueError(f'changed during installation: {rel}')
    created = []
    try:
        for rel, data in planned.items():
            p = safe_path(target, rel)
            create_file(p, data, mode=0o755 if rel.endswith('.sh') else 0o644)
            created.append((p, data))
        if old_receipt is None:
            data = (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode()
            create_file(receipt_path, data)
    except (OSError, ValueError):
        # Clean up only our new files if unchanged; never revert another writer's content.
        for p, data in reversed(created):
            if not p.is_symlink() and p.is_file() and p.read_bytes() == data:
                p.unlink()
        raise
    print(f'INSTALLED: {len(planned)} new files; {len(pending)} migrations pending; existing files preserved')


if __name__ == '__main__':
    try:
        install(sys.argv[1], os.environ.get('DRY_RUN') == '1')
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'BLOCKED: {exc}', file=sys.stderr)
        sys.exit(1)
