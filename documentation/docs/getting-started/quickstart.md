---
id: quickstart
title: Quickstart
---

## 🚀 Get Started in Seconds

Kakashi is designed for immediate use with intelligent defaults and high performance out of the box.

### Basic Usage

```python
from kakashi import get_logger, get_async_logger

# Synchronous logging (high performance)
logger = get_logger(__name__)
logger.info("Application started", version="1.0.0")
logger.warning("This is a warning message")
logger.error("Something went wrong", component="startup")

# Asynchronous logging (maximum throughput)
async_logger = get_async_logger(__name__)
async_logger.info("High-volume logging", user_id=123)
```

### Module Loggers

```python
from kakashi import get_logger

# Create loggers for different modules
app_logger = get_logger("myapp")
db_logger = get_logger("myapp.database")
api_logger = get_logger("myapp.api")

# Structured logging with fields
db_logger.info("Database connection established", db="primary", pool_size=10)
api_logger.info("Endpoint called", route="/users", method="GET", status=200)
```

### Performance Features

```python
# Thread-local buffering for concurrent applications
logger.info("Processing request", request_id="abc-123", user_id=456)

# Batch processing for high throughput
for i in range(1000):
    logger.debug("Processing item", item_id=i, status="pending")

# Automatic batch flush when threshold reached
```

### Cleanup

```python
from kakashi import shutdown_async_logging

# Graceful shutdown of async logging
shutdown_async_logging()
```


