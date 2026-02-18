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
)
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

    # Initialize FX session state defaults
    st.session_state.setdefault("fx_rate", config.FX_DEFAULT_RATE)
    st.session_state.setdefault("fx_date", "Not yet fetched")
    st.session_state.setdefault("fx_source", "Default")
    st.session_state.setdefault("fx_stale", True)

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

    # Calculate button
    if st.button("Calculate Shadow Payroll", type="primary", use_container_width=True):
        logger.info("Estimation triggered")

        result = run_estimation(input_data, api_key)

        if result:
            model_name = st.session_state.get("estimation_model_name", config.LLM_MODEL)
            timestamp = st.session_state.get("estimation_timestamp", "Unknown")
            render_estimation_results(result, model_name, timestamp)
        else:
            logger.error("Estimation failed")


if __name__ == "__main__":
    main()
