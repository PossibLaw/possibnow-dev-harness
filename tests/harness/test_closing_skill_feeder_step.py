"""The closing skill must end with the cross-repo feeder step so every install carries it."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'skills' / 'closing-sprint-and-syncing-state' / 'SKILL.md'


def test_closing_skill_ends_with_the_cross_repo_feeder_step():
    text = SKILL.read_text()
    assert 'cross-repo-tasks/feed.py' in text, 'closing skill does not name the feeder'
    last_paragraph = text.rstrip().split('\n\n')[-1]
    assert 'feed.py' in last_paragraph, 'the feeder step is not the last step of the skill'
    assert 'skip' in text.lower() and 'not installed' in text.lower(), 'skill must say what to do when the feeder is absent'
