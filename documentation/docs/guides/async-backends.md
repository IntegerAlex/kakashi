---
id: async-backends
title: Async Backends
---

## Async Logging Architecture

For high-throughput applications, Kakashi provides async backends that perform non-blocking I/O operations and batch writes for optimal performance.

### When to Use Async Logging

- **High-throughput applications** (>1000 logs/second)
- **I/O-bound workloads** where logging shouldn't block request processing
- **Production environments** where performance is critical
- **Applications with strict latency requirements**

### Basic Async Setup

```python
import kakashi

# Enable async logging for production
kakashi.setup("production", async_logging=True)

# Or explicitly configure
from kakashi.core.async_backend import AsyncConfig

config = AsyncConfig(
    buffer_size=1000,
    flush_interval=1.0,
    max_workers=4
)
```

### Async Pipeline Components

#### AsyncPipeline

```python
from kakashi.core.async_pipeline import AsyncPipeline, AsyncPipelineConfig

config = AsyncPipelineConfig(
    min_level=LogLevel.INFO,
    enrichers=(timestamp_enricher, context_enricher),
    filters=(level_filter,),
    formatter=optimized_json_formatter,
    writers=(async_file_writer, async_network_writer),
    
    # Async-specific settings
    buffer_size=500,
    flush_interval=0.5,
    backpressure_limit=5000
)

pipeline = AsyncPipeline(config)
```

#### Async Writers

```python
import asyncio
import aiofiles
from typing import List

class AsyncFileWriter:
    """High-performance async file writer with batching."""
    
    def __init__(self, file_path: Path, batch_size: int = 100):
        self.file_path = file_path
        self.batch_size = batch_size
        self.buffer: List[str] = []
        self._lock = asyncio.Lock()
    
    async def write(self, message: str) -> None:
        async with self._lock:
            self.buffer.append(message)
            
            if len(self.buffer) >= self.batch_size:
                await self._flush_buffer()
    
    async def _flush_buffer(self) -> None:
        if not self.buffer:
            return
        
        try:
            async with aiofiles.open(self.file_path, 'a') as f:
                await f.write('\n'.join(self.buffer) + '\n')
                await f.fsync()  # Ensure data is written to disk
        except OSError as e:
            print(f"Async write error: {e}", file=sys.stderr)
        finally:
            self.buffer.clear()

class AsyncNetworkWriter:
    """Async HTTP writer with retry logic."""
    
    def __init__(self, endpoint: str, timeout: float = 5.0, max_retries: int = 3):
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
    
    async def write(self, message: str) -> None:
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(
                    self.endpoint,
                    json={'log': message},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status < 400:
                        return
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == self.max_retries - 1:
                    print(f"Async network write failed: {e}", file=sys.stderr)
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Backpressure Handling

Async pipelines handle backpressure to prevent memory exhaustion:

```python
class BackpressureConfig:
    """Configuration for backpressure handling."""
    
    def __init__(self):
        self.buffer_size = 1000           # Normal buffer size
        self.warning_threshold = 800      # Warn when buffer is 80% full
        self.drop_threshold = 1200        # Drop logs when buffer exceeds this
        self.drop_strategy = 'oldest'     # 'oldest', 'newest', or 'priority'

async def handle_backpressure(pipeline: AsyncPipeline, record: LogRecord) -> bool:
    """Handle backpressure by dropping or queuing logs."""
    buffer_size = pipeline.get_buffer_size()
    config = pipeline.backpressure_config
    
    if buffer_size > config.drop_threshold:
        # Drop logs based on strategy
        if config.drop_strategy == 'oldest':
            pipeline.drop_oldest_logs(buffer_size - config.buffer_size)
        elif config.drop_strategy == 'priority':
            pipeline.drop_low_priority_logs()
        
        # Log dropped message count
        await pipeline.process_internal(LogRecord(
            timestamp=time.time(),
            level=LogLevel.WARNING,
            logger_name='kakashi.backpressure',
            message=f"Dropped {buffer_size - config.buffer_size} logs due to backpressure"
        ))
        
        return False  # Don't process this log
    
    elif buffer_size > config.warning_threshold:
        # Warn about approaching limit
        await pipeline.process_internal(LogRecord(
            timestamp=time.time(),
            level=LogLevel.WARNING,
            logger_name='kakashi.backpressure',
            message=f"Buffer {buffer_size}/{config.buffer_size} (approaching limit)"
        ))
    
    return True  # Process the log
```

### Performance Monitoring

Monitor async pipeline performance:

```python
from dataclasses import dataclass
from typing import Dict
import time

@dataclass
class AsyncMetrics:
    """Metrics for async pipeline performance."""
    logs_processed: int = 0
    logs_dropped: int = 0
    buffer_size: int = 0
    flush_count: int = 0
    average_flush_time: float = 0.0
    last_flush_time: float = 0.0

class AsyncPipelineMonitor:
    """Monitor async pipeline performance."""
    
    def __init__(self, pipeline: AsyncPipeline):
        self.pipeline = pipeline
        self.metrics = AsyncMetrics()
        self._start_time = time.time()
    
    async def collect_metrics(self) -> AsyncMetrics:
        """Collect current metrics."""
        self.metrics.buffer_size = self.pipeline.get_buffer_size()
        self.metrics.logs_processed = self.pipeline.get_processed_count()
        self.metrics.logs_dropped = self.pipeline.get_dropped_count()
        return self.metrics
    
    async def report_metrics(self, interval: float = 60.0) -> None:
        """Periodically report metrics."""
        while True:
            await asyncio.sleep(interval)
            metrics = await self.collect_metrics()
            
            uptime = time.time() - self._start_time
            rate = metrics.logs_processed / uptime if uptime > 0 else 0
            
            print(f"Async Pipeline Metrics:")
            print(f"  Processed: {metrics.logs_processed} ({rate:.1f}/sec)")
            print(f"  Dropped: {metrics.logs_dropped}")
            print(f"  Buffer Size: {metrics.buffer_size}")
            print(f"  Avg Flush Time: {metrics.average_flush_time:.3f}s")
```

### Configuration Examples

#### High-Throughput Web Server

```python
def create_web_server_pipeline() -> AsyncPipeline:
    """Optimized for web servers with high request volume."""
    
    config = AsyncPipelineConfig(
        min_level=LogLevel.INFO,
        
        # Minimal enrichers for performance
        enrichers=(timestamp_enricher, request_id_enricher),
        
        # Essential filters only
        filters=(level_filter, rate_limit_filter),
        
        # Fast JSON formatter
        formatter=optimized_json_formatter,
        
        # Async writers with batching
        writers=(
            AsyncFileWriter('/var/log/app/access.log', batch_size=200),
            AsyncNetworkWriter('https://logs.example.com/ingest')
        ),
        
        # Aggressive batching for throughput
        buffer_size=2000,
        flush_interval=0.1,  # Flush every 100ms
        backpressure_limit=10000
    )
    
    return AsyncPipeline(config)
```

#### Real-time Analytics

```python
def create_analytics_pipeline() -> AsyncPipeline:
    """Pipeline for real-time analytics with low latency."""
    
    config = AsyncPipelineConfig(
        min_level=LogLevel.DEBUG,
        
        # Rich context for analytics
        enrichers=(
            timestamp_enricher,
            context_enricher,
            session_enricher,
            geo_enricher
        ),
        
        # No filtering - capture everything
        filters=(),
        
        # Structured format for analytics
        formatter=analytics_json_formatter,
        
        # Multiple analytics destinations
        writers=(
            AsyncKafkaWriter('analytics-topic'),
            AsyncElasticsearchWriter('logs-index'),
            AsyncMetricsWriter()  # Extract metrics from logs
        ),
        
        # Low latency settings
        buffer_size=100,
        flush_interval=0.05,  # 50ms flush interval
        backpressure_limit=1000
    )
    
    return AsyncPipeline(config)
```

### Error Handling and Recovery

```python
class AsyncErrorHandler:
    """Handle errors in async pipelines."""
    
    def __init__(self, pipeline: AsyncPipeline):
        self.pipeline = pipeline
        self.error_count = 0
        self.last_error_time = 0
    
    async def handle_writer_error(self, writer: AsyncWriter, error: Exception) -> None:
        """Handle writer errors with retry logic."""
        self.error_count += 1
        self.last_error_time = time.time()
        
        # Log the error
        await self.pipeline.process_internal(LogRecord(
            timestamp=time.time(),
            level=LogLevel.ERROR,
            logger_name='kakashi.async.error',
            message=f"Writer {writer.__class__.__name__} failed: {error}",
            exception_info=sys.exc_info()
        ))
        
        # Implement retry logic or circuit breaker
        if self.error_count > 10:
            # Circuit breaker - temporarily disable writer
            await self._disable_writer_temporarily(writer)
    
    async def _disable_writer_temporarily(self, writer: AsyncWriter, duration: float = 60.0) -> None:
        """Temporarily disable a failing writer."""
        self.pipeline.disable_writer(writer)
        await asyncio.sleep(duration)
        self.pipeline.enable_writer(writer)
        self.error_count = 0  # Reset error count
```

### Best Practices

1. **Buffer Sizing**: Start with 1000-2000 buffer size, adjust based on throughput
2. **Flush Intervals**: Balance latency vs. throughput (0.1-1.0 seconds)
3. **Backpressure**: Always configure backpressure limits to prevent memory issues
4. **Monitoring**: Monitor buffer sizes and flush times in production
5. **Error Handling**: Implement retry logic and circuit breakers for network writers
6. **Graceful Shutdown**: Ensure all buffered logs are flushed on shutdown

```python
async def graceful_shutdown(pipeline: AsyncPipeline) -> None:
    """Gracefully shutdown async pipeline."""
    print("Shutting down async pipeline...")
    
    # Stop accepting new logs
    pipeline.stop_accepting()
    
    # Flush remaining logs
    await pipeline.flush_all()
    
    # Close writers
    await pipeline.close_writers()
    
    print("Async pipeline shutdown complete")
```
