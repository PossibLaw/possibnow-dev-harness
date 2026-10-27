# Published release verification — v4.3.4

Published: 2026-10-27T15:34:53Z (GitHub Release, not draft/prerelease; tag and release created by Sal).
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.3.4
Tag: annotated v4.3.4 (object 4ae4bfe) peeled to e1ebb44be682c299719cb33ef927f9ead47b1138, the merge of PR #47, which
carries the 4.3.4 version files, so tagged installs report 4.3.4.
PRs since 4.3.3: #46 (4.3.3 receipt), #47 (worktrees created with no parent, Stop-hook completion notice, version and pins).

## Public smoke

Run on October 27, 2026 against a disposable customized Git repository (own CLAUDE.md and .agent/HANDOFF.md, one commit):

```bash
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/v4.3.4/scripts/bootstrap-project.sh | DEV_HARNESS_REF=v4.3.4 bash -s -- . --adopt
```

- Bootstrap script SHA-256 at the tag: 8c714804abcf3183558fd087d44f66cc583197812b090645dc16441cc92f358a (identical to the tagged file).
- Dry run: 108 files would be created; zero target changes.
- Real run: 108 new files, 1 migration pending (customized CLAUDE.md preserved byte for byte; HANDOFF preserved).
- `.harness/releases/4.3.4/VERSION.json`: version 4.3.4, commit e1ebb44…, source_dirty false.
- Rerun: 0 new files, no churn.

## Installed plugin and live check

Marketplace entry 4.3.4 (PossibLaw/PossibLaw-Plugins PR #13, merged before the tag). `claude plugin update` moved the user
scope and the Trazomo local scope from 4.3.3 to 4.3.4. The installed Stop hook, run once for worktree auto-22, posted the
"Claude Code content update" completion notice to Slack and recorded it in the marker. auto-22 was moved under Trazomo with
`orca worktree set --no-parent`.

Local verification: `uvx --with pytest pytest -q` 368 passed; `scripts/verify-pack.sh` DONE; CI `verify` passed on #47.

## Follow-ups

- First nightly run with the notice and no-parent placement: tonight. Running sessions pick up the hook after a restart.
- The Claude Code content update (Trazomo PR #865) was merged by Sal; its follow-up is Trazomo issue #866.
