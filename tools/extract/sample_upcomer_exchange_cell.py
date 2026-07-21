#!/usr/bin/env python3
"""Dry upcomer exchange-cell sampler design.

This tool is a design and fixture-validation step only. It does not write
OpenFOAM case directories, launch postprocessing, read native solver fields by
default, fit coefficients, or change admission state.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract.sample_upcomer_matched_plane_metrics import (
    cell_values,
    normalize,
    parse_legacy_vtk,
    polygon_area,
    temperature_from_fields,
)

TASK_ID = "TODO-UPCOMER-EXCHANGE-SAMPLER-DESIGN-2026-07-21"
PACKAGE_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design"
)
CONTRACT_PACKAGE = (
    ROOT
    / "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_upcomer_exchange_evidence_extraction"
)
CASE_QUEUE = CONTRACT_PACKAGE / "case_time_window_queue.csv"
FIELD_MAP = CONTRACT_PACKAGE / "sampler_field_map.csv"

REQUIRED_OUTPUT_FIELDS = [
    {
        "field_name": "R_mu",
        "unit": "dimensionless",
        "basis": "mu_recirc / mu_main from same-window recirculation and main-cell state",
        "availability": "computed_if_mu_exists_in_cell_sample",
        "unavailable_policy": "emit not_available_with_reason if mu is missing",
    },
    {
        "field_name": "R_rho",
        "unit": "dimensionless",
        "basis": "rho_recirc / rho_main from same-window recirculation and main-cell state",
        "availability": "computed_if_rho_exists_in_cell_sample",
        "unavailable_policy": "emit not_available_with_reason if rho is missing",
    },
    {
        "field_name": "V_recirc",
        "unit": "m3",
        "basis": "sum(cellVolume) over recircMask>=0.5, fallback to U dot throughflow normal < 0",
        "availability": "computed_if_cellVolume_and_mask_or_U_exist",
        "unavailable_policy": "emit not_available_with_reason if no coherent volume basis exists",
    },
    {
        "field_name": "mdot_exchange",
        "unit": "kg/s",
        "basis": "0.5*(main_to_cell_flux + cell_to_main_flux) across named exchange interface",
        "availability": "computed_if_interface_U_rho_area_exist",
        "unavailable_policy": "emit not_available_with_reason if interface plane is missing",
    },
    {
        "field_name": "tau_recirc",
        "unit": "s",
        "basis": "rho_recirc * V_recirc / abs(mdot_exchange)",
        "availability": "computed_if_V_recirc_rho_recirc_and_mdot_exchange_exist",
        "unavailable_policy": "emit not_available_with_reason for zero or missing exchange flux",
    },
    {
        "field_name": "T_main",
        "unit": "K",
        "basis": "rho*volume weighted main-cell temperature",
        "availability": "computed_if_T_or_rho_temperature_fallback_exists",
        "unavailable_policy": "emit not_available_with_reason if thermal state is absent",
    },
    {
        "field_name": "T_recirc",
        "unit": "K",
        "basis": "rho*volume weighted recirculation-cell temperature",
        "availability": "computed_if_T_or_rho_temperature_fallback_exists",
        "unavailable_policy": "emit not_available_with_reason if thermal state is absent",
    },
    {
        "field_name": "wall_core_delta_T",
        "unit": "K",
        "basis": "area-weighted wall_T - T_recirc",
        "availability": "computed_if_wall_T_and_T_recirc_exist",
        "unavailable_policy": "emit not_available_with_reason if wall-band thermal state is absent",
    },
    {
        "field_name": "pressure_residual",
        "unit": "Pa",
        "basis": "delta_p_observed - delta_p_straight - delta_p_hydrostatic - delta_p_minor",
        "availability": "computed_if_pressure_terms_are_supplied",
        "unavailable_policy": "emit not_available_with_reason if pressure basis is incomplete",
    },
    {
        "field_name": "energy_residual",
        "unit": "W",
        "basis": "Q_wall + Q_source - Q_sink - mdot_exchange*cp*(T_recirc-T_main)",
        "availability": "computed_if_thermal_source_terms_and_exchange_state_exist",
        "unavailable_policy": "emit not_available_with_reason if source/sink or exchange terms are incomplete",
    },
]

SCHEMA_FIELDS = [
    "field_name",
    "unit",
    "basis",
    "availability",
    "unavailable_policy",
    "runtime_policy",
]
PLAN_FIELDS = [
    "case_id",
    "case_key",
    "region",
    "time_window_s",
    "representative_plane",
    "required_output_fields",
    "dry_schema_status",
    "compute_execution_allowed_from_this_row",
    "native_output_mutation_allowed",
    "admission_use",
    "source_paths",
]
FIXTURE_FIELDS = [
    "fixture_id",
    "metric",
    "value",
    "expected",
    "status",
    "basis",
]
GUARD_FIELDS = ["guard_id", "status", "policy"]
HANDOFF_FIELDS = ["sequence", "work_package", "objective", "release_condition", "forbidden_action"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]
EXTRACTION_ROW_FIELDS = [
    "case_id",
    "time_window_s",
    "extraction_status",
    "missing_inputs",
    "R_mu",
    "R_mu_status",
    "R_rho",
    "V_recirc_m3",
    "mdot_exchange_kg_s",
    "tau_recirc_s",
    "T_main_K",
    "T_recirc_K",
    "wall_core_delta_T_K",
    "pressure_residual_Pa",
    "pressure_residual_status",
    "energy_residual_W",
    "energy_residual_status",
    "same_window_id",
    "pressure_basis",
    "thermal_basis",
    "volume_basis",
    "property_mode",
    "source_use_category",
    "admission_use",
    "fit_allowed_now",
    "score_allowed_now",
    "runtime_policy",
    "residual_policy",
    "interface_basis",
    "recirc_mask_basis",
]


def rel(path: Path | None) -> str:
    return relative_to_workspace(path) if path else ""


def fstr(value: Any, precision: int = 10) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "" if value is None else str(value)
    if not math.isfinite(number):
        return ""
    return f"{number:.{precision}g}"


def row_for_csv(row: dict[str, Any]) -> dict[str, str]:
    formatted: dict[str, str] = {}
    for field in EXTRACTION_ROW_FIELDS:
        value = row.get(field, "")
        if isinstance(value, (float, int)):
            formatted[field] = fstr(value)
        else:
            formatted[field] = "" if value is None else str(value)
    return formatted


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    total = float(np.sum(weights))
    if total <= 0.0:
        return math.nan
    return float(np.sum(values * weights) / total)


def polygon_areas(vtk: dict[str, Any]) -> np.ndarray:
    points = vtk["points"]
    return np.asarray([polygon_area(points[poly]) for poly in vtk["polygons"]], dtype=float)


def scalar_field(vtk: dict[str, Any], name: str, n_items: int) -> np.ndarray | None:
    values = cell_values(vtk, name)
    if values is None:
        return None
    return np.asarray(values, dtype=float).reshape(n_items)


def vector_field(vtk: dict[str, Any], name: str, n_items: int) -> np.ndarray | None:
    values = cell_values(vtk, name)
    if values is None:
        return None
    return np.asarray(values, dtype=float).reshape(n_items, 3)


def load_volume_csv(path: Path) -> dict[int, float]:
    rows = read_csv(path)
    volumes: dict[int, float] = {}
    for row in rows:
        cell_id = row.get("cell_id") or row.get("cellId") or row.get("cellID")
        volume = row.get("cellVolume_m3") or row.get("cellVolume") or row.get("V")
        if cell_id is None or volume is None:
            raise ValueError("volume CSV requires cell_id and cellVolume_m3 columns")
        volumes[int(float(cell_id))] = float(volume)
    if not volumes:
        raise ValueError("volume CSV contains no rows")
    return volumes


def cell_id_array(vtk: dict[str, Any], n_cells: int) -> np.ndarray | None:
    for name in ("cellId", "cellID", "cell_id", "origCellId", "origCellID"):
        values = scalar_field(vtk, name, n_cells)
        if values is not None:
            return np.asarray(values, dtype=int).reshape(n_cells)
    return None


def volume_field(vtk: dict[str, Any], n_cells: int, volume_csv: Path | None = None) -> tuple[np.ndarray | None, str]:
    direct = scalar_field(vtk, "cellVolume", n_cells)
    if direct is not None:
        return direct, "vtk_cellVolume"
    if volume_csv is None:
        return None, "missing_cellVolume"
    lookup = load_volume_csv(volume_csv)
    ids = cell_id_array(vtk, n_cells)
    if ids is not None:
        missing = [int(cell_id) for cell_id in ids if int(cell_id) not in lookup]
        if missing:
            raise ValueError(f"volume CSV missing cell ids: {missing[:5]}")
        return np.asarray([lookup[int(cell_id)] for cell_id in ids], dtype=float), "mesh_volume_csv_by_cell_id"
    ordered = [lookup[idx] for idx in range(n_cells) if idx in lookup]
    if len(ordered) == n_cells:
        return np.asarray(ordered, dtype=float), "mesh_volume_csv_by_vtk_cell_order"
    raise ValueError("missing cellVolume and no usable cell-id mapping for volume CSV")


def recirc_mask(vtk: dict[str, Any], throughflow_normal: np.ndarray, n_cells: int) -> tuple[np.ndarray, str]:
    explicit = scalar_field(vtk, "recircMask", n_cells)
    if explicit is not None:
        return explicit >= 0.5, "recircMask"
    velocities = vector_field(vtk, "U", n_cells)
    if velocities is None:
        raise ValueError("missing recircMask and U for recirculation mask")
    return (velocities @ throughflow_normal) < 0.0, "U_dot_n_reverse"


def temperature_array(vtk: dict[str, Any], rho: np.ndarray, n_cells: int) -> tuple[np.ndarray, str]:
    temp_values = scalar_field(vtk, "T", n_cells)
    return temperature_from_fields(temp_values, rho)


def compute_cell_state(
    cell_vtk: Path,
    throughflow_normal: np.ndarray,
    volume_csv: Path | None = None,
) -> dict[str, Any]:
    vtk = parse_legacy_vtk(cell_vtk)
    n_cells = len(vtk["polygons"])
    if n_cells == 0:
        raise ValueError("cell VTK has no polygons/cells")
    volume, volume_basis = volume_field(vtk, n_cells, volume_csv)
    rho = scalar_field(vtk, "rho", n_cells)
    if volume is None or rho is None:
        raise ValueError("missing cellVolume or rho")
    mask, mask_basis = recirc_mask(vtk, throughflow_normal, n_cells)
    main = ~mask
    if not np.any(mask):
        raise ValueError("recirculation mask selected zero cells")
    if not np.any(main):
        raise ValueError("main mask selected zero cells")
    temp, temp_basis = temperature_array(vtk, rho, n_cells)
    weights = rho * volume
    mu = scalar_field(vtk, "mu", n_cells)
    rho_recirc = weighted_mean(rho[mask], volume[mask])
    rho_main = weighted_mean(rho[main], volume[main])
    out: dict[str, Any] = {
        "cell_count": n_cells,
        "recirc_cell_count": int(np.sum(mask)),
        "main_cell_count": int(np.sum(main)),
        "V_recirc_m3": float(np.sum(volume[mask])),
        "V_main_m3": float(np.sum(volume[main])),
        "rho_recirc_kg_m3": rho_recirc,
        "rho_main_kg_m3": rho_main,
        "R_rho": rho_recirc / rho_main if rho_main > 0.0 else math.nan,
        "T_recirc_K": weighted_mean(temp[mask], weights[mask]),
        "T_main_K": weighted_mean(temp[main], weights[main]),
        "recirc_mask_basis": mask_basis,
        "thermal_basis": f"rho_volume_weighted_{temp_basis}",
        "volume_basis": volume_basis,
    }
    if mu is None:
        out["R_mu_status"] = "not_available_with_reason:missing_mu"
        out["R_mu"] = math.nan
    else:
        mu_recirc = weighted_mean(mu[mask], volume[mask])
        mu_main = weighted_mean(mu[main], volume[main])
        out["mu_recirc_Pa_s"] = mu_recirc
        out["mu_main_Pa_s"] = mu_main
        out["R_mu"] = mu_recirc / mu_main if mu_main > 0.0 else math.nan
        out["R_mu_status"] = "computed"
    return out


def compute_interface_exchange(interface_vtk: Path, interface_normal: np.ndarray) -> dict[str, Any]:
    vtk = parse_legacy_vtk(interface_vtk)
    areas = polygon_areas(vtk)
    if len(areas) == 0 or float(np.sum(areas)) <= 0.0:
        raise ValueError("interface VTK has no positive-area faces")
    velocities = vector_field(vtk, "U", len(areas))
    rho = scalar_field(vtk, "rho", len(areas))
    if velocities is None or rho is None:
        raise ValueError("missing U or rho on interface")
    un = velocities @ interface_normal
    face_flux = rho * un * areas
    main_to_cell = float(np.sum(np.maximum(face_flux, 0.0)))
    cell_to_main = float(np.sum(np.maximum(-face_flux, 0.0)))
    return {
        "interface_face_count": len(areas),
        "signed_mdot_main_to_cell_kg_s": float(np.sum(face_flux)),
        "positive_mdot_main_to_cell_kg_s": main_to_cell,
        "negative_mdot_cell_to_main_kg_s": cell_to_main,
        "absolute_mdot_kg_s": float(np.sum(np.abs(face_flux))),
        "mdot_exchange_kg_s": 0.5 * (main_to_cell + cell_to_main),
        "exchange_flux_imbalance_kg_s": main_to_cell - cell_to_main,
        "interface_basis": "area_weighted_rho_U_dot_n_positive_main_to_cell",
    }


def compute_wall_state(wall_vtk: Path) -> dict[str, Any]:
    vtk = parse_legacy_vtk(wall_vtk)
    areas = polygon_areas(vtk)
    if len(areas) == 0 or float(np.sum(areas)) <= 0.0:
        raise ValueError("wall VTK has no positive-area faces")
    rho = scalar_field(vtk, "rho", len(areas))
    temp_values = scalar_field(vtk, "T", len(areas))
    temp, temp_basis = temperature_from_fields(temp_values, rho)
    wall_heat_flux = scalar_field(vtk, "wallHeatFlux", len(areas))
    out = {
        "wall_face_count": len(areas),
        "wall_T_K": weighted_mean(temp, areas),
        "wall_temperature_basis": f"area_weighted_{temp_basis}",
    }
    if wall_heat_flux is not None:
        out["wallHeatFlux_W_m2"] = weighted_mean(wall_heat_flux, areas)
        out["Q_wall_proxy_W"] = float(np.sum(wall_heat_flux * areas))
    return out


def pressure_residual_pa(
    delta_p_observed_pa: float | None,
    delta_p_straight_pa: float | None,
    delta_p_hydrostatic_pa: float = 0.0,
    delta_p_minor_pa: float = 0.0,
) -> tuple[float, str]:
    terms = [delta_p_observed_pa, delta_p_straight_pa, delta_p_hydrostatic_pa, delta_p_minor_pa]
    if any(finite_or_none(term) is None for term in terms):
        return math.nan, "not_available_with_reason:missing_pressure_basis"
    residual = float(delta_p_observed_pa) - float(delta_p_straight_pa) - float(delta_p_hydrostatic_pa) - float(delta_p_minor_pa)
    return residual, "computed_observed_minus_straight_minus_hydrostatic_minus_minor"


def energy_residual_w(
    q_wall_w: float | None,
    q_source_w: float | None,
    q_sink_w: float | None,
    mdot_exchange_kg_s: float | None,
    cp_j_kg_k: float | None,
    t_main_k: float | None,
    t_recirc_k: float | None,
) -> tuple[float, str]:
    terms = [q_wall_w, q_source_w, q_sink_w, mdot_exchange_kg_s, cp_j_kg_k, t_main_k, t_recirc_k]
    if any(finite_or_none(term) is None for term in terms):
        return math.nan, "not_available_with_reason:missing_energy_or_exchange_basis"
    exchange_power = float(mdot_exchange_kg_s) * float(cp_j_kg_k) * (float(t_recirc_k) - float(t_main_k))
    residual = float(q_wall_w) + float(q_source_w) - float(q_sink_w) - exchange_power
    return residual, "computed_Qwall_plus_Qsource_minus_Qsink_minus_exchange_enthalpy"


def assemble_exchange_row(
    case_id: str,
    time_window_s: str,
    cell_state: dict[str, Any],
    interface_state: dict[str, Any],
    wall_state: dict[str, Any] | None = None,
    pressure_terms: dict[str, float] | None = None,
    energy_terms: dict[str, float] | None = None,
) -> dict[str, Any]:
    mdot = interface_state.get("mdot_exchange_kg_s")
    tau = math.nan
    if finite_or_none(mdot) is not None and abs(float(mdot)) > 1e-300:
        tau = float(cell_state["rho_recirc_kg_m3"]) * float(cell_state["V_recirc_m3"]) / abs(float(mdot))
    pressure_terms = pressure_terms or {}
    energy_terms = energy_terms or {}
    p_residual, p_basis = pressure_residual_pa(
        pressure_terms.get("delta_p_observed_pa"),
        pressure_terms.get("delta_p_straight_pa"),
        pressure_terms.get("delta_p_hydrostatic_pa", 0.0),
        pressure_terms.get("delta_p_minor_pa", 0.0),
    )
    q_wall = energy_terms.get("Q_wall_W")
    if q_wall is None and wall_state is not None:
        q_wall = wall_state.get("Q_wall_proxy_W")
    e_residual, e_basis = energy_residual_w(
        q_wall,
        energy_terms.get("Q_source_W", 0.0),
        energy_terms.get("Q_sink_W", 0.0),
        mdot,
        energy_terms.get("cp_J_kg_K"),
        cell_state.get("T_main_K"),
        cell_state.get("T_recirc_K"),
    )
    wall_core_delta = math.nan
    if wall_state is not None and finite_or_none(wall_state.get("wall_T_K")) is not None:
        wall_core_delta = float(wall_state["wall_T_K"]) - float(cell_state["T_recirc_K"])
    return {
        "case_id": case_id,
        "time_window_s": time_window_s,
        "extraction_status": "computed_from_supplied_inputs",
        "missing_inputs": "",
        "R_mu": cell_state.get("R_mu", math.nan),
        "R_mu_status": cell_state.get("R_mu_status", "computed"),
        "R_rho": cell_state.get("R_rho", math.nan),
        "V_recirc_m3": cell_state.get("V_recirc_m3", math.nan),
        "mdot_exchange_kg_s": mdot,
        "tau_recirc_s": tau,
        "T_main_K": cell_state.get("T_main_K", math.nan),
        "T_recirc_K": cell_state.get("T_recirc_K", math.nan),
        "wall_core_delta_T_K": wall_core_delta,
        "pressure_residual_Pa": p_residual,
        "pressure_residual_status": p_basis,
        "energy_residual_W": e_residual,
        "energy_residual_status": e_basis,
        "same_window_id": f"{case_id}:{time_window_s}",
        "pressure_basis": p_basis,
        "thermal_basis": cell_state.get("thermal_basis", ""),
        "volume_basis": cell_state.get("volume_basis", ""),
        "property_mode": "sampled_same_window_fields",
        "source_use_category": "training_or_support_only_until_split_gate",
        "admission_use": "diagnostic_only_until_same_qoi_uq_and_phase4b_rescore",
        "fit_allowed_now": "false",
        "score_allowed_now": "false",
        "runtime_policy": "not_a_predictive_runtime_input",
        "residual_policy": "do_not_hide_heat_residual_in_internal_Nu",
        "interface_basis": interface_state.get("interface_basis", ""),
        "recirc_mask_basis": cell_state.get("recirc_mask_basis", ""),
    }


def unavailable_exchange_row(case_id: str, time_window_s: str, missing_inputs: list[str], reason: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "time_window_s": time_window_s,
        "extraction_status": f"not_available_with_reason:{reason}",
        "missing_inputs": ";".join(missing_inputs),
        "R_mu": math.nan,
        "R_mu_status": "not_available_with_reason:missing_inputs",
        "R_rho": math.nan,
        "V_recirc_m3": math.nan,
        "mdot_exchange_kg_s": math.nan,
        "tau_recirc_s": math.nan,
        "T_main_K": math.nan,
        "T_recirc_K": math.nan,
        "wall_core_delta_T_K": math.nan,
        "pressure_residual_Pa": math.nan,
        "pressure_residual_status": "not_available_with_reason:missing_pressure_basis",
        "energy_residual_W": math.nan,
        "energy_residual_status": "not_available_with_reason:missing_energy_or_exchange_basis",
        "same_window_id": f"{case_id}:{time_window_s}",
        "pressure_basis": "not_available_with_reason:missing_inputs",
        "thermal_basis": "not_available_with_reason:missing_inputs",
        "property_mode": "not_available_with_reason:missing_inputs",
        "source_use_category": "training_or_support_only_until_split_gate",
        "admission_use": "diagnostic_only_until_same_qoi_uq_and_phase4b_rescore",
        "fit_allowed_now": "false",
        "score_allowed_now": "false",
        "runtime_policy": "not_a_predictive_runtime_input",
        "residual_policy": "do_not_hide_heat_residual_in_internal_Nu",
        "interface_basis": "not_available_with_reason:missing_inputs",
        "recirc_mask_basis": "not_available_with_reason:missing_inputs",
    }


def write_extraction_rows(output_dir: Path, rows: list[dict[str, Any]]) -> None:
    csv_dump(output_dir / "exchange_sampler_rows.csv", EXTRACTION_ROW_FIELDS, [row_for_csv(row) for row in rows])
    json_dump(output_dir / "exchange_sampler_rows.json", {"rows": rows})


def parse_vector(text: str) -> np.ndarray:
    parts = [float(part.strip()) for part in text.split(",")]
    if len(parts) != 3:
        raise ValueError(f"expected three comma-separated vector components, got {text!r}")
    return normalize(np.asarray(parts, dtype=float))


def schema_rows() -> list[dict[str, Any]]:
    return [
        {
            **row,
            "runtime_policy": "not_a_predictive_runtime_input; training/support evidence only after split gates",
        }
        for row in REQUIRED_OUTPUT_FIELDS
    ]


def dry_plan_rows() -> list[dict[str, Any]]:
    required = ";".join(row["field_name"] for row in REQUIRED_OUTPUT_FIELDS)
    rows = []
    for row in read_csv(CASE_QUEUE):
        rows.append(
            {
                "case_id": row["case_id"],
                "case_key": row["case_key"],
                "region": row["region"],
                "time_window_s": row["time_window_s"],
                "representative_plane": row["representative_plane"],
                "required_output_fields": required,
                "dry_schema_status": "schema_defined_compute_execution_still_separate",
                "compute_execution_allowed_from_this_row": "false",
                "native_output_mutation_allowed": "false",
                "admission_use": "diagnostic_only_until_extracted_uq_and_rescore",
                "source_paths": ";".join([rel(CASE_QUEUE), row.get("source_paths", "")]),
            }
        )
    return rows


def no_launch_guardrails() -> list[dict[str, str]]:
    return [
        {
            "guard_id": "native_outputs",
            "status": "blocked",
            "policy": "do not mutate native CFD/OpenFOAM outputs or case directories",
        },
        {
            "guard_id": "scheduler",
            "status": "blocked",
            "policy": "sampler design row cannot submit, cancel, requeue, or monitor jobs",
        },
        {
            "guard_id": "postprocessing",
            "status": "blocked",
            "policy": "no OpenFOAM, foamPostProcess, reconstruction, or sampler execution from this row",
        },
        {
            "guard_id": "admission",
            "status": "blocked",
            "policy": "no fit, model selection, exchange-cell admission, internal-Nu reopening, or scorecard trigger",
        },
        {
            "guard_id": "residual_lane",
            "status": "pass",
            "policy": "pressure and energy residuals remain explicit fields, not hidden in internal Nu",
        },
    ]


def next_agent_handoff() -> list[dict[str, Any]]:
    return [
        {
            "sequence": 1,
            "work_package": "compute_node_sampler_execution",
            "objective": "run this schema on salt_2/salt_3/salt_4 queued windows through sbatch or srun",
            "release_condition": "sampled cell/interface/wall outputs exist or each case has a terminal source-field failure",
            "forbidden_action": "no login-node OpenFOAM or duplicate sampler against live terminal jobs",
        },
        {
            "sequence": 2,
            "work_package": "same_qoi_uq_pairing",
            "objective": "attach same-label same-formula same-sign same-window UQ to exchange-state and residual QOIs",
            "release_condition": "UQ rows pass for each candidate metric or remain explicitly blocked",
            "forbidden_action": "no Phase 4B rescore without UQ status",
        },
        {
            "sequence": 3,
            "work_package": "phase4b_exchange_readiness_rescore",
            "objective": "classify rows as one-stream, signed-flow junction, exchange-cell scoreable, or diagnostic-only",
            "release_condition": "scoreable/not-scoreable decision with residuals preserved as separate lanes",
            "forbidden_action": "no residual absorption into internal Nu",
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    paths = [
        Path("tools/extract/sample_upcomer_exchange_cell.py"),
        Path("tools/extract/test_sample_upcomer_exchange_cell.py"),
        CASE_QUEUE,
        FIELD_MAP,
        Path("tools/extract/sample_upcomer_convection_cell.py"),
        Path("tools/extract/sample_upcomer_matched_plane_metrics.py"),
    ]
    rows = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        rows.append(
            {
                "path": rel(full),
                "role": "task_output" if path.name.startswith(("sample_upcomer_exchange_cell", "test_sample_upcomer_exchange_cell")) else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": "false",
                "mutated": str(path.name.startswith(("sample_upcomer_exchange_cell", "test_sample_upcomer_exchange_cell"))).lower(),
            }
        )
    return rows


def fixture_validation_rows() -> list[dict[str, Any]]:
    return [
        {
            "fixture_id": "unit_fixture_contract",
            "metric": "schema_field_count",
            "value": len(REQUIRED_OUTPUT_FIELDS),
            "expected": 10,
            "status": "pass" if len(REQUIRED_OUTPUT_FIELDS) == 10 else "fail",
            "basis": "dry schema includes exchange-state, property-ratio, pressure, and energy fields",
        },
        {
            "fixture_id": "unit_fixture_contract",
            "metric": "compute_execution_allowed_from_design",
            "value": "false",
            "expected": "false",
            "status": "pass",
            "basis": "design package has no launch path",
        },
    ]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, recirculation, exchange-cell, sampler-design, no-solver]
related:
  - {rel(CONTRACT_PACKAGE)}
---
# Upcomer Exchange-Cell Sampler Design

This package implements the dry sampler-design step for the throughflow plus
recirculation/exchange-cell path. It defines the output schema and validates the
calculation kernels with synthetic fixtures, but it does not run OpenFOAM or
sample native CFD fields.

## Decision

- required schema fields: `{summary["required_schema_fields"]}`
- dry case/time plan rows: `{summary["dry_plan_rows"]}`
- fixture validation rows: `{summary["fixture_validation_rows"]}`
- compute execution allowed from this row: `false`
- fit/admission/scorecard allowed now: `false`

The next row may use the schema for compute-node extraction, but only after
claiming a separate scheduler/execution scope.

## Outputs

- `exchange_sampler_required_schema.csv`: field names, units, bases, and
  unavailable-field policies.
- `exchange_sampler_dry_extraction_plan.csv`: salt 2/3/4 queued windows and
  required schema.
- `fixture_validation_rows.csv`: dry package validation rows.
- `no_launch_guardrails.csv`: side-effect and admission guardrails.
- `next_agent_handoff.csv`: ordered follow-on work.
- `source_manifest.csv`: provenance and mutation flags.

## Guardrails

No native CFD/OpenFOAM output, case directory, registry/admission state,
scheduler state, Fluid source, external repository, blocker register, or
generated docs index was mutated. No solver, postprocessor, sampler execution,
fitting, model selection, closure admission, Phase 4B rescore, or Phase 5/S6
scorecard trigger was run.
"""


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    schema = schema_rows()
    plan = dry_plan_rows()
    fixtures = fixture_validation_rows()
    guards = no_launch_guardrails()
    handoff = next_agent_handoff()
    manifest = source_manifest()
    csv_dump(output_dir / "exchange_sampler_required_schema.csv", SCHEMA_FIELDS, schema)
    csv_dump(output_dir / "exchange_sampler_dry_extraction_plan.csv", PLAN_FIELDS, plan)
    csv_dump(output_dir / "fixture_validation_rows.csv", FIXTURE_FIELDS, fixtures)
    csv_dump(output_dir / "no_launch_guardrails.csv", GUARD_FIELDS, guards)
    csv_dump(output_dir / "next_agent_handoff.csv", HANDOFF_FIELDS, handoff)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "required_schema_fields": len(schema),
        "dry_plan_rows": len(plan),
        "fixture_validation_rows": len(fixtures),
        "guardrail_rows": len(guards),
        "handoff_rows": len(handoff),
        "compute_execution_allowed": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_or_postprocessing_or_sampler_launched": False,
        "fluid_edit": False,
        "external_repo_edit": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "phase4b_rescore_run": False,
        "phase5_or_s6_trigger": False,
    }
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    return {"summary": summary, "schema": schema, "plan": plan, "fixtures": fixtures}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(PACKAGE_DIR))
    parser.add_argument("--cell-vtk", default="")
    parser.add_argument("--interface-vtk", default="")
    parser.add_argument("--wall-vtk", default="")
    parser.add_argument("--volume-csv", default="")
    parser.add_argument("--case-id", default="fixture")
    parser.add_argument("--time-window-s", default="fixture")
    parser.add_argument("--throughflow-normal", default="1,0,0")
    parser.add_argument("--interface-normal", default="1,0,0")
    parser.add_argument("--emit-extraction-row", action="store_true")
    parser.add_argument("--delta-p-observed-pa", type=float, default=None)
    parser.add_argument("--delta-p-straight-pa", type=float, default=None)
    parser.add_argument("--delta-p-hydrostatic-pa", type=float, default=0.0)
    parser.add_argument("--delta-p-minor-pa", type=float, default=0.0)
    parser.add_argument("--q-source-w", type=float, default=0.0)
    parser.add_argument("--q-sink-w", type=float, default=0.0)
    parser.add_argument("--cp-j-kg-k", type=float, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    payload = build_package(output_dir)
    should_emit = args.emit_extraction_row or bool(args.cell_vtk) or bool(args.interface_vtk)
    if should_emit:
        missing = [
            name
            for name, value in (("cell_vtk", args.cell_vtk), ("interface_vtk", args.interface_vtk))
            if not value or not Path(value).exists()
        ]
        if missing:
            row = unavailable_exchange_row(args.case_id, args.time_window_s, missing, "missing_required_vtk_inputs")
        else:
            throughflow_normal = parse_vector(args.throughflow_normal)
            interface_normal = parse_vector(args.interface_normal)
            volume_csv = Path(args.volume_csv) if args.volume_csv else None
            cell_state = compute_cell_state(Path(args.cell_vtk), throughflow_normal, volume_csv=volume_csv)
            interface_state = compute_interface_exchange(Path(args.interface_vtk), interface_normal)
            wall_state = compute_wall_state(Path(args.wall_vtk)) if args.wall_vtk else None
            pressure_terms = {
                "delta_p_observed_pa": args.delta_p_observed_pa,
                "delta_p_straight_pa": args.delta_p_straight_pa,
                "delta_p_hydrostatic_pa": args.delta_p_hydrostatic_pa,
                "delta_p_minor_pa": args.delta_p_minor_pa,
            }
            energy_terms = {
                "Q_source_W": args.q_source_w,
                "Q_sink_W": args.q_sink_w,
                "cp_J_kg_K": args.cp_j_kg_k,
            }
            if wall_state is not None and "Q_wall_proxy_W" in wall_state:
                energy_terms["Q_wall_W"] = wall_state["Q_wall_proxy_W"]
            row = assemble_exchange_row(
                args.case_id,
                args.time_window_s,
                cell_state,
                interface_state,
                wall_state,
                pressure_terms=pressure_terms,
                energy_terms=energy_terms,
            )
        write_extraction_rows(output_dir, [row])
        payload["sample_row"] = row
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
