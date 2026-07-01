"""Hand-crafted expected extraction outputs for the 10 golden fixture Markdown files (D-04).

Each constant is a DocumentExtractionOutput representing the expected result of running
the extraction pass on the corresponding doc_XX_*.md fixture file. These are used as
canned FakeLLMAdapter responses in golden-fixture replay tests.

Naming convention: DOC_01_EXPECTED through DOC_10_EXPECTED, one per fixture.
"""

from kir.llm.pydantic_ai_adapter import (
    DocumentExtractionOutput,
    ExtractedConceptDTO,
    ExtractedEntityDTO,
    ExtractedGlossaryTermDTO,
    ExtractedReferenceDTO,
)

# ---------------------------------------------------------------------------
# doc_01_rich.md — rich fixture with all four categories
# ---------------------------------------------------------------------------

DOC_01_EXPECTED = DocumentExtractionOutput(
    concepts=[
        ExtractedConceptDTO(
            name="event bus",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="subscription filter",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="at-least-once delivery",
            definition=None,
            category=None,
        ),
    ],
    glossary=[],
    entities=[
        ExtractedEntityDTO(name="Nexus Platform", kind="system"),
        ExtractedEntityDTO(name="AeroCorp Systems", kind="organization"),
    ],
    references=[
        ExtractedReferenceDTO(
            target="https://docs.zephyr-framework.io/deploy",
            context="Zephyr deployment guide",
        ),
        ExtractedReferenceDTO(
            target="https://github.com/aerocorp/zephyr-examples",
            context="Zephyr Example Repository",
        ),
    ],
)

# ---------------------------------------------------------------------------
# doc_02_glossary_heavy.md — primarily glossary, few concepts, no entities/references
# ---------------------------------------------------------------------------

DOC_02_EXPECTED = DocumentExtractionOutput(
    concepts=[],
    glossary=[
        ExtractedGlossaryTermDTO(
            term="event",
            definition="a discrete, immutable record of something that happened within the system, identified by a type string and a timestamp",
        ),
        ExtractedGlossaryTermDTO(
            term="handler",
            definition="a registered function or callable that processes events matching a declared subscription filter",
        ),
        ExtractedGlossaryTermDTO(
            term="manifest",
            definition="the YAML configuration file that describes which handlers are registered, their subscription filters, and their resource quotas for a given deployment context",
        ),
        ExtractedGlossaryTermDTO(
            term="subscription filter",
            definition="a declarative predicate evaluated against incoming event metadata",
        ),
        ExtractedGlossaryTermDTO(
            term="delivery guarantee",
            definition="the protocol commitment made by the event bus regarding how many times a handler will receive a given event",
        ),
    ],
    entities=[],
    references=[],
)

# ---------------------------------------------------------------------------
# doc_03_entity_reference.md — entity and reference heavy
# ---------------------------------------------------------------------------

DOC_03_EXPECTED = DocumentExtractionOutput(
    concepts=[],
    glossary=[],
    entities=[
        ExtractedEntityDTO(name="Stratos Engineering", kind="organization"),
        ExtractedEntityDTO(name="Open Infrastructure Foundation", kind="organization"),
        ExtractedEntityDTO(name="Lena Hoffmann", kind="person"),
        ExtractedEntityDTO(name="Marcus Dubois", kind="person"),
        ExtractedEntityDTO(name="Technical Steering Committee", kind="organization"),
        ExtractedEntityDTO(name="VoltaCo", kind="organization"),
    ],
    references=[
        ExtractedReferenceDTO(
            target="https://spec.zephyr-io.org/v3",
            context="canonical specification for the Zephyr event protocol",
        ),
        ExtractedReferenceDTO(
            target="https://community.zephyr-io.org",
            context="Zephyr Discourse forum",
        ),
        ExtractedReferenceDTO(
            target="https://github.com/open-infra/zephyr",
            context="reference implementation",
        ),
    ],
)

# ---------------------------------------------------------------------------
# doc_04_category_boundary.md — term "channel" is both concept and glossary;
# "channel" appears as glossary (explicitly defined); "Zephyr Registry" is entity;
# URLs are references
# ---------------------------------------------------------------------------

DOC_04_EXPECTED = DocumentExtractionOutput(
    concepts=[],
    glossary=[
        ExtractedGlossaryTermDTO(
            term="channel",
            definition="a named, typed conduit through which events of a specific schema flow between producers and consumers",
        ),
    ],
    entities=[
        ExtractedEntityDTO(name="Zephyr Registry", kind="system"),
        ExtractedEntityDTO(name="Open Infrastructure Foundation", kind="organization"),
    ],
    references=[
        ExtractedReferenceDTO(
            target="https://registry.zephyr-io.org",
            context="browse currently registered channels and their subscriber counts",
        ),
        ExtractedReferenceDTO(
            target="https://docs.zephyr-io.org/channels/naming",
            context="channel naming convention guide",
        ),
    ],
)

# ---------------------------------------------------------------------------
# doc_05_implicit_terminology.md — terms used repeatedly but never explicitly defined
# ---------------------------------------------------------------------------

DOC_05_EXPECTED = DocumentExtractionOutput(
    concepts=[
        ExtractedConceptDTO(
            name="backpressure",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="adaptive throttling",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="flow control",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="high-water mark",
            definition=None,
            category=None,
        ),
    ],
    glossary=[],
    entities=[],
    references=[],
)

# ---------------------------------------------------------------------------
# doc_06_implicit_terminology_2.md — schema evolution concepts, no explicit definitions
# ---------------------------------------------------------------------------

DOC_06_EXPECTED = DocumentExtractionOutput(
    concepts=[
        ExtractedConceptDTO(
            name="schema evolution",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="additive change",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="migration window",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="schema versioning",
            definition=None,
            category=None,
        ),
    ],
    glossary=[],
    entities=[],
    references=[],
)

# ---------------------------------------------------------------------------
# doc_07_genuinely_sparse.md — one concept, no glossary/entities/references
# ---------------------------------------------------------------------------

DOC_07_EXPECTED = DocumentExtractionOutput(
    concepts=[
        ExtractedConceptDTO(
            name="heartbeat",
            definition=None,
            category=None,
        ),
    ],
    glossary=[],
    entities=[],
    references=[],
)

# ---------------------------------------------------------------------------
# doc_08_world_knowledge_adjacent.md — "cache" redefined in project-specific way
# ---------------------------------------------------------------------------

DOC_08_EXPECTED = DocumentExtractionOutput(
    concepts=[
        ExtractedConceptDTO(
            name="cache invalidation",
            definition=None,
            category=None,
        ),
    ],
    glossary=[
        ExtractedGlossaryTermDTO(
            term="cache",
            definition="the per-handler store of event processing outcomes that allows a handler to skip reprocessing an event it has already seen",
        ),
    ],
    entities=[],
    references=[],
)

# ---------------------------------------------------------------------------
# doc_09_mixed_headings.md — multi-level headings (H1/H2/H3/H4), plugin concepts
# ---------------------------------------------------------------------------

DOC_09_EXPECTED = DocumentExtractionOutput(
    concepts=[
        ExtractedConceptDTO(
            name="plugin system",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="plugin lifecycle",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="conditional activation",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="plugin isolation",
            definition=None,
            category=None,
        ),
    ],
    glossary=[],
    entities=[],
    references=[],
)

# ---------------------------------------------------------------------------
# doc_10_rich_2.md — configuration/settings topic, second rich fixture
# ---------------------------------------------------------------------------

DOC_10_EXPECTED = DocumentExtractionOutput(
    concepts=[
        ExtractedConceptDTO(
            name="settings hierarchy",
            definition=None,
            category=None,
        ),
        ExtractedConceptDTO(
            name="configuration schema",
            definition=None,
            category=None,
        ),
    ],
    glossary=[
        ExtractedGlossaryTermDTO(
            term="environment profile",
            definition="a named set of configuration overrides that apply when Zephyr is deployed in a specific environment",
        ),
    ],
    entities=[
        ExtractedEntityDTO(name="ConfiguCore", kind="system"),
    ],
    references=[
        ExtractedReferenceDTO(
            target="https://docs.zephyr-framework.io/config/schema",
            context="canonical schema reference",
        ),
        ExtractedReferenceDTO(
            target="https://docs.zephyr-framework.io/upgrade",
            context="official upgrade documentation",
        ),
    ],
)
