# Codebase Structure

**Analysis Date:** 2026-02-06

## Directory Layout

```
ShadowPayrollAgent-refactored/
├── app.py                              # Main Streamlit entry point
├── requirements.txt                    # Python dependencies
├── README.md                           # Project documentation
├── CONTRIBUTING.md                     # Contribution guidelines
├── REFACTORING_SUMMARY.md              # v2.0 refactoring notes
├── .planning/
│   └── codebase/                       # GSD planning documents
├── src/
│   ├── __init__.py
│   └── shadow_payroll/
│       ├── __init__.py                 # Package exports
│       ├── app.py                      # Deprecated entry point
│       ├── models.py                   # Pydantic data models
│       ├── calculations.py             # Payroll calculation logic
│       ├── llm_handler.py              # LLM integration with OpenAI
│       ├── ui.py                       # Streamlit UI components
│       ├── config.py                   # Configuration management
│       ├── utils.py                    # Utility functions
│       ├── excel_exporter.py           # Excel report generation
│       └── corporate_theme.css         # Streamlit custom styling
└── tests/
    ├── __init__.py
    ├── conftest.py                     # Pytest fixtures
    ├── test_calculations.py            # Calculator unit tests
    ├── test_models.py                  # Model validation tests
    └── test_utils.py                   # Utility function tests
```

## Directory Purposes

**Root Directory:**
- Purpose: Project root with entry point and configuration files
- Contains: Streamlit app entry point, dependency lists, documentation

**src/shadow_payroll/:**
- Purpose: Main package containing all application logic
- Contains: Business logic, UI, integrations, utilities
- Key files: All production code except entry point

**tests/:**
- Purpose: Pytest test suite with fixtures and test modules
- Contains: Unit tests for calculations, models, utilities
- Key files: conftest.py for shared fixtures

**docs/:**
- Purpose: Documentation artifacts (if present)
- Contains: User guides, API documentation

## Key File Locations

**Entry Points:**
- `app.py`: Main Streamlit application entry point (run with `streamlit run app.py`)
- `src/shadow_payroll/__init__.py`: Package exports for programmatic use

**Configuration:**
- `src/shadow_payroll/config.py`: Centralized AppConfig dataclass with environment variable support
- `requirements.txt`: Python package dependencies (v2.0 with LangChain/OpenAI)

**Core Logic:**
- `src/shadow_payroll/models.py`: Pydantic models for data validation (PayrollInput, BaseCalculation, TaxCalculation, ShadowPayrollResult)
- `src/shadow_payroll/calculations.py`: PayrollCalculator class with base calculation and contribution estimation methods
- `src/shadow_payroll/llm_handler.py`: TaxLLMHandler class for OpenAI integration with prompt engineering

**User Interface:**
- `src/shadow_payroll/ui.py`: All Streamlit UI functions (forms, results display, sidebar)
- `src/shadow_payroll/corporate_theme.css`: Custom CSS styling for professional appearance

**Integration & Export:**
- `src/shadow_payroll/excel_exporter.py`: ExcelExporter class generating styled Excel reports
- `src/shadow_payroll/utils.py`: FX rate fetching, JSON cleaning, PE risk calculation

**Testing:**
- `tests/conftest.py`: Pytest fixtures (sample_payroll_input, sample_base_calculation, sample_tax_calculation, mock_fx_data)
- `tests/test_calculations.py`: Tests for PayrollCalculator and input validation
- `tests/test_models.py`: Tests for Pydantic model validation
- `tests/test_utils.py`: Tests for utility functions

## Naming Conventions

**Files:**
- Snake case: `shadow_payroll.py`, `llm_handler.py`, `excel_exporter.py`
- Test files: `test_<module>.py` pattern matching module being tested
- Configuration: `config.py`, `<theme>.css`

**Directories:**
- Snake case: `shadow_payroll/`, `src/`, `tests/`
- Purpose-driven: `/tests`, `/docs`

**Python Classes:**
- PascalCase: `PayrollCalculator`, `TaxLLMHandler`, `ExcelExporter`, `PayrollInput`, `ShadowPayrollResult`

**Functions:**
- Snake case: `calculate_base()`, `render_input_form()`, `get_cached_usd_ars_rate()`

**Constants:**
- UPPER_SNAKE_CASE in config: `DEFAULT_SALARY_USD`, `LLM_MODEL`, `FX_CACHE_TTL`

**Private Methods/Attributes:**
- Leading underscore: `_build_tax_prompt()`, `_cached_llm_call()`, `_apply_styling()`

## Where to Add New Code

**New Feature (e.g., new calculation type):**
- Primary code: `src/shadow_payroll/calculations.py` - Add static method to PayrollCalculator
- Models: `src/shadow_payroll/models.py` - Add Pydantic model if new data structure needed
- UI: `src/shadow_payroll/ui.py` - Add render function for new input/output section
- Tests: `tests/test_calculations.py` - Add test class and cases

**New Component/Module:**
- Implementation: Create new file in `src/shadow_payroll/<component_name>.py`
- Export: Add to `src/shadow_payroll/__init__.py` in `__all__` list
- Tests: Create `tests/test_<component_name>.py` with same module structure
- Integration: Import and use in appropriate layer (UI, calculations, or main)

**Utilities:**
- Shared helpers: `src/shadow_payroll/utils.py`
- Cross-cutting functions: FX fetching, formatting, validation helpers
- Pattern: Top-level function or utility class

**UI Components:**
- New forms/sections: Add function to `src/shadow_payroll/ui.py` following `render_*()` convention
- Styling: Update `src/shadow_payroll/corporate_theme.css` for theme-wide changes
- Session state: Access/set via `st.session_state` dict in UI functions

**Configuration Values:**
- Add field to `AppConfig` dataclass in `src/shadow_payroll/config.py`
- Set default value and type
- Add env variable override in `from_env()` method if needed
- Document the configuration in docstring

**External Integrations:**
- LLM calls: Use `src/shadow_payroll/llm_handler.py::TaxLLMHandler` pattern
- FX data: Use `src/shadow_payroll/utils.py::get_cached_usd_ars_rate()` pattern
- New API: Create handler class in new module, follow error handling patterns

## Special Directories

**.planning/codebase/:**
- Purpose: GSD (Generate-Scaffold-Deploy) planning documents (architecture, structure, conventions, testing, concerns)
- Generated: Yes (by GSD mapper commands)
- Committed: Yes (tracked in git for future reference)

**.pytest_cache/:**
- Purpose: Pytest cache for test discovery and run optimization
- Generated: Yes (auto-created by pytest)
- Committed: No (in .gitignore)

**src/shadow_payroll_calculator.egg-info/:**
- Purpose: Package metadata generated during editable install
- Generated: Yes (by pip install -e .)
- Committed: No (in .gitignore)

## Import Patterns

**Absolute imports (preferred):**
```python
from shadow_payroll.models import PayrollInput, ShadowPayrollResult
from shadow_payroll.config import config
from shadow_payroll.calculations import PayrollCalculator
```

**Relative imports (within package):**
```python
from .models import PayrollInput
from .config import config
```

**Entry point special handling:**
```python
# app.py adds src to path for package discovery
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
from shadow_payroll.ui import ...
```

## Module Dependencies Graph

```
app.py
  └─> shadow_payroll.ui
      ├─> shadow_payroll.models
      ├─> shadow_payroll.config
      ├─> shadow_payroll.calculations
      │   ├─> shadow_payroll.models
      │   └─> shadow_payroll.config
      ├─> shadow_payroll.llm_handler
      │   ├─> shadow_payroll.models
      │   ├─> shadow_payroll.config
      │   └─> shadow_payroll.utils
      ├─> shadow_payroll.excel_exporter
      │   └─> shadow_payroll.models
      └─> shadow_payroll.utils
          ├─> shadow_payroll.config
          └─> (external: requests, streamlit)

shadow_payroll.__init__
  ├─> shadow_payroll.config
  ├─> shadow_payroll.models
  ├─> shadow_payroll.calculations
  ├─> shadow_payroll.llm_handler
  ├─> shadow_payroll.utils
  └─> shadow_payroll.excel_exporter

tests/
  ├─> shadow_payroll.* (all modules)
  └─> pytest fixtures in conftest.py
```

## File Size Reference

**Core modules:**
- `models.py` (~230 lines): Data structures with validation
- `ui.py` (~340 lines): UI components and orchestration
- `calculations.py` (~210 lines): Business logic
- `llm_handler.py` (~240 lines): LLM integration
- `utils.py` (~210 lines): Utilities
- `excel_exporter.py` (~180 lines): Export formatting

**Tests:**
- `test_calculations.py` (~200 lines): Calculation unit tests
- `test_models.py`: Model validation tests
- `test_utils.py`: Utility tests
- `conftest.py` (~50 lines): Shared fixtures

---

*Structure analysis: 2026-02-06*
