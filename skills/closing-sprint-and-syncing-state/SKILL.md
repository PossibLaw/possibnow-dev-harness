---
name: closing-sprint-and-syncing-state
description: Preserve the previous handoff, refresh current state, and prepare shared continuity when pausing, closing a sprint, or shipping work.
metadata:
  version: 2.2.0
---

# Closing Sprint and Syncing State

Read `docs/workflows/contracts.md` for the checkpoint and commit contract. Update PLAN to reflect current work. Prepare a current HANDOFF that retains decisions, exact constraints, blockers, evidence links, and the next action.

Replace the checkpoint, do not prepend. Each entry is one line with a link. Put the date, what changed and a link to the PR, issue, plan or runbook; the narrative belongs in that PR or issue body, not in HANDOFF. Keep `## Status` to a few lines and `## Recent work` to about ten entries.

Before installing the candidate, write a carry-forward list from the full prior handoff: for each item of open work, owed item, pending decision, UNCONFIRMED fact and active constraint, give the item, its old location, and KEPT, POINTS TO an issue, or RESOLVED with evidence (merged PR, closed issue, register row, or a later entry). If an item's state cannot be confirmed, keep it and mark it UNCONFIRMED. Put the list in the PR body so a reviewer can check it against the archived file; the helper cannot detect a dropped item.

Use the checkpoint.py helper described in that contract after reviewing the full prior handoff and authoritative current state. Keep every unresolved task and active constraint, regardless of age. The helper preserves and verifies exact prior bytes and refuses a candidate over the size limits; semantic completeness still requires review. Check with `python3 .agent/integrations/handoff_size.py .` before committing. Normal resume reads only current HANDOFF.

Read docs/workflows/learning.md only for requested or enabled learning; keep candidates separate from adopted lessons. Review all changed continuity for sensitive content, commit it with the work, and verify the authorized delivery on remote main. Keep raw runtime logs and credentials private. Report incomplete validation or delivery honestly.

Last step, after the checkpoint and delivery: feed this repository's register into the
machine-wide task list so one file shows what is open across all repositories. From the
repository root run `python3 ~/.agents/skills/cross-repo-tasks/feed.py`. If that script is
not installed on this machine, skip the step and say so in the handoff; do not install it.
