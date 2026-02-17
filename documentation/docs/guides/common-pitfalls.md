---
id: common-pitfalls
title: Common Pitfalls with Async Loggers
---

## Overview

This guide documents common mistakes when using Kakashi's async logging and how to avoid them.

## 1. Relying on `flush()` for Durability

**Wrong**: Assuming `flush()` waits for all queued messages to be written.

```python
async_logger.info("Critical audit event")
async_logger.flush()  # Does NOT guarantee durability!
# Message may still be in queue - process could exit before it's written
```

**Why**: `AsyncLogger.flush()` only sleeps 1ms to yield to the background worker. Functional async loggers have no `flush()` that drains the queue.

**Right**: Call `shutdown_async_backend(timeout=...)` at application exit.

```python
import atexit
from kakashi.core.async_interface import shutdown_async_backend
atexit.register(shutdown_async_backend)
```

---

## 2. Not Shutting Down Async Backends

**Wrong**: Letting the process exit without calling shutdown.

```python
# main.py
logger = get_async_logger(__name__)
logger.info("Server stopping")
# Process exits - queued messages are lost
```

**Why**: Worker threads may not get CPU time to drain the queue before the process exits. Daemon threads are terminated immediately.

**Right**: Register shutdown with atexit or call it explicitly before exit.

```python
atexit.register(lambda: shutdown_async_backend(timeout=10.0))
```

---

## 3. Using Async Loggers in Tests Without Cleanup

**Wrong**: Asserting on log output immediately after async logging.

```python
def test_login():
    logger = get_async_logger("auth")
    logger.info("User logged in", user_id="123")
    assert "User logged in" in open("app.log").read()  # Flaky - message may not be written yet
```

**Why**: Messages are enqueued asynchronously. The assertion runs before the worker processes the queue.

**Right**: Shut down the backend before asserting, or use a sync logger for this test.

```python
def test_login():
    logger = get_async_logger("auth")
    logger.info("User logged in", user_id="123")
    shutdown_async_backend(timeout=2.0)
    assert "User logged in" in open("app.log").read()
```

See [Testing Patterns](/docs/guides/testing-patterns) for more.

---

## 4. Queue Overflow and Silent Message Drops

**Wrong**: Assuming every log call results in a written message.

```python
# High throughput - queue fills up
for i in range(1_000_000):
    logger.info("Event", id=i)  # Some messages may be dropped
```

**Why**: When the queue is full, the configured overflow strategy (e.g. `drop_oldest`) causes silent drops. There is no exception.

**Right**: Monitor queue size via `get_async_stats()`, size the queue appropriately, and treat async logging as best-effort for non-critical telemetry.

```python
stats = get_async_stats()
if stats.get("queue_size", 0) > 0.8 * stats.get("max_queue_size", 1):
    # Consider backpressure or alerting
    pass
```

---

## 5. Mixing Legacy and Functional Async APIs

**Wrong**: Calling both shutdown functions and getting confused about which backend is active.

```python
from kakashi import get_async_logger, shutdown_async_logging
from kakashi.core.async_interface import get_async_logger as get_func_async, shutdown_async_backend

# Two different systems - easy to mix up
legacy = get_async_logger("a")
func = get_func_async("b")
# Which shutdown drains which queue?
```

**Why**: Kakashi has two separate async implementations. Each has its own queue and shutdown.

**Right**: Stick to one system. For new code, use the functional API throughout.

```python
from kakashi.core.async_interface import get_async_logger, shutdown_async_backend
logger = get_async_logger(__name__)
# ...
shutdown_async_backend()
```

---

## 6. Blocking on Full Queue with Default Config

**Wrong**: Assuming `put` always succeeds; in `block` mode a full queue can block the calling thread.

```python
# Default overflow_strategy is "block"
for i in range(100_000):
    logger.info("x")  # Can block indefinitely if workers are slow
```

**Right**: For high-throughput or latency-sensitive paths, use `queue_overflow_strategy="drop_oldest"` and accept potential drops, or increase queue size and worker count.

---

## Summary

| Pitfall | Mitigation |
|---------|------------|
| Relying on `flush()` | Use `shutdown_async_backend()` at exit |
| No shutdown | Register `atexit.register(shutdown_async_backend)` |
| Flaky tests | Shut down before asserting, or use sync logger |
| Queue overflow | Monitor stats, size queue, treat as best-effort |
| Mixing APIs | Use functional async only for new code |
| Blocking on full queue | Use `drop_oldest` or increase capacity |
