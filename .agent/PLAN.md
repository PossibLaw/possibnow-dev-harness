---
contract_version: 1
artifact_type: plan
status: IN_REVIEW
depends_on: []
produces: [eval_ids, release_scope]
feeds_into: [.agent/TEST.md]
memory:
  include_in_memory: true
  tags: [plan]
---

# Current (October 27, 2026): v4.3.4 on main; nothing in progress

Shipped October 26 and 27, 2026 (PRs #35 to #49, releases v4.3.1 to v4.3.4): autonomous runs work end to end (start,
guard, takeover, notice, own-repo placement, cleanup); the issue sync reports status by name and tracks issues started
anywhere; the content-freshness engine and the nightly triage with the morning brief are live. Each change was test-first;
acceptance evidence is in the PR bodies and the release receipts. The sections below are the per-change plans, kept as
history; their acceptance cases all pass.

Open work and next actions live in `.agent/TASKS.md` (rows H-MIG01, H-FR02, H-FR03, H-TR02, H-CDX01) and `.agent/HANDOFF.md`.

# Unreleased: sticky autonomous-run marker with human takeover (GR01 follow-up)

Baseline: main 63364ef (v4.3.1 published). Branch: feat/autonomy-takeover-marker.
Decision: Sal chose option (b) on October 26, 2026. Detection by branch name switched off in both
October 26 runs when the session changed branch; a strict marker would have blocked Sal's own merges.

Design: after `orca worktree create` returns, the dispatcher writes `agent-auto.json` into the new
worktree's private git directory (survives branch switches, goes away with the worktree). The guard
treats a marked worktree as autonomous until the marker says a person took over. A new
UserPromptSubmit hook records the first prompt as the dispatcher's; any later prompt, in that session
or another one in the same worktree, is a person, so the marker is released and normal ask-first
rules apply. `AGENT_AUTO=1` still forces autonomous; `auto-<n>` branches without a marker still count.

Acceptance (Given/When/Then):
- T1 happy path: Given a dispatcher-marked worktree on any branch, When the agent runs `gh pr merge`
  or a publishing MCP tool, Then it is blocked, even after switching to `fix/anything`.
- T2 takeover: Given the dispatcher's prompt was recorded, When a person types a second prompt,
  Then the hook says the guard is released and `gh pr merge` asks first instead of blocking.
- T3 other session: Given a recorded dispatcher session, When a prompt arrives from a different
  session in that worktree, Then the guard is released.
- T4 race edge: Given the dispatcher's prompt reached the session before the marker existed, When the
  first person's prompt arrives, Then the transcript shows an earlier prompt and the guard is released.
- T5 failure/security: Given an autonomous run, When the agent tries to delete or rewrite
  `agent-auto.json` through Bash, Then it is blocked; a Write or Edit to it is refused in every session.
- T6 dispatcher: Given an eligible issue, When the dispatcher starts it, Then the new worktree carries
  a marker naming the repo and issue; a marker failure is reported and does not stop the run.
- T7 unmarked: Given no marker and an ordinary branch, Then behaviour is unchanged (merge asks first),
  and the prompt hook prints nothing.

UNCONFIRMED: whether Claude Code writes the current prompt to the transcript before UserPromptSubmit
fires (T4 does not depend on it: only prompts with different text count); Codex has no takeover hook,
so a Codex auto run stays blocked until its marker is removed by hand.

# Unreleased: Orca worktree setup helper and runbook (ORC00)

Baseline: main 58ba0c0 (v4.2.1 published). Branch: orc00/orca-setup.
Source: `~/.local/bin/orca-worktree-setup` written October 20, 2026 (one machine, untracked)
and the Orca session notes of October 14 and 20, 2026.

Scope: commit the setup helper as `scripts/orca-worktree-setup`; add the generic runbook
`docs/orca.md`; require both in `scripts/verify-pack.sh`; ignore `.orca`. No version bump,
release pins, installed projects, globals, models, permissions, learning mode, or Scale.
Per-person Orca settings are out of scope for this public repo.

## Acceptance and evidence plan

- O1 (happy): with `ORCA_ROOT_PATH` and `ORCA_WORKTREE_PATH` set, the helper copies
  `.claude/settings.local.json` and env files, copies `--clone` paths, links Claude memory,
  prints `ready <worktree>`.
- O2 (edge): a file already in the worktree is kept, never overwritten; a rerun copies
  nothing; a missing `--clone` source is skipped silently; an empty argument is ignored;
  no `npm ci` without `package-lock.json`.
- O3 (failure/safety): without the Orca variables the helper exits non-zero naming
  `ORCA_ROOT_PATH`; an unknown option exits 2. Secrets are copied only from the main
  checkout into a gitignored path of the worktree, never printed.
- V1: `scripts/verify-pack.sh` requires the helper (executable), the runbook and the test;
  full suite green.

## Task Checklist
- [x] O1–O3 covered by `tests/harness/test_orca_worktree_setup.py` (red first, then green)
- [x] V1 verify-pack passes
- [ ] PR reviewed and merged by Sal

## Addendum: issue sync (ORC01, same baseline, stacked branch orc01/issue-sync)

- S1 (happy): first run creates one labelled issue per identified open row with marker, source and flywheel line; a second run changes nothing; a prose edit updates the issue; a DONE row or a row that leaves the register closes it.
- S2 (edge): rows without an ID are reported, not invented; `--only` limits to one repo; `--dry-run` writes nothing and reports counts; the board step is skipped while disabled.
- S3 (failure/safety): a row matching a card or bank pattern is never sent and is named in the summary; an issue closed or edited on GitHub is reported as drift and never reopened or written back; a repository without a register is an error in the summary, not a crash.
- Covered by `tests/harness/test_sync_tasks_to_issues.py` (red first, 14 tests). Live dry run on October 23, 2026 planned 147 issues across four private repositories.


## Also unreleased on this branch (PR #14): git guardrail gaps + Pocock-derived skills

Baseline: main 58ba0c0 (v4.2.1 published). Branch: feat/v4.3.0-git-guards-and-pocock-skills.
Source for adopted skills: mattpocock/skills @ 49dd158d1076134a641b33efb035946536778336 (MIT).

Scope: close force-push/branch-delete/discard gaps in `scripts/guardrails/blacklist.py`;
add user-invoked `splitting-work-into-tickets` and `running-a-retro` skills; add
`docs/references/writing-for-agents*.md` as a maintainer-only reference. No version bump,
release pins, installed projects, globals, models, permissions, learning mode, or Scale.
v4.3.0 is cut separately after its publish smoke gate.

## Acceptance and evidence plan

- G1 (happy): `git push origin main`, `push -u origin feature`, `branch -d`, `restore --staged .`, `clean -n` run silently.
- G2 (edge): force-push to main/master is blocked in every spelling (`-f`, trailing `--force`/`-f`, `--force-with-lease`, `+main`, `+HEAD:master`); `git clean -df|-xdf|--force` blocked; `push ... && cd main` stays silent.
- G3 (failure/safety): other force-pushes, `branch -D`, `branch --delete --force`, `checkout .`, `checkout -- .`, `restore .`, `restore --worktree .` ask first.
- S1: installer delivers both new skills to `.claude/skills/` and `.agents/skills/` in a disposable fixture; writing-for-agents is not shipped.
- S2: `scripts/verify-pack.sh` requires both skills and their metadata; full suite green.
