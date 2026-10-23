"""Behavior of scripts/orca-worktree-setup, the generic Orca setup-script helper.

Orca calls a project's Setup Script with ORCA_ROOT_PATH (main checkout) and
ORCA_WORKTREE_PATH (new worktree). The helper copies gitignored local files the
agent needs, links Claude's project memory, and installs Node packages only when
a lockfile exists. These tests use disposable fixtures and a fake HOME.
"""
import os
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts' / 'orca-worktree-setup'


def run(root, wt, home, *args, check=True):
    env = {**os.environ, 'ORCA_ROOT_PATH': str(root), 'ORCA_WORKTREE_PATH': str(wt), 'HOME': str(home)}
    return subprocess.run(['bash', str(SCRIPT), *args], env=env, capture_output=True, text=True, check=check)


def fixture(tmp_path):
    root = tmp_path / 'main'
    wt = tmp_path / 'worktree'
    home = tmp_path / 'home'
    for p in (root / '.claude', wt, home):
        p.mkdir(parents=True)
    (root / '.claude' / 'settings.local.json').write_text('{"permissions": {}}\n')
    (root / '.env.local').write_text('SECRET=1\n')
    return root, wt, home


def test_script_exists_and_is_executable():
    assert SCRIPT.is_file(), 'scripts/orca-worktree-setup is missing'
    assert SCRIPT.stat().st_mode & stat.S_IXUSR, 'scripts/orca-worktree-setup is not executable'


def test_copies_local_settings_and_env_files_into_worktree(tmp_path):
    root, wt, home = fixture(tmp_path)
    out = run(root, wt, home).stdout
    assert (wt / '.claude' / 'settings.local.json').read_text() == '{"permissions": {}}\n'
    assert (wt / '.env.local').read_text() == 'SECRET=1\n'
    assert 'copied  .claude/settings.local.json' in out
    assert out.rstrip().endswith(f'ready   {wt}')


def test_never_overwrites_a_file_already_in_the_worktree(tmp_path):
    root, wt, home = fixture(tmp_path)
    (wt / '.env.local').write_text('WORKTREE_OWN=1\n')
    out = run(root, wt, home).stdout
    assert (wt / '.env.local').read_text() == 'WORKTREE_OWN=1\n'
    assert 'keep    .env.local' in out


def test_clone_flag_copies_extra_gitignored_paths_and_skips_missing_ones(tmp_path):
    root, wt, home = fixture(tmp_path)
    (root / 'var' / 'items').mkdir(parents=True)
    (root / 'var' / 'items' / 'a.json').write_text('{}')
    out = run(root, wt, home, '--clone', 'var', '--clone', 'absent').stdout
    assert (wt / 'var' / 'items' / 'a.json').read_text() == '{}'
    assert 'copied  var' in out
    assert 'absent' not in out


def test_links_claude_project_memory_to_main_checkout(tmp_path):
    root, wt, home = fixture(tmp_path)
    slug = lambda p: ''.join(c if c.isalnum() else '-' for c in str(p))
    main_mem = home / '.claude' / 'projects' / slug(root) / 'memory'
    main_mem.mkdir(parents=True)
    run(root, wt, home)
    link = home / '.claude' / 'projects' / slug(wt) / 'memory'
    assert link.is_symlink() and link.resolve() == main_mem.resolve()


def test_rerun_is_idempotent(tmp_path):
    root, wt, home = fixture(tmp_path)
    run(root, wt, home)
    out = run(root, wt, home).stdout
    assert 'copied' not in out
    assert out.count('keep') == 2


def test_ignores_empty_arguments_and_rejects_unknown_ones(tmp_path):
    root, wt, home = fixture(tmp_path)
    assert run(root, wt, home, '').returncode == 0
    bad = run(root, wt, home, '--bogus', check=False)
    assert bad.returncode == 2 and 'unknown option' in bad.stderr


def test_requires_orca_environment(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith('ORCA_')}
    env['HOME'] = str(tmp_path)
    res = subprocess.run(['bash', str(SCRIPT)], env=env, capture_output=True, text=True)
    assert res.returncode != 0 and 'ORCA_ROOT_PATH' in res.stderr


def test_skips_npm_when_worktree_has_no_lockfile(tmp_path):
    root, wt, home = fixture(tmp_path)
    out = run(root, wt, home).stdout
    assert 'running npm ci' not in out and not any(l.startswith('node') for l in out.splitlines())
