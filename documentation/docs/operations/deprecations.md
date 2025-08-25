---
id: deprecations
title: Deprecations & Compatibility
---

Legacy singleton-style API is maintained for compatibility but will be deprecated. Prefer the functional API via `kakashi.core` and top-level helpers.

Legacy middleware names map to enterprise integrations:

- FastAPI: `kakashi.setup_fastapi(app, ...)`
- Flask: `kakashi.setup_flask(app, ...)`
- Django: `kakashi.setup_django(...)`
