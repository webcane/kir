"""PydanticAIAdapter — the ONLY file in the codebase that imports pydantic_ai.

Per the hexagonal boundary (Anti-Pattern 4, ARCHITECTURE.md): domain/,
compiler/, and tooling/ must never import pydantic_ai. All LLM-SDK surface
is isolated here behind the LLMPort Protocol defined in core/ports/llm_port.py.

This adapter implements D-02: one combined structured-output call per document,
returning concepts, glossary terms, entities, and references together as a
single validated Pydantic model (DocumentExtractionOutput).
"""


from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent, ModelRetry
from pydantic_ai.settings import ModelSettings

from kir.core.domain.models.document import Section


# ---------------------------------------------------------------------------
# Extraction DTOs
# ---------------------------------------------------------------------------


class ExtractedConceptDTO(BaseModel):
    """A substantive idea, topic, or technical term discussed in the document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    definition: str | None = None
    category: str | None = None


class ExtractedGlossaryTermDTO(BaseModel):
    """A term that is explicitly defined or explained in the document text."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    term: str
    definition: str


class ExtractedEntityDTO(BaseModel):
    """A named person, organization, system, tool, or product mentioned."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    kind: str  # e.g. "person", "organization", "system" — free text at extraction time


class ExtractedReferenceDTO(BaseModel):
    """A pointer to another document, URL, or external resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target: str
    context: str | None = None


class DocumentExtractionOutput(BaseModel):
    """Combined output_type for the one-call-per-document extraction (D-02).

    All four categories validate together as one unit — partial-category
    failures cannot occur because PydanticAI validates the whole model.
    Used as LLMCache values and as the return type of LLMPort.extract().
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    concepts: list[ExtractedConceptDTO] = Field(default_factory=list)
    glossary: list[ExtractedGlossaryTermDTO] = Field(default_factory=list)
    entities: list[ExtractedEntityDTO] = Field(default_factory=list)
    references: list[ExtractedReferenceDTO] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class PydanticAIAdapter:
    """The only class in the codebase that constructs a pydantic_ai.Agent.

    Pass code depends on LLMPort, never on this class or on pydantic_ai types
    directly (Anti-Pattern 4, ARCHITECTURE.md).

    Implements LLMPort structurally: exposes model_id: str and
    async extract(*, sections, prompt) -> DocumentExtractionOutput.
    """

    def __init__(self, model: str, *, max_output_retries: int = 2) -> None:
        self.model_id: str = model
        self._agent: Agent[None, DocumentExtractionOutput] = Agent(
            model,
            output_type=DocumentExtractionOutput,  # v2 API name (not the v1 name)
            retries={"output": max_output_retries},  # v2 retries dict
            model_settings=ModelSettings(temperature=0.1, max_tokens=4096),
        )

        @self._agent.output_validator
        async def _non_empty(output: DocumentExtractionOutput) -> DocumentExtractionOutput:
            """Semantic guardrail: reject a fully-empty extraction result (AI-SPEC.md §6)."""
            if not any([output.concepts, output.glossary, output.entities, output.references]):
                raise ModelRetry(
                    "All four extraction categories are empty — re-read and retry."
                )
            return output

    async def extract(
        self,
        *,
        sections: list[Section],
        prompt: str,
    ) -> DocumentExtractionOutput:
        """Execute one combined extraction call per document (D-02).

        Args:
            sections: The document's parsed sections (passed for typing; the
                rendered prompt already contains their text content).
            prompt: The fully-rendered extraction prompt (PromptRegistry output).

        Returns:
            DocumentExtractionOutput with concepts, glossary, entities, references.
        """
        result = await self._agent.run(prompt)
        return result.output  # v2 API name
