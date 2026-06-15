# Contributing to Kakashi

Thank you for your interest in contributing! The following guidelines will help you get started.

## Reporting Issues

- Search [existing issues](https://github.com/IntegerAlex/kakashi/issues) before opening a new one.
- Include a minimal, reproducible example and your Python version when reporting bugs.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/IntegerAlex/kakashi.git
cd kakashi

# Install with development dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Code Style

- Format code with [black](https://black.readthedocs.io/): `black .`
- Lint with [flake8](https://flake8.pycqa.org/): `flake8 kakashi/`
- Type-check with [mypy](https://mypy.readthedocs.io/): `mypy kakashi/`

## Submitting a Pull Request

1. Fork the repository and create a feature branch from `main`.
2. Write tests for any new functionality.
3. Ensure all tests, lint, and type checks pass.
4. Open a pull request with a clear description of the change.

## License

By contributing you agree that your code will be released under the project's [LGPL-2.1 license](LICENSE).
