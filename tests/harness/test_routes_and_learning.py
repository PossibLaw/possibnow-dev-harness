from pathlib import Path
import re
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / 'packs/project'


def test_root_routes_and_required_safety_homes():
    for name in ('AGENTS.md', 'CLAUDE.md'):
        for target in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', (PACK / name).read_text()):
            assert (PACK / target).is_file(), target
    delivery = (PACK / 'docs/workflows/delivery.md').read_text()
    for requirement in ['TDD', 'Security Review Mode', 'cross-user isolation', 'CSRF', 'remote main', 'content', 'UNCONFIRMED']:
        assert requirement in delivery
    assert 'existing project content routes' in (PACK / 'AGENTS.md').read_text()
    assert 'before replacing' in (PACK / 'AGENTS.md').read_text()


def test_learning_modes_and_promotion_are_canonical():
    policy = (PACK / 'docs/workflows/learning.md').read_text()
    for requirement in ['OFF: add no entries', 'CAPTURE:', 'APPLY:', 'two distinct',
                        'explicitly', 'unapproved', 'future action', 'authorization', 'retire']:
        assert requirement in policy
    state = (PACK / '.agent/LEARNINGS.md').read_text()
    assert '## Candidates (unapproved)' in state and '## Adopted lessons' in state
    assert 'docs/workflows/learning.md' in state
    assert 'auto-captured' not in state


@pytest.mark.parametrize('mode', ['OFF', 'CAPTURE', 'APPLY'])
def test_checkpoint_advice_never_captures_or_edits(tmp_path, mode):
    state = tmp_path / '.agent'
    state.mkdir()
    (state / 'PLAN.md').write_text(f'## Learning Mode\n- Mode: `{mode}`\n')
    (state / 'HANDOFF.md').write_text('current')
    (state / 'LEARNINGS.md').write_text('# Candidates\none-off unconfirmed observation\n')
    before = {p.name: p.read_bytes() for p in state.iterdir()}
    result = subprocess.run(['bash', str(PACK / '.agent/integrations/run-checkpoint.sh'), str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert {p.name: p.read_bytes() for p in state.iterdir()} == before
    if mode == 'OFF':
        assert 'Skip learnings' in result.stdout
    else:
        assert 'candidates are unapproved' in result.stdout


def test_templates_do_not_reintroduce_learning_or_handoff_diaries():
    plan = (PACK / '.agent/PLAN.md').read_text()
    assert 'docs/workflows/learning.md' in plan
    assert 'Session Timeline' not in plan
    assert 'append observations' not in plan
    assert 'Session Timeline' not in (PACK / '.agent/HANDOFF.md').read_text()
