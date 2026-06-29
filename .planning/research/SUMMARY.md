# Project Research Summary

**Project:** KIR (Knowledge Intermediate Representation)
**Domain:** Deterministic, LLM-assisted semantic compiler (Markdown → canonical Knowledge IR), Python, hexagonal architecture, tactical DDD
**Researched:** 2026-06-29
**Confidence:** HIGH

## Executive Summary

KIR is best understood as a compiler in the LLVM sense — a stable, typed Intermediate Representation produced by a pipeline of independently testable passes — applied to the problem of turning a corpus of Markdown documents into a canonical, provenance-tracked knowledge model. The closest prior art (Microsoft GraphRAG, Cognee, the academic Extract-Define-Canonicalize framework, and the classical ontology-learning "layer cake") all converge on the same decomposition KIR already uses: extract -> canonicalize/merge -> relate -> classify -> detect conflicts. Where KIR differs sharply from every comparable system surveyed is in refusing to bundle rendering, storage/query, or automatic conflict resolution into the product — and in treating conflicts as permanent, recorded, first-class artifacts rather than something to vote/merge away. This is a genuine, defensible, citable differentiator, not a missing feature, and it should be protected from scope creep throughout the roadmap.

The recommended stack (Python 3.13+, Pydantic v2, PydanticAI, Typer, ruamel.yaml, uv, Ruff, pytest) is confirmed as correct for this exact problem shape, with one timing caveat: PydanticAI shipped v2.0.0 six days before this research, so v1-era API names (`result_type`, `.data`) must not be copy-pasted from older tutorials. The hexagonal architecture (domain ring -> application/passes ring -> adapters ring, with ports owned by the domain) maps cleanly onto the two-compiler structure already named in PROJECT.md: a per-document Document Compiler and a whole-corpus Knowledge Compiler, each with its own pass registry.

The dominant risk across all four research tracks is the same risk wearing different clothes: **silent loss of information disguised as success.** Determinism is at risk because `temperature=0` does not make LLM calls reproducible (provider batching/floating-point non-associativity defeats this); alias resolution is at risk of silent over-merging (collapsing distinct concepts) and under-merging (fragmenting true aliases) — a failure mode directly documented in a filed GraphRAG production bug; merge order-dependence can make the same corpus compile to different Knowledge IRs depending on filesystem traversal order; incremental rebuild can leave stale merge state across documents that share a concept; and permissive Pydantic validation can quietly violate the project's core "never silently resolve" principle from inside the LLM adapter, below where conflict detection ever sees the problem. All five are addressable architecturally (response caching keyed on checksum+prompt+schema+model, strict validation with explicit failure artifacts, content-derived sort keys, a concept-level reverse index for invalidation) but only if designed in from the foundational phase, not retrofitted after passes are built.

## Key Findings

### Recommended Stack

The user's pre-selected stack is confirmed correct with no replacements needed: Python 3.13+, Pydantic v2 (2.13.x), PydanticAI (v2.0.0, released 2026-06-23 — pin deliberately, read the upgrade guide), Typer (0.26.x), Ruff, pytest, and uv. The one notable addition beyond the user's list is **ruamel.yaml** over PyYAML as the YAML engine — PyYAML reorders dict keys and drops comments, which directly works against the git-diffable, human-readable artifact requirement. **networkx** is recommended for cycle detection in the Conflict pass (relation graphs at hundreds-of-documents scale don't need anything heavier). **python-slugify** is recommended for deriving stable concept IDs. A static type checker (pyright or mypy) is flagged as a gap in the user's stated stack worth raising during roadmap planning, given how much the hexagonal architecture benefits from compile-time port/adapter mismatch detection.

**Core technologies:**
- Pydantic v2 — canonical IR schema, validation, (de)serialization backbone for Concept/Relation/Taxonomy/Document/Conflict
- PydanticAI v2 — provider-agnostic LLM-backed passes returning validated Pydantic models directly, with `TestModel`/`FunctionModel` + VCR cassettes for golden-fixture testing without live API calls
- Typer — CLI framework, type-hint-driven, pairs naturally with Pydantic for argument validation
- ruamel.yaml — round-trip-faithful YAML serialization for git-diffable, human-reviewable artifacts
- uv — dependency management, `src/` layout, reproducible checksum-pinned resolution (a nice parallel to KIR's own checksum-based incremental-compile philosophy)

### Expected Features

**Must have (table stakes):** entity/concept extraction; relation extraction as explicit typed edges; alias/synonym canonicalization (the hardest pass in any such pipeline); per-element source/provenance tracking; stable deterministic concept IDs; incremental rebuild via checksum diffing; versioned/reproducible output; conflict *detection* (six categories: duplicate concepts, conflicting definitions, taxonomy conflicts, alias conflicts, orphans, cycles); modular independently-testable pass pipeline; taxonomy/category structure over concepts.

**Should have (differentiators):** conflicts recorded as permanent first-class artifacts, never auto-resolved (KIR's strongest, most citable differentiator vs. every comparable system, all of which default to voting/heuristic resolution); the IR itself as the literal product boundary, with no downstream rendering/serving; closed, explicit relation vocabulary (trades expressiveness for mergeability/determinism); per-element (not per-chunk) provenance; golden-fixture-tested LLM passes; taxonomy decoupled from source folder/file hierarchy.

**Defer (v2+/reject):** `doctor`/`stats` diagnostics (v1.x); conflict-resolution workflow tooling (v1.x, still never silent); additional source parsers beyond Markdown (v1.x+, trigger on a concrete second corpus); schema migration tooling (defer until a second schema version exists); rendering/wiki export, graph/vector DB storage, automatic conflict resolution, and query/retrieval APIs are **permanent anti-features**, not deferrals — these are the single most natural "obvious next feature" requests and must be actively guarded against, since they are the literal product of nearly every comparable system surveyed (GraphRAG, Cognee).

### Architecture Approach

Hexagonal architecture (ports/adapters) crossed with a linear compiler-pass pipeline, organized as three concentric rings where dependency arrows point inward only: the domain ring (pure Pydantic models + Protocol-based ports, zero SDK/filesystem imports) is innermost; the application/passes ring (PassRegistry, DocumentCompiler, KnowledgeCompiler use-cases) depends only on domain types and port interfaces; the adapters ring (PydanticAI LLM adapter, YAML repository, Markdown parser, Typer CLI) is outermost and is the only place external SDK imports may appear. Passes self-register via decorator (directly analogous to LLVM's PassBuilder registration), are pure functions of `(IR_in, PassContext[ports]) -> IR_out`, and never call each other directly or mutate IR in place.

**Major components:**
1. Domain models (Concept, Relation, Taxonomy, Document, Conflict, Provenance as Pydantic `BaseModel`s) — pure, zero I/O, owns the port Protocols
2. Pass registry + two distinct pipelines (Document Compiler: per-file, parallelizable; Knowledge Compiler: whole-corpus, sequential merge) — the project's core extension mechanism
3. LLM Adapter (PydanticAI `Agent`, `output_type=DomainModel`) — implements `LLMPort`, isolates all provider SDK imports
4. Repository Adapter (one YAML file per artifact under `documents/`, `concepts/`, `relations/`, `taxonomy/`, `aliases/`, `metadata/`) — implements `RepositoryPort`
5. CLI (Typer) — thin composition root wiring concrete adapters into use-case services; the only layer that knows about every adapter simultaneously

### Critical Pitfalls

1. **Determinism promised at the wrong layer** — `temperature=0`/fixed seed does not make LLM calls reproducible across runs (provider batching + floating-point non-associativity). Avoid by redefining "deterministic" as a property of (inputs + cached/recorded LLM responses), not of the LLM call itself: cache every LLM-backed pass output keyed on (document checksum, prompt version, schema version, *dated* model identifier — never a rolling alias).
2. **Silent over/under-merging in alias resolution** — directly documented in a filed GraphRAG bug (#1718): name-only dedup keys silently drop entities with the same title but different type. Avoid by never keying merge logic on name alone (always carry type + provenance), separating normalize/judge/merge into distinct passes, and recording every merge decision below a confidence threshold as a conflict, not a silent accept.
3. **Merge order-dependence** — pairwise merge is non-commutative; filesystem traversal order can silently change which canonical name wins. Avoid by sorting documents by a content-derived key (checksum/ID, never mtime) before any merge pass, and adding a shuffled-order regression test that asserts byte-identical Knowledge IR.
4. **Incremental compilation misses cross-document invalidation** — checksum-only invalidation answers "did this document change?" but not "which other documents' merge results are now stale because they shared a concept?" Avoid with a reverse index (concept ID <-> contributing document IDs) and an explicit incremental-vs-full-recompile regression test.
5. **Structured-output validation silently coerced** — permissive Pydantic config (`extra="ignore"`, default-value fallbacks) inside the LLM adapter is the easiest way to violate "never silently resolve" without anyone noticing, since it happens below where conflict detection ever sees the data. Avoid with strict validation (`extra="forbid"`), bounded retries, and an explicit "extraction failed" artifact type on exhaustion.

## Implications for Roadmap

Based on combined research, the architecture's suggested build order (domain -> ports -> registry -> deterministic passes -> fake LLM adapter -> LLM-backed passes -> real adapters -> use-cases -> incremental logic -> CLI -> 700-doc validation) and the pitfalls' "foundational, must be settled before X" warnings line up tightly. Determinism-enforcing infrastructure (response caching, strict validation, content-derived sort order) must be built *into* the foundation, not layered on after passes exist — retrofitting any of Pitfalls 1, 3, or 6 after artifacts are already in git is expensive (canonical names get baked into provenance records).

### Phase 1: Domain Core + Ports + Pass Registry
**Rationale:** Architecture research is explicit that domain models and the pass-registry mechanism must exist and be proven in isolation (with fakes) before any pass can be written — this is the "structural guarantee that must be designed in, not retrofitted" foundation.
**Delivers:** Pydantic models for Document, Concept, Relation, Taxonomy, Conflict, Provenance with invariants (slug-derived IDs); `LLMPort`/`RepositoryPort`/`MarkdownParserPort` Protocols; `PassRegistry` with topological dependency ordering, unit-tested with trivial fake passes.
**Addresses:** Stable deterministic concept IDs, provenance modeling, "adding a new pass doesn't touch existing passes" (FEATURES.md table stakes).
**Avoids:** Anti-Pattern 1 (leaky hexagon — adapter imports in domain) and Anti-Pattern 2 (passes reaching around the registry) from ARCHITECTURE.md, by construction.

### Phase 2: Document Compiler (Deterministic Passes + Fake LLM Adapter)
**Rationale:** Deterministic passes (Parse, Section, Metadata) need no LLM and are fastest to get right; a fake/mock LLM adapter must exist before any real LLM-backed pass is built, per the suggested build order, so cost/determinism risk is deferred safely.
**Delivers:** Per-document Document IR pipeline (Markdown -> parsed/sectioned/metadata-tagged Document IR), `FakeLLMAdapter`/`TestModel` harness, YAML repository adapter for `documents/`.
**Uses:** markdown-it-py (parsing), ruamel.yaml (repository), pytest fixtures (no LLM calls yet).
**Implements:** Document Compiler use-case service, per-document checksum computation (groundwork for incremental rebuild).

### Phase 3: LLM Adapter Foundation — Determinism & Validation Contract
**Rationale:** PITFALLS.md is explicit that the response-caching architecture and strict-validation contract are foundational decisions that must be settled *before* ExtractConcepts is built, not bolted on after several passes already have permissive error handling baked in.
**Delivers:** Real PydanticAI LLM adapter with content-addressed response cache (keyed on document checksum + prompt version + schema version + dated model ID), strict Pydantic validation (`extra="forbid"`), bounded retry policy with explicit "extraction failed" artifact on exhaustion, versioned prompt templates.
**Avoids:** Pitfall 1 (determinism at the wrong layer) and Pitfall 6 (silent coercion) — both flagged as foundational, architecture-level decisions, not bolt-ons.

### Phase 4: ExtractConcepts (First LLM-Backed Pass, Document-Level)
**Rationale:** Per PROJECT.md's pass ordering, ExtractConcepts runs per-document and is the first LLM-backed pass; building it against the Phase 3 contract validates the caching/validation architecture end-to-end before the harder cross-document passes.
**Delivers:** `ExtractConceptsPass` integrated into the Document Compiler pipeline, golden-fixture tests (recorded/mocked responses) including deliberately malformed-response fixtures to exercise the retry-and-fail path.
**Addresses:** Entity/concept extraction (table stakes).
**Avoids:** Pitfall 5 cost blind spot — validate real per-pass token cost on a small (20-50 doc) sample here, before scaling.

### Phase 5: Knowledge Compiler — Alias Resolution & Concept Merge
**Rationale:** FEATURES.md and PITFALLS.md both single out this as the highest-risk pass in the whole pipeline (hardest, most failure-prone, with a directly-documented production bug in the closest comparable system). It deserves dedicated adversarial test fixtures before running against the full corpus.
**Delivers:** `ResolveAliasesPass` + `MergeConceptsPass` with normalize/judge/merge kept as separate passes, content-derived sort order for merge-order determinism, reverse index (concept <-> contributing documents) for future incremental invalidation, adversarial fixtures replicating the GraphRAG (name, type) collision shape.
**Avoids:** Pitfall 2 (silent over/under-merging) and Pitfall 3 (merge order-dependence) — both explicitly mapped to this phase in PITFALLS.md.

### Phase 6: Relations, Taxonomy, and Conflict Detection
**Rationale:** Architecture and feature dependency analysis both establish that BuildRelations/BuildTaxonomy require merged canonical concepts, and Conflict detection must run last because conflicts are properties of the merged graph, not any single document.
**Delivers:** `BuildRelationsPass` (closed vocabulary), `BuildTaxonomyPass` (semantically independent of source folder structure — with a regression check against the real Slab folder hierarchy to catch path-leakage shortcuts), `ConflictPass` covering all six conflict categories with adversarial fixtures per category.
**Addresses:** Typed relation extraction, taxonomy classification, conflict detection — all P1 features.
**Avoids:** Anti-Pattern 3 (one mega-pipeline) by keeping this strictly whole-corpus, post-merge.

### Phase 7: Incremental Compilation
**Rationale:** PITFALLS.md and ARCHITECTURE.md agree this should be layered on only after the full (non-incremental) pipeline is correct — debugging incremental logic and pass logic simultaneously is unnecessarily hard.
**Delivers:** Per-document checksum diffing gating which Document IR artifacts rebuild; concept-level invalidation expansion (not just "1 changed document -> re-merge only that document") using the Phase 5 reverse index; incremental-vs-full-recompile regression test.
**Avoids:** Pitfall 4 (stale cross-document invalidation) — explicitly flagged as needing a dedicated synthetic corpus with deliberately overlapping concepts before scaling to 700 docs.

### Phase 8: CLI, End-to-End Wiring, and 700-Document Validation
**Rationale:** The CLI composition root is deliberately last (architecture build order step 12) since it should be pure wiring with no business logic; the 700-doc acceptance bar can only be meaningfully attempted once every component is individually tested.
**Delivers:** `kir compile` end-to-end command; full run against the real 700-document Slab export with conflicts/provenance verified; determinism conformance test (shuffle document order, diff byte-for-byte); cost/rate-limit validation against the full corpus (batch API if economical).
**Addresses:** PROJECT.md's explicit v1 acceptance bar.

### Phase Ordering Rationale

- Foundation-first ordering (domain -> ports -> registry -> deterministic passes -> fake adapter -> real adapter) is directly prescribed by ARCHITECTURE.md's "Suggested Build Order" and exists specifically so the two hardest structural guarantees (zero domain knowledge of LLM/filesystem; new passes don't touch existing ones) are designed in from day one, not retrofitted.
- Determinism-and-validation infrastructure (Phase 3) is placed *before* the first real LLM-backed pass (Phase 4) because PITFALLS.md treats response caching and strict validation as architectural decisions that are "expensive to retrofit once several passes already have permissive error handling baked in."
- Alias resolution/merge (Phase 5) gets its own dedicated phase, separate from extraction (Phase 4) and from relations/taxonomy/conflict (Phase 6), because FEATURES.md and PITFALLS.md both independently flag it as the single highest-risk, most failure-prone pass in the entire pipeline.
- Incremental compilation (Phase 7) is deliberately sequenced after the full pipeline works correctly, per both ARCHITECTURE.md (debugging two unknowns at once is harder) and PITFALLS.md (the cross-document invalidation bug is invisible at 1-document scale and needs a working merge graph to test against).
- This ordering also naturally enforces the FEATURES.md anti-feature boundary: there is no phase for rendering, query/retrieval, or graph DB storage — the roadmap stops at the IR, by design.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (LLM Adapter Foundation):** PydanticAI v2.0.0 is six days old at time of research; confirm exact API surface (Tool Output vs Native Output mode choice, `ModelRetry`/`output_retries` configuration, provider-extras packaging) against current docs before implementation, not against pre-mid-2026 tutorials.
- **Phase 5 (Alias Resolution & Merge):** No single source covers KIR's exact combination of closed-vocabulary relations + LLM-judged alias merge + strict determinism; the normalize/judge/merge pass split and confidence-threshold-as-conflict policy will likely need refinement against real extraction behavior on a representative document sample.
- **Phase 7 (Incremental Compilation):** The cross-document invalidation data model (reverse index design, what counts as "affected") is synthesized by analogy from general build-system literature (Docker, TypeScript, Lean4), not from a source that solves this exact content-addressed-merge-graph problem — expect to iterate on the invalidation scoping logic.

Phases with standard, well-documented patterns (skip research-phase):
- **Phase 1 (Domain Core + Ports + Registry):** Pydantic v2 modeling, Protocol-based ports, and decorator-based registry are all corroborated by official docs and canonical references (Cosmic Python, LLVM pass manager docs).
- **Phase 2 (Document Compiler):** Markdown parsing + deterministic passes + YAML repository adapter are standard, low-risk implementations with mature libraries.
- **Phase 8 (CLI):** Typer composition-root wiring is a well-established, low-risk pattern.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core libraries verified against official docs/PyPI/changelogs same week as research; only soft spot is PydanticAI v2.0.0's six-day-old API surface |
| Features | MEDIUM-HIGH | Table stakes and anti-features well-corroborated across multiple independent comparable systems (GraphRAG, Cognee, EDC, academic surveys); specific complexity/priority estimates are KIR-context judgment calls, not measured |
| Architecture | HIGH (structure) / MEDIUM (specifics) | Component boundaries, hexagonal layering, build order, registry pattern all corroborated by official docs (LLVM, Cosmic Python, PydanticAI). Exact PassContext shape and incremental-dependency-tracking mechanics are synthesized from analogous systems — no single source covers this exact combination |
| Pitfalls | MEDIUM-HIGH | Determinism and entity-resolution findings verified against multiple independent sources including a real GraphRAG production post-mortem (#1718); cross-document invalidation pattern is software-engineering-general (Docker, TypeScript, Lean4) applied by extrapolation to KIR's specific content-addressed merge graph, not directly sourced for this exact case |

**Overall confidence:** HIGH

### Gaps to Address

- **PydanticAI v2 API surface stability:** v2.0.0 is six days old; re-check the exact `output_type`/`ModelRetry`/`output_retries` API against current docs immediately before implementing the LLM adapter (Phase 3), not from memory of this research.
- **Closed relation vocabulary edge cases:** Real corpus content will produce relations that don't cleanly fit the closed vocabulary (related_to, depends_on, part_of, etc.) — an explicit policy (conflict record vs. fallback vs. rejection) needs to be decided during Phase 6 planning, not left to implicit per-run LLM judgment (which would break determinism).
- **LLM cost validation:** No real per-pass token cost data exists yet; must be measured against a 20-50 document representative sample (Phase 4) and again at 50-100 documents (Phase 8 pre-validation) before assuming the full 700-doc compile is economically/operationally viable.
- **Incremental invalidation data model specifics:** The reverse-index design (concept ID <-> contributing documents) is a reasonable extrapolation, not a directly-sourced pattern — expect to iterate during Phase 7 implementation against a small synthetic corpus with deliberately overlapping concepts before trusting it at 700-doc scale.
- **Type checker choice:** pyright vs mypy is flagged as a genuine judgment call in STACK.md, not resolved by research — decide during Phase 1 tooling setup based on team/editor preference.

## Sources

### Primary (HIGH confidence)
- https://pydantic.dev/docs/ai/project/changelog/ — PydanticAI v1->v2 changelog and breaking changes
- https://ai.pydantic.dev/testing/ and https://ai.pydantic.dev/api/models/test/ — TestModel/FunctionModel golden-fixture testing pattern
- https://pypi.org/project/pydantic-ai/, /pydantic/, /typer/, /ruamel.yaml/ — version/compatibility verification
- https://llvm.org/docs/NewPassManager.html and https://llvm.org/docs/WritingAnLLVMNewPMPass.html — pass pipeline registration pattern
- https://www.cosmicpython.com/book/chapter_06_uow and https://github.com/cosmicpython/book — Repository/Unit of Work pattern reference
- https://github.com/microsoft/graphrag/issues/1718 — direct production post-mortem of the (name, type) silent-merge bug
- https://arxiv.org/html/2404.03868v1 — Extract-Define-Canonicalize (EDC) framework, maps directly to KIR's pass structure

### Secondary (MEDIUM confidence)
- https://github.com/microsoft/graphrag, https://microsoft.github.io/graphrag/index/overview/ — GraphRAG architecture and incremental indexing history
- https://github.com/topoteretes/cognee — Cognee as a counterexample (bundles storage/retrieval KIR rejects)
- https://www.zansara.dev/posts/2026-03-24-temp-0-llm/ and https://unstract.com/blog/understanding-why-deterministic-output-from-llms-is-nearly-impossible/ — LLM non-determinism mechanics
- https://docs.docker.com/build/cache/invalidation/, GitHub microsoft/TypeScript#54501, leanprover/lean4#13449 — general incremental-build invalidation pattern, applied by analogy
- https://www.morphllm.com/llm-cost-optimization, https://www.typedef.ai/resources/handle-token-limits-rate-limits-large-scale-llm-inference — LLM cost/rate-limit economics

### Tertiary (LOW confidence)
- https://www.mindstudio.ai/blog/karpathy-llm-knowledge-base-architecture-compiler-analogy — secondary-source blog summarizing an informal framing, used only for analogy framing
- https://pnt.jacbex.com/pydanticai-2026-04-08.html — single source for the 20-30% validation-failure-rate figure, treat as illustrative only

---
*Research completed: 2026-06-29*
*Ready for roadmap: yes*
