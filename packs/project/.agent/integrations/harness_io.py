"""Small shared filesystem primitives; no shell evaluation or external dependencies."""
import hashlib
import os
from pathlib import Path
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts or rel.parts[0] == '.git':
        raise ValueError(f'unsafe relative path: {relative}')
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f'refusing symlink: {path}')
        if path.exists():
            if path == root / rel and not path.is_file():
                raise ValueError(f'not a regular file: {path}')
            if path != root / rel and not path.is_dir():
                raise ValueError(f'not a directory: {path}')
    return path


def read_optional(path):
    return path.read_bytes() if path.exists() else None


def create_file(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def replace_checked(path, data, expected):
    if read_optional(path) != expected:
        raise ValueError(f'changed during operation: {path}')
    fd, temp = tempfile.mkstemp(prefix='.harness-write-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if read_optional(path) != expected:
            raise ValueError(f'changed during operation: {path}')
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
