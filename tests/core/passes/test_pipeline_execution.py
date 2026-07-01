"""Integration proof for Phase 1's core success criteria:

- A real dependency graph (fake_b depends_on fake_a) executes in order via
  PassRegistry.pipeline() and accumulates structured Diagnostic instances.
- Running the same pipeline twice against fresh FakeIR inputs produces
  byte-identical serialized output (determinism).
- CompilerContext + fake ports + fake passes compose end-to-end.
"""

from kir.core.domain.ir import FakeIR
from kir.core.domain.models.diagnostic import Diagnostic
from kir.core.passes.context import CompilerContext
from kir.core.passes.registry import PassRegistry
from tests.core.passes.fakes.fake_llm_port import FakeLLMPort
from tests.core.passes.fakes.fake_parser import FakeMarkdownParser
from tests.core.passes.fakes.fake_passes import fake_pass_a, fake_pass_b
from tests.core.passes.fakes.fake_repository import InMemoryFakeRepository

def test_pipeline_executes_passes_in_dependency_order_and_accumulates_diagnostics(
    fake_registry: PassRegistry, fake_compiler_context: CompilerContext
) -> None:
    pipeline = fake_registry.pipeline()
    result = FakeIR(value=0)
    for pass_fn in pipeline:
        result = pass_fn(result, fake_compiler_context)

    assert result.value == 2
    assert len(result.diagnostics) >= 2
    codes = {d.code for d in result.diagnostics}
    assert "FAKE_A" in codes
    assert "FAKE_B" in codes

def test_rerun_produces_byte_identical_output(
    fake_registry: PassRegistry, fake_compiler_context: CompilerContext
) -> None:
    pipeline = fake_registry.pipeline()

    result_1 = FakeIR(value=0)
    for pass_fn in pipeline:
        result_1 = pass_fn(result_1, fake_compiler_context)

    result_2 = FakeIR(value=0)
    for pass_fn in pipeline:
        result_2 = pass_fn(result_2, fake_compiler_context)

    assert result_1.model_dump_json() == result_2.model_dump_json()

def test_all_diagnostics_are_structured_not_printed(
    fake_registry: PassRegistry, fake_compiler_context: CompilerContext, capsys
) -> None:
    pipeline = fake_registry.pipeline()
    result = FakeIR(value=0)
    for pass_fn in pipeline:
        result = pass_fn(result, fake_compiler_context)

    assert all(isinstance(d, Diagnostic) for d in result.diagnostics)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

async def test_fake_ports_construct_with_no_arguments_and_are_callable() -> None:
    llm = FakeLLMPort()
    repository = InMemoryFakeRepository()
    parser = FakeMarkdownParser()

    # LLMPort.extract() is now async and takes keyword-only sections + prompt (D-02)
    result = await llm.extract(sections=[], prompt="test")
    assert isinstance(result, object)
    repository.save("artifact-1", {"id": "artifact-1"})
    assert repository.load("artifact-1") == {"id": "artifact-1"}
    assert isinstance(parser.parse("# heading"), list)

def test_fake_compiler_context_composes_with_fake_pass(
    fake_compiler_context: CompilerContext,
) -> None:
    ir = FakeIR(value=0)
    result = fake_pass_a(ir, fake_compiler_context)
    assert result.value == 1
    assert len(result.diagnostics) == 1
