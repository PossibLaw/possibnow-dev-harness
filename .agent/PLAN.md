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
