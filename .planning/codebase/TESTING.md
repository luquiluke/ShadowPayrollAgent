# Testing Patterns

**Analysis Date:** 2026-02-06

## Test Framework

**Runner:**
- Framework: `pytest`
- Version: Not pinned in visible config (installed via requirements.txt)
- Config file: `pytest.ini` and `pyproject.toml` [tool.pytest.ini_options]

**Assertion Library:**
- Built-in `assert` statements with pytest enhancements
- `pytest.approx()` for floating-point comparisons: `assert safe_divide(10.0, 3.0) == pytest.approx(3.333333, rel=1e-5)`
- `pytest.raises()` for exception testing: `with pytest.raises(ValueError, match="Salary must be between"):`

**Run Commands:**
```bash
pytest                          # Run all tests with verbose output
pytest -v                       # Verbose output
pytest --tb=short              # Short traceback format
pytest --cov=src/shadow_payroll # With coverage report
pytest --cov-report=html       # Generate HTML coverage report
pytest tests/                  # Run specific directory
pytest tests/test_models.py    # Run specific file
pytest -k test_calculate_base  # Run tests matching pattern
```

**Configuration Details from `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = """
    -v
    --strict-markers
    --tb=short
    --cov=src/shadow_payroll
    --cov-report=term-missing
    --cov-report=html
"""
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
]
```

## Test File Organization

**Location:**
- Co-located in separate `tests/` directory (not alongside source code)
- Directory structure mirrors source: `tests/test_<module>.py` for `src/<module>.py`

**Current test files:**
- `tests/conftest.py` - Shared fixtures
- `tests/test_models.py` - Pydantic model tests
- `tests/test_calculations.py` - Business logic tests
- `tests/test_utils.py` - Utility function tests

**Naming:**
- File: `test_<module_name>.py`
- Class: `Test<SubjectName>` (e.g., `TestPayrollCalculator`, `TestValidateCalculationInputs`)
- Method: `test_<scenario>` (e.g., `test_calculate_base_basic`, `test_negative_salary_rejected`)

**Directory Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_calculations.py     # PayrollCalculator and validation tests
├── test_models.py          # Pydantic model validation tests
└── test_utils.py           # Utility function tests
```

## Test Structure

**Suite Organization:**
All test classes group related tests. Example from `tests/test_calculations.py`:

```python
class TestPayrollCalculator:
    """Test suite for PayrollCalculator class."""

    def test_calculate_base_basic(self):
        """Test basic calculation with simple inputs."""
        # Setup
        input_data = PayrollInput(...)
        calculator = PayrollCalculator()

        # Execute
        result = calculator.calculate_base(input_data)

        # Assert
        assert result.salary_monthly_ars == 10_000_000.0
        assert result.benefits_monthly_ars == 3_000_000.0
        assert result.gross_monthly_ars == 13_000_000.0
        assert result.fx_rate == 1000.0

class TestValidateCalculationInputs:
    """Test suite for input validation."""

    def test_validate_valid_inputs(self):
        """Test validation with valid inputs."""
        # Should not raise any exception
        validate_calculation_inputs(...)
```

**Patterns:**

1. **Setup Phase:** Create test data and objects
```python
input_data = PayrollInput(
    salary_usd=120000.0,
    duration_months=12,
    housing_usd=24000.0,
    school_usd=12000.0,
    fx_rate=1000.0,
)
calculator = PayrollCalculator()
```

2. **Execution Phase:** Call the function/method under test
```python
result = calculator.calculate_base(input_data)
summary = calculator.calculate_summary(input_data, base)
```

3. **Assertion Phase:** Verify results
```python
assert result.salary_monthly_ars == 10_000_000.0
assert result.benefits_monthly_ars == 3_000_000.0
assert "gross_monthly_ars" in summary
```

4. **Teardown:** Not typically used (fixtures handle cleanup)

## Mocking

**Framework:** Not detected in codebase

**Current approach:** No external mocking library (unittest.mock, pytest-mock) observed in tests. Instead:
- Tests use real Pydantic models
- Tests use real calculation functions
- No mocking of FX API calls observed yet
- No mocking of LLM calls in existing tests

**What IS being tested:**
- Model validation (actual Pydantic validators)
- Business calculations (real PayrollCalculator methods)
- Utility functions (real functions with deterministic behavior)

**What's NOT tested yet:**
- External API calls (FX rate fetching)
- LLM integration (would need mocking)
- Streamlit UI components (would need specialized testing)

## Fixtures and Factories

**Test Data:**
Defined in `tests/conftest.py`:

```python
@pytest.fixture
def sample_payroll_input():
    """Fixture providing sample PayrollInput for tests."""
    return PayrollInput(
        salary_usd=100000.0,
        duration_months=12,
        has_spouse=True,
        num_children=2,
        housing_usd=20000.0,
        school_usd=15000.0,
        fx_rate=1000.0,
    )

@pytest.fixture
def sample_base_calculation():
    """Fixture providing sample BaseCalculation for tests."""
    return BaseCalculation(
        salary_monthly_ars=8_333_333.0,
        benefits_monthly_ars=2_916_667.0,
        gross_monthly_ars=11_250_000.0,
        fx_rate=1000.0,
    )

@pytest.fixture
def sample_tax_calculation():
    """Fixture providing sample TaxCalculation for tests."""
    return TaxCalculation(
        ganancias_monthly=500000.0,
        employee_contributions=1_912_500.0,
        net_employee=8_837_500.0,
        employer_contributions=2_700_000.0,
        total_cost_employer=13_950_000.0,
        pe_risk="Alto",
        comments="Long-term assignment exceeds 183 days. High PE risk.",
    )

@pytest.fixture
def mock_fx_data():
    """Fixture providing mock FX rate data."""
    return {
        "rate": 1000.0,
        "date": "2025-01-20T12:00:00Z",
        "source": "open.er-api.com",
    }
```

**Location:**
- Shared fixtures: `tests/conftest.py`
- Test-specific fixtures: Can be added inline in individual test files if needed

**Factory Pattern:**
- Fixtures serve as test data factories
- Each fixture returns valid test data for a specific model
- Fixtures are reusable across multiple test classes/functions

## Coverage

**Requirements:**
- Target coverage not explicitly stated
- HTML reports generated by default: `--cov-report=html`
- Terminal reports with missing line info: `--cov-report=term-missing`

**View Coverage:**
```bash
pytest --cov=src/shadow_payroll --cov-report=term-missing
pytest --cov=src/shadow_payroll --cov-report=html
# Then open htmlcov/index.html in browser
```

**Coverage Config from `pyproject.toml`:**
```toml
[tool.coverage.run]
source = ["src/shadow_payroll"]
omit = [
    "*/tests/*",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

## Test Types

**Unit Tests:**
- Scope: Individual functions, classes, and methods
- Approach: Isolated, fast, deterministic
- Examples:
  - `test_calculate_base_basic()` - Tests PayrollCalculator.calculate_base()
  - `test_negative_salary_rejected()` - Tests PayrollInput model validation
  - `test_format_positive_amount()` - Tests format_currency_ars()
- Characteristics: No external API calls, no I/O, pure computation

**Integration Tests:**
- Defined via marker but not heavily used yet
- Would test: Multiple components working together (e.g., input → calculation → result model)
- Could test: FX API integration, LLM integration
- Marker available: `@pytest.mark.integration`

**E2E Tests:**
- Not implemented
- Would require: Streamlit testing framework (streamlit.testing.v1)
- Would test: Full UI workflows

## Common Patterns

**Valid Input Testing:**
```python
def test_valid_input(self):
    """Test creating valid PayrollInput."""
    input_data = PayrollInput(
        salary_usd=100000.0,
        duration_months=12,
        has_spouse=True,
        num_children=2,
        housing_usd=20000.0,
        school_usd=15000.0,
        fx_rate=1000.0,
    )

    assert input_data.salary_usd == 100000.0
    assert input_data.duration_months == 12
    assert input_data.has_spouse is True
```

**Validation Error Testing:**
```python
def test_negative_salary_rejected(self):
    """Test negative salary is rejected."""
    with pytest.raises(ValidationError):
        PayrollInput(salary_usd=-50000.0, fx_rate=1000.0)

def test_validate_salary_too_high(self):
    """Test validation fails with excessive salary."""
    with pytest.raises(ValueError, match="Salary must be between"):
        validate_calculation_inputs(
            salary_usd=99_000_000.0,
            duration_months=12,
            housing_usd=0.0,
            school_usd=0.0,
            fx_rate=1000.0,
        )
```

**Multiple Scenario Testing:**
```python
def test_calculate_base_zero_benefits(self):
    """Test calculation with zero benefits."""
    input_data = PayrollInput(
        salary_usd=150000.0,
        duration_months=24,
        housing_usd=0.0,
        school_usd=0.0,
        fx_rate=1000.0,
    )

    calculator = PayrollCalculator()
    result = calculator.calculate_base(input_data)

    assert result.benefits_monthly_ars == 0.0
    assert result.gross_monthly_ars == result.salary_monthly_ars
```

**Boundary Testing:**
```python
def test_medium_risk_borderline(self):
    """Test medium risk for borderline durations."""
    # 6 months = 180 days (just under threshold)
    assert calculate_pe_risk_level(6) == "Bajo"

    # 7 months = 210 days (just over threshold)
    assert calculate_pe_risk_level(7) == "Medio"
```

**Floating Point Comparison:**
```python
def test_decimal_result(self):
    """Test division resulting in decimal."""
    assert safe_divide(10.0, 3.0) == pytest.approx(3.333333, rel=1e-5)
```

**Error Message Matching:**
```python
def test_error_message_includes_field_name(self):
    """Test error message includes field name."""
    with pytest.raises(ValueError, match="Salary must be positive"):
        validate_positive_number(-100.0, "Salary")
```

**Immutability Testing (Frozen Models):**
```python
def test_base_calculation_is_frozen(self):
    """Test BaseCalculation is immutable."""
    base = BaseCalculation(
        salary_monthly_ars=10_000_000.0,
        benefits_monthly_ars=2_000_000.0,
        gross_monthly_ars=12_000_000.0,
        fx_rate=1000.0,
    )

    with pytest.raises(ValidationError):
        base.fx_rate = 1200.0
```

## Test Execution Notes

**Default Test Discovery:**
- Looks in `tests/` directory
- Finds files matching `test_*.py`
- Finds classes matching `Test*`
- Finds functions matching `test_*`

**Test Markers:**
Available markers (from `pyproject.toml`):
- `@pytest.mark.unit` - For unit tests
- `@pytest.mark.integration` - For integration tests
- `@pytest.mark.slow` - For slow tests
- `--strict-markers` enforced (unknown markers cause errors)

---

*Testing analysis: 2026-02-06*
