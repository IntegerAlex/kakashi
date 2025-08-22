"""
High-performance formatters optimized for structured logging.

This module provides formatters specifically designed for structured logging
with orjson integration, machine-readable output, and optimal performance
for modern log analysis platforms.

Key features:
- orjson-powered JSON formatting for maximum speed
- Structured data preservation
- Machine-readable output optimized for analysis
- Minimal overhead formatting options
- Custom field handling and serialization
- Cloud-native and observability platform integration
"""

import json
from typing import Any, Dict, Callable
from datetime import datetime

from .records import LogRecord, LogLevel
from .structured_logger import fast_json_serialize_str, HAS_ORJSON


# ============================================================================
# STRUCTURED FORMATTERS
# ============================================================================

def optimized_json_formatter(record: LogRecord) -> str:
    """
    Ultra-fast JSON formatter using orjson optimizations.
    
    This is the default formatter for structured logging, optimized
    for maximum performance and machine readability.
    
    Args:
        record: Log record to format
    
    Returns:
        JSON string optimized for log analysis platforms
    """
    # Build structured entry optimized for serialization
    entry = {
        "@timestamp": datetime.fromtimestamp(record.timestamp).isoformat() + "Z",
        "level": record.level.name,
        "message": record.message,
    }
    
    # Add fields efficiently
    if record.fields:
        entry.update(record.fields)
    
    # Add context information
    if record.context:
        if record.context.service_name:
            entry["service"] = record.context.service_name
        if record.context.version:
            entry["version"] = record.context.version
        if record.context.environment:
            entry["environment"] = record.context.environment
        if record.context.trace_id:
            entry["trace_id"] = record.context.trace_id
        if record.context.user_id:
            entry["user_id"] = record.context.user_id
        if record.context.request_id:
            entry["request_id"] = record.context.request_id
        if record.context.custom:
            entry.update(record.context.custom)
    
    # Add source information if available
    if hasattr(record, 'source_file') and record.source_file:
        entry["source"] = {
            "file": record.source_file,
            "line": getattr(record, 'source_line', None),
            "function": getattr(record, 'source_function', None)
        }
    
    # Add thread information if available
    if record.thread_id:
        entry["thread"] = {
            "id": record.thread_id,
            "name": record.thread_name
        }
    
    # Logger name
    if record.logger_name:
        entry["logger"] = record.logger_name
    
    return fast_json_serialize_str(entry)


def minimal_json_formatter(record: LogRecord) -> str:
    """
    Minimal JSON formatter for high-performance scenarios.
    
    This formatter includes only essential fields to minimize
    serialization overhead and output size.
    
    Args:
        record: Log record to format
    
    Returns:
        Minimal JSON string
    """
    entry = {
        "ts": record.timestamp,
        "lvl": record.level.name[0],  # Single letter level
        "msg": record.message,
    }
    
    # Add fields directly
    if record.fields:
        entry.update(record.fields)
    
    # Add minimal context
    if record.context and record.context.trace_id:
        entry["tid"] = record.context.trace_id
    if record.context and record.context.user_id:
        entry["uid"] = record.context.user_id
    
    return fast_json_serialize_str(entry)


def elk_stack_formatter(record: LogRecord) -> str:
    """
    Formatter optimized for ELK Stack (Elasticsearch, Logstash, Kibana).
    
    This formatter produces output specifically optimized for the
    Elastic Stack ecosystem with proper field naming and structure.
    
    Args:
        record: Log record to format
    
    Returns:
        ELK-optimized JSON string
    """
    # Use ELK-standard field names
    entry = {
        "@timestamp": datetime.fromtimestamp(record.timestamp).isoformat() + "Z",
        "@version": "1",
        "level": record.level.name.lower(),
        "message": record.message,
        "host": {
            "name": "unknown"  # Could be populated from environment
        }
    }
    
    # Add structured fields under 'fields' namespace (Logstash convention)
    if record.fields:
        entry["fields"] = record.fields
    
    # Add service information
    if record.context:
        service_info = {}
        if record.context.service_name:
            service_info["name"] = record.context.service_name
        if record.context.version:
            service_info["version"] = record.context.version
        if record.context.environment:
            service_info["environment"] = record.context.environment
        if service_info:
            entry["service"] = service_info
    
    # Add tracing information (APM compatible)
    if record.context and record.context.trace_id:
        entry["trace"] = {"id": record.context.trace_id}
        if record.context.span_id:
            entry["trace"]["span_id"] = record.context.span_id
    
    # Add user context
    if record.context and record.context.user_id:
        entry["user"] = {"id": record.context.user_id}
    
    # Add source location for debugging
    if hasattr(record, 'source_file') and record.source_file:
        entry["log"] = {
            "file": {
                "path": record.source_file,
                "line": getattr(record, 'source_line', None)
            },
            "function": getattr(record, 'source_function', None)
        }
    
    return fast_json_serialize_str(entry)


def splunk_formatter(record: LogRecord) -> str:
    """
    Formatter optimized for Splunk ingestion.
    
    This formatter produces output compatible with Splunk's
    preferred JSON structure and field naming conventions.
    
    Args:
        record: Log record to format
    
    Returns:
        Splunk-optimized JSON string
    """
    # Splunk prefers epoch time
    entry = {
        "time": record.timestamp,
        "severity": record.level.name,
        "message": record.message,
    }
    
    # Add all fields at root level (Splunk-friendly)
    if record.fields:
        # Prefix custom fields to avoid conflicts
        for key, value in record.fields.items():
            entry[f"field_{key}"] = value
    
    # Service metadata
    if record.context:
        if record.context.service_name:
            entry["sourcetype"] = record.context.service_name
        if record.context.environment:
            entry["environment"] = record.context.environment
        if record.context.version:
            entry["version"] = record.context.version
    
    # Tracing (compatible with Splunk APM)
    if record.context and record.context.trace_id:
        entry["trace_id"] = record.context.trace_id
    if record.context and record.context.span_id:
        entry["span_id"] = record.context.span_id
    
    # User information
    if record.context and record.context.user_id:
        entry["user"] = record.context.user_id
    
    # Logger information
    if record.logger_name:
        entry["logger"] = record.logger_name
    
    # Thread information (useful for debugging)
    if record.thread_id:
        entry["thread"] = f"{record.thread_name}_{record.thread_id}"
    
    return fast_json_serialize_str(entry)


def prometheus_logs_formatter(record: LogRecord) -> str:
    """
    Formatter compatible with Prometheus/Grafana Loki log format.
    
    This formatter produces output optimized for Grafana Loki
    and Prometheus-based observability stacks.
    
    Args:
        record: Log record to format
    
    Returns:
        Prometheus/Loki-compatible JSON string
    """
    # Grafana Loki preferred format
    entry = {
        "timestamp": int(record.timestamp * 1000000000),  # Nanoseconds
        "level": record.level.name.lower(),
        "msg": record.message,
    }
    
    # Add labels (for Loki stream identification)
    labels = {}
    if record.context:
        if record.context.service_name:
            labels["service"] = record.context.service_name
        if record.context.environment:
            labels["env"] = record.context.environment
        if record.context.version:
            labels["version"] = record.context.version
    
    if labels:
        entry["labels"] = labels
    
    # Add structured fields
    if record.fields:
        entry.update(record.fields)
    
    # Tracing information
    if record.context and record.context.trace_id:
        entry["traceID"] = record.context.trace_id  # Jaeger/Tempo compatibility
    
    return fast_json_serialize_str(entry)


def datadog_formatter(record: LogRecord) -> str:
    """
    Formatter optimized for Datadog log ingestion.
    
    This formatter produces output compatible with Datadog's
    log structure and attribute naming conventions.
    
    Args:
        record: Log record to format
    
    Returns:
        Datadog-compatible JSON string
    """
    entry = {
        "timestamp": int(record.timestamp * 1000),  # Milliseconds
        "status": record.level.name.lower(),
        "message": record.message,
    }
    
    # Service tags (Datadog APM integration)
    if record.context:
        if record.context.service_name:
            entry["service"] = record.context.service_name
        if record.context.version:
            entry["version"] = record.context.version
        if record.context.environment:
            entry["env"] = record.context.environment
    
    # Custom attributes
    if record.fields:
        # Use Datadog's @ prefix for custom attributes
        for key, value in record.fields.items():
            entry[f"@{key}"] = value
    
    # Tracing (APM correlation)
    if record.context and record.context.trace_id:
        entry["dd.trace_id"] = record.context.trace_id
    if record.context and record.context.span_id:
        entry["dd.span_id"] = record.context.span_id
    
    # User tracking
    if record.context and record.context.user_id:
        entry["usr.id"] = record.context.user_id
    
    # Logger source
    if record.logger_name:
        entry["logger.name"] = record.logger_name
    
    # Source location
    if hasattr(record, 'source_file') and record.source_file:
        entry["logger.file_name"] = record.source_file
        entry["logger.line"] = getattr(record, 'source_line', None)
    
    return fast_json_serialize_str(entry)


def opentelemetry_formatter(record: LogRecord) -> str:
    """
    Formatter compatible with OpenTelemetry log format.
    
    This formatter produces output following OpenTelemetry
    semantic conventions for logs.
    
    Args:
        record: Log record to format
    
    Returns:
        OpenTelemetry-compatible JSON string
    """
    # OpenTelemetry log record format
    entry = {
        "timestamp": int(record.timestamp * 1000000000),  # Nanoseconds
        "severity_number": _get_otel_severity_number(record.level),
        "severity_text": record.level.name,
        "body": record.message,
    }
    
    # Resource attributes
    resource = {}
    if record.context:
        if record.context.service_name:
            resource["service.name"] = record.context.service_name
        if record.context.version:
            resource["service.version"] = record.context.version
        if record.context.environment:
            resource["deployment.environment"] = record.context.environment
    
    if resource:
        entry["resource"] = resource
    
    # Attributes (structured fields)
    if record.fields:
        entry["attributes"] = record.fields
    
    # Trace context
    if record.context and record.context.trace_id:
        entry["trace_id"] = record.context.trace_id
    if record.context and record.context.span_id:
        entry["span_id"] = record.context.span_id
    
    # Instrumentation scope
    if record.logger_name:
        entry["instrumentation_scope"] = {
            "name": record.logger_name
        }
    
    return fast_json_serialize_str(entry)


def _get_otel_severity_number(level: LogLevel) -> int:
    """Get OpenTelemetry severity number for log level."""
    severity_map = {
        LogLevel.DEBUG: 5,
        LogLevel.INFO: 9,
        LogLevel.WARNING: 13,
        LogLevel.ERROR: 17,
        LogLevel.CRITICAL: 21,
    }
    return severity_map.get(level, 9)


# ============================================================================
# COMPACT FORMATTERS FOR HIGH-THROUGHPUT
# ============================================================================

def ultra_compact_formatter(record: LogRecord) -> str:
    """
    Ultra-compact formatter for maximum throughput scenarios.
    
    This formatter produces the smallest possible output while
    maintaining structured logging benefits.
    
    Args:
        record: Log record to format
    
    Returns:
        Ultra-compact JSON string
    """
    # Use single-character keys
    entry = {
        "t": int(record.timestamp),
        "l": record.level.value,  # Numeric level
        "m": record.message[:100],  # Truncate message
    }
    
    # Add only essential fields
    if record.fields:
        # Truncate field names and values
        essential_fields = {}
        for key, value in list(record.fields.items())[:5]:  # Max 5 fields
            short_key = key[:10]  # Truncate key
            if isinstance(value, str) and len(value) > 50:
                essential_fields[short_key] = value[:50] + "..."
            else:
                essential_fields[short_key] = value
        entry["f"] = essential_fields
    
    # Minimal context
    # Minimal context with safe attribute access
    if record.context and hasattr(record.context, 'trace_id') and record.context.trace_id:
        entry["tid"] = record.context.trace_id[:8]  # Truncate trace ID
    
    return fast_json_serialize_str(entry)


def binary_efficient_formatter(record: LogRecord) -> bytes:
    """
    Binary-efficient formatter returning bytes directly.
    
    This formatter skips string conversion to provide maximum
    performance for binary sinks.
    
    Args:
        record: Log record to format
    
    Returns:
        JSON bytes
    """
    entry = {
        "timestamp": record.timestamp,
        "level": record.level.value,
        "message": record.message,
    }
    
    if record.fields:
        entry["fields"] = record.fields
    
    # Use orjson directly for bytes output
    if HAS_ORJSON:
        import orjson
        return orjson.dumps(entry, option=orjson.OPT_UTC_Z)
    else:
        return json.dumps(entry, separators=(',', ':')).encode('utf-8')


# ============================================================================
# CUSTOM FIELD PROCESSORS
# ============================================================================

def sanitize_sensitive_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize sensitive fields in log data.
    
    Args:
        fields: Original fields dictionary
    
    Returns:
        Sanitized fields dictionary
    """
    # Use frozenset for better performance
    sensitive_keys = frozenset({
        'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'auth',
        'credit_card', 'ccn', 'ssn', 'social_security', 'api_key',
        'private_key', 'certificate', 'cookie', 'session', 'authorization'
    })
    
    # Pre-filter sensitive keys for substring matching (only keys longer than 2 chars)
    substring_keys = frozenset(key for key in sensitive_keys if len(key) > 2)
    
    sanitized = {}
    for key, value in fields.items():
        key_lower = key.lower()
        # Efficient check: exact match first, then optimized substring check
        if key_lower in sensitive_keys:
            sanitized[key] = "[REDACTED]"
        elif any(sensitive in key_lower for sensitive in substring_keys):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    
    return sanitized


def truncate_large_fields(fields: Dict[str, Any], max_size: int = 1000) -> Dict[str, Any]:
    """
    Truncate large field values to prevent oversized logs.
    
    Args:
        fields: Original fields dictionary
        max_size: Maximum size for field values
    
    Returns:
        Truncated fields dictionary
    """
    truncated = {}
    for key, value in fields.items():
        if isinstance(value, str) and len(value) > max_size:
            truncated[key] = value[:max_size] + f"... [TRUNCATED, was {len(value)} chars]"
        elif isinstance(value, (list, dict)) and len(str(value)) > max_size:
            truncated[key] = f"[LARGE_{type(value).__name__.upper()}_TRUNCATED]"
        else:
            truncated[key] = value
    
    return truncated


# ============================================================================
# FORMATTER REGISTRY
# ============================================================================

STRUCTURED_FORMATTERS = {
    # Default formatters
    "default": optimized_json_formatter,
    "json": optimized_json_formatter,
    "minimal": minimal_json_formatter,
    "compact": ultra_compact_formatter,
    
    # Platform-specific formatters
    "elk": elk_stack_formatter,
    "elasticsearch": elk_stack_formatter,
    "splunk": splunk_formatter,
    "datadog": datadog_formatter,
    "prometheus": prometheus_logs_formatter,
    "loki": prometheus_logs_formatter,
    "opentelemetry": opentelemetry_formatter,
    "otel": opentelemetry_formatter,
    
    # Performance formatters
    "ultra_compact": ultra_compact_formatter,
    "high_performance": minimal_json_formatter,
}


def get_structured_formatter(name: str) -> Callable[[LogRecord], str]:
    """
    Get a structured formatter by name.
    
    Args:
        name: Formatter name
    
    Returns:
        Formatter function
    
    Raises:
        ValueError: If formatter not found
    """
    formatter = STRUCTURED_FORMATTERS.get(name)
    if not formatter:
        available = ", ".join(STRUCTURED_FORMATTERS.keys())
        raise ValueError(f"Unknown formatter '{name}'. Available: {available}")
    return formatter


def register_structured_formatter(name: str, formatter: Callable[[LogRecord], str]) -> None:
    """
    Register a custom structured formatter.
    
    Args:
        name: Formatter name
        formatter: Formatter function
    """
    STRUCTURED_FORMATTERS[name] = formatter
