"""Tests for MetadataPass — DOC-01 coverage.

MetadataPass populates id (slug of first heading), title, checksum (SHA-256 hex
of source), and language='en' on the Document IR. Depends on parse and section.
"""

import hashlib

from kir.compiler.documents.passes.metadata import metadata_pass
from kir.core.domain.models.document import Document, Section
from kir.core.domain.value_objects import Checksum
from kir.core.passes.context import CompilerContext

def _make_document(
    source: str = "test source",
    sections: tuple[Section, ...] = (),
) -> Document:
    """Build a minimal Document for MetadataPass testing."""
    return Document(
        id="placeholder-id",
        title="Placeholder",
        source=source,
        checksum=Checksum(algorithm="sha256", value="a" * 64),
        language="",
        sections=sections,
    )

class TestMetadataPassChecksum:
    def test_metadata_pass_computes_sha256_checksum(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """MetadataPass computes SHA-256 hex digest of ir.source."""
        source = "deterministic source text"
        expected_hex = hashlib.sha256(source.encode()).hexdigest()
        ir = _make_document(source=source)
        result = metadata_pass(ir, fake_compiler_context)

        assert result.checksum.value == expected_hex
        assert result.checksum.algorithm == "sha256"

    def test_metadata_pass_checksum_is_deterministic(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """Same source always produces the same checksum."""
        source = "same content"
        ir = _make_document(source=source)
        result1 = metadata_pass(ir, fake_compiler_context)
        result2 = metadata_pass(ir, fake_compiler_context)

        assert result1.checksum.value == result2.checksum.value

    def test_metadata_pass_different_sources_produce_different_checksums(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """Different sources produce different checksums."""
        ir1 = _make_document(source="content A")
        ir2 = _make_document(source="content B")
        result1 = metadata_pass(ir1, fake_compiler_context)
        result2 = metadata_pass(ir2, fake_compiler_context)

        assert result1.checksum.value != result2.checksum.value

class TestMetadataPassTitle:
    def test_metadata_pass_title_from_first_heading(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """Title is derived from the first section with a non-empty heading."""
        sections = (
            Section(heading="My Doc", content="body"),
            Section(heading="Second", content="more"),
        )
        ir = _make_document(sections=sections)
        result = metadata_pass(ir, fake_compiler_context)

        assert result.title == "My Doc"

    def test_metadata_pass_title_skips_preamble_section(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """Preamble section (heading='') is skipped when deriving title."""
        sections = (
            Section(heading="", content="preamble"),
            Section(heading="Real Title", content="body"),
        )
        ir = _make_document(sections=sections)
        result = metadata_pass(ir, fake_compiler_context)

        assert result.title == "Real Title"

    def test_metadata_pass_title_untitled_when_no_headings(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """Title is 'Untitled' when all sections have empty headings."""
        sections = (
            Section(heading="", content="preamble content"),
            Section(heading="", content="more content"),
        )
        ir = _make_document(sections=sections)
        result = metadata_pass(ir, fake_compiler_context)

        assert result.title == "Untitled"

    def test_metadata_pass_title_untitled_when_no_sections(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """Title is 'Untitled' when there are no sections."""
        ir = _make_document(sections=())
        result = metadata_pass(ir, fake_compiler_context)

        assert result.title == "Untitled"

class TestMetadataPassId:
    def test_metadata_pass_id_is_slug_of_title(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """id is a URL-safe slug: lowercase, spaces → hyphens."""
        sections = (Section(heading="Hello World", content="body"),)
        ir = _make_document(sections=sections)
        result = metadata_pass(ir, fake_compiler_context)

        assert result.id == "hello-world"

    def test_metadata_pass_id_untitled_when_no_heading(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """id is 'untitled' when title is 'Untitled'."""
        ir = _make_document(sections=())
        result = metadata_pass(ir, fake_compiler_context)

        assert result.id == "untitled"

    def test_metadata_pass_id_strips_special_characters(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """id strips non-alphanumeric, non-hyphen characters."""
        sections = (Section(heading="Hello, World!", content="body"),)
        ir = _make_document(sections=sections)
        result = metadata_pass(ir, fake_compiler_context)

        assert result.id == "hello-world"

    def test_metadata_pass_id_lowercased(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """id is always lowercase."""
        sections = (Section(heading="CamelCase Title", content="body"),)
        ir = _make_document(sections=sections)
        result = metadata_pass(ir, fake_compiler_context)

        assert result.id == "camelcase-title"

class TestMetadataPassLanguage:
    def test_metadata_pass_language_is_en(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """language is always 'en' after metadata_pass (Phase 2 scope)."""
        ir = _make_document()
        result = metadata_pass(ir, fake_compiler_context)

        assert result.language == "en"

class TestMetadataPassImmutability:
    def test_metadata_pass_returns_immutable_copy(
        self, fake_compiler_context: CompilerContext
    ) -> None:
        """metadata_pass returns a new Document; original is unchanged."""
        ir = _make_document(source="test")
        result = metadata_pass(ir, fake_compiler_context)

        # Original unchanged
        assert ir.title == "Placeholder"
        assert ir.language == ""
        # Result is populated
        assert result.title == "Untitled"
        assert result.language == "en"
        # Different objects
        assert ir is not result
