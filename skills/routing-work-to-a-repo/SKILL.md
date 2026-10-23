---
name: routing-work-to-a-repo
description: Turn one sentence of work ("I'm working on the ESRB session design") into a GitHub issue in the right repository, with the flywheel line, and offer an Orca worktree on it. Use when the user names work without naming a repo, says "file this", "route this", "add a task for", or "where does this go".
metadata:
  version: 1.0.0
---

# Routing work to a repository

One sentence in, one issue out, in the repository that owns the topic. The table that
maps topics to repositories is personal and lives outside this harness; this skill only
reads it.

## 1. Find the routing table

Read `~/agent-tasks/routing.md` (or the path in `$AGENT_TASKS_ROUTING`). If the file is
missing, stop and say so; do not route from memory. The table has: topic, match words,
repository (`owner/repo`), register path, owner, issue labels. First matching row wins,
top to bottom.

## 2. Match the sentence

Compare the sentence against each row's match words (case-insensitive, whole words,
plural forms allowed). Exactly one row: continue. No match, or two rows that match equally
well: ask the user which repository, showing the candidates; never guess. Nothing matches
and the user says it is machine-level work (no repo): tell them it belongs in the
`## Global` section of `~/.agents/TASKS.md` and offer to add it there instead.

Refuse, and say why, when the sentence carries bank or card details, credentials or
personal admin. File names are fine; numbers are not.

## 3. Get the flywheel line

Every issue carries one sentence of this shape:

> This leads to **X**, which leads to **Y**, which gets me **Z**.

If the user's sentence does not say what the work leads to, ask once, in one line. If they
decline, file with `Flywheel: UNCONFIRMED` so the morning summary shows the gap.

## 4. Create the issue

Title: the user's sentence, trimmed to 80 characters. Body:

```
**Source:** routed from a sentence on <date>
**Work:** <the sentence>
**Owner:** <owner from the table>
**Flywheel:** This leads to X, which leads to Y, which gets me Z.
```

Labels: the row's labels, which include `agent-task` and `routed`. Create with
`gh issue create -R <owner/repo> --title ... --body-file - --label agent-task --label routed`
locally; from a Claude Code cloud session use `gh api repos/<owner>/<repo>/issues -X POST`
instead (the proxy blocks `gh issue`). Creating an issue is a remote write: say what will
be filed and where, then do it.

Then append a row to the repository's register (`.agent/TASKS.md`, first section) with a
new ID (prefix `R` plus a number not yet used, for example `R1`) and the same text, so the
nightly sync owns the issue from its next run. Do this in a branch and commit it with the
work, or tell the user the row is still to be added.

## 5. Offer the worktree

Ask: "Open an Orca worktree on it now?" On yes:

```
orca worktree create --repo path:<register path minus .agent/TASKS.md> --issue <number> --agent claude
```

(or `--agent codex`). On no, stop; the issue is the record and the board shows it.

## 6. Report

One line: the issue link, the repository, the owner, whether a worktree was opened.
