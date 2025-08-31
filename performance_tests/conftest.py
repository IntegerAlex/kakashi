"""
Pytest configuration for Kakashi performance tests.

This file provides fixtures and configuration for running
industry-standard performance and compatibility tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(scope="session", autouse=True)
def cleanup_async_logging():
    """Ensure async logging is properly shut down after all tests."""
    yield
    from kakashi import shutdown_async_logging
    shutdown_async_logging()

@pytest.fixture(scope="session")
def temp_test_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test artifacts."""
    temp_dir = Path(tempfile.mkdtemp(prefix="kakashi_tests_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration parameters."""
    return {
        "performance": {
            "message_counts": [1000, 10000, 50000],
            "thread_counts": [1, 2, 4, 8],
            "timeout_seconds": 300,
            "memory_limit_mb": 500,
            "min_sync_throughput": 10000,
            "min_async_throughput": 50000,
            "max_memory_usage": 100,
            "max_concurrency_penalty": 0.3
        },
        "stability": {
            "concurrent_threads": 10,
            "test_duration_seconds": 60,
            "memory_sampling_interval": 5,
            "max_memory_growth_mb": 50,
            "max_error_rate": 0.01,
            "max_response_time_ms": 1000
        }
    }

@pytest.fixture(scope="session")
def comparison_loggers():
    """Set up comparison logging libraries."""
    loggers = {}
    
    try:
        # Standard library logging
        import logging
        logging.basicConfig(level=logging.INFO)
        std_logger = logging.getLogger("stdlib_test")
        std_logger.addHandler(logging.NullHandler())
        std_logger.propagate = False
        loggers["standard_library"] = std_logger
        print("✅ Standard library logging available")
    except ImportError as e:
        print(f"⚠️  Standard library logging not available: {e}")
    except Exception as e:
        print(f"⚠️  Unexpected error setting up standard library logging: {e}")
    
    try:
        # Loguru
        from loguru import logger
        logger.remove()
        logger.add(lambda msg: None, level="INFO")
        loggers["loguru"] = logger
        print("✅ Loguru available")
    except ImportError:
        print("⚠️  Loguru not available (not installed)")
    except ModuleNotFoundError:
        print("⚠️  Loguru not available (not installed)")
    except Exception as e:
        print(f"⚠️  Unexpected error setting up Loguru: {e}")
    
    try:
        # Structlog
        import structlog
        structlog.configure(
            processors=[structlog.processors.JSONRenderer()],
            wrapper_class=structlog.BoundLogger,
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        loggers["structlog"] = structlog.get_logger("structlog_test")
        print("✅ Structlog available")
    except ImportError:
        print("⚠️  Structlog not available (not installed)")
    except ModuleNotFoundError:
        print("⚠️  Structlog not available (not installed)")
    except Exception as e:
        print(f"⚠️  Unexpected error setting up Structlog: {e}")
    
    if not loggers:
        print("⚠️  No comparison loggers available - tests will only run against Kakashi")
    
    return loggers

@pytest.fixture(scope="function")
def kakashi_sync_logger():
    """Create a fresh Kakashi sync logger for each test."""
    from kakashi import get_logger
    return get_logger("test_sync_logger")

@pytest.fixture(scope="function")
def kakashi_async_logger():
    """Create a fresh Kakashi async logger for each test.
    
    Note: This logger is "asynchronous" in the sense that it doesn't block
    the calling thread, but it doesn't use Python's async/await syntax.
    The info() method is synchronous and enqueues messages to a background queue.
    """
    from kakashi import get_async_logger
    logger = get_async_logger("test_async_logger")
    yield logger
    # Clean up async logging to prevent daemon thread errors
    from kakashi import shutdown_async_logging
    shutdown_async_logging()

@pytest.fixture(scope="function")
def kakashi_structured_logger():
    """Create a fresh Kakashi structured logger for each test."""
    from kakashi.core import create_structured_logger
    return create_structured_logger("test_structured_logger")
