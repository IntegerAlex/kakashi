"""
kakashi - Enterprise-grade logging for Python applications.

🚀 Simple usage:
    import kakashi
    kakashi.setup()  # Intelligent auto-configuration
    kakashi.info("Hello world!")

🏢 Enterprise usage:
    import kakashi
    kakashi.setup("production", service="my-api", version="1.0.0")
    logger = kakashi.get_logger(__name__)
    logger.info("Service started", component="api", port=8000)

🔧 Framework integrations:
    # FastAPI
    kakashi.setup_fastapi(app)
    
    # Flask  
    kakashi.setup_flask(app)
    
    # Django
    kakashi.setup_django()
"""

# Import all public API functions from the api module
from .api import (
    # Core setup
    setup,
    
    # Simple logging functions
    debug, info, warning, warn, error, critical, fatal, exception,
    metric, audit, security,
    
    # Framework integrations
    setup_fastapi, setup_flask, setup_django,
    
    # Integration availability flags
    FASTAPI_AVAILABLE, FLASK_AVAILABLE, DJANGO_AVAILABLE,
)

# Core components - explicit imports to avoid namespace pollution
from .core.interface import (
    get_logger, get_structured_logger, get_request_logger,
    setup_logging, set_log_level,
    set_request_context, set_user_context, set_custom_context, clear_request_context,
    configure_colors, enable_bright_colors, disable_colors,
    create_custom_logger, clear_logger_cache, PerformanceLogger, get_performance_logger
)
from .core.records import LogLevel, LogRecord, LogContext

# Package metadata
__version__ = "0.1.0"
__author__ = "Akshat Kotpalliwar"

# Main exports - Streamlined public API
__all__ = [
    # ---- CORE API (Essential) ----
    "setup",           # ⭐ Main setup function
    
    # ---- SIMPLE LOGGING (Primary Use Case) ----
    "debug", "info", "warning", "warn", "error", "critical", "fatal", "exception",
    "metric", "audit", "security",
    
    # ---- ADVANCED API (Power Users) ----
    "get_logger", "get_structured_logger", "get_request_logger",
    "setup_logging", "set_log_level",
    
    # Context management
    "set_request_context", "set_user_context", "set_custom_context", "clear_request_context",
    
    # Configuration
    "configure_colors", "enable_bright_colors", "disable_colors",
    
    # Core data types
    "LogLevel", "LogRecord", "LogContext",
    
    # Integration availability flags
    "FASTAPI_AVAILABLE", "FLASK_AVAILABLE", "DJANGO_AVAILABLE",
]

# Add integration exports if available
if FASTAPI_AVAILABLE:
    __all__.extend([
        "setup_fastapi",           # ⭐ Simple FastAPI setup
    ])

if FLASK_AVAILABLE:
    __all__.extend([
        "setup_flask",            # ⭐ Simple Flask setup
    ])

if DJANGO_AVAILABLE:
    __all__.extend([
        "setup_django",           # ⭐ Simple Django setup
    ])