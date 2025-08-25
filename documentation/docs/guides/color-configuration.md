---
id: color-configuration
title: Color Configuration
---

Console colors:

```python
from kakashi import enable_bright_colors, disable_colors

enable_bright_colors()
disable_colors()
```

Custom config:

```python
from kakashi import configure_colors

configure_colors(bright_colors=True, colored_file_logs=False)
```
