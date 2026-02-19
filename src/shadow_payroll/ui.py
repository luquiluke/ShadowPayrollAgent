"""
Streamlit UI components for Shadow Payroll Calculator.

This module contains all UI-related functions and page rendering logic.
"""

import logging
from datetime import datetime
from typing import Optional

import streamlit as st

# Inject custom legal/corporate CSS theme
def inject_corporate_theme():
    with open(
        str((__import__('pathlib').Path(__file__).parent / "corporate_theme.css").resolve()), "r", encoding="utf-8"
    ) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

inject_corporate_theme()

from .config import config, set_openai_api_key, COUNTRIES, CURRENCIES, COUNTRY_CURRENCIES, COUNTRY_REGIONS
from .models import PayrollInput, ShadowPayrollResult, EstimationResponse, CostLineItem, PERiskAssessment
from .utils import get_cached_usd_ars_rate, get_fx_rates
from .calculations import PayrollCalculator
from .llm_handler import TaxLLMHandler, LLMError
from .estimator import CountryEstimator, EstimationError
from .excel_exporter import export_to_excel
from .scenarios import add_scenario, remove_scenario, get_scenarios, auto_name, normalize_line_items, MAX_SCENARIOS

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
    """Applies dark theme. CSS custom properties handle theming via corporate_theme.css."""
    # No JS needed -- CSS rewrite in Plan 01 handles theming entirely via CSS
    pass


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

    Also fetches and displays the host country currency rate when
    a non-Argentina host country is selected.
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

        # Host country currency rate
        host_country = st.session_state.get("host_country")
        if host_country and host_country != "Argentina":
            host_currency = COUNTRY_CURRENCIES.get(host_country, "USD")
            if host_currency != "USD":
                all_rates = get_fx_rates("USD")
                if all_rates and host_currency in all_rates.get("rates", {}):
                    host_rate = all_rates["rates"][host_currency]
                    st.session_state["fx_rate_host"] = host_rate
                    st.info(
                        f"**{host_rate:,.2f} {host_currency}/USD**\n\n"
                        f"Host country: {host_country}"
                    )
                else:
                    st.session_state["fx_rate_host"] = 1.0
            else:
                st.session_state["fx_rate_host"] = 1.0


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


# --- Multi-country estimation UI functions ---

_RATING_COLORS = {
    "Low": "#2ecc71",
    "Medium": "#f39c12",
    "High": "#e74c3c",
}


def render_estimation_results(
    result: EstimationResponse, model_name: str, timestamp: str
) -> None:
    """
    Main results page orchestrator for multi-country estimation.

    Calls sub-functions in order: cost breakdown, cost rating,
    AI insights, PE risk section, and footer disclaimer.

    Args:
        result: Validated estimation response from the LLM.
        model_name: LLM model name for metadata display.
        timestamp: Generation timestamp for metadata display.
    """
    st.markdown("---")
    render_cost_breakdown(result)
    render_cost_rating(result)
    render_insights(result)
    render_pe_risk_section(result)
    render_disclaimer_footer(model_name, timestamp)


def render_cost_breakdown(result: EstimationResponse) -> None:
    """
    Render itemized cost breakdown with dual currency display.

    Shows each line item with USD and local currency amounts.
    Range items display a low-high range with disclaimer text.

    Args:
        result: Estimation response containing line_items and totals.
    """
    st.subheader("Cost Breakdown")

    for item in result.line_items:
        col_label, col_usd, col_local = st.columns([3, 1, 1])
        with col_label:
            st.markdown(f"**{item.label}**")
            if item.is_range and item.range_disclaimer:
                st.caption(item.range_disclaimer)
        with col_usd:
            if item.is_range and item.range_low_usd is not None and item.range_high_usd is not None:
                st.markdown(f"USD {item.range_low_usd:,.0f} - {item.range_high_usd:,.0f}")
            else:
                st.markdown(f"USD {item.amount_usd:,.0f}")
        with col_local:
            if not item.is_range:
                st.markdown(f"{item.local_currency} {item.amount_local:,.0f}")

    # Total row
    st.markdown("---")
    col_label, col_usd, col_local = st.columns([3, 1, 1])
    with col_label:
        st.markdown("**Total Employer Cost**")
    with col_usd:
        st.markdown(f"**USD {result.total_employer_cost_usd:,.0f}**")
    with col_local:
        st.markdown(
            f"**{result.local_currency} {result.total_employer_cost_local:,.0f}**"
        )


def render_cost_rating(result: EstimationResponse) -> None:
    """
    Render color-coded cost rating with regional benchmark context.

    Shows overall rating as a colored badge with typical range,
    plus per-item ratings for key cost components.

    Args:
        result: Estimation response containing overall_rating and item_ratings.
    """
    st.subheader("Cost Rating")

    # Overall rating badge
    rating = result.overall_rating
    color = _RATING_COLORS.get(rating.level, "#aaa")
    low = f"USD {rating.typical_range_low_usd:,.0f}"
    high = f"USD {rating.typical_range_high_usd:,.0f}"
    st.markdown(
        f'<p style="font-size:1em; line-height:1.6;">'
        f'<span style="display:inline-block; width:12px; height:12px; '
        f'border-radius:50%; background:{color}; margin-right:6px; vertical-align:middle;"></span>'
        f'<strong>{rating.level}</strong>'
        f'<span style="color:#aaa;"> \u2014 Typical range for {rating.region_name}: '
        f'{low}\u2013{high}</span></p>',
        unsafe_allow_html=True,
    )

    # Item ratings
    for item_rating in result.item_ratings:
        item_color = _RATING_COLORS.get(item_rating.level, "#aaa")
        st.markdown(
            f'<span style="display:inline-block; width:8px; height:8px; '
            f'border-radius:50%; background:{item_color}; margin-right:4px;"></span>'
            f'{item_rating.item_label}: <strong>{item_rating.level}</strong> '
            f'<span style="color:#aaa;">{item_rating.context}</span>',
            unsafe_allow_html=True,
        )


def render_insights(result: EstimationResponse) -> None:
    """
    Render AI insights as a narrative paragraph.

    Displays the LLM-generated 2-3 sentence analysis in an info box.

    Args:
        result: Estimation response containing insights_paragraph.
    """
    st.subheader("AI Insights")
    st.info(result.insights_paragraph)


def render_pe_risk_section(result: EstimationResponse) -> None:
    """
    Render Permanent Establishment risk assessment section.

    Includes risk level badge, PE threshold info, visual timeline bar,
    threshold warning, treaty information, mitigation suggestions,
    and optional economic employer note.

    Args:
        result: Estimation response containing pe_risk assessment.
    """
    pe = result.pe_risk
    st.subheader("Permanent Establishment Risk")

    # Risk level badge
    color = _RATING_COLORS.get(pe.risk_level, "#aaa")
    st.markdown(
        f'<span style="display:inline-block; width:12px; height:12px; '
        f'border-radius:50%; background:{color}; margin-right:6px;"></span>'
        f'<strong style="font-size:1.1em;">{pe.risk_level}</strong> '
        f'<span style="color:#aaa;"> \u2014 PE threshold: {pe.pe_threshold_days} days</span>',
        unsafe_allow_html=True,
    )

    # Timeline bar
    render_pe_timeline_bar(pe.assignment_duration_days, pe.pe_threshold_days)

    # Threshold warning
    if pe.exceeds_threshold:
        months = pe.assignment_duration_days // 30
        st.warning(
            f"Your {months}-month assignment ({pe.assignment_duration_days} days) "
            f"exceeds the {pe.pe_threshold_days}-day PE threshold."
        )

    # Treaty section
    if pe.treaty_exists:
        treaty_text = ""
        if pe.treaty_name:
            treaty_text += f"**Treaty:** {pe.treaty_name}\n\n"
        if pe.treaty_implications:
            treaty_text += pe.treaty_implications
        if treaty_text:
            st.info(treaty_text)
    else:
        home = st.session_state.get("home_country", "Home")
        host = st.session_state.get("host_country", "Host")
        warning_text = pe.no_treaty_warning or (
            f"No tax treaty found between {home} and {host} -- default PE rules apply."
        )
        st.error(warning_text)

    # Mitigation suggestions
    if pe.mitigation_suggestions:
        st.markdown("**Mitigation Suggestions:**")
        for i, suggestion in enumerate(pe.mitigation_suggestions, 1):
            st.markdown(f"{i}. {suggestion}")

    # Economic employer note
    if pe.economic_employer_note:
        st.info(pe.economic_employer_note)


def render_pe_timeline_bar(duration_days: int, threshold_days: int) -> None:
    """
    Render visual timeline bar showing assignment duration vs PE threshold.

    Green bar if under threshold, red if over. White vertical line marks
    the threshold position. Duration label inside bar, threshold label above.

    Args:
        duration_days: Assignment duration in days.
        threshold_days: PE threshold in days for the country pair.
    """
    max_days = max(duration_days, threshold_days) * 1.2  # 20% padding
    duration_pct = min((duration_days / max_days) * 100, 100)
    threshold_pct = min((threshold_days / max_days) * 100, 100)
    exceeds = duration_days > threshold_days
    bar_color = "#e74c3c" if exceeds else "#2ecc71"

    html = f"""
    <div style="position:relative; height:40px; background:#2d2d2d; border-radius:8px; overflow:visible; margin:24px 0 10px 0;">
        <!-- Duration bar -->
        <div style="position:absolute; top:0; left:0; height:100%; width:{duration_pct}%;
                     background:{bar_color}; border-radius:8px 0 0 8px; transition:width 0.3s;"></div>
        <!-- Threshold marker -->
        <div style="position:absolute; top:0; left:{threshold_pct}%; height:100%; width:2px;
                     background:#ffffff; z-index:2;"></div>
        <!-- Labels -->
        <div style="position:absolute; top:50%; left:4px; transform:translateY(-50%);
                     color:white; font-size:12px; z-index:3;">
            {duration_days} days
        </div>
        <div style="position:absolute; top:-18px; left:{threshold_pct}%; transform:translateX(-50%);
                     color:#aaa; font-size:11px; white-space:nowrap;">
            PE threshold: {threshold_days} days
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_disclaimer_footer(model_name: str, timestamp: str) -> None:
    """
    Render footer disclaimer and expandable metadata section.

    Args:
        model_name: LLM model name used for the estimation.
        timestamp: Generation timestamp string.
    """
    st.markdown("---")
    st.caption(
        "This tool provides estimates only and does not constitute tax, legal, "
        "or financial advice. Users should consult qualified professionals."
    )
    with st.expander("Estimation Metadata"):
        st.write(f"Estimated by **{model_name}** on {timestamp}")


def run_estimation(
    input_data: PayrollInput, api_key: str
) -> Optional[EstimationResponse]:
    """
    Execute multi-country shadow payroll estimation.

    Creates a CountryEstimator and calls estimate() with the current
    host country FX rate from session state. Records model name and
    timestamp in session state for metadata display.

    Args:
        input_data: Validated payroll input data.
        api_key: OpenAI API key.

    Returns:
        Optional[EstimationResponse]: Estimation result or None if failed.
    """
    local_currency = COUNTRY_CURRENCIES.get(input_data.host_country, "USD")

    # Get host FX rate from session state or fall back
    if local_currency == "USD":
        fx_rate_host = 1.0
    else:
        fx_rate_host = st.session_state.get("fx_rate_host", 1.0)

    # Record metadata for display
    model_name = config.LLM_MODEL
    timestamp = datetime.now().strftime("%b %d, %Y at %H:%M")
    st.session_state["estimation_model_name"] = model_name
    st.session_state["estimation_timestamp"] = timestamp

    try:
        with st.spinner("Estimating shadow payroll costs with AI..."):
            estimator = CountryEstimator(api_key)
            result = estimator.estimate(input_data, fx_rate_host)
        return result
    except EstimationError as e:
        st.error(f"Estimation error: {e}")
        logger.error(f"Estimation error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected estimation error: {e}")
        logger.exception("Unexpected estimation error")
        return None


# --- Scenario comparison UI functions ---


def _prepare_result_for_scenario(result_dict: dict) -> dict:
    """Convert EstimationResponse.model_dump() line_items list to label->amount dict.

    scenarios.py normalize_line_items expects result["line_items"] as
    ``{label: amount_usd}`` but EstimationResponse.model_dump() produces
    a list of CostLineItem dicts.  This bridges the gap.
    """
    line_items = result_dict.get("line_items", [])
    if isinstance(line_items, list):
        result_dict = dict(result_dict)  # shallow copy
        result_dict["line_items"] = {
            item["label"]: item.get("amount_usd", 0.0)
            for item in line_items
            if isinstance(item, dict)
        }
    return result_dict


def render_scenario_controls(
    result_dict: dict,
    input_data_dict: dict,
    model_name: str,
    timestamp: str,
) -> None:
    """Render 'Save as Scenario' button and saved scenario list below estimation results.

    Args:
        result_dict: EstimationResponse as dict (from model_dump()).
        input_data_dict: PayrollInput as dict (from model_dump()).
        model_name: LLM model name used for estimation.
        timestamp: Human-readable estimation timestamp.
    """
    scenarios = get_scenarios()

    # Save button
    if len(scenarios) < MAX_SCENARIOS:
        if st.button("Save as Scenario", key="save_scenario_btn"):
            name = auto_name(input_data_dict)
            prepared = _prepare_result_for_scenario(result_dict)
            success = add_scenario(name, input_data_dict, prepared, model_name, timestamp)
            if success:
                st.success(f"Scenario saved: {name}")
                st.rerun()
    else:
        st.info(f"Maximum {MAX_SCENARIOS} scenarios reached. Remove one to add another.")


def render_saved_scenarios() -> None:
    """Show saved scenario chips/cards as a horizontal row with remove buttons."""
    scenarios = get_scenarios()
    if not scenarios:
        return

    st.markdown(f"**Scenarios ({len(scenarios)}/{MAX_SCENARIOS})**")

    cols = st.columns(len(scenarios))
    for idx, (col, scenario) in enumerate(zip(cols, scenarios)):
        with col:
            total = scenario.get("result", {}).get("total_employer_cost_usd", 0)
            st.markdown(
                f'<div style="background:var(--bg-surface, #2d3642); padding:12px; '
                f'border-radius:8px; text-align:center;">'
                f'<div style="font-weight:600; color:var(--text-primary, #f5f7fa);">'
                f'{scenario["name"]}</div>'
                f'<div style="font-family:\'JetBrains Mono\',monospace; color:var(--accent-blue, #4fc3f7); '
                f'font-size:1.1em; margin-top:4px;">${total:,.0f}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Remove", key=f"remove_scenario_{idx}"):
                remove_scenario(idx)
                st.rerun()


def render_comparison_table(scenarios: list[dict]) -> None:
    """Render color-coded comparison table when 2+ scenarios exist.

    Rows = cost categories, columns = scenarios.
    Green background on cheapest value per row, red on most expensive.
    No percentage or absolute delta numbers -- color only.

    Args:
        scenarios: List of scenario dicts from session state.
    """
    if len(scenarios) < 2:
        return

    labels, matrix = normalize_line_items(scenarios)

    # Build header row
    header_cells = '<th style="text-align:left; padding:10px 14px; border-bottom:2px solid #3a4252;">Cost Category</th>'
    for scenario in scenarios:
        header_cells += (
            f'<th style="text-align:right; padding:10px 14px; border-bottom:2px solid #3a4252;">'
            f'{scenario["name"]}</th>'
        )

    # Build data rows
    body_rows = ""
    num_scenarios = len(scenarios)
    for label_idx, label in enumerate(labels):
        row_values = [matrix[s_idx][label_idx] for s_idx in range(num_scenarios)]
        min_val = min(row_values)
        max_val = max(row_values)
        all_equal = min_val == max_val

        cells = f'<td style="padding:10px 14px; border-bottom:1px solid #3a4252;">{label}</td>'
        for val in row_values:
            bg = ""
            if not all_equal:
                if val == min_val:
                    bg = "background:rgba(46, 204, 113, 0.15);"
                elif val == max_val:
                    bg = "background:rgba(231, 76, 60, 0.15);"
            cells += (
                f'<td style="text-align:right; padding:10px 14px; border-bottom:1px solid #3a4252; '
                f"font-family:'JetBrains Mono',monospace; {bg}\">${val:,.0f}</td>"
            )
        body_rows += f"<tr>{cells}</tr>"

    # Total row
    totals = [
        s.get("result", {}).get("total_employer_cost_usd", 0.0) for s in scenarios
    ]
    min_total = min(totals)
    max_total = max(totals)
    totals_equal = min_total == max_total

    total_cells = (
        '<td style="padding:10px 14px; font-weight:700; border-top:2px solid #3a4252;">'
        "Total Employer Cost</td>"
    )
    for val in totals:
        bg = ""
        if not totals_equal:
            if val == min_total:
                bg = "background:rgba(46, 204, 113, 0.15);"
            elif val == max_total:
                bg = "background:rgba(231, 76, 60, 0.15);"
        total_cells += (
            f'<td style="text-align:right; padding:10px 14px; font-weight:700; '
            f"font-family:'JetBrains Mono',monospace; border-top:2px solid #3a4252; {bg}\">"
            f"${val:,.0f}</td>"
        )
    body_rows += f"<tr>{total_cells}</tr>"

    html = f"""
    <table style="width:100%; border-collapse:collapse; background:#2d3642; border-radius:8px;
                  color:#f5f7fa; margin:16px 0;">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{body_rows}</tbody>
    </table>
    """
    st.markdown("### Scenario Comparison")
    st.markdown(html, unsafe_allow_html=True)


def render_scenario_summary(scenarios: list[dict]) -> None:
    """Render plain-English summary identifying cheapest and most expensive scenarios.

    Only shows when 2+ scenarios exist.

    Args:
        scenarios: List of scenario dicts from session state.
    """
    if len(scenarios) < 2:
        return

    totals = [
        (s["name"], s.get("result", {}).get("total_employer_cost_usd", 0.0))
        for s in scenarios
    ]
    cheapest = min(totals, key=lambda t: t[1])
    most_expensive = max(totals, key=lambda t: t[1])

    st.markdown(
        f"**{cheapest[0]}** is the most cost-effective option. "
        f"{most_expensive[0]} has the highest total employer cost."
    )
