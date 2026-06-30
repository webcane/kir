"""CompilerContext — the explicit, immutable dependency-injection container.

Carries the three domain-owned ports (LLM, repository, parser) plus
run metadata (compiler/schema version) that every pass call receives.
Never a module-level global — always constructed explicitly by the
caller and threaded through the pipeline (CLAUDE.md "No global state").

A frozen dataclass, not a Pydantic BaseModel: the Protocol-typed port
fields are not natively Pydantic-validatable without
`arbitrary_types_allowed=True`, and CompilerContext is never
serialized — see 01-PATTERNS.md for the explicit rationale.
"""

from __future__ import annotations

from dataclasses import dataclass

from kir.core.ports.llm_port import LLMPort
from kir.core.ports.parser_port import MarkdownParserPort
from kir.core.ports.repository_port import RepositoryPort


@dataclass(frozen=True, slots=True)
class CompilerContext:
    llm: LLMPort
    repository: RepositoryPort
    parser: MarkdownParserPort
    compiler_version: str
    schema_version: str
