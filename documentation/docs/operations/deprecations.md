---
id: deprecations
title: Deprecations & Compatibility
---

## Two Async Logging Systems

Kakashi provides **two separate async logging implementations**. Choose based on your needs:

### 1. Legacy Async (Simple)

- **Location**: `kakashi.core.logger.AsyncLogger`
- **Entry point**: `from kakashi import get_async_logger` (when using the main package logger API)
- **Characteristics**: Single global queue, fixed 10K capacity, writes to stderr, minimal configuration
- **Shutdown**: `shutdown_async_logging()`
- **Use when**: Simple scripts, quick prototypes, or when you need minimal setup
- **Status**: Will be deprecated in v0.3.0; use functional async for new code

### 2. Functional Async (Pipeline-Based)

- **Location**: `kakashi.core.async_interface`
- **Entry points**: `get_async_logger`, `get_async_structured_logger`, `get_high_performance_logger`, `get_network_logger`
- **Characteristics**: Configurable queue size, workers, batching, file/network sinks, structured JSON
- **Shutdown**: `shutdown_async_backend(timeout=...)`
- **Use when**: Production applications, high throughput, file/network logging, structured output
- **Status**: **Recommended for new code**

### Which One Am I Using?

- If you call `from kakashi import get_async_logger` and get an `AsyncLogger` (no `log_file` or `formatter_type`), you are using the **legacy** system.
- If you call `from kakashi.core.async_interface import get_async_logger` or use `get_structured_logger` with async config, you are using the **functional** system.

### Migration Path

```python
# Legacy (will be deprecated)
from kakashi import get_async_logger, shutdown_async_logging
logger = get_async_logger(__name__)
# ... use logger ...
shutdown_async_logging()

# Functional (recommended)
from kakashi.core.async_interface import get_async_logger, shutdown_async_backend
logger = get_async_logger(__name__)  # Same name, different implementation
# ... use logger ...
shutdown_async_backend(timeout=5.0)
```

---

## Other Deprecations

Legacy singleton-style API is maintained for compatibility but will be deprecated. Prefer the functional API via `kakashi.core` and top-level helpers.

Legacy middleware names map to enterprise integrations:

- FastAPI: `kakashi.setup_fastapi(app, ...)`
- Flask: `kakashi.setup_flask(app, ...)`
- Django: `kakashi.setup_django(...)`

### Deprecation Timeline

| Component | Deprecation (v0.3.0) | Removal (v0.4.0) |
|-----------|----------------------|------------------|
| Legacy `AsyncLogger` / `get_async_logger` from `kakashi` | Yes (use `kakashi.core.async_interface`) | Yes |
| Legacy singleton API | Yes | TBD |
