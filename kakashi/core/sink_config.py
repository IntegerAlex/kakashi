"""
Configuration system for sink-based logging.

This module extends the configuration system to support the new Sinks
architecture, enabling multi-destination log shipping with sophisticated
routing and configuration options.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union, Callable
from pathlib import Path
from enum import Enum

from .records import LogLevel, LogContext, LogRecord
from .sinks import (
    Sink, FileSink, ConsoleSink, RotatingFileSink, UDPSink, TCPSink, HTTPSink,
    BufferedSink, ConditionalSink, NullSink,
    create_elasticsearch_sink, create_splunk_sink
)
from .sink_pipeline import ( 
    SinkPipeline, SinkPipelineConfig, 
    create_field_router
)
from .pipeline import (
    Formatter, default_json_formatter, simple_text_formatter, compact_formatter,
    thread_enricher, exception_enricher, context_enricher
)


class SinkType(Enum):
    """Types of supported sinks."""
    CONSOLE = "console"
    FILE = "file"  
    ROTATING_FILE = "rotating_file"
    UDP = "udp"
    TCP = "tcp"
    HTTP = "http"
    ELASTICSEARCH = "elasticsearch"
    SPLUNK = "splunk"
    NULL = "null"
    BUFFERED = "buffered"
    CONDITIONAL = "conditional"


@dataclass
class SinkSpec:
    """Specification for creating a sink."""
    type: SinkType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Optional conditional routing
    condition: Optional[Callable[[LogRecord], bool]] = None
    
    # Optional buffering
    buffer_size: Optional[int] = None
    flush_interval: Optional[float] = None


@dataclass(frozen=True)
class SinkLoggerConfig:
    """
    Configuration for a sink-based logger.
    
    This extends LoggerConfig to support multiple sinks and
    advanced routing capabilities.
    """
    # Logger identification
    name: str
    
    # Pipeline configuration (sink-based)
    pipeline: SinkPipeline
    
    # Base context that's added to all log records
    base_context: Optional[LogContext] = None
    
    # Source location capture (can impact performance)
    capture_source: bool = False
    
    # Exception handling
    capture_exceptions: bool = True
    
    # Sink-specific settings
    auto_flush_interval: Optional[float] = None  # Auto-flush all sinks periodically
    
    def with_base_context(self, context: LogContext) -> 'SinkLoggerConfig':
        """Create a new config with updated base context."""
        return SinkLoggerConfig(
            name=self.name,
            pipeline=self.pipeline,
            base_context=context.merge(self.base_context) if self.base_context else context,
            capture_source=self.capture_source,
            capture_exceptions=self.capture_exceptions,
            auto_flush_interval=self.auto_flush_interval
        )
    
    def with_pipeline(self, pipeline: SinkPipeline) -> 'SinkLoggerConfig':
        """Create a new config with a different pipeline."""
        return SinkLoggerConfig(
            name=self.name,
            pipeline=pipeline,
            base_context=self.base_context,
            capture_source=self.capture_source,
            capture_exceptions=self.capture_exceptions,
            auto_flush_interval=self.auto_flush_interval
        )


@dataclass(frozen=True)
class SinkEnvironmentConfig:
    """
    Environment configuration with sink support.
    
    This extends EnvironmentConfig to support multi-sink configurations
    for different environments and use cases.
    """
    # Environment type
    environment: str = "development"
    
    # Default log levels
    min_level: LogLevel = LogLevel.INFO
    
    # Base paths
    log_directory: Path = field(default_factory=lambda: Path("logs"))
    
    # Default formatter
    formatter: Formatter = default_json_formatter
    
    # Sink specifications
    sink_specs: List[SinkSpec] = field(default_factory=list)
    
    # Advanced routing
    enable_conditional_routing: bool = False
    routing_rules: List[Callable[[LogRecord], List[Sink]]] = field(default_factory=list)
    
    # Performance settings
    include_thread_info: bool = True
    include_source_location: bool = False
    
    # Application context
    service_name: Optional[str] = None
    version: Optional[str] = None
    
    # Auto-flush settings
    auto_flush_interval: Optional[float] = None
    
    def __post_init__(self):
        """Validate and normalize configuration."""
        if isinstance(self.log_directory, str):
            object.__setattr__(self, 'log_directory', Path(self.log_directory))


# ============================================================================
# SINK FACTORY FUNCTIONS
# ============================================================================

def create_sink_from_spec(spec: SinkSpec, log_directory: Path) -> Sink:
    """
    Create a sink from a specification.
    
    Args:
        spec: Sink specification
        log_directory: Base directory for file-based sinks
    
    Returns:
        Configured sink instance
    """
    config = spec.config
    
    if spec.type == SinkType.CONSOLE:
        sink = ConsoleSink(
            spec.name,
            stream=config.get("stream", "stdout"),
            flush=config.get("flush", True)
        )
    
    elif spec.type == SinkType.FILE:
        file_path = log_directory / config.get("filename", "app.log")
        sink = FileSink(
            spec.name,
            file_path,
            encoding=config.get("encoding", "utf-8"),
            create_dirs=config.get("create_dirs", True),
            append=config.get("append", True)
        )
    
    elif spec.type == SinkType.ROTATING_FILE:
        file_path = log_directory / config.get("filename", "app.log")
        sink = RotatingFileSink(
            spec.name,
            file_path,
            max_bytes=config.get("max_bytes", 100 * 1024 * 1024),
            backup_count=config.get("backup_count", 10),
            encoding=config.get("encoding", "utf-8"),
            rotation_type=config.get("rotation_type", "size")
        )
    
    elif spec.type == SinkType.UDP:
        sink = UDPSink(
            spec.name,
            config["host"],
            config["port"],
            max_packet_size=config.get("max_packet_size", 8192),
            timeout=config.get("timeout", 5.0)
        )
    
    elif spec.type == SinkType.TCP:
        sink = TCPSink(
            spec.name,
            config["host"],
            config["port"],
            timeout=config.get("timeout", 10.0),
            keepalive=config.get("keepalive", True),
            reconnect_attempts=config.get("reconnect_attempts", 3)
        )
    
    elif spec.type == SinkType.HTTP:
        sink = HTTPSink(
            spec.name,
            config["url"],
            method=config.get("method", "POST"),
            headers=config.get("headers"),
            timeout=config.get("timeout", 30.0),
            max_retries=config.get("max_retries", 3)
        )
    
    elif spec.type == SinkType.ELASTICSEARCH:
        sink = create_elasticsearch_sink(
            spec.name,
            config["host"],
            port=config.get("port", 9200),
            index=config.get("index", "logs"),
            doc_type=config.get("doc_type", "_doc")
        )
    
    elif spec.type == SinkType.SPLUNK:
        sink = create_splunk_sink(
            spec.name,
            config["host"],
            port=config.get("port", 8088),
            token=config["token"],
            index=config.get("index", "main")
        )
    
    elif spec.type == SinkType.NULL:
        sink = NullSink(spec.name)
    
    else:
        raise ValueError(f"Unknown sink type: {spec.type}")
    
    # Apply conditional wrapper if needed
    if spec.condition:
        sink = ConditionalSink(f"{spec.name}_conditional", sink, spec.condition)
    
    # Apply buffering if requested
    if spec.buffer_size or spec.flush_interval:
        sink = BufferedSink(
            f"{spec.name}_buffered",
            sink,
            buffer_size=spec.buffer_size or 1000,
            flush_interval=spec.flush_interval or 5.0
        )
    
    return sink


# ============================================================================
# CONFIGURATION PRESETS
# ============================================================================

def development_sink_config(
    log_directory: Union[str, Path] = "logs",
    service_name: Optional[str] = None,
    version: Optional[str] = None,
    include_network: bool = False
) -> SinkEnvironmentConfig:
    """Create sink configuration optimized for development."""
    
    sink_specs = [
        # Console output for immediate feedback
        SinkSpec(SinkType.CONSOLE, "console", {"stream": "stdout", "flush": True}),
        
        # File output for persistence
        SinkSpec(SinkType.FILE, "app_file", {"filename": "app.log"}),
        
        # Separate debug file
        SinkSpec(
            SinkType.FILE, 
            "debug_file", 
            {"filename": "debug.log"},
            condition=lambda record: record.level == LogLevel.DEBUG
        ),
    ]
    
    # Optional network sink for development testing
    if include_network:
        sink_specs.append(
            SinkSpec(SinkType.UDP, "dev_logstash", {
                "host": "localhost",
                "port": 5000
            })
        )
    
    return SinkEnvironmentConfig(
        environment="development",
        min_level=LogLevel.DEBUG,
        log_directory=Path(log_directory),
        formatter=simple_text_formatter,  # Human-readable for dev
        sink_specs=sink_specs,
        include_thread_info=True,
        include_source_location=True,  # Helpful for debugging
        service_name=service_name,
        version=version
    )


def production_sink_config(
    log_directory: Union[str, Path] = "/var/log",
    service_name: Optional[str] = None,
    version: Optional[str] = None,
    elasticsearch_host: Optional[str] = None,
    splunk_config: Optional[Dict[str, Any]] = None,
    custom_webhooks: Optional[List[str]] = None
) -> SinkEnvironmentConfig:
    """Create sink configuration optimized for production log shipping."""
    
    sink_specs = [
        # Minimal console output (errors only)
        SinkSpec(
            SinkType.CONSOLE, 
            "console_errors",
            {"stream": "stderr", "flush": True},
            condition=lambda record: record.level >= LogLevel.ERROR
        ),
        
        # Rotating application logs
        SinkSpec(SinkType.ROTATING_FILE, "app_logs", {
            "filename": "app.log",
            "max_bytes": 100 * 1024 * 1024,  # 100MB
            "backup_count": 30,
            "rotation_type": "size"
        }),
        
        # Separate error logs with longer retention
        SinkSpec(
            SinkType.ROTATING_FILE, 
            "error_logs",
            {
                "filename": "errors.log",
                "max_bytes": 50 * 1024 * 1024,  # 50MB
                "backup_count": 90  # 90 files = longer retention
            },
            condition=lambda record: record.level >= LogLevel.ERROR
        ),
    ]
    
    # Elasticsearch integration
    if elasticsearch_host:
        sink_specs.append(
            SinkSpec(SinkType.ELASTICSEARCH, "elasticsearch", {
                "host": elasticsearch_host,
                "port": 9200,
                "index": f"logs-{service_name or 'app'}"
            })
        )
    
    # Splunk integration
    if splunk_config:
        sink_specs.append(
            SinkSpec(SinkType.SPLUNK, "splunk", splunk_config)
        )
    
    # Custom webhooks for alerts/integrations
    if custom_webhooks:
        for i, webhook_url in enumerate(custom_webhooks):
            sink_specs.append(
                SinkSpec(SinkType.HTTP, f"webhook_{i}", {
                    "url": webhook_url,
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"}
                })
            )
    
    return SinkEnvironmentConfig(
        environment="production",
        min_level=LogLevel.INFO,
        log_directory=Path(log_directory),
        formatter=default_json_formatter,  # Structured for processing
        sink_specs=sink_specs,
        include_thread_info=True,
        include_source_location=False,  # Performance consideration
        service_name=service_name,
        version=version,
        auto_flush_interval=10.0  # Flush every 10 seconds
    )


def microservices_sink_config(
    log_directory: Union[str, Path] = "logs",
    service_name: str = "microservice",
    version: Optional[str] = None,
    log_aggregator_host: str = "logstash",
    log_aggregator_port: int = 5000,
    metrics_endpoint: Optional[str] = None
) -> SinkEnvironmentConfig:
    """Create sink configuration optimized for microservices architecture."""
    
    sink_specs = [
        # Local file for debugging
        SinkSpec(SinkType.ROTATING_FILE, "local_logs", {
            "filename": f"{service_name}.log",
            "max_bytes": 50 * 1024 * 1024,  # 50MB
            "backup_count": 5  # Limited local storage
        }),
        
        # Central log aggregation (primary)
        SinkSpec(SinkType.UDP, "log_aggregator", {
            "host": log_aggregator_host,
            "port": log_aggregator_port
        }),
        
        # Buffered console for container logs
        SinkSpec(
            SinkType.CONSOLE,
            "container_logs", 
            {"stream": "stdout", "flush": False},
            buffer_size=100,
            flush_interval=1.0
        ),
    ]
    
    # Optional metrics endpoint for structured logs
    if metrics_endpoint:
        sink_specs.append(
            SinkSpec(
                SinkType.HTTP, 
                "metrics",
                {"url": metrics_endpoint, "method": "POST"},
                condition=lambda record: record.fields and "metric" in record.fields
            )
        )
    
    # Conditional routing based on service context
    routing_rules = [
        create_field_router("component", {
            "database": [FileSink("db_logs", Path(log_directory) / "database.log")],
            "cache": [FileSink("cache_logs", Path(log_directory) / "cache.log")],
            "api": [FileSink("api_logs", Path(log_directory) / "api.log")],
        })
    ]
    
    return SinkEnvironmentConfig(
        environment="microservices",
        min_level=LogLevel.INFO,
        log_directory=Path(log_directory),
        formatter=default_json_formatter,
        sink_specs=sink_specs,
        enable_conditional_routing=True,
        routing_rules=routing_rules,
        include_thread_info=True,
        include_source_location=False,
        service_name=service_name,
        version=version,
        auto_flush_interval=5.0
    )


def high_performance_sink_config(
    log_directory: Union[str, Path] = "logs",
    service_name: Optional[str] = None,
    udp_endpoints: Optional[List[tuple[str, int]]] = None
) -> SinkEnvironmentConfig:
    """Create sink configuration optimized for high-performance scenarios."""
    
    sink_specs = [
        # Buffered file output for performance
        SinkSpec(
            SinkType.ROTATING_FILE,
            "high_perf_logs",
            {
                "filename": "high_perf.log",
                "max_bytes": 500 * 1024 * 1024,  # 500MB files
                "backup_count": 10
            },
            buffer_size=5000,  # Large buffer
            flush_interval=1.0   # Frequent flushes
        ),
        
        # Minimal console (errors only, no buffering)
        SinkSpec(
            SinkType.CONSOLE,
            "critical_console",
            {"stream": "stderr", "flush": True},
            condition=lambda record: record.level >= LogLevel.CRITICAL
        ),
    ]
    
    # Multiple UDP endpoints for redundancy
    if udp_endpoints:
        for i, (host, port) in enumerate(udp_endpoints):
            sink_specs.append(
                SinkSpec(SinkType.UDP, f"udp_endpoint_{i}", {
                    "host": host,
                    "port": port,
                    "max_packet_size": 8192
                })
            )
    
    return SinkEnvironmentConfig(
        environment="high_performance",
        min_level=LogLevel.INFO,
        log_directory=Path(log_directory),
        formatter=compact_formatter,  # Minimal overhead
        sink_specs=sink_specs,
        include_thread_info=False,  # Skip for performance
        include_source_location=False,  # Skip for performance
        service_name=service_name,
        auto_flush_interval=0.5  # Aggressive flushing
    )


# ============================================================================
# LOGGER FACTORY FUNCTIONS
# ============================================================================

def create_sink_logger_config(
    name: str,
    env_config: SinkEnvironmentConfig,
    custom_sinks: Optional[List[Sink]] = None
) -> SinkLoggerConfig:
    """
    Create a sink-based logger configuration.
    
    Args:
        name: Logger name
        env_config: Environment configuration
        custom_sinks: Optional additional custom sinks
    
    Returns:
        SinkLoggerConfig ready for creating a sink-based logger
    """
    # Create sinks from specifications
    sinks = []
    for spec in env_config.sink_specs:
        sink = create_sink_from_spec(spec, env_config.log_directory)
        sinks.append(sink)
    
    # Add any custom sinks
    if custom_sinks:
        sinks.extend(custom_sinks)
    
    # Create enrichers
    enrichers = []
    if env_config.include_thread_info:
        enrichers.append(thread_enricher)
    enrichers.append(exception_enricher)
    
    # Add base context enricher if available
    base_context = None
    if env_config.service_name or env_config.version:
        base_context = LogContext(
            service_name=env_config.service_name,
            version=env_config.version,
            environment=env_config.environment
        )
        if base_context:
            enrichers.append(context_enricher(base_context))
    
    # Create pipeline configuration
    if env_config.enable_conditional_routing and env_config.routing_rules:
        # Use conditional routing
        pipeline_config = SinkPipelineConfig(
            min_level=env_config.min_level,
            enrichers=tuple(enrichers),
            filters=(),
            formatter=env_config.formatter,
            sinks=tuple(sinks),
            enable_conditional_routing=True,
            routing_rules=tuple(env_config.routing_rules)
        )
    else:
        # Use multi-sink approach
        pipeline_config = SinkPipelineConfig(
            min_level=env_config.min_level,
            enrichers=tuple(enrichers),
            filters=(),
            formatter=env_config.formatter,
            sinks=tuple(sinks)
        )
    
    pipeline = SinkPipeline(pipeline_config)
    
    return SinkLoggerConfig(
        name=name,
        pipeline=pipeline,
        base_context=base_context,
        capture_source=env_config.include_source_location,
        capture_exceptions=True,
        auto_flush_interval=env_config.auto_flush_interval
    )
