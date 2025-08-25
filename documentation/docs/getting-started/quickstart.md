---
id: quickstart
title: Quickstart
---

Basic usage:

```python
import kakashi

kakashi.setup()

kakashi.info("Application started")
kakashi.warning("This is a warning message")
kakashi.error("Something went wrong", component="startup")
```

Module loggers:

```python
from kakashi import get_structured_logger

app_logger = get_structured_logger("myapp")
db_logger = get_structured_logger("myapp.database")
api_logger = get_structured_logger("myapp.api")

db_logger.info("Database connection established", db="primary")
api_logger.info("Endpoint called", route="/users")
```


