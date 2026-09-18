# Troubleshooting

- Missing target: create/select the intended project directory and run from its root.
- Missing Python/Git/Bash: the project installer requires these local tools.
- PENDING files: existing differing instructions are deliberately preserved. Follow
  the versioned optimization policy named in installation output for a reviewed diff.
- Oversized existing root: keep its local policy until a reviewed migration reduces
  it to <=150 physical lines. Do not delete or truncate it just to pass the cap.
- Conflicting release snapshot or partial install: preserve local work; inspect its
  INSTALL.json and reconcile or use the guarded rollback command in the README.
- Ignored continuity: use git check-ignore -v on the named files; narrow only the
  relevant rules after a secret review. All related sanitized continuity is shared.
  The installer preserves .gitignore byte-for-byte.
- Checkpoint hash rejection: another edit intervened. Review the new state and
  regenerate the candidate; do not merely recalculate the hash to force it through.
- Corrupt/conflicting archive: retain HANDOFF, repair/verify archival from evidence,
  then retry. Never delete legacy history or bypass verification.
- Commit blocked by Claude hook: review and stage all changed sanitized continuity,
  including HANDOFF, HISTORY and archives, with the work. The hook checks common
  direct Git commands; it does not operate in Codex or Cursor.
- Old plugin id possiblaw-starter: uninstall the old marketplace entry and install
  possibnow-dev-harness. Confirm the actual installed version; marketplace delivery
  is separate from a source GitHub release.

Live Windows execution is UNCONFIRMED. Use a supported Unix environment; this
release does not add a Windows or another client's runtime adapter.
