"""
Shadow Payroll Calculator Package

A comprehensive tool for calculating shadow payroll estimates
for international assignments to Argentina.
"""

__version__ = "2.0.0"
__author__ = "Shadow Payroll Team"

from .config import config
from .models import PayrollInput, ShadowPayrollResult
from .calculations import PayrollCalculator
from .llm_handler import TaxLLMHandler
from .utils import get_cached_usd_ars_rate
from .excel_exporter import export_to_excel

__all__ = [
    "config",
    "PayrollInput",
    "ShadowPayrollResult",
    "PayrollCalculator",
    "TaxLLMHandler",
    "get_cached_usd_ars_rate",
    "export_to_excel",
]
