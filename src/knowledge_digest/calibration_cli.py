"""Command-line surface for the isolated Phase 4 calibration workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

from .calibration import CalibrationBlocked, build_calibration_result
from .calibration_artifact import validate_calibration_artifact
from .corpus_isolation import cleanup_disposable_corpus, prepare_disposable_corpus
from .errors import ValidationError
from .gold import canonical_json_bytes, freeze_confirmed_gold, write_gold_draft


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("calibration", path, f"invalid JSON ({error})") from error
    if not isinstance(value, dict):
        raise ValidationError("calibration", path, "JSON must be an object")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(canonical_json_bytes(value) + b"\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_sha256(value: str, field: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValidationError("calibration", field, "must be a lowercase SHA-256")
    return value


def write_recommended_config(source: Path, destination: Path) -> bool:
    """Write a fresh embedding recommendation without overriding explicit Jaccard."""
    config = _read_object(source)
    similarity = config.get("similarity")
    if not isinstance(similarity, dict):
        raise ValidationError("calibration", source, "similarity config is required")
    if destination.exists():
        existing = _read_object(destination)
        existing_similarity = existing.get("similarity")
        if isinstance(existing_similarity, dict) and existing_similarity.get("backend") == "jaccard":
            return False
        raise ValidationError(
            "calibration", destination, "recommendation destination already exists"
        )
    recommended = json.loads(json.dumps(config))
    recommended["similarity"]["backend"] = "embedding"
    _write_json(destination, recommended)
    return True


def _prepare_corpus(args: argparse.Namespace) -> int:
    result = prepare_disposable_corpus(args.source, args.kb, args.disposable)
    _write_json(args.manifest, result)
    return 0


def _cleanup_corpus(args: argparse.Namespace) -> int:
    preparation = _read_object(args.manifest)
    result = cleanup_disposable_corpus(args.disposable, preparation)
    _write_json(args.cleanup_evidence, result)
    return 0


def _freeze_gold(args: argparse.Namespace) -> int:
    freeze_confirmed_gold(args.draft, args.decisions, args.output, args.audit)
    return 0


def _draft_gold(args: argparse.Namespace) -> int:
    result = write_gold_draft(args.candidates, args.output)
    _write_json(args.audit, result)
    return 0


def _calibrate(args: argparse.Namespace) -> int:
    scored = _read_object(args.cases)
    cases = scored.get("cases")
    if not isinstance(cases, list):
        raise ValidationError("calibration", args.cases, "cases array is required")
    if args.dimension < 1:
        raise ValidationError("calibration", "dimension", "must be positive")
    for name in ("probe_fingerprint", "corpus_hash", "gold_hash", "vectors_hash"):
        _require_sha256(getattr(args, name), name)
    if args.service_failure_code:
        try:
            build_calibration_result(cases, service_failure_code=args.service_failure_code)
        except CalibrationBlocked as blocked:
            if args.output.exists():
                raise ValidationError(
                    "calibration", args.output, "refusing to overwrite an artifact on BLOCKED"
                )
            if args.blocked_evidence is None:
                raise ValidationError(
                    "calibration", "blocked_evidence", "required for service failure"
                )
            _write_json(args.blocked_evidence, blocked.evidence)
            return 2
    result = build_calibration_result(cases)
    ordered_cases = sorted(cases, key=lambda item: item["case_id"])
    gold_binding = [case.get("gold_case_hash") for case in ordered_cases]
    vector_manifest_hashes = {case.get("vector_manifest_hash") for case in ordered_cases}
    if any(not isinstance(item, str) for item in gold_binding) or _sha256(gold_binding) != args.gold_hash:
        raise ValidationError("calibration", "gold_hash", "does not bind the confirmed cases")
    if vector_manifest_hashes != {args.vectors_hash}:
        raise ValidationError("calibration", "vectors_hash", "does not bind the scored vectors")
    split_binding = [
        {
            "case_id": case["case_id"],
            "lineage_id": case["lineage_id"],
            "split": case["split"],
        }
        for case in sorted(cases, key=lambda item: item["case_id"])
    ]
    artifact: dict[str, Any] = {
        "schema_version": "calibration-artifact.v1",
        "adoption_status": result["adoption_status"],
        "endpoint_identity": args.endpoint_identity,
        "model": args.model,
        "dimension": args.dimension,
        "probe_fingerprint": args.probe_fingerprint,
        "corpus_hash": args.corpus_hash,
        "gold_hash": args.gold_hash,
        "split_hash": _sha256(split_binding),
        "vectors_hash": args.vectors_hash,
        "metrics": result["metrics"],
        "cases": result["cases"],
        "tool_version": "knowledge-digest-calibrate/0.1.0",
    }
    if result["adoption_status"] == "adopted":
        artifact["thresholds"] = result["thresholds"]
    validate_calibration_artifact(artifact)
    _write_json(args.output, artifact)
    _write_json(args.split_audit, result["metrics"]["coverage"])
    if result["adoption_status"] == "adopted" and args.recommended_config is not None:
        if args.config is None:
            raise ValidationError("calibration", "config", "required for recommendation")
        write_recommended_config(args.config, args.recommended_config)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knowledge-digest-calibrate")
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare-corpus")
    prepare.add_argument("--source", type=Path, required=True)
    prepare.add_argument("--kb", type=Path, required=True)
    prepare.add_argument("--disposable", type=Path, required=True)
    prepare.add_argument("--manifest", type=Path, required=True)
    prepare.set_defaults(handler=_prepare_corpus)

    cleanup = commands.add_parser("cleanup-corpus")
    cleanup.add_argument("--disposable", type=Path, required=True)
    cleanup.add_argument("--manifest", type=Path, required=True)
    cleanup.add_argument("--cleanup-evidence", type=Path, required=True)
    cleanup.set_defaults(handler=_cleanup_corpus)

    gold = commands.add_parser("freeze-gold")
    gold.add_argument("--draft", type=Path, required=True)
    gold.add_argument("--decisions", type=Path, required=True)
    gold.add_argument("--output", type=Path, required=True)
    gold.add_argument("--audit", type=Path, required=True)
    gold.set_defaults(handler=_freeze_gold)

    draft = commands.add_parser("draft-gold")
    draft.add_argument("--candidates", type=Path, required=True)
    draft.add_argument("--output", type=Path, required=True)
    draft.add_argument("--audit", type=Path, required=True)
    draft.set_defaults(handler=_draft_gold)

    calibrate = commands.add_parser("calibrate")
    calibrate.add_argument("--cases", type=Path, required=True)
    calibrate.add_argument("--output", type=Path, required=True)
    calibrate.add_argument("--split-audit", type=Path, required=True)
    calibrate.add_argument("--endpoint-identity", required=True)
    calibrate.add_argument("--model", required=True)
    calibrate.add_argument("--dimension", type=int, required=True)
    calibrate.add_argument("--probe-fingerprint", required=True)
    calibrate.add_argument("--corpus-hash", required=True)
    calibrate.add_argument("--gold-hash", required=True)
    calibrate.add_argument("--vectors-hash", required=True)
    calibrate.add_argument("--service-failure-code")
    calibrate.add_argument("--blocked-evidence", type=Path)
    calibrate.add_argument("--config", type=Path)
    calibrate.add_argument("--recommended-config", type=Path)
    calibrate.set_defaults(handler=_calibrate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        return int(args.handler(args))
    except (ValidationError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
