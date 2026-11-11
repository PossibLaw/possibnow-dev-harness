"""Commands an agent runs from a skill, command or agent file must not hardcode the home folder.

Repositories may live under another root (`$REPOS`) and the private configs under `$AGENT_TASKS_DIR`.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = ('~/possibnow-dev-harness/', '~/agent-tasks')


def _files():
    for folder in ('skills', 'commands', 'agents'):
        yield from (ROOT / folder).rglob('*.md')


def test_no_skill_command_or_agent_hardcodes_the_home_folder_paths():
    bad = [f'{p.relative_to(ROOT)}:{n}: {line.strip()}'
           for p in _files() for n, line in enumerate(p.read_text().splitlines(), 1)
           if any(f in line for f in FORBIDDEN)]
    assert not bad, 'use "${REPOS:-$HOME}/possibnow-dev-harness/..." and "${AGENT_TASKS_DIR:-$HOME/agent-tasks}/...":\n' + '\n'.join(bad)


def test_morning_brief_skill_uses_the_configurable_roots():
    text = (ROOT / 'skills' / 'answering-the-morning-brief' / 'SKILL.md').read_text()
    assert '"${REPOS:-$HOME}/possibnow-dev-harness/scripts/plan-board.py"' in text
    assert '"${REPOS:-$HOME}/possibnow-dev-harness/scripts/dispatch-auto-issues.py"' in text
    assert '"${AGENT_TASKS_DIR:-$HOME/agent-tasks}/board.json"' in text
    assert '"${AGENT_TASKS_DIR:-$HOME/agent-tasks}/policy/dispatch.json"' in text
