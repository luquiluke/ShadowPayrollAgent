# Phase 1: Foundation Fixes - Research

**Researched:** 2026-02-17
**Domain:** Pydantic v2 migration, Streamlit UI completion, FX metadata, test expansion
**Confidence:** HIGH

## Summary

Phase 1 is a focused tech debt cleanup across four modules: `models.py` (Pydantic v1 to v2 + field renaming), `ui.py` (incomplete form + duplicate error handler + FX sidebar), `llm_handler.py` (English field names in prompts), and comprehensive test expansion. The codebase is small (7 source files, ~700 LOC) with 57 passing tests covering calculations, models, and utilities.

The current Pydantic installation is **v2.12.5** but models use deprecated v1 syntax (`@validator`, `class Config`). All v2 patterns have been verified working in the local environment. Streamlit **v1.53.1** is installed with `streamlit.testing.v1.AppTest` available for UI testing. pytest-mock is available for LLM mocking.

**Primary recommendation:** Migrate models first (breaks tests and LLM handler), then fix UI form and FX metadata in parallel, then expand tests to cover new and existing gaps. Field renaming propagates to LLM prompts, Excel exporter, and display labels -- plan for full grep-and-replace across all consumers.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Model migration scope:**
- Full v1->v2 syntax migration AND rename Argentina-specific fields for multi-country readiness
- `ganancias_mensual` -> `income_tax_monthly`, `aportes_employee` -> `employee_contributions`, etc.
- All English field names -- models, LLM prompts, and internal code
- LLM prompt responses must use English field names
- Keep PE risk helper in utils.py as a fallback/sanity check on LLM output (don't remove)

**Form field defaults:**
- All new fields (children, housing, school) optional with defaults of 0
- Two-column layout: left column for employee/assignment details, right column for benefits/extras
- Add home country + host country dropdown fields now (for Phase 2 readiness) -- default to Argentina
- Validation ranges: $0-15,000/month housing, $0-10,000/month school
- User can pick display currency (USD, EUR, GBP, etc.) via dropdown

**FX rate visibility:**
- Sidebar: persistent info widget showing current live rate and last refresh time, with manual override option
- Results section: show the specific rate, date, and source used in that calculation
- API failure: use last known cached rate with clear "stale data" warning and timestamp, allow manual override
- Support user-selected display currency (not just USD + ARS)

**Test expectations:**
- Comprehensive test expansion: cover all current gaps (LLM parsing, UI integration, Excel export)
- LLM tests: mock responses for CI + optional real API integration test for manual validation
- Target: 90%+ code coverage
- No test markers needed -- suite small enough to run everything

### Claude's Discretion

**Frozen/mutable model split:**
- Claude picks the best pattern for Streamlit form binding vs immutable results

### Deferred Ideas (OUT OF SCOPE)

None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.12.5 (installed) | Data validation models | Already in requirements, v2 syntax is the target |
| streamlit | 1.53.1 (installed) | UI framework + AppTest for testing | Already in requirements, AppTest available |
| pytest | 8.0+ (installed) | Test framework | Already in requirements |
| pytest-mock | 3.12+ (installed) | Mocking for LLM and API tests | Already in requirements |
| pytest-cov | 4.1+ (installed) | Coverage reporting | Already in requirements, target 90%+ |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| streamlit.testing.v1.AppTest | Built into Streamlit 1.53.1 | UI integration testing | Testing form rendering, widget interactions |
| unittest.mock | stdlib | Mocking LLM responses, API calls | LLM handler tests, FX rate tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AppTest | Manual st.session_state mocking | AppTest is official, supports widget interaction natively |
| pytest-mock | unittest.mock directly | pytest-mock wraps unittest.mock with nicer fixture API, already installed |

**Installation:** No new packages needed. All dependencies already in `requirements.txt`.

## Architecture Patterns

### Recommended Model Split (Claude's Discretion Area)

**Recommendation: Mutable input model, frozen result models.**

Rationale: Streamlit widgets bind to variables that change on rerun. `PayrollInput` must be mutable (`frozen=False, validate_assignment=True`) so form values update correctly. All result models (`BaseCalculation`, `TaxCalculation`, `ShadowPayrollResult`, `FXRateData`) should be frozen -- they represent computed results that should never mutate.

This matches the current pattern and is correct for the Streamlit architecture:
- `PayrollInput`: `ConfigDict(validate_assignment=True)` -- mutable, validates on set
- `BaseCalculation`: `ConfigDict(frozen=True)` -- immutable result
- `TaxCalculation`: `ConfigDict(frozen=True)` -- immutable result
- `ShadowPayrollResult`: `ConfigDict(frozen=True)` -- immutable result
- `FXRateData`: `ConfigDict(frozen=True)` -- immutable result

### Field Renaming Map

Current Spanish/mixed names must become English. Full mapping based on codebase grep:

**TaxCalculation model fields (already English in model, but LLM prompt/response uses Spanish):**
| Current LLM JSON Key | New LLM JSON Key | Model Field (already) |
|----------------------|-------------------|----------------------|
| `ganancias_mensual` | `income_tax_monthly` | `ganancias_monthly` -> `income_tax_monthly` |
| `aportes_employee` | `employee_contributions` | `employee_contributions` (no change) |
| `neto_employee` | `net_employee` | `net_employee` (no change) |
| `aportes_employer` | `employer_contributions` | `employer_contributions` (no change) |
| `total_cost_employer` | `total_cost_employer` | `total_cost_employer` (no change) |
| `pe_risk` | `pe_risk` | `pe_risk` (no change) |
| `comentarios` | `comments` | `comments` (no change) |

**ShadowPayrollResult.to_display_dict() keys (Spanish -> English):**
| Current Key | New Key |
|------------|---------|
| `Bruto mensual ARS` | `Gross Monthly (ARS)` |
| `Ganancias mensual estimado` | `Income Tax Monthly (est.)` |
| `Aportes employee` | `Employee Contributions` |
| `Neto employee` | `Net Employee` |
| `Aportes employer` | `Employer Contributions` |
| `Costo total employer` | `Total Employer Cost` |
| `Riesgo PE` | `PE Risk` |
| `Comentarios` | `Comments` |
| `Tipo de cambio` | `Exchange Rate` |
| `Fecha FX` | `FX Date` |
| `Fuente FX` | `FX Source` |

### Files Affected by Field Renaming

1. `src/shadow_payroll/models.py` -- model field names + `to_display_dict()`
2. `src/shadow_payroll/llm_handler.py` -- prompt template JSON keys + response parsing
3. `src/shadow_payroll/excel_exporter.py` -- `monetary_fields` list references display dict keys
4. `src/shadow_payroll/ui.py` -- `render_results()` references model attributes
5. `tests/conftest.py` -- fixture field names
6. `tests/test_models.py` -- field name assertions + display dict key assertions

### PayrollInput New Fields for Phase 2 Readiness

Based on context decisions, `PayrollInput` needs:
- `home_country: str = "Argentina"` (dropdown, any country)
- `host_country: str = "Argentina"` (dropdown, any country)
- `display_currency: str = "USD"` (dropdown: USD, EUR, GBP, etc.)
- Existing fields already present: `num_children`, `housing_usd`, `school_usd`
- Validation update: housing max $15,000/month = $180,000/year, school max $10,000/month = $120,000/year

### FX Rate Sidebar Pattern

Current flow: `get_fx_rate()` called inline in form area, returns `(rate, date, source)` but metadata never reaches session state.

New flow:
1. On app load, fetch FX rate and store in `st.session_state` (`fx_rate`, `fx_date`, `fx_source`, `fx_stale`)
2. Sidebar widget: always-visible info showing rate + timestamp + source, with manual override input
3. On calculation: read from session state (guaranteed populated)
4. On API failure: set `fx_stale = True`, use last cached value, show warning
5. Results section: display rate/date/source from the `ShadowPayrollResult` object (already designed for this)

### Anti-Patterns to Avoid
- **Mixing v1 and v2 Pydantic syntax in same file:** Complete the migration fully, don't leave any `@validator` or `class Config` behind
- **Hardcoding country lists in UI:** Use a constant/config for country list so Phase 2 can extend easily
- **Testing Streamlit by importing functions directly:** Use `AppTest.from_file()` for UI integration tests instead of calling render functions outside Streamlit context

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pydantic v1->v2 migration | Custom validation decorators | `field_validator` + `ConfigDict` | Built-in, tested, documented |
| UI testing | Mock Streamlit session state manually | `streamlit.testing.v1.AppTest` | Official test framework, supports widgets |
| LLM response mocking | Fake HTTP server | `pytest-mock` / `unittest.mock.patch` | Simple, no infrastructure needed |
| Country lists | Hardcoded arrays | `pydantic` Literal types or config constant | Single source of truth |

**Key insight:** Every tool needed for Phase 1 is already installed. No new dependencies. The work is purely refactoring and wiring existing pieces correctly.

## Common Pitfalls

### Pitfall 1: Pydantic v2 validator signature change
**What goes wrong:** `@validator` in v1 receives `cls, v` with positional field name. `@field_validator` in v2 receives `cls, v` as an `info` object or plain value depending on mode.
**Why it happens:** Different decorator API between versions.
**How to avoid:** Use `@field_validator('field_name')` with `@classmethod` decorator. The function receives `cls` and `v` (the value). For accessing other field values, use `mode='after'` and accept `self` as a model instance.
**Warning signs:** `TypeError: ... takes 2 positional arguments but 3 were given`

### Pitfall 2: Streamlit AppTest widget interaction order
**What goes wrong:** `AppTest` tests fail because widgets must be interacted with in render order, and `.run()` must be called after setting values.
**Why it happens:** AppTest simulates full Streamlit rerun cycle.
**How to avoid:** Call `at.run()` first to render, then access widgets by key or index, set values, then `at.run()` again to process.
**Warning signs:** `IndexError` or `KeyError` when accessing widgets before first `.run()`

### Pitfall 3: LLM prompt field name mismatch after renaming
**What goes wrong:** LLM prompt asks for `income_tax_monthly` but LLM might still return Spanish keys from its training data.
**Why it happens:** LLM follows prompt instructions imperfectly.
**How to avoid:** Make the prompt JSON schema explicit and add a parsing fallback that checks for both old and new key names. Add robust tests with mock responses.
**Warning signs:** `KeyError` in `calculate_tax()` response parsing

### Pitfall 4: Excel exporter string matching breaks on rename
**What goes wrong:** `monetary_fields` list in `excel_exporter.py` matches display dict keys by string. After renaming, old strings don't match.
**Why it happens:** Tight coupling between display dict keys and Excel formatting logic.
**How to avoid:** Update `monetary_fields` list in Excel exporter at the same time as `to_display_dict()`. Or better: identify monetary fields by type (float) rather than string matching.
**Warning signs:** Excel files with unformatted numbers (no currency symbol)

### Pitfall 5: Test fixtures with old field names
**What goes wrong:** Existing 57 tests all pass with current field names. After renaming `ganancias_monthly` -> `income_tax_monthly`, fixtures and assertions break.
**Why it happens:** Field rename is a breaking change that propagates to all test files.
**How to avoid:** Update `conftest.py` fixtures first, then update all test assertions. Run `pytest` after each file change.
**Warning signs:** Mass test failures after model rename

## Code Examples

### Pydantic v2 Model with ConfigDict (verified locally)

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator

class PayrollInput(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    salary_usd: float = Field(
        default=400000.0,
        ge=0.0,
        le=10_000_000.0,
        description="Annual home salary in USD",
    )

    home_country: str = Field(
        default="Argentina",
        description="Employee home country",
    )

    @field_validator("salary_usd")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Monetary values must be positive")
        return v
```

### Frozen Result Model (verified locally)

```python
class TaxCalculation(BaseModel):
    model_config = ConfigDict(frozen=True)

    income_tax_monthly: float = Field(ge=0.0, description="Monthly income tax")
    employee_contributions: float = Field(ge=0.0, description="Employee social contributions")
    net_employee: float = Field(ge=0.0, description="Net after deductions")
    employer_contributions: float = Field(ge=0.0, description="Employer contributions")
    total_cost_employer: float = Field(ge=0.0, description="Total employer cost")
    pe_risk: str = Field(description="PE risk level")
    comments: str = Field(description="Tax analysis comments")

    @field_validator("pe_risk")
    @classmethod
    def validate_pe_risk(cls, v: str) -> str:
        valid_levels = ["Low", "Medium", "High"]
        if v not in valid_levels:
            raise ValueError(f"PE risk must be one of {valid_levels}")
        return v
```

### English LLM Prompt JSON Schema

```python
prompt = f"""
...
Reply ONLY with valid JSON, no Markdown, using this exact structure:
{{
  "income_tax_monthly": <number>,
  "employee_contributions": <number>,
  "net_employee": <number>,
  "employer_contributions": <number>,
  "total_cost_employer": <number>,
  "pe_risk": "Low | Medium | High",
  "comments": "<detailed analysis text>"
}}
"""
```

### Streamlit AppTest for UI (verified available)

```python
from streamlit.testing.v1 import AppTest

def test_app_renders():
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception
    assert len(at.title) > 0

def test_form_inputs():
    at = AppTest.from_file("app.py")
    at.session_state["OPENAI_API_KEY"] = "sk-test"
    at.run()
    # Access number inputs
    salary_input = at.number_input[0]
    assert salary_input.value == 400000.0
```

### Mock LLM Response Test

```python
from unittest.mock import patch, MagicMock

def test_calculate_tax_parses_valid_response():
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "income_tax_monthly": 500000.0,
        "employee_contributions": 1700000.0,
        "net_employee": 8000000.0,
        "employer_contributions": 2400000.0,
        "total_cost_employer": 14400000.0,
        "pe_risk": "High",
        "comments": "Assignment exceeds 183 days."
    })

    with patch.object(handler.llm, 'invoke', return_value=mock_response):
        result = handler.calculate_tax(input_data, base)
        assert result.income_tax_monthly == 500000.0
        assert result.pe_risk == "High"
```

### FX Rate Sidebar Widget Pattern

```python
def render_fx_sidebar() -> None:
    with st.sidebar:
        st.subheader("Exchange Rate")
        fx_data = get_cached_usd_ars_rate()
        if fx_data:
            st.info(f"Live: {fx_data['rate']:,.2f} ARS/USD\n"
                    f"Updated: {fx_data['date']}\n"
                    f"Source: {fx_data['source']}")
            st.session_state["fx_rate"] = fx_data["rate"]
            st.session_state["fx_date"] = fx_data["date"]
            st.session_state["fx_source"] = fx_data["source"]
            st.session_state["fx_stale"] = False
        else:
            cached = st.session_state.get("fx_rate", config.FX_DEFAULT_RATE)
            st.warning(f"Using cached rate: {cached:,.2f} ARS/USD (stale)")
            st.session_state["fx_stale"] = True

        override = st.number_input("Manual override", value=st.session_state.get("fx_rate", config.FX_DEFAULT_RATE))
        if override != st.session_state.get("fx_rate"):
            st.session_state["fx_rate"] = override
            st.session_state["fx_source"] = "Manual"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@validator` decorator | `@field_validator` with `@classmethod` | Pydantic v2.0 (June 2023) | All validators must be migrated |
| `class Config:` inner class | `model_config = ConfigDict(...)` | Pydantic v2.0 (June 2023) | All model configs must be migrated |
| `.dict()` method | `.model_dump()` method | Pydantic v2.0 (June 2023) | Check if used anywhere (not currently) |
| `.schema()` class method | `.model_json_schema()` | Pydantic v2.0 (June 2023) | Check if used anywhere (not currently) |
| Manual Streamlit testing | `streamlit.testing.v1.AppTest` | Streamlit ~1.28 (2023) | Available for proper UI testing |

**Deprecated/outdated:**
- `@validator`: Deprecated in Pydantic v2, will be removed in future v3. Currently emits deprecation warnings.
- `class Config`: Deprecated in Pydantic v2, replaced by `model_config = ConfigDict(...)`.

## Open Questions

1. **Country list for dropdowns**
   - What we know: Need home_country + host_country dropdowns defaulting to Argentina
   - What's unclear: How comprehensive should the country list be? Full ISO 3166-1 list (~249 entries) or curated subset?
   - Recommendation: Use a curated list of ~30 common expat destination countries for now. Store as a constant in `config.py`. Easy to expand later.

2. **Display currency dropdown scope**
   - What we know: User wants USD, EUR, GBP, etc. as display currency options
   - What's unclear: Does this require real-time FX conversion for all currency pairs, or just labeling?
   - Recommendation: For Phase 1, support display currency selection in the model and UI, but actual multi-currency conversion is Phase 2 scope. Store the preference, calculate in ARS internally.

3. **PE risk validator -- English only or bilingual?**
   - What we know: Currently accepts both Spanish ("Bajo"/"Medio"/"Alto") and English ("Low"/"Medium"/"High")
   - What's unclear: After switching to English-only LLM responses, should we still accept Spanish?
   - Recommendation: Switch to English-only ("Low"/"Medium"/"High") since the LLM prompt will request English. The PE risk helper in utils.py should also return English values.

4. **AppTest limitations with CSS injection**
   - What we know: `ui.py` runs `inject_corporate_theme()` at module import time, which reads a CSS file
   - What's unclear: Whether AppTest handles `unsafe_allow_html=True` and file I/O during test imports
   - Recommendation: Wrap CSS loading in try-except (already noted as tech debt). In tests, this should work since the CSS file exists, but add defensive handling.

## Sources

### Primary (HIGH confidence)
- Local environment verification: `pydantic==2.12.5`, `streamlit==1.53.1`, all v2 patterns tested
- Codebase analysis: All 7 source files read and analyzed
- CONCERNS.md: Pre-existing tech debt documentation (2026-02-15)
- Test suite: 57 tests passing, coverage gaps identified

### Secondary (MEDIUM confidence)
- Pydantic v2 migration patterns: Verified by executing v2 syntax locally (`ConfigDict`, `field_validator`, `frozen`, `validate_assignment`)
- Streamlit AppTest: Import verified, API explored via `dir()`, but not yet used in actual test

### Tertiary (LOW confidence)
- AppTest behavior with complex widgets (sidebar, custom CSS): Not tested, based on API inspection only

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed, versions verified
- Architecture: HIGH -- model split pattern verified, field renaming mapped exhaustively
- Pitfalls: HIGH -- based on direct codebase analysis and local verification
- Test patterns: MEDIUM -- AppTest available but not battle-tested in this codebase yet

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (stable domain, no fast-moving dependencies)
