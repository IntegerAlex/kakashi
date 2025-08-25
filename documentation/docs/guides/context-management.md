---
id: context-management
title: Context Management
---

Attach request/user/custom context to enrich logs:

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


