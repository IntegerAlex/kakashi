---
id: async-backends
title: Async Backends
---

## Async Logging Architecture

For high-throughput applications, Kakashi provides async backends that perform non-blocking I/O operations and batch writes for optimal performance.

### When to Use Async Logging

- **High-throughput applications** (>1000 logs/second)
- **I/O-bound workloads** where logging shouldn't block request processing
- **Production environments** where performance is critical
- **Applications with strict latency requirements**

### Basic Async Setup

```python
from kakashi.core.async_interface import setup_async_logging

# Enable async logging for production
setup_async_logging(
    environment="production",
    service_name="my-api",
    version="1.0.0",
    max_queue_size=25000,
    worker_count=2,
    batch_size=200
)
```

### Async Pipeline Components

#### AsyncPipeline

```python
from kakashi.core.async_pipeline import AsyncPipeline, AsyncPipelineConfig
from kakashi.core.pipeline import PipelineConfig
from kakashi.core.async_backend import AsyncConfig

# Create standard pipeline config
pipeline_config = PipelineConfig(
    min_level=LogLevel.INFO,
    enrichers=(thread_enricher, exception_enricher),
    filters=(),
    formatter=default_json_formatter,
    writers=(file_writer("app.log"),)
)

# Create async config
async_config = AsyncConfig(
    max_queue_size=25000,
    worker_count=2,
    batch_size=200,
    batch_timeout=0.1,
    enable_batching=True
)

# Create async pipeline config
async_pipeline_config = AsyncPipelineConfig(
    pipeline_config=pipeline_config,
    async_config=async_config,
    enable_async=True,
    fallback_to_sync=True
)

pipeline = AsyncPipeline(async_pipeline_config)
```

### Async Backend Configuration

```python
from kakashi.core.async_backend import AsyncConfig, configure_async_backend

# Configure global async backend
backend = configure_async_backend(
    max_queue_size=50000,
    worker_count=4,
    batch_size=500,
    enable_batching=True,
    overflow_strategy="drop_oldest"
)
```

### High-Performance Async Logging

```python
from kakashi.core.async_interface import get_high_performance_logger

# Get ultra-high-performance logger
logger = get_high_performance_logger(
    name="trading",
    log_file="trades.log",
    max_queue_size=100000,
    worker_count=8,
    batch_size=1000
)

# In high-frequency trading loop:
for trade in trades:
    logger.info("Trade executed", **trade.to_dict())  # Microsecond latency
```

### Network Logging

```python
from kakashi.core.async_interface import get_network_logger

def send_to_elasticsearch(message):
    # Your Elasticsearch client code
    es_client.index(index="logs", body=json.loads(message))

logger = get_network_logger("api", send_to_elasticsearch)
logger.info("API call", endpoint="/users", response_time=45)
# Sent to Elasticsearch asynchronously
```

### Performance Monitoring

Monitor async pipeline performance:

```python
from kakashi.core.async_interface import get_async_stats

# Get runtime statistics
stats = get_async_stats()
print(f"Queue size: {stats['queue_size']}")
print(f"Messages processed: {stats['messages_enqueued']}")
print(f"Active workers: {stats['active_workers']}")
```

### Configuration Examples

#### High-Throughput Web Server

```python
from kakashi.core.async_interface import setup_async_logging

def setup_web_server_logging():
    """Optimized for web servers with high request volume."""
    
    setup_async_logging(
        environment="production",
        service_name="web-api",
        version="2.1.0",
        max_queue_size=100000,
        worker_count=8,
        batch_size=1000
    )
```

#### Real-time Analytics

```python
from kakashi.core.async_interface import get_async_structured_logger

def setup_analytics_logging():
    """Logger for real-time analytics with low latency."""
    
    logger = get_async_structured_logger(
        "analytics",
        service="user-analytics",
        version="1.0.0"
    )
    
    return logger
```

### Flush Semantics (Important)

**`flush()` on async loggers does NOT guarantee durability.**

- **Legacy AsyncLogger** (from `kakashi.core.logger`): `flush()` only sleeps 1ms to yield to the background worker. It does **not** wait for queued messages to be written.
- **Functional async loggers** (from `kakashi.core.async_interface`): There is no `flush()` that drains the queue. Messages are processed asynchronously in batches.
- **Only `shutdown_async_backend(timeout=...)` guarantees** that all queued messages are processed before the process exits. This is the ONLY way to ensure no message loss at shutdown.

**Do not rely on `flush()` for application logic.** Treat async logging as best-effort telemetry. For critical audit trails or state, write to a reliable store (database, message queue) and log secondarily.

### Error Handling and Recovery

```python
from kakashi.core.async_interface import shutdown_async_backend

def graceful_shutdown():
    """Gracefully shutdown the async logging backend."""
    try:
        shutdown_async_backend(timeout=10.0)
        print("Async logging shutdown complete")
    except Exception as e:
        print(f"Error during shutdown: {e}")
```

### Application Shutdown Patterns

**You must call `shutdown_async_backend()` at application exit** to prevent message loss. If the process exits without shutdown, queued messages may never be written.

#### Recommended: Register with atexit

```python
import atexit
from kakashi.core.async_interface import shutdown_async_backend

# Register early (e.g. at startup)
atexit.register(shutdown_async_backend)

# Or with custom timeout for high-volume apps:
atexit.register(lambda: shutdown_async_backend(timeout=10.0))
```

#### Timeout Considerations

- **Default (5s)**: Suitable for most applications
- **High-volume**: Use 10-30s if you expect large queues or slow disk/network I/O
- **Tests**: Use shorter timeouts (1-2s) to avoid hanging test suites
- If timeout is exceeded, some messages may be dropped during shutdown

#### What Happens Without Shutdown

- Worker threads are daemon threads in some configurations; the process can exit before the queue drains
- Even with non-daemon workers, abrupt exit (SIGKILL, `os._exit`) bypasses atexit
- Result: silent message loss. Always register shutdown for production services.

### Best Practices

1. **Queue Sizing**: Start with 25,000-50,000 max queue size, adjust based on throughput
2. **Worker Count**: Use 2-4 workers for most applications, 8+ for extreme throughput
3. **Batch Sizing**: Start with 200-500 batch size, increase for higher throughput
4. **Monitoring**: Monitor queue sizes and worker health in production
5. **Error Handling**: Implement graceful shutdown to prevent message loss
6. **Graceful Shutdown**: Ensure all queued messages are processed on shutdown (see Application Shutdown Patterns above)

---

*Last updated: 2025-08-27*
*Contributors: [IntegerAlex]*
