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
