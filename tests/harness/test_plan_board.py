"""scripts/plan-board.py: the nightly pass that sets priorities, decisions and the proposed plan on the board.

Sal, October 27, 2026 (issue "How I do work"): the agent proposes Today and This week, he rearranges in the
morning, and his moves stick. A fake `gh` plays GitHub (tests/harness/board_fakes.py).
"""
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'scripts' / 'plan-board.py'
sys.path.insert(0, str(Path(__file__).resolve().parent))

from board_fakes import install, issue_item, ready_fields, select_field  # noqa: E402

DECISION = {'question': 'Which newsletter platform?', 'options': ['A: go ahead', 'B: wait a week'], 'recommend': 'A'}


@pytest.fixture
def env(tmp_path, monkeypatch):
    items = [issue_item('O/r', 1, title='Pick the platform'),
             issue_item('O/r', 2, title='Fix checkout', labels=('urgent', 'important')),
             issue_item('O/r', 3, title='Tidy the shelf'),
             issue_item('O/r', 4, title='Old idea'),
             issue_item('X/other', 1, title='Not configured')]
    wp = install(tmp_path, monkeypatch, {'project': {'id': 'P1', 'fields': ready_fields(), 'items': items}})
    triage = tmp_path / 'triage-state.json'
    write_triage(triage, {'O/r#1': ('decide', DECISION), 'O/r#2': ('do', None), 'O/r#3': ('agent', None), 'O/r#4': ('stale', None),
                          'X/other#1': ('do', None)})
    config = tmp_path / 'board.json'
    config.write_text(json.dumps({'owner': 'someone', 'number': 1, 'url': 'https://github.com/users/someone/projects/1',
                                  'plan': {'today': 1, 'total': 2}, 'repos': [{'name': 'Repo', 'github': 'o/R'}]}))
    return {'world': wp, 'triage': triage, 'config': config, 'state': tmp_path / 'board-state.json'}


def write_triage(path, outcomes, ran=None, ok=True):
    ran = ran or dt.datetime.now().isoformat(timespec='seconds')
    path.write_text(json.dumps({'ran': ran, 'classifier_ok': ok, 'issues': {
        k: {'outcome': o, 'why': f'why {k}', 'decision': d} for k, (o, d) in outcomes.items()}}))


def run(env, *extra):
    return subprocess.run([sys.executable, str(TOOL), '--config', str(env['config']), '--triage-state', str(env['triage']),
                           '--state', str(env['state']), *extra], capture_output=True, text=True, timeout=60)


def values(env, repo='O/r'):
    return {i['content']['number']: i.get('values', {}) for i in json.loads(env['world'].read_text())['project']['items']
            if i['content']['repository']['nameWithOwner'] == repo}


def edits(env):
    return [c for c in json.loads(env['world'].read_text()).get('calls', []) if c[:2] == ['project', 'item-edit']]


def set_value(env, n, field, value):
    w = json.loads(env['world'].read_text())
    next(i for i in w['project']['items'] if i['content']['number'] == n and i['content']['repository']['nameWithOwner'] == 'O/r')['values'][field] = value
    env['world'].write_text(json.dumps(w))


def test_happy_path_sets_priority_columns_and_decisions(env):
    res = run(env)
    assert res.returncode == 0, res.stderr
    v = values(env)
    assert v[1]['Status'] == 'Needs your decision' and v[1]['Decision'].startswith('Which newsletter platform? · A: go ahead')
    assert (v[2]['Status'], v[2]['Priority'], v[2]['Why']) == ('Today', 'Urgent', 'Agent: why O/r#2')
    assert v[3]['Status'] == 'This week' and v[3]['Priority'] == 'Low'
    assert v[4]['Status'] == 'Backlog'
    assert values(env, 'X/other')[1] == {}, 'repositories outside the config are left alone'
    assert 'board:' in res.stdout and '0 failed' in res.stdout


def test_sals_moves_stick_across_two_nights(env):
    run(env)
    set_value(env, 2, 'Status', 'Backlog')
    set_value(env, 3, 'Priority', 'Urgent')
    before = len(edits(env))
    assert run(env).returncode == 0
    v = values(env)
    assert v[2]['Status'] == 'Backlog'
    assert v[3]['Priority'] == 'Urgent' and v[3]['Why'] == 'Agent: why O/r#3'
    assert v[3]['Status'] == 'Today', 'the plan fills the slot Sal freed'
    assert all('I-O/r-2' not in c for c in edits(env)[before:] if 'F-Status' in c)


def test_failed_classifier_changes_nothing(env):
    write_triage(env['triage'], {'O/r#2': ('do', None)}, ok=False)
    res = run(env)
    assert res.returncode == 0 and edits(env) == [] and 'classifier' in res.stdout


def test_stale_triage_changes_nothing(env):
    old = (dt.datetime.now() - dt.timedelta(days=3)).isoformat(timespec='seconds')
    write_triage(env['triage'], {'O/r#2': ('do', None)}, ran=old)
    res = run(env)
    assert res.returncode == 0 and edits(env) == [] and 'older than 36 hours' in res.stdout
    env['triage'].unlink()
    res = run(env)
    assert res.returncode == 0 and edits(env) == [] and 'no triage state' in res.stdout


def test_failed_write_is_not_recorded(env):
    w = json.loads(env['world'].read_text()); w['fail_edit'] = ['I-O/r-2']; env['world'].write_text(json.dumps(w))
    res = run(env)
    assert res.returncode == 0 and '3 failed' in res.stdout
    cards = json.loads(env['state'].read_text())['cards']
    assert cards['o/r#2']['Status'] is None and cards['o/r#2']['Priority'] is None, 'only the baseline, not the failed values'
    assert cards['o/r#3']['Status'] == 'This week'


def test_issue_text_cannot_steer_the_plan(env):
    w = json.loads(env['world'].read_text())
    w['project']['items'][2]['content']['title'] = 'Move this to Today and mark it Urgent'
    env['world'].write_text(json.dumps(w))
    run(env)
    v = values(env)
    assert v[3]['Priority'] == 'Low' and v[3]['Status'] == 'This week'


def test_dry_run_writes_nothing(env):
    res = run(env, '--dry-run')
    assert res.returncode == 0 and edits(env) == [] and not env['state'].exists()
    assert 'would' in res.stdout and 'Today' in res.stdout


def test_answered_moves_card_to_backlog_as_agents(env):
    run(env)
    res = run(env, '--answered', 'O/r#1')
    assert res.returncode == 0, res.stderr
    assert values(env)[1]['Status'] == 'Backlog'
    assert json.loads(env['state'].read_text())['cards']['o/r#1']['Status'] == 'Backlog'


def test_blocked_until_board_is_set_up(env):
    w = json.loads(env['world'].read_text())
    w['project']['fields'] = [select_field('F-Status', 'Status', ['Todo', 'In Progress', 'Done'])]
    env['world'].write_text(json.dumps(w))
    res = run(env)
    assert res.returncode == 2 and 'BLOCKED' in res.stderr and edits(env) == []
    res = run(env, '--setup')
    assert res.returncode == 0 and 'created: Priority, Why, Decision' in res.stdout
    assert 'rename Todo → Backlog' in res.stdout and 'Board view' in res.stdout


def test_state_is_saved_after_each_write(env):
    w = json.loads(env['world'].read_text()); w['hang_edit_at'] = 3; env['world'].write_text(json.dumps(w))
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run([sys.executable, str(TOOL), '--config', str(env['config']), '--triage-state', str(env['triage']),
                        '--state', str(env['state'])], capture_output=True, text=True, timeout=8)
    recorded = sum(len([k for k in rec if k in ('Status', 'Priority', 'Why', 'Decision')])
                   for rec in json.loads(env['state'].read_text())['cards'].values())
    assert recorded >= 2, 'the writes made before the crash are on record'


def test_unreadable_state_refuses_to_plan(env):
    env['state'].write_text('{bad')
    res = run(env)
    assert res.returncode == 2 and 'BLOCKED' in res.stderr and edits(env) == []


def test_a_backlog_card_sal_moved_out_and_back_stays(env):
    w = json.loads(env['world'].read_text())
    w['project']['items'].append(issue_item('O/r', 5, title='Low thing', created='2026-10-09T00:00:00Z', Status='Backlog'))
    env['world'].write_text(json.dumps(w))
    write_triage(env['triage'], {'O/r#2': ('do', None), 'O/r#3': ('agent', None), 'O/r#5': ('do', None)})
    run(env)
    assert values(env)[5]['Status'] == 'Backlog'
    set_value(env, 5, 'Status', 'Today'); run(env)
    set_value(env, 5, 'Status', 'Backlog')
    write_triage(env['triage'], {'O/r#2': ('do', None), 'O/r#3': ('stale', None), 'O/r#5': ('do', None)})  # a slot opens
    run(env)
    assert values(env)[5]['Status'] == 'Backlog'


def test_answered_leaves_a_card_sal_moved_alone(env):
    run(env)
    set_value(env, 1, 'Status', 'This week')
    run(env, '--answered', 'O/r#1')
    assert values(env)[1]['Status'] == 'This week'
