"""ParsePass — populates Document.sections from the MarkdownParserPort.

Calls ctx.parser.parse(ir.source) to obtain a list[Section] from the
parser adapter (MarkdownItAdapter in production, FakeMarkdownParser in tests).
The pass never imports markdown_it directly — it interacts only via the port.
"""


from kir.core.domain.models.document import Document
from kir.core.passes.context import CompilerContext

from kir.compiler.documents.passes import register_pass


@register_pass("parse")
def parse_pass(ir: Document, ctx: CompilerContext) -> Document:
    """Populate Document.sections from the parser adapter.

    Calls ctx.parser.parse(ir.source) — the MarkdownParserPort call. The
    adapter (MarkdownItAdapter or a test fake) handles the actual parsing.
    Returns an immutable copy of ir with sections populated.

    No LLM calls. No direct import of MarkdownItAdapter.
    """
    sections = ctx.parser.parse(ir.source)
    return ir.model_copy(update={"sections": tuple(sections)})
