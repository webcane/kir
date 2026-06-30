"""FakeLLMPort — trivial, no-network implementation of LLMPort for tests."""

from __future__ import annotations


class FakeLLMPort:
    def extract(self, text: str) -> object:
        return {"text": text}
