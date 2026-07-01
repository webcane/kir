"""PromptRegistryPort — minimal protocol for prompt template loading (WR-04).

Satisfies the hexagonal boundary: ExtractConceptsPass and CompilerContext
depend on this protocol, never on the concrete PromptRegistry in kir.llm.
"""

from typing import Protocol


class PromptRegistryPort(Protocol):
    def render(self, name: str, **kwargs: object) -> str: ...
