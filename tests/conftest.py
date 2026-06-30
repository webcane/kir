"""Shared pytest fixtures for the kir test suite.

Fixtures are added in Plan 04 (fake_compiler_context, fake_registry, and a
tmp_path-based repository fixture). This file exists from Wave 0 so pytest's
rootdir-relative conftest discovery is established before any fixtures are
added — later plans only add fixtures here, never create this file.
"""

import pytest


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
