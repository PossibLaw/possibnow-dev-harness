#!/usr/bin/env python3
"""Watch the sources our articles and lessons cite; file a work order when they change.

Usage:
    content-freshness.py --config PATH [--dry-run] [--state PATH] [--report PATH]

One engine for every repository (Sal, October 26, 2026): each watch names a repository, the content
files to read, and how to republish. Every run:
- reads the links each content file cites (markdown and HTML), skipping `ignore_hosts`;
- fetches each source once and compares its main text with the last run: a source whose sentences
  changed by more than `change_threshold` (default 3%) is "changed"; one that fails `dead_after`
  runs in a row (default 2) is "dead"; one that now redirects somewhere new is "moved";
- reads each vendor doc index (an llms.txt-style page of links) and reports pages that are new;
- keeps every finding pending until the watch's issue is closed, so a change is never dropped
  because the agent has not reached it yet;
- writes the pending findings to one issue per watch, a work order the nightly autonomous
  dispatcher can start: Owner Agent, files in scope, each article with what changed in each source,
  how to finish (a pull request that closes the issue) and how to republish.
The first run only records a baseline. `--dry-run` fetches and reports but writes nothing.

Config (JSON):
  {"change_threshold": 0.03, "dead_after": 2,
   "watches": [{"name", "title", "auto": true, "repo": {"name", "path", "github"},
                "content": ["glob relative to the repo", ...], "scope": ["folder/", ...],
                "ignore_hosts": [...], "inventories": [{"name", "index": "https://.../llms.txt"}],
                "republish": "how Sal republishes", "finish": ["extra step", ...]}]}

Standard library only; GitHub through `gh api` (REST). Exit 0 unless the config is unreadable (2).
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import html
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

LABEL = "content-freshness"
MD_LINK = re.compile(r"\]\((https?://[^)\s]+)\)")
BARE = re.compile(r"(?:href=[\"']|<)(https?://[^\"'>\s]+)")
SKIP_TAGS = {"script", "style", "nav", "header", "footer", "noscript", "svg", "aside", "form"}


# ---- sources -------------------------------------------------------------------------

class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def main_text(raw: str, content_type: str) -> str:
    if "html" in content_type or raw.lstrip().startswith("<"):
        p = _Text()
        try:
            p.feed(raw)
        except Exception:  # noqa: BLE001  malformed pages still yield what was parsed
            pass
        raw = " ".join(p.parts)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()[:200_000]


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 3]


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "possibnow-content-freshness/1 (+https://github.com/PossibLaw/possibnow-dev-harness)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            raw = res.read(3_000_000).decode(res.headers.get_content_charset() or "utf-8", "replace")
            return {"ok": True, "status": res.status, "final_url": res.geturl(), "text": main_text(raw, res.headers.get("Content-Type", ""))}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code}
    except Exception as exc:  # noqa: BLE001  DNS, TLS, timeouts: all count as one failed check
        return {"ok": False, "status": type(exc).__name__}


def compare(before: str, after: str) -> tuple[float, list[str], list[str]]:
    a, b = sentences(before), sentences(after)
    sa, sb = set(a), set(b)
    added = [s for s in b if s not in sa]
    removed = [s for s in a if s not in sb]
    share = (len(added) + len(removed)) / max(len(a), len(b), 1)
    return share, added, removed


def cited(repo_path: Path, patterns: list[str], ignore_hosts: list[str]) -> dict[str, list[str]]:
    """{content file (relative): [source url, ...]} in citation order, own hosts skipped."""
    out: dict[str, list[str]] = {}
    for pattern in patterns:
        for name in sorted(glob.glob(str(repo_path / pattern), recursive=True)):
            text = Path(name).read_text(encoding="utf-8", errors="replace")
            urls = []
            for m in list(MD_LINK.finditer(text)) + list(BARE.finditer(text)):
                url = m.group(1).rstrip(".,;")
                host = urllib.parse.urlparse(url).hostname or ""
                if url not in urls and not any(host == h or host.endswith("." + h) for h in ignore_hosts):
                    urls.append(url)
            if urls:
                out[str(Path(name).relative_to(repo_path))] = urls
    return out


def index_pages(text: str) -> list[str]:
    return sorted(set(re.findall(r"https?://[^\s)\]>\"']+", text)))


# ---- GitHub --------------------------------------------------------------------------

def gh(path: str, method: str = "GET", payload: dict | None = None):
    cmd = ["gh", "api", "--method", method, path]
    if payload is not None:
        cmd += ["--input", "-"]
    res = subprocess.run(cmd, input=json.dumps(payload) if payload is not None else None, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"gh api {method} {path}: {(res.stderr or res.stdout).strip()[:200]}")
    return json.loads(res.stdout) if res.stdout.strip() else {}


def marker(name: str) -> str:
    return f"<!-- content-freshness:{name} -->"


def find_issue(github: str, name: str) -> dict | None:
    for issue in gh(f"repos/{github}/issues?state=open&labels={LABEL}&per_page=100"):
        if marker(name) in (issue.get("body") or ""):
            return issue
    return None


def ensure_label(github: str, name: str):
    if name not in {l["name"] for l in gh(f"repos/{github}/labels?per_page=100")}:
        gh(f"repos/{github}/labels", "POST", {"name": name, "color": "0e8a16", "description": "Cited sources changed; work order from content-freshness"})


# ---- work order ------------------------------------------------------------------------

def render(watch: dict, pending: dict, checked: str) -> str:
    scope = watch.get("scope") or []
    articles: dict[str, list[dict]] = {}
    for f in pending.get("sources", {}).values():
        for file in f["files"]:
            articles.setdefault(file, []).append(f)
    pages = pending.get("pages", {})
    total = sum(len(v) for v in articles.values()) + len(pages)
    lines = [
        f"# {watch.get('title') or watch['name'] + ' update'}: work order", "",
        "- **Owner:** Agent",
        f"- **Checked:** {checked}",
        "- **Files in scope:** " + ", ".join(f"`{s}`" for s in scope),
        "", f"## What needs to change ({total} items)", "",
    ]
    for file in sorted(articles):
        lines.append(f"### `{file}`")
        lines.append("")
        for f in sorted(articles[file], key=lambda x: x["url"]):
            if f["kind"] == "changed":
                lines.append(f"- **Source changed** ({f['share']:.0%} of its sentences): {f['url']}")
                lines += [f"  - Now says: \"{s[:240]}\"" for s in f.get("added", [])[:3]]
                lines += [f"  - No longer says: \"{s[:240]}\"" for s in f.get("removed", [])[:3]]
            elif f["kind"] == "dead":
                lines.append(f"- **Source is dead** (status {f['status']} on {f['failures']} checks in a row): {f['url']}. Find the current page or remove the claim it supports.")
            elif f["kind"] == "moved":
                lines.append(f"- **Source moved**: {f['url']} now lands on {f['final_url']}. Check it still supports the claim, then update the link.")
        lines.append("")
    if pages:
        lines += ["### New vendor doc pages", "", "Decide whether each one matters to our readers; cover it where it fits or skip it with a reason.", ""]
        for url, inv in sorted(pages.items()):
            lines.append(f"- {inv}: {url}")
        lines.append("")
    lines += [
        "## How to do it", "",
        "1. Handle every item in this run. For each one, update the content or skip it with a one-line reason.",
        "2. Read the source before writing. Change only what the source change affects; keep the author's voice and structure. If you cannot verify a claim, stop and write the question on this issue.",
        "3. Edit only inside the files in scope.",
        *[f"{i}. {step}" for i, step in enumerate(watch.get("finish") or [], start=4)],
        f"{4 + len(watch.get('finish') or [])}. Open a draft pull request titled `[auto] {watch.get('title') or watch['name'] + ' update'}` with three sections: **What changed** (article by article, in plain language), **Skipped and why**, and **To republish**: \"{watch.get('republish', 'Merge this pull request.')}\" End the body with `Closes #` and this issue's number. Post the same summary as a comment on this issue.",
        "", marker(watch["name"]),
    ]
    return "\n".join(lines) + "\n"


# ---- run -----------------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--state", type=Path, default=Path.home() / ".agents" / "freshness-state.json")
    ap.add_argument("--report", type=Path, default=Path.home() / ".agents" / "freshness-report.md")
    args = ap.parse_args(argv)
    try:
        cfg = json.loads(args.config.expanduser().read_text(encoding="utf-8"))
        watches = cfg["watches"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"BLOCKED: bad config {args.config}: {exc}", file=sys.stderr)
        return 2
    threshold = float(cfg.get("change_threshold", 0.03))
    dead_after = int(cfg.get("dead_after", 2))
    state_path = args.state.expanduser()
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    except ValueError:
        state = {}
    sources, indexes, pending_all = state.setdefault("sources", {}), state.setdefault("indexes", {}), state.setdefault("pending", {})
    checked = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    report = [f"# Content freshness {'(dry run) ' if args.dry_run else ''}{checked[:16].replace('T', ' ')}", ""]
    fetched: dict[str, dict] = {}

    for watch in watches:
        repo = watch["repo"]
        name, github = watch["name"], repo["github"]
        pending = json.loads(json.dumps(pending_all.get(name, {"sources": {}, "pages": {}})))
        errors = []
        issue = None
        try:
            issue = find_issue(github, name)
        except RuntimeError as exc:
            errors.append(str(exc))
        if issue is None and not errors and (pending["sources"] or pending["pages"]) and pending.get("filed"):
            pending = {"sources": {}, "pages": {}}  # the work order was closed: its findings were handled
        citations = cited(Path(repo["path"]).expanduser(), watch.get("content") or [], watch.get("ignore_hosts") or [])
        by_url: dict[str, list[str]] = {}
        for file, urls in citations.items():
            for url in urls:
                by_url.setdefault(url, []).append(file)
        new_findings = 0
        for url, files in sorted(by_url.items()):
            if url not in fetched:
                fetched[url] = fetch(url)
            now, before = fetched[url], sources.get(url)
            finding = None
            if now["ok"]:
                if before and before.get("text") is not None:
                    share, added, removed = compare(before["text"], now["text"])
                    if share > threshold:
                        finding = {"kind": "changed", "share": share, "added": added[:3], "removed": removed[:3]}
                    elif before.get("final_url") and now["final_url"] != before["final_url"] and urllib.parse.urlparse(now["final_url"]).path != urllib.parse.urlparse(before["final_url"]).path:
                        finding = {"kind": "moved", "final_url": now["final_url"]}
                record = {"text": now["text"], "final_url": now["final_url"], "status": now["status"], "failures": 0}
            else:
                failures = (before or {}).get("failures", 0) + 1
                if failures >= dead_after and (before or {}).get("failures", 0) < dead_after:
                    finding = {"kind": "dead", "status": now["status"], "failures": failures}
                record = {**(before or {}), "status": now["status"], "failures": failures}
                record.setdefault("text", None)
            record["checked"] = checked
            fetched[url]["record"] = record
            if finding:
                pending["sources"][url] = {"url": url, "files": files, **finding}
                new_findings += 1
            elif url in pending["sources"]:
                pending["sources"][url]["files"] = files
        for inv in watch.get("inventories") or []:
            got = fetched.get(inv["index"]) or fetch(inv["index"])
            fetched[inv["index"]] = got
            if not got["ok"]:
                errors.append(f"{inv['name']}: index unavailable ({got['status']})")
                continue
            pages_now = index_pages(got["text"])
            seen = indexes.get(inv["index"])
            if seen is not None:
                for url in sorted(set(pages_now) - set(seen)):
                    pending["pages"][url] = inv["name"]
                    new_findings += 1
            got["pages"] = pages_now

        items = len(pending["sources"]) + len(pending["pages"])
        title = watch.get("title") or f"{name} update"
        line = f"## {title} ({github}): {len(citations)} files, {len(by_url)} sources; {new_findings} new findings, {items} pending"
        report.append(line)
        if items:
            body = render(watch, pending, checked)
            labels = [LABEL, "agent-task"] + (["auto-ok"] if watch.get("auto") else [])
            if args.dry_run:
                report.append(f"- would {'update' if issue else 'file'} \"{title}\" with: " + ", ".join(sorted({f for s in pending['sources'].values() for f in s['files']} | set(pending["pages"]))))
            else:
                try:
                    ensure_label(github, LABEL)
                    if issue:
                        names = sorted({l["name"] for l in issue.get("labels", []) if isinstance(l, dict)} | set(labels))
                        gh(f"repos/{github}/issues/{issue['number']}", "PATCH", {"title": title, "body": body, "labels": names})
                        report.append(f"- updated \"{title}\": {issue['html_url']}")
                    else:
                        made = gh(f"repos/{github}/issues", "POST", {"title": title, "body": body, "labels": labels})
                        report.append(f"- filed \"{title}\": {made['html_url']}")
                    pending["filed"] = True
                except RuntimeError as exc:
                    errors.append(str(exc))
        if errors:
            report.append("- Errors:")
            report += [f"  - {e}" for e in errors]
        report.append("")
        pending_all[name] = pending

    out = "\n".join(report) + "\n"
    print(out, end="")
    if not args.dry_run:
        for url, got in fetched.items():
            if "record" in got:
                sources[url] = got["record"]
            if "pages" in got:
                indexes[url] = got["pages"]
        state["ran"] = checked
        for p in (state_path, args.report.expanduser()):
            p.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
        args.report.expanduser().write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
