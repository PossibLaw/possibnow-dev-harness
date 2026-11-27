# Published release verification — v4.4.0

Published: 2026-11-27T03:33:28Z, normal GitHub Release (not draft/prerelease),
tagged and published by Sal after the release PR merge.
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.4.0
Annotated tag object: `8cabfb387fa58add5535ab244d0ab19464dca795`.
Peeled commit: `9aa3fa718bf66d61e8f58c572b5690e26ebf9dcb`, PR #87 merge.
Payload: PR #86, HANDOFF is a pointer, not a log (size check, commit guard,
one-line entry rule, compaction). Companion private change: agent-tasks PR #7.
Marketplace: PossibLaw/PossibLaw-Plugins PR #18 merged; entry is 4.4.0.

## Pre-tag validation
- R440-1: installer tests pointed at 4.4.0 failed first (8 failed, 12 passed), then
  passed after the pin bump (20 passed).
- R440-2: 566 passed; verify-pack DONE; `claude plugin validate .` passed; CI
  `verify` passed on PRs #86 and #87.

## Public bootstrap smoke (R440-3)
Downloaded the v4.4.0 bootstrap; byte-identical to the tag. SHA-256:
`c83ccabd7f716f4c719e7be05d448aac2be9d9fd583ba5629814a05e72166fcd`.
Installed into a disposable Git repository with customized AGENTS, CLAUDE, HANDOFF
and .gitignore: all four preserved byte for byte; 109 created files, 2 pending
customized entries; VERSION.json reports 4.4.0, the peeled commit above, and
source_dirty false; `.agent/integrations/handoff_size.py` installed and passes on the
fixture. A repeat installation changed no bytes or mtimes (114 files).

## Installed rollout (first machine)
- One shared plugin registry (both Orca profiles link `plugins/` to `~/.claude/plugins`).
  The three live registrations (user, project at the home folder, Trazomo local) now
  report 4.4.0. Registrations for deleted worktrees were left untouched.
- Installed plugin manifest, hook manifest, the four guard scripts, `handoff_size.py`
  and `checkpoint.py` match the tag byte for byte. The installed Bash hook, run through
  its manifest command, refuses a commit of a 40-line Status (exit 2, limit named) and
  allows a short one (exit 0); it wrote no bytecode beside the size check.
- Codex guard refreshed from a clean detached checkout of the tag: the four guards and
  the new `handoff_size.py` match the tag. `config.toml` is semantically unchanged
  (one blank line normalized; backup kept beside it); trust records preserved.

## Follow-ups
- Second machine: not reachable from this machine on 2026-11-26 (hostname did not
  resolve). Its plugin update, Codex guard refresh (if installed) and the context-guard
  wording edit remain owed (Sal). UNCONFIRMED until done.
- Restart running Claude sessions to load 4.4.0; Codex: run `/hooks` once if it asks
  to re-trust.
- Trazomo: add `.agent/handoff-limits.json` with `required_headings: ["## Session Timeline"]`.
