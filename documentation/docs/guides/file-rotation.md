---
id: file-rotation
title: File Rotation
---

Kakashi writes per-module files and rotates daily with a size fallback. Example layout:

```text
logs/
├── app.log
└── modules/
    ├── database.log
    ├── api.log
    ├── authentication.log
    └── background_tasks.log
```
