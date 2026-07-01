"""Integration tests for DocumentCompiler (02-04b, DOC-01, DOC-02).

Tests:
- DOC-01: compile() produces a fully-populated Document IR
- DOC-02: compiling two different files never cross-contaminates sections or metadata
- Pipeline length: DocumentCompiler has exactly four passes

All tests use FakeLLMAdapter — zero live API calls.
asyncio_mode="auto" is configured globally so no @pytest.mark.asyncio needed.
"""

import pathlib

from kir.compiler.documents.compiler import DocumentCompiler
from kir.compiler.documents.passes import document_registry
from kir.core.config.versions import compiler_version, prompt_version, schema_version
from kir.core.passes.context import CompilerContext
from kir.llm.cache import InMemoryCache, LLMCache
from kir.llm.fake_adapter import FakeLLMAdapter
from kir.llm.prompts.registry import PromptRegistry
from tests.compiler.documents.fixtures.extract_concepts.expected_outputs import (
    DOC_01_EXPECTED,
)
from tests.core.passes.fakes.fake_repository import InMemoryFakeRepository
from kir.compiler.documents.adapters.markdown_it_adapter import MarkdownItAdapter


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_compiler_context(fake_output=None) -> tuple[DocumentCompiler, FakeLLMAdapter]:
    """Build a DocumentCompiler with FakeLLMAdapter wired into a full Phase 2 context.

    Returns both the compiler and the adapter so callers can inspect call_count.
    """
    adapter = FakeLLMAdapter(output=fake_output)
    ctx = CompilerContext(
        llm=adapter,
        repository=InMemoryFakeRepository(),
        parser=MarkdownItAdapter(),
        compiler_version=compiler_version,
        schema_version=schema_version,
        prompt_version=prompt_version,
        llm_cache=LLMCache(InMemoryCache()),
        prompts=PromptRegistry(),
    )
    compiler = DocumentCompiler(document_registry, ctx)
    return compiler, adapter


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_document_compiler_compiles_markdown_to_full_document_ir(
    tmp_path: pathlib.Path,
) -> None:
    """DOC-01: compile() returns a fully-populated Document IR from a Markdown file."""
    # Write a Markdown file to tmp_path
    doc_content = (
        pathlib.Path(__file__).parent
        / "fixtures"
        / "extract_concepts"
        / "doc_01_rich.md"
    ).read_text(encoding="utf-8")
    doc_path = tmp_path / "doc.md"
    doc_path.write_text(doc_content, encoding="utf-8")

    compiler, _ = _make_compiler_context(fake_output=DOC_01_EXPECTED)
    result = await compiler.compile(doc_path)

    # Core IR fields are populated
    assert result.id and len(result.id) > 0, "id should be non-empty"
    assert result.title and len(result.title) > 0, "title should be non-empty"

    # Checksum is a 64-char SHA-256 hex string
    assert len(result.checksum.value) == 64, "checksum should be 64 hex chars"
    assert result.checksum.algorithm == "sha256"

    # Language is detected
    assert result.language == "en"

    # Sections were parsed
    assert isinstance(result.sections, tuple)
    assert len(result.sections) > 0

    # Concepts were extracted from DOC_01_EXPECTED
    assert isinstance(result.concepts, tuple)
    assert len(result.concepts) > 0

    # No unexpected diagnostics
    assert result.diagnostics == ()


async def test_no_cross_contamination(tmp_path: pathlib.Path) -> None:
    """DOC-02: compiling two different files never puts one file's content in the other's IR."""
    doc_a_text = (
        "# Document Alpha\n\n"
        "Alpha is about the alpha concept. It describes alpha thoroughly.\n\n"
        "## Alpha Details\n\nAlpha detail section with alpha-specific content."
    )
    doc_b_text = (
        "# Document Beta\n\n"
        "Beta is about the beta concept. It describes beta thoroughly.\n\n"
        "## Beta Details\n\nBeta detail section with beta-specific content."
    )

    from kir.llm.pydantic_ai_adapter import (
        DocumentExtractionOutput,
        ExtractedConceptDTO,
    )

    output_a = DocumentExtractionOutput(
        concepts=[ExtractedConceptDTO(name="alpha concept")],
        glossary=[],
        entities=[],
        references=[],
    )
    output_b = DocumentExtractionOutput(
        concepts=[ExtractedConceptDTO(name="beta concept")],
        glossary=[],
        entities=[],
        references=[],
    )

    doc_a_path = tmp_path / "doc_a.md"
    doc_b_path = tmp_path / "doc_b.md"
    doc_a_path.write_text(doc_a_text, encoding="utf-8")
    doc_b_path.write_text(doc_b_text, encoding="utf-8")

    # Use separate compilers with separate caches and adapters
    compiler_a, _ = _make_compiler_context(fake_output=output_a)
    compiler_b, _ = _make_compiler_context(fake_output=output_b)

    result_a = await compiler_a.compile(doc_a_path)
    result_b = await compiler_b.compile(doc_b_path)

    # Titles are different
    assert result_a.title != result_b.title

    # Checksums are different (different source content)
    assert result_a.checksum.value != result_b.checksum.value

    # Section content from doc_a does not appear in doc_b
    sections_a_content = {s.content for s in result_a.sections}
    sections_b_content = {s.content for s in result_b.sections}
    assert not sections_a_content.intersection(
        sections_b_content
    ), "Cross-contamination detected: section content appeared in both documents"

    # Headings are different
    headings_a = {s.heading for s in result_a.sections}
    headings_b = {s.heading for s in result_b.sections}
    assert not headings_a.intersection(
        headings_b
    ), "Cross-contamination detected: heading appeared in both documents"


def test_document_compiler_pipeline_has_four_passes() -> None:
    """DocumentCompiler._pipeline contains exactly 4 passes (parse, section, metadata, extract_concepts)."""
    # Build directly to access _pipeline
    from kir.llm.pydantic_ai_adapter import DocumentExtractionOutput

    adapter = FakeLLMAdapter(output=DocumentExtractionOutput())
    ctx = CompilerContext(
        llm=adapter,
        repository=InMemoryFakeRepository(),
        parser=MarkdownItAdapter(),
        compiler_version=compiler_version,
        schema_version=schema_version,
        prompt_version=prompt_version,
        llm_cache=LLMCache(InMemoryCache()),
        prompts=PromptRegistry(),
    )
    compiler = DocumentCompiler(document_registry, ctx)
    assert len(compiler._pipeline) == 4


async def test_compile_persists_document_to_repository(tmp_path: pathlib.Path) -> None:
    """STOR-01: compile() saves exactly one artifact to the repository with the expected keys."""
    from kir.llm.pydantic_ai_adapter import DocumentExtractionOutput, ExtractedConceptDTO

    doc_text = (
        "# Alpha Concept\n\n"
        "Alpha is about the alpha concept. It describes alpha thoroughly.\n\n"
        "## Alpha Details\n\nAlpha detail section with alpha-specific content."
    )
    doc_path = tmp_path / "alpha.md"
    doc_path.write_text(doc_text, encoding="utf-8")

    fake_output = DocumentExtractionOutput(
        concepts=[ExtractedConceptDTO(name="alpha concept")],
        glossary=[],
        entities=[],
        references=[],
    )
    repo = InMemoryFakeRepository()
    adapter = FakeLLMAdapter(output=fake_output)
    ctx = CompilerContext(
        llm=adapter,
        repository=repo,
        parser=MarkdownItAdapter(),
        compiler_version=compiler_version,
        schema_version=schema_version,
        prompt_version=prompt_version,
        llm_cache=LLMCache(InMemoryCache()),
        prompts=PromptRegistry(),
    )
    compiler = DocumentCompiler(document_registry, ctx)
    await compiler.compile(doc_path)

    assert len(repo._store) == 1
    stored = list(repo._store.values())[0]
    assert isinstance(stored, dict)
    assert set(stored.keys()) >= {"id", "title", "source", "checksum", "language", "sections"}
    assert stored["id"] and len(stored["id"]) > 0
    assert stored["title"] and len(stored["title"]) > 0
    # artifact_id key matches the document's id field
    artifact_id = list(repo._store.keys())[0]
    assert artifact_id == stored["id"]


async def test_two_documents_produce_two_distinct_repository_entries(
    tmp_path: pathlib.Path,
) -> None:
    """STOR-02: compiling two different Markdown files produces two separate, non-overlapping repository entries."""
    from kir.llm.pydantic_ai_adapter import DocumentExtractionOutput, ExtractedConceptDTO

    doc_a_text = (
        "# Document Alpha\n\n"
        "Alpha is about the alpha concept. It describes alpha thoroughly.\n\n"
        "## Alpha Details\n\nAlpha detail section with alpha-specific content."
    )
    doc_b_text = (
        "# Document Beta\n\n"
        "Beta is about the beta concept. It describes beta thoroughly.\n\n"
        "## Beta Details\n\nBeta detail section with beta-specific content."
    )

    output_a = DocumentExtractionOutput(
        concepts=[ExtractedConceptDTO(name="alpha concept")],
        glossary=[],
        entities=[],
        references=[],
    )
    output_b = DocumentExtractionOutput(
        concepts=[ExtractedConceptDTO(name="beta concept")],
        glossary=[],
        entities=[],
        references=[],
    )

    doc_a_path = tmp_path / "doc_a.md"
    doc_b_path = tmp_path / "doc_b.md"
    doc_a_path.write_text(doc_a_text, encoding="utf-8")
    doc_b_path.write_text(doc_b_text, encoding="utf-8")

    # Both compilers share a single repository so id collisions would be
    # visible as a missing or overwritten entry.
    repo = InMemoryFakeRepository()

    adapter_a = FakeLLMAdapter(output=output_a)
    ctx_a = CompilerContext(
        llm=adapter_a,
        repository=repo,
        parser=MarkdownItAdapter(),
        compiler_version=compiler_version,
        schema_version=schema_version,
        prompt_version=prompt_version,
        llm_cache=LLMCache(InMemoryCache()),
        prompts=PromptRegistry(),
    )
    compiler_a = DocumentCompiler(document_registry, ctx_a)

    adapter_b = FakeLLMAdapter(output=output_b)
    ctx_b = CompilerContext(
        llm=adapter_b,
        repository=repo,
        parser=MarkdownItAdapter(),
        compiler_version=compiler_version,
        schema_version=schema_version,
        prompt_version=prompt_version,
        llm_cache=LLMCache(InMemoryCache()),
        prompts=PromptRegistry(),
    )
    compiler_b = DocumentCompiler(document_registry, ctx_b)

    await compiler_a.compile(doc_a_path)
    await compiler_b.compile(doc_b_path)

    assert len(repo._store) == 2, "Expected 2 distinct entries; id collision may have occurred"
    key_a, key_b = list(repo._store.keys())
    assert key_a != key_b

    title_a = repo._store[key_a]["title"]
    title_b = repo._store[key_b]["title"]
    assert title_a != title_b
