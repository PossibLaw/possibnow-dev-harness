# Memory and Indexing Decision Guide

Use this guide to decide which persistence layer should own a fact, when to turn on optional memory/indexing tools, and how Graphify fits into the PossibNow Dev Harness.

Status: draft decision guide
Last reviewed: 2026-06-29
Graphify source reviewed: https://github.com/safishamsi/graphify

## Short Version

The Dev Harness should stay file-first, and it runs in two tiers: **Tier 1 (Starter, default)** is the everyday file-based workflow; **Tier 2 (Scale, opt-in via `/possibnow-dev-harness:scale`)** adds Graphify indexing and wiki orientation as a codebase grows.

Canonical memory is the local, reviewable file set:
- `.agent/PLAN.md` (goal, assumptions, and task checklist — the former CONTEXT and TASKS are folded in here)
- `.agent/TEST.md`
- `.agent/REVIEW.md`
- `.agent/HANDOFF.md` (current checkpoint)
- `.agent/HISTORY.md` (exact prior handoffs, on demand)

Optional layers must be additive:
- `.agent/LEARNINGS.md` captures reusable process observations only when learning mode is enabled, and a lesson is promoted only after it recurs at least twice or the user confirms it (validation-gated).
- Wiki mode (Tier 2) accelerates orientation, but source code and tests remain authoritative.
- Graphify (Tier 2) is an optional wiki/indexing backend that can generate a graph report, graph JSON, cache, visualization, and optional wiki pages.
- Claude Code native memory is outside the Dev Harness contract and should not become the repo source of truth.
- A retrieval backend such as MemPalace is a deferred future option over completed local artifacts; it is not shipped today.

Default recommendation: keep the current HANDOFF plus historical HISTORY on, keep learnings/wiki/Graphify (Tier 2) off until a repo has enough repeated context load pain to justify them.

## Trust Order

1. Source code, tests, runtime behavior, and committed configuration
2. Active workflow artifacts: `PLAN.md`, `TEST.md`, `REVIEW.md`, `HANDOFF.md` and historical checkpoints in HISTORY
3. Curated repo docs and manually maintained wiki pages with source citations
4. `.agent/LEARNINGS.md`
5. Generated Graphify output and any Claude native memory retrieval (a future MemPalace-style retrieval backend would sit here too)

If any lower layer conflicts with a higher layer, trust the higher layer and update or discard the stale lower-layer claim.

## Layer Responsibilities

| Layer | Default | Main job | Owner | Commit? | Read when | Write when |
| --- | --- | --- | --- | --- | --- | --- |
| `AGENTS.md` / `CLAUDE.md` | On | Stable startup rules and routing | Human-maintained template | Yes | Every agent session | Rarely, for policy changes |
| `.agent/PLAN.md` | On demand | Current objective, assumptions, task checklist, evals, risks | Active task owner | Yes | Planning or task execution | Before implementation |
| `.agent/TEST.md` | On demand | Validation commands, eval receipts, security checks | QA/implementer | Yes | Test/validation work | During verification |
| `.agent/REVIEW.md` | On demand | Review findings and security checklist | Reviewer | Yes | Review work | During review |
| `.agent/HANDOFF.md` | On | Current checkpoint only; old checkpoints archived in HISTORY | Final task owner | Yes | Resume, handoff, parallel worktree | End of meaningful work |
| `.agent/HISTORY.md` | On demand | Exact historical handoffs | Final task owner | Yes | Specific historical question | Before replacing HANDOFF |
| `.agent/LEARNINGS.md` | Off | Reusable observations and proposed improvements (validation-gated) | Agent only when enabled | Yes | Learning mode tasks | CAPTURE/APPLY mode only |
| Manual wiki (Tier 2) | Off | Curated codebase map and concept pages | Agent/human curator | Yes | Deep orientation/repo review | After verified changes |
| Graphify output (Tier 2) | Off | Generated graph/index over code/docs/raw materials | Tool-generated | Usually no | Orientation/query acceleration | Explicit graph refresh |
| Claude native memory | Tool-specific | Personal/global preferences | Claude Code | Outside repo | Personal behavior only | Never for client/repo facts by default |

## How Current Memory Works

### Current Handoff and Historical Handoffs

HANDOFF contains the current checkpoint. HISTORY preserves exact previous
handoffs with identifiers and hashes. Verify archival before replacing current
state; preserve active constraints and legacy historical records. Normal resume
loads HANDOFF only. See the current contract in
`packs/project/docs/workflows/contracts.md` for migration and delivery rules.

### Learnings

`.agent/LEARNINGS.md` is not task memory. It is a controlled improvement queue.

Best capture points:
- sprint closeout
- pre-git-cycle checkpoints
- repeated corrections worth turning into a norm or skill

Use it only when `Learning Mode` is `CAPTURE` or `APPLY`:
- `CAPTURE`: record bounded unapproved candidates or gated lessons with evidence; no policy edits.
- `APPLY`: capture under the same gate and propose policy changes; apply only authorized edits.

Do not use learnings for:
- ordinary task status
- decisions needed by the current implementation
- codebase maps
- client facts
- facts that belong in source docs or tests

### Retrieval Backend (deferred future option)

A semantic retrieval backend over completed local artifacts (for example MemPalace) is a **deferred future option**. It is **not shipped today** — there are no ingest stubs or hooks in the pack.

If such a backend is added later, the principles still hold: completed file artifacts remain the source of truth, retrieval is advisory, retrieved entries must cite the source artifact path and timestamp, and the backend must never become a second writable truth store. The write path would stay: complete local artifacts → update the canonical `HANDOFF.md` (current checkpoint with a verified archive in HISTORY) → ingest the completed artifacts → verify retrieval against current local files and source code.

### Manual Wiki

The current wiki workflow is a persistent codebase orientation layer. It is for maps, concepts, domain glossary, architecture summaries, and links between files.

Use it when:
- sessions repeatedly spend time rediscovering the same codebase structure
- a repo has enough moving parts that a map saves time
- a review needs a broad starting point before targeted source verification

Keep manual wiki pages citation-heavy:
- source paths or URLs
- last verified date
- confidence level
- explicit `UNCONFIRMED` markers

### Graphify

Graphify should fit as an optional wiki backend, not a replacement for the Dev Harness workflow.

From the upstream README reviewed on 2026-04-10, Graphify can read a folder of code, docs, papers, screenshots, diagrams, and images, then produce `graphify-out/` with a graph visualization, `GRAPH_REPORT.md`, `graph.json`, and cache. It supports `.graphifyignore`, labels relationships as extracted/inferred/ambiguous, has query/path/explain commands, can generate an agent-crawlable wiki with `--wiki`, and has assistant install commands for Codex and Claude Code. It also documents always-on assistant hooks and git hooks.

Dev Harness policy should narrow that:
- Graphify is allowed only when `.agent/WIKI.md` sets `Wiki backend: graphify`.
- Use Graphify output for orientation and focused graph queries.
- Do not install always-on assistant hooks without explicit user approval.
- Do not install Graphify git hooks without explicit user approval.
- Do not run watch mode by default.
- Before graphing, create or verify `.graphifyignore`.
- Exclude secrets, `.env*`, generated files, dependency/vendor folders, build outputs, caches, logs, private client exports, and raw client data.
- Treat `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json`, generated wiki pages, and query results as advisory until verified against source code.

Recommended default generated-output policy:
- keep `graphify-out/` local unless the team explicitly decides to commit it
- commit `.graphifyignore` only if it contains project-safe exclusions
- never commit generated output that may include client facts, secrets, or proprietary source summaries

### Claude Code Native Memory

Claude Code memory can be useful for stable personal preferences, but it should not be part of the Dev Harness's repo memory model.

Use it for:
- user-level communication preferences
- stable personal workflow defaults

Do not use it for:
- repo decisions that should be visible in files
- client facts
- API secrets or credentials
- source-code claims
- task status

If Claude memory conflicts with repo files, repo files win.

## Where Each Fact Should Go

| Fact type | Put it here | Not here |
| --- | --- | --- |
| Current task objective | `.agent/PLAN.md` | Wiki, Graphify, Claude memory |
| Current next action | `.agent/HANDOFF.md` (Current Baton) | Learnings, Graphify |
| Test command and receipt | `.agent/TEST.md` | Timeline-only notes |
| Review finding | `.agent/REVIEW.md` | Wiki-only notes |
| "What happened last session" | `.agent/HISTORY.md` | `AGENTS.md`, `CLAUDE.md` |
| Reusable process improvement | `.agent/LEARNINGS.md` | Handoff baton/timeline |
| Architecture overview | Manual wiki or generated Graphify report | Handoff |
| Source-backed codebase map | Manual wiki or Graphify, with source verification | Claude memory |
| Stable repo policy | `AGENTS.md` / `CLAUDE.md` / workflow docs | History |
| Personal preference | Tool-native user memory | Repo docs |

## Narrowing Recommendations

### Baseline For Most Repos

Keep:
- `AGENTS.md` and `CLAUDE.md`
- `.agent/PLAN.md`, `.agent/TEST.md`, `.agent/REVIEW.md`, `.agent/HANDOFF.md`, `.agent/HISTORY.md`
- `docs/workflows/contracts.md`
- `docs/workflows/token-management.md`
- `docs/workflows/wiki.md`

Default off (Tier 2 or future):
- `.agent/LEARNINGS.md`
- manual wiki (Tier 2)
- Graphify (Tier 2)
- a future retrieval backend (e.g. MemPalace)
- Claude native memory for repo facts

### Add Manual Wiki When

- the same codebase overview is needed repeatedly
- the repo has stable concepts worth curating
- humans want editable Obsidian-style pages

Manual wiki is the first optional indexing layer because it is simple, file-based, reviewable, and easy to prune.

### Add Graphify When

- the repo is large enough that manual wiki creation is slow
- you need a quick first-pass map over code/docs/raw materials
- graph queries would save more time than maintaining hand-written pages
- generated output can be safely kept local or reviewed before commit

Graphify should produce input to wiki mode, not new policy. Its report can seed manual wiki pages after verification.

For non-developer users, the intended prompt is simple:

```text
Index this codebase with Graphify.
```

The agent should then follow the Graphify Indexing Request Contract in `docs/workflows/graphify.md`: enable Graphify in `.agent/WIKI.md`, create safe ignore rules, ask before installing missing tooling, run a one-time graph build, and report the generated output paths.

### Consider a Retrieval Backend Later (deferred)

A semantic retrieval backend (e.g. MemPalace) is not shipped today. It would only be worth revisiting when:

- the team needs retrieval across many completed tasks
- file search through the HISTORY entries and handoffs is no longer enough
- the backend can retrieve verbatim snippets with artifact citations

Any such backend should index completed artifacts, not raw repo content by default.

### Use Claude Native Memory Sparingly

Do not depend on it for repo continuity. It is not shared, reviewable, or guaranteed to match local files.

## Suggested Operating Model

```yaml
memory_model:
  tier: 1 # 1 (Starter, default) | 2 (Scale, opt-in via /possibnow-dev-harness:scale)
  source_of_truth:
    - source_code
    - tests
    - runtime_behavior
    - .agent/PLAN.md
    - .agent/TEST.md
    - .agent/REVIEW.md
    - .agent/HANDOFF.md
  session_timeline: .agent/HISTORY.md # Historical checkpoints loaded on demand
  learning_mode: OFF # OFF | CAPTURE | APPLY (validation-gated promotion)
  wiki_mode: OFF # OFF | ON (Tier 2)
  wiki_backend: manual # manual | graphify (Tier 2)
  retrieval_backend: none # deferred future option (e.g. MemPalace)
  claude_native_memory_for_repo_facts: OFF
```

## Decision Questions

Use these before adding or enabling a memory/indexing layer:

1. What repeated work will this remove?
2. What file remains the source of truth?
3. Is the output local, reviewable, and easy to delete?
4. Could the output contain client data, secrets, or proprietary summaries?
5. Who updates stale claims?
6. What command verifies generated claims against source?
7. What is the off switch?

If any answer is unclear, keep the layer off.

## Proposed Dev Harness Direction

1. Keep the file-based contract pipeline as canonical (Tier 1).
2. Keep learnings, manual wiki, and Graphify default-off; gate Graphify/wiki behind Tier 2 (`/possibnow-dev-harness:scale`). A retrieval backend (e.g. MemPalace) stays a deferred future option, not shipped today.
3. Add `Wiki backend: manual | graphify` to `.agent/WIKI.md`.
4. Treat Graphify as a backend for wiki/index generation, with no always-on hooks unless explicitly approved.
5. Do not add Ix to the Dev Harness for now.
6. Prefer pruning duplicate memory over adding another backend.
7. Require generated indexes to cite source files and be verified before they influence implementation.

Current normative learning policy: packs/project/docs/workflows/learning.md. Historical research below earlier dates is evidence, not an instruction to enable learning or integrations.
