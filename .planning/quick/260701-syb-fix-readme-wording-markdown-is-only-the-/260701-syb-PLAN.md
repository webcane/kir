---
task: 260701-syb-fix-readme-wording-markdown-is-only-the-
type: quick
autonomous: true
files_modified:
  - README.md
must_haves:
  truths:
    - "README no longer implies KIR only ingests Markdown; it conveys Markdown as the first supported source format, with more planned, without claiming multi-format support exists today"
    - "README no longer uses the word 'corpora' or 'corpus'; replaced with a common term (e.g. 'documents' or 'sources')"
    - "Product-boundary framing (KIR compiles to Knowledge IR only, no UI/query/render/vector-search claims) is unchanged"
  artifacts:
    - path: "README.md"
      provides: "Corrected tagline and Use Cases lead-in wording"
  key_links: []
---

<objective>
Fix two wording issues in README.md raised by user feedback (in Russian, translated):

1. The README's tagline and "Use Cases" lead-in currently imply KIR only ingests Markdown files. KIR's actual scope (per `.planning/PROJECT.md` line 5: "heterogeneous raw sources (starting with Markdown)") is that Markdown is the *first* supported source format, with more planned — not the only one. Fix the wording to convey this without overstating current capability (do not claim multi-format support exists today; `.planning/REQUIREMENTS.md` explicitly defers multi-format parsing).
2. The word "corpora" is uncommon/hard to understand for a general README audience. Replace it with a common term ("documents" or "sources", used consistently with surrounding sentence context) everywhere it appears in README.md.

Purpose: Ship-quality README wording — accurate framing of current vs. planned capability, and plain language accessible to a general audience.
Output: Updated README.md with both issues fixed in the tagline, Use Cases lead-in, and any other occurrence.
</objective>

<execution_context>
@$HOME/.claude/gsd-core/workflows/execute-plan.md
@$HOME/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@README.md
@.planning/PROJECT.md
@.planning/REQUIREMENTS.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix markdown-only framing and replace "corpora" in README.md</name>
  <files>README.md</files>
  <action>
    Edit README.md to fix both wording issues. Do not restructure sections, add new sections, or change any other content — this is a wording-only fix.

    1. Tagline (line 3): Replace "it compiles raw Markdown corpora into a canonical Knowledge IR" with wording that (a) drops "corpora" for a common word, and (b) frames Markdown as the first/current supported source format rather than the only one — mirror the established project framing in `.planning/PROJECT.md` line 5 ("heterogeneous raw sources (starting with Markdown)"). Example target phrasing: "KIR is a semantic compiler implementing a Knowledge ETL pipeline: it compiles raw sources — starting with Markdown — into a canonical Knowledge IR." Do not claim multi-format ingestion is implemented today; "starting with" / "first supported format" framing is correct, "supports X formats" is not.

    2. Use Cases lead-in paragraph (line 7): Replace "so they never have to re-derive structure from raw Markdown themselves" with equivalent wording that does not narrow the scope to Markdown-only if it implies exclusivity — check whether this instance needs the same "starting with Markdown" caveat or whether "raw Markdown" here is accurate as a concrete example (it is describing the current/first input, so it may stand as-is if not paired with an exclusivity claim; use judgment consistent with the tagline fix — prefer not to overcorrect a factually accurate concrete reference).

    3. Search the entire README.md for every remaining occurrence of "corpora", "corpus", or "Corpora" (case-insensitive) and replace each with a common word appropriate to its sentence context (e.g. "documents", "sources", "content") — check lines 24 and 26 ("additional raw sources for KIR to compile" already avoids it; verify "Sync tools that keep a Knowledge IR up to date as source Markdown changes" on line 26 and any other line using "Markdown" in an exclusivity-implying way, e.g. "as source Markdown changes" — decide case by case whether it implies Markdown is the only source and adjust only if so).

    4. Re-read the full file after edits to confirm: no "corpora"/"corpus" remains anywhere in README.md; no sentence claims or implies Markdown is the only supported/ingestible format; no sentence claims multi-format support exists today; the product-boundary framing (Knowledge IR as the output boundary, no UI/query/render/vector-search claims) is unchanged from the current file.
  </action>
  <verify>
    <automated>! grep -qi 'corpora\|corpus' /Users/mniedre/git/kir/README.md &amp;&amp; echo PASS || echo FAIL</automated>
  </verify>
  <done>README.md contains no instance of "corpora"/"corpus"; the tagline and Use Cases lead-in describe Markdown as the first/current supported source format (not the only one) without claiming multi-format support exists today; no other README content or section structure changed.</done>
</task>

</tasks>

<verification>
Run `grep -in "corpora\|corpus" README.md` — expect no output (empty match).
Run `grep -in "markdown" README.md` and manually confirm no remaining sentence implies Markdown is the sole/only supported input format.
Diff README.md against its prior version to confirm changes are wording-only (no section additions/removals, no reordering).
</verification>

<success_criteria>
- README.md tagline and Use Cases lead-in no longer imply Markdown-only ingestion; they convey Markdown as the first supported format with more planned, without overclaiming current multi-format support
- README.md contains zero occurrences of "corpora" or "corpus"
- No other README.md content, structure, or product-boundary framing changed
</success_criteria>

<output>
Create `.planning/quick/260701-syb-fix-readme-wording-markdown-is-only-the-/260701-syb-SUMMARY.md` when done
</output>
