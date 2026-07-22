#!/usr/bin/env python3
"""Build diagnostic ROI-average bridge for blocked S13 upcomer exchange work."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-DIAGNOSTIC-ROI-AVERAGE-BRIDGE-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge"

SEGMENTATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight"
TOPOLOGY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release"
SOURCE_GEN = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
CELL_VOLUME_ROOT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation/cell_volumes"
SALT2_CELL = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/vtk/salt_2_cell_fields.vtk"
SALT34_CELL = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix/vtk"

CASE_IDS = ("salt_2", "salt_3", "salt_4")
VTK_BY_CASE = {
    "salt_2": SALT2_CELL,
    "salt_3": SALT34_CELL / "salt_3_cell_fields.vtk",
    "salt_4": SALT34_CELL / "salt_4_cell_fields.vtk",
}
VOLUME_BY_CASE = {case_id: CELL_VOLUME_ROOT / f"{case_id}_cell_volumes.csv" for case_id in CASE_IDS}
MASK_BY_CASE = {
    case_id: SEGMENTATION / "masks" / f"{case_id}_right_leg_reverse_flow_candidate_mask.csv"
    for case_id in CASE_IDS
}

BRIDGE_FIELDS = [
    "case_id",
    "roi_basis",
    "selected_cell_count",
    "V_recirc_proxy_m3",
    "interface_area_proxy_m2",
    "mean_ux_m_s",
    "mean_uy_m_s",
    "mean_uz_m_s",
    "mean_speed_m_s",
    "T_recirc_proxy_K",
    "rho_recirc_proxy_kg_m3",
    "Q_exchange_proxy_m3_s",
    "mdot_exchange_proxy_kg_s",
    "tau_recirc_proxy_s",
    "q_source_W",
    "q_sink_W",
    "q_net_W",
    "q_wall_W",
    "q_wall_status",
    "q_net_per_V_W_m3",
    "q_net_per_interface_area_W_m2",
    "q_net_over_mdot_proxy_J_kg",
    "pressure_residual_support",
    "energy_residual_support",
    "admission_use",
    "blocking_reason",
]
SOURCE_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]
GUARD_FIELDS = ["guard_id", "status", "policy"]
SUPPORT_FIELDS = [
    "case_id",
    "qoi_or_claim",
    "proxy_value",
    "unit",
    "proxy_basis",
    "can_support_trend_discussion",
    "can_support_admission",
    "admission_status",
    "reason_not_admissible",
]
DECISION_FIELDS = [
    "decision_id",
    "diagnostic_rows",
    "production_harvest_allowed",
    "s11_candidate_released",
    "coefficient_admission_allowed",
    "decision",
    "reason",
]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def by_case(path: Path) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in read_csv(path)}


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        text = str(value).strip()
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def fmt(value: float) -> str:
    return "" if not math.isfinite(value) else f"{value:.12g}"


def read_selected_mask(path: Path) -> dict[int, dict[str, float]]:
    selected: dict[int, dict[str, float]] = {}
    for row in read_csv(path):
        if row.get("mask_role") != "largest_candidate_component":
            continue
        cell_id = int(row["cell_id"])
        selected[cell_id] = {
            "ux": as_float(row["ux"]),
            "uy": as_float(row["uy"]),
            "uz": as_float(row["uz"]),
            "speed": as_float(row["speed"]),
        }
    if not selected:
        raise ValueError(f"no largest_candidate_component rows in {rel(path)}")
    return selected


def read_volumes(path: Path, wanted: set[int]) -> dict[int, float]:
    volumes: dict[int, float] = {}
    for row in read_csv(path):
        cell_id = int(row["cell_id"])
        if cell_id in wanted:
            volumes[cell_id] = as_float(row["cellVolume_m3"])
    missing = wanted - set(volumes)
    if missing:
        raise ValueError(f"volume CSV missing {len(missing)} selected cells in {rel(path)}")
    return volumes


def skip_field_values(handle: Any, n_values: int) -> None:
    remaining = n_values
    while remaining > 0:
        line = handle.readline()
        if not line:
            raise ValueError("unexpected EOF while skipping VTK field values")
        remaining -= len(line.split())


def read_scalar_field_values(handle: Any, n_tuples: int, wanted: set[int]) -> dict[int, float]:
    values: dict[int, float] = {}
    seen = 0
    while seen < n_tuples:
        line = handle.readline()
        if not line:
            raise ValueError("unexpected EOF while reading VTK scalar field")
        for token in line.split():
            if seen in wanted:
                values[seen] = float(token)
            seen += 1
            if seen == n_tuples:
                break
    return values


def read_vtk_scalar_fields(vtk_path: Path, wanted: set[int], field_names: set[str]) -> dict[str, dict[int, float]]:
    found: dict[str, dict[int, float]] = {}
    with vtk_path.open("r", encoding="utf-8", errors="replace") as handle:
        line = handle.readline()
        while line and not line.startswith("CELL_DATA"):
            line = handle.readline()
        if not line:
            raise ValueError(f"CELL_DATA not found in {rel(vtk_path)}")
        field = handle.readline().split()
        if len(field) < 3 or field[0] != "FIELD":
            raise ValueError(f"FIELD attributes not found in {rel(vtk_path)}")
        n_arrays = int(field[2])
        for _ in range(n_arrays):
            header = handle.readline().split()
            while not header:
                header = handle.readline().split()
            name = header[0]
            n_comp = int(header[1])
            n_tuples = int(header[2])
            n_values = n_comp * n_tuples
            if name in field_names and n_comp == 1:
                found[name] = read_scalar_field_values(handle, n_tuples, wanted)
            else:
                skip_field_values(handle, n_values)
    missing_fields = field_names - set(found)
    if missing_fields:
        raise ValueError(f"missing scalar VTK fields {sorted(missing_fields)} in {rel(vtk_path)}")
    return found


def weighted_mean(values: dict[int, float], volumes: dict[int, float]) -> float:
    total_v = sum(volumes.values())
    if total_v <= 0.0:
        return math.nan
    return sum(values[cell_id] * volumes[cell_id] for cell_id in volumes) / total_v


def build_case_row(case_id: str, topology: dict[str, str], source: dict[str, str]) -> dict[str, Any]:
    mask = read_selected_mask(MASK_BY_CASE[case_id])
    selected = set(mask)
    volumes = read_volumes(VOLUME_BY_CASE[case_id], selected)
    vtk_fields = read_vtk_scalar_fields(VTK_BY_CASE[case_id], selected, {"T", "rho"})
    v_recirc = sum(volumes.values())
    mean_ux = weighted_mean({cid: vals["ux"] for cid, vals in mask.items()}, volumes)
    mean_uy = weighted_mean({cid: vals["uy"] for cid, vals in mask.items()}, volumes)
    mean_uz = weighted_mean({cid: vals["uz"] for cid, vals in mask.items()}, volumes)
    mean_speed = weighted_mean({cid: vals["speed"] for cid, vals in mask.items()}, volumes)
    mean_t = weighted_mean(vtk_fields["T"], volumes)
    mean_rho = weighted_mean(vtk_fields["rho"], volumes)
    area = as_float(topology["interface_area_m2"])
    q_exchange = abs(mean_uy) * area
    mdot = mean_rho * q_exchange if math.isfinite(mean_rho) else math.nan
    tau = v_recirc / q_exchange if q_exchange > 0.0 else math.nan
    q_source = as_float(source["q_source_w"])
    q_sink = as_float(source["q_sink_w"])
    q_net = as_float(source["q_net_w"])
    q_net_per_v = q_net / v_recirc if v_recirc > 0.0 else math.nan
    q_net_per_area = q_net / area if area > 0.0 else math.nan
    q_net_over_mdot = q_net / mdot if mdot > 0.0 else math.nan
    blocking = topology["blocking_reason"]
    return {
        "case_id": case_id,
        "roi_basis": "dominant_velocity_component_proxy_nonadmissible",
        "selected_cell_count": len(selected),
        "V_recirc_proxy_m3": fmt(v_recirc),
        "interface_area_proxy_m2": fmt(area),
        "mean_ux_m_s": fmt(mean_ux),
        "mean_uy_m_s": fmt(mean_uy),
        "mean_uz_m_s": fmt(mean_uz),
        "mean_speed_m_s": fmt(mean_speed),
        "T_recirc_proxy_K": fmt(mean_t),
        "rho_recirc_proxy_kg_m3": fmt(mean_rho),
        "Q_exchange_proxy_m3_s": fmt(q_exchange),
        "mdot_exchange_proxy_kg_s": fmt(mdot),
        "tau_recirc_proxy_s": fmt(tau),
        "q_source_W": fmt(q_source),
        "q_sink_W": fmt(q_sink),
        "q_net_W": fmt(q_net),
        "q_wall_W": "",
        "q_wall_status": "blocked_no_trusted_wall_core_band_or_wallHeatFlux_integration",
        "q_net_per_V_W_m3": fmt(q_net_per_v),
        "q_net_per_interface_area_W_m2": fmt(q_net_per_area),
        "q_net_over_mdot_proxy_J_kg": fmt(q_net_over_mdot),
        "pressure_residual_support": "diagnostic_only_blocked_geometry",
        "energy_residual_support": "diagnostic_only_static_source_sink_no_Q_wall_W",
        "admission_use": "nonadmissible_proxy_no_fit_no_exchange_cell_release",
        "blocking_reason": blocking,
    }


def guardrails() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "status": "false", "policy": "read only existing VTK, masks, volumes, and ledgers"},
        {"guard_id": "scheduler_action", "status": "false", "policy": "local diagnostic reduction only"},
        {"guard_id": "surface_extraction", "status": "false", "policy": "blocked geometry cannot launch surface extraction"},
        {"guard_id": "sampler_or_harvest", "status": "false", "policy": "proxy rows are not sampler inputs"},
        {"guard_id": "coefficient_or_admission", "status": "false", "policy": "effective indicators are not coefficients and cannot be fit"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "status": "false", "policy": "energy residual remains explicit and blocked by Q_wall_W"},
    ]


def support_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qois = [
        ("mdot_exchange_proxy_kg_s", "exchange_flux_proxy", "kg/s", "rho_recirc_proxy * abs(mean_Uy) * topology_interface_area_proxy"),
        ("tau_recirc_proxy_s", "residence_time_proxy", "s", "V_recirc_proxy / Q_exchange_proxy"),
        ("q_net_W", "wall_heat_flow_proxy", "W", "static source minus sink net; not wallHeatFlux over released wall band"),
        ("q_net_per_interface_area_W_m2", "surface_intensity_proxy", "W/m2", "static q_net divided by diagnostic topology interface area"),
        ("q_net_over_mdot_proxy_J_kg", "exchange_energy_per_mass_proxy", "J/kg", "static q_net divided by mdot_exchange_proxy"),
    ]
    out: list[dict[str, Any]] = []
    for row in rows:
        for key, claim, unit, basis in qois:
            out.append(
                {
                    "case_id": row["case_id"],
                    "qoi_or_claim": claim,
                    "proxy_value": row.get(key, ""),
                    "unit": unit,
                    "proxy_basis": basis,
                    "can_support_trend_discussion": "true",
                    "can_support_admission": "false",
                    "admission_status": "not_admissible_proxy_only",
                    "reason_not_admissible": (
                        "missing released source-bounded CV, trusted exchange surface, "
                        "trusted wall/core band, Q_wall_W, and same-window UQ"
                    ),
                }
            )
    return out


def decision_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "decision_id": "S13-diagnostic-roi-average-bridge",
            "diagnostic_rows": str(len(rows)),
            "production_harvest_allowed": "false",
            "s11_candidate_released": "false",
            "coefficient_admission_allowed": "false",
            "decision": "diagnostic_proxy_values_available_not_admissible",
            "reason": (
                "average proxy values are available for trend discussion, but known topology/wall/UQ gates remain failed"
            ),
        }
    ]


def source_manifest(out: Path) -> list[dict[str, Any]]:
    paths: list[tuple[Path, str, bool]] = [
        (Path("tools/extract/build_s13_upcomer_exchange_diagnostic_roi_average_bridge.py"), "task_output", False),
        (Path("tools/extract/test_s13_upcomer_exchange_diagnostic_roi_average_bridge.py"), "task_output", False),
        (SEGMENTATION / "recirc_segmentation_case_summary.csv", "read_only_context", False),
        (TOPOLOGY / "topology_cv_case_summary.csv", "read_only_context", False),
        (SOURCE_GEN / "source_sink_summary.csv", "read_only_context", False),
        (CELL_VOLUME_ROOT, "read_only_context", False),
        (out, "task_output", False),
    ]
    for vtk in VTK_BY_CASE.values():
        paths.append((vtk, "read_only_context", False))
    for mask in MASK_BY_CASE.values():
        paths.append((mask, "read_only_context", False))
    rows = []
    for path, role, native in paths:
        full = path if path.is_absolute() else ROOT / path
        rows.append(
            {
                "path": rel(full),
                "role": role,
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(role == "task_output" and full != out).lower(),
            }
        )
    return rows


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    (out / "README.md").write_text(
        f"""---
provenance:
  - {rel(TOPOLOGY / 'topology_cv_case_summary.csv')}
  - {rel(SOURCE_GEN / 'source_sink_summary.csv')}
  - {rel(SEGMENTATION / 'recirc_segmentation_case_summary.csv')}
tags: [s13, upcomer-exchange, diagnostic-proxy, roi-average, no-admission]
related:
  - {rel(OUT / 'diagnostic_roi_average_bridge.csv')}
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_diagnostic_only
---
# S13 Diagnostic ROI-Average Bridge

This package computes a diagnostic-only ROI-average fallback from the blocked
dominant reverse-flow component. It is intended to preserve useful scale
information while keeping S13 production harvest, UQ, fitting, S11/S15/S6, and
exchange-cell admission disabled.

Decision: `complete_diagnostic_only_no_release`.

- cases processed: `{summary['case_count']}`
- diagnostic proxy rows: `{summary['diagnostic_proxy_rows']}`
- proxy support rows: `{summary['proxy_support_rows']}`
- admission rows released: `0`
- surface extraction allowed: `false`
- harvest/UQ allowed: `false`

The proxy uses volume-weighted ROI `U`, `T`, and `rho`, topology diagnostic
interface area, and static source/sink terms. `Q_wall_W` remains unavailable
because no trusted wall/core band or wallHeatFlux integration is released.
Effective indicators such as `q_net_per_V_W_m3` and
`q_net_over_mdot_proxy_J_kg` are not coefficients and must not be fitted.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    topology = by_case(TOPOLOGY / "topology_cv_case_summary.csv")
    source = by_case(SOURCE_GEN / "source_sink_summary.csv")
    rows = [build_case_row(case_id, topology[case_id], source[case_id]) for case_id in CASE_IDS]
    support = support_rows(rows)
    decisions = decision_rows(rows)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "complete_diagnostic_only_no_release",
        "case_count": len(CASE_IDS),
        "diagnostic_proxy_rows": len(rows),
        "proxy_support_rows": len(support),
        "admission_rows_released": 0,
        "surface_extraction_allowed": False,
        "sampler_or_harvest_allowed": False,
        "same_window_uq_allowed": False,
        "fit_or_model_selection": False,
        "exchange_cell_admission": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "residual_absorbed_into_internal_Nu": False,
    }
    csv_dump(out / "diagnostic_roi_average_bridge.csv", BRIDGE_FIELDS, rows)
    csv_dump(out / "diagnostic_roi_average_metrics.csv", BRIDGE_FIELDS, rows)
    csv_dump(out / "proxy_admission_support_matrix.csv", SUPPORT_FIELDS, support)
    csv_dump(out / "diagnostic_bridge_decision.csv", DECISION_FIELDS, decisions)
    csv_dump(out / "no_mutation_guardrails.csv", GUARD_FIELDS, guardrails())
    csv_dump(out / "source_manifest.csv", SOURCE_FIELDS, source_manifest(out))
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return {"summary": summary, "rows": rows}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(args.output_dir)
    print(json.dumps(payload["summary"], indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
