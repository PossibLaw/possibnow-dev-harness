---
contract_version: 1
artifact_type: plan
status: IN_PROGRESS
depends_on: []
produces:
  - eval_ids
  - assumptions
  - risks
  - milestone_status
feeds_into:
  - .agent/TEST.md
  - .agent/REVIEW.md
  - .agent/HANDOFF.md
memory:
  include_in_memory: true
  tags: [plan]
---

# PLAN

## Current Plan Snapshot (Read First)
Keep the active plan in the sections below. On every checkpoint, update this current plan in place or prepend the newest active note above older active notes. Do not create alternate plan files.

## Objective
- IN_PROGRESS: <Define target outcome>

## Suggested Roles
- `product-strategist` for scope sharpening and success criteria.
- `engineering-planner` for milestones, file impact, and eval IDs.

## Scope
- In scope:
- Out of scope:

## Constraints
- Time:
- Safety:
- Tooling:
- Environment:

## Evals (Definition of Done)
Before implementation, define how we will verify success.

Minimum coverage for any behavior change:
- Happy path
- Edge/boundary
- Failure/security case

If this work involves an LLM/agent/RAG system, also define:
- Trace source (real vs synthetic)
- Target failure categories (if known)

## Learning Mode
- Mode: `OFF` (default)
- Change only by explicit task instruction or deliberate project choice.
- Authoritative mode/promotion policy: `docs/workflows/learning.md`.

## Continuity Checkpoint
- Sprint label: `UNCONFIRMED`
- For substantive active work, follow `docs/workflows/contracts.md` at a checkpoint.
- Update the current plan and prepare one current HANDOFF after verified archival.
- Keep completed narratives in HISTORY; retain all unresolved work/active constraints.
- Ordinary questions and read-only checks do not create delivery-state work.
- Advisory helper: `.agent/integrations/run-checkpoint.sh --reason sprint-closeout`.

## Assumptions
- [ASSUMPTION]

## Risks
- Risk:
  - Impact:
  - Mitigation:

## Open Questions
- Question:
  - Owner:
  - Needed by:

## Task Checklist
Track in-progress, done, blocked, and unconfirmed work items here (this absorbs the former `TASKS.md`).
- [ ] Task — status: `TODO` | `IN_PROGRESS` | `DONE` | `BLOCKED` | `UNCONFIRMED`

## Contract Outputs (Required)
- Eval IDs defined for `E1`/`E2`/`E3` in `.agent/TEST.md`.
- Assumptions marked `CONFIRMED`, `UNCONFIRMED`, or `ASSUMED`.
- Risks include impact and mitigation.
- Milestone statuses reflect current execution state.
- Planning outputs are compatible with the canonical role specs in `docs/roles/`.

## Milestones
| Milestone | Owner | Status | Acceptance Check |
| --- | --- | --- | --- |
| Define requirements | | IN_PROGRESS | Objective and acceptance are explicit |
| Implement changes | | PENDING | Requested files updated |
| Validate outcomes | | PENDING | Checks executed with receipts |
| Handoff | | PENDING | Risks and next actions documented |
| Sprint checkpoint | | PENDING | PLAN and HANDOFF synced before pause or ship |

## Exit Criteria
- Requested outputs complete and validated.
- Remaining blockers documented.

STOP: normal resume context ends here; older entries below are archive.

## Historical Archive
- Move superseded plan notes below this line only when they are no longer active.
