"""
Streamlit UI components for Shadow Payroll Calculator.

This module contains all UI-related functions and page rendering logic.
"""

import logging
from typing import Optional, Tuple

import streamlit as st

from .config import config, set_openai_api_key
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


def render_header() -> None:
    """Render page header and title."""
    st.title("Shadow Payroll Calculator – Argentina 2025")
    st.caption(
        "Herramienta informativa de shadow payroll para expatriados. "
        "No constituye asesoramiento fiscal ni legal."
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
            st.subheader("🔑 Configuración")
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Ingrese su API key de OpenAI para habilitar los cálculos",
            )
            if api_key:
                st.session_state["OPENAI_API_KEY"] = api_key
                set_openai_api_key(api_key)
                st.success("API key configurada correctamente")
                st.rerun()

    return st.session_state.get("OPENAI_API_KEY")


def render_api_key_prompt() -> None:
    """Display prompt for API key if not configured."""
    st.info("👈 Inserte su API Key de OpenAI en la barra lateral para comenzar.")
    st.markdown("""
    ### ¿Cómo obtener una API Key?

    1. Visite [OpenAI Platform](https://platform.openai.com/)
    2. Inicie sesión o cree una cuenta
    3. Navegue a API Keys
    4. Genere una nueva clave
    5. Cópiela e ingrésela en la barra lateral

    **Nota de seguridad:** Su API key nunca se almacena y solo se usa durante esta sesión.
    """)


def get_fx_rate() -> Tuple[float, str, str]:
    """
    Get exchange rate from API or manual input.

    Returns:
        Tuple[float, str, str]: (rate, date, source)
    """
    fx_data = get_cached_usd_ars_rate()

    if fx_data:
        st.success(
            f"✅ Tipo de cambio automático: **{fx_data['rate']:,.2f} ARS/USD** | "
            f"Fecha: {fx_data['date']} | Fuente: {fx_data['source']}"
        )
        default_rate = fx_data["rate"]
        fx_date = fx_data["date"]
        fx_source = fx_data["source"]
    else:
        st.warning(
            "⚠️ No se pudo obtener el tipo de cambio automático. "
            "Ingrese valor manual."
        )
        default_rate = config.FX_DEFAULT_RATE
        fx_date = "Manual"
        fx_source = "Manual"

    rate = st.number_input(
        "Tipo de cambio fiscal ARS/USD",
        value=default_rate,
        min_value=1.0,
        max_value=100000.0,
        help="Tipo de cambio a utilizar para conversión USD → ARS",
    )

    return rate, fx_date, fx_source


def render_input_form() -> Optional[PayrollInput]:
    """
    Render input form and collect user data.

    Returns:
        Optional[PayrollInput]: Validated input data or None if invalid
    """
    st.subheader("📋 Datos de la Asignación")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Información Salarial**")
        salary_usd = st.number_input(
            "Salario anual home (USD)",
            value=config.DEFAULT_SALARY_USD,
            min_value=config.MIN_SALARY,
            max_value=config.MAX_SALARY,
            step=10000.0,
            help="Salario base anual en USD antes de impuestos",
        )

        duration_months = st.number_input(
            "Duración asignación (meses)",
            value=config.DEFAULT_DURATION_MONTHS,
            min_value=config.MIN_DURATION,
            max_value=config.MAX_DURATION,
            help="Duración prevista de la asignación internacional",
        )

    with col2:
        st.markdown("**Información Familiar y Beneficios**")
        has_spouse = st.checkbox(
            "Cónyuge a cargo",
            help="Indica si el empleado tiene cónyuge dependiente",
        )

        num_children = st.number_input(
            "Hijos a cargo",
            value=0,
            min_value=config.MIN_DEPENDENTS,
            max_value=config.MAX_DEPENDENTS,
            help="Número de hijos dependientes",
        )

        housing_usd = st.number_input(
            "Vivienda anual (USD)",
            value=config.DEFAULT_HOUSING_USD,
            min_value=config.MIN_BENEFIT,
            max_value=config.MAX_BENEFIT,
            step=5000.0,
            help="Subsidio anual de vivienda",
        )

        school_usd = st.number_input(
            "Escuela anual (USD)",
            value=config.DEFAULT_SCHOOL_USD,
            min_value=config.MIN_BENEFIT,
            max_value=config.MAX_BENEFIT,
            step=5000.0,
            help="Subsidio anual de educación",
        )

    # FX Rate section
    st.markdown("---")
    st.subheader("💱 Tipo de Cambio")
    fx_rate, fx_date, fx_source = get_fx_rate()

    # Create and validate input model
    try:
        input_data = PayrollInput(
            salary_usd=salary_usd,
            duration_months=duration_months,
            has_spouse=has_spouse,
            num_children=num_children,
            housing_usd=housing_usd,
            school_usd=school_usd,
            fx_rate=fx_rate,
        )
        # Store FX metadata for later use
        st.session_state["fx_date"] = fx_date
        st.session_state["fx_source"] = fx_source

        return input_data

    except Exception as e:
        st.error(f"❌ Error en validación de datos: {e}")
        logger.error(f"Input validation error: {e}")
        return None


def render_results(result: ShadowPayrollResult) -> None:
    """
    Display calculation results.

    Args:
        result: Complete shadow payroll calculation result
    """
    st.markdown("---")
    st.subheader("📊 Resultados Shadow Payroll")

    # Display results in organized sections
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**💰 Montos Mensuales (ARS)**")
        st.metric("Bruto Mensual", f"{result.base.gross_monthly_ars:,.2f}")
        st.metric("Ganancias (4ta Cat.)", f"{result.tax.ganancias_monthly:,.2f}")
        st.metric("Aportes Employee", f"{result.tax.employee_contributions:,.2f}")
        st.metric("Neto Employee", f"{result.tax.net_employee:,.2f}")

    with col2:
        st.markdown("**🏢 Costos Employer (ARS)**")
        st.metric("Aportes Employer", f"{result.tax.employer_contributions:,.2f}")
        st.metric(
            "Costo Total Employer",
            f"{result.tax.total_cost_employer:,.2f}",
            help="Costo total mensual para el empleador",
        )

        # PE Risk indicator
        risk_color = {
            "Bajo": "🟢",
            "Medio": "🟡",
            "Alto": "🔴",
            "Low": "🟢",
            "Medium": "🟡",
            "High": "🔴",
        }
        st.metric(
            "Riesgo PE",
            f"{risk_color.get(result.tax.pe_risk, '⚪')} {result.tax.pe_risk}",
        )

    # Comments section
    st.markdown("**📝 Comentarios y Alertas Fiscales**")
    st.info(result.tax.comments)

    # Metadata
    with st.expander("ℹ️ Información Adicional"):
        st.write(f"**Tipo de cambio:** {result.base.fx_rate:,.2f} ARS/USD")
        st.write(f"**Fecha FX:** {result.fx_date}")
        st.write(f"**Fuente FX:** {result.fx_source}")


def render_excel_download(result: ShadowPayrollResult) -> None:
    """
    Render Excel download button.

    Args:
        result: Calculation result to export
    """
    try:
        excel_bytes = export_to_excel(result)

        st.download_button(
            label="📊 Descargar Reporte Excel",
            data=excel_bytes,
            file_name="shadow_payroll_argentina_2025.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Descargue un reporte Excel con todos los resultados",
        )
    except Exception as e:
        st.error(f"Error generando Excel: {e}")
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
        with st.spinner("🤖 Interpretando normativa fiscal con IA..."):
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
        st.error(f"❌ Error en servicio LLM: {e}")
        logger.error(f"LLM error: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Error inesperado en cálculo: {e}")
        logger.exception("Unexpected calculation error")
        return None


def render_sidebar_info() -> None:
    """Render informational sidebar content."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ℹ️ Acerca de")
        st.markdown("""
        Esta herramienta calcula estimaciones de shadow payroll
        para asignaciones internacionales a Argentina.

        **Incluye:**
        - Cálculo de Impuesto a las Ganancias
        - Aportes y contribuciones sociales
        - Evaluación de riesgo PE
        - Alertas de compliance

        **Versión:** 2.0
        **Año fiscal:** 2025
        """)

        st.markdown("---")
        st.markdown("### ⚠️ Disclaimer")
        st.markdown("""
        Esta herramienta es solo informativa.
        No reemplaza asesoramiento profesional.
        Consulte con especialistas tributarios.
        """)
