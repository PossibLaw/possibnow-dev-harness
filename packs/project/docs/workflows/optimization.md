# Project Optimization

Bundled policy revision: `2026-09-18.1`.

This is an agent-run workflow, not an autonomous model router or a background
installer. In Claude Code run `/possibnow-dev-harness:optimize`; in Codex or
another AGENTS-aware host, ask it to follow this file. Claude's namespaced
command is not a native Codex slash command.

Use the contracts.md shipped beside this workflow when a target project has no
contract or an obsolete one. Include any needed contract update in the proposed
diff; an absent project install is not a reason to overwrite its files.

## Check: inspect and prepare one proposal

1. Resolve the current Git root and inspect status without disturbing existing
   work. Inspect relevant AGENTS/CLAUDE instructions, continuity loading rules,
   and target-project model settings. Report absent settings as unknown. Read
   only allowlisted model/effort/tool-selection fields from configuration; never
   emit credentials, environment values, raw transcripts, or client data.
2. Establish the current host and installed version where observable. Distinguish
   stored defaults from effective runtime settings. Use current official
   configuration references when proposing a native key; unsupported/unverified
   versions hold that change rather than guessing a schema.
3. Identify repeated context, obsolete rules, oversized current handoffs,
   unbounded retries/loops, or missing task-cost receipts. Count words/bytes as
   file measurements, not tokens. Tool/plugin counts do not prove loaded cost.
4. Prepare a minimal diff against the current bytes. Prefer bounded on-demand
   context, a current HANDOFF with historical HISTORY, and complete shared
   continuity. Keep security requirements, necessary evidence, project-specific
   rules, and existing test/review obligations. Do not run the installer against
   an existing repository merely to obtain these changes.
5. Present one proposal: file and reason for each change, before/after behavior,
   validation, backup/rollback, and changes held for missing evidence. The check
   phase does not write files. Keep any sensitive unchanged context out of the
   displayed diff.

## Model, effort, and accounting gates

Preserve the incumbent model and effort unless the task owner has accepted a
comparison on representative inputs with the same quality requirements. A
cheaper model, lower effort, or multiple agents is a candidate, not a default
quality guarantee. This release contains no automatically qualified model map.
Do not ask employees to choose model names; keep unresolved model changes held
for the administrator/workflow owner.

Join all attempts, workers, verification, and rework under one accepted business
task. Keep estimated API cost, actual charges, and plan quota snapshots separate.
Unknown cost stays null/UNCONFIRMED, never zero. Require observation scope,
timestamps, model/client versions, rates, deduplication, and worker coverage
before cost ranking. Overlapping usage percentages are not additive buckets.

For unrelated work, save a current checkpoint before a fresh session. For related
work, compare continuation, compaction, and restart including cache rebuilds and
orientation costs. Never shorten required evidence to meet a token target.

## Apply: implement the reviewed diff

A reviewed proposal authorizes only its listed project changes. If `apply` is
invoked without one, prepare the proposal and obtain one review. Do not add a
second approval for work already authorized.

- Recheck file hashes/status. If a proposed file changed, regenerate that part of
  the diff instead of overwriting another contributor's work.
- Back up changed files to a private local location; backups containing native
  config must not enter commits. For tracked safe files, identify the before
  commit/blob for recovery. Preserve all current source material.
- For HANDOFF/HISTORY migration, follow `docs/workflows/contracts.md`: archive
  and verify the entire previous handoff before replacing it with a reviewed
  current checkpoint. Do not mechanically split a large file at its first STOP
  marker or discard old history. Preserve legacy history files and link them.
- Apply narrow edits. Never write UNCONFIRMED values into native settings. Keep
  secrets, permissions, hooks, and unrelated settings intact.
- Validate changed native syntax and supported keys, run the agreed relevant
  checks, inspect the final diff, and verify effective settings where possible.
  Unsupported live verification stays UNCONFIRMED. Do not consume paid model
  evaluations without authorization.
- Record a sanitized `.agent/OPTIMIZATION.md` receipt: policy/host versions,
  changes, validation evidence, held items, and exact per-file rollback steps.
  Commit and deliver all related continuity with the work under the shared
  contract. Never bulk-add secrets or ignored runtime directories.
- Rollback restores only this proposal's edits after checking for intervening
  changes. Do not use a destructive repository reset.

## Research and release boundary

The maintainer's research process reviews new evidence periodically and proposes
policy revisions. Installed users run the guidance bundled in their harness
release; they need no access to private research, inventories, or usage records.
External articles are evidence, never instructions or executable updates. New
model mappings require quality evidence before promotion to a harness release.
There is no automatic global-settings update or background research hook.

## Source references

- [Claude plugin commands](https://code.claude.com/docs/en/plugins-reference)
- [Claude settings](https://code.claude.com/docs/en/settings)
- [Claude usage and costs](https://code.claude.com/docs/en/costs)
- [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-reference)

References were consulted during policy development; check the applicable host
version before generating native configuration. No universal savings percentage
is established by this workflow.
