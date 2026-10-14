"""Codex host support: same guardrails, adapted to Codex's hook contract.

Codex sends shell commands as tool_name "Bash" with tool_input.command (same as
Claude) but parses and ignores permissionDecision "ask", and sends file edits as
apply_patch with the patch text in tool_input.command.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
GUARDS = ROOT / "scripts" / "guardrails"
INSTALLER = ROOT / "scripts" / "install_codex_guardrails.py"


def _env():
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    return env


def run(script, payload, *args):
    cwd = tempfile.mkdtemp(prefix="codex-guard-")
    payload.setdefault("cwd", cwd)
    return subprocess.run(
        [sys.executable, str(GUARDS / script), *args],
        input=json.dumps(payload), capture_output=True, text=True, cwd=cwd, env=_env(),
    )


def bash(command):
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}}


def patch(body):
    return {"hook_event_name": "PreToolUse", "tool_name": "apply_patch", "tool_input": {"command": body}}


# --- validate-bash.py --host codex ---


def test_codex_blocked_command_exits_2():
    result = run("validate-bash.py", bash("git push -f origin main"), "--host", "codex")
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


@pytest.mark.parametrize("command", ["git rebase main", "git branch -D old", "git restore ."])
def test_codex_ask_first_becomes_block_with_instruction(command):
    result = run("validate-bash.py", bash(command), "--host", "codex")
    assert result.returncode == 2, "Codex ignores 'ask', so ask-first must block"
    assert "ASK-FIRST" in result.stderr
    assert "ask the user" in result.stderr
    assert result.stdout.strip() == ""


def test_codex_safe_command_passes():
    result = run("validate-bash.py", bash("git status"), "--host", "codex")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_claude_host_still_asks():
    result = run("validate-bash.py", bash("git rebase main"))
    assert result.returncode == 0
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask"


# --- protect-files.py with Codex apply_patch ---


@pytest.mark.parametrize(
    "body",
    [
        "*** Begin Patch\n*** Update File: .env\n@@\n-A=1\n+A=2\n*** End Patch",
        "*** Begin Patch\n*** Add File: config/id_ed25519\n+key\n*** End Patch",
        "*** Begin Patch\n*** Delete File: certs/server.pem\n*** End Patch",
        "*** Begin Patch\n*** Update File: notes.txt\n*** Move to: .aws/credentials\n@@\n-x\n+y\n*** End Patch",
        "*** Begin Patch\n*** Add File: src/ok.py\n+print(1)\n*** Update File: .env.local\n@@\n-a\n+b\n*** End Patch",
    ],
    ids=["update-env", "add-key", "delete-pem", "move-to-aws", "second-file-protected"],
)
def test_codex_patch_to_protected_file_blocked(body):
    result = run("protect-files.py", patch(body))
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


def test_codex_patch_to_safe_files_passes():
    body = "*** Begin Patch\n*** Add File: src/app.py\n+x\n*** Update File: README.md\n@@\n-a\n+b\n*** End Patch"
    result = run("protect-files.py", patch(body))
    assert result.returncode == 0


# --- installer ---


def install(home):
    pytest.importorskip("tomllib", reason="installer checks parse TOML (Python 3.11+)")
    return subprocess.run(
        [sys.executable, str(INSTALLER), "--codex-home", str(home)],
        capture_output=True, text=True, env=_env(),
    )


def test_installer_copies_guards_and_registers_hooks(tmp_path):
    (tmp_path / "config.toml").write_text('model = "x"\n\n[projects."/a"]\ntrust_level = "trusted"\n')
    result = install(tmp_path)
    assert result.returncode == 0, result.stderr
    dest = tmp_path / "hooks" / "possibnow"
    for name in ("validate-bash.py", "protect-files.py", "blacklist.py"):
        assert (dest / name).is_file()
    import tomllib
    config = tomllib.loads((tmp_path / "config.toml").read_text())
    assert config["model"] == "x" and config["projects"]["/a"]["trust_level"] == "trusted"
    groups = config["hooks"]["PreToolUse"]
    commands = {g["matcher"]: g["hooks"][0]["command"] for g in groups}
    assert "--host codex" in commands["^Bash$"] and "validate-bash.py" in commands["^Bash$"]
    assert "protect-files.py" in commands["^apply_patch$"]


def test_installer_is_idempotent_and_keeps_backup(tmp_path):
    (tmp_path / "config.toml").write_text('model = "x"\n')
    install(tmp_path)
    first = (tmp_path / "config.toml").read_text()
    install(tmp_path)
    assert (tmp_path / "config.toml").read_text() == first
    import tomllib
    assert len(tomllib.loads(first)["hooks"]["PreToolUse"]) == 2
    assert list(tmp_path.glob("config.toml.bak-*"))


def test_installer_keeps_codex_trust_state_tables(tmp_path):
    state = '[hooks.state."/x/hooks.json:stop:0:0"]\nenabled = true\ntrusted_hash = "sha256:ab"\n'
    (tmp_path / "config.toml").write_text('model = "x"\n\n' + state)
    result = install(tmp_path)
    assert result.returncode == 0, result.stderr
    import tomllib
    config = tomllib.loads((tmp_path / "config.toml").read_text())
    assert config["hooks"]["state"]["/x/hooks.json:stop:0:0"]["trusted_hash"] == "sha256:ab"
    assert len(config["hooks"]["PreToolUse"]) == 2


def test_installer_refuses_existing_unmanaged_hooks_table(tmp_path):
    (tmp_path / "config.toml").write_text('[[hooks.PreToolUse]]\nmatcher = "x"\n')
    result = install(tmp_path)
    assert result.returncode != 0
    assert "hooks" in result.stderr
