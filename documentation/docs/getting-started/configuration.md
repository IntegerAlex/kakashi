---
id: configuration
title: Configuration
---

Environment presets:

```python
from kakashi import setup_logging

setup_logging("development")
setup_logging("production", service_name="user-api", version="2.1.0")
```

Log level:

```python
from kakashi import set_log_level

set_log_level('DEBUG')
```

---

*Last updated: 2025-08-27*
*Contributors: [IntegerAlex]*
