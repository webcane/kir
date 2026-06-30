"""kir.llm — the only package in the codebase that imports pydantic_ai.

All external LLM SDK imports (pydantic_ai, openai, anthropic, etc.) are
confined to this package. Core/, compiler/, and tooling/ must never import
from pydantic_ai directly (Anti-Pattern 4, ARCHITECTURE.md).
"""
