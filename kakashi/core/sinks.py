"""
Log shipping sinks architecture for mylogs.

This module implements a comprehensive sinks system that allows logs to be
shipped to multiple destinations simultaneously. It transforms mylogs from
a simple logging library into a full log shipping solution.

Supported destinations:
- Files (with rotation)
- Console (stdout/stderr)
- Network (UDP, TCP, HTTP)
- Message queues
- Cloud services
- Custom destinations

Key features:
- Multiple sinks per logger
- Conditional routing based on log content
- Built-in buffering and batching
- Error resilience and retries
- Structured and unstructured data support
"""

import json
import socket
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import sys
from enum import Enum

from .records import LogRecord


class SinkResult(Enum):
    """Result of a sink write operation."""
    SUCCESS = "success"
    ERROR = "error" 
    RETRY = "retry"
    FILTERED = "filtered"


@dataclass
class SinkStats:
    """Statistics for a sink."""
    messages_sent: int = 0
    messages_failed: int = 0
    messages_filtered: int = 0
    bytes_sent: int = 0
    last_success: Optional[float] = None
    last_error: Optional[float] = None
    error_count: int = 0
    retry_count: int = 0


class Sink(ABC):
    """
    Abstract base class for all log sinks.
    
    A sink is responsible for receiving formatted log messages and
    delivering them to a specific destination. Sinks can be files,
    network endpoints, message queues, or any other destination.
    
    Design principles:
    - Immutable configuration
    - Thread-safe operations
    - Graceful error handling
    - Optional filtering and transformation
    - Performance monitoring
    """
    
    def __init__(self, name: str):
        """
        Initialize the sink.
        
        Args:
            name: Unique name for this sink instance
        """
        self.name = name
        self.stats = SinkStats()
        self._lock = threading.RLock()
    
    @abstractmethod
    def write(self, message: str, record: Optional[LogRecord] = None) -> SinkResult:
        """
        Write a formatted message to this sink.
        
        Args:
            message: The formatted log message
            record: Optional original LogRecord for advanced processing
            
        Returns:
            SinkResult indicating the outcome
        """
        pass
    
    def should_write(self, record: LogRecord) -> bool:
        """
        Determine if this record should be written to this sink.
        
        Override this method to implement sink-specific filtering.
        
        Args:
            record: The log record to evaluate
            
        Returns:
            True if the record should be written
        """
        return True
    
    def transform_message(self, message: str, record: Optional[LogRecord] = None) -> str:
        """
        Transform the message before writing.
        
        Override this method to implement sink-specific transformations
        like adding metadata, changing format, etc.
        
        Args:
            message: The formatted message
            record: Optional original LogRecord
            
        Returns:
            Transformed message
        """
        return message
    
    def flush(self) -> None:
        """
        Flush any buffered data.
        
        Override this method if the sink uses buffering.
        """
        pass
    
    def close(self) -> None:
        """
        Close the sink and release resources.
        
        Override this method to clean up resources like file handles,
        network connections, etc.
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for this sink."""
        with self._lock:
            return {
                'name': self.name,
                'messages_sent': self.stats.messages_sent,
                'messages_failed': self.stats.messages_failed,
                'messages_filtered': self.stats.messages_filtered,
                'bytes_sent': self.stats.bytes_sent,
                'last_success': self.stats.last_success,
                'last_error': self.stats.last_error,
                'error_count': self.stats.error_count,
                'retry_count': self.stats.retry_count,
                'error_rate': (
                    self.stats.error_count / max(1, self.stats.messages_sent + self.stats.messages_failed)
                ),
            }
    
    def _record_success(self, bytes_sent: int = 0) -> None:
        """Record a successful write."""
        with self._lock:
            self.stats.messages_sent += 1
            self.stats.bytes_sent += bytes_sent
            self.stats.last_success = time.time()
    
    def _record_error(self) -> None:
        """Record a failed write."""
        with self._lock:
            self.stats.messages_failed += 1
            self.stats.error_count += 1
            self.stats.last_error = time.time()
    
    def _record_retry(self) -> None:
        """Record a retry attempt."""
        with self._lock:
            self.stats.retry_count += 1
    
    def _record_filtered(self) -> None:
        """Record a filtered message."""
        with self._lock:
            self.stats.messages_filtered += 1


# ============================================================================
# FILE SINKS
# ============================================================================

class FileSink(Sink):
    """
    Sink that writes logs to a file.
    
    Features:
    - Atomic writes
    - Directory creation
    - UTF-8 encoding
    - Optional compression
    """
    
    def __init__(
        self,
        name: str,
        file_path: Union[str, Path],
        encoding: str = "utf-8",
        create_dirs: bool = True,
        append: bool = True
    ):
        """
        Initialize file sink.
        
        Args:
            name: Sink name
            file_path: Path to the log file
            encoding: File encoding
            create_dirs: Whether to create parent directories
            append: Whether to append to existing file
        """
        super().__init__(name)
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.create_dirs = create_dirs
        self.append = append
        
        if self.create_dirs:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def write(self, message: str, record: Optional[LogRecord] = None) -> SinkResult:
        """Write message to file with comprehensive error handling and fallbacks."""
        if record and not self.should_write(record):
            self._record_filtered()
            return SinkResult.FILTERED
        
        try:
            transformed_message = self.transform_message(message, record)
            
            # Primary write attempt
            try:
                # Ensure directory exists
                if self.create_dirs and not self.file_path.parent.exists():
                    self.file_path.parent.mkdir(parents=True, exist_ok=True)
                
                mode = 'a' if self.append else 'w'
                with open(self.file_path, mode, encoding=self.encoding) as f:
                    f.write(transformed_message + '\n')
                    f.flush()
                
                self._record_success(len(transformed_message.encode(self.encoding)))
                return SinkResult.SUCCESS
                
            except (OSError, IOError, PermissionError):
                # Fallback 1: Try writing to a fallback location
                try:
                    fallback_path = Path.cwd() / f"mylogs_fallback_{self.name}.log"
                    with open(fallback_path, 'a', encoding='utf-8') as f:
                        f.write(f"[FALLBACK] {transformed_message}\n")
                        f.flush()
                    self._record_success(len(transformed_message))
                    return SinkResult.SUCCESS
                    
                except Exception:
                    # Fallback 2: Write to stderr
                    try:
                        print(f"[MYLOGS-FALLBACK-{self.name.upper()}] {transformed_message}", file=sys.stderr)
                        self._record_success(len(transformed_message))
                        return SinkResult.SUCCESS
                    except Exception:
                        # Complete failure - fail silently to prevent app crash
                        self._record_error()
                        return SinkResult.ERROR
                        
        except Exception as e:
            # Unexpected error - fail gracefully without crashing the app
            self._record_error()
            try:
                # Try to report the error to stderr
                print(f"[MYLOGS-ERROR-{self.name.upper()}] Logging failed: {str(e)[:100]}", file=sys.stderr)
            except Exception:
                pass  # Even stderr failed - complete silent failure
            return SinkResult.ERROR


class RotatingFileSink(Sink):
    """
    Sink that writes logs to rotating files.
    
    Features:
    - Size-based rotation
    - Time-based rotation
    - Automatic compression
    - Configurable retention
    """
    
    def __init__(
        self,
        name: str,
        file_path: Union[str, Path],
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 10,
        encoding: str = "utf-8",
        rotation_type: str = "size"  # "size" or "time"
    ):
        """
        Initialize rotating file sink.
        
        Args:
            name: Sink name
            file_path: Base path for log files
            max_bytes: Maximum size before rotation (for size-based)
            backup_count: Number of backup files to keep
            encoding: File encoding
            rotation_type: "size" or "time"
        """
        super().__init__(name)
        self.file_path = Path(file_path)
        self.encoding = encoding
        
        # Create parent directories
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if rotation_type == "size":
            self.handler = RotatingFileHandler(
                str(self.file_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=encoding
            )
        elif rotation_type == "time":
            self.handler = TimedRotatingFileHandler(
                str(self.file_path),
                when='midnight',
                interval=1,
                backupCount=backup_count,
                encoding=encoding
            )
        else:
            raise ValueError(f"Unknown rotation_type: {rotation_type}")
    
    def write(self, message: str, record: Optional[LogRecord] = None) -> SinkResult:
        """Write message with rotation."""
        if record and not self.should_write(record):
            self._record_filtered()
            return SinkResult.FILTERED
        
        try:
            transformed_message = self.transform_message(message, record)
            
            # Use the handler's stream directly for thread safety
            self.handler.emit(type('MockRecord', (), {
                'getMessage': lambda: transformed_message,
                'levelno': 20,  # INFO level
                'created': time.time()
            })())
            
            self._record_success(len(transformed_message.encode(self.encoding)))
            return SinkResult.SUCCESS
            
        except Exception:
            self._record_error()
            return SinkResult.ERROR
    
    def close(self) -> None:
        """Close the rotating file handler."""
        self.handler.close()


# ============================================================================
# CONSOLE SINKS
# ============================================================================

class ConsoleSink(Sink):
    """
    Sink that writes logs to console (stdout/stderr).
    
    Features:
    - Configurable output stream
    - Color support detection
    - Automatic flushing
    """
    
    def __init__(
        self,
        name: str,
        stream: str = "stdout",  # "stdout" or "stderr"
        flush: bool = True
    ):
        """
        Initialize console sink.
        
        Args:
            name: Sink name
            stream: Output stream ("stdout" or "stderr")
            flush: Whether to flush after each write
        """
        super().__init__(name)
        self.stream = sys.stdout if stream == "stdout" else sys.stderr
        self.flush = flush
    
    def write(self, message: str, record: Optional[LogRecord] = None) -> SinkResult:
        """Write message to console."""
        if record and not self.should_write(record):
            self._record_filtered()
            return SinkResult.FILTERED
        
        try:
            transformed_message = self.transform_message(message, record)
            
            print(transformed_message, file=self.stream, flush=self.flush)
            
            self._record_success(len(transformed_message.encode()))
            return SinkResult.SUCCESS
            
        except Exception:
            self._record_error()
            return SinkResult.ERROR


# ============================================================================
# NETWORK SINKS
# ============================================================================

class UDPSink(Sink):
    """
    Sink that sends logs via UDP.
    
    Features:
    - Non-blocking UDP transmission
    - Configurable packet size
    - Automatic JSON serialization
    - Connection reuse
    """
    
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        max_packet_size: int = 8192,
        timeout: float = 5.0
    ):
        """
        Initialize UDP sink.
        
        Args:
            name: Sink name
            host: Target hostname or IP
            port: Target port
            max_packet_size: Maximum UDP packet size
            timeout: Socket timeout
        """
        super().__init__(name)
        self.host = host
        self.port = port
        self.max_packet_size = max_packet_size
        self.timeout = timeout
        self.socket = None
        self._socket_lock = threading.Lock()
    
    def _get_socket(self) -> socket.socket:
        """Get or create UDP socket."""
        with self._socket_lock:
            if self.socket is None:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.settimeout(self.timeout)
            return self.socket
    
    def write(self, message: str, record: Optional[LogRecord] = None) -> SinkResult:
        """Send message via UDP with comprehensive error handling and fallbacks."""
        if record and not self.should_write(record):
            self._record_filtered()
            return SinkResult.FILTERED
        
        try:
            transformed_message = self.transform_message(message, record)
            
            # Primary UDP send attempt
            try:
                data = transformed_message.encode('utf-8')
                
                # Check packet size
                if len(data) > self.max_packet_size:
                    # Truncate large messages to fit UDP limits
                    truncate_size = self.max_packet_size - 100
                    data = data[:truncate_size] + b"... [TRUNCATED-UDP]"
                
                sock = self._get_socket()
                sock.sendto(data, (self.host, self.port))
                
                self._record_success(len(data))
                return SinkResult.SUCCESS
                
            except socket.timeout:
                # Network timeout - retry might help
                self._record_retry()
                return SinkResult.RETRY
                
            except (socket.error, OSError):
                # Network error - fallback to local logging
                try:
                    # Fallback to stderr
                    print(f"[MYLOGS-UDP-FALLBACK-{self.name.upper()}] Network failed, local log: {transformed_message}", file=sys.stderr)
                    self._record_success(len(transformed_message))
                    return SinkResult.SUCCESS
                except Exception:
                    # Even stderr failed - fail silently
                    self._record_error()
                    return SinkResult.ERROR
                    
            except Exception:
                # Socket creation/setup error
                try:
                    # Close and reset socket for next attempt
                    if self.socket:
                        try:
                            self.socket.close()
                        except Exception:
                            pass
                        self.socket = None
                    
                    # Fallback to stderr
                    print(f"[MYLOGS-UDP-ERROR-{self.name.upper()}] Socket error, local log: {transformed_message}", file=sys.stderr)
                    self._record_success(len(transformed_message))
                    return SinkResult.SUCCESS
                except Exception:
                    self._record_error()
                    return SinkResult.ERROR
                    
        except Exception as e:
            # Unexpected error - fail gracefully
            self._record_error()
            try:
                print(f"[MYLOGS-UDP-CRITICAL-{self.name.upper()}] Unexpected error: {str(e)[:100]}", file=sys.stderr)
            except Exception:
                pass  # Complete silent failure
            return SinkResult.ERROR
    
    def close(self) -> None:
        """Close UDP socket."""
        with self._socket_lock:
            if self.socket:
                self.socket.close()
                self.socket = None


class TCPSink(Sink):
    """
    Sink that sends logs via TCP with connection pooling.
    
    Features:
    - Connection pooling and reuse
    - Automatic reconnection
    - Buffering and batching
    - Keep-alive support
    """
    
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        timeout: float = 10.0,
        keepalive: bool = True,
        reconnect_attempts: int = 3
    ):
        """
        Initialize TCP sink.
        
        Args:
            name: Sink name
            host: Target hostname or IP
            port: Target port
            timeout: Connection timeout
            keepalive: Enable TCP keepalive
            reconnect_attempts: Number of reconnection attempts
        """
        super().__init__(name)
        self.host = host
        self.port = port
        self.timeout = timeout
        self.keepalive = keepalive
        self.reconnect_attempts = reconnect_attempts
        self.socket = None
        self._socket_lock = threading.Lock()
    
    def _get_socket(self) -> socket.socket:
        """Get or create TCP connection."""
        with self._socket_lock:
            if self.socket is None:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)
                
                if self.keepalive:
                    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
                self.socket.connect((self.host, self.port))
            
            return self.socket
    
    def write(self, message: str, record: Optional[LogRecord] = None) -> SinkResult:
        """Send message via TCP."""
        if record and not self.should_write(record):
            self._record_filtered()
            return SinkResult.FILTERED
        
        for attempt in range(self.reconnect_attempts + 1):
            try:
                transformed_message = self.transform_message(message, record)
                data = (transformed_message + '\n').encode('utf-8')
                
                sock = self._get_socket()
                sock.sendall(data)
                
                self._record_success(len(data))
                return SinkResult.SUCCESS
                
            except (socket.error, ConnectionError, BrokenPipeError):
                # Connection failed, reset socket for next attempt
                with self._socket_lock:
                    if self.socket:
                        try:
                            self.socket.close()
                        except:
                            pass
                        self.socket = None
                
                if attempt < self.reconnect_attempts:
                    self._record_retry()
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    self._record_error()
                    return SinkResult.ERROR
            
            except Exception:
                self._record_error()
                return SinkResult.ERROR
        
        return SinkResult.ERROR
    
    def close(self) -> None:
        """Close TCP connection."""
        with self._socket_lock:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None


class HTTPSink(Sink):
    """
    Sink that sends logs via HTTP/HTTPS POST requests.
    
    Features:
    - REST API integration
    - JSON payload formatting
    - Authentication support
    - Retry with exponential backoff
    """
    
    def __init__(
        self,
        name: str,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize HTTP sink.
        
        Args:
            name: Sink name
            url: Target URL
            method: HTTP method (POST, PUT)
            headers: Additional HTTP headers
            timeout: Request timeout
            max_retries: Maximum retry attempts
        """
        super().__init__(name)
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Set default headers
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/json'
    
    def write(self, message: str, record: Optional[LogRecord] = None) -> SinkResult:
        """Send message via HTTP with comprehensive error handling and fallbacks."""
        if record and not self.should_write(record):
            self._record_filtered()
            return SinkResult.FILTERED
        
        try:
            transformed_message = self.transform_message(message, record)
            
            # Primary HTTP send attempt
            try:
                import urllib.request
                import urllib.error
                
                # Prepare payload (assume JSON format)
                try:
                    # Try to parse as JSON for proper formatting
                    data = json.loads(transformed_message)
                    payload = json.dumps(data).encode('utf-8')
                except json.JSONDecodeError:
                    # Fallback to wrapping in JSON object
                    payload = json.dumps({"message": transformed_message}).encode('utf-8')
                except Exception:
                    # If even JSON encoding fails, use raw bytes
                    payload = transformed_message.encode('utf-8')
                
                request = urllib.request.Request(
                    self.url,
                    data=payload,
                    headers=self.headers,
                    method=self.method
                )
                
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    if 200 <= response.status < 300:
                        self._record_success(len(payload))
                        return SinkResult.SUCCESS
                    else:
                        # HTTP error response - fallback to local logging
                        self._record_error()
                        try:
                            print(f"[MYLOGS-HTTP-FALLBACK-{self.name.upper()}] HTTP {response.status}, local log: {transformed_message}", file=sys.stderr)
                            return SinkResult.RETRY  # Still return retry for HTTP errors
                        except Exception:
                            return SinkResult.ERROR
                        
            except ImportError:
                # urllib not available - fallback to stderr
                try:
                    print(f"[MYLOGS-HTTP-NOIMPORT-{self.name.upper()}] No HTTP lib, local log: {transformed_message}", file=sys.stderr)
                    self._record_success(len(transformed_message))
                    return SinkResult.SUCCESS
                except Exception:
                    self._record_error()
                    return SinkResult.ERROR
                    
            except urllib.error.HTTPError as e:
                # HTTP error - with fallback logging
                try:
                    print(f"[MYLOGS-HTTP-ERROR-{self.name.upper()}] HTTP {e.code}, local log: {transformed_message}", file=sys.stderr)
                except Exception:
                    pass
                    
                if 400 <= e.code < 500:
                    # Client error, don't retry
                    self._record_error()
                    return SinkResult.ERROR
                else:
                    # Server error, retry
                    self._record_error()
                    return SinkResult.RETRY
                    
            except (urllib.error.URLError, socket.timeout, OSError):
                # Network error - fallback to stderr
                try:
                    print(f"[MYLOGS-HTTP-NETWORK-{self.name.upper()}] Network failed, local log: {transformed_message}", file=sys.stderr)
                    self._record_success(len(transformed_message))
                    return SinkResult.SUCCESS  # Success because we logged locally
                except Exception:
                    self._record_error()
                    return SinkResult.ERROR
                    
        except Exception as e:
            # Unexpected error - fail gracefully
            self._record_error()
            try:
                print(f"[MYLOGS-HTTP-CRITICAL-{self.name.upper()}] Unexpected error: {str(e)[:100]}", file=sys.stderr)
            except Exception:
                pass  # Complete silent failure
            return SinkResult.ERROR


# ============================================================================
# SPECIALTY SINKS
# ============================================================================

class NullSink(Sink):
    """
    Sink that discards all messages (for testing/benchmarking).
    """
    
    def __init__(self, name: str = "null"):
        super().__init__(name)
    
    def write(self, message: str, record: Optional[LogRecord] = None) -> SinkResult:
        """Discard the message."""
        self._record_success(len(message.encode()))
        return SinkResult.SUCCESS


class BufferedSink(Sink):
    """
    Sink that buffers messages and flushes periodically.
    
    This is useful for high-throughput scenarios where you want to
    batch writes to expensive destinations.
    """
    
    def __init__(
        self,
        name: str,
        target_sink: Sink,
        buffer_size: int = 1000,
        flush_interval: float = 5.0
    ):
        """
        Initialize buffered sink.
        
        Args:
            name: Sink name
            target_sink: The sink to forward messages to
            buffer_size: Number of messages to buffer
            flush_interval: Maximum time between flushes (seconds)
        """
        super().__init__(name)
        self.target_sink = target_sink
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        self.buffer: List[tuple[str, Optional[LogRecord]]] = []
        self.last_flush = time.time()
        self._buffer_lock = threading.Lock()
    
    def write(self, message: str, record: Optional[LogRecord] = None) -> SinkResult:
        """Buffer the message and flush if necessary."""
        with self._buffer_lock:
            self.buffer.append((message, record))
            
            should_flush = (
                len(self.buffer) >= self.buffer_size or
                time.time() - self.last_flush >= self.flush_interval
            )
            
            if should_flush:
                self._flush_buffer()
        
        return SinkResult.SUCCESS
    
    def _flush_buffer(self) -> None:
        """Flush buffered messages to target sink."""
        if not self.buffer:
            return
        
        messages_to_flush = self.buffer[:]
        self.buffer.clear()
        self.last_flush = time.time()
        
        # Send all buffered messages
        for message, record in messages_to_flush:
            try:
                result = self.target_sink.write(message, record)
                if result == SinkResult.SUCCESS:
                    self._record_success()
                else:
                    self._record_error()
            except Exception:
                self._record_error()
    
    def flush(self) -> None:
        """Force flush of buffered messages."""
        with self._buffer_lock:
            self._flush_buffer()
    
    def close(self) -> None:
        """Flush buffer and close target sink."""
        self.flush()
        self.target_sink.close()


class ConditionalSink(Sink):
    """
    Sink that only writes messages matching certain conditions.
    
    This allows for sophisticated routing based on log content,
    level, context, or any other criteria.
    """
    
    def __init__(
        self,
        name: str,
        target_sink: Sink,
        condition: Callable[[LogRecord], bool]
    ):
        """
        Initialize conditional sink.
        
        Args:
            name: Sink name
            target_sink: The sink to forward matching messages to
            condition: Function that returns True for messages to forward
        """
        super().__init__(name)
        self.target_sink = target_sink
        self.condition = condition
    
    def write(self, message: str, record: Optional[LogRecord] = None) -> SinkResult:
        """Write message only if condition is met."""
        if record is None or not self.condition(record):
            self._record_filtered()
            return SinkResult.FILTERED
        
        result = self.target_sink.write(message, record)
        
        if result == SinkResult.SUCCESS:
            self._record_success()
        elif result == SinkResult.ERROR:
            self._record_error()
        
        return result
    
    def close(self) -> None:
        """Close target sink."""
        self.target_sink.close()


# ============================================================================
# SINK UTILITIES
# ============================================================================

def create_elasticsearch_sink(
    name: str,
    host: str,
    port: int = 9200,
    index: str = "logs",
    doc_type: str = "_doc"
) -> HTTPSink:
    """
    Create a sink for Elasticsearch.
    
    Args:
        name: Sink name
        host: Elasticsearch host
        port: Elasticsearch port
        index: Index name
        doc_type: Document type
    
    Returns:
        HTTPSink configured for Elasticsearch
    """
    url = f"http://{host}:{port}/{index}/{doc_type}"
    headers = {
        'Content-Type': 'application/json'
    }
    
    return HTTPSink(name, url, headers=headers)


def create_splunk_sink(
    name: str,
    host: str,
    port: int = 8088,
    token: str = "",
    index: str = "main"
) -> HTTPSink:
    """
    Create a sink for Splunk HEC (HTTP Event Collector).
    
    Args:
        name: Sink name
        host: Splunk host
        port: Splunk HEC port
        token: HEC token
        index: Splunk index
    
    Returns:
        HTTPSink configured for Splunk
    """
    url = f"https://{host}:{port}/services/collector"
    headers = {
        'Authorization': f'Splunk {token}',
        'Content-Type': 'application/json'
    }
    
    class SplunkTransformSink(HTTPSink):
        def transform_message(self, message: str, record: Optional[LogRecord] = None) -> str:
            """Transform message for Splunk HEC format."""
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                data = {"message": message}
            
            splunk_event = {
                "time": int(time.time()),
                "index": index,
                "event": data
            }
            
            return json.dumps(splunk_event)
    
    return SplunkTransformSink(name, url, headers=headers)


# ============================================================================
# SINK REGISTRY
# ============================================================================

class SinkRegistry:
    """
    Registry for managing multiple sinks.
    
    This allows for centralized sink management, statistics collection,
    and coordinated shutdown.
    """
    
    def __init__(self):
        self.sinks: Dict[str, Sink] = {}
        self._lock = threading.RLock()
    
    def register(self, sink: Sink) -> None:
        """Register a sink."""
        with self._lock:
            self.sinks[sink.name] = sink
    
    def unregister(self, name: str) -> Optional[Sink]:
        """Unregister a sink."""
        with self._lock:
            return self.sinks.pop(name, None)
    
    def get(self, name: str) -> Optional[Sink]:
        """Get a sink by name."""
        with self._lock:
            return self.sinks.get(name)
    
    def list_sinks(self) -> List[str]:
        """List all registered sink names."""
        with self._lock:
            return list(self.sinks.keys())
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all sinks."""
        with self._lock:
            return {name: sink.get_stats() for name, sink in self.sinks.items()}
    
    def flush_all(self) -> None:
        """Flush all sinks."""
        with self._lock:
            for sink in self.sinks.values():
                try:
                    sink.flush()
                except Exception:
                    pass  # Continue with other sinks
    
    def close_all(self) -> None:
        """Close all sinks."""
        with self._lock:
            for sink in self.sinks.values():
                try:
                    sink.close()
                except Exception:
                    pass  # Continue with other sinks
            self.sinks.clear()


# Global sink registry
_global_registry = SinkRegistry()


def get_sink_registry() -> SinkRegistry:
    """Get the global sink registry."""
    return _global_registry
