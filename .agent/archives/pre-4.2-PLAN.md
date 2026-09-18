---
contract_version: 1
artifact_type: plan
status: IN_PROGRESS
depends_on: []
produces: []
feeds_into: []
memory:
  include_in_memory: true
  tags: [plan]
---

# 4.1.0 Plan

Scope: optimization slash command plus shared continuity commit contract. Preserve model choices, existing project state, secrets/private ignores, and historical handoffs. No fleet-wide migration or paid model eval.

E1: fresh install provides optimization workflow and HISTORY; named continuity is trackable.
E2: upgrades and repeated installs preserve existing state; dry-run creates nothing.
E3: commits cannot omit changed named continuity, content records, archives, or history; staging, ignored rules, and path-limited commits are checked without including unrelated private notes.
E4: command defaults to a read-only diff; apply requires the reviewed proposal and no unvalidated model changes. Instruction/pack validation only; live agent application not executed.

Status: implementation and local verification complete; release candidate ready for the authorized delivery workflow.

## Codex workflow parity — September 18, 2026

Scope: expose the four Claude command workflows through Codex project skills, while keeping the Claude command files and runtime hooks intact. The harness clone supplies Init; installed projects receive Scale, Guardrails, and Optimize plus the four existing workflow skills in `.agents/skills/`.

E1 (happy): a fresh project install provides seven discoverable Codex skills and preserves the Claude files. E2 (edge): dry-run and existing-state installs preserve project data. E3 (failure/security): invalid paths or symlink escapes fail safely; the Guardrails skill does not claim Claude hooks protect Codex. E4: Codex skill frontmatter validates. Live Codex invocation is `UNCONFIRMED`.

Status: implementation and local checks complete; remote delivery pending.
