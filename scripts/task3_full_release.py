"""Thin Task3 execution order and raw Reader candidate handoff.

This module only coordinates already-owned seams.  It does not compile pages,
score quality, decide comparison values, or invent a second release state.
The ``--raw-input`` adapter delegates compilation to ``reader_compiler`` and
returns a candidate; it does not bypass the existing release confirmation.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


TASK3_SEQUENCE = (
    "freeze",
    "candidate",
    "quality",
    "comparison",
    "summary",
    "confirmation",
    "readback",
)

_STEP_SUCCESS = {
    "freeze": {"passed"},
    "candidate": {"passed"},
    "quality": {"passed"},
    "comparison": {"passed"},
    "summary": {"passed"},
    "confirmation": {"confirmed"},
    "readback": {"released", "not_released"},
}


def _write_handoff(output_dir: Path, handoff: Mapping[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "closeout-handoff.json"
    temporary = output_dir / f".{target.name}.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(handoff, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def _downgrade_replay_statuses(value: Any) -> Any:
    """Remove captured release authority from nested replay evidence."""

    if isinstance(value, Mapping):
        return {
            key: "not_released" if key in {"status", "digest_release_status", "release_status"} and item == "released" else _downgrade_replay_statuses(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_downgrade_replay_statuses(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_downgrade_replay_statuses(item) for item in value)
    return value


def build_closeout_handoff(
    *,
    status: str,
    actual_result: Mapping[str, Any],
    risk_items: list[Mapping[str, Any]],
    deferred_items: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Create the narrow handoff consumed by Task 3-Closeout."""
    if status not in {"released", "not_released"}:
        raise ValueError(f"unsupported Task3 status: {status}")
    return {
        "schema_version": "kd-task3-closeout-handoff.v1",
        "status": status,
        "actual_result": dict(actual_result),
        "risk_items": [dict(item) for item in risk_items],
        "deferred_items": [dict(item) for item in deferred_items],
        "closeout_scope": ["document_sync", "archive", "cleanup", "recovery_rehearsal"],
        "closeout_must_not": ["new_pages", "new_topics", "new_quality_gates", "status_rewrite"],
    }


def run_task3_full_release(
    *,
    steps: Mapping[str, Callable[[], Mapping[str, Any]]],
    output_dir: Path | None = None,
    risk_items: list[Mapping[str, Any]] | None = None,
    deferred_items: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the frozen sequence and hand off the observed final status.

    Each callable belongs to an existing module or an evidence-producing
    adapter supplied by the caller.  Missing steps fail loudly.  A failed or
    undecidable intermediate result cannot be upgraded by this coordinator;
    the final status comes from the readback seam and falls back to
    ``not_released`` when it is not a valid release state.
    """
    missing = [name for name in TASK3_SEQUENCE if name not in steps]
    if missing:
        raise ValueError(f"missing Task3 steps: {', '.join(missing)}")

    observed: dict[str, dict[str, Any]] = {}
    sequence: list[str] = []
    stopped_at: str | None = None
    for index, name in enumerate(TASK3_SEQUENCE):
        value = steps[name]()
        if not isinstance(value, Mapping):
            raise TypeError(f"Task3 step {name} must return a mapping")
        observed[name] = dict(value)
        sequence.append(name)
        if observed[name].get("status") not in _STEP_SUCCESS[name]:
            stopped_at = name
            for remaining in TASK3_SEQUENCE[index + 1:]:
                observed[remaining] = {"status": "not_run", "reason": f"stopped after {name} returned an invalid or failed status"}
            break

    readback_status = observed.get("readback", {}).get("status")
    status = readback_status if readback_status in {"released", "not_released"} else "not_released"
    if stopped_at is not None or any(observed[name].get("status") in {"failed", "error", "unknown"} for name in observed):
        status = "not_released"

    run_result = {
        "schema_version": "kd-task3-full-release-run.v1",
        "sequence": sequence,
        "steps": observed,
        "status": status,
        "stopped_at": stopped_at,
    }
    handoff = build_closeout_handoff(
        status=status,
        actual_result=run_result,
        risk_items=list(risk_items or []),
        deferred_items=list(deferred_items or []),
    )
    result = {**run_result, "handoff": handoff}
    if output_dir is not None:
        _write_handoff(output_dir, handoff)
    return result


def run_task3_full_release_from_json(
    steps_path: Path,
    *,
    output_dir: Path | None = None,
    risk_items: list[Mapping[str, Any]] | None = None,
    deferred_items: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the thin entrypoint from captured adapter facts."""

    value = json.loads(Path(steps_path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping) or not isinstance(value.get("steps"), Mapping):
        raise ValueError("steps JSON must contain an object under steps")
    captured = {str(key): dict(item) for key, item in value["steps"].items() if isinstance(item, Mapping)}
    captured = {name: _downgrade_replay_statuses(item) for name, item in captured.items()}
    # A captured released readback is never live authority.  Normalize it
    # before the coordinator builds either the run result or the on-disk
    # handoff, so no intermediate write can expose a false released state.
    readback = captured.get("readback")
    if isinstance(readback, Mapping) and readback.get("status") == "released":
        captured["readback"] = {
            **dict(readback),
            "status": "not_released",
            "reason": "captured JSON replay cannot authorize live release",
        }
    result = run_task3_full_release(
        steps={name: (lambda name=name: captured[name]) for name in TASK3_SEQUENCE if name in captured},
        output_dir=output_dir,
        risk_items=risk_items,
        deferred_items=deferred_items,
    )
    return result


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--steps-json", type=Path)
    mode.add_argument("--raw-input", type=Path, help="compile a reader-first candidate from raw source files")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--semantic-candidate", type=Path)
    parser.add_argument("--risk-items-json", type=Path)
    parser.add_argument("--deferred-items-json", type=Path)
    args = parser.parse_args()

    if args.raw_input is not None:
        from knowledge_digest.reader_compiler import compile_reader_bundle

        result = compile_reader_bundle(args.raw_input, args.output, semantic_candidate=args.semantic_candidate)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        # Candidate generation is a successful execution even though the
        # existing Task3 release boundary correctly remains not_released.
        return 0 if result["quality"]["status"] == "passed" else 1

    def load_items(path: Path | None) -> list[Mapping[str, Any]]:
        if path is None:
            return []
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, list) or any(not isinstance(item, Mapping) for item in value):
            raise ValueError(f"{path} must contain a JSON array of objects")
        return [dict(item) for item in value]

    result = run_task3_full_release_from_json(
        args.steps_json,
        output_dir=args.output,
        risk_items=load_items(args.risk_items_json),
        deferred_items=load_items(args.deferred_items_json),
    )
    return 0 if result["status"] == "released" else 1


if __name__ == "__main__":
    raise SystemExit(main())
