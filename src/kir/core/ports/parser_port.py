"""MarkdownParserPort — domain-owned port for parsing raw Markdown source."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from kir.core.domain.models.document import Section


class MarkdownParserPort(Protocol):
    def parse(self, text: str) -> list[Section]: ...
