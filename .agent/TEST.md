---
contract_version: 1
artifact_type: test
status: VALIDATED
depends_on: [.agent/PLAN.md]
produces: [test_receipts, limitations]
feeds_into: [.agent/REVIEW.md, .agent/HANDOFF.md]
memory:
  include_in_memory: true
  tags: [test]
---

# 4.2.0 Validation receipts

Baseline main 4f43649: `./scripts/verify-pack.sh` passed, 172 tests.
Failing-before: 16 new entry/update checks failed on original overwrite behavior,
backup churn, line limits, missing current policies, unsafe nested destinations,
and missing rollback/validation helpers. Five checkpoint tests failed before the
preservation helper existed. Additional red checks reproduced conflicting archive
IDs and automatically discoverable nested root candidates.

Passing-after: `./scripts/verify-pack.sh`: 209 passed, DONE. Existing guardrail
scripts, hooks, and test files are unchanged. `claude plugin validate .` passed.
The three modified skill files passed quick_validate.py. `git diff --check` passed.

| Eval | Evidence |
| --- | --- |
| E1-E2 | Fresh install routes and generated roots; 150/151 LF/CRLF with/without final newline; excessive rendered values fail before writes |
| E3 | Required delivery/security/content/checkpoint/learning routes and canonical homes remain reachable; detailed TEST/REVIEW checklists retained |
| E4 | Old 4f43649 installer fixture plus customized roots/content routes/native settings/continuity/unrelated bytes all preserved |
| E5 | Dry-run/repeat snapshots unchanged; differing roots reported PENDING; snapshot tampering and unsafe paths refused |
| E6 | Exact CRLF/unterminated archive bytes/hash/ID/time; dedup; corruption, conflicting ID, failed archive, changed HANDOFF, missing current sections refused |
| E7 | Advisory learning-policy checks; OFF/CAPTURE/APPLY checklist runs add/promote nothing and make no writes; candidates/adopted records separate |
| E8 | No eager root imports or shipped rules/memory chain; snapshot roots/skills have non-discoverable candidate suffixes |
| E9 | All existing Claude guardrail regression tests unchanged and green; client integration claims reviewed against mechanisms/docs |
| E10 | Local tagged repository fixture: default/explicit v4.2.0 bootstrap selects release commit over newer branch HEAD; reports correct version/commit and clean source |

Publication smoke from the real remote tag is a release gate, to be recorded after
publication before handing out the final command. Installer rollback was exercised
against a customized fixture; changed-file and path-traversal refusals delete nothing.
Nested symlink/non-directory preflight makes no target writes. Shell helper remains executable.

## Measurements (not tokens or money)

| Entry | Before lines / words / bytes | After lines / words / bytes |
| --- | --- | --- |
| AGENTS.md | 178 / 1890 / 13582 | 65 / 487 / 3740 |
| CLAUDE.md | 202 / 2003 / 14446 | 65 / 487 / 3732 |

Optional global templates remain unchanged: 70 and 77 lines; their size checks pass.
Automatic startup inspection is static: the shipped roots expand to themselves,
with no eager imports. Existing client globals, memories, plugins, nested overrides,
and live client compliance are UNCONFIRMED. No paid model eval or live project
migration ran. Optimize semantic check/apply remains an advisory agent workflow;
helper tests do not prove model decisions or semantic retention.

Prior receipts preserved verbatim: archives/pre-4.2-TEST.md.
