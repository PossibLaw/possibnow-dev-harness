#!/usr/bin/env python3
"""PreToolUse guard for MCP tools: in an autonomous run, deny any tool that publishes.

Matched by name against AUTONOMOUS_DENIED_TOOL_PATTERNS (publish, prepublish, create_post,
LinkedIn, Slack posting). Drafting tools pass. Outside autonomous runs everything passes.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autonomy import is_autonomous  # noqa: E402
from blacklist import AUTONOMOUS_DENIED_TOOL_PATTERNS  # noqa: E402


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)
    tool = data.get("tool_name", "") or ""
    if not tool.startswith("mcp__") or not is_autonomous(data.get("cwd")):
        sys.exit(0)
    for pattern in AUTONOMOUS_DENIED_TOOL_PATTERNS:
        if re.search(pattern, tool, re.I):
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Autonomous run: publishing tools are never allowed ({tool} matched '{pattern}'). Save a draft instead and leave publishing to the human.",
            }}))
            sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
