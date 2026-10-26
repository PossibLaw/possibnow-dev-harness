#!/usr/bin/env python3
"""Start autonomous agent runs on eligible issues, within caps, and flag their PRs.

Usage:
    dispatch-auto-issues.py --config PATH [--dry-run] [--state PATH] [--report PATH]

Policy (the autonomy page in the private repo is the source; this is the mechanism):
- Eligible: open issue carrying every label in `labels.eligible` (default agent-task and
  auto-ok); owner is not a human (an "Owner:" line naming a person other than Agent makes
  it ineligible); the body names at least one path and every path is under the repo's
  `allowed_paths`; no open PR already references the issue; no running worktree is linked
  to it.
- Caps: `max_runs` across all repos, `max_per_repo` per repo; running `auto-*` worktrees
  and open auto PRs count.
- Start: `orca worktree create --repo path:<repo> --name auto-<n> --issue <n> --agent <id>
  --prompt <text>`; the branch is therefore orca/auto-<n>, which the harness guardrails
  recognise as autonomous (no merge, no publish).
- Flag: every open PR whose head branch is orca/auto-* gets the label `labels.pr`
  (default agent-auto) and the title prefix "[auto] ". Nothing is ever merged here.
- Report: Markdown for the morning summary, plus a JSON state file.

Config (JSON): {"enabled": true, "max_runs": 2, "max_per_repo": 1, "agent": "claude",
  "model": null, "labels": {"eligible": [...], "pr": "agent-auto"},
  "repos": [{"name", "path", "github", "allowed_paths": [...]}], "prompt": "... {issue_url} ..."}

Standard library only; GitHub through `gh api` (REST); Orca through the `orca` CLI.
Exit 0 unless the config is unreadable (2).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

PATH_RE = re.compile(r"`([^`\s]+/[^`\s]*)`")
OWNER_RE = re.compile(r"\*\*Owner:\*\*\s*([^\n|]+)", re.I)
HUMAN_OWNER_RE = re.compile(r"\b(sal|salvador|client|human)\b", re.I)


def sh(cmd: list[str], payload: dict | None = None):
    data = json.dumps(payload) if payload is not None else None
    res = subprocess.run(cmd, input=data, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])}: {failure_text(res)}")
    return json.loads(res.stdout) if res.stdout.strip() else {}


def failure_text(res: subprocess.CompletedProcess) -> str:
    """Orca with --json reports errors on stdout as {"ok": false, "error": {...}} and leaves stderr empty."""
    if res.stderr.strip():
        return res.stderr.strip()[:200]
    try:
        err = json.loads(res.stdout).get("error") or {}
    except (ValueError, AttributeError):
        return res.stdout.strip()[:200]
    code, msg = err.get("code", ""), err.get("message", "")
    return (f"{code}: {msg}" if msg and msg != code else code or res.stdout.strip())[:200]


def gh(path: str, method: str = "GET", payload: dict | None = None):
    cmd = ["gh", "api", "--method", method, path]
    if payload is not None:
        cmd += ["--input", "-"]
    return sh(cmd, payload)


def orca_worktrees() -> list[dict]:
    out = sh(["orca", "worktree", "list", "--json"])
    result = out.get("result", out)
    wts = result.get("worktrees", result) if isinstance(result, dict) else result
    return [w for w in (wts or []) if not w.get("isArchived")]


def auto_name(wt: dict) -> str | None:
    branch = (wt.get("branch") or "").replace("refs/heads/", "")
    name = wt.get("displayName") or ""
    if branch.startswith("orca/auto-"):
        return branch[len("orca/"):]
    if name.startswith("auto-"):
        return name
    return None


def issue_paths(body: str, repo_path: str | Path | None = None) -> list[str]:
    """Paths the issue names in backticks: a token counts only when it exists in the repo checkout,
    or its parent folder does (a new file in an existing folder). Model names, keychain items and
    branch names therefore do not count. The sync's own Source line and register files are ignored."""
    lines = [l for l in (body or "").splitlines() if not l.lstrip().startswith("**Source:**")]
    found = {m.group(1).lstrip("./") for m in PATH_RE.finditer("\n".join(lines))}
    candidates = sorted(p for p in found if "/.agent/" not in f"/{p}" and not p.startswith("http") and ":" not in p and "@" not in p)
    if repo_path is None:
        return candidates
    root = Path(repo_path).expanduser()
    if not root.is_dir():
        return candidates
    kept = []
    for p in candidates:
        full = root / p
        if full.exists() or full.parent.is_dir():
            kept.append(p)
    return kept


HUMAN_PHRASES_RE = re.compile(r"\b(sal (decides|says|reviews|confirms|approves|answers|chooses|wants to)|ask sal|sal to |sal:|his (decision|answer|word)|sal's (decision|answer|word|call))", re.I)


def reject_reason(issue: dict, repo: dict, eligible_labels: list[str]) -> str | None:
    names = {l["name"] for l in issue.get("labels", []) if isinstance(l, dict)}
    missing = [l for l in eligible_labels if l not in names]
    if missing:
        return f"not labelled {', '.join(missing)}"
    body = issue.get("body") or ""
    m = OWNER_RE.search(body)
    if m and HUMAN_OWNER_RE.search(m.group(1)):
        return f"owner is {m.group(1).strip()} (a person decides or acts)"
    if not m:
        hit = HUMAN_PHRASES_RE.search(body)
        if hit:
            return f"no owner column, and the row waits on a person (\"{hit.group(0).strip()}\")"
    paths = issue_paths(body, repo.get("path"))
    if not paths:
        return "no paths named in the issue body; the policy needs the files it touches"
    allowed = tuple(p.rstrip("/") + "/" for p in repo.get("allowed_paths", []))
    bad = [p for p in paths if not p.startswith(allowed)]
    if bad:
        return f"path outside the allowed list: {', '.join(bad)}"
    return None


def flag_auto_prs(repo: dict, pr_label: str, dry_run: bool) -> tuple[list[str], dict[int, str], list[str]]:
    """Returns (flagged lines, {issue number: pr url} for open auto PRs, errors)."""
    flagged, open_by_issue, errors = [], {}, []
    try:
        pulls = gh(f"repos/{repo['github']}/pulls?state=open&per_page=100")
    except RuntimeError as exc:
        return flagged, open_by_issue, [str(exc)]
    for pr in pulls:
        head = (pr.get("head") or {}).get("ref", "")
        if not head.startswith("orca/auto-"):
            continue
        try:
            open_by_issue[int(head[len("orca/auto-"):])] = pr["html_url"]
        except ValueError:
            pass
        names = {l["name"] for l in pr.get("labels", []) if isinstance(l, dict)}
        needs_label = pr_label not in names
        needs_title = not pr["title"].startswith("[auto]")
        if not (needs_label or needs_title):
            continue
        if dry_run:
            flagged.append(f"would flag {repo['name']} #{pr['number']} {pr['html_url']}")
            continue
        try:
            if needs_label:
                gh(f"repos/{repo['github']}/issues/{pr['number']}/labels", "POST", {"labels": [pr_label]})
            if needs_title:
                gh(f"repos/{repo['github']}/pulls/{pr['number']}", "PATCH", {"title": f"[auto] {pr['title']}"})
            flagged.append(f"{repo['name']} #{pr['number']} flagged {pr_label}: {pr['html_url']}")
        except RuntimeError as exc:
            errors.append(f"flag #{pr['number']}: {exc}")
    return flagged, open_by_issue, errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--state", type=Path, default=Path.home() / ".agents" / "dispatch-state.json")
    ap.add_argument("--report", type=Path, default=Path.home() / ".agents" / "dispatch-report.md")
    args = ap.parse_args(argv)
    try:
        cfg = json.loads(args.config.expanduser().read_text(encoding="utf-8"))
        repos = cfg["repos"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"BLOCKED: bad config {args.config}: {exc}", file=sys.stderr)
        return 2
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Autonomous runs {'(dry run) ' if args.dry_run else ''}{now}", ""]
    if cfg.get("enabled", True) is False:
        lines.append("Dispatcher disabled in config; nothing started.")
        out = "\n".join(lines) + "\n"
        print(out, end="")
        if not args.dry_run:
            args.report.expanduser().write_text(out, encoding="utf-8")
        return 0
    max_runs = int(cfg.get("max_runs", 2))
    max_per_repo = int(cfg.get("max_per_repo", 1))
    eligible_labels = (cfg.get("labels") or {}).get("eligible", ["agent-task", "auto-ok"])
    pr_label = (cfg.get("labels") or {}).get("pr", "agent-auto")
    prompt_tpl = cfg.get("prompt") or "Autonomous run. Complete {issue_url}. Open a DRAFT PR titled '[auto] ...' labelled agent-auto. Never merge, never publish."

    try:
        running = orca_worktrees()
    except RuntimeError as exc:
        lines.append(f"Orca unavailable ({exc}); nothing started.")
        out = "\n".join(lines) + "\n"
        print(out, end="")
        if not args.dry_run:
            args.report.expanduser().write_text(out, encoding="utf-8")
        return 0
    running_auto = [w for w in running if auto_name(w)]
    running_issues = {w.get("linkedIssue") for w in running_auto if w.get("linkedIssue")}
    total = len(running_auto)
    per_repo: dict[str, int] = {}
    for w in running_auto:
        key = w.get("repoPath") or (w.get("git") or {}).get("path") or ""
        for repo in repos:
            if key and (key.rstrip("/") == str(Path(repo["path"]).expanduser()).rstrip("/") or key == f"path:{repo['path']}"):
                per_repo[repo["name"]] = per_repo.get(repo["name"], 0) + 1
    started, skipped, flagged_all, errors = [], [], [], []
    quiet_skips = 0  # issues that simply lack auto-ok: counted, not listed
    state = {"ran": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "started": [], "running_before": total}

    for repo in repos:
        flagged, open_prs, ferr = flag_auto_prs(repo, pr_label, args.dry_run)
        flagged_all += flagged
        errors += ferr
        try:
            issues = [i for i in gh(f"repos/{repo['github']}/issues?state=open&labels={eligible_labels[0]}&per_page=100") if "pull_request" not in i]
        except RuntimeError as exc:
            errors.append(f"{repo['name']}: {exc}")
            continue
        for issue in sorted(issues, key=lambda i: i["number"]):
            n = issue["number"]
            tag = f"{repo['name']} #{n} {issue.get('title', '')[:60]}"
            reason = reject_reason(issue, repo, eligible_labels)
            if reason:
                if reason.startswith("not labelled"):
                    quiet_skips += 1
                else:
                    skipped.append(f"{tag}: {reason}")
                continue
            if n in open_prs:
                skipped.append(f"{tag}: open PR already exists ({open_prs[n]})")
                continue
            if n in running_issues:
                skipped.append(f"{tag}: already running in a worktree")
                continue
            if total >= max_runs:
                skipped.append(f"{tag}: cap reached ({max_runs} runs total)")
                continue
            if per_repo.get(repo["name"], 0) >= max_per_repo:
                skipped.append(f"{tag}: cap reached ({max_per_repo} per repo)")
                continue
            prompt = prompt_tpl.replace("{issue_url}", issue["html_url"]).replace("{issue_number}", str(n)).replace("{repo}", repo["github"])
            repo_selector = f"path:{Path(repo['path']).expanduser()}"  # Orca does not expand ~ itself
            cmd = ["orca", "worktree", "create", "--repo", repo_selector, "--name", f"auto-{n}", "--issue", str(n),
                   "--agent", cfg.get("agent", "claude"), "--prompt", prompt, "--json"]
            if cfg.get("model"):
                cmd += ["--model", cfg["model"]]
            if args.dry_run:
                started.append(f"would start {tag}")
            else:
                try:
                    sh(cmd)
                    started.append(f"started {tag} → worktree auto-{n}")
                    state["started"].append({"repo": repo["name"], "issue": n, "url": issue["html_url"], "worktree": f"auto-{n}"})
                except RuntimeError as exc:
                    errors.append(f"{tag}: {exc}")
                    continue
            total += 1
            per_repo[repo["name"]] = per_repo.get(repo["name"], 0) + 1

    lines.append(f"Running before this pass: {state['running_before']} auto worktree(s). Caps: {max_runs} total, {max_per_repo} per repo. {quiet_skips} issue(s) without auto-ok not listed.")
    for head, items in (("Started", started), ("Skipped", skipped), ("Pull requests flagged", flagged_all), ("Errors", errors)):
        if items:
            lines.append(f"- {head}:")
            lines += [f"  - {x}" for x in items]
    if not started:
        lines.append("- Nothing started." if not args.dry_run else "- Nothing would start.")
    out = "\n".join(lines) + "\n"
    print(out, end="")
    if not args.dry_run:
        for p in (args.report, args.state):
            p.expanduser().parent.mkdir(parents=True, exist_ok=True)
        args.report.expanduser().write_text(out, encoding="utf-8")
        state.update({"skipped": skipped, "flagged": flagged_all, "errors": errors})
        args.state.expanduser().write_text(json.dumps(state, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
