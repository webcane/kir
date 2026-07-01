"""Pass Protocol — the structural contract every compiler pass satisfies.

A pass is any object exposing `name`, `depends_on`, and a callable
`__call__(ir, ctx) -> ir`. No inheritance is required — passes are
plain functions or callables decorated to attach `name`/`depends_on`
attributes (see `PassRegistry`).
"""

from typing import Protocol


class Pass(Protocol):
    name: str
    depends_on: tuple[str, ...]

    def __call__(self, ir: object, ctx: "CompilerContext") -> object: ...
