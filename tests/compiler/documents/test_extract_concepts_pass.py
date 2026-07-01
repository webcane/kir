"""Unit tests for ExtractConceptsPass (02-04b).

Covers:
- Basic LLM call and IR population (smoke test)
- LLM-02: cache hit suppresses second LLM call
- D-03 / LLM-03: LLM failure writes Diagnostic, does not halt
- Golden fixture replay for doc_01 (rich) and doc_07 (sparse)

All tests use FakeLLMAdapter — zero live API calls.
asyncio_mode="auto" is configured globally so no @pytest.mark.asyncio needed.
"""

from __future__ import annotations

from kir.compiler.documents.adapters.markdown_it_adapter import MarkdownItAdapter
from kir.compiler.documents.passes.extract_concepts import extract_concepts_pass
from kir.core.config.versions import compiler_version, prompt_version, schema_version
from kir.core.domain.models.diagnostic import Severity
from kir.core.domain.models.document import Document
from kir.core.domain.value_objects import Checksum
from kir.core.passes.context import CompilerContext
from kir.llm.cache import InMemoryCache, LLMCache
from kir.llm.fake_adapter import FakeLLMAdapter
from kir.llm.prompts.registry import PromptRegistry
from tests.compiler.documents.conftest import _ErrorFakeLLMAdapter, make_phase2_context
from tests.compiler.documents.fixtures.extract_concepts.expected_outputs import (
    DOC_01_EXPECTED,
    DOC_07_EXPECTED,
)
from tests.core.passes.fakes.fake_repository import InMemoryFakeRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CHECKSUM_VALUE = "a" * 64


def _make_doc_with_content(content: str, checksum_value: str = _CHECKSUM_VALUE) -> Document:
    """Build a minimal Document whose source is passed through MarkdownItAdapter
    to produce real sections (needed so the checksum-based cache key is meaningful).

    Args:
        content: Raw Markdown source.
        checksum_value: A stable SHA-256 hex string (64 chars) for the cache key.

    Returns:
        A Document with sections pre-populated from the content.
    """
    adapter = MarkdownItAdapter()
    sections = tuple(adapter.parse(content))
    return Document(
        id="test-doc",
        title="Test Document",
        source=content,
        checksum=Checksum(algorithm="sha256", value=checksum_value),
        language="en",
        sections=sections,
    )


def _make_context_with_adapter(
    adapter: FakeLLMAdapter | _ErrorFakeLLMAdapter,
    cache: LLMCache | None = None,
) -> CompilerContext:
    """Build a CompilerContext with a pre-constructed adapter and optional cache."""
    return CompilerContext(
        llm=adapter,
        repository=InMemoryFakeRepository(),
        parser=MarkdownItAdapter(),
        compiler_version=compiler_version,
        schema_version=schema_version,
        prompt_version=prompt_version,
        llm_cache=cache or LLMCache(InMemoryCache()),
        prompts=PromptRegistry(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_extract_concepts_pass_calls_llm_and_populates_document() -> None:
    """extract_concepts_pass calls FakeLLMAdapter once and populates concepts."""
    adapter = FakeLLMAdapter(output=DOC_01_EXPECTED)
    ctx = _make_context_with_adapter(adapter)
    ir = _make_doc_with_content("# Overview\n\nZephyr is a framework.")

    result = await extract_concepts_pass(ir, ctx)

    assert adapter.call_count == 1
    assert len(result.concepts) > 0


async def test_extract_concepts_pass_cache_hit_skips_llm_call() -> None:
    """LLM-02: second call to same document checksum hits cache, skips LLM (call_count stays 1)."""
    adapter = FakeLLMAdapter(output=DOC_01_EXPECTED)
    cache = LLMCache(InMemoryCache())
    ctx = _make_context_with_adapter(adapter, cache=cache)
    ir = _make_doc_with_content("# Overview\n\nZephyr is a framework.")

    # First call — cache miss, LLM is called
    result_1 = await extract_concepts_pass(ir, ctx)
    assert adapter.call_count == 1

    # Second call with same IR and same context (same cache key) — cache hit, no LLM
    result_2 = await extract_concepts_pass(ir, ctx)
    assert adapter.call_count == 1  # still 1 — LLM was NOT called again

    # Both results agree
    assert result_1.concepts == result_2.concepts


async def test_extraction_failure_produces_diagnostic_not_halt() -> None:
    """D-03 / LLM-03: LLM failure appends Diagnostic(code='extraction-failed'), does not raise."""
    error = RuntimeError("extraction failed")
    error_adapter = _ErrorFakeLLMAdapter(error)
    ctx = _make_context_with_adapter(error_adapter)
    ir = _make_doc_with_content("# Failure Doc\n\nSome content.")

    # Must not raise
    result = await extract_concepts_pass(ir, ctx)

    # Diagnostic is present
    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert diag.code == "extraction-failed"
    assert diag.severity == Severity.ERROR

    # Semantic fields are empty (not populated on failure)
    assert result.concepts == ()
    assert result.glossary == ()
    assert result.entities == ()
    assert result.references == ()


async def test_extract_concepts_pass_with_golden_fixture_doc_01() -> None:
    """Golden fixture replay: doc_01_rich — pass returns DOC_01_EXPECTED concepts."""
    fixture_path = (
        __file__
    )
    # Read the actual fixture file content
    import pathlib

    doc_path = (
        pathlib.Path(__file__).parent
        / "fixtures"
        / "extract_concepts"
        / "doc_01_rich.md"
    )
    content = doc_path.read_text(encoding="utf-8")

    adapter = FakeLLMAdapter(output=DOC_01_EXPECTED)
    ctx = _make_context_with_adapter(adapter)
    ir = _make_doc_with_content(content)

    result = await extract_concepts_pass(ir, ctx)

    # Concepts should match DOC_01_EXPECTED
    expected_concept_names = tuple(c.name for c in DOC_01_EXPECTED.concepts)
    assert result.concepts == expected_concept_names


async def test_extract_concepts_pass_with_golden_fixture_doc_07_sparse() -> None:
    """Golden fixture replay: doc_07_sparse — pass returns single concept, empty glossary."""
    import pathlib

    doc_path = (
        pathlib.Path(__file__).parent
        / "fixtures"
        / "extract_concepts"
        / "doc_07_genuinely_sparse.md"
    )
    content = doc_path.read_text(encoding="utf-8")

    adapter = FakeLLMAdapter(output=DOC_07_EXPECTED)
    ctx = _make_context_with_adapter(adapter)
    ir = _make_doc_with_content(content)

    result = await extract_concepts_pass(ir, ctx)

    assert len(result.concepts) == 1
    assert result.glossary == ()
