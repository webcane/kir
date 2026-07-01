"""MarkdownParserPort — domain-owned port for parsing raw Markdown source."""

from typing import Protocol

from kir.core.domain.models.document import Section


class MarkdownParserPort(Protocol):
    """Port for parsing raw Markdown source into logical sections.

    The implementation (e.g., MarkdownItAdapter) is an interchangeable detail
    behind this Protocol — never a domain dependency.
    """

    def parse(self, text: str) -> list[Section]:
        """Parse Markdown text into logical sections.

        Args:
            text: Raw Markdown source to parse.

        Returns:
            List of Section objects (heading + content pairs).
        """
        ...
