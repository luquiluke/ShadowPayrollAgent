"""
Country-agnostic estimation engine using LangChain structured output.

This module provides the CountryEstimator class that replaces the
Argentina-only TaxLLMHandler for multi-country shadow payroll estimation.
Uses LangChain's with_structured_output() to get validated Pydantic
models directly from LLM calls.
"""

import logging
from typing import Dict

import streamlit as st
from langchain_openai import ChatOpenAI
from openai import OpenAIError

from .config import config, COUNTRY_REGIONS, COUNTRY_CURRENCIES
from .models import PayrollInput, EstimationResponse

logger = logging.getLogger(__name__)


class EstimationError(Exception):
    """Custom exception for estimation failures."""

    pass


class CountryEstimator:
    """
    Multi-country shadow payroll estimator using LLM structured output.

    Uses LangChain's with_structured_output() to return validated
    EstimationResponse models directly from LLM calls, eliminating
    manual JSON parsing.
    """

    def __init__(self, api_key: str) -> None:
        """
        Initialize the estimator with an OpenAI API key.

        Args:
            api_key: OpenAI API key for LLM calls.
        """
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            api_key=api_key,
            timeout=config.LLM_TIMEOUT,
        )
        self.structured_llm = self.llm.with_structured_output(
            EstimationResponse, strict=False
        )
        logger.info(
            f"Initialized CountryEstimator with model {config.LLM_MODEL}"
        )

    def estimate(
        self, input_data: PayrollInput, fx_rate_host: float
    ) -> EstimationResponse:
        """
        Estimate shadow payroll costs for any country pair.

        Args:
            input_data: Validated payroll input with country pair and assignment details.
            fx_rate_host: Exchange rate from USD to host country local currency.

        Returns:
            EstimationResponse: Validated structured estimation with line items,
                ratings, PE risk, and insights.

        Raises:
            EstimationError: If the LLM call fails or returns invalid data.
        """
        region = COUNTRY_REGIONS.get(input_data.host_country, "Global")
        local_currency = COUNTRY_CURRENCIES.get(
            input_data.host_country, "USD"
        )
        prompt = self._build_prompt(
            input_data, fx_rate_host, region, local_currency
        )

        try:
            cached_dict = self._cached_estimate(prompt)
            return EstimationResponse(**cached_dict)
        except EstimationError:
            raise
        except Exception as e:
            logger.error(f"Estimation failed: {e}")
            raise EstimationError(f"Estimation failed: {e}") from e

    @st.cache_data(ttl=config.LLM_CACHE_TTL, show_spinner=False)
    def _cached_estimate(_self, prompt: str) -> Dict:
        """
        Cached LLM call that returns a serializable dict.

        Uses _self prefix to exclude the instance from the Streamlit cache key.
        Returns a dict (via model_dump) for cache serialization; the caller
        reconstructs the EstimationResponse.

        Args:
            prompt: The estimation prompt to send to the LLM.

        Returns:
            Dict: EstimationResponse as a dictionary.

        Raises:
            EstimationError: If the LLM call fails.
        """
        try:
            logger.info("Making structured LLM call for estimation")
            result = _self.structured_llm.invoke(prompt)
            logger.info("Structured LLM call successful")
            return result.model_dump()
        except OpenAIError as e:
            logger.error(f"OpenAI API error during estimation: {e}")
            raise EstimationError(f"OpenAI API error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during estimation: {e}")
            raise EstimationError(f"Unexpected error: {e}") from e

    def _build_prompt(
        self,
        input_data: PayrollInput,
        fx_rate: float,
        region: str,
        local_currency: str,
    ) -> str:
        """
        Build the multi-country estimation prompt.

        Args:
            input_data: Validated payroll input.
            fx_rate: USD to host country currency exchange rate.
            region: Regional benchmark group (e.g., "Western Europe").
            local_currency: ISO 4217 currency code for host country.

        Returns:
            str: Formatted prompt for the structured LLM call.
        """
        duration_days = input_data.duration_months * 30

        return f"""You are a senior international tax and expatriate compensation specialist.

Estimate the annual shadow payroll costs for an expatriate assignment:

**Assignment Details:**
- Home country: {input_data.home_country}
- Host country: {input_data.host_country}
- Annual base salary: USD {input_data.salary_usd:,.0f}
- Assignment duration: {input_data.duration_months} months ({duration_days} days)
- Housing allowance: USD {input_data.housing_usd:,.0f}/year
- School allowance: USD {input_data.school_usd:,.0f}/year
- Dependent spouse: {"Yes" if input_data.has_spouse else "No"}
- Dependent children: {input_data.num_children}
- Host country currency: {local_currency} (1 USD = {fx_rate:,.2f} {local_currency})
- Region for benchmarking: {region}

**Instructions:**
1. Provide an itemized annual cost breakdown with these line items at minimum:
   - Income Tax (host country)
   - Social Security - Employee contributions
   - Social Security - Employer contributions
   - PE Administration / Compliance costs
   - Housing Allowance (pass-through with any tax gross-up)
   - School / Education Allowance (pass-through with any tax gross-up)
   - Total Employer Cost
   If any item is not applicable for the host country, still include it with amount 0 and a note in the range_disclaimer field.

2. For each item, provide amounts in both USD and {local_currency}.

3. If you cannot estimate a specific line item with confidence, set is_range to true and provide a reasonable low/high range with an explanation.

4. Rate the total cost and key items (income tax, social security) as Low/Medium/High compared to the {region} regional average. Include the typical range for this region.

5. Assess Permanent Establishment (PE) risk:
   - What is the PE day threshold for {input_data.home_country} -> {input_data.host_country}?
   - Does a tax treaty exist between these countries?
   - Does the {input_data.duration_months}-month ({duration_days}-day) duration exceed the threshold?
   - Provide 1-2 specific mitigation suggestions
   - If no treaty exists, explicitly warn about double taxation risk
   - If relevant, note the distinction between economic employer and legal employer

6. Write a 2-3 sentence insights paragraph explaining the key cost drivers and any optimization opportunities. Write as an expert advisor, not as a data dump.

Important: All amounts should be ANNUAL, not monthly."""


def create_estimator(api_key: str) -> CountryEstimator:
    """
    Factory function to create a CountryEstimator.

    Args:
        api_key: OpenAI API key.

    Returns:
        CountryEstimator: Configured estimator instance.
    """
    return CountryEstimator(api_key=api_key)
