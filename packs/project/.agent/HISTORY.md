---
contract_version: 1
artifact_type: history
status: IN_PROGRESS
depends_on: [.agent/HANDOFF.md]
produces: [historical_checkpoints]
feeds_into: [.agent/HANDOFF.md]
memory:
  include_in_memory: false
  tags: [history]
---

# Historical Handoffs

Committed archive of previous HANDOFF checkpoints. Load specific entries only
for a historical question, not at startup. Before replacing HANDOFF, preserve its
exact contents with a checkpoint ID, archive time, and SHA-256 hash; verify that
copy first. Preserve existing historical files and link them here during migration.

New checkpoints go above older ones. Do not put credentials or raw private data
in a shared checkpoint; review and sanitize the source before archiving.
