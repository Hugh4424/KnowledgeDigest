"""Compare a KnowledgeDigest Reader candidate with the existing CompanyBrain tree."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


LINK = re.compile(r"(!?\[[^\]]*\])\(([^)\n]+)\)")
INTERNAL = re.compile(r"(?i)(sha256|content[_-]?fingerprint|digest[_-]?topic|source[_-]?id|reader signals)")


def _reader_metrics(root: Path) -> dict[str, Any]:
    bundle = root / "bundle"
    pages = sorted(bundle.glob("products/*/modules/*/knowledge/*.md"))
    products = sorted(path.name for path in (bundle / "products").iterdir() if path.is_dir())
    modules = sorted(
        f"{product.name}/{module.name}"
        for product in (bundle / "products").iterdir()
        if product.is_dir()
        for module in (product / "modules").iterdir()
        if module.is_dir() and module.name != "knowledge"
    )
    knowledge_types = sorted(
        f"{product.name}/{kind.name}"
        for product in (bundle / "products").iterdir()
        if product.is_dir()
        for kind in (product / "knowledge-types").iterdir()
        if kind.is_dir()
    )
    broken_links: list[str] = []
    leaks: list[str] = []
    line_limit: list[str] = []
    for path in sorted(bundle.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if INTERNAL.search(text):
            leaks.append(path.relative_to(bundle).as_posix())
        if len(text.splitlines()) > 300:
            line_limit.append(path.relative_to(bundle).as_posix())
        for match in LINK.finditer(text):
            target = match.group(2).strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "data:", "#")):
                continue
            target_path = (path.parent / target).resolve()
            try:
                target_path.relative_to(bundle.resolve())
            except ValueError:
                broken_links.append(f"{path.relative_to(bundle).as_posix()}->{target}")
                continue
            if not target_path.is_file():
                broken_links.append(f"{path.relative_to(bundle).as_posix()}->{target}")
    manifest_path = root / "audit/source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    quality_path = root / "reports/quality.json"
    quality = json.loads(quality_path.read_text(encoding="utf-8")) if quality_path.is_file() else {}
    by_product: dict[str, dict[str, Any]] = {}
    for entry in manifest.get("entries", []):
        product = entry.get("product", "unknown")
        row = by_product.setdefault(product, {"source_count": 0, "module_count": 0, "reader_page_count": 0})
        row["source_count"] += 1
        row["reader_page_count"] += len(entry.get("reader_paths", []))
    for product in products:
        by_product.setdefault(product, {})["module_count"] = sum(item.startswith(product + "/") for item in modules)
    return {
        "root": str(root),
        "source_count": manifest.get("source_count", 0),
        "failure_count": manifest.get("failure_count", 0),
        "product_count": len(products),
        "products": products,
        "module_count": len(modules),
        "knowledge_type_count": len(knowledge_types),
        "knowledge_page_count": len(pages),
        "product_overview_count": sum((bundle / "products" / product / "overview.md").is_file() for product in products),
        "semantic_candidate_count": quality.get("semantic_candidate_count", 0),
        "fidelity_only_count": quality.get("fidelity_only_count", 0),
        "quality_proxy": quality.get("score"),
        "reader_quality_proxy_passed": quality.get("reader_quality_proxy_passed"),
        "broken_links": broken_links,
        "internal_metadata_leaks": leaks,
        "line_limit_violations": line_limit,
        "by_product": by_product,
        "reader_category_layers": ["product", "knowledge_type", "module", "knowledge"],
    }


def _companybrain_metrics(root: Path) -> dict[str, Any]:
    products_root = root / "Products"
    products: dict[str, dict[str, Any]] = {}
    for product in sorted(path for path in products_root.iterdir() if path.is_dir()):
        files = sorted(product.rglob("*.md"))
        categories = {
            "product_positioning": (product / "产品定位").is_dir(),
            "module_manual": (product / "模块手册").is_dir(),
            "experience_and_pitfalls": (product / "经验与坑").is_dir(),
            "standards_and_assets": (product / "规范与资产").is_dir(),
            "scenario_index": (product / "使用场景索引.md").is_file(),
            "document_overview": (product / "文档总览.md").is_file(),
        }
        products[product.name] = {
            "markdown_file_count": len(files),
            "category_layers": [name for name, present in categories.items() if present],
            "categories": categories,
        }
    return {
        "root": str(root),
        "product_count": len(products),
        "products": products,
        "markdown_file_count": sum(item["markdown_file_count"] for item in products.values()),
        "category_layers": ["product_positioning", "module_manual", "experience_and_pitfalls", "standards_and_assets", "scenario_index"],
    }


def _markdown(reader: dict[str, Any], companybrain: dict[str, Any]) -> str:
    lines = [
        "# KnowledgeDigest 与 CompanyBrain 对比",
        "",
        "> 本报告只比较可观测结构、入口、覆盖和清洁度；两边来源规模不同，不把文件数直接当作知识质量分数。",
        "",
        "## 总体指标",
        "",
        "| 指标 | KnowledgeDigest | CompanyBrain |",
        "| --- | ---: | ---: |",
        f"| 产品数 | {reader['product_count']} | {companybrain['product_count']} |",
        f"| 知识/Markdown 文件 | {reader['knowledge_page_count']} 页 | {companybrain['markdown_file_count']} 个 |",
        f"| 模块数 | {reader['module_count']} | 未统一统计 |",
        f"| 知识类型数 | {reader['knowledge_type_count']} | 5 类常见目录 |",
        f"| 来源数 | {reader['source_count']} | 未统一统计 |",
        f"| 内部元数据泄漏 | {len(reader['internal_metadata_leaks'])} | 未统一统计 |",
        f"| 断链 | {len(reader['broken_links'])} | 未统一统计 |",
        "",
        "## 结构差异",
        "",
        f"- KnowledgeDigest 当前层级：`{' → '.join(reader['reader_category_layers'])}`。",
        f"- CompanyBrain 当前层级：`产品 → 产品定位/模块手册/经验与坑/规范与资产`，并有场景索引和文档总览。",
        "- 本次修复把“产品定位/模块手册/技术实现/经验与坑/规范与资产”变成产品下的可点击知识类型入口；它们是来源映射，不是模型凭空补写的产品结论。",
        "",
        "## KnowledgeDigest 产品分布",
        "",
        "| 产品 | 来源 | 模块 | Reader 页 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for product in reader["products"]:
        item = reader["by_product"].get(product, {})
        lines.append(f"| {product} | {item.get('source_count', 0)} | {item.get('module_count', 0)} | {item.get('reader_page_count', 0)} |")
    lines.extend([
        "",
        "## 结论",
        "",
        f"- 机器代理分：`{reader.get('quality_proxy')}`，门槛通过：`{reader.get('reader_quality_proxy_passed')}`。",
        f"- 语义整理页：`{reader.get('semantic_candidate_count')}`；保真整理页：`{reader.get('fidelity_only_count')}`。保真整理不是语义消化，不能冒充 CompanyBrain 式整理。",
        f"- 仍有 `{reader.get('fidelity_only_count')}` 条 `fidelity_only` 资料；它们只是保真整理，不等于模型语义消化，已在 Audit/报告中保留失败证据。" if reader.get("fidelity_only_count") else "- 89 条来源均有语义候选，但仍需按既有读者门确认事实保真，不能把机器结构分当成事实正确性。",
    ])
    return "\n".join(lines) + "\n"


def _diagnosis_markdown(reader: dict[str, Any]) -> str:
    semantic = int(reader.get("semantic_candidate_count") or 0)
    fidelity = int(reader.get("fidelity_only_count") or 0)
    total = semantic + fidelity
    return "\n".join([
        "# KnowledgeDigest 质量根因诊断",
        "",
        "## 直接证据",
        "",
        f"- 真实来源：{reader.get('source_count')} 条；Reader 逻辑页：{reader.get('knowledge_page_count')} 页；来源失败：{reader.get('failure_count')} 条。",
        f"- 语义整理：{semantic}/{total}；保真整理：{fidelity}/{total}。保真整理保留内容，但没有完成产品级归纳。",
        f"- 当前机器结构检查：{reader.get('reader_quality_proxy_passed')}；哈希/内部字段泄漏：{len(reader.get('internal_metadata_leaks', []))}；断链：{len(reader.get('broken_links', []))}。",
        "",
        "## 根因",
        "",
        f"1. 原流程把“来源完整”当成“知识已消化”：来源能落到页面、页数不超限、没有哈希泄漏，就可能得到高机器分；但本次仍有 {fidelity} 条资料是保真正文，所以原来的质量门没有挡住“原文堆放”。",
        "2. 原 Reader 投影没有把产品目录、知识类型和模块入口作为第一等输出，导致产品资料平铺或被单条候选路径分散；候选里的单来源模块名也会制造很多假模块。",
        "3. 修复前语义候选只覆盖部分来源；也没有稳定的批量语义编译和进度/失败证据，系统只能回退保真页，用户看到的是“跑完了”而不是“消化完成了”。本次已补固定批量、零重放和逐批失败记录。",
        "4. Reader 与 Audit 边界曾混在同一页：source id、hash、fingerprint 和运行字段进入正文，直接损害阅读体验；现在已移到 `audit/`，Reader 只保留简短来源入口。",
        "",
        "## 本次修复已经解决",
        "",
        "- 以顶层来源目录建立 4 个产品目录；产品下增加产品定位、模块手册、技术实现、经验与坑、规范与资产类型入口。",
        "- 用稳定的产品/模块/知识页路径承载 89 条来源；每条来源有唯一 `reader_paths`，超长页拆分并互链。",
        "- 清除 Reader 内部元数据，修复候选旧目录断链；质量报告增加断链检查。",
        "",
        "## 尚未冒充完成的部分",
        "",
        "- 这次真实包仍是 `not_released` candidate；没有把机器代理分 100 当成 CompanyBrain 等价质量。",
        f"- {fidelity} 条保真页仍需后续受控语义编译，才能真正达到“摘要、边界、经验、规范、模块知识”都经过消化的 80 分目标；这不是本次结构修复可以伪造的结果。" if fidelity else "- 89 条来源均有语义候选；仍需人工或固定读者门确认语义候选没有事实失真，不能把机器结构分当成事实正确性。",
        "",
    ]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reader", type=Path, required=True)
    parser.add_argument("--companybrain", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reader = _reader_metrics(args.reader.resolve())
    companybrain = _companybrain_metrics(args.companybrain.resolve())
    result = {"schema_version": "task3-reader-comparison.v1", "reader": reader, "companybrain": companybrain}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "comparison.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "COMPARISON.md").write_text(_markdown(reader, companybrain), encoding="utf-8")
    (args.output / "ROOT-CAUSE.md").write_text(_diagnosis_markdown(reader), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
