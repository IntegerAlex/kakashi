#!/usr/bin/env python3
"""
Setup script for Kakashi package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from pyproject.toml
def get_requirements():
    requirements = []
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    return requirements

setup(
    name="kakashi",
    version="0.1.0",
    author="Akshat Kotpalliwar",
    author_email="akshatkot@gmail.com",
    description="High-performance logging utility for Python applications with advanced features",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/IntegerAlex/kakashi",
    project_urls={
        "Bug Reports": "https://github.com/IntegerAlex/kakashi/issues",
        "Documentation": "https://github.com/IntegerAlex/kakashi/wiki",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware",
    ],
    python_requires=">=3.7",
    install_requires=get_requirements(),
    extras_require={
        "fastapi": ["fastapi>=0.68.0", "starlette>=0.14.0"],
        "flask": ["flask>=1.0.0"],
        "django": ["django>=3.0.0"],
        "web": ["fastapi>=0.68.0", "starlette>=0.14.0", "flask>=1.0.0", "django>=3.0.0"],
        "gui": ["tkinter;python_version>='3.0'"],
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.910",
            "pre-commit>=2.15.0",
            "build>=0.8.0",
            "twine>=4.0.0",
        ],
        "performance": [
            "orjson>=3.8.0",
            "uvloop>=0.17.0;sys_platform!='win32'",
        ],
        "all": [
            "fastapi>=0.68.0", 
            "starlette>=0.14.0", 
            "flask>=1.0.0", 
            "django>=3.0.0",
            "orjson>=3.8.0",
            "uvloop>=0.17.0;sys_platform!='win32'",
        ],
    },
    entry_points={
        "console_scripts": [
            "kakashi-demo=kakashi.examples.basic_usage:main",
            "kakashi-basic=kakashi.examples.basic_usage:main",
            "kakashi-web=kakashi.examples.web_framework_examples:run_all_examples",
            "kakashi-gui=kakashi.examples.gui_application_example:gui_example",
            "kakashi-cli=kakashi.examples.cli_application_example:cli_example",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=["logging", "logger", "fastapi", "middleware", "colored-logs", "performance", "singleton", "rotation"],
    license="LGPL-2.1",
)
