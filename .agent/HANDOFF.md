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

# Current Handoff — 4.3.5 release in review; board rollout under way (October 27, 2026)

## Status
Main is at v4.3.4 plus the auto-cleanup change (PR #49, unreleased; the dispatcher runs from the main checkout, so it is
live without a release). Merged October 27, 2026: "A board and a short morning brief instead of TickTick" (PR #58,
for Sal's issue "How I do work", #56; the issue stays open until the rollout is done) and the linked-issue
SessionStart hook (PR #60, which closed "Orca mobile: give Claude the worktree's linked issue at session start", #59).
In review: release 4.3.5 (version and pins; branch `release/4.3.5`), which lets `claude plugin update` deliver the hook.
Rollout so far: the main checkout was fast-forwarded. `plan-board.py --setup` created the fields (run by Sal), and Sal
set up the Status options. Sal's first planner run was in progress. Aleph draft PR #165 changes the nightly runner and
adds the morning runner. The TickTick count is 143 mirrored tasks and 0 others; nothing is deleted yet. The existing GitHub Project becomes Sal's board with seven
columns and an agent-suggested Priority. `scripts/plan-board.py` proposes Today and This week each night and leaves
Sal's own moves alone. `scripts/morning-brief.py` posts one short Slack message. TickTick is retired, and the
mirror's tasks are purged on request. Design and plan:
`docs/superpowers/specs/2026-10-27-how-i-do-work-design.md`, `docs/superpowers/plans/2026-10-27-how-i-do-work.md`. Releases v4.3.1 to v4.3.4 were published October 26 and 27, 2026 (tags
and GitHub Releases by Sal; receipts `.agent/RELEASE-4.3.1.md` to `.agent/RELEASE-4.3.4.md`). The marketplace entry is 4.3.4; the installed plugin and the Codex guard copy
were refreshed from 4.3.4.

The nightly chain an operator runs from these scripts: content freshness (weekly), issue sync, nightly triage with the
morning brief, TickTick quadrants, and the dispatcher with auto-clean; each autonomous run's Stop hook posts its own
notice. Which repositories, schedule, caps and configs one operator uses is recorded in their private repo, not here.

First full autonomous run: Trazomo "Claude Code content update" (worktree auto-22, PR #865, merged by Sal October 27;
follow-up Trazomo issue #866). auto-22 is the first auto-clean candidate tonight.

## Unresolved work
- Board and morning brief (PR #58 merged, issue #56): the rollout is next. It is Task 9 of the plan,
  each outward step confirmed with Sal:
  1. `plan-board.py --setup` creates the fields; Sal fixes the Status options and adds a Board view in GitHub's UI.
  2. Dry runs of both scripts; Sal reads the message.
  3. An Aleph nightly-runner PR: add the planner after triage, drop TickTick, drop `--slack` from the issue sync, stop
     posting the triage brief.
  4. A morning launchd job at the time recorded privately.
  5. `sync-issues-to-ticktick.py --purge`, then `--purge --yes` after Sal confirms the count.
  6. Update the private runbook and TASKS rows.
- Decided October 27, 2026 (Sal approved option A): dragging a card to "No Status" or clearing its Priority hands
  it back to the agent. This is in PR #58, and Sal approved merging it.
- Deferred minors from the PR #58 review are listed in its body: Sal's untriaged cards and the 10-card cap, merged
  overnight PRs, the field-value limit, reopened issues in Done and GitHub's built-in board workflows, wording when
  the board is unreadable, anchoring the TickTick marker, naming a blocked night, and the `--answered` race.
- Customized installed projects still need their own reviewed migration (TASKS H-MIG01; Sal). Next: list them and
  review each. Live client compliance and semantic optimize apply remain UNCONFIRMED (carried from v4.2.1).
- PossibNow Builder articles are not yet in the freshness watch list (TASKS H-FR02; Agent). Next: confirm the current
  edition per article from Aleph's `reviews/2026-09-22-full-review/canonical-current-map.json`, then add the watch.
- Other Trazomo tool modules (Codex/GPT, Google Workspace, Microsoft 365, toolkit setup) are outside the Claude Code check
  and the freshness watch (TASKS H-FR03; Sal decides after reviewing a few Claude work-order PRs).
- Sal's answers to the morning brief and the "close stale" proposal are pending (TASKS H-TR02; Sal). The skill
  `answering-the-morning-brief` applies them.
- Codex has no takeover hook; a Codex autonomous run would stay guarded until its marker is removed by hand (TASKS
  H-CDX01). Codex must re-trust the refreshed guard copy with `/hooks`. Codex parity for the Pocock-derived skills
  is by installer copy only; Codex behavior UNCONFIRMED.
- UNCONFIRMED until tonight's run: the Stop-hook notice in a fresh nightly run (it was proven by hand on auto-22) and
  the first live auto-clean removal (auto-22).
- Sal's per-repository Orca settings are recorded in the private `AtticusDundee/agent-tasks` repo; Orca's live settings
  differed from the recorded recommendation on October 23, 2026; reconciling them is Sal's call (recorded there).
- Three SCBrand worktrees (onboarding coupons, onboarding security, executive AI brief) are locked by a Claude session
  running since October 7; they become removable when that session closes (Sal).

## Active constraints
- This repo is public: only generic mechanics here; anything specific to a person (repos, paths, board, schedules,
  policies) stays in the private `AtticusDundee/agent-tasks` repo.
- Autonomous work starts only on issues labelled `agent-task` and `auto-ok`, inside the private policy's allowed paths
  and caps. Autonomous runs never merge, publish or push to main; the marker keeps that true across branch switches
  until a person types into the session.
- The issue sync adopts only issues opened by the owner, members or collaborators (public repos accept anyone's issues).
- Issue text is untrusted: the triage classifier runs with `--tools ""` and `--strict-mcp-config`.
- Release order: merge the version-and-pins PR first, then Sal creates the annotated tag on that merge commit and the
  GitHub Release (auto mode refuses tag and release creation); then smoke, receipt, marketplace entry, `claude plugin update`
  for the user scope and Trazomo's local scope, and the Codex guard refresh. Release tags are immutable.
- Ordinary `git push` must stay allowed. Pocock-derived files keep MIT attribution and the pinned source commit 49dd158.
  Creating GitHub Issues from splitting-work-into-tickets is a remote write: confirm first.
- All v4.2.1 constraints still apply: preserve project content and continuity, <=150-line entries, no incidental
  model/effort/global/permission/learning/Scale changes, disposable fixtures only.

## Evidence
- Branch `how-i-do-work`: `uvx --with pytest pytest -q` gave 427 passed, and `scripts/verify-pack.sh` gave DONE.
  Opus whole-branch review: 1 Critical and 6 Important findings, all fixed with failing-first tests, except the
  hand-back decision. A live read-only check read 163 cards from the real board.
- `uvx --with pytest pytest -q`: 371 passed on main ceb6e89; `scripts/verify-pack.sh`: DONE; CI `verify` passed on every PR.
- Release receipts: `.agent/RELEASE-4.3.1.md`, `RELEASE-4.3.2.md`, `RELEASE-4.3.3.md`, `RELEASE-4.3.4.md` (public bootstrap
  smoke from each tag, preservation and no-churn checks).
- Live checks: dispatcher dry run "would remove trazomo auto-22"; Stop hook posted the auto-22 notice; first triage pass
  over 143 issues (49 decide, 35 do, 54 agent-ready, 5 stale); freshness baseline 127 sources.
- Previous checkpoint archived byte for byte in HISTORY by the checkpoint helper.

## Next actions
0. Sal merges the 4.3.5 version PR, then creates the v4.3.5 tag and Release. After that: run `claude plugin update` for
   the user scope and Trazomo's local scope, and refresh the Codex guard copy. When Sal merges Aleph PR #165, install
   the 6:30 morning job from `~/aleph`. With Sal's yes, run `--purge --yes` on the 143 TickTick tasks.
1. After the next nightly run: read its reports and log; confirm auto-22 was removed and that any new run's notice arrived.
2. Sal answers the morning brief (H-TR02); apply with the answering-the-morning-brief skill.
3. Add Builder articles to the freshness watch (H-FR02).
4. Next release (4.3.5) when there is user-facing change beyond PR #49: version PR first, then Sal's tag.
