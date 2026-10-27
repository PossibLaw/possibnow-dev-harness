#!/usr/bin/env python3
"""Morning brief: one short Slack message built from Sal's board.

Usage:
    morning-brief.py --config PATH [--triage-state PATH] [--state PATH] [--dispatch-state PATH] [--dry-run]

Sal, October 27, 2026 (issue "How I do work"): the nightly posts were too long to read on a phone; the one
that worked was the autonomous-run notice, one line with a link. He wants "the top 10 things that need to
get done ... today and then this week", each with what it is, the repo, the priority and a link, plus the
board. Each run:
1. applies the automatic moves (scripts/board_rules.py): issue closed → Done, an open linked pull request →
   Needs your review, an autonomous run the dispatcher started → Being worked on; each is recorded as the
   agent's in the board state;
2. Overnight: one line per open pull request carrying `pr_label` opened since the last posted brief;
3. at most 10 cards, Today first, then This week, each by priority then age, and "+N more on the board";
4. a closing line counting cards in Needs your decision and triage's stale or duplicate issues, and the
   board link;
5. posts to $SLACK_WEBHOOK_URL; only a posted brief moves the `reported` mark that opens the next window.
`--dry-run` prints the message and writes and posts nothing.

Config: the same private file as scripts/plan-board.py. Standard library only; GitHub through `gh`.
Exit 2 on a bad config or a board that is not set up; 0 otherwise.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from board_github import load_board, setup_gaps, write  # noqa: E402
from board_rules import PRIORITIES, automatic_changes, triage_problem  # noqa: E402

LIMIT = 10


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except ValueError:
        return {}


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def overnight(repos: list[dict], label: str, since: dt.datetime) -> tuple[list[str], list[str]]:
    lines, errors = [], []
    for repo in repos:
        res = subprocess.run(["gh", "api", f"repos/{repo['github']}/pulls?state=open&sort=created&direction=desc&per_page=50"],
                             capture_output=True, text=True, timeout=60)
        if res.returncode != 0:
            errors.append(f"{repo['name']}: {res.stderr.strip()[:120]}")
            continue
        for p in json.loads(res.stdout or "[]"):
            created = dt.datetime.fromisoformat(p["created_at"].replace("Z", "+00:00"))
            if created <= since or label not in {l["name"] for l in p.get("labels", [])}:
                continue
            title = esc(p["title"].removeprefix("[auto] "))
            lines.append(f"• Autonomous run finished: {title} ({repo['name']}). Ready for your review: <{p['html_url']}|pull request #{p['number']}>")
    return lines, errors


def post_slack(text: str) -> str:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return "slack: SLACK_WEBHOOK_URL not set; not posted"
    req = urllib.request.Request(url, data=json.dumps({"text": text}).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=20)
        return "slack: posted"
    except Exception as exc:  # noqa: BLE001
        return f"slack: failed ({exc})"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--triage-state", type=Path, default=Path.home() / ".agents" / "triage-state.json")
    ap.add_argument("--state", type=Path, default=Path.home() / ".agents" / "board-state.json")
    ap.add_argument("--dispatch-state", type=Path, default=Path.home() / ".agents" / "dispatch-state.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    try:
        cfg = json.loads(args.config.expanduser().read_text(encoding="utf-8"))
        owner, number, repos, board_url = cfg["owner"], int(cfg["number"]), cfg["repos"], cfg["url"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"BLOCKED: bad config {args.config}: {exc}", file=sys.stderr)
        return 2
    names = {r["github"].lower(): r["name"] for r in repos}
    state_path = args.state.expanduser()
    state = load_json(state_path)
    now = dt.datetime.now(dt.timezone.utc)
    try:
        since = dt.datetime.fromisoformat(state["reported"])
    except (KeyError, ValueError):
        since = now - dt.timedelta(days=1)

    notes, cards = [], []
    try:
        board = load_board(owner, number, cfg.get("owner_type", "user"))
    except RuntimeError as exc:
        board = None
        notes.append(f"Could not read the board ({esc(str(exc))}).")
    if board is not None:
        gaps = setup_gaps(board)
        if gaps:
            print("BLOCKED: board not set up; run plan-board.py --setup\n" + "\n".join(f"- {g}" for g in gaps), file=sys.stderr)
            return 2
        cards = [c for c in board.cards if c.repo.lower() in names]
        for c in cards:
            c.key = c.key.lower()
        started = {s.get("url") for s in load_json(args.dispatch_state.expanduser()).get("started", [])}
        for ch in automatic_changes(cards, started):
            card = next(c for c in cards if c.key == ch.key)
            if args.dry_run:
                print(f"- would move {ch.key} to {ch.value}")
            else:
                try:
                    write(board, ch)
                except RuntimeError as exc:
                    notes.append(f"Could not move {esc(card.title)} to {ch.value} ({esc(str(exc))[:80]}).")
                    continue
                state.setdefault("cards", {}).setdefault(ch.key, {})["Status"] = ch.value
            card.status = ch.value

    triage = load_json(args.triage_state.expanduser())
    if triage_problem(triage, dt.datetime.now()):
        notes.append("Triage did not run cleanly last night; priorities and the plan were left as they were.")
    runs, errors = overnight(repos, cfg.get("pr_label", "agent-auto"), since)
    notes += [f"Could not read pull requests for {e}." for e in errors]

    def order(c):
        return (PRIORITIES.index(c.priority) if c.priority in PRIORITIES else len(PRIORITIES), c.created)

    open_cards = [c for c in cards if c.state == "OPEN"]
    today = sorted([c for c in open_cards if c.status == "Today"], key=order)
    week = sorted([c for c in open_cards if c.status == "This week"], key=order)
    lines = [f"*Morning brief: {dt.datetime.now().strftime('%A, %B %d')}*", *notes]
    lines += (["*Overnight*", *runs] if runs else ["Overnight: nothing finished."])
    shown = 0
    for head, group in (("*Today*", today), ("*This week*", week)):
        take = group[:LIMIT - shown]
        if take:
            lines.append(head)
            for c in take:
                shown += 1
                lines.append(f"{shown}. <{c.url}|{esc(c.title)}> · {esc(names[c.repo.lower()])} · {c.priority or 'No priority'}")
    if not shown:
        lines.append("Nothing planned yet; open the board to pick.")
    if len(today) + len(week) > shown:
        lines.append(f"+{len(today) + len(week) - shown} more on the board")
    decisions = sum(1 for c in open_cards if c.status == "Needs your decision")
    stale = sum(1 for v in triage.get("issues", {}).values() if v.get("outcome") in ("stale", "duplicate"))
    lines.append(f"{decisions} decisions waiting · {stale} look stale. Reply in Claude to answer (\"brief 1A\", \"close stale\").")
    lines.append(f"<{board_url}|Open the board>")
    text = "\n".join(lines)
    print(text)
    if args.dry_run:
        return 0
    slack_line = post_slack(text)
    print(slack_line)
    if slack_line == "slack: posted":
        state["reported"] = now.isoformat(timespec="seconds")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
