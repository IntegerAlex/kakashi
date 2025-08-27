---
id: pipeline-composition
title: Pipeline Composition
---

## Creating Custom Pipelines

Kakashi's functional architecture allows you to compose custom logging pipelines from reusable components.

### Basic Pipeline Creation

```python
from kakashi.core.pipeline import Pipeline, PipelineConfig
from kakashi.core.records import LogLevel

# Create a simple console pipeline
config = PipelineConfig(
    min_level=LogLevel.INFO,
    enrichers=(thread_enricher, exception_enricher),
    filters=(),
    formatter=default_json_formatter,
    writers=(console_writer,)
)

pipeline = Pipeline(config)
```

### Custom Enrichers

Enrichers add metadata to log records:

```python
from kakashi.core.records import LogRecord
import time
import threading

def timestamp_enricher(record: LogRecord) -> LogRecord:
    """Add high-precision timestamp."""
    # Create new record with updated timestamp
    return LogRecord(
        timestamp=time.time(),
        level=record.level,
        logger_name=record.logger_name,
        message=record.message,
        fields=record.fields,
        context=record.context,
        exception=record.exception,
        exception_traceback=record.exception_traceback,
        module=record.module,
        function=record.function,
        line_number=record.line_number,
        thread_id=record.thread_id,
        thread_name=record.thread_name,
        process_id=record.process_id
    )

def thread_enricher(record: LogRecord) -> LogRecord:
    """Add thread information."""
    return LogRecord(
        timestamp=record.timestamp,
        level=record.level,
        logger_name=record.logger_name,
        message=record.message,
        fields=record.fields,
        context=record.context,
        exception=record.exception,
        exception_traceback=record.exception_traceback,
        module=record.module,
        function=record.function,
        line_number=record.line_number,
        thread_id=threading.get_ident(),
        thread_name=threading.current_thread().name,
        process_id=record.process_id
    )

def correlation_id_enricher(record: LogRecord) -> LogRecord:
    """Add correlation ID from thread-local storage."""
    import threading
    _local = threading.local()
    
    correlation_id = getattr(_local, 'correlation_id', None)
    if correlation_id and record.context:
        # Create new context with correlation ID
        new_context = record.context.with_custom(correlation_id=correlation_id)
        return record.with_context(new_context)
    return record
```

### Custom Filters

Filters determine which records to process:

```python
def sensitive_data_filter(record: LogRecord) -> bool:
    """Filter out logs containing sensitive data."""
    sensitive_patterns = ['password', 'token', 'secret']
    message_lower = record.message.lower()
    return not any(pattern in message_lower for pattern in sensitive_patterns)

def rate_limit_filter(record: LogRecord) -> bool:
    """Rate limit logs by logger name."""
    # Implementation would track rate limits per logger
    # This is a placeholder - implement your own rate limiting logic
    return True

def environment_filter(record: LogRecord) -> bool:
    """Only process logs for current environment."""
    import os
    if record.context and record.context.environment:
        return record.context.environment == os.getenv('ENVIRONMENT', 'development')
    return True
```

### Custom Formatters

Formatters convert records to strings:

```python
import json
from datetime import datetime

def compact_json_formatter(record: LogRecord) -> str:
    """Compact JSON format for production."""
    data = {
        't': datetime.fromtimestamp(record.timestamp).isoformat(),
        'l': record.level.name,
        'n': record.logger_name,
        'm': record.message
    }
    
    if record.context:
        if record.context.ip:
            data['ip'] = record.context.ip
        if record.context.user_id:
            data['uid'] = record.context.user_id
        if record.context.custom:
            data.update(record.context.custom)
    
    return json.dumps(data, separators=(',', ':'))

def logfmt_formatter(record: LogRecord) -> str:
    """Logfmt format for easy parsing."""
    parts = [
        f'time={datetime.fromtimestamp(record.timestamp).isoformat()}',
        f'level={record.level.name}',
        f'logger={record.logger_name}',
        f'msg="{record.message}"'
    ]
    
    if record.context:
        if record.context.ip:
            parts.append(f'ip={record.context.ip}')
        if record.context.user_id:
            parts.append(f'user_id={record.context.user_id}')
    
    return ' '.join(parts)
```

### Custom Writers

Writers send formatted logs to destinations:

```python
from pathlib import Path
import time

def rotating_file_writer(log_file: Path, max_size: int = 100_000_000):
    """File writer with size-based rotation."""
    def writer(message: str) -> None:
        try:
            if log_file.exists() and log_file.stat().st_size > max_size:
                # Rotate file
                backup_file = log_file.with_suffix(f'.{int(time.time())}.log')
                log_file.rename(backup_file)
            
            with log_file.open('a', encoding='utf-8') as f:
                f.write(message + '\n')
                f.flush()
        except (OSError, UnicodeError) as e:
            print(f"File write error: {e}", file=sys.stderr)
    
    return writer

def network_writer(endpoint: str, timeout: float = 5.0):
    """Send logs to network endpoint."""
    import requests
    
    def writer(message: str) -> None:
        try:
            requests.post(
                endpoint,
                json={'log': message},
                timeout=timeout
            )
        except requests.RequestException as e:
            print(f"Network write error: {e}", file=sys.stderr)
    
    return writer
```

### Pipeline Composition Patterns

#### Multi-Destination Pipeline

```python
def create_multi_destination_pipeline(log_dir: Path) -> Pipeline:
    """Pipeline that writes to console, file, and metrics."""
    
    config = PipelineConfig(
        min_level=LogLevel.INFO,
        enrichers=(
            thread_enricher,
            exception_enricher,
        ),
        filters=(
            sensitive_data_filter,
            environment_filter,
        ),
        formatter=default_json_formatter,
        writers=(
            console_writer,
            rotating_file_writer(log_dir / 'app.log'),
        )
    )
    
    return Pipeline(config)
```

#### Environment-Specific Pipelines

```python
def create_development_pipeline() -> Pipeline:
    """Development pipeline with verbose output."""
    return Pipeline(PipelineConfig(
        min_level=LogLevel.DEBUG,
        enrichers=(thread_enricher, exception_enricher),
        formatter=simple_text_formatter,
        writers=(console_writer,)
    ))

def create_production_pipeline(log_dir: Path) -> Pipeline:
    """Production pipeline optimized for performance."""
    return Pipeline(PipelineConfig(
        min_level=LogLevel.INFO,
        enrichers=(thread_enricher, exception_enricher),
        filters=(sensitive_data_filter,),
        formatter=default_json_formatter,
        writers=(
            rotating_file_writer(log_dir / 'app.log'),
        )
    ))
```

#### Conditional Pipeline Selection

```python
def create_adaptive_pipeline() -> Pipeline:
    """Pipeline that adapts based on environment."""
    import os
    from pathlib import Path
    
    environment = os.getenv('ENVIRONMENT', 'development')
    
    if environment == 'development':
        return create_development_pipeline()
    elif environment == 'production':
        return create_production_pipeline(Path('/var/log/myapp'))
    else:  # testing
        return create_testing_pipeline()

def create_testing_pipeline() -> Pipeline:
    """Testing pipeline with minimal overhead."""
    return Pipeline(PipelineConfig(
        min_level=LogLevel.WARNING,
        enrichers=(),
        filters=(),
        formatter=compact_formatter,
        writers=(null_writer,)
    ))
```

### Performance Considerations

- **Hot Path Optimization**: Place expensive enrichers after filters
- **Memory Efficiency**: Use immutable data structures to enable sharing
- **Error Isolation**: Each component should handle its own errors
- **Lazy Evaluation**: Only compute expensive fields when needed

```python
def performance_optimized_pipeline() -> Pipeline:
    """High-performance pipeline for production."""
    return Pipeline(PipelineConfig(
        min_level=LogLevel.INFO,
        # Fast filters first
        filters=(),
        # Lightweight enrichers
        enrichers=(thread_enricher, exception_enricher),
        # Optimized formatter
        formatter=default_json_formatter,
        # Efficient writers
        writers=(file_writer("app.log"),)
    ))
```

---

*Last updated: 2025-08-27*
*Contributors: [IntegerAlex]*
