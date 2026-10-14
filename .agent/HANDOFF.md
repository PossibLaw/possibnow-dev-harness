---
contract_version: 1
artifact_type: handoff
status: IN_REVIEW
depends_on: [.agent/PLAN.md]
produces: [next_actions, historical_checkpoint_link]
feeds_into: []
memory:
  include_in_memory: true
  tags: [handoff]
---

# Current Handoff — git guardrail gaps + Pocock-derived skills (unreleased)

## Status
Branch feat/v4.3.0-git-guards-and-pocock-skills off main 58ba0c0 (v4.2.1).
Guardrail gaps closed in scripts/guardrails/blacklist.py with 29 new cases;
two user-invoked skills and a maintainer reference added. PR open for review.

## Unresolved work
- v4.3.0 release not cut: version, README pins, bootstrap tag and publish smoke remain.
- Carried from v4.2.1: customized installed projects still need their own reviewed
  migration; live client compliance and semantic optimize apply remain UNCONFIRMED;
  marketplace publication is separate.
- Sal's machine runs the cached plugin at 4.1.0, not 4.2.1; update is a separate step.
- Codex parity for the new skills is by installer copy only; Codex behavior UNCONFIRMED.

## Active constraints
- Ordinary `git push` must stay allowed (running-novice-safe-git-cycle depends on it).
- Pocock-derived files keep MIT attribution and the pinned source commit 49dd158.
- Creating GitHub Issues from splitting-work-into-tickets is a remote write: confirm first.
- All v4.2.1 constraints still apply: preserve project content and continuity, <=150-line
  entries, no incidental model/effort/global/permission/learning/Scale changes,
  disposable fixtures only, immutable release tags.

## Evidence
- `uvx --with pytest pytest -q`: 241 passed (baseline 212); red run showed 18 expected failures first.
- `scripts/verify-pack.sh`: DONE: verification passed.
- Disposable-fixture install: both skills present under .claude/skills and .agents/skills.
- PLAN.md: G1–G3, S1–S2 acceptance cases.
- Previous checkpoint (v4.2.1 published) archived in HISTORY.

## Next actions
1. Review and merge the PR.
2. Cut v4.3.0: bump plugin.json, README pins, tests' tag fixtures; run publish smoke.
3. Update the installed plugin on Sal's machine from 4.1.0 to the new release.
