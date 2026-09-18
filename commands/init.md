---
description: Initialize the current repo with PossibNow Dev Harness project files (.agent/ state templates, AGENTS.md, CLAUDE.md, docs/roles, docs/workflows, docs/glossary, .claude/skills). Auto-detects stack and pre-fills test/lint/typecheck/build commands.
argument-hint: [--preserve-progress] [--dry-run] [--name NAME] [--owner OWNER] [--primary CMD] [--test CMD] [--lint CMD] [--typecheck CMD] [--build CMD]
allowed-tools: Bash
---

# /possibnow-dev-harness:init

Bootstrap the **current working directory** with PossibNow Dev Harness project files. Run this once after installing the plugin so your repo has the state-artifact pipeline (PLAN/TEST/REVIEW/HANDOFF), the project-level governance files, and the host-agnostic role and workflow contracts.

## What it installs into the repo

- `AGENTS.md` and `CLAUDE.md` — project-level governance (Codex + Claude)
- `.agent/{PLAN,REVIEW,TEST,HANDOFF,HISTORY,WIKI,LEARNINGS}.md` — state-artifact templates (PLAN now also holds the former CONTEXT assumptions and TASKS checklist; HANDOFF is current; HISTORY preserves previous checkpoints)
- `.agent/integrations/` — advisory continuity-checkpoint helper (`run-checkpoint.sh`) that prints the PLAN/HANDOFF updates to make
- `docs/roles/*.md` — six canonical role contracts (product-strategist, engineering-planner, reviewer, security-reviewer, qa-validator, docs-releaser)
- `docs/workflows/{evals,contracts,wiki,graphify,token-management,optimization}.md`
- `docs/glossary.md` and `docs/vendor/*.md`
- `.claude/skills/{closing-sprint-and-syncing-state,running-novice-safe-git-cycle,applying-simplicity-ladder,scaling-up-with-graphify}/SKILL.md` — project-local Claude workflow skills
- `.agents/skills/` — Codex-discoverable copies of those four workflows plus Scale, Guardrails, and Optimize equivalents
- `.agent/HANDOFF.md` remains trackable for team continuity and must ship with every commit (the Claude Code guardrail blocks `git commit` while it is untracked or unstaged); all related sanitized continuity ships with the work

## What it does NOT touch

The plugin's runtime guardrails (`hooks/`, `scripts/guardrails/`, top-level `agents/` and `skills/`) live inside the plugin install and apply automatically when Claude Code starts. This command only adds files that need to live in your project repo. Existing state files are always preserved, even without `--preserve-progress`. It does not migrate an old combined handoff; use `/possibnow-dev-harness:optimize` to review that change.

## Steps to run

Run the existing installer with the current working directory as target. Pass through whatever arguments the user provided.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/install-project.sh" "$PWD" $ARGUMENTS
```

If $ARGUMENTS is empty, this still works — the script defaults to fresh install. Common flags:

- `--preserve-progress` — skip overwriting any existing `.agent/*.md` continuity files (use this when re-running on a repo that already has work in progress)
- `--dry-run` — show what would be copied without writing anything
- `--name <project_name>` — project name placeholder substitution (defaults to repo dir name)
- `--owner <team_or_owner>` — owner placeholder substitution
- `--primary "<cmd>"`, `--test "<cmd>"`, `--lint "<cmd>"`, `--typecheck "<cmd>"`, `--build "<cmd>"` — explicit overrides for stack commands (otherwise auto-detected from `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`)

## After it runs

If the script reports `DONE: project files installed into <path>`, remind the user with this exact text:

> PossibNow Dev Harness files installed. Next steps:
>
> 1. Review the diff: `git status && git diff`
> 2. Commit the shared governance, templates, and all related sanitized continuity so other contributors receive the current checkpoint and historical context. Review the handoff first and remove credentials, secrets, raw private client data, and machine-specific paths:
>    ```
>    git add AGENTS.md CLAUDE.md docs/ .agent/PLAN.md .agent/TEST.md .agent/REVIEW.md .agent/HANDOFF.md .agent/HISTORY.md .agent/WIKI.md .agent/LEARNINGS.md .agent/integrations/ .claude/skills/ .agents/skills/ .gitignore
>    ```
>    ```
>    git commit -m "Add PossibNow Dev Harness governance + workflow templates"
>    ```
> 3. If any commands show as `UNCONFIRMED` in `.agent/TEST.md` or `CLAUDE.md`, fill them in (or re-run init with `--test "..."` etc.)
> 4. The `closing-sprint-and-syncing-state` skill will keep `PLAN.md` and current HANDOFF and historical HISTORY current as you work.
> 5. From now on, every commit must include its changed continuity: refresh the current checkpoint, archive its predecessor, review and stage all related records, then commit. In Claude Code the guardrail refuses a commit that would leave the handoff untracked or unstaged.

If the script blocks (e.g., target placeholder error, missing pack), surface the error and the suggested fix verbatim — do not paper over it.

## When NOT to use this command

If the user is opening a repo that already has the harness installed (presence of `AGENTS.md` + `.agent/PLAN.md`), do not re-run init blindly. Either run with `--preserve-progress` or skip — re-running without that flag will back up existing files (`.bak.<timestamp>`) but still overwrite, which is rarely what the user wants mid-project.
