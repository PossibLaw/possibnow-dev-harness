#!/usr/bin/env python3
"""Archive exact prior bytes, verify, and install a human/agent-reviewed checkpoint.

Semantic completeness requires review; hashes enforce byte preservation, not meaning.
The lock serializes this helper's writers. External editors must still be coordinated.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.dont_write_bytecode = True

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_io import create_file, read_optional, replace_checked, safe_path, sha


def archive_bytes(path, data):
    if not path.exists():
        create_file(path, data)
    if path.read_bytes() != data:
        raise ValueError(f'archive verification failed: {path}')


def checkpoint(root, candidate, expected_sha):
    root = Path(root).resolve()
    handoff = safe_path(root, '.agent/HANDOFF.md')
    history = safe_path(root, '.agent/HISTORY.md')
    new = Path(candidate).read_bytes()
    for heading in (b'## Status', b'## Unresolved work', b'## Active constraints', b'## Evidence', b'## Next actions'):
        if heading not in new.splitlines():
            raise ValueError(f'candidate missing section: {heading.decode()}')
    lock = safe_path(root, '.agent/.checkpoint.lock')
    create_file(lock, b'checkpoint in progress\n')
    try:
        old = handoff.read_bytes()
        if sha(old) != expected_sha:
            raise ValueError('HANDOFF changed since review; regenerate the candidate')
        if new == old:
            return 'unchanged'
        archive_rel = f'.agent/archives/handoffs/{sha(old)}.md'
        archive = safe_path(root, archive_rel)
        previous_history = read_optional(history)
        archive_bytes(archive, old)
        if handoff.read_bytes() != old:
            raise ValueError('HANDOFF changed during archival')
        checkpoint_id = 'checkpoint-' + sha(old)
        marker = f'<!-- {checkpoint_id} -->'.encode()
        if marker not in (previous_history or b''):
            stamp = datetime.now(timezone.utc).isoformat()
            entry = (f'\n\n{marker.decode()}\n## {checkpoint_id}\n'
                     f'Archived at: {stamp}\n\nSHA-256: `{sha(old)}`\n\n'
                     f'Exact prior bytes: [checkpoint](archives/handoffs/{sha(old)}.md)\n').encode()
            replace_checked(history, (previous_history or b'# Historical Handoffs\n') + entry, previous_history)
        else:
            block = previous_history.split(marker, 1)[1].split(b'<!-- checkpoint-', 1)[0]
            if (f'SHA-256: `{sha(old)}`'.encode() not in block or
                    f'(archives/handoffs/{sha(old)}.md)'.encode() not in block or
                    b'Archived at:' not in block):
                raise ValueError('conflicting checkpoint ID in HISTORY')
            if read_optional(history) != previous_history:
                raise ValueError('HISTORY changed during archival')
        # Verify persisted bytes and locator immediately before replacing HANDOFF.
        if archive.read_bytes() != old or marker not in history.read_bytes():
            raise ValueError('archive verification failed')
        replace_checked(handoff, new, old)
        return checkpoint_id
    finally:
        lock.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', type=Path)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--reviewed', action='store_true', required=True,
                        help='Confirm candidate retains unresolved work/active constraints and source is sanitized')
    args = parser.parse_args()
    try:
        print(checkpoint(args.target, args.candidate, args.expected_sha256))
    except (ValueError, OSError) as exc:
        print(f'BLOCKED: {exc}', file=sys.stderr)
        sys.exit(1)
