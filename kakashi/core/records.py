"""
Immutable log record data structures for functional logging pipeline.

This module defines the core data structures used throughout the functional
logging system. All structures are immutable for thread safety and predictability.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, Tuple
from enum import IntEnum
from datetime import datetime


class LogLevel(IntEnum):
    """Log levels as integers for fast comparison."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    
    @classmethod
    def from_name(cls, name: str) -> 'LogLevel':
        """Create LogLevel from string name."""
        return cls[name.upper()]
    
    @property
    def name(self) -> str:
        """Get the level name."""
        return self._name_


@dataclass(frozen=True)
class LogContext:
    """Immutable context information that can be attached to log records."""
    # Request/network context
    ip: Optional[str] = None
    access: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    # User context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Application context
    service_name: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    
    # Custom context (immutable dict)
    custom: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Ensure custom dict is immutable after initialization."""
        # Ensure custom dict is immutable
        if self.custom is not None:
            object.__setattr__(self, 'custom', dict(self.custom))  # Create defensive copy
    
    def merge(self, other: 'LogContext') -> 'LogContext':
        """Create a new LogContext by merging this one with another."""
        merged_custom = {**(self.custom or {}), **(other.custom or {})}
        
        return LogContext(
            ip=other.ip or self.ip,
            access=other.access or self.access,
            user_agent=other.user_agent or self.user_agent,
            request_id=other.request_id or self.request_id,
            user_id=other.user_id or self.user_id,
            session_id=other.session_id or self.session_id,
            service_name=other.service_name or self.service_name,
            version=other.version or self.version,
            environment=other.environment or self.environment,
            custom=merged_custom if merged_custom else None
        )
    
    def with_custom(self, **kwargs) -> 'LogContext':
        """Create a new LogContext with additional custom fields."""
        merged_custom = {**(self.custom or {}), **kwargs}
        return LogContext(
            ip=self.ip,
            access=self.access,
            user_agent=self.user_agent,
            request_id=self.request_id,
            user_id=self.user_id,
            session_id=self.session_id,
            service_name=self.service_name,
            version=self.version,
            environment=self.environment,
            custom=merged_custom
        )


@dataclass(frozen=True)
class LogRecord:
    """
    Immutable log record representing a single log event.
    
    This is the core data structure that flows through the entire logging pipeline.
    It's designed to be:
    - Immutable (thread-safe, cacheable, predictable)
    - Fast to create (minimal allocations)
    - Rich enough for any logging use case
    - Compatible with structured logging
    """
    # Core fields (always present)
    timestamp: float  # Unix timestamp with microsecond precision
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
    
    def __post_init__(self) -> None:
        """Ensure fields dict is immutable."""
        if self.fields is not None:
            object.__setattr__(self, 'fields', dict(self.fields))  # Defensive copy
    
    @property
    def datetime(self) -> datetime:
        """Get timestamp as datetime object."""
        return datetime.fromtimestamp(self.timestamp)
    
    @property
    def level_name(self) -> str:
        """Get the level name as string."""
        return self.level.name
    
    def with_context(self, context: LogContext) -> 'LogRecord':
        """Create a new LogRecord with merged context."""
        new_context = self.context.merge(context) if self.context else context
        
        return LogRecord(
            timestamp=self.timestamp,
            level=self.level,
            logger_name=self.logger_name,
            message=self.message,
            fields=self.fields,
            context=new_context,
            exception=self.exception,
            exception_traceback=self.exception_traceback,
            module=self.module,
            function=self.function,
            line_number=self.line_number,
            thread_id=self.thread_id,
            thread_name=self.thread_name,
            process_id=self.process_id
        )
    
    def with_fields(self, **fields) -> 'LogRecord':
        """Create a new LogRecord with additional fields."""
        merged_fields = {**(self.fields or {}), **fields}
        
        return LogRecord(
            timestamp=self.timestamp,
            level=self.level,
            logger_name=self.logger_name,
            message=self.message,
            fields=merged_fields if merged_fields else None,
            context=self.context,
            exception=self.exception,
            exception_traceback=self.exception_traceback,
            module=self.module,
            function=self.function,
            line_number=self.line_number,
            thread_id=self.thread_id,
            thread_name=self.thread_name,
            process_id=self.process_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log record to a dictionary for serialization."""
        result = {
            'timestamp': self.timestamp,
            'datetime': self.datetime.isoformat(),
            'level': self.level.name,
            'level_value': int(self.level),
            'logger': self.logger_name,
            'message': self.message,
        }
        
        # Add optional fields
        if self.fields:
            result['fields'] = self.fields
        
        if self.context:
            context_dict = {}
            for key, value in [
                ('ip', self.context.ip),
                ('access', self.context.access),
                ('user_agent', self.context.user_agent),
                ('request_id', self.context.request_id),
                ('user_id', self.context.user_id),
                ('session_id', self.context.session_id),
                ('service_name', self.context.service_name),
                ('version', self.context.version),
                ('environment', self.context.environment),
            ]:
                if value is not None:
                    context_dict[key] = value
            
            if self.context.custom:
                context_dict.update(self.context.custom)
            
            if context_dict:
                result['context'] = context_dict
        
        # Add source location if available
        if self.module or self.function or self.line_number:
            source = {}
            if self.module:
                source['module'] = self.module
            if self.function:
                source['function'] = self.function
            if self.line_number:
                source['line'] = self.line_number
            result['source'] = source
        
        # Add threading info if available
        if self.thread_id or self.thread_name or self.process_id:
            threading_info = {}
            if self.thread_id:
                threading_info['thread_id'] = self.thread_id
            if self.thread_name:
                threading_info['thread_name'] = self.thread_name
            if self.process_id:
                threading_info['process_id'] = self.process_id
            result['threading'] = threading_info
        
        # Add exception info if available
        if self.exception:
            result['exception'] = {
                'type': type(self.exception).__name__,
                'message': str(self.exception),
            }
            if self.exception_traceback:
                result['exception']['traceback'] = self.exception_traceback
        
        return result


def create_log_record(
    level: Union[LogLevel, str, int],
    logger_name: str,
    message: str,
    *,
    timestamp: Optional[float] = None,
    fields: Optional[Dict[str, Any]] = None,
    context: Optional[LogContext] = None,
    exception: Optional[Exception] = None,
    exception_traceback: Optional[str] = None,
    module: Optional[str] = None,
    function: Optional[str] = None,
    line_number: Optional[int] = None,
    thread_id: Optional[int] = None,
    thread_name: Optional[str] = None,
    process_id: Optional[int] = None,
) -> LogRecord:
    """
    Factory function to create LogRecord with automatic timestamp and level conversion.
    
    This function optimizes the common case of creating log records by:
    - Automatically setting timestamp if not provided
    - Converting level from various formats to LogLevel enum
    - Providing default values for optional fields
    """
    if timestamp is None:
        timestamp = time.time()
    
    if isinstance(level, str):
        level = LogLevel.from_name(level)
    elif isinstance(level, int):
        level = LogLevel(level)
    
    return LogRecord(
        timestamp=timestamp,
        level=level,
        logger_name=logger_name,
        message=message,
        fields=fields,
        context=context,
        exception=exception,
        exception_traceback=exception_traceback,
        module=module,
        function=function,
        line_number=line_number,
        thread_id=thread_id,
        thread_name=thread_name,
        process_id=process_id,
    )


# Pre-defined context instances for common use cases
EMPTY_CONTEXT = LogContext()
