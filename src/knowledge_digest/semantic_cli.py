"""Public CLI for the Task7 semantic compiler."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .semantic_compiler import (
    DEFAULT_CACHE_ROOT,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_OUTPUT_PARENT,
    configured_provider_from_env,
    compile_batch,
)


def _exit_code(outcome: str) -> int:
    return {
        "not_released": 1,
        "released": 0,
        "completed": 0,
        "blocked": 2,
        "interrupted": 2,
        "unavailable": 2,
        "failed": 3,
        "cancelled": 4,
    }.get(str(outcome), 3)


def _env_path(name: str, fallback: Path) -> Path:
    value = os.environ.get(name)
    return Path(value) if value else fallback


_LEGACY_FLAGS = (
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


def main(argv: list[str] | None = None) -> int:
    invocation = list(argv) if argv is not None else sys.argv[1:]
    if any(
        argument == flag or argument.startswith(flag + "=")
        for argument in invocation
        for flag in _LEGACY_FLAGS
    ):
        print(
            "digest 的历史参数已迁移；请使用 python scripts/legacy_digest_reference.py "
            + " ".join(invocation),
            file=sys.stderr,
        )
        return 2
    parser = argparse.ArgumentParser(
        prog="digest",
        description="把冻结的本地语料编译成 KnowledgeDigest 语义批次",
        allow_abbrev=False,
    )
    parser.add_argument("new_dir", type=Path, help="冻结语料目录；来源文件位于 new_dir/items")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="冻结来源清单；默认使用 config/task4-source-coverage-89-input.v1.json",
    )
    parser.add_argument("--model-id", default="task7-semantic-model", help=argparse.SUPPRESS)
    parser.add_argument("--prompt-version", default="task7-semantic-compiler-v1", help=argparse.SUPPRESS)
    parser.add_argument("--topic-map", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--output-parent", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--cache-root", type=Path, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(invocation)
    provider = configured_provider_from_env()

    result = compile_batch(
        args.new_dir,
        manifest_path=args.manifest,
        output_parent=args.output_parent or _env_path("KNOWLEDGEDIGEST_TASK7_OUTPUT_PARENT", DEFAULT_OUTPUT_PARENT),
        topic_map_path=args.topic_map,
        cache_root=args.cache_root or _env_path("KNOWLEDGEDIGEST_TASK7_CACHE_ROOT", DEFAULT_CACHE_ROOT),
        provider=provider,
        model_id=args.model_id,
        prompt_version=args.prompt_version,
        stdout=sys.stderr,
    )
    output = {
        "outcome": result.outcome,
        "run_status": result.run_status,
        "publish_status": result.publish_status,
        "batch": str(result.output_dir),
        "plan": dict(result.plan),
        "provider_calls": result.provider_calls,
        "cache_hits": result.cache_hits,
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return _exit_code(result.outcome)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
