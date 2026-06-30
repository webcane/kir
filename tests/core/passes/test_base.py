"""Tests for the Pass Protocol contract."""

from __future__ import annotations

import pytest

from kir.core.passes.base import Pass


def test_pass_is_a_protocol_and_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        Pass()  # type: ignore[misc]
