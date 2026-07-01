"""tests.core.passes.fakes: fake pass/port implementations.

Importing this package imports every fake module so that decorator-based
registration (fake_passes.py's @register_pass) always fires, regardless of
test collection order (RESEARCH.md Pitfall 1 mitigation — mandatory).
"""

from tests.core.passes.fakes import (  # noqa: F401
    fake_cache,
    fake_llm_port,
    fake_parser,
    fake_passes,
    fake_repository,
)
