"""Shared check: is this hook running inside an autonomous (self-started) agent run?

Order of evidence:
1. AGENT_AUTO=1 in the environment: autonomous, always.
2. A marker `agent-auto.json` in the worktree's private git directory, written by the dispatcher
   right after `orca worktree create`: autonomous until a person takes over the session. The marker
   survives branch switches and disappears with the worktree. The UserPromptSubmit hook
   (`autonomy-takeover.py`) records the dispatcher's first prompt and releases the marker on any
   later prompt, because only a person types into the pane after the dispatcher's prompt.
3. No marker: the current branch is `auto-<n>` or `orca/auto-<n>` (Orca 1.4.240 names the branch
   after `--name`; older designs assumed an orca/ prefix).
Data-only helper imported by the guardrail hooks and the dispatcher; no main.
"""
import datetime as _dt
import json
import os
import re
import subprocess

AUTO_BRANCH_RE = re.compile(r"^(orca/)?auto-\d+$")
MARKER_NAME = "agent-auto.json"


def auto_issue(branch):
    """The issue number when `branch` is a dispatcher branch (auto-<n> or orca/auto-<n>), else None."""
    m = AUTO_BRANCH_RE.match((branch or "").replace("refs/heads/", ""))
    return int(m.group(0).rsplit("-", 1)[1]) if m else None


def _git(cwd, *args):
    try:
        proc = subprocess.run(["git", "-C", cwd or os.getcwd(), *args], capture_output=True, text=True, timeout=5)
    except Exception:
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def marker_path(cwd=None):
    """Path of the marker for the worktree containing `cwd`, or None outside a git checkout."""
    git_dir = _git(cwd, "rev-parse", "--absolute-git-dir")
    return os.path.join(git_dir, MARKER_NAME) if git_dir else None


def read_marker(cwd=None):
    path = marker_path(cwd)
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {"unreadable": True}
    except (OSError, ValueError):
        return {"unreadable": True}  # a damaged marker still means autonomous: the safe side


def write_marker(cwd, data):
    """Create or replace the marker; returns its path. Raises OSError/RuntimeError on failure."""
    path = marker_path(cwd)
    if not path:
        raise RuntimeError(f"not a git checkout: {cwd}")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    os.replace(tmp, path)
    return path


def _now():
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _prompt_texts(transcript_path):
    """Texts of the prompts a person or the launcher typed in this session, oldest first."""
    texts = []
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isSidechain"):
                    continue
                content = (entry.get("message") or {}).get("content")
                if isinstance(content, list):
                    parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
                    if not parts:
                        continue  # tool results
                    content = " ".join(parts)
                if isinstance(content, str) and content.strip():
                    texts.append(content.strip())
    except (OSError, TypeError):
        pass
    return texts


def note_prompt(cwd, session_id, prompt="", transcript_path=None):
    """Called on every prompt. Returns "dispatched", "taken_over" or None (no marker / nothing to do)."""
    marker = read_marker(cwd)
    if marker is None or marker.get("taken_over"):
        return None
    session_id = session_id or ""
    if marker.get("dispatched_session") is None:
        # First prompt seen since the marker: the dispatcher's, unless this session already had a
        # different prompt (the dispatcher's prompt arrived before the marker was written).
        current = (prompt or "").strip()
        # The transcript may already hold the current prompt, possibly wrapped (Orca's first prompt is
        # stored inside <pasted_content> tags), so a text containing or contained in it is the same prompt.
        earlier = [t for t in _prompt_texts(transcript_path) if not (current and (current in t or t in current))] if transcript_path else []
        if not earlier:
            marker.update(dispatched_session=session_id, dispatched_at=_now())
            write_marker(cwd, marker)
            return "dispatched"
    marker.update(taken_over=_now(), taken_over_session=session_id)
    write_marker(cwd, marker)
    return "taken_over"


def is_autonomous(cwd=None):
    if os.environ.get("AGENT_AUTO") == "1":
        return True
    marker = read_marker(cwd)
    if marker is not None:
        return not marker.get("taken_over")
    branch = _git(cwd, "branch", "--show-current")
    return branch is not None and auto_issue(branch) is not None
