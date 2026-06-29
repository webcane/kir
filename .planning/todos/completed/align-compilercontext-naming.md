---
title: Align CompilerContext naming between ARCHITECTURE.md and REQUIREMENTS.md
date: 2026-06-29
priority: medium
---

## Problem

`REQUIREMENTS.md` (CORE-05) explicitly names the shared pass context `CompilerContext`. `.planning/research/ARCHITECTURE.md` uses `PassContext` everywhere instead (class name, code examples, prose in "Suggested Build Order" step 3).

## Why it matters

If left unresolved, the implementation will pick one name and silently diverge from the other document's terminology — confusing future readers about which is authoritative.

## Action

Pick one name (recommend `CompilerContext`, since REQUIREMENTS.md is the requirement-of-record) and update ARCHITECTURE.md's class name, code examples, and prose to match before Phase 1 implementation begins.
