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
    """Parse document source into logical sections.

    Calls the MarkdownParserPort to decompose the raw source into a sequence
    of Section objects (heading + content pairs).

    Args:
        ir: Document IR with source populated, sections empty.
        ctx: CompilerContext providing the MarkdownParserPort.

    Returns:
        Immutable Document copy with sections populated from parsing.
    """
    sections = ctx.parser.parse(ir.source)
    return ir.model_copy(update={"sections": tuple(sections)})
