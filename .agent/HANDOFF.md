---
contract_version: 1
artifact_type: handoff
status: COMPLETE
depends_on: [.agent/PLAN.md, .agent/TEST.md, .agent/REVIEW.md, .agent/RELEASE-4.2.1.md]
produces: [next_actions, historical_checkpoint_link]
feeds_into: []
memory:
  include_in_memory: true
  tags: [handoff]
---

# Current Handoff — v4.2.1 published

## Status
Release v4.2.1 is published from ffe828e765d687fc63a6e8fff0a2382e40de0ea5.
PRs #11/#12 are merged; local and CI verification passed with 212 tests.
Both project entries are 65 physical lines. Public double-pinned bootstrap smoke
passed preservation, read-only preview, idempotency, exact commit, and rollback.

## Unresolved work
- Customized installed projects remain pending their own reviewed migration;
  downloading the release does not complete it. No real installed project was modified.
- Live client compliance and semantic optimize apply remain UNCONFIRMED.
- Marketplace publication remains separate; no external marketplace repo was changed.

## Active constraints
- Preserve project-specific routes/commands/content constraints and all continuity.
- <=150 physical lines per shipped/new entry is project policy, not a savings claim.
- No incidental model/effort/global/permission/learning/Scale changes or paid model evals.
- Use disposable fixtures for installer/migration testing, never real projects.
- Preserve legacy/recovered archives and all related sanitized continuity with work.
- Inspect ignored continuity before checkout updates; use --no-overwrite-ignore.
- Keep release tags immutable. v4.2.0 failed a final rollback portability gate;
  v4.2.1 includes the verified correction and is the recommended release.

## Evidence
- RELEASE-4.2.1.md: public release URL, commit, bootstrap hash and actual smoke receipt.
- TEST.md: E1-E10 and separate line/word/byte metrics; REVIEW.md: security assessment.
- docs/architecture/rule-ownership.md: current authoritative guidance homes.
- Previous checkpoint: checkpoint-6d4bbad1154ecf70171e3136fe9cf434969439f9ffa28272cc9d4ebf094221d5 in HISTORY; exact bytes verified.

## Next actions
1. Existing-project owners use the pinned v4.2.1 update in RELEASE-4.2.1.md.
2. Follow its versioned optimization policy in read-only check mode; apply only
   the reviewed proposal. Preserve custom files and active constraints during migration.
3. Keep live-client/marketplace limitations explicit until separately verified.
