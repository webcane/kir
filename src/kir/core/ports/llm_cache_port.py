"""LLMCachePort — semantic cache port for LLM extraction results (LLM-02).

Defines the keyword-argument interface used by ExtractConceptsPass.
LLMCache in kir.llm satisfies this protocol structurally.

The four-component key (checksum + prompt_version + schema_version + model_id)
is an LLM-domain concern; this port expresses it at the domain boundary without
importing any kir.llm types.
"""

from typing import Protocol


class LLMCachePort(Protocol):
    """Semantic cache port for LLM extraction results.

    Uses a four-component key (checksum + prompt_version + schema_version + model_id)
    to enable cache hits across document changes and model updates.
    """

    def get(
        self,
        *,
        checksum: str,
        prompt_version: str,
        schema_version: str,
        model_id: str,
    ) -> object | None:
        """Retrieve cached extraction result by composite key.

        Args:
            checksum: SHA-256 checksum of the document source.
            prompt_version: Version identifier for the extraction prompt.
            schema_version: Version identifier for the extraction schema.
            model_id: Model identifier (e.g., "gpt-4o-2024-11-20").

        Returns:
            Cached extraction result if key matches, None otherwise.
        """
        ...

    def set(
        self,
        *,
        checksum: str,
        prompt_version: str,
        schema_version: str,
        model_id: str,
        value: object,
    ) -> None:
        """Store extraction result in cache by composite key.

        Args:
            checksum: SHA-256 checksum of the document source.
            prompt_version: Version identifier for the extraction prompt.
            schema_version: Version identifier for the extraction schema.
            model_id: Model identifier (e.g., "gpt-4o-2024-11-20").
            value: Extraction result to cache (ExtractionResult).
        """
        ...
