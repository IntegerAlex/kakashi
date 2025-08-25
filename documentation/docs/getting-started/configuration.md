---
id: configuration
title: Configuration
---

Environment presets:

```python
import kakashi

kakashi.setup("development")
kakashi.setup("production", service="user-api", version="2.1.0")
```

Log level:

```python
from kakashi import set_log_level

set_log_level('DEBUG')
```


