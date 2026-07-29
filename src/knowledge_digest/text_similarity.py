"""Shared deterministic token overlap used by clustering and retrieval."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Protocol

from pathlib import Path

from .embedding import EmbeddingError, validate_vector_cache_entry, vector_cache_entry


_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _similarity(left: str, right: str) -> float:
    left_tokens, right_tokens = _tokens(left), _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


class SimilarityScorer(Protocol):
    backend: str

    def score(self, left: str, right: str) -> float: ...


@dataclass
class JaccardScorer:
    backend: str = "jaccard"

    def score(self, left: str, right: str) -> float:
        return _similarity(left, right)


@dataclass
class EmbeddingScorer:
    client: object
    probe_fingerprint: str
    cache_path: Path | None = None
    backend: str = "embedding"
    _cache: dict[str, list[float]] = field(default_factory=dict)
    _hash_cache: dict[str, list[float]] = field(default_factory=dict)
    _cache_hits: int = 0

    def __post_init__(self) -> None:
        if self.cache_path is None or not self.cache_path.is_file():
            return
        import json

        for line in self.cache_path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            vector = validate_vector_cache_entry(
                item,
                endpoint_identity=self.client.endpoint_identity,
                model=self.client.model,
                dimension=self.client.dimension,
                probe_fingerprint=self.probe_fingerprint,
            )
            if vector is not None:
                self._hash_cache[item["input_hash"]] = vector

    @property
    def cache_stats(self) -> dict[str, int]:
        return {
            "entries": len(self._cache),
            "persisted_entries": len(self._hash_cache),
            "hits": self._cache_hits,
        }

    def _vectors(self, texts: list[str]) -> list[list[float]]:
        import hashlib

        for text in texts:
            if text in self._cache:
                continue
            input_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if input_hash in self._hash_cache:
                self._cache[text] = self._hash_cache[input_hash]
                self._cache_hits += 1
        missing = [text for text in dict.fromkeys(texts) if text not in self._cache]
        if missing:
            try:
                vectors = self.client.embed(missing)
            except Exception as error:
                if isinstance(error, EmbeddingError):
                    raise
                raise EmbeddingError(f"embedding scorer failed ({type(error).__name__})") from error
            if len(vectors) != len(missing):
                raise EmbeddingError("embedding scorer returned a partial batch")
            self._cache.update(zip(missing, vectors, strict=True))
            if self.cache_path is not None:
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                with self.cache_path.open("a", encoding="utf-8") as target:
                    for text, vector in zip(missing, vectors, strict=True):
                        item = vector_cache_entry(
                            text,
                            vector,
                            endpoint_identity=self.client.endpoint_identity,
                            model=self.client.model,
                            dimension=self.client.dimension,
                            probe_fingerprint=self.probe_fingerprint,
                        )
                        import json

                        target.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")
                        self._hash_cache[item["input_hash"]] = vector
        return [self._cache[text] for text in texts]

    def prefetch(self, texts: list[str]) -> None:
        self._vectors(list(dict.fromkeys(texts)))

    def score(self, left: str, right: str) -> float:
        left_vector, right_vector = self._vectors([left, right])
        left_norm = math.sqrt(sum(value * value for value in left_vector))
        right_norm = math.sqrt(sum(value * value for value in right_vector))
        if left_norm == 0 or right_norm == 0:
            raise EmbeddingError("embedding scorer received a zero vector")
        return sum(a * b for a, b in zip(left_vector, right_vector, strict=True)) / (
            left_norm * right_norm
        )
