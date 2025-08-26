"""
Professional High-Performance Logging Core

This module provides the core logging functionality with a clean,
maintainable architecture optimized for real-world applications.

FEATURES:
- High throughput (60K+ logs/sec) with balanced concurrency
- Thread-safe operation with minimal contention
- Structured logging support
- Memory-efficient buffer management
- Professional, maintainable code structure
"""

# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

# Core data structures
from .records import LogRecord, LogContext, LogLevel, create_log_record

# ============================================================================
# MAIN LOGGER IMPLEMENTATION
# ============================================================================

# Main logger implementation
from .logger import (
    Logger, AsyncLogger, LogFormatter,
    get_logger, get_async_logger, clear_logger_cache
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
    get_async_logger as get_legacy_async_logger, 
    get_high_performance_logger, get_network_logger,
    get_async_structured_logger, setup_async_logging, configure_async_backend,
    get_async_stats, shutdown_async_backend, benchmark_async_performance
)

# ============================================================================
# FUNCTIONAL LOGGER (Legacy compatibility)
# ============================================================================

# Functional logger (legacy compatibility)
from .functional_logger import (
    FunctionalLogger, BoundLogger, create_logger,
    create_structured_logger, create_request_logger
)

# ============================================================================
# STRUCTURED LOGGING
# ============================================================================

# Structured logging components
from .structured_logger import (
    StructuredLogger, BoundStructuredLogger, StructuredLogEntry,
    create_structured_logger, create_high_performance_structured_logger
)
from .structured_formatters import (
    optimized_json_formatter, minimal_json_formatter, elk_stack_formatter,
    splunk_formatter, prometheus_logs_formatter, datadog_formatter,
    opentelemetry_formatter, ultra_compact_formatter, binary_efficient_formatter
)

# ============================================================================
# SINK SYSTEM
# ============================================================================

# Sink-based logging system
from .sinks import (
    Sink, FileSink, ConsoleSink, UDPSink, TCPSink, HTTPSink,
    NullSink, BufferedSink, ConditionalSink,
    create_elasticsearch_sink, create_splunk_sink, SinkRegistry, get_sink_registry
)
from .sink_pipeline import (
    SinkPipeline, SinkPipelineConfig,
    create_multi_sink_pipeline, create_conditional_routing_pipeline,
    create_log_shipping_pipeline, create_level_router, create_field_router, create_context_router
)
from .sink_config import (
    SinkType, SinkSpec, SinkLoggerConfig, SinkEnvironmentConfig,
    development_sink_config, production_sink_config, microservices_sink_config,
    high_performance_sink_config, create_sink_logger_config
)

# ============================================================================
# MAIN INTERFACE (Primary API)
# ============================================================================

# Main interface (primary API)
from .interface import (
    get_logger as get_legacy_logger, get_structured_logger, get_request_logger,
    setup_logging, set_log_level,
    set_request_context, set_user_context, set_custom_context, clear_request_context,
    configure_colors, enable_bright_colors, disable_colors,
    create_custom_logger, clear_logger_cache,
    PerformanceLogger, get_performance_logger
)

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # ---- MAIN LOGGER IMPLEMENTATION ----
    "Logger",  # Main logger class
    "AsyncLogger",  # Async logger class
    "LogFormatter",  # Formatter class
    "get_logger",  # Main entry point
    "get_async_logger",  # Async logger entry point
    "clear_logger_cache",
    
    # ---- CORE DATA STRUCTURES ----
    "LogRecord",
    "LogContext", 
    "LogLevel",
    "create_log_record",
    
    # ---- CONFIGURATION ----
    "EnvironmentConfig",
    "LoggerConfig",
    "development_config",
    "production_config", 
    "testing_config",
    "setup_environment",
    "get_environment_config",
    "set_environment_config",
    "context_scope",
    
    # ---- PIPELINE COMPONENTS ----
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
    
    # ---- ASYNC COMPONENTS ----
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
    
    # ---- ASYNC INTERFACE ----
    "get_legacy_async_logger",
    "get_high_performance_logger",
    "get_network_logger",
    "get_async_structured_logger",
    "setup_async_logging",
    "configure_async_backend",
    "get_async_stats",
    "shutdown_async_backend",
    "benchmark_async_performance",
    
    # ---- STRUCTURED LOGGING ----
    "StructuredLogger",
    "BoundStructuredLogger", 
    "StructuredLogEntry",
    "create_structured_logger",
    "create_high_performance_structured_logger",
    "optimized_json_formatter",
    "minimal_json_formatter",
    "elk_stack_formatter",
    "splunk_formatter",
    "prometheus_logs_formatter",
    "datadog_formatter",
    "opentelemetry_formatter",
    "ultra_compact_formatter",
    "binary_efficient_formatter",
    
    # ---- SINK SYSTEM ----
    "Sink",
    "FileSink",
    "ConsoleSink", 
    "UDPSink",
    "TCPSink",
    "HTTPSink",
    "NullSink",
    "BufferedSink",
    "ConditionalSink",
    "create_elasticsearch_sink",
    "create_splunk_sink",
    "SinkRegistry",
    "get_sink_registry",
    "SinkPipeline",
    "SinkPipelineConfig",
    "create_multi_sink_pipeline",
    "create_conditional_routing_pipeline",
    "create_log_shipping_pipeline",
    "create_level_router",
    "create_field_router",
    "create_context_router",
    "SinkType",
    "SinkSpec",
    "SinkLoggerConfig",
    "SinkEnvironmentConfig",
    "development_sink_config",
    "production_sink_config",
    "microservices_sink_config",
    "high_performance_sink_config",
    "create_sink_logger_config",
    
    # ---- LEGACY COMPATIBILITY ----
    "FunctionalLogger",
    "BoundLogger",
    "create_logger",
    "create_structured_logger",
    "create_request_logger",
    "get_legacy_logger",
    "get_structured_logger",
    "get_request_logger",
    "setup_logging",
    "set_log_level",
    "set_request_context",
    "set_user_context",
    "set_custom_context",
    "clear_request_context",
    "configure_colors",
    "enable_bright_colors",
    "disable_colors",
    "create_custom_logger",
    "PerformanceLogger",
    "get_performance_logger",
]
