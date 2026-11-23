# Published release verification — v4.3.8

Published: 2026-11-23T19:41:36Z, normal GitHub Release (not draft/prerelease),
explicitly authorized by Sal in the release session.
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.3.8
Annotated tag object: `bd087c4eb7f35aaf7f7441655961cdf339cc74fa`.
Peeled commit: `8aa577c455d36040b0485bbeb2c6f6df7b658780`, PR #84 merge.
Payload: PR #83 (#82), ignored shared-continuity diagnostics and migration guidance.
Marketplace: PossibLaw/PossibLaw-Plugins PR #17 merged; entry is 4.3.8.

## Public bootstrap smoke

Downloaded the v4.3.8 bootstrap and compared it byte-for-byte with the tag.
SHA-256: `c88de111df3015b7647ff82b3298f5ab7e78d563faa8cc0b6c779639066847be`.
Installed into a disposable Git repository with customized AGENTS, CLAUDE, HANDOFF
and .gitignore. All four originals were preserved byte-for-byte. Receipt: 107
created files, 2 pending customized entries; VERSION.json reports 4.3.8, the exact
peeled commit above and source_dirty false. Repeat installation changed no bytes
or mtimes. Existing tags and historical receipts were not altered.

## Validation

- Failing first: updated installer expectations, 8 failed / 7 passed on 4.3.7.
- After release pins: all 15 installer cases passed.
- Full verify-pack: 518 passed, 4 Python-version skips; those four installer cases
  passed separately under Python 3.14. All 522 cases covered locally.
- Release PR #84: Verify Harness workflow 45251076506 succeeded.
- Plugin and marketplace manifest validation passed (existing optional-icon warning).
- git diff --check passed; earlier #83 evidence is in TEST/REVIEW.

## Installed rollout

- First machine: four live registrations (user, project and two local scopes) now
  report 4.3.8. One local registration remained stale after the scoped CLI reported
  it current; only that entry's version/cache metadata was corrected after checking
  the installed cache against the tag. The original registry was backed up; no
  enabled state, permissions or unrelated plugin entries changed.
- Second machine: its live user registration is 4.3.8. Deleted-worktree registrations
  on both machines were left untouched; they are not active installations.
- On both machines, plugin manifest, hook manifest and the four guard scripts match
  the tag byte-for-byte. The installed Bash hook, invoked through its actual manifest
  command, blocks ignored REVIEW with the exact rule, permits it after explicit
  staging, and keeps unrelated private notes ignored. Both smokes passed.
- Existing Codex guard installation refreshed from a clean tagged clone. All four
  copied scripts match the tag. Config TOML, hook definitions, unrelated settings
  and trust records are semantically unchanged (formatting was normalized).
  There was no existing Codex guard installation on the second machine.
- Both machines' harness source checkouts were fast-forwarded. Affected client
  continuity migration was reviewed, passed local/CI gates, merged, and delivered
  to both primary checkouts. Formerly ignored originals were backed up privately;
  sanitized historical records are shared; private data exclusions remain intact.
  One private checkout received the verified commits via a Git bundle because its
  GitHub login was unavailable; no credentials were copied or changed.
- Machine-specific paths, inventory and client records stay private.

## Follow-ups

Running Claude sessions need restarting to load the updated plugin. Codex trust
records were preserved; the installer directs the operator to /hooks if review is
requested. No running sessions were interrupted. Customized project-pack migrations
beyond the affected continuity rules remain H-MIG01; plugin updates deliberately do
not overwrite preserved project instructions. Remote private Git authentication
remains an operator follow-up; the requested checkout update itself is complete.
