"""Structured diagnostics accumulated by compiler passes (CORE-06)."""


from enum import Enum

from pydantic import BaseModel, ConfigDict


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Diagnostic(BaseModel):
    """A single structured diagnostic emitted by a pass.

    Diagnostics are accumulated, never used to halt the pipeline mid-run
    (D-01) — passes record problems here instead of raising/printing.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    severity: Severity
    message: str
    location: str | None = None
    suggestion: str | None = None
