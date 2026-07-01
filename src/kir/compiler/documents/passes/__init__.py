"""Document-compiler PassRegistry and register_pass decorator.

document_registry is the module-level PassRegistry instance for all document-compiler
passes. It is distinct from any core PassRegistry used in Phase 1 tests — this registry
owns only the deterministic document passes (parse, section, metadata) and the
async extraction pass (extract_concepts, added in Plan 04).

The forced imports at the bottom of this module ensure decorator registration fires
regardless of test collection order (per RESEARCH.md Pitfall 3 — import order).
"""

from __future__ import annotations

from kir.core.passes.registry import PassRegistry

document_registry = PassRegistry()


def register_pass(name: str, depends_on: tuple[str, ...] = ()):
    """Decorator that registers a document-compiler pass into document_registry.

    Mirrors the pattern in tests/core/passes/fakes/fake_passes.py but registers
    into document_registry (not a test-only registry).

    Args:
        name: Unique name for the pass, used to identify it in the dependency graph.
        depends_on: Tuple of pass names this pass depends on. Validated at
                    pipeline() build time, not at register time (D-02).
    """

    def decorator(fn):  # type: ignore[no-untyped-def]
        fn.name = name
        fn.depends_on = depends_on
        document_registry.register(fn)
        return fn

    return decorator


# Force-import all pass modules to ensure decorator registration fires.
from . import parse, section, metadata, extract_concepts  # noqa: E402, F401
