## Product Identity

KIR (Knowledge Intermediate Representation) is a deterministic semantic compiler: it takes raw Markdown corpora as source and compiles them into a canonical Knowledge IR — never a UI, a query engine, or a rendering layer. The Knowledge IR is the final product boundary; nothing downstream of compilation (rendering, querying, vector search, serving) is this project's concern. See `.planning/PROJECT.md` ("Product Boundary") for the full diagram of what is in/out of the compiler's boundary.

## Implementation Philosophy

- Compiler architecture over pipelines — discrete, registry-driven passes, not an ad-hoc script chain
- Explicit Pydantic models over dicts — every IR type (Concept, Relation, Taxonomy, Document, Conflict) is a typed, validated contract
- Immutable IR — compiled artifacts are not mutated in place; recompilation produces new artifacts
- Small, independently-testable passes — each pass is unit-testable in isolation, without standing up the full pipeline
- No hidden side effects — passes declare their inputs/outputs explicitly; no pass silently depends on another's internal state
- No global state — configuration and provider selection are threaded explicitly (e.g. via typed `Settings`), never read from ambient globals

## Layer Boundaries / What NOT to Build

Recurring violations an agent is likely to attempt — do not do these:

- Importing LLM or YAML SDKs directly into `domain/` — adapters are interchangeable details behind a domain-owned port (e.g. `LLMPort`), never a domain dependency
- Passes reaching around the registry to call each other directly — passes communicate only through the registry/pipeline, never via direct imports of one another
- Building rendering, query, or vector-search features — these are explicitly out of scope; this project ends at the Knowledge IR

See `.planning/REQUIREMENTS.md` ("Out of Scope") and `.planning/research/ARCHITECTURE.md` ("Anti-Patterns") for the full, authoritative lists — do not re-derive or duplicate them here.

## Decision Hierarchy

When trade-offs conflict, resolve in this order (confirmed; not to be re-litigated):

Correctness → Determinism → Canonical Knowledge IR → Extensibility → Performance → Developer Convenience

## Definition of Done

A pass or feature is done when it is: deterministic, independently tested, reproducible, versioned, documented, and compatible with incremental compilation.

## References

- `.planning/PROJECT.md` — product definition, architecture principles, product boundary, milestones, architectural decisions
- `.planning/REQUIREMENTS.md` — full requirement set, traceability, out-of-scope list
- `.planning/PROCESS.md` — project process
- `.planning/research/ARCHITECTURE.md` — architecture research, anti-patterns
- `.planning/research/SUMMARY.md` — research summary
- `.planning/research/FEATURES.md` — feature research
- `.planning/research/STACK.md` — technology stack research and rationale

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
