"""CORE-07 immutability proofs across Document, Concept, and FakeIR.

For each entity type: model_copy(update=...) produces a new instance, the
original is unchanged, and direct field reassignment raises.
"""

import pytest
from pydantic import ValidationError

from kir.core.domain.ir import FakeIR
from kir.core.domain.models.concept import Concept
from kir.core.domain.models.diagnostic import Diagnostic, Severity
from kir.core.domain.models.document import Document
from kir.core.domain.value_objects import Checksum, ConceptId


def test_document_model_copy_does_not_mutate_original():
    original = Document(
        id="doc-1",
        title="Intro",
        source="raw/intro.md",
        checksum=Checksum(algorithm="sha256", value="abc123"),
        language="en",
    )
    updated = original.model_copy(update={"title": "Updated Intro"})

    assert original.title == "Intro"
    assert updated.title == "Updated Intro"
    assert original is not updated


def test_document_direct_field_reassignment_raises():
    original = Document(
        id="doc-1",
        title="Intro",
        source="raw/intro.md",
        checksum=Checksum(algorithm="sha256", value="abc123"),
        language="en",
    )
    with pytest.raises(ValidationError):
        original.title = "Mutated"


def test_concept_model_copy_does_not_mutate_original():
    original = Concept(id=ConceptId(value="auth"), canonical_name="Authentication")
    updated = original.model_copy(update={"canonical_name": "AuthN"})

    assert original.canonical_name == "Authentication"
    assert updated.canonical_name == "AuthN"
    assert original is not updated


def test_concept_direct_field_reassignment_raises():
    original = Concept(id=ConceptId(value="auth"), canonical_name="Authentication")
    with pytest.raises(ValidationError):
        original.canonical_name = "Mutated"


def test_fake_ir_model_copy_does_not_mutate_original():
    original = FakeIR(value=0)
    diagnostic = Diagnostic(code="E001", severity=Severity.ERROR, message="bad")
    updated = original.model_copy(
        update={"value": 1, "diagnostics": original.diagnostics + (diagnostic,)}
    )

    assert original.value == 0
    assert original.diagnostics == ()
    assert updated.value == 1
    assert updated.diagnostics == (diagnostic,)
    assert original is not updated


def test_fake_ir_direct_field_reassignment_raises():
    original = FakeIR(value=0)
    with pytest.raises(ValidationError):
        original.value = 1
