"""
Main API functions for kakashi - extracted from __init__.py for better organization.

This module contains the core public API functions that users interact with.
"""

import os
import sys
import threading
from typing import Optional, Union, Any, Dict, List
from pathlib import Path
from importlib.util import find_spec

from .core.interface import (
    get_logger, get_structured_logger, get_request_logger,
    setup_logging, set_log_level,
    set_request_context, set_user_context, set_custom_context, clear_request_context,
    configure_colors, enable_bright_colors, disable_colors,
    create_custom_logger, clear_logger_cache, PerformanceLogger, get_performance_logger
)
from .core.records import LogLevel, LogRecord, LogContext
from .core.functional_logger import FunctionalLogger

# Global state for simple API
_default_logger: Optional[FunctionalLogger] = None
_setup_complete: bool = False
_setup_lock = threading.RLock()

# Integration availability flags
FASTAPI_AVAILABLE = False
FLASK_AVAILABLE = False  
DJANGO_AVAILABLE = False

# Check for optional integrations with comprehensive error handling
try:
    # Check if FastAPI is actually installed before importing our integration
    if find_spec("fastapi") and find_spec("starlette"):
        from .integrations.fastapi_integration import *
        FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
except Exception as e:
    # Any other error during FastAPI integration import - log but continue
    FASTAPI_AVAILABLE = False
    try:
        import sys
        print(f"[MYLOGS-WARNING] FastAPI integration disabled due to error: {str(e)[:100]}", file=sys.stderr)
    except Exception:
        pass

try:
    # Check if Flask is actually installed before importing our integration
    if find_spec("flask"):
        from .integrations.flask_integration import *
        FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
except Exception as e:
    # Any other error during Flask integration import - log but continue
    FLASK_AVAILABLE = False
    try:
        import sys
        print(f"[MYLOGS-WARNING] Flask integration disabled due to error: {str(e)[:100]}", file=sys.stderr)
    except Exception:
        pass

try:
    # Check if Django is actually installed before importing our integration
    if find_spec("django"):
        from .integrations.django_integration import *
        DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
except Exception as e:
    # Any other error during Django integration import - log but continue
    DJANGO_AVAILABLE = False
    try:
        import sys
        print(f"[MYLOGS-WARNING] Django integration disabled due to error: {str(e)[:100]}", file=sys.stderr)
    except Exception:
        pass


def setup(
    environment: Optional[str] = None,
    service: Optional[str] = None,
    version: Optional[str] = None,
    log_directory: Optional[Union[str, Path]] = None,
    level: Optional[Union[str, LogLevel]] = None,
    structured: bool = True,
    async_logging: Optional[bool] = None,
    console_output: bool = True,
    file_output: bool = True,
    **kwargs: Any
) -> None:
    """
    🚀 Intelligent one-line setup for mylogs.
    
    This function automatically configures mylogs with sensible defaults based on
    your environment while allowing customization for enterprise needs.
    
    Args:
        environment: Auto-detected if None. Options: 'development', 'production', 'testing'
        service: Service name (added to all logs). Auto-detected from __main__ if None
        version: Service version (added to all logs)
        log_directory: Where to write log files. Auto-configured if None
        level: Log level. Auto-configured based on environment if None
        structured: Use structured JSON logging (recommended: True)
        async_logging: Use async I/O. Auto-configured based on environment if None
        console_output: Log to console (stdout/stderr)
        file_output: Log to files
        **kwargs: Additional configuration passed to environment setup
    
    Examples:
        # Simplest possible setup
        mylogs.setup()
        
        # Development setup
        mylogs.setup("development")
        
        # Production setup with service info
        mylogs.setup("production", service="user-api", version="2.1.0")
        
        # High-performance setup
        mylogs.setup("production", async_logging=True, level="INFO")
        
        # Custom directory
        mylogs.setup(log_directory="/var/log/myapp")
    """
    global _default_logger, _setup_complete
    
    with _setup_lock:
        if _setup_complete:
            return  # Already set up - idempotent
        
        # 0. Defensive validation with graceful fallbacks
        try:
            # Validate environment
            if environment is not None and not isinstance(environment, str):
                environment = str(environment) if environment else None
            if environment and environment.lower() not in ('development', 'dev', 'production', 'prod', 'testing', 'test'):
                print(f"[MYLOGS-WARNING] Unknown environment '{environment}', falling back to 'development'", file=sys.stderr)
                environment = 'development'
            
            # Validate service name
            if service is not None and not isinstance(service, str):
                service = str(service) if service else None
            
            # Validate log directory
            if log_directory is not None:
                try:
                    log_directory = Path(log_directory)
                    # Try to create directory if it doesn't exist
                    log_directory.mkdir(parents=True, exist_ok=True)
                except (OSError, PermissionError):
                    print(f"[MYLOGS-WARNING] Cannot create log directory '{log_directory}', using current directory", file=sys.stderr)
                    log_directory = Path.cwd() / "logs"
                    try:
                        log_directory.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        log_directory = None  # Will use default
                except Exception as e:
                    print(f"[MYLOGS-WARNING] Invalid log directory '{log_directory}': {e}", file=sys.stderr)
                    log_directory = None
            
            # Validate level
            if level is not None:
                if isinstance(level, str):
                    try:
                        level = LogLevel.from_name(level.upper())
                    except (ValueError, KeyError):
                        print(f"[MYLOGS-WARNING] Invalid log level '{level}', using INFO", file=sys.stderr)
                        level = LogLevel.INFO
                elif not isinstance(level, LogLevel):
                    try:
                        level = LogLevel(level)
                    except (ValueError, TypeError):
                        print(f"[MYLOGS-WARNING] Invalid log level type '{type(level)}', using INFO", file=sys.stderr)
                        level = LogLevel.INFO
                        
        except Exception as validation_error:
            # If validation itself fails, use safe defaults
            print(f"[MYLOGS-ERROR] Setup validation failed: {validation_error!s}, using safe defaults", file=sys.stderr)
            environment = 'development'
            service = None
            log_directory = None
            level = LogLevel.INFO
        
        # 1. Auto-detect environment if not provided (after validation)
        if environment is None:
            environment = _detect_environment()
        
        # 2. Auto-detect service name if not provided (after validation)
        if service is None:
            service = _detect_service_name()
        
        # 3. Auto-configure async logging based on environment
        if async_logging is None:
            async_logging = environment.lower() in ('production', 'prod')
        
        # 4. Use validated level or auto-configure based on environment
        if level is None:
            if environment.lower() in ('development', 'dev'):
                level = LogLevel.DEBUG
            elif environment.lower() in ('testing', 'test'):
                level = LogLevel.INFO
            else:  # production
                level = LogLevel.INFO
        
        # 5. Set up environment configuration
        env_kwargs = {
            'service_name': service,
            'version': version,
            'enable_async_io': async_logging,
            **kwargs
        }
        
        if log_directory:
            env_kwargs['log_directory'] = log_directory
        
        # Configure environment with error handling
        try:
            setup_logging(environment, **env_kwargs)
        except Exception as setup_error:
            print(f"[MYLOGS-ERROR] Environment setup failed: {setup_error}, using minimal configuration", file=sys.stderr)
            # Fallback to minimal setup - just create a basic logger
        
        # 6. Create default logger for simple API with error handling
        try:
            if structured:
                _default_logger = get_structured_logger("kakashi.default")
            else:
                _default_logger = get_logger("kakashi.default")
        except Exception as logger_error:
            print(f"[KAKASHI-ERROR] Logger creation failed: {logger_error}, using basic fallback", file=sys.stderr)
            # Create a minimal fallback logger that just prints to stderr
            from .fallback import FallbackLogger
            _default_logger = FallbackLogger()
        
        _setup_complete = True
        
        # 7. Log setup completion with error handling
        try:
            _default_logger.info("Kakashi setup complete", 
                               environment=environment,
                               service=service or "unknown",
                               version=version or "unknown",
                               async_logging=async_logging,
                               structured_logging=structured)
        except Exception:
            try:
                print(f"[KAKASHI-INFO] Setup complete for {service or 'unknown'} in {environment} environment", file=sys.stderr)
            except Exception:
                pass  # Even stderr failed - complete silent operation


def _detect_environment() -> str:
    """Auto-detect the runtime environment.
    
    Returns:
        str: Detected environment name ('development', 'production', or 'testing')
    """
    # Check common environment variables
    env_vars: List[tuple[str, Optional[Dict[str, str]]]] = [
        ('ENVIRONMENT', None),
        ('ENV', None), 
        ('STAGE', None),
        ('DEPLOY_ENV', None),
        ('NODE_ENV', {'development': 'development', 'production': 'production'}),
        ('FLASK_ENV', {'development': 'development', 'production': 'production'}),
        ('DJANGO_SETTINGS_MODULE', None),
    ]
    
    for var, mapping in env_vars:
        value = os.getenv(var, '').lower()
        if value:
            if mapping and value in mapping:
                return mapping[value]
            elif value in ('dev', 'development', 'local'):
                return 'development'
            elif value in ('prod', 'production', 'live'):
                return 'production' 
            elif value in ('test', 'testing', 'stage', 'staging'):
                return 'testing'
    
    # Check if we're in a testing framework
    if 'pytest' in sys.modules or 'unittest' in sys.modules:
        return 'testing'
    
    # Check if we're in a development environment
    if os.getenv('DEBUG', '').lower() in ('true', '1', 'yes'):
        return 'development'
    
    # Default to development for safety
    return 'development'


def _detect_service_name() -> str:
    """Auto-detect service name from the main module.
    
    Returns:
        str: Detected service name or default 'python-app'
    """
    try:
        import __main__
        if hasattr(__main__, '__file__') and __main__.__file__:
            return Path(__main__.__file__).stem
    except (ImportError, AttributeError, OSError):
        pass
    
    # Fallback to package/directory name
    try:
        cwd_name = Path.cwd().name
        if cwd_name and cwd_name != '/':
            return cwd_name
    except (OSError, AttributeError):
        pass
    
    return "python-app"


def _ensure_setup() -> None:
    """Ensure setup has been called, auto-setup if not. Never crashes."""
    try:
        if not _setup_complete:
            setup()  # Auto-setup with defaults
    except Exception as e:
        # If even auto-setup fails, create emergency fallback
        global _default_logger
        if _default_logger is None:
            try:
                print(f"[KAKASHI-CRITICAL] Auto-setup failed: {e!s}, using emergency fallback", file=sys.stderr)
                from .fallback import EmergencyLogger
                _default_logger = EmergencyLogger()
            except (OSError, ImportError):
                # Complete failure - create a no-op logger
                from .fallback import NoOpLogger
                _default_logger = NoOpLogger()


# Internal error logger for logging failures
def _log_internal_error(operation: str, error: Exception) -> None:
    """Log internal errors to stderr with fallback to print."""
    try:
        print(f"[KAKASHI-INTERNAL-ERROR] {operation} failed: {error}", file=sys.stderr)
    except Exception:
        # Last resort - use print to stdout
        try:
            print(f"[KAKASHI-INTERNAL-ERROR] {operation} failed: {error}")
        except Exception:
            pass  # Complete failure - silent operation


# Top-level logging functions for super simple usage - never crash the app
def debug(message: str, **fields: Any) -> None:
    """Log a debug message. Auto-setup if not configured. Never crashes."""
    try:
        _ensure_setup()
        _default_logger.debug(message, **fields)
    except Exception as e:
        _log_internal_error("debug logging", e)


def info(message: str, **fields: Any) -> None:
    """Log an info message. Auto-setup if not configured. Never crashes."""
    try:
        _ensure_setup()
        _default_logger.info(message, **fields)
    except Exception as e:
        _log_internal_error("info logging", e)


def warning(message: str, **fields: Any) -> None:
    """Log a warning message. Auto-setup if not configured. Never crashes.""" 
    try:
        _ensure_setup()
        _default_logger.warning(message, **fields)
    except Exception as e:
        _log_internal_error("warning logging", e)


def warn(message: str, **fields: Any) -> None:
    """Alias for warning(). Auto-setup if not configured. Never crashes."""
    try:
        warning(message, **fields)
    except Exception as e:
        _log_internal_error("warn logging", e)


def error(message: str, **fields: Any) -> None:
    """Log an error message. Auto-setup if not configured. Never crashes."""
    try:
        _ensure_setup()
        _default_logger.error(message, **fields)
    except Exception as e:
        _log_internal_error("error logging", e)


def critical(message: str, **fields: Any) -> None:
    """Log a critical message. Auto-setup if not configured. Never crashes."""
    try:
        _ensure_setup()
        _default_logger.critical(message, **fields)
    except Exception as e:
        _log_internal_error("critical logging", e)


def fatal(message: str, **fields: Any) -> None:
    """Alias for critical(). Auto-setup if not configured. Never crashes."""
    try:
        critical(message, **fields)
    except Exception as e:
        _log_internal_error("fatal logging", e)


def exception(message: str, **fields: Any) -> None:
    """Log an error with exception traceback. Auto-setup if not configured. Never crashes."""
    try:
        _ensure_setup()
        _default_logger.exception(message, **fields)
    except Exception as e:
        _log_internal_error("exception logging", e)


# Metric and structured logging conveniences - never crash the app
def metric(name: str, value: Union[int, float], **fields: Any) -> None:
    """Log a metric. Auto-setup if not configured. Never crashes."""
    try:
        _ensure_setup()
        if hasattr(_default_logger, 'metric'):
            _default_logger.metric(name, value, **fields)
        else:
            _default_logger.info(f"METRIC: {name}={value}", metric_name=name, metric_value=value, **fields)
    except Exception as e:
        _log_internal_error("metric logging", e)


def audit(action: str, resource: str, **fields: Any) -> None:
    """Log an audit event. Auto-setup if not configured. Never crashes."""
    try:
        _ensure_setup()
        if hasattr(_default_logger, 'audit'):
            _default_logger.audit(action, resource, **fields)
        else:
            _default_logger.info(f"AUDIT: {action} on {resource}", audit_action=action, audit_resource=resource, **fields)
    except Exception as e:
        _log_internal_error("audit logging", e)


def security(event_type: str, severity: str = "info", **fields: Any) -> None:
    """Log a security event. Auto-setup if not configured. Never crashes."""
    try:
        _ensure_setup()
        level_func = getattr(_default_logger, severity.lower(), _default_logger.info)
        level_func(f"SECURITY: {event_type}", security_event=event_type, security_severity=severity, **fields)
    except Exception as e:
        _log_internal_error("security logging", e)


# Framework integration shortcuts with comprehensive error handling
if FASTAPI_AVAILABLE:
    def setup_fastapi(app: Any, **kwargs: Any) -> Any:
        """🚀 One-line FastAPI logging setup with enterprise observability."""
        try:
            if not hasattr(app, '_mylogs_setup'):
                from .integrations.fastapi_integration import setup_fastapi_enterprise
                middleware = setup_fastapi_enterprise(app, **kwargs)
                app._mylogs_setup = True  # Mark as configured to ensure idempotency
                return middleware
            else:
                # Already configured - return existing middleware if available
                for middleware in getattr(app, 'user_middleware', []):
                    if hasattr(middleware, 'cls') and 'ObservabilityMiddleware' in str(middleware.cls):
                        return middleware.cls
                return None
        except Exception as e:
            try:
                print(f"[KAKASHI-ERROR] FastAPI setup failed: {str(e)[:100]}", file=sys.stderr)
            except (OSError, UnicodeError):
                pass
            return None
else:
    def setup_fastapi(app: Any, **kwargs: Any) -> None:
        """FastAPI not available - provide graceful fallback."""
        try:
            print("[KAKASHI-WARNING] FastAPI not available. Install with: pip install kakashi[fastapi]", file=sys.stderr)
        except (OSError, UnicodeError):
            pass

if FLASK_AVAILABLE:
    def setup_flask(app: Any, **kwargs: Any) -> Any:
        """🚀 One-line Flask logging setup with enterprise observability."""
        try:
            if not hasattr(app, '_mylogs_setup'):
                from .integrations.flask_integration import setup_flask_enterprise
                handler = setup_flask_enterprise(app, **kwargs)
                app._mylogs_setup = True  # Mark as configured to ensure idempotency
                return handler
            else:
                # Already configured - return existing handler if available
                return getattr(app, '_mylogs_handler', None)
        except Exception as e:
            try:
                print(f"[KAKASHI-ERROR] Flask setup failed: {str(e)[:100]}", file=sys.stderr)
            except (OSError, UnicodeError):
                pass
            return None
else:
    def setup_flask(app: Any, **kwargs: Any) -> None:
        """Flask not available - provide graceful fallback."""
        try:
            print("[KAKASHI-WARNING] Flask not available. Install with: pip install kakashi[flask]", file=sys.stderr)
        except (OSError, UnicodeError):
            pass

if DJANGO_AVAILABLE:
    def setup_django(**kwargs: Any) -> Any:
        """🚀 One-line Django logging setup with enterprise observability."""
        try:
            # Check if Django is configured
            try:
                from django.conf import settings
                if not getattr(settings, '_MYLOGS_SETUP', False):
                    from .integrations.django_integration import setup_django_enterprise
                    result = setup_django_enterprise(**kwargs)
                    settings._MYLOGS_SETUP = True  # Mark as configured to ensure idempotency
                    return result
                else:
                    # Already configured
                    return None
            except (ImportError, AttributeError):
                # Django might not be configured yet - still try to set up
                from .integrations.django_integration import setup_django_enterprise
                return setup_django_enterprise(**kwargs)
        except Exception as e:
            try:
                print(f"[KAKASHI-ERROR] Django setup failed: {str(e)[:100]}", file=sys.stderr)
            except (OSError, UnicodeError):
                pass
            return None
else:
    def setup_django(**kwargs: Any) -> None:
        """Django not available - provide graceful fallback."""
        try:
            print("[KAKASHI-WARNING] Django not available. Install with: pip install kakashi[django]", file=sys.stderr)
        except (OSError, UnicodeError):
            pass
