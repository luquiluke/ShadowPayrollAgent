# Technology Stack

**Analysis Date:** 2026-02-15

## Languages

**Primary:**
- Python 3.10+ - Complete application codebase
- Python 3.11 - Supported in CI/CD matrix
- Python 3.12 - Supported in CI/CD matrix

**Secondary:**
- HTML/CSS - Streamlit UI theming (custom corporate theme)
- JavaScript - Streamlit theme injection

## Runtime

**Environment:**
- Python 3.10+ (configured in `pyproject.toml` with `requires-python = ">=3.10"`)
- Streamlit runtime for web UI

**Package Manager:**
- pip - Primary package manager
- setuptools - Build backend (`setuptools>=61.0`)
- Lockfile: Present in `.venv/` directory (virtual environment)

## Frameworks

**Core:**
- Streamlit 1.33.0+ - Web UI framework and session state management
- LangChain 0.3.0+ - LLM orchestration and prompt management
- LangChain-OpenAI 0.2.0+ - OpenAI integration layer
- Pydantic 2.0.0+ - Data validation and type safety for models

**Data Processing:**
- pandas 2.2.0+ - DataFrame operations for report generation
- openpyxl 3.1.0+ - Excel file generation and formatting

**HTTP & API:**
- requests 2.31.0+ - External API calls for exchange rates

**Testing:**
- pytest 8.0.0+ - Test runner and framework
- pytest-cov 4.1.0+ - Code coverage reporting
- pytest-mock 3.12.0+ - Test mocking utilities

**Code Quality & Development:**
- Black 24.0.0+ - Code formatter (line-length: 88)
- Ruff 0.1.0+ - Fast Python linter
- MyPy 1.8.0+ - Static type checker
- pre-commit 3.6.0+ - Git hooks framework

## Key Dependencies

**Critical:**
- openai 1.30.0 (< 2.0) - OpenAI API client (pinned to v1.x for compatibility)
- streamlit 1.33.0+ - UI framework with caching decorators
- langchain 0.3.0+ - LLM prompt management and response handling
- pydantic 2.0.0+ - Model validation with Field constraints

**Infrastructure:**
- requests - External FX API integration (`open.er-api.com`)
- pandas - Report data transformation
- openpyxl - Excel styling and currency formatting

## Configuration

**Environment:**
- `.env.example` - Template for required environment variables
- `.env` - Runtime configuration (not committed, in `.gitignore`)
- Loaded via `os.getenv()` in `config.py`

**Key Environment Variables:**
- `OPENAI_API_KEY` - Required for LLM operations (no default)
- `LLM_MODEL` - Optional, defaults to `gpt-4o`
- `LLM_TEMPERATURE` - Optional, defaults to `0.0` (deterministic)
- `FX_API_URL` - Optional, defaults to `https://open.er-api.com/v6/latest/USD`
- `LOG_LEVEL` - Optional, defaults to `INFO`

**Build:**
- `pyproject.toml` - Project metadata, dependencies, tool configurations
- `.pre-commit-config.yaml` - Pre-commit hooks (Black, Ruff, MyPy)

## Configuration Details

**Black Formatting:**
```
line-length = 88
target-version = ['py310', 'py311', 'py312']
```

**Ruff Linting:**
```
line-length = 88
target-version = "py310"
select = ["E", "W", "F", "I", "B", "C4", "UP"]
per-file-ignores = {"__init__.py": ["F401"]}
```

**MyPy Type Checking:**
```
python_version = "3.10"
check_untyped_defs = true
strict_equality = true
disallow_untyped_defs = false  (not enforced)
```
Modules with `ignore_missing_imports`: streamlit, langchain, langchain_openai, langchain_community, openpyxl

**pytest Configuration:**
```
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = ["-v", "--strict-markers", "--tb=short", "--cov=src/shadow_payroll"]
markers = ["unit", "integration", "slow"]
```

## Platform Requirements

**Development:**
- Python 3.10+ with pip
- Virtual environment (`.venv/` directory)
- Git for pre-commit hooks
- OS Support: Linux, macOS, Windows (tested in CI/CD matrix)

**Production:**
- Streamlit runtime environment
- Python 3.10+ installed
- Network access to:
  - OpenAI API (`api.openai.com`)
  - FX rate API (`open.er-api.com`)
- OpenAI API key required

**Deployment:**
- Tested on Ubuntu, Windows, macOS in CI/CD
- Streamlit Cloud compatible (typical deployment)
- No database server required (stateless calculations)

## Caching & Performance

**Streamlit Caching:**
- `@st.cache_data(ttl=3600)` for FX rate fetching (1 hour TTL)
- `@st.cache_data(ttl=config.LLM_CACHE_TTL)` for LLM responses (configurable, default 1 hour)
- Session state for API key storage

**Timeouts:**
- LLM API timeout: 30 seconds (configurable in `config.LLM_TIMEOUT`)
- FX API timeout: 5 seconds (configurable in `config.FX_API_TIMEOUT`)

---

*Stack analysis: 2026-02-15*
