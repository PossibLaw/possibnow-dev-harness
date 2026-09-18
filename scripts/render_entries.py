#!/usr/bin/env python3
"""Generate two small host adapters from one authored entry."""
import sys
from pathlib import Path
from entry_policy import validate

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = {
    'AGENTS.md': 'Host: AGENTS-aware clients discover this entry according to their own precedence rules.',
    'CLAUDE.md': 'Host: Claude Code discovers this entry; no automatic handbook imports are used.',
}


def render():
    body = (ROOT / 'packs/entry.md').read_text()
    for name, adapter in ADAPTERS.items():
        data = ('<!-- Generated from packs/entry.md; edit that source in the harness. -->\n'
                + body + '\n' + adapter + '\n').encode()
        validate(data, name)
        p = ROOT / 'packs/project' / name
        if '--check' in sys.argv:
            if p.read_bytes() != data:
                raise ValueError(f'{name} is out of sync; run scripts/render_entries.py')
        else:
            p.write_bytes(data)


if __name__ == '__main__':
    try:
        render()
    except (ValueError, OSError) as exc:
        print(f'BLOCKED: {exc}', file=sys.stderr)
        sys.exit(1)
