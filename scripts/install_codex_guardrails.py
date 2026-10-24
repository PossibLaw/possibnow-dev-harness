#!/usr/bin/env python3
"""Install the PossibNow guardrails as Codex PreToolUse hooks.

Copies the guardrail scripts to <codex-home>/hooks/possibnow/ and registers them
inline in <codex-home>/config.toml between marker lines (not hooks.json, which
Orca manages). Re-running refreshes the scripts and leaves an unchanged config
alone. New or changed hooks stay skipped until trusted with /hooks in Codex.
"""
import argparse
import json
import re
import shlex
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARDS = ROOT / "scripts" / "guardrails"
FILES = ("validate-bash.py", "protect-files.py", "blacklist.py", "autonomy.py")
BEGIN = "# >>> possibnow-dev-harness codex guardrails >>>"
END = "# <<< possibnow-dev-harness codex guardrails <<<"


def block(dest):
    def group(matcher, script, args=""):
        command = f"python3 {shlex.quote(str(dest / script))}{args}"
        return (f'[[hooks.PreToolUse]]\nmatcher = {json.dumps(matcher)}\n\n'
                f'[[hooks.PreToolUse.hooks]]\ntype = "command"\ncommand = {json.dumps(command)}\n'
                f'timeout = 30\nstatusMessage = "PossibNow guardrails"\n')
    return (f"{BEGIN}\n" + group("^Bash$", "validate-bash.py", " --host codex") + "\n"
            + group("^apply_patch$", "protect-files.py") + f"{END}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    home = parser.parse_args().codex_home.expanduser().resolve()
    config = home / "config.toml"
    text = config.read_text() if config.exists() else ""

    managed = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.S)
    outside = managed.sub("", text)
    # [hooks.state."..."] tables are Codex's own trust records, not hook definitions.
    if re.search(r"^\s*\[\[?hooks(\]|\.(?!state[.\]]))", outside, re.M):
        print(f"BLOCKED: {config} already has its own [hooks] tables. Merge the PossibNow "
              f"hooks by hand to avoid changing existing hooks.", file=sys.stderr)
        sys.exit(1)

    dest = home / "hooks" / "possibnow"
    dest.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copy2(GUARDS / name, dest / name)

    new = outside.rstrip("\n") + ("\n\n" if outside.strip() else "") + block(dest)
    if new != text:
        if config.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(config, config.with_name(f"config.toml.bak-{stamp}"))
        config.write_text(new)
        print(f"Registered PossibNow guardrails in {config}")
    else:
        print(f"PossibNow guardrails already registered in {config}")
    print(f"Guard scripts: {dest}\nNext: open Codex and run /hooks to review and trust them.")


if __name__ == "__main__":
    main()
