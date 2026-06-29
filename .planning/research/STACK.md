# Stack Research

**Domain:** Deterministic, LLM-assisted semantic compiler (raw Markdown → versioned Knowledge IR), Python, hexagonal architecture, tactical DDD
**Researched:** 2026-06-29
**Confidence:** HIGH (core libraries verified against official docs/PyPI/changelogs same week); MEDIUM on a few fast-moving specifics called out inline

## Verdict on the User's Pre-Selected Stack

**Confirmed, with one timing caveat.** Python 3.13+, Pydantic v2, Typer, Ruff, Pytest, uv, and PydanticAI for LLM calls is the correct 2025/2026 stack for this exact problem shape (structured, validated, provider-agnostic LLM extraction feeding a versioned IR). Nothing here needs to be replaced.

The one real sharp edge: **PydanticAI shipped a major version bump (v2.0.0) on 2026-06-23 — six days before this research was run.** This is not a maturity problem (the project is "Production/Stable" per PyPI classifiers and has an explicit API-stability policy), but it is a *timing* problem: the public docs, blog posts, and Stack Overflow answers in your training/search corpus are mostly still v1-flavored, and a non-trivial set of APIs were renamed or restructured in v2 (see Pitfalls below). Pin deliberately and read the upgrade guide once, rather than copy-pasting v1-era snippets.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.13+ | Runtime | User's choice is sound. 3.13 brings the experimental free-threaded build and better error messages but neither matters much here; the real reason to require 3.13 is that it's the current "default" interpreter for new uv-managed projects and has the longest remaining support runway of versions already battle-tested by the ecosystem. All target libraries (Pydantic 2.13, PydanticAI 2.x, Typer 0.26.x, ruamel.yaml 0.19.x) declare explicit 3.13/3.14 support. HIGH confidence. |
| Pydantic | v2, **2.13.x** (latest 2.13.4, released 2026-05-06) | Domain models, IR schemas, validation, (de)serialization backbone | This is the right call categorically, not just incidentally: Pydantic v2's Rust core (`pydantic-core`) gives you fast validation on a 700-document corpus, `model_dump(mode="json")` / `model_validate` give you the JSON-compatible dict that YAML serialization libraries consume directly, and `Field`, `model_config`, discriminated unions, and computed/validated fields are exactly the toolkit needed to express a versioned IR schema (Concept, Relation, Taxonomy, Document, Conflict) with strict validation. HIGH confidence. |
| PydanticAI | **v2.0.0** (released 2026-06-23, first stable v2; v1 reached stability Sept 2025) | Provider-agnostic LLM-backed compiler passes (ExtractConcepts, ResolveAliases, BuildRelations, taxonomy classification) returning validated Pydantic models | This is the correct architectural choice for "Concept model is the contract, not whichever provider produced it." PydanticAI is built by the Pydantic team specifically to make `output_type=YourPydanticModel` work uniformly across OpenAI, Anthropic, Gemini, Groq, Mistral, etc., with automatic validation + typed retries (`ModelRetry`) on schema mismatch instead of hand-rolled JSON-repair glue. HIGH confidence on the architectural fit; MEDIUM confidence on exact API surface staying stable through your build window — see Pitfalls. |
| Typer | **0.26.x** (latest 0.26.8, 2026-06-26) | CLI framework (`kir compile`, future `doctor`/`stats`) | Typer's type-hint-driven command definition pairs naturally with Pydantic models for argument/option validation, and its `Annotated[...]`-based API is the modern idiom. As of 0.26.0 Typer vendors Click internally rather than depending on it as an external package — a recent change worth knowing about if you ever inspect installed dependencies or hit a Click-specific issue, since you can no longer `pip install click==X` to pin around it. Subcommand grouping (`Typer()` sub-apps per pass-group, e.g. `kir compile`, future `kir doctor`) is the standard pattern for compiler-style CLIs. HIGH confidence. |
| Ruff | latest (0.x, rolling) | Lint + format (replaces Black + isort + Flake8 + many plugins) | Single Rust binary, no separate formatter/linter split to maintain, and it is now the de facto standard for new Python projects in 2025/2026 — there is no serious competing tool. Use `select`, not bare `extend-select`, to keep your rule set explicit and auditable. Recommended starter set for this project: `E, F, I, UP, B, SIM, C4, RET, TID, TC, PTH` (errors/pyflakes, import sort, pyupgrade, bugbear, simplify, comprehensions, return, tidy-imports, type-checking-imports, pathlib). HIGH confidence. |
| pytest | latest (8.x) | Test runner | No competing standard exists for Python testing in this era. Pair with `pytest-asyncio` (PydanticAI's Agent.run is async-first) and `pytest-recording` / VCR cassettes for LLM-pass tests (see below). HIGH confidence. |
| uv | latest (0.x, rolling) | Dependency management, virtualenv, packaging, task running | Correct choice: uv is now the dominant Python project tool (Rust-based, 10-100x faster than pip/poetry for resolution), and `uv add`, `uv run`, `uv.lock` give reproducible, checksum-pinned dependency resolution — itself a nice parallel to the project's own checksum-based incremental-compile philosophy. Use `uv init --package` (not the default flat layout) to get the `src/` layout, which is the correct choice for a project that is conceptually a distributable library/CLI (not a throwaway script). HIGH confidence. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruamel.yaml | **0.19.x** (latest 0.19.1, 2026-01-02) | YAML (de)serialization of Pydantic models, one file per artifact | **Recommended over PyYAML.** PyYAML's `yaml.dump`/`yaml.safe_load` cannot round-trip comments, reorders keys, and emits Python-flavored YAML that is not always cleanly re-parseable across tags. ruamel.yaml is purpose-built for round-trip fidelity (preserves comments, key order, quoting style) — directly relevant to this project because conflict/provenance YAML artifacts are meant to be human-reviewed and possibly hand-edited in git, and you don't want diff noise from key reordering on every recompile. Use `ruamel.yaml.YAML(typ="safe")` (or `"rt"` if you want round-trip comment preservation) feeding from/to `model.model_dump(mode="json")` / `Model.model_validate(data)`. MEDIUM-HIGH confidence: functionally correct, but note the `pydantic_yaml` convenience wrapper below as a thinner option. |
| pydantic-yaml | latest (1.x) | Optional thin convenience layer (`to_yaml_file`, `parse_yaml_file_as`) over ruamel.yaml | Use only if you want one-line `to_yaml_file(model, path)` / `parse_yaml_file_as(Model, path)` helpers instead of writing your own `model_dump` → `ruamel.yaml.dump` glue. Functionally it *is* ruamel.yaml underneath — not a competing choice, a wrapper. Given this project needs custom dumping (one-file-per-artifact across `documents/`, `concepts/`, `relations/`, `taxonomy/`, `aliases/`, `metadata/`, plus deterministic key ordering for git-diff cleanliness), writing a small `kir.adapters.yaml_repository` module directly on ruamel.yaml is likely cleaner than fighting a generic wrapper's defaults. MEDIUM confidence — a "could go either way" pick, not a correction. |
| PyYAML | — | — | **Do not use as the primary YAML engine.** Fine as a transitive dependency of something else, but do not hand-roll serialization on top of it for artifacts meant to be git-diffed and human-reviewed — see "What NOT to Use." |
| pydantic-settings | latest (2.x) | CLI/app configuration (LLM provider selection, API keys, model names, paths) loaded from env vars / `.env` / CLI overrides | Standard pairing with Pydantic v2 for anything needing layered config (defaults → `.env` → environment → CLI flags). Use a `Settings(BaseSettings)` model for provider/model selection so "which LLM provider is active" is itself a validated, typed value, not a loose string threaded through the codebase. HIGH confidence — this is the de facto standard, no real competitor. |
| python-slugify | latest (8.x) | Deriving stable concept IDs from canonical names | This is the most mature, actively maintained slugify library (MIT licensed, handles Unicode transliteration via `text-unidecode`/`Unidecode`). Newer micro-libraries (`smart-slugify`, `sluggi`) exist but have far less track record — not worth the risk for something as load-bearing as concept-ID stability across compiler runs. HIGH confidence. |
| pytest-asyncio | latest | Run async tests | PydanticAI's `Agent.run()` is async; you will need this regardless of whether you also use VCR-style cassettes. MEDIUM-HIGH confidence (standard pairing, not project-specific). |
| pytest-recording (VCR.py-based) or PydanticAI's own `TestModel`/`FunctionModel` | latest | Deterministic testing of LLM-backed passes without live API calls | **Two complementary tools, not a choice between them.** `pydantic_ai.models.test.TestModel` / `FunctionModel` let you swap in a fake model via `Agent.override(model=...)` for fast, no-network unit tests of pass *plumbing* (does the pass call the agent correctly, handle `ModelRetry`, etc.). `pytest-recording` (VCR cassettes) lets you record one real provider call per golden fixture once, then replay deterministically in CI forever — this is the direct implementation of the project's stated requirement ("LLM-backed passes are tested against recorded/mocked LLM responses (golden fixtures)"). Use `TestModel` for pass-logic unit tests; use VCR cassettes for golden-fixture regression tests that need to look like real provider output. HIGH confidence — this combination is explicitly documented by the PydanticAI team. |
| Jinja2 | latest (3.x) | Prompt templating for LLM-backed passes, if prompts grow beyond simple f-strings | Only pull this in once prompts need composition/versioning beyond what an f-string or PydanticAI's built-in `instructions=` string supports. Not needed at MVP. LOW priority, MEDIUM confidence it'll be needed eventually given "prompt version" is already a tracked field in your IR. |
| networkx | latest (3.x) | Cycle detection for circular semantic relations (conflict pass) | Lightweight, pure-Python graph library; sufficient for the corpus scale (hundreds of documents, thousands of concepts). `nx.simple_cycles` or `nx.find_cycle` directly implements "circular semantic relations" detection without hand-rolling DFS cycle detection. MEDIUM confidence — reasonable default, not deeply researched against alternatives, because the scale here doesn't justify anything heavier (e.g., graph databases are explicitly out of scope per PROJECT.md). |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Ruff (lint + format) | Single tool replacing Black/isort/Flake8 | Configure via `[tool.ruff]` + `[tool.ruff.lint]` in `pyproject.toml`. Run both `ruff check` and `ruff format` in CI/pre-commit. |
| mypy or pyright (pick one) | Static type checking | Not in the user's explicit list but worth flagging: Pydantic v2 models are typed, and a hexagonal architecture with ports/adapters benefits enormously from a type checker catching adapter/port mismatches at lint time rather than runtime. **Recommend pyright** if using VS Code/Cursor (faster, better Pydantic plugin support); mypy if the team is more CLI/CI-centric. This is a gap in the user's stated stack worth raising explicitly during roadmap planning. MEDIUM confidence — genuinely a judgment call, not a correction. |
| pre-commit | Git hook runner | Wire up `ruff check --fix`, `ruff format`, and the type checker as pre-commit hooks so determinism-breaking formatting noise never lands in artifact diffs. |
| uv (also a dev tool) | `uv run pytest`, `uv run kir compile ...`, lockfile management | Already covered above as core; mentioned again here because `uv.lock` is itself part of your determinism story — pin it and commit it. |

## Installation

```bash
# Project init (src layout, packageable CLI)
uv init --package kir
cd kir
uv python pin 3.13

# Core
uv add "pydantic>=2.13" "pydantic-ai>=2.0" "typer>=0.26" "ruamel.yaml>=0.19" \
       "pydantic-settings>=2" "python-slugify>=8" "networkx>=3"

# Optional convenience YAML wrapper (evaluate; may skip in favor of a thin custom adapter)
uv add "pydantic-yaml>=1"

# Dev dependencies
uv add --dev "pytest>=8" "pytest-asyncio" "pytest-recording" "ruff" "pyright"
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|--------------|-------------|--------------------------|
| PydanticAI | Instructor (`python-instructor`) | If you specifically want the thinnest possible "wrap any client, get structured output" layer without an agent/tool-calling abstraction at all. Instructor is more minimal and has been around longer; PydanticAI is more opinionated/full-featured (agents, tools, retries, multi-step). Given this project's passes are single-shot structured extraction (not multi-turn tool-calling agents), Instructor is a legitimate lighter-weight alternative — but the user has already chosen PydanticAI and it is a sound choice; no reason to switch. |
| PydanticAI | LangChain / LangGraph | Only if you anticipate needing durable, resumable multi-step agent workflows with checkpointing across process restarts. The project's passes are stateless, single-purpose, and explicitly designed as independently-testable pipeline stages — LangGraph's graph-of-agents model is solving a different problem than "deterministic compiler pass." Avoid. |
| ruamel.yaml | PyYAML | Only for throwaway/internal config files where round-trip fidelity and diff cleanliness genuinely don't matter. Given every KIR artifact is meant to be git-diffed and possibly hand-reviewed, this condition does not hold anywhere in this project. |
| Typer | Click (raw) | If you needed something more low-level/unopinionated, or were stuck on Python <3.7 typing features. Not relevant here — Typer is built on top of Click's model and is the natural choice for a type-hint-first, Pydantic-adjacent codebase. |
| networkx | Hand-rolled DFS cycle detection | If you want zero extra dependencies for a single well-understood algorithm. Reasonable, but networkx is so lightweight and well-tested that pulling it in is lower risk than maintaining bespoke graph-traversal code for something as correctness-sensitive as conflict detection. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|--------------|
| PyYAML as primary serializer for artifact files | Drops comments, reorders dict keys non-deterministically relative to source order, and complicates clean git diffs on every recompile — directly works against the "git-friendly, human-readable" storage requirement in PROJECT.md. | ruamel.yaml (round-trip mode if preserving human edits matters; safe mode otherwise) |
| Pydantic v1 patterns/APIs (`.dict()`, `.json()`, `class Config:`, `parse_obj`) | These are deprecated/removed in Pydantic v2; a large fraction of "Pydantic" content on the web (StackOverflow, older blog posts, even some LLM training data) still teaches v1 idioms. Mixing v1 and v2 idioms in a versioned-schema codebase is a recipe for silent bugs. | `.model_dump()`, `.model_dump_json()`, `model_config = ConfigDict(...)`, `.model_validate()` |
| PydanticAI v1-era snippets copied verbatim (`result_type`, `.data`, `result_retries`) | These were renamed in the v2.0.0 release (2026-06-23): `result_type` → `output_type`, `FinalResult.data` → `.output`, `result_retries` → `output_retries`. Any tutorial/blog content predating mid-2026 will use the old names and will simply fail at runtime or type-check time. | `output_type=YourModel`, `result.output`, `Agent(output_retries=N)` — confirm against the current official docs/changelog before scaffolding the first pass. |
| Building your own JSON-repair/retry loop around raw provider SDKs | This is precisely the manual glue PydanticAI exists to eliminate — re-implementing it would be both wasted effort and a worse, less-tested version of what `output_type` + `ModelRetry` already does. | PydanticAI's built-in `output_type`, `ModelRetry`, and configurable `retries={'output': N}` |
| Monolithic dataclasses / TypedDicts for the IR instead of Pydantic models | You'd lose free validation, free JSON-schema generation (useful for PydanticAI's tool-calling output mode), and a consistent `model_dump`/`model_validate` boundary between domain core and YAML adapters — undermining the hexagonal-architecture goal of a clean, typed contract at the port boundary. | Pydantic v2 `BaseModel` subclasses for every IR type (Concept, Relation, Taxonomy, Document, Conflict) |
| Picking a YAML emission strategy without controlling key order/sort | Pydantic's default `model_dump()` preserves field-declaration order, which is good — but verify your chosen YAML dumper doesn't alphabetically re-sort keys (a common silent default in some YAML library configs), or every recompile produces gratuitous diff noise even when content is unchanged. | Explicitly set `sort_keys=False` / use ruamel.yaml's default declaration-order behavior; write a determinism test that recompiles unchanged input twice and diffs the YAML byte-for-byte. |

## Stack Patterns by Variant

**If pinning PydanticAI today (mid-2026):**
- Pin to `pydantic-ai>=2.0,<3` and read `https://pydantic.dev/docs/ai/project/changelog/` once before writing the first pass — v2 changed `end_strategy` default (`'early'` → `'graceful'`), introduced the "harness"/"capabilities" concept, and slimmed default provider extras (you'll likely need to explicitly add `pydantic-ai-slim[openai,anthropic]`-style extras rather than assuming everything is bundled). Because v2.0.0 is six days old at time of writing, expect a `2.0.x` or `2.1.x` patch cadence to settle rough edges; re-check before each phase of the roadmap that depends heavily on PydanticAI.

**If a given LLM-backed pass needs maximum cross-provider reliability:**
- Use PydanticAI's default **Tool Output** mode (`output_type=YourModel`, no wrapper) — it works via tool-calling across virtually every provider and is the most broadly compatible mode.
- Reserve **NativeOutput** for cases where you specifically want the model's native JSON-schema-constrained decoding (tighter guarantees, fewer supported providers) — useful for the more structurally strict passes (e.g., taxonomy classification against a fixed enum) if you find tool-calling output drifting.
- Avoid **PromptedOutput** except as a last-resort fallback for providers with neither tool-calling nor native structured output — it is explicitly the least reliable of the three modes.

**If artifacts need to remain hand-editable by a human reviewer (e.g., conflict resolution files):**
- Use ruamel.yaml's round-trip (`"rt"`) mode rather than `"safe"`, so any comments a human reviewer adds survive the next compiler pass that touches the same file (though note: compiler-written fields will still need explicit re-validation through the Pydantic model on load, regardless of dumper mode).

**If the corpus grows well past 700 documents in a later milestone:**
- Re-evaluate networkx for relation-cycle detection at that scale (it's pure Python and will start to show overhead in the tens-of-thousands-of-nodes range) — not a concern at current scale, flagged for future research only.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|------------------|-------|
| pydantic-ai 2.0.0 | pydantic >=2.x (latest 2.13.x) | PydanticAI is built directly on Pydantic v2's validation core; no separate pin needed beyond a reasonably recent Pydantic 2.x. |
| typer 0.26.x | Python >=3.10 | Vendors Click internally as of 0.26.0 — you cannot override the Click version via your own dependency pin; if a Click-specific bug ever surfaces, it must be fixed upstream in Typer, not worked around with a separate Click pin. |
| ruamel.yaml 0.19.x | Python >=3.9 | Be aware the maintainer has flagged a PyPI-driven possibility of a future package rename (PEP 625 normalization, `ruamel.yaml` → `ruamel_yaml`); not an immediate concern but worth a changelog check if a future `uv lock` ever fails to resolve the package name. |
| pydantic 2.13.x | Python 3.9–3.14 | No conflict with the project's 3.13+ floor; full forward compatibility through 3.14. |
| uv (any current) | pyproject.toml PEP 621 | Standard; no compatibility concerns specific to this stack. |

## Sources

- https://pydantic.dev/docs/ai/project/changelog/ — PydanticAI v1→v2 changelog, breaking changes, API stability policy (HIGH confidence, official, fetched same week as release)
- https://pydantic.dev/articles/pydantic-ai-v2 — official v2 announcement: harness/capabilities concept, "use v2 for new projects" guidance, 3-month breaking-change cadence within major versions (HIGH confidence, official)
- https://pydantic.dev/docs/ai/core-concepts/output/ — Tool Output / Native Output / Prompted Output modes, `ModelRetry`, output validators (HIGH confidence, official docs)
- https://pypi.org/project/pydantic-ai/ — version 2.1.0 confirmed live as of 2026-06-29 (released day-of-research), Python 3.10–3.14 support, Production/Stable classifier (HIGH confidence)
- https://pypi.org/project/pydantic/ — version 2.13.4 (2026-05-06), Python 3.9–3.14 (HIGH confidence)
- https://pypi.org/project/typer/ — version 0.26.8 (2026-06-26), vendored-Click change, Rich dependency confirmed (HIGH confidence)
- https://pypi.org/project/ruamel.yaml/ — version 0.19.1 (2026-01-02), Python 3.9–3.14, MIT license (HIGH confidence)
- https://ai.pydantic.dev/testing/ (and surrounding DeepWiki / pytest-recording docs) — `TestModel`/`FunctionModel` + VCR-cassette golden fixture pattern for testing LLM-backed passes without live calls (MEDIUM-HIGH confidence, official docs + corroborating community sources)
- WebSearch: "ruamel.yaml vs PyYAML round-trip comments" — comment/key-order preservation comparison, corroborated across multiple independent sources (MEDIUM-HIGH confidence)
- WebSearch: "python-slugify vs alternatives" — maturity/maintenance comparison for concept-ID slugification (MEDIUM confidence, no official benchmark, but consistent across sources)
- WebSearch: "Ruff recommended rule sets 2025/2026" — `select` vs `extend-select` guidance, standard rule-set composition (MEDIUM confidence, community consensus, not an official Astral "recommended defaults" doc)
- WebSearch: "uv src layout vs flat layout" — `uv init --package` recommendation for distributable CLI/library projects (MEDIUM confidence, community + official uv docs cross-referenced)

---
*Stack research for: Deterministic LLM-assisted semantic compiler (KIR)*
*Researched: 2026-06-29*
