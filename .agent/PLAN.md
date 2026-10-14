---
contract_version: 1
artifact_type: plan
status: IN_REVIEW
depends_on: []
produces: [eval_ids, release_scope]
feeds_into: [.agent/TEST.md]
memory:
  include_in_memory: true
  tags: [plan]
---

# Unreleased: git guardrail gaps + Pocock-derived skills

Baseline: main 58ba0c0 (v4.2.1 published). Branch: feat/v4.3.0-git-guards-and-pocock-skills.
Source for adopted skills: mattpocock/skills @ 49dd158d1076134a641b33efb035946536778336 (MIT).

Scope: close force-push/branch-delete/discard gaps in `scripts/guardrails/blacklist.py`;
add user-invoked `splitting-work-into-tickets` and `running-a-retro` skills; add
`docs/references/writing-for-agents*.md` as a maintainer-only reference. No version bump,
release pins, installed projects, globals, models, permissions, learning mode, or Scale.
v4.3.0 is cut separately after its publish smoke gate.

## Acceptance and evidence plan

- G1 (happy): `git push origin main`, `push -u origin feature`, `branch -d`, `restore --staged .`, `clean -n` run silently.
- G2 (edge): force-push to main/master is blocked in every spelling (`-f`, trailing `--force`/`-f`, `--force-with-lease`, `+main`, `+HEAD:master`); `git clean -df|-xdf|--force` blocked; `push ... && cd main` stays silent.
- G3 (failure/safety): other force-pushes, `branch -D`, `branch --delete --force`, `checkout .`, `checkout -- .`, `restore .`, `restore --worktree .` ask first.
- S1: installer delivers both new skills to `.claude/skills/` and `.agents/skills/` in a disposable fixture; writing-for-agents is not shipped.
- S2: `scripts/verify-pack.sh` requires both skills and their metadata; full suite green.
