"""PassRegistry — decorator-friendly self-registration plus build-time,
graphlib.TopologicalSorter-based dependency-ordered pipeline construction.

Per D-02: `register()` never validates `depends_on` — import order may
mean a dependency hasn't registered yet. Only `pipeline()` validates the
full dependency graph, at build time, raising a clearly named error
(`MissingDependencyError` or `graphlib.CycleError`) that names the
missing pass or the cycle members.
"""


from graphlib import CycleError, TopologicalSorter

from kir.core.passes.base import Pass


class MissingDependencyError(ValueError):
    """Raised when a pass references an unregistered dependency.

    Raised at pipeline() build time (not at register() time) when a pass
    declares depends_on naming a pass that was never registered (D-02).
    """


class PassRegistry:
    """Registry for compiler passes with dependency-ordered pipeline construction.

    Provides decorator-friendly registration and build-time topological sorting
    of passes via graphlib.TopologicalSorter. Validation occurs only at
    pipeline() build time, not at register() time, to accommodate import order.
    """

    def __init__(self) -> None:
        """Initialize an empty pass registry."""
        self._passes: dict[str, Pass] = {}

    def register(self, pass_obj: Pass) -> Pass:
        """Register a pass for inclusion in the pipeline.

        Does not validate depends_on at this point (D-02); validation occurs
        only at pipeline() build time. Returns the pass unchanged for use as
        a decorator.

        Args:
            pass_obj: Pass object with name and depends_on attributes.

        Returns:
            The same pass_obj, unchanged.
        """
        # Registration itself never validates depends_on (D-02) —
        # import order may mean a dependency hasn't registered yet.
        self._passes[pass_obj.name] = pass_obj
        return pass_obj

    def pipeline(self) -> list[Pass]:
        """Build a topologically-sorted pipeline of all registered passes.

        Validates that all declared dependencies are registered and that no
        cycles exist. Raises MissingDependencyError or CycleError on validation
        failure.

        Returns:
            List of passes in dependency order (all transitive dependencies
            resolved, ready for execution).

        Raises:
            MissingDependencyError: If a pass depends on an unregistered pass.
            CycleError: If pass dependencies form a cycle.
        """
        graph: dict[str, set[str]] = {}
        for name, p in self._passes.items():
            for dep in p.depends_on:
                if dep not in self._passes:
                    raise MissingDependencyError(
                        f"Pass {name!r} declares depends_on={dep!r}, "
                        f"but no pass named {dep!r} is registered."
                    )
            graph[name] = set(p.depends_on)
        try:
            sorter = TopologicalSorter(graph)
            ordered_names = list(sorter.static_order())
        except CycleError as exc:
            # exc.args[1] is the list of nodes forming the cycle (CPython docs).
            # Preserve it on the re-raised exception so callers can still
            # read .args[1]; only args[0] (the message) gains our context.
            raise CycleError(
                f"Circular pass dependency detected: {exc.args[1]}", exc.args[1]
            ) from exc
        return [self._passes[name] for name in ordered_names]
