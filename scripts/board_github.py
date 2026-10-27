"""Read Sal's GitHub Project board and write its field values, through the `gh` CLI.

Reads page by page (100 cards a page) with one GraphQL query; writes one field value at a time with
`gh project item-edit`. Only issue cards become Cards; draft items and pull requests on the board are
skipped. Needs a `gh` token with the `project` scope. Standard library only.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field

from board_rules import PRIORITIES, STATUSES, Card, Change

TEXT_FIELDS = ("Why", "Decision")

QUERY = """query($login: String!, $number: Int!, $after: String) {
  %s(login: $login) {
    projectV2(number: $number) {
      id
      fields(first: 50) { nodes {
        ... on ProjectV2SingleSelectField { id name options { id name } }
        ... on ProjectV2Field { id name }
      } }
      items(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content {
            __typename
            ... on Issue {
              url number title state createdAt
              repository { nameWithOwner }
              labels(first: 30) { nodes { name } }
              closedByPullRequestsReferences(first: 5, includeClosedPrs: false) { nodes { url } }
            }
          }
          fieldValues(first: 20) { nodes {
            ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
            ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
          } }
        }
      }
    }
  }
}"""


@dataclass
class Board:
    project_id: str
    fields: dict[str, dict] = field(default_factory=dict)
    cards: list[Card] = field(default_factory=list)


def _gh(args: list[str]) -> str:
    res = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:2])}: {res.stderr.strip()[:200]}")
    return res.stdout


def load_board(owner: str, number: int, owner_type: str = "user") -> Board:
    board, after = None, None
    while True:
        args = ["api", "graphql", "-f", f"query={QUERY % owner_type}", "-f", f"login={owner}", "-F", f"number={number}"]
        if after:
            args += ["-f", f"after={after}"]
        project = (json.loads(_gh(args)).get("data") or {}).get(owner_type, {}).get("projectV2")
        if not project:
            raise RuntimeError(f"board {owner}/{number} not found")
        if board is None:
            board = Board(project["id"], {f["name"]: {"id": f["id"], "options": {o["name"]: o["id"] for o in f.get("options", [])}}
                                          for f in project["fields"]["nodes"] if f.get("name")})
        for node in project["items"]["nodes"]:
            c = node.get("content") or {}
            if c.get("__typename") != "Issue":
                continue
            values = {v["field"]["name"]: v.get("name", v.get("text")) for v in node["fieldValues"]["nodes"] if v.get("field")}
            repo = c["repository"]["nameWithOwner"]
            board.cards.append(Card(item_id=node["id"], key=f"{repo}#{c['number']}", url=c["url"], title=c["title"], repo=repo,
                                    state=c["state"], created=c["createdAt"], labels={l["name"] for l in c["labels"]["nodes"]},
                                    status=values.get("Status"), priority=values.get("Priority"), why=values.get("Why"),
                                    decision=values.get("Decision"),
                                    open_prs=[p["url"] for p in c["closedByPullRequestsReferences"]["nodes"]]))
        page = project["items"]["pageInfo"]
        if not page["hasNextPage"]:
            return board
        after = page["endCursor"]


def write(board: Board, change: Change) -> None:
    f = board.fields[change.field]
    args = ["project", "item-edit", "--id", change.item_id, "--project-id", board.project_id, "--field-id", f["id"]]
    args += ["--text", change.value] if change.field in TEXT_FIELDS else ["--single-select-option-id", f["options"][change.value]]
    _gh(args)


def setup_gaps(board: Board) -> list[str]:
    gaps = []
    have = list(board.fields.get("Status", {}).get("options", {}))
    missing = [s for s in STATUSES if s not in have]
    if missing:
        renames = [f"{old} → {new}" for old, new in (("Todo", "Backlog"), ("In Progress", "Being worked on")) if old in have and new in missing]
        gaps.append("In the board's settings, edit the Status field" + (f": rename {', '.join(renames)} (cards keep their place)" if renames else "")
                    + f"; it needs these options in this order: {', '.join(STATUSES)}. Missing now: {', '.join(missing)}.")
    absent = [n for n in ("Priority", *TEXT_FIELDS) if n not in board.fields]
    wrong = "Priority" in board.fields and list(board.fields["Priority"]["options"]) != list(PRIORITIES)
    if absent:
        gaps.append(f"Missing fields {', '.join(absent)}: run plan-board.py --setup to create them.")
    if wrong:
        gaps.append(f"The Priority field's options should be {', '.join(PRIORITIES)}, in that order.")
    return gaps


def create_fields(owner: str, number: int, board: Board) -> list[str]:
    created = []
    for name in ("Priority", *TEXT_FIELDS):
        if name in board.fields:
            continue
        args = ["project", "field-create", str(number), "--owner", owner, "--name", name]
        args += ["--data-type", "SINGLE_SELECT", "--single-select-options", ",".join(PRIORITIES)] if name == "Priority" else ["--data-type", "TEXT"]
        _gh(args)
        created.append(name)
    return created
