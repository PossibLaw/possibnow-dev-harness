from pathlib import Path
import hashlib
import importlib.util
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'packs/project/.agent/integrations/checkpoint.py'


def module():
    assert TOOL.exists(), 'checkpoint preservation helper is missing'
    spec = importlib.util.spec_from_file_location('checkpoint', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture(tmp_path):
    state = tmp_path / '.agent'
    state.mkdir()
    old = b'# Old\r\n## Unresolved work\r\n- Finish auth checks\r\n## Active constraints\r\n- Never publish drafts\r\nOlder narrative without final newline'
    (state / 'HANDOFF.md').write_bytes(old)
    (state / 'HISTORY.md').write_bytes(b'# Legacy history\nKeep this\n')
    candidate = tmp_path / 'candidate.md'
    candidate.write_text('# Current\n## Status\nIn progress\n## Unresolved work\n- Finish auth checks\n## Active constraints\n- Never publish drafts\n## Evidence\nTEST.md\n## Next actions\nFinish checks\n')
    return state, old, candidate


def test_archive_bytes_verified_and_identical_archives_deduplicate(tmp_path):
    m = module()
    state, old, candidate = fixture(tmp_path)
    digest = hashlib.sha256(old).hexdigest()
    m.checkpoint(tmp_path, candidate, digest)
    archived = state / 'archives/handoffs' / (digest + '.md')
    assert archived.read_bytes() == old
    assert (state / 'HISTORY.md').read_bytes().startswith(b'# Legacy history\nKeep this\n')
    assert digest in (state / 'HISTORY.md').read_text()
    assert 'Archived at:' in (state / 'HISTORY.md').read_text()
    assert (state / 'HANDOFF.md').read_bytes() == candidate.read_bytes()
    before = (state / 'HISTORY.md').read_bytes()
    (state / 'HANDOFF.md').write_bytes(old)
    m.checkpoint(tmp_path, candidate, digest)
    assert (state / 'HISTORY.md').read_bytes() == before
    assert len(list(archived.parent.iterdir())) == 1


def test_archive_failure_leaves_handoff_intact(tmp_path, monkeypatch):
    m = module()
    state, old, candidate = fixture(tmp_path)
    def fail(*args, **kwargs):
        raise OSError('archive unavailable')
    monkeypatch.setattr(m, 'archive_bytes', fail)
    with pytest.raises(OSError):
        m.checkpoint(tmp_path, candidate, hashlib.sha256(old).hexdigest())
    assert (state / 'HANDOFF.md').read_bytes() == old


def test_intervening_edit_is_not_overwritten(tmp_path, monkeypatch):
    m = module()
    state, old, candidate = fixture(tmp_path)
    real = m.archive_bytes
    def edit(*args, **kwargs):
        result = real(*args, **kwargs)
        (state / 'HANDOFF.md').write_bytes(b'concurrent work')
        return result
    monkeypatch.setattr(m, 'archive_bytes', edit)
    with pytest.raises(ValueError, match='changed'):
        m.checkpoint(tmp_path, candidate, hashlib.sha256(old).hexdigest())
    assert (state / 'HANDOFF.md').read_bytes() == b'concurrent work'


def test_corrupt_existing_archive_is_not_trusted(tmp_path):
    m = module()
    state, old, candidate = fixture(tmp_path)
    digest = hashlib.sha256(old).hexdigest()
    folder = state / 'archives/handoffs'
    folder.mkdir(parents=True)
    (folder / (digest + '.md')).write_bytes(b'corrupt')
    with pytest.raises(ValueError):
        m.checkpoint(tmp_path, candidate, digest)
    assert (state / 'HANDOFF.md').read_bytes() == old


def test_same_candidate_is_a_noop(tmp_path):
    m = module()
    state, old, candidate = fixture(tmp_path)
    (state / 'HANDOFF.md').write_bytes(candidate.read_bytes())
    before = (state / 'HISTORY.md').read_bytes()
    m.checkpoint(tmp_path, candidate, hashlib.sha256(candidate.read_bytes()).hexdigest())
    assert (state / 'HISTORY.md').read_bytes() == before


def test_conflicting_history_id_is_refused(tmp_path):
    m = module()
    state, old, candidate = fixture(tmp_path)
    digest = hashlib.sha256(old).hexdigest()
    (state / 'HISTORY.md').write_text(f'<!-- checkpoint-{digest} -->\nWrong archive reference\n')
    with pytest.raises(ValueError, match='conflicting'):
        m.checkpoint(tmp_path, candidate, digest)
    assert (state / 'HANDOFF.md').read_bytes() == old


def test_missing_current_sections_is_refused(tmp_path):
    m = module()
    state, old, candidate = fixture(tmp_path)
    candidate.write_text('# Done\n')
    with pytest.raises(ValueError, match='missing section'):
        m.checkpoint(tmp_path, candidate, hashlib.sha256(old).hexdigest())
    assert (state / 'HANDOFF.md').read_bytes() == old
