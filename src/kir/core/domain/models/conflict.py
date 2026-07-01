"""Conflict value object.

Kept intentionally minimal — CONF-01..03's full conflict modeling is M2
scope. This phase only needs the type to exist per CORE-01's entity list.
"""


from pydantic import BaseModel, ConfigDict

from kir.core.domain.value_objects import ConceptId


class Conflict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    conflict_type: str
    description: str
    concept_ids: tuple[ConceptId, ...] = ()
