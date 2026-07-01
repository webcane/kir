# Zephyr Schema Evolution

As systems grow, event schemas change. Zephyr provides schema evolution primitives that
allow producers and consumers to be upgraded independently without downtime.

## Additive Changes

Additive changes are the safest kind of schema evolution. Adding a new optional field
to an existing event type is additive — older consumers ignore unknown fields, and newer
consumers can use the new data. The Zephyr runtime validates that all deployed handlers
remain compatible after each additive change.

## Breaking Changes and Migration Windows

Breaking changes require a migration window. During the migration window, the event bus
simultaneously routes both the old and new event schema versions to their respective
handlers. Once all handlers have been migrated, the old schema version is deprecated
and removed from the registry.

Schema versioning is tracked automatically by the Zephyr toolchain. Each schema version
is assigned a monotonically increasing integer identifier. Rollbacks revert to a
previous schema version without manual registry edits.
