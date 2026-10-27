"""Stop hook: tell Sal in Slack the moment an autonomous run finishes or gets stuck.

Sal, October 27, 2026: "I should get a notice when something finishes at that time. Not a day later."
The dispatcher's morning report only flags pull requests on its next nightly pass.
"""
import importlib.util
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARDS = ROOT / 'scripts' / 'guardrails'
HOOK = GUARDS / 'autonomy-notify.py'
POSTS = []

FAKE_GH = r'''#!/usr/bin/env python3
import json, os, sys
world = json.load(open(os.environ["FAKE_WORLD"])); args = sys.argv[1:]
path = next(a for a in args[1:] if not a.startswith("-") and a not in ("GET",)).split("?")[0]
if path.endswith("/pulls"):
    print(json.dumps(world.get("pulls", [])))
elif "/issues/" in path:
    print(json.dumps({"number": 22, "title": "Claude Code content update", "html_url": "https://github.com/o/r/issues/22"}))
else:
    print("unhandled", path, file=sys.stderr); sys.exit(1)
'''


class Slack(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        if self.server.fail:
            self.send_response(500); self.end_headers(); return
        POSTS.append(json.loads(body)['text'])
        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')

    def log_message(self, *a):
        pass


def autonomy():
    spec = importlib.util.spec_from_file_location('autonomy_notify_under_test', GUARDS / 'autonomy.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def git(*args, cwd):
    env = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@e.invalid', 'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@e.invalid'}
    subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, env=env)


@pytest.fixture
def env(tmp_path, monkeypatch):
    POSTS.clear()
    server = ThreadingHTTPServer(('127.0.0.1', 0), Slack); server.fail = False
    threading.Thread(target=server.serve_forever, daemon=True).start()
    main = tmp_path / 'main'; main.mkdir()
    git('init', '-q', '-b', 'main', cwd=main); git('commit', '-q', '--allow-empty', '-m', 'i', cwd=main)
    wt = tmp_path / 'auto-22'
    git('worktree', 'add', '-q', '-b', 'auto-22', str(wt), cwd=main)
    autonomy().write_marker(str(wt), {'repo': 'o/r', 'issue': 22, 'title': 'Claude Code content update', 'worktree': 'auto-22',
                                      'started': '2026-10-27T03:06:45+00:00', 'dispatched_session': 's1'})
    bin_dir = tmp_path / 'bin'; bin_dir.mkdir()
    (bin_dir / 'gh').write_text(FAKE_GH); (bin_dir / 'gh').chmod(0o755)
    world = tmp_path / 'world.json'; world.write_text('{}')
    transcript = tmp_path / 't.jsonl'
    transcript.write_text('\n'.join(json.dumps(e) for e in (
        {'type': 'user', 'message': {'role': 'user', 'content': 'Autonomous run ...'}},
        {'type': 'assistant', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': 'I could not verify the /goal syntax against the docs, so I stopped and asked on the issue.'}]}},
    )) + '\n')
    e = {k: v for k, v in os.environ.items() if k != 'AGENT_AUTO'}
    e.update(PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}", FAKE_WORLD=str(world), SLACK_WEBHOOK_URL=f'http://127.0.0.1:{server.server_address[1]}/hook')
    yield {'wt': str(wt), 'world': world, 'env': e, 'server': server, 'transcript': str(transcript)}
    server.shutdown()


def stop(env, **extra):
    payload = {'hook_event_name': 'Stop', 'session_id': 's1', 'cwd': env['wt'], 'transcript_path': env['transcript'], 'stop_hook_active': False, **extra}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, cwd=env['wt'], env=env['env'], timeout=30)


def with_pr(env):
    env['world'].write_text(json.dumps({'pulls': [{'number': 865, 'title': '[auto] Claude Code content update', 'html_url': 'https://github.com/o/r/pull/865',
                                                    'head': {'ref': 'auto-22'}, 'body': 'Closes #22', 'created_at': '2026-10-27T03:50:00Z', 'draft': True}]}))


def test_a_finished_run_posts_the_issue_and_its_pull_request_by_name(env):
    with_pr(env)
    res = stop(env)
    assert res.returncode == 0, res.stderr
    [text] = POSTS
    assert 'Claude Code content update' in text and '[auto] Claude Code content update' in text and 'https://github.com/o/r/pull/865' in text
    assert 'review' in text.lower()


def test_the_same_finish_is_announced_once(env):
    with_pr(env)
    stop(env); stop(env)
    assert len(POSTS) == 1


def test_a_run_that_stops_without_a_pull_request_says_it_needs_sal_and_quotes_the_agent(env):
    res = stop(env)
    assert res.returncode == 0, res.stderr
    [text] = POSTS
    assert 'without a pull request' in text and 'could not verify the /goal syntax' in text and 'auto-22' in text


def test_ordinary_sessions_and_taken_over_runs_stay_quiet(env, tmp_path):
    plain = tmp_path / 'plain'; plain.mkdir(); git('init', '-q', '-b', 'feature/x', cwd=plain)
    stop(env, cwd=str(plain))
    m = autonomy(); marker = m.read_marker(env['wt']); marker['taken_over'] = '2026-10-27T04:00:00+00:00'; m.write_marker(env['wt'], marker)
    with_pr(env); stop(env)
    assert POSTS == []


def test_a_slack_failure_never_blocks_the_agent_and_is_retried_next_time(env):
    with_pr(env)
    env['server'].fail = True
    res = stop(env)
    assert res.returncode == 0 and POSTS == []
    env['server'].fail = False
    stop(env)
    assert len(POSTS) == 1


def test_a_stop_hook_re_entry_is_ignored(env):
    with_pr(env)
    stop(env, stop_hook_active=True)
    assert POSTS == []
