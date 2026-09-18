---
name: possibnow-guardrails
description: Inspect and explain PossibNow guardrails for the current workspace, including which protections are actually active in Claude Code or Codex.
---

# Guardrail status

Treat this as a read-only status or rule check. Inspect the harness `hooks/hooks.json` and relevant `scripts/guardrails/` rules when available. For an installed project, inspect its `AGENTS.md` and any observable host configuration needed for the user's question. Do not print secrets or raw environment values.

Distinguish documented rules from protections actually active in this host. Claude Code plugin hooks include destructive-command validation, sensitive-file warnings, format checks, and a shared-handoff commit guard. Those Claude hooks do not automatically run in Codex or from the project-file installer. Report Codex protections only when the active configuration or runtime provides evidence; mark unobservable status `UNCONFIRMED`.

If the user asks to add or change Codex enforcement, assess the specific mechanism and scope as a separate implementation task. Do not suggest that this informational skill itself intercepts commands or file writes.
