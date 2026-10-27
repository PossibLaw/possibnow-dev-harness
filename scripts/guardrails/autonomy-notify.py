#!/usr/bin/env python3
"""Stop hook: tell Sal in Slack the moment an autonomous run finishes or gets stuck.

Sal, October 27, 2026: "I should get a notice when something finishes at that time. Not a day later."
Runs only in a worktree the dispatcher marked (`agent-auto.json`) and only until a person takes the
session over. When the agent ends its turn:
- a pull request for the run exists (head branch is the worktree's branch, or its body names the issue,
  opened after the run started): post the issue and the pull request, by name, ready for review;
- none exists: post that the run stopped without a pull request and quote the agent's last message,
  because it probably needs Sal.
Each outcome is announced once (recorded in the marker); a failed post is retried at the next stop.
The Slack webhook comes from $SLACK_WEBHOOK_URL or the macOS keychain item `aleph/SLACK_WEBHOOK_URL`
and is never printed. This hook never blocks the agent: it always exits 0 and prints nothing.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autonomy import read_marker, write_marker  # noqa: E402


def _gh(path):
    res = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=30)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip()[:200])
    return json.loads(res.stdout or "null")


def _branch(cwd):
    res = subprocess.run(["git", "-C", cwd, "branch", "--show-current"], capture_output=True, text=True, timeout=10)
    return res.stdout.strip() if res.returncode == 0 else ""


def _webhook():
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if url:
        return url
    res = subprocess.run(["security", "find-generic-password", "-s", "aleph/SLACK_WEBHOOK_URL", "-w"], capture_output=True, text=True, timeout=10)
    return res.stdout.strip() if res.returncode == 0 else ""


def _last_message(transcript_path):
    last = ""
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("type") != "assistant" or entry.get("isSidechain"):
                    continue
                content = (entry.get("message") or {}).get("content")
                texts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"] if isinstance(content, list) else [content or ""]
                text = " ".join(t for t in texts if t).strip()
                if text:
                    last = text
    except (OSError, TypeError):
        pass
    return re.sub(r"\s+", " ", last)[:400]


def _pull_request(marker, branch):
    issue = str(marker.get("issue", ""))
    started = marker.get("started", "")
    found = []
    for pr in _gh(f"repos/{marker['repo']}/pulls?state=all&sort=created&direction=desc&per_page=50") or []:
        head = (pr.get("head") or {}).get("ref", "")
        names_issue = issue and re.search(rf"#{re.escape(issue)}\b", pr.get("body") or "")
        if (branch and head == branch) or (names_issue and (pr.get("created_at") or "") >= started):
            found.append(pr)
    return found[0] if found else None


def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, EOFError):
        return
    if data.get("stop_hook_active"):
        return
    cwd = data.get("cwd") or os.getcwd()
    marker = read_marker(cwd)
    if not marker or marker.get("taken_over") or not marker.get("repo"):
        return
    branch = _branch(cwd)
    pr = _pull_request(marker, branch)
    outcome = pr["html_url"] if pr else "no-pr"
    if (marker.get("notified") or {}).get("outcome") == outcome:
        return
    title = marker.get("title")
    if not title:
        try:
            title = (_gh(f"repos/{marker['repo']}/issues/{marker['issue']}") or {}).get("title")
        except RuntimeError:
            title = None
    title = title or f"issue #{marker.get('issue')}"
    repo_name = marker["repo"].split("/")[-1]
    where = marker.get("worktree") or branch
    if pr:
        text = (f"Autonomous run finished: {title} ({repo_name}). Ready for your review: {pr['title']} {pr['html_url']}. "
                f"Merge it when it is right; worktree {where} in Orca.")
    else:
        text = (f"Autonomous run stopped without a pull request: {title} ({repo_name}). It may need you. "
                f"Last message: \"{_last_message(data.get('transcript_path'))}\" Open worktree {where} in Orca.")
    url = _webhook()
    if not url:
        return
    req = urllib.request.Request(url, data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            if res.status >= 300:
                return
    except Exception:  # noqa: BLE001  retried at the next stop
        return
    marker["notified"] = {"outcome": outcome, "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    write_marker(cwd, marker)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001  never stand in the agent's way
        pass
    sys.exit(0)
