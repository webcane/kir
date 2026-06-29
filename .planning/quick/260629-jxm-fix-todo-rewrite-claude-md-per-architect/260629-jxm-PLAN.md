---
task: rewrite-claude-md-architectural-invariants
date: 2026-06-29
type: quick
---

# Plan: Rewrite CLAUDE.md per architectural-invariants structure

## Resolution: GSD sync-block handling

`/Users/mniedre/.claude/gsd-core/templates/claude-md.md` and `docs-update.md` confirm: `generate-claude-md` independently resyncs the content **inside** `<!-- GSD:project-start source:PROJECT.md -->`, `<!-- GSD:stack-start source:STACK.md -->`, `<!-- GSD:conventions-start source:CONVENTIONS.md -->`, and `<!-- GSD:architecture-start source:ARCHITECTURE.md -->` markers from their respective source files, with no hand-written-content detection inside those specific blocks (the hand-written-doc preservation prompt in docs-update.md applies to whole files outside the canonical doc queue, not to in-file marker regions). A future `/gsd-docs-update` run would silently overwrite anything hand-written placed inside those four markers.

**Decision:** The new architectural-invariants content (Product Identity, Implementation Philosophy, Layer Boundaries, Decision Hierarchy, Definition of Done, References) goes **outside and below** all four sync-managed blocks (`project`, `stack`, `conventions`, `architecture`), in a new plain (non-marker) section. The `project-start`/`stack-start`/`conventions-start`/`architecture-start` blocks themselves are **removed entirely** from CLAUDE.md — they are GSD's default "echo the stack/conventions/architecture docs into CLAUDE.md" behavior, and this rewrite is intentionally rejecting that approach in favor of links. Removing the blocks (rather than emptying them) means a future `/gsd-docs-update` has nothing to resync into, since no markers remain for those four sections.

The `workflow-start`/`workflow-end` block (GSD Workflow Enforcement) is preserved verbatim — unrelated to this rewrite. The `profile-start`/`profile-end` block is preserved verbatim — GSD-managed by a different command, not in scope, and dropping it would just cause `/gsd-profile-user` to re-add the placeholder anyway.

## Task 1: Rewrite CLAUDE.md

Replace the full content of `/Users/mniedre/git/kir/CLAUDE.md` with:

1. Remove the four blocks: `<!-- GSD:project-start -->...<!-- GSD:project-end -->`, `<!-- GSD:stack-start -->...<!-- GSD:stack-end -->`, `<!-- GSD:conventions-start -->...<!-- GSD:conventions-end -->`, `<!-- GSD:architecture-start -->...<!-- GSD:architecture-end -->` in their entirety (markers and content).
2. In their place, insert a new unmarked section structured exactly as the todo specifies:
   - `## Product Identity` — one paragraph: KIR is a semantic compiler; Knowledge IR is the final product boundary; link to PROJECT.md's Product Boundary diagram rather than restating it.
   - `## Implementation Philosophy` — short bullet list: compiler architecture over pipelines, explicit Pydantic models over dicts, immutable IR, small independently-testable passes, no hidden side effects, no global state.
   - `## Layer Boundaries / What NOT to Build` — terse restatement of recurring violations an agent is likely to attempt (importing LLM/YAML SDKs into domain/, passes calling each other directly, building rendering/query/vector-search features). Link to REQUIREMENTS.md's Out of Scope table and research/ARCHITECTURE.md's Anti-Patterns section instead of re-deriving them.
   - `## Decision Hierarchy` — confirmed order, stated as not to be re-litigated: Correctness → Determinism → Canonical Knowledge IR → Extensibility → Performance → Developer Convenience.
   - `## Definition of Done` — deterministic, independently tested, reproducible, versioned, documented, compatible with incremental compilation.
   - `## References` — explicit links to `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/PROCESS.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/SUMMARY.md`, `.planning/research/FEATURES.md`, `.planning/research/STACK.md`. (Note: verify which of SUMMARY.md/FEATURES.md exist under `.planning/research/`; link only to files that exist, do not fabricate paths — if a referenced file doesn't exist, omit it from the list or note it's pending.)
3. Keep `<!-- GSD:skills-start -->...<!-- GSD:skills-end -->` as-is (unrelated to this rewrite's scope; it's a thin discovery block, not duplicated content).
4. Keep `<!-- GSD:workflow-start -->...<!-- GSD:workflow-end -->` exactly as-is, in its current position.
5. Keep `<!-- GSD:profile-start -->...<!-- GSD:profile-end -->` exactly as-is, in its current position (last section).
6. Section ordering in the rewritten file: Skills block, then the new architectural-invariants section, then Workflow Enforcement, then Profile — i.e. preserve the relative order of the blocks that remain, and insert the new section where `project`/`stack`/`conventions`/`architecture` used to be (top of file, before Skills).

Do not duplicate any Stack table, Architecture Principles list, or Architectural Decisions list — these stay exclusively in `.planning/PROJECT.md` and `.planning/research/STACK.md`; CLAUDE.md links to them.

**Verification:** Before writing, run `ls /Users/mniedre/git/kir/.planning/research/` to confirm which of SUMMARY.md/FEATURES.md/STACK.md/ARCHITECTURE.md actually exist, and only link to files confirmed present.

## Task 2: Verify

- Read back the rewritten `/Users/mniedre/git/kir/CLAUDE.md` and confirm:
  - No `GSD:project-*`, `GSD:stack-*`, `GSD:conventions-*`, `GSD:architecture-*` markers remain.
  - `GSD:skills-*`, `GSD:workflow-*`, `GSD:profile-*` blocks are byte-identical to the original (skills/workflow) or unchanged (profile).
  - All six target sections (Product Identity, Implementation Philosophy, Layer Boundaries, Decision Hierarchy, Definition of Done, References) are present.
  - No Stack table, Architecture Principles list, or Architectural Decisions list duplicated.
  - Every link target in References resolves to an existing file under `.planning/`.
- No test suite exists yet for this project (pre-Phase-1) — this is a documentation-only change, no code/test execution needed.

## Done condition

`/Users/mniedre/git/kir/CLAUDE.md` contains: Skills block (unchanged) → new architectural-invariants section (Product Identity, Implementation Philosophy, Layer Boundaries/What NOT to Build, Decision Hierarchy, Definition of Done, References) → Workflow Enforcement block (unchanged) → Profile block (unchanged). No Stack table, Architecture Principles, or Architectural Decisions duplicated anywhere in the file.
