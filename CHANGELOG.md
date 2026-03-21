## Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2026-03-

### Added
- `LOG_LEVEL_DEBUG`, `LOG_LEVEL_INFO`, `LOG_LEVEL_WARNING`, `LOG_LEVEL_ERROR`, and `LOG_LEVEL_CRITICAL` named constants exported from the top-level package, replacing bare integer literals throughout the API.
- `AsyncLogger.close()` method for an explicit per-instance best-effort flush before discarding an async logger.
- `CONTRIBUTING.md` with setup, testing, style, and pull-request guidelines (the README linked to this file but it was previously missing).

### Changed
- `shutdown_async_logging` is now registered with `atexit` so buffered async messages are flushed when the interpreter exits rather than being silently dropped.
- `shutdown_async_logging()` now drains the queue via a `None` sentinel and waits for the background worker to finish before returning, ensuring pending messages are processed.
- `AsyncLogger.flush()` and `AsyncLogger.close()` docstrings clarified to accurately describe the best-effort, timing-based nature of the operation.
- Removed legacy root-level `__init__.py` that shadowed the `kakashi/` package in editable installs.
- Removed `setup.py`; `pyproject.toml` is now the single canonical build configuration.

### Fixed
- README license text corrected from MIT to LGPL-2.1, matching the `LICENSE` file and packaging metadata.

## [0.2.1] - 2026-02-05

### Changed
- Use `orjson` by default for structured logging for improved performance.
- Adjusted GUI extra so that the tkinter dependency is handled correctly.

### Fixed
- Corrected `NOTICE` to reference the **LGPL-2.1** license instead of MIT for the software source code, while keeping branding restrictions unchanged.
- Improved stability and CI tests, including fixes for long-running performance and stability test suites.

## [0.2.0] - 2025-08-27

### Added
- Initial `pyproject.toml`-based build configuration and packaging metadata.
- Documentation site structure and initial guides for configuration, installation, and usage.
- Performance benchmarks and published benchmark results.

### Changed
- Refined documentation content (README and docs) for clarity and SEO.
- Updated download and marketing assets, including badges and call-to-action elements.
- Introduced a `NOTICE` file to clearly separate software licensing from branding restrictions.

## [0.1.0] - 2025-08-22

### Added
- Initial public release of Kakashi with core logging functionality.
- Support for common Python web frameworks (FastAPI, Flask, Django) via integration examples.
- Console entry points for basic, web, GUI, and CLI logging demos.

