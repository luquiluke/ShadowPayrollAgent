# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-15)

**Core value:** Help HR teams and expats answer "Is this assignment worth the cost?" with AI-powered shadow payroll estimates for any country, rated against industry benchmarks.
**Current focus:** Phase 3 - Decision Experience

## Current Position

Phase: 3 of 3 (Decision Experience)
Plan: 3 of 3 in current phase (03-03 complete)
Status: All phases complete
Last activity: 2026-02-19 -- Completed 03-03 (PDF & Excel export)

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: 5.7 min
- Total execution time: 0.73 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation-fixes | 2 | 11 min | 5.5 min |
| 02-multi-country-estimation | 2 | 13 min | 6.5 min |
| 03-decision-experience | 3 | 22 min | 7.3 min |

**Recent Trend:**
- Last 5 plans: 02-02 (10 min), 03-01 (2 min), 03-02 (2 min), 03-03 (18 min)
- Trend: stable (03-03 longer due to PDF/Excel export complexity)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 3 phases (quick depth) -- Foundation -> Estimation -> Decision Experience
- [Roadmap]: DSGN-03 (disclaimers) grouped with estimation, not visual polish -- disclaimers are integral to AI output
- [Roadmap]: DSGN-01/DSGN-02 grouped with scenario/export in Phase 3 -- polish stable features, avoid rework
- [01-01]: Mutable PayrollInput (validate_assignment=True) for Streamlit form binding
- [01-01]: English-only PE risk values -- removed Spanish entirely for multi-country readiness
- [01-01]: display_currency collected but not used for conversion in Phase 1
- [01-01]: Specific housing/school limits (180k/120k) instead of generic MAX_BENEFIT
- [01-02]: FX sidebar as persistent widget with session state as single source of truth
- [01-02]: AppTest integration with graceful skip for CI compatibility
- [01-02]: 90%+ coverage target for non-UI modules; ui.py covered by AppTest
- [Phase 02]: strict=False for with_structured_output to support Optional fields
- [Phase 02]: Dict serialization for Streamlit cache compatibility with Pydantic models
- [Phase 02]: Removed fx_rate < 1.0 check to support all currency pairs
- [02-02]: Unicode escape sequences (\u2013, \u2014) not HTML entities in st.markdown -- Streamlit does not parse HTML entities
- [02-02]: Explicit USD prefix on benchmark range for unambiguous dual-currency display
- [02-02]: CSS diagonal stripe removed from corporate_theme.css -- cosmetic; Phase 3 handles full CSS polish
- [03-01]: Plain dicts (TypedDict schema) for scenarios, not Pydantic -- Streamlit cache compatibility
- [03-01]: Label normalization via lowercase mapping dict to canonical English labels
- [03-01]: CSS custom properties in :root for consistent theming across all components
- [03-02]: Bridge function converts model_dump() line_items list to dict for scenarios.py compatibility
- [03-02]: Session state stores last_result + last_result_obj for persistence across Streamlit reruns
- [03-03]: ReportLab built-in fonts (Helvetica, Courier) -- no custom TTF registration
- [03-03]: Light backgrounds for PDF tables (print-friendly) vs dark theme for web UI
- [03-03]: _ensure_dict_line_items helper in both PDF and Excel for format consistency

### Pending Todos

None yet.

### Blockers/Concerns

- ~~Pydantic v1 syntax in models.py blocks all new model work~~ (RESOLVED in 01-01)
- ~~reportlab vs. weasyprint decision needed before Phase 3 PDF work~~ (RESOLVED: chose reportlab in 03-03)

## Session Continuity

Last session: 2026-02-19
Stopped at: Completed 03-03-PLAN.md -- All phases complete
Resume file: None
