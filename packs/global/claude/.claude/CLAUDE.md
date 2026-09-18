# Global Instructions

Repo Root (absolute path, required): /path/to/your/repo

## Scope
These rules apply to every Claude Code session across all projects.

## Precedence
1. `~/.claude/CLAUDE.md` (global)
2. `<project>/CLAUDE.md` (project)
3. `<project>/<subdir>/CLAUDE.md` (subtree)
4. Skills (`SKILL.md`)
5. Agents (`.claude/agents/*.md`)
6. Commands (`.claude/commands/*.md`)
7. State artifacts (`.agent/*.md`)
If two rules conflict, follow the higher layer.

## Repo Root & State File Paths (Required)
1. Before writing any state file (`.agent/PLAN.md`, `.agent/HANDOFF.md`, `.claude/history.md`), resolve the repo root using `git rev-parse --show-toplevel` and confirm with `pwd`.
2. If the resolved root is under `/tmp`, `/var/folders`, or any OS temp directory, return `BLOCKED` and ask for the real repo root.
3. If multiple repo roots or worktrees are possible, ask the user which repo root to use.
4. If the repo root cannot be resolved, ask the user for the absolute repo root path and do not write any state files until confirmed.
5. Always write the plan to `${REPO_ROOT}/.agent/PLAN.md`.
6. Always write the handoff to `${REPO_ROOT}/.agent/HANDOFF.md`.
7. Always write history to `${REPO_ROOT}/.claude/history.md`.
8. If `.agent/` or `.claude/` is missing, return `BLOCKED` and ask for permission to create them under `${REPO_ROOT}`.
9. When saving, print the absolute path used; if it is not under `${REPO_ROOT}`, stop and ask for correction.

## Communication
- Be direct, concise, and outcome-first.
- State assumptions explicitly and label unknowns as `UNCONFIRMED`.
- Use exact file paths and concrete commands in recommendations.

## TDD and Evals
- For code changes, use TDD when feasible: begin with a failing test/eval, implement the minimum change to pass, then refactor with checks still passing.
- Never assume eval inputs, acceptance criteria, fixtures, or expected outputs; mark gaps as `UNCONFIRMED` and resolve with one targeted follow-up question when needed.
- For new or changed behavior, present an end-user eval walkthrough before implementation in plain language using Given/When/Then with at least: happy path, edge case, and failure/security case.
- Minimize user friction: infer likely test/eval commands and fixtures from repository signals first (e.g., manifest files, lockfiles, CI config).

## Safety Boundaries
Always do:
- Protect secrets and redact sensitive values.
- Keep edits minimal, reviewable, and scoped to the task.
- Prefer read-only API operations unless explicitly authorized.

Ask first:
- Destructive actions, schema changes, force pushes, or history rewrites.
- Remote writes to production systems.
- Any change outside requested scope or workspace boundaries.

Never do:
- Invent facts when evidence is missing.
- Claim completion without validation evidence.
- Expose credentials or private keys in output.

## Accuracy and Recency
- For requests using `latest`, `current`, `today`, or `as of now`, capture current time in ISO format first.
- Prefer official vendor documentation and release notes.
- Cite source location and source date when recency affects correctness.
- For vendor setup/API/security guidance, verify against official vendor docs and cite source date.

## Context Management
- Do not bulk-load large documents; process sequentially.
- Persist key state to disk (`.agent/PLAN.md`, `.agent/CONTEXT.md`, `.agent/TASKS.md`, `.agent/HANDOFF.md`).
- In a repo with roughly 40–50+ source files, offer Tier 2 Scale mode through the `scaling-up-with-graphify` skill (a local Graphify index queried instead of re-reading source). Never install upstream Graphify hooks, watch mode, git hooks, or the MCP server without explicit approval.
- Keep this file short; move detailed workflows to skills or docs.

## Change Tracking
- Log edits to instruction files in the relevant `CHANGELOG.md`.
- Record what changed, why, impact, and decision status.

## Completion Contract
- Return `DONE` only when acceptance checks pass.
- If blocked, return `BLOCKED: <reason>` plus attempted steps and next action.

## Shared Project Continuity
Commit sanitized current and historical handoffs, plans, context/tasks, test/review summaries, learnings, wiki, content continuity, archives, and existing project history with their work. Keep credentials, environment files, locks, and raw runtime caches private. Use HANDOFF for current state and HISTORY for exact archived checkpoints. Archive and verify before replacement; verify authorized delivery on remote main. Do not sweep other repositories or overwrite another tool's settings to enforce this policy.
