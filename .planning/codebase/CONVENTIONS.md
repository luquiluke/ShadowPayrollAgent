# Coding Conventions

**Analysis Date:** 2026-02-06

## Naming Patterns

**Files:**
- Module files: `snake_case.py` (e.g., `calculations.py`, `llm_handler.py`, `config.py`)
- Test files: `test_<module>.py` (e.g., `test_calculations.py`, `test_models.py`)
- CSS files: `snake_case.css` (e.g., `corporate_theme.css`)

**Functions:**
- All functions use `snake_case` (e.g., `calculate_base()`, `estimate_employee_contributions()`, `get_cached_usd_ars_rate()`)
- Helper/private functions use leading underscore: `_build_tax_prompt()`, `_validate_inputs()`
- Factory functions use `from_` prefix: `from_env()`

**Variables:**
- Local variables and parameters: `snake_case` (e.g., `input_data`, `gross_monthly_ars`, `fx_rate`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_SALARY_USD`, `MIN_SALARY`, `MAX_DURATION`)
- Private module constants: `_UPPER_SNAKE_CASE`

**Types & Classes:**
- Classes use `PascalCase` (e.g., `PayrollCalculator`, `TaxLLMHandler`, `PayrollInput`)
- Exception classes end with `Error` (e.g., `LLMError`, `FXRateError`)
- Pydantic model classes use `PascalCase` (e.g., `PayrollInput`, `BaseCalculation`, `TaxCalculation`)

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
- Exception: `__init__.py` ignores F401 (unused imports)
- Config: `pyproject.toml` [tool.ruff]

**Type Checking:**
- Tool: `mypy`
- Settings: `pyproject.toml` [tool.mypy]
- Strict config: `disallow_untyped_defs = false` (not enforced)
- External packages ignored: streamlit, langchain, openpyxl

## Import Organization

**Order:**
1. Standard library imports
2. Third-party imports
3. Local application imports

**Example from `calculations.py`:**
```python
import logging
from typing import Dict, Any

from .models import PayrollInput, BaseCalculation
from .config import config
```

**Example from `models.py`:**
```python
from typing import Optional
from pydantic import BaseModel, Field, validator, ConfigDict

from .config import config
```

**Path Aliases:**
- Relative imports used throughout: `from .config import config`
- No absolute path aliases configured

## Error Handling

**Patterns:**
- Custom exceptions defined near the top of modules that use them
- All custom exceptions inherit from `Exception`: `class LLMError(Exception):`
- Docstrings explain when exceptions are raised
- Specific exception types caught and handled in different ways

**Examples:**
```python
# From llm_handler.py
class LLMError(Exception):
    """Custom exception for LLM-related errors."""
    pass

# From utils.py
class FXRateError(Exception):
    """Custom exception for FX rate retrieval errors."""
    pass

# From calculations.py - validation raising ValueError
if salary_usd < config.MIN_SALARY or salary_usd > config.MAX_SALARY:
    raise ValueError(
        f"Salary must be between {config.MIN_SALARY} and {config.MAX_SALARY}"
    )

# Exception catching in utils.py
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

## Logging

**Framework:** Python's standard `logging` module

**Setup:** Each module initializes a logger:
```python
import logging
logger = logging.getLogger(__name__)
```

**Patterns:**
- Info level for main flow events: `logger.info(f"Calculating base shadow payroll: salary=${input_data.salary_usd}, fx_rate={input_data.fx_rate}")`
- Error level for error conditions: `logger.error(f"HTTP request failed for FX rate: {e}")`
- Debug level for detailed diagnostic info: `logger.debug("Input validation passed")`
- All logs include context/values via f-strings
- Config location: `src/shadow_payroll/config.py` - LOG_LEVEL and LOG_FORMAT settings

## Comments

**When to Comment:**
- Complex business logic or non-obvious calculations
- Assumptions about data or third-party APIs
- References to external requirements (e.g., Argentine tax law, PE thresholds)

**Example from `calculations.py` (lines 62-64):**
```python
# Convert annual benefits to monthly ARS
total_benefits_usd = input_data.housing_usd + input_data.school_usd
benefits_monthly_ars = (total_benefits_usd / 12) * input_data.fx_rate
```

**Example from `utils.py` (lines 150-152):**
```python
# Based on Argentine tax law, assignments longer than 183 days
# (approximately 6 months) may trigger PE concerns.
```

**JSDoc/TSDoc:**
- Not used (Python project). Uses Python docstrings instead.

**Docstring Style:**
- All modules have module-level docstrings (3 lines, summary + purpose)
- All classes have class docstrings explaining purpose and responsibility
- All functions have docstrings with Args, Returns, and optional Example sections
- Docstrings follow Google/NumPy convention

**Examples:**

Module docstring (from `models.py`):
```python
"""
Pydantic models for data validation and type safety.

This module defines all data models used in the Shadow Payroll Calculator
with comprehensive validation rules.
"""
```

Class docstring (from `calculations.py`):
```python
class PayrollCalculator:
    """
    Handles shadow payroll base calculations.

    This class performs the deterministic portion of shadow payroll
    calculations, converting USD amounts to ARS and computing
    monthly breakdowns.
    """
```

Function docstring (from `calculations.py`):
```python
@staticmethod
def calculate_base(input_data: PayrollInput) -> BaseCalculation:
    """
    Calculate base shadow payroll amounts.

    Performs currency conversion and monthly breakdown calculations.
    This is the deterministic part that doesn't require LLM.

    Args:
        input_data: Validated payroll input data

    Returns:
        BaseCalculation: Base calculation results

    Example:
        >>> from models import PayrollInput
        >>> input_data = PayrollInput(
        ...     salary_usd=400000,
        ...     duration_months=36,
        ...     housing_usd=50000,
        ...     school_usd=30000,
        ...     fx_rate=1000
        ... )
        >>> calc = PayrollCalculator()
        >>> result = calc.calculate_base(input_data)
        >>> print(result.gross_monthly_ars)
    """
```

## Function Design

**Size:** Most functions are 10-30 lines. Longer functions (30+ lines) perform multiple distinct operations and include clear sections with comments.

**Parameters:**
- Use type hints for all parameters: `def calculate_base(input_data: PayrollInput) -> BaseCalculation:`
- Complex parameters often use Pydantic models rather than multiple primitive arguments
- Static methods used for stateless utility functions: `@staticmethod`

**Return Values:**
- Explicit return types on all functions
- Optional returns use `Optional[Type]`: `Optional[Dict[str, Any]]`
- Union types used when returning different types: Not observed in this codebase
- Functions that fail return `None` rather than raising exceptions (e.g., `get_usd_ars_rate()` returns `None` on failure)
- Calculation functions return Pydantic models for type safety: `BaseCalculation`, `TaxCalculation`

## Module Design

**Exports:**
- Modules export their main classes and functions
- `__init__.py` files typically empty or import main classes (not observed as heavily used here)
- No barrel files (`index.ts` style) used

**Module Purpose & Organization:**
- `models.py`: All Pydantic data models
- `config.py`: Configuration management and environment variables
- `calculations.py`: Business logic for deterministic calculations
- `llm_handler.py`: LLM integration and prompting
- `utils.py`: Utility functions (FX rates, formatting, validation)
- `ui.py`: Streamlit UI components
- `excel_exporter.py`: Excel export functionality

**Validation:**
- Input validation done via Pydantic validators in models
- Business logic validation in dedicated functions: `validate_calculation_inputs()`
- Validators use `@validator` decorator from Pydantic: `@validator("salary_usd", "housing_usd", "school_usd")`

**Configuration:**
- All configuration centralized in `config.py`
- Config created as singleton: `config = AppConfig.from_env()`
- Configuration class uses `@dataclass` with class attributes for settings
- Environment variable overrides via `from_env()` class method
- Two separate functions for API key: `get_openai_api_key()` and `set_openai_api_key()`

## Data Validation

**Pydantic Models:**
- All input data models extend `BaseModel`
- Frozen models use `frozen = True` in Config for immutability: `BaseCalculation`, `TaxCalculation`
- Mutable models use `validate_assignment = True`: `PayrollInput`
- Field constraints using Pydantic Field: `ge` (greater than or equal), `le` (less than or equal), `gt` (greater than)

**Example:**
```python
class PayrollInput(BaseModel):
    salary_usd: float = Field(
        default=config.DEFAULT_SALARY_USD,
        ge=config.MIN_SALARY,
        le=config.MAX_SALARY,
        description="Annual home salary in USD",
    )
```

**Custom Validators:**
- Decorated with `@validator` accepting field name(s)
- Check specific business rules beyond simple constraints
- Raise `ValueError` with descriptive message

**Example:**
```python
@validator("fx_rate")
def validate_fx_rate(cls, v: float) -> float:
    """Ensure FX rate is reasonable."""
    if v <= 0:
        raise ValueError("FX rate must be positive")
    if v < 1.0:
        raise ValueError("ARS/USD rate seems too low (expected > 1)")
    if v > 100000:
        raise ValueError("ARS/USD rate seems unreasonably high")
    return v
```

---

*Convention analysis: 2026-02-06*
