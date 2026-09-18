---
contract_version: 1
artifact_type: handoff
status: IN_PROGRESS
depends_on:
  - .agent/PLAN.md
  - .agent/TEST.md
  - .agent/REVIEW.md
produces:
  - next_actions
  - open_questions
  - decision_summary
  - historical_checkpoint_link
feeds_into:
  - .agent/WIKI.md
memory:
  include_in_memory: true
  tags: [handoff]
---

# HANDOFF

This is the shared, version-controlled continuity record for the current checkpoint only. Commit it and all related continuity with the work. Previous checkpoints live in `.agent/HISTORY.md`; archive the exact prior handoff and verify its hash before replacing it. Preserve historical context and active constraints.

On resume read this current file. Retrieve a specific HISTORY entry only when needed.

## Current Baton (Read First)
Refresh this section in place at every checkpoint. Keep the newest actionable state here.

## Status
- Current phase:
- Owner:
- Timestamp (ISO):
- Overall status: `IN_PROGRESS`
- Checkpoint reason: `task-end` | `sprint-closeout` | `pre-git-cycle` | `context-50` | `handoff`
- Tier: `1 (Starter)` | `2 (Scale)`
- Scale mode: `OFF` | `ON`

## Suggested Roles
- `docs-releaser` owns handoff quality, docs alignment, and next-action clarity.

## What Was Completed
- Item:
  - Files:
  - Evidence:

## Decisions
- Decision:
  - Chose:
  - Rejected:
  - Why:
  - Status: `CONFIRMED` or `PROVISIONAL`

## Exact Values and Constraints
- Value:
- Constraint:
- Conditional rule: IF / THEN / BUT / EXCEPT

## Open Questions
- Question:
- Needed from:
- Risk if unanswered:

## Next Actions
1.
2.
3.

## Sprint / Git Cycle
- Sprint label:
- Sprint status: `IN_PROGRESS` | `PAUSED` | `COMPLETE`
- Git cycle status: `NOT_STARTED` | `REVIEWING` | `READY_TO_COMMIT` | `COMMITTED` | `PUSHED` | `PR_OPEN`
- Recommended next git step:

## Learning / Memory
- Learning mode: `OFF` | `CAPTURE` | `APPLY`
- Learnings updated: `YES` | `NO` | `N/A`

## Do-Not-Reread
- Archive or stale sources to skip unless explicitly requested.

## Contract Links (Required)
- Eval IDs covered:
- Test receipts referenced:
- Review findings referenced:

## Wiki Sync (Required When `.agent/WIKI.md` Enabled — Tier 2)
- Wiki root:
- Wiki index updated: `YES` or `NO`
- Pages updated:

## Historical Checkpoint
- Previous checkpoint ID:
- History locator and verified SHA-256:
