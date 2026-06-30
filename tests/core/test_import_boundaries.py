"""CORE-01: the domain layer must depend on nothing — no LLM SDK, no
filesystem library, no YAML library. This is an automated AST-based audit,
not a manual code review.
"""

import ast
from pathlib import Path

FORBIDDEN_MODULES = {
    "yaml",
    "ruamel",
    "openai",
    "anthropic",
    "pydantic_ai",
    "pathlib",
    "os.path",
    "requests",
    "httpx",
    "markdown_it",
    "mistune",
}


def _imported_modules(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text())
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def test_domain_has_no_forbidden_imports():
    domain_files = Path("src/kir/core/domain").rglob("*.py")
    violations = {}
    for f in domain_files:
        found = _imported_modules(f) & FORBIDDEN_MODULES
        if found:
            violations[str(f)] = found
    assert not violations, f"Forbidden imports in domain layer: {violations}"


def test_pydantic_is_not_forbidden():
    # pydantic is the one allowed third-party import in domain code per
    # CLAUDE.md's "Explicit Pydantic models over dicts".
    assert "pydantic" not in FORBIDDEN_MODULES
