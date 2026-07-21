#!/usr/bin/env python3
"""Shared helpers for the July 13 lit-review closure-rigor packages."""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-13"
DATE_DIR = ROOT / "work_products" / "2026-07" / DATE
LITREV_ROOT = (
    ROOT.parent
    / "papers"
    / "LitRev-start---Closure-and-Modeling-Decisions-for-Developing-HITEC-Flow-TAMU-MSFL"
)
LITREV_SYNTHESIS = (
    ROOT
    / "reports"
    / "2026-07"
    / DATE
    / "2026-07-13_litrev_lessons_and_research_pathways"
)

PRESSURE_LEDGER = (
    ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-08"
    / "2026-07-08_pressure_term_ledger"
    / "pressure_term_ledger.csv"
)
MINOR_LOSS_TWO_TAP = (
    ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-08"
    / "2026-07-08_minor_loss_two_tap"
    / "minor_loss_two_tap.csv"
)
CLOSURE_OBSERVATIONS = (
    ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-09"
    / "2026-07-09_closure_observation_table_thermal_refresh"
    / "closure_observations.csv"
)
THERMAL_BOUNDARY = (
    ROOT
    / "work_products"
    / "2026-07"
    / DATE
    / "2026-07-13_thermal_boundary_patch_role_table"
    / "thermal_boundary_patch_role_table.csv"
)
THERMAL_SEGMENTS = (
    ROOT
    / "work_products"
    / "2026-07"
    / DATE
    / "2026-07-13_thermal_boundary_patch_role_table"
    / "segment_reduction_inputs.csv"
)
PREDICTIVE_THERMAL = (
    ROOT
    / "work_products"
    / "2026-07"
    / DATE
    / "2026-07-13_predictive_heat_loss_path"
    / "control_volume_effective_thermal_table.csv"
)
NO_RADIATION_PARITY = (
    ROOT
    / "work_products"
    / "2026-07"
    / DATE
    / "2026-07-13_cfd_bc_no_radiation_1d_parity"
    / "section_heat_loss_comparison.csv"
)
TIME_UNCERTAINTY = (
    ROOT
    / "work_products"
    / "2026-07"
    / DATE
    / "2026-07-13_time_series_uncertainty_story"
    / "mainline_salt234_uncertainty_components.csv"
)
CORRELATION_TABLE = LITREV_ROOT / "data" / "correlation_table.csv"
RESEARCH_PATHWAYS = LITREV_SYNTHESIS / "research_pathways.csv"

G = 9.80665


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: render(row.get(field, "")) for field in fieldnames})


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_readme(path: Path, title: str, task_id: str, sections: Mapping[str, str]) -> None:
    lines = [
        f"# {title}",
        "",
        f"Date: `{DATE}`",
        "",
        f"Task: `{task_id}`",
        "",
        "## Source Context",
        "",
        f"- Lit-rev synthesis: `{rel(LITREV_SYNTHESIS)}`",
        f"- Research pathways: `{rel(RESEARCH_PATHWAYS)}`",
        "",
    ]
    for heading, body in sections.items():
        lines.extend([f"## {heading}", "", body.strip(), ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def render(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.8g}"
    return str(value)


def num(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return default
    try:
        result = float(text)
    except ValueError:
        return default
    return result if math.isfinite(result) else default


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_inputs(paths: Iterable[Path]) -> None:
    missing = [rel(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("missing required inputs: " + ", ".join(missing))


def rho_reis(T_K: float) -> float:
    return 2293.6 - 0.7497 * T_K


def beta_reis(T_K: float) -> float:
    return 0.7497 / rho_reis(T_K)


def mu_reis(T_K: float) -> float:
    return 0.4737 - 2.297e-3 * T_K + 3.731e-6 * T_K**2 - 2.019e-9 * T_K**3


def mu_jin(T_K: float) -> float:
    eta_mpa_s = 1.149 * math.exp(-810.896 / T_K + 7.806e5 / T_K**2)
    return 1e-3 * eta_mpa_s


def cp_reis(T_K: float) -> float:
    return 5806.0 - 10.833 * T_K + 7.2413e-3 * T_K**2


def cp_parida(_: float) -> float:
    return 1423.5


def cp_hoffman(_: float) -> float:
    return 1560.0


def cp_vdi(T_K: float) -> float:
    return 1303.9 + 0.60666 * (T_K - 273.15)


def k_santini(T_K: float) -> float:
    return 0.78 - 1.25e-3 * T_K + 1.6e-6 * T_K**2


def k_constant_050(_: float) -> float:
    return 0.50


def k_constant_060(_: float) -> float:
    return 0.60


def k_shen(T_K: float) -> float:
    return 0.697 - 0.000461 * (T_K - 273.15)


def property_mode(mode: str, T_K: float) -> dict[str, Any]:
    if mode == "replication_reis_jadyn":
        return {
            "rho_kg_m3": rho_reis(T_K),
            "mu_pa_s": mu_reis(T_K),
            "cp_jkgk": cp_reis(T_K),
            "k_w_mk": k_santini(T_K),
            "provenance_author_title": "Reis, Seo, and Hassan, Molten Salt Flow Visualization to Characterize Boundary Layer Behavior and Heat Transfer in a Natural Circulation Loop; Santini et al., Measurement of Thermal Conductivity of Molten Salts in the Range 100-500 C",
            "source_status": "replication_plus_measured_k_candidate",
        }
    if mode == "sohal_janz_full":
        return {
            "rho_kg_m3": rho_reis(T_K),
            "mu_pa_s": mu_reis(T_K),
            "cp_jkgk": cp_reis(T_K),
            "k_w_mk": k_constant_050(T_K),
            "provenance_author_title": "Sohal et al., Engineering Database of Liquid Salt Thermophysical and Thermochemical Properties; Janz et al., Molten Salts data compilations",
            "source_status": "source_supported_sensitivity_k_screening",
        }
    if mode == "jin_viscosity_parida_cp_santini_k":
        return {
            "rho_kg_m3": rho_reis(T_K),
            "mu_pa_s": mu_jin(T_K),
            "cp_jkgk": cp_parida(T_K),
            "k_w_mk": k_santini(T_K),
            "provenance_author_title": "Jin et al., Accurate Viscosity Measurement of Nitrates/Nitrites Salts for Concentrated Solar Power; Parida and Basu, On the Specific Heat Capacity of HITEC-Salt Nanocomposites for Concentrated Solar Power Applications; Santini et al., Measurement of Thermal Conductivity of Molten Salts in the Range 100-500 C",
            "source_status": "updated_candidate_sensitivity",
        }
    if mode == "jin_viscosity_cp_1560_k_060":
        return {
            "rho_kg_m3": rho_reis(T_K),
            "mu_pa_s": mu_jin(T_K),
            "cp_jkgk": cp_hoffman(T_K),
            "k_w_mk": k_constant_060(T_K),
            "provenance_author_title": "Jin et al., Accurate Viscosity Measurement of Nitrates/Nitrites Salts for Concentrated Solar Power; Hoffman and Cohen, Fused Salt Heat Transfer Part III: Forced-Convection Heat Transfer in Circular Tubes Containing NaNO2-KNO3-NaNO3",
            "source_status": "historical_constant_cp_k_sensitivity",
        }
    if mode == "shen_celsius_comparison":
        return {
            "rho_kg_m3": rho_reis(T_K),
            "mu_pa_s": mu_jin(T_K),
            "cp_jkgk": 1549.0 - 0.15 * (T_K - 273.15),
            "k_w_mk": k_shen(T_K),
            "provenance_author_title": "Shen et al., Convective Heat Transfer of Molten Salt in Receiver Tube with Axially and Circumferentially Non-Uniform Heat Flux; Jin et al., Accurate Viscosity Measurement of Nitrates/Nitrites Salts for Concentrated Solar Power",
            "source_status": "clean_celsius_basis_comparison",
        }
    raise KeyError(f"unknown property mode {mode}")


PROPERTY_MODES = [
    "replication_reis_jadyn",
    "sohal_janz_full",
    "jin_viscosity_parida_cp_santini_k",
    "jin_viscosity_cp_1560_k_060",
    "shen_celsius_comparison",
]


def prandtl(mu: float, cp: float, k: float) -> float:
    return cp * mu / k


def reynolds(rho: float, u: float, D: float, mu: float) -> float:
    return rho * abs(u) * D / mu


def grashof(rho: float, mu: float, beta: float, dT: float, D: float) -> float:
    nu = mu / rho
    return G * beta * abs(dT) * D**3 / (nu * nu)


def safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b in (None, 0):
        return None
    return a / b


def classify_orientation(span: str) -> str:
    text = span.lower()
    if "lower" in text or "upper" in text or "test_section" in text:
        return "mostly_horizontal"
    if "right" in text:
        return "mostly_vertical_downcomer"
    if "left" in text:
        return "mostly_vertical_upcomer"
    if "cool" in text:
        return "cooling_branch"
    return "unknown"


def heating_sign_for_span(span: str, thermal_row: Mapping[str, str] | None) -> str:
    if thermal_row:
        q = num(thermal_row.get("realized_wallHeatFlux_W_positive_to_fluid"))
        if q is not None:
            if q > 1e-9:
                return "heating"
            if q < -1e-9:
                return "cooling"
    text = span.lower()
    if "lower" in text or "test" in text:
        return "heating_expected"
    if "upper" in text or "cool" in text:
        return "cooling_expected"
    return "passive_or_unknown"


def case_sort_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (str(row.get("case_id", "")), str(row.get("span", row.get("one_d_segment", ""))), str(row.get("source_id", "")))


def summary_payload(task_id: str, output_dir: Path, primary_rows: int, outputs: Sequence[str], notes: Sequence[str]) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "date": DATE,
        "created_utc": now_utc(),
        "output_dir": rel(output_dir),
        "primary_rows": primary_rows,
        "outputs": list(outputs),
        "notes": list(notes),
        "source_context": {
            "litrev_synthesis": rel(LITREV_SYNTHESIS),
            "research_pathways": rel(RESEARCH_PATHWAYS),
        },
    }

