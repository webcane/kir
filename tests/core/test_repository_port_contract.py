"""Shared contract test proving RepositoryPort port-substitutability: the
same test runs unmodified against both InMemoryFakeRepository and
YamlFileRepository (variant 1 and variant 2), proving the boundary is real
rather than merely asserting a fake exists.
"""

from pathlib import Path

import pytest

from kir.tooling.repository.yaml_repository import YamlFileRepository
from tests.core.passes.fakes.fake_repository import InMemoryFakeRepository

@pytest.fixture(params=["in_memory", "yaml_file"])
def repository(request: pytest.FixtureRequest, tmp_path: Path):
    if request.param == "in_memory":
        return InMemoryFakeRepository()
    return YamlFileRepository(tmp_path / "kir")

def test_save_then_load_roundtrips(repository) -> None:
    repository.save("artifact-1", {"id": "artifact-1", "version": 1})
    assert repository.load("artifact-1") == {"id": "artifact-1", "version": 1}
