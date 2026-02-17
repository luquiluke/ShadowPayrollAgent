"""
Unit tests for LLM handler module.

Tests LLM response parsing, prompt building, and error handling
using mocked LLM calls (no real API calls).
"""

import json

import pytest
from unittest.mock import patch, MagicMock

from shadow_payroll.llm_handler import TaxLLMHandler, LLMError
from shadow_payroll.models import PayrollInput, BaseCalculation, TaxCalculation


def _make_handler():
    """Create a TaxLLMHandler without calling __init__ (avoids API key requirement)."""
    handler = TaxLLMHandler.__new__(TaxLLMHandler)
    handler.llm = MagicMock()
    return handler


def _valid_response_dict():
    """Return a valid LLM response dict."""
    return {
        "income_tax_monthly": 500000.0,
        "employee_contributions": 1700000.0,
        "net_employee": 8000000.0,
        "employer_contributions": 2400000.0,
        "total_cost_employer": 14400000.0,
        "pe_risk": "High",
        "comments": "Assignment exceeds 183 days.",
    }


class TestCalculateTax:
    """Test suite for TaxLLMHandler.calculate_tax."""

    def test_parses_valid_response(self, sample_payroll_input, sample_base_calculation):
        """Test calculate_tax correctly parses a valid JSON response."""
        handler = _make_handler()
        valid_json = json.dumps(_valid_response_dict())

        with patch.object(handler, "_cached_llm_call", return_value=valid_json):
            result = handler.calculate_tax(sample_payroll_input, sample_base_calculation)

        assert isinstance(result, TaxCalculation)
        assert result.income_tax_monthly == 500000.0
        assert result.employee_contributions == 1700000.0
        assert result.net_employee == 8000000.0
        assert result.employer_contributions == 2400000.0
        assert result.total_cost_employer == 14400000.0
        assert result.pe_risk == "High"
        assert result.comments == "Assignment exceeds 183 days."

    def test_malformed_json_raises_value_error(
        self, sample_payroll_input, sample_base_calculation
    ):
        """Test calculate_tax raises ValueError on malformed JSON."""
        handler = _make_handler()
        malformed = "{ this is not valid json }"

        with patch.object(handler, "_cached_llm_call", return_value=malformed):
            with pytest.raises(ValueError, match="invalid JSON"):
                handler.calculate_tax(sample_payroll_input, sample_base_calculation)

    def test_missing_required_field_raises_value_error(
        self, sample_payroll_input, sample_base_calculation
    ):
        """Test calculate_tax raises ValueError when required field is missing."""
        handler = _make_handler()
        incomplete = _valid_response_dict()
        del incomplete["pe_risk"]

        with patch.object(
            handler, "_cached_llm_call", return_value=json.dumps(incomplete)
        ):
            with pytest.raises(ValueError, match="missing required field"):
                handler.calculate_tax(sample_payroll_input, sample_base_calculation)

    def test_json_wrapped_in_markdown_fences(
        self, sample_payroll_input, sample_base_calculation
    ):
        """Test calculate_tax handles JSON wrapped in markdown code fences."""
        handler = _make_handler()
        fenced = f"```json\n{json.dumps(_valid_response_dict())}\n```"

        with patch.object(handler, "_cached_llm_call", return_value=fenced):
            result = handler.calculate_tax(sample_payroll_input, sample_base_calculation)

        assert result.pe_risk == "High"
        assert result.income_tax_monthly == 500000.0

    def test_llm_api_failure_raises_llm_error(
        self, sample_payroll_input, sample_base_calculation
    ):
        """Test calculate_tax raises LLMError when LLM API call fails."""
        handler = _make_handler()

        with patch.object(
            handler, "_cached_llm_call", side_effect=LLMError("API timeout")
        ):
            with pytest.raises(LLMError, match="API timeout"):
                handler.calculate_tax(sample_payroll_input, sample_base_calculation)

    def test_invalid_pe_risk_value_raises_value_error(
        self, sample_payroll_input, sample_base_calculation
    ):
        """Test calculate_tax raises ValueError when pe_risk has invalid value."""
        handler = _make_handler()
        bad_risk = _valid_response_dict()
        bad_risk["pe_risk"] = "SuperHigh"

        with patch.object(
            handler, "_cached_llm_call", return_value=json.dumps(bad_risk)
        ):
            with pytest.raises(ValueError, match="Invalid LLM response data"):
                handler.calculate_tax(sample_payroll_input, sample_base_calculation)


class TestTaxLLMHandlerInit:
    """Test suite for TaxLLMHandler initialization."""

    @patch("shadow_payroll.llm_handler.ChatOpenAI")
    def test_init_with_api_key(self, mock_chat):
        """Test handler initializes with provided API key."""
        handler = TaxLLMHandler(api_key="sk-test-key")
        assert handler.llm is not None
        mock_chat.assert_called_once()

    def test_init_without_api_key_raises_error(self):
        """Test handler raises ValueError when no API key available."""
        with patch("shadow_payroll.config.get_openai_api_key", return_value=None):
            with pytest.raises(ValueError, match="API key is required"):
                TaxLLMHandler(api_key=None)

    @patch("shadow_payroll.llm_handler.ChatOpenAI")
    def test_create_llm_handler_factory(self, mock_chat):
        """Test factory function creates handler."""
        from shadow_payroll.llm_handler import create_llm_handler

        handler = create_llm_handler("sk-test-key")
        assert isinstance(handler, TaxLLMHandler)


class TestCachedLLMCall:
    """Test suite for _cached_llm_call method."""

    @patch("shadow_payroll.llm_handler.ChatOpenAI")
    def test_cached_llm_call_returns_content(self, mock_chat_cls):
        """Test _cached_llm_call returns response content."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"test": "value"}'
        mock_llm.invoke.return_value = mock_response
        mock_chat_cls.return_value = mock_llm

        handler = TaxLLMHandler(api_key="sk-test")
        # Call the cached method directly
        result = handler._cached_llm_call("test prompt")
        assert result == '{"test": "value"}'

    @patch("shadow_payroll.llm_handler.ChatOpenAI")
    def test_cached_llm_call_propagates_errors_via_calculate_tax(self, mock_chat_cls):
        """Test that LLM errors from _cached_llm_call surface through calculate_tax."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("Connection failed")
        mock_chat_cls.return_value = mock_llm

        handler = TaxLLMHandler(api_key="sk-test")
        input_data = PayrollInput(
            salary_usd=100000.0, duration_months=12, fx_rate=1000.0
        )
        base = BaseCalculation(
            salary_monthly_ars=8_333_333.0,
            benefits_monthly_ars=0.0,
            gross_monthly_ars=8_333_333.0,
            fx_rate=1000.0,
        )
        # The error will surface as either LLMError or RuntimeError
        with pytest.raises((LLMError, RuntimeError)):
            handler.calculate_tax(input_data, base)


class TestBuildTaxPrompt:
    """Test suite for TaxLLMHandler._build_tax_prompt."""

    def test_prompt_contains_english_field_names(
        self, sample_payroll_input, sample_base_calculation
    ):
        """Test prompt uses English field names, not Spanish."""
        handler = _make_handler()
        prompt = handler._build_tax_prompt(sample_payroll_input, sample_base_calculation)

        assert "income_tax_monthly" in prompt
        assert "employee_contributions" in prompt
        assert "employer_contributions" in prompt
        assert "pe_risk" in prompt
        # Should NOT contain old Spanish field names
        assert "ganancias_mensual" not in prompt
        assert "aportes_employee" not in prompt

    def test_prompt_contains_input_values(
        self, sample_payroll_input, sample_base_calculation
    ):
        """Test prompt includes the input data values."""
        handler = _make_handler()
        prompt = handler._build_tax_prompt(sample_payroll_input, sample_base_calculation)

        assert str(sample_payroll_input.duration_months) in prompt
        assert "spouse" in prompt.lower() or "Spouse" in prompt
