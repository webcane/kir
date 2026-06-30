"""PromptRegistry — loads versioned extraction prompt templates by name.

Follows the same explicit-error-class convention as MissingDependencyError
in core/passes/registry.py: a missing prompt file raises a named
PromptNotFoundError (subclass of FileNotFoundError), never a bare IOError
or a generic exception.

Prompt versioning scheme (RESEARCH.md Pattern 6): simple integer embedded in
the filename (extract_v1.md, extract_v2.md, ...). The version string "1", "2"
etc. is the prompt_version component of the LLM-02 cache key. Changing any
prompt content = rename/add a file + bump the prompt_version constant in
core/config/versions.py.
"""

from __future__ import annotations

from pathlib import Path


class PromptNotFoundError(FileNotFoundError):
    """Raised when a requested prompt template file does not exist.

    Follows the explicit-error-class convention: callers can catch this
    specifically (rather than catching the broader FileNotFoundError) if they
    want to produce a structured Diagnostic vs. hard-failing.
    """


class PromptRegistry:
    """Loads versioned prompt Markdown templates and interpolates kwargs.

    Default prompts directory is the sibling directory of this module file
    (i.e. ``src/kir/llm/prompts/``), so ``render("extract_v1")`` loads
    ``src/kir/llm/prompts/extract_v1.md`` without any configuration.

    A custom ``prompts_dir`` can be injected (e.g. in tests with ``tmp_path``)
    to load alternative templates.
    """

    def __init__(self, prompts_dir: Path | None = None) -> None:
        self._dir: Path = prompts_dir if prompts_dir is not None else Path(__file__).parent

    def render(self, name: str, **kwargs: object) -> str:
        """Load a prompt template by name and interpolate keyword arguments.

        Args:
            name: Template name without extension (e.g. "extract_v1").
            **kwargs: Variables to interpolate via str.format(**kwargs).

        Returns:
            The rendered prompt string.

        Raises:
            PromptNotFoundError: If ``{name}.md`` does not exist in prompts_dir.
            KeyError: If the template contains a placeholder not supplied via kwargs.
        """
        path = self._dir / f"{name}.md"
        if not path.exists():
            raise PromptNotFoundError(
                f"Prompt template not found: {path!s}"
            )
        template = path.read_text(encoding="utf-8")
        return template.format(**kwargs)
