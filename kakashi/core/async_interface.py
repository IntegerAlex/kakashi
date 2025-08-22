"""
Async-specific interface functions for high-performance logging.

This module provides convenient functions for creating and using asynchronous
loggers with various performance optimizations.
"""

from typing import Optional, Dict, Any, Union
from pathlib import Path

from .config import (
    EnvironmentConfig, LoggerConfig, 
    development_config, production_config, testing_config,
    create_logger_config
)
from .functional_logger import (
    FunctionalLogger, BoundLogger, create_logger
)
from .async_backend import (
    AsyncConfig, AsyncBackend, shutdown_async_logging, 
    get_async_backend, set_async_backend
)
from .async_pipeline import (
    create_high_performance_pipeline,
    create_network_pipeline
)


# ============================================================================
# ASYNC LOGGER CREATION FUNCTIONS
# ============================================================================

def get_async_logger(
    name: str,
    log_file: Optional[str] = None,
    formatter_type: str = "default",
    async_config: Optional[AsyncConfig] = None
) -> FunctionalLogger:
    """
    Get an async logger with non-blocking I/O.
    
    This creates a logger that performs all I/O operations asynchronously,
    providing dramatically improved performance for high-throughput scenarios.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional custom log file name
        formatter_type: Type of formatter ('default', 'json', 'compact', 'detailed')
        async_config: Optional custom async configuration
    
    Returns:
        FunctionalLogger with async I/O pipeline
        
    Example:
        # High-performance async logger
        logger = get_async_logger(__name__)
        logger.info("This returns immediately!")  # Non-blocking I/O
        
        # Custom async configuration
        config = AsyncConfig(max_queue_size=20000, worker_count=3)
        logger = get_async_logger("high_volume", async_config=config)
    """
    # Get current environment config and force async
    env_config = get_environment_config()
    
    # Override async config if provided
    if async_config:
        env_config = EnvironmentConfig(
            environment=env_config.environment,
            console_level=env_config.console_level,
            file_level=env_config.file_level,
            log_directory=env_config.log_directory,
            console_formatter=env_config.console_formatter,
            file_formatter=env_config.file_formatter,
            include_thread_info=env_config.include_thread_info,
            include_source_location=env_config.include_source_location,
            service_name=env_config.service_name,
            version=env_config.version,
            use_colors=env_config.use_colors,
            bright_colors=env_config.bright_colors,
            enable_async_io=True,
            async_config=async_config
        )
    
    # Create logger config with async forced on
    logger_config = create_logger_config(name, env_config, log_file, formatter_type, force_async=True)
    return create_logger(logger_config)


def get_high_performance_logger(
    name: str,
    log_file: str,
    max_queue_size: int = 50000,
    worker_count: int = 2,
    batch_size: int = 500
) -> FunctionalLogger:
    """
    Get a logger optimized for maximum throughput.
    
    This creates a logger with aggressive performance optimizations:
    - Large message queue
    - Multiple worker threads
    - Large batch sizes
    - Minimal enrichers for speed
    
    Args:
        name: Logger name
        log_file: Log file path (required for high-performance mode)
        max_queue_size: Maximum messages in queue
        worker_count: Number of worker threads
        batch_size: Messages per batch
    
    Returns:
        FunctionalLogger optimized for maximum throughput
        
    Example:
        # Ultra-high-performance logger
        logger = get_high_performance_logger("trading", "trades.log", 
                                           max_queue_size=100000, worker_count=4)
        
        # In trading loop:
        for trade in trades:
            logger.info("Trade executed", **trade.to_dict())  # Microsecond latency
    """
    pipeline = create_high_performance_pipeline(
        file_path=log_file,
        max_queue_size=max_queue_size,
        worker_count=worker_count,
        batch_size=batch_size
    )
    
    config = LoggerConfig(
        name=name,
        pipeline=pipeline,
        capture_source=False,  # Disable for speed
        capture_exceptions=True,
        is_async=True
    )
    
    return create_logger(config)


def get_network_logger(
    name: str,
    network_writer_func: callable,
    max_queue_size: int = 20000,
    batch_size: int = 100,
    max_retries: int = 5
) -> FunctionalLogger:
    """
    Get a logger that sends logs to network destinations.
    
    Perfect for shipping logs to Elasticsearch, Splunk, or custom log
    aggregation services without blocking your application.
    
    Args:
        name: Logger name
        network_writer_func: Function that sends formatted message over network
        max_queue_size: Maximum messages to queue
        batch_size: Messages per network batch
        max_retries: Retries for network failures
    
    Returns:
        FunctionalLogger with async network I/O
        
    Example:
        def send_to_elasticsearch(message):
            # Your Elasticsearch client code
            es_client.index(index="logs", body=json.loads(message))
        
        logger = get_network_logger("api", send_to_elasticsearch)
        logger.info("API call", endpoint="/users", response_time=45)
        # Sent to Elasticsearch asynchronously
    """
    async_config = AsyncConfig(
        max_queue_size=max_queue_size,
        worker_count=1,  # Single worker to maintain order
        batch_size=batch_size,
        enable_batching=True,
        max_error_retries=max_retries,
        error_retry_delay=0.5,  # Longer delay for network issues
        queue_overflow_strategy="drop_oldest"
    )
    
    pipeline = create_network_pipeline(network_writer_func, async_config=async_config)
    
    config = LoggerConfig(
        name=name,
        pipeline=pipeline,
        capture_source=False,
        capture_exceptions=True,
        is_async=True
    )
    
    return create_logger(config)


def get_async_structured_logger(
    name: str,
    log_file: Optional[str] = None,
    async_config: Optional[AsyncConfig] = None,
    **default_fields
) -> BoundLogger:
    """
    Get an async structured logger with default fields.
    
    Args:
        name: Logger name
        log_file: Optional custom log file
        async_config: Optional async configuration
        **default_fields: Fields to include in every log message
    
    Returns:
        BoundLogger with async I/O and predefined fields
        
    Example:
        logger = get_async_structured_logger("api", service="user-service", version="1.2.3")
        logger.info("User created", user_id=123, email="user@example.com")
        # {"service": "user-service", "version": "1.2.3", "user_id": 123, ...}
    """
    base_logger = get_async_logger(name, log_file, "json", async_config)
    return base_logger.with_fields(**default_fields)


# ============================================================================
# ASYNC ENVIRONMENT SETUP
# ============================================================================

def setup_async_logging(
    environment: str = "production",
    service_name: Optional[str] = None,
    version: Optional[str] = None,
    log_directory: Optional[Union[str, Path]] = None,
    max_queue_size: int = 25000,
    worker_count: int = 2,
    batch_size: int = 200
) -> EnvironmentConfig:
    """
    Quick setup for high-performance async logging.
    
    This automatically configures async I/O with sensible defaults
    for production environments.
    
    Args:
        environment: 'development', 'production', or 'testing'
        service_name: Service name (added to all logs)
        version: Version (added to all logs)
        log_directory: Custom log directory
        max_queue_size: Maximum messages in async queue
        worker_count: Number of worker threads
        batch_size: Messages per batch
    
    Returns:
        EnvironmentConfig with async I/O enabled
        
    Example:
        # Production async setup
        setup_async_logging("production", 
                           service_name="user-api", 
                           version="2.1.0",
                           max_queue_size=50000,
                           worker_count=4)
    """
    # Create custom async config
    async_config = AsyncConfig(
        max_queue_size=max_queue_size,
        worker_count=worker_count,
        batch_size=batch_size,
        enable_batching=True,
        queue_overflow_strategy="drop_oldest" if environment == "production" else "block"
    )
    
    # Get environment config factory
    if environment.lower() in ('development', 'dev'):
        config_func = development_config
    elif environment.lower() in ('production', 'prod'):
        config_func = production_config
    elif environment.lower() in ('testing', 'test'):
        config_func = testing_config
    else:
        raise ValueError(f"Unknown environment: {environment}")
    
    # Create config with async enabled
    kwargs = {
        'enable_async_io': True
    }
    if service_name:
        kwargs['service_name'] = service_name
    if version:
        kwargs['version'] = version
    if log_directory:
        kwargs['log_directory'] = log_directory
    
    env_config = config_func(**kwargs)
    
    # Override with custom async config
    env_config = EnvironmentConfig(
        environment=env_config.environment,
        console_level=env_config.console_level,
        file_level=env_config.file_level,
        log_directory=env_config.log_directory,
        console_formatter=env_config.console_formatter,
        file_formatter=env_config.file_formatter,
        include_thread_info=env_config.include_thread_info,
        include_source_location=env_config.include_source_location,
        service_name=env_config.service_name,
        version=env_config.version,
        use_colors=env_config.use_colors,
        bright_colors=env_config.bright_colors,
        enable_async_io=True,
        async_config=async_config
    )
    
    set_environment_config(env_config)
    return env_config


# ============================================================================
# ASYNC BACKEND MANAGEMENT
# ============================================================================

def configure_async_backend(
    max_queue_size: int = 25000,
    worker_count: int = 2,
    batch_size: int = 200,
    enable_batching: bool = True,
    overflow_strategy: str = "drop_oldest"
) -> AsyncBackend:
    """
    Configure the global async backend.
    
    Args:
        max_queue_size: Maximum messages in queue
        worker_count: Number of worker threads
        batch_size: Messages per batch
        enable_batching: Whether to enable batching
        overflow_strategy: "block", "drop_oldest", or "drop_newest"
    
    Returns:
        Configured AsyncBackend instance
        
    Example:
        # Configure for high throughput
        backend = configure_async_backend(
            max_queue_size=100000,
            worker_count=8,
            batch_size=1000
        )
    """
    async_config = AsyncConfig(
        max_queue_size=max_queue_size,
        worker_count=worker_count,
        batch_size=batch_size,
        enable_batching=enable_batching,
        queue_overflow_strategy=overflow_strategy
    )
    
    backend = AsyncBackend(async_config)
    set_async_backend(backend)
    return backend


def get_async_stats() -> Dict[str, Any]:
    """
    Get statistics from the async backend.
    
    Returns:
        Dictionary with async performance statistics
        
    Example:
        stats = get_async_stats()
        print(f"Queue size: {stats['queue_size']}")
        print(f"Messages processed: {stats['messages_enqueued']}")
        print(f"Throughput: {stats['messages_enqueued'] / elapsed_time:.0f} msg/sec")
    """
    backend = get_async_backend()
    return backend.get_stats()


def shutdown_async_backend(timeout: float = 5.0) -> None:
    """
    Gracefully shutdown the async logging backend.
    
    This ensures all queued messages are processed before shutdown.
    Call this at application exit to prevent message loss.
    
    Args:
        timeout: Maximum time to wait for shutdown
        
    Example:
        import atexit
        atexit.register(shutdown_async_backend)
        
        # Or manually at exit:
        shutdown_async_backend(timeout=10.0)
    """
    shutdown_async_logging(timeout)


# ============================================================================
# PERFORMANCE UTILITIES
# ============================================================================

def benchmark_async_performance(
    message_count: int = 10000,
    thread_count: int = 4,
    file_path: str = "benchmark.log"
) -> Dict[str, Any]:
    """
    Benchmark async vs sync logging performance.
    
    Args:
        message_count: Messages to log per thread
        thread_count: Number of concurrent threads
        file_path: File to write benchmark logs
    
    Returns:
        Dictionary with detailed benchmark results
        
    Example:
        results = benchmark_async_performance(50000, 8)
        print(f"Async is {results['performance_improvement']:.1f}x faster")
        print(f"Latency improvement: {results['latency_improvement']:.1f}x")
    """
    from .pipeline import create_file_pipeline
    from .async_pipeline import create_async_file_pipeline
    
    def sync_factory():
        return create_file_pipeline(file_path + "_sync")
    
    def async_factory():
        return create_async_file_pipeline(file_path + "_async")
    
    return benchmark_async_vs_sync(
        sync_factory, 
        async_factory, 
        message_count, 
        thread_count
    )


# ============================================================================
# IMPORT COMPATIBILITY
# ============================================================================

# Make functions available for import
from .interface import (
    get_environment_config, set_environment_config,
    set_request_context, set_user_context, set_custom_context,
    clear_request_context, configure_colors, enable_bright_colors,
    disable_colors
)

__all__ = [
    # Async logger creation
    "get_async_logger",
    "get_high_performance_logger", 
    "get_network_logger",
    "get_async_structured_logger",
    
    # Async environment setup
    "setup_async_logging",
    
    # Backend management
    "configure_async_backend",
    "get_async_stats",
    "shutdown_async_backend",
    
    # Performance utilities
    "benchmark_async_performance",
    
    # Re-exported from interface
    "get_environment_config",
    "set_environment_config",
    "set_request_context",
    "set_user_context", 
    "set_custom_context",
    "clear_request_context",
    "configure_colors",
    "enable_bright_colors",
    "disable_colors",
]
