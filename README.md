# PossibNow Dev Harness

Drop a complete, tool-agnostic instruction hierarchy — planning, testing, review, and handoff workflows — into any repository without writing files from scratch. It works with Claude Code, Codex, Cursor, or any assistant that reads `AGENTS.md`/`CLAUDE.md`.

It was built by distilling hundreds of pages of best-practice references (captured under `docs/references/`) into practical, reusable templates.

> **Renamed in v4.0.0** — formerly *PossibLaw Agent Starter Pack* (plugin id `possiblaw-starter`). The plugin id is now `possibnow-dev-harness`, slash commands are `/possibnow-dev-harness:*`, and the repo lives at `PossibLaw/possibnow-dev-harness` (old URLs redirect). If you had the old plugin installed: `/plugin uninstall possiblaw-starter@possiblaw-plugins`, then install the new id below.

---

## Deploy It (Start Here)

Pick one path. **Both scaffold the same files** (`AGENTS.md`, `CLAUDE.md`, `.agent/*`, `docs/roles/`, `docs/workflows/`, `.claude/skills/`) into your repo and auto-detect your stack (Node/Python/Go/Rust) to pre-fill test/lint/build commands.

### Path A — One-line install into any repo (recommended)

Works with **any** assistant. Run this **from inside your target repo**:

```bash
# New/empty repo — scaffold everything
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/main/scripts/bootstrap-project.sh | bash -s -- .

# Existing repo with code — keep your progress files
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/main/scripts/bootstrap-project.sh | bash -s -- . --adopt
```

That's the whole install. Prefer not to pipe a remote script, or want overrides (`--name`, `--dry-run`, explicit commands)? See [Install options & advanced usage](#install-options--advanced-usage).

### Path B — Claude Code plugin (adds slash commands)

If you use Claude Code and want `/`-command convenience plus always-on runtime guardrails:

```
/plugin marketplace add PossibLaw/PossibLaw-Plugins
/plugin install possibnow-dev-harness@possiblaw-plugins
```

Then, inside any repo you want scaffolded, run:

```
/possibnow-dev-harness:init
```

The plugin also adds runtime guardrails (destructive-command blocker, sensitive-file protection, format-on-write, and a shared-handoff commit guard that refuses `git commit` while `.agent/HANDOFF.md` is untracked or unstaged) to every Claude Code session.

> **Tier 2 hooks (off by default):** the optional `hooks/tier2-hooks.json` (validate-task, validate-subagent, sanitize-input, git-status SessionStart) ships but is **not active by default**. Enable it by merging its entries into your `.claude/settings.json`. The base `hooks/hooks.json` guardrails are on by default once the plugin is installed.

### Which path should I use?

| | Path A — Script | Path B — Plugin |
|---|---|---|
| **Assistant** | Claude, Codex, Cursor, any `AGENTS.md` tool | Claude Code only |
| **Install** | One `curl` command, per repo | Marketplace install once, then `/init` per repo |
| **Adds slash commands** | No | Yes (`/possibnow-dev-harness:*`) |
| **Runtime guardrail hooks** | No (files only) | Yes |
| **Best for** | Any repo, any tool, CI, non-Claude teams | Claude Code users who want the full experience |

Optional user-level defaults (Codex/Claude global files) are covered under [Optional Global Setup](#optional-global-setup).

## Optimize an Existing Project

After updating the plugin, run:

```text
/possibnow-dev-harness:optimize
```

The default is read-only: inspect one project and prepare an evidence-backed
configuration diff. Review the proposal once, then run:

```text
/possibnow-dev-harness:optimize apply
```

The agent rechecks for intervening edits, backs up affected files, applies only
the reviewed changes, validates them, and records rollback instructions. Existing
model/effort choices stay unchanged unless task-specific quality evidence supports
a change. This is an agent workflow, not a deterministic installer or an automatic
router; no savings are guaranteed. It uses bundled policy `2026-09-18.1`, with no
private research access or always-on research hook.

For Codex/other hosts after project installation, ask: "Follow
`docs/workflows/optimization.md` to optimize this project." The namespaced slash
command itself is Claude Code-specific.

Update an installed Claude plugin with `/plugin update possibnow-dev-harness@possiblaw-plugins`,
then start a new session or use the host's plugin reload mechanism. Existing
projects are not silently migrated; `/optimize` prepares their changes.

## Two Tiers (How This Pack Grows With You)

The harness is built for non-developer legal users and starts simple. It has two tiers, and it grows with your codebase instead of overwhelming you up front.

- **Tier 1 — Starter (default):** the everyday workflow most projects ever need — `PLAN → TEST → REVIEW → HANDOFF`, current HANDOFF plus historical HISTORY, runtime guardrails, the **simplicity ladder** (prefer the simplest thing that works: reuse before writing new code), and always-on token discipline.
- **Tier 2 — Scale (opt-in, gated as the codebase grows):** indexed retrieval with Graphify, wiki orientation, and deeper review. When a repo gets large the harness suggests `/possibnow-dev-harness:scale`; you opt in. Tier 2 never removes Tier 1 rules — it only adds to them.

Learnings are **validation-gated**: auto-captured notes land in an Inbox, and a lesson is promoted into a category in `.agent/LEARNINGS.md` only if it recurred at least twice or you explicitly confirmed it. The template opens with a compass (what to capture / what not to), organizes promoted lessons into categories, and includes a review loop — so the learnings file stays small, trustworthy, and reviewable.

## Canonical Role Model

The dev harness is the canonical home for host-agnostic delivery roles.

- Shared role contracts live in `packs/project/docs/roles/*.md`.
- Codex routing lives in `packs/project/AGENTS.md`.
- Claude routing lives in `packs/project/CLAUDE.md` and the top-level `agents/*.md` (promoted from `packs/global/claude/.claude/agents/` in v2.0.0).
- Plugin packages and runtime adapters belong in the separate Plugins repository.

## What Each File Does

### Project-level files
- `AGENTS.md`: Codex operating contract for the repo; defines scope, execution standards, and routing behavior.
- `CLAUDE.md`: Claude operating contract for the repo; mirrors delivery and safety expectations for Claude workflows.
- `docs/vendor/README.md`: Vendor-doc contract; defines how agents should use local vendor references over model memory.
- `docs/vendor/supabase.md`: Initial vendor reference guide (Supabase) with key usage, env patterns, and security reminders.
- `docs/roles/README.md`: Canonical host-agnostic role registry for planning, review, validation, and handoff work.
- `docs/roles/*.md`: Shared role contracts that Claude and Codex wrappers should both follow.
- `docs/workflows/evals.md`: Evals-driven development guide to define “done” and iterate safely (with extra guidance for LLM features).
- `docs/workflows/contracts.md`: Typed workflow contract for `PLAN -> TEST -> REVIEW -> HANDOFF`, plus continuity checkpoints and optional memory/stage-skill integration rules.
- `docs/workflows/wiki.md`: Optional wiki-mode workflow for persistent codebase context (Obsidian-friendly) with trust-order and verification rules.
- `.agent/PLAN.md`: Working plan template — objective, assumptions, milestones, risks, and acceptance criteria (now also absorbs the former CONTEXT and TASKS checklists).
- `.agent/REVIEW.md`: Structured review rubric focused on correctness, regressions, and security findings.
- `.agent/TEST.md`: Validation contract with TDD/eval evidence requirements and security test checklist.
- `.agent/HANDOFF.md`: current checkpoint only.
- `.agent/HISTORY.md`: verified archive of previous handoffs, loaded on demand.
- `.agent/WIKI.md`: Optional wiki-mode config with Obsidian vault path and wiki sync rules (Tier 2).
- `.agent/LEARNINGS.md`: Optional, validation-gated learning log (default off) for reusable observations and proposed skill/plugin/instruction improvements.
- `.agent/integrations/*`: Local advisory checkpoint helper (`run-checkpoint.sh`) that prints the PLAN/HANDOFF updates to make.
- `docs/workflows/token-management.md`: Token/context budgeting guide so the harness stays fast and cheap.
- `.claude/skills/*/SKILL.md`: Repo-local workflow skills for repeated procedures (sprint closeout, novice-safe git cycle, the simplicity ladder, and scaling up with Graphify).

### Optional global files
- `~/.codex/AGENTS.md`: User-level Codex defaults that apply across repositories.
- `~/.claude/CLAUDE.md`: User-level Claude defaults that apply across repositories.
- `~/.claude/agents/*.md`: Reusable specialist agents available to Claude sessions.

This repository includes:
- Project-level instruction files (`AGENTS.md`, `CLAUDE.md`, `.agent/*`).
- Repo-local workflow skills under `.claude/skills/`.
- Optional global instruction files (`~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.claude/agents/*.md`).
- Full reference/source docs used to design this workflow.
- Architecture decision guides, including `docs/architecture/memory-and-indexing-guide.md`.

## Install options & advanced usage

The [one-line install](#path-a--one-line-install-into-any-repo-recommended) above covers most cases. This section documents the modes, flags, and alternatives.

### Pick the right mode

- **Brand new repo:** run the installer as-is (no `--adopt`). This creates all harness files.
- **Existing/older repo:** add `--adopt` (alias for `--preserve-progress`) so your existing state files are never overwritten.
- **Existing repo, intentionally reset progress** (PLAN/HANDOFF) to fresh templates: run without `--adopt`.

If you run the installer in a brand-new/empty repo (no detectable stack files yet), you may see a warning that commands are `UNCONFIRMED`. This is expected—either initialize the project and re-run, pass explicit `--primary/--test/--lint/--typecheck/--build` overrides, or edit `.agent/TEST.md` and `CLAUDE.md`.

### Adopt into an existing or older repo

`--adopt` preserves any existing continuity files and **assesses your codebase size** (it counts source files). When the repo is large (more than ~50 source files), the installer recommends turning on **Tier 2 Scale mode**:

```text
  SOURCE_FILE_COUNT=320
NOTE: large codebase detected (320 source files, threshold 50).
  ... In Claude Code, run: /possibnow-dev-harness:scale
```

Scale mode builds a Graphify index so the agent **queries the index instead of re-reading files**, which keeps a big codebase affordable. The SessionStart hook keeps reminding you until Scale mode is on. Small repos get no nudge and stay in the lean Tier 1 workflow. See `docs/workflows/graphify.md` and `docs/workflows/token-management.md`.

### Install without piping a remote script

If you prefer not to execute a remote script directly:

```bash
git clone --depth 1 https://github.com/PossibLaw/possibnow-dev-harness.git /tmp/possibnow-dev-harness
/tmp/possibnow-dev-harness/scripts/install-project.sh .
rm -rf /tmp/possibnow-dev-harness
```

### Manual install from a local harness clone

```bash
git clone https://github.com/PossibLaw/possibnow-dev-harness.git
cd possibnow-dev-harness
./scripts/install-project.sh ~/code/my-app
```

Tip: `git clone` uses the repository name (`possibnow-dev-harness`) as the folder unless you pass a custom destination:

```bash
git clone https://github.com/PossibLaw/possibnow-dev-harness.git my-dev-harness
```

The project installer auto-detects likely commands from repo signals (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, lockfiles). Use overrides only when you want explicit values:

```bash
./scripts/install-project.sh ~/code/my-app \
  --name "your-project" \
  --owner "your-team" \
  --primary "pnpm dev" \
  --test "pnpm test" \
  --lint "pnpm lint" \
  --typecheck "pnpm typecheck" \
  --build "pnpm build"
```

The installer keeps project continuity trackable and preserves existing state on every rerun. It removes exact obsolete harness exclusions while retaining broader custom and private rules for explicit review. Commit current/history handoffs, plan/context/tasks, test/review summaries, learnings, wiki, content continuity, archives, and existing project history with the work. Review for secrets and raw sensitive data before staging.

**Every commit must carry the handoff.** Refresh the Current Baton, run `git add .agent/HANDOFF.md`, then commit. In Claude Code the `validate-bash` guardrail refuses a `git commit` that would leave `.agent/HANDOFF.md` untracked or with unstaged edits (it honors `git commit -a` and an inline `git add` that covers the file, and never fires in repos without a handoff). Codex and other AGENTS.md-aware tools have no runtime hook, so `AGENTS.md` and `docs/workflows/contracts.md` state the same rule for them.

## Optional Global Setup

Install Codex and Claude global files:

```bash
./scripts/install-global.sh --codex --claude
```

Install only one tool:

```bash
./scripts/install-global.sh --codex
./scripts/install-global.sh --claude
```

## What Gets Added

### Project-level target repo
- `AGENTS.md`
- `CLAUDE.md`
- `.agent/PLAN.md`
- `.agent/REVIEW.md`
- `.agent/TEST.md`
- `.agent/HANDOFF.md`
- `.agent/WIKI.md`
- `.agent/LEARNINGS.md`
- `.agent/integrations/README.md`
- `.agent/integrations/run-checkpoint.sh`
- `.claude/skills/closing-sprint-and-syncing-state/SKILL.md`
- `.claude/skills/running-novice-safe-git-cycle/SKILL.md`
- `.claude/skills/applying-simplicity-ladder/SKILL.md`
- `.claude/skills/scaling-up-with-graphify/SKILL.md`
- `docs/vendor/README.md`
- `docs/vendor/supabase.md`
- `docs/roles/README.md`
- `docs/roles/product-strategist.md`
- `docs/roles/engineering-planner.md`
- `docs/roles/reviewer.md`
- `docs/roles/security-reviewer.md`
- `docs/roles/qa-validator.md`
- `docs/roles/docs-releaser.md`
- `docs/workflows/evals.md`
- `docs/workflows/contracts.md`
- `docs/workflows/wiki.md`
- `docs/workflows/graphify.md`
- `docs/workflows/token-management.md`
- `docs/glossary.md`
- `.gitignore` updates: exact obsolete continuity exclusions are removed; unrelated private rules remain. Broad rules hiding continuity produce a warning.

`Learning Mode` defaults to `OFF`. Turn it on per task by setting `Learning Mode: CAPTURE` or `Learning Mode: APPLY` in `.agent/PLAN.md` (or by explicit prompt instruction).
Continuity checkpoints default to sprint closeout, pre-git-cycle, session end, and "context feels ~50% full" as a heuristic trigger.

### Global-level home folder (optional)
- `~/.codex/AGENTS.md`
- `~/.claude/CLAUDE.md`
- `~/.claude/agents/*.md`

## Vendor Docs Workflow
- Keep project-curated vendor integration guidance in `docs/vendor/<vendor>.md`.
- Include `Last verified: YYYY-MM-DD` and official source links in each vendor file.
- Agents should read `docs/vendor/` first for vendor/API/security setup work, then verify against current official docs when recency matters.

## Contract Pipeline and Optional Integrations
- `docs/workflows/contracts.md` defines the typed artifact header, continuity checkpoint rules, and cross-artifact linkage rules.
- Required stage order: `PLAN -> TEST -> REVIEW -> HANDOFF`.

## Memory
- `docs/architecture/memory-and-indexing-guide.md` explains which memory/indexing layer owns which facts and when to enable optional layers.
- Source code, tests, runtime behavior, and active state artifacts remain the source of truth.
- Current state is `.agent/HANDOFF.md`; `.agent/HISTORY.md` preserves prior handoffs verbatim. PLAN holds the goal, assumptions, and task checklist. All relevant continuity ships with the work.
- `.agent/LEARNINGS.md` is default-off and validation-gated: capture a reusable observation only when `Learning Mode` is `CAPTURE` or `APPLY`. Auto-captured notes stage in an Inbox and are promoted into a category only after a lesson recurs at least twice or you confirm it. The template opens with a compass (what to capture / what not to) and carries a review loop for periodic triage.
- `.agent/integrations/run-checkpoint.sh` is an advisory printer — it lists the required `PLAN`/`HANDOFF` updates at sprint closeout, pre-git-cycle, or context pressure. It does not write state.
- Wiki mode and Graphify are Tier 2 orientation/indexing layers; generated claims stay advisory until verified against source.

Examples:
- Local artifact: a handoff records that matter records are created only after `conflict_check.status = approved`, why draft matters for rejected intakes were rejected, what tests proved it, and what remains open.
- Historical checkpoints: archive and hash-verify the old handoff in HISTORY before replacement; do not load that archive during normal resume.
- Manual wiki (Tier 2): use curated pages for stable codebase maps, domain glossary, architecture notes, and cross-links that humans may want to edit.
- Graphify (Tier 2): read the generated wiki layer (`graphify-out/wiki/index.md`) and run focused graph queries for first-pass orientation on larger repos, then verify the result in source before implementation.
- Non-developer path: ask the agent to "index this codebase with Graphify" (or run `/possibnow-dev-harness:scale`). The project contract tells the agent to configure `.agent/WIKI.md`, create safe ignore rules, install Graphify only with approval if missing, run the graph build, and report where the output lives.

> Note: a retrieval backend such as MemPalace is a *possible future optional layer* over completed local artifacts; it is not shipped today.

## Optional Wiki Mode
- `docs/workflows/wiki.md` defines how to use a persistent wiki for faster startup context.
- Wiki mode is for orientation and synthesis, not authority; source code and tests remain authoritative.
- Supports both in-repo wiki files and external Obsidian vaults on local disk.
- Wiki backend defaults to `manual`; `graphify` is an optional generated graph/wiki backend.
- Graphify output such as `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json` is advisory until verified against source.
- Do not install Graphify always-on assistant hooks, git hooks, or watch mode without explicit user approval.
- To enable it in a repo, set `Enabled: ON` and update `Vault root (absolute)` in `.agent/WIKI.md`.
- After vault setup, the wiki root is generated with `{vault_root}/codebases/{repo_name}` and reused for handoff sync.

## Safety and Rollback
- Existing destination files are backed up before overwrite.
- Backup format: `<filename>.bak.<timestamp>`.
- Installers only copy curated files from `packs/`.
- Runtime files, auth files, logs, and caches are never installed.

## Verify This Harness

```bash
./scripts/verify-pack.sh
```

`verify-pack.sh` also runs the guardrail unit tests (`tests/guardrails/`) when a `python3` with pytest is available, and reports `UNCONFIRMED` otherwise. To run them directly:

```bash
python3 -m pytest tests/guardrails -q
```

## Learning Mode Helper

Set learning mode in a repo's `.agent/PLAN.md` without manual edits:

```bash
# from inside target repo
/path/to/possibnow-dev-harness/scripts/set-learning-mode.sh CAPTURE

# explicit target repo path
/path/to/possibnow-dev-harness/scripts/set-learning-mode.sh /path/to/your/repo OFF
```

## Continuity Checkpoint Helper

Flag a sprint-closeout or pre-git checkpoint in a target repo:

```bash
# from inside target repo
./.agent/integrations/run-checkpoint.sh --reason sprint-closeout

# explicit target repo path
/path/to/your/repo/.agent/integrations/run-checkpoint.sh /path/to/your/repo --reason pre-git-cycle
```

The helper does not invent summaries. It is an advisory checklist printer: it flags the required `.agent/PLAN.md` and `.agent/HANDOFF.md` updates (archive/verify old HANDOFF in HISTORY, then replace the current checkpoint), reads learning mode, and shows git scope. It does not write state and does not call any backend.

## Repository Layout

```text
packs/
  project/                 # Repo-level files
    docs/roles/            # Canonical host-agnostic role contracts
    docs/vendor/           # Local vendor integration references
    docs/workflows/        # Evals, contracts, token management, and indexing guidance
    .claude/skills/        # Repo-local workflow skills
    .agent/integrations/   # Local advisory checkpoint helper (run-checkpoint.sh)
  global/claude/           # ~/.claude curated files
  global/codex/            # ~/.codex curated files
scripts/                   # Bash only (macOS + Linux)
  bootstrap-project.sh
  install-project.sh
  install-global.sh
  verify-pack.sh
  set-learning-mode.sh
docs/
  references/              # Full source docs
  architecture/
  onboarding/
```

## Source Lineage
- `docs/references/claude-md-agents-md-reference-guide.md`
- `docs/references/agent-instructions-summary.md`
- `docs/references/claude-agents-README.md`

## Notes
- Launch support is macOS and Linux only. Scripts are bash-only; Windows/PowerShell support has been dropped.
