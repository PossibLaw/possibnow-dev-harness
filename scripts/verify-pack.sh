#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

REQUIRED_FILES=(
  "README.md"
  "CHANGELOG.md"
  ".agent/HANDOFF.md"
  ".claude-plugin/plugin.json"
  "commands/init.md"
  "commands/guardrails.md"
  "commands/scale.md"
  "commands/optimize.md"
  ".agents/skills/possibnow-init/SKILL.md"
  ".agents/skills/possibnow-scale/SKILL.md"
  ".agents/skills/possibnow-guardrails/SKILL.md"
  ".agents/skills/possibnow-optimize/SKILL.md"
  "packs/project/docs/workflows/optimization.md"
  "packs/project/.agent/HISTORY.md"
  "skills/closing-sprint-and-syncing-state/SKILL.md"
  "skills/running-novice-safe-git-cycle/SKILL.md"
  "skills/applying-simplicity-ladder/SKILL.md"
  "skills/scaling-up-with-graphify/SKILL.md"
  "hooks/hooks.json"
  "scripts/guardrails/validate-bash.py"
  "tests/guardrails/test_validate_bash.py"
  "scripts/bootstrap-project.sh"
  "scripts/install-project.sh"
  "scripts/install-global.sh"
  "scripts/verify-pack.sh"
  "scripts/set-learning-mode.sh"
  "packs/project/AGENTS.md"
  "packs/project/CLAUDE.md"
  "packs/project/docs/roles/README.md"
  "packs/project/docs/roles/product-strategist.md"
  "packs/project/docs/roles/engineering-planner.md"
  "packs/project/docs/roles/reviewer.md"
  "packs/project/docs/roles/security-reviewer.md"
  "packs/project/docs/roles/qa-validator.md"
  "packs/project/docs/roles/docs-releaser.md"
  "packs/project/docs/vendor/README.md"
  "packs/project/docs/vendor/supabase.md"
  "packs/project/docs/workflows/evals.md"
  "packs/project/docs/workflows/contracts.md"
  "packs/project/docs/workflows/wiki.md"
  "packs/project/docs/workflows/graphify.md"
  "packs/project/docs/workflows/token-management.md"
  "packs/project/docs/glossary.md"
  "packs/project/.agent/PLAN.md"
  "packs/project/.agent/REVIEW.md"
  "packs/project/.agent/TEST.md"
  "packs/project/.agent/HANDOFF.md"
  "packs/project/.agent/WIKI.md"
  "packs/project/.agent/LEARNINGS.md"
  "packs/project/.agent/integrations/README.md"
  "packs/project/.agent/integrations/run-checkpoint.sh"
  "packs/global/codex/.codex/AGENTS.md"
  "packs/global/claude/.claude/CLAUDE.md"
)

FORBIDDEN_PATTERNS=(
  "packs/global/claude/.claude/debug"
  "packs/global/claude/.claude/projects"
  "packs/global/claude/.claude/cache"
  "packs/global/claude/.claude/history.jsonl"
  "packs/global/codex/.codex/auth.json"
  "packs/global/codex/.codex/history.jsonl"
  "packs/global/codex/.codex/sessions"
  "packs/project/.claude/history.md"
  "packs/project/.agent/CONTEXT.md"
  "packs/project/.agent/TASKS.md"
  "packs/project/.agent/integrations/mempalace-ingest.sh"
  "packs/project/.agent/integrations/mempalace-ingest.ps1"
  "packs/project/.agent/integrations/run-checkpoint.ps1"
  "scripts/verify-pack.ps1"
  "scripts/install-project.ps1"
  "scripts/install-global.ps1"
  "scripts/bootstrap-project.ps1"
  "scripts/set-learning-mode.ps1"
  "scripts/guardrails/persist-state.py"
)

missing=0
for rel in "${REQUIRED_FILES[@]}"; do
  if [[ ! -e "$REPO_ROOT/$rel" ]]; then
    echo "BLOCKED: missing required file: $rel"
    missing=1
  fi
done
if [[ "$missing" -ne 0 ]]; then
  exit 1
fi

for rel in "${FORBIDDEN_PATTERNS[@]}"; do
  if [[ -e "$REPO_ROOT/$rel" ]]; then
    echo "BLOCKED: forbidden path present (should have been removed): $rel"
    exit 1
  fi
done

if git -C "$REPO_ROOT" check-ignore -q .agent/HANDOFF.md; then
  echo "BLOCKED: root .agent/HANDOFF.md must be trackable for team continuity"
  exit 1
fi
if git -C "$REPO_ROOT" check-ignore -q .agent/PLAN.md; then
  echo "BLOCKED: root .agent/PLAN.md must be trackable"
  exit 1
fi

for script in "$REPO_ROOT/scripts/bootstrap-project.sh" "$REPO_ROOT/scripts/install-project.sh" "$REPO_ROOT/scripts/install-global.sh" "$REPO_ROOT/scripts/verify-pack.sh" "$REPO_ROOT/scripts/set-learning-mode.sh"; do
  if [[ ! -x "$script" ]]; then
    echo "BLOCKED: script is not executable: ${script#$REPO_ROOT/}"
    exit 1
  fi
done

# Installer behavior is covered with disposable fixtures in tests/installer.
python3 "$REPO_ROOT/scripts/render_entries.py" --check
python3 "$REPO_ROOT/scripts/entry_policy.py" "$REPO_ROOT/packs/project/AGENTS.md" "$REPO_ROOT/packs/project/CLAUDE.md" "$REPO_ROOT/packs/global/codex/.codex/AGENTS.md" "$REPO_ROOT/packs/global/claude/.claude/CLAUDE.md"

has_rg=0
if command -v rg >/dev/null 2>&1; then
  has_rg=1
fi

STOP_MARKER="STOP: normal resume context ends here; older entries below are archive."

allowed_placeholders='<(PROJECT_NAME|TEAM_OR_OWNER|PRIMARY_COMMAND|TEST_COMMAND|LINT_COMMAND|TYPECHECK_COMMAND|BUILD_COMMAND)>'
if [[ "$has_rg" -eq 1 ]]; then
  unexpected="$(rg -n '<[A-Z_]+>' "$REPO_ROOT/packs" | rg -v "$allowed_placeholders" || true)"
else
  unexpected="$(grep -RInE -I --exclude-dir='.*' --exclude='.*' -- '<[A-Z_]+>' "$REPO_ROOT/packs" | grep -Ev -- "$allowed_placeholders" || true)"
fi
if [[ -n "$unexpected" ]]; then
  echo "BLOCKED: unexpected placeholder(s) found:"
  echo "$unexpected"
  exit 1
fi

# Stale references that must not survive the v3 refresh / v4 rename (scoped to the active pack + harness files).
forbid_text() {
  local pattern="$1"
  local hits
  local scope=("$REPO_ROOT/packs/project" "$REPO_ROOT/skills" "$REPO_ROOT/commands" "$REPO_ROOT/hooks")
  if [[ "$has_rg" -eq 1 ]]; then
    hits="$(rg -l --fixed-strings "$pattern" "${scope[@]}" 2>/dev/null || true)"
  else
    hits="$(grep -RIl -- "$pattern" "${scope[@]}" 2>/dev/null || true)"
  fi
  if [[ -n "$hits" ]]; then
    echo "BLOCKED: stale reference '$pattern' still present in:"
    echo "$hits"
    exit 1
  fi
}
forbid_text "mempalace-ingest"
forbid_text ".claude/history.md"
forbid_text "run-checkpoint.ps1"
forbid_text "Local Continuity Files (Do Not Commit)"
forbid_text "continuity stays local"
forbid_text "possiblaw-starter"
forbid_text "Agent Starter Pack"

require_text() {
  local file="$1"
  local pattern="$2"
  local message="$3"
  if [[ "$has_rg" -eq 1 ]]; then
    if ! rg -q --fixed-strings "$pattern" "$file"; then
      echo "BLOCKED: $message"
      exit 1
    fi
    return 0
  fi

  if ! grep -Fq -- "$pattern" "$file"; then
    echo "BLOCKED: $message"
    exit 1
  fi
}

# Check reachable policy homes, not duplicated handbook text in each root.
for f in CLAUDE.md AGENTS.md; do
  for workflow in delivery contracts learning content clients optimization graphify token-management; do
    require_text "$REPO_ROOT/packs/project/$f" "docs/workflows/$workflow.md" "missing task route: $workflow in $f"
    test -f "$REPO_ROOT/packs/project/docs/workflows/$workflow.md"
  done
done

require_text "$REPO_ROOT/packs/project/docs/roles/README.md" "## Canonical Roles" "missing canonical role table in packs/project/docs/roles/README.md"

# Continuity contract
require_text "$REPO_ROOT/packs/project/docs/workflows/contracts.md" "## Current and Historical Continuity Contract (Required)" "missing current/history continuity contract in contracts.md"
require_text "$REPO_ROOT/packs/project/docs/workflows/contracts.md" "## Continuity Checkpoints (Required)" "missing checkpoint section in contracts.md"
require_text "$REPO_ROOT/packs/project/docs/workflows/contracts.md" "## Scale Mode (Tier 2, Default OFF)" "missing scale mode section in contracts.md"
require_text "$REPO_ROOT/packs/project/docs/workflows/wiki.md" "## Trust Order (Required)" "missing trust order section in packs/project/docs/workflows/wiki.md"
require_text "$REPO_ROOT/packs/project/docs/workflows/graphify.md" "graphifyy" "graphify.md not refreshed to upstream package name graphifyy"
require_text "$REPO_ROOT/packs/project/docs/workflows/token-management.md" "# Token Management" "missing title in packs/project/docs/workflows/token-management.md"

# State artifacts
require_text "$REPO_ROOT/packs/project/.agent/WIKI.md" "artifact_type: wiki_config" "missing wiki config artifact_type in packs/project/.agent/WIKI.md"
require_text "$REPO_ROOT/packs/project/.agent/WIKI.md" 'Vault root (absolute): `UNCONFIRMED`' "missing vault-path setup marker in packs/project/.agent/WIKI.md"
require_text "$REPO_ROOT/packs/project/.agent/PLAN.md" "contract_version: 1" "missing contract header in packs/project/.agent/PLAN.md"
require_text "$REPO_ROOT/packs/project/.agent/PLAN.md" "artifact_type: plan" "missing plan artifact_type in packs/project/.agent/PLAN.md"
require_text "$REPO_ROOT/packs/project/.agent/PLAN.md" "## Task Checklist" "missing task checklist (folded TASKS) in packs/project/.agent/PLAN.md"
require_text "$REPO_ROOT/packs/project/.agent/PLAN.md" "$STOP_MARKER" "missing newest-first stop marker in packs/project/.agent/PLAN.md"
require_text "$REPO_ROOT/packs/project/.agent/TEST.md" "artifact_type: test" "missing test artifact_type in packs/project/.agent/TEST.md"
require_text "$REPO_ROOT/packs/project/.agent/REVIEW.md" "artifact_type: review" "missing review artifact_type in packs/project/.agent/REVIEW.md"
require_text "$REPO_ROOT/packs/project/.agent/HANDOFF.md" "artifact_type: handoff" "missing handoff artifact_type in packs/project/.agent/HANDOFF.md"
require_text "$REPO_ROOT/packs/project/.agent/HANDOFF.md" "shared, version-controlled continuity record" "missing shared continuity policy in packs/project/.agent/HANDOFF.md"
require_text "$REPO_ROOT/packs/project/.agent/HANDOFF.md" "## Sprint / Git Cycle" "missing sprint git section in packs/project/.agent/HANDOFF.md"
require_text "$REPO_ROOT/packs/project/.agent/HANDOFF.md" ".agent/HISTORY.md" "missing historical checkpoint link"
require_text "$REPO_ROOT/packs/project/.agent/HISTORY.md" "include_in_memory: false" "history must be on-demand"
require_text "$REPO_ROOT/packs/project/docs/workflows/learning.md" "## Promotion gate" "missing validation/promotion gate in packs/project/.agent/LEARNINGS.md"
require_text "$REPO_ROOT/packs/project/.agent/integrations/README.md" "run-checkpoint" "missing run-checkpoint reference in integrations README"

# Skills
require_text "$REPO_ROOT/skills/closing-sprint-and-syncing-state/SKILL.md" "name: closing-sprint-and-syncing-state" "missing closing sprint skill metadata"
require_text "$REPO_ROOT/skills/running-novice-safe-git-cycle/SKILL.md" "name: running-novice-safe-git-cycle" "missing git cycle skill metadata"
require_text "$REPO_ROOT/skills/applying-simplicity-ladder/SKILL.md" "name: applying-simplicity-ladder" "missing simplicity ladder skill metadata"
require_text "$REPO_ROOT/skills/scaling-up-with-graphify/SKILL.md" "name: scaling-up-with-graphify" "missing scale mode skill metadata"

# Plugin manifest
require_text "$REPO_ROOT/.claude-plugin/plugin.json" '"name": "possibnow-dev-harness"' "missing plugin name in .claude-plugin/plugin.json"
require_text "$REPO_ROOT/.claude-plugin/plugin.json" '"version": "4.2.0"' "plugin.json not bumped to version 4.2.0"

# Shared handoff commit guard (Claude runtime) and its tests
require_text "$REPO_ROOT/scripts/guardrails/validate-bash.py" "def check_handoff_commit" "missing shared-handoff commit guard in scripts/guardrails/validate-bash.py"
require_text "$REPO_ROOT/tests/guardrails/test_validate_bash.py" "test_commit_blocked_when_handoff_untracked" "missing shared-handoff commit guard tests in tests/guardrails/test_validate_bash.py"
require_text "$REPO_ROOT/hooks/hooks.json" "validate-bash.py" "validate-bash hook not wired in hooks/hooks.json"

agent_md_count="$(find "$REPO_ROOT/agents" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')"
if [[ "$agent_md_count" -lt 8 ]]; then
  echo "BLOCKED: expected at least 8 agent .md files in agents/, found $agent_md_count"
  exit 1
fi

if [[ ! -x "$REPO_ROOT/scripts/guardrails/validate-bash.py" ]]; then
  echo "BLOCKED: scripts/guardrails/validate-bash.py is not executable"
  exit 1
fi
require_text "$REPO_ROOT/packs/global/claude/.claude/CLAUDE.md" "For vendor setup/API/security guidance, verify against official vendor docs and cite source date." "missing vendor recency rule in packs/global/claude/.claude/CLAUDE.md"
require_text "$REPO_ROOT/packs/global/codex/.codex/AGENTS.md" "For vendor setup/API/security guidance, verify against official vendor docs and cite source date." "missing vendor recency rule in packs/global/codex/.codex/AGENTS.md"

# Guardrail unit tests: run with the first python3 that has pytest; otherwise report the gap.
PYTEST_PY=""
for candidate in "$REPO_ROOT/.venv/bin/python" python3 /usr/bin/python3 /opt/homebrew/bin/python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import pytest' >/dev/null 2>&1; then
    PYTEST_PY="$candidate"
    break
  fi
done
if [[ -n "$PYTEST_PY" ]]; then
  if ! (cd "$REPO_ROOT" && "$PYTEST_PY" -m pytest tests/guardrails tests/installer tests/harness -q -p no:cacheprovider); then
    echo "BLOCKED: guardrail unit tests failed (tests/guardrails)"
    exit 1
  fi
else
  echo "BLOCKED: pytest required for release verification (UNCONFIRMED)"
  exit 1
fi

echo "DONE: verification passed"
