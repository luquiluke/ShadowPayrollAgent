# Testing Patterns

**Analysis Date:** 2026-02-15

## Test Framework

**Runner:**
- Framework: `pytest` (>=8.0.0)
- Config file: `pyproject.toml` [tool.pytest.ini_options]

**Assertion Library:**
- Built-in `assert` statements with pytest enhancements
- `pytest.approx()` for floating-point comparisons
- `pytest.raises()` for exception testing with optional `match` parameter for message matching

**Run Commands:**
```bash
pytest                                    # Run all tests with default options
pytest -v                                 # Verbose output
pytest tests/test_models.py               # Run specific file
pytest tests/test_calculations.py::TestPayrollCalculator  # Run specific class
pytest -k test_calculate_base             # Run tests matching pattern
pytest --cov=src/shadow_payroll           # With coverage report
pytest --cov-report=html                  # Generate HTML coverage report
pytest --tb=short                         # Short traceback format
```

**Configuration from `pyproject.toml`:**
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

**Default behavior:**
- Always runs with verbose output (`-v`)
- Always generates coverage report
- Uses short traceback format for failures
- Enforces marker registry (unknown markers cause errors)

## Test File Organization

**Location:**
- Tests in separate `tests/` directory (not co-located with source)
- Mirrors source structure: `tests/test_<module>.py` for `src/shadow_payroll/<module>.py`

**Current test files:**
- `tests/__init__.py` - Empty package marker
- `tests/conftest.py` - Shared fixtures and configuration
- `tests/test_models.py` - Pydantic model validation (265 lines, ~18 test methods)
- `tests/test_calculations.py` - Business logic tests (201 lines, ~18 test methods)
- `tests/test_utils.py` - Utility function tests (147 lines, ~15 test methods)

**Naming conventions:**
- File: `test_<module_name>.py`
- Class: `Test<SubjectName>` (e.g., `TestPayrollCalculator`, `TestValidateCalculationInputs`)
- Method: `test_<scenario>` (e.g., `test_calculate_base_basic`, `test_negative_salary_rejected`)

**Directory structure:**
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_calculations.py     # PayrollCalculator and validate_calculation_inputs tests
├── test_models.py          # Pydantic model validation tests
└── test_utils.py           # Utility function tests
```

## Test Structure

**Test Class Organization:**
Tests grouped by subject in classes. Example from `tests/test_models.py`:

```python
class TestPayrollInput:
    """Test suite for PayrollInput model."""

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
        assert input_data.num_children == 2
```

**Typical test structure follows Arrange-Act-Assert pattern:**

1. **Arrange/Setup:** Create test data and objects
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

2. **Act/Execute:** Call the function or method under test
```python
result = calculator.calculate_base(input_data)
```

3. **Assert:** Verify results
```python
assert result.salary_monthly_ars == 10_000_000.0
assert result.benefits_monthly_ars == 3_000_000.0
assert result.gross_monthly_ars == 13_000_000.0
```

4. **Teardown:** Not typically used (fixtures handle cleanup)

## Mocking

**Framework:** Not heavily used in current tests

**Current approach:**
- Tests use real Pydantic models (not mocked)
- Tests use real calculation functions (deterministic, no external deps)
- Tests use real utility functions

**What is tested without mocking:**
- Model validation (actual Pydantic validators)
- Business calculations (real PayrollCalculator methods)
- Utility functions (real functions: format_currency_ars, calculate_pe_risk_level, etc.)

**What's NOT tested yet (would need mocking):**
- External API calls (FX rate fetching via requests)
- LLM integration (OpenAI API calls via langchain)
- Streamlit UI components (would need streamlit.testing.v1)
- Caching behavior (@st.cache_data decorator)

**Recommended mocking setup when needed:**
- Use `pytest-mock` (in requirements.txt) for fixtures
- Mock `requests.get()` for FX API testing
- Mock `ChatOpenAI.invoke()` for LLM handler testing

## Fixtures and Factories

**Shared fixtures in `tests/conftest.py`:**

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

**Fixture usage:**
- Fixtures are injected as function parameters
- Single fixture instance reused per test function (function scope)
- Can be combined: `def test_method(self, sample_payroll_input, sample_base_calculation):`

**Location:**
- Shared fixtures: `tests/conftest.py` (available to all tests)
- Test-specific fixtures: Can add directly in individual test files if needed

## Coverage

**Configuration from `pyproject.toml`:**
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

**Generate coverage reports:**
```bash
pytest --cov=src/shadow_payroll --cov-report=term-missing
# Shows missing line numbers in terminal

pytest --cov=src/shadow_payroll --cov-report=html
# Opens htmlcov/index.html in browser for detailed view
```

**Current coverage:**
- Target coverage: Not explicitly stated
- Reports generated by default on every test run
- HTML reports saved to `htmlcov/` directory

## Test Types

**Unit Tests (Dominant):**
- Scope: Individual functions, classes, and methods
- Approach: Isolated, fast, deterministic
- Examples:
  - `test_calculate_base_basic()` - Tests PayrollCalculator.calculate_base()
  - `test_negative_salary_rejected()` - Tests PayrollInput model validation
  - `test_format_positive_amount()` - Tests format_currency_ars()
- Characteristics: No external API calls, no I/O, pure computation

**Integration Tests (Defined but not used):**
- Defined via marker: `@pytest.mark.integration`
- Would test: Multiple components working together (e.g., input → validation → calculation → result model)
- Could test: FX API integration, LLM integration
- Not yet implemented (no tests marked with `@pytest.mark.integration`)

**E2E Tests:**
- Not implemented
- Would require: Streamlit testing framework (streamlit.testing.v1)
- Would test: Full UI workflows end-to-end

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

**Pydantic ValidationError Testing:**
```python
def test_negative_salary_rejected(self):
    """Test negative salary is rejected."""
    with pytest.raises(ValidationError):
        PayrollInput(salary_usd=-50000.0, fx_rate=1000.0)

def test_unreasonably_high_fx_rate_rejected(self):
    """Test unreasonably high FX rate is rejected."""
    with pytest.raises(ValidationError, match="unreasonably high"):
        PayrollInput(fx_rate=200000.0)
```

**ValueError Testing with Message Matching:**
```python
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

**Business Logic Testing:**
```python
def test_calculate_summary(self):
    """Test calculation summary generation."""
    input_data = PayrollInput(
        salary_usd=120000.0,
        duration_months=12,
        housing_usd=24000.0,
        school_usd=12000.0,
        fx_rate=1000.0,
    )

    calculator = PayrollCalculator()
    base = calculator.calculate_base(input_data)
    summary = calculator.calculate_summary(input_data, base)

    assert summary["duration_months"] == 12
    assert summary["duration_days"] == 360
    assert "gross_monthly_ars" in summary
    assert "total_cost_assignment_ars" in summary
```

**Boundary Testing:**
```python
def test_medium_risk_borderline(self):
    """Test medium risk for borderline durations."""
    # 6 months = 180 days (just under 183 day threshold)
    assert calculate_pe_risk_level(6) == "Bajo"

    # 7 months = 210 days (over threshold)
    assert calculate_pe_risk_level(7) == "Medio"
```

**Floating Point Comparison:**
```python
def test_decimal_result(self):
    """Test division resulting in decimal."""
    assert safe_divide(10.0, 3.0) == pytest.approx(3.333333, rel=1e-5)
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

**Multiple Scenarios Testing:**
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

**Helper Function Testing:**
```python
def test_clean_json_with_backticks(self):
    """Test cleaning JSON wrapped in markdown fences."""
    raw = '```json\n{"key": "value"}\n```'
    cleaned = clean_llm_json_response(raw)
    assert cleaned == '{"key": "value"}'

def test_clean_already_clean_json(self):
    """Test cleaning already clean JSON."""
    raw = '{"key": "value"}'
    cleaned = clean_llm_json_response(raw)
    assert cleaned == '{"key": "value"}'
```

## Test Execution Notes

**Default test discovery:**
- Finds files matching `test_*.py` in `tests/` directory
- Finds classes matching `Test*`
- Finds methods matching `test_*`

**Available markers (from pyproject.toml):**
- `@pytest.mark.unit` - For unit tests
- `@pytest.mark.integration` - For integration tests
- `@pytest.mark.slow` - For slow/long-running tests
- `--strict-markers` enforced (unknown markers cause test failure)

**Run tests by marker:**
```bash
pytest -m unit              # Run only unit tests
pytest -m integration       # Run only integration tests
pytest -m "not slow"        # Run all except slow tests
```

## Known Test Gaps

**Not tested yet (identified in CONCERNS.md):**
1. **LLM response parsing** - `llm_handler.py` calculate_tax() method
   - JSON parsing and field extraction logic not covered
   - Error handling for malformed LLM responses untested

2. **FX rate caching** - `utils.py` get_cached_usd_ars_rate()
   - Streamlit cache behavior not testable without mocking
   - Cache invalidation logic untested

3. **UI components** - `ui.py` all functions
   - Streamlit components require specialized testing
   - Would need `streamlit.testing.v1` framework

4. **Excel export** - `excel_exporter.py`
   - File generation not tested
   - Missing in test suite entirely

5. **Error recovery** - All modules
   - Graceful degradation not systematically tested
   - Fallback paths partially untested

---

*Testing analysis: 2026-02-15*
