# Codex Global Instructions

Repo Root (absolute path, required): /path/to/your/repo

Global defaults for Codex sessions.

## Scope
- Applies to all Codex sessions unless overridden by project `AGENTS.md`.
- Project-level `AGENTS.md` has higher priority for project-specific behavior.

## Tool Ownership
Codex should treat these as instruction sources by default:
- `~/.codex/AGENTS.md`
- `<project>/AGENTS.md`
- `<project>/.agent/*.md` only when explicitly triggered by task type (planning, review, test, handoff, governance change).

Codex should ignore non-Codex instruction files unless explicitly asked:
- `CLAUDE.md`
- `.claude/*`

## Startup Checklist
1. Resolve working directory.
2. Read `~/.codex/AGENTS.md`.
3. Read `<project>/AGENTS.md` if present.
4. Start requested work immediately. Do not preload `.agent/*.md` files.

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

## On-Demand State Files
Load only when needed:
- `PLAN.md` for planning requests.
- `REVIEW.md` for review requests.
- `TEST.md` for test/validation requests.
- `HANDOFF.md` for resume or cross-agent baton passing.
- `CONTINUITY.md` only for global workflow/governance changes.

## Standards
- Keep edits minimal and reviewable.
- Use exact file paths and actionable commands.
- Mark unknown facts as `UNCONFIRMED`.
- Return `BLOCKED` with reason and next step when stuck.
- During review tasks, enforce `.agent/REVIEW.md` Security Review Mode and checklist.
- During test/validation tasks, enforce `.agent/TEST.md` security checks for auth, data access, input handling, API, and deployment/runtime changes.
- For code changes, use TDD when feasible: start with a failing test/eval, implement the minimal change, then refactor with tests still passing.
- Never assume eval inputs, acceptance criteria, or expected outputs. Mark gaps as `UNCONFIRMED` and resolve with a targeted user question before execution.
- For new or changed behavior, walk the user through an eval plan in plain language before implementation (at minimum: happy path, edge case, and failure/security case with observable expected results).
- Minimize user friction: infer likely test/eval commands and fixtures from repository signals first; ask the user only targeted follow-ups for unresolved unknowns.

## Accuracy and Recency
- For requests using `latest`, `current`, `today`, or `as of now`, capture current time in ISO format first.
- Prefer official vendor documentation and release notes.
- Cite source location and source date when recency affects correctness.
- For vendor setup/API/security guidance, verify against official vendor docs and cite source date.

## Safety
- Never expose secrets in output.
- Ask before destructive or irreversible actions.
- Never invent evidence or test results.

## Shared Project Continuity
Commit sanitized current and historical handoffs, plans, context/tasks, test/review summaries, learnings, wiki, content continuity, archives, and existing project history with their work. Keep credentials, environment files, locks, and raw runtime caches private. Use HANDOFF for current state and HISTORY for exact archived checkpoints. Archive and verify before replacement; verify authorized delivery on remote main. Do not sweep other repositories or overwrite another tool's settings to enforce this policy.
