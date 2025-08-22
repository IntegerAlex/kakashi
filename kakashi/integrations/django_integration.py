"""
🚀 Enterprise-ready Django integration for mylogs.

This module provides comprehensive Django integration with structured logging,
sinks architecture, and enterprise observability features.

Features:
- 🏢 Enterprise observability (metrics, traces, audits)
- 📊 Structured logging with key-value pairs  
- 🎯 Multi-sink architecture (console, files, network)
- 🔍 Request/response tracing with correlation IDs
- 📈 Performance monitoring and SLA tracking
- 🔒 Security event logging and threat detection
- ⚡ Django-native middleware integration
- 🌐 Distributed tracing support
- 📋 Model operation tracking and audit trails
- 🎪 Management command logging
- 📋 Health check and metrics endpoints

Install with: pip install mylogs[django]
"""

try:
    from django.conf import settings
    from django.http import HttpRequest, HttpResponse, JsonResponse
    from django.utils.deprecation import MiddlewareMixin
    from django.db.models.signals import post_save, post_delete
    from django.contrib.auth.signals import user_logged_in, user_login_failed
    from django.dispatch import receiver
    from django.urls import path
except ImportError as e:
    raise ImportError(
        "Django integration requires django. "
        "Install with: pip install mylogs[django] or pip install django"
    ) from e

import time
import uuid
import functools
import threading
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime

from ..core import (
    StructuredLogger, create_structured_logger,
    development_sink_config, production_sink_config, 
    create_sink_logger_config
)


class EnterpriseDjangoMiddleware(MiddlewareMixin):
    """
    🏢 Enterprise-grade observability middleware for Django.
    
    Provides comprehensive request/response logging, performance monitoring,
    security event detection, and distributed tracing support.
    """
    
    def __init__(self, get_response: Optional[Callable] = None):
        """
        Initialize enterprise Django observability middleware.
        
        Args:
            get_response: Django get_response callable
        """
        super().__init__(get_response)
        
        # Configuration from Django settings
        self.service_name = getattr(settings, 'MYLOGS_SERVICE_NAME', 'django-service')
        self.version = getattr(settings, 'MYLOGS_SERVICE_VERSION', 'unknown')
        self.environment = getattr(settings, 'MYLOGS_ENVIRONMENT', 'development')
        self.enable_request_body_logging = getattr(settings, 'MYLOGS_REQUEST_BODY_LOGGING', False)
        self.enable_response_body_logging = getattr(settings, 'MYLOGS_RESPONSE_BODY_LOGGING', False)
        self.max_body_size = getattr(settings, 'MYLOGS_MAX_BODY_SIZE', 10000)
        self.exclude_paths = set(getattr(settings, 'MYLOGS_EXCLUDE_PATHS', [
            '/admin/', '/health/', '/metrics/', '/favicon.ico', '/static/', '/media/'
        ]))
        self.slow_request_threshold = getattr(settings, 'MYLOGS_SLOW_REQUEST_THRESHOLD', 1.0)
        self.enable_security_monitoring = getattr(settings, 'MYLOGS_SECURITY_MONITORING', True)
        self.enable_performance_monitoring = getattr(settings, 'MYLOGS_PERFORMANCE_MONITORING', True)
        self.correlation_id_header = getattr(settings, 'MYLOGS_CORRELATION_ID_HEADER', 'HTTP_X_CORRELATION_ID')
        self.trace_id_header = getattr(settings, 'MYLOGS_TRACE_ID_HEADER', 'HTTP_X_TRACE_ID')
        
        # Create structured logger
        self.logger = self._create_logger()
        
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
        
        self.logger.info("Django enterprise observability middleware initialized",
                        service=self.service_name,
                        version=self.version,
                        environment=self.environment,
                        security_monitoring=self.enable_security_monitoring,
                        performance_monitoring=self.enable_performance_monitoring)
    
    def _create_logger(self) -> StructuredLogger:
        """Create a structured logger with appropriate sinks."""
        if self.environment == "development":
            config = development_sink_config(
                service_name=self.service_name,
                version=self.version
            )
        else:
            config = production_sink_config(
                service_name=self.service_name,
                version=self.version
            )
        
        logger_config = create_sink_logger_config("django.observability", config)
        return create_structured_logger("django.observability", 
                                       pipeline=logger_config.pipeline)
    
    def process_request(self, request: HttpRequest) -> None:
        """Handle request start with enterprise observability."""
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.exclude_paths):
            return None
        
        request.mylogs_start_time = time.time()
        request.mylogs_request_id = str(uuid.uuid4())
        
        # Extract or generate correlation and trace IDs
        request.mylogs_correlation_id = request.META.get(self.correlation_id_header, request.mylogs_request_id)
        request.mylogs_trace_id = request.META.get(self.trace_id_header, str(uuid.uuid4()))
        
        # Extract client information
        client_info = self._extract_client_info(request)
        request.mylogs_client_info = client_info
        
        # Security monitoring
        security_events = []
        if self.enable_security_monitoring:
            security_events = self._detect_security_threats(request)
        request.mylogs_security_events = security_events
        
        # Log request start
        self.logger.info("Request started",
                        request_id=request.mylogs_request_id,
                        correlation_id=request.mylogs_correlation_id,
                        trace_id=request.mylogs_trace_id,
                        method=request.method,
                        path=request.path,
                        query_params=dict(request.GET),
                        client_ip=client_info['ip'],
                        user_agent=client_info['user_agent'],
                        service=self.service_name,
                        version=self.version,
                        environment=self.environment,
                        user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                        security_events=security_events if security_events else None)
        
        # Log request body if enabled
        if self.enable_request_body_logging and request.body:
            try:
                if len(request.body) <= self.max_body_size:
                    body_str = request.body.decode('utf-8', errors='ignore')
                    self.logger.debug("Request body captured",
                                    request_id=request.mylogs_request_id,
                                    body_size=len(request.body),
                                    body_preview=body_str[:200] + "..." if len(body_str) > 200 else body_str,
                                    content_type=request.content_type)
            except Exception as e:
                self.logger.warning("Failed to capture request body",
                                  request_id=request.mylogs_request_id,
                                  error=str(e))
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Handle request completion with enterprise observability."""
        # Skip if no timing info or excluded paths
        if not hasattr(request, 'mylogs_start_time'):
            return response
        
        if any(request.path.startswith(path) for path in self.exclude_paths):
            return response
        
        # Calculate duration
        duration_ms = (time.time() - request.mylogs_start_time) * 1000
        
        # Update performance metrics
        with self._lock:
            self.request_count += 1
            self.total_request_time += duration_ms
        
        # Add observability headers
        response['X-Correlation-ID'] = request.mylogs_correlation_id
        response['X-Trace-ID'] = request.mylogs_trace_id
        response['X-Request-ID'] = request.mylogs_request_id
        response['X-Service-Name'] = self.service_name
        response['X-Service-Version'] = self.version
        
        # Log response body if enabled and small enough
        response_info = {}
        if self.enable_response_body_logging and hasattr(response, 'content') and response.content:
            if len(response.content) <= self.max_body_size:
                try:
                    body_str = response.content.decode('utf-8', errors='ignore')
                    response_info["body_preview"] = body_str[:200] + "..." if len(body_str) > 200 else body_str
                    response_info["body_size"] = len(response.content)
                except:
                    response_info["body_note"] = "Could not decode response body"
        
        # Log request completion
        self.logger.info("Request completed",
                        request_id=request.mylogs_request_id,
                        correlation_id=request.mylogs_correlation_id,
                        trace_id=request.mylogs_trace_id,
                        method=request.method,
                        path=request.path,
                        status_code=response.status_code,
                        duration_ms=round(duration_ms, 2),
                        client_ip=request.mylogs_client_info['ip'],
                        response_size=len(response.content) if hasattr(response, 'content') and response.content else None,
                        service=self.service_name,
                        version=self.version,
                        environment=self.environment,
                        user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                        **response_info)
        
        # Performance monitoring
        if self.enable_performance_monitoring:
            self._record_performance_metrics(request, response, duration_ms)
        
        # Log slow requests
        if duration_ms > (self.slow_request_threshold * 1000):
            self.logger.warning("Slow request detected",
                              request_id=request.mylogs_request_id,
                              duration_ms=round(duration_ms, 2),
                              threshold_ms=self.slow_request_threshold * 1000,
                              method=request.method,
                              path=request.path,
                              status_code=response.status_code,
                              user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None)
        
        # Security event logging
        if hasattr(request, 'mylogs_security_events') and request.mylogs_security_events:
            self.logger.security("Security threats detected",
                               request_id=request.mylogs_request_id,
                               threats=request.mylogs_security_events,
                               client_ip=request.mylogs_client_info['ip'],
                               user_agent=request.mylogs_client_info['user_agent'],
                               path=request.path,
                               user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None)
        
        return response
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """Handle unhandled exceptions with comprehensive logging."""
        with self._lock:
            self.error_count += 1
        
        # Log the exception
        self.logger.error("Unhandled exception",
                        request_id=getattr(request, 'mylogs_request_id', str(uuid.uuid4())),
                        correlation_id=getattr(request, 'mylogs_correlation_id', 'unknown'),
                        error_type=type(exception).__name__,
                        error_message=str(exception),
                        method=request.method,
                        path=request.path,
                        client_ip=getattr(request, 'mylogs_client_info', {}).get('ip', 'unknown'),
                        service=self.service_name,
                        version=self.version,
                        user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None)
        
        return None
    
    def _extract_client_info(self, request: HttpRequest) -> Dict[str, Any]:
        """Extract client information from request."""
        # Get real IP address (handle proxies, load balancers)
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        real_ip = request.META.get("HTTP_X_REAL_IP")
        
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif real_ip:
            client_ip = real_ip
        else:
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return {
            "ip": client_ip,
            "user_agent": request.META.get("HTTP_USER_AGENT", "unknown"),
            "referer": request.META.get("HTTP_REFERER"),
            "host": request.META.get("HTTP_HOST"),
            "origin": request.META.get("HTTP_ORIGIN")
        }
    
    def _detect_security_threats(self, request: HttpRequest) -> List[str]:
        """Detect potential security threats in the request."""
        threats = []
        
        # Check URL and query parameters for suspicious patterns
        url_str = request.build_absolute_uri().lower()
        query_str = str(request.GET).lower()
        
        for threat_type, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                if pattern in url_str or pattern in query_str:
                    threats.append(f"{threat_type}_attempt")
                    break
        
        # Check for unusually long URLs
        if len(request.build_absolute_uri()) > 2000:
            threats.append("long_url_attack")
        
        # Check for too many query parameters
        if len(request.GET) > 50:
            threats.append("parameter_pollution")
        
        # Check request headers for suspicious patterns
        for header_name, header_value in request.META.items():
            if header_name.startswith('HTTP_') and isinstance(header_value, str):
                if any(pattern in header_value.lower() for patterns in self.suspicious_patterns.values() for pattern in patterns):
                    threats.append("malicious_header")
                    break
        
        return threats
    
    def _record_performance_metrics(self, request: HttpRequest, response: HttpResponse, duration_ms: float) -> None:
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


class EnterpriseDjangoLogger:
    """
    🏢 Enterprise Django logger for model operations and business events.
    """
    
    def __init__(self, logger: Optional[StructuredLogger] = None):
        """
        Initialize enterprise Django logger.
        
        Args:
            logger: Custom structured logger (auto-created if None)
        """
        if logger is None:
            self.logger = self._create_logger()
        else:
            self.logger = logger
    
    def _create_logger(self) -> StructuredLogger:
        """Create a structured logger."""
        service_name = getattr(settings, 'MYLOGS_SERVICE_NAME', 'django-service')
        version = getattr(settings, 'MYLOGS_SERVICE_VERSION', 'unknown')
        environment = getattr(settings, 'MYLOGS_ENVIRONMENT', 'development')
        
        if environment == "development":
            config = development_sink_config(
                service_name=service_name,
                version=version
            )
        else:
            config = production_sink_config(
                service_name=service_name,
                version=version
            )
        
        logger_config = create_sink_logger_config("django.business", config)
        return create_structured_logger("django.business", 
                                       pipeline=logger_config.pipeline)
    
    def log_model_operation(self, model_name: str, operation: str, 
                           obj_id: Optional[str] = None, user_id: Optional[str] = None, **fields):
        """Log model operations (CRUD) for audit trails."""
        self.logger.audit(f"Model {operation}",
                         model=model_name,
                         operation=operation,
                         object_id=obj_id,
                         user_id=user_id,
                         **fields)
    
    def log_user_action(self, action: str, user_id: Optional[str] = None, 
                       target: Optional[str] = None, **fields):
        """Log user actions for security and audit purposes."""
        self.logger.audit("User action",
                         action=action,
                         user_id=user_id,
                         target=target,
                         **fields)
    
    def log_business_event(self, event_name: str, **fields):
        """Log business events for analytics and monitoring."""
        self.logger.info("Business event",
                        event=event_name,
                        **fields)
    
    def log_security_event(self, event_type: str, severity: str = "info", **fields):
        """Log security-related events."""
        self.logger.security(event_type, severity=severity, **fields)


# ============================================================================
# HEALTH CHECK AND METRICS VIEWS
# ============================================================================

def health_check_view(request):
    """Health check endpoint for Django."""
    service_name = getattr(settings, 'MYLOGS_SERVICE_NAME', 'django-service')
    version = getattr(settings, 'MYLOGS_SERVICE_VERSION', 'unknown')
    
    # Basic health check - can be extended with custom checks
    health_status = {
        "service": service_name,
        "version": version,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "django_version": getattr(settings, 'DJANGO_VERSION', 'unknown'),
        "debug_mode": settings.DEBUG
    }
    
    return JsonResponse(health_status)


def metrics_view(request):
    """Metrics endpoint for Django."""
    service_name = getattr(settings, 'MYLOGS_SERVICE_NAME', 'django-service')
    version = getattr(settings, 'MYLOGS_SERVICE_VERSION', 'unknown')
    environment = getattr(settings, 'MYLOGS_ENVIRONMENT', 'development')
    
    # Get middleware instance if available
    for middleware_cls in settings.MIDDLEWARE:
        if 'EnterpriseDjangoMiddleware' in middleware_cls:
            # This is a simplified approach - in practice you'd store the instance
            break
    
    metrics_data = {
        "service_info": {
            "name": service_name,
            "version": version,
            "environment": environment
        },
        "django_info": {
            "version": getattr(settings, 'DJANGO_VERSION', 'unknown'),
            "debug_mode": settings.DEBUG
        }
    }
    
    return JsonResponse(metrics_data)


# ============================================================================
# SIGNAL HANDLERS FOR AUTOMATIC LOGGING
# ============================================================================

def setup_django_signal_logging(logger: Optional[EnterpriseDjangoLogger] = None):
    """
    Set up automatic logging for Django model signals.
    
    Args:
        logger: Custom enterprise logger (auto-created if None)
    """
    if logger is None:
        logger = EnterpriseDjangoLogger()
    
    @receiver(post_save)
    def log_model_save(sender, instance, created, **kwargs):
        """Log model save operations."""
        operation = "CREATE" if created else "UPDATE"
        logger.log_model_operation(
            sender.__name__,
            operation,
            obj_id=str(getattr(instance, 'id', 'unknown')),
            model_fields={field.name: str(getattr(instance, field.name, None)) 
                         for field in sender._meta.fields if hasattr(instance, field.name)}
        )
    
    @receiver(post_delete)
    def log_model_delete(sender, instance, **kwargs):
        """Log model delete operations."""
        logger.log_model_operation(
            sender.__name__,
            "DELETE",
            obj_id=str(getattr(instance, 'id', 'unknown'))
        )
    
    @receiver(user_logged_in)
    def log_user_login(sender, request, user, **kwargs):
        """Log successful user logins."""
        logger.log_user_action(
            "LOGIN",
            user_id=str(user.id),
            username=user.username,
            client_ip=request.META.get('REMOTE_ADDR', 'unknown')
        )
    
    @receiver(user_login_failed)
    def log_user_login_failed(sender, credentials, request, **kwargs):
        """Log failed login attempts."""
        logger.log_security_event(
            "LOGIN_FAILED",
            severity="warning",
            username=credentials.get('username', 'unknown'),
            client_ip=request.META.get('REMOTE_ADDR', 'unknown')
        )


# ============================================================================
# MANAGEMENT COMMAND LOGGING
# ============================================================================

def log_management_command(command_name: str, logger_name: Optional[str] = None):
    """
    Decorator for Django management commands to add enterprise logging.
    
    Args:
        command_name: Name of the management command
        logger_name: Custom logger name
        
    Example:
        @log_management_command("sync_users")
        class Command(BaseCommand):
            help = "Synchronize users with external system"
            
            def handle(self, *args, **options):
                # Command logic here
                pass
    """
    def decorator(command_class):
        original_handle = command_class.handle
        
        @functools.wraps(original_handle)
        def logged_handle(self, *args, **options):
            logger = EnterpriseDjangoLogger()
            start_time = time.time()
            command_id = str(uuid.uuid4())
            
            logger.logger.info("Management command started",
                             command=command_name,
                             command_id=command_id,
                             args=args,
                             options=options)
            
            try:
                result = original_handle(self, *args, **options)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.logger.info("Management command completed successfully",
                                 command=command_name,
                                 command_id=command_id,
                                 duration_ms=round(duration_ms, 2))
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.logger.error("Management command failed",
                                   command=command_name,
                                   command_id=command_id,
                                   error_type=type(e).__name__,
                                   error_message=str(e),
                                   duration_ms=round(duration_ms, 2))
                raise
        
        command_class.handle = logged_handle
        return command_class
    
    return decorator


# ============================================================================
# SIMPLE INTEGRATION FUNCTIONS
# ============================================================================

def setup_django_enterprise(**kwargs):
    """
    🚀 One-line setup for enterprise-grade Django observability.
    
    This function provides configuration guidance for Django integration.
    Unlike Flask/FastAPI, Django configuration is done through settings.py.
    
    Add to your Django settings.py:
    
        MIDDLEWARE = [
            # ... your other middleware
            'mylogs.integrations.django_integration.EnterpriseDjangoMiddleware',
        ]
        
        # MyLogs Configuration
        MYLOGS_SERVICE_NAME = 'my-django-app'
        MYLOGS_SERVICE_VERSION = '1.0.0'
        MYLOGS_ENVIRONMENT = 'production'  # or 'development', 'staging'
        MYLOGS_SECURITY_MONITORING = True
        MYLOGS_PERFORMANCE_MONITORING = True
        MYLOGS_REQUEST_BODY_LOGGING = False  # Be careful with sensitive data
        MYLOGS_RESPONSE_BODY_LOGGING = False
        MYLOGS_SLOW_REQUEST_THRESHOLD = 1.0  # seconds
    
    In your URLconf, add health/metrics endpoints:
    
        from mylogs.integrations.django_integration import health_check_view, metrics_view
        
        urlpatterns = [
            # ... your other URLs
            path('health/', health_check_view, name='health'),
            path('metrics/', metrics_view, name='metrics'),
        ]
    
    To enable automatic model logging:
    
        from mylogs.integrations.django_integration import setup_django_signal_logging
        
        # In your apps.py or settings.py
        setup_django_signal_logging()
    
    Returns:
        Configuration guidance (this function is informational)
    """
    logger = create_structured_logger("django.setup")
    
    logger.info("Django enterprise observability setup guidance provided",
               note="Add middleware and settings to your Django configuration",
               middleware="mylogs.integrations.django_integration.EnterpriseDjangoMiddleware",
               required_settings=["MYLOGS_SERVICE_NAME", "MYLOGS_SERVICE_VERSION", "MYLOGS_ENVIRONMENT"])
    
    return {
        "status": "guidance_provided",
        "middleware": "mylogs.integrations.django_integration.EnterpriseDjangoMiddleware",
        "health_endpoint": "mylogs.integrations.django_integration.health_check_view",
        "metrics_endpoint": "mylogs.integrations.django_integration.metrics_view",
        "signal_logging": "mylogs.integrations.django_integration.setup_django_signal_logging"
    }


# ============================================================================
# URL PATTERNS FOR EASY INTEGRATION
# ============================================================================

# URL patterns that can be included in your Django URLconf
urlpatterns = [
    path('health/', health_check_view, name='mylogs_health'),
    path('metrics/', metrics_view, name='mylogs_metrics'),
]


# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

# Legacy aliases for backward compatibility
DjangoLoggingMiddleware = EnterpriseDjangoMiddleware
DjangoLogger = EnterpriseDjangoLogger

def get_django_logger(name: str = "django", log_file: Optional[str] = None):
    """Legacy function - creates a basic structured logger."""
    return create_structured_logger(name)

def log_django_error(error: Exception, view: Optional[str] = None, 
                    user_id: Optional[str] = None):
    """Legacy function - logs Django errors."""
    logger = create_structured_logger("django.error")
    logger.error("Django error",
                error_type=type(error).__name__,
                error_message=str(error),
                view=view,
                user_id=user_id)

# Simple alias for the main function
setup_django = setup_django_enterprise

__all__ = [
    # New enterprise API
    "setup_django_enterprise",
    "setup_django",
    "EnterpriseDjangoMiddleware",
    "EnterpriseDjangoLogger", 
    "setup_django_signal_logging",
    "log_management_command",
    "health_check_view",
    "metrics_view",
    "urlpatterns",
    
    # Legacy compatibility
    "DjangoLoggingMiddleware",
    "DjangoLogger",
    "get_django_logger",
    "log_django_error",
]