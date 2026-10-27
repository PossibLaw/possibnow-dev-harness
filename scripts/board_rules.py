"""Rules for Sal's board: who owns a card's column and priority, the nightly plan, and automatic moves.

Sal, October 27, 2026 (issue "How I do work"): the agent suggests a priority for every issue and
proposes Today and This week; his moves stick. A value is the agent's while it still equals what the
agent last wrote or last saw (the state file records that); with no record, an empty or Backlog column and
an empty priority are the agent's. Anything else is Sal's: the record then says SAL and the plan leaves it
alone for good, even if Sal later moves it back. An automatic move or an answered decision records anew.
An empty column or priority is always the agent's: dragging a card to "No Status" (or clearing its
Priority) is how Sal hands it back. Automatic moves describe
facts (a pull request is open, the issue closed, an autonomous run started) and always apply.
Pure functions; scripts/board_github.py reads and writes the board.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

STATUSES = ("Backlog", "Needs your decision", "This week", "Today", "Being worked on", "Needs your review", "Done")
PRIORITIES = ("Urgent", "High", "Medium", "Low")
UNCLAIMED = {"Status": (None, "Backlog"), "Priority": (None,)}
FACTS = ("Being worked on", "Needs your review", "Done")
SAL = "(sal)"


@dataclass
class Card:
    item_id: str
    key: str
    url: str
    title: str
    repo: str
    state: str
    created: str
    labels: set[str] = field(default_factory=set)
    status: str | None = None
    priority: str | None = None
    why: str | None = None
    decision: str | None = None
    open_prs: list[str] = field(default_factory=list)


@dataclass
class Change:
    item_id: str
    key: str
    field: str
    value: str


def priority_from_labels(labels: set[str]) -> str:
    urgent, important = "urgent" in labels, "important" in labels
    return "Urgent" if urgent and important else "High" if important else "Medium" if urgent else "Low"


def is_agents(current: str | None, recorded: dict, field: str) -> bool:
    if current is None:
        return True
    if field in recorded:
        return recorded[field] != SAL and current == recorded[field]
    return current in UNCLAIMED[field]


def ownership_marks(cards: list[Card], state: dict) -> dict[str, dict]:
    """What to record for each open card before planning: the value it holds if it is the agent's, SAL if not."""
    records = state.get("cards", {})
    marks = {}
    for c in cards:
        if c.state != "OPEN":
            continue
        rec = records.get(c.key, {})
        marks[c.key] = {f: (cur if is_agents(cur, rec, f) else SAL) for f, cur in (("Status", c.status), ("Priority", c.priority))}
    return marks


def decision_text(decision: dict) -> str:
    parts = [decision.get("question") or "Decide how to proceed.", *(decision.get("options") or []),
             f"Recommend {decision.get('recommend', 'A')}"]
    return " · ".join(parts)[:1000]


def plan_changes(cards: list[Card], triage: dict, state: dict, today_cap: int, total_cap: int) -> list[Change]:
    verdicts, records = triage.get("issues", {}), state.get("cards", {})
    out: list[Change] = []

    def emit(c: Card, fld: str, value: str, current):
        if value != current:
            out.append(Change(c.item_id, c.key, fld, value))

    live = [(c, verdicts[c.key], records.get(c.key, {})) for c in cards if c.state == "OPEN" and c.key in verdicts]
    rank: dict[str, str] = {}
    for c, v, rec in live:
        if is_agents(c.priority, rec, "Priority"):
            rank[c.key] = priority_from_labels(c.labels)
            emit(c, "Priority", rank[c.key], c.priority)
            emit(c, "Why", f"Agent: {v.get('why', '')}", c.why)
        else:
            rank[c.key] = c.priority or "Low"

    sal_today = sal_week = 0
    candidates, rest = [], []
    for c, v, rec in live:
        outcome = "do" if v.get("outcome") == "decide" and rec.get("answered") else v.get("outcome")
        if not is_agents(c.status, rec, "Status"):
            sal_today += c.status == "Today"
            sal_week += c.status == "This week"
            continue
        if c.status in FACTS:
            continue
        if outcome == "decide":
            emit(c, "Status", "Needs your decision", c.status)
            if v.get("decision"):
                emit(c, "Decision", decision_text(v["decision"]), c.decision)
        elif outcome in ("do", "agent"):
            candidates.append(c)
        else:
            rest.append(c)

    total_slots = max(0, total_cap - sal_today - sal_week)
    today_slots = min(max(0, today_cap - sal_today), total_slots)
    candidates.sort(key=lambda c: (PRIORITIES.index(rank[c.key]), c.created))
    for n, c in enumerate(candidates):
        emit(c, "Status", "Today" if n < today_slots else "This week" if n < total_slots else "Backlog", c.status)
    for c in rest:
        emit(c, "Status", "Backlog", c.status)
    return out


def automatic_changes(cards: list[Card], started_urls: set[str], records: dict | None = None) -> list[Change]:
    records = records or {}
    out = []
    for c in cards:
        if c.state != "OPEN":
            want = "Done"
        elif c.open_prs:
            want = "Needs your review" if c.status != "Done" else None
        elif c.url in started_urls:
            want = "Being worked on"
        elif c.status == "Needs your review" and records.get(c.key, {}).get("Status") == "Needs your review":
            want = "Backlog"  # the agent moved it there for a pull request that is no longer open
        else:
            want = None
        if want and want != c.status:
            out.append(Change(c.item_id, c.key, "Status", want))
    return out


def triage_problem(triage: dict, now: dt.datetime) -> str | None:
    if not triage.get("ran"):
        return "no triage state; the board was left as it was"
    if triage.get("classifier_ok") is False:
        return "the triage classifier failed last night; the board was left as it was"
    ran = dt.datetime.fromisoformat(triage["ran"]).replace(tzinfo=None)
    if now - ran > dt.timedelta(hours=36):
        return f"the triage state is older than 36 hours ({triage['ran']}); the board was left as it was"
    return None
