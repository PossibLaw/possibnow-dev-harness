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

A shared, version-controlled continuity record for one current checkpoint.
Each entry is one line that points to the PR, issue or document holding the detail.
A close replaces this file through `checkpoint.py`; it never prepends a narrative.
Procedure: `docs/workflows/contracts.md`. Previous checkpoints: `.agent/HISTORY.md`.
Size check: `python3 .agent/integrations/handoff_size.py .` (limits in `.agent/handoff-limits.json`).

## Status
A few lines: where things stand now, not how they got here.
- Phase:
- Timestamp:
- Owner:
- Status: IN_PROGRESS
- Tier: 1 (Starter)
- Scale mode: OFF

## Recent work
Newest first, one line each; the link holds the detail. About ten kept; older entries
are in the archived checkpoints.
- YYYY-MM-DD What changed ([PR or issue](link))

## Unresolved work
- Task, owner, blocker, and evidence still needed:

## Active constraints
- Still-active decisions, exact values, and conditional rules:

## Evidence
- Relevant PLAN/TASKS, TEST/REVIEW, content records, and source locators:

## Next actions
1. Next concrete action:

## Sprint / Git Cycle
- Delivery state and next Git action:
- Previous checkpoint ID and verified HISTORY locator:

## Optional state
- Learning mode: OFF (read actual project declaration before learning work)
- Wiki sync when enabled:
- Legacy history locators, if any:
