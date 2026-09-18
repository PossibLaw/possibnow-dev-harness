from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / 'scripts/entry_policy.py'


@pytest.mark.parametrize('newline', [b'\n', b'\r\n'])
@pytest.mark.parametrize('trailing', [False, True])
@pytest.mark.parametrize('lines,code', [(150, 0), (151, 1)])
def test_physical_line_boundary(tmp_path, newline, trailing, lines, code):
    p = tmp_path / 'AGENTS.md'
    p.write_bytes(newline.join([b'# line'] * lines) + (newline if trailing else b''))
    result = subprocess.run([sys.executable, str(CHECK), str(p)], capture_output=True)
    assert result.returncode == code


def test_eager_import_is_rejected_even_in_short_entry(tmp_path):
    p = tmp_path / 'CLAUDE.md'
    p.write_text('@docs/handbook.md\n')
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs/handbook.md').write_text('@../.agent/HISTORY.md\n')
    assert subprocess.run([sys.executable, str(CHECK), str(p)], capture_output=True).returncode == 1


def test_templates_are_generated_and_no_global_config_leaks():
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/render_entries.py'), '--check'], capture_output=True)
    assert result.returncode == 0
    for name in ['AGENTS.md', 'CLAUDE.md']:
        data = (ROOT / 'packs/project' / name).read_text()
        assert len(data.splitlines()) <= 150
        assert '~/' not in data
        assert 'read-only' in data
        assert 'do not load' in data.lower()


def test_extensionless_inline_import_is_rejected(tmp_path):
    p = tmp_path / 'CLAUDE.md'
    p.write_text('Always read @README at startup.\n')
    assert subprocess.run([sys.executable, str(CHECK), str(p)], capture_output=True).returncode == 1


def test_no_automatically_loaded_rules_or_memory_are_shipped():
    for relative in ('.claude/rules', '.cursor/rules', 'AGENTS.override.md', 'CLAUDE.local.md'):
        assert not (ROOT / 'packs/project' / relative).exists()
