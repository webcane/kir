---
title: Audit codebase against STYLE_GUIDE.md rules
date: 2026-07-01
priority: medium
---

## Problem

`.planning/STYLE_GUIDE.md` was written after the codebase already existed. TYPE_CHECKING/`__future__` removal was verified directly, but the other rules in the guide (type-hint style, docstrings, error handling, logging, method decomposition, naming, imports) have not been checked against the current source.

## Why it matters

Without an audit, the style guide is aspirational rather than descriptive of the real codebase state. New contributions could silently violate rules nobody checked for compliance on day one.

## Action

Review `src/kir/` against each STYLE_GUIDE.md section and report findings (don't fix yet):

1. Type hints: parameterized generics (`list[T]` not `List[T]`), union types (`T | None` not `Optional[T]`)
2. Docstrings: do public functions/classes have Google-style docstrings?
3. Error handling: specific exception types, meaningful messages, no bare `except:`
4. Logging: module-level `logger = logging.getLogger(__name__)` present where needed
5. Method structure: public methods orchestrate, private methods handle single concerns
6. String formatting: f-strings used consistently
7. Import order: stdlib → third-party → local, grouped with blank lines
8. Naming: snake_case / PascalCase / UPPER_SNAKE_CASE conventions followed

**Output:** A findings report (markdown), not fixes.

**Depends on:** none — codebase is stable enough to audit now.
