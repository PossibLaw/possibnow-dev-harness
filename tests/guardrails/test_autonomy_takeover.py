"""Sticky autonomous-run marker with human takeover (PLAN T1-T5, T7).

The dispatcher marks each worktree it starts with `agent-auto.json` in the worktree's private git
directory. A marked worktree stays autonomous across branch switches until a person types a prompt;
the UserPromptSubmit hook records the dispatcher's first prompt and releases the guard on any later one.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARDS = ROOT / "scripts" / "guardrails"
BASH_HOOK = str(GUARDS / "validate-bash.py")
MCP_HOOK = str(GUARDS / "guard-auto-publish.py")
FILE_HOOK = str(GUARDS / "protect-files.py")
PROMPT_HOOK = str(GUARDS / "autonomy-takeover.py")
DISPATCH_PROMPT = "You are a senior software engineer. This is an AUTONOMOUS run started by the nightly dispatcher. Get started on this: https://github.com/o/r/issues/42"


def autonomy():
    spec = importlib.util.spec_from_file_location("autonomy_under_test", GUARDS / "autonomy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def env():
    e = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "AGENT_AUTO")}
    e.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    return e


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=env())


def worktree(tmp_path, branch="auto-42", marked=True):
    """A real linked worktree, as Orca makes them; marked the way the dispatcher marks it."""
    main = tmp_path / "main"
    main.mkdir()
    git("init", "-q", "-b", "main", cwd=main)
    git("commit", "-q", "--allow-empty", "-m", "init", cwd=main)
    wt = tmp_path / "wt"
    git("worktree", "add", "-q", "-b", branch, str(wt), cwd=main)
    if marked:
        autonomy().write_marker(str(wt), {"repo": "o/r", "issue": 42})
    return str(wt)


def bash(command, cwd):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}
    return subprocess.run([sys.executable, BASH_HOOK], input=json.dumps(payload), capture_output=True, text=True, cwd=cwd, env=env())


def mcp(tool, cwd):
    payload = {"tool_name": tool, "tool_input": {"publish": True}, "cwd": cwd}
    return subprocess.run([sys.executable, MCP_HOOK], input=json.dumps(payload), capture_output=True, text=True, cwd=cwd, env=env())


def prompt(cwd, session, text, transcript=None):
    payload = {"hook_event_name": "UserPromptSubmit", "session_id": session, "cwd": cwd, "prompt": text,
               "transcript_path": str(transcript) if transcript else ""}
    return subprocess.run([sys.executable, PROMPT_HOOK], input=json.dumps(payload), capture_output=True, text=True, cwd=cwd, env=env())


def blocked(res):
    return res.returncode == 2 and "autonomous" in res.stderr.lower()


def asks(res):
    return res.returncode == 0 and '"permissionDecision": "ask"' in res.stdout


def mcp_denied(res):
    return res.returncode == 0 and '"permissionDecision": "deny"' in res.stdout


def test_t1_marked_worktree_stays_autonomous_after_a_branch_switch(tmp_path):
    wt = worktree(tmp_path)
    assert blocked(bash("gh pr merge 5", wt))
    git("checkout", "-q", "-b", "fix/harvest-pull-before-commit", cwd=wt)
    assert blocked(bash("gh pr merge 5", wt)), "the marker, not the branch name, decides"
    assert mcp_denied(mcp("mcp__substack__publish_draft", wt))


def test_t2_a_second_prompt_releases_the_guard(tmp_path):
    wt = worktree(tmp_path, branch="feature/x")
    first = prompt(wt, "s1", DISPATCH_PROMPT)
    assert first.returncode == 0 and "released" not in first.stdout.lower()
    assert blocked(bash("gh pr merge 5", wt)), "the dispatcher's own prompt keeps the run autonomous"
    second = prompt(wt, "s1", "Merge PR")
    assert second.returncode == 0 and "released" in second.stdout.lower()
    assert asks(bash("gh pr merge 5", wt)), "after takeover merge asks first, as in any session"
    assert not mcp_denied(mcp("mcp__substack__publish_draft", wt))


def test_t3_a_prompt_from_another_session_releases_the_guard(tmp_path):
    wt = worktree(tmp_path)
    prompt(wt, "dispatched", DISPATCH_PROMPT)
    res = prompt(wt, "someone-else", "What is the status?")
    assert "released" in res.stdout.lower()
    assert autonomy().is_autonomous(wt) is False
    assert asks(bash("gh pr merge 5", wt)), "a released marker wins over the auto-<n> branch name"


def test_t4_race_where_the_dispatcher_prompt_came_before_the_marker(tmp_path):
    wt = worktree(tmp_path)
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("\n".join(json.dumps(e) for e in (
        {"type": "user", "message": {"role": "user", "content": DISPATCH_PROMPT}},
        {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "ok"}]}},
        {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "x"}]}},
        {"type": "user", "isMeta": True, "message": {"role": "user", "content": "<system-reminder>x</system-reminder>"}},
    )) + "\n")
    res = prompt(wt, "s1", "Merge PR", transcript)
    assert "released" in res.stdout.lower(), "an earlier prompt in the transcript means this one is a person"
    assert asks(bash("gh pr merge 5", wt))


def test_t4_the_dispatcher_prompt_already_in_the_transcript_does_not_release(tmp_path):
    # Orca's first prompt is stored wrapped in paste tags; it must still count as the same prompt.
    wt = worktree(tmp_path)
    transcript = tmp_path / "t.jsonl"
    transcript.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": f'  <pasted_content id="b26a"> {DISPATCH_PROMPT} </pasted_content>'}}) + "\n")
    res = prompt(wt, "s1", DISPATCH_PROMPT, transcript)
    assert "released" not in res.stdout.lower()
    assert blocked(bash("gh pr merge 5", wt))


def test_t5_an_autonomous_agent_cannot_remove_or_rewrite_its_marker(tmp_path):
    wt = worktree(tmp_path)
    marker = autonomy().marker_path(wt)
    for cmd in (f"rm {marker}", f"rm -f .git/worktrees/wt/agent-auto.json", f"echo '{{}}' > {marker}", "python3 -c \"import os; os.remove('agent-auto.json')\""):
        assert blocked(bash(cmd, wt)), cmd
    payload = {"tool_name": "Write", "tool_input": {"file_path": marker, "content": "{}"}, "cwd": wt}
    res = subprocess.run([sys.executable, FILE_HOOK], input=json.dumps(payload), capture_output=True, text=True, cwd=wt, env=env())
    assert res.returncode == 2, "Write/Edit to the marker is refused in every session"


def test_t7_unmarked_worktree_is_unchanged_and_the_prompt_hook_is_silent(tmp_path):
    wt = worktree(tmp_path, branch="feature/y", marked=False)
    assert asks(bash("gh pr merge 5", wt))
    res = prompt(wt, "s1", "hello")
    assert res.returncode == 0 and res.stdout.strip() == ""
    assert autonomy().read_marker(wt) is None


def test_env_override_still_forces_autonomous(tmp_path):
    wt = worktree(tmp_path, branch="feature/z", marked=False)
    payload = {"tool_name": "Bash", "tool_input": {"command": "gh pr merge 5"}, "cwd": wt}
    res = subprocess.run([sys.executable, BASH_HOOK], input=json.dumps(payload), capture_output=True, text=True, cwd=wt, env={**env(), "AGENT_AUTO": "1"})
    assert blocked(res)
