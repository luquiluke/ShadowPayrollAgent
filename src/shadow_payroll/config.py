"""
Configuration management for Shadow Payroll Calculator.

This module centralizes all configuration values, environment variables,
and application settings.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Main application configuration."""

    # Streamlit Settings
    PAGE_TITLE: str = "Shadow Payroll Calculator Argentina 2025"
    PAGE_LAYOUT: str = "centered"

    # LLM Settings
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.0
    LLM_TIMEOUT: int = 30  # seconds

    # FX API Settings
    FX_API_URL: str = "https://open.er-api.com/v6/latest/USD"
    FX_API_TIMEOUT: int = 5  # seconds
    FX_CACHE_TTL: int = 3600  # 1 hour in seconds
    FX_DEFAULT_RATE: float = 1000.0  # Fallback rate

    # Calculation Defaults
    DEFAULT_SALARY_USD: float = 400000.0
    DEFAULT_DURATION_MONTHS: int = 36
    DEFAULT_HOUSING_USD: float = 50000.0
    DEFAULT_SCHOOL_USD: float = 30000.0

    # Validation Constraints
    MIN_SALARY: float = 0.0
    MAX_SALARY: float = 10_000_000.0
    MIN_DURATION: int = 1
    MAX_DURATION: int = 60
    MIN_DEPENDENTS: int = 0
    MAX_DEPENDENTS: int = 10
    MIN_BENEFIT: float = 0.0
    MAX_BENEFIT: float = 1_000_000.0
    MAX_HOUSING_USD: float = 180_000.0  # $15k/month * 12
    MAX_SCHOOL_USD: float = 120_000.0  # $10k/month * 12

    # Argentina Tax Constants (2025)
    EMPLOYEE_CONTRIBUTION_RATE: float = 0.17  # ~17%
    EMPLOYER_CONTRIBUTION_RATE: float = 0.24  # ~24%
    PE_RISK_THRESHOLD_DAYS: int = 183

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Cache Settings
    ENABLE_CACHE: bool = True
    LLM_CACHE_TTL: int = 3600  # 1 hour

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        config = cls()

        # Override with environment variables if present
        config.LLM_MODEL = os.getenv("LLM_MODEL", config.LLM_MODEL)
        config.LLM_TEMPERATURE = float(
            os.getenv("LLM_TEMPERATURE", str(config.LLM_TEMPERATURE))
        )
        config.FX_API_URL = os.getenv("FX_API_URL", config.FX_API_URL)
        config.LOG_LEVEL = os.getenv("LOG_LEVEL", config.LOG_LEVEL)

        return config


def get_openai_api_key() -> Optional[str]:
    """
    Get OpenAI API key from environment.

    Returns:
        Optional[str]: API key if found, None otherwise
    """
    return os.getenv("OPENAI_API_KEY")


def set_openai_api_key(api_key: str) -> None:
    """
    Set OpenAI API key in environment.

    Args:
        api_key: The OpenAI API key to set
    """
    os.environ["OPENAI_API_KEY"] = api_key


# Global configuration instance
config = AppConfig.from_env()

# Country list for expat assignments (curated common destinations)
COUNTRIES: list[str] = [
    "Argentina",
    "Australia",
    "Brazil",
    "Canada",
    "Chile",
    "China",
    "Colombia",
    "France",
    "Germany",
    "India",
    "Ireland",
    "Italy",
    "Japan",
    "Mexico",
    "Netherlands",
    "New Zealand",
    "Peru",
    "Philippines",
    "Poland",
    "Portugal",
    "Singapore",
    "South Korea",
    "Spain",
    "Sweden",
    "Switzerland",
    "United Arab Emirates",
    "United Kingdom",
    "United States",
    "Uruguay",
    "Other",
]

# Supported display currencies
CURRENCIES: list[str] = [
    "USD",
    "EUR",
    "GBP",
    "ARS",
    "BRL",
    "CAD",
    "CHF",
    "CNY",
    "JPY",
    "MXN",
    "SGD",
    "AUD",
]

# Country to region mapping for benchmark comparison
COUNTRY_REGIONS: dict[str, str] = {
    "Argentina": "Latin America",
    "Australia": "Asia-Pacific",
    "Brazil": "Latin America",
    "Canada": "North America",
    "Chile": "Latin America",
    "China": "Asia-Pacific",
    "Colombia": "Latin America",
    "France": "Western Europe",
    "Germany": "Western Europe",
    "India": "South Asia",
    "Ireland": "Western Europe",
    "Italy": "Western Europe",
    "Japan": "Asia-Pacific",
    "Mexico": "Latin America",
    "Netherlands": "Western Europe",
    "New Zealand": "Asia-Pacific",
    "Peru": "Latin America",
    "Philippines": "Asia-Pacific",
    "Poland": "Central & Eastern Europe",
    "Portugal": "Western Europe",
    "Singapore": "Asia-Pacific",
    "South Korea": "Asia-Pacific",
    "Spain": "Western Europe",
    "Sweden": "Northern Europe",
    "Switzerland": "Western Europe",
    "United Arab Emirates": "Middle East",
    "United Kingdom": "Western Europe",
    "United States": "North America",
    "Uruguay": "Latin America",
    "Other": "Global",
}

# Country to ISO 4217 currency code mapping
COUNTRY_CURRENCIES: dict[str, str] = {
    "Argentina": "ARS",
    "Australia": "AUD",
    "Brazil": "BRL",
    "Canada": "CAD",
    "Chile": "CLP",
    "China": "CNY",
    "Colombia": "COP",
    "France": "EUR",
    "Germany": "EUR",
    "India": "INR",
    "Ireland": "EUR",
    "Italy": "EUR",
    "Japan": "JPY",
    "Mexico": "MXN",
    "Netherlands": "EUR",
    "New Zealand": "NZD",
    "Peru": "PEN",
    "Philippines": "PHP",
    "Poland": "PLN",
    "Portugal": "EUR",
    "Singapore": "SGD",
    "South Korea": "KRW",
    "Spain": "EUR",
    "Sweden": "SEK",
    "Switzerland": "CHF",
    "United Arab Emirates": "AED",
    "United Kingdom": "GBP",
    "United States": "USD",
    "Uruguay": "UYU",
    "Other": "USD",
}
