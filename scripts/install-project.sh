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
  --preserve-progress   Preserve existing files (always the default)
  --adopt               Adopt into an existing/older repo (alias for --preserve-progress).
                        Existing differing files remain pending reviewed migration.
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

require_option_value() {
  local option_name="$1"
  local option_value="${2:-}"
  if [[ -z "${option_value// }" || "$option_value" == --* ]]; then
    echo "BLOCKED: missing value for $option_name"
    usage
    exit 1
  fi
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
      shift
      ;;
    --adopt)
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

# Rendering and all target writes use the conservative shared installer.
export PROJECT_NAME TEAM_OR_OWNER PRIMARY_COMMAND TEST_COMMAND LINT_COMMAND TYPECHECK_COMMAND BUILD_COMMAND DRY_RUN
exec python3 "$SCRIPT_DIR/install_pack.py" "$TARGET_DIR"
