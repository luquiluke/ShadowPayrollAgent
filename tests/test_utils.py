"""
Unit tests for utility functions.
"""

import json

import pytest
from unittest.mock import patch, MagicMock

from shadow_payroll.utils import (
    clean_llm_json_response,
    format_currency_ars,
    calculate_pe_risk_level,
    validate_positive_number,
    safe_divide,
    get_usd_ars_rate,
    FXRateError,
)
from shadow_payroll.config import get_openai_api_key, set_openai_api_key


class TestCleanLLMJsonResponse:
    """Test suite for clean_llm_json_response function."""

    def test_clean_json_with_backticks(self):
        """Test cleaning JSON wrapped in markdown fences."""
        raw = '```json\n{"key": "value"}\n```'
        cleaned = clean_llm_json_response(raw)
        assert cleaned == '{"key": "value"}'

    def test_clean_json_without_json_keyword(self):
        """Test cleaning with backticks but no 'json' keyword."""
        raw = '```\n{"key": "value"}\n```'
        cleaned = clean_llm_json_response(raw)
        assert cleaned == '{"key": "value"}'

    def test_clean_already_clean_json(self):
        """Test cleaning already clean JSON."""
        raw = '{"key": "value"}'
        cleaned = clean_llm_json_response(raw)
        assert cleaned == '{"key": "value"}'

    def test_clean_with_whitespace(self):
        """Test cleaning JSON with surrounding whitespace."""
        raw = '  \n  {"key": "value"}  \n  '
        cleaned = clean_llm_json_response(raw)
        assert cleaned == '{"key": "value"}'


class TestFormatCurrencyARS:
    """Test suite for format_currency_ars function."""

    def test_format_positive_amount(self):
        """Test formatting positive currency amount."""
        result = format_currency_ars(1234567.89)
        assert result == "ARS 1,234,567.89"

    def test_format_zero(self):
        """Test formatting zero amount."""
        result = format_currency_ars(0.0)
        assert result == "ARS 0.00"

    def test_format_negative_amount(self):
        """Test formatting negative amount."""
        result = format_currency_ars(-500.50)
        assert result == "ARS -500.50"

    def test_format_large_amount(self):
        """Test formatting large amount."""
        result = format_currency_ars(123456789.99)
        assert result == "ARS 123,456,789.99"


class TestCalculatePERiskLevel:
    """Test suite for calculate_pe_risk_level function."""

    def test_low_risk_short_duration(self):
        """Test low risk for short assignments."""
        assert calculate_pe_risk_level(3) == "Low"
        assert calculate_pe_risk_level(1) == "Low"

    def test_medium_risk_borderline(self):
        """Test medium risk for borderline durations."""
        # 6 months = 180 days (just under threshold)
        assert calculate_pe_risk_level(6) == "Low"

        # 7 months = 210 days (just over threshold)
        assert calculate_pe_risk_level(7) == "Medium"

    def test_high_risk_long_duration(self):
        """Test high risk for long assignments."""
        assert calculate_pe_risk_level(12) == "High"
        assert calculate_pe_risk_level(24) == "High"
        assert calculate_pe_risk_level(36) == "High"

    def test_threshold_exactly_183_days(self):
        """Test exactly at PE threshold."""
        # 183 days ÷ 30 = 6.1 months
        assert calculate_pe_risk_level(6) == "Low"
        # 7 months = 210 days (over threshold)
        assert calculate_pe_risk_level(7) == "Medium"


class TestValidatePositiveNumber:
    """Test suite for validate_positive_number function."""

    def test_valid_positive_number(self):
        """Test validation passes for positive number."""
        # Should not raise exception
        validate_positive_number(100.0, "Test Value")
        validate_positive_number(0.01, "Test Value")

    def test_zero_allowed(self):
        """Test zero is allowed (not negative)."""
        # Should not raise exception
        validate_positive_number(0.0, "Test Value")

    def test_negative_number_rejected(self):
        """Test negative number raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_number(-50.0, "Salary")

    def test_error_message_includes_field_name(self):
        """Test error message includes field name."""
        with pytest.raises(ValueError, match="Salary must be positive"):
            validate_positive_number(-100.0, "Salary")


class TestSafeDivide:
    """Test suite for safe_divide function."""

    def test_normal_division(self):
        """Test normal division."""
        assert safe_divide(10.0, 2.0) == 5.0
        assert safe_divide(100.0, 4.0) == 25.0

    def test_division_by_zero_returns_default(self):
        """Test division by zero returns default value."""
        assert safe_divide(10.0, 0.0, default=0.0) == 0.0
        assert safe_divide(100.0, 0.0, default=999.0) == 999.0

    def test_division_by_zero_default_is_zero(self):
        """Test default value is 0.0 when not specified."""
        assert safe_divide(10.0, 0.0) == 0.0

    def test_negative_numbers(self):
        """Test division with negative numbers."""
        assert safe_divide(-10.0, 2.0) == -5.0
        assert safe_divide(10.0, -2.0) == -5.0

    def test_decimal_result(self):
        """Test division resulting in decimal."""
        assert safe_divide(10.0, 3.0) == pytest.approx(3.333333, rel=1e-5)


class TestCalculatePERiskLevelEnglish:
    """Additional PE risk tests confirming English-only return values."""

    def test_returns_low_for_short(self):
        assert calculate_pe_risk_level(3) == "Low"

    def test_returns_medium_for_borderline(self):
        assert calculate_pe_risk_level(7) == "Medium"

    def test_returns_high_for_long(self):
        assert calculate_pe_risk_level(12) == "High"

    def test_never_returns_spanish(self):
        """Ensure no Spanish values returned for any duration."""
        for months in range(1, 60):
            result = calculate_pe_risk_level(months)
            assert result in ("Low", "Medium", "High"), f"Unexpected: {result}"
            assert result not in ("Bajo", "Medio", "Alto"), f"Spanish found: {result}"


class TestGetUsdArsRate:
    """Test suite for get_usd_ars_rate with mocked HTTP."""

    @patch("shadow_payroll.utils.requests.get")
    def test_successful_api_response(self, mock_get):
        """Test successful FX rate fetch from API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "success",
            "rates": {"ARS": 1050.75},
            "time_last_update_utc": "Mon, 20 Jan 2025 00:00:01 +0000",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_usd_ars_rate()
        assert result is not None
        assert result["rate"] == 1050.75
        assert result["source"] == "open.er-api.com"
        assert "date" in result

    @patch("shadow_payroll.utils.requests.get")
    def test_failed_api_returns_none(self, mock_get):
        """Test failed API call returns None."""
        mock_get.side_effect = Exception("Connection refused")

        result = get_usd_ars_rate()
        assert result is None

    @patch("shadow_payroll.utils.requests.get")
    def test_api_non_success_result_returns_none(self, mock_get):
        """Test non-success API result returns None."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "error"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_usd_ars_rate()
        assert result is None

    @patch("shadow_payroll.utils.requests.get")
    def test_api_missing_ars_rate_returns_none(self, mock_get):
        """Test API response without ARS rate returns None."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "success",
            "rates": {"EUR": 0.85},
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_usd_ars_rate()
        assert result is None


class TestCleanLLMJsonResponseExtended:
    """Additional edge cases for clean_llm_json_response."""

    def test_nested_json_in_fences(self):
        """Test nested JSON inside markdown fences."""
        raw = '```json\n{"a": {"b": [1, 2, 3]}}\n```'
        cleaned = clean_llm_json_response(raw)
        parsed = json.loads(cleaned)
        assert parsed["a"]["b"] == [1, 2, 3]

    def test_multiple_backtick_blocks(self):
        """Test cleaning with only opening/closing backticks."""
        raw = '```\n{"key": "value"}\n```'
        cleaned = clean_llm_json_response(raw)
        assert json.loads(cleaned) == {"key": "value"}

    def test_empty_string(self):
        """Test cleaning empty string."""
        cleaned = clean_llm_json_response("")
        assert cleaned == ""

    def test_plain_text_not_json(self):
        """Test cleaning plain text that isn't JSON."""
        raw = "This is just text"
        cleaned = clean_llm_json_response(raw)
        assert cleaned == "This is just text"


class TestFormatCurrencyARSExtended:
    """Additional format_currency_ars tests."""

    def test_small_amount(self):
        """Test formatting small amount."""
        result = format_currency_ars(0.01)
        assert result == "ARS 0.01"

    def test_exact_integer(self):
        """Test formatting exact integer amount."""
        result = format_currency_ars(1000.0)
        assert result == "ARS 1,000.00"


class TestFXRateError:
    """Test FXRateError custom exception."""

    def test_fx_rate_error_is_exception(self):
        """Test FXRateError is a proper exception."""
        with pytest.raises(FXRateError):
            raise FXRateError("Rate unavailable")

    def test_fx_rate_error_message(self):
        """Test FXRateError carries message."""
        err = FXRateError("test message")
        assert str(err) == "test message"


class TestGetUsdArsRateEdgeCases:
    """Edge cases for FX rate fetching."""

    @patch("shadow_payroll.utils.requests.get")
    def test_http_timeout_returns_none(self, mock_get):
        """Test HTTP timeout returns None."""
        import requests

        mock_get.side_effect = requests.Timeout("Request timed out")
        result = get_usd_ars_rate()
        assert result is None

    @patch("shadow_payroll.utils.requests.get")
    def test_invalid_json_returns_none(self, mock_get):
        """Test invalid JSON response returns None."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("err", "doc", 0)
        mock_get.return_value = mock_response

        result = get_usd_ars_rate()
        assert result is None


class TestConfigHelpers:
    """Test config helper functions."""

    def test_set_and_get_openai_api_key(self):
        """Test setting and retrieving API key via environment."""
        import os

        original = os.environ.get("OPENAI_API_KEY")
        try:
            set_openai_api_key("sk-test-12345")
            assert get_openai_api_key() == "sk-test-12345"
        finally:
            if original is not None:
                os.environ["OPENAI_API_KEY"] = original
            else:
                os.environ.pop("OPENAI_API_KEY", None)
