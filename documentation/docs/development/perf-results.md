---
id: perf-results
title: Latest Performance Results
---

Below are the latest **production-ready performance results** from the Kakashi performance validation suite, demonstrating the library's superior performance characteristics.

## 🏆 Performance Summary

- **Throughput**: 56,310+ logs/sec (3.1x faster than standard library)
- **Concurrency Scaling**: 1.17x (adding threads improves performance)
- **Async Performance**: 169,074 logs/sec (9.3x faster than standard library)
- **Memory Efficiency**: <0.02MB memory usage for async operations

## 📊 Benchmark Results

### Throughput Performance

| Test | Total Logs | Execution Time | Throughput | Performance |
|------|------------|----------------|------------|-------------|
| **Kakashi Basic** | 100,000 | 1.78s | **56,310 logs/sec** | **3.1x faster** |
| **Kakashi Concurrent** | 100,000 | 1.51s | **66,116 logs/sec** | **3.6x faster** |
| **Kakashi Async** | 100,000 | 0.59s | **169,074 logs/sec** | **9.3x faster** |
| Standard Library | 100,000 | 5.51s | 18,159 logs/sec | Baseline |

### Concurrency Scaling Analysis

| Threads | Kakashi (logs/sec) | Stdlib (logs/sec) | Scaling Factor |
|---------|-------------------|------------------|----------------|
| 1 | 56,310 | 18,159 | **3.1x** |
| 16 | 66,116 | 10,734 | **6.2x** |
| **Scaling** | **1.17x** | **0.59x** | **Kakashi wins** |

### Memory Usage

| Test | Memory Usage (Δ MB) | Peak Memory (MB) | Efficiency |
|------|----------------------|------------------|------------|
| **Kakashi Basic** | <0.02 | <0.05 | **Excellent** |
| **Kakashi Async** | <0.02 | <0.05 | **Excellent** |
| **Kakashi Concurrent** | <0.02 | <0.05 | **Excellent** |

## 🎯 Key Performance Insights

- **Superior Concurrency**: Kakashi's 1.17x scaling means adding threads improves performance
- **Async Excellence**: 169K logs/sec demonstrates true asynchronous processing
- **Memory Efficiency**: Consistent <0.02MB memory usage across all scenarios
- **Production Ready**: All metrics exceed production performance targets

## ⚖️ Legal Disclaimer

**⚠️ IMPORTANT**: These performance results are provided for informational purposes only. Performance may vary based on system configuration, workload, and other factors. These results are not guarantees of performance and should not be used for commercial claims without independent verification.

## 📋 Test Environment

- **Platform**: Linux (WSL2)
- **Python**: 3.13.5
- **Hardware**: Development system
- **Test Suite**: `performance_tests/validate_performance.py`

**Note**: Results were captured on a development system and may not reflect production performance. Always test in your specific environment.


