"""Task9 K3 freeze and acceptance preflight behavior."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = PROJECT_ROOT / "tests"
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))


def _write_file(root: Path, relative: str, content: str | bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)


def _make_freeze_sources(root: Path, *, input_count: int = 89) -> tuple[Path, Path, Path]:
    input_source = root / "input-source"
    release4_source = root / "release4-source"
    comparison_source = root / "comparison-source"
    for index in range(input_count):
        _write_file(input_source, f"space/module-{index // 10:02d}/source-{index:03d}.md", f"source {index}\n")
    _write_file(input_source, ".DS_Store", b"finder metadata")
    _write_file(input_source, "space/.hidden.md", "hidden input\n")

    _write_file(release4_source, "Home.md", "# release4\n")
    _write_file(release4_source, "products/acme/page.md", "release4 page\n")
    _write_file(release4_source, ".DS_Store", b"finder metadata")

    _write_file(comparison_source, "Home.md", "# comparison\n")
    _write_file(comparison_source, "products/acme/page.md", "comparison page\n")
    _write_file(comparison_source, ".DS_Store", b"finder metadata")
    _write_file(comparison_source, "products/.draft.md", "hidden comparison\n")
    _write_file(comparison_source, "_gbrain/pages/generated.md", "generated mirror\n")
    return input_source, release4_source, comparison_source


def test_freeze_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    freeze = getattr(module, "freeze", None)
    assert callable(freeze), "knowledge_digest.kb_accept.freeze is not implemented"

    input_source, release4_source, comparison_source = _make_freeze_sources(tmp_path / "sources")
    freeze_root = tmp_path / "freeze"
    result = freeze(input_source, release4_source, comparison_source, freeze_root)

    assert result["status"] == "frozen"
    frozen_id = result["frozen_id"]
    assert isinstance(frozen_id, str) and len(frozen_id) == 64
    frozen_dir = freeze_root / frozen_id
    manifest_path = frozen_dir / "manifest.json"
    assert manifest_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["frozen_id"] == frozen_id
    assert manifest["schema_version"] == "task9-freeze-manifest.v1"
    assert manifest["exclusions"]["skip_dotfiles"] is True
    assert manifest["exclusions"]["skip_gbrain"] is True
    assert set(manifest["snapshots"]) == {"input", "release4", "comparison"}

    input_snapshot = frozen_dir / manifest["snapshots"]["input"]["root"]
    release4_snapshot = frozen_dir / manifest["snapshots"]["release4"]["root"]
    comparison_snapshot = frozen_dir / manifest["snapshots"]["comparison"]["root"]
    assert input_snapshot.is_dir()
    assert release4_snapshot.is_dir()
    assert comparison_snapshot.is_dir()
    assert manifest["snapshots"]["input"]["file_count"] == 89
    assert len(manifest["snapshots"]["input"]["files"]) == 89
    assert all(row["path"].endswith(".md") for row in manifest["snapshots"]["input"]["files"])
    assert all(
        ".DS_Store" not in row["path"] and not row["path"].startswith("_gbrain/")
        for snapshot in manifest["snapshots"].values()
        for row in snapshot["files"]
    )
    assert not any(path.name == ".DS_Store" for path in frozen_dir.rglob("*"))
    assert not (comparison_snapshot / "_gbrain").exists()

    for snapshot in manifest["snapshots"].values():
        for row in snapshot["files"]:
            copied = frozen_dir / snapshot["root"] / row["path"]
            assert copied.is_file()
            assert hashlib.sha256(copied.read_bytes()).hexdigest() == row["sha256"]

    original = (input_source / "space/module-00/source-000.md").read_bytes()
    (input_source / "space/module-00/source-000.md").write_bytes(b"changed after freeze\n")
    assert (input_snapshot / "space/module-00/source-000.md").read_bytes() == original
    (input_source / "space/module-00/source-000.md").write_bytes(original)

    second_root = tmp_path / "freeze-again"
    second = freeze(input_source, release4_source, comparison_source, second_root)
    assert second["frozen_id"] == frozen_id
    assert json.loads((second_root / frozen_id / "manifest.json").read_text(encoding="utf-8"))["frozen_id"] == frozen_id

    too_few_source, release4_again, comparison_again = _make_freeze_sources(
        tmp_path / "too-few", input_count=88
    )
    with pytest.raises(ValueError):
        freeze(too_few_source, release4_again, comparison_again, tmp_path / "invalid-freeze")


def _assert_blocked_without_conclusions(result: dict[str, object]) -> None:
    assert result["status"] == "blocked"
    assert result["results"] == []
    assert result["question_results"] == []
    assert result["conclusions"] == []


def _make_current_kb(root: Path) -> Path:
    kb = root / "target-kb"
    version = root / ".target-kb.kd" / "versions" / "20260916-120000-001"
    version.mkdir(parents=True)
    _write_file(version, "Home.md", "# target\n")
    kb.mkdir()
    (kb / "current").symlink_to("../.target-kb.kd/versions/20260916-120000-001")
    return kb


def test_preflight_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    freeze = getattr(module, "freeze", None)
    preflight = getattr(module, "preflight", None)
    accept = getattr(module, "accept", None)
    assert callable(freeze), "knowledge_digest.kb_accept.freeze is not implemented"
    assert callable(preflight), "knowledge_digest.kb_accept.preflight is not implemented"
    assert callable(accept), "knowledge_digest.kb_accept.accept is not implemented"

    input_source, release4_source, comparison_source = _make_freeze_sources(tmp_path / "sources")
    frozen = freeze(input_source, release4_source, comparison_source, tmp_path / "freeze")
    missing_snapshot = freeze(input_source, release4_source, comparison_source, tmp_path / "freeze-missing")
    accepted_snapshot = freeze(input_source, release4_source, comparison_source, tmp_path / "freeze-accept")
    frozen_id = frozen["frozen_id"]

    intact = preflight(frozen_id, tmp_path / "freeze")
    assert intact["status"] == "ready"
    assert intact["results"] == []
    assert set(intact["tree_hashes"]) == {"input", "release4", "comparison"}

    tampered_path = tmp_path / "freeze" / frozen_id / "comparison" / "products/acme/page.md"
    tampered_path.write_text("tampered\n", encoding="utf-8")
    tampered = preflight(frozen_id, tmp_path / "freeze")
    _assert_blocked_without_conclusions(tampered)
    assert any("hash" in reason or "manifest" in reason or "tree" in reason for reason in tampered["reasons"])

    missing_dir = tmp_path / "freeze-missing" / missing_snapshot["frozen_id"] / "input"
    missing_dir.rename(missing_dir.with_name("input-removed"))
    missing = preflight(missing_snapshot["frozen_id"], tmp_path / "freeze-missing")
    _assert_blocked_without_conclusions(missing)
    assert any("missing" in reason or "whitelist" in reason for reason in missing["reasons"])

    target_kb = _make_current_kb(tmp_path)
    real_tree_hash = module.kb_tree_hash
    tree_hash_calls = 0

    def counting_tree_hash(root: Path) -> str:
        nonlocal tree_hash_calls
        tree_hash_calls += 1
        return real_tree_hash(root)

    monkeypatch.setattr(module, "kb_tree_hash", counting_tree_hash)
    live_comparison = comparison_source.resolve()
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text

    def reject_live_bytes(path: Path) -> bytes:
        resolved = path.resolve()
        if resolved == live_comparison or live_comparison in resolved.parents:
            raise AssertionError("preflight read the live comparison source")
        return original_read_bytes(path)

    def reject_live_text(path: Path, *args: object, **kwargs: object) -> str:
        resolved = path.resolve()
        if resolved == live_comparison or live_comparison in resolved.parents:
            raise AssertionError("preflight read the live comparison source")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", reject_live_bytes)
    monkeypatch.setattr(Path, "read_text", reject_live_text)
    accepted = accept(
        accepted_snapshot["frozen_id"],
        target_kb,
        freeze_root=tmp_path / "freeze-accept",
    )
    assert accepted["status"] == "not_evaluated"
    assert accepted["acceptance_status"] == "not_evaluated"
    assert accepted["reason_code"] == "acceptance_not_evaluated"
    assert accepted["target_kb_tree_hash"]
    assert accepted["results"] == []
    # preflight hashes the three frozen roots, then accept revalidates those
    # roots after preflight before evaluating the target.
    assert tree_hash_calls == 7


def _source_and_page(
    path: str,
    source_uri: str,
    source_text: str,
    *,
    title: str | None = None,
    fingerprint: str | None = None,
    anchor: str | None = None,
) -> tuple[dict[str, object], dict[str, str]]:
    digest = fingerprint or hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    page: dict[str, object] = {
        "page_path": path,
        "title": title or Path(path).stem,
        "text": f"# {title or Path(path).stem}\n\nAnswer from the frozen source.\n",
        "evidence": [
            {
                "page_path": path,
                "page_anchor": anchor or "reference-1",
                "source_uri": source_uri,
                "content_hash": digest,
                "line_start": 1,
                "line_end": len(source_text.splitlines()),
            }
        ],
    }
    if anchor:
        page["text"] = f'<a id="{anchor}"></a>\n' + str(page["text"])
    return page, {source_uri: source_text}


def test_question_generator() -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    generate_questions = getattr(module, "generate_questions", None)
    assert callable(generate_questions), "knowledge_digest.kb_accept.generate_questions is not implemented"

    pages = [
        {"page_path": "products/acme/settings/b.md", "title": "Settings B", "text": "# Settings B\nB answer.\n"},
        {"page_path": "products/acme/settings/a.md", "title": "Settings A", "text": "# Settings A\nA answer.\n"},
        {"page_path": "products/acme/only.md", "text": "# Only\nOne answer.\n"},
    ]
    first = generate_questions(pages)
    second = generate_questions(list(reversed(pages)))

    assert first["question_set_sha256"] == second["question_set_sha256"]
    assert [row["page_path"] for row in first["questions"]] == [
        "products/acme/only.md",
        "products/acme/settings/a.md",
        "products/acme/settings/b.md",
    ]
    assert [row["template"] for row in first["questions"]] == ["{} 是什么", "{} 是什么", "{} 怎么配置"]
    assert "products/acme" in first["degraded_modules"]

    invalid = module._question_list([])
    assert "question_set_empty" in invalid[1]


def test_judge_four_results() -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    judge = getattr(module, "judge", None)
    assert callable(judge), "knowledge_digest.kb_accept.judge is not implemented"

    path = "products/acme/settings/page.md"
    page, sources = _source_and_page(path, "raw/settings.md", "setting one\nsetting two\n", anchor="reference-1")
    question = {
        "question_id": "q-good",
        "prompt": "Settings 是什么",
        "page_path": path,
        "module": "products/acme/settings",
        "title": "Settings",
        "page_anchor": "reference-1",
    }
    frozen = {
        "input": sources,
        "snapshots": {
            "release4": {path: {"page_path": path, "text": "release4 settings\n"}},
            "comparison": {path: {"text": "old settings\n"}},
        },
    }
    good = judge(question, {path: page}, frozen)
    assert (good["answer_hit"], good["location_valid"], good["source_correct"], good["comparison_uncovered"]) == (True, True, True, False)
    assert good["snapshot_matches"] == {"release4": True, "comparison": True}

    module_fallback_question = {
        "question_id": "q-module-fallback",
        "prompt": "Target 是什么",
        "page_path": "products/acme/settings/new-page.md",
        "module": "products/acme/settings",
        "title": "Target",
        "page_anchor": "reference-1",
    }
    module_fallback_page, module_fallback_sources = _source_and_page(
        module_fallback_question["page_path"],
        "raw/new-page.md",
        "new answer\n",
        title="Target",
        anchor="reference-1",
    )
    module_fallback = judge(
        module_fallback_question,
        {module_fallback_question["page_path"]: module_fallback_page},
        {
            "input": module_fallback_sources,
            "comparison_pages": {
                "products/acme/settings/other-page.md": {
                    "title": "Other",
                    "text": "other answer\n",
                },
            },
        },
    )
    assert module_fallback["comparison_uncovered"] is True

    partial_hash = dict(page)
    partial_hash["evidence"] = [dict(
        page["evidence"][0],
        content_hash=hashlib.sha256(b"setting one\nsetting two\n").hexdigest(),
        line_start=1,
        line_end=1,
    )]
    partial_hash_result = judge(question, {path: partial_hash}, frozen)
    assert partial_hash_result["location_valid"] is True
    assert partial_hash_result["source_correct"] is False
    assert partial_hash_result["answer_hit"] is False

    wrong = dict(page)
    wrong["evidence"] = [dict(page["evidence"][0], content_hash="0" * 64)]
    wrong_result = judge(question, {path: wrong}, frozen)
    assert wrong_result["answer_hit"] is False
    assert wrong_result["source_correct"] is False
    assert wrong_result["hard_failure"] is True
    assert wrong_result["failure_reason"] == "source_incorrect"

    wrong_location = dict(page)
    wrong_location["evidence"] = [dict(page["evidence"][0], page_anchor="wrong-anchor")]
    wrong_location_result = judge(question, {path: wrong_location}, frozen)
    assert wrong_location_result["answer_hit"] is False
    assert wrong_location_result["location_valid"] is False
    assert wrong_location_result["source_correct"] is False

    valid_source_missing_anchor = dict(page)
    valid_source_missing_anchor["text"] = valid_source_missing_anchor["text"].replace(
        '<a id="reference-1"></a>\n', ""
    )
    soft_location_miss = judge(question, {path: valid_source_missing_anchor}, frozen)
    assert soft_location_miss["answer_hit"] is False
    assert soft_location_miss["location_valid"] is False
    assert soft_location_miss["source_correct"] is True
    assert soft_location_miss["hard_failure"] is False

    unscoped_page = dict(page)
    unscoped_page.pop("evidence")
    unscoped_evidence = dict(page["evidence"][0])
    unscoped_evidence.pop("page_path")
    unscoped_result = judge(
        question,
        {"pages": [unscoped_page], "evidence": [unscoped_evidence]},
        frozen,
    )
    assert unscoped_result["answer_hit"] is False
    assert unscoped_result["location_valid"] is False
    assert unscoped_result["source_correct"] is False

    missing = judge(question, {}, frozen)
    assert missing["location_valid"] is False
    assert missing["hard_failure"] is True

    uncovered = judge(question, {path: page}, {"input": sources, "comparison_pages": {}})
    assert uncovered["comparison_uncovered"] is True
    assert uncovered["hard_failure"] is False

    release4_only_path = "products/acme/settings/release4-only.md"
    release4_only_page, release4_only_sources = _source_and_page(
        release4_only_path,
        "raw/release4-only.md",
        "release4-only answer\n",
        anchor="reference-1",
    )
    release4_only_question = {
        "question_id": "q-release4-only",
        "prompt": "Release4 only 是什么",
        "page_path": release4_only_path,
        "page_anchor": "reference-1",
        "source_snapshot": "release4",
    }
    release4_only = judge(
        release4_only_question,
        {release4_only_path: release4_only_page},
        {
            "input": release4_only_sources,
            "snapshots": {"release4": {release4_only_path: release4_only_page}, "comparison": {}},
        },
    )
    assert release4_only["snapshot_matches"] == {"release4": True, "comparison": False}
    assert release4_only["comparison_uncovered"] is True


def test_verdict_summary() -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    summarize = getattr(module, "summarize", None)
    assert callable(summarize), "knowledge_digest.kb_accept.summarize is not implemented"

    correct = [{"answer_hit": True, "source_correct": True, "comparison_uncovered": False, "hard_failure": False} for _ in range(10)]
    uncovered = [{"answer_hit": False, "source_correct": False, "comparison_uncovered": True, "hard_failure": False} for _ in range(18)]
    result = summarize([*correct, *uncovered])
    assert result["status"] == "pass"
    assert result["effective_question_count"] == 10
    assert result["uncovered_question_count"] == 18
    assert result["correct_rate"] == 1.0

    hard = summarize([*correct[:9], {"answer_hit": False, "source_correct": False, "comparison_uncovered": False, "hard_failure": True}])
    assert hard["status"] == "fail"
    assert hard["reason_code"] == "hard_failures"

    no_effective = summarize(uncovered)
    assert no_effective["status"] == "fail"
    assert no_effective["reason_code"] == "no_effective_questions"

    insufficient = summarize(correct[:9])
    assert insufficient["status"] == "blocked"

    soft_miss = dict(correct[0], answer_hit=False, location_valid=False, source_correct=True, hard_failure=False)
    below_threshold = summarize([*correct[:7], soft_miss, soft_miss, soft_miss])
    assert below_threshold["status"] == "fail"
    assert below_threshold["reason_code"] == "answer_or_source_rate_below_threshold"
    assert insufficient["reason_code"] == "insufficient_effective_questions"


def _write_accept_sources(root: Path, *, page_paths: list[str]) -> tuple[Path, Path, Path, dict[str, str]]:
    input_source = root / "input-source"
    release4_source = root / "release4-source"
    comparison_source = root / "comparison-source"
    source_values: dict[str, str] = {}
    for index in range(89 - len(page_paths)):
        _write_file(input_source, f"filler/{index:03d}.md", f"filler {index}\n")
    for index, path in enumerate(page_paths):
        source_uri = f"raw/{index:03d}.md"
        source_text = f"answer {index}\n"
        source_values[source_uri] = source_text
        _write_file(input_source, source_uri, source_text)
        _write_file(release4_source, path, f"# old {index}\n")
        _write_file(comparison_source, path, f"# old {index}\n")
    return input_source, release4_source, comparison_source, source_values


def test_record_binding_replay(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    freeze = module.freeze
    accept = module.accept
    from fixtures.task9_publish import make_batch_with_nav, make_kb
    from knowledge_digest.kb_publish import publish

    page_path = "products/acme/settings/page.md"
    input_source, release4_source, comparison_source, source_values = _write_accept_sources(tmp_path / "sources", page_paths=[page_path])
    batch = make_batch_with_nav(tmp_path / "batch", pages={page_path: "# Settings\nanswer 0\n"})
    digest = source_values["raw/000.md"]
    (batch / "_audit" / "sources.jsonl").write_text(
        json.dumps({"page_path": page_path, "page_anchor": "reference-1", "source_uri": "raw/000.md", "content_hash": hashlib.sha256(digest.encode()).hexdigest(), "line_start": 1, "line_end": 1}) + "\n",
        encoding="utf-8",
    )
    kb = make_kb(tmp_path / "kb")
    published = publish(batch, kb, run_id="accept-publish")
    assert published["status"] == "released"
    frozen = freeze(input_source, release4_source, comparison_source, tmp_path / "freeze")
    question_set = {"questions": [{"question_id": "q-one", "prompt": "Settings 是什么", "page_path": page_path}]}
    first = accept(frozen["frozen_id"], kb, freeze_root=tmp_path / "freeze", question_set=question_set, run_id="accept-one")
    assert first["status"] == "blocked"  # one effective question is below the frozen minimum of ten
    locator_result = accept(tmp_path / "freeze" / frozen["frozen_id"], kb, question_set=question_set, run_id="accept-locator")
    assert locator_result["frozen_id"] == frozen["frozen_id"]
    replayed = accept(frozen["frozen_id"], kb, freeze_root=tmp_path / "freeze", question_set=question_set, replay=first, run_id="accept-replay")
    assert replayed["status"] == first["status"]
    current = (kb / "current").resolve() / page_path
    current.write_text(current.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    changed = accept(frozen["frozen_id"], kb, freeze_root=tmp_path / "freeze", question_set=question_set, replay=first, run_id="accept-changed")
    assert changed["status"] == "blocked"
    assert changed["message"] == "被测对象已变，不可复跑"
    assert changed["conclusions"] == []


def test_discrimination(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    discrimination_check = getattr(module, "discrimination_check", None)
    assert callable(discrimination_check), "knowledge_digest.kb_accept.discrimination_check is not implemented"
    root = tmp_path / "frozen"
    _write_file(root, "input/raw/a.md", "answer\n")
    _write_file(root, "comparison/products/acme/settings/page.md", "old answer\n")
    path = "products/acme/settings/page.md"
    def questions_for(prefix: str, *, anchor: str | None = None) -> list[dict[str, object]]:
        return [
            {"question_id": f"{prefix}-1", "prompt": "q1", "page_path": path, **({"page_anchor": anchor} if anchor else {})},
            {"question_id": f"{prefix}-2", "prompt": "q2", "page_path": path, **({"page_anchor": anchor} if anchor else {})},
        ]

    valid_page, _ = _source_and_page(path, "raw/a.md", "answer\n", anchor="reference-1")
    missing_table_page, _ = _source_and_page(path, "raw/a.md", "answer\n")
    wrong_citation_page = dict(valid_page)
    wrong_citation_page["evidence"] = [dict(valid_page["evidence"][0], content_hash="0" * 64)]
    fixture = {"samples": [
        {
            "sample_id": "missing-table",
            "must_fail": True,
            "questions": questions_for("missing-table", anchor="reference-1"),
            "pages": {path: missing_table_page},
            "expected_failure_reasons": ["location_invalid", "location_invalid"],
        },
        {
            "sample_id": "wrong-citation",
            "must_fail": True,
            "questions": questions_for("wrong-citation"),
            "pages": {path: wrong_citation_page},
            "expected_failure_reasons": ["source_incorrect", "source_incorrect"],
        },
        {
            "sample_id": "orphan-page",
            "must_fail": True,
            "questions": questions_for("orphan-page"),
            "pages": {},
            "expected_failure_reasons": ["answer_missing", "answer_missing"],
        },
        {
            "sample_id": "correct",
            "must_fail": False,
            "questions": questions_for("correct"),
            "pages": {path: valid_page},
        },
    ]}
    result = discrimination_check(root, fixture)
    assert result["status"] == "passed"
    assert len(result["samples"]) == 4
    assert result["fixture_sha256"]

    default_fixture = module._default_discrimination_fixture(root)
    assert any(not sample.get("must_fail", True) for sample in default_fixture["samples"])
    default_result = discrimination_check(root, default_fixture)
    assert default_result["status"] == "passed"

    empty_root = tmp_path / "empty-control"
    _write_file(empty_root, "input/raw/a.md", "")
    _write_file(empty_root, "comparison/products/acme/settings/page.md", "old answer\n")
    empty_fixture = module._default_discrimination_fixture(empty_root)
    assert not any(not sample.get("must_fail", True) for sample in empty_fixture["samples"])
    empty_result = discrimination_check(empty_root, empty_fixture)
    assert empty_result["status"] == "failed"
    assert empty_result["reason_code"] == "discrimination_positive_control_missing"


def test_e2e_aggregate(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    from fixtures.task9_publish import make_batch_with_nav, make_kb
    from knowledge_digest.kb_publish import publish, rollback, kb_tree_hash

    page_paths = [
        f"products/p{index:02d}/module/{letter}.md"
        for index in range(5)
        for letter in ("a", "b")
    ]
    input_source, release4_source, comparison_source, source_values = _write_accept_sources(tmp_path / "e2e-sources", page_paths=page_paths)
    pages = {path: f"# Topic {index}\nanswer {index}\n" for index, path in enumerate(page_paths)}
    first_batch = make_batch_with_nav(tmp_path / "first", pages=pages)
    second_batch = make_batch_with_nav(tmp_path / "second", pages={path: value.replace("answer", "answer v2") for path, value in pages.items()})
    audit_rows = []
    for index, path in enumerate(page_paths):
        uri = f"raw/{index:03d}.md"
        audit_rows.append({"page_path": path, "source_uri": uri, "content_hash": hashlib.sha256(source_values[uri].encode()).hexdigest(), "line_start": 1, "line_end": 1})
    for batch in (first_batch, second_batch):
        (batch / "_audit" / "sources.jsonl").write_text("".join(json.dumps(row) + "\n" for row in audit_rows), encoding="utf-8")
    kb = make_kb(tmp_path / "e2e-kb")
    first = publish(first_batch, kb, run_id="e2e-first")
    second = publish(second_batch, kb, run_id="e2e-second")
    assert first["status"] == second["status"] == "released"
    frozen = module.freeze(input_source, release4_source, comparison_source, tmp_path / "e2e-freeze")
    result = module.accept(frozen["frozen_id"], kb, freeze_root=tmp_path / "e2e-freeze", run_id="e2e-accept")
    assert result["status"] == "pass"
    assert result["verdict"]["effective_question_count"] == 10
    replay = module.accept(frozen["frozen_id"], kb, freeze_root=tmp_path / "e2e-freeze", replay=result, run_id="e2e-replay")
    assert replay["status"] == "pass"
    rolled_back = rollback(kb, run_id="e2e-rollback")
    assert rolled_back["status"] == "rolled_back"
    assert kb_tree_hash((kb / "current").resolve()) == first["new_tree_hash"]


def test_real_k2_prompt_matches_chinese_description_contract(tmp_path: Path) -> None:
    """The public K2 compiler path must ask the provider for validator-safe text."""
    from fixtures.task8_nav import make_batch
    from knowledge_digest.semantic_navigation import build_index, build_mount_tree, compile_batch_navigation, reconcile_pages

    class Cache:
        model_id = "test-model"
        prompt_version = "test-prompt"
        topic_map_version = "test-topic-map"

        def get(self, key: str, *, expected_fingerprint: str | None = None) -> str | None:
            return None

        def set_with_fingerprint(self, key: str, value: str, *, fingerprint: str) -> None:
            return None

    class PromptAwareGateway:
        model_id = "test-model"
        prompt_version = "test-prompt"
        topic_map_version = "test-topic-map"

        def __init__(self) -> None:
            self.prompts: list[str] = []
            self.description_count = 0

        def complete(self, prompt: str) -> str:
            self.prompts.append(prompt)
            if prompt.startswith("task8 home suggestions"):
                return json.dumps(["如何查找页面？", "什么是页面入口？", "怎么核对来源？"], ensure_ascii=False)
            if "中文" not in prompt:
                return "Navigate to the settings page."
            self.description_count += 1
            return f"这页帮助读者完成第{self.description_count}项配置。"

    batch = make_batch(tmp_path / "k2-prompt")
    pages = reconcile_pages(batch)
    index = build_index(build_mount_tree(pages))
    gateway = PromptAwareGateway()
    result = compile_batch_navigation(batch, cache=Cache(), gateway=gateway, query_fixture=None)

    assert result.navigation_status == "generated_ok"
    description_prompts = [prompt for prompt in gateway.prompts if prompt.startswith("task8 description")]
    assert len(description_prompts) == 3
    assert all("中文" in prompt for prompt in description_prompts)


def test_k2_failure_metrics_keep_provider_calls(tmp_path: Path) -> None:
    """A provider rejection must retain calls already made before the failure."""
    from fixtures.task8_nav import make_batch
    from knowledge_digest.semantic_navigation import compile_batch_navigation

    class Cache:
        def get(self, key: str, *, expected_fingerprint: str | None = None) -> str | None:
            return None

        def set_with_fingerprint(self, key: str, value: str, *, fingerprint: str) -> None:
            return None

    class EnglishGateway:
        model_id = "test-model"
        prompt_version = "test-prompt"
        topic_map_version = "test-topic-map"

        def complete(self, prompt: str) -> str:
            return "Navigate to the settings page."

    batch = make_batch(tmp_path / "k2-metrics")
    result = compile_batch_navigation(batch, cache=Cache(), gateway=EnglishGateway(), query_fixture=None)

    assert result.navigation_status == "blocked"
    assert "model-output-invalid:description must contain Chinese text" in result.blocked_reasons
    metrics = json.loads((batch / "_audit" / "run-metrics.json").read_text(encoding="utf-8"))
    assert metrics["task8_navigation"]["provider_calls"] == 1
    assert metrics["task8_navigation"]["actual_provider_calls"] == 1


def test_k2_failure_metrics_keep_provider_tokens_when_validation_rejects(tmp_path: Path) -> None:
    """Provider usage remains attributable when the returned text fails validation."""
    from fixtures.task8_nav import make_batch
    from knowledge_digest.semantic_navigation import compile_batch_navigation

    class Cache:
        def get(self, key: str, *, expected_fingerprint: str | None = None) -> str | None:
            return None

        def set_with_fingerprint(self, key: str, value: str, *, fingerprint: str) -> None:
            return None

    class TokenRejectGateway:
        model_id = "test-model"
        prompt_version = "test-prompt"
        topic_map_version = "test-topic-map"

        def __init__(self) -> None:
            self.last_provider_tokens: int | None = None

        def complete(self, prompt: str) -> str:
            self.last_provider_tokens = 23
            return "Navigate to the settings page."

    batch = make_batch(tmp_path / "k2-token-failure")
    result = compile_batch_navigation(batch, cache=Cache(), gateway=TokenRejectGateway(), query_fixture=None)

    assert result.navigation_status == "blocked"
    metrics = json.loads((batch / "_audit" / "run-metrics.json").read_text(encoding="utf-8"))
    navigation = metrics["task8_navigation"]
    assert navigation["provider_calls"] == 1
    assert navigation["actual_provider_calls"] == 1
    assert navigation["provider_tokens"] == 23
    assert navigation["actual_provider_tokens"] == 23
    assert navigation["provider_token_observations"] == 1


def test_k2_retry_replaces_stale_metric_reasons(tmp_path: Path) -> None:
    """A successful retry must not retain zero-value reasons from a prior failure."""
    from fixtures.task8_nav import make_batch
    from knowledge_digest.semantic_navigation import compile_batch_navigation

    class Cache:
        def get(self, key: str, *, expected_fingerprint: str | None = None) -> str | None:
            return None

        def set_with_fingerprint(self, key: str, value: str, *, fingerprint: str) -> None:
            return None

    class EnglishGateway:
        model_id = "test-model"
        prompt_version = "test-prompt"
        topic_map_version = "test-topic-map"

        def complete(self, prompt: str) -> str:
            return "Navigate to the settings page."

    class GoodGateway:
        model_id = "test-model"
        prompt_version = "test-prompt"
        topic_map_version = "test-topic-map"

        def __init__(self) -> None:
            self.description_count = 0
            self.last_provider_tokens: int | None = None

        def complete(self, prompt: str) -> str:
            if prompt.startswith("task8 home suggestions"):
                self.last_provider_tokens = 7
                return json.dumps(["如何查找页面？", "什么是页面入口？", "怎么核对来源？"], ensure_ascii=False)
            self.description_count += 1
            self.last_provider_tokens = 11
            return f"这页帮助读者完成第{self.description_count}项配置。"

    batch = make_batch(tmp_path / "k2-retry")
    first = compile_batch_navigation(batch, cache=Cache(), gateway=EnglishGateway(), query_fixture=None)
    assert first.navigation_status == "blocked"
    failed_metrics = json.loads((batch / "_audit" / "run-metrics.json").read_text(encoding="utf-8"))
    assert failed_metrics["task8_navigation"]["reasons"]["provider_tokens"] == "provider_usage_unavailable"

    second = compile_batch_navigation(batch, cache=Cache(), gateway=GoodGateway(), query_fixture=None)
    assert second.navigation_status == "generated_ok"
    succeeded_metrics = json.loads((batch / "_audit" / "run-metrics.json").read_text(encoding="utf-8"))
    navigation = succeeded_metrics["task8_navigation"]
    assert navigation["provider_calls"] == 4
    assert navigation["provider_tokens"] == 40
    assert navigation["reasons"] == {}


def test_k2_metrics_include_provider_tokens_and_elapsed_time(tmp_path: Path) -> None:
    """K2 must expose the same cost dimensions that K3 inherits."""
    from fixtures.task8_nav import make_batch
    from knowledge_digest.semantic_navigation import compile_batch_navigation

    class Cache:
        def get(self, key: str, *, expected_fingerprint: str | None = None) -> str | None:
            return None

        def set_with_fingerprint(self, key: str, value: str, *, fingerprint: str) -> None:
            return None

    class TokenGateway:
        model_id = "test-model"
        prompt_version = "test-prompt"
        topic_map_version = "test-topic-map"

        def __init__(self) -> None:
            self.description_count = 0
            self.last_provider_tokens: int | None = None

        def complete(self, prompt: str) -> str:
            if prompt.startswith("task8 home suggestions"):
                self.last_provider_tokens = 7
                return json.dumps(["如何查找页面？", "什么是页面入口？", "怎么核对来源？"], ensure_ascii=False)
            self.description_count += 1
            self.last_provider_tokens = 11
            return f"这页帮助读者完成第{self.description_count}项配置。"

    batch = make_batch(tmp_path / "k2-cost")
    gateway = TokenGateway()
    result = compile_batch_navigation(batch, cache=Cache(), gateway=gateway, query_fixture=None)

    assert result.navigation_status == "generated_ok"
    metrics = json.loads((batch / "_audit" / "run-metrics.json").read_text(encoding="utf-8"))
    navigation = metrics["task8_navigation"]
    assert navigation["provider_calls"] == 4
    assert navigation["actual_provider_calls"] == 4
    assert navigation["provider_tokens"] == 40
    assert navigation["actual_provider_tokens"] == 40
    assert navigation["provider_token_observations"] == 4
    assert isinstance(navigation["elapsed_ms"], int)


def test_accept_generates_questions_from_published_target_pages(tmp_path: Path) -> None:
    """Default questions must target the K1 pages that acceptance actually evaluates."""
    module = importlib.import_module("knowledge_digest.kb_accept")
    from fixtures.task9_publish import make_batch_with_nav, make_kb
    from knowledge_digest.kb_publish import publish

    input_source, release4_source, comparison_source = _make_freeze_sources(tmp_path / "sources")
    # The release4 wrapper reproduces the real artifact shape.  Keep one
    # ordinary comparison product so the built-in discrimination control has
    # a deterministic page to bind.
    for source in (release4_source,):
        products = source / "products"
        bundle = source / "bundle"
        bundle.mkdir()
        products.rename(bundle / "products")

    page_paths = [
        f"products/product-{index:02d}/module/{letter}.md"
        for index in range(5)
        for letter in ("a", "b")
    ]
    batch = make_batch_with_nav(
        tmp_path / "batch",
        pages={path: f"# Topic {index}\nanswer {index}\n" for index, path in enumerate(page_paths)},
    )
    kb = make_kb(tmp_path / "kb")
    published = publish(batch, kb, run_id="target-question-source")
    assert published["status"] == "released"

    frozen = module.freeze(input_source, release4_source, comparison_source, tmp_path / "freeze")
    result = module.accept(frozen["frozen_id"], kb, freeze_root=tmp_path / "freeze", run_id="target-question-source-accept")

    questions = result.get("question_set", {}).get("questions", [])
    assert len(questions) == 10
    assert {row.get("source_snapshot") for row in questions} == {"target"}
    assert "question_set_empty" not in result.get("reasons", [])


def test_mapped_question_generator_is_deterministic_and_caps_logical_modules() -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    generate = getattr(module, "generate_mapped_questions", None)
    assert callable(generate), "knowledge_digest.kb_accept.generate_mapped_questions is not implemented"

    pages = [
        {
            "page_path": "products/acme/_general/a.md",
            "text": "# A\nanswer a\n",
            "evidence": [{"source_block_id": "source-a-b0001", "source_path": "raw/a.md"}],
        },
        {
            "page_path": "products/acme/_general/b.md",
            "text": "# B\nanswer b\n",
            "evidence": [{"source_block_id": "source-b-b0001", "source_path": "raw/b.md"}],
        },
        {
            "page_path": "products/acme/_general/c.md",
            "text": "# C\nanswer c\n",
            "evidence": [{"source_block_id": "source-c-b0001", "source_path": "raw/c.md"}],
        },
    ]
    mapping = {
        "schema_version": "task9-comparison-mapping.v1",
        "mapping_id": "fixture-map",
        "entries": [
            {
                "source_id": "source-c",
                "source_uri": "raw/c.md",
                "source_sha256": "c" * 64,
                "comparison_page": "Products/acme/one/c.md",
                "comparison_sha256": "1" * 64,
                "logical_module": "Products/acme/one",
            },
            {
                "source_id": "source-a",
                "source_uri": "raw/a.md",
                "source_sha256": "a" * 64,
                "comparison_page": "Products/acme/one/a.md",
                "comparison_sha256": "2" * 64,
                "logical_module": "Products/acme/one",
            },
            {
                "source_id": "source-b",
                "source_uri": "raw/b.md",
                "source_sha256": "b" * 64,
                "comparison_page": "Products/acme/one/b.md",
                "comparison_sha256": "3" * 64,
                "logical_module": "Products/acme/one",
            },
        ],
    }
    first = generate(pages, mapping)
    second = generate(list(reversed(pages)), mapping)
    assert first["question_set_sha256"] == second["question_set_sha256"]
    assert len(first["questions"]) == 2
    assert {row["page_path"] for row in first["questions"]} == {
        "products/acme/_general/a.md",
        "products/acme/_general/b.md",
    }
    assert {row["module"] for row in first["questions"]} == {"Products/acme/one"}
    assert first["degraded_modules"] == []


def test_accept_validates_and_binds_comparison_mapping(tmp_path: Path) -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    from fixtures.task9_publish import make_batch_with_nav, make_kb
    from knowledge_digest.kb_publish import publish

    page_path = "products/acme/settings/page.md"
    input_source, release4_source, comparison_source, source_values = _write_accept_sources(
        tmp_path / "mapping-sources", page_paths=[page_path]
    )
    batch = make_batch_with_nav(
        tmp_path / "mapping-batch",
        pages={page_path: "# Settings\nanswer 0\n"},
    )
    source_text = source_values["raw/000.md"]
    source_hash = hashlib.sha256(source_text.encode()).hexdigest()
    (batch / "_audit" / "sources.jsonl").write_text(
        json.dumps({
            "page_path": page_path,
            "source_block_id": "source-one-b0001",
            "source_path": "raw/000.md",
            "content_hash": source_hash,
            "line_start": 1,
            "line_end": 1,
        }) + "\n",
        encoding="utf-8",
    )
    target = make_kb(tmp_path / "mapping-target")
    assert publish(batch, target, run_id="mapping-publish")["status"] == "released"
    freeze_root = tmp_path / "mapping-freeze"
    frozen = module.freeze(input_source, release4_source, comparison_source, freeze_root)
    manifest = json.loads(
        (freeze_root / frozen["frozen_id"] / "manifest.json").read_text(encoding="utf-8")
    )
    input_sha = next(row["sha256"] for row in manifest["snapshots"]["input"]["files"] if row["path"] == "raw/000.md")
    comparison_sha = next(
        row["sha256"]
        for row in manifest["snapshots"]["comparison"]["files"]
        if row["path"] == page_path
    )
    mapping = {
        "schema_version": "task9-comparison-mapping.v1",
        "mapping_id": "fixture-map",
        "source_manifest_sha256": manifest["manifest_sha256"],
        "source_snapshot_tree_hash": manifest["snapshots"]["input"]["tree_hash"],
        "comparison_frozen_id": frozen["frozen_id"],
        "comparison_tree_hash": manifest["snapshots"]["comparison"]["tree_hash"],
        "entry_count": 1,
        "entries": [{
            "source_id": "source-one",
            "source_uri": "raw/000.md",
            "source_sha256": input_sha,
            "comparison_page": page_path,
            "comparison_sha256": comparison_sha,
            "logical_module": "products/acme/settings",
        }],
    }
    result = module.accept(
        frozen["frozen_id"],
        target,
        freeze_root=freeze_root,
        comparison_mapping=mapping,
        run_id="mapping-accept",
    )
    assert result["status"] == "blocked"
    assert result["reason_code"] == "insufficient_effective_questions"
    assert len(result["question_set"]["questions"]) == 1
    assert result["comparison_mapping"]["mapping_id"] == "fixture-map"
    assert result["comparison_mapping"]["sha256"]
    assert result["comparison_mapping_sha256"] == result["comparison_mapping"]["sha256"]
    assert result["question_set"]["questions"][0]["comparison_page"] == page_path

    replayed = module.accept(
        frozen["frozen_id"],
        target,
        freeze_root=freeze_root,
        comparison_mapping=mapping,
        replay=result,
        run_id="mapping-replay",
    )
    assert replayed["status"] == result["status"]
    assert replayed["question_results"] == result["question_results"]

    invalid = dict(mapping, comparison_tree_hash="0" * 64)
    blocked = module.accept(
        frozen["frozen_id"],
        target,
        freeze_root=freeze_root,
        comparison_mapping=invalid,
        run_id="mapping-invalid",
    )
    assert blocked["status"] == "blocked"
    assert blocked["reason_code"] == "comparison_mapping_blocked"
    assert blocked["results"] == []


def test_accept_rejects_overrepresented_supplied_questions(tmp_path: Path) -> None:
    """A caller cannot turn one page into an artificial acceptance sample."""
    module = importlib.import_module("knowledge_digest.kb_accept")
    from fixtures.task9_publish import make_batch_with_nav, make_kb
    from knowledge_digest.kb_publish import publish

    page_path = "products/acme/settings/page.md"
    input_source, release4_source, comparison_source, _ = _write_accept_sources(
        tmp_path / "sources", page_paths=[page_path]
    )
    batch = make_batch_with_nav(tmp_path / "batch", pages={page_path: "# Settings\nanswer\n"})
    target = make_kb(tmp_path / "target")
    assert publish(batch, target, run_id="shape-publish")["status"] == "released"
    frozen_root = tmp_path / "freeze"
    frozen = module.freeze(input_source, release4_source, comparison_source, frozen_root)
    question_set = {
        "questions": [
            {"question_id": f"q-{index}", "prompt": f"Prompt {index}", "page_path": page_path}
            for index in range(10)
        ]
    }

    result = module.accept(
        frozen["frozen_id"],
        target,
        freeze_root=frozen_root,
        question_set=question_set,
        run_id="shape-accept",
    )
    assert result["status"] == "blocked"
    assert result["results"] == []
    assert any("questions.module_overrepresented" in reason for reason in result["reasons"])
    assert any("questions.page_repeated" in reason for reason in result["reasons"])


def test_accept_without_target_pages_is_not_evaluated_and_cli_is_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = importlib.import_module("knowledge_digest.kb_accept")
    input_source, release4_source, comparison_source = _make_freeze_sources(tmp_path / "sources")
    frozen_root = tmp_path / "freeze"
    frozen = module.freeze(input_source, release4_source, comparison_source, frozen_root)
    target = _make_current_kb(tmp_path)

    result = module.accept(frozen["frozen_id"], target, freeze_root=frozen_root, run_id="empty-target")
    assert result["status"] == "not_evaluated"
    assert result["acceptance_status"] == "not_evaluated"
    assert result["reason_code"] == "acceptance_not_evaluated"
    assert result["results"] == []
    assert result["conclusions"] == []

    exit_code = module.main([
        frozen["frozen_id"],
        str(target),
        "--freeze-root",
        str(frozen_root),
        "--run-id",
        "empty-target-cli",
    ])
    emitted = json.loads(capsys.readouterr().out)
    assert exit_code != 0
    assert emitted["status"] == "not_evaluated"

    with pytest.raises(ValueError, match="protected acceptance state"):
        module.accept(
            frozen["frozen_id"],
            target,
            freeze_root=frozen_root,
            output=target / "current" / "acceptance.json",
            run_id="protected-output",
        )
    assert not (target / "current" / "acceptance.json").exists()
