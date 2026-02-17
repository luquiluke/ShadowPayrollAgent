"""
Streamlit UI components for Shadow Payroll Calculator.

This module contains all UI-related functions and page rendering logic.
"""

import logging
from typing import Optional

import streamlit as st

# Inject custom legal/corporate CSS theme
def inject_corporate_theme():
    with open(
        str((__import__('pathlib').Path(__file__).parent / "corporate_theme.css").resolve()), "r", encoding="utf-8"
    ) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_corporate_theme()

from .config import config, set_openai_api_key, COUNTRIES, CURRENCIES
from .models import PayrollInput, ShadowPayrollResult
from .utils import get_cached_usd_ars_rate
from .calculations import PayrollCalculator
from .llm_handler import TaxLLMHandler, LLMError
from .excel_exporter import export_to_excel

logger = logging.getLogger(__name__)


def configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title=config.PAGE_TITLE,
        layout=config.PAGE_LAYOUT,
        page_icon="💼",
    )
    # Always apply dark theme
    inject_dark_theme()


def inject_dark_theme():
    """Injects the dark theme CSS and JS into the page."""
    st.markdown("<style id='corporate-theme'></style>", unsafe_allow_html=True)
    st.markdown("""
        <script>
        document.body.classList.remove('theme-light-override', 'theme-dark-override');
        document.body.classList.add('theme-dark-override');
        </script>
    """, unsafe_allow_html=True)


def render_header() -> None:
    """Render page header and title."""
    st.title("Shadow Payroll Calculator")
    st.caption(
        "Informational shadow payroll tool for expatriate assignments. "
        "This does not constitute tax or legal advice."
    )
    st.markdown("---")


def get_api_key() -> Optional[str]:
    """
    Get OpenAI API key from session state or user input.

    Returns:
        Optional[str]: API key if available, None otherwise
    """
    if "OPENAI_API_KEY" not in st.session_state:
        with st.sidebar:
            st.subheader("Configuration")
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Enter your OpenAI API key to enable calculations",
            )
            if api_key:
                st.session_state["OPENAI_API_KEY"] = api_key
                set_openai_api_key(api_key)
                st.success("API key configured successfully")
                st.rerun()

    return st.session_state.get("OPENAI_API_KEY")


def render_api_key_prompt() -> None:
    """Display prompt for API key if not configured."""
    st.info("Enter your OpenAI API Key in the sidebar to get started.")
    st.markdown("""
    ### How to get an API Key

    1. Visit [OpenAI Platform](https://platform.openai.com/)
    2. Sign in or create an account
    3. Generate a new key
    4. Copy and paste it in the sidebar

    **Security note:** Your API key is never stored and is only used during this session.
    """)


def render_fx_sidebar() -> None:
    """
    Render a persistent FX rate sidebar widget.

    Fetches the live exchange rate, displays it with metadata,
    and provides a manual override option. Populates session state
    with fx_rate, fx_date, fx_source, and fx_stale.
    """
    with st.sidebar:
        st.subheader("Exchange Rate")
        fx_data = get_cached_usd_ars_rate()

        if fx_data:
            st.info(
                f"**{fx_data['rate']:,.2f} ARS/USD**\n\n"
                f"Updated: {fx_data['date']}\n\n"
                f"Source: {fx_data['source']}"
            )
            st.session_state["fx_rate"] = fx_data["rate"]
            st.session_state["fx_date"] = fx_data["date"]
            st.session_state["fx_source"] = fx_data["source"]
            st.session_state["fx_stale"] = False
        else:
            cached_rate = st.session_state.get("fx_rate", config.FX_DEFAULT_RATE)
            st.warning(
                f"**Using cached rate: {cached_rate:,.2f} ARS/USD**\n\n"
                f"API unavailable — data may be stale"
            )
            st.session_state["fx_stale"] = True

        # Manual override
        override = st.number_input(
            "Manual FX Override",
            value=st.session_state.get("fx_rate", config.FX_DEFAULT_RATE),
            min_value=1.0,
            max_value=100000.0,
            help="Override the automatic exchange rate",
        )
        if override != st.session_state.get("fx_rate"):
            st.session_state["fx_rate"] = override
            st.session_state["fx_source"] = "Manual"
            st.session_state["fx_date"] = "Manual entry"


def render_input_form() -> Optional[PayrollInput]:
    """
    Render input form and collect user data.

    Returns:
        Optional[PayrollInput]: Validated input data or None if invalid
    """
    st.subheader("Assignment Details")

    # Read FX rate from session state (populated by render_fx_sidebar)
    fx_rate = st.session_state.get("fx_rate", config.FX_DEFAULT_RATE)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Employee & Assignment**")
        salary_usd = st.number_input(
            "Annual Home Salary (USD)",
            value=config.DEFAULT_SALARY_USD,
            min_value=config.MIN_SALARY,
            max_value=config.MAX_SALARY,
            step=10000.0,
            help="Annual base salary in USD before taxes",
        )

        duration_months = st.number_input(
            "Assignment Duration (months)",
            value=config.DEFAULT_DURATION_MONTHS,
            min_value=config.MIN_DURATION,
            max_value=config.MAX_DURATION,
            help="Expected duration of the international assignment",
        )

        home_country = st.selectbox(
            "Home Country",
            COUNTRIES,
            index=COUNTRIES.index("Argentina"),
        )

        host_country = st.selectbox(
            "Host Country",
            COUNTRIES,
            index=COUNTRIES.index("Argentina"),
        )

    with col2:
        st.markdown("**Family & Benefits**")
        has_spouse = st.checkbox(
            "Dependent Spouse",
            help="Whether the employee has a dependent spouse",
        )

        num_children = st.number_input(
            "Dependent Children",
            value=0,
            min_value=0,
            max_value=10,
        )

        housing_usd = st.number_input(
            "Annual Housing Benefit (USD)",
            value=0.0,
            min_value=0.0,
            max_value=180000.0,
            step=1000.0,
        )

        school_usd = st.number_input(
            "Annual School Benefit (USD)",
            value=0.0,
            min_value=0.0,
            max_value=120000.0,
            step=1000.0,
        )

        display_currency = st.selectbox(
            "Display Currency",
            CURRENCIES,
            index=0,
        )

    try:
        input_data = PayrollInput(
            salary_usd=salary_usd,
            duration_months=duration_months,
            has_spouse=has_spouse,
            num_children=num_children,
            housing_usd=housing_usd,
            school_usd=school_usd,
            fx_rate=fx_rate,
            home_country=home_country,
            host_country=host_country,
            display_currency=display_currency,
        )
        return input_data
    except Exception as e:
        st.error(f"Input validation error: {e}")
        logger.error(f"Input validation error: {e}")
        return None


def render_results(result: ShadowPayrollResult) -> None:
    """
    Display calculation results.

    Args:
        result: Complete shadow payroll calculation result
    """
    st.markdown("---")
    st.subheader("Shadow Payroll Results")

    # Display results in organized sections
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Monthly Amounts (ARS)**")
        st.metric("Gross Monthly", f"{result.base.gross_monthly_ars:,.2f}")
        st.metric("Income Tax (4th Cat.)", f"{result.tax.income_tax_monthly:,.2f}")
        st.metric("Employee Contributions", f"{result.tax.employee_contributions:,.2f}")
        st.metric("Net Employee", f"{result.tax.net_employee:,.2f}")

    with col2:
        st.markdown("**Employer Costs (ARS)**")
        st.metric("Employer Contributions", f"{result.tax.employer_contributions:,.2f}")
        st.metric(
            "Total Employer Cost",
            f"{result.tax.total_cost_employer:,.2f}",
            help="Total monthly cost for the employer",
        )

        # PE Risk indicator
        risk_color = {
            "Low": "🟢",
            "Medium": "🟡",
            "High": "🔴",
        }
        st.metric(
            "PE Risk",
            f"{risk_color.get(result.tax.pe_risk, '⚪')} {result.tax.pe_risk}",
        )

    # Comments section
    st.markdown("**Tax Comments & Alerts**")
    st.info(result.tax.comments)

    # Metadata
    with st.expander("Additional Information"):
        st.write(f"**Exchange Rate:** {result.base.fx_rate:,.2f} ARS/USD")
        st.write(f"**FX Date:** {result.fx_date}")
        st.write(f"**FX Source:** {result.fx_source}")
        if st.session_state.get("fx_stale", False):
            st.warning("Exchange rate data may be stale — API was unavailable")


def render_excel_download(result: ShadowPayrollResult) -> None:
    """
    Render Excel download button.

    Args:
        result: Calculation result to export
    """
    try:
        excel_bytes = export_to_excel(result)

        st.download_button(
            label="Download Excel Report",
            data=excel_bytes,
            file_name="shadow_payroll_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download an Excel report with all results",
        )
    except Exception as e:
        st.error(f"Error generating Excel: {e}")
        logger.error(f"Excel generation error: {e}")


def run_calculation(input_data: PayrollInput, api_key: str) -> Optional[ShadowPayrollResult]:
    """
    Execute shadow payroll calculation.

    Args:
        input_data: Validated input data
        api_key: OpenAI API key

    Returns:
        Optional[ShadowPayrollResult]: Calculation result or None if failed
    """
    try:
        # Step 1: Base calculation
        calculator = PayrollCalculator()
        base = calculator.calculate_base(input_data)

        # Step 2: LLM tax calculation
        with st.spinner("Analyzing tax regulations with AI..."):
            llm_handler = TaxLLMHandler(api_key=api_key)
            tax = llm_handler.calculate_tax(input_data, base)

        # Step 3: Combine results
        result = ShadowPayrollResult(
            base=base,
            tax=tax,
            fx_date=st.session_state.get("fx_date", "Unknown"),
            fx_source=st.session_state.get("fx_source", "Unknown"),
        )

        logger.info("Calculation completed successfully")
        return result

    except LLMError as e:
        st.error(f"LLM service error: {e}")
        logger.error(f"LLM error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected calculation error: {e}")
        logger.exception("Unexpected calculation error")
        return None


def render_sidebar_info() -> None:
    """Render informational sidebar content."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This tool calculates shadow payroll estimates
        for international assignments.

        **Includes:**
        - Income tax calculation
        - Social security contributions
        - PE risk assessment
        - Compliance alerts

        **Version:** 2.0
        """)

        st.markdown("---")
        st.markdown("### Disclaimer")
        st.markdown("""
        This tool is for informational purposes only.
        It does not replace professional advice.
        Consult with tax specialists.
        """)
