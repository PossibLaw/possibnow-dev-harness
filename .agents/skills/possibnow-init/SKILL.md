---
name: possibnow-init
description: Initialize a target repository with the PossibNow Dev Harness project pack. Use when the user explicitly asks to scaffold or update a repo with this harness.
---

# Initialize a project

This skill lives in the harness repository. Resolve the harness root from this file's location (`.agents/skills/possibnow-init/SKILL.md`) and use its `scripts/install-project.sh`.

Choose the target from the user's path, or the current working directory if none was given. Resolve the target to an absolute existing directory. If the target is the harness repository itself, stop unless the user explicitly requested a self-install. Inspect existing `AGENTS.md` and `.agent/PLAN.md` before running against an installed project; explain that all existing files are preserved. Differing files remain pending reviewed migration; the installer reports the versioned policy and candidate paths.

Run `scripts/install-project.sh TARGET [options]` from the harness root. Pass user options as separate arguments, never as executable shell text. Support `--dry-run`, `--adopt`, `--preserve-progress`, `--name`, `--owner`, and the command overrides shown by `--help`. For an existing repo, use `--adopt` unless the user supplied a different supported mode.

Report the installer's result and any `UNCONFIRMED` commands. If it fails, show the actionable error. After a successful write, report pending migrations and the release policy path; review the diff and remind the user to sanitize and commit the shared governance and continuity files with their work. Do not claim that Claude hooks are installed by this project-file installer.
