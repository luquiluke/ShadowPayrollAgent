# Roadmap: Shadow Payroll Decision Tool

## Overview

Transform the existing Argentina-only shadow payroll calculator into a multi-country AI-powered decision tool. The journey: fix confirmed tech debt that blocks new development, build a country-agnostic estimation engine as the core capability, then layer scenario comparison and professional export to deliver the "decision tool" experience that differentiates this from a simple calculator.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation Fixes** - Clean up confirmed tech debt that blocks multi-country development
- [x] **Phase 2: Multi-Country Estimation** - Country-agnostic AI estimation engine with cost rating and PE risk
- [ ] **Phase 3: Decision Experience** - Scenario comparison, professional export, and visual polish

## Phase Details

### Phase 1: Foundation Fixes
**Goal**: Existing codebase is clean, complete, and ready to extend with new capabilities
**Depends on**: Nothing (first phase)
**Requirements**: FNDX-01, FNDX-02, FNDX-03, FNDX-04
**Success Criteria** (what must be TRUE):
  1. All Pydantic models use v2 syntax (field_validator, ConfigDict) and all existing tests pass
  2. Input form collects all employee fields (children count, housing benefit, school benefit) and validates through Pydantic
  3. FX rate results display actual rate value, date, and source instead of "Unknown"
  4. No duplicate exception handlers in the UI code
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Pydantic v2 migration, English field renaming, LLM prompt update, complete input form
- [x] 01-02-PLAN.md — FX sidebar widget, metadata fix, comprehensive test expansion (90%+ coverage)

### Phase 2: Multi-Country Estimation
**Goal**: Users can estimate shadow payroll costs for any country with itemized breakdown, cost rating, and PE risk
**Depends on**: Phase 1
**Requirements**: ESTM-01, ESTM-02, ESTM-03, ESTM-04, ESTM-05, DSGN-03
**Success Criteria** (what must be TRUE):
  1. User can select any destination country and receive an itemized shadow payroll cost estimate (income tax, social security, PE admin, allowances)
  2. User sees each estimate rated Low/Medium/High against AI-estimated regional benchmarks
  3. User sees plain-English AI insights explaining cost drivers and optimization opportunities
  4. User sees PE risk assessment with treaty-aware explanation for any country pair
  5. All AI-generated estimates are clearly labeled as estimates with visible disclaimers ("AI estimate, not tax advice")
**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md — Estimation engine: response models, config mappings, generalized FX, CountryEstimator with LangChain structured output
- [x] 02-02-PLAN.md — Estimation UI: cost breakdown, cost rating badges, PE risk section with timeline bar, AI insights, disclaimers, app wiring

### Phase 3: Decision Experience
**Goal**: Users can compare scenarios side-by-side and export professional reports that serve as the deliverable
**Depends on**: Phase 2
**Requirements**: SCEN-01, SCEN-02, SCEN-03, EXPO-01, EXPO-02, EXPO-03, DSGN-01, DSGN-02
**Success Criteria** (what must be TRUE):
  1. User can create up to 3 scenarios with different countries/durations and see them side-by-side
  2. User sees visual delta highlighting showing which scenario costs more and by how much (percentage differences)
  3. User can export results to Excel with scenario comparison data included
  4. User can generate a professional PDF report with executive summary, cost breakdown, and disclaimers
  5. App has modern SaaS aesthetic with clean navigation flow from input to results to comparison to export
**Plans**: TBD

Plans:
- [ ] 03-01: Scenario engine and comparison UI
- [ ] 03-02: Export upgrade (Excel enhancement + PDF generation)
- [ ] 03-03: Visual polish and portfolio readiness

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation Fixes | 2/2 | ✓ Complete | 2026-02-17 |
| 2. Multi-Country Estimation | 2/2 | ✓ Complete | 2026-02-18 |
| 3. Decision Experience | 0/3 | Not started | - |
