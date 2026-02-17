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

    # Render FX sidebar (populates session state with FX data)
    render_fx_sidebar()

    # Render sidebar
    render_sidebar_info()

    # Render input form
    input_data = render_input_form()

    if not input_data:
        logger.warning("Invalid input data")
        return

    # Calculate button
    if st.button("Calculate Shadow Payroll", type="primary", use_container_width=True):
        logger.info("Calculation triggered")

        result = run_calculation(input_data, api_key)

        if result:
            render_results(result)
            render_excel_download(result)
        else:
            logger.error("Calculation failed")


if __name__ == "__main__":
    main()
