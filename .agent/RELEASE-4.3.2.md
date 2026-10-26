# Published release verification — v4.3.2

Published: 2026-10-26T18:46:18Z (GitHub Release, not draft/prerelease; tag and release created by Sal).
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.3.2
Source commit: 39413b4740a9caaacc7b0c18fec74745537d80e6 (merge of PR #39 on main).
Annotated tag v4.3.2 (object ac6a860) peeled to that commit.
PRs since 4.3.1: #38 (4.3.1 receipt), #39 (sticky autonomy marker with human takeover; release cut).

## Public smoke

Run on October 26, 2026 against a disposable customized Git repository (own CLAUDE.md and .agent/HANDOFF.md, one commit):

```bash
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/v4.3.2/scripts/bootstrap-project.sh | DEV_HARNESS_REF=v4.3.2 bash -s -- . --adopt
```

- Bootstrap script SHA-256 at the tag: dab2018738b4f10980b491d21430b2b21bea3ed14f0040dd71f802fd571cc656 (identical to the tagged file).
- Dry run: 104 files would be created; zero target changes.
- Real run: 104 new files, 1 migration pending (customized CLAUDE.md preserved byte for byte; HANDOFF preserved).
- `.harness/releases/4.3.2/VERSION.json`: version 4.3.2, commit 39413b4…, source_dirty false.
- Rerun: 0 new files, no churn.
- No real installed project was modified.

## Installed-plugin check

Marketplace entry 4.3.2 (PossibLaw/PossibLaw-Plugins PR #11, merged). `claude plugin update` moved the user scope and
the Trazomo local scope from 4.3.1 to 4.3.2 (commit 39413b4). The installed guard and takeover hook, run against a
disposable marked worktree: merge blocked on `auto-99`, still blocked after switching to `fix/other-work`, still blocked
after the dispatcher's prompt, released to ask-first after a second prompt, with the release notice printed.

Local verification before the cut: `uvx --with pytest pytest -q` 332 passed; `scripts/verify-pack.sh` DONE; CI `verify`
passed on PR #39.

## Follow-ups

- Live observation in an Orca session (hook payload fields and the release notice) happens on the next dispatcher run.
- Codex has no takeover hook; a Codex auto run stays guarded until its marker is removed.
- Customized installed projects still need their own reviewed migration (unchanged from 4.2.1).
