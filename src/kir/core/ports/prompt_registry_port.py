"""PromptRegistryPort — minimal protocol for prompt template loading (WR-04).

Satisfies the hexagonal boundary: ExtractConceptsPass and CompilerContext
depend on this protocol, never on the concrete PromptRegistry in kir.llm.
"""

from typing import Protocol


class PromptRegistryPort(Protocol):
    """Port for rendering prompt templates with variable substitution.

    The concrete prompt registry implementation (file-based, database-backed, etc.)
    is an interchangeable detail behind this Protocol.
    """

    def render(self, name: str, **kwargs: object) -> str:
        """Render a prompt template with the given variables.

        Args:
            name: Name/identifier of the prompt template (e.g., "extract_v1").
            **kwargs: Template variables to substitute in the prompt.

        Returns:
            Rendered prompt string with variables substituted.
        """
        ...
