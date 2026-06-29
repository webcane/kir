---
title: CLAUDE.md redesign rationale
date: 2026-06-29
context: Exploration session triggered by detailed user feedback on what CLAUDE.md should contain for KIR
---

## Decision

CLAUDE.md should stop being a stack/conventions dump and become a thin decision-making layer on top of the existing `.planning/` documents — answering "how should the agent think when implementing KIR," not "what is KIR" (PROJECT.md), "what to do now" (ROADMAP.md), or "what must be built" (REQUIREMENTS.md).

## Division of responsibility (explicitly confirmed)

- **PROJECT.md** stays the source of truth for Architecture Principles (the 10-item list) and Architectural Decisions. CLAUDE.md does not duplicate these — it links to them.
- **CLAUDE.md** holds only:
  - Product Identity (one-line "never build X" framing)
  - Implementation Philosophy (compiler-over-pipeline, explicit-over-convenient style preferences)
  - Layer Boundaries / What NOT to build (recurring anti-pattern guardrails, e.g. rendering, vector search, query APIs — already enumerated in REQUIREMENTS.md's Out of Scope table, but worth a terse restatement here since this is what an agent is most likely to accidentally violate)
  - Decision Hierarchy (confirmed order: Correctness → Determinism → Canonical Knowledge IR → Extensibility → Performance → Developer Convenience)
  - Definition of Done
  - Explicit links to `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/PROCESS.md`, and `.planning/research/{ARCHITECTURE,SUMMARY,FEATURES,STACK}.md` as the canonical detail sources

## Why this matters

The user's framing: a good CLAUDE.md for a project like KIR should be evaluated by one criterion — does it help make the same architectural decisions the same way a month from now? Stack/coding-convention content (Python/Typer/uv version pins) belongs in research/STACK.md or an ADR, not CLAUDE.md, because it changes; the decision-making philosophy and invariants should survive a full reimplementation in a different language.

## Follow-up

See [[rewrite-claude-md-architectural-invariants]] todo for the concrete rewrite.
