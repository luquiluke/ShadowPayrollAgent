# Coding Conventions

**Analysis Date:** 2026-02-15

## Naming Patterns

**Files:**
- Module files: `snake_case.py` (e.g., `calculations.py`, `llm_handler.py`, `config.py`)
- Test files: `test_<module>.py` (e.g., `test_calculations.py`, `test_models.py`)
- CSS files: `snake_case.css` (e.g., `corporate_theme.css`)

**Functions:**
- All functions use `snake_case` (e.g., `calculate_base()`, `estimate_employee_contributions()`, `get_cached_usd_ars_rate()`)
- Helper/private functions use leading underscore: `_build_tax_prompt()`, `_cached_llm_call()`
- Factory functions use `from_` prefix: `from_env()`, `create_llm_handler()`

**Variables:**
- Local variables and parameters: `snake_case` (e.g., `input_data`, `gross_monthly_ars`, `fx_rate`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_SALARY_USD`, `MIN_SALARY`, `MAX_DURATION`)
- Boolean/flag variables: prefix with `is_`, `has_`, `should_` (e.g., `has_spouse`, `validate_assignment`)
- Private module constants: `_UPPER_SNAKE_CASE`

**Types & Classes:**
- Classes use `PascalCase` (e.g., `PayrollCalculator`, `TaxLLMHandler`, `PayrollInput`)
- Exception classes end with `Error` (e.g., `LLMError`, `FXRateError`)
- Pydantic model classes use `PascalCase` (e.g., `PayrollInput`, `BaseCalculation`, `TaxCalculation`)
- Data classes use `PascalCase` (e.g., `AppConfig`)

## Code Style

**Formatting:**
- Tool: `Black` (line length: 88 characters)
- Config: `pyproject.toml` [tool.black]
- Target versions: Python 3.10, 3.11, 3.12

**Linting:**
- Tool: `Ruff`
- Rules enabled:
  - E, W: pycodestyle errors and warnings
  - F: pyflakes
  - I: isort (import sorting)
  - B: flake8-bugbear
  - C4: flake8-comprehensions
  - UP: pyupgrade
- Ignored rules: E501 (line length), B008 (function calls in defaults), C901 (complexity)
- Exception: `__init__.py` ignores F401 (unused imports allowed for re-exports)
- Config: `pyproject.toml` [tool.ruff]

**Type Checking:**
- Tool: `mypy`
- Settings: `pyproject.toml` [tool.mypy]
- Strict config: `disallow_untyped_defs = false` (not enforced)
- External packages ignored: streamlit, langchain, langchain_openai, langchain_community, openpyxl

## Import Organization

**Order:**
1. Standard library imports
2. Third-party imports (organized alphabetically within group)
3. Local application imports

**Example from `ui.py`:**
```python
import logging
from typing import Optional, Tuple

import streamlit as st

from .config import config, set_openai_api_key
from .models import PayrollInput, ShadowPayrollResult
```

**Import Style:**
- Prefer relative imports within package: `from .models import PayrollInput`
- Absolute imports for top-level: `from shadow_payroll import PayrollInput`
- Imports organized by isort (enforced by Ruff `I` rule)

**Path Aliases:**
- No path aliases configured (all imports are standard relative or absolute)

## Error Handling

**Patterns:**
- Custom exceptions inherit from `Exception`: `class LLMError(Exception):`
- Custom exceptions defined near top of modules that use them
- Specific exception types caught and handled distinctly
- Broad `Exception` catches used as safety net with logging
- Errors logged before raising/converting

**Examples from codebase:**

Custom exception definition:
```python
# From llm_handler.py
class LLMError(Exception):
    """Custom exception for LLM-related errors."""
    pass

# From utils.py
class FXRateError(Exception):
    """Custom exception for FX rate retrieval errors."""
    pass
```

Multi-level exception handling:
```python
# From utils.py - get_usd_ars_rate()
try:
    response = requests.get(config.FX_API_URL, timeout=config.FX_API_TIMEOUT)
    response.raise_for_status()
    data = response.json()
except requests.RequestException as e:
    logger.error(f"HTTP request failed for FX rate: {e}")
    return None
except (KeyError, ValueError, json.JSONDecodeError) as e:
    logger.error(f"Failed to parse FX rate response: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected error fetching FX rate: {e}")
    return None
```

Nested try-except for clear error context:
```python
# From llm_handler.py - calculate_tax()
try:
    raw_response = self._cached_llm_call(prompt)
    cleaned_response = clean_llm_json_response(raw_response)

    try:
        response_data = json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        logger.debug(f"Raw response: {raw_response}")
        raise ValueError(f"LLM returned invalid JSON: {e}\n...")

    try:
        tax_calc = TaxCalculation(...)
    except KeyError as e:
        logger.error(f"Missing required field in LLM response: {e}")
        raise ValueError(f"LLM response missing required field: {e}\n...")
```

**Validation:**
- Input validation done via Pydantic validators in models
- Business logic validation in dedicated functions: `validate_calculation_inputs()`
- Validators use `@validator` decorator (Pydantic v1 syntax - note: codebase uses v1 despite requiring v2)
- Raise `ValueError` or `ValidationError` with descriptive messages

## Logging

**Framework:** Python's standard `logging` module

**Setup:** Each module initializes logger at module level:
```python
import logging
logger = logging.getLogger(__name__)
```

**Log Levels:**
- `logger.debug()` - Detailed diagnostic info (e.g., "Cleaned LLM response", validation passed)
- `logger.info()` - Main flow events (e.g., "Calculating base shadow payroll", "Tax calculation successful")
- `logger.warning()` - Unexpected but handled situations
- `logger.error()` - Error conditions without raising (e.g., "HTTP request failed", "Failed to parse response")

**Patterns:**
- Info logs include context/values: `logger.info(f"Calculating base shadow payroll: salary=${input_data.salary_usd}, fx_rate={input_data.fx_rate}")`
- Error logs include exception message: `logger.error(f"OpenAI API error: {e}")`
- Debug logs truncate large data: `logger.debug(f"Cleaned LLM response: {text[:100]}...")`

**Configuration:**
- Log level: `config.LOG_LEVEL` (default: "INFO")
- Log format: `config.LOG_FORMAT` (default: "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
- Set up in `app.py`: `logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), ...)`

## Comments

**When to Comment:**
- Complex business logic or non-obvious calculations
- References to external requirements (Argentine tax law, PE thresholds)
- Trade-offs or assumptions about data
- Algorithm explanations where intent isn't obvious from code

**When NOT to Comment:**
- Self-documenting code (good function names explain intent)
- Simple assignments: `gross = salary + benefits`

**Docstring Style:**
- All modules have module-level docstrings (summary + purpose)
- All classes have class docstrings explaining responsibility
- All public functions have docstrings with Args, Returns, Raises, Example sections
- Private functions may have brief docstrings if complex

**Docstring Format:**
```python
def get_usd_ars_rate() -> Optional[Dict[str, Any]]:
    """
    Fetch USD to ARS exchange rate from external API.

    Uses open.er-api.com (free, no API key required).
    Implements caching via Streamlit's cache mechanism.

    Returns:
        Optional[Dict[str, Any]]: Dictionary containing:
            - rate (float): The exchange rate
            - date (str): Last update timestamp
            - source (str): Data source name
        Returns None if request fails.

    Raises:
        FXRateError: If API returns invalid data

    Example:
        >>> fx_data = get_usd_ars_rate()
        >>> if fx_data:
        ...     print(f"Rate: {fx_data['rate']} ARS/USD")
    """
```

## Function Design

**Size:** Most functions are 10-30 lines. Longer functions (30+ lines) perform multiple distinct operations with clear sections.

**Parameters:**
- Use type hints for all parameters and return values
- Complex parameters often use Pydantic models instead of multiple primitives
- Static methods used for stateless utility functions: `@staticmethod`
- Avoid function calls in default arguments (Ruff B008 rule)

**Return Values:**
- Explicit return types on all functions
- Optional returns explicitly typed: `Optional[Type]` (not implicit None)
- Union types used when needed: `Dict[str, Any]`
- Calculation functions return Pydantic models: `BaseCalculation`, `TaxCalculation`
- Utility functions may return `None` on failure with graceful handling

**Example of static method pattern:**
```python
class PayrollCalculator:
    @staticmethod
    def calculate_base(input_data: PayrollInput) -> BaseCalculation:
        """Calculate base shadow payroll amounts."""
        # ...implementation
```

## Module Design

**Exports:**
- Public functions/classes have no leading underscore
- Private implementation details prefixed with underscore
- `__init__.py` files re-export main classes via relative imports

**Module Responsibilities:**
- `config.py` - Configuration, constants, and environment overrides (AppConfig class)
- `models.py` - Pydantic data models and field validation
- `calculations.py` - Deterministic business logic, no I/O
- `utils.py` - Helper functions (FX fetching, formatting, validation utilities)
- `llm_handler.py` - LLM integration, prompt building, response parsing
- `excel_exporter.py` - Excel report generation
- `ui.py` - Streamlit UI components and page rendering

**Single Responsibility:**
- Each module has one primary concern
- PayrollCalculator in calculations.py handles only deterministic math
- TaxLLMHandler in llm_handler.py handles only LLM interactions
- No god objects or modules doing too much

## Dataclass vs Pydantic

**Use `@dataclass`:**
- For simple configuration holding (e.g., `AppConfig` in `config.py`)
- When no validation needed
- Mutable by default (good for config)

**Use Pydantic `BaseModel`:**
- For all domain data models requiring validation
- For API request/response contracts
- Input validation always via Pydantic
- Frozen models (`frozen = True` in Config) for immutable results: `BaseCalculation`, `TaxCalculation`
- Mutable models (`validate_assignment = True` in Config) for user input: `PayrollInput`

## Pre-commit Integration

**Hooks configured in `.pre-commit-config.yaml`:**
1. trailing-whitespace - Removes trailing whitespace
2. end-of-file-fixer - Ensures single newline at EOF
3. check-yaml, check-json, check-toml - YAML/JSON/TOML validation
4. check-added-large-files - Prevents committing large files (>1000KB)
5. debug-statements - Detects debugger/breakpoint statements
6. black - Code formatting (auto-fix)
7. ruff - Linting with auto-fix (`--fix --exit-non-zero-on-fix`)
8. mypy - Type checking (skips tests)

**To run locally:**
```bash
pre-commit run --all-files
```

**Important:** Hooks run automatically before commit if installed (`pre-commit install`)

---

*Convention analysis: 2026-02-15*
