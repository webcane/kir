"""Concept entity."""


from pydantic import BaseModel, ConfigDict

from kir.core.domain.models.provenance import SourceRef
from kir.core.domain.value_objects import ConceptId


class Concept(BaseModel):
    """Semantic concept entity with identity, definition, and provenance.

    Represents a named concept extracted from source documents, with optional
    definition, category, and source lineage.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: ConceptId
    canonical_name: str
    aliases: tuple[str, ...] = ()
    definition: str | None = None
    category: str | None = None
    provenance: tuple[SourceRef, ...] = ()
