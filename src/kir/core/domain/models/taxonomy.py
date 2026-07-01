"""Taxonomy value object.

Kept intentionally minimal — TAX-01's full taxonomy modeling is M2 scope.
This phase only needs the type to exist per CORE-01's entity list.
"""


from pydantic import BaseModel, ConfigDict


class Taxonomy(BaseModel):
    """Hierarchical taxonomy classification for a concept.

    Represents a hierarchical classification path (e.g., ["Biology", "Genetics"])
    with a human-readable label. Full taxonomy modeling is Phase 3/M2 scope.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: tuple[str, ...]
    label: str
