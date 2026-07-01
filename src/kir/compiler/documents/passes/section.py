"""SectionPass — normalizes section content (strips leading/trailing whitespace).

This is a pure normalization pass that does not change headings or add/remove
sections. It depends on parse (sections must be populated first).
"""


from kir.core.domain.models.document import Document, Section
from kir.core.passes.context import CompilerContext

from kir.compiler.documents.passes import register_pass


@register_pass("section", depends_on=("parse",))
def section_pass(ir: Document, ctx: CompilerContext) -> Document:
    """Normalize section content — strip leading/trailing whitespace.

    Iterates over ir.sections and strips each Section's content.
    Returns an immutable copy of ir with normalized sections.

    This pass does not modify headings or change the number of sections.
    """
    normalized = tuple(
        Section(heading=s.heading, content=s.content.strip()) for s in ir.sections
    )
    return ir.model_copy(update={"sections": normalized})
