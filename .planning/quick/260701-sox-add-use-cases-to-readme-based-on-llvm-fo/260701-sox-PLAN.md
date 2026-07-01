---
task: add-use-cases-to-readme-based-on-llvm-for-knowledge-analogy
date: 2026-07-01
type: quick
---

# Plan: Add use cases to README based on LLVM-for-knowledge analogy

## Context

Source todo: `.planning/todos/pending/2026-07-01-add-use-cases-to-readme-based-on-llvm-for-knowledge-analogy.md`

Current `README.md` is a single line:

```
# kir
KIR is a semantic compiler implementing a Knowledge ETL pipeline.
```

It communicates nothing about value proposition, audience, or what gets built on top of the Knowledge IR. This plan extends it with a "Use Cases" section and a "Who Kir Is For" section, per the todo spec.

**Product-boundary constraint (CLAUDE.md):** KIR compiles Markdown into a canonical Knowledge IR and stops there. It is never a UI, query engine, rendering layer, or vector-search system. All three use-case categories below MUST be framed as systems **built on top of** KIR's output artifact (the Knowledge IR) — never as things KIR itself does. Every bullet should read as "X consumes/uses the Knowledge IR to do Y," not "KIR does Y."

## Task 1: Rewrite README.md with Use Cases and Who Kir Is For sections

Files: `README.md`

Replace the full content of `README.md` with:

1. Keep the existing `# kir` H1 title and the one-line tagline (`KIR is a semantic compiler implementing a Knowledge ETL pipeline.`), optionally lightly polished, but preserve its meaning — do not remove the ETL-pipeline framing since it's the project's established self-description.

2. Add a `## Use Cases` section, framed with a short lead-in sentence invoking the LLVM analogy (LLVM is a compiler backend that many languages/tools build on top of; KIR is the analogous compiler backend for knowledge — its output, the Knowledge IR, is the substrate other tools consume). Structure as three subsections, each with 2-4 concise bullets naming concrete downstream system types and what they'd do with the Knowledge IR (not what KIR itself does):

   - `### Knowledge Development & Transformation Tools` — analysers that consume the Knowledge IR to surface concept/relation/taxonomy metrics, optimisers/linters that flag conflicts or redundant concepts recorded in the IR, code/schema generators that emit typed artifacts from the IR, visualizers that render the IR's concept graph.
   - `### AI & Agent Platforms` — a semantic layer that grounds LLM prompts/context in the IR's canonical concepts and relations, Q&A engines that query the IR instead of raw documents, agent decision cores that reason over the IR's taxonomy and provenance instead of unstructured text.
   - `### Ecosystem Components` — parsers/importers that produce additional raw sources for KIR to compile, IR stores/databases that persist and version compiled Knowledge IR artifacts, sync tools that keep a Knowledge IR up to date as source Markdown changes.

   Each bullet: one line, concise, README-appropriate (no full paragraphs). Explicitly avoid phrasing that implies KIR itself renders, queries, serves, or vector-searches — those verbs belong to the downstream tool being described, with KIR/the Knowledge IR as the input they consume.

3. Add a `## Who Kir Is For` section (short paragraph or 3-bullet list) stating:
   - Kir is NOT for end users — it does not produce a browsable or queryable product; it outputs raw, structured IR.
   - Kir IS for developers building their own knowledge platforms, tools, or agents on top of that IR.
   - Kir's job is to solve the "raw data" problem: compiling messy, inconsistent Markdown into a strict, machine-readable, versioned Knowledge IR that downstream tools can rely on without re-deriving structure themselves.

4. Do not add installation instructions, CLI usage, API docs, or roadmap/status content — those are out of scope for this todo; keep the file focused on positioning (tagline + Use Cases + Who Kir Is For).

**Verify:**
- `grep -c "^## " README.md` returns at least 3 (Use Cases, Who Kir Is For, plus any existing/kept sections).
- `grep -iE "query engine|rendering layer|vector search|serves queries" README.md | grep -iv "built on top\|downstream\|consumes\|on top of"` returns no matches where KIR is the subject performing that action (manual read-check — grep is a sanity aid, not a full gate, since phrasing varies).
- Read the final file back in full and confirm every Use Cases bullet names a downstream tool/system as the actor and the Knowledge IR as what it consumes — not KIR performing the action itself.

**Done:** `README.md` contains the original tagline, a `## Use Cases` section with the three required subsections (Knowledge Development & Transformation Tools, AI & Agent Platforms, Ecosystem Components) each with concrete bullets framed as consumers of the Knowledge IR, and a `## Who Kir Is For` section covering the NOT-for-end-users / FOR-developers / raw-data-problem framing. No content implies KIR itself is a UI, query engine, renderer, or vector-search system.
