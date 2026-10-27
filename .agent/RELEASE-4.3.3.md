# Published release verification — v4.3.3

Published: 2026-10-26T23:46:01Z (GitHub Release, not draft/prerelease; tag and release created by Sal).
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.3.3
Tag: annotated v4.3.3 (object 76f1af6) peeled to 7cf243d9d9a0aff786960cc721fa808b0bbb5f4a, the merge of PR #44.
Version files: the tag was created before the version bump, so files installed from it report 4.3.2. PR #45 (d11149d)
moved main to 4.3.3; the plugin installs from main and reports 4.3.3. The tag was not moved (release tags are immutable).
PRs since 4.3.2: #40 (4.3.2 receipt), #41 (sync status report, issues started anywhere, weekly worktree line), #42
(dispatcher pagination, named PRs), #43 (content-freshness engine), #44 (nightly triage, TickTick quadrants, team-only
adoption, answering-the-morning-brief skill), #45 (version and pins).

## Public smoke

Run on October 26, 2026 against a disposable customized Git repository (own CLAUDE.md and .agent/HANDOFF.md, one commit):

```bash
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/v4.3.3/scripts/bootstrap-project.sh | DEV_HARNESS_REF=v4.3.3 bash -s -- . --adopt
```

- Bootstrap script SHA-256 at the tag: dab2018738b4f10980b491d21430b2b21bea3ed14f0040dd71f802fd571cc656.
- Dry run: 108 files would be created; zero target changes.
- Real run: 108 new files, 1 migration pending (customized CLAUDE.md preserved byte for byte; HANDOFF preserved).
- `.harness/releases/4.3.2/VERSION.json`: version 4.3.2, commit 7cf243d…, source_dirty false (see Version files above).
- Rerun: 0 new files, no churn.

## Installed plugin

Marketplace entry 4.3.3 (PossibLaw/PossibLaw-Plugins PR #12, merged). `claude plugin update` moved the user scope and the
Trazomo local scope from 4.3.2 to 4.3.3; the cache holds `skills/answering-the-morning-brief`.

Local verification: `uvx --with pytest pytest -q` 361 passed; `scripts/verify-pack.sh` DONE; CI `verify` passed on #44 and #45.

## Follow-ups

- Next release: cut the tag after the version-bump PR merges, so tagged installs report their own version.
- UNCONFIRMED until the first scheduled run: headless `claude -p` authenticating under launchd for the nightly triage.
