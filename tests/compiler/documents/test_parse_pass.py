"""Tests for ParsePass — DOC-01 coverage.

ParsePass populates Document.sections by calling ctx.parser.parse(ir.source)
via the MarkdownParserPort. Tests use both FakeMarkdownParser (via the
fake_compiler_context fixture) and MarkdownItAdapter directly to verify
real heading-based splitting behavior.
"""

from __future__ import annotations

import pytest

from kir.compiler.documents.adapters.markdown_it_adapter import MarkdownItAdapter
from kir.compiler.documents.passes.parse import parse_pass
from kir.core.domain.models.document import Document, Section
from kir.core.domain.value_objects import Checksum
from kir.core.passes.context import CompilerContext


def _make_document(source: str = "test source") -> Document:
    """Build a minimal Document with safe defaults for testing."""
    return Document(
        id="test-doc",
        title="Test",
        source=source,
        checksum=Checksum(algorithm="sha256", value="a" * 64),
        language="en",
        sections=(),
    )


class TestParsePassWithFakeParser:
    """Tests using the FakeMarkdownParser (via fake_compiler_context fixture)."""

    def test_parse_pass_populates_sections_from_parser(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """ParsePass calls ctx.parser.parse() and stores the result as sections."""
        ir = _make_document("some markdown source")
        result = parse_pass(ir, fake_compiler_context)

        # FakeMarkdownParser returns [Section(heading="fake", content=source)]
        assert isinstance(result.sections, tuple)
        assert len(result.sections) > 0

    def test_parse_pass_returns_immutable_copy(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """parse_pass returns a new Document; original sections are unchanged."""
        ir = _make_document("source text")
        result = parse_pass(ir, fake_compiler_context)

        # Original is unchanged (empty tuple)
        assert ir.sections == ()
        # Result has populated sections
        assert len(result.sections) > 0
        # They are different objects
        assert ir is not result

    def test_parse_pass_sections_content_matches_source(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """FakeMarkdownParser injects the source text as section content."""
        source = "hello world content"
        ir = _make_document(source)
        result = parse_pass(ir, fake_compiler_context)

        # FakeMarkdownParser.parse() returns [Section(heading="fake", content=text)]
        assert result.sections[0].content == source


class TestParsePassWithMarkdownItAdapter:
    """Tests using MarkdownItAdapter directly to verify real heading-based splitting."""

    def _make_context_with_adapter(
        self, fake_compiler_context: CompilerContext
    ) -> CompilerContext:
        """Replace the fake parser in fake_compiler_context with MarkdownItAdapter."""
        return CompilerContext(
            llm=fake_compiler_context.llm,
            repository=fake_compiler_context.repository,
            parser=MarkdownItAdapter(),
            compiler_version=fake_compiler_context.compiler_version,
            schema_version=fake_compiler_context.schema_version,
        )

    def test_parse_pass_with_markdown_it_adapter_heading_based_splitting(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """ParsePass with MarkdownItAdapter splits on H1–H2 headings per D-01."""
        ctx = self._make_context_with_adapter(fake_compiler_context)
        ir = _make_document("# H1\n\ncontent\n\n## H2\n\nmore")
        result = parse_pass(ir, ctx)

        assert len(result.sections) == 2
        assert result.sections[0].heading == "H1"
        assert result.sections[1].heading == "H2"

    def test_parse_pass_preamble_gets_empty_heading(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """Content before first heading becomes preamble Section with heading=''."""
        ctx = self._make_context_with_adapter(fake_compiler_context)
        ir = _make_document("preamble text\n\n# First Heading\n\nbody")
        result = parse_pass(ir, ctx)

        assert len(result.sections) == 2
        assert result.sections[0].heading == ""
        assert "preamble text" in result.sections[0].content
        assert result.sections[1].heading == "First Heading"

    def test_parse_pass_heading_content_excluded_from_body(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """Section content does not include heading syntax (the '#' characters)."""
        ctx = self._make_context_with_adapter(fake_compiler_context)
        ir = _make_document("# My Heading\n\nbody paragraph")
        result = parse_pass(ir, ctx)

        assert result.sections[0].heading == "My Heading"
        assert "#" not in result.sections[0].content
        assert "body paragraph" in result.sections[0].content

    def test_parse_pass_all_heading_levels_h1_to_h6(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """H1 through H6 all trigger new sections per D-01."""
        ctx = self._make_context_with_adapter(fake_compiler_context)
        source = "# H1\n\n## H2\n\n### H3\n\n#### H4\n\n##### H5\n\n###### H6"
        ir = _make_document(source)
        result = parse_pass(ir, ctx)

        assert len(result.sections) == 6
        headings = [s.heading for s in result.sections]
        assert headings == ["H1", "H2", "H3", "H4", "H5", "H6"]
