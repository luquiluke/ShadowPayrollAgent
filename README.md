# Shadow Payroll Calculator – Argentina 2025

[![License: MIT](https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative)](https://opensource.org/licenses/MIT)
![Status](https://img.shields.io/badge/Status-v2.0-green?logo=experiment)
![Region](https://img.shields.io/badge/Region-Argentina-blue?logo=googlemaps)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33%2B-ff4b4b?logo=streamlit)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-orange?logo=chainlink)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-gpt_4o-black?logo=openai)](https://platform.openai.com/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen?logo=pytest)](https://docs.pytest.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Herramienta informativa para estimar el impacto de **Shadow Payroll** y **riesgo de Establecimiento Permanente (PE)** en asignaciones internacionales hacia Argentina.

> ⚠️ Uso informativo. No constituye asesoramiento fiscal ni legal.

---

## 🚀 Funcionalidades

### Cálculos Principales
- ✅ Cálculo de shadow payroll mensual en ARS
- ✅ Estimación de Impuesto a las Ganancias (4ta categoría)
- ✅ Cálculo de aportes employee (~17%) y employer (~24%)
- ✅ Costo total mensual para el empleador
- ✅ Evaluación automática de riesgo PE (Bajo / Medio / Alto)

### Características Técnicas
- 🌐 FX automático USD → ARS con fecha y fuente
- 📊 Exportación a Excel con formato profesional
- ✨ Validación de datos con Pydantic
- 🧪 Suite completa de tests con pytest
- 🎨 Code quality con Black, Ruff, y MyPy
- 📝 Logging integrado para debugging
- ⚡ Caching para optimizar API calls

---

## 🏗️ Arquitectura (v2.0)

El proyecto ha sido completamente refactorizado con arquitectura modular:

```
ShadowPayrollAgent-refactored/
├── src/
│   └── shadow_payroll/
│       ├── __init__.py
│       ├── config.py          # Configuración centralizada
│       ├── models.py           # Validación con Pydantic
│       ├── calculations.py     # Lógica de cálculo
│       ├── llm_handler.py      # Integración con LLM
│       ├── utils.py            # Utilidades (FX, helpers)
│       ├── excel_exporter.py   # Generación de Excel
│       └── ui.py               # Componentes Streamlit
├── tests/
│   ├── test_calculations.py
│   ├── test_models.py
│   ├── test_utils.py
│   └── conftest.py
├── app.py                      # Punto de entrada
├── requirements.txt            # Dependencias
├── pyproject.toml             # Configuración del proyecto
├── .pre-commit-config.yaml    # Pre-commit hooks
└── pytest.ini                 # Configuración de tests
```

### Mejoras v2.0

#### ✅ Modularización
- Separación de concerns (UI, lógica, modelos, configuración)
- Código más mantenible y testeable
- Imports claros y organizados

#### ✅ Validación de Datos
- Pydantic models para inputs y outputs
- Validación automática de rangos y tipos
- Mensajes de error claros

#### ✅ Manejo de Errores
- Excepciones específicas por tipo
- Logging detallado
- Mensajes informativos al usuario

#### ✅ Testing
- >80% cobertura de código
- Tests unitarios para cálculos críticos
- Fixtures reutilizables
- Configuración CI/CD ready

#### ✅ Code Quality
- Black para formateo consistente
- Ruff para linting
- MyPy para type checking
- Pre-commit hooks automáticos

#### ✅ Configuración
- Centralizada en `config.py`
- Variables de entorno con `.env`
- Valores por defecto sensatos

---

## 🧠 Tecnología

| Categoría | Tecnologías |
|-----------|-------------|
| **Core** | Python 3.10+, Streamlit |
| **LLM** | LangChain, OpenAI API (GPT-4o) |
| **Validación** | Pydantic 2.0+ |
| **Excel** | OpenPyXL, Pandas |
| **Testing** | pytest, pytest-cov, pytest-mock |
| **Quality** | Black, Ruff, MyPy, Pre-commit |
| **APIs** | open.er-api.com (FX rates) |

---

## 🔐 Seguridad

- ✅ API Key **nunca se guarda** en código
- ✅ Input via Streamlit sidebar (session only)
- ✅ `.env` en `.gitignore`
- ✅ Validación exhaustiva de inputs
- ✅ No se registran datos sensibles en logs

---

## ▶️ Inicio Rápido

### Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes)
- OpenAI API Key ([obtener aquí](https://platform.openai.com/))

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/luquiluke/ShadowPayrollAgent.git
cd ShadowPayrollAgent

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno virtual
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables de entorno (opcional)
cp .env.example .env
# Editar .env con tu API key (o usar sidebar en la app)

# 6. Ejecutar aplicación
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src/shadow_payroll --cov-report=html

# Solo tests unitarios
pytest -m unit

# Ver reporte HTML
# Abrir htmlcov/index.html en el navegador
```

---

## 🛠️ Desarrollo

### Setup para Contribuidores

```bash
# Instalar pre-commit hooks
pre-commit install

# Ejecutar pre-commit manualmente
pre-commit run --all-files

# Formatear código
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/shadow_payroll
```

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías detalladas.

---

## 📖 Uso

### Interfaz Web

1. Ejecutar `streamlit run app.py`
2. Ingresar API Key de OpenAI en la barra lateral
3. Completar formulario con datos de asignación:
   - Salario anual (USD)
   - Duración (meses)
   - Información familiar
   - Beneficios (vivienda, educación)
4. Click en "Calcular Shadow Payroll"
5. Ver resultados y descargar Excel

### API Programática

```python
from shadow_payroll import PayrollCalculator, PayrollInput, TaxLLMHandler

# Crear input
input_data = PayrollInput(
    salary_usd=100000,
    duration_months=12,
    housing_usd=20000,
    school_usd=15000,
    fx_rate=1000.0
)

# Calcular base
calculator = PayrollCalculator()
base = calculator.calculate_base(input_data)

# Calcular impuestos con LLM
llm_handler = TaxLLMHandler(api_key="sk-...")
tax = llm_handler.calculate_tax(input_data, base)

print(f"Costo mensual: ARS {tax.total_cost_employer:,.2f}")
```

---

## 📋 Configuración

### Variables de Entorno

Crear archivo `.env` basado en `.env.example`:

```bash
OPENAI_API_KEY=sk-your-api-key-here
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.0
FX_API_URL=https://open.er-api.com/v6/latest/USD
LOG_LEVEL=INFO
```

### Configuración Avanzada

Editar `src/shadow_payroll/config.py` para ajustar:
- Tasas de contribuciones (employee/employer)
- Límites de validación
- Timeouts de API
- TTL de caché

---

## 🤝 Contribuir

Las contribuciones son bienvenidas! Ver [CONTRIBUTING.md](CONTRIBUTING.md) para:

- Setup de desarrollo
- Guías de código
- Proceso de PR
- Testing guidelines

---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

---

## 🙏 Acknowledgments

- OpenAI por GPT-4o API
- Streamlit por el framework
- LangChain por la integración LLM
- open.er-api.com por FX rates gratuitas

---

## 📞 Soporte

- 🐛 **Issues**: [GitHub Issues](https://github.com/luquiluke/ShadowPayrollAgent/issues)
- 📧 **Email**: [Crear issue para contacto]
- 📖 **Docs**: Este README y CONTRIBUTING.md

---

## 🗺️ Roadmap

- [ ] Soporte multi-país (Brasil, Chile, México)
- [ ] Dashboard con métricas históricas
- [ ] Exportación a PDF
- [ ] API REST
- [ ] CLI tool
- [ ] Integración con HRIS systems

---

## ⭐ Si te resulta útil

Dale una ⭐ al repo para ayudar a otros a encontrarlo!

---

**Versión**: 2.0.0
**Última actualización**: Enero 2025
**Mantenedor**: [@luquiluke](https://github.com/luquiluke)
