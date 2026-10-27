#!/usr/bin/env python3
"""Nightly triage of every open tracked issue, with recommendations Sal can answer by number.

Usage:
    triage-issues.py --config PATH [--dry-run] [--state PATH] [--brief PATH] [--today WEEKDAY]

Sal, October 26, 2026: everything sat in one TickTick quadrant until he looked at it; he wants
recommendations. Decisions that night: a morning Slack brief with the top five decisions; the agent
sets `urgent` and `important` and Sal overrides; the top five daily plus a Monday sweep that closes
finished issues.

Each run:
1. reads every open issue carrying the tracking label in each configured repository, and the merged
   pull requests of the last 90 days that mention each one;
2. asks the classifier (a command, normally headless Claude Code) to sort each issue into
   decide / do / agent / done / stale / duplicate, mark it urgent and important, and, for decisions,
   write the question, options and a recommendation;
3. sets the `urgent` and `important` labels, which TickTick's Eisenhower map turns into quadrants.
   A label Sal set before the first triage, or changed since, is his and is never touched again;
4. writes the brief: the top five decisions (urgent and important first) as one numbered list, what
   only Sal can do, what agents could take, what looks finished, and what looks stale. The state file
   keeps each issue's outcome, reason and decision, and whether the classifier answered, for the
   board planner (scripts/plan-board.py);
5. on `sweep_day` (default Monday) closes issues the classifier calls done AND a merged pull request
   mentions, with a comment naming that pull request. Stale and duplicate issues are only proposed.
A classifier failure changes no labels and says so in the brief. `--dry-run` writes nothing.

Config (JSON): {"label": "agent-task", "brief_size": 5, "batch": 25, "sweep_day": "Monday",
  "classifier": {"command": ["claude", "-p", "--model", "...", "--output-format", "json", "--no-session-persistence"]},
  "repos": [{"name": "Aleph", "github": "PossibLaw/aleph"}, ...]}
Standard library only; GitHub through `gh api` (REST). Exit 0 unless the config is unreadable (2).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

MANAGED = ("urgent", "important")
OUTCOMES = ("decide", "do", "agent", "done", "stale", "duplicate")

RUBRIC = """You are triaging Sal Carranza's open GitHub issues across his repositories (a legal-tech and
AI-education founder: Aleph runs his PossibNow newsletter and content system, Trazomo is his course
platform, scbrand and LumenAtlas are client and brand work, possibnow-dev-harness is his agent tooling).
Today is {today}. For EVERY issue below, decide:

- outcome, exactly one of:
  "decide"    Sal must make a decision or ruling before anyone can act.
  "do"        Sal must do it himself (an account, a recording, a client call, a payment, a login).
  "agent"     An agent could do it now without Sal: the files are named or obvious and no judgment
              call is pending.
  "done"      The work appears finished (a merged pull request, or the text says it is complete).
  "stale"     Nobody needs this any more, or it was overtaken by later work.
  "duplicate" The same work as another listed issue (give that one's KEY in "duplicate_of").
- urgent: true when it has a date within 7 days, blocks other open work, or is a launch,
  production, client or money risk. Otherwise false.
- important: true when it moves revenue, a launch, a client commitment, or the content flywheel.
  Otherwise false.
- why: at most 20 words, plain language.
- decision (only for "decide"): {{"question": "...", "options": ["A: ...", "B: ..."], "recommend": "A"}}
  Two to four short options. Recommend the one you would choose and keep the reason in "why".

Answer with ONLY a JSON array, one object per issue:
[{{"key": "<KEY>", "outcome": "...", "urgent": false, "important": false, "why": "...", "decision": {{...}}, "duplicate_of": null}}]

Issues:
"""


def gh(path: str, method: str = "GET", payload: dict | None = None):
    cmd = ["gh", "api", "--method", method, path]
    if payload is not None:
        cmd += ["--input", "-"]
    res = subprocess.run(cmd, input=json.dumps(payload) if payload is not None else None, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"gh api {method} {path}: {(res.stderr or res.stdout).strip()[:200]}")
    return json.loads(res.stdout) if res.stdout.strip() else {}


def gh_all(path: str, stop=None) -> list:
    out, page = [], 1
    while True:
        batch = gh(f"{path}&per_page=100&page={page}")
        out += batch
        if len(batch) < 100 or (stop and batch and stop(batch[-1])):
            return out
        page += 1


def merged_mentions(github: str, since: dt.datetime) -> dict[int, list[dict]]:
    stop = lambda pr: (pr.get("updated_at") or "") < since.strftime("%Y-%m-%dT%H:%M:%SZ")
    prs = [p for p in gh_all(f"repos/{github}/pulls?state=closed&sort=updated&direction=desc", stop) if p.get("merged_at")]
    out: dict[int, list[dict]] = {}
    for pr in prs:
        for n in {int(x) for x in re.findall(r"#(\d+)\b", f"{pr.get('title', '')}\n{pr.get('body') or ''}")}:
            out.setdefault(n, []).append({"title": pr["title"], "url": pr["html_url"], "merged": pr["merged_at"][:10]})
    return out


def prompt_for(batch: list[dict], today: str) -> str:
    parts = [RUBRIC.format(today=today)]
    for it in batch:
        prs = "; ".join(f"{p['title']} (merged {p['merged']})" for p in it["prs"]) or "none"
        parts.append("\n".join([
            f"KEY: {it['key']}",
            f"Title: {it['title']}",
            f"Repository: {it['repo']}",
            f"Labels: {', '.join(sorted(it['labels'])) or 'none'}",
            f"Opened: {it['created'][:10]} · last updated: {it['updated'][:10]}",
            f"Merged pull requests mentioning it: {prs}",
            "Body:", (it["body"] or "")[:1500], "---"]))
    return "\n".join(parts)


def classify(command: list[str], batch: list[dict], today: str) -> dict[str, dict]:
    res = subprocess.run(command, input=prompt_for(batch, today), capture_output=True, text=True, timeout=900)
    if res.returncode != 0:
        raise RuntimeError(f"classifier exited {res.returncode}: {(res.stderr or res.stdout).strip()[:200]}")
    text = res.stdout
    try:
        wrapped = json.loads(text)
        if isinstance(wrapped, dict):
            if wrapped.get("is_error"):
                raise RuntimeError(f"classifier error: {str(wrapped.get('result'))[:200]}")
            text = wrapped.get("result", "")
        elif isinstance(wrapped, list):
            text = json.dumps(wrapped)
    except ValueError:
        pass
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.S)
    raw = fenced.group(1) if fenced else text[text.find("["): text.rfind("]") + 1]
    try:
        verdicts = json.loads(raw)
    except ValueError as exc:
        raise RuntimeError(f"classifier answer was not JSON: {exc}") from exc
    out = {}
    for v in verdicts:
        if isinstance(v, dict) and v.get("key") and v.get("outcome") in OUTCOMES:
            out[v["key"]] = v
    return out


def rank(item: dict) -> tuple:
    v = item["verdict"]
    return (not (v.get("urgent") and v.get("important")), not v.get("important"), not v.get("urgent"), item["created"])


def render_brief(items: list[dict], size: int, today: str, closed: list[str], errors: list[str]) -> tuple[str, list[dict]]:
    judged = [i for i in items if i.get("verdict")]
    by = {o: sorted([i for i in judged if i["verdict"]["outcome"] == o], key=rank) for o in OUTCOMES}
    lines = [f"# Morning brief: {today}", "",
             f"Reply in any Claude session with your picks, for example \"brief 1A 2B\". Labels, the board and closes follow your answers.", ""]
    decisions = []
    top = by["decide"][:size]
    if top:
        lines += [f"## Your decisions (top {len(top)} of {len(by['decide'])})", ""]
        for n, it in enumerate(top, start=1):
            v = it["verdict"]; d = v.get("decision") or {}
            lines.append(f"{n}. {it['title']} ({it['repo']}): {d.get('question', 'Decide how to proceed.')}")
            lines.append("   " + " · ".join(d.get("options") or ["A: proceed", "B: hold"]))
            lines.append(f"   Recommend {d.get('recommend', 'A')}: {v.get('why', '')} · {it['url']}")
            decisions.append({"n": n, "key": it["key"], "title": it["title"], "url": it["url"], **d})
        if len(by["decide"]) > size:
            lines.append(f"   ({len(by['decide']) - size} more decisions are waiting; they move up as these clear.)")
        lines.append("")

    def section(head, group, limit=5, extra=""):
        if not group:
            return
        lines.append(f"## {head} ({len(group)}){extra}")
        lines.append("")
        lines.extend(f"- {i['title']} ({i['repo']}): {i['verdict'].get('why', '')} · {i['url']}" for i in group[:limit])
        if len(group) > limit:
            lines.append(f"- and {len(group) - limit} more")
        lines.append("")

    section("Only you can do these", by["do"])
    section("Agents could take these", by["agent"], extra="; reply \"opt in\" with the names you want")
    if closed:
        lines += [f"## Closed by the Monday sweep ({len(closed)})", ""] + [f"- {c}" for c in closed] + [""]
    section("Looks finished; confirm and close", [i for i in by["done"] if not i.get("closed")])
    section("Looks stale or duplicate; reply \"close stale\" to close them", by["stale"] + by["duplicate"])
    quad = lambda u, im: sum(1 for i in judged if bool(i["verdict"].get("urgent")) == u and bool(i["verdict"].get("important")) == im)
    lines += [f"Open: {len(items)} · urgent and important {quad(True, True)} · important {quad(False, True)} · urgent {quad(True, False)} · neither {quad(False, False)}", ""]
    if errors:
        lines += ["## Problems this run", ""] + [f"- {e}" for e in errors] + [""]
    return "\n".join(lines), decisions


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--state", type=Path, default=Path.home() / ".agents" / "triage-state.json")
    ap.add_argument("--brief", type=Path, default=Path.home() / ".agents" / "triage-brief.md")
    ap.add_argument("--today", help="weekday name to use (testing the sweep)")
    args = ap.parse_args(argv)
    try:
        cfg = json.loads(args.config.expanduser().read_text(encoding="utf-8"))
        repos, command = cfg["repos"], cfg["classifier"]["command"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"BLOCKED: bad config {args.config}: {exc}", file=sys.stderr)
        return 2
    label = cfg.get("label", "agent-task")
    now = dt.datetime.now()
    weekday = args.today or now.strftime("%A")
    today = f"{weekday}, {now.strftime('%B %d, %Y')}"
    state_path = args.state.expanduser()
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    except ValueError:
        state = {}
    issues_state = state.setdefault("issues", {})
    errors: list[str] = []
    items: list[dict] = []
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=90)
    for repo in repos:
        try:
            mentions = merged_mentions(repo["github"], since)
            for i in gh_all(f"repos/{repo['github']}/issues?state=open&labels={urllib.parse.quote(label)}"):
                if "pull_request" in i:
                    continue
                items.append({"key": f"{repo['github']}#{i['number']}", "github": repo["github"], "repo": repo["name"], "number": i["number"],
                              "title": i["title"], "url": i["html_url"], "body": i.get("body") or "", "created": i.get("created_at") or "",
                              "updated": i.get("updated_at") or "", "labels": {l["name"] for l in i.get("labels", []) if isinstance(l, dict)},
                              "prs": mentions.get(i["number"], [])})
        except RuntimeError as exc:
            errors.append(f"{repo['name']}: {exc}")

    size = int(cfg.get("batch", 25))
    verdicts: dict[str, dict] = {}
    for start in range(0, len(items), size):
        batch = items[start:start + size]
        try:
            verdicts.update(classify(command, batch, today))
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
            errors.append(f"classifier, issues {start + 1}-{start + len(batch)}: {exc}")
    for it in items:
        it["verdict"] = verdicts.get(it["key"])
    missing = [it["title"] for it in items if not it["verdict"]]
    if missing and len(missing) < len(items):
        errors.append(f"classifier skipped {len(missing)} issues; their labels were left alone")

    labels_ready: set[str] = set()
    for it in items:
        v, rec = it["verdict"], issues_state.setdefault(it["key"], {})
        if "set" not in rec:
            rec["pinned"] = sorted(l for l in MANAGED if l in it["labels"])  # there before the first triage: Sal's
        else:
            for l in MANAGED:
                if l not in rec["pinned"] and (l in it["labels"]) != bool(rec["set"].get(l)):
                    rec["pinned"] = sorted(set(rec["pinned"]) | {l})  # changed since the triage set it: Sal's now
        if not v:
            continue
        want = {l: bool(v.get(l)) for l in MANAGED}
        rec.update(outcome=v["outcome"], why=v.get("why", ""), decision=v.get("decision") if v["outcome"] == "decide" else None, judged=now.isoformat(timespec="seconds"))
        for l in MANAGED:
            if l in rec["pinned"] or (l in it["labels"]) == want[l]:
                continue
            if args.dry_run:
                continue
            try:
                if want[l]:
                    if it["github"] not in labels_ready:
                        names = {x["name"] for x in gh(f"repos/{it['github']}/labels?per_page=100")}
                        for name, color in (("urgent", "d93f0b"), ("important", "fbca04")):
                            if name not in names:
                                gh(f"repos/{it['github']}/labels", "POST", {"name": name, "color": color, "description": "Set by the nightly triage; change it and the triage leaves it alone"})
                        labels_ready.add(it["github"])
                    gh(f"repos/{it['github']}/issues/{it['number']}/labels", "POST", {"labels": [l]})
                else:
                    gh(f"repos/{it['github']}/issues/{it['number']}/labels/{l}", "DELETE")
            except RuntimeError as exc:
                errors.append(f"{it['title']}: {exc}")
        rec["set"] = {l: ((l in it["labels"]) if l in rec["pinned"] else want[l]) for l in MANAGED}

    closed: list[str] = []
    if weekday.lower() == str(cfg.get("sweep_day", "Monday")).lower():
        for it in items:
            v = it["verdict"]
            if not v or v["outcome"] != "done" or not it["prs"]:
                continue
            pr = it["prs"][0]
            note = f"Closed by the Monday sweep: the merged pull request \"{pr['title']}\" ({pr['url']}) covers this. Reopen it if anything is left."
            if not args.dry_run:
                try:
                    gh(f"repos/{it['github']}/issues/{it['number']}/comments", "POST", {"body": note})
                    gh(f"repos/{it['github']}/issues/{it['number']}", "PATCH", {"state": "closed", "state_reason": "completed"})
                except RuntimeError as exc:
                    errors.append(f"{it['title']}: {exc}"); continue
            it["closed"] = True
            closed.append(f"{it['title']} ({it['repo']}): {pr['title']} · {it['url']}")

    if not verdicts and items:
        errors.append("classifier returned nothing; no labels were changed")
    brief, decisions = render_brief(items, int(cfg.get("brief_size", 5)), today, closed, errors)
    print(brief, end="")
    if not args.dry_run:
        for p in (state_path, args.brief.expanduser()):
            p.parent.mkdir(parents=True, exist_ok=True)
        state.update(ran=now.isoformat(timespec="seconds"), decisions=decisions, classifier_ok=bool(verdicts) or not (items or errors))
        state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
        args.brief.expanduser().write_text(brief, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
