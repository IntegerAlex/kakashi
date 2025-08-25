---
id: architecture
title: Architecture
---

## Core Design Principles

Kakashi implements a **functional, pipeline-based architecture** with immutable configuration, eliminating hidden global state and providing predictable behavior.

### Functional Pipeline Architecture

The logging system processes records through a series of **pure functions**:

```python
LogRecord → Enrichers → Filters → Formatter → Writers
```

#### Pipeline Components

1. **Enrichers** (`Callable[[LogRecord], LogRecord]`)
   - Add context and metadata to log records
   - Stateless transformations (thread-safe)
   - Examples: timestamp enricher, context enricher, source location enricher

2. **Filters** (`Callable[[LogRecord], bool]`)
   - Determine if a record should be processed
   - Level filtering, module filtering, custom business logic
   - Short-circuit evaluation for performance

3. **Formatters** (`Callable[[LogRecord], str]`)
   - Convert log records to output strings
   - JSON, compact text, or custom formats
   - Optimized for minimal allocations

4. **Writers** (`Callable[[str], None]`)
   - Send formatted logs to destinations
   - Console, files, network endpoints
   - Error isolation (writer failures don't crash app)

### Immutable Configuration

```python
@dataclass(frozen=True)
class PipelineConfig:
    min_level: LogLevel = LogLevel.INFO
    enrichers: Tuple[Enricher, ...] = ()
    filters: Tuple[Filter, ...] = ()
    formatter: Optional[Formatter] = None
    writers: Tuple[Writer, ...] = ()
```

### Data Structures

#### LogRecord
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

#### LogContext
```python
@dataclass(frozen=True)
class LogContext:
    # Request context
    ip: Optional[str] = None
    access: Optional[str] = None
    request_id: Optional[str] = None
    
    # User context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Application context
    service_name: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    
    # Custom fields
    custom: Optional[Dict[str, Any]] = None
```

### Async Backend

For high-throughput scenarios, Kakashi provides an optional async backend:

```python
class AsyncPipeline:
    async def process(self, record: LogRecord) -> None:
        # Non-blocking I/O operations
        # Batched writes for efficiency
        # Backpressure handling
```

### Thread Safety

- **Immutable data structures** eliminate race conditions
- **Pure functions** have no shared state
- **Thread-local context** for request/user information
- **Lock-free hot path** for maximum performance

### Performance Characteristics

- **Hot path optimization**: Level checks first, minimal allocations
- **Lazy evaluation**: Expensive operations only when needed
- **Batched I/O**: Async backend batches writes for efficiency
- **Memory efficiency**: Immutable structures enable sharing

### Error Handling

- **Graceful degradation**: Writer failures don't crash the application
- **Fallback loggers**: Emergency loggers when setup fails
- **Error isolation**: Each pipeline component is isolated
- **Silent operation**: Never crash the host application
