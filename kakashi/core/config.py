"""
Immutable configuration system for functional logging.

This module replaces the stateful singleton ConfigurationManager with
immutable configuration objects that are explicitly passed around.
This makes the system's behavior completely predictable and eliminates
hidden global state.
"""

from dataclasses import dataclass, field
from typing import Optional, Union
from pathlib import Path

from .records import LogLevel, LogContext
from .pipeline import (
    Pipeline, Formatter, create_console_pipeline, create_file_pipeline, create_dual_pipeline,
    simple_text_formatter, default_json_formatter, compact_formatter,
    context_enricher
)
from .async_backend import AsyncConfig
from .async_pipeline import (
    AsyncPipeline, create_async_file_pipeline, 
    create_async_dual_pipeline
)
from .structured_formatters import optimized_json_formatter

@dataclass(frozen=True)
class LoggerConfig:
    """
    Immutable configuration for a functional logger.
    
    This replaces the old singleton-based configuration system with
    an explicit, immutable configuration that's passed to loggers.
    """
    # Logger identification
    name: str
    
    # Pipeline configuration (sync or async)
    pipeline: Union[Pipeline, AsyncPipeline]
    
    # Base context that's added to all log records
    base_context: Optional[LogContext] = None
    
    # Source location capture (can impact performance)
    capture_source: bool = False
    
    # Exception handling
    capture_exceptions: bool = True
    
    # Async settings
    is_async: bool = False  # Whether this logger uses async I/O
    
    def with_base_context(self, context: LogContext) -> 'LoggerConfig':
        """Create a new config with updated base context."""
        return LoggerConfig(
            name=self.name,
            pipeline=self.pipeline,
            base_context=context.merge(self.base_context) if self.base_context else context,
            capture_source=self.capture_source,
            capture_exceptions=self.capture_exceptions
        )
    
    def with_pipeline(self, pipeline: Union[Pipeline, AsyncPipeline]) -> 'LoggerConfig':
        """Create a new config with a different pipeline."""
        return LoggerConfig(
            name=self.name,
            pipeline=pipeline,
            base_context=self.base_context,
            capture_source=self.capture_source,
            capture_exceptions=self.capture_exceptions,
            is_async=isinstance(pipeline, AsyncPipeline)
        )


@dataclass(frozen=True)
class EnvironmentConfig:
    """
    Environment-specific configuration that affects how loggers are created.
    
    This is passed to the logger factory functions to create appropriately
    configured loggers for different environments (dev, prod, etc.).
    """
    # Environment type
    environment: str = "development"  # development, production, testing
    
    # Default log levels
    console_level: LogLevel = LogLevel.INFO
    file_level: LogLevel = LogLevel.DEBUG
    
    # Base paths
    log_directory: Path = field(default_factory=lambda: Path("logs"))
    
    # Default formatters
    console_formatter: Formatter = optimized_json_formatter  
    file_formatter: Formatter = optimized_json_formatter
    
    # Performance settings
    include_thread_info: bool = True
    include_source_location: bool = False  # Can be expensive
    
    # Application context (added to all logs)
    service_name: Optional[str] = None
    version: Optional[str] = None
    
    # Color settings (for text formatters)
    use_colors: bool = True
    bright_colors: bool = False
    
    # Async I/O settings
    enable_async_io: bool = False  # Enable asynchronous I/O by default
    async_config: Optional[AsyncConfig] = None  # Custom async configuration
    
    def __post_init__(self):
        """Validate and normalize configuration."""
        # Ensure log directory is a Path object
        if isinstance(self.log_directory, str):
            object.__setattr__(self, 'log_directory', Path(self.log_directory))
    
    @property
    def is_production(self) -> bool:
        """Check if this is a production environment."""
        return self.environment.lower() in ('production', 'prod')
    
    @property
    def is_development(self) -> bool:
        """Check if this is a development environment."""
        return self.environment.lower() in ('development', 'dev')
    
    @property
    def base_context(self) -> Optional[LogContext]:
        """Create base context from environment settings."""
        if self.service_name or self.version:
            return LogContext(
                service_name=self.service_name,
                version=self.version,
                environment=self.environment
            )
        return None


# ============================================================================
# CONFIGURATION PRESETS
# ============================================================================

def development_config(
    log_directory: Union[str, Path] = "logs",
    service_name: Optional[str] = None,
    version: Optional[str] = None,
    enable_async_io: bool = False,
    use_structured_logging: bool = True  # Enable structured logging by default
) -> EnvironmentConfig:
    """Create configuration optimized for development."""
    async_config = AsyncConfig(
        max_queue_size=5000,  # Moderate queue for development
        worker_count=1,
        batch_size=50,
        enable_batching=True
    ) if enable_async_io else None

    return EnvironmentConfig(
        environment="development",
        console_level=LogLevel.DEBUG,
        file_level=LogLevel.DEBUG,
        log_directory=Path(log_directory),
        console_formatter=simple_text_formatter,
        file_formatter=default_json_formatter,
        include_thread_info=True,
        include_source_location=True,  # Helpful for debugging
        service_name=service_name,
        version=version,
        use_colors=True,
        bright_colors=True,
        enable_async_io=enable_async_io,
        async_config=async_config
    )


def production_config(
    log_directory: Union[str, Path] = "/var/log",
    service_name: Optional[str] = None,
    version: Optional[str] = None,
    enable_async_io: bool = True  # Enable async by default in production
) -> EnvironmentConfig:
    """Create configuration optimized for production."""
    # High-performance async config for production
    async_config = AsyncConfig(
        max_queue_size=25000,  # Large queue for high throughput
        worker_count=2,  # Multiple workers for production load
        batch_size=200,  # Large batches for efficiency
        batch_timeout=0.05,  # Quick batching
        enable_batching=True,
        queue_overflow_strategy="drop_oldest"  # Don't block production code
    ) if enable_async_io else None

    return EnvironmentConfig(
        environment="production",
        console_level=LogLevel.WARNING,  # Minimal console output
        file_level=LogLevel.INFO,
        log_directory=Path(log_directory),
        console_formatter=compact_formatter,  # Compact for production
        file_formatter=default_json_formatter,  # Structured for log analysis
        include_thread_info=True,
        include_source_location=False,  # Avoid performance overhead
        service_name=service_name,
        version=version,
        use_colors=False,  # No colors in production
        enable_async_io=enable_async_io,
        async_config=async_config
    )


def testing_config(
    log_directory: Union[str, Path] = "test_logs",
    service_name: Optional[str] = None,
    enable_async_io: bool = False  # Usually sync for deterministic tests
) -> EnvironmentConfig:
    """Create configuration optimized for testing."""
    # Simple async config for testing if enabled
    async_config = AsyncConfig(
        max_queue_size=1000,  # Small queue for tests
        worker_count=1,
        batch_size=10,
        enable_batching=False,  # Disable batching for deterministic tests
        shutdown_timeout=1.0  # Quick shutdown in tests
    ) if enable_async_io else None

    return EnvironmentConfig(
        environment="testing",
        console_level=LogLevel.WARNING,  # Quiet during tests
        file_level=LogLevel.DEBUG,
        log_directory=Path(log_directory),
        console_formatter=compact_formatter,
        file_formatter=default_json_formatter,
        include_thread_info=False,  # Less noise in tests
        include_source_location=False,
        service_name=service_name,
        version="test",
        use_colors=False,
        enable_async_io=enable_async_io,
        async_config=async_config
    )


# ============================================================================
# LOGGER FACTORY FUNCTIONS
# ============================================================================

def create_logger_config(
    name: str,
    env_config: EnvironmentConfig,
    log_file: Optional[str] = None,
    formatter_type: str = "default",
    force_async: Optional[bool] = None  # Override env async setting
) -> LoggerConfig:
    """
    Create a LoggerConfig based on environment configuration.
    
    This is the main factory function that replaces the old singleton-based
    logger creation system.
    
    Args:
        name: Logger name (typically __name__)
        env_config: Environment configuration
        log_file: Optional custom log file name
        formatter_type: Type of formatter ('default', 'json', 'compact', 'detailed')
    
    Returns:
        Immutable LoggerConfig ready to create a functional logger
    """
    # Determine log file path
    if log_file:
        # Custom log file in modules subdirectory
        log_path = env_config.log_directory / "modules" / f"{log_file}.log"
    else:
        # Default log file
        log_path = env_config.log_directory / "app.log"
    
    # Select formatters based on type
    if formatter_type == "json":
        console_formatter = default_json_formatter
        file_formatter = default_json_formatter
    elif formatter_type == "compact":
        console_formatter = compact_formatter
        file_formatter = compact_formatter
    elif formatter_type == "detailed":
        from .pipeline import detailed_formatter
        console_formatter = detailed_formatter
        file_formatter = detailed_formatter
    else:  # default
        console_formatter = env_config.console_formatter
        file_formatter = env_config.file_formatter
    
    # Determine if we should use async I/O
    use_async = force_async if force_async is not None else env_config.enable_async_io
    
    # Create pipeline based on environment and async setting
    if use_async:
        # Create async pipeline
        if env_config.is_production:
            # Production: file-focused with minimal console output
            pipeline = create_async_dual_pipeline(
                file_path=log_path,
                console_level=env_config.console_level,
                file_level=env_config.file_level,
                console_formatter=console_formatter,
                file_formatter=file_formatter,
                async_config=env_config.async_config
            )
        elif env_config.is_development:
            # Development: dual output with rich formatting
            pipeline = create_async_dual_pipeline(
                file_path=log_path,
                console_level=env_config.console_level,
                file_level=env_config.file_level,
                console_formatter=console_formatter,
                file_formatter=file_formatter,
                async_config=env_config.async_config
            )
        else:
            # Testing or other: primarily file-based
            pipeline = create_async_file_pipeline(
                file_path=log_path,
                min_level=env_config.file_level,
                formatter=file_formatter,
                include_thread_info=env_config.include_thread_info,
                async_config=env_config.async_config
            )
    else:
        # Create synchronous pipeline
        if env_config.is_production:
            # Production: file-focused with minimal console output
            pipeline = create_dual_pipeline(
                file_path=log_path,
                console_level=env_config.console_level,
                file_level=env_config.file_level,
                console_formatter=console_formatter,
                file_formatter=file_formatter
            )
        elif env_config.is_development:
            # Development: dual output with rich formatting
            pipeline = create_dual_pipeline(
                file_path=log_path,
                console_level=env_config.console_level,
                file_level=env_config.file_level,
                console_formatter=console_formatter,
                file_formatter=file_formatter
            )
        else:
            # Testing or other: primarily file-based
            pipeline = create_file_pipeline(
                file_path=log_path,
                min_level=env_config.file_level,
                formatter=file_formatter,
                include_thread_info=env_config.include_thread_info
            )
    
    # Add base context enricher if we have environment context
    if env_config.base_context:
        pipeline = pipeline.with_enricher(context_enricher(env_config.base_context))
    
    return LoggerConfig(
        name=name,
        pipeline=pipeline,
        base_context=env_config.base_context,
        capture_source=env_config.include_source_location,
        capture_exceptions=True,
        is_async=use_async
    )


def create_console_logger_config(
    name: str,
    min_level: LogLevel = LogLevel.INFO,
    formatter: Formatter = simple_text_formatter
) -> LoggerConfig:
    """Create a simple console-only logger configuration."""
    pipeline = create_console_pipeline(
        min_level=min_level,
        formatter=formatter,
        include_thread_info=True
    )
    
    return LoggerConfig(
        name=name,
        pipeline=pipeline,
        capture_source=False,
        capture_exceptions=True
    )


def create_file_logger_config(
    name: str,
    file_path: Union[str, Path],
    min_level: LogLevel = LogLevel.DEBUG,
    formatter: Formatter = default_json_formatter
) -> LoggerConfig:
    """Create a simple file-only logger configuration."""
    pipeline = create_file_pipeline(
        file_path=file_path,
        min_level=min_level,
        formatter=formatter,
        include_thread_info=True
    )
    
    return LoggerConfig(
        name=name,
        pipeline=pipeline,
        capture_source=False,
        capture_exceptions=True
    )


# ============================================================================
# GLOBAL ENVIRONMENT MANAGEMENT
# ============================================================================

class EnvironmentManager:
    """
    Simple, thread-safe manager for global environment configuration.
    
    Unlike the old singleton system, this just holds a reference to an
    immutable configuration that can be easily swapped out for testing
    or different environments.
    """
    
    def __init__(self, env_config: Optional[EnvironmentConfig] = None):
        self._config = env_config or development_config()
        self._lock = threading.RLock()
    
    def get_config(self) -> EnvironmentConfig:
        """Get the current environment configuration."""
        with self._lock:
            return self._config
    
    def set_config(self, config: EnvironmentConfig) -> None:
        """Set a new environment configuration."""
        with self._lock:
            self._config = config
    
    def create_logger_config(self, name: str, **kwargs) -> LoggerConfig:
        """Create a logger config using the current environment configuration."""
        return create_logger_config(name, self.get_config(), **kwargs)


# Global environment manager (can be replaced for testing)
import threading
_default_env_manager = EnvironmentManager()


def get_environment_config() -> EnvironmentConfig:
    """Get the current global environment configuration."""
    return _default_env_manager.get_config()


def set_environment_config(config: EnvironmentConfig) -> None:
    """Set the global environment configuration."""
    _default_env_manager.set_config(config)


def setup_environment(environment: str = "development", **kwargs) -> EnvironmentConfig:
    """
    Quick setup function for common environments.
    
    Args:
        environment: 'development', 'production', or 'testing'
        **kwargs: Additional arguments passed to the config constructor
        
    Returns:
        The created EnvironmentConfig (also sets it globally)
    """
    if environment.lower() in ('development', 'dev'):
        config = development_config(**kwargs)
    elif environment.lower() in ('production', 'prod'):
        config = production_config(**kwargs)
    elif environment.lower() in ('testing', 'test'):
        config = testing_config(**kwargs)
    else:
        raise ValueError(f"Unknown environment: {environment}")
    
    set_environment_config(config)
    return config


# ============================================================================
# CONTEXT MANAGEMENT
# ============================================================================

import contextvars

# Context variables for request-scoped information
_current_context: contextvars.ContextVar[Optional[LogContext]] = contextvars.ContextVar(
    'current_context', default=None
)


def get_current_context() -> Optional[LogContext]:
    """Get the current log context from context variables."""
    return _current_context.get()


def set_current_context(context: LogContext) -> None:
    """Set the current log context."""
    _current_context.set(context)


def clear_current_context() -> None:
    """Clear the current log context."""
    _current_context.set(None)


def merge_current_context(context: LogContext) -> None:
    """Merge new context with the existing current context."""
    current = get_current_context()
    if current:
        merged = current.merge(context)
    else:
        merged = context
    set_current_context(merged)


class context_scope:
    """
    Context manager for scoped logging context.
    
    Usage:
        with context_scope(LogContext(user_id="123")):
            logger.info("This will include user_id")
    """
    
    def __init__(self, context: LogContext):
        self.context = context
        self.previous_context = None
    
    def __enter__(self):
        self.previous_context = get_current_context()
        if self.previous_context:
            set_current_context(self.previous_context.merge(self.context))
        else:
            set_current_context(self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_current_context(self.previous_context)
