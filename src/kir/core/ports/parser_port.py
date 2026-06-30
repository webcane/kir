"""MarkdownParserPort — domain-owned port for parsing raw Markdown source."""

from __future__ import annotations

from typing import Protocol


class MarkdownParserPort(Protocol):
    def parse(self, text: str) -> object: ...
