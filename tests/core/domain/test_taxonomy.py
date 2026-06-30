import pytest
from pydantic import ValidationError

from kir.core.domain.models.taxonomy import Taxonomy


def test_taxonomy_constructs():
    taxonomy = Taxonomy(path=["root", "security"], label="Security")
    assert isinstance(taxonomy.path, tuple)
    assert taxonomy.path == ("root", "security")
    assert taxonomy.label == "Security"


def test_taxonomy_is_frozen_and_forbids_extra():
    taxonomy = Taxonomy(path=["root"], label="Root")
    with pytest.raises(ValidationError):
        taxonomy.label = "Other"
    with pytest.raises(ValidationError):
        Taxonomy(path=["root"], label="Root", extra_field="x")
