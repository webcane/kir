"""Tests for SectionPass — DOC-01 coverage.

SectionPass normalizes section content by stripping leading/trailing whitespace.
It does not modify headings or add/remove sections.
"""

from __future__ import annotations

from kir.compiler.documents.passes.section import section_pass
from kir.core.domain.models.document import Document, Section
from kir.core.domain.value_objects import Checksum
from kir.core.passes.context import CompilerContext


def _make_document_with_sections(*sections: Section) -> Document:
    """Build a Document with the given sections for testing."""
    return Document(
        id="test-doc",
        title="Test",
        source="test source",
        checksum=Checksum(algorithm="sha256", value="a" * 64),
        language="en",
        sections=tuple(sections),
    )


class TestSectionPass:
    def test_section_pass_strips_whitespace_from_content(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """SectionPass strips leading/trailing whitespace from Section.content."""
        section_with_whitespace = Section(
            heading="My Section", content="  \n  content here  \n  "
        )
        ir = _make_document_with_sections(section_with_whitespace)
        result = section_pass(ir, fake_compiler_context)

        assert len(result.sections) == 1
        assert result.sections[0].content == "content here"

    def test_section_pass_preserves_headings(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """SectionPass does not modify headings."""
        original_heading = "Preserved Heading"
        s = Section(heading=original_heading, content="  body  ")
        ir = _make_document_with_sections(s)
        result = section_pass(ir, fake_compiler_context)

        assert result.sections[0].heading == original_heading

    def test_section_pass_produces_immutable_copy(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """section_pass returns a new Document; original is unchanged."""
        s = Section(heading="H", content="  text  ")
        ir = _make_document_with_sections(s)
        result = section_pass(ir, fake_compiler_context)

        # Original sections unchanged (whitespace intact)
        assert ir.sections[0].content == "  text  "
        # Result has stripped content
        assert result.sections[0].content == "text"
        # Different objects
        assert ir is not result

    def test_section_pass_handles_multiple_sections(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """SectionPass processes all sections, not just the first."""
        sections = [
            Section(heading="A", content="  alpha  "),
            Section(heading="B", content="\nbeta\n"),
            Section(heading="C", content="gamma"),
        ]
        ir = _make_document_with_sections(*sections)
        result = section_pass(ir, fake_compiler_context)

        assert len(result.sections) == 3
        assert result.sections[0].content == "alpha"
        assert result.sections[1].content == "beta"
        assert result.sections[2].content == "gamma"

    def test_section_pass_empty_sections_remain_empty(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """Sections with only whitespace content become empty string after stripping."""
        s = Section(heading="H", content="   \n\t  ")
        ir = _make_document_with_sections(s)
        result = section_pass(ir, fake_compiler_context)

        assert result.sections[0].content == ""

    def test_section_pass_no_sections_is_a_no_op(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """SectionPass with no sections returns document with empty sections tuple."""
        ir = _make_document_with_sections()
        result = section_pass(ir, fake_compiler_context)

        assert result.sections == ()
