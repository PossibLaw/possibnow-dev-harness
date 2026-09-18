# Implementation, validation, review, and delivery

Load this policy for implementation, validation, review, or shipping. Answer ordinary
questions and read-only inspections directly; they do not require new PLAN, TEST,
REVIEW, or HANDOFF records. For substantive work use the relevant stages below,
scaled to the task, retaining the project's stricter applicable requirements.

## Plan and implement

- Preserve project identity, custom routing, commands, constraints, and unrelated edits.
- Keep objective, assumptions, tasks, acceptance criteria, and eval IDs in PLAN;
  use existing TASKS/CONTEXT files where the project already separates them.
- Explain happy, boundary, and failure/security cases with observable expected
  results before changing behavior. Infer fixtures/commands from project evidence;
  label material gaps UNCONFIRMED and resolve them before executing ambiguous evals.
- Use TDD when feasible: failing evidence, minimum fix, then refactor while green.
  Never remove a failing check to manufacture success. Record a justified waiver
  when an applicable check cannot run; do not invent evidence.
- Apply the simplicity ladder: omit unnecessary work, reuse existing code, prefer
  the standard library, native features, existing dependencies, then a small solution.
- Do not change models, effort, permissions, global settings, learning mode, or
  Scale/wiki activation incidentally. Obtain missing authorization before destructive
  actions, schema changes, external writes, or broader scope; honor authorization
  already supplied for this task.

## Validate

Use `.agent/TEST.md` for the applicable matrix, security checklist, and receipts.
Record commands, inputs, expected/actual outcomes, and failing-before/passing-after
results against PLAN eval IDs. Derive unresolved commands from manifests and CI.
Code changes require relevant tests, lint, typecheck, and build where applicable.
Instruction changes require route/ownership/conflict and startup-import checks.
State changes require completeness and preservation checks.

For auth, data access, input handling, API, or deployment/runtime changes, check
server-side authentication/authorization, cross-user isolation, secrets exposure,
input injection, session/CSRF handling, dependency risks, deployment defaults,
network access, and backup/restore as applicable. Record N/A reasons rather than
inventing coverage or silently dropping a required check.

## Review

Use `.agent/REVIEW.md` Security Review Mode and its checklist. Review correctness,
regressions, security/privacy, maintainability, and evidence. Consider hostile
inputs and trust boundaries. Cite file/evidence, impact, severity, and a concrete
fix for each finding. Check conflicting instructions and unsupported control claims.
Do not mark required work complete while upstream acceptance or review is unresolved.

## Ship

Inspect status/diff and isolate this task on a focused branch. Complete applicable
checks, then follow [contracts](contracts.md) for the current checkpoint and shared
continuity. Review secrets/private data, stage explicit paths, and commit code/docs
with all changed sanitized continuity, including existing content and history files.
Push and complete the authorized PR/merge/release workflow. Verify the actual code
and continuity on remote main before claiming shared delivery. Keep blockers explicit.
Never bulk-add secrets, credential stores, environment files, caches, or raw logs.

## Specialized guidance

Read only the role needed from `docs/roles/README.md`. Vendor setup uses curated
`docs/vendor/` references and current official sources when recency matters, with
source dates. Graphify and wiki remain opt-in; their generated output is advisory,
and source code/tests win disagreements. Their procedures live in graphify.md and
wiki.md. Context/cost accounting lives in token-management.md.
