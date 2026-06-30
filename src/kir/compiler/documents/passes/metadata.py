"""MetadataPass — populates id, title, checksum, and language on the Document IR.

Computes a SHA-256 checksum of the raw source, derives the title from the first
section with a non-empty heading, slugifies the title to produce the document id,
and sets language='en'. Depends on parse and section so sections are normalised
before title derivation.
"""

from __future__ import annotations

import hashlib
import re

from kir.core.domain.models.document import Document
from kir.core.domain.value_objects import Checksum
from kir.core.passes.context import CompilerContext

from kir.compiler.documents.passes import register_pass


def _slugify(title: str) -> str:
    """Convert a title string to a URL-safe slug.

    Lowercases, replaces spaces with hyphens, removes all characters that are
    not alphanumeric or hyphens, and collapses consecutive hyphens.
    """
    slug = title.lower()
    slug = slug.replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    return slug or "untitled"


@register_pass("metadata", depends_on=("parse", "section"))
def metadata_pass(ir: Document, ctx: CompilerContext) -> Document:
    """Populate id, title, checksum, and language on the Document IR.

    - checksum: SHA-256 hex digest of ir.source (encoded as UTF-8).
    - title: heading of the first section with a non-empty heading, or 'Untitled'.
    - id: URL-safe slug of title (lowercase, spaces → hyphens, strip non-alnum).
    - language: always 'en' for this phase (multi-language detection is out of scope).

    Source stays unchanged (already in ir.source from initial Document construction).
    Returns an immutable copy of ir with the four fields populated.
    """
    checksum_hex = hashlib.sha256(ir.source.encode()).hexdigest()

    # Derive title from the first section with a non-empty heading.
    title = "Untitled"
    for section in ir.sections:
        if section.heading:
            title = section.heading
            break

    doc_id = _slugify(title)

    return ir.model_copy(
        update={
            "checksum": Checksum(algorithm="sha256", value=checksum_hex),
            "title": title,
            "id": doc_id,
            "language": "en",
        }
    )
