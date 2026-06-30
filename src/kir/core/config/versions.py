"""Module-level version constants threaded through CompilerContext.

`prompt_version` is declared now even though no prompt exists until
Phase 2 — this is the natural home for it per ARCHITECTURE.md's
structure, and pre-declaring it avoids a later edit to this file.
"""

from __future__ import annotations

compiler_version = "0.1.0"
schema_version = "1"
prompt_version = "1"
