# Zephyr Framework Overview

Zephyr is a modular event-driven framework for building distributed systems. Its core
abstraction is the event bus, which decouples producers from consumers and enables
asynchronous coordination across services.

## Event Bus Architecture

The event bus routes messages between registered handlers. Each handler declares a
subscription filter that limits which event types it receives, reducing unnecessary
processing load. The framework guarantees at-least-once delivery for all published events.

## Integration with Nexus Platform

The Zephyr SDK integrates natively with Nexus Platform, the infrastructure provider
developed by AeroCorp Systems. Configuration is managed through a YAML manifest file
deployed to the Nexus cluster. For full deployment instructions, refer to the official
Zephyr deployment guide at https://docs.zephyr-framework.io/deploy.

## Getting Started

Install the SDK using the standard package manager, then register your event handlers
and publish your first event. Example projects are available in the
[Zephyr Example Repository](https://github.com/aerocorp/zephyr-examples).
