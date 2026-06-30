import pytest
from pydantic import ValidationError

from kir.core.domain.models.document import Document, Section
from kir.core.domain.value_objects import Checksum


def _checksum() -> Checksum:
    return Checksum(algorithm="sha256", value="abc123")


def test_document_constructs_with_defaults():
    document = Document(
        id="doc-1",
        title="Intro",
        source="raw/intro.md",
        checksum=_checksum(),
        language="en",
    )
    assert document.id == "doc-1"
    assert document.sections == ()
    assert document.concepts == ()
    assert document.glossary == ()
    assert document.entities == ()
    assert document.references == ()


def test_document_constructs_with_sections():
    section = Section(heading="Intro", content="Hello world")
    document = Document(
        id="doc-1",
        title="Intro",
        source="raw/intro.md",
        checksum=_checksum(),
        language="en",
        sections=[section],
    )
    assert isinstance(document.sections, tuple)
    assert document.sections == (section,)


def test_document_is_frozen_and_forbids_extra():
    document = Document(
        id="doc-1",
        title="Intro",
        source="raw/intro.md",
        checksum=_checksum(),
        language="en",
    )
    with pytest.raises(ValidationError):
        document.title = "Other"
    with pytest.raises(ValidationError):
        Document(
            id="doc-1",
            title="Intro",
            source="raw/intro.md",
            checksum=_checksum(),
            language="en",
            extra_field="x",
        )


def test_section_is_frozen_and_forbids_extra():
    section = Section(heading="Intro", content="Hello world")
    with pytest.raises(ValidationError):
        section.heading = "Other"
    with pytest.raises(ValidationError):
        Section(heading="Intro", content="Hello world", extra_field="x")
