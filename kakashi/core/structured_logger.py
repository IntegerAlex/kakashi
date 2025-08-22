"""
High-performance structured logging optimized for modern log analysis platforms.

This module implements a structured logging interface that prioritizes key-value
pairs over string formatting, uses high-speed JSON serialization, and defers
expensive operations to async worker threads.

Key features:
- Key-value pair focused API (logger.info('event', key=value))
- orjson for ultra-fast JSON serialization
- Deferred serialization in worker threads
- Optimized for machine parsing (Elasticsearch, Splunk, etc.)
- Backward compatible with traditional logging
- Zero-copy when possible
- Structured data validation
"""

import time
import threading
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field, asdict

from .records import LogRecord, LogLevel, LogContext

# Try to import orjson for high-performance JSON serialization
try:
    import orjson
    HAS_ORJSON = True
    
    def fast_json_serialize(data: Any) -> bytes:
        """Ultra-fast JSON serialization using orjson."""
        return orjson.dumps(
            data,
            option=orjson.OPT_UTC_Z | orjson.OPT_SERIALIZE_NUMPY  # Optimize for logging
        )
    
    def fast_json_serialize_str(data: Any) -> str:
        """Ultra-fast JSON serialization returning string."""
        return orjson.dumps(
            data,
            option=orjson.OPT_UTC_Z | orjson.OPT_SERIALIZE_NUMPY
        ).decode('utf-8')
    
except ImportError:
    import json
    HAS_ORJSON = False
    
    def fast_json_serialize(data: Any) -> bytes:
        """Fallback JSON serialization using standard library."""
        return json.dumps(data, separators=(',', ':')).encode('utf-8')
    
    def fast_json_serialize_str(data: Any) -> str:
        """Fallback JSON serialization returning string."""
        return json.dumps(data, separators=(',', ':'))


@dataclass
class StructuredLogEntry:
    """
    High-performance structured log entry optimized for serialization.
    
    This class is designed to be serialized efficiently and contains
    only the essential data needed for structured logging.
    """
    timestamp: float
    level: str
    message: str
    fields: Dict[str, Any] = field(default_factory=dict)
    
    # Context information
    service: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    
    # Request/trace context
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Source location (optional, impacts performance)
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    source_function: Optional[str] = None
    
    # Thread information
    thread_id: Optional[int] = None
    thread_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        # Use dataclass asdict but exclude None values for efficiency
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}
    
    def to_json_bytes(self) -> bytes:
        """Convert to JSON bytes for high-performance output."""
        return fast_json_serialize(self.to_dict())
    
    def to_json_str(self) -> str:
        """Convert to JSON string."""
        return fast_json_serialize_str(self.to_dict())
    
    def add_field(self, key: str, value: Any) -> None:
        """Add a field to the structured entry."""
        self.fields[key] = value
    
    def add_fields(self, **kwargs) -> None:
        """Add multiple fields to the structured entry."""
        self.fields.update(kwargs)


class StructuredLogger:
    """
    High-performance structured logger optimized for key-value logging.
    
    This logger is designed to:
    1. Accept key-value pairs as the primary logging interface
    2. Defer expensive JSON serialization to worker threads
    3. Minimize object allocation and copying
    4. Optimize for machine parsing and analysis
    5. Provide backward compatibility with string-based logging
    
    Example usage:
        logger = StructuredLogger("my_service")
        
        # Preferred: Key-value structured logging
        logger.info("User logged in", user_id=123, auth_method="password")
        logger.error("Payment failed", order_id="ord123", amount=99.99, error="card_declined")
        
        # Also supports: Traditional string logging
        logger.info("User logged in: user_id=123")
    """
    
    def __init__(
        self,
        name: str,
        pipeline: Optional[Any] = None,  # SinkPipeline or AsyncPipeline
        min_level: LogLevel = LogLevel.INFO,
        include_source: bool = False,
        include_thread_info: bool = True,
        base_context: Optional[LogContext] = None,
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name/identifier
            pipeline: Pipeline to send log records to
            min_level: Minimum log level to process
            include_source: Whether to capture source location (impacts performance)
            include_thread_info: Whether to include thread information
            base_context: Base context added to all log entries
        """
        self.name = name
        self.pipeline = pipeline
        self.min_level = min_level
        self.include_source = include_source
        self.include_thread_info = include_thread_info
        self.base_context = base_context
        
        # Performance counters
        self._messages_logged = 0
        self._bytes_generated = 0
        self._lock = threading.RLock()
    
    def _should_log(self, level: LogLevel) -> bool:
        """Fast level check."""
        return level >= self.min_level
    
    def _create_structured_entry(
        self,
        level: LogLevel,
        message: str,
        **fields
    ) -> StructuredLogEntry:
        """
        Create a structured log entry with minimal overhead.
        
        This method is optimized for speed and low memory allocation.
        """
        now = time.time()
        
        entry = StructuredLogEntry(
            timestamp=now,
            level=level.name,
            message=message,
            fields=fields
        )
        
        # Add base context if available
        if self.base_context:
            if self.base_context.service_name:
                entry.service = self.base_context.service_name
            if self.base_context.version:
                entry.version = self.base_context.version
            if self.base_context.environment:
                entry.environment = self.base_context.environment
            if self.base_context.trace_id:
                entry.trace_id = self.base_context.trace_id
            if self.base_context.user_id:
                entry.user_id = self.base_context.user_id
        
        # Add thread information if enabled
        if self.include_thread_info:
            current_thread = threading.current_thread()
            entry.thread_id = current_thread.ident
            entry.thread_name = current_thread.name
        
        # Add source information if enabled (expensive!)
        if self.include_source:
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back and frame.f_back.f_back:
                caller_frame = frame.f_back.f_back
                entry.source_file = caller_frame.f_code.co_filename
                entry.source_line = caller_frame.f_lineno
                entry.source_function = caller_frame.f_code.co_name
        
        return entry
    
    def _log_structured(self, level: LogLevel, message: str, **fields) -> None:
        """
        Internal method to log a structured entry.
        
        This method creates the structured entry and sends it to the pipeline
        for processing. Serialization is deferred to the pipeline/worker threads.
        """
        if not self._should_log(level):
            return
        
        # Create structured entry (fast)
        entry = self._create_structured_entry(level, message, **fields)
        
        # Convert to LogRecord for pipeline compatibility
        log_record = LogRecord(
            timestamp=entry.timestamp,
            level=level,
            message=message,
            fields=entry.fields,
            context=self.base_context,
            source_file=entry.source_file,
            source_line=entry.source_line,
            source_function=entry.source_function,
            thread_id=entry.thread_id,
            thread_name=entry.thread_name,
            logger_name=self.name
        )
        
        # Send to pipeline (deferred processing)
        if self.pipeline:
            try:
                self.pipeline.process(log_record)
            except Exception:
                # Never let logging errors crash the application
                pass
        
        # Update performance counters
        with self._lock:
            self._messages_logged += 1
    
    # ========================================================================
    # STRUCTURED LOGGING API (PREFERRED)
    # ========================================================================
    
    def debug(self, message: str, **fields) -> None:
        """Log debug message with structured fields."""
        self._log_structured(LogLevel.DEBUG, message, **fields)
    
    def info(self, message: str, **fields) -> None:
        """Log info message with structured fields."""
        self._log_structured(LogLevel.INFO, message, **fields)
    
    def warning(self, message: str, **fields) -> None:
        """Log warning message with structured fields."""
        self._log_structured(LogLevel.WARNING, message, **fields)
    
    def warn(self, message: str, **fields) -> None:
        """Alias for warning."""
        self.warning(message, **fields)
    
    def error(self, message: str, **fields) -> None:
        """Log error message with structured fields."""
        self._log_structured(LogLevel.ERROR, message, **fields)
    
    def critical(self, message: str, **fields) -> None:
        """Log critical message with structured fields."""
        self._log_structured(LogLevel.CRITICAL, message, **fields)
    
    def fatal(self, message: str, **fields) -> None:
        """Alias for critical."""
        self.critical(message, **fields)
    
    # ========================================================================
    # SPECIALIZED STRUCTURED LOGGING METHODS
    # ========================================================================
    
    def metric(self, metric_name: str, value: Union[int, float], **fields) -> None:
        """Log a metric with structured fields."""
        self._log_structured(
            LogLevel.INFO,
            f"Metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            metric_type="gauge",
            **fields
        )
    
    def counter(self, counter_name: str, increment: int = 1, **fields) -> None:
        """Log a counter increment with structured fields."""
        self._log_structured(
            LogLevel.INFO,
            f"Counter: {counter_name}",
            counter_name=counter_name,
            counter_increment=increment,
            metric_type="counter",
            **fields
        )
    
    def timer(self, operation: str, duration_ms: float, **fields) -> None:
        """Log a timing measurement with structured fields."""
        self._log_structured(
            LogLevel.INFO,
            f"Timer: {operation}",
            operation=operation,
            duration_ms=duration_ms,
            metric_type="timer",
            **fields
        )
    
    def event(self, event_name: str, **fields) -> None:
        """Log an event with structured fields."""
        self._log_structured(
            LogLevel.INFO,
            f"Event: {event_name}",
            event_name=event_name,
            event_type="custom",
            **fields
        )
    
    def audit(self, action: str, resource: str, **fields) -> None:
        """Log an audit event with structured fields."""
        self._log_structured(
            LogLevel.INFO,
            f"Audit: {action} on {resource}",
            audit_action=action,
            audit_resource=resource,
            audit_timestamp=time.time(),
            **fields
        )
    
    def request(self, method: str, path: str, status_code: int, duration_ms: float, **fields) -> None:
        """Log an HTTP request with structured fields."""
        level = LogLevel.ERROR if status_code >= 400 else LogLevel.INFO
        self._log_structured(
            level,
            f"HTTP {method} {path}",
            http_method=method,
            http_path=path,
            http_status_code=status_code,
            http_duration_ms=duration_ms,
            **fields
        )
    
    def security(self, event_type: str, severity: str = "info", **fields) -> None:
        """Log a security event with structured fields."""
        level_map = {
            "info": LogLevel.INFO,
            "warning": LogLevel.WARNING,
            "error": LogLevel.ERROR,
            "critical": LogLevel.CRITICAL
        }
        level = level_map.get(severity, LogLevel.INFO)
        
        self._log_structured(
            level,
            f"Security: {event_type}",
            security_event_type=event_type,
            security_severity=severity,
            security_timestamp=time.time(),
            **fields
        )
    
    # ========================================================================
    # CONTEXT MANAGEMENT
    # ========================================================================
    
    def with_context(self, **context_fields) -> 'BoundStructuredLogger':
        """Create a bound logger with additional context."""
        if self.base_context:
            new_context = self.base_context.with_custom(**context_fields)
        else:
            new_context = LogContext(custom=context_fields)
        
        return BoundStructuredLogger(
            base_logger=self,
            bound_context=new_context
        )
    
    def with_trace(self, trace_id: str, span_id: Optional[str] = None) -> 'BoundStructuredLogger':
        """Create a bound logger with trace context."""
        context_fields = {"trace_id": trace_id}
        if span_id:
            context_fields["span_id"] = span_id
        return self.with_context(**context_fields)
    
    def with_user(self, user_id: str, **user_fields) -> 'BoundStructuredLogger':
        """Create a bound logger with user context."""
        context_fields = {"user_id": user_id, **user_fields}
        return self.with_context(**context_fields)
    
    def with_request(self, request_id: str, **request_fields) -> 'BoundStructuredLogger':
        """Create a bound logger with request context."""
        context_fields = {"request_id": request_id, **request_fields}
        return self.with_context(**context_fields)
    
    # ========================================================================
    # PERFORMANCE AND STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logger performance statistics."""
        with self._lock:
            stats = {
                "name": self.name,
                "messages_logged": self._messages_logged,
                "bytes_generated": self._bytes_generated,
                "min_level": self.min_level.name,
                "include_source": self.include_source,
                "include_thread_info": self.include_thread_info,
                "has_orjson": HAS_ORJSON,
            }
            
            if self.pipeline:
                pipeline_stats = getattr(self.pipeline, 'get_stats', lambda: {})()
                stats["pipeline_stats"] = pipeline_stats
            
            return stats
    
    def reset_stats(self) -> None:
        """Reset performance counters."""
        with self._lock:
            self._messages_logged = 0
            self._bytes_generated = 0


class BoundStructuredLogger:
    """
    A structured logger bound to specific context.
    
    This logger automatically includes bound context in all log messages,
    making it perfect for request-scoped or user-scoped logging.
    """
    
    def __init__(self, base_logger: StructuredLogger, bound_context: LogContext):
        """
        Initialize bound logger.
        
        Args:
            base_logger: The base structured logger
            bound_context: Context to include in all messages
        """
        self.base_logger = base_logger
        self.bound_context = bound_context
        
        # Extract common context fields for efficiency
        self._context_fields = {}
        if bound_context.custom:
            self._context_fields.update(bound_context.custom)
        
        if bound_context.trace_id:
            self._context_fields["trace_id"] = bound_context.trace_id
        if bound_context.user_id:
            self._context_fields["user_id"] = bound_context.user_id
        if bound_context.request_id:
            self._context_fields["request_id"] = bound_context.request_id
    
    def _merge_fields(self, **fields) -> Dict[str, Any]:
        """Merge bound context with provided fields."""
        merged = self._context_fields.copy()
        merged.update(fields)
        return merged
    
    # Delegate all logging methods to base logger with context
    def debug(self, message: str, **fields) -> None:
        self.base_logger.debug(message, **self._merge_fields(**fields))
    
    def info(self, message: str, **fields) -> None:
        self.base_logger.info(message, **self._merge_fields(**fields))
    
    def warning(self, message: str, **fields) -> None:
        self.base_logger.warning(message, **self._merge_fields(**fields))
    
    def warn(self, message: str, **fields) -> None:
        self.base_logger.warning(message, **self._merge_fields(**fields))
    
    def error(self, message: str, **fields) -> None:
        self.base_logger.error(message, **self._merge_fields(**fields))
    
    def critical(self, message: str, **fields) -> None:
        self.base_logger.critical(message, **self._merge_fields(**fields))
    
    def fatal(self, message: str, **fields) -> None:
        self.base_logger.critical(message, **self._merge_fields(**fields))
    
    # Specialized methods
    def metric(self, metric_name: str, value: Union[int, float], **fields) -> None:
        self.base_logger.metric(metric_name, value, **self._merge_fields(**fields))
    
    def counter(self, counter_name: str, increment: int = 1, **fields) -> None:
        self.base_logger.counter(counter_name, increment, **self._merge_fields(**fields))
    
    def timer(self, operation: str, duration_ms: float, **fields) -> None:
        self.base_logger.timer(operation, duration_ms, **self._merge_fields(**fields))
    
    def event(self, event_name: str, **fields) -> None:
        self.base_logger.event(event_name, **self._merge_fields(**fields))
    
    def audit(self, action: str, resource: str, **fields) -> None:
        self.base_logger.audit(action, resource, **self._merge_fields(**fields))
    
    def request(self, method: str, path: str, status_code: int, duration_ms: float, **fields) -> None:
        self.base_logger.request(method, path, status_code, duration_ms, **self._merge_fields(**fields))
    
    def security(self, event_type: str, severity: str = "info", **fields) -> None:
        self.base_logger.security(event_type, severity, **self._merge_fields(**fields))
    
    # Context management
    def with_context(self, **context_fields) -> 'BoundStructuredLogger':
        """Create a new bound logger with additional context."""
        return self.base_logger.with_context(**self._merge_fields(**context_fields))


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_structured_logger(
    name: str,
    pipeline: Optional[Any] = None,
    min_level: LogLevel = LogLevel.INFO,
    include_source: bool = False,
    include_thread_info: bool = True,
    base_context: Optional[LogContext] = None,
) -> StructuredLogger:
    """
    Create a high-performance structured logger.
    
    Args:
        name: Logger name/identifier
        pipeline: Pipeline to send log records to
        min_level: Minimum log level to process
        include_source: Whether to capture source location (impacts performance)
        include_thread_info: Whether to include thread information
        base_context: Base context added to all log entries
    
    Returns:
        StructuredLogger instance optimized for key-value logging
    
    Example:
        logger = create_structured_logger("my_service")
        logger.info("User action", user_id=123, action="login", success=True)
    """
    return StructuredLogger(
        name=name,
        pipeline=pipeline,
        min_level=min_level,
        include_source=include_source,
        include_thread_info=include_thread_info,
        base_context=base_context
    )


def create_high_performance_structured_logger(
    name: str,
    pipeline: Optional[Any] = None,
    min_level: LogLevel = LogLevel.INFO
) -> StructuredLogger:
    """
    Create a structured logger optimized for maximum performance.
    
    This logger disables expensive features like source location capture
    and minimizes overhead for high-throughput scenarios.
    
    Args:
        name: Logger name/identifier
        pipeline: Pipeline to send log records to
        min_level: Minimum log level to process
    
    Returns:
        StructuredLogger instance optimized for maximum performance
    """
    return StructuredLogger(
        name=name,
        pipeline=pipeline,
        min_level=min_level,
        include_source=False,  # Disable for performance
        include_thread_info=False,  # Disable for performance
        base_context=None
    )
