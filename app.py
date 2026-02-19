"""
Shadow Payroll Calculator - Main Application Entry Point

This is the main entry point for the Streamlit application.
Run with: streamlit run app.py
"""

import logging
import sys
from pathlib import Path

import streamlit as st

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from shadow_payroll.ui import (
    configure_page,
    render_header,
    get_api_key,
    render_api_key_prompt,
    render_fx_sidebar,
    render_input_form,
    render_results,
    render_excel_download,
    run_calculation,
    run_estimation,
    render_estimation_results,
    render_sidebar_info,
    render_scenario_controls,
    render_saved_scenarios,
    render_comparison_table,
    render_scenario_summary,
)
from shadow_payroll.scenarios import get_scenarios
from shadow_payroll.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    logger.info("Starting Shadow Payroll Calculator")

    # Configure page
    configure_page()

    # Render header
    render_header()

    # Check for API key
    api_key = get_api_key()

    if not api_key:
        render_api_key_prompt()
        render_sidebar_info()
        return

    # Initialize session state defaults
    st.session_state.setdefault("fx_rate", config.FX_DEFAULT_RATE)
    st.session_state.setdefault("fx_date", "Not yet fetched")
    st.session_state.setdefault("fx_source", "Default")
    st.session_state.setdefault("fx_stale", True)
    st.session_state.setdefault("scenarios", [])

    # Render sidebar
    render_sidebar_info()

    # Render input form (populates host_country in session state)
    input_data = render_input_form()

    if not input_data:
        logger.warning("Invalid input data")
        return

    # Store host_country in session state so FX sidebar can react
    st.session_state["host_country"] = input_data.host_country
    st.session_state["home_country"] = input_data.home_country

    # Render FX sidebar AFTER host_country is known
    render_fx_sidebar()

    # Calculate button -- run estimation and store in session state
    if st.button("Calculate Shadow Payroll", type="primary", use_container_width=True):
        logger.info("Estimation triggered")

        result = run_estimation(input_data, api_key)

        if result:
            model_name = st.session_state.get("estimation_model_name", config.LLM_MODEL)
            timestamp = st.session_state.get("estimation_timestamp", "Unknown")
            # Persist result across Streamlit reruns
            st.session_state["last_result"] = result.model_dump()
            st.session_state["last_input"] = input_data.model_dump()
            st.session_state["last_model_name"] = model_name
            st.session_state["last_timestamp"] = timestamp
            st.session_state["last_result_obj"] = result
        else:
            logger.error("Estimation failed")

    # Re-render last result if it exists (persists across reruns)
    if "last_result" in st.session_state:
        result_obj = st.session_state.get("last_result_obj")
        model_name = st.session_state.get("last_model_name", config.LLM_MODEL)
        timestamp = st.session_state.get("last_timestamp", "Unknown")

        if result_obj is not None:
            render_estimation_results(result_obj, model_name, timestamp)

        # Scenario controls below results
        render_scenario_controls(
            st.session_state["last_result"],
            st.session_state["last_input"],
            model_name,
            timestamp,
        )

    # Saved scenarios section (always shown if scenarios exist)
    render_saved_scenarios()

    # Comparison section (2+ scenarios)
    scenarios = get_scenarios()
    if len(scenarios) >= 2:
        st.markdown("---")
        render_comparison_table(scenarios)
        render_scenario_summary(scenarios)


if __name__ == "__main__":
    main()
