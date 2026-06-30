"""FakeIR — minimal Pydantic frozen model used exclusively by Plan 03/04's
pass-mechanics tests. Deliberately decoupled from Document/Concept schema —
never used by real Document/Concept tests."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from kir.core.domain.models.diagnostic import Diagnostic


class FakeIR(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    value: int = 0
    diagnostics: tuple[Diagnostic, ...] = ()
