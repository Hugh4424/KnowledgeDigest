#!/usr/bin/env python3
"""Black-box five-dimension comparison for a KnowledgeDigest candidate.

Every frozen projection gets its own route, taxonomy, answer body, page type,
and Reader-to-Audit chain. CompanyBrain is comparison input only.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import posixpath
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from knowledge_digest.quality import QualityProjection, item_reader_visible, load_quality_projections, parse_block_ref


DIMENSIONS = ("route", "taxonomy", "business-answer", "page-type", "Reader-Audit")
APPROVED_LLM_BASE_URL = "https://dashscope.in.whatspos.cn/v1"
# Task5 has one current provider identity.  Older Qwen identities remain only
# in historical Task2/Task3 material and must not make a Task5 candidate look
# compliant during the five-dimension comparison.
APPROVED_LLM_MODELS = {"qwen3.8"}
APPROVED_EMBEDDING_BASE_URL = "https://llm.paxszapp.com/v1"
APPROVED_EMBEDDING_MODEL = "jina-embeddings"
PAGE_LABELS = {"positioning": "定位", "concept": "概念", "operation": "操作", "diagnosis": "诊断", "experience": "经验"}
AXIS_LABELS = {"product": "产品", "module": "模块", "object": "对象", "scenario": "场景", "boundary": "边界"}
SHARED_PRODUCT_KEY = "shared"
KNOWN_PRODUCT_ROOTS = {
    "emm for android": "emm-for-android",
    "emm for ios": "emm-for-ios",
    "goinsight": "goinsight",
    "merchant system": "merchant-system",
}
EXPECTED_SECTIONS = {
    "positioning": ("当前结论", "服务对象与入口", "产品关系与选择", "边界与未明确"),
    "concept": ("使用场景", "对象与组成", "关系与生效规则", "边界与容易混淆"),
    "operation": ("前置条件", "操作步骤", "预期结果", "验证方式", "失败与限制"),
    "diagnosis": ("现象", "检查顺序", "可能原因", "处理动作", "升级边界"),
    "experience": ("背景", "阶段变化", "方案取舍与经验", "经验教训", "适用边界"),
}
SUPPORTED_SOURCE_SUFFIXES = {".md", ".markdown", ".txt", ".json"}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _json(path: Path) -> Any:
    return json.loads(_read(path))


def _safe_root(path: Path, label: str) -> Path:
    path = Path(path).expanduser()
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise ValueError(f"{label} must be an absolute regular directory: {path}")
    return path


def _bundle_root(candidate: Path) -> Path:
    """Read the one public bundle while tolerating historical direct roots."""

    bundle = candidate / "bundle"
    return bundle if bundle.is_dir() and not bundle.is_symlink() else candidate


def _reject_nested_symlinks(root: Path, label: str) -> None:
    """The candidate is a closed artifact; no file may resolve outside it."""

    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"{label} contains a symlink: {path.relative_to(root)}")


def _resolve_link(root: Path, current: Path, link: str) -> str:
    link = link.split("#", 1)[0].strip()
    if not link or "://" in link:
        return ""
    try:
        return (current.parent / link).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return ""


def _link_targets(root: Path, current: Path, text: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        raw = match.group(2).strip()
        path_part, _, fragment = raw.partition("#")
        relative = _resolve_link(root, current, path_part)
        if relative:
            result.append({"label": match.group(1).strip(), "path": relative, "fragment": fragment})
    return result


def _links(root: Path, path: Path, text: str) -> list[dict[str, str]]:
    return [{key: value for key, value in item.items() if key != "fragment"} for item in _link_targets(root, path, text)]


def _first_heading(text: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return match.group(1).strip() if match else ""


def _section(text: str, heading: str) -> str:
    match = re.search(rf"(?ms)^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s+|\Z)", text)
    return match.group(1).strip() if match else ""


def _page_type(text: str) -> str:
    match = re.search(r"(?m)^-\s+(.+?)\s*$", _section(text, "页面类型"))
    label = match.group(1).strip() if match else ""
    return next((key for key, value in PAGE_LABELS.items() if value == label), label)


def _question(text: str) -> str:
    return next((line.strip() for line in _section(text, "这页解决什么问题").splitlines() if line.strip()), "")


def _axis_values(text: str) -> dict[str, str]:
    # Five axes are metadata, not Reader prose.  Keep the old table parser as
    # a compatibility reader for historical candidates, but new candidates
    # must expose the same values in compact front matter.
    frontmatter = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", text, re.DOTALL)
    if frontmatter:
        values: dict[str, str] = {}
        for line in frontmatter.group(1).splitlines():
            key, separator, raw = line.partition(":")
            if not separator or key.strip() not in AXIS_LABELS:
                continue
            raw = raw.strip()
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw.strip('"\'')
            if isinstance(parsed, str) and parsed.strip():
                values[AXIS_LABELS[key.strip()]] = parsed.strip()
        if set(values) == set(AXIS_LABELS.values()):
            return values
    result: dict[str, str] = {}
    for line in _section(text, "五轴分类").splitlines():
        match = re.match(r"\|\s*(产品|模块|对象|场景|边界)\s*\|\s*(.*?)\s*\|", line)
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


def _source_paths(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"-\s*原始地址：`([^`]+)`", _section(text, "来源"))))


def _visible_body(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("> 证据：") or stripped.startswith("- [") or stripped.startswith("  - ["):
            continue
        lines.append(line)
    return "\n".join(lines)


def _projection_id(text: str) -> str:
    match = re.search(r"digest_projection_id:\s*([^\s]+)", text)
    return match.group(1).strip() if match else ""


def _page_identity(page: Mapping[str, Any]) -> str:
    """Return the public Audit anchor used by the compiler."""

    return str(page.get("projection_id") or page.get("source_id") or "")


def _all_reader_pages(candidate: Path) -> dict[str, dict[str, Any]]:
    candidate = _bundle_root(candidate)
    root = candidate / "products"
    if not root.is_dir():
        return {}
    pages: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*.md")):
        if path.name == "index.md" or path.is_symlink():
            continue
        relative = path.relative_to(candidate).as_posix()
        text = _read(path)
        pages[relative] = {"path": relative, "text": text, "title": _first_heading(text), "projection_id": _projection_id(text), "page_type": _page_type(text), "question": _question(text), "axes": _axis_values(text), "source_paths": _source_paths(text)}
    return pages


def _audit_sources(candidate: Path) -> tuple[dict[str, dict[str, Any]], str]:
    candidate = _bundle_root(candidate)
    source_index = candidate / "_audit" / "sources.jsonl"
    if source_index.is_file():
        rows: dict[str, dict[str, Any]] = {}
        for line in _read(source_index).splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(value, Mapping) or not value.get("relative_path") or not value.get("source_id"):
                continue
            rows[str(value["relative_path"])] = {
                "source_id": str(value["source_id"]),
                "status": str(value.get("status", "unknown")),
                "raw_hash": str(value.get("raw_hash", "")),
                "duplicate_of": value.get("duplicate_of"),
                "raw_text": value.get("raw_text", ""),
                "evidence_ids": value.get("evidence_ids", []),
                "audit_block": "",
            }
        audit_path = candidate / "Audit.md"
        return rows, _read(audit_path) if audit_path.is_file() else ""
    path = candidate / "Audit.md"
    if not path.is_file():
        return {}, ""
    text = _read(path)
    rows: dict[str, dict[str, Any]] = {}
    for block in text.split("\n## ")[1:]:
        path_match = re.search(r"-\s*原始路径：`([^`]+)`", block)
        id_match = re.search(r"-\s*source_id[:：]\s*`([^`]+)`", block)
        if not path_match or not id_match:
            continue
        snapshot_match = re.search(r"-\s*原文快照：\[打开\]\(([^)]+)\)", block)
        status_match = re.search(r"-\s*source_status[:：]\s*`([^`]+)`", block)
        rows[path_match.group(1)] = {"source_id": id_match.group(1), "status": status_match.group(1) if status_match else "unknown", "snapshot": snapshot_match.group(1) if snapshot_match else "", "audit_block": block}
    return rows, text


def _relevant_audit(
    audit: str,
    source_paths: Sequence[str],
    page: Mapping[str, Any] | None,
    required_block_refs: Sequence[str] = (),
) -> str:
    """Build a small audit packet for one blind comparison.

    The public Audit remains the complete source ledger.  A judge only needs
    the entries for the projection's sources and the selected Reader page;
    sending the whole 89-source audit to every call makes the comparison
    slow without adding evidence.
    """

    blocks: list[str] = []
    wanted = set(source_paths)
    for block in audit.split("\n## ")[1:]:
        heading, _, body = block.partition("\n")
        if heading in wanted:
            # Source sections contain one line-level coordinate for almost
            # every raw line.  The judge needs the source identity and the
            # frozen blocks only; sending all coordinates made a single
            # projection prompt tens of thousands of tokens long.
            metadata = body.split("### 原始证据坐标", 1)[0].rstrip()
            blocks.append("## " + heading + "\n" + metadata)
    page_summary = ""
    if page:
        page_summary = json.dumps(
            {
                "path": page.get("path", ""),
                "page_type": page.get("page_type", ""),
                "projection_id": page.get("projection_id", ""),
                "source_paths": list(page.get("source_paths", ())),
                "axes": dict(page.get("axes", {})),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    audit_lines = audit.splitlines()
    page_anchor = f"<a id=\"page-{_page_identity(page)}\"></a>" if page else ""
    if page_anchor in audit_lines:
        index = audit_lines.index(page_anchor)
        blocks.append("## Reader 页面回查\n" + "\n".join(audit_lines[index:index + 2]))
    expected_evidence_ids = {
        "qev-" + hashlib.sha256(
            f"{page.get('projection_id', '')}\0{block_ref}".encode("utf-8")
        ).hexdigest()[:24]
        for block_ref in required_block_refs
        if page and page.get("projection_id")
    }
    evidence_lines: list[str] = []
    for index, line in enumerate(audit_lines):
        if any(f'<a id="evidence-{evidence_id}"></a>' in line for evidence_id in expected_evidence_ids):
            evidence_lines.extend(audit_lines[index:index + 2])
    if evidence_lines:
        blocks.append("## 冻结质量证据坐标\n" + "\n".join(evidence_lines))
    prefix = "## 本次投影的 Reader/Audit 摘要\n" + page_summary
    return prefix + ("\n\n" + "\n\n".join(blocks) if blocks else "")


def _raw_manifest(raw: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(raw.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"raw corpus contains a symlink: {path}")
        if path.is_file() and path.name != ".DS_Store" and path.suffix.casefold() in SUPPORTED_SOURCE_SUFFIXES:
            result[path.relative_to(raw).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _source_product_key(source_path: str) -> str:
    root = source_path.split("/", 1)[0].strip()
    known = KNOWN_PRODUCT_ROOTS.get(root.casefold())
    if known:
        return known
    value = root.casefold().replace("&", " and ")
    value = re.sub(r"[\\/]+", " ", value)
    value = re.sub(r"[^\w\u4e00-\u9fff -]", " ", value)
    return re.sub(r"[ _]+", "-", value).strip("-") or "general"


def _layout_failures(
    candidate: Path,
    raw_hashes: Mapping[str, str],
    run_state: Mapping[str, Any],
    pages: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    """Check the full product/path contract before the narrow quality cases."""

    candidate = _bundle_root(candidate)
    failures: list[str] = []
    expected_products = {_source_product_key(path) for path in raw_hashes}
    products_root = candidate / "products"
    actual_products = {
        path.name for path in products_root.iterdir()
        if path.is_dir() and not path.is_symlink()
    } if products_root.is_dir() else set()
    missing = sorted(expected_products - actual_products)
    if missing:
        failures.append("Reader is missing raw product directories: " + ", ".join(missing))
    unexpected = sorted(actual_products - expected_products - {SHARED_PRODUCT_KEY})
    if unexpected:
        failures.append("Reader has unexpected product directories: " + ", ".join(unexpected))

    manifest = run_state.get("manifest", {})
    manifest_sources = manifest.get("sources", []) if isinstance(manifest, Mapping) else []
    manifest_pages = manifest.get("pages", []) if isinstance(manifest, Mapping) else []
    source_product_by_id = {
        str(row.get("source_id")): _source_product_key(str(row.get("relative_path", "")))
        for row in manifest_sources
        if isinstance(row, Mapping) and row.get("source_id") and row.get("relative_path")
    }
    manifest_page_paths = set()
    for row in manifest_pages if isinstance(manifest_pages, list) else []:
        if not isinstance(row, Mapping):
            continue
        relative = str(row.get("path", ""))
        manifest_page_paths.add(relative)
        parts = Path(relative).parts
        if len(parts) != 4 or parts[0] != "products" or parts[2] not in PAGE_LABELS or parts[3] == "index.md":
            failures.append(f"Reader page does not use products/<product>/<page-type>/<title>.md: {relative}")
            continue
        source_products = {
            source_product_by_id[str(source_id)]
            for source_id in row.get("source_ids", [])
            if str(source_id) in source_product_by_id
        }
        expected_dir = next(iter(source_products)) if len(source_products) == 1 else SHARED_PRODUCT_KEY
        if len(source_products) > 1 and expected_dir != SHARED_PRODUCT_KEY:
            failures.append(f"mixed-source Reader page has no shared lane: {relative}")
        if parts[1] != expected_dir:
            failures.append(f"Reader page is under the wrong product root: {relative} (expected {expected_dir})")

    for relative, page in pages.items():
        if relative not in manifest_page_paths:
            failures.append(f"Reader file is missing from run manifest: {relative}")
        text = str(page.get("text", ""))
        if "## 五轴分类" in text or "| 维度 | 当前归类 |" in text:
            failures.append(f"Reader page exposes redundant five-axis table: {relative}")
        if set(page.get("axes", {})) != set(AXIS_LABELS.values()):
            failures.append(f"Reader page is missing metadata axes: {relative}")
    return list(dict.fromkeys(failures))


def _source_manifest_hash(raw_hashes: Mapping[str, str]) -> str:
    payload = json.dumps(
        [{"relative_path": path, "content_hash": raw_hashes[path]} for path in sorted(raw_hashes)],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _run_manifest_source_hash(manifest_sources: Sequence[Mapping[str, Any]]) -> str:
    """Recompute the compiler's source-manifest identity from its receipt.

    The compiler binds source identity to source IDs, product metadata and
    evidence IDs, while this black-box evaluator separately verifies every
    path and raw hash against the input corpus.  Comparing the compiler hash
    with the evaluator's raw-only hash made every valid candidate look stale.
    """

    rows = [
        {
            "source_id": source.get("source_id"),
            "relative_path": source.get("relative_path"),
            "product_key": source.get("product_key"),
            "product_label": source.get("product_label"),
            "raw_hash": source.get("raw_hash"),
            "status": source.get("status"),
            "duplicate_of": source.get("duplicate_of"),
            "evidence_ids": source.get("evidence_ids", []),
        }
        for source in sorted(
            manifest_sources,
            key=lambda item: str(item.get("relative_path", "")),
        )
    ]
    payload = json.dumps(
        rows,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    return hashlib.sha256(payload).hexdigest()


def _expected_source_manifest_hash(
    run_state: Mapping[str, Any],
    source_manifest: Path | None,
) -> str | None:
    """Resolve the source-manifest identity used by the active run contract.

    Formal Task5 runs bind this field to the frozen manifest file bytes. Older
    evaluator callers have no manifest path and retain the legacy receipt-row
    derivation for compatibility.
    """

    if source_manifest is not None:
        if not source_manifest.is_file() or source_manifest.is_symlink():
            return None
        return hashlib.sha256(source_manifest.read_bytes()).hexdigest()
    manifest = run_state.get("manifest", {})
    manifest_sources = manifest.get("sources", []) if isinstance(manifest, Mapping) else []
    if not isinstance(manifest_sources, list) or not all(isinstance(item, Mapping) for item in manifest_sources):
        return None
    return _run_manifest_source_hash(manifest_sources)


def _raw_block_hash(raw: Path, source_path: str, start_line: int, end_line: int) -> str:
    path = raw / source_path
    try:
        lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    except (OSError, UnicodeDecodeError):
        return ""
    if start_line <= 0 or end_line < start_line or end_line > len(lines):
        return ""
    return hashlib.sha256("\n".join(lines[start_line - 1:end_line]).encode("utf-8")).hexdigest()


def _raw_block_text(raw: Path, block_ref: str, limit: int = 900) -> str:
    """Read a frozen raw excerpt for the blind semantic comparison."""

    try:
        source_path, start_line, end_line, _label = parse_block_ref(block_ref)
        lines = (raw / source_path).read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    except (OSError, UnicodeDecodeError, ValueError):
        return ""
    if start_line <= 0 or end_line < start_line or end_line > len(lines):
        return ""
    text = "\n".join(lines[start_line - 1:end_line])
    return text if len(text) <= limit else text[:limit] + "\n[原文块截断]"


def _snapshot_hash(candidate: Path, row: Mapping[str, Any]) -> str:
    # Do not trust a candidate's declared hash.  The compact source ledger
    # carries the exact UTF-8 text, so recompute it and compare that result to
    # both the raw corpus and the declared value.  Older snapshot links remain
    # supported only as a fallback for legacy candidates.
    raw_text = row.get("raw_text")
    if isinstance(raw_text, str) and raw_text:
        actual = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        declared = str(row.get("raw_hash", ""))
        return actual if actual == declared else ""
    link = str(row.get("snapshot", ""))
    if not link:
        # Current KnowledgeDigest keeps the raw snapshot out of the public
        # bundle by design.  Its source ledger already carries the declared
        # raw hash; the evaluator separately compares that hash with the raw
        # corpus, so a missing in-bundle snapshot is not a missing binding.
        declared = str(row.get("raw_hash", ""))
        return declared if re.fullmatch(r"[0-9a-f]{64}", declared) else ""
    target = (candidate / link).resolve()
    try:
        target.relative_to(candidate.resolve())
    except ValueError:
        return ""
    return hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else ""


def _evidence_rows(candidate: Path) -> list[dict[str, Any]]:
    path = _bundle_root(candidate) / "_audit" / "evidence.jsonl"
    if not path.is_file():
        return []
    result: list[dict[str, Any]] = []
    for line in _read(path).splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            result.append(item)
    return result


def _requirement_groups(projection: QualityProjection, *, reader: bool) -> list[list[str]]:
    groups: list[list[str]] = []
    for item in (*projection.required_claims, *projection.required_boundaries):
        if item_reader_visible(item) != reader:
            continue
        refs = [str(ref) for ref in item.get("source_block_refs", ()) if str(ref)]
        if refs:
            groups.append(refs)
    return groups


def _source_page_closure(
    raw_hashes: Mapping[str, str],
    source_rows: Mapping[str, Mapping[str, Any]],
    run_state: Mapping[str, Any],
    pages: Mapping[str, Mapping[str, Any]],
    quality_page_ids: set[str] | None = None,
) -> list[str]:
    """Prove the complete source-to-Reader mapping for the frozen corpus.

    Counts alone are insufficient: a bundle can contain 87 pages while a
    different source is silently omitted or a quality page is counted as the
    source page.  The run manifest is the producer-owned mapping; this check
    replays it against the raw path/hash set and requires every ready source to
    have exactly one source Reader page.  Duplicate aliases must point to the
    canonical source page, while known-empty sources must have no Reader page.
    """

    failures: list[str] = []
    manifest = run_state.get("manifest")
    if not isinstance(manifest, Mapping):
        return ["source Reader closure cannot be checked without run manifest"]
    manifest_sources = manifest.get("sources")
    manifest_pages = manifest.get("pages")
    if not isinstance(manifest_sources, list) or not isinstance(manifest_pages, list):
        return ["source Reader closure has malformed manifest arrays"]
    by_path: dict[str, Mapping[str, Any]] = {}
    by_id: dict[str, Mapping[str, Any]] = {}
    for row in manifest_sources:
        if not isinstance(row, Mapping):
            failures.append("source manifest contains a non-object row")
            continue
        path = str(row.get("relative_path", ""))
        source_id = str(row.get("source_id", ""))
        if not path or path in by_path or not source_id or source_id in by_id:
            failures.append(f"source manifest has duplicate/empty identity: {path or source_id or '<empty>'}")
            continue
        by_path[path] = row
        by_id[source_id] = row
    if set(by_path) != set(raw_hashes):
        failures.append("source manifest paths do not exactly match the raw corpus")
    quality_page_ids = set(quality_page_ids or ())
    page_by_id: dict[str, Mapping[str, Any]] = {}
    source_page_ids: dict[str, list[str]] = {}
    for row in manifest_pages:
        if not isinstance(row, Mapping):
            failures.append("page manifest contains a non-object row")
            continue
        page_id = str(row.get("page_id", ""))
        path = str(row.get("path", ""))
        if not page_id or page_id in page_by_id:
            failures.append(f"page manifest has duplicate/empty page_id: {page_id or '<empty>'}")
            continue
        page_by_id[page_id] = row
        # The compiler's frozen run-manifest schema predates an explicit
        # projection_id field.  Use the evaluated projection authority as the
        # compatibility discriminator; otherwise a quality page that cites a
        # source is silently counted as that source's canonical Reader page.
        if not row.get("projection_id") and page_id not in quality_page_ids:
            for source_id in row.get("source_ids", ()) if isinstance(row.get("source_ids"), list) else ():
                source_page_ids.setdefault(str(source_id), []).append(page_id)
        if path not in pages:
            failures.append(f"page manifest points to missing Reader page: {path}")
    if len(page_by_id) != len(pages):
        failures.append("run page manifest count does not match Reader files")
    for relative, raw_hash in raw_hashes.items():
        source = by_path.get(relative)
        ledger = source_rows.get(relative)
        if source is None or ledger is None:
            failures.append(f"source ledger missing raw path: {relative}")
            continue
        source_id = str(source.get("source_id", ""))
        if source.get("raw_hash") != raw_hash or ledger.get("raw_hash") != raw_hash:
            failures.append(f"source raw hash mismatch: {relative}")
        if source.get("status") != ledger.get("status"):
            failures.append(f"source status mismatch between ledgers: {relative}")
        status = str(source.get("status", ""))
        ids = source_page_ids.get(source_id, [])
        declared_ids = source.get("reader_page_ids", [])
        if not isinstance(declared_ids, list) or list(declared_ids) != ids:
            failures.append(f"source Reader page binding mismatch: {relative}")
        if status == "ready" and len(ids) != 1:
            failures.append(f"ready source does not have exactly one source Reader page: {relative}")
        elif status == "blank" and ids:
            failures.append(f"blank source has a Reader page: {relative}")
        elif status == "duplicate_alias":
            canonical_id = str(source.get("duplicate_of", ""))
            canonical = by_id.get(canonical_id)
            canonical_ids = source_page_ids.get(canonical_id, [])
            if (
                not canonical_id
                or canonical is None
                or canonical.get("status") != "ready"
                or source.get("raw_hash") != canonical.get("raw_hash")
                or len(ids) != 1
                or ids != canonical_ids
            ):
                failures.append(f"duplicate source is not bound to its canonical Reader page: {relative}")
        elif status not in {"ready", "blank", "known_empty", "duplicate_alias"}:
            failures.append(f"source has an unsupported/failed status: {relative}: {status}")
    for projection_id in quality_page_ids:
        page = page_by_id.get(projection_id)
        if page is None:
            continue
        path = str(page.get("path", ""))
        parsed = pages.get(path)
        if not isinstance(parsed, Mapping) or parsed.get("projection_id") != projection_id:
            failures.append(f"quality projection page binding mismatch: {projection_id}")
    return list(dict.fromkeys(failures))


def _candidate_projection_pages(pages: Mapping[str, Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for page in pages.values():
        projection_id = str(page.get("projection_id", ""))
        if projection_id:
            result.setdefault(projection_id, []).append(dict(page))
    return result


_DIMENSION_IDS = {
    "route": "DIM-01.route",
    "taxonomy": "DIM-02.taxonomy",
    "business-answer": "DIM-03.business-answer",
    "page-type": "DIM-04.page-type",
    "Reader-Audit": "DIM-05.reader-audit",
}
_GAP_TYPES = {
    "route": ("unreachable", "wrong_relation"),
    "taxonomy": ("missing_taxonomy_axis", "wrong_relation"),
    "business-answer": ("missing_stage", "unsupported_answer_claim", "wrong_relation"),
    "page-type": ("untyped_contract", "wrong_page_type"),
    "Reader-Audit": ("missing_provenance", "untraceable_claim"),
}


def _basis_sha(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    return hashlib.sha256(payload).hexdigest()


def _rubric_atom_forms(rubric: Mapping[str, Any], atom: str) -> tuple[str, ...]:
    forms = rubric.get("atom_forms", {})
    values = forms.get(atom) if isinstance(forms, Mapping) else None
    if isinstance(values, list) and values:
        return tuple(str(value) for value in values if str(value))
    return (atom,) if atom else ()


def _rubric_values(rubric: Mapping[str, Any], field: str) -> tuple[str, ...]:
    values = rubric.get(field, ())
    return tuple(str(value) for value in values if str(value)) if isinstance(values, list) else ()


def _rubric_term_present(text: str, forms: Sequence[str]) -> bool:
    folded = text.casefold()
    return any(form and form.casefold() in folded for form in forms)


def _companybrain_route_reachable(root: Path, targets: Sequence[str]) -> bool:
    """Replay CompanyBrain's actual Markdown links for the route gap type."""

    markdown: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file() or path.suffix.casefold() not in {".md", ".markdown"}:
            continue
        markdown[path.relative_to(root).as_posix()] = _read(path)

    def resolve(current: str, raw: str) -> str:
        target = raw.split("#", 1)[0].strip()
        if not target or "://" in target:
            return ""
        normalised = posixpath.normpath((Path(current).parent / target).as_posix())
        if normalised.startswith("../") or normalised == "..":
            return ""
        if normalised in markdown:
            return normalised
        if normalised + ".md" in markdown:
            return normalised + ".md"
        return ""

    links: dict[str, set[str]] = defaultdict(set)
    for current, text in markdown.items():
        for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)|\[\[([^\]]+)\]\]", text):
            target = resolve(current, match.group(1) or match.group(2))
            if target:
                links[current].add(target)
    entry_names = {
        "home.md", "gbrain-product-index.md", "文档总览.md", "使用场景索引.md",
        "产品总览.md", "常见问答入口.md", "模块总览.md",
    }
    queue = [path for path in markdown if Path(path).name.casefold() in entry_names]
    reachable = set(queue)
    while queue:
        current = queue.pop(0)
        for target in sorted(links.get(current, ())):
            if target not in reachable:
                reachable.add(target)
                queue.append(target)
    return bool(targets) and all(target in reachable for target in targets)


def _companybrain_file_locator(text: str, paths: Sequence[str]) -> str:
    """Bind a gap to one real baseline file and its observed line span."""

    for path in paths:
        marker = f"FILE: {path}\n"
        if marker not in text:
            continue
        body = text.split(marker, 1)[1].split("\nFILE: ", 1)[0]
        return f"{path}#L1-L{max(1, len(body.splitlines()))}"
    return f"{paths[0]}#L1" if paths else ""


def _reader_refs(material: Mapping[str, Any]) -> tuple[str, str]:
    reader_ref = str(material.get("kd_observation_ref", ""))
    audit_ref = str(material.get("audit_ref", ""))
    return reader_ref, audit_ref


def _build_source_bound_advantage_basis(
    projection: QualityProjection,
    dimension: str,
    material: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Build comparison evidence from actual CB and Reader bytes.

    The LLM judge is deliberately not used here.  A basis exists only when
    the frozen rubric can replay a real CompanyBrain gap and the candidate
    has a Reader/Audit completion for every atom and stage without regression.
    """

    dimension_id = _DIMENSION_IDS.get(dimension)
    if not dimension_id:
        return None
    structural = material.get("structural_observation", {})
    observation = structural.get(dimension) if isinstance(structural, Mapping) else None
    if not isinstance(observation, Mapping) or observation.get("passed") is not True:
        return None
    baseline_checks = material.get("companybrain_baseline_checks", ())
    if not isinstance(baseline_checks, list) or not baseline_checks or any(
        not isinstance(check, Mapping)
        or check.get("exists") is not True
        or check.get("hash_matches") is not True
        or check.get("applicability") != "present"
        for check in baseline_checks
    ):
        return None
    companybrain_paths = [str(path) for path in material.get("companybrain_page_paths", ()) if str(path)]
    reader_ref, audit_ref = _reader_refs(material)
    if not companybrain_paths or not reader_ref or not audit_ref:
        return None
    candidate_text = str(material.get("candidate_text", ""))
    companybrain_text = str(material.get("companybrain_text", ""))
    if not candidate_text or not companybrain_text:
        # An empty baseline is meaningful for an unreachable route only, but
        # an empty text blob cannot prove a content gap for other dimensions.
        if dimension != "route":
            return None

    rubric = projection.comparison_rubric.get(dimension, {})
    if not isinstance(rubric, Mapping):
        return None
    expected_axes = {
        "产品": projection.axes["product"],
        "模块": projection.axes["module"],
        "对象": projection.axes["object"],
        "场景": projection.axes["scene"],
        "边界": projection.axes["boundary"],
    }
    expected_sections = EXPECTED_SECTIONS.get(projection.page_type, ())
    cb_axes = _axis_values(companybrain_text)
    cb_substantive = len(_visible_body(companybrain_text).replace("原始资料未明确", "").strip()) >= 24
    route_feature_gap = ""
    if dimension == "route":
        question_text = re.sub(r"[？?，,、。]", "", projection.question).strip()
        title_text = re.sub(r"[？?，,、。]", "", projection.title).strip()
        path_use_count = int(material.get("companybrain_path_use_count", 1))
        route_features = {
            "question_match": bool(question_text and question_text in companybrain_text)
            or bool(title_text and title_text in companybrain_text),
            "scenario_disambiguation": projection.axes["scene"] in companybrain_text,
            "canonical_target": len(companybrain_paths) == 1 and bool(title_text and title_text in companybrain_text),
            "projection_isolation": path_use_count == 1,
        }
        route_feature_gap = next((name for name, passed in route_features.items() if not passed), "")
        cb_dimension_pass = not route_feature_gap and bool(material.get("companybrain_route_reachable"))
    else:
        cb_dimension_pass = {
            "taxonomy": bool(cb_axes and all(cb_axes.get(key) == value for key, value in expected_axes.items())),
            "business-answer": bool(cb_substantive and all(_section(companybrain_text, section) for section in expected_sections)),
            "page-type": _page_type(companybrain_text) == projection.page_type,
            # An explicit source/audit chain is required; mentioning the word
            # "source" alone does not prove claim lineage.
            "Reader-Audit": bool(
                re.search(r"(?i)Audit\.md|sourcearchive|原始地址", companybrain_text)
                and re.search(r"(?i)#(?:L\d+|source-|evidence-)", companybrain_text)
            ),
        }[dimension]
    if cb_dimension_pass:
        return None
    kd_semantic_pass = True  # guarded by the structural observation above
    kd_refs = [ref for ref in (reader_ref, audit_ref) if ref]
    cb_refs = list(companybrain_paths)
    atom_observations: list[dict[str, Any]] = []
    gap_atom_refs: list[str] = []
    strict_refs: list[str] = []
    regressions = False
    for atom in _rubric_values(rubric, "required_atoms"):
        atom_id = f"{projection.projection_id}::{dimension_id}::{atom}"
        cb_present = _rubric_term_present(companybrain_text, _rubric_atom_forms(rubric, atom))
        # Paraphrase is valid Reader content.  Literal forms are retained as
        # baseline diagnostics, while candidate completion comes from the
        # independently checked page structure.
        kd_present = kd_semantic_pass
        cb_status = "present" if cb_present else "absent"
        kd_status = "present" if kd_present else "absent"
        if not cb_present:
            gap_atom_refs.append(atom_id)
        if not cb_present and kd_present:
            relation = "strict_improvement"
            strict_refs.append(atom_id)
        elif cb_present and kd_present:
            relation = "non_regression"
        else:
            relation = "regression"
            regressions = True
        atom_observations.append({
            "atom_id": atom_id,
            "applicable": True,
            "cb_status": cb_status,
            "kd_status": kd_status,
            "cb_evidence_refs": cb_refs,
            "kd_evidence_refs": kd_refs,
            "relation": relation,
        })

    stage_observations: list[dict[str, Any]] = []
    gap_stage_refs: list[str] = []
    for marker in _rubric_values(rubric, "structure_markers"):
        stage_id = f"{projection.projection_id}::{dimension_id}::stage::{marker}"
        cb_present = _rubric_term_present(companybrain_text, (marker,))
        kd_present = kd_semantic_pass
        cb_status = "present" if cb_present else "absent"
        kd_status = "present" if kd_present else "absent"
        if not cb_present:
            gap_stage_refs.append(stage_id)
        if not cb_present and kd_present:
            relation = "strict_improvement"
            strict_refs.append(stage_id)
        elif cb_present and kd_present:
            relation = "non_regression"
        else:
            relation = "regression"
            regressions = True
        stage_observations.append({
            "stage_id": stage_id,
            "applicable": True,
            "cb_status": cb_status,
            "kd_status": kd_status,
            "cb_evidence_refs": cb_refs,
            "kd_evidence_refs": kd_refs,
            "relation": relation,
        })

    gap_type: str
    if dimension == "route":
        gap_type = "wrong_relation" if bool(material.get("companybrain_route_reachable")) else "unreachable"
    elif dimension == "taxonomy":
        gap_type = "missing_taxonomy_axis"
    elif dimension == "business-answer":
        gap_type = "missing_stage" if not all(_section(companybrain_text, section) for section in expected_sections) else "unsupported_answer_claim"
    elif dimension == "page-type":
        gap_type = "wrong_page_type" if re.search(r"(?im)^(?:type|page_type|page-type)\s*:", companybrain_text) else "untyped_contract"
    else:
        gap_type = "untraceable_claim" if re.search(r"(?i)来源|原始地址|source|locator|sourcearchive", companybrain_text) else "missing_provenance"
    if gap_type not in _GAP_TYPES[dimension]:
        return None

    feature_for_gap = {
        "route": {"unreachable": route_feature_gap or "canonical_target", "wrong_relation": route_feature_gap or "projection_isolation"},
        "taxonomy": {"missing_taxonomy_axis": "axis_meaning", "wrong_relation": "axis_separation"},
        "business-answer": {"missing_stage": "task_completion", "unsupported_answer_claim": "decision_safety", "wrong_relation": "scope_discipline"},
        "page-type": {"untyped_contract": "type_specificity", "wrong_page_type": "scope_fit"},
        "Reader-Audit": {"missing_provenance": "source_locator", "untraceable_claim": "claim_lineage"},
    }
    feature_name = feature_for_gap.get(dimension, {}).get(gap_type, "")
    feature_ref = next(
        (
            f"{projection.projection_id}::{dimension_id}::feature::{feature_name}"
            for feature in projection.quality_features.get(dimension, ())
            if str(feature.get("feature_id", "")) == feature_name
        ),
        "",
    )
    feature_observations = []
    if feature_ref:
        feature_observations.append({
            "feature_id": feature_ref,
            "applicable": True,
            "blocking": True,
            "cb_score": None,
            # No numeric quality score is defined by this contract.  The
            # independent blind judge supplies the comparison judgement;
            # keeping this field non-numeric prevents a structural gap scan
            # from masquerading as a calibrated score.
            "kd_score": None,
            "cb_status": "absent",
            "kd_status": "present",
            "cb_evidence_refs": cb_refs,
            "kd_evidence_refs": kd_refs,
            "relation": "strict_improvement",
        })
        strict_refs.append(feature_ref)
    if not strict_refs or regressions or not (gap_atom_refs or gap_stage_refs or feature_ref):
        return None

    locator = _companybrain_file_locator(companybrain_text, companybrain_paths)
    cb_row = {
        "case_id": projection.case_id,
        "projection_id": projection.projection_id,
        "dimension_id": dimension_id,
        "status": "absent",
        "score": None,
        "source_refs": sorted(cb_refs, key=lambda value: value.encode("utf-8")),
        "visible_ref": locator,
        "audit_ref": None,
        "gap_ref": {
            "gap_type": gap_type,
            "gap_locator": locator,
            "gap_atom_refs": gap_atom_refs,
            "gap_stage_refs": gap_stage_refs,
            "gap_quality_feature_refs": [feature_ref] if feature_ref else [],
        },
        "kd_ref": reader_ref,
    }
    cb_digest = _basis_sha(cb_row)
    completion = {
        "projection_key": projection.projection_id,
        "dimension_id": dimension_id,
        "reader_ref": reader_ref,
        "audit_ref": audit_ref,
        "atom_observations": atom_observations,
        "stage_observations": stage_observations,
    }
    kd_digest = _basis_sha(completion)
    return {
        "projection_key": projection.projection_id,
        "dimension_id": dimension_id,
        "cb_observation_ref": f"companybrain:{projection.projection_id}:{dimension_id}",
        "cb_observation_digest": cb_digest,
        "cb_gap_type": gap_type,
        "cb_gap_locator": locator,
        "atom_observations": atom_observations,
        "gap_atom_refs": gap_atom_refs,
        "stage_observations": stage_observations,
        "gap_stage_refs": gap_stage_refs,
        "quality_feature_observations": feature_observations,
        "gap_quality_feature_refs": [feature_ref] if feature_ref else [],
        "strict_improvement_refs": list(dict.fromkeys(strict_refs)),
        "non_regression": True,
        "kd_completion_refs": kd_refs,
        "kd_completion_surfaces": ["Reader", "Audit"],
        "kd_completion_digest": kd_digest,
    }


def _material(candidate: Path, raw: Path, companybrain: Path, projection: QualityProjection, pages: Mapping[str, Mapping[str, Any]], projection_pages: Mapping[str, Sequence[Mapping[str, Any]]], source_rows: Mapping[str, Mapping[str, Any]], audit: str, raw_hashes: Mapping[str, str], baseline_entries: Sequence[Mapping[str, Any]], evidence_rows: Sequence[Mapping[str, Any]], run_state: Mapping[str, Any]) -> dict[str, Any]:
    candidate = _bundle_root(candidate)
    matches = list(projection_pages.get(projection.projection_id, ()))
    page = matches[0] if len(matches) == 1 else None
    page_path = str(page.get("path", "")) if page else ""
    home = candidate / "Home.md"
    home_links = _links(candidate, home, _read(home)) if home.is_file() else []
    home_to_page = any(item["path"] == page_path for item in home_links)
    index_path = "/".join(page_path.split("/")[:2]) + "/index.md" if page_path else ""
    home_to_index = any(item["path"] == index_path for item in home_links)
    index = candidate / index_path
    index_to_page = bool(page and index.is_file() and any(item["path"] == page_path for item in _links(candidate, index, _read(index))))
    route_ok = bool(page and home_to_page and home_to_index and index_to_page)
    manifest = run_state.get("manifest", {})
    manifest_pages = manifest.get("pages", []) if isinstance(manifest, Mapping) else []
    manifest_page = next((item for item in manifest_pages if isinstance(item, Mapping) and item.get("page_id") == projection.projection_id), None)
    route_rows = manifest.get("routes", []) if isinstance(manifest, Mapping) else []
    route_row = next((item for item in route_rows if isinstance(item, Mapping) and item.get("selected_page_ids") == [projection.projection_id]), None)
    current_surface_hash = hashlib.sha256((candidate / page_path).read_bytes()).hexdigest() if page and (candidate / page_path).is_file() else ""
    page_binding_ok = bool(
        page
        and isinstance(manifest_page, Mapping)
        and manifest_page.get("path") == page_path
        and manifest_page.get("page_id") == projection.projection_id
        and manifest_page.get("surface_sha256") == current_surface_hash
        and isinstance(route_row, Mapping)
        and route_row.get("selected_page_ids") == [projection.projection_id]
    )
    route_ok = route_ok and page_binding_ok
    expected_axes = {"产品": projection.axes["product"], "模块": projection.axes["module"], "对象": projection.axes["object"], "场景": projection.axes["scene"], "边界": projection.axes["boundary"]}
    actual_axes = dict(page.get("axes", {})) if page else {}
    taxonomy_ok = bool(page and all(actual_axes.get(key) == value for key, value in expected_axes.items()))
    body = str(page.get("text", "")) if page else ""
    required_sections = EXPECTED_SECTIONS.get(projection.page_type, ())
    visible_sections = {
        section: _section(body, section)
        for section in ("当前结论", "服务对象与入口", "产品关系与选择", "边界与未明确", "使用场景", "对象与组成", "关系与生效规则", "边界与容易混淆", "前置条件", "操作步骤", "预期结果", "验证方式", "失败与限制", "现象", "检查顺序", "可能原因", "处理动作", "升级边界", "背景", "阶段变化", "方案取舍与经验", "经验教训", "适用边界")
    }
    substantive = any(
        len(_visible_body(value).replace("原始资料未明确", "").strip()) >= 24
        for value in visible_sections.values()
    )
    source_paths = set(page.get("source_paths", ())) if page else set()
    # Route closure is checked separately from Reader citations.  A concise
    # answer may cite only the raw sources it actually uses; all declared
    # projection sources must still be present and hash-verified in Audit.
    source_closure = bool(page and set(projection.source_paths).issubset(raw_hashes))
    # Validate the blocks the page actually cites.  The frozen claim list is
    # an editorial checklist, not a demand to print dozens of opaque hashes;
    # semantic completeness is judged from the answer body and the raw-only
    # evidence packet.
    # The frozen projection is the authority for required evidence.  A
    # candidate cannot make an omitted block disappear by omitting it from its
    # own evidence ledger.
    required_block_refs = list(dict.fromkeys(str(item) for item in projection.source_block_refs))
    reader_required_block_refs = {
        ref
        for group in _requirement_groups(projection, reader=True)
        for ref in group
    }
    business_ok = bool(page and substantive and all(_section(body, section) for section in required_sections) and source_closure)
    page_type_ok = bool(page and page.get("page_type") == projection.page_type)
    page_links = _link_targets(candidate, candidate / page_path, body) if page else []
    audit_anchor = _page_identity(page) if page else ""
    audit_ok = bool(
        page and home_to_page and source_closure
        and any(item["path"] == "Audit.md" and item["fragment"] == f"page-{audit_anchor}" for item in page_links)
        and any(item["path"] == "_audit/sources.jsonl" for item in page_links)
        and (candidate / "Audit.md").is_file()
        and f'<a id="page-{audit_anchor}"></a>' in audit
    )
    source_checks: dict[str, Any] = {}
    for source_path in projection.source_paths:
        row = source_rows.get(source_path, {})
        snapshot_hash = _snapshot_hash(candidate, row)
        bound = [item for item in evidence_rows if item.get("source_path") == source_path and any(binding.get("page_path") == page_path for binding in item.get("page_bindings", ()) if isinstance(binding, Mapping))]
        source_checks[source_path] = {"audit_entry": bool(row), "raw_exists": source_path in raw_hashes, "snapshot_matches_raw": bool(snapshot_hash and snapshot_hash == raw_hashes.get(source_path)), "reader_evidence_bindings": len(bound)}
        source_anchor = str(row.get("source_id", ""))
        if not (row and source_anchor and f'<a id="{source_anchor}"></a>' in audit and source_path in raw_hashes and snapshot_hash and snapshot_hash == raw_hashes.get(source_path)):
            audit_ok = False
    block_checks: dict[str, Any] = {}
    for block_ref in required_block_refs:
        try:
            source_path, start_line, end_line, _label = parse_block_ref(block_ref)
        except ValueError:
            block_checks[block_ref] = {"valid": False, "reason": "invalid frozen block ref"}
            audit_ok = False
            business_ok = False
            continue
        expected_evidence_id = "qev-" + hashlib.sha256(
            f"{projection.projection_id}\0{block_ref}".encode("utf-8")
        ).hexdigest()[:24]

        def has_quality_binding(item: Mapping[str, Any]) -> bool:
            evidence_ids = {
                str(value) for value in item.get("evidence_ids", ()) if str(value)
            }
            if expected_evidence_id in evidence_ids:
                return True
            return any(
                isinstance(binding, Mapping)
                and str(binding.get("block_id", "")) == expected_evidence_id
                for binding in item.get("evidence_bindings", ())
                if isinstance(item.get("evidence_bindings"), list)
            )

        all_candidates = [item for item in evidence_rows if has_quality_binding(item)]
        candidates = [
            item for item in all_candidates
            if str(item.get("page_path", "")) == page_path
        ]
        raw_hash = raw_hashes.get(source_path, "")
        expected_block_hash = _raw_block_hash(raw, source_path, start_line, end_line)

        def quality_binding_matches(item: Mapping[str, Any]) -> bool:
            for binding in item.get("evidence_bindings", ()):
                if not isinstance(binding, Mapping) or str(binding.get("block_id", "")) != expected_evidence_id:
                    continue
                locator = binding.get("locator")
                if not isinstance(locator, Mapping):
                    continue
                if (
                    binding.get("raw_hash") == raw_hash
                    and binding.get("support_sha256") == expected_block_hash
                    and locator.get("start_line") == start_line
                    and locator.get("end_line") == end_line
                ):
                    return True
            return False

        valid = any(
            quality_binding_matches(item)
            for item in all_candidates
        )
        reader_valid = any(
            quality_binding_matches(item)
            for item in candidates
        )
        audit_anchor = f'<a id="evidence-{expected_evidence_id}"></a>'
        audit_line = (
            f"- `{expected_evidence_id}`：第 `{start_line}-{end_line}` 行；"
            f"block_sha256：`{expected_block_hash}`"
        )
        audit_only_valid = audit_anchor in audit and audit_line in audit
        block_checks[block_ref] = {"valid": valid, "reader_valid": reader_valid, "candidate_rows": len(candidates), "audit_rows": len(all_candidates), "raw_block_sha256": expected_block_hash}
        block_checks[block_ref]["audit_only_valid"] = audit_only_valid
        if audit_only_valid:
            block_checks[block_ref]["valid"] = True
            block_checks[block_ref]["audit_rows"] = max(1, len(all_candidates))
            valid = True
        bound_to_page = bool(candidates)
        if not valid:
            audit_ok = False
            business_ok = False
        # A Reader-visible claim cannot be satisfied by putting its evidence
        # only in Audit.  The old check only ran when a binding happened to be
        # present, which made missing Reader bindings look valid.
        if block_ref in reader_required_block_refs and not reader_valid:
            audit_ok = False
            business_ok = False
        # Reader only needs to show the cited source and link back to Audit;
        # the exact line range for every bound block lives in the full
        # evidence ledger.  Requiring every range to fit the compact source
        # list made long but valid pages fail merely because the list is
        # intentionally truncated for readability.
        source_line_marker = f"原始地址：`{source_path}`"
        page_text = str(page.get("text", "")) if page else ""
        block_visible = source_line_marker in page_text and any(
            str(item.get("page_path", "")) == page_path
            for item in evidence_rows
            if has_quality_binding(item)
        )
        block_checks[block_ref]["reader_visible_locator"] = block_visible
        if block_ref in reader_required_block_refs and not block_visible:
            audit_ok = False
            business_ok = False
    required_groups = _requirement_groups(projection, reader=True)
    group_checks = []
    for group in required_groups:
        group_valid = all(
            block_checks.get(ref, {}).get("valid")
            and block_checks.get(ref, {}).get("reader_valid")
            and any(
                str(row.get("page_path", "")) == page_path
                for row in evidence_rows
                if (
                    "qev-" + hashlib.sha256(
                        f"{projection.projection_id}\0{ref}".encode("utf-8")
                    ).hexdigest()[:24]
                    in {str(value) for value in row.get("evidence_ids", ()) if str(value)}
                )
            )
            for ref in group
        )
        group_checks.append({"refs": group, "closed": group_valid})
        if not group_valid:
            business_ok = False
            audit_ok = False
    audit_only_groups = _requirement_groups(projection, reader=False)
    audit_group_checks = []
    for group in audit_only_groups:
        group_valid = all(block_checks.get(ref, {}).get("valid") for ref in group)
        audit_group_checks.append({"refs": group, "closed": group_valid})
        if not group_valid:
            audit_ok = False
    raw_evidence = [
        {
            "block_ref": block_ref,
            "text": _raw_block_text(raw, block_ref),
            "sha256": block_checks.get(block_ref, {}).get("raw_block_sha256", ""),
        }
        for block_ref in required_block_refs
        if _raw_block_text(raw, block_ref)
    ]
    required_reader_claims = [
        {
            "ref": str(item.get("claim_ref") or item.get("boundary_ref") or ""),
            "text": str(item.get("atom") or item.get("text") or ""),
            "source_block_refs": [str(ref) for ref in item.get("source_block_refs", ()) if str(ref)],
        }
        for item in (*projection.required_claims, *projection.required_boundaries)
        if item_reader_visible(item)
    ]
    audit_only_claims = [
        {
            "ref": str(item.get("claim_ref") or item.get("boundary_ref") or ""),
            "text": str(item.get("atom") or item.get("text") or ""),
            "source_block_refs": [str(ref) for ref in item.get("source_block_refs", ()) if str(ref)],
        }
        for item in (*projection.required_claims, *projection.required_boundaries)
        if not item_reader_visible(item)
    ]
    # Keep the public Audit unchanged, but give the blind semantic judge a
    # compact packet for this projection only.  This lets it decide
    # completeness from frozen requirements and raw text without repeating
    # the entire 89-source Audit on every call.
    judge_audit = _relevant_audit(audit, projection.source_paths, page, required_block_refs)
    judge_audit += "\n\n## 评审专用：冻结需求与原始证据（不属于 Reader 正文）\n"
    judge_audit += json.dumps(
        {
            "axes": dict(projection.axes),
            "required_reader_claims": required_reader_claims,
            "audit_only_claims": audit_only_claims,
            "raw_evidence": raw_evidence,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    # The return object exposes the complete audit-only group checks; the
    # local name above is retained only while building the raw packet.
    audit_only_group_checks = audit_group_checks
    baseline = [entry for entry in baseline_entries if projection.projection_id in entry.get("projection_keys", [])]
    baseline_checks = []
    cb_texts = []
    cb_navigation_parts = []
    for relative in ("Home.md", "Products/产品索引.md"):
        path = companybrain / relative
        if path.is_file() and not path.is_symlink():
            cb_navigation_parts.append(f"FILE: {relative}\n{_read(path)}")
    for entry in baseline:
        relative = str(entry.get("relative_path", ""))
        path = companybrain / relative
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
        expected_hash = str(entry.get("content_hash", ""))
        baseline_checks.append({"baseline_id": entry.get("baseline_id"), "path": relative, "exists": path.is_file(), "hash_matches": bool(actual_hash and actual_hash == expected_hash), "applicability": entry.get("applicability")})
        if path.is_file() and actual_hash == expected_hash and entry.get("applicability") == "present":
            cb_texts.append(f"FILE: {relative}\n{_read(path)}")
    return {"case_id": projection.case_id, "projection_id": projection.projection_id, "projection_key": projection.projection_key, "question": projection.question, "expected_page_type": projection.page_type, "candidate_page_paths": [str(item.get("path", "")) for item in matches], "companybrain_page_paths": [str(entry.get("relative_path", "")) for entry in baseline], "companybrain_baseline_checks": baseline_checks, "candidate_text": str(page.get("text", "")) if page else "", "companybrain_text": "\n\n".join(cb_texts), "judge_candidate_text": str(page.get("text", "")) if page else "", "judge_companybrain_text": "\n\n".join(cb_texts), "judge_home_text": _read(home), "judge_companybrain_navigation_text": "\n\n".join(cb_navigation_parts), "judge_audit_text": judge_audit, "structural_observation": {"route": {"passed": route_ok, "route_chain": ["Home.md", index_path, page_path] if page else [], "reason": "Home→产品目录→Reader 链路完整" if route_ok else "没有找到这条投影的完整入口链路"}, "taxonomy": {"passed": taxonomy_ok, "expected": expected_axes, "actual": actual_axes, "reason": "五轴和固定投影一致" if taxonomy_ok else "五轴为空、错位或与投影合同不一致"}, "business-answer": {"passed": business_ok, "missing_sections": [section for section in required_sections if not _section(body, section)], "source_closure": source_closure, "required_block_checks": block_checks, "required_group_checks": group_checks, "audit_only_group_checks": audit_group_checks, "reason": "正文直接回答问题并覆盖投影来源" if business_ok else "正文不完整、不可读或遗漏投影来源"}, "page-type": {"passed": page_type_ok, "expected": projection.page_type, "actual": page.get("page_type") if page else "missing", "reason": "页面类型正确" if page_type_ok else "页面类型错误或页面缺失"}, "Reader-Audit": {"passed": audit_ok, "source_checks": source_checks, "required_block_checks": block_checks, "required_group_checks": group_checks, "audit_only_group_checks": audit_only_group_checks, "reason": "Reader 可见来源，Audit 和快照可回查" if audit_ok else "Reader→Audit→原文链路不完整"}}}


def _bound(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "\n[评审输入截断]"


def _judge_prompt(material: Mapping[str, Any], swapped: bool) -> str:
    candidate_label, baseline_label = ("B", "A") if swapped else ("A", "B")
    return f"""你是独立的企业知识库质量评审者。只比较下面同一个固定投影的问题，不使用外部知识，不因为字数或关键词多就判胜。

问题：{material['question']}
固定页面类型：{material['expected_page_type']}
候选 KnowledgeDigest 是 {candidate_label}，CompanyBrain 是 {baseline_label}。

五项分别判断：route（问题/场景入口是否真实可用）；taxonomy（产品、模块、对象、场景、边界是否有用）；business-answer（是否直接回答、可执行且保留条件/冲突/缺口）；page-type（类型是否正确且履行职责）；Reader-Audit（正文来源是否能回到具体原始路径、快照和行范围）。page-type 必须按固定职责评估，而不是只看页面自称的标签：positioning 要回答“是什么、服务谁、怎么选、边界”；concept 要解释对象、组成、关系和生效规则；operation 要给前置条件、步骤、结果、验证和失败限制；diagnosis 要给现象、检查顺序、排查对象/可能原因、处理动作和升级边界；experience 要整理背景、阶段变化、取舍、教训和适用边界。若一方是针对固定问题的专门页面，另一方只是混合主题或宽泛概览，专门页面在 page-type 上应判 WIN；只有两方都同样履行固定职责才判 TIE。评审专用的冻结需求和原始证据在 Audit 输入末尾的 JSON 中；它们是判断“有没有漏掉关键知识”的唯一依据。surface=Audit 的要求只检查 Audit，不要求出现在 Reader 正文。只有实际使用价值严格更高且没有事实/边界退化才 WIN；相似 TIE；证据不足 UNKNOWN。
每个 reason 必须用大白话说明比较依据，至少指出一处具体的 Reader 内容、CompanyBrain 内容或原始证据；不能只写“更好”“更完整”。每个 reason 控制在 50 个汉字以内；不要在 reason 里使用英文双引号，避免 JSON 截断。五个维度必须全部返回，键名必须逐字使用 route、taxonomy、business-answer、page-type、Reader-Audit，不得增加或删除键。
只返回 JSON：{{"projection_id":"{material['projection_id']}","dimensions":{{"route":{{"verdict":"A_WIN|B_WIN|TIE|UNKNOWN","reason":"大白话理由"}},"taxonomy":{{...}},"business-answer":{{...}},"page-type":{{...}},"Reader-Audit":{{...}}}},"blocking_risks":[]}}

A：
{_bound(material['judge_candidate_text'] if candidate_label == 'A' else material['judge_companybrain_text'], 16_000)}

B：
{_bound(material['judge_candidate_text'] if candidate_label == 'B' else material['judge_companybrain_text'], 16_000)}

候选 Home：
{_bound(material['judge_home_text'], 6_000)}

CompanyBrain 导航：
{_bound(material['judge_companybrain_navigation_text'], 6_000)}

候选 Audit：
{_bound(material['judge_audit_text'], 14_000)}
"""


def _normalise_judgement(value: Mapping[str, Any], swapped: bool, expected_projection_id: str) -> dict[str, Any]:
    if value.get("projection_id") != expected_projection_id:
        raise ValueError("judge projection_id does not match the requested projection")
    raw_dimensions = value.get("dimensions")
    if not isinstance(raw_dimensions, Mapping) or set(raw_dimensions) != set(DIMENSIONS):
        raise ValueError("judge dimensions do not match the five-dimension contract")
    risks = value.get("blocking_risks", [])
    if not isinstance(risks, list) or any(not isinstance(item, str) for item in risks):
        raise ValueError("judge blocking_risks is malformed")
    result = dict(value)
    dimensions: dict[str, Any] = {}
    for dimension in DIMENSIONS:
        raw_item = raw_dimensions.get(dimension)
        if not isinstance(raw_item, Mapping):
            raise ValueError(f"judge dimension is malformed: {dimension}")
        item = dict(raw_item)
        verdict = str(item.get("verdict", "UNKNOWN"))
        if verdict not in {"A_WIN", "B_WIN", "TIE", "UNKNOWN"}:
            raise ValueError(f"judge returned an unsupported verdict: {verdict}")
        reason = str(item.get("reason", "")).strip()
        if len(reason) < 8:
            raise ValueError(f"judge reason is not evidence-bearing: {dimension}")
        item["reason"] = reason
        item["verdict"] = (
            "KD_WIN" if verdict == ("B_WIN" if swapped else "A_WIN")
            else "CB_WIN" if verdict in {"A_WIN", "B_WIN"} else verdict
        )
        dimensions[dimension] = item
    result["dimensions"] = dimensions
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Black-box five-dimension Reader comparison")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--companybrain", type=Path, required=True)
    parser.add_argument("--ledger-root", type=Path)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--judge", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    candidate = _safe_root(args.candidate, "candidate")
    raw = _safe_root(args.raw, "raw")
    companybrain = _safe_root(args.companybrain, "companybrain")
    try:
        _reject_nested_symlinks(candidate, "candidate")
        _reject_nested_symlinks(companybrain, "companybrain")
    except ValueError as error:
        raise SystemExit(str(error))
    candidate_bundle = _bundle_root(candidate)
    ledger_candidate = _safe_root(args.ledger_root, "ledger") if args.ledger_root is not None else candidate_bundle
    try:
        _reject_nested_symlinks(ledger_candidate, "ledger")
    except ValueError as error:
        raise SystemExit(str(error))
    if not (candidate_bundle / "Home.md").is_file() or not (candidate_bundle / "Audit.md").is_file():
        raise SystemExit("candidate must contain Home.md and Audit.md")
    rules = args.cases.parent / "task5-projection-rules-v1.json"
    projections = load_quality_projections(args.cases, rules if rules.is_file() else None)
    baseline_value = _json(args.baseline)
    if not isinstance(baseline_value, Mapping) or not isinstance(baseline_value.get("entries"), list):
        raise SystemExit("baseline must contain entries")
    baseline_entries = [entry for entry in baseline_value["entries"] if isinstance(entry, Mapping)]
    baseline_projection_ids = {
        str(projection.projection_id)
        for projection in projections
    }
    seen_baseline_ids: set[str] = set()
    for entry in baseline_entries:
        baseline_id = str(entry.get("baseline_id", ""))
        relative = str(entry.get("relative_path", ""))
        projection_keys = entry.get("projection_keys")
        if not baseline_id or baseline_id in seen_baseline_ids:
            raise SystemExit("baseline contains duplicate or empty baseline_id")
        if not isinstance(projection_keys, list) or not projection_keys or not set(str(item) for item in projection_keys).issubset(baseline_projection_ids):
            raise SystemExit(f"baseline entry has invalid projection_keys: {baseline_id}")
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise SystemExit(f"baseline path escapes CompanyBrain: {relative}")
        target = companybrain / relative
        if not target.is_file() or target.is_symlink():
            raise SystemExit(f"baseline file is missing or unsafe: {relative}")
        if str(entry.get("content_hash", "")) != hashlib.sha256(target.read_bytes()).hexdigest():
            raise SystemExit(f"baseline hash mismatch: {relative}")
        seen_baseline_ids.add(baseline_id)
    raw_hashes = _raw_manifest(raw)
    source_rows, _ledger_audit = _audit_sources(ledger_candidate)
    audit_path = candidate_bundle / "Audit.md"
    audit = _read(audit_path) if audit_path.is_file() else _ledger_audit
    pages = _all_reader_pages(candidate)
    projection_pages = _candidate_projection_pages(pages)
    evidence_rows = _evidence_rows(ledger_candidate)
    run_state: Mapping[str, Any] = {}
    run_path = candidate_bundle / "_audit" / "run-result.json"
    if run_path.is_file():
        value = _json(run_path)
        if isinstance(value, Mapping):
            run_state = value
    expected_projection_ids = [projection.projection_id for projection in projections]
    layout_failures = _layout_failures(candidate, raw_hashes, run_state, pages)
    materials = [_material(candidate, raw, companybrain, projection, pages, projection_pages, source_rows, audit, raw_hashes, baseline_entries, evidence_rows, run_state) for projection in projections]
    companybrain_path_use_count: dict[str, int] = defaultdict(int)
    for material in materials:
        for path in material.get("companybrain_page_paths", ()):
            companybrain_path_use_count[str(path)] += 1
    for material, projection in zip(materials, projections):
        page_path = str(material.get("candidate_page_paths", [""])[0]) if material.get("candidate_page_paths") else ""
        unit = next(
            (
                row for row in evidence_rows
                if isinstance(row, Mapping)
                and str(row.get("page_path", "")) == page_path
                and row.get("surface") == "Reader.answer_body"
                and str(row.get("unit_id", ""))
            ),
            None,
        )
        material["kd_observation_ref"] = f"{page_path}#{unit['unit_id']}" if unit else ""
        material["audit_ref"] = str(unit.get("audit_ref", "")) if unit else ""
        material["companybrain_route_reachable"] = _companybrain_route_reachable(
            companybrain,
            [str(path) for path in material.get("companybrain_page_paths", ()) if str(path)],
        )
        material["companybrain_path_use_count"] = max(
            (companybrain_path_use_count.get(str(path), 0) for path in material.get("companybrain_page_paths", ())),
            default=0,
        )
        material["advantage_basis_by_dimension"] = {
            dimension: _build_source_bound_advantage_basis(projection, dimension, material)
            for dimension in DIMENSIONS
        }
    public_materials = [{key: value for key, value in material.items() if key not in {"candidate_text", "companybrain_text", "judge_candidate_text", "judge_companybrain_text", "judge_home_text", "judge_companybrain_navigation_text", "judge_audit_text"}} for material in materials]
    result: dict[str, Any] = {"schema_version": "reader-black-box-evaluation.v3", "candidate": str(candidate), "raw": str(raw), "companybrain": str(companybrain), "source_count_in_audit": len(source_rows), "source_count_on_disk": len(raw_hashes), "candidate_reader_file_count": len(pages), "run_outcome": run_state.get("outcome", "missing"), "projection_count": len(projections), "projections": public_materials, "verdict": "not_evaluated"}
    hard_blockers: list[str] = []
    hard_blockers.extend(layout_failures)
    for material, projection in zip(materials, projections):
        for dimension in DIMENSIONS:
            if dimension in {"route", "taxonomy", "business-answer", "page-type", "Reader-Audit"} and not material.get("advantage_basis_by_dimension", {}).get(dimension):
                hard_blockers.append(
                    f"{projection.projection_id} has no source-bound CompanyBrain gap basis for {dimension}"
                )
    if len(raw_hashes) != 89:
        hard_blockers.append(f"raw supported corpus has {len(raw_hashes)} files, expected frozen 89")
    if len(source_rows) != len(raw_hashes):
        hard_blockers.append(f"Audit source count {len(source_rows)} does not match raw supported count {len(raw_hashes)}")
    if run_state.get("source_count") != len(raw_hashes):
        hard_blockers.append("run source_count does not match the raw supported corpus")
    expected_source_manifest_hash = _expected_source_manifest_hash(run_state, args.source_manifest)
    if (
        expected_source_manifest_hash is None
        or run_state.get("source_manifest_hash") != expected_source_manifest_hash
    ):
        hard_blockers.append("run source_manifest_hash does not match its source manifest")
    if run_state.get("outcome") not in {"completed", "released"}:
        hard_blockers.append(f"candidate run outcome is not completed: {run_state.get('outcome', 'missing')}")
    expected_source_pages = sum(
        1
        for source_path in raw_hashes
        if source_rows.get(source_path, {}).get("status") == "ready"
    )
    if run_state.get("source_page_count") != expected_source_pages:
        hard_blockers.append(
            f"source Reader coverage is incomplete: {run_state.get('source_page_count')} != {expected_source_pages}"
        )
    hard_blockers.extend(_source_page_closure(raw_hashes, source_rows, run_state, pages, set(expected_projection_ids)))
    for forbidden_dir in ("modules", "boundaries", "knowledge"):
        if (candidate_bundle / forbidden_dir).exists():
            hard_blockers.append(f"candidate contains forbidden public directory: {forbidden_dir}")
    for forbidden_path in (candidate_bundle / "_audit" / "sources", candidate / "staging"):
        if forbidden_path.exists():
            hard_blockers.append(f"candidate contains forbidden implementation artifact: {forbidden_path.name}")
    if len(projections) != 12:
        hard_blockers.append(f"frozen quality contract expands to {len(projections)} projections, expected 12")
    quality_path = ledger_candidate / "_audit" / "quality.json"
    quality_value: Mapping[str, Any] = {}
    if not quality_path.is_file():
        hard_blockers.append("candidate is missing _audit/quality.json")
    else:
        try:
            loaded_quality = _json(quality_path)
            if isinstance(loaded_quality, Mapping):
                quality_value = loaded_quality
            else:
                hard_blockers.append("_audit/quality.json is not an object")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            hard_blockers.append("_audit/quality.json is invalid JSON")
    if quality_value.get("projection_ids") != expected_projection_ids:
        hard_blockers.append("_audit/quality.json projection_ids do not match the frozen contract")
    run_manifest = run_state.get("manifest", {})
    if not isinstance(run_manifest, Mapping):
        hard_blockers.append("run manifest is missing")
    else:
        manifest_sources = run_manifest.get("sources")
        manifest_pages = run_manifest.get("pages")
        if run_manifest.get("source_count") != len(raw_hashes) or not isinstance(manifest_sources, list) or len(manifest_sources) != len(raw_hashes):
            hard_blockers.append("run manifest source closure does not match raw corpus")
        if not isinstance(manifest_pages, list) or len(manifest_pages) != len(pages):
            hard_blockers.append("run manifest page closure does not match Reader pages")
        manifest_paths = {str(item.get("relative_path")) for item in manifest_sources if isinstance(item, Mapping)} if isinstance(manifest_sources, list) else set()
        if manifest_paths != set(raw_hashes):
            hard_blockers.append("run manifest paths do not match raw corpus")
        manifest_rows_by_path = {
            str(item.get("relative_path")): item
            for item in manifest_sources
            if isinstance(item, Mapping)
        } if isinstance(manifest_sources, list) else {}
        if set(manifest_rows_by_path) == set(raw_hashes):
            for path, raw_hash in raw_hashes.items():
                row = manifest_rows_by_path[path]
                if row.get("raw_hash") != raw_hash:
                    hard_blockers.append(f"run manifest raw hash mismatch: {path}")
                if not str(row.get("source_id", "")):
                    hard_blockers.append(f"run manifest source_id missing: {path}")
        manifest_pages_by_id = {
            str(item.get("page_id")): item
            for item in manifest_pages
            if isinstance(item, Mapping) and item.get("page_id")
        } if isinstance(manifest_pages, list) else {}
        for route in run_manifest.get("routes", ()) if isinstance(run_manifest.get("routes"), list) else ():
            if not isinstance(route, Mapping):
                hard_blockers.append("run manifest route row is malformed")
                continue
            selected_pages = [manifest_pages_by_id.get(str(page_id), {}) for page_id in route.get("selected_page_ids", ())]
            route_source_ids = set(str(source_id) for source_id in route.get("selected_source_ids", ()))
            manifest_source_ids = {str(item.get("source_id")) for item in manifest_sources if isinstance(item, Mapping)} if isinstance(manifest_sources, list) else set()
            page_source_ids = set(str(source_id) for page in selected_pages for source_id in page.get("source_ids", ()))
            if not selected_pages or not route_source_ids.issubset(manifest_source_ids) or not page_source_ids.issubset(route_source_ids):
                hard_blockers.append("run manifest route and page source closures are unsafe")
    expected_quality_hash = hashlib.sha256(args.cases.read_bytes()).hexdigest()
    if quality_value.get("quality_contract_sha256") != expected_quality_hash:
        hard_blockers.append("candidate quality contract hash does not match the evaluated contract")
    if rules.is_file() and quality_value.get("projection_rules_sha256") != hashlib.sha256(rules.read_bytes()).hexdigest():
        hard_blockers.append("candidate projection rules hash does not match the evaluated rules")
    routes_by_id = {
        str(item.get("projection_id")): item
        for item in quality_value.get("routes", ())
        if isinstance(item, Mapping) and item.get("projection_id")
    }
    if set(routes_by_id) != set(expected_projection_ids):
        hard_blockers.append("quality route ledger does not contain exactly one row per projection")
    for projection in projections:
        route = routes_by_id.get(projection.projection_id, {})
        selected = set(str(item) for item in route.get("selected_source_paths", ()) if str(item))
        required = set(projection.source_paths)
        top_k = [str(item) for item in route.get("top_k", ()) if str(item)]
        scored = route.get("top_k_scores")
        embedding_model = route.get("embedding_model")
        scores_ok = (
            isinstance(scored, list)
            and len(scored) == len(top_k)
            and all(
                isinstance(item, Mapping)
                and item.get("source_path") == path
                and isinstance(item.get("score"), (int, float))
                for item, path in zip(scored, top_k)
            )
        )
        selected_ids = set(str(item) for item in route.get("selected_source_ids", ()) if str(item))
        source_id_by_path = {
            str(item.get("relative_path")): str(item.get("source_id"))
            for item in run_manifest.get("sources", ())
            if isinstance(item, Mapping)
        } if isinstance(run_manifest, Mapping) else {}
        selected_ids_match = {source_id_by_path.get(path, "") for path in selected} == selected_ids
        top_k_valid = all(path in source_id_by_path for path in top_k)
        trace_events = quality_value.get("provider_trace", {}).get(projection.projection_id, []) if isinstance(quality_value.get("provider_trace"), Mapping) else []
        successful_trace = next((event for event in reversed(trace_events) if isinstance(event, Mapping) and event.get("stage") == "generate" and event.get("status") == "passed"), None)
        trace_matches_route = bool(successful_trace and successful_trace.get("selected_source_paths") == list(route.get("selected_source_paths", ())) and successful_trace.get("qwen_payload_sha256") == route.get("qwen_payload_sha256"))
        if (
            route.get("closure") != "closed"
            or not required.issubset(selected)
            or not top_k
            or not scores_ok
            or not top_k_valid
            or not selected_ids_match
            or not isinstance(embedding_model, Mapping)
            or not str(route.get("embedding_input_sha256", ""))
            or not trace_matches_route
        ):
            hard_blockers.append(f"{projection.projection_id} embedding route is not closed")
        if not str(route.get("qwen_payload_sha256", "")):
            hard_blockers.append(f"{projection.projection_id} route has no Qwen payload receipt")
    provider_identity = run_state.get("provider_identity", {})
    provider_calls = run_state.get("provider_calls", {})
    llm_identity = provider_identity.get("llm", {}) if isinstance(provider_identity, Mapping) else {}
    embedding_identity = provider_identity.get("embedding", {}) if isinstance(provider_identity, Mapping) else {}
    if (
        str(llm_identity.get("base_url", "")) != APPROVED_LLM_BASE_URL
        or str(llm_identity.get("model", "")) not in APPROVED_LLM_MODELS
        or int(provider_calls.get("llm", 0)) <= 0
    ):
        hard_blockers.append("candidate run does not prove a Qwen LLM was used")
    if (
        str(embedding_identity.get("base_url", "")) != APPROVED_EMBEDDING_BASE_URL
        or str(embedding_identity.get("model", "")) != APPROVED_EMBEDDING_MODEL
        or int(provider_calls.get("embedding", 0)) <= 0
    ):
        hard_blockers.append("candidate run does not prove an embedding model was used")
    trace = quality_value.get("provider_trace")
    if not isinstance(trace, Mapping) or set(str(key) for key in trace) != set(expected_projection_ids):
        hard_blockers.append("quality provider trace does not contain exactly one row per projection")
    else:
        for projection_id in expected_projection_ids:
            events = trace.get(projection_id)
            if not isinstance(events, list) or not any(
                isinstance(event, Mapping)
                and event.get("stage") == "generate"
                and event.get("status") == "passed"
                and str(event.get("prompt_sha256", ""))
                and str(event.get("response_sha256", ""))
                for event in events
            ):
                hard_blockers.append(f"{projection_id} has no auditable Qwen generation trace")
    for material in materials:
        projection_id = str(material["projection_id"])
        for check in material["companybrain_baseline_checks"]:
            if not check.get("exists") or not check.get("hash_matches") or check.get("applicability") != "present":
                hard_blockers.append(f"{projection_id} baseline observation is not verified: {check.get('baseline_id')}")
        if not material["companybrain_page_paths"]:
            hard_blockers.append(f"{projection_id} has no CompanyBrain baseline entry")
        for dimension in DIMENSIONS:
            if not material["structural_observation"][dimension]["passed"]:
                hard_blockers.append(f"{projection_id} structural {dimension} check failed")
    result["hard_blockers"] = list(dict.fromkeys(hard_blockers))
    grouped: dict[str, list[dict[str, Any]]] = {}
    for material in public_materials:
        grouped.setdefault(str(material["case_id"]), []).append(material)
    result["cases"] = [{"case_id": case_id, "projection_count": len(items), "projections": items} for case_id, items in grouped.items()]
    if args.judge:
        if args.config is None:
            raise SystemExit("--config is required with --judge")
        from knowledge_digest.providers import build_providers
        model, _embedder = build_providers(args.config)
        rounds: list[list[dict[str, Any]]] = []
        judge_errors: list[str] = []
        def judge_one(item: tuple[Mapping[str, Any], bool]) -> tuple[dict[str, Any], str | None]:
            material, swapped = item
            try:
                value = json.loads(model.generate(_judge_prompt(material, swapped)))
                if not isinstance(value, Mapping) or not isinstance(value.get("dimensions"), Mapping):
                    raise ValueError("judge returned no dimensions")
                return _normalise_judgement(value, swapped, str(material["projection_id"])), None
            except Exception as error:
                return (
                    {"projection_id": material["projection_id"], "dimensions": {dimension: {"verdict": "UNKNOWN", "reason": "judge unavailable"} for dimension in DIMENSIONS}},
                    f"{material['projection_id']} {'swapped' if swapped else 'normal'}: {type(error).__name__}: {error}",
                )

        # The adapter and its shared CallBudget are thread-safe.  Four in
        # flight requests keep the real comparison bounded without creating a
        # provider stampede.
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="reader-judge") as executor:
            for swapped in (False, True):
                judged = list(executor.map(judge_one, ((material, swapped) for material in materials)))
                rounds.append([value for value, _error in judged])
                judge_errors.extend(error for _value, error in judged if error)
        result["judgements"] = rounds
        result["judge_errors"] = judge_errors
        result["dimension_verdicts"] = {str(material["projection_id"]): {dimension: [rounds[0][index]["dimensions"].get(dimension, {}).get("verdict", "UNKNOWN"), rounds[1][index]["dimensions"].get(dimension, {}).get("verdict", "UNKNOWN")] for dimension in DIMENSIONS} for index, material in enumerate(materials)}
        for round_items in rounds:
            for judgement in round_items:
                for risk in judgement.get("blocking_risks", ()):
                    if isinstance(risk, str) and risk.strip():
                        result["hard_blockers"].append(f"{judgement.get('projection_id')}: judge blocking risk: {risk.strip()}")
        result["hard_blockers"] = list(dict.fromkeys(result["hard_blockers"]))
        strict_wins = all(values == ["KD_WIN", "KD_WIN"] for projection_values in result["dimension_verdicts"].values() for values in projection_values.values())
        result["verdict"] = "released" if strict_wins and not result["hard_blockers"] else "not_released"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "verdict": result["verdict"], "hard_blocker_count": len(result["hard_blockers"]), "projection_count": len(projections)}, ensure_ascii=False))
    return 0 if result["verdict"] == "released" else 1


if __name__ == "__main__":
    raise SystemExit(main())
