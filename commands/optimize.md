---
description: Inspect this project's context and configuration, prepare an optimization diff, and apply the reviewed proposal without changing unvalidated models.
argument-hint: [check | apply]
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, WebFetch, WebSearch
---

# /possibnow-dev-harness:optimize

Optimize the current repository using the bundled workflow at
`${CLAUDE_PLUGIN_ROOT}/packs/project/docs/workflows/optimization.md`.
Read that file first. It works even before `/init`; do not bootstrap or overwrite
project instructions just to perform the inspection.

Treat `$ARGUMENTS` as data, never executable shell text. No argument, or `check`,
means read-only inspection and a proposed diff. `apply` means apply the specific
proposal already reviewed in this conversation. If no proposal was reviewed,
prepare it first and ask for one review before applying it. Reject other modes
with this usage; do not guess a target outside the current repository.

Honor the user's existing authorization and project instructions. Preserve
current models and effort unless task-specific evaluation evidence qualifies a
change. Do not install tools, change global settings, broaden permissions,
restart agents, stop loops, or fetch executable policy from the research repo.

Return the bundled policy revision, findings with evidence, proposed changes,
held changes and their missing evidence, and the next action. On apply, include
validation receipts and exact rollback instructions. Do not claim measured
savings or successful live configuration without evidence.
