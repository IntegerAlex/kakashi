"""
High-performance asynchronous logging backend.

This module implements a non-blocking I/O system where logger calls return immediately
after placing messages in a queue, while dedicated worker threads handle all I/O
operations. This completely eliminates I/O latency from the hot path.

Key benefits:
- Logger calls return in microseconds instead of milliseconds
- Application performance unaffected by slow I/O (disk, network)
- Automatic batching for optimal throughput
- Graceful shutdown ensures no message loss
- Multiple worker threads for high-volume scenarios
"""

import queue
import threading
import time
import atexit
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import sys

from .records import LogRecord
from .pipeline import Writer


class AsyncBackendState(Enum):
    """States of the async backend."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


@dataclass
class AsyncConfig:
    """Configuration for asynchronous logging backend."""
    # Queue settings
    max_queue_size: int = 10000  # Maximum messages in queue before blocking/dropping
    queue_overflow_strategy: str = "block"  # "block", "drop_oldest", "drop_newest"
    
    # Worker thread settings
    worker_count: int = 1  # Number of worker threads
    batch_size: int = 100  # Messages to process in one batch
    batch_timeout: float = 0.1  # Max seconds to wait for batch to fill
    
    # Shutdown settings
    shutdown_timeout: float = 5.0  # Max seconds to wait for graceful shutdown
    
    # Error handling
    max_error_retries: int = 3  # Max retries for failed writes
    error_retry_delay: float = 0.1  # Delay between retries
    
    # Performance tuning
    enable_batching: bool = True  # Enable message batching for efficiency
    thread_name_prefix: str = "AsyncLogger"  # Prefix for worker thread names


class QueueMessage:
    """Message in the async queue."""
    
    __slots__ = ('record', 'writer', 'formatted_message', 'retry_count', 'timestamp')
    
    def __init__(
        self, 
        record: LogRecord, 
        writer: Writer, 
        formatted_message: str,
        retry_count: int = 0
    ):
        self.record = record
        self.writer = writer
        self.formatted_message = formatted_message
        self.retry_count = retry_count
        self.timestamp = time.time()


class AsyncWriter:
    """
    Asynchronous wrapper for synchronous writers.
    
    This class wraps any synchronous writer and makes it asynchronous by
    enqueuing write requests instead of performing them immediately.
    """
    
    def __init__(self, sync_writer: Writer, backend: 'AsyncBackend'):
        """
        Initialize async writer.
        
        Args:
            sync_writer: The synchronous writer to wrap
            backend: The async backend to use for queueing
        """
        self.sync_writer = sync_writer
        self.backend = backend
        self._writer_id = id(sync_writer)  # Unique identifier
    
    def __call__(self, formatted_message: str, record: Optional[LogRecord] = None) -> None:
        """
        Asynchronously write a formatted message.
        
        This method returns immediately after enqueuing the message.
        The actual I/O is performed by worker threads.
        
        Args:
            formatted_message: The formatted log message
            record: Optional LogRecord for additional context
        """
        if not self.backend.is_running():
            # Fallback to synchronous write if backend is not running
            try:
                self.sync_writer(formatted_message)
            except Exception:
                # Silently ignore errors if async backend is stopped
                pass
            return
        
        # Create queue message
        message = QueueMessage(record, self.sync_writer, formatted_message)
        
        # Enqueue message (this should be very fast)
        try:
            self.backend.enqueue(message)
        except queue.Full:
            # Handle queue overflow based on strategy
            self.backend._handle_queue_overflow(message)
        except Exception:
            # Last resort: try synchronous write
            try:
                self.sync_writer(formatted_message)
            except Exception:
                pass  # Silently ignore to prevent crashes


class WorkerThread(threading.Thread):
    """
    Worker thread that processes queued log messages.
    
    This thread continuously pulls messages from the queue and
    writes them using the original synchronous writers.
    """
    
    def __init__(self, backend: 'AsyncBackend', worker_id: int):
        """
        Initialize worker thread.
        
        Args:
            backend: The async backend this worker belongs to
            worker_id: Unique identifier for this worker
        """
        super().__init__(
            name=f"{backend.config.thread_name_prefix}-{worker_id}",
            daemon=True  # Daemon thread won't prevent program exit
        )
        self.backend = backend
        self.worker_id = worker_id
        self._stop_event = threading.Event()
        
    def stop(self) -> None:
        """Signal the worker thread to stop."""
        self._stop_event.set()
    
    def run(self) -> None:
        """Main worker thread loop."""
        config = self.backend.config
        
        while not self._stop_event.is_set():
            try:
                if config.enable_batching:
                    self._process_batch()
                else:
                    self._process_single()
            except (OSError, ValueError, queue.Empty, queue.Full) as e:
                # Log worker errors to stderr (avoid recursion)
                try:
                    print(f"AsyncLogger worker {self.worker_id} error: {e}", file=sys.stderr)
                except (OSError, UnicodeError):
                    pass  # Even stderr logging failed
                time.sleep(0.1)  # Brief pause before continuing
        
        # Process remaining messages during shutdown
        self._drain_queue()
    
    def _process_single(self) -> None:
        """Process a single message from the queue."""
        try:
            message = self.backend.queue.get(timeout=0.1)
            self._write_message(message)
            self.backend.queue.task_done()
        except queue.Empty:
            pass  # No message available, continue loop
    
    def _process_batch(self) -> None:
        """Process a batch of messages for better efficiency."""
        config = self.backend.config
        batch = []
        batch_start = time.time()
        
        # Collect messages for batch
        while (len(batch) < config.batch_size and 
               time.time() - batch_start < config.batch_timeout):
            try:
                message = self.backend.queue.get(timeout=0.01)
                batch.append(message)
            except queue.Empty:
                if batch:
                    break  # Process what we have
                # No messages and no batch, wait a bit longer
                if time.time() - batch_start < config.batch_timeout:
                    continue
                else:
                    break
        
        # Process the batch
        if batch:
            self._write_batch(batch)
            # Mark all messages as done
            for _ in batch:
                self.backend.queue.task_done()
    
    def _write_message(self, message: QueueMessage) -> None:
        """Write a single message, with retry logic."""
        config = self.backend.config
        
        try:
            message.writer(message.formatted_message)
        except Exception as e:
            # Handle write errors with retry logic
            if message.retry_count < config.max_error_retries:
                message.retry_count += 1
                time.sleep(config.error_retry_delay)
                # Re-enqueue for retry
                try:
                    self.backend.queue.put_nowait(message)
                except queue.Full:
                    # If queue is full, drop the message to prevent infinite loops
                    print(f"AsyncLogger: Dropping message after retry failure: {e}", file=sys.stderr)
            else:
                # Max retries exceeded, log error and drop message
                print(f"AsyncLogger: Max retries exceeded, dropping message: {e}", file=sys.stderr)
    
    def _write_batch(self, batch: List[QueueMessage]) -> None:
        """Write a batch of messages, grouping by writer for efficiency."""
        # Group messages by writer for batching efficiency
        writer_batches: Dict[int, List[QueueMessage]] = {}
        
        for message in batch:
            writer_id = id(message.writer)
            if writer_id not in writer_batches:
                writer_batches[writer_id] = []
            writer_batches[writer_id].append(message)
        
        # Process each writer's batch
        for writer_messages in writer_batches.values():
            for message in writer_messages:
                self._write_message(message)
    
    def _drain_queue(self) -> None:
        """Drain remaining messages from queue during shutdown."""
        try:
            while True:
                message = self.backend.queue.get_nowait()
                self._write_message(message)
                self.backend.queue.task_done()
        except queue.Empty:
            pass  # Queue is empty


class AsyncBackend:
    """
    High-performance asynchronous logging backend.
    
    This class manages the message queue and worker threads that handle
    all I/O operations asynchronously. Logger calls return immediately
    after enqueuing messages.
    """
    
    def __init__(self, config: Optional[AsyncConfig] = None):
        """
        Initialize async backend.
        
        Args:
            config: Configuration for async behavior
        """
        self.config = config or AsyncConfig()
        self.queue: queue.Queue = queue.Queue(maxsize=self.config.max_queue_size)
        self.workers: List[WorkerThread] = []
        self.state = AsyncBackendState.STOPPED
        self._lock = threading.RLock()
        
        # Statistics
        self.messages_enqueued = 0
        self.messages_dropped = 0
        self.messages_written = 0
        
        # Register cleanup on exit
        atexit.register(self.shutdown)
    
    def start(self) -> None:
        """Start the async backend and worker threads."""
        with self._lock:
            if self.state != AsyncBackendState.STOPPED:
                return  # Already started or starting
            
            self.state = AsyncBackendState.STARTING
            
            # Create and start worker threads
            for i in range(self.config.worker_count):
                worker = WorkerThread(self, i)
                self.workers.append(worker)
                worker.start()
            
            self.state = AsyncBackendState.RUNNING
    
    def stop(self) -> None:
        """Stop worker threads gracefully."""
        with self._lock:
            if self.state != AsyncBackendState.RUNNING:
                return  # Not running
            
            self.state = AsyncBackendState.STOPPING
            
            # Signal all workers to stop
            for worker in self.workers:
                worker.stop()
    
    def shutdown(self, timeout: Optional[float] = None) -> None:
        """
        Shutdown the async backend gracefully.
        
        Args:
            timeout: Maximum time to wait for shutdown (uses config default if None)
        """
        if timeout is None:
            timeout = self.config.shutdown_timeout
        
        self.stop()
        
        # Wait for all workers to finish
        for worker in self.workers:
            worker.join(timeout=timeout)
        
        # Wait for queue to be empty with timeout
        try:
            # Use timeout to avoid hanging indefinitely
            start_time = time.time()
            while not self.queue.empty() and time.time() - start_time < timeout:
                time.sleep(0.1)
        except (OSError, ValueError, RuntimeError):
            pass  # Ignore errors during shutdown
        
        self.state = AsyncBackendState.STOPPED
        self.workers.clear()
    
    def is_running(self) -> bool:
        """Check if the backend is running."""
        return self.state == AsyncBackendState.RUNNING
    
    def enqueue(self, message: QueueMessage) -> None:
        """
        Enqueue a message for asynchronous processing.
        
        Args:
            message: The message to enqueue
            
        Raises:
            queue.Full: If the queue is full and blocking strategy is used
        """
        if not self.is_running():
            self.start()  # Auto-start if not running
        
        self.queue.put(message, block=True, timeout=0.001)  # Very short timeout
        self.messages_enqueued += 1
    
    def _handle_queue_overflow(self, message: QueueMessage) -> None:
        """Handle queue overflow based on configured strategy."""
        strategy = self.config.queue_overflow_strategy
        
        if strategy == "block":
            # Block until space is available (default behavior)
            try:
                self.queue.put(message, block=True, timeout=1.0)
                self.messages_enqueued += 1
            except queue.Full:
                self.messages_dropped += 1
        
        elif strategy == "drop_oldest":
            # Drop oldest message to make room
            try:
                self.queue.get_nowait()  # Remove oldest
                self.queue.put_nowait(message)  # Add new
                self.messages_enqueued += 1
                self.messages_dropped += 1
            except (queue.Empty, queue.Full):
                self.messages_dropped += 1
        
        elif strategy == "drop_newest":
            # Drop the new message
            self.messages_dropped += 1
        
        else:
            # Unknown strategy, drop message
            self.messages_dropped += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get runtime statistics."""
        return {
            'state': self.state.value,
            'queue_size': self.queue.qsize(),
            'max_queue_size': self.config.max_queue_size,
            'worker_count': len(self.workers),
            'messages_enqueued': self.messages_enqueued,
            'messages_dropped': self.messages_dropped,
            'messages_written': self.messages_written,
            'active_workers': sum(1 for w in self.workers if w.is_alive()),
        }


# Global async backend instance
_global_async_backend: Optional[AsyncBackend] = None
_backend_lock = threading.RLock()


def get_async_backend(config: Optional[AsyncConfig] = None) -> AsyncBackend:
    """
    Get the global async backend instance.
    
    Args:
        config: Configuration for the backend (only used on first call)
        
    Returns:
        The global AsyncBackend instance
    """
    global _global_async_backend
    
    with _backend_lock:
        if _global_async_backend is None:
            _global_async_backend = AsyncBackend(config)
        return _global_async_backend


def set_async_backend(backend: AsyncBackend) -> None:
    """
    Set a custom async backend instance.
    
    Args:
        backend: The AsyncBackend instance to use globally
    """
    global _global_async_backend
    
    with _backend_lock:
        if _global_async_backend is not None:
            _global_async_backend.shutdown()
        _global_async_backend = backend


def create_async_writer(sync_writer: Writer, backend: Optional[AsyncBackend] = None) -> AsyncWriter:
    """
    Create an async wrapper for a synchronous writer.
    
    Args:
        sync_writer: The synchronous writer to wrap
        backend: Optional custom backend (uses global backend if None)
        
    Returns:
        AsyncWriter that performs non-blocking writes
    """
    if backend is None:
        backend = get_async_backend()
    
    return AsyncWriter(sync_writer, backend)


def shutdown_async_logging(timeout: float = 5.0) -> None:
    """
    Shutdown the global async logging backend gracefully.
    
    Args:
        timeout: Maximum time to wait for shutdown
    """
    global _global_async_backend
    
    with _backend_lock:
        if _global_async_backend is not None:
            _global_async_backend.shutdown(timeout)
            _global_async_backend = None
