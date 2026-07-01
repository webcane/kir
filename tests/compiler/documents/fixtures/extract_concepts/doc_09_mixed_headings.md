# Zephyr Plugin System

Zephyr supports a plugin system that allows third-party extensions to add new event
types, handlers, and routing rules without modifying the core framework.

## Plugin Lifecycle

### Registration

Plugins are registered at startup by placing a plugin manifest in the Zephyr plugins
directory. The manifest declares the plugin's name, version, and the event types it
introduces.

### Activation

#### Conditional Activation

A plugin can be conditionally activated based on the presence of a feature flag in the
deployment manifest. This allows operators to enable or disable plugins without
redeploying the core framework.

#### Activation Order

Plugins are activated in dependency order. If Plugin B depends on Plugin A, Zephyr
ensures Plugin A is fully activated before activating Plugin B.

## Plugin Isolation

Plugins run in an isolated execution context. A failure in one plugin does not affect
other plugins or the core event bus. Plugin logs are namespaced by plugin name to
simplify debugging.
