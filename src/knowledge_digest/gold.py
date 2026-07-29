"""Offline AI-draft exchange and explicit per-item gold confirmation."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import ValidationError

_DRAFT_FIELDS = frozenset(
    {
        "case_id",
        "lineage_id",
        "content_identity",
        "stage",
        "stratum",
        "ai_label",
        "label_version",
        "left_ref",
        "right_ref",
        "right_root",
        "query_id",
        "gold_action",
    }
)
_DECISION_FIELDS = frozenset(
    {
        "case_id",
        "decision",
        "label",
        "lineage_id",
        "content_identity",
        "draft_hash",
    }
)
_CONFIRMED_CASE_FIELDS = frozenset(
    {
        "case_id",
        "lineage_id",
        "content_identity",
        "stage",
        "stratum",
        "label",
        "label_version",
        "left_ref",
        "right_ref",
        "right_root",
        "query_id",
        "gold_action",
        "confirmed",
    }
)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _read_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("gold", path, f"invalid {label} JSONL ({error})") from error
    if not rows or not all(isinstance(row, dict) for row in rows):
        raise ValidationError("gold", path, f"{label} must contain JSON objects")
    return rows


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


def write_gold_draft(candidate_path: Path, output_path: Path) -> dict[str, Any]:
    """Validate and freeze an AI-produced draft exchange without confirming it."""
    rows = _read_jsonl(candidate_path, "AI draft candidate")
    seen: set[str] = set()
    for row in rows:
        if set(row) != _DRAFT_FIELDS:
            raise ValidationError("gold", "draft", "draft fields must match the exact schema")
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ValidationError("gold", "case_id", "must be unique and non-empty")
        seen.add(case_id)
        _validate_sha256(row.get("content_identity"), "content_identity")
        if row.get("stage") not in {"S2", "S3"}:
            raise ValidationError("gold", "stage", "must be S2 or S3")
        if not isinstance(row.get("lineage_id"), str) or not row["lineage_id"]:
            raise ValidationError("gold", "lineage_id", "must be non-empty")
        if not isinstance(row.get("stratum"), dict) or not row["stratum"]:
            raise ValidationError("gold", "stratum", "must be a non-empty object")
        if not isinstance(row.get("ai_label"), str) or not row["ai_label"]:
            raise ValidationError("gold", "ai_label", "must be non-empty")
        if not isinstance(row.get("label_version"), str) or not row["label_version"]:
            raise ValidationError("gold", "label_version", "must be non-empty")
        for field in ("left_ref", "right_ref", "right_root", "query_id"):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ValidationError("gold", field, "must be non-empty")
        if row["right_root"] not in {"corpus", "kb"}:
            raise ValidationError("gold", "right_root", "must be corpus or kb")
        _validate_right_root(row["stage"], row["right_root"])
        if row["stage"] == "S3" and row.get("gold_action") not in {"new", "revise", "merge_multiple"}:
            raise ValidationError("gold", "gold_action", "is required for S3")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{output_path.name}.", dir=output_path.parent)
    try:
        with os.fdopen(descriptor, "wb") as target:
            for row in sorted(rows, key=lambda item: item["case_id"]):
                target.write(canonical_json_bytes(row) + b"\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, output_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {
        "schema_version": "gold-draft-exchange.v1",
        "case_count": len(rows),
        "draft_hash": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "confirmed_count": 0,
    }


def _validate_sha256(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValidationError("gold", field, "must be a lowercase SHA-256")
    return value


def _validate_right_root(stage: str, right_root: str) -> None:
    expected = "corpus" if stage == "S2" else "kb"
    if right_root != expected:
        raise ValidationError("gold", "right_root", f"{stage} requires {expected}")


def _validate_confirmed_case(case: dict[str, Any]) -> None:
    if set(case) != _CONFIRMED_CASE_FIELDS:
        raise ValidationError("gold", "case", "confirmed case fields must match the exact schema")
    for field in ("case_id", "lineage_id", "label", "label_version", "left_ref", "right_ref", "query_id"):
        if not isinstance(case[field], str) or not case[field]:
            raise ValidationError("gold", field, "must be non-empty")
    _validate_sha256(case["content_identity"], "content_identity")
    if case["stage"] not in {"S2", "S3"}:
        raise ValidationError("gold", "stage", "must be S2 or S3")
    if not isinstance(case["stratum"], dict) or not case["stratum"]:
        raise ValidationError("gold", "stratum", "must be a non-empty object")
    if case["right_root"] not in {"corpus", "kb"}:
        raise ValidationError("gold", "right_root", "must be corpus or kb")
    _validate_right_root(case["stage"], case["right_root"])
    if case["stage"] == "S2":
        if case["gold_action"] is not None:
            raise ValidationError("gold", "gold_action", "must be null for S2")
    elif case["gold_action"] not in {"new", "revise", "merge_multiple"}:
        raise ValidationError("gold", "gold_action", "is required for S3")
    if case["confirmed"] is not True:
        raise ValidationError("gold", "confirmed", "must be true")


def freeze_confirmed_gold(
    draft_path: Path,
    decisions_path: Path,
    output_path: Path,
    audit_path: Path,
) -> dict[str, Any]:
    """Freeze gold only when every draft item has one explicit user decision."""
    if output_path.resolve() == audit_path.resolve():
        raise ValidationError("gold", output_path, "gold and audit paths must differ")
    drafts = _read_jsonl(draft_path, "draft")
    decisions = _read_jsonl(decisions_path, "decision")
    draft_hash = hashlib.sha256(draft_path.read_bytes()).hexdigest()
    by_id: dict[str, dict[str, Any]] = {}
    for row in drafts:
        if set(row) != _DRAFT_FIELDS:
            raise ValidationError("gold", "draft", "draft fields must match the exact schema")
        case_id = row["case_id"]
        if not isinstance(case_id, str) or not case_id or case_id == "*" or case_id in by_id:
            raise ValidationError("gold", "case_id", "must be unique and non-empty")
        if not isinstance(row["lineage_id"], str) or not row["lineage_id"]:
            raise ValidationError("gold", "lineage_id", "must be non-empty")
        _validate_sha256(row["content_identity"], "content_identity")
        if row["stage"] not in {"S2", "S3"}:
            raise ValidationError("gold", "stage", "must be S2 or S3")
        if not isinstance(row["stratum"], dict) or not row["stratum"]:
            raise ValidationError("gold", "stratum", "must be a non-empty object")
        if not isinstance(row["ai_label"], str) or not row["ai_label"]:
            raise ValidationError("gold", "ai_label", "must be non-empty")
        if not isinstance(row["label_version"], str) or not row["label_version"]:
            raise ValidationError("gold", "label_version", "must be non-empty")
        for field in ("left_ref", "right_ref", "right_root", "query_id"):
            if not isinstance(row[field], str) or not row[field]:
                raise ValidationError("gold", field, "must be non-empty")
        if row["right_root"] not in {"corpus", "kb"}:
            raise ValidationError("gold", "right_root", "must be corpus or kb")
        _validate_right_root(row["stage"], row["right_root"])
        if row["stage"] == "S3" and row["gold_action"] not in {"new", "revise", "merge_multiple"}:
            raise ValidationError("gold", "gold_action", "is required for S3")
        by_id[case_id] = row

    decision_by_id: dict[str, dict[str, Any]] = {}
    for row in decisions:
        required = _DECISION_FIELDS - {"label"}
        if not set(row).issubset(_DECISION_FIELDS) or not required <= set(row):
            raise ValidationError("gold", "decision", "decision fields are invalid")
        case_id = row["case_id"]
        if case_id not in by_id or case_id in decision_by_id:
            raise ValidationError("gold", "decision", "each known case needs one decision")
        if row["decision"] not in {"confirm", "reject"}:
            raise ValidationError("gold", "decision", "must be confirm or reject")
        draft = by_id[case_id]
        if (
            row["lineage_id"] != draft["lineage_id"]
            or row["content_identity"] != draft["content_identity"]
            or row["draft_hash"] != draft_hash
        ):
            raise ValidationError(
                "gold", case_id, "decision identity or draft hash mismatch"
            )
        if "label" in row and (
            row["decision"] != "confirm"
            or not isinstance(row["label"], str)
            or not row["label"]
        ):
            raise ValidationError("gold", "label", "override is valid only for confirmation")
        decision_by_id[case_id] = row
    missing = sorted(set(by_id) - set(decision_by_id))
    if missing:
        raise ValidationError("gold", "decision", f"missing per-item decision: {', '.join(missing)}")

    confirmed: list[dict[str, Any]] = []
    audit_decisions: list[dict[str, str]] = []
    for case_id in sorted(by_id):
        draft = by_id[case_id]
        decision = decision_by_id[case_id]
        audit_decisions.append(
            {
                "case_id": case_id,
                "lineage_id": draft["lineage_id"],
                "content_identity": draft["content_identity"],
                "decision": decision["decision"],
                "draft_hash": draft_hash,
            }
        )
        if decision["decision"] == "confirm":
            confirmed.append(
                {
                    "case_id": case_id,
                    "lineage_id": draft["lineage_id"],
                    "content_identity": draft["content_identity"],
                    "stage": draft["stage"],
                    "stratum": draft["stratum"],
                    "label": decision.get("label", draft["ai_label"]),
                    "label_version": draft["label_version"],
                    "left_ref": draft["left_ref"],
                    "right_ref": draft["right_ref"],
                    "right_root": draft["right_root"],
                    "query_id": draft["query_id"],
                    "gold_action": draft["gold_action"],
                    "confirmed": True,
                }
            )
    case_hashes = [
        hashlib.sha256(canonical_json_bytes(case)).hexdigest()
        for case in confirmed
    ]
    gold_hash = hashlib.sha256(canonical_json_bytes(case_hashes)).hexdigest()
    gold = {
        "schema_version": "confirmed-gold.v1",
        "unconfirmed_count": 0,
        "gold_hash": gold_hash,
        "cases": confirmed,
    }
    audit = {
        "schema_version": "gold-confirmation-audit.v1",
        "unconfirmed_count": 0,
        "draft_count": len(drafts),
        "confirmed_count": len(confirmed),
        "rejected_count": len(drafts) - len(confirmed),
        "gold_hash": gold_hash,
        "decisions": audit_decisions,
    }
    _write_json(output_path, gold)
    _write_json(audit_path, audit)
    return gold


def load_confirmed_gold(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("gold", path, f"invalid confirmed gold ({error})") from error
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "unconfirmed_count",
        "gold_hash",
        "cases",
    }:
        raise ValidationError("gold", path, "confirmed gold has an invalid schema")
    if value["schema_version"] != "confirmed-gold.v1" or value["unconfirmed_count"] != 0:
        raise ValidationError("gold", path, "gold is not fully confirmed")
    cases = value["cases"]
    if not isinstance(cases, list) or not cases or not all(
        isinstance(case, dict) for case in cases
    ):
        raise ValidationError("gold", path, "unconfirmed case cannot enter metrics")
    seen: set[str] = set()
    for case in cases:
        _validate_confirmed_case(case)
        if case["case_id"] in seen:
            raise ValidationError("gold", "case_id", "must be unique")
        seen.add(case["case_id"])
    actual_hash = hashlib.sha256(
        canonical_json_bytes(
            [hashlib.sha256(canonical_json_bytes(case)).hexdigest() for case in cases]
        )
    ).hexdigest()
    if value["gold_hash"] != actual_hash:
        raise ValidationError("gold", path, "gold hash mismatch")
    return value
