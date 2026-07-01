# STYLE_GUIDE.md Compliance Audit — src/kir

**Date:** 2026-07-01
**Scope:** All 46 Python files under `src/kir/` (tests excluded)
**Method:** grep/AST sweep per STYLE_GUIDE.md section; no fixes applied (per todo scope)

## Summary

| # | Rule area | Status |
|---|-----------|--------|
| 1 | Type hints (generics, unions, TYPE_CHECKING, `__future__`) | ✅ Clean |
| 2 | Docstrings on public functions/classes | ⚠️ 32 gaps |
| 3 | Error handling (specific exceptions, no bare `except:`) | ✅ Clean |
| 4 | Module-level logging | ❌ Absent everywhere |
| 5 | Method structure (orchestrate/decompose) | ⚠️ Minor gaps |
| 6 | String formatting (f-strings) | ✅ Clean |
| 7 | Import order/direction | ✅ Clean |
| 8 | Naming conventions | ✅ Clean (one idiom nit) |

---

## 1. Type Hints — ✅ Clean

No occurrences of `Optional[`, `Union[`, `List[`, `Dict[`, `typing.Literal`, `TYPE_CHECKING`, or
`from __future__ import annotations` anywhere in `src/kir`. Matches the prior migration
(00356c5) and the STYLE_GUIDE's own note that this was "verified directly."

## 2. Docstrings — ⚠️ 32 public defs missing docstrings

All domain model classes (`Concept`, `Relation`, `Document`, etc.) and the main pass/compiler
modules have docstrings. The gaps cluster almost entirely in two places:

- **Port `Protocol` classes and their abstract methods** — `core/ports/*.py` (all 5 files:
  `CachePort`, `LLMCachePort`, `PromptRegistryPort`, `RepositoryPort`, `MarkdownParserPort`)
  and their `get`/`set`/`save`/`load`/`parse`/`render` method stubs.
- **Registry/context plumbing** — `core/passes/registry.py` (`PassRegistry`, `register`,
  `pipeline`), `core/passes/context.py` (`CompilerContext`), `core/passes/base.py` (`Pass`),
  `tooling/repository/yaml_repository.py` (`YamlFileRepository`, `save`, `load`), `llm/cache.py`
  (`get`, `set`).
- A handful of one-off model classes: `core/domain/manifest.py:ArtifactManifest`,
  `core/domain/ir.py:FakeIR`, `core/domain/models/conflict.py:Conflict`,
  `core/domain/models/diagnostic.py:Severity`, `core/domain/models/taxonomy.py:Taxonomy`,
  `core/domain/models/document.py:Section`, `core/domain/models/document.py:Document`,
  `compiler/documents/passes/__init__.py:decorator`.

None of these are exotic — they're `Protocol` contracts and small container classes, so the
missing docstrings are a real but low-severity gap (the guide requires docstrings on "all
public functions, classes, and modules").

## 3. Error Handling — ✅ Clean

- Zero bare `except:` blocks.
- Only 3 `except` clauses in the whole codebase, all appropriately scoped:
  - `core/passes/registry.py:46` — `except CycleError as exc:` (specific), re-raised with
    added context `from exc`.
  - `compiler/documents/compiler.py:91` — `except Exception as exc:` around a persistence
    call, re-raised as `RuntimeError(...) from exc` with a meaningful message.
  - `compiler/documents/passes/extract_concepts.py:123` — `except Exception as exc:  #
    noqa: BLE001` around the LLM call; broad-by-design (D-03 failure handling — LLM/network
    errors are unpredictable) and explicitly annotated to suppress the linter's broad-except
    warning rather than silently violating the rule.
- Every `raise X(...)` inside an `except` block chains with `from exc`.

## 4. Logging — ❌ No module-level loggers anywhere

`grep -rl "logger\."` and `grep -rl "logger = logging.getLogger"` both return zero files.
There is no `import logging` anywhere in `src/kir`. The STYLE_GUIDE's logging section (module
logger + INFO/DEBUG/ERROR usage in passes) is entirely unimplemented — this isn't a partial
violation, it's a whole rule area with 0% adoption. Worth flagging explicitly since it's easy
to assume "no findings" means compliant; here it means the feature doesn't exist yet.

## 5. Method Structure & Decomposition — ⚠️ Minor gaps

- All Pydantic model classes are correctly `frozen=True`.
- Most functions are short; the longest are:
  - `extract_concepts_pass` (70 lines, `compiler/documents/passes/extract_concepts.py:77`) —
    has clear numbered-step comments (1–5) but the body is one flat function rather than
    delegating each step to a private helper, unlike the guide's own example. Two helpers
    (`_sections_to_text`, `_apply_extraction`) already exist as module-level functions; steps
    2–4 (cache check/call/write) are still inline.
  - `MarkdownItAdapter.parse` (54 lines) and `DocumentCompiler.compile` (47 lines) — both
    read as an orchestration recipe with inline loops rather than deeper decomposition, but
    stay under a "one clear job" reading; borderline against the "under 20 lines per private
    method" guidance since they aren't split into private methods at all.
- Architectural note: the STYLE_GUIDE's "Pass Design" section shows passes as **classes**
  (`class RelationExtractionPass(Pass): async def __call__(...)`), but the actual codebase
  implements passes as **module-level functions** decorated with `@register_pass(...)`
  (`extract_concepts_pass`, `metadata_pass`, `section_pass`, `parse_pass`). This is a
  documentation/implementation mismatch, not a bug — but the guide's public/private
  method-decomposition guidance doesn't map cleanly onto function-based passes, and the doc
  should either be updated to show the function-based pattern or the passes should be
  reworked as classes to match the documented example.

## 6. String Formatting — ✅ Clean

No `.format()` or `%`-style formatting for user-facing/log messages. The single `.format()`
call (`llm/prompts/registry.py:62`, `template.format(**kwargs)`) is template interpolation
of externally-loaded prompt templates, not the kind of message formatting the rule targets —
correctly distinct from f-string message construction, and the docstring above it explains
the intent.

## 7. Import Order & Direction — ✅ Clean

- Every file groups imports stdlib → third-party → local with blank lines between groups
  (spot-checked `compiler/documents/compiler.py`, `tooling/repository/yaml_repository.py`,
  `core/passes/context.py`, and others).
- No relative imports (`from .` / `from ..`) anywhere in `src/kir` — everything uses absolute
  `kir.*` imports, which is stricter than the guide requires (it permits relative imports
  within a package) but not a violation.
- `core/domain/` imports only `pydantic` (plus stdlib `enum`/`dataclasses` in a couple of
  model files) — no adapter or pass imports leak into the domain layer.
- `core/passes/context.py` imports `LLMPort`/`LLMCachePort` from `core.ports`, not from
  `kir.llm` — correctly depends on the port, not the adapter.
- No pass-to-pass direct imports found.
- No `__all__` re-exports in any `__init__.py`.

## 8. Naming Conventions — ✅ Clean (one idiom nit)

- All classes are PascalCase, all functions/variables snake_case (spot-checked every
  `class ` declaration in the codebase — 37 classes, all compliant).
- One idiom nit: `core/domain/models/diagnostic.py:Severity` is declared as
  `class Severity(str, Enum)`. The STYLE_GUIDE's "Deprecated Methods" section recommends
  `enum.StrEnum` for fixed string sets (Python 3.11+); `(str, Enum)` still works but is the
  pattern StrEnum was introduced to replace. Not a naming violation, but worth folding into
  the same modernization pass that already removed TYPE_CHECKING/`__future__`.

---

## Recommended follow-up (not actioned — audit only)

1. Add docstrings to the 5 port `Protocol` classes + their methods, `PassRegistry`,
   `CompilerContext`, `Pass`, `YamlFileRepository`, `LLMCache.get/set`, and the remaining
   listed model classes (~32 spots, mechanical work).
2. Decide whether logging is in scope yet; if so, add module-level `logger = logging.getLogger(__name__)`
   to the passes/compiler/adapters and instrument the documented INFO/DEBUG/ERROR points. If
   intentionally deferred, note that decision somewhere so it isn't mistaken for an oversight.
3. Either update STYLE_GUIDE.md's Pass Design section to show the function-based
   `@register_pass` pattern actually in use, or migrate passes to class-based to match the doc.
4. Optional: decompose `extract_concepts_pass`'s inline cache-check/LLM-call/cache-write steps
   into private helpers, matching `_sections_to_text`/`_apply_extraction`.
5. Optional: `Severity` → `enum.StrEnum`.
