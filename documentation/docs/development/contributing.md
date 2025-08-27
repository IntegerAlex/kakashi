---
id: contributing
title: Contributing to Kakashi
---

## 🚀 Welcome Contributors!

Thank you for your interest in contributing to Kakashi! This guide will help you understand the codebase, development workflow, and how to make meaningful contributions.

## 🏗️ Understanding the Codebase

### Project Structure

```
kakashi/
├── kakashi/                    # Main package
│   ├── __init__.py            # Public API exports
│   └── core/                  # Core implementation
│       ├── logger.py          # Main Logger and AsyncLogger classes
│       ├── records.py         # LogRecord, LogContext, LogLevel
│       ├── config.py          # Configuration system
│       └── pipeline.py        # Pipeline processing components
├── performance_tests/          # Performance validation suite
│   └── validate_performance.py
├── documentation/              # Docusaurus documentation site
├── tests/                     # Test suite
├── pyproject.toml            # Package configuration
└── README.md                 # Project overview
```

### Core Architecture Overview

Kakashi is built around these key principles:

1. **Performance-First**: Every design decision prioritizes performance
2. **Thread Safety**: Zero contention through thread-local storage
3. **Memory Efficiency**: Minimal allocations and buffer pooling
4. **Clean API**: Simple, intuitive interface for developers

## 🔧 Development Setup

### Prerequisites

- Python 3.7+
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/IntegerAlex/kakashi.git
   cd kakashi
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e .[dev]
   ```

## 🧪 Testing Strategy

### Test Categories

#### Unit Tests

Test individual components in isolation:

```python
import pytest
from kakashi.core.logger import Logger

class TestLogger:
    def test_logger_creation(self):
        """Test basic logger creation."""
        logger = Logger("test.logger")
        assert logger.name == "test.logger"
        assert logger._min_level == 20  # INFO level
    
    def test_level_filtering(self):
        """Test level filtering works correctly."""
        logger = Logger("test", min_level=30)  # WARNING and above
        
        # DEBUG should be filtered out
        logger._log(10, "debug message")  # No output expected
        
        # WARNING should pass through
        logger._log(30, "warning message")  # Should be processed
```

#### Performance Tests

Test performance characteristics:

```python
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.performance
class TestLoggerPerformance:
    def test_single_thread_throughput(self):
        """Test single-thread logging throughput."""
        logger = Logger("perf_test")
        
        # Warm up
        for _ in range(1000):
            logger._log(20, "warm up message")
        
        # Benchmark
        start_time = time.time()
        num_logs = 100000
        
        for i in range(num_logs):
            logger._log(20, f"benchmark message {i}")
        
        elapsed = time.time() - start_time
        throughput = num_logs / elapsed
        
        # Assert minimum throughput
        assert throughput > 50000, f"Throughput {throughput:.0f} logs/sec too low"
```

## 🚀 Contributing Workflow

### Before Starting

1. **Open an issue** to discuss the feature or bug fix
2. **Check existing code** for similar functionality
3. **Review architecture** to understand design patterns
4. **Write tests first** (TDD approach recommended)

### Feature Development Process

1. **Create feature branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Write failing tests** for the new functionality
3. **Implement the feature** following existing patterns
4. **Make tests pass** with minimal code changes
5. **Refactor and optimize** while keeping tests green
6. **Add documentation** and examples
7. **Submit pull request** with clear description

## 📝 Code Style & Standards

### Python Style Guide

- **PEP 8** compliance enforced by `black` and `flake8`
- **Type hints** required for all public APIs
- **Docstrings** required for all public functions and classes
- **Line length**: 88 characters (black default)

### Code Formatting

```python
def create_high_performance_logger(
    name: str, 
    min_level: int = 20, 
    batch_size: int = 100
) -> Logger:
    """Create a high-performance logger instance.
    
    Args:
        name: Logger name (typically __name__)
        min_level: Minimum log level (default: INFO)
        batch_size: Batch size for I/O optimization
        
    Returns:
        Configured Logger instance
    """
    return Logger(name, min_level, batch_size)
```

## 🔍 Debugging & Profiling

### Performance Profiling

```python
import cProfile
import pstats
from kakashi.core.logger import Logger

def profile_logging_performance():
    """Profile logging performance."""
    logger = Logger("profile_test")
    
    # Profile logging operations
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Perform logging operations
    for i in range(10000):
        logger._log(20, f"test message {i}")
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
```

### Memory Profiling

```python
import tracemalloc
import gc
from kakashi.core.logger import Logger

def profile_memory_usage():
    """Profile memory usage during logging."""
    tracemalloc.start()
    
    logger = Logger("memory_test")
    
    # Take snapshot before logging
    snapshot1 = tracemalloc.take_snapshot()
    
    # Perform logging operations
    for i in range(1000):
        logger._log(20, f"memory test message {i}")
    
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

## 🎯 Common Contribution Areas

### Performance Improvements

1. **Hot Path Optimization**
   - Reduce CPU cycles in critical paths
   - Optimize memory allocations
   - Improve cache locality

2. **Concurrency Enhancements**
   - Better thread scaling
   - Lock-free algorithms
   - Improved batch processing

3. **Memory Optimization**
   - Buffer pooling strategies
   - Object reuse patterns
   - Garbage collection optimization

### Feature Additions

1. **New Output Formats**
   - JSON formatters
   - Custom serialization
   - Template-based formatting

2. **Additional Sinks**
   - Network logging
   - Database logging
   - Cloud service integration

## 📋 Pull Request Guidelines

### PR Checklist

- [ ] **Tests pass**: All existing tests continue to pass
- [ ] **New tests**: New functionality has comprehensive tests
- [ ] **Documentation**: Public APIs are documented
- [ ] **Type hints**: All new code has proper type annotations
- [ ] **Performance**: No significant performance regressions
- [ ] **Backwards compatibility**: Changes don't break existing APIs

### PR Description Template

```markdown
## Summary
Brief description of the changes.

## Changes
- List of specific changes made
- Include any breaking changes

## Testing
- Description of tests added
- Performance impact (if any)

## Documentation
- Link to updated documentation
- Examples of new functionality

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Performance tested
```

## 🚀 Release Process

### Version Numbering

Kakashi follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

### Release Checklist

1. **Update version** in `pyproject.toml` and `__init__.py`
2. **Update CHANGELOG.md** with release notes
3. **Run full test suite** including performance tests
4. **Build and test package**: `python -m build && pip install dist/*.whl`
5. **Create release tag**: `git tag v0.2.0`
6. **Push to PyPI**: `twine upload dist/*`
7. **Create GitHub release** with release notes

## 🤝 Community

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Email**: Direct contact for security issues

### Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct. Please be respectful and inclusive in all interactions.

## 🔧 Development Tools & Workflow

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Code Quality Tools

```bash
# Format code with black
black kakashi/ tests/

# Check code style with flake8
flake8 kakashi/ tests/

# Run type checking with mypy
mypy kakashi/

# Run security checks with bandit
bandit -r kakashi/
```

### Continuous Integration

Our CI pipeline runs on every PR and includes:

- **Unit Tests**: pytest with coverage reporting
- **Performance Tests**: Automated performance regression detection
- **Code Quality**: black, flake8, mypy, bandit
- **Documentation**: Build and validate docs
- **Package Build**: Test package installation

## 📊 Performance Testing Guidelines

### Benchmarking Standards

When contributing performance improvements:

1. **Baseline Measurement**: Always measure current performance first
2. **Statistical Significance**: Run benchmarks multiple times (min 5 runs)
3. **Environment Consistency**: Use same hardware/OS for comparisons
4. **Memory Profiling**: Include memory usage in performance analysis

### Performance Test Examples

```python
import pytest
import time
import statistics
from kakashi.core.logger import Logger

class TestLoggerPerformance:
    def test_logging_throughput_benchmark(self):
        """Benchmark logging throughput with statistical analysis."""
        logger = Logger("throughput_test")
        num_logs = 100000
        run_times = []
        
        # Multiple benchmark runs
        for run in range(5):
            start_time = time.perf_counter()
            
            for i in range(num_logs):
                logger._log(20, f"benchmark message {i}")
            
            end_time = time.perf_counter()
            run_times.append(end_time - start_time)
        
        # Calculate statistics
        mean_time = statistics.mean(run_times)
        std_dev = statistics.stdev(run_times)
        throughput = num_logs / mean_time
        
        # Performance assertions
        assert throughput > 50000, f"Throughput {throughput:.0f} logs/sec below threshold"
        assert std_dev / mean_time < 0.1, "Performance too variable"
        
        print(f"Throughput: {throughput:.0f} logs/sec")
        print(f"Mean time: {mean_time:.4f}s ± {std_dev:.4f}s")
```

## 🐛 Debugging Common Issues

### Common Development Problems

#### 1. Import Errors

```bash
# If you get import errors, ensure you're in the right environment
source venv/bin/activate
pip install -e .

# Check PYTHONPATH
echo $PYTHONPATH
```

#### 2. Test Failures

```bash
# Run specific test with verbose output
pytest tests/test_logger.py::TestLogger::test_logger_creation -v -s

# Run with coverage
pytest --cov=kakashi tests/

# Debug specific test
pytest tests/test_logger.py::TestLogger::test_logger_creation --pdb
```

#### 3. Performance Regressions

```bash
# Run performance tests only
pytest -m performance

# Compare with previous results
python performance_tests/validate_performance.py --compare-baseline
```

### Debugging Tips

1. **Use logging**: Add debug logs to understand execution flow
2. **Profile locally**: Use cProfile and memory_profiler for performance issues
3. **Check dependencies**: Ensure all dependencies are correctly installed
4. **Verify environment**: Check Python version and virtual environment

## 📚 Documentation Standards

### Docstring Format

Follow Google-style docstrings:

```python
def process_log_record(record: LogRecord, context: LogContext) -> str:
    """Process a log record with context information.
    
    Args:
        record: The log record to process
        context: Additional context information
        
    Returns:
        Formatted log message string
        
    Raises:
        ValueError: If record is invalid
        TypeError: If context is wrong type
        
    Example:
        >>> record = LogRecord(level=20, message="test")
        >>> context = LogContext(user_id="123")
        >>> process_log_record(record, context)
        'test [user_id=123]'
    """
    if not record:
        raise ValueError("Record cannot be None")
    
    # Implementation here
    return formatted_message
```

### API Documentation

- **Public APIs**: Must have comprehensive docstrings
- **Examples**: Include usage examples for complex functions
- **Type hints**: All parameters and return values must be typed
- **Error handling**: Document all possible exceptions

## 🚀 Advanced Development Topics

### Memory Management

Understanding Kakashi's memory model:

```python
class MemoryOptimizedLogger:
    """Example of memory optimization patterns used in Kakashi."""
    
    def __init__(self):
        # Object pooling for frequently allocated objects
        self._buffer_pool = []
        self._max_pool_size = 100
    
    def _get_buffer(self):
        """Get buffer from pool or create new one."""
        if self._buffer_pool:
            return self._buffer_pool.pop()
        return bytearray(1024)
    
    def _return_buffer(self, buffer):
        """Return buffer to pool for reuse."""
        if len(self._buffer_pool) < self._max_pool_size:
            buffer.clear()  # Reset buffer
            self._buffer_pool.append(buffer)
```

### Thread Safety Patterns

```python
import threading
from contextlib import contextmanager

class ThreadSafeComponent:
    """Example of thread safety patterns in Kakashi."""
    
    def __init__(self):
        self._local = threading.local()
        self._lock = threading.RLock()
    
    @contextmanager
    def _thread_context(self):
        """Manage thread-local context safely."""
        if not hasattr(self._local, 'context'):
            with self._lock:
                if not hasattr(self._local, 'context'):
                    self._local.context = {}
        yield self._local.context
```

## 🔒 Security Considerations

### Input Validation

```python
import re
from typing import Optional

def validate_log_message(message: str) -> Optional[str]:
    """Validate and sanitize log message input.
    
    Args:
        message: Raw log message
        
    Returns:
        Sanitized message or None if invalid
    """
    if not isinstance(message, str):
        return None
    
    # Remove potential injection patterns
    sanitized = re.sub(r'[<>"\']', '', message)
    
    # Limit message length
    if len(sanitized) > 10000:
        return None
    
    return sanitized
```

### Secure Configuration

```python
import os
from pathlib import Path

def load_secure_config(config_path: str) -> dict:
    """Load configuration with security checks."""
    path = Path(config_path)
    
    # Security checks
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Prevent path traversal
    if '..' in str(path.resolve()):
        raise ValueError("Invalid config path")
    
    # Check file permissions
    if path.stat().st_mode & 0o777 != 0o600:
        raise PermissionError("Config file has insecure permissions")
    
    # Load and validate config
    # Implementation here
    return config
```

## 📈 Monitoring & Observability

### Health Checks

```python
class LoggerHealthCheck:
    """Monitor logger health and performance."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.metrics = {}
    
    def check_health(self) -> dict:
        """Perform comprehensive health check."""
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'metrics': self._collect_metrics(),
            'issues': self._identify_issues()
        }
        
        if health_status['issues']:
            health_status['status'] = 'degraded'
        
        return health_status
    
    def _collect_metrics(self) -> dict:
        """Collect performance and health metrics."""
        return {
            'message_count': getattr(self.logger, '_message_count', 0),
            'error_count': getattr(self.logger, '_error_count', 0),
            'last_message_time': getattr(self.logger, '_last_message_time', 0)
        }
```

## 🎯 Contribution Ideas

### Good First Issues

- **Documentation**: Improve docstrings and examples
- **Test Coverage**: Add tests for edge cases
- **Error Handling**: Improve error messages and handling
- **Performance**: Optimize specific code paths

### Advanced Contributions

- **New Sinks**: Implement additional output destinations
- **Formatters**: Create new log message formats
- **Filters**: Add sophisticated log filtering
- **Metrics**: Implement logging metrics and monitoring

### Research Areas

- **Async Performance**: Investigate async/await optimizations
- **Memory Profiling**: Deep dive into memory usage patterns
- **Concurrency Models**: Explore alternative threading approaches
- **Compression**: Research log compression techniques

## 📞 Getting in Touch

### Communication Channels

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Email**: For security issues (see SECURITY.md)
- **Discord**: Community chat (if available)

### Response Times

- **Bug Reports**: Within 24 hours
- **Feature Requests**: Within 48 hours
- **Security Issues**: Within 12 hours
- **General Questions**: Within 72 hours

---

## 🙏 Acknowledgments

Thank you for contributing to Kakashi! Your contributions help make it a better logging library for everyone. Whether you're fixing a typo, adding a feature, or reporting a bug, every contribution matters.

**Remember**: Quality over quantity. Take your time to understand the codebase and write good, maintainable code. We're here to help you succeed!

---

*Last updated: 2025-08-27*
*Contributors: [IntegerAlex]*
