"""scripts/content-freshness.py: watch the sources our articles and lessons cite; file a work order when they change.

Sal, October 26, 2026: the Claude Code drift work order is "basically the same thing we need to do with
articles we draft for possibnow, as well as anything else we teach in trazomo". One shared engine,
a watch list per repository; it checks cited sources (changed, dead, moved) and vendor doc indexes
(new pages). The work order is an issue the nightly autonomous dispatcher can start.

A local web server plays the cited sites and a fake `gh` plays GitHub; nothing leaves the test.
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
TOOL = ROOT / 'scripts' / 'content-freshness.py'
DISPATCH = ROOT / 'scripts' / 'dispatch-auto-issues.py'

PAGES = {}  # path -> (status, html)


class Site(BaseHTTPRequestHandler):
    def do_GET(self):
        status, body = PAGES.get(self.path, (404, '<html><body>Not found</body></html>'))
        if status in (301, 302):
            self.send_response(status); self.send_header('Location', body); self.end_headers(); return
        data = body.encode()
        self.send_response(status); self.send_header('Content-Type', 'text/html'); self.send_header('Content-Length', str(len(data))); self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


FAKE_GH = r'''#!/usr/bin/env python3
import json, sys, os
wp = os.environ["FAKE_WORLD"]; world = json.load(open(wp)); args = sys.argv[1:]
world.setdefault("calls", []).append(args)
def save(): json.dump(world, open(wp, "w"), indent=1)
method = args[args.index("--method") + 1] if "--method" in args else "GET"
full = next(a for a in args[1:] if not a.startswith("-") and a != method)
path = full.split("?")[0]
body = json.load(sys.stdin) if "--input" in args else {}
repo = "/".join(path.split("/")[1:3])
issues = world.setdefault("issues", {}).setdefault(repo, [])
labels = world.setdefault("labels", {}).setdefault(repo, [])
if path.endswith("/labels") and "/issues/" not in path and method == "GET":
    out = [{"name": n} for n in labels]
elif path.endswith("/labels") and "/issues/" not in path and method == "POST":
    labels.append(body["name"]); out = {"name": body["name"]}
elif path.endswith("/issues") and method == "GET":
    out = [i for i in issues if i["state"] == "open" and any(l["name"] == "content-freshness" for l in i["labels"])]
elif path.endswith("/issues") and method == "POST":
    num = max([i["number"] for i in issues], default=0) + 1
    issue = {"number": num, "title": body["title"], "body": body["body"], "state": "open",
             "labels": [{"name": n} for n in body.get("labels", [])], "html_url": f"https://github.com/{repo}/issues/{num}"}
    issues.append(issue); out = issue
elif "/issues/" in path and method == "PATCH":
    num = int(path.rsplit("/", 1)[1]); issue = next(i for i in issues if i["number"] == num)
    if "labels" in body: body["labels"] = [{"name": n} for n in body["labels"]]
    issue.update(body); out = issue
elif "/issues/" in path and method == "GET":
    num = int(path.rsplit("/", 1)[1]); out = next(i for i in issues if i["number"] == num)
else:
    print("fake gh: unhandled", method, path, file=sys.stderr); save(); sys.exit(1)
save(); print(json.dumps(out))
'''

LONG = ' '.join(f'Sentence number {i} explains how the tool behaves in a stable way.' for i in range(60))


def page(text):
    return 200, f'<html><head><title>t</title><script>var x={hash(text)}</script></head><body><nav>Menu Home Docs</nav><main><p>{text}</p></main><footer>© 2026</footer></body></html>'


@pytest.fixture
def env(tmp_path, monkeypatch):
    server = ThreadingHTTPServer(('127.0.0.1', 0), Site)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    PAGES.clear()
    PAGES['/docs/work-iq'] = page('Work IQ reasons over mail and calendar. ' + LONG)
    PAGES['/docs/stable'] = page('A page that does not change. ' + LONG)
    PAGES['/llms.txt'] = (200, f'- [Intro]({base}/docs/intro)\n- [Agents]({base}/docs/agents)\n')
    repo = tmp_path / 'aleph'
    lib = repo / 'content' / 'library-current'
    (lib / 'work-iq-pilot').mkdir(parents=True)
    (lib / 'work-iq-pilot' / 'article.md').write_text(
        f'# Build a work-context pilot\n\nMicrosoft documents Work IQ. [Work IQ API overview]({base}/docs/work-iq)\n\nAlso see [stable]({base}/docs/stable) and [our site](https://possibnow.substack.com/p/x).\n')
    (lib / 'other-page').mkdir()
    (lib / 'other-page' / 'article.md').write_text(f'# Other\n\nOnly [stable]({base}/docs/stable).\n')
    bin_dir = tmp_path / 'bin'; bin_dir.mkdir()
    (bin_dir / 'gh').write_text(FAKE_GH); (bin_dir / 'gh').chmod(0o755)
    world = tmp_path / 'world.json'; world.write_text('{}')
    monkeypatch.setenv('PATH', f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv('FAKE_WORLD', str(world))
    config = tmp_path / 'freshness.json'
    config.write_text(json.dumps({
        'watches': [{
            'name': 'PossibNow library', 'title': 'PossibNow library update', 'auto': True,
            'repo': {'name': 'Aleph', 'path': str(repo), 'github': 'PossibLaw/aleph'},
            'content': ['content/library-current/*/article.md'], 'scope': ['content/library-current/'],
            'ignore_hosts': ['possibnow.substack.com'],
            'inventories': [{'name': 'Vendor docs', 'index': f'{base}/llms.txt'}],
            'republish': 'Refresh the article\'s Substack review draft; Sal updates the live post.',
        }],
    }))
    yield {'base': base, 'repo': repo, 'world': world, 'config': config, 'state': tmp_path / 'state.json', 'report': tmp_path / 'report.md'}
    server.shutdown()


def run(env, *extra):
    return subprocess.run([sys.executable, str(TOOL), '--config', str(env['config']), '--state', str(env['state']), '--report', str(env['report']), *extra],
                          capture_output=True, text=True, timeout=120)


def issues(env):
    return json.loads(env['world'].read_text()).get('issues', {}).get('PossibLaw/aleph', [])


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    return mod


def test_first_run_records_a_baseline_and_files_nothing(env):
    res = run(env)
    assert res.returncode == 0, res.stderr
    assert issues(env) == []
    state = json.loads(env['state'].read_text())
    assert f"{env['base']}/docs/work-iq" in state['sources']
    assert not any('substack.com' in u for u in state['sources']), 'own site is ignored'


def test_a_real_change_files_a_work_order_the_dispatcher_accepts(env):
    run(env)
    PAGES['/docs/work-iq'] = page('Work IQ now also reads Teams chats and Planner tasks. Application permissions are supported. ' + LONG.replace('stable way', 'new way'))
    res = run(env)
    assert res.returncode == 0, res.stderr
    [issue] = issues(env)
    body = issue['body']
    assert issue['title'] == 'PossibNow library update'
    assert {l['name'] for l in issue['labels']} >= {'content-freshness', 'agent-task', 'auto-ok'}
    assert '**Owner:** Agent' in body
    assert '`content/library-current/work-iq-pilot/article.md`' in body
    assert f"{env['base']}/docs/work-iq" in body and 'Teams chats' in body, 'says what changed in the source'
    assert 'other-page' not in body, 'only articles citing a changed source are listed'
    assert 'Closes #' in body and 'Substack review draft' in body and 'Skipped and why' in body
    d = module(DISPATCH, 'dispatch_for_freshness')
    repo = {'name': 'Aleph', 'path': str(env['repo']), 'allowed_paths': ['content/']}
    assert d.reject_reason(issue, repo, ['agent-task', 'auto-ok']) is None, 'the nightly dispatcher must be able to start it'


def test_cosmetic_changes_are_ignored(env):
    run(env)
    PAGES['/docs/work-iq'] = page('Work IQ reasons over mail and calendar. ' + LONG + ' Updated.')  # one word and a new script hash
    run(env)
    assert issues(env) == []


def test_a_link_is_dead_only_after_two_failed_weeks(env):
    run(env)
    PAGES['/docs/stable'] = (404, 'gone')
    run(env)
    assert issues(env) == [], 'one failure may be an outage'
    run(env)
    [issue] = issues(env)
    assert 'dead' in issue['body'].lower() and '404' in issue['body']
    assert '`content/library-current/other-page/article.md`' in issue['body']


def test_findings_stay_listed_until_the_issue_closes(env):
    run(env)
    PAGES['/docs/work-iq'] = page('Work IQ now also reads Teams chats and Planner tasks. Application permissions are supported. ' + LONG.replace('stable way', 'new way'))
    run(env)
    run(env)  # nothing new this week, issue still open
    [issue] = issues(env)
    assert 'Teams chats' in issue['body'], 'an unhandled change is not dropped'
    w = json.loads(env['world'].read_text()); w['issues']['PossibLaw/aleph'][0]['state'] = 'closed'; env['world'].write_text(json.dumps(w))
    run(env)
    assert [i for i in issues(env) if i['state'] == 'open'] == [], 'handled findings are cleared once the issue is closed'


def test_new_vendor_doc_pages_are_reported(env):
    run(env)
    PAGES['/llms.txt'] = (200, PAGES['/llms.txt'][1] + f"- [Routines]({env['base']}/docs/routines)\n")
    run(env)
    [issue] = issues(env)
    assert f"{env['base']}/docs/routines" in issue['body'] and 'Vendor docs' in issue['body']


def test_dry_run_writes_nothing(env):
    run(env)
    PAGES['/docs/work-iq'] = page('Work IQ now also reads Teams chats and Planner tasks. Application permissions are supported. ' + LONG.replace('stable way', 'new way'))
    before = env['state'].read_text()
    res = run(env, '--dry-run')
    assert res.returncode == 0, res.stderr
    assert issues(env) == [] and env['state'].read_text() == before
    assert 'work-iq-pilot' in res.stdout


def test_bad_config_is_reported_not_fatal_to_the_nightly_job(env):
    env['config'].write_text('{not json')
    res = run(env)
    assert res.returncode == 2 and 'BLOCKED' in res.stderr
