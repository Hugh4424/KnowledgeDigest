"""Reader-facing publication records.

This module renders navigation only.  It does not classify claims, choose
identities, or write files; writeback consumes its records in the same publish
transaction as topic pages.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .kb_structure import PublicationContract, serialize_source_index
from .paths import DigestPaths


def _record(path: str, kind: str, content: str) -> dict[str, Any]:
    page = {
        "target_path": path,
        "rendered_content": content,
        "final_body": "",
        "claims": [],
        "layout_finalized": True,
        "digest_kind": kind,
        "publication_audit_scope": "none",
    }
    return {
        "draft_id": f"navigation-{kind}-{path.replace('/', '-')}",
        "action": "publish_navigation",
        "digest_kind": kind,
        "target_path": path,
        "rendered_content": content,
        "claims": [],
        "layout_finalized": True,
        "publication_audit_scope": "none",
        "target_paths": [path],
        "split_pages": [page],
    }


def build_topic_part_navigation(
    parts: list[dict[str, Any]],
    *,
    overview_path: str,
    related_key: str,
) -> list[dict[str, Any]]:
    """Project one topic's overview/part/prev-next navigation without writing."""
    ordered = sorted(
        (dict(part) for part in parts),
        key=lambda part: (int(part.get("part_index", 0)), str(part.get("target_path", ""))),
    )
    rows: list[dict[str, Any]] = []
    for index, part in enumerate(ordered):
        target_path = str(part.get("target_path", ""))
        rows.append(
            {
                "part_index": int(part.get("part_index", index + 1)),
                "target_path": target_path,
                "entry_path": target_path,
                "overview_path": overview_path,
                "related_key": related_key,
                "prev": ordered[index - 1].get("target_path") if index else None,
                "next": ordered[index + 1].get("target_path") if index + 1 < len(ordered) else None,
            }
        )
    return rows


def _validate_existing_navigation(paths: DigestPaths, publication: PublicationContract) -> None:
    targets = [publication.home_path]
    targets.extend(publication.category_index_path(category.category_id) for category in publication.categories)
    targets.extend(f"{publication.index_root}/{parent_id}.md" for parent_id in publication.parent_ids)
    targets.append("README.md")
    for target in targets:
        path = paths.kb_dir / target
        if path.is_symlink():
            raise ValidationError("publication", path, "existing navigation page must not be a symlink")
        if path.exists() and "managed_by: KnowledgeDigest" not in path.read_text(encoding="utf-8"):
            raise ValidationError("publication", path, "existing navigation page must declare managed_by: KnowledgeDigest")


def _topic_rows(
    layouts: list[dict[str, Any]],
    publication: PublicationContract,
    paths: DigestPaths | None = None,
) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {category.category_id: [] for category in publication.categories}
    if paths is not None:
        from .page_layout import declared_managed_topics

        for record in declared_managed_topics(paths, publication):
            rows[record["category_id"]].append(
                {
                    "topic_id": record["topic_id"],
                    "title": record["title"],
                    "target_path": record["target_path"],
                    "part_number": int(record["part_number"]),
                    "product_slug": None,
                    "related_topics": [],
                }
            )
    for layout in layouts:
        category_id = str(layout.get("publication_category_id") or publication.pending_category.category_id)
        if category_id not in rows:
            category_id = publication.pending_category.category_id
        topic_key = str(layout.get("topic_id", ""))
        rows[category_id] = [row for row in rows[category_id] if row["topic_id"] != topic_key]
        for page in layout.get("split_pages", []):
            rows[category_id].append(
                {
                    "topic_id": str(layout.get("topic_id", "")),
                    "title": str(layout.get("title") or layout.get("topic_id") or "未命名主题"),
                    "target_path": str(page.get("target_path", "")),
                    "part_number": int(page.get("page_index", 1)),
                    "product_slug": (layout.get("publication") or {}).get("product_slug")
                    if isinstance(layout.get("publication"), dict)
                    else None,
                    "related_topics": list(
                        layout.get("related_topics")
                        or ((layout.get("publication") or {}).get("related_topics", [])
                            if isinstance(layout.get("publication"), dict) else [])
                    ),
                }
            )
    for category_id in rows:
        rows[category_id].sort(key=lambda row: (row["title"].casefold(), row["part_number"], row["target_path"]))
    return rows


def _topic_link_lines(rows: list[dict[str, Any]], index_path: str, kb_dir: Path) -> list[str]:
    lines: list[str] = []
    for row in rows:
        relative = Path(
            os.path.relpath(kb_dir / row["target_path"], start=kb_dir / Path(index_path).parent)
        ).as_posix()
        suffix = "" if row["part_number"] == 1 else f"（第 {row['part_number']} 部分）"
        lines.append(f"- [{row['title']}{suffix}]({relative})")
    return lines


def _expanded_navigation(
    layouts: list[dict[str, Any]],
    paths: DigestPaths,
    publication: PublicationContract,
    *,
    topic_universe: set[str] | None,
    source_index: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    _validate_existing_navigation(paths, publication)
    rows = _topic_rows(layouts, publication, paths)
    records: list[dict[str, Any]] = []

    readme = "\n".join(
        [
            "---",
            "managed_by: KnowledgeDigest",
            "digest_kind: readme",
            "---",
            "",
            "# Knowledge Digest",
            "",
            "这是可阅读的知识发布目录。",
            "",
            "- 从 [Home.md](Home.md) 进入分类。",
            "- `indexes/` 是分类导航，`pages/` 是主题正文。",
            "- `_digest/` 保存来源索引和运行审计；归档目录不要手改。",
            "",
        ]
    )
    records.append(_record("README.md", "readme", readme))

    visible_categories = {
        category.category_id
        for category in publication.categories
        if rows.get(category.category_id)
    }
    visible_parents = {
        category.parent_id
        for category in publication.categories
        if category.category_id in visible_categories
    }
    home_lines = [
        "---",
        "managed_by: KnowledgeDigest",
        "digest_kind: home",
        "---",
        "",
        "# Knowledge Digest",
        "",
        "## 按领域浏览",
    ]
    for parent_id in publication.parent_ids:
        if parent_id not in visible_parents:
            continue
        parent_path = f"{publication.index_root}/{parent_id}.md"
        parent_title = publication.parent_titles[parent_id]
        home_lines.append(f"- [{parent_title}]({parent_path})")
    if publication.pending_category.category_id in visible_categories:
        home_lines.extend(["", "## 待复核", f"- [{publication.pending_category.title}]({publication.category_index_path(publication.pending_category.category_id)})", ""])
    else:
        home_lines.append("")
    records.append(_record(publication.home_path, "home", "\n".join(home_lines)))

    for parent_id in publication.parent_ids:
        if parent_id not in visible_parents:
            continue
        parent_path = f"{publication.index_root}/{parent_id}.md"
        lines = [
            "---",
            "managed_by: KnowledgeDigest",
            "digest_kind: parent-index",
            f"digest_parent_id: {parent_id}",
            "---",
            "",
            f"# {publication.parent_titles[parent_id]}",
            "",
            "## 子分类",
        ]
        children = [
            category
            for category in publication.categories
            if category.parent_id == parent_id and category.category_id in visible_categories
        ]
        if not children:
            continue
        for category in children:
            target = publication.category_index_path(category.category_id)
            relative = Path(
                os.path.relpath(paths.kb_dir / target, start=paths.kb_dir / Path(parent_path).parent)
            ).as_posix()
            lines.append(f"- [{category.title}]({relative})")
        records.append(_record(parent_path, "parent-index", "\n".join([*lines, ""])))

    known_topics = set(topic_universe or {row["topic_id"] for values in rows.values() for row in values})
    for category in publication.categories:
        if category.category_id not in visible_categories:
            continue
        target = publication.category_index_path(category.category_id)
        lines = [
            "---",
            "managed_by: KnowledgeDigest",
            "digest_kind: category",
            f"digest_category_id: {category.category_id}",
            "---",
            "",
            f"# {category.title}",
            "",
            "## 主题",
        ]
        category_rows = rows[category.category_id]
        grouped: dict[str | None, list[dict[str, Any]]] = {}
        for row in category_rows:
            grouped.setdefault(row.get("product_slug"), []).append(row)
        for product_slug, grouped_rows in sorted(grouped.items(), key=lambda pair: pair[0] or ""):
            if category.parent_id == "products" and product_slug:
                lines.extend(["", f"### {product_slug}"])
            for row in grouped_rows:
                related = next(
                    (row.get("related_topics", []) for _layout in layouts if _layout.get("topic_id") == row["topic_id"]),
                    row.get("related_topics", []),
                )
                valid_related = [value for value in related if value in known_topics]
                if valid_related:
                    lines.append(f"<!-- related: {', '.join(valid_related)} -->")
            lines.extend(_topic_link_lines(grouped_rows, target, paths.kb_dir))
        records.append(_record(target, "category", "\n".join([*lines, ""])))

    if source_index is not None:
        if not isinstance(source_index, dict):
            raise ValidationError("publication", "source-index", "source index must be an object")
        if source_index.get("entries"):
            records.append(
                _record(
                    publication.source_index_path,
                    "source-index",
                    serialize_source_index(source_index, source_index_path=publication.source_index_path),
                )
            )
    return records


def build_publication_navigation(
    layouts: list[dict[str, Any]],
    paths: DigestPaths,
    publication: PublicationContract,
    *,
    topic_universe: set[str] | None = None,
    source_index: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return records after read-only validation; never write publication files."""
    # Phase 4 will pass the complete topic/source universe when it wires the
    # extended records into one writeback batch.  Until then, the existing
    # pipeline uses the safe category/topic subset accepted by current S5.
    if any(category.parent_id for category in publication.categories) and (
        topic_universe is not None or source_index is not None
    ):
        return _expanded_navigation(
            layouts,
            paths,
            publication,
            topic_universe=topic_universe,
            source_index=source_index,
        )

    # A legacy flat contract remains readable, but still uses this one renderer
    # and the same staged record shape.  New default KBs always use hierarchy.
    _validate_existing_navigation(paths, publication)
    rows = _topic_rows(layouts, publication, paths)
    visible_categories = {category.category_id for category in publication.categories if rows.get(category.category_id)}
    home_lines = [
        "---", "managed_by: KnowledgeDigest", "digest_kind: home", "---", "",
        "# Knowledge Digest", "", "## 分类",
        *[
            f"- [{category.title}]({publication.category_index_path(category.category_id)})"
            for category in publication.categories
            if category.category_id in visible_categories
        ],
        "",
    ]
    records = [_record(publication.home_path, "home", "\n".join(home_lines))]
    for category in publication.categories:
        if category.category_id not in visible_categories:
            continue
        target = publication.category_index_path(category.category_id)
        lines = [
            "---", "managed_by: KnowledgeDigest", "digest_kind: category",
            f"digest_category_id: {category.category_id}", "---", "", f"# {category.title}", "", "## 主题",
        ]
        lines.extend(_topic_link_lines(rows[category.category_id], target, paths.kb_dir))
        records.append(_record(target, "category", "\n".join([*lines, ""])))
    if source_index is not None:
        if not isinstance(source_index, dict):
            raise ValidationError("publication", "source-index", "source index must be an object")
        if source_index.get("entries"):
            records.append(
                _record(
                    publication.source_index_path,
                    "source-index",
                    serialize_source_index(source_index, source_index_path=publication.source_index_path),
                )
            )
    return records
