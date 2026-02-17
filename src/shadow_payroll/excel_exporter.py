"""
Excel export functionality for shadow payroll reports.

This module handles generating formatted Excel reports with
proper styling and currency formatting.
"""

import logging
from io import BytesIO
from typing import Dict, Any

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .models import ShadowPayrollResult

logger = logging.getLogger(__name__)


class ExcelExporter:
    """
    Handles Excel report generation for shadow payroll results.

    Creates professionally formatted Excel files with proper
    currency formatting and cell alignment.
    """

    # Styling constants
    HEADER_FILL = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
    CURRENCY_FORMAT = '[$ARS] #,##0.00'
    COLUMN_WIDTH_LABEL = 40
    COLUMN_WIDTH_VALUE = 80

    @staticmethod
    def create_report(result: ShadowPayrollResult) -> BytesIO:
        """
        Generate Excel report from shadow payroll results.

        Args:
            result: Complete shadow payroll calculation result

        Returns:
            BytesIO: Excel file as bytes buffer ready for download

        Example:
            >>> exporter = ExcelExporter()
            >>> excel_bytes = exporter.create_report(result)
            >>> # Can be used with Streamlit download button
        """
        logger.info("Generating Excel report")

        # Convert result to display dictionary
        data = result.to_display_dict()

        # Create DataFrame
        df = pd.DataFrame(list(data.items()), columns=["Field", "Value"])

        # Create Excel file in memory
        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Shadow Payroll')

            workbook = writer.book
            worksheet = writer.sheets['Shadow Payroll']

            # Apply styling
            ExcelExporter._apply_styling(worksheet, df)

        output.seek(0)
        logger.info("Excel report generated successfully")

        return output

    @staticmethod
    def _apply_styling(worksheet, df: pd.DataFrame) -> None:
        """
        Apply formatting and styling to worksheet.

        Args:
            worksheet: openpyxl worksheet object
            df: DataFrame containing the data
        """
        # Set column widths
        worksheet.column_dimensions['A'].width = ExcelExporter.COLUMN_WIDTH_LABEL
        worksheet.column_dimensions['B'].width = ExcelExporter.COLUMN_WIDTH_VALUE

        # Style header row
        for cell in worksheet[1]:
            cell.fill = ExcelExporter.HEADER_FILL
            cell.font = ExcelExporter.HEADER_FONT
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # Apply text wrapping and alignment to all cells
        align = Alignment(wrap_text=True, vertical='top', horizontal='left')
        for row in worksheet.iter_rows(min_row=1, max_row=worksheet.max_row):
            for cell in row:
                cell.alignment = align

        # Apply ARS currency format to numeric values (rows 2-7)
        # These correspond to the monetary fields in the result
        monetary_fields = [
            "Gross Monthly (ARS)",
            "Income Tax Monthly (est.)",
            "Employee Contributions",
            "Net Employee",
            "Employer Contributions",
            "Total Employer Cost",
        ]

        for row_idx in range(2, len(df) + 2):  # +2 because Excel is 1-indexed + header
            cell_label = worksheet[f"A{row_idx}"].value
            if cell_label in monetary_fields:
                worksheet[f"B{row_idx}"].number_format = ExcelExporter.CURRENCY_FORMAT

        logger.debug("Styling applied to Excel worksheet")

    @staticmethod
    def create_detailed_report(
        result: ShadowPayrollResult, input_summary: Dict[str, Any]
    ) -> BytesIO:
        """
        Generate detailed Excel report with multiple sheets.

        Args:
            result: Shadow payroll calculation result
            input_summary: Dictionary with input parameters and additional context

        Returns:
            BytesIO: Excel file with multiple sheets

        Note:
            Creates two sheets:
            1. Summary - Main results
            2. Details - Input parameters and assumptions
        """
        logger.info("Generating detailed Excel report")

        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = result.to_display_dict()
            df_summary = pd.DataFrame(
                list(summary_data.items()), columns=["Field", "Value"]
            )
            df_summary.to_excel(writer, index=False, sheet_name='Summary')

            # Details sheet
            df_details = pd.DataFrame(
                list(input_summary.items()), columns=["Parameter", "Value"]
            )
            df_details.to_excel(writer, index=False, sheet_name='Details')

            # Apply styling to both sheets
            workbook = writer.book
            ExcelExporter._apply_styling(workbook['Summary'], df_summary)
            ExcelExporter._apply_styling(workbook['Details'], df_details)

        output.seek(0)
        logger.info("Detailed Excel report generated successfully")

        return output


def export_to_excel(result: ShadowPayrollResult) -> BytesIO:
    """
    Convenience function to export result to Excel.

    Args:
        result: Shadow payroll calculation result

    Returns:
        BytesIO: Excel file ready for download
    """
    exporter = ExcelExporter()
    return exporter.create_report(result)
