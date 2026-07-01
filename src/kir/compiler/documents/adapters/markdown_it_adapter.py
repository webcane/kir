"""MarkdownItAdapter — the ONLY file in the kir package that imports markdown_it.

Adapter boundary: this module wraps markdown-it-py's token-stream API and converts
it into the domain type list[Section]. Passes and core code call this via the
MarkdownParserPort protocol (ctx.parser.parse(text)) and never see markdown_it types.

Per the Phase 2 threat register (T-02-06): no other file in kir.compiler or kir.core
may import markdown_it. The acceptance_criteria grep gate enforces this at CI time.
"""


from markdown_it import MarkdownIt

from kir.core.domain.models.document import Section


class MarkdownItAdapter:
    """Implements MarkdownParserPort by splitting Markdown text into Sections at every
    heading level (H1–H6). Content before the first heading becomes a preamble Section
    with heading='' per D-01.

    The only file in kir that imports markdown_it — callers interact with the
    MarkdownParserPort protocol only.
    """

    def __init__(self) -> None:
        self._md = MarkdownIt()

    def parse(self, text: str) -> list[Section]:
        """Parse Markdown text into a list of Sections.

        Any content before the first heading becomes a preamble Section with
        heading=''. Each H1–H6 heading starts a new Section. Trailing empty
        sections (no heading and no content) are discarded.

        Args:
            text: Raw Markdown source text.

        Returns:
            A list of Section objects. Returns [Section(heading='', content='')] for
            blank input, or a single preamble section if text has no headings.
        """
        if not text or not text.strip():
            return []

        tokens = self._md.parse(text)

        sections: list[Section] = []
        current_heading: str = ""
        current_content_parts: list[str] = []
        in_heading: bool = False

        def _flush() -> None:
            """Append the current accumulated section to sections if non-empty."""
            content = "\n\n".join(current_content_parts).strip()
            if current_heading or content:
                sections.append(Section(heading=current_heading, content=content))

        for token in tokens:
            if token.type == "heading_open":
                # Save the previous section before starting a new one.
                _flush()
                current_heading = ""
                current_content_parts = []
                in_heading = True
            elif token.type == "heading_close":
                in_heading = False
            elif token.type == "inline":
                if in_heading:
                    # The inline token immediately after heading_open is the heading text.
                    current_heading = token.content
                else:
                    # Body inline content (paragraph_open / inline / paragraph_close groups).
                    if token.content:
                        current_content_parts.append(token.content)
            # All other token types (paragraph_open, paragraph_close, fence, hr, etc.)
            # are structural and do not contribute visible content directly — their
            # inline children carry the actual text.

        # Flush the final section.
        _flush()

        return sections
