"""
Performance Benchmark Tests for Kakashi.

These tests measure and compare Kakashi's performance against
other logging libraries using pytest-benchmark.
"""

import pytest
import time
import threading
import asyncio
import psutil
import gc
from typing import Dict, Any
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestThroughputBenchmarks:
    """Test throughput performance benchmarks."""
    
    def test_sync_throughput_benchmark(self, benchmark, kakashi_sync_logger, comparison_loggers):
        """Benchmark sync logging throughput."""
        
        def kakashi_sync_logging():
            for i in range(1000):
                kakashi_sync_logger.info(f"Benchmark message {i}")
        
        def std_lib_logging():
            logger = comparison_loggers.get("standard_library")
            if logger:
                for i in range(1000):
                    logger.info(f"Benchmark message {i}")
        
        def loguru_logging():
            logger = comparison_loggers.get("loguru")
            if logger:
                for i in range(1000):
                    logger.info(f"Benchmark message {i}")
        
        def structlog_logging():
            logger = comparison_loggers.get("structlog")
            if logger:
                for i in range(1000):
                    logger.info(f"Benchmark message {i}")
        
        # Run benchmarks
        kakashi_result = benchmark(kakashi_sync_logging)
        
        if "standard_library" in comparison_loggers:
            std_result = benchmark(std_lib_logging)
            print(f"\nKakashi vs Standard Library:")
            print(f"  Kakashi: {kakashi_result.stats.mean:.6f}s")
            print(f"  StdLib:   {std_result.stats.mean:.6f}s")
            print(f"  Speedup:  {std_result.stats.mean / kakashi_result.stats.mean:.2f}x")
        
        if "loguru" in comparison_loggers:
            loguru_result = benchmark(loguru_logging)
            print(f"\nKakashi vs Loguru:")
            print(f"  Kakashi: {kakashi_result.stats.mean:.6f}s")
            print(f"  Loguru:  {loguru_result.stats.mean:.6f}s")
            print(f"  Speedup: {loguru_result.stats.mean / kakashi_result.stats.mean:.2f}x")
        
        if "structlog" in comparison_loggers:
            structlog_result = benchmark(structlog_logging)
            print(f"\nKakashi vs Structlog:")
            print(f"  Kakashi:  {kakashi_result.stats.mean:.6f}s")
            print(f"  Structlog: {structlog_result.stats.mean:.6f}s")
            print(f"  Speedup:   {structlog_result.stats.mean / kakashi_result.stats.mean:.2f}x")
    
    def test_async_throughput_benchmark(self, benchmark, kakashi_async_logger):
        """Benchmark async logging throughput."""
        
        async def kakashi_async_logging():
            tasks = []
            for i in range(1000):
                task = kakashi_async_logger.info(f"Async benchmark message {i}")
                tasks.append(task)
            await asyncio.gather(*tasks)
        
        def run_async_benchmark():
            asyncio.run(kakashi_async_logging())
        
        result = benchmark(run_async_benchmark)
        print(f"\nKakashi Async Throughput: {result.stats.mean:.6f}s")
    
    def test_structured_logging_benchmark(self, benchmark, kakashi_structured_logger):
        """Benchmark structured logging performance."""
        
        def structured_logging():
            for i in range(1000):
                kakashi_structured_logger.info(
                    "Structured message",
                    user_id=i,
                    action="benchmark",
                    timestamp=time.time(),
                    metadata={"test": True, "iteration": i}
                )
        
        result = benchmark(structured_logging)
        print(f"\nKakashi Structured Logging: {result.stats.mean:.6f}s")

class TestConcurrencyBenchmarks:
    """Test concurrency performance benchmarks."""
    
    def test_concurrent_threading_benchmark(self, benchmark, kakashi_sync_logger):
        """Benchmark concurrent threading performance."""
        
        def concurrent_logging(thread_count: int):
            def log_messages():
                for i in range(100):
                    kakashi_sync_logger.info(f"Thread message {i}")
            
            threads = []
            for _ in range(thread_count):
                thread = threading.Thread(target=log_messages)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
        
        # Test different thread counts
        for thread_count in [1, 2, 4, 8]:
            def run_concurrent():
                concurrent_logging(thread_count)
            
            result = benchmark(run_concurrent)
            print(f"\nConcurrent Logging ({thread_count} threads): {result.stats.mean:.6f}s")
    
    def test_concurrent_async_benchmark(self, benchmark, kakashi_async_logger):
        """Benchmark concurrent async performance."""
        
        async def concurrent_async_logging(task_count: int):
            async def log_messages():
                for i in range(100):
                    await kakashi_async_logger.info(f"Async task message {i}")
            
            tasks = [log_messages() for _ in range(task_count)]
            await asyncio.gather(*tasks)
        
        # Test different task counts
        for task_count in [1, 2, 4, 8]:
            def run_concurrent_async():
                asyncio.run(concurrent_async_logging(task_count))
            
            result = benchmark(run_concurrent_async)
            print(f"\nConcurrent Async Logging ({task_count} tasks): {result.stats.mean:.6f}s")

class TestMemoryBenchmarks:
    """Test memory usage benchmarks."""
    
    def test_memory_usage_benchmark(self, kakashi_sync_logger):
        """Benchmark memory usage during logging."""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Get baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Log many messages
        for i in range(10000):
            kakashi_sync_logger.info(f"Memory test message {i}")
        
        # Force garbage collection
        gc.collect()
        
        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_change = final_memory - baseline_memory
        
        print(f"\nMemory Usage Benchmark:")
        print(f"  Baseline memory: {baseline_memory:.2f} MB")
        print(f"  Final memory: {final_memory:.2f} MB")
        print(f"  Memory change: {memory_change:+.2f} MB")
        
        # Assertions - handle both positive and negative memory changes
        if memory_change > 0:
            # Memory increased - check it's reasonable
            assert memory_change < 100, f"Memory increase too high: {memory_change:.2f} MB"
        else:
            # Memory decreased (garbage collection freed memory) - this is good
            print(f"  ✅ Memory decreased by {abs(memory_change):.2f} MB (garbage collection working)")
            # Allow up to 50MB decrease (very aggressive garbage collection)
            assert memory_change > -50, f"Memory decrease too aggressive: {memory_change:.2f} MB"
    
    def test_memory_pressure_test(self, kakashi_sync_logger):
        """Test memory behavior under pressure."""
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
        assert abs(recovery_change) < 20, f"Memory not recovered to baseline: {recovery_change:+.2f} MB"

class TestLatencyBenchmarks:
    """Test latency benchmarks."""
    
    def test_single_message_latency(self, benchmark, kakashi_sync_logger):
        """Benchmark single message latency."""
        
        def single_message():
            kakashi_sync_logger.info("Single message test")
        
        result = benchmark(single_message)
        print(f"\nSingle Message Latency: {result.stats.mean * 1000:.3f} ms")
    
    def test_batch_latency_benchmark(self, benchmark, kakashi_sync_logger):
        """Benchmark batch message latency."""
        
        def batch_messages():
            for i in range(100):
                kakashi_sync_logger.info(f"Batch message {i}")
        
        result = benchmark(batch_messages)
        avg_latency = result.stats.mean / 100 * 1000  # ms per message
        print(f"\nBatch Message Latency: {avg_latency:.3f} ms per message")

class TestScalabilityBenchmarks:
    """Test scalability benchmarks."""
    
    def test_message_count_scalability(self, benchmark, kakashi_sync_logger):
        """Test how performance scales with message count."""
        
        for message_count in [100, 1000, 10000]:
            def log_messages():
                for i in range(message_count):
                    kakashi_sync_logger.info(f"Scalability test message {i}")
            
            result = benchmark(log_messages)
            throughput = message_count / result.stats.mean
            print(f"\nScalability ({message_count} messages):")
            print(f"  Time:      {result.stats.mean:.6f}s")
            print(f"  Throughput: {throughput:.0f} msg/s")
    
    def test_concurrency_scalability(self, benchmark, kakashi_sync_logger):
        """Test how performance scales with concurrency."""
        
        for thread_count in [1, 2, 4, 8, 16]:
            def concurrent_logging():
                def log_messages():
                    for i in range(50):
                        kakashi_sync_logger.info(f"Concurrency test message {i}")
                
                threads = []
                for _ in range(thread_count):
                    thread = threading.Thread(target=log_messages)
                    threads.append(thread)
                    thread.start()
                
                for thread in threads:
                    thread.join()
            
            result = benchmark(concurrent_logging)
            total_messages = thread_count * 50
            throughput = total_messages / result.stats.mean
            print(f"\nConcurrency Scalability ({thread_count} threads):")
            print(f"  Time:      {result.stats.mean:.6f}s")
            print(f"  Throughput: {throughput:.0f} msg/s")
            print(f"  Efficiency: {throughput / thread_count:.0f} msg/s/thread")
