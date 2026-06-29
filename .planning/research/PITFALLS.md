# Pitfalls Research

**Domain:** LLM-assisted deterministic semantic compiler — knowledge extraction, entity/alias resolution, ontology/taxonomy merging across ~700 Markdown documents, incremental compilation
**Researched:** 2026-06-29
**Confidence:** MEDIUM-HIGH (determinism and entity-resolution findings verified against multiple independent sources including a real production post-mortem; cost/scale figures verified against current provider pricing models; some incremental-compilation findings are software-engineering-general rather than KIR-specific and are flagged accordingly)

## Critical Pitfalls

### Pitfall 1: "Determinism" Is Promised at the Wrong Layer (temperature=0 / fixed seed does not mean reproducible)

**What goes wrong:**
KIR's Core Value commits to "given identical raw sources, compiler version, prompt version, and schema version, KIR must deterministically compile." Teams building on this assumption typically believe `temperature=0` (or a fixed seed) makes an LLM call deterministic, then ship a compiler whose "deterministic" guarantee silently breaks the first time output differs between two runs with byte-identical inputs.

**Why it happens:**
Floating-point arithmetic is not associative, and inference servers batch concurrent requests together; the precise numeric path a token's logits take depends on what else is being processed in the same batch, which varies between runs. Even with `temperature=0` and a fixed seed, when two candidate tokens have close logits, tiny floating-point rounding differences can flip which one wins, and that single divergence cascades through every subsequent token (autoregressive generation). Provider behavior differs and changes over time: OpenAI's `seed` + `system_fingerprint` is "same most of the time" but the fingerprint itself changes whenever OpenAI updates the model/backend without notice; Anthropic does not expose a stable seed parameter at all, so Claude reproducibility is `temperature=0` + identical input and is explicitly best-effort, not guaranteed. (MEDIUM-HIGH confidence — corroborated by Thinking Machines' public writeup on LLM inference nondeterminism and a dedicated technical post on temp=0 myths; this is widely reported but the underlying provider internals are inherently a moving target.)

**How to avoid:**
Redefine what "deterministic" means in the Knowledge IR schema *before* writing the Knowledge Compiler: KIR should guarantee reproducibility of the *pipeline given a recorded LLM response*, not reproducibility of the *LLM call itself*. Concretely: (1) every LLM-backed pass output gets cached/recorded keyed by (document checksum, prompt version, schema version, model identifier) — recompilation with unchanged inputs replays the cached response rather than re-calling the LLM; (2) the "prompt version" and "model identifier" recorded in every artifact (already in the Active requirements) must include the exact dated model snapshot, not a rolling alias (e.g. `claude-sonnet-4-6-20260115`, not `claude-sonnet-4-6-latest`) since providers silently swap weights/backends under floating aliases; (3) deterministic passes (Parse, Section, Metadata, BuildTaxonomy structure, Conflict detection logic itself) must be proven byte-identical via unit tests with zero reliance on LLM ordering; (4) document in the Knowledge IR schema that "determinism" is a property of (inputs + cached LLM responses), and that a fresh, uncached LLM call against the same document is permitted to extract a *semantically equivalent but textually different* result — this is a conflict-worthy event, not silently accepted as "the same."

**Warning signs:**
- Re-running `kir compile` twice on an unchanged corpus produces different concept IDs, definitions, or YAML diffs — and nobody has a caching layer to explain why.
- Tests assert exact LLM output strings rather than asserting against recorded/golden fixtures.
- The "prompt version" recorded in metadata is a generic label ("v1") rather than a hash of the actual prompt template + model identifier.
- No mechanism exists to detect when a provider deprecates/changes a model version out from under a pinned alias.

**Phase to address:**
Foundational — must be settled in the pass-pipeline / LLM-adapter design phase (before ExtractConcepts/ResolveAliases passes are built), because the recording/caching boundary is an architectural decision, not a bolt-on. Should also shape the "LLM passes tested via recorded/mocked responses" requirement already in PROJECT.md.

---

### Pitfall 2: Silent Over-Merging and Under-Merging in Cross-Document Alias Resolution

**What goes wrong:**
Two failure modes, both silent (i.e., they don't crash, they corrupt): (a) **over-merging** — two genuinely distinct concepts get collapsed into one canonical concept because their names/descriptions look similar (e.g., "Cache" the CS data structure vs. "Cache" the company's internal caching service), permanently losing the distinction and poisoning every downstream relation/taxonomy edge that touches either; (b) **under-merging** — true aliases ("API Gateway", "Gateway", "the gateway service") are extracted as separate concepts across different documents because surface form varies, fragmenting what should be one canonical concept across N near-duplicate concept IDs.

**Why it happens:**
This is a documented, recurring real-world failure in the closest production analog to KIR's Knowledge Compiler: Microsoft's GraphRAG has a filed bug (GitHub #1718) where `finalize_entities` groups entities by (title, type) to merge descriptions, but the subsequent `drop_duplicates` step keys only on title — so when the same title legitimately appears with two different types, the dedup step keeps only the *first* row and silently discards the other entity's accumulated descriptions, with no error, warning, or log entry. More generally, simple string-matching dedup (what most "GraphRAG-style" pipelines default to) cannot catch synonyms, abbreviations, casing differences, or multilingual variants ("IT" vs. "Information Technology", "2024" vs. "Year 2024") — these get isolated as separate, never-merged entities. The inverse error (over-merging) happens when alias resolution is run as raw LLM judgment per pair without a normalization step first: extraction-time surface variation, ambiguous scope, and inconsistent typing get fed directly into the merge decision, and LLM judges can confidently merge two distinct real-world entities that happen to share a name. (HIGH confidence on the GraphRAG bug — verified directly from the GitHub issue; MEDIUM-HIGH on the general over/under-merging pattern — corroborated by multiple independent sources on semantic entity resolution.)

**How to avoid:**
1. Never key dedup/merge logic on name-only matching, even as an intermediate step — always carry category/type and source-document provenance through the entire merge pipeline so a (name, type) collision is distinguishable from a true alias.
2. Separate "normalize" from "judge" from "merge" as distinct, independently testable passes (this maps naturally onto KIR's existing ResolveAliases → MergeConcepts pass split) — do not let one LLM call both decide *and* execute a merge in the same step.
3. Every merge decision (alias→canonical) must be recorded as a provenance-bearing artifact showing which source documents and which surface forms fed into the canonical concept — this is required for the explicit "alias conflicts" detection already in scope, and it is also the only way to debug an over-merge after the fact, since the failure is otherwise invisible.
4. Treat every alias-merge decision below a confidence threshold (or any case where descriptions/categories disagree) as a recorded **conflict**, not a silent accept — this aligns directly with KIR's "never silently resolve" design principle, but it must be enforced specifically at the merge-decision granularity, not just at the document level.
5. Add an explicit regression test fixture replicating the GraphRAG (name, type) collision shape — two same-named, different-category concepts across two documents — and assert KIR keeps both as distinct concepts with a recorded near-duplicate-name conflict, never silently drops one.

**Warning signs:**
- Concept count after MergeConcepts drops by an amount disproportionate to actual duplication in the corpus (silent over-merge).
- Multiple concepts in the output with near-identical canonical names/slugs that were never flagged as a possible alias conflict (silent under-merge / missed alias).
- Aliases or descriptions "disappear" between Document IR and Knowledge IR with no corresponding conflict record.
- Re-ordering which documents are compiled first changes the final canonical name chosen for a merged concept (see Pitfall 3).

**Phase to address:**
ResolveAliases / MergeConcepts pass design phase — this is the highest-risk pass in the whole pipeline and deserves its own dedicated test corpus of adversarial near-duplicate cases before it's run against the full 700-document corpus.

---

### Pitfall 3: Merge Order-Dependence (Same Corpus, Different Document Processing Order, Different Knowledge IR)

**What goes wrong:**
Pairwise/incremental merge algorithms (process doc 1, merge into running knowledge base, process doc 2, merge, ...) are not commutative in general. Which document happens to be processed first can determine which surface form becomes the "canonical name," which definition wins when two documents define the same concept differently, and even which entities end up clustered together at all when similarity is near a threshold. This directly undermines KIR's core determinism guarantee in a way that's easy to miss because *within a single run* the output looks stable — the bug only appears when document discovery order changes (e.g., directory listing order differs between OSes, or a new document is inserted into the corpus and shifts processing order for unrelated documents).

**Why it happens:**
This is a well-known property of pairwise match-and-merge and hierarchical clustering algorithms in entity resolution literature: merge functions are non-commutative by default, and when there are "tied" merge candidates, whichever one is encountered first wins, with no canonical way to break the tie deterministically unless the algorithm is explicitly designed for it. (MEDIUM-HIGH confidence — well-established in entity-resolution and clustering literature, not specific to LLM pipelines but directly applicable since KIR's MergeConcepts pass is exactly this kind of algorithm.)

**How to avoid:**
- Sort documents by a stable, content-derived key (e.g., document ID or checksum, never filesystem mtime/directory order) before any merge pass runs, so processing order is itself a deterministic function of content, not of OS/filesystem state.
- Make canonical-name selection a pure function of the full candidate set (e.g., "shortest name," "name from earliest-dated source," or "most frequent surface form across the corpus") rather than "whichever I saw first" — this makes the choice independent of arrival order.
- When two documents define a concept differently, this is a **conflict** to record (per KIR's design), not a "last writer wins" or "first writer wins" — but the *recording* of the conflict (which definition is marked primary vs. alternate, if any default is needed for non-interactive use) must itself be order-independent.
- Add a determinism regression test: compile the same corpus with documents shuffled into two different processing orders and diff the resulting Knowledge IR — they must be byte-identical (modulo recorded-conflict ordering, which should also be sorted deterministically, e.g., by concept ID then conflict type).

**Warning signs:**
- Two `kir compile` runs on the same corpus from two different machines/checkouts (different filesystem traversal order) produce different canonical names for the same concept.
- Adding one new unrelated document to the corpus changes the canonical name or definition selected for an existing, untouched concept.
- MergeConcepts pass iterates over a Python `dict`/`set` of documents without an explicit, content-derived sort key.

**Phase to address:**
MergeConcepts / BuildTaxonomy pass design, plus a dedicated "determinism conformance test" added to the testing strategy phase — this is cheap to prevent up front (sort by checksum) and expensive to retrofit once canonical names are already embedded in downstream artifacts and provenance records.

---

### Pitfall 4: Incremental Compilation Misses Cross-Document Invalidation (Stale Knowledge IR After a "Local" Edit)

**What goes wrong:**
KIR's incremental compilation design (per-document checksum diffing → only rebuild affected Document IR → re-merge only "the affected Knowledge IR") is the standard approach for this scale, but the subtle and common bug is under-scoping "affected." If document A and document B both reference the same concept ("Kubernetes"), and document A is edited in a way that changes that concept's definition or aliases, the Knowledge Compiler must recompute merge state for *all* documents that share that concept — not just re-run the pass on A. If invalidation is scoped only to "Document IR artifacts whose checksum changed" rather than "Knowledge IR concepts whose contributing documents changed," the system will silently leave stale concept merges, stale taxonomy placement, and stale relations in Knowledge IR after what looks like a successful incremental recompile.

**Why it happens:**
This is the general "incremental build invalidation" problem (well documented across build systems — Docker layer caching, TypeScript's multi-year-old incremental-build staleness bug, Lean 4's incremental cache issue) applied to a *content-addressed merge graph* rather than a *dependency DAG of files*. The KIR-specific twist is that the "dependency" isn't explicit (no document declares "I depend on concept X") — it's discovered by the LLM during ExtractConcepts/ResolveAliases, so the invalidation graph is itself a build artifact, not known in advance. Checksum-only invalidation correctly answers "did this document's raw content change?" but does not answer "which other already-compiled documents' merge results are now stale because they shared a concept with this one?" (MEDIUM confidence — the general pattern is HIGH confidence and well-documented in mature build tools; the specific cross-document concept-sharing manifestation in an LLM-extracted merge graph is a reasonable, but not directly-sourced, extrapolation specific to KIR's architecture.)

**How to avoid:**
- Persist a reverse index from concept ID → contributing document IDs (and from document ID → concept IDs it touches) as part of the Knowledge IR metadata, not just a flat document checksum table.
- On every incremental compile, after determining which Document IR artifacts need rebuilding from checksum diff, expand the invalidation set to every concept those documents touch (old *and* new contributing-document sets, since a document edit can remove a concept reference too), then re-run MergeConcepts/BuildRelations/BuildTaxonomy/Conflict only for that expanded concept set — never assume "1 document changed → 1 document's worth of merge work."
- Treat "a document was deleted" and "a document's extracted concepts changed" as first-class invalidation triggers, not just "a document's content checksum changed" — a deleted document still requires recomputing merge state for every concept it used to contribute to.
- Write an incremental-compile regression test: compile two documents sharing a concept, edit one document's definition of that concept, recompile incrementally, and assert the *other*, unedited document's view of the shared concept (in Knowledge IR) reflects the merge with the new definition — not the stale pre-edit merge.

**Warning signs:**
- After an incremental recompile, a full from-scratch recompile of the entire corpus produces a different Knowledge IR than the incremental one did (the canonical "ground truth" check for any incremental build system).
- The recompile log shows N Document IR artifacts rebuilt but the Knowledge Compiler step processes a number of concepts suspiciously close to N (i.e., it never widens the blast radius beyond directly-changed documents).
- Conflicts that should appear after an edit (e.g., a new definition disagreeing with an unedited document's definition of the same concept) don't show up until a full recompile is forced.

**Phase to address:**
Incremental compilation phase — specifically when designing the checksum/cache-invalidation data model. This should be designed and tested *before* scaling to the full 700-document corpus, using a small synthetic corpus with deliberately overlapping concepts, since the bug is invisible at 1-document scale and only manifests with cross-document concept sharing.

---

### Pitfall 5: LLM Cost and Rate Limits Are Underestimated by Treating Per-Document Cost as the Whole Bill

**What goes wrong:**
Teams budget LLM cost for a knowledge-extraction pipeline by estimating "tokens per document x cost per token x number of documents" for a single pass, then are surprised when the real bill is 4-6x higher because KIR's pipeline runs *multiple* LLM-backed passes per document (ExtractConcepts, ResolveAliases, definition generation, taxonomy classification, relation extraction are all called out as separate LLM-backed passes in PROJECT.md) and because re-running the full corpus during development/debugging (prompt iteration, schema changes, bug fixes) multiplies the per-document cost by the number of development iterations, not just the number of production compiles.

**Why it happens:**
Each LLM-backed pass is a separate API call with its own prompt overhead (system prompt, schema description, few-shot examples if any) — a 5-pass pipeline over 700 documents is 3,500 LLM calls minimum per full compile, and during active development of prompts/schemas this number gets multiplied by every iteration cycle, with no batch/cache discount unless deliberately engineered in. Most "LLM rate limit incidents" are self-inflicted by oversized prompts and bursty traffic rather than genuine API limits, and request-count limits alone don't protect against a single oversized document blowing the per-call cost. (MEDIUM-HIGH confidence — cost-multiplier math is straightforward arithmetic from the project's own documented pass list; the cost-optimization findings are corroborated by multiple independent, recent sources on LLM API economics.)

**How to avoid:**
- Build the LLM-response cache (Pitfall 1) as a cost-control mechanism, not just a determinism mechanism: once a document's checksum + prompt version + schema version combination has been compiled once, every subsequent dev/CI run replays the cached response for free. This is the single highest-leverage cost control for a project that will be recompiled constantly during development.
- For the full 700-document corpus, prefer the provider's batch API (typically ~50% discount, stacks with prompt caching for shared system-prompt/schema prefixes) for non-interactive full-corpus compiles, since `kir compile` is explicitly a batch/offline operation, not a live chat — there's no latency requirement forcing synchronous calls.
- Budget per-pass, not per-document: estimate cost as (number of LLM-backed passes) x (documents needing that pass) x (tokens per call), and separately track development-time cost (prompt iteration against a *small* fixed sample, not the full 700-doc corpus) versus production full-compile cost.
- Add explicit per-call and per-run token/cost logging from day one (cost recorded alongside compiler/schema/prompt version in artifact metadata) so a runaway prompt or unexpectedly large document is visible immediately rather than discovered at the end-of-month bill.
- Rate-limit and retry logic must be designed for ~3,500+ calls per full compile from the start, with exponential backoff and the ability to resume a partially-completed compile (which is also just sound incremental-compilation design — see Pitfall 4) rather than treating "the whole corpus in one shot" as a single uninterruptible unit of work.

**Warning signs:**
- Cost estimates in planning only ever cite "cost per document" without multiplying by number of distinct LLM-backed passes.
- No caching layer exists, so every prompt tweak during development triggers a full 700-document, 5-pass re-extraction.
- A single large/malformed document (e.g., a 50-page Slab export page) causes a disproportionate cost spike or a hard rate-limit failure that aborts the entire compile run rather than being isolated and retried.

**Phase to address:**
LLM adapter / pass-pipeline design phase (caching architecture) and the incremental-compilation phase (resumability). Should be validated against a representative subset (e.g., 20-50 documents) before the full 700-document acceptance run, specifically to measure real per-pass token costs rather than estimating from training-data pricing assumptions.

---

### Pitfall 6: Structured-Output Validation Failures Get Silently Coerced or Swallowed Instead of Recorded as Conflicts

**What goes wrong:**
PydanticAI (and structured-output LLM tooling generally) validates LLM JSON output against a Pydantic schema and retries on failure, but teams commonly configure permissive fallback behavior (e.g., `extra="ignore"`, loose retry-until-it-parses loops, or default-value fallbacks) to keep the pipeline from crashing — and this silently discards information the LLM extracted, or silently substitutes a default/empty value for a field the LLM couldn't populate correctly. For a project whose entire design principle is "never silently resolve," this is the single easiest way to violate that principle without anyone noticing, because validation coercion happens *inside* the LLM adapter, below the level where conflict-detection logic ever sees the data.

**Why it happens:**
LLMs hallucinate fields, return wrong types, or emit malformed JSON at a non-trivial rate (commonly cited around 20-30% of raw responses needing at least one retry/repair pass before validating cleanly against a non-trivial schema). The natural engineering response under time pressure is to make validation permissive enough that the pipeline "just works," which trades correctness for throughput — exactly backwards for a compiler whose value proposition is correctness guarantees. (MEDIUM confidence — the specific 20-30% failure-rate figure comes from a single source and should be treated as illustrative rather than load-bearing; the general pattern of permissive-validation-as-silent-data-loss is corroborated by multiple sources and is a logical consequence of how retry/repair loops are commonly implemented.)

**How to avoid:**
- Configure all PydanticAI agent output models with strict validation (`extra="forbid"` or equivalent, no silently-ignored fields) — a schema mismatch must be a recorded failure, never a quiet drop.
- Define an explicit, bounded retry policy (e.g., retry twice with progressively more explicit schema instructions) and, on exhaustion, emit a recorded extraction-failure artifact for that document/pass — not a default/empty concept, not a skipped document. This failure artifact should be visible in the same conflict-reporting surface as semantic conflicts (duplicate concepts, taxonomy conflicts), since from the user's perspective "the compiler couldn't extract this reliably" is exactly as important as "the compiler found contradictory definitions."
- Never let a validation retry silently change the semantic content of what's recorded (e.g., truncating a list of aliases to fit a retry's stricter prompt) — log what was discarded/changed, even if only in debug-level provenance metadata.
- Golden-fixture tests (already in PROJECT.md's testing strategy) must include deliberately malformed/edge-case LLM responses (truncated JSON, extra hallucinated fields, wrong enum values) to exercise the retry-and-fail path, not just the happy path.

**Warning signs:**
- Pipeline runs report "0 errors" on a corpus where manual spot-checks reveal missing concepts/aliases/relations that should have been extracted.
- The LLM adapter layer has any `try/except` that catches a validation error and returns an empty/default model instead of propagating a recorded failure.
- No artifact type exists in the conflict/metadata schema for "extraction failed/degraded for this document+pass," forcing failures to either crash the whole compile or vanish silently.

**Phase to address:**
LLM Adapter implementation phase (the PydanticAI integration layer) — strict validation and explicit failure-as-artifact behavior should be the default from the first LLM-backed pass implemented (ExtractConcepts), since retrofitting this after several passes already have permissive error handling baked in is expensive.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip the LLM-response cache, call the API fresh every compile during early development | Simpler adapter code, less to build up front | Cost multiplies with every prompt iteration; reproducibility becomes impossible to test (Pitfall 1, 5) | Never beyond the first throwaway prototype pass — build the cache before the second LLM-backed pass is added |
| Use a rolling/"latest" model alias instead of a dated, pinned model identifier | One less config value to manage; always "the newest model" | Silent behavior drift breaks the determinism guarantee with no warning (Pitfall 1) | Never in any artifact-producing run; acceptable only for ad hoc manual exploration outside the compiler |
| Name-only string matching for alias/dedup detection as a first pass | Fast to implement, no LLM call needed for obvious exact matches | Under-merges true aliases with surface variation and over-merges same-named distinct concepts (Pitfall 2) | Acceptable only as a pre-filter to narrow LLM-judged candidate pairs, never as the final merge decision |
| Scope incremental rebuild strictly to documents whose checksum changed, ignore concept-sharing | Much simpler invalidation logic, ships faster | Silently stale Knowledge IR after cross-document edits (Pitfall 4); undermines trust in incremental compiles entirely | Never past an initial spike/prototype — must be fixed before incremental compilation is considered "done" |
| Permissive Pydantic validation (`extra="ignore"`, silent defaults) to avoid pipeline crashes during early integration | Pipeline "works" end-to-end sooner, fewer crashes during demos | Violates the core "never silently resolve" design principle; data loss is invisible (Pitfall 6) | Acceptable only behind a debug flag during interactive prompt-engineering sessions, never in `kir compile` |
| Process documents in filesystem/directory listing order for merge passes | Zero extra code | Order-dependent output breaks the determinism guarantee when document discovery order varies (Pitfall 3) | Never — sorting by a stable content-derived key costs almost nothing to add up front |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|-------------------|
| Anthropic / OpenAI APIs via PydanticAI | Assuming `temperature=0` (or a seed param) makes output reproducible across runs/days | Treat all LLM calls as non-deterministic at the system boundary; rely on response caching keyed by (input checksum, prompt version, schema version, pinned model ID) for reproducibility, not on sampling parameters |
| PydanticAI structured output | Loosening schema validation (`extra="ignore"`, broad retry-until-parses loops) to reduce pipeline failures | Strict schemas (`extra="forbid"`), bounded retries, explicit "extraction failed" artifact on exhaustion — never a silent default |
| Provider batch APIs | Treating the full 700-doc compile as 3,500+ synchronous, ad hoc calls | Route the full-corpus compile through the provider's batch API (offline, ~50% cheaper, stacks with prompt caching); reserve synchronous calls for small-sample dev iteration |
| Model identifiers / aliases | Pinning to a generic model family name without a dated snapshot | Always pin and record the exact dated model identifier in artifact metadata; alias-based pinning silently drifts when the provider updates the alias target |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| No LLM-response cache during development | Every prompt/schema tweak triggers a full corpus re-extraction; iteration loop becomes painfully slow and expensive | Build content-addressed response caching before the second LLM-backed pass is implemented | Becomes intolerable well before 700 documents — even 50-100 documents with 3+ passes makes uncached iteration too slow/costly to sustain |
| Pairwise/naive O(n^2) alias-candidate comparison across all concepts | Compile time grows quadratically as the concept count grows with corpus size | Pre-filter candidate pairs with cheap blocking (name similarity, category, embedding bucket) before invoking the LLM judge on a pair | Noticeable above a few hundred concepts; becomes a real bottleneck well within the 700-document target corpus, since each document can yield many concepts |
| Treating "recompile" as "recompile everything" because checksum-scoped invalidation feels safer than properly scoping cross-document invalidation | Full recompiles take longer and longer as corpus grows; team avoids running compiles during development because they're slow | Implement and test true incrementality (Pitfall 4) rather than working around it by always doing full recompiles | Becomes a daily productivity tax once the corpus is anywhere near its 700-document target size |
| Synchronous, unbounded-concurrency LLM calls across 700 documents | Rate-limit errors abort the run; bursty request patterns trigger provider throttling | Bounded concurrency with backoff, and/or batch API submission, designed for resumability after partial failure | Hits provider RPM/TPM ceilings well before reaching the full corpus if run with naive unbounded parallelism |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Sending raw Slab export content (which may include internal-only names, infrastructure details, credentials accidentally left in docs) to a third-party LLM API without review | Internal/sensitive data leaves the org boundary via every ExtractConcepts call | Add a basic pre-flight scan/allowlist step before any document is sent to an LLM provider; confirm with the user/org what data classification the 700-document corpus carries before wiring up live API calls |
| Logging full LLM prompts/responses (including document content) in plaintext for the golden-fixture/cache layer without access controls | Cached fixtures or response logs become an unintended copy of potentially sensitive source content, sitting outside the access controls of the original source system | Treat the response cache/fixture store with the same access constraints as the raw source corpus; don't assume "it's just test data" |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-------------------|
| Conflicts recorded as undifferentiated YAML dumps with no severity/category signal | User facing hundreds of recorded conflicts across 700 documents has no way to triage what matters | Categorize and rank conflicts (duplicate concept vs. minor definition wording difference vs. circular relation) so the highest-impact conflicts surface first |
| `kir compile` reports success/failure only at the whole-run level | One bad document or one failed extraction silently degrades the whole corpus's output, or aborts hours of otherwise-successful work | Per-document/per-pass status reporting, with the ability to see exactly which of the 700 documents succeeded, partially succeeded (with a recorded extraction-failure artifact), or were skipped, without losing the rest of the run |
| No visibility into LLM cost/token usage per compile run | User has no early warning before a routine recompile becomes an expensive surprise | Emit per-run and per-pass token/cost summaries as part of compile output, especially once the cache layer means most runs should be cheap — a sudden cost spike (cache miss storm) becomes immediately visible |

## "Looks Done But Isn't" Checklist

- [ ] **Determinism guarantee:** Often verified only by "ran it twice on my machine, looked the same" — verify with an explicit test that shuffles document processing order and diffs the resulting Knowledge IR byte-for-byte (Pitfall 1, 3).
- [ ] **Incremental compilation:** Often verified only by "editing one document and recompiling produces a fast result" — verify by comparing an incremental recompile's output against a full from-scratch recompile on the same corpus state; they must be identical (Pitfall 4).
- [ ] **Conflict detection coverage:** Often verified only against happy-path duplicate-concept cases — verify against the full documented conflict taxonomy (duplicate concepts, conflicting definitions, taxonomy conflicts, alias conflicts, orphan concepts, circular relations) with a dedicated adversarial fixture for each.
- [ ] **"Never silently resolve":** Often violated invisibly inside the LLM adapter (permissive validation, default-value fallbacks) even when the Conflict pass itself is correctly strict — verify by auditing every `try/except` and every Pydantic model config in the LLM adapter layer for silent coercion (Pitfall 6).
- [ ] **Provenance preservation:** Often correct for the "happy path" single-document-per-concept case but silently dropped/merged when a concept's provenance spans many source documents during a merge — verify with a concept deliberately sourced from 5+ documents and confirm all 5 provenance entries survive MergeConcepts.
- [ ] **Cost/scale readiness for 700 documents:** Often validated only against a small (10-20 document) dev sample — verify actual per-pass token costs and rate-limit behavior against a representative 50-100 document subset before attempting the full 700-document acceptance run.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|-----------------|
| Determinism broken (no response cache, relying on sampling params) | MEDIUM | Retrofit a content-addressed response cache keyed on (document checksum, prompt version, schema version, model ID); re-run the corpus once to populate it; add the shuffled-order regression test going forward |
| Silent over-merge discovered late (two distinct concepts collapsed) | HIGH | Requires re-deriving which source documents/aliases fed the bad merge from provenance records (if they were preserved — if not, this is effectively unrecoverable without re-extraction), splitting the concept, and re-running downstream relation/taxonomy passes for everything that referenced the merged concept |
| Cross-document stale-invalidation bug found in production incremental builds | MEDIUM | Force a full from-scratch recompile to re-establish ground truth, then fix the invalidation scoping (Pitfall 4) and add the incremental-vs-full diff regression test before trusting incremental compiles again |
| Cost overrun from uncached, multi-pass, full-corpus iteration during development | LOW-MEDIUM | Add the response cache retroactively (no schema changes needed if designed reasonably); going forward, restrict full-corpus runs to validated/cached prompt versions and use a small dev sample for iteration |
| Permissive validation already shipped, silent data loss suspected | MEDIUM | Re-run the affected passes with strict validation against the cached/recorded raw LLM responses (if retained) to detect what was previously discarded; if raw responses weren't retained, this requires re-calling the LLM, which reintroduces a fresh determinism question for the "recovered" data |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|-------------------|---------------|
| Determinism promised at the wrong layer (Pitfall 1) | LLM Adapter / pass-pipeline foundation phase | Compile the same corpus twice with a populated cache; assert byte-identical Knowledge IR; assert pinned model IDs appear in all metadata |
| Silent over/under-merging in alias resolution (Pitfall 2) | ResolveAliases / MergeConcepts pass design phase | Adversarial fixture: same-name-different-type concepts stay distinct with a recorded conflict; true aliases with surface variation get merged with provenance intact |
| Merge order-dependence (Pitfall 3) | MergeConcepts / BuildTaxonomy pass design phase | Shuffle document processing order, diff resulting Knowledge IR — must be identical |
| Incremental compilation misses cross-document invalidation (Pitfall 4) | Incremental compilation phase | Edit one document sharing a concept with an unedited document; incremental recompile must match a full recompile exactly |
| LLM cost/rate-limit underestimation (Pitfall 5) | LLM Adapter design phase + pre-700-doc validation milestone | Measure real per-pass token cost on a 50-100 document representative sample before the full acceptance run; confirm caching reduces repeat-run cost near zero |
| Structured-output validation silently coerced (Pitfall 6) | LLM Adapter implementation phase (first LLM-backed pass) | Audit every validation/retry code path for silent defaults; confirm an "extraction failed" artifact type exists and is exercised by a malformed-response fixture |

## Sources

- [GitHub: microsoft/graphrag Issue #1718 — Fatal Bug: Incorrect deduplication of entities with same title but different type](https://github.com/microsoft/graphrag/issues/1718) — HIGH confidence, direct production post-mortem of the exact failure mode relevant to KIR's MergeConcepts pass
- [zansara.dev — Setting the temperature to zero will make an LLM deterministic?](https://www.zansara.dev/posts/2026-03-24-temp-0-llm/) — MEDIUM-HIGH confidence, technical deep-dive on floating-point/batching non-determinism
- [unstract.com — Why is deterministic output from LLMs nearly impossible?](https://unstract.com/blog/understanding-why-deterministic-output-from-llms-is-nearly-impossible/) — MEDIUM confidence, corroborating source
- [decodingai.com — How to Keep a Knowledge Graph Clean for AI Agents](https://www.decodingai.com/p/keep-knowledge-graph-clean) — MEDIUM confidence, over-merging/corruption pattern
- [towardsdatascience.com — The Rise of Semantic Entity Resolution](https://towardsdatascience.com/the-rise-of-semantic-entity-resolution/) — MEDIUM confidence, normalize-before-merge best practice
- [GitHub: microsoft/graphrag Issue #847 — Is there an existing Entity Resolution step?](https://github.com/microsoft/graphrag/issues/847) — MEDIUM confidence, confirms name-only-matching limitation in the default pipeline
- HPI / arXiv — Transforming Pairwise Duplicates to Entity Clusters for High-quality Duplicate Detection — MEDIUM confidence, order-dependence in pairwise merge/clustering
- arXiv 1509.03302 — Performance Bounds for Pairwise Entity Resolution — MEDIUM confidence, corroborating
- [Docker Docs — Build cache invalidation](https://docs.docker.com/build/cache/invalidation/) — MEDIUM confidence, general incremental-build invalidation pattern (cross-domain analogy, not KIR-specific)
- [GitHub: microsoft/TypeScript Issue #54501 — Build cache invalidation bug](https://github.com/microsoft/TypeScript/issues/54501) — MEDIUM confidence, corroborating general incremental-build staleness pattern
- [GitHub: leanprover/lean4 Issue #13449 — Incremental build cache can cause incorrect test results](https://github.com/leanprover/lean4/issues/13449) — MEDIUM confidence, corroborating
- [morphllm.com — LLM Cost Optimization: 5 Levers to Cut API Spend 70-85%](https://www.morphllm.com/llm-cost-optimization) — MEDIUM confidence, batch/caching discount figures
- [typedef.ai — Handle Token & Rate Limits in Large-Scale LLM Inference](https://www.typedef.ai/resources/handle-token-limits-rate-limits-large-scale-llm-inference) — MEDIUM confidence, rate-limit incident root causes
- [agiflow.io — Effective Practices for Mocking LLM Responses During the SDLC](https://agiflow.io/blog/effective-practices-for-mocking-llm-responses-during-the-software-development-lifecycle) — MEDIUM confidence, golden-fixture/VCR testing strategy
- [sixty-north.com — Deterministic Testing for LangChain Agents](https://blog.sixty-north.com/deterministic-testing-for-langchain-agents.html) — MEDIUM confidence, recording-captures-decisions-not-context pitfall (prompt drift in fixtures)
- [pnt.jacbex.com — PydanticAI: Controlled LLM Output That Actually Validates](https://pnt.jacbex.com/pydanticai-2026-04-08.html) — LOW-MEDIUM confidence (single source for the 20-30% validation failure rate figure; treat as illustrative)
- [bix-tech.com — PydanticAI: Validation and Reliability in LLM Applications](https://bix-tech.com/pydanticai-validation-and-reliability-in-llm-applications-without-the-headaches/) — MEDIUM confidence, corroborating permissive-validation pitfall

---
*Pitfalls research for: LLM-assisted deterministic semantic compiler (KIR)*
*Researched: 2026-06-29*
