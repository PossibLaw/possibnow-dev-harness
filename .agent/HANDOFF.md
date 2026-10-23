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

# Current Handoff — Orca worktree setup helper and runbook (ORC00, unreleased)

## Status
Branch `orc00/orca-setup` off main 58ba0c0 (v4.2.1). Adds `scripts/orca-worktree-setup`
(moved from one machine's `~/.local/bin`), the generic `docs/orca.md` runbook, nine
fixture tests, verify-pack entries, a README pointer, and `.orca` in `.gitignore`.
PR #15 open for Sal's review; nothing merged. Row ORC00 of the machine-wide Program 1
(Orca-first operating system). Row FD01 is stacked on it as branch `fd01/feeder-step`:
the closing skill (2.1.0) now ends with the cross-repo feeder step, with one test.

## Unresolved work
- Program 1 rows in this repo: FD01 (in review, stacked PR) and ORC01 (generic issue-sync
  script, next). See `.agent/TASKS.md`.
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
- All v4.2.1 constraints still apply: preserve project content and continuity, <=150-line
  entries, no incidental model/effort/global/permission/learning/Scale changes,
  disposable fixtures only, immutable release tags.

## Evidence
- `uvx --with pytest pytest -q`: 222 passed with FD01 (221 for ORC00 alone, baseline 212); the nine new tests failed first
  (script missing), then passed after the move.
- `scripts/verify-pack.sh`: DONE: verification passed (now requires the script, runbook and test).
- `docs/orca.md` field names checked against Orca CLI 1.4.232 (`orca repo list --json`,
  `orca project setups --json`); the custom issue command is not exposed by the CLI.
- Previous checkpoint (v4.2.1 published) archived in HISTORY by the checkpoint helper.

## Next actions
1. Sal reviews and merges the ORC00 PR (or asks for changes).
2. Sal reviews the stacked FD01 PR (merge after ORC00).
3. ORC01: generic issue-sync script with fixture tests, own branch and PR.
