# 🚀 Kakashi Performance Test Suite

A comprehensive, industry-standard test suite for validating Kakashi's performance, stability, and compatibility across different Python versions and environments.

## 📋 Overview

This test suite provides:

- **API Compatibility Tests**: Verify all Kakashi APIs work correctly
- **Performance Benchmark Tests**: Measure throughput, latency, and scalability
- **Stability Tests**: Validate reliability under stress conditions
- **Cross-Python Testing**: Support for Python 3.9, 3.10, 3.11, and 3.12
- **CI/CD Integration**: GitHub Actions workflow for automated testing
- **Comprehensive Reporting**: Detailed test reports and performance metrics

## 🏗️ Architecture

```
performance_tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_api_compatibility.py # API compatibility tests
├── test_performance.py      # Performance benchmark tests
├── test_stability.py        # Stability and stress tests
├── run_tests.py             # Main test runner script
├── generate_summary.py      # Summary report generator
├── pytest.ini              # Pytest configuration
├── requirements.txt         # Test dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd performance_tests
pip install -r requirements.txt
```

### 2. Run All Tests

```bash
python run_tests.py --install-deps
```

### 3. Run Specific Test Categories

```bash
# API compatibility only
python run_tests.py --api-only

# Performance benchmarks only
python run_tests.py --performance-only

# Stability tests only
python run_tests.py --stability-only
```

### 4. Generate Reports

```bash
python run_tests.py --save-report
```

## 🧪 Test Categories

### API Compatibility Tests (`test_api_compatibility.py`)

- **Basic Logging**: Import, creation, and basic operations
- **Configuration**: Environment setup and log level validation
- **Context Management**: Request and user context handling
- **Pipeline System**: Console and file pipeline creation
- **Error Handling**: Malformed inputs and exception logging

### Performance Benchmark Tests (`test_performance.py`)

- **Throughput**: Messages per second under various conditions
- **Concurrency**: Multi-threaded and async performance
- **Memory Usage**: Memory consumption and leak detection
- **Latency**: Single message and batch processing times
- **Scalability**: Performance scaling with load and concurrency

### Stability Tests (`test_stability.py`)

- **Concurrent Stability**: High-concurrency reliability
- **Memory Stability**: Memory leak detection and recovery
- **Error Handling**: Stability under error conditions
- **Long-Running**: Extended session stability

## 📊 Performance Metrics

The test suite measures and validates:

| Metric | Target | Description |
|--------|--------|-------------|
| Sync Throughput | >10K logs/sec | Synchronous logging performance |
| Async Throughput | >50K logs/sec | Asynchronous logging performance |
| Memory Usage | <100MB | Memory consumption under load |
| Concurrency Scaling | >1.0x | Performance improvement with threads |
| Error Rate | <1% | Stability under stress |

## 🔧 Configuration

### Pytest Configuration (`pytest.ini`)

- **Benchmark Settings**: 5 minimum rounds, auto warmup
- **Output Format**: Verbose with short tracebacks
- **Timeout**: 300 seconds per test
- **Markers**: Organized test categorization

### Test Configuration (`conftest.py`)

- **Performance Thresholds**: Configurable performance targets
- **Stability Parameters**: Configurable stress test parameters
- **Comparison Loggers**: Loguru, Structlog, Standard Library
- **Fixtures**: Reusable test components

## 🚀 CI/CD Integration

### GitHub Actions Workflow

The `.github/workflows/performance-tests.yml` provides:

- **Matrix Testing**: Python 3.9, 3.10, 3.11, 3.12
- **Automated Execution**: Push, PR, and scheduled runs
- **Artifact Management**: Test results and benchmark data
- **PR Integration**: Automatic comments with test results
- **Failure Handling**: Comprehensive error reporting

### Workflow Triggers

- **Push**: Main and develop branches
- **Pull Request**: Any PR affecting Kakashi or tests
- **Schedule**: Weekly runs on Sundays
- **Manual**: Workflow dispatch with custom parameters

## 📈 Running Tests Locally

### Prerequisites

```bash
# Install Kakashi in development mode
pip install -e ..

# Install test dependencies
pip install -r requirements.txt
```

### Basic Test Execution

```bash
# Run with pytest directly
pytest -v

# Run with custom markers
pytest -m "not slow"
pytest -m "benchmark"
pytest -m "stability"

# Run specific test file
pytest test_performance.py -v
```

### Advanced Options

```bash
# Performance benchmarks only
pytest test_performance.py --benchmark-only

# Generate JUnit XML reports
pytest --junitxml=results.xml

# Parallel execution
pytest -n auto

# Coverage reporting
pytest --cov=kakashi --cov-report=html
```

## 📊 Understanding Results

### Test Output

```
🚀 Kakashi Performance Test Suite
==================================================

🔧 Running API Compatibility Tests...
Command: python -m pytest test_api_compatibility.py -v --tb=short
✅ API Compatibility Tests (2.34s)

⚡ Running Performance Benchmark Tests...
Command: python -m pytest test_performance.py -v --benchmark-only --benchmark-sort=mean
✅ Performance Benchmark Tests (45.67s)

🛡️ Running Stability Tests...
Command: python -m pytest test_stability.py -v --tb=short
✅ Stability Tests (12.89s)

==================================================
📊 KAKASHI PERFORMANCE TEST REPORT
==================================================

📈 Summary:
  Total Tests: 3
  Successful: 3
  Failed: 0
  Success Rate: 100.0%
  Total Duration: 60.90s

🎉 ALL TESTS PASSED! Kakashi is performing excellently!
==================================================
```

### Benchmark Results

```
Kakashi vs Standard Library:
  Kakashi: 0.000123s
  StdLib:   0.000456s
  Speedup:  3.71x

Kakashi vs Loguru:
  Kakashi: 0.000123s
  Loguru:  0.000234s
  Speedup: 1.90x

Kakashi vs Structlog:
  Kakashi:  0.000123s
  Structlog: 0.000567s
  Speedup:   4.61x
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure Kakashi is installed
   pip install -e ..
   
   # Check Python path
   export PYTHONPATH="${PYTHONPATH}:${PWD}"
   ```

2. **Performance Test Failures**
   ```bash
   # Check system resources
   free -h
   nproc
   
   # Run with fewer iterations
   pytest test_performance.py --benchmark-min-rounds=3
   ```

3. **Memory Issues**
   ```bash
   # Monitor memory usage
   python -c "import psutil; print(psutil.virtual_memory())"
   
   # Force garbage collection
   python -c "import gc; gc.collect()"
   ```

### Debug Mode

```bash
# Enable verbose output
pytest -v -s

# Show local variables on failure
pytest --tb=long

# Run single test
pytest test_performance.py::TestThroughputBenchmarks::test_sync_throughput_benchmark -v
```

## 📚 Advanced Usage

### Custom Test Configuration

```python
# In conftest.py
@pytest.fixture(scope="session")
def custom_config():
    return {
        "performance": {
            "message_counts": [100, 1000, 10000],
            "thread_counts": [1, 2, 4],
            "timeout_seconds": 60
        }
    }
```

### Adding New Tests

```python
# In test_performance.py
class TestCustomBenchmarks:
    def test_custom_metric(self, benchmark, kakashi_sync_logger):
        def custom_operation():
            # Your custom test logic here
            pass
        
        result = benchmark(custom_operation)
        assert result.stats.mean < 0.1  # Custom assertion
```

### Custom Markers

```python
# In pytest.ini
markers =
    custom: marks tests as custom benchmarks
    integration: marks tests as integration tests

# In test files
@pytest.mark.custom
def test_custom_benchmark():
    pass
```

## 🤝 Contributing

### Adding New Tests

1. **Follow Naming Convention**: `test_*.py` files
2. **Use Appropriate Markers**: `@pytest.mark.benchmark`, `@pytest.mark.stability`
3. **Include Assertions**: Validate performance and stability requirements
4. **Add Documentation**: Clear docstrings explaining test purpose

### Test Guidelines

- **Performance Tests**: Use `pytest-benchmark` for accurate measurements
- **Stability Tests**: Include proper cleanup and resource management
- **API Tests**: Test both success and failure scenarios
- **Concurrency Tests**: Use appropriate synchronization primitives

### Code Quality

```bash
# Run linting
flake8 performance_tests/
black performance_tests/
isort performance_tests/

# Type checking
mypy performance_tests/
```

## 📄 License

This test suite is part of the Kakashi project and follows the same license terms.

## 🆘 Support

For issues with the test suite:

1. Check the troubleshooting section above
2. Review GitHub Actions logs for CI failures
3. Open an issue with detailed error information
4. Include system information and Python version

---

**Happy Testing! 🚀**
