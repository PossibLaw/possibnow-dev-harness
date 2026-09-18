#!/usr/bin/env python3
"""Validate physical entry lines and reject automatic instruction imports."""
import re
import sys
from pathlib import Path

LIMIT = 150


def physical_lines(data):
    return data.count(b'\n') + int(bool(data) and not data.endswith(b'\n'))


def validate(data, label):
    count = physical_lines(data)
    if count > LIMIT:
        raise ValueError(f'{label}: {count} physical lines exceeds {LIMIT}')
    # No eager @file imports, even inline ones. Email addresses are not imports.
    if re.search(rb'(?:^|[\s`])@[^\s`]+', data, re.M):
        raise ValueError(f'{label}: eager instruction import; use a task-specific Markdown route')
    return count


if __name__ == '__main__':
    try:
        for arg in sys.argv[1:]:
            data = Path(arg).read_bytes()
            print(f'{arg}: {validate(data, arg)} lines; {len(data.split())} words; {len(data)} bytes')
    except (ValueError, OSError) as exc:
        print(f'BLOCKED: {exc}', file=sys.stderr)
        sys.exit(1)
