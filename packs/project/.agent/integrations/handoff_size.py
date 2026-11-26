#!/usr/bin/env python3
"""Check that .agent/HANDOFF.md stays one short current checkpoint (a pointer, not a log).

Usage: handoff_size.py [repo-root]   exit 0 within limits, 1 when a limit is broken.

Limits (override per repository in .agent/handoff-limits.json; changes need review):
  max_bytes 24000, status_max_lines 30, status_max_bytes 4000, max_line_chars 1500,
  required_headings [] (headings the repository's own tooling needs).
It only reads and reports. It never archives, rewrites or prints HANDOFF content.
Python 3 standard library only.
"""
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True

HANDOFF_REL = '.agent/HANDOFF.md'
CONFIG_REL = '.agent/handoff-limits.json'
DEFAULTS = {'max_bytes': 24_000, 'status_max_lines': 30, 'status_max_bytes': 4_000,
            'max_line_chars': 1_500, 'required_headings': []}
FIX = ('Move finished narrative to history with `.agent/integrations/checkpoint.py` (write a short '
       'candidate, then `python3 .agent/integrations/checkpoint.py . --candidate <path> '
       '--expected-sha256 <sha> --reviewed`), and keep each entry to one line that links to the '
       'PR, issue or document holding the detail.')


def load_limits(root):
    """Return (limits, notices). A bad config value keeps its default and says so."""
    limits = dict(DEFAULTS, required_headings=[])
    notices = []
    path = Path(root) / CONFIG_REL
    if not path.is_file():
        return limits, notices
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('not a JSON object')
    except (ValueError, OSError) as exc:
        notices.append(f'{CONFIG_REL} is unreadable ({exc.__class__.__name__}); using the default limits.')
        return limits, notices
    for key, value in data.items():
        if key == 'required_headings':
            if isinstance(value, list) and all(isinstance(h, str) and h.startswith('#') for h in value):
                limits[key] = [h.strip() for h in value]
            else:
                notices.append(f'{CONFIG_REL}: required_headings must be a list of headings; ignored.')
        elif key in DEFAULTS:
            if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                limits[key] = value
            else:
                notices.append(f'{CONFIG_REL}: {key} must be a positive whole number; using the default {DEFAULTS[key]}.')
        else:
            notices.append(f'{CONFIG_REL}: unknown key {key!r} ignored.')
    return limits, notices


_STATUS = re.compile(r'##\s+status\b', re.IGNORECASE)


def _section(lines, pattern):
    """The body of the first `## ` section whose heading matches, up to the next `## `
    heading, blank edges trimmed. Variants such as `## status (Nov 25)` still count."""
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            body = []
            for rest in lines[i + 1:]:
                if rest.startswith('## '):
                    break
                body.append(rest)
            return '\n'.join(body).strip()
    return None


def check_text(text, limits):
    """Return a list of problems; empty means within limits. Never quotes the content."""
    if isinstance(text, bytes):
        size, text = len(text), text.decode('utf-8', errors='replace')
    else:
        size = len(text.encode('utf-8'))
    lines = text.replace('\r\n', '\n').split('\n')
    problems = []
    if size > limits['max_bytes']:
        problems.append(f'HANDOFF is {size} bytes (limit {limits["max_bytes"]}).')
    status = _section(lines, _STATUS)
    if status is not None:  # a missing Status is bounded by max_bytes; require it via required_headings
        count, nbytes = len(status.split('\n')), len(status.encode('utf-8'))
        if count > limits['status_max_lines']:
            problems.append(f'## Status is {count} lines (limit {limits["status_max_lines"]}).')
        if nbytes > limits['status_max_bytes']:
            problems.append(f'## Status is {nbytes} bytes (limit {limits["status_max_bytes"]}).')
    long = [f'line {n} ({len(line)} chars)' for n, line in enumerate(lines, 1) if len(line) > limits['max_line_chars']]
    if long:
        problems.append(f'Lines over {limits["max_line_chars"]} characters: {", ".join(long[:10])}'
                        + (f' and {len(long) - 10} more.' if len(long) > 10 else '.'))
    present = {line.strip() for line in lines}
    for heading in limits['required_headings']:
        if heading not in present:
            problems.append(f'HANDOFF must keep the "{heading}" heading this repository\'s tooling needs.')
    return problems


def check_repo(root):
    """Return (problems, notices) for root/.agent/HANDOFF.md; no file means nothing to check."""
    limits, notices = load_limits(root)
    path = Path(root) / HANDOFF_REL
    if not path.is_file():
        return [], notices
    return check_text(path.read_bytes(), limits), notices


def message(problems):
    return 'BLOCKED: .agent/HANDOFF.md must stay one short checkpoint. ' + ' '.join(problems) + ' ' + FIX


def main(argv):
    root = Path(argv[1] if len(argv) > 1 else '.')
    if not (root / HANDOFF_REL).is_file():
        print(f'OK: no {HANDOFF_REL}; nothing to check.')
        return 0
    problems, notices = check_repo(root)
    for notice in notices:
        print(f'NOTICE: {notice}', file=sys.stderr)
    if problems:
        print(message(problems), file=sys.stderr)
        return 1
    print(f'OK: {HANDOFF_REL} is within the size limits.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
