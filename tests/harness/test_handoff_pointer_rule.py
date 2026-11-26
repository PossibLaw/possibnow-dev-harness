"""The text that invited prepending now asks for one line with a link (November 25, 2026).

Trazomo's HANDOFF matched the 4.3.8 structure exactly; the drift came from practice, and
three things invited it: the checkpoint checklist ("refresh the Current Baton at the
top"), the closing skill, and run prompts that asked for a HANDOFF entry. These tests pin
the replacement wording (HS-8, HS-9) and this repository's own HANDOFF (HS-12).
"""
import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / 'packs/project'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# HS-8
def test_closing_skill_replaces_and_requires_a_carry_forward_list():
    text = (ROOT / 'skills/closing-sprint-and-syncing-state/SKILL.md').read_text()
    assert 'Replace the checkpoint, do not prepend. Each entry is one line with a link.' in text
    assert 'carry-forward list' in text
    for state in ('KEPT', 'POINTS TO', 'RESOLVED'):
        assert state in text, f'carry-forward states must include {state}'
    assert 'old location' in text
    assert 'UNCONFIRMED' in text, 'unconfirmable items are kept and marked UNCONFIRMED'


# HS-9
def test_contract_states_the_pointer_rules():
    text = ' '.join((PACK / 'docs/workflows/contracts.md').read_text().split())
    assert 'A HANDOFF entry is one line' in text
    assert 'never prepends' in text
    assert 'handoff_size.py' in text
    assert 'handoff-limits.json' in text
    for kept in ('owed items', 'pending decisions', 'UNCONFIRMED facts'):
        assert kept in text


def test_template_has_recent_work_and_a_short_status():
    text = (PACK / '.agent/HANDOFF.md').read_text()
    one_line = ' '.join(text.split())
    assert ('Each entry is one line that points to the PR, issue or document holding the detail. '
            'A close replaces this file through `checkpoint.py`; it never prepends a narrative.') in one_line
    assert '## Recent work' in text
    assert 'Newest first, one line each; the link holds the detail.' in one_line
    status = text.split('## Status', 1)[1].split('\n## ', 1)[0]
    assert 'a few lines' in status.lower()


def test_entry_files_carry_the_rule_line():
    for name in ('AGENTS.md', 'CLAUDE.md'):
        text = ' '.join((PACK / name).read_text().split())
        assert 'one line with a link' in text, name


def test_checkpoint_checklist_says_replace_not_prepend(tmp_path):
    (tmp_path / '.agent').mkdir()
    (tmp_path / '.agent/PLAN.md').write_text('# Plan\n')
    (tmp_path / '.agent/HANDOFF.md').write_text('# Handoff\n')
    out = subprocess.run(['bash', str(PACK / '.agent/integrations/run-checkpoint.sh'), str(tmp_path)],
                         capture_output=True, text=True, check=True).stdout
    assert 'Current Baton at the top' not in out
    assert 'replace the checkpoint through checkpoint.py; one line per entry with a link' in out
    assert 'handoff_size.py' in out


ONE_LINE = 'one line under `## Recent work`'


def test_dispatcher_default_prompt_asks_for_one_line():
    text = (ROOT / 'scripts/dispatch-auto-issues.py').read_text()
    default = text.split('prompt_tpl = cfg.get("prompt") or ', 1)[1].split('\n', 1)[0]
    assert ONE_LINE in default and 'HANDOFF' in default


def test_freshness_work_order_asks_for_one_line():
    mod = load(ROOT / 'scripts/content-freshness.py', 'content_freshness')
    body = mod.render({'name': 'w', 'scope': ['a.md']}, {'sources': {}, 'pages': {}}, '2026-11-25')
    assert ONE_LINE in body and 'HANDOFF' in body


# HS-12
def test_this_repository_handoff_is_within_limits():
    mod = load(PACK / '.agent/integrations/handoff_size.py', 'handoff_size')
    problems, _ = mod.check_repo(ROOT)
    assert problems == [], problems


def test_verify_pack_runs_the_size_check():
    assert 'handoff_size.py' in (ROOT / 'scripts/verify-pack.sh').read_text()
