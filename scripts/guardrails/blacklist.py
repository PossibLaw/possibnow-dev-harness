"""Guardrails pattern definitions.

Data module — no main. Imported by validate-bash.py and protect-files.py.
"""

# Commands that are always blocked (exit 2)
BLOCKED_PATTERNS = [
    r"rm\s+-rf\s",
    r"sudo\s+rm\s",
    r"curl\s.*\|\s*bash",
    r"wget\s.*\|\s*bash",
    r"dd\s+if=",
    r"chmod\s+777",
    r"chmod\s+-R\s+777",
    r"git\s+push\s+--force\s+origin\s+(main|master)",
    r"git\s+reset\s+--hard",
    r"git\s+clean\s+-f",
    r"mkfs\.",
    r":\(\)\{\s*:\|:&\s*\};:",
]

# Commands that require user confirmation (permissionDecision: "ask")
ESCALATE_PATTERNS = [
    r"git\s+reset(?!\s+--hard)",
    r"git\s+rebase",
    r"git\s+push\s+--force(?!\s+origin\s+(main|master))",
    r"rm\s+-r(?!f)\s",
    # chmod: escalate only genuinely risky forms — recursive, world-writable
    # (others get write), setuid/setgid. Scoped changes (644, 755, 600, 000,
    # +x, u+w) pass silently; 777 and -R 777 stay hard-blocked above.
    r"chmod\s+-R\s",
    r"chmod\s+\S*[oa]\+w",
    r"chmod\s+(-[a-zA-Z]+\s+)*\+w\b",
    r"chmod\s+\S*\+s\b",
    r"chmod\s+(-[a-zA-Z]+\s+)*[2467][0-7]{3}\b",
    r"chmod\s+(-[a-zA-Z]+\s+)*[0-7]{2,3}[2367]\b",
]

# Merging a pull request asks first in every session (the human merges).
ESCALATE_PATTERNS += [
    r"gh\s+pr\s+merge\b",
    r"gh\s+api\s.*\/pulls\/\d+\/merge\b",
]

# Autonomous runs (AGENT_AUTO=1 or a branch named orca/auto-*): blocked outright.
# Merging is never theirs; publishing of any kind is never theirs. Drafting is fine.
AUTONOMOUS_BLOCKED_PATTERNS = [
    r"gh\s+pr\s+merge\b",
    r"gh\s+api\s.*\/pulls\/\d+\/merge\b",
    r"\bpost-note\b",
    r"\bpublish[-_]draft\b",
    r"\bprepublish[-_]draft\b",
    r"[\"']publish[\"']\s*:\s*true",
    r"[\"']send[\"']\s*:\s*true",
    r"\bnpm\s+(run\s+)?publish\b",
    r"\bgit\s+push\s+\S*\s*(origin\s+)?(main|master)\b",
]

# MCP tools an autonomous run may never call (matched against the tool name).
AUTONOMOUS_DENIED_TOOL_PATTERNS = [
    r"publish",
    r"prepublish",
    r"create_post",
    r"send_newsletter",
    r"linkedin",
    r"slack.*(post|send)",
]

# Files that should never be written to
PROTECTED_FILE_PATTERNS = [
    r"\.env$",
    r"\.env\.",
    r"\.git/config$",
    r"\.gitconfig$",
    r"id_rsa",
    r"id_ed25519",
    r"\.pem$",
    r"\.key$",
    r"credentials\.json$",
    r"secrets\.yaml$",
    r"\.secret$",
    r"\.ssh/",
    r"\.aws/",
]
