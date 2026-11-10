"""scripts/repo_paths.py: config paths may use $REPOS (per-machine repository root)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import repo_paths  # noqa: E402


def test_repos_defaults_to_home(monkeypatch):
    monkeypatch.delenv("REPOS", raising=False)
    monkeypatch.setenv("HOME", "/home/x")
    assert repo_paths.expand_path("$REPOS/my-repo", "repos[0].path") == "/home/x/my-repo"
    assert repo_paths.expand_path("${REPOS}/my-repo", "k") == "/home/x/my-repo"


def test_repos_env_is_used_and_may_use_tilde(monkeypatch):
    monkeypatch.setenv("HOME", "/home/x")
    monkeypatch.setenv("REPOS", "/srv/code")
    assert repo_paths.expand_path("$REPOS/my-repo", "k") == "/srv/code/my-repo"
    monkeypatch.setenv("REPOS", "~/code")
    assert repo_paths.expand_path("$REPOS/my-repo", "k") == "/home/x/code/my-repo"


def test_tilde_paths_unchanged(monkeypatch):
    monkeypatch.setenv("HOME", "/home/x")
    monkeypatch.setenv("REPOS", "/srv/code")
    assert repo_paths.expand_path("~/my-repo", "k") == "/home/x/my-repo"
    assert repo_paths.expand_path("/abs/my-repo", "k") == "/abs/my-repo"


def test_unknown_variable_fails_naming_the_key(monkeypatch):
    monkeypatch.delenv("NOPE", raising=False)
    with pytest.raises(ValueError) as exc:
        repo_paths.expand_path("$NOPE/my-repo", "repos[2].path")
    assert "repos[2].path" in str(exc.value) and "NOPE" in str(exc.value)


def test_resolve_repos_expands_every_path(monkeypatch):
    monkeypatch.setenv("REPOS", "/srv/code")
    repos = [{"name": "a", "path": "$REPOS/a"}, {"name": "b"}]
    out = repo_paths.resolve_repos(repos, "repos")
    assert out[0]["path"] == "/srv/code/a" and "path" not in out[1]
    assert repos[0]["path"] == "$REPOS/a"  # input untouched


def test_same_path_ignores_case_on_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert repo_paths.same_path("/Users/x/Repos/my-repo/", "path:/users/x/repos/my-repo") is True
    assert repo_paths.same_path("/a/b", "/a/c") is False


def test_same_path_is_case_sensitive_elsewhere(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert repo_paths.same_path("/a/my-repo", "/a/aleph") is False
    assert repo_paths.same_path("/a/my-repo/", "/a/my-repo") is True


def test_empty_repos_counts_as_unset(monkeypatch):
    monkeypatch.setenv("HOME", "/home/x")
    monkeypatch.setenv("REPOS", "")
    assert repo_paths.expand_path("$REPOS/my-repo", "k") == "/home/x/my-repo"


def test_unsupported_brace_syntax_is_an_error(monkeypatch):
    monkeypatch.setenv("REPOS", "/srv")
    with pytest.raises(ValueError) as exc:
        repo_paths.expand_path("${REPOS:-x}/a", "repos[0].path")
    assert "repos[0].path" in str(exc.value)
