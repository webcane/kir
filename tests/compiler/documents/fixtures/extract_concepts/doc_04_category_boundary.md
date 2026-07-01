# Zephyr Routing and Channel Management

This document covers the routing subsystem and channel lifecycle in Zephyr.

## Channels

A **channel** is defined as a named, typed conduit through which events of a specific
schema flow between producers and consumers. Channels enforce type safety at publish time.

The channel concept is central to Zephyr's architecture: every event must be published
to a named channel, and handlers subscribe to channels rather than individual event types.
This design keeps routing logic declarative and auditable.

## The Zephyr Registry

The Zephyr Registry is the runtime directory that maps channel names to their registered
handlers. You can browse currently registered channels and their subscriber counts at
https://registry.zephyr-io.org. The Registry itself is operated by the Open Infrastructure
Foundation and is updated automatically on each deployment.

The Open Infrastructure Foundation also publishes a channel naming convention guide at
https://docs.zephyr-io.org/channels/naming.
