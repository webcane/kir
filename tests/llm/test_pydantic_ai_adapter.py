"""Unit tests for FakeLLMAdapter and PydanticAIAdapter (LLM-01, LLM-03)."""

from __future__ import annotations

import pytest
from pydantic_ai.models.test import TestModel

from kir.llm.fake_adapter import FakeLLMAdapter
from kir.llm.pydantic_ai_adapter import DocumentExtractionOutput, PydanticAIAdapter


class TestFakeLLMAdapter:
    async def test_fake_llm_adapter_satisfies_llm_port_structurally(self) -> None:
        adapter = FakeLLMAdapter()
        result = await adapter.extract(sections=[], prompt="test")
        assert isinstance(result, DocumentExtractionOutput)

    async def test_fake_llm_adapter_call_count_increments(self) -> None:
        adapter = FakeLLMAdapter()
        await adapter.extract(sections=[], prompt="first")
        await adapter.extract(sections=[], prompt="second")
        assert adapter.call_count == 2

    async def test_fake_llm_adapter_returns_configured_output(self) -> None:
        custom = DocumentExtractionOutput(
            concepts=[],
            glossary=[],
            entities=[],
            references=[],
        )
        adapter = FakeLLMAdapter(output=custom)
        result = await adapter.extract(sections=[], prompt="test")
        assert result is custom

    def test_fake_llm_adapter_model_id_attribute(self) -> None:
        assert FakeLLMAdapter.model_id == "fake:v0"
        assert FakeLLMAdapter().model_id == "fake:v0"


class TestPydanticAIAdapter:
    async def test_pydantic_ai_adapter_uses_fake_model(self) -> None:
        # Provide non-empty output args so the output_validator (which rejects
        # all-empty results) doesn't exhaust retries.
        non_empty_args = {
            "concepts": [{"name": "test concept"}],
            "glossary": [],
            "entities": [],
            "references": [],
        }
        adapter = PydanticAIAdapter("test")
        with adapter._agent.override(model=TestModel(custom_output_args=non_empty_args)):
            result = await adapter.extract(sections=[], prompt="extract something")
        assert isinstance(result, DocumentExtractionOutput)
        assert len(result.concepts) > 0
