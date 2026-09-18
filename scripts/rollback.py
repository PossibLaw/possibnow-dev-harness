#!/usr/bin/env python3
"""Remove only unchanged files created by one conservative harness installation."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

try:
    from harness_io import safe_path, sha
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'packs/project/.agent/integrations'))
    from harness_io import safe_path, sha


def rollback(root, receipt_path):
    root = Path(root).resolve()
    receipt_path = Path(receipt_path).absolute()
    rel = receipt_path.relative_to(root)
    safe_path(root, rel)
    receipt = json.loads(receipt_path.read_text())
    if receipt.get('schema') != 1 or rel.as_posix() != f".harness/releases/{receipt['version']}/INSTALL.json":
        raise ValueError('unsupported receipt')
    paths = []
    expected = {}
    for relative, digest in receipt['created'].items():
        if not (relative in ('AGENTS.md', 'CLAUDE.md') or relative.startswith(('docs/', '.agent/', '.agents/skills/', '.claude/skills/', '.harness/releases/'))):
            raise ValueError(f'non-harness path in receipt: {relative}')
        p = safe_path(root, relative)
        if p.exists() and (not p.is_file() or sha(p.read_bytes()) != digest):
            raise ValueError(f'changed since installation: {relative}; preserve/reconcile it before rollback')
        paths.append(p)
        expected[p] = digest
    # Check everything first; a conflicting file means no deletes.
    for p in paths:
        if p.exists():
            safe_path(root, p.relative_to(root))
            if sha(p.read_bytes()) != expected[p]:
                raise ValueError(f'changed during rollback: {p}; remaining files retained')
            p.unlink()
    receipt_path.unlink()
    for parent in sorted({q for p in paths + [receipt_path] for q in p.parents if q != root and root in q.parents}, key=lambda p: len(p.parts), reverse=True):
        try:
            parent.rmdir()
        except OSError:
            pass  # Keep all directories containing unrelated files.
    print('ROLLED BACK: removed unchanged files from this receipt; pre-existing files preserved')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', type=Path)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    try:
        rollback(args.target, args.receipt)
    except (ValueError, OSError, KeyError) as exc:
        print(f'BLOCKED: {exc}', file=sys.stderr)
        sys.exit(1)
