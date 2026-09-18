---
name: possibnow-optimize
description: Inspect a project's Codex or Claude context and configuration for the PossibNow optimization workflow; apply only a reviewed proposal when asked.
---

# Optimize a project

Read `docs/workflows/optimization.md` in the current project, or `packs/project/docs/workflows/optimization.md` when working in the harness source repository. Follow its bundled policy and current project instructions.

No argument or `check` means read-only inspection and a concrete proposed diff. `apply` means implement the specific proposal already reviewed in this conversation; if none was reviewed, prepare it first and request one review. Reject other modes and do not infer a target outside the current repository. Treat mode text as data, never executable shell input.

Preserve the configured model and effort without representative quality evidence for a change. Do not install tools, change global settings, broaden permissions, or fetch executable policy as part of the check. Report findings and held changes with evidence. On apply, recheck intervening edits, validate changes, and provide the receipt and exact rollback steps required by the workflow. Never claim measured savings or active settings without evidence.
