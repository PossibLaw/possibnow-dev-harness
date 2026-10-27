#!/usr/bin/env python3
"""Nightly board pass, after triage: priorities, decisions and the proposed plan on Sal's GitHub Project.

Usage:
    plan-board.py --config PATH [--triage-state PATH] [--state PATH] [--dry-run] [--setup] [--answered KEY]

Sal, October 27, 2026 (issue "How I do work"): TickTick did not show him what to work on; he wants a board
he can drag cards on, an agent that suggests priorities and proposes Today and This week, and his moves to
stick. Each run:
1. reads the board (scripts/board_github.py) and the triage state (scripts/triage-issues.py);
2. changes nothing when the triage state is missing, older than 36 hours, or the classifier failed;
3. for each open issue card in a configured repository, applies scripts/board_rules.py: Priority from the
   `urgent`/`important` labels with the triage reason in `Why`; decisions to "Needs your decision" with the
   question in `Decision`; the top `do`/`agent` issues into Today and This week around Sal's own cards;
4. records each value it wrote in the state file, only after the write succeeded. A value that no longer
   matches the record is Sal's and is never changed again.
`--setup` creates the Priority, Why and Decision fields and prints the steps only Sal can do in the GitHub
UI. `--answered KEY` (owner/repo#n) moves an answered decision back to Backlog; the
answering-the-morning-brief skill calls it. `--dry-run` writes nothing.

Config (JSON, private): {"owner": "...", "owner_type": "user", "number": 1, "url": "https://github.com/...",
  "plan": {"today": 3, "total": 10}, "repos": [{"name": "Aleph", "github": "Owner/repo"}], "pr_label": "agent-auto"}
Standard library only; GitHub through `gh` (needs the `project` scope). Exit 2 on a bad config or a board
that is not set up; 0 otherwise.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from board_github import create_fields, load_board, setup_gaps, write  # noqa: E402
from board_rules import Change, plan_changes  # noqa: E402

UI_STEPS = ("In the GitHub board, add a Board view: New view → Board, columns by Status, sorted by Priority. "
            "Then rerun plan-board.py --setup until nothing is missing.")


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except ValueError:
        return {}


def triage_problem(triage: dict, now: dt.datetime) -> str | None:
    if not triage.get("ran"):
        return "no triage state; the board was left as it was"
    if triage.get("classifier_ok") is False:
        return "the triage classifier failed last night; the board was left as it was"
    ran = dt.datetime.fromisoformat(triage["ran"]).replace(tzinfo=None)
    if now - ran > dt.timedelta(hours=36):
        return f"the triage state is older than 36 hours ({triage['ran']}); the board was left as it was"
    return None


def apply(board, changes: list[Change], state: dict, dry_run: bool) -> tuple[int, list[str]]:
    failed = []
    for ch in changes:
        if dry_run:
            print(f"- would set {ch.key} {ch.field} = {ch.value}")
            continue
        try:
            write(board, ch)
        except RuntimeError as exc:
            failed.append(f"{ch.key} {ch.field}: {exc}")
            continue
        state.setdefault("cards", {}).setdefault(ch.key, {})[ch.field] = ch.value
    return len(changes) - len(failed), failed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--triage-state", type=Path, default=Path.home() / ".agents" / "triage-state.json")
    ap.add_argument("--state", type=Path, default=Path.home() / ".agents" / "board-state.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--setup", action="store_true", help="create the board's fields and list the UI steps")
    ap.add_argument("--answered", metavar="KEY", help="owner/repo#n of a decision Sal answered: back to Backlog")
    args = ap.parse_args(argv)
    try:
        cfg = json.loads(args.config.expanduser().read_text(encoding="utf-8"))
        owner, number, repos = cfg["owner"], int(cfg["number"]), cfg["repos"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"BLOCKED: bad config {args.config}: {exc}", file=sys.stderr)
        return 2
    owner_type = cfg.get("owner_type", "user")
    try:
        board = load_board(owner, number, owner_type)
    except RuntimeError as exc:
        print(f"board: could not read {owner}/{number}: {exc}")
        return 0

    if args.setup:
        if args.dry_run:
            print("board: would create any missing Priority, Why and Decision fields")
        else:
            created = create_fields(owner, number, board)
            print(f"board: created: {', '.join(created) if created else 'nothing (all fields exist)'}")
            board = load_board(owner, number, owner_type)
        for gap in setup_gaps(board):
            print(f"- {gap}")
        print(f"- {UI_STEPS}")
        return 0
    gaps = setup_gaps(board)
    if gaps:
        print("BLOCKED: board not set up; run plan-board.py --setup\n" + "\n".join(f"- {g}" for g in gaps), file=sys.stderr)
        return 2

    state_path = args.state.expanduser()
    state = load_json(state_path)
    configured = {r["github"].lower() for r in repos}
    cards = [c for c in board.cards if c.repo.lower() in configured]
    for c in cards:
        c.key = c.key.lower()
    now = dt.datetime.now()

    if args.answered:
        card = next((c for c in cards if c.key == args.answered.lower()), None)
        if card is None:
            print(f"board: {args.answered} is not on the board")
            return 0
        changes = [Change(card.item_id, card.key, "Status", "Backlog")] if card.status != "Backlog" else []
    else:
        triage = load_json(args.triage_state.expanduser())
        problem = triage_problem(triage, now)
        if problem:
            print(f"board: {problem}")
            return 0
        verdicts = {"issues": {k.lower(): v for k, v in triage.get("issues", {}).items()}}
        plan = cfg.get("plan") or {}
        changes = plan_changes(cards, verdicts, state, int(plan.get("today", 3)), int(plan.get("total", 10)))

    done, failed = apply(board, changes, state, args.dry_run)
    by_field = Counter(ch.field for ch in changes)
    counts = ", ".join(f"{f} {by_field[f]}" for f in ("Status", "Priority", "Why", "Decision"))
    verb = "would make" if args.dry_run else "made"
    print(f"board: {verb} {len(changes)} changes ({counts}); {len(failed)} failed")
    for f in failed[:5]:
        print(f"- failed: {f}")
    if not args.dry_run:
        state["planned"] = now.isoformat(timespec="seconds")
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
