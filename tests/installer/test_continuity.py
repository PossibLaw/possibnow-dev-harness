from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts/install-project.sh'


def install(target, *args):
    return subprocess.run(['bash', str(SCRIPT), str(target), *args], capture_output=True, text=True)


def test_dry_run_is_read_only(tmp_path):
    before = list(tmp_path.rglob('*'))
    assert install(tmp_path, '--dry-run').returncode == 0
    assert list(tmp_path.rglob('*')) == before


def test_upgrade_preserves_history_and_removes_only_obsolete_rules(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    state = tmp_path / '.agent'
    state.mkdir()
    (state / 'HANDOFF.md').write_text('current work\n')
    (state / 'HISTORY.md').write_text('historical work\n')
    (tmp_path / '.gitignore').write_text('.env*\n.agent/private-notes.md\n.agent/PLAN.md\n.agent/HISTORY.md\n.agent/CONTENT-PLAN.md\n.claude/history.md\n')
    result = install(tmp_path, '--adopt')
    assert result.returncode == 0, result.stderr
    assert (state / 'HANDOFF.md').read_text() == 'current work\n'
    assert (state / 'HISTORY.md').read_text() == 'historical work\n'
    for rel in ['.agent/PLAN.md', '.agent/TEST.md', '.agent/HISTORY.md', '.agent/CONTENT-PLAN.md', '.claude/history.md']:
        assert subprocess.run(['git', '-C', str(tmp_path), 'check-ignore', '-q', rel]).returncode == 1
    for rel in ['.env.local', '.agent/private-notes.md']:
        assert subprocess.run(['git', '-C', str(tmp_path), 'check-ignore', '-q', rel]).returncode == 0


def test_fresh_install_delivers_optimization_workflow_and_history(tmp_path):
    assert install(tmp_path).returncode == 0
    assert (tmp_path / 'docs/workflows/optimization.md').is_file()
    assert (tmp_path / '.agent/HISTORY.md').is_file()


def test_existing_continuity_preserved_even_without_adopt(tmp_path):
    state = tmp_path / '.agent'
    state.mkdir()
    (state / 'HANDOFF.md').write_text('must survive\n')
    (state / 'HISTORY.md').write_text('history must survive\n')
    assert install(tmp_path).returncode == 0
    assert (state / 'HANDOFF.md').read_text() == 'must survive\n'
    assert (state / 'HISTORY.md').read_text() == 'history must survive\n'


def test_symlinked_state_directory_cannot_escape_target(tmp_path):
    target = tmp_path / 'target'
    outside = tmp_path / 'outside'
    target.mkdir()
    outside.mkdir()
    (target / '.agent').symlink_to(outside, target_is_directory=True)
    result = install(target)
    assert result.returncode != 0
    assert list(outside.iterdir()) == []
