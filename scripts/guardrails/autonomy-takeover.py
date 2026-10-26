#!/usr/bin/env python3
"""UserPromptSubmit hook: release the autonomous-run guard when a person takes over the session.

The dispatcher marks each worktree it starts (`agent-auto.json` in the worktree's git directory).
The first prompt seen after that is the dispatcher's own; any later prompt, in that session or in
another session in the same worktree, comes from a person, so the marker is released and the normal
ask-first rules apply from then on. Without a marker this hook does nothing and prints nothing.
It never blocks a prompt.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autonomy import note_prompt  # noqa: E402

RELEASED = ("Autonomous-run guard released: a person is steering this session, so merging and "
            "publishing follow the normal ask-first rules again.")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)
    try:
        result = note_prompt(data.get("cwd"), data.get("session_id"), data.get("prompt") or "", data.get("transcript_path") or None)
    except Exception:
        sys.exit(0)  # never stand between a person and their prompt
    if result == "taken_over":
        print(json.dumps({"systemMessage": RELEASED,
                          "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": RELEASED}}))
    sys.exit(0)


if __name__ == "__main__":
    main()
