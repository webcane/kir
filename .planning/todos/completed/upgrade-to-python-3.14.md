---
title: Upgrade to Python 3.14 and finalize type-hint strategy
date: 2026-07-01
priority: low
---

## Problem

Python 3.14 changes the semantics around deferred type-annotation evaluation (PEP 649 replaces PEP 563). `from __future__ import annotations` becomes redundant, and `if TYPE_CHECKING:` guards become riskier (not safer) since they can now cause runtime `ForwardRef` errors if the annotation isn't quoted.

KIR has already removed both patterns from the codebase (see commit `d9e10b5`), anticipating this shift. But the project still targets `requires-python = ">=3.13"` in `pyproject.toml`.

## Why it matters

- Confirms the codebase's current explicit-import style is forward-compatible with 3.14's default behavior.
- Once on 3.14, deferred annotation evaluation is the language default — no import needed, no TYPE_CHECKING risk from stringified forward refs.
- Third-party libraries (Pydantic, pydantic-ai) need to have caught up to PEP 649 semantics before this is safe.

## Action

1. Confirm Pydantic, pydantic-ai, and other core deps support PEP 649 `ForwardRef` semantics.
2. Bump `requires-python` to `>=3.14` in `pyproject.toml`.
3. Update CI to run on Python 3.14.
4. Re-run `scripts/check_style_rules.sh` and full test suite to confirm no regressions.
5. Update `.planning/STYLE_GUIDE.md` to note Python 3.14 as the baseline (remove "why this works" caveats tied to pre-3.14 versions, if any).

**Status:** Deferred until Python 3.14 is released/stable and dependency ecosystem catches up.
