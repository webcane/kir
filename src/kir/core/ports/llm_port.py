"""LLMPort — domain-owned port for LLM-backed semantic analysis.

The concrete LLM library (e.g. PydanticAI) is an interchangeable adapter
detail behind this Protocol — never a domain dependency.

Both Protocols are defined here so pass-ring code can type-hint against them
without importing from the llm/ package (Anti-Pattern 4: no llm/ imports in
domain/ or passes/).
"""

from typing import Protocol

from kir.core.domain.models.document import Section


class ExtractionResult(Protocol):
    """Structural Protocol satisfied by DocumentExtractionOutput from llm/ package.

    Defined in core/ so domain and pass code can type-hint against the result
    shape without importing from the adapter ring.
    """

    concepts: list
    glossary: list
    entities: list
    references: list


class LLMPort(Protocol):
    """Domain-owned port for LLM-backed combined extraction (D-02).

    One call per document — sections and prompt are passed together;
    the implementation returns a combined ExtractionResult rather than
    four separate calls.
    """

    model_id: str

    async def extract(
        self,
        *,
        sections: list[Section],
        prompt: str,
    ) -> ExtractionResult:
        """Extract concepts, glossary, entities, and references from sections.

        Args:
            sections: Document sections to extract from.
            prompt: Rendering prompt instructing the LLM what to extract.

        Returns:
            ExtractionResult with concepts, glossary, entities, references lists.
        """
        ...
