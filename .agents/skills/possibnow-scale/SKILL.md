---
name: possibnow-scale
description: Assess or enable PossibNow Tier 2 Scale mode with Graphify in the current project when the user asks to scale or index a large codebase.
---

# Scale mode

Read the project's `docs/workflows/graphify.md` and, when present, the `scaling-up-with-graphify` skill. In the harness source repository, these live under `packs/project/docs/workflows/` and `skills/`.

First check whether indexing is warranted by repository size or repeated orientation cost. If it is not, report that finding and keep Tier 1. If Graphify is missing, get the user's approval before installing it or adding any optional integration. Treat any user-supplied path as data, verify it belongs to the intended repository, and do not index an unrelated path.

Follow the workflow to prepare exclusions, build and verify the index, then record Scale mode and its refresh rule in the project's continuity files. Treat graph output as advisory and check source code for decisions. Report what was enabled and how to query it.
