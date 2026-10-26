"""The skill that applies Sal's answers to the nightly triage brief ("brief 1A 2B", "opt in ...", "close stale")."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'skills' / 'answering-the-morning-brief' / 'SKILL.md'


def test_skill_exists_with_metadata_and_triggers():
    assert SKILL.is_file(), 'skills/answering-the-morning-brief/SKILL.md is missing'
    text = SKILL.read_text()
    assert text.startswith('---\nname: answering-the-morning-brief\n')
    assert 'description:' in text and 'brief 1A' in text and 'opt in' in text and 'close stale' in text


def test_skill_reads_the_saved_decisions_and_records_each_answer_on_the_issue():
    text = SKILL.read_text()
    assert 'triage-state.json' in text and 'triage-brief.md' in text
    assert 'comment' in text.lower()
    assert 'TASKS.md' in text, 'register-backed issues are changed in the register, because the sync overwrites GitHub edits'


def test_skill_opts_in_only_what_the_dispatcher_would_accept_and_never_touches_sals_labels():
    text = SKILL.read_text()
    assert 'auto-ok' in text and 'dispatch-auto-issues.py' in text and '--dry-run' in text
    assert 'urgent' in text and 'important' in text and 'override' in text.lower()
    assert 'names, not numbers' in text.lower() or 'by name' in text.lower()
