"""scripts/board_github.py: read Sal's GitHub Project board and write field values, through `gh`.

A fake `gh` plays GitHub (tests/harness/board_fakes.py); nothing leaves the test.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from board_fakes import install, issue_item, ready_fields, select_field  # noqa: E402
import board_github  # noqa: E402
from board_github import create_fields, load_board, load_state, save_state, setup_gaps, write  # noqa: E402
from board_rules import Change  # noqa: E402


def world(**kw):
    return {'project': {'id': 'P1', 'fields': ready_fields(), 'items': []}, **kw}


def test_reads_every_page_of_cards(tmp_path, monkeypatch):
    w = world(); w['project']['items'] = [issue_item('O/r', n) for n in range(150)] + [
        {'id': 'D1', 'type': 'DraftIssue', 'content': {'title': 'draft'}}, {'id': 'D2', 'type': 'PullRequest', 'content': {'title': 'pr'}}]
    wp = install(tmp_path, monkeypatch, w)
    board = load_board('someone', 1)
    assert len(board.cards) == 150 and board.project_id == 'P1'
    calls = [c for c in json.loads(wp.read_text())['calls'] if c[:2] == ['api', 'graphql']]
    assert len(calls) == 2 and any(a.startswith('after=') for a in calls[1])


def test_card_fields_and_open_prs_are_read(tmp_path, monkeypatch):
    w = world(); w['project']['items'] = [issue_item('O/r', 7, title='Fix checkout', labels=('urgent',), prs=('https://github.com/O/r/pull/9',),
                                                     Status='Today', Priority='High', Why='Agent: x', Decision='Q?')]
    install(tmp_path, monkeypatch, w)
    c = load_board('someone', 1).cards[0]
    assert (c.key, c.title, c.repo, c.state, c.labels) == ('O/r#7', 'Fix checkout', 'O/r', 'OPEN', {'urgent'})
    assert (c.status, c.priority, c.why, c.decision, c.open_prs) == ('Today', 'High', 'Agent: x', 'Q?', ['https://github.com/O/r/pull/9'])


def test_organization_boards_are_read(tmp_path, monkeypatch):
    w = world(owner_type='organization'); w['project']['items'] = [issue_item('O/r', 1)]
    install(tmp_path, monkeypatch, w)
    assert len(load_board('org', 1, 'organization').cards) == 1


def test_write_uses_option_id_for_selects_and_text_for_text(tmp_path, monkeypatch):
    w = world(); w['project']['items'] = [issue_item('O/r', 1)]
    wp = install(tmp_path, monkeypatch, w)
    board = load_board('someone', 1)
    write(board, Change('I-O/r-1', 'O/r#1', 'Status', 'Today'))
    write(board, Change('I-O/r-1', 'O/r#1', 'Why', 'Agent: launch'))
    after = json.loads(wp.read_text())
    assert after['project']['items'][0]['values'] == {'Status': 'Today', 'Why': 'Agent: launch'}
    edits = [c for c in after['calls'] if c[:2] == ['project', 'item-edit']]
    assert '--single-select-option-id' in edits[0] and '--text' in edits[1]


def test_write_failure_raises(tmp_path, monkeypatch):
    w = world(fail_edit=['I-O/r-1']); w['project']['items'] = [issue_item('O/r', 1)]
    install(tmp_path, monkeypatch, w)
    board = load_board('someone', 1)
    with pytest.raises(RuntimeError):
        write(board, Change('I-O/r-1', 'O/r#1', 'Status', 'Today'))


def test_setup_gaps_names_missing_status_options_and_fields(tmp_path, monkeypatch):
    w = world(); w['project']['fields'] = [select_field('F-Status', 'Status', ['Todo', 'In Progress', 'Done'])]
    install(tmp_path, monkeypatch, w)
    gaps = '\n'.join(setup_gaps(load_board('someone', 1)))
    assert 'Todo' in gaps and 'Backlog' in gaps and 'In Progress' in gaps and 'Being worked on' in gaps and 'Needs your decision' in gaps
    assert 'Priority' in gaps and 'Why' in gaps and 'Decision' in gaps and '--setup' in gaps
    w['project']['fields'] = ready_fields(); install(tmp_path, monkeypatch, w)
    assert setup_gaps(load_board('someone', 1)) == []


def test_create_fields_adds_only_missing_ones(tmp_path, monkeypatch):
    w = world(); w['project']['fields'] = [f for f in ready_fields() if f['name'] not in ('Priority', 'Decision')]
    wp = install(tmp_path, monkeypatch, w)
    assert create_fields('someone', 1, load_board('someone', 1)) == ['Priority', 'Decision']
    fields = {f['name']: f for f in json.loads(wp.read_text())['project']['fields']}
    assert [o['name'] for o in fields['Priority']['options']] == ['Urgent', 'High', 'Medium', 'Low']
    assert 'options' not in fields['Decision']


def test_a_hung_gh_call_raises_runtime_error(tmp_path, monkeypatch):
    install(tmp_path, monkeypatch, world(hang_graphql=True))
    monkeypatch.setattr(board_github, 'TIMEOUT', 1)
    with pytest.raises(RuntimeError):
        load_board('someone', 1)


def test_state_is_saved_whole_and_garbage_is_refused(tmp_path):
    p = tmp_path / 'state.json'
    assert load_state(p) == {}
    save_state(p, {'cards': {'o/r#1': {'Status': 'Today'}}})
    assert load_state(p) == {'cards': {'o/r#1': {'Status': 'Today'}}} and not list(tmp_path.glob('*.tmp'))
    p.write_text('{bad')
    with pytest.raises(ValueError):
        load_state(p)
