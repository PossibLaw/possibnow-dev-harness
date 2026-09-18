---
description: Inspect the PossibNow Claude Code guardrails and report which protections are actually observable in this workspace.
argument-hint: [optional status or rule check]
allowed-tools: Read
---

# /possibnow-dev-harness:guardrails

Read the plugin's `hooks/hooks.json` and the relevant `scripts/guardrails/` rule.
When available, inspect enabled plugin/hook configuration without printing secrets.
Report configured protections separately from verified active runtime enforcement.
A missing runtime observation is UNCONFIRMED, not proof a protection is active.

The base plugin hooks cover destructive-command validation, sensitive-file warnings,
format checks, and a shared-continuity commit guard for common direct Git commands.
The optional Tier 2 hook file is not enabled by default. The hook suite tests these
scripts directly; it is not a general shell sandbox or proof of live session behavior.

Project-file installation supplies advisory guidance and helpers. Claude hooks do
not protect Codex, Cursor, or other hosts. Use the bundled client integration policy
at `${CLAUDE_PLUGIN_ROOT}/packs/project/docs/workflows/clients.md` for boundaries.
Do not change hooks, permissions, models, or native settings during this status check.
