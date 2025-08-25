---
id: contributing
title: Contributing
---

## Development Setup

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

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

### Project Structure

```
kakashi/
├── kakashi/                 # Main package
│   ├── __init__.py         # Public API exports
│   ├── api.py              # Top-level API functions
│   ├── fallback.py         # Fallback loggers for error cases
│   ├── core/               # Core functional components
│   │   ├── pipeline.py     # Functional pipeline architecture
│   │   ├── records.py      # Immutable data structures
│   │   ├── config.py       # Immutable configuration
│   │   ├── interface.py    # Logger factory functions
│   │   ├── async_*.py      # Async backend components
│   │   └── structured_*.py # Structured logging components
│   ├── integrations/       # Web framework integrations
│   │   ├── fastapi_integration.py
│   │   ├── flask_integration.py
│   │   └── django_integration.py
│   └── examples/           # Usage examples and demos
├── tests/                  # Test suite
├── documentation/          # Docusaurus documentation site
├── pyproject.toml         # Package configuration
├── setup.py               # Setuptools configuration
└── README.md              # Project overview
```

## Code Style

### Python Style Guide

- **PEP 8** compliance enforced by `black` and `flake8`
- **Type hints** required for all public APIs
- **Docstrings** required for all public functions and classes
- **Line length**: 88 characters (black default)

### Code Formatting

```bash
# Format code
black kakashi/ tests/

# Check formatting
black --check kakashi/ tests/

# Lint code
flake8 kakashi/ tests/

# Type checking
mypy kakashi/
```

### Documentation Style

- **Google-style docstrings** for functions and classes
- **Type annotations** in docstrings when helpful
- **Examples** in docstrings for complex functions

```python
def create_pipeline(config: PipelineConfig) -> Pipeline:
    """Create a logging pipeline from configuration.
    
    Args:
        config: Immutable pipeline configuration containing enrichers,
            filters, formatters, and writers.
    
    Returns:
        A configured Pipeline instance ready for processing log records.
    
    Example:
        >>> config = PipelineConfig(
        ...     min_level=LogLevel.INFO,
        ...     formatter=json_formatter,
        ...     writers=(console_writer,)
        ... )
        >>> pipeline = create_pipeline(config)
        >>> pipeline.process(log_record)
    """
```

## Testing

### Test Structure

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows
- **Performance tests**: Benchmark critical paths

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kakashi --cov-report=html

# Run specific test file
pytest tests/test_pipeline.py

# Run tests matching pattern
pytest -k "test_async"

# Run performance tests
pytest -m "performance"
```

### Test Categories

```python
import pytest

@pytest.mark.unit
def test_log_record_creation():
    """Unit test for LogRecord creation."""
    pass

@pytest.mark.integration
def test_pipeline_integration():
    """Integration test for pipeline components."""
    pass

@pytest.mark.performance
def test_pipeline_throughput():
    """Performance test for pipeline throughput."""
    pass
```

### Writing Tests

#### Unit Test Example

```python
import pytest
from kakashi.core.records import LogRecord, LogLevel, LogContext

class TestLogRecord:
    """Test LogRecord functionality."""
    
    def test_record_creation(self):
        """Test basic record creation."""
        record = LogRecord(
            timestamp=1234567890.0,
            level=LogLevel.INFO,
            logger_name='test',
            message='Test message'
        )
        
        assert record.timestamp == 1234567890.0
        assert record.level == LogLevel.INFO
        assert record.logger_name == 'test'
        assert record.message == 'Test message'
    
    def test_record_immutability(self):
        """Test that records are immutable."""
        record = LogRecord(
            timestamp=1234567890.0,
            level=LogLevel.INFO,
            logger_name='test',
            message='Test message'
        )
        
        with pytest.raises(AttributeError):
            record.message = 'Modified message'
    
    def test_context_merging(self):
        """Test context merging functionality."""
        context1 = LogContext(ip='192.168.1.1', user_id='123')
        context2 = LogContext(ip='10.0.0.1', session_id='abc')
        
        merged = context1.merge(context2)
        
        assert merged.ip == '10.0.0.1'  # context2 takes precedence
        assert merged.user_id == '123'   # from context1
        assert merged.session_id == 'abc'  # from context2
```

#### Integration Test Example

```python
import pytest
import tempfile
from pathlib import Path
from kakashi.core.pipeline import Pipeline, PipelineConfig
from kakashi.core.records import LogRecord, LogLevel

class TestPipelineIntegration:
    """Test pipeline component integration."""
    
    def test_file_pipeline_integration(self):
        """Test complete file logging pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'test.log'
            
            # Create pipeline
            config = PipelineConfig(
                min_level=LogLevel.INFO,
                formatter=json_formatter,
                writers=(file_writer(log_file),)
            )
            pipeline = Pipeline(config)
            
            # Process log record
            record = LogRecord(
                timestamp=1234567890.0,
                level=LogLevel.INFO,
                logger_name='test',
                message='Test message'
            )
            pipeline.process(record)
            
            # Verify output
            assert log_file.exists()
            content = log_file.read_text()
            assert 'Test message' in content
            assert 'INFO' in content
```

### Performance Testing

```python
import pytest
import time
from kakashi.core.pipeline import Pipeline, PipelineConfig

@pytest.mark.performance
class TestPipelinePerformance:
    """Performance tests for pipeline components."""
    
    def test_pipeline_throughput(self):
        """Test pipeline throughput under load."""
        config = PipelineConfig(
            min_level=LogLevel.INFO,
            formatter=optimized_json_formatter,
            writers=(noop_writer,)  # No-op writer for pure pipeline testing
        )
        pipeline = Pipeline(config)
        
        # Warm up
        for _ in range(100):
            pipeline.process(create_test_record())
        
        # Benchmark
        start_time = time.time()
        num_records = 10000
        
        for _ in range(num_records):
            pipeline.process(create_test_record())
        
        elapsed = time.time() - start_time
        throughput = num_records / elapsed
        
        # Assert minimum throughput (adjust based on requirements)
        assert throughput > 50000, f"Throughput {throughput:.0f} records/sec too low"
```

## Architecture Guidelines

### Functional Design Principles

1. **Immutability**: All data structures should be immutable
2. **Pure Functions**: Pipeline components should be pure functions
3. **Composability**: Components should be easily composable
4. **Error Isolation**: Errors in one component shouldn't affect others

### Performance Considerations

1. **Hot Path Optimization**: Optimize the common logging path
2. **Lazy Evaluation**: Defer expensive operations until needed
3. **Memory Efficiency**: Minimize allocations and enable sharing
4. **Thread Safety**: Design for concurrent access without locks

### Error Handling Philosophy

1. **Never Crash**: Logging should never crash the host application
2. **Graceful Degradation**: Provide fallbacks when components fail
3. **Silent Operation**: Log internal errors to stderr, don't propagate
4. **Recovery**: Attempt to recover from transient failures

## Adding New Features

### Before Starting

1. **Open an issue** to discuss the feature
2. **Check existing code** for similar functionality
3. **Review architecture** to understand design patterns
4. **Write tests first** (TDD approach recommended)

### Feature Development Process

1. **Create feature branch**: `git checkout -b feature/my-feature`
2. **Write failing tests** for the new functionality
3. **Implement the feature** following existing patterns
4. **Make tests pass** with minimal code changes
5. **Refactor and optimize** while keeping tests green
6. **Add documentation** and examples
7. **Submit pull request** with clear description

### Example: Adding a New Enricher

```python
# 1. Write the test first
def test_hostname_enricher():
    """Test hostname enricher adds hostname to records."""
    record = LogRecord(
        timestamp=time.time(),
        level=LogLevel.INFO,
        logger_name='test',
        message='Test message'
    )
    
    enriched = hostname_enricher(record)
    
    assert enriched.extra_fields is not None
    assert 'hostname' in enriched.extra_fields
    assert enriched.extra_fields['hostname'] == socket.gethostname()

# 2. Implement the enricher
import socket
from kakashi.core.records import LogRecord

def hostname_enricher(record: LogRecord) -> LogRecord:
    """Add hostname to log record.
    
    Args:
        record: The log record to enrich.
    
    Returns:
        A new log record with hostname added to extra_fields.
    """
    hostname = socket.gethostname()
    extra_fields = {**(record.extra_fields or {}), 'hostname': hostname}
    
    return record.with_extra_fields(extra_fields)

# 3. Add to pipeline module exports
__all__ = [
    # ... existing exports ...
    'hostname_enricher',
]
```

## Pull Request Guidelines

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

## Release Process

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

## Community

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Email**: Direct contact for security issues

### Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct. Please be respectful and inclusive in all interactions.

### Recognition

Contributors are recognized in:
- **README.md**: Major contributors listed
- **CHANGELOG.md**: Contributors credited for each release
- **GitHub**: Contributor graphs and statistics
