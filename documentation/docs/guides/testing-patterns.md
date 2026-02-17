---
id: testing-patterns
title: Testing Patterns for Async Loggers
---

## Overview

Testing applications that use async logging requires care. Async loggers enqueue messages to a background queue; if tests exit before the queue drains, logs may not be written and assertions can fail or become flaky.

## When to Use Sync vs Async Loggers in Tests

### Use Sync Loggers When

- You need to assert on log output immediately
- The test checks that specific log lines were written
- You want deterministic, non-flaky tests
- Testing log format or content

```python
from kakashi import get_logger

def test_user_login_logged():
    """Sync logger: output is immediate, assertions work reliably."""
    logger = get_logger("auth")
    logger.info("User logged in", user_id="123")

    # Log is already written; safe to assert on file content
    assert "User logged in" in open("logs/app.log").read()
```

### Use Async Loggers When

- You are testing async logging behavior itself
- Performance benchmarks
- Integration tests where log content is not asserted
- When you explicitly shut down the backend before asserting

## Proper Async Backend Shutdown in Tests

### Functional Async (Pipeline-Based)

For loggers created via `get_async_logger`, `get_high_performance_logger`, or `get_async_structured_logger` from `kakashi.core.async_interface`, use `shutdown_async_backend` in teardown:

```python
import pytest
from kakashi.core.async_interface import get_async_logger, shutdown_async_backend

@pytest.fixture
def async_logger():
    logger = get_async_logger("test.async")
    yield logger
    # Must shut down before test ends to drain queue
    shutdown_async_backend(timeout=2.0)

def test_async_logging(async_logger):
    async_logger.info("Test message", key="value")
    shutdown_async_backend(timeout=2.0)  # Or in fixture teardown
    # Now safe to assert on output
```

### Legacy Async (Simple AsyncLogger)

For `AsyncLogger` from `kakashi.core.logger` (returned by `get_async_logger` from the main package when using the simple API):

```python
import pytest
from kakashi import get_async_logger, shutdown_async_logging

@pytest.fixture
def legacy_async_logger():
    logger = get_async_logger("test.legacy")
    yield logger
    shutdown_async_logging()

def test_legacy_async(legacy_async_logger):
    legacy_async_logger.info("Message")
    shutdown_async_logging()  # Drain before assert
```

## Waiting for Queue Drain

If you cannot shut down (e.g. shared backend), you can poll `get_async_stats()` until the queue is empty. Use with care and a timeout to avoid hanging tests:

```python
import time
from kakashi.core.async_interface import get_async_stats

def wait_for_queue_drain(timeout: float = 5.0, poll_interval: float = 0.05) -> bool:
    """Wait until async queue is empty or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        stats = get_async_stats()
        if stats.get("queue_size", 0) == 0:
            return True
        time.sleep(poll_interval)
    return False

def test_async_with_poll(async_logger):
    async_logger.info("Message")
    assert wait_for_queue_drain(timeout=2.0), "Queue did not drain"
    # Now assert on output
```

## Example Test Fixtures

### Fixture with Proper Cleanup

```python
# conftest.py
import pytest
from kakashi.core.async_interface import (
    get_async_logger,
    shutdown_async_backend,
    get_async_stats,
)

@pytest.fixture
def async_logger_with_teardown():
    """Async logger that shuts down cleanly after each test."""
    logger = get_async_logger("test.async")
    yield logger
    shutdown_async_backend(timeout=2.0)

@pytest.fixture(scope="module")
def async_logger_module_scope():
    """Shared async logger for a module; shutdown once at end."""
    logger = get_async_logger("test.module")
    yield logger
    shutdown_async_backend(timeout=5.0)
```

### Testing with Temp Directory

```python
import tempfile
from pathlib import Path
from kakashi.core.async_interface import get_async_logger, shutdown_async_backend

def test_async_logs_to_file():
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "test.log"
        logger = get_async_logger("test", log_file=str(log_path))
        logger.info("Written to file")
        shutdown_async_backend(timeout=2.0)

        content = log_path.read_text()
        assert "Written to file" in content
```

## Anti-Patterns to Avoid

1. **Asserting immediately after logging** without shutdown or drain:
   ```python
   async_logger.info("x")
   assert "x" in file_content  # Flaky: message may still be in queue
   ```

2. **Not shutting down in teardown** when using async loggers:
   ```python
   @pytest.fixture
   def async_logger():
       return get_async_logger("test")  # No teardown - messages can be lost
   ```

3. **Relying on `flush()`** for async loggers:
   ```python
   async_logger.info("x")
   async_logger.flush()  # Does NOT wait for queue - still flaky
   ```

4. **Using async logger when sync suffices** for content assertions:
   Prefer sync loggers when you need to assert on log output.

## Summary

- Use sync loggers when asserting on log content.
- For async loggers, always call `shutdown_async_backend` (functional) or `shutdown_async_logging` (legacy) in teardown or before asserting.
- Optionally poll `get_async_stats()` for queue drain with a timeout.
- Never rely on `flush()` for durability in tests.
