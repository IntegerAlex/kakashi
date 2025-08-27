---
id: performance
title: Performance Guide
---

## Performance Characteristics

Kakashi is designed for **production-grade high-performance logging** with minimal overhead and superior concurrency scaling. Understanding its performance characteristics helps optimize your application.

### 🏆 Current Performance Benchmarks

#### Throughput Benchmarks

| Configuration | Throughput (logs/sec) | Concurrency Scaling | Memory Usage | Notes |
|--------------|----------------------|-------------------|--------------|-------|
| **Kakashi Basic** | **56,310** | N/A | &lt;0.02MB | **3.1x faster than stdlib** |
| **Kakashi Concurrent** | **66,116** | **1.17x** | &lt;0.02MB | **Adding threads improves performance** |
| **Kakashi Async** | **169,074** | N/A | &lt;0.02MB | **9.3x faster than stdlib** |
| Standard Library | 18,159 | 0.59x | &lt;0.01MB | Python built-in |
| Structlog | 12,181 | 0.47x | &lt;0.01MB | Production ready |
| Loguru | 14,690 | 0.46x | &lt;0.01MB | Feature rich |

#### Memory Usage

| Component | Memory per log | Notes |
|-----------|---------------|-------|
| LogRecord | 150-300 bytes | Optimized for minimal allocation |
| Thread-local buffer | 1-2KB | Efficient batch processing |
| Async queue | &lt;0.02MB | Background worker optimization |
| Total overhead | &lt;0.05MB | Production-ready memory footprint |

### Hot Path Optimization

The logging hot path is optimized for **maximum performance** with minimal CPU cycles:

```python
def _log(self, level: int, message: str, fields: Optional[Dict[str, Any]] = None) -> None:
    # 1. Fast level check (1-2 CPU cycles) - pre-computed threshold
    if level < self._min_level:
        return
    
    # 2. Format message with minimal allocations
    formatted = self._formatter.format_message(level, self.name, message, fields)
    
    # 3. Thread-local batch accumulation (no locks)
    self._thread_local.batch.append(formatted)
    
    # 4. Batch flush when threshold reached (efficient I/O)
    if len(self._thread_local.batch) >= self._batch_size:
        self._flush_batch(self._thread_local.batch)
        self._thread_local.batch.clear()
```

#### Key Performance Features

- **Pre-computed level thresholds**: Eliminates runtime level calculations
- **Thread-local buffering**: Zero contention between threads
- **Batch processing**: Reduces I/O operations by 10-100x
- **Direct sys.stderr.write**: Bypasses Python's buffering overhead

### Performance Best Practices

#### 1. Level Filtering

Always use appropriate log levels to minimize processing:

```python
# Good: Level check happens first
logger.debug("Expensive operation: %s", expensive_computation())

# Better: Explicit level check
if logger.isEnabledFor(LogLevel.DEBUG):
    logger.debug("Expensive operation: %s", expensive_computation())

# Best: Use structured logging with lazy evaluation
logger.debug("Expensive operation", result=lambda: expensive_computation())
```

#### 2. Structured Field Optimization

Use efficient field types and avoid deep nesting:

```python
# Good: Simple types
logger.info("User action", user_id=123, action="login")

# Avoid: Complex objects that require serialization
logger.info("User action", user=complex_user_object)

# Better: Extract relevant fields
logger.info("User action", 
           user_id=user.id,
           user_type=user.type,
           action="login")
```

#### 3. Context Management

Minimize context switching overhead:

```python
# Good: Set context once per request
set_request_context("192.168.1.1", "GET /api/users")
logger.info("Processing request")
logger.info("Database query completed")
clear_request_context()

# Avoid: Setting context for each log
logger.info("Processing request", ip="192.168.1.1")
logger.info("Database query", ip="192.168.1.1")
```

#### 4. Async Logging for High Throughput

Use async logging for I/O-bound applications:

```python
# High-throughput configuration
kakashi.setup("production", 
              async_logging=True,
              buffer_size=2000,
              flush_interval=0.1)
```

### Memory Optimization

#### Immutable Data Structures

Kakashi uses immutable data structures that enable memory sharing:

```python
# Multiple records can share the same context
base_context = LogContext(service_name="api", version="1.0.0")

# These records share the base context in memory
record1 = LogRecord(..., context=base_context.with_custom(user_id="123"))
record2 = LogRecord(..., context=base_context.with_custom(user_id="456"))
```

### Profiling and Monitoring

#### Built-in Performance Monitoring

```python
from kakashi.core.async_interface import get_async_stats

# Monitor async pipeline performance
stats = get_async_stats()
print(f"Queue size: {stats['queue_size']}")
print(f"Messages processed: {stats['messages_enqueued']}")
print(f"Throughput: {stats['messages_enqueued'] / elapsed_time:.0f} msg/sec")
```

#### Custom Profiling

```python
import cProfile
import pstats

def profile_logging_performance():
    """Profile logging performance."""
    
    # Set up logging
    logger = get_structured_logger(__name__)
    
    # Profile logging operations
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Perform logging operations
    for i in range(10000):
        logger.info("Test message", iteration=i, data="sample")
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
```

### Performance Testing

#### Throughput Testing

```python
import time
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_throughput():
    """Test logging throughput under concurrent load."""
    
    logger = get_structured_logger("performance_test")
    num_threads = 10
    logs_per_thread = 1000
    
    def log_worker(thread_id: int) -> float:
        start_time = time.time()
        for i in range(logs_per_thread):
            logger.info("Test message", thread_id=thread_id, iteration=i)
        return time.time() - start_time
    
    # Run concurrent logging
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        times = list(executor.map(log_worker, range(num_threads)))
    total_time = time.time() - start_time
    
    total_logs = num_threads * logs_per_thread
    throughput = total_logs / total_time
    
    print(f"Concurrent throughput: {throughput:.0f} logs/sec")
    print(f"Average thread time: {sum(times) / len(times):.3f}s")
```

#### Memory Usage Testing

```python
import tracemalloc
import gc

def test_memory_usage():
    """Test memory usage during logging."""
    
    # Start memory tracing
    tracemalloc.start()
    
    logger = get_structured_logger("memory_test")
    
    # Take snapshot before logging
    snapshot1 = tracemalloc.take_snapshot()
    
    # Perform logging operations
    for i in range(1000):
        logger.info("Test message", iteration=i, data="x" * 100)
    
    # Force garbage collection
    gc.collect()
    
    # Take snapshot after logging
    snapshot2 = tracemalloc.take_snapshot()
    
    # Analyze memory usage
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    
    print("Top memory allocations:")
    for stat in top_stats[:10]:
        print(stat)
```

### Production Optimization

#### Configuration for Different Environments

```python
def get_optimized_config(environment: str) -> dict:
    """Get optimized configuration for environment."""
    
    if environment == "development":
        return {
            "level": LogLevel.DEBUG,
            "structured": True,
            "async_logging": False,
            "console_output": True,
            "file_output": True,
        }
    
    elif environment == "production":
        return {
            "level": LogLevel.INFO,
            "structured": True,
            "async_logging": True,
            "console_output": False,
            "file_output": True,
            "buffer_size": 2000,
            "flush_interval": 0.1,
        }
    
    elif environment == "high_throughput":
        return {
            "level": LogLevel.WARNING,
            "structured": True,
            "async_logging": True,
            "console_output": False,
            "file_output": True,
            "buffer_size": 5000,
            "flush_interval": 0.05,
        }
```

#### Monitoring Production Performance

```python
import psutil
import time

class ProductionMonitor:
    """Monitor logging performance in production."""
    
    def __init__(self):
        self.start_time = time.time()
        self.log_count = 0
        self.error_count = 0
    
    def record_log(self) -> None:
        self.log_count += 1
    
    def record_error(self) -> None:
        self.error_count += 1
    
    def get_metrics(self) -> dict:
        uptime = time.time() - self.start_time
        process = psutil.Process()
        
        return {
            "uptime": uptime,
            "logs_processed": self.log_count,
            "logs_per_second": self.log_count / uptime if uptime > 0 else 0,
            "error_rate": self.error_count / self.log_count if self.log_count > 0 else 0,
            "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
        }
```

### Performance Troubleshooting

#### Common Performance Issues

1. **High CPU Usage**
   - Check for expensive enrichers or formatters
   - Verify log level filtering is working
   - Profile to identify bottlenecks

2. **High Memory Usage**
   - Check async buffer sizes
   - Look for memory leaks in custom components
   - Monitor object creation patterns

3. **I/O Bottlenecks**
   - Use async I/O for high throughput
   - Implement batched writes
   - Check disk performance

4. **Thread Contention**
   - Use immutable data structures
   - Avoid shared mutable state
   - Consider lock-free algorithms

#### Debugging Performance Issues

```python
def debug_performance_issue():
    """Debug logging performance issues."""
    
    # Enable detailed timing
    import cProfile
    import io
    import pstats
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run problematic code
    logger = get_structured_logger("debug")
    for i in range(1000):
        logger.info("Test message", data={"key": "value", "index": i})
    
    profiler.disable()
    
    # Analyze results
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats()
    
    print(stream.getvalue())
```

---

*Last updated: 2025-08-27*
*Contributors: [IntegerAlex]*
