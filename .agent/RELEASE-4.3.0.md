# Published release verification — v4.3.0

Published: 2026-10-24T22:00:14Z (GitHub Release, not draft/prerelease).
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.3.0
Source commit: 8275b16c8b044e03a041ae10942585b1d9fd550d (merge of PR #32 on main).
Annotated tag v4.3.0 (object 21706ecf) peeled to that commit.
PRs since 4.2.1: #14 (git guardrail gaps, Pocock skills, Codex hooks), #15, #16, #17, #18, #19, #20 (Program 1: Orca setup, feeder step, issue sync, work router), #21 (board step), #26 (autonomy guardrails and dispatcher), #27 (TickTick mirror), #30, #31, #32 (release cut).

## Public smoke

Run on October 24, 2026 against a disposable customized Git repository (own CLAUDE.md and .agent/HANDOFF.md, one commit):

```bash
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/v4.3.0/scripts/bootstrap-project.sh | DEV_HARNESS_REF=v4.3.0 bash -s -- . --adopt
```

- Bootstrap script SHA-256 at the tag: 2aae63c172e30b78d015f2f38a37194ab84c9a9ceff969b546771aa27c6b8396
- Dry run: 104 files would be created; zero target changes.
- Real run: 104 new files, 1 migration pending (the customized CLAUDE.md, preserved byte for byte), existing files preserved.
- `.harness/releases/4.3.0/VERSION.json`: version 4.3.0, commit 8275b16c…, source_dirty false.
- Rerun: 0 new files, no churn.
- Delivered skills include routing-work-to-a-repo, splitting-work-into-tickets and running-a-retro.
- No real installed project was modified.

Local verification before the cut: `uvx --with pytest pytest -q` 311 passed; `scripts/verify-pack.sh` DONE.

## Follow-ups

- Marketplace entry 4.3.0: PossibLaw/PossibLaw-Plugins PR opened the same day; after merge, `claude plugin update possibnow-dev-harness@possiblaw-plugins` on Sal's Mac (cached 4.1.0).
- Codex guardrails on Sal's Mac were refreshed by `scripts/install_codex_guardrails.py`; the 4.3.0 installer ships `autonomy.py`.
- Customized installed projects still need their own reviewed migration (unchanged from 4.2.1).
