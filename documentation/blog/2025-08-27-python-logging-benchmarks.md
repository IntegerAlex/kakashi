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
| Kakashi Async | **160,618** | **164,940** | 98,856 | 1.875 MB |
| Structlog | 144,459 | 128,622 | 88,687 | 0.000 MB |
| Standard Library | 124,160 | 115,467 | 85,680 | 0.000 MB |
| Kakashi Sync | 97,268 | 51,454 | 68,931 | 0.000 MB |
| Loguru | 81,879 | 93,358 | 63,383 | 0.875 MB |

### Fair diff vs Kakashi Async

Percent difference relative to Kakashi Async (negative = slower):

| Library | Basic vs KA | Concurrent vs KA | Structured vs KA |
|---------|-------------:|-----------------:|-----------------:|
| Structlog | -10.1% | -22.0% | -10.3% |
| Standard Library | -22.6% | -30.0% | -13.3% |
| Kakashi Sync | -39.4% | -68.8% | -30.3% |
| Loguru | -49.0% | -43.4% | -35.9% |

## What This Means

### Kakashi Async is the Winner in These Tests

- Leads basic throughput and concurrent performance
- Maintains high performance (\~165K logs/sec) even with 16 concurrent threads

### Standard Library and Structlog Performed Well

- Structlog and the standard library posted strong basic throughput; standard lib remains a solid zero-deps choice

### Concurrent Performance Varies

- Kakashi Async: Minimal performance drop between basic and concurrent
- Structlog / Standard: Moderate drop
- Kakashi Sync / Loguru: Larger drops under concurrency

### Thread Consistency

Measured by ratio of min/max thread times (higher is more consistent):
- Kakashi Sync: ~0.90
- Structlog: ~0.39
- Kakashi Async: ~0.25
- Standard Library: ~0.27
- Loguru: ~0.18

## Structured Logging Overhead (from this run)

- Kakashi Async: ~+98% overhead
- Kakashi Sync: ~+49% overhead
- Standard Library: ~+27% overhead
- Loguru: ~+19% overhead
- Structlog: ~+66% overhead

## Recommendation (Based on This Test)

- High-throughput services: Kakashi Async
- Simple apps: Standard library
- Heavy structured logging: Consider trade-offs; Loguru showed lower overhead in this run
- Avoid Kakashi Sync for heavily concurrent workloads

## Limitations

- Single machine, single OS and CPU
- Specific message patterns and concurrency
- No network writers (null handlers)

## Conclusion

Kakashi's async logger delivered strong performance in this benchmark, particularly under concurrency. Async logging appears advantageous by decoupling log production from I/O.

If your application logs heavily under load, consider async-first designs. As always, benchmark with your own workloads.

---

Disclaimer: This benchmark reflects specific conditions and one implementation. Your mileage will vary; validate in your environment before making production decisions.
