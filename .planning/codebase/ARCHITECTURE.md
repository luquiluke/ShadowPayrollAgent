# Architecture

**Analysis Date:** 2026-02-15

## Pattern Overview

**Overall:** Layered architecture with separation of concerns between presentation, business logic, and integration layers.

**Key Characteristics:**
- Clear separation between UI (Streamlit), business logic (calculations), and external integrations (LLM, FX API)
- Modular design with independent calculators and handlers
- Data-driven approach using Pydantic models for validation and type safety
- Deterministic calculations separated from AI-driven complex tax calculations
- Session-based state management via Streamlit

## Layers

**Presentation Layer (UI):**
- Purpose: Streamlit-based user interface for collecting inputs and displaying results
- Location: `src/shadow_payroll/ui.py`
- Contains: UI components, form rendering, result display, Excel download
- Depends on: Models (validation), Configuration, Utils (FX rates), Calculators, LLM Handler
- Used by: `app.py` (main entry point)

**Business Logic Layer (Calculations):**
- Purpose: Deterministic payroll calculations and validations
- Location: `src/shadow_payroll/calculations.py`
- Contains: `PayrollCalculator` class with static methods for base calculations, contribution estimation, and summary generation
- Depends on: Models (input/output types), Configuration (rates and limits)
- Used by: UI layer, LLM handler

**Data Models & Validation:**
- Purpose: Type-safe data structures with comprehensive validation
- Location: `src/shadow_payroll/models.py`
- Contains: `PayrollInput`, `BaseCalculation`, `TaxCalculation`, `ShadowPayrollResult`, `FXRateData`
- Depends on: Pydantic, Configuration (default values and constraints)
- Used by: All layers (UI, calculations, LLM, export)

**LLM Integration Layer:**
- Purpose: AI-driven tax calculation and compliance analysis
- Location: `src/shadow_payroll/llm_handler.py`
- Contains: `TaxLLMHandler` class managing OpenAI API calls with prompt engineering and response validation
- Depends on: LangChain/OpenAI, Models, Configuration, Utils (JSON cleaning)
- Used by: UI layer (run_calculation function)

**Export Layer:**
- Purpose: Transform results into formatted Excel reports
- Location: `src/shadow_payroll/excel_exporter.py`
- Contains: `ExcelExporter` class with styling and currency formatting
- Depends on: Pandas, OpenPyXL, Models (ShadowPayrollResult)
- Used by: UI layer for download button

**Utilities & Infrastructure:**
- Purpose: Cross-cutting utilities and configuration
- Location: `src/shadow_payroll/utils.py`, `src/shadow_payroll/config.py`
- Contains: FX rate fetching (with caching), JSON response cleaning, currency formatting, PE risk calculation, configuration management
- Depends on: Requests, Streamlit cache, standard library
- Used by: All layers

## Data Flow

**User Input → Calculation → Result Display:**

1. **Input Collection**: User enters salary, duration, dependents, benefits via `render_input_form()` in UI
2. **Input Validation**: Pydantic `PayrollInput` model validates all inputs using field constraints from config
3. **FX Rate Acquisition**: `get_cached_usd_ars_rate()` fetches current rate from external API (with 1-hour cache)
4. **Base Calculation**: `PayrollCalculator.calculate_base()` performs deterministic USD→ARS conversion
5. **Tax Calculation**: `TaxLLMHandler.calculate_tax()` calls OpenAI with structured prompt for complex tax logic
6. **Result Composition**: Results combined into `ShadowPayrollResult` containing base and tax calculations
7. **Display & Export**: Results rendered via `render_results()` and offered for Excel export via `render_excel_download()`

**State Management:**
- Streamlit session state holds `OPENAI_API_KEY` and FX rate metadata (`fx_date`, `fx_source`)
- LLM responses are cached in Streamlit cache (TTL: 1 hour) to avoid duplicate API calls with same inputs
- FX rate data is Streamlit-cached (TTL: 1 hour) to minimize external API calls

## Key Abstractions

**PayrollCalculator:**
- Purpose: Encapsulates all deterministic payroll calculation logic
- Examples: `src/shadow_payroll/calculations.py`
- Pattern: Static utility class with no state; all methods are pure functions

**TaxLLMHandler:**
- Purpose: Manages LLM interactions with prompt engineering and response validation
- Examples: `src/shadow_payroll/llm_handler.py`
- Pattern: Instance-based handler with cached API method; uses composition with LangChain's `ChatOpenAI`

**Data Models (Pydantic):**
- Purpose: Type-safe, validated data containers with built-in serialization
- Examples: `PayrollInput`, `BaseCalculation`, `TaxCalculation`, `ShadowPayrollResult`
- Pattern: Immutable frozen models for calculation results; mutable input model for form validation

## Entry Points

**Web Application:**
- Location: `app.py`
- Triggers: `streamlit run app.py`
- Responsibilities: Page configuration, header rendering, API key check, orchestration of UI flow

**Package Imports:**
- Location: `src/shadow_payroll/__init__.py`
- Exports: All public APIs (config, models, calculators, LLM handler, utilities, exporters)
- Used by: External code or CLI tools

## Error Handling

**Strategy:** Layered exception handling with specific exception classes and user-friendly error messages.

**Patterns:**
- Model validation errors: Pydantic raises `ValidationError` with field-level details; UI catches and displays formatted error
- LLM errors: `LLMError` custom exception wraps OpenAI API errors; UI displays LLM error message with retry guidance
- FX API errors: `FXRateError` returned as None; UI falls back to manual input with warning
- JSON parsing errors: Cleaned via `clean_llm_json_response()` before parsing; logs raw response for debugging
- General calculation errors: Try/catch in `run_calculation()` displays user-friendly error and logs full traceback

## Cross-Cutting Concerns

**Logging:**
- Framework: Python `logging` module
- Configured in `app.py` based on `config.LOG_LEVEL` (default: INFO)
- Used throughout for: API calls, calculations, errors, cache operations
- Example: `logger = logging.getLogger(__name__)`

**Validation:**
- Framework: Pydantic v2 with field-level constraints
- Applied at: Model instantiation in UI; Pydantic validators enforce business rules
- Example: `salary_usd` field validates min/max from config; `fx_rate` validator ensures reasonable range

**Authentication:**
- Mechanism: OpenAI API key stored in Streamlit session state
- Accessed via: `get_api_key()` function in UI
- Never persisted: Session-scoped only; shows disclaimer about security
- Fallback: Users prompted to enter key in sidebar if missing

**Configuration:**
- Centralized in `src/shadow_payroll/config.py` via `AppConfig` dataclass
- Values can be overridden by environment variables (e.g., `LLM_MODEL`, `LOG_LEVEL`)
- Constants include: LLM settings, FX API URLs, validation ranges, calculation rates
- Access pattern: Import `from .config import config` and use `config.CONSTANT_NAME`

---

*Architecture analysis: 2026-02-15*
