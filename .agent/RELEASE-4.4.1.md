# Release v4.4.1 — the Bash guard follows `cd` and ignores heredocs

Status: version and pins prepared (branch `release/4.4.1`); not yet tagged or published.
Payload: PR #91 (H-GR86): commit checks follow `cd`/`pushd`; heredoc bodies,
redirections and newline-separated commands are no longer read as pathspecs.

## Pre-tag validation
- R441-1: installer tests pointed at 4.4.1 failed first (8 failed, 12 passed), then
  passed after the pin bump (20 passed).
- R441-2: full suite and verify-pack results are recorded in TEST.md.

## Publication (pending Sal)
Tag the release PR merge commit, publish the GitHub Release, then record here: tag
object, peeled commit, public bootstrap smoke, marketplace PR, plugin updates, Codex
guard refresh (validate-bash.py changed).
