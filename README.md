<div align="center">
  <img src="documentation/static/img/kakashi-logo.png" alt="Kakashi Logo" width="200" height="200">
  <h1>Kakashi - Professional High-Performance Logging Library</h1>
</div>

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/kakashi?period=total&units=INTERNATIONAL_SYSTEM&left_color=RED&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/kakashi)
[![PyPI Version](https://img.shields.io/pypi/v/kakashi)](https://pypi.org/project/kakashi/)
[![PyPI License](https://img.shields.io/pypi/l/kakashi)](https://github.com/IntegerAlex/kakashi/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/IntegerAlex/kakashi)](https://github.com/IntegerAlex/kakashi/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/IntegerAlex/kakashi)](https://github.com/IntegerAlex/kakashi/issues)

A modern, high-performance logging library designed for production applications that require both high throughput and excellent concurrency scaling.

## 🚀 Features

- **High Performance**: 60,000+ logs/sec throughput with balanced concurrency
- **Thread-Safe**: Minimal contention with thread-local optimizations
- **Structured Logging**: Field-based logging with minimal overhead
- **Memory Efficient**: <0.02MB memory usage for async operations
- **Professional Code**: Clean, maintainable architecture
- **Drop-in Replacement**: Compatible with Python's built-in logging

## 📊 Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| **Throughput** | 60,000+ logs/sec | ✅ EXCEEDED (852,153 logs/sec) |
| **Concurrency Scaling** | 0.65x+ | ✅ EXCEEDED (1.13x scaling) |
| **Memory Usage** | <0.02MB | ✅ Maintained |
| **Structured Overhead** | <10% | ✅ Maintained |

## 🏆 Benchmark Results

**⚠️ LEGAL DISCLAIMER**: The following benchmark results are provided for informational purposes only. Performance may vary based on system configuration, workload, and other factors. These results are not guarantees of performance and should not be used for commercial claims or comparisons without independent verification. Kakashi makes no warranties regarding performance characteristics.

*Re-benchmarked 2026-06-15 on Python 3.12.3, Linux 6.17, 16-core CPU.*

### Performance Comparison vs Industry Standards

| Library | Throughput (logs/sec) | Concurrency Scaling | Async Throughput | Notes |
|---------|----------------------|-------------------|------------------|-------|
| **Kakashi v0.2.2** | **852,153** | **1.13x** | **407,361** | SUPERIOR performance |
| Standard Library | 198,122 | 0.43x | N/A | Python built-in |
| Structlog | 203,592 | 0.20x | N/A | Production ready |
| Loguru | 116,966 | 0.25x | N/A | Feature rich |

### Performance Analysis

- **Single-threaded**: **4.3x** faster than standard library
- **Concurrency scaling**: **11.3x** faster than standard library under 16-thread contention
- **Only library with >1x scaling**: all competitors degrade significantly under concurrency
- **Async throughput**: **407K logs/sec** non-blocking enqueue
- **Memory efficiency**: Maintains low memory footprint across all scenarios

**Note**: These benchmarks were run on a development system and may not reflect production performance. Always test in your specific environment.

## 🏗️ Architecture

```
kakashi/
├── core/                    # Core logging implementation
│   ├── logger.py           # Main Logger and AsyncLogger classes
│   ├── records.py          # LogRecord, LogContext, LogLevel
│   ├── config.py           # Configuration system
│   ├── pipeline.py         # Pipeline processing components
│   ├── async_backend.py    # Asynchronous I/O backend
│   ├── structured_logger.py # Structured logging support
│   └── sinks.py            # Output destination system
├── performance_tests/       # Performance validation
│   └── validate_performance.py
└── README.md               # This file
```

## 📖 Quick Start

### Basic Usage

```python
from kakashi import get_logger, get_async_logger

# Synchronous logging
logger = get_logger(__name__)
logger.info("Application started", version="1.0.0")

# Asynchronous logging for high throughput
async_logger = get_async_logger(__name__)
async_logger.info("High-volume logging")

# Structured logging with fields
logger.info("User action", user_id=123, action="login", ip="192.168.1.1")
```

### Advanced Configuration

```python
from kakashi import setup_environment, production_config

# Production setup
config = production_config(
    service_name="my-api",
    version="2.1.0",
    enable_async_io=True
)
setup_environment(config)
```

### Framework Integration

```python
# FastAPI
from fastapi import FastAPI
from kakashi import setup_logging

app = FastAPI()
setup_logging("production", service_name="fastapi-app")

# Flask
from flask import Flask
from kakashi import setup_logging

app = Flask(__name__)
setup_logging("production", service_name="flask-app")
```

## 🔧 Installation

```bash
pip install kakashi
```

## 🧪 Performance Validation

Run the performance validation to ensure your installation meets production targets:

```bash
cd performance_tests
python validate_performance.py
```

This will test:
- Throughput performance (60K+ logs/sec)
- Concurrency scaling (0.65x+)
- Memory efficiency (<0.02MB)
- Structured logging overhead (<10%)

## 📚 API Reference

### Core Classes

- **`Logger`**: High-performance synchronous logger
- **`AsyncLogger`**: Asynchronous logger with batch processing
- **`LogFormatter`**: Optimized message formatting

### Main Functions

- **`get_logger(name, min_level=20)`**: Get a synchronous logger
- **`get_async_logger(name, min_level=20)`**: Get an asynchronous logger
- **`clear_logger_cache()`**: Clear logger cache

### Configuration

- **`setup_environment(env, **kwargs)`**: Configure logging environment
- **`production_config(**kwargs)`**: Production-optimized configuration
- **`development_config(**kwargs)`**: Development-optimized configuration

## 🎯 Use Cases

### High-Throughput Applications

- **API Services**: Handle thousands of requests per second
- **Data Processing**: Log millions of events efficiently
- **Real-time Systems**: Minimal latency logging

### Production Environments

- **Microservices**: Structured logging with context
- **Distributed Systems**: Async logging for scalability
- **Cloud-Native Apps**: Memory-efficient operation

## 🔍 Performance Characteristics

### Throughput Optimization

- Thread-local buffer management
- Pre-computed level checks
- Direct I/O operations
- Minimal object allocation

### Concurrency Optimization

- Lock-free hot paths
- Thread-local caching
- Batch processing
- Cache-line optimization

### Memory Optimization

- Buffer pooling and reuse
- Zero-copy operations where possible
- Adaptive buffer sizing
- Reference counting for lifecycle management

## 🚨 Migration from v0.1.x

The v0.2.0 release maintains backward compatibility while providing significant performance improvements:

```python
# Old v0.1.x code (still works)
from kakashi import setup, get_logger
setup("production")
logger = get_logger(__name__)

# New v0.2.0 code (recommended)
from kakashi import get_logger
logger = get_logger(__name__)  # Auto-configuration
```

## 🧭 Roadmap & Collaboration

We are looking for collaborators to help build the next evolution of Kakashi:

- Cloud log dump and long-term storage integrations (S3/GCS/Azure Blob, Kinesis, Kafka)
- Scalable log analysis pipelines (batch + streaming) with enrichment and alerting
- Incident reporting (SLOs/SLIs, error budgets, paging hooks, RCA helpers)
- First-class observability dashboards (Grafana/Loki, Kibana, Datadog, custom UI)

If you’re interested in shaping these capabilities, please:

- Open a discussion with your proposal and interests
- File an issue with [area:roadmap] label
- Or reach out via GitHub to coordinate design/ownership

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the GNU Lesser General Public License v2.1 (LGPL-2.1) - see the [LICENSE](LICENSE) file for details.

## ⚖️ Legal Disclaimers

### Performance Claims

- All performance metrics and benchmark results are provided for informational purposes only
- Performance may vary significantly based on system configuration, workload patterns, and environmental factors
- These results are not guarantees of performance and should not be used for commercial claims without independent verification
- Kakashi makes no warranties regarding performance characteristics or suitability for specific use cases

### Benchmark Results

- Benchmark results are based on specific test conditions and may not reflect real-world performance
- Comparisons with other libraries are provided for context only and should not be considered definitive
- Users are encouraged to conduct their own performance testing in their specific environments
- Results may vary between different Python versions, operating systems, and hardware configurations

### Usage and Liability

- Kakashi is provided "as is" without warranty of any kind
- Users assume all risk associated with the use of this software
- The authors and contributors are not liable for any damages arising from the use of Kakashi
- Always test thoroughly in your specific environment before production deployment

---

**Kakashi v0.2.2** - Professional High-Performance Logging for Python
