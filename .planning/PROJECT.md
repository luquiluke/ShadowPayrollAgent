# Shadow Payroll Decision Tool

## What This Is

A decision-support tool for HR teams and expats evaluating international assignments. Enter an employee's details and destination countries, and the AI estimates shadow payroll costs, rates them low/medium/high against industry benchmarks, and lets you compare scenarios side-by-side. Built on Streamlit with a modern SaaS aesthetic that doubles as a portfolio piece.

## Core Value

Help HR teams and expats answer "Is this assignment worth the cost?" with AI-powered shadow payroll estimates for any country, rated against industry benchmarks.

## Requirements

### Validated

- ✓ Single employee Argentine shadow payroll calculation — existing
- ✓ USD to ARS conversion with live FX rates (open.er-api.com) — existing
- ✓ OpenAI LLM-powered tax calculations (Ganancias, contributions) — existing
- ✓ Permanent Establishment (PE) risk assessment — existing
- ✓ Excel report export with styled formatting — existing
- ✓ Pydantic data validation for payroll inputs — existing
- ✓ Streamlit web UI with session-based state management — existing
- ✓ API key session management (session-scoped, not persisted) — existing

### Active

- [ ] Modern SaaS visual redesign (gradients, rounded cards, polished typography)
- [ ] Multi-country shadow payroll estimation via LLM (any destination)
- [ ] Cost rating (low/medium/high) against industry benchmarks per region
- [ ] Scenario comparison — side-by-side (different countries, durations)
- [ ] Multi-employee batch processing
- [ ] PDF report export (professional, client-ready)
- [ ] Fix incomplete input form (missing children, housing, school fields)
- [ ] Fix FX rate metadata never stored (always shows "Unknown")
- [ ] Migrate Pydantic v1 syntax to v2 (field_validator, ConfigDict)
- [ ] Improved UX flow for the full calculation journey
- [ ] Fix duplicate exception handler in render_input_form()

### Out of Scope

- React/FastAPI rewrite — staying with Streamlit, pushing it as far as it goes
- Real-time chat or collaboration features — single-user decision tool
- Multi-user authentication/roles — portfolio piece, not enterprise SaaS
- Database persistence layer — calculations are ephemeral (may revisit in v2)
- OAuth/SSO integration — API key session-scoped is sufficient

## Context

This is a brownfield project. The existing codebase has a solid modular architecture (layered: UI, business logic, LLM integration, export) but several known bugs and incomplete features. The Pydantic models use deprecated v1 syntax, the input form is incomplete, and FX rate metadata never populates.

The app currently handles Argentina-only calculations. The evolution is to make the LLM handle any country's shadow payroll estimation, turning it from a calculator into a decision tool. The LLM already knows global tax structures at a high level — accuracy is "directional estimate, not tax advice."

Target audience: HR teams evaluating international assignments, expats considering relocation, and portfolio viewers who should see both design polish and technical depth.

Stack: Python 3.10+, Streamlit 1.33+, LangChain 0.3+, OpenAI GPT-4o, Pydantic 2.0+, pandas, openpyxl.

## Constraints

- **Framework**: Streamlit — staying with it, custom CSS/theming for visual polish
- **LLM Provider**: OpenAI (GPT-4o) via LangChain — existing integration, no migration planned
- **Accuracy**: LLM-powered estimates are directional, not tax advice — must include disclaimers
- **FX Data**: Free API (open.er-api.com) — acceptable for portfolio piece, no SLA
- **Cost**: Minimize OpenAI API costs — use caching, round inputs where possible

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Stay with Streamlit | User prefers pushing Streamlit to its limits over a full rewrite; faster to ship | — Pending |
| LLM-powered multi-country | Covers any destination without maintaining country-specific tax databases; showcases AI | — Pending |
| Industry benchmarks via LLM | LLM can provide directional benchmark comparisons; no need for external benchmark database | — Pending |
| Modern SaaS visual direction | Portfolio piece targeting "looks professional AND technically impressive" reaction | — Pending |

---
*Last updated: 2026-02-15 after initialization*
