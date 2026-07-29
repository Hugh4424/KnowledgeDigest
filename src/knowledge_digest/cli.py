"""Command-line entry point for the first KnowledgeDigest slice."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import SUPPORTED_LLM_FORMATS, resolve_settings
from .errors import ValidationError
from .kb_structure import parse_roots
from .paths import validate_paths
from .pipeline import audit_run

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "knowledge-digest.json"


class DigestArgumentParser(argparse.ArgumentParser):
    """Keep command-line input failures inside the documented error contract."""

    def error(self, message: str) -> None:
        raise ValidationError("arguments", "arguments", message)


def build_parser() -> argparse.ArgumentParser:
    parser = DigestArgumentParser(
        description="Audit new notes against a knowledge base.",
        allow_abbrev=False,
    )
    parser.add_argument("new_dir", type=Path, help="directory containing new source notes")
    parser.add_argument("kb_dir", type=Path, help="knowledge-base directory containing kb.structure.md")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="JSON settings file (defaults to the KnowledgeDigest project configuration)",
    )
    parser.add_argument("--dry-run", action="store_true", help="write only a run audit report")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--page-match-threshold", type=float, default=None)
    parser.add_argument(
        "--cluster-auto-threshold", "--high", dest="high", type=float, default=None
    )
    parser.add_argument(
        "--cluster-review-threshold", "--medium", dest="medium", type=float, default=None
    )
    parser.add_argument("--max-doc-lines", "--max-lines", dest="max_lines", type=int, default=None)
    parser.add_argument(
        "--llm-format",
        choices=SUPPORTED_LLM_FORMATS,
        default=None,
        help="provider API format; enables LLM refinement",
    )
    parser.add_argument("--llm-batch-max-claims", type=int, default=None)
    parser.add_argument("--llm-batch-max-source-chars", type=int, default=None)
    parser.add_argument("--llm-batch-concurrency", type=int, default=None)
    parser.add_argument(
        "--llm-summary",
        dest="llm_summary_enabled",
        action="store_true",
        default=None,
        help="generate a cited summary with a deterministic evidence section",
    )
    parser.add_argument(
        "--no-llm",
        dest="llm_enabled",
        action="store_false",
        default=None,
        help="force the offline identity generator (no provider calls)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        llm_enabled = args.llm_enabled
        if llm_enabled is None and args.llm_format is not None:
            llm_enabled = True
        settings = resolve_settings(
            args.config,
            top_k=args.top_k,
            page_match_threshold=args.page_match_threshold,
            high=args.high,
            medium=args.medium,
            max_lines=args.max_lines,
            llm_enabled=llm_enabled,
            llm_format=args.llm_format,
            llm_summary_enabled=args.llm_summary_enabled,
            llm_batch_max_claims=args.llm_batch_max_claims,
            llm_batch_max_source_chars=args.llm_batch_max_source_chars,
            llm_batch_concurrency=args.llm_batch_concurrency,
        )
        paths = validate_paths(args.new_dir, args.kb_dir)
        roots = parse_roots(paths.structure_path)
        report_path, summary = audit_run(paths, settings, roots, dry_run=args.dry_run)
    except ValidationError as error:
        print(str(error), file=sys.stderr)
        return 1

    print(f"{summary}; report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
