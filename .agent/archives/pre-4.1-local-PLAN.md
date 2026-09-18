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
  - .agent/HANDOFF.md
memory:
  include_in_memory: true
  tags: [plan]
---

# PLAN

## Objective
- IN_PROGRESS: Land the continuity-checkpoint workflow update in the starter pack and leave the repo ready for the next coding agent to review, stage, and ship.

## Scope
- In scope:
  - checkpoint rules in project templates
  - local checkpoint helper scripts
  - repo-local skills for sprint closeout and novice-safe git cycle
  - installer, verifier, README, and architecture doc updates
- Out of scope:
  - implementing a real MemPalace backend in this repo
  - staging, committing, or pushing changes

## Constraints
- Keep the pack file-first; local artifacts remain source of truth.
- Do not assume a real context meter exists; treat "50%" as a heuristic checkpoint trigger.
- Do not invent MemPalace success; only call a local helper if a target repo adds one.
- Preserve unrelated local changes.

## Evals
- E1 Happy path: `./scripts/verify-pack.sh` passes.
- E2 Installed-repo flow: install the pack into a temp repo and run the checkpoint helper successfully.
- E3 Failure/safety: MemPalace remains optional and skipped cleanly when no local helper exists.

## Assumptions
- [CONFIRMED] User wants a checkpoint rule or helper, not a hidden always-on hook.
- [CONFIRMED] Sprint closeout is the primary continuity trigger.
- [CONFIRMED] Novice-safe git flow should be recommended explicitly.
- [CONFIRMED] MemPalace is not implemented in this repo today; only the contract existed before this update.

## Risks
- Risk:
  - Impact: local continuity files may be confused with committed pack templates.
  - Mitigation: keep this root `.agent/` state local and treat it as baton-pass only.
- Risk:
  - Impact: `.gitignore` has a pre-existing local modification that may be unrelated to this task.
  - Mitigation: next agent should inspect it before staging anything.

## Open Questions
- Question:
  - Owner: next coding agent
  - Needed by: before shipping
  - Text: should the repo’s pre-existing `.gitignore` modification be kept, amended, or excluded from the final change set?

## Milestones
| Milestone | Owner | Status | Acceptance Check |
| --- | --- | --- | --- |
| Define continuity design | codex | DONE | Hook model and triggers decided |
| Implement pack changes | codex | DONE | Templates, docs, scripts, and skills updated |
| Validate pack | codex | DONE | `verify-pack.sh` and temp-repo dry run passed |
| Prepare handoff | codex | IN_PROGRESS | Local plan, handoff, and history updated |

## Exit Criteria
- Next agent can understand what changed, what was validated, and what still needs judgment before shipping.
