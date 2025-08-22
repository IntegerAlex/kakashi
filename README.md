# Kakashi - High-Performance Python Logging Utility

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/kakashi.svg)](https://badge.fury.io/py/kakashi)

Enterprise-grade logging for Python with a modern functional pipeline, structured logging, and first-class FastAPI/Flask/Django integrations. Backward-compatible aliases are kept, but the functional API is now the recommended path.

## 🚀 Features

- **✅ Functional API (new)**: Immutable config, composable pipelines, thread-safe by design
- **🧱 Structured logging**: JSON and compact text formatters for consistent logs
- **📡 Enterprise integrations (new)**: One-line setup for FastAPI, Flask, and Django
- **📅 Rotation & files**: Daily rotation with 100MB size fallback; per-module files
- **🎨 Color control**: Bright/disabled modes; independent console/file color config
- **🌐 Context**: Request, user, and custom context fields with helpers
- **⚙️ Environments**: Development/production/testing presets with `setup()`

## 📦 Installation

### Basic Installation

```bash
pip install kakashi
```

### With integrations

```bash
pip install kakashi[fastapi]
```

```bash
pip install kakashi[flask]
```

```bash
pip install kakashi[django]
```

All web integrations:

```bash
pip install kakashi[web]
```

### Development Installation

```bash
pip install kakashi[dev]
```

Optional performance extras:

```bash
pip install kakashi[performance]
```

Everything:

```bash
pip install kakashi[all]
```

## 🛠️ Quick Start

### Basic Usage (simple API)

```python
import kakashi

# Intelligent, one-line setup (auto-detects environment and sensible defaults)
kakashi.setup()

# Ultra-simple logging helpers
kakashi.info("Application started")
kakashi.warning("This is a warning message")
kakashi.error("Something went wrong", component="startup")
```

### Module loggers (structured)

```python
from kakashi import get_structured_logger

app_logger = get_structured_logger("myapp")
db_logger = get_structured_logger("myapp.database")
api_logger = get_structured_logger("myapp.api")

db_logger.info("Database connection established", db="primary")
api_logger.info("Endpoint called", route="/users")
```

### Request/user/custom context

```python
from kakashi import (
    get_structured_logger,
    set_request_context,
    set_user_context,
    set_custom_context,
    clear_request_context,
)

logger = get_structured_logger(__name__)
set_request_context("192.168.1.100", "POST /api/users")
set_user_context(user_id="42", role="admin")
set_custom_context(trace_id="abc-123")
logger.info("User created successfully")
clear_request_context()
```

### FastAPI integration (enterprise)

```python
from fastapi import FastAPI
import kakashi

app = FastAPI()
kakashi.setup_fastapi(app, service_name="my-api", environment="production")

@app.get("/")
async def root():
    kakashi.info("Root endpoint accessed")
    return {"message": "Hello World"}
```

## 📋 Log Format

The default log format includes:

```text
TIMESTAMP | LEVEL | MODULE | ACCESS | IP | MESSAGE
2024-01-15 10:30:45.123 | INFO     | myapp.users | POST /api/users | 192.168.1.100 | User created successfully
```

## 🎨 Color Configuration

### Enable Bright Colors

```python
from kakashi import enable_bright_colors

enable_bright_colors()
```

### Disable All Colors

```python
from kakashi import disable_colors

disable_colors()
```

### Custom Color Configuration

```python
from kakashi import configure_colors

# Bright console colors, plain file logs
configure_colors(bright_colors=True, colored_file_logs=False)
```

## ⚙️ Environment Configuration

### Development Setup

```python
import kakashi
kakashi.setup("development")  # Verbose console output
```

### Production Setup

```python
import kakashi
kakashi.setup("production", service="user-api", version="2.1.0")
```

## 📁 Log File Organization

```text
logs/
├── app.log                    # Default application logs
└── modules/
    ├── database.log          # Database-specific logs
    ├── api.log              # API-specific logs
    ├── authentication.log   # Auth-specific logs
    └── background_tasks.log # Background task logs
```

## 🔧 Advanced Configuration

### Log Level Configuration

```python
from kakashi import set_log_level

set_log_level('DEBUG')  # Set global log level
```

### Console and File Color Settings

```python
from kakashi import set_console_colors, set_file_colors

set_console_colors(bright=True)        # Bright console colors
set_file_colors(enabled=True, bright=False)  # Normal file colors
```

### Request Context Management

```python
from kakashi import set_request_context, clear_request_context

# Set context
set_request_context("192.168.1.100", "GET /api/data")

# Your logging here...

# Clear context when done
clear_request_context()
```

## 🔌 Web Framework Integrations

### FastAPI (one-line enterprise setup)

```python
from fastapi import FastAPI
import kakashi

app = FastAPI()
kakashi.setup_fastapi(app)
```

### Flask (one-line enterprise setup)

```python
from flask import Flask
import kakashi

app = Flask(__name__)
kakashi.setup_flask(app)

@app.route("/")
def index():
    kakashi.info("Flask index hit")
    return {"ok": True}

### Django (URL patterns provided)

In Django, call `kakashi.setup_django()` in your startup (e.g., `apps.py`), then include the provided health/metrics URLs from `kakashi.integrations.django_integration.urlpatterns`.

## 🧪 Running the Demo

After installation, you can run the built-in demo:

```bash
kakashi-demo
```

This will create example log files in the `logs/` directory demonstrating all features.

## 🧭 Deprecations and Compatibility

- The legacy singleton-style API is maintained for compatibility but will be deprecated in future versions. Prefer the functional API exposed via `kakashi.core` and the simple top-level helpers in `kakashi`.
- Old middleware names like `IPLoggingMiddleware` and functions like `create_ip_logging_middleware`, `setup_fastapi_logging`, `init_flask_logging`, and legacy Django aliases now map to the new enterprise integrations and may be removed in the future. Use:
  - FastAPI: `kakashi.setup_fastapi(app, ...)`
  - Flask: `kakashi.setup_flask(app, ...)`
  - Django: `kakashi.setup_django(...)`

See optional extras in installation for `fastapi`, `flask`, `django`, `web`, `performance`, and `all` bundles.

## 📚 API Reference

### Core Functions

- `setup(environment=None, service=None, version=None, ...)`: One-line intelligent setup
- `get_logger(name)`: Traditional logger instance (compat)
- `get_structured_logger(name)`: Structured logger instance (recommended)
- `get_request_logger(name)`: Logger with request context helpers
- `set_log_level(level)`: Set global log level
- `setup_logging(environment)`: Advanced environment configuration
- `set_request_context(ip, access)`, `set_user_context(...)`, `set_custom_context(...)`, `clear_request_context()`

### Color Configuration

- `configure_colors(bright_colors, colored_file_logs, bright_file_colors)`
- `enable_bright_colors()` / `disable_colors()`
- `set_console_colors(bright)` / `set_file_colors(enabled, bright)`

### Middleware (Compatibility)

- Legacy names like `IPLoggingMiddleware` map to enterprise integrations. Prefer:
  - `setup_fastapi(app, ...)`
  - `setup_flask(app, ...)`
  - `setup_django(...)`

## 🏗️ Architecture

The core is a functional, pipeline-based design with immutable configuration:

- **Pipelines**: Composable enrichers, filters, formatters, and writers
- **Context**: Structured `LogContext` with helpers for request/user/custom fields
- **Async backend**: Optional async pipelines for high-throughput scenarios
- **Rotation**: Daily rotation with size-based fallback for file writers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the NCCF Project
- Inspired by the need for production-ready logging solutions
- Thanks to the FastAPI and Starlette communities for middleware inspiration

## 📞 Support

For support, please open an issue on the [GitHub repository](https://github.com/IntegerAlex/kakashi/issues).
