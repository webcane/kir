"""tests.core.passes.fakes: fake pass/port implementations.

This explicit __init__.py exists so that later plans can import every fake
pass module here, ensuring decorator-based self-registration always fires
regardless of test collection order (see 01-RESEARCH.md Pitfall 1). No fake
implementations exist yet — fake_passes.py, fake_llm_port.py,
fake_repository.py, and fake_parser.py are added in a later plan.
"""
