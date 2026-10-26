"""Guardrails for autonomous (self-started) agent runs: no merge, no publishing.

A run is autonomous when AGENT_AUTO=1 is in the environment or the current git branch
starts with orca/auto-. In every session `gh pr merge` asks first; in an autonomous run
it is blocked, and so is every publishing command.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASH_HOOK = str(ROOT / "scripts" / "guardrails" / "validate-bash.py")
MCP_HOOK = str(ROOT / "scripts" / "guardrails" / "guard-auto-publish.py")


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "AGENT_AUTO")}
    env.update(extra)
    return env


def bash(command, cwd=None, env=None):
    cwd = cwd or tempfile.mkdtemp(prefix="auto-guard-")
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}
    return subprocess.run([sys.executable, BASH_HOOK], input=json.dumps(payload), capture_output=True, text=True, cwd=cwd, env=env or clean_env())


def mcp(tool_name, env=None, cwd=None):
    cwd = cwd or tempfile.mkdtemp(prefix="auto-guard-")
    payload = {"tool_name": tool_name, "tool_input": {"publish": True}, "cwd": cwd}
    return subprocess.run([sys.executable, MCP_HOOK], input=json.dumps(payload), capture_output=True, text=True, cwd=cwd, env=env or clean_env())


def auto_branch_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "orca/auto-42", str(repo)], check=True)
    return str(repo)


def asks(res):
    return res.returncode == 0 and '"permissionDecision": "ask"' in res.stdout


def test_merge_asks_first_in_a_normal_session():
    assert asks(bash("gh pr merge 5 --squash"))
    assert asks(bash("gh api -X PUT repos/o/r/pulls/5/merge"))


def test_merge_is_blocked_in_an_autonomous_run_by_env():
    res = bash("gh pr merge 5 --squash", env=clean_env(AGENT_AUTO="1"))
    assert res.returncode == 2 and "autonomous" in res.stderr.lower()


def test_merge_is_blocked_on_an_auto_branch(tmp_path):
    res = bash("gh pr merge 5", cwd=auto_branch_repo(tmp_path))
    assert res.returncode == 2 and "autonomous" in res.stderr.lower()


def test_merge_is_blocked_on_the_branch_orca_actually_creates(tmp_path):
    # Orca 1.4.240 names the worktree branch after the --name, with no orca/ prefix: auto-<n>.
    repo = tmp_path / "plain"; repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "auto-42", str(repo)], check=True)
    res = bash("gh pr merge 5", cwd=str(repo))
    assert res.returncode == 2 and "autonomous" in res.stderr.lower()


def test_a_human_branch_that_merely_starts_with_auto_is_not_autonomous(tmp_path):
    repo = tmp_path / "human"; repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "auto-complete-widget", str(repo)], check=True)
    assert asks(bash("gh pr merge 5", cwd=str(repo)))


def test_publishing_commands_are_blocked_only_in_autonomous_runs(tmp_path):
    for cmd in ("node src/cli.js post-note --id 3", 'curl -d \'{"publish": true}\' https://x', "npm run publish-draft"):
        assert bash(cmd).returncode == 0, cmd
        res = bash(cmd, env=clean_env(AGENT_AUTO="1"))
        assert res.returncode == 2 and "publish" in res.stderr.lower(), cmd


def test_drafting_is_allowed_in_autonomous_runs():
    for cmd in ("node src/cli.js draft-article --topic x", 'curl -d \'{"publish": false, "send": false}\' https://x', "git push -u origin orca/auto-42"):
        assert bash(cmd, env=clean_env(AGENT_AUTO="1")).returncode == 0, cmd


def test_mcp_publish_tools_are_denied_only_in_autonomous_runs(tmp_path):
    for tool in ("mcp__substack__publish_draft", "mcp__substack__prepublish_draft", "mcp__linkedin__create_post"):
        assert mcp(tool).returncode == 0 and "deny" not in mcp(tool).stdout, tool
        res = mcp(tool, env=clean_env(AGENT_AUTO="1"))
        assert res.returncode == 0 and '"permissionDecision": "deny"' in res.stdout, tool
    res = mcp("mcp__substack__publish_draft", cwd=auto_branch_repo(tmp_path))
    assert '"permissionDecision": "deny"' in res.stdout


def test_mcp_draft_tools_pass_in_autonomous_runs():
    for tool in ("mcp__substack__post_draft_from_markdown", "mcp__substack__put_draft", "mcp__substack__add_tags"):
        res = mcp(tool, env=clean_env(AGENT_AUTO="1"))
        assert res.returncode == 0 and "deny" not in res.stdout, tool
