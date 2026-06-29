---
title: Elevate Diagnostics and LLM cache to required Phase 1/2 mechanics in ARCHITECTURE.md
date: 2026-06-29
source_todo: .planning/todos/completed/elevate-diagnostics-cache-to-required.md
---

Fix todo: ARCHITECTURE.md under-represented two hard M1 requirements (CORE-06 diagnostics, LLM-02 response cache) by framing them only under optional "Scaling Considerations" rather than as required Phase 1/2 mechanics.

## Changes

1. Pattern 1 (`extract_concepts_pass` example): thread `Diagnostic` objects through the pass's return value (`ir.diagnostics + diagnostics`), not just `concepts`.
2. Scaling Considerations / Scaling Priorities #1: reword from "consider caching LLM responses..." to state the `llm/cache.py` cache (checksum, prompt_version, schema_version, model_id) is a required Phase 2 mechanism, present from the first LLM-backed pass.
3. Suggested Build Order step 7: rename to "Real LLM adapter + response cache" and require the cache to be built alongside the adapter, not deferred.

Note: the project-structure section (`core/domain/models/diagnostic.py`, `llm/cache.py`) was already elevated into the required structure by a prior pass (see Structure Rationale bullet on line 139) — this task closes the remaining gaps in the Pattern 1 example and Scaling/Build Order sections.
