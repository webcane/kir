---
title: Elevate Diagnostics and LLM cache from optional-scaling framing to required Phase 1/2 mechanics in ARCHITECTURE.md
date: 2026-06-29
priority: medium
---

## Problem

Two hard M1 requirements are under-represented in `.planning/research/ARCHITECTURE.md`:

1. **CORE-06** requires every pass to return structured diagnostics (code, severity, source location, optional suggestion) as part of its output artifact. ARCHITECTURE.md's Pattern 1 example (`extract_concepts_pass`) returns only `ir.model_copy(update={"concepts": concepts})` — no diagnostics shown anywhere in the recommended structure or examples.
2. **LLM-02** requires LLM responses to be cached/recorded keyed on (document checksum, prompt version, schema version, pinned model id). ARCHITECTURE.md only mentions this in "Scaling Considerations" as an optional optimization for future scale ("consider caching LLM responses..."), not as a required Phase 2 mechanism.

## Why it matters

Both are explicit M1 (current milestone) requirements, not deferred v2/v3 concerns. Framing them as optional scaling work risks them being skipped or bolted on late, which is exactly the kind of retrofit the project's "structural guarantees designed in from step 1-3" build-order philosophy warns against.

## Action

Update ARCHITECTURE.md:
- Add a `Diagnostics` value object to the recommended domain/IR structure and show it threaded through the Pattern 1 pass example.
- Add an explicit cache abstraction/module (keyed on checksum + prompt_version + schema_version + model id) to the recommended project structure and Suggested Build Order, not just the Scaling Considerations section.
