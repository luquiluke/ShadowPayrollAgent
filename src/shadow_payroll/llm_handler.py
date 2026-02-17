"""
LLM integration for tax calculations.

This module handles all interactions with OpenAI's GPT models
for complex tax and compliance analysis.
"""

import json
import logging
from typing import Optional

import streamlit as st
from langchain_openai import ChatOpenAI
from openai import OpenAIError

from .config import config
from .models import PayrollInput, BaseCalculation, TaxCalculation
from .utils import clean_llm_json_response

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Custom exception for LLM-related errors."""

    pass


class TaxLLMHandler:
    """
    Handles LLM interactions for tax calculations.

    This class manages prompts, API calls, and response parsing
    for tax-related calculations that require expert knowledge.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM handler.

        Args:
            api_key: OpenAI API key. If None, will try to get from environment.

        Raises:
            ValueError: If API key is not provided and not in environment
        """
        if not api_key:
            from .config import get_openai_api_key

            api_key = get_openai_api_key()

        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            api_key=api_key,
            timeout=config.LLM_TIMEOUT,
        )
        logger.info(f"Initialized LLM handler with model {config.LLM_MODEL}")

    def _build_tax_prompt(
        self, input_data: PayrollInput, base: BaseCalculation
    ) -> str:
        """
        Build comprehensive tax calculation prompt.

        Args:
            input_data: Original payroll input
            base: Base calculation results

        Returns:
            str: Formatted prompt for LLM
        """
        prompt = f"""
You are a senior specialist in Argentine Income Tax, payroll, and expatriates (2025).

Case data:
- Gross monthly ARS: {base.gross_monthly_ars:,.2f}
- Salary monthly ARS: {base.salary_monthly_ars:,.2f}
- Benefits monthly ARS: {base.benefits_monthly_ars:,.2f}
- Dependent spouse: {"Yes" if input_data.has_spouse else "No"}
- Dependent children: {input_data.num_children}
- Assignment duration (months): {input_data.duration_months}
- FX rate used: {input_data.fx_rate:,.2f} ARS/USD

Instructions:
1. Calculate estimated monthly shadow payroll for Argentina (2025).
2. Include:
   - Income tax (Ganancias, 4th category) considering personal deductions
   - Employee contributions (~17%): retirement, health insurance, PAMI
   - Employer contributions (~24%): employer social charges
3. Evaluate Permanent Establishment (PE) risk considering:
   - Assignment duration (>183 days = higher risk)
   - Type of activities
   - Physical presence in Argentina
4. Flag any tax or compliance alerts as applicable.

Important considerations:
- Personal deductions vary based on spouse and dependent children
- The non-taxable minimum must be applied correctly
- Percentages are approximate and may vary

Respond ONLY with valid JSON, no Markdown, with this exact structure:
{{
  "income_tax_monthly": <number>,
  "employee_contributions": <number>,
  "net_employee": <number>,
  "employer_contributions": <number>,
  "total_cost_employer": <number>,
  "pe_risk": "Low | Medium | High",
  "comments": "<detailed analysis text>"
}}

IMPORTANT: Your response must be only the JSON, without additional explanations or markdown formatting.
"""
        return prompt

    @st.cache_data(ttl=config.LLM_CACHE_TTL, show_spinner=False)
    def _cached_llm_call(_self, prompt: str) -> str:
        """
        Cached LLM API call.

        Uses Streamlit cache to avoid repeated calls with same inputs.
        The _self parameter has underscore prefix to exclude from cache key.

        Args:
            prompt: The prompt to send to LLM

        Returns:
            str: Raw LLM response

        Raises:
            LLMError: If API call fails
        """
        try:
            logger.info("Making LLM API call")
            response = _self.llm.invoke(prompt)
            logger.info("LLM API call successful")
            return response.content
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling LLM: {e}")
            raise LLMError(f"Unexpected error: {e}")

    def calculate_tax(
        self, input_data: PayrollInput, base: BaseCalculation
    ) -> TaxCalculation:
        """
        Calculate taxes and contributions using LLM.

        This method uses the LLM to perform complex tax calculations
        that require expert knowledge of Argentine tax law.

        Args:
            input_data: Original payroll input
            base: Base calculation results

        Returns:
            TaxCalculation: Validated tax calculation results

        Raises:
            LLMError: If LLM call fails
            ValueError: If LLM response is invalid

        Example:
            >>> handler = TaxLLMHandler(api_key="sk-...")
            >>> input_data = PayrollInput(...)
            >>> base = BaseCalculation(...)
            >>> tax_result = handler.calculate_tax(input_data, base)
            >>> print(tax_result.pe_risk)
        """
        prompt = self._build_tax_prompt(input_data, base)

        logger.info("Requesting tax calculation from LLM")

        try:
            # Get response (cached if available)
            raw_response = self._cached_llm_call(prompt)

            # Clean response (remove markdown fences)
            cleaned_response = clean_llm_json_response(raw_response)

            # Parse JSON
            try:
                response_data = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.debug(f"Raw response: {raw_response}")
                logger.debug(f"Cleaned response: {cleaned_response}")
                raise ValueError(
                    f"LLM returned invalid JSON: {e}\n"
                    f"Response: {cleaned_response[:200]}..."
                )

            # Validate and create TaxCalculation model
            try:
                tax_calc = TaxCalculation(
                    income_tax_monthly=response_data["income_tax_monthly"],
                    employee_contributions=response_data["employee_contributions"],
                    net_employee=response_data["net_employee"],
                    employer_contributions=response_data["employer_contributions"],
                    total_cost_employer=response_data["total_cost_employer"],
                    pe_risk=response_data["pe_risk"],
                    comments=response_data["comments"],
                )
                logger.info("Tax calculation successful")
                return tax_calc

            except KeyError as e:
                logger.error(f"Missing required field in LLM response: {e}")
                raise ValueError(
                    f"LLM response missing required field: {e}\n"
                    f"Response: {response_data}"
                )
            except Exception as e:
                logger.error(f"Failed to validate LLM response: {e}")
                raise ValueError(f"Invalid LLM response data: {e}")

        except LLMError:
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in tax calculation: {e}")
            raise LLMError(f"Tax calculation failed: {e}")


def create_llm_handler(api_key: str) -> TaxLLMHandler:
    """
    Factory function to create TaxLLMHandler.

    Args:
        api_key: OpenAI API key

    Returns:
        TaxLLMHandler: Configured handler instance
    """
    return TaxLLMHandler(api_key=api_key)
