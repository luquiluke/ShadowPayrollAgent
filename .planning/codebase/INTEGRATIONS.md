# External Integrations

**Analysis Date:** 2026-02-15

## APIs & External Services

**LLM (Large Language Model):**
- OpenAI GPT-4o - Complex tax calculations and compliance analysis
  - SDK/Client: `langchain-openai` (0.2.0+) wrapping OpenAI API
  - Auth: `OPENAI_API_KEY` environment variable
  - Implementation: `src/shadow_payroll/llm_handler.py` (`TaxLLMHandler` class)
  - Usage: Tax calculations, PE risk assessment, compliance comments
  - Model configurable: `LLM_MODEL` env var (defaults to `gpt-4o`)
  - Temperature: `LLM_TEMPERATURE` env var (defaults to 0.0 for deterministic output)

**Foreign Exchange Rates:**
- open.er-api.com (free tier, no API key required) - USD to ARS exchange rates
  - SDK/Client: `requests` library HTTP GET
  - URL: `https://open.er-api.com/v6/latest/USD` (configurable via `FX_API_URL`)
  - Timeout: 5 seconds (configurable via `FX_API_TIMEOUT`)
  - Response format: JSON with `result: "success"`, `rates: {ARS: <value>}`, `time_last_update_utc`
  - Caching: Streamlit cache with 1-hour TTL (configurable via `FX_CACHE_TTL`)
  - Fallback rate: 1000.0 ARS/USD if API fails (configurable via `FX_DEFAULT_RATE`)
  - Implementation: `src/shadow_payroll/utils.py` (`get_usd_ars_rate()`, `get_cached_usd_ars_rate()`)

## Data Storage

**Databases:**
- None - Stateless application
- All calculations performed in-memory during session

**File Storage:**
- Local filesystem only - Excel reports generated in-memory as BytesIO buffers
- No persistent file storage
- Reports downloaded directly via Streamlit download button

**Caching:**
- Streamlit session state - For API key storage across page reruns
- Streamlit cache_data - For FX rates (1 hour) and LLM responses (1 hour)
- No external cache server required

## Authentication & Identity

**Auth Provider:**
- Custom OpenAI API key management
  - Implementation: `src/shadow_payroll/config.py` (`get_openai_api_key()`, `set_openai_api_key()`)
  - Storage: Environment variable `OPENAI_API_KEY`
  - Session State: Stored in `st.session_state["OPENAI_API_KEY"]` after user input
  - UI Input: Password field in sidebar (Streamlit security type)
  - Approach: User must provide API key in UI before calculations available

**User Interface Authentication:**
- No user authentication system
- API key serves as auth token for accessing LLM functionality
- Application is single-user or assumes same user provides API key

## Monitoring & Observability

**Error Tracking:**
- None configured in codebase
- Custom exception classes for error handling:
  - `LLMError` in `llm_handler.py` - LLM operation failures
  - `FXRateError` in `utils.py` - Exchange rate retrieval failures

**Logging:**
- Python standard `logging` module
- Configured in `app.py` with `logging.basicConfig()`
- Level: Configurable via `LOG_LEVEL` env var (defaults to `INFO`)
- Format: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`
- Handlers: Console (`logging.StreamHandler()`)
- Log locations: Console output, no file persistence
- Logger instances created per module via `logging.getLogger(__name__)`

**Structured Logging:**
- Info: Application start, API calls, calculation completion
- Debug: LLM response cleaning, Excel generation
- Error: API failures, validation errors, parsing exceptions
- Warning: Invalid inputs, missing API keys

## CI/CD & Deployment

**Hosting:**
- Streamlit (typical) - Application server framework
- Compatible with Streamlit Cloud deployment
- No specific hosting platform required

**CI Pipeline:**
- GitHub Actions (`.github/workflows/ci.yml`)
- Triggers: Push to main/develop, pull requests
- Test Matrix:
  - OS: Ubuntu, Windows, macOS
  - Python: 3.10, 3.11, 3.12
- Steps:
  1. Checkout code
  2. Setup Python version
  3. Cache pip packages
  4. Install dependencies from `requirements.txt`
  5. Run pytest with coverage
  6. Upload coverage to Codecov (only ubuntu-latest + py3.10)
  7. Lint checks (Black, Ruff, MyPy)
  8. Security scans (Safety, Bandit)

**Deployment Notes:**
- No automated deployment pipeline configured
- Manual deployment to Streamlit Cloud or similar platform required
- Environment variables must be set in deployment environment

## Environment Configuration

**Required Environment Variables:**
- `OPENAI_API_KEY` - Critical for LLM functionality (no default)

**Optional Environment Variables:**
- `LLM_MODEL` - Default: `gpt-4o`
- `LLM_TEMPERATURE` - Default: `0.0`
- `FX_API_URL` - Default: `https://open.er-api.com/v6/latest/USD`
- `LOG_LEVEL` - Default: `INFO` (options: DEBUG, INFO, WARNING, ERROR, CRITICAL)

**Secrets Location:**
- `.env` file for local development (not committed, in `.gitignore`)
- Template: `.env.example`
- Production: Deploy to platform-specific secret management (e.g., Streamlit Cloud secrets, GitHub Secrets)

## Webhooks & Callbacks

**Incoming:**
- None - Application is pull-based, not event-driven
- All interactions initiated by user through Streamlit UI

**Outgoing:**
- None - No notifications or callbacks to external systems
- One-way API calls to OpenAI and FX rate provider

## External API Error Handling

**OpenAI API:**
- Exception handling: `OpenAIError` caught in `_cached_llm_call()`
- Fallback behavior: Raises `LLMError` for user notification
- Retry logic: None (handled by OpenAI client with defaults)
- Response validation: JSON parsing with error logging

**FX Rate API:**
- Exception handling: `requests.RequestException` caught in `get_usd_ars_rate()`
- Fallback behavior: Returns `None`, UI displays error or uses default rate
- Caching: Avoids repeated failures within TTL
- Response validation: Checks for `result: "success"` and `ARS` in rates dict

## Rate Limiting

**OpenAI:**
- Handled by OpenAI API rate limiting (depends on account tier)
- Streamlit cache (1 hour TTL) reduces repeated calls for same prompt
- No explicit rate limiting in application code

**FX API:**
- Free tier allows requests without API key
- Streamlit cache (1 hour TTL) prevents excessive API calls
- No explicit rate limiting configured

## Data Security Considerations

**API Keys:**
- Sensitive: `OPENAI_API_KEY` should never be committed
- Transport: Provided via environment variables, not in code
- Storage: Streamlit session state (in-memory only)
- No persistence to database or files

**User Input:**
- Validated via Pydantic models in `src/shadow_payroll/models.py`
- Constraints: Min/max ranges, positive values, reasonable FX rates
- JSON responses from LLM validated before database storage (no DB exists)

**Calculations:**
- All calculations performed in-memory during session
- No sensitive data logged (API keys filtered from logs)
- Excel reports generated in-memory, not persisted

---

*Integration audit: 2026-02-15*
