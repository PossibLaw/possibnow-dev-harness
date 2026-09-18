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

## Codex workflow parity — September 18, 2026

- Failing-before: `./scripts/verify-pack.sh` reported the four missing Codex skill files.
- Passing-after: `./scripts/verify-pack.sh` passed with 172 tests and verified that a fresh install includes seven Codex skills. `git diff --check` passed. All four new skill files passed `skill-creator/scripts/quick_validate.py`.
- The installer uses the existing safe-copy path, which rejects writes through symlinked destinations. Existing dry-run and preservation fixtures remain green.
- Additional failing-before: the `.agents` symlink fixture found that the installer wrote other files before rejecting that path. Passing-after: preflight now rejects it before any target write.
- Live Codex skill invocation, plugin distribution, and installed-project migration: `UNCONFIRMED` (not exercised).
