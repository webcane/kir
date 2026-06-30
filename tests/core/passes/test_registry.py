"""Tests for PassRegistry: build-time-only dependency validation (D-02),
graphlib.TopologicalSorter-based dependency ordering, cycle/missing-dependency
detection, and the EXT-01 no-edit-existing-files extensibility proof.
"""

from __future__ import annotations

from graphlib import CycleError

import pytest

from kir.core.passes.registry import MissingDependencyError, PassRegistry


def _fake_pass(name: str, depends_on: tuple[str, ...] = ()):
    def fn(ir: object, ctx: object) -> object:
        return ir

    fn.name = name
    fn.depends_on = depends_on
    return fn


@pytest.fixture
def registry() -> PassRegistry:
    return PassRegistry()


def test_register_with_unregistered_dependency_does_not_raise(
    registry: PassRegistry,
) -> None:
    # D-02: registration itself must NOT validate depends_on.
    registry.register(_fake_pass("a", depends_on=("nonexistent",)))


def test_missing_dependency_detected_at_pipeline_build_time_not_register(
    registry: PassRegistry,
) -> None:
    registry.register(_fake_pass("a", depends_on=("nonexistent",)))
    with pytest.raises(MissingDependencyError, match="nonexistent"):
        registry.pipeline()


def test_circular_dependency_detected_at_pipeline_build_time(
    registry: PassRegistry,
) -> None:
    registry.register(_fake_pass("a", depends_on=("b",)))
    registry.register(_fake_pass("b", depends_on=("a",)))
    with pytest.raises(CycleError):
        registry.pipeline()


def test_pipeline_returns_dependency_ordered_passes(registry: PassRegistry) -> None:
    # Register out of dependency order on purpose.
    registry.register(_fake_pass("c", depends_on=("a", "b")))
    registry.register(_fake_pass("b", depends_on=("a",)))
    registry.register(_fake_pass("a"))

    ordered = registry.pipeline()
    names = [p.name for p in ordered]

    assert names.index("a") < names.index("b")
    assert names.index("a") < names.index("c")
    assert names.index("b") < names.index("c")


def test_ext01_new_pass_registered_in_this_file_appears_in_pipeline(
    registry: PassRegistry,
) -> None:
    # EXT-01 proof: a brand-new pass, defined entirely within this test
    # file (not by editing registry.py/base.py/context.py), can be
    # registered and correctly appears in pipeline() output.
    def third_party_pass(ir: object, ctx: object) -> object:
        return ir

    third_party_pass.name = "third_party"
    third_party_pass.depends_on = ()

    registry.register(third_party_pass)

    ordered = registry.pipeline()
    assert any(p.name == "third_party" for p in ordered)
