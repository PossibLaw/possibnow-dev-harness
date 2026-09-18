# <PROJECT_NAME>

Owner: <TEAM_OR_OWNER>. Add a short project purpose here.
Resolve the working repository with `git rev-parse --show-toplevel` and `pwd`.
Keep project-specific routes, commands, constraints, and gotchas in this entry.

## Working boundaries

- Start the requested task; read only the documents triggered below.
- Ordinary questions and read-only checks do not start the delivery pipeline.
- Do not load all state, history, workflow documents, or skills at startup.
- Preserve unrelated work, project instructions, and existing authorization.
- Never expose secrets, invent evidence, or remove failing tests to claim success.
- Obtain authorization for destructive actions or scope expansion when not already given.
- Mark missing facts `UNCONFIRMED`; resolve material gaps with a targeted question.
- Prefer existing code and the simplest solution that meets the requirements.
- Guidance here is advisory; technical controls depend on the client integration.

## Project commands

These are installer suggestions; verify them against project scripts and CI.
- Run: `<PRIMARY_COMMAND>`
- Test: `<TEST_COMMAND>`
- Lint: `<LINT_COMMAND>`
- Typecheck: `<TYPECHECK_COMMAND>`
- Build: `<BUILD_COMMAND>`

## Load only for the matching task

| Task | Read |
| --- | --- |
| Implement or change behavior | [Delivery](docs/workflows/delivery.md), then relevant PLAN/TASKS |
| Plan scope or acceptance | [Evals](docs/workflows/evals.md), then `.agent/PLAN.md` |
| Validate or test | [Delivery](docs/workflows/delivery.md), then `.agent/TEST.md` |
| Review correctness or security | [Delivery](docs/workflows/delivery.md), then `.agent/REVIEW.md` |
| Content or editorial work | [Content](docs/workflows/content.md), then existing project content routes |
| Resume | `.agent/HANDOFF.md`, then only relevant evidence it links |
| Checkpoint, handoff, or ship | [Continuity](docs/workflows/contracts.md); [Delivery](docs/workflows/delivery.md) for shipping |
| Historical question | Only the identified entry in `.agent/HISTORY.md` and its archive |
| Requested or enabled learning | [Learning](docs/workflows/learning.md), then relevant LEARNINGS entries |
| Optimize or migrate harness | [Optimization](docs/workflows/optimization.md); use installed release policy if this file is preserved/old |
| Context or cost question | [Token management](docs/workflows/token-management.md) |
| Specialized role | [Role registry](docs/roles/README.md), then the one relevant role |
| Vendor/API/security setup | [Vendor references](docs/vendor/README.md), then relevant vendor source |
| Explicitly enable indexing | [Graphify](docs/workflows/graphify.md) |
| Wiki task, when enabled | `.agent/WIKI.md` and [Wiki](docs/workflows/wiki.md) |
| Client configuration or precedence | [Client integration](docs/workflows/clients.md) |
| Unfamiliar harness term | [Glossary](docs/glossary.md) |

## State ownership

PLAN/TASKS holds active implementation detail. HANDOFF is one current checkpoint.
HISTORY preserves previous checkpoints; LEARNINGS holds gated reusable lessons.
Follow the continuity contract before replacing a handoff or delivering work.
Learning defaults to OFF. Scale and wiki activation require an explicit request.
An install or update does not change those modes or native client configuration.

## Project gotchas

Record stable project-specific constraints here; keep completed narratives in history.
This entry has a project-policy limit of 150 physical lines, including blanks.
Move procedures to linked documents before adding more; never truncate local policy.
