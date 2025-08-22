"""
Sink-based pipeline architecture.

This module extends the functional pipeline system to work with the new
Sinks architecture, enabling powerful log shipping capabilities with
multiple destinations, conditional routing, and advanced features.
"""

from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass
import threading

from .records import LogRecord, LogLevel
from .pipeline import Enricher, Filter, Formatter
from .sinks import Sink, SinkResult, get_sink_registry


@dataclass(frozen=True)
class SinkPipelineConfig:
    """Configuration for sink-based pipeline."""
    min_level: LogLevel = LogLevel.INFO
    enrichers: tuple[Enricher, ...] = ()
    filters: tuple[Filter, ...] = ()
    formatter: Formatter = None
    sinks: tuple[Sink, ...] = ()
    
    # Advanced routing options
    enable_conditional_routing: bool = False
    routing_rules: tuple[Callable[[LogRecord], List[Sink]], ...] = ()
    
    # Error handling
    continue_on_sink_error: bool = True
    max_sink_errors: int = 100
    
    def __post_init__(self):
        """Validate the pipeline configuration."""
        if not self.formatter:
            from .pipeline import default_json_formatter
            object.__setattr__(self, 'formatter', default_json_formatter)
        if not self.sinks and not self.routing_rules:
            from .sinks import ConsoleSink
            object.__setattr__(self, 'sinks', (ConsoleSink("default"),))


class SinkPipeline:
    """
    Pipeline that processes log records through sinks.
    
    This pipeline extends the functional logging concept to work with
    the Sinks architecture, enabling:
    - Multiple destination logging
    - Conditional routing based on log content
    - Per-sink error handling and statistics
    - Advanced features like buffering and retries
    """
    
    def __init__(self, config: SinkPipelineConfig):
        """
        Initialize sink pipeline.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.sink_error_counts: Dict[str, int] = {}
        self.messages_processed = 0
        self.messages_routed = 0
        self.routing_failures = 0
        self._lock = threading.RLock()
        
        # Register all sinks with global registry
        registry = get_sink_registry()
        for sink in self.config.sinks:
            registry.register(sink)
    
    def process(self, record: LogRecord) -> None:
        """
        Process a log record through the sink pipeline.
        
        This method:
        1. Applies enrichers and filters
        2. Formats the message
        3. Routes to appropriate sinks based on configuration
        4. Handles per-sink errors gracefully
        
        Args:
            record: The log record to process
        """
        # Fast level check first
        if record.level < self.config.min_level:
            return
        
        with self._lock:
            self.messages_processed += 1
        
        try:
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
            
            # Route to sinks
            self._route_to_sinks(formatted_message, enriched_record)
            
        except Exception:
            # Never let pipeline errors crash the application
            pass
    
    def _route_to_sinks(self, formatted_message: str, record: LogRecord) -> None:
        """Route formatted message to appropriate sinks."""
        sinks_to_write = []
        
        if self.config.enable_conditional_routing and self.config.routing_rules:
            # Use routing rules to determine sinks
            for routing_rule in self.config.routing_rules:
                try:
                    rule_sinks = routing_rule(record)
                    sinks_to_write.extend(rule_sinks)
                except Exception:
                    with self._lock:
                        self.routing_failures += 1
        else:
            # Use configured sinks
            sinks_to_write = list(self.config.sinks)
        
        # Write to all determined sinks
        for sink in sinks_to_write:
            self._write_to_sink(sink, formatted_message, record)
        
        if sinks_to_write:
            with self._lock:
                self.messages_routed += 1
    
    def _write_to_sink(self, sink: Sink, formatted_message: str, record: LogRecord) -> None:
        """Write to a single sink with error handling."""
        try:
            result = sink.write(formatted_message, record)
            
            if result == SinkResult.ERROR:
                self._handle_sink_error(sink)
            elif result == SinkResult.RETRY:
                # For now, treat retries as errors
                # Future enhancement: implement retry logic
                self._handle_sink_error(sink)
                
        except Exception:
            self._handle_sink_error(sink)
    
    def _handle_sink_error(self, sink: Sink) -> None:
        """Handle errors from a specific sink."""
        with self._lock:
            self.sink_error_counts[sink.name] = self.sink_error_counts.get(sink.name, 0) + 1
            
            # If a sink has too many errors, we could disable it
            if self.sink_error_counts[sink.name] > self.config.max_sink_errors:
                # Future enhancement: disable problematic sinks
                pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        with self._lock:
            sink_stats = {}
            for sink in self.config.sinks:
                sink_stats[sink.name] = sink.get_stats()
            
            return {
                'messages_processed': self.messages_processed,
                'messages_routed': self.messages_routed,
                'routing_failures': self.routing_failures,
                'sink_error_counts': dict(self.sink_error_counts),
                'sink_stats': sink_stats,
                'active_sinks': len(self.config.sinks),
            }
    
    def flush(self) -> None:
        """Flush all sinks in the pipeline."""
        for sink in self.config.sinks:
            try:
                sink.flush()
            except Exception:
                pass
    
    def close(self) -> None:
        """Close all sinks in the pipeline."""
        for sink in self.config.sinks:
            try:
                sink.close()
            except Exception:
                pass
    
    # Compatibility methods with standard Pipeline
    def with_enricher(self, enricher: Enricher) -> 'SinkPipeline':
        """Create a new pipeline with an additional enricher."""
        new_enrichers = self.config.enrichers + (enricher,)
        new_config = SinkPipelineConfig(
            min_level=self.config.min_level,
            enrichers=new_enrichers,
            filters=self.config.filters,
            formatter=self.config.formatter,
            sinks=self.config.sinks,
            enable_conditional_routing=self.config.enable_conditional_routing,
            routing_rules=self.config.routing_rules,
            continue_on_sink_error=self.config.continue_on_sink_error,
            max_sink_errors=self.config.max_sink_errors
        )
        return SinkPipeline(new_config)
    
    def with_filter(self, filter_func: Filter) -> 'SinkPipeline':
        """Create a new pipeline with an additional filter."""
        new_filters = self.config.filters + (filter_func,)
        new_config = SinkPipelineConfig(
            min_level=self.config.min_level,
            enrichers=self.config.enrichers,
            filters=new_filters,
            formatter=self.config.formatter,
            sinks=self.config.sinks,
            enable_conditional_routing=self.config.enable_conditional_routing,
            routing_rules=self.config.routing_rules,
            continue_on_sink_error=self.config.continue_on_sink_error,
            max_sink_errors=self.config.max_sink_errors
        )
        return SinkPipeline(new_config)
    
    def with_sink(self, sink: Sink) -> 'SinkPipeline':
        """Create a new pipeline with an additional sink."""
        new_sinks = self.config.sinks + (sink,)
        new_config = SinkPipelineConfig(
            min_level=self.config.min_level,
            enrichers=self.config.enrichers,
            filters=self.config.filters,
            formatter=self.config.formatter,
            sinks=new_sinks,
            enable_conditional_routing=self.config.enable_conditional_routing,
            routing_rules=self.config.routing_rules,
            continue_on_sink_error=self.config.continue_on_sink_error,
            max_sink_errors=self.config.max_sink_errors
        )
        
        # Register new sink
        get_sink_registry().register(sink)
        
        return SinkPipeline(new_config)


# ============================================================================
# SINK PIPELINE FACTORY FUNCTIONS
# ============================================================================

def create_multi_sink_pipeline(
    sinks: List[Sink],
    min_level: LogLevel = LogLevel.INFO,
    formatter: Optional[Formatter] = None,
    include_thread_info: bool = True
) -> SinkPipeline:
    """
    Create a pipeline that writes to multiple sinks.
    
    Args:
        sinks: List of sinks to write to
        min_level: Minimum log level
        formatter: Message formatter
        include_thread_info: Whether to include thread information
    
    Returns:
        SinkPipeline configured for multiple sinks
        
    Example:
        from mylogs.core.sinks import FileSink, ConsoleSink, UDPSink
        
        sinks = [
            ConsoleSink("console"),
            FileSink("file", "app.log"),
            UDPSink("logstash", "localhost", 5000)
        ]
        
        pipeline = create_multi_sink_pipeline(sinks)
        # Now logs go to console, file, and Logstash simultaneously!
    """
    enrichers = []
    if include_thread_info:
        from .pipeline import thread_enricher, exception_enricher
        enrichers.extend([thread_enricher, exception_enricher])
    
    if formatter is None:
        from .pipeline import default_json_formatter
        formatter = default_json_formatter
    
    config = SinkPipelineConfig(
        min_level=min_level,
        enrichers=tuple(enrichers),
        filters=(),
        formatter=formatter,
        sinks=tuple(sinks)
    )
    
    return SinkPipeline(config)


def create_conditional_routing_pipeline(
    routing_rules: List[Callable[[LogRecord], List[Sink]]],
    min_level: LogLevel = LogLevel.INFO,
    formatter: Optional[Formatter] = None
) -> SinkPipeline:
    """
    Create a pipeline with conditional routing based on log content.
    
    Args:
        routing_rules: List of functions that determine which sinks to use
        min_level: Minimum log level
        formatter: Message formatter
    
    Returns:
        SinkPipeline with conditional routing
        
    Example:
        from mylogs.core.sinks import FileSink, UDPSink
        from mylogs.core.records import LogLevel
        
        error_sink = FileSink("errors", "errors.log")
        debug_sink = FileSink("debug", "debug.log")
        alert_sink = UDPSink("alerts", "alert-system", 9999)
        
        def route_by_level(record):
            if record.level >= LogLevel.ERROR:
                return [error_sink, alert_sink]  # Errors go to file + alerts
            elif record.level == LogLevel.DEBUG:
                return [debug_sink]  # Debug only to debug file
            else:
                return [error_sink]  # Everything else to error file
        
        pipeline = create_conditional_routing_pipeline([route_by_level])
    """
    if formatter is None:
        from .pipeline import default_json_formatter
        formatter = default_json_formatter
    
    config = SinkPipelineConfig(
        min_level=min_level,
        enrichers=(),
        filters=(),
        formatter=formatter,
        sinks=(),  # No default sinks when using routing
        enable_conditional_routing=True,
        routing_rules=tuple(routing_rules)
    )
    
    return SinkPipeline(config)


def create_log_shipping_pipeline(
    console_sink: Optional[Sink] = None,
    file_sink: Optional[Sink] = None,
    network_sinks: Optional[List[Sink]] = None,
    min_level: LogLevel = LogLevel.INFO
) -> SinkPipeline:
    """
    Create a comprehensive log shipping pipeline.
    
    This creates a production-ready pipeline that can simultaneously:
    - Log to console for development/debugging
    - Log to files for local storage
    - Ship logs to remote systems (ELK, Splunk, etc.)
    
    Args:
        console_sink: Optional console sink
        file_sink: Optional file sink
        network_sinks: Optional list of network sinks
        min_level: Minimum log level
    
    Returns:
        SinkPipeline configured for comprehensive log shipping
        
    Example:
        from mylogs.core.sinks import ConsoleSink, RotatingFileSink, HTTPSink, create_elasticsearch_sink
        
        pipeline = create_log_shipping_pipeline(
            console_sink=ConsoleSink("console"),
            file_sink=RotatingFileSink("app_logs", "app.log", max_bytes=100*1024*1024),
            network_sinks=[
                create_elasticsearch_sink("elk", "elasticsearch.company.com"),
                HTTPSink("webhook", "https://api.company.com/logs")
            ]
        )
        # Logs now go to console, rotating files, Elasticsearch, and webhook!
    """
    sinks = []
    
    if console_sink:
        sinks.append(console_sink)
    
    if file_sink:
        sinks.append(file_sink)
    
    if network_sinks:
        sinks.extend(network_sinks)
    
    # If no sinks provided, create defaults
    if not sinks:
        from .sinks import ConsoleSink, FileSink
        sinks = [
            ConsoleSink("default_console"),
            FileSink("default_file", "app.log")
        ]
    
    return create_multi_sink_pipeline(sinks, min_level=min_level)


# ============================================================================
# ROUTING UTILITIES
# ============================================================================

def create_level_router(sink_mapping: Dict[LogLevel, List[Sink]]) -> Callable[[LogRecord], List[Sink]]:
    """
    Create a routing function based on log levels.
    
    Args:
        sink_mapping: Mapping from log levels to lists of sinks
    
    Returns:
        Routing function
        
    Example:
        from mylogs.core.sinks import ConsoleSink, FileSink, UDPSink
        
        router = create_level_router({
            LogLevel.DEBUG: [FileSink("debug", "debug.log")],
            LogLevel.INFO: [ConsoleSink("console"), FileSink("info", "app.log")],
            LogLevel.ERROR: [FileSink("errors", "errors.log"), UDPSink("alerts", "alerter", 9999)]
        })
    """
    def route_by_level(record: LogRecord) -> List[Sink]:
        return sink_mapping.get(record.level, [])
    
    return route_by_level


def create_field_router(field_name: str, sink_mapping: Dict[Any, List[Sink]], default_sinks: List[Sink] = None) -> Callable[[LogRecord], List[Sink]]:
    """
    Create a routing function based on log record fields.
    
    Args:
        field_name: Name of the field to route on
        sink_mapping: Mapping from field values to lists of sinks
        default_sinks: Default sinks if field not found or value not mapped
    
    Returns:
        Routing function
        
    Example:
        from mylogs.core.sinks import FileSink
        
        router = create_field_router("service", {
            "api": [FileSink("api_logs", "api.log")],
            "database": [FileSink("db_logs", "database.log")],
            "worker": [FileSink("worker_logs", "workers.log")]
        })
    """
    def route_by_field(record: LogRecord) -> List[Sink]:
        if not record.fields:
            return default_sinks or []
        
        field_value = record.fields.get(field_name)
        sinks = sink_mapping.get(field_value, default_sinks or [])
        return sinks
    
    return route_by_field


def create_context_router(context_field: str, sink_mapping: Dict[Any, List[Sink]], default_sinks: List[Sink] = None) -> Callable[[LogRecord], List[Sink]]:
    """
    Create a routing function based on log record context.
    
    Args:
        context_field: Name of the context field to route on
        sink_mapping: Mapping from context values to lists of sinks
        default_sinks: Default sinks if context not found or value not mapped
    
    Returns:
        Routing function
        
    Example:
        from mylogs.core.sinks import FileSink
        
        router = create_context_router("user_id", {
            "admin": [FileSink("admin_logs", "admin.log")],
            "premium": [FileSink("premium_logs", "premium.log")]
        }, default_sinks=[FileSink("user_logs", "users.log")])
    """
    def route_by_context(record: LogRecord) -> List[Sink]:
        if not record.context or not record.context.custom:
            return default_sinks or []
        
        context_value = record.context.custom.get(context_field)
        sinks = sink_mapping.get(context_value, default_sinks or [])
        return sinks
    
    return route_by_context
