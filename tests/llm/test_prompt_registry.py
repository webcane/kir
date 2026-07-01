"""Unit tests for PromptRegistry and PromptNotFoundError."""

from __future__ import annotations

import pytest

from kir.llm.prompts.registry import PromptNotFoundError, PromptRegistry


class TestPromptRegistry:
    def test_render_extract_v1_returns_non_empty_string(self) -> None:
        text = PromptRegistry().render("extract_v1", sections="# Test\n\nSome content.")
        assert isinstance(text, str)
        assert len(text) > 0

    def test_render_unknown_prompt_raises_not_found(self) -> None:
        with pytest.raises(PromptNotFoundError):
            PromptRegistry().render("nonexistent_v99")

    def test_render_with_custom_prompts_dir(self, tmp_path: object) -> None:
        from pathlib import Path

        d = Path(tmp_path)  # type: ignore[arg-type]
        (d / "test.md").write_text("hello {greeting}", encoding="utf-8")
        result = PromptRegistry(d).render("test", greeting="world")
        assert result == "hello world"

    def test_render_missing_placeholder_raises(self, tmp_path: object) -> None:
        from pathlib import Path

        d = Path(tmp_path)  # type: ignore[arg-type]
        (d / "needs_var.md").write_text("value: {missing_var}", encoding="utf-8")
        with pytest.raises(KeyError):
            PromptRegistry(d).render("needs_var")
