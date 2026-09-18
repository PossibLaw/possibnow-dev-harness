from pathlib import Path
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def test_bootstrap_pins_pack_ref_and_reports_commit(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    for folder in ('scripts', 'packs', 'skills', '.agents', '.claude-plugin'):
        shutil.copytree(ROOT / folder, source / folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    def git(*args):
        return subprocess.check_output(['git', '-C', str(source), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', *args], text=True).strip()
    git('init', '-q')
    git('add', '.')
    git('commit', '-qm', 'release fixture')
    released = git('rev-parse', 'HEAD')
    git('tag', 'v4.2.0')
    (source / 'packs/project/docs/glossary.md').write_text('unreleased main content')
    git('commit', '-qam', 'unreleased change')
    target = tmp_path / 'target'
    target.mkdir()
    env = os.environ.copy()
    for key in ('DEV_HARNESS_REF', 'STARTER_PACK_REF', 'STARTER_PACK_REPO_URL'):
        env.pop(key, None)
    env['DEV_HARNESS_REPO_URL'] = source.as_uri()
    # Default tag and explicit double pin must both select the release, not branch HEAD.
    for explicit in (False, True):
        if explicit:
            env['DEV_HARNESS_REF'] = 'v4.2.0'
        result = subprocess.run(['bash', str(ROOT / 'scripts/bootstrap-project.sh'), str(target), '--adopt'], env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        metadata = json.loads((target / '.harness/releases/4.2.0/VERSION.json').read_text())
        assert metadata == {'version': '4.2.0', 'commit': released, 'source_dirty': False}
        assert released in result.stdout
        assert (target / 'docs/glossary.md').read_text() != 'unreleased main content'
