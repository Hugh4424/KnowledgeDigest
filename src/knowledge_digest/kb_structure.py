"""Dependency-free parser and write gate for ``kb.structure.md``."""

from __future__ import annotations

import os
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

from .errors import ValidationError


DEFAULT_ROOTS = ("pages", "_archive", "_queues")
DEFAULT_PUBLICATION_HOME = "Home.md"
DEFAULT_PUBLICATION_INDEX_ROOT = "indexes"
DEFAULT_PUBLICATION_SOURCE_INDEX = "indexes/sources.md"
DEFAULT_PENDING_CATEGORY_ID = "pending"
DEFAULT_PENDING_CATEGORY_TITLE = "待归类"
DEFAULT_PENDING_TOPIC_DIR = "pages/待归类"
DEFAULT_TAXONOMY_VERSION = "1.0.0"
DEFAULT_TAXONOMY_OWNER = "KnowledgeDigest maintainers"
DEFAULT_TAXONOMY_CHANGE_POLICY = "SemVer; maintainers edit kb.structure.md"
SOURCE_INDEX_SCHEMA_VERSION = "1.0.0"
TOPIC_INDEX_SCHEMA_VERSION = "2.0.0"
LEGACY_TOPIC_INDEX_SCHEMA_VERSION = "1.0.0"
DEFAULT_PARENT_IDS = frozenset({"products", "engineering", "customers", "operations", "principles", "other"})
DEFAULT_PARENT_TITLES = {
    "products": "产品",
    "engineering": "研发",
    "customers": "客户",
    "operations": "运营",
    "principles": "原则",
    "other": "其他",
}


@dataclass(frozen=True)
class PublicationCategory:
    """One reader-visible category declared by the knowledge-base owner."""

    category_id: str
    title: str
    topic_dir: str
    parent_id: str | None = None
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class PublicationContract:
    """The small, explicit range in which KnowledgeDigest may publish readers pages."""

    home_path: str
    index_root: str
    categories: tuple[PublicationCategory, ...]
    taxonomy_version: str = DEFAULT_TAXONOMY_VERSION
    taxonomy_owner: str = DEFAULT_TAXONOMY_OWNER
    taxonomy_change_policy: str = DEFAULT_TAXONOMY_CHANGE_POLICY
    source_index_path: str = DEFAULT_PUBLICATION_SOURCE_INDEX

    @property
    def parent_ids(self) -> tuple[str, ...]:
        return tuple(sorted({category.parent_id for category in self.categories if category.parent_id}))

    @property
    def parent_titles(self) -> dict[str, str]:
        return {
            parent_id: DEFAULT_PARENT_TITLES.get(parent_id, parent_id.replace("-", " ").title())
            for parent_id in self.parent_ids
        }

    def category(self, category_id: str) -> PublicationCategory:
        for category in self.categories:
            if category.category_id == category_id:
                return category
        raise ValidationError("publication", category_id, "category is not declared")

    @property
    def pending_category(self) -> PublicationCategory:
        return next(category for category in self.categories if category.category_id == DEFAULT_PENDING_CATEGORY_ID)

    def category_index_path(self, category_id: str) -> str:
        if category_id not in {category.category_id for category in self.categories}:
            raise ValidationError("publication", category_id, "category is not declared")
        return f"{self.index_root}/{category_id}.md"


@dataclass(frozen=True)
class StructureContract:
    """The small structure contract needed before a formal write."""

    roots: tuple[str, ...]
    why_field: str | None
    version_field: str | None
    missing_fields: tuple[str, ...]
    suggestions: tuple[str, ...]
    publication: PublicationContract | None
    publication_errors: tuple[str, ...]
    allow_official_write: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "roots": list(self.roots),
            "why_field": self.why_field,
            "version_field": self.version_field,
            "missing_fields": list(self.missing_fields),
            "suggestions": list(self.suggestions),
            "publication": (
                {
                    "home_path": self.publication.home_path,
                    "index_root": self.publication.index_root,
                    "categories": [
                        {
                            "id": category.category_id,
                            "title": category.title,
                            "topic_dir": category.topic_dir,
                            "parent_id": category.parent_id,
                            "aliases": list(category.aliases),
                        }
                        for category in self.publication.categories
                    ],
                }
                if self.publication is not None
                else None
            ),
            "taxonomy_version": self.publication.taxonomy_version if self.publication else None,
            "taxonomy_owner": self.publication.taxonomy_owner if self.publication else None,
            "taxonomy_change_policy": self.publication.taxonomy_change_policy if self.publication else None,
            "publication_source_index": self.publication.source_index_path if self.publication else None,
            "publication_errors": list(self.publication_errors),
            "allow_official_write": self.allow_official_write,
        }


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def _frontmatter_lines(text: str) -> list[str] | None:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() in {"---", "..."}:
            return lines[1:index]
    return None


def _frontmatter_values(text: str) -> dict[str, str]:
    lines = _frontmatter_lines(text)
    if lines is None:
        return {}
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        values[key.strip()] = _unquote(value)
    return values


def _safe_relative_path(value: str, *, field: str, directory: bool) -> str:
    candidate = _unquote(value)
    path = Path(candidate)
    if (
        not candidate
        or path.is_absolute()
        or "\\" in candidate
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValidationError("publication", field, "must be a safe relative path")
    if directory and path.suffix:
        raise ValidationError("publication", field, "must name a directory, not a file")
    if not directory and path.suffix.lower() != ".md":
        raise ValidationError("publication", field, "must name a Markdown file")
    return path.as_posix()


def _is_same_or_parent(left: str, right: str) -> bool:
    left_parts = Path(left).parts
    right_parts = Path(right).parts
    return len(left_parts) <= len(right_parts) and left_parts == right_parts[: len(left_parts)]


def _publication_category_rows(frontmatter: list[str] | None) -> list[dict[str, Any]]:
    if frontmatter is None:
        return []
    start = next(
        (index for index, line in enumerate(frontmatter) if line.strip() == "publication_categories:"),
        None,
    )
    if start is None:
        return []
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in frontmatter[start + 1 :]:
        if line and not line[0].isspace():
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current is not None:
                rows.append(current)
            current = {}
            stripped = stripped[2:].strip()
        elif current is None:
            raise ValidationError("publication", "publication_categories", "must contain a YAML list")
        if ":" not in stripped:
            raise ValidationError("publication", "publication_categories", "contains an invalid category entry")
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = _unquote(value)
        if key not in {"id", "title", "topic_dir", "parent_id", "aliases"}:
            raise ValidationError("publication", key, "is not a supported publication category field")
        if key in current and key != "aliases":
            raise ValidationError("publication", key, "is repeated in one publication category")
        if key == "aliases":
            current.setdefault(key, []).append(value)
        else:
            current[key] = value
    if current is not None:
        rows.append(current)
    return rows


def _publication_contract(
    text: str,
    *,
    require_taxonomy: bool = False,
) -> tuple[PublicationContract | None, tuple[str, ...]]:
    """Parse publication fields without guessing a legacy knowledge-base layout."""
    frontmatter = _frontmatter_lines(text)
    values = _frontmatter_values(text)
    errors: list[str] = []
    taxonomy_version = values.get("taxonomy_version")
    taxonomy_owner = values.get("taxonomy_owner")
    taxonomy_change_policy = values.get("taxonomy_change_policy")
    raw_source_index = values.get("publication_source_index", DEFAULT_PUBLICATION_SOURCE_INDEX)
    if require_taxonomy and not taxonomy_version:
        errors.append("taxonomy_version is missing")
    if require_taxonomy and not taxonomy_owner:
        errors.append("taxonomy_owner is missing")
    if require_taxonomy and not taxonomy_change_policy:
        errors.append("taxonomy_change_policy is missing")
    raw_home = values.get("publication_home")
    raw_index_root = values.get("publication_index_root")
    if not raw_home:
        errors.append("publication_home is missing")
    if not raw_index_root:
        errors.append("publication_index_root is missing")
    try:
        rows = _publication_category_rows(frontmatter)
    except ValidationError as error:
        rows = []
        errors.append(error.reason)
    if not rows and not any(error.startswith("publication_categories") for error in errors):
        errors.append("publication_categories is missing or empty")
    if errors:
        return None, tuple(errors)

    try:
        home_path = _safe_relative_path(str(raw_home), field="publication_home", directory=False)
        index_root = _safe_relative_path(
            str(raw_index_root), field="publication_index_root", directory=True
        )
        source_index_path = _safe_relative_path(
            str(raw_source_index), field="publication_source_index", directory=False
        )
        if source_index_path == "_digest/source-index.md":
            source_index_path = DEFAULT_PUBLICATION_SOURCE_INDEX
        categories: list[PublicationCategory] = []
        category_ids: set[str] = set()
        for row in rows:
            missing = sorted({"id", "title", "topic_dir"} - set(row))
            if missing:
                raise ValidationError(
                    "publication",
                    "publication_categories",
                    f"category is missing field(s): {', '.join(missing)}",
                )
            category_id = row["id"].strip()
            title = row["title"].strip()
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", category_id):
                raise ValidationError(
                    "publication",
                    "publication_categories.id",
                    "category id must contain only letters, numbers, underscores, or hyphens",
                )
            if not title:
                raise ValidationError("publication", "publication_categories", "category title must be non-empty")
            if category_id in category_ids:
                raise ValidationError("publication", category_id, "category id is duplicated")
            category_ids.add(category_id)
            parent_id = str(row.get("parent_id", "")).strip() or None
            if parent_id == category_id:
                raise ValidationError("publication", category_id, "category cannot parent itself")
            aliases = tuple(dict.fromkeys(
                alias.strip() for alias in row.get("aliases", []) if isinstance(alias, str) and alias.strip()
            ))
            categories.append(
                PublicationCategory(
                    category_id=category_id,
                    title=title,
                    topic_dir=_safe_relative_path(
                        row["topic_dir"], field=f"publication_categories.{category_id}.topic_dir", directory=True
                    ),
                    parent_id=parent_id,
                    aliases=aliases,
                )
            )
        pending = [category for category in categories if category.category_id == DEFAULT_PENDING_CATEGORY_ID]
        if len(pending) != 1:
            raise ValidationError("publication", "publication_categories", "must declare exactly one pending category")
        if pending[0].title != DEFAULT_PENDING_CATEGORY_TITLE:
            raise ValidationError(
                "publication",
                "publication_categories.pending.title",
                "must be 待归类",
            )
        parent_ids = {category.parent_id for category in categories if category.parent_id}
        category_id_set = {category.category_id for category in categories}
        if require_taxonomy and any(category.parent_id is None for category in categories):
            raise ValidationError("publication", "publication_categories.parent_id", "every leaf category must declare a parent_id")
        if require_taxonomy:
            invalid_parents = sorted(parent_id for parent_id in parent_ids if parent_id not in DEFAULT_PARENT_IDS)
            if invalid_parents:
                raise ValidationError("publication", "publication_categories.parent_id", f"unknown parent id(s): {', '.join(invalid_parents)}")
            if pending[0].parent_id != "other":
                raise ValidationError("publication", "publication_categories.pending.parent_id", "pending must belong to other")
        if any(category.category_id in parent_ids for category in categories):
            raise ValidationError("publication", "publication_categories", "parent IDs must be logical nodes, not leaf category IDs")
        if require_taxonomy and (not taxonomy_version or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", taxonomy_version)):
            raise ValidationError("publication", "taxonomy_version", "must be SemVer")
        if require_taxonomy and (not taxonomy_owner or not taxonomy_change_policy):
            raise ValidationError("publication", "taxonomy", "owner and change policy must be non-empty")
        locations = [index_root, *(category.topic_dir for category in categories)]
        if any(_is_same_or_parent(home_path, location) or _is_same_or_parent(location, home_path) for location in locations):
            raise ValidationError("publication", "publication_home", "must not overlap an index or topic directory")
        if any(
            _is_same_or_parent(topic_dir, source_index_path)
            or _is_same_or_parent(source_index_path, topic_dir)
            for topic_dir in (category.topic_dir for category in categories)
        ):
            raise ValidationError("publication", "publication_source_index", "must not overlap a topic directory")
        for index, first in enumerate(locations):
            for second in locations[index + 1 :]:
                if _is_same_or_parent(first, second) or _is_same_or_parent(second, first):
                    raise ValidationError("publication", first, "publication directories must not overlap")
    except ValidationError as error:
        return None, (error.reason,)
    return PublicationContract(
        home_path,
        index_root,
        tuple(categories),
        taxonomy_version=str(taxonomy_version or DEFAULT_TAXONOMY_VERSION),
        taxonomy_owner=str(taxonomy_owner or DEFAULT_TAXONOMY_OWNER),
        taxonomy_change_policy=str(taxonomy_change_policy or DEFAULT_TAXONOMY_CHANGE_POLICY),
        source_index_path=source_index_path,
    ), ()


DEFAULT_PUBLICATION_CATEGORIES: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    ("product-overview", "产品概览", "pages/products/product-overview", "products", ("overview",)),
    ("product-capability", "产品能力", "pages/products/product-capability", "products", ("features",)),
    ("product-operations", "产品运营", "pages/products/product-operations", "products", ("usage",)),
    ("product-boundary", "产品边界", "pages/products/product-boundary", "products", ("limits",)),
    ("architecture", "架构设计", "pages/engineering/architecture", "engineering", ()),
    ("implementation", "实现细节", "pages/engineering/implementation", "engineering", ("code",)),
    ("operations-troubleshooting", "运维与排障", "pages/engineering/operations-troubleshooting", "engineering", ("troubleshooting",)),
    ("development-practice", "研发实践", "pages/engineering/development-practice", "engineering", ("process",)),
    ("customer-overview", "客户概览", "pages/customers/customer-overview", "customers", ()),
    ("customer-case", "客户案例", "pages/customers/customer-case", "customers", ("case",)),
    ("market-feedback", "市场反馈", "pages/customers/market-feedback", "customers", ("feedback",)),
    ("project", "项目", "pages/operations/project", "operations", ()),
    ("management", "管理", "pages/operations/management", "operations", ()),
    ("people", "人员与组织", "pages/operations/people", "operations", ("team",)),
    ("competitor", "竞品", "pages/operations/competitor", "operations", ("competition",)),
    ("event", "事件", "pages/operations/event", "operations", ("events",)),
    ("business-principle", "业务原则", "pages/principles/business-principle", "principles", ()),
    ("content-standard", "内容规范", "pages/principles/content-standard", "principles", ("content",)),
    ("delivery-standard", "交付规范", "pages/principles/delivery-standard", "principles", ("delivery",)),
    ("unclassified", "其他", "pages/other/unclassified", "other", ("other",)),
    (DEFAULT_PENDING_CATEGORY_ID, DEFAULT_PENDING_CATEGORY_TITLE, DEFAULT_PENDING_TOPIC_DIR, "other", ("needs-review",)),
)


def default_publication_structure() -> str:
    """Return the complete initial declaration for a new knowledge base."""
    lines = [
        "---",
        "roots: [pages, _archive, _queues]",
        "why_field: why",
        "version_field: version",
        f"taxonomy_version: {DEFAULT_TAXONOMY_VERSION}",
        f"taxonomy_owner: {DEFAULT_TAXONOMY_OWNER}",
        f"taxonomy_change_policy: {DEFAULT_TAXONOMY_CHANGE_POLICY}",
        f"publication_home: {DEFAULT_PUBLICATION_HOME}",
        f"publication_index_root: {DEFAULT_PUBLICATION_INDEX_ROOT}",
        f"publication_source_index: {DEFAULT_PUBLICATION_SOURCE_INDEX}",
        "publication_categories:",
    ]
    for category_id, title, topic_dir, parent_id, aliases in DEFAULT_PUBLICATION_CATEGORIES:
        lines.extend([f"  - id: {category_id}", f"    title: {title}", f"    topic_dir: {topic_dir}", f"    parent_id: {parent_id}"])
        lines.extend(f"    aliases: {alias}" for alias in aliases)
    lines.extend(["---", "", "# KnowledgeDigest structure", ""])
    return "\n".join(lines)


def _write_initial_document(path: Path, content: str) -> Path:
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def initialize_default_publication(kb_dir: Path) -> PublicationContract:
    """Create the owned first-run reader files after the caller holds the KB lock.

    This function never upgrades a non-empty directory.  Callers must recheck
    that boundary under the lock before invoking it.
    """
    structure = default_publication_structure()
    contract, errors = _publication_contract(structure)
    if contract is None:
        raise AssertionError(f"built-in publication contract is invalid: {errors!r}")
    documents = {
        kb_dir / "kb.structure.md": structure,
        kb_dir / contract.home_path: "---\nmanaged_by: KnowledgeDigest\ndigest_kind: home\n---\n\n# Knowledge Digest\n",
    }
    existing = [path for path in documents if path.exists() or path.is_symlink()]
    if existing:
        raise ValidationError("publication", existing[0], "new knowledge base already contains a publication file")

    created_directories: list[Path] = []
    for directory in sorted(
        {path.parent for path in documents},
        key=lambda value: (len(value.parts), value.as_posix()),
    ):
        if directory.exists():
            if directory.is_symlink() or not directory.is_dir():
                raise ValidationError("publication", directory, "initial publication directory must be a regular directory")
            continue
        missing: list[Path] = []
        cursor = directory
        while not cursor.exists():
            missing.append(cursor)
            cursor = cursor.parent
        if cursor.is_symlink() or not cursor.is_dir():
            raise ValidationError("publication", cursor, "initial publication parent must be a regular directory")
        for missing_directory in reversed(missing):
            missing_directory.mkdir(exist_ok=False)
            created_directories.append(missing_directory)

    temporary_documents: list[tuple[Path, Path, str]] = []
    written: list[tuple[Path, str]] = []
    try:
        for target, content in documents.items():
            temporary_documents.append((target, _write_initial_document(target, content), content))
        for target, temporary, content in temporary_documents:
            os.replace(temporary, target)
            _fsync_directory(target.parent)
            written.append((target, content))
    except (OSError, ValidationError) as error:
        for _target, temporary, _content in temporary_documents:
            temporary.unlink(missing_ok=True)
        for target, content in reversed(written):
            try:
                if target.is_file() and target.read_text(encoding="utf-8") == content:
                    target.unlink()
                    _fsync_directory(target.parent)
            except OSError:
                pass
        for directory in sorted(created_directories, key=lambda value: len(value.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise ValidationError("publication", kb_dir, f"new knowledge-base initialization failed ({error})") from error
    return contract


def parse_roots(structure_path: Path) -> tuple[str, ...]:
    """Read roots from YAML-like frontmatter, with safe layout defaults."""
    frontmatter = _frontmatter_lines(structure_path.read_text(encoding="utf-8"))
    if frontmatter is None:
        return DEFAULT_ROOTS

    roots: list[str] = []
    named_roots: dict[str, str] = {}
    for index, line in enumerate(frontmatter):
        stripped = line.strip()
        for key in ("page_root", "archive_root", "queue_root"):
            if stripped.startswith(f"{key}:"):
                candidate = _unquote(stripped.partition(":")[2])
                if candidate:
                    named_roots[key] = candidate
        if not stripped.startswith("roots:"):
            continue
        inline = stripped.partition(":")[2].strip()
        if inline.startswith("[") and inline.endswith("]"):
            roots = [_unquote(item) for item in inline[1:-1].split(",") if _unquote(item)]
            break
        if inline:
            candidate = _unquote(inline)
            roots = [candidate] if candidate else []
            break
        for child in frontmatter[index + 1 :]:
            if child and not child[0].isspace():
                break
            item = child.strip()
            if item.startswith("- "):
                candidate = _unquote(item[2:])
                if candidate:
                    roots.append(candidate)
            elif item:
                break
        break
    if roots:
        return tuple(roots)
    if named_roots:
        return (
            named_roots.get("page_root", DEFAULT_ROOTS[0]),
            named_roots.get("archive_root", DEFAULT_ROOTS[1]),
            named_roots.get("queue_root", DEFAULT_ROOTS[2]),
        )
    return DEFAULT_ROOTS


def inspect_structure(structure_path: Path, *, require_taxonomy: bool = False) -> StructureContract:
    """Read the roots and required Why/version declarations used by the write gate."""
    text = structure_path.read_text(encoding="utf-8")
    values = _frontmatter_values(text)
    why_field = values.get("why_field") or None
    version_field = values.get("version_field") or None
    missing: list[str] = []
    suggestions: list[str] = []
    if not why_field:
        missing.append("Why")
        suggestions.append("在 kb.structure.md frontmatter 增加非空 why_field，例如 why_field: why")
    if not version_field:
        missing.append("version history")
        suggestions.append(
            "在 kb.structure.md frontmatter 增加非空 version_field，例如 version_field: version"
        )
    publication, publication_errors = _publication_contract(text, require_taxonomy=require_taxonomy)
    roots = parse_roots(structure_path)
    return StructureContract(
        roots=roots,
        why_field=why_field,
        version_field=version_field,
        missing_fields=tuple(missing),
        suggestions=tuple(suggestions),
        publication=publication,
        publication_errors=publication_errors,
        allow_official_write=not missing and not publication_errors,
    )


def validate_structure(structure_path: Path) -> dict[str, Any]:
    """Return a JSON-ready structure check without raising on missing fields."""
    return inspect_structure(structure_path).as_dict()


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("publication", field, "must be a non-empty string")
    return value.strip()


def _require_safe_target(value: Any, field: str) -> str:
    return _safe_relative_path(_require_string(value, field), field=field, directory=False)


def _validate_topic_evidence(value: Any, field: str, *, allow_legacy: bool = False) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValidationError("publication", field, "must be a non-empty evidence list")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValidationError("publication", f"{field}[{index}]", "must be an object")
        if allow_legacy and item.get("legacy_digest_topic_id"):
            normalized.append(dict(item))
            continue
        source_uri = item.get("source_uri")
        fingerprint = item.get("content_fingerprint")
        line_number = item.get("line_number")
        if not isinstance(source_uri, str) or not source_uri.strip():
            raise ValidationError("publication", f"{field}[{index}].source_uri", "must be non-empty")
        if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            raise ValidationError("publication", f"{field}[{index}].content_fingerprint", "must be SHA-256")
        if not isinstance(line_number, int) or line_number < 1:
            raise ValidationError("publication", f"{field}[{index}].line_number", "must be a positive integer")
        normalized.append({**item, "source_uri": source_uri.strip(), "content_fingerprint": fingerprint, "line_number": line_number})
    return normalized


def migrate_topic_index(value: Any) -> dict[str, Any]:
    """Normalize legacy 1.0.0 rows without recalculating identity or paths."""
    if not isinstance(value, dict):
        raise ValidationError("publication", "topic-index", "must be an object")
    version = value.get("schema_version")
    if version == LEGACY_TOPIC_INDEX_SCHEMA_VERSION:
        topics = value.get("topics")
        if not isinstance(topics, list):
            raise ValidationError("publication", "topic-index.topics", "must be a list")
        migrated: list[dict[str, Any]] = []
        for index, topic in enumerate(topics):
            if not isinstance(topic, dict):
                raise ValidationError("publication", f"topic-index.topics[{index}]", "must be an object")
            required = {"topic_id", "source_ids", "category_id", "published_path", "product_slug"}
            if not required.issubset(topic):
                raise ValidationError("publication", f"topic-index.topics[{index}]", "has unknown or missing fields")
            old_id = _require_string(topic["topic_id"], "topic-index.topic_id")
            source_ids = topic["source_ids"]
            if not isinstance(source_ids, list) or not source_ids or any(not isinstance(item, str) or not item for item in source_ids):
                raise ValidationError("publication", old_id, "source_ids must be a non-empty string list")
            published_path = topic["published_path"]
            if published_path is not None:
                published_path = _require_safe_target(published_path, "topic-index.published_path")
            product_slug = topic["product_slug"]
            if product_slug is not None:
                product_slug = _require_string(product_slug, "topic-index.product_slug")
            migrated.append(
                {
                    "topic_key": f"legacy/{old_id}",
                    "knowledge_type": "unknown",
                    # Legacy rows did not carry semantic axes.  Keep the old
                    # path available to Task2's page-layout code, but mark the
                    # semantic projection degraded so it cannot enter the new
                    # formal navigation axis.
                    "product": None,
                    "module": None,
                    "object_intent": None,
                    "source_members": list(source_ids),
                    "published_path": None,
                    "legacy_published_path": published_path,
                    "old_path_mapping": (
                        [{"old_path": published_path, "relation": "unmappable", "evidence_refs": [{"legacy_digest_topic_id": old_id}]}]
                        if published_path
                        else []
                    ),
                    "status": "degraded",
                    "legacy_compat": True,
                    "topic_plan_version": "legacy-1.0.0",
                    "reason": "migrated from legacy TopicIndex",
                    "evidence_refs": [{"legacy_digest_topic_id": old_id}],
                    "digest_topic_id": old_id,
                    # Compatibility aliases are intentionally retained for the
                    # existing page-layout and incremental update code.
                    "topic_id": old_id,
                    "source_ids": list(source_ids),
                    "category_id": topic["category_id"],
                    "product_slug": product_slug,
                }
            )
        return {"schema_version": TOPIC_INDEX_SCHEMA_VERSION, "topics": migrated, "migration": {"from": version, "preserved": True}}
    if version != TOPIC_INDEX_SCHEMA_VERSION:
        raise ValidationError("publication", "topic-index.schema_version", "unsupported schema version")
    return value


def validate_topic_index(value: Any) -> dict[str, Any]:
    """Validate the current TopicIndex and migrate the legacy 1.0.0 shape."""
    normalized = migrate_topic_index(value)
    topics = normalized.get("topics")
    if not isinstance(topics, list):
        raise ValidationError("publication", "topic-index.topics", "must be a list")
    seen_topics: set[str] = set()
    seen_sources: set[str] = set()
    seen_paths: set[str] = set()
    validated: list[dict[str, Any]] = []
    required = {
        "topic_key", "knowledge_type", "product", "module", "object_intent", "source_members", "published_path",
        "old_path_mapping", "status", "topic_plan_version", "reason", "evidence_refs",
    }
    for index, topic in enumerate(topics):
        if not isinstance(topic, dict):
            raise ValidationError("publication", f"topic-index.topics[{index}]", "must be an object")
        missing = required - set(topic)
        if missing:
            raise ValidationError("publication", f"topic-index.topics[{index}]", f"missing fields: {', '.join(sorted(missing))}")
        topic_key = _require_string(topic["topic_key"], "topic-index.topic_key")
        _require_string(topic["knowledge_type"], "topic-index.knowledge_type")
        if topic_key in seen_topics:
            raise ValidationError("publication", topic_key, "topic key is duplicated")
        seen_topics.add(topic_key)
        status = topic["status"]
        if status not in {"published", "degraded"}:
            raise ValidationError("publication", topic_key, "unsupported topic status")
        members = topic["source_members"]
        if not isinstance(members, list) or not members or any(not isinstance(item, str) or not item for item in members):
            raise ValidationError("publication", topic_key, "source_members must be a non-empty string list")
        if len(set(members)) != len(members) or seen_sources.intersection(members):
            raise ValidationError("publication", topic_key, "source membership is duplicated")
        seen_sources.update(members)
        axis_fields = ("product", "module", "object_intent")
        if status == "published" and any(not isinstance(topic[field], str) or not topic[field].strip() for field in axis_fields):
            raise ValidationError("publication", topic_key, "published axis fields must be non-empty")
        if status == "degraded" and any(topic[field] is not None for field in axis_fields):
            raise ValidationError("publication", topic_key, "degraded axis fields must be JSON null")
        path = topic["published_path"]
        if status == "published":
            path = _require_safe_target(path, "topic-index.published_path")
            if path in seen_paths:
                raise ValidationError("publication", path, "published path is duplicated")
            seen_paths.add(path)
        elif path is not None:
            raise ValidationError("publication", topic_key, "degraded published_path must be JSON null")
        mappings = topic["old_path_mapping"]
        if not isinstance(mappings, list):
            raise ValidationError("publication", topic_key, "old_path_mapping must be a list")
        normalized_mappings: list[dict[str, Any]] = []
        for mapping in mappings:
            if not isinstance(mapping, dict) or set(mapping) != {"old_path", "relation", "evidence_refs"}:
                raise ValidationError("publication", topic_key, "old_path_mapping has invalid fields")
            old_path = _require_safe_target(mapping["old_path"], "topic-index.old_path_mapping.old_path")
            if mapping["relation"] not in {"rename", "merge", "split", "unmappable"}:
                raise ValidationError("publication", topic_key, "old_path_mapping relation is unsupported")
            mapping_evidence = _validate_topic_evidence(
                mapping["evidence_refs"],
                f"topic-index.topics[{index}].old_path_mapping.evidence_refs",
                allow_legacy=bool(topic.get("legacy_compat")),
            )
            normalized_mappings.append({"old_path": old_path, "relation": mapping["relation"], "evidence_refs": mapping_evidence})
        evidence_refs = topic["evidence_refs"]
        evidence_refs = _validate_topic_evidence(evidence_refs, f"topic-index.topics[{index}].evidence_refs", allow_legacy=bool(topic.get("legacy_compat")))
        row = dict(topic)
        row["topic_key"] = topic_key
        row["source_members"] = sorted(members)
        row["published_path"] = path
        row["old_path_mapping"] = sorted(normalized_mappings, key=lambda item: (item["old_path"], item["relation"]))
        row["evidence_refs"] = sorted(evidence_refs, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True)) if isinstance(evidence_refs, list) else evidence_refs
        # Keep old consumers working when they read a current index.
        row.setdefault("topic_id", row.get("digest_topic_id") or topic_key)
        row.setdefault("source_ids", list(row["source_members"]))
        row.setdefault("category_id", None)
        row.setdefault("product_slug", row.get("product"))
        validated.append(row)
    return {**normalized, "schema_version": TOPIC_INDEX_SCHEMA_VERSION, "topics": sorted(validated, key=lambda row: row["topic_key"])}


def validate_source_index(value: Any) -> dict[str, Any]:
    """Validate the internal representation of the fixed Markdown source index."""
    if not isinstance(value, dict):
        raise ValidationError("publication", "source-index", "must be an object")
    if value.get("schema_version") != SOURCE_INDEX_SCHEMA_VERSION:
        raise ValidationError("publication", "source-index.schema_version", "unsupported schema version")
    entries = value.get("entries")
    if not isinstance(entries, list):
        raise ValidationError("publication", "source-index.entries", "must be a list")
    seen_uris: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValidationError("publication", f"source-index.entries[{index}]", "must be an object")
        required = {"source_uri", "content_fingerprint", "status", "target_paths"}
        if set(entry) != required:
            raise ValidationError("publication", f"source-index.entries[{index}]", "has unknown or missing fields")
        source_uri = _require_string(entry["source_uri"], "source-index.source_uri")
        if source_uri in seen_uris:
            raise ValidationError("publication", source_uri, "source URI is duplicated")
        seen_uris.add(source_uri)
        fingerprint = _require_string(entry["content_fingerprint"], "source-index.content_fingerprint")
        if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            raise ValidationError("publication", source_uri, "content fingerprint must be SHA-256")
        status = _require_string(entry["status"], "source-index.status")
        if status not in {"published", "needs-review", "pending", "duplicate"}:
            raise ValidationError("publication", status, "unsupported source status")
        paths = entry["target_paths"]
        if not isinstance(paths, list) or any(not isinstance(path, str) for path in paths):
            raise ValidationError("publication", source_uri, "target_paths must be a string list")
        normalized.append(
            {
                "source_uri": source_uri,
                "content_fingerprint": fingerprint,
                "status": status,
                "target_paths": [_require_safe_target(path, "source-index.target_paths") for path in paths],
            }
        )
    return {"schema_version": SOURCE_INDEX_SCHEMA_VERSION, "entries": normalized}


def _escape_table_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def _split_table_row(line: str) -> list[str]:
    if not line.strip().startswith("|") or not line.rstrip().endswith("|"):
        raise ValidationError("publication", "source-index", "row must be a Markdown table row")
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in line.strip()[1:-1]:
        if char == "|" and not escaped:
            cells.append("".join(current).strip())
            current = []
            continue
        if char == "\\" and not escaped:
            escaped = True
            current.append(char)
            continue
        current.append(char)
        escaped = False
    cells.append("".join(current).strip())
    return [cell.replace("\\|", "|").replace("\\\\", "\\") for cell in cells]


def serialize_source_index(value: dict[str, Any], *, source_index_path: str = DEFAULT_PUBLICATION_SOURCE_INDEX) -> str:
    """Serialize source-index as the one canonical, reader-visible Markdown form."""
    normalized = validate_source_index(value)
    index_parent = Path(source_index_path).parent
    lines = [
        "---",
        "managed_by: KnowledgeDigest",
        "digest_kind: source-index",
        f"schema_version: {normalized['schema_version']}",
        "---",
        "",
        "# 来源索引",
        "",
        "| source_uri | content_fingerprint | status | target_paths |",
        "| --- | --- | --- | --- |",
    ]
    for entry in normalized["entries"]:
        target_links = []
        for path in entry["target_paths"]:
            relative = Path(os.path.relpath(path, start=index_parent)).as_posix()
            target_links.append(f"[{_escape_table_cell(path)}]({quote(relative, safe='/._-')})")
        lines.append(
            "| "
            + " | ".join(
                (
                    _escape_table_cell(entry["source_uri"]),
                    entry["content_fingerprint"],
                    entry["status"],
                    _escape_table_cell(", ".join(target_links)),
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def parse_source_index_markdown(
    text: str,
    *,
    source_index_path: str = DEFAULT_PUBLICATION_SOURCE_INDEX,
) -> dict[str, Any]:
    """Parse and validate the fixed source-index Markdown representation."""
    if not isinstance(text, str):
        raise ValidationError("publication", "source-index", "must be text")
    lines = text.splitlines()
    if "digest_kind: source-index" not in lines or not any(line.startswith("schema_version:") for line in lines):
        raise ValidationError("publication", "source-index", "managed header is missing")
    version = next(line.partition(":")[2].strip() for line in lines if line.startswith("schema_version:"))
    table_start = next((index for index, line in enumerate(lines) if line.startswith("| source_uri |")), None)
    if table_start is None or table_start + 1 >= len(lines):
        raise ValidationError("publication", "source-index", "fixed table header is missing")
    columns = _split_table_row(lines[table_start])
    expected = ["source_uri", "content_fingerprint", "status", "target_paths"]
    if columns != expected:
        raise ValidationError("publication", "source-index", "fixed columns are invalid")
    index_parent = Path(source_index_path).parent
    rows: list[dict[str, Any]] = []
    for line in lines[table_start + 2 :]:
        if not line.strip():
            continue
        cells = _split_table_row(line)
        if len(cells) != len(expected):
            raise ValidationError("publication", "source-index", "row column count is invalid")
        target_cell = cells[3]
        linked_targets = re.findall(r"\]\(([^)#]+)(?:#[^)]+)?\)", target_cell)
        if linked_targets:
            target_paths = [
                Path(os.path.normpath(os.path.join(index_parent, unquote(path)))).as_posix()
                for path in linked_targets
            ]
        else:
            # Read older projections whose target_paths were root-relative text.
            target_paths = [unquote(path.strip()) for path in target_cell.split(",") if path.strip()]
        rows.append(
            {
                "source_uri": cells[0],
                "content_fingerprint": cells[1],
                "status": cells[2],
                "target_paths": target_paths,
            }
        )
    return validate_source_index({"schema_version": version, "entries": rows})


# Clear aliases for callers that prefer the noun form.
parse_structure_contract = inspect_structure
structure_contract = inspect_structure
