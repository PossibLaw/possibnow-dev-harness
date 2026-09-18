from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]


def run(target, *args):
    return subprocess.run(['bash', str(ROOT / 'scripts/install-project.sh'), str(target), *args], capture_output=True, text=True)


def snapshot(target):
    return {str(p.relative_to(target)): p.read_bytes() for p in target.rglob('*') if p.is_file()}


def test_customized_update_is_preserved_and_proposed(tmp_path):
    originals = {
        'AGENTS.md': b'# My project\r\nContent edits: read editorial/ROUTES.md\r\nTest: make special\r\nNever publish drafts.\r\n',
        'CLAUDE.md': b'custom instructions\n' * 151,
        'docs/workflows/optimization.md': b'custom older optimization route\n',
        '.agent/HANDOFF.md': b'old unresolved task\nSTOP marker\nolder active constraint',
        '.agent/HISTORY.md': b'legacy history\r\n',
        '.agent/PLAN.md': b'Learning Mode: APPLY\nwork in progress',
        '.agent/CONTENT-PLAN.md': b'active publication constraint',
        '.agent/LEARNINGS.md': b'OFF: keep these lessons unchanged',
        '.codex/config.toml': b'model = "keep-current"\n',
        '.claude/settings.json': b'{}\n',
        'unrelated.txt': b'uncommitted edit',
    }
    for rel, data in originals.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    result = run(tmp_path, '--adopt')
    assert result.returncode == 0, result.stdout + result.stderr
    for rel, data in originals.items():
        assert (tmp_path / rel).read_bytes() == data
    assert 'PENDING' in result.stdout and '151' in result.stdout
    policy = tmp_path / '.harness/releases/4.2.1/docs/workflows/optimization.md'
    assert policy.exists()
    receipt = json.loads((policy.parents[2] / 'INSTALL.json').read_text())
    assert receipt['version'] == '4.2.1'
    assert 'AGENTS.md' in {x['path'] for x in receipt['pending']}
    before = snapshot(tmp_path)
    assert run(tmp_path, '--adopt').returncode == 0
    assert snapshot(tmp_path) == before


def test_update_dry_run_and_repeat_are_read_only(tmp_path):
    (tmp_path / 'AGENTS.md').write_text('custom\n')
    before = snapshot(tmp_path)
    assert run(tmp_path, '--dry-run').returncode == 0
    assert snapshot(tmp_path) == before
    assert run(tmp_path).returncode == 0
    before = snapshot(tmp_path)
    assert run(tmp_path).returncode == 0
    assert snapshot(tmp_path) == before


def test_new_install_roots_and_routes(tmp_path):
    result = run(tmp_path, '--name', 'Fixture', '--test', 'make test')
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / '.agent/integrations/run-checkpoint.sh').stat().st_mode & 0o100
    for name in ['AGENTS.md', 'CLAUDE.md']:
        text = (tmp_path / name).read_text()
        assert len(text.splitlines()) <= 150
        assert 'Fixture' in text and 'make test' in text
        for doc in ['delivery', 'contracts', 'learning', 'content', 'optimization', 'clients']:
            assert f'docs/workflows/{doc}.md' in text
            assert (tmp_path / f'docs/workflows/{doc}.md').is_file()


def test_render_over_limit_fails_before_any_write(tmp_path):
    result = run(tmp_path, '--name', 'x\n' * 151)
    assert result.returncode != 0
    assert snapshot(tmp_path) == {}


def test_nested_symlink_is_rejected_before_any_write(tmp_path):
    target = tmp_path / 'target'
    target.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (target / 'docs').mkdir()
    (target / 'docs/workflows').symlink_to(outside, target_is_directory=True)
    before = snapshot(target)
    result = run(target)
    assert result.returncode != 0
    assert snapshot(target) == before
    assert list(outside.iterdir()) == []


def test_rollback_preserves_existing_and_refuses_intervening_edits(tmp_path):
    (tmp_path / 'AGENTS.md').write_text('custom root\n')
    assert run(tmp_path).returncode == 0
    tool = tmp_path / '.harness/releases/4.2.1/tools/rollback.py'
    receipt = tool.parent.parent / 'INSTALL.json'
    original = (tmp_path / 'CLAUDE.md').read_bytes()
    (tmp_path / 'CLAUDE.md').write_text('edited after install\n')
    before = snapshot(tmp_path)
    args = [sys.executable, str(tool), str(tmp_path), '--receipt', str(receipt)]
    assert subprocess.run(args, capture_output=True).returncode != 0
    assert snapshot(tmp_path) == before
    (tmp_path / 'CLAUDE.md').write_bytes(original)
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert snapshot(tmp_path) == {'AGENTS.md': b'custom root\n'}


def test_unchanged_older_install_is_preserved_until_review(tmp_path):
    import io
    import tarfile
    source = tmp_path / 'older-source'
    source.mkdir()
    archive = subprocess.check_output(['git', '-C', str(ROOT), 'archive', '4f43649'])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(source)
    target = tmp_path / 'target'
    target.mkdir()
    old = subprocess.run(['bash', str(source / 'scripts/install-project.sh'), str(target)], capture_output=True)
    assert old.returncode == 0
    before = snapshot(target)
    result = run(target, '--adopt')
    assert result.returncode == 0, result.stdout + result.stderr
    for rel, data in before.items():
        assert (target / rel).read_bytes() == data
    assert 'PENDING: preserve AGENTS.md' in result.stdout


def test_release_snapshot_tampering_fails_before_other_writes(tmp_path):
    assert run(tmp_path).returncode == 0
    policy = tmp_path / '.harness/releases/4.2.1/docs/workflows/optimization.md'
    policy.write_text('local snapshot edit')
    before = snapshot(tmp_path)
    assert run(tmp_path).returncode != 0
    assert snapshot(tmp_path) == before


def test_receipt_traversal_is_rejected_without_deletes(tmp_path):
    assert run(tmp_path).returncode == 0
    receipt = tmp_path / '.harness/releases/4.2.1/INSTALL.json'
    data = json.loads(receipt.read_text())
    data['created']['docs/../../outside'] = 'fake'
    receipt.write_text(json.dumps(data))
    before = snapshot(tmp_path)
    tool = receipt.parent / 'tools/rollback.py'
    result = subprocess.run([sys.executable, str(tool), str(tmp_path), '--receipt', str(receipt)], capture_output=True)
    assert result.returncode != 0
    assert snapshot(tmp_path) == before


def test_snapshot_roots_are_not_discoverable_nested_instructions(tmp_path):
    assert run(tmp_path).returncode == 0
    bundle = tmp_path / '.harness/releases/4.2.1'
    for name in ('AGENTS.md', 'CLAUDE.md'):
        assert not list(bundle.rglob(name))
        assert (bundle / (name + '.candidate')).is_file()
    assert not list(bundle.rglob('SKILL.md'))


def test_non_directory_parent_is_rejected_without_target_writes(tmp_path):
    (tmp_path / 'docs').write_bytes(b'pre-existing file, not a directory')
    before = snapshot(tmp_path)
    assert run(tmp_path).returncode != 0
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("use_alias_target", [False, True])
def test_rollback_accepts_alias_for_target_root(tmp_path, use_alias_target):
    real = tmp_path / 'real'
    real.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(real, target_is_directory=True)
    assert run(real).returncode == 0
    tool = real / '.harness/releases/4.2.1/tools/rollback.py'
    receipt = alias / '.harness/releases/4.2.1/INSTALL.json'
    result = subprocess.run([sys.executable, str(tool), str(alias if use_alias_target else real), '--receipt', str(receipt)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert snapshot(real) == {}


def test_rollback_rejects_internal_directory_symlink(tmp_path):
    real = tmp_path / 'real'
    real.mkdir()
    assert run(real).returncode == 0
    outside = tmp_path / 'outside-harness'
    (real / '.harness').rename(outside)
    (real / '.harness').symlink_to(outside, target_is_directory=True)
    before = snapshot(real)
    tool = outside / 'releases/4.2.1/tools/rollback.py'
    result = subprocess.run([sys.executable, str(tool), str(real), '--receipt', str(real / '.harness/releases/4.2.1/INSTALL.json')], capture_output=True)
    assert result.returncode != 0
    assert snapshot(real) == before
