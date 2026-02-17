"""
Utility functions for Shadow Payroll Calculator.

This module contains helper functions for FX rates, JSON cleaning,
and other utility operations.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import requests
import streamlit as st

from .config import config

logger = logging.getLogger(__name__)


class FXRateError(Exception):
    """Custom exception for FX rate retrieval errors."""

    pass


def get_usd_ars_rate() -> Optional[Dict[str, Any]]:
    """
    Fetch USD to ARS exchange rate from external API.

    Uses open.er-api.com (free, no API key required).
    Implements caching via Streamlit's cache mechanism.

    Returns:
        Optional[Dict[str, Any]]: Dictionary containing:
            - rate (float): The exchange rate
            - date (str): Last update timestamp
            - source (str): Data source name
        Returns None if request fails.

    Raises:
        FXRateError: If API returns invalid data

    Example:
        >>> fx_data = get_usd_ars_rate()
        >>> if fx_data:
        ...     print(f"Rate: {fx_data['rate']} ARS/USD")
    """
    try:
        logger.info(f"Fetching FX rate from {config.FX_API_URL}")

        response = requests.get(
            config.FX_API_URL, timeout=config.FX_API_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()

        if data.get("result") != "success":
            logger.error(f"FX API returned non-success result: {data.get('result')}")
            raise FXRateError(f"API returned result: {data.get('result')}")

        if "ARS" not in data.get("rates", {}):
            logger.error("ARS rate not found in API response")
            raise FXRateError("ARS rate not available")

        rate_data = {
            "rate": round(data["rates"]["ARS"], 2),
            "date": data.get("time_last_update_utc", datetime.utcnow().isoformat()),
            "source": "open.er-api.com",
        }

        logger.info(f"Successfully fetched FX rate: {rate_data['rate']} ARS/USD")
        return rate_data

    except requests.RequestException as e:
        logger.error(f"HTTP request failed for FX rate: {e}")
        return None
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse FX rate response: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching FX rate: {e}")
        return None


@st.cache_data(ttl=config.FX_CACHE_TTL)
def get_cached_usd_ars_rate() -> Optional[Dict[str, Any]]:
    """
    Cached version of get_usd_ars_rate.

    Uses Streamlit's cache to avoid repeated API calls.
    Cache expires after FX_CACHE_TTL seconds (default: 1 hour).

    Returns:
        Optional[Dict[str, Any]]: Same as get_usd_ars_rate
    """
    return get_usd_ars_rate()


def clean_llm_json_response(text: str) -> str:
    """
    Remove markdown code fences from LLM JSON responses.

    Many LLMs wrap JSON output in ```json ... ``` blocks.
    This function strips those markers for clean parsing.

    Args:
        text: Raw LLM response text

    Returns:
        str: Cleaned JSON string ready for parsing

    Example:
        >>> raw = '```json\\n{"key": "value"}\\n```'
        >>> clean = clean_llm_json_response(raw)
        >>> print(clean)
        {"key": "value"}
    """
    text = text.strip()

    # Remove markdown code fences
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    logger.debug(f"Cleaned LLM response: {text[:100]}...")
    return text


def format_currency_ars(amount: float) -> str:
    """
    Format amount as Argentine Pesos currency.

    Args:
        amount: Numeric amount to format

    Returns:
        str: Formatted currency string

    Example:
        >>> format_currency_ars(1234567.89)
        'ARS 1,234,567.89'
    """
    return f"ARS {amount:,.2f}"


def calculate_pe_risk_level(duration_months: int) -> str:
    """
    Determine Permanent Establishment (PE) risk level.

    Based on Argentine tax law, assignments longer than 183 days
    (approximately 6 months) may trigger PE concerns.

    Args:
        duration_months: Assignment duration in months

    Returns:
        str: Risk level - "Low", "Medium", or "High"

    Example:
        >>> calculate_pe_risk_level(3)
        'Low'
        >>> calculate_pe_risk_level(12)
        'High'
    """
    days = duration_months * 30  # Approximate conversion

    if days < config.PE_RISK_THRESHOLD_DAYS:
        return "Low"
    elif days < config.PE_RISK_THRESHOLD_DAYS + 90:  # 183-273 days
        return "Medium"
    else:
        return "High"


def validate_positive_number(value: float, field_name: str) -> None:
    """
    Validate that a number is positive.

    Args:
        value: Number to validate
        field_name: Name of field for error messages

    Raises:
        ValueError: If value is negative
    """
    if value < 0:
        raise ValueError(f"{field_name} must be positive, got {value}")


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default on division by zero.

    Args:
        numerator: Top number
        denominator: Bottom number
        default: Value to return if denominator is zero

    Returns:
        float: Result of division or default value
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default
