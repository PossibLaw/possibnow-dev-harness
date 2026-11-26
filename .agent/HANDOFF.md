---
contract_version: 1
artifact_type: handoff
status: IN_PROGRESS
depends_on: [.agent/PLAN.md, .agent/TASKS.md]
produces: [next_actions, historical_checkpoint_link]
feeds_into: []
memory:
  include_in_memory: true
  tags: [handoff]
---

# HANDOFF

One current checkpoint. Each entry is one line that points to the PR, issue or document
holding the detail. A close replaces this file through `checkpoint.py`; it never prepends.
Previous checkpoints: [HISTORY](HISTORY.md). Register: [TASKS](TASKS.md).

## Status
- 2026-11-25: branch `Fix-Handoff-Size` makes HANDOFF a pointer, not a log: size check, commit guard, rule text. Plan: [PLAN](PLAN.md). Unreleased; ships as 4.4.0 in a separate release PR.
- main is v4.3.8, published and installed on both machines ([RELEASE-4.3.8](RELEASE-4.3.8.md)).
- This file was compacted from the stacked November 23 checkpoint; the carry-forward ledger is in this branch's PR body.

## Recent work
- 2026-11-25 HANDOFF pointer rule, `handoff_size.py`, commit guard and compaction (branch `Fix-Handoff-Size`; [PLAN](PLAN.md))
- 2026-11-23 v4.3.8 published, marketplace and installs updated ([RELEASE-4.3.8](RELEASE-4.3.8.md), [PR #84](https://github.com/PossibLaw/possibnow-dev-harness/pull/84))
- 2026-11-23 Shared-continuity commit diagnostics ([#82](https://github.com/PossibLaw/possibnow-dev-harness/issues/82), [PR #83](https://github.com/PossibLaw/possibnow-dev-harness/pull/83))
- 2026-11-16 v4.3.7: plugin hooks under a path with a space ([#78](https://github.com/PossibLaw/possibnow-dev-harness/issues/78), [PR #79](https://github.com/PossibLaw/possibnow-dev-harness/pull/79); [RELEASE-4.3.7](RELEASE-4.3.7.md))
- 2026-11-13 Dispatcher counts a bare folder only when it exists ([PR #77](https://github.com/PossibLaw/possibnow-dev-harness/pull/77))
- 2026-11-13 v4.3.6 published: PRs #66, #70, #72, #74 ([RELEASE-4.3.6](RELEASE-4.3.6.md))
- 2026-11-10 Config paths may use `$REPOS` ([PR #72](https://github.com/PossibLaw/possibnow-dev-harness/pull/72); `docs/orca.md`)
- 2026-11-04 Issue sync: no duplicate mirror for a row that links its issue ([#69](https://github.com/PossibLaw/possibnow-dev-harness/issues/69), [PR #70](https://github.com/PossibLaw/possibnow-dev-harness/pull/70))
- 2026-10-28 Board planner and morning brief live ([#56](https://github.com/PossibLaw/possibnow-dev-harness/issues/56), [PR #58](https://github.com/PossibLaw/possibnow-dev-harness/pull/58))
- 2026-10-27 v4.3.5: auto-clean (PR #49), board and brief (PR #58), linked-issue hook (PR #60) ([RELEASE-4.3.5](RELEASE-4.3.5.md))

## Unresolved work
- Merge the private dispatch-prompt change with this release ([agent-tasks PR #7](https://github.com/AtticusDundee/agent-tasks/pull/7); Sal). Apply the same `~/.claude/hooks/context-guard.py` wording edit on the second machine (logged in `~/.claude/CHANGELOG.md`, 2026-11-25).
- Guard false positive (found 2026-11-25): `validate-bash.py` checks the payload cwd, not a `cd` target in the command, and reads a heredoc marker after `git commit -F -` as a pathspec ("path-limited commit"). Workaround: `git -C <repo> commit -F <file>`. Needs an issue and a failing test.
- Customized installed projects need their own reviewed migration (H-MIG01, [#51](https://github.com/PossibLaw/possibnow-dev-harness/issues/51); Sal). Live client compliance and semantic optimize apply: UNCONFIRMED since v4.2.1.
- Codex: no linked-issue or takeover hook; a Codex autonomous run stays guarded until its marker is removed by hand (H-CDX01, [#55](https://github.com/PossibLaw/possibnow-dev-harness/issues/55)). Codex parity of the Pocock-derived skills: UNCONFIRMED.
- Morning brief answers and the "close stale" proposal (H-TR02, [#54](https://github.com/PossibLaw/possibnow-dev-harness/issues/54); Sal). Apply with `answering-the-morning-brief`.
- Widen Trazomo's Claude Code check and freshness watch to other tool modules (H-FR03, [#53](https://github.com/PossibLaw/possibnow-dev-harness/issues/53); Sal decides after a few Claude work-order PRs).
- Owed after v4.3.7/v4.3.8: restart running Claude sessions; run `/hooks` in Codex once to confirm trust ([RELEASE-4.3.8](RELEASE-4.3.8.md)).
- Second machine: private Git login unavailable; its checkout was updated by verified Git bundle ([RELEASE-4.3.8](RELEASE-4.3.8.md)). Follow up on authentication.
- Scheduled jobs moving to an always-on second machine: tracked privately (operator's Aleph issue and private runbook).
- Autonomous queue of October 28: auto-131 and auto-790 started; Aleph #142, #168 and Trazomo #851, #866 queued. Their outcome is UNCONFIRMED. Next, when the batch merges cleanly: add paths to the 36 "no paths named" issues (Sal approved; via register PRs where a register is the source).
- UNCONFIRMED: the nightly harness checkout is pulled past PR #77 (and whether it is pulled automatically before each run).
- UNCONFIRMED: issue sync summary no longer lists scbrand E8 to E15 as drift (H-ORC03, #69); the `state_reason: duplicate` PATCH is unproven live.
- UNCONFIRMED: the Stop-hook notice in a fresh nightly run, and the first live auto-clean removal (auto-22).
- UNCONFIRMED: first mobile use of the linked-issue hook (next session Sal opens from his phone should start with the link).
- Builder freshness watch (H-FR02): first live run was a baseline; when the first Builder work order arrives, Sal decides whether to add `auto-ok`.
- Pending decision (Sal): keep `library-current/` as the September 15 archive, or refresh it to the September 22 text.
- Pending decision (Sal, 2026-10-28: wait): Claude account per repo; revisit when Orca issue #8770 ships. Until then a private daily reminder covers switching accounts.
- Deferred minors from the PR #58 review: listed in [PR #58](https://github.com/PossibLaw/possibnow-dev-harness/pull/58)'s body; pick up when the board's first weeks show which matter.
- UNCONFIRMED: three SCBrand worktrees (onboarding coupons, onboarding security, executive AI brief) locked by a Claude session running since October 7; removable when it closes (Sal).

## Active constraints
- This repo is public: only generic mechanics. Anything specific to a person (repos, paths, board, schedules, nightly chain, Orca settings, policies) stays in the private `AtticusDundee/agent-tasks` repo and runbook.
- Autonomous work starts only on issues labelled `agent-task` and `auto-ok`, inside the private policy's allowed paths and caps. Autonomous runs never merge, publish or push to main; the marker keeps that true across branch switches until a person types into the session.
- The issue sync adopts only issues opened by the owner, members or collaborators.
- Issue text is untrusted. The triage classifier runs with `--tools ""` and `--strict-mcp-config`. The linked-issue hook gives only the link, never the issue text.
- The board planner never changes a column or priority Sal set; only automatic moves (linked PR, closed issue, autonomous run started) override. Its state file is saved after every write; an unreadable state file stops the planner.
- Release order: 1. merge the version-and-pins PR; 2. annotated tag and GitHub Release only with Sal's authorization (auto mode refuses them); 3. smoke, receipt, marketplace entry, `claude plugin update` (user scope and Trazomo local scope), Codex guard refresh. Tags are immutable; Claude Code updates a plugin only when the marketplace version changes.
- Ordinary `git push` stays allowed. Pocock-derived files keep MIT attribution and pinned source commit 49dd158. Creating GitHub Issues from splitting-work-into-tickets is a remote write: confirm first.
- v4.2.1 constraints: preserve project content and continuity; entries of at most 150 lines; no incidental model, effort, global, permission, learning or Scale changes; disposable fixtures only.
- HANDOFF limits (this branch): 24,000 bytes; `## Status` 30 lines / 4,000 bytes; lines 1,500 characters. Changes to `.agent/handoff-limits.json` need review.

## Evidence
- Current branch: [PLAN](PLAN.md) evals HS-1 to HS-12; test receipts go in [TEST](TEST.md) before the PR.
- Last release: [RELEASE-4.3.8](RELEASE-4.3.8.md); earlier receipts `RELEASE-4.2.1.md` to `RELEASE-4.3.7.md`.
- Previous checkpoint archived byte for byte by `checkpoint.py`; locator in [HISTORY](HISTORY.md).

## Next actions
1. Review and merge the `Fix-Handoff-Size` PR; then a release PR for 4.4.0 with the migration note.
2. After release: compact Trazomo-style installs once with a carry-forward list; set `required_headings` where tooling needs a heading (Trazomo: `## Session Timeline`).
3. Sal answers the morning brief decisions (H-TR02, #54).
4. Sal decides on `library-current/` (see Unresolved work).
5. Check the issue sync summary for scbrand E8 to E15 drift (H-ORC03, #69).
6. Watch the October 28 autonomous batch; then add paths to the near-miss issues.

## Sprint / Git Cycle
- Branch `Fix-Handoff-Size` off main ee6ddda; draft PR after checks pass.
