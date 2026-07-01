"""InMemoryFakeRepository — variant 1 of RepositoryPort, used in the shared
contract test (tests/core/test_repository_port_contract.py) alongside
YamlFileRepository to prove port-substitutability."""

class InMemoryFakeRepository:
    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    def save(self, artifact_id: str, artifact: object) -> None:
        self._store[artifact_id] = artifact

    def load(self, artifact_id: str) -> object:
        return self._store[artifact_id]
