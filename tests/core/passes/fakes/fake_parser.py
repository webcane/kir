"""FakeMarkdownParser — trivial implementation of MarkdownParserPort for tests."""

from kir.core.domain.models.document import Section

class FakeMarkdownParser:
    def parse(self, text: str) -> list[Section]:
        return [Section(heading="fake", content=text)]
