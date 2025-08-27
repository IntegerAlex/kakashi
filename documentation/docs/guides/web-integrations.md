---
id: web-integrations
title: Web Framework Integrations
---

FastAPI:

```python
from fastapi import FastAPI
from kakashi.integrations.fastapi_integration import setup_fastapi_enterprise

app = FastAPI()
setup_fastapi_enterprise(app, service_name="my-api", environment="production")
```

Flask:

```python
from flask import Flask
from kakashi.integrations.flask_integration import setup_flask_enterprise

app = Flask(__name__)
setup_flask_enterprise(app)
```

Django:

Call `kakashi.integrations.django_integration.setup_django_enterprise()` during startup and include URLs from
`kakashi.integrations.django_integration.urlpatterns`.

---

*Last updated: 2025-08-27*
*Contributors: [IntegerAlex]*
