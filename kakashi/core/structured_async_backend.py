"""
High-performance async backend optimized for structured logging.

This module extends the async logging backend to handle deferred JSON serialization,
moving expensive operations to worker threads while keeping the main logging calls
as fast as possible.

Key optimizations:
- Deferred JSON serialization in worker threads
- Structured data pipeline optimization
- Zero-copy when possible
- Batch serialization for efficiency
- orjson integration for maximum performance
"""

import time
import queue
import threading
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from .async_backend import AsyncConfig, WorkerThread, AsyncBackend
from .structured_logger import StructuredLogEntry
from .records import LogRecord, LogLevel
from .sinks import Sink, SinkResult


class SerializationMode(Enum):
    """Serialization mode for structured logging."""
    DEFERRED = "deferred"  # Serialize in worker thread
    IMMEDIATE = "immediate"  # Serialize immediately
    BATCH = "batch"  # Batch serialize multiple entries


@dataclass
class StructuredLogMessage:
    """
    Structured log message for async processing.
    
    This message contains the raw structured data that will be
    serialized in the worker thread, minimizing main thread overhead.
    """
    entry: StructuredLogEntry
    sink_name: str
    serialization_mode: SerializationMode = SerializationMode.DEFERRED
    
    # Pre-serialized data (for immediate mode)
    pre_serialized: Optional[str] = None
    
    def __post_init__(self):
        """Auto-serialize if in immediate mode."""
        if self.serialization_mode == SerializationMode.IMMEDIATE:
            self.pre_serialized = self.entry.to_json_str()


class StructuredWorkerThread(WorkerThread):
    """
    Worker thread optimized for structured logging.
    
    This worker thread handles deferred JSON serialization and
    batch processing of structured log entries.
    """
    
    def __init__(
        self,
        thread_id: int,
        message_queue: queue.Queue,
        sink_registry: Dict[str, Sink],
        batch_size: int = 100,
        batch_timeout: float = 0.1,
        enable_batching: bool = True
    ):
        """
        Initialize structured worker thread.
        
        Args:
            thread_id: Unique thread identifier
            message_queue: Queue to receive messages from
            sink_registry: Registry of available sinks
            batch_size: Number of entries to batch together
            batch_timeout: Maximum time to wait for batch completion
            enable_batching: Whether to enable batch processing
        """
        super().__init__(thread_id, message_queue, sink_registry)
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.enable_batching = enable_batching
        
        # Batch processing state
        self.current_batch: List[StructuredLogMessage] = []
        self.last_batch_time = time.time()
        
        # Performance counters
        self.entries_serialized = 0
        self.batches_processed = 0
        self.serialization_time = 0.0
    
    def run(self) -> None:
        """
        Main worker thread loop with structured logging optimizations.
        """
        while not self.shutdown_event.is_set():
            try:
                # Process messages with timeout to allow batch flushing
                timeout = min(self.batch_timeout, 0.1)
                
                try:
                    message = self.message_queue.get(timeout=timeout)
                    
                    if message is None:  # Shutdown signal
                        break
                    
                    if isinstance(message, StructuredLogMessage):
                        self._process_structured_message(message)
                    else:
                        # Fallback for regular messages
                        self._process_regular_message(message)
                        
                    self.messages_processed += 1
                    
                except queue.Empty:
                    # Timeout - check if we need to flush batch
                    if self.enable_batching and self.current_batch:
                        current_time = time.time()
                        if current_time - self.last_batch_time >= self.batch_timeout:
                            self._flush_batch()
                
            except Exception:
                self.errors += 1
        
        # Flush any remaining batch on shutdown
        if self.current_batch:
            self._flush_batch()
    
    def _process_structured_message(self, message: StructuredLogMessage) -> None:
        """
        Process a structured log message with optimizations.
        
        Args:
            message: Structured log message to process
        """
        if self.enable_batching and message.serialization_mode == SerializationMode.BATCH:
            # Add to batch for processing
            self.current_batch.append(message)
            
            # Flush batch if full or timeout reached
            if len(self.current_batch) >= self.batch_size:
                self._flush_batch()
            
        else:
            # Process immediately
            self._process_single_structured_message(message)
    
    def _process_single_structured_message(self, message: StructuredLogMessage) -> None:
        """
        Process a single structured message.
        
        Args:
            message: Structured message to process
        """
        sink = self.sink_registry.get(message.sink_name)
        if not sink:
            self.errors += 1
            return
        
        try:
            # Serialize if needed (deferred serialization)
            if message.pre_serialized:
                serialized_data = message.pre_serialized
            else:
                start_time = time.time()
                serialized_data = message.entry.to_json_str()
                self.serialization_time += time.time() - start_time
                self.entries_serialized += 1
            
            # Convert to LogRecord for sink compatibility
            log_record = LogRecord(
                timestamp=message.entry.timestamp,
                level=LogLevel[message.entry.level],
                message=message.entry.message,
                fields=message.entry.fields,
                logger_name=message.sink_name
            )
            
            # Write to sink
            result = sink.write(serialized_data, log_record)
            
            if result != SinkResult.SUCCESS:
                self.errors += 1
            
        except Exception:
            self.errors += 1
    
    def _flush_batch(self) -> None:
        """
        Flush the current batch of structured messages.
        
        This method serializes multiple entries together for efficiency.
        """
        if not self.current_batch:
            return
        
        start_time = time.time()
        
        try:
            # Group messages by sink for efficient processing
            sink_batches: Dict[str, List[StructuredLogMessage]] = {}
            for message in self.current_batch:
                if message.sink_name not in sink_batches:
                    sink_batches[message.sink_name] = []
                sink_batches[message.sink_name].append(message)
            
            # Process each sink's batch
            for sink_name, messages in sink_batches.items():
                sink = self.sink_registry.get(sink_name)
                if not sink:
                    self.errors += len(messages)
                    continue
                
                # Batch serialize entries
                serialized_entries = []
                for message in messages:
                    if message.pre_serialized:
                        serialized_entries.append(message.pre_serialized)
                    else:
                        serialized_entries.append(message.entry.to_json_str())
                        self.entries_serialized += 1
                
                # Send batch to sink (one entry at a time for now)
                # Future optimization: implement batch write in sinks
                for i, message in enumerate(messages):
                    try:
                        log_record = LogRecord(
                            timestamp=message.entry.timestamp,
                            level=LogLevel[message.entry.level],
                            message=message.entry.message,
                            fields=message.entry.fields,
                            logger_name=sink_name
                        )
                        
                        result = sink.write(serialized_entries[i], log_record)
                        if result != SinkResult.SUCCESS:
                            self.errors += 1
                            
                    except Exception:
                        self.errors += 1
            
            # Update batch stats
            self.batches_processed += 1
            self.serialization_time += time.time() - start_time
            
        finally:
            # Clear batch and update timing
            self.current_batch.clear()
            self.last_batch_time = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker thread statistics including serialization metrics."""
        base_stats = super().get_stats()
        base_stats.update({
            'entries_serialized': self.entries_serialized,
            'batches_processed': self.batches_processed,
            'serialization_time': self.serialization_time,
            'current_batch_size': len(self.current_batch),
            'avg_serialization_time': (
                self.serialization_time / max(1, self.entries_serialized)
            ),
        })
        return base_stats


class StructuredAsyncBackend(AsyncBackend):
    """
    Async backend optimized for structured logging.
    
    This backend provides deferred JSON serialization and specialized
    handling for structured log entries.
    """
    
    def __init__(self, config: AsyncConfig):
        """Initialize structured async backend."""
        super().__init__(config)
        
        # Override worker threads with structured versions
        self.worker_threads = []
        for i in range(config.worker_count):
            worker = StructuredWorkerThread(
                thread_id=i,
                message_queue=self.message_queue,
                sink_registry=self.sink_registry,
                batch_size=config.batch_size,
                batch_timeout=config.batch_timeout,
                enable_batching=config.enable_batching
            )
            self.worker_threads.append(worker)
            worker.start()
    
    def enqueue_structured_entry(
        self,
        entry: StructuredLogEntry,
        sink_name: str,
        serialization_mode: SerializationMode = SerializationMode.DEFERRED
    ) -> bool:
        """
        Enqueue a structured log entry for async processing.
        
        Args:
            entry: Structured log entry
            sink_name: Name of the sink to write to
            serialization_mode: How to handle serialization
        
        Returns:
            True if successfully enqueued, False otherwise
        """
        try:
            message = StructuredLogMessage(
                entry=entry,
                sink_name=sink_name,
                serialization_mode=serialization_mode
            )
            
            # Try to enqueue with timeout
            self.message_queue.put(message, timeout=0.001)
            
            with self._stats_lock:
                self.total_messages += 1
            
            return True
            
        except queue.Full:
            # Handle queue overflow based on strategy
            if self.config.queue_overflow_strategy == "drop_oldest":
                try:
                    self.message_queue.get_nowait()  # Drop oldest
                    self.message_queue.put(message, timeout=0.001)
                    
                    with self._stats_lock:
                        self.dropped_messages += 1
                        self.total_messages += 1
                    
                    return True
                except (queue.Empty, queue.Full):
                    pass
            
            with self._stats_lock:
                self.dropped_messages += 1
            
            return False
        
        except Exception:
            with self._stats_lock:
                self.errors += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics including structured logging metrics."""
        base_stats = super().get_stats()
        
        # Add structured-specific stats from worker threads
        total_entries_serialized = 0
        total_batches_processed = 0
        total_serialization_time = 0.0
        
        for worker in self.worker_threads:
            if isinstance(worker, StructuredWorkerThread):
                worker_stats = worker.get_stats()
                total_entries_serialized += worker_stats.get('entries_serialized', 0)
                total_batches_processed += worker_stats.get('batches_processed', 0)
                total_serialization_time += worker_stats.get('serialization_time', 0.0)
        
        base_stats.update({
            'total_entries_serialized': total_entries_serialized,
            'total_batches_processed': total_batches_processed,
            'total_serialization_time': total_serialization_time,
            'avg_serialization_time_per_entry': (
                total_serialization_time / max(1, total_entries_serialized)
            ),
        })
        
        return base_stats


# ============================================================================
# STRUCTURED ASYNC WRITER
# ============================================================================

class StructuredAsyncWriter:
    """
    Writer that sends structured entries to async backend.
    
    This writer integrates with the sink pipeline to provide
    high-performance async structured logging.
    """
    
    def __init__(
        self,
        backend: StructuredAsyncBackend,
        sink_name: str,
        serialization_mode: SerializationMode = SerializationMode.DEFERRED
    ):
        """
        Initialize structured async writer.
        
        Args:
            backend: Structured async backend
            sink_name: Name of target sink
            serialization_mode: Serialization strategy
        """
        self.backend = backend
        self.sink_name = sink_name
        self.serialization_mode = serialization_mode
        
        # Performance counters
        self.entries_sent = 0
        self.entries_dropped = 0
    
    def write_entry(self, entry: StructuredLogEntry) -> bool:
        """
        Write a structured entry to the async backend.
        
        Args:
            entry: Structured log entry to write
        
        Returns:
            True if successfully queued, False if dropped
        """
        success = self.backend.enqueue_structured_entry(
            entry, self.sink_name, self.serialization_mode
        )
        
        if success:
            self.entries_sent += 1
        else:
            self.entries_dropped += 1
        
        return success
    
    def get_stats(self) -> Dict[str, Any]:
        """Get writer statistics."""
        return {
            'sink_name': self.sink_name,
            'serialization_mode': self.serialization_mode.value,
            'entries_sent': self.entries_sent,
            'entries_dropped': self.entries_dropped,
            'drop_rate': self.entries_dropped / max(1, self.entries_sent + self.entries_dropped)
        }


# ============================================================================
# GLOBAL BACKEND MANAGEMENT
# ============================================================================

_global_structured_backend: Optional[StructuredAsyncBackend] = None
_backend_lock = threading.Lock()


def get_structured_async_backend() -> Optional[StructuredAsyncBackend]:
    """Get the global structured async backend."""
    return _global_structured_backend


def setup_structured_async_backend(config: AsyncConfig) -> StructuredAsyncBackend:
    """
    Set up the global structured async backend.
    
    Args:
        config: Async configuration
    
    Returns:
        Configured structured async backend
    """
    global _global_structured_backend
    
    with _backend_lock:
        if _global_structured_backend:
            _global_structured_backend.shutdown()
        
        _global_structured_backend = StructuredAsyncBackend(config)
        return _global_structured_backend


def shutdown_structured_async_backend() -> None:
    """Shutdown the global structured async backend."""
    global _global_structured_backend
    
    with _backend_lock:
        if _global_structured_backend:
            _global_structured_backend.shutdown()
            _global_structured_backend = None


def get_structured_async_stats() -> Dict[str, Any]:
    """Get structured async backend statistics."""
    backend = get_structured_async_backend()
    if backend:
        return backend.get_stats()
    return {}
