---
phase: 2
phase_name: "Document Compiler"
project: "KIR"
generated: "2026-07-01"
counts:
  decisions: 13
  lessons: 8
  patterns: 9
  surprises: 6
missing_artifacts:
  - "02-UAT.md"
---

# Phase 2 Learnings: Document Compiler

## Decisions

### ExtractionResult defined as structural Protocol in core/, not llm/

`ExtractionResult` is a `typing.Protocol` in `src/kir/core/ports/llm_port.py`, not in `src/kir/llm/`. The extraction pass can type-hint against it without ever importing from `kir.llm`.

**Rationale:** Anti-Pattern 4 in ARCHITECTURE.md: domain/pass code must not import from infrastructure adapters. Defining `ExtractionResult` in `core/` means the extraction pass is typed correctly at the boundary while respecting the hexagonal boundary.
**Source:** 02-01-SUMMARY.md

---

### prompts: object = None in CompilerContext (later upgraded to PromptRegistryPort)

Initially `CompilerContext.prompts` was typed as `object` to preserve the hexagonal boundary: `PromptRegistry` lives in `llm/`, and importing it in `context.py` would have violated CORE-01. The final implementation introduced a `PromptRegistryPort` Protocol in `core/ports/` as the correct fix.

**Rationale:** Typing as `object` was a deferred decision that correctly avoided importing the adapter. The code review (CR-02/WR-04) identified that the correct resolution is a domain-owned port, not a bare `object` type. The `PromptRegistryPort` was added in the critical-fixes pass.
**Source:** 02-01-SUMMARY.md, 02-REVIEW.md

---

### asyncio_mode=auto for zero-boilerplate async tests

`asyncio_mode = "auto"` in `[tool.pytest.ini_options]` makes all async test functions runnable without `@pytest.mark.asyncio` decoration.

**Rationale:** Boilerplate decoration on every async test is noise and causes silent failures when forgotten. `asyncio_mode=auto` is the pytest-asyncio recommended approach for codebases where async tests are the norm.
**Source:** 02-01-SUMMARY.md

---

### ALLOW_MODEL_REQUESTS=False autouse session fixture blocks live API calls

`tests/conftest.py` sets `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False` in an autouse session fixture. Any test that reaches a live LLM endpoint fails loudly with a `ModelError`.

**Rationale:** LLM-03 requires zero live API calls in the test suite. The autouse session scope ensures this invariant holds even for tests that don't explicitly use `FakeLLMAdapter` — a future test author cannot accidentally introduce a live call without failing CI.
**Source:** 02-01-SUMMARY.md

---

### document_registry is a fresh PassRegistry(), separate from the core registry

`src/kir/compiler/documents/passes/__init__.py` creates `document_registry = PassRegistry()` — a fresh instance entirely separate from any registry used in Phase 1 tests.

**Rationale:** A shared registry would cross-contaminate Phase 1 fake passes with Phase 2 document passes. Separate instances mean `document_registry.pipeline()` returns exactly the four document-compiler passes and nothing else.
**Source:** 02-03-SUMMARY.md

---

### Forced imports in passes/__init__.py guarantee decorator registration order

`src/kir/compiler/documents/passes/__init__.py` ends with `from . import parse, section, metadata, extract_concepts`. These forced imports ensure every `@register_pass` decorator fires when the package is imported, regardless of pytest collection order.

**Rationale:** RESEARCH.md Pitfall 3: if a pass module is never imported during a test run (e.g., pytest only collected tests from another module), the decorator never fires and the pass is invisible to `pipeline()`. The forced imports fix this at the package level.
**Source:** 02-03-SUMMARY.md

---

### _apply_extraction typed as object to honor the LLMPort seam

`extract_concepts.py`'s `_apply_extraction(ir, result)` types `result` as `object`. The pass never imports `DocumentExtractionOutput` or any type from `kir.llm` — attribute access is via duck typing with `# type: ignore[attr-defined]`.

**Rationale:** Importing `DocumentExtractionOutput` in the extraction pass would violate the hexagonal boundary. The `object` type + duck typing approach keeps `kir.compiler` import-clean of `kir.llm`, verified by `grep -r "import kir.llm" src/kir/compiler/`.
**Source:** 02-04a-SUMMARY.md

---

### DocumentCompiler constructs initial Document with empty Checksum

`DocumentCompiler.compile()` creates the initial `Document` with `Checksum(algorithm="sha256", value="")`. MetadataPass then computes and fills the real SHA-256 checksum.

**Rationale:** Computing the SHA-256 at construction time (before passes run) would mean computing it twice — once to build the initial Document, once in MetadataPass. Seeding with an empty value avoids double-computation and makes the metadata pass the single source of truth for checksum.
**Source:** 02-04a-SUMMARY.md

---

### make_phase2_context() is a plain function, not a pytest fixture

`tests/compiler/documents/conftest.py` defines `make_phase2_context()` as a plain function, not a `@pytest.fixture`.

**Rationale:** `test_no_cross_contamination` needs two independent contexts within a single test. pytest fixtures can only produce one value per test invocation — a plain function can be called as many times as needed within a test body.
**Source:** 02-04b-SUMMARY.md

---

### _ErrorFakeLLMAdapter lives in conftest, not in src/

The error-raising test double is defined in `tests/compiler/documents/conftest.py` rather than in `src/kir/llm/fake_adapter.py`.

**Rationale:** Error injection is a test concern, not a production concern. Placing it in `src/` would pollute the production adapter tree with test-only code. Keeping it in conftest makes the scope explicit.
**Source:** 02-04b-SUMMARY.md

---

### test_no_cross_contamination uses separate DocumentCompiler instances per file

The isolation test creates separate `DocumentCompiler` instances (and separate `InMemoryCache` instances) for each input file, not a shared compiler.

**Rationale:** A shared cache with a shared compiler could mask isolation failures — if two documents happen to produce the same cache key, the second would return the first's cached LLM output. Separate instances eliminate this possibility.
**Source:** 02-04b-SUMMARY.md

---

### DOC_02_EXPECTED has empty concepts list — glossary and concept are mutually exclusive

The golden fixture for `doc_02_glossary_heavy.md` specifies zero concepts despite the document having five explicit term definitions.

**Rationale:** The AI-SPEC category-boundary rule: a term that is explicitly defined in text is a glossary entry, not a concept. Concepts are implicitly used terms. A term that appears in both would be double-counted. The empty concepts list encodes this as a test assertion.
**Source:** 02-04b-SUMMARY.md

---

### LLMCachePort defined as new Protocol in core/ports/

Rather than reusing `CachePort` (which has a generic `get(key: str)` interface), a new `LLMCachePort` Protocol was defined in `core/ports/llm_cache_port.py` with the four-keyword `get(checksum, prompt_version, schema_version, model_id)` interface.

**Rationale:** This resolved CR-02 cleanly: `CompilerContext.llm_cache` can be typed as `LLMCache | None` (or `LLMCachePort | None`) and the type checker can verify call sites. The generic `CachePort` is too narrow for the LLM-specific cache key structure.
**Source:** 02-VERIFICATION.md

---

## Lessons

### Prompt formatting bug invisible when FakeLLMAdapter ignores the prompt argument

CR-01 (sections passed as Python tuple repr to the prompt renderer) was invisible to the test suite because `FakeLLMAdapter.extract()` ignores the `prompt` parameter and returns a canned output unconditionally. The LLM would have received unparseable input in production.

**Context:** The test for the prompt registry used a raw string, not a serialized `list[Section]`. The fix was to add `_sections_to_text()` in the extraction pass and assert on the rendered string in a test that exercises the full call path. Future: any test involving a fake LLM adapter should also test the prompt content, not just the return value.
**Source:** 02-REVIEW.md

---

### Context field typed incorrectly causes runtime TypeError suppressed by type: ignore

CR-02: `CompilerContext.llm_cache` was typed as `CachePort | None` but `extract_concepts_pass` called it with four keyword arguments that only `LLMCache` (not `CachePort`) accepts. The mismatch was suppressed by `# type: ignore[union-attr]` and caught only in code review.

**Context:** `type: ignore` comments on optional field access should be a red flag that the field's declared type doesn't match the usage. The fix is to narrow the type (define a `LLMCachePort` Protocol) rather than suppress the error. Never suppress a `union-attr` ignore without resolving the underlying type mismatch.
**Source:** 02-REVIEW.md

---

### Null guards for optional context fields must precede the D-03 exception handler

CR-03: `extract_concepts_pass` called `ctx.prompts.render()` and `ctx.llm_cache.get()` before the D-03 `except Exception` handler. `AttributeError` on `None` occurred before the handler could catch it, crashing the pipeline entirely instead of emitting a `Diagnostic`.

**Context:** The D-03 exception handler only covers the LLM call (step 3). If steps 1 or 2 fail, they fail outside the handler. Null-check optional fields at pass entry — before any call site — and return early (or raise `ValueError`) if required fields are absent.
**Source:** 02-REVIEW.md

---

### Subagent worktree isolation fails when local branch is ahead of origin

Plan 02-02's worktree subagent attempts failed the `worktree_branch_check` guard twice because the local `master` (post-wave-1 merge) was ahead of `origin/master`. Execution fell back to sequential main-tree.

**Context:** Worktree isolation requires creating the worktree from the current local branch, not `origin/master`. When the orchestrator's branch check compares against the remote tip, any ahead-of-origin state causes the guard to fail. This is an orchestration tooling limitation, not a code issue — but it means worktree isolation is fragile when local commits haven't been pushed.
**Source:** 02-02-SUMMARY.md

---

### Subagent session usage limits can cut execution mid-plan

Plan 02-02's subagent hit a session usage limit after completing Tasks 1 and 2. Task 3 (tests) was completed inline by the orchestrator.

**Context:** Multi-task plans with large file counts are at risk of hitting per-session limits in subagent mode. Mitigation: keep subagent task scope small (1-2 tasks per subagent dispatch), or plan for orchestrator inline completion of the final task.
**Source:** 02-02-SUMMARY.md

---

### extract_concepts must appear in the forced import list in passes/__init__.py

When Plan 04a added `extract_concepts.py`, the forced import list in `passes/__init__.py` had to be updated to include `from . import extract_concepts`. Without this, the pass is never registered in `document_registry`.

**Context:** Every new pass module added to `src/kir/compiler/documents/passes/` must also be added to the forced import list in `__init__.py`. This is easy to forget. The verification command `python -c "from kir.compiler.documents.passes import document_registry; print(len(document_registry.pipeline()))"` should be run after adding any new pass.
**Source:** 02-04a-SUMMARY.md

---

### asyncio.iscoroutinefunction() required to dispatch mixed sync/async pipeline

`DocumentCompiler.compile()` uses `asyncio.iscoroutinefunction(pass_fn)` to determine whether to `await` or call directly. A pipeline with mixed sync/async passes cannot use a uniform dispatch without this check.

**Context:** The current pipeline is all-sync (parse, section, metadata) except `extract_concepts` (async). `iscoroutinefunction` handles the mixed case without requiring every pass to become async or wrapping sync passes in coroutines.
**Source:** 02-04a-SUMMARY.md

---

### STOR-01/STOR-02 gap not caught until milestone audit

`YamlFileRepository` was proven in Phase 1 isolation, but `DocumentCompiler.compile()` was never wired to call `ctx.repository.save()`. The integration gap was invisible to phase-level tests and only surfaced at the M1 milestone audit.

**Context:** Phase-level verification confirms individual components work. Cross-phase integration — specifically "does the compiler write artifacts to disk?" — requires an E2E flow test, not just unit tests of the repository adapter. Future: integration tests should include a filesystem assertion ("a YAML file was created at the expected path") alongside the in-memory Document IR assertions.
**Source:** v1.0-MILESTONE-AUDIT.md

---

## Patterns

### Async pass: async def + asyncio.iscoroutinefunction dispatch

An async pass is a coroutine function with the same signature as a sync pass: `async def pass_fn(ir: Document, ctx: CompilerContext) -> Document`. `DocumentCompiler.compile()` gates dispatch on `asyncio.iscoroutinefunction(pass_fn)`.

**When to use:** Any pass that calls an async adapter (LLMPort, future async RepositoryPort). The pattern allows mixing sync and async passes in a single pipeline without forcing all passes to be async.
**Source:** 02-04a-SUMMARY.md

---

### D-03 failure path: bare except Exception + Diagnostic, no halt

When an LLM call fails inside a pass, the failure path is:
```python
except Exception as exc:
    ir = ir.model_copy(update={"diagnostics": ir.diagnostics + (Diagnostic(..., severity=ERROR),)})
    return ir
```
The pipeline continues with the remaining passes on the Diagnostic-annotated IR.

**When to use:** Any pass that calls a fallible external service (LLM, future HTTP adapter). Halting the pipeline on LLM failure violates the "always run all passes" principle (D-01). The Diagnostic preserves the failure record for downstream inspection without aborting.
**Source:** 02-04a-SUMMARY.md

---

### LLMPort seam: pass accesses LLM only via ctx.llm, never imports kir.llm

No file under `src/kir/compiler/` imports any symbol from `kir.llm`. Extraction passes access LLM via `ctx.llm.extract(...)` (typed against `LLMPort`), cache via `ctx.llm_cache` (typed against `LLMCachePort`), and prompts via `ctx.prompts` (typed against `PromptRegistryPort`).

**When to use:** All extraction passes. The boundary is enforced by `grep -r "from kir.llm" src/kir/compiler/` → zero matches. Add this grep to the verification checklist for any Phase 3+ pass that calls an external service.
**Source:** 02-04a-SUMMARY.md

---

### FakeLLMAdapter in src/, not tests/ — production-tree test double

`FakeLLMAdapter` lives in `src/kir/llm/fake_adapter.py` so it can be imported by integration tests, end-to-end scripts, and future CLI tooling without path hacks.

**When to use:** Any test double intended for use outside of `tests/` (e.g., a development REPL, a CLI dry-run mode). Doubles that are only used in `tests/` can live in `tests/`.
**Source:** 02-02-SUMMARY.md

---

### Golden fixture replay: FakeLLMAdapter(output=EXPECTED) without live API calls

Integration tests configure `FakeLLMAdapter` with a hand-authored `DocumentExtractionOutput` constant. The test then runs the full pipeline and asserts that the Document IR fields match the DTO fields.

**When to use:** E2E extraction tests that verify the full pipeline behavior (prompt rendering, cache key construction, LLM output mapping). The fixture + expected_outputs pattern makes test intent explicit and allows running the full pipeline without any LLM API access.
**Source:** 02-04b-SUMMARY.md

---

### LLMCacheKey.build() enforces all four components non-empty

`LLMCacheKey.build(checksum, prompt_version, schema_version, model_id)` raises `ValueError` if any component is an empty string.

**When to use:** Any cache key construction that depends on versioned inputs. An empty component produces a degenerate key (e.g., `"abc::v2:gpt-4"`) that silently collides with any other key that has the same non-empty components. Enforcing non-empty at build time is cheap and prevents silent cache poisoning.
**Source:** 02-02-SUMMARY.md

---

### ALLOW_MODEL_REQUESTS=False autouse session fixture

```python
@pytest.fixture(autouse=True, scope="session")
def block_real_llm_calls() -> Generator[None, None, None]:
    original = pydantic_ai_models.ALLOW_MODEL_REQUESTS
    pydantic_ai_models.ALLOW_MODEL_REQUESTS = False
    yield
    pydantic_ai_models.ALLOW_MODEL_REQUESTS = original
```

**When to use:** Any test suite that includes a pydantic-ai adapter or any code that might reach a live LLM endpoint. The autouse + session scope means no test can bypass it. Note: the correct return type is `Generator[None, None, None]`, not `object` (see WR-05 in 02-REVIEW.md).
**Source:** 02-01-SUMMARY.md

---

### PromptRegistry with versioned Markdown templates

`PromptRegistry` loads prompt templates by name from a `prompts/` directory (e.g., `extract_v1.md`). Templates use `str.format(**kwargs)` interpolation. Missing templates raise `PromptNotFoundError` (subclass of `FileNotFoundError`).

**When to use:** Any phase that adds new LLM extraction prompts. Name the file with a version suffix (`_v1`, `_v2`) so old prompts remain available for cache replay. `PromptNotFoundError` is catchable by callers that want to fall back gracefully.
**Source:** 02-02-SUMMARY.md

---

### Phase 2 context helper: make_phase2_context() function

`make_phase2_context(fake_output=None, raise_error=None)` constructs a full `CompilerContext` for Phase 2 extraction tests: `FakeLLMAdapter` or `_ErrorFakeLLMAdapter`, `InMemoryCache`, `LLMCache`, `PromptRegistry`, `MarkdownItAdapter`, all wired into `CompilerContext`.

**When to use:** Any extraction pass test or DocumentCompiler integration test in Phase 2+. The helper centralizes the wiring so tests don't duplicate 15+ lines of context construction. Plain function (not fixture) allows multiple contexts per test.
**Source:** 02-04b-SUMMARY.md

---

## Surprises

### Prompt receives Python object repr — invisible because FakeLLMAdapter ignores prompt

CR-01 was a production-quality bug: every extraction prompt sent to a real LLM would contain `(Section(heading='...', content='...'),)` instead of readable text. The test suite passed because `FakeLLMAdapter.extract()` ignores its `prompt` argument entirely.

**Impact:** High if uncaught before production use. The fix (`_sections_to_text()`) was straightforward — the surprise was that neither the pass author nor the initial test suite caught it. Any fake that ignores input arguments creates a blind spot for input validation bugs. Consider adding an assertion on the `prompt` argument in `FakeLLMAdapter` to catch formatting regressions.
**Source:** 02-REVIEW.md

---

### MarkdownItAdapter silently drops all code block content

`MarkdownItAdapter` captures only `inline` tokens. `fence` tokens (code blocks) have their content in `token.content`, not in inline children — they are silently dropped. A section containing only a code block produces `Section(content='')`.

**Impact:** Medium. The Phase 2 golden fixtures don't contain standalone code-block sections, so no test caught this. For a documentation corpus with code-heavy sections (e.g., API reference docs), extraction quality would be significantly degraded. Fix: handle `fence` tokens explicitly with `current_content_parts.append(token.content)`.
**Source:** 02-REVIEW.md

---

### Worktree subagent isolation failed — local master ahead of origin/master

Plan 02-02 required two worktree fallbacks before switching to sequential main-tree execution. The root cause was that `origin/master` was at the Phase 1 tip while local `master` had post-wave-1 commits. The worktree branch check guard used `origin/master` as the reference.

**Impact:** Low code impact — Plan 02-02 completed correctly via main-tree execution. The operational surprise: worktree isolation as currently implemented is unreliable when local commits haven't been pushed. Subagents should be documented as requiring a clean upstream sync before use.
**Source:** 02-02-SUMMARY.md

---

### Narrowing FakeMarkdownParser.parse() return type broke 2 Phase 1 tests

When Plan 02-01 changed `MarkdownParserPort.parse()` from `object` to `list[Section]` and updated `FakeMarkdownParser` accordingly, two Phase 1 tests (`test_pipeline_execution.py` and `test_context.py`) that used the old `llm.extract("some text")` and `parser.parse()` signatures broke.

**Impact:** Low — both were auto-fixed in the same commit. The lesson: any narrowing of a port interface is a breaking change for all existing fakes. Check all fake implementations (not just the primary one) before committing an interface change.
**Source:** 02-01-SUMMARY.md

---

### Phase 2 code review found 3 critical bugs that blocked a clean pass

The Phase 2 code review (`/gsd-code-review`) found 3 critical findings (CR-01: prompt repr, CR-02: cache type mismatch, CR-03: null crash) that required a follow-up implementation pass before verification. All three were invisible to the test suite.

**Impact:** Medium delay — required a critical-fixes plan before the verification pass could succeed. The 3 criticals all shared a root cause: `FakeLLMAdapter`'s ignoring of input parameters meant tests didn't exercise the full call path. This suggests the Phase 2 code review should have been run before writing golden fixture tests, not after.
**Source:** 02-REVIEW.md, 02-VERIFICATION.md

---

### STOR-01/STOR-02 gap only surfaced at milestone audit, not phase verification

Both Phase 1 and Phase 2 verifications passed. The STOR-01/STOR-02 integration gap (DocumentCompiler never calls ctx.repository.save()) was only caught at the M1 milestone audit, not at any phase boundary.

**Impact:** Medium. The YamlFileRepository works correctly in isolation. The gap means no YAML artifact is written to disk during compilation — the Document IR only exists in memory. The milestone audit's cross-phase integration check was the correct detection mechanism; the gap was genuinely invisible to per-phase verification, which checked component behavior, not pipeline behavior.
**Source:** v1.0-MILESTONE-AUDIT.md

---

_Phase: 02-document-compiler_
_Generated: 2026-07-01_
_Source artifacts: 02-01..04b-SUMMARY.md, 02-REVIEW.md, 02-VERIFICATION.md, v1.0-MILESTONE-AUDIT.md_
