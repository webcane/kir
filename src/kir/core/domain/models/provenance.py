"""Provenance value objects — where a piece of knowledge came from.

Canonical home for `SourceRef`. Do not redefine `SourceRef` elsewhere;
import it from this module.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SourceRef(BaseModel):
    """A pointer back to the raw source a piece of knowledge was derived from."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: str
    section: str | None = None
