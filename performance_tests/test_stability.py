"""
Stability Tests for Kakashi.

These tests verify Kakashi's reliability and stability under
various stress conditions and edge cases.
"""

import pytest
import time
import threading
import asyncio
import random
import string
import gc
import psutil
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestConcurrentStability:
    """Test stability under concurrent access."""
    
    def test_high_concurrency_stability(self, kakashi_sync_logger):
        """Test stability under high concurrent load."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id: int, message_count: int):
            try:
                for i in range(message_count):
                    kakashi_sync_logger.info(
                        f"Worker {worker_id} message {i}",
                        worker_id=worker_id,
                        message_id=i,
                        timestamp=time.time()
                    )
                    time.sleep(0.001)  # Small delay to simulate real work
                results.append(f"Worker {worker_id} completed successfully")
            except Exception as e:
                errors.append(f"Worker {worker_id} failed: {e}")
        
        # Start many concurrent workers
        thread_count = 20
        messages_per_worker = 100
        
        threads = []
        start_time = time.time()
        
        for i in range(thread_count):
            thread = threading.Thread(
                target=worker,
                args=(i, messages_per_worker),
                name=f"Worker-{i}"
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        total_messages = thread_count * messages_per_worker
        throughput = total_messages / total_time
        
        print(f"\nHigh Concurrency Stability Test:")
        print(f"  Threads: {thread_count}")
        print(f"  Messages per worker: {messages_per_worker}")
        print(f"  Total messages: {total_messages}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.0f} msg/s")
        print(f"  Successful workers: {len(results)}")
        print(f"  Failed workers: {len(errors)}")
        
        # Assertions
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == thread_count, f"Not all workers completed: {len(results)}/{thread_count}"
        assert throughput > 1000, f"Throughput too low: {throughput:.0f} msg/s"
    
    def test_concurrent_logger_creation(self, kakashi_sync_logger):
        """Test stability when creating many loggers concurrently."""
        import threading
        
        loggers = []
        errors = []
        
        def create_logger(worker_id: int):
            try:
                for i in range(10):
                    logger = kakashi_sync_logger.__class__(f"concurrent_logger_{worker_id}_{i}")
                    loggers.append(logger)
                    
                    # Use the logger immediately
                    logger.info(f"Test message from logger {worker_id}_{i}")
                    
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Logger creation failed for worker {worker_id}: {e}")
        
        # Start concurrent logger creation
        thread_count = 10
        threads = []
        
        for i in range(thread_count):
            thread = threading.Thread(target=create_logger, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        print(f"\nConcurrent Logger Creation Test:")
        print(f"  Threads: {thread_count}")
        print(f"  Loggers created: {len(loggers)}")
        print(f"  Errors: {len(errors)}")
        
        # Assertions
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(loggers) == thread_count * 10, f"Expected {thread_count * 10} loggers, got {len(loggers)}"
    
    def test_mixed_operation_stability(self, kakashi_sync_logger):
        """Test stability with mixed operations (read/write/delete)."""
        import threading
        import time
        
        operations = []
        errors = []
        
        def mixed_operations(worker_id: int):
            try:
                for i in range(50):
                    # Different types of operations
                    if i % 3 == 0:
                        # Info logging
                        kakashi_sync_logger.info(f"Info message {i} from worker {worker_id}")
                    elif i % 3 == 1:
                        # Warning logging
                        kakashi_sync_logger.warning(f"Warning message {i} from worker {worker_id}")
                    else:
                        # Error logging
                        kakashi_sync_logger.error(f"Error message {i} from worker {worker_id}")
                    
                    operations.append(f"Worker {worker_id} operation {i}")
                    time.sleep(0.001)
                    
            except Exception as e:
                errors.append(f"Worker {worker_id} failed: {e}")
        
        # Start mixed operations
        thread_count = 8
        threads = []
        
        for i in range(thread_count):
            thread = threading.Thread(target=mixed_operations, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        print(f"\nMixed Operations Stability Test:")
        print(f"  Threads: {thread_count}")
        print(f"  Operations completed: {len(operations)}")
        print(f"  Errors: {len(errors)}")
        
        # Assertions
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(operations) == thread_count * 50, f"Expected {thread_count * 50} operations, got {len(operations)}"

class TestMemoryStability:
    """Test memory stability under various conditions."""
    
    def test_memory_leak_detection(self, kakashi_sync_logger):
        """Test for memory leaks during extended logging."""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Get baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_samples = [baseline_memory]
        
        # Log messages in cycles to detect memory leaks
        for cycle in range(5):
            print(f"Memory cycle {cycle + 1}/5...")
            
            # Log many messages
            for i in range(10000):
                kakashi_sync_logger.info(f"Memory leak test message {i} cycle {cycle}")
            
            # Force garbage collection
            gc.collect()
            
            # Sample memory
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(current_memory)
            
            # Small delay between cycles
            time.sleep(0.1)
        
        # Analyze memory growth
        memory_growth = memory_samples[-1] - memory_samples[0]
        max_memory = max(memory_samples)
        min_memory = min(memory_samples)
        memory_variance = max_memory - min_memory
        
        print(f"\nMemory Leak Detection Test:")
        print(f"  Baseline memory: {baseline_memory:.2f} MB")
        print(f"  Final memory: {memory_samples[-1]:.2f} MB")
        print(f"  Memory change: {memory_growth:+.2f} MB")
        print(f"  Memory variance: {memory_variance:.2f} MB")
        print(f"  Memory samples: {[f'{m:.2f}' for m in memory_samples]}")
        
        # Assertions - handle both positive and negative memory changes
        if memory_growth > 0:
            # Memory increased - check it's reasonable
            assert memory_growth < 50, f"Memory growth too high: {memory_growth:.2f} MB"
        else:
            # Memory decreased (garbage collection freed memory) - this is good
            print(f"  ✅ Memory decreased by {abs(memory_growth):.2f} MB (garbage collection working)")
            # Allow up to 30MB decrease (aggressive garbage collection)
            assert memory_growth > -30, f"Memory decrease too aggressive: {memory_growth:.2f} MB"
        
        # Memory variance should be reasonable regardless of growth direction
        assert memory_variance < 100, f"Memory variance too high: {memory_variance:.2f} MB"
    
    def test_memory_pressure_recovery(self, kakashi_sync_logger):
        """Test memory recovery after pressure."""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Get baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Apply memory pressure
        pressure_loggers = []
        for i in range(100):
            logger = kakashi_sync_logger.__class__(f"pressure_{i}")
            pressure_loggers.append(logger)
            
            for j in range(100):
                logger.info(f"Pressure message {j} from logger {i}")
        
        # Measure memory under pressure
        gc.collect()
        pressure_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Clear pressure (remove references)
        pressure_loggers.clear()
        gc.collect()
        
        # Measure recovery
        recovery_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\nMemory Pressure Recovery Test:")
        print(f"  Baseline memory: {baseline_memory:.2f} MB")
        print(f"  Pressure memory: {pressure_memory:.2f} MB")
        print(f"  Recovery memory: {recovery_memory:.2f} MB")
        print(f"  Pressure increase: {pressure_memory - baseline_memory:+.2f} MB")
        print(f"  Recovery change: {recovery_memory - baseline_memory:+.2f} MB")
        
        # Assertions
        pressure_increase = pressure_memory - baseline_memory
        recovery_change = recovery_memory - baseline_memory
        
        # Pressure should increase memory usage
        assert pressure_increase > 0, "Memory pressure not applied"
        
        # Recovery should be close to baseline (within 20MB)
        # Allow for some memory overhead from the test itself
        # Handle both positive and negative recovery changes
        if recovery_change > 0:
            # Memory still above baseline
            assert recovery_change < 20, f"Memory not recovered to baseline: {recovery_change:+.2f} MB"
        else:
            # Memory below baseline (garbage collection freed memory) - this is good
            print(f"  ✅ Memory recovered below baseline by {abs(recovery_change):.2f} MB (garbage collection working)")
            # Allow up to 15MB decrease (aggressive garbage collection)
            assert recovery_change > -15, f"Memory decrease too aggressive: {recovery_change:+.2f} MB"

class TestErrorHandlingStability:
    """Test stability under error conditions."""
    
    def test_malformed_input_stability(self, kakashi_sync_logger):
        """Test stability with malformed inputs."""
        import threading
        
        errors = []
        successful_logs = []
        
        def malformed_input_worker(worker_id: int):
            try:
                for i in range(100):
                    # Test various malformed inputs
                    if i % 4 == 0:
                        # None message
                        kakashi_sync_logger.info(None)
                    elif i % 4 == 1:
                        # Empty message
                        kakashi_sync_logger.info("")
                    elif i % 4 == 2:
                        # Very long message
                        long_message = "x" * 10000
                        kakashi_sync_logger.info(long_message)
                    else:
                        # Invalid field types
                        kakashi_sync_logger.info("Test message", invalid_field=object())
                    
                    successful_logs.append(f"Worker {worker_id} log {i}")
                    time.sleep(0.001)
                    
            except Exception as e:
                errors.append(f"Worker {worker_id} failed: {e}")
        
        # Start malformed input workers
        thread_count = 5
        threads = []
        
        for i in range(thread_count):
            thread = threading.Thread(target=malformed_input_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        print(f"\nMalformed Input Stability Test:")
        print(f"  Threads: {thread_count}")
        print(f"  Successful logs: {len(successful_logs)}")
        print(f"  Errors: {len(errors)}")
        
        # Assertions - should handle malformed inputs gracefully
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(successful_logs) == thread_count * 100, f"Expected {thread_count * 100} logs, got {len(successful_logs)}"
    
    def test_exception_logging_stability(self, kakashi_sync_logger):
        """Test stability when logging exceptions."""
        import threading
        
        errors = []
        successful_logs = []
        
        def exception_logging_worker(worker_id: int):
            try:
                for i in range(50):
                    try:
                        # Intentionally raise exceptions
                        if i % 3 == 0:
                            raise ValueError(f"Test value error {i}")
                        elif i % 3 == 1:
                            raise RuntimeError(f"Test runtime error {i}")
                        else:
                            raise TypeError(f"Test type error {i}")
                    except Exception as e:
                        # Log the exception
                        kakashi_sync_logger.exception(f"Caught exception in worker {worker_id}")
                    
                    successful_logs.append(f"Worker {worker_id} exception log {i}")
                    time.sleep(0.001)
                    
            except Exception as e:
                errors.append(f"Worker {worker_id} failed: {e}")
        
        # Start exception logging workers
        thread_count = 4
        threads = []
        
        for i in range(thread_count):
            thread = threading.Thread(target=exception_logging_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        print(f"\nException Logging Stability Test:")
        print(f"  Threads: {thread_count}")
        print(f"  Successful logs: {len(successful_logs)}")
        print(f"  Errors: {len(errors)}")
        
        # Assertions
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(successful_logs) == thread_count * 50, f"Expected {thread_count * 50} logs, got {len(successful_logs)}"

class TestLongRunningStability:
    """Test stability over extended periods."""
    
    def test_extended_logging_stability(self, kakashi_sync_logger):
        """Test stability during extended logging sessions."""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Get baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        message_count = 0
        errors = []
        
        try:
            # Log messages continuously for a period
            while time.time() - start_time < 30:  # 30 seconds
                try:
                    kakashi_sync_logger.info(
                        f"Extended stability test message {message_count}",
                        timestamp=time.time(),
                        message_id=message_count
                    )
                    message_count += 1
                    
                    # Small delay to prevent overwhelming
                    time.sleep(0.01)
                    
                except Exception as e:
                    errors.append(f"Message {message_count} failed: {e}")
                    break
                    
        except KeyboardInterrupt:
            pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Final memory measurement
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_change = final_memory - baseline_memory
        
        throughput = message_count / total_time
        
        print(f"\nExtended Logging Stability Test:")
        print(f"  Duration: {total_time:.2f}s")
        print(f"  Messages logged: {message_count}")
        print(f"  Throughput: {throughput:.0f} msg/s")
        print(f"  Baseline memory: {baseline_memory:.2f} MB")
        print(f"  Final memory: {final_memory:.2f} MB")
        print(f"  Memory change: {memory_change:+.2f} MB")
        print(f"  Errors: {len(errors)}")
        
        # Assertions
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert message_count > 1000, f"Too few messages logged: {message_count}"
        assert throughput > 50, f"Throughput too low: {throughput:.0f} msg/s"
        
        # Handle both positive and negative memory changes
        if memory_change > 0:
            # Memory increased - check it's reasonable
            assert memory_change < 100, f"Memory growth too high: {memory_change:.2f} MB"
        else:
            # Memory decreased (garbage collection freed memory) - this is good
            print(f"  ✅ Memory decreased by {abs(memory_change):.2f} MB (garbage collection working)")
            # Allow up to 50MB decrease (aggressive garbage collection)
            assert memory_change > -50, f"Memory decrease too aggressive: {memory_change:.2f} MB"
