"""
API Compatibility Tests for Kakashi.

These tests ensure all Kakashi APIs work correctly and
maintain backward compatibility.
"""

import pytest
import sys
import traceback
from pathlib import Path
from typing import Any
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestBasicLogging:
    """Test basic logging functionality."""
    
    def test_basic_imports(self):
        """Test that all basic imports work."""
        from kakashi import get_logger, get_async_logger
        from kakashi.core import Logger, AsyncLogger, LogLevel
        from kakashi.core.records import LogRecord, LogContext
        
        assert get_logger is not None
        assert get_async_logger is not None
        assert Logger is not None
        assert AsyncLogger is not None
        assert LogLevel is not None
        assert LogRecord is not None
        assert LogContext is not None
    
    def test_sync_logger_creation(self, kakashi_sync_logger):
        """Test sync logger creation and basic operations."""
        logger = kakashi_sync_logger
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'critical')
    
    def test_async_logger_creation(self, kakashi_async_logger):
        """Test async logger creation and basic operations."""
        logger = kakashi_async_logger
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'critical')
    
    def test_basic_logging_operations(self, kakashi_sync_logger):
        """Test that basic logging operations work without errors."""
        logger = kakashi_sync_logger
        
        # Test all log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Test with fields
        logger.info("Message with fields", user_id=123, action="test")
        
        # Test exception logging
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("Exception occurred")
    
    def test_structured_logging(self, kakashi_structured_logger):
        """Test structured logging functionality."""
        logger = kakashi_structured_logger
        assert logger is not None
        
        # Test structured logging with fields
        logger.info("Structured message", user_id=123, action="test")
        logger.metric("test_metric", 42.5, unit="count")
        logger.counter("test_counter", 1)
        logger.timer("test_operation", 15.5, unit="ms")

class TestConfiguration:
    """Test configuration system."""
    
    def test_environment_setup(self):
        """Test environment configuration setup."""
        from kakashi import setup_logging, set_log_level
        from kakashi.core import LogLevel
        
        # Test environment setup
        config = setup_logging("development", service_name="test-service")
        assert config is not None
        
        # Test log level setting
        set_log_level(LogLevel.DEBUG)
        
        # Verify the change took effect
        from kakashi.core import get_environment_config
        env_config = get_environment_config()
        assert env_config.file_level == LogLevel.DEBUG
    
    def test_log_level_validation(self):
        """Test log level validation and conversion."""
        from kakashi.core import LogLevel
        
        # Test string to LogLevel conversion
        assert LogLevel.from_name("DEBUG") == LogLevel.DEBUG
        assert LogLevel.from_name("INFO") == LogLevel.INFO
        assert LogLevel.from_name("WARNING") == LogLevel.WARNING
        assert LogLevel.from_name("ERROR") == LogLevel.ERROR
        assert LogLevel.from_name("CRITICAL") == LogLevel.CRITICAL
        
        # Test integer to LogLevel conversion
        assert LogLevel(10) == LogLevel.DEBUG
        assert LogLevel(20) == LogLevel.INFO
        assert LogLevel(30) == LogLevel.WARNING
        assert LogLevel(40) == LogLevel.ERROR
        assert LogLevel(50) == LogLevel.CRITICAL

class TestContextManagement:
    """Test context management functionality."""
    
    def test_request_context(self):
        """Test request context management."""
        from kakashi import set_request_context, clear_request_context
        from kakashi.core import get_current_context
        
        # Set request context
        set_request_context(ip="127.0.0.1", access="GET /test")
        
        # Verify context is set
        context = get_current_context()
        assert context is not None
        assert context.ip == "127.0.0.1"
        assert context.access == "GET /test"
        
        # Clear context
        clear_request_context()
        
        # Verify context is cleared
        context = get_current_context()
        assert context is None
    
    def test_user_context(self):
        """Test user context management."""
        from kakashi import set_user_context
        from kakashi.core import get_current_context
        
        # Set user context
        set_user_context(user_id="test-user", session_id="test-session")
        
        # Verify context is set
        context = get_current_context()
        assert context is not None
        assert context.user_id == "test-user"
        assert context.session_id == "test-session"
    
    def test_context_scope(self):
        """Test context scope management."""
        from kakashi.core import context_scope, LogContext, get_current_context
        
        # Test context scope
        with context_scope(LogContext(custom={"test": "value"})):
            context = get_current_context()
            assert context is not None
            assert context.custom.get("test") == "value"
        
        # Verify context is restored
        context = get_current_context()
        assert context is None or "test" not in context.custom

class TestPipelineSystem:
    """Test pipeline system functionality."""
    
    def test_pipeline_creation(self):
        """Test pipeline creation and configuration."""
        from kakashi.core.pipeline import create_console_pipeline, create_file_pipeline
        from kakashi.core.records import LogLevel
        
        # Test console pipeline
        console_pipeline = create_console_pipeline(min_level=LogLevel.INFO)
        assert console_pipeline is not None
        assert hasattr(console_pipeline, 'process')
        
        # Test file pipeline
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            file_pipeline = create_file_pipeline(f.name, min_level=LogLevel.INFO)
            assert file_pipeline is not None
            assert hasattr(file_pipeline, 'process')
            
            # Clean up
            import os
            os.unlink(f.name)
    
    def test_pipeline_processing(self):
        """Test pipeline processing functionality."""
        from kakashi.core.pipeline import create_console_pipeline
        from kakashi.core.records import LogRecord, LogLevel
        from kakashi.core.records import LogContext
        
        pipeline = create_console_pipeline(min_level=LogLevel.INFO)
        
        # Create a test record
        context = LogContext()
        record = LogRecord(
            level=LogLevel.INFO,
            message="Test message",
            context=context,
            timestamp=1234567890.0
        )
        
        # Process the record
        result = pipeline.process(record)
        assert result is not None

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_log_levels(self):
        """Test handling of invalid log levels."""
        from kakashi.core import LogLevel
        
        # Test invalid string
        with pytest.raises(ValueError):
            LogLevel.from_name("INVALID")
        
        # Test invalid integer
        with pytest.raises(ValueError):
            LogLevel(999)
    
    def test_malformed_messages(self):
        """Test handling of malformed messages."""
        logger = pytest.importorskip("kakashi").get_logger("test_malformed")
        
        # Test None message
        logger.info(None)
        
        # Test empty message
        logger.info("")
        
        # Test very long message
        long_message = "x" * 10000
        logger.info(long_message)
    
    def test_concurrent_access(self):
        """Test concurrent access to loggers."""
        import threading
        import time
        
        logger = pytest.importorskip("kakashi").get_logger("test_concurrent")
        
        def log_messages():
            for i in range(100):
                logger.info(f"Message {i} from thread {threading.current_thread().name}")
                time.sleep(0.001)
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_messages, name=f"Thread-{i}")
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # If we get here without errors, concurrent access works
        assert True
