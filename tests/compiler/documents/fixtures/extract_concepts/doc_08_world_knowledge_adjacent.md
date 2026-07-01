# Zephyr Result Cache

In Zephyr, a **cache** is defined as the per-handler store of event processing outcomes
that allows a handler to skip reprocessing an event it has already seen. This is
distinct from a general-purpose data cache: a Zephyr cache stores exactly one boolean
outcome per event identity, not arbitrary data.

## Cache Scope

The Zephyr cache is scoped to a single handler instance and a single deployment run.
It is never shared across handler instances or persisted across restarts. Its purpose
is deduplication within a single run, not performance optimization across runs.

## Cache Invalidation

The cache is invalidated automatically when the handler's subscription filter changes.
An updated filter may cause previously-processed events to match new criteria, so the
cache must be cleared to ensure correctness. The Zephyr runtime handles invalidation
transparently — no application code is required.
