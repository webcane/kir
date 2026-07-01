---
goal: Add Google-style docstrings to all public APIs
scope: Pass classes, domain models, Port protocols, registry functions
priority: medium
depends: null
---

## Task Summary

Add Google-style docstrings to all public functions, classes, and modules across `src/kir/` to satisfy STYLE_GUIDE.md requirements. Current coverage is inconsistent — many public APIs lack method-level documentation of Args/Returns/Raises.

## Why It Matters

Explicit API contracts enable discoverability without reading implementation. Aligns with KIR's "explicit over implicit" principle and improves onboarding.

## Scope (What's In)

1. **Pass classes** (`.py` files in `src/kir/passes/`)
   - Class docstring (one line: "Transforms X to Y")
   - `__call__` method docstring with Args, Returns, Raises
   - Helper methods only if non-obvious

2. **Domain model classes** (`.py` files in `src/kir/domain/`)
   - `Concept`, `Relation`, `Document`, `Taxonomy`, `Conflict`, etc.
   - One-line class docstring per model
   - `__init__` or field docstrings only if non-obvious (Pydantic fields are self-documenting)

3. **Port protocols** (`src/kir/ports/`)
   - `LLMPort`, `MarkdownParserPort`, `RepositoryPort`, `CachePort`
   - Method signatures with Args, Returns, Raises

4. **Registry/pipeline functions** (`src/kir/pipeline/`)
   - Public entry points with full Args/Returns/Raises

## What's Out

- Private methods (leading underscore) — one-liner only if logic is non-obvious
- Test files (docstrings follow normal conventions, not required to be exhaustive)
- __pycache__, .git, vendored code

## Approach

1. **Audit scope** — scan `src/kir/` to identify all public APIs lacking docstrings
2. **Plan by module** — group edits by file to minimize churn
3. **Apply docstrings** — use Google-style format per STYLE_GUIDE.md
4. **Verify** — spot-check 5-10 representative docstrings for completeness

## Dependencies

**Prerequisite (completed prior):** Audit results from `audit-codebase-against-style-guide` if available. Otherwise, proceed with targeted scan of public APIs.

## Success Criteria

- All public Pass classes have docstrings with Args/Returns/Raises
- All domain model classes have class-level docstring
- All Port protocol methods have signature documentation
- All registry/pipeline entry points documented
- No coverage gaps in `src/kir/` public surface
- Docstrings follow Google style from STYLE_GUIDE.md
