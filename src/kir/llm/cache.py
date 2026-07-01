"""LLM cache layer — four-part cache key construction and InMemoryCache.

Implements LLM-02: cache key = checksum + prompt_version + schema_version +
pinned model_id. All four components must be non-empty to guard against
degenerate cache-key collisions (AI-SPEC.md Section 6 guardrail).

InMemoryCache is the production CachePort implementation for Phase 2.
File-based persistence (SQLite, shelve) is Phase 5 scope per RESEARCH.md
Pattern 7 — in-memory is sufficient for single-run correctness.
"""


from kir.core.ports.cache_port import CachePort


class LLMCacheKey:
    """Builds the four-part composite cache key required by LLM-02.

    Key format: ``checksum:prompt_version:schema_version:model_id``

    All four components must be non-empty strings. A degenerate (empty/None)
    component would allow different documents or configurations to collide on
    the same cache entry — LLM-02's integrity guarantee would be silently
    violated.
    """

    def build(
        self,
        checksum: str,
        prompt_version: str,
        schema_version: str,
        model_id: str,
    ) -> str:
        """Build and return the composite cache key string.

        Args:
            checksum: Document content checksum (SHA-based, from Document.checksum.value).
            prompt_version: Versioned prompt identifier (e.g. "1" for extract_v1.md).
            schema_version: Extraction schema version (from Settings / CompilerContext).
            model_id: Pinned LLM model identifier (e.g. "anthropic:claude-sonnet-4-6").

        Returns:
            Colon-delimited composite key string.

        Raises:
            ValueError: If any component is None or empty.
        """
        if not all([checksum, prompt_version, schema_version, model_id]):
            raise ValueError(
                "All four cache key components must be non-empty (LLM-02 integrity)"
            )
        return f"{checksum}:{prompt_version}:{schema_version}:{model_id}"


class LLMCache:
    """LLM response cache wrapping a generic CachePort backend.

    Provides a high-level get/set interface using the four-part LLM cache key
    (LLM-02) rather than raw string keys. Storage is delegated entirely to the
    injected CachePort backend (InMemoryCache in Phase 2; file-based in Phase 5).
    """

    def __init__(self, backend: CachePort) -> None:
        self._backend = backend
        self._key_builder = LLMCacheKey()

    def get(
        self,
        *,
        checksum: str,
        prompt_version: str,
        schema_version: str,
        model_id: str,
    ) -> object | None:
        """Look up a cached extraction result.

        Returns None on a cache miss. All four key components are keyword-only
        to prevent positional argument confusion.
        """
        key = self._key_builder.build(checksum, prompt_version, schema_version, model_id)
        return self._backend.get(key)

    def set(
        self,
        *,
        checksum: str,
        prompt_version: str,
        schema_version: str,
        model_id: str,
        value: object,
    ) -> None:
        """Store an extraction result under the four-part cache key.

        All four key components are keyword-only to prevent positional confusion.
        """
        key = self._key_builder.build(checksum, prompt_version, schema_version, model_id)
        self._backend.set(key, value)


class InMemoryCache:
    """Production in-memory CachePort implementation for Phase 2.

    Mirrors the FakeCache pattern from tests/core/passes/fakes/fake_cache.py,
    but lives in src/ as a legitimate production implementation. A single
    compiler run shares one InMemoryCache instance, so results extracted during
    the run are available to cache lookups within the same run.

    File-based persistence (cross-run cache) is Phase 5 scope per RESEARCH.md
    Pattern 7 — in-memory is correct and sufficient for Phase 2's correctness
    requirement (LLM-02).
    """

    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self._store.get(key)

    def set(self, key: str, value: object) -> None:
        self._store[key] = value
