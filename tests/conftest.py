"""Shared pytest fixtures for the kir test suite.

This file exists from Wave 0 so pytest's rootdir-relative conftest discovery
is established before any fixtures are added. Plan 04 adds
`fake_compiler_context` (a CompilerContext built from fake ports) and
`fake_registry` (a fresh PassRegistry with fake_pass_a/fake_pass_b
registered, constructed per-test to avoid cross-test interference).
"""

from __future__ import annotations

import pytest

from kir.core.config.versions import compiler_version, schema_version
from kir.core.passes.context import CompilerContext
from kir.core.passes.registry import PassRegistry
from tests.core.passes.fakes.fake_llm_port import FakeLLMPort
from tests.core.passes.fakes.fake_parser import FakeMarkdownParser
from tests.core.passes.fakes.fake_passes import fake_pass_a, fake_pass_b
from tests.core.passes.fakes.fake_repository import InMemoryFakeRepository


@pytest.fixture
def fake_compiler_context() -> CompilerContext:
    """A CompilerContext constructed from fake ports — proves CompilerContext
    + ports + passes compose end-to-end without any domain/pass code change."""
    return CompilerContext(
        llm=FakeLLMPort(),
        repository=InMemoryFakeRepository(),
        parser=FakeMarkdownParser(),
        compiler_version=compiler_version,
        schema_version=schema_version,
    )


@pytest.fixture
def fake_registry() -> PassRegistry:
    """A fresh PassRegistry with fake_pass_a/fake_pass_b registered.

    Constructed fresh per test (rather than reusing the shared module-level
    registry in fake_passes.py) to avoid cross-test interference.
    """
    registry = PassRegistry()
    registry.register(fake_pass_a)
    registry.register(fake_pass_b)
    return registry


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Treat "no tests collected" as success, not failure.

    Wave 0 (this plan) intentionally ships zero tests — `uv run pytest` must
    exit 0 to prove the toolchain/layout/discovery baseline works before any
    domain code exists. Pytest's own convention for zero tests collected is
    exit code 5 (NO_TESTS_COLLECTED), not 0, so it is normalized here. Once
    later plans add real tests, this hook has no effect (exit code stays
    whatever pytest reports for an actual test run).
    """
    if exitstatus == pytest.ExitCode.NO_TESTS_COLLECTED:
        session.exitstatus = pytest.ExitCode.OK
