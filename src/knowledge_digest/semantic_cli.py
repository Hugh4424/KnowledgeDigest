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
from .reader_projection import compile_reader_candidate, promote_reader_seed
from . import semantic_navigation
from .semantic_navigation import build_navigation_dependencies


def _write_blocked_navigation_status(batch: Path, reason: str) -> None:
    """Best-effort blocked marker for valid, safely writable K1 batches."""
    try:
        manifest_path = batch / "_audit" / "page-manifest.json"
        if batch.is_symlink() or (batch / "_audit").is_symlink() or not manifest_path.is_file():
            return
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != "task7-page-manifest.v1":
            return
        payload["navigation"] = {
            "navigation_status": "blocked",
            "success_pages": 0,
            "blocked_sources": len(payload.get("blockers", [])) if isinstance(payload.get("blockers"), list) else 0,
            "blocked_reasons": [reason],
        }
        temporary = manifest_path.with_name(f".{manifest_path.name}.navigation.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return


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
            "digest 的历史参数已退役；请移除历史参数后使用当前 digest 参数 "
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
    parser.add_argument(
        "--reader",
        action="store_true",
        help="在 K1/K2 批次之后编译独立的 K3 Reader candidate",
    )
    parser.add_argument(
        "--reader-seed",
        type=Path,
        default=None,
        help="可选的同语料 Reader seed；先校验 89 条原文哈希，再重新绑定当前 K1/K2 审计",
    )
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
    query_fixture_value = os.environ.get("KNOWLEDGEDIGEST_TASK8_QUERY_FIXTURE")
    query_fixture = Path(query_fixture_value) if query_fixture_value else None
    try:
        if result.run_status != "complete":
            navigation = semantic_navigation.NavigationResult(
                navigation_status="blocked",
                success_pages=0,
                blocked_sources=0,
                blocked_reasons=("K1-run-not-complete",),
                nav_files=(),
            )
            _write_blocked_navigation_status(result.output_dir, "K1-run-not-complete")
        else:
            navigation_dependencies = build_navigation_dependencies(
                cache_root=args.cache_root or _env_path("KNOWLEDGEDIGEST_TASK7_CACHE_ROOT", DEFAULT_CACHE_ROOT),
                provider_config_path=None,
                query_fixture=query_fixture,
            )
            navigation = semantic_navigation.compile_batch_navigation(
                result.output_dir,
                cache=navigation_dependencies.cache,
                gateway=navigation_dependencies.gateway,
                query_fixture=navigation_dependencies.query_fixture,
            )
    except semantic_navigation.NavigationInputError as error:
        _write_blocked_navigation_status(result.output_dir, error.reason)
        navigation = semantic_navigation.NavigationResult(
            navigation_status="blocked",
            success_pages=0,
            blocked_sources=0,
            blocked_reasons=(error.reason,),
            nav_files=(),
        )
    except (OSError, TypeError, ValueError, RuntimeError) as error:
        _write_blocked_navigation_status(result.output_dir, "navigation-dependency-failed")
        navigation = semantic_navigation.NavigationResult(
            navigation_status="blocked",
            success_pages=0,
            blocked_sources=0,
            blocked_reasons=("navigation-dependency-failed", type(error).__name__),
            nav_files=(),
        )
    navigation_status = getattr(navigation, "navigation_status", navigation.as_dict().get("navigation_status", "blocked"))
    reader_projection = None
    if args.reader:
        if result.run_status != "complete" or navigation_status == "blocked":
            reader_projection = {
                "status": "blocked",
                "publish_status": "not_released",
                "reason": "reader_requires_complete_k1_k2_navigation",
            }
        else:
            try:
                if args.reader_seed is not None:
                    reader_projection = promote_reader_seed(
                        args.reader_seed,
                        result.output_dir,
                        result.output_dir / "_reader-candidate",
                        input_root=args.new_dir,
                    ).as_dict()
                else:
                    reader_projection = compile_reader_candidate(
                        result.output_dir,
                        provider=provider,
                        cache_root=args.cache_root or _env_path("KNOWLEDGEDIGEST_TASK7_CACHE_ROOT", DEFAULT_CACHE_ROOT),
                        input_root=args.new_dir,
                    ).as_dict()
            except (OSError, TypeError, ValueError, RuntimeError) as error:
                reader_projection = {
                    "status": "blocked",
                    "publish_status": "not_released",
                    "reason": "reader-projection-failed",
                    "error": f"{type(error).__name__}: {error}",
                }
    effective_outcome = (
        "blocked"
        if result.run_status == "complete" and navigation_status == "blocked"
        else result.outcome
    )
    if args.reader and (not isinstance(reader_projection, dict) or reader_projection.get("status") != "candidate"):
        effective_outcome = "blocked"
    output = {
        "outcome": effective_outcome,
        "run_status": result.run_status,
        "publish_status": result.publish_status,
        "batch": str(result.output_dir),
        "plan": dict(result.plan),
        "provider_calls": result.provider_calls,
        "cache_hits": result.cache_hits,
        "navigation": navigation.as_dict(),
        "reader": reader_projection,
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return _exit_code(effective_outcome)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
