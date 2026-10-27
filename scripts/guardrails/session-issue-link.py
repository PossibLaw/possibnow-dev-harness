#!/usr/bin/env python3
"""SessionStart hook: give Claude the GitHub issue an Orca worktree is linked to.

Sal, October 27, 2026: on the desktop, a worktree created from an issue starts Claude with the issue link in
the input box and Enter starts the work; the Orca mobile app starts Claude without the link. This hook asks
Orca (`orca worktree current --json`) which issue the session's worktree is linked to and, on a fresh start
(`startup` or `clear`), adds the link to the session's context, so a one-word first message such as "go"
starts the same work. Only the link is given; the issue's text is never fetched here. Outside an Orca
worktree, in the main checkout, without a linked GitHub issue, or when `orca` is missing, slow or answers
oddly, it adds nothing. It never blocks the session: it always exits 0 and prints nothing else.
"""
import json
import re
import subprocess
import sys

PROJECT_RE = re.compile(r"^github:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)$")
CONTEXT = ("This Orca worktree is linked to GitHub issue {url}. If the person's first message does not name "
           "other work (for example it is just \"go\"), treat that issue as the work and follow the instructions "
           "for a session that opens with only a GitHub issue link.")


def linked_issue_url(cwd):
    try:
        res = subprocess.run(["orca", "worktree", "current", "--json"], cwd=cwd, capture_output=True, text=True, timeout=3)
        wt = json.loads(res.stdout)["result"]["worktree"]
    except Exception:
        return None
    issue, project = wt.get("linkedIssue"), PROJECT_RE.match(str(wt.get("projectId") or ""))
    if wt.get("isMainWorktree") or not project or isinstance(issue, bool) or not isinstance(issue, int) or issue <= 0:
        return None
    return f"https://github.com/{project.group(1)}/{project.group(2)}/issues/{issue}"


def main():
    try:
        data = json.load(sys.stdin)
        if data.get("source", "startup") not in ("startup", "clear"):
            return
        url = linked_issue_url(data.get("cwd") or None)
        if url:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": CONTEXT.format(url=url)}}))
    except Exception:
        return


if __name__ == "__main__":
    main()
    sys.exit(0)
