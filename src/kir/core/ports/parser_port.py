"""MarkdownParserPort — domain-owned port for parsing raw Markdown source."""

from typing import Protocol

from kir.core.domain.models.document import Section


class MarkdownParserPort(Protocol):
    def parse(self, text: str) -> list[Section]: ...
