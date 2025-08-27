---
slug: python-logging-benchmarks
title: Testing Python Logging Libraries — A Performance Comparison
authors: [akshat]
tags: [python, logging, benchmarks]
date: 2024-12-15
---

> Legal note: These results reflect one environment and workload. Performance varies by system, patterns, and configuration. Always benchmark with your workloads before production decisions.

I recently needed to choose a logging library for a new Python project and decided to run some benchmarks to see which one performs best. I tested four popular libraries: Python's standard logging, Loguru, Structlog, and Kakashi. The results were pretty surprising.

## Why I Ran This Test

My project needs to handle a lot of log messages — around 50,000+ per second during peak times — with good performance under concurrent load. Rather than just picking a library based on popularity, I wanted actual performance data.

## The Test Setup

I wrote a simple benchmark script that tests three scenarios:

### 1. Basic Throughput Test
- Logs 100,000 messages as fast as possible
- Uses realistic message templates like "User user_1234 completed action login in 45.67ms"
- Measures logs per second and memory usage

### 2. Concurrent Performance Test
- Runs 16 threads simultaneously
- Each thread logs 10,000 messages (160,000 total)
- Tests how well libraries handle multiple threads writing logs at the same time
- Measures scaling efficiency and thread consistency

### 3. Structured Logging Overhead Test
- Compares simple string messages vs structured data with fields
- Tests the performance cost of adding structured data like user_id, request_id, etc.
- Measures the overhead percentage

Environment: 16-core CPU, 64GB RAM, Python 3.11.

## The Results

Logs per second:

| Library | Basic Throughput | Concurrent | Structured | Memory Impact |
|---------|------------------|------------|------------|---------------|
| Kakashi Async | **174,706** | **164,411** | 105,659 | 1.75 MB |
| Standard Library | 128,842 | 108,602 | 86,791 | 0.125 MB |
| Kakashi Sync | 100,927 | 48,203 | 66,743 | 0.0 MB |
| Loguru | 87,406 | 66,782 | 68,855 | 0.0 MB |
| Structlog | Failed | Failed | Failed | - |

Note: Structlog failed due to a configuration issue in this test setup.

## What This Means

### Kakashi Async is the Winner in These Tests

- ~35% faster than standard library in basic throughput
- ~51% faster than standard library under concurrent load
- Maintained high performance (164K vs 174K logs/sec) even with 16 concurrent threads

### Standard Library Held Its Own

Python's built-in logging performed well, coming in second. It's a solid choice if you prefer zero external dependencies.

### Concurrent Performance Varies

- Kakashi Async: Minimal performance drop (174K → 164K)
- Standard Library: Moderate drop (128K → 108K)
- Kakashi Sync: Significant drop (100K → 48K)
- Loguru: Notable drop (87K → 66K)

### Thread Consistency

Measured by ratio of min/max thread times (higher is more consistent):
- Kakashi Sync: ~0.85 (most consistent)
- Standard Library: ~0.42
- Kakashi Async: ~0.23
- Loguru: ~0.17

## Why Kakashi Async Performed Best Here

1. Async queue design that avoids blocking the calling thread
2. Less contention with multiple concurrent threads
3. Efficient message processing for both simple and structured logs

Trade-off: slightly higher memory usage (~1.75MB), which is acceptable for most services.

## Structured Logging Overhead

All libraries showed overhead with structured data:
- Standard Library: ~+50% overhead
- Kakashi Async: ~+89% overhead
- Kakashi Sync: ~+41% overhead
- Loguru: ~+21% overhead (lowest overhead here)

## Recommendation (Based on This Test)

- High-throughput services: Kakashi Async
- Simple apps: Standard library
- Heavy structured logging: Consider Loguru
- Avoid Kakashi Sync for heavily concurrent workloads

## Limitations

- Single machine, single OS and CPU
- Specific message patterns and concurrency
- No network writers (null handlers)
- Structlog omitted due to config issue

## Conclusion

Kakashi's async logger delivered strong performance in this benchmark, particularly under concurrency. Async logging appears advantageous by decoupling log production from I/O.

If your application logs heavily under load, consider async-first designs. As always, benchmark with your own workloads.

---

Disclaimer: This benchmark reflects specific conditions and one implementation. Your mileage will vary; validate in your environment before making production decisions.
