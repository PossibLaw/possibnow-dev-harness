#!/usr/bin/env python3
"""Mirror open labelled GitHub issues into one TickTick list, idempotently.

Usage:
    sync-issues-to-ticktick.py --config PATH [--dry-run] [--state PATH]

Each open issue carrying the configured label becomes one task in the configured list
(created when missing). The task title is the issue title; the content carries a marker
`agent-task:<repo>#<n>` and the issue link; `priority` comes from the issue labels through
the config's `priority` map (keys are label names plus `default`; TickTick values 0 none,
1 low, 3 medium, 5 high, which its Eisenhower matrix reads as quadrants). Closed issues
complete their task. Nothing is deleted.

Config (JSON): {"list": "Agent tasks", "label": "agent-task",
  "priority": {"urgent": 5, "default": 3, "maintenance": 0},
  (or the Eisenhower form: {"urgent+important": 5, "important": 3, "urgent": 1, "default": 0, "maintenance": 0})
  "repos": [{"name": "Aleph", "github": "Owner/repo"}, ...]}

Environment: TICKTICK_TOKEN (required; personal API token or OAuth access token),
TICKTICK_BASE_URL (default https://api.ticktick.com). GitHub through `gh api` (REST).
Standard library only. Exit 2 on a bad config or a missing token; 0 otherwise, with
per-repo errors in the summary.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

MARKER_RE = re.compile(r"agent-task:(?P<repo>[^#\s]+)#(?P<num>\d+)")


class TickTick:
    def __init__(self, token: str, base: str, dry_run: bool):
        self.token, self.base, self.dry_run = token, base.rstrip("/"), dry_run
        self.writes = 0

    def call(self, method: str, path: str, payload: dict | None = None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"TickTick {method} {path}: HTTP {exc.code} {exc.read().decode('utf-8', 'replace')[:160]}") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"TickTick {method} {path}: {exc}") from None

    def list_id(self, name: str) -> str | None:
        for p in self.call("GET", "/open/v1/project"):
            if p.get("name") == name:
                return p["id"]
        if self.dry_run:
            return None
        return self.call("POST", "/open/v1/project", {"name": name, "kind": "TASK"})["id"]

    def open_tasks(self, pid: str) -> list[dict]:
        return self.call("GET", f"/open/v1/project/{pid}/data").get("tasks", [])

    def create(self, pid: str, title: str, content: str, priority: int) -> dict:
        self.writes += 1
        return self.call("POST", "/open/v1/task", {"projectId": pid, "title": title, "content": content, "priority": priority})

    def update(self, task: dict, **fields) -> dict:
        self.writes += 1
        return self.call("POST", f"/open/v1/task/{task['id']}", {"id": task["id"], "projectId": task["projectId"], **fields})

    def complete(self, task: dict):
        self.writes += 1
        return self.call("POST", f"/open/v1/project/{task['projectId']}/task/{task['id']}/complete")


def gh_issues(repo: str, label: str) -> list[dict]:
    out, page = [], 1
    while True:
        res = subprocess.run(["gh", "api", "--method", "GET", f"repos/{repo}/issues?state=all&labels={label}&per_page=100&page={page}"],
                             capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"gh api issues {repo}: {res.stderr.strip()[:160]}")
        batch = json.loads(res.stdout or "[]")
        # The API filters by label; check again so a proxy or stub that ignores the query cannot widen the set.
        out += [i for i in batch if "pull_request" not in i and label in {l.get("name") for l in i.get("labels", []) if isinstance(l, dict)}]
        if len(batch) < 100:
            return out
        page += 1


def priority_for(issue: dict, pmap: dict) -> int:
    names = {l["name"] for l in issue.get("labels", []) if isinstance(l, dict)}
    if "urgent+important" in pmap:
        # Eisenhower map (October 26, 2026): the nightly triage sets `urgent` and `important`.
        urgent, important = "urgent" in names, "important" in names
        if urgent and important:
            return int(pmap["urgent+important"])
        if important:
            return int(pmap.get("important", pmap["default"]))
        if urgent:
            return int(pmap.get("urgent", pmap["default"]))
        return int(pmap["maintenance"]) if "maintenance" in names and "maintenance" in pmap else int(pmap["default"])
    best = None
    for name in names:
        if name in pmap and name != "default":
            val = int(pmap[name])
            best = val if best is None else max(best, val) if val != 0 else best
    if "maintenance" in names and "urgent" not in names:
        return int(pmap.get("maintenance", 0))
    return int(pmap["default"]) if best is None else best


def content_for(repo_name: str, issue: dict) -> str:
    return f"agent-task:{repo_name}#{issue['number']}\n{issue['html_url']}\nSynced from GitHub; edits here are not written back."


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--state", type=Path, default=Path.home() / ".agents" / "ticktick-state.json")
    args = ap.parse_args(argv)
    try:
        cfg = json.loads(args.config.expanduser().read_text(encoding="utf-8"))
        repos, list_name, label, pmap = cfg["repos"], cfg["list"], cfg.get("label", "agent-task"), cfg["priority"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"BLOCKED: bad config {args.config}: {exc}", file=sys.stderr)
        return 2
    token = os.environ.get("TICKTICK_TOKEN", "").strip()
    if not token:
        print("BLOCKED: TICKTICK_TOKEN is not set (load it from the keychain item named in the private config)", file=sys.stderr)
        return 2
    tt = TickTick(token, os.environ.get("TICKTICK_BASE_URL", "https://api.ticktick.com"), args.dry_run)
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    created = updated = completed = would = 0
    errors: list[str] = []
    try:
        pid = tt.list_id(list_name)
        existing = tt.open_tasks(pid) if pid else []
    except RuntimeError as exc:
        print(f"# TickTick sync {now}\n- Errors:\n  - {exc}\n")
        return 0
    by_marker: dict[tuple[str, int], dict] = {}
    for t in existing:
        m = MARKER_RE.search(t.get("content") or "")
        if m:
            by_marker[(m.group("repo"), int(m.group("num")))] = t
    for repo in repos:
        try:
            issues = gh_issues(repo["github"], label)
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        for issue in issues:
            key = (repo["name"], issue["number"])
            task = by_marker.pop(key, None)
            if issue["state"] != "open":
                if task is not None and task.get("status", 0) == 0:
                    if not args.dry_run:
                        try:
                            tt.complete(task)
                        except RuntimeError as exc:
                            errors.append(str(exc)); continue
                    completed += 1
                continue
            title, content, prio = issue["title"], content_for(repo["name"], issue), priority_for(issue, pmap)
            if task is None:
                if args.dry_run:
                    would += 1
                    continue
                try:
                    tt.create(pid, title, content, prio)
                    created += 1
                except RuntimeError as exc:
                    errors.append(f"{repo['name']}#{issue['number']}: {exc}")
                continue
            fields = {}
            if task.get("title") != title:
                fields["title"] = title
            if int(task.get("priority", 0)) != prio:
                fields["priority"] = prio
            if fields:
                if not args.dry_run:
                    try:
                        tt.update(task, **fields)
                    except RuntimeError as exc:
                        errors.append(f"{repo['name']}#{issue['number']}: {exc}"); continue
                updated += 1
    if args.dry_run:
        line = f"ticktick: would create {would}, update {updated}, complete {completed} in \"{list_name}\""
    else:
        line = f"ticktick: created {created}, updated {updated}, completed {completed} in \"{list_name}\" ({len(existing)} open before)"
    out = [f"# TickTick sync {'(dry run) ' if args.dry_run else ''}{now}", line]
    if errors:
        out.append("- Errors:")
        out += [f"  - {e}" for e in errors]
    print("\n".join(out))
    if not args.dry_run:
        args.state.expanduser().parent.mkdir(parents=True, exist_ok=True)
        args.state.expanduser().write_text(json.dumps({"ran": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "list_id": pid,
                                                        "created": created, "updated": updated, "completed": completed, "errors": errors}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
