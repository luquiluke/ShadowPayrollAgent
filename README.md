# Shadow Payroll Calculator

[![License: MIT](https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative)](https://opensource.org/licenses/MIT)
![Status](https://img.shields.io/badge/Status-v3.0-green?logo=experiment)
![Region](https://img.shields.io/badge/Region-Multi--Pa%C3%ADs-blue?logo=googlemaps)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33%2B-ff4b4b?logo=streamlit)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-orange?logo=chainlink)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-gpt_4o-black?logo=openai)](https://platform.openai.com/)
[![Tests](https://img.shields.io/badge/tests-107%20passing-brightgreen?logo=pytest)](https://docs.pytest.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Herramienta profesional para estimar costos de **Shadow Payroll**, comparar escenarios entre paises y evaluar **riesgo de Establecimiento Permanente (PE)** en asignaciones internacionales.

> **Slater Consulting** -- Herramienta de uso informativo. No constituye asesoramiento fiscal ni legal.

---

## Funcionalidades

### Estimacion Multi-Pais
- Estimacion de costos de shadow payroll para **30 paises** (Argentina, Alemania, Singapur, EAU, etc.)
- Desglose de costos con montos en **USD y moneda local** simultaneamente
- Tipo de cambio automatico para cualquier par de divisas via API
- Calificacion de costos con contexto regional (Low / Medium / High)
- Evaluacion de riesgo PE con timeline visual, tratados fiscales y sugerencias de mitigacion
- Insights generados por IA con analisis narrativo de 2-3 oraciones

### Comparacion de Escenarios
- Guardar hasta **3 escenarios** para comparacion lado a lado
- Tabla de comparacion con **codigo de colores** (verde = mas barato, rojo = mas caro por fila)
- Resumen automatico identificando la opcion mas economica
- Normalizacion de etiquetas entre paises para comparacion justa

### Exportacion Profesional
- **PDF** con logo de Slater Consulting, graficos de barras, tablas estilizadas y disclaimer legal
- **Excel** multi-hoja con hoja de comparacion + detalle por escenario
- Codigo de colores verde/rojo en ambos formatos
- Botones de descarga disponibles inmediatamente despues de estimar (sin necesidad de guardar escenario)

### Caracteristicas Tecnicas
- FX automatico para todas las divisas con cache de 1 hora
- Validacion de datos con Pydantic v2
- 107 tests unitarios pasando
- Tema oscuro fintech con CSS custom properties
- Logging integrado para debugging
- Pre-commit hooks con Black, Ruff y MyPy

---

## Arquitectura (v3.0)

```
ShadowPayrollAgent-refactored/
├── app.py                          # Punto de entrada (streamlit run app.py)
├── src/shadow_payroll/
│   ├── config.py                   # Configuracion centralizada, paises, divisas
│   ├── models.py                   # Modelos Pydantic (PayrollInput, EstimationResponse)
│   ├── calculations.py             # Logica de calculo determinista
│   ├── llm_handler.py              # Integracion con LLM (prompts + parsing)
│   ├── estimator.py                # CountryEstimator - estimacion multi-pais
│   ├── scenarios.py                # CRUD de escenarios, normalizacion de etiquetas
│   ├── utils.py                    # FX rates, helpers
│   ├── ui.py                       # Componentes Streamlit (formulario, resultados, comparacion)
│   ├── excel_exporter.py           # Exportacion Excel multi-hoja con estilos
│   ├── pdf_exporter.py             # Exportacion PDF con ReportLab (graficos, tablas, branding)
│   ├── corporate_theme.css         # Tema oscuro fintech con CSS custom properties
│   └── logo.png                    # Logo de Slater Consulting
├── tests/
│   ├── conftest.py                 # Fixtures compartidos
│   ├── test_calculations.py        # Tests de calculo
│   ├── test_models.py              # Tests de validacion
│   ├── test_ui.py                  # Tests de UI (AppTest)
│   └── test_utils.py               # Tests de utilidades
├── requirements.txt
├── pyproject.toml
└── .pre-commit-config.yaml
```

---

## Tecnologia

| Categoria | Tecnologias |
|-----------|-------------|
| **Core** | Python 3.10+, Streamlit |
| **LLM** | LangChain, OpenAI API (GPT-4o) |
| **Validacion** | Pydantic v2 |
| **PDF** | ReportLab (Platypus, graficos, tablas) |
| **Excel** | openpyxl, Pandas |
| **Testing** | pytest (107 tests), pytest-cov, pytest-mock |
| **Quality** | Black, Ruff, MyPy, Pre-commit |
| **FX** | open.er-api.com (rates gratuitas, 23 divisas) |

---

## Inicio Rapido

### Requisitos

- Python 3.10 o superior
- pip
- OpenAI API Key ([obtener aqui](https://platform.openai.com/))

### Instalacion

```bash
# 1. Clonar el repositorio
git clone https://github.com/luquiluke/ShadowPayrollAgent.git
cd ShadowPayrollAgent

# 2. Crear y activar entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar aplicacion
streamlit run app.py
```

La aplicacion se abrira en `http://localhost:8501`

---

## Uso

### Flujo Principal

1. Ejecutar `streamlit run app.py`
2. Ingresar API Key de OpenAI en la barra lateral
3. Seleccionar pais de origen y pais destino
4. Completar datos de asignacion (salario, duracion, beneficios)
5. Click en **"Calculate Shadow Payroll"**
6. Ver resultados: desglose de costos, calificacion, riesgo PE, insights
7. Descargar PDF o Excel directamente

### Comparacion de Escenarios

1. Estimar un primer pais y click en **"Save Comparison Scenario"**
2. Cambiar pais destino y estimar de nuevo
3. Guardar segundo escenario
4. Ver tabla de comparacion con codigo de colores
5. Descargar PDF/Excel con ambos escenarios

---

## Paises Soportados

Argentina, Australia, Brasil, Canada, Chile, China, Colombia, Francia, Alemania, India, Irlanda, Italia, Japon, Mexico, Paises Bajos, Nueva Zelanda, Peru, Filipinas, Polonia, Portugal, Singapur, Corea del Sur, Espana, Suecia, Suiza, Emiratos Arabes Unidos, Reino Unido, Estados Unidos, Uruguay.

---

## Seguridad

- API Key **nunca se guarda** en codigo ni en disco
- Input via Streamlit sidebar (solo sesion)
- `.env` en `.gitignore`
- Validacion exhaustiva de inputs con Pydantic
- No se registran datos sensibles en logs

---

## Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src/shadow_payroll --cov-report=html

# Test especifico
pytest tests/test_calculations.py -v
```

---

## Desarrollo

```bash
# Instalar pre-commit hooks
pre-commit install

# Ejecutar checks manualmente
pre-commit run --all-files

# Formatear codigo
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/shadow_payroll
```

---

## Configuracion

### Variables de Entorno

```bash
OPENAI_API_KEY=sk-your-api-key-here
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.0
LOG_LEVEL=INFO
```

### Configuracion Avanzada

Editar `src/shadow_payroll/config.py` para ajustar:
- Tasas de contribuciones (employee/employer)
- Limites de validacion
- Branding de PDF (nombre de empresa, logo, disclaimer)
- Timeouts de API y TTL de cache

---

## Historial de Versiones

### v3.0 (Febrero 2025)
- **Estimacion multi-pais** con 30 paises y 23 divisas
- **Comparacion de escenarios** con tabla de colores y resumen
- **Exportacion PDF** profesional con ReportLab (graficos, branding, disclaimer)
- **Exportacion Excel** multi-hoja con estilos y codigo de colores
- **Tipo de cambio dinamico** por pais (no solo ARS/USD)
- **Logo de Slater Consulting** en PDF y Excel
- **Tema oscuro fintech** con CSS custom properties
- **Riesgo PE** con timeline visual, tratados y mitigacion
- **107 tests** pasando

### v2.0 (Enero 2025)
- Refactorizacion completa con arquitectura modular
- Validacion con Pydantic v2
- Suite de tests con pytest
- Code quality con Black, Ruff, MyPy
- Exportacion Excel basica

### v1.0
- Calculadora Argentina con LLM
- Interfaz Streamlit basica
- Exportacion Excel simple

---

## Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

---

## Soporte

- **Issues**: [GitHub Issues](https://github.com/luquiluke/ShadowPayrollAgent/issues)
- **Docs**: Este README

---

**Version**: 3.0.0
**Ultima actualizacion**: Febrero 2025
**Mantenedor**: [@luquiluke](https://github.com/luquiluke)
