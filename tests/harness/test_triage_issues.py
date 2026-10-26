"""scripts/triage-issues.py: nightly triage of every open tracked issue, with recommendations.

Sal, October 26, 2026: "We need to triage the issues. Figure out what I need to do ... everything is in
one quadrant until I look at it ... Need recommendations really." Decisions: a morning Slack brief with
the top five decisions; the agent sets `urgent`/`important` and Sal overrides; the top five daily plus a
Monday sweep that closes finished issues.

A fake `gh` plays GitHub and a fake classifier plays Claude; nothing leaves the test.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'scripts' / 'triage-issues.py'

FAKE_GH = r'''#!/usr/bin/env python3
import json, sys, os
from urllib.parse import parse_qs
wp = os.environ["FAKE_WORLD"]; world = json.load(open(wp)); args = sys.argv[1:]
world.setdefault("calls", []).append(args)
def save(): json.dump(world, open(wp, "w"), indent=1)
method = args[args.index("--method") + 1] if "--method" in args else "GET"
full = next(a for a in args[1:] if not a.startswith("-") and a != method)
path, q = full.split("?")[0], {k: v[0] for k, v in parse_qs(full.split("?")[1] if "?" in full else "").items()}
body = json.load(sys.stdin) if "--input" in args else {}
repo = "/".join(path.split("/")[1:3])
issues = world.setdefault("issues", {}).setdefault(repo, [])
def page(items):
    per, n = int(q.get("per_page", 30)), int(q.get("page", 1)); return items[(n - 1) * per: n * per]
if path.endswith("/issues") and method == "GET":
    out = page([i for i in issues if i["state"] == q.get("state", "open") and any(l["name"] == q.get("labels") for l in i["labels"])])
elif path.endswith("/pulls") and method == "GET":
    out = page(world.get("pulls", {}).get(repo, []))
elif path.endswith("/labels") and "/issues/" not in path and method == "GET":
    out = [{"name": n} for n in world.setdefault("repo_labels", {}).setdefault(repo, [])]
elif path.endswith("/labels") and "/issues/" not in path and method == "POST":
    world["repo_labels"].setdefault(repo, []).append(body["name"]); out = {"name": body["name"]}
elif "/issues/" in path and path.endswith("/labels") and method == "POST":
    num = int(path.split("/")[4]); i = next(x for x in issues if x["number"] == num)
    have = {l["name"] for l in i["labels"]}; i["labels"] += [{"name": n} for n in body["labels"] if n not in have]; out = i["labels"]
elif "/issues/" in path and "/labels/" in path and method == "DELETE":
    num = int(path.split("/")[4]); name = path.rsplit("/", 1)[1]; i = next(x for x in issues if x["number"] == num)
    i["labels"] = [l for l in i["labels"] if l["name"] != name]; out = []
elif "/issues/" in path and path.endswith("/comments") and method == "POST":
    world.setdefault("comments", []).append({"repo": repo, "number": int(path.split("/")[4]), "body": body["body"]}); out = {"id": 1}
elif "/issues/" in path and method == "PATCH":
    num = int(path.rsplit("/", 1)[1]); i = next(x for x in issues if x["number"] == num); i.update(body); out = i
else:
    print("fake gh: unhandled", method, path, file=sys.stderr); save(); sys.exit(1)
save(); print(json.dumps(out))
'''

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, re, sys
world = json.load(open(os.environ["FAKE_WORLD"]))
if world.get("classifier_fails"):
    print("boom", file=sys.stderr); sys.exit(1)
prompt = sys.stdin.read()
keys = re.findall(r"^KEY: (\S+)$", prompt, re.M)
log = world.setdefault("prompts", []); log.append(keys); json.dump(world, open(os.environ["FAKE_WORLD"], "w"), indent=1)
answer = [dict(world["verdicts"][k], key=k) for k in keys if k in world["verdicts"]]
print(json.dumps({"type": "result", "is_error": False, "result": "Here you go:\n```json\n" + json.dumps(answer) + "\n```"}))
'''


def issue(repo, n, title, labels=('agent-task',), body='', updated='2026-10-20T00:00:00Z'):
    return {'number': n, 'title': title, 'state': 'open', 'labels': [{'name': l} for l in labels], 'body': body,
            'html_url': f'https://github.com/{repo}/issues/{n}', 'created_at': '2026-10-01T00:00:00Z', 'updated_at': updated}


def decide(question, urgent=False, important=True, why='launch depends on it'):
    return {'outcome': 'decide', 'urgent': urgent, 'important': important, 'why': why,
            'decision': {'question': question, 'options': ['A: go ahead', 'B: wait a week'], 'recommend': 'A'}}


@pytest.fixture
def env(tmp_path, monkeypatch):
    bin_dir = tmp_path / 'bin'; bin_dir.mkdir()
    for name, src in (('gh', FAKE_GH), ('fake-claude', FAKE_CLAUDE)):
        (bin_dir / name).write_text(src); (bin_dir / name).chmod(0o755)
    world = tmp_path / 'world.json'
    world.write_text(json.dumps({
        'issues': {
            'Owner/aleph': [
                issue('Owner/aleph', 1, 'Pick the newsletter platform'),
                issue('Owner/aleph', 2, 'Record the October video'),
                issue('Owner/aleph', 3, 'Tidy the research shelf'),
                issue('Owner/aleph', 4, 'Harvest runner pulls before commit'),
                issue('Owner/aleph', 5, 'Old idea nobody touched', updated='2026-06-01T00:00:00Z'),
                issue('Owner/aleph', 6, 'Already marked urgent by Sal', labels=('agent-task', 'urgent')),
            ],
            'Owner/trazomo': [issue('Owner/trazomo', 10 + i, f'Ruling {i}') for i in range(7)],
        },
        'pulls': {'Owner/aleph': [{'number': 157, 'title': 'TS04: harvest runner fast-forwards main', 'body': 'Closes #4', 'merged_at': '2026-10-26T18:00:00Z',
                                   'updated_at': '2026-10-26T18:00:00Z', 'html_url': 'https://github.com/Owner/aleph/pull/157'}],
                  'Owner/trazomo': []},
        'verdicts': {
            'Owner/aleph#1': decide('Which newsletter platform?', urgent=True, important=True),
            'Owner/aleph#2': {'outcome': 'do', 'urgent': True, 'important': True, 'why': 'publishes Tuesday'},
            'Owner/aleph#3': {'outcome': 'agent', 'urgent': False, 'important': False, 'why': 'files named, no judgment needed'},
            'Owner/aleph#4': {'outcome': 'done', 'urgent': False, 'important': False, 'why': 'PR 157 merged'},
            'Owner/aleph#5': {'outcome': 'stale', 'urgent': False, 'important': False, 'why': 'untouched since June'},
            'Owner/aleph#6': decide('Approve the cover?', urgent=False, important=False, why='minor'),
            **{f'Owner/trazomo#{10 + i}': decide(f'Ruling {i}?', urgent=(i < 2), important=(i % 2 == 0)) for i in range(7)},
        },
    }))
    monkeypatch.setenv('PATH', f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv('FAKE_WORLD', str(world))
    config = tmp_path / 'triage.json'
    config.write_text(json.dumps({
        'label': 'agent-task', 'brief_size': 5, 'batch': 4, 'sweep_day': 'Monday',
        'classifier': {'command': ['fake-claude']},
        'repos': [{'name': 'Aleph', 'github': 'Owner/aleph'}, {'name': 'trazomo', 'github': 'Owner/trazomo'}],
    }))
    return {'world': world, 'config': config, 'state': tmp_path / 'state.json', 'brief': tmp_path / 'brief.md'}


def run(env, *extra, day='Tuesday'):
    return subprocess.run([sys.executable, str(TOOL), '--config', str(env['config']), '--state', str(env['state']), '--brief', str(env['brief']),
                           '--today', day, *extra], capture_output=True, text=True, timeout=60)


def world(env):
    return json.loads(env['world'].read_text())


def labels(env, repo, n):
    return {l['name'] for l in next(i for i in world(env)['issues'][repo] if i['number'] == n)['labels']}


def test_sets_urgent_and_important_labels_from_the_recommendation(env):
    res = run(env)
    assert res.returncode == 0, res.stderr
    assert {'urgent', 'important'} <= labels(env, 'Owner/aleph', 1)
    assert 'urgent' not in labels(env, 'Owner/aleph', 3) and 'important' not in labels(env, 'Owner/aleph', 3)
    assert {'urgent'} <= labels(env, 'Owner/trazomo', 10) and 'important' not in labels(env, 'Owner/trazomo', 11)


def test_issues_are_sent_to_the_classifier_in_batches_with_context(env):
    run(env)
    prompts = world(env)['prompts']
    assert all(len(keys) <= 4 for keys in prompts) and sum(len(k) for k in prompts) == 13
    log = env['state'].read_text()
    assert 'Owner/aleph#4' in log


def test_a_label_sal_set_or_changed_is_never_overridden(env):
    run(env)
    assert 'urgent' in labels(env, 'Owner/aleph', 6), 'Sal marked it urgent before the first triage; the triage does not remove it'
    w = world(env)
    i1 = next(i for i in w['issues']['Owner/aleph'] if i['number'] == 1)
    i1['labels'] = [l for l in i1['labels'] if l['name'] != 'urgent']  # Sal disagrees
    env['world'].write_text(json.dumps(w))
    run(env)
    assert 'urgent' not in labels(env, 'Owner/aleph', 1), 'his override sticks on the next run'


def test_the_brief_names_the_top_five_decisions_with_options_and_a_recommendation(env):
    run(env)
    brief = env['brief'].read_text()
    numbered = [l for l in brief.splitlines() if l[:2] in {f'{n}.' for n in range(1, 10)}]
    assert len(numbered) == 5, brief
    assert numbered[0].startswith('1. Pick the newsletter platform'), 'urgent and important come first, by name'
    assert 'A: go ahead' in brief and 'Recommend A' in brief and 'https://github.com/Owner/aleph/issues/1' in brief
    assert 'Approve the cover?' not in brief, 'neither urgent nor important does not make the top five'
    assert 'Record the October video' in brief, 'things only Sal can do are listed too'
    assert 'Tidy the research shelf' in brief, 'agent-ready work is offered for opt-in'
    assert 'reply' in brief.lower()


def test_the_monday_sweep_closes_finished_issues_backed_by_a_merged_pr(env):
    run(env, day='Tuesday')
    assert next(i for i in world(env)['issues']['Owner/aleph'] if i['number'] == 4)['state'] == 'open', 'only Mondays close'
    run(env, day='Monday')
    w = world(env)
    assert next(i for i in w['issues']['Owner/aleph'] if i['number'] == 4)['state'] == 'closed'
    assert any(c['number'] == 4 and 'TS04: harvest runner fast-forwards main' in c['body'] for c in w['comments'])
    assert next(i for i in w['issues']['Owner/aleph'] if i['number'] == 5)['state'] == 'open', 'stale is proposed, never closed unasked'
    assert 'Old idea nobody touched' in env['brief'].read_text()


def test_done_without_a_merged_pr_is_not_closed(env):
    w = world(env); w['pulls']['Owner/aleph'] = []; env['world'].write_text(json.dumps(w))
    run(env, day='Monday')
    assert next(i for i in world(env)['issues']['Owner/aleph'] if i['number'] == 4)['state'] == 'open'


def test_dry_run_changes_nothing(env):
    res = run(env, '--dry-run', day='Monday')
    assert res.returncode == 0, res.stderr
    w = world(env)
    assert not any(c[:3] == ['api', '--method', 'POST'] or c[:3] == ['api', '--method', 'PATCH'] or c[:3] == ['api', '--method', 'DELETE'] for c in w['calls'])
    assert not env['state'].exists() and 'Pick the newsletter platform' in res.stdout


def test_a_classifier_failure_changes_no_labels_and_says_so(env):
    w = world(env); w['classifier_fails'] = True; env['world'].write_text(json.dumps(w))
    res = run(env)
    assert res.returncode == 0
    assert 'urgent' not in labels(env, 'Owner/aleph', 1)
    assert 'classifier' in env['brief'].read_text().lower()
