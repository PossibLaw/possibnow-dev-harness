"""The work-router skill: one sentence → the right repo's issue, with the flywheel line."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'skills' / 'routing-work-to-a-repo' / 'SKILL.md'


def test_routing_skill_exists_with_metadata():
    assert SKILL.is_file(), 'skills/routing-work-to-a-repo/SKILL.md is missing'
    text = SKILL.read_text()
    assert text.startswith('---\nname: routing-work-to-a-repo\n')
    assert 'description:' in text


def test_routing_skill_reads_a_private_table_and_never_guesses():
    text = SKILL.read_text()
    assert 'routing.md' in text, 'skill must name the routing table file'
    assert 'ask' in text.lower() and 'no match' in text.lower() or 'nothing matches' in text.lower()


def test_routing_skill_files_the_issue_with_flywheel_line_and_offers_a_worktree():
    text = SKILL.read_text()
    assert 'This leads to' in text, 'flywheel line shape must be in the skill'
    assert 'gh issue create' in text or 'gh api' in text
    assert 'agent-task' in text and 'routed' in text
    assert 'orca worktree create' in text
    assert 'never' in text.lower() and ('bank' in text.lower() or 'card' in text.lower())
