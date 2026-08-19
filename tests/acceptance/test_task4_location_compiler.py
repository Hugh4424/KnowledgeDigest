from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from knowledge_digest.task4_location_pilot import compile_location_candidate


CONFIG_PATH = Path(__file__).parents[2] / "config" / "task4-location-pilot.v1.json"


def _fixture_config(tmp_path: Path) -> tuple[Path, Path]:
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for entry in config["required_sources"]:
        path = raw_root / entry["source_uri"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {entry['title']}\n\n事实：{entry['title']}。\n", encoding="utf-8")
        entry["line_count"] = len(path.read_text(encoding="utf-8").splitlines())
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    for entry in config["excluded_sources"]:
        path = raw_root / entry["source_uri"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# excluded {entry['source_uri']}\n", encoding="utf-8")
        entry["line_count"] = len(path.read_text(encoding="utf-8").splitlines())
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    for claim in config["claims"]:
        claim["line_start"] = 1
        claim["line_end"] = 3
        claim["text"] = claim["text"]
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return raw_root, config_path


def _valid_provider(request: dict[str, object]) -> dict[str, object]:
    claims = {str(row["claim_id"]): row for row in request["claims"]}  # type: ignore[index]
    sections = []
    for section in request["sections"]:  # type: ignore[index]
        sections.append(
            {
                "section_id": section["section_id"],
                "layer": section["layer"],
                "heading": section["heading"],
                "claim_ids": list(section["claim_ids"]),
                "bullets": [str(claims[str(claim_id)]["text"]) for claim_id in section["claim_ids"]],
            }
        )
    return {"schema_version": "task4-location-provider.v1", "sections": sections, "fidelity_only": False}


def test_manifest_freezes_required_sources(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    result = compile_location_candidate(raw_root, tmp_path / "candidate", config_path=config_path)

    assert result["status"] == "completed"
    manifest = json.loads((tmp_path / "candidate" / "audit" / "source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_id"] == "goinsight-location-pilot-20260817-v1"
    assert [row["source_uri"] for row in manifest["required_sources"]] == [
        "GoInsight/数据分析.md",
        "GoInsight/位置字段筛选.md",
        "GoInsight/设备位置历史数据集.md",
    ]


def test_canonical_page_uses_stable_path(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    result = compile_location_candidate(raw_root, tmp_path / "candidate", config_path=config_path)

    assert result["canonical_page"] == "products/GoInsight/字段与筛选/位置字段筛选.md"
    page = tmp_path / "candidate" / result["canonical_page"]
    assert page.is_file()
    content = page.read_text(encoding="utf-8")
    assert "cluster-" not in content
    assert "draft-" not in content
    assert "## 先看：怎么用" in content
    assert "## 再看：规则和边界" in content


def test_related_topics_are_reachable_from_route(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    compile_location_candidate(raw_root, tmp_path / "candidate", config_path=config_path)

    home = (tmp_path / "candidate" / "Home.md").read_text(encoding="utf-8")
    index = (tmp_path / "candidate" / "products/GoInsight/字段与筛选/index.md").read_text(encoding="utf-8")
    assert "products/GoInsight/index.md" in home
    assert "位置字段筛选.md" in index
    assert "../数据分析.md" in index
    assert "../设备位置历史数据集.md" in index


def test_reader_projection_hides_machine_identity_fields(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    output = tmp_path / "candidate"
    result = compile_location_candidate(raw_root, output, config_path=config_path)

    source = (output / "sources/GoInsight/位置字段筛选.md").read_text(encoding="utf-8")
    page = (output / result["canonical_page"]).read_text(encoding="utf-8")
    assert "source_id" not in source
    assert "content_hash" not in source
    assert "lines:" not in source
    assert "verified content hash" not in page
    assert "source_id" not in page


def test_home_route_resolves_to_one_canonical_page(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    output = tmp_path / "candidate"
    result = compile_location_candidate(raw_root, output, config_path=config_path)

    current = output / "Home.md"
    route = ["Home.md"]
    for relative_link in ("products/GoInsight/index.md", "字段与筛选/index.md", "位置字段筛选.md"):
        current = current.parent / relative_link
        route.append(current.relative_to(output).as_posix())
        assert current.is_file(), current
    assert route == [
        "Home.md",
        "products/GoInsight/index.md",
        "products/GoInsight/字段与筛选/index.md",
        result["canonical_page"],
    ]
    assert len(
        [path for path in output.rglob("位置字段筛选.md") if not path.relative_to(output).as_posix().startswith("sources/")]
    ) == 1


def test_canonical_identity_does_not_depend_on_input_order(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    first_config = json.loads(config_path.read_text(encoding="utf-8"))
    second_config = json.loads(config_path.read_text(encoding="utf-8"))
    second_config["required_sources"] = list(reversed(second_config["required_sources"]))
    second_config["excluded_sources"] = list(reversed(second_config["excluded_sources"]))
    second_config["claims"] = list(reversed(second_config["claims"]))
    second_config["sections"] = list(reversed(second_config["sections"]))
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first_path.write_text(json.dumps(first_config, ensure_ascii=False), encoding="utf-8")
    second_path.write_text(json.dumps(second_config, ensure_ascii=False), encoding="utf-8")

    first = compile_location_candidate(raw_root, tmp_path / "first", config_path=first_path)
    second = compile_location_candidate(raw_root, tmp_path / "second", config_path=second_path)

    assert first["canonical_page"] == second["canonical_page"]
    assert first["canonical_page_hash"] != ""
    assert second["canonical_page_hash"] != ""


def test_manifest_drift_is_failed_and_not_reader(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    (raw_root / "GoInsight/位置字段筛选.md").write_text("changed\n", encoding="utf-8")

    result = compile_location_candidate(raw_root, tmp_path / "candidate", config_path=config_path)

    assert result["status"] == "failed"
    assert result["failure_code"] == "manifest_drift"
    assert not (tmp_path / "candidate" / "Home.md").exists()
    run = json.loads((tmp_path / "candidate/audit/compilation-run.json").read_text(encoding="utf-8"))
    assert run["delivery_status"] == "not_released"
    assert run["reader_inclusion"] is False


def test_added_primary_source_requires_a_new_manifest(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    extra = dict(config["required_sources"][0])
    extra["source_uri"] = "GoInsight/extra.md"
    config["required_sources"].append(extra)
    config["required_source_count"] = 4
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    result = compile_location_candidate(raw_root, tmp_path / "candidate", config_path=config_path)

    assert result["status"] == "failed"
    assert result["failure_code"] == "manifest_drift"
    assert result["candidate_status"] == "not_released"


def test_compile_does_not_overwrite_an_existing_candidate(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    output = tmp_path / "candidate"
    first = compile_location_candidate(raw_root, output, config_path=config_path)
    page = output / first["canonical_page"]
    before = page.read_bytes()

    second = compile_location_candidate(raw_root, output, config_path=config_path)

    assert second["failure_code"] == "output_exists"
    assert page.read_bytes() == before


def test_claim_evidence_has_unique_anchor_and_shared_catalog(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    output = tmp_path / "candidate"
    result = compile_location_candidate(raw_root, output, config_path=config_path, provider=_valid_provider)

    assert result["status"] == "completed"
    record = json.loads((output / "audit/claim-evidence.json").read_text(encoding="utf-8"))
    claims = record["claims"]
    assert len(claims) == len({claim["claim_id"] for claim in claims})
    assert all(claim["validation_status"] == "verified" for claim in claims)
    assert all(claim["fragment_locator"].startswith("lines:") for claim in claims)
    assert all(len(claim["content_hash"]) == 64 for claim in claims)
    assert all(len(claim["claim_fingerprint"]) == 64 for claim in claims)
    page = (output / result["canonical_page"]).read_text(encoding="utf-8")
    assert "Inside" in page and "Outside" in page
    assert "数据集详情页和全局筛选卡片" in page
    assert "raw://" not in page
    assert "provider response" not in page


def test_invalid_provider_json_is_audit_only_fallback(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)

    result = compile_location_candidate(
        raw_root,
        tmp_path / "candidate",
        config_path=config_path,
        provider=lambda _request: "not-json",
    )

    assert result["status"] == "degraded"
    assert result["failure_code"] == "provider_schema"
    assert result["reader_eligible"] is False
    assert not (tmp_path / "candidate/Home.md").exists()
    run = json.loads((tmp_path / "candidate/audit/compilation-run.json").read_text(encoding="utf-8"))
    assert run["fallback_mode"] == "audit-only"
    assert run["delivery_status"] == "not_released"


def test_provider_unknown_claim_is_degraded(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)

    def bad_provider(request: dict[str, object]) -> dict[str, object]:
        response = _valid_provider(request)
        response["sections"][0]["claim_ids"].append("UNKNOWN")  # type: ignore[index]
        response["sections"][0]["bullets"].append("unsupported")  # type: ignore[index]
        return response

    result = compile_location_candidate(raw_root, tmp_path / "candidate", config_path=config_path, provider=bad_provider)

    assert result["status"] == "degraded"
    assert result["failure_code"] == "unknown_claim"
    assert not (tmp_path / "candidate/products").exists()


def test_degraded_fallback_fidelity_only_response_cannot_enter_reader(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)

    def fidelity_only(_request: dict[str, object]) -> dict[str, object]:
        return {"schema_version": "task4-location-provider.v1", "sections": [], "fidelity_only": True}

    result = compile_location_candidate(raw_root, tmp_path / "candidate", config_path=config_path, provider=fidelity_only)

    assert result["status"] == "degraded"
    assert result["failure_code"] == "fidelity_only"
    assert not (tmp_path / "candidate/Home.md").exists()


def test_missing_claim_anchor_is_degraded(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["claims"][0]["line_start"] = 99
    config["claims"][0]["line_end"] = 99
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    result = compile_location_candidate(raw_root, tmp_path / "candidate", config_path=config_path)

    assert result["status"] == "degraded"
    assert result["failure_code"] == "claim_anchor"
    assert not (tmp_path / "candidate/Home.md").exists()


def test_manifest_drift_after_freeze_stops_before_write(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)

    def mutating_provider(_request: dict[str, object]) -> dict[str, object]:
        path = raw_root / "GoInsight/数据分析.md"
        path.write_text(path.read_text(encoding="utf-8") + "漂移\n", encoding="utf-8")
        return _valid_provider(_request)

    result = compile_location_candidate(raw_root, tmp_path / "candidate", config_path=config_path, provider=mutating_provider)

    assert result["status"] == "failed"
    assert result["failure_code"] == "manifest_drift"
    assert not (tmp_path / "candidate/Home.md").exists()


def test_claim_duplicate_source_redirects_to_one_canonical_page(tmp_path: Path) -> None:
    raw_root, config_path = _fixture_config(tmp_path)
    duplicate_path = raw_root / "GoInsight/位置字段筛选-duplicate.md"
    shutil.copyfile(raw_root / "GoInsight/位置字段筛选.md", duplicate_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["duplicate_sources"] = [
        {
            "source_uri": "GoInsight/位置字段筛选-duplicate.md",
            "canonical_source_uri": "GoInsight/位置字段筛选.md",
            "line_count": len(duplicate_path.read_text(encoding="utf-8").splitlines()),
            "sha256": hashlib.sha256(duplicate_path.read_bytes()).hexdigest(),
        }
    ]
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    result = compile_location_candidate(raw_root, tmp_path / "candidate", config_path=config_path)

    assert result["status"] == "completed"
    manifest = json.loads((tmp_path / "candidate/audit/source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["duplicate_sources"][0]["status"] == "duplicate"
    assert manifest["duplicate_sources"][0]["redirect_target_path"] == result["canonical_page"]
    assert not (tmp_path / "candidate/products/GoInsight/字段与筛选/位置字段筛选-duplicate.md").exists()
