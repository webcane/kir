import pytest
from pydantic import ValidationError

from kir.core.domain.models.provenance import SourceRef
from kir.core.domain.value_objects import Checksum, ConceptId, RelationId


def test_concept_id_constructs_and_is_frozen():
    concept_id = ConceptId(value="auth")
    assert concept_id.value == "auth"
    with pytest.raises(ValidationError):
        concept_id.value = "x"


def test_concept_id_rejects_extra_fields():
    with pytest.raises(ValidationError):
        ConceptId(value="auth", extra_field="x")


def test_relation_id_constructs_and_is_frozen():
    relation_id = RelationId(value="rel-1")
    assert relation_id.value == "rel-1"
    with pytest.raises(ValidationError):
        relation_id.value = "x"


def test_concept_id_and_relation_id_are_distinct_types():
    assert ConceptId is not RelationId
    assert not isinstance(ConceptId(value="a"), RelationId)


def test_checksum_constructs_compares_equal_and_is_hashable():
    checksum = Checksum(algorithm="sha256", value="abc123")
    assert checksum.algorithm == "sha256"
    assert checksum.value == "abc123"

    other = Checksum(algorithm="sha256", value="abc123")
    assert checksum == other
    assert hash(checksum) == hash(other)

    as_dict_key = {checksum: "ok"}
    assert as_dict_key[other] == "ok"


def test_checksum_is_frozen_and_forbids_extra():
    checksum = Checksum(algorithm="sha256", value="abc123")
    with pytest.raises(ValidationError):
        checksum.value = "other"
    with pytest.raises(ValidationError):
        Checksum(algorithm="sha256", value="abc123", extra_field="x")


def test_source_ref_constructs_with_required_fields():
    ref = SourceRef(document_id="doc-1", section="intro")
    assert ref.document_id == "doc-1"
    assert ref.section == "intro"


def test_source_ref_section_defaults_to_none():
    ref = SourceRef(document_id="doc-1")
    assert ref.section is None


def test_source_ref_is_frozen_and_forbids_extra():
    ref = SourceRef(document_id="doc-1")
    with pytest.raises(ValidationError):
        ref.document_id = "doc-2"
    with pytest.raises(ValidationError):
        SourceRef(document_id="doc-1", extra_field="x")
