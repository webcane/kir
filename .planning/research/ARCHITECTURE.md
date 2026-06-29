# Architecture Research

**Domain:** Semantic compiler / IR pipeline (compiler-pass architecture applied to knowledge extraction), built with hexagonal architecture + tactical DDD in Python/Pydantic
**Researched:** 2026-06-29
**Confidence:** HIGH (component boundaries, build order, registry pattern, hexagonal layering — all corroborated by official docs / canonical references) / MEDIUM (exact pass-context object shape, incremental-compilation dependency tracking — synthesized from analogous systems, no single source covers this exact combination)

## Standard Architecture

### System Overview

KIR is best understood as three concentric rings (hexagonal) crossed with a linear pipeline (compiler passes). The rings give you *what depends on what*; the pipeline gives you *what runs in what order*. Both must hold simultaneously: every pass lives in the application ring and depends only on domain-ring types and port interfaces, never on a concrete adapter.

```
┌────────────────────────────────────────────────────────────────────────┐
│  ADAPTERS (outermost ring — driven by ports, swappable, "dirty")       │
│                                                                          │
│  ┌────────────┐  ┌────────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ CLI (Typer)│  │ LLM Adapter    │  │ YAML Repo   │  │ Markdown    │ │
│  │ kir compile│  │ (PydanticAI    │  │ (documents/,│  │ Parser      │ │
│  │            │  │  Agent + model)│  │ concepts/...)│  │ Adapter     │ │
│  └─────┬──────┘  └───────┬────────┘  └──────┬──────┘  └──────┬──────┘ │
│        │                 │ implements        │ implements      │       │
│        │                 │ LLMPort           │ RepositoryPort  │       │
├────────┼─────────────────┼───────────────────┼─────────────────┼───────┤
│        ▼                 ▼                   ▼                 ▼       │
│  APPLICATION RING — orchestration, no I/O details, depends on PORTS    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  PassPipeline / PassRegistry                                    │    │
│  │  Parse → Section → Metadata → ExtractConcepts(LLM) →            │    │
│  │  ResolveAliases → MergeConcepts → BuildRelations →               │    │
│  │  BuildTaxonomy → Conflict                                        │    │
│  │  each Pass: (IR_in, PassContext[ports]) -> IR_out                │    │
│  └────────────────────────────────────────────────────────────────┘    │
│  ┌──────────────────┐   ┌───────────────────────┐                      │
│  │ DocumentCompiler  │   │ KnowledgeCompiler      │  (use-case services)│
│  │ (use case)        │   │ (use case)             │                      │
│  └──────────────────┘   └───────────────────────┘                      │
├──────────────────────────────────────────────────────────────────────--┤
│  DOMAIN RING (innermost — pure, zero I/O, zero SDK imports)            │
│                                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Document │ │ Concept  │ │ Relation │ │ Taxonomy │ │ Conflict     │  │
│  │ (Entity) │ │ (Entity) │ │ (VO)     │ │ (VO/Agg) │ │ (VO)         │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  Pydantic BaseModels only. No `openai`, `anthropic`, `pathlib`, `yaml`. │
│  Ports defined here too (as Protocols/ABCs) — domain OWNS the          │
│  interface, adapters DEPEND ON the domain, never the reverse.          │
└──────────────────────────────────────────────────────────────────────--┘
```

**Dependency rule (the one rule that matters):** arrows of *dependency* point inward only. The domain ring imports nothing from application or adapters. The application ring imports domain + port interfaces, never concrete adapter classes. Adapters import domain (to implement the ports) and external SDKs (`openai`, `pyyaml`, `markdown-it-py`) — and are the *only* place those imports are allowed to appear. If you ever write `import openai` or `import yaml` inside anything under `domain/` or `passes/`, that is the single most important anti-pattern to catch in review.

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Domain models | Define Concept, Relation, Taxonomy, Document, Conflict as pure data + invariants | Pydantic `BaseModel` subclasses, no I/O, validators enforce invariants (e.g. concept id = slug) |
| Ports (interfaces) | Define the *shape* of what the domain/application needs from the outside world, owned by the inside | `typing.Protocol` or `abc.ABC` classes — `LLMPort`, `DocumentRepositoryPort`, `KnowledgeRepositoryPort`, `MarkdownParserPort` |
| Passes | Single, independently-testable transformation step: one IR in, one IR (or IR delta) out | Plain Python callables/classes registered in a `PassRegistry`; LLM-backed passes take a port, not a concrete client |
| Pass pipeline / registry | Orders passes, resolves dependencies between them, exposes `register()` so new passes don't touch existing code | Decorator-based self-registration into a module-level registry, analogous to LLVM's `PassBuilder` callback registration |
| Use-case services (DocumentCompiler, KnowledgeCompiler) | Orchestrate "run this pipeline over this input, persist via this port" — the only place that sequences passes and talks to ports | Plain Python classes/functions in `application/`, injected with port implementations at construction time |
| LLM Adapter | Implements `LLMPort` using PydanticAI `Agent`, hides provider selection (OpenAI/Anthropic/etc.) and prompt/version pinning | `pydantic_ai.Agent[DepsT, OutputT]`, output type = the exact Pydantic domain/DTO model the pass expects |
| Repository Adapter | Implements `DocumentRepositoryPort` / `KnowledgeRepositoryPort`, translates domain objects ↔ one-YAML-file-per-artifact on disk | Plain Python class wrapping `pathlib` + `pyyaml`/`ruamel.yaml`, one file per concept/relation/document |
| Markdown Parser Adapter | Implements `MarkdownParserPort`, turns raw `.md` bytes into a parse tree the first pass can consume | Wraps `markdown-it-py` or `mistune`; returns domain-safe DTOs, not library-native AST nodes |
| CLI | Thin entrypoint: parse args, wire concrete adapters into use-case services, invoke, report | `Typer` app; this is the *composition root* — the only place all three rings get wired together |

## Recommended Project Structure

```
src/kir/
├── domain/                      # Innermost ring — zero I/O, zero SDK imports
│   ├── models/
│   │   ├── document.py          # Document IR: Document, Section entities
│   │   ├── concept.py           # Concept entity (id, canonical name, aliases, definition...)
│   │   ├── relation.py          # Relation value object (type, source, target)
│   │   ├── taxonomy.py          # Taxonomy value object / small aggregate
│   │   ├── conflict.py          # Conflict value object (never silently resolved)
│   │   └── provenance.py        # Provenance value object (doc id + section, shared by all)
│   ├── ir.py                    # DocumentIR / KnowledgeIR aggregate roots (top-level envelopes)
│   └── ports/                   # Interfaces OWNED by the domain, implemented by adapters
│       ├── llm_port.py          # Protocol: extract_concepts(), resolve_aliases(), classify_taxonomy()...
│       ├── repository_port.py   # Protocol: DocumentRepository, KnowledgeRepository
│       └── parser_port.py       # Protocol: MarkdownParser
│
├── passes/                      # Application ring — the pipeline itself
│   ├── registry.py              # PassRegistry: register(), get_pipeline(), dependency ordering
│   ├── base.py                  # Pass protocol: __call__(ir_in, ctx: PassContext) -> ir_out
│   ├── document/                # Document Compiler passes (Markdown → Document IR)
│   │   ├── parse.py             # ParsePass (deterministic)
│   │   ├── section.py           # SectionPass (deterministic)
│   │   └── metadata.py          # MetadataPass (deterministic)
│   └── knowledge/                # Knowledge Compiler passes (Document IR[] → Knowledge IR)
│       ├── extract_concepts.py  # ExtractConceptsPass (LLM-backed, uses LLMPort)
│       ├── resolve_aliases.py   # ResolveAliasesPass (LLM-backed)
│       ├── merge_concepts.py    # MergeConceptsPass (deterministic merge logic)
│       ├── build_relations.py   # BuildRelationsPass (LLM-backed)
│       ├── build_taxonomy.py    # BuildTaxonomyPass (LLM-backed)
│       └── conflict.py          # ConflictPass (deterministic, detects + records)
│
├── application/                 # Use-case orchestration
│   ├── document_compiler.py     # DocumentCompiler: runs document/* pipeline per source file
│   └── knowledge_compiler.py    # KnowledgeCompiler: runs knowledge/* pipeline across all Document IRs
│
├── adapters/                    # Outermost ring — all SDK/filesystem/YAML imports live here ONLY
│   ├── llm/
│   │   ├── pydantic_ai_adapter.py   # Implements LLMPort via pydantic_ai.Agent
│   │   └── prompts/                  # Versioned prompt templates (pinned per Key Decision: determinism)
│   ├── repository/
│   │   ├── yaml_document_repo.py     # Implements DocumentRepositoryPort (documents/*.yaml)
│   │   └── yaml_knowledge_repo.py    # Implements KnowledgeRepositoryPort (concepts/, relations/, taxonomy/, aliases/, metadata/)
│   └── parsing/
│       └── markdown_it_adapter.py    # Implements MarkdownParserPort
│
├── cli/
│   └── main.py                  # Typer app — composition root: wires adapters into compilers
│
└── config/
    └── versions.py              # compiler_version, schema_version, prompt_version constants
```

### Structure Rationale

- **`domain/` has no subfolder for "services"** — tactical DDD here stays deliberately thin (per PROJECT.md's explicit rejection of Event Sourcing / enterprise DDD). Concept/Relation/Taxonomy/Document are the only Entities/VOs/Aggregates; no domain services layer is needed because pass logic that needs orchestration lives in `passes/` and `application/`, not inside the domain models.
- **`domain/ports/` lives inside the domain package, not in `adapters/`** — this is the crux of "ports are owned by the inside." The domain (and the passes that consume ports) defines *what shape of behavior it needs*; adapters are graded against that shape. This is what makes "new LLM provider" or "new storage backend" a zero-domain-change event.
- **`passes/document/` vs `passes/knowledge/`** mirrors the two-compiler structure already named in PROJECT.md (Document Compiler, Knowledge Compiler) — each is a distinct pipeline with its own pass registry instance, not one monolithic 9-stage pipeline. This also matches the natural incremental-compilation boundary: Document IR passes run per-file (parallelizable, cacheable by checksum); Knowledge IR passes run once over the merged set.
- **`adapters/llm/prompts/`** is separated out and versioned because the determinism requirement ("identical inputs + prompt version → identical output") means prompt text is effectively part of the adapter's public contract, not a throwaway string literal.
- **No `core/` or `shared/` grab-bag folder** — provenance and IDs are domain value objects (`domain/models/provenance.py`), not "shared utilities." Compiler/schema/prompt version stamps live in `config/versions.py` and are *read* by adapters and passes but the domain models simply have fields for them (`compiler_version: str`) — the domain doesn't know *how* those values get sourced.

## Architectural Patterns

### Pattern 1: Pass as a Pure Function over Ports, Registered by Decorator

**What:** Each compiler pass is a callable with the signature `(ir: InputIR, ctx: PassContext) -> OutputIR`. `PassContext` carries only port interfaces (never concrete adapters) plus run metadata (versions, config). Passes self-register into a `PassRegistry` via decorator at import time — directly analogous to LLVM's `PassBuilder` pipeline-callback registration, but using Python's "decorator runs on module import" mechanic instead of C++ static registration.

**When to use:** Every step in both the Document Compiler and Knowledge Compiler pipelines. This is the project's core extension mechanism — it directly satisfies the "adding a new pass does not require modifying existing passes" requirement.

**Trade-offs:** Self-registration via decorator means import order / `__init__.py` re-exports matter (a pass that's never imported never registers) — mitigate with an explicit `passes/document/__init__.py` and `passes/knowledge/__init__.py` that import every pass module so registration always fires. Upside: genuinely zero-touch extension — a new pass is a new file plus one line in `__init__.py`, never an edit to the pipeline definition or existing passes.

**Example:**
```python
# passes/registry.py
from typing import Protocol, Callable
from kir.domain.ir import DocumentIR, KnowledgeIR

class PassContext:
    """Carries ports + run metadata. No concrete adapters, ever."""
    def __init__(self, llm, repository, compiler_version, schema_version, prompt_version):
        self.llm = llm                  # LLMPort
        self.repository = repository    # RepositoryPort
        self.compiler_version = compiler_version
        self.schema_version = schema_version
        self.prompt_version = prompt_version

class Pass(Protocol):
    name: str
    depends_on: tuple[str, ...]   # names of passes that must run first
    def __call__(self, ir, ctx: PassContext): ...

class PassRegistry:
    def __init__(self):
        self._passes: dict[str, Pass] = {}

    def register(self, pass_obj: Pass) -> Pass:
        self._passes[pass_obj.name] = pass_obj
        return pass_obj

    def pipeline(self) -> list[Pass]:
        # topological sort over depends_on — new passes slot in
        # by declaring dependencies, not by editing this method
        return _topo_sort(self._passes)

knowledge_registry = PassRegistry()

def register_pass(name: str, depends_on: tuple[str, ...] = ()):
    def decorator(fn):
        fn.name = name
        fn.depends_on = depends_on
        knowledge_registry.register(fn)
        return fn
    return decorator

# passes/knowledge/extract_concepts.py
@register_pass("extract_concepts", depends_on=("parse", "section", "metadata"))
def extract_concepts_pass(ir: DocumentIR, ctx: PassContext) -> DocumentIR:
    concepts = ctx.llm.extract_concepts(ir.sections, prompt_version=ctx.prompt_version)
    return ir.model_copy(update={"concepts": concepts})
```

### Pattern 2: Ports as Protocols Owned by the Domain (Dependency Inversion)

**What:** Instead of the domain importing an adapter's interface, the domain (or the pass layer that sits right against it) declares a `typing.Protocol` describing exactly the behavior it needs. Adapters are then *structurally* checked against that Protocol — no explicit inheritance required, which keeps adapters free to depend on their SDKs without the domain ever importing adapter code.

**When to use:** Every external dependency the passes need — LLM calls, file/YAML I/O, Markdown parsing. This is literally what "domain model has zero knowledge of LLM SDKs or filesystem/YAML" means operationalized.

**Trade-offs:** `Protocol` (structural typing) is more Pythonic and avoids import-time coupling that `ABC` inheritance would require; downside is slightly weaker enforcement (nothing stops an adapter from "accidentally" satisfying a Protocol without meaning to) — acceptable trade for a single-team v1 project. Mypy/pyright will flag mismatches at type-check time regardless.

**Example:**
```python
# domain/ports/llm_port.py
from typing import Protocol
from kir.domain.models.concept import ExtractedConcept
from kir.domain.models.relation import ExtractedRelation

class LLMPort(Protocol):
    def extract_concepts(self, sections: list[str], *, prompt_version: str) -> list[ExtractedConcept]: ...
    def resolve_aliases(self, concepts: list[ExtractedConcept], *, prompt_version: str) -> dict[str, str]: ...
    def classify_taxonomy(self, concept: ExtractedConcept, *, prompt_version: str) -> str: ...

# adapters/llm/pydantic_ai_adapter.py  -- the ONLY file that imports pydantic_ai / openai / anthropic
from pydantic_ai import Agent
from kir.domain.ports.llm_port import LLMPort
from kir.domain.models.concept import ExtractedConcept

class PydanticAILLMAdapter(LLMPort):
    def __init__(self, model: str, prompts_dir):
        self._agent = Agent(model, output_type=list[ExtractedConcept])
        self._prompts_dir = prompts_dir

    def extract_concepts(self, sections, *, prompt_version):
        prompt = self._load_prompt("extract_concepts", prompt_version)
        result = self._agent.run_sync(prompt.format(sections=sections))
        return result.output
```

### Pattern 3: Repository per Aggregate, YAML-File-per-Artifact Adapter

**What:** Following the Cosmic Python "Repository pattern" (abstraction over persistent storage, one repository per aggregate root), define `DocumentRepositoryPort` and `KnowledgeRepositoryPort` in the domain, then implement them with an adapter that maps each Pydantic model instance to exactly one YAML file under `documents/`, `concepts/`, `relations/`, `taxonomy/`, `aliases/`, `metadata/` — matching PROJECT.md's explicit "one YAML file per artifact, never monolithic JSON" constraint.

**When to use:** Any time a pass or use-case service needs to load/save Document IR or Knowledge IR artifacts. A full Unit-of-Work wrapper (atomic multi-file commit) is *optional complexity* — given the determinism/idempotency requirements and single-process CLI usage, a simpler "repository writes are last-step-of-a-use-case, and conflicts/partial writes are surfaced rather than rolled back" approach is adequate for v1; do not over-engineer a transactional UoW unless corruption from partial writes becomes an observed problem.

**Trade-offs:** One-file-per-artifact is git-diff-friendly and human-readable (the explicit goal) at the cost of many small file I/O operations across 700 documents — mitigated by the incremental-compilation requirement (only changed documents get rewritten, checksum-gated).

## Data Flow

### Compile Request Flow (the two-compiler pipeline)

```
kir compile (CLI / composition root)
    ↓ wires concrete adapters into use-case services
DocumentCompiler.compile_all(source_dir)
    ↓ for each .md file: checksum compare against documents/*.yaml
    ↓ (skip unchanged — incremental compilation)
    Markdown file → [ParsePass → SectionPass → MetadataPass] → Document IR
    ↓ DocumentRepositoryPort.save(document_ir)  →  documents/<id>.yaml
    ↓ (repeat per changed document; passes run independently, in isolation)
KnowledgeCompiler.compile(all_document_irs)
    ↓ [ExtractConceptsPass(LLM) → ResolveAliasesPass(LLM) → MergeConceptsPass →
    ↓  BuildRelationsPass(LLM) → BuildTaxonomyPass(LLM) → ConflictPass]
    ↓ each pass: KnowledgeIR_n + PassContext(ports) -> KnowledgeIR_n+1
    ↓ KnowledgeRepositoryPort.save(knowledge_ir)
    → concepts/*.yaml, relations/*.yaml, taxonomy/*.yaml, aliases/*.yaml, metadata/*.yaml, conflicts/*.yaml
    ↓
CLI reports: N documents compiled, M concepts merged, K conflicts recorded
```

### State/IR Flow Through Passes

```
Document IR (immutable Pydantic model)
    ↓ pass N reads, NEVER mutates in place
    ↓ pass N returns a NEW IR instance (ir.model_copy(update={...}))
Document IR (next version)
    ↓ ... repeat for each registered pass in dependency order ...
Final Document IR  →  persisted via DocumentRepositoryPort

[All Document IRs]
    ↓ fed into KnowledgeCompiler as a list
Knowledge IR (accumulates concepts/relations/taxonomy/conflicts across documents)
    ↓ same immutable-pass-chain discipline
Final Knowledge IR  →  persisted via KnowledgeRepositoryPort
```

### Key Data Flows

1. **Provenance threading:** Every Concept/Relation/Definition created by any pass carries a `Provenance` value object (source document id + section) from the moment it's extracted. This is *not* bolted on at the end — `ExtractConceptsPass` must stamp provenance immediately because by the `MergeConceptsPass` stage, multiple documents' concepts are being unioned and origin would otherwise be unrecoverable.
2. **Incremental recompilation:** `DocumentCompiler` computes a checksum per source file before running any pass; only documents whose checksum differs from the stored `documents/<id>.yaml` checksum field get recompiled (Bazel/content-hash style, not Make-style mtime comparison — mtimes are unreliable across git checkouts/clones). Changed-document IDs are then the *only* input set that triggers Knowledge IR re-merge, not a full-corpus re-run — this is what makes incremental compilation tractable at 700 documents.
3. **Conflict surfacing, not resolution:** `ConflictPass` is structurally identical to other passes (`IR_in -> IR_out`) but its "output" is additive — it never deletes or silently rewrites a conflicting concept/relation; it appends `Conflict` value objects to the Knowledge IR and lets a human/separate review step decide. This flow must never be short-circuited by an earlier pass "fixing" something it now finds ambiguous — that responsibility belongs solely to `ConflictPass` placed last in the pipeline.
4. **Version stamping:** `compiler_version`, `schema_version`, `prompt_version` are read from `config/versions.py` by the CLI composition root, placed into `PassContext`, and every persisted artifact (Document IR, Knowledge IR, and every individual Concept/Relation if needed) carries them — this is what makes "identical inputs + versions → identical output" checkable after the fact.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| v1 / 700 docs (current target) | Single-process CLI run, in-memory Knowledge IR during the merge passes, sequential pass execution. This is entirely sufficient — do not add async/concurrency/queueing for v1. |
| ~5,000-10,000 docs | Document Compiler passes (per-file, no cross-document state) parallelize trivially via `concurrent.futures` / multiprocessing since each Document IR build is independent; Knowledge Compiler passes (which need the full merged set) become the bottleneck — first thing to profile. |
| 50,000+ docs / multi-corpus | Knowledge IR merge passes may need batching/streaming (process concepts in chunks rather than holding the full corpus's extracted concepts in memory at once) and the LLM adapter may need request batching/concurrency limits; repository adapter may need an index file to avoid scanning every YAML file on every incremental run. |

### Scaling Priorities

1. **First bottleneck (well before 700 docs becomes a problem):** LLM API latency/cost during `ExtractConceptsPass`/`ResolveAliasesPass`/`BuildRelationsPass`/`BuildTaxonomyPass` — these are the only passes that leave the process. Mitigate with per-document-checksum incremental compilation (already a v1 requirement) so re-runs don't re-call the LLM for unchanged documents, and consider caching LLM responses keyed on (document checksum, prompt version) independent of the Document IR cache.
2. **Second bottleneck:** Sequential file I/O across hundreds of small YAML files in the repository adapter — solvable with straightforward batching (write all changed files in one pass) long before it requires anything architecturally interesting.

## Anti-Patterns

### Anti-Pattern 1: Domain Models with Adapter Imports ("Leaky Hexagon")

**What people do:** Import `openai`, `anthropic`, `pydantic_ai`, `yaml`, or `pathlib.Path`-based file logic directly inside `domain/models/*.py` or inside a pass module "just to add one helper," e.g. a `Concept.from_yaml()` classmethod that calls `yaml.safe_load` directly on the domain model.
**Why it's wrong:** It silently destroys the entire reason for hexagonal architecture here — the domain (and the determinism guarantee) becomes coupled to a specific LLM SDK version or YAML library quirk. PROJECT.md is explicit that this is a hard requirement, not a style preference.
**Instead:** Domain models only know how to validate/represent themselves (`model_validate`, `model_dump`). Any (de)serialization to a specific *format* (YAML on disk, JSON over the wire) is the repository adapter's job — it calls `Concept.model_validate(yaml.safe_load(f))`, not the other way around.

### Anti-Pattern 2: Passes That Reach Around the Registry to Call Each Other Directly

**What people do:** Inside `MergeConceptsPass`, directly import and call `extract_concepts_pass(...)` to "get fresh data" instead of trusting that the pipeline already ran it and the result is in the IR being passed in.
**Why it's wrong:** Breaks the "each pass consumes one IR, produces one IR" contract and reintroduces hidden coupling between passes — exactly what the registry/pipeline mechanism exists to prevent. It also makes passes untestable in isolation (PROJECT.md requires deterministic passes to be unit-testable directly).
**Instead:** Passes only ever read from the `IR` argument they're given and the `PassContext` ports. If a pass needs data computed by an earlier pass, that data must already be a field on the IR by the time it reaches this pass — express that as a `depends_on` declaration in the registry, not a direct function call.

### Anti-Pattern 3: One Mega-Pipeline Instead of Two Compilers

**What people do:** Merge Document Compiler and Knowledge Compiler into a single linear 9-stage pipeline that runs end-to-end per document, including the cross-document merge steps.
**Why it's wrong:** `MergeConceptsPass`, `BuildRelationsPass`, `BuildTaxonomyPass`, and `ConflictPass` inherently need *all* Document IRs (or the accumulated Knowledge IR) as input — they cannot run per-document. Forcing them into a per-document loop either produces wrong results (premature merging) or forces awkward global-state workarounds that defeat the "independently testable pass" goal.
**Instead:** Keep Document Compiler (per-file, parallelizable, produces Document IR) and Knowledge Compiler (whole-corpus, produces Knowledge IR) as two distinct pipelines/registries, exactly as PROJECT.md's pass list already implies via its ordering — `Parse → Section → Metadata → ExtractConcepts` is naturally per-document, `ResolveAliases → MergeConcepts → BuildRelations → BuildTaxonomy → Conflict` is naturally whole-corpus.

### Anti-Pattern 4: Treating PydanticAI's Agent as the Port Itself

**What people do:** Type the `PassContext.llm` field (or the pass function signature) directly as `pydantic_ai.Agent`, reasoning "PydanticAI is already provider-agnostic, so this is fine."
**Why it's wrong:** It's a smaller leak than importing `openai` directly, but it still couples every pass's type signature to a third-party library, and it conflates "which provider" (an `Agent`'s job) with "what capability does this pass need" (the port's job — e.g. `extract_concepts(sections) -> list[ExtractedConcept]`, a *much* narrower interface than the full `Agent` API surface). It also makes swapping PydanticAI itself for something else later a domain-wide change instead of an adapter-only change.
**Instead:** Define narrow `LLMPort` Protocols per capability (or one `LLMPort` with one method per semantic-analysis pass) in `domain/ports/llm_port.py`; only `adapters/llm/pydantic_ai_adapter.py` imports and constructs `pydantic_ai.Agent`.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| LLM provider (OpenAI/Anthropic/etc., via PydanticAI) | `LLMPort` Protocol implemented by `PydanticAILLMAdapter`; `pydantic_ai.Agent(model, output_type=DomainModel)` returns validated Pydantic objects directly | Confirmed (HIGH, official PydanticAI docs): `Agent` supports OpenAI, Anthropic, Gemini, and many more via a model-string switch — provider choice becomes a config value, not a code change. Testing uses `TestModel`/`FunctionModel`/`Agent.override()` to avoid live API calls in CI — directly satisfies PROJECT.md's "LLM-backed passes tested against recorded/mocked responses" requirement. |
| Filesystem (raw sources + `kir/` output) | `RepositoryPort` implementations read/write YAML; raw source directory is read-only (never mutated, per PROJECT.md constraint) | Use a strict read-only path for the raw source tree (no write operations ever attempted against it, enforced by adapter design, e.g. accepting only a `Path` opened in a context that never calls `.write_*`). |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI ↔ Application (DocumentCompiler/KnowledgeCompiler) | Direct method calls; CLI is the composition root that constructs adapters and injects them | CLI is the only layer allowed to know about *all* concrete adapter classes simultaneously. |
| Application ↔ Passes | `PassRegistry.pipeline()` returns ordered list; use-case service iterates and calls each pass with `(ir, ctx)` | Use-case service owns the loop; passes never know about each other or about the use-case service. |
| Passes ↔ Domain | Passes import domain models/ports directly (passes live in the "application ring" conceptually, but are the layer most tightly coupled to domain types by design — that's expected and fine) | Passes must NOT import adapters; only ports. |
| Domain ↔ Ports | Ports are declared inside `domain/ports/`, so this isn't really a "boundary" — it's domain defining its own needs | This is the dependency-inversion mechanism: domain owns the contract, adapters fulfill it. |
| Adapters ↔ External SDKs | Direct imports (`pydantic_ai`, `yaml`, `markdown_it`) — fully isolated to `adapters/` | Any upgrade/swap of PydanticAI, the YAML library, or the Markdown parser touches exactly one adapter file and its tests, never domain/passes/application. |

## Suggested Build Order

Dependencies flow inside-out and bottom-up: you cannot test a pass without the domain models it consumes/produces existing first; you cannot wire a CLI without use-case services existing first.

1. **Domain models** (`domain/models/*`, `domain/ir.py`) — Concept, Relation, Taxonomy, Document, Conflict, Provenance as Pydantic models with their invariants (slug-derived Concept IDs, etc.). Zero dependencies on anything else in the project. Fully unit-testable in isolation (construct a `Concept`, assert validation behavior) before any pass or adapter exists.
2. **Ports** (`domain/ports/*`) — Define `LLMPort`, `RepositoryPort` (split into Document/Knowledge), `MarkdownParserPort` as Protocols, informed by what step 3's passes will need. Still zero external dependencies — these are interfaces, not implementations.
3. **Pass registry mechanism** (`passes/registry.py`, `passes/base.py`) — Build and unit-test the registration/topological-ordering machinery itself using trivial fake passes before writing any real pass. This is infrastructure, not domain logic, and should be provably correct (new pass added → pipeline order updates correctly, no existing pass touched) before real passes depend on it.
4. **Deterministic passes first** (`passes/document/parse.py`, `section.py`, `metadata.py`; `passes/knowledge/merge_concepts.py`, `conflict.py`) — These need no LLM port, no real I/O — pure functions over domain models, fastest to get right and fully unit-testable with plain fixtures.
5. **Fake/mock LLM adapter for testing** (a `FakeLLMAdapter` implementing `LLMPort` with canned responses, or PydanticAI's own `TestModel`/`FunctionModel`) — Build this *before* the real LLM adapter so that LLM-backed passes (step 6) can be developed and tested without live API calls or cost from day one.
6. **LLM-backed passes** (`passes/document/extract_concepts... ` — note: ExtractConcepts is listed under Document Compiler's pass list in PROJECT.md since it runs per-document; `passes/knowledge/resolve_aliases.py`, `build_relations.py`, `build_taxonomy.py`) — Each written against `LLMPort`, tested against the fake/mock adapter from step 5 with recorded/golden fixtures.
7. **Real LLM adapter** (`adapters/llm/pydantic_ai_adapter.py` + versioned prompts) — Implement `LLMPort` for real using `pydantic_ai.Agent`. Can be developed in parallel with steps 4-6 since it only needs the `LLMPort` contract from step 2, not the passes themselves.
8. **Repository adapter** (`adapters/repository/yaml_*.py`) — Implement `RepositoryPort` against the one-YAML-file-per-artifact layout. Depends only on domain models (step 1) and the port interface (step 2); can also be developed in parallel with steps 4-7.
9. **Markdown parser adapter** (`adapters/parsing/markdown_it_adapter.py`) — Implement `MarkdownParserPort`. Needed concretely by step 4's `ParsePass` consumer at the use-case level, but the *pass itself* only needs the port, so this can trail slightly behind without blocking pass development.
10. **Use-case services** (`application/document_compiler.py`, `knowledge_compiler.py`) — Wire `PassRegistry.pipeline()` execution against real or fake ports; this is where the two pipelines actually run end-to-end for the first time. Depends on steps 3-9 all being in place (at least with fakes for ports not yet implemented).
11. **Incremental-compilation logic** (checksum comparison gating which documents recompile) — Layer this into `DocumentCompiler` once the basic per-document pipeline (step 10) works correctly without it; get correctness first, then add the "skip unchanged" optimization, since it's much easier to debug a full-recompile pipeline than to debug incremental logic and pass logic simultaneously.
12. **CLI** (`cli/main.py`) — The composition root: wires real adapters (steps 7-9) into use-case services (step 10) and exposes `kir compile`. This is deliberately last because it has the most dependencies and the least independent logic — it should be almost entirely wiring, with no business logic of its own to test.
13. **End-to-end validation against the 700-document corpus** — Only attempted once steps 1-12 are individually tested; this is integration validation, not a build step that produces new components.

**Why this order, restated:** the project's two hardest constraints — "domain has zero knowledge of LLM/filesystem" and "new passes don't require touching existing ones" — are both *structural* guarantees that must be designed in from step 1-3, not retrofitted. Building domain models and the pass registry mechanism first (and proving them in isolation with fakes) is what makes steps 4-9 genuinely parallelizable and step 12 genuinely thin.

## Sources

- [Using the New Pass Manager — LLVM Documentation](https://llvm.org/docs/NewPassManager.html) — pass pipeline / PassBuilder registration-callback pattern (HIGH confidence, official docs)
- [Writing an LLVM Pass — LLVM Documentation](https://llvm.org/docs/WritingAnLLVMNewPMPass.html) — pass structure conventions (HIGH confidence, official docs)
- [Pass Infrastructure — MLIR/LLVM](https://mlir.llvm.org/docs/PassManagement/) — nested pass-manager hierarchy concept, analogous to Document-pass vs Knowledge-pass split (HIGH confidence, official docs)
- [Architecture Patterns with Python ("Cosmic Python") — Unit of Work Pattern](https://www.cosmicpython.com/book/chapter_06_uow) — Repository + Unit of Work abstraction over persistence (HIGH confidence, canonical reference text for Python DDD/hexagonal patterns)
- [Architecture Patterns with Python — GitHub](https://github.com/cosmicpython/book) — full reference architecture for ports/adapters in Python (HIGH confidence)
- [Pydantic AI — Dependencies (official docs)](https://ai.pydantic.dev/dependencies/) — `RunContext`/deps injection pattern for swapping real vs. fake dependencies (HIGH confidence, official docs)
- [Pydantic AI — Testing (official docs)](https://ai.pydantic.dev/testing/) — `TestModel`, `FunctionModel`, `Agent.override()` for mocked/deterministic LLM testing without live API calls (HIGH confidence, official docs)
- [Pydantic AI — pydantic_ai.models.test (official API docs)](https://ai.pydantic.dev/api/models/test/) — TestModel mechanics (HIGH confidence, official docs)
- [Pydantic AI overview — pydantic.dev](https://pydantic.dev/pydantic-ai) — provider-agnostic model support (OpenAI, Anthropic, Gemini, Bedrock, Ollama, etc.) confirmed via official vendor page (HIGH confidence)
- [Hexagonal Architecture in Python — dev.to / Pablo Ifran Czerny](https://dev.to/elpic/hexagonal-architecture-in-python-wiring-adapters-dependency-injection-and-the-application-layer-61l) — ports/adapters wiring + composition root pattern in Python (MEDIUM confidence, community source, consistent with Cosmic Python)
- [Bazel — Artifact-Based Build Systems](https://bazel.build/basics/artifact-based-builds) and [Bazel — Dependencies](https://bazel.build/concepts/dependencies) — content-hash-based incremental rebuild pattern, applied here to per-document checksum gating (HIGH confidence, official docs, pattern applied by analogy)
- [Python Registry Pattern — dev.to](https://dev.to/dentedlogic/stop-writing-giant-if-else-chains-master-the-python-registry-pattern-ldm) and [Implementing the Registry Pattern with Decorators in Python — Medium](https://medium.com/@tihomir.manushev/implementing-the-registry-pattern-with-decorators-in-python-de8daf4a452a) — decorator-based self-registration mechanism, the Python-idiomatic analog to LLVM's pass registration (MEDIUM confidence, community sources, well-established pattern)

---
*Architecture research for: semantic compiler / compiler-pass pipeline with hexagonal architecture + tactical DDD, Python/Pydantic stack*
*Researched: 2026-06-29*
