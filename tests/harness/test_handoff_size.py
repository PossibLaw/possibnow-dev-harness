"""HANDOFF stays a pointer, not a log (November 25, 2026).

Every close and autonomous run prepended a narrative entry, so the current HANDOFF only
grew (Trazomo: 95 KB). handoff_size.py enforces the limits from Trazomo PR #929: file
24,000 bytes; `## Status` 30 lines and 4,000 bytes; any line 1,500 characters; plus the
headings a repository's own tooling needs. It reports; it never rewrites anything.
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'packs/project/.agent/integrations/handoff_size.py'
TEMPLATE = ROOT / 'packs/project/.agent/HANDOFF.md'


def module():
    assert TOOL.exists(), 'handoff size check is missing'
    spec = importlib.util.spec_from_file_location('handoff_size', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def handoff(status_lines=3, filler_bytes=0, line=None):
    status = '\n'.join(f'- status {i}' for i in range(status_lines))
    body = (f'# HANDOFF\n\n## Status\n{status}\n\n## Recent work\n- 2026-11-25 x ([#1](u))\n\n'
            '## Unresolved work\n- none\n\n## Active constraints\n- none\n\n## Evidence\n- none\n\n'
            '## Next actions\n1. none\n')
    if line:
        body += line + '\n'
    if filler_bytes:
        body += 'x' * filler_bytes
    return body


def write(tmp_path, text, limits=None):
    agent = tmp_path / '.agent'
    agent.mkdir(exist_ok=True)
    (agent / 'HANDOFF.md').write_text(text)
    if limits is not None:
        (agent / 'handoff-limits.json').write_text(limits if isinstance(limits, str) else json.dumps(limits))
    return agent / 'HANDOFF.md'


def run(tmp_path):
    return subprocess.run([sys.executable, str(TOOL), str(tmp_path)], capture_output=True, text=True)


def pad_to(text, size):
    """Pad with short lines so no single line breaks the line limit."""
    missing = size - len(text.encode())
    chunk = ('y' * 99 + '\n')
    text += chunk * (missing // len(chunk))
    return text + 'z' * (size - len(text.encode()))


# HS-1
def test_handoff_under_every_limit_passes(tmp_path):
    write(tmp_path, handoff())
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'OK' in result.stdout


# HS-2 boundaries
def test_file_size_boundary(tmp_path):
    m = module()
    limits = m.load_limits(tmp_path)[0]
    assert m.check_text(pad_to(handoff(), 24_000), limits) == []
    problems = m.check_text(pad_to(handoff(), 24_001), limits)
    assert problems and '24001 bytes' in problems[0] and '24000' in problems[0]


def test_status_line_boundary(tmp_path):
    m = module()
    limits = m.load_limits(tmp_path)[0]
    assert m.check_text(handoff(status_lines=30), limits) == []
    problems = m.check_text(handoff(status_lines=31), limits)
    assert any('## Status is 31 lines' in p for p in problems)


def test_status_byte_boundary(tmp_path):
    m = module()
    limits = m.load_limits(tmp_path)[0]
    def status(size):  # 20 lines (under the line cap) totalling `size` bytes
        lines = ['a' * 199] * 19
        return '\n'.join(lines + ['a' * (size - 19 * 200)])
    exact, over = status(4_000), status(4_001)
    assert len(exact.encode()) == 4_000
    assert m.check_text(f'## Status\n{exact}\n## Next actions\n', limits) == []
    problems = m.check_text(f'## Status\n{over}\n## Next actions\n', limits)
    assert any('## Status is 4001 bytes' in p for p in problems)


def test_line_length_boundary_counts_characters_not_bytes(tmp_path):
    m = module()
    limits = m.load_limits(tmp_path)[0]
    assert m.check_text(handoff(line='é' * 1_500), limits) == []
    problems = m.check_text(handoff(line='é' * 1_501), limits)
    assert any('1501 chars' in p for p in problems)


def test_missing_status_is_bounded_by_size_unless_required(tmp_path):
    # Legacy handoffs without `## Status` must not block every commit; the file-size cap
    # still applies, and a repository can require the heading.
    m = module()
    text = '# HANDOFF\n## Current Baton\n- x\n'
    assert m.check_text(text, m.load_limits(tmp_path)[0]) == []
    write(tmp_path, text, {'required_headings': ['## Status']})
    problems = m.check_text(text, m.load_limits(tmp_path)[0])
    assert any('"## Status"' in p for p in problems)


# HS-3 failure message, no rewriting
def test_over_limit_reports_the_fix_and_rewrites_nothing(tmp_path):
    path = write(tmp_path, handoff(status_lines=40))
    (tmp_path / '.agent/HISTORY.md').write_text('# History\n')
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (tmp_path / '.agent').rglob('*') if p.is_file()}
    result = run(tmp_path)
    assert result.returncode == 1
    out = result.stdout + result.stderr
    assert 'BLOCKED' in out and '## Status is 40 lines' in out
    assert 'checkpoint.py' in out and 'one line' in out
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (tmp_path / '.agent').rglob('*') if p.is_file()}
    assert after == before
    assert not (tmp_path / '.agent/archives').exists()
    assert path.read_text() == handoff(status_lines=40)


def test_message_never_echoes_handoff_content(tmp_path):
    secret = 'sk-live-' + 'q' * 1_600
    write(tmp_path, handoff(line=secret))
    result = run(tmp_path)
    assert result.returncode == 1
    assert 'sk-live-' not in result.stdout + result.stderr


# HS-4 per-repository limits
def test_repository_limits_override_defaults(tmp_path):
    write(tmp_path, handoff(status_lines=40), {'status_max_lines': 50})
    assert run(tmp_path).returncode == 0


def test_malformed_limits_fall_back_to_defaults_with_a_notice(tmp_path):
    write(tmp_path, handoff(status_lines=40), '{not json')
    result = run(tmp_path)
    assert result.returncode == 1
    assert 'handoff-limits.json' in result.stdout + result.stderr
    assert 'default' in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize('bad', [0, -5, 'big', True, 1.5, None])
def test_invalid_limit_values_keep_the_default(tmp_path, bad):
    m = module()
    write(tmp_path, handoff(), {'max_bytes': bad})
    limits, notices = m.load_limits(tmp_path)
    assert limits['max_bytes'] == 24_000
    assert any('max_bytes' in n for n in notices)


# HS-5 required headings
def test_required_heading_missing_fails_and_is_named(tmp_path):
    write(tmp_path, handoff(), {'required_headings': ['## Session Timeline']})
    result = run(tmp_path)
    assert result.returncode == 1
    assert '## Session Timeline' in result.stdout + result.stderr


def test_required_heading_present_passes(tmp_path):
    write(tmp_path, handoff() + '\n## Session Timeline\n- 2026-11-25 lane a ([#2](u))\n',
          {'required_headings': ['## Session Timeline']})
    assert run(tmp_path).returncode == 0


def test_no_handoff_is_nothing_to_check(tmp_path):
    result = run(tmp_path)
    assert result.returncode == 0
    assert 'nothing to check' in result.stdout


# HS-10 the template plus one Recent-work line stays small
def test_template_plus_one_recent_work_line_passes(tmp_path):
    m = module()
    text = TEMPLATE.read_text()
    assert '## Recent work' in text
    head, tail = text.split('## Recent work\n', 1)
    text = head + '## Recent work\n- 2026-11-25 Nightly run: nothing to change, 3 items skipped ([#12](https://example.invalid/12))\n' + tail
    assert m.check_text(text, m.load_limits(tmp_path)[0]) == []


# Review finding: a variant Status heading must not dodge the Status limits.
@pytest.mark.parametrize('heading', ['## status', '## Status (Nov 25)', '##  Status', '## STATUS — current'])
def test_status_heading_variants_are_still_measured(tmp_path, heading):
    m = module()
    body = '\n'.join(f'- n{i}' for i in range(31))
    problems = m.check_text(f'# H\n{heading}\n{body}\n## Next actions\n', m.load_limits(tmp_path)[0])
    assert any('## Status is 31 lines' in p for p in problems)


def test_status_like_words_are_not_the_status_section(tmp_path):
    m = module()
    body = '\n'.join(f'- n{i}' for i in range(31))
    assert m.check_text(f'# H\n## Statusboard links\n{body}\n', m.load_limits(tmp_path)[0]) == []
