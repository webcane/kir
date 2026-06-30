---
phase: 02-document-compiler
plan: "03"
subsystem: document-compiler-passes
tags:
  - markdown-parsing
  - compiler-passes
  - document-ir
  - adapter-boundary
dependency_graph:
  requires:
    - 02-01  # Phase 2 contracts: MarkdownParserPort returns list[Section], Document models
  provides:
    - markdown-it-adapter
    - parse-pass
    - section-pass
    - metadata-pass
    - document-registry
  affects:
    - 02-04a  # DocumentCompiler wiring — imports document_registry.pipeline()
    - 02-04b  # Extraction pass — depends on parse, section, metadata passes
tech_stack:
  added: []
  patterns:
    - MarkdownItAdapter as sole markdown_it importer — adapter isolation boundary
    - document_registry PassRegistry (distinct from core PassRegistry) for document passes
    - register_pass decorator closing over document_registry (mirrors fake_passes.py pattern)
    - Forced module imports in passes/__init__.py to guarantee decorator registration
    - model_copy immutable IR update pattern for all three passes
    - _slugify() helper for URL-safe id derivation in MetadataPass
key_files:
  created:
    - src/kir/compiler/__init__.py
    - src/kir/compiler/documents/__init__.py
    - src/kir/compiler/documents/adapters/__init__.py
    - src/kir/compiler/documents/adapters/markdown_it_adapter.py
    - src/kir/compiler/documents/passes/__init__.py
    - src/kir/compiler/documents/passes/parse.py
    - src/kir/compiler/documents/passes/section.py
    - src/kir/compiler/documents/passes/metadata.py
    - tests/compiler/documents/test_parse_pass.py
    - tests/compiler/documents/test_section_pass.py
    - tests/compiler/documents/test_metadata_pass.py
  modified: []
decisions:
  - "MarkdownItAdapter is the sole file importing markdown_it — all passes call ctx.parser.parse() via MarkdownParserPort; T-02-06 grep gate passes"
  - "document_registry is a fresh PassRegistry() instance, not the core one — avoids cross-contamination between document-compiler passes and Phase 1 test passes"
  - "register_pass in passes/__init__.py closes over document_registry — same decorator pattern as fake_passes.py but for production document passes"
  - "Forced imports (from . import parse, section, metadata) at end of __init__.py — ensures decorators fire regardless of test collection order (RESEARCH.md Pitfall 3)"
  - "MetadataPass constructs Checksum(algorithm='sha256', value=hex) — includes the algorithm field per Checksum model's required fields"
  - "parse_pass imports register_pass via 'from kir.compiler.documents.passes import register_pass' (package-level import, not cross-pass import)"
metrics:
  duration: 5 minutes
  completed: "2026-06-30"
  tasks_completed: 2
  files_modified: 11
---

# Phase 02 Plan 03: Document Compiler Passes Summary

**One-liner:** MarkdownItAdapter splits Markdown at H1-H6 headings into list[Section]; ParsePass, SectionPass, MetadataPass registered into document_registry in dependency order; 26 unit tests covering all three passes; markdown_it isolated to the adapter boundary.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | MarkdownItAdapter and compiler/documents package scaffold | afb087e | src/kir/compiler/__init__.py, documents/__init__.py, adapters/__init__.py, markdown_it_adapter.py |
| 2 | ParsePass, SectionPass, MetadataPass with document-level PassRegistry and unit tests | 46df5e4 | src/kir/compiler/documents/passes/ (4 files), tests/compiler/documents/ (3 test files) |

## What Was Built

### Task 1: MarkdownItAdapter and package scaffold

Created the `kir.compiler`, `kir.compiler.documents`, and `kir.compiler.documents.adapters` package hierarchy with empty `__init__.py` files.

`MarkdownItAdapter` (`src/kir/compiler/documents/adapters/markdown_it_adapter.py`) is the sole file in the project that imports `markdown_it`. It implements `MarkdownParserPort.parse(text: str) -> list[Section]` by:
1. Calling `self._md.parse(text)` to get the markdown-it-py token stream.
2. Walking the token stream: `heading_open` starts a new section, the immediately following `inline` token is the heading text, `heading_close` ends the heading, and subsequent `inline` tokens in non-heading context contribute body content.
3. Pre-heading content becomes a preamble `Section(heading="", content=...)` per D-01.
4. Trailing empty sections are discarded.
5. Returns `[]` for blank input.

The return type is `list[Section]` (domain type), so passes never see `markdown_it` types.

### Task 2: Three deterministic passes and document_registry

`src/kir/compiler/documents/passes/__init__.py` defines:
- `document_registry = PassRegistry()` — a fresh registry instance for document-compiler passes (distinct from any core PassRegistry used in Phase 1)
- `register_pass(name, depends_on)` — decorator that closes over `document_registry`
- Forced imports: `from . import parse, section, metadata` — ensures decorators fire on module import

**ParsePass** (`parse.py`): calls `ctx.parser.parse(ir.source)`, returns `ir.model_copy(update={"sections": tuple(sections)})`. No `markdown_it` import.

**SectionPass** (`section.py`): strips leading/trailing whitespace from each `Section.content`. Depends on `parse`. Returns immutable copy.

**MetadataPass** (`metadata.py`):
- Checksum: `Checksum(algorithm="sha256", value=hashlib.sha256(ir.source.encode()).hexdigest())`
- Title: first section with non-empty heading, or "Untitled"
- Id: `_slugify(title)` — lowercase, spaces to hyphens, strip non-alnum, collapse hyphens
- Language: always `"en"`
- Depends on `parse` and `section`

`document_registry.pipeline()` returns `[parse_pass, section_pass, metadata_pass]` in correct dependency order.

### Unit Tests (26 total)

| File | Tests | Coverage |
|------|-------|----------|
| test_parse_pass.py | 7 | Sections populated, immutability, heading splitting, preamble, H1-H6 levels |
| test_section_pass.py | 6 | Whitespace stripping, heading preservation, immutability, multiple sections, empty sections |
| test_metadata_pass.py | 13 | SHA-256 checksum, determinism, title derivation, untitled fallback, slug id, language |

All 95 tests pass (69 pre-existing + 26 new).

## Deviations from Plan

### Auto-fixed Issues

None — the plan was executed exactly as written with one minor deviation:

**1. [Deviation - Order fix] Import alphabetic order corrected to match acceptance criterion**
- **Found during:** Task 2 acceptance criteria check
- **Issue:** `from . import metadata, parse, section` (alphabetical) did not match the exact grep pattern `from . import parse, section, metadata` in the acceptance criterion
- **Fix:** Changed import order to `from . import parse, section, metadata` to match the plan's specified string
- **Files modified:** `src/kir/compiler/documents/passes/__init__.py`
- **Commit:** 46df5e4

## Verification Results

All plan verification criteria passed:

- `uv run pytest tests/compiler/documents/test_parse_pass.py tests/compiler/documents/test_section_pass.py tests/compiler/documents/test_metadata_pass.py -x -q` — 26 passed
- `uv run pytest -x -q` (full suite) — 95 passed
- `grep "document_registry" src/kir/compiler/documents/passes/__init__.py` — match found
- `grep "from . import parse, section, metadata" src/kir/compiler/documents/passes/__init__.py` — match found
- `grep -r "import markdown_it" src/kir/compiler/documents/passes/` — zero matches
- `grep "depends_on" src/kir/compiler/documents/passes/section.py` — match: `depends_on=("parse",)`
- `grep "depends_on" src/kir/compiler/documents/passes/metadata.py` — match: `depends_on=("parse", "section")`
- `python -c "from kir.compiler.documents.passes import document_registry; p = document_registry.pipeline(); print(len(p) >= 3)"` — True

## Known Stubs

None — all three passes fully implement their stated behavior. The "placeholder-id" in test fixtures is intentional test-only data (metadata_pass overwrites it during the test).

## Threat Flags

No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries. Threat mitigations confirmed:

| T-ID | Status | Evidence |
|------|--------|---------|
| T-02-06 | Mitigated | `grep -r "import markdown_it" src/kir/compiler/documents/passes/` returns zero matches |
| T-02-07 | Mitigated | Passes import only from `kir.core.*` and `kir.compiler.documents.passes` (the package registry); no pass imports another pass module |
| T-02-08 | Accepted | No remediation needed per threat register |

## Self-Check: PASSED

Files verified:
- FOUND: src/kir/compiler/__init__.py
- FOUND: src/kir/compiler/documents/__init__.py
- FOUND: src/kir/compiler/documents/adapters/__init__.py
- FOUND: src/kir/compiler/documents/adapters/markdown_it_adapter.py
- FOUND: src/kir/compiler/documents/passes/__init__.py
- FOUND: src/kir/compiler/documents/passes/parse.py
- FOUND: src/kir/compiler/documents/passes/section.py
- FOUND: src/kir/compiler/documents/passes/metadata.py
- FOUND: tests/compiler/documents/test_parse_pass.py
- FOUND: tests/compiler/documents/test_section_pass.py
- FOUND: tests/compiler/documents/test_metadata_pass.py

Commits verified:
- FOUND: afb087e (Task 1)
- FOUND: 46df5e4 (Task 2)
