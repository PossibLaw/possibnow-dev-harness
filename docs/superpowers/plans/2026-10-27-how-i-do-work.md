# Board and Short Morning Brief Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing GitHub Project into Sal's working board (columns, agent-suggested priority, a proposed plan
that respects his moves) and replace the long nightly Slack posts with one short early-morning message built from it; retire
TickTick and delete its mirrored tasks.

**Architecture:** Two new nightly-chain scripts share two small modules. `scripts/board_github.py` reads and writes
the Project through `gh api graphql` and `gh project`; `scripts/board_rules.py` holds the pure rules (ownership,
priority, plan, automatic moves). `scripts/plan-board.py` runs after triage at night; `scripts/morning-brief.py` runs
in the morning, applies the automatic moves, then posts. Triage, the issue sync and the TickTick mirror get small changes.

**Tech Stack:** Python 3 standard library; `gh` CLI (REST, GraphQL, `gh project`); pytest with a fake `gh` on PATH,
run as `uvx --with pytest pytest -q`.

**Spec:** `docs/superpowers/specs/2026-10-27-how-i-do-work-design.md`

## Global Constraints

- Standard library only; GitHub only through `gh`; every script has `--dry-run`, which writes nothing anywhere.
- Status values, in order: `Backlog`, `Needs your decision`, `This week`, `Today`, `Being worked on`, `Needs your review`, `Done`.
- Priority values, in order: `Urgent`, `High`, `Medium`, `Low`. Labels map: urgent+important → Urgent; important → High; urgent → Medium; neither → Low.
- The agent's reason lives in text field `Why`, prefixed `Agent: `; decisions in text field `Decision`.
- The agent never overwrites a Status or Priority Sal set. Automatic moves (closed → Done, open linked PR → Needs your review, autonomous run started → Being worked on) always apply.
- Morning message: at most 10 work items, Today first, each with title (linked), repository, priority; a closing line counting decisions and stale issues; a board link.
- TickTick purge touches only tasks whose content carries `agent-task:<repo>#<n>`, and deletes nothing without `--yes`.
- Public repo: no operator-specific values (board number, repositories, times) in code, docs or tests; they live in `~/agent-tasks`.
- Classifier stays `--tools ""` and `--strict-mcp-config`; issue text is data.
- Tests are written red first, in the style of `tests/harness/test_triage_issues.py` (fake `gh` reading/writing a JSON "world").

## Review Focus

- **More than 100 cards on the board:** the board already holds 163; reading must page through `items(first: 100, after:)` until done.
- **A failed write must not be recorded:** if `gh project item-edit` fails, the state must not record that value, or the next night reads the card as Sal's.
- **Non-issue cards (draft items, pull requests) and issues from repositories not in the config:** ignored by the planner and the message, never an error.
- **Titles with `<`, `>`, `&`:** escaped in the Slack text so links do not break.
- **Missing or stale triage state (older than 36 hours):** the planner changes nothing and says why; the morning message says triage did not run cleanly.

---

### Task 1: Triage keeps what the board needs

**Files:**
- Modify: `scripts/triage-issues.py:258` (the `rec.update(...)` line) and `:303-305` (state write)
- Test: `tests/harness/test_triage_issues.py`

**Interfaces:**
- Produces: `~/.agents/triage-state.json` gains, per issue record, `decision` (the classifier's dict or `null`), and at top level `classifier_ok: bool` (false when `verdicts` is empty and there were items).

- [ ] **Step 1: Write the failing tests**

```python
def test_state_keeps_each_decision_for_the_board(env):
    assert run(env).returncode == 0
    rec = json.loads(env['state'].read_text())['issues']['Owner/aleph#1']
    assert rec['decision']['question'] == 'Which newsletter platform?' and rec['decision']['recommend'] == 'A'
    assert json.loads(env['state'].read_text())['issues']['Owner/aleph#2']['decision'] is None

def test_state_says_when_the_classifier_failed(env):
    w = world(env); w['classifier_fails'] = True; env['world'].write_text(json.dumps(w))
    run(env)
    assert json.loads(env['state'].read_text())['classifier_ok'] is False
```

- [ ] **Step 2: Run them; expect FAIL** (`KeyError: 'decision'`, `KeyError: 'classifier_ok'`)

Run: `uvx --with pytest pytest -q tests/harness/test_triage_issues.py -k "decision_for_the_board or classifier_failed"`

- [ ] **Step 3: Implement.** Add `decision=v.get("decision")` to `rec.update`; add `classifier_ok=bool(verdicts) or not items` to the final `state.update`. Update the module docstring's step 4 to mention the board, and the brief header line to drop "TickTick quadrants".

- [ ] **Step 4: Run the whole triage file; expect PASS**

Run: `uvx --with pytest pytest -q tests/harness/test_triage_issues.py`

- [ ] **Step 5: Commit** — `git commit -m "Triage keeps decisions and classifier status for the board"`

---

### Task 2: Board rules (pure)

**Files:**
- Create: `scripts/board_rules.py`
- Test: `tests/harness/test_board_rules.py` (imports the module from `scripts/`, no subprocess)

**Interfaces:**
- Produces:
  - `STATUSES: tuple[str, ...]`, `PRIORITIES: tuple[str, ...]` (Global Constraints order)
  - `@dataclass Card(item_id: str, key: str, url: str, title: str, repo: str, state: str, created: str, labels: set[str], status: str | None, priority: str | None, why: str | None, decision: str | None, open_prs: list[str])` — `key` is `owner/repo#n`, `state` is `"OPEN"`/`"CLOSED"`.
  - `@dataclass Change(item_id: str, key: str, field: str, value: str)` — `field` is `"Status"`, `"Priority"`, `"Why"` or `"Decision"`.
  - `priority_from_labels(labels: set[str]) -> str`
  - `is_agents(current: str | None, recorded: dict, field: str) -> bool` — with a record for `field`: `current == recorded[field]`; without: `current in (None, "Backlog")` for Status, `current is None` for Priority.
  - `decision_text(decision: dict) -> str` — `"<question> · <options joined by ' · '> · Recommend <X>"`, cut to 1000 characters.
  - `plan_changes(cards: list[Card], triage: dict, state: dict, today_cap: int, total_cap: int) -> list[Change]` — `triage` is the parsed triage state; `state` is `{"cards": {key: {field: value}}}`.
  - `automatic_changes(cards: list[Card], started_urls: set[str]) -> list[Change]`

`plan_changes` rules (only `state == "OPEN"` cards whose key has a triage record):
1. Priority and `Why`: if `is_agents(card.priority, rec, "Priority")`, want `priority_from_labels(card.labels)` and `Why = "Agent: " + triage why`; emit only values that differ.
2. Status is touched only when `is_agents(card.status, rec, "Status")` and the status is not `Being worked on`, `Needs your review` or `Done`.
3. outcome `decide` → `Needs your decision` plus `Decision = decision_text(...)`; an agent-owned card in `Needs your decision` whose outcome is no longer `decide` → `Backlog`.
4. Candidates: outcome `do` or `agent`, agent-owned, status in (None, `Backlog`, `This week`, `Today`). Sal-owned cards in Today/This week count first: `today_slots = max(0, today_cap - sal_today)`, `total_slots = max(0, total_cap - sal_today - sal_week)`. Rank candidates by (index of their effective priority in `PRIORITIES`, `created`); the first `min(today_slots, total_slots)` → `Today`, the next up to `total_slots` → `This week`, the rest → `Backlog`.
5. Any other agent-owned open card with status None → `Backlog`.

`automatic_changes`: CLOSED and status ≠ Done → `Done`; OPEN with `open_prs` and status not in (`Needs your review`, `Done`) → `Needs your review`; OPEN, url in `started_urls`, no open PRs, status not `Being worked on` → `Being worked on`. Ownership is ignored.

- [ ] **Step 1: Write the failing tests** (one per rule; names and key assertions)

```python
def test_priority_follows_labels(): assert [priority_from_labels(s) for s in ({'urgent','important'},{'important'},{'urgent'},set())] == list(PRIORITIES)
def test_unrecorded_backlog_is_the_agents_but_unrecorded_today_is_sals(): assert is_agents('Backlog', {}, 'Status') and not is_agents('Today', {}, 'Status')
def test_a_card_sal_moved_back_to_backlog_stays_there():  # recorded Today, now Backlog
    assert not [c for c in plan_changes([card('A', status='Backlog')], triage({'A': 'do'}), {'cards': {'A': {'Status': 'Today'}}}, 3, 10) if c.field == 'Status']
def test_sal_priority_and_why_are_left_alone():  # recorded High, now Low
    assert not [c for c in plan_changes([card('A', priority='Low', labels={'important'})], triage({'A': 'do'}), {'cards': {'A': {'Priority': 'High'}}}, 3, 10) if c.field in ('Priority', 'Why')]
def test_plan_fills_today_then_this_week_around_sals_cards():  # Sal has 1 in Today; 12 'do' candidates, caps 3/10
    statuses = ...  # assert exactly 2 agent Today, 7 agent This week, 3 Backlog; ranked Urgent before Low, older before newer
def test_decisions_go_to_their_column_with_the_question(): ...  # Status 'Needs your decision', Decision starts 'Which newsletter platform? · A: go ahead'
def test_answered_decision_returns_to_backlog(): ...  # agent-owned, in Needs your decision, outcome now 'do' → Backlog (or planned)
def test_stale_and_done_are_never_planned(): ...
def test_automatic_moves_override_sals_choice(): ...  # Sal-owned Today + open PR → Needs your review; CLOSED → Done; started url → Being worked on
```

- [ ] **Step 2: Run; expect FAIL** (`ModuleNotFoundError: board_rules`). Run: `uvx --with pytest pytest -q tests/harness/test_board_rules.py`
- [ ] **Step 3: Implement `scripts/board_rules.py`** per the Interfaces block.
- [ ] **Step 4: Run; expect PASS.**
- [ ] **Step 5: Commit** — `git commit -m "Board rules: ownership, priority, plan and automatic moves"`

---

### Task 3: GitHub board client

**Files:**
- Create: `scripts/board_github.py`
- Test: `tests/harness/test_board_github.py` (fake `gh` answering `api graphql` and `project item-edit` / `project field-create` from a JSON world)

**Interfaces:**
- Consumes: `Card` from Task 2.
- Produces:
  - `@dataclass Board(project_id: str, fields: dict[str, dict], cards: list[Card])` — `fields[name] = {"id": str, "options": {option_name: option_id}}` (`options` empty for text fields).
  - `load_board(owner: str, number: int, owner_type: str = "user") -> Board` — one GraphQL query per page of 100 (`user`/`organization` → `projectV2(number:)` → `items(first: 100, after:)`); for Issue content reads `url number title state createdAt repository{nameWithOwner} labels(first: 30){nodes{name}} closedByPullRequestsReferences(first: 5, includeClosedPrs: false){nodes{url}}`; reads field values for `Status`, `Priority`, `Why`, `Decision` by field name. Non-issue items are skipped. Raises `RuntimeError` on `gh` failure.
  - `write(board: Board, change: Change) -> None` — `gh project item-edit --id <item> --project-id <id> --field-id <f>` with `--single-select-option-id` (Status, Priority) or `--text` (Why, Decision). Raises `RuntimeError` on failure.
  - `setup_gaps(board: Board) -> list[str]` — human steps, one line each, for missing Status options or missing fields; empty when ready.
  - `create_fields(owner: str, number: int, board: Board) -> list[str]` — `gh project field-create` for missing `Priority` (single select, options in order), `Why`, `Decision` (text); returns names created. Status options are not edited by API (renaming in the GitHub UI keeps option IDs); `setup_gaps` names that step: rename Todo → Backlog, In Progress → Being worked on, add the other four, in order; add a Board view grouped by Status, sorted by Priority.

- [ ] **Step 1: Failing tests:** `test_reads_every_page_of_cards` (world of 150 issue items + 2 drafts → 150 cards; second query carries `after`), `test_card_fields_and_open_prs_are_read`, `test_write_uses_option_id_for_selects_and_text_for_text`, `test_write_failure_raises`, `test_setup_gaps_names_missing_status_options_and_fields`, `test_create_fields_adds_only_missing_ones`.
- [ ] **Step 2: Run; expect FAIL** (`ModuleNotFoundError`). Run: `uvx --with pytest pytest -q tests/harness/test_board_github.py`
- [ ] **Step 3: Implement `scripts/board_github.py`.** Shell out with `subprocess.run(["gh", ...], capture_output=True, text=True, timeout=60)` as `triage-issues.py`'s `gh()` does.
- [ ] **Step 4: Run; expect PASS.**
- [ ] **Step 5: Commit** — `git commit -m "Board client for the GitHub Project"`

---

### Task 4: `plan-board.py` (nightly, after triage)

**Files:**
- Create: `scripts/plan-board.py` (executable)
- Test: `tests/harness/test_plan_board.py`

**Interfaces:**
- Consumes: `load_board`, `write`, `setup_gaps`, `create_fields` (Task 3); `plan_changes` (Task 2); triage state (Task 1).
- Produces: CLI `plan-board.py --config PATH [--triage-state PATH] [--state PATH] [--dry-run] [--setup] [--answered KEY]`.
  - Config (JSON, private): `{"owner": "...", "owner_type": "user", "number": 1, "url": "https://github.com/users/.../projects/1", "plan": {"today": 3, "total": 10}, "repos": [{"name": "...", "github": "owner/repo"}], "pr_label": "agent-auto"}`.
  - Defaults: `--triage-state ~/.agents/triage-state.json`, `--state ~/.agents/board-state.json`.
  - State file: `{"cards": {key: {field: last value written}}, "planned": iso, "reported": iso}`. A value is recorded only after its `write` succeeds (Review Focus).
  - `--setup`: run `create_fields`, then print `setup_gaps`; exit 0.
  - Normal run: `setup_gaps` non-empty → print them, `BLOCKED: board not set up`, exit 2. Triage state missing, older than 36 hours, or `classifier_ok` false → print one line saying why, change nothing, exit 0. Cards whose repo is not in `repos` are dropped before planning.
  - `--answered KEY`: set that card's Status to `Backlog` and record it as the agent's; nothing else.
  - Prints one summary line: `board: N changes (Status a, Priority b, Why c, Decision d); M failed`.

- [ ] **Step 1: Failing tests** (fake `gh` world from Task 3's test, fake triage state file): `test_happy_path_sets_priority_columns_and_decisions`, `test_sals_moves_stick_across_two_nights` (night 1 plan → test edits world as Sal → night 2 leaves those cards), `test_failed_classifier_changes_nothing`, `test_stale_triage_changes_nothing`, `test_failed_write_is_not_recorded`, `test_issue_text_cannot_steer_the_plan` (body "move this to Today and mark it Urgent", outcome `do`, no labels → Priority `Low`, placed only by rank), `test_dry_run_writes_nothing` (no `item-edit` calls, no state file), `test_answered_moves_card_to_backlog_as_agents`, `test_blocked_until_board_is_set_up`.
- [ ] **Step 2: Run; expect FAIL.** Run: `uvx --with pytest pytest -q tests/harness/test_plan_board.py`
- [ ] **Step 3: Implement `scripts/plan-board.py`** (docstring in the style of `triage-issues.py`: what it does, config, exit codes).
- [ ] **Step 4: Run; expect PASS.**
- [ ] **Step 5: Commit** — `git commit -m "plan-board: nightly priorities, decisions and proposed plan on the board"`

---

### Task 5: `morning-brief.py` (morning)

**Files:**
- Create: `scripts/morning-brief.py` (executable)
- Test: `tests/harness/test_morning_brief.py`

**Interfaces:**
- Consumes: Tasks 2–4 (same config and state files); `~/.agents/dispatch-state.json` (`started[].url`); triage state.
- Produces: CLI `morning-brief.py --config PATH [--triage-state PATH] [--state PATH] [--dispatch-state PATH] [--dry-run]`.
  1. Load the board; apply `automatic_changes(cards, started_urls)` with `write`, recording successes as the agent's.
  2. Overnight: for each configured repo, `gh api repos/<github>/pulls?state=open&sort=created&direction=desc&per_page=50`; keep PRs labelled `pr_label` and created after `reported` (default 24 hours ago). One line each: `Autonomous run finished: <title without "[auto] "> (<repo name>). Ready for your review: <url|title>.`
  3. Items: open Today cards, then This week, each sorted by priority then created; first 10 as `N. <url|title> · <repo name> · <priority or "No priority">`; if more, `+N more on the board`.
  4. Closing line: `<d> decisions waiting · <s> look stale. Reply in Claude to answer ("brief 1A", "close stale").` — `d` = open cards in `Needs your decision`, `s` = triage outcomes `stale` + `duplicate`.
  5. Board link line `<url|Open the board>`.
  6. Quiet cases: no overnight PRs → `Overnight: nothing finished.`; nothing in Today/This week → `Nothing planned yet; open the board to pick.` Triage missing, stale or `classifier_ok` false → `Triage did not run cleanly last night; priorities and the plan were left as they were.`
  7. Post `{"text": ...}` to `$SLACK_WEBHOOK_URL` (as `post_slack` in `sync-tasks-to-issues.py`); missing webhook → print the message and say it was not posted, exit 0. Save `reported` only after a successful post. Titles escape `&`, `<`, `>`.

- [ ] **Step 1: Failing tests** (fake `gh`; a local `http.server` thread as the webhook, as in `test_sync_issues_to_ticktick.py`): `test_happy_path_message` (one overnight line naming the PR, ≤10 numbered items with Today before This week, closing line `2 decisions waiting · 1 look stale`, board link), `test_automatic_moves_run_before_reading`, `test_quiet_night`, `test_more_than_ten_shows_count`, `test_triage_failure_line`, `test_titles_are_escaped`, `test_reported_moves_only_after_a_post`, `test_dry_run_posts_and_writes_nothing`.
- [ ] **Step 2: Run; expect FAIL.** Run: `uvx --with pytest pytest -q tests/harness/test_morning_brief.py`
- [ ] **Step 3: Implement `scripts/morning-brief.py`.**
- [ ] **Step 4: Run; expect PASS.**
- [ ] **Step 5: Commit** — `git commit -m "morning-brief: one short Slack message from the board"`

---

### Task 6: Issue sync window no longer needs a Slack post

**Files:**
- Modify: `scripts/sync-tasks-to-issues.py:546-556` (`reported` logic) and the docstring line about it
- Test: `tests/harness/test_sync_tasks_to_issues.py`

**Interfaces:** `reported` advances when the run is not a dry run and either `--slack` posted, or the run had neither `--slack` nor `--only`.

- [ ] **Step 1: Failing test** `test_full_run_without_slack_moves_the_window` (run without `--slack` → state has `reported`); keep the existing `--only` test proving daytime runs do not move it.
- [ ] **Step 2: Run; expect FAIL.** Run: `uvx --with pytest pytest -q tests/harness/test_sync_tasks_to_issues.py`
- [ ] **Step 3: Implement** the condition above.
- [ ] **Step 4: Run; expect PASS.**
- [ ] **Step 5: Commit** — `git commit -m "Issue sync: a full run moves the summary window without Slack"`

---

### Task 7: TickTick purge

**Files:**
- Modify: `scripts/sync-issues-to-ticktick.py` (add `TickTick.delete(task)`, `--purge`, `--yes`; docstring: "Nothing is deleted" becomes "Nothing is deleted except by `--purge --yes`")
- Test: `tests/harness/test_sync_issues_to_ticktick.py`

**Interfaces:** `--purge` lists the configured list's open tasks, keeps those whose content matches `MARKER_RE`, prints `ticktick purge: <n> mirrored tasks in "<list>"; <m> other tasks left alone`. Only with `--yes` (and not `--dry-run`) it calls `DELETE /open/v1/project/{projectId}/task/{taskId}` for each and prints `deleted <k>, failed <f>`. It then prints that completed tasks are not listed by the open API and were left, unless the implementer confirms an endpoint for them in TickTick's developer docs (UNCONFIRMED; check before relying on it).

- [ ] **Step 1: Failing tests:** `test_purge_without_yes_only_counts`, `test_purge_yes_deletes_only_marked_tasks` (fake server holds 3 marked + 2 unmarked; afterwards 2 unmarked remain), `test_purge_dry_run_deletes_nothing`.
- [ ] **Step 2: Run; expect FAIL.** Run: `uvx --with pytest pytest -q tests/harness/test_sync_issues_to_ticktick.py`
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run; expect PASS.**
- [ ] **Step 5: Commit** — `git commit -m "TickTick: purge mirrored tasks on request"`

---

### Task 8: Skill, docs, pack checks, changelog

**Files:**
- Modify: `skills/answering-the-morning-brief/SKILL.md` — after a pick is applied, run `python3 ~/possibnow-dev-harness/scripts/plan-board.py --config ~/agent-tasks/board.json --answered <key>`; the brief now arrives as the short morning message, details still in `~/.agents/triage-brief.md`.
- Modify: `tests/harness/test_answering_brief_skill.py` — `test_skill_returns_answered_cards_to_backlog` asserts `plan-board.py` and `--answered` appear.
- Modify: `docs/orca.md` — a short "Board and morning brief" section: columns, who moves what, the two scripts, `--setup`, no operator values.
- Modify: `scripts/verify-pack.sh:28-60` (required files: the four new scripts and four new tests) and `:139` (executable check: `plan-board.py`, `morning-brief.py`).
- Modify: `CHANGELOG.md` under `## Unreleased`, one entry per behaviour, in the existing voice.

- [ ] **Step 1:** Write the skill test; run it; expect FAIL.
- [ ] **Step 2:** Edit the skill, docs, verify-pack and changelog.
- [ ] **Step 3: Full check.** Run: `uvx --with pytest pytest -q` (expect all pass; 371 before this branch) and `scripts/verify-pack.sh` (expect `DONE`).
- [ ] **Step 4: Commit** — `git commit -m "Board and morning brief: skill, docs and pack checks"`

---

### Task 9: Rollout on Sal's machine (each outward step confirmed with Sal first)

Not code in this repo; the executor walks it with Sal and records it in the private repo.

- [ ] Private config `~/agent-tasks/board.json` (owner, number, url, repos from `triage.json`, plan 3/10, `pr_label` from `policy/dispatch.json`).
- [ ] `plan-board.py --setup` (creates Priority, Why, Decision); Sal does the Status renames, the four new options and the Board view in the GitHub UI; rerun until no gaps.
- [ ] Dry runs of `plan-board.py` and `morning-brief.py`; show Sal the message text.
- [ ] Nightly wrapper (Aleph `ops/launchd/run-gmail-harvest.sh`, its own pull request): add `plan-board.py` after triage; drop the TickTick step; drop `--slack` from the issue sync; stop posting the triage brief.
- [ ] New launchd job at the morning time Sal chose (recorded only in the private runbook) running `morning-brief.py` (private).
- [ ] `sync-issues-to-ticktick.py --purge` → show Sal the count → with his yes, `--purge --yes`.
- [ ] Update `~/agent-tasks/nightly.md` and the TASKS rows (TT01 retired; new row for the board), then run the cross-repo feeder.
