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
    # Any force flag (-f, -df, -xdf, --force) deletes untracked files.
    r"git\s+clean\b[^;&|\n]*\s(-[a-zA-Z]*f[a-zA-Z]*|--force)\b",
    # Force-push to main/master in any spelling: -f, trailing flag, lease, or +refspec.
    r"git\s+push\b(?=[^;&|\n]*\s(-[a-zA-Z]*f[a-zA-Z]*|--force(-with-lease)?(=\S*)?)(\s|$))(?=[^;&|\n]*\s(\S*:)?(main|master)(\s|$))",
    r"git\s+push\b[^;&|\n]*\s\+(\S*:)?(main|master)(\s|$)",
    r"mkfs\.",
    r":\(\)\{\s*:\|:&\s*\};:",
]

# Commands that require user confirmation (permissionDecision: "ask")
ESCALATE_PATTERNS = [
    r"git\s+reset(?!\s+--hard)",
    r"git\s+rebase",
    r"git\s+push\s+--force(?!\s+origin\s+(main|master))",
    # Other force-push spellings, branch force-delete, and discarding all working-tree changes.
    r"git\s+push\b[^;&|\n]*\s(-[a-zA-Z]*f[a-zA-Z]*|--force\S*)(\s|$)",
    r"git\s+push\b[^;&|\n]*\s\+\S",
    r"git\s+branch\b[^;&|\n]*\s-[a-zA-Z]*D",
    r"git\s+branch\b(?=[^;&|\n]*\s(--delete|-d)\b)(?=[^;&|\n]*\s(--force|-f)\b)",
    r"git\s+checkout\s+(--\s+)?\.(\s|$)",
    r"git\s+restore\b(?![^;&|\n]*--staged)[^;&|\n]*\s\.(\s|$)",
    r"git\s+restore\b[^;&|\n]*(--worktree|\s-W\b)[^;&|\n]*\s\.(\s|$)",
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
