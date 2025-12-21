# Shadow Payroll Calculator – Argentina 2025

[![License: MIT](https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Prototype-yellow?logo=experiment)
[![Region](https://img.shields.io/badge/Region-Argentina-blue?logo=googlemaps)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33%2B-ff4b4b?logo=streamlit)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-orange?logo=chainlink)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-black?logo=openai)](https://platform.openai.com/)


Herramienta informativa para estimar el impacto de **Shadow Payroll** y **riesgo de Establecimiento Permanente (PE)** en asignaciones internacionales hacia Argentina.

> ⚠️ Uso informativo. No constituye asesoramiento fiscal ni legal.

---

## 🚀 Funcionalidades

- Cálculo de shadow payroll mensual en ARS
- Estimación de:
  - Impuesto a las Ganancias
  - Aportes employee / employer
  - Costo total employer
- Evaluación de riesgo PE (Bajo / Medio / Alto)
- FX automático USD → ARS con:
  - Fecha
  - Fuente
- Exportación a Excel con formato profesional

---

## 🧠 Tecnología

- Python 3.10+
- Streamlit
- LangChain
- OpenAI API
- OpenPyXL
- API FX gratuita (open.er-api.com))

---

## 🔐 API Key OpenAI

La API Key **no se guarda** en el código.

Debe ingresarse al ejecutar la app desde la barra lateral.

---

## ▶️ Cómo ejecutar

```bash
git clone https://github.com/luquiluke/ShadowPayrollAgent.git
cd ShadowPayrollAgent

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
