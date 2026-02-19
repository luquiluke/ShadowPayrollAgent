---
phase: 03-decision-experience
plan: 02
subsystem: ui, state-management
tags: [streamlit, scenarios, comparison-table, color-coding, session-state]

requires:
  - phase: 03-decision-experience
    plan: 01
    provides: "Scenario CRUD module (scenarios.py), label normalization, CSS custom properties"
provides:
  - "Scenario management UI (save/remove/display scenarios)"
  - "Color-coded comparison table with normalized line items"
  - "Plain-English scenario summary identifying cheapest option"
  - "Full scenario flow wired in app.py with session state persistence"
affects: [03-03]

tech-stack:
  added: []
  patterns: [session state persistence for estimation results, list-to-dict line item bridging]

key-files:
  created: []
  modified:
    - src/shadow_payroll/ui.py
    - app.py

key-decisions:
  - "Bridge function _prepare_result_for_scenario converts model_dump() list to label->amount dict for scenarios.py compatibility"
  - "Session state stores last_result and last_result_obj for persistence across Streamlit reruns"
  - "inject_dark_theme cleaned to no-op -- CSS custom properties handle all theming"

patterns-established:
  - "Scenario save flow: estimate -> model_dump() -> _prepare_result_for_scenario -> add_scenario"
  - "Session state keys: last_result, last_input, last_model_name, last_timestamp, last_result_obj"

duration: 2min
completed: 2026-02-19
---

# Phase 3 Plan 02: Scenario Comparison UI Summary

**Scenario save/compare flow with color-coded comparison table, auto-naming, and session state persistence across Streamlit reruns**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-19T21:42:10Z
- **Completed:** 2026-02-19T21:44:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Built 4 scenario UI functions: render_scenario_controls, render_saved_scenarios, render_comparison_table, render_scenario_summary
- Color-coded HTML comparison table with green (cheapest) and red (most expensive) per row, JetBrains Mono numbers
- Rewired app.py for full scenario flow: estimate -> save -> compare on single scrolling page
- Session state persistence ensures estimation results survive Streamlit reruns

## Task Commits

Each task was committed atomically:

1. **Task 1: Add scenario management UI and comparison table to ui.py** - `fe2b118` (feat)
2. **Task 2: Rewire app.py for scenario flow** - `9d949ea` (feat)

## Files Created/Modified
- `src/shadow_payroll/ui.py` - Added scenario controls, saved scenarios display, comparison table, summary text; cleaned inject_dark_theme
- `app.py` - Added scenario imports, session state persistence for last result, scenario flow rendering

## Decisions Made
- Created `_prepare_result_for_scenario()` bridge function to convert EstimationResponse.model_dump() line_items (list of dicts) to the label->amount dict format that scenarios.py normalize_line_items expects
- Stored both `last_result` (dict) and `last_result_obj` (EstimationResponse) in session state -- dict for scenario storage, object for render_estimation_results
- Cleaned inject_dark_theme to a no-op since Plan 01 CSS rewrite handles all theming via custom properties

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Bridged list-to-dict line_items format mismatch**
- **Found during:** Task 1 (render_scenario_controls)
- **Issue:** scenarios.py normalize_line_items expects result["line_items"] as {label: amount_usd} dict, but EstimationResponse.model_dump() produces a list of CostLineItem dicts
- **Fix:** Added _prepare_result_for_scenario() that converts list format to dict format before storing
- **Files modified:** src/shadow_payroll/ui.py
- **Verification:** Import check passes, test suite passes (107 tests)
- **Committed in:** fe2b118 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential for correctness -- without the bridge function, comparison table would fail on real data. No scope creep.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Scenario comparison UI complete, ready for Plan 03 (PDF export / Excel enhancement)
- Session state keys documented for downstream consumption
- All 107 tests passing

## Self-Check: PASSED

All 2 modified files verified on disk. Both task commits (fe2b118, 9d949ea) confirmed in git log.

---
*Phase: 03-decision-experience*
*Completed: 2026-02-19*
