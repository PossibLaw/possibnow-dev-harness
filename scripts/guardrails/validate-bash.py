#!/usr/bin/env python3
"""PreToolUse hook for Bash — blocks destructive commands, escalates risky ones,
and refuses `git commit` while the shared project continuity is ignored, untracked, or unstaged."""

import json
import re
import shlex
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blacklist import BLOCKED_PATTERNS, ESCALATE_PATTERNS

# Shared continuity file that must ship with every commit that changes it.
HANDOFF_REL = ".agent/HANDOFF.md"
_SHELL_OPERATORS = {"&&", "||", ";", ";;", "|", "|&", "&"}
_GIT_GLOBAL_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}


def _tokenize(command):
    """Split a shell command into tokens, keeping quoted strings intact and
    surfacing operators (&&, ||, ;, |) as their own tokens."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def _segments(tokens):
    """Group tokens into simple commands separated by shell operators."""
    segments, current = [], []
    for tok in tokens:
        if tok in _SHELL_OPERATORS:
            if current:
                segments.append(current)
            current = []
        else:
            current.append(tok)
    if current:
        segments.append(current)
    return segments


def _parse_git_segment(segment):
    """Return (subcommand, args, chdir) for a `git ...` segment, else None."""
    if not segment or segment[0] != "git":
        return None
    chdir = None
    i = 1
    while i < len(segment):
        tok = segment[i]
        if tok in _GIT_GLOBAL_OPTS_WITH_ARG and i + 1 < len(segment):
            if tok == "-C":
                chdir = segment[i + 1]
            i += 2
            continue
        if tok.startswith("-"):
            i += 1
            continue
        return tok, segment[i + 1 :], chdir
    return None


def _run_git(repo_dir, *args):
    try:
        proc = subprocess.run(
            ["git", "-C", repo_dir, *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _abs_path_covers(tok_abs, handoff_abs):
    """Is the handoff the same file as tok_abs, or inside that directory? Compared by
    inode so symlinked checkouts and case-insensitive filesystems behave."""
    if not os.path.exists(tok_abs):
        return False
    current = handoff_abs
    while True:
        try:
            if os.path.samefile(tok_abs, current):
                return True
        except OSError:
            return False
        parent = os.path.dirname(current)
        if parent == current:
            return False
        current = parent


def _add_covers(add_args, add_dir, toplevel, untracked, rel=HANDOFF_REL):
    """Does `git add <add_args>` (run from add_dir) stage the handoff? Untracked files
    are only picked up by explicit paths, `.`/`:/`, or -A/--all — never by -u/--update.
    Relative pathspecs are resolved the way git does: relative to add_dir's prefix
    inside the repo, so no raw path strings are ever compared."""
    add_root = _run_git(add_dir, "rev-parse", "--show-toplevel")
    if not add_root or not os.path.samefile(add_root.strip(), toplevel):
        return False
    if any(x in add_args for x in ("-n", "--dry-run", "-N", "--intent-to-add", "-p", "--patch", "-i", "--interactive")):
        return False
    if any(x.startswith((":!", ":^", ":(exclude")) for x in add_args):
        return False
    paths = [x for x in add_args if not x.startswith("-")]
    update_only = any(x in add_args for x in ("-u", "--update"))
    if update_only and untracked:
        return False
    prefix = _run_git(add_dir, "rev-parse", "--show-prefix")
    if prefix is None:
        return False
    prefix = prefix.strip()
    handoff_from_add_dir = os.path.relpath(rel, prefix) if prefix else rel
    handoff_abs = os.path.join(toplevel, *rel.split("/"))
    for tok in add_args:
        if tok in ("-A", "--all", "--no-ignore-removal"):
            if not paths:
                return True
            continue
        if tok in ("-u", "--update"):
            if not untracked and not paths:
                return True
            continue
        if tok.startswith("-"):
            continue
        if tok in (":/", ":/."):
            return True
        if os.path.isabs(tok):
            if _abs_path_covers(tok, handoff_abs):
                return True
            continue
        norm = os.path.normpath(tok)
        if norm == ".":
            if not handoff_from_add_dir.startswith(".."):
                return True
            continue
        if norm == handoff_from_add_dir or handoff_from_add_dir.startswith(norm + "/"):
            return True
    return False


def _commit_includes_all(commit_args):
    """`git commit -a` / `--all` (also combined short flags like -am) stages
    modified tracked files, but never untracked ones."""
    skip = False
    for tok in commit_args:
        if skip:
            skip = False
            continue
        if tok in ("-m", "--message", "-F", "--file", "--author", "--date"):
            skip = True
            continue
        if tok == "--all":
            return True
        if tok.startswith("-") and not tok.startswith("--") and "a" in tok[1:]:
            return True
    return False


CONTINUITY_NAMES = {"HANDOFF.md", "HISTORY.md", "PLAN.md", "CONTEXT.md", "TASKS.md",
                    "TEST.md", "REVIEW.md", "LEARNINGS.md", "WIKI.md", "CONTINUITY.md",
                    "OPTIMIZATION.md"}


def _is_continuity(rel):
    if rel in (".claude/history.md", "HISTORY.md"):
        return True
    if not rel.startswith(".agent/") or not rel.endswith(".md"):
        return False
    tail = rel[len(".agent/"):]
    return (tail in CONTINUITY_NAMES or tail.startswith("CONTENT-")
            or tail.startswith(("archive/", "archives/")))


def _continuity_paths(root):
    # Include tracked deletions and ignored named continuity, but not arbitrary
    # private notes, logs, credentials or symlinked directories.
    tracked = _run_git(root, "ls-files", "-z", "--", ".agent", ".claude/history.md", "HISTORY.md") or ""
    paths = {p for p in tracked.split("\0") if _is_continuity(p)}
    agent_dir = os.path.join(root, ".agent")
    if not os.path.islink(agent_dir):
        for directory, dirs, files in os.walk(agent_dir, followlinks=False):
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(directory, d))]
            for name in files:
                rel = os.path.relpath(os.path.join(directory, name), root).replace(os.sep, "/")
                if _is_continuity(rel):
                    paths.add(rel)
    for rel in (".claude/history.md", "HISTORY.md"):
        if os.path.isfile(os.path.join(root, rel)):
            paths.add(rel)
    return sorted(paths)


def _path_limited_commit(args):
    skip = False
    for arg in args:
        if skip:
            skip = False
            continue
        if arg in ("-m", "--message", "-F", "--file", "--author", "--date", "-C", "-c", "--reuse-message", "--reedit-message") or re.fullmatch(r"-[a-zA-Z]*[mF]", arg):
            skip = True
        elif arg in ("--", "--only", "-o", "--include", "-i") or not arg.startswith("-"):
            return True
    return False


def check_handoff_commit(command, cwd):
    """Best-effort guard for common direct git commands, not a shell sandbox.

    Require changed named continuity and archives in the commit. Complex shell
    wrappers still rely on the shared contract and review.
    """
    try:
        base_dir = cwd or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        adds = []
        for segment in _segments(_tokenize(command)):
            parsed = _parse_git_segment(segment)
            if not parsed:
                continue
            sub, args, chdir = parsed
            repo_dir = os.path.normpath(os.path.join(base_dir, chdir)) if chdir else base_dir
            if sub == "add":
                adds.append((args, repo_dir))
                continue
            if sub != "commit":
                continue
            root = _run_git(repo_dir, "rev-parse", "--show-toplevel")
            if not root:
                continue
            root = root.strip()
            for rel in _continuity_paths(root):
                if _run_git(root, "check-ignore", rel):
                    return f"BLOCKED: {rel} is ignored. Review sensitive content and narrow its obsolete ignore rule before committing continuity."
                status = _run_git(root, "status", "--porcelain", "-z", "--untracked-files=all", "--", rel)
                if not status:
                    continue
                xy = status[:2]
                if _path_limited_commit(args):
                    return f"BLOCKED: a path-limited commit could omit changed continuity {rel}. Stage reviewed continuity and use an ordinary git commit."
                untracked = xy == "??"
                unstaged = not untracked and xy[1] != " "
                if not (untracked or unstaged):
                    continue
                inline = any(_add_covers(a, where, root, untracked, rel) for a, where in adds)
                if inline or (unstaged and _commit_includes_all(args)):
                    continue
                reason = "untracked" if untracked else "unstaged edits"
                return f"BLOCKED: {rel} has {reason}. Review for sensitive content, then run: git add {rel} -- and retry the commit."
        return None
    except Exception:
        return None


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    # Check blocked patterns first
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            print(
                f"BLOCKED: Command matches destructive pattern '{pattern}'. "
                f"Use a safer alternative.",
                file=sys.stderr,
            )
            sys.exit(2)

    # Shared handoff must ship with the work it describes
    handoff_block = check_handoff_commit(command, data.get("cwd"))
    if handoff_block:
        print(handoff_block, file=sys.stderr)
        sys.exit(2)

    # Check escalation patterns
    for pattern in ESCALATE_PATTERNS:
        if re.search(pattern, command):
            result = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": (
                        f"This command may have unintended consequences "
                        f"(matched pattern '{pattern}'). Confirm before proceeding."
                    ),
                }
            }
            print(json.dumps(result))
            sys.exit(0)

    # Safe command — approve
    sys.exit(0)


if __name__ == "__main__":
    main()
