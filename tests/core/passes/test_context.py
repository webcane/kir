"""Tests for CompilerContext (immutable DI container) and version constants."""

from __future__ import annotations

import dataclasses

import pytest

from kir.core.config.versions import compiler_version, prompt_version, schema_version
from kir.core.passes.context import CompilerContext


class _FakeLLM:
    model_id: str = "fake:v0"

    async def extract(self, *, sections: list, prompt: str) -> object:
        return None


class _FakeRepository:
    def save(self, artifact_id: str, artifact: object) -> None:
        pass

    def load(self, artifact_id: str) -> object:
        return None


class _FakeParser:
    def parse(self, text: str) -> list:
        return []


def _make_context() -> CompilerContext:
    return CompilerContext(
        llm=_FakeLLM(),
        repository=_FakeRepository(),
        parser=_FakeParser(),
        compiler_version="0.1.0",
        schema_version="1",
    )


def test_compiler_context_constructs_with_fake_ports() -> None:
    ctx = _make_context()
    assert ctx.compiler_version == "0.1.0"
    assert ctx.schema_version == "1"


def test_compiler_context_is_frozen() -> None:
    ctx = _make_context()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.compiler_version = "x"  # type: ignore[misc]


def test_compiler_context_fields_are_readable_not_required_to_compare_equal() -> None:
    fake_llm = _FakeLLM()
    fake_repo = _FakeRepository()
    fake_parser = _FakeParser()
    ctx = CompilerContext(
        llm=fake_llm,
        repository=fake_repo,
        parser=fake_parser,
        compiler_version="0.1.0",
        schema_version="1",
    )
    assert ctx.llm is fake_llm
    assert ctx.repository is fake_repo
    assert ctx.parser is fake_parser


def test_version_constants_are_importable_strings() -> None:
    assert isinstance(compiler_version, str)
    assert isinstance(schema_version, str)
    assert isinstance(prompt_version, str)
