"""Deterministic Task1 topic-axis planning.

This module is intentionally provider-free.  It builds the structural input
used by later publication stages, but it never writes reader pages.
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit

from .errors import ValidationError
from .identity import source_id
from .kb_structure import parse_roots
from .paths import DigestPaths


TOPIC_AXIS_SCHEMA_VERSION = "1.0.0"
TOPIC_PLAN_SCHEMA_VERSION = "1.0.0"
TOPIC_INDEX_SCHEMA_VERSION = "2.0.0"
MATCH_ORDER = ("canonical", "alias", "parent_path", "h1_title", "candidate")
KNOWLEDGE_TYPE_REGISTRY_SCHEMA_VERSION = "1.0.0"
DEFAULT_RESERVED = frozenset({"home", "index", "indexes", "_digest", "_archive", "_queues", "pending"})
_EXPLICIT_TOPIC_PAGE_TYPES = frozenset(
    {"product_overview", "module_or_capability", "procedure_or_rule"}
)
_INGESTIBLE = {".md", ".txt", ".json"}
_SOURCE_LINE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
_H1 = re.compile(r"^#\s+(.+?)\s*$")
_VERSION = re.compile(r"\b(?:v\d+(?:\.\d+){0,2}|version\s*\d+(?:\.\d+){0,2})\b", re.I)


def _normalize_knowledge_type(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("topic-axis", "knowledge_type", "must be a non-empty string")
    import unicodedata

    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).strip()).casefold()


def _knowledge_type(row: dict[str, Any]) -> str:
    """Read an explicit knowledge type from an already validated source row."""
    value = row.get("knowledge_type")
    if value is None:
        raise ValidationError("topic-axis", "source.knowledge_type", "must be explicit")
    return _normalize_knowledge_type(value)


def _knowledge_type_registry_defaults(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = dict(value or {})
    entries = value.get("entries", [])
    if not isinstance(entries, list):
        raise ValidationError("topic-axis", "KnowledgeTypeRegistry.entries", "must be a list")
    result = {
        "schema_version": str(value.get("schema_version") or KNOWLEDGE_TYPE_REGISTRY_SCHEMA_VERSION),
        "owner": str(value.get("owner") or ""),
        "entries": [],
    }
    for index, raw in enumerate(entries):
        if not isinstance(raw, dict):
            raise ValidationError("topic-axis", f"KnowledgeTypeRegistry.entries[{index}]", "must be an object")
        canonical = raw.get("canonical")
        if not isinstance(canonical, str) or not canonical.strip():
            raise ValidationError("topic-axis", f"KnowledgeTypeRegistry.entries[{index}].canonical", "must be non-empty")
        aliases = raw.get("aliases", [])
        source_refs = raw.get("source_refs", [])
        status = raw.get("status")
        if not isinstance(aliases, list) or any(not isinstance(item, str) for item in aliases):
            raise ValidationError("topic-axis", f"KnowledgeTypeRegistry.entries[{index}].aliases", "must be a string list")
        if not isinstance(source_refs, list) or any(not isinstance(item, (str, dict)) for item in source_refs):
            raise ValidationError("topic-axis", f"KnowledgeTypeRegistry.entries[{index}].source_refs", "must be a list")
        if status not in {"canonical", "candidate", "conflict", "unknown"}:
            raise ValidationError("topic-axis", f"KnowledgeTypeRegistry.entries[{index}].status", "has unsupported status")
        if status == "canonical" and (not str(raw.get("owner") or result["owner"]).strip() or not source_refs):
            raise ValidationError("topic-axis", f"KnowledgeTypeRegistry.entries[{index}]", "canonical entry needs owner and source_refs")
        result["entries"].append(
            {
                "canonical": _normalize_knowledge_type(canonical),
                "aliases": sorted({_normalize_knowledge_type(item) for item in aliases if item.strip()}),
                "owner": str(raw.get("owner") or result["owner"]),
                "source_refs": sorted(source_refs, key=_json),
                "status": status,
                "reason": str(raw.get("reason") or ""),
            }
        )
    result["entries"].sort(key=lambda item: item["canonical"])
    return result


def build_knowledge_type_registry(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the type registry only from explicit current source evidence."""
    grouped: dict[str, dict[str, Any]] = {}
    for row in inventory:
        if not isinstance(row, dict):
            raise ValidationError("topic-axis", "knowledge_type registry", "inventory rows must be objects")
        canonical = _knowledge_type(row)
        item = grouped.setdefault(canonical, {"aliases": set(), "source_refs": []})
        item["aliases"].add(canonical)
        refs = row.get("evidence_refs", [])
        if not isinstance(refs, list) or not refs:
            raise ValidationError("topic-axis", row.get("source_id") or canonical, "knowledge_type needs source_refs")
        item["source_refs"].extend(ref for ref in refs if isinstance(ref, dict))
    entries = []
    for canonical, item in sorted(grouped.items()):
        refs = sorted(item["source_refs"], key=_json)
        if not refs:
            raise ValidationError("topic-axis", canonical, "knowledge_type needs source_refs")
        entries.append(
            {
                "canonical": canonical,
                "aliases": sorted(item["aliases"]),
                "owner": "KnowledgeDigest source compiler",
                "source_refs": refs,
                "status": "canonical",
                "reason": "explicit source declaration; no external taxonomy is imported",
            }
        )
    return _knowledge_type_registry_defaults(
        {
            "schema_version": KNOWLEDGE_TYPE_REGISTRY_SCHEMA_VERSION,
            "owner": "KnowledgeDigest source compiler",
            "entries": entries,
        }
    )


def read_topic_axis_settings(structure_path: Path) -> dict[str, Any]:
    """Read the small opt-in declaration without changing the old structure parser."""
    if not structure_path.is_file():
        return {"enabled": False, "topic_root": None}
    values: dict[str, Any] = {}
    for line in structure_path.read_text(encoding="utf-8").splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        raw = raw.strip().strip("\"'")
        if key in {"topic_axis_enabled", "topic_axis_root", "topic_root", "topic_axis_override_manifest"}:
            values[key] = raw
    return {
        "enabled": str(values.get("topic_axis_enabled", "")).casefold() in {"true", "yes", "1"},
        "topic_root": values.get("topic_axis_root") or values.get("topic_root"),
        "override_manifest": values.get("topic_axis_override_manifest"),
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError("topic-axis", path, "source declaration file is missing")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValidationError("topic-axis", f"{path}:{line_number}", "source declaration is invalid JSON") from error
        if not isinstance(value, dict):
            raise ValidationError("topic-axis", f"{path}:{line_number}", "source declaration must be an object")
        value["_line_number"] = line_number
        rows.append(value)
    return rows


def _relative_content_path(value: Any, items_dir: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("topic-axis", "content_path", "source declaration needs content_path")
    candidate = Path(value.strip())
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(items_dir)
        except ValueError as error:
            raise ValidationError("topic-axis", value, "content_path is outside items") from error
    else:
        parts = candidate.parts
        if parts and parts[0] == "items":
            candidate = Path(*parts[1:])
    if not candidate.parts or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValidationError("topic-axis", value, "content_path must be a safe relative path")
    return candidate.as_posix()


def _slug(value: Any, *, reserved: Iterable[str] = DEFAULT_RESERVED) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    # NFKC is deliberately done without transliteration: an un-auditable
    # non-ASCII canonical term must degrade instead of being guessed.
    import unicodedata

    normalized = unicodedata.normalize("NFKC", normalized).casefold()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    normalized = re.sub(r"-+", "-", normalized)
    if not normalized:
        return None
    reserved_values = set(reserved)
    if normalized in reserved_values:
        normalized = f"x-{normalized}"
        if normalized in reserved_values:
            return None
    return normalized


def topic_key_v1(product: str, module: str, object_intent: str, *, reserved: Iterable[str] = DEFAULT_RESERVED) -> str:
    parts = [_slug(product, reserved=reserved), _slug(module, reserved=reserved), _slug(object_intent, reserved=reserved)]
    if any(part is None for part in parts):
        raise ValidationError("topic-axis", "topic_key_v1", "canonical axis has no auditable ASCII slug")
    return "v1/" + "/".join(part for part in parts if part is not None)


def topic_key_v2(
    knowledge_type: str,
    product: str,
    module: str,
    object_intent: str,
    *,
    reserved: Iterable[str] = DEFAULT_RESERVED,
) -> str:
    parts = [
        _slug(knowledge_type, reserved=reserved),
        _slug(product, reserved=reserved),
        _slug(module, reserved=reserved),
        _slug(object_intent, reserved=reserved),
    ]
    if any(part is None for part in parts):
        raise ValidationError("topic-axis", "topic_key_v2", "canonical axis has no auditable ASCII slug")
    return "v2/" + "/".join(part for part in parts if part is not None)


def degraded_key(evidence_values: Iterable[str], *, reserved: Iterable[str] = DEFAULT_RESERVED) -> str:
    for value in evidence_values:
        slug = _slug(value, reserved=reserved)
        if slug:
            return f"degraded/{slug}"
    raise ValidationError("topic-axis", "degraded_key", "no readable evidence slug is available")


def _evidence_path_slug(value: str, *, reserved: Iterable[str] = DEFAULT_RESERVED) -> str:
    """Make a collision-resistant ASCII slug from an evidence path.

    Canonical axes still use ``_slug`` and fail closed for non-ASCII values.
    Degraded keys may retain the source path's Unicode identity as ``uXXXX``
    segments so two Chinese-named files in one folder do not collapse into
    the same ``...-md`` key.  This is an encoding of the evidence, not a
    hash or an input-order suffix.
    """
    import unicodedata

    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    pieces: list[str] = []
    for char in normalized:
        if ("a" <= char <= "z") or ("0" <= char <= "9"):
            pieces.append(char)
        elif char.isspace() or char in "/\\._-":
            pieces.append("-")
        elif ord(char) < 128:
            pieces.append("-")
        else:
            pieces.append(f"-u{ord(char):x}-")
    slug = re.sub(r"-+", "-", "".join(pieces)).strip("-")
    if not slug:
        raise ValidationError("topic-axis", "degraded_key", "no readable evidence slug is available")
    reserved_values = set(reserved)
    if slug in reserved_values:
        slug = f"x-{slug}"
        if slug in reserved_values:
            raise ValidationError("topic-axis", "degraded_key", "reserved evidence slug collision")
    return slug


def _degraded_source_key(row: dict[str, Any], *, reserved: Iterable[str] = DEFAULT_RESERVED) -> str:
    parent_path = str(row.get("parent_path") or "").strip()
    content_path = str(row.get("content_path") or "").strip()
    if parent_path and content_path:
        # A parent directory alone is not a unique evidence item when a real
        # export contains many degraded pages below the same Confluence node.
        return f"degraded/{_evidence_path_slug(content_path, reserved=reserved)}"
    values = [
        row.get("h1") or "",
        row.get("title") or "",
        urlsplit(str(row.get("source_uri") or "")).path,
    ]
    return degraded_key(values, reserved=reserved)


def _source_meta(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("source_meta")
    return value if isinstance(value, dict) else {}


def _clean_source_seed(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    import unicodedata

    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def _seed_refs(row: dict[str, Any], field: str) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for raw in row.get("evidence_refs", []):
        if not isinstance(raw, dict):
            continue
        ref = dict(raw)
        ref["seed_field"] = field
        refs.append(ref)
    return refs


def build_source_product_gazetteer(
    inventory: list[dict[str, Any]],
    *,
    owner: str = "KnowledgeDigest source compiler",
) -> dict[str, Any]:
    """Build the source-canonical gazetteer without external vocabulary.

    Task1 treats an explicit ``products/<product>`` root and a declared source
    page/capability title as canonical facts of the current corpus.  This is a
    deterministic source-canonical confirmation, not a model promotion and not
    a claim about an external business taxonomy.  Provider/model proposals
    still enter through ``match_product_gazetteer`` as ``candidate`` and never
    change this output.
    """
    products: dict[str, dict[str, Any]] = {}
    modules: dict[str, dict[str, Any]] = {}
    for row in inventory:
        if _knowledge_type(row) != "products":
            continue
        parent_path = str(row.get("parent_path") or "")
        parent_parts = list(Path(parent_path).parts)
        product_index = parent_parts.index("products") + 1 if "products" in parent_parts else 0
        product_seed = _clean_source_seed(parent_parts[product_index] if product_index < len(parent_parts) else None)
        if product_seed:
            product = products.setdefault(
                product_seed.casefold(),
                {"canonical": product_seed, "aliases": set(), "source_refs": []},
            )
            product["aliases"].add(product_seed)
            product["source_refs"].extend(_seed_refs(row, "parent_path"))

        source_meta = _source_meta(row)
        declared_module = source_meta.get("module")
        title_seed = _clean_source_seed(declared_module) or _clean_source_seed(row.get("title"))
        h1_seed = _clean_source_seed(row.get("h1"))
        module_seed = title_seed or h1_seed or _clean_source_seed(Path(str(row.get("content_path") or "")).stem)
        if module_seed:
            module = modules.setdefault(
                module_seed.casefold(),
                {"canonical": module_seed, "aliases": set(), "source_refs": []},
            )
            explicit_aliases = source_meta.get("module_aliases", [])
            if not isinstance(explicit_aliases, list):
                explicit_aliases = []
            for alias in [*explicit_aliases, h1_seed if h1_seed != module_seed else None]:
                if alias and alias.casefold() != module_seed.casefold():
                    module["aliases"].add(alias)
            module["source_refs"].extend(_seed_refs(row, "title_or_h1"))

    entries: list[dict[str, Any]] = []
    for kind, seeds in (("product", products), ("module", modules)):
        for item in seeds.values():
            refs = sorted(
                item["source_refs"],
                key=lambda ref: (
                    str(ref.get("source_uri")),
                    int(ref.get("line_number") or 0),
                    str(ref.get("content_fingerprint")),
                    str(ref.get("seed_field")),
                ),
            )
            entries.append(
                {
                    "kind": kind,
                    "canonical": item["canonical"],
                    "aliases": sorted(item["aliases"], key=str.casefold),
                    "object_intents": [],
                    "owner": owner,
                    "source_refs": refs,
                    "status": "canonical",
                    "reason": "source-canonical fact from the explicit products root and source evidence; no external vocabulary or model promotion",
                }
            )
    return _gazetteer_defaults(
        {
            "schema_version": TOPIC_AXIS_SCHEMA_VERSION,
            "owner": owner,
            "match_order": list(MATCH_ORDER),
            "entries": entries,
        }
    )


def _first_heading(text: str) -> tuple[str | None, int | None]:
    for number, line in enumerate(text.splitlines(), start=1):
        match = _H1.match(line)
        if match:
            return match.group(1).strip(), number
    return None, None


def _structure_features(text: str, *, content_path: str, title: str | None, parent_path: str | None) -> dict[str, bool]:
    lines = text.splitlines()
    lower = text.casefold()
    return {
        "parent_child": bool(parent_path) or "/" in content_path or bool(re.search(r"(?:parent|parent_path)\s*:", lower)),
        "table": any("|" in line and line.count("|") >= 2 for line in lines),
        "faq": bool(re.search(r"\b(?:faq|frequently asked|常见问题|问答)\b", lower)),
        "image": bool(re.search(r"!\[[^]]*\]\([^)]*\)|<img\b", text, re.I)),
        "bilingual": bool(re.search(r"[\u4e00-\u9fff]", text) and re.search(r"[A-Za-z]", text)),
        "version": bool(_VERSION.search(text)),
        "noise": not bool((title or "").strip()) or bool(re.search(r"(?:todo|draft|lorem ipsum|噪声)", lower)),
    }


def _normal_link_target(source_path: str, target: str) -> str | None:
    target = unquote(target.strip().split("#", 1)[0])
    if not target or target.startswith(("http:", "https:", "mailto:", "ftp:")):
        return None
    # A host-relative web link such as `/wiki/spaces/...` is an external
    # Confluence link, not a local source-tree path.  Ignore that known web
    # shape as an edge; other absolute targets remain fail-closed.  We never
    # resolve or read an absolute filesystem path.
    if target == "/wiki" or target.startswith("/wiki/"):
        return None
    if target.startswith("/"):
        raise ValidationError("topic-axis", target, "internal link must not escape the source tree")
    import posixpath

    base = Path(source_path).parent.as_posix()
    normalized = posixpath.normpath(posixpath.join(base, target))
    if normalized == ".." or normalized.startswith("../"):
        raise ValidationError("topic-axis", target, "internal link escapes the source tree")
    candidate = Path(normalized)
    if candidate.suffix == "":
        candidate = candidate.with_suffix(".md")
    candidate = Path(*[part for part in candidate.parts if part not in {"", "."}])
    return candidate.as_posix()


def build_source_inventory(new_dir_or_paths: Path | DigestPaths, *, expected_count: int | None = None) -> list[dict[str, Any]]:
    """Create a stable, lossless structural inventory from the declared inputs."""
    new_dir = new_dir_or_paths.new_dir if isinstance(new_dir_or_paths, DigestPaths) else Path(new_dir_or_paths)
    items_dir = new_dir / "items"
    declarations = _read_jsonl(new_dir / "sources.jsonl")
    by_path: dict[str, dict[str, Any]] = {}
    for row in declarations:
        path = _relative_content_path(row.get("content_path"), items_dir)
        if path in by_path:
            raise ValidationError("topic-axis", path, "source path is declared more than once")
        uri = row.get("source_uri")
        if not isinstance(uri, str) or not uri.strip():
            raise ValidationError("topic-axis", path, f"source_uri is missing at sources.jsonl:{row['_line_number']}")
        knowledge_type = _normalize_knowledge_type(row.get("knowledge_type"))
        by_path[path] = {**row, "content_path": path, "source_uri": uri.strip(), "knowledge_type": knowledge_type}
    files = sorted(
        path.relative_to(items_dir).as_posix()
        for path in items_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in _INGESTIBLE
    )
    missing = sorted(set(files) - set(by_path))
    if missing:
        raise ValidationError("topic-axis", ", ".join(missing), "source file is absent from sources.jsonl")
    extra = sorted(set(by_path) - set(files))
    if extra:
        raise ValidationError("topic-axis", ", ".join(extra), "source declaration does not point to a readable input file")
    if expected_count is not None and len(files) != expected_count:
        raise ValidationError("topic-axis", "source inventory", f"expected {expected_count} sources, found {len(files)}")
    uri_fingerprints: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    for content_path in files:
        declaration = by_path[content_path]
        path = items_dir / content_path
        if path.is_symlink():
            raise ValidationError("topic-axis", path, "source input must not be a symlink")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise ValidationError("topic-axis", path, f"source snapshot cannot be read ({error})") from error
        fingerprint = hashlib.sha256(text.encode("utf-8")).hexdigest()
        previous = uri_fingerprints.get(declaration["source_uri"])
        if previous is not None and previous != fingerprint:
            raise ValidationError("topic-axis", declaration["source_uri"], "same URI declares conflicting fingerprints")
        uri_fingerprints[declaration["source_uri"]] = fingerprint
        h1, h1_line = _first_heading(text)
        metadata = {key: value for key, value in declaration.items() if not key.startswith("_")}
        metadata.update(_source_meta(declaration))
        declared_title = metadata.get("title")
        title = declared_title.strip() if isinstance(declared_title, str) and declared_title.strip() else Path(content_path).stem
        parent_path = metadata.get("parent_path") or metadata.get("parent")
        if not isinstance(parent_path, str) or not parent_path.strip():
            parent_path = str(Path(content_path).parent) if str(Path(content_path).parent) != "." else None
        source_edges: list[dict[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            for target in _SOURCE_LINE.findall(line):
                normalized = _normal_link_target(content_path, target)
                if normalized is None:
                    continue
                target_uri = by_path.get(normalized, {}).get("source_uri")
                if not target_uri:
                    raise ValidationError("topic-axis", f"{content_path}:{line_number}", f"internal link target is not declared: {normalized}")
                source_edges.append(
                    {
                        "target_path": normalized,
                        "target_source_uri": target_uri,
                        "line_number": line_number,
                    }
                )
        source_edges.sort(key=lambda edge: (str(edge["target_source_uri"] or edge["target_path"]), edge["target_path"], edge["line_number"]))
        evidence = [{"source_uri": declaration["source_uri"], "content_fingerprint": fingerprint, "line_number": h1_line or 1}]
        records.append(
            {
                "source_id": source_id(declaration["source_uri"]),
                "source_uri": declaration["source_uri"],
                "knowledge_type": declaration["knowledge_type"],
                "content_path": content_path,
                "content_fingerprint": fingerprint,
                "title": title,
                "h1": h1,
                "h1_line": h1_line,
                "parent_path": parent_path,
                "structure_features": _structure_features(text, content_path=content_path, title=title, parent_path=parent_path),
                "link_edges": source_edges,
                "evidence_refs": evidence,
                "source_meta": metadata,
                "validation_status": "passed",
            }
        )
    records.sort(key=lambda row: (row["source_uri"], row["content_path"]))
    return records


def _gazetteer_defaults(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = dict(value or {})
    entries = value.get("entries", [])
    if not isinstance(entries, list):
        raise ValidationError("topic-axis", "ProductGazetteer.entries", "must be a list")
    result = {
        "schema_version": str(value.get("schema_version") or TOPIC_AXIS_SCHEMA_VERSION),
        "owner": value.get("owner"),
        "match_order": list(value.get("match_order") or MATCH_ORDER),
        "entries": [],
    }
    if tuple(result["match_order"]) != MATCH_ORDER:
        raise ValidationError("topic-axis", "ProductGazetteer.match_order", "must use the fixed match order")
    for index, raw in enumerate(entries):
        if not isinstance(raw, dict):
            raise ValidationError("topic-axis", f"ProductGazetteer.entries[{index}]", "must be an object")
        kind = raw.get("kind")
        status = raw.get("status")
        if kind not in {"product", "module"}:
            raise ValidationError("topic-axis", f"ProductGazetteer.entries[{index}].kind", "must be product or module")
        if status not in {"canonical", "candidate", "conflict", "unknown"}:
            raise ValidationError("topic-axis", f"ProductGazetteer.entries[{index}].status", "has unsupported status")
        canonical = raw.get("canonical")
        aliases = raw.get("aliases", [])
        object_intents = raw.get("object_intents", [])
        source_refs = raw.get("source_refs", [])
        if not isinstance(canonical, str) or not canonical.strip():
            raise ValidationError("topic-axis", f"ProductGazetteer.entries[{index}].canonical", "must be non-empty")
        if not isinstance(aliases, list) or any(not isinstance(item, str) for item in aliases):
            raise ValidationError("topic-axis", f"ProductGazetteer.entries[{index}].aliases", "must be a string list")
        if not isinstance(object_intents, list) or any(not isinstance(item, str) for item in object_intents):
            raise ValidationError("topic-axis", f"ProductGazetteer.entries[{index}].object_intents", "must be a string list")
        if not isinstance(source_refs, list) or any(not isinstance(item, (str, dict)) for item in source_refs):
            raise ValidationError("topic-axis", f"ProductGazetteer.entries[{index}].source_refs", "must be a list")
        if status == "canonical" and (not str(raw.get("owner") or "").strip() or not source_refs):
            raise ValidationError("topic-axis", f"ProductGazetteer.entries[{index}]", "canonical entry needs owner and source_refs")
        result["entries"].append(
            {
                "kind": kind,
                "canonical": canonical.strip(),
                "aliases": sorted(set(item.strip() for item in aliases if item.strip()), key=str.casefold),
                "object_intents": sorted(set(item.strip() for item in object_intents if item.strip()), key=str.casefold),
                "owner": str(raw.get("owner") or ""),
                "source_refs": sorted(source_refs, key=lambda item: _json(item)),
                "status": status,
                "reason": str(raw.get("reason") or ""),
            }
        )
    result["entries"].sort(key=lambda item: (item["kind"], _slug(item["canonical"]) or item["canonical"].casefold()))
    return result


def _load_fenced_json(structure_path: Path, marker: str, section_name: str) -> dict[str, Any] | None:
    text = structure_path.read_text(encoding="utf-8")
    start = text.find(marker)
    if start < 0:
        return None
    fenced_start = text.find("```json", start)
    if fenced_start < 0:
        raise ValidationError("topic-axis", structure_path, f"{section_name} section has no JSON block")
    payload_start = fenced_start + len("```json")
    end = text.find("```", payload_start)
    if end < 0:
        raise ValidationError("topic-axis", structure_path, f"{section_name} JSON block is unterminated")
    try:
        value = json.loads(text[payload_start:end].strip())
    except json.JSONDecodeError as error:
        raise ValidationError("topic-axis", structure_path, f"{section_name} JSON is invalid") from error
    if not isinstance(value, dict):
        raise ValidationError("topic-axis", structure_path, f"{section_name} JSON must be an object")
    return value


def _write_fenced_section(structure_path: Path, marker: str, section: str, section_name: str) -> None:
    text = structure_path.read_text(encoding="utf-8")
    start = text.find(marker)
    if start >= 0:
        fence = text.find("```json", start)
        end = text.find("```", fence + len("```json")) if fence >= 0 else -1
        if end < 0:
            raise ValidationError("topic-axis", structure_path, f"{section_name} JSON block is unterminated")
        text = text[:start] + section.rstrip("\n") + text[end + 3 :]
    else:
        text = text.rstrip() + "\n\n" + section
    descriptor, temporary_name = tempfile.mkstemp(
        dir=structure_path.parent, prefix=f".{structure_path.name}.", suffix=".tmp", text=True
    )
    temporary = Path(temporary_name)
    try:
        with open(descriptor, "w", encoding="utf-8", closefd=True) as handle:
            handle.write(text)
            handle.flush()
        temporary.replace(structure_path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def load_product_gazetteer(structure_path: Path) -> dict[str, Any]:
    value = _load_fenced_json(structure_path, "<!-- KnowledgeDigest:ProductGazetteer -->", "ProductGazetteer")
    return _gazetteer_defaults(value)


def serialize_product_gazetteer(value: dict[str, Any]) -> str:
    return "<!-- KnowledgeDigest:ProductGazetteer -->\n```json\n" + json.dumps(_gazetteer_defaults(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n```\n"


def write_product_gazetteer(structure_path: Path, value: dict[str, Any]) -> None:
    section = serialize_product_gazetteer(value)
    _write_fenced_section(structure_path, "<!-- KnowledgeDigest:ProductGazetteer -->", section, "ProductGazetteer")


def load_knowledge_type_registry(structure_path: Path) -> dict[str, Any]:
    value = _load_fenced_json(structure_path, "<!-- KnowledgeDigest:KnowledgeTypeRegistry -->", "KnowledgeTypeRegistry")
    return _knowledge_type_registry_defaults(value)


def serialize_knowledge_type_registry(value: dict[str, Any]) -> str:
    return "<!-- KnowledgeDigest:KnowledgeTypeRegistry -->\n```json\n" + json.dumps(
        _knowledge_type_registry_defaults(value), ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n```\n"


def write_knowledge_type_registry(structure_path: Path, value: dict[str, Any]) -> None:
    section = serialize_knowledge_type_registry(value)
    _write_fenced_section(structure_path, "<!-- KnowledgeDigest:KnowledgeTypeRegistry -->", section, "KnowledgeTypeRegistry")


def _norm_match(value: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", str(value or "").casefold())).strip()


def _match_values(record: dict[str, Any], tier: str, kind: str) -> list[str]:
    meta = record.get("source_meta") if isinstance(record.get("source_meta"), dict) else {}
    if tier in {"canonical", "alias"}:
        return [str(meta[kind]) for _ in (0,) if isinstance(meta.get(kind), str)]
    if tier == "parent_path":
        value = str(record.get("parent_path") or "")
        return [value, *Path(value).parts]
    if tier == "h1_title":
        return [str(record.get("h1") or ""), str(record.get("title") or "")]
    return []


def match_product_gazetteer(record: dict[str, Any], gazetteer: dict[str, Any]) -> dict[str, Any]:
    gazetteer = _gazetteer_defaults(gazetteer)
    result: dict[str, Any] = {"source_id": record["source_id"], "product": None, "module": None, "matches": [], "status": "published", "reason": ""}
    for kind in ("product", "module"):
        chosen: dict[str, Any] | None = None
        chosen_tier: str | None = None
        conflict = False
        for tier in MATCH_ORDER:
            if tier == "candidate":
                meta = record.get("source_meta") if isinstance(record.get("source_meta"), dict) else {}
                candidate_value = meta.get(f"{kind}_candidate") or meta.get(f"{kind}_model_candidate")
                if isinstance(candidate_value, str) and candidate_value.strip():
                    chosen = {
                        "kind": kind,
                        "canonical": candidate_value.strip(),
                        "aliases": [],
                        "object_intents": [],
                        "owner": "",
                        "source_refs": [],
                        "status": "candidate",
                        "reason": "provider/model candidate; not promoted",
                        "matched_by_tier": tier,
                    }
                    chosen_tier = tier
                    result["matches"].append({"kind": kind, "tier": tier, "status": "candidate", "canonical": candidate_value.strip()})
                break
            values = {_norm_match(value) for value in _match_values(record, tier, kind) if value}
            candidates: list[dict[str, Any]] = []
            for entry in gazetteer["entries"]:
                if entry["kind"] != kind:
                    continue
                names = [entry["canonical"]] if tier == "canonical" else entry["aliases"] if tier == "alias" else [entry["canonical"], *entry["aliases"]]
                if any(_norm_match(name) in values for name in names):
                    candidates.append(entry)
            if candidates:
                if len(candidates) > 1:
                    conflict = True
                    result["matches"].append({"kind": kind, "tier": tier, "status": "conflict", "canonical": sorted(item["canonical"] for item in candidates)})
                else:
                    chosen, chosen_tier = candidates[0], tier
                    result["matches"].append({"kind": kind, "tier": tier, "status": chosen["status"], "canonical": chosen["canonical"]})
                break
        if conflict:
            result["status"] = "degraded"
            result["reason"] = f"{kind} has multiple {chosen_tier or 'same-tier'} matches"
        elif chosen is None:
            result["status"] = "degraded"
            result["reason"] = f"{kind} is unknown"
        elif chosen["status"] != "canonical" or chosen_tier == "candidate":
            result["status"] = "degraded"
            result["reason"] = f"{kind} match is not canonical"
        result[kind] = {**chosen, "matched_by_tier": chosen_tier} if chosen is not None else None
    if result["product"] is None or result["module"] is None:
        result["status"] = "degraded"
    return result


def _object_candidates(record: dict[str, Any]) -> list[tuple[str, str]]:
    meta = record.get("source_meta") if isinstance(record.get("source_meta"), dict) else {}
    values: list[tuple[str, str]] = []
    managed = meta.get("managed_object_intent") or meta.get("object_intent")
    if isinstance(managed, str) and managed.strip():
        values.append(("managed", managed.strip()))
    elif isinstance(meta.get("object"), str) and isinstance(meta.get("intent"), str):
        values.append(("metadata", f"{meta['object'].strip()} {meta['intent'].strip()}"))
    elif isinstance(meta.get("object"), str) and meta["object"].strip():
        values.append(("metadata", meta["object"].strip()))
    elif isinstance(meta.get("intent"), str) and meta["intent"].strip():
        values.append(("metadata", meta["intent"].strip()))
    h1 = record.get("h1")
    title = record.get("title")
    if isinstance(h1, str) and h1.strip():
        values.append(("h1", h1.strip()))
    if isinstance(title, str) and title.strip() and title != h1:
        values.append(("title", title.strip()))
    parent = record.get("parent_path")
    if isinstance(parent, str) and parent.strip():
        values.append(("parent_path", Path(parent).name))
    return values


def _single_source_checks(record: dict[str, Any], match: dict[str, Any], object_status: str, *, conflict: bool = False) -> dict[str, bool]:
    features = record.get("structure_features") if isinstance(record.get("structure_features"), dict) else {}
    evidence = record.get("evidence_refs") if isinstance(record.get("evidence_refs"), list) else []
    required_features = {"parent_child", "table", "faq", "image", "bilingual", "version", "noise"}
    fingerprint = record.get("content_fingerprint")
    complete_evidence = any(
        isinstance(ref, dict)
        and isinstance(ref.get("source_uri"), str)
        and ref.get("source_uri") == record.get("source_uri")
        and isinstance(ref.get("content_fingerprint"), str)
        and ref.get("content_fingerprint") == fingerprint
        and isinstance(ref.get("line_number"), int)
        and ref["line_number"] >= 1
        for ref in evidence
    )
    return {
        "资料完整": bool(
            isinstance(record.get("source_uri"), str)
            and record["source_uri"].strip()
            and isinstance(fingerprint, str)
            and re.fullmatch(r"[0-9a-f]{64}", fingerprint)
            and isinstance(record.get("content_path"), str)
            and record["content_path"].strip()
            and (record.get("title") or record.get("h1"))
            and isinstance(record.get("parent_path"), str)
            and record["parent_path"].strip()
            and isinstance(record.get("source_id"), str)
            and record["source_id"].strip()
            and required_features <= set(features)
            and all(isinstance(features[key], bool) for key in required_features)
            and record.get("validation_status") == "passed"
        ),
        "topic_axis_explicit": match.get("status") == "published" and (match.get("product") or {}).get("status") == "canonical" and (match.get("module") or {}).get("status") == "canonical",
        "meaningful_structure": bool(record.get("h1") or record.get("title") or record.get("parent_path") or any(value for key, value in features.items() if key != "noise")),
        "required_evidence": complete_evidence,
        "fact_conflict_free": not conflict,
    }


def _evidence_refs(members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for member in members:
        refs.extend(member.get("evidence_refs", []))
    return sorted(refs, key=lambda ref: (str(ref.get("source_uri")), int(ref.get("line_number") or 0), str(ref.get("content_fingerprint"))))


def _explicit_topic_page_type(member_rows: list[dict[str, Any]]) -> str | None:
    """Preserve explicit source metadata in the Task1 topic authority.

    Titles, headings and body text are deliberately not classifiers. A merged
    topic must declare one identical value for every member; otherwise the
    upstream snapshot is ambiguous and must stop rather than guess.
    """
    values: list[str | None] = []
    for row in member_rows:
        metadata = row.get("source_meta") if isinstance(row.get("source_meta"), dict) else {}
        raw_value = row.get("page_type") if "page_type" in row else metadata.get("page_type")
        if raw_value is None:
            values.append(None)
            continue
        if not isinstance(raw_value, str) or not raw_value.strip():
            raise ValidationError("topic-axis", row.get("source_id") or "page_type", "explicit page_type must be a non-empty string")
        page_type = raw_value.strip()
        if page_type not in _EXPLICIT_TOPIC_PAGE_TYPES:
            raise ValidationError("topic-axis", row.get("source_id") or "page_type", f"unsupported explicit page_type: {page_type}")
        values.append(page_type)
    if not any(value is not None for value in values):
        return None
    if any(value is None for value in values):
        raise ValidationError(
            "topic-axis",
            ",".join(sorted(str(row.get("source_id") or "") for row in member_rows)),
            "merged topic page_type metadata is incomplete",
        )
    unique = sorted({value for value in values if value is not None})
    if len(unique) != 1:
        raise ValidationError(
            "topic-axis",
            ",".join(sorted(str(row.get("source_id") or "") for row in member_rows)),
            "merged topic page_type metadata conflicts",
        )
    return unique[0]


def build_topic_plan(
    inventory: list[dict[str, Any]],
    gazetteer: dict[str, Any],
    *,
    topic_root: str | None,
    reserved: Iterable[str] | None = None,
) -> dict[str, Any]:
    has_products = any(_knowledge_type(row) == "products" for row in inventory)
    gazetteer = _gazetteer_defaults(gazetteer) if has_products else {
        "schema_version": TOPIC_AXIS_SCHEMA_VERSION,
        "owner": None,
        "match_order": list(MATCH_ORDER),
        "entries": [],
    }
    matches: dict[str, dict[str, Any]] = {}
    for row in inventory:
        knowledge_type = _knowledge_type(row)
        if knowledge_type != "products":
            matches[row["source_id"]] = {
                "source_id": row["source_id"],
                "knowledge_type": knowledge_type,
                "product": None,
                "module": None,
                "matches": [],
                "status": "degraded",
                "reason": f"ProductGazetteer is not applicable to knowledge_type={knowledge_type}",
            }
            continue
        match = match_product_gazetteer(row, gazetteer)
        match["knowledge_type"] = knowledge_type
        matches[row["source_id"]] = match
    candidates: list[dict[str, Any]] = []
    degraded: list[dict[str, Any]] = []
    for row in inventory:
        match = matches[row["source_id"]]
        object_values = _object_candidates(row)
        object_status = "missing" if not object_values else "unique"
        object_value: str | None = None
        if object_values:
            first_tier = object_values[0][0]
            same_tier = sorted({value for tier, value in object_values if tier == first_tier})
            if len(same_tier) == 1:
                object_value = same_tier[0]
            else:
                object_status = "conflict"
        gazetteer_conflict = any(item.get("status") == "conflict" for item in match.get("matches", []))
        checks = _single_source_checks(row, match, object_status, conflict=object_status == "conflict" or gazetteer_conflict)
        canonical = match.get("status") == "published" and object_status == "unique" and all(checks.values()) and topic_root
        if canonical:
            key = (match["product"]["canonical"], match["module"]["canonical"], object_value or "")
            candidates.append({"row": row, "match": match, "object": object_value, "checks": checks, "group": key})
        else:
            reasons = [key for key, value in checks.items() if not value]
            if not topic_root:
                reasons.append("topic root declaration is missing")
            if object_status != "unique":
                reasons.append(f"object/intent seed is {object_status}")
            if _knowledge_type(row) != "products":
                reasons.append(match.get("reason") or "ProductGazetteer is not applicable")
            degraded.append({"row": row, "match": match, "object": None, "checks": checks, "reason": "; ".join(reasons) or match.get("reason") or "degraded"})
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        product, module, object_value = item["group"]
        groups[(
            _slug(product, reserved=()),
            _slug(module, reserved=()),
            _slug(object_value, reserved=()),
        )].append(item)
    topics: list[dict[str, Any]] = []
    reserved_values = set(DEFAULT_RESERVED)
    if reserved is not None:
        reserved_values.update(str(item) for item in reserved if str(item).strip())
    if topic_root:
        reserved_values.update(Path(topic_root).parts)
    candidate_topics: list[dict[str, Any]] = []
    for group, items in sorted(
        groups.items(),
        key=lambda pair: tuple("" if part is None else part for part in pair[0]),
    ):
        product = items[0]["match"]["product"]["canonical"]
        module = items[0]["match"]["module"]["canonical"]
        object_value = items[0]["object"]
        member_rows = [item["row"] for item in items]
        try:
            key = topic_key_v2(_knowledge_type(member_rows[0]), product, module, object_value, reserved=reserved_values)
        except ValidationError:
            for item in items:
                degraded.append(
                    {
                        **item,
                        "object": None,
                        "reason": "topic key cannot escape a reserved-word collision",
                    }
                )
            continue
        page_type = _explicit_topic_page_type(member_rows)
        candidate_topics.append(
            {
                "topic_key": key,
                "knowledge_type": _knowledge_type(member_rows[0]),
                "product": product,
                "module": module,
                "object_intent": object_value,
                "source_members": sorted(row["source_id"] for row in member_rows),
                "published_path": f"{topic_root}/{key.removeprefix('v2/')}.md" if topic_root else None,
                "old_path_mapping": [],
                "status": "published",
                "merge_mode": "single" if len(items) == 1 else "merge",
                "topic_plan_version": TOPIC_PLAN_SCHEMA_VERSION,
                "reason": "",
                "evidence_refs": _evidence_refs(member_rows),
                "single_source_checks": items[0]["checks"] if len(items) == 1 else None,
                "candidate_items": items,
                **({"page_type": page_type} if page_type else {}),
            }
        )
    candidate_key_counts = defaultdict(int)
    for topic in candidate_topics:
        candidate_key_counts[topic["topic_key"]] += 1
    for candidate in candidate_topics:
        if candidate_key_counts[candidate["topic_key"]] == 1:
            candidate.pop("candidate_items", None)
            topics.append(candidate)
            continue
        raise ValidationError(
            "topic-axis",
            "PUBLISHED_PATH_COLLISION",
            f"topic key/path collision: {candidate['topic_key']}",
        )
    for item in sorted(degraded, key=lambda value: (value["row"]["source_uri"], value["row"]["source_id"])):
        row = item["row"]
        key = _degraded_source_key(row, reserved=reserved_values)
        if any(topic["topic_key"] == key for topic in topics):
            raise ValidationError("topic-axis", key, "DEGRADED_KEY_COLLISION")
        topics.append(
            {
                "topic_key": key,
                "knowledge_type": _knowledge_type(row),
                "product": None,
                "module": None,
                "object_intent": None,
                "source_members": [row["source_id"]],
                "published_path": None,
                "old_path_mapping": [],
                "status": "degraded",
                "merge_mode": "degraded",
                "topic_plan_version": TOPIC_PLAN_SCHEMA_VERSION,
                "reason": item["reason"],
                "evidence_refs": _evidence_refs([row]),
                "single_source_checks": item["checks"],
            }
        )
    topics.sort(key=lambda topic: topic["topic_key"])
    # Formal paths are identity-derived and must be unique.  Never add a suffix.
    seen_topic_keys: set[str] = set()
    seen_paths: dict[str, str] = {}
    for topic in topics:
        if topic["topic_key"] in seen_topic_keys:
            raise ValidationError("topic-axis", topic["topic_key"], "TOPIC_KEY_COLLISION")
        seen_topic_keys.add(topic["topic_key"])
        path = topic.get("published_path")
        if not path:
            continue
        previous = seen_paths.get(path)
        if previous and previous != topic["topic_key"]:
            raise ValidationError("topic-axis", path, "PUBLISHED_PATH_COLLISION")
        seen_paths[path] = topic["topic_key"]
    return {
        "schema_version": TOPIC_PLAN_SCHEMA_VERSION,
        "topic_plan_version": TOPIC_PLAN_SCHEMA_VERSION,
        "status": "frozen",
        "provider_boundary": "before_provider",
        "topics": topics,
        "matches": [matches[key] for key in sorted(matches)],
        "plan_sha256": _sha(topics),
    }


def build_topic_examples(
    inventory: list[dict[str, Any]],
    gazetteer: dict[str, Any],
    *,
    topic_root: str | None,
    include_failure_matrix: bool = False,
    reserved: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Return examples; synthetic failure rows are test-fixture-only by opt-in."""
    examples: list[dict[str, Any]] = []
    full_plan = build_topic_plan(inventory, gazetteer, topic_root=topic_root, reserved=reserved)
    merged = next((topic for topic in full_plan["topics"] if topic["status"] == "published" and len(topic["source_members"]) > 1), None)
    if merged:
        examples.append({"example_id": "example-merge", "kind": "normal_merge", "source_members": merged["source_members"], "topic": merged, "evidence_refs": merged["evidence_refs"]})
    if inventory:
        unknown_plan = next(
            (topic for topic in full_plan["topics"] if topic["status"] == "degraded" and "unknown" in str(topic.get("reason", "")).lower()),
            None,
        )
        if unknown_plan is None and include_failure_matrix:
            unknown_row = dict(inventory[0], source_meta={}, parent_path="products/unknown", title=None, h1=None)
            unknown_plan = build_topic_plan([unknown_row], gazetteer, topic_root=topic_root, reserved=reserved)["topics"][0]
        if unknown_plan:
            examples.append({"example_id": "example-unknown", "kind": "unknown", "source_members": unknown_plan["source_members"], "topic": unknown_plan, "evidence_refs": unknown_plan["evidence_refs"]})
        if include_failure_matrix:
            entries = list(gazetteer.get("entries", []))
            product = next((entry for entry in entries if entry.get("kind") == "product"), None)
            if product:
                conflict_gazetteer = dict(gazetteer)
                conflict_gazetteer["entries"] = [*entries, {**product, "owner": "conflict-owner", "source_refs": ["fixture:conflict"]}]
                conflict_plan = build_topic_plan([inventory[0]], conflict_gazetteer, topic_root=topic_root, reserved=reserved)["topics"][0]
                examples.append({"example_id": "example-conflict", "kind": "conflict_degraded", "source_members": conflict_plan["source_members"], "topic": conflict_plan, "evidence_refs": conflict_plan["evidence_refs"]})
            base = inventory[0]
            failure_cases: list[tuple[str, dict[str, Any]]] = []
            failure_cases.append(("资料完整", dict(base, parent_path=None)))
            failure_cases.append(("topic_axis_explicit", dict(base, source_meta={**_source_meta(base), "product": "Candidate Product"})))
            failure_cases.append(("meaningful_structure", dict(base, title=None, h1=None, parent_path=None, structure_features={key: (key == "noise") for key in ("parent_child", "table", "faq", "image", "bilingual", "version", "noise")})))
            failure_cases.append(("required_evidence", dict(base, evidence_refs=[{"source_uri": base["source_uri"], "content_fingerprint": "0" * 64, "line_number": 0}])))
            failure_cases.append(("fact_conflict_free", base))
            for field, failure_row in failure_cases:
                failure_gazetteer = gazetteer
                if field == "fact_conflict_free":
                    product = next((entry for entry in gazetteer.get("entries", []) if entry.get("kind") == "product"), None)
                    if product:
                        failure_gazetteer = dict(gazetteer)
                        failure_gazetteer["entries"] = [*gazetteer.get("entries", []), {**product, "owner": "conflict-owner", "source_refs": ["fixture:conflict-failure"]}]
                failure_topic = build_topic_plan([failure_row], failure_gazetteer, topic_root=topic_root, reserved=reserved)["topics"][0]
                examples.append({"example_id": f"example-failure-{field}", "kind": "single_source_failure", "failed_check": field, "source_members": failure_topic["source_members"], "topic": failure_topic, "evidence_refs": failure_topic["evidence_refs"]})
    remaining = max(0, 20 - len(examples))
    for row in sorted(inventory, key=lambda item: (item["source_uri"], item["source_id"]))[:remaining]:
        single = build_topic_plan([row], gazetteer, topic_root=topic_root, reserved=reserved)
        topic = single["topics"][0]
        examples.append(
            {
                "example_id": f"example-{len(examples) + 1:03d}",
                "kind": "normal" if topic["status"] == "published" else "degraded",
                "source_members": topic["source_members"],
                "topic": topic,
                "evidence_refs": topic["evidence_refs"],
            }
        )
    return examples


def topic_index_from_plan(plan: dict[str, Any], *, old_topic_index: dict[str, Any] | None = None) -> dict[str, Any]:
    old_rows = (old_topic_index or {}).get("topics", []) if isinstance(old_topic_index, dict) else []
    old_rows = [row for row in old_rows if isinstance(row, dict)]
    old_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for old in old_rows:
        members = old.get("source_members") or old.get("source_ids") or []
        for member in members:
            old_by_source[str(member)].append(old)
    old_by_path = {
        str(row.get("published_path") or row.get("legacy_published_path")): row
        for row in old_rows
        if row.get("published_path") or row.get("legacy_published_path")
    }
    topics: list[dict[str, Any]] = []
    path_users: dict[str, list[str]] = defaultdict(list)
    for row in plan.get("topics", []):
        matching_old: dict[str, dict[str, Any]] = {}
        for member in row.get("source_members", []):
            for old in old_by_source.get(str(member), []):
                identity = str(old.get("topic_key") or old.get("topic_id") or old.get("digest_topic_id") or "")
                if identity:
                    matching_old[identity] = old
        old = old_by_path.get(str(row.get("published_path")))
        if old is not None:
            identity = str(old.get("topic_key") or old.get("topic_id") or old.get("digest_topic_id") or "")
            if identity:
                matching_old[identity] = old
        item = dict(row)
        if matching_old:
            ordered_old = [matching_old[key] for key in sorted(matching_old)]
            first = ordered_old[0]
            item["digest_topic_id"] = first.get("digest_topic_id") or first.get("topic_id")
            mappings: list[dict[str, Any]] = []
            for candidate in ordered_old:
                old_path = candidate.get("published_path") or candidate.get("legacy_published_path")
                if not old_path:
                    continue
                candidate_identity = str(candidate.get("topic_key") or candidate.get("topic_id") or candidate.get("digest_topic_id") or "")
                if old_path == row.get("published_path"):
                    continue
                mappings.append(
                    {
                        "old_path": old_path,
                        "relation": "merge" if len(ordered_old) > 1 else "rename",
                        "evidence_refs": list(row.get("evidence_refs") or [{"source_uri": "legacy://topic-index", "content_fingerprint": "0" * 64, "line_number": 1}]),
                    }
                )
                path_users[str(old_path)].append(str(row["topic_key"]))
            item["old_path_mapping"] = mappings
        else:
            item["digest_topic_id"] = None
        item["topic_id"] = item.get("digest_topic_id") or item["topic_key"]
        item["source_ids"] = list(item["source_members"])
        item["category_id"] = None
        item["product_slug"] = _slug(item.get("product")) if item.get("product") else None
        topics.append(item)
    # One old path feeding multiple current topics is a split, not a silent
    # rename.  Rebuild the relation on each affected row deterministically.
    for item in topics:
        for mapping in item.get("old_path_mapping", []):
            if len(set(path_users.get(str(mapping["old_path"]), []))) > 1:
                mapping["relation"] = "split"
    topics.sort(key=lambda row: row["topic_key"])
    return {"schema_version": TOPIC_INDEX_SCHEMA_VERSION, "topics": topics, "index_sha256": _sha(topics)}


def _topic_for_source(plan: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for topic in plan.get("topics", []):
        for member in topic.get("source_members", []):
            result[str(member)] = str(topic["topic_key"])
    return result


def affected_set(
    inventory: list[dict[str, Any]],
    plan: dict[str, Any],
    *,
    previous_inventory: list[dict[str, Any]] | None = None,
    previous_plan: dict[str, Any] | None = None,
    current_index: dict[str, Any] | None = None,
    previous_index: dict[str, Any] | None = None,
    rebuild: bool = False,
) -> dict[str, Any]:
    current_topics = _topic_for_source(plan)
    previous_topics = _topic_for_source(previous_plan or {})
    current_by_uri = {row["source_uri"]: row for row in inventory}
    previous_by_uri = {row["source_uri"]: row for row in previous_inventory or []}
    changed_sources = {
        uri for uri in set(current_by_uri) | set(previous_by_uri)
        if _json(current_by_uri.get(uri)) != _json(previous_by_uri.get(uri))
    }
    affected_sources = {current_by_uri[uri]["source_id"] for uri in changed_sources if uri in current_by_uri}
    removed_sources = {row["source_id"] for uri, row in previous_by_uri.items() if uri not in current_by_uri}
    affected_sources.update(removed_sources)
    changed_topics = {current_topics.get(source) for source in affected_sources if current_topics.get(source)} | {previous_topics.get(source) for source in affected_sources if previous_topics.get(source)}
    current_matches = {str(item.get("source_id")): item for item in plan.get("matches", []) if isinstance(item, dict)}
    previous_matches = {str(item.get("source_id")): item for item in (previous_plan or {}).get("matches", []) if isinstance(item, dict)}
    for source in set(current_matches) | set(previous_matches):
        if _json(current_matches.get(source)) != _json(previous_matches.get(source)):
            affected_sources.add(source)
            if current_topics.get(source):
                changed_topics.add(current_topics[source])
            if previous_topics.get(source):
                changed_topics.add(previous_topics[source])
    def mapping_members(index: dict[str, Any] | None) -> dict[str, tuple[tuple[str, str, str], tuple[str, ...]]]:
        result: dict[str, tuple[tuple[str, str, str], tuple[str, ...]]] = {}
        for row in (index or {}).get("topics", []):
            if not isinstance(row, dict):
                continue
            key = str(row.get("topic_key") or row.get("topic_id") or row.get("digest_topic_id") or "")
            if not key:
                continue
            mappings = row.get("old_path_mapping") or []
            mapping_signature = tuple(
                sorted(
                    (
                        str(item.get("old_path")),
                        str(item.get("relation")),
                        _json(item.get("evidence_refs") or []),
                    )
                    for item in mappings
                    if isinstance(item, dict)
                )
            )
            if not mapping_signature and row.get("legacy_published_path"):
                mapping_signature = ((str(row["legacy_published_path"]), "legacy", ""),)
            members = tuple(sorted(str(item) for item in (row.get("source_members") or row.get("source_ids") or []) if item))
            result[key] = (mapping_signature, members)
        return result

    current_mappings = mapping_members(current_index)
    previous_mappings = mapping_members(previous_index)
    for key in set(current_mappings) | set(previous_mappings):
        if current_mappings.get(key) == previous_mappings.get(key):
            continue
        changed_topics.add(key)
        for source in (current_mappings.get(key, ((), ()))[1] + previous_mappings.get(key, ((), ()))[1]):
            affected_sources.add(source)
    if _json(previous_plan or {}) != _json(plan):
        changed_topics.update(set(current_topics.values()) ^ set(previous_topics.values()))
        # A plan can change while preserving every source-to-topic mapping,
        # for example when a topic's evidence, reason, or match projection is
        # revised.  Compare topic records as well, otherwise metadata-only
        # changes would miss the affected topic and its source members.
        current_topic_rows = {
            str(row.get("topic_key")): row
            for row in plan.get("topics", [])
            if isinstance(row, dict) and row.get("topic_key")
        }
        previous_topic_rows = {
            str(row.get("topic_key")): row
            for row in (previous_plan or {}).get("topics", [])
            if isinstance(row, dict) and row.get("topic_key")
        }
        for key in set(current_topic_rows) | set(previous_topic_rows):
            if _json(current_topic_rows.get(key)) == _json(previous_topic_rows.get(key)):
                continue
            changed_topics.add(key)
            for row in (current_topic_rows.get(key), previous_topic_rows.get(key)):
                if isinstance(row, dict):
                    affected_sources.update(str(member) for member in row.get("source_members", []) if member)
    if rebuild or previous_inventory is None or previous_plan is None:
        changed_topics.update(current_topics.values())
        affected_sources.update(row["source_id"] for row in inventory)
    related_sources: set[str] = set()
    all_rows = [row for row in [*(previous_inventory or []), *inventory] if isinstance(row, dict) and row.get("source_id")]
    for row in all_rows:
        if row["source_id"] not in affected_sources:
            continue
        for edge in row.get("link_edges", []):
            target_uri = edge.get("target_source_uri")
            target = current_by_uri.get(target_uri or "") or previous_by_uri.get(target_uri or "")
            if target:
                related_sources.add(target["source_id"])
                if current_topics.get(target["source_id"]):
                    changed_topics.add(current_topics[target["source_id"]])
                if previous_topics.get(target["source_id"]):
                    changed_topics.add(previous_topics[target["source_id"]])
    # An affected or deleted target also invalidates sources that point to it.
    # This reverse pass is required when the target is gone from the current
    # inventory, because only the previous snapshot still contains the edge.
    for row in all_rows:
        for edge in row.get("link_edges", []):
            target_uri = edge.get("target_source_uri")
            target = current_by_uri.get(target_uri or "") or previous_by_uri.get(target_uri or "")
            if not target or target["source_id"] not in affected_sources:
                continue
            source_id_value = row["source_id"]
            related_sources.add(source_id_value)
            if current_topics.get(source_id_value):
                changed_topics.add(current_topics[source_id_value])
            if previous_topics.get(source_id_value):
                changed_topics.add(previous_topics[source_id_value])
    affected_sources.update(related_sources)
    return {
        "schema_version": "1.0.0",
        "rebuild": bool(rebuild),
        "affected_source_ids": sorted(affected_sources),
        "affected_topic_keys": sorted(topic for topic in changed_topics if topic),
        "changed_source_uris": sorted(changed_sources),
        "related_source_ids": sorted(related_sources),
        "empty": not affected_sources and not changed_topics,
    }


def _frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            values[key.strip()] = value.strip().strip("\"'")
    return values


def _managed_content_hash(path: Path) -> str:
    """Hash the page payload, excluding the self-referential frontmatter."""
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    if lines and lines[0].strip() == b"---":
        for index in range(1, len(lines)):
            if lines[index].strip() == b"---":
                raw = b"".join(lines[index + 1:])
                break
    return hashlib.sha256(raw).hexdigest()


def find_managed_conflicts(kb_dir: Path, plan: dict[str, Any], *, run_id: str, override_manifest: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    manifest_rows = list(override_manifest or [])
    manifest_paths: set[str] = set()
    manifest_refs: set[str] = set()
    for index, row in enumerate(manifest_rows):
        if not isinstance(row, dict):
            raise ValidationError("topic-axis", f"override_manifest[{index}]", "must be an object")
        path_value = row.get("path")
        override_ref = row.get("override_ref")
        if not isinstance(path_value, str) or not path_value.strip():
            raise ValidationError("topic-axis", f"override_manifest[{index}].path", "must be non-empty")
        if path_value in manifest_paths:
            raise ValidationError("topic-axis", path_value, "override path is duplicated")
        manifest_paths.add(path_value)
        if not isinstance(override_ref, str) or not override_ref.strip():
            raise ValidationError("topic-axis", f"override_manifest[{index}].override_ref", "must be non-empty")
        if override_ref in manifest_refs:
            raise ValidationError("topic-axis", override_ref, "override_ref is duplicated")
        manifest_refs.add(override_ref)
    manifest_payload = [
        {key: value for key, value in row.items() if key != "manifest_sha256"}
        for row in manifest_rows
    ]
    manifest_sha256 = _sha(sorted(manifest_payload, key=lambda row: (str(row.get("path")), str(row.get("override_ref")))) if manifest_payload else [])
    overrides = {str(row["path"]): row for row in manifest_rows}
    conflicts: list[dict[str, Any]] = []
    for topic in plan.get("topics", []):
        path_value = topic.get("published_path")
        if not path_value:
            continue
        path = kb_dir / str(path_value)
        if not path.is_file():
            continue
        values = _frontmatter(path)
        expected = values.get("managed_content_hash") or values.get("content_hash")
        if not expected:
            conflicts.append({"code": "MANAGED_CONTENT_CONFLICT", "run_id": run_id, "topic_key": topic["topic_key"], "digest_topic_id": topic.get("digest_topic_id"), "path": str(path_value), "managed_content_hash": None, "actual_content_hash": _managed_content_hash(path), "action": "preserve_and_stop", "recovery": "reconcile_then_rerun", "reason": "existing published path has no valid managed content hash"})
            continue
        actual = _managed_content_hash(path)
        if expected == actual:
            continue
        override = overrides.get(str(path_value))
        if override and override.get("manifest_sha256") == manifest_sha256 and override.get("topic_key") == topic.get("topic_key") and override.get("actual_content_hash") == actual and override.get("managed_content_hash") == expected and override.get("reason") and override.get("operator_note"):
            conflicts.append({"code": "MANAGED_CONTENT_OVERRIDE", "run_id": run_id, "topic_key": topic["topic_key"], "path": str(path_value), "manifest_sha256": manifest_sha256, "override_ref": override["override_ref"], "action": "replace_after_explicit_override"})
            continue
        conflicts.append({"code": "MANAGED_CONTENT_CONFLICT", "run_id": run_id, "topic_key": topic["topic_key"], "digest_topic_id": topic.get("digest_topic_id"), "path": str(path_value), "managed_content_hash": expected, "actual_content_hash": actual, "action": "preserve_and_stop", "recovery": "reconcile_then_rerun"})
    return conflicts


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", text=True)
    temporary = Path(temporary_name)
    try:
        with open(descriptor, "w", encoding="utf-8", closefd=True) as handle:
            handle.write(text)
            handle.flush()
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def write_topic_axis_outputs(
    kb_dir: Path,
    inventory: list[dict[str, Any]],
    plan: dict[str, Any],
    index: dict[str, Any],
    affected: dict[str, Any],
    *,
    run_id: str,
    conflicts: list[dict[str, Any]] | None = None,
    examples: list[dict[str, Any]] | None = None,
    gazetteer: dict[str, Any] | None = None,
    knowledge_type_registry: dict[str, Any] | None = None,
) -> Path:
    """Atomically write the four Task1 audit projections and nothing else."""
    from .kb_structure import validate_topic_index

    index = validate_topic_index(index)
    digest = kb_dir / "_digest"
    inventory_text = "".join(_json(row) + "\n" for row in sorted(inventory, key=lambda row: (row["source_uri"], row["content_path"])))
    _atomic_text(digest / "source-inventory.jsonl", inventory_text)
    _atomic_text(digest / "topic-plan.json", json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    _atomic_text(digest / "topic-index.json", json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    hashes = {
        "source_inventory": hashlib.sha256(inventory_text.encode("utf-8")).hexdigest(),
        "topic_plan": hashlib.sha256((json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")).hexdigest(),
        "topic_index": hashlib.sha256((json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")).hexdigest(),
    }
    report = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "delivery_status": "not_released",
        "task": "task1-knowledge-publication-topic-axis",
        "provider_boundary": "before_provider",
        "source_count": len(inventory),
        "affected_set": affected,
        "conflicts": list(conflicts or []),
        "examples": list(examples or []),
        "artifacts": {
            "source_inventory": "_digest/source-inventory.jsonl",
            "topic_plan": "_digest/topic-plan.json",
            "topic_index": "_digest/topic-index.json",
        },
        "artifact_sha256": hashes,
        "reader_package_changed": False,
        "gazetteer_generated": bool(gazetteer),
        "gazetteer_entry_count": len((gazetteer or {}).get("entries", [])),
        "knowledge_type_registry_entry_count": len((knowledge_type_registry or {}).get("entries", [])),
    }
    report_path = digest / "runs" / f"{run_id}.json"
    _atomic_text(report_path, json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return report_path


def topic_axis_plan(
    paths: DigestPaths,
    *,
    rebuild: bool = False,
    gazetteer: dict[str, Any] | None = None,
    old_topic_index: dict[str, Any] | None = None,
    previous_inventory: list[dict[str, Any]] | None = None,
    previous_plan: dict[str, Any] | None = None,
    topic_root: str | None = None,
) -> dict[str, Any]:
    """Compute the frozen Task1 plan; callers may persist it explicitly."""
    settings = read_topic_axis_settings(paths.structure_path)
    topic_root = topic_root or settings.get("topic_root")
    reserved = set(parse_roots(paths.structure_path))
    if topic_root:
        reserved.update(Path(topic_root).parts)
    inventory = build_source_inventory(paths)
    knowledge_type_registry = load_knowledge_type_registry(paths.structure_path)
    registry_generated = False
    if not knowledge_type_registry["entries"]:
        knowledge_type_registry = build_knowledge_type_registry(inventory)
        registry_generated = True
    gazetteer_generated = False
    if any(_knowledge_type(row) == "products" for row in inventory):
        if gazetteer is None:
            gazetteer = load_product_gazetteer(paths.structure_path)
            if not gazetteer["entries"]:
                gazetteer = build_source_product_gazetteer(inventory)
                gazetteer_generated = True
    else:
        gazetteer = {
            "schema_version": TOPIC_AXIS_SCHEMA_VERSION,
            "owner": None,
            "match_order": list(MATCH_ORDER),
            "entries": [],
        }
    plan = build_topic_plan(inventory, gazetteer, topic_root=topic_root, reserved=reserved)
    examples = build_topic_examples(inventory, gazetteer, topic_root=topic_root, include_failure_matrix=False, reserved=reserved)
    index = topic_index_from_plan(plan, old_topic_index=old_topic_index)
    affected = affected_set(
        inventory,
        plan,
        previous_inventory=previous_inventory,
        previous_plan=previous_plan,
        current_index=index,
        previous_index=old_topic_index,
        rebuild=rebuild,
    )
    return {
        "inventory": inventory,
        "knowledge_type_registry": knowledge_type_registry,
        "registry_generated": registry_generated,
        "gazetteer": _gazetteer_defaults(gazetteer),
        "gazetteer_generated": gazetteer_generated,
        "topic_plan": plan,
        "topic_index": index,
        "affected_set": affected,
        "examples": examples,
    }


def _read_previous_inventory(path: Path) -> list[dict[str, Any]] | None:
    if not path.is_file():
        return None
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("topic-axis", path, f"cannot read previous SourceInventory ({error})") from error
    if not all(isinstance(row, dict) for row in rows):
        raise ValidationError("topic-axis", path, "previous SourceInventory must contain JSON objects")
    return rows


def _read_previous_plan(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("topic-axis", path, f"cannot read previous TopicPlan ({error})") from error
    if not isinstance(value, dict):
        raise ValidationError("topic-axis", path, "previous TopicPlan must be a JSON object")
    return value


def _read_override_manifest(kb_dir: Path, configured_path: str | None) -> list[dict[str, Any]] | None:
    if not configured_path:
        return None
    candidate = Path(configured_path)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValidationError("topic-axis", configured_path, "override manifest path must stay inside the knowledge base")
    path = kb_dir / candidate
    if path.is_symlink() or not path.is_file():
        raise ValidationError("topic-axis", path, "declared override manifest is missing or a symlink")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("topic-axis", path, f"cannot read override manifest ({error})") from error
    if not isinstance(value, list):
        raise ValidationError("topic-axis", path, "override manifest must be a JSON array")
    return value


def run_topic_axis(
    paths: DigestPaths,
    *,
    rebuild: bool = False,
    run_id: str | None = None,
    topic_root: str | None = None,
    override_manifest: list[dict[str, Any]] | None = None,
) -> tuple[Path, str]:
    from .kb_structure import validate_topic_index

    old_index_path = paths.kb_dir / "_digest" / "topic-index.json"
    old_index = None
    if old_index_path.is_file():
        try:
            old_index = validate_topic_index(json.loads(old_index_path.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValidationError("topic-axis", old_index_path, f"cannot read old TopicIndex ({error})") from error
    digest_dir = paths.kb_dir / "_digest"
    previous_inventory = _read_previous_inventory(digest_dir / "source-inventory.jsonl")
    previous_plan = _read_previous_plan(digest_dir / "topic-plan.json")
    settings = read_topic_axis_settings(paths.structure_path)
    if override_manifest is not None and settings.get("override_manifest"):
        raise ValidationError("topic-axis", paths.structure_path, "override manifest must be supplied either by declaration or API, not both")
    effective_override_manifest = override_manifest or _read_override_manifest(paths.kb_dir, settings.get("override_manifest"))
    result = topic_axis_plan(
        paths,
        rebuild=rebuild,
        old_topic_index=old_index,
        previous_inventory=previous_inventory,
        previous_plan=previous_plan,
        topic_root=topic_root,
    )
    if result["registry_generated"]:
        write_knowledge_type_registry(paths.structure_path, result["knowledge_type_registry"])
    if result["gazetteer_generated"]:
        write_product_gazetteer(paths.structure_path, result["gazetteer"])
    run_id = run_id or f"run-topic-axis-{hashlib.sha256(_json(result['topic_plan']).encode()).hexdigest()[:16]}"
    conflicts = find_managed_conflicts(paths.kb_dir, result["topic_plan"], run_id=run_id, override_manifest=effective_override_manifest)
    report_path = write_topic_axis_outputs(
        paths.kb_dir,
        result["inventory"],
        result["topic_plan"],
        result["topic_index"],
        result["affected_set"],
        run_id=run_id,
        conflicts=conflicts,
        examples=result["examples"],
        gazetteer=result["gazetteer"] if result["gazetteer_generated"] else None,
        knowledge_type_registry=result["knowledge_type_registry"],
    )
    if any(row["code"] == "MANAGED_CONTENT_CONFLICT" for row in conflicts):
        raise ValidationError("topic-axis", report_path, "MANAGED_CONTENT_CONFLICT; preserved manual content")
    return report_path, f"task1 topic axis: inventoried {len(result['inventory'])} source(s); planned {len(result['topic_plan']['topics'])} topic(s); not_released"
