# CLAUDE.md

Repo Root (absolute path, required): /path/to/your/repo

<PROJECT_NAME> — replace this line with a 2-line project description.

## Two Tiers (How This Pack Grows With You)
- **Tier 1 — Starter (default):** small-app workflow — `PLAN → TEST → REVIEW → HANDOFF`, current/historical continuity, guardrails, and the simplicity ladder. This is everything most projects need.
- **Tier 2 — Scale (gated as the codebase grows):** indexed retrieval (Graphify), wiki orientation, deeper review. When a repo gets large the harness will suggest `/possibnow-dev-harness:scale`; you opt in. Tier 2 never removes Tier 1 rules — it adds to them.

## Startup Contract
1. This file is the only startup instruction. Do not read other files unless triggered.
2. Do the requested task immediately.
3. Load extra files only on trigger:
   - Planning request → `.agent/PLAN.md`
   - Test request → `.agent/TEST.md`
   - Review request → `.agent/REVIEW.md`
   - Handoff, resume, or parallel worktree → `.agent/HANDOFF.md` (current checkpoint only; historical questions load a specific HISTORY entry)
   - Contract workflow, artifact schema, or stage handoff questions → `docs/workflows/contracts.md`
   - Token/context budget questions → `docs/workflows/token-management.md`
   - Optimize configuration or `/possibnow-dev-harness:optimize` → `docs/workflows/optimization.md`
   - Role workflow, routing, or specialization questions → `docs/roles/README.md` plus the relevant role file in `docs/roles/`
   - Codebase has grown / "index this code" / large existing repo → `docs/workflows/graphify.md` (Scale mode, Tier 2)
   - Wiki mode, Obsidian vault path, or persistent knowledge questions → `.agent/WIKI.md` and `docs/workflows/wiki.md` (Tier 2)
   - Learning request, or `Learning Mode` = `CAPTURE`/`APPLY` → `.agent/LEARNINGS.md`
   - Vendor/integration setup or API config → `docs/vendor/`
   - Evals/help defining “done” → `docs/workflows/evals.md`
   - Unfamiliar term (e.g. "eval", "handoff", "trust boundary") → `docs/glossary.md`
4. If more repo context is needed, read the newest section of `.agent/HANDOFF.md` next — not the whole repo.
5. Global continuity stays in `~/.claude/CLAUDE.md`. Repo continuity is optional and on-demand.
6. When a sprint is wrapping, work is about to pause or ship, or context feels roughly half full, run a continuity checkpoint before losing state.

## Token Discipline (Always On)
Keep context small so the harness stays fast and cheap (full guide: `docs/workflows/token-management.md`):
- On resume, read the current `.agent/HANDOFF.md`; historical checkpoints stay in `.agent/HISTORY.md`.
- Load the trigger files in the Startup Contract on demand — never read the whole repo or all docs at startup.
- Keep stable blocks (this file, `.agent/PLAN.md`) stable within a session so the prompt cache keeps paying off; avoid churning them mid-task.
- Apply the simplicity ladder (below) — less generated code is less to read, review, and maintain.
- At Tier 2, query the Graphify index instead of re-reading source files.

## Simplicity Ladder (Always On)
After you understand the problem, prefer the simplest option that works, in this order:
1. Does this even need to exist? (skip unneeded work)
2. Reuse something already in the codebase.
3. Use the language standard library.
4. Use a native platform feature.
5. Use an existing dependency already in the project.
6. A small, well-understood one-liner.
7. Only then write a minimal new solution.
Analyze thoroughly; build minimally. The full procedure is the `applying-simplicity-ladder` skill.

## Repo Root & State File Paths (Required)
1. Before writing any state file (`.agent/PLAN.md`, `.agent/HANDOFF.md`, `.agent/WIKI.md`), resolve the repo root using `git rev-parse --show-toplevel` and confirm with `pwd`.
2. If the resolved root is under `/tmp`, `/var/folders`, or any OS temp directory, return `BLOCKED` and ask for the real repo root.
3. If multiple repo roots or worktrees are possible, ask the user which repo root to use.
4. If the repo root cannot be resolved, ask the user for the absolute repo root path and do not write any state files until confirmed.
5. Use the canonical continuity files under `${REPO_ROOT}/.agent/`, including current HANDOFF and historical HISTORY.
6. Do not create competing current handoffs; HISTORY is the canonical archive of previous handoffs.
7. Keep newest-first continuity and stop-boundary rules from `docs/workflows/contracts.md`.
8. If `.agent/` is missing, return `BLOCKED` and ask for permission to create it under `${REPO_ROOT}`.
9. When saving, print the absolute path used; if it is not under `${REPO_ROOT}`, stop and ask for correction.

## Tool Ownership
- Claude reads: `CLAUDE.md` (this file), `~/.claude/CLAUDE.md` (global), `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`.
- `AGENTS.md` is the cross-tool mirror of this contract (read by Codex and other AGENTS.md-aware tools). Keep the two in sync, with one deliberate difference: `AGENTS.md` carries the full TDD and boundary text because those tools may have no global layer; this file points to `~/.claude/CLAUDE.md` for it instead.
- Shared contracts in `docs/roles/`, `docs/workflows/`, and `docs/vendor/` apply to every tool.

## Session Memory
Current continuity lives in `${REPO_ROOT}/.agent/HANDOFF.md`; previous checkpoints are preserved in `${REPO_ROOT}/.agent/HISTORY.md`. Both are version-controlled.

Before pausing, handing off, or moving into a git cycle, refresh:
- `${REPO_ROOT}/.agent/PLAN.md` milestone status and sprint status.
- `${REPO_ROOT}/.agent/HANDOFF.md`: archive and verify the previous checkpoint in HISTORY, then update the current decisions, open questions, and next actions.
- `${REPO_ROOT}/.agent/LEARNINGS.md` only when `Learning Mode` is `CAPTURE` or `APPLY`, and only for gated lessons.

When resuming prior work, read the current `${REPO_ROOT}/.agent/HANDOFF.md`; load history only when specifically needed.

## Shared Continuity (Committed with Work)
- Keep one current `.agent/HANDOFF.md` and preserve previous checkpoints in `.agent/HISTORY.md`.
- Archive the exact prior handoff with an ID and SHA-256 hash; verify preservation before replacement. Preserve legacy history and active constraints.
- Commit all relevant continuity with the work: handoff/history, plan/context/tasks, test/review summaries, learnings, wiki, content continuity, archives, and an existing project history.
- Review and sanitize before staging explicit files. Secrets, environment files, transient locks, and raw runtime caches stay private.
- Push and merge continuity with its work, then verify remote main before claiming a shared handoff is complete.
- The Claude Bash guard checks common direct commits for omitted named continuity; other hosts follow this contract. It is not a shell security sandbox.

## Optional Learning Loop (Default OFF, Validation-Gated)
- Default: `Learning Mode` is `OFF`.
- Turn on for a task by either:
  - setting `Learning Mode` in `.agent/PLAN.md`, or
  - explicit user instruction (`Learning Mode: CAPTURE` or `Learning Mode: APPLY`).
- Mode behavior:
  - `OFF`: no learning entries and no skill/plugin updates.
  - `CAPTURE`: add lessons to `.agent/LEARNINGS.md` only.
  - `APPLY`: capture lessons and propose specific skill/plugin/instruction updates.
- **Promotion gate:** only add a lesson that has earned its place — it recurred at least twice, or the user explicitly confirmed it. One-off observations stay out. This keeps the learnings file small and trustworthy (it does not rot).
- This is additive. Do not replace `.agent/HANDOFF.md`.

## Commands
`<PRIMARY_COMMAND>` - Primary local workflow command.
`<TEST_COMMAND>` - Run tests.
`<LINT_COMMAND>` - Run linting.
`<TYPECHECK_COMMAND>` - Run type checks.
`<BUILD_COMMAND>` - Build or package the project.

Run `<LINT_COMMAND> && <TYPECHECK_COMMAND> && <TEST_COMMAND>` before handoff.

## Stack
- Runtime:
- Framework:
- Data layer:
- Testing:
- Tooling:

## Code Map
- Entry point:
- Config files:
- API layer:
- Domain logic:
- Data/storage:
- Tests:

## Canonical Roles
- `product-strategist` — Clarifies user value, scope, and success criteria. Source of truth: `docs/roles/product-strategist.md`.
- `engineering-planner` — Produces an executable implementation plan with risks and eval IDs. Source of truth: `docs/roles/engineering-planner.md`.
- `reviewer` — Performs correctness and regression review. Source of truth: `docs/roles/reviewer.md`.
- `security-reviewer` — Performs attacker-minded review and security-check pressure testing. Source of truth: `docs/roles/security-reviewer.md`.
- `qa-validator` — Executes evals and records receipts. Source of truth: `docs/roles/qa-validator.md`.
- `docs-releaser` — Syncs handoff and user-facing docs after validation. Source of truth: `docs/roles/docs-releaser.md`.

In Claude Code, invoke each role via its `@name` handle (for example `@reviewer`, `@qa-validator`). Name = canonical role.

## Routing Rules
- Product framing, scope, or success-definition work → `@product-strategist`.
- Implementation planning and architecture tradeoffs → `@engineering-planner`.
- Test execution, eval receipts, and validation evidence → `@qa-validator`.
- Correctness, regressions, and maintainability review → `@reviewer`.
- Security-sensitive review or trust-boundary changes → `@security-reviewer`.
- Release notes, handoff, and docs sync after validated changes → `@docs-releaser`.
- If required facts are missing, escalate once with a targeted question.

Supporting specialists (not canonical roles — use when a canonical role is not a fit):
- Source extraction or fact gathering → `@research-agent`.
- Markdown-heavy doc drafting without release ownership → `@docs-agent`.

## Contract Pipeline (Required)
- Canonical source: `docs/workflows/contracts.md`. Read it for full rules, artifact schema, cross-artifact linkage, and validation commands.
- Quick summary: stage order is `PLAN.md` → `TEST.md` → `REVIEW.md` → `HANDOFF.md`; each stage must cite evidence from the prior stage; never return `DONE` with an unresolved upstream artifact.

## Continuity Checkpoint Contract
- Canonical source: `docs/workflows/contracts.md` (Continuity Checkpoints section).
- Quick summary: run a checkpoint at sprint close, before a git cycle, before ending the session, and when context pressure risks losing current state. Each checkpoint updates `.agent/PLAN.md` and current `.agent/HANDOFF.md` and historical `.agent/HISTORY.md`, and `.agent/LEARNINGS.md` when learning mode is enabled.
- If present, the optional helper `.agent/integrations/run-checkpoint.sh` prints the required updates as a checklist; it does not write state for you.

## Scale Mode (Tier 2, Default OFF)
- For small projects, stay in Tier 1. When the codebase grows large (roughly 40–50+ source files) or you start working inside an existing large codebase, switch on Scale mode with `/possibnow-dev-harness:scale`.
- Scale mode builds a queryable index of the code (Graphify) so you query the index instead of re-reading files, and configures `.agent/WIKI.md`. See `docs/workflows/graphify.md`.
- Record `Tier: 2 (Scale)` and `Scale mode: ON` in `.agent/HANDOFF.md` when enabled.
- When Scale mode is ON: after every merge to `main`, run `graphify update .` then `graphify export wiki`; query with `graphify affected`, `graphify explain`, `graphify query ... --context call`, and `graphify path ... --undirected` (table and rules in `docs/workflows/graphify.md`). Graph output is advisory; source wins. The upstream slash skill, its hooks, watch mode, and the MCP server stay off unless the user approves.

## Optional Wiki Mode (Tier 2, Default OFF)
- Configure vault and wiki paths in `.agent/WIKI.md` before first use.
- Use `docs/workflows/wiki.md` for startup flow, metadata, and lint rules.
- Wiki pages accelerate orientation; source code and tests remain authoritative.
- For full repository review requests, start with `.agent/WIKI.md` and wiki index, then verify in code.

## Vendor References
- For vendor/integration setup, API config, or security guidance, read `docs/vendor/<vendor>.md` first.
- Treat `docs/vendor/*.md` guidance as authoritative over model-memory defaults.
- If the vendor file is missing or stale, consult official vendor docs/release notes before answering.
- Cite the official source URL and source date for recency-sensitive vendor guidance.

## Git Workflow Contract
- Use focused branches and atomic commits.
- Attach validation evidence to PRs and handoffs.
- Never commit credentials.
- Stage all reviewed changed continuity with the work, including HANDOFF and HISTORY. Keep only secrets and raw runtime state private.
- For novice-safe shipping, run this order:
  1. `git status --short`
  2. review `git diff --stat` and files changed
  3. run relevant checks
  4. refresh the PLAN + HANDOFF checkpoint, then stage reviewed changed continuity explicitly
  5. commit a focused change
  6. push the branch, complete the authorized merge, and verify remote main when a remote exists
- If the local helper exists, prefer `.agent/integrations/run-checkpoint.sh --reason pre-git-cycle`.

## Security Review Contract
- For review tasks, apply `.agent/REVIEW.md` Security Review Mode and complete the required security checklist.
- For validation/test tasks, run `.agent/TEST.md` security checks when work touches auth, data access, input handling, API surface, or deployment/runtime settings.

## TDD and Eval Contract
- The TDD rule, the `UNCONFIRMED` rule, and the Given/When/Then eval walkthrough are global policy in `~/.claude/CLAUDE.md` (TDD and Evals). Not repeated here.
- Repo-specific: if an eval plan is missing or vague, follow `docs/workflows/evals.md` and propose a minimal 3-eval set (happy, edge, failure/security) before implementation.

## Boundary Rules
- Safety boundaries (secrets, scope, ask-first on destructive or schema changes, never claim completion without evidence) are global policy in `~/.claude/CLAUDE.md` (Safety Boundaries). Not repeated here.
- Repo-specific, never do:
  - Remove failing tests to force a pass.
  - Read instruction files not triggered by the current task (see Startup Contract).

## Local Norms
- Persist repeated user corrections here so they survive across sessions.
- Do not duplicate higher-layer policy from `~/.claude/CLAUDE.md`.
