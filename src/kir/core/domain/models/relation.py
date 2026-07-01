"""Relation value object.

`relation_type` stays a plain string this phase — the relation vocabulary
(REL-01) is core-and-extensible (per PROJECT.md's Architectural Decisions),
finalized in Phase 3/M2, not hardcoded as an enum here.
"""


from pydantic import BaseModel, ConfigDict

from kir.core.domain.models.provenance import SourceRef
from kir.core.domain.value_objects import ConceptId, RelationId


class Relation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: RelationId
    relation_type: str
    source_concept_id: ConceptId
    target_concept_id: ConceptId
    provenance: tuple[SourceRef, ...] = ()
