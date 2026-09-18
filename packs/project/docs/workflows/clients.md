# Client integration and limits

Reviewed against official documentation on 2026-09-18. A Markdown rule is
**advisory**, even when a client automatically reads it. Enforcement claims
below apply only to the named mechanism. Live client behavior for this release
is **UNCONFIRMED** unless a release receipt names an actual client test.

| Client | Discovery and precedence | Workflow invocation | Technical controls and limits |
| --- | --- | --- | --- |
| Codex | Global/project AGENTS layers; override files and nearer directory instructions can take precedence. Inspect the effective chain. | Project skills in `.agents/skills`, `$skill-name`, or explicit workflow path. | Harness Markdown advisory. This pack installs no Codex hook/permission adapter. Claude hooks unsupported here; native Codex settings remain user-owned. Live invocation UNCONFIRMED. |
| Claude Code | CLAUDE.md hierarchy, path-scoped rules, and explicit imports can add context. The harness root contains no eager imports. | Plugin `/possibnow-dev-harness:*` commands or local `.claude/skills`. | **Enforced when enabled:** Claude plugin hooks cover the tested subset of Bash/file checks; project-file installation alone adds no hooks. Native permissions remain user-owned. Live plugin behavior UNCONFIRMED for this release. |
| Cursor | Root and nested AGENTS.md are combined, with more specific directory instructions taking precedence. User/team/project Cursor rules can also apply; inspect those separately. | Explicitly ask to follow a workflow path. Harness-specific command/skill discovery unverified. | Markdown advisory; no harness runtime adapter shipped. Claude hooks unsupported here. Live integration UNCONFIRMED. |
| Other clients | Consult their own documented instruction discovery. | Explicit workflow path if file/tool access permits. | Advisory or unsupported; unverified until tested. |

## Inspect effective startup

The generated entries contain task routes, not automatic imports. The shared
source produces two adapters; detailed procedures are opened only for matching
tasks. Source verification rejects eager file imports in either entry. This checks
the shipped roots, not all pre-existing global instructions, rules, automatic
memories, parent directories, nested overrides, or plugin metadata in a live client.
Inspect those layers during a client-specific optimization check. Do not rewrite
them, disable memory, or relax permissions as an incidental harness update.

Claude import syntax and client discovery are not portable. Avoid copying a host's
global paths, native configuration keys, or hook claims into shared workflows.
A helper invoked from any client can enforce its own byte/hash/file checks; it
does not make all of that client's actions subject to a security sandbox.

## Evidence and sources

- [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude memory and imports](https://code.claude.com/docs/en/memory)
- [Claude hooks](https://code.claude.com/docs/en/hooks)
- [Cursor rules](https://cursor.com/docs/rules)

The unchanged tests under tests/guardrails exercise Claude hook scripts directly.
They do not demonstrate active enforcement in every installed client session.
