---
name: closing-sprint-and-syncing-state
description: Preserve the previous handoff, refresh current state, and prepare shared continuity when pausing, closing a sprint, or shipping work.
metadata:
  version: 2.0.0
---

# Closing Sprint and Syncing State

Read `docs/workflows/contracts.md` for the checkpoint and commit contract. Update PLAN to reflect current work. Prepare a current HANDOFF that retains decisions, exact constraints, blockers, evidence links, and the next action.

Before replacing HANDOFF, archive its exact old contents in HISTORY under a unique ID and hash; verify preservation and check for intervening edits. A failed archive leaves the current handoff intact. Do not duplicate an identical checkpoint or delete legacy history. Normal resume reads only current HANDOFF.

Update learnings only when enabled and supported by its promotion rule. Review all changed continuity for sensitive content, commit it with the work, and verify the authorized delivery on remote main. Keep raw runtime logs and credentials private. Report incomplete validation or delivery honestly.
