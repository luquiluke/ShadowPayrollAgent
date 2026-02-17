"""
Unit tests for Pydantic models.
"""

import pytest
from pydantic import ValidationError
from shadow_payroll.models import (
    PayrollInput,
    BaseCalculation,
    TaxCalculation,
    ShadowPayrollResult,
    FXRateData,
)


class TestPayrollInput:
    """Test suite for PayrollInput model."""

    def test_valid_input(self):
        """Test creating valid PayrollInput."""
        input_data = PayrollInput(
            salary_usd=100000.0,
            duration_months=12,
            has_spouse=True,
            num_children=2,
            housing_usd=20000.0,
            school_usd=15000.0,
            fx_rate=1000.0,
        )

        assert input_data.salary_usd == 100000.0
        assert input_data.duration_months == 12
        assert input_data.has_spouse is True
        assert input_data.num_children == 2

    def test_default_values(self):
        """Test default values are applied."""
        input_data = PayrollInput(fx_rate=1000.0)

        assert input_data.has_spouse is False
        assert input_data.num_children == 0
        assert input_data.home_country == "Argentina"
        assert input_data.host_country == "Argentina"
        assert input_data.display_currency == "USD"

    def test_negative_salary_rejected(self):
        """Test negative salary is rejected."""
        with pytest.raises(ValidationError):
            PayrollInput(salary_usd=-50000.0, fx_rate=1000.0)

    def test_excessive_children_rejected(self):
        """Test excessive number of children is rejected."""
        with pytest.raises(ValidationError):
            PayrollInput(num_children=20, fx_rate=1000.0)

    def test_zero_fx_rate_rejected(self):
        """Test zero FX rate is rejected."""
        with pytest.raises(ValidationError):
            PayrollInput(fx_rate=0.0)

    def test_negative_fx_rate_rejected(self):
        """Test negative FX rate is rejected."""
        with pytest.raises(ValidationError):
            PayrollInput(fx_rate=-100.0)

    def test_unreasonably_low_fx_rate_rejected(self):
        """Test unreasonably low FX rate is rejected."""
        with pytest.raises(ValidationError, match="rate seems too low"):
            PayrollInput(fx_rate=0.5)

    def test_unreasonably_high_fx_rate_rejected(self):
        """Test unreasonably high FX rate is rejected."""
        with pytest.raises(ValidationError, match="unreasonably high"):
            PayrollInput(fx_rate=200000.0)

    def test_get_total_benefits_usd(self):
        """Test total benefits calculation."""
        input_data = PayrollInput(
            housing_usd=30000.0, school_usd=20000.0, fx_rate=1000.0
        )

        assert input_data.get_total_benefits_usd() == 50000.0

    def test_get_duration_in_days(self):
        """Test duration conversion to days."""
        input_data = PayrollInput(duration_months=12, fx_rate=1000.0)

        assert input_data.get_duration_in_days() == 360

    def test_invalid_country_rejected(self):
        """Test invalid country is rejected."""
        with pytest.raises(ValidationError):
            PayrollInput(fx_rate=1000.0, home_country="Narnia")

    def test_invalid_currency_rejected(self):
        """Test invalid currency is rejected."""
        with pytest.raises(ValidationError):
            PayrollInput(fx_rate=1000.0, display_currency="XYZ")


class TestBaseCalculation:
    """Test suite for BaseCalculation model."""

    def test_valid_base_calculation(self):
        """Test creating valid BaseCalculation."""
        base = BaseCalculation(
            salary_monthly_ars=10_000_000.0,
            benefits_monthly_ars=2_000_000.0,
            gross_monthly_ars=12_000_000.0,
            fx_rate=1000.0,
        )

        assert base.gross_monthly_ars == 12_000_000.0

    def test_base_calculation_is_frozen(self):
        """Test BaseCalculation is immutable."""
        base = BaseCalculation(
            salary_monthly_ars=10_000_000.0,
            benefits_monthly_ars=2_000_000.0,
            gross_monthly_ars=12_000_000.0,
            fx_rate=1000.0,
        )

        with pytest.raises(ValidationError):
            base.fx_rate = 1200.0

    def test_get_annual_gross_ars(self):
        """Test annual gross calculation."""
        base = BaseCalculation(
            salary_monthly_ars=10_000_000.0,
            benefits_monthly_ars=2_000_000.0,
            gross_monthly_ars=12_000_000.0,
            fx_rate=1000.0,
        )

        assert base.get_annual_gross_ars() == 144_000_000.0


class TestTaxCalculation:
    """Test suite for TaxCalculation model."""

    def test_valid_tax_calculation(self):
        """Test creating valid TaxCalculation."""
        tax = TaxCalculation(
            income_tax_monthly=500000.0,
            employee_contributions=1_700_000.0,
            net_employee=8_000_000.0,
            employer_contributions=2_400_000.0,
            total_cost_employer=14_400_000.0,
            pe_risk="Medium",
            comments="Test comments",
        )

        assert tax.pe_risk == "Medium"

    def test_negative_income_tax_rejected(self):
        """Test negative tax amount is rejected."""
        with pytest.raises(ValidationError):
            TaxCalculation(
                income_tax_monthly=-500000.0,
                employee_contributions=1_700_000.0,
                net_employee=8_000_000.0,
                employer_contributions=2_400_000.0,
                total_cost_employer=14_400_000.0,
                pe_risk="Low",
                comments="Test",
            )

    def test_invalid_pe_risk_rejected(self):
        """Test invalid PE risk level is rejected."""
        with pytest.raises(ValidationError, match="PE risk must be one of"):
            TaxCalculation(
                income_tax_monthly=500000.0,
                employee_contributions=1_700_000.0,
                net_employee=8_000_000.0,
                employer_contributions=2_400_000.0,
                total_cost_employer=14_400_000.0,
                pe_risk="Invalid",
                comments="Test",
            )

    def test_english_pe_risk_accepted(self):
        """Test English PE risk levels are accepted."""
        tax = TaxCalculation(
            income_tax_monthly=500000.0,
            employee_contributions=1_700_000.0,
            net_employee=8_000_000.0,
            employer_contributions=2_400_000.0,
            total_cost_employer=14_400_000.0,
            pe_risk="High",
            comments="Test",
        )

        assert tax.pe_risk == "High"


class TestShadowPayrollResult:
    """Test suite for ShadowPayrollResult model."""

    def test_valid_result(self):
        """Test creating valid ShadowPayrollResult."""
        base = BaseCalculation(
            salary_monthly_ars=10_000_000.0,
            benefits_monthly_ars=2_000_000.0,
            gross_monthly_ars=12_000_000.0,
            fx_rate=1000.0,
        )

        tax = TaxCalculation(
            income_tax_monthly=500000.0,
            employee_contributions=1_700_000.0,
            net_employee=8_000_000.0,
            employer_contributions=2_400_000.0,
            total_cost_employer=14_400_000.0,
            pe_risk="Low",
            comments="All good",
        )

        result = ShadowPayrollResult(
            base=base, tax=tax, fx_date="2025-01-20", fx_source="open.er-api.com"
        )

        assert result.fx_date == "2025-01-20"
        assert result.base.gross_monthly_ars == 12_000_000.0

    def test_to_display_dict(self):
        """Test conversion to display dictionary."""
        base = BaseCalculation(
            salary_monthly_ars=10_000_000.0,
            benefits_monthly_ars=2_000_000.0,
            gross_monthly_ars=12_000_000.0,
            fx_rate=1000.0,
        )

        tax = TaxCalculation(
            income_tax_monthly=500000.0,
            employee_contributions=1_700_000.0,
            net_employee=8_000_000.0,
            employer_contributions=2_400_000.0,
            total_cost_employer=14_400_000.0,
            pe_risk="Low",
            comments="All good",
        )

        result = ShadowPayrollResult(
            base=base, tax=tax, fx_date="2025-01-20", fx_source="Test"
        )

        display_dict = result.to_display_dict()

        assert "Gross Monthly (ARS)" in display_dict
        assert "Income Tax Monthly (est.)" in display_dict
        assert display_dict["Exchange Rate"] == 1000.0
        assert display_dict["FX Source"] == "Test"


class TestFXRateData:
    """Test suite for FXRateData model."""

    def test_valid_fx_rate_data(self):
        """Test creating valid FXRateData."""
        fx_data = FXRateData(
            rate=1000.0, date="2025-01-20T12:00:00Z", source="open.er-api.com"
        )

        assert fx_data.rate == 1000.0
        assert fx_data.source == "open.er-api.com"

    def test_zero_rate_rejected(self):
        """Test zero rate is rejected."""
        with pytest.raises(ValidationError):
            FXRateData(rate=0.0, date="2025-01-20", source="Test")

    def test_negative_rate_rejected(self):
        """Test negative rate is rejected."""
        with pytest.raises(ValidationError):
            FXRateData(rate=-100.0, date="2025-01-20", source="Test")
