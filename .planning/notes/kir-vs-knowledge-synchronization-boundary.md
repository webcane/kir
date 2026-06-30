---
title: Boundary — KIR vs Knowledge Synchronization (reverse-sync of manual wiki edits)
date: 2026-06-30
context: exploration session (/gsd-explore)
---

## Question

How is "reverse sync" supposed to work when a user manually edits the *generated wiki files*
(Obsidian/Logseq/Notion/etc.) downstream of KIR?

## Answer

There is no reverse-sync mechanism inside KIR, and there shouldn't be one — by design (PROJECT.md,
"Product Boundary", line 40: `Synchronization / Rendering Agent` is explicitly downstream and out
of scope).

Two distinct concerns get conflated by the word "sync":

1. **Inside KIR's boundary:** if a human edits the *source* `.md` corpus that KIR compiles, that's
   just a normal (incremental) recompilation input. No special-casing needed — KIR doesn't need to
   know an edit "came from a wiki workflow." This is true only if the wiki tool's storage *is* the
   same source files KIR ingests.

2. **Outside KIR's boundary (the "Knowledge Synchronization" component, referenced in
   https://gist.github.com/webcane/ffd9da2eda7ad626284837eb48267860):** this is a one-way
   projection, Knowledge IR → wiki pages (Obsidian/Logseq/MkDocs/search index/etc.). It performs
   **no semantic reasoning** — all semantic decisions happen upstream in the Knowledge Compiler.
   Its job when re-generating wiki pages from an updated IR is to **not destroy manual edits/annotations**
   already present in the wiki (analogous to a code generator preserving hand-edited regions). That's
   a downstream-consumer responsibility, never built or depended on by KIR.

So: "reverse sync" in the sense of *manual wiki edits flowing back into the Knowledge IR* is not a
thing KIR does or needs to support. The wiki is a *view* of the knowledge, not the knowledge source.
If wiki edits should influence the canonical model, the human edits the source Markdown corpus
instead, and KIR recompiles normally.

## Why this matters

This is a recurring point of confusion (came up unprompted in this session) because the word "sync"
is overloaded — it could mean "merge knowledge changes into the model" (KIR's job, via recompilation)
or "merge manual edits into generated output" (Sync Agent's job, non-semantic, never built here).
Future contributors/agents touching anything resembling sync, reverse-sync, or wiki-write paths
should check this boundary before treating it as in-scope.

## Naming follow-up

"Synchronization / Rendering Agent" (PROJECT.md, Product Boundary diagram, and Architecture
Principle #8) is misleading — "synchronization" implies bidirectionality, but the component is a
one-way IR→view projection that reconciles desired state (Knowledge IR) with existing state (wiki +
manual edits) without losing human input. A better name surfaced in this session: **Knowledge
Reconciler** (cf. reconciliation pattern from React/Kubernetes — desired-state vs actual-state
reconciliation, which is exactly this component's behavior).

PROJECT.md was *not* updated with this rename — only captured here as a decision worth revisiting
if/when this component is actually scoped or named elsewhere (it's out of scope for KIR itself, so
there's no urgency to rename it in this repo's docs).
