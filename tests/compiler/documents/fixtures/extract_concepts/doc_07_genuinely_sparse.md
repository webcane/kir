# Zephyr Heartbeat

The heartbeat is an internal signal emitted by the event bus on a configurable interval
to confirm the bus is alive and processing events normally. Applications that require
liveness monitoring can subscribe to the heartbeat channel.
