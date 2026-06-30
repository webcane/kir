from typing import Protocol, get_type_hints

import pytest
from pydantic import ValidationError

from kir.core.domain.models.diagnostic import Diagnostic, Severity
from kir.core.ports.cache_port import CachePort
from kir.core.ports.llm_port import LLMPort
from kir.core.ports.parser_port import MarkdownParserPort
from kir.core.ports.repository_port import RepositoryPort


def test_diagnostic_constructs_with_defaults():
    diagnostic = Diagnostic(code="E001", severity=Severity.ERROR, message="bad thing")
    assert diagnostic.code == "E001"
    assert diagnostic.severity == Severity.ERROR
    assert diagnostic.message == "bad thing"
    assert diagnostic.location is None
    assert diagnostic.suggestion is None


def test_severity_has_exactly_three_members():
    assert {member.name for member in Severity} == {"ERROR", "WARNING", "INFO"}


def test_diagnostic_is_frozen_and_forbids_extra():
    diagnostic = Diagnostic(code="E001", severity=Severity.ERROR, message="bad thing")
    with pytest.raises(ValidationError):
        diagnostic.code = "E002"
    with pytest.raises(ValidationError):
        Diagnostic(
            code="E001", severity=Severity.ERROR, message="bad thing", extra_field="x"
        )


class _DiagnosticsHolder:
    """Local model used only to prove tuple-not-list storage behavior for an
    accumulating Diagnostic field, per Task 1 Test 6."""

    def __init__(self, diagnostics):
        self.diagnostics = tuple(diagnostics)


def test_diagnostic_accumulating_field_is_stored_as_tuple():
    from pydantic import BaseModel, ConfigDict

    class Holder(BaseModel):
        model_config = ConfigDict(frozen=True, extra="forbid")
        diagnostics: tuple[Diagnostic, ...] = ()

    d = Diagnostic(code="E001", severity=Severity.ERROR, message="bad thing")
    holder = Holder(diagnostics=[d])  # pass a list literal
    assert isinstance(holder.diagnostics, tuple)
    assert holder.diagnostics == (d,)


@pytest.mark.parametrize(
    "port_cls", [LLMPort, RepositoryPort, MarkdownParserPort, CachePort]
)
def test_ports_are_protocol_subclasses(port_cls):
    assert Protocol in port_cls.__mro__
    with pytest.raises(TypeError):
        port_cls()


def test_repository_port_has_save_and_load_signatures():
    hints_save = get_type_hints(RepositoryPort.save)
    hints_load = get_type_hints(RepositoryPort.load)
    assert "artifact_id" in hints_save
    assert "artifact" in hints_save
    assert "artifact_id" in hints_load


def test_cache_port_has_get_and_set_signatures():
    hints_get = get_type_hints(CachePort.get)
    hints_set = get_type_hints(CachePort.set)
    assert "key" in hints_get
    assert "key" in hints_set
    assert "value" in hints_set
