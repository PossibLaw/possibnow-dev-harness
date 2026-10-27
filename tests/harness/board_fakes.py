"""A fake `gh` for the board scripts: GraphQL reads of a Project, `gh project item-edit` / `field-create`,
and the REST pull-request list. The world is a JSON file named by $FAKE_WORLD; every call is logged in it.
"""
import json
import os
from pathlib import Path

FAKE_GH = r'''#!/usr/bin/env python3
import json, os, sys
wp = os.environ["FAKE_WORLD"]; world = json.load(open(wp)); args = sys.argv[1:]
world.setdefault("calls", []).append(args)
def save(): json.dump(world, open(wp, "w"), indent=1)
def opt(name):
    return args[args.index(name) + 1] if name in args else None
def flag(name):  # -f name=value / -F name=value
    for i, a in enumerate(args):
        if a in ("-f", "-F") and args[i + 1].startswith(name + "="):
            return args[i + 1].split("=", 1)[1]
proj = world.get("project")
if args[:2] == ["api", "graphql"] and proj is None:
    save(); print("Could not resolve to a ProjectV2", file=sys.stderr); sys.exit(1)
if args[:2] == ["api", "graphql"]:
    after = int(flag("after") or 0)
    page = proj["items"][after:after + 100]
    fields = [{"id": f["id"], "name": f["name"], **({"options": f["options"]} if "options" in f else {})} for f in proj["fields"]]
    def node(it):
        vals = []
        for f in proj["fields"]:
            v = it.get("values", {}).get(f["name"])
            if v is None:
                continue
            vals.append({"name": v, "field": {"name": f["name"]}} if "options" in f else {"text": v, "field": {"name": f["name"]}})
        c = dict(it["content"]); c["__typename"] = it.get("type", "Issue")
        return {"id": it["id"], "content": c, "fieldValues": {"nodes": vals}}
    more = after + 100 < len(proj["items"])
    data = {"projectV2": {"id": proj["id"], "fields": {"nodes": fields},
                          "items": {"pageInfo": {"hasNextPage": more, "endCursor": str(after + 100) if more else None}, "nodes": [node(i) for i in page]}}}
    save(); print(json.dumps({"data": {world.get("owner_type", "user"): data}})); sys.exit(0)
if args[:2] == ["project", "item-edit"]:
    item = next(i for i in proj["items"] if i["id"] == opt("--id"))
    if item["id"] in world.get("fail_edit", []):
        save(); print("edit refused", file=sys.stderr); sys.exit(1)
    f = next(f for f in proj["fields"] if f["id"] == opt("--field-id"))
    if opt("--single-select-option-id"):
        value = next(o["name"] for o in f["options"] if o["id"] == opt("--single-select-option-id"))
    else:
        value = opt("--text")
    item.setdefault("values", {})[f["name"]] = value
    save(); print("{}"); sys.exit(0)
if args[:2] == ["project", "field-create"]:
    name = opt("--name"); fid = f"F-{name}"
    f = {"id": fid, "name": name}
    if opt("--data-type") == "SINGLE_SELECT":
        f["options"] = [{"id": f"{fid}-{n}", "name": n} for n in opt("--single-select-options").split(",")]
    proj["fields"].append(f)
    save(); print(json.dumps({"id": fid})); sys.exit(0)
if args[0] == "api" and "/pulls" in args[-1]:
    repo = "/".join(args[-1].split("/")[1:3])
    save(); print(json.dumps(world.get("pulls", {}).get(repo, []))); sys.exit(0)
save(); print("fake gh: unhandled " + " ".join(args), file=sys.stderr); sys.exit(1)
'''

STATUS_OPTIONS = ["Backlog", "Needs your decision", "This week", "Today", "Being worked on", "Needs your review", "Done"]


def select_field(fid, name, options):
    return {"id": fid, "name": name, "options": [{"id": f"{fid}-{o}", "name": o} for o in options]}


def ready_fields():
    return [{"id": "F-Title", "name": "Title"}, select_field("F-Status", "Status", STATUS_OPTIONS),
            select_field("F-Priority", "Priority", ["Urgent", "High", "Medium", "Low"]),
            {"id": "F-Why", "name": "Why"}, {"id": "F-Decision", "name": "Decision"}]


def issue_item(repo, n, title=None, state="OPEN", labels=(), created="2026-10-01T00:00:00Z", prs=(), **values):
    return {"id": f"I-{repo}-{n}", "type": "Issue",
            "content": {"url": f"https://github.com/{repo}/issues/{n}", "number": n, "title": title or f"Issue {n}", "state": state,
                        "createdAt": created, "repository": {"nameWithOwner": repo},
                        "labels": {"nodes": [{"name": l} for l in labels]},
                        "closedByPullRequestsReferences": {"nodes": [{"url": u} for u in prs]}},
            "values": {k: v for k, v in values.items()}}


def install(tmp_path, monkeypatch, world: dict) -> Path:
    bin_dir = tmp_path / "bin"; bin_dir.mkdir(exist_ok=True)
    (bin_dir / "gh").write_text(FAKE_GH); (bin_dir / "gh").chmod(0o755)
    wp = tmp_path / "world.json"; wp.write_text(json.dumps(world))
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_WORLD", str(wp))
    return wp
