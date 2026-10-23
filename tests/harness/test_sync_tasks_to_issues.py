"""scripts/sync-tasks-to-issues.py: repo .agent/TASKS.md rows → GitHub issues (one way).

A fake `gh` on PATH records every call in a JSON world file; nothing reaches GitHub.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'scripts' / 'sync-tasks-to-issues.py'

FAKE_GH = r'''#!/usr/bin/env python3
import json, sys, os
world_path = os.environ["FAKE_GH_WORLD"]
world = json.load(open(world_path))
args = sys.argv[1:]
world.setdefault("calls", []).append(args)
if world.get("fail_next", 0) > 0:
    world["fail_next"] -= 1; json.dump(world, open(world_path, "w"), indent=1)
    print("Post https://api.github.com/x: net/http: TLS handshake timeout", file=sys.stderr); sys.exit(1)
def save():
    json.dump(world, open(world_path, "w"), indent=1)
if args[:2] == ["project", "item-add"]:
    url = args[args.index("--url") + 1]
    world.setdefault("board_items", []).append(url)
    save(); print(json.dumps({"id": "PVTI_" + str(len(world["board_items"]))})); sys.exit(0)
if args[:1] != ["api"]:
    save(); print("{}"); sys.exit(0)
method = "GET"
if "--method" in args:
    method = args[args.index("--method") + 1]
path = next(a for a in args[1:] if not a.startswith("-") and a not in (method,)).split("?")[0]
body = json.load(sys.stdin) if "--input" in args else {}
repo = "/".join(path.split("/")[1:3])
issues = world.setdefault("issues", {}).setdefault(repo, [])
labels = world.setdefault("labels", {}).setdefault(repo, ["bug"])
if path.endswith("/labels") and method == "GET":
    out = [{"name": n} for n in labels]
elif path.endswith("/labels") and method == "POST":
    labels.append(body["name"]); out = {"name": body["name"]}
elif "/issues/" in path and method == "PATCH":
    num = int(path.rsplit("/", 1)[1])
    issue = next(i for i in issues if i["number"] == num)
    issue.update(body); out = issue
elif "/issues/" in path and path.endswith("/comments") and method == "POST":
    out = {"id": 1}
elif path.endswith("/issues") and method == "GET":
    out = [i for i in issues if any(l["name"] == "agent-task" for l in i["labels"])]
elif path.endswith("/issues") and method == "POST":
    if body.get("title") == world.get("fail_title"):
        save(); print("HTTP 422: Validation Failed", file=sys.stderr); sys.exit(1)
    num = max([i["number"] for i in issues], default=0) + 1
    issue = {"number": num, "title": body["title"], "body": body["body"], "state": "open",
             "labels": [{"name": n} for n in body.get("labels", [])], "html_url": f"https://github.com/{repo}/issues/{num}"}
    issues.append(issue); out = issue
else:
    print(f"fake gh: unhandled {method} {path}", file=sys.stderr); save(); sys.exit(1)
save(); print(json.dumps(out))
'''

REGISTER = """# Register

## Open items (October 23, 2026)

Intro paragraph.

### A. Waiting on Sal

| ID | Item | Owner | State | Done means |
| --- | --- | --- | --- | --- |
| BL-A1 | Name the next round and its order | Sal | OPEN. Waiting since October 1 | Order recorded. This leads to the next round, which leads to launch, which gets me paying users. |
| BL-A2 | Pay the vendor invoice | Sal | OPEN | card number 4111 1111 1111 1111 on file |
| BL-A3 | Old item | Sal | DONE October 22 | Shipped |

### B. Plain

| # | Task | Owner | Notes |
| --- | --- | --- | --- |
| E1 | Send the agreement to the client | Sal | File `Master-Agreement-TEMPLATE.docx` in Downloads (has bank details in Exhibit A: never copy) |
| | Row without an identifier | Agent | should be reported |

## Older section

| ID | Item |
| --- | --- |
| OLD1 | must not be synced |
"""


def module():
    spec = importlib.util.spec_from_file_location('sync_tasks', TOOL)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses need the module registered
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def world(tmp_path, monkeypatch):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    gh = bin_dir / 'gh'
    gh.write_text(FAKE_GH)
    gh.chmod(0o755)
    world_path = tmp_path / 'world.json'
    world_path.write_text('{}')
    monkeypatch.setenv('PATH', f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv('FAKE_GH_WORLD', str(world_path))
    repo = tmp_path / 'alpha'
    (repo / '.agent').mkdir(parents=True)
    (repo / '.agent' / 'TASKS.md').write_text(REGISTER)
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({
        'label': 'agent-task',
        'repos': [{'name': 'alpha', 'path': str(repo), 'github': 'Owner/alpha'}],
        'board': {'enabled': False},
    }))
    return {'path': world_path, 'repo': repo, 'config': config, 'state': tmp_path / 'state.json', 'summary': tmp_path / 'summary.md'}


def run(world, *extra):
    cmd = [sys.executable, str(TOOL), '--config', str(world['config']), '--state', str(world['state']),
           '--summary', str(world['summary']), *extra]
    return subprocess.run(cmd, capture_output=True, text=True)


def read_world(world):
    return json.loads(world['path'].read_text())


# ---- parsing ----------------------------------------------------------------

def test_parse_register_reads_only_first_section_and_identified_rows():
    rows = module().parse_register(REGISTER)
    ids = [r.id for r in rows]
    assert ids == ['BL-A1', 'BL-A2', 'BL-A3', 'E1']
    assert rows[0].section == 'A. Waiting on Sal'
    assert rows[0].cells['Item'] == 'Name the next round and its order'


def test_parse_register_reports_rows_without_an_id():
    missing = module().rows_without_id(REGISTER)
    assert len(missing) == 1 and 'Row without an identifier' in missing[0]


def test_done_rows_are_detected_from_the_state_cell():
    rows = {r.id: r for r in module().parse_register(REGISTER)}
    assert rows['BL-A3'].done is True
    assert rows['BL-A1'].done is False
    assert rows['E1'].done is False  # no state column: open


def test_privacy_filter_blocks_card_numbers_but_allows_file_names():
    m = module()
    rows = {r.id: r for r in m.parse_register(REGISTER)}
    assert m.privacy_violations(rows['BL-A2'].text)
    assert not m.privacy_violations(rows['E1'].text)
    assert not m.privacy_violations('23 untracked `*.bak.20260824-171806` files and commit 46a05e654 and PR #703')
    assert m.privacy_violations('routing number 021000021') and m.privacy_violations('4111-1111-1111-1111')


def test_render_includes_marker_source_and_flywheel_line():
    m = module()
    rows = {r.id: r for r in m.parse_register(REGISTER)}
    title, body = m.render(rows['BL-A1'], 'alpha')
    assert title == '[BL-A1] Name the next round and its order'
    assert '<!-- agent-task:alpha:BL-A1 sha:' in body
    assert 'This leads to the next round' in body
    assert '.agent/TASKS.md' in body
    _, body_e1 = m.render(rows['E1'], 'alpha')
    assert 'UNCONFIRMED' in body_e1 and 'FW01' in body_e1


# ---- end to end with the fake gh ----------------------------------------------

def test_first_run_creates_issues_with_label_and_skips_private_rows(world):
    res = run(world)
    assert res.returncode == 0, res.stderr
    w = read_world(world)
    titles = sorted(i['title'] for i in w['issues']['Owner/alpha'])
    assert titles == ['[BL-A1] Name the next round and its order', '[E1] Send the agreement to the client']
    assert 'agent-task' in w['labels']['Owner/alpha']
    assert all(i['labels'] == [{'name': 'agent-task'}] for i in w['issues']['Owner/alpha'])
    summary = world['summary'].read_text()
    assert 'BL-A2' in summary and 'card' in summary.lower() or 'private' in summary.lower()
    assert 'Row without an identifier' in summary


def test_second_run_is_idempotent(world):
    run(world)
    before = json.dumps(read_world(world)['issues'], sort_keys=True)
    res = run(world)
    assert res.returncode == 0, res.stderr
    assert json.dumps(read_world(world)['issues'], sort_keys=True) == before
    assert 'created 0' in world['summary'].read_text()


def test_prose_change_updates_the_issue(world):
    run(world)
    tasks = world['repo'] / '.agent' / 'TASKS.md'
    tasks.write_text(tasks.read_text().replace('Name the next round and its order', 'Name the next round'))
    run(world)
    titles = [i['title'] for i in read_world(world)['issues']['Owner/alpha']]
    assert '[BL-A1] Name the next round' in titles and '[BL-A1] Name the next round and its order' not in titles


def test_row_marked_done_closes_the_issue_and_vanished_row_closes_with_comment(world):
    run(world)
    tasks = world['repo'] / '.agent' / 'TASKS.md'
    text = tasks.read_text().replace('| Sal | OPEN. Waiting since October 1 |', '| Sal | DONE October 23 |')
    text = text.replace('| E1 | Send the agreement to the client | Sal | File `Master-Agreement-TEMPLATE.docx` in Downloads (has bank details in Exhibit A: never copy) |\n', '')
    tasks.write_text(text)
    run(world)
    w = read_world(world)
    states = {i['title'].split(']')[0][1:]: i['state'] for i in w['issues']['Owner/alpha']}
    assert states == {'BL-A1': 'closed', 'E1': 'closed'}
    assert any('/comments' in ' '.join(c) for c in w['calls'])


def test_issue_closed_on_github_is_reported_as_drift_not_reopened(world):
    run(world)
    w = read_world(world)
    w['issues']['Owner/alpha'][0]['state'] = 'closed'
    world['path'].write_text(json.dumps(w))
    run(world)
    w = read_world(world)
    assert w['issues']['Owner/alpha'][0]['state'] == 'closed'
    summary = world['summary'].read_text()
    assert 'drift' in summary.lower() and 'closed on GitHub' in summary


def test_issue_edited_on_github_is_reported_as_drift(world):
    run(world)
    w = read_world(world)
    w['issues']['Owner/alpha'][0]['body'] += '\nhand edit'
    world['path'].write_text(json.dumps(w))
    run(world)
    assert 'edited on GitHub' in world['summary'].read_text()


def test_dry_run_writes_nothing_to_github(world):
    res = run(world, '--dry-run')
    assert res.returncode == 0, res.stderr
    w = read_world(world)
    assert not w.get('issues', {}).get('Owner/alpha')
    assert 'would create 2' in res.stdout


def test_only_flag_limits_to_one_repo(world, tmp_path):
    cfg = json.loads(world['config'].read_text())
    cfg['repos'].append({'name': 'beta', 'path': str(tmp_path / 'nowhere'), 'github': 'Owner/beta'})
    world['config'].write_text(json.dumps(cfg))
    res = run(world, '--only', 'alpha')
    assert res.returncode == 0, res.stderr
    assert 'beta' not in world['summary'].read_text()


def test_board_step_is_skipped_while_disabled(world):
    run(world)
    calls = read_world(world)['calls']
    assert not any('graphql' in ' '.join(c) for c in calls)
    assert 'board: off' in world['summary'].read_text()


def test_transient_gh_failure_is_retried(world):
    w = read_world(world); w['fail_next'] = 2; world['path'].write_text(json.dumps(w))
    res = run(world)
    assert res.returncode == 0, res.stderr
    titles = sorted(i['title'] for i in read_world(world)['issues']['Owner/alpha'])
    assert len(titles) == 2
    assert 'Errors' not in world['summary'].read_text()


def test_persistent_failure_on_one_row_does_not_abort_the_others(world):
    w = read_world(world); w['fail_title'] = '[BL-A1] Name the next round and its order'; world['path'].write_text(json.dumps(w))
    res = run(world)
    assert res.returncode == 0, res.stderr
    titles = [i['title'] for i in read_world(world)['issues']['Owner/alpha']]
    assert titles == ['[E1] Send the agreement to the client']
    summary = world['summary'].read_text()
    assert 'BL-A1' in summary and 'Errors' in summary and '422' in summary


def enable_board(world):
    cfg = json.loads(world['config'].read_text())
    cfg['board'] = {'enabled': True, 'owner': 'Owner', 'number': 1}
    world['config'].write_text(json.dumps(cfg))


def test_board_step_adds_every_open_synced_issue_once(world):
    enable_board(world)
    run(world)
    w = read_world(world)
    assert sorted(w['board_items']) == ['https://github.com/Owner/alpha/issues/1', 'https://github.com/Owner/alpha/issues/2']
    assert 'board: added 2' in world['summary'].read_text()
    run(world)
    assert len(read_world(world)['board_items']) == 2, 'already-added issues must not be re-added'
    assert 'board: added 0' in world['summary'].read_text()


def test_board_step_adds_issues_that_existed_before_the_board_was_enabled(world):
    run(world)  # issues created with the board off
    enable_board(world)
    run(world)
    assert len(read_world(world)['board_items']) == 2


def test_board_failure_is_reported_not_fatal(world):
    enable_board(world)
    w = read_world(world); w['fail_next'] = 0; world['path'].write_text(json.dumps(w))
    # make item-add fail persistently by pointing at a stub that rejects: simulate via fail_next large after creates
    run(world)  # first run adds fine
    w = read_world(world); w['fail_next'] = 50; world['path'].write_text(json.dumps(w))
    tasks = world['repo'] / '.agent' / 'TASKS.md'
    tasks.write_text(tasks.read_text().replace('| BL-A3 | Old item | Sal | DONE October 22 | Shipped |', '| BL-A3 | Old item | Sal | DONE October 22 | Shipped |\n| BL-A4 | New item | Sal | OPEN | x |'))
    res = run(world)
    assert res.returncode == 0, res.stderr
    assert 'Errors (board)' in world['summary'].read_text() or 'Errors' in world['summary'].read_text()

