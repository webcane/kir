# Zephyr Configuration System

Zephyr's configuration system provides a structured, validated way to control framework
behavior across environments. All configuration is declarative and version-controlled.

## Settings Hierarchy

The settings hierarchy defines the precedence order for configuration values. Values
provided by the deployment manifest override values in the default configuration file,
which in turn override compiled-in defaults. This layered approach allows environment-
specific overrides without forking configuration files.

## Environment Profiles

An **environment profile** is defined as a named set of configuration overrides that
apply when Zephyr is deployed in a specific environment (development, staging,
production). Profiles are declared in the deployment manifest and selected at startup
via the ZEPHYR_ENV environment variable.

## Configuration Schema

The configuration schema is maintained by ConfiguCore, the configuration management
library that Zephyr uses internally. The canonical schema reference is published at
https://docs.zephyr-framework.io/config/schema. ConfiguCore validates all configuration
at startup and reports validation errors as structured Diagnostics before the event bus
starts.

For migration guides when upgrading between Zephyr major versions, see the official
upgrade documentation at https://docs.zephyr-framework.io/upgrade.
