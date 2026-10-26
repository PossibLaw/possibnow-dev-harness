# Published release verification — v4.3.1

Published: 2026-10-26T18:15:01Z (GitHub Release, not draft/prerelease; tag and release created by Sal).
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.3.1
Source commit: a64b505dda65894ab103b59b7177b9a68dc7a800 (merge of PR #37 on main).
Annotated tag v4.3.1 (object db98719) peeled to that commit.
PRs since 4.3.0: #33 (4.3.0 receipt), #34 (dispatcher paths and owner), #35 (tilde-expanded Orca selector, Orca JSON error in the report), #36 (`auto-<n>` branches count as autonomous), #37 (caps: closed issue frees the slot, repos matched by Orca `repoId`; release cut).

## Public smoke

Run on October 26, 2026 against a disposable customized Git repository (own CLAUDE.md and .agent/HANDOFF.md, one commit):

```bash
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/v4.3.1/scripts/bootstrap-project.sh | DEV_HARNESS_REF=v4.3.1 bash -s -- . --adopt
```

- Bootstrap script SHA-256 at the tag: 64998defd09110142fc0777a71c59986cf24a2456b0a1d0f10d5b9888c2cf942 (identical to the tagged file).
- Dry run: 104 files would be created; zero target changes.
- Real run: 104 new files, 1 migration pending (the customized CLAUDE.md, preserved byte for byte; HANDOFF preserved).
- `.harness/releases/4.3.1/VERSION.json`: version 4.3.1, commit a64b505…, source_dirty false.
- Rerun: 0 new files, no churn.
- No real installed project was modified.

Local verification before the cut: `uvx --with pytest pytest -q` 321 passed; `scripts/verify-pack.sh` DONE; CI `verify` passed on PR #37.

## Follow-ups

- Marketplace entry 4.3.1: PossibLaw/PossibLaw-Plugins PR #10; after merge, `claude plugin update possibnow-dev-harness@possiblaw-plugins` on Sal's Mac.
- Codex guardrails on Sal's Mac refreshed by `scripts/install_codex_guardrails.py` (config.toml unchanged; whether Codex asks to re-trust the changed scripts is UNCONFIRMED).
- Customized installed projects still need their own reviewed migration (unchanged from 4.2.1).
