# Zephyr Backpressure Handling

When a handler cannot keep up with the incoming event rate, backpressure builds up in
the event bus queue. The framework monitors queue depth and applies flow control
automatically to prevent memory exhaustion.

## Flow Control Mechanisms

The primary flow control mechanism is adaptive throttling. When queue depth exceeds the
configured high-water mark, Zephyr reduces the dispatch rate proportionally. Producers
that publish faster than consumers can process will experience increased latency on
their publish calls.

Adaptive throttling is transparent to handlers — they continue receiving events at the
rate they can process without needing any code changes. Producers, however, should
implement retry logic to handle the increased latency gracefully.

## Monitoring Backpressure

The Zephyr metrics endpoint exposes the current queue depth, dispatch rate, and
throttle ratio as time-series data. Operators should configure alerts on sustained
high-water mark breaches to detect handler bottlenecks early.
