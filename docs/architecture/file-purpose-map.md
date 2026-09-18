# File Purpose Map

## Project Pack (`packs/project`)
- `AGENTS.md`: Codex startup and execution contract for a repo.
- `CLAUDE.md`: Claude startup and execution contract for a repo.
- `docs/roles/README.md`: canonical role registry shared by Codex and Claude wrappers.
- `docs/roles/*.md`: role contracts for planning, review, validation, and handoff stages.
- `docs/vendor/README.md`: rules for using local vendor docs as authoritative defaults.
- `docs/vendor/supabase.md`: Supabase-specific integration and security reference.
- `docs/workflows/evals.md`: evals-driven development guide (define “done”, design evals, and iterate safely).
- `docs/workflows/contracts.md`: typed state-artifact pipeline (`PLAN -> TEST -> REVIEW -> HANDOFF`) plus continuity checkpoint and optional skill integration rules.
- `docs/workflows/token-management.md`: context/cost measurement guidance, loaded for context or cost tasks.
- `docs/workflows/wiki.md`: optional Tier-2 wiki-mode workflow for persistent context acceleration with code-first verification.
- `docs/workflows/graphify.md`: optional Tier-2 Graphify indexing workflow and non-developer request contract.
- `docs/glossary.md`: short, beginner-friendly glossary of terms used across the pack.
- `.agent/PLAN.md`: planning artifact template (objective, assumptions, and task checklist — absorbs the former CONTEXT and TASKS files).
- `.agent/REVIEW.md`: review + security checklist.
- `.agent/TEST.md`: validation matrix and security checks.
- `.agent/HANDOFF.md`: current checkpoint only.
- `.agent/HISTORY.md`: exact archived handoffs, loaded on demand; preserves legacy historical records.
- `.agent/WIKI.md`: optional Tier-2 wiki-mode config (vault path, wiki root, sync rules).
- `.agent/LEARNINGS.md`: optional, validation-gated learning log for reusable observations and improvement proposals.
- `.agent/integrations/*`: local advisory checkpoint helper (`run-checkpoint.sh`) that prints the required PLAN/HANDOFF updates; it does not write state or call a backend.
- `.claude/skills/*/SKILL.md`: repo-local workflow skills for repeated procedures (sprint closeout, novice-safe git cycle, the simplicity ladder, scaling up with Graphify).

## Global Pack (`packs/global`)
- `codex/.codex/AGENTS.md`: Codex user-level global policy.
- `claude/.claude/CLAUDE.md`: Claude user-level global policy.
- `claude/.claude/agents/*.md`: reusable global sub-agents.

## Scripts (bash only — macOS + Linux)
- `scripts/bootstrap-project.sh`: clones the pack to a temp dir and runs the project installer.
- `scripts/install-project.sh`: installs project hierarchy into any repo.
- `scripts/install-global.sh`: optional global hierarchy installer.
- `scripts/verify-pack.sh`: structural and safety checks.
- `scripts/set-learning-mode.sh`: updates `.agent/PLAN.md` learning mode (`OFF`, `CAPTURE`, `APPLY`).

## Plugin Components (top-level)
- `.claude-plugin/plugin.json`: Claude Code plugin manifest (`possibnow-dev-harness`).
- `commands/init.md`: `/possibnow-dev-harness:init` — scaffolds project files into the current repo.
- `commands/scale.md`: `/possibnow-dev-harness:scale` — raises the repo to Tier 2 (Scale mode: Graphify + wiki).
- `commands/guardrails.md`: `/possibnow-dev-harness:guardrails` — views active Tier-1 safety hooks.
- `skills/applying-simplicity-ladder/SKILL.md`: the always-on simplicity-ladder procedure.
- `skills/scaling-up-with-graphify/SKILL.md`: Tier-2 procedure for indexing a larger codebase.
- `agents/*.md`: host-agnostic specialist agents promoted to the top level.
- `hooks/hooks.json`: Tier-1 Claude runtime hooks, on by default with the plugin; `hooks/tier2-hooks.json` is the opt-in Tier-2 set.
- `scripts/guardrails/*`: hook implementations — destructive-command blocker and shared-handoff commit guard (`validate-bash.py`), protected-file check, format check, and the Tier-2 helpers; unit tests live in `tests/guardrails/`.

## Repository Docs
- `docs/architecture/memory-and-indexing-guide.md`: decision guide for repo memory layers, optional indexing, and Graphify fit.

For the current authoritative routing/ownership map, use [rule-ownership.md](rule-ownership.md). The root entries are generated adapters; implementation procedures live in the delivery workflow.
