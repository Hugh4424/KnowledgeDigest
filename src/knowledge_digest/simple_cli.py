"""Stable ``digest`` entry point for the Task7 semantic compiler."""

from __future__ import annotations

import sys

from .semantic_cli import main as _semantic_main


def _exit_code(outcome: str) -> int:
    """Keep the historical public outcome mapping for compatibility imports."""

    return {
        "released": 0,
        "completed": 0,
        "not_released": 1,
        "blocked": 2,
        "interrupted": 2,
        "unavailable": 2,
        "failed": 3,
        "cancelled": 4,
    }.get(str(outcome), 3)


def main(argv: list[str] | None = None) -> int:
    invocation = list(argv) if argv is not None else sys.argv[1:]
    legacy_flags = (
        "--no-llm",
        "--config",
        "--provider-config",
        "--quality-config",
        "--slice-config",
        "--companybrain-root",
        "--gate",
        "--fixture-bundle",
        "--m401-attempt",
        "--m401-run-root",
        "--m401-packet",
        "--m401-r-receipt",
        "--workflowhub-successor",
    )
    if any(
        argument == flag or argument.startswith(flag + "=")
        for argument in invocation
        for flag in legacy_flags
    ):
        print(
            "digest 的历史参数已退役；请移除历史参数后使用当前 digest 参数 "
            + " ".join(invocation),
            file=sys.stderr,
        )
        raise SystemExit(2)
    return _semantic_main(invocation)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["_exit_code", "main"]
