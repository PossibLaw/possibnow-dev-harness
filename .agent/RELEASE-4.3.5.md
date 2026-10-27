# Published release verification — v4.3.5

Published: 2026-10-27T19:45:15Z. This is a GitHub Release, not a draft or prerelease; Sal created the tag and the
release.
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.3.5
Tag: annotated v4.3.5 (object 8a61942), peeled to c5ced839885980c822bf39dee9b5d71a1675928a, the merge of PR #61. That
merge carries the 4.3.5 version files, so tagged installs report 4.3.5.
PRs since 4.3.4:
- #48: the 4.3.4 receipt
- #49: auto-clean of finished autonomous worktrees
- #50: continuity
- #58: the board and the short morning brief, for issue "How I do work"
- #60: the linked issue at session start, for Orca mobile
- #61: version and pins

## Public smoke

Run on October 27, 2026 against a disposable customized Git repository with its own CLAUDE.md and .agent/HANDOFF.md
and one commit:

```bash
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/v4.3.5/scripts/bootstrap-project.sh -o bootstrap.sh
DEV_HARNESS_REF=v4.3.5 bash bootstrap.sh . --adopt
```

- Bootstrap script SHA-256 at the tag: 42db5de01f11fc3e29a37e2d9305b7046ca8da908e76490dfc5de397eb4631f8, identical to
  the tagged file.
- Real run: 108 new files and 1 pending migration. The customized CLAUDE.md was preserved byte for byte, and so was
  the HANDOFF.
- `.harness/releases/4.3.5/VERSION.json`: version 4.3.5, commit c5ced83…, source_dirty false.
- Rerun: 0 new files, no churn.
- The separate dry run from earlier receipts was not repeated.

## Installed plugin and live check

- The marketplace entry is 4.3.5 (PossibLaw/PossibLaw-Plugins PR #14, merged after the tag).
- `claude plugin update` moved the user scope and the Trazomo local scope from 4.3.4 to 4.3.5. The installed
  `hooks/hooks.json` wires `session-issue-link.py`; running sessions pick it up after a restart.
- Codex guard copy: the four copied guardrail files did not change from v4.3.4 to v4.3.5 and already match
  `~/.codex/hooks/possibnow/` byte for byte, so no refresh and no re-trust were needed.
- Board rollout on Sal's machine (details in the private runbook):
  - board fields created and Status options set by Sal;
  - first planner run made 344 changes with 0 failures;
  - Aleph PR #165 merged (planner in the nightly run; TickTick and the long daily posts out);
  - the 06:30 morning job is installed;
  - 143 mirrored TickTick tasks were deleted with 0 failures, and a recount found 0.

Local verification: `uvx --with pytest pytest -q` 434 passed; `scripts/verify-pack.sh` DONE; CI `verify` passed on #61.

## Follow-ups

- First 22:00 run with the board planner tonight, and the first 06:30 morning brief tomorrow. Check both, then close
  issue "How I do work" (#56).
- On mobile, a session in a worktree linked to an issue should get the link; check on the next one Sal opens from his
  phone.
