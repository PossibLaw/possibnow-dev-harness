# Token Management

Optimize cost per accepted task, including attempts, tools, verification, and
human correction. Token counts alone do not measure quality or a subscription bill.

- Keep HANDOFF current-only; preserve exact previous checkpoints in HISTORY and
  retrieve a specific historical entry when needed. Both remain committed.
- Load task-relevant instructions and sources on demand. Start with targeted
  reads, then expand when dependencies or complete evidence require it.
- Keep stable instruction prefixes stable, but update facts when they change.
  Caching discounts and write charges are model/provider-specific; use actual
  usage categories and rates rather than a universal savings percentage.
- Prefer existing code and deterministic tools where they satisfy the task.
- Treat Graphify/indexing and multi-agent execution as measured candidates, not
  automatic savings. Include indexing, all workers, and synthesis in the cost.
- Keep quota snapshots, estimates, and billed costs separate. Unknown cost is
  UNCONFIRMED, not zero. Overlapping usage characteristics cannot be added.
- For unrelated work, checkpoint before a fresh session. For related work,
  measure continuation versus compaction/restart, including cache rebuilds.

Run `/possibnow-dev-harness:optimize` in Claude Code, or follow
`docs/workflows/optimization.md` in another host, for a project-specific proposal.
Preserve the incumbent model and quality requirements until a comparison supports
changing them. No fixed context-percentage cutoff or universal savings claim is
part of this policy.
