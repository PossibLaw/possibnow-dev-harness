#!/usr/bin/env python3
"""Mirror each repository's current task register into GitHub issues, one way.

Usage:
    sync-tasks-to-issues.py --config PATH [--only NAME] [--dry-run]
                            [--state PATH] [--summary PATH] [--slack]

The repository `.agent/TASKS.md` files stay the source of truth. Every identified
row of the first `## ` section becomes one issue carrying the configured label
(default `agent-task`) and a hidden marker `<!-- agent-task:REPO:ID sha:HASH -->`.
Rows whose state says DONE/RESOLVED/CLOSED/MERGED/SHIPPED close their issue; rows
that leave the register close it with a comment. Changes made on GitHub (closed,
edited) are never written back into the prose: they are listed as drift in the
summary. Rows that match the privacy patterns (card or bank details) are never
sent; file names are fine. Rows without an ID are reported, not invented.

GitHub access goes through `gh api` (REST), which works locally and in Claude Code
cloud sessions. The Project board step runs only when `board.enabled` is true in the
config and needs a token with the `project` scope. Issues are added once each
(tracked in the state file); a user board can hold organization repositories' issues
(confirmed October 23, 2026).

Config (JSON):
    {"label": "agent-task",
     "repos": [{"name": "Aleph", "path": "~/Aleph", "github": "Owner/repo"}, ...],
     "board": {"enabled": true, "owner": "AtticusDundee", "number": 1},
     "deny_patterns": ["..."]}            # optional; defaults below

Standard library only. Exit 0 even when some repositories fail; failures are in the
summary. Exit 2 on a bad config.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ID_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*$")
DONE_RE = re.compile(r"^\W*(DONE|RESOLVED|CLOSED|MERGED|SHIPPED)\b", re.I)
MARKER_RE = re.compile(r"<!-- agent-task:(?P<repo>[^:]+):(?P<id>[^ ]+) sha:(?P<sha>[0-9a-f]+) -->")
FLYWHEEL_RE = re.compile(r"((?:This|this|It|it) leads to[^|]*)")
DEFAULT_DENY = [
    r"\b\d{13,19}\b",                                 # long contiguous numbers (card, account)
    r"\b\d{4}([ -])\d{4}\1\d{4}\1\d{4}\b",          # card numbers in groups of four
    r"(?i)\b(iban|swift|bic|routing number|account number|acct(?:ount)? no\.?|cvv|cvc|card number|sort code)\b",
    r"(?i)\b(?:exp(?:iry|ires|\.)?|valid thru)\s*:?\s*\d{1,2}/\d{2,4}\b",
]
STATE_COLUMNS = ("state", "status", "state / next step", "resulting state", "state / evidence")
# Upper-case tags in a row's state cell become labels (added, never removed by the sync).
TAG_LABELS = {"AUTO-OK": "auto-ok", "MAINTENANCE": "maintenance", "URGENT": "urgent"}
LABEL_COLORS = {"auto-ok": "0e8a16", "maintenance": "bfd4f2", "urgent": "d93f0b"}
TASK_COLUMNS = ("task", "item", "work", "what it is", "title")


@dataclasses.dataclass
class Row:
    id: str
    cells: dict
    section: str
    text: str
    done: bool
    tags: tuple = ()


def row_tags(state: str) -> tuple:
    return tuple(label for tag, label in TAG_LABELS.items() if re.search(rf"\b{re.escape(tag)}\b", state))


def _clean(cell: str) -> str:
    return re.sub(r"[*`]", "", cell).strip()


def _split_row(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", inner)]


def first_section(text: str) -> list[str]:
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("## ")), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return lines[start + 1 : end]


def _tables(lines: list[str]):
    """Yield (section_heading, header_cells, [row_lines]) for each table in the section."""
    section = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("### "):
            section = line[4:].strip()
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*:?-", lines[i + 1]):
            header = [_clean(c) for c in _split_row(line)]
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            yield section, header, rows
            continue
        i += 1


def _state_of(cells: dict) -> str:
    for name, value in cells.items():
        if name.lower() in STATE_COLUMNS:
            return value
    return ""


def parse_register(text: str) -> list[Row]:
    rows: list[Row] = []
    seen: set[str] = set()
    for section, header, lines in _tables(first_section(text)):
        for line in lines:
            values = _split_row(line)
            if not values:
                continue
            rid = _clean(values[0])
            if not ID_RE.match(rid) or not any(ch.isdigit() for ch in rid) or len(rid) > 16 or rid in seen:
                continue
            seen.add(rid)
            cells = {header[k] if k < len(header) else f"col{k}": v for k, v in enumerate(values[1:], start=1)}
            state = _state_of(cells)
            rows.append(Row(rid, cells, section, line, bool(DONE_RE.match(_clean(state))), row_tags(_clean(state))))
    return rows


def rows_without_id(text: str) -> list[str]:
    out = []
    for _section, _header, lines in _tables(first_section(text)):
        for line in lines:
            values = _split_row(line)
            first = _clean(values[0]) if values else ""
            if not ID_RE.match(first) or not any(ch.isdigit() for ch in first):
                content = " | ".join(v for v in values if v).strip()
                if content:
                    out.append(content[:160])
    return out


def privacy_violations(text: str, patterns: list[str] | None = None) -> list[str]:
    return [p for p in (patterns or DEFAULT_DENY) if re.search(p, text)]


def _task_text(row: Row) -> str:
    for name, value in row.cells.items():
        if name.lower() in TASK_COLUMNS and value:
            return _clean(value)
    longest = max(row.cells.values(), key=len, default="")
    return _clean(longest)


def render(row: Row, repo_name: str) -> tuple[str, str]:
    task = _task_text(row)
    short = task if len(task) <= 80 else task[:77].rstrip() + "..."
    title = f"[{row.id}] {short}"
    m = FLYWHEEL_RE.search(row.text)
    flywheel = _clean(m.group(1)).rstrip(". ") + "." if m else (
        "UNCONFIRMED. Add the \"this leads to X, which leads to Y, which gets me Z\" line to the row (FW01).")
    lines = [f"**Source:** `{repo_name}/.agent/TASKS.md`" + (f" › {row.section}" if row.section else ""), ""]
    for name, value in row.cells.items():
        if value:
            lines.append(f"- **{name}:** {value}")
    lines += ["", f"**Flywheel:** {flywheel}", "", f"**State in register:** {'done' if row.done else 'open'}",
              "", "_Synced one way from the repository register; edits here are reported as drift, not written back._"]
    body = "\n".join(lines)
    sha = hashlib.sha256((title + "\n" + body).encode("utf-8")).hexdigest()[:12]
    return title, body + f"\n\n<!-- agent-task:{repo_name}:{row.id} sha:{sha} -->"


def split_marker(body: str) -> tuple[str, dict | None]:
    m = MARKER_RE.search(body or "")
    if not m:
        return body or "", None
    without = (body[: m.start()] + body[m.end():]).rstrip("\n")
    return without, m.groupdict()


# ---- GitHub ----------------------------------------------------------------------

class GitHub:
    def __init__(self, dry_run: bool):
        self.dry_run = dry_run

    def api(self, path: str, method: str = "GET", payload: dict | None = None):
        cmd = ["gh", "api", "--method", method, path]
        data = None
        if payload is not None:
            cmd += ["--input", "-"]
            data = json.dumps(payload)
        for attempt in range(4):
            res = subprocess.run(cmd, input=data, capture_output=True, text=True)
            if res.returncode == 0:
                return json.loads(res.stdout) if res.stdout.strip() else {}
            err = res.stderr.strip()[:200]
            transient = any(s in err for s in ("timeout", "TLS", "connection reset", "EOF", "502", "503", "504", "rate limit", "temporarily"))
            if not transient or attempt == 3:
                raise RuntimeError(f"gh api {method} {path}: {err}")
            time.sleep(2 * (attempt + 1))
        raise RuntimeError("unreachable")

    def ensure_labels(self, repo: str, label: str):
        names = {l["name"] for l in self.api(f"repos/{repo}/labels?per_page=100")}
        wanted = {label: ("5319e7", "Mirrored from .agent/TASKS.md by sync-tasks-to-issues"),
                  **{name: (color, f"Set by the sync from an upper-case {name.upper()} tag in the register row") for name, color in LABEL_COLORS.items()}}
        for name, (color, desc) in wanted.items():
            if name not in names and not self.dry_run:
                self.api(f"repos/{repo}/labels", "POST", {"name": name, "color": color, "description": desc})

    def labelled_issues(self, repo: str, label: str) -> list[dict]:
        out, page = [], 1
        while True:
            batch = self.api(f"repos/{repo}/issues?state=all&labels={label}&per_page=100&page={page}")
            out += [i for i in batch if "pull_request" not in i]
            if len(batch) < 100:
                return out
            page += 1

    def create(self, repo: str, title: str, body: str, labels: list[str]) -> dict:
        return self.api(f"repos/{repo}/issues", "POST", {"title": title, "body": body, "labels": labels})

    def update(self, repo: str, number: int, **fields) -> dict:
        return self.api(f"repos/{repo}/issues/{number}", "PATCH", fields)

    def comment(self, repo: str, number: int, text: str):
        return self.api(f"repos/{repo}/issues/{number}/comments", "POST", {"body": text})


# ---- sync ------------------------------------------------------------------------

def sync_repo(cfg: dict, repo: dict, gh: GitHub, deny: list[str]) -> dict:
    name, github = repo["name"], repo["github"]
    label = cfg.get("label", "agent-task")
    r = {"repo": name, "github": github, "created": [], "updated": [], "closed": [], "drift": [],
         "private": [], "no_id": [], "errors": [], "would_create": 0, "open_urls": []}
    tasks = Path(repo["path"]).expanduser() / ".agent" / "TASKS.md"
    if not tasks.is_file():
        r["errors"].append(f"no register at {tasks}")
        return r
    text = tasks.read_text(encoding="utf-8")
    rows = parse_register(text)
    r["no_id"] = rows_without_id(text)
    try:
        gh.ensure_labels(github, label)
        existing = gh.labelled_issues(github, label)
    except RuntimeError as exc:
        r["errors"].append(str(exc))
        return r
    by_id: dict[str, dict] = {}
    for issue in existing:
        _, marker = split_marker(issue.get("body") or "")
        if marker and marker["repo"] == name:
            by_id[marker["id"]] = issue
    for row in rows:
        hits = privacy_violations(row.text, deny)
        if hits:
            r["private"].append(f"{row.id}: matches a private-data pattern; not sent")
            continue
        try:
            _sync_row(row, name, github, label, gh, by_id, r)
        except RuntimeError as exc:
            r["errors"].append(f"{row.id}: {exc}")
    for rid, issue in by_id.items():
        if issue["state"] == "open":
            try:
                if not gh.dry_run:
                    gh.comment(github, issue["number"], "Closed by the sync: the row left the register's current section.")
                    gh.update(github, issue["number"], state="closed", state_reason="not_planned")
                r["closed"].append(f"{rid} #{issue['number']} (row left the register)")
            except RuntimeError as exc:
                r["errors"].append(f"{rid} #{issue['number']}: {exc}")
    return r


def _sync_row(row: Row, name: str, github: str, label: str, gh: GitHub, by_id: dict, r: dict) -> None:
    if True:
        title, body = render(row, name)
        _, new_marker = split_marker(body)
        issue = by_id.pop(row.id, None)
        if issue is None:
            if row.done:
                return
            if gh.dry_run:
                r["would_create"] += 1
            else:
                created = gh.create(github, title, body, [label, *row.tags])
                r["created"].append(f"{row.id} → #{created['number']}")
                r["open_urls"].append(created.get("html_url") or f"https://github.com/{github}/issues/{created['number']}")
            return
        current_body, old_marker = split_marker(issue.get("body") or "")
        hand_edited = old_marker is not None and hashlib.sha256((issue["title"] + "\n" + current_body).encode("utf-8")).hexdigest()[:12] != old_marker["sha"]
        if hand_edited:
            r["drift"].append(f"{row.id} #{issue['number']}: edited on GitHub; the register version " + ("replaced it" if (old_marker and old_marker["sha"] != new_marker["sha"] and not row.done) else "was kept as the record"))
        if row.done:
            if issue["state"] == "open":
                if not gh.dry_run:
                    gh.update(github, issue["number"], state="closed", state_reason="completed")
                r["closed"].append(f"{row.id} #{issue['number']} (row done)")
            return
        if issue["state"] == "closed":
            r["drift"].append(f"{row.id} #{issue['number']}: closed on GitHub but the row is still open; not reopened")
            return
        r["open_urls"].append(issue.get("html_url") or f"https://github.com/{github}/issues/{issue['number']}")
        have = {l["name"] for l in issue.get("labels", []) if isinstance(l, dict)}
        missing = [name for name in row.tags if name not in have]
        if old_marker is None or old_marker["sha"] != new_marker["sha"] or missing:
            fields = {"title": title, "body": body}
            if missing:
                fields["labels"] = sorted(have | set(missing))
            if not gh.dry_run:
                gh.update(github, issue["number"], **fields)
            r["updated"].append(f"{row.id} #{issue['number']}" + (f" (+{', '.join(missing)})" if missing else ""))


def board_step(cfg: dict, results: list[dict], state: dict, dry_run: bool) -> tuple[str, list[str]]:
    """Add every open synced issue to the GitHub Project board once. Needs `gh` with the project scope."""
    board = cfg.get("board") or {}
    if not board.get("enabled"):
        return "board: off (enable in config once the gh token has the project scope)", []
    owner, number = board.get("owner"), board.get("number")
    if not owner or not number:
        return "board: enabled but owner or number missing in config", []
    added_before = set(state.get("board_added", []))
    todo = [u for r in results for u in r["open_urls"] if u not in added_before]
    if dry_run:
        return f"board: would add {len(todo)} to {owner}/projects/{number} ({len(added_before)} already on it)", []
    added, errors = 0, []
    for url in todo:
        res = subprocess.run(["gh", "project", "item-add", str(number), "--owner", owner, "--url", url, "--format", "json"],
                             capture_output=True, text=True)
        if res.returncode == 0:
            added_before.add(url)
            added += 1
        else:
            errors.append(f"board {url}: {res.stderr.strip()[:160]}")
            if len(errors) >= 5:
                errors.append("board: stopping after 5 failures this run")
                break
    state["board_added"] = sorted(added_before)
    return f"board: added {added} to {owner}/projects/{number} ({len(added_before)} on it in total)", errors


def summarize(results: list[dict], board_line: str, dry_run: bool, board_errors: list[str] | None = None) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    out = [f"# Task → issue sync {'(dry run) ' if dry_run else ''}{now}", ""]
    for r in results:
        if dry_run:
            out.append(f"## {r['repo']} ({r['github']}): would create {r['would_create']}, update {len(r['updated'])}, close {len(r['closed'])}")
        else:
            out.append(f"## {r['repo']} ({r['github']}): created {len(r['created'])}, updated {len(r['updated'])}, closed {len(r['closed'])}, drift {len(r['drift'])}")
        for key, head in (("created", "Created"), ("updated", "Updated"), ("closed", "Closed"), ("drift", "Drift (GitHub differs from the register)"),
                          ("private", "Not sent (private data pattern)"), ("no_id", "Rows without an ID (add one in the register)"), ("errors", "Errors")):
            if r[key]:
                out.append(f"- {head}:")
                out += [f"  - {item}" for item in r[key]]
        out.append("")
    out.append(board_line)
    if board_errors:
        out.append("- Errors (board):")
        out += [f"  - {e}" for e in board_errors]
    return "\n".join(out) + "\n"


def post_slack(text: str) -> str:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return "slack: SLACK_WEBHOOK_URL not set; summary not posted"
    body = json.dumps({"text": text[:3900]}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=20)
        return "slack: posted"
    except Exception as exc:  # noqa: BLE001
        return f"slack: failed ({exc})"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--only", help="sync one configured repo by name")
    ap.add_argument("--dry-run", action="store_true", help="plan only; nothing is written to GitHub")
    ap.add_argument("--state", type=Path, default=Path.home() / ".agents" / "sync-state.json", help="last-run record (JSON)")
    ap.add_argument("--summary", type=Path, default=Path.home() / ".agents" / "sync-summary.md", help="morning summary (Markdown)")
    ap.add_argument("--slack", action="store_true", help="post the summary to $SLACK_WEBHOOK_URL")
    args = ap.parse_args(argv)
    try:
        cfg = json.loads(args.config.expanduser().read_text(encoding="utf-8"))
        repos = cfg["repos"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"BLOCKED: bad config {args.config}: {exc}", file=sys.stderr)
        return 2
    if args.only:
        repos = [r for r in repos if r["name"] == args.only]
        if not repos:
            print(f"BLOCKED: no repo named {args.only} in {args.config}", file=sys.stderr)
            return 2
    gh = GitHub(args.dry_run)
    deny = cfg.get("deny_patterns") or DEFAULT_DENY
    results = [sync_repo(cfg, repo, gh, deny) for repo in repos]
    state_path = args.state.expanduser()
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    except ValueError:
        state = {}
    board_line, board_errors = board_step(cfg, results, state, args.dry_run)
    summary = summarize(results, board_line, args.dry_run, board_errors)
    if args.slack:
        summary += post_slack(summary) + "\n"
    print(summary, end="")
    if not args.dry_run:
        for path in (args.summary, args.state):
            path.expanduser().parent.mkdir(parents=True, exist_ok=True)
        args.summary.expanduser().write_text(summary, encoding="utf-8")
        state.update({"ran": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                      "results": [{k: v for k, v in r.items() if k != "open_urls"} for r in results]})
        state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
