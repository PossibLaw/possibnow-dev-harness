---
contract_version: 1
artifact_type: handoff
status: READY_TO_RELEASE
depends_on: [.agent/PLAN.md, .agent/TEST.md, .agent/REVIEW.md]
produces: [next_actions, historical_checkpoint_link]
feeds_into: []
memory:
  include_in_memory: true
  tags: [handoff]
---

# Current Handoff — 4.2.0

## Status
Compact portable harness implementation is validated: 209 tests, plugin/skill
validators, and diff checks passed. AGENTS and CLAUDE are each 65 physical lines.
Release delivery is in progress on feat/compact-portable-harness.

## Unresolved work
- Merge with passing CI; publish v4.2.0 and verify the double-pinned remote bootstrap
  on a disposable customized fixture before providing the final update command.
- Live Codex/Claude/Cursor behavior and semantic optimize apply remain UNCONFIRMED.
- Marketplace distribution is separate; no external marketplace repository was changed.

## Active constraints
- Work only in the harness source; no Aleph or other installed project modifications.
- Existing project-specific policy/state stays intact until a reviewed migration.
- <=150 physical lines per shipped/new root is project policy, not a savings claim.
- Do not change models, effort, globals, permissions, learning modes, or Scale.
- No paid model comparison. Test installation/migration only in disposable fixtures.
- Preserve legacy/recovered archives and all sanitized continuity with the work.
- Before checkout updates inspect ignored continuity and use --no-overwrite-ignore.

## Evidence
- .agent/TEST.md: E1-E10 receipts and limitations; .agent/REVIEW.md: security review.
- docs/architecture/rule-ownership.md: authoritative policy homes and contradictions.
- Previous checkpoint: checkpoint-21381c233de60059dbea10f73bb4cbcf7efe55d99369229bb2ada46ba3ab43e4 in HISTORY, exact bytes verified.

## Next actions
1. Complete PR/CI/merge and v4.2.0 publication.
2. Verify published script/pack commit, then record publication evidence and provide
   the pinned update, reviewed optimize migration, and guarded rollback commands.
3. Installed project owners review pending customized files; downloading alone does
   not complete their migration. Keep semantic/live-client limits explicit.

Checkpoint time: 2026-09-18T17:10:09.004880+00:00
