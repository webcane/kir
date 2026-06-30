import pytest
from pydantic import ValidationError

from kir.core.domain.models.concept import Concept
from kir.core.domain.models.provenance import SourceRef
from kir.core.domain.value_objects import ConceptId


def test_concept_constructs_with_defaults():
    concept = Concept(id=ConceptId(value="auth"), canonical_name="Authentication")
    assert concept.id == ConceptId(value="auth")
    assert concept.canonical_name == "Authentication"
    assert concept.aliases == ()
    assert concept.definition is None
    assert concept.category is None
    assert concept.provenance == ()


def test_concept_constructs_with_all_fields():
    ref = SourceRef(document_id="doc-1")
    concept = Concept(
        id=ConceptId(value="auth"),
        canonical_name="Authentication",
        aliases=["AuthN", "Auth"],
        definition="The process of verifying identity",
        category="security",
        provenance=[ref],
    )
    assert isinstance(concept.aliases, tuple)
    assert concept.aliases == ("AuthN", "Auth")
    assert isinstance(concept.provenance, tuple)
    assert concept.provenance == (ref,)


def test_concept_is_frozen_and_forbids_extra():
    concept = Concept(id=ConceptId(value="auth"), canonical_name="Authentication")
    with pytest.raises(ValidationError):
        concept.canonical_name = "Other"
    with pytest.raises(ValidationError):
        Concept(
            id=ConceptId(value="auth"),
            canonical_name="Authentication",
            extra_field="x",
        )
