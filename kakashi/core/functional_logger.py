"""
High-performance functional logger implementation.

This module implements the core Logger class that replaces the old
stateful logging system with a functional, pipeline-based approach.
The logger is a lightweight wrapper around an immutable configuration
and pipeline that processes log records through pure functions.
"""

import sys
import time
import traceback
from typing import Optional, Dict, Any, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import LoggerConfig

from .records import LogRecord, LogContext, LogLevel
from .config import LoggerConfig, get_current_context


class FunctionalLogger:
    """
    High-performance functional logger.
    
    This logger is designed for maximum performance and minimal memory footprint:
    - No global state or singletons
    - Immutable configuration
    - Minimal object creation in hot path
    - Fast level checks to avoid unnecessary work
    - Pure functional pipeline processing
    
    The logger itself is just a thin wrapper around the pipeline configuration.
    All the real work happens in the pure functions of the pipeline.
    """
    
    __slots__ = ('_config', '_name', '_min_level', '_pipeline', '_capture_source', '_capture_exceptions')
    
    def __init__(self, config: 'LoggerConfig') -> None:
        """
        Initialize functional logger with immutable configuration.
        
        Args:
            config: Immutable LoggerConfig containing pipeline and settings
        """
        self._config = config
        self._name = config.name
        self._pipeline = config.pipeline
        self._min_level = config.pipeline.config.min_level
        self._capture_source = config.capture_source
        self._capture_exceptions = config.capture_exceptions
    
    @property
    def name(self) -> str:
        """Get the logger name."""
        return self._name
    
    @property
    def config(self) -> 'LoggerConfig':
        """Get the logger configuration (immutable)."""
        return self._config
    
    def is_enabled_for(self, level: Union[LogLevel, str, int]) -> bool:
        """
        Fast check if logging is enabled for a given level.
        
        This is optimized to be as fast as possible since it's called
        on every logging attempt.
        """
        if isinstance(level, str):
            level = LogLevel.from_name(level)
        elif isinstance(level, int):
            level = LogLevel(level)
        
        return level >= self._min_level
    
    def _create_record(
        self,
        level: LogLevel,
        message: str,
        fields: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        timestamp: Optional[float] = None
    ) -> LogRecord:
        """
        Create a log record with automatic context and source location.
        
        This method is optimized for speed:
        - Minimal allocations
        - Fast timestamp generation
        - Optional source location capture
        - Context merging
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Get source location if enabled (can be expensive)
        module = None
        function = None
        line_number = None
        
        if self._capture_source:
            frame = sys._getframe(2)  # Skip _create_record and the public method
            module = frame.f_globals.get('__name__')
            function = frame.f_code.co_name
            line_number = frame.f_lineno
        
        # Get current context and merge with base context
        current_context = get_current_context()
        final_context = None
        
        if self._config.base_context or current_context:
            if self._config.base_context and current_context:
                final_context = self._config.base_context.merge(current_context)
            else:
                final_context = self._config.base_context or current_context
        
        # Handle exception traceback if needed
        exception_traceback = None
        if exception and self._capture_exceptions:
            try:
                exception_traceback = ''.join(traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                ))
            except (OSError, ValueError, RecursionError):
                # Don't let traceback formatting crash the logger
                exception_traceback = f"Failed to format traceback for {type(exception).__name__}"
        
        return LogRecord(
            timestamp=timestamp,
            level=level,
            logger_name=self._name,
            message=message,
            fields=fields,
            context=final_context,
            exception=exception,
            exception_traceback=exception_traceback,
            module=module,
            function=function,
            line_number=line_number,
            # Thread info is added by enrichers in the pipeline
        )
    
    def log(
        self,
        level: Union[LogLevel, str, int],
        message: str,
        *,
        fields: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a message at the specified level.
        
        This is the core logging method that all other methods delegate to.
        It's optimized for speed with early returns and minimal work.
        
        Args:
            level: Log level
            message: Log message
            fields: Optional structured data fields
            exception: Optional exception to include
            **kwargs: Additional fields (merged with fields dict)
        """
        # Convert level to LogLevel enum
        if isinstance(level, str):
            level = LogLevel.from_name(level)
        elif isinstance(level, int):
            level = LogLevel(level)
        
        # Fast level check - return immediately if logging not enabled
        if not self.is_enabled_for(level):
            return
        
        # Merge kwargs into fields if present
        if kwargs:
            if fields:
                fields = {**fields, **kwargs}
            else:
                fields = kwargs
        
        # Create log record
        record = self._create_record(level, message, fields, exception)
        
        # Process through pipeline
        try:
            self._pipeline.process(record)
        except (OSError, ValueError, UnicodeError):
            # Never let logging errors crash the application
            # In production, you might want to write to stderr or a separate error channel
            pass
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def warn(self, message: str, **kwargs) -> None:
        """Alias for warning (compatibility)."""
        self.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self.log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self.log(LogLevel.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """
        Log an error message with exception information.
        
        This automatically captures the current exception from sys.exc_info().
        """
        exc_info = sys.exc_info()
        if exc_info[1] is not None:
            kwargs['exception'] = exc_info[1]
        self.error(message, **kwargs)
    
    def with_fields(self, **fields) -> 'BoundLogger':
        """
        Create a bound logger with predefined fields.
        
        This creates a new logger that automatically includes the specified
        fields in all log messages.
        
        Returns:
            BoundLogger instance with predefined fields
        """
        return BoundLogger(self, fields)
    
    def with_context(self, context: LogContext) -> 'BoundLogger':
        """
        Create a bound logger with additional context.
        
        Returns:
            BoundLogger instance with additional context
        """
        return BoundLogger(self, {}, context)


class BoundLogger:
    """
    A logger bound to specific fields and/or context.
    
    This allows creating logger instances that automatically include
    certain fields or context in all messages, which is useful for
    request-scoped logging or component-specific logging.
    """
    
    __slots__ = ('_logger', '_bound_fields', '_bound_context')
    
    def __init__(
        self,
        logger: FunctionalLogger,
        bound_fields: Optional[Dict[str, Any]] = None,
        bound_context: Optional[LogContext] = None
    ):
        self._logger = logger
        self._bound_fields = bound_fields or {}
        self._bound_context = bound_context
    
    @property
    def name(self) -> str:
        """Get the underlying logger name."""
        return self._logger.name
    
    def is_enabled_for(self, level: Union[LogLevel, str, int]) -> bool:
        """Check if logging is enabled for a given level."""
        return self._logger.is_enabled_for(level)
    
    def _merge_fields(self, fields: Optional[Dict[str, Any]], **kwargs) -> Optional[Dict[str, Any]]:
        """Merge bound fields with provided fields."""
        if not self._bound_fields and not fields and not kwargs:
            return None
        
        merged = dict(self._bound_fields)  # Start with bound fields
        if fields:
            merged.update(fields)
        if kwargs:
            merged.update(kwargs)
        
        return merged if merged else None
    
    def _create_record_with_context(self, level: LogLevel, message: str, fields: Optional[Dict[str, Any]], exception: Optional[Exception]) -> LogRecord:
        """Create a log record and add bound context."""
        record = self._logger._create_record(level, message, fields, exception)
        
        if self._bound_context:
            record = record.with_context(self._bound_context)
        
        return record
    
    def log(
        self,
        level: Union[LogLevel, str, int],
        message: str,
        *,
        fields: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """Log a message with bound fields and context."""
        # Convert level
        if isinstance(level, str):
            level = LogLevel.from_name(level)
        elif isinstance(level, int):
            level = LogLevel(level)
        
        # Fast level check
        if not self.is_enabled_for(level):
            return
        
        # Merge fields
        merged_fields = self._merge_fields(fields, **kwargs)
        
        # If we have bound context, we need to create the record manually
        if self._bound_context:
            record = self._create_record_with_context(level, message, merged_fields, exception)
            try:
                self._logger._pipeline.process(record)
            except Exception:
                pass
        else:
            # No bound context, delegate to main logger
            self._logger.log(level, message, fields=merged_fields, exception=exception)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def warn(self, message: str, **kwargs) -> None:
        """Alias for warning."""
        self.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self.log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self.log(LogLevel.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log an error message with exception information."""
        exc_info = sys.exc_info()
        if exc_info[1] is not None:
            kwargs['exception'] = exc_info[1]
        self.error(message, **kwargs)
    
    def with_fields(self, **fields) -> 'BoundLogger':
        """Create a new bound logger with additional fields."""
        merged_fields = {**self._bound_fields, **fields}
        return BoundLogger(self._logger, merged_fields, self._bound_context)
    
    def with_context(self, context: LogContext) -> 'BoundLogger':
        """Create a new bound logger with additional context."""
        merged_context = self._bound_context.merge(context) if self._bound_context else context
        return BoundLogger(self._logger, self._bound_fields, merged_context)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_logger(config: LoggerConfig) -> FunctionalLogger:
    """
    Create a functional logger from configuration.
    
    This is the main factory function for creating loggers.
    """
    return FunctionalLogger(config)


# ============================================================================
# CONVENIENCE FUNCTIONS FOR STRUCTURED LOGGING
# ============================================================================

def create_structured_logger(
    name: str,
    config: LoggerConfig,
    **default_fields
) -> BoundLogger:
    """
    Create a logger optimized for structured logging.
    
    This creates a bound logger with default fields that are included
    in every log message, making it ideal for structured logging scenarios.
    """
    logger = create_logger(config)
    return logger.with_fields(**default_fields)


def create_request_logger(
    name: str,
    config: LoggerConfig,
    request_id: str,
    user_id: Optional[str] = None,
    ip: Optional[str] = None,
    **additional_fields
) -> BoundLogger:
    """
    Create a logger bound to request-specific context.
    
    This is useful for web applications where you want all log messages
    within a request to include request-specific information.
    """
    context = LogContext(
        request_id=request_id,
        user_id=user_id,
        ip=ip
    )
    
    logger = create_logger(config)
    bound_logger = logger.with_context(context)
    
    if additional_fields:
        bound_logger = bound_logger.with_fields(**additional_fields)
    
    return bound_logger
