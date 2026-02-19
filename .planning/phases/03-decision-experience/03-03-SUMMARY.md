---
phase: 03-decision-experience
plan: 03
subsystem: ui, export
tags: [reportlab, pdf, excel, openpyxl, download-buttons, charts]

requires:
  - phase: 03-decision-experience
    plan: 01
    provides: "Scenario CRUD module, label normalization, PDF branding config"
  - phase: 03-decision-experience
    plan: 02
    provides: "Scenario comparison UI, session state persistence, bridge function for line_items"
provides:
  - "ReportLab PDF exporter with charts, tables, branding, and disclaimers"
  - "Multi-scenario Excel comparison workbook with per-scenario detail sheets"
  - "PDF and Excel download buttons in the UI"
  - "Descriptive export filenames with date"
affects: []

tech-stack:
  added: [reportlab>=4.4.0, Pillow>=10.0.0]
  patterns: [ReportLab Platypus flowables for PDF, openpyxl direct workbook manipulation for multi-sheet Excel]

key-files:
  created:
    - src/shadow_payroll/pdf_exporter.py
  modified:
    - src/shadow_payroll/excel_exporter.py
    - src/shadow_payroll/ui.py
    - app.py
    - requirements.txt

key-decisions:
  - "ReportLab built-in fonts (Helvetica, Courier) -- no custom TTF registration needed"
  - "Light backgrounds for PDF tables (print-friendly) vs dark theme for web UI"
  - "Single create_comparison_report method for both 1 and N scenarios in Excel"
  - "_ensure_dict_line_items helper in both PDF and Excel exporters for format consistency"

patterns-established:
  - "PDFExporter.generate(scenarios, metadata) -> BytesIO pattern for PDF generation"
  - "ExcelExporter.create_comparison_report(scenarios, metadata) -> BytesIO for multi-sheet Excel"
  - "generate_export_filename(scenarios, extension) for consistent file naming"

duration: 18min
completed: 2026-02-19
---

# Phase 3 Plan 03: PDF & Excel Export Summary

**ReportLab PDF exporter with comparison charts, per-scenario details, and branding plus multi-scenario Excel workbook with download buttons in UI**

## Performance

- **Duration:** 18 min
- **Started:** 2026-02-19T21:46:57Z
- **Completed:** 2026-02-19T22:05:16Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created PDFExporter generating multi-page PDF with executive summary, VerticalBarChart cost comparison, per-scenario detail pages (input summary, cost breakdown, cost rating, AI insights, PE risk with timeline bar), and disclaimer page with header/footer on every page
- Upgraded ExcelExporter with create_comparison_report() producing multi-sheet workbook: Comparison sheet with color-coded min/max highlighting plus per-scenario detail sheets
- Added render_export_buttons() and generate_export_filename() to UI, wired into app.py to show PDF and Excel download buttons after scenarios are saved

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ReportLab PDF exporter** - `ecc2ce1` (feat)
2. **Task 2: Upgrade Excel exporter and add export buttons** - `d963228` (feat)

## Files Created/Modified
- `src/shadow_payroll/pdf_exporter.py` - ReportLab PDF generation: PDFExporter class with charts, tables, branding, header/footer
- `src/shadow_payroll/excel_exporter.py` - Added create_comparison_report(), _ensure_dict_line_items(), per-scenario sheets
- `src/shadow_payroll/ui.py` - Added render_export_buttons(), generate_export_filename(), imported PDFExporter and ExcelExporter
- `app.py` - Wired render_export_buttons() call after scenario comparison section
- `requirements.txt` - Added reportlab>=4.4.0 and Pillow>=10.0.0

## Decisions Made
- Used ReportLab built-in fonts (Helvetica for headings/body, Courier for numbers) per research recommendation -- avoids TTF registration complexity
- PDF uses light backgrounds for tables (print-friendly) while web UI keeps dark fintech theme
- Both PDF and Excel exporters include _ensure_dict_line_items helper to handle both list-of-dicts and dict line_items formats
- create_comparison_report() used for both single and multi-scenario Excel (always produces comparison + detail sheets)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed list-format line_items breaking normalize_line_items in PDF export**
- **Found during:** Task 1 (PDF exporter verification)
- **Issue:** Scenarios with line_items as list of CostLineItem dicts (from model_dump()) caused AttributeError in normalize_line_items which expects dict format
- **Fix:** Added _ensure_dict_line_items() helper that converts list format to {label: amount_usd} dict before passing to normalize_line_items
- **Files modified:** src/shadow_payroll/pdf_exporter.py
- **Verification:** Both single-scenario (list format) and multi-scenario (dict format) PDFs generate successfully
- **Committed in:** ecc2ce1 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential for correctness -- same format mismatch as 03-02 but in a different code path. No scope creep.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All Phase 3 plans complete -- full decision experience delivered
- PDF and Excel exports functional with professional styling
- All 107 existing tests passing

## Self-Check: PASSED

All 5 files verified on disk. Both task commits (ecc2ce1, d963228) confirmed in git log.

---
*Phase: 03-decision-experience*
*Completed: 2026-02-19*
