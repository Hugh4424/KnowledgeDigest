#!/usr/bin/env python3
"""CLI for the isolated full-corpus Reader compiler and batch quality table."""

from __future__ import annotations

import argparse
import json
import signal
from pathlib import Path

from knowledge_digest.task4_reader_quality import assess_reader_quality, compile_full_reader


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile and assess the Task4 full Reader candidate")
    sub = parser.add_subparsers(dest="command", required=True)
    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("--raw-input", required=True, type=Path)
    compile_parser.add_argument("--output", required=True, type=Path)
    compile_parser.add_argument("--config", required=True, type=Path)
    compile_parser.add_argument("--semantic-candidate", type=Path)
    assess_parser = sub.add_parser("assess")
    assess_parser.add_argument("--candidate", required=True, type=Path)
    assess_parser.add_argument("--companybrain", required=True, type=Path)
    assess_parser.add_argument("--quality-config", required=True, type=Path)
    assess_parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "compile":
        interrupted = {"value": False}

        def on_signal(_signum: int, _frame: object) -> None:
            interrupted["value"] = True

        previous = signal.signal(signal.SIGINT, on_signal)
        try:
            result = compile_full_reader(args.raw_input, args.output, args.config, cancel_check=lambda: interrupted["value"])
        finally:
            signal.signal(signal.SIGINT, previous)
    else:
        result = assess_reader_quality(args.candidate, args.companybrain, args.quality_config, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") in {"candidate", "better_than_companybrain", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
