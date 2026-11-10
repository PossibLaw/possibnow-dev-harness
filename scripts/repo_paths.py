"""Config paths that follow the machine's repository root.

A config path may start with `$REPOS` (or `${REPOS}`); `REPOS` is set per machine in the scheduled job's
environment and defaults to the home directory, so `~/Aleph` and `$REPOS/Aleph` agree when it is unset.
Expansion is `os.path.expandvars` then `os.path.expanduser`. A `$NAME` that is not set is an error
that names the config key, never a silently wrong path.
"""
from __future__ import annotations

import os
import re
import sys

_VAR = re.compile(r"\$(?:\{(\w+)\}|(\w+))")


def expand_path(value: str, key: str) -> str:
    env = dict(os.environ)
    env.setdefault("REPOS", os.path.expanduser("~"))
    env["REPOS"] = os.path.expanduser(env["REPOS"])
    for m in _VAR.finditer(value):
        name = m.group(1) or m.group(2)
        if name not in env:
            raise ValueError(f"{key}: ${name} is not set in the environment (value {value!r})")
    expanded = _VAR.sub(lambda m: env[m.group(1) or m.group(2)], value)
    return os.path.expanduser(expanded)


def resolve_repos(repos: list[dict], key: str = "repos") -> list[dict]:
    """Copies of the repo entries with `path` expanded; a repo without a path is left alone."""
    out = []
    for i, repo in enumerate(repos):
        repo = dict(repo)
        if repo.get("path"):
            repo["path"] = expand_path(str(repo["path"]), f"{key}[{i}].path")
        out.append(repo)
    return out


def normalize(path: str) -> str:
    """Comparable form of a path (an Orca `path:` selector is accepted): realpath, no trailing slash,
    case-folded on macOS, whose filesystem is case-insensitive."""
    if path.startswith("path:"):
        path = path[5:]
    path = os.path.realpath(path).rstrip("/") or "/"
    return path.casefold() if sys.platform == "darwin" else path


def same_path(a: str, b: str) -> bool:
    return normalize(a) == normalize(b)
