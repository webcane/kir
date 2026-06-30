---
phase: 02-document-compiler
plan: "01"
subsystem: core-contracts
tags:
  - ports
  - domain-models
  - test-infrastructure
  - async
dependency_graph:
  requires:
    - 01-04  # CompilerContext + PassRegistry (Phase 1)
  provides:
    - narrowed-llm-port
    - extraction-result-protocol
    - narrowed-parser-port
    - document-diagnostics-field
    - compiler-context-phase2-fields
    - pytest-async-infra
    - llm-call-guard
  affects:
    - 02-02  # Markdown parsing adapter + ParsePass/SectionPass/MetadataPass
    - 02-03  # LLM infrastructure (PydanticAIAdapter, cache, prompt registry)
    - 02-04a # Extraction pass + DocumentCompiler
tech_stack:
  added:
    - pydantic-ai-slim[openai,anthropic]>=2.0,<3  # LLM abstraction (adapter ring only)
    - markdown-it-py>=4.2.0  # CommonMark-compliant Markdown parser (adapter ring)
    - pydantic-settings>=2  # Settings management
    - pytest-asyncio>=0.21  # Async test support
  patterns:
    - Structural Protocol typing for ExtractionResult (domain never imports llm/)
    - TYPE_CHECKING guard for Section import in ports (avoids circular import risk)
    - asyncio_mode=auto for zero-boilerplate async tests
    - ALLOW_MODEL_REQUESTS=False autouse fixture for LLM call guard
key_files:
  created:
    - tests/compiler/__init__.py
    - tests/compiler/documents/__init__.py
    - tests/llm/__init__.py
  modified:
    - pyproject.toml
    - uv.lock
    - src/kir/core/ports/llm_port.py
    - src/kir/core/ports/parser_port.py
    - src/kir/core/domain/models/document.py
    - src/kir/core/passes/context.py
    - tests/conftest.py
    - tests/core/passes/fakes/fake_llm_port.py
    - tests/core/passes/fakes/fake_parser.py
    - tests/core/passes/test_pipeline_execution.py
    - tests/core/passes/test_context.py
decisions:
  - "LLMPort.extract() uses TYPE_CHECKING guard for Section import — document.py does not import from ports/, so the import is safe, but TYPE_CHECKING avoids any future circular import issues as the graph grows"
  - "ExtractionResult defined as structural Protocol in core/ (not llm/) — pass-ring code can type-hint against it without violating the hexagonal boundary (Anti-Pattern 4 compliance)"
  - "prompts: object = None in CompilerContext — PromptRegistry lives in llm/; typing as object preserves the hexagonal boundary (consistent with Protocol-typing approach)"
  - "FakeMarkdownParser.parse() now returns list[Section] with one fake section — existing Phase 1 tests that call parse() now get structured output rather than raw dict"
  - "test_pipeline_execution.py test updated to async since LLMPort.extract() is now async — asyncio_mode=auto handles this without @pytest.mark.asyncio decoration"
metrics:
  duration: 5 minutes
  completed: "2026-07-01"
  tasks_completed: 3
  files_modified: 14
---

# Phase 02 Plan 01: Phase 2 Contracts and Infrastructure Summary

**One-liner:** Phase 2 contracts established — LLMPort narrowed to async extract(sections, prompt) with ExtractionResult Protocol, MarkdownParserPort returns list[Section], Document gains diagnostics field, CompilerContext gains three Phase 2 fields, pytest-asyncio and pydantic-ai-slim installed, LLM call guard wired.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Install Phase 2 deps and configure asyncio_mode | c0ca870 | pyproject.toml, uv.lock |
| 2 | Narrow LLMPort and MarkdownParserPort contracts | 4c069e1 | src/kir/core/ports/llm_port.py, parser_port.py, fakes, tests |
| 3 | Extend Document, CompilerContext; scaffold test packages; add LLM guard | f486bde | document.py, context.py, conftest.py, 3x __init__.py |

## What Was Built

### Task 1: Dependencies and pytest configuration

Installed four new packages:
- `pydantic-ai-slim[openai,anthropic]>=2.0` — the LLM adapter library (only permitted in `src/kir/llm/` per CLAUDE.md)
- `markdown-it-py>=4.2.0` — CommonMark-compliant Markdown parser (Google Assured OSS)
- `pydantic-settings>=2` — for typed settings objects
- `pytest-asyncio>=0.21` — async test support

Added `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` so async test functions need no decorator boilerplate.

### Task 2: Narrowed port contracts (interface-first guarantee)

`src/kir/core/ports/llm_port.py` was rewritten with two Protocols:
- `ExtractionResult` — structural Protocol with `concepts`, `glossary`, `entities`, `references` list attributes. Lives in `core/` so pass-ring code can type-hint against the result without importing from `llm/`.
- `LLMPort` — Protocol with `model_id: str` and `async def extract(self, *, sections: list[Section], prompt: str) -> ExtractionResult`. Implements D-02 (one combined call per document).

`src/kir/core/ports/parser_port.py` return type changed from `object` to `list[Section]`.

Both fakes updated accordingly: `FakeLLMPort` gets `model_id = "fake:v0"` and async `extract()`; `FakeMarkdownParser.parse()` returns `list[Section]`.

Two Phase 1 tests updated to match the new signatures:
- `test_pipeline_execution.py`: `test_fake_ports_construct_with_no_arguments_and_are_callable` made async, uses `await llm.extract(sections=[], prompt="test")`
- `test_context.py`: `_FakeLLM` and `_FakeParser` private test classes updated to new signatures

### Task 3: Domain model extension and test infrastructure

`Document` model gained `diagnostics: tuple[Diagnostic, ...] = ()` field after `references` (D-03 prerequisite — extraction pass will populate it on errors).

`CompilerContext` gained three optional Phase 2 fields with defaults (all existing construction sites remain valid without changes):
- `prompt_version: str = ""`
- `llm_cache: CachePort | None = None`
- `prompts: object = None`

Three empty test package `__init__.py` files created for future Phase 2 tests:
- `tests/compiler/__init__.py`
- `tests/compiler/documents/__init__.py`
- `tests/llm/__init__.py`

`tests/conftest.py` gained `block_real_llm_calls` — an `autouse=True, scope="session"` fixture that sets `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False` for the entire test session (LLM-03 compliance). Any test that accidentally reaches a live API will fail loudly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_pipeline_execution.py to use async extract() call**
- **Found during:** Task 2 verification (uv run pytest tests/core/ -x -q)
- **Issue:** `test_fake_ports_construct_with_no_arguments_and_are_callable` called `llm.extract("some text")` with the old positional text argument; fails with TypeError after narrowing
- **Fix:** Made test function async; updated to `await llm.extract(sections=[], prompt="test")`; updated `parser.parse()` return type assertion from `object` to `list`
- **Files modified:** `tests/core/passes/test_pipeline_execution.py`
- **Commit:** 4c069e1

**2. [Rule 1 - Bug] Updated test_context.py _FakeLLM and _FakeParser to new signatures**
- **Found during:** Task 2 — proactive check of all fake implementations
- **Issue:** `_FakeLLM` in `test_context.py` used old `extract(text)` signature; `_FakeParser` returned `object` not `list`
- **Fix:** `_FakeLLM` gets `model_id = "fake:v0"` and `async def extract(*, sections, prompt)` shape; `_FakeParser.parse()` returns `list`
- **Files modified:** `tests/core/passes/test_context.py`
- **Commit:** 4c069e1

## Verification Results

All plan verification criteria passed:
- `uv run pytest -x -q` — 69 passed (0 failures)
- `grep -r "def extract(self, text" src/kir/core/` — zero matches
- `grep "async def extract" src/kir/core/ports/llm_port.py` — 1 match
- `grep "diagnostics" src/kir/core/domain/models/document.py` — 1 match
- `grep "prompt_version" src/kir/core/passes/context.py` — 1 match
- `grep "asyncio_mode" pyproject.toml` — 1 match
- `python -c "import pydantic_ai"` — exit 0
- `python -c "import markdown_it"` — exit 0

## Known Stubs

None — this plan establishes contracts only (Protocol definitions, field additions). No data-flow stubs were introduced; the new fields all have safe empty defaults.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries introduced. The `block_real_llm_calls` fixture mitigates T-02-02 (live API calls in tests). Supply-chain risk (T-02-SC) was pre-audited in RESEARCH.md — all four packages confirmed legitimate before install.

## Self-Check: PASSED

Files verified:
- FOUND: src/kir/core/ports/llm_port.py
- FOUND: src/kir/core/ports/parser_port.py
- FOUND: src/kir/core/domain/models/document.py
- FOUND: src/kir/core/passes/context.py
- FOUND: tests/conftest.py
- FOUND: tests/compiler/__init__.py
- FOUND: tests/compiler/documents/__init__.py
- FOUND: tests/llm/__init__.py

Commits verified:
- FOUND: c0ca870 (Task 1)
- FOUND: 4c069e1 (Task 2)
- FOUND: f486bde (Task 3)
