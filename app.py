import streamlit as st
import pandas as pd
from io import BytesIO
import os
import json
import requests
from openpyxl.styles import Alignment
from langchain_openai import ChatOpenAI

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Shadow Payroll Calculator Argentina 2025",
    layout="centered"
)

st.title("Shadow Payroll Calculator – Argentina 2025")
st.caption(
    "Herramienta informativa de shadow payroll para expatriados. "
    "No constituye asesoramiento fiscal ni legal."
)

# =========================
# OPENAI API KEY (SAFE LOAD)
# =========================

if "OPENAI_API_KEY" not in st.session_state:
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    if api_key:
        st.session_state["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_API_KEY"] = api_key

if "OPENAI_API_KEY" not in st.session_state:
    st.info("Inserte su API Key de OpenAI en la columna izquierda.")
    st.stop()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# =========================
# FX – USD / ARS (GRATIS + ARS)
# =========================

def obtener_tipo_cambio_usd_ars():
    """
    Fuente: open.er-api.com
    Gratis, sin API key, soporta ARS
    """
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()

        if data.get("result") != "success":
            return None

        return {
            "rate": round(data["rates"]["ARS"], 2),
            "date": data.get("time_last_update_utc"),
            "source": "open.er-api.com"
        }
    except Exception:
        return None

# =========================
# INPUTS
# =========================

col1, col2 = st.columns(2)

with col1:
    salario_usd = st.number_input("Salario anual home (USD)", value=400000.0)
    duracion_meses = st.number_input("Duración asignación (meses)", min_value=1, value=36)

with col2:
    conyuge = st.checkbox("Cónyuge a cargo")
    hijos = st.number_input("Hijos a cargo", min_value=0, value=0)
    vivienda_usd = st.number_input("Vivienda anual (USD)", value=50000.0)
    escuela_usd = st.number_input("Escuela anual (USD)", value=30000.0)

# =========================
# FX UI (FECHA + FUENTE)
# =========================

fx_data = obtener_tipo_cambio_usd_ars()

if fx_data:
    st.success(
        f"FX automático: {fx_data['rate']} ARS/USD | "
        f"Fecha: {fx_data['date']} | Fuente: {fx_data['source']}"
    )
    tipo_cambio_default = fx_data["rate"]
    fx_date = fx_data["date"]
    fx_source = fx_data["source"]
else:
    st.warning("No se pudo obtener el FX automático. Ingrese valor manual.")
    tipo_cambio_default = 1000.0
    fx_date = "Manual"
    fx_source = "Manual"

tipo_cambio = st.number_input(
    "Tipo de cambio fiscal ARS/USD",
    value=tipo_cambio_default
)

# =========================
# CÁLCULO BASE (DETERMINÍSTICO)
# =========================

def calcular_base_shadow():
    salario_mensual_ars = (salario_usd / 12) * tipo_cambio
    beneficios_mensual_ars = ((vivienda_usd + escuela_usd) / 12) * tipo_cambio
    bruto = salario_mensual_ars + beneficios_mensual_ars

    return {
        "salario_mensual_ars": round(salario_mensual_ars, 0),
        "beneficios_mensual_ars": round(beneficios_mensual_ars, 0),
        "bruto_mensual_ars": round(bruto, 0)
    }

# =========================
# LLM JSON CLEANER
# =========================

def limpiar_json_llm(texto: str) -> str:
    """
    Elimina fences ```json ``` del output del modelo
    """
    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.replace("```json", "").replace("```", "").strip()
    return texto

# =========================
# MAIN
# =========================

if st.button("Calcular Shadow Payroll"):

    base = calcular_base_shadow()

    prompt = f"""
Sos un especialista senior en Impuesto a las Ganancias Argentina, payroll y expatriados (año 2025).

Datos del caso:
- Bruto mensual ARS: {base['bruto_mensual_ars']}
- Salario mensual ARS: {base['salario_mensual_ars']}
- Beneficios mensuales ARS: {base['beneficios_mensual_ars']}
- Cónyuge a cargo: {"Sí" if conyuge else "No"}
- Hijos a cargo: {hijos}
- Duración asignación (meses): {duracion_meses}
- FX utilizado: {tipo_cambio} ARS/USD
- Fecha FX: {fx_date}

Instrucciones:
1. Calculá shadow payroll mensual estimado 2025.
2. Incluí:
   - Impuesto a las Ganancias (4ta categoría)
   - Aportes employee (~17%)
   - Aportes employer (~24%)
3. Evaluá riesgo de Establecimiento Permanente (PE) si duración >183 días.
4. Indicá alertas fiscales y de compliance si corresponden.

Respondé SOLO JSON válido, sin Markdown, con esta estructura:
{{
  "ganancias_mensual": number,
  "aportes_employee": number,
  "neto_employee": number,
  "aportes_employer": number,
  "total_cost_employer": number,
  "pe_risk": "Bajo | Medio | Alto",
  "comentarios": string
}}
"""

    with st.spinner("Interpretando normativa fiscal con IA..."):
        response = llm.invoke(prompt).content

    try:
        clean_response = limpiar_json_llm(response)
        llm_result = json.loads(clean_response)
    except Exception as e:
        st.error("Error interpretando respuesta del modelo.")
        st.write("Respuesta cruda:")
        st.code(response)
        st.write("Respuesta limpia:")
        st.code(clean_response)
        st.exception(e)
        st.stop()

    resultados = {
        "Bruto mensual ARS": base["bruto_mensual_ars"],
        "Ganancias mensual estimado": llm_result["ganancias_mensual"],
        "Aportes employee": llm_result["aportes_employee"],
        "Neto employee": llm_result["neto_employee"],
        "Aportes employer": llm_result["aportes_employer"],
        "Costo total employer": llm_result["total_cost_employer"],
        "Riesgo PE": llm_result["pe_risk"],
        "Comentarios": llm_result["comentarios"],
        "Tipo de cambio": tipo_cambio,
        "Fecha FX": fx_date,
        "Fuente FX": fx_source,
    }

    st.subheader("Resultado Shadow Payroll")
    for k, v in resultados.items():
        st.write(f"**{k}:** {v}")

    # ===============================
    # EXPORTAR A EXCEL (PRO)
    # ===============================
    df = pd.DataFrame(list(resultados.items()), columns=["Campo", "Resultado"])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Shadow Payroll')

        workbook  = writer.book
        worksheet = writer.sheets['Shadow Payroll']

        # Columnas anchas
        worksheet.column_dimensions['A'].width = 40
        worksheet.column_dimensions['B'].width = 80

        # Con wrap + alineación vertical
        align = Alignment(wrap_text=True, vertical='top', horizontal='left')
        for row in worksheet.iter_rows(min_row=1, max_row=worksheet.max_row):
            for cell in row:
                cell.alignment = align
        # Formato ARS para B2 a B7
        ars_format = '[$ARS] #,##0.00'
        for row in range(2, 8):
            worksheet[f"B{row}"].number_format = ars_format

    output.seek(0)

    st.download_button(
        label="📊 Descargar Excel",
        data=output,
        file_name="shadow_payroll_argentina_2025.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

