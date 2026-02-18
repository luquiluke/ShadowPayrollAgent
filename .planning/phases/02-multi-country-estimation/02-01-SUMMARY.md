---
phase: 02-multi-country-estimation
plan: 01
subsystem: api
tags: [langchain, pydantic, structured-output, fx-rates, estimation]

# Dependency graph
requires:
  - phase: 01-foundation-fixes
    provides: Pydantic v2 models, validated PayrollInput, COUNTRIES list, FX utility
provides:
  - EstimationResponse and sub-models (CostLineItem, CostRating, ItemRating, PERiskAssessment)
  - CountryEstimator class with LangChain structured output
  - COUNTRY_REGIONS and COUNTRY_CURRENCIES config mappings (30 countries)
  - Generalized get_fx_rates(base_currency) utility
  - Generalized PayrollInput fx_rate validator (accepts sub-1.0 rates)
affects: [02-02, ui, results-rendering]

# Tech tracking
tech-stack:
  added: []
  patterns: [LangChain with_structured_output(strict=False), cached structured LLM calls via dict serialization]

key-files:
  created:
    - src/shadow_payroll/estimator.py
  modified:
    - src/shadow_payroll/models.py
    - src/shadow_payroll/config.py
    - src/shadow_payroll/utils.py
    - tests/test_models.py

key-decisions:
  - "strict=False for with_structured_output to support Optional fields and defaults"
  - "Dict serialization for Streamlit cache compatibility (model_dump -> reconstruct)"
  - "Removed fx_rate < 1.0 check to support EUR/USD, GBP/USD rates"

patterns-established:
  - "CountryEstimator pattern: structured LLM -> model_dump for cache -> reconstruct on return"
  - "Config mappings: static dict for country->region and country->currency"
  - "Generalized FX: get_fx_rates(base_currency) with automatic Streamlit cache keying"

# Metrics
duration: 3min
completed: 2026-02-18
---

# Phase 2 Plan 1: Estimation Engine Summary

**CountryEstimator with LangChain structured output, 5 Pydantic response models, 30-country config mappings, and generalized FX utility**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-18T17:13:15Z
- **Completed:** 2026-02-18T17:16:42Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Built EstimationResponse model hierarchy (CostLineItem, CostRating, ItemRating, PERiskAssessment) with frozen Pydantic v2 models and Field descriptions for LLM guidance
- Created CountryEstimator class using LangChain with_structured_output(strict=False) for validated structured responses
- Added COUNTRY_REGIONS and COUNTRY_CURRENCIES mappings for all 30 supported countries
- Generalized FX utility to fetch rates for any base currency
- Removed ARS-specific fx_rate validator restriction to support all currency pairs

## Task Commits

Each task was committed atomically:

1. **Task 1: Add response models, config mappings, and generalize FX** - `c5b91cf` (feat)
2. **Task 2: Create CountryEstimator with LangChain structured output** - `bb8c909` (feat)

## Files Created/Modified
- `src/shadow_payroll/estimator.py` - CountryEstimator class with estimate(), _build_prompt(), _cached_estimate(), EstimationError, create_estimator()
- `src/shadow_payroll/models.py` - Added CostLineItem, CostRating, ItemRating, PERiskAssessment, EstimationResponse; updated fx_rate validator
- `src/shadow_payroll/config.py` - Added COUNTRY_REGIONS (30 entries) and COUNTRY_CURRENCIES (30 entries)
- `src/shadow_payroll/utils.py` - Added get_fx_rates(base_currency) with Streamlit caching
- `tests/test_models.py` - Updated fx_rate test from rejection to acceptance of sub-1.0 values

## Decisions Made
- Used `strict=False` for `with_structured_output` because EstimationResponse has Optional fields with defaults, which OpenAI strict mode rejects
- Cache serialization via `model_dump()` / reconstruct pattern for Streamlit's `st.cache_data` compatibility (Pydantic models are not natively serializable by Streamlit)
- Removed the `v < 1.0` fx_rate validation check entirely (not replaced with a different threshold) since valid currency pairs like EUR/USD have rates below 1.0

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing test for fx_rate validator change**
- **Found during:** Task 1 (fx_rate validator update)
- **Issue:** `test_unreasonably_low_fx_rate_rejected` expected ValidationError for fx_rate=0.5, but we intentionally removed that check
- **Fix:** Replaced test with `test_sub_one_fx_rate_accepted` that verifies fx_rate=0.92 is accepted
- **Files modified:** tests/test_models.py
- **Verification:** All 107 tests pass
- **Committed in:** c5b91cf (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix in tests)
**Impact on plan:** Test update was a direct consequence of the planned validator change. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Estimation engine backend is complete and ready for UI integration in 02-02
- CountryEstimator can be imported and used: `from shadow_payroll.estimator import create_estimator`
- All existing tests pass (107/107), no regressions
- The old Argentina-only flow (llm_handler.py, calculations.py) remains intact

## Self-Check: PASSED

All 5 files verified on disk. Both task commits (c5b91cf, bb8c909) verified in git log.

---
*Phase: 02-multi-country-estimation*
*Completed: 2026-02-18*
