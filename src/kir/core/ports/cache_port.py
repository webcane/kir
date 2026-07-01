"""CachePort — generic key/value cache port (D-03: no LLM-specific cache-key
concepts here; cache-key construction is an adapter-level concern)."""


from typing import Protocol


class CachePort(Protocol):
    """Generic key/value cache port for storing and retrieving values.

    The concrete cache implementation (in-memory dict, Redis, etc.) is an
    interchangeable detail behind this Protocol.
    """

    def get(self, key: str) -> object | None:
        """Retrieve a cached value by key.

        Args:
            key: Cache key to retrieve.

        Returns:
            Cached value if present, None otherwise.
        """
        ...

    def set(self, key: str, value: object) -> None:
        """Store a value in the cache.

        Args:
            key: Cache key to store under.
            value: Value to cache (must be serializable by the implementation).
        """
        ...
