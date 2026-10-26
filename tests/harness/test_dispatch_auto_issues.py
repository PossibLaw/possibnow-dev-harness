"""scripts/dispatch-auto-issues.py: start Orca runs on eligible auto-ok issues, within caps.

Fake `gh` and fake `orca` on PATH record calls in a world file; nothing is started.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'scripts' / 'dispatch-auto-issues.py'

FAKE_GH = r'''#!/usr/bin/env python3
import json, sys, os
wp = os.environ["FAKE_WORLD"]; world = json.load(open(wp)); args = sys.argv[1:]
world.setdefault("calls", []).append(["gh", *args])
def save(): json.dump(world, open(wp, "w"), indent=1)
method = args[args.index("--method") + 1] if "--method" in args else "GET"
path = next(a for a in args[1:] if not a.startswith("-") and a != method).split("?")[0]
body = json.load(sys.stdin) if "--input" in args else {}
if path.endswith("/issues") and method == "GET":
    repo = "/".join(path.split("/")[1:3]); out = world.get("issues", {}).get(repo, [])
elif path.endswith("/pulls") and method == "GET":
    repo = "/".join(path.split("/")[1:3]); out = world.get("pulls", {}).get(repo, [])
elif "/pulls/" in path and method == "PATCH":
    repo = "/".join(path.split("/")[1:3]); num = int(path.rsplit("/", 1)[1])
    pr = next(p for p in world["pulls"][repo] if p["number"] == num); pr.update(body); out = pr
elif "/issues/" in path and path.endswith("/labels") and method == "POST":
    repo = "/".join(path.split("/")[1:3]); num = int(path.split("/")[4])
    world.setdefault("pr_labels", {}).setdefault(f"{repo}#{num}", []).extend(body["labels"]); out = []
elif "/issues/" in path and path.endswith("/comments") and method == "POST":
    out = {"id": 1}
elif path.count("/") == 4 and "/issues/" in path and method == "GET":
    repo = "/".join(path.split("/")[1:3]); num = int(path.rsplit("/", 1)[1])
    if num in world.get("closed", {}).get(repo, []):
        out = {"number": num, "state": "closed"}
    elif any(i["number"] == num for i in world.get("issues", {}).get(repo, [])):
        out = {"number": num, "state": "open"}
    else:
        print("fake gh: 404", path, file=sys.stderr); save(); sys.exit(1)
else:
    print("fake gh: unhandled", method, path, file=sys.stderr); save(); sys.exit(1)
save(); print(json.dumps(out))
'''

FAKE_ORCA = r'''#!/usr/bin/env python3
import json, sys, os
wp = os.environ["FAKE_WORLD"]; world = json.load(open(wp)); args = sys.argv[1:]
world.setdefault("calls", []).append(["orca", *args])
def save(): json.dump(world, open(wp, "w"), indent=1)
if args[:2] == ["worktree", "list"]:
    out = {"ok": True, "result": {"worktrees": world.get("worktrees", [])}}
elif args[:2] == ["repo", "list"]:
    out = {"ok": True, "result": {"repos": world.get("repos", [{"id": "id-alpha", "path": "/repos/alpha"}, {"id": "id-beta", "path": "/repos/beta"}])}}
elif args[:2] == ["worktree", "create"]:
    name = args[args.index("--name") + 1]
    repo = args[args.index("--repo") + 1]
    if "~" in repo or world.get("orca_create_error"):
        # Real Orca: no tilde expansion, and with --json the error goes to stdout, nothing to stderr, exit 1.
        save(); print(json.dumps({"ok": False, "error": {"code": world.get("orca_create_error", "repo_not_found"), "message": "repo_not_found"}})); sys.exit(1)
    issue = int(args[args.index("--issue") + 1])
    wt_path = "/wt/" + name
    if os.environ.get("FAKE_WT_ROOT"):
        import subprocess
        wt_path = os.path.join(os.environ["FAKE_WT_ROOT"], name)
        os.makedirs(wt_path)
        subprocess.run(["git", "init", "-q", "-b", name, wt_path], check=True)
    world.setdefault("worktrees", []).append({"displayName": name, "branch": "refs/heads/" + name, "linkedIssue": issue, "isArchived": False, "path": wt_path, "repoPath": repo})
    out = {"ok": True, "result": {"worktree": {"path": wt_path, "branch": name}} if not world.get("create_without_path") else {}}
else:
    print("fake orca: unhandled", args, file=sys.stderr); save(); sys.exit(1)
save(); print(json.dumps(out))
'''


def issue(repo, num, labels, body, title="task"):
    return {"number": num, "title": f"[X{num}] {title}", "state": "open", "html_url": f"https://github.com/{repo}/issues/{num}",
            "labels": [{"name": l} for l in labels], "body": body}


BODY_OK = "**Source:** `alpha/.agent/TASKS.md`\n- **Owner:** Agent\n- **Task:** fix `src/lib/x.js` and `tests/x.test.js`\n**Flywheel:** This leads to a, which leads to b, which gets me c."
BODY_SAL = "- **Owner:** Sal\n- **Task:** decide `src/lib/x.js`"
BODY_BAD_PATH = "- **Owner:** Agent\n- **Task:** rotate `config/secrets.json`"
BODY_NO_PATH = "- **Owner:** Agent\n- **Task:** think about things"


@pytest.fixture
def world(tmp_path, monkeypatch):
    bin_dir = tmp_path / 'bin'; bin_dir.mkdir()
    for name, src in (('gh', FAKE_GH), ('orca', FAKE_ORCA)):
        f = bin_dir / name; f.write_text(src); f.chmod(0o755)
    wp = tmp_path / 'world.json'
    wp.write_text(json.dumps({"issues": {"Owner/alpha": [
        issue("Owner/alpha", 1, ["agent-task", "auto-ok"], BODY_OK, "safe chore"),
        issue("Owner/alpha", 2, ["agent-task"], BODY_OK, "not opted in"),
        issue("Owner/alpha", 3, ["agent-task", "auto-ok"], BODY_SAL, "sal decides"),
        issue("Owner/alpha", 4, ["agent-task", "auto-ok"], BODY_BAD_PATH, "touches secrets"),
        issue("Owner/alpha", 5, ["agent-task", "auto-ok"], BODY_NO_PATH, "no paths"),
        issue("Owner/alpha", 6, ["agent-task", "auto-ok"], BODY_OK, "second safe chore"),
        issue("Owner/alpha", 7, ["agent-task", "auto-ok"], BODY_OK, "third safe chore"),
    ], "Owner/beta": [issue("Owner/beta", 11, ["agent-task", "auto-ok"], BODY_OK, "beta chore")]},
        "pulls": {"Owner/alpha": [], "Owner/beta": []}}))
    monkeypatch.setenv('PATH', f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv('FAKE_WORLD', str(wp))
    config = tmp_path / 'dispatch.json'
    config.write_text(json.dumps({
        "max_runs": 2, "max_per_repo": 1, "agent": "claude",
        "labels": {"eligible": ["agent-task", "auto-ok"], "pr": "agent-auto"},
        "repos": [{"name": "alpha", "path": "/repos/alpha", "github": "Owner/alpha", "allowed_paths": ["src/", "tests/"]},
                  {"name": "beta", "path": "/repos/beta", "github": "Owner/beta", "allowed_paths": ["src/", "tests/"]}],
        "prompt": "Autonomous run. Complete {issue_url}. Open a DRAFT PR titled '[auto] ...' and label it agent-auto. Never merge or publish."
    }))
    return {'path': wp, 'config': config, 'state': tmp_path / 'state.json', 'report': tmp_path / 'report.md'}


def run(world, *extra):
    return subprocess.run([sys.executable, str(TOOL), '--config', str(world['config']), '--state', str(world['state']), '--report', str(world['report']), *extra], capture_output=True, text=True)


def read(world):
    return json.loads(world['path'].read_text())


def started(world):
    return [c for c in read(world).get('calls', []) if c[:3] == ['orca', 'worktree', 'create']]


def test_starts_only_eligible_issues_within_caps(world):
    res = run(world)
    assert res.returncode == 0, res.stderr
    calls = started(world)
    issues = sorted(int(c[c.index('--issue') + 1]) for c in calls)
    assert issues == [1, 11], 'one per repo, two total: alpha #1 and beta #11'
    report = world['report'].read_text()
    assert '#2' not in report, 'issues that simply lack auto-ok must not be listed one by one'
    assert '1 issue(s) without auto-ok not listed' in report or '1 issues without auto-ok' in report
    assert '#3' in report and 'Sal' in report
    assert '#4' in report and 'config/secrets.json' in report
    assert '#5' in report and 'no path' in report.lower()
    assert '#6' in report and 'cap' in report.lower()


def test_prompt_and_names_mark_the_run_as_autonomous(world):
    run(world)
    call = started(world)[0]
    assert call[call.index('--name') + 1] == 'auto-1'
    prompt = call[call.index('--prompt') + 1]
    assert 'Autonomous run' in prompt and 'https://github.com/Owner/alpha/issues/1' in prompt and 'agent-auto' in prompt
    assert '--agent' in call and call[call.index('--agent') + 1] == 'claude'


def test_running_worktrees_count_against_caps_and_issues_are_not_restarted(world):
    run(world)
    res = run(world)
    assert res.returncode == 0, res.stderr
    assert len(started(world)) == 2, 'second run must not start anything: caps full and issues already running'
    assert 'already running' in world['report'].read_text().lower() or 'cap' in world['report'].read_text().lower()


def test_issue_with_an_open_pr_is_skipped(world):
    w = read(world)
    w['pulls']['Owner/alpha'] = [{"number": 90, "title": "fix", "state": "open", "head": {"ref": "orca/auto-1"}, "body": "Closes #1", "labels": [], "html_url": "https://github.com/Owner/alpha/pull/90"}]
    world['path'].write_text(json.dumps(w))
    run(world)
    issues = sorted(int(c[c.index('--issue') + 1]) for c in started(world))
    assert 1 not in issues and 6 in issues


def test_open_auto_prs_are_flagged_with_label_and_title_prefix(world):
    w = read(world)
    w['pulls']['Owner/alpha'] = [{"number": 90, "title": "fix the thing", "state": "open", "head": {"ref": "orca/auto-1"}, "body": "", "labels": [], "html_url": "https://github.com/Owner/alpha/pull/90"},
                                 {"number": 91, "title": "[auto] already flagged", "state": "open", "head": {"ref": "orca/auto-6"}, "body": "", "labels": [{"name": "agent-auto"}], "html_url": "https://github.com/Owner/alpha/pull/91"}]
    world['path'].write_text(json.dumps(w))
    run(world)
    w = read(world)
    pr90 = next(p for p in w['pulls']['Owner/alpha'] if p['number'] == 90)
    assert pr90['title'] == '[auto] fix the thing'
    assert 'agent-auto' in w.get('pr_labels', {}).get('Owner/alpha#90', [])
    assert 'Owner/alpha#91' not in w.get('pr_labels', {})
    assert '#90' in world['report'].read_text()


def test_tilde_repo_paths_are_expanded_before_orca_sees_them(world, tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    cfg = json.loads(world['config'].read_text())
    cfg['repos'][0]['path'] = '~/alpha'
    world['config'].write_text(json.dumps(cfg))
    res = run(world)
    assert res.returncode == 0, res.stderr
    alpha = [c for c in started(world) if c[c.index('--issue') + 1] == '1']
    assert alpha, 'alpha #1 must start; Orca rejects a literal ~ in path: selectors'
    assert alpha[0][alpha[0].index('--repo') + 1] == f'path:{tmp_path}/alpha'
    assert 'started alpha #1' in world['report'].read_text()


def test_orca_json_error_reaches_the_report(world):
    w = read(world); w['orca_create_error'] = 'repo_not_found'; world['path'].write_text(json.dumps(w))
    res = run(world)
    assert res.returncode == 0, res.stderr
    report = world['report'].read_text()
    assert 'repo_not_found' in report, 'Orca --json writes the error to stdout; the report must carry it'
    assert 'Nothing started' in report


def test_prs_on_the_branch_orca_actually_creates_are_flagged_and_block_a_restart(world):
    # Orca 1.4.240 names the branch auto-<n>, not orca/auto-<n>; both spellings must count.
    w = read(world)
    w['pulls']['Owner/alpha'] = [{"number": 92, "title": "shortlist", "state": "open", "head": {"ref": "auto-1"}, "body": "", "labels": [], "html_url": "https://github.com/Owner/alpha/pull/92"}]
    world['path'].write_text(json.dumps(w))
    run(world)
    w = read(world)
    assert next(p for p in w['pulls']['Owner/alpha'] if p['number'] == 92)['title'] == '[auto] shortlist'
    assert 'agent-auto' in w.get('pr_labels', {}).get('Owner/alpha#92', [])
    assert 1 not in [int(c[c.index('--issue') + 1]) for c in started(world)], 'issue #1 already has an open auto PR'


def test_worktrees_on_the_branch_orca_actually_creates_count_against_caps(world):
    w = read(world)
    w['worktrees'] = [{"displayName": "auto-1", "branch": "refs/heads/auto-1", "linkedIssue": 1, "isArchived": False, "path": "/wt/auto-1", "repoPath": "/repos/alpha"}]
    world['path'].write_text(json.dumps(w))
    run(world)
    issues = sorted(int(c[c.index('--issue') + 1]) for c in started(world))
    assert issues == [11], 'alpha is at its per-repo cap and #1 is already running'


def test_per_repo_cap_counts_worktrees_in_the_shape_orca_really_sends(world):
    # Orca 1.4.240 records carry repoId and git.path (the worktree), never repoPath.
    w = read(world)
    w['worktrees'] = [{"displayName": "auto-1", "branch": "refs/heads/auto-1", "linkedIssue": 1, "isArchived": False,
                       "path": "/wt/auto-1", "repoId": "id-alpha", "git": {"path": "/wt/auto-1", "branch": "refs/heads/auto-1"}}]
    world['path'].write_text(json.dumps(w))
    run(world)
    issues = sorted(int(c[c.index('--issue') + 1]) for c in started(world))
    assert issues == [11], 'alpha already has one running auto worktree, so only beta may start'


def test_auto_worktree_whose_issue_is_closed_no_longer_counts_against_caps(world):
    # October 26, 2026: auto-130 and auto-850 stayed open in Orca after their issues closed,
    # so the next night saw both caps full and would have started nothing.
    w = read(world)
    w['worktrees'] = [{"displayName": "auto-1", "branch": "refs/heads/some-human-branch", "linkedIssue": 1, "isArchived": False, "path": "/wt/auto-1", "repoPath": "/repos/alpha"},
                      {"displayName": "auto-11", "branch": "refs/heads/auto-11", "linkedIssue": 11, "isArchived": False, "path": "/wt/auto-11", "repoPath": "/repos/beta"}]
    w['issues']['Owner/alpha'] = [i for i in w['issues']['Owner/alpha'] if i['number'] != 1]
    w['closed'] = {"Owner/alpha": [1]}
    world['path'].write_text(json.dumps(w))
    res = run(world)
    assert res.returncode == 0, res.stderr
    issues = sorted(int(c[c.index('--issue') + 1]) for c in started(world))
    assert issues == [6], 'alpha #1 is closed so its worktree is finished; beta #11 is open and still running'
    assert 'Running before this pass: 1 auto worktree(s)' in world['report'].read_text()


def test_t6_dispatcher_marks_each_started_worktree(world, tmp_path, monkeypatch):
    monkeypatch.setenv('FAKE_WT_ROOT', str(tmp_path / 'wts'))
    res = run(world)
    assert res.returncode == 0, res.stderr
    m = guard_module()
    marker = m.read_marker(str(tmp_path / 'wts' / 'auto-1'))
    assert marker and marker['repo'] == 'Owner/alpha' and marker['issue'] == 1 and marker['worktree'] == 'auto-1'
    assert m.is_autonomous(str(tmp_path / 'wts' / 'auto-1'))
    assert 'marker' not in world['report'].read_text().lower()


def test_t6_dispatcher_finds_the_worktree_when_orca_omits_the_path(world, tmp_path, monkeypatch):
    monkeypatch.setenv('FAKE_WT_ROOT', str(tmp_path / 'wts'))
    w = read(world); w['create_without_path'] = True; world['path'].write_text(json.dumps(w))
    run(world)
    assert guard_module().read_marker(str(tmp_path / 'wts' / 'auto-11'))


def test_t6_a_marker_failure_is_reported_and_the_run_continues(world):
    res = run(world)  # the default fake reports /wt/auto-<n>, which does not exist
    assert res.returncode == 0, res.stderr
    report = world['report'].read_text()
    assert 'started alpha #1' in report and 'started beta #11' in report
    assert 'marker was not written' in report


def guard_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location('autonomy_for_dispatch', ROOT / 'scripts' / 'guardrails' / 'autonomy.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def test_dry_run_starts_nothing_and_reports(world):
    res = run(world, '--dry-run')
    assert res.returncode == 0, res.stderr
    assert started(world) == []
    assert 'would start' in res.stdout


def test_disabled_config_starts_nothing(world):
    cfg = json.loads(world['config'].read_text()); cfg['enabled'] = False; world['config'].write_text(json.dumps(cfg))
    res = run(world)
    assert res.returncode == 0 and started(world) == [] and 'disabled' in world['report'].read_text().lower()


def test_paths_are_only_tokens_that_exist_in_the_repo(tmp_path):
    m = module()
    repo = tmp_path / 'r'; (repo / 'src' / 'lib').mkdir(parents=True); (repo / 'src' / 'lib' / 'x.js').write_text('')
    body = "fix `src/lib/x.js`, model `qwen/qwen-plus`, keychain `aleph/SLACK_WEBHOOK_URL`, branch `orca/auto-3`, new file `src/lib/new.js`, folder `docs/`"
    assert m.issue_paths(body, repo) == ['docs/', 'src/lib/new.js', 'src/lib/x.js'] or m.issue_paths(body, repo) == ['src/lib/new.js', 'src/lib/x.js']


def test_rows_without_an_owner_line_are_rejected_when_the_text_says_sal_decides(tmp_path):
    m = module()
    repo = {'name': 'alpha', 'path': str(tmp_path), 'allowed_paths': ['src/']}
    (tmp_path / 'src').mkdir()
    labels = [{'name': 'agent-task'}, {'name': 'auto-ok'}]
    needs_sal = {'labels': labels, 'body': "- **Work:** rewrite `src/a.js` once Sal decides the format\n- **Evidence / next:** Sal says go"}
    agent_ok = {'labels': labels, 'body': "- **Work:** tidy `src/a.js`\n- **Evidence / next:** tests pass"}
    assert 'Sal' in (m.reject_reason(needs_sal, repo, ['agent-task', 'auto-ok']) or '')
    assert m.reject_reason(agent_ok, repo, ['agent-task', 'auto-ok']) is None


def module():
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location('dispatch_auto', TOOL)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    return mod

