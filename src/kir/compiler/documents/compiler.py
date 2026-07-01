"""DocumentCompiler — service that wires all four document passes into a pipeline.

Receives a PassRegistry (containing the four document passes registered via
kir.compiler.documents.passes) and a CompilerContext, validates the dependency
graph at construction time (via registry.pipeline()), and exposes a single
async compile() method that reads a Markdown file and returns a fully-populated
Document IR.

Usage:
    from kir.compiler.documents.passes import document_registry
    compiler = DocumentCompiler(document_registry, ctx)
    doc = await compiler.compile(Path("notes.md"))

Async passes (extract_concepts_pass) are dispatched with await; sync passes
(parse_pass, section_pass, metadata_pass) are called directly. The distinction
is made at runtime via asyncio.iscoroutinefunction().
"""


import asyncio
from pathlib import Path

from kir.core.domain.models.document import Document
from kir.core.domain.value_objects import Checksum
from kir.core.passes.context import CompilerContext
from kir.core.passes.registry import PassRegistry


class DocumentCompiler:
    """Compiler that runs all four document passes in dependency order.

    The pipeline is validated at construction time (PassRegistry.pipeline()
    performs a topological sort and raises if any depends_on reference is
    unresolved). After construction, compile() can be called any number of
    times without re-validating the pipeline.

    Args:
        registry: A PassRegistry that already has the four document passes
                  registered (parse, section, metadata, extract_concepts).
        context: The CompilerContext for this compilation run (llm, llm_cache,
                 prompts, prompt_version, schema_version, etc.).
    """

    def __init__(self, registry: PassRegistry, context: CompilerContext) -> None:
        self._pipeline = registry.pipeline()  # validates dependency graph at construction
        self._ctx = context

    async def compile(self, source_path: Path) -> Document:
        """Compile a single Markdown file into a fully-populated Document IR.

        Reads the file, constructs an initial Document IR with empty semantic
        fields, then runs each pass in pipeline order. Async passes are awaited;
        sync passes are called directly.

        Args:
            source_path: Path to the Markdown source file. The caller controls
                         the input corpus — no path-traversal restriction is
                         applied here (DocumentCompiler is a batch CLI tool,
                         not a web service; see Plan 04a threat model).

        Returns:
            A fully-populated Document IR with id, title, checksum, language,
            sections, concepts, glossary, entities, references, and any
            Diagnostics accumulated by passes.
        """
        text = source_path.read_text(encoding="utf-8")

        # Construct initial Document IR — semantic fields are empty stubs that
        # the passes populate in dependency order.
        ir = Document(
            id="",
            title="",
            source=text,
            checksum=Checksum(algorithm="sha256", value=""),
            language="",
        )

        for pass_fn in self._pipeline:
            if asyncio.iscoroutinefunction(pass_fn):
                ir = await pass_fn(ir, self._ctx)
            else:
                ir = pass_fn(ir, self._ctx)

        self._ctx.repository.save(ir.id, ir.model_dump())
        return ir
