from __future__ import annotations

import json
import hashlib
import importlib.util
import re
from dataclasses import replace
from pathlib import Path

import pytest

from knowledge_digest.compiler import (
    Bundle,
    DigestRequest,
    PAGE_TYPES,
    ReaderPage,
    _redact_reader_text,
    _draft_prompt,
    _paragraph_evidence,
    _restrict_prompt_card,
    _route_pages,
    _quality_route_sources,
    _generate_quality_pages,
    _augment_quality_sources,
    _quality_evidence,
    _normalise_page,
    _render_evidence,
    _relative_page_link,
    _root_relative_prefix,
    _question_id,
    _tree_hash,
    _bundle_terminal_state,
    _load_sources,
    _verify_batch,
    SourceDoc,
    digest,
    digest_slice_then_full,
)
from knowledge_digest.quality import (
    _comparison_atom_id,
    _quality_rows,
    _quality_candidate_observation,
    _validate_render_ledger,
    build_candidate_quality_result,
    evaluate_reader_quality,
    item_reader_visible,
    load_quality_projections,
    reader_evidence_groups,
    _source_reader_coverage_blockers,
)
import knowledge_digest.quality as quality_module
from knowledge_digest.providers import ProviderConfigError, ProviderError
from knowledge_digest import publisher

_EVALUATOR_SPEC = importlib.util.spec_from_file_location(
    "task5_reader_evaluator", Path(__file__).parents[1] / "scripts" / "evaluate_reader_candidate.py"
)
assert _EVALUATOR_SPEC and _EVALUATOR_SPEC.loader
_EVALUATOR = importlib.util.module_from_spec(_EVALUATOR_SPEC)
_EVALUATOR_SPEC.loader.exec_module(_EVALUATOR)
DIMENSIONS = _EVALUATOR.DIMENSIONS
_normalise_judgement = _EVALUATOR._normalise_judgement
_source_page_closure = _EVALUATOR._source_page_closure


class FakeModel:
    identity = {"model": "fake"}

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if "通用事实校验器" in prompt:
            page_ids = list(dict.fromkeys(re.findall(r'"page_id"\s*:\s*"((?:src|topic)-[^"]+)"', prompt)))
            return json.dumps({"results": [{"page_id": page_id, "violations": []} for page_id in page_ids]}, ensure_ascii=False)
        if "规划少量跨来源主题页" in prompt:
            return json.dumps({"topics": []}, ensure_ascii=False)
        if "修正一张已经生成的 Reader 页面" in prompt:
            title = re.search(r'"title":\s*"([^"]+)"', prompt).group(1)
            question = re.search(r'"question":\s*"([^"]+)"', prompt).group(1)
            page_type = re.search(r'"page_type":\s*"([^"]+)"', prompt).group(1)
            axes_match = re.search(r'"axes":\s*(\{.*?\}),\s*"summary"', prompt, re.DOTALL)
            axes = json.loads(axes_match.group(1)) if axes_match else {
                "product": "EMM", "module": "资料模块", "object": "资料对象", "scenario": "资料场景", "boundary": "资料边界"
            }
            return json.dumps({
                "title": title,
                "question": question,
                "page_type": page_type,
                "axes": axes,
                "summary": {"body": "原始资料未明确", "evidence_ids": []},
                "sections": {heading: {"body": "原始资料未明确", "evidence_ids": []} for heading in PAGE_TYPES[page_type]},
            }, ensure_ascii=False)
        if "把多个相关来源整理成一张" in prompt:
            evidence_ids = list(dict.fromkeys(re.findall(r'"evidence_id"\s*:\s*"([^"\n]+)"', prompt)))
            selected_ids = []
            selected_sources = set()
            for candidate in evidence_ids:
                source_id = candidate.rsplit("-e", 1)[0]
                if source_id in selected_sources:
                    continue
                selected_sources.add(source_id)
                selected_ids.append(candidate)
                if len(selected_ids) == 2:
                    break
            selected_ids = selected_ids or evidence_ids[:1]
            page_type = re.search(r'"page_type":"(positioning|concept|operation|diagnosis|experience)"', prompt).group(1)
            return json.dumps({
                "title": "EMM 产品定位与阅读入口" if page_type == "positioning" else "EMM 异常定位",
                "question": "EMM 是什么，主要模块和使用边界是什么？" if page_type == "positioning" else "EMM 遇到异常时如何定位、处理和升级？",
                "page_type": page_type,
                "axes": {
                    "product": "ignored",
                    "module": "产品定位",
                    "object": "受管设备",
                    "scenario": "产品选择",
                    "boundary": "来源明确的范围",
                },
                "summary": {"body": "本页汇总多个来源中的产品定位事实。", "evidence_ids": selected_ids},
                "sections": {heading: {"body": "来源中的业务事实。", "evidence_ids": selected_ids} for heading in PAGE_TYPES[page_type]},
            }, ensure_ascii=False)
        source_id = re.search(r"(src-[0-9a-f]{20})-e", prompt).group(1)
        evidence_id = re.search(r'"evidence_id"\s*:\s*"([^"]+)"', prompt).group(1)
        return json.dumps({
            "title": "终端激活与停用",
            "question": "如何激活或停用终端？",
            "page_type": "operation",
            "axes": {
                "product": "ignored",
                "module": "终端管理",
                "object": "Terminal",
                "scenario": "管理员管理终端状态",
                "boundary": "权限与状态限制",
            },
            "summary": {"body": "本页说明终端状态操作。", "evidence_ids": [evidence_id]},
            "sections": {heading: {"body": "原始资料中的操作内容。", "evidence_ids": [evidence_id]} for heading in PAGE_TYPES["operation"]},
        }, ensure_ascii=False)


class PlannerDiagnosisModel(FakeModel):
    def generate(self, prompt: str) -> str:
        if "规划少量跨来源主题页" in prompt:
            source_ids = re.findall(r'"source_id"\s*:\s*"(src-[^"]+)"', prompt)
            return json.dumps({
                "topics": [{
                    "title": "已有的异常专题",
                    "question": "已有专题如何定位异常？",
                    "page_type": "diagnosis",
                    "source_ids": source_ids,
                }]
            }, ensure_ascii=False)
        return super().generate(prompt)


class OneSourceUnavailableModel(FakeModel):
    def generate(self, prompt: str) -> str:
        if "资料路径：" in prompt and "bad.md" in prompt:
            raise ProviderError("provider request timed out")
        return super().generate(prompt)


class SourceVerificationViolationModel(FakeModel):
    def generate(self, prompt: str) -> str:
        if "通用事实校验器" in prompt:
            page_ids = list(dict.fromkeys(re.findall(r'"page_id"\s*:\s*"((?:src|topic)-[^" ]+)"', prompt)))
            return json.dumps({
                "results": [
                    {
                        "page_id": page_id,
                        "violations": ([{"type": "unsupported", "detail": "正文事实没有被证据支持", "evidence_ids": []}] if page_id.startswith("src-") else []),
                    }
                    for page_id in page_ids
                ]
            }, ensure_ascii=False)
        return super().generate(prompt)


class FakeEmbedder:
    identity = {"model": "fake", "dimension": "3"}

    def __init__(self) -> None:
        self.calls = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [[float(index + 1), 1.0, 0.5] for index, _ in enumerate(texts)]


class RouteChangingEmbedder:
    identity = {"model": "route-changing", "dimension": "2"}

    def __init__(self, reverse: bool = False) -> None:
        self.reverse = reverse

    def embed(self, texts: list[str]) -> list[list[float]]:
        source_count = len(texts) - 1
        query_vector = [0.0, 1.0] if self.reverse else [1.0, 0.0]
        vectors = []
        for index in range(source_count):
            vectors.append([1.0, 0.0] if "EMM介绍文档.md" in texts[index] else [0.0, 1.0])
        return [*vectors, query_vector]


class RecordingEmbedder(FakeEmbedder):
    def __init__(self) -> None:
        super().__init__()
        self.inputs: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.inputs.extend(texts)
        return super().embed(texts)


class QualityFakeModel:
    identity = {"model": "fake-quality"}

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if "通用事实校验器" in prompt:
            page_ids = list(dict.fromkeys(re.findall(r'"page_id"\s*:\s*"((?:Q-|src-|topic-)[^"]+)"', prompt)))
            return json.dumps({"results": [{"page_id": page_id, "violations": []} for page_id in page_ids]}, ensure_ascii=False)
        if "一次处理下面每一份独立原始资料" in prompt:
            pages = []
            source_ids = list(dict.fromkeys(re.findall(r'"source_id"\s*:\s*"((?:src|source)-[^"]+)"', prompt)))
            supplied_evidence_ids = list(dict.fromkeys(re.findall(r'"evidence_id"\s*:\s*"([^"]+)"', prompt)))
            if not supplied_evidence_ids:
                prefix_match = re.search(r"完整 evidence_id 前缀是 ([^\s，]+)-", prompt)
                suffixes = re.findall(r"^\[(e\d{4})\]", prompt, re.MULTILINE)
                if prefix_match:
                    supplied_evidence_ids = [f"{prefix_match.group(1)}-{suffix}" for suffix in suffixes]
            for source_id in source_ids:
                refs = [
                    evidence_id
                    for evidence_id in supplied_evidence_ids
                    if evidence_id.startswith(f"{source_id}-")
                ][:1]
                pages.append({
                    "source_id": source_id,
                    "page": {
                        "schema_version": "task5-semantic-output.v2",
                        "title": "来源摘要",
                        "page_type": "concept",
                        "page_type_claim_ids": refs or ["source-claim-placeholder"],
                        "axis": {"product": "EMM", "module": "资料模块", "object": "资料对象", "scene": "资料场景", "boundary": "原始资料边界"},
                        "axis_claim_ids": {name: refs or ["source-claim-placeholder"] for name in ("product", "module", "object", "scene", "boundary")},
                        "summary": {"body": "来源摘要。" if refs else "原始资料未明确", "claim_ids": refs, "evidence_ids": refs},
                        "sections": {heading: {"body": "资料内容。" if refs else "原始资料未明确", "claim_ids": refs, "evidence_ids": refs} for heading in PAGE_TYPES["concept"]},
                    },
                })
            return json.dumps({"pages": pages}, ensure_ascii=False)
        if "你是企业知识库编辑。只根据下面这一份原始资料" in prompt:
            evidence_ids = list(dict.fromkeys(re.findall(r'"evidence_id"\s*:\s*"([^"]+)"', prompt)))
            if not evidence_ids:
                prefix_match = re.search(r"完整 evidence_id 前缀是 ([^\s，]+)-", prompt)
                suffixes = re.findall(r"^\[(e\d{4})\]", prompt, re.MULTILINE)
                if prefix_match:
                    evidence_ids = [f"{prefix_match.group(1)}-{suffix}" for suffix in suffixes]
            return json.dumps({
                "schema_version": "task5-semantic-output.v2",
                "title": "来源摘要",
                "page_type": "concept",
                "page_type_claim_ids": evidence_ids[:1],
                "axis": {"product": "EMM", "module": "资料模块", "object": "资料对象", "scene": "资料场景", "boundary": "原始资料边界"},
                "axis_claim_ids": {name: evidence_ids[:1] for name in ("product", "module", "object", "scene", "boundary")},
                "summary": {"body": "基于原始资料整理的来源摘要。", "claim_ids": evidence_ids[:1], "evidence_ids": evidence_ids[:1]},
                "sections": {heading: {"body": "基于原始资料整理的内容。", "claim_ids": evidence_ids[:1], "evidence_ids": evidence_ids[:1]} for heading in PAGE_TYPES["concept"]},
            }, ensure_ascii=False)
        page_type = re.search(r"^- page_type: (\S+)$", prompt, re.MULTILINE).group(1)
        title = re.search(r"^- title: (.+)$", prompt, re.MULTILINE).group(1)
        question = re.search(r"^- question: (.+)$", prompt, re.MULTILINE).group(1)
        raw_axes = json.loads(re.search(r"^- axes: (\{.*\})$", prompt, re.MULTILINE).group(1))
        axes = {key: value for key, value in raw_axes.items() if key != "scene"}
        axes["scenario"] = raw_axes["scene"]
        evidence_ids = list(dict.fromkeys(re.findall(r'"evidence_id"\s*:\s*"(qev-[0-9a-f]+)"', prompt)))
        return json.dumps({
            "schema_version": "task5-semantic-output.v2",
            "title": title,
            "page_type": page_type,
            "page_type_claim_ids": evidence_ids,
            "axis": {"product": axes["product"], "module": axes["module"], "object": axes["object"], "scene": axes["scenario"], "boundary": axes["boundary"]},
            "axis_claim_ids": {name: evidence_ids for name in ("product", "module", "object", "scene", "boundary")},
            "summary": {"body": "基于原始资料整理的固定问题答案。", "claim_ids": evidence_ids, "evidence_ids": evidence_ids},
            "sections": {heading: {"body": "基于原始资料整理的可执行说明。", "claim_ids": evidence_ids, "evidence_ids": evidence_ids} for heading in PAGE_TYPES[page_type]},
        }, ensure_ascii=False)


class RecordingSourceDigestModel(FakeModel):
    def __init__(self) -> None:
        super().__init__()
        self.source_digest_prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        if "你是企业知识库编辑。只根据下面这一份原始资料" in prompt:
            self.source_digest_prompts.append(prompt)
        return super().generate(prompt)


class QualityClosureRetryModel(QualityFakeModel):
    """First quality answer omits one required group, second fixes it."""

    def __init__(self) -> None:
        super().__init__()
        self.omitted_once = False

    def generate(self, prompt: str) -> str:
        if "固定投影：" in prompt and not self.omitted_once:
            self.omitted_once = True
            value = json.loads(super().generate(prompt))
            evidence_ids = list(dict.fromkeys(re.findall(r'"evidence_id"\s*:\s*"(qev-[0-9a-f]+)"', prompt)))
            required_match = re.search(
                r"必答证据覆盖（硬要求）：\n(\[.*?\])\n上面每个",
                prompt,
                re.DOTALL,
            )
            required_groups = json.loads(required_match.group(1)) if required_match else []
            omitted = str(required_groups[0]["must_cite_at_least_one"][0]) if required_groups else evidence_ids[-1]

            def remove(value: object) -> object:
                if isinstance(value, list):
                    return [remove(item) for item in value if item != omitted]
                if isinstance(value, dict):
                    return {key: remove(item) for key, item in value.items()}
                return value

            return json.dumps(remove(value), ensure_ascii=False)
        return super().generate(prompt)


class QualitySourceVerificationViolationModel(QualityFakeModel):
    def generate(self, prompt: str) -> str:
        if "通用事实校验器" in prompt:
            self.calls += 1
            page_ids = list(dict.fromkeys(re.findall(r'"page_id"\s*:\s*"((?:Q-|src-|topic-)[^"]+)"', prompt)))
            return json.dumps({
                "results": [
                    {
                        "page_id": page_id,
                        "violations": ([{
                            "type": "unsupported",
                            "detail": "来源页事实没有被证据支持",
                            "evidence_ids": [],
                        }] if page_id.startswith("src-") else []),
                }
                for page_id in page_ids
            ]
            }, ensure_ascii=False)
        if "修正一张已经生成的 Reader 页面" in prompt:
            evidence_id = re.search(r'"evidence_id":\s*"([^"]+)"', prompt).group(1)
            return json.dumps({
                "schema_version": "task5-semantic-output.v2",
                "title": "来源摘要",
                "page_type": "concept",
                "page_type_claim_ids": [evidence_id],
                "axis": {"product": "EMM", "module": "资料模块", "object": "资料对象", "scene": "资料场景", "boundary": "原始资料边界"},
                "axis_claim_ids": {name: [evidence_id] for name in ("product", "module", "object", "scene", "boundary")},
                "summary": {"body": "原始资料未明确", "claim_ids": [], "evidence_ids": []},
                "sections": {heading: {"body": "原始资料未明确", "claim_ids": [], "evidence_ids": []} for heading in PAGE_TYPES["concept"]},
            }, ensure_ascii=False)
        return super().generate(prompt)


def _page(page_type: str, product: str) -> ReaderPage:
    headings = PAGE_TYPES[page_type]
    sections = {"summary": {"body": "摘要", "evidence_ids": ()}}
    sections.update({heading: {"body": "内容", "evidence_ids": ()} for heading in headings})
    return ReaderPage(
        source_id=f"src-{product}-{page_type}",
        title=f"{product}-{page_type}",
        question="页面问题",
        page_type=page_type,
        axes={"product": product, "module": "模块", "object": "对象", "scenario": "场景", "boundary": "边界"},
        sections=sections,
    )


def test_home_routes_only_to_the_reader_role_that_matches_the_question() -> None:
    pages = [_page("positioning", "EMM"), _page("operation", "EMM"), _page("diagnosis", "GoInsight")]
    routes = _route_pages(pages, FakeEmbedder())

    assert all(page.page_type == "positioning" for page in routes["我想了解一个产品是什么、服务谁、怎么选以及边界"])
    assert all(page.page_type == "operation" for page in routes["我想按步骤完成一项操作"])
    assert all(page.page_type == "diagnosis" for page in routes["我遇到了问题，需要定位原因"])
    assert all(len(selected) <= 1 for selected in routes.values())


def test_quality_surface_requires_an_explicit_reader_token() -> None:
    assert item_reader_visible({"surface": "Reader.body+Audit"}) is True
    assert item_reader_visible({"surface": "Audit"}) is False
    assert item_reader_visible({"surface": "not-reader"}) is False
    assert item_reader_visible({}) is False


def test_quality_embedding_order_is_consumed_by_qwen_closure() -> None:
    root = Path(__file__).parents[1]
    projections = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )
    sources = _load_sources(Path("/Users/Hugh/Downloads/confluence 原始数据"))
    projection = next(item for item in projections if item.projection_id == "Q-POS-01.positioning")

    normal, normal_ledger = _quality_route_sources((projection,), sources, RouteChangingEmbedder())
    reverse, reverse_ledger = _quality_route_sources((projection,), sources, RouteChangingEmbedder(reverse=True))

    assert set(normal[projection.projection_id]) == set(projection.source_paths)
    assert set(reverse[projection.projection_id]) == set(projection.source_paths)
    assert normal[projection.projection_id] != reverse[projection.projection_id]
    assert normal_ledger[0]["selected_source_paths"] == list(normal[projection.projection_id])
    assert reverse_ledger[0]["selected_source_paths"] == list(reverse[projection.projection_id])


def test_long_source_prompt_keeps_all_raw_lines_in_compact_form() -> None:
    lines = tuple(f"| row {index} | {'事实内容 ' * 10}|" for index in range(1, 901))
    source_id = "src-long-table"
    raw_text = "\n".join(lines)
    source = SourceDoc(
        source_id=source_id,
        relative_path="emm for ios/long-table.md",
        raw_bytes=raw_text.encode("utf-8"),
        text=raw_text,
        lines=lines,
        product="emm-for-ios",
        product_label="EMM for iOS",
        evidence=tuple(
            {
                "evidence_id": f"{source_id}-e{index:04d}",
                "start_line": index,
                "end_line": index,
                "text": lines[index - 1],
            }
            for index in range(1, len(lines) + 1)
        ),
    )

    prompt = _draft_prompt(source)

    assert len(prompt) < 120_000
    assert "[e0001]" in prompt
    assert "完整 evidence_id 前缀是 src-long-table-" in prompt
    assert lines[-1] in prompt


def test_quality_page_retries_once_after_evidence_closure_failure() -> None:
    root = Path(__file__).parents[1]
    projections = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )
    sources = _load_sources(Path("/Users/Hugh/Downloads/confluence 原始数据"))
    sources, _extra = _augment_quality_sources(sources, projections)
    model = QualityClosureRetryModel()

    pages, failures, _ledger, trace = _generate_quality_pages(
        (projections[0],), sources, FakeEmbedder(), model
    )

    assert len(pages) == 1
    assert failures == []
    assert [item["attempt"] for item in trace[projections[0].projection_id]] == [1, 2]
    assert trace[projections[0].projection_id][-1]["status"] == "passed"


def test_digest_publishes_reader_home_audit_and_exact_snapshots(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    first = source / "merchant system"
    first.mkdir()
    original = "## 激活\n\n管理员可以激活 Terminal。\n"
    (first / "终端.md").write_text(original, encoding="utf-8")
    second = source / "emm for android "
    second.mkdir()
    (second / "设备.md").write_text("## 设备\n\n设备需要注册。\n", encoding="utf-8")
    output = tmp_path / "kb"
    model = FakeModel()
    embedder = FakeEmbedder()

    result = digest(
        DigestRequest(
            source,
            output,
            tmp_path / "unused.json",
            companybrain_route_snapshot={
                "companybrain_snapshot_id": "cb-test",
                "companybrain_tree_sha256": "b" * 64,
                "observation_sha256": "c" * 64,
            },
        ),
        (model, embedder),
    )

    assert result.outcome == "completed"
    assert result.home_path == output / "bundle" / "Home.md"
    assert (output / "bundle" / "Home.md").is_file()
    assert (output / "bundle" / "Audit.md").is_file()
    assert (output / "bundle" / "_audit" / "run-result.json").is_file()
    assert (output / "bundle" / "_audit" / "run-result.receipt.json").is_file()
    assert (output / "bundle" / "_audit" / "companybrain-route-snapshot.json").is_file()
    assert (output / "bundle" / "_audit" / "evidence.jsonl").is_file()
    assert not (output / ".manifest.sha256").exists()
    assert not (output / "bundle" / "_audit" / "sources").exists()
    source_rows = [json.loads(line) for line in (output / "bundle" / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(source_rows) == 2
    assert all("raw_text" not in row for row in source_rows)
    assert all(row["line_count"] > 0 for row in source_rows)
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert run["source_count"] == 2
    assert run["source_page_count"] == 2
    assert run["topic_page_count"] == 2
    assert run["reader_page_count"] == 4
    assert run["provider_calls"]["llm"] == model.calls
    assert run["provider_calls"]["embedding"] == embedder.calls
    assert run["companybrain_binding"] == {
        "companybrain_snapshot_id": "cb-test",
        "companybrain_tree_sha256": "b" * 64,
        "observation_sha256": "c" * 64,
    }
    receipt = json.loads((output / "bundle" / "_audit" / "run-result.receipt.json").read_text(encoding="utf-8"))
    assert receipt["run_id"] == run["run_id"]
    assert receipt["tree_sha256"] == run["manifest"]["tree_sha256"]
    snapshot = json.loads((output / "bundle" / "_audit" / "companybrain-route-snapshot.json").read_text(encoding="utf-8"))
    assert snapshot["status"] == "missing"
    assert snapshot["run_id"] == run["run_id"]
    assert snapshot["source_manifest_sha256"] == run["source_manifest_hash"]


def test_each_ready_source_gets_exactly_one_source_digest_request(tmp_path: Path) -> None:
    source = tmp_path / "source" / "goinsight"
    source.mkdir(parents=True)
    (source / "one.md").write_text("## 一\n\n第一份资料。\n", encoding="utf-8")
    (source / "two.md").write_text("## 二\n\n第二份资料。\n", encoding="utf-8")
    output = tmp_path / "kb"
    model = RecordingSourceDigestModel()

    result = digest(DigestRequest(tmp_path / "source", output, tmp_path / "unused.json"), (model, FakeEmbedder()))

    assert result.outcome == "completed"
    requested_paths = [
        re.search(r"^资料路径：(.+)$", prompt, re.MULTILINE).group(1)
        for prompt in model.source_digest_prompts
    ]
    assert sorted(requested_paths) == ["goinsight/one.md", "goinsight/two.md"]
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    ready_sources = [row for row in run["manifest"]["sources"] if row["source_digest_eligible"]]
    assert len(model.source_digest_prompts) == len(ready_sources) == 2
    assert run["provider_call_plan"]["ready_sources"] == 2
    assert run["provider_calls"]["llm"] >= len(model.source_digest_prompts)


def test_task5_source_digest_failure_uses_bounded_recovery_and_stays_audit_only(tmp_path: Path) -> None:
    import knowledge_digest.compiler as compiler

    source = tmp_path / "source"
    source.mkdir()
    (source / "bad.md").write_text("## 失败资料\n\n这份资料用于验证失败边界。\n", encoding="utf-8")
    source_doc = compiler._load_sources(source)[0]

    class FailingModel:
        identity = {"model": "failing"}

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, _prompt: str) -> str:
            self.calls += 1
            raise ProviderError("provider request timed out")

    model = FailingModel()

    pages, failures = compiler._generate_pages(
        (source_doc,),
        model,
        retry_limit=compiler._QUALITY_SOURCE_RETRY_LIMIT,
        require_task5_semantic=True,
    )

    assert pages == []
    assert len(failures) == 1
    # One HTTP attempt per logical request; compiler recovery adds at most
    # three requests for one stubborn source.
    assert model.calls == 4
    assert failures[0]["status"] == "audit_only"


def test_task5_quality_recovery_budget_matches_active_contract() -> None:
    import knowledge_digest.compiler as compiler

    # The contract is a global pool, not one retry budget per source. The
    # per-source loop may still use at most three extra attempts, but the
    # aggregate planner and executor must stop at twelve recovery calls.
    assert compiler._QUALITY_SOURCE_RETRY_LIMIT == 12


def test_task5_quality_recovery_executor_obeys_global_budget(tmp_path: Path) -> None:
    import threading
    import knowledge_digest.compiler as compiler

    source = tmp_path / "source"
    source.mkdir()
    for index in range(14):
        (source / f"doc-{index:02d}.md").write_text(
            f"## 失败资料 {index}\n\n这份资料用于验证全局恢复预算。\n",
            encoding="utf-8",
        )
    sources = compiler._load_sources(source)

    class FailingModel:
        identity = {"model": "failing-global-budget"}

        def __init__(self) -> None:
            self.calls = 0
            self._lock = threading.Lock()

        def generate(self, _prompt: str) -> str:
            with self._lock:
                self.calls += 1
            raise ProviderError("provider request timed out")

    model = FailingModel()
    pages, failures = compiler._generate_pages(
        sources,
        model,
        retry_limit=compiler._QUALITY_SOURCE_RETRY_LIMIT,
        require_task5_semantic=True,
    )

    assert pages == []
    assert len(failures) == len(sources) == 14
    assert model.calls == len(sources) + compiler._QUALITY_SOURCE_RETRY_LIMIT == 26


def test_public_secret_scan_blocks_before_atomic_publication(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import knowledge_digest.compiler as compiler

    source = tmp_path / "source" / "goinsight"
    source.mkdir(parents=True)
    (source / "one.md").write_text("## 一\n\n第一份资料。\n", encoding="utf-8")
    output = tmp_path / "kb"
    original_render_page = compiler._render_page
    monkeypatch.setattr(
        compiler,
        "_render_page",
        lambda page, sources, pages: "# 不应发布\n\napi_key: leaked-secret\n",
    )

    result = digest(DigestRequest(tmp_path / "source", output, tmp_path / "unused.json"), (FakeModel(), FakeEmbedder()))

    assert result.outcome == "blocked"
    assert "public bundle secret/path scan failed" in result.reason_code
    assert not output.exists()
    assert not list(tmp_path.glob(".kb.staging-*"))
    monkeypatch.setattr(compiler, "_render_page", original_render_page)


def test_m402_allows_only_host_staging_audit_intermediates(tmp_path: Path) -> None:
    import knowledge_digest.compiler as compiler

    files = {"_audit/quality.json": b'{"source":"/tmp/formal-staging"}\n'}

    with pytest.raises(ValueError, match="public bundle secret/path scan failed"):
        compiler._published_files(files)

    published = compiler._published_files(files, allow_formal_intermediate=True)
    assert published == {"bundle/_audit/quality.json": files["_audit/quality.json"]}


def test_atomic_publication_failure_leaves_no_target_or_staging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "kb"

    def fail_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError("injected rename failure")

    monkeypatch.setattr(publisher.os, "replace", fail_replace)

    with pytest.raises(publisher.PublishError, match="atomic publication failed"):
        publisher.commit({"bundle/Home.md": b"# Home\n"}, output, run_id="atomic-test")

    assert not output.exists()
    assert not list(tmp_path.glob(".kb.staging-*"))
    assert not (tmp_path / ".kb.lock").exists()


def test_task5_public_outcome_keeps_candidate_execution_separate_from_release() -> None:
    page = _page("concept", "EMM")
    request = DigestRequest(
        Path("raw"),
        Path("output"),
        Path("provider.json"),
        quality_config_path=Path("quality.json"),
    )
    incomplete = Bundle(
        files={"_audit/quality.json": b'{"publication_status":"not_released","verdict":"UNKNOWN"}\n'},
        pages=(page,),
        sources=(),
        run_id="run-candidate",
        warnings=(),
    )
    candidate = Bundle(
        files={"_audit/quality.json": b'{"publication_status":"released","verdict":"released"}\n'},
        pages=(page,),
        sources=(),
        run_id="run-candidate",
        warnings=(),
    )
    formal_request = replace(request, gate="M402")

    assert _bundle_terminal_state(incomplete, request) == ("not_released", "quality_not_released")
    assert _bundle_terminal_state(candidate, formal_request) == ("not_released", "quality_result_not_promoted")
    assert _bundle_terminal_state(replace(candidate, quality_result={"publication_status": "released", "verdict": "released"}), replace(formal_request, quality_result_promoted=True)) == ("released", None)


def test_public_entry_writes_one_bundle_tree_and_no_legacy_digest_tree(tmp_path: Path) -> None:
    source = tmp_path / "source" / "merchant system"
    source.mkdir(parents=True)
    (source / "说明.md").write_text("## 说明\n\n管理员可以配置终端。\n", encoding="utf-8")
    output = tmp_path / "run"

    result = digest(DigestRequest(tmp_path / "source", output, tmp_path / "unused.json"), (FakeModel(), FakeEmbedder()))

    assert result.outcome == "completed"
    assert result.home_path == output / "bundle" / "Home.md"
    assert (output / "bundle" / "Home.md").is_file()
    assert (output / "bundle" / "Audit.md").is_file()
    assert not (output / "Home.md").exists()
    assert not (output / "_digest").exists()
    assert all(path.relative_to(output).parts[0] == "bundle" for path in output.rglob("*") if path.is_file())


def test_digest_does_not_overwrite_existing_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "one.md").write_text("# one\n", encoding="utf-8")
    output = tmp_path / "kb"
    output.mkdir()
    sentinel = output / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")

    result = digest(DigestRequest(source, output, tmp_path / "unused.json"), (FakeModel(), FakeEmbedder()))

    assert result.outcome == "failed"
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_publisher_lock_blocks_competing_run_without_touching_target(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "one.md").write_text("# one\n", encoding="utf-8")
    output = tmp_path / "kb"
    lock = output.parent / f".{output.name}.lock"
    lock.write_text("owned by another run\n", encoding="utf-8")

    result = digest(DigestRequest(source, output, tmp_path / "unused.json"), (FakeModel(), FakeEmbedder()))

    assert result.outcome == "failed"
    assert "lock" in (result.reason_code or "")
    assert not output.exists()
    assert lock.read_text(encoding="utf-8") == "owned by another run\n"


def test_render_ledger_does_not_publish_raw_evidence_text() -> None:
    source = SourceDoc(
        source_id="src-ledger-test",
        relative_path="one.md",
        raw_bytes=b"secret fact",
        text="secret fact",
        lines=("secret fact",),
        product="emm",
        product_label="EMM",
        evidence=({"evidence_id": "src-ledger-test-e0001", "start_line": 1, "end_line": 1, "text": "secret fact"},),
    )
    page = ReaderPage(
        source_id=source.source_id,
        title="事实页",
        question="事实是什么？",
        page_type="concept",
        axes={"product": "EMM", "module": "模块", "object": "对象", "scenario": "场景", "boundary": "边界"},
        sections={
            "summary": {"body": "事实", "evidence_ids": ("src-ledger-test-e0001",), "claim_ids": ("claim-1",)},
            **{heading: {"body": "原始资料未明确", "evidence_ids": ()} for heading in PAGE_TYPES["concept"]},
        },
        axis_evidence_ids={name: ("src-ledger-test-e0001",) for name in ("product", "module", "object", "scenario", "boundary")},
        relative_path="products/emm/concept/fact.md",
        page_id="page-1",
        page_key="source:src-ledger-test",
    )

    payload = _render_evidence((source,), (page,), {"问题": (page,)})
    rows = [json.loads(line) for line in payload.decode("utf-8").splitlines()]

    assert rows
    assert all(row["schema_version"] == "knowledge-digest-render-unit.v1" for row in rows)
    assert all("text" not in row for row in rows)
    assert all("secret fact" not in json.dumps(row, ensure_ascii=False) for row in rows)
    assert any(row["surface"] == "Reader.section" for row in rows)
    assert any(row["surface"] == "Reader.answer_body" for row in rows)
    assert any(row["surface"] == "Reader.page_type" for row in rows)
    axis_rows = [row for row in rows if row["surface"] == "Reader.axis"]
    assert len(axis_rows) == 5
    assert all(row["evidence_ids"] for row in axis_rows)
    assert any(row["surface"] == "Home.route" for row in rows)
    home_route = next(row for row in rows if row["surface"] == "Home.route")
    assert home_route["page_path"] == "bundle/Home.md"
    assert home_route["home_target_page_identity"] == page.page_id
    assert home_route["slot"].endswith(f":{page.page_id}")
    title = next(row for row in rows if row["surface"] == "Reader.title")
    stable_key = "\0".join((title["page_path"], title["page_key"], title["surface"], title["slot"]))
    assert title["unit_id"] == "u-" + hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:24]


def test_quality_lineage_reports_unknown_sections_separately() -> None:
    source = SourceDoc(
        source_id="src-lineage-unknown",
        relative_path="one.md",
        raw_bytes=b"fact",
        text="fact",
        lines=("fact",),
        product="emm",
        product_label="EMM",
        evidence=({"evidence_id": "src-lineage-unknown-e0001", "start_line": 1, "end_line": 1, "text": "fact"},),
    )
    page = ReaderPage(
        source_id=source.source_id,
        title="事实页",
        question="事实是什么？",
        page_type="concept",
        axes={"product": "EMM", "module": "模块", "object": "对象", "scenario": "场景", "boundary": "边界"},
        sections={
            "summary": {"body": "事实", "evidence_ids": ("src-lineage-unknown-e0001",)},
            **{heading: {"body": "原始资料未明确", "evidence_ids": ()} for heading in PAGE_TYPES["concept"]},
        },
        axis_evidence_ids={name: ("src-lineage-unknown-e0001",) for name in ("product", "module", "object", "scenario", "boundary")},
        relative_path="products/emm/concept/fact.md",
        page_id="page-lineage-unknown",
        page_key="source:src-lineage-unknown",
    )
    ledger = _render_evidence((source,), (page,), {"问题": (page,)})
    ledger_rows = [json.loads(line) for line in ledger.decode("utf-8").splitlines()]
    unknown_section_rows = [
        row for row in ledger_rows
        if row["surface"] in {"Reader.section", "Reader.answer_body"}
        and not row["evidence_ids"]
    ]
    assert len(unknown_section_rows) == 8
    assert {row["surface"] for row in unknown_section_rows} == {"Reader.section", "Reader.answer_body"}
    result = build_candidate_quality_result(
        projections=(),
        files={
            page.relative_path: b"# fact\n",
            "Home.md": b"# home\n",
            "Audit.md": b'<a id="evidence-src-lineage-unknown-e0001"></a>\n',
            "_audit/evidence.jsonl": ledger,
        },
        route_ledger=[{"projection_id": "none"}],
    )

    assert result["unknown_units"] == 8
    assert result["rendered_units"] == result["bound_units"] == 10
    assert result["lineage_coverage"] == 1.0


def test_quality_result_blocks_ready_source_without_reader_page() -> None:
    sources = "\n".join([
        json.dumps({
            "source_id": "src-ready-missing",
            "source_digest_eligible": True,
            "reader_page_ids": [],
        }, ensure_ascii=False),
        json.dumps({
            "source_id": "src-known-empty",
            "source_digest_eligible": False,
            "reader_page_ids": [],
        }, ensure_ascii=False),
    ]) + "\n"

    assert _source_reader_coverage_blockers({"_audit/sources.jsonl": sources.encode("utf-8")}) == [
        "source_reader_coverage_incomplete:1",
    ]


def test_candidate_quality_result_never_promotes_structural_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(quality_module, "_validate_render_ledger", lambda *_args: [])
    monkeypatch.setattr(quality_module, "_source_reader_coverage_blockers", lambda *_args: [])
    monkeypatch.setattr(quality_module, "_companybrain_binding_errors", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        quality_module,
        "_quality_rows",
        lambda *_args, **_kwargs: {
            "dimension_verdicts": {"projection": {"DIM-01.route": ["KD_WIN", "KD_WIN"]}},
            "quality_rows": [{"projection_key": "projection", "dimension_id": "DIM-01.route", "verdict": "KD_WIN"}],
            "projections": [],
        },
    )

    result = build_candidate_quality_result(
        projections=(),
        files={"Audit.md": b"# Audit\n", "_audit/evidence.jsonl": b""},
        companybrain_observation={"run_id": "run", "rows": []},
        expected_source_manifest_sha256="a" * 64,
        expected_run_id="run",
        route_ledger=[{"projection_id": "projection"}],
    )

    assert result["quality_result_status"] == "candidate"
    assert result["publication_status"] == "not_released"
    assert result["verdict"] == "UNKNOWN"
    assert all(row["verdict"] == "UNKNOWN" for row in result["quality_rows"])
    assert all(
        values == ["UNKNOWN", "UNKNOWN"]
        for dimensions in result["dimension_verdicts"].values()
        for values in dimensions.values()
    )


def test_slice_candidate_does_not_require_companybrain_observation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(quality_module, "_validate_render_ledger", lambda *_args: [])
    monkeypatch.setattr(quality_module, "_source_reader_coverage_blockers", lambda *_args: [])

    result = build_candidate_quality_result(
        projections=(),
        files={"Audit.md": b"# Audit\n", "_audit/evidence.jsonl": b""},
        route_ledger=[{"projection_id": "projection"}],
        require_companybrain_observation=False,
    )

    assert "companybrain_observation_missing" not in result["hard_blockers"]
    assert "quality_dimensions_not_all_kd_win" in result["hard_blockers"]


def test_quality_lineage_rejects_unbound_reader_metadata() -> None:
    source = SourceDoc(
        source_id="src-metadata-only",
        relative_path="one.md",
        raw_bytes=b"fact",
        text="fact",
        lines=("fact",),
        product="emm",
        product_label="EMM",
        evidence=(),
    )
    page = ReaderPage(
        source_id=source.source_id,
        title="事实页",
        question="事实是什么？",
        page_type="concept",
        axes={"product": "EMM", "module": "原始资料未明确", "object": "原始资料未明确", "scenario": "原始资料未明确", "boundary": "原始资料未明确"},
        sections={"summary": {"body": "原始资料未明确", "evidence_ids": ()}},
        relative_path="products/emm/concept/fact.md",
        page_id="page-metadata-only",
        page_key="source:src-metadata-only",
    )

    ledger = _render_evidence((source,), (page,))
    errors = _validate_render_ledger(
        [json.loads(line) for line in ledger.decode("utf-8").splitlines()],
        {page.relative_path: b"# fact\n", "Audit.md": b""},
    )
    assert sum(error.startswith("render_unit_lineage:") for error in errors) == 3
    assert sum(error.startswith("render_unit_evidence_bindings:") for error in errors) == 3


def test_render_evidence_rejects_duplicate_home_route_target() -> None:
    source = SourceDoc(
        source_id="src-duplicate-route",
        relative_path="duplicate.md",
        raw_bytes=b"fact",
        text="fact",
        lines=("fact",),
        product="emm",
        product_label="EMM",
        evidence=({"evidence_id": "src-duplicate-route-e0001", "start_line": 1, "end_line": 1, "text": "fact"},),
    )
    page = ReaderPage(
        source_id=source.source_id,
        title="重复目标页",
        question="是什么？",
        page_type="concept",
        axes={"product": "EMM", "module": "模块", "object": "对象", "scenario": "场景", "boundary": "边界"},
        sections={
            "summary": {"body": "事实", "evidence_ids": ("src-duplicate-route-e0001",), "claim_ids": ("claim-1",)},
            **{heading: {"body": "原始资料未明确", "evidence_ids": ()} for heading in PAGE_TYPES["concept"]},
        },
        axis_evidence_ids={name: ("src-duplicate-route-e0001",) for name in ("product", "module", "object", "scenario", "boundary")},
        relative_path="products/emm/concept/duplicate.md",
        page_id="duplicate-page",
        page_key="source:src-duplicate-route",
    )
    with pytest.raises(ValueError, match="duplicate Home.route target"):
        _render_evidence((source,), (page,), {"问题": (page, page)})


def test_quality_evaluator_stays_unknown_without_companybrain_observation(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    result = evaluate_reader_quality(
        bundle_root=tmp_path,
        quality_config=root / "config" / "task5-quality-cases-v2.json",
        companybrain_observation=None,
    )

    assert result["schema_version"] == "task5-quality-result.v3"
    assert result["quality_result_status"] == "candidate"
    assert result["verdict"] == "UNKNOWN"
    assert "companybrain_observation_missing" in result["hard_blockers"]


def test_quality_baseline_requires_current_m402_binding() -> None:
    root = Path(__file__).parents[1]
    projections = (load_quality_projections(root / "config" / "task5-quality-cases-v2.json", root / "config" / "task5-projection-rules-v1.json")[0],)
    result = build_candidate_quality_result(
        projections=projections,
        files={"Audit.md": b"# Audit\n", "_audit/evidence.jsonl": b""},
        route_ledger=[{"projection_id": "Q"}],
        companybrain_observation={"run_id": "run-old"},
    )

    assert "companybrain_binding_missing:source_manifest_sha256" in result["hard_blockers"]
    assert all(row["verdict"] == "UNKNOWN" for row in result["quality_rows"])


def test_quality_rejects_file_list_snapshot_without_observation_rows() -> None:
    root = Path(__file__).parents[1]
    projections = (load_quality_projections(root / "config" / "task5-quality-cases-v2.json", root / "config" / "task5-projection-rules-v1.json")[0],)
    result = build_candidate_quality_result(
        projections=projections,
        files={"Audit.md": b"# Audit\n", "_audit/evidence.jsonl": b""},
        route_ledger=[{"projection_id": "Q"}],
        companybrain_observation={
            "run_id": "run-current",
            "source_manifest_sha256": "a" * 64,
            "companybrain_snapshot_id": "cb-current",
            "companybrain_tree_sha256": "b" * 64,
            "observation_sha256": "c" * 64,
        },
    )
    assert "companybrain_observation_rows_missing" in result["hard_blockers"]


def test_m402_source_closure_requires_frozen_89_entries() -> None:
    from knowledge_digest.compiler import _validate_m402_source_closure

    source = SourceDoc(
        "src-test",
        "merchant system/test.md",
        b"fact\n",
        "fact\n",
        ("fact",),
        "merchant-system",
        "Merchant System",
        ({"evidence_id": "src-test-e0001", "start_line": 1, "end_line": 1, "text": "fact"},),
    )
    with pytest.raises(ValueError, match="exactly 89"):
        _validate_m402_source_closure((source,))


def test_task5_semantic_page_rejects_long_exact_raw_copy() -> None:
    raw = "这是一个很长的原始段落，用于验证系统不能把整段原文直接当成业务答案。" * 12
    source = SourceDoc(
        "src-copy",
        "merchant system/copy.md",
        (raw + "\n").encode("utf-8"),
        raw + "\n",
        tuple(raw.splitlines()),
        "merchant-system",
        "Merchant System",
        ({"evidence_id": "src-copy-e0001", "start_line": 1, "end_line": 1, "text": raw},),
    )
    value = {
        "schema_version": "task5-semantic-output.v2",
        "title": "简要说明",
        "page_type": "concept",
        "page_type_claim_ids": ["src-copy-e0001"],
        "axis": {name: "已确认" for name in ("product", "module", "object", "scene", "boundary")},
        "axis_claim_ids": {name: ["src-copy-e0001"] for name in ("product", "module", "object", "scene", "boundary")},
        "summary": {"body": raw, "claim_ids": ["src-copy-e0001"], "evidence_ids": ["src-copy-e0001"]},
        "sections": {
            heading: {"body": "简短说明", "claim_ids": ["src-copy-e0001"], "evidence_ids": ["src-copy-e0001"]}
            for heading in PAGE_TYPES["concept"]
        },
    }
    with pytest.raises(ValueError, match="copies a long raw evidence block"):
        _normalise_page(
            (source,),
            value,
            expected_page_type="concept",
            expected_axes={name: "已确认" for name in ("product", "module", "object", "scenario", "boundary")},
            require_task5_semantic=True,
        )


def test_render_ledger_requires_raw_lineage_and_reports_tampering() -> None:
    source = SourceDoc(
        "src-test", "merchant system/test.md", "事实\n".encode("utf-8"), "事实\n", ("事实",),
        "merchant-system", "Merchant System", (
            {"evidence_id": "src-test-e0001", "start_line": 1, "end_line": 1, "text": "事实", "block_content_sha256": "a" * 64},
        ),
    )
    page = ReaderPage(
        source_id=source.source_id,
        title="测试页",
        question="问题",
        page_type="concept",
        axes={"product": "Merchant System", "module": "模块", "object": "对象", "scenario": "场景", "boundary": "边界"},
        sections={"summary": {"body": "事实", "evidence_ids": ("src-test-e0001",)}, **{heading: {"body": "事实", "evidence_ids": ("src-test-e0001",)} for heading in PAGE_TYPES["concept"]}},
        axis_evidence_ids={name: ("src-test-e0001",) for name in ("product", "module", "object", "scenario", "boundary")},
        page_id="src-test",
        page_key="source:src-test",
        relative_path="products/merchant-system/concept/测试页.md",
    )
    rows = [json.loads(line) for line in _render_evidence((source,), (page,), {"问题": (page,)}).decode("utf-8").splitlines()]
    assert rows and not _validate_render_ledger(
        rows,
        {
            page.relative_path: b"# page\n",
            "Home.md": b"# home\n",
            "bundle/Home.md": b"# home\n",
            "Audit.md": b'<a id="evidence-src-test-e0001"></a>\n',
        },
    )
    rows[0]["raw_hash"] = "0" * 64
    assert any(error.startswith("render_unit_lineage") or error.startswith("render_unit_raw_hash") for error in _validate_render_ledger(rows, {page.relative_path: b"# page\n", "Home.md": b"# home\n"}))


def test_slice_then_full_reuses_exact_source_prompt_in_one_context(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "first.md").write_text("# first\n", encoding="utf-8")
    (source / "second.md").write_text("# second\n", encoding="utf-8")
    output = tmp_path / "full"
    model = FakeModel()
    embedder = FakeEmbedder()

    result = digest_slice_then_full(
        DigestRequest(source, output, tmp_path / "unused.json", source_paths=("first.md",), evaluation_mode="slice"),
        DigestRequest(source, output, tmp_path / "unused.json", evaluation_mode="full"),
        (model, embedder),
    )

    assert result.full_result.outcome == "completed"
    assert result.slice_run_id
    assert result.full_run_id
    assert result.reused_response_count >= 1
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert run["run_context"]["slice_run_id"] == result.slice_run_id
    assert run["run_context"]["slice_llm_plan"] >= 1
    assert run["run_context"]["slice_embedding_plan"] >= 1
    assert run["provider_call_plan"]["max_total_requests"] >= (
        run["run_context"]["slice_llm_plan"] + run["run_context"]["slice_embedding_plan"]
    )


def test_digest_slice_uses_only_the_explicit_source_closure(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "first.md").write_text("# first\n", encoding="utf-8")
    (source / "second.md").write_text("# second\n", encoding="utf-8")
    output = tmp_path / "slice"

    result = digest(
        DigestRequest(
            source,
            output,
            tmp_path / "unused.json",
            source_paths=("first.md",),
            evaluation_mode="slice",
        ),
        (FakeModel(), FakeEmbedder()),
    )

    assert result.outcome == "completed"
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert run["evaluation_mode"] == "slice"
    assert run["source_selection"] == ["first.md"]
    assert run["source_count"] == 1
    assert not (output / "bundle" / "products" / "merchant-system" / "operation" / "second.md").exists()


def test_one_provider_failure_keeps_other_reader_pages_and_marks_audit(tmp_path: Path) -> None:
    source = tmp_path / "source" / "merchant system"
    source.mkdir(parents=True)
    (source / "good.md").write_text("## Good\n\n管理员可以查看终端。\n", encoding="utf-8")
    (source / "bad.md").write_text("## Bad\n\n这份资料本次不可用。\n", encoding="utf-8")
    output = tmp_path / "kb"

    result = digest(DigestRequest(tmp_path / "source", output, tmp_path / "unused.json"), (OneSourceUnavailableModel(), FakeEmbedder()))

    assert result.outcome == "not_released"
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert run["source_page_count"] == 1
    assert run["audit_only_count"] == 1
    assert run["raw_only_reader_source_count"] == 1
    audit = (output / "bundle" / "Audit.md").read_text(encoding="utf-8")
    assert "provider unavailable: provider request timed out" in audit
    assert "bad.md" in audit
    source_rows = [json.loads(line) for line in (output / "bundle" / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()]
    bad_row = next(row for row in source_rows if row["relative_path"].endswith("bad.md"))
    assert bad_row["status"] == "failed"
    assert "provider unavailable" in bad_row["failure"]["reason"]


def test_invalid_provider_config_is_blocked_before_publication(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "one.md").write_text("# One\n\n事实。\n", encoding="utf-8")
    output = tmp_path / "kb"
    config = tmp_path / "provider.json"
    config.write_text("{}\n", encoding="utf-8")

    result = digest(DigestRequest(source, output, config))

    assert result.outcome == "blocked"
    assert result.reason_code == "provider config needs llm and embedding objects"
    assert not (output / "bundle").exists()


def test_m402_gate_blocks_before_provider_or_raw_when_bindings_are_missing(tmp_path: Path) -> None:
    from knowledge_digest.compiler import DigestRequest

    result = digest(
        DigestRequest(
            tmp_path / "missing-raw",
            tmp_path / "downloads-run",
            tmp_path / "provider.json",
            gate="M402",
            runtime_config_path=tmp_path / "runtime.json",
            m401_packet_path=tmp_path / "missing-m401.json",
            m401_r_receipt_path=tmp_path / "missing-m401-r.json",
            workflowhub_successor_path=tmp_path / "missing-handoff.json",
            companybrain_root=tmp_path / "missing-companybrain",
        )
    )

    assert result.outcome == "blocked"
    assert result.reason_code == "M401 packet is missing"
    assert not (tmp_path / "downloads-run").exists()


def test_slice_then_full_m402_validates_gate_before_provider_or_companybrain(tmp_path: Path, monkeypatch) -> None:
    import knowledge_digest.compiler as compiler

    provider_build_called = False

    def fail_if_provider_built(_path):
        nonlocal provider_build_called
        provider_build_called = True
        raise AssertionError("provider construction must happen after M402 preflight")

    monkeypatch.setattr(compiler, "build_providers", fail_if_provider_built)
    request_common = {
        "gate": "M402",
        "runtime_config_path": tmp_path / "runtime.json",
        "m401_packet_path": tmp_path / "missing-m401.json",
        "m401_r_receipt_path": tmp_path / "missing-m401-r.json",
        "workflowhub_successor_path": tmp_path / "missing-handoff.json",
        "companybrain_root": tmp_path / "companybrain",
    }

    with pytest.raises(ValueError, match="M401 packet is missing"):
        compiler.digest_slice_then_full(
            DigestRequest(
                tmp_path / "raw",
                tmp_path / "downloads",
                tmp_path / "provider.json",
                source_paths=("first.md",),
                evaluation_mode="slice",
                **request_common,
            ),
            DigestRequest(
                tmp_path / "raw",
                tmp_path / "downloads",
                tmp_path / "provider.json",
                evaluation_mode="full",
                **request_common,
            ),
        )

    assert provider_build_called is False
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "companybrain").exists()
    assert not (tmp_path / "downloads").exists()


def test_m401_gate_requires_c3_fixture_before_touching_raw_or_provider(tmp_path: Path) -> None:
    from knowledge_digest.compiler import DigestRequest

    result = digest(
        DigestRequest(
            tmp_path / "must-not-read-raw",
            tmp_path / "must-not-write-kb",
            tmp_path / "must-not-read-provider-config.json",
            gate="M401",
            fixture_bundle_path=tmp_path / "missing-c3-bundle",
            m401_attempt_path=tmp_path / "M401",
            m401_run_root_path=tmp_path / "M401" / "run-root",
        )
    )

    assert result.outcome == "blocked"
    assert result.reason_code == "M401 fixture bundle is missing"
    assert not (tmp_path / "must-not-write-kb").exists()
    assert not (tmp_path / "M401").exists()


def test_m401_materializes_only_a_closed_fixture_and_records_real_rollback(tmp_path: Path, monkeypatch) -> None:
    import knowledge_digest.compiler as compiler

    fixture = tmp_path / "c3" / "bundle"
    audit = fixture / "_audit"
    audit.mkdir(parents=True)
    page_bytes = b"# One\n\nFixture page.\n"
    fixture_files = {
        "_audit/audit-pages.json": b'{"pages":[]}\n',
        "_audit/source-status.json": b'{"source_count":1,"sources":[]}\n',
        "_audit/companybrain-route-snapshot.json": b'{"schema_version":"knowledge-digest-companybrain-route-snapshot.v1"}\n',
        "_audit/semantic-compile-ledger.jsonl": b'{"status":"no_semantic_trace"}\n',
        "_audit/semantic-response-ledger.jsonl": b'{"status":"no_semantic_trace"}\n',
        "_audit/route-ledger.jsonl": b'{"query_id":"q1","status":"failed"}\n',
        "_audit/raw-coordinate-map.json": b'{"sources":[]}\n',
        "_audit/source-not-documented-zero-match.json": b'{"zero_match":true}\n',
        "_audit/source-not-documented-verifier.json": b'{"status":"passed"}\n',
        "products/goinsight/concept/one.md": page_bytes,
    }
    manifest = {
        "schema_version": "knowledge-digest-run-manifest.v1",
        "source_count": 1,
        "sources": [{
            "source_id": "source-1",
            "relative_path": "one.md",
            "product_key": "goinsight",
            "product_label": "GoInsight",
            "raw_hash": "a" * 64,
            "status": "ready",
            "source_digest_eligible": True,
            "duplicate_of": None,
            "evidence_ids": ["ev-1"],
            "reader_page_ids": ["source:source-1"],
            "failure": None,
        }],
        "routes": [{
            "query_id": "q1",
            "question": "q",
            "scene": "s",
            "route_name": "r",
            "product_key": "goinsight",
            "projection_id": "p",
            "candidate_source_ids": ["source-1"],
            "selected_source_ids": [],
            "selected_page_ids": [],
            "scores": {},
            "embedding_receipt": None,
            "qwen_payload_sha256": "",
            "evidence_bindings": [],
            "home_target_page_identity": "",
            "status": "failed",
            "failure": "fixture route is intentionally failed",
        }],
        "pages": [{
            "page_id": "source:source-1",
            "page_key": "source:source-1",
            "page_type": "concept",
            "axes": {
                "product": "GoInsight",
                "module": "未明确",
                "object": "未明确",
                "scenario": "未明确",
                "boundary": "未明确",
            },
            "source_ids": ["source-1"],
            "path": "products/goinsight/concept/one.md",
            "surface_sha256": compiler._sha(page_bytes),
            }],
        }
    fixture_files["_audit/route-ledger.jsonl"] = compiler._canonical_json(manifest["routes"][0])
    for relative, content in fixture_files.items():
        path = fixture / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    manifest["tree_sha256"] = compiler._tree_hash(fixture_files)
    trace_anchors = [
        "tests/test_simple_digest.py::test_home_routes_only_to_the_reader_role_that_matches_the_question",
        "tests/test_simple_digest.py::test_quality_surface_requires_an_explicit_reader_token",
        "tests/test_simple_digest.py::test_quality_embedding_order_is_consumed_by_qwen_closure",
        "tests/test_simple_digest.py::test_one_provider_failure_keeps_other_reader_pages_and_marks_audit",
        "tests/test_simple_digest.py::test_quality_result_blocks_ready_source_without_reader_page",
        "tests/test_simple_digest.py::test_candidate_quality_result_never_promotes_structural_wins",
        "tests/test_simple_digest.py::test_slice_then_full_reuses_exact_source_prompt_in_one_context",
        "tests/test_simple_digest.py::test_reader_tree_preserves_each_raw_product_root_and_page_type",
        "tests/test_simple_digest.py::test_public_secret_scan_blocks_before_atomic_publication",
        "tests/test_simple_digest.py::test_m402_gate_blocks_before_provider_or_raw_when_bindings_are_missing",
        "tests/test_simple_digest.py::test_render_ledger_requires_raw_lineage_and_reports_tampering",
        "tests/test_simple_digest.py::test_digest_adds_cross_source_product_entry_page",
        "tests/test_simple_digest.py::test_quality_contract_expands_to_all_frozen_projections",
    ]
    trace = [{
        "ac_id": f"AC-v4-{index:02d}",
        "evidence": {
            "command": "uv run --frozen python -",
            "input_snapshot": "c" * 40,
            "input_material": "d" * 64,
            "output_ref": "C3/run-root/bundle",
            "output_sha256": manifest["tree_sha256"],
            "actual_result": f"anchor={trace_anchors[index - 1]}; C3 fixture closure verified for AC-v4-{index:02d}",
            "failure_counterexample": f"anchor={trace_anchors[index - 1]}; Missing fixture closure for AC-v4-{index:02d} must stop M401.",
        },
    } for index in range(1, 14)]
    run = {
        "manifest": manifest,
        "quality_projection_count": 0,
        "snapshot_tree": "c" * 40,
        "material_id": "d" * 64,
        "m401_ac_trace": trace,
    }
    run["canonical_sha256"] = compiler._sha(compiler._canonical_json(run))
    run_bytes = (json.dumps(run, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    fixture_files["_audit/run-result.json"] = run_bytes
    directory = {
        "schema_version": "task5-directory-manifest.v1",
        "required_paths": [f"bundle/{relative}" for relative in compiler._FORMAL_PUBLIC_AUDIT_FILES],
        "files": [
            {"path": relative, "sha256": compiler._sha(content), "bytes": len(content), "lines": content.count(b"\n")}
            for relative, content in sorted(fixture_files.items(), key=lambda item: item[0].encode("utf-8"))
            if relative not in {"_audit/run-result.json", "_audit/directory-manifest.json"}
        ],
        "tree_sha256": manifest["tree_sha256"],
    }
    directory["canonical_sha256"] = compiler._sha(compiler._canonical_json(directory))
    directory_bytes = (json.dumps(directory, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    fixture_files["_audit/directory-manifest.json"] = directory_bytes
    for relative, content in fixture_files.items():
        (fixture / relative).write_bytes(content)

    # A trace that only names a logical output and invents its hash must fail
    # before M401 creates an attempt or run-root. This is the regression for
    # the previously accepted synthetic C3 trace.
    bad_run = json.loads(run_bytes.decode("utf-8"))
    bad_run["m401_ac_trace"][0]["evidence"]["output_ref"] = "C3/logical-output"
    bad_run["m401_ac_trace"][0]["evidence"]["output_sha256"] = "e" * 64
    bad_run.pop("canonical_sha256", None)
    bad_run["canonical_sha256"] = compiler._sha(compiler._canonical_json(bad_run))
    bad_run_bytes = (json.dumps(bad_run, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    (fixture / "_audit/run-result.json").write_bytes(bad_run_bytes)
    bad_attempt = tmp_path / "bad-attempt"
    bad_result = compiler.digest(compiler.DigestRequest(
        tmp_path / "raw-must-not-be-read",
        tmp_path / "public-must-not-be-written",
        tmp_path / "provider-must-not-be-read.json",
        gate="M401",
        fixture_bundle_path=fixture,
        m401_attempt_path=bad_attempt,
        m401_run_root_path=bad_attempt / "run-root",
    ))
    assert bad_result.outcome == "blocked"
    assert bad_result.reason_code == "M401 fixture AC trace is not verifiable"
    assert not bad_attempt.exists()

    (fixture / "_audit/run-result.json").write_bytes(run_bytes)
    legacy_audit = fixture / "_audit/sources.jsonl"
    legacy_audit.write_bytes(b'{"source_id":"source-1"}\n')
    legacy_attempt = tmp_path / "legacy-attempt"
    legacy_result = compiler.digest(compiler.DigestRequest(
        tmp_path / "raw-must-not-be-read",
        tmp_path / "public-must-not-be-written",
        tmp_path / "provider-must-not-be-read.json",
        gate="M401",
        fixture_bundle_path=fixture,
        m401_attempt_path=legacy_attempt,
        m401_run_root_path=legacy_attempt / "run-root",
    ))
    assert legacy_result.outcome == "blocked"
    assert legacy_result.reason_code == "M401 fixture bundle has unexpected audit files: _audit/sources.jsonl"
    assert not legacy_attempt.exists()
    legacy_audit.unlink()

    monkeypatch.setattr(
        compiler,
        "_m401_test_receipt",
        lambda *args, **kwargs: {"status": "passed", "receipt_kind": kwargs["receipt_kind"]},
    )
    attempt = tmp_path / "attempt"
    run_root = attempt / "run-root"
    result = compiler.digest(compiler.DigestRequest(
        tmp_path / "raw-must-not-be-read",
        tmp_path / "public-must-not-be-written",
        tmp_path / "provider-must-not-be-read.json",
        gate="M401",
        fixture_bundle_path=fixture,
        m401_attempt_path=attempt,
        m401_run_root_path=run_root,
        m401_command="[\"digest\",\"--gate\",\"M401\"]",
    ))

    assert result.outcome == "completed"
    assert (run_root / "bundle" / "Home.md").exists() is False
    packet_path = attempt / "M401-evidence-packet.json"
    attempt_receipt = json.loads((attempt / "attempt-receipt.json").read_text(encoding="utf-8"))
    packet_bytes = packet_path.read_bytes()
    assert attempt_receipt["packet_sha256"] == compiler._sha(packet_bytes)
    assert json.loads(packet_bytes)["run_root_sha256"] == compiler._m401_file_snapshot(
        compiler._regular_files(run_root / "bundle", "test bundle")
    )[1]
    assert (attempt / "inverse.patch").read_bytes()


def test_source_page_factual_violation_is_kept_out_of_reader(tmp_path: Path) -> None:
    source = tmp_path / "source" / "merchant system"
    source.mkdir(parents=True)
    (source / "one.md").write_text("## Terminal\n\n管理员可以查看终端。\n", encoding="utf-8")
    output = tmp_path / "kb"

    result = digest(DigestRequest(tmp_path / "source", output, tmp_path / "unused.json"), (SourceVerificationViolationModel(), FakeEmbedder()))

    assert result.outcome == "not_released"
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert run["source_page_count"] == 0
    assert run["audit_only_count"] == 1
    audit = (output / "bundle" / "Audit.md").read_text(encoding="utf-8")
    assert "quality verifier found factual violations" in audit
    source_rows = [json.loads(line) for line in (output / "bundle" / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()]
    assert source_rows[0]["failure"] is not None


def _verifier_source_and_page() -> tuple[SourceDoc, ReaderPage]:
    source = SourceDoc(
        source_id="src-verifier-test",
        relative_path="one.md",
        raw_bytes=b"fact",
        text="fact",
        lines=("fact",),
        product="EMM",
        product_label="EMM",
        evidence=({"evidence_id": "e1", "start_line": 1, "end_line": 1, "text": "fact"},),
    )
    sections = {"summary": {"body": "fact", "evidence_ids": ("e1",)}}
    sections.update({heading: {"body": "原始资料未明确", "evidence_ids": ()} for heading in PAGE_TYPES["concept"]})
    page = ReaderPage(
        source_id=source.source_id,
        title="事实页面",
        question="事实是什么？",
        page_type="concept",
        axes={"product": "EMM", "module": "模块", "object": "对象", "scenario": "场景", "boundary": "边界"},
        sections=sections,
    )
    return source, page


class _StaticVerifier:
    identity = {"model": "static-verifier"}
    calls = 0

    def __init__(self, response: str) -> None:
        self.response = response

    def generate(self, prompt: str) -> str:
        self.calls += 1
        return self.response


def test_verifier_collapses_duplicate_result_for_single_page() -> None:
    source, page = _verifier_source_and_page()
    model = _StaticVerifier(json.dumps({"results": [
        {"page_id": page.source_id, "violations": []},
        {"page_id": page.source_id, "violations": []},
    ]}))

    result = _verify_batch([page], {source.source_id: source}, model, attempts=1)

    assert list(result) == [page.source_id]
    assert result[page.source_id] == []


def test_verifier_rejects_non_object_violation_instead_of_dropping_it() -> None:
    source, page = _verifier_source_and_page()
    model = _StaticVerifier(json.dumps({"results": [{
        "page_id": page.source_id,
        "violations": ["unsupported"],
    }]}))

    with pytest.raises(ValueError, match="violation is malformed"):
        _verify_batch([page], {source.source_id: source}, model, attempts=1)


def test_digest_adds_cross_source_product_entry_page(tmp_path: Path) -> None:
    source = tmp_path / "source" / "emm for android "
    source.mkdir(parents=True)
    (source / "one.md").write_text("## One\n\n设备需要注册。\n", encoding="utf-8")
    (source / "two.md").write_text("## Two\n\n管理员配置设备。\n", encoding="utf-8")
    output = tmp_path / "kb"

    result = digest(DigestRequest(tmp_path / "source", output, tmp_path / "unused.json"), (FakeModel(), FakeEmbedder()))

    assert result.outcome == "completed"
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert run["source_page_count"] == 2
    assert run["topic_page_count"] == 1
    assert "EMM 产品定位与阅读入口" in (output / "bundle" / "Home.md").read_text(encoding="utf-8")
    audit = (output / "bundle" / "Audit.md").read_text(encoding="utf-8")
    assert audit.count("EMM 产品定位与阅读入口") == 3


def test_reader_tree_preserves_each_raw_product_root_and_page_type(tmp_path: Path) -> None:
    source = tmp_path / "source"
    for product in ("GoInsight", "emm for android ", "emm for ios", "merchant system"):
        directory = source / product
        directory.mkdir(parents=True)
        (directory / "说明.md").write_text("## 说明\n\n管理员可以查看并配置设备。\n", encoding="utf-8")
    output = tmp_path / "kb"

    result = digest(DigestRequest(source, output, tmp_path / "unused.json"), (FakeModel(), FakeEmbedder()))

    assert result.outcome == "completed"
    product_dirs = {path.name for path in (output / "bundle" / "products").iterdir() if path.is_dir()}
    assert {"goinsight", "emm-for-android", "emm-for-ios", "merchant-system"} <= product_dirs
    assert product_dirs <= {"goinsight", "emm-for-android", "emm-for-ios", "merchant-system", "shared"}
    reader_pages = [path for path in (output / "bundle" / "products").rglob("*.md") if path.name != "index.md"]
    assert reader_pages
    assert all(len(path.relative_to(output / "bundle").parts) == 4 for path in reader_pages)
    assert all(path.relative_to(output / "bundle").parts[2] in PAGE_TYPES for path in reader_pages)
    assert all("## 五轴分类" not in path.read_text(encoding="utf-8") for path in reader_pages)
    assert all("product:" in path.read_text(encoding="utf-8").split("---", 2)[1] for path in reader_pages)


def test_single_source_still_gets_product_and_diagnostic_entry_pages(tmp_path: Path) -> None:
    source = tmp_path / "source" / "goinsight"
    source.mkdir(parents=True)
    (source / "incident.md").write_text("## 故障排查\n\n查询失败时检查权限和数据集。\n", encoding="utf-8")
    output = tmp_path / "kb"

    result = digest(DigestRequest(tmp_path / "source", output, tmp_path / "unused.json"), (FakeModel(), FakeEmbedder()))

    assert result.outcome == "completed"
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert run["topic_page_count"] >= 2
    pages = list((output / "bundle" / "products" / "goinsight").rglob("*.md"))
    texts = [page.read_text(encoding="utf-8") for page in pages]
    assert sum("## 页面类型\n\n- 定位" in text for text in texts) == 1
    assert sum("## 页面类型\n\n- 诊断" in text for text in texts) == 1


def test_product_diagnosis_entry_is_added_even_when_planner_has_a_narrow_diagnosis(tmp_path: Path) -> None:
    source = tmp_path / "source" / "goinsight"
    source.mkdir(parents=True)
    (source / "migration.md").write_text("## 迁移故障\n\n迁移失败后需要排查并重试。\n", encoding="utf-8")
    (source / "query.md").write_text("## 查询异常\n\n查询失败时检查权限。\n", encoding="utf-8")
    output = tmp_path / "kb"

    result = digest(DigestRequest(tmp_path / "source", output, tmp_path / "unused.json"), (PlannerDiagnosisModel(), FakeEmbedder()))

    assert result.outcome == "completed"
    pages = list((output / "bundle" / "products" / "goinsight").rglob("*.md"))
    texts = [page.read_text(encoding="utf-8") for page in pages]
    assert sum("## 页面类型\n\n- 诊断" in text for text in texts) == 2


def test_experience_entry_is_kept_when_one_source_records_history(tmp_path: Path) -> None:
    source = tmp_path / "source" / "goinsight"
    source.mkdir(parents=True)
    (source / "retrospective.md").write_text("## 复盘\n\nSprint 回顾记录了改进方向。\n", encoding="utf-8")
    output = tmp_path / "kb"

    result = digest(DigestRequest(tmp_path / "source", output, tmp_path / "unused.json"), (FakeModel(), FakeEmbedder()))

    assert result.outcome == "completed"
    pages = list((output / "bundle" / "products" / "goinsight").rglob("*.md"))
    texts = [page.read_text(encoding="utf-8") for page in pages]
    assert sum("## 页面类型\n\n- 经验" in text for text in texts) == 1


def test_reader_boundary_redacts_credentials_but_keeps_field_names() -> None:
    text = _redact_reader_text(
        "服务账号 maxstore-emm@szzolon.com；password: abc123；字段 apiSecretToPaxstore。"
    )

    assert "maxstore-emm@szzolon.com" not in text
    assert "abc123" not in text
    assert "apiSecretToPaxstore" in text


def test_reader_boundary_redacts_common_key_and_bearer_formats() -> None:
    text = _redact_reader_text(
        "api_key: key-123；private_key=private-456；Authorization: Bearer bearer-789"
    )

    assert "key-123" not in text
    assert "private-456" not in text
    assert "bearer-789" not in text
    assert "api_key" in text
    assert "private_key" in text
    assert "Authorization: Bearer" in text


def test_evidence_splits_escaped_numbered_confluence_items() -> None:
    evidence = _paragraph_evidence(
        (
            "初始化策略效果",
            r"1 Apple ID",
            r"2\. Appearance",
            r"![](image.png)",
            r"3\. App Store",
            r"4\. Biometric",
        ),
        "src-example",
    )

    texts = [str(item["text"]) for item in evidence]
    assert any(r"2\. Appearance" in text for text in texts)
    assert any(r"3\. App Store" in text for text in texts)
    assert not any(r"2\. Appearance" in text and r"3\. App Store" in text for text in texts)


def test_aggregate_prompt_card_cannot_reference_omitted_evidence() -> None:
    card = {
        "summary": "摘要事实",
        "summary_evidence_ids": ["keep", "omit"],
        "sections": {"当前结论": {"body": "事实", "evidence_ids": ["keep", "omit"]}},
    }

    bounded = _restrict_prompt_card(card, {"keep"})

    assert bounded["summary_evidence_ids"] == ["keep"]
    assert bounded["summary"] == "原始资料未明确"
    assert bounded["sections"]["当前结论"]["evidence_ids"] == ["keep"]
    assert bounded["sections"]["当前结论"]["body"] == "原始资料未明确"


def test_reader_redaction_hides_machine_evidence_lists() -> None:
    assert "qev-" not in _redact_reader_text("开关 [qev-0123456789abcdef01234567, qev-abcdef012345678901234567]")


def test_digest_preserves_empty_and_duplicate_sources_without_fake_pages(tmp_path: Path) -> None:
    source = tmp_path / "source" / "merchant system"
    source.mkdir(parents=True)
    content = "## Terminal\n\n管理员可以查看终端。\n"
    (source / "one.md").write_text(content, encoding="utf-8")
    (source / "duplicate.md").write_text(content, encoding="utf-8")
    (source / "empty.md").write_text(" \n\n", encoding="utf-8")
    output = tmp_path / "kb"

    result = digest(DigestRequest(tmp_path / "source", output, tmp_path / "unused.json"), (FakeModel(), FakeEmbedder()))

    assert result.outcome == "not_released"
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert run["source_count"] == 3
    assert run["source_page_count"] == 1
    assert run["duplicate_source_count"] == 1
    assert run["audit_only_count"] == 1
    source_rows = {
        row["relative_path"]: row
        for row in (
            json.loads(line)
            for line in (output / "bundle" / "_audit" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        )
    }
    assert source_rows["merchant system/empty.md"]["status"] == "known_empty"
    assert source_rows["merchant system/empty.md"]["failure"]["reason"] == "known_empty_source"
    audit = (output / "bundle" / "Audit.md").read_text(encoding="utf-8")
    assert "source_kind: `duplicate_alias`" in audit
    assert "known_empty_source" in audit
    assert "Reader 页面：未生成" in audit


def test_quality_contract_expands_to_all_frozen_projections() -> None:
    root = Path(__file__).parents[1]
    projections = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )

    assert len(projections) == 12
    assert [item.projection_id for item in projections] == [
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
    ]


def test_quality_leaf_diagnosis_projections_inherit_shared_reader_contract() -> None:
    root = Path(__file__).parents[1]
    projections = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )
    by_id = {item.projection_id: item for item in projections}

    shared = by_id["Q-DIA-01.diagnosis"] if "Q-DIA-01.diagnosis" in by_id else None
    migration = by_id["Q-DIA-01.diagnosis.migration"]

    assert migration.guidance
    assert migration.repair_guidance
    assert migration.reader_markers
    assert "指标阈值" in migration.repair_guidance
    assert any("迁移任务完成条件" in str(item.get("marker", "")) for item in migration.reader_markers)
    assert shared is None


def test_quality_evidence_closure_includes_claim_and_boundary_line_refs() -> None:
    root = Path(__file__).parents[1]
    projections = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )
    sources = _load_sources(Path("/Users/Hugh/Downloads/confluence 原始数据"))
    by_path = {source.relative_path: source for source in sources}

    for projection in projections:
        evidence, evidence_ids, source_ids = _quality_evidence(projection, by_path)
        assert evidence
        assert len(evidence) == len(evidence_ids)
        assert set(projection.source_paths).issubset({row["source_path"] for row in evidence})
        assert source_ids

    query = next(item for item in projections if item.projection_id == "Q-DIA-01.diagnosis.query")
    assert any("#L29-L32::dataset-selection" in ref for ref in query.source_block_refs)
    assert any("点击数据集后重新回答" in str(item.get("text", "")) for item in _quality_evidence(query, by_path)[0])
    assert any("点击数据集后重新回答" in str(item.get("text", "")) for item in query.required_boundaries)

    augmented, _extra = _augment_quality_sources(sources, projections)
    assert sum(len(source.evidence) for source in augmented) > sum(len(source.evidence) for source in sources)


def test_quality_embedding_receives_only_route_metadata_not_source_text() -> None:
    root = Path(__file__).parents[1]
    projections = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )
    sources = _load_sources(Path("/Users/Hugh/Downloads/confluence 原始数据"))
    embedder = RecordingEmbedder()

    _quality_route_sources((projections[0],), sources, embedder)

    assert embedder.inputs
    assert all("canonical_text" not in item for item in embedder.inputs)
    assert all("raw_context" not in item for item in embedder.inputs)
    assert all(source.text not in item for source in sources for item in embedder.inputs)
    descriptor_count = len(embedder.inputs) - len(projections[:1])
    descriptors = [json.loads(item) for item in embedder.inputs[:descriptor_count]]
    assert all("content_sha256" in item for item in descriptors)


def test_reader_quality_obligations_use_typed_requirements_not_marker_inventory() -> None:
    root = Path(__file__).parents[1]
    projections = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )
    sources = _load_sources(Path("/Users/Hugh/Downloads/confluence 原始数据"))
    by_path = {source.relative_path: source for source in sources}
    projection = next(item for item in projections if item.projection_id == "Q-POS-01.positioning")
    evidence, _ids, _source_ids = _quality_evidence(projection, by_path)

    groups = reader_evidence_groups(projection, evidence)
    evidence_by_id = {str(item["evidence_id"]): item for item in evidence}
    assert all(group and all(item_id in evidence_by_id for item_id in group) for group in groups)
    assert groups == tuple(
        tuple(
            dict.fromkeys(
                str(item["evidence_id"])
                for ref in requirement.get("source_block_refs", ())
                for item in evidence
                if item.get("block_ref") == ref
            )
        )
        for requirement in (*projection.required_claims, *projection.required_boundaries)
        if item_reader_visible(requirement)
    )


def test_quality_rows_require_reader_audit_completion_and_companybrain_gap() -> None:
    root = Path(__file__).parents[1]
    projection = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )[0]
    page_path = "products/emm/positioning/answer.md"
    terms = []
    for rubric in projection.comparison_rubric.values():
        for field in ("required_atoms", "structure_markers"):
            terms.extend(str(item) for item in rubric.get(field, ()))
    page_text = """---
page_type: "定位"
product: "%s"
module: "%s"
object: "%s"
scenario: "%s"
boundary: "%s"
---

# 答案
<!-- digest_projection_id: %s -->

这页把产品定位、服务对象、产品关系和边界整理成一个可直接使用的答案。

## 当前结论
产品定位结论。

## 服务对象与入口
服务对象和入口说明。

## 产品关系与选择
产品关系和选择说明。

## 边界与未明确
边界和未明确事项。

%s
""" % (
        projection.axes["product"],
        projection.axes["module"],
        projection.axes["object"],
        projection.axes["scene"],
        projection.axes["boundary"],
        projection.projection_id,
        "\n".join(dict.fromkeys(terms)),
    )
    files = {
        page_path: page_text.encode("utf-8"),
        "Home.md": ("产品定位\n" + projection.projection_id).encode("utf-8"),
        "Audit.md": (
        f'<a id="page-{projection.projection_id}"></a>\n'
        '<a id="evidence-test"></a>\n'
        "来源 原始地址 原文 source_status"
        ).encode("utf-8"),
    }
    ledger_row = {
        "schema_version": "knowledge-digest-render-unit.v1",
        "unit_id": "u-test",
        "page_key": "answer:test:positioning",
        "page_path": page_path,
        "surface": "Reader.answer_body",
        "slot": "当前结论",
        "text_sha256": "a" * 64,
        "audit_ref": "Audit.md#evidence-test",
        "claim_ids": ["claim-test"],
        "evidence_ids": ["evidence-test"],
        "raw_source_id": "source-test",
        "raw_hash": "b" * 64,
        "block_id": "block-test",
        "claim_id": "claim-test",
        "locator": {"start_line": 1, "end_line": 1},
        "support_sha256": "c" * 64,
        "evidence_bindings": [{
            "raw_source_id": "source-test",
            "raw_hash": "b" * 64,
            "block_id": "block-test",
            "claim_id": "claim-test",
            "locator": {"start_line": 1, "end_line": 1},
            "support_sha256": "c" * 64,
        }],
        "home_target_page_identity": projection.projection_id,
    }
    gap_types = {
        "DIM-01.route": "unreachable",
        "DIM-02.taxonomy": "missing_taxonomy_axis",
        "DIM-03.business-answer": "missing_stage",
        "DIM-04.page-type": "untyped_contract",
        "DIM-05.reader-audit": "missing_provenance",
    }
    cb_rows = []
    for dimension, label in (
        ("DIM-01.route", "route"),
        ("DIM-02.taxonomy", "taxonomy"),
        ("DIM-03.business-answer", "business-answer"),
        ("DIM-04.page-type", "page-type"),
        ("DIM-05.reader-audit", "Reader-Audit"),
    ):
        rubric = projection.comparison_rubric[label]
        cb_rows.append({
            "case_id": projection.case_id,
            "projection_id": projection.projection_id,
            "dimension_id": dimension,
            "status": "absent",
            "score": None,
            "source_refs": ["CompanyBrain/page.md"],
            "visible_ref": "CompanyBrain/page.md#L1-L2",
            "audit_ref": None,
            "gap_ref": {
                "gap_type": gap_types[dimension],
                "gap_locator": "CompanyBrain/page.md#L1-L2",
                "gap_atom_refs": [
                    f"{projection.projection_id}::{dimension}::{atom}"
                    for atom in rubric["required_atoms"]
                ],
                "gap_stage_refs": [
                    f"{projection.projection_id}::{dimension}::stage::{marker}"
                    for marker in rubric["structure_markers"]
                ],
            },
            "kd_ref": None,
        })
    result = _quality_rows(
        (projection,),
        {projection.projection_id: (page_path, page_text)},
        blockers=(),
        companybrain_observation={"rows": cb_rows},
        ledger_rows=[ledger_row],
        route_ledger=[{
            "projection_id": projection.projection_id,
            "status": "ready",
            "selected_page_ids": [projection.projection_id],
            "home_target_page_identity": projection.projection_id,
        }],
        files=files,
    )
    assert [row["verdict"] for row in result["quality_rows"]] == ["KD_WIN"] * 5
    assert all(
        result["dimension_verdicts"][projection.projection_id][dimension] == ["KD_WIN", "UNKNOWN"]
        for dimension in ("DIM-01.route", "DIM-02.taxonomy", "DIM-03.business-answer", "DIM-04.page-type", "DIM-05.reader-audit")
    )
    assert all(row["advantage_basis"]["kd_completion_surfaces"] == ["Reader", "Audit"] for row in result["quality_rows"])

    # A CompanyBrain row marked absent without explicit gap atoms/stages is
    # not enough to claim a strict improvement for the whole dimension.
    for row in cb_rows:
        row["gap_ref"] = {**row["gap_ref"], "gap_atom_refs": [], "gap_stage_refs": []}
    incomplete_gap = _quality_rows(
        (projection,),
        {projection.projection_id: (page_path, page_text)},
        blockers=(),
        companybrain_observation={"rows": cb_rows},
        ledger_rows=[ledger_row],
        route_ledger=[{
            "projection_id": projection.projection_id,
            "status": "ready",
            "selected_page_ids": [projection.projection_id],
            "home_target_page_identity": projection.projection_id,
        }],
        files=files,
    )
    assert all(row["verdict"] == "UNKNOWN" for row in incomplete_gap["quality_rows"])


def test_quality_rows_accept_an_observed_partial_companybrain_gap() -> None:
    root = Path(__file__).parents[1]
    projection = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )[0]
    page_path = "products/emm/positioning/answer.md"
    rubric = projection.comparison_rubric["route"]
    page_text = "# 答案\n<!-- digest_projection_id: %s -->\n%s\n" % (
        projection.projection_id,
        "\n".join(dict.fromkeys([
            *(str(item) for item in rubric.get("required_atoms", ())),
            *(str(item) for item in rubric.get("structure_markers", ())),
        ])),
    )
    files = {
        page_path: page_text.encode("utf-8"),
        "Home.md": ("产品定位\n" + projection.projection_id).encode("utf-8"),
        "Audit.md": (
            f'<a id="page-{projection.projection_id}"></a>\n来源 原始地址 原文 source_status'
        ).encode("utf-8"),
    }
    ledger_row = {
        "schema_version": "knowledge-digest-render-unit.v1",
        "unit_id": "u-partial",
        "page_key": "answer:test:positioning",
        "page_path": page_path,
        "surface": "Reader.answer_body",
        "slot": "当前结论",
        "text_sha256": "a" * 64,
        "audit_ref": "Audit.md#evidence-partial",
        "claim_ids": ["claim-partial"],
        "evidence_ids": ["evidence-partial"],
        "raw_source_id": "source-partial",
        "raw_hash": "b" * 64,
        "block_id": "block-partial",
        "claim_id": "claim-partial",
        "locator": {"start_line": 1, "end_line": 1},
        "support_sha256": "c" * 64,
        "evidence_bindings": [{
            "raw_source_id": "source-partial",
            "raw_hash": "b" * 64,
            "block_id": "block-partial",
            "claim_id": "claim-partial",
            "locator": {"start_line": 1, "end_line": 1},
            "support_sha256": "c" * 64,
        }],
        "home_target_page_identity": projection.projection_id,
    }
    dimension = "DIM-01.route"
    atom_ids = [
        _comparison_atom_id(projection.projection_id, dimension, str(atom))
        for atom in rubric["required_atoms"]
    ]
    marker_ids = [
        f"{projection.projection_id}::{dimension}::stage::{marker}"
        for marker in rubric["structure_markers"]
    ]
    cb_rows = [{
        "case_id": projection.case_id,
        "projection_id": projection.projection_id,
        "dimension_id": dimension,
        "status": "absent",
        "score": None,
        "source_refs": ["CompanyBrain/page.md"],
        "visible_ref": "CompanyBrain/page.md#L1-L2",
        "audit_ref": None,
        "gap_ref": {
            "gap_type": "wrong_relation",
            "gap_locator": "CompanyBrain/page.md#L1-L2",
            "gap_atom_refs": atom_ids[:1],
            "gap_stage_refs": marker_ids[:1],
        },
        "kd_ref": None,
    }]
    result = _quality_rows(
        (projection,),
        {projection.projection_id: (page_path, page_text)},
        blockers=(),
        companybrain_observation={"rows": cb_rows},
        ledger_rows=[ledger_row],
        route_ledger=[{
            "projection_id": projection.projection_id,
            "status": "ready",
            "selected_page_ids": [projection.projection_id],
            "home_target_page_identity": projection.projection_id,
        }],
        files=files,
    )

    route_row = next(row for row in result["quality_rows"] if row["dimension_id"] == dimension)
    assert route_row["verdict"] == "KD_WIN"
    assert route_row["advantage_basis"]["gap_atom_refs"] == atom_ids[:1]
    assert route_row["advantage_basis"]["gap_stage_refs"] == marker_ids[:1]


def test_quality_observation_uses_reader_structure_not_literal_inventory() -> None:
    root = Path(__file__).parents[1]
    projection = load_quality_projections(
        root / "config" / "task5-quality-cases-v2.json",
        root / "config" / "task5-projection-rules-v1.json",
    )[1]
    page_path = "products/emm-for-android/concept/answer.md"
    page_text = """---
page_type: "概念"
product: "EMM for Android"
module: "策略与配置"
object: "通信和网络配置组与配置项"
scenario: "配置项查阅与不生效排查"
boundary: "Android 版本、托管模式与配置项状态"
digest_page_id: "Q-CON-01.concept"
---

# 策略与配置关系

这页把配置层级、生效条件和排查边界整理成一个可直接阅读的答案。

## 使用场景

管理员需要确认某个配置项作用在哪个设备环境，以及为什么没有生效。

## 对象与组成

策略包含通信和网络配置组，配置组再包含具体配置项。

## 关系与生效规则

Android 版本、托管模式和配置项状态共同影响最终是否生效。

## 边界与容易混淆

原始资料没有明确的地方保留为未明确，不把历史记录当成当前规则。
"""
    files = {
        page_path: page_text.encode("utf-8"),
        "Home.md": "EMM\n[策略与配置关系](products/emm-for-android/concept/answer.md)\n".encode("utf-8"),
        "Audit.md": (
            '<a id="page-Q-CON-01.concept"></a>\n'
            '<a id="evidence-semantic"></a>\n'
        ).encode("utf-8"),
    }
    ledger_row = {
        "page_path": page_path,
        "surface": "Reader.answer_body",
        "slot": "answer",
        "unit_id": "semantic-answer",
        "evidence_ids": ["evidence-semantic"],
        "audit_ref": "Audit.md#evidence-semantic",
    }
    observation = _quality_candidate_observation(
        projection,
        "DIM-02.taxonomy",
        {projection.projection_id: (page_path, page_text)},
        [ledger_row],
        (),
        files,
    )
    assert observation["passed"] is True
    assert observation["taxonomy_ok"] is True
    assert observation["missing_atoms"]


def test_quality_page_links_resolve_from_nested_page_directory() -> None:
    page = "products/emm/operation/zero-touch.md"

    assert _root_relative_prefix("products/emm/source.md") == "../../"
    assert _root_relative_prefix(page) == "../../../"
    assert _relative_page_link(page, "products/emm/source.md") == "../source.md"
    assert _relative_page_link(page, "products/emm/diagnosis/metric.md") == "../diagnosis/metric.md"


def test_quality_branch_publishes_source_coverage_and_projection_pages(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    output = tmp_path / "quality-kb"
    model = QualityFakeModel()
    embedder = FakeEmbedder()

    result = digest(
        DigestRequest(
            Path("/Users/Hugh/Downloads/confluence 原始数据"),
            output,
            tmp_path / "unused.json",
            root / "config" / "task5-quality-cases-v2.json",
        ),
        (model, embedder),
    )

    assert result.outcome == "not_released"
    assert result.reason_code == "run: companybrain_observation_missing"
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert run["source_count"] == 89
    assert run["source_page_count"] == 87
    assert run["quality_page_count"] == 12
    assert run["known_empty_sources"] == ["emm for android /AE - AirViewer厂商管理.md"]
    assert run["provider_calls"]["llm"] >= 111
    assert run["provider_calls"]["llm"] <= run["provider_call_plan"]["max_llm_requests"]
    assert set(run["quality_provider_trace"]) == {
        item.projection_id
        for item in load_quality_projections(
            root / "config" / "task5-quality-cases-v2.json",
            root / "config" / "task5-projection-rules-v1.json",
        )
    }
    assert all(run["quality_provider_trace"][key] for key in run["quality_provider_trace"])
    assert all(
        any(event.get("stage") == "generate" and event.get("status") == "passed" for event in events)
        for events in run["quality_provider_trace"].values()
    )
    reader_pages = [path for path in (output / "bundle" / "products").rglob("*.md") if path.name != "index.md"]
    assert len(reader_pages) == 99
    assert "qev-" not in "\n".join(path.read_text(encoding="utf-8") for path in reader_pages)
    nested = next(path for path in reader_pages if "/operation/" in path.as_posix())
    nested_text = nested.read_text(encoding="utf-8")
    assert "../../../Audit.md" in nested_text
    assert "../../../_audit/sources.jsonl" in nested_text
    assert "## 分类" not in nested_text
    assert "- 产品：" not in nested_text
    assert "- 模块：" not in nested_text
    assert "- 对象：" not in nested_text
    assert "- 场景：" not in nested_text
    assert "- 边界：" not in nested_text
    assert (output / "bundle" / "_audit" / "quality.json").is_file()
    quality = json.loads((output / "bundle" / "_audit" / "quality.json").read_text(encoding="utf-8"))
    assert all(route["top_k_scores"] for route in quality["routes"])
    assert all(route["embedding_input_sha256"] for route in quality["routes"])
    assert all(route["qwen_payload_sha256"] for route in quality["routes"])
    trace_by_id = quality["provider_trace"]
    for route in quality["routes"]:
        passed = next(
            event
            for event in reversed(trace_by_id[route["projection_id"]])
            if event.get("stage") in {"generate", "repair"} and event.get("status") == "passed"
        )
        assert route["qwen_payload_sha256"] == passed["qwen_payload_sha256"]
        assert passed["selected_source_paths"] == route["selected_source_paths"]
    manifest = run["manifest"]
    assert manifest["source_count"] == 89
    assert len(manifest["sources"]) == 89
    assert len(manifest["pages"]) == 99
    assert all(row["page_key"].startswith(("source:", "answer:")) for row in manifest["pages"])
    assert all(row["selected_source_ids"] for row in manifest["routes"])
    for route in manifest["routes"]:
        assert route["route_name"] in {
            "我想了解一个产品是什么、服务谁、怎么选以及边界",
            "我想理解一个模块、对象或配置项",
            "我想按步骤完成一项操作",
            "我遇到了问题，需要定位原因",
            "我想了解历史经验、版本和踩坑",
        }
        assert route["query_id"] == _question_id(
            route["question"],
            route["scene"],
            route["product_key"] + "\0" + route["projection_id"],
        )
        page = next(item for item in manifest["pages"] if item["page_id"] in route["selected_page_ids"])
        assert page["page_key"].split(":", 2)[1] == route["query_id"]
        assert isinstance(route["scores"], dict)
        assert set(route["embedding_receipt"]) == {
            "provider",
            "model",
            "request_identity",
            "selected_source_ids",
            "selected_closure_sha256",
            "response_sha256",
            "status",
        }
        assert route["embedding_receipt"]["status"] == "passed"
        assert route["embedding_receipt"]["selected_source_ids"] == route["selected_source_ids"]
    anchors = re.findall(r'<a id="([^"]+)"></a>', (output / "bundle" / "Audit.md").read_text(encoding="utf-8"))
    assert len(anchors) == len(set(anchors))
    assert not any(path.name in {"modules", "boundaries", "knowledge"} for path in output.rglob("*"))
    home = (output / "bundle" / "Home.md").read_text(encoding="utf-8")
    product_dirs = {path.name for path in (output / "bundle" / "products").iterdir() if path.is_dir()}
    assert {"goinsight", "emm-for-android", "emm-for-ios", "merchant-system", "shared"}.issubset(product_dirs)
    assert "products/emm-for-android/index.md" in home
    assert "products/emm-for-ios/index.md" in home
    assert "products/shared/index.md" in home
    assert "## 五轴分类" not in "\n".join(path.read_text(encoding="utf-8") for path in reader_pages)
    assert any("/shared/positioning/" in path.as_posix() for path in reader_pages)
    assert "products/merchant-system/index.md" in home
    assert "products/merchant-system-原始资料分类口径-与-maxstore-的产品归属未在本案例原文确认/index.md" not in home
    quality_bytes = (output / "bundle" / "_audit" / "quality.json").read_bytes()
    assert run["quality_sha256"] == hashlib.sha256(quality_bytes).hexdigest()


def test_tree_hash_covers_quality_but_excludes_only_recursive_run_receipts() -> None:
    assert _tree_hash({"_audit/quality.json": b"one"}) != _tree_hash({"_audit/quality.json": b"two"})
    assert _tree_hash({"_audit/run-result.json": b"one"}) == _tree_hash({"_audit/run-result.json": b"two"})
    assert _tree_hash({"_audit/run-result.receipt.json": b"one"}) == _tree_hash({"_audit/run-result.receipt.json": b"two"})


def test_companybrain_snapshot_uses_the_canonical_markdown_file_list_identity(tmp_path: Path) -> None:
    from knowledge_digest.companybrain_snapshot import build_companybrain_snapshot

    root = tmp_path / "companybrain"
    root.mkdir()
    (root / "b.md").write_text("B\n", encoding="utf-8")
    (root / "a.md").write_text("A\n", encoding="utf-8")
    (root / "ignored.json").write_text("not in the approved Markdown snapshot\n", encoding="utf-8")

    snapshot = build_companybrain_snapshot(root)
    entries = [
        {"relative_path": "a.md", "sha256": hashlib.sha256(b"A\n").hexdigest()},
        {"relative_path": "b.md", "sha256": hashlib.sha256(b"B\n").hexdigest()},
    ]
    expected = hashlib.sha256(
        (json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()
    assert snapshot["companybrain_tree_sha256"] == expected
    assert snapshot["companybrain_snapshot_id"] == f"cb-{expected[:24]}"


def test_quality_branch_rejects_source_pages_after_semantic_verification(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    output = tmp_path / "quality-kb-source-failure"

    result = digest(
        DigestRequest(
            Path("/Users/Hugh/Downloads/confluence 原始数据"),
            output,
            tmp_path / "unused.json",
            root / "config" / "task5-quality-cases-v2.json",
        ),
        (QualitySourceVerificationViolationModel(), FakeEmbedder()),
    )

    # Source pages are no longer sent through a second LLM verifier in the
    # simplified compiler. Quality answer pages still receive the independent
    # verifier; this model only flags source page IDs. The run is nevertheless
    # not released because a current CompanyBrain observation is absent.
    assert result.outcome == "not_released"
    assert result.reason_code == "run: companybrain_observation_missing"
    run = json.loads((output / "bundle" / "_audit" / "run-result.json").read_text(encoding="utf-8"))
    assert run["source_page_count"] == 87
    assert run["quality_page_count"] == 12
    assert run["known_empty_sources"] == ["emm for android /AE - AirViewer厂商管理.md"]
    assert "quality verifier found factual violations" not in (output / "bundle" / "Audit.md").read_text(encoding="utf-8")


def test_black_box_judgement_accepts_only_the_frozen_verdict_vocabulary() -> None:
    raw = {
        "projection_id": "Q-POS-01.positioning",
        "dimensions": {dimension: {"verdict": "A_WIN", "reason": "具体页面证据可回查"} for dimension in DIMENSIONS},
        "blocking_risks": [],
    }

    normal = _normalise_judgement(raw, False, "Q-POS-01.positioning")
    assert all(item["verdict"] == "KD_WIN" for item in normal["dimensions"].values())

    for bad in (
        {**raw, "projection_id": "Q-CON-01.concept"},
        {**raw, "dimensions": {**raw["dimensions"], "route": {"verdict": "KD_WIN"}}},
    ):
        try:
            _normalise_judgement(bad, False, "Q-POS-01.positioning")
        except ValueError:
            pass
        else:
            raise AssertionError("invalid blind-judge output was accepted")


def test_black_box_source_closure_accepts_exact_known_empty_as_an_audit_only_row() -> None:
    raw_hash = "a" * 64
    manifest = {
        "sources": [{
            "relative_path": "empty.md",
            "source_id": "source-empty",
            "raw_hash": raw_hash,
            "status": "known_empty",
            "reader_page_ids": [],
        }],
        "pages": [],
    }
    assert _source_page_closure(
        {"empty.md": raw_hash},
        {"empty.md": {"raw_hash": raw_hash, "status": "known_empty"}},
        {"manifest": manifest},
        {},
    ) == []
