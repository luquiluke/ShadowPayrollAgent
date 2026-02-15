# Codebase Concerns

**Analysis Date:** 2026-02-15

## Tech Debt

**Pydantic v1 syntax in v2 project:**
- Issue: `models.py` uses deprecated `@validator` decorator and `class Config` pattern instead of Pydantic v2's `field_validator` and `model_config = ConfigDict(...)`
- Files: `src/shadow_payroll/models.py` (lines 9, 21-23, 70-86, 104-106, 135-137, 171-177, 187-189, 220-221)
- Impact: Will break when Pydantic v2 fully deprecates v1 syntax in future versions. IDE warnings and type checking may fail. Inconsistent with stated code style in CLAUDE.md which explicitly forbids v1 syntax.
- Fix approach: Migrate all model definitions to use `field_validator` with `mode='after'`, replace `class Config` blocks with `model_config = ConfigDict(frozen=True, validate_assignment=True, etc.)`. Follow Pydantic v2 migration guide.

**Incomplete input form with duplicate error handling:**
- Issue: `render_input_form()` in `ui.py` (lines 139-196) is incomplete. Collects only salary, duration, and spouse inputs. Line 177 has placeholder comment "# ...existing code for collecting other inputs...". Exception handling block appears twice (lines 188-196).
- Files: `src/shadow_payroll/ui.py` (lines 139-196)
- Impact: Form never collects `num_children`, `housing_usd`, or `school_usd` fields required by `PayrollInput` model. This causes validation errors when users try to calculate. Duplicate exception handling is dead code. The form will fail validation since `PayrollInput` requires all these fields.
- Fix approach: Complete the form by adding missing input widgets for children count, housing benefit, and school benefit in the col2 section. Remove duplicate exception handler block (lines 193-196). Consolidate FX rate collection into this function for logical grouping.

**FX metadata never stored in session state:**
- Issue: `run_calculation()` tries to read `fx_date` and `fx_source` from session state (ui.py lines 300-301) but these are never set. The `get_fx_rate()` function returns them (line 136) but main flow doesn't capture them to session state.
- Files: `src/shadow_payroll/ui.py` (lines 102-136, 300-301), `app.py` (lines 39-83)
- Impact: Excel export and result display always show "Unknown" for FX date/source even when API data is available. Session state inconsistency makes debugging harder. Users cannot see the actual FX data source in final results.
- Fix approach: In `main()` function in app.py, capture return values from `get_fx_rate()` and store in `st.session_state` before calling `run_calculation()`. Pass actual values to `ShadowPayrollResult` constructor instead of "Unknown".

**Unused PE risk calculation helper:**
- Issue: `calculate_pe_risk_level()` in `utils.py` (lines 147-173) implements PE risk logic based on assignment duration, but the LLM prompt always asks LLM to evaluate PE risk independently (llm_handler.py line 94). Helper function never called from anywhere in codebase.
- Files: `src/shadow_payroll/utils.py` (lines 147-173), `src/shadow_payroll/llm_handler.py` (line 94)
- Impact: Duplicate logic creates confusion about which calculation is authoritative. If LLM returns inconsistent results, there's no fallback. Dead code increases maintenance burden.
- Fix approach: Either remove the helper function if LLM is the source of truth, or use it as validation/sanity check on LLM response. If keeping, document explicitly why both exist and which takes precedence.

**Unsafe HTML rendering for CSS injection:**
- Issue: `inject_corporate_theme()` uses `st.markdown(..., unsafe_allow_html=True)` to load local CSS file (ui.py lines 13-17). While local file loading is safer than user input, this pattern could be exploited if CSS file becomes user-modifiable.
- Files: `src/shadow_payroll/ui.py` (lines 13-19)
- Impact: Opens XSS vector if CSS file path becomes dynamic or user-controlled in future. Current fixed path is safe but not future-proof. Module-level execution of file I/O at import time could fail if file missing.
- Fix approach: Use Streamlit's native styling mechanisms where possible. For custom CSS, consider using Streamlit config file instead of runtime HTML injection. If HTML injection is necessary, wrap in try-except and document security boundary clearly.

## Known Bugs

**Duplicate exception handler in render_input_form():**
- Symptoms: Second exception handler (lines 193-196 in ui.py) is unreachable dead code that duplicates lines 188-191
- Files: `src/shadow_payroll/ui.py` (lines 188-196)
- Trigger: Form submission with invalid data — only first handler executes
- Workaround: Remove the second handler block

**Form incomplete causes validation errors:**
- Symptoms: Form collects salary, duration, spouse but not num_children, housing_usd, school_usd. `PayrollInput` validation fails when submitted because required fields missing.
- Files: `src/shadow_payroll/ui.py` (lines 170-186)
- Trigger: User clicks "Calcular" button after incomplete form input
- Workaround: Complete the form implementation to collect all fields

**FX rate metadata shows "Unknown" always:**
- Symptoms: Excel exports and result display show "Fecha FX: Unknown" and "Fuente FX: Unknown" even when `get_fx_rate()` returned valid API data
- Files: `src/shadow_payroll/ui.py` (lines 102-136, 300-301)
- Trigger: Any calculation run
- Workaround: Store FX metadata in session state before calculation

## Security Considerations

**API key handling in session state:**
- Risk: OpenAI API key stored in Streamlit session state (ui.py line 79). While session-scoped and not persisted to disk, memory exposure is possible in shared Streamlit deployments or debugging sessions.
- Files: `src/shadow_payroll/ui.py` (line 79), `src/shadow_payroll/config.py` (line 94)
- Current mitigation: `type="password"` input field hides visible typing. Key marked session-scoped and documented in CLAUDE.md. Streamlit reruns clear old data.
- Recommendations: Consider using environment-only API key on production servers. Add warning if running on shared deployment. Implement session timeout. Log API key access (with redaction) for audit trail. Use Streamlit Secrets management on production.

**LLM prompt injection via user inputs:**
- Risk: `build_tax_prompt()` in `llm_handler.py` interpolates user inputs directly into prompt (lines 76-117). If validation is bypassed, malicious input could manipulate LLM behavior.
- Files: `src/shadow_payroll/llm_handler.py` (lines 63-118)
- Current mitigation: Pydantic models validate inputs before reaching LLM handler. Float/int fields prevent text injection.
- Recommendations: Add additional validation for comments/text fields if any user-supplied text enters prompts in future. Consider using prompt templates instead of f-string interpolation. Log all LLM prompts and responses for audit.

**Streamlit multi-user deployment risks:**
- Risk: Application designed for single-user Streamlit Cloud, but could be deployed on shared servers where users share session state or API keys due to cache_data decorator using global Streamlit cache.
- Files: `src/shadow_payroll/ui.py` (lines 70-84), `src/shadow_payroll/utils.py` (line 87)
- Current mitigation: None explicit
- Recommendations: Document deployment assumptions clearly. Add warnings if detecting shared environment. Implement per-user API key isolation on production. Use Streamlit Secrets management instead of text input on secured deployments.

## Performance Bottlenecks

**FX API call with global cache across users:**
- Problem: `get_cached_usd_ars_rate()` decorated with `@st.cache_data()` (utils.py line 87) uses global Streamlit cache. In multi-user scenario, all users share same cached rate even if they should be isolated. Cache TTL 3600s is long for 24/7 operation with volatile markets.
- Files: `src/shadow_payroll/utils.py` (lines 87-98)
- Cause: Streamlit cache is global, not per-user. 1-hour TTL means stale rates during periods of currency volatility.
- Improvement path: Make cache TTL configurable via environment variable. Document that FX rates are shared across all users (acceptable for read-only app). Consider background refresh job for shared deployments. Monitor API call patterns for rate limiting.

**LLM response caching with weak key:**
- Problem: `_cached_llm_call()` caches LLM responses using prompt as key (llm_handler.py line 120). If input values change slightly (e.g., salary 399999 vs 400000), new API calls occur even for near-identical scenarios.
- Files: `src/shadow_payroll/llm_handler.py` (lines 120-147)
- Cause: Prompt includes precise float values. Natural floating-point arithmetic creates unique prompts for similar inputs.
- Improvement path: Round inputs to nearest significant unit (e.g., nearest 1000 USD) before building prompt. Or implement semantic caching that groups "similar" requests. Cache TTL is 3600s which is reasonable.

**Excel export creates in-memory structures:**
- Problem: `ExcelExporter.create_report()` (excel_exporter.py lines 37-75) creates pandas DataFrame and openpyxl workbook in memory. No streaming or chunking.
- Files: `src/shadow_payroll/excel_exporter.py` (lines 37-75)
- Cause: Results are small (11-12 rows), so not an issue now, but pattern won't scale if multi-scenario reports added
- Improvement path: Current approach acceptable for current scale. If expanding to scenario comparison reports, implement streaming Excel generation.

## Fragile Areas

**Pydantic model immutability conflicts:**
- Files: `src/shadow_payroll/models.py` (lines 97-125, 128-177, 180-214)
- Why fragile: `BaseCalculation` and `TaxCalculation` are frozen (immutable) but `PayrollInput` is not (lines 21-23). Mix of mutable/immutable models creates cognitive load and potential for bugs.
- Safe modification: Decide on immutability strategy. Either freeze all models consistently, or make all mutable. Add explicit test for immutability to catch future changes.
- Test coverage: `test_models.py` includes immutability test for `BaseCalculation` (lines 102-112) but only that one model. Add tests for `TaxCalculation` and `ShadowPayrollResult` immutability.

**UI state depends on invisible session state:**
- Files: `src/shadow_payroll/ui.py` (lines 70-84, 300-301), `app.py` (lines 39-83)
- Why fragile: `run_calculation()` expects `fx_date` and `fx_source` in session state (lines 300-301) but these are only set if code path reaches `get_fx_rate()` before form submission. Missing logic means "Unknown" values silently propagate.
- Safe modification: Make session state initialization explicit at app startup. Use `st.session_state.setdefault()` to guarantee defaults exist. Document all session state keys in comments at top of file.
- Test coverage: No UI integration tests exist, so this flow never validated automatically.

**LLM response parsing brittle to format changes:**
- Files: `src/shadow_payroll/llm_handler.py` (lines 188-221)
- Why fragile: Parsing expects exact JSON field names (`ganancias_mensual`, `aportes_employee`, etc.). If LLM returns slightly different format, error is caught but cryptic. Chained exception handlers hide actual problem.
- Safe modification: Add explicit field validation before JSON parsing. Log raw LLM response on parse failure for debugging. Consider using Pydantic validation for LLM response instead of manual JSON/KeyError handling. Add retry logic with model instruction clarification.
- Test coverage: No tests exist for LLM response parsing. Add mock LLM tests that inject malformed JSON, missing fields, and edge cases.

**Static CSS file dependency:**
- Files: `src/shadow_payroll/ui.py` (lines 13-19), `src/shadow_payroll/corporate_theme.css`
- Why fragile: Module import fails if CSS file not found at exact path. File I/O happens at module load time before proper error handling. File located via pathlib.__import__ which is indirect and fragile.
- Safe modification: Wrap CSS loading in try-except. Log warning but continue if CSS missing. Use safer path resolution. Consider embedding CSS as string or using Streamlit config.
- Test coverage: No tests for missing CSS or styling failures.

## Scaling Limits

**Single LLM API call per calculation:**
- Current capacity: 1 calculation per ~5 seconds (LLM timeout at 30s)
- Limit: Streamlit synchronous execution blocks on LLM call. No background job processing or queuing.
- Scaling path: For multi-tenant deployment, implement async task queue (Celery + Redis) to decouple UI from LLM latency. Return pending results via polling. Cache common scenarios.

**Session state growth in Streamlit deployments:**
- Current capacity: Fine for single user, one session per browser
- Limit: If using `st.cache_data()` globally across all users (which current code does with FX rates), memory grows unbounded over time
- Scaling path: Implement per-session cache vs global cache. Use Redis for shared cache layer in multi-instance deployments. Implement cache eviction policy.

**No persistence layer:**
- Current capacity: Calculations exist only in memory during session
- Limit: Cannot support calculation history, audit trails, or multi-session workflows
- Scaling path: Add database layer (SQLite for dev, PostgreSQL for prod) to store calculation history

## Dependencies at Risk

**LangChain/OpenAI API dependency:**
- Risk: Application tightly coupled to OpenAI's GPT-4o via LangChain. No abstraction for swapping models or providers.
- Impact: If OpenAI raises prices significantly, migrating to Claude/Anthropic requires rewriting `TaxLLMHandler` class
- Migration plan: Extract LLM interface into abstract base class. Implement provider adapters for different LLMs. Decouple prompt format from provider.

**Streamlit framework lock-in:**
- Risk: UI tightly coupled to Streamlit widgets (`st.number_input()`, `st.markdown()`, etc.). Migration to FastAPI/React would require complete UI rewrite.
- Impact: Difficult to export as library. Single-user limitation. No multi-user or fine-grained permission support.
- Migration plan: Separate calculation logic (framework-agnostic) from UI. Could expose as REST API and build multiple UI frontends.

**Open.er-api.com FX API dependency:**
- Risk: External free API with no SLA. If service goes down, app shows fallback rate but silently loses accuracy.
- Impact: Calculations show hardcoded 1000 ARS/USD when API fails (config.py line 30). Users don't know they're using stale rates.
- Migration plan: Implement fallback chain. Add explicit warning to UI when using non-current rates. Consider paid FX data service for production.

## Missing Critical Features

**No audit trail or calculation history:**
- Problem: Users cannot review past calculations or export calculation audit trail for tax compliance. Each calculation is ephemeral.
- Blocks: Compliance workflows, client delivery, dispute resolution
- Path: Add persistent storage. Store calculation inputs, LLM prompt, LLM response, final result, timestamp, user ID. Export audit report.

**No scenario comparison:**
- Problem: Users cannot easily compare different assumption scenarios (e.g., "what if salary was 10% higher?").
- Blocks: Planning workflows, budgeting
- Path: Implement scenario builder. Store multiple calculations in session. Compare side-by-side. Export comparison matrix.

**No manual override for LLM-calculated values:**
- Problem: Users cannot override LLM's tax estimate if they believe it's wrong or have known exceptions.
- Blocks: Expert workflows, exception handling
- Path: Add "Override" mode in results UI. Allow manual entry of tax amounts. Store override flag and reason in audit trail.

## Test Coverage Gaps

**No tests for LLM response parsing:**
- What's not tested: `TaxLLMHandler.calculate_tax()` method, JSON parsing with malformed responses, missing fields, invalid PE risk levels
- Files: `src/shadow_payroll/llm_handler.py` (lines 149-229)
- Risk: LLM response format changes or API errors not caught until production. Current error handling is defensive but untested.
- Priority: **High** — LLM integration is core to application. A single bad LLM response cascades to user error.

**No tests for UI components:**
- What's not tested: Form input validation, API key entry flow, FX rate display, results rendering, Excel download
- Files: `src/shadow_payroll/ui.py` (all functions)
- Risk: Form validation incomplete (lines 139-192) — only caught by manual testing. Streamlit reruns and widget state management complex to test.
- Priority: **High** — UI is user-facing and currently broken (incomplete form).

**No tests for Excel export:**
- What's not tested: Excel file generation, styling application, cell formatting, multiple sheet generation
- Files: `src/shadow_payroll/excel_exporter.py` (lines 37-165)
- Risk: Excel output could corrupt silently. Users see broken files only after download.
- Priority: **Medium** — Feature is user-facing. Broken exports harm trust.

**No end-to-end integration tests:**
- What's not tested: Complete flow from input form → calculation → LLM call → result display → Excel export
- Files: Span across all modules
- Risk: Individual modules tested but integration points fragile. Session state, FX metadata, async flows not validated.
- Priority: **Medium** — E2E tests catch issues that unit tests miss.

**No tests for error scenarios:**
- What's not tested: OpenAI API errors, FX API timeouts, invalid model responses, network failures
- Files: `src/shadow_payroll/llm_handler.py`, `src/shadow_payroll/utils.py`
- Risk: Error paths untested. Exception messages unclear. Recovery flows undefined.
- Priority: **Medium** — Users will encounter errors in production. Better error handling improves UX.

---

*Concerns audit: 2026-02-15*
