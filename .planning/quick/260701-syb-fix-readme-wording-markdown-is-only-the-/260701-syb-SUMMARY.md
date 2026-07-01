---
task: 260701-syb-fix-readme-wording-markdown-is-only-the-
type: quick
subsystem: docs
tags: [readme, wording]

key-files:
  modified: [README.md]

key-decisions:
  - "Tagline rewritten to 'starting with Markdown' framing, mirroring PROJECT.md's 'heterogeneous raw sources (starting with Markdown)' phrasing"
  - "Left 'raw Markdown' references in Use Cases lead-in (line 7) and Who Kir Is For (line 32) unchanged — they describe the current concrete input accurately without claiming exclusivity, per plan guidance not to overcorrect factually accurate concrete references"

requirements-completed: []

duration: 5min
completed: 2026-07-01
---

# Quick Task 260701-syb: Fix README Wording Summary

**Reworded README tagline to frame Markdown as the first supported source format (not the only one) and replaced "corpora" with plain language.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-07-01T17:52:00Z
- **Completed:** 2026-07-01T17:52:57Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Fixed tagline to convey Markdown as the first/current supported source format, not the only one, mirroring `.planning/PROJECT.md`'s "heterogeneous raw sources (starting with Markdown)" framing — without claiming multi-format support exists today
- Removed the only occurrence of "corpora" in README.md, replacing it with plain language ("raw sources")

## Task Commits

1. **Task 1: Fix markdown-only framing and replace "corpora" in README.md** - `2c37fe4` (fix)

**Plan metadata:** committed separately by orchestrator (docs commit not made by this executor per constraints)

## Files Created/Modified
- `README.md` - Tagline (line 3) reworded from "it compiles raw Markdown corpora into a canonical Knowledge IR" to "it compiles raw sources — starting with Markdown — into a canonical Knowledge IR"

## Decisions Made
- Searched the full README for every "corpora"/"corpus" occurrence (case-insensitive) — found and fixed exactly one, on line 3. No other occurrences existed.
- Evaluated all other "Markdown" mentions (Use Cases lead-in line 7, Ecosystem Components line 26, Who Kir Is For line 32) for exclusivity implications. None claim or imply Markdown is the only supported format — each refers to Markdown as the current concrete input, which is factually accurate — so left unchanged per plan guidance to avoid overcorrecting accurate concrete references.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

README wording now accurately reflects current vs. planned capability (Markdown as first format, more planned) and uses plain language throughout. No further action needed; task is fully self-contained.

---

## Self-Check: PASSED

- FOUND: README.md contains updated tagline (verified via git diff)
- FOUND: commit 2c37fe4 exists in git log
- PASS: `grep -qi 'corpora\|corpus' README.md` returns no match (confirmed before commit)
- PASS: `git diff --diff-filter=D --name-only HEAD~1 HEAD` shows no deletions

---
*Task: 260701-syb-fix-readme-wording-markdown-is-only-the-*
*Completed: 2026-07-01*
