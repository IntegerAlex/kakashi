---
id: core
title: Core API Reference
---

## 🚀 High-Performance Logging API

Kakashi provides a modern, high-performance logging API designed for production applications with superior throughput and concurrency scaling.

## Logger Factory Functions

### `get_logger(name, min_level=20)`

Get a high-performance synchronous logger instance.

```python
def get_logger(name: str, min_level: int = 20) -> Logger
```

**Returns:** A `Logger` instance optimized for high throughput with thread-local buffering.

**Parameters:**
- `name`: Logger name (typically `__name__`)
- `min_level`: Minimum log level (default: 20 = INFO)

**Example:**
```python
from kakashi import get_logger

logger = get_logger(__name__)
logger.info("Application started", version="1.0.0")
logger.warning("Configuration warning", config_file="app.conf")
logger.error("Database connection failed", db="primary", error="timeout")
```

### `get_async_logger(name, min_level=20)`

Get a high-performance asynchronous logger instance.

```python
def get_async_logger(name: str, min_level: int = 20) -> AsyncLogger
```

**Returns:** An `AsyncLogger` instance optimized for maximum throughput with background processing.

**Parameters:**
- `name`: Logger name (typically `__name__`)
- `min_level`: Minimum log level (default: 20 = INFO)

**Example:**
```python
from kakashi import get_async_logger

async_logger = get_async_logger(__name__)
async_logger.info("High-volume logging", user_id=123, action="login")
async_logger.warning("Rate limit approaching", requests_per_min=95)
```

## Core Classes

### `Logger`

High-performance synchronous logger with thread-local buffering.

```python
class Logger:
    def __init__(self, name: str, min_level: int = 20)
    
    def debug(self, message: str, **fields: Any) -> None
    def info(self, message: str, **fields: Any) -> None
    def warning(self, message: str, **fields: Any) -> None
    def error(self, message: str, **fields: Any) -> None
    def critical(self, message: str, **fields: Any) -> None
    def exception(self, message: str, **fields: Any) -> None
    
    def flush(self) -> None
```

**Key Features:**
- Thread-local buffering for minimal contention
- Pre-computed level checks for fast filtering
- Batch processing for efficient I/O
- Direct `sys.stderr.write` for maximum performance

### `AsyncLogger`

High-performance asynchronous logger with background processing.

```python
class AsyncLogger:
    def __init__(self, name: str, min_level: int = 20)
    
    def debug(self, message: str, **fields: Any) -> None
    def info(self, message: str, **fields: Any) -> None
    def warning(self, message: str, **fields: Any) -> None
    def error(self, message: str, **fields: Any) -> None
    def critical(self, message: str, **fields: Any) -> None
    def exception(self, message: str, **fields: Any) -> None
    
    def flush(self) -> None
```

**Key Features:**
- Background worker thread for non-blocking operation
- Queue-based message handling with backpressure protection
- Batch processing for optimal throughput
- Graceful shutdown with proper cleanup

## Utility Functions

### `clear_logger_cache()`

Clear the logger cache (useful for testing and memory management).

```python
def clear_logger_cache() -> None
```

**Example:**
```python
from kakashi import clear_logger_cache

# Clear all cached loggers
clear_logger_cache()
```

### `shutdown_async_logging()`

Gracefully shutdown async logging and wait for background workers to complete.

```python
def shutdown_async_logging() -> None
```

**Example:**
```python
from kakashi import shutdown_async_logging

# Graceful shutdown
shutdown_async_logging()
```

## Log Levels

Kakashi uses standard Python logging levels:

```python
import logging

# Standard levels (compatible with Python's logging module)
DEBUG = 10      # Detailed information for debugging
INFO = 20       # General information about program execution
WARNING = 30    # Warning messages for potentially problematic situations
ERROR = 40      # Error messages for serious problems
CRITICAL = 50   # Critical error messages for fatal errors
```

## Performance Characteristics

### Thread Safety
- **Zero Contention**: Thread-local buffering eliminates lock contention
- **Batch Processing**: Efficient I/O with configurable batch sizes
- **Pre-computed Checks**: Fast level filtering with minimal overhead

### Memory Efficiency
- **Buffer Pooling**: Reusable buffers for consistent memory usage
- **Structured Fields**: Efficient serialization as `key=value` pairs
- **Minimal Allocations**: Optimized for production workloads

### Async Performance
- **Background Processing**: Non-blocking operation with worker threads
- **Queue Management**: Intelligent backpressure handling
- **Batch Optimization**: Maximum throughput through efficient batching

```python
def get_performance_logger(name: str) -> PerformanceLogger
```

## Configuration Functions

### `set_log_level(level)`

Set global log level.

```python
def set_log_level(level: Union[str, LogLevel]) -> None
```

**Examples:**
```python
set_log_level('DEBUG')
set_log_level(LogLevel.INFO)
```

## Context Management

### `set_request_context(ip, access)`

Set request context for all subsequent logs.

```python
def set_request_context(
    ip: str, 
    access: str,
    request_id: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None
```

### `set_user_context(**kwargs)`

Set user context for all subsequent logs.

```python
def set_user_context(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **custom_fields: Any
) -> None
```

### `set_custom_context(**kwargs)`

Set custom context fields.

```python
def set_custom_context(**fields: Any) -> None
```

### `clear_request_context()`

Clear all request context.

```python
def clear_request_context() -> None
```

## Advanced Functions

### `create_custom_logger(name, config)`

Create a logger with custom configuration.

```python
def create_custom_logger(
    name: str, 
    config: LoggerConfig
) -> FunctionalLogger
```

### `clear_logger_cache()`

Clear the logger cache (useful for testing).

```python
def clear_logger_cache() -> None
```

## Simple Logging Functions

Direct logging functions that auto-setup if needed:

```python
def debug(message: str, **fields: Any) -> None
def info(message: str, **fields: Any) -> None
def warning(message: str, **fields: Any) -> None
def error(message: str, **fields: Any) -> None
def critical(message: str, **fields: Any) -> None
def exception(message: str, **fields: Any) -> None

# Specialized logging
def metric(name: str, value: Union[int, float], **fields: Any) -> None
def audit(action: str, resource: str, **fields: Any) -> None
def security(event_type: str, severity: str = "info", **fields: Any) -> None
```

## Data Types

### `LogLevel`

```python
class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    
    @classmethod
    def from_name(cls, name: str) -> 'LogLevel'
```

### `LogRecord`

```python
@dataclass(frozen=True)
class LogRecord:
    timestamp: float
    level: LogLevel
    logger_name: str
    message: str
    context: Optional[LogContext] = None
    exception_info: Optional[Tuple] = None
    source_location: Optional[SourceLocation] = None
    extra_fields: Optional[Dict[str, Any]] = None
```

### `LogContext`

```python
@dataclass(frozen=True)
class LogContext:
    ip: Optional[str] = None
    access: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    service_name: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None
    
    def merge(self, other: 'LogContext') -> 'LogContext'
    def with_custom(self, **kwargs) -> 'LogContext'
```
