---
contract_version: 1
artifact_type: test
status: IN_PROGRESS
depends_on: []
produces: []
feeds_into: []
memory:
  include_in_memory: true
  tags: [test]
---

# 4.1.0 Test Receipts

- Failing-before: new installer/continuity tests plus existing Bash guard suite: 15 failed, 83 passed. Failures covered read-only preview, state preservation, missing workflow/history, and omitted continuity.
- Passing-after: `./scripts/verify-pack.sh`: 172 passed, DONE. Includes guardrail and installer tests; shell verifier checks fresh, legacy, and broad-custom ignore handling.
- `claude plugin validate .`: Validation passed.
- Revised closeout/Git-cycle skills: quick_validate.py passed after installing PyYAML in the isolated test environment.
- `git diff --check`: passed.
- Old root handoff archival: exact-content SHA-256 verification passed before replacement.

No paid model eval, live slash-command conversation, native model change, production API test, or user-project migration ran. E4 is an instruction/pack check, not end-to-end proof of agent decisions.

- Additional failing-before: symlinked-state escape test failed; after write-path rejection was added, the complete suite passed with 172 tests.
