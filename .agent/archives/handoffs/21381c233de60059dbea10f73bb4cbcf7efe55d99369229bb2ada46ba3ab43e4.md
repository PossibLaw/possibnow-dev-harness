---
contract_version: 1
artifact_type: handoff
status: IN_PROGRESS
depends_on: [.agent/PLAN.md, .agent/TEST.md, .agent/REVIEW.md]
produces: [next_actions, historical_checkpoint_link]
feeds_into: []
memory:
  include_in_memory: true
  tags: [handoff]
---

# Current Handoff

Checkpoint: Codex workflow parity, September 18, 2026.

The harness now has four Codex project skills corresponding to its Claude commands: Init, Scale, Guardrails, and Optimize. The project installer places Scale, Guardrails, Optimize, and the four existing workflow skills in `.agents/skills/` of target repos. Init lives in the harness clone, where its bundled installer is available. Codex invokes these with `$name`; Claude retains its namespaced slash commands. The informational Guardrails skill does not enforce Claude hooks in Codex.

Validation: `scripts/verify-pack.sh` passed with 172 tests, including skill delivery and symlinked `.agents` preflight rejection. Four new skills passed `quick_validate.py`; `git diff --check` passed. A live Codex skill invocation and plugin distribution remain UNCONFIRMED.

Next: deliver this change with its PLAN, TEST, REVIEW, HANDOFF, and HISTORY files, then verify remote main. Project owners must update an installed pack to receive the new skills; existing projects are not silently migrated. The v4.1.0 optimization policy and previous release context remain in HISTORY.

The previous HANDOFF is preserved verbatim and hash-verified in HISTORY. Prior recovered continuity remains under `.agent/archives/` as described there.
