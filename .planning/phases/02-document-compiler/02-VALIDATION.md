---
phase: 02
slug: document-compiler
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-30
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (installed) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/compiler/documents/ -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| LLMPort narrowing | 01 | 0 | LLM-01 | — | N/A | unit | `uv run pytest tests/compiler/documents/test_extract_concepts_pass.py -x` | ❌ W0 | ⬜ pending |
| FakeLLMAdapter | 01 | 0 | LLM-01, LLM-03 | — | No live API calls | unit | `uv run pytest tests/llm/ -x` | ❌ W0 | ⬜ pending |
| ParsePass | 02 | 1 | DOC-01 | — | N/A | unit | `uv run pytest tests/compiler/documents/test_parse_pass.py -x` | ❌ W0 | ⬜ pending |
| SectionPass | 02 | 1 | DOC-01 | — | N/A | unit | `uv run pytest tests/compiler/documents/test_section_pass.py -x` | ❌ W0 | ⬜ pending |
| MetadataPass | 02 | 1 | DOC-01 | — | N/A | unit | `uv run pytest tests/compiler/documents/test_metadata_pass.py -x` | ❌ W0 | ⬜ pending |
| LLM cache key | 02 | 1 | LLM-02 | Degenerate cache collision | Empty component → ValueError | unit | `uv run pytest tests/llm/test_cache.py -x` | ❌ W0 | ⬜ pending |
| Prompt registry | 02 | 1 | LLM-02 | — | N/A | unit | `uv run pytest tests/llm/test_prompt_registry.py -x` | ❌ W0 | ⬜ pending |
| PydanticAIAdapter | 03 | 2 | LLM-01, DOC-03 | Prompt injection | System prompt fixed; document text never in instructions position | unit | `uv run pytest tests/llm/test_pydantic_ai_adapter.py -x` | ❌ W0 | ⬜ pending |
| ExtractConceptsPass | 03 | 2 | DOC-03, LLM-02, LLM-03 | — | Failure → Diagnostic, not halt | unit | `uv run pytest tests/compiler/documents/test_extract_concepts_pass.py -x` | ❌ W0 | ⬜ pending |
| Golden fixtures | 03 | 2 | LLM-03 | — | Zero live API calls | unit | `uv run pytest tests/compiler/documents/fixtures/extract_concepts/ -x` | ❌ W0 | ⬜ pending |
| DocumentCompiler | 04 | 3 | DOC-01, DOC-02 | — | No cross-contamination | integration | `uv run pytest tests/compiler/documents/test_document_compiler.py -x` | ❌ W0 | ⬜ pending |
| Isolation test | 04 | 3 | DOC-02 | — | Two docs produce independent IRs | integration | `uv run pytest tests/compiler/documents/test_document_compiler.py::test_no_cross_contamination -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/compiler/documents/__init__.py` — empty init
- [ ] `tests/compiler/documents/test_parse_pass.py` — stubs for DOC-01 (section splitting, H1–H6, preamble)
- [ ] `tests/compiler/documents/test_section_pass.py` — stubs for DOC-01 (section normalization)
- [ ] `tests/compiler/documents/test_metadata_pass.py` — stubs for DOC-01 (id, title, checksum, language, source fields)
- [ ] `tests/compiler/documents/test_extract_concepts_pass.py` — stubs for DOC-03, LLM-01, LLM-02, LLM-03 (D-03 failure case)
- [ ] `tests/compiler/documents/test_document_compiler.py` — stubs for DOC-01 (integration), DOC-02 (isolation)
- [ ] `tests/compiler/documents/fixtures/extract_concepts/` — 10 synthetic `.md` + expected `DocumentExtractionOutput` pairs (D-04)
- [ ] `tests/llm/__init__.py` — empty init
- [ ] `tests/llm/test_cache.py` — stubs for LLM-02 (key construction, empty-component ValueError)
- [ ] `tests/llm/test_prompt_registry.py` — stubs for prompt versioning
- [ ] `tests/llm/test_pydantic_ai_adapter.py` — stubs for LLM-01 (adapter satisfies LLMPort)
- [ ] `pyproject.toml` — add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]`; add `pytest-asyncio>=0.21` to dev deps
- [ ] `tests/conftest.py` — add `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False` autouse fixture

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
