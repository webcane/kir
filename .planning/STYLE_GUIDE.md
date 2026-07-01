# KIR Python Style Guide

## Core Principles

1. **Explicit is better than implicit** — code should show, not hide
2. **Honest imports** — if you use something, import it directly
3. **No architectural hiding tricks** — TYPE_CHECKING, __future__, and string annotations are design-smell indicators
4. **Deterministic semantics** — type hints should be checkable without running code

---

## Type Annotations

### Parameterized Generics (Python 3.9+)

✅ **Use built-in parameterized generics:**
```python
def extract(text: str) -> list[Concept]:
    pass

def group_relations(relations: list[Relation]) -> dict[str, list[Relation]]:
    pass
```

❌ **Don't use typing module equivalents:**
```python
from typing import List, Dict

def extract(text: str) -> List[Concept]:
    pass
```

### Union Types (Python 3.10+)

✅ **Use the `|` syntax for unions:**
```python
def get_concept(id: str) -> Concept | None:
    pass

def process(value: str | int | list[str]) -> None:
    pass
```

❌ **Don't use Optional or Union:**
```python
from typing import Optional, Union

def get_concept(id: str) -> Optional[Concept]:
    pass

def process(value: Union[str, int, List[str]]) -> None:
    pass
```

### ✅ DO: Import types directly

```python
from kir.core.domain.models.document import Section

def process(section: Section) -> None:
    pass
```

### ❌ DON'T: Use TYPE_CHECKING to avoid imports

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kir.core.domain.models.document import Section

def process(section: "Section") -> None:  # Wrong: hides that you use Section
    pass
```

**Why:** TYPE_CHECKING blocks signal architectural problems (circular dependencies). If a cycle exists, refactor instead of hiding it.

### ❌ DON'T: Use `from __future__ import annotations`

```python
from __future__ import annotations  # Remove this

def process(section: Section) -> None:  # Annotations are evaluated normally
    pass
```

**Why:** 
- No real forward references exist in KIR (only 1 quoted annotation across 28 files)
- `__future__` was a PEP 563 hack; Python 3.14 makes it obsolete
- Makes type evaluation implicit — you can't tell if `Section` is a forward ref or a direct type without reading the imports

---

## Import Rules

### ✅ Import order and grouping

```python
# 1. Standard library
from typing import Protocol

# 2. Third-party packages
from pydantic import BaseModel

# 3. Local (kir) packages
from kir.core.domain.models.document import Section
from kir.core.ports.parser_port import ParserPort
```

### ✅ Allowed import directions

| From | To | Allowed? | Example |
|------|-----|----------|---------|
| `domain/` | nothing | ✅ | No imports except stdlib/third-party |
| `passes/` | `domain/`, `ports/` | ✅ | Passes work with IR (domain) and Ports |
| `ports/` | nothing | ✅ | Protocols are standalone contracts |
| `adapters/` (future) | `domain/`, `ports/`, external SDKs | ✅ | Adapters implement ports using domain models |
| `tooling/` | all | ✅ | Tooling is the composition root |

### ❌ Forbidden import directions

```python
# ❌ Never import adapters from domain/passes
from kir.llm import LLMAdapter  # Domain must not know about concrete LLMs

# ❌ Never pass-to-pass direct imports
from kir.core.passes.extraction_pass import extract  # Passes register, don't call each other

# ❌ Never domain imports from adapters (delayed, OK; direct, NO)
# Adapters implement ports, not the reverse
```

---

## Pass Design

### ✅ Self-register via decorator

```python
@registry.register(depends_on=("concept_extraction",))
class RelationExtractionPass(Pass):
    async def __call__(self, ir: KnowledgeIR, ctx: CompilerContext) -> KnowledgeIR:
        # Process relations
        return ir
```

### ❌ DON'T: Call other passes directly

```python
# Wrong: direct pass-to-pass coupling
from kir.core.passes.concept_pass import ConceptExtractionPass
result = ConceptExtractionPass()(ir, ctx)
```

**Why:** Passes communicate through the registry and IR mutations. Direct imports create invisible dependencies.

---

## Model Design

### ✅ Use Pydantic frozen models for immutability

```python
from pydantic import BaseModel

class Concept(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    id: str
    label: str
    definition: str
```

### ✅ Explicit type hints (no `Any`)

```python
# Good:
def extract(text: str) -> list[Concept]:
    pass

# Bad:
def extract(text: Any) -> Any:
    pass
```

---

## Module Structure

### One concept per file

```
src/kir/core/domain/models/
├── concept.py       # Concept entity
├── relation.py      # Relation entity
├── document.py      # Document aggregate
└── diagnostic.py    # Diagnostic value object
```

### No `__all__` re-exports in `__init__.py`

```python
# src/kir/core/domain/__init__.py
# Empty or re-export only what's stable

# src/kir/core/domain/models/__init__.py
# Let imports be explicit: from kir.core.domain.models.concept import Concept
```

**Why:** Explicit imports reveal the dependency graph. Magic re-exports hide coupling.

---

## Error Handling

### Specific Exception Types

✅ **Always catch specific exceptions:**
```python
try:
    result = ir_processor.extract(text)
except ValueError as e:
    logger.error(f"Invalid input format: {e}")
    raise
except FileNotFoundError as e:
    logger.error(f"Config file not found: {e}")
    raise ConfigError(f"Missing configuration: {e}") from e
```

❌ **Never use bare except:**
```python
try:
    result = ir_processor.extract(text)
except:  # Wrong!
    logger.error("Error occurred")
    raise
```

### Error Messages

- Provide meaningful error messages for users
- Include context: what was being processed, why it failed
- Log the full exception with `logger.exception()` for debugging

---

## Logging

### Module-Level Logger

✅ **Configure logger at module level:**
```python
import logging

logger = logging.getLogger(__name__)

class ConceptExtractor(Pass):
    async def __call__(self, ir: KnowledgeIR, ctx: CompilerContext) -> KnowledgeIR:
        logger.info("Extracting concepts from document")
        try:
            # ... processing ...
            logger.debug(f"Extracted {len(ir.concepts)} concepts")
        except Exception as e:
            logger.error(f"Concept extraction failed: {e}")
            raise
```

### Logging Levels

- `DEBUG`: Detailed info for debugging (e.g., "Extracted 42 concepts")
- `INFO`: General operation info (e.g., "Starting extraction pass")
- `WARNING`: Potential issues (e.g., "Malformed reference, skipping")
- `ERROR`: Errors that don't stop operation
- `CRITICAL`: Critical errors that stop operation

---

## Documentation

### Docstrings for Public APIs

✅ **All public functions, classes, and modules must have docstrings:**
```python
class ConceptExtraction(Pass):
    """Extract concept definitions from document sections.
    
    Processes document sections and identifies distinct concepts with
    their definitions and relationships. Results are stored in the IR
    under the concepts ring.
    """
    
    async def __call__(self, ir: KnowledgeIR, ctx: CompilerContext) -> KnowledgeIR:
        """Execute concept extraction pass.
        
        Args:
            ir: The knowledge IR to process
            ctx: Compiler context with configuration and utilities
            
        Returns:
            Updated IR with extracted concepts
            
        Raises:
            ValueError: If input IR is invalid
            ProcessingError: If extraction fails
        """
        ...
```

### Comment Guidelines

- Comments should explain **why**, not what (code is self-documenting)
- Keep comments brief; update them when code changes
- Use English only
- Inline comments for non-obvious logic only

❌ **Bad comment:**
```python
# Increment counter
counter += 1
```

✅ **Good comment:**
```python
# Skip this concept if it was already extracted in the previous phase
# to avoid duplicate definitions in the final IR
if concept.id in existing_ids:
    continue
```

---

## Method Structure & Decomposition

Public methods should **orchestrate** workflow by delegating to small, single-purpose private methods.

### Rules:
- Public methods read like a high-level recipe
- Private methods (`_method_name`) handle one specific concern (validation, loading, transformation, persistence)
- Each private method should ideally be under 20 lines
- Avoid deeply nested conditionals; extract to private methods instead

### Anti-pattern vs Recommended:

❌ **Bad: Everything in one method**
```python
async def extract_concepts(self, ir: KnowledgeIR) -> KnowledgeIR:
    # Inline validation
    if not ir or not ir.sections:
        raise ValueError("No sections to process")
    
    # Inline extraction (imagine 50 more lines...)
    concepts = []
    for section in ir.sections:
        for line in section.text.split("\n"):
            if line.startswith("##"):
                concepts.append(Concept(label=line[2:].strip()))
    
    # Inline mutation
    ir.concepts.extend(concepts)
    return ir
```

✅ **Good: Public method orchestrates, private methods handle concerns**
```python
async def extract_concepts(self, ir: KnowledgeIR) -> KnowledgeIR:
    """Extract concepts from document sections."""
    self._validate_input(ir)
    concepts = await self._parse_sections(ir.sections)
    return self._attach_concepts(ir, concepts)

def _validate_input(self, ir: KnowledgeIR) -> None:
    if not ir or not ir.sections:
        raise ValueError("No sections to process")

async def _parse_sections(self, sections: list[Section]) -> list[Concept]:
    concepts = []
    for section in sections:
        concepts.extend(self._extract_from_section(section))
    return concepts

def _extract_from_section(self, section: Section) -> list[Concept]:
    concepts = []
    for line in section.text.split("\n"):
        if line.startswith("##"):
            concepts.append(Concept(label=line[2:].strip()))
    return concepts

def _attach_concepts(self, ir: KnowledgeIR, concepts: list[Concept]) -> KnowledgeIR:
    ir.concepts.extend(concepts)
    return ir
```

---

## Deprecated Methods

❌ **Don't use deprecated Python features:**
- `datetime.utcnow()` → use `datetime.now(timezone.utc)`
- `Optional[T]` → use `T | None`
- `List[T]`, `Dict[K, V]` → use `list[T]`, `dict[K, V]`
- `typing.Literal` (for fixed sets) → use `enum.StrEnum` or regular `Enum`

---

## Testing

### Pytest Markers

Use markers for test categorization:
```python
import pytest

@pytest.mark.unit
def test_concept_extraction():
    """Test concept entity creation."""
    concept = Concept(id="c1", label="Python", definition="A programming language")
    assert concept.label == "Python"

@pytest.mark.integration
async def test_extraction_pass_with_real_ir():
    """Test extraction pass against real IR."""
    pass_instance = ConceptExtractionPass()
    # ... full pipeline test ...
```

### Test Independence

- Each test should be independent
- Use fixtures for shared setup
- Avoid test interdependencies

---

## String Formatting

### ✅ Use f-strings

```python
# Good
name = "Python"
version = 3.14
message = f"Using {name} {version}"
logger.info(f"Processing document: {doc_id}")

# Also good for multi-line
error_msg = (
    f"Failed to extract concepts from {section.title}: "
    f"input was {len(text)} characters"
)
```

❌ **Don't use .format() or %**
```python
# Avoid
message = "Using {} {}".format(name, version)
message = "Using %s %s" % (name, version)
```

---

## Naming Conventions

- **Functions & Variables:** `snake_case` (e.g., `extract_concepts`, `relation_count`)
- **Classes:** `PascalCase` (e.g., `ConceptExtraction`, `KnowledgeIR`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_ITERATIONS`, `DEFAULT_TIMEOUT`)
- **Private members:** prefix with `_` (e.g., `_internal_state`, `_validate()`)
- **All code:** English only

---

## Async Code

### ✅ Use async/await for passes

```python
@registry.register()
class ExtractConceptsPass(Pass):
    async def __call__(self, ir: KnowledgeIR, ctx: CompilerContext) -> KnowledgeIR:
        logger.info("Extracting concepts")
        concepts = await self._extract_all(ir.sections)
        ir.concepts.extend(concepts)
        return ir
    
    async def _extract_all(self, sections: list[Section]) -> list[Concept]:
        # Processes asynchronously if needed
        return [self._extract_from_section(s) for s in sections]
```

### Always await async calls

```python
# Good
result = await llm_port.extract(sections)

# Bad
result = llm_port.extract(sections)  # Forgot await!
```

---

## Pydantic Models

### Immutability & Configuration

✅ **All domain models should be frozen (immutable):**
```python
from pydantic import BaseModel, ConfigDict

class Concept(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    id: str
    label: str
    definition: str
```

### Validation

✅ **Use Pydantic's built-in validation:**
```python
from pydantic import BaseModel, Field, field_validator

class Document(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    sections: list[Section] = Field(default_factory=list)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
```

---

## Import Guidelines

### Import Order

✅ **Group imports in this order:**

```python
# 1. Standard library
import logging
from typing import Protocol
from dataclasses import dataclass

# 2. Third-party packages
from pydantic import BaseModel, Field

# 3. Local imports (kir packages)
from kir.core.domain.models.concept import Concept
from kir.core.passes.registry import registry
from kir.core.ports.llm_port import LLMPort
```

### Absolute vs Relative Imports

✅ **Use absolute imports from kir package:**
```python
from kir.core.domain.models.document import Document
from kir.core.passes.base import Pass
```

✅ **Relative imports are OK for tightly coupled modules in the same package:**
```python
# In kir/core/passes/extraction.py:
from .registry import registry
from .base import Pass
```

❌ **Don't use relative imports across package boundaries:**
```python
# In kir/core/passes/extraction.py, don't do:
from ..domain.models import Concept  # Use absolute instead
```

### Remove Unused Imports

Use automated tools (ruff, isort) to detect and remove unused imports.

---

## Linting & CI Rules

### Required: type checking

```bash
mypy src/kir --strict
pyright src/kir --outputjson
```

### Required: no TYPE_CHECKING blocks

```bash
# In ruff.toml or flake8 config:
forbidden-patterns = [
    "if TYPE_CHECKING:",  # ← Error: refactor instead
]
```

### Required: no __future__ annotations

```bash
# Lint rule: flag 'from __future__ import annotations'
# Error message: "Use explicit imports; __future__ is not needed in KIR"
```

### Recommended: Code Formatting

```bash
# Format with ruff
ruff format src/ tests/

# Sort imports with ruff
ruff check --select I src/
```

### Recommended: import-linter (Phase 3+)

```yaml
# import_linter.cfg (when codebase exceeds 100 files)
forbidden_modules:
  - domain:
      - "adapters.*"
      - "compiler.*"
  - passes:
      - "llm.*"
      - "tooling.*"
```

---

## Migration Plan (If Implementing)

1. **Phase 1 (now):** Remove TYPE_CHECKING from `llm_port.py`, `parser_port.py`
2. **Phase 2:** Remove `from __future__ import annotations` from all files
3. **Phase 3:** Refactor `base.py` to eliminate the TYPE_CHECKING guard on CompilerContext
4. **Phase 4 (Python 3.14+):** No changes needed; the style will be the default

---

## Rationale

This style guide enforces **architectural honesty**: if you depend on something, import it directly. If that creates a cycle, the architecture is wrong — fix it instead of using TYPE_CHECKING or __future__ as a band-aid. This keeps the dependency graph clean and makes it impossible to accidentally hide coupling.
