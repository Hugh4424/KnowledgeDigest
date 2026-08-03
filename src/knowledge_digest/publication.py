"""Semantic publication metadata and fail-closed field validation.

The provider may suggest reader-facing wording, but this module remains the
authority for taxonomy membership, claim references, deterministic fallbacks,
and the needs-review boundary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from .errors import ValidationError
from .identity import readable_slug
from .kb_structure import PublicationContract


_SCHEMA_FIELDS = ("title", "slug", "category_id", "summary", "why", "version", "related_topics", "claim_refs", "field_refs")
_FIELD_REF_NAMES = ("title", "category_id", "summary", "why", "version")
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
_NUMERIC_RE = re.compile(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?%?(?![A-Za-z0-9_])")
_IDENTIFIER_RE = re.compile(r"\b[A-Z][A-Z0-9_-]{2,}\b")


@dataclass(frozen=True)
class PublicationMetadata:
    title: str
    slug: str
    category_id: str
    summary: str
    why: str
    version: str
    related_topics: tuple[str, ...] = ()
    claim_refs: tuple[str, ...] = ()
    field_refs: dict[str, tuple[str, ...]] = field(default_factory=dict)
    field_status: dict[str, str] = field(default_factory=dict)
    needs_review: bool = False
    fallback_reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "slug": self.slug,
            "category_id": self.category_id,
            "summary": self.summary,
            "why": self.why,
            "version": self.version,
            "related_topics": list(self.related_topics),
            "claim_refs": list(self.claim_refs),
            "field_refs": {key: list(value) for key, value in self.field_refs.items()},
            "field_status": dict(self.field_status),
            "needs_review": self.needs_review,
            "fallback_reasons": list(self.fallback_reasons),
        }


def deterministic_category_id(text: str, publication: PublicationContract) -> str:
    """Choose a conservative reader category when no provider suggestion exists.

    This is deliberately a small, auditable fallback rather than an attempt to
    replace semantic classification.  Unknown material remains in ``pending``;
    known product/engineering/customer/operations/principle terms are routed to
    the most specific declared leaf whose aliases match.
    """
    normalized = str(text or "").casefold()
    if not normalized or len(publication.categories) <= 1:
        return publication.pending_category.category_id
    # Source paths/titles are intentionally included by the caller.  These
    # rules are conservative and explainable: a category wins only when its
    # domain terms outscore the others; otherwise the item stays reviewable.
    leaf_terms = {
        "architecture": ("架构", "architecture", "部署方案", "deployment", "系统设计"),
        "implementation": ("api", "接口", "代码", "sdk", "token", "auth", "实现", "开发者"),
        "operations-troubleshooting": ("bug", "error", "故障", "排障", "日志", "监控", "问题分析"),
        "development-practice": ("sprint", "迭代", "研发实践", "retrospective", "开发流程"),
        "project": ("项目", "project", "方案", "里程碑"),
        "management": ("权限", "角色", "管理", "组织", "global system"),
        "people": ("年假", "annual leave", "人员", "team", "会议", "meeting"),
        "competitor": ("竞品", "competitor"),
        "event": ("活动", "event", "发布会"),
        "customer-case": ("客户案例", "customer case", "商户需求", "售后"),
        "customer-overview": ("客户", "商户", "用户", "merchant", "customer"),
        "market-feedback": ("市场", "反馈", "调研", "feedback"),
        "product-overview": ("产品概览", "产品介绍", "product overview"),
        "product-capability": ("功能", "模块", "终端", "设备", "应用", "支付", "产品能力"),
        "product-operations": ("安装", "使用", "运营", "配置", "收费"),
        "product-boundary": ("边界", "限制", "不支持", "兼容"),
        "business-principle": ("原则", "规范", "标准", "制度"),
        "content-standard": ("文档规范", "内容规范", "模板", "邮件模板"),
        "delivery-standard": ("交付", "上线", "发布规范", "验收"),
        "unclassified": ("其他",),
    }
    scores = {
        category.category_id: sum(
            1 for term in leaf_terms.get(category.category_id, ()) if term.casefold() in normalized
        )
        for category in publication.categories
        if category.category_id != publication.pending_category.category_id
    }
    best = max(scores.values(), default=0)
    if best <= 0:
        return publication.pending_category.category_id
    winners = sorted(category_id for category_id, score in scores.items() if score == best)
    return winners[0]


def _claim_key(claim: Mapping[str, Any]) -> str:
    return str(claim.get("claim_fingerprint") or claim.get("raw_id") or "").strip()


def _claim_text(claim: Mapping[str, Any]) -> str:
    return str(claim.get("text") or "")


def _fallback_title(claims: list[Mapping[str, Any]], explicit: str | None) -> str:
    candidates = [explicit, *(str(claim.get("title") or "").strip() for claim in claims)]
    for candidate in candidates:
        if candidate and len(candidate) >= 4:
            return candidate[:80].strip()
    for claim in claims:
        text = _claim_text(claim).strip()
        if text:
            return text[:80].strip()
    return "未命名知识主题"


def _slug_for(title: str, stable_topic_id: str | None = None) -> str:
    try:
        slug = readable_slug(title).encode("ascii", "ignore").decode("ascii")
    except (UnicodeEncodeError, ValidationError):
        slug = ""
    slug = re.sub(r"[^a-z0-9-]+", "-", slug.casefold()).strip("-")[:64]
    if len(slug) < 3:
        suffix = re.sub(r"[^a-z0-9]+", "", (stable_topic_id or "topic"))[-8:] or "topic"
        slug = f"topic-{suffix}"[:64]
    return slug


def _fallback_refs(claims: list[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(key for key in (_claim_key(claim) for claim in claims) if key)


def _field_has_supported_facts(value: str, refs: list[str], by_key: dict[str, Mapping[str, Any]]) -> bool:
    text = "\n".join(_claim_text(by_key[ref]) for ref in refs if ref in by_key)
    for token in (*_NUMERIC_RE.findall(value), *_IDENTIFIER_RE.findall(value)):
        if token not in text:
            return False
    return True


def _fallback_metadata(
    claims: list[Mapping[str, Any]],
    publication: PublicationContract,
    *,
    title: str | None,
    category_id: str | None,
    stable_topic_id: str | None,
    reasons: list[str],
) -> PublicationMetadata:
    claim_refs = _fallback_refs(claims)
    safe_title = _fallback_title(claims, title)
    safe_category = category_id if category_id in {item.category_id for item in publication.categories} else publication.pending_category.category_id
    safe_slug = _slug_for(safe_title, stable_topic_id)
    claim_texts = [text.strip() for text in (_claim_text(claim) for claim in claims) if text.strip()]
    summary = "来源未提供摘要；请阅读 Evidence。"
    version_match = re.search(r"\b(?:v|version|版本)\s*[0-9]+(?:\.[0-9]+){0,3}\b", " ".join(claim_texts), re.IGNORECASE)
    version = version_match.group(0) if version_match else "未提供版本信息"
    fields = {
        "title": claim_refs,
        "category_id": claim_refs,
        "summary": claim_refs,
        "why": claim_refs,
        "version": claim_refs,
    }
    return PublicationMetadata(
        title=safe_title,
        slug=safe_slug,
        category_id=safe_category,
        summary=summary,
        why="来源未说明",
        version=version,
        claim_refs=claim_refs,
        field_refs=fields,
        field_status={name: "fallback" for name in _FIELD_REF_NAMES},
        needs_review=True,
        fallback_reasons=tuple(dict.fromkeys(reasons or ["publication suggestion missing"])),
    )


def validate_publication_suggestion(
    raw: Any,
    *,
    claims: list[dict[str, Any]],
    publication: PublicationContract,
    topic_universe: set[str] | None = None,
    fallback_title: str | None = None,
    stable_topic_id: str | None = None,
    fallback_category_id: str | None = None,
) -> PublicationMetadata:
    """Validate one provider object and fall back field-by-field on defects."""
    if not isinstance(publication, PublicationContract):
        raise ValidationError("publication", "contract", "PublicationContract is required")
    claim_rows = [claim for claim in claims if isinstance(claim, Mapping)]
    by_key = {_claim_key(claim): claim for claim in claim_rows if _claim_key(claim)}
    if not isinstance(raw, Mapping):
        return _fallback_metadata(
            claim_rows,
            publication,
            title=fallback_title,
            category_id=fallback_category_id,
            stable_topic_id=stable_topic_id,
            reasons=["publication object is missing"],
        )
    reasons: list[str] = []
    unknown = sorted(set(raw) - set(_SCHEMA_FIELDS))
    if unknown:
        reasons.append(f"unknown fields: {', '.join(unknown)}")
    raw_refs = raw.get("claim_refs")
    claim_refs = [str(value).strip() for value in raw_refs] if isinstance(raw_refs, list) and all(isinstance(value, str) for value in raw_refs) else []
    if not claim_refs or len(claim_refs) > 80 or any(ref not in by_key for ref in claim_refs) or len(set(claim_refs)) != len(claim_refs):
        reasons.append("claim_refs are not a subset of the current claims")
        claim_refs = list(_fallback_refs(claim_rows))
    ref_set = set(claim_refs)
    field_refs_raw = raw.get("field_refs")
    field_refs: dict[str, tuple[str, ...]] = {}
    if not isinstance(field_refs_raw, Mapping) or set(field_refs_raw) != set(_FIELD_REF_NAMES):
        reasons.append("field_refs schema is invalid")
        field_refs = {name: tuple(claim_refs) for name in _FIELD_REF_NAMES}
    else:
        for name in _FIELD_REF_NAMES:
            value = field_refs_raw.get(name)
            refs = [str(item).strip() for item in value] if isinstance(value, list) and all(isinstance(item, str) for item in value) else []
            if not refs or len(refs) > 16 or any(ref not in ref_set for ref in refs) or len(set(refs)) != len(refs):
                reasons.append(f"field_refs.{name} is invalid")
                refs = list(claim_refs)
            field_refs[name] = tuple(refs)

    def text_field(name: str, maximum: int, fallback: str) -> tuple[str, str]:
        value = raw.get(name)
        refs = list(field_refs[name])
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
            reasons.append(f"{name} is invalid")
            return fallback, "fallback"
        value = value.strip()
        if not _field_has_supported_facts(value, refs, by_key):
            reasons.append(f"{name} contains unsupported facts")
            return fallback, "fallback"
        return value, "validated"

    title_raw = raw.get("title")
    if not isinstance(title_raw, str) or not 4 <= len(title_raw.strip()) <= 80:
        reasons.append("title is invalid")
        title = _fallback_title(claim_rows, fallback_title)
        title_status = "fallback"
    else:
        title, title_status = title_raw.strip(), "validated"
    slug_raw = raw.get("slug")
    if not isinstance(slug_raw, str) or not _SLUG_RE.fullmatch(slug_raw.strip()):
        reasons.append("slug is invalid")
        slug, slug_status = _slug_for(title, stable_topic_id), "fallback"
    else:
        slug, slug_status = slug_raw.strip(), "validated"
    category_raw = raw.get("category_id")
    allowed_categories = {item.category_id for item in publication.categories}
    if not isinstance(category_raw, str) or category_raw.strip() not in allowed_categories:
        reasons.append("category_id is not declared")
        category_id, category_status = (
            fallback_category_id if fallback_category_id in allowed_categories else publication.pending_category.category_id,
            "fallback",
        )
    else:
        category_id, category_status = category_raw.strip(), "validated"
    summary, summary_status = text_field("summary", 420, "来源未提供摘要；请阅读 Evidence。")
    why, why_status = text_field("why", 280, "来源未说明")
    version, version_status = text_field("version", 120, "未提供版本信息")
    related_raw = raw.get("related_topics")
    related = [str(item).strip() for item in related_raw] if isinstance(related_raw, list) and all(isinstance(item, str) for item in related_raw) else []
    if len(related) > 8:
        related = related[:8]
        reasons.append("related_topics exceeded maxItems")
    universe = topic_universe or set()
    valid_related = tuple(item for item in related if not universe or item in universe)
    if len(valid_related) != len(related):
        reasons.append("unknown related topic was discarded")
    statuses = {"title": title_status, "category_id": category_status, "summary": summary_status, "why": why_status, "version": version_status}
    return PublicationMetadata(
        title=title,
        slug=slug,
        category_id=category_id,
        summary=summary,
        why=why,
        version=version,
        related_topics=valid_related,
        claim_refs=tuple(claim_refs),
        field_refs=field_refs,
        field_status=statuses,
        needs_review=bool(reasons),
        fallback_reasons=tuple(dict.fromkeys(reasons)),
    )
