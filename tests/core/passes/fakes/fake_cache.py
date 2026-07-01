"""FakeCache — generic key/value implementation of CachePort (D-03 scope:
no LLM-specific cache-key concepts such as checksum/prompt_version/
schema_version/model_id; that belongs to Phase 2's LLM-02, built on top of
this generic Protocol, not here)."""

class FakeCache:
    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self._store.get(key)

    def set(self, key: str, value: object) -> None:
        self._store[key] = value
