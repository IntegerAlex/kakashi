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

---

Thank you for contributing to Kakashi! Your contributions help make it a better logging library for everyone.
