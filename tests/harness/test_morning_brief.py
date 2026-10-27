"""scripts/morning-brief.py: one short Slack message in the morning, built from the board.

Sal, October 27, 2026 (issue "How I do work"): "ideally that morning Slack is just the top 10 things that need
to get done this week, but really today and then this week", each with what it is, the repo, the priority
and a link, plus a link to the board. A fake `gh` plays GitHub; a local web server plays Slack.
"""
import datetime as dt
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'scripts' / 'morning-brief.py'
sys.path.insert(0, str(Path(__file__).resolve().parent))

from board_fakes import install, issue_item, ready_fields  # noqa: E402

NOW = dt.datetime.now(dt.timezone.utc)


def iso(delta_hours=0):
    return (NOW - dt.timedelta(hours=delta_hours)).strftime('%Y-%m-%dT%H:%M:%SZ')


def pr(n, title, label=True, hours_ago=2):
    return {'number': n, 'title': title, 'html_url': f'https://github.com/O/r/pull/{n}', 'created_at': iso(hours_ago),
            'labels': [{'name': 'agent-auto'}] if label else []}


@pytest.fixture
def slack():
    posts = []

    class Hook(BaseHTTPRequestHandler):
        def do_POST(self):
            posts.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200); self.end_headers(); self.wfile.write(b'ok')

        def log_message(self, *a):
            pass

    server = HTTPServer(('127.0.0.1', 0), Hook)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield {'url': f'http://127.0.0.1:{server.server_port}/hook', 'posts': posts}
    server.shutdown()


@pytest.fixture
def env(tmp_path, monkeypatch, slack):
    items = [issue_item('O/r', 1, title='Record the intro', Status='Today', Priority='High'),
             issue_item('O/r', 2, title='Fix checkout', Status='Today', Priority='Urgent'),
             issue_item('O/r', 3, title='Onboarding security', Status='This week', Priority='Medium', created='2026-09-01T00:00:00Z'),
             issue_item('O/r', 4, title='Coupons', Status='This week'),
             issue_item('O/r', 5, title='Pick a platform', Status='Needs your decision'),
             issue_item('O/r', 6, title='Approve the cover', Status='Needs your decision'),
             issue_item('O/r', 7, title='Has a pull request', Status='Backlog', prs=('https://github.com/O/r/pull/70',)),
             issue_item('O/r', 8, title='Closed already', Status='Today', state='CLOSED'),
             issue_item('O/r', 9, title='Started overnight', Status='Backlog'),
             issue_item('O/r', 10, title='Stale one', Status='Backlog'),
             issue_item('O/r', 12, title='Closed stale', Status='Done', state='CLOSED')]
    wp = install(tmp_path, monkeypatch, {
        'project': {'id': 'P1', 'fields': ready_fields(), 'items': items},
        'pulls': {'O/r': [pr(865, '[auto] Claude Code content update'), pr(800, '[auto] Old run', hours_ago=72), pr(801, 'Sal fixes a typo', label=False)]}})
    triage = tmp_path / 'triage-state.json'
    triage.write_text(json.dumps({'ran': dt.datetime.now().isoformat(timespec='seconds'), 'classifier_ok': True,
                                  'issues': {'O/r#10': {'outcome': 'stale'}, 'O/r#11': {'outcome': 'do'}, 'O/r#12': {'outcome': 'stale'},
                                             'O/r#13': {'outcome': 'duplicate'}}}))
    dispatch = tmp_path / 'dispatch-state.json'
    dispatch.write_text(json.dumps({'ran': iso(6), 'started': [{'url': 'https://github.com/O/r/issues/9'}]}))
    config = tmp_path / 'board.json'
    config.write_text(json.dumps({'owner': 'someone', 'number': 1, 'url': 'https://github.com/users/someone/projects/1',
                                  'repos': [{'name': 'Trazomo', 'github': 'O/r'}], 'pr_label': 'agent-auto'}))
    monkeypatch.setenv('SLACK_WEBHOOK_URL', slack['url'])
    return {'world': wp, 'triage': triage, 'dispatch': dispatch, 'config': config, 'state': tmp_path / 'board-state.json'}


def run(env, *extra):
    return subprocess.run([sys.executable, str(TOOL), '--config', str(env['config']), '--triage-state', str(env['triage']),
                           '--state', str(env['state']), '--dispatch-state', str(env['dispatch']), *extra],
                          capture_output=True, text=True, timeout=60)


def statuses(env):
    return {i['content']['number']: i.get('values', {}).get('Status') for i in json.loads(env['world'].read_text())['project']['items']}


def add_week_cards(env, count):
    w = json.loads(env['world'].read_text())
    w['project']['items'] += [issue_item('O/r', 100 + i, Status='This week', Priority='Low') for i in range(count)]
    env['world'].write_text(json.dumps(w))


def test_happy_path_message(env, slack):
    res = run(env)
    assert res.returncode == 0, res.stderr
    assert len(slack['posts']) == 1
    text = slack['posts'][0]['text']
    assert 'Autonomous run finished: Claude Code content update (Trazomo). Ready for your review: <https://github.com/O/r/pull/865|' in text
    assert 'Old run' not in text and 'typo' not in text
    lines = text.splitlines()
    numbered = [l for l in lines if l[:2] in ('1.', '2.', '3.', '4.')]
    assert numbered == ['1. <https://github.com/O/r/issues/2|Fix checkout> · Trazomo · Urgent',
                        '2. <https://github.com/O/r/issues/1|Record the intro> · Trazomo · High',
                        '3. <https://github.com/O/r/issues/3|Onboarding security> · Trazomo · Medium',
                        '4. <https://github.com/O/r/issues/4|Coupons> · Trazomo · No priority']
    assert lines.index('*Today*') < lines.index('*This week*')
    assert '2 decisions waiting · 1 look stale. Reply in Claude to answer ("brief 1A", "close stale").' in text
    assert text.rstrip().endswith('<https://github.com/users/someone/projects/1|Open the board>')
    assert 'Closed already' not in text


def test_automatic_moves_run_before_reading(env):
    run(env)
    s = statuses(env)
    assert (s[7], s[8], s[9]) == ('Needs your review', 'Done', 'Being worked on')
    assert json.loads(env['state'].read_text())['cards']['o/r#8']['Status'] == 'Done'


def test_quiet_night(env, slack):
    w = json.loads(env['world'].read_text())
    w['pulls'] = {'O/r': []}
    for i in w['project']['items']:
        if i['values'].get('Status') in ('Today', 'This week'):
            i['values']['Status'] = 'Backlog'
    env['world'].write_text(json.dumps(w))
    run(env)
    text = slack['posts'][0]['text']
    assert 'Overnight: nothing finished.' in text and 'Nothing planned yet; open the board to pick.' in text
    assert 'Open the board' in text


def test_more_than_ten_shows_count(env, slack):
    add_week_cards(env, 12)
    run(env)
    text = slack['posts'][0]['text']
    assert sum(1 for l in text.splitlines() if l.split('.')[0].isdigit()) == 10
    assert '+6 more on the board' in text


def test_triage_failure_line(env, slack):
    env['triage'].write_text(json.dumps({'ran': dt.datetime.now().isoformat(timespec='seconds'), 'classifier_ok': False, 'issues': {}}))
    run(env)
    assert 'Triage did not run cleanly last night; priorities and the plan were left as they were.' in slack['posts'][0]['text']


def test_titles_are_escaped(env, slack):
    w = json.loads(env['world'].read_text())
    w['project']['items'][1]['content']['title'] = 'Fix <checkout> & pay'
    env['world'].write_text(json.dumps(w))
    run(env)
    assert '|Fix &lt;checkout&gt; &amp; pay>' in slack['posts'][0]['text']


def test_reported_moves_only_after_a_post(env, slack, monkeypatch):
    monkeypatch.delenv('SLACK_WEBHOOK_URL')
    res = run(env)
    assert 'not posted' in res.stdout and 'reported' not in json.loads(env['state'].read_text())
    monkeypatch.setenv('SLACK_WEBHOOK_URL', slack['url'])
    run(env)
    assert 'reported' in json.loads(env['state'].read_text())
    run(env)
    assert 'Overnight: nothing finished.' in slack['posts'][-1]['text'], 'the window starts at the last post'


def test_dry_run_posts_and_writes_nothing(env, slack):
    res = run(env, '--dry-run')
    assert res.returncode == 0 and slack['posts'] == [] and not env['state'].exists()
    assert 'Fix checkout' in res.stdout
    assert statuses(env)[8] == 'Today'


def test_unreadable_board_still_posts(env, slack):
    w = json.loads(env['world'].read_text()); del w['project']; env['world'].write_text(json.dumps(w))
    res = run(env)
    assert res.returncode == 0
    text = slack['posts'][0]['text']
    assert 'Could not read the board' in text and 'Claude Code content update' in text


def test_stale_dispatch_state_is_ignored(env):
    env['state'].write_text(json.dumps({'reported': (NOW - dt.timedelta(hours=20)).isoformat(timespec='seconds')}))
    env['dispatch'].write_text(json.dumps({'ran': iso(72), 'started': [{'url': 'https://github.com/O/r/issues/9'}]}))
    run(env)
    assert statuses(env)[9] == 'Backlog'


def test_triage_older_than_last_brief_is_flagged(env, slack):
    env['state'].write_text(json.dumps({'reported': (NOW - dt.timedelta(hours=1)).isoformat(timespec='seconds')}))
    env['triage'].write_text(json.dumps({'ran': (dt.datetime.now() - dt.timedelta(hours=10)).isoformat(timespec='seconds'),
                                         'classifier_ok': True, 'issues': {}}))
    run(env)
    assert 'Triage did not run cleanly last night' in slack['posts'][0]['text']
