"""Evidence-only Task5 quality gate.

The gate never accepts a caller-supplied verdict.  It runs the existing
black-box evaluator against the actual candidate, raw corpus and CompanyBrain
tree, then stores only the evaluator's recomputed result and a sanitized
summary for the publication runtime.
"""

from __future__ import annotations

import json
import subprocess
import sys
import re
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping


DIMENSIONS = (
    "DIM-01.route",
    "DIM-02.taxonomy",
    "DIM-03.business-answer",
    "DIM-04.page-type",
    "DIM-05.reader-audit",
)
DIMENSION_LABELS = {
    "DIM-01.route": "route",
    "DIM-02.taxonomy": "taxonomy",
    "DIM-03.business-answer": "business-answer",
    "DIM-04.page-type": "page-type",
    "DIM-05.reader-audit": "Reader-Audit",
}
EXPECTED_PROJECTION_IDS = (
    "Q-POS-01.positioning",
    "Q-CON-01.concept",
    "Q-OPR-01.qr.operation",
    "Q-OPR-01.zero-touch.operation",
    "Q-DIA-01.diagnosis.metric",
    "Q-DIA-01.diagnosis.migration",
    "Q-DIA-01.diagnosis.query",
    "Q-DIA-01.diagnosis.delete",
    "Q-DIA-01.diagnosis.doc",
    "Q-EXP-01.experience",
    "Q-BND-01.operation",
    "Q-BND-01.diagnosis",
)
SELF_REFERENTIAL_BUNDLE_FILES = frozenset({"_audit/directory-manifest.json", "_audit/run-result.json"})


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def _sha(value: bytes) -> str:
    return sha256(value).hexdigest()


def _tree_digest(root: Path) -> str:
    rows: list[bytes] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and not item.is_symlink()):
        relative = path.relative_to(root).as_posix()
        # The publication manifest and run result contain the tree identity
        # and are finalized after the candidate is evaluated.  Keep this
        # identity aligned with task5_runtime._manifest(), which excludes
        # those two self-referential records.
        if relative in SELF_REFERENTIAL_BUNDLE_FILES:
            continue
        rows.append(relative.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return _sha(b"".join(rows))


def _observation_digest(value: Any) -> str:
    return _sha(_canonical(value))


def _judge_rounds(value: Mapping[str, Any], projection_id: str, dimension: str) -> tuple[str, ...]:
    """Return the two independent judge decisions without accepting a static verdict."""

    rounds = value.get("judgements")
    if not isinstance(rounds, list) or len(rounds) != 2:
        return ()
    decisions: list[str] = []
    source_dimension = DIMENSION_LABELS[dimension]
    for round_items in rounds:
        if not isinstance(round_items, list):
            return ()
        judgement = next(
            (item for item in round_items if isinstance(item, Mapping) and item.get("projection_id") == projection_id),
            None,
        )
        dimensions = judgement.get("dimensions") if isinstance(judgement, Mapping) else None
        item = dimensions.get(source_dimension) if isinstance(dimensions, Mapping) else None
        verdict = item.get("verdict") if isinstance(item, Mapping) else None
        reason = str(item.get("reason", "")).strip() if isinstance(item, Mapping) else ""
        if verdict not in {"KD_WIN", "CB_WIN", "TIE", "UNKNOWN"} or len(reason) < 8:
            return ()
        decisions.append(str(verdict))
    return tuple(decisions)


def _basis_for_win(projection: Mapping[str, Any], dimension: str, decisions: tuple[str, ...]) -> dict[str, Any] | None:
    # A judge result is not a CompanyBrain observation.  The old code created
    # a synthetic basis here, which let a judge-only result claim a strict win
    # even when no frozen gap/atom mapping existed.  Only an independently
    # produced, source-bound basis may be promoted by this gate.
    basis = projection.get("advantage_basis")
    if not isinstance(basis, Mapping):
        per_dimension = projection.get("advantage_basis_by_dimension")
        basis = per_dimension.get(DIMENSION_LABELS[dimension]) if isinstance(per_dimension, Mapping) else None
    if not isinstance(basis, Mapping):
        return None
    structural = projection.get("structural_observation")
    observation = structural.get(DIMENSION_LABELS[dimension]) if isinstance(structural, Mapping) else None
    if not isinstance(observation, Mapping) or observation.get("passed") is not True:
        return None
    result = dict(basis)
    result["judge_decisions"] = list(decisions)
    return result


def _public_result(value: Mapping[str, Any]) -> dict[str, Any]:
    """Remove host paths and judge payloads from the machine summary."""

    projections = value.get("projections", [])
    public_projections = [
        dict(item)
        for item in projections
        if isinstance(item, Mapping)
    ]
    raw_dimension_verdicts = value.get("dimension_verdicts", {})
    dimension_verdicts = {}
    if isinstance(raw_dimension_verdicts, Mapping):
        for projection_id in EXPECTED_PROJECTION_IDS:
            raw_values = raw_dimension_verdicts.get(projection_id, {})
            dimension_verdicts[projection_id] = {
                dimension: raw_values.get(DIMENSION_LABELS[dimension], ["UNKNOWN", "UNKNOWN"])
                if isinstance(raw_values, Mapping) else ["UNKNOWN", "UNKNOWN"]
                for dimension in DIMENSIONS
            }
    rows: list[dict[str, Any]] = []
    projection_by_id = {str(item.get("projection_id", "")): item for item in public_projections}
    for projection_id in EXPECTED_PROJECTION_IDS:
        projection = projection_by_id.get(projection_id, {})
        for dimension in DIMENSIONS:
            decisions = _judge_rounds(value, projection_id, dimension)
            basis = _basis_for_win(projection, dimension, decisions) if decisions == ("KD_WIN", "KD_WIN") else None
            structural = projection.get("structural_observation", {}) if isinstance(projection, Mapping) else {}
            reader_observation = structural.get(DIMENSION_LABELS[dimension], {}) if isinstance(structural, Mapping) else {}
            cb_observation = {
                "projection_id": projection_id,
                "dimension_id": dimension,
                "companybrain_page_paths": projection.get("companybrain_page_paths", []),
                "baseline_checks": projection.get("companybrain_baseline_checks", []),
            }
            rows.append({
                "projection_key": projection_id,
                "dimension_id": dimension,
                "verdict": "KD_WIN" if basis is not None else "UNKNOWN",
                "kd_observation_ref": f"reader:{projection_id}:{dimension}" if basis is not None else None,
                "cb_observation_ref": f"companybrain:{projection_id}:{dimension}" if basis is not None else None,
                "observation_digests": {"reader": str(basis.get("kd_completion_digest")), "companybrain": str(basis.get("cb_observation_digest"))} if basis is not None else {},
                "advantage_basis": basis,
            })
    result: dict[str, Any] = {
        "schema_version": "task5-quality-result.v3",
        "projection_count": int(value.get("projection_count", 0)),
        "verdict": str(value.get("verdict", "UNKNOWN")),
        "hard_blockers": [str(item) for item in value.get("hard_blockers", [])],
        "judge_errors": [str(item) for item in value.get("judge_errors", [])],
        "dimension_verdicts": dimension_verdicts,
        "source_count_in_audit": int(value.get("source_count_in_audit", 0)),
        "source_count_on_disk": int(value.get("source_count_on_disk", 0)),
        "candidate_reader_file_count": int(value.get("candidate_reader_file_count", 0)),
        "run_outcome": str(value.get("run_outcome", "UNKNOWN")),
        "projections": public_projections,
        "quality_rows": rows,
        "quality_result_status": "candidate",
        "candidate_tree_sha256": "",
        "published_tree_sha256": None,
        "input_identity": {},
    }
    return result


def evaluate_candidate(
    *,
    candidate: Path,
    raw: Path,
    companybrain: Path,
    cases: Path,
    baseline: Path,
    config: Path,
    output: Path,
    judge: bool = True,
    ledger_root: Path | None = None,
    source_manifest: Path | None = None,
) -> dict[str, Any]:
    """Recompute the five dimensions from the actual files."""

    if output.exists():
        raise RuntimeError("quality result output already exists; use a new attempt path")
    script = Path(__file__).resolve().parents[2] / "scripts" / "evaluate_reader_candidate.py"
    command = [
        sys.executable,
        str(script),
        "--candidate",
        str(Path(candidate).resolve()),
        "--raw",
        str(Path(raw).resolve()),
        "--companybrain",
        str(Path(companybrain).resolve()),
        "--cases",
        str(Path(cases).resolve()),
        "--baseline",
        str(Path(baseline).resolve()),
        *(('--ledger-root', str(Path(ledger_root).resolve())) if ledger_root is not None else ()),
        *(('--source-manifest', str(Path(source_manifest).resolve())) if source_manifest is not None else ()),
        "--output",
        str(Path(output).resolve()),
    ]
    if judge:
        command.extend(("--config", str(Path(config).resolve()), "--judge"))
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if not output.is_file():
        raise RuntimeError("quality evaluator did not produce a result")
    try:
        raw_result = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("quality evaluator produced malformed JSON") from error
    if not isinstance(raw_result, Mapping):
        raise RuntimeError("quality evaluator result is not an object")
    result = _public_result(raw_result)
    result["input_identity"] = {
        "candidate_tree_sha256": _tree_digest(Path(candidate)),
        "raw_tree_sha256": _tree_digest(Path(raw)),
        "companybrain_tree_sha256": _tree_digest(Path(companybrain)),
        "cases_sha256": _sha(cases.read_bytes()),
        "baseline_sha256": _sha(baseline.read_bytes()),
        "provider_config_sha256": _sha(config.read_bytes()),
    }
    result["candidate_tree_sha256"] = result["input_identity"]["candidate_tree_sha256"]
    result["command_exit_code"] = int(completed.returncode)
    result["stdout_sha256"] = _sha(completed.stdout.encode("utf-8"))
    result["stderr_sha256"] = _sha(completed.stderr.encode("utf-8"))
    result["quality_result_sha256"] = _sha(_canonical(result))
    result["canonical_sha256"] = _sha(_canonical(result))
    output.write_bytes(_canonical(result))
    return result


def strict_winner(result: Mapping[str, Any]) -> bool:
    if result.get("schema_version") != "task5-quality-result.v3":
        return False
    if result.get("quality_result_status") != "released":
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", str(result.get("candidate_tree_sha256", ""))) or result.get("published_tree_sha256") != result.get("candidate_tree_sha256"):
        return False
    rows = result.get("quality_rows")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_PROJECTION_IDS) * len(DIMENSIONS):
        return False
    expected_pairs = {(projection_id, dimension) for projection_id in EXPECTED_PROJECTION_IDS for dimension in DIMENSIONS}
    actual_pairs: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            return False
        projection_id = str(row.get("projection_key", ""))
        dimension = str(row.get("dimension_id", ""))
        if (projection_id, dimension) not in expected_pairs or (projection_id, dimension) in actual_pairs:
            return False
        actual_pairs.add((projection_id, dimension))
        if row.get("verdict") != "KD_WIN" or not row.get("kd_observation_ref") or not row.get("cb_observation_ref"):
            return False
        digests = row.get("observation_digests")
        if not isinstance(digests, Mapping) or set(digests) != {"reader", "companybrain"} or any(not re.fullmatch(r"[0-9a-f]{64}", str(value)) for value in digests.values()):
            return False
        basis = row.get("advantage_basis")
        if not isinstance(basis, Mapping):
            return False
        required_basis = {"projection_key", "dimension_id", "cb_observation_ref", "cb_observation_digest", "cb_gap_type", "cb_gap_locator", "atom_observations", "gap_atom_refs", "stage_observations", "gap_stage_refs", "quality_feature_observations", "gap_quality_feature_refs", "strict_improvement_refs", "non_regression", "kd_completion_refs", "kd_completion_surfaces", "kd_completion_digest"}
        if not required_basis.issubset(basis) or basis.get("projection_key") != projection_id or basis.get("dimension_id") != dimension:
            return False
        # A strict win is only admissible when the public row carries the two
        # normalized blind-judge decisions.  A hand-built/static basis is not
        # a substitute for the actual comparison calls.
        if basis.get("judge_decisions") != ["KD_WIN", "KD_WIN"]:
            return False
        allowed_gap_types = {
            "DIM-01.route": {"unreachable", "wrong_relation"},
            "DIM-02.taxonomy": {"missing_taxonomy_axis", "wrong_relation"},
            "DIM-03.business-answer": {"missing_stage", "unsupported_answer_claim", "wrong_relation"},
            "DIM-04.page-type": {"untyped_contract", "wrong_page_type"},
            "DIM-05.reader-audit": {"missing_provenance", "untraceable_claim"},
        }
        if not basis.get("strict_improvement_refs") or basis.get("non_regression") is not True or basis.get("cb_gap_type") not in allowed_gap_types[dimension] or not basis.get("cb_gap_locator"):
            return False
        if basis.get("cb_observation_digest") != digests.get("companybrain") or basis.get("kd_completion_digest") != digests.get("reader") or not re.fullmatch(r"[0-9a-f]{64}", str(basis.get("kd_completion_digest", ""))):
            return False
        if not isinstance(basis.get("kd_completion_surfaces"), list) or set(basis["kd_completion_surfaces"]) != {"Reader", "Audit"}:
            return False
        atoms = basis.get("atom_observations")
        if not isinstance(atoms, list) or not atoms:
            return False
        atom_ids = set()
        gap_atom_refs = basis.get("gap_atom_refs")
        gap_stage_refs = basis.get("gap_stage_refs")
        gap_feature_refs = basis.get("gap_quality_feature_refs")
        if not isinstance(gap_atom_refs, list) or not isinstance(gap_stage_refs, list) or not isinstance(gap_feature_refs, list) or not (gap_atom_refs or gap_stage_refs or gap_feature_refs):
            return False
        for atom in atoms:
            if not isinstance(atom, Mapping) or set(atom) != {"atom_id", "applicable", "cb_status", "kd_status", "cb_evidence_refs", "kd_evidence_refs", "relation"}:
                return False
            atom_id = str(atom["atom_id"])
            if not atom_id or atom_id in atom_ids or atom.get("applicable") is not True:
                return False
            atom_ids.add(atom_id)
            if atom.get("cb_status") not in {"present", "absent", "unknown", "forbidden"} or atom.get("kd_status") not in {"present", "absent", "unknown", "forbidden"}:
                return False
            if atom.get("cb_status") in {"unknown", "forbidden"} or atom.get("kd_status") in {"unknown", "forbidden"}:
                return False
            if atom.get("relation") not in {"strict_improvement", "non_regression", "tie", "regression", "unknown"}:
                return False
        if not set(str(item) for item in gap_atom_refs).issubset(atom_ids):
            return False
        gap_atoms = [atom for atom in atoms if str(atom.get("atom_id")) in {str(item) for item in gap_atom_refs}]
        if any(atom.get("cb_status") != "absent" for atom in gap_atoms):
            return False
        strict_atoms = [atom for atom in atoms if atom.get("relation") == "strict_improvement" and atom.get("cb_status") == "absent" and atom.get("kd_status") == "present"]
        if not strict_atoms and not basis.get("gap_stage_refs") and not basis.get("gap_quality_feature_refs"):
            return False
        if any(not isinstance(refs, list) for refs in (basis.get("cb_evidence_refs", []), basis.get("kd_evidence_refs", []))):
            return False
        for stage in basis.get("stage_observations", []):
            if not isinstance(stage, Mapping) or not {"stage_id", "applicable", "cb_status", "kd_status", "cb_evidence_refs", "kd_evidence_refs", "relation"}.issubset(stage):
                return False
        for feature in basis.get("quality_feature_observations", []):
            if not isinstance(feature, Mapping) or not {"feature_id", "applicable", "blocking", "cb_score", "kd_score", "cb_status", "kd_status", "cb_evidence_refs", "kd_evidence_refs", "relation"}.issubset(feature):
                return False
            if feature.get("cb_score") is not None or feature.get("kd_score") is not None:
                return False
    if actual_pairs != expected_pairs:
        return False
    dimensions = result.get("dimension_verdicts")
    if not isinstance(dimensions, Mapping) or set(str(key) for key in dimensions) != set(EXPECTED_PROJECTION_IDS):
        return False
    for values in dimensions.values():
        if not isinstance(values, Mapping):
            return False
        for dimension in DIMENSIONS:
            verdicts = values.get(dimension)
            if verdicts != ["KD_WIN", "KD_WIN"]:
                return False
    return str(result.get("verdict")) == "released" and not result.get("hard_blockers") and not result.get("judge_errors")


__all__ = ["DIMENSIONS", "evaluate_candidate", "strict_winner"]
