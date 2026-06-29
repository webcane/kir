---
title: "Decision: split KIR into 5 independent packages within one repo; Core ships first"
date: 2026-06-29
context: Exploration session checking ARCHITECTURE.md consistency and evaluating a proposed 4-way architectural split (Core / Document Compiler / Knowledge Compiler / Tooling)
---

## Decision

KIR's persistent architectural shape (currently `PROJECT.md`'s "Architecture & Workstreams" table, A–E) is restructured into **5 independent packages within a single repo** (separate folders/packages with clear import boundaries, not separate repos):

1. **Core** — Domain Model, Ports (LLMPort, RepositoryPort, MarkdownParserPort), Pass API, CompilerContext
2. **Document Compiler** — Parsers, Extractors (deterministic only), Document IR assembly
3. **Knowledge Compiler** — Merge, Relations, Taxonomy, Validation
4. **LLM Infrastructure** — kept as its own package (not folded into Document Compiler's Extractors), since it has standalone correctness concerns: structured output, prompt registry/versioning, provider adapter, caching, replay tests
5. **Tooling** — CLI, Repository/Storage adapter, Tests

This maps directly onto the existing Workstream A/B/C/D/E split already named in PROJECT.md — the change is making the boundary a literal package/import boundary rather than just a conceptual workstream label.

## Dependency rule (the core constraint)

**Core is not parallelizable with the other four.** Per ARCHITECTURE.md's "Suggested Build Order" (steps 1–3), the other four packages all depend on Core's domain models and port contracts existing first — Document Compiler, Knowledge Compiler, and Tooling's Repository adapter all implement or consume Core's ports; LLM Infrastructure implements `LLMPort`.

Practical sequencing:
1. Core ships first and its contracts (domain models + ports) are frozen.
2. Document Compiler, Knowledge Compiler, LLM Infrastructure, and Tooling then proceed in parallel, each depending only on Core's frozen contracts — never on each other directly (consistent with ARCHITECTURE.md Anti-Pattern 2: passes never reach around the registry to call each other).

## Follow-up

This should be reflected in PROJECT.md's "Architecture & Workstreams" section (replacing or supplementing the current A–E table with the explicit package-boundary framing and the Core-first dependency rule) — not done in this session, left as a deliberate follow-up since PROJECT.md edits weren't in scope of this exploration's output set.
