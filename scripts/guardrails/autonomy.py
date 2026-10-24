"""Shared check: is this hook running inside an autonomous (self-started) agent run?

True when AGENT_AUTO=1 is in the environment, or the current git branch of `cwd`
starts with `orca/auto-` (the name the dispatcher gives every self-started worktree).
Data-only helper imported by the guardrail hooks; no main.
"""
import os
import subprocess


def is_autonomous(cwd=None):
    if os.environ.get("AGENT_AUTO") == "1":
        return True
    try:
        proc = subprocess.run(["git", "-C", cwd or os.getcwd(), "branch", "--show-current"],
                              capture_output=True, text=True, timeout=5)
        return proc.returncode == 0 and proc.stdout.strip().startswith("orca/auto-")
    except Exception:
        return False
