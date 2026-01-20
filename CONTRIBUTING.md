# Contributing to Shadow Payroll Calculator

Thank you for your interest in contributing to the Shadow Payroll Calculator! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ShadowPayrollAgent.git
   cd ShadowPayrollAgent
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Quality

We use several tools to maintain code quality:

### Black (Code Formatting)

Format your code with Black:
```bash
black src/ tests/
```

### Ruff (Linting)

Lint your code with Ruff:
```bash
ruff check src/ tests/
```

To auto-fix issues:
```bash
ruff check --fix src/ tests/
```

### MyPy (Type Checking)

Run type checking:
```bash
mypy src/shadow_payroll
```

### Pre-commit Hooks

Pre-commit hooks will run automatically before each commit. To run manually:
```bash
pre-commit run --all-files
```

## Testing

### Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src/shadow_payroll --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_calculations.py
```

Run specific test:
```bash
pytest tests/test_calculations.py::TestPayrollCalculator::test_calculate_base_basic
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names following the pattern `test_<what_is_being_tested>`
- Group related tests in classes
- Use fixtures from `conftest.py` for common test data
- Aim for high test coverage (>80%)

Example test:
```python
def test_calculate_base_with_valid_inputs(sample_payroll_input):
    """Test base calculation with valid inputs."""
    calculator = PayrollCalculator()
    result = calculator.calculate_base(sample_payroll_input)

    assert result.gross_monthly_ars > 0
    assert result.fx_rate == sample_payroll_input.fx_rate
```

## Submitting Changes

### Commit Messages

Follow these guidelines for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add input validation for FX rates

- Validate FX rate is positive
- Reject unreasonably high/low rates
- Add comprehensive tests

Closes #123
```

### Pull Request Process

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Your commit message"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request on GitHub

5. Ensure all CI checks pass

6. Request review from maintainers

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows the project style (Black, Ruff pass)
- [ ] All tests pass (`pytest`)
- [ ] New code has tests
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive
- [ ] Pre-commit hooks pass

## Code Style

### Python Style

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all public functions/classes
- Keep functions focused and single-purpose
- Prefer explicit over implicit

### Docstring Format

Use Google-style docstrings:

```python
def calculate_something(value: float, rate: float) -> float:
    """
    Calculate something important.

    Args:
        value: The base value
        rate: The rate to apply

    Returns:
        float: The calculated result

    Raises:
        ValueError: If value is negative
    """
    if value < 0:
        raise ValueError("Value must be positive")
    return value * rate
```

### Project Structure

```
ShadowPayrollAgent/
├── src/
│   └── shadow_payroll/
│       ├── __init__.py
│       ├── config.py         # Configuration
│       ├── models.py          # Pydantic models
│       ├── calculations.py    # Business logic
│       ├── llm_handler.py     # LLM integration
│       ├── utils.py           # Utilities
│       ├── excel_exporter.py  # Excel generation
│       └── ui.py              # Streamlit UI
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Test fixtures
│   ├── test_calculations.py
│   ├── test_models.py
│   └── test_utils.py
├── app.py                    # Main entry point
├── requirements.txt          # Dependencies
├── pyproject.toml           # Project config
└── README.md                # Documentation
```

## Questions?

If you have questions, please:

1. Check existing issues
2. Open a new issue with the "question" label
3. Be specific and provide context

Thank you for contributing!
