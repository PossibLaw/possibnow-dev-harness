"""Hook commands must survive a plugin path that contains a space (issue #78).

Orca runs Claude Code from a profile under "~/Library/Application Support/...", so the plugin root
has a space in it. An unquoted `${CLAUDE_PLUGIN_ROOT}/scripts/...` is split by the shell at that space
and the hook fails with "No such file or directory"; Claude Code treats that as non-blocking, so every
guardrail silently stops running. Each command is run the way a host runs it, through `/bin/sh -c`,
with the plugin root placed under a folder whose name has a space.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOK_FILES = ["hooks/hooks.json", "hooks/tier2-hooks.json"]
PAYLOAD = json.dumps({"source": "resume"})  # every hook treats this as "nothing to do"


def hook_commands():
    found = []
    for rel in HOOK_FILES:
        data = json.loads((ROOT / rel).read_text())
        for event, groups in data["hooks"].items():
            for group in groups:
                for hook in group["hooks"]:
                    found.append(pytest.param(rel, hook["command"], id=f"{rel}:{event}:{hook['command'].split('/')[-1].rstrip(chr(34))}"))
    return found


@pytest.fixture
def spaced_root(tmp_path):
    parent = tmp_path / "Application Support" / "plugin cache"
    parent.mkdir(parents=True)
    root = parent / "possibnow-dev-harness"
    root.symlink_to(ROOT, target_is_directory=True)
    return str(root)


def run_sh(command, cwd, env):
    return subprocess.run(["/bin/sh", "-c", command], input=PAYLOAD, capture_output=True, text=True, cwd=cwd, env=env, timeout=30)


def base_env(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "AGENT_AUTO", "CLAUDE_PLUGIN_ROOT")}
    env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
    return env


@pytest.mark.parametrize("rel,command", hook_commands())
def test_hook_runs_when_the_plugin_root_is_an_environment_variable_with_a_space(rel, command, spaced_root, tmp_path):
    env = base_env(tmp_path)
    env["CLAUDE_PLUGIN_ROOT"] = spaced_root
    res = run_sh(command, str(tmp_path), env)
    assert "No such file or directory" not in res.stderr, res.stderr
    assert res.returncode == 0, f"{command!r} exited {res.returncode}: {res.stderr}"


@pytest.mark.parametrize("rel,command", hook_commands())
def test_hook_runs_when_the_host_substitutes_a_plugin_root_with_a_space(rel, command, spaced_root, tmp_path):
    # Some hosts replace the placeholder in the command text before the shell sees it.
    res = run_sh(command.replace("${CLAUDE_PLUGIN_ROOT}", spaced_root), str(tmp_path), base_env(tmp_path))
    assert "No such file or directory" not in res.stderr, res.stderr
    assert res.returncode == 0, f"{command!r} exited {res.returncode}: {res.stderr}"


@pytest.mark.parametrize("rel,command", hook_commands())
def test_every_plugin_root_reference_sits_inside_double_quotes(rel, command):
    assert "${CLAUDE_PLUGIN_ROOT}" in command
    assert '"${CLAUDE_PLUGIN_ROOT}/' in command, f"{rel}: quote the path in {command!r}"
