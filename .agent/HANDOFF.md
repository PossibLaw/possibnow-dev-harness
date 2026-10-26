---
contract_version: 1
artifact_type: handoff
status: IN_REVIEW
depends_on: [.agent/PLAN.md, .agent/TASKS.md]
produces: [next_actions, historical_checkpoint_link]
feeds_into: []
memory:
  include_in_memory: true
  tags: [handoff]
---

# Current Handoff — Program 1 rows ORC00, FD01, ORC01, ORC02 merged (unreleased)

## Status
v4.3.1 published October 26, 2026 from a64b505 (tag and GitHub Release by Sal; public bootstrap smoke passed;
receipt in `.agent/RELEASE-4.3.1.md`). Marketplace PR #10 in PossibLaw-Plugins; plugin update follows its merge.
Sal chose option (b) for autonomous detection on October 26: sticky worktree marker released by a human prompt.
Built and cut as 4.3.2 on branch `feat/autonomy-takeover-marker` (PLAN T1-T7, eleven tests). It reaches tonight's run
only after the v4.3.2 tag, marketplace entry and plugin update; until then 4.3.1's `auto-<n>` branch check applies.

Release 4.3.1 cut on branch `release/4.3.1` (October 26, 2026): PRs #35 and #36 plus the caps fix (closed issue frees
the slot; worktrees matched to repos by Orca `repoId`). After merge: tag v4.3.1, GitHub Release, bootstrap smoke,
RELEASE-4.3.1.md, marketplace entry 4.3.1, `claude plugin update`, Codex hook refresh.
Open decision (Sal): autonomous detection is by branch name, so it switches off when a session changes branch, as
both October 26 runs did on Sal's instructions. Options are a sticky worktree marker, with or without a human-takeover
release; see the October 26 session summary. Running sessions keep the hooks they started with.

Branch `Fix-GitHub-Issues` (October 26, 2026): the first autonomous night (October 25, 22:01) started nothing.
Both `auto-ok` issues (aleph #130, Trazomo #850) passed eligibility, then `orca worktree create` failed with
`repo_not_found` because the dispatcher passed `path:~/Aleph` unexpanded, and the report showed a blank reason
because Orca `--json` writes errors to stdout. Fixed in `scripts/dispatch-auto-issues.py` (expanduser on the
selector; `failure_text` reads the JSON error), two tests red first, suite 315, verify-pack DONE. Nights 2 and 3
of the plan in `~/.agents/research/2026-10-25-auto-ok-candidates.md` stay as written (Sal's call, October 26).
After merging that fix (PR #35) the dispatcher was run by hand at 10:39 on October 26 and started
`auto-130` (Aleph) and `auto-850` (Trazomo). Second finding: Orca names the branch `auto-<n>`, not
`orca/auto-<n>`, so the no-merge/no-publish guard and the `agent-auto` PR flag would not have fired; both now
accept either spelling (four tests). The two running agents use whatever hook copy their checkout carries,
so the guard reaches them only once the installed pack is updated (UNCONFIRMED which copy they load).

v4.3.0 published October 24, 2026 from 8275b16 (tag, GitHub Release, public bootstrap smoke passed; receipt in
`.agent/RELEASE-4.3.0.md`). Marketplace PR open in PossibLaw-Plugins; installed plugin update pending.

Release 4.3.0 cut on branch `release/4.3.0` (October 24, 2026): version, pins, fixtures and changelog
moved to 4.3.0; Codex installer ships `autonomy.py`. After merge: annotated tag v4.3.0 on the merge
commit, GitHub Release, public bootstrap smoke into a disposable repo, RELEASE-4.3.0.md, marketplace
entry 4.3.0, installed plugin updated from 4.1.0. PR #14 merged October 24 after a resolve against main.

GR01 enforcement on branch `gr01/enforcement` (October 23, 2026): sync tag labels, autonomous-run
guardrails (`autonomy.py`, `guard-auto-publish.py`, blacklist additions), `dispatch-auto-issues.py`.
Policy and config are in the private repo; the Aleph runner calls the dispatcher after the sync.
TT01 on branch `tt01/ticktick` (October 23, 2026): `scripts/sync-issues-to-ticktick.py` with six tests;
config in the private repo; the Aleph runner calls it after the issue sync with the keychain token.

Merged to main on October 23, 2026: PR #15 (ORC00), then #19 carrying #16 (FD01), #17 (ORC01)
and #18 (ORC02), which had merged into their stacked bases rather than main. Branches and
worktrees removed. No release cut; version stays 4.2.1 until PR #14 lands and v4.3.0 is cut.
Earlier branch-level status kept below for the record.
Board step merged as PR #21 (October 23, 2026, after Sal approved the
`project` scope and the cross-owner check passed): open synced issues go once onto
`AtticusDundee/projects/1`. Three tests; suite 244.

Branch `orc00/orca-setup` off main 58ba0c0 (v4.2.1). Adds `scripts/orca-worktree-setup`
(moved from one machine's `~/.local/bin`), the generic `docs/orca.md` runbook, nine
fixture tests, verify-pack entries, a README pointer, and `.orca` in `.gitignore`.
PR #15 open for Sal's review; nothing merged. Row ORC00 of the machine-wide Program 1
(Orca-first operating system). Row FD01 is stacked on it as branch `fd01/feeder-step`:
the closing skill (2.1.0) now ends with the cross-repo feeder step, with one test.
Row ORC01 is stacked on that as branch `orc01/issue-sync`: `scripts/sync-tasks-to-issues.py`
(register rows → `agent-task` issues, one way, drift reported) with 16 fake-`gh` tests.
Row ORC02 is stacked on that as branch `orc02/work-router`: the `routing-work-to-a-repo`
skill (one sentence → issue in the owning repo, flywheel line, Orca worktree offer).

## Unresolved work
- Program 1 rows in this repo: FD01, ORC01 and ORC02, all in review as stacked PRs. See
  `.agent/TASKS.md`. The Project board step of the sync stays off until Sal approves the
  `project` scope on the gh token and a user board is confirmed to hold organization
  repositories' issues (UNCONFIRMED; GitHub docs disagree with each other).
- Sal's per-repository Orca settings (setup lines, wait-for-setup, LumenAtlas) are recorded
  in the private `AtticusDundee/agent-tasks` repo, not here. Orca's live settings on Sal's
  Mac differed from the recorded recommendation on October 23, 2026; reconciling them is
  Sal's call (recorded there).
- Carried from PR #14 (branch feat/v4.3.0-git-guards-and-pocock-skills, unmerged): v4.3.0
  release not cut (version, README pins, bootstrap tag, publish smoke); customized
  installed projects still need their own reviewed migration; live client compliance and
  semantic optimize apply UNCONFIRMED; Sal's machine runs the cached plugin at 4.1.0;
  Codex parity for the Pocock-derived skills UNCONFIRMED.
- This branch and PR #14 both touch CHANGELOG.md, README.md and `.agent/` continuity;
  whichever merges second needs a small conflict resolution.

## Active constraints
- This repo is public: only generic Orca mechanics here; anything specific to a person
  (which repos, setup lines, board, sync configuration) stays in a private repo.
- Orca worktrees are created only when Sal asks; no agent starts work on its own until
  the autonomy policy (Program 1 row GR01) is written and approved.
- Ordinary `git push` must stay allowed; Pocock-derived files keep MIT attribution (PR #14).

## This branch (PR #14) on top of main

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
- `uvx --with pytest pytest -q`: 241 passed with ORC02 (238 with ORC01's retry fix, 236 with ORC01 (222 with FD01, 221 for ORC00 alone, baseline 212); the nine new tests failed first
  (script missing), then passed after the move.
- `scripts/verify-pack.sh`: DONE: verification passed (now requires the script, runbook and test).
- `docs/orca.md` field names checked against Orca CLI 1.4.232 (`orca repo list --json`,
  `orca project setups --json`); the custom issue command is not exposed by the CLI.
- Previous checkpoint (v4.2.1 published) archived in HISTORY by the checkpoint helper.

## Next actions
1. Switch the harness main checkout to `main` so the Aleph nightly runner finds `scripts/sync-tasks-to-issues.py` (checkout currently holds PR #14's branch).
2. Sal confirms the routing table and answers the GR01/FW01 questions in the private repo.
3. Cut v4.3.0 after PR #14 merges; update the installed plugin on Sal's machine.
- `uvx --with pytest pytest -q`: 241 passed (baseline 212); red run showed 18 expected failures first.
- `scripts/verify-pack.sh`: DONE: verification passed.
- Disposable-fixture install: both skills present under .claude/skills and .agents/skills.
- PLAN.md: G1–G3, S1–S2 acceptance cases.
- Previous checkpoint (v4.2.1 published) archived in HISTORY.

## Next actions
1. Review and merge the PR.
2. Cut v4.3.0: bump plugin.json, README pins, tests' tag fixtures; run publish smoke.
3. Update the installed plugin on Sal's machine from 4.1.0 to the new release.
