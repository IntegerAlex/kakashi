"""
High-performance functional logging core - completely framework independent.

This module provides the new functional logging API that replaces the old
singleton-based system with immutable configuration and pipeline processing.

The new system is:
- Functional: No global state, pure functions, predictable behavior
- Fast: Minimal allocations, optimized hot paths, zero-copy where possible  
- Flexible: Composable pipelines, immutable configuration, easy testing
- Safe: Thread-safe by design, no race conditions, graceful error handling

For backward compatibility, the old API is still available but will be
deprecated in future versions. New code should use the functional API.
"""

# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

# Core data structures
from .records import LogRecord, LogContext, LogLevel, create_log_record

# ============================================================================
# MAIN INTERFACE (Primary API)
# ============================================================================

# Main interface (primary API)
from .interface import (
    get_logger, get_structured_logger, get_request_logger,
    setup_logging, set_log_level,
    set_request_context, set_user_context, set_custom_context, clear_request_context,
    configure_colors, enable_bright_colors, disable_colors,
    create_custom_logger, clear_logger_cache,
    PerformanceLogger, get_performance_logger
)

# ============================================================================
# CONFIGURATION SYSTEM
# ============================================================================

# Configuration system
from .config import (
    EnvironmentConfig, LoggerConfig,
    development_config, production_config, testing_config,
    setup_environment, get_environment_config, set_environment_config,
    context_scope
)

# ============================================================================
# PIPELINE COMPONENTS
# ============================================================================

# Pipeline components  
from .pipeline import (
    Pipeline, PipelineConfig,
    # Enrichers
    thread_enricher, exception_enricher, context_enricher,
    # Filters
    level_filter, field_filter, logger_name_filter,
    # Formatters
    default_json_formatter, simple_text_formatter, compact_formatter, detailed_formatter,
    # Writers
    console_writer, stderr_writer, file_writer, null_writer,
    # Factory functions
    create_console_pipeline, create_file_pipeline, create_dual_pipeline
)

# ============================================================================
# ASYNC COMPONENTS
# ============================================================================

# Async components
from .async_backend import (
    AsyncConfig, AsyncBackend, shutdown_async_logging
)
from .async_pipeline import (
    AsyncPipeline, AsyncPipelineConfig,
    create_async_console_pipeline, create_async_file_pipeline,
    create_async_dual_pipeline, create_high_performance_pipeline,
    create_network_pipeline, benchmark_async_vs_sync
)
from .async_interface import (
    get_async_logger, get_high_performance_logger, get_network_logger,
    get_async_structured_logger, setup_async_logging, configure_async_backend,
    get_async_stats, shutdown_async_backend, benchmark_async_performance
)

# ============================================================================
# LOGGER IMPLEMENTATION
# ============================================================================

# Logger implementation
from .functional_logger import (
    FunctionalLogger, BoundLogger, create_logger,
    create_structured_logger, create_request_logger
)

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # ---- MAIN INTERFACE (Primary API) ----
    "get_logger",  # Main entry point
    "get_structured_logger",
    "get_request_logger", 
    "setup_logging",
    "set_log_level",
    
    # Context management
    "set_request_context",
    "set_user_context", 
    "set_custom_context",
    "clear_request_context",
    "context_scope",
    
    # Configuration
    "configure_colors",
    "enable_bright_colors",
    "disable_colors",
    
    # Advanced functions
    "create_custom_logger",
    "clear_logger_cache",
    "get_performance_logger",
    
    # Core data structures
    "LogRecord",
    "LogContext", 
    "LogLevel",
    "create_log_record",
    
    # Configuration objects
    "EnvironmentConfig",
    "LoggerConfig",
    "development_config",
    "production_config", 
    "testing_config",
    "setup_environment",
    "get_environment_config",
    "set_environment_config",
    
    # Pipeline components
    "Pipeline",
    "PipelineConfig",
    "thread_enricher",
    "exception_enricher", 
    "context_enricher",
    "level_filter",
    "field_filter",
    "logger_name_filter",
    "default_json_formatter",
    "simple_text_formatter",
    "compact_formatter",
    "detailed_formatter",
    "console_writer",
    "stderr_writer",
    "file_writer",
    "null_writer",
    "create_console_pipeline",
    "create_file_pipeline",
    "create_dual_pipeline",
    
    # Async components
    "AsyncConfig",
    "AsyncBackend",
    "AsyncPipeline",
    "AsyncPipelineConfig",
    "create_async_console_pipeline",
    "create_async_file_pipeline",
    "create_async_dual_pipeline",
    "create_high_performance_pipeline",
    "create_network_pipeline",
    "shutdown_async_logging",
    "benchmark_async_vs_sync",
    
    # Async interface functions
    "get_async_logger",
    "get_high_performance_logger",
    "get_network_logger",
    "get_async_structured_logger",
    "setup_async_logging",
    "configure_async_backend",
    "get_async_stats",
    "shutdown_async_backend",
    "benchmark_async_performance",
    
    # Logger classes
    "FunctionalLogger",
    "BoundLogger",
    "PerformanceLogger",
    "create_logger",
    "create_structured_logger",
    "create_request_logger",
]
