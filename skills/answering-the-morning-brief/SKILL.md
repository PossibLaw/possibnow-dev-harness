---
name: answering-the-morning-brief
description: Apply Sal's answers to the nightly triage brief. Use when he replies with picks like "brief 1A 2B", "1A 3B" right after the brief, "opt in <names>", or "close stale", or asks to act on the morning brief.
metadata:
  version: 1.0.0
---

# Answering the morning brief

The nightly triage (`scripts/triage-issues.py`) writes a brief: Sal's top decisions as one numbered
list, what only he can do, what agents could take, and what looks stale. The short morning Slack message
(`scripts/morning-brief.py`) counts the decisions and stale issues; the decisions also sit in the board's
"Needs your decision" column. He answers in a Claude session. This skill turns those answers into changes on GitHub, and reports back by name, not
numbers.

## Read what was asked

1. Read `~/.agents/triage-state.json`. Its `decisions` list holds each numbered decision: `n`, `key`
   (`owner/repo#number`), `title`, `url`, `question`, `options`, `recommend`. Its `ran` field says when.
2. Read `~/.agents/triage-brief.md` for the other sections (agent-ready and stale lists, by title).
3. If the brief is more than a day older than Sal's message, say so and ask whether to use it.

## Apply each answer

- **A pick such as `2B`:** find decision 2, take option B's text, and post a comment on the issue:
  "Sal decided on <date>: <option text>." Then act on what the option says:
  - Drop, close or won't do: close the issue as not planned.
  - Hand the work to an agent: treat it like "opt in" below.
  - Every pick that leaves the issue open: move its card back to Backlog so the next nightly plan can
    pick it up: `python3 ~/possibnow-dev-harness/scripts/plan-board.py --config ~/agent-tasks/board.json --answered <key>`.
  - Anything else: leave it open. If the issue came from a register row (its body carries the hidden
    `agent-task:` marker), the decision also belongs in that repository's `.agent/TASKS.md` row. The
    sync overwrites GitHub-side edits, so update the row through a small pull request and say so.
- **`opt in <names>`:** match each name to an issue in the brief's agent section. Add `auto-ok` only
  when the nightly dispatcher would accept the issue. Check it with
  `python3 ~/possibnow-dev-harness/scripts/dispatch-auto-issues.py --config ~/agent-tasks/policy/dispatch.json --dry-run`.
  For any it would reject, report the reason (for example "no files named") and the edit that fixes it.
- **`close stale`:** close every issue in the brief's stale section with a comment quoting the triage's
  reason, as not planned. Close nothing else.

## Never

- Never change an `urgent` or `important` label Sal set. The triage treats his labels as an override and
  so does this skill. Change them only when he asks in words.
- Never act on an issue that is not in the brief, and never publish, merge or deploy anything here.

## Report

Answer by name, not numbers: "Newsletter architecture: decided A, comment posted; register row update
in PR <link>." List anything you could not apply and why.
