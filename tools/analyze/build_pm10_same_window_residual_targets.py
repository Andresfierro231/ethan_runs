#!/usr/bin/env python3
"""Build same-window PM10 pressure residual targets from matched-plane samples.

The output is diagnostic evidence for recirculation-aware scoring. It is not an
ordinary pipe coefficient, component K, model-selection admission, or runtime
input.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract import sample_upcomer_matched_plane_metrics as matched


PM10_CASES = ("salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q")
DEFAULT_PARSED_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package/parsed"
)
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_pm10_same_window_residual_targets"
)

PLANE_FIELDS = [
    "case_key",
    "plane_location",
    "representative_time_s",
    "sampled_plane_file",
    "pressure_target_status",
    "area_m2",
    "mean_p_rgh_pa",
    "mean_rho_kg_m3",
    "mean_speed_m_s",
    "dynamic_pressure_pa",
    "source_paths",
]

TARGET_FIELDS = [
    "case_key",
    "target_status",
    "residual_metric",
    "pm10_pressure_partial_residual_pa",
    "abs_pm10_pressure_partial_residual_pa",
    "delta_p_rgh_out_minus_in_pa",
    "kinetic_correction_out_minus_in_pa",
    "local_dynamic_pressure_mean_pa",
    "K_partial_dynamic_diagnostic",
    "pressure_residual_basis",
    "fit_allowed_now",
    "model_selection_allowed_now",
    "runtime_input_allowed_now",
    "blockers",
    "source_paths",
]

BLOCKER_FIELDS = [
    "case_key",
    "blocker_id",
    "status",
    "unblock_action",
    "source_paths",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def resolve_workspace_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def fmt(value: Any, precision: int = 10) -> str:
    parsed = parse_float(value)
    if parsed is None:
        return "" if value is None else str(value)
    return f"{parsed:.{precision}g}"


def unique_join(values: Iterable[str]) -> str:
    seen: list[str] = []
    for value in values:
        for part in str(value).split(";"):
            cleaned = part.strip()
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
    return ";".join(seen)


def plane_area_and_fields(path: Path) -> dict[str, float]:
    vtk = matched.parse_legacy_vtk(path)
    points = vtk["points"]
    polygons = vtk["polygons"]
    areas = np.array([matched.polygon_area(points[poly]) for poly in polygons], dtype=float)
    if len(areas) == 0 or float(np.sum(areas)) <= 0.0:
        raise ValueError("no positive-area polygons")
    p_rgh = matched.cell_values(vtk, "p_rgh")
    rho = matched.cell_values(vtk, "rho")
    velocity = matched.cell_values(vtk, "U")
    if p_rgh is None or rho is None or velocity is None:
        raise ValueError("missing one of required fields p_rgh/rho/U")
    p_arr = np.asarray(p_rgh, dtype=float).reshape(len(areas))
    rho_arr = np.asarray(rho, dtype=float).reshape(len(areas))
    vel_arr = np.asarray(velocity, dtype=float).reshape(len(areas), 3)
    speed = np.linalg.norm(vel_arr, axis=1)
    mean_rho = float(np.average(rho_arr, weights=areas))
    mean_speed = float(np.average(speed, weights=areas))
    return {
        "area_m2": float(np.sum(areas)),
        "mean_p_rgh_pa": float(np.average(p_arr, weights=areas)),
        "mean_rho_kg_m3": mean_rho,
        "mean_speed_m_s": mean_speed,
        "dynamic_pressure_pa": 0.5 * mean_rho * mean_speed * mean_speed,
    }


def rows_for_case(parsed_dir: Path, case_key: str) -> list[dict[str, str]]:
    return read_csv(parsed_dir / f"matched_plane_metrics_{case_key}.csv")


def plane_pressure_rows(parsed_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_key in PM10_CASES:
        for row in rows_for_case(parsed_dir, case_key):
            sampled = row.get("sampled_plane_file", "")
            sampled_path = resolve_workspace_path(sampled) if sampled else Path("")
            status = "pressure_plane_available"
            parsed: dict[str, float] = {}
            if not sampled or not sampled_path.exists():
                status = "missing_sampled_plane_vtk"
            else:
                try:
                    parsed = plane_area_and_fields(sampled_path)
                except Exception as exc:  # noqa: BLE001
                    status = f"pressure_plane_parse_failed:{exc}"
            rows.append(
                {
                    "case_key": case_key,
                    "plane_location": row.get("plane_location", ""),
                    "representative_time_s": row.get("representative_time_s", ""),
                    "sampled_plane_file": sampled,
                    "pressure_target_status": status,
                    "area_m2": fmt(parsed.get("area_m2")),
                    "mean_p_rgh_pa": fmt(parsed.get("mean_p_rgh_pa")),
                    "mean_rho_kg_m3": fmt(parsed.get("mean_rho_kg_m3")),
                    "mean_speed_m_s": fmt(parsed.get("mean_speed_m_s")),
                    "dynamic_pressure_pa": fmt(parsed.get("dynamic_pressure_pa")),
                    "source_paths": unique_join([sampled, row.get("source_paths", "")]),
                }
            )
    return rows


def by_case_plane(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("case_key", "")), {})[str(row.get("plane_location", ""))] = row
    return grouped


def target_rows(plane_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = by_case_plane(plane_rows)
    rows: list[dict[str, Any]] = []
    for case_key in PM10_CASES:
        planes = grouped.get(case_key, {})
        inlet = planes.get("upcomer_inlet")
        outlet = planes.get("upcomer_outlet")
        blockers: list[str] = []
        if inlet is None or outlet is None:
            blockers.append("missing_inlet_or_outlet_plane")
        elif inlet.get("pressure_target_status") != "pressure_plane_available":
            blockers.append("inlet_pressure_plane_unavailable")
        elif outlet.get("pressure_target_status") != "pressure_plane_available":
            blockers.append("outlet_pressure_plane_unavailable")
        p_in = parse_float(inlet.get("mean_p_rgh_pa") if inlet else None)
        p_out = parse_float(outlet.get("mean_p_rgh_pa") if outlet else None)
        q_in = parse_float(inlet.get("dynamic_pressure_pa") if inlet else None)
        q_out = parse_float(outlet.get("dynamic_pressure_pa") if outlet else None)
        if p_in is None or p_out is None:
            blockers.append("missing_p_rgh_endpoint")
        if q_in is None or q_out is None:
            blockers.append("missing_dynamic_pressure_endpoint")
        source_paths = unique_join(row.get("source_paths", "") for row in planes.values())
        if blockers:
            rows.append(
                {
                    "case_key": case_key,
                    "target_status": "blocked_missing_pressure_endpoint",
                    "residual_metric": "pm10_pressure_partial_residual_pa",
                    "pm10_pressure_partial_residual_pa": "",
                    "abs_pm10_pressure_partial_residual_pa": "",
                    "delta_p_rgh_out_minus_in_pa": "",
                    "kinetic_correction_out_minus_in_pa": "",
                    "local_dynamic_pressure_mean_pa": "",
                    "K_partial_dynamic_diagnostic": "",
                    "pressure_residual_basis": "blocked",
                    "fit_allowed_now": "no",
                    "model_selection_allowed_now": "no",
                    "runtime_input_allowed_now": "no",
                    "blockers": unique_join(blockers),
                    "source_paths": source_paths,
                }
            )
            continue
        delta_p_rgh = p_out - p_in
        kinetic = q_out - q_in
        residual = delta_p_rgh - kinetic
        q_ref = 0.5 * (q_in + q_out)
        rows.append(
            {
                "case_key": case_key,
                "target_status": "residual_target_available",
                "residual_metric": "pm10_pressure_partial_residual_pa",
                "pm10_pressure_partial_residual_pa": fmt(residual),
                "abs_pm10_pressure_partial_residual_pa": fmt(abs(residual)),
                "delta_p_rgh_out_minus_in_pa": fmt(delta_p_rgh),
                "kinetic_correction_out_minus_in_pa": fmt(kinetic),
                "local_dynamic_pressure_mean_pa": fmt(q_ref),
                "K_partial_dynamic_diagnostic": fmt(residual / q_ref if q_ref and q_ref > 0.0 else None),
                "pressure_residual_basis": "p_rgh_out_minus_in_minus_dynamic_pressure_change;straight_and_development_terms_missing;diagnostic_only",
                "fit_allowed_now": "no",
                "model_selection_allowed_now": "no",
                "runtime_input_allowed_now": "no",
                "blockers": "straight_development_component_isolation_missing;mesh_time_uq_required;split_policy_required",
                "source_paths": source_paths,
            }
        )
    return rows


def blocker_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in targets:
        case_key = row.get("case_key", "")
        if row.get("target_status") != "residual_target_available":
            rows.append(
                {
                    "case_key": case_key,
                    "blocker_id": "PM10_PRESSURE_ENDPOINT_TARGET",
                    "status": row.get("target_status", ""),
                    "unblock_action": "re-run matched-plane OpenFOAM sampling with U/rho/p_rgh on inlet and outlet planes",
                    "source_paths": row.get("source_paths", ""),
                }
            )
        rows.extend(
            [
                {
                    "case_key": case_key,
                    "blocker_id": "PM10_COMPONENT_ISOLATION",
                    "status": "missing",
                    "unblock_action": "add straight/dev pressure terms before interpreting the partial residual as a closure correction",
                    "source_paths": row.get("source_paths", ""),
                },
                {
                    "case_key": case_key,
                    "blocker_id": "PM10_MESH_TIME_UQ",
                    "status": "missing",
                    "unblock_action": "attach same-QOI uncertainty for pressure endpoints and recirculation metrics",
                    "source_paths": row.get("source_paths", ""),
                },
            ]
        )
    return rows


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    (output_dir / "README.md").write_text(
        f"""---
provenance:
  - {summary["parsed_dir"]}
tags: [pm10, pressure, residual-target, upcomer, recirculation]
date: 2026-07-20
type: work_product
status: active
---
# PM10 Same-Window Residual Targets

This package derives same-window PM10 pressure targets from the matched-plane
VTK samples already produced by the PM10 extraction path. The target is a
partial pressure residual:

`p_rgh(outlet) - p_rgh(inlet) - (q_dynamic(outlet) - q_dynamic(inlet))`

It is diagnostic-only because straight/development component isolation and
mesh/time uncertainty are still missing. It is suitable for PM10
recirculation-aware residual ranking, but not for ordinary pipe fitting,
component `K`, model-selection admission, or runtime-input use.
""",
        encoding="utf-8",
    )


def build_package(parsed_dir: Path = DEFAULT_PARSED_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    planes = plane_pressure_rows(parsed_dir)
    targets = target_rows(planes)
    blockers = blocker_rows(targets)
    csv_dump(output_dir / "pm10_plane_pressure_targets.csv", PLANE_FIELDS, planes)
    csv_dump(output_dir / "pm10_same_window_residual_targets.csv", TARGET_FIELDS, targets)
    csv_dump(output_dir / "pm10_same_window_residual_blockers.csv", BLOCKER_FIELDS, blockers)
    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(targets),
        "plane_rows": len(planes),
        "residual_target_available_cases": sum(row["target_status"] == "residual_target_available" for row in targets),
        "fit_allowed_now": 0,
        "model_selection_allowed_now": 0,
        "runtime_input_allowed_now": 0,
        "parsed_dir": rel(parsed_dir),
        "output_dir": rel(output_dir),
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parsed-dir", type=Path, default=DEFAULT_PARSED_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_package(args.parsed_dir, args.output_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
