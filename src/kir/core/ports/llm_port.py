"""LLMPort — domain-owned port for LLM-backed semantic analysis.

The concrete LLM library (e.g. PydanticAI) is an interchangeable adapter
detail behind this Protocol — never a domain dependency.
"""

from __future__ import annotations

from typing import Protocol


class LLMPort(Protocol):
    def extract(self, text: str) -> object: ...
