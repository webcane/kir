"""RepositoryPort — domain-owned port for artifact persistence."""


from typing import Protocol


class RepositoryPort(Protocol):
    def save(self, artifact_id: str, artifact: object) -> None: ...
    def load(self, artifact_id: str) -> object: ...
