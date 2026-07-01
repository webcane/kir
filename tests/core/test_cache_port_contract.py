"""Shared contract test proving FakeCache satisfies CachePort and that the
abstraction is swappable (D-03). Structured as a parametrized fixture (even
though only one CachePort implementation exists this phase) so a second
variant can be parametrized in later without restructuring this test.
"""

import pytest

from tests.core.passes.fakes.fake_cache import FakeCache

@pytest.fixture(params=["in_memory"])
def cache(request: pytest.FixtureRequest) -> FakeCache:
    if request.param == "in_memory":
        return FakeCache()
    raise ValueError(f"unknown cache variant: {request.param!r}")

def test_set_then_get_roundtrips(cache: FakeCache) -> None:
    cache.set("key", "value")
    assert cache.get("key") == "value"

def test_get_missing_key_returns_none(cache: FakeCache) -> None:
    assert cache.get("missing") is None
