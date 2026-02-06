# Codebase Concerns

**Analysis Date:** 2026-02-06

## Tech Debt

**Incomplete Input Form Implementation:**
- Issue: The `render_input_form()` function in `src/shadow_payroll/ui.py` (lines 177-191) has a placeholder comment `# ...existing code for collecting other inputs...` instead of complete implementation. Essential fields like `num_children`, `housing_usd`, `school_usd`, and FX rate section are missing from the current UI flow.
- Files: `src/shadow_payroll/ui.py` (lines 177-196)
- Impact: The application cannot collect all required input fields that `PayrollInput` model expects. This breaks the calculation flow when users attempt to submit the form, as required fields will be missing or undefined.
- Fix approach: Restore the removed input collection code for num_children, housing_usd, school_usd, and add the FX rate section back into the form rendering.

**Pydantic Version Inconsistency:**
- Issue: Code imports and uses deprecated Pydantic v1 syntax (`validator`, `class Config`) while `requirements.txt` specifies `pydantic>=2.0.0`. The recent commit (visible in git diff) downgraded from Pydantic v2 syntax (`field_validator`, `model_config`) to v1 syntax.
- Files: `src/shadow_payroll/models.py` (imports on line 9, validators on lines 70-86, 171-177)
- Impact: Running against Pydantic v2.0+ will cause validation decorators to fail or behave unexpectedly. The code will issue deprecation warnings at minimum, and may fail entirely depending on Pydantic configuration.
- Fix approach: Either update code to use Pydantic v2 syntax (`field_validator`, `ConfigDict`, `model_config`) or pin `pydantic<2.0.0` in requirements.txt. Recommend fixing code to v2 syntax since it's already specified as required.

**Unused Import in models.py:**
- Issue: `ConfigDict` is imported on line 9 but never used in the file. The models use `class Config:` instead of `model_config = ConfigDict(...)`.
- Files: `src/shadow_payroll/models.py` (line 9)
- Impact: Dead code, minor maintainability issue, signals incomplete migration.
- Fix approach: Remove unused import or complete migration to Pydantic v2 syntax.

**Duplicate Exception Handling in UI:**
- Issue: The `render_input_form()` function has duplicate exception handling blocks (lines 188-196 in ui.py). The same error handling code appears twice.
- Files: `src/shadow_payroll/ui.py` (lines 188-196)
- Impact: Code redundancy, harder to maintain, potential for inconsistent error handling in future updates.
- Fix approach: Remove the duplicate try-except block and consolidate into single error handler.

## Known Bugs

**Missing FX Rate Metadata in Session State:**
- Symptoms: When calculation is performed, `run_calculation()` attempts to retrieve `fx_date` and `fx_source` from `st.session_state` (lines 300-301 in ui.py), but these are never populated since the FX rate collection code is commented out.
- Files: `src/shadow_payroll/ui.py` (lines 177-196, 300-301)
- Trigger: Call `run_calculation()` after incomplete form submission
- Workaround: The code defaults to "Unknown" for missing values, but this provides poor user experience in results output.

**JavaScript DOM Manipulation Risk:**
- Issue: The `inject_dark_theme()` function (lines 42-50 in ui.py) directly manipulates browser DOM classes using unsafe_allow_html=True with JavaScript. This is fragile and may break with Streamlit version updates.
- Files: `src/shadow_payroll/ui.py` (lines 42-50)
- Trigger: On page load
- Workaround: Falls back gracefully if JS doesn't execute, but theme may not apply as intended.

**CSS File Loading with Dynamic Path:**
- Issue: The `inject_corporate_theme()` function (lines 13-17 in ui.py) uses complex path resolution with `__import__('pathlib')` at module load time before proper initialization. If the CSS file is not found, the entire module import fails.
- Files: `src/shadow_payroll/ui.py` (lines 13-19)
- Trigger: Module import when corporate_theme.css is missing or moved
- Workaround: None - application will crash
- Improvement: Use try-except around CSS injection, use more robust path resolution.

## Security Considerations

**API Key Exposure in Session State:**
- Risk: OpenAI API key is stored in Streamlit's `st.session_state` (line 79 in ui.py). While the code claims keys are never stored, they persist in session state for the duration of the Streamlit session, potentially visible in browser memory or logs.
- Files: `src/shadow_payroll/ui.py` (lines 70-84)
- Current mitigation: Session-scoped storage only (not persisted to disk), but not ideal for security-sensitive applications.
- Recommendations: Consider using Streamlit secrets management (st.secrets), implement token expiration, add audit logging for API key access.

**External API Rate Limit Lack of Backoff:**
- Risk: The `get_usd_ars_rate()` function in `src/shadow_payroll/utils.py` makes direct requests to `open.er-api.com` without exponential backoff or rate limiting. Rapid calls could trigger rate limiting or IP blocking.
- Files: `src/shadow_payroll/utils.py` (lines 27-84)
- Current mitigation: HTTP timeout (5 seconds) and caching (1 hour TTL)
- Recommendations: Implement exponential backoff for failed requests, add circuit breaker pattern, monitor rate limit headers.

**No Input Sanitization for LLM Prompt:**
- Risk: User input values are directly interpolated into the LLM prompt string without sanitization (lines 76-114 in llm_handler.py). While numerical values are safer, the prompt itself could be manipulated if input validation is bypassed.
- Files: `src/shadow_payroll/llm_handler.py` (lines 63-118)
- Current mitigation: Pydantic validation ensures numeric types and ranges
- Recommendations: Add additional input sanitization in prompt building, consider parameterized prompts, validate LLM response structure strictly.

## Performance Bottlenecks

**Large UI File:**
- Problem: `src/shadow_payroll/ui.py` contains 342 lines - too large for a single module. It handles page config, form rendering, results display, Excel export, API key management, and sidebar info.
- Files: `src/shadow_payroll/ui.py`
- Cause: No separation of UI concerns into submodules
- Improvement path: Break into `ui/forms.py`, `ui/results.py`, `ui/sidebar.py`, `ui/__init__.py` for better organization and reusability.

**LLM Request Caching Not Handling Parameter Variations:**
- Problem: The `@st.cache_data` decorator on `_cached_llm_call()` (line 120 in llm_handler.py) uses the prompt string as cache key. If similar calculations with minor differences are performed, they might hit cache unnecessarily or miss cache on trivial variations.
- Files: `src/shadow_payroll/llm_handler.py` (lines 120-147)
- Cause: Streamlit's cache_data uses function parameters as key, including full prompt text
- Improvement path: Consider implementing content-hash based caching or explicit cache keys based on calculation inputs rather than full prompt.

**No Connection Pooling for HTTP Requests:**
- Problem: Each FX rate request creates a new HTTP connection via `requests.get()` in utils.py (line 52). Multiple requests won't reuse connections.
- Files: `src/shadow_payroll/utils.py` (line 52)
- Cause: Simple requests.get() without session management
- Improvement path: Use `requests.Session()` with connection pooling, or use aiohttp for async requests if needed.

## Fragile Areas

**LLM Response Parsing:**
- Files: `src/shadow_payroll/llm_handler.py` (lines 180-229)
- Why fragile: The JSON parsing expects very specific field names from LLM output (`ganancias_mensual`, `aportes_employee`, `neto_employee`, etc.). If LLM returns variations (different capitalization, missing fields, extra fields), parsing fails. The prompt instructions are strict, but LLM responses are inherently variable.
- Safe modification: Add more robust JSON extraction (handle missing fields with defaults), improve error messages to show what was received, add field name normalization, consider schema validation with pydantic after parsing.
- Test coverage: Gaps - no tests for LLM response parsing with malformed inputs. Only happy path tested via mock data.

**PE Risk Validation:**
- Files: `src/shadow_payroll/models.py` (lines 171-177)
- Why fragile: Validator accepts both Spanish and English risk levels ("Bajo", "Medio", "Alto", "Low", "Medium", "High"). This creates inconsistency - same enum should use single language. If LLM returns different variations (e.g., "BAJO", "bajo"), validation fails.
- Safe modification: Normalize all inputs to single language (prefer Spanish for Argentina context), use Python Enum for fixed set of values, update LLM prompt to explicitly request one of exact values with examples.
- Test coverage: Models are tested but not PE risk enum variations.

**Configuration Magic Numbers:**
- Files: `src/shadow_payroll/config.py` (lines 49-51)
- Why fragile: Contribution rates (17% employee, 24% employer) and PE risk threshold (183 days) are hardcoded for "Argentina 2025" but may change year to year or by regulation. No mechanism to version or update these dynamically.
- Safe modification: Move constants to database or external config file with effective dates, add version tracking, document source of each number with regulation references.
- Test coverage: No tests validating these match current tax regulations.

**Excel Export Hard-coded Field Names:**
- Files: `src/shadow_payroll/excel_exporter.py` (lines 104-116)
- Why fragile: Monetary field detection uses hardcoded Spanish field names ("Bruto mensual ARS", "Ganancias mensual estimado", etc.). If `to_display_dict()` changes field names, Excel formatting breaks silently.
- Safe modification: Define field metadata in models to indicate which fields are monetary, use metadata during export rather than hardcoded names.
- Test coverage: Excel export not tested - no assertions on output format.

## Scaling Limits

**Streamlit Session State Limitations:**
- Current capacity: Streamlit keeps session state in memory per user per session. With many concurrent users, memory usage grows linearly.
- Limit: On shared Streamlit Cloud or modest servers, >100 concurrent users will cause memory pressure and crashes.
- Scaling path: Implement server-side session storage (Redis, database), use Streamlit's backend isolation, or deploy on larger infrastructure with Streamlit Enterprise.

**LLM API Rate Limits:**
- Current capacity: OpenAI GPT-4o has rate limits (requests per minute, tokens per minute). Each calculation makes one LLM call.
- Limit: With caching at 1 hour TTL, 60+ concurrent users calculating different scenarios will hit API rate limits.
- Scaling path: Implement request queuing, add retry with exponential backoff, use cheaper model for common calculations, batch requests.

## Dependencies at Risk

**OpenAI SDK Version Pinning:**
- Risk: `requirements.txt` pins `openai>=1.30.0,<2.0`. The constraint will prevent future OpenAI 2.0 updates which may have breaking changes or require code updates.
- Impact: Long-term maintenance burden - will need to plan migration when OpenAI 2.0 is released.
- Migration plan: When OpenAI 2.0 available, test compatibility, update code if needed, review breaking changes in their migration guide.

**Streamlit Rapid Development:**
- Risk: Streamlit is under active development with frequent releases. The `streamlit>=1.33.0` constraint is loose. Minor version updates could introduce subtle UI changes or deprecate features used (like `st.cache_data`).
- Impact: Unpredictable behavior, potential UI breaks on dependency updates.
- Migration plan: Pin to specific minor version (e.g., `streamlit==1.33.0`), test updates before upgrading, monitor Streamlit changelog.

**LangChain Ecosystem Volatility:**
- Risk: LangChain has significant API changes between versions. Current requirement `langchain>=0.3.0` and `langchain-openai>=0.2.0` are loose constraints.
- Impact: Code may break on minor updates (e.g., ChatOpenAI initialization changes).
- Migration plan: Pin versions more tightly (e.g., `langchain==0.3.x`), monitor LangChain migration guides.

## Missing Critical Features

**No Error Recovery Mechanism:**
- Problem: If LLM call fails, calculation stops completely. No retry logic, no fallback to previous calculation, no ability to re-attempt.
- Blocks: Users must reload page and recalculate from scratch on transient API errors.
- Recommendation: Implement retry decorator with exponential backoff, add manual retry button in UI, cache last successful result.

**No Audit Logging:**
- Problem: Calculations are performed but not logged to persistent storage. No way to track what calculations were performed, when, or with what inputs. Especially important for tax compliance scenarios.
- Blocks: Compliance audit trails, user support (can't reproduce user's calculation), security monitoring.
- Recommendation: Log all calculations to database with timestamp, user ID (if added), inputs, outputs, API costs.

**No Multi-User Support:**
- Problem: Application is single-user per Streamlit session. No concept of user accounts, authentication, or data isolation between users.
- Blocks: Enterprise deployment, multi-user scenarios, saving/sharing calculations.
- Recommendation: Add authentication layer (Auth0, Streamlit Cloud auth), implement user accounts, add persistent storage for saved calculations.

**No Input Undo/History:**
- Problem: Users cannot see calculation history or undo changes. Each calculation starts fresh.
- Blocks: Comparing scenarios, auditing changes, learning from past calculations.
- Recommendation: Add calculation history page, allow users to save scenarios, compare side-by-side results.

## Test Coverage Gaps

**No LLM Response Parsing Tests:**
- What's not tested: How `calculate_tax()` in `llm_handler.py` handles malformed LLM responses, missing fields, incorrect data types, or unexpected field variations.
- Files: `src/shadow_payroll/llm_handler.py` (lines 149-229) - no corresponding test file for this module
- Risk: Silent failures or cryptic error messages if LLM response format changes
- Priority: High - this is critical path code that converts unstructured LLM output to structured data

**No UI Integration Tests:**
- What's not tested: Form validation flow, button clicks, Streamlit state management, session handling. The `render_input_form()` and `run_calculation()` functions in `ui.py` have no tests.
- Files: `src/shadow_payroll/ui.py` (entire file)
- Risk: UI bugs go undetected until user testing. Complete workflows untested.
- Priority: High - UI is user-facing

**No Excel Export Tests:**
- What's not tested: Whether Excel files are generated correctly, formatting is applied, currency symbols are present. The `ExcelExporter` class has no test suite.
- Files: `src/shadow_payroll/excel_exporter.py`
- Risk: Users may download broken Excel files without knowing
- Priority: Medium - less critical than calculations but affects user satisfaction

**No FX API Failure Scenario Tests:**
- What's not tested: How application behaves when FX API is down, slow, or returns invalid data. Current tests only mock successful responses.
- Files: `src/shadow_payroll/utils.py` (lines 27-84), `tests/test_utils.py`
- Risk: Application may crash or hang on real API failures
- Priority: Medium - reliability issue but not calculation-critical

**No Configuration Validation Tests:**
- What's not tested: Whether config values are within acceptable ranges, whether missing env vars cause problems.
- Files: `src/shadow_payroll/config.py`
- Risk: Invalid configuration silently affects calculations
- Priority: Low - configuration is mostly static

---

*Concerns audit: 2026-02-06*
