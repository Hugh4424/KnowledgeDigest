#!/usr/bin/env python3
"""One-shot reference entry point for the pre-Task7 reader compiler.

This deliberately keeps the old command surface in a script. The production
``digest`` entry point no longer dispatches to it, while existing comparison
workflows can still invoke the same compiler modules and flags explicitly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT / "src"))

from knowledge_digest.companybrain_snapshot import build_companybrain_snapshot
from knowledge_digest.compiler import DigestRequest, digest, digest_slice_then_full


def _exit_code(outcome: str) -> int:
    return {
        "released": 0,
        "completed": 0,
        "not_released": 1,
        "blocked": 2,
        "unavailable": 2,
        "failed": 3,
        "cancelled": 4,
    }.get(str(outcome), 3)


def _slice_source_paths(path: Path) -> tuple[str, ...]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"slice config is invalid: {path}") from error
    if not isinstance(value, dict) or value.get("schema_version") != "task5-slice-cases.v1":
        raise ValueError("slice config schema_version is invalid")
    cases = value.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("slice config has no cases")
    seen_cases: set[str] = set()
    result: list[str] = []
    seen_paths: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("slice config case is invalid")
        case_id = str(case.get("case_id", "")).strip()
        paths = case.get("source_paths")
        if not case_id or case_id in seen_cases or not isinstance(paths, list) or not paths:
            raise ValueError("slice config case identity or paths are invalid")
        seen_cases.add(case_id)
        for raw_path in paths:
            relative = str(raw_path).strip()
            candidate = Path(relative)
            if not relative or candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
                raise ValueError(f"slice source path is unsafe: {relative}")
            if relative not in seen_paths:
                seen_paths.add(relative)
                result.append(relative)
    if not result:
        raise ValueError("slice config derives no source paths")
    return tuple(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="legacy_digest_reference",
        description="旧版 KnowledgeDigest reader compiler 对照入口",
        allow_abbrev=False,
    )
    parser.add_argument("new_dir", nargs="?", type=Path, help="原始资料目录")
    parser.add_argument("kb_dir", nargs="?", type=Path, help="新的知识库输出目录")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--provider-config", type=Path, default=None)
    parser.add_argument("--quality-config", type=Path, default=None)
    parser.add_argument("--slice-config", type=Path, default=None)
    parser.add_argument("--companybrain-root", type=Path, default=None)
    parser.add_argument("--gate", choices=("M401", "M402"), default=None)
    parser.add_argument("--fixture-bundle", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--m401-attempt", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--m401-run-root", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--m401-packet", type=Path, default=None)
    parser.add_argument("--m401-r-receipt", type=Path, default=None)
    parser.add_argument("--workflowhub-successor", type=Path, default=None)
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args(argv)
    invocation = list(argv) if argv is not None else sys.argv[1:]
    if args.gate == "M401":
        if (args.new_dir is None) != (args.kb_dir is None):
            parser.error("M401 accepts either both reader positionals or neither")
        if args.new_dir is None:
            args.new_dir = Path(".")
            args.kb_dir = Path(".")
    elif args.new_dir is None or args.kb_dir is None:
        parser.error("new_dir and kb_dir are required outside the flag-only M401 gate")
    m401_command = json.dumps(["digest", *invocation], ensure_ascii=False, separators=(",", ":"))
    if args.config is not None and args.provider_config is not None and args.gate != "M402":
        parser.error("--config and --provider-config cannot be combined")
    if args.gate == "M402" and args.config is None:
        parser.error("M402 requires --config=<runtime-config>")
    if args.gate == "M402" and args.provider_config is None:
        parser.error("M402 requires --provider-config=<provider-config>")
    provider_config = args.provider_config or (None if args.gate == "M402" else args.config) or (
        Path.home() / ".config" / "knowledge-digest" / "config.json"
    )
    if args.no_llm:
        if args.quality_config is not None or args.slice_config is not None or args.gate is not None:
            parser.error("--quality-config/--slice-config/--gate cannot be combined with --no-llm")
        from knowledge_digest.cli import main as offline_main

        return offline_main(list(argv) if argv is not None else sys.argv[1:])
    try:
        companybrain_snapshot = (
            None
            if args.gate == "M402"
            else (
                build_companybrain_snapshot(args.companybrain_root)
                if args.companybrain_root is not None
                else None
            )
        )
        common = {
            "gate": args.gate,
            "runtime_config_path": args.config,
            "m401_packet_path": args.m401_packet,
            "m401_r_receipt_path": args.m401_r_receipt,
            "workflowhub_successor_path": args.workflowhub_successor,
            "companybrain_root": args.companybrain_root,
            "fixture_bundle_path": args.fixture_bundle,
            "m401_attempt_path": args.m401_attempt,
            "m401_run_root_path": args.m401_run_root,
            "m401_command": m401_command,
            "companybrain_route_snapshot": companybrain_snapshot,
        }
        if args.slice_config is not None:
            slice_paths = _slice_source_paths(args.slice_config)
            slice_request = DigestRequest(
                args.new_dir,
                args.kb_dir.with_name(args.kb_dir.name + ".slice-check"),
                provider_config,
                args.quality_config,
                source_paths=slice_paths,
                evaluation_mode="slice",
                **common,
            )
            full_request = DigestRequest(
                args.new_dir,
                args.kb_dir,
                provider_config,
                args.quality_config,
                evaluation_mode="full",
                **common,
            )
            sequence = digest_slice_then_full(slice_request, full_request)
            result = sequence.full_result
            output = {
                "outcome": result.outcome,
                "run_id": result.run_id,
                "slice_run_id": sequence.slice_run_id,
                "reused_response_count": sequence.reused_response_count,
                "home": str(result.home_path) if result.home_path else None,
                "audit": str(result.audit_path) if result.audit_path else None,
                "reason": result.reason_code,
            }
        else:
            result = digest(DigestRequest(
                args.new_dir,
                args.kb_dir,
                provider_config,
                args.quality_config,
                **common,
            ))
            output = {
                "outcome": result.outcome,
                "run_id": result.run_id,
                "home": str(result.home_path) if result.home_path else None,
                "audit": str(result.audit_path) if result.audit_path else None,
                "reason": result.reason_code,
            }
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(output, ensure_ascii=False))
    return _exit_code(result.outcome)


if __name__ == "__main__":
    raise SystemExit(main())
