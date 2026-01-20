"""
Core calculation logic for shadow payroll.

This module contains all deterministic payroll calculations
that don't require LLM integration.
"""

import logging
from typing import Dict, Any

from .models import PayrollInput, BaseCalculation
from .config import config

logger = logging.getLogger(__name__)


class PayrollCalculator:
    """
    Handles shadow payroll base calculations.

    This class performs the deterministic portion of shadow payroll
    calculations, converting USD amounts to ARS and computing
    monthly breakdowns.
    """

    @staticmethod
    def calculate_base(input_data: PayrollInput) -> BaseCalculation:
        """
        Calculate base shadow payroll amounts.

        Performs currency conversion and monthly breakdown calculations.
        This is the deterministic part that doesn't require LLM.

        Args:
            input_data: Validated payroll input data

        Returns:
            BaseCalculation: Base calculation results

        Example:
            >>> from models import PayrollInput
            >>> input_data = PayrollInput(
            ...     salary_usd=400000,
            ...     duration_months=36,
            ...     housing_usd=50000,
            ...     school_usd=30000,
            ...     fx_rate=1000
            ... )
            >>> calc = PayrollCalculator()
            >>> result = calc.calculate_base(input_data)
            >>> print(result.gross_monthly_ars)
        """
        logger.info(
            f"Calculating base shadow payroll: "
            f"salary=${input_data.salary_usd}, "
            f"fx_rate={input_data.fx_rate}"
        )

        # Convert annual salary to monthly ARS
        salary_monthly_ars = (input_data.salary_usd / 12) * input_data.fx_rate

        # Convert annual benefits to monthly ARS
        total_benefits_usd = input_data.housing_usd + input_data.school_usd
        benefits_monthly_ars = (total_benefits_usd / 12) * input_data.fx_rate

        # Calculate gross monthly total
        gross_monthly_ars = salary_monthly_ars + benefits_monthly_ars

        result = BaseCalculation(
            salary_monthly_ars=round(salary_monthly_ars, 2),
            benefits_monthly_ars=round(benefits_monthly_ars, 2),
            gross_monthly_ars=round(gross_monthly_ars, 2),
            fx_rate=input_data.fx_rate,
        )

        logger.info(
            f"Base calculation complete: gross_monthly={result.gross_monthly_ars} ARS"
        )

        return result

    @staticmethod
    def estimate_employee_contributions(gross_monthly_ars: float) -> float:
        """
        Estimate employee social security contributions.

        Uses configured rate (default ~17% for Argentina 2025).

        Args:
            gross_monthly_ars: Gross monthly salary in ARS

        Returns:
            float: Estimated employee contributions in ARS

        Note:
            This is a simplified estimation. Actual contributions
            may vary based on specific circumstances.
        """
        return round(
            gross_monthly_ars * config.EMPLOYEE_CONTRIBUTION_RATE, 2
        )

    @staticmethod
    def estimate_employer_contributions(gross_monthly_ars: float) -> float:
        """
        Estimate employer social security contributions.

        Uses configured rate (default ~24% for Argentina 2025).

        Args:
            gross_monthly_ars: Gross monthly salary in ARS

        Returns:
            float: Estimated employer contributions in ARS

        Note:
            This is a simplified estimation. Actual contributions
            may vary based on industry and company size.
        """
        return round(
            gross_monthly_ars * config.EMPLOYER_CONTRIBUTION_RATE, 2
        )

    @staticmethod
    def calculate_summary(
        input_data: PayrollInput, base: BaseCalculation
    ) -> Dict[str, Any]:
        """
        Generate calculation summary with key metrics.

        Args:
            input_data: Original input data
            base: Base calculation results

        Returns:
            Dict[str, Any]: Summary metrics including totals and averages
        """
        total_duration_months = input_data.duration_months
        total_gross_ars = base.gross_monthly_ars * total_duration_months

        # Estimate total costs with contributions
        employee_contrib = PayrollCalculator.estimate_employee_contributions(
            base.gross_monthly_ars
        )
        employer_contrib = PayrollCalculator.estimate_employer_contributions(
            base.gross_monthly_ars
        )

        total_cost_monthly = (
            base.gross_monthly_ars + employer_contrib - employee_contrib
        )
        total_cost_assignment = total_cost_monthly * total_duration_months

        return {
            "duration_months": total_duration_months,
            "duration_days": input_data.get_duration_in_days(),
            "salary_monthly_ars": base.salary_monthly_ars,
            "benefits_monthly_ars": base.benefits_monthly_ars,
            "gross_monthly_ars": base.gross_monthly_ars,
            "estimated_employee_contrib": employee_contrib,
            "estimated_employer_contrib": employer_contrib,
            "estimated_total_cost_monthly": total_cost_monthly,
            "total_gross_assignment_ars": total_gross_ars,
            "total_cost_assignment_ars": total_cost_assignment,
            "fx_rate": base.fx_rate,
        }


def validate_calculation_inputs(
    salary_usd: float,
    duration_months: int,
    housing_usd: float,
    school_usd: float,
    fx_rate: float,
) -> None:
    """
    Validate calculation inputs before processing.

    Args:
        salary_usd: Annual salary in USD
        duration_months: Assignment duration
        housing_usd: Annual housing benefit
        school_usd: Annual school benefit
        fx_rate: Exchange rate

    Raises:
        ValueError: If any input is invalid
    """
    if salary_usd < config.MIN_SALARY or salary_usd > config.MAX_SALARY:
        raise ValueError(
            f"Salary must be between {config.MIN_SALARY} and {config.MAX_SALARY}"
        )

    if duration_months < config.MIN_DURATION or duration_months > config.MAX_DURATION:
        raise ValueError(
            f"Duration must be between {config.MIN_DURATION} and {config.MAX_DURATION} months"
        )

    if housing_usd < 0 or school_usd < 0:
        raise ValueError("Benefits cannot be negative")

    if fx_rate <= 0:
        raise ValueError("Exchange rate must be positive")

    logger.debug("Input validation passed")
