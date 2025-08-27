---
id: architecture
title: Architecture
---

## Core Design Principles

Kakashi implements a **high-performance, thread-safe architecture** optimized for production workloads with minimal contention and maximum throughput.

### High-Performance Architecture

The logging system is designed around **performance-first principles**:

```python
Fast Level Check → Thread-Local Buffer → Batch Processing → Optimized I/O
```

#### Core Components

1. **Logger** (`Logger`)
   - Thread-local buffering for minimal contention
   - Pre-computed level checks for fast filtering
   - Batch processing for efficient I/O operations
   - Direct `sys.stderr.write` for maximum performance

2. **AsyncLogger** (`AsyncLogger`)
   - Background worker thread for non-blocking operation
   - Queue-based message handling with backpressure protection
   - Batch processing for optimal throughput
   - Graceful shutdown with proper cleanup

3. **LogFormatter** (`LogFormatter`)
   - Optimized string formatting with minimal allocations
   - Structured field serialization as `key=value` pairs
   - Unified path for simple and structured logging
   - Memory-efficient string operations

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
    # Core fields (always present)
    timestamp: float
    level: LogLevel
    logger_name: str
    message: str
    
    # Optional structured fields
    fields: Optional[Dict[str, Any]] = None  # Key-value pairs for structured logging
    context: Optional[LogContext] = None     # Contextual information
    
    # Exception information
    exception: Optional[Exception] = None
    exception_traceback: Optional[str] = None
    
    # Source location (for debugging)
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    
    # Threading information
    thread_id: Optional[int] = None
    thread_name: Optional[str] = None
    process_id: Optional[int] = None
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
    def process(self, record: LogRecord) -> None:
        # Non-blocking I/O operations through async backend
        # Batched writes for efficiency
        # Fallback to sync pipeline if async fails
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
