---
title: Rewrite CLAUDE.md per architectural-invariants structure
date: 2026-06-29
priority: medium
---

## Task

Rewrite `/Users/mniedre/git/kir/CLAUDE.md` so it stops duplicating stack tables and Architecture Principles already covered by `.planning/PROJECT.md`, and instead becomes a thin decision-making layer: "how should the agent think when implementing KIR," not what KIR is or what to build now.

## Target structure (per exploration session, see [[claude-md-redesign-rationale]])

1. **Product Identity** — one paragraph: KIR is a semantic compiler; Knowledge IR is the final product boundary. Link to PROJECT.md's Product Boundary diagram rather than restating it.
2. **Implementation Philosophy** — short bullet list: compiler architecture over pipelines, explicit Pydantic models over dicts, immutable IR, small independently-testable passes, no hidden side effects, no global state.
3. **Layer Boundaries / What NOT to build** — terse restatement of the recurring violations an agent is likely to attempt (importing LLM/YAML SDKs into domain/, passes calling each other directly, building rendering/query/vector-search features). Link to REQUIREMENTS.md's Out of Scope table and ARCHITECTURE.md's Anti-Patterns section instead of re-deriving them.
4. **Decision Hierarchy** (confirmed, do not re-litigate): Correctness → Determinism → Canonical Knowledge IR → Extensibility → Performance → Developer Convenience.
5. **Definition of Done** — deterministic, independently tested, reproducible, versioned, documented, compatible with incremental compilation.
6. **References** — explicit links to `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/PROCESS.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/SUMMARY.md`, `.planning/research/FEATURES.md`, `.planning/research/STACK.md`.

## Explicitly remove from CLAUDE.md

- The full Stack table (Technology Stack section) — belongs in research/STACK.md, not a system prompt that should survive a language rewrite.
- Duplicated Architecture Principles / Architectural Decisions — PROJECT.md owns these, CLAUDE.md should link, not copy.
- Empty placeholder sections (Conventions, Architecture "not yet mapped") — replace with the new structure or drop if genuinely empty.

## Note on existing GSD-managed sections

CLAUDE.md currently has GSD-managed blocks (`<!-- GSD:project-start -->`, `<!-- GSD:stack-start -->`, etc.) that appear to be auto-generated/synced from PROJECT.md, STACK.md research, etc. Check whether this rewrite should happen by editing the source files those blocks sync from (PROJECT.md, a new CONVENTIONS.md philosophy section) rather than hand-editing CLAUDE.md directly, to avoid the next GSD sync overwriting the rewrite. Worth checking `/gsd-docs-update` or the GSD sync mechanism before hand-editing.

## Suggested entry point

Run via `/gsd-quick` per this project's CLAUDE.md workflow-enforcement rule (file-changing edits should go through a GSD command).
