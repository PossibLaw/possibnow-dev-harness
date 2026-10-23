"""scripts/sync-issues-to-ticktick.py: open agent-task issues → one TickTick list, idempotently.

A fake TickTick API (http.server in a thread) and a fake `gh` on PATH; nothing leaves the test.
"""
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'scripts' / 'sync-issues-to-ticktick.py'

FAKE_GH = r'''#!/usr/bin/env python3
import json, sys, os
world = json.load(open(os.environ["FAKE_GH_WORLD"])); args = sys.argv[1:]
path = next(a for a in args[1:] if not a.startswith("-") and a != "GET").split("?")[0]
repo = "/".join(path.split("/")[1:3])
state = "open"
q = sys.argv[-1] if "?" in sys.argv[-1] else ""
if "state=all" in " ".join(args): state = "all"
issues = world["issues"].get(repo, [])
print(json.dumps([i for i in issues if state == "all" or i["state"] == "open"]))
'''


class FakeTickTick(BaseHTTPRequestHandler):
    store = {"projects": [{"id": "p1", "name": "Tasks"}], "tasks": {}, "calls": [], "auth": []}

    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def log_message(self, *a):
        pass

    def do_GET(self):
        s = self.store; s["calls"].append(("GET", self.path)); s["auth"].append(self.headers.get("Authorization"))
        if self.path == "/open/v1/project":
            return self._send(200, s["projects"])
        if self.path.endswith("/data"):
            pid = self.path.split("/")[4]
            return self._send(200, {"project": next(p for p in s["projects"] if p["id"] == pid), "tasks": [t for t in s["tasks"].values() if t["projectId"] == pid and t["status"] == 0], "columns": []})
        self._send(404, {})

    def do_POST(self):
        s = self.store; body = self._body(); s["calls"].append(("POST", self.path, body))
        if self.path == "/open/v1/project":
            p = {"id": f"p{len(s['projects']) + 1}", "name": body["name"]}; s["projects"].append(p); return self._send(200, p)
        if self.path == "/open/v1/task":
            tid = f"t{len(s['tasks']) + 1}"; t = {"id": tid, "status": 0, **body}; s["tasks"][tid] = t; return self._send(200, t)
        if self.path.endswith("/complete"):
            tid = self.path.split("/")[6]; s["tasks"][tid]["status"] = 2; return self._send(200, {})
        if self.path.startswith("/open/v1/task/"):
            tid = self.path.split("/")[4]; s["tasks"][tid].update(body); return self._send(200, s["tasks"][tid])
        self._send(404, {})


@pytest.fixture
def api():
    FakeTickTick.store = {"projects": [{"id": "p1", "name": "Tasks"}], "tasks": {}, "calls": [], "auth": []}
    srv = HTTPServer(("127.0.0.1", 0), FakeTickTick)
    th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def issue(repo, num, labels, title, state="open"):
    return {"number": num, "title": f"[X{num}] {title}", "state": state, "html_url": f"https://github.com/{repo}/issues/{num}",
            "labels": [{"name": l} for l in labels], "body": "x"}


@pytest.fixture
def world(tmp_path, monkeypatch, api):
    bin_dir = tmp_path / 'bin'; bin_dir.mkdir()
    gh = bin_dir / 'gh'; gh.write_text(FAKE_GH); gh.chmod(0o755)
    wp = tmp_path / 'gh-world.json'
    wp.write_text(json.dumps({"issues": {"Owner/alpha": [
        issue("Owner/alpha", 1, ["agent-task", "urgent"], "urgent thing"),
        issue("Owner/alpha", 2, ["agent-task"], "important thing"),
        issue("Owner/alpha", 3, ["agent-task", "maintenance"], "tidy"),
        issue("Owner/alpha", 4, ["bug"], "not synced"),
    ]}}))
    monkeypatch.setenv('PATH', f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv('FAKE_GH_WORLD', str(wp))
    monkeypatch.setenv('TICKTICK_BASE_URL', api)
    monkeypatch.setenv('TICKTICK_TOKEN', 'test-token')
    config = tmp_path / 'ticktick.json'
    config.write_text(json.dumps({"list": "Agent tasks", "label": "agent-task",
                                  "priority": {"urgent": 5, "default": 3, "maintenance": 0},
                                  "repos": [{"name": "alpha", "github": "Owner/alpha"}]}))
    return {'gh': wp, 'config': config, 'state': tmp_path / 'state.json'}


def run(world, *extra):
    return subprocess.run([sys.executable, str(TOOL), '--config', str(world['config']), '--state', str(world['state']), *extra], capture_output=True, text=True)


def tasks():
    return list(FakeTickTick.store["tasks"].values())


def test_creates_the_list_once_and_one_task_per_open_issue_with_quadrant_priority(world):
    res = run(world)
    assert res.returncode == 0, res.stderr
    names = [p["name"] for p in FakeTickTick.store["projects"]]
    assert names == ["Tasks", "Agent tasks"]
    by_title = {t["title"]: t for t in tasks()}
    assert set(by_title) == {"[X1] urgent thing", "[X2] important thing", "[X3] tidy"}
    assert by_title["[X1] urgent thing"]["priority"] == 5
    assert by_title["[X2] important thing"]["priority"] == 3
    assert by_title["[X3] tidy"]["priority"] == 0
    assert all(t["projectId"] == "p2" for t in tasks())
    assert "https://github.com/Owner/alpha/issues/1" in by_title["[X1] urgent thing"]["content"]
    assert "agent-task:alpha#1" in by_title["[X1] urgent thing"]["content"]
    assert all(a == "Bearer test-token" for a in FakeTickTick.store["auth"])
    assert "created 3" in res.stdout


def test_second_run_changes_nothing(world):
    run(world)
    before = json.dumps(FakeTickTick.store["tasks"], sort_keys=True)
    res = run(world)
    assert res.returncode == 0, res.stderr
    assert json.dumps(FakeTickTick.store["tasks"], sort_keys=True) == before
    assert "created 0" in res.stdout and "updated 0" in res.stdout
    assert len([p for p in FakeTickTick.store["projects"] if p["name"] == "Agent tasks"]) == 1


def test_label_or_title_change_updates_the_task(world):
    run(world)
    w = json.loads(world['gh'].read_text())
    i2 = next(i for i in w["issues"]["Owner/alpha"] if i["number"] == 2)
    i2["labels"].append({"name": "urgent"}); i2["title"] = "[X2] important thing, now urgent"
    world['gh'].write_text(json.dumps(w))
    res = run(world)
    t = next(t for t in tasks() if "agent-task:alpha#2" in t["content"])
    assert t["priority"] == 5 and t["title"] == "[X2] important thing, now urgent"
    assert "updated 1" in res.stdout


def test_closed_issue_completes_the_task(world):
    run(world)
    w = json.loads(world['gh'].read_text())
    next(i for i in w["issues"]["Owner/alpha"] if i["number"] == 3)["state"] = "closed"
    world['gh'].write_text(json.dumps(w))
    res = run(world)
    t = next(t for t in tasks() if "agent-task:alpha#3" in t["content"])
    assert t["status"] == 2
    assert "completed 1" in res.stdout


def test_missing_token_is_a_clear_failure_without_calls(world, monkeypatch):
    monkeypatch.delenv('TICKTICK_TOKEN')
    res = run(world)
    assert res.returncode == 2 and "TICKTICK_TOKEN" in res.stderr
    assert FakeTickTick.store["calls"] == []


def test_dry_run_reads_but_writes_nothing(world):
    res = run(world, '--dry-run')
    assert res.returncode == 0, res.stderr
    assert tasks() == [] and all(c[0] == "GET" for c in FakeTickTick.store["calls"])
    assert "would create 3" in res.stdout
