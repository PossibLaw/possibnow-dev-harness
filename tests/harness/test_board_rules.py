"""scripts/board_rules.py: who owns a card's column and priority, and what the nightly plan changes.

Sal, October 27, 2026 (issue "How I do work"): the agent suggests a priority for every issue and proposes
Today and This week; "his moves stick"; automatic moves (pull request open, issue closed, run started)
always apply. Pure functions; nothing leaves the test.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

from board_rules import (PRIORITIES, Card, automatic_changes, decision_text, is_agents,  # noqa: E402
                         plan_changes, priority_from_labels)


def card(key, status=None, priority=None, labels=(), state='OPEN', created='2026-10-01T00:00:00Z', open_prs=()):
    return Card(item_id=f'item-{key}', key=key, url=f'https://github.com/O/r/issues/{key}', title=f'Issue {key}', repo='O/r',
                state=state, created=created, labels=set(labels), status=status, priority=priority, why=None, decision=None,
                open_prs=list(open_prs))


def triage(outcomes, why='launch depends on it', decision=None):
    return {'issues': {k: {'outcome': o, 'why': why, 'decision': decision if o == 'decide' else None} for k, o in outcomes.items()}}


def changed(changes, field):
    return {c.key: c.value for c in changes if c.field == field}


def test_priority_follows_labels():
    assert [priority_from_labels(s) for s in ({'urgent', 'important'}, {'important'}, {'urgent'}, set())] == list(PRIORITIES)


def test_unrecorded_backlog_is_the_agents_but_unrecorded_today_is_sals():
    assert is_agents(None, {}, 'Status') and is_agents('Backlog', {}, 'Status')
    assert not is_agents('Today', {}, 'Status')
    assert is_agents('Today', {'Status': 'Today'}, 'Status')
    assert is_agents(None, {}, 'Priority') and not is_agents('High', {}, 'Priority')


def test_agent_priority_and_reason_are_written():
    ch = plan_changes([card('A', labels={'important'})], triage({'A': 'do'}), {'cards': {}}, 3, 10)
    assert changed(ch, 'Priority') == {'A': 'High'}
    assert changed(ch, 'Why') == {'A': 'Agent: launch depends on it'}


def test_a_card_sal_moved_back_to_backlog_stays_there():
    ch = plan_changes([card('A', status='Backlog')], triage({'A': 'do'}), {'cards': {'A': {'Status': 'Today'}}}, 3, 10)
    assert changed(ch, 'Status') == {}


def test_sal_priority_and_why_are_left_alone():
    ch = plan_changes([card('A', priority='Low', labels={'important'})], triage({'A': 'do'}), {'cards': {'A': {'Priority': 'High'}}}, 3, 10)
    assert changed(ch, 'Priority') == {} and changed(ch, 'Why') == {}


def test_plan_fills_today_then_this_week_around_sals_cards():
    sals = card('S', status='Today')  # unrecorded and not in Backlog: Sal put it there
    cands = [card(f'c{i}', labels={'urgent', 'important'} if i < 4 else set(), created=f'2026-10-{20 - i:02d}T00:00:00Z') for i in range(12)]
    ch = changed(plan_changes([sals, *cands], triage({c.key: 'do' for c in [sals, *cands]}), {'cards': {}}, 3, 10), 'Status')
    assert 'S' not in ch
    assert [k for k, v in ch.items() if v == 'Today'] == ['c3', 'c2']
    assert sorted(k for k, v in ch.items() if v == 'This week') == sorted(['c1', 'c0', 'c11', 'c10', 'c9', 'c8', 'c7'])
    assert sorted(k for k, v in ch.items() if v == 'Backlog') == ['c4', 'c5', 'c6']


def test_agent_cards_are_replanned_each_night():
    ch = plan_changes([card('A', status='Today')], triage({'A': 'do'}), {'cards': {'A': {'Status': 'Today'}}}, 0, 0)
    assert changed(ch, 'Status') == {'A': 'Backlog'}


def test_decisions_go_to_their_column_with_the_question():
    d = {'question': 'Which newsletter platform?', 'options': ['A: go ahead', 'B: wait a week'], 'recommend': 'A'}
    ch = plan_changes([card('D')], triage({'D': 'decide'}, decision=d), {'cards': {}}, 3, 10)
    assert changed(ch, 'Status') == {'D': 'Needs your decision'}
    assert changed(ch, 'Decision') == {'D': 'Which newsletter platform? · A: go ahead · B: wait a week · Recommend A'}
    assert decision_text({'question': 'x' * 2000, 'options': [], 'recommend': 'A'}).__len__() <= 1000


def test_answered_decision_returns_to_backlog():
    ch = plan_changes([card('D', status='Needs your decision')], triage({'D': 'do'}), {'cards': {'D': {'Status': 'Needs your decision'}}}, 0, 0)
    assert changed(ch, 'Status') == {'D': 'Backlog'}


def test_stale_done_and_untriaged_are_never_planned():
    cards = [card('S'), card('F'), card('U'), card('X', state='CLOSED')]
    ch = plan_changes(cards, triage({'S': 'stale', 'F': 'done', 'X': 'do'}), {'cards': {}}, 3, 10)
    assert changed(ch, 'Status') == {'S': 'Backlog', 'F': 'Backlog'}


def test_automatic_moves_override_sals_choice():
    cards = [card('P', status='Today', open_prs=['https://github.com/O/r/pull/9']), card('C', status='Today', state='CLOSED'),
             card('R', status='Backlog'), card('N', status='Needs your review', open_prs=['u'])]
    ch = changed(automatic_changes(cards, {'https://github.com/O/r/issues/R'}), 'Status')
    assert ch == {'P': 'Needs your review', 'C': 'Done', 'R': 'Being worked on'}
