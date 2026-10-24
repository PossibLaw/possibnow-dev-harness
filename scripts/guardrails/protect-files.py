#!/usr/bin/env python3
"""PreToolUse hook for Write|Edit — blocks writes to sensitive files."""

import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blacklist import PROTECTED_FILE_PATTERNS


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    if data.get("tool_name") == "apply_patch":
        # Codex sends edits as a patch; every touched path is in its file headers.
        paths = re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$",
                           tool_input.get("command", ""), re.MULTILINE)
    else:
        paths = [tool_input.get("file_path", "")]

    for file_path in filter(None, (p.strip() for p in paths)):
        for pattern in PROTECTED_FILE_PATTERNS:
            if re.search(pattern, file_path):
                print(
                    f"BLOCKED: File '{file_path}' matches protected pattern '{pattern}'. "
                    f"This file contains sensitive data and should not be modified by an agent.",
                    file=sys.stderr,
                )
                sys.exit(2)

    # Safe file — approve
    sys.exit(0)


if __name__ == "__main__":
    main()
