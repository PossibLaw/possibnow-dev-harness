# Release v4.4.0 — HANDOFF is a pointer, not a log

Status: version and pins prepared (branch `release/4.4.0`); not yet tagged or published.
Payload: PR #86 (HANDOFF size check, commit guard, one-line entry rule, compaction).
Companion private change: agent-tasks PR #7 (dispatch prompt), merged 2026-11-26.

## Pre-tag validation
- R440-1: installer tests pointed at 4.4.0 failed first (8 failed, 12 passed), then
  passed after the pin bump (20 passed).
- R440-2: full suite and verify-pack results are recorded in TEST.md.

## Publication (pending Sal)
Tag the release PR merge commit, publish the GitHub Release, then record here: tag
object, peeled commit, public bootstrap smoke, marketplace PR, plugin updates on both
machines, Codex guard refresh.

## Migration note for installs
Run one HANDOFF compaction with a carry-forward list, then the check keeps it small.
Repositories whose tooling needs a heading set `required_headings` in
`.agent/handoff-limits.json` (Trazomo: `## Session Timeline`).
