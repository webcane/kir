"""ExtractConceptsPass — async LLM-backed extraction pass (D-02, D-03).

This pass is the only document-compiler pass that is async: it calls
ctx.llm.extract() which performs a structured-output LLM call.

Cache integration (LLM-02): before invoking the LLM, the pass checks
ctx.llm_cache using the four-part key (checksum + prompt_version +
schema_version + model_id). On a hit it returns the cached result without
touching the LLM. On a miss it calls ctx.llm.extract(), writes the result
to the cache, then returns it.

D-03 failure handling: if ctx.llm.extract() raises (e.g. PydanticAI's
output_retries are exhausted), the exception is caught, a Diagnostic with
code='extraction-failed' is appended to the IR, and the pass returns an
otherwise-unmodified Document. The pipeline does NOT halt.

Boundary rule: this file must NOT import from kir.llm — the LLM adapter is
accessed exclusively via ctx.llm (LLMPort) and ctx.llm_cache (LLMCachePort).
"""

from kir.core.domain.models.diagnostic import Diagnostic, Severity
from kir.core.domain.models.document import Document, Section
from kir.core.passes.context import CompilerContext

from kir.compiler.documents.passes import register_pass


def _sections_to_text(sections: tuple[Section, ...]) -> str:
    """Render sections as readable Markdown text for the extraction prompt.

    Each section is rendered as its heading (if any) followed by its content,
    separated by blank lines. This produces the readable document text the LLM
    expects — not Python object repr.
    """
    parts: list[str] = []
    for s in sections:
        if s.heading:
            parts.append(f"## {s.heading}\n\n{s.content}")
        else:
            parts.append(s.content)
    return "\n\n".join(parts)


def _apply_extraction(ir: Document, result: object) -> Document:
    """Map a DocumentExtractionOutput onto the Document IR.

    Extracts the string fields from each DTO and stores them as tuples of
    strings in the Document's tuple[str, ...] fields. The Document model
    types are still tuple[str, ...] (Phase 1 placeholders) — the phase 2
    extraction pass populates them with DTO-derived strings, not DTO objects.

    Args:
        ir: The current Document IR.
        result: A DocumentExtractionOutput (typed as object to honour the
                LLMPort seam — this file never imports pydantic_ai or the
                concrete DTO classes directly).

    Returns:
        An immutable copy of ir with concepts, glossary, entities, and
        references populated.
    """
    concepts: tuple[str, ...] = tuple(c.name for c in result.concepts)  # type: ignore[attr-defined]
    glossary: tuple[str, ...] = tuple(g.term for g in result.glossary)  # type: ignore[attr-defined]
    entities: tuple[str, ...] = tuple(e.name for e in result.entities)  # type: ignore[attr-defined]
    references: tuple[str, ...] = tuple(r.target for r in result.references)  # type: ignore[attr-defined]
    return ir.model_copy(
        update={
            "concepts": concepts,
            "glossary": glossary,
            "entities": entities,
            "references": references,
        }
    )


@register_pass("extract_concepts", depends_on=("parse", "section", "metadata"))
async def extract_concepts_pass(ir: Document, ctx: CompilerContext) -> Document:
    """Async LLM-backed extraction pass — populates concepts, glossary, entities, references.

    Steps:
    1. Render extraction prompt via ctx.prompts.render().
    2. Check LLM cache (ctx.llm_cache) — return cached result immediately on a hit.
    3. Call ctx.llm.extract() — on failure write a Diagnostic (D-03) and return.
    4. Write the fresh result to the cache.
    5. Apply the extraction to the Document IR via _apply_extraction().

    If ctx.prompts or ctx.llm_cache is None (not configured), the pass returns
    the Document unmodified rather than crashing — callers that need extraction
    must supply both via CompilerContext.

    Args:
        ir: Document IR (sections, checksum, id, title already populated by
            parse/section/metadata passes).
        ctx: CompilerContext carrying llm, llm_cache, prompts, prompt_version,
             schema_version.

    Returns:
        An immutable Document copy with concepts/glossary/entities/references
        populated, or with a Diagnostic appended if LLM extraction failed,
        or unmodified if prompts/llm_cache are not configured.
    """
    # Guard: skip gracefully if Phase 2 deps are not wired in the context
    if ctx.prompts is None or ctx.llm_cache is None:
        return ir

    # Step 1: render prompt with readable section text (not Python repr)
    sections_text = _sections_to_text(ir.sections)
    prompt: str = ctx.prompts.render("extract_v1", sections=sections_text)

    # Step 2: cache check
    cached = ctx.llm_cache.get(
        checksum=ir.checksum.value,
        prompt_version=ctx.prompt_version,
        schema_version=ctx.schema_version,
        model_id=ctx.llm.model_id,
    )
    if cached is not None:
        return _apply_extraction(ir, cached)

    # Step 3: LLM call with D-03 failure handling
    try:
        result = await ctx.llm.extract(sections=list(ir.sections), prompt=prompt)
    except Exception as exc:  # noqa: BLE001
        return ir.model_copy(
            update={
                "diagnostics": ir.diagnostics
                + (
                    Diagnostic(
                        code="extraction-failed",
                        severity=Severity.ERROR,
                        message=f"LLM extraction failed after retries: {exc}",
                    ),
                )
            }
        )

    # Step 4: cache the result
    ctx.llm_cache.set(
        checksum=ir.checksum.value,
        prompt_version=ctx.prompt_version,
        schema_version=ctx.schema_version,
        model_id=ctx.llm.model_id,
        value=result,
    )

    # Step 5: apply extraction to Document IR
    return _apply_extraction(ir, result)
