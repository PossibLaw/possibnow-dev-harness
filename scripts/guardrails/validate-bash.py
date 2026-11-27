#!/usr/bin/env python3
"""PreToolUse hook for Bash — blocks destructive commands, escalates risky ones,
and refuses `git commit` while the shared project continuity is ignored, untracked, or unstaged."""

import json
import re
import shlex
import subprocess
import sys
import os

# Imported helpers must not leave bytecode in the plugin or Codex hooks folder.
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blacklist import BLOCKED_PATTERNS, ESCALATE_PATTERNS, AUTONOMOUS_BLOCKED_PATTERNS
from autonomy import is_autonomous

# The size check ships in the project pack; a Codex install copies it next to this file.
_HERE = os.path.dirname(os.path.abspath(__file__))
for _dir in (_HERE, os.path.join(_HERE, "..", "..", "packs", "project", ".agent", "integrations")):
    if os.path.isfile(os.path.join(_dir, "handoff_size.py")):
        sys.path.insert(0, os.path.normpath(_dir))
        break
try:
    import handoff_size
except ImportError:  # pragma: no cover - an incomplete copy skips only the size check
    handoff_size = None

# Shared continuity file that must ship with every commit that changes it.
HANDOFF_REL = ".agent/HANDOFF.md"
_SHELL_OPERATORS = {"&&", "||", ";", ";;", "|", "|&", "&"}
_GIT_GLOBAL_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}


_HEREDOC_WORD = re.compile(r"<<(-?)[ \t]*(?:'([^']*)'|\"([^\"]*)\"|([A-Za-z_][A-Za-z0-9_]*))")


def _prepare(command):
    """Drop heredoc bodies and turn unquoted newlines into `;`, so a message body is
    never read as arguments and each line is its own command. Quoted text, including
    `"$(cat <<'EOF' ... EOF)"`, is left whole."""
    out, pending, i, quote = [], [], 0, None
    n = len(command)
    while i < n:
        ch = command[i]
        if quote:
            out.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < n:
                out.append(command[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch == "\\" and i + 1 < n:
            if command[i + 1] == "\n":  # line continuation
                i += 2
                continue
            out.append(command[i:i + 2])
            i += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            i += 1
            continue
        if command.startswith("<<", i) and not command.startswith("<<<", i):
            m = _HEREDOC_WORD.match(command, i)
            if m:
                pending.append((m.group(2) or m.group(3) or m.group(4) or "", m.group(1) == "-"))
                out.append(" << HEREDOC ")
                i = m.end()
                continue
        if ch == "\n":
            out.append(" ; ")
            i += 1
            for word, strip_tabs in pending:  # skip each body through its delimiter line
                while i < n:
                    end = command.find("\n", i)
                    line = command[i:] if end == -1 else command[i:end]
                    i = n if end == -1 else end + 1
                    if (line.lstrip("\t") if strip_tabs else line) == word:
                        break
            pending = []
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _tokenize(command):
    """Split a shell command into tokens, keeping quoted strings intact and
    surfacing operators (&&, ||, ;, |) as their own tokens."""
    command = _prepare(command)
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def _is_redirection(tok):
    return bool(tok) and set(tok) <= set("<>&|") and ("<" in tok or ">" in tok)


def _segments(tokens):
    """Group tokens into simple commands separated by shell operators. Redirections
    (`> file`, `2>&1`, `<< HEREDOC`) and their targets are dropped, never arguments."""
    segments, current = [], []
    skip = False
    for tok in tokens:
        if skip:
            skip = False
            continue
        if _is_redirection(tok):
            if current and current[-1].isdigit():  # the fd in `2>&1`, `2>/dev/null`
                current.pop()
            skip = True
            continue
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


def _git_commands(command, base_dir):
    """Yield (subcommand, args, repo_dir) for each `git` command, following `cd` the way
    the shell would. After a `cd` this hook cannot resolve (an unset variable, `cd -`),
    later commands are skipped rather than judged against the wrong repository."""
    current = base_dir
    for segment in _segments(_tokenize(command)):
        if segment[0] in ("cd", "pushd"):
            targets = [tok for tok in segment[1:] if tok == "-" or not tok.startswith("-")]
            target = targets[0] if targets else "~"
            if current is None or target == "-":
                current = None
                continue
            path = os.path.normpath(os.path.join(current, os.path.expanduser(os.path.expandvars(target))))
            current = path if "$" not in path and os.path.isdir(path) else None
            continue
        if current is None:
            continue
        parsed = _parse_git_segment(segment)
        if not parsed:
            continue
        sub, args, chdir = parsed
        repo_dir = os.path.normpath(os.path.join(current, chdir)) if chdir else current
        yield sub, args, repo_dir


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
        for sub, args, repo_dir in _git_commands(command, base_dir):
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
                if _run_git(root, "check-ignore", "--", rel):
                    # Keep the non-verbose check as the gate: -v also reports
                    # negated rules for paths that are NOT ignored.
                    rule = _run_git(root, "check-ignore", "-v", "--", rel)
                    path = shlex.quote(rel)
                    detail = rule.strip() if rule else f"unavailable; run git check-ignore -v -- {path}"
                    return (
                        f"BLOCKED: {rel} is ignored; sanitized continuity must be committed with the work.\n"
                        f"Matching ignore rule (source:line:pattern, then path): {detail}\n"
                        "This conflicts with the shared-continuity policy and may be an outdated local-only configuration. "
                        "Review the file for secrets and private runtime data; keep those private. "
                        "Narrow only the matching ignore rule to share the sanitized continuity, then run "
                        f"git add -- {path} and stage any reviewed .gitignore changes before retrying the commit. "
                        "Do not force-add ignored directories."
                    )
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


def check_handoff_size(command, cwd):
    """Refuse a commit that changes HANDOFF while it breaks the size limits.

    Reads only; never archives or rewrites. Commits that leave HANDOFF unchanged
    are not checked, so an older oversized file does not block unrelated work.
    """
    try:
        base_dir = cwd or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        for sub, _args, repo_dir in _git_commands(command, base_dir):
            if sub != "commit":
                continue
            if handoff_size is None:
                print("NOTICE: handoff_size.py not found beside the guard; HANDOFF size not checked. "
                      "Re-run the guard installer.", file=sys.stderr)
                return None
            root = _run_git(repo_dir, "rev-parse", "--show-toplevel")
            if not root:
                continue
            root = root.strip()
            if not _run_git(root, "status", "--porcelain", "--untracked-files=all", "--", HANDOFF_REL):
                continue
            problems, _ = handoff_size.check_repo(root)
            if problems:
                return handoff_size.message(problems)
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

    # Autonomous runs: no merging, no publishing (drafting is fine)
    if is_autonomous(data.get("cwd")):
        for pattern in AUTONOMOUS_BLOCKED_PATTERNS:
            if re.search(pattern, command):
                print(
                    f"BLOCKED: this is an autonomous agent run; merging and publishing are never "
                    f"allowed here (matched '{pattern}'). Leave the draft PR for the human to merge.",
                    file=sys.stderr,
                )
                sys.exit(2)

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
    size_block = check_handoff_size(command, data.get("cwd"))
    if size_block:
        print(size_block, file=sys.stderr)
        sys.exit(2)

    # Check escalation patterns
    codex = sys.argv[1:3] == ["--host", "codex"]
    autonomous = is_autonomous(data.get("cwd"))
    for pattern in ESCALATE_PATTERNS:
        if re.search(pattern, command):
            if autonomous:
                # Nobody is there to answer, so a question would stall the run.
                print(
                    f"BLOCKED: this is an autonomous agent run and this command is ask-first "
                    f"(matched pattern '{pattern}'). There is no one to ask, so it is refused: "
                    f"take another route, or leave it in the draft PR for the human.",
                    file=sys.stderr,
                )
                sys.exit(2)
            if codex:
                # Codex parses but ignores permissionDecision "ask", so ask-first must block.
                print(
                    f"ASK-FIRST: this command may have unintended consequences "
                    f"(matched pattern '{pattern}'). Codex hooks cannot prompt: stop and ask the user "
                    f"to confirm in chat, and if they agree, have them run it themselves.",
                    file=sys.stderr,
                )
                sys.exit(2)
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
