# Published release verification — v4.4.1

Published: 2026-11-27T04:30:09Z, normal GitHub Release (not draft/prerelease),
tagged and published by Sal after the release PR merge.
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.4.1
Annotated tag object: `b6b09b32a122c59ccc7d6b53a6079c9c88c5c886`.
Peeled commit: `865bcf659136e4e2042b392baa27e84fcbf0fa10`, PR #92 merge.
Payload: PR #91 (H-GR86): commit checks follow `cd`/`pushd`; heredoc bodies,
redirections and newline-separated commands are no longer read as pathspecs.
Marketplace: PossibLaw/PossibLaw-Plugins PR #19 merged; entry is 4.4.1.

## Pre-tag validation
- R441-1: installer tests pointed at 4.4.1 failed first (8 failed, 12 passed), then
  passed after the pin bump (20 passed).
- R441-2: 580 passed; verify-pack DONE; `claude plugin validate .` passed; CI
  `verify` passed on PRs #91 and #92.

## Public bootstrap smoke (R441-3)
Downloaded the v4.4.1 bootstrap; byte-identical to the tag. SHA-256:
`e19c53b47f375f3f2159ded1040ca17932b30911449f2656470cb2e4ee9436b9`.
Disposable repository with customized AGENTS, CLAUDE, HANDOFF and .gitignore: all
four preserved byte for byte; 109 created files, 2 pending customized entries;
VERSION.json reports 4.4.1, the peeled commit above, source_dirty false. A repeat
installation changed no bytes or mtimes (114 files).

## Installed rollout (first machine)
- The three live registrations (user, project at the home folder, Trazomo local) report
  4.4.1. Plugin and hook manifests, the four guard scripts, `handoff_size.py` and
  `checkpoint.py` match the tag byte for byte.
- Installed Bash hook, run through its manifest command from a session repository with
  an unstaged HANDOFF edit: the November 25 pattern `cd <other repo> && git add app.py
  && git commit -F - <<'EOF' ... EOF` is allowed (exit 0); `cd <other repo> && git add -A
  && git commit` with a 40-line Status there is refused (exit 2, limit named).
- Codex guards refreshed from a clean detached checkout of the tag; all five copied
  files match the tag; `config.toml` byte-identical (already registered).

## Follow-ups
- Second machine: still unreachable from here; its 4.4.0/4.4.1 plugin update, Codex
  guard refresh (if installed) and context-guard wording edit remain owed (Sal).
- Restart running Claude sessions to load 4.4.1.
