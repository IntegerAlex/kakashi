"""
Asynchronous pipeline integration.

This module extends the functional pipeline system to support non-blocking I/O
through the async backend. It provides async versions of pipeline components
that maintain the same functional design while delivering dramatically improved
performance.
"""

from typing import Callable, Optional, List, Dict, Any, Union
from dataclasses import dataclass
import time

from .records import LogRecord, LogLevel
from .pipeline import (
    Pipeline, PipelineConfig, Enricher, Filter, Formatter,
    thread_enricher, exception_enricher, default_json_formatter, simple_text_formatter, console_writer, file_writer
)
from .async_backend import (
    AsyncBackend, AsyncConfig, create_async_writer, 
    get_async_backend
)


@dataclass(frozen=True)
class AsyncPipelineConfig:
    """Configuration for asynchronous pipeline."""
    # Standard pipeline config
    pipeline_config: PipelineConfig
    
    # Async-specific settings
    async_config: AsyncConfig
    
    # Performance settings
    enable_async: bool = True  # Can disable async for testing/debugging
    fallback_to_sync: bool = True  # Fallback to sync if async fails
    
    # Batch processing settings
    enable_enricher_batching: bool = False  # Experimental: batch enricher processing


class AsyncPipeline:
    """
    Asynchronous version of the functional pipeline.
    
    This pipeline processes enrichers and formatters synchronously (for consistency)
    but performs all I/O operations asynchronously through the async backend.
    This provides the best balance of consistency and performance.
    """
    
    def __init__(
        self, 
        config: AsyncPipelineConfig,
        backend: Optional[AsyncBackend] = None
    ):
        """
        Initialize async pipeline.
        
        Args:
            config: Async pipeline configuration
            backend: Optional custom async backend
        """
        self.config = config
        self.backend = backend or get_async_backend(config.async_config)
        
        # Create async writers from sync writers
        self.async_writers = []
        for sync_writer in config.pipeline_config.writers:
            async_writer = create_async_writer(sync_writer, self.backend)
            self.async_writers.append(async_writer)
        
        # Keep sync pipeline for fallback
        self.sync_pipeline = Pipeline(config.pipeline_config)
        
        # Performance tracking
        self.messages_processed = 0
        self.total_processing_time = 0.0
        self.last_reset_time = time.time()
    
    def process(self, record: LogRecord) -> None:
        """
        Process a log record through the async pipeline.
        
        This method:
        1. Applies enrichers and filters synchronously (for consistency)
        2. Formats the message synchronously
        3. Enqueues the formatted message for async I/O
        4. Returns immediately (non-blocking)
        
        Args:
            record: The log record to process
        """
        start_time = time.perf_counter()
        
        # Fast level check first
        if record.level < self.config.pipeline_config.min_level:
            return
        
        # If async is disabled or backend not running, fallback to sync
        if not self.config.enable_async or not self.backend.is_running():
            if self.config.fallback_to_sync:
                self.sync_pipeline.process(record)
            return
        
        try:
            # Apply enrichers (synchronous for consistency)
            enriched_record = record
            for enricher in self.config.pipeline_config.enrichers:
                enriched_record = enricher(enriched_record)
            
            # Apply filters (synchronous)
            for filter_func in self.config.pipeline_config.filters:
                if not filter_func(enriched_record):
                    return
            
            # Format the record (synchronous)
            formatted_message = self.config.pipeline_config.formatter(enriched_record)
            
            # Send to async writers (non-blocking)
            for async_writer in self.async_writers:
                async_writer(formatted_message, enriched_record)
            
            # Update statistics
            self.messages_processed += 1
            self.total_processing_time += time.perf_counter() - start_time
            
        except Exception:
            # Fallback to sync pipeline on errors
            if self.config.fallback_to_sync:
                try:
                    self.sync_pipeline.process(record)
                except Exception:
                    # Last resort: ignore the error to prevent crashes
                    pass
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this pipeline."""
        current_time = time.time()
        elapsed = current_time - self.last_reset_time
        
        if self.messages_processed > 0:
            avg_processing_time = self.total_processing_time / self.messages_processed
            throughput = self.messages_processed / elapsed if elapsed > 0 else 0
        else:
            avg_processing_time = 0
            throughput = 0
        
        backend_stats = self.backend.get_stats() if self.backend else {}
        
        return {
            'messages_processed': self.messages_processed,
            'avg_processing_time_ns': avg_processing_time * 1_000_000_000,
            'throughput_msg_per_sec': throughput,
            'total_processing_time': self.total_processing_time,
            'elapsed_time': elapsed,
            'backend_stats': backend_stats,
        }
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self.messages_processed = 0
        self.total_processing_time = 0.0
        self.last_reset_time = time.time()
    
    def shutdown(self, timeout: float = 5.0) -> None:
        """Shutdown the async pipeline gracefully."""
        if self.backend:
            self.backend.shutdown(timeout)
    
    # Compatibility methods with sync Pipeline
    def with_enricher(self, enricher: Enricher) -> 'AsyncPipeline':
        """Create a new async pipeline with an additional enricher."""
        new_enrichers = self.config.pipeline_config.enrichers + (enricher,)
        new_pipeline_config = PipelineConfig(
            min_level=self.config.pipeline_config.min_level,
            enrichers=new_enrichers,
            filters=self.config.pipeline_config.filters,
            formatter=self.config.pipeline_config.formatter,
            writers=self.config.pipeline_config.writers
        )
        new_async_config = AsyncPipelineConfig(
            pipeline_config=new_pipeline_config,
            async_config=self.config.async_config,
            enable_async=self.config.enable_async,
            fallback_to_sync=self.config.fallback_to_sync
        )
        return AsyncPipeline(new_async_config, self.backend)
    
    def with_filter(self, filter_func: Filter) -> 'AsyncPipeline':
        """Create a new async pipeline with an additional filter."""
        new_filters = self.config.pipeline_config.filters + (filter_func,)
        new_pipeline_config = PipelineConfig(
            min_level=self.config.pipeline_config.min_level,
            enrichers=self.config.pipeline_config.enrichers,
            filters=new_filters,
            formatter=self.config.pipeline_config.formatter,
            writers=self.config.pipeline_config.writers
        )
        new_async_config = AsyncPipelineConfig(
            pipeline_config=new_pipeline_config,
            async_config=self.config.async_config,
            enable_async=self.config.enable_async,
            fallback_to_sync=self.config.fallback_to_sync
        )
        return AsyncPipeline(new_async_config, self.backend)


# ============================================================================
# ASYNC PIPELINE FACTORY FUNCTIONS
# ============================================================================

def create_async_console_pipeline(
    min_level: LogLevel = LogLevel.INFO,
    formatter: Formatter = simple_text_formatter,
    include_thread_info: bool = True,
    async_config: Optional[AsyncConfig] = None
) -> AsyncPipeline:
    """Create an async pipeline that logs to console."""
    enrichers = []
    if include_thread_info:
        enrichers.append(thread_enricher)
    enrichers.append(exception_enricher)
    
    pipeline_config = PipelineConfig(
        min_level=min_level,
        enrichers=tuple(enrichers),
        filters=(),
        formatter=formatter,
        writers=(console_writer,)
    )
    
    async_pipeline_config = AsyncPipelineConfig(
        pipeline_config=pipeline_config,
        async_config=async_config or AsyncConfig()
    )
    
    return AsyncPipeline(async_pipeline_config)


def create_async_file_pipeline(
    file_path: Union[str, 'Path'],
    min_level: LogLevel = LogLevel.DEBUG,
    formatter: Formatter = default_json_formatter,
    include_thread_info: bool = True,
    async_config: Optional[AsyncConfig] = None
) -> AsyncPipeline:
    """Create an async pipeline that logs to a file."""
    enrichers = []
    if include_thread_info:
        enrichers.append(thread_enricher)
    enrichers.append(exception_enricher)
    
    pipeline_config = PipelineConfig(
        min_level=min_level,
        enrichers=tuple(enrichers),
        filters=(),
        formatter=formatter,
        writers=(file_writer(file_path),)
    )
    
    async_pipeline_config = AsyncPipelineConfig(
        pipeline_config=pipeline_config,
        async_config=async_config or AsyncConfig()
    )
    
    return AsyncPipeline(async_pipeline_config)


def create_async_dual_pipeline(
    file_path: Union[str, 'Path'],
    console_level: LogLevel = LogLevel.INFO,
    file_level: LogLevel = LogLevel.DEBUG,
    console_formatter: Formatter = simple_text_formatter,
    file_formatter: Formatter = default_json_formatter,
    async_config: Optional[AsyncConfig] = None
) -> AsyncPipeline:
    """Create an async pipeline that logs to both console and file."""
    enrichers = (thread_enricher, exception_enricher)
    
    # Use the lower level as the base
    min_level = min(console_level, file_level)
    
    # Create a custom formatter that applies different formatting based on destination
    # For now, we'll use the file formatter as primary and let writers handle specifics
    
    pipeline_config = PipelineConfig(
        min_level=min_level,
        enrichers=enrichers,
        filters=(),
        formatter=file_formatter,  # Primary formatter
        writers=(console_writer, file_writer(file_path))
    )
    
    async_pipeline_config = AsyncPipelineConfig(
        pipeline_config=pipeline_config,
        async_config=async_config or AsyncConfig()
    )
    
    return AsyncPipeline(async_pipeline_config)


def create_high_performance_pipeline(
    file_path: Union[str, 'Path'],
    min_level: LogLevel = LogLevel.INFO,
    max_queue_size: int = 50000,  # Large queue for high throughput
    worker_count: int = 2,  # Multiple workers for high volume
    batch_size: int = 500,  # Large batches for efficiency
    enable_batching: bool = True
) -> AsyncPipeline:
    """
    Create a high-performance async pipeline optimized for maximum throughput.
    
    This configuration is optimized for scenarios with very high message volume
    where maximum throughput is more important than individual message latency.
    """
    # Minimal enrichers for maximum speed
    enrichers = (exception_enricher,)  # Skip thread info for speed
    
    # High-performance async configuration
    async_config = AsyncConfig(
        max_queue_size=max_queue_size,
        worker_count=worker_count,
        batch_size=batch_size,
        batch_timeout=0.05,  # Shorter timeout for responsiveness
        enable_batching=enable_batching,
        queue_overflow_strategy="drop_oldest"  # Don't block on overflow
    )
    
    pipeline_config = PipelineConfig(
        min_level=min_level,
        enrichers=enrichers,
        filters=(),
        formatter=default_json_formatter,  # JSON is efficient
        writers=(file_writer(file_path),)
    )
    
    async_pipeline_config = AsyncPipelineConfig(
        pipeline_config=pipeline_config,
        async_config=async_config
    )
    
    return AsyncPipeline(async_pipeline_config)


def create_network_pipeline(
    network_writer: Callable[[str], None],
    min_level: LogLevel = LogLevel.INFO,
    async_config: Optional[AsyncConfig] = None
) -> AsyncPipeline:
    """
    Create an async pipeline for network logging (e.g., to log aggregators).
    
    This is perfect for sending logs to systems like Elasticsearch, Splunk,
    or custom log aggregation services without blocking the application.
    """
    enrichers = (thread_enricher, exception_enricher)
    
    # Network-optimized async config
    if async_config is None:
        async_config = AsyncConfig(
            max_queue_size=20000,  # Large queue for network buffering
            worker_count=1,  # Single worker to maintain order
            batch_size=100,  # Moderate batching for network efficiency
            enable_batching=True,
            max_error_retries=5,  # More retries for network issues
            error_retry_delay=0.5,  # Longer delay for network errors
            queue_overflow_strategy="drop_oldest"
        )
    
    pipeline_config = PipelineConfig(
        min_level=min_level,
        enrichers=enrichers,
        filters=(),
        formatter=default_json_formatter,  # Structured data for network
        writers=(network_writer,)
    )
    
    async_pipeline_config = AsyncPipelineConfig(
        pipeline_config=pipeline_config,
        async_config=async_config
    )
    
    return AsyncPipeline(async_pipeline_config)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def benchmark_async_vs_sync(
    pipeline_factory: Callable[[], Pipeline],
    async_pipeline_factory: Callable[[], AsyncPipeline],
    message_count: int = 10000,
    thread_count: int = 4
) -> Dict[str, Any]:
    """
    Benchmark async vs sync pipeline performance.
    
    Args:
        pipeline_factory: Function that creates sync pipeline
        async_pipeline_factory: Function that creates async pipeline
        message_count: Number of messages to log per thread
        thread_count: Number of concurrent threads
    
    Returns:
        Dictionary with benchmark results
    """
    import threading
    import time
    from .records import create_log_record
    
    def sync_worker(pipeline: Pipeline, messages: int, results: List[float]):
        """Worker function for sync benchmark."""
        start_time = time.perf_counter()
        for i in range(messages):
            record = create_log_record(
                LogLevel.INFO, 
                "benchmark", 
                f"Sync message {i}",
                fields={"iteration": i, "worker": threading.current_thread().name}
            )
            pipeline.process(record)
        end_time = time.perf_counter()
        results.append(end_time - start_time)
    
    def async_worker(pipeline: AsyncPipeline, messages: int, results: List[float]):
        """Worker function for async benchmark."""
        start_time = time.perf_counter()
        for i in range(messages):
            record = create_log_record(
                LogLevel.INFO,
                "benchmark", 
                f"Async message {i}",
                fields={"iteration": i, "worker": threading.current_thread().name}
            )
            pipeline.process(record)
        end_time = time.perf_counter()
        results.append(end_time - start_time)
    
    # Benchmark sync pipeline
    sync_pipeline = pipeline_factory()
    sync_results = []
    sync_threads = []
    
    sync_start = time.perf_counter()
    for i in range(thread_count):
        thread = threading.Thread(
            target=sync_worker, 
            args=(sync_pipeline, message_count, sync_results)
        )
        sync_threads.append(thread)
        thread.start()
    
    for thread in sync_threads:
        thread.join()
    sync_end = time.perf_counter()
    
    # Benchmark async pipeline
    async_pipeline = async_pipeline_factory()
    async_results = []
    async_threads = []
    
    async_start = time.perf_counter()
    for i in range(thread_count):
        thread = threading.Thread(
            target=async_worker, 
            args=(async_pipeline, message_count, async_results)
        )
        async_threads.append(thread)
        thread.start()
    
    for thread in async_threads:
        thread.join()
    
    # Wait for async pipeline to finish processing
    async_pipeline.backend.queue.join()
    async_end = time.perf_counter()
    
    # Calculate results
    total_messages = message_count * thread_count
    
    sync_total_time = sync_end - sync_start
    async_total_time = async_end - async_start
    
    sync_throughput = total_messages / sync_total_time
    async_throughput = total_messages / async_total_time
    
    # Get async pipeline stats
    async_stats = async_pipeline.get_performance_stats()
    
    # Cleanup
    async_pipeline.shutdown()
    
    return {
        'total_messages': total_messages,
        'thread_count': thread_count,
        'message_count_per_thread': message_count,
        
        'sync_total_time': sync_total_time,
        'sync_throughput': sync_throughput,
        'sync_avg_thread_time': sum(sync_results) / len(sync_results),
        
        'async_total_time': async_total_time,
        'async_throughput': async_throughput,
        'async_avg_thread_time': sum(async_results) / len(async_results),
        
        'performance_improvement': async_throughput / sync_throughput,
        'latency_improvement': (sum(sync_results) / len(sync_results)) / (sum(async_results) / len(async_results)),
        
        'async_pipeline_stats': async_stats,
    }
