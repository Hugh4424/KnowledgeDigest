"""Compile raw KnowledgeDigest material into a reader-first bundle.

This is the high-level Task 3 seam.  It deliberately keeps provenance in
``audit`` and keeps the ``bundle`` suitable for a person to read.  It does
not claim that deterministic cleanup is semantic rewriting; a semantic
candidate is only used when its source URI and content fingerprint match.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .reader_frontmatter import parse_concept_document, serialize_concept_document


SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt", ".json"}
MAX_PAGE_LINES = 300
PART_BODY_LINES = 240
READER_QUALITY_THRESHOLD = 80
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_INTERNAL_LINE = re.compile(
    r"^(?:\s*(?:digest[_-]|content[_-]?fingerprint|source[_-]?id|topic[_-]?id|"
    r"provider[_-]|generated[_-]|reader[_-]?signals|machine[_-]?pass))",
    re.IGNORECASE,
)
_SOURCE_FOOTNOTE = re.compile(r"^\[\^[^\]]+\]:\s*(?:raw://|source[-_]|https?://)", re.IGNORECASE)
_HASH_TEXT = re.compile(r"(?i)(?:sha256|content[_-]?fingerprint|digest[_-]?topic|source[_-]?id)\s*[:=]?[`'\"]?[0-9a-f]{16,}")
_MARKDOWN_LINK = re.compile(r"(!?\[[^\]]*\])\(([^)\n]+)\)")


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    source_uri: str
    relative_path: str
    title: str
    product: str
    product_label: str
    module: str
    module_label: str
    knowledge_type: str
    knowledge_type_label: str
    knowledge_type_reason: str
    mapping_reason: str
    raw_text: str
    cleaned_body: str
    content_fingerprint: str
    line_count: int
    semantic_status: str
    semantic_body: str | None
    semantic_summary: str | None
    error: str | None = None
    integrity_status: str = "passed"
    integrity_details: tuple[str, ...] = ()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalize_label(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("\u00a0", " ")
    value = re.sub(r"\s+", " ", value).strip(" _-")
    return value or "未命名资料"


def _slug(value: str, fallback: str = "item") -> str:
    value = unicodedata.normalize("NFKC", value).strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[\\/]+", " ", value)
    value = re.sub(r"[^0-9a-z\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:80] or fallback


def _product_label(directory: str) -> tuple[str, str]:
    normalized = _normalize_label(directory)
    key = re.sub(r"\s+", " ", normalized).strip().lower()
    known = {
        "goinsight": ("goinsight", "GoInsight"),
        "emm for android": ("emm-for-android", "EMM for Android"),
        "emm for ios": ("emm-for-ios", "EMM for iOS"),
        "merchant system": ("merchant-system", "Merchant System"),
    }
    if key in known:
        return known[key]
    return _slug(normalized, "unclassified"), normalized


_MODULE_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("设备管理", "device-management", ("terminal", "设备", "airviewer", "ipad", "android")),
    ("应用管理", "app-management", ("app", "应用", "store", "开发者")),
    ("账号与权限", "identity-and-access", ("sso", "权限", "角色", "用户", "登录", "identity")),
    ("消息与邮件", "messaging-and-email", ("邮件", "email", "通知")),
    ("商户与支付", "merchant-and-payment", ("merchant", "商户", "payment", "支付", "小票", "processor")),
    ("日志与审计", "logs-and-audit", ("日志", "log", "audit", "activity")),
    ("策略与配置", "policy-and-configuration", ("策略", "policy", "配置", "settings", "规则")),
    ("数据与分析", "data-and-analytics", ("数据", "dashboard", "指标", "分析", "query", "goinsight")),
)

_KNOWN_MODULE_KEYS = {key for _label, key, _needles in _MODULE_RULES}


def _module_for(stem: str, body: str, semantic_module: str | None) -> tuple[str, str, str]:
    if isinstance(semantic_module, str) and semantic_module.strip():
        label = _normalize_label(semantic_module)
        return _slug(label, "general"), label, "semantic_candidate"
    haystack = f"{stem}\n{body[:3000]}".lower()
    for label, key, needles in _MODULE_RULES:
        if any(needle.lower() in haystack for needle in needles):
            return key, label, "keyword_mapping"
    return "general", "General knowledge", "fallback_general"


_KNOWLEDGE_TYPE_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("经验与坑", "experience-and-pitfalls", ("bug", "故障", "回归", "复盘", "retrospective", "retro", "release", "版本演进", "踩坑", "缺陷", "发布检查")),
    ("规范与资产", "standards-and-assets", ("规范", "policy", "参数", "文案", "协议", "标准", "properties", "资产")),
    ("产品定位与边界", "product-positioning", ("产品介绍", "产品定位", "产品总览", "产品关系", "产品价值", "背景介绍", "商业模式")),
    ("技术实现", "technical-implementation", ("api", "接口", "数据库", "clickhouse", "mysql", "架构", "部署", "server", "sdk", "环境", "flink", "迁移")),
)


def _knowledge_type_for(stem: str, body: str) -> tuple[str, str, str]:
    # Classify from the document title and opening heading first.  Searching
    # the whole body makes almost every operational note look like a bug,
    # policy, or configuration document merely because those words occur in a
    # copied example.
    opening = "\n".join(body.splitlines()[:8])
    haystack = f"{stem}\n{opening}".lower()
    for label, key, needles in _KNOWLEDGE_TYPE_RULES:
        if any(needle.lower() in haystack for needle in needles):
            return key, label, "keyword_mapping"
    return "module-manual", "模块手册", "fallback_module_manual"


def _rewrite_reader_links(
    body: str,
    *,
    bundle: Path,
    page_relative: str,
    source_relative: str,
    input_root: Path,
    source_first_paths: Mapping[str, str],
) -> str:
    """Keep external links, repair links to another raw source, drop stale links.

    Semantic candidates may contain links relative to their old candidate tree.
    Leaving those links in place creates dead Reader navigation, so an unknown
    non-URL target becomes plain link text instead of a false clickable link.
    """

    page_path = bundle / page_relative
    raw_path = input_root / source_relative

    def replace(match: re.Match[str]) -> str:
        label, target = match.groups()
        target = target.strip()
        if target.startswith("<") and ">" in target:
            target = target[1:target.index(">")]
        if target.startswith(("http://", "https://", "mailto:", "data:", "#")):
            return match.group(0)
        target_path, anchor = (target.split("#", 1) + [""])[:2] if "#" in target else (target, "")
        if not target_path:
            return match.group(0)

        bundle_target = (page_path.parent / target_path).resolve()
        try:
            bundle_target.relative_to(bundle.resolve())
        except ValueError:
            bundle_target = None
        if bundle_target is not None and bundle_target.is_file():
            return match.group(0)

        raw_target = (raw_path.parent / target_path).resolve()
        try:
            raw_relative = raw_target.relative_to(input_root.resolve()).as_posix()
        except ValueError:
            raw_relative = ""
        reader_target = source_first_paths.get(raw_relative)
        if reader_target:
            rewritten = os.path.relpath(bundle / reader_target, start=page_path.parent).replace(os.sep, "/")
            return f"{label}({rewritten}{('#' + anchor) if anchor else ''})"

        # Absolute Confluence paths and links into a previous candidate are not
        # valid local Reader links. Keep the visible label, lose the dead href.
        return label

    return _MARKDOWN_LINK.sub(replace, body)


def _strip_frontmatter(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalized.startswith("---\n"):
        closing = normalized.find("\n---\n", 4)
        if closing != -1:
            return normalized[closing + len("\n---\n"):]
    return normalized


def _clean_body(text: str, title: str) -> str:
    lines = _strip_frontmatter(text).splitlines()
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if _INTERNAL_LINE.match(line) or _SOURCE_FOOTNOTE.match(line):
            continue
        if stripped.startswith("<!--") and ("digest" in stripped.lower() or "hash" in stripped.lower()):
            continue
        cleaned.append(line.rstrip())
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    normalized_title = _normalize_label(title).casefold()
    if cleaned and re.match(r"^#\s+", cleaned[0]):
        first = re.sub(r"^#\s+", "", cleaned[0]).strip()
        if first.casefold() == normalized_title:
            cleaned.pop(0)
            while cleaned and not cleaned[0].strip():
                cleaned.pop(0)
    compact: list[str] = []
    blank = 0
    for line in cleaned:
        if not line.strip():
            blank += 1
            if blank > 2:
                continue
        else:
            blank = 0
        compact.append(line)
    body = "\n".join(compact).strip()
    return body


def _content_signatures(text: str) -> dict[str, int]:
    """Return small, deterministic signals for facts that must survive cleanup.

    This is deliberately a loss detector, not a semantic quality score.  It
    catches dropped executable code while allowing a semantic candidate to
    reorganize tables, links, version history and ordinary prose.
    """

    normalized = _strip_frontmatter(text)
    fenced = re.findall(r"```[^\n]*\n(.*?)```", normalized, re.DOTALL)
    code = "\n".join(fenced)
    return {
        # Semantic prose may turn tables and ordinary links into a clearer
        # explanation.  Executable code is different: dropping it is a hard
        # fact-loss signal, so only protected code artifacts are compared.
        "code_fence_markers": len(re.findall(r"^\s*```", normalized, re.MULTILINE)),
        "code_urls": len(re.findall(r"(?:https?://|mailto:)[^\s)]+", code, re.IGNORECASE)),
        "code_numeric_tokens": len(re.findall(r"(?<![\w])(?:v?\d+(?:[._:/-]\d+)+|\d{2,})(?![\w])", code, re.IGNORECASE)),
    }


def _content_integrity(raw_body: str, candidate_body: str) -> tuple[str, tuple[str, ...]]:
    required = _content_signatures(raw_body)
    actual = _content_signatures(candidate_body)
    missing = tuple(
        f"{key}:{actual[key]}/{required[key]}"
        for key in required
        if required[key] > actual[key]
    )
    return ("failed", missing) if missing else ("passed", ())


def _summary(body: str, title: str) -> str:
    for line in body.splitlines():
        value = line.strip()
        if not value or value.startswith("#") or value.startswith(("- ", "* ", "> ", "|")):
            continue
        value = re.sub(r"\s+", " ", value)
        value = re.sub(r"^目标[:：]\s*", "", value)
        if len(value) >= 8:
            value = _MARKDOWN_LINK.sub(lambda match: match.group(1).strip("[]!"), value)
            return value[:180].rstrip("。；;，,") + ("……" if len(value) > 180 else "。")
    return f"本页整理 {title} 的操作、规则或背景资料。"


def _source_uri(relative_path: str) -> str:
    return f"raw://confluence/{PurePosixPath(relative_path).as_posix()}"


def _source_id(source_uri: str, fingerprint: str) -> str:
    return "source-" + _sha256_text(source_uri + "\0" + fingerprint)[:20]


def _safe_read(path: Path) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except (OSError, UnicodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _load_semantic_candidate(candidate_root: Path | None) -> dict[str, dict[str, Any]]:
    if candidate_root is None:
        return {}
    root = Path(candidate_root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("semantic candidate must be a real directory")
    bundle = root / "bundle"
    if not bundle.is_dir():
        raise ValueError("semantic candidate must contain bundle/")
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(bundle.rglob("*.md")):
        try:
            frontmatter, body = parse_concept_document(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        sources = frontmatter.get("sources")
        if not isinstance(sources, list):
            continue
        source_entries = [item for item in sources if isinstance(item, Mapping)]
        for source in source_entries:
            uri = source.get("resource") or source.get("source_uri")
            fingerprint = source.get("digest_content_fingerprint") or source.get("content_fingerprint")
            if not isinstance(uri, str) or not uri.strip() or not isinstance(fingerprint, str) or not _SHA256.fullmatch(fingerprint):
                continue
            parts = path.relative_to(bundle).parts
            module = parts[3] if len(parts) >= 5 and parts[0] == "products" and parts[2] == "modules" else None
            result.setdefault(uri, {"fingerprint": fingerprint, "title": frontmatter.get("title"), "body": body, "summary": frontmatter.get("description"), "module": module, "path": path.as_posix()})
    return result


def _semantic_module_counts(semantic_map: Mapping[str, Mapping[str, Any]]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    prefix = "raw://confluence/"
    for source_uri, item in semantic_map.items():
        module = item.get("module")
        if not isinstance(module, str) or not module.strip() or not source_uri.startswith(prefix):
            continue
        relative = PurePosixPath(source_uri[len(prefix):])
        if len(relative.parts) < 2:
            continue
        product, _label = _product_label(relative.parts[0])
        key = _slug(module, "general")
        counts[(product, key)] = counts.get((product, key), 0) + 1
    return counts


def _unique_slug(value: str, used: set[str]) -> str:
    base = _slug(value, "knowledge")
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def _reader_document(*, title: str, description: str, status: str, body: str) -> str:
    frontmatter = {
        "description": description,
        "status": status,
        "title": title,
        "type": "KnowledgeDigest Knowledge",
    }
    return serialize_concept_document(frontmatter, body)


def _part_body(*, title: str, summary: str, chunk: list[str], index: int, total: int, previous: str | None, following: str | None, source_reference: str) -> str:
    page_title = title if total == 1 else f"{title}（第 {index}/{total} 部分）"
    lines = [f"# {page_title}", "", f"> {summary}", ""]
    if total > 1:
        lines.extend([f"> 本资料按阅读长度拆分为 {total} 个连续页面，当前为第 {index} 部分。", ""])
        navigation: list[str] = []
        if previous:
            navigation.append(f"[上一部分]({previous})")
        if following:
            navigation.append(f"[下一部分]({following})")
        if navigation:
            lines.extend([" · ".join(navigation), ""])
    visible_chunk = list(chunk)
    if visible_chunk and visible_chunk[0].strip().casefold() in {"## summary", "## 摘要"}:
        rest = visible_chunk[1:]
        while rest and not rest[0].strip():
            rest.pop(0)
        if rest and re.sub(r"\s+", " ", rest[0].strip()).casefold() == re.sub(r"\s+", " ", summary.strip()).casefold():
            visible_chunk = rest[1:]
    lines.extend(["## 摘要", "", summary, "", "## 详细内容", ""])
    lines.extend(visible_chunk)
    lines.extend(["", "## 来源", "", f"[查看来源入口](../../../../../{source_reference})", ""])
    return "\n".join(lines).strip() + "\n"


def _split_chunks(body: str) -> list[list[str]]:
    lines = body.splitlines()
    if not lines:
        return []
    return [lines[offset: offset + PART_BODY_LINES] for offset in range(0, len(lines), PART_BODY_LINES)]


def _write_product_pages(bundle: Path, product: str, label: str, documents: list[SourceDocument], source_references: Mapping[str, str]) -> tuple[int, int, dict[str, list[str]]]:
    product_root = bundle / "products" / product
    product_root.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[SourceDocument]] = {}
    for document in documents:
        grouped.setdefault(document.module, []).append(document)
    module_rows = sorted(grouped.items(), key=lambda item: item[0])
    overview_lines = [
        f"# {label}",
        "",
        "## 资料范围",
        "",
        f"本目录收录 {len(documents)} 条与 **{label}** 相关的资料，按模块整理。",
        "",
        "## 产品边界",
        "",
        "本页的产品归属依据来源目录和已冻结的来源映射；没有额外推断跨产品边界。需要具体事实时，请进入下方模块知识页并查看来源入口。",
        "",
        "## 模块入口",
        "",
    ]
    for module, rows in module_rows:
        overview_lines.append(f"- [{rows[0].module_label}](modules/{module}/index.md) — {len(rows)} 条资料")
    type_groups: dict[str, list[SourceDocument]] = {}
    for document in documents:
        type_groups.setdefault(document.knowledge_type, []).append(document)
    overview_lines.extend(["", "## 按知识类型", ""])
    for knowledge_type, rows in sorted(type_groups.items()):
        overview_lines.append(f"- [{rows[0].knowledge_type_label}](knowledge-types/{knowledge_type}/index.md) — {len(rows)} 条资料")
    (product_root / "overview.md").write_text("\n".join(overview_lines) + "\n", encoding="utf-8")
    index_lines = [f"# {label}", "", "- [产品总览](overview.md)", "- [模块索引](modules/index.md)", "", "## 按模块阅读", ""]
    for module, rows in module_rows:
        index_lines.append(f"- [{rows[0].module_label}](modules/{module}/index.md) — {len(rows)} 条资料")
    index_lines.extend(["", "## 按知识类型阅读", ""])
    for knowledge_type, rows in sorted(type_groups.items()):
        index_lines.append(f"- [{rows[0].knowledge_type_label}](knowledge-types/{knowledge_type}/index.md) — {len(rows)} 条资料")
    (product_root / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    module_index_root = product_root / "modules"
    module_index_root.mkdir(exist_ok=True)
    module_index_lines = [f"# {label} 模块索引", ""]
    page_count = 0
    page_paths: dict[str, list[str]] = {}
    type_entries: dict[str, list[tuple[str, str, str]]] = {}
    for module, rows in module_rows:
        module_label = rows[0].module_label
        module_index_lines.append(f"- [{module_label}]({module}/index.md) — {len(rows)} 条资料")
        module_root = module_index_root / module
        knowledge_root = module_root / "knowledge"
        knowledge_root.mkdir(parents=True, exist_ok=True)
        module_lines = [f"# {module_label}", "", f"本模块收录 {len(rows)} 条资料。", "", "## 知识页", ""]
        used: set[str] = set()
        page_entries: list[tuple[str, str, str]] = []
        for document in sorted(rows, key=lambda item: (item.title.casefold(), item.relative_path)):
            base = _unique_slug(document.title, used)
            chunks = _split_chunks(document.semantic_body or document.cleaned_body)
            if not chunks:
                continue
            if len(chunks) == 1:
                names = [f"{base}.md"]
            else:
                names = [f"{base}-part-{i:02d}.md" for i in range(1, len(chunks) + 1)]
            source_reference = source_references[document.source_id]
            summary = document.semantic_summary or _summary(document.semantic_body or document.cleaned_body, document.title)
            for i, chunk in enumerate(chunks, start=1):
                previous = names[i - 2] if i > 1 else None
                following = names[i] if i < len(names) else None
                rel = f"products/{product}/modules/{module}/knowledge/{names[i - 1]}"
                body = _part_body(title=document.title, summary=summary, chunk=chunk, index=i, total=len(chunks), previous=previous, following=following, source_reference=source_reference)
                status = "degraded" if document.semantic_status in {"fidelity_only", "unclassified", "candidate_mismatch", "semantic_empty", "semantic_fact_loss_fallback"} else "published"
                (knowledge_root / names[i - 1]).write_text(_reader_document(title=document.title, description=summary, status=status, body=body), encoding="utf-8")
                page_count += 1
            page_paths[document.source_id] = [
                f"products/{product}/modules/{module}/knowledge/{name}" for name in names
            ]
            type_entries.setdefault(document.knowledge_type, []).append(
                (document.title, page_paths[document.source_id][0], summary)
            )
            page_entries.append((document.title, names[0], summary))
        for title, name, summary in page_entries:
            module_lines.append(f"- [{title}](knowledge/{name}) — {summary}")
        (module_root / "index.md").write_text("\n".join(module_lines) + "\n", encoding="utf-8")
    (module_index_root / "index.md").write_text("\n".join(module_index_lines) + "\n", encoding="utf-8")
    type_root = product_root / "knowledge-types"
    for knowledge_type, entries in sorted(type_entries.items()):
        category_root = type_root / knowledge_type
        category_root.mkdir(parents=True, exist_ok=True)
        category_label = next(document.knowledge_type_label for document in documents if document.knowledge_type == knowledge_type)
        category_lines = [f"# {category_label}", "", f"本产品在此类型下收录 {len(entries)} 条资料。", "", "## 知识页", ""]
        for title, target, summary in sorted(entries, key=lambda item: item[0].casefold()):
            category_lines.append(f"- [{title}]({os.path.relpath(bundle / target, start=category_root).replace(os.sep, '/')}) — {summary}")
        (category_root / "index.md").write_text("\n".join(category_lines) + "\n", encoding="utf-8")
    return len(module_rows), page_count, page_paths


def _validate_no_reader_leaks(bundle: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(bundle.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if _HASH_TEXT.search(text):
            violations.append(f"HASH_OR_INTERNAL_METADATA:{path.relative_to(bundle).as_posix()}")
        if any(marker in text for marker in ("Reader signals", "digest_content_hash", "digest_topic_id", "content_fingerprint", "source_id:")):
            violations.append(f"INTERNAL_FIELD:{path.relative_to(bundle).as_posix()}")
    return violations


def _validate_reader_links(bundle: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(bundle.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in _MARKDOWN_LINK.finditer(text):
            target = match.group(2).strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "data:", "#")):
                continue
            target_path = (path.parent / target).resolve()
            try:
                target_path.relative_to(bundle.resolve())
            except ValueError:
                violations.append(f"NAVIGATION_ESCAPE:{path.relative_to(bundle).as_posix()}->{target}")
                continue
            if not target_path.is_file():
                violations.append(f"BROKEN_READER_LINK:{path.relative_to(bundle).as_posix()}->{target}")
    return violations


def _quality_score(*, bundle: Path, documents: list[SourceDocument], source_total: int, product_count: int, module_count: int, page_count: int, source_anchors: Mapping[str, str]) -> dict[str, Any]:
    reader_files = sorted(bundle.rglob("*.md"))
    knowledge_pages = sorted(bundle.glob("products/*/modules/*/knowledge/*.md"))
    valid = [document for document in documents if document.error is None and document.integrity_status == "passed"]
    coverage = len(valid) / source_total if source_total else 0.0
    required_structure = product_count > 0 and all(
        (path.is_file() for path in [bundle / "index.md", bundle / "products" / "index.md"])
    )
    product_entries = sum(1 for product in {document.product for document in documents} if (bundle / "products" / product / "overview.md").is_file() and (bundle / "products" / product / "index.md").is_file())
    expected_products = len({document.product for document in documents})
    structure = 20.0 if required_structure and module_count > 0 else 0.0
    product_entry = 15.0 * (product_entries / expected_products if expected_products else 0.0)
    leaks = _validate_no_reader_leaks(bundle)
    link_violations = _validate_reader_links(bundle)
    cleanliness = 15.0 if not leaks and not link_violations else max(0.0, 15.0 - min(15.0, float(len(leaks) + len(link_violations))))
    fidelity = 20.0 * (len(valid) / len(documents) if documents else 0.0)
    traceability = min(10.0, 10.0 * (len(source_anchors) / len(valid) if valid else 0.0))
    score = min(100.0, round(structure + 20.0 * coverage + product_entry + cleanliness + fidelity + traceability, 2))
    line_violations = [path.relative_to(bundle).as_posix() for path in reader_files if len(path.read_text(encoding="utf-8").splitlines()) > MAX_PAGE_LINES]
    return {
        "schema_version": "reader-quality-proxy.v1",
        "status": "passed" if score >= READER_QUALITY_THRESHOLD and not leaks and not link_violations and not line_violations else "failed",
        "score": score,
        "threshold": READER_QUALITY_THRESHOLD,
        "reader_quality_proxy_passed": score >= READER_QUALITY_THRESHOLD and not leaks and not link_violations and not line_violations,
        "components": {
            "structure": {"points": structure, "max": 20},
            "source_coverage": {"points": round(20.0 * coverage, 2), "max": 20, "valid": len(valid), "total": source_total},
            "product_entry": {"points": round(product_entry, 2), "max": 15, "passed": product_entries, "total": expected_products},
            "reader_cleanliness": {"points": cleanliness, "max": 15, "violations": leaks + link_violations},
            "content_fidelity": {"points": round(fidelity, 2), "max": 20, "passed": len(valid), "readable_documents": len(documents)},
            "traceability": {"points": round(traceability, 2), "max": 10, "mapped": len(source_anchors)},
        },
        "line_limit_violations": line_violations,
        "link_violations": link_violations,
        "reader_page_count": len(knowledge_pages),
    }


def _assert_output_root(output_root: Path) -> None:
    if not output_root.is_absolute():
        raise ValueError("output root must be absolute")
    if output_root.is_symlink():
        raise ValueError("output root must not be a symlink")
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError("output root must be new and empty")
    output_root.mkdir(parents=True, exist_ok=True)


def compile_reader_bundle(input_root: Path, output_root: Path, *, semantic_candidate: Path | None = None) -> dict[str, Any]:
    """Compile one raw source directory into a reader-first candidate."""

    input_root = Path(input_root).resolve()
    if input_root.is_symlink() or not input_root.is_dir():
        raise ValueError("input root must be a real directory")
    _assert_output_root(Path(output_root))
    output_root = Path(output_root).resolve()
    semantic_map = _load_semantic_candidate(semantic_candidate)
    semantic_module_counts = _semantic_module_counts(semantic_map)
    bundle = output_root / "bundle"
    audit = output_root / "audit"
    reports = output_root / "reports"
    bundle.mkdir()
    audit.mkdir()
    reports.mkdir()
    documents: list[SourceDocument] = []
    failures: list[dict[str, Any]] = []
    source_paths = [path for path in sorted(input_root.rglob("*")) if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in SUPPORTED_SUFFIXES]
    for path in source_paths:
        relative = path.relative_to(input_root).as_posix()
        raw, error = _safe_read(path)
        if raw is None:
            failure = {"relative_path": relative, "status": "failed", "reason": error or "unreadable"}
            failures.append(failure)
            continue
        raw_bytes = raw.encode("utf-8")
        fingerprint = _sha256_bytes(raw_bytes)
        uri = _source_uri(relative)
        source_id = _source_id(uri, fingerprint)
        parts = PurePosixPath(relative).parts
        if len(parts) > 1:
            product, product_label = _product_label(parts[0])
            product_reason = "top_level_directory"
        else:
            product, product_label, product_reason = "unclassified", "Unclassified", "unclassified_source"
        title_match = next((line[2:].strip() for line in raw.splitlines() if line.startswith("# ") and line[2:].strip()), None)
        title = _normalize_label(title_match or Path(relative).stem.replace("_", " "))
        cleaned = _clean_body(raw, title)
        if not cleaned:
            failures.append({
                "source_id": source_id,
                "relative_path": relative,
                "status": "failed",
                "reason": "empty_content",
                "source_uri": uri,
            })
            continue
        semantic = semantic_map.get(uri)
        semantic_body = None
        semantic_summary = None
        semantic_status = "fidelity_only"
        semantic_module = None
        mapping_reason = product_reason
        if semantic is not None:
            if semantic.get("fingerprint") == fingerprint:
                candidate_body = _clean_body(str(semantic.get("body") or ""), title)
                semantic_summary = _normalize_label(str(semantic.get("summary") or "")) if semantic.get("summary") else None
                semantic_module = semantic.get("module")
                semantic_body = candidate_body or None
                semantic_status = "semantic_candidate" if candidate_body else "semantic_empty"
                mapping_reason = "semantic_candidate"
            else:
                semantic_status = "candidate_mismatch"
        semantic_module_key = _slug(semantic_module, "general") if isinstance(semantic_module, str) else "general"
        if semantic_module_key not in _KNOWN_MODULE_KEYS and semantic_module_counts.get((product, semantic_module_key), 0) < 2:
            semantic_module = None
        module, module_label, module_reason = _module_for(Path(relative).stem, semantic_body or cleaned, semantic_module)
        if module_reason != "fallback_general":
            mapping_reason = f"{mapping_reason}+{module_reason}"
        if product == "unclassified":
            semantic_status = "unclassified" if semantic_status == "fidelity_only" else semantic_status
        integrity_status = "passed"
        integrity_details: tuple[str, ...] = ()
        if semantic_body:
            integrity_status, integrity_details = _content_integrity(cleaned, semantic_body)
            if integrity_status == "failed":
                failures.append({
                    "source_id": source_id,
                    "source_uri": uri,
                    "relative_path": relative,
                    "status": "failed",
                    "reason": "semantic_content_integrity_failed",
                    "details": list(integrity_details),
                })
                semantic_body = None
                semantic_status = "semantic_fact_loss_fallback"
        knowledge_type, knowledge_type_label, knowledge_type_reason = _knowledge_type_for(
            Path(relative).stem, semantic_body or cleaned
        )
        documents.append(SourceDocument(
            source_id,
            uri,
            relative,
            title,
            product,
            product_label,
            module,
            module_label,
            knowledge_type,
            knowledge_type_label,
            knowledge_type_reason,
            mapping_reason,
            raw,
            cleaned,
            fingerprint,
            len(raw.splitlines()),
            semantic_status,
            semantic_body,
            semantic_summary,
            integrity_status=integrity_status,
            integrity_details=integrity_details,
        ))
    source_anchors: dict[str, str] = {}
    used_anchors: set[str] = set()
    for document in documents:
        source_anchors[document.source_id] = _unique_slug(f"source-{document.title}", used_anchors)
    products: dict[str, list[SourceDocument]] = {}
    for document in documents:
        products.setdefault(document.product, []).append(document)
    bundle.mkdir(exist_ok=True)
    (bundle / "Home.md").write_text("# Home\n\n[Reader index](index.md)\n", encoding="utf-8")
    (bundle / "README.md").write_text("# KnowledgeDigest Reader\n\n这是本次运行生成的读者入口。审计字段和失败现场位于同级 `audit/`，本候选包尚未正式发布。\n\n- delivery_status: `not_released`\n", encoding="utf-8")
    product_lines = ["# Products", ""]
    root_lines = ["# Reader index", "", "知识按产品和模块组织。", "", "## Products", "", "- [Products](products/index.md)"]
    total_modules = 0
    total_pages = 0
    reader_paths: dict[str, list[str]] = {}
    source_references = {
        document.source_id: f"references/sources/{document.product}.md#{source_anchors[document.source_id]}"
        for document in documents
    }
    for product in sorted(products):
        rows = products[product]
        label = rows[0].product_label
        module_count, page_count, product_reader_paths = _write_product_pages(bundle, product, label, rows, source_references)
        total_modules += module_count
        total_pages += page_count
        reader_paths.update(product_reader_paths)
        product_lines.append(f"- [{label}]({product}/index.md) — {len(rows)} 条资料，{module_count} 个模块")
    (bundle / "products").mkdir(exist_ok=True)
    (bundle / "products" / "index.md").write_text("\n".join(product_lines) + "\n", encoding="utf-8")
    root_lines.extend(["", "## 统计", "", f"- 产品：{len(products)}", f"- 模块：{total_modules}", f"- 知识页：{total_pages}"])
    (bundle / "index.md").write_text("\n".join(root_lines) + "\n", encoding="utf-8")
    references = bundle / "references"
    references.mkdir()
    source_lines = ["# Sources", "", "按产品查看来源入口；完整指纹和运行证据在 `audit/source-manifest.json`。", ""]
    for product in sorted(products):
        rows = products[product]
        source_lines.append(f"- [{rows[0].product_label}](sources/{product}.md)")
    (references / "sources.md").write_text("\n".join(source_lines) + "\n", encoding="utf-8")
    source_dir = references / "sources"
    source_dir.mkdir()
    for product in sorted(products):
        source_rows = [products[product][0].product_label]
        source_rows.extend(["", "Reader 页面只显示简短入口；本页只保留来源名称和原始路径。", ""])
        for document in sorted(products[product], key=lambda item: item.relative_path):
            source_rows.extend([
                f"<a id=\"{source_anchors[document.source_id]}\"></a>",
                f"## {document.title}",
                f"- 原始路径：`{document.relative_path}`",
                f"- 资料状态：`{document.semantic_status}`",
                "",
            ])
        (source_dir / f"{product}.md").write_text("\n".join(source_rows) + "\n", encoding="utf-8")
    source_first_paths = {
        document.relative_path: reader_paths[document.source_id][0]
        for document in documents
    }
    for document in documents:
        for reader_path in reader_paths[document.source_id]:
            page = bundle / reader_path
            frontmatter, body = parse_concept_document(page.read_text(encoding="utf-8"))
            rewritten = _rewrite_reader_links(
                body,
                bundle=bundle,
                page_relative=reader_path,
                source_relative=document.relative_path,
                input_root=input_root,
                source_first_paths=source_first_paths,
            )
            page.write_text(serialize_concept_document(frontmatter, rewritten), encoding="utf-8")
    source_entries: list[dict[str, Any]] = []
    for document in sorted(documents, key=lambda item: item.relative_path):
        names = reader_paths[document.source_id]
        source_entries.append({"source_id": document.source_id, "source_uri": document.source_uri, "relative_path": document.relative_path, "title": document.title, "content_fingerprint": document.content_fingerprint, "line_count": document.line_count, "validation_status": document.integrity_status, "validation_reason": list(document.integrity_details), "product": document.product, "product_label": document.product_label, "module": document.module, "module_label": document.module_label, "knowledge_type": document.knowledge_type, "knowledge_type_label": document.knowledge_type_label, "knowledge_type_reason": document.knowledge_type_reason, "mapping_reason": document.mapping_reason, "reader_paths": names, "semantic_status": document.semantic_status})
    _write_json(audit / "source-manifest.json", {"schema_version": "reader-source-manifest.v2", "generated_at": _now(), "source_count": len(source_paths), "failure_count": len(failures), "entries": source_entries, "failures": failures})
    run_status = "degraded" if failures else "candidate"
    _write_json(audit / "run-manifest.json", {"schema_version": "reader-compiler-run.v1", "generated_at": _now(), "status": run_status, "input_root": str(input_root), "semantic_candidate": str(Path(semantic_candidate).resolve()) if semantic_candidate else None, "source_count": len(source_paths), "failure_count": len(failures)})
    quality = _quality_score(bundle=bundle, documents=documents, source_total=len(source_paths), product_count=len(products), module_count=total_modules, page_count=total_pages, source_anchors=source_anchors)
    quality["semantic_candidate_count"] = sum(document.semantic_status == "semantic_candidate" for document in documents)
    quality["fidelity_only_count"] = sum(document.semantic_status in {"fidelity_only", "unclassified", "candidate_mismatch", "semantic_empty", "semantic_fact_loss_fallback"} for document in documents)
    _write_json(reports / "quality.json", quality)
    _write_json(reports / "projection-report.json", {"schema_version": "reader-projection-report.v2", "status": quality["status"], "source_count": len(source_paths), "failure_count": len(failures), "product_count": len(products), "module_count": total_modules, "knowledge_type_count": len({document.knowledge_type for document in documents}), "reader_page_count": total_pages, "logical_entry_count": len(documents), "semantic_candidate_count": quality["semantic_candidate_count"], "fidelity_only_count": quality["fidelity_only_count"]})
    release_status = "not_released"
    _write_json(reports / "release-summary.json", {"schema_version": "reader-release-summary.v2", "delivery_status": release_status, "candidate_status": quality["status"], "reader_quality_score": quality["score"], "reason": "candidate requires existing Task3 summary confirmation and release readback" if not failures else "not_released: audit failures must be resolved before release", "human_reviewed": False})
    return {"status": "candidate", "delivery_status": release_status, "quality": quality, "source_count": len(source_paths), "failure_count": len(failures), "product_count": len(products), "module_count": total_modules, "knowledge_type_count": len({document.knowledge_type for document in documents}), "reader_page_count": total_pages, "output_root": str(output_root)}


__all__ = ["MAX_PAGE_LINES", "READER_QUALITY_THRESHOLD", "compile_reader_bundle"]
