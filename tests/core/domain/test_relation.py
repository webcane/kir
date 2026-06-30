import pytest
from pydantic import ValidationError

from kir.core.domain.models.relation import Relation
from kir.core.domain.value_objects import ConceptId, RelationId


def test_relation_constructs_with_defaults():
    relation = Relation(
        id=RelationId(value="rel-1"),
        relation_type="related_to",
        source_concept_id=ConceptId(value="auth"),
        target_concept_id=ConceptId(value="authz"),
    )
    assert relation.relation_type == "related_to"
    assert relation.provenance == ()


def test_relation_type_is_plain_string_not_enum():
    relation = Relation(
        id=RelationId(value="rel-1"),
        relation_type="depends_on",
        source_concept_id=ConceptId(value="auth"),
        target_concept_id=ConceptId(value="authz"),
    )
    assert isinstance(relation.relation_type, str)
    # Arbitrary, not-yet-canonical vocabulary words must be accepted —
    # the vocabulary is core-and-extensible, not a closed enum this phase.
    arbitrary = Relation(
        id=RelationId(value="rel-2"),
        relation_type="authenticates_with",
        source_concept_id=ConceptId(value="auth"),
        target_concept_id=ConceptId(value="authz"),
    )
    assert arbitrary.relation_type == "authenticates_with"


def test_relation_is_frozen_and_forbids_extra():
    relation = Relation(
        id=RelationId(value="rel-1"),
        relation_type="related_to",
        source_concept_id=ConceptId(value="auth"),
        target_concept_id=ConceptId(value="authz"),
    )
    with pytest.raises(ValidationError):
        relation.relation_type = "other"
    with pytest.raises(ValidationError):
        Relation(
            id=RelationId(value="rel-1"),
            relation_type="related_to",
            source_concept_id=ConceptId(value="auth"),
            target_concept_id=ConceptId(value="authz"),
            extra_field="x",
        )
