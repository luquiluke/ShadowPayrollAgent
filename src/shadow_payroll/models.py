"""
Pydantic models for data validation and type safety.

This module defines all data models used in the Shadow Payroll Calculator
with comprehensive validation rules.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .config import config


class PayrollInput(BaseModel):
    """
    Input data for shadow payroll calculation.

    Validates all user inputs according to business rules.
    """

    model_config = ConfigDict(frozen=False, validate_assignment=True)

    salary_usd: float = Field(
        default=config.DEFAULT_SALARY_USD,
        ge=config.MIN_SALARY,
        le=config.MAX_SALARY,
        description="Annual home salary in USD",
    )

    duration_months: int = Field(
        default=config.DEFAULT_DURATION_MONTHS,
        ge=config.MIN_DURATION,
        le=config.MAX_DURATION,
        description="Assignment duration in months",
    )

    has_spouse: bool = Field(
        default=False,
        description="Whether employee has dependent spouse",
    )

    num_children: int = Field(
        default=0,
        ge=config.MIN_DEPENDENTS,
        le=config.MAX_DEPENDENTS,
        description="Number of dependent children",
    )

    housing_usd: float = Field(
        default=config.DEFAULT_HOUSING_USD,
        ge=config.MIN_BENEFIT,
        le=config.MAX_BENEFIT,
        description="Annual housing benefit in USD",
    )

    school_usd: float = Field(
        default=config.DEFAULT_SCHOOL_USD,
        ge=config.MIN_BENEFIT,
        le=config.MAX_BENEFIT,
        description="Annual school benefit in USD",
    )

    fx_rate: float = Field(
        gt=0.0,
        description="USD to ARS exchange rate",
    )

    @field_validator("salary_usd", "housing_usd", "school_usd")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        """Ensure monetary values are positive."""
        if v < 0:
            raise ValueError("Monetary values must be positive")
        return v

    @field_validator("fx_rate")
    @classmethod
    def validate_fx_rate(cls, v: float) -> float:
        """Ensure FX rate is reasonable."""
        if v <= 0:
            raise ValueError("FX rate must be positive")
        if v < 1.0:
            raise ValueError("ARS/USD rate seems too low (expected > 1)")
        if v > 100000:
            raise ValueError("ARS/USD rate seems unreasonably high")
        return v

    def get_total_benefits_usd(self) -> float:
        """Calculate total annual benefits in USD."""
        return self.housing_usd + self.school_usd

    def get_duration_in_days(self) -> int:
        """Approximate duration in days (30 days per month)."""
        return self.duration_months * 30


class BaseCalculation(BaseModel):
    """
    Base shadow payroll calculation (deterministic part).

    This represents the calculation that can be done without LLM.
    """

    model_config = ConfigDict(frozen=True)

    salary_monthly_ars: float = Field(
        description="Monthly salary in ARS",
    )

    benefits_monthly_ars: float = Field(
        description="Monthly benefits in ARS",
    )

    gross_monthly_ars: float = Field(
        description="Total gross monthly amount in ARS",
    )

    fx_rate: float = Field(
        description="Exchange rate used",
    )

    def get_annual_gross_ars(self) -> float:
        """Calculate annual gross in ARS."""
        return self.gross_monthly_ars * 12


class TaxCalculation(BaseModel):
    """
    Tax and contribution calculations (LLM-generated).

    This represents the complex tax calculations performed by the LLM.
    """

    model_config = ConfigDict(frozen=True)

    ganancias_monthly: float = Field(
        ge=0.0,
        description="Monthly Ganancias tax (income tax)",
    )

    employee_contributions: float = Field(
        ge=0.0,
        description="Monthly employee social security contributions",
    )

    net_employee: float = Field(
        ge=0.0,
        description="Net amount for employee after deductions",
    )

    employer_contributions: float = Field(
        ge=0.0,
        description="Monthly employer social security contributions",
    )

    total_cost_employer: float = Field(
        ge=0.0,
        description="Total monthly cost for employer",
    )

    pe_risk: str = Field(
        description="Permanent Establishment risk level",
    )

    comments: str = Field(
        description="Additional tax comments and alerts",
    )

    @field_validator("pe_risk")
    @classmethod
    def validate_pe_risk(cls, v: str) -> str:
        """Validate PE risk is one of expected values."""
        valid_levels = ["Bajo", "Medio", "Alto", "Low", "Medium", "High"]
        if v not in valid_levels:
            raise ValueError(f"PE risk must be one of {valid_levels}, got {v}")
        return v


class ShadowPayrollResult(BaseModel):
    """
    Complete shadow payroll calculation result.

    Combines base calculations and tax calculations.
    """

    model_config = ConfigDict(frozen=True)

    base: BaseCalculation
    tax: TaxCalculation
    fx_date: str = Field(description="Date of FX rate")
    fx_source: str = Field(description="Source of FX rate")

    def to_display_dict(self) -> dict:
        """
        Convert result to dictionary for display.

        Returns:
            dict: Formatted results for UI display
        """
        return {
            "Bruto mensual ARS": self.base.gross_monthly_ars,
            "Ganancias mensual estimado": self.tax.ganancias_monthly,
            "Aportes employee": self.tax.employee_contributions,
            "Neto employee": self.tax.net_employee,
            "Aportes employer": self.tax.employer_contributions,
            "Costo total employer": self.tax.total_cost_employer,
            "Riesgo PE": self.tax.pe_risk,
            "Comentarios": self.tax.comments,
            "Tipo de cambio": self.base.fx_rate,
            "Fecha FX": self.fx_date,
            "Fuente FX": self.fx_source,
        }


class FXRateData(BaseModel):
    """Exchange rate data from external API."""

    model_config = ConfigDict(frozen=True)

    rate: float = Field(gt=0.0, description="Exchange rate value")
    date: str = Field(description="Last update timestamp")
    source: str = Field(description="Data source name")
