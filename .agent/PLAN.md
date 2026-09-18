---
contract_version: 1
artifact_type: plan
status: IN_PROGRESS
depends_on: []
produces: [eval_ids, release_scope]
feeds_into: [.agent/TEST.md]
memory:
  include_in_memory: true
  tags: [plan]
---

# 4.2.0 Compact portable harness

Baseline: main 4f43649b175ad18813319bba6849d200238c307f, unchanged after fetch.
Original entries: AGENTS 178 lines/1890 words/13582 bytes; CLAUDE 202/2003/14446.
Sal's <=150 physical line policy applies to each shipped/newly generated root,
not a scientific optimum or cost claim. Rule ownership: docs/architecture/rule-ownership.md.

Scope: one source for compact adapters; on-demand canonical procedures; current-only
handoff with verified exact archives; gated learnings; conservative file-preserving
updates with versioned candidates/receipts/rollback; double-pinned v4.2.0 release.
Do not modify installed projects, globals, models/effort, permissions, learning
mode, or Scale. Tests use disposable fixtures only; no paid model comparison.

## Acceptance and evidence plan

- E1: fresh fixture gets valid routes and <=150-line entries.
- E2: 150 passes/151 fails with LF, CRLF, and missing final newline.
- E3: planning, validation, review/security, content, checkpoint and learning rules
  remain in reachable authoritative homes; retain detailed TEST/REVIEW checklists.
- E4: customized and unchanged older fixtures preserve every pre-existing byte;
  differing files remain pending reviewed migration, including oversized entries.
- E5: dry-run/check makes no target writes; same release/options repeat is idempotent.
- E6: archive full prior bytes/hash/timestamp/ID; failed/corrupt/conflicting archive
  or intervening edit leaves HANDOFF intact. Candidate semantic completeness is reviewed.
- E7: OFF captures nothing; candidates never count as adopted lessons. CAPTURE
  never edits instructions; APPLY requires authorization. Static/advisory coverage.
- E8: no eager root imports, rules, or state/history/library preload; read-only
  questions bypass delivery state. Existing external client context is unverified.
- E9: existing Claude guardrail tests remain unchanged and passing; client matrix
  names enforcement limits. No new runtime adapter is claimed.
- E10: tag-based bootstrap fixture selects release over newer branch; published
  curl smoke must select the actual release version/commit before final delivery.

## Milestones

Implementation complete; local verification and release review in progress.
Publish v4.2.0 only after full verification and CI pass. Preserve all sanitized
continuity with work and verify remote main. Record post-publication smoke evidence
in the GitHub release notes so the immutable tag is not moved after verification.

## Learning Mode
- Mode: `OFF` (existing task default)

Prior plan preserved verbatim: archives/pre-4.2-PLAN.md.
