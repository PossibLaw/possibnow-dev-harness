# Published release verification — v4.3.7

Published: 2026-11-16T20:37:45Z. This is a GitHub Release, not a draft or prerelease; Sal created the tag and the
release.
Release: https://github.com/PossibLaw/possibnow-dev-harness/releases/tag/v4.3.7
Tag: annotated v4.3.7, peeled to 616e355f44cfa73ea609f7c62e287aba058dd4ef, the merge of PR #80. That merge carries
the 4.3.7 version files, so tagged installs report 4.3.7.
PRs since 4.3.6:
- #77: the dispatcher counts a bare folder name as a path only when that folder exists at the root
- #79: plugin hooks run when the plugin path contains a space (#78); `git rebase` and plain `git reset` no longer ask
  first; an autonomous run refuses an ask-first command instead of asking
- #80: version and pins

## Public smoke

Run on November 16, 2026 against a disposable Git repository with its own CLAUDE.md and .agent/HANDOFF.md and one
commit:

```bash
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/v4.3.7/scripts/bootstrap-project.sh -o bootstrap.sh
DEV_HARNESS_REF=v4.3.7 bash bootstrap.sh . --adopt
```

- Bootstrap script SHA-256 at the tag: 0ed113b4fcb5b4529a3d70c7524da6b686ce4db2670a21e60416d2cc36197972, identical to
  the tagged file.
- Real run: 108 new files and 1 pending migration. The customized CLAUDE.md and HANDOFF were preserved byte for byte.
- `.harness/releases/4.3.7/VERSION.json`: version 4.3.7, commit 616e355…, source_dirty false.
- Rerun: 0 changed files.

## Installed plugin and live check

- The marketplace entry is 4.3.7 (PossibLaw/PossibLaw-Plugins PR #16, merged after the tag).
- `claude plugin update` moved the user scope and the Trazomo local scope from 4.3.6 to 4.3.7 on the operator's first
  machine, and the user scope from 4.3.6 to 4.3.7 on the second machine. On both machines every Orca profile's
  `plugins` folder is a link to the one user install, so one update covers all profiles.
- Hooks under a path with a space, the reason for this release: on each machine, every command in the installed
  `hooks/hooks.json` was run through `/bin/sh` with `CLAUDE_PLUGIN_ROOT` set to the real install path under an Orca
  profile ("Application Support"). All seven exited 0 with no error. Before this release each failed with
  `No such file or directory`.
- Live session: a fresh Claude Code session started in an Orca terminal on the first machine, took one prompt, ran
  one shell command and stopped with no hook error. Sessions before the update showed a hook error on SessionStart,
  UserPromptSubmit and Stop.
- Codex guard copy (first machine): `validate-bash.py` and `blacklist.py` changed in this release, so
  `scripts/install_codex_guardrails.py` was rerun from the tagged checkout. The four copied files now match the tag
  byte for byte. The installer rewrote its marked block in the Codex config with the same two commands; the file still
  parses and its other settings are unchanged. Whether Codex asks to trust the hooks again is UNCONFIRMED: run `/hooks`
  in Codex once to check. The second machine has no Codex guard copy installed.
- Other local and project installs on the operator's first machine still run older versions (4.1.0 to 4.3.5); that
  is TASKS H-MIG01.

Local verification: `scripts/verify-pack.sh` 506 passed, 4 skipped, DONE; CI `verify` passed on #79 and #80.

## Follow-ups

- H-MIG01: review and migrate the older installs.
- Running Claude sessions pick up 4.3.7 after a restart. From then on, sessions started from an Orca profile enforce
  the guardrails they had been skipping: destructive commands are refused, deletions and merges ask first, autonomous
  runs cannot merge or publish, and an autonomous run posts its completion notice.
- Codex: run `/hooks` once to confirm the two PossibNow hooks are trusted.
