"""
Scenario state management for multi-country comparison.

Manages up to MAX_SCENARIOS scenarios in Streamlit session state.
Each scenario is a plain dict (not Pydantic) for Streamlit cache compatibility.
"""

from typing import TypedDict

import streamlit as st

MAX_SCENARIOS: int = 3

# Canonical line item labels for cross-country normalization
CANONICAL_LABELS: list[str] = [
    "Income Tax",
    "Social Security - Employee",
    "Social Security - Employer",
    "PE Administration",
    "Housing Allowance",
    "Education Allowance",
    "Other",
]

# Mapping of common LLM-returned label variants to canonical labels
_LABEL_MAP: dict[str, str] = {
    # Income Tax variants
    "income tax": "Income Tax",
    "ganancias": "Income Tax",
    "irpf": "Income Tax",
    "einkommensteuer": "Income Tax",
    "impuesto a las ganancias": "Income Tax",
    "personal income tax": "Income Tax",
    # Social Security - Employee variants
    "social security - employee": "Social Security - Employee",
    "social security employee": "Social Security - Employee",
    "employee social security": "Social Security - Employee",
    "aportes employee": "Social Security - Employee",
    "employee contributions": "Social Security - Employee",
    # Social Security - Employer variants
    "social security - employer": "Social Security - Employer",
    "social security employer": "Social Security - Employer",
    "employer social security": "Social Security - Employer",
    "contribuciones employer": "Social Security - Employer",
    "employer contributions": "Social Security - Employer",
    # PE Administration variants
    "pe administration": "PE Administration",
    "permanent establishment": "PE Administration",
    "pe admin": "PE Administration",
    "pe setup": "PE Administration",
    # Housing variants
    "housing allowance": "Housing Allowance",
    "housing": "Housing Allowance",
    "rent allowance": "Housing Allowance",
    # Education variants
    "education allowance": "Education Allowance",
    "education": "Education Allowance",
    "school allowance": "Education Allowance",
    "schooling": "Education Allowance",
    # Other
    "other": "Other",
    "miscellaneous": "Other",
    "other costs": "Other",
}


class ScenarioData(TypedDict):
    """Schema for a single scenario stored in session state."""

    name: str
    input_data: dict
    result: dict
    model_name: str
    timestamp: str


def add_scenario(
    name: str,
    input_data: dict,
    result: dict,
    model_name: str,
    timestamp: str,
) -> bool:
    """Append a scenario to session state.

    Returns True on success, False if MAX_SCENARIOS reached.
    """
    scenarios: list[dict] = st.session_state.setdefault("scenarios", [])
    if len(scenarios) >= MAX_SCENARIOS:
        st.warning(f"Maximum {MAX_SCENARIOS} scenarios reached. Remove one to add another.")
        return False
    scenarios.append(
        ScenarioData(
            name=name,
            input_data=input_data,
            result=result,
            model_name=model_name,
            timestamp=timestamp,
        )
    )
    return True


def remove_scenario(index: int) -> None:
    """Remove scenario at *index* from session state (bounds-checked)."""
    scenarios: list[dict] = st.session_state.get("scenarios", [])
    if 0 <= index < len(scenarios):
        scenarios.pop(index)


def get_scenarios() -> list[ScenarioData]:
    """Return the current list of saved scenarios."""
    return st.session_state.get("scenarios", [])


def clear_scenarios() -> None:
    """Remove all scenarios from session state."""
    st.session_state["scenarios"] = []


def auto_name(input_data: dict) -> str:
    """Generate a descriptive label from input data.

    Returns a string like ``"Germany (36mo)"``.
    """
    country = input_data.get("host_country", "Unknown")
    months = input_data.get("duration_months", "?")
    return f"{country} ({months}mo)"


def normalize_line_items(
    scenarios: list[ScenarioData],
) -> tuple[list[str], list[list[float]]]:
    """Normalize line-item labels across scenarios for comparison tables.

    Returns
    -------
    canonical_labels : list[str]
        Ordered list of canonical label strings (only those present in at
        least one scenario).
    values_matrix : list[list[float]]
        ``values_matrix[scenario_idx][label_idx]`` is the USD amount for
        that scenario/label pair (0.0 when the label is absent).
    """
    # Collect which canonical labels appear across all scenarios
    present: set[str] = set()
    scenario_maps: list[dict[str, float]] = []

    for scenario in scenarios:
        mapping: dict[str, float] = {}
        result = scenario.get("result", {})
        line_items: dict = result.get("line_items", {})
        for raw_label, amount in line_items.items():
            canonical = _LABEL_MAP.get(raw_label.lower().strip(), "Other")
            # Accumulate into canonical bucket (in case multiple raw labels map
            # to the same canonical)
            mapping[canonical] = mapping.get(canonical, 0.0) + float(amount)
            present.add(canonical)
        scenario_maps.append(mapping)

    # Preserve canonical ordering, filtered to only labels that appear
    canonical_labels = [lbl for lbl in CANONICAL_LABELS if lbl in present]

    # Build matrix
    values_matrix: list[list[float]] = []
    for mapping in scenario_maps:
        row = [mapping.get(lbl, 0.0) for lbl in canonical_labels]
        values_matrix.append(row)

    return canonical_labels, values_matrix
