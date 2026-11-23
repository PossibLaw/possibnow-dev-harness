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


## Issue 82 review (November 23, 2026)

Reviewed the guard diagnostic, 12 added regression cases, troubleshooting and
confirmed shared-continuity policy against PLAN C82-1 through C82-4. No blocking
finding in the scoped diff. The filename set and block semantics remain intact.
Keep the non-verbose check-ignore gate: verbose output also reports negated rules,
so using that output as the gate would incorrectly block explicit exceptions.

Security Review Mode: the diagnostic runs read-only Git commands using argv lists,
never a shell; the suggested staging path is shell-quoted and follows `--`.
No force-add, ignore edits, index mutation or file-content reads are introduced.
Tests verify an unchanged index and files and absence of private-content sentinels
from output. Only Git's matching ignore-rule metadata is displayed. Unrelated
private notes stay ignored and untracked after the migration fixture commits.

Auth/session/CSRF, tenant isolation and API/deployment changes: N/A (local hook
message only; no service endpoints, permission or runtime configuration changes).
Dependencies: no new runtime dependency. Existing fail-open Git-error behavior
and best-effort shell parsing are unchanged; this is not a shell sandbox.
The fallback retains the block and offers a diagnostic command if verbose rule
lookup fails. Live client migration and installed-plugin rollout remain separate,
unverified work (H-MIG01 / H-GR82). See TEST for actual validation receipts.


## v4.3.8 release review (November 23, 2026)

Version/pin-only release of reviewed PR #83. Active README, bootstrap, manifests,
workflow routes and installer fixtures agree on 4.3.8; old changelog/receipts retained.
No new runtime dependency, network permission, auth/API behavior or secret handling.
Public tag smoke must precede installation claims. Installed copies must match tag
bytes; preserve settings outside the managed Codex block and private project files.
Sal authorized tag/release publication and installed updates in this session.


## v4.3.8 rollout review

Published release and marketplace match the reviewed version. Tagged bootstrap
and installed runtime bytes were verified; no secrets or private inventory copied
into this repository. Scoped stale registration repair preserved unrelated fields
and a private backup. Codex changes are script refresh plus TOML formatting only;
settings and trust records compare equal. Session restarts were left to the operator.
