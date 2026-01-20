"""
Unit tests for calculation module.
"""

import pytest
from shadow_payroll.models import PayrollInput, BaseCalculation
from shadow_payroll.calculations import PayrollCalculator, validate_calculation_inputs


class TestPayrollCalculator:
    """Test suite for PayrollCalculator class."""

    def test_calculate_base_basic(self):
        """Test basic calculation with simple inputs."""
        input_data = PayrollInput(
            salary_usd=120000.0,
            duration_months=12,
            has_spouse=False,
            num_children=0,
            housing_usd=24000.0,
            school_usd=12000.0,
            fx_rate=1000.0,
        )

        calculator = PayrollCalculator()
        result = calculator.calculate_base(input_data)

        # Monthly salary: 120000 / 12 = 10000 USD * 1000 = 10,000,000 ARS
        assert result.salary_monthly_ars == 10_000_000.0

        # Monthly benefits: (24000 + 12000) / 12 = 3000 USD * 1000 = 3,000,000 ARS
        assert result.benefits_monthly_ars == 3_000_000.0

        # Gross: 10,000,000 + 3,000,000 = 13,000,000 ARS
        assert result.gross_monthly_ars == 13_000_000.0

        # Check FX rate is preserved
        assert result.fx_rate == 1000.0

    def test_calculate_base_with_different_fx_rate(self):
        """Test calculation with different FX rate."""
        input_data = PayrollInput(
            salary_usd=100000.0,
            duration_months=12,
            housing_usd=0.0,
            school_usd=0.0,
            fx_rate=1200.0,
        )

        calculator = PayrollCalculator()
        result = calculator.calculate_base(input_data)

        # Monthly salary: 100000 / 12 = 8333.33 USD * 1200 = 10,000,000 ARS
        expected_salary = (100000.0 / 12) * 1200.0
        assert result.salary_monthly_ars == round(expected_salary, 2)

    def test_calculate_base_zero_benefits(self):
        """Test calculation with zero benefits."""
        input_data = PayrollInput(
            salary_usd=150000.0,
            duration_months=24,
            housing_usd=0.0,
            school_usd=0.0,
            fx_rate=1000.0,
        )

        calculator = PayrollCalculator()
        result = calculator.calculate_base(input_data)

        assert result.benefits_monthly_ars == 0.0
        assert result.gross_monthly_ars == result.salary_monthly_ars

    def test_estimate_employee_contributions(self):
        """Test employee contribution estimation."""
        gross = 10_000_000.0  # 10M ARS
        contributions = PayrollCalculator.estimate_employee_contributions(gross)

        # Should be ~17% of gross
        expected = gross * 0.17
        assert contributions == round(expected, 2)

    def test_estimate_employer_contributions(self):
        """Test employer contribution estimation."""
        gross = 10_000_000.0  # 10M ARS
        contributions = PayrollCalculator.estimate_employer_contributions(gross)

        # Should be ~24% of gross
        expected = gross * 0.24
        assert contributions == round(expected, 2)

    def test_calculate_summary(self):
        """Test calculation summary generation."""
        input_data = PayrollInput(
            salary_usd=120000.0,
            duration_months=12,
            housing_usd=24000.0,
            school_usd=12000.0,
            fx_rate=1000.0,
        )

        calculator = PayrollCalculator()
        base = calculator.calculate_base(input_data)
        summary = calculator.calculate_summary(input_data, base)

        assert summary["duration_months"] == 12
        assert summary["duration_days"] == 360
        assert "gross_monthly_ars" in summary
        assert "total_cost_assignment_ars" in summary


class TestValidateCalculationInputs:
    """Test suite for input validation."""

    def test_validate_valid_inputs(self):
        """Test validation with valid inputs."""
        # Should not raise any exception
        validate_calculation_inputs(
            salary_usd=100000.0,
            duration_months=12,
            housing_usd=20000.0,
            school_usd=10000.0,
            fx_rate=1000.0,
        )

    def test_validate_salary_too_low(self):
        """Test validation fails with negative salary."""
        with pytest.raises(ValueError, match="Salary must be between"):
            validate_calculation_inputs(
                salary_usd=-1000.0,
                duration_months=12,
                housing_usd=0.0,
                school_usd=0.0,
                fx_rate=1000.0,
            )

    def test_validate_salary_too_high(self):
        """Test validation fails with excessive salary."""
        with pytest.raises(ValueError, match="Salary must be between"):
            validate_calculation_inputs(
                salary_usd=99_000_000.0,  # Way too high
                duration_months=12,
                housing_usd=0.0,
                school_usd=0.0,
                fx_rate=1000.0,
            )

    def test_validate_duration_too_short(self):
        """Test validation fails with duration < 1."""
        with pytest.raises(ValueError, match="Duration must be between"):
            validate_calculation_inputs(
                salary_usd=100000.0,
                duration_months=0,
                housing_usd=0.0,
                school_usd=0.0,
                fx_rate=1000.0,
            )

    def test_validate_duration_too_long(self):
        """Test validation fails with duration > 60."""
        with pytest.raises(ValueError, match="Duration must be between"):
            validate_calculation_inputs(
                salary_usd=100000.0,
                duration_months=100,
                housing_usd=0.0,
                school_usd=0.0,
                fx_rate=1000.0,
            )

    def test_validate_negative_benefits(self):
        """Test validation fails with negative benefits."""
        with pytest.raises(ValueError, match="Benefits cannot be negative"):
            validate_calculation_inputs(
                salary_usd=100000.0,
                duration_months=12,
                housing_usd=-1000.0,
                school_usd=0.0,
                fx_rate=1000.0,
            )

    def test_validate_zero_fx_rate(self):
        """Test validation fails with zero FX rate."""
        with pytest.raises(ValueError, match="Exchange rate must be positive"):
            validate_calculation_inputs(
                salary_usd=100000.0,
                duration_months=12,
                housing_usd=0.0,
                school_usd=0.0,
                fx_rate=0.0,
            )

    def test_validate_negative_fx_rate(self):
        """Test validation fails with negative FX rate."""
        with pytest.raises(ValueError, match="Exchange rate must be positive"):
            validate_calculation_inputs(
                salary_usd=100000.0,
                duration_months=12,
                housing_usd=0.0,
                school_usd=0.0,
                fx_rate=-100.0,
            )
