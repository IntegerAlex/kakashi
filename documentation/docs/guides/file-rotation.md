---
id: file-rotation
title: File Rotation
---

Kakashi provides size-based file rotation through the `RotatingFileSink` class. Files are rotated when they exceed a specified size limit.

## Basic File Rotation

```python
from kakashi.core.sinks import RotatingFileSink

# Create a rotating file sink
rotating_sink = RotatingFileSink(
    name="app_logs",
    file_path="logs/app.log",
    max_bytes=100 * 1024 * 1024,  # 100MB
    backup_count=10,  # Keep 10 backup files
    rotation_type="size"  # Size-based rotation
)
```

## File Organization

Kakashi writes per-module files and rotates based on size. Example layout:

```text
logs/
├── app.log                    # Current log file
├── app.log.1                 # First backup
├── app.log.2                 # Second backup
├── app.log.3                 # Third backup
└── modules/
    ├── database.log          # Database module logs
    ├── api.log              # API module logs
    ├── authentication.log    # Auth module logs
    └── background_tasks.log # Background task logs
```

## Configuration Options

```python
# Custom rotation settings
rotating_sink = RotatingFileSink(
    name="high_volume_logs",
    file_path="logs/high_volume.log",
    max_bytes=500 * 1024 * 1024,  # 500MB files
    backup_count=30,               # Keep 30 backup files
    rotation_type="size",          # Size-based rotation
    encoding="utf-8"               # File encoding
)
```

## Integration with Pipelines

```python
from kakashi.core.sink_pipeline import create_file_pipeline

# Create pipeline with rotating file sink
pipeline = create_file_pipeline(
    file_path="logs/app.log",
    min_level=LogLevel.INFO,
    formatter=default_json_formatter
)
```

---

*Last updated: 2025-08-27*
*Contributors: [IntegerAlex]*
