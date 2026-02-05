## Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

