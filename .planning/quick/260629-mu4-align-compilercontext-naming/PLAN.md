---
quick_id: 260629-mu4
date: 2026-06-29
---

Align CompilerContext naming between ARCHITECTURE.md and REQUIREMENTS.md.

REQUIREMENTS.md (CORE-05) names the shared pass context `CompilerContext`. ARCHITECTURE.md used `PassContext` everywhere instead. Replace all occurrences of `PassContext` with `CompilerContext` in `.planning/research/ARCHITECTURE.md` (class name, code examples, prose) so the two documents agree before Phase 1 implementation begins.
