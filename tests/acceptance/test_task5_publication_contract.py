from __future__ import annotations

import subprocess
import sys
import tomllib
import json
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parents[2]

_B2_MODULES = (
    "compiler", "companybrain_mapping", "companybrain_snapshot", "full_release",
    "m401_r_adapter", "quality", "quality_compare", "reader_compiler",
    "reader_quality", "task4_reader_quality", "task5_provider", "task5_quality_gate",
    "task5_runtime", "task5_semantic_model",
)
_B2_OLD_TESTS = (
    "tests/acceptance/test_reader_compiler.py",
    "tests/acceptance/test_task2b_body_compiler.py",
    "tests/acceptance/test_task2c_reader_quality.py",
    "tests/acceptance/test_task3_projection.py",
    "tests/acceptance/test_task3_quality_release.py",
    "tests/acceptance/test_task4_companybrain_mapping.py",
    "tests/acceptance/test_task4_full_compiler.py",
    "tests/acceptance/test_task4_full_quality.py",
    "tests/acceptance/test_task4_location_gate.py",
    "tests/acceptance/test_task5_compiler_formal_tree.py",
    "tests/acceptance/test_task5_contract.py",
    "tests/acceptance/test_task5_full_run.py",
    "tests/acceptance/test_task5_m401_r_adapter.py",
    "tests/acceptance/test_task5_projection.py",
    "tests/acceptance/test_task5_provider.py",
    "tests/acceptance/test_task5_quality_compare.py",
    "tests/acceptance/test_task5_quality_gate.py",
    "tests/acceptance/test_task5_source_semantic.py",
    "tests/test_simple_digest.py",
)


def test_publication_contract_uses_current_reader_tree_not_legacy_audit_paths():
    contract = json.loads((PROJECT_ROOT / "config" / "task5-publication-layout-v2.json").read_text(encoding="utf-8"))
    assert contract["schema_version"] == "task5-publication-layout.v2"
    assert contract["public_root"] == "bundle"
    assert contract["reader_entry"] == "Home.md"
    assert contract["audit_entry"] == "Audit.md"
    assert contract["reader_page_pattern"] == "products/<product>/<page_type>/<readable-title>.md"
    assert contract["page_types"] == ["positioning", "concept", "operation", "diagnosis", "experience"]
    assert {"modules", "boundaries", "knowledge"}.issubset(set(contract["forbidden_reader_path_segments"]))


def test_legacy_retirement_guard() -> None:
    remaining_modules = [
        f"src/knowledge_digest/{module}.py"
        for module in _B2_MODULES
        if (PROJECT_ROOT / "src" / "knowledge_digest" / f"{module}.py").exists()
    ]
    remaining_tests = [path for path in _B2_OLD_TESTS if (PROJECT_ROOT / path).exists()]
    assert not remaining_modules + remaining_tests, "B2 legacy retirement guard: " + ", ".join(remaining_modules + remaining_tests)


def test_public_cli_exit_codes_keep_blocked_and_unavailable_distinct_from_not_released():
    from knowledge_digest.simple_cli import _exit_code

    assert _exit_code("released") == 0
    assert _exit_code("completed") == 0
    assert _exit_code("not_released") == 1
    assert _exit_code("blocked") == 2
    assert _exit_code("unavailable") == 2
    assert _exit_code("failed") == 3
    assert _exit_code("cancelled") == 4


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
    assert "--manifest" in result.stdout
    assert "--no-llm" not in result.stdout
    assert "--slice-config" not in result.stdout
    assert "--provider-config" not in result.stdout
    assert "--gate" not in result.stdout
    assert "--m401-packet" not in result.stdout
    assert "--m401-r-receipt" not in result.stdout
    assert "--workflowhub-successor" not in result.stdout

    import_graph = subprocess.run(
        [
            sys.executable,
            "-c",
            "import knowledge_digest.simple_cli; "
            "import knowledge_digest.semantic_compiler; "
            "import knowledge_digest.semantic_navigation; "
            "import knowledge_digest.kb_accept; import knowledge_digest.kb_publish",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert import_graph.returncode == 0, import_graph.stderr
