"""SectionPass — normalizes section content (strips leading/trailing whitespace).

This is a pure normalization pass that does not change headings or add/remove
sections. It depends on parse (sections must be populated first).
"""


from kir.core.domain.models.document import Document, Section
from kir.core.passes.context import CompilerContext

from kir.compiler.documents.passes import register_pass


@register_pass("section", depends_on=("parse",))
def section_pass(ir: Document, ctx: CompilerContext) -> Document:
    """Normalize section content by stripping whitespace.

    Trims leading and trailing whitespace from each section's content.
    Headings and section count remain unchanged.

    Args:
        ir: Document IR with sections populated by parse pass.
        ctx: CompilerContext (not used by this pass).

    Returns:
        Immutable Document copy with normalized (whitespace-stripped) sections.
    """
    normalized = tuple(
        Section(heading=s.heading, content=s.content.strip()) for s in ir.sections
    )
    return ir.model_copy(update={"sections": normalized})
