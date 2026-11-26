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

# 4.2.1 Validation receipts

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

Publication smoke from the real v4.2.1 tag passed; RELEASE-4.2.1.md records the
verified public command, commit, file preservation, repeat behavior, and rollback. Installer rollback was exercised
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

## v4.2.1 publication gate fix

The actual v4.2.0 curl smoke verified matching bootstrap bytes/version/commit,
customized-state preservation, pending oversized entry, read-only preview, and
repeat byte/mtime stability. Rollback refused a logically equivalent macOS target
root path before deletion. A new alias fixture reproduced that failure before the
fix. Root alias normalization now retains internal-symlink rejection; three extra
regression cases cover both alias/canonical root arguments and an internal symlink.
Final published v4.2.1 smoke remains the release gate.

Patch validation: ./scripts/verify-pack.sh passed with 212 tests.

E10 final: public v4.2.1 bootstrap/pack/rollback smoke passed; GitHub Release published with its receipt.


## Issue 82 shared-continuity diagnostics (November 23, 2026)

PLAN C82-1/C82-3, failing before implementation:
`/usr/bin/python3 -m pytest tests/guardrails/test_validate_bash.py -q -k 'reports_rule_without or narrow_ignore_exception'`
reported 8 failed, 4 passed. Failures were the missing ignore source/line/pattern
in the existing diagnostic. Four migration cases already passed and preserve policy.

After implementation, C82-1 through C82-3:
`/usr/bin/python3 -m pytest tests/guardrails/test_validate_bash.py -q`
reported **140 passed**. Eight cases cover four continuity files and two ignore
sources with unrelated staged work; four cases remove the obstruction using a
narrow exception, stage sanitized continuity and verify the resulting commit.
Checks also prove no file/index mutations, no private-content output and continued
exclusion of unrelated private notes. No real client files were used as fixtures.

C82-4: `./scripts/verify-pack.sh` reported **518 passed, 4 skipped**, DONE.
The four skips require Python 3.11+ tomllib; the script found pytest on system
Python 3.9. Re-ran exactly the four installer cases with Python 3.14:
`UV_TOOL_DIR=/tmp/possibnow-82-uv-tools uv --cache-dir /tmp/possibnow-82-uv-cache tool run --python /opt/homebrew/bin/python3 --with pytest pytest tests/guardrails/test_codex_host.py -q -k installer`
reported **4 passed, 12 deselected**. Together all 522 collected cases passed.
The default Homebrew python3 initially lacked pytest; the system interpreter was
used without changing global packages. Test-tool installation stayed under /tmp.

`git diff --check` passed. Ignore audit: existing .agent/REVIEW.md and TEST.md are
tracked here; check-ignore reports no matching ignore for REVIEW/TEST/WIKI/LEARNINGS.
No harness ignore-rule migration was needed. Live installed plugins, client
repository migrations and host enforcement are UNCONFIRMED by these tests.
Security applicability and review are recorded in REVIEW.md.


## v4.3.8 release validation (November 23, 2026)

R438-1/R438-2 failing before pin changes: installer tests 8 failed / 7 passed.
After updating active pins: 15 passed. `./scripts/verify-pack.sh`: 518 passed,
4 skipped (Python 3.9 lacks tomllib), DONE. The four skipped Codex installer cases
were rerun on Python 3.14: 4 passed. `claude plugin validate .`: passed with the
existing optional-icon warning. `git diff --check`: passed. No runtime code changes
beyond the already merged #83 payload. Public-tag smoke and installed-byte checks
are release-stage gates recorded in RELEASE-4.3.8.md after publication.


## v4.3.8 published verification

Public bootstrap hash/version/commit, customized-file preservation and repeat
byte/mtime stability passed. Five live registrations across two machines verify
as 4.3.8; installed Bash-hook block/allow/private-note smokes and tag-byte checks
passed on both. Four Codex scripts match the tag; configuration/trust records are
semantically unchanged. Full publication receipts: RELEASE-4.3.8.md.

## HANDOFF pointer rule and size check (November 25, 2026, branch Fix-Handoff-Size)

Evals HS-1 to HS-12 from [PLAN](PLAN.md).
- Red first: 35 of the new tests failed before implementation (`uvx --with pytest pytest -q` on the five touched test files: 35 failed, 165 passed); existing tests unchanged and passing.
- One test changed during implementation: a missing `## Status` no longer fails by default (it would block every commit in legacy handoffs and broke 11 existing guard fixtures); it is bounded by `max_bytes` and can be required through `required_headings`.
- HS-12: `handoff_size.py .` on the old HANDOFF: BLOCKED, Status 72 lines / 4,620 bytes. After `checkpoint.py`: OK, 8,351 bytes; archive `49727121…f3b424` byte-identical to `HEAD:.agent/HANDOFF.md` (`cmp`).
- Full suite: `uvx --with pytest pytest -q` 559 passed (baseline 522). `scripts/verify-pack.sh`: DONE (554 passed, 5 skipped in its interpreter).
- Sonnet review (read-only): no blocking defects. Fixed with failing-first tests: variant `## Status` headings now measured (4 cases red, then green); guard sets `dont_write_bytecode` (red, then green); a notice when the size module is missing. The staged-versus-disk case was already covered by the unstaged-HANDOFF guard (regression test added). Not changed: limits can be loosened in the same commit (documented as review-required).
- After review: `uvx --with pytest pytest -q` 566 passed; `scripts/verify-pack.sh` DONE (561 passed, 5 skipped).
