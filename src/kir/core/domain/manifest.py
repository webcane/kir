"""ArtifactManifest — id + version only this phase (D-04 scope limit).

No checksum field, no dependency-index field — those are later Artifact
System milestones (see PROJECT.md's cross-cutting "Artifact System" thread).
"""


from pydantic import BaseModel, ConfigDict


class ArtifactManifest(BaseModel):
    """Metadata for a compiled artifact: id and version.

    Phase 1 scope includes only id and version; extended fields
    (checksum, dependencies) are Phase 2/3 scope (see PROJECT.md).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_id: str
    version: int
