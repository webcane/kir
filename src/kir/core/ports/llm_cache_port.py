"""LLMCachePort — semantic cache port for LLM extraction results (LLM-02).

Defines the keyword-argument interface used by ExtractConceptsPass.
LLMCache in kir.llm satisfies this protocol structurally.

The four-component key (checksum + prompt_version + schema_version + model_id)
is an LLM-domain concern; this port expresses it at the domain boundary without
importing any kir.llm types.
"""

from typing import Protocol


class LLMCachePort(Protocol):
    def get(
        self,
        *,
        checksum: str,
        prompt_version: str,
        schema_version: str,
        model_id: str,
    ) -> object | None: ...

    def set(
        self,
        *,
        checksum: str,
        prompt_version: str,
        schema_version: str,
        model_id: str,
        value: object,
    ) -> None: ...
