"""STOR-01 (one YAML file per artifact, never monolithic JSON), STOR-02
(output directory disjoint from raw-source directory), and path-traversal
artifact_id safety proofs for YamlFileRepository.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from kir.tooling.repository.yaml_repository import YamlFileRepository


def test_save_then_load_roundtrips(tmp_path: Path) -> None:
    repo = YamlFileRepository(tmp_path / "kir")
    repo.save("artifact-1", {"id": "artifact-1", "version": 1})
    assert repo.load("artifact-1") == {"id": "artifact-1", "version": 1}


def test_one_file_per_artifact(tmp_path: Path) -> None:
    output_dir = tmp_path / "kir"
    repo = YamlFileRepository(output_dir)
    repo.save("artifact-1", {"id": "artifact-1"})
    repo.save("artifact-2", {"id": "artifact-2"})

    yaml_files = list(output_dir.glob("*.yaml"))
    assert len(yaml_files) == 2


def test_output_dir_disjoint_from_raw_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "kir"
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "source.md").write_text("# Raw source\n")

    repo = YamlFileRepository(output_dir)
    repo.save("artifact-1", {"id": "artifact-1"})

    # No file written by save() appears under the raw directory.
    assert list(raw_dir.glob("*.yaml")) == []
    # The raw-source file is untouched.
    assert (raw_dir / "source.md").read_text() == "# Raw source\n"
    # The output directory and raw directory are disjoint paths.
    assert output_dir != raw_dir
    assert not output_dir.is_relative_to(raw_dir)
    assert not raw_dir.is_relative_to(output_dir)


def test_path_traversal_artifact_id_does_not_escape_output_dir(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "kir"
    repo = YamlFileRepository(output_dir)

    with pytest.raises(ValueError, match="artifact_id"):
        repo.save("../../etc/passwd", {"malicious": True})

    # No file was written outside the configured output directory.
    assert not (tmp_path / "etc").exists()
    assert not (tmp_path.parent / "etc").exists()


def test_path_traversal_artifact_id_rejected_on_load(tmp_path: Path) -> None:
    output_dir = tmp_path / "kir"
    repo = YamlFileRepository(output_dir)

    with pytest.raises(ValueError, match="artifact_id"):
        repo.load("../../etc/passwd")
