#!/usr/bin/env python3
"""Isolated real-service acceptance for Phase 4 embedding calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Sequence

from knowledge_digest.calibration_cli import main as calibration_main
from knowledge_digest.calibration import (
    coverage_audit,
    feature_separation,
    strict_lineage_split,
)
from knowledge_digest.config import DigestSettings, EmbeddingSettings, resolve_settings
from knowledge_digest.corpus_isolation import (
    cleanup_disposable_corpus,
    prepare_disposable_corpus,
    tree_manifest,
)
from knowledge_digest.embedding import (
    EmbeddingError,
    OpenAIEmbeddingClient,
    normalize_endpoint_identity,
)
from knowledge_digest.provider_config import configured_provider_config_path, effective_embedding_provider
from knowledge_digest.text_similarity import _similarity, _tokens
from knowledge_digest.gold import canonical_json_bytes, load_confirmed_gold


RESULT_NAME = "real-service-acceptance.json"
ARTIFACT_NAME = "calibration-artifact.json"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_json(path: Path, value: object) -> None:
    payload = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(payload)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _overlaps(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
        return True
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return True
    except ValueError:
        return False


def validate_paths(
    corpus: Path,
    kb: Path,
    temp_root: Path,
    evidence_dir: Path,
    config: Path,
) -> tuple[Path, Path, Path, Path, Path]:
    """Resolve five caller-selected paths and reject every overlap."""
    supplied = (corpus, kb, temp_root, evidence_dir, config)
    if any(not path.is_absolute() for path in supplied):
        raise ValueError("corpus, kb, temp, evidence, and config paths must be absolute")
    resolved = tuple(path.resolve(strict=True) for path in supplied)
    corpus_path, kb_path, temp_path, evidence_path, config_path = resolved
    for path, label in (
        (corpus_path, "corpus"),
        (kb_path, "kb"),
        (temp_path, "temp"),
        (evidence_path, "evidence"),
    ):
        if not path.is_dir():
            raise ValueError(f"{label} path must be a directory")
    if not config_path.is_file():
        raise ValueError("config path must be a regular file")
    for index, left in enumerate(resolved):
        for right in resolved[index + 1 :]:
            if _overlaps(left, right):
                raise ValueError("corpus, kb, temp, evidence, and config paths must be distinct")
    return resolved


def _embedding_settings(
    config: Path, *, provider_config_path: Path | None = None
) -> tuple[EmbeddingSettings, DigestSettings]:
    settings = resolve_settings(
        config,
        top_k=None,
        high=None,
        medium=None,
        max_lines=None,
        provider_config_path=provider_config_path,
    )
    if settings.similarity.backend != "jaccard":
        raise ValueError(
            "acceptance requires explicit similarity.backend=jaccard; it never enables embedding"
        )
    embedding = settings.similarity.embedding
    if embedding is None:
        raise ValueError("similarity.embedding connection settings are required")
    provider = effective_embedding_provider(
        provider_config_path=settings.provider_config_path,
        base_url=embedding.base_url,
        model=embedding.model,
        expected_dimension=embedding.expected_dimension,
        api_key_env=embedding.api_key_env,
    )
    return replace(
        embedding,
        base_url=provider["base_url"],
        model=provider["model"],
        expected_dimension=provider["expected_dimension"],
    ), settings


def real_probe(
    settings: EmbeddingSettings, env: dict[str, str]
) -> dict[str, Any]:
    """Make the approved endpoint request used as the service identity probe."""
    client = OpenAIEmbeddingClient(
        settings,
        api_key=env.get(settings.api_key_env),
    )
    return {
        "endpoint_identity": client.endpoint_identity,
        "model": client.model,
        "dimension": client.dimension,
        "probe_fingerprint": client.probe_fingerprint(),
    }


def _default_calibrate(
    *,
    cases: Path | None,
    evidence_dir: Path,
    service_identity: dict[str, Any],
    corpus_hash: str,
    config: Path,
    disposable_corpus: Path,
    formal_kb: Path,
    embedding_settings: EmbeddingSettings,
    digest_settings: DigestSettings,
    env: dict[str, str],
) -> dict[str, Any]:
    if cases is None:
        return {
            "result": "BLOCKED",
            "reason_code": "confirmed_scored_cases_missing",
        }
    if not cases.is_absolute() or not cases.is_file():
        raise ValueError("cases path must be an existing absolute file")
    raw = load_confirmed_gold(cases)
    scored_path = disposable_corpus.parent / "scored-cases.json"
    artifact = evidence_dir / ARTIFACT_NAME
    split_audit = evidence_dir / "split-coverage-audit.json"
    vector_manifest_path = evidence_dir / "vector-manifest.json"
    replay_path = evidence_dir / ".replay-artifact.json"
    replay_audit = evidence_dir / ".replay-split-audit.json"
    completed = False
    try:
        scored_rows, gold_hash, vectors_hash, vector_manifest = _score_real_cases(
            raw,
            disposable_corpus=disposable_corpus,
            kb_root=formal_kb,
            settings=embedding_settings,
            digest_settings=digest_settings,
            env=env,
        )
        _write_json(scored_path, {"cases": scored_rows})
        _write_json(vector_manifest_path, vector_manifest)
        persisted_vectors_hash = _sha256_bytes(
            json.dumps(
                json.loads(vector_manifest_path.read_text(encoding="utf-8")),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        if persisted_vectors_hash != vectors_hash:
            raise RuntimeError("persisted vector manifest hash mismatch")
        common = [
            "calibrate", "--cases", str(scored_path), "--confirmed-gold", str(cases),
            "--endpoint-identity", str(service_identity["endpoint_identity"]),
            "--model", str(service_identity["model"]), "--dimension", str(service_identity["dimension"]),
            "--probe-fingerprint", str(service_identity["probe_fingerprint"]),
            "--corpus-hash", corpus_hash, "--gold-hash", gold_hash,
            "--vectors-hash", vectors_hash,
        ]
        exit_code = calibration_main(
            common + ["--output", str(artifact), "--split-audit", str(split_audit), "--config", str(config)]
        )
        if exit_code != 0 or not artifact.is_file():
            raise RuntimeError("calibration command failed")
        artifact_value = json.loads(artifact.read_text(encoding="utf-8"))
        replay_exit = calibration_main(
            common + ["--output", str(replay_path), "--split-audit", str(replay_audit)]
        )
        replay_match = (
            replay_exit == 0
            and replay_path.is_file()
            and replay_audit.is_file()
            and replay_path.read_bytes() == artifact.read_bytes()
            and replay_audit.read_bytes() == split_audit.read_bytes()
            and persisted_vectors_hash == artifact_value["vectors_hash"]
        )
        if not replay_match:
            return {"result": "BLOCKED", "reason_code": "replay_mismatch", "replay_match": False}
        completed = True
        return {
            "result": artifact_value["adoption_status"],
            "artifact": artifact_value,
            "artifact_path": str(artifact),
            "replay_match": True,
        }
    finally:
        if not completed:
            artifact.unlink(missing_ok=True)
            split_audit.unlink(missing_ok=True)
            vector_manifest_path.unlink(missing_ok=True)
        replay_path.unlink(missing_ok=True)
        replay_audit.unlink(missing_ok=True)
        scored_path.unlink(missing_ok=True)


def _safe_read(root: Path, relative: object) -> str:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("case references must be non-empty relative paths")
    path = (root / relative).resolve(strict=True)
    try:
        path.relative_to(root.resolve(strict=True))
    except ValueError as error:
        raise ValueError("case reference escapes its approved root") from error
    if not path.is_file() or path.suffix.lower() != ".md":
        raise ValueError("case reference must select one Markdown file")
    return path.read_text(encoding="utf-8")


def _cosine(left: list[float], right: list[float]) -> float:
    left_norm = sum(item * item for item in left) ** 0.5
    right_norm = sum(item * item for item in right) ** 0.5
    if left_norm == 0 or right_norm == 0:
        raise ValueError("zero vector cannot be scored")
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)


def _validate_identity_bindings(bindings: list[dict[str, Any]]) -> None:
    source_lineages: dict[tuple[str, str], str] = {}
    query_bindings: dict[str, tuple[tuple[str, str], str, object]] = {}
    for binding in bindings:
        source = (binding["left_ref"], binding["left_hash"])
        lineage = binding["lineage_id"]
        query_id = binding["query_id"]
        action = binding["gold_action"]
        if source_lineages.setdefault(source, lineage) != lineage:
            raise ValueError("one source identity must use exactly one lineage_id")
        expected = (source, lineage, action)
        if query_bindings.setdefault(query_id, expected) != expected:
            raise ValueError(
                "one query_id must bind exactly one source, lineage_id, and gold_action"
            )


def _score_real_cases(
    raw: dict[str, Any],
    *,
    disposable_corpus: Path,
    kb_root: Path | None,
    settings: EmbeddingSettings,
    digest_settings: DigestSettings,
    env: dict[str, str],
) -> tuple[list[dict[str, Any]], str, str, list[dict[str, str]]]:
    """Derive every score/outcome from approved files and the real service."""
    rows = raw["cases"]
    allowed = {
        "case_id", "lineage_id", "content_identity", "label_version", "stage",
        "label", "stratum", "confirmed", "gold_action", "left_ref", "right_ref",
        "right_root", "query_id",
    }
    material: list[tuple[dict[str, Any], str, str]] = []
    identity_bindings: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) - allowed or "scores" in row or "outcomes" in row:
            raise ValueError("formal cases must be unscored confirmed-gold references")
        if row.get("confirmed") is not True:
            raise ValueError("formal cases must be individually confirmed")
        expected_root = "corpus" if row.get("stage") == "S2" else "kb"
        if row.get("right_root") != expected_root:
            raise ValueError(f"{row.get('stage')} formal cases require right_root={expected_root}")
        right_root = disposable_corpus if row.get("right_root", "corpus") == "corpus" else kb_root
        if right_root is None:
            raise ValueError("S3 KB references require an explicit kb_root")
        left = _safe_read(disposable_corpus, row.get("left_ref"))
        right = _safe_read(right_root, row.get("right_ref"))
        identity = hashlib.sha256((left + "\0" + right).encode("utf-8")).hexdigest()
        if row.get("content_identity") != identity:
            raise ValueError("confirmed gold content_identity does not match isolated files")
        identity_bindings.append(
            {
                "left_ref": row["left_ref"],
                "left_hash": _sha256_bytes(left.encode("utf-8")),
                "lineage_id": row["lineage_id"],
                "query_id": row["query_id"],
                "gold_action": row.get("gold_action"),
            }
        )
        base = {key: value for key, value in row.items() if key not in {"left_ref", "right_ref", "right_root"}}
        base["gold_case_hash"] = hashlib.sha256(canonical_json_bytes(row)).hexdigest()
        material.append((base, left, right))
    _validate_identity_bindings(identity_bindings)
    client = OpenAIEmbeddingClient(settings, api_key=env.get(settings.api_key_env))
    corpus_candidates = [
        (path.relative_to(disposable_corpus).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(disposable_corpus.rglob("*.md"))
        if path.is_file()
    ]
    kb_candidates = [
        (path.relative_to(kb_root).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(kb_root.rglob("*.md"))
        if path.is_file()
    ] if kb_root is not None else []
    unique_texts = list(dict.fromkeys(
        [text for _, left, right in material for text in (left, right)]
        + [text for _, text in corpus_candidates]
        + [text for _, text in kb_candidates]
    ))
    vectors = client.embed(unique_texts)
    by_text = dict(zip(unique_texts, vectors, strict=True))
    vector_manifest = [
        {
            "root": root,
            "path_hash": _sha256_bytes(relative.encode("utf-8")),
            "input_hash": _sha256_bytes(text.encode("utf-8")),
            "vector_hash": _sha256_bytes(
                json.dumps(by_text[text], separators=(",", ":")).encode("utf-8")
            ),
        }
        for root, candidates in (("corpus", corpus_candidates), ("kb", kb_candidates))
        for relative, text in candidates
    ]
    vector_manifest_hash = _sha256_bytes(
        json.dumps(vector_manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    provisional = []
    material_by_case: dict[str, tuple[str, str]] = {}
    for base, left, right in material:
        material_by_case[base["case_id"]] = (left, right)
        vector_hashes = {
            side: _sha256_bytes(
                json.dumps(by_text[text], separators=(",", ":")).encode("utf-8")
            )
            for side, text in (("left", left), ("right", right))
        }
        provisional.append({
            **base,
            "vector_hashes": vector_hashes,
            "vector_manifest_hash": vector_manifest_hash,
            "scores": {
                "jaccard": _similarity(left, right),
                "embedding": _cosine(by_text[left], by_text[right]),
            },
            "outcomes": {"jaccard": {}, "embedding": {}},
        })
    split_rows = strict_lineage_split(provisional)
    gold_binding = [
        case["gold_case_hash"]
        for case in sorted(split_rows, key=lambda item: item["case_id"])
    ]
    computed_gold_hash = _sha256_bytes(
        json.dumps(gold_binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    if raw.get("gold_hash") != computed_gold_hash:
        raise ValueError("confirmed gold hash mismatch")
    if coverage_audit(split_rows)["undecidable_cells"]:
        return split_rows, computed_gold_hash, vector_manifest_hash, vector_manifest
    separation = feature_separation(split_rows, "calibration")
    thresholds = {
        "jaccard": {
            "S2": digest_settings.medium,
            "S3": digest_settings.page_match_threshold,
        },
        "embedding": {
            "S2": min(
                separation["S2"]["embedding"]["positive"]["quantiles"]["p50"],
                (
                    separation["S2"]["embedding"]["positive"]["min"]
                    + separation["S2"]["embedding"]["negative"]["max"]
                ) / 2,
            ),
            "S3": (
                separation["S3"]["embedding"]["positive"]["min"]
                + separation["S3"]["embedding"]["negative"]["max"]
            ) / 2,
        },
    }
    split_by_query: dict[str, str] = {}
    split_by_source: dict[tuple[str, str], str] = {}
    binding_by_case = {
        row["case_id"]: binding for row, binding in zip(rows, identity_bindings, strict=True)
    }
    for row in split_rows:
        binding = binding_by_case[row["case_id"]]
        source = (binding["left_ref"], binding["left_hash"])
        if split_by_query.setdefault(binding["query_id"], row["split"]) != row["split"]:
            raise ValueError("one query_id cannot cross calibration and holdout")
        if split_by_source.setdefault(source, row["split"]) != row["split"]:
            raise ValueError("one source identity cannot cross calibration and holdout")

    def cluster_outcomes(backend: str) -> tuple[dict[str, int], dict[str, str]]:
        pending = list(corpus_candidates)
        memberships: dict[str, int] = {}
        tiers: dict[str, str] = {}
        cluster_id = 0
        while pending:
            seed_path, seed_text = pending.pop(0)
            members = [(seed_path, seed_text)]
            for candidate in list(pending):
                scores = [
                    _similarity(candidate[1], member[1])
                    if backend == "jaccard"
                    else _cosine(by_text[candidate[1]], by_text[member[1]])
                    for member in members
                ]
                if scores and min(scores) >= thresholds[backend]["S2"]:
                    members.append(candidate)
                    pending.remove(candidate)
            pair_scores = [
                _similarity(left[1], right[1])
                if backend == "jaccard"
                else _cosine(by_text[left[1]], by_text[right[1]])
                for index, left in enumerate(members)
                for right in members[index + 1 :]
            ]
            min_pair = min(pair_scores) if pair_scores else 1.0
            token_count = len(_tokens("\n".join(text for _, text in members)))
            for path, _ in members:
                memberships[path] = cluster_id
                tiers[path] = (
                    "insufficient_signal"
                    if token_count < 3
                    else "auto"
                    if min_pair >= (
                        digest_settings.high
                        if backend == "jaccard"
                        else separation["S2"]["embedding"]["positive"]["quantiles"]["p50"]
                    )
                    else "needs_review"
                    if min_pair >= thresholds[backend]["S2"]
                    else "insufficient_signal"
                )
            cluster_id += 1
        return memberships, tiers

    cluster_results = {
        backend: cluster_outcomes(backend) for backend in ("jaccard", "embedding")
    }
    original_by_id = {row["case_id"]: row for row in rows}
    query_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in split_rows:
        original = original_by_id[row["case_id"]]
        for backend in ("jaccard", "embedding"):
            predicted = row["scores"][backend] >= thresholds[backend][row["stage"]]
            if row["stage"] == "S2":
                original = original_by_id[row["case_id"]]
                predicted = (
                    cluster_results[backend][0][original["left_ref"]]
                    == cluster_results[backend][0][original["right_ref"]]
                )
            if row["stage"] == "S3":
                query_id = original.get("query_id")
                if not isinstance(query_id, str) or not query_id:
                    raise ValueError("S3 formal cases require query_id")
                query_groups.setdefault((row["split"], query_id, backend), []).append(row)
                predicted = False  # assigned after deterministic top-k ranking
            actual = row["label"] == "positive"
            row["outcomes"][backend] = {
                "predicted_positive": predicted,
                "correct": predicted == actual,
                "error": predicted != actual,
            }
            if row["stage"] == "S2":
                row["outcomes"][backend]["predicted_tier"] = cluster_results[backend][1][
                    original["left_ref"]
                ]
                observed_paths = {
                    original["left_ref"],
                    original["right_ref"],
                }
                row["outcomes"][backend]["observed_clusters"] = [
                    {
                        "cluster_id": f"cluster-{cluster_results[backend][0][path]}",
                        "tier": cluster_results[backend][1][path],
                    }
                    for path in sorted(observed_paths)
                ]
                row["outcomes"][backend]["tier_high"] = (
                    digest_settings.high
                    if backend == "jaccard"
                    else separation["S2"]["embedding"]["positive"]["quantiles"]["p50"]
                )
                row["outcomes"][backend]["tier_medium"] = thresholds[backend]["S2"]
    for (split, query_id, backend), candidates in query_groups.items():
        query_text = material_by_case[candidates[0]["case_id"]][0]
        candidate_scores = [
            (
                relative,
                _similarity(query_text, page_text)
                if backend == "jaccard"
                else _cosine(by_text[query_text], by_text[page_text]),
            )
            for relative, page_text in kb_candidates
        ]
        ranked = sorted(candidate_scores, key=lambda item: (-item[1], item[0]))
        selected_paths = {
            path
            for path, score in ranked[: digest_settings.top_k]
            if score >= thresholds[backend]["S3"]
        }
        for row in candidates:
            predicted = original_by_id[row["case_id"]]["right_ref"] in selected_paths
            actual = row["label"] == "positive"
            row["outcomes"][backend].update(
                predicted_positive=predicted,
                correct=predicted == actual,
                error=predicted != actual,
            )
    for row in split_rows:
        original = original_by_id[row["case_id"]]
        if row["stage"] != "S3":
            continue
        for backend in ("jaccard", "embedding"):
            query_text = material_by_case[row["case_id"]][0]
            ranked = sorted(
                (
                    (
                        relative,
                        _similarity(query_text, page_text)
                        if backend == "jaccard"
                        else _cosine(by_text[query_text], by_text[page_text]),
                    )
                    for relative, page_text in kb_candidates
                ),
                key=lambda item: (-item[1], item[0]),
            )
            selected = sum(
                score >= thresholds[backend]["S3"]
                for _, score in ranked[: digest_settings.top_k]
            )
            predicted_action = "merge_multiple" if selected >= 2 else "revise" if selected == 1 else "new"
            row["outcomes"][backend]["predicted_action"] = predicted_action
            row["outcomes"][backend]["action_correct"] = predicted_action == row.get("gold_action")
    vectors_hash = vector_manifest_hash
    return split_rows, computed_gold_hash, vectors_hash, vector_manifest


def _sensitive_scan(
    *,
    corpus: Path,
    evidence_dir: Path,
    secret: str | None,
) -> dict[str, Any]:
    evidence_files = [
        path for path in evidence_dir.rglob("*") if path.is_file() and path.name != RESULT_NAME
    ]
    evidence_payloads = [(path, path.read_bytes()) for path in evidence_files]
    matches: list[str] = []
    if secret:
        needle = secret.encode("utf-8")
        matches.extend(
            f"credential:{path.relative_to(evidence_dir)}"
            for path, payload in evidence_payloads
            if needle and needle in payload
        )
    for source in corpus.rglob("*"):
        if not source.is_file():
            continue
        body = source.read_bytes()
        if not body:
            continue
        needles = {body}
        needles.update(
            line.strip()
            for line in body.splitlines()
            if len(line.strip()) >= 12
        )
        for path, payload in evidence_payloads:
            if any(needle in payload for needle in needles):
                matches.append(f"corpus:{path.relative_to(evidence_dir)}")
    return {
        "schema_version": "sensitive-scan.v1",
        "scanned_file_count": len(evidence_files),
        "credential_or_corpus_matches": sorted(set(matches)),
        "passed": not matches,
    }


def run_acceptance(
    *,
    corpus: Path,
    kb: Path,
    temp_root: Path,
    evidence_dir: Path,
    config: Path,
    cases: Path | None = None,
    env: dict[str, str] | None = None,
    provider_config_path: Path | None = None,
    probe: Callable[[EmbeddingSettings, dict[str, str]], dict[str, Any]] = real_probe,
    calibrate: Callable[..., dict[str, Any]] = _default_calibrate,
) -> dict[str, Any]:
    corpus, kb, temp_root, evidence_dir, config = validate_paths(
        corpus, kb, temp_root, evidence_dir, config
    )
    if any(temp_root.iterdir()):
        raise ValueError("temp root must be empty and caller-owned")
    if any(evidence_dir.iterdir()):
        raise ValueError("evidence directory must be empty and caller-owned")
    source_before = tree_manifest(corpus)
    kb_before = tree_manifest(kb)
    config_before = config.read_bytes()
    embedding, digest_settings = _embedding_settings(
        config, provider_config_path=provider_config_path
    )
    requested_backend = digest_settings.similarity.backend
    endpoint_identity = normalize_endpoint_identity(embedding.base_url)
    source_env = dict(os.environ if env is None else env)
    provider = effective_embedding_provider(
        provider_config_path=provider_config_path,
        base_url=embedding.base_url,
        model=embedding.model,
        expected_dimension=embedding.expected_dimension,
        api_key_env=embedding.api_key_env,
        env=source_env,
    )
    if provider.get("api_key"):
        source_env[embedding.api_key_env] = str(provider["api_key"])
    service: dict[str, Any] = {
        "probe_kind": "real_endpoint_request",
        "endpoint_identity": endpoint_identity,
        "model": embedding.model,
        "dimension": embedding.expected_dimension,
    }
    disposable = temp_root / "corpus-copy"
    preparation: dict[str, Any] | None = None
    cleanup: dict[str, Any] = {"complete": False}
    calibration: dict[str, Any]
    try:
        preparation = prepare_disposable_corpus(corpus, kb, disposable)
        if (
            preparation["markdown_count"] != 89
            or preparation["excluded_non_markdown_count"] != 2
        ):
            raise ValueError("company corpus boundary must be exactly 89 Markdown and 2 excluded")
        try:
            probed = probe(embedding, source_env)
            if probed != {
                "endpoint_identity": endpoint_identity,
                "model": embedding.model,
                "dimension": embedding.expected_dimension,
                "probe_fingerprint": probed.get("probe_fingerprint"),
            }:
                raise ValueError("probe identity does not match approved embedding config")
            fingerprint = probed.get("probe_fingerprint")
            if (
                not isinstance(fingerprint, str)
                or len(fingerprint) != 64
                or any(character not in "0123456789abcdef" for character in fingerprint)
            ):
                raise ValueError("probe_fingerprint must be sha256")
            service.update(probed)
            calibration = calibrate(
                cases=cases,
                evidence_dir=evidence_dir,
                service_identity=probed,
                corpus_hash=preparation["corpus_hash"],
                config=config,
                disposable_corpus=disposable,
                formal_kb=kb,
                embedding_settings=embedding,
                digest_settings=digest_settings,
                env=source_env,
            )
        except EmbeddingError:
            calibration = {
                "result": "BLOCKED",
                "reason_code": "embedding_service_unavailable",
            }
    finally:
        if preparation is not None and disposable.exists():
            cleanup_result = cleanup_disposable_corpus(disposable, preparation)
            cleanup = {
                "complete": cleanup_result["cleanup_complete"],
                "source_unchanged": cleanup_result["source_unchanged"],
                "formal_kb_unchanged": cleanup_result["formal_kb_unchanged"],
            }

    result_name = str(calibration["result"])
    artifact_path = evidence_dir / ARTIFACT_NAME
    if result_name == "BLOCKED":
        artifact_path.unlink(missing_ok=True)
    scan = _sensitive_scan(
        corpus=corpus,
        evidence_dir=evidence_dir,
        secret=source_env.get(embedding.api_key_env),
    )
    if not scan["passed"]:
        artifact_path.unlink(missing_ok=True)
        result_name = "BLOCKED"
        calibration = {
            "result": "BLOCKED",
            "reason_code": "sensitive_material_detected",
        }
    source_after = tree_manifest(corpus)
    kb_after = tree_manifest(kb)
    result: dict[str, Any] = {
        "schema_version": "phase4-real-service-acceptance.v1",
        "result": result_name,
        "requested_backend": requested_backend,
        "effective_runtime_backend": "jaccard",
        "service": service,
        "corpus": {
            "manifest_hash": preparation["corpus_hash"] if preparation else None,
            "markdown_count": preparation["markdown_count"] if preparation else None,
            "excluded_non_markdown_count": (
                preparation["excluded_non_markdown_count"] if preparation else None
            ),
        },
        "source_unchanged": source_after == source_before,
        "formal_kb_unchanged": kb_after == kb_before,
        "config_unchanged": config.read_bytes() == config_before,
        "config_sha256": _sha256_bytes(config_before),
        "cleanup": cleanup,
        "process_ownership": {
            "owner_pid": os.getpid(),
            "spawned_pids": [],
            "remaining_owned_pids": [],
        },
        "sensitive_scan": scan,
        "replay_match": bool(calibration.get("replay_match", False)),
    }
    if result_name == "BLOCKED":
        result["reason_code"] = calibration["reason_code"]
    elif "artifact" in calibration:
        result["artifact"] = {
            "path": calibration.get("artifact_path"),
            "adoption_status": calibration["artifact"]["adoption_status"],
            "sha256": _sha256_bytes(
                json.dumps(
                    calibration["artifact"],
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                + b"\n"
            ),
        }
    if not all(
        (
            result["source_unchanged"],
            result["formal_kb_unchanged"],
            result["config_unchanged"],
            cleanup["complete"],
            not any(temp_root.iterdir()),
            not list(evidence_dir.glob(".replay-*")),
        )
    ):
        artifact_path.unlink(missing_ok=True)
        result["result"] = "BLOCKED"
        result["reason_code"] = "isolation_or_cleanup_failed"
        result.pop("artifact", None)
    _write_json(evidence_dir / RESULT_NAME, result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--kb", type=Path, required=True)
    parser.add_argument("--temp-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--cases", type=Path)
    parser.add_argument("--provider-config", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = run_acceptance(
            corpus=args.corpus,
            kb=args.kb,
            temp_root=args.temp_root,
            evidence_dir=args.evidence_dir,
            config=args.config,
            cases=args.cases,
            provider_config_path=args.provider_config or configured_provider_config_path(),
        )
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(str(error))
        return 2
    print(
        json.dumps(
            {
                "result": result["result"],
                "evidence": str((args.evidence_dir / RESULT_NAME).resolve()),
            },
            sort_keys=True,
        )
    )
    return 0 if result["result"] != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
