"""
Functional logging pipeline components.

This module implements a high-performance, functional pipeline architecture where
log records flow through a series of pure functions:

1. Enrichers: Add context and metadata to log records
2. Filters: Determine if a log record should be processed
3. Formatters: Convert log records to output strings
4. Writers: Send formatted logs to destinations

All components are stateless functions, making the system highly predictable,
testable, and performant.
"""

from typing import Callable, Any, Union, Tuple, Optional
from dataclasses import dataclass
import sys
import os
import threading
import traceback
import json
from pathlib import Path

from .records import LogRecord, LogContext, LogLevel


# Type definitions for pipeline functions
Enricher = Callable[[LogRecord], LogRecord]
Filter = Callable[[LogRecord], bool] 
Formatter = Callable[[LogRecord], str]
Writer = Callable[[str], None]


@dataclass(frozen=True)
class PipelineConfig:
    """Immutable configuration for a logging pipeline."""
    min_level: LogLevel = LogLevel.INFO
    enrichers: Tuple[Enricher, ...] = ()
    filters: Tuple[Filter, ...] = ()
    formatter: Optional[Formatter] = None
    writers: Tuple[Writer, ...] = ()
    
    def __post_init__(self) -> None:
        """Validate the pipeline configuration."""
        if not self.formatter:
            object.__setattr__(self, 'formatter', default_json_formatter)
        if not self.writers:
            object.__setattr__(self, 'writers', (console_writer,))


class Pipeline:
    """
    Functional logging pipeline that processes log records.
    
    The pipeline is immutable once created and processes records through
    a series of pure functions. This design provides:
    - Predictable behavior (no hidden state)
    - High performance (minimal allocations)
    - Thread safety (no shared mutable state)
    - Easy testing (pure functions)
    """
    
    def __init__(self, config: PipelineConfig):
        self.config = config
    
    def process(self, record: LogRecord) -> None:
        """
        Process a log record through the pipeline.
        
        This is the hot path - optimized for minimal CPU cycles and allocations.
        """
        # Fast level check first (avoid unnecessary work)
        if record.level < self.config.min_level:
            return
        
        # Apply enrichers (chain immutable transformations)
        enriched_record = record
        for enricher in self.config.enrichers:
            enriched_record = enricher(enriched_record)
        
        # Apply filters
        for filter_func in self.config.filters:
            if not filter_func(enriched_record):
                return
        
        # Format the record
        formatted_message = self.config.formatter(enriched_record)
        
        # Write to all destinations
        for writer in self.config.writers:
            try:
                writer(formatted_message)
            except (OSError, UnicodeError, ValueError) as e:
                # Never let writer errors crash the application
                # Log writer failures to stderr for debugging
                try:
                    import sys
                    print(f"[MYLOGS-WRITER-ERROR] Writer failed: {e}", file=sys.stderr)
                except Exception:
                    pass  # Even error reporting failed - continue silently
    
    def with_enricher(self, enricher: Enricher) -> 'Pipeline':
        """Create a new pipeline with an additional enricher."""
        new_enrichers = self.config.enrichers + (enricher,)
        new_config = PipelineConfig(
            min_level=self.config.min_level,
            enrichers=new_enrichers,
            filters=self.config.filters,
            formatter=self.config.formatter,
            writers=self.config.writers
        )
        return Pipeline(new_config)
    
    def with_filter(self, filter_func: Filter) -> 'Pipeline':
        """Create a new pipeline with an additional filter."""
        new_filters = self.config.filters + (filter_func,)
        new_config = PipelineConfig(
            min_level=self.config.min_level,
            enrichers=self.config.enrichers,
            filters=new_filters,
            formatter=self.config.formatter,
            writers=self.config.writers
        )
        return Pipeline(new_config)
    
    def with_writer(self, writer: Writer) -> 'Pipeline':
        """Create a new pipeline with an additional writer."""
        new_writers = self.config.writers + (writer,)
        new_config = PipelineConfig(
            min_level=self.config.min_level,
            enrichers=self.config.enrichers,
            filters=self.config.filters,
            formatter=self.config.formatter,
            writers=new_writers
        )
        return Pipeline(new_config)


# ============================================================================
# BUILT-IN ENRICHERS
# ============================================================================

def thread_enricher(record: LogRecord) -> LogRecord:
    """Add current thread information to log record."""
    current_thread = threading.current_thread()
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
        thread_id=current_thread.ident,
        thread_name=current_thread.name,
        process_id=os.getpid(),
    )


def exception_enricher(record: LogRecord) -> LogRecord:
    """Add exception traceback if an exception is present."""
    if record.exception and not record.exception_traceback:
        tb = traceback.format_exception(
            type(record.exception),
            record.exception,
            record.exception.__traceback__
        )
        return LogRecord(
            timestamp=record.timestamp,
            level=record.level,
            logger_name=record.logger_name,
            message=record.message,
            fields=record.fields,
            context=record.context,
            exception=record.exception,
            exception_traceback=''.join(tb),
            module=record.module,
            function=record.function,
            line_number=record.line_number,
            thread_id=record.thread_id,
            thread_name=record.thread_name,
            process_id=record.process_id,
        )
    return record


def context_enricher(base_context: LogContext) -> Enricher:
    """Create an enricher that adds base context to all records."""
    def enricher(record: LogRecord) -> LogRecord:
        if record.context:
            merged_context = base_context.merge(record.context)
        else:
            merged_context = base_context
        
        return record.with_context(merged_context)
    return enricher


# ============================================================================
# BUILT-IN FILTERS
# ============================================================================

def level_filter(min_level: LogLevel) -> Filter:
    """Create a filter that only allows records at or above the specified level."""
    def filter_func(record: LogRecord) -> bool:
        return record.level >= min_level
    return filter_func


def field_filter(field_name: str, expected_value: Any) -> Filter:
    """Create a filter that only allows records with a specific field value."""
    def filter_func(record: LogRecord) -> bool:
        if not record.fields:
            return False
        return record.fields.get(field_name) == expected_value
    return filter_func


def logger_name_filter(allowed_names: set[str]) -> Filter:
    """Create a filter that only allows records from specific loggers."""
    def filter_func(record: LogRecord) -> bool:
        return record.logger_name in allowed_names
    return filter_func


# ============================================================================
# BUILT-IN FORMATTERS
# ============================================================================

def default_json_formatter(record: LogRecord) -> str:
    """High-performance JSON formatter optimized for structured logging."""
    # Use the built-in to_dict method for consistency
    data = record.to_dict()
    
    # Use json.dumps with separators for compact output
    return json.dumps(data, separators=(',', ':'), ensure_ascii=False, default=str)


def simple_text_formatter(record: LogRecord) -> str:
    """Simple text formatter for human-readable output."""
    timestamp = record.datetime.strftime('%H:%M:%S.%f')[:-3]  # Include milliseconds
    
    # Get context info
    context_parts = []
    if record.context:
        if record.context.ip:
            context_parts.append(f"IP:{record.context.ip}")
        if record.context.access:
            context_parts.append(f"ACCESS:{record.context.access}")
        if record.context.user_id:
            context_parts.append(f"USER:{record.context.user_id}")
    
    context_str = " | ".join(context_parts) if context_parts else "N/A"
    
    base_msg = f"{timestamp} | {record.level.name:8s} | {record.logger_name} | {context_str} | {record.message}"
    
    # Add fields if present
    if record.fields:
        fields_str = " | ".join(f"{k}={v}" for k, v in record.fields.items())
        base_msg += f" | {fields_str}"
    
    # Add exception if present
    if record.exception:
        base_msg += f"\nException: {type(record.exception).__name__}: {record.exception}"
        if record.exception_traceback:
            base_msg += f"\n{record.exception_traceback}"
    
    return base_msg


def compact_formatter(record: LogRecord) -> str:
    """Ultra-compact formatter for resource-constrained environments."""
    timestamp = record.datetime.strftime('%H:%M:%S')
    return f"{timestamp} | {record.level.name[0]} | {record.message}"


def detailed_formatter(record: LogRecord) -> str:
    """Detailed formatter with all available information."""
    timestamp = record.datetime.isoformat()
    
    parts = [
        f"[{timestamp}]",
        f"[{record.level.name}]",
        f"[{record.logger_name}]",
    ]
    
    if record.thread_id:
        parts.append(f"[T:{record.thread_id}]")
    if record.process_id:
        parts.append(f"[P:{record.process_id}]")
    if record.module:
        parts.append(f"[{record.module}:{record.line_number or '?'}]")
    
    parts.append(record.message)
    
    result = " ".join(parts)
    
    if record.fields:
        result += " | Fields: " + json.dumps(record.fields, separators=(',', ':'))
    
    if record.context and (record.context.ip or record.context.user_id):
        context_info = []
        if record.context.ip:
            context_info.append(f"ip={record.context.ip}")
        if record.context.user_id:
            context_info.append(f"user={record.context.user_id}")
        result += " | Context: " + ",".join(context_info)
    
    return result


# ============================================================================
# BUILT-IN WRITERS
# ============================================================================

def console_writer(message: str) -> None:
    """Write message to stdout."""
    print(message, flush=True)


def stderr_writer(message: str) -> None:
    """Write message to stderr."""
    print(message, file=sys.stderr, flush=True)


def file_writer(file_path: Union[str, Path]) -> Writer:
    """Create a writer that appends messages to a file."""
    path = Path(file_path)
    
    def writer(message: str) -> None:
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append message with newline
        with open(path, 'a', encoding='utf-8') as f:
            f.write(message + '\n')
            f.flush()
    
    return writer


def null_writer(message: str) -> None:
    """Null writer that discards all messages (for testing)."""
    pass


# ============================================================================
# PIPELINE FACTORY FUNCTIONS
# ============================================================================

def create_console_pipeline(
    min_level: LogLevel = LogLevel.INFO,
    formatter: Formatter = simple_text_formatter,
    include_thread_info: bool = True,
) -> Pipeline:
    """Create a pipeline that logs to console with sensible defaults."""
    enrichers = []
    if include_thread_info:
        enrichers.append(thread_enricher)
    enrichers.append(exception_enricher)
    
    config = PipelineConfig(
        min_level=min_level,
        enrichers=tuple(enrichers),
        filters=(),
        formatter=formatter,
        writers=(console_writer,)
    )
    return Pipeline(config)


def create_file_pipeline(
    file_path: Union[str, Path],
    min_level: LogLevel = LogLevel.DEBUG,
    formatter: Formatter = default_json_formatter,
    include_thread_info: bool = True,
) -> Pipeline:
    """Create a pipeline that logs to a file."""
    enrichers = []
    if include_thread_info:
        enrichers.append(thread_enricher)
    enrichers.append(exception_enricher)
    
    config = PipelineConfig(
        min_level=min_level,
        enrichers=tuple(enrichers),
        filters=(),
        formatter=formatter,
        writers=(file_writer(file_path),)
    )
    return Pipeline(config)


def create_dual_pipeline(
    file_path: Union[str, Path],
    console_level: LogLevel = LogLevel.INFO,
    file_level: LogLevel = LogLevel.DEBUG,
    console_formatter: Formatter = simple_text_formatter,
    file_formatter: Formatter = default_json_formatter,
) -> Pipeline:
    """Create a pipeline that logs to both console and file with different levels."""
    enrichers = (thread_enricher, exception_enricher)
    
    # Create separate pipelines for console and file, then combine writers
    console_pipeline = Pipeline(PipelineConfig(
        min_level=console_level,
        enrichers=enrichers,
        filters=(),
        formatter=console_formatter,
        writers=(console_writer,)
    ))
    
    file_pipeline = Pipeline(PipelineConfig(
        min_level=file_level,
        enrichers=enrichers,
        filters=(),
        formatter=file_formatter,
        writers=(file_writer(file_path),)
    ))
    
    # For dual pipeline, we need a custom implementation
    class DualPipeline(Pipeline):
        def __init__(self):
            # Use the lower level as the base
            min_level = min(console_level, file_level)
            super().__init__(PipelineConfig(min_level=min_level))
            self.console_pipeline = console_pipeline
            self.file_pipeline = file_pipeline
        
        def process(self, record: LogRecord) -> None:
            # Process through both pipelines
            if record.level >= console_level:
                self.console_pipeline.process(record)
            if record.level >= file_level:
                self.file_pipeline.process(record)
    
    return DualPipeline()
