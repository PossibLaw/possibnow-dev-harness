# Checkpoint helpers

`run-checkpoint.sh` is an advisory checklist printer. It makes no writes, does not
enable learning, and does not load histories or run a delivery pipeline for you.

`checkpoint.py TARGET --candidate PATH --expected-sha256 HASH --reviewed` archives
exact prior HANDOFF bytes, verifies preservation, checks for intervening edits,
and replaces the current handoff with a separately prepared reviewed candidate.
Python 3 standard library only. Follow `docs/workflows/contracts.md` first.
The candidate must have Status, Unresolved work, Active constraints, Evidence,
and Next actions headings. Completeness and sanitization require human/agent review.

Read SHA-256 with `shasum -a 256 .agent/HANDOFF.md` before preparing the proposal.
Pass that original hash when applying; do not recalculate it merely to bypass a
changed-file rejection. Coordinate concurrent editors; the helper lock covers
other helper runs, not arbitrary applications. Do not commit transient locks or
Python bytecode. Archives and sanitized continuity are version-controlled.
