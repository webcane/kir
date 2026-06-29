# Requirements: KIR (Knowledge Intermediate Representation)

**Defined:** 2026-06-29
**Core Value:** Given identical raw sources, compiler version, prompt version, and schema version, KIR must deterministically compile raw Markdown into a canonical Knowledge IR that merges concepts/relations/taxonomy across documents, preserves full provenance, and explicitly records (never silently resolves) semantic conflicts.

## v1 Requirements

### Compiler Foundation

- [ ] **CORE-01**: Domain model (Concept, Relation, Taxonomy, Document entities; ConceptId, RelationId, Checksum, SourceRef value objects) has zero import-level dependency on LLM SDKs, filesystem, or YAML libraries
- [ ] **CORE-02**: System exposes ports (LLMPort, RepositoryPort, MarkdownParserPort) as typed interfaces that adapters implement, so swapping an LLM provider or storage backend never requires touching domain code
- [ ] **CORE-03**: Compiler passes register independently (decorator/plugin-based registry) such that adding a new pass never requires modifying existing passes
- [ ] **CORE-04**: Compiler executes a deterministic pipeline of CompilerPass instances; each pass declares what it consumes, what it produces, and its dependencies, and the pipeline resolves execution order automatically from those declarations rather than a hardcoded sequence
- [ ] **CORE-05**: All compiler passes execute inside a shared, immutable CompilerContext (carrying config, cache, repository, LLM port, logger, metrics, versions) rather than receiving these piecemeal
- [ ] **CORE-06**: Every pass returns structured diagnostics (errors, warnings, infos) as part of its output artifact, instead of printing or logging output directly
- [ ] **CORE-07**: Passes never mutate a previous IR in place; each pass produces a new immutable artifact

### Compiler Passes (architectural contract)

- [ ] **PASS-01**: Every transformation of knowledge is implemented as a CompilerPass
- [ ] **PASS-02**: Each pass consumes exactly one IR representation and produces exactly one IR representation
- [ ] **PASS-03**: Passes are deterministic and independently testable in isolation
- [ ] **PASS-04**: Passes communicate only through IR artifacts and CompilerContext — never through side channels or shared mutable state
- [ ] **PASS-05**: Pass execution order is derived from declared dependencies (see CORE-04), not hardcoded sequencing

### Document Compiler

- [ ] **DOC-01**: System parses a single Markdown source into Document IR (id, title, source, checksum, language, sections, concepts, glossary, entities, references)
- [ ] **DOC-02**: Document IR for one document never merges information from another document
- [ ] **DOC-03**: System extracts concept mentions, glossary terms, entities, and references from a parsed document via an LLM-backed pass returning validated structured output

### LLM Adapter & Determinism

- [ ] **LLM-01**: LLM-backed passes depend only on LLMPort (the domain-owned port), never directly on a specific LLM SDK or library — the concrete provider integration (e.g. a PydanticAI-based adapter) is an interchangeable implementation detail
- [ ] **LLM-02**: LLM responses are cached/recorded keyed on (document checksum, prompt version, schema version, pinned model id) so reruns against unchanged inputs reproduce identical output without re-calling the LLM
- [ ] **LLM-03**: LLM-backed passes are unit-tested against recorded responses (golden fixtures), never against a live API call in CI

### Knowledge Compiler — Concept Merge

- [ ] **KNOW-01**: System resolves aliases and merges concept mentions from multiple Document IR artifacts into canonical concepts
- [ ] **KNOW-02**: Every canonical concept contains id, canonical name, aliases, definition, category, taxonomy path, relations, provenance, and source documents
- [ ] **KNOW-03**: Concept identity is stable across compiler runs for an unchanged concept; the compiler defines explicit, deterministic identity rules (the specific algorithm — e.g. name-slug vs. registry-assigned — is an implementation decision made during planning, not fixed here, and must account for renames like "OAuth" → "OAuth 2.1" not silently minting a new identity)
- [ ] **KNOW-04**: Concept merge has a defined, deterministic ordering policy so the result does not depend on the order documents are processed in

### Relations & Taxonomy

- [ ] **REL-01**: Relations are explicit, first-class semantic objects using a documented core vocabulary (related_to, depends_on, part_of, implements, extends, replaces, uses, contains) that can be extended with new relation types over time without breaking existing data — never inferred from presentation/formatting
- [ ] **REL-02**: System has an explicit, documented policy for extracted relations that don't cleanly fit the current vocabulary (e.g. conflict record vs. related_to fallback vs. proposing a vocabulary extension), applied consistently rather than left to per-run LLM judgment
- [ ] **TAX-01**: Taxonomy is modeled as an independent semantic classification, not derived from source folder/filename/repository structure

### Provenance

- [ ] **PROV-01**: Every concept, definition, and relation preserves its origin (source document + section)

### Conflict Detection

- [ ] **CONF-01**: System detects duplicate concepts, conflicting definitions, taxonomy conflicts, alias conflicts, orphan concepts, and circular semantic relations
- [ ] **CONF-02**: Conflict detection runs after concept merge, relation building, and taxonomy building (conflicts are properties of the merged graph, not of any single document)
- [ ] **CONF-03**: Detected conflicts are written as first-class YAML conflict records — never silently auto-resolved

### Incremental Compilation

- [ ] **INCR-01**: System computes a checksum per source document and recompiles only Document IR for documents whose checksum changed
- [ ] **INCR-02**: When a document's Document IR changes, the system re-merges only the Knowledge IR affected by that document's concepts (not the full corpus), using a reverse concept→document index to determine the affected scope

### Versioning & Storage

- [ ] **VER-01**: Every generated artifact records compiler version, schema version, and prompt version
- [ ] **VER-02**: Knowledge IR readers reject (rather than silently accept or guess-coerce) artifacts whose schema version is incompatible with the reader
- [ ] **VER-03**: Each artifact records, in addition to compiler/schema/prompt version, the version of every pass that contributed to it (a "pass manifest"), so a future schema or pass change can be distinguished from a stale artifact
- [ ] **STOR-01**: Each artifact (document, concept, relation, taxonomy node, alias, conflict, metadata) is stored as an individual YAML file — no monolithic JSON
- [ ] **STOR-02**: Generated kir/ output is written to a directory separate from raw sources; raw source files are never modified by the compiler

### Extensibility

- [ ] **EXT-01**: New CompilerPass implementations can be discovered and registered without modifying the core pipeline (plugin-style registration), so third-party/future passes are addable the same way built-in passes are

### CLI

- [ ] **CLI-01**: `kir compile` runs the full pipeline (raw → Document IR → Knowledge IR) end-to-end over a directory of Markdown sources

### Acceptance

- [ ] **ACC-01**: `kir compile` succeeds end-to-end on a small reference corpus (~20 representative documents) as part of CI, with conflicts and provenance correctly recorded — this is the fast, repeatable correctness gate
- [ ] **ACC-02**: `kir compile` succeeds end-to-end on the user's real 700-document Slab Markdown export, producing Knowledge IR with conflicts and provenance correctly recorded — this is the real-world scale validation, run on demand rather than every CI run

## v2 Requirements

### Diagnostics CLI

- **DIAG-01**: `kir doctor` validates IR consistency and reports conflicts/orphans without recompiling
- **DIAG-02**: `kir stats` reports corpus statistics (concept count, relation count, conflict count, etc.)

### Conflict Workflow

- **CONF-04**: Human/LLM-assisted conflict-resolution *workflow* tooling (still never silent, still records the resolution as a versioned decision, not an automatic overwrite)

### Additional Sources

- **SRC-01**: HTML source parsing
- **SRC-02**: PDF source parsing

### Schema Evolution

- **SCHEMA-01**: Schema migration tooling for upgrading Knowledge IR artifacts between schema versions

## Out of Scope

| Feature | Reason |
|---------|--------|
| Query/retrieval API or RAG-style Q&A over the IR | KIR's API ends at the IR files; building retrieval forces a query-model commitment (graph/vector/hybrid) that belongs to downstream consumers, and reintroduces LLM-call non-determinism into what should be a clean compiled artifact. The single most tempting scope-creep vector — every comparable system surveyed treats this as their actual product. |
| Rendering/exporting to wiki formats (Logseq, Obsidian, Notion, Markdown notes) | Couples Knowledge IR schema evolution to specific renderer needs; breaks the "stable IR, swappable everything else" compiler promise. Downstream consumer's responsibility. |
| Graph database / vector store as canonical storage | KIR's canonical storage is YAML files, full stop; embedding a DB dependency introduces runtime/serving concerns and backend schema lock-in. Consumers load the IR into their own DB if they want one. |
| Automatic conflict resolution / truth-discovery voting | Resolution heuristics are inherently lossy and/or non-deterministic; violates both the determinism requirement and the "never silently resolve" requirement. Permanent exclusion, not a v1 deferral. |
| Real-time / streaming / file-watch ingestion | Adds concurrency and partial-state complexity disproportionate to a batch-compile use case; in tension with determinism (no stable notion of "current state" mid-stream). Document-level, on-demand incrementality only. |
| Multi-format source parsing (HTML, PDF, DOCX, Notion export) in v1 | Each format has structural quirks unrelated to the core semantic-merge problem; deferred until the Markdown pipeline is proven on the reference and real corpora. |
| General-purpose ontology/schema editor UI | Implies a mutable, human-edited canonical state that competes with "recompile from raw source." Same boundary violation as the renderer anti-feature. |
| `doctor`/`stats` CLI commands in v1 | Real but bounded scope-creep risk; deferred to v1.x once there's real compiled output to inspect. |
| Event Sourcing / full enterprise DDD tooling | Only tactical DDD patterns (Entities, Value Objects, Aggregates) are needed to model Concept/Relation/Taxonomy; explicitly rejected as unneeded complexity for this system's size. |
| Hardcoding the relation vocabulary or ConceptId algorithm into requirements | Both are intentionally specified as architectural contracts (core/extensible vocabulary; stable, rule-defined identity) rather than frozen implementations, so the underlying technique can evolve without rewriting requirements. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | TBD (roadmap) | Pending |
| CORE-02 | TBD (roadmap) | Pending |
| CORE-03 | TBD (roadmap) | Pending |
| CORE-04 | TBD (roadmap) | Pending |
| CORE-05 | TBD (roadmap) | Pending |
| CORE-06 | TBD (roadmap) | Pending |
| CORE-07 | TBD (roadmap) | Pending |
| PASS-01 | TBD (roadmap) | Pending |
| PASS-02 | TBD (roadmap) | Pending |
| PASS-03 | TBD (roadmap) | Pending |
| PASS-04 | TBD (roadmap) | Pending |
| PASS-05 | TBD (roadmap) | Pending |
| DOC-01 | TBD (roadmap) | Pending |
| DOC-02 | TBD (roadmap) | Pending |
| DOC-03 | TBD (roadmap) | Pending |
| LLM-01 | TBD (roadmap) | Pending |
| LLM-02 | TBD (roadmap) | Pending |
| LLM-03 | TBD (roadmap) | Pending |
| KNOW-01 | TBD (roadmap) | Pending |
| KNOW-02 | TBD (roadmap) | Pending |
| KNOW-03 | TBD (roadmap) | Pending |
| KNOW-04 | TBD (roadmap) | Pending |
| REL-01 | TBD (roadmap) | Pending |
| REL-02 | TBD (roadmap) | Pending |
| TAX-01 | TBD (roadmap) | Pending |
| PROV-01 | TBD (roadmap) | Pending |
| CONF-01 | TBD (roadmap) | Pending |
| CONF-02 | TBD (roadmap) | Pending |
| CONF-03 | TBD (roadmap) | Pending |
| INCR-01 | TBD (roadmap) | Pending |
| INCR-02 | TBD (roadmap) | Pending |
| VER-01 | TBD (roadmap) | Pending |
| VER-02 | TBD (roadmap) | Pending |
| VER-03 | TBD (roadmap) | Pending |
| STOR-01 | TBD (roadmap) | Pending |
| STOR-02 | TBD (roadmap) | Pending |
| EXT-01 | TBD (roadmap) | Pending |
| CLI-01 | TBD (roadmap) | Pending |
| ACC-01 | TBD (roadmap) | Pending |
| ACC-02 | TBD (roadmap) | Pending |

**Coverage:**
- v1 requirements: 39 total
- Mapped to phases: 0 (populated by roadmap creation)
- Unmapped: 39 ⚠️ (expected — roadmap not yet created)

---
*Requirements defined: 2026-06-29*
*Last updated: 2026-06-29 after incorporating user's architectural-contract feedback (compiler pipeline, CompilerContext, pass diagnostics/isolation, provider-agnostic LLM port, flexible identity/vocabulary, two-tier acceptance, IR compatibility, pass manifest, plugin extensibility)*
