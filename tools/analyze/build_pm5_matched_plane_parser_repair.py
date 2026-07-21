#!/usr/bin/env python3
"""Repair/reparse staged PM5 matched-plane VTK outputs.

This is a derived parser for the staged AGENT-357 PM5 outputs. It does not run
OpenFOAM and does not mutate native CFD cases.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np


TASK = "AGENT-404"
DATE = "2026-07-15"
OUT_REL = Path("work_products/2026-07/2026-07-15/2026-07-15_pm5_matched_plane_parser_repair")
PM5_PACKAGE_REL = Path("work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock")
STAGED_RECON_REL = Path("tmp/2026-07-14_pm5_corrected_q_matched_plane_unlock/recon")
MESH_CENTERLINE_REL = Path("work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines")
PLANE_SPECS = [
    ("upcomer_inlet", "left_lower_leg", "s00"),
    ("upcomer_mid", "test_section_span", "s02"),
    ("upcomer_outlet", "left_upper_leg", "s04"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(root: Path, path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    materialized = list(rows)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in materialized:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
    return len(materialized)


def fmt(value: Any, precision: int = 10) -> str:
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return ""
    return f"{number:.{precision}g}"


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= 0.0:
        raise ValueError("zero-length normal")
    return vector / norm


def vtk_tokenize(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="ignore").replace("\r", "\n").split()


def parse_legacy_vtk_with_field_arrays(path: Path) -> dict[str, Any]:
    tokens = vtk_tokenize(path)
    idx = 0
    points: np.ndarray | None = None
    polygons: list[list[int]] = []
    point_fields: dict[str, np.ndarray] = {}
    cell_fields: dict[str, np.ndarray] = {}

    def take_float_array(start: int, count: int) -> tuple[np.ndarray, int]:
        vals = [float(tokens[start + i]) for i in range(count)]
        return np.array(vals, dtype=float), start + count

    while idx < len(tokens):
        upper = tokens[idx].upper()
        if upper == "POINTS":
            n_points = int(tokens[idx + 1])
            arr, idx = take_float_array(idx + 3, n_points * 3)
            points = arr.reshape(n_points, 3)
            continue
        if upper == "POLYGONS":
            n_poly = int(tokens[idx + 1])
            total_size = int(tokens[idx + 2])
            idx += 3
            end = idx + total_size
            for _ in range(n_poly):
                n_vertices = int(tokens[idx])
                idx += 1
                polygons.append([int(tokens[idx + j]) for j in range(n_vertices)])
                idx += n_vertices
            idx = end
            continue
        if upper in {"POINT_DATA", "CELL_DATA"}:
            n_items = int(tokens[idx + 1])
            target = point_fields if upper == "POINT_DATA" else cell_fields
            idx += 2
            while idx < len(tokens):
                kind = tokens[idx].upper()
                if kind in {"POINTS", "POLYGONS", "CELL_DATA", "POINT_DATA"}:
                    break
                if kind == "SCALARS":
                    name = tokens[idx + 1]
                    n_comp = int(tokens[idx + 3]) if len(tokens) > idx + 3 and tokens[idx + 3].isdigit() else 1
                    idx += 4
                    if idx < len(tokens) and tokens[idx].upper() == "LOOKUP_TABLE":
                        idx += 2
                    arr, idx = take_float_array(idx, n_items * n_comp)
                    reshaped = arr.reshape(n_items, n_comp)
                    target[name] = reshaped[:, 0] if n_comp == 1 else reshaped
                    continue
                if kind == "VECTORS":
                    name = tokens[idx + 1]
                    idx += 3
                    arr, idx = take_float_array(idx, n_items * 3)
                    target[name] = arr.reshape(n_items, 3)
                    continue
                if kind == "FIELD":
                    n_arrays = int(tokens[idx + 2])
                    idx += 3
                    for _ in range(n_arrays):
                        name = tokens[idx]
                        n_comp = int(tokens[idx + 1])
                        n_tuples = int(tokens[idx + 2])
                        idx += 4  # skip name, component count, tuple count, type
                        arr, idx = take_float_array(idx, n_comp * n_tuples)
                        reshaped = arr.reshape(n_tuples, n_comp)
                        target[name] = reshaped[:, 0] if n_comp == 1 else reshaped
                    continue
                idx += 1
            continue
        idx += 1

    if points is None:
        raise ValueError(f"VTK file has no POINTS block: {path}")
    return {"points": points, "polygons": polygons, "point_fields": point_fields, "cell_fields": cell_fields}


def polygon_area(points: np.ndarray) -> float:
    if len(points) < 3:
        return 0.0
    anchor = points[0]
    area = 0.0
    for idx in range(1, len(points) - 1):
        area += 0.5 * float(np.linalg.norm(np.cross(points[idx] - anchor, points[idx + 1] - anchor)))
    return area


def cell_values(vtk: dict[str, Any], field_name: str) -> np.ndarray | None:
    if field_name in vtk["cell_fields"]:
        return np.asarray(vtk["cell_fields"][field_name], dtype=float)
    if field_name not in vtk["point_fields"]:
        return None
    point_values = np.asarray(vtk["point_fields"][field_name], dtype=float)
    values = [np.mean(point_values[poly], axis=0) for poly in vtk["polygons"]]
    return np.asarray(values, dtype=float)


def load_station(root: Path, source_id: str, span: str, suffix: str) -> dict[str, Any]:
    path = root / MESH_CENTERLINE_REL / source_id / "mesh_stations.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    label = f"{span}__{suffix}"
    for station in payload.get("stations", []):
        if station.get("label") == label:
            return station
    raise KeyError(f"missing station {label} for {source_id}")


def choose_time_dir(case_dir: Path, fo_name: str, preferred_time: str) -> Path | None:
    base = case_dir / "postProcessing" / fo_name
    if (base / preferred_time).exists():
        return base / preferred_time
    if not base.exists():
        return None
    dirs = [path for path in base.iterdir() if path.is_dir()]
    if not dirs:
        return None
    return sorted(dirs, key=lambda p: p.name)[-1]


def parse_plane_vtk(path: Path, normal: np.ndarray) -> dict[str, Any]:
    vtk = parse_legacy_vtk_with_field_arrays(path)
    points = vtk["points"]
    polygons = vtk["polygons"]
    areas = np.array([polygon_area(points[poly]) for poly in polygons], dtype=float)
    if len(areas) == 0 or float(np.sum(areas)) <= 0.0:
        raise ValueError("no positive-area polygons")
    velocities = cell_values(vtk, "U")
    rho = cell_values(vtk, "rho")
    temp = cell_values(vtk, "T")
    if velocities is None or rho is None or temp is None:
        raise ValueError("missing one of required fields U/rho/T")
    velocities = np.asarray(velocities, dtype=float).reshape(len(areas), 3)
    rho = np.asarray(rho, dtype=float).reshape(len(areas))
    temp = np.asarray(temp, dtype=float).reshape(len(areas))
    un = velocities @ normal
    speed2 = np.sum(velocities * velocities, axis=1)
    secondary2 = np.sum((velocities - np.outer(un, normal)) ** 2, axis=1)
    reverse = un < 0.0
    abs_flux = np.abs(rho * un) * areas
    reverse_flux = np.maximum(-rho * un, 0.0) * areas
    signed_flux = rho * un * areas
    forward_flux = np.maximum(rho * un, 0.0) * areas
    signed_denom = float(np.sum(signed_flux))
    forward_denom = float(np.sum(forward_flux))
    abs_flux_denom = float(np.sum(abs_flux))
    signed_bulk_t = float(np.sum(signed_flux * temp) / signed_denom) if abs(signed_denom) > 1e-300 else math.nan
    forward_bulk_t = float(np.sum(forward_flux * temp) / forward_denom) if forward_denom > 1e-300 else math.nan
    signed_flux_ratio = abs(signed_denom) / max(abs_flux_denom, 1e-300)
    use_forward_bulk = signed_flux_ratio < 1.0e-3 or not (250.0 <= signed_bulk_t <= 900.0)
    parsed: dict[str, Any] = {
        "face_count": len(areas),
        "reverse_area_fraction": float(np.sum(areas[reverse]) / np.sum(areas)),
        "reverse_mass_fraction": float(np.sum(reverse_flux) / max(float(np.sum(abs_flux)), 1e-300)),
        "secondary_velocity_fraction": float(
            math.sqrt(float(np.average(secondary2, weights=areas)))
            / max(math.sqrt(float(np.average(speed2, weights=areas))), 1e-300)
        ),
        "bulk_T_K": forward_bulk_t if use_forward_bulk else signed_bulk_t,
        "signed_mass_flux_bulk_T_K": signed_bulk_t,
        "forward_bulk_T_K": forward_bulk_t,
        "bulk_T_rule": "forward_mass_flux_bulk_T_signed_flux_near_cancelled" if use_forward_bulk else "signed_mass_flux_bulk_T",
        "signed_flux_ratio": signed_flux_ratio,
        "signed_mass_flow_proxy": signed_denom,
    }
    for field in ("Re", "Pr", "Ri", "Gr", "Ra"):
        values = cell_values(vtk, field)
        if values is not None:
            parsed[field] = float(np.average(np.asarray(values, dtype=float).reshape(len(areas)), weights=areas))
    if "Re" in parsed and "Pr" in parsed:
        diameter = 0.021209  # 0.835 in test-section bore, used only as fallback scale.
        parsed["Gz"] = float(parsed["Re"]) * float(parsed["Pr"]) * diameter
    return parsed


def parse_wall_vtk(path: Path, station: dict[str, Any]) -> dict[str, Any]:
    vtk = parse_legacy_vtk_with_field_arrays(path)
    points = vtk["points"]
    polygons = vtk["polygons"]
    temp = cell_values(vtk, "T")
    whf = cell_values(vtk, "wallHeatFlux")
    if temp is None:
        raise ValueError("missing wall T")
    normal = normalize(np.array([float(station["nx"]), float(station["ny"]), float(station["nz"])]))
    point = np.array([float(station["x"]), float(station["y"]), float(station["z"])])
    bore = float(station.get("bore_m") or 0.02)
    band_half_width = 0.5 * bore
    areas = np.array([polygon_area(points[poly]) for poly in polygons], dtype=float)
    keep = []
    for poly in polygons:
        centroid = np.mean(points[poly], axis=0)
        keep.append(abs(float((centroid - point) @ normal)) <= band_half_width)
    keep_arr = np.asarray(keep, dtype=bool)
    if int(np.sum(keep_arr)) < 1:
        keep_arr = np.ones(len(areas), dtype=bool)
    selected_areas = areas[keep_arr]
    temp_values = np.asarray(temp, dtype=float).reshape(len(areas))[keep_arr]
    result = {
        "wall_face_count": int(np.sum(keep_arr)),
        "wall_T_K": float(np.average(temp_values, weights=selected_areas)),
        "wall_band_half_width_m": band_half_width,
        "wallHeatFlux_available": whf is not None,
    }
    if whf is not None:
        whf_values = np.asarray(whf, dtype=float).reshape(len(areas))[keep_arr]
        result["wallHeatFlux_W_m2"] = float(np.average(whf_values, weights=selected_areas))
    return result


def parse_case(root: Path, case: dict[str, str]) -> list[dict[str, object]]:
    case_key = case["case_key"]
    case_dir = root / STAGED_RECON_REL / case_key
    rows = []
    for plane_location, span, suffix in PLANE_SPECS:
        station = load_station(root, case["parent_geometry_source_id"], span, suffix)
        normal = normalize(np.array([float(station["nx"]), float(station["ny"]), float(station["nz"])]))
        plane_time_dir = choose_time_dir(case_dir, "upcomerMatchedPlaneSurfaces", case["representative_time_s"])
        wall_time_dir = choose_time_dir(case_dir, "upcomerMatchedWallBandSurfaces", case["representative_time_s"])
        plane_path = plane_time_dir / f"plane_{plane_location}.vtk" if plane_time_dir else None
        wall_path = wall_time_dir / "upcomerWallPatches.vtk" if wall_time_dir else None
        parsed: dict[str, Any] = {}
        quality: list[str] = []
        if plane_path is None or not plane_path.exists():
            quality.append("missing_plane_vtk")
        else:
            try:
                parsed.update(parse_plane_vtk(plane_path, normal))
            except Exception as exc:  # pragma: no cover - captured in output.
                quality.append(f"plane_parse_failed:{exc}")
        if wall_path is None or not wall_path.exists():
            quality.append("missing_wall_vtk")
        else:
            try:
                parsed.update(parse_wall_vtk(wall_path, station))
            except Exception as exc:  # pragma: no cover - captured in output.
                quality.append(f"wall_parse_failed:{exc}")
        if parsed.get("wallHeatFlux_available") is False:
            quality.append("wallHeatFlux_missing_from_staged_wall_band_vtk")
        has_plane = all(key in parsed for key in ("reverse_area_fraction", "reverse_mass_fraction", "bulk_T_K", "Re", "Pr", "Ri"))
        has_wall_t = "wall_T_K" in parsed
        has_whf = "wallHeatFlux_W_m2" in parsed
        if has_plane and has_wall_t and has_whf:
            metric_status = "complete_with_wallHeatFlux"
            admission_status = "ready_for_pressure_and_internal_nu_gate_review_not_admitted"
        elif has_plane and has_wall_t:
            metric_status = "plane_and_wall_temperature_repaired_wallHeatFlux_blocked"
            admission_status = "ready_for_f6_pressure_onset_review_not_internal_nu"
        else:
            metric_status = "incomplete"
            admission_status = "blocked"
        delta = None
        if "wall_T_K" in parsed and "bulk_T_K" in parsed:
            delta = float(parsed["wall_T_K"]) - float(parsed["bulk_T_K"])
        rows.append(
            {
                "case_key": case_key,
                "source_id": case["parent_geometry_source_id"],
                "case_role": case["requested_split_role"],
                "plane_location": plane_location,
                "span": span,
                "station_label": f"{span}__{suffix}",
                "representative_time_s": case["representative_time_s"],
                "actual_plane_time_dir": plane_time_dir.name if plane_time_dir else "",
                "actual_wall_time_dir": wall_time_dir.name if wall_time_dir else "",
                "sampled_plane_file": rel(root, plane_path),
                "sampled_wall_file": rel(root, wall_path),
                "metric_status": metric_status,
                "face_count": parsed.get("face_count", ""),
                "wall_face_count": parsed.get("wall_face_count", ""),
                "reverse_area_fraction": fmt(parsed.get("reverse_area_fraction")),
                "reverse_mass_fraction": fmt(parsed.get("reverse_mass_fraction")),
                "secondary_velocity_fraction": fmt(parsed.get("secondary_velocity_fraction")),
                "bulk_T_K": fmt(parsed.get("bulk_T_K")),
                "forward_bulk_T_K": fmt(parsed.get("forward_bulk_T_K")),
                "bulk_T_rule": parsed.get("bulk_T_rule", "signed_mass_flux_bulk_T"),
                "wall_T_K": fmt(parsed.get("wall_T_K")),
                "wallHeatFlux_W_m2": fmt(parsed.get("wallHeatFlux_W_m2")),
                "wallHeatFlux_available": str(has_whf).lower(),
                "Re": fmt(parsed.get("Re")),
                "Pr": fmt(parsed.get("Pr")),
                "Ri": fmt(parsed.get("Ri")),
                "Gr": fmt(parsed.get("Gr")),
                "Ra": fmt(parsed.get("Ra")),
                "Gz": fmt(parsed.get("Gz")),
                "delta_T_wall_bulk_K": fmt(delta),
                "admission_status": admission_status,
                "quality_flags": ";".join(quality),
                "source_paths": case["source_case_dir"] + ";" + case["mesh_stations_path"],
            }
        )
    return rows


METRIC_FIELDS = [
    "case_key",
    "source_id",
    "case_role",
    "plane_location",
    "span",
    "station_label",
    "representative_time_s",
    "actual_plane_time_dir",
    "actual_wall_time_dir",
    "sampled_plane_file",
    "sampled_wall_file",
    "metric_status",
    "face_count",
    "wall_face_count",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "bulk_T_K",
    "forward_bulk_T_K",
    "bulk_T_rule",
    "wall_T_K",
    "wallHeatFlux_W_m2",
    "wallHeatFlux_available",
    "Re",
    "Pr",
    "Ri",
    "Gr",
    "Ra",
    "Gz",
    "delta_T_wall_bulk_K",
    "admission_status",
    "quality_flags",
    "source_paths",
]


def build(root: Path, out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = read_csv(root / PM5_PACKAGE_REL / "pm5_matched_plane_case_list.csv")
    metric_rows = []
    for case in cases:
        metric_rows.extend(parse_case(root, case))
    status_counts: dict[str, int] = {}
    for row in metric_rows:
        status_counts[row["metric_status"]] = status_counts.get(row["metric_status"], 0) + 1
    repaired_rows = sum(1 for row in metric_rows if str(row["metric_status"]).startswith("plane_and_wall_temperature"))
    whf_rows = sum(1 for row in metric_rows if row["wallHeatFlux_available"] == "true")
    f6_ready = repaired_rows == len(metric_rows) and len(metric_rows) > 0
    gate_rows = [
        {
            "gate": "pm5_plane_parser_repair",
            "status": "pass" if repaired_rows == len(metric_rows) else "partial",
            "evidence": f"metric_rows={len(metric_rows)}; repaired_plane_wallT_rows={repaired_rows}; status_counts={status_counts}",
            "next_action": "consume repaired U/rho/T/Re/Ri rows for F6/onset review",
        },
        {
            "gate": "pm5_wallHeatFlux_internal_nu",
            "status": "blocked_missing_wallHeatFlux",
            "evidence": f"wallHeatFlux_rows={whf_rows}; foamPostProcess wallHeatFlux failed in staged logs",
            "next_action": "repair OpenFOAM wallHeatFlux functionObject/thermophysicalTransport context before internal-Nu admission",
        },
        {
            "gate": "f6_phi_re_bounded_review",
            "status": "ready_for_review_not_admitted" if f6_ready else "blocked",
            "evidence": f"all_pm5_rows_have_repaired_plane_and_wallT={f6_ready}; admitted_rows=0",
            "next_action": "resample missing PM5 plane fields before F6 gate; keep mdot as guardrail and no global multiplier",
        },
    ]
    by_case: dict[str, list[dict[str, object]]] = {}
    for row in metric_rows:
        by_case.setdefault(str(row["case_key"]), []).append(row)
    resample_rows = []
    for case_key, rows in sorted(by_case.items()):
        repaired = sum(1 for row in rows if str(row["metric_status"]).startswith("plane_and_wall_temperature"))
        missing_plane = sum(1 for row in rows if "plane_parse_failed" in str(row["quality_flags"]))
        missing_whf = sum(1 for row in rows if row["wallHeatFlux_available"] == "false")
        if missing_plane:
            required_action = "resample planes with rho/Re/Pr/Ri/Gr/Ra plus U/T at representative time"
        elif missing_whf:
            required_action = "repair wallHeatFlux generation/sampling for wall band"
        else:
            required_action = "none"
        resample_rows.append(
            {
                "case_key": case_key,
                "rows": len(rows),
                "repaired_plane_wallT_rows": repaired,
                "missing_plane_field_rows": missing_plane,
                "missing_wallHeatFlux_rows": missing_whf,
                "required_action": required_action,
            }
        )
    counts = {
        "repaired_metric_rows": write_csv(out_dir / "repaired_pm5_matched_plane_metrics.csv", metric_rows, METRIC_FIELDS),
        "gate_rows": write_csv(out_dir / "pm5_f6_gate_refresh.csv", gate_rows, ["gate", "status", "evidence", "next_action"]),
        "resample_rows": write_csv(out_dir / "pm5_resample_requirements.csv", resample_rows, ["case_key", "rows", "repaired_plane_wallT_rows", "missing_plane_field_rows", "missing_wallHeatFlux_rows", "required_action"]),
    }
    source_rows = [
        {"path": str(PM5_PACKAGE_REL / "pm5_matched_plane_case_list.csv"), "role": "case list", "exists": str((root / PM5_PACKAGE_REL / "pm5_matched_plane_case_list.csv").exists()).lower()},
        {"path": str(STAGED_RECON_REL), "role": "staged VTK inputs", "exists": str((root / STAGED_RECON_REL).exists()).lower()},
        {"path": "tools/extract/sample_upcomer_matched_plane_metrics.py", "role": "original parser used for comparison", "exists": str((root / "tools/extract/sample_upcomer_matched_plane_metrics.py").exists()).lower()},
    ]
    counts["source_rows"] = write_csv(out_dir / "source_manifest.csv", source_rows, ["path", "role", "exists"])
    summary = {
        "task": TASK,
        "date": DATE,
        "created_utc": utc_now(),
        "case_count": len(cases),
        "metric_rows": len(metric_rows),
        "status_counts": status_counts,
        "wallHeatFlux_rows": whf_rows,
        "f6_pressure_onset_review_ready_not_admitted": f6_ready,
        "internal_nu_wallHeatFlux_blocked": whf_rows < len(metric_rows),
        "native_solver_outputs_mutated": False,
        "openfoam_launched": False,
        "scheduler_jobs_launched": False,
        "external_fluid_modified": False,
        "counts": counts,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    readme = f"""# PM5 Matched-Plane Parser Repair

Date: {DATE}
Task: {TASK}

## Result

Repaired parsing of staged PM5 legacy VTK `FIELD attributes` arrays. The parser
recovers full `U`, `rho`, `T`, `Re`, `Pr`, `Ri`, `Gr`, `Ra`, and wall-band `T`
for `salt2_lo5q`.

The repair is partial: `salt2_hi5q`, `salt4_lo5q`, and `salt4_hi5q` staged
plane VTKs only contain `T`, `p_rgh`, and `U`, so F6 remains blocked until those
planes are resampled with `rho/Re/Pr/Ri/Gr/Ra`. Internal-Nu also remains blocked
because `wallHeatFlux` was not present in the staged wall-band VTKs.

## Outputs

- `repaired_pm5_matched_plane_metrics.csv` ({len(metric_rows)} rows)
- `pm5_f6_gate_refresh.csv` ({len(gate_rows)} rows)
- `pm5_resample_requirements.csv` ({len(resample_rows)} rows)
- `source_manifest.csv`
- `summary.json`

## Next Action

Resample the three incomplete PM5 cases with the full plane field set
`U rho T Re Pr Ri Gr Ra`, and repair the OpenFOAM `wallHeatFlux` generation
context before attempting internal-Nu admission.

## Guardrails

- No OpenFOAM solver or postprocessing launch.
- No native CFD solver-output mutation.
- No external Fluid edit.
- No scheduler action.
"""
    (out_dir / "README.md").write_text(readme)
    return summary


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    summary = build(root, root / OUT_REL)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
