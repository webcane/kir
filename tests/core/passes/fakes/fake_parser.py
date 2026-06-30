"""FakeMarkdownParser — trivial implementation of MarkdownParserPort for tests."""

from __future__ import annotations


class FakeMarkdownParser:
    def parse(self, text: str) -> object:
        return {"raw": text}
