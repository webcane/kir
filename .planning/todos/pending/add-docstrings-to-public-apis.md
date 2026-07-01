---
title: Add Google-style docstrings to all public APIs
date: 2026-07-01
priority: medium
---

## Problem

STYLE_GUIDE.md requires Google-style docstrings on all public functions, classes, and modules. Current coverage across `src/kir/` is inconsistent — some Pass classes and domain models have module-level docstrings, but method-level `Args`/`Returns`/`Raises` documentation is largely absent.

## Why it matters

Without consistent docstrings, the compiler's pass contracts (what a pass expects/returns/raises) aren't discoverable without reading the implementation. This slows onboarding and makes API contracts implicit rather than explicit — contrary to the project's "explicit over implicit" principle.

## Action

Add docstrings to:

- All `Pass` implementations and their `__call__` methods (describe what IR transformation occurs, Args, Returns, Raises)
- All domain model classes (`Concept`, `Relation`, `Document`, `Taxonomy`, `Conflict`, etc.) — one-line class purpose
- All public `Port` protocols (`LLMPort`, `MarkdownParserPort`, `RepositoryPort`, `CachePort`)
- Registry/pipeline public functions

Format:
```python
async def __call__(self, ir: KnowledgeIR, ctx: CompilerContext) -> KnowledgeIR:
    """One-line summary.

    Args:
        ir: ...
        ctx: ...

    Returns:
        ...

    Raises:
        ...
    """
```

Private methods only need docstrings if non-obvious; brief one-liners are fine otherwise.

**Depends on:** [[audit-codebase-against-style-guide]] — audit first to know exact scope/gaps.
