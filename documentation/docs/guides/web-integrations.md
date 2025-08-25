---
id: web-integrations
title: Web Framework Integrations
---

FastAPI:

```python
from fastapi import FastAPI
import kakashi

app = FastAPI()
kakashi.setup_fastapi(app, service_name="my-api", environment="production")
```

Flask:

```python
from flask import Flask
import kakashi

app = Flask(__name__)
kakashi.setup_flask(app)
```

Django:

Call `kakashi.setup_django()` during startup and include URLs from
`kakashi.integrations.django_integration.urlpatterns`.
