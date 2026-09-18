---
name: running-novice-safe-git-cycle
description: Review scope, validate, and deliver code plus sanitized current and historical continuity through the authorized Git workflow.
metadata:
  version: 2.0.0
---

# Running Novice-Safe Git Cycle

1. Inspect status and diff to isolate the requested work and preserve unrelated changes.
2. Run relevant checks; record actual receipts and unresolved failures.
3. Follow `docs/workflows/contracts.md` to archive the old handoff in HISTORY before refreshing the current HANDOFF. Update related plan, context, tasks, test/review summaries, learnings, wiki, content continuity, and existing project history when relevant.
4. Review the exact candidate files for secrets and raw sensitive data. Stage explicit reviewed paths, including all changed continuity and archives. Do not force-add ignored directories, credentials, logs, or caches.
5. Make a focused commit; push and complete the authorized PR/merge workflow. Verify code and continuity on remote main before claiming delivery. If approval or checks block merging, keep that state explicit.

Do not exclude project continuity under an obsolete local-only rule, overwrite another contributor's edits, discard historical handoffs, or claim unrun checks passed. The command guard covers common direct Git commands, not every shell wrapper; inspect the staged diff yourself.
