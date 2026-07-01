# Zephyr Terminology Reference

This document defines the core terms used throughout the Zephyr framework documentation.
Understanding these definitions is essential before reading any other Zephyr guides.

## Core Definitions

An **event** is defined as a discrete, immutable record of something that happened within
the system, identified by a type string and a timestamp. Events are the fundamental unit
of communication in Zephyr.

A **handler** is defined as a registered function or callable that processes events
matching a declared subscription filter. Handlers execute asynchronously and must not
block the event loop.

A **manifest** is defined as the YAML configuration file that describes which handlers
are registered, their subscription filters, and their resource quotas for a given
deployment context.

## Extended Definitions

A **subscription filter** refers to a declarative predicate evaluated against incoming
event metadata. Only events whose metadata satisfies the filter are dispatched to the
associated handler.

A **delivery guarantee** means the protocol commitment made by the event bus regarding
how many times a handler will receive a given event. Zephyr guarantees at-least-once
delivery by default.
