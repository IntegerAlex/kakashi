"""
Main interface for the functional logging system.

This module provides the primary API that replaces the old singleton-based
logging system. It offers both high-level convenience functions and
low-level access to the functional components.
"""

from typing import Optional, Dict, Union, Any
import threading
from pathlib import Path

from .records import LogLevel, LogContext
from .config import (
    EnvironmentConfig, LoggerConfig, 
    development_config, get_environment_config, set_environment_config, setup_environment,
    create_logger_config, get_current_context, set_current_context, clear_current_context, 
    merge_current_context
)
from .functional_logger import (
    FunctionalLogger, BoundLogger, create_logger, 
    create_request_logger
)

# Global logger registry for caching (thread-safe)
_logger_cache: Dict[str, FunctionalLogger] = {}
_cache_lock = threading.RLock()


# ============================================================================
# PRIMARY API FUNCTIONS
# ============================================================================

def get_logger(
    name: str,
    log_file: Optional[str] = None,
    formatter_type: str = "default"
) -> FunctionalLogger:
    """
    Get a functional logger instance.
    
    This is the main entry point for getting loggers. It replaces the old
    singleton-based get_logger function with a functional equivalent that
    uses explicit configuration.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional custom log file name
        formatter_type: Type of formatter ('default', 'json', 'compact', 'detailed')
    
    Returns:
        FunctionalLogger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Application started")
        
        # Custom log file
        db_logger = get_logger(__name__, "database")
        db_logger.info("Database connected")
        
        # JSON logging
        api_logger = get_logger("api", "api_logs", "json")
        api_logger.info("API call", user_id=123, endpoint="/users")
    """
    # Create cache key
    cache_key = f"{name}:{log_file or 'default'}:{formatter_type}"
    
    # Check cache first (thread-safe)
    with _cache_lock:
        if cache_key in _logger_cache:
            return _logger_cache[cache_key]
    
    # Create new logger
    env_config = get_environment_config()
    logger_config = create_logger_config(name, env_config, log_file, formatter_type)
    logger = create_logger(logger_config)
    
    # Cache it (thread-safe)
    with _cache_lock:
        _logger_cache[cache_key] = logger
    
    return logger


def get_structured_logger(
    name: str,
    log_file: Optional[str] = None,
    **default_fields: Any
) -> BoundLogger:
    """
    Get a structured logger with default fields.
    
    This creates a logger optimized for structured logging that automatically
    includes the specified fields in every log message.
    
    Args:
        name: Logger name
        log_file: Optional custom log file
        **default_fields: Fields to include in every log message
    
    Returns:
        BoundLogger with predefined fields
        
    Example:
        logger = get_structured_logger("api", service="user-service", version="1.2.3")
        logger.info("User created", user_id=123, email="user@example.com")
        # Logs: {"service": "user-service", "version": "1.2.3", "user_id": 123, ...}
    """
    base_logger = get_logger(name, log_file, "json")  # Structured logging uses JSON
    return base_logger.with_fields(**default_fields)


def get_request_logger(
    name: str,
    request_id: str,
    user_id: Optional[str] = None,
    ip: Optional[str] = None,
    **additional_fields: Any
) -> BoundLogger:
    """
    Get a request-scoped logger.
    
    This creates a logger bound to request-specific context, useful for
    web applications where you want all logs within a request to include
    request information.
    
    Args:
        name: Logger name
        request_id: Unique request identifier
        user_id: Optional user identifier
        ip: Optional IP address
        **additional_fields: Additional fields to include
    
    Returns:
        BoundLogger with request context
        
    Example:
        logger = get_request_logger("api", "req-123", user_id="user-456", ip="192.168.1.1")
        logger.info("Processing request")
        # All logs will include request_id, user_id, and ip
    """
    env_config = get_environment_config()
    logger_config = create_logger_config(name, env_config, None, "json")
    return create_request_logger(name, logger_config, request_id, user_id, ip, **additional_fields)


# ============================================================================
# CONFIGURATION FUNCTIONS
# ============================================================================

def setup_logging(
    environment: str = "development",
    service_name: Optional[str] = None,
    version: Optional[str] = None,
    log_directory: Optional[Union[str, Path]] = None,
    enable_async_io: Optional[bool] = None
) -> EnvironmentConfig:
    """
    Quick setup function for common logging configurations.
    
    This replaces the old setup_logging function with an explicit,
    functional approach.
    
    Args:
        environment: 'development', 'production', or 'testing'
        service_name: Optional service name (added to all logs)
        version: Optional version (added to all logs)  
        log_directory: Optional custom log directory
    
    Returns:
        The created EnvironmentConfig
        
    Example:
        # Development setup
        setup_logging("development", service_name="my-app", version="1.0.0")
        
        # Production setup
        setup_logging("production", service_name="my-app", log_directory="/var/log/myapp")
    """
    kwargs = {}
    if service_name:
        kwargs['service_name'] = service_name
    if version:
        kwargs['version'] = version
    if log_directory:
        kwargs['log_directory'] = log_directory
    if enable_async_io is not None:
        kwargs['enable_async_io'] = enable_async_io
    
    return setup_environment(environment, **kwargs)


def set_log_level(level: Union[LogLevel, str]) -> None:
    """
    Set the minimum log level globally.
    
    Note: This creates a new environment configuration with the updated level.
    Existing loggers will continue to use their original configuration until
    recreated.
    
    Args:
        level: Log level to set
        
    Example:
        set_log_level("DEBUG")
        set_log_level(LogLevel.WARNING)
    """
    if isinstance(level, str):
        level = LogLevel.from_name(level)
    
    current_config = get_environment_config()
    
    # Create new config with updated levels
    if current_config.environment == "development":
        new_config = development_config(
            log_directory=current_config.log_directory,
            service_name=current_config.service_name,
            version=current_config.version
        )
        # Update both console and file levels for development
        new_config = EnvironmentConfig(
            environment=new_config.environment,
            console_level=level,
            file_level=level,
            log_directory=new_config.log_directory,
            console_formatter=new_config.console_formatter,
            file_formatter=new_config.file_formatter,
            include_thread_info=new_config.include_thread_info,
            include_source_location=new_config.include_source_location,
            service_name=new_config.service_name,
            version=new_config.version,
            use_colors=new_config.use_colors,
            bright_colors=new_config.bright_colors
        )
    else:
        # For production, only update file level (keep console level high)
        new_config = EnvironmentConfig(
            environment=current_config.environment,
            console_level=current_config.console_level,
            file_level=level,
            log_directory=current_config.log_directory,
            console_formatter=current_config.console_formatter,
            file_formatter=current_config.file_formatter,
            include_thread_info=current_config.include_thread_info,
            include_source_location=current_config.include_source_location,
            service_name=current_config.service_name,
            version=current_config.version,
            use_colors=current_config.use_colors,
            bright_colors=current_config.bright_colors
        )
    
    set_environment_config(new_config)
    
    # Clear logger cache to force recreation with new levels
    with _cache_lock:
        _logger_cache.clear()


# ============================================================================
# CONTEXT MANAGEMENT FUNCTIONS
# ============================================================================

def set_request_context(ip: Optional[str] = None, access: Optional[str] = None) -> None:
    """
    Set request context for current thread/task.
    
    This context will be automatically included in all log messages
    from the current thread/task until cleared.
    
    Args:
        ip: IP address
        access: Access information (e.g., "GET /api/users")
        
    Example:
        set_request_context("192.168.1.1", "POST /api/users")
        logger.info("Creating user")  # Will include IP and access info
    """
    context = LogContext(ip=ip, access=access)
    current = get_current_context()
    
    if current:
        merged = current.merge(context)
        set_current_context(merged)
    else:
        set_current_context(context)


def set_user_context(user_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
    """
    Set user context for current thread/task.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        
    Example:
        set_user_context("user123", "session456")
        logger.info("User action performed")  # Will include user info
    """
    context = LogContext(user_id=user_id, session_id=session_id)
    merge_current_context(context)


def set_custom_context(**kwargs: Any) -> None:
    """
    Set custom context fields for current thread/task.
    
    Args:
        **kwargs: Custom context fields
        
    Example:
        set_custom_context(tenant_id="tenant123", api_version="v2")
        logger.info("API call")  # Will include custom context
    """
    context = LogContext(custom=kwargs)
    merge_current_context(context)


def clear_request_context() -> None:
    """Clear all context for current thread/task."""
    clear_current_context()


# ============================================================================
# COLOR AND FORMATTING FUNCTIONS
# ============================================================================

def configure_colors(
    use_colors: bool = True,
    bright_colors: bool = False
) -> None:
    """
    Configure color settings globally.
    
    Args:
        use_colors: Whether to use colors in console output
        bright_colors: Whether to use bright color variants
        
    Example:
        configure_colors(use_colors=True, bright_colors=True)
    """
    current_config = get_environment_config()
    
    # Create new config with updated color settings
    new_config = EnvironmentConfig(
        environment=current_config.environment,
        console_level=current_config.console_level,
        file_level=current_config.file_level,
        log_directory=current_config.log_directory,
        console_formatter=current_config.console_formatter,
        file_formatter=current_config.file_formatter,
        include_thread_info=current_config.include_thread_info,
        include_source_location=current_config.include_source_location,
        service_name=current_config.service_name,
        version=current_config.version,
        use_colors=use_colors,
        bright_colors=bright_colors
    )
    
    set_environment_config(new_config)
    
    # Clear cache to force recreation with new settings
    with _cache_lock:
        _logger_cache.clear()


def enable_bright_colors() -> None:
    """Enable bright colors for console output."""
    configure_colors(use_colors=True, bright_colors=True)


def disable_colors() -> None:
    """Disable all colors in console output."""
    configure_colors(use_colors=False, bright_colors=False)


# ============================================================================
# ADVANCED FUNCTIONS
# ============================================================================

def create_custom_logger(
    name: str,
    config: 'LoggerConfig'
) -> FunctionalLogger:
    """
    Create a logger with completely custom configuration.
    
    This is for advanced users who want full control over the logger
    configuration, bypassing the environment-based defaults.
    
    Args:
        name: Logger name
        config: Custom LoggerConfig
    
    Returns:
        FunctionalLogger with custom configuration
    """
    return create_logger(config)


def clear_logger_cache() -> None:
    """
    Clear the logger cache.
    
    This forces all subsequent get_logger calls to create new logger
    instances with current configuration. Useful after changing
    global configuration.
    """
    with _cache_lock:
        _logger_cache.clear()


# ============================================================================
# PERFORMANCE UTILITIES
# ============================================================================

class PerformanceLogger:
    """
    High-performance logger for hot code paths.
    
    This pre-creates and caches everything possible to minimize
    overhead in performance-critical code.
    """
    
    def __init__(self, logger: FunctionalLogger):
        self._logger = logger
        self._is_debug_enabled = logger.is_enabled_for(LogLevel.DEBUG)
        self._is_info_enabled = logger.is_enabled_for(LogLevel.INFO)
        self._is_warning_enabled = logger.is_enabled_for(LogLevel.WARNING)
        self._is_error_enabled = logger.is_enabled_for(LogLevel.ERROR)
    
    def debug_fast(self, message: str) -> None:
        """Ultra-fast debug logging with pre-computed level check."""
        if self._is_debug_enabled:
            self._logger.debug(message)
    
    def info_fast(self, message: str) -> None:
        """Ultra-fast info logging with pre-computed level check."""
        if self._is_info_enabled:
            self._logger.info(message)
    
    def warning_fast(self, message: str) -> None:
        """Ultra-fast warning logging with pre-computed level check."""
        if self._is_warning_enabled:
            self._logger.warning(message)
    
    def error_fast(self, message: str) -> None:
        """Ultra-fast error logging with pre-computed level check."""
        if self._is_error_enabled:
            self._logger.error(message)


def get_performance_logger(name: str) -> PerformanceLogger:
    """
    Get a performance-optimized logger for hot code paths.
    
    This pre-computes level checks and caches everything possible
    to minimize logging overhead in performance-critical code.
    
    Args:
        name: Logger name
    
    Returns:
        PerformanceLogger instance
        
    Example:
        perf_logger = get_performance_logger("hot_path")
        
        # In performance-critical loop:
        for item in large_list:
            perf_logger.debug_fast("Processing item")  # Minimal overhead
    """
    base_logger = get_logger(name)
    return PerformanceLogger(base_logger)
