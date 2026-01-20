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
Sos un especialista senior en Impuesto a las Ganancias Argentina, payroll y expatriados (año 2025).

Datos del caso:
- Bruto mensual ARS: {base.gross_monthly_ars:,.2f}
- Salario mensual ARS: {base.salary_monthly_ars:,.2f}
- Beneficios mensuales ARS: {base.benefits_monthly_ars:,.2f}
- Cónyuge a cargo: {"Sí" if input_data.has_spouse else "No"}
- Hijos a cargo: {input_data.num_children}
- Duración asignación (meses): {input_data.duration_months}
- FX utilizado: {input_data.fx_rate:,.2f} ARS/USD

Instrucciones:
1. Calculá shadow payroll mensual estimado 2025 para Argentina.
2. Incluí:
   - Impuesto a las Ganancias (4ta categoría) considerando deducciones personales
   - Aportes employee (~17%): jubilación, obra social, PAMI
   - Aportes employer (~24%): contribuciones patronales
3. Evaluá riesgo de Establecimiento Permanente (PE) considerando:
   - Duración de la asignación (>183 días = mayor riesgo)
   - Tipo de actividades
   - Presencia física en Argentina
4. Indicá alertas fiscales y de compliance si corresponden.

Consideraciones importantes:
- Las deducciones personales varían según cónyuge e hijos a cargo
- El mínimo no imponible debe aplicarse correctamente
- Los porcentajes son aproximados y pueden variar

Respondé SOLO con JSON válido, sin Markdown, con esta estructura exacta:
{{
  "ganancias_mensual": <número>,
  "aportes_employee": <número>,
  "neto_employee": <número>,
  "aportes_employer": <número>,
  "total_cost_employer": <número>,
  "pe_risk": "Bajo | Medio | Alto",
  "comentarios": "<texto con análisis detallado>"
}}

IMPORTANTE: Tu respuesta debe ser únicamente el JSON, sin explicaciones adicionales ni formato markdown.
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
                    ganancias_monthly=response_data["ganancias_mensual"],
                    employee_contributions=response_data["aportes_employee"],
                    net_employee=response_data["neto_employee"],
                    employer_contributions=response_data["aportes_employer"],
                    total_cost_employer=response_data["total_cost_employer"],
                    pe_risk=response_data["pe_risk"],
                    comments=response_data["comentarios"],
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
