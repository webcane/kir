import pytest
from pydantic import ValidationError

from kir.core.domain.models.conflict import Conflict
from kir.core.domain.value_objects import ConceptId


def test_conflict_constructs_with_defaults():
    conflict = Conflict(
        id="conflict-1",
        conflict_type="definition_mismatch",
        description="Two definitions disagree",
    )
    assert conflict.concept_ids == ()


def test_conflict_constructs_with_concept_ids():
    conflict = Conflict(
        id="conflict-1",
        conflict_type="definition_mismatch",
        description="Two definitions disagree",
        concept_ids=[ConceptId(value="auth"), ConceptId(value="authz")],
    )
    assert isinstance(conflict.concept_ids, tuple)
    assert conflict.concept_ids == (ConceptId(value="auth"), ConceptId(value="authz"))


def test_conflict_is_frozen_and_forbids_extra():
    conflict = Conflict(
        id="conflict-1",
        conflict_type="definition_mismatch",
        description="Two definitions disagree",
    )
    with pytest.raises(ValidationError):
        conflict.description = "Other"
    with pytest.raises(ValidationError):
        Conflict(
            id="conflict-1",
            conflict_type="definition_mismatch",
            description="Two definitions disagree",
            extra_field="x",
        )
