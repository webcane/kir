import pytest
from pydantic import ValidationError

from kir.core.domain.manifest import ArtifactManifest


def test_artifact_manifest_constructs():
    manifest = ArtifactManifest(artifact_id="doc-1", version=1)
    assert manifest.artifact_id == "doc-1"
    assert manifest.version == 1


def test_artifact_manifest_has_only_id_and_version_fields():
    assert set(ArtifactManifest.model_fields.keys()) == {"artifact_id", "version"}


def test_artifact_manifest_is_frozen_and_forbids_extra():
    manifest = ArtifactManifest(artifact_id="doc-1", version=1)
    with pytest.raises(ValidationError):
        manifest.version = 2
    with pytest.raises(ValidationError):
        ArtifactManifest(artifact_id="doc-1", version=1, extra_field="x")
