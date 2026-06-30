"""YamlFileRepository — the project's first permanent adapter: a
RepositoryPort implementation writing one YAML file per artifact (STOR-01),
to a directory kept disjoint from any raw-source directory (STOR-02).

Per the Phase 1 threat register (T-01-08): `artifact_id` is the only
externally-influenced input this phase that becomes a filesystem path
component, so it is validated against a restrictive allowlist pattern
before any Path is constructed — rejecting path-traversal characters
rather than attempting to sanitize/strip them.

Per the Phase 1 threat register (T-01-09): `ruamel.yaml.YAML(typ="safe")`
is used explicitly (not the default round-trip mode) to restrict
deserialization to plain Python types.
"""

from __future__ import annotations

import re
from pathlib import Path

import ruamel.yaml

_SAFE_ARTIFACT_ID = re.compile(r"^[A-Za-z0-9_-]+$")


class YamlFileRepository:
    def __init__(self, output_dir: Path) -> None:
        self._dir = output_dir
        self._yaml = ruamel.yaml.YAML(typ="safe")

    def _validate_artifact_id(self, artifact_id: str) -> None:
        if not _SAFE_ARTIFACT_ID.match(artifact_id):
            raise ValueError(
                f"artifact_id {artifact_id!r} is not a safe filename "
                "component (must match ^[A-Za-z0-9_-]+$)"
            )

    def save(self, artifact_id: str, artifact: object) -> None:
        self._validate_artifact_id(artifact_id)
        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._dir / f"{artifact_id}.yaml", "w") as f:
            self._yaml.dump(artifact, f)

    def load(self, artifact_id: str) -> object:
        self._validate_artifact_id(artifact_id)
        with open(self._dir / f"{artifact_id}.yaml") as f:
            return self._yaml.load(f)
