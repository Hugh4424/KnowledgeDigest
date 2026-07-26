"""Single-writer mutual exclusion for one knowledge base."""

from __future__ import annotations

import fcntl
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path

from .errors import ValidationError


LOCK_FILENAME = ".digest.lock"


@contextmanager
def kb_lock(kb_dir: Path) -> Iterator[Path]:
    """Hold an exclusive non-blocking lock on kb_dir for the whole run."""
    lock_path = kb_dir / LOCK_FILENAME
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValidationError(
                "kb_lock",
                lock_path,
                "another digest run is processing this knowledge base; retry later",
            ) from error
        try:
            yield lock_path
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()
