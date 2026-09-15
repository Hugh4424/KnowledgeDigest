"""Deterministic navigation graph checks for the Task8 compiler."""

from __future__ import annotations

from collections import Counter
from collections import deque
from dataclasses import dataclass, field
import hashlib
import inspect
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence
import unicodedata
import urllib.request

import yaml

from .llm import OPENAI_FORMAT, _endpoint as _llm_endpoint, _request_in_child as _llm_request_in_child, _request_payload as _llm_request_payload
from .semantic_page import PAGE_FRONTMATTER_FIELDS
from .semantic_compiler import configured_provider_from_env


# Labels may contain bracketed product markers such as ``[AE]``. Parse the
# target separately and allow the label to contain ordinary brackets.
WIKILINK_RE = re.compile(r"\[\[([^\]|#\n]+)(?:#[^\]|#\n]+)?(?:\|[^\n]*?)?\]\]")


def _provider_usage_tokens(value: object) -> int | None:
    if not isinstance(value, Mapping):
        return None
    total = value.get("total_tokens")
    if isinstance(total, int) and not isinstance(total, bool) and total >= 0:
        return total
    prompt_tokens = value.get("prompt_tokens")
    completion_tokens = value.get("completion_tokens")
    if all(isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in (prompt_tokens, completion_tokens)):
        return int(prompt_tokens) + int(completion_tokens)
    for key in ("tokens", "total", "completion"):
        candidate = value.get(key)
        if isinstance(candidate, int) and not isinstance(candidate, bool) and candidate >= 0:
            return candidate
    return None


def _normalize_link(value: str) -> str:
    target = value.strip().replace("\\", "/")
    if not target.endswith(".md"):
        target += ".md"
    return target


def parse_wikilinks(text: str) -> tuple[str, ...]:
    """Return normalized wikilink targets in source order, without duplicates."""

    result: list[str] = []
    for raw_target in WIKILINK_RE.findall(text):
        target = _normalize_link(raw_target)
        if target not in result:
            result.append(target)
    return tuple(result)


def check_coverage_three(
    *,
    page_paths: Sequence[str],
    documents: Mapping[str, str],
) -> tuple[str, ...]:
    """Check page coverage, target existence, and manifest boundary by BFS."""

    pages = {_normalize_link(path) for path in page_paths}
    normalized_documents = {_normalize_link(path): text for path, text in documents.items()}
    nodes = set(normalized_documents) | pages
    graph = {path: parse_wikilinks(text) for path, text in normalized_documents.items()}
    reasons: set[str] = set()
    queue: deque[str] = deque(["Home.md"] if "Home.md" in nodes else [])
    visited: set[str] = set()
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        for target in graph.get(current, ()):
            if target not in nodes:
                reasons.add(f"coverage-dead-link:{target}")
                continue
            queue.append(target)
    for path in sorted(pages - visited):
        reasons.add(f"coverage-orphan:{path}")
    for path in sorted(visited):
        if path.startswith("products/") and not path.endswith("/Index.md") and path not in pages:
            reasons.add(f"coverage-outside-manifest:{path}")
    return tuple(sorted(reasons))


def _normalized_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _description_skeleton(value: str, metadata: Mapping[str, object]) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    for field in ("title", "product", "section"):
        token = metadata.get(field)
        if isinstance(token, str) and token:
            normalized = normalized.replace(unicodedata.normalize("NFKC", token).casefold(), "")
    return "".join(character for character in normalized if character.isalnum())


def check_description_criteria(
    *,
    descriptions: Mapping[str, str],
    page_metadata: Mapping[str, Mapping[str, object]],
) -> tuple[str, ...]:
    """Return every violated frozen description distinctness criterion."""

    reasons: set[str] = set()
    for path, description in descriptions.items():
        if not isinstance(description, str) or not description.strip():
            reasons.add(f"description-empty:{path}")

    normalized = {path: _normalized_text(value) for path, value in descriptions.items() if isinstance(value, str)}
    for value, paths in _groups(normalized).items():
        if value and len(paths) > 1:
            reasons.add(f"description-exact-duplicate:{','.join(paths)}")

    skeletons = {
        path: _description_skeleton(value, page_metadata.get(path, {}))
        for path, value in descriptions.items()
        if isinstance(value, str) and value.strip()
    }
    for value, paths in _groups(skeletons).items():
        if value and len(paths) >= 3:
            reasons.add(f"description-skeleton-duplicate:{','.join(paths)}")

    templates: Counter[str] = Counter()
    for value in normalized.values():
        for prefix in ("如何", "什么是", "怎么", "怎样", "哪里", "在哪"):
            if value.startswith(prefix):
                templates[prefix] += 1
                break
    for template, count in templates.items():
        if count >= 3:
            reasons.add(f"description-question-template:{template}")
    if sum(templates.values()) >= 3:
        reasons.add("description-question-template:aggregate")
    return tuple(sorted(reasons))


@dataclass(frozen=True)
class QueryPathResult:
    status: str
    checked: int
    reasons: tuple[str, ...]


def check_query_paths(
    *,
    documents: Mapping[str, str],
    page_paths: Sequence[str],
    query_fixture: str | Path | None,
) -> QueryPathResult:
    """Check the frozen query set against shortest navigation paths."""

    if query_fixture is None:
        return QueryPathResult("incomplete", 0, ("query-fixture-missing",))
    try:
        payload = json.loads(Path(query_fixture).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return QueryPathResult("blocked", 0, ("query-fixture-invalid",))
    if not isinstance(payload, dict) or payload.get("schema_version") != "task8-query-paths.v1":
        return QueryPathResult("blocked", 0, ("query-fixture-schema-invalid",))
    queries = payload.get("queries")
    if not isinstance(queries, list) or len(queries) != 10:
        count = len(queries) if isinstance(queries, list) else "invalid"
        return QueryPathResult("blocked", 0, (f"query-count-invalid:{count}",))
    if payload.get("status") != "frozen":
        return QueryPathResult("blocked", 0, ("query-fixture-not-frozen",))
    malformed = [
        row for row in queries
        if not isinstance(row, dict)
        or not isinstance(row.get("id"), str) or not row.get("id").strip()
        or not isinstance(row.get("query"), str) or not row.get("query").strip()
    ]
    if malformed:
        return QueryPathResult("blocked", 0, ("query-fixture-row-invalid",))
    missing_targets = tuple(
        f"query-target-slug-missing:{row['id']}"
        for row in queries
        if not isinstance(row.get("target_slug"), str) or not row.get("target_slug").strip()
    )
    if missing_targets:
        return QueryPathResult("incomplete", 0, missing_targets)

    pages = {_normalize_link(path) for path in page_paths}
    normalized_documents = {_normalize_link(path): text for path, text in documents.items()}
    nodes = set(normalized_documents) | pages
    graph = {path: parse_wikilinks(text) for path, text in normalized_documents.items()}
    distances: dict[str, int] = {"Home.md": 0}
    queue: deque[str] = deque(["Home.md"] if "Home.md" in nodes else [])
    while queue:
        current = queue.popleft()
        for target in graph.get(current, ()):
            if target in nodes and target not in distances:
                distances[target] = distances[current] + 1
                queue.append(target)

    reasons: list[str] = []
    for row in queries:
        target_slug = _normalize_link(str(row["target_slug"]))
        candidates = sorted(path for path in pages if path == target_slug)
        if not candidates:
            basename_candidates = sorted(
                path for path in pages if PurePosixPath(path).stem == PurePosixPath(target_slug).stem
            )
            if len(basename_candidates) == 1:
                candidates = basename_candidates
            elif len(basename_candidates) > 1:
                reasons.append(f"query-target-ambiguous:{row['id']}:{target_slug}")
                continue
        if not candidates:
            reasons.append(f"query-target-missing:{row['id']}:{target_slug}")
            continue
        distance = distances.get(candidates[0])
        if distance is None:
            reasons.append(f"query-target-unreachable:{row['id']}:{target_slug}")
        elif distance > 3:
            reasons.append(f"query-path-too-long:{row['id']}:{distance}")
    return QueryPathResult("blocked" if reasons else "passed", len(queries), tuple(sorted(set(reasons))))


def _groups(values: Mapping[str, str]) -> Mapping[str, tuple[str, ...]]:
    grouped: dict[str, list[str]] = {}
    for path, value in values.items():
        grouped.setdefault(value, []).append(path)
    return {value: tuple(sorted(paths)) for value, paths in grouped.items()}


__all__ = ["QueryPathResult", "check_coverage_three", "check_description_criteria", "check_query_paths", "parse_wikilinks", "validate_description_output"]


MANIFEST_SCHEMA_VERSION = "task7-page-manifest.v1"
NAVIGATION_GENERATED_BY = "knowledge_digest_semantic_navigation.py"
REJECTION_WORDS = frozenset({"最佳", "推荐", "最强", "完美", "绝对", "领先"})
REQUIRED_MANIFEST_FIELDS = (
    "schema_version",
    "publish_status",
    "run_status",
    "attempt_id",
    "source_snapshot",
    "blockers",
    "pages",
    "source_to_pages",
    "source_ledger",
)
REQUIRED_PAGE_FIELDS = ("topic_key", "page_path", "page_paths")
REQUIRED_PAGE_FRONTMATTER_FIELDS = ("title", "product", "section")


def _safe_segment(value: object, *, field: str) -> str:
    """Validate one frontmatter value before using it as a directory name."""

    if not isinstance(value, str) or not value.strip():
        raise NavigationInputError(f"{field}-missing", f"{field} must be a non-empty path segment")
    segment = value.strip()
    if segment in {".", ".."} or "/" in segment or "\\" in segment or "\x00" in segment:
        raise NavigationInputError(
            "nav-frontmatter-path-invalid",
            f"{field} must be a safe single path segment: {value!r}",
        )
    return segment


def _validate_batch_layout(batch_dir: Path) -> Path:
    """Reject symlinked batch roots and write-critical parent directories."""

    if batch_dir.is_symlink() or not batch_dir.is_dir():
        raise NavigationInputError("batch-path-invalid", "batch directory must be a real directory")
    batch = batch_dir.resolve()
    for name in ("_audit", "products"):
        path = batch_dir / name
        if path.is_symlink():
            raise NavigationInputError("batch-path-symlink", f"batch {name} directory must not be a symlink")
        if path.exists() and not path.is_dir():
            raise NavigationInputError("batch-path-invalid", f"batch {name} path must be a directory")
    for root_name in ("_audit", "products"):
        root = batch_dir / root_name
        if root.is_dir():
            for child in root.rglob("*"):
                if child.is_symlink():
                    raise NavigationInputError("batch-path-symlink", f"batch path must not traverse a symlink: {child}")
    return batch


def _safe_batch_path(batch_dir: Path, relative_path: str, *, field: str) -> Path:
    """Resolve a batch-relative path while rejecting symlink traversal."""

    batch = _validate_batch_layout(batch_dir)
    normalized = _relative_path(relative_path, field=field)
    candidate = batch_dir / normalized
    current = batch_dir
    for part in PurePosixPath(normalized).parts:
        current = current / part
        if current.is_symlink():
            raise NavigationInputError("batch-path-symlink", f"{field} must not traverse a symlink: {normalized}")
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        raise NavigationInputError("batch-path-invalid", f"cannot resolve {field}: {normalized}") from exc
    if not resolved.is_relative_to(batch):
        raise NavigationInputError("{0}-escape".format(field), f"{field} must stay inside the batch: {normalized!r}")
    return candidate


class NavigationInputError(ValueError):
    """A batch cannot be safely used as navigation input."""

    def __init__(self, reason: str, message: str | None = None) -> None:
        self.reason = reason
        super().__init__(message or reason)


@dataclass(frozen=True)
class NavigationResult:
    navigation_status: str
    success_pages: int
    blocked_sources: int
    blocked_reasons: tuple[str, ...]
    nav_files: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "navigation_status": self.navigation_status,
            "success_pages": self.success_pages,
            "blocked_sources": self.blocked_sources,
            "blocked_reasons": list(self.blocked_reasons),
            "nav_files": list(self.nav_files),
        }


@dataclass(frozen=True)
class NavigationDependencies:
    cache: Any
    gateway: Any
    query_fixture: Path | None


@dataclass(frozen=True)
class ConfiguredNavigationGateway:
    provider: Any
    model_id: str
    prompt_version: str = "task8-navigation-v1"
    topic_map_version: str = "task8-topic-map-v1"

    def _complete_configured(self, prompt: str) -> Mapping[str, Any]:
        if len(prompt) > self.provider.max_input_chars:
            raise NavigationInputError("provider-config-invalid", "navigation prompt exceeds configured limit")
        if self.provider.api_format not in ("openai", "anthropic") or not self.provider.base_url or not self.provider.model or not self.provider.api_key:
            raise NavigationInputError("provider-config-invalid", "provider configuration is incomplete")
        kind = "suggestions" if prompt.startswith("task8 home suggestions") else "description"
        shape = '{"suggestions":["..."]}' if kind == "suggestions" else '{"description":"..."}'
        task8_prompt = (
            "Task8 navigation generation. Return ONLY one JSON object with this exact shape: "
            f"{shape}\\nDo not include markdown fences or extra keys.\\n{prompt}"
        )
        request_body = _llm_request_payload(
            self.provider.api_format,
            self.provider.model,
            task8_prompt,
            max_tokens=self.provider.max_tokens,
            json_mode=True,
        )
        headers = {"content-type": "application/json"}
        if self.provider.api_format == OPENAI_FORMAT:
            headers["authorization"] = f"Bearer {self.provider.api_key}"
        else:
            headers["x-api-key"] = self.provider.api_key
            headers["anthropic-version"] = "2023-06-01"
        request = urllib.request.Request(
            _llm_endpoint(self.provider.base_url, self.provider.api_format),
            data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            envelope = json.loads(_llm_request_in_child(request, timeout=self.provider.timeout))
            content = envelope["choices"][0]["message"]["content"] if self.provider.api_format == OPENAI_FORMAT else envelope["content"][0]["text"]
            result = json.loads(str(content))
        except Exception as error:
            raise NavigationInputError("provider-output-invalid", f"provider returned invalid navigation JSON ({type(error).__name__}: {error})") from error
        if not isinstance(result, Mapping):
            raise NavigationInputError("provider-output-invalid", "navigation provider result must be an object")
        tokens = _provider_usage_tokens(envelope.get("usage", {}))
        if tokens is None:
            raise NavigationInputError("provider-usage-unavailable", "provider response did not include usage tokens")
        return {**dict(result), "provider_tokens": tokens}

    def complete(self, prompt: str) -> str:
        """Adapt an injected or configured provider to the Task8 text contract."""
        configured = all(hasattr(self.provider, name) for name in ("api_format", "base_url", "api_key", "model", "timeout", "max_tokens", "max_input_chars"))
        complete = self._complete_configured if configured else getattr(self.provider, "complete", None)
        if not callable(complete):
            raise NavigationInputError("model-output-invalid", "configured provider is not callable")
        result = complete(prompt)
        if isinstance(result, str):
            return result
        if not isinstance(result, Mapping):
            raise NavigationInputError("model-output-invalid", "configured provider output is not an object")
        if not any(key in result for key in ("description", "text", "content", "suggestions", "intro")):
            raise NavigationInputError("model-output-invalid", "configured provider output has no navigation text")
        token_value = result.get("provider_tokens")
        if not isinstance(token_value, int) or isinstance(token_value, bool) or token_value < 0:
            raise NavigationInputError("provider-usage-unavailable", "configured navigation output has no valid token count")
        for key in ("description", "text", "content"):
            value = result.get(key)
            if isinstance(value, str):
                return value
        suggestions = result.get("suggestions")
        if isinstance(suggestions, (list, tuple)):
            return json.dumps(list(suggestions), ensure_ascii=False)
        intro = result.get("intro")
        if isinstance(intro, str):
            return intro
        if isinstance(intro, (list, tuple)):
            return json.dumps(list(intro), ensure_ascii=False)
        raise NavigationInputError("model-output-invalid", "configured provider output has no navigation text")


@dataclass(frozen=True)
class UnavailableNavigationGateway:
    """A dependency-safe gateway that makes missing configuration fail closed."""

    reason: str = "provider-config-missing"
    model_id: str = "unconfigured-navigation-model"
    prompt_version: str = "task8-navigation-v1"
    topic_map_version: str = "task8-topic-map-v1"

    def complete(self, prompt: str) -> str:
        raise NavigationInputError(self.reason, "navigation provider configuration is missing")


class JsonlNavigationCache:
    """Task8 cache adapter using the K1 JSONL entry shape and key namespace."""

    def __init__(self, root: str | Path, *, model_id: str, prompt_version: str, topic_map_version: str) -> None:
        self.root = Path(root)
        if self.root.exists() and (self.root.is_symlink() or not self.root.is_dir()):
            raise NavigationInputError("cache-root-invalid", "navigation cache root is not a real directory")
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink() or not self.root.is_dir():
            raise NavigationInputError("cache-root-invalid", "navigation cache root is not a directory")
        self.model_id = model_id
        self.prompt_version = prompt_version
        self.topic_map_version = topic_map_version

    @property
    def path(self) -> Path:
        path = self.root / "entries.jsonl"
        if path.is_symlink():
            raise NavigationInputError("cache-root-invalid", "navigation cache entries must not be a symlink")
        return path

    def get(self, key: str, *, expected_fingerprint: str | None = None) -> str | None:
        if not self.path.exists():
            return None
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise NavigationInputError("cache-invalid", "navigation cache cannot be read") from exc
        found: str | None = None
        for line in lines:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise NavigationInputError("cache-invalid", "navigation cache contains invalid JSON") from exc
            if not isinstance(entry, dict) or entry.get("cache_key") != key:
                continue
            if any(
                entry.get(field) != expected
                for field, expected in (
                    ("model_id", self.model_id),
                    ("prompt_version", self.prompt_version),
                    ("topic_map_version", self.topic_map_version),
                )
            ):
                raise NavigationInputError("cache-invalid", "navigation cache identity does not match the requested key")
            if not isinstance(entry.get("created_from_fingerprint"), str) or not entry["created_from_fingerprint"]:
                raise NavigationInputError("cache-invalid", "navigation cache fingerprint is missing")
            if expected_fingerprint is not None and entry["created_from_fingerprint"] != expected_fingerprint:
                raise NavigationInputError("cache-invalid", "navigation cache fingerprint does not match requested input")
            result = entry.get("result")
            if not isinstance(result, str):
                raise NavigationInputError("cache-output-invalid", "navigation cache result must be a string")
            if found is not None and found != result:
                raise NavigationInputError("cache-invalid", "navigation cache has conflicting results for one key")
            found = result
        return found

    def set(self, key: str, value: str) -> None:
        self._set(key, value, key.split(":", 1)[-1])

    def set_with_fingerprint(self, key: str, value: str, *, fingerprint: str) -> None:
        self._set(key, value, fingerprint)

    def _set(self, key: str, value: str, fingerprint: str) -> None:
        if not isinstance(key, str) or not key or not isinstance(value, str):
            raise TypeError("navigation cache key and value must be strings")
        if not isinstance(fingerprint, str) or not fingerprint:
            raise TypeError("navigation cache fingerprint must be a non-empty string")
        entry = {
            "cache_key": key,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "topic_map_version": self.topic_map_version,
            "result": value,
            "created_from_fingerprint": fingerprint,
        }
        try:
            with self.path.open("a", encoding="utf-8", newline="") as stream:
                stream.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            raise NavigationInputError("cache-write-failed", "navigation cache cannot be written") from exc


@dataclass(frozen=True)
class ReconciledPage:
    """One manifest page entry after filesystem and frontmatter reconciliation."""

    topic_key: str
    page_path: str
    page_paths: tuple[str, ...]
    source_paths: tuple[str, ...]
    frontmatter: Mapping[str, Any]
    text: str

    @property
    def title(self) -> str:
        return str(self.frontmatter["title"])

    @property
    def product(self) -> str:
        return str(self.frontmatter["product"])

    @property
    def section(self) -> str:
        return str(self.frontmatter["section"])


@dataclass(frozen=True)
class MountEntry:
    page: ReconciledPage
    wikilink: str
    description: str | None = None
    physical_path: str | None = None

    @property
    def target_path(self) -> str:
        return self.physical_path or self.page.page_path


@dataclass(frozen=True)
class NavigationDocument:
    relative_path: str
    frontmatter: Mapping[str, Any]
    body: str

    @property
    def text(self) -> str:
        return _render_frontmatter(self.frontmatter) + "\n\n" + self.body.rstrip() + "\n"


def _relative_path(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NavigationInputError(f"{field}-missing", f"{field} must be a non-empty relative path")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise NavigationInputError(f"{field}-escape", f"{field} must stay inside the batch: {value!r}")
    return path.as_posix()


def _read_manifest(batch_dir: Path) -> Mapping[str, Any]:
    _validate_batch_layout(batch_dir)
    manifest_path = _safe_batch_path(batch_dir, "_audit/page-manifest.json", field="manifest-path")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NavigationInputError("manifest-missing", "page-manifest.json is missing") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NavigationInputError("manifest-invalid", "page-manifest.json is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise NavigationInputError("manifest-invalid", "page-manifest.json must contain an object")
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in payload:
            raise NavigationInputError(f"missing-manifest-field:{field}", f"manifest missing {field}")
    if payload["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise NavigationInputError("manifest-schema-mismatch", "unsupported page-manifest schema")
    if payload.get("run_status") not in {"complete", "blocked", "interrupted"}:
        raise NavigationInputError("manifest-run-status-invalid", "manifest run_status is invalid")
    if payload.get("publish_status") not in {"not_released", "released"}:
        raise NavigationInputError("manifest-publish-status-invalid", "manifest publish_status is invalid")
    if not isinstance(payload.get("blockers"), list):
        raise NavigationInputError("manifest-blockers-invalid", "manifest blockers must be an array")
    if not isinstance(payload.get("source_to_pages"), dict):
        raise NavigationInputError("manifest-source-to-pages-invalid", "manifest source_to_pages must be an object")
    if not isinstance(payload.get("source_ledger"), list):
        raise NavigationInputError("manifest-source-ledger-invalid", "manifest source_ledger must be an array")
    if not isinstance(payload["pages"], list):
        raise NavigationInputError("pages-not-list", "manifest pages must be an array")
    return MappingProxyType(payload)


def load_and_validate(batch_dir: str | Path) -> Mapping[str, Any]:
    """Load the K1 manifest and validate its stable top-level contract."""

    batch = Path(batch_dir)
    _validate_batch_layout(batch)
    return _read_manifest(batch)


def _read_frontmatter(path: Path) -> tuple[Mapping[str, Any], str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise NavigationInputError("page-unreadable", f"cannot read page {path}") from exc
    if not text.startswith("---\n"):
        raise NavigationInputError("nav-frontmatter-incomplete", f"page has no frontmatter: {path}")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise NavigationInputError("nav-frontmatter-incomplete", f"page frontmatter is not closed: {path}")
    try:
        frontmatter = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        raise NavigationInputError("nav-frontmatter-invalid", f"page frontmatter is invalid: {path}") from exc
    if not isinstance(frontmatter, dict):
        raise NavigationInputError("nav-frontmatter-incomplete", f"page frontmatter is not an object: {path}")
    for field in REQUIRED_PAGE_FRONTMATTER_FIELDS:
        if field not in frontmatter or not isinstance(frontmatter[field], str) or not frontmatter[field].strip():
            raise NavigationInputError(
                "nav-frontmatter-incomplete",
                f"page frontmatter missing {field}: {path}",
            )
    return MappingProxyType(frontmatter), text


def _manifest_page_paths(row: Mapping[str, Any]) -> tuple[str, ...]:
    for field in REQUIRED_PAGE_FIELDS:
        if field not in row:
            raise NavigationInputError(f"page-field-missing:{field}", f"manifest page missing {field}")
    page_path = _relative_path(row["page_path"], field="page_path")
    raw_paths = row["page_paths"]
    if not isinstance(raw_paths, list) or not raw_paths:
        raise NavigationInputError("page-paths-invalid", "manifest page_paths must be a non-empty array")
    page_paths = tuple(_relative_path(value, field="page_path") for value in raw_paths)
    if page_path != page_paths[0] or len(set(page_paths)) != len(page_paths):
        raise NavigationInputError("page-paths-inconsistent", "page_path must be the first unique page_paths entry")
    if any(not value.startswith("products/") or not value.endswith(".md") for value in page_paths):
        raise NavigationInputError("page-path-outside-products", "navigation pages must be products/*.md")
    if any(PurePosixPath(value).name == "Index.md" for value in page_paths):
        raise NavigationInputError("nav-index-name-conflict", "Index.md is reserved for navigation")
    return page_paths


def reconcile_pages(batch_dir: str | Path) -> tuple[ReconciledPage, ...]:
    """Reconcile manifest page entries with every emitted products page."""

    batch = Path(batch_dir)
    manifest = _read_manifest(batch)
    rows: list[tuple[Mapping[str, Any], tuple[str, ...]]] = []
    declared_paths: dict[str, str] = {}
    for raw_row in manifest["pages"]:
        if not isinstance(raw_row, dict):
            raise NavigationInputError("page-entry-invalid", "manifest pages must contain objects")
        page_paths = _manifest_page_paths(raw_row)
        topic_key = raw_row["topic_key"]
        if not isinstance(topic_key, str) or not topic_key.strip():
            raise NavigationInputError("page-topic-key-missing", "manifest page topic_key must be non-empty")
        for page_path in page_paths:
            previous = declared_paths.setdefault(page_path, topic_key)
            if previous != topic_key:
                raise NavigationInputError("page-path-duplicate", f"page path belongs to multiple topics: {page_path}")
        rows.append((MappingProxyType(raw_row), page_paths))

    emitted_paths = set()
    products_root = batch / "products"
    for path in products_root.rglob("*.md"):
        if path.is_symlink() or not path.resolve().is_relative_to(batch.resolve()):
            raise NavigationInputError("page-path-symlink", f"products page must stay inside the batch: {path}")
        if path.is_file() and path.name != "Index.md":
            emitted_paths.add(path.relative_to(batch).as_posix())
    declared_set = set(declared_paths)
    missing_files = sorted(declared_set - emitted_paths)
    undeclared_files = sorted(emitted_paths - declared_set)
    if missing_files:
        raise NavigationInputError("manifest-page-file-missing", f"manifest page file missing: {missing_files[0]}")
    if undeclared_files:
        raise NavigationInputError("products-page-undeclared", f"products page is not in manifest: {undeclared_files[0]}")

    reconciled: list[ReconciledPage] = []
    for row, page_paths in rows:
        first_path = batch / page_paths[0]
        if first_path.is_symlink() or not first_path.resolve().is_relative_to(batch.resolve()):
            raise NavigationInputError("page-path-symlink", f"page path must stay inside the batch: {page_paths[0]}")
        for physical_path in page_paths:
            candidate = batch / physical_path
            if candidate.is_symlink() or not candidate.resolve().is_relative_to(batch.resolve()):
                raise NavigationInputError("page-path-symlink", f"page path must stay inside the batch: {physical_path}")
        frontmatter, text = _read_frontmatter(first_path)
        for field in ("product", "section"):
            _safe_segment(frontmatter[field], field=field)
        source_paths = tuple(
            sorted(_relative_path(value, field="source_path") for value in row.get("source_paths", []))
        )
        reconciled.append(
            ReconciledPage(
                topic_key=str(row["topic_key"]),
                page_path=page_paths[0],
                page_paths=page_paths,
                source_paths=source_paths,
                frontmatter=frontmatter,
                text=text,
            )
        )
    return tuple(sorted(reconciled, key=lambda page: page.page_path))


def build_mount_tree(
    pages: Sequence[ReconciledPage],
) -> dict[str, dict[str, tuple[MountEntry, ...]]]:
    """Build the deterministic product/section mount tree for navigation."""

    grouped: dict[str, dict[str, list[MountEntry]]] = {}
    ordered_pages = sorted(pages, key=lambda page: (page.product, page.section, page.page_path))
    for page in ordered_pages:
        for physical_path in page.page_paths:
            grouped.setdefault(page.product, {}).setdefault(page.section, []).append(
                MountEntry(
                    page=page,
                    physical_path=physical_path,
                    wikilink=f"[[{physical_path.removesuffix('.md')}|{page.title}]]",
                )
            )
    return {
        product: {
            section: tuple(entries)
            for section, entries in sorted(sections.items())
        }
        for product, sections in sorted(grouped.items())
    }


def build_navigation_frontmatter(
    *,
    title: str,
    product: str,
    section: str,
    module: str,
    tier: int,
    created: str,
    updated: str,
) -> Mapping[str, Any]:
    """Return the exact Task7-shaped frontmatter for a navigation page."""

    if tier not in {1, 2}:
        raise ValueError("navigation tier must be 1 or 2")
    values: dict[str, Any] = {
        "title": title,
        "type": "reference",
        "page_model": "derived",
        "scope": "company",
        "product": product,
        "section": section,
        "module": module,
        "tier": tier,
        "trust": "medium",
        "source_status": "compiled",
        "quality_status": "formal",
        "created": created,
        "updated": updated,
        "generated_by": NAVIGATION_GENERATED_BY,
        "tags": ["company", "navigation"],
        "source": "batch",
    }
    return MappingProxyType({field: values[field] for field in PAGE_FRONTMATTER_FIELDS})


def infer_module_title(titles: Sequence[str]) -> str:
    """Infer a stable module label from the tokens in its page titles."""

    title_values = (titles,) if isinstance(titles, str) else titles
    tokens: list[str] = []
    for title in title_values:
        current: list[str] = []
        for character in str(title):
            if character.isalnum():
                current.append(character)
            elif current:
                tokens.append("".join(current))
                current = []
        if current:
            tokens.append("".join(current))
    if not tokens:
        return "模块"
    counts = Counter(tokens)
    highest = max(counts.values())
    return min(token for token, count in counts.items() if count == highest)


def _frontmatter_value(value: object) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(_frontmatter_value(item) for item in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _render_frontmatter(frontmatter: Mapping[str, Any]) -> str:
    if tuple(frontmatter) != tuple(PAGE_FRONTMATTER_FIELDS):
        raise ValueError("navigation frontmatter must contain the exact Task7 16-field order")
    return "\n".join(
        ["---", *(f"{field}: {_frontmatter_value(frontmatter[field])}" for field in PAGE_FRONTMATTER_FIELDS), "---"]
    )


def _tree_entries(tree: Mapping[str, Mapping[str, Sequence[MountEntry]]]) -> tuple[MountEntry, ...]:
    return tuple(
        entry
        for product in sorted(tree)
        for section in sorted(tree[product])
        for entry in tree[product][section]
    )


def _tree_dates(tree: Mapping[str, Mapping[str, Sequence[MountEntry]]]) -> tuple[str, str]:
    entries = _tree_entries(tree)
    if not entries:
        raise ValueError("navigation cannot derive dates from an empty mount tree")
    created = [entry.page.frontmatter.get("created") for entry in entries]
    updated = [entry.page.frontmatter.get("updated") for entry in entries]
    if any(not isinstance(value, str) or not value.strip() for value in (*created, *updated)):
        raise NavigationInputError("nav-frontmatter-incomplete", "page dates are required for navigation")
    return min(created), max(updated)


def build_index(tree: Mapping[str, Mapping[str, Sequence[MountEntry]]]) -> NavigationDocument:
    """Render the global product/section index without model output."""

    created, updated = _tree_dates(tree)
    frontmatter = build_navigation_frontmatter(
        title="知识索引",
        product="navigation",
        section="navigation",
        module="navigation",
        tier=1,
        created=created,
        updated=updated,
    )
    lines = ["# 知识索引", ""]
    for product, sections in sorted(tree.items()):
        lines.extend((f"## {product}", ""))
        for section in sorted(sections):
            lines.append(f"- [[products/{product}/{section}/Index|{section}]]")
        lines.append("")
    return NavigationDocument(relative_path="Index.md", frontmatter=frontmatter, body="\n".join(lines).rstrip())


def build_module_indexes(
    tree: Mapping[str, Mapping[str, Sequence[MountEntry]]],
) -> dict[str, NavigationDocument]:
    """Render one deterministic module index per product/section mount."""

    created, updated = _tree_dates(tree)
    result: dict[str, NavigationDocument] = {}
    for product, sections in sorted(tree.items()):
        for section, entries in sorted(sections.items()):
            title = infer_module_title(tuple(entry.page.title for entry in entries))
            frontmatter = build_navigation_frontmatter(
                title=title,
                product=product,
                section=section,
                module=section,
                tier=2,
                created=created,
                updated=updated,
            )
            lines = [f"# {title}", "", "## 页面", ""]
            for entry in entries:
                lines.extend((f"- {entry.wikilink}", "  description: <!-- description:pending -->"))
            relative_path = f"products/{product}/{section}/Index.md"
            result[relative_path] = NavigationDocument(
                relative_path=relative_path,
                frontmatter=frontmatter,
                body="\n".join(lines).rstrip(),
            )
    return result


def build_home(
    tree: Mapping[str, Mapping[str, Sequence[MountEntry]]],
    *,
    success_pages: int,
    blocked_sources: int,
) -> NavigationDocument:
    """Render the deterministic Home sections and leave a model slot for P3."""

    created, updated = _tree_dates(tree)
    frontmatter = build_navigation_frontmatter(
        title="批次入口",
        product="navigation",
        section="navigation",
        module="navigation",
        tier=1,
        created=created,
        updated=updated,
    )
    lines = [
        "# 批次入口",
        "",
        f"nav: success_pages={success_pages} blocked_sources={blocked_sources}",
        "",
        "## 快速入口",
        "- [[Index|知识索引]]",
    ]
    lines.extend(f"- [[Index#{product}|{product}]]" for product in sorted(tree))
    lines.extend(
        (
            "",
            "## 查询建议",
            "<!-- query-suggestions:pending -->",
            "",
            "## 使用边界",
            "本目录为临时对照产物；正式入口归 K3。",
        )
    )
    return NavigationDocument(relative_path="Home.md", frontmatter=frontmatter, body="\n".join(lines).rstrip())


def build_navigation_cache_key(
    *,
    kind: str,
    input_bytes: bytes | str,
    model_id: str,
    prompt_version: str,
    topic_map_version: str,
) -> str:
    """Build the Task8 cache key from the five frozen identity components."""

    kind_values = {"description": ("page-desc", "task8-desc"), "suggestion": ("home-suggest", "task8-suggest")}
    try:
        task_id, prefix = kind_values[kind]
    except KeyError as exc:
        raise ValueError("navigation cache kind must be description or suggestion") from exc
    if isinstance(input_bytes, str):
        raw = input_bytes.encode("utf-8")
    elif isinstance(input_bytes, bytes):
        raw = input_bytes
    else:
        raise TypeError("navigation cache input_bytes must be bytes or str")
    values = (model_id, prompt_version, topic_map_version)
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError("navigation cache identity values must be non-empty strings")
    material = {
        "task": task_id,
        "input_fingerprint": hashlib.sha256(raw).hexdigest(),
        "model_id": model_id,
        "prompt_version": prompt_version,
        "topic_map_version": topic_map_version,
    }
    canonical = json.dumps(material, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return f"{prefix}:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def build_navigation_dependencies(
    *,
    cache_root: str | Path,
    provider_config_path: str | Path | None,
    query_fixture: str | Path | None,
) -> NavigationDependencies:
    """Construct production dependencies without making a provider request."""

    provider = configured_provider_from_env(provider_config_path)
    gateway = (
        ConfiguredNavigationGateway(provider=provider, model_id=provider.model)
        if provider is not None
        else UnavailableNavigationGateway()
    )
    cache = JsonlNavigationCache(
        cache_root,
        model_id=gateway.model_id,
        prompt_version=gateway.prompt_version,
        topic_map_version=gateway.topic_map_version,
    )
    fixture = Path(query_fixture) if query_fixture is not None else None
    return NavigationDependencies(cache=cache, gateway=gateway, query_fixture=fixture)


def resolve_cached_output(
    *,
    cache: Any,
    gateway: Any,
    cache_key: str,
    prompt: str,
    created_from_fingerprint: str | None = None,
    validator: Any | None = None,
) -> str:
    """Read a cached model result or make exactly one injected gateway call."""

    get = getattr(cache, "get")
    try:
        parameters = inspect.signature(get).parameters
    except (TypeError, ValueError):
        parameters = {}
    cached = get(cache_key, expected_fingerprint=created_from_fingerprint) if "expected_fingerprint" in parameters else get(cache_key)
    if cached is not None:
        if not isinstance(cached, str):
            raise TypeError("cached navigation output must be a string")
        if callable(validator):
            return validator(cached)
        return cached
    complete = getattr(gateway, "complete", None)
    if not callable(complete):
        if callable(gateway):
            complete = gateway
        else:
            raise TypeError("navigation gateway must expose complete() or be callable")
    output = complete(prompt)
    if not isinstance(output, str):
        raise TypeError("navigation gateway output must be a string")
    if callable(validator):
        output = validator(output)
    set_with_fingerprint = getattr(cache, "set_with_fingerprint", None)
    if created_from_fingerprint is not None and callable(set_with_fingerprint):
        set_with_fingerprint(cache_key, output, fingerprint=created_from_fingerprint)
    else:
        cache.set(cache_key, output)
    return output


def validate_model_output(value: str) -> str:
    """Validate the shared non-empty, non-promotional navigation text contract."""

    if not isinstance(value, str):
        raise NavigationInputError("model-output-invalid", "model output must be a string")
    normalized = value.strip()
    if not normalized:
        raise NavigationInputError("model-output-missing", "model output is empty")
    if any(word in normalized for word in REJECTION_WORDS):
        raise NavigationInputError("model-output-rejected", "model output contains a rejection word")
    return normalized


def validate_description_output(value: str) -> str:
    """Validate the frozen Chinese, single-line, declarative page description."""

    normalized = validate_model_output(value)
    if "\n" in normalized or "\r" in normalized:
        raise NavigationInputError("model-output-invalid", "description must be one line")
    if not any("\u4e00" <= character <= "\u9fff" for character in normalized):
        raise NavigationInputError("model-output-invalid", "description must contain Chinese text")
    if normalized.endswith(("？", "?")) or normalized.startswith(("如何", "什么是", "怎么", "怎样", "哪里", "在哪")):
        raise NavigationInputError("model-output-invalid", "description must be a declarative sentence")
    # Provider prose may contain multiple source-faithful clauses. The frozen
    # contract requires a declarative, non-question description, not a single
    # punctuation-delimited clause; retain the stronger empty/Chinese/question
    # checks above.
    return normalized


def validate_query_suggestions(values: Sequence[str]) -> tuple[str, ...]:
    """Validate the unbounded, non-empty Home suggestion list."""

    if isinstance(values, str) or not isinstance(values, Sequence):
        raise NavigationInputError("query-suggestions-missing", "query suggestions must be an array")
    if len(values) < 3:
        raise NavigationInputError("query-suggestions-missing", "at least three query suggestions are required")
    return tuple(validate_model_output(value) for value in values)


def _validate_suggestion_json(raw: str) -> str:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NavigationInputError("model-output-invalid", "query suggestions are not valid JSON") from exc
    validate_query_suggestions(value)
    return raw


def build_navigation_metrics(*, page_count: int, provider_calls: int, cache_hits: int) -> Mapping[str, int]:
    """Return the K2 cost projection without writing the batch metrics file."""

    values = (page_count, provider_calls, cache_hits)
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
        raise ValueError("navigation metrics counters must be non-negative integers")
    return MappingProxyType(
        {
            "planned_provider_calls": page_count + 1,
            "provider_calls": provider_calls,
            "cache_hits": cache_hits,
            "description_calls": page_count,
            "suggestion_calls": 1,
        }
    )


def _page_body_excerpt(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            text = text[end + len("\n---\n") :]
    return "\n".join(text.splitlines()[:30])


def _gateway_identity(gateway: Any) -> tuple[str, str, str]:
    model_id = getattr(gateway, "model_id", "injected-model")
    prompt_version = getattr(gateway, "prompt_version", "task8-navigation-v1")
    topic_map_version = getattr(gateway, "topic_map_version", "task8-topic-map-v1")
    values = (model_id, prompt_version, topic_map_version)
    if any(not isinstance(value, str) or not value for value in values):
        raise NavigationInputError("model-identity-invalid", "gateway model identity is incomplete")
    return values


def _resolve_with_stats(
    *,
    cache: Any,
    gateway: Any,
    cache_key: str,
    prompt: str,
    stats: dict[str, int],
    created_from_fingerprint: str | None = None,
    validator: Any | None = None,
) -> str:
    get = getattr(cache, "get")
    try:
        parameters = inspect.signature(get).parameters
    except (TypeError, ValueError):
        parameters = {}
    cached = get(cache_key, expected_fingerprint=created_from_fingerprint) if "expected_fingerprint" in parameters else get(cache_key)
    if cached is not None:
        stats["cache_hits"] += 1
        if not isinstance(cached, str):
            raise NavigationInputError("cache-output-invalid", "cached navigation output must be a string")
        if callable(validator):
            return validator(cached)
        return cached
    stats["provider_calls"] += 1
    return resolve_cached_output(
        cache=cache,
        gateway=gateway,
        cache_key=cache_key,
        prompt=prompt,
        created_from_fingerprint=created_from_fingerprint,
        validator=validator,
    )


def _generate_model_outputs(
    *,
    pages: Sequence[ReconciledPage],
    index: NavigationDocument,
    cache: Any,
    gateway: Any,
) -> tuple[dict[str, str], tuple[str, ...], dict[str, int]]:
    model_id, prompt_version, topic_map_version = _gateway_identity(gateway)
    stats = {"provider_calls": 0, "cache_hits": 0}
    descriptions: dict[str, str] = {}
    for page in pages:
        page_material = page.text.encode("utf-8")
        key = build_navigation_cache_key(
            kind="description",
            input_bytes=page_material,
            model_id=model_id,
            prompt_version=prompt_version,
            topic_map_version=topic_map_version,
        )
        prompt = (
            "task8 description\n"
            f"title={page.title}\nproduct={page.product}\nsection={page.section}\n"
            f"body:\n{_page_body_excerpt(page.text)}"
        )
        output = _resolve_with_stats(
            cache=cache,
            gateway=gateway,
            cache_key=key,
            prompt=prompt,
            stats=stats,
            created_from_fingerprint=hashlib.sha256(page_material).hexdigest(),
            validator=validate_description_output,
        )
        descriptions[page.page_path] = output

    index_material = index.body.encode("utf-8")
    suggestion_key = build_navigation_cache_key(
        kind="suggestion",
        input_bytes=index_material,
        model_id=model_id,
        prompt_version=prompt_version,
        topic_map_version=topic_map_version,
    )
    suggestion_prompt = f"task8 home suggestions\nindex:\n{index.body}"
    raw_suggestions = _resolve_with_stats(
        cache=cache,
        gateway=gateway,
        cache_key=suggestion_key,
        prompt=suggestion_prompt,
        stats=stats,
        created_from_fingerprint=hashlib.sha256(index_material).hexdigest(),
        validator=_validate_suggestion_json,
    )
    try:
        suggestions_value = json.loads(raw_suggestions)
    except json.JSONDecodeError as exc:
        raise NavigationInputError("model-output-invalid", "query suggestions are not valid JSON") from exc
    suggestions = validate_query_suggestions(suggestions_value)
    return descriptions, suggestions, stats


def _module_documents(
    tree: Mapping[str, Mapping[str, Sequence[MountEntry]]],
    descriptions: Mapping[str, str],
) -> dict[str, NavigationDocument]:
    skeleton = build_module_indexes(tree)
    result: dict[str, NavigationDocument] = {}
    for relative_path, document in skeleton.items():
        product, section = relative_path.split("/")[1:3]
        lines = [f"# {document.frontmatter['title']}", "", "## 页面", ""]
        for entry in tree[product][section]:
            description = descriptions[entry.page.page_path]
            lines.extend((f"- {entry.wikilink}", f"  description: {description}"))
        result[relative_path] = NavigationDocument(
            relative_path=relative_path,
            frontmatter=document.frontmatter,
            body="\n".join(lines).rstrip(),
        )
    return result


def _home_document(document: NavigationDocument, suggestions: Sequence[str]) -> NavigationDocument:
    body = document.body.replace(
        "<!-- query-suggestions:pending -->",
        "\n".join(f"- {suggestion}" for suggestion in suggestions),
    )
    return NavigationDocument(relative_path=document.relative_path, frontmatter=document.frontmatter, body=body)


__all__ += [
    "ConfiguredNavigationGateway",
    "JsonlNavigationCache",
    "MANIFEST_SCHEMA_VERSION",
    "MountEntry",
    "NavigationDocument",
    "NavigationDependencies",
    "NAVIGATION_GENERATED_BY",
    "NavigationInputError",
    "NavigationResult",
    "UnavailableNavigationGateway",
    "REJECTION_WORDS",
    "ReconciledPage",
    "build_index",
    "build_home",
    "build_mount_tree",
    "build_navigation_cache_key",
    "build_navigation_dependencies",
    "build_navigation_frontmatter",
    "build_navigation_metrics",
    "build_module_indexes",
    "infer_module_title",
    "load_and_validate",
    "reconcile_pages",
    "resolve_cached_output",
    "validate_query_suggestions",
    "validate_model_output",
    "validate_description_output",
]
