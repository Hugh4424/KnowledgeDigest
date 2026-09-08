from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from knowledge_digest.compiler import (
    _EXPECTED_DIMENSIONS,
    _EXPECTED_PROJECTION_IDS,
    DigestRequest,
    _canonical_json,
    _formal_snd_artifacts,
    _formalise_public_bundle,
    _FORMAL_PUBLIC_AUDIT_FILES,
    _M402_RUNTIME_CONTRACT_FILES,
    _load_sources,
    _route_ledger_projection,
    PAGE_TYPES,
    _sha,
    _surface_qa_from_files,
    _tree_hash,
    _validate_m402_worktree_binding,
    _validate_m402_published_closure,
    _validate_m402_gate,
    _validate_m402_runtime_config,
    _validate_m402_runtime_identity,
    _run_c3_fixture,
)
from knowledge_digest.publisher import commit
from knowledge_digest.quality import promote_quality_result


class _C3FakeModel:
    identity = {"model": "c3-fake"}

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if "通用事实校验器" in prompt:
            page_ids = list(dict.fromkeys(re.findall(r'"page_id"\s*:\s*"((?:src|topic)-[^\"]+)"', prompt)))
            return json.dumps({"results": [{"page_id": page_id, "violations": []} for page_id in page_ids]}, ensure_ascii=False)
        if "规划少量跨来源主题页" in prompt:
            return json.dumps({"topics": []}, ensure_ascii=False)
        evidence_id = re.search(r'"evidence_id"\s*:\s*"([^\"]+)"', prompt).group(1)
        return json.dumps({
            "title": "受控 fixture 页面",
            "question": "如何完成这项操作？",
            "page_type": "operation",
            "axes": {
                "product": "GoInsight",
                "module": "fixture 模块",
                "object": "fixture 对象",
                "scenario": "fixture 场景",
                "boundary": "fixture 边界",
            },
            "summary": {"body": "来源中的受控事实。", "evidence_ids": [evidence_id]},
            "sections": {
                heading: {"body": "来源中的受控事实。", "evidence_ids": [evidence_id]}
                for heading in PAGE_TYPES["operation"]
            },
        }, ensure_ascii=False)


class _C3FakeEmbedder:
    identity = {"model": "c3-fake", "dimension": "2"}

    def __init__(self) -> None:
        self.calls = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [[1.0, 0.0] for _ in texts]


_C3_OWNER_COMMAND = (
    "uv run --frozen pytest -q "
    "tests/acceptance/test_task5_publication_contract.py "
    "tests/acceptance/test_task5_quality_gate.py "
    "tests/acceptance/test_task5_projection.py "
    "tests/test_simple_digest.py"
)

_C3_AC_ANCHORS = (
    "tests/acceptance/test_task5_publication_contract.py::test_registered_digest_entrypoint_is_the_thin_reader_cli",
    "tests/test_simple_digest.py::test_digest_publishes_reader_home_audit_and_exact_snapshots",
    "tests/test_simple_digest.py::test_quality_embedding_order_is_consumed_by_qwen_closure",
    "tests/test_simple_digest.py::test_one_provider_failure_keeps_other_reader_pages_and_marks_audit",
    "tests/acceptance/test_task5_quality_gate.py::test_quality_gate_rejects_static_basis_without_blind_judge_receipt",
    "tests/acceptance/test_task5_quality_gate.py::test_public_result_does_not_promote_judge_only_result",
    "tests/test_simple_digest.py::test_slice_then_full_reuses_exact_source_prompt_in_one_context",
    "tests/acceptance/test_task5_quality_gate.py::test_quality_gate_requires_every_dimension_to_win_twice",
    "tests/acceptance/test_task5_projection.py::test_coordinate_map_preserves_non_overlapping_raw_offsets",
    "tests/test_simple_digest.py::test_reader_tree_preserves_each_raw_product_root_and_page_type",
    "tests/test_simple_digest.py::test_public_secret_scan_blocks_before_atomic_publication",
    "tests/test_simple_digest.py::test_m402_gate_blocks_before_provider_or_raw_when_bindings_are_missing",
    "tests/acceptance/test_task5_projection.py::test_snd_verifier_rejects_tampered_block_result",
)


def _c3_trace_factory(run: dict[str, object], tree_sha256: str) -> list[dict[str, object]]:
    return [
        {
            "ac_id": f"AC-v4-{index:02d}",
            "evidence": {
                "command": _C3_OWNER_COMMAND,
                "input_snapshot": str(run["snapshot_tree"]),
                "input_material": str(run["material_id"]),
                "output_ref": "C3/run-root/bundle",
                "output_sha256": tree_sha256,
                "actual_result": f"anchor={_C3_AC_ANCHORS[index - 1]}; C3 owner test passed for AC-v4-{index:02d}",
                "failure_counterexample": f"anchor={_C3_AC_ANCHORS[index - 1]}; missing formal closure must fail AC-v4-{index:02d}.",
            },
        }
        for index in range(1, 14)
    ]


def test_c3_fixture_rejects_trace_without_concrete_test_anchors(tmp_path: Path) -> None:
    source = tmp_path / "raw" / "GoInsight"
    source.mkdir(parents=True)
    (source / "one.md").write_text("## 一项操作\n\n管理员可以完成这项操作。\n", encoding="utf-8")
    attempt = tmp_path / "attempts" / "c3-generic-trace" / "C3"

    def generic_trace(run: dict[str, object], tree_sha256: str) -> list[dict[str, object]]:
        return [
            {
                "ac_id": f"AC-v4-{index:02d}",
                "evidence": {
                    "command": _C3_OWNER_COMMAND,
                    "input_snapshot": str(run["snapshot_tree"]),
                    "input_material": str(run["material_id"]),
                    "output_ref": "C3/run-root/bundle",
                    "output_sha256": tree_sha256,
                    "actual_result": "all C3 behavior tests passed",
                    "failure_counterexample": "missing closure must fail",
                },
            }
            for index in range(1, 14)
        ]

    with pytest.raises(ValueError, match="AC trace is not verifiable"):
        _run_c3_fixture(
            DigestRequest(source.parent, tmp_path / "unused-output", tmp_path / "unused-provider.json"),
            (_C3FakeModel(), _C3FakeEmbedder()),
            attempt_path=attempt,
            snapshot_tree="a" * 40,
            material_id="b" * 64,
            command=_C3_OWNER_COMMAND,
            ac_trace_factory=generic_trace,
        )

    assert not attempt.exists()


def test_c3_fixture_requires_external_trace_before_any_attempt_write(tmp_path: Path) -> None:
    from knowledge_digest.compiler import _run_c3_fixture

    source = tmp_path / "raw" / "GoInsight"
    source.mkdir(parents=True)
    (source / "one.md").write_text("## 一项操作\n\n管理员可以完成这项操作。\n", encoding="utf-8")
    attempt = tmp_path / "attempts" / "c3-no-trace" / "C3"

    with pytest.raises(ValueError, match="externally produced AC trace"):
        _run_c3_fixture(
            DigestRequest(source.parent, tmp_path / "unused-output", tmp_path / "unused-provider.json"),
            (_C3FakeModel(), _C3FakeEmbedder()),
            attempt_path=attempt,
            snapshot_tree="a" * 40,
            material_id="b" * 64,
            command="[\"c3\"]",
            ac_trace_factory=None,
        )

    assert not attempt.exists()


def test_c3_fixture_publishes_only_closed_formal_bundle_and_real_inverse(tmp_path: Path) -> None:
    source = tmp_path / "raw"
    for product in ("EMM for Android", "EMM for iOS", "GoInsight", "Merchant System"):
        product_dir = source / product
        product_dir.mkdir(parents=True)
        (product_dir / "one.md").write_text("## 一项操作\n\n管理员可以完成这项操作。\n", encoding="utf-8")
    attempt = tmp_path / "attempts" / "c3-pass" / "C3"
    result = _run_c3_fixture(
        DigestRequest(source, tmp_path / "unused-output", tmp_path / "unused-provider.json"),
        (_C3FakeModel(), _C3FakeEmbedder()),
        attempt_path=attempt,
        snapshot_tree="a" * 40,
        material_id="b" * 64,
        command=_C3_OWNER_COMMAND,
        ac_trace_factory=_c3_trace_factory,
    )

    bundle = attempt / "run-root" / "bundle"
    assert result["status"] == "passed"
    assert result["run_root_ref"] == "run-root/bundle"
    assert bundle.is_dir()
    assert {path.relative_to(bundle).as_posix() for path in bundle.glob("_audit/*")} == set(_FORMAL_PUBLIC_AUDIT_FILES)
    assert {path.name for path in (bundle / "products").iterdir() if path.is_dir()} == {
        "emm-for-android", "emm-for-ios", "goinsight", "merchant-system",
    }
    assert not (attempt / "run-root" / "attempt").exists()

    run = json.loads((bundle / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert len(run["m401_ac_trace"]) == 13
    assert run["m401_ac_trace"][0]["evidence"]["output_sha256"] == _tree_hash({
        path.relative_to(bundle).as_posix(): path.read_bytes()
        for path in bundle.rglob("*")
        if path.is_file()
    })
    attempt_record = json.loads((attempt / "attempt.json").read_text(encoding="utf-8"))
    assert set(attempt_record) == {
        "schema_version", "gate", "attempt_id", "attempt_seq", "material_id", "command",
        "command_sha256", "before_snapshot", "after_snapshot", "changed_paths",
        "before_sha256", "after_sha256", "patch_sha256", "inverse_patch_ref",
        "inverse_patch_sha256", "inverse_base_after_snapshot", "run_root_ref", "exit_code",
        "status", "reason_code",
    }
    assert attempt_record["status"] == "passed"
    assert (attempt / "inverse.patch").stat().st_size > 0

    reverse_check_root = tmp_path / "reverse-check"
    subprocess.run(["git", "init", "-q", str(reverse_check_root)], check=True)
    shutil.copytree(bundle, reverse_check_root / "run-root" / "bundle")
    subprocess.run(["git", "-C", str(reverse_check_root), "add", "run-root"], check=True)
    reverse_check = subprocess.run(
        ["git", "-C", str(reverse_check_root), "apply", "--check", "--reverse", str(attempt / "inverse.patch")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert reverse_check.returncode == 0, reverse_check.stderr


def test_c3_fixture_rejects_existing_attempt_without_touching_it(tmp_path: Path) -> None:
    source = tmp_path / "raw" / "GoInsight"
    source.mkdir(parents=True)
    (source / "one.md").write_text("内容。\n", encoding="utf-8")
    attempt = tmp_path / "attempts" / "c3-existing" / "C3"
    attempt.mkdir(parents=True)
    marker = attempt / "keep.txt"
    marker.write_text("keep\n", encoding="utf-8")

    with pytest.raises(ValueError, match="new and empty"):
        _run_c3_fixture(
            DigestRequest(source.parent, tmp_path / "unused-output", tmp_path / "unused-provider.json"),
            (_C3FakeModel(), _C3FakeEmbedder()),
            attempt_path=attempt,
            snapshot_tree="a" * 40,
            material_id="b" * 64,
            command=_C3_OWNER_COMMAND,
            ac_trace_factory=_c3_trace_factory,
        )
    assert marker.read_text(encoding="utf-8") == "keep\n"


def test_m402_runtime_authority_is_rebound_from_current_bytes(tmp_path: Path) -> None:
    source_root = Path(__file__).parents[2]
    project_root = tmp_path / "project"
    config_root = project_root / "config"
    config_root.mkdir(parents=True)

    runtime_source = source_root / "config/task5-reader-quality-provider-v2.json"
    runtime = json.loads(runtime_source.read_text(encoding="utf-8"))
    authority_map = source_root / "config/task5-runtime-authority-map-v1.json"
    shutil.copy2(authority_map, project_root / "config/task5-runtime-authority-map-v1.json")
    authority_map_value = json.loads(authority_map.read_text(encoding="utf-8"))
    authority_paths = [item["path"] for item in authority_map_value["authorities"]]
    for relative in sorted(set(_M402_RUNTIME_CONTRACT_FILES.values()) | set(authority_paths)):
        source = source_root / relative
        target = project_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for field, relative in _M402_RUNTIME_CONTRACT_FILES.items():
        authority = json.loads((project_root / relative).read_text(encoding="utf-8"))
        runtime["quality_contract"][field] = _sha(_canonical_json(authority))
    runtime_path = config_root / runtime_source.name
    runtime_path.write_bytes(_canonical_json(runtime))
    quality_path = project_root / "config/task5-quality-cases-v2.json"
    for item in authority_map_value["authorities"]:
        if item["path"] == "config/task5-reader-quality-provider-v2.json":
            item["actual_sha256"] = _sha(runtime_path.read_bytes())
            item["canonical_sha256"] = _sha(_canonical_json(runtime))
            break
    (project_root / "config/task5-runtime-authority-map-v1.json").write_bytes(
        _canonical_json(authority_map_value)
    )

    authority_identity = _validate_m402_runtime_config(
        runtime_path,
        runtime,
        runtime_path.read_bytes(),
        quality_path,
        project_root=project_root,
    )
    handoff = {
        "runtime_contract": {
            "runtime_contract_id": authority_identity["runtime_contract_id"],
            "runtime_contract_hash": authority_identity["derived_runtime_contract_hash"],
        },
    }
    _validate_m402_runtime_identity(handoff, authority_identity)
    handoff["runtime_contract"]["runtime_contract_hash"] = "0" * 64
    with pytest.raises(ValueError, match="runtime contract identity mismatch"):
        _validate_m402_runtime_identity(handoff, authority_identity)

    (project_root / "config/task5-source-block-claim-contract-v1.json").write_text(
        '{"tampered":true}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="runtime authority hash is stale"):
        _validate_m402_runtime_config(
            runtime_path,
            runtime,
            runtime_path.read_bytes(),
            quality_path,
            project_root=project_root,
        )


def _m402_release_closure_fixture(tmp_path: Path) -> tuple[dict, dict[str, bytes], dict, Path]:
    run_id = "run-m402-closure"
    source_rows = []
    for index in range(89):
        status = "known_empty" if index == 87 else "duplicate_alias" if index == 88 else "ready"
        source_rows.append({
            "source_id": f"source-{index}",
            "relative_path": f"product-{index}.md",
            "product_key": ("emm-for-android", "emm-for-ios", "goinsight", "merchant-system")[index % 4],
            "product_label": "Product",
            "raw_hash": f"{index:064x}",
            "status": status,
            "source_digest_eligible": status == "ready",
            "duplicate_of": "source-0" if status == "duplicate_alias" else None,
            "evidence_ids": [f"evidence-{index}"],
            "reader_page_ids": [f"page-source-{index}"],
            "failure": None,
        })
    page_rows = [
        {
            "page_id": f"page-source-{index}",
            "page_key": f"source:source-{index}",
            "page_type": page_type,
            "axes": {name: "value" for name in ("product", "module", "object", "scenario", "boundary")},
            "source_ids": [f"source-{index}"],
            "path": f"products/product-{index}.md",
            "surface_sha256": "a" * 64,
        }
        for index, page_type in enumerate(PAGE_TYPES)
    ]
    page_rows.extend(
        {
            "page_id": f"page-answer-{index}",
            "page_key": f"answer:projection-{index}",
            "page_type": "diagnosis",
            "axes": {name: "value" for name in ("product", "module", "object", "scenario", "boundary")},
            "source_ids": ["source-0"],
            "path": f"products/answers/{index}.md",
            "surface_sha256": "b" * 64,
        }
        for index in range(12)
    )
    manifest = {
        "schema_version": "knowledge-digest-run-manifest.v1",
        "source_count": 89,
        "sources": source_rows,
        "routes": [],
        "pages": page_rows,
        "tree_sha256": "c" * 64,
    }
    routes = []
    for index, projection_id in enumerate(_EXPECTED_PROJECTION_IDS):
        routes.append({
            "query_id": projection_id,
            "question": "question",
            "scene": "scene",
            "route_name": "route",
            "product_key": "goinsight",
            "projection_id": projection_id,
            "candidate_source_ids": ["source-0"],
            "status": "ready",
            "selected_page_ids": [f"page-answer-{index}"],
            "home_target_page_identity": f"page-answer-{index}",
            "selected_source_ids": ["source-0"],
            "scores": {"source-0": 1.0},
            "embedding_receipt": {
                "provider": "jina",
                "model": "jina-embeddings-v3",
                "request_identity": "request",
                "selected_source_ids": ["source-0"],
                "selected_closure_sha256": "a" * 64,
                "response_sha256": "b" * 64,
                "status": "passed",
            },
            "qwen_payload_sha256": "c" * 64,
            "evidence_bindings": [],
            "failure": None,
        })
    manifest["routes"] = routes
    run = {
        "run_id": run_id,
        "source_count": 89,
        "source_manifest_hash": "d" * 64,
        "quality_projection_count": 12,
        "quality_projection_ids": list(_EXPECTED_PROJECTION_IDS),
        "quality_page_count": 12,
        "manifest": manifest,
        "companybrain_binding": {
            "companybrain_snapshot_id": "snapshot-1",
            "companybrain_tree_sha256": "e" * 64,
            "observation_sha256": "f" * 64,
        },
    }
    quality_rows = [
        {"projection_key": projection_id, "dimension_id": dimension, "verdict": "UNKNOWN"}
        for projection_id in _EXPECTED_PROJECTION_IDS
        for dimension in _EXPECTED_DIMENSIONS
    ]
    comparison_dimensions = {
        projection_id: {dimension: ["KD_WIN", "KD_WIN"] for dimension in _EXPECTED_DIMENSIONS}
        for projection_id in _EXPECTED_PROJECTION_IDS
    }
    candidate = {
        "run_id": run_id,
        "source_count_in_audit": 89,
        "source_count_on_disk": 89,
        "source_manifest_sha256": "d" * 64,
        "candidate_tree_sha256": "c" * 64,
        "candidate_manifest_ref": "bundle/_audit/directory-manifest.json",
        "candidate_manifest_sha256": "d" * 64,
        "candidate_reader_file_count": 12,
        "rendered_units": 1,
        "bound_units": 1,
        "lineage_coverage": 1.0,
        "projection_count": 12,
        "projection_ids": list(_EXPECTED_PROJECTION_IDS),
        "dimensions": list(_EXPECTED_DIMENSIONS),
        "dimension_verdicts": {
            projection_id: {dimension: ["UNKNOWN", "UNKNOWN"] for dimension in _EXPECTED_DIMENSIONS}
            for projection_id in _EXPECTED_PROJECTION_IDS
        },
        "quality_rows": quality_rows,
        "comparison": {
            "verdict": "released",
            "publication_status": "released",
            "hard_blockers": [],
            "dimension_verdicts": comparison_dimensions,
        },
        "companybrain_snapshot_id": "snapshot-1",
        "companybrain_tree_sha256": "e" * 64,
        "observation_sha256": "f" * 64,
    }
    case_by_projection = {
        projection_id: projection_id.split(".", 1)[0]
        for projection_id in _EXPECTED_PROJECTION_IDS
    }
    observation_rows = [
        {
            "case_id": case_by_projection[projection_id],
            "projection_id": projection_id,
            "dimension_id": dimension,
            "status": "absent",
            "score": None,
            "source_refs": [],
            "visible_ref": None,
            "audit_ref": None,
            "gap_ref": None,
            "kd_ref": None,
        }
        for projection_id in _EXPECTED_PROJECTION_IDS
        for dimension in _EXPECTED_DIMENSIONS
    ]
    observation = {
        "run_id": run_id,
        "source_manifest_sha256": "d" * 64,
        "companybrain_snapshot_id": "snapshot-1",
        "companybrain_tree_sha256": "e" * 64,
        "rows": observation_rows,
    }
    observation["observation_sha256"] = _sha(_canonical_json({
        key: observation[key]
        for key in ("run_id", "source_manifest_sha256", "companybrain_snapshot_id", "companybrain_tree_sha256", "rows")
    }))
    run["companybrain_binding"]["observation_sha256"] = observation["observation_sha256"]
    candidate["observation_sha256"] = observation["observation_sha256"]
    gap_types = {
        "DIM-01.route": "wrong_relation",
        "DIM-02.taxonomy": "missing_taxonomy_axis",
        "DIM-03.business-answer": "missing_stage",
        "DIM-04.page-type": "untyped_contract",
        "DIM-05.reader-audit": "missing_provenance",
    }
    for row in quality_rows:
        projection_id = row["projection_key"]
        dimension = row["dimension_id"]
        observation_row = next(item for item in observation_rows if item["projection_id"] == projection_id and item["dimension_id"] == dimension)
        observation_digest = _sha(_canonical_json({
            "case_id": observation_row["case_id"],
            "projection_id": projection_id,
            "dimension_id": dimension,
            "status": observation_row["status"],
            "score": observation_row["score"],
            "source_refs": observation_row["source_refs"],
            "visible_ref": observation_row["visible_ref"],
            "audit_ref": observation_row["audit_ref"],
            "gap_ref": observation_row["gap_ref"],
            "kd_ref": observation_row["kd_ref"],
        }))
        reader_ref = f"products/answers/{projection_id}#unit-{dimension}"
        row.update({
            "kd_observation_ref": reader_ref,
            "cb_observation_ref": f"companybrain:{projection_id}:{dimension}",
            "observation_digests": {"reader": "a" * 64, "companybrain": observation_digest},
            "advantage_basis": {
                "projection_key": projection_id,
                "dimension_id": dimension,
                "cb_observation_ref": f"companybrain:{projection_id}:{dimension}",
                "cb_observation_digest": observation_digest,
                "cb_gap_type": gap_types[dimension],
                "cb_gap_locator": "CompanyBrain/page#anchor",
                "atom_observations": [],
                "gap_atom_refs": [],
                "stage_observations": [],
                "gap_stage_refs": [],
                "quality_feature_observations": [],
                "gap_quality_feature_refs": [],
                "strict_improvement_refs": ["atom"],
                "non_regression": True,
                "kd_completion_refs": [reader_ref, f"Audit.md#page-{projection_id}"],
                "kd_completion_surfaces": ["Reader", "Audit"],
                "kd_completion_digest": "a" * 64,
            },
        })
    observation_path = tmp_path / "actual-run" / "attempts" / run_id / "companybrain-observation.json"
    observation_path.parent.mkdir(parents=True)
    observation_path.write_bytes(_canonical_json(observation))
    public_files = {
        "_audit/companybrain-route-snapshot.json": _canonical_json({
            "schema_version": "knowledge-digest-companybrain-route-snapshot.v1",
            "status": "available",
            "run_id": run_id,
            "source_manifest_sha256": "d" * 64,
            "companybrain_snapshot_id": "snapshot-1",
            "companybrain_tree_sha256": "e" * 64,
            "observation_sha256": observation["observation_sha256"],
            "regular_markdown_files": [],
            "entry_files": [],
            "observation_ref": "companybrain-observation:run-m402-closure",
            "failure": None,
        }),
        "_audit/route-ledger.jsonl": _route_ledger_projection(manifest),
    }
    public_files.update({row["path"]: b"# page\n" for row in page_rows})
    return run, public_files, candidate, tmp_path


def test_m402_finalizer_rechecks_real_run_closure_after_rename(tmp_path: Path) -> None:
    run, public_files, candidate, evidence_root = _m402_release_closure_fixture(tmp_path)
    _validate_m402_published_closure(
        run,
        public_files,
        candidate,
        evidence_root=evidence_root,
        published_tree_sha256="c" * 64,
        published_manifest_sha256="d" * 64,
    )

    run, public_files, candidate, evidence_root = _m402_release_closure_fixture(tmp_path / "bad-status")
    run["manifest"]["sources"][0]["status"] = "known_empty"
    with pytest.raises(ValueError, match="source status closure"):
        _validate_m402_published_closure(
            run,
            public_files,
            candidate,
            evidence_root=evidence_root,
            published_tree_sha256="c" * 64,
            published_manifest_sha256="d" * 64,
        )

    run, public_files, candidate, evidence_root = _m402_release_closure_fixture(tmp_path / "bad-quality")
    candidate["comparison"]["dimension_verdicts"][_EXPECTED_PROJECTION_IDS[0]][_EXPECTED_DIMENSIONS[0]] = ["TIE", "TIE"]
    with pytest.raises(ValueError, match="strict 12x5 KD_WIN"):
        _validate_m402_published_closure(
            run,
            public_files,
            candidate,
            evidence_root=evidence_root,
            published_tree_sha256="c" * 64,
            published_manifest_sha256="d" * 64,
        )


def test_surface_qa_replays_reader_audit_links_and_anchors() -> None:
    run = {
        "run_id": "run-surface",
        "manifest": {
            "pages": [{
                "page_id": "page-1",
                "path": "products/goinsight/concept/page.md",
            }],
            "routes": [{"home_target_page_identity": "page-1"}],
        },
    }
    public_files = {
        "README.md": b"# Reader\n",
        "Home.md": b"[Page](products/goinsight/concept/page.md)\n",
        "Audit.md": b'<a id="page-page-1"></a>\n',
        "products/goinsight/concept/page.md": b"# Page\n[Audit](../../../Audit.md#page-page-1)\n",
    }
    tree_sha256 = _tree_hash(public_files)
    receipt = _surface_qa_from_files(
        run,
        public_files,
        phase="published",
        candidate_tree_sha256=tree_sha256,
        candidate_manifest_sha256="a" * 64,
        published_tree_sha256=tree_sha256,
        published_manifest_sha256="a" * 64,
    )
    assert receipt["status"] == "passed"
    assert receipt["checks"]["relative_links"] is True
    assert receipt["checks"]["audit_anchors"] is True

    broken = dict(public_files)
    broken["Home.md"] = b"[Missing](products/goinsight/concept/missing.md)\n"
    failed = _surface_qa_from_files(
        run,
        broken,
        phase="published",
        candidate_tree_sha256=_tree_hash(broken),
        candidate_manifest_sha256="a" * 64,
        published_tree_sha256=_tree_hash(broken),
        published_manifest_sha256="a" * 64,
    )
    assert failed["status"] == "failed"
    assert any(item.startswith("link_target_missing:") for item in failed["issues"])

    mentioned_only = dict(public_files)
    mentioned_only["Home.md"] = "目标路径：products/goinsight/concept/page.md\n".encode("utf-8")
    unreachable = _surface_qa_from_files(
        run,
        mentioned_only,
        phase="published",
        candidate_tree_sha256=_tree_hash(mentioned_only),
        candidate_manifest_sha256="a" * 64,
        published_tree_sha256=_tree_hash(mentioned_only),
        published_manifest_sha256="a" * 64,
    )
    assert unreachable["status"] == "failed"
    assert "home_route_unreachable:page-1" in unreachable["issues"]

def test_m402_preflight_requires_quality_config_before_other_inputs(tmp_path: Path) -> None:
    gate_root = tmp_path / "quality" / "evidence" / "task5"
    gate_root.mkdir(parents=True)
    packet = gate_root / "M401-evidence-packet.json"
    receipt = gate_root / "M401-R-review-receipt.json"
    handoff = gate_root / "workflowhub-implementation-handoff.json"
    packet.write_bytes(b"{}")
    receipt.write_bytes(b"{}")
    handoff.write_bytes(b"{}")
    request = DigestRequest(
        new_dir=tmp_path / "raw",
        kb_dir=tmp_path / "output",
        provider_config_path=tmp_path / "provider.json",
        gate="M402",
        runtime_config_path=tmp_path / "runtime.json",
        m401_packet_path=packet,
        m401_r_receipt_path=receipt,
        workflowhub_successor_path=handoff,
        companybrain_root=tmp_path / "companybrain",
    )

    with pytest.raises(ValueError, match="M402 requires a quality config"):
        _validate_m402_gate(request)


def test_m402_rejects_a_handoff_for_another_worktree(tmp_path: Path) -> None:
    handoff = {"current": {"worktree": str(tmp_path / "other-checkout")}}

    with pytest.raises(ValueError, match="does not match the compiler worktree"):
        _validate_m402_worktree_binding(handoff)


def test_snd_operational_error_is_a_release_blocker(tmp_path: Path) -> None:
    raw = tmp_path / "raw" / "GoInsight"
    raw.mkdir(parents=True)
    (raw / "17  智能搭建.md").write_text(
        "系统发生错误后检查日志并重试。\n",
        encoding="utf-8",
    )
    sources = _load_sources(tmp_path / "raw")

    _certificate, verifier = _formal_snd_artifacts(
        sources,
        source_snapshot_id="snapshot-test",
        material_id="m" * 64,
    )

    assert verifier["status"] == "unknown"
    assert verifier["failure_code"] == "zero_match_not_closed"


def test_formal_compiler_projection_keeps_only_the_v47_machine_tree(tmp_path: Path) -> None:
    raw = tmp_path / "raw" / "GoInsight"
    raw.mkdir(parents=True)
    (raw / "one.md").write_text("## 一\n\n资料。\n", encoding="utf-8")
    sources = _load_sources(tmp_path / "raw")
    source = sources[0]
    page_id = f"source:{source.source_id}"
    manifest = {
        "schema_version": "knowledge-digest-run-manifest.v1",
        "source_count": 1,
        "sources": [{
            "source_id": source.source_id,
            "relative_path": source.relative_path,
            "product_key": source.product,
            "product_label": source.product_label,
            "raw_hash": _sha(source.raw_bytes),
            "status": source.status,
            "source_digest_eligible": True,
            "duplicate_of": None,
            "evidence_ids": [str(source.evidence[0]["evidence_id"])],
            "reader_page_ids": [page_id],
            "failure": None,
        }],
        "routes": [],
        "pages": [{
            "page_id": page_id,
            "page_key": page_id,
            "page_type": "concept",
            "axes": {name: "未明确" for name in ("product", "module", "object", "scenario", "boundary")},
            "source_ids": [source.source_id],
            "path": "products/goinsight/concept/one.md",
            "surface_sha256": "a" * 64,
        }],
        "tree_sha256": "",
    }
    run = {
        "schema_version": "knowledge-digest-run.v1",
        "run_id": "run-formal-test",
        "evaluation_mode": "full",
        "source_manifest_hash": "b" * 64,
        "source_count": 1,
        "quality_projection_count": 0,
        "provider_calls": {"llm": 1, "embedding": 1},
        "manifest": manifest,
        "quality_provider_trace": {},
        # The formalizer must not trust a staging release decision when the
        # deterministic SND closure is not passed.
        "outcome": "released",
    }
    files = {
        "README.md": b"# KnowledgeDigest\n",
        "Home.md": b"# Home\n",
        "Audit.md": "- 来源索引：[_audit/sources.jsonl](_audit/sources.jsonl)\n".encode("utf-8"),
        "products/goinsight/concept/one.md": (
            "# One\n"
            "来源：[_audit/sources.jsonl](_audit/sources.jsonl)\n"
            "证据：[_audit/evidence.jsonl](_audit/evidence.jsonl)\n"
            "质量：[_audit/quality.json](_audit/quality.json)\n"
        ).encode("utf-8"),
        "_audit/companybrain-route-snapshot.json": b'{"schema_version":"knowledge-digest-companybrain-route-snapshot.v1"}\n',
        "_audit/run-result.json": _canonical_json(run),
        "_audit/sources.jsonl": b"legacy\n",
        "_audit/evidence.jsonl": b"legacy\n",
        "_audit/quality.json": b"legacy\n",
        "_audit/run-result.receipt.json": b"legacy\n",
    }

    result = _formalise_public_bundle(
        files,
        sources=sources,
        run_id="run-formal-test",
        quality_result_ref="actual-run/attempts/run-formal-test/quality-result.json",
        quality_result_sha256="c" * 64,
        material_id="d" * 64,
    )

    audit = {path for path in result if path.startswith("_audit/")}
    assert audit == {
        "_audit/audit-pages.json",
        "_audit/source-status.json",
        "_audit/companybrain-route-snapshot.json",
        "_audit/semantic-compile-ledger.jsonl",
        "_audit/semantic-response-ledger.jsonl",
        "_audit/route-ledger.jsonl",
        "_audit/raw-coordinate-map.json",
        "_audit/source-not-documented-zero-match.json",
        "_audit/source-not-documented-verifier.json",
        "_audit/run-result.json",
        "_audit/directory-manifest.json",
    }
    assert not any(path.endswith(name) for path in result for name in ("sources.jsonl", "evidence.jsonl", "quality.json", "run-result.receipt.json"))
    assert all(
        not re.search(r"\]\(_audit/(?:sources\.jsonl|evidence\.jsonl|quality\.json)\)", content.decode("utf-8"))
        for path, content in result.items()
        if path.endswith(".md")
    )
    public_run = json.loads(result["_audit/run-result.json"].decode("utf-8"))
    public_page = next(
        page for page in public_run["manifest"]["pages"]
        if page["path"] == "products/goinsight/concept/one.md"
    )
    assert public_page["surface_sha256"] == _sha(result[public_page["path"]])


def test_formal_compiler_removes_nested_links_to_non_public_ledgers(tmp_path: Path) -> None:
    raw = tmp_path / "raw" / "GoInsight"
    raw.mkdir(parents=True)
    (raw / "one.md").write_text("## 一\n\n资料。\n", encoding="utf-8")
    sources = _load_sources(tmp_path / "raw")
    manifest = {
        "schema_version": "knowledge-digest-run-manifest.v1",
        "source_count": 1,
        "sources": [],
        "routes": [],
        "pages": [],
        "tree_sha256": "",
    }
    run = {
        "schema_version": "knowledge-digest-run.v1",
        "run_id": "run-formal-nested-link",
        "source_manifest_hash": "b" * 64,
        "source_count": 1,
        "provider_calls": {},
        "manifest": manifest,
        "quality_provider_trace": {},
        "outcome": "released",
    }
    files = {
        "README.md": b"# KnowledgeDigest\n",
        "Home.md": b"# Home\n",
        "Audit.md": b"# Audit\n",
        "products/goinsight/operation/one.md": (
            "# One\n"
            "来源：[来源索引](../../../_audit/sources.jsonl)\n"
            "证据：[Evidence](../../../_audit/evidence.jsonl)\n"
            "质量：[Quality](../../../_audit/quality.json)\n"
        ).encode("utf-8"),
        "_audit/companybrain-route-snapshot.json": b"{}\n",
        "_audit/run-result.json": _canonical_json(run),
        "_audit/sources.jsonl": b"legacy\n",
        "_audit/evidence.jsonl": b"legacy\n",
        "_audit/quality.json": b"legacy\n",
    }

    result = _formalise_public_bundle(
        files,
        sources=sources,
        run_id="run-formal-nested-link",
        quality_result_ref="actual-run/attempts/run-formal-nested-link/quality-result.json",
        quality_result_sha256="c" * 64,
        material_id="d" * 64,
    )

    text = result["products/goinsight/operation/one.md"].decode("utf-8")
    assert "../../../_audit/sources.jsonl" not in text
    assert "../../../_audit/evidence.jsonl" not in text
    assert "../../../_audit/quality.json" not in text
    assert "来源索引（机器证据保留在 host-only receipt）" in text
    public_run = json.loads(result["_audit/run-result.json"])
    assert public_run["schema_version"] == "knowledge-digest-run.v1"
    assert public_run["publication_status"] == "not_released"
    assert public_run["outcome"] == "success"
    assert public_run["canonical_sha256"]


def test_formal_compiler_never_releases_an_attempt_quality_artifact(tmp_path: Path) -> None:
    raw = tmp_path / "raw" / "GoInsight"
    raw.mkdir(parents=True)
    (raw / "one.md").write_text("## 一\n\n资料说明。\n", encoding="utf-8")
    sources = _load_sources(tmp_path / "raw")
    run = {
        "schema_version": "knowledge-digest-run.v1",
        "run_id": "run-candidate-only",
        "outcome": "released",
        "manifest": {
            "schema_version": "knowledge-digest-run-manifest.v1",
            "source_count": 1,
            "sources": [],
            "routes": [],
            "pages": [],
            "tree_sha256": "",
        },
    }
    files = {
        "README.md": b"# KnowledgeDigest\n",
        "Home.md": b"# Home\n",
        "Audit.md": b"Audit\n",
        "products/goinsight/concept/one.md": b"# One\n",
        "_audit/run-result.json": _canonical_json(run),
    }

    result = _formalise_public_bundle(
        files,
        sources=sources,
        run_id="run-candidate-only",
        quality_result_ref="actual-run/attempts/run-candidate-only/quality-result.json",
        quality_result_sha256="a" * 64,
        material_id="b" * 64,
    )
    public_run = json.loads(result["_audit/run-result.json"])
    assert public_run["publication_status"] == "not_released"
    assert public_run["outcome"] == "success"
    assert public_run["quality_result"]["ref"].startswith("actual-run/attempts/")


def test_quality_promotion_requires_two_round_kd_win_and_published_tree_binding() -> None:
    dimensions = (
        "DIM-01.route",
        "DIM-02.taxonomy",
        "DIM-03.business-answer",
        "DIM-04.page-type",
        "DIM-05.reader-audit",
    )
    candidate = {
        "schema_version": "task5-quality-result.v3",
        "quality_result_status": "candidate",
        "publication_status": "not_released",
        "run_outcome": "candidate",
        "candidate_tree_sha256": "a" * 64,
        "published_tree_sha256": None,
        "hard_blockers": [],
        "judge_errors": [],
        "rendered_units": 1,
        "bound_units": 1,
        "dimension_verdicts": {"projection": {dimension: ["UNKNOWN", "UNKNOWN"] for dimension in dimensions}},
        "quality_rows": [
            {
                "projection_key": "projection",
                "dimension_id": dimension,
                "verdict": "UNKNOWN",
                "advantage_basis": {"cb_gap_type": "missing_stage"},
            }
            for dimension in dimensions
        ],
        "comparison": {
            "verdict": "released",
            "publication_status": "released",
            "quality_result_status": "released",
            "hard_blockers": [],
            "dimension_verdicts": {"projection": {dimension: ["KD_WIN", "KD_WIN"] for dimension in dimensions}},
        },
    }

    promoted = promote_quality_result(
        candidate,
        candidate_tree_sha256="a" * 64,
        published_tree_sha256="a" * 64,
        candidate_manifest_ref="bundle/_audit/directory-manifest.json",
        candidate_manifest_sha256="b" * 64,
        published_manifest_ref="bundle/_audit/directory-manifest.json",
        published_manifest_sha256="b" * 64,
    )

    assert promoted["publication_status"] == "released"
    assert promoted["published_tree_sha256"] == "a" * 64
    assert all(row["verdict"] == "KD_WIN" for row in promoted["quality_rows"])

    with pytest.raises(ValueError, match="candidate and published tree hashes differ"):
        promote_quality_result(
            candidate,
            candidate_tree_sha256="a" * 64,
            published_tree_sha256="c" * 64,
            candidate_manifest_ref="bundle/_audit/directory-manifest.json",
            candidate_manifest_sha256="b" * 64,
            published_manifest_ref="bundle/_audit/directory-manifest.json",
            published_manifest_sha256="b" * 64,
        )


def test_task5_publisher_quarantines_output_when_finalization_does_not_release(tmp_path: Path) -> None:
    output = tmp_path / "run"
    receipt = commit(
        {"bundle/Home.md": b"# Home\n"},
        output,
        run_id="formal-test",
        task5=True,
        finalizer=lambda _root, _run_id, _owner_nonce: {
            "state": "failed",
            "reason_code": "QUALITY_GATE_FAILED",
        },
    )

    assert receipt["committed"] is False
    assert receipt["state"] == "failed"
    assert not output.exists()
    failure_roots = list(tmp_path.glob("run.failure.formal-test.*"))
    assert len(failure_roots) == 1
    assert (failure_roots[0] / "failure.json").is_file()
    assert not (failure_roots[0] / "bundle").exists()
    assert not (tmp_path / "run.task5.lock").exists()
