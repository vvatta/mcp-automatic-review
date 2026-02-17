# Contributing to MCP Malware Sandbox

Thank you for your interest in contributing to the MCP Malware Sandbox!

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check if the issue already exists
2. Create a new issue with a clear title and description
3. Include steps to reproduce (for bugs)
4. Include expected vs actual behavior

### Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write/update tests as needed
5. Ensure all tests pass (`pytest tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings to functions and classes
- Keep functions focused and small
- Write clear commit messages

### Testing

- Add tests for new features
- Ensure existing tests pass
- Aim for high test coverage
- Test edge cases

### Documentation

- Update README.md if needed
- Add docstrings to new code
- Update architecture docs for significant changes
- Include examples for new features

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/mcp-automatic-review.git
cd mcp-automatic-review

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

## Adding New Features

### Adding a New Attack Vector

1. Update `src/interrogator/llm_fuzzer.py`
2. Add the attack type to `AttackType` enum
3. Implement payload generation method
4. Add tests in `tests/test_llm_fuzzer.py`

### Adding a New Monitor

1. Update `src/monitor/behavior_monitor.py`
2. Add monitoring method
3. Update `generate_report()` to include new data
4. Add tests

## Questions?

Open an issue or discussion on GitHub.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
