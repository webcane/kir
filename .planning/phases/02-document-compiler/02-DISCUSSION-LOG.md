# Phase 2: Document Compiler - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-30
**Phase:** 2-Document Compiler
**Areas discussed:** Section split, Extraction shape, Extraction failure, Fixtures

---

## Section split

| Option | Description | Selected |
|--------|-------------|----------|
| Heading-based, any level | Every heading (H1-H6) starts a new section; content before the first heading becomes an untitled preamble section. | ✓ |
| Top-level headings only (H1/H2) | Only H1/H2 start new sections; deeper headings stay nested inside their parent section's content. | |
| Let research decide | Defer to ARCHITECTURE.md's pipeline sketch and the research phase. | |

**User's choice:** Heading-based, any level
**Notes:** Matches the `Parse → Section → Metadata` pipeline already sketched in ARCHITECTURE.md.

---

## Extraction shape

| Option | Description | Selected |
|--------|-------------|----------|
| One combined call | A single structured-output call returns concepts, glossary, entities, references together. | ✓ |
| Separate calls per category | Four independent LLMPort calls, each with its own prompt/schema. | |

**User's choice:** One combined call
**Notes:** Cheaper (1 LLM call/doc); categories are related enough that joint context likely improves accuracy.

---

## Extraction failure

| Option | Description | Selected |
|--------|-------------|----------|
| Diagnostic error, empty extraction, compile continues | Document IR still produced (empty concepts/glossary/entities/references), structured Diagnostic error recorded. | ✓ |
| Hard-fail the document compile | Whole document's compilation aborts if extraction fails. | |

**User's choice:** Diagnostic error, empty extraction, compile continues
**Notes:** Consistent with Phase 1's D-01 — pipeline always runs every pass to completion; halting is the caller's decision, not the pipeline's.

---

## Fixtures

| Option | Description | Selected |
|--------|-------------|----------|
| Small synthetic fixtures, hand-authored | Short, purpose-built Markdown docs with hand-crafted expected output. | ✓ |
| Real excerpts from project docs | Real Markdown from .planning/ as fixture input. | |
| Both | Synthetic for unit tests, real excerpts for integration. | |

**User's choice:** Small synthetic fixtures, hand-authored
**Notes:** Easy to reason about, fast, deterministic, sufficient for unit-level pass testing at this phase's scope.

---

## Claude's Discretion

- Markdown parser library choice (e.g. `mistune` vs `markdown-it-py`) — left to research.
- Exact prompt versioning scheme (semver, content hash, manual integer) — left to research/planning.
- Exact cache adapter implementation atop Phase 1's generic Cache Protocol (in-memory vs file-based) — left to research/planning.

## Deferred Ideas

None — discussion stayed within phase scope. Cross-document merging/alias resolution/knowledge-level taxonomy confirmed as existing Phase 3 scope, not pulled forward.
