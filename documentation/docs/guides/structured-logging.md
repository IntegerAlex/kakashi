---
id: structured-logging
title: Structured Logging
---

Use structured loggers for consistent machine-parsable output:

```python
from kakashi import get_structured_logger

logger = get_structured_logger(__name__)
logger.info("User created", user_id=42, role="admin")
```
