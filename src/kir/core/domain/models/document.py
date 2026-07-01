"""Document entity — the Document IR per DOC-01.

Sub-fields (concepts/glossary/entities/references) are populated for real
only starting in Phase 2; here they are typed placeholders so the entity
shape exists per CORE-01.
"""


from pydantic import BaseModel, ConfigDict

from kir.core.domain.models.diagnostic import Diagnostic
from kir.core.domain.value_objects import Checksum


class Section(BaseModel):
    """Logical section of a document with optional heading and content.

    Represents a subdivision of a document as parsed by the MarkdownParserPort.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    heading: str
    content: str


class Document(BaseModel):
    """Document IR — root container for parsed and annotated document content.

    Holds the raw source, checksums, logical sections, and placeholder tuples
    for extracted concepts, glossary, entities, and references (populated in
    Phase 2/M1-extended by extraction passes).
    """

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
    diagnostics: tuple[Diagnostic, ...] = ()
