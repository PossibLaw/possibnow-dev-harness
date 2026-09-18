# AGENTS.md

Repo Root (absolute path, required): /path/to/your/repo

Cross-tool project instruction file for <PROJECT_NAME>. This mirrors `CLAUDE.md`; keep the two in sync.

## Two Tiers (How This Pack Grows With You)
- **Tier 1 — Starter (default):** small-app workflow — `PLAN → TEST → REVIEW → HANDOFF`, current/historical continuity, guardrails, and the simplicity ladder. Everything most projects need.
- **Tier 2 — Scale (gated as the codebase grows):** indexed retrieval (Graphify), wiki orientation, deeper review. When a repo gets large the harness suggests Scale mode; you opt in. Tier 2 adds to Tier 1, never removes it.

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
5. Global continuity stays in `~/.codex/AGENTS.md`. Repo continuity is optional and on-demand.
6. When a sprint is wrapping, work is about to pause or ship, or context feels roughly half full, run a continuity checkpoint before losing state.

## Token Discipline (Always On)
Keep context small (full guide: `docs/workflows/token-management.md`):
- On resume, read the current `.agent/HANDOFF.md`; historical checkpoints stay in `.agent/HISTORY.md`.
- Load the trigger files in the Startup Contract on demand — never read the whole repo or all docs at startup.
- Keep genuinely stable instruction blocks stable; update PLAN whenever the facts change.
- Apply the simplicity ladder (below) — less generated code is less to read, review, and maintain.
- At Tier 2, query the Graphify index instead of re-reading source files.

## Simplicity Ladder (Always On)
After you understand the problem, prefer the simplest option that works, in this order:
1. Does this even need to exist? 2. Reuse something already in the codebase. 3. Standard library. 4. Native platform feature. 5. Existing dependency. 6. A small one-liner. 7. Only then a minimal new solution.
Analyze thoroughly; build minimally.

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
- This file is the cross-tool contract (read by Codex and other AGENTS.md-aware tools), with global defaults in `~/.codex/AGENTS.md`.
- `CLAUDE.md` is the Claude mirror of this contract; keep the two in sync.
- Shared contracts in `docs/roles/`, `docs/workflows/`, and `docs/vendor/` apply to every tool.

## Session Memory
Current continuity lives in `${REPO_ROOT}/.agent/HANDOFF.md`; previous checkpoints are preserved in `${REPO_ROOT}/.agent/HISTORY.md`. Both are version-controlled.

Before pausing, handing off, or moving into a git cycle, refresh:
- `${REPO_ROOT}/.agent/PLAN.md` milestone status and sprint status.
- `${REPO_ROOT}/.agent/HANDOFF.md`: archive and verify the old checkpoint in HISTORY, then write the new Current Baton.
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
- Turn on by setting `Learning Mode` in `.agent/PLAN.md` or by explicit user instruction (`CAPTURE` or `APPLY`).
- Mode behavior:
  - `OFF`: no learning entries and no skill/plugin updates.
  - `CAPTURE`: add lessons to `.agent/LEARNINGS.md` only.
  - `APPLY`: capture lessons and propose specific skill/plugin/instruction updates.
- **Promotion gate:** only add a lesson that recurred at least twice or that the user explicitly confirmed. One-off observations stay out, so the file does not rot.
- This is additive. Do not replace `.agent/HANDOFF.md`.

## Canonical Roles
- `product-strategist` — Clarifies user value, scope, and success criteria. Source of truth: `docs/roles/product-strategist.md`.
- `engineering-planner` — Produces an executable implementation plan with risks and eval IDs. Source of truth: `docs/roles/engineering-planner.md`.
- `reviewer` — Performs correctness and regression review. Source of truth: `docs/roles/reviewer.md`.
- `security-reviewer` — Performs attacker-minded review and security-check pressure testing. Source of truth: `docs/roles/security-reviewer.md`.
- `qa-validator` — Executes evals and records receipts. Source of truth: `docs/roles/qa-validator.md`.
- `docs-releaser` — Syncs handoff and user-facing docs after validation. Source of truth: `docs/roles/docs-releaser.md`.

## Routing Rules
- Product framing, scope, or success-definition work → `product-strategist`.
- Implementation planning and architecture tradeoffs → `engineering-planner`.
- Test execution, eval receipts, and validation evidence → `qa-validator`.
- Correctness, regressions, and maintainability review → `reviewer`.
- Security-sensitive review or trust-boundary changes → `security-reviewer`.
- Release notes, handoff, and docs sync after validated changes → `docs-releaser`.
- If required facts are missing, escalate once with a targeted question.

## Contract Pipeline (Required)
- Canonical source: `docs/workflows/contracts.md`. Read it for full rules, artifact schema, cross-artifact linkage, and validation commands.
- Quick summary: stage order is `PLAN.md` → `TEST.md` → `REVIEW.md` → `HANDOFF.md`; each stage must cite evidence from the prior stage; never return `DONE` with an unresolved upstream artifact.

## Continuity Checkpoint Contract
- Canonical source: `docs/workflows/contracts.md` (Continuity Checkpoints section).
- Quick summary: run a checkpoint at sprint close, before a git cycle, before ending the session, and when context pressure risks losing current state. Each checkpoint updates `.agent/PLAN.md` and current `.agent/HANDOFF.md` and historical `.agent/HISTORY.md`, and `.agent/LEARNINGS.md` when learning mode is enabled.
- If present, the optional helper `.agent/integrations/run-checkpoint.sh` prints the required updates as a checklist; it does not write state for you.

## Scale Mode (Tier 2, Default OFF)
- For small projects, stay in Tier 1. When the codebase grows large (roughly 40–50+ source files) or you start working inside an existing large codebase, switch on Scale mode.
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

## Security Review Contract
- For review tasks, apply `.agent/REVIEW.md` Security Review Mode and complete the required security checklist.
- For validation/test tasks, run `.agent/TEST.md` security checks when work touches auth, data access, input handling, API surface, or deployment/runtime settings.

## TDD and Eval Contract
- For code changes, use TDD when feasible: start with a failing test/eval, implement the minimum code to pass, then refactor while checks stay green.
- Never assume eval inputs, acceptance criteria, fixtures, or expected outputs; mark unknowns as `UNCONFIRMED` and resolve with a targeted user question.
- For any new or changed behavior, provide an end-user eval walkthrough before implementation using plain language plus Given/When/Then, including happy path, edge case, and failure/security case.
- Minimize user friction: infer likely test/eval commands and fixtures from repository signals first; ask the user only targeted follow-ups for unresolved unknowns.
- If an eval plan is missing or vague, follow `docs/workflows/evals.md` and propose a minimal 3-eval set (happy, edge, failure/security) before implementation.

## Boundary Rules
Always do:
- Keep edits within requested scope.
- Cite exact file paths and commands.
- Mark unknowns as `UNCONFIRMED`.

Ask first:
- Destructive actions, schema changes, or remote write operations.
- Scope expansion beyond requested deliverables.

Never do:
- Invent facts or claim completion without validation.
- Remove failing tests to force passing results.
- Expose secrets.
- Modify Claude-specific files (`CLAUDE.md`, `.claude/*`) unless user explicitly asks.
- Read instruction files not triggered by the current task.

## Git Workflow Contract
- Use focused branches and atomic commits.
- Attach validation evidence to PRs/handoffs.
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

## Local Norms
- Persist repeated user corrections here so they survive across sessions.
- Do not duplicate higher-layer policy from `~/.codex/AGENTS.md`.
