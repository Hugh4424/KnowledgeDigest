#!/usr/bin/env python3
"""Retired Task5 runner.

The production entry point is the registered ``digest`` command.  Keeping
this filename as a failing shim prevents old automation from silently
starting the historical runtime and producing a second output contract.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "scripts/task5_reader_quality.py is retired; use the digest CLI gate "
        "(`digest --gate M401` or `digest --gate M402`).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
