"""Deterministic, read-only mapping from Task4 cases to CompanyBrain pages."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "task4-companybrain-mapping.v2"
_GENERIC = {"产品", "模块手册", "产品定位", "经验与坑", "规范与资产", "技术实现", "资料汇总", "总览", "index"}
_STOP = {"ae", "emm", "android", "ios", "global", "system", "merchant", "management", "portal", "reseller"}
_ORACLE_NOISE = {"默认", "不能", "不支", "必须", "最多", "至少", "权限", "来源", "为了", "能让"}
_ACTION_TERMS = {"创建", "新建", "添加", "编辑", "删除", "管理", "操作", "查看", "设置", "配置", "更改", "重置", "激活", "停用", "发布", "安装", "升级", "注册", "订阅", "登录"}
_TASK_PATTERNS = (
    ("重置密码&更改邮箱", "account"),
    ("编辑&删除", "maintain"),
    ("激活&停用", "lifecycle"),
    ("远程控制", "remote_control"),
    ("定向发布", "distribute"),
    ("零接触", "enroll"),
    ("二维码", "enroll"),
    ("注册", "enroll"),
    ("入网", "enroll"),
    ("分发", "distribute"),
    ("发布", "distribute"),
    ("创建", "create"),
    ("新建", "create"),
    ("添加", "add"),
    ("上传", "upload"),
    ("删除", "delete"),
    ("编辑", "edit"),
    ("配置", "configure"),
    ("设置", "configure"),
    ("策略", "configure"),
    ("参数", "configure"),
    ("筛选", "filter"),
    ("管理", "manage"),
    ("运维", "manage"),
    ("日志", "audit"),
    ("审计", "audit"),
    ("列表", "browse"),
    ("详情", "browse"),
    ("查询", "browse"),
    ("报告", "report"),
    ("快照", "report"),
    ("数据集", "dataset"),
    ("迁移", "migrate"),
    ("订阅", "subscribe"),
    ("账单", "billing"),
    ("支付", "billing"),
    ("sso", "identity"),
    ("权限", "permission"),
    ("角色", "permission"),
    ("分析", "analysis"),
    ("类型", "reference"),
    ("规范", "reference"),
    ("介绍", "overview"),
    ("简介", "overview"),
    ("q&a", "overview"),
)
_SEMANTIC_NOISE = {"页面", "页", "文档", "流程", "相关", "以及", "与", "及", "的", "大全", "总览"}
_FRONTMATTER_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _baseline_files(root: Path) -> list[Path]:
    """Return the frozen CompanyBrain file scope.

    The Task4 baseline is the full non-system file tree, not only the curated
    Markdown pages used as Reader targets.  A file whose own name starts with
    ``.`` is system noise (for example ``.DS_Store``); files below ordinary
    directories remain part of the frozen tree.  This matches the 1,406-file
    baseline contract and makes changes to auxiliary manifests/configuration
    visible instead of silently narrowing the comparison scope.
    """
    return [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink() and not path.name.startswith(".")
    ]


def _baseline_entries(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "byte_count": path.stat().st_size,
            "sha256": _sha256(path.read_bytes()),
        }
        for path in _baseline_files(root)
    ]


def tree_hash(root: Path) -> str:
    entries = _baseline_entries(root)
    payload = {
        "scope": "all_regular_non_dotname_files",
        "file_count": len(entries),
        "entries": entries,
    }
    return _sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def source_manifest_hash(source_manifest: Mapping[str, Any] | None) -> str | None:
    """Hash source identity/content, excluding run-specific timestamps and paths."""
    if not isinstance(source_manifest, Mapping):
        return None
    entries = []
    for row in source_manifest.get("entries", []):
        if not isinstance(row, Mapping):
            continue
        entries.append({
            key: row.get(key)
            for key in ("source_uri", "source_id", "source_snapshot_id", "content_hash", "byte_count", "status", "title", "product", "module", "topic_key")
        })
    entries.sort(key=lambda row: str(row.get("source_uri", "")))
    return _sha256(json.dumps({"source_count": len(entries), "entries": entries}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def normalize(value: Any) -> str:
    value = unicodedata.normalize("NFKC", str(value)).casefold()
    value = re.sub(r"\.(?:md|markdown|txt)$", "", value)
    value = re.sub(r"^\s*\d+[.)、]?\s*", "", value)
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[和与及]", "", value)
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value)


def _semantic_title(value: Any) -> str:
    title = unicodedata.normalize("NFKC", str(value)).strip()
    title = title.split("_", 1)[0].strip()
    title = re.sub(r"^\s*(?:\[?ae\]?|emm|airviewer|android|ios|global|maxstore)\s*[-_:：]?\s*", "", title, flags=re.I)
    title = re.sub(r"^\s*\d+[.)、]?\s*", "", title)
    return title.strip()


def _semantic_task(title: str) -> str:
    lowered = _semantic_title(title).casefold()
    for phrase, task in _TASK_PATTERNS:
        if phrase.casefold() in lowered:
            return task
    return "describe"


def _semantic_object(title: str) -> str:
    cleaned = _semantic_title(title)
    for phrase, _task in _TASK_PATTERNS:
        cleaned = re.sub(re.escape(phrase), " ", cleaned, flags=re.I)
    cleaned = re.sub(r"[\[\]（）()【】、，,：:；;·•&+\-/]+", " ", cleaned)
    words = [word for word in re.split(r"\s+", cleaned) if word and word not in _SEMANTIC_NOISE]
    return "".join(words) or _semantic_title(title)


def comparison_key(
    *,
    product_or_domain: Any,
    module: Any,
    object_or_scenario: Any,
    task: Any,
    page_type: Any,
) -> str:
    """Build a stable typed identity hash for one Reader comparison topic."""
    fields = (product_or_domain, module, object_or_scenario, task, page_type)
    if any(not str(field or "").strip() for field in fields):
        raise ValueError("semantic comparison key fields must be non-empty")
    identity = {
        "schema": "reader-comparison-key.v1",
        "product_or_domain": normalize(product_or_domain),
        "module": normalize(module),
        "object_or_scenario": normalize(object_or_scenario),
        "task": normalize(task),
        "page_type": normalize(page_type),
    }
    canonical = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "ck1:" + _sha256(canonical)


def semantic_fields(*, product_or_domain: Any, module: Any, title: Any, page_type: Any) -> dict[str, str]:
    object_or_scenario = _semantic_object(str(title))
    task = _semantic_task(str(title))
    return {
        "product_or_domain": str(product_or_domain or "").strip(),
        "module": str(module or "").strip(),
        "object_or_scenario": object_or_scenario,
        "task": task,
        "page_type": str(page_type or "").strip(),
        "comparison_key": comparison_key(
            product_or_domain=product_or_domain,
            module=module,
            object_or_scenario=object_or_scenario,
            task=task,
            page_type=page_type,
        ),
    }


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    marker = text.find("\n---\n", 4)
    if marker < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[4:marker].splitlines():
        match = _FRONTMATTER_LINE.match(line)
        if match:
            result[match.group(1)] = match.group(2).strip().strip("'\"")
    return result


def _baseline_page_semantic_fields(page: Mapping[str, Any]) -> dict[str, str] | None:
    path = Path(str(page["path"]))
    metadata = page.get("metadata", {})
    if not isinstance(metadata, Mapping):
        metadata = {}
    parts = path.parts
    product = str(metadata.get("product") or (parts[1] if len(parts) > 1 and parts[0] == "Products" else ""))
    if not product:
        return None
    module_parts = [metadata.get(key) for key in ("section", "subproduct", "module") if metadata.get(key)]
    if module_parts:
        module = "/".join(str(item) for item in module_parts)
    elif len(parts) > 2 and parts[0] == "Products":
        module = "/".join(parts[2:-1])
    else:
        module = ""
    if not module:
        return None
    page_type = str(metadata.get("page_type") or "procedure")
    if page_type not in {"procedure", "diagnostic"}:
        # The current Task4 case registry asks a procedure question even when
        # CompanyBrain stores the answer as a reference/rule page.
        page_type = "procedure"
    try:
        return semantic_fields(product_or_domain=product, module=module, title=page["title"], page_type=page_type)
    except ValueError:
        # Navigation/overview pages can have no stable object identity (for
        # example a page titled only after the product name).  They remain in
        # the Reader page inventory, but must not enter the exact-key index.
        return None


def _baseline_page_semantic_candidates(page: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return identities explicitly named by a page title or its headings."""
    text = str(page.get("text", ""))
    candidates: list[dict[str, Any]] = []
    headings: list[tuple[str, int]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append((re.sub(r"[*_`~]", "", match.group(2)).strip(), line_number))
    if not headings:
        headings = [(str(page.get("title", "")), 1)]
    for heading, line_number in headings:
        fields = _baseline_page_semantic_fields({**page, "title": heading})
        if fields:
            candidates.append({
                "semantic_fields": fields,
                "title": heading,
                "evidence_refs": [{
                    "path": str(page["path"]),
                    "line_start": line_number,
                    "line_end": line_number,
                    "kind": "baseline_heading",
                }],
            })
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in candidates:
        key = (candidate["semantic_fields"]["comparison_key"], str(page["path"]))
        unique.setdefault(key, candidate)
    return list(unique.values())


def _tokens(value: str) -> set[str]:
    value = normalize(value)
    tokens = set(re.findall(r"[a-z0-9]{2,}", value))
    tokens.update(value[index:index + 2] for index in range(len(value) - 1) if re.fullmatch(r"[\u4e00-\u9fff]{2}", value[index:index + 2]))
    return {token for token in tokens if token not in _GENERIC and token not in _STOP}


def _term_chunks(value: str) -> set[str]:
    """Use stable two-character Chinese chunks, avoiding cross-word ngrams."""
    normalized = normalize(value)
    terms: set[str] = set()
    for chunk in re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]+", normalized):
        if re.fullmatch(r"[a-z0-9]+", chunk):
            terms.add(chunk)
        else:
            terms.update(chunk[index:index + 2] for index in range(0, len(chunk) - 1, 2))
    return {term for term in terms if term not in _GENERIC and term not in _STOP}


def _content_terms(value: str) -> set[str]:
    """Use sliding Chinese bigrams for body retrieval; titles stay stricter."""
    normalized = normalize(value)
    terms: set[str] = set()
    for chunk in re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]+", normalized):
        if re.fullmatch(r"[a-z0-9]+", chunk):
            terms.add(chunk)
        else:
            terms.update(chunk[index:index + 2] for index in range(len(chunk) - 1))
    return {term for term in terms if term not in _GENERIC and term not in _STOP}


def _case_subject(case: Mapping[str, Any]) -> str:
    title = str(case.get("target_title") or "")
    # Exported Confluence names commonly put the real subject before the first
    # breadcrumb underscore.  Keep underscores inside an ordinary title only
    # when no breadcrumb-like suffix is present.
    subject = title.split("_", 1)[0].strip()
    subject = re.sub(r"^\s*(?:\[?ae\]?|emm)\s*[-_:：]?\s*", "", subject, flags=re.I)
    subject = re.sub(r"^\s*\d+[.)、]?\s*", "", subject)
    return subject.strip() or title


def _case_identity_terms(case: Mapping[str, Any]) -> set[str]:
    """Return title/claim terms that can identify a baseline topic.

    Required claims are stronger identity evidence than generic module words,
    but common oracle boundary words must not manufacture a title match.
    """
    terms = _term_chunks(_case_subject(case))
    for claim in case.get("required_claims", []) or []:
        terms.update(_term_chunks(str(claim)))
    return {term for term in terms if term not in _ORACLE_NOISE}


def _page_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return re.sub(r"[*_`~]", "", match.group(1)).strip()
    return path.stem


def _source_context(source_manifest: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not isinstance(source_manifest, Mapping):
        return {}
    rows = source_manifest.get("entries", [])
    return {str(row.get("source_id")): row for row in rows if isinstance(row, Mapping) and row.get("source_id")}


def _score(case: Mapping[str, Any], page: Mapping[str, Any], source: Mapping[str, Any] | None) -> tuple[int, list[str]]:
    subject = _case_subject(case)
    identity_terms = _case_identity_terms(case)
    page_title = str(page["title"])
    subject_norm = normalize(subject)
    page_norm = normalize(page_title)
    reasons: list[str] = []
    score = 0
    frequencies = page.get("title_token_frequency", {})
    if "总览" in page_title or normalize(page_title) in {"概览", "模块总览"}:
        # An overview is a navigation aid, not the semantic target when the
        # source names a concrete task or object.  Keep it as a candidate for
        # audit, but do not let shared module words make it win the mapping.
        score -= 25
        reasons.append("generic_overview_penalty")
    if subject_norm and subject_norm == page_norm:
        score += 100
        reasons.append("title_exact")
    elif subject_norm and (subject_norm in page_norm or page_norm in subject_norm):
        score += 55
        reasons.append("title_contains")
    subject_tokens_all = _term_chunks(subject)
    subject_tokens = set(subject_tokens_all)
    if source:
        subject_tokens -= _term_chunks(str(source.get("module", "")))
    title_tokens = _term_chunks(page_title)
    # Keep the original subject tokens for title identity.  Removing module
    # words here made a page with only one generic word (for example 删除 or
    # 管理) look like a semantic match.  Module words are still removed for
    # content overlap below, where they are useful as context rather than
    # identity.
    overlap = identity_terms & title_tokens
    if overlap:
        score += min(60, sum(20 if int(frequencies.get(token, 99)) <= 2 else 9 for token in overlap))
        reasons.append("title_tokens:" + ",".join(sorted(overlap)))
    title_claims = {
        normalize(str(claim))
        for claim in case.get("required_claims", []) or []
        if normalize(str(claim)) and normalize(str(claim)) in page_norm
    }
    if title_claims:
        score += min(48, len(title_claims) * 24)
        reasons.append("title_claims:" + ",".join(sorted(title_claims)))
    content_tokens = _content_terms(str(page.get("text", "")))
    content_overlap = subject_tokens & content_tokens
    if content_overlap:
        score += min(45, sum(15 if int(frequencies.get(token, 99)) <= 3 else 6 for token in content_overlap))
        reasons.append("content_tokens:" + ",".join(sorted(content_overlap)))
    source_content_terms = _content_terms(str(source.get("source_text", ""))) if source else set()
    source_content_overlap = source_content_terms & content_tokens
    content_frequencies = page.get("content_token_frequency", {})
    rare_source_overlap = {
        token for token in source_content_overlap
        if int(content_frequencies.get(token, 99)) <= 3
    }
    if rare_source_overlap:
        score += min(90, len(rare_source_overlap) * 6)
        reasons.append("source_content:" + ",".join(sorted(rare_source_overlap)[:12]))
    if source:
        product = normalize(source.get("product", ""))
        module_name = str(source.get("module", "")).rsplit("/", 1)[-1]
        module_tokens = _term_chunks(module_name)
        path_parts = Path(str(page["path"])).parts
        path_product = normalize(path_parts[1]) if len(path_parts) > 1 and path_parts[0] == "Products" else ""
        if product and product == path_product:
            score += 20
            reasons.append("product_path")
        path_norm = normalize(page["path"])
        module_overlap = {token for token in module_tokens if token in path_norm}
        if module_overlap:
            score += min(36, len(module_overlap) * 18)
            reasons.append("module_path:" + ",".join(sorted(module_overlap)))
        source_module_norm = normalize(str(source.get("module", "")))
        for platform in ("android", "ios"):
            if platform in source_module_norm:
                opposite = "ios" if platform == "android" else "android"
                if opposite in path_norm:
                    score -= 80
                    reasons.append(f"platform_path_conflict:{opposite}")
                elif platform in path_norm:
                    score += 30
                    reasons.append(f"platform_path:{platform}")
    return score, reasons


def build_mapping(
    companybrain_root: Path,
    cases: list[Mapping[str, Any]],
    source_manifest: Mapping[str, Any] | None = None,
    source_texts: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    pages: list[dict[str, Any]] = []
    for path in sorted(Path(companybrain_root).rglob("*.md")):
        if path.is_symlink() or not path.is_file() or "_config" in path.relative_to(companybrain_root).parts:
            continue
        relative = path.relative_to(companybrain_root).as_posix()
        if relative.startswith("_gbrain/"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        pages.append({"path": relative, "title": _page_title(path, text), "text": text, "metadata": _frontmatter(text), "sha256": _sha256(path.read_bytes())})
    frequencies: dict[str, int] = {}
    content_frequencies: dict[str, int] = {}
    for page in pages:
        for token in _term_chunks(str(page["title"])):
            frequencies[token] = frequencies.get(token, 0) + 1
        for token in _content_terms(str(page["text"])):
            content_frequencies[token] = content_frequencies.get(token, 0) + 1
    for page in pages:
        page["title_token_frequency"] = frequencies
        page["content_token_frequency"] = content_frequencies
    source_by_id = _source_context(source_manifest)
    for source_id, source_text in (source_texts or {}).items():
        if source_id in source_by_id:
            source_by_id[source_id] = {**source_by_id[source_id], "source_text": source_text}
    result: list[dict[str, Any]] = []
    exact_mode = all(
        (source_by_id.get(str(case.get("source_snapshot_id")), {}).get("status") != "valid")
        or all(str(case.get(field) or "").strip() for field in ("product_or_domain", "module", "object_or_scenario", "task", "page_type", "comparison_key"))
        for case in cases
    )
    exact_index: dict[str, list[dict[str, Any]]] = {}
    if exact_mode:
        for page in pages:
            for supported in _baseline_page_semantic_candidates(page):
                fields = supported["semantic_fields"]
                exact_index.setdefault(fields["comparison_key"], []).append({
                    "path": page["path"],
                    "title": supported["title"],
                    "sha256": page["sha256"],
                    "semantic_fields": fields,
                    "identity_evidence_refs": supported["evidence_refs"],
                })
    for case in cases:
        source = source_by_id.get(str(case.get("source_snapshot_id")))
        if not source or source.get("status") != "valid":
            result.append({
                "case_id": str(case.get("case_id")),
                "target_title": case.get("target_title"),
                "source_snapshot_id": case.get("source_snapshot_id"),
                "status": "undecidable" if exact_mode else "unmatched",
                "entry_path": None,
                "top_score": 0,
                "runner_up_score": 0,
                "basis": ["source_context_unavailable"],
                "candidate_paths": [],
            })
            continue
        if exact_mode:
            expected_key = comparison_key(
                product_or_domain=case["product_or_domain"],
                module=case["module"],
                object_or_scenario=case["object_or_scenario"],
                task=case["task"],
                page_type=case["page_type"],
            )
            key = str(case["comparison_key"])
            candidates = exact_index.get(key, []) if key == expected_key else []
            if len(candidates) == 1:
                candidate = candidates[0]
                result.append({
                    "case_id": str(case.get("case_id")),
                    "target_title": case.get("target_title"),
                    "source_snapshot_id": case.get("source_snapshot_id"),
                    "comparison_key": key,
                    "status": "unique",
                    "entry_path": candidate["path"],
                    "entry_sha256": candidate["sha256"],
                    "top_score": None,
                    "runner_up_score": None,
                    "basis": ["exact_comparison_key", "frozen_baseline_heading_index"],
                    "candidate_paths": [item["path"] for item in candidates],
                    "identity_evidence_refs": candidate["identity_evidence_refs"],
                })
            elif len(candidates) > 1:
                result.append({
                    "case_id": str(case.get("case_id")),
                    "target_title": case.get("target_title"),
                    "source_snapshot_id": case.get("source_snapshot_id"),
                    "comparison_key": key,
                    "status": "ambiguous",
                    "entry_path": None,
                    "entry_sha256": None,
                    "top_score": None,
                    "runner_up_score": None,
                    "basis": ["exact_comparison_key_duplicate"],
                    "candidate_paths": [item["path"] for item in candidates],
                })
            else:
                result.append({
                    "case_id": str(case.get("case_id")),
                    "target_title": case.get("target_title"),
                    "source_snapshot_id": case.get("source_snapshot_id"),
                    "comparison_key": key,
                    "status": "not_applicable",
                    "entry_path": None,
                    "entry_sha256": None,
                    "top_score": None,
                    "runner_up_score": None,
                    "basis": ["exact_key_absent_from_exhaustive_reader_page_scope"],
                    "candidate_paths": [],
                    "not_applicable_reason": "baseline_exhaustive_reader_page_scope_has_no_entry_for_frozen_comparison_key",
                })
            continue
        ranked: list[tuple[int, dict[str, Any], list[str]]] = []
        for page in pages:
            score, reasons = _score(case, page, source)
            if score > 0 and not any(reason.startswith("platform_path_conflict:") for reason in reasons):
                ranked.append((score, page, reasons))
        ranked.sort(key=lambda row: (-row[0], row[1]["path"]))
        top = ranked[0] if ranked else None
        second_score = ranked[1][0] if len(ranked) > 1 else 0
        # A unique baseline needs a real title signal and a clear margin.  A
        # weak token hit is reported as unmatched, never guessed as N/A.
        product_required = bool(source and source.get("product"))
        product_match = "product_path" in (top[2] if top else [])
        title_reasons = top[2] if top else []
        title_token_terms = next((reason.split(":", 1)[1].split(",") for reason in title_reasons if reason.startswith("title_tokens:")), [])
        title_claim_terms = next((reason.split(":", 1)[1].split(",") for reason in title_reasons if reason.startswith("title_claims:")), [])
        semantic_title_claims = [term for term in title_claim_terms if term not in _ACTION_TERMS]
        strong_title = bool(top and ("title_exact" in title_reasons or "title_contains" in title_reasons or len(title_token_terms) >= 2 or semantic_title_claims))
        # Body overlap is retrieval evidence only.  It cannot establish a
        # unique baseline identity: generic words such as 删除/管理 can make
        # an unrelated page score highly.  Only a strong title identity can
        # authorize the frozen entry_path.
        strong_score = bool(top and (top[0] >= 75 or (semantic_title_claims and top[0] >= 45)))
        strong_match = bool(top and strong_score and strong_title and (not product_required or product_match))
        if strong_match and top[0] > second_score:
            status = "unique"
            entry_path = top[1]["path"]
        elif strong_match and top[0] == second_score:
            status = "ambiguous"
            entry_path = None
        else:
            status = "unmatched"
            entry_path = None
        result.append({
            "case_id": str(case.get("case_id")),
            "target_title": case.get("target_title"),
            "source_snapshot_id": case.get("source_snapshot_id"),
            "status": status,
            "entry_path": entry_path,
            "entry_sha256": top[1]["sha256"] if entry_path else None,
            "top_score": top[0] if top else 0,
            "runner_up_score": second_score,
            "basis": top[2] if top else [],
            "candidate_paths": [row[1]["path"] for row in ranked[:5]],
        })
    counts = {status: sum(row["status"] == status for row in result) for status in ("unique", "ambiguous", "not_applicable", "undecidable", "unmatched")}
    baseline_entries = _baseline_entries(Path(companybrain_root))
    supported_by_path: dict[str, list[dict[str, Any]]] = {}
    if exact_mode:
        for key, values in exact_index.items():
            for value in values:
                supported_by_path.setdefault(str(value["path"]), []).append({
                    "comparison_key": key,
                    "title": value["title"],
                    "identity_evidence_refs": value["identity_evidence_refs"],
                })
    manifest_entries: list[dict[str, Any]] = []
    for entry in baseline_entries:
        item = dict(entry)
        path = companybrain_root / str(entry["path"])
        if path.suffix.casefold() == ".md":
            item["title"] = _page_title(path, path.read_text(encoding="utf-8", errors="replace"))
            supports = supported_by_path.get(str(entry["path"]), [])
            if supports:
                item["supported_comparison_keys"] = sorted({str(value["comparison_key"]) for value in supports})
                item["identity_evidence_refs"] = [ref for value in supports for ref in value["identity_evidence_refs"]]
        manifest_entries.append(item)
    return {
        "schema_version": "task4-companybrain-mapping.v3" if exact_mode else SCHEMA_VERSION,
        "mapping_id": "companybrain-task4-exact-map-v1" if exact_mode else "companybrain-task4-auto-map-v1",
        "mapping_mode": "exact_semantic_key_v1" if exact_mode else "fuzzy_diagnostic_v2",
        "companybrain_manifest": {
            "root_label": "CompanyBrain",
            "manifest_id": "companybrain-full-20260819-current-v2",
            "tree_hash": tree_hash(Path(companybrain_root)),
            "scope": "all_regular_non_dotname_files",
            "file_count": len(baseline_entries),
            "page_count": len(pages),
            "reader_page_scope": {
                "scope_id": "companybrain-reader-pages-20260819-v1",
                "exhaustive": True,
                "rule": "all_regular_non_dotname_markdown_excluding__gbrain_and__config",
                "page_count": len(pages),
            },
            "entries": manifest_entries,
        },
        "key_index": [
            {
                "comparison_key": key,
                "entry_paths": [item["path"] for item in values],
                "identity_evidence_refs": [ref for item in values for ref in item["identity_evidence_refs"]],
            }
            for key, values in sorted(exact_index.items())
        ] if exact_mode else [],
        "source_manifest_hash": source_manifest_hash(source_manifest),
        "case_count": len(result),
        "counts": counts,
        "cases": result,
    }
