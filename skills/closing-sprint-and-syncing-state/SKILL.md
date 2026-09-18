---
name: closing-sprint-and-syncing-state
description: Preserve the previous handoff, refresh current state, and prepare shared continuity when pausing, closing a sprint, or shipping work.
metadata:
  version: 2.0.0
---

# Closing Sprint and Syncing State

Read `docs/workflows/contracts.md` for the checkpoint and commit contract. Update PLAN to reflect current work. Prepare a current HANDOFF that retains decisions, exact constraints, blockers, evidence links, and the next action.

Use the checkpoint.py helper described in that contract after reviewing the full prior handoff and authoritative current state. Keep every unresolved task and active constraint, regardless of age. The helper preserves and verifies exact prior bytes; semantic completeness still requires review. Normal resume reads only current HANDOFF.

Read docs/workflows/learning.md only for requested or enabled learning; keep candidates separate from adopted lessons. Review all changed continuity for sensitive content, commit it with the work, and verify the authorized delivery on remote main. Keep raw runtime logs and credentials private. Report incomplete validation or delivery honestly.
