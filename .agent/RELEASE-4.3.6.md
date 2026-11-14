# Published release verification — v4.3.6

Published: 2026-11-14T03:14:48Z. This is a GitHub Release, not a draft or prerelease; Sal created the tag and the
release.
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.3.6
Tag: annotated v4.3.6, peeled to a32f9fa7e5d50db9ba4dd6dc2054db71e3209bfe, the merge of PR #75. That merge carries
the 4.3.6 version files, so tagged installs report 4.3.6.
PRs since 4.3.5:
- #66: the dispatcher skips issues with an open PR or a linked Orca worktree (#65)
- #70: issue sync: no mirror for a register row that links its own issue (#69)
- #71, #73: continuity
- #72: config paths may use `$REPOS` (per-machine repository root)
- #74: skill commands use `$REPOS` and `$AGENT_TASKS_DIR`
- #75: version and pins

## Public smoke

Run on November 13, 2026 against a disposable Git repository with its own CLAUDE.md and .agent/HANDOFF.md and one
commit:

```bash
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/v4.3.6/scripts/bootstrap-project.sh -o bootstrap.sh
DEV_HARNESS_REF=v4.3.6 bash bootstrap.sh . --adopt
```

- Bootstrap script SHA-256 at the tag: 41e645573a1b830012d895c8b03056a9b0055a125b29cd737e2f3a34f9a9a910, identical to
  the tagged file.
- Real run: 108 new files and 1 pending migration. The customized CLAUDE.md and HANDOFF were preserved byte for byte.
- `.harness/releases/4.3.6/VERSION.json`: version 4.3.6, commit a32f9fa…, source_dirty false.
- Rerun: 0 changed files.

## Installed plugin and live check

- The marketplace entry is 4.3.6 (PossibLaw/PossibLaw-Plugins PR #15, merged after the tag).
- `claude plugin update` moved the user scope and the Trazomo local scope from 4.3.5 to 4.3.6.
- The operator's second machine had the harness enabled in settings but under a marketplace name it did not have, so
  the plugin never loaded there. The marketplace was re-registered as `possiblaw-plugins` and the harness (4.3.6),
  superpowers and plugin-dev were installed at user scope.
- Codex guard copy: the four copied guardrail files did not change from v4.3.5 to v4.3.6 and match
  `~/.codex/hooks/possibnow/` byte for byte, so no refresh and no re-trust were needed.
- Other local and project installs on the operator's machine still run older versions (4.1.0 to 4.3.5); that is
  TASKS H-MIG01.

Local verification: `uvx --with pytest pytest -q` 470 passed; `scripts/verify-pack.sh` DONE; CI `verify` passed on #74
and #75.

## Follow-ups

- H-MIG01: review and migrate the older installs.
- Running Claude sessions pick up 4.3.6 after a restart.
