---
contract_version: 1
artifact_type: review
status: VALIDATED
depends_on: [.agent/PLAN.md, .agent/TEST.md]
produces: [security_assessment, residual_risks]
feeds_into: [.agent/HANDOFF.md]
memory:
  include_in_memory: true
  tags: [review, security]
---

# 4.2.1 Review

Reviewed requirement preservation against docs/architecture/rule-ownership.md and
E1-E10 in TEST.md. Root adapters have one authoring source and meaningful task
routes; ordinary questions do not trigger the delivery pipeline. The full security
validation/review checklists remain in the state templates and are explicitly routed.
No historical research was rewritten as evidence for the 150-line project policy.

## Security Review Mode

- Target writes: all destination paths preflight before creation; existing files
  are never overwritten. Nested symlinks/non-directory parents fail. Exclusive
  creation and hash rechecks address intervening edits. No shell eval of options.
- Checkpoint: byte-exact archive/locator verification, ID conflict checks and
  dedup precede replacement. Failures preserve the existing HANDOFF; locks serialize
  helper runs. Semantic completeness and sanitization remain reviewed obligations.
- Rollback: preflight hashes/path boundaries before any deletion; retain unrelated
  files and refuse changed files. No reset or broad deletion command is used.
- Startup: snapshot root/skill candidates use non-instruction suffixes. No eager
  handbook/history import or client settings adapter is added.
- Confidentiality: release snapshots contain bundled templates, never copied
  customized project contents. Receipts contain hashes and paths, not secrets.
  Optimization backups stay private. No credentials, model or permission changes.
- Auth/API/session/tenant isolation: N/A; no service endpoints or identity system
  changed. The relevant input boundary is local filesystem paths and file content.
- Dependencies/runtime: Python standard library; existing pytest-only test setup.
  Existing Claude guardrails and tests remain unchanged. Other hosts do not gain
  Claude enforcement; live client claims are explicitly UNCONFIRMED.

Resolved findings: overwrite risk, recurring backup churn, late symlink rejection,
learning-mode contradictions, timeline appending, conflicting archive IDs, and
nested snapshot instruction discovery. No known blocking source finding remains.

Residual limits: coordinate external editors during filesystem replacement;
helper locks cannot serialize arbitrary applications. Optimization and lesson
promotion are advisory agent decisions, not a new semantic migration/learning
engine. Preserved customized entries can remain oversized pending reviewed migration.
Marketplace distribution and live client integration require their own verification.

Prior review preserved verbatim: archives/pre-4.2-REVIEW.md.

## v4.2.1 correction review

The public-tag smoke exposed a root alias portability gap in rollback. Normalize
only the chosen target-root alias before deriving the receipt-relative path; keep
safe_path checks on every internal component. Do not resolve the receipt directly
and hide an internal symlink. Candidate tag v4.2.0 remains immutable; v4.2.1 must
pass the public smoke before release publication.

Publication review complete: the actual v4.2.1 public-tag smoke passed and the release is published. See RELEASE-4.2.1.md.
