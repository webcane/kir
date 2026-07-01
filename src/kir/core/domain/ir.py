"""FakeIR — minimal Pydantic frozen model used exclusively by Plan 03/04's
pass-mechanics tests. Deliberately decoupled from Document/Concept schema —
never used by real Document/Concept tests."""


from pydantic import BaseModel, ConfigDict

from kir.core.domain.models.diagnostic import Diagnostic


class FakeIR(BaseModel):
    """Minimal IR for pass-mechanics unit tests.

    Deliberately decoupled from Document/Concept schema; used only by
    test-infrastructure tests of pass mechanics (Plan 03/04).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: int = 0
    diagnostics: tuple[Diagnostic, ...] = ()
