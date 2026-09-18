# Contract Pipeline and Continuity

This is the authoritative state/checkpoint contract. Use [delivery](delivery.md)
for implementation, validation, review, and Git procedures. Ordinary questions or
read-only checks do not run the delivery pipeline or rewrite continuity.

## State responsibilities

| Layer | Responsibility |
| --- | --- |
| Root entries | Stable identity, important commands/gotchas, boundaries, task routes |
| Workflows and skills | Canonical procedures and thin invocation adapters |
| PLAN and existing TASKS/CONTEXT | Active detail, assumptions, acceptance criteria, task checklist |
| HANDOFF | One current checkpoint: status, unresolved work, active constraints, evidence, next actions |
| HISTORY | Index and preserved prior checkpoints, retrieved individually |
| LEARNINGS | Bounded candidate/adopted lesson records under learning.md |

Substantive implementation proceeds PLAN → TEST → REVIEW → HANDOFF. PLAN defines
eval IDs; TEST records results for those IDs; REVIEW cites the test evidence;
HANDOFF points to relevant current results. Preserve existing content-specific
state and separate TASKS/CONTEXT files. Do not create competing current handoffs.

## Typed artifact headers

State templates use contract_version, artifact_type, status, depends_on, produces,
feeds_into, and memory. Keep these fields coherent when updating existing records.
History has include_in_memory: false. These are advisory metadata, not client
access controls. Do not mass-rewrite legacy records just to normalize headers.

## Current and Historical Continuity Contract (Required)

Resolve the working repository and confirm the intended root before writing state.
Do not accidentally save real-project state to a temporary clone. Explicitly
requested disposable tests are allowed. If the root/worktree is ambiguous, resolve
it with the user; do not guess or create state in another project. Honor existing
authorization to initialize missing state. Report the destination when checkpointing.

Before replacing HANDOFF:

1. Read the entire current file, including older sections in a legacy combined file.
   Review authoritative current source, PLAN/TASKS, issues, test/review evidence,
   and relevant content state. Prepare a new current checkpoint separately.
2. Carry every still-active constraint and unresolved task forward regardless of
   its age. Only mark a task resolved with evidence. Move completed narratives and
   superseded statuses to history, retaining concise evidence references as needed.
3. Review the old and proposed state for secrets/private data before archival.
   If old bytes contain sensitive data, stop shared archival and agree a private
   preservation/sanitization plan; do not silently destroy or publish the source.
4. Capture the prior SHA-256. Archive the complete prior bytes under a unique
   checkpoint ID with a UTC timestamp and SHA-256 in HISTORY. New archives are
   linked byte-exact files under `.agent/archives/handoffs/`; this avoids encoding
   loss and lets readers retrieve one checkpoint. Preserve existing inline and
   legacy history unchanged and add locators to it, never mechanically split at STOP.
5. Read the archive back and verify the bytes/hash and HISTORY locator. Recheck
   HANDOFF for intervening edits before replacing it. Failed archival, corruption,
   or changed state leaves the existing handoff intact. Identical archives deduplicate.
6. Install the reviewed current checkpoint. Normal resume reads only HANDOFF and
   relevant referenced evidence, not HISTORY or the entire prior project record.

Use the bundled `.agent/integrations/checkpoint.py` when available. It enforces
byte preservation, archive verification, deduplication, and hash rechecks. Pass
`--candidate PATH --expected-sha256 HASH --reviewed` after the semantic review.
Its lock serializes helper runs; coordinate independent editors during replacement.
The helper cannot infer unresolved work, sanitize secrets, or prove semantic fidelity.
If an older customized helper is preserved, use the new release snapshot helper
under `.harness/releases/4.2.1/.agent/integrations/` explicitly.

## Continuity Checkpoints (Required)

Checkpoint substantive active work at sprint close/pause, before Git delivery,
before losing session context, and when handing work to another session.
Update active PLAN status and prepare the current handoff as above. Learning work
follows [learning](learning.md); OFF means no additions. The optional
run-checkpoint.sh prints a checklist and never writes state or starts a learner.
Routine questions that create no ongoing work need no fabricated checkpoint.

## Shared continuity delivery

Commit all related sanitized continuity with its work: current/history handoffs,
PLAN/TASKS/CONTEXT, TEST/REVIEW, learnings, wiki, content records, archives, and
existing project history. Keep secrets, environment files, credentials, locks,
bytecode caches, and raw logs private. Stage explicit reviewed files.

The installer preserves ignore rules and reports ones hiding shared files for
review. Narrow those deliberately before delivery without exposing private files.
Do not force-add ignored directories indiscriminately. Follow delivery.md to push,
merge, and verify the files on remote main before claiming shared completion.
The Claude Bash hook checks common direct commits; it is not a shell sandbox.
Other clients follow this rule through advisory instructions unless separately enforced.

## Scale Mode (Tier 2, Default OFF)

Tier 1 uses the task-scoped contracts above. Tier 2 adds optional indexing/wiki
orientation; it never weakens required checks. Repository size can justify a
suggestion, not automatic activation. Follow graphify.md only when requested and
wiki.md when enabled. No models, learning modes, or integrations change incidentally.

Role-specific work loads only the relevant role from docs/roles/README.md.
No optional memory backend is installed; canonical project files retain authority.
