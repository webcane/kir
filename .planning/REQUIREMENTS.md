# Requirements: KIR (Knowledge Intermediate Representation)

**Defined:** 2026-06-29
**Core Value:** Given identical raw sources, compiler version, prompt version, and schema version, KIR must deterministically compile raw Markdown into a canonical Knowledge IR that merges concepts/relations/taxonomy across documents, preserves full provenance, and explicitly records (never silently resolves) semantic conflicts.

## M1 — Current Roadmap Scope (Phases 1-2)

Requirements actively being planned/executed. Maps to phases in `.planning/ROADMAP.md`.

### Compiler Foundation

- [x] **CORE-01**: Domain model (Concept, Relation, Taxonomy, Document entities; ConceptId, RelationId, Checksum, SourceRef value objects) has zero import-level dependency on LLM SDKs, filesystem, or YAML libraries
- [x] **CORE-02**: System exposes ports (LLMPort, RepositoryPort, MarkdownParserPort) as typed interfaces that adapters implement, so swapping an LLM provider or storage backend never requires touching domain code
- [x] **CORE-03**: Compiler passes register independently (decorator/plugin-based registry) such that adding a new pass never requires modifying existing passes
- [x] **CORE-04**: Compiler executes a deterministic pipeline of CompilerPass instances; each pass declares what it consumes, what it produces, and its dependencies, and the pipeline resolves execution order automatically from those declarations rather than a hardcoded sequence
- [x] **CORE-05**: All compiler passes execute inside a shared, immutable CompilerContext (carrying config, cache, repository, LLM port, logger, metrics, versions) rather than receiving these piecemeal
- [x] **CORE-06**: Every pass returns structured diagnostics (each with code, severity, source location, and optional suggestion — Rust-compiler-style) as part of its output artifact, instead of printing or logging output directly
- [x] **CORE-07**: Passes never mutate a previous IR in place; each pass produces a new immutable artifact

### Compiler Passes (architectural contract)

- [x] **PASS-01**: Every transformation of knowledge is implemented as a CompilerPass
- [x] **PASS-02**: Each pass consumes exactly one IR representation and produces exactly one IR representation
- [x] **PASS-03**: Passes are deterministic and independently testable in isolation
- [x] **PASS-04**: Passes communicate only through IR artifacts and CompilerContext — never through side channels or shared mutable state
- [x] **PASS-05**: Pass execution order is derived from declared dependencies (see CORE-04), not hardcoded sequencing

### Document Compiler

- [x] **DOC-01**: System parses a single Markdown source into Document IR (id, title, source, checksum, language, sections, concepts, glossary, entities, references)
- [x] **DOC-02**: Document IR for one document never merges information from another document
- [x] **DOC-03**: System extracts concept mentions, glossary terms, entities, and references from a parsed document via an LLM-backed pass returning validated structured output

### LLM Adapter & Determinism

- [x] **LLM-01**: LLM-backed passes depend only on LLMPort (the domain-owned port), never directly on a specific LLM SDK or library — the concrete provider integration (e.g. a PydanticAI-based adapter) is an interchangeable implementation detail
- [x] **LLM-02**: LLM responses are cached/recorded keyed on (document checksum, prompt version, schema version, pinned model id) so reruns against unchanged inputs reproduce identical output without re-calling the LLM
- [x] **LLM-03**: LLM-backed passes are unit-tested against recorded responses (golden fixtures), never against a live API call in CI

### Extensibility

- [x] **EXT-01**: New CompilerPass implementations can be discovered and registered without modifying the core pipeline (plugin-style registration), so third-party/future passes are addable the same way built-in passes are

### Storage

- [x] **STOR-01**: Each artifact (document, concept, relation, taxonomy node, alias, conflict, metadata) is stored as an individual YAML file — no monolithic JSON
- [x] **STOR-02**: Generated kir/ output is written to a directory separate from raw sources; raw source files are never modified by the compiler

## M2 — Future Milestone Scope, Already Defined (Knowledge Compiler + Validation)

Already-decided v1 scope — not deferred, not speculative — but not yet broken into detailed phases in ROADMAP.md. Will become Phase 3 (Knowledge Compiler) and Phase 4 (Validation) when M1 completes and the roadmap is rewritten for M2. See PROJECT.md ## Milestones.

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

### Versioning

- [ ] **VER-01**: Every generated artifact records compiler version, schema version, and prompt version
- [ ] **VER-02**: Knowledge IR readers reject (rather than silently accept or guess-coerce) artifacts whose schema version is incompatible with the reader
- [ ] **VER-03**: Each artifact records, in addition to compiler/schema/prompt version, the version of every pass that contributed to it (a "pass manifest"), so a future schema or pass change can be distinguished from a stale artifact

### Testing Infrastructure

- [ ] **TEST-01**: Pipeline output is verifiable via golden-file comparison (compiled Knowledge IR vs. a committed expected YAML snapshot), not only field-by-field assertions, so any unintended output drift is caught automatically
- [ ] **TEST-02**: Test fixtures are organized in three tiers by corpus size — tiny (~5 docs, runs on every CI commit), medium (~50 docs, regression coverage), real (the 700-doc Slab export, on-demand acceptance) — so test cost scales with how often each tier needs to run

### Acceptance

- [ ] **ACC-01**: `kir compile` succeeds end-to-end on the tiny and medium reference corpora as part of CI, with conflicts and provenance correctly recorded and verified against golden-file snapshots — this is the fast, repeatable correctness gate

## M3 — Future Milestone Scope, Already Defined (Incremental Compilation + CLI)

Already-decided v1 scope — not deferred, not speculative — but not yet broken into detailed phases in ROADMAP.md. Will become Phase 5 (Incremental Compilation) and Phase 6 (CLI & Real-Corpus Acceptance) when M2 completes. See PROJECT.md ## Milestones.

### Incremental Compilation

- [ ] **INCR-01**: System computes a checksum per source document and recompiles only Document IR for documents whose checksum changed
- [ ] **INCR-02**: When a document's Document IR changes, the system re-merges only the Knowledge IR affected by that document's concepts (not the full corpus), using a reverse concept→document index to determine the affected scope

### CLI

- [ ] **CLI-01**: `kir compile` runs the full pipeline (raw → Document IR → Knowledge IR) end-to-end over a directory of Markdown sources

### Acceptance

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

| Requirement | Milestone | Phase | Status |
|-------------|-----------|-------|--------|
| CORE-01 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| CORE-02 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| CORE-03 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| CORE-04 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| CORE-05 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| CORE-06 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| CORE-07 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| PASS-01 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| PASS-02 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| PASS-03 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| PASS-04 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| PASS-05 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| EXT-01 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| STOR-01 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| STOR-02 | M1 | Phase 1 (in ROADMAP.md) | Pending |
| DOC-01 | M1 | Phase 2 (in ROADMAP.md) | Pending |
| DOC-02 | M1 | Phase 2 (in ROADMAP.md) | Pending |
| DOC-03 | M1 | Phase 2 (in ROADMAP.md) | Pending |
| LLM-01 | M1 | Phase 2 (in ROADMAP.md) | Pending |
| LLM-02 | M1 | Phase 2 (in ROADMAP.md) | Pending |
| LLM-03 | M1 | Phase 2 (in ROADMAP.md) | Pending |
| KNOW-01 | M2 | Phase 3 (future) | Not yet planned |
| KNOW-02 | M2 | Phase 3 (future) | Not yet planned |
| KNOW-03 | M2 | Phase 3 (future) | Not yet planned |
| KNOW-04 | M2 | Phase 3 (future) | Not yet planned |
| REL-01 | M2 | Phase 3 (future) | Not yet planned |
| REL-02 | M2 | Phase 3 (future) | Not yet planned |
| TAX-01 | M2 | Phase 3 (future) | Not yet planned |
| PROV-01 | M2 | Phase 3 (future) | Not yet planned |
| CONF-01 | M2 | Phase 3 (future) | Not yet planned |
| CONF-02 | M2 | Phase 3 (future) | Not yet planned |
| CONF-03 | M2 | Phase 3 (future) | Not yet planned |
| VER-01 | M2 | Phase 4 (future) | Not yet planned |
| VER-02 | M2 | Phase 4 (future) | Not yet planned |
| VER-03 | M2 | Phase 4 (future) | Not yet planned |
| TEST-01 | M2 | Phase 4 (future) | Not yet planned |
| TEST-02 | M2 | Phase 4 (future) | Not yet planned |
| ACC-01 | M2 | Phase 4 (future) | Not yet planned |
| INCR-01 | M3 | Phase 5 (future) | Not yet planned |
| INCR-02 | M3 | Phase 5 (future) | Not yet planned |
| CLI-01 | M3 | Phase 6 (future) | Not yet planned |
| ACC-02 | M3 | Phase 6 (future) | Not yet planned |

**Coverage:**
- v1 requirements: 42 total, across 3 milestones (M1: 21, M2: 17, M3: 4)
- Mapped to a milestone/phase: 42 ✓
- Detailed-planned in current ROADMAP.md (M1 only): 21 (Phases 1-2)
- Not yet detail-planned (M2/M3 — already scoped, awaiting their milestone): 21
- Unmapped: 0

**Note on milestone restructure (2026-06-29):** Per user feedback, ROADMAP.md was trimmed to only the current milestone (M1, Phases 1-2) rather than carrying all 6 phases up front — PROJECT.md now holds the persistent ## Milestones (M1/M2/M3) and ## Architecture & Workstreams views, while ROADMAP.md is rewritten per-milestone. This table reflects that split: "Pending" = actively planned in the current ROADMAP.md; "Not yet planned" = already-decided v1 scope, correctly deferred from detailed planning until its milestone becomes current (not a scope cut). The "39 total" miscount from initial requirements-definition was corrected to 40 during original roadmap creation, then grew to 42 with TEST-01/TEST-02 (golden-file testing, tiered fixture corpora).

---
*Requirements defined: 2026-06-29*
*Last updated: 2026-06-29 — restructured into M1 (current roadmap scope) / M2 / M3 (future milestone scope, already defined) sections and traceability columns, mirroring the Milestones split now documented in PROJECT.md. No requirements were added, removed, or rescoped in this pass — only their presentation relative to "currently planned" vs. "future milestone" was reorganized.*
