"""FakeLLMPort — trivial, no-network implementation of LLMPort for tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kir.core.domain.models.document import Section


class FakeLLMPort:
    model_id: str = "fake:v0"

    async def extract(self, *, sections: list[Section], prompt: str) -> object:
        return {"sections": [s.heading for s in sections], "prompt": prompt}
