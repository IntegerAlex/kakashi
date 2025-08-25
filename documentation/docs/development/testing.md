---
id: testing
title: Testing Guide
---

## Testing Philosophy

Kakashi follows a comprehensive testing strategy with multiple test types to ensure reliability, performance, and maintainability.

## Test Categories

### Unit Tests

Test individual components in isolation:

```python
import pytest
from kakashi.core.records import LogRecord, LogLevel, LogContext
from kakashi.core.pipeline import Pipeline, PipelineConfig

class TestLogRecord:
    """Unit tests for LogRecord functionality."""
    
    def test_record_creation(self):
        """Test basic record creation."""
        record = LogRecord(
            timestamp=1234567890.0,
            level=LogLevel.INFO,
            logger_name='test.module',
            message='Test message'
        )
        
        assert record.timestamp == 1234567890.0
        assert record.level == LogLevel.INFO
        assert record.logger_name == 'test.module'
        assert record.message == 'Test message'
        assert record.context is None
    
    def test_record_with_context(self):
        """Test record creation with context."""
        context = LogContext(
            ip='192.168.1.1',
            user_id='user123',
            custom={'trace_id': 'abc-123'}
        )
        
        record = LogRecord(
            timestamp=1234567890.0,
            level=LogLevel.INFO,
            logger_name='test.module',
            message='Test message',
            context=context
        )
        
        assert record.context.ip == '192.168.1.1'
        assert record.context.user_id == 'user123'
        assert record.context.custom['trace_id'] == 'abc-123'
    
    def test_record_immutability(self):
        """Test that records are immutable."""
        record = LogRecord(
            timestamp=1234567890.0,
            level=LogLevel.INFO,
            logger_name='test.module',
            message='Test message'
        )
        
        # Should raise AttributeError when trying to modify
        with pytest.raises(AttributeError):
            record.message = 'Modified message'
        
        with pytest.raises(AttributeError):
            record.level = LogLevel.ERROR
```

### Integration Tests

Test component interactions and workflows:

```python
import pytest
import tempfile
import json
from pathlib import Path
from kakashi.core.pipeline import Pipeline, PipelineConfig
from kakashi.core.formatters import json_formatter
from kakashi.core.writers import file_writer

class TestPipelineIntegration:
    """Integration tests for pipeline components."""
    
    def test_complete_logging_flow(self):
        """Test complete flow from record to file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / 'test.log'
            
            # Create pipeline with file output
            config = PipelineConfig(
                min_level=LogLevel.INFO,
                enrichers=(timestamp_enricher, context_enricher),
                filters=(level_filter,),
                formatter=json_formatter,
                writers=(file_writer(log_file),)
            )
            
            pipeline = Pipeline(config)
            
            # Process multiple records
            records = [
                LogRecord(
                    timestamp=1234567890.0,
                    level=LogLevel.INFO,
                    logger_name='test.app',
                    message='Application started'
                ),
                LogRecord(
                    timestamp=1234567891.0,
                    level=LogLevel.WARNING,
                    logger_name='test.app',
                    message='Configuration warning',
                    context=LogContext(user_id='admin')
                ),
                LogRecord(
                    timestamp=1234567892.0,
                    level=LogLevel.DEBUG,  # Should be filtered out
                    logger_name='test.app',
                    message='Debug message'
                )
            ]
            
            for record in records:
                pipeline.process(record)
            
            # Verify output
            assert log_file.exists()
            
            lines = log_file.read_text().strip().split('\n')
            assert len(lines) == 2  # DEBUG message filtered out
            
            # Verify JSON structure
            log1 = json.loads(lines[0])
            assert log1['level'] == 'INFO'
            assert log1['message'] == 'Application started'
            
            log2 = json.loads(lines[1])
            assert log2['level'] == 'WARNING'
            assert log2['context']['user_id'] == 'admin'
    
    def test_multi_writer_pipeline(self):
        """Test pipeline with multiple writers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / 'app.log'
            file2 = Path(temp_dir) / 'errors.log'
            
            # Create pipeline with multiple writers
            config = PipelineConfig(
                min_level=LogLevel.INFO,
                formatter=json_formatter,
                writers=(
                    file_writer(file1),
                    conditional_file_writer(file2, min_level=LogLevel.ERROR)
                )
            )
            
            pipeline = Pipeline(config)
            
            # Process records of different levels
            pipeline.process(LogRecord(
                timestamp=1234567890.0,
                level=LogLevel.INFO,
                logger_name='test',
                message='Info message'
            ))
            
            pipeline.process(LogRecord(
                timestamp=1234567891.0,
                level=LogLevel.ERROR,
                logger_name='test',
                message='Error message'
            ))
            
            # Verify outputs
            assert file1.exists()
            assert file2.exists()
            
            # Both messages in app.log
            app_lines = file1.read_text().strip().split('\n')
            assert len(app_lines) == 2
            
            # Only error message in errors.log
            error_lines = file2.read_text().strip().split('\n')
            assert len(error_lines) == 1
            
            error_log = json.loads(error_lines[0])
            assert error_log['level'] == 'ERROR'
```

### Async Tests

Test asynchronous components:

```python
import pytest
import asyncio
from kakashi.core.async_pipeline import AsyncPipeline, AsyncPipelineConfig

class TestAsyncPipeline:
    """Tests for async pipeline functionality."""
    
    @pytest.mark.asyncio
    async def test_async_pipeline_processing(self):
        """Test async pipeline processes records correctly."""
        processed_messages = []
        
        async def test_writer(message: str) -> None:
            processed_messages.append(message)
        
        config = AsyncPipelineConfig(
            min_level=LogLevel.INFO,
            formatter=json_formatter,
            writers=(test_writer,),
            buffer_size=10,
            flush_interval=0.1
        )
        
        pipeline = AsyncPipeline(config)
        
        # Process records
        records = [
            LogRecord(
                timestamp=1234567890.0 + i,
                level=LogLevel.INFO,
                logger_name='test.async',
                message=f'Message {i}'
            )
            for i in range(5)
        ]
        
        for record in records:
            await pipeline.process(record)
        
        # Wait for flush
        await asyncio.sleep(0.2)
        
        # Verify all messages processed
        assert len(processed_messages) == 5
        for i, message in enumerate(processed_messages):
            log_data = json.loads(message)
            assert log_data['message'] == f'Message {i}'
    
    @pytest.mark.asyncio
    async def test_async_backpressure(self):
        """Test async pipeline handles backpressure correctly."""
        processed_count = 0
        dropped_count = 0
        
        async def slow_writer(message: str) -> None:
            nonlocal processed_count
            await asyncio.sleep(0.01)  # Simulate slow I/O
            processed_count += 1
        
        def drop_handler(record: LogRecord) -> None:
            nonlocal dropped_count
            dropped_count += 1
        
        config = AsyncPipelineConfig(
            min_level=LogLevel.INFO,
            formatter=json_formatter,
            writers=(slow_writer,),
            buffer_size=10,
            flush_interval=0.1,
            backpressure_limit=20,
            drop_handler=drop_handler
        )
        
        pipeline = AsyncPipeline(config)
        
        # Send many records quickly to trigger backpressure
        for i in range(50):
            await pipeline.process(LogRecord(
                timestamp=1234567890.0 + i,
                level=LogLevel.INFO,
                logger_name='test.backpressure',
                message=f'Message {i}'
            ))
        
        # Wait for processing
        await asyncio.sleep(1.0)
        await pipeline.flush()
        
        # Verify some messages were dropped due to backpressure
        assert dropped_count > 0
        assert processed_count + dropped_count == 50
```

### Performance Tests

Test performance characteristics:

```python
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.performance
class TestLoggingPerformance:
    """Performance tests for logging components."""
    
    def test_single_thread_throughput(self):
        """Test single-thread logging throughput."""
        # Create high-performance pipeline
        config = PipelineConfig(
            min_level=LogLevel.INFO,
            formatter=fast_text_formatter,
            writers=(noop_writer,)  # No-op writer for pure pipeline testing
        )
        
        pipeline = Pipeline(config)
        
        # Warm up
        for _ in range(100):
            pipeline.process(create_test_record())
        
        # Benchmark
        start_time = time.time()
        num_records = 100000
        
        for i in range(num_records):
            pipeline.process(LogRecord(
                timestamp=start_time + i * 0.000001,
                level=LogLevel.INFO,
                logger_name='perf.test',
                message=f'Performance test message {i}'
            ))
        
        elapsed = time.time() - start_time
        throughput = num_records / elapsed
        
        # Assert minimum throughput (adjust based on hardware)
        assert throughput > 100000, f"Throughput {throughput:.0f} records/sec too low"
        
        print(f"Single-thread throughput: {throughput:.0f} records/sec")
    
    def test_concurrent_throughput(self):
        """Test concurrent logging throughput."""
        config = PipelineConfig(
            min_level=LogLevel.INFO,
            formatter=json_formatter,
            writers=(noop_writer,)
        )
        
        pipeline = Pipeline(config)
        num_threads = 10
        records_per_thread = 10000
        
        def log_worker(thread_id: int) -> float:
            start_time = time.time()
            
            for i in range(records_per_thread):
                pipeline.process(LogRecord(
                    timestamp=start_time + i * 0.000001,
                    level=LogLevel.INFO,
                    logger_name=f'perf.thread{thread_id}',
                    message=f'Thread {thread_id} message {i}'
                ))
            
            return time.time() - start_time
        
        # Run concurrent test
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            thread_times = list(executor.map(log_worker, range(num_threads)))
        total_time = time.time() - start_time
        
        total_records = num_threads * records_per_thread
        overall_throughput = total_records / total_time
        
        print(f"Concurrent throughput: {overall_throughput:.0f} records/sec")
        print(f"Average thread time: {sum(thread_times) / len(thread_times):.3f}s")
        
        # Assert reasonable concurrent performance
        assert overall_throughput > 50000, f"Concurrent throughput too low: {overall_throughput:.0f}"
    
    def test_memory_usage(self):
        """Test memory usage during logging."""
        import tracemalloc
        import gc
        
        tracemalloc.start()
        
        config = PipelineConfig(
            min_level=LogLevel.INFO,
            formatter=json_formatter,
            writers=(noop_writer,)
        )
        
        pipeline = Pipeline(config)
        
        # Take initial snapshot
        snapshot1 = tracemalloc.take_snapshot()
        
        # Perform logging operations
        for i in range(10000):
            pipeline.process(LogRecord(
                timestamp=time.time(),
                level=LogLevel.INFO,
                logger_name='memory.test',
                message=f'Memory test message {i}',
                context=LogContext(
                    user_id=f'user_{i % 100}',
                    custom={'iteration': i, 'data': 'x' * 50}
                )
            ))
        
        # Force garbage collection
        gc.collect()
        
        # Take final snapshot
        snapshot2 = tracemalloc.take_snapshot()
        
        # Analyze memory usage
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_memory = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        
        # Memory usage should be reasonable (less than 10MB for 10k records)
        memory_mb = total_memory / 1024 / 1024
        assert memory_mb < 10, f"Memory usage too high: {memory_mb:.1f}MB"
        
        print(f"Memory usage: {memory_mb:.1f}MB for 10,000 records")
```

### Framework Integration Tests

Test web framework integrations:

```python
import pytest
from unittest.mock import Mock, patch

class TestFastAPIIntegration:
    """Test FastAPI integration."""
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_fastapi_middleware_setup(self):
        """Test FastAPI middleware setup."""
        from fastapi import FastAPI
        from kakashi.integrations.fastapi_integration import setup_fastapi_enterprise
        
        app = FastAPI()
        
        # Set up middleware
        middleware = setup_fastapi_enterprise(app, service_name="test-api")
        
        # Verify middleware was added
        assert len(app.user_middleware) > 0
        
        # Check middleware configuration
        middleware_obj = app.user_middleware[0]
        assert 'ObservabilityMiddleware' in str(middleware_obj.cls)
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    @pytest.mark.asyncio
    async def test_fastapi_request_logging(self):
        """Test FastAPI request logging."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from kakashi.integrations.fastapi_integration import setup_fastapi_enterprise
        
        app = FastAPI()
        setup_fastapi_enterprise(app, service_name="test-api")
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        
        # Capture logs
        with patch('kakashi.info') as mock_log:
            response = client.get("/test")
            
            assert response.status_code == 200
            
            # Verify request was logged
            mock_log.assert_called()
            
            # Check log content
            call_args = mock_log.call_args
            assert 'GET /test' in str(call_args)

class TestFlaskIntegration:
    """Test Flask integration."""
    
    @pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not available")
    def test_flask_setup(self):
        """Test Flask integration setup."""
        from flask import Flask
        from kakashi.integrations.flask_integration import setup_flask_enterprise
        
        app = Flask(__name__)
        
        # Set up integration
        handler = setup_flask_enterprise(app, service_name="test-flask")
        
        # Verify handler was configured
        assert handler is not None
        assert hasattr(app, '_mylogs_setup')
        assert app._mylogs_setup is True
    
    @pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not available")
    def test_flask_request_logging(self):
        """Test Flask request logging."""
        from flask import Flask
        from kakashi.integrations.flask_integration import setup_flask_enterprise
        
        app = Flask(__name__)
        setup_flask_enterprise(app, service_name="test-flask")
        
        @app.route('/test')
        def test_endpoint():
            return {"message": "test"}
        
        client = app.test_client()
        
        # Capture logs
        with patch('kakashi.info') as mock_log:
            response = client.get('/test')
            
            assert response.status_code == 200
            
            # Verify request was logged
            mock_log.assert_called()
```

## Test Utilities

### Test Fixtures

Common test fixtures for reuse:

```python
import pytest
import tempfile
from pathlib import Path
from kakashi.core.records import LogRecord, LogLevel, LogContext

@pytest.fixture
def temp_log_file():
    """Provide a temporary log file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_file = Path(f.name)
    
    yield log_file
    
    # Cleanup
    if log_file.exists():
        log_file.unlink()

@pytest.fixture
def sample_log_record():
    """Provide a sample log record for testing."""
    return LogRecord(
        timestamp=1234567890.0,
        level=LogLevel.INFO,
        logger_name='test.module',
        message='Test message',
        context=LogContext(
            ip='192.168.1.1',
            user_id='test_user',
            custom={'trace_id': 'abc-123'}
        )
    )

@pytest.fixture
def mock_writer():
    """Provide a mock writer for testing."""
    messages = []
    
    def writer(message: str) -> None:
        messages.append(message)
    
    writer.messages = messages
    return writer

@pytest.fixture
def test_pipeline(mock_writer):
    """Provide a test pipeline with mock writer."""
    config = PipelineConfig(
        min_level=LogLevel.DEBUG,
        formatter=json_formatter,
        writers=(mock_writer,)
    )
    
    return Pipeline(config)
```

### Test Helpers

Utility functions for testing:

```python
def create_test_record(
    level: LogLevel = LogLevel.INFO,
    message: str = "Test message",
    logger_name: str = "test.logger",
    **context_fields
) -> LogRecord:
    """Create a test log record with optional context."""
    context = None
    if context_fields:
        context = LogContext(**context_fields)
    
    return LogRecord(
        timestamp=time.time(),
        level=level,
        logger_name=logger_name,
        message=message,
        context=context
    )

def assert_log_contains(log_output: str, expected_fields: dict):
    """Assert that log output contains expected fields."""
    import json
    
    log_data = json.loads(log_output)
    
    for field, expected_value in expected_fields.items():
        assert field in log_data, f"Field '{field}' not found in log output"
        assert log_data[field] == expected_value, f"Field '{field}' has value {log_data[field]}, expected {expected_value}"

def wait_for_async_processing(pipeline: AsyncPipeline, timeout: float = 1.0):
    """Wait for async pipeline to process all pending records."""
    import asyncio
    
    async def wait():
        start_time = time.time()
        while pipeline.get_buffer_size() > 0 and time.time() - start_time < timeout:
            await asyncio.sleep(0.01)
        
        # Final flush
        await pipeline.flush()
    
    asyncio.run(wait())
```

## Test Configuration

### pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

addopts = 
    --strict-markers
    --disable-warnings
    -v
    --tb=short

markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow tests (can be skipped)
    asyncio: Async tests
    fastapi: FastAPI integration tests
    flask: Flask integration tests
    django: Django integration tests

# Async test configuration
asyncio_mode = auto
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = kakashi
omit = 
    */tests/*
    */examples/*
    */venv/*
    */build/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

[html]
directory = htmlcov
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kakashi --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m performance

# Run tests in parallel
pytest -n auto

# Run with verbose output
pytest -v -s
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.7, 3.8, 3.9, "3.10", "3.11", "3.12"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev,all]
    
    - name: Run tests
      run: |
        pytest --cov=kakashi --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

This comprehensive testing guide ensures Kakashi maintains high quality and reliability across all components and use cases.
