#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Install project-level agent files into a target repository.

Usage:
  install-project.sh [target-repo] [options]

Options:
  --name <project_name>
  --owner <team_or_owner>
  --primary "<primary_command>"
  --test "<test_command>"
  --lint "<lint_command>"
  --typecheck "<typecheck_command>"
  --build "<build_command>"
  --preserve-progress   Preserve existing progress files (now always the default)
  --adopt               Adopt into an existing/older repo (alias for --preserve-progress).
                        Also assesses codebase size and recommends Tier 2 Scale mode (Graphify)
                        when the repo is large.
  --dry-run
  -h, --help

Adding to an existing/older repo:
  install-project.sh /path/to/old-repo --adopt
USAGE
}

TARGET_DIR="."
if [[ $# -gt 0 && "$1" != -* ]]; then
  TARGET_DIR="$1"
  shift
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  if [[ "$TARGET_DIR" == "/path/to/your/repo" || "$TARGET_DIR" == "C:\\path\\to\\your\\repo" ]]; then
    echo "BLOCKED: target directory is still a placeholder: $TARGET_DIR"
    echo "Hint: run from inside your target repo with '.' as the target."
    exit 1
  fi
  echo "BLOCKED: target directory does not exist: $TARGET_DIR"
  echo "Hint: run from inside your target repo with '.' as the target."
  exit 1
fi

TARGET_DIR="$(cd "$TARGET_DIR" && pwd -P)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PACK_ROOT="$REPO_ROOT/packs/project"
TS="$(date '+%Y%m%d-%H%M%S')"

if [[ ! -d "$PACK_ROOT" ]]; then
  echo "BLOCKED: missing project pack: $PACK_ROOT"
  exit 1
fi

PROJECT_NAME="$(basename "$TARGET_DIR")"
TEAM_OR_OWNER="${USER:-UNCONFIRMED}"
PRIMARY_COMMAND="UNCONFIRMED"
TEST_COMMAND="UNCONFIRMED"
LINT_COMMAND="UNCONFIRMED"
TYPECHECK_COMMAND="UNCONFIRMED"
BUILD_COMMAND="UNCONFIRMED"
DETECTED_STACK="UNCONFIRMED"
USER_PRIMARY_COMMAND=""
USER_TEST_COMMAND=""
USER_LINT_COMMAND=""
USER_TYPECHECK_COMMAND=""
USER_BUILD_COMMAND=""
DRY_RUN=0
PRESERVE_PROGRESS=1
SCALE_THRESHOLD=50
SRC_COUNT=0

PROGRESS_REL_FILES=(
  ".agent/PLAN.md"
  ".agent/REVIEW.md"
  ".agent/TEST.md"
  ".agent/HANDOFF.md"
  ".agent/HISTORY.md"
  ".agent/WIKI.md"
  ".agent/LEARNINGS.md"
)

# Exact legacy continuity exclusions to retire; never remove broad custom rules.
SHARED_STATE_REL_FILES=(
  ".agent/CONTENT-PLAN.md"
  ".agent/CONTENT-HANDOFF.md"
  ".agent/CONTINUITY.md"
  ".agent/OPTIMIZATION.md"
  ".agent/HANDOFF.md"
  ".agent/HISTORY.md"
  ".claude/history.md"
  ".agent/PLAN.md"
  ".agent/CONTEXT.md"
  ".agent/TASKS.md"
  ".agent/REVIEW.md"
  ".agent/TEST.md"
  ".agent/WIKI.md"
  ".agent/LEARNINGS.md"
)

detect_node_pm() {
  local dir="$1"
  local pkg="$dir/package.json"

  if [[ -f "$pkg" ]]; then
    if grep -q '"packageManager"[[:space:]]*:[[:space:]]*"pnpm@' "$pkg"; then
      echo "pnpm"
      return
    fi
    if grep -q '"packageManager"[[:space:]]*:[[:space:]]*"yarn@' "$pkg"; then
      echo "yarn"
      return
    fi
    if grep -q '"packageManager"[[:space:]]*:[[:space:]]*"bun@' "$pkg"; then
      echo "bun"
      return
    fi
  fi

  if [[ -f "$dir/pnpm-lock.yaml" ]]; then
    echo "pnpm"
    return
  fi
  if [[ -f "$dir/yarn.lock" ]]; then
    echo "yarn"
    return
  fi
  if [[ -f "$dir/bun.lockb" || -f "$dir/bun.lock" ]]; then
    echo "bun"
    return
  fi

  echo "npm"
}

detect_defaults() {
  local dir="$1"

  if [[ -f "$dir/package.json" ]]; then
    local pm
    pm="$(detect_node_pm "$dir")"
    DETECTED_STACK="node"
    case "$pm" in
      yarn)
        PRIMARY_COMMAND="yarn dev"
        TEST_COMMAND="yarn test"
        LINT_COMMAND="yarn lint"
        TYPECHECK_COMMAND="yarn typecheck"
        BUILD_COMMAND="yarn build"
        ;;
      bun)
        PRIMARY_COMMAND="bun run dev"
        TEST_COMMAND="bun test"
        LINT_COMMAND="bun run lint"
        TYPECHECK_COMMAND="bun run typecheck"
        BUILD_COMMAND="bun run build"
        ;;
      *)
        PRIMARY_COMMAND="${pm} run dev"
        TEST_COMMAND="${pm} test"
        LINT_COMMAND="${pm} run lint"
        TYPECHECK_COMMAND="${pm} run typecheck"
        BUILD_COMMAND="${pm} run build"
        ;;
    esac
    return
  fi

  if [[ -f "$dir/pyproject.toml" || -f "$dir/requirements.txt" || -f "$dir/requirements-dev.txt" || -f "$dir/Pipfile" ]]; then
    DETECTED_STACK="python"
    PRIMARY_COMMAND="UNCONFIRMED"
    TEST_COMMAND="pytest -q"
    LINT_COMMAND="ruff check ."
    TYPECHECK_COMMAND="mypy ."
    BUILD_COMMAND="python -m build"
    return
  fi

  if [[ -f "$dir/go.mod" ]]; then
    DETECTED_STACK="go"
    PRIMARY_COMMAND="go run ."
    TEST_COMMAND="go test ./..."
    LINT_COMMAND="golangci-lint run"
    TYPECHECK_COMMAND="go vet ./..."
    BUILD_COMMAND="go build ./..."
    return
  fi

  if [[ -f "$dir/Cargo.toml" ]]; then
    DETECTED_STACK="rust"
    PRIMARY_COMMAND="cargo run"
    TEST_COMMAND="cargo test"
    LINT_COMMAND="cargo clippy --all-targets --all-features -- -D warnings"
    TYPECHECK_COMMAND="cargo check --all-targets --all-features"
    BUILD_COMMAND="cargo build"
    return
  fi
}

is_progress_rel_file() {
  local rel="$1"
  for progress_rel in "${PROGRESS_REL_FILES[@]}"; do
    if [[ "$rel" == "$progress_rel" ]]; then
      return 0
    fi
  done
  return 1
}

require_option_value() {
  local option_name="$1"
  local option_value="${2:-}"
  if [[ -z "${option_value// }" || "$option_value" == --* ]]; then
    echo "BLOCKED: missing value for $option_name"
    usage
    exit 1
  fi
}

# Count source files in the target repo to decide whether to recommend Tier 2
# Scale mode (Graphify). Uses the same extension set + threshold as the
# SessionStart scale nudge in scripts/guardrails/git-status.sh. Best-effort.
assess_codebase_size() {
  local dir="$1"
  local code_re='\.(py|js|jsx|ts|tsx|go|rs|java|rb|php|c|cc|cpp|cxx|h|hpp|cs|swift|kt|scala|m|mm|sh)$'
  if git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    SRC_COUNT=$(git -C "$dir" ls-files 2>/dev/null | grep -cE "$code_re" || true)
  else
    SRC_COUNT=$(find "$dir" -type f 2>/dev/null \
      | grep -vE '/(\.git|node_modules|dist|build|vendor|\.venv|venv|target)/' \
      | grep -cE "$code_re" || true)
  fi
  SRC_COUNT=${SRC_COUNT:-0}
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      require_option_value "$1" "${2:-}"
      PROJECT_NAME="$2"
      shift 2
      ;;
    --owner)
      require_option_value "$1" "${2:-}"
      TEAM_OR_OWNER="$2"
      shift 2
      ;;
    --primary)
      require_option_value "$1" "${2:-}"
      USER_PRIMARY_COMMAND="$2"
      shift 2
      ;;
    --test)
      require_option_value "$1" "${2:-}"
      USER_TEST_COMMAND="$2"
      shift 2
      ;;
    --lint)
      require_option_value "$1" "${2:-}"
      USER_LINT_COMMAND="$2"
      shift 2
      ;;
    --typecheck)
      require_option_value "$1" "${2:-}"
      USER_TYPECHECK_COMMAND="$2"
      shift 2
      ;;
    --build)
      require_option_value "$1" "${2:-}"
      USER_BUILD_COMMAND="$2"
      shift 2
      ;;
    --preserve-progress)
      PRESERVE_PROGRESS=1
      shift
      ;;
    --adopt)
      PRESERVE_PROGRESS=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "BLOCKED: unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

# Infer commands to reduce setup friction.
detect_defaults "$TARGET_DIR"

# Assess codebase size to decide whether to recommend Tier 2 Scale mode.
assess_codebase_size "$TARGET_DIR"

# Explicit CLI flags always win.
if [[ -n "${USER_PRIMARY_COMMAND// }" ]]; then
  PRIMARY_COMMAND="$USER_PRIMARY_COMMAND"
fi
if [[ -n "${USER_TEST_COMMAND// }" ]]; then
  TEST_COMMAND="$USER_TEST_COMMAND"
fi
if [[ -n "${USER_LINT_COMMAND// }" ]]; then
  LINT_COMMAND="$USER_LINT_COMMAND"
fi
if [[ -n "${USER_TYPECHECK_COMMAND// }" ]]; then
  TYPECHECK_COMMAND="$USER_TYPECHECK_COMMAND"
fi
if [[ -n "${USER_BUILD_COMMAND// }" ]]; then
  BUILD_COMMAND="$USER_BUILD_COMMAND"
fi

if [[ -z "${PRIMARY_COMMAND// }" ]]; then PRIMARY_COMMAND="UNCONFIRMED"; fi
if [[ -z "${TEST_COMMAND// }" ]]; then TEST_COMMAND="UNCONFIRMED"; fi
if [[ -z "${LINT_COMMAND// }" ]]; then LINT_COMMAND="UNCONFIRMED"; fi
if [[ -z "${TYPECHECK_COMMAND// }" ]]; then TYPECHECK_COMMAND="UNCONFIRMED"; fi
if [[ -z "${BUILD_COMMAND// }" ]]; then BUILD_COMMAND="UNCONFIRMED"; fi

assert_local_write_path() {
  local current="$1"
  while [[ "$current" != "$TARGET_DIR" ]]; do
    if [[ -L "$current" ]]; then
      echo "BLOCKED: refusing to write through a symlink: $current"
      exit 1
    fi
    current="$(dirname "$current")"
  done
}

for path in "$TARGET_DIR/.agent" "$TARGET_DIR/.agents" "$TARGET_DIR/.claude" "$TARGET_DIR/docs" "$TARGET_DIR/.gitignore"; do
  assert_local_write_path "$path"
done

LAST_COPY_STATUS=0

copy_with_backup() {
  local src="$1"
  local dst="$2"
  local rel="$3"

  LAST_COPY_STATUS=0
  assert_local_write_path "$dst"

  if [[ ! -f "$src" ]]; then
    echo "BLOCKED: source file missing: $src"
    exit 1
  fi

  if [[ "$DRY_RUN" -eq 0 ]]; then mkdir -p "$(dirname "$dst")"; fi

  if [[ -e "$dst" ]] && is_progress_rel_file "$rel"; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "DRY_RUN preserve: $dst (existing progress file)"
    else
      echo "Preserved: $dst (existing progress file)"
    fi
    return 0
  fi

  if [[ -e "$dst" ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "DRY_RUN backup: $dst -> ${dst}.bak.${TS}"
    else
      cp "$dst" "${dst}.bak.${TS}"
      echo "Backed up: $dst -> ${dst}.bak.${TS}"
    fi
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY_RUN copy: $src -> $dst"
  else
    cp "$src" "$dst"
    echo "Copied: $src -> $dst"
  fi

  LAST_COPY_STATUS=1
}

ensure_state_ignore_policy() {
  local gitignore="$TARGET_DIR/.gitignore"
  [[ -f "$gitignore" ]] || return 0
  local line rel remove tmp
  local old_header="# Local agent continuity files (keep local; do not commit)"
  local newer_header="# Local agent working state; HANDOFF.md is shared with the team"
  if [[ "$DRY_RUN" -eq 0 ]]; then tmp="$(mktemp "${gitignore}.tmp.XXXXXX")"; fi
  while IFS= read -r line || [[ -n "$line" ]]; do
    remove=0
    if [[ "$line" == "$old_header" || "$line" == "$newer_header" ]]; then remove=1; fi
    for rel in "${SHARED_STATE_REL_FILES[@]}"; do
      if [[ "$line" == "$rel" || "$line" == "/$rel" ]]; then remove=1; fi
    done
    if [[ "$remove" -eq 1 ]]; then
      echo "Remove obsolete continuity ignore rule: $line"
    elif [[ "$DRY_RUN" -eq 0 ]]; then
      printf '%s\n' "$line" >>"$tmp"
    fi
  done <"$gitignore"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    if cmp -s "$tmp" "$gitignore"; then
      rm "$tmp"
    else
      cp "$gitignore" "${gitignore}.bak.${TS}"
      mv "$tmp" "$gitignore"
    fi
  fi
}

warn_if_handoff_ignored() {
  if ! git -C "$TARGET_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 0
  fi

  local rel
  for rel in "${SHARED_STATE_REL_FILES[@]}"; do
    if git -C "$TARGET_DIR" check-ignore -q "$rel"; then
      echo "WARNING: $rel is still ignored by a broader custom rule."
      echo "Review $TARGET_DIR/.gitignore and narrow only the relevant rule after checking sensitive content."
    fi
  done
}

replace_placeholders() {
  local file="$1"
  PROJECT_NAME="$PROJECT_NAME" \
  TEAM_OR_OWNER="$TEAM_OR_OWNER" \
  PRIMARY_COMMAND="$PRIMARY_COMMAND" \
  TEST_COMMAND="$TEST_COMMAND" \
  LINT_COMMAND="$LINT_COMMAND" \
  TYPECHECK_COMMAND="$TYPECHECK_COMMAND" \
  BUILD_COMMAND="$BUILD_COMMAND" \
  perl -0pi -e 's/<PROJECT_NAME>/$ENV{"PROJECT_NAME"}/g; s/<TEAM_OR_OWNER>/$ENV{"TEAM_OR_OWNER"}/g; s/<PRIMARY_COMMAND>/$ENV{"PRIMARY_COMMAND"}/g; s/<TEST_COMMAND>/$ENV{"TEST_COMMAND"}/g; s/<LINT_COMMAND>/$ENV{"LINT_COMMAND"}/g; s/<TYPECHECK_COMMAND>/$ENV{"TYPECHECK_COMMAND"}/g; s/<BUILD_COMMAND>/$ENV{"BUILD_COMMAND"}/g' "$file"
}

TEST_FILE_PREEXISTED=0
if [[ -e "$TARGET_DIR/.agent/TEST.md" ]]; then
  TEST_FILE_PREEXISTED=1
fi
TEST_FILE_WAS_COPIED=0

copy_with_backup "$PACK_ROOT/AGENTS.md" "$TARGET_DIR/AGENTS.md" "AGENTS.md"
copy_with_backup "$PACK_ROOT/CLAUDE.md" "$TARGET_DIR/CLAUDE.md" "CLAUDE.md"
copy_with_backup "$PACK_ROOT/docs/roles/README.md" "$TARGET_DIR/docs/roles/README.md" "docs/roles/README.md"
copy_with_backup "$PACK_ROOT/docs/roles/product-strategist.md" "$TARGET_DIR/docs/roles/product-strategist.md" "docs/roles/product-strategist.md"
copy_with_backup "$PACK_ROOT/docs/roles/engineering-planner.md" "$TARGET_DIR/docs/roles/engineering-planner.md" "docs/roles/engineering-planner.md"
copy_with_backup "$PACK_ROOT/docs/roles/reviewer.md" "$TARGET_DIR/docs/roles/reviewer.md" "docs/roles/reviewer.md"
copy_with_backup "$PACK_ROOT/docs/roles/security-reviewer.md" "$TARGET_DIR/docs/roles/security-reviewer.md" "docs/roles/security-reviewer.md"
copy_with_backup "$PACK_ROOT/docs/roles/qa-validator.md" "$TARGET_DIR/docs/roles/qa-validator.md" "docs/roles/qa-validator.md"
copy_with_backup "$PACK_ROOT/docs/roles/docs-releaser.md" "$TARGET_DIR/docs/roles/docs-releaser.md" "docs/roles/docs-releaser.md"
copy_with_backup "$PACK_ROOT/docs/vendor/README.md" "$TARGET_DIR/docs/vendor/README.md" "docs/vendor/README.md"
copy_with_backup "$PACK_ROOT/docs/vendor/supabase.md" "$TARGET_DIR/docs/vendor/supabase.md" "docs/vendor/supabase.md"
copy_with_backup "$PACK_ROOT/docs/workflows/evals.md" "$TARGET_DIR/docs/workflows/evals.md" "docs/workflows/evals.md"
copy_with_backup "$PACK_ROOT/docs/workflows/contracts.md" "$TARGET_DIR/docs/workflows/contracts.md" "docs/workflows/contracts.md"
copy_with_backup "$PACK_ROOT/docs/workflows/wiki.md" "$TARGET_DIR/docs/workflows/wiki.md" "docs/workflows/wiki.md"
copy_with_backup "$PACK_ROOT/docs/workflows/graphify.md" "$TARGET_DIR/docs/workflows/graphify.md" "docs/workflows/graphify.md"
copy_with_backup "$PACK_ROOT/docs/workflows/optimization.md" "$TARGET_DIR/docs/workflows/optimization.md" "docs/workflows/optimization.md"
copy_with_backup "$PACK_ROOT/docs/workflows/token-management.md" "$TARGET_DIR/docs/workflows/token-management.md" "docs/workflows/token-management.md"
copy_with_backup "$PACK_ROOT/docs/glossary.md" "$TARGET_DIR/docs/glossary.md" "docs/glossary.md"
copy_with_backup "$PACK_ROOT/.agent/PLAN.md" "$TARGET_DIR/.agent/PLAN.md" ".agent/PLAN.md"
copy_with_backup "$PACK_ROOT/.agent/REVIEW.md" "$TARGET_DIR/.agent/REVIEW.md" ".agent/REVIEW.md"
copy_with_backup "$PACK_ROOT/.agent/TEST.md" "$TARGET_DIR/.agent/TEST.md" ".agent/TEST.md"
TEST_FILE_WAS_COPIED="$LAST_COPY_STATUS"
copy_with_backup "$PACK_ROOT/.agent/HANDOFF.md" "$TARGET_DIR/.agent/HANDOFF.md" ".agent/HANDOFF.md"
copy_with_backup "$PACK_ROOT/.agent/HISTORY.md" "$TARGET_DIR/.agent/HISTORY.md" ".agent/HISTORY.md"
copy_with_backup "$PACK_ROOT/.agent/WIKI.md" "$TARGET_DIR/.agent/WIKI.md" ".agent/WIKI.md"
copy_with_backup "$PACK_ROOT/.agent/LEARNINGS.md" "$TARGET_DIR/.agent/LEARNINGS.md" ".agent/LEARNINGS.md"
copy_with_backup "$PACK_ROOT/.agent/integrations/README.md" "$TARGET_DIR/.agent/integrations/README.md" ".agent/integrations/README.md"
copy_with_backup "$PACK_ROOT/.agent/integrations/run-checkpoint.sh" "$TARGET_DIR/.agent/integrations/run-checkpoint.sh" ".agent/integrations/run-checkpoint.sh"
copy_with_backup "$REPO_ROOT/skills/closing-sprint-and-syncing-state/SKILL.md" "$TARGET_DIR/.claude/skills/closing-sprint-and-syncing-state/SKILL.md" ".claude/skills/closing-sprint-and-syncing-state/SKILL.md"
copy_with_backup "$REPO_ROOT/skills/running-novice-safe-git-cycle/SKILL.md" "$TARGET_DIR/.claude/skills/running-novice-safe-git-cycle/SKILL.md" ".claude/skills/running-novice-safe-git-cycle/SKILL.md"
copy_with_backup "$REPO_ROOT/skills/applying-simplicity-ladder/SKILL.md" "$TARGET_DIR/.claude/skills/applying-simplicity-ladder/SKILL.md" ".claude/skills/applying-simplicity-ladder/SKILL.md"
copy_with_backup "$REPO_ROOT/skills/scaling-up-with-graphify/SKILL.md" "$TARGET_DIR/.claude/skills/scaling-up-with-graphify/SKILL.md" ".claude/skills/scaling-up-with-graphify/SKILL.md"
for skill in closing-sprint-and-syncing-state running-novice-safe-git-cycle applying-simplicity-ladder scaling-up-with-graphify; do
  copy_with_backup "$REPO_ROOT/skills/$skill/SKILL.md" "$TARGET_DIR/.agents/skills/$skill/SKILL.md" ".agents/skills/$skill/SKILL.md"
done
for skill in possibnow-scale possibnow-guardrails possibnow-optimize; do
  copy_with_backup "$REPO_ROOT/.agents/skills/$skill/SKILL.md" "$TARGET_DIR/.agents/skills/$skill/SKILL.md" ".agents/skills/$skill/SKILL.md"
done
ensure_state_ignore_policy

if [[ "$DRY_RUN" -eq 0 ]]; then
  replace_placeholders "$TARGET_DIR/AGENTS.md"
  replace_placeholders "$TARGET_DIR/CLAUDE.md"
  if [[ "$PRESERVE_PROGRESS" -eq 0 || "$TEST_FILE_PREEXISTED" -eq 0 || "$TEST_FILE_WAS_COPIED" -eq 1 ]]; then
    replace_placeholders "$TARGET_DIR/.agent/TEST.md"
  fi
fi

echo ""
echo "DONE: project files installed into $TARGET_DIR"
echo "Resolved values:"
echo "  PRESERVE_PROGRESS=$PRESERVE_PROGRESS"
echo "  DETECTED_STACK=$DETECTED_STACK"
echo "  PROJECT_NAME=$PROJECT_NAME"
echo "  TEAM_OR_OWNER=$TEAM_OR_OWNER"
echo "  PRIMARY_COMMAND=$PRIMARY_COMMAND"
echo "  TEST_COMMAND=$TEST_COMMAND"
echo "  LINT_COMMAND=$LINT_COMMAND"
echo "  TYPECHECK_COMMAND=$TYPECHECK_COMMAND"
echo "  BUILD_COMMAND=$BUILD_COMMAND"
echo "  SOURCE_FILE_COUNT=$SRC_COUNT"
warn_if_handoff_ignored

if [[ "$SRC_COUNT" -gt "$SCALE_THRESHOLD" ]]; then
  echo ""
  echo "NOTE: large codebase detected ($SRC_COUNT source files, threshold $SCALE_THRESHOLD)."
  echo "  This looks like an existing/large repo. Turn on Tier 2 'Scale mode' so the agent"
  echo "  queries an index instead of re-reading files every session:"
  echo "    - In Claude Code, run: /possibnow-dev-harness:scale"
  echo "    - Reference: docs/workflows/graphify.md and docs/workflows/token-management.md"
  echo "  (The SessionStart hook will also remind you until Scale mode is on.)"
fi

if [[ "$PRIMARY_COMMAND" == "UNCONFIRMED" || "$TEST_COMMAND" == "UNCONFIRMED" || "$LINT_COMMAND" == "UNCONFIRMED" || "$TYPECHECK_COMMAND" == "UNCONFIRMED" || "$BUILD_COMMAND" == "UNCONFIRMED" ]]; then
  echo ""
  echo "WARNING: one or more commands are UNCONFIRMED."
  echo "Why this happens:"
  echo "  - The installer infers commands by detecting project signals (for example: package.json, pyproject.toml, go.mod, Cargo.toml, lockfiles)."
  echo "  - No supported signals were detected, so safe defaults remain UNCONFIRMED (common in a brand-new/empty repo)."
  echo "How to fix:"
  echo "  - Initialize your project (add the relevant config files) and re-run this installer, OR"
  echo "  - Re-run with explicit overrides: --primary/--test/--lint/--typecheck/--build, OR"
  echo "  - Edit Commands in: $TARGET_DIR/.agent/TEST.md and $TARGET_DIR/CLAUDE.md"
fi
