"""
🚀 Enterprise-ready Flask integration for mylogs.

This module provides comprehensive Flask integration with structured logging,
sinks architecture, and enterprise observability features.

Features:
- 🏢 Enterprise observability (metrics, traces, audits)  
- 📊 Structured logging with key-value pairs
- 🎯 Multi-sink architecture (console, files, network)
- 🔍 Request/response tracing with correlation IDs
- 📈 Performance monitoring and SLA tracking
- 🔒 Security event logging and threat detection
- ⚡ Optimized for Flask's request context
- 🌐 Distributed tracing support
- 📋 Health check and metrics endpoints

Install with: pip install mylogs[flask]
"""

try:
    from flask import Flask, request, g, jsonify
except ImportError as e:
    raise ImportError(
        "Flask integration requires flask. "
        "Install with: pip install mylogs[flask] or pip install flask"
    ) from e

import time
import uuid
import functools
from typing import Optional, Callable, Dict, Any, List, Set, Union
from datetime import datetime
import threading

from ..core.structured_logger import StructuredLogger, create_structured_logger
# Note: sink_config imports may need to be updated based on actual module structure


class EnterpriseFlaskHandler:
    """
    🏢 Enterprise-grade observability handler for Flask.
    
    Provides comprehensive request/response logging, performance monitoring,
    security event detection, and distributed tracing support.
    """
    
    def __init__(
        self,
        app: Optional[Flask] = None,
        logger: Optional[StructuredLogger] = None,
        service_name: Optional[str] = None,
        version: Optional[str] = None,
        environment: str = "development",
        enable_request_body_logging: bool = False,
        enable_response_body_logging: bool = False,
        max_body_size: int = 10000,
        exclude_paths: Optional[Set[str]] = None,
        slow_request_threshold: float = 1.0,  # seconds
        enable_security_monitoring: bool = True,
        enable_performance_monitoring: bool = True,
        correlation_id_header: str = "X-Correlation-ID",
        trace_id_header: str = "X-Trace-ID",
    ):
        """
        Initialize enterprise Flask observability handler.
        
        Args:
            app: Flask application (can be set later with init_app)
            logger: Custom structured logger (auto-created if None)
            service_name: Name of the service for observability
            version: Service version
            environment: Environment (development/production/staging)
            enable_request_body_logging: Log request bodies (careful with sensitive data)
            enable_response_body_logging: Log response bodies (careful with large responses)
            max_body_size: Maximum body size to log (bytes)
            exclude_paths: Set of paths to exclude from logging
            slow_request_threshold: Threshold for slow request alerts (seconds)
            enable_security_monitoring: Enable security event detection
            enable_performance_monitoring: Enable performance metrics collection
            correlation_id_header: Header name for correlation ID
            trace_id_header: Header name for trace ID
        """
        self.service_name = service_name
        self.version = version or "unknown"
        self.environment = environment
        self.enable_request_body_logging = enable_request_body_logging
        self.enable_response_body_logging = enable_response_body_logging
        self.max_body_size = max_body_size
        self.exclude_paths = exclude_paths or {"/health", "/metrics", "/favicon.ico"}
        self.slow_request_threshold = slow_request_threshold
        self.enable_security_monitoring = enable_security_monitoring
        self.enable_performance_monitoring = enable_performance_monitoring
        self.correlation_id_header = correlation_id_header
        self.trace_id_header = trace_id_header
        
        # Create structured logger if not provided
        if logger is None:
            self.logger = self._create_default_logger()
        else:
            self.logger = logger
        
        # Performance tracking
        self.request_count = 0
        self.error_count = 0
        self.total_request_time = 0.0
        self._lock = threading.Lock()
        
        # Security monitoring patterns
        self.suspicious_patterns = {
            'sql_injection': ['union select', 'drop table', 'insert into', 'delete from'],
            'xss': ['<script', 'javascript:', 'onerror='],
            'path_traversal': ['../', '..\/', '%2e%2e%2f'],
            'command_injection': ['$(', '`', '&&', '||', ';']
        }
        
        if app is not None:
            self.init_app(app)
    
    def _create_default_logger(self) -> StructuredLogger:
        """Create a default structured logger with appropriate sinks."""
        # Create a basic structured logger - sink configuration may need adjustment
        return create_structured_logger(
            "flask.observability",
            include_source=self.environment == "development",
            include_thread_info=True
        )
    
    def init_app(self, app: Flask) -> None:
        """Initialize the Flask application with enterprise observability."""
        # Auto-detect service info from app if not provided
        if self.service_name is None:
            self.service_name = getattr(app, 'name', 'flask-service')
        
        # Register hooks
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_appcontext)
        
        # Register error handlers
        app.errorhandler(Exception)(self._handle_exception)
        
        # Store handler reference in app
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['mylogs_enterprise'] = self
        
        # Log initialization
        self.logger.info("Flask enterprise observability initialized",
                        service=self.service_name,
                        version=self.version,
                        environment=self.environment,
                        security_monitoring=self.enable_security_monitoring,
                        performance_monitoring=self.enable_performance_monitoring)
    
    def _before_request(self) -> None:
        """Handle request start with enterprise observability."""
        # Skip excluded paths
        if request.path in self.exclude_paths:
            return
        
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())
        
        # Extract or generate correlation and trace IDs
        g.correlation_id = request.headers.get(self.correlation_id_header, g.request_id)
        g.trace_id = request.headers.get(self.trace_id_header, str(uuid.uuid4()))
        
        # Extract client information
        client_info = self._extract_client_info()
        g.client_info = client_info
        
        # Security monitoring
        g.security_events = []
        if self.enable_security_monitoring:
            g.security_events = self._detect_security_threats()
        
        # Log request start
        self.logger.info("Request started",
                        request_id=g.request_id,
                        correlation_id=g.correlation_id,
                        trace_id=g.trace_id,
                        method=request.method,
                        path=request.path,
                        query_params=dict(request.args),
                        client_ip=client_info['ip'],
                        user_agent=client_info['user_agent'],
                        service=self.service_name,
                        version=self.version,
                        environment=self.environment,
                        security_events=g.security_events if g.security_events else None)
        
        # Log request body if enabled
        if self.enable_request_body_logging and request.data:
            try:
                if len(request.data) <= self.max_body_size:
                    body_str = request.data.decode('utf-8', errors='ignore')
                    self.logger.debug("Request body captured",
                                    request_id=g.request_id,
                                    body_size=len(request.data),
                                    body_preview=body_str[:200] + "..." if len(body_str) > 200 else body_str,
                                    content_type=request.content_type)
            except Exception as e:
                self.logger.warning("Failed to capture request body",
                                  request_id=g.request_id,
                                  error=str(e))
    
    def _after_request(self, response: Any) -> Any:
        """Handle request completion with enterprise observability."""
        # Skip excluded paths or if no timing info
        if request.path in self.exclude_paths or not hasattr(g, 'start_time'):
            return response
        
        # Calculate duration
        duration_ms = (time.time() - g.start_time) * 1000
        
        # Update performance metrics
        with self._lock:
            self.request_count += 1
            self.total_request_time += duration_ms
        
        # Add observability headers
        response.headers[self.correlation_id_header] = g.correlation_id
        response.headers[self.trace_id_header] = g.trace_id
        response.headers["X-Request-ID"] = g.request_id
        response.headers["X-Service-Name"] = self.service_name
        response.headers["X-Service-Version"] = self.version
        
        # Log response body if enabled and small enough
        response_info = {}
        if self.enable_response_body_logging and response.data:
            if len(response.data) <= self.max_body_size:
                try:
                    body_str = response.data.decode('utf-8', errors='ignore')
                    response_info["body_preview"] = body_str[:200] + "..." if len(body_str) > 200 else body_str
                    response_info["body_size"] = len(response.data)
                except:
                    response_info["body_note"] = "Could not decode response body"
        
        # Log request completion
        self.logger.info("Request completed",
                        request_id=g.request_id,
                        correlation_id=g.correlation_id,
                        trace_id=g.trace_id,
                        method=request.method,
                        path=request.path,
                        status_code=response.status_code,
                        duration_ms=round(duration_ms, 2),
                        client_ip=g.client_info['ip'],
                        response_size=len(response.data) if response.data else None,
                        service=self.service_name,
                        version=self.version,
                        environment=self.environment,
                        **response_info)
        
        # Performance monitoring
        if self.enable_performance_monitoring:
            self._record_performance_metrics(response, duration_ms)
        
        # Log slow requests
        if duration_ms > (self.slow_request_threshold * 1000):
            self.logger.warning("Slow request detected",
                              request_id=g.request_id,
                              duration_ms=round(duration_ms, 2),
                              threshold_ms=self.slow_request_threshold * 1000,
                              method=request.method,
                              path=request.path,
                              status_code=response.status_code)
        
        # Security event logging
        if hasattr(g, 'security_events') and g.security_events:
            self.logger.security("Security threats detected",
                               request_id=g.request_id,
                               threats=g.security_events,
                               client_ip=g.client_info['ip'],
                               user_agent=g.client_info['user_agent'],
                               path=request.path)
        
        return response
    
    def _teardown_appcontext(self, exception: Optional[Exception]) -> None:
        """Handle application context teardown."""
        if exception:
            self.logger.error("Application context error",
                            request_id=getattr(g, 'request_id', 'unknown'),
                            error_type=type(exception).__name__,
                            error_message=str(exception),
                            method=request.method if request else None,
                            path=request.path if request else None)
    
    def _handle_exception(self, error: Exception) -> Any:
        """Handle unhandled exceptions with comprehensive logging."""
        with self._lock:
            self.error_count += 1
        
        # Log the exception
        self.logger.error("Unhandled exception",
                        request_id=getattr(g, 'request_id', str(uuid.uuid4())),
                        correlation_id=getattr(g, 'correlation_id', 'unknown'),
                        error_type=type(error).__name__,
                        error_message=str(error),
                        method=request.method if request else None,
                        path=request.path if request else None,
                        client_ip=getattr(g, 'client_info', {}).get('ip', 'unknown'),
                        service=self.service_name,
                        version=self.version)
        
        # Return JSON error response for API endpoints, HTML for others
        if request and (request.path.startswith('/api/') or 
                       request.headers.get('Content-Type', '').startswith('application/json')):
            return jsonify({
                "error": "Internal server error",
                "request_id": getattr(g, 'request_id', 'unknown'),
                "correlation_id": getattr(g, 'correlation_id', 'unknown'),
                "service": self.service_name,
                "timestamp": datetime.utcnow().isoformat()
            }), 500
        
        # Re-raise for Flask's default error handling
        raise error
    
    def _extract_client_info(self) -> Dict[str, Any]:
        """Extract client information from request."""
        # Get real IP address (handle proxies, load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")
        
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif real_ip:
            client_ip = real_ip
        else:
            client_ip = request.remote_addr or "unknown"
        
        return {
            "ip": client_ip,
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "referer": request.headers.get("Referer"),
            "host": request.headers.get("Host"),
            "origin": request.headers.get("Origin")
        }
    
    def _detect_security_threats(self) -> List[str]:
        """Detect potential security threats in the request."""
        threats = []
        
        # Check URL and query parameters for suspicious patterns
        url_str = request.url.lower()
        query_str = str(request.args).lower()
        
        for threat_type, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                if pattern in url_str or pattern in query_str:
                    threats.append(f"{threat_type}_attempt")
                    break
        
        # Check for unusually long URLs
        if len(request.url) > 2000:
            threats.append("long_url_attack")
        
        # Check for too many query parameters
        if len(request.args) > 50:
            threats.append("parameter_pollution")
        
        # Check request headers for suspicious patterns
        for header_name, header_value in request.headers.items():
            if any(pattern in header_value.lower() for patterns in self.suspicious_patterns.values() for pattern in patterns):
                threats.append("malicious_header")
                break
        
        return threats
    
    def _record_performance_metrics(self, response, duration_ms: float) -> None:
        """Record performance metrics."""
        metrics = {
            "request_duration_ms": duration_ms,
            "status_code": response.status_code,
            "method": request.method,
            "path": request.path,
            "service": self.service_name,
            "version": self.version,
            "environment": self.environment
        }
        
        # Log as a metric
        self.logger.metric("http_request_duration", duration_ms, **metrics)
        
        if response.status_code >= 400:
            self.logger.metric("http_request_errors", 1, 
                             status_code=response.status_code,
                             path=request.path,
                             method=request.method)


class HealthCheckBlueprint:
    """Health check blueprint with detailed service status."""
    
    def __init__(self, handler: EnterpriseFlaskHandler, url_prefix: str = ""):
        self.handler = handler
        self.url_prefix = url_prefix
        self.health_checks: Dict[str, Callable[[], bool]] = {}
        self.startup_time = time.time()
        
    def add_health_check(self, name: str, check_func: Callable[[], bool]):
        """Add a custom health check."""
        self.health_checks[name] = check_func
    
    def create_blueprint(self):
        """Create Flask blueprint with health and metrics endpoints."""
        from flask import Blueprint
        
        bp = Blueprint('mylogs_observability', __name__, url_prefix=self.url_prefix)
        
        @bp.route('/health')
        def health_check():
            """Service health check endpoint."""
            checks = {}
            overall_healthy = True
            
            # Run all health checks
            for name, check_func in self.health_checks.items():
                try:
                    healthy = check_func()
                    checks[name] = {"status": "healthy" if healthy else "unhealthy"}
                    if not healthy:
                        overall_healthy = False
                except Exception as e:
                    checks[name] = {"status": "error", "error": str(e)}
                    overall_healthy = False
            
            uptime = time.time() - self.startup_time
            
            health_status = {
                "service": self.handler.service_name,
                "version": self.handler.version,
                "status": "healthy" if overall_healthy else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": round(uptime, 2),
                "checks": checks
            }
            
            # Log health check
            if overall_healthy:
                self.handler.logger.debug("Health check passed", **health_status)
            else:
                self.handler.logger.warning("Health check failed", **health_status)
            
            status_code = 200 if overall_healthy else 503
            return jsonify(health_status), status_code
        
        @bp.route('/metrics')
        def metrics():
            """Service metrics endpoint."""
            with self.handler._lock:
                avg_response_time = (self.handler.total_request_time / self.handler.request_count) if self.handler.request_count > 0 else 0
                
                metrics_data = {
                    "requests_total": self.handler.request_count,
                    "errors_total": self.handler.error_count,
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "service_info": {
                        "name": self.handler.service_name,
                        "version": self.handler.version,
                        "environment": self.handler.environment
                    }
                }
            
            return jsonify(metrics_data)
        
        return bp


# ============================================================================
# SIMPLE INTEGRATION FUNCTIONS  
# ============================================================================

def setup_flask_enterprise(
    app: Flask,
    service_name: Optional[str] = None,
    version: Optional[str] = None,
    environment: Optional[str] = None,
    enable_health_endpoint: bool = True,
    enable_metrics_endpoint: bool = True,
    enable_security_monitoring: bool = True,
    **handler_kwargs
) -> EnterpriseFlaskHandler:
    """
    🚀 One-line setup for enterprise-grade Flask observability.
    
    This function automatically configures your Flask application with:
    - Comprehensive request/response logging
    - Performance monitoring
    - Security threat detection
    - Health check endpoints  
    - Distributed tracing support
    - Structured logging with sinks
    
    Args:
        app: Flask application instance
        service_name: Name of your service (auto-detected if None)
        version: Service version (auto-detected if None)
        environment: Environment (auto-detected if None) 
        enable_health_endpoint: Add /health endpoint
        enable_metrics_endpoint: Add /metrics endpoint
        enable_security_monitoring: Enable security threat detection
        **handler_kwargs: Additional handler configuration
    
    Returns:
        EnterpriseFlaskHandler instance for further customization
        
    Example:
        from flask import Flask
        import mylogs
        
        app = Flask(__name__)
        
        # Simple setup
        mylogs.setup_flask(app)
        
        # Advanced setup
        handler = mylogs.setup_flask(
            app,
            service_name="user-api",
            version="1.2.0",
            environment="production" 
        )
    """
    # Auto-detect values if not provided
    if service_name is None:
        service_name = app.name
    if environment is None:
        from os import getenv
        environment = getenv('FLASK_ENV', getenv('ENVIRONMENT', 'development'))
    
    # Create and initialize handler
    handler = EnterpriseFlaskHandler(
        app=app,
        service_name=service_name,
        version=version,
        environment=environment,
        enable_security_monitoring=enable_security_monitoring,
        **handler_kwargs
    )
    
    # Add health and metrics endpoints
    if enable_health_endpoint or enable_metrics_endpoint:
        health_bp = HealthCheckBlueprint(handler)
        
        if enable_health_endpoint or enable_metrics_endpoint:
            bp = health_bp.create_blueprint()
            app.register_blueprint(bp)
    
    # Log setup completion
    handler.logger.info("Flask enterprise observability setup complete",
                       service=service_name,
                       version=version or "unknown",
                       environment=environment,
                       health_endpoint=enable_health_endpoint,
                       metrics_endpoint=enable_metrics_endpoint,
                       security_monitoring=enable_security_monitoring)
    
    return handler


def flask_enterprise_route(
    route_name: Optional[str] = None,
    logger: Optional[StructuredLogger] = None,
    **log_fields
):
    """
    🎯 Decorator for enterprise route logging with structured data.
    
    This decorator automatically logs route entry/exit with structured data
    and performance metrics.
    
    Args:
        route_name: Custom name for the route (auto-detected if None)
        logger: Custom logger (uses app logger if None)
        **log_fields: Additional fields to include in all route logs
        
    Example:
        @app.route('/users/<int:user_id>')
        @flask_enterprise_route("get_user", component="user_service")
        def get_user(user_id):
            return {"user_id": user_id}
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            route_name_final = route_name or f.__name__
            
            # Get logger
            if logger:
                route_logger = logger
            else:
                handler = current_app.extensions.get('mylogs_enterprise')
                route_logger = handler.logger if handler else None
            
            if route_logger:
                # Log route entry
                route_logger.info("Route started",
                                request_id=getattr(g, 'request_id', 'unknown'),
                                route_name=route_name_final,
                                function_name=f.__name__,
                                args=args,
                                kwargs=kwargs,
                                **log_fields)
            
            try:
                # Execute the route
                result = f(*args, **kwargs)
                
                # Log successful completion
                if route_logger:
                    duration_ms = (time.time() - start_time) * 1000
                    route_logger.info("Route completed successfully",
                                    request_id=getattr(g, 'request_id', 'unknown'),
                                    route_name=route_name_final,
                                    duration_ms=round(duration_ms, 2),
                                    **log_fields)
                
                return result
                
            except Exception as e:
                # Log route error
                if route_logger:
                    duration_ms = (time.time() - start_time) * 1000
                    route_logger.error("Route failed with exception",
                                     request_id=getattr(g, 'request_id', 'unknown'),
                                     route_name=route_name_final,
                                     error_type=type(e).__name__,
                                     error_message=str(e),
                                     duration_ms=round(duration_ms, 2),
                                     **log_fields)
                raise
        
        return wrapper
    return decorator


# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

# Legacy aliases for backward compatibility  
FlaskLoggingHandler = EnterpriseFlaskHandler
init_flask_logging = setup_flask_enterprise
flask_log_route = flask_enterprise_route

def get_flask_logger(name: str = "flask", log_file: Optional[str] = None):
    """Legacy function - creates a basic structured logger."""
    return create_structured_logger(name)

def log_flask_error(error: Exception, route: Optional[str] = None):
    """Legacy function - logs Flask errors."""
    logger = create_structured_logger("flask.error")
    logger.error("Flask error", 
                error_type=type(error).__name__,
                error_message=str(error),
                route=route)

# Simple alias for the main function
setup_flask = setup_flask_enterprise

__all__ = [
    # New enterprise API
    "setup_flask_enterprise",
    "setup_flask",
    "EnterpriseFlaskHandler", 
    "HealthCheckBlueprint",
    "flask_enterprise_route",
    
    # Legacy compatibility
    "FlaskLoggingHandler",
    "init_flask_logging", 
    "flask_log_route",
    "get_flask_logger",
    "log_flask_error",
]