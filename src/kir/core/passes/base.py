"""Pass Protocol — the structural contract every compiler pass satisfies.

A pass is any object exposing `name`, `depends_on`, and a callable
`__call__(ir, ctx) -> ir`. No inheritance is required — passes are
plain functions or callables decorated to attach `name`/`depends_on`
attributes (see `PassRegistry`).
"""

from typing import Protocol


class Pass(Protocol):
    """Structural contract every compiler pass satisfies.

    Passes can be plain functions or callables (no inheritance required);
    attributes are attached via decorators or the registry mechanism.
    """

    name: str
    depends_on: tuple[str, ...]

    def __call__(self, ir: object, ctx: "CompilerContext") -> object:
        """Execute the pass on the input IR.

        Args:
            ir: Input IR to transform.
            ctx: CompilerContext providing access to ports and metadata.

        Returns:
            Transformed IR (typically an immutable copy with fields updated).
        """
        ...
