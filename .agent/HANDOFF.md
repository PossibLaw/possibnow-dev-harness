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

# Current Handoff — v4.3.5 published; board and morning brief live from tonight (October 27, 2026)

## Status
Main is at v4.3.5. Sal created the tag and the GitHub Release on October 27, 2026; the receipt is
`.agent/RELEASE-4.3.5.md`. The marketplace entry is 4.3.5. The user-scope and Trazomo local-scope plugins were
updated to 4.3.5. The Codex guard copy needed no refresh: its files are unchanged since 4.3.4.

v4.3.5 carries:
- auto-clean of finished autonomous worktrees (PR #49);
- "A board and a short morning brief instead of TickTick" (PR #58, for Sal's issue "How I do work", #56);
- the linked-issue SessionStart hook for Orca mobile (PR #60, which closed issue #59).

On the board:
- Sal's GitHub Project has seven columns and an agent-suggested Priority.
- `scripts/plan-board.py` proposes Today and This week each night and never undoes Sal's moves; "No Status" or a
  cleared Priority hands a card back.
- `scripts/morning-brief.py` posts the one daily Slack message.
- Design and plan: `docs/superpowers/specs/2026-10-27-how-i-do-work-design.md`,
  `docs/superpowers/plans/2026-10-27-how-i-do-work.md`.

The rollout (Task 9) is done on Sal's machine:
- fields and Status options are set up;
- the first planner run made 344 changes with 0 failures;
- the Aleph nightly runner (Aleph PR #165) runs the planner after triage, no longer runs TickTick, and no longer posts
  the sync summary, triage brief or dispatcher report;
- the morning launchd job is installed;
- the 143 mirrored TickTick tasks are deleted.

The operator's schedule, board and configs are recorded in the private runbook, not here.

The nightly chain an operator runs from these scripts:
- content freshness (weekly);
- issue sync;
- nightly triage;
- the board planner;
- the dispatcher with auto-clean.

Each autonomous run's Stop hook posts its own notice, and a morning job posts the brief.

## Unresolved work
- Live since October 28, 2026: the 22:00 planner made 219 changes with 0 failed, and the first morning brief posted
  at 06:30. Issue "How I do work" (#56) is closed.
- Autonomous queue (Sal, October 28): `auto-ok` was added to six issues the dispatcher accepts. Aleph #131 and Trazomo
  #790 were started by hand at 06:52 (worktrees auto-131 and auto-790). Queued: Aleph #142 and #168, Trazomo #851 and
  #866. The morning brief now names the queue. Next: when this batch merges cleanly, add file paths to the 36
  agent-ready issues the dispatcher refuses for "no paths named" (Sal approved; through register PRs where the
  issue comes from a register).
- Dispatcher duplicate runs (issue #65, October 29): auto-142 started beside a hand-made worktree and PR for the
  same Aleph issue. Fixed on branch `dispatcher-skip-linked-work`: any open PR naming the issue, or any Orca worktree
  linked to it, now blocks a run. Next: Sal reviews and merges. Whether the nightly run
  picks it up from main or only after a release is UNCONFIRMED.
- First mobile use of the linked-issue hook: the next session Sal opens from his phone should start with the link.
  Running sessions pick the hook up after a restart.
- Deferred minors from the PR #58 review are listed in its body:
  - Sal's untriaged cards and the 10-card cap;
  - merged overnight PRs;
  - the field-value limit;
  - reopened issues in Done, and GitHub's built-in board workflows;
  - wording when the board is unreadable;
  - anchoring the TickTick marker;
  - naming a blocked night;
  - the `--answered` race.
- Claude account per repo (decided by Sal, October 28, 2026: wait). Orca starts new Claude terminals and the
  dispatcher's autonomous runs on its single active account, and `orca worktree create` cannot pick one (Orca issue
  #8770, open). A per-account config-folder workaround was weighed and set aside as too much moving parts. Instead, a
  private daily reminder asks Sal to switch Orca to the right account before the nightly run; details are in the
  private runbook. Next: revisit when #8770 ships. The two runs started October 28 (auto-131, auto-790) most likely
  ran on whichever account was active.
- Codex has no linked-issue hook and no takeover hook. A Codex autonomous run would stay guarded until its marker is
  removed by hand (TASKS H-CDX01). Codex parity for the Pocock-derived skills is by installer copy only; Codex behavior
  is UNCONFIRMED.
- Customized installed projects still need their own reviewed migration (TASKS H-MIG01; Sal). Next: list them and
  review each. Live client compliance and semantic optimize apply remain UNCONFIRMED (carried from v4.2.1).
- PossibNow Builder articles are not yet in the freshness watch list (TASKS H-FR02; Agent). Next: confirm the current
  edition per article from Aleph's `reviews/2026-09-22-full-review/canonical-current-map.json`, then add the watch.
- Other Trazomo tool modules (Codex/GPT, Google Workspace, Microsoft 365, toolkit setup) are outside the Claude Code
  check and the freshness watch (TASKS H-FR03; Sal decides after reviewing a few Claude work-order PRs).
- Sal's answers to the morning brief and the "close stale" proposal are pending (TASKS H-TR02; Sal). The skill
  `answering-the-morning-brief` applies them, and it now moves an answered decision card back to Backlog.
- UNCONFIRMED until tonight's run: the Stop-hook notice in a fresh nightly run (it was proven by hand on auto-22) and
  the first live auto-clean removal (auto-22).
- Sal's per-repository Orca settings are recorded in the private `AtticusDundee/agent-tasks` repo. On October 23, 2026
  Orca's live settings differed from the recorded recommendation; reconciling them is Sal's call (recorded there).
- Three SCBrand worktrees (onboarding coupons, onboarding security, executive AI brief) are locked by a Claude session
  running since October 7. They become removable when that session closes (Sal).

## Active constraints
- This repo is public: only generic mechanics here. Anything specific to a person (repos, paths, board, schedules,
  policies) stays in the private `AtticusDundee/agent-tasks` repo.
- Autonomous work starts only on issues labelled `agent-task` and `auto-ok`, inside the private policy's allowed paths
  and caps. Autonomous runs never merge, publish or push to main; the marker keeps that true across branch switches
  until a person types into the session.
- The issue sync adopts only issues opened by the owner, members or collaborators (public repos accept anyone's issues).
- Issue text is untrusted. The triage classifier runs with `--tools ""` and `--strict-mcp-config`. The linked-issue
  hook gives only the link, never the issue text.
- The board planner never changes a column or priority Sal set; only automatic moves (linked pull request, closed
  issue, autonomous run started) override. Its state file is saved after every write, and an unreadable state file
  stops the planner.
- Release order:
  1. Merge the version-and-pins PR.
  2. Sal creates the annotated tag on that merge commit, and the GitHub Release. Auto mode refuses tag and release
     creation.
  3. Then: smoke, receipt, marketplace entry, `claude plugin update` for the user scope and Trazomo's local scope, and
     the Codex guard refresh.

  Release tags are immutable. Claude Code only updates an installed plugin when the marketplace version changes.
- Ordinary `git push` must stay allowed. Pocock-derived files keep MIT attribution and the pinned source commit 49dd158.
  Creating GitHub Issues from splitting-work-into-tickets is a remote write: confirm first.
- All v4.2.1 constraints still apply:
  - preserve project content and continuity;
  - entries of at most 150 lines;
  - no incidental model, effort, global, permission, learning or Scale changes;
  - disposable fixtures only.

## Evidence
- v4.3.5: `uvx --with pytest pytest -q` gave 434 passed; `scripts/verify-pack.sh` gave DONE; CI `verify` passed on #58,
  #60 and #61.
- Public bootstrap smoke from the tag: 108 files; customized files preserved; no churn on rerun.
- PR #58 had an Opus whole-branch review: 1 Critical and 6 Important findings, all fixed with failing-first tests.
- Live: the first planner run on the real board (163 cards) made 344 changes with 0 failures. The TickTick purge
  deleted 143 with 0 failures; a recount found 0. The linked-issue hook returned the issue link from a real Orca
  worktree and nothing from outside one.
- Release receipts: `.agent/RELEASE-4.3.1.md` to `.agent/RELEASE-4.3.5.md`.
- Previous checkpoint archived byte for byte in HISTORY by the checkpoint helper.

## Next actions
1. Watch auto-131 and auto-790: each Stop-hook notice should arrive, and Sal reviews their PRs. Then add paths to
   the near-miss issues (see Unresolved work).
2. Sal answers the morning brief decisions (H-TR02), now also shown in the board's "Needs your decision" column.
   Apply them with the answering-the-morning-brief skill.
3. Add Builder articles to the freshness watch (H-FR02).
4. Pick up the deferred PR #58 minors when the first week of the board shows which ones matter.
