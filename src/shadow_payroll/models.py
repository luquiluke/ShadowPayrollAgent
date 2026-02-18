"""
Pydantic models for data validation and type safety.

This module defines all data models used in the Shadow Payroll Calculator
with comprehensive validation rules.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .config import config, COUNTRIES, CURRENCIES


class PayrollInput(BaseModel):
    """
    Input data for shadow payroll calculation.

    Validates all user inputs according to business rules.
    """

    model_config = ConfigDict(validate_assignment=True)

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
        le=config.MAX_HOUSING_USD,
        description="Annual housing benefit in USD",
    )

    school_usd: float = Field(
        default=config.DEFAULT_SCHOOL_USD,
        ge=config.MIN_BENEFIT,
        le=config.MAX_SCHOOL_USD,
        description="Annual school benefit in USD",
    )

    fx_rate: float = Field(
        gt=0.0,
        description="USD to host country currency exchange rate",
    )

    home_country: str = Field(
        default="Argentina",
        description="Employee home country",
    )

    host_country: str = Field(
        default="Argentina",
        description="Host/assignment country",
    )

    display_currency: str = Field(
        default="USD",
        description="Preferred display currency",
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
            raise ValueError("Exchange rate must be positive")
        if v > 100000:
            raise ValueError("Exchange rate seems unreasonably high")
        return v

    @field_validator("home_country", "host_country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        """Ensure country is in the supported list."""
        if v not in COUNTRIES:
            raise ValueError(f"Country must be one of {COUNTRIES}, got {v}")
        return v

    @field_validator("display_currency")
    @classmethod
    def validate_display_currency(cls, v: str) -> str:
        """Ensure currency is in the supported list."""
        if v not in CURRENCIES:
            raise ValueError(f"Currency must be one of {CURRENCIES}, got {v}")
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

    income_tax_monthly: float = Field(
        ge=0.0,
        description="Monthly income tax estimate",
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
        valid_levels = ["Low", "Medium", "High"]
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
            "Gross Monthly (ARS)": self.base.gross_monthly_ars,
            "Income Tax Monthly (est.)": self.tax.income_tax_monthly,
            "Employee Contributions": self.tax.employee_contributions,
            "Net Employee": self.tax.net_employee,
            "Employer Contributions": self.tax.employer_contributions,
            "Total Employer Cost": self.tax.total_cost_employer,
            "PE Risk": self.tax.pe_risk,
            "Comments": self.tax.comments,
            "Exchange Rate": self.base.fx_rate,
            "FX Date": self.fx_date,
            "FX Source": self.fx_source,
        }


class FXRateData(BaseModel):
    """Exchange rate data from external API."""

    model_config = ConfigDict(frozen=True)

    rate: float = Field(gt=0.0, description="Exchange rate value")
    date: str = Field(description="Last update timestamp")
    source: str = Field(description="Data source name")


# --- Multi-country estimation response models ---


class CostLineItem(BaseModel):
    """Single cost component in the breakdown."""

    model_config = ConfigDict(frozen=True)

    label: str = Field(description="Cost item name, e.g. 'Income Tax', 'Employer Social Security'")
    amount_usd: float = Field(description="Annual amount in USD")
    amount_local: float = Field(description="Annual amount in host country local currency")
    local_currency: str = Field(description="ISO 4217 currency code for local amount, e.g. 'EUR'")
    is_range: bool = Field(
        description="True if this is an estimate range rather than a specific amount"
    )
    range_low_usd: Optional[float] = Field(
        default=None, description="Low end of range in USD if is_range is True"
    )
    range_high_usd: Optional[float] = Field(
        default=None, description="High end of range in USD if is_range is True"
    )
    range_disclaimer: Optional[str] = Field(
        default=None, description="Explanation for why a range is shown instead of specific amount"
    )


class CostRating(BaseModel):
    """Cost rating against regional benchmarks."""

    model_config = ConfigDict(frozen=True)

    level: str = Field(description="One of 'Low', 'Medium', 'High'")
    region_name: str = Field(description="Region name, e.g. 'Western Europe'")
    typical_range_low_usd: float = Field(
        description="Low end of typical range for this region in USD"
    )
    typical_range_high_usd: float = Field(
        description="High end of typical range for this region in USD"
    )


class ItemRating(BaseModel):
    """Rating for a specific cost item."""

    model_config = ConfigDict(frozen=True)

    item_label: str = Field(description="Which line item this rating applies to")
    level: str = Field(description="One of 'Low', 'Medium', 'High'")
    context: str = Field(description="Brief context like 'Above average for Western Europe'")


class PERiskAssessment(BaseModel):
    """Permanent Establishment risk assessment."""

    model_config = ConfigDict(frozen=True)

    risk_level: str = Field(description="One of 'Low', 'Medium', 'High'")
    pe_threshold_days: int = Field(description="PE day threshold for this country pair")
    assignment_duration_days: int = Field(description="Assignment duration in days")
    exceeds_threshold: bool = Field(description="Whether assignment exceeds PE threshold")
    treaty_exists: bool = Field(
        description="Whether a tax treaty exists between the two countries"
    )
    treaty_name: Optional[str] = Field(
        default=None, description="Name of the tax treaty if it exists"
    )
    treaty_implications: Optional[str] = Field(
        default=None, description="How the treaty affects PE risk"
    )
    no_treaty_warning: Optional[str] = Field(
        default=None, description="Warning text if no treaty exists"
    )
    mitigation_suggestions: list[str] = Field(
        description="1-2 actionable suggestions to mitigate PE risk"
    )
    economic_employer_note: Optional[str] = Field(
        default=None,
        description="Note about economic vs legal employer if relevant",
    )


class EstimationResponse(BaseModel):
    """Complete multi-country shadow payroll estimation."""

    model_config = ConfigDict(frozen=True)

    # Cost breakdown
    line_items: list[CostLineItem] = Field(description="Itemized cost breakdown")
    total_employer_cost_usd: float = Field(
        description="Total annual employer cost in USD"
    )
    total_employer_cost_local: float = Field(
        description="Total annual employer cost in local currency"
    )
    local_currency: str = Field(
        description="ISO 4217 currency code for the host country"
    )

    # Cost rating
    overall_rating: CostRating = Field(
        description="Overall cost rating against regional benchmarks"
    )
    item_ratings: list[ItemRating] = Field(
        description="Ratings for key items: income tax and social security"
    )

    # PE risk
    pe_risk: PERiskAssessment = Field(
        description="Permanent Establishment risk assessment"
    )

    # AI insights
    insights_paragraph: str = Field(
        description="2-3 sentence narrative analysis of cost drivers and optimization opportunities, written as expert advice"
    )
