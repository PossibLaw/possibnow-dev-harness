---
description: Initialize the current repo with PossibNow Dev Harness project files (.agent/ state templates, AGENTS.md, CLAUDE.md, docs/roles, docs/workflows, docs/glossary, .claude/skills). Auto-detects stack and pre-fills test/lint/typecheck/build commands.
argument-hint: [--preserve-progress] [--dry-run] [--name NAME] [--owner OWNER] [--primary CMD] [--test CMD] [--lint CMD] [--typecheck CMD] [--build CMD]
allowed-tools: Bash
---

# /possibnow-dev-harness:init

Bootstrap the **current working directory** with PossibNow Dev Harness project files. Run this once after installing the plugin so your repo has the state-artifact pipeline (PLAN/TEST/REVIEW/HANDOFF), the project-level governance files, and the host-agnostic role and workflow contracts.

## Run

Run the bundled `scripts/install-project.sh` with the current directory as target.
Pass user options as separate arguments; treat argument text as data, never shell
code. Support --adopt, --preserve-progress, --dry-run and overrides shown by --help.
Resolve the installer under `${CLAUDE_PLUGIN_ROOT}`.

The conservative installer creates missing files and preserves all existing
files. Differing instructions/workflows are PENDING reviewed migration, including
oversized root entries. It supplies a versioned release snapshot, INSTALL.json
receipt, current optimization-policy path, and rollback helper. Existing continuity
and client configuration remain intact. Repeating the same install is idempotent.

Report the actual version/commit and pending items. Downloading a new pack is not
completing migration. Use the reported versioned optimization policy for a read-only
check, then apply the reviewed proposal. Inspect the diff and share sanitized
continuity with the work under docs/workflows/contracts.md.

Surface installer errors and remediation. A project-only installation adds files;
Claude runtime hooks require the separately installed/enabled Claude plugin.
