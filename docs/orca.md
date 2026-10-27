# Orca runbook (generic)

How to set a repository up in [Orca](https://www.onorca.dev) so that an agent started
in a fresh worktree behaves like one started in the main checkout. This file holds
only the mechanics that are the same for every repository. Per-person settings
(which repositories, their exact setup lines, board and sync configuration) belong in
a private repository, never here.

Verified against Orca CLI 1.4.232 on macOS (October 2026). Field names come from the
Project Settings dialog of that version; later versions may rename them.

## 1. Add the repository

In Orca: **Add project → existing folder**, pointing at the main checkout. Or from a
terminal:

```sh
orca repo add /path/to/repo
orca repo list --json      # confirm it is registered
```

Orca reads the GitHub owner and repository from the `origin` remote. The GitHub
account it uses is the local `gh` login (`gh auth status`).

## 2. Project settings (open Project Settings for the repository)

| Setting | Value | Why |
| --- | --- | --- |
| Default Worktree Base | `origin/main` (or the repository's default branch) | New work starts from the latest main |
| Worktree Location | leave the global default (`~/orca/workspaces`) | One place for every worktree |
| Setup Script | one line, see section 3 | Copies local files and installs packages before the agent starts |
| When to run | Run by default | Every new worktree gets the same treatment |
| Wait for setup to complete before starting agent | **On** | Otherwise the agent starts before packages are installed |
| Archive Script | empty | Nothing to clean up unless the repository needs it |
| Custom GitHub Issue Command | leave empty | In Orca 1.4.x this field runs as a shell command in a split pane, not as the agent's first prompt (stablyai/orca#9066). Text pasted here produces a shell error. See section 4. |
| External worktrees | Hide (global default) | Show it per repository only when worktrees made outside Orca must appear |
| Advanced → Command Source | leave | Matters only for a repository that ships a shared `orca.yaml` |

Setting the issue command makes Orca write a `.orca` entry to the repository's
`.gitignore`. Commit that line; it keeps Orca's local files out of `git status`.

## 3. Setup script

`scripts/orca-worktree-setup` in this harness is a shared helper. Install it once
per machine and point every project's Setup Script at it:

```sh
install -m 755 scripts/orca-worktree-setup ~/.local/bin/orca-worktree-setup
```

Orca runs the Setup Script with `ORCA_ROOT_PATH` (main checkout) and
`ORCA_WORKTREE_PATH` (the new worktree) set. The helper:

1. Copies `.claude/settings.local.json`, `.env`, `.env.local` and `.dev.vars` from the
   main checkout when they exist, never overwriting a file already in the worktree.
2. Copies each extra gitignored path given with `--clone <path>` (indexes, data
   snapshots). On APFS the copy is a clone: instant, no extra disk, and changes in the
   worktree never reach the main checkout.
3. Links Claude Code's project memory for the worktree to the main checkout's memory
   (memory is keyed by folder path, so a worktree would otherwise start with none).
4. Runs `npm ci` when the worktree has a `package-lock.json`, using the pinned Node
   version from `.nvmrc` when `fnm` is installed.

Running it twice is safe. The setup line pattern is:

```text
~/.local/bin/orca-worktree-setup [--clone <gitignored path>]...
```

Examples: a plain Python repository uses the bare command; a Node app with a local
index uses `~/.local/bin/orca-worktree-setup --clone graphify-out`.

Tests: `tests/harness/test_orca_worktree_setup.py` (disposable fixtures, fake HOME).

## 4. What the agent gets when work starts from an issue

Orca 1.4.x puts only the bare issue URL in the agent's input as an unsent draft. The
Project Settings field "Custom GitHub Issue Command" does not change that: it is executed
as a shell command in a split pane (open request stablyai/orca#9066, "upcoming"). Leave it
empty.

To give every agent the same starting instructions, put a rule in the instruction file the
agent reads anyway: the repository's `CLAUDE.md` / `AGENTS.md`, or the person's global
`~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`. Example rule:

```text
When a session opens with only a GitHub issue link (Orca worktrees start this way), read
.agent/HANDOFF.md first, then treat the link as the work to start. Ask before assuming.
```

The Orca mobile app starts the agent without the issue link. The harness's SessionStart hook
(`scripts/guardrails/session-issue-link.py`) closes that gap for Claude Code. When a session starts in a worktree linked to an
issue, it asks `orca worktree current --json` for the link and adds it to the session's context. A one-word first message
such as "go" then starts the same work. Only the link is given; outside a linked worktree the hook adds nothing.

Worktrees created from the CLI are different: `orca worktree create --prompt "<text>"`
does deliver the text as the agent's first prompt. The nightly dispatcher uses that path.

Check which Orca version you run (`orca --version`) and re-test when #9066 lands.

## 5. Creating a worktree

Only **Name** and **Agent** change from one task to the next; every other field keeps
its default:

| Field | Choose |
| --- | --- |
| Run on | the local machine |
| Create From | `origin/main` for new work; the **GitHub** tab for an issue or PR; the **Branch** tab to continue an existing branch |
| Name | the task, not the repository (`orca worktree create` in Orca 1.4.240 uses it as the branch name unchanged; whether the app adds a prefix is UNCONFIRMED) |
| Agent | the agent to start, or a blank terminal |
| Sparse checkout | Full |

Do not open a branch that is already checked out elsewhere (git refuses the same
branch in two worktrees). From a terminal: `orca worktree create --help`.

### Autonomous worktrees (started by the dispatcher)

`scripts/dispatch-auto-issues.py` creates `auto-<n>` worktrees and writes `agent-auto.json`
into each one's git directory. While that marker is present the guardrails treat the
session as autonomous: no merging, no publishing, no pushing to main, even after the
session switches branch. The first prompt is the dispatcher's. Type anything into the
pane and the guard is released for that worktree; the session then follows the normal
ask-first rules, and a notice says so.

Each run appears under its own repository in the sidebar (the dispatcher creates it with no parent). When the agent
finishes its turn, a Stop hook posts to Slack at once: the issue and its pull request when one exists, or a note that the
run stopped without a pull request, quoting the agent's last message.

A worktree stops counting against the dispatcher's caps once its linked issue is closed. The nightly run then removes it
when nothing would be lost: idle for six hours, nothing uncommitted, and its work on the default branch (or its pull request
merged). The branch is kept and the report names each removal; anything else is listed as kept, with the reason.
When you are done with it, archive it from the Orca sidebar, or remove it from a terminal
with `orca worktree rm --worktree path:<worktree path>`. Removing deletes the checkout
folder but keeps the branch, so push or merge first. Closing the terminal tab does neither.

### The board and the morning brief

Open issues sit on a GitHub Project board you can keep open beside Orca, on a laptop or a phone. Columns, left to
right: Backlog, Needs your decision, This week, Today, Being worked on, Needs your review, Done.

- Each night, after triage, `scripts/plan-board.py` gives every card a Priority (Urgent, High, Medium, Low, from the
  `urgent` and `important` labels) with the agent's reason in `Why`, puts decisions in Needs your decision with the
  question in `Decision`, and proposes Today and This week (at most `plan.total` cards, `plan.today` of them today).
- Drag cards or change a priority whenever you like: anything you set is yours, and the agent never changes it back.
  To give a card back to the agent, drag it to "No Status" (or clear its Priority); the next night plans it again.
- In the morning, `scripts/morning-brief.py` moves cards that changed by themselves (an open linked pull request goes
  to Needs your review, a closed issue to Done, an autonomous run the dispatcher started to Being worked on), then
  posts one short Slack message: what finished overnight, at most ten cards (Today first), a count of decisions and
  stale issues, and the board link.
- First time: `scripts/plan-board.py --config <private config> --setup` creates the fields and prints the steps only
  you can do in GitHub (the Status options, and a Board view sorted by Priority).

## 6. What not to run in a worktree

A worktree holds a snapshot of any `--clone`d data directory. Jobs that write to that
data (scheduled pipelines, harvesters, ledgers) must run from the main checkout, or
their output never reaches the real data. Drafting, code changes and tests are fine in
worktrees.

## 7. Checks

```sh
orca repo list --json | python3 -c "import json,sys; [print(r['path'], r['hookSettings']['scripts']['setup'] or '(none)', r['hookSettings']['setupAgentStartupPolicy']) for r in json.load(sys.stdin)['result']['repos']]"
```

Expect each repository's setup line and `wait-for-setup` rather than
`start-immediately`. The custom issue command is not exposed by the CLI in 1.4.232;
check it in the dialog.
