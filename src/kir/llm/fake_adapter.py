"""FakeLLMAdapter — production-tree fake satisfying LLMPort for DI and golden-fixture replay.

Lives in src/ (not tests/) so it is importable from the DocumentCompiler
composition root in non-CI environments and from any test that needs it.
Satisfies LLMPort structurally: exposes model_id: str and
async extract(*, sections, prompt) -> DocumentExtractionOutput.
"""

from __future__ import annotations

from kir.llm.pydantic_ai_adapter import DocumentExtractionOutput


class FakeLLMAdapter:
    """Canned-response LLM adapter for pass plumbing tests and golden-fixture replay.

    Configured with a fixed DocumentExtractionOutput (or an empty one by default).
    Tracks call_count so tests can assert the adapter was (or was not) called.
    """

    model_id: str = "fake:v0"

    def __init__(self, output: DocumentExtractionOutput | None = None) -> None:
        self._output: DocumentExtractionOutput = output or DocumentExtractionOutput()
        self._call_count: int = 0

    async def extract(
        self,
        *,
        sections: object,
        prompt: str,
    ) -> DocumentExtractionOutput:
        """Return the configured canned output and increment call_count."""
        self._call_count += 1
        return self._output

    @property
    def call_count(self) -> int:
        """Number of times extract() has been called on this instance."""
        return self._call_count
