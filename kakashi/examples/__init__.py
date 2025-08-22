"""
Example usage of kakashi in various scenarios.

This package contains examples showing how to use kakashi in different
types of Python applications.
"""

from .basic_usage import main as basic_example
from .web_framework_examples import (
    fastapi_example,
    flask_example,
    django_example_setup
)
from .gui_application_example import gui_example
from .cli_application_example import cli_example

__all__ = [
    'basic_example',
    'fastapi_example',
    'flask_example', 
    'django_example_setup',
    'gui_example',
    'cli_example'
]
