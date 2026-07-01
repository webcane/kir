"""Taxonomy value object.

Kept intentionally minimal — TAX-01's full taxonomy modeling is M2 scope.
This phase only needs the type to exist per CORE-01's entity list.
"""


from pydantic import BaseModel, ConfigDict


class Taxonomy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    path: tuple[str, ...]
    label: str
