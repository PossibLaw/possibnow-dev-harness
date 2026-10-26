"""Shared check: is this hook running inside an autonomous (self-started) agent run?

True when AGENT_AUTO=1 is in the environment, or the current git branch of `cwd` is
`auto-<n>` or `orca/auto-<n>` (the dispatcher names every self-started worktree auto-<n>;
Orca 1.4.240 uses that as the branch name, older designs assumed an orca/ prefix).
Data-only helper imported by the guardrail hooks; no main.
"""
import os
import re
import subprocess

AUTO_BRANCH_RE = re.compile(r"^(orca/)?auto-\d+$")


def auto_issue(branch):
    """The issue number when `branch` is a dispatcher branch (auto-<n> or orca/auto-<n>), else None."""
    m = AUTO_BRANCH_RE.match((branch or "").replace("refs/heads/", ""))
    return int(m.group(0).rsplit("-", 1)[1]) if m else None


def is_autonomous(cwd=None):
    if os.environ.get("AGENT_AUTO") == "1":
        return True
    try:
        proc = subprocess.run(["git", "-C", cwd or os.getcwd(), "branch", "--show-current"],
                              capture_output=True, text=True, timeout=5)
        return proc.returncode == 0 and auto_issue(proc.stdout.strip()) is not None
    except Exception:
        return False
