# PossibNow Dev Harness

Compact entry instructions, detailed guidance on demand, and preserved project
continuity for coding assistants. The project templates are generated from one
shared source. Each AGENTS.md and CLAUDE.md must stay at or below **150 physical
lines**, including blanks. This is Sal's project policy, not an optimal-length or
cost-savings claim. Original research remains under `docs/references/`.

## Install or update a project

Run from the target repository root (macOS/Linux, Bash, Git, Python 3):

```bash
curl -fsSL https://raw.githubusercontent.com/PossibLaw/possibnow-dev-harness/v4.2.0/scripts/bootstrap-project.sh | DEV_HARNESS_REF=v4.2.0 bash -s -- . --adopt
```

Both the downloaded script and the pack it clones are pinned to `v4.2.0`.
Add `--dry-run` to preview without target writes. The installer reports the pack
version and source commit. A clean repository can use the same command.
`--adopt` and `--preserve-progress` remain compatibility aliases for preservation.

**Existing project files are preserved byte-for-byte.** The installer creates
missing files; equal files are left alone. Differing root entries, workflows,
skills, and helpers remain pending a reviewed migration. It does not infer that
an older file is uncustomized from its name. Even an unchanged older installation
is conservatively preserved. Existing oversized roots can remain pending; they
are never truncated to pass the new cap. Repeating the same install/options/ref
makes no file changes or duplicate backups.

The snapshot under `.harness/releases/4.2.0/` supplies the current guidance and
candidate versions. Root/skill candidates use a `.candidate` suffix so clients
do not discover them as active nested instructions. `INSTALL.json` records created-file hashes, pending file
hashes/candidate paths, and ignored-file warnings at installation time. A candidate
is a starting point for a reviewed diff, not permission to discard custom content.
The snapshot is a release artifact; its policy is authored once in the source pack.
For a local comparison, run `git diff --no-index -- AGENTS.md .harness/releases/4.2.0/AGENTS.md.candidate`
(exit 1 means differences). This exposes the template difference for review; it is
not a customization-preserving patch to apply wholesale.

Downloading the new harness does **not** complete a customized project's migration.
Existing continuity, unrelated files, native/global settings, model/effort choices,
permissions, learning mode, and Scale/wiki activation are not changed. Existing
ignore rules are preserved; warnings identify shared files needing a deliberate
ignore-rule review before committing sanitized continuity.

## Migrate preserved files

Ask the agent in that project:

```text
Follow .harness/releases/4.2.0/docs/workflows/optimization.md in check mode.
Prepare a read-only migration proposal preserving my project routes, commands,
content instructions, active constraints, unresolved tasks, and continuity.
```

Review the actual diff, before hashes, validation, private backups, and rollback
steps. Then ask it to apply **that reviewed proposal**. The workflow rechecks
hashes, validates the compact entries and routes, and records `.agent/OPTIMIZATION.md`.
An intervening edit requires reconciliation before any affected apply. Check mode
writes nothing, including receipts. The semantic migration is an agent workflow;
there is no automatic semantic merger or model/effort optimizer.

Use the explicit versioned policy path above even if an older customized Optimize
skill or `docs/workflows/optimization.md` was preserved. A newly installed Codex
`$possibnow-optimize` skill also routes to the current snapshot. Claude's plugin
command uses the policy bundled with that installed plugin version.

## Rollback

To undo an installation that has not subsequently been edited:

```bash
python3 .harness/releases/4.2.0/tools/rollback.py . --receipt .harness/releases/4.2.0/INSTALL.json
```

This checks all created-file hashes first, removes only files listed in that
receipt, and retains pre-existing/unrelated files. If a created file has changed,
it refuses before deleting anything; preserve/reconcile that work first. This
undoes installation, not a later reviewed semantic migration. For that migration,
use the exact private backup and before/after hash steps in OPTIMIZATION.md; restore
only reviewed files after checking intervening edits. Never reset the entire repo.

## Guidance and state ownership

| Location | Purpose and load trigger |
| --- | --- |
| AGENTS.md / CLAUDE.md | Stable project identity, commands, boundaries, explicit task routes |
| docs/workflows/delivery.md | Implementation, TDD/evals, validation/security, review, Git delivery |
| docs/workflows/contracts.md | Checkpoint preparation, exact archival, history, shared continuity |
| docs/workflows/content.md | Content tasks; retain the project's editorial routes and acceptance |
| docs/workflows/learning.md | Requested/enabled learning; authoritative modes and promotion gate |
| docs/workflows/optimization.md | Read-only proposal and reviewed migration apply |
| docs/workflows/clients.md | Actual client discovery, precedence, enforcement status and limits |
| PLAN / existing TASKS and CONTEXT | Active work, acceptance criteria, assumptions and task detail |
| HANDOFF | One current checkpoint with unresolved work and active constraints |
| HISTORY + linked archives | Complete previous checkpoints, retrieved individually |
| LEARNINGS | Separate unapproved candidates and adopted reusable lessons |

Ordinary questions and read-only checks do not start the full delivery pipeline.
No root eagerly imports the handbook, histories, or skill library. Specialized
roles, vendor references, Graphify, wiki, and cost guidance load only for their
matching tasks. [Rule ownership](docs/architecture/rule-ownership.md) maps the
former inline rules to their authoritative homes.

HANDOFF preparation requires reviewing the whole prior checkpoint and authoritative
current state, retaining unresolved tasks and active constraints regardless of age.
The `checkpoint.py` helper preserves exact prior bytes in a hash-addressed archive
linked from HISTORY, verifies it, and checks for intervening edits before replacement.
It deduplicates identical archives. Existing inline/legacy histories stay intact.
Semantic completeness and secret sanitization require review; the helper cannot infer them.

Learning defaults to **OFF** (no entries). **CAPTURE** permits bounded candidates
and evidenced lessons; candidates have no standing authority. Promotion requires
two distinct evidenced recurrences or explicit user confirmation, plus the future
action changed. **APPLY** may propose policy/skill/plugin edits; only separately
authorized edits are applied. Consolidate or retire stale lessons. No automatic
learning service, diary, or background instruction editing is installed.

## Client integrations

- Codex: project skills under `.agents/skills`; invoke `$possibnow-scale`,
  `$possibnow-guardrails`, or `$possibnow-optimize`. Init lives in this source clone
  as `$possibnow-init /path/to/project`, where its installer is available.
- Claude Code: plugin `/possibnow-dev-harness:init`, `:scale`, `:guardrails`, and
  `:optimize`; project workflow skills under `.claude/skills`.
- Cursor and other clients: follow explicit workflow paths using their supported
  instruction discovery. Harness-specific skill/command integration is unverified.

Claude plugin installation (marketplace publication is separate from this release):

```text
/plugin marketplace add PossibLaw/PossibLaw-Plugins
/plugin install possibnow-dev-harness@possiblaw-plugins
```

Markdown is advisory. Enabled Claude plugin hooks enforce their tested subset of
command/file rules; they do not protect Codex, Cursor, or other clients. Project
installation alone adds no runtime hooks. Native permissions remain client-owned.
Optional Tier 2 hooks stay off by default. [Client details and official sources](packs/project/docs/workflows/clients.md)
list enforced/advisory/unsupported/unverified boundaries. Live client behavior for
this release remains UNCONFIRMED; unit tests are not proof of session enforcement.

## Source development and advanced use

```bash
./scripts/install-project.sh /path/to/project --adopt --dry-run
./scripts/install-project.sh /path/to/project --name "Project" --test "make test"
python3 scripts/render_entries.py
./scripts/verify-pack.sh
```

Stack commands are suggestions from manifests, not tested facts. `--primary`,
`--test`, `--lint`, `--typecheck`, `--build`, `--name`, and `--owner` customize new
candidates; they never rewrite a preserved project file. For repeat installs use
the same ref/options. A conflicting same-version snapshot requires reconciliation
or receipt-based rollback before regenerating it.

Author roots in `packs/entry.md`; the renderer produces the two shipped adapters.
The line validator counts LF/CRLF and an unterminated last line. It also rejects
eager @file imports. It does not inspect the user's pre-existing global instructions,
client rules, memories, or plugins. Do not minify or merge paragraphs to evade the cap.

Validation uses disposable repositories and the unchanged guardrail regression
suite. No installed real project is a test fixture. Release receipts distinguish
lines, words, and bytes, and mark live behavior UNCONFIRMED when not exercised.
Optional global defaults under packs/global and install-global.sh are separate;
this project update does not run them. No memory backend or new client runtime
adapter is introduced. The former plugin id was possiblaw-starter; historical
release notes retain that name for provenance.
