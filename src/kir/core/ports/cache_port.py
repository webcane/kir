"""CachePort — generic key/value cache port (D-03: no LLM-specific cache-key
concepts here; cache-key construction is an adapter-level concern)."""

from __future__ import annotations

from typing import Protocol


class CachePort(Protocol):
    def get(self, key: str) -> object | None: ...
    def set(self, key: str, value: object) -> None: ...
