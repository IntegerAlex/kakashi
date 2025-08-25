---
id: core
title: Core API Reference
---

## Setup Functions

### `setup(environment=None, service=None, version=None, **kwargs)`

Intelligent one-line setup for Kakashi with automatic environment detection.

```python
def setup(
    environment: Optional[str] = None,
    service: Optional[str] = None,
    version: Optional[str] = None,
    log_directory: Optional[Union[str, Path]] = None,
    level: Optional[Union[str, LogLevel]] = None,
    structured: bool = True,
    async_logging: Optional[bool] = None,
    console_output: bool = True,
    file_output: bool = True,
    **kwargs: Any
) -> None
```

**Parameters:**
- `environment`: Auto-detected if None. Options: 'development', 'production', 'testing'
- `service`: Service name (auto-detected from `__main__` if None)
- `version`: Service version (added to all logs)
- `log_directory`: Where to write log files (auto-configured if None)
- `level`: Log level (auto-configured based on environment if None)
- `structured`: Use structured JSON logging (recommended: True)
- `async_logging`: Use async I/O (auto-configured for production)
- `console_output`: Enable console logging
- `file_output`: Enable file logging

**Examples:**
```python
# Simplest setup
kakashi.setup()

# Production setup
kakashi.setup("production", service="user-api", version="2.1.0")

# High-performance setup
kakashi.setup("production", async_logging=True, level="INFO")
```

### `setup_logging(environment, **kwargs)`

Advanced environment configuration for power users.

```python
def setup_logging(
    environment: str,
    service_name: Optional[str] = None,
    version: Optional[str] = None,
    log_directory: Optional[Path] = None,
    enable_async_io: bool = False,
    **kwargs: Any
) -> None
```

## Logger Factory Functions

### `get_logger(name)`

Get a traditional logger instance (compatibility mode).

```python
def get_logger(name: str) -> Logger
```

### `get_structured_logger(name)`

Get a structured logger instance (recommended).

```python
def get_structured_logger(name: str) -> StructuredLogger
```

**Returns:** Logger with structured field support:
```python
logger = get_structured_logger(__name__)
logger.info("User created", user_id=42, role="admin")
```

### `get_request_logger(name)`

Get a logger with request context helpers.

```python
def get_request_logger(name: str) -> RequestLogger
```

### `get_performance_logger(name)`

Get a logger optimized for high-throughput scenarios.

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
