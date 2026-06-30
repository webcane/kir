"""PassRegistry — decorator-friendly self-registration plus build-time,
graphlib.TopologicalSorter-based dependency-ordered pipeline construction.

Per D-02: `register()` never validates `depends_on` — import order may
mean a dependency hasn't registered yet. Only `pipeline()` validates the
full dependency graph, at build time, raising a clearly named error
(`MissingDependencyError` or `graphlib.CycleError`) that names the
missing pass or the cycle members.
"""

from __future__ import annotations

from graphlib import CycleError, TopologicalSorter

from kir.core.passes.base import Pass


class MissingDependencyError(ValueError):
    """Raised at pipeline() build time when a pass declares depends_on
    naming a pass that was never registered. Per D-02, this is NOT
    raised at register() time."""


class PassRegistry:
    def __init__(self) -> None:
        self._passes: dict[str, Pass] = {}

    def register(self, pass_obj: Pass) -> Pass:
        # Registration itself never validates depends_on (D-02) —
        # import order may mean a dependency hasn't registered yet.
        self._passes[pass_obj.name] = pass_obj
        return pass_obj

    def pipeline(self) -> list[Pass]:
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
