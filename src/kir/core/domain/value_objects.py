"""Domain value objects shared across entities.

`SourceRef` lives in `src/kir/core/domain/models/provenance.py` (its
canonical home) and is re-exported here is intentionally NOT done to avoid
two import paths for the same type — import `SourceRef` from
`kir.core.domain.models.provenance` directly.
"""


from pydantic import BaseModel, ConfigDict


class ConceptId(BaseModel):
    """Identifier for a Concept. Distinct type from RelationId so the two
    can never be silently interchanged."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: str


class RelationId(BaseModel):
    """Identifier for a Relation. Distinct type from ConceptId so the two
    can never be silently interchanged."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: str


class Checksum(BaseModel):
    """A content checksum, e.g. for cache-key construction or change detection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    algorithm: str
    value: str
