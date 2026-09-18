# Continuity Checkpoint Helper

The helper is committed with the repository. Run `bash .agent/integrations/run-checkpoint.sh . --reason pre-git-cycle` to print the required updates. It is advisory: it never writes state or calls a backend.

Update PLAN, archive and verify the exact previous HANDOFF in HISTORY, and write the current checkpoint. Update learnings only when enabled. Review and commit all related continuity with the work, preserving historical records and keeping secrets/raw runtime state private. See `docs/workflows/contracts.md`.
