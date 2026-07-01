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

from dataclasses import dataclass

from kir.core.ports.llm_cache_port import LLMCachePort
from kir.core.ports.llm_port import LLMPort
from kir.core.ports.parser_port import MarkdownParserPort
from kir.core.ports.prompt_registry_port import PromptRegistryPort
from kir.core.ports.repository_port import RepositoryPort


@dataclass(frozen=True, slots=True)
class CompilerContext:
    """Immutable dependency-injection container for compiler passes.

    Provides access to domain-owned ports (LLM, repository, parser) and
    run metadata (versions). Never a module-level global; explicitly threaded
    through the pipeline. Frozen dataclass (not Pydantic) to avoid validation
    overhead for Protocol-typed port fields.
    """

    llm: LLMPort
    repository: RepositoryPort
    parser: MarkdownParserPort
    compiler_version: str
    schema_version: str
    # Phase 2 additions (all optional with defaults for backward compatibility):
    prompt_version: str = ""
    llm_cache: LLMCachePort | None = None
    prompts: PromptRegistryPort | None = None
