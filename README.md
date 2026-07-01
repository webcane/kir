# kir

KIR is a semantic compiler implementing a Knowledge ETL pipeline: it compiles raw Markdown corpora into a canonical Knowledge IR.

## Use Cases

LLVM is a compiler backend that many languages and tools build on top of, without ever needing to reimplement code generation or optimization themselves. KIR is the analogous compiler backend for knowledge: its output, the Knowledge IR, is the substrate other tools consume, so they never have to re-derive structure from raw Markdown themselves.

### Knowledge Development & Transformation Tools

- Analysers that consume the Knowledge IR to surface concept, relation, and taxonomy metrics
- Optimisers and linters that flag conflicts or redundant concepts recorded in the IR
- Code and schema generators that emit typed artifacts from the IR
- Visualizers that render the IR's concept graph

### AI & Agent Platforms

- A semantic layer that grounds LLM prompts and context in the IR's canonical concepts and relations
- Q&A engines that query the IR instead of raw documents
- Agent decision cores that reason over the IR's taxonomy and provenance instead of unstructured text

### Ecosystem Components

- Parsers and importers that produce additional raw sources for KIR to compile
- IR stores and databases that persist and version compiled Knowledge IR artifacts
- Sync tools that keep a Knowledge IR up to date as source Markdown changes

## Who Kir Is For

- Kir is **not** for end users — it does not produce a browsable or queryable product; it outputs raw, structured IR.
- Kir **is** for developers building their own knowledge platforms, tools, or agents on top of that IR.
- Kir's job is to solve the "raw data" problem: compiling messy, inconsistent Markdown into a strict, machine-readable, versioned Knowledge IR that downstream tools can rely on without re-deriving structure themselves.
