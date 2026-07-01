---
created: 2026-07-01T11:56:44.373Z
title: Add use cases to README based on LLVM-for-knowledge analogy
area: docs
files:
  - README.md
---

## Problem

The README is currently a single-line placeholder: "KIR is a semantic compiler implementing a Knowledge ETL pipeline." It doesn't communicate Kir's value proposition, its target audience (tool builders, not end users), or the concrete systems that can be built on top of Knowledge IR. Newcomers have no way to understand what Kir enables without reading the full planning docs.

## Solution

Add a "Use Cases" section to README.md based on the LLVM-for-knowledge analogy, structured around:

1. **Knowledge Development & Transformation Tools** (analysers, optimisers, code generators, visualizers)
2. **AI & Agent Platforms** (semantic layer for LLMs, Q&A engines, agent decision cores)
3. **Ecosystem Components** (parsers/importers, IR stores, sync tools)

Also add a **"Who Kir Is For"** summary that clarifies:
- Kir is NOT for end users (it outputs raw IR)
- Kir IS for developers building their own knowledge platforms
- Kir solves the "raw data" problem by compiling chaos into strict, machine-readable IR

The text should draw directly from the use case analysis provided in the capture context, translated to concise, README-appropriate prose.
