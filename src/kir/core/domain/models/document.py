"""Document entity — the Document IR per DOC-01.

Sub-fields (concepts/glossary/entities/references) are populated for real
only starting in Phase 2; here they are typed placeholders so the entity
shape exists per CORE-01.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from kir.core.domain.value_objects import Checksum


class Section(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    heading: str
    content: str


class Document(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    source: str
    checksum: Checksum
    language: str
    sections: tuple[Section, ...] = ()
    # Placeholder element type: Phase 2's extraction pass will replace this
    # with proper concept-mention references once concept extraction exists.
    concepts: tuple[str, ...] = ()
    glossary: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
