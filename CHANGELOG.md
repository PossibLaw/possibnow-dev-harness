# CHANGELOG

## 4.3.1 — 2026-10-26 — Autonomous runs actually start, stay guarded, and free their slot

The first autonomous night (October 25, 2026) started nothing; these fixes come from that run and the by-hand run the next morning. Bootstrap and pack pinned to v4.3.1.

- **Dispatcher caps**: an auto worktree stops counting against the caps once its linked issue is closed (Orca keeps the worktree, and people keep working in the pane), so the next night is not stalled; the report lists such worktrees under "Finished, still open in Orca". Running worktrees are now matched to their repo through `orca repo list` (Orca records carry `repoId`, never `repoPath`), so the per-repo cap counts them at all; running-issue checks are per repo. Two tests, red first.
- **Autonomous-run detection**: Orca 1.4.240 names a worktree's branch after `--name`, so dispatcher runs live on `auto-<n>`, not `orca/auto-<n>`. The guard (`scripts/guardrails/autonomy.py`, new `auto_issue`), the dispatcher's worktree count and PR flagging now accept both spellings; `auto-complete-widget` and similar human branches stay normal. Four tests, two red first.
- **Dispatcher**: repo paths from the config are tilde-expanded before they reach `orca worktree create --repo path:...` (Orca does not expand `~`, so every start failed with `repo_not_found` on the night of October 25, 2026); when Orca exits non-zero with an empty stderr, the `--json` error on stdout is read and its code reaches the morning report instead of a blank. Two tests, red first.
- **Dispatcher**: a backticked token counts as a path only when it exists in the repo checkout or its parent folder does, so model names, keychain items and branch names no longer count; a row with no Owner column is rejected when its text waits on a person ("Sal decides", "ask Sal", "Sal's call"). Two tests, red first.

## 4.3.0 — 2026-10-24 — Orca-first operating system, autonomy guardrails, Codex hooks

Orca worktree setup helper and runbook; issue sync, board step, TickTick mirror, work router and autonomy dispatcher; git guardrail gaps and Pocock-derived skills (PR #14); guardrails as Codex hooks. Bootstrap and pack pinned to v4.3.0.

- **Orca**: add `scripts/orca-worktree-setup`, the shared Setup Script helper for Orca worktrees (copies `.claude/settings.local.json` and env files from the main checkout without overwriting, clones extra gitignored paths with `--clone`, links Claude Code project memory to the main checkout, runs `npm ci` only when a lockfile exists; reruns are no-ops). Add `docs/orca.md`, the generic runbook: project settings, setup line pattern, wait-for-setup, issue command template, worktree creation fields, what not to run in worktrees. Nine fixture-based tests in `tests/harness/test_orca_worktree_setup.py`; both files required by `scripts/verify-pack.sh`.
- **Autonomy (GR01)**: (1) the sync turns upper-case tags in a row's state cell into labels it adds and never removes (`AUTO-OK` → `auto-ok`, `MAINTENANCE` → `maintenance`, `URGENT` → `urgent`), creating the labels per repo; (2) guardrails: `gh pr merge` and the REST merge ask first in every session; in an autonomous run (`AGENT_AUTO=1` or a branch named `orca/auto-*`) merging and publishing commands are blocked (`post-note`, `publish_draft`, `prepublish_draft`, `"publish": true`, `"send": true`, `npm publish`, push to main) and the new `guard-auto-publish.py` PreToolUse hook denies MCP tools that publish or post (drafting tools pass); shared check in `scripts/guardrails/autonomy.py`; (3) `scripts/dispatch-auto-issues.py` starts Orca worktrees (`auto-<n>`, branch `orca/auto-<n>`) on open issues carrying the eligible labels, not owned by a person, naming only allowed paths, with no open PR or running worktree, within total and per-repo caps; flags every open `orca/auto-*` PR with `agent-auto` and a `[auto]` title prefix; writes the morning report; `--dry-run`. Policy and config live outside this repo. Tests: 2 sync, 7 guardrail, 7 dispatcher, all written first.
- **Dispatcher report**: issues that simply lack `auto-ok` are counted in one line instead of listed one by one, so the morning report stays short.
- **Orca runbook**: corrected section 4. In Orca 1.4.x the Custom GitHub Issue Command field runs as a shell command in a split pane and the agent gets only the bare issue URL (stablyai/orca#9066); the runbook now says to leave the field empty and put starter instructions in `CLAUDE.md` / `AGENTS.md`, and notes that `orca worktree create --prompt` does deliver a first prompt.
- **TickTick link (TT01)**: add `scripts/sync-issues-to-ticktick.py`, mirroring open labelled GitHub issues into one TickTick list (created when missing), one task per issue with a marker in the content, priority from labels through a configurable map (TickTick's Eisenhower matrix reads 5/3/0 as quadrants), closed issues completed, nothing deleted, `--dry-run`. Token from `TICKTICK_TOKEN`; base URL overridable for tests. Six tests against an in-process fake TickTick API and a fake `gh`, written first. Which repos, list and map live outside this repo.
- **Issue sync board step**: with `board.enabled`, every open synced issue is added once to the configured GitHub Project (`gh project item-add`, needs the `project` scope); adds are tracked in the state file, failures are listed under the board line and never fail the run, `--dry-run` reports the count. A user-owned board holding organization repositories' issues was confirmed on October 23, 2026. Three new tests.
- **Work router**: add the user-invoked skill `routing-work-to-a-repo` (one sentence → the owning repository's GitHub issue with the flywheel line, labels `agent-task` and `routed`, a register row, and an offered Orca worktree). The topic → repository table is personal and read from `~/agent-tasks/routing.md`; the skill never guesses on no match and refuses bank or card details. Test: `tests/harness/test_routing_skill.py`.
- **Issue sync**: add `scripts/sync-tasks-to-issues.py`, a one-way mirror of each configured repository's `.agent/TASKS.md` first section into GitHub issues labelled `agent-task` (hidden marker per row, prose wins; DONE rows and rows that leave the register close their issue; GitHub-side closes and edits are reported as drift, never written back; card and bank patterns are never sent; rows without an ID are reported; `--dry-run`, `--only`, `--slack` summary; Project board step behind `board.enabled`, off by default). Uses `gh api` REST only. Fourteen tests with a fake `gh` in `tests/harness/test_sync_tasks_to_issues.py`; required by `scripts/verify-pack.sh`. Configuration (which repos, label, board) lives outside this repo.
- **Closing skill** (`skills/closing-sprint-and-syncing-state`, 2.1.0): ends with the cross-repo feeder step (`python3 ~/.agents/skills/cross-repo-tasks/feed.py`) so every install carries it; when the feeder is not installed the skill says to skip and note it in the handoff. Test: `tests/harness/test_closing_skill_feeder_step.py`.
- `.gitignore`: ignore `.orca` (Orca writes it when a project's issue command is set). No version bump; per-person Orca settings stay out of this public repo.
- **Codex installer**: `scripts/install_codex_guardrails.py` now also copies `autonomy.py`, which `validate-bash.py` imports since the autonomy guardrails; without it the Codex hook failed on every call. Test added.

### Git guardrail gaps and Pocock-derived skills (PR #14, included in 4.3.0)

- **Guardrails (`scripts/guardrails/blacklist.py`)**: force-push to main/master is now blocked in every common spelling (`-f`, trailing `--force`/`-f`, `--force-with-lease`, `+main` refspec), and `git clean` with any force flag (`-df`, `-xdf`, `--force`) is blocked. Ask-first now covers other force-push spellings, `git branch -D` / `--delete --force`, `git checkout .`, and `git restore .` (not `--staged`). Ordinary `git push`, `branch -d`, `restore --staged` and `clean -n` stay silent. 29 new regression cases (241 total).
- **Skills**: add user-invoked `splitting-work-into-tickets` and `running-a-retro`, adapted from mattpocock/skills at 49dd158 (MIT, attributed in each file). Tickets publish to GitHub Issues when a GitHub remote and `gh` auth exist, else to local `.agent/tickets/`; frontier tickets are meant for parallel worktree agents.
- **Docs**: add `docs/references/writing-for-agents*.md` as a maintainer reference (not shipped to projects).
- **Codex guardrails**: `validate-bash.py --host codex` turns ask-first into a block with an instruction to ask the user (Codex parses but ignores `ask`); `protect-files.py` reads paths from Codex `apply_patch` headers (Add/Update/Delete/Move to). New `scripts/install_codex_guardrails.py` copies the guards to `~/.codex/hooks/possibnow/` and registers them inline in `config.toml` between markers (not Orca-managed `hooks.json`), keeps Codex trust-state tables, is idempotent, and refuses to merge into existing hook definitions. Live Codex 0.155.1 run: force-push to main blocked, `branch -D` stopped as ask-first. 16 new cases (257 total).

## 4.2.1 — 2026-09-18 — Verified portable release

- Fix rollback receipt handling when the target root has an equivalent path alias (including macOS /var and /private/var). Internal symlinks and out-of-repo receipt paths remain rejected.
- The v4.2.0 tag failed its final published rollback smoke gate; it is preserved unchanged for provenance. Use v4.2.1 for both bootstrap and pack. All compact-guidance and conservative-update changes below are included.

## 4.2.0 — 2026-09-18 — Compact portable guidance and conservative upgrades

- Generate both project entries from one compact source and enforce 150 physical lines each, including LF/CRLF and final unterminated lines. Detailed delivery, continuity, content, learning, and client guidance loads on demand.
- Preserve all existing project files. Supply versioned candidates, current optimization policy, pending migration hashes, and a guarded installation rollback receipt. Dry-run writes nothing; repeated installs do not churn files. Ignore rules are preserved and reported for review.
- Add byte-exact checkpoint archival, verification, deduplication, and intervening-edit checks. Semantic completeness remains reviewed; legacy history survives intact.
- Reconcile OFF/CAPTURE/APPLY and candidate/promotion gates; distinguish advisory instructions from tested Claude-only hooks.
- Pin bootstrap and pack to v4.2.0; print source version/commit. No model, permission, learning mode, Scale, or global setting changes.

### Codex workflow parity (included in 4.2.0)

- Add Codex project skills for Init, Scale, Guardrails, and Optimize. The project installer ships the three ongoing skills and the four existing workflow skills to `.agents/skills/`; Init is available from the harness clone where its installer source lives.
- Clarify that Codex invokes these with `$name` and that Claude plugin hooks do not run in Codex. Preflight rejects symlinked Codex skill directories before writing project files.

## 4.1.0 — 2026-09-18

- Add `/possibnow-dev-harness:optimize`: read-only proposal, then reviewed project apply with validation/rollback and quality-gated model changes.
- Commit all relevant sanitized continuity; split current HANDOFF from historical HISTORY. Preserve existing state on every installer rerun.
- Retire exact legacy continuity ignore rules while preserving private and broad custom exclusions for review.
- Extend the direct Git commit guard to named continuity, content records, archives, and existing history.
- Make installer dry-run read-only and add regression coverage.

## 2026-08-31 — v4.0.1 — guardrail fixes: chmod escalation narrowed to risky forms; format-check emits valid hook output
- **`scripts/guardrails/blacklist.py`**: the escalate-tier rule `chmod\s+(?!777)` asked for confirmation on EVERY chmod the hard tier didn't block — including `chmod 644`, `chmod +x`, and `chmod 000` on scratch files — which made the confirm tier pure noise in agent-heavy sessions (observed 2026-08-31: a test harness's `chmod 000` on a mktemp file woke the user). Replaced with a risky-forms set: recursive (`-R`), world-writable grants (`o+w` / `a+w` / bare `+w`, and numeric modes whose others digit grants write: 2/3/6/7), and setuid/setgid (`+s`, four-digit modes starting 2/4/6). The mode-777 forms stay hard-blocked in `BLOCKED_PATTERNS`, unchanged. Tests updated to the new contract: `chmod 644` / `chmod +x` moved to the safe group with `000` / `600` / `u+w` / `755` beside them; `-R 755`, `o+w`, `a+w`, `666`, `4755`, `u+s` pinned as escalated. 81 pytest cases pass.
- **`scripts/guardrails/format-check.sh`**: both output sites emitted `{"hookSpecificOutput":{"suppressOutput":true}}`, an invalid shape — `suppressOutput` is a top-level field and `hookSpecificOutput` requires `hookEventName` — so every Write/Edit surfaced a "Hook JSON output validation failed" error in the transcript (observed in every lane session 2026-08-31). Now emits `{"suppressOutput":true}`.
- `scripts/verify-pack.sh`: version check bumped to 4.0.1.

## 2026-08-24 — Graphify workflow refreshed to the CLI (verified against graphify 0.9.49)
- `packs/project/docs/workflows/graphify.md`, `skills/scaling-up-with-graphify/SKILL.md`, and `commands/scale.md` documented the upstream `/graphify` slash skill at ~v0.1.8; the harness never installs that skill and its build flags (`/graphify --update`) no longer match the CLI. All three now drive the CLI directly: `graphify update .` + `graphify export wiki` to build, `graphify affected` / `explain` / `query --context call` / `path --undirected` / `god-nodes` to query, `--force` after ignore edits, and a freshness rule (rebuild after every merge to `main`). Guidance from a real 659-file build: exclude prose and media in `.graphifyignore` (headings otherwise outnumber code nodes) and keep `tests/` in the graph so `affected` lists the covering tests. The doc carries a copy-paste bootstrap prompt for any agent and records why the upstream `graphify claude install` hooks stay off (a nudge on every tool call; `--project` commits an absolute binary path).
- `packs/project/{CLAUDE,AGENTS}.md` Scale Mode: one bullet with the rebuild-after-merge rule and the query commands, pointing at the doc.
- `packs/global/claude/.claude/CLAUDE.md`: one Context Management bullet offering Tier 2 through the `scaling-up-with-graphify` skill in repos with roughly 40–50+ source files, with the no-upstream-hooks rule; logged in the global pack CHANGELOG. (Codex global `AGENTS.md` unchanged: it has no Context Management section; the project-level `AGENTS.md` carries the rule.)

## 2026-08-24 — v4.0.0 — PossibNow Dev Harness rename + enforced shared handoff
- **Renamed the pack to PossibNow Dev Harness.** Plugin id `possiblaw-starter` → `possibnow-dev-harness`; slash commands are now `/possibnow-dev-harness:init`, `/possibnow-dev-harness:scale`, and `/possibnow-dev-harness:guardrails`; the GitHub repo moved from `PossibLaw/agent-starter-pack` to `PossibLaw/possibnow-dev-harness` (old URLs redirect). **Breaking for installed plugins:** run `/plugin uninstall possiblaw-starter@possiblaw-plugins`, then `/plugin install possibnow-dev-harness@possiblaw-plugins`. The marketplace entry in `PossibLaw/PossibLaw-Plugins` must be updated to the new id, source repo, and version.
- **`.agent/HANDOFF.md` must now ship with every commit.** New Claude Code guardrail in `scripts/guardrails/validate-bash.py` (`check_handoff_commit`) refuses `git commit` while the shared handoff is untracked or has unstaged edits; it honors `git commit -a`/`--all` and an inline `git add` that covers the file, and stays silent outside git repos or when the repo has no handoff. Thirty new pytest cases in `tests/guardrails/test_validate_bash.py`. Project instructions (`packs/project/{CLAUDE,AGENTS}.md`), `docs/workflows/contracts.md`, the `running-novice-safe-git-cycle` and `closing-sprint-and-syncing-state` skills, the handoff template, `commands/init.md`, and `commands/guardrails.md` state the rule for Codex and human contributors, who have no runtime hook.
- Made `.agent/HANDOFF.md` the shared, version-controlled continuity record so every developer receives the current baton and newest-first session history. Other `.agent/*.md` working-state files remain local and ignored by default.
- Updated the project installer to remove its legacy `.agent/HANDOFF.md` ignore entry while preserving local-state and unrelated ignore rules, with a verification fixture covering the migration.
- Split README command sequences into one-command code blocks so each command has its own copy action.
- `scripts/verify-pack.sh` now checks the new plugin identity and version, the handoff guard and its tests, forbids the old plugin id and product name in active pack files, and runs the guardrail pytest suite when a `python3` with pytest is available. `.github/workflows/verify-pack.yml` drops the dead Windows leg (it called `scripts/verify-pack.ps1`, removed in v3.0.0) and installs pytest so the guardrail tests run in CI.
- `scripts/bootstrap-project.sh` reads `DEV_HARNESS_REPO_URL` / `DEV_HARNESS_REF`; the old `STARTER_PACK_REPO_URL` / `STARTER_PACK_REF` names still work as aliases.
- Rebranded `assets/hero.svg` and refreshed its file table (dropped the v3-removed `TASKS.md`/`CONTEXT.md` rows). Removed stale PowerShell instructions from `docs/onboarding/`.

## 2026-08-23 — project CLAUDE.md template de-duplicated against the global layer
- `packs/project/CLAUDE.md`: the **TDD and Eval Contract** and **Boundary Rules** sections repeated the global `packs/global/claude/.claude/CLAUDE.md` (TDD and Evals; Safety Boundaries) nearly verbatim, against the template's own Local Norms rule. They are now a pointer to the global layer plus the repo-specific rules only (`docs/workflows/evals.md` fallback; never remove failing tests to force a pass; never read untriggered instruction files). **Tool Ownership** records that `AGENTS.md` deliberately keeps the full text for tools that may have no global layer. `packs/project/AGENTS.md` unchanged. Measured saving ~110 tokens per session; the point is one source of truth that cannot drift.

## 2026-06-29 — v3.0.0 — First-principles refresh (two-tier progressive harness)
- Reframed the pack as a **two-tier progressive harness** for non-developer legal users: **Tier 1 (Starter, default)** keeps the `PLAN → TEST → REVIEW → HANDOFF` workflow with single-file continuity, guardrails, the simplicity ladder, and token discipline; **Tier 2 (Scale, opt-in)** adds Graphify indexing, wiki orientation, and deeper review. Added the `/possiblaw-starter:scale` command (`commands/scale.md`) as the gate the harness suggests as a codebase grows. Bumped `.claude-plugin/plugin.json` to `3.0.0`.
- **Merged continuity into one file.** `.claude/history.md` is removed; its newest-first session timeline now lives below a STOP marker inside `.agent/HANDOFF.md` (current baton on top). Updated `docs/architecture/memory-and-indexing-guide.md`, README, glossary, and the checkpoint helper accordingly.
- **Folded `.agent/CONTEXT.md` and `.agent/TASKS.md` into `.agent/PLAN.md`** (goal + assumptions + task checklist in one place). The `.agent/` set is now PLAN, REVIEW, TEST, HANDOFF, WIKI, LEARNINGS.
- Added the **simplicity ladder** (`skills/applying-simplicity-ladder/`), a **token-management guide** (`docs/workflows/token-management.md`), the **scaling-up-with-graphify** skill (`skills/scaling-up-with-graphify/`), and **validation-gated learnings** (a lesson is promoted to `.agent/LEARNINGS.md` only if it recurred at least twice or the user confirmed it).
- Added an **adopt-into-an-existing-repo** path: `scripts/install-project.sh --adopt` (alias for `--preserve-progress`) preserves existing state and **assesses codebase size**, recommending Tier 2 Scale mode when a repo exceeds ~50 source files (prints `SOURCE_FILE_COUNT` + a `/possiblaw-starter:scale` recommendation). The SessionStart hook (`scripts/guardrails/git-status.sh`) emits the same one-line nudge until Scale mode is on. Documented the existing/older-repo flow in the README.
- **Removed MemPalace stubs** (`packs/project/.agent/integrations/mempalace-ingest.{sh,ps1}`); MemPalace is now mentioned only as a possible future optional retrieval backend, not something shipped. The checkpoint helper (`packs/project/.agent/integrations/run-checkpoint.sh`) is now a pure advisory checklist printer that lists the PLAN/HANDOFF updates and never writes state or calls a backend.
- **Dropped all Windows/PowerShell support**: removed every `*.ps1` script (`scripts/{bootstrap-project,install-project,install-global,verify-pack,set-learning-mode}.ps1`, `packs/project/.agent/integrations/{run-checkpoint,mempalace-ingest}.ps1`) and all PowerShell instructions from README and command docs. Launch support is macOS + Linux (bash) only; cross-tool support via `AGENTS.md` is preserved.
- **Removed three unused agents** (`agents/{task-planner,test-agent,test-generator}.md`) and the `COMPACT_STATE` sidecar plus `scripts/guardrails/persist-state.py` and `tests/guardrails/test_persist_state.py`; dropped `persist-state` from the Tier 2 hooks list.
- **Fixed the history.md commit-vs-gitignore contradiction**: `commands/init.md` no longer tells users to `git add .claude/history.md`/`.agent/*` state files — continuity files stay local and gitignored; only shared governance/scaffold files are committed.
- **Fixed the guardrails command identity**: `commands/guardrails.md` now uses `/possiblaw-starter:guardrails` (matching the `possiblaw-starter` plugin) and drops the unwired "Stop Prompts Validation" claim, leaving the accurate Tier-1 hooks (validate-bash, protect-files, format-check).
- Updated `docs/architecture/file-purpose-map.md` and `packs/project/docs/glossary.md` to match the new inventory and concepts.

## 2026-05-01 — Newest-first continuity contract
- Updated continuity templates so `PLAN.md`, `HANDOFF.md`, and `.claude/history.md` keep current resume context above a stop marker, preserve older material below an archive boundary, and avoid alternate continuity sidecar files.
- Kept `AGENTS.md` and `CLAUDE.md` changes pointer-level while moving detailed newest-first behavior into `docs/workflows/contracts.md` and the checkpoint skills.
- Updated verification scripts to require the stop marker in the three canonical continuity templates.

## 2026-04-28 — v2.1.0 — Project-init slash command
- Added `/possiblaw-starter:init` slash command (`commands/init.md`) that runs `scripts/install-project.sh` against the current working directory. Closes the UX gap where users installing only the plugin had no in-Claude-Code path to scaffold the state-artifact pipeline (`.agent/*.md`), governance files (`AGENTS.md`, `CLAUDE.md`), role + workflow contracts (`docs/roles/`, `docs/workflows/`), and project-local skills into their own repo.
- Bumped plugin version to `2.1.0` in `.claude-plugin/plugin.json` so users running `/plugin update` pick up the new command.
- README updated: explains that `/plugin install` provides the global runtime layer (guardrails + agents + skills) and `/possiblaw-starter:init` provides the per-project files.

## 2026-04-28 — v2.0.0 — Plugin packaging + guardrails absorption
- Added Claude Code plugin manifest at `.claude-plugin/plugin.json` (`name: possiblaw-starter`, `version: 2.0.0`); the starter pack is now installable as a single Claude Code plugin while preserving the existing dual-host bootstrap installers for Codex.
- Promoted repo-local workflow skills from `packs/project/.claude/skills/` to top-level `skills/` (`closing-sprint-and-syncing-state`, `running-novice-safe-git-cycle`); added `version: 1.0.0` to each `SKILL.md` frontmatter.
- Promoted host-agnostic agent definitions from `packs/global/claude/.claude/agents/` to top-level `agents/` (11 `.md` files).
- Absorbed runtime guardrails (predecessor: `possiblaw-guardrails` v1.2.2 plugin): copied hooks (`hooks/hooks.json`, `hooks/tier2-hooks.json`), Python/shell scripts (`scripts/guardrails/{validate-bash,protect-files,format-check,blacklist,persist-state,sanitize-input,validate-task,validate-subagent,git-status}`), pytest suite (`tests/guardrails/test_*.py`, 113 tests passing), and the `/possiblaw-starter:guardrails` slash command (`commands/guardrails.md`).
- Updated all `${CLAUDE_PLUGIN_ROOT}/scripts/...` hook command paths to point at the new `scripts/guardrails/` location; updated test `SCRIPT` path constants to `parent.parent.parent / "scripts" / "guardrails" / ...` so pytest runs against the relocated scripts.
- Updated install scripts so `install-project.{sh,ps1}` copy SKILL.md files from top-level `skills/` and `install-global.{sh,ps1}` copy agents from top-level `agents/` (Bash + PowerShell parity preserved). Codex pack assets (`packs/global/codex/.codex/*`, `packs/project/AGENTS.md`, `docs/roles/*`, `docs/workflows/*`, `.agent/` templates) are unchanged.
- Updated `scripts/verify-pack.{sh,ps1}` to require the plugin manifest, top-level `skills/` and `agents/` (>=10 agent .md files), `hooks/hooks.json`, `scripts/guardrails/validate-bash.py` (executable), and `tests/guardrails/test_validate_bash.py`.
- Tier 2 hooks (validate-task, validate-subagent, sanitize-input, persist-state, git-status SessionStart) ship in `hooks/tier2-hooks.json` and remain disabled by default; documented opt-in path in `README.md`.

## 2026-04-22
- Fixed installer cross-platform parity: Bash `install-project.sh` now tracks whether `.agent/TEST.md` was newly copied and uses the same placeholder-replacement condition as the PowerShell installer (`scripts/install-project.sh`).
- Renamed the Claude reviewer wrapper to match the canonical role (`packs/global/claude/.claude/agents/reviewer.md`, previously `review-agent.md`); updated references in `scripts/verify-pack.sh`, `scripts/verify-pack.ps1`, `packs/project/docs/roles/README.md`, and `packs/project/CLAUDE.md`.
- Collapsed the duplicated `Contract Pipeline` and `Continuity Checkpoint Contract` bodies in `packs/project/CLAUDE.md` and `packs/project/AGENTS.md` into short pointers to the canonical source (`packs/project/docs/workflows/contracts.md`).
- Added parity governance sections to `packs/project/CLAUDE.md` so Claude and Codex templates now mirror each other: `Tool Ownership`, `Canonical Roles`, aligned `Routing Rules`, and `Security Review Contract`.
- Extracted the Graphify Indexing Request Contract out of `packs/project/docs/workflows/wiki.md` into a dedicated `packs/project/docs/workflows/graphify.md`; added an explicit note that the upstream PyPI package is `graphifyy` (CLI entry point `graphify`); updated installer/verify scripts, README, architecture docs, and the Startup Contract in both CLAUDE.md and AGENTS.md to point at the new file.
- Added `packs/project/docs/glossary.md` with 25+ beginner-friendly definitions (roles, artifacts, TDD/evals, trust boundary, IDOR/CSRF, UNCONFIRMED, BLOCKED); linked from Startup Contract in CLAUDE.md and AGENTS.md.
- Shipped stub MemPalace hooks (`packs/project/.agent/integrations/mempalace-ingest.{sh,ps1}`) so the advertised integration point is self-documenting; updated `packs/project/.agent/integrations/README.md` to describe the stubs, and added them to installer copy lists and `scripts/verify-pack.{sh,ps1}` required-file checks.
- Filled the empty `evals.md` eval-table with a concrete worked example (Export contacts as CSV — happy, edge, failure/security) to anchor the beginner audience.
- Removed a tracked macOS artifact (`.DS_Store`) from `packs/project/.agent/integrations/`.

## 2026-04-21
- Added explicit continuity-checkpoint rules to the Codex and Claude project templates so sprint closeout, pre-git-cycle, session end, and context-pressure checkpoints refresh plan, handoff, and history consistently (`packs/project/AGENTS.md`, `packs/project/CLAUDE.md`, `packs/project/.agent/PLAN.md`, `packs/project/.agent/TASKS.md`, `packs/project/.agent/HANDOFF.md`, `packs/project/.claude/history.md`, `packs/project/docs/workflows/contracts.md`).
- Added local checkpoint integration helpers plus a MemPalace hook contract under `.agent/integrations/` (`packs/project/.agent/integrations/README.md`, `packs/project/.agent/integrations/run-checkpoint.sh`, `packs/project/.agent/integrations/run-checkpoint.ps1`).
- Added repo-local workflow skills for sprint closeout/state sync and a novice-safe git cycle (`packs/project/.claude/skills/closing-sprint-and-syncing-state/SKILL.md`, `packs/project/.claude/skills/running-novice-safe-git-cycle/SKILL.md`).
- Updated installers, verification scripts, README, and architecture docs so the new continuity helpers and skills install and validate as part of the pack (`scripts/install-project.sh`, `scripts/install-project.ps1`, `scripts/verify-pack.sh`, `scripts/verify-pack.ps1`, `README.md`, `docs/architecture/file-purpose-map.md`, `docs/architecture/memory-and-indexing-guide.md`).

## 2026-04-09
- Added a canonical host-agnostic role registry plus six shared role contracts for planning, review, validation, and handoff (`packs/project/docs/roles/README.md`, `packs/project/docs/roles/*.md`).
- Updated project templates to route Codex and Claude through the shared role contracts instead of freeform role lists (`packs/project/AGENTS.md`, `packs/project/CLAUDE.md`, `packs/project/.agent/PLAN.md`, `packs/project/.agent/TEST.md`, `packs/project/.agent/REVIEW.md`, `packs/project/.agent/HANDOFF.md`, `packs/project/docs/workflows/contracts.md`).
- Replaced weak Claude-side wrappers with role-aligned host adapters and added canonical wrappers for strategy, planning, QA, and release work (`packs/global/claude/.claude/agents/*.md`).
- Updated installers, verification scripts, and top-level docs so the shared role registry installs and validates as part of the starter pack (`scripts/install-project.sh`, `scripts/install-project.ps1`, `scripts/verify-pack.sh`, `scripts/verify-pack.ps1`, `README.md`, `docs/architecture/file-purpose-map.md`).
- Added optional wiki-mode workflow doc for persistent context acceleration with trust order and verification rules (`packs/project/docs/workflows/wiki.md`).
- Added concise wiki-mode pointers in project startup templates while keeping detailed guidance in workflow docs (`packs/project/AGENTS.md`, `packs/project/CLAUDE.md`, `packs/project/docs/workflows/contracts.md`).
- Updated installers and verification scripts to include and enforce wiki-mode artifacts (`scripts/install-project.sh`, `scripts/install-project.ps1`, `scripts/verify-pack.sh`, `scripts/verify-pack.ps1`).
- Added `.agent/WIKI.md` starter template for wiki enablement flag, Obsidian vault path, auto-derived wiki root, and sync rules.
- Updated handoff/history templates to capture wiki sync output (`packs/project/.agent/HANDOFF.md`, `packs/project/.claude/history.md`).
- Updated startup and local-continuity rules so wiki configuration is treated as a first-class state artifact (`packs/project/AGENTS.md`, `packs/project/CLAUDE.md`, `scripts/install-project.sh`, `scripts/install-project.ps1`, `scripts/verify-pack.sh`, `scripts/verify-pack.ps1`).
- Added a typed workflow contract doc for staged state artifacts and optional integrations (`packs/project/docs/workflows/contracts.md`).
- Updated project templates to enforce pipeline sequencing and optional integration points for raw-mode memory retrieval and stage skills (`packs/project/AGENTS.md`, `packs/project/CLAUDE.md`).
- Added structured contract headers to state artifact templates and explicit cross-artifact linkage fields (`packs/project/.agent/PLAN.md`, `packs/project/.agent/CONTEXT.md`, `packs/project/.agent/TASKS.md`, `packs/project/.agent/REVIEW.md`, `packs/project/.agent/TEST.md`, `packs/project/.agent/HANDOFF.md`, `packs/project/.agent/LEARNINGS.md`).
- Updated installers to include the new contracts workflow artifact (`scripts/install-project.sh`, `scripts/install-project.ps1`).
- Expanded pack verification to require the contracts workflow artifact, contract sections, and typed artifact headers (`scripts/verify-pack.sh`, `scripts/verify-pack.ps1`).
- Updated top-level docs to reflect the new contract pipeline and optional memory/skill integration guidance (`README.md`, `docs/architecture/file-purpose-map.md`, `packs/project/docs/workflows/evals.md`).

## 2026-03-03
- Improved installer warning messaging when command inference leaves `UNCONFIRMED` values (`scripts/install-project.sh`, `scripts/install-project.ps1`) with explicit “why” and remediation steps.
- Clarified `.agent/TEST.md` guidance to treat `UNCONFIRMED` commands the same as placeholders (`packs/project/.agent/TEST.md`).
- Moved “Pick the Right Mode” guidance to the top of the quick start and documented the `UNCONFIRMED` warning (`README.md`).
- Added an evals-driven development workflow doc and linked it from project templates (`packs/project/docs/workflows/evals.md`, `packs/project/AGENTS.md`, `packs/project/CLAUDE.md`).

## 2026-03-01
- Enforced repo-root validation and state-file path constraints in project templates (`packs/project/CLAUDE.md`, `packs/project/AGENTS.md`) and global templates (`packs/global/claude/.claude/CLAUDE.md`, `packs/global/codex/.codex/AGENTS.md`).
- Added explicit `BLOCKED + ask` behavior when repo root is unresolved, ambiguous, or inside OS temp directories.
- Standardized required state artifact write paths to `${REPO_ROOT}/.agent/PLAN.md`, `${REPO_ROOT}/.agent/HANDOFF.md`, and `${REPO_ROOT}/.claude/history.md` for both Claude and Codex contracts.
- Added vendor documentation support in the project pack (`packs/project/docs/vendor/README.md`, `packs/project/docs/vendor/supabase.md`) with metadata and official-source requirements.
- Added vendor routing rules to project templates and explicit vendor recency verification rules to global templates.
- Updated project installers (`scripts/install-project.sh`, `scripts/install-project.ps1`) and verification scripts (`scripts/verify-pack.sh`, `scripts/verify-pack.ps1`) to include and enforce vendor documentation artifacts.
- Updated docs (`README.md`, `docs/architecture/file-purpose-map.md`) to document the `docs/vendor/` extension pattern and Supabase as the initial vendor guide.

## 2026-02-20
- Added bootstrap installers (`scripts/bootstrap-project.sh` and `scripts/bootstrap-project.ps1`) that clone the starter pack to a temporary directory and install into the current repo by default.
- Updated project installers (`scripts/install-project.sh` and `scripts/install-project.ps1`) so target path is optional and defaults to `.`.
- Added explicit placeholder-path validation with actionable hints when users leave `/path/to/your/repo` or `C:\path\to\your\repo` unchanged.
- Updated onboarding docs to use no-placeholder quick-start commands and preserve-progress bootstrap examples.
- Updated verification scripts to require bootstrap installer entrypoints.

## 2026-02-19
- Added native Windows PowerShell script variants for project install, global install, pack verification, and learning mode updates.
- Added `--preserve-progress` mode to project installers (`.sh` and `.ps1`) so existing repos can refresh starter-pack files without overwriting progress artifacts.
- Updated verification scripts to require both Bash and PowerShell entrypoints.
- Updated GitHub Actions verification workflow to run on both Linux and Windows.
- Added `.gitattributes` line-ending rules for `.sh` and `.ps1` scripts.
- Updated onboarding and architecture docs to document Windows usage via PowerShell.

## 2026-02-17
- Added optional `.agent/LEARNINGS.md` template to project pack for opt-in learning capture.
- Added explicit `Learning Mode` controls (`OFF`, `CAPTURE`, `APPLY`) to project `AGENTS.md`, `CLAUDE.md`, and `.agent/PLAN.md`.
- Added `scripts/set-learning-mode.sh` helper command to toggle learning mode quickly in `.agent/PLAN.md`.
- Updated `scripts/install-project.sh` and `scripts/verify-pack.sh` to install and validate learning artifacts.
- Updated docs (`README.md`, `docs/architecture/file-purpose-map.md`) to document default-off learning workflow and activation.

## 2026-02-11
- Initial starter-pack structure created.
- Added combined Claude + Codex project/global packs.
- Added installer scripts for project and optional global setup.
- Added verification script.
- Added full reference docs and onboarding/architecture documentation.
- Added TDD and eval contracts to project templates (`packs/project/AGENTS.md`, `packs/project/CLAUDE.md`, `packs/project/.agent/TEST.md`).
- Added no-assumption eval policy and required end-user eval walkthrough format.
- Synced global templates with TDD/eval + low-friction inference guidance (`packs/global/codex/.codex/AGENTS.md`, `packs/global/claude/.claude/CLAUDE.md`).
- Upgraded `scripts/install-project.sh` with repo-based command auto-detection plus explicit override support.
- Updated onboarding docs for one-command install in both new and existing repos.
