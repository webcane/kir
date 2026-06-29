# Feature Research

**Domain:** Knowledge-extraction / semantic-compiler / ontology-construction-from-documents systems
**Researched:** 2026-06-29
**Confidence:** MEDIUM-HIGH (table stakes and anti-features are well-corroborated across multiple independent systems; specific complexity estimates are KIR-context judgment calls, not measured)

## Comparable Systems Surveyed

- **Microsoft GraphRAG** — most directly comparable: an indexing *pipeline* (not a wiki/UI) that turns raw text into entities/relationships/communities, with Parquet artifacts as its "IR." Added incremental indexing in v0.4.0/v1.0 after users hit full-reindex pain at scale. [GitHub](https://github.com/microsoft/graphrag), [docs](https://microsoft.github.io/graphrag/index/overview/), [incremental indexing](https://github.com/microsoft/graphrag/discussions/511)
- **Cognee** — AI agent memory platform; "ECL" (Extract-Cognify-Load) pipeline, modular passes, multi-backend graph storage, explicit incremental-learning feature. Useful as a counterexample: it deliberately bundles storage/retrieval/serving, which KIR explicitly rejects. [GitHub](https://github.com/topoteretes/cognee)
- **EDC (Extract-Define-Canonicalize)** — academic LLM-KG-construction framework; clean three-stage decomposition (open extraction → schema definition → canonicalization) that maps closely onto KIR's ExtractConcepts → ResolveAliases → MergeConcepts passes. [arXiv:2404.03868](https://arxiv.org/html/2404.03868v1)
- **Ontology Learning "Layer Cake"** — classical decomposition of ontology-from-text into term extraction → concept formation → taxonomy → relation extraction → rule extraction. KIR's pass pipeline is a modern, LLM-backed instance of this same layer cake. [Wimalasuriya survey](https://www.cs.uoregon.edu/Reports/AREA-200903-Wimalasuriya.pdf)
- **Truth discovery / knowledge fusion literature** — decades of DB research on what happens when multiple sources disagree (TruthFinder, CRH, etc.) — overwhelmingly about *resolving* conflicts via source reliability voting. KIR's design (record, never auto-resolve) is a deliberate, defensible departure from this default, not an oversight. [TruthFinder](http://web.cs.ucla.edu/~yzsun/classes/2014Spring_CS7280/Papers/Trust/kdd07_xyin.pdf)
- **Karpathy-style "LLM knowledge base as compiler" framing** — informal but directly on-point articulation of the same LLVM-for-knowledge analogy KIR uses, independently arriving at incremental compilation and dependency tracking as the feature that "separates a research prototype from a production knowledge base." [MindStudio summary](https://www.mindstudio.ai/blog/karpathy-llm-knowledge-base-architecture-compiler-analogy)

## Feature Landscape

### Table Stakes (Users Expect These)

Features every credible knowledge-extraction/compiler system has. Missing these makes KIR feel like a toy extraction script, not a compiler.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Entity/concept extraction from raw text | The baseline capability every comparable system (GraphRAG, Cognee, EDC, every ontology-learning pipeline) leads with | MEDIUM | KIR: `ExtractConcepts` pass, LLM-backed via PydanticAI. Already in PROJECT.md scope. |
| Relation extraction as explicit typed edges | All surveyed systems treat relations as first-class, typed objects, not just co-occurrence | MEDIUM | KIR already specifies a closed relation vocabulary (related_to, depends_on, part_of, etc.) — stricter than GraphRAG's free-text relations, which is a deliberate, defensible choice for determinism |
| Entity/alias canonicalization (dedup + synonym merge) | Every surveyed system (EDC's "Canonicalize" stage, GraphRAG dedup, Cognee's Memify) treats this as non-negotiable — raw LLM extraction always produces near-duplicate mentions | HIGH | This is the hardest pass in any such pipeline. KIR's `ResolveAliases`/`MergeConcepts` passes correspond directly to EDC's canonicalization stage. Expect this to be the most failure-prone pass at 700-doc scale. |
| Source/provenance tracking per fact | Universal across surveyed systems in some form (GraphRAG keeps source chunk refs; truth-discovery literature is built entirely around per-source attribution) | LOW-MEDIUM | KIR's per-element (document + section) provenance is actually *more* granular than GraphRAG's default (which tracks at text-unit/chunk level). This is a genuine strength to lean into. |
| Stable, deterministic IDs across reruns | Needed for any system that claims to be incremental or diffable; GraphRAG's pre-1.0 versions lacked this and it forced full reindexes on every update (explicitly called out as a limitation they later fixed) | LOW-MEDIUM | KIR's slug-of-canonical-name approach is simpler than GraphRAG's UUID approach but has a real failure mode: renames. PROJECT.md already names this risk ("stability... handled via explicit alias/merge tracking") — flag for PITFALLS. |
| Incremental rebuild (don't reprocess unchanged sources) | Explicitly called "the feature that separates a research prototype from a production knowledge base" (Karpathy framing); GraphRAG added this as a major version feature after users hit full-reindex costs in production | MEDIUM-HIGH | KIR's checksum-based per-document diffing is simpler than GraphRAG's incremental indexing (which has to handle graph-merge semantics); KIR's scope (re-merge only affected Knowledge IR) is appropriately scoped for v1. |
| Versioned/reproducible output (compiler+schema+prompt version stamped on artifacts) | Determinism is the precondition for any "compiler" framing to be credible; without it, incremental rebuild and golden-fixture testing are both meaningless | LOW | Already in PROJECT.md scope. This is what makes the LLVM analogy more than marketing — verify it's enforced (CI test that reruns produce byte-identical output) rather than just specified. |
| Conflict/inconsistency detection | All comparable systems have *some* mechanism — most resolve via truth-discovery/voting (GraphRAG, Cognee implicitly via "memify" cleanup), but the *detection* step (duplicate concepts, contradictory definitions, orphan/cyclic relations) is universal | MEDIUM-HIGH | KIR differentiates here on the resolution policy (next section), not detection itself. Detection (duplicate concepts, conflicting definitions, taxonomy conflicts, alias conflicts, orphans, cycles) is table stakes; what KIR does with conflicts is the differentiator. |
| Modular/extensible processing pipeline (independent passes) | EDC, the ontology layer-cake model, and GraphRAG's workflow system all decompose into independently runnable/testable stages — this is the standard architecture for this entire problem class, not unique to compilers | MEDIUM | KIR's pass-registration mechanism is well-aligned with prior art; the differentiator is doing it with a genuinely typed IR-to-IR contract per pass rather than a loosely-coupled DAG of side-effecting steps (GraphRAG's workflow model is closer to the latter). |
| Taxonomy/category structure over concepts | Ontology-learning layer cake treats this as a required late stage; GraphRAG's community detection is a (statistical, not semantic) analog | MEDIUM | KIR's LLM-driven taxonomy classification (semantic, not folder/community-derived) is closer to true ontology-learning than GraphRAG's Leiden-clustering approach, which is statistical and unstable run-to-run. |

### Differentiators (Competitive Advantage)

Features that set KIR apart from the surveyed comparable systems. These should be the focus of the project's identity — not hedged, not "also offers."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Conflicts recorded as first-class artifacts, never silently resolved | Every surveyed system (GraphRAG, Cognee, truth-discovery literature broadly) defaults to *resolving* conflicts via voting/reliability heuristics, which silently discards information and is non-deterministic/order-dependent. KIR's "always surface, never auto-resolve" stance is a genuine, citable departure from the field's default — and it composes with the determinism requirement (auto-resolution via LLM vote would itself be a non-deterministic, version-fragile process) | MEDIUM | This is KIR's strongest differentiator. It should be advertised as a feature, not apologized for as "we haven't built conflict resolution yet." PROJECT.md already encodes this correctly as permanent, not a v1 deferral — keep it that way through the roadmap. |
| Stable, typed, versioned IR as the literal product boundary | GraphRAG's "IR" (Parquet tables) and Cognee's graph are internal implementation details consumed by their own query/retrieval layers — neither exposes a stable schema contract as the product. KIR inverts this: the IR *is* the product, with no downstream rendering/serving in scope | MEDIUM | This is the core "LLVM for knowledge" claim. The differentiation is real only if the schema is actually versioned and consumers can pin to a schema version — verify this is enforced, not just declared. |
| Closed, explicit relation vocabulary (no free-text relations) | GraphRAG and most LLM-KG-construction surveys extract free-text/open relation labels (e.g., "is influenced by," "works alongside") which are expressive but make merging, querying, and determinism harder. KIR's fixed vocabulary (depends_on, part_of, implements, etc.) trades some expressiveness for mergeability and stability | LOW-MEDIUM | Real differentiator vs. open-relation-extraction systems, but watch the failure mode: real corpora (700 Slab docs) will produce relations that don't fit the closed vocabulary cleanly. Decide now whether "doesn't fit" becomes a conflict record, an `related_to` fallback, or a rejected extraction — this needs an explicit policy, not implicit LLM judgment call per-run (which would break determinism). |
| Per-element provenance (document + section), not per-chunk | GraphRAG tracks provenance at the text-unit/chunk level (coarser); KIR ties provenance to every concept, definition, and relation individually | LOW-MEDIUM | Genuine, demonstrable granularity advantage. Worth highlighting in any comparison with GraphRAG specifically. |
| Independently testable passes with golden-fixture LLM mocking | Most LLM-KG pipelines (GraphRAG, Cognee) are tested end-to-end or not at all for the LLM-backed stages, because nondeterminism makes unit testing them awkward. KIR's recorded/mocked-response testing strategy for LLM passes is a deliberate answer to a problem the field mostly doesn't solve | MEDIUM | This is more of an engineering-process differentiator than a user-facing feature, but it directly enables the determinism claim to be verifiable rather than asserted. |
| Taxonomy decoupled from source folder/file hierarchy | Most personal-knowledge tools (and even some KG pipelines that bootstrap from directory structure) conflate "where the file lives" with "what category it belongs to." KIR explicitly models taxonomy as a separate semantic artifact derived by the compiler, never inherited from source layout | LOW-MEDIUM | This matters concretely for the 700-doc Slab export, where Slab's own folder structure reflects org/team boundaries, not semantic categories — a real, not hypothetical, distinction. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that look attractive (or that comparable systems bundle in) but would compromise KIR's "API ends at the IR" boundary or its determinism guarantee.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|------------------|-------------|
| Rendering/exporting to a wiki format (Logseq, Obsidian, Notion, Markdown notes) | Natural "make it useful immediately" ask once you have a graph; every comparable system (GraphRAG's query layer, Cognee's full memory stack) bundles some form of this | Couples the IR schema's evolution to specific renderer needs, breaks the "stable IR, swappable everything else" compiler promise, and turns scope creep into a permanent maintenance burden (each new renderer = new compatibility surface) | Downstream consumer's job, per PROJECT.md. KIR ships a schema and example/reference adapter docs at most, never a renderer. |
| Graph database / vector store as the canonical storage | Almost every comparable system (Cognee explicitly, GraphRAG's embeddings step) treats a graph DB or vector index as part of the core product, because it's needed for *querying* | KIR's deliverable is the IR, not a query interface; embedding a DB dependency would mean the "compiler" suddenly has runtime/serving concerns, contradicts the YAML-file-per-artifact/git-friendly storage requirement, and creates schema lock-in to a specific backend's query model | Keep canonical storage as plain YAML files. Anyone wanting graph/vector query support loads the IR into their own DB — that's the explicit downstream boundary. |
| Automatic conflict resolution / "best answer" voting (truth discovery) | Standard expectation from anyone who's used a system that resolves conflicting facts automatically (this is the default in essentially all truth-discovery and knowledge-fusion literature) | Auto-resolution requires either a non-deterministic heuristic (source-reliability voting, LLM judgment) or silent data loss — both violate KIR's core determinism and "never silently resolve" requirements simultaneously | Conflicts are recorded as structured artifacts for human or separately-versioned LLM-assisted review, never resolved inline during compilation. (Already correctly scoped in PROJECT.md — protect this from scope creep during roadmap planning.) |
| Real-time / streaming incremental updates (sub-document, file-watch, live ingestion) | "Incremental" gets conflated with "live" — Cognee and some enterprise KG pipelines do support streaming ingestion | Adds concurrency, partial-state, and ordering complexity disproportionate to KIR's actual need (batch compile of a document corpus); also in tension with determinism (need to define "current state" at any instant) | Per-document checksum diffing on each `kir compile` invocation, run on demand. Document-level incrementality, not sub-document/streaming. Already correctly scoped. |
| Multi-format source parsing (HTML, PDF, DOCX, Notion export, etc.) in v1 | Real-world corpora are rarely pure Markdown; tempting to generalize the parser early since "compiler front-ends are usually swappable anyway" | Each format has its own structural quirks (PDF layout reconstruction, HTML semantic noise) that will surface edge cases unrelated to the core semantic-merge problem KIR is trying to prove out; dilutes focus before the 700-doc Markdown acceptance bar is met | Defer additional parsers until the Document IR / Knowledge IR pipeline is proven at scale on Markdown. Already correctly scoped as Out of Scope in PROJECT.md. |
| General-purpose ontology/ schema editor UI | Once concepts/taxonomy exist, an obvious "let humans fix it up" UI suggests itself, and several ontology-management tools (Protege-style) bundle this | This is a wiki/editor concern wearing an ontology hat — same boundary violation as the renderer anti-feature, and a UI implies a mutable, human-edited canonical state that competes with the compiler's "recompile from raw source" model | If humans need to correct extraction errors, that happens via prompt/schema/source changes that get recompiled — not via direct edits to generated YAML. Direct YAML edits would be silently overwritten on next compile anyway, which is itself worth documenting as expected behavior. |
| Query/retrieval API or RAG-style Q&A over the IR | This is the single most common feature in every comparable system (GraphRAG's entire raison d'être is the Q-layer on top of the graph; Cognee is explicitly a "memory for agents" retrieval product) | Building retrieval means committing to a query model (graph traversal? vector similarity? hybrid?) which is exactly the kind of downstream-consumer decision PROJECT.md says KIR must stay agnostic to; it would also reintroduce non-determinism (LLM-based Q&A) into what should be a clean compiled artifact | KIR's API ends at the IR files. Any consumer wanting Q&A loads the IR into their own RAG/graph stack. This is arguably the single most important anti-feature to hold the line on, since it is the default feature of literally every other system surveyed. |
| `doctor`/`stats` diagnostic commands in v1 | Natural "let me inspect what got compiled" ask once any non-trivial corpus is run through | Not a boundary violation like the others, but a real scope-creep risk: feels small, but invites building ad hoc reporting/visualization logic that creeps toward the wiki/dashboard anti-feature if not bounded | Already correctly deferred past v1 in PROJECT.md. When eventually built, scope tightly to artifact-validity/structural reporting (counts, conflict summaries) — not visualization. |

## Feature Dependencies

```
Entity/concept extraction (ExtractConcepts)
    └──requires──> Document parsing + sectioning (Parse → Section → Metadata)

Alias/synonym resolution (ResolveAliases)
    └──requires──> Entity/concept extraction
                       └──enables──> Concept merging across documents (MergeConcepts)

Concept merging (MergeConcepts)
    └──requires──> Alias/synonym resolution
    └──requires──> Stable deterministic concept IDs
                       └──enables──> Relation building (BuildRelations) at canonical-concept granularity

Relation building (BuildRelations)
    └──requires──> Concept merging (relations are between canonical concepts, not raw mentions)
                       └──enables──> Taxonomy building (BuildTaxonomy) and Conflict detection

Taxonomy building (BuildTaxonomy)
    └──requires──> Concept merging
    └──conflicts-if-coupled-to──> Source folder/file hierarchy (must stay independent, per Anti-Features)

Conflict detection (Conflict pass)
    └──requires──> Concept merging, Relation building, Taxonomy building
                       (conflicts are detected ACROSS the merged outputs of prior passes, must run last)

Provenance tracking
    └──cross-cuts──> every pass (not a separate pass; an invariant every pass must preserve)

Incremental rebuild (checksum diffing)
    └──requires──> Stable deterministic concept IDs (without ID stability, "only re-merge affected IR" is undefined)
    └──requires──> Per-artifact versioning (compiler/schema/prompt version stamps)

Deterministic/reproducible output
    └──requires──> LLM passes tested via recorded/mocked responses (golden fixtures)
    └──requires──> Closed relation vocabulary (free-text relation extraction would reintroduce LLM-call variance into the schema itself)
    └──enables──> Incremental rebuild (determinism is the precondition — without it, "unchanged source → unchanged output" can't be trusted, defeating the point of skipping recompilation)

Query/retrieval API (ANTI-FEATURE)
    └──conflicts──> Stable IR-as-product-boundary (building retrieval forces a query-model commitment KIR should stay agnostic to)

Automatic conflict resolution (ANTI-FEATURE)
    └──conflicts──> Determinism requirement AND "never silently resolve" requirement (resolution heuristics are inherently lossy and/or non-deterministic)

Rendering/wiki export (ANTI-FEATURE)
    └──conflicts──> Stable IR-as-product-boundary (couples IR schema evolution to specific renderer needs)
```

### Dependency Notes

- **MergeConcepts requires stable deterministic concept IDs:** Without ID stability across runs, "incremental compilation" (re-merge only affected Knowledge IR) has no anchor to diff against — this is exactly the limitation pre-1.0 GraphRAG hit and had to retrofit. Get ID stability right before building incremental rebuild on top of it.
- **Conflict detection must run after merge/relation/taxonomy passes, not interleaved:** Conflicts (duplicate concepts, taxonomy conflicts, alias conflicts, cycles) are properties of the *merged* graph, not of any single document — this is why it's the last pass in PROJECT.md's pipeline order, and that ordering should be treated as load-bearing, not incidental.
- **Determinism requirement enables incremental rebuild:** This is the most important transitive dependency in the whole system. If LLM passes aren't pinned/recorded and relation vocabulary isn't closed, then "unchanged checksum → skip rebuild" is not actually safe, because the *meaning* of "unchanged" silently degrades. Roadmap should sequence determinism-enforcing work (golden fixtures, version stamping) before or alongside incremental rebuild, not after.
- **Query/retrieval API conflicts with stable IR boundary:** This is the most consequential anti-feature/differentiator tension to police during roadmap planning, because it is the single most natural "obvious next feature" once a working IR exists, and it is the feature nearly every comparable system in this research treats as their actual product.
- **Taxonomy building conflicts with source-hierarchy coupling:** Worth a regression-style check in v1 testing (e.g., the 700-doc Slab corpus has its own folder structure) — verify taxonomy assignment doesn't correlate suspiciously well with source folder, which would indicate the LLM pass is shortcutting via filename/path leakage rather than semantic content.

## MVP Definition

### Launch With (v1)

Minimum viable product to validate the compiler concept end-to-end on the real 700-document corpus. This list is already well-aligned with PROJECT.md's "Active" requirements — restated here through the features lens for traceability.

- [ ] Document parsing → Document IR (per-document, no cross-document merge) — proves the front-end half of the compiler works in isolation
- [ ] Concept extraction + alias resolution + merge → canonical concepts with stable IDs — the core "this is genuinely a compiler, not a dump of LLM output" capability
- [ ] Typed relation extraction (closed vocabulary) — essential because it's both a table-stakes capability and KIR's stated differentiator vs. open-relation extraction
- [ ] Taxonomy classification, independent of source structure — essential differentiator vs. naive folder-based or community-detection-based grouping
- [ ] Per-element provenance (document + section) on every concept/definition/relation — table stakes, and the basis for the provenance differentiator
- [ ] Conflict detection (duplicates, contradictions, taxonomy/alias conflicts, orphans, cycles) recorded as artifacts, never resolved — KIR's headline differentiator; cannot be deferred without losing the project's core thesis
- [ ] Incremental rebuild via per-document checksum diffing — table stakes for any corpus this size; full-recompile-only would make iteration on the 700-doc corpus painfully slow during development itself
- [ ] Compiler/schema/prompt version stamping on every artifact — prerequisite for both determinism claims and safe incremental rebuild
- [ ] One-YAML-file-per-artifact repository layout — table stakes for the "git-friendly compiled output" identity
- [ ] `kir compile` end-to-end CLI — the only user-facing surface needed to validate the concept

### Add After Validation (v1.x)

Trigger: v1 succeeds on the 700-doc corpus and conflicts/provenance are validated as useful by the user reviewing real output.

- [ ] `kir doctor` / `kir stats` diagnostic commands — trigger: once there's enough real compiled output that ad hoc YAML inspection becomes the bottleneck
- [ ] Conflict-resolution workflow tooling (still human/LLM-assisted, still never silent) — trigger: once enough real conflicts have accumulated on the 700-doc corpus to know what a useful resolution UX even looks like (this is explicitly a *workflow* feature, not auto-resolution — the "never silently resolve" rule stays permanent)
- [ ] Additional source parsers (HTML, PDF, Notion export) — trigger: Markdown pipeline proven at scale AND a concrete second corpus in a different format becomes available

### Future Consideration (v2+)

- [ ] Schema migration tooling for Knowledge IR version upgrades — defer until there's a second schema version to migrate to/from; premature before that
- [ ] Reference/example downstream adapter (e.g., a thin sample renderer into one wiki format, kept clearly out-of-tree) — defer because building even a reference adapter risks blurring the "KIR doesn't render" boundary in the eyes of early adopters; only worth doing once the boundary is well-established by usage

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Concept extraction + merge with stable IDs | HIGH | HIGH | P1 |
| Typed relation extraction (closed vocab) | HIGH | MEDIUM | P1 |
| Provenance tracking (document + section) | HIGH | LOW | P1 |
| Conflict detection (record, never resolve) | HIGH | MEDIUM | P1 |
| Taxonomy classification (structure-independent) | MEDIUM | MEDIUM | P1 |
| Incremental rebuild (checksum diffing) | HIGH | MEDIUM | P1 |
| Version stamping (compiler/schema/prompt) | MEDIUM | LOW | P1 |
| YAML-per-artifact repo layout | MEDIUM | LOW | P1 |
| `doctor`/`stats` commands | MEDIUM | LOW | P2 |
| Conflict-resolution workflow tooling | MEDIUM | MEDIUM | P2 |
| Additional source parsers | LOW (for v1 corpus) | HIGH | P3 |
| Schema migration tooling | LOW (no v2 schema yet) | MEDIUM | P3 |
| Query/retrieval API | N/A — anti-feature | N/A | Reject |
| Rendering/wiki export | N/A — anti-feature | N/A | Reject |
| Automatic conflict resolution | N/A — anti-feature | N/A | Reject |

**Priority key:**
- P1: Must have for v1 (matches PROJECT.md's "Active" requirements and the 700-doc acceptance bar)
- P2: Should have, add once v1 is validated
- P3: Nice to have, future consideration
- Reject: Deliberately out of scope, permanent (not a deferral)

## Competitor Feature Analysis

| Feature | GraphRAG (Microsoft) | Cognee | KIR's Approach |
|---------|----------------------|--------|-----------------|
| Relation typing | Open/free-text relations extracted per text unit | Graph + vector hybrid, relation types emerge from extraction, less constrained | Closed, explicit vocabulary (related_to, depends_on, part_of, implements, extends, replaces, uses, contains) — trades expressiveness for mergeability/determinism |
| Conflict handling | Implicit — no explicit conflict ledger; community summarization tends to smooth over contradictions | "Memify" post-processing pipeline cleans/optimizes the graph, implying some silent normalization | Explicit conflict detection across 6 categories, recorded as permanent artifacts, never auto-resolved |
| Provenance granularity | Per text-unit/chunk | Not clearly documented at per-fact granularity | Per concept/definition/relation, tied to document + section |
| Incremental updates | Added in v0.4.0/v1.0 after full-reindex pain; supports diff + merge | "Incremental learning" advertised as a core feature from the start | Per-document checksum diffing, re-merge only affected Knowledge IR; scoped to v1 from day one |
| Storage format | Parquet tables + configurable vector store | Unified relational + vector + graph engine (NetworkX/FalkorDB/Neo4j) | One YAML file per artifact — git-diffable, human-readable, no DB dependency |
| Taxonomy/grouping | Statistical community detection (Leiden algorithm) — clusters by graph structure, not semantic category | Ontology generation described as "cognitive-science-grounded" but bundled with retrieval concerns | LLM-driven semantic taxonomy classification, explicitly decoupled from any structural/statistical proxy |
| Product boundary | Indexing pipeline + query/retrieval layer (DRIFT, local/global search) bundled together | Full "memory platform": extraction + storage + retrieval + agent integrations bundled | API ends at the IR; no query/retrieval, no storage backend choice, no agent integration — those are all downstream |
| Determinism / testability | Not a stated design goal; LLM extraction variance is accepted | Not a stated design goal | Explicit design goal: golden-fixture testing for LLM passes, version-stamped artifacts, deterministic concept IDs |

## Sources

- [Microsoft GraphRAG (GitHub)](https://github.com/microsoft/graphrag) — MEDIUM confidence (official repo, but architecture details required cross-referencing docs site)
- [GraphRAG indexing overview docs](https://microsoft.github.io/graphrag/index/overview/) — MEDIUM-HIGH confidence (official docs)
- [GraphRAG incremental indexing discussion #511](https://github.com/microsoft/graphrag/discussions/511) — MEDIUM confidence (official GitHub discussion, community-reported but maintainer-engaged)
- [GraphRAG incremental indexing issue #741](https://github.com/microsoft/graphrag/issues/741) — MEDIUM confidence
- [Cognee (GitHub)](https://github.com/topoteretes/cognee) — MEDIUM confidence (official repo README)
- [Extract-Define-Canonicalize (EDC) framework, arXiv:2404.03868](https://arxiv.org/html/2404.03868v1) — HIGH confidence (peer-reviewed-track arXiv paper, directly maps to KIR's pass structure)
- [Ontology-Based Information Extraction survey, Wimalasuriya](https://www.cs.uoregon.edu/Reports/AREA-200903-Wimalasuriya.pdf) — MEDIUM confidence (academic survey, somewhat dated but the layer-cake model remains the standard reference decomposition)
- [LLM-empowered knowledge graph construction: A survey, arXiv:2510.20345](https://arxiv.org/html/2510.20345v1) — MEDIUM-HIGH confidence (recent survey covering canonicalization/dedup approaches)
- [Truth discovery with multiple conflicting information providers, KDD'07](http://web.cs.ucla.edu/~yzsun/classes/2014Spring_CS7280/Papers/Trust/kdd07_xyin.pdf) — HIGH confidence (foundational, widely-cited paper establishing the field's default "resolve conflicts via voting" approach that KIR deliberately departs from)
- [Karpathy compiler-analogy summary, MindStudio blog](https://www.mindstudio.ai/blog/karpathy-llm-knowledge-base-architecture-compiler-analogy) — LOW-MEDIUM confidence (secondary-source blog summarizing an informal framing, not a primary technical source; used only for the analogy/feature-emphasis framing, not as evidence of a "system")
- `.planning/PROJECT.md` — HIGH confidence (primary source for KIR's own scope and requirements)

---
*Feature research for: knowledge-extraction / semantic-compiler / ontology-construction-from-documents systems*
*Researched: 2026-06-29*
