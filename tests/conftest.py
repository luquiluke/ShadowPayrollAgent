"""
Pytest configuration and shared fixtures.
"""

import pytest
from shadow_payroll.models import PayrollInput, BaseCalculation, TaxCalculation


@pytest.fixture
def sample_payroll_input():
    """Fixture providing sample PayrollInput for tests."""
    return PayrollInput(
        salary_usd=100000.0,
        duration_months=12,
        has_spouse=True,
        num_children=2,
        housing_usd=20000.0,
        school_usd=15000.0,
        fx_rate=1000.0,
    )


@pytest.fixture
def sample_base_calculation():
    """Fixture providing sample BaseCalculation for tests."""
    return BaseCalculation(
        salary_monthly_ars=8_333_333.0,
        benefits_monthly_ars=2_916_667.0,
        gross_monthly_ars=11_250_000.0,
        fx_rate=1000.0,
    )


@pytest.fixture
def sample_tax_calculation():
    """Fixture providing sample TaxCalculation for tests."""
    return TaxCalculation(
        income_tax_monthly=500000.0,
        employee_contributions=1_912_500.0,
        net_employee=8_837_500.0,
        employer_contributions=2_700_000.0,
        total_cost_employer=13_950_000.0,
        pe_risk="High",
        comments="Long-term assignment exceeds 183 days. High PE risk.",
    )


@pytest.fixture
def mock_fx_data():
    """Fixture providing mock FX rate data."""
    return {
        "rate": 1000.0,
        "date": "2025-01-20T12:00:00Z",
        "source": "open.er-api.com",
    }
