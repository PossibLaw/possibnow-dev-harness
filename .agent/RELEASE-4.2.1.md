# Published release verification — v4.2.1

Published: 2026-09-18T17:18:49Z (GitHub Release, not draft/prerelease).
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.2.1
Source commit: ffe828e765d687fc63a6e8fff0a2382e40de0ea5
Remote annotated tag peeled to that exact commit.
PRs: #11 compact harness; #12 portable rollback correction.

## E10 public smoke

The curl command below was executed against a disposable customized Git repository.
Downloaded bootstrap bytes matched the released Git blob, and the cloned pack
reported version 4.2.1, the same commit, and source_dirty=false.

- Dry-run left all target file bytes and mtimes unchanged.
- Existing customized entry, workflow, continuity, learning record, and unrelated
  uncommitted file stayed byte-for-byte unchanged.
- The 151-line customized entry remained intact and explicitly PENDING migration.
- New CLAUDE entry and AGENTS candidate passed at 65 lines each.
- Repeating the update changed no bytes or mtimes and produced no duplicate archives.
- Guarded rollback restored the original fixture, including through macOS's root alias.
- No real installed project was modified. No paid model comparison ran.

```bash
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/v4.2.1/scripts/bootstrap-project.sh | DEV_HARNESS_REF=v4.2.1 bash -s -- . --adopt
```

Bootstrap SHA-256: 27d5b8f70d27076fee91b37c79da3fce81ad79fe5b386b75d99b7d59c1ef573e
Verified at: 2026-09-18T17:18:31.220788+00:00

The same machine-readable receipt is attached to the GitHub Release. Full local
and CI verification passed with 212 tests; plugin and modified skills validated.
Before/after metrics and review details are in TEST.md and REVIEW.md.

## Migration and rollback

Downloading preserves customized files; it does not complete their migration.
Use .harness/releases/4.2.1/docs/workflows/optimization.md in check mode, then apply
only the reviewed proposal with hash rechecks/private backups/validation/receipts.

```bash
python3 .harness/releases/4.2.1/tools/rollback.py . --receipt .harness/releases/4.2.1/INSTALL.json
```

Installation rollback removes only unchanged files from that receipt. For later
semantic migration, follow OPTIMIZATION.md's per-file before/after hashes and
private backup steps; preserve intervening edits and never reset the entire repo.
Live client compliance and semantic optimize apply remain UNCONFIRMED. Marketplace
publication is separate; that repository and installed projects were not modified.
The v4.2.0 candidate tag remains unchanged for provenance and is not recommended.
