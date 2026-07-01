"""Shared fixtures for document compiler tests (Phase 2).

Provides Phase 2 CompilerContext variants wired with FakeLLMAdapter,
LLMCache(InMemoryCache()), and PromptRegistry() — needed by extraction
pass unit tests and DocumentCompiler integration tests.
"""

from __future__ import annotations

import pytest

from kir.compiler.documents.adapters.markdown_it_adapter import MarkdownItAdapter
from kir.core.config.versions import compiler_version, schema_version, prompt_version
from kir.core.passes.context import CompilerContext
from kir.llm.cache import InMemoryCache, LLMCache
from kir.llm.fake_adapter import FakeLLMAdapter
from kir.llm.pydantic_ai_adapter import DocumentExtractionOutput
from kir.llm.prompts.registry import PromptRegistry
from tests.core.passes.fakes.fake_repository import InMemoryFakeRepository


def make_phase2_context(
    fake_output: DocumentExtractionOutput | None = None,
    raise_error: Exception | None = None,
) -> CompilerContext:
    """Build a Phase 2 CompilerContext with FakeLLMAdapter wired for tests.

    Args:
        fake_output: If provided, FakeLLMAdapter returns this output on extract().
        raise_error: If provided, FakeLLMAdapter raises this exception on extract().

    Returns:
        A CompilerContext with FakeLLMAdapter, LLMCache(InMemoryCache()),
        PromptRegistry(), and proper version constants.
    """
    if raise_error is not None:
        adapter = _ErrorFakeLLMAdapter(raise_error)
    else:
        adapter = FakeLLMAdapter(output=fake_output)

    return CompilerContext(
        llm=adapter,
        repository=InMemoryFakeRepository(),
        parser=MarkdownItAdapter(),
        compiler_version=compiler_version,
        schema_version=schema_version,
        prompt_version=prompt_version,
        llm_cache=LLMCache(InMemoryCache()),
        prompts=PromptRegistry(),
    )


class _ErrorFakeLLMAdapter:
    """FakeLLMAdapter variant that raises a configured exception on extract()."""

    model_id: str = "fake:v0"

    def __init__(self, error: Exception) -> None:
        self._error = error
        self._call_count: int = 0

    async def extract(self, *, sections: object, prompt: str) -> DocumentExtractionOutput:
        self._call_count += 1
        raise self._error

    @property
    def call_count(self) -> int:
        return self._call_count


@pytest.fixture
def phase2_context() -> CompilerContext:
    """Default Phase 2 context with an empty-output FakeLLMAdapter."""
    return make_phase2_context()
