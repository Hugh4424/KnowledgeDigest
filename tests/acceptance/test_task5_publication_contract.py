from __future__ import annotations

import subprocess
import sys
import tomllib
import json
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parents[2]


def test_publication_contract_uses_current_reader_tree_not_legacy_audit_paths():
    contract = json.loads((PROJECT_ROOT / "config" / "task5-publication-layout-v2.json").read_text(encoding="utf-8"))
    assert contract["schema_version"] == "task5-publication-layout.v2"
    assert contract["public_root"] == "bundle"
    assert contract["reader_entry"] == "Home.md"
    assert contract["audit_entry"] == "Audit.md"
    assert contract["reader_page_pattern"] == "products/<product>/<page_type>/<readable-title>.md"
    assert contract["page_types"] == ["positioning", "concept", "operation", "diagnosis", "experience"]
    assert {"modules", "boundaries", "knowledge"}.issubset(set(contract["forbidden_reader_path_segments"]))


def test_public_route_ledger_is_a_byte_exact_manifest_projection():
    from knowledge_digest.compiler import _route_ledger_projection, _validate_route_ledger_projection

    route = {
        "query_id": "q-1",
        "question": "question",
        "scene": "scene",
        "route_name": "route",
        "product_key": "goinsight",
        "projection_id": "projection-1",
        "candidate_source_ids": ["source-1"],
        "selected_source_ids": ["source-1"],
        "selected_page_ids": ["answer:q-1:operation"],
        "scores": {"source-1": 1.0},
        "embedding_receipt": None,
        "qwen_payload_sha256": "a" * 64,
        "evidence_bindings": [],
        "home_target_page_identity": "answer:q-1:operation",
        "status": "failed",
        "failure": "fixture failure",
    }
    manifest = {"routes": [route]}
    files = {"_audit/route-ledger.jsonl": _route_ledger_projection(manifest)}

    _validate_route_ledger_projection(files, manifest, label="fixture")

    files["_audit/route-ledger.jsonl"] += b"{}\n"
    with pytest.raises(ValueError, match="route ledger projection does not match manifest.routes"):
        _validate_route_ledger_projection(files, manifest, label="fixture")


def test_public_cli_exit_codes_keep_blocked_and_unavailable_distinct_from_not_released():
    from knowledge_digest.simple_cli import _exit_code

    assert _exit_code("released") == 0
    assert _exit_code("completed") == 0
    assert _exit_code("not_released") == 1
    assert _exit_code("blocked") == 2
    assert _exit_code("unavailable") == 2
    assert _exit_code("failed") == 3
    assert _exit_code("cancelled") == 4


def test_m401_public_gate_does_not_require_reader_positionals(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "knowledge_digest.simple_cli",
            "--gate",
            "M401",
            "--fixture-bundle",
            str(tmp_path / "missing-c3-bundle"),
            "--m401-attempt",
            str(tmp_path / "m401-attempt"),
            "--m401-run-root",
            str(tmp_path / "m401-attempt" / "run-root"),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "M401 fixture bundle is missing" in result.stdout


def test_registered_digest_entrypoint_is_the_thin_reader_cli():
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["scripts"]["digest"] == "knowledge_digest.simple_cli:main"

    result = subprocess.run(
        [sys.executable, "-m", "knowledge_digest.simple_cli", "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "new_dir" in result.stdout
    assert "--no-llm" in result.stdout
    assert "--slice-config" in result.stdout
    assert "--provider-config" in result.stdout
    assert "--gate" in result.stdout
    assert "--m401-packet" in result.stdout
    assert "--m401-r-receipt" in result.stdout
    assert "--workflowhub-successor" in result.stdout

    import_graph = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import knowledge_digest.simple_cli; "
            "import knowledge_digest.compiler; import knowledge_digest.providers; "
            "import knowledge_digest.publisher; "
            "assert 'knowledge_digest.task5_runtime' not in sys.modules; "
            "assert 'knowledge_digest.task5_provider' not in sys.modules",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert import_graph.returncode == 0, import_graph.stderr

    legacy_module = subprocess.run(
        [sys.executable, "-m", "knowledge_digest.task5_runtime", "raw-preflight", "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert legacy_module.returncode == 2
    assert "historical test support" in legacy_module.stderr

    legacy_script = subprocess.run(
        [sys.executable, "scripts/task5_reader_quality.py", "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert legacy_script.returncode == 2
    assert "is retired" in legacy_script.stderr
