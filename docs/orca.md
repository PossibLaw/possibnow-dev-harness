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
| Custom GitHub Issue Command | the template in section 4 | First message an agent gets when work starts from an issue |
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

## 4. Custom GitHub issue command template

Plain text, not a slash command, so the same text works for Claude Code and Codex:

```text
Read .agent/HANDOFF.md and .agent/PLAN.md first. Then complete {{artifact_url}}. Never assume: ask if anything is unclear. Write a failing test before changing code, keep the change scoped to the issue, and open a draft PR when the checks pass.
```

`{{artifact_url}}` is replaced by Orca with the issue or PR link. The repository's own
`CLAUDE.md` / `AGENTS.md` defines what "the checks" are.

## 5. Creating a worktree

Only **Name** and **Agent** change from one task to the next; every other field keeps
its default:

| Field | Choose |
| --- | --- |
| Run on | the local machine |
| Create From | `origin/main` for new work; the **GitHub** tab for an issue or PR; the **Branch** tab to continue an existing branch |
| Name | the task, not the repository (it becomes the branch `orca/<name>`) |
| Agent | the agent to start, or a blank terminal |
| Sparse checkout | Full |

Do not open a branch that is already checked out elsewhere (git refuses the same
branch in two worktrees). From a terminal: `orca worktree create --help`.

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
