"""RepositoryPort — domain-owned port for artifact persistence."""


from typing import Protocol


class RepositoryPort(Protocol):
    """Port for persisting and retrieving compiled IR artifacts.

    The concrete repository implementation (filesystem, S3, database, etc.)
    is an interchangeable detail behind this Protocol.
    """

    def save(self, artifact_id: str, artifact: object) -> None:
        """Persist a compiled artifact.

        Args:
            artifact_id: Unique identifier for the artifact.
            artifact: Artifact object to persist (IR, manifest, etc.).
        """
        ...

    def load(self, artifact_id: str) -> object:
        """Retrieve a previously persisted artifact.

        Args:
            artifact_id: Unique identifier for the artifact to load.

        Returns:
            Loaded artifact object.
        """
        ...
