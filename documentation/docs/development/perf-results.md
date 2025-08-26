---
id: perf-results
title: Latest Performance Results
---

Below are the latest high-intensity performance and memory results captured from the Kakashi performance test suite.

## Summary

- CPUs: 16
- RAM: 7.4GB
- Platform: linux
- Python: 3.13.5

## Throughput and Timing

| Test | Total Logs | Execution Time | Throughput |
|------|------------|----------------|------------|
| basic_logging_performance | 100,000 | 15.536s | 6,437 logs/sec |
| async_logging_performance | 100,000 | 17.316s | 5,775 logs/sec |
| concurrent_logging_performance | 100,000 | 28.888s | 3,462 logs/sec |
| context_switching_performance | 100,000 | 16.696s | 5,989 logs/sec |

## Memory Usage

| Test | Memory Usage (Δ MB) | Peak Memory (MB) |
|------|----------------------|------------------|
| basic_logging_performance | 0.03 | 20.2 |
| async_logging_performance | 0.02 | 20.2 |
| concurrent_logging_performance | 0.08 | 20.4 |
| structured_logging_overhead | 0.02 | 20.4 |
| memory_leak_test | 0.01 | 20.5 |
| context_switching_performance | 0.02 | 20.5 |

## Notes

- Logging output was disabled during tests to avoid I/O skew and large logs.
- Results file: generated at `performance_tests/performance_results.json` (ignored from VCS).


