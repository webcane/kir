"""fake_pass_a / fake_pass_b — two fake CompilerPass implementations exercising
a real dependency graph (fake_pass_b depends_on fake_pass_a), registered into a
module-level PassRegistry via the register_pass decorator.

Per RESEARCH.md Pitfall 1: decorator registration only fires on import, so
`tests/core/passes/fakes/__init__.py` must import this module unconditionally
to guarantee registration regardless of test collection order.
"""

from __future__ import annotations

from kir.core.domain.ir import FakeIR
from kir.core.domain.models.diagnostic import Diagnostic, Severity
from kir.core.passes.registry import PassRegistry

registry = PassRegistry()


def register_pass(name: str, depends_on: tuple[str, ...] = ()):
    def decorator(fn):
        fn.name = name
        fn.depends_on = depends_on
        registry.register(fn)
        return fn

    return decorator


@register_pass("fake_a")
def fake_pass_a(ir: FakeIR, ctx: object) -> FakeIR:
    return ir.model_copy(
        update={
            "value": ir.value + 1,
            "diagnostics": ir.diagnostics
            + (
                Diagnostic(
                    code="FAKE_A",
                    severity=Severity.INFO,
                    message="fake_pass_a ran",
                ),
            ),
        }
    )


@register_pass("fake_b", depends_on=("fake_a",))
def fake_pass_b(ir: FakeIR, ctx: object) -> FakeIR:
    return ir.model_copy(
        update={
            "value": ir.value + 1,
            "diagnostics": ir.diagnostics
            + (
                Diagnostic(
                    code="FAKE_B",
                    severity=Severity.INFO,
                    message="fake_pass_b ran",
                ),
            ),
        }
    )
