#!/usr/bin/env python3
"""Sample physical segment interface bulk temperatures from existing XY planes.

The July 8 span-endpoint package proved that existing ``secmeanSurfaces`` XY
files can recover mass-flux-weighted bulk temperatures without rerunning
OpenFOAM. This follow-up makes the interface contract explicit for heat-ledger
control volumes: every sampled row identifies the physical segment, inlet or
outlet role, source plane, recirculation status, and temperature selection rule.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from sample_span_endpoint_temperatures import (
    bulk_t_from_xy,
    find_secmean_dir,
    load_xy_for_station,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECON_ROOT = ROOT / "tmp/2026-06-30_claude_action_items"
DEFAULT_OUT = ROOT / "work_products/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces"
TASK_DATE = "2026-07-09"
TASK_ID = "TODO-THERMAL-OPENFOAM-INTERFACE-SAMPLING"
THERMAL_PACKAGE = (
    ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling"
)
THERMAL_TMP = ROOT / "tmp/2026-07-09_thermal_openfoam_interface_sampling"
MESH_CENTERLINE_ROOT = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
OF_ENV_SCRIPT = ROOT / "tools/ofenv/of13_env.sh"
FO_NAME = "thermalInterfaceSurfaces"

CASES = [
    {
        "case_id": "salt_2",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "recon_dir_name": "recon_salt2_of13",
    },
    {
        "case_id": "salt_3",
        "source_id": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "recon_dir_name": "recon_salt3_of13",
    },
    {
        "case_id": "salt_4",
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "recon_dir_name": "recon_salt4_of13",
    },
]

MAINLINE_CASES = [
    {
        "case_id": "salt_2",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "source_case_root": ROOT
        / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
        "existing_recon_dir": DEFAULT_RECON_ROOT / "recon_salt2_of13",
        "time_s": "7915",
    },
    {
        "case_id": "salt_3",
        "source_id": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "source_case_root": ROOT
        / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
        "existing_recon_dir": DEFAULT_RECON_ROOT / "recon_salt3_of13",
        "time_s": "7618",
    },
    {
        "case_id": "salt_4",
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "source_case_root": ROOT
        / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
        "existing_recon_dir": DEFAULT_RECON_ROOT / "recon_salt4_of13",
        "time_s": "10000",
    },
]

CONTROL_PLANE_FIELDS = [
    "case_id",
    "source_id",
    "plane_label",
    "control_volume",
    "control_volume_group",
    "interface_role",
    "span",
    "fraction_along_span",
    "x",
    "y",
    "z",
    "nx",
    "ny",
    "nz",
    "normal_positive_direction",
    "geometry_source",
    "notes",
]

OPENFOAM_SAMPLE_FIELDS = [
    "case_id",
    "source_id",
    "time_s",
    "plane_label",
    "control_volume",
    "control_volume_group",
    "interface_role",
    "span",
    "plane_file",
    "status",
    "n_faces",
    "n_masked",
    "T_mixing_cup_signed_K",
    "T_positive_normal_bulk_K",
    "T_negative_normal_bulk_K",
    "T_forward_dominant_bulk_K",
    "T_simple_K",
    "mdot_signed_proxy",
    "positive_flux_proxy",
    "negative_flux_proxy_abs",
    "dominant_flow_direction",
    "backflow_fraction",
    "temperature_selection_rule",
    "radiation_output_term",
    "quality_flags",
]

OPENFOAM_COMPONENTS = [
    {
        "control_volume": "heater_interior",
        "control_volume_group": "heater",
        "span": "lower_leg",
        "start_fraction": 3.0 / 9.0,
        "end_fraction": 6.0 / 9.0,
        "notes": "Brackets pipeleg_lower_04_straight through pipeleg_lower_06_straight, not the full lower leg.",
    },
    {
        "control_volume": "cooler_reducer_interior",
        "control_volume_group": "cooler_reducer",
        "span": "upper_leg",
        "start_fraction": 3.0 / 9.0,
        "end_fraction": 6.0 / 9.0,
        "notes": "Brackets pipeleg_upper_06_reducer, pipeleg_upper_05_cooler, and pipeleg_upper_04_reducer.",
    },
]

JUNCTION_PLANES = [
    ("lower_left_junction", "junction", "lower_leg", 0.5 / 9.0, "lower_leg_face"),
    ("lower_left_junction", "junction", "left_lower_leg", 0.5 / 2.0, "left_lower_leg_face"),
    ("lower_right_junction", "junction", "lower_leg", 8.5 / 9.0, "lower_leg_face"),
    ("lower_right_junction", "junction", "right_leg", 0.5 / 3.0, "right_leg_face"),
    ("upper_right_junction", "junction", "right_leg", 2.5 / 3.0, "right_leg_face"),
    ("upper_right_junction", "junction", "upper_leg", 8.5 / 9.0, "upper_leg_face"),
    ("upper_left_junction", "junction", "upper_leg", 0.5 / 9.0, "upper_leg_face"),
    ("upper_left_junction", "junction", "left_upper_leg", 1.5 / 2.0, "left_upper_leg_face"),
    ("test_section_lower_junction", "junction", "left_lower_leg", 1.5 / 2.0, "left_lower_leg_face"),
    ("test_section_lower_junction", "junction", "test_section_span", 2.5 / 3.0, "test_section_face"),
    ("test_section_upper_junction", "junction", "test_section_span", 0.5 / 3.0, "test_section_face"),
    ("test_section_upper_junction", "junction", "left_upper_leg", 0.5 / 2.0, "left_upper_leg_face"),
]

RAW_SPANS = [
    "lower_leg",
    "left_lower_leg",
    "test_section_span",
    "left_upper_leg",
    "upper_leg",
    "right_leg",
]

RAW_SPAN_FLOW = {
    "lower_leg": ("s04", "s00"),
    "left_lower_leg": ("s00", "s04"),
    "test_section_span": ("s00", "s04"),
    "left_upper_leg": ("s00", "s04"),
    "upper_leg": ("s00", "s04"),
    "right_leg": ("s04", "s00"),
}

PHYSICAL_SEGMENTS = [
    {
        "physical_segment": "lower_leg",
        "component_spans": ["lower_leg"],
        "inlet_span": "lower_leg",
        "inlet_station": "s04",
        "outlet_span": "lower_leg",
        "outlet_station": "s00",
        "bracket_status": "bracketed_full_span_interfaces",
        "fit_use_status": "validation_diagnostic",
        "notes": "Full lower-leg control volume; heater patch is not separately bracketed inside the span.",
    },
    {
        "physical_segment": "cooling_branch",
        "component_spans": ["upper_leg"],
        "inlet_span": "upper_leg",
        "inlet_station": "s00",
        "outlet_span": "upper_leg",
        "outlet_station": "s04",
        "bracket_status": "bracketed_upper_leg_but_partial_cooler_sink",
        "fit_use_status": "validation_diagnostic",
        "notes": "Available upper-leg endpoints do not isolate the cooler/reducer sink; July 8 span package estimated only partial cooler coverage.",
    },
    {
        "physical_segment": "downcomer",
        "component_spans": ["right_leg"],
        "inlet_span": "right_leg",
        "inlet_station": "s04",
        "outlet_span": "right_leg",
        "outlet_station": "s00",
        "bracket_status": "bracketed_full_span_interfaces",
        "fit_use_status": "validation_diagnostic",
        "notes": "Right-leg downcomer flow is reversed relative to station labels.",
    },
    {
        "physical_segment": "upcomer",
        "component_spans": ["left_lower_leg", "test_section_span", "left_upper_leg"],
        "inlet_span": "left_lower_leg",
        "inlet_station": "s00",
        "outlet_span": "left_upper_leg",
        "outlet_station": "s04",
        "bracket_status": "bracketed_composite_high_recirculation_diagnostic",
        "fit_use_status": "validation_only_recirculation_cell",
        "notes": "Composite riser control volume; high recirculation makes residuals diagnostic only.",
    },
    {
        "physical_segment": "junction",
        "component_spans": [],
        "inlet_span": "",
        "inlet_station": "",
        "outlet_span": "",
        "outlet_station": "",
        "bracket_status": "not_bracketed_by_available_secmean_surfaces",
        "fit_use_status": "not_fit_unbracketed_junction",
        "notes": "Grouped junction wall losses are not enclosed by a single inlet/outlet interface pair.",
    },
]

SAMPLE_FIELDS = [
    "source_id",
    "case_id",
    "recon_case_dir",
    "secmean_dir",
    "physical_segment",
    "component_span",
    "interface_role",
    "station_label",
    "plane_file",
    "T_bulk_K",
    "T_fwd_bulk_K",
    "T_simple_K",
    "T_used_K",
    "temperature_selection_rule",
    "recirculation_ratio",
    "mdot_proxy",
    "n_faces",
    "n_masked",
    "status",
    "quality_flags",
]

REGISTRY_FIELDS = [
    "source_id",
    "case_id",
    "physical_segment",
    "component_spans",
    "inlet_interface",
    "outlet_interface",
    "bracket_status",
    "fit_use_status",
    "notes",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def station_index(station: str) -> int:
    return int(station.removeprefix("s"))


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def fmt(value: Any, digits: int = 6) -> str:
    parsed = safe_float(value)
    if parsed is None:
        return ""
    return f"{parsed:.{digits}f}".rstrip("0").rstrip(".")


def q(value: str | Path) -> str:
    return "'" + str(value).replace("'", "'\"'\"'") + "'"


def slug(value: str) -> str:
    return "".join(char if char.isalnum() or char == "_" else "_" for char in value)


def mesh_stations_path(source_id: str) -> Path:
    return MESH_CENTERLINE_ROOT / source_id / "mesh_stations.json"


def load_mesh_payload(source_id: str) -> dict[str, Any]:
    path = mesh_stations_path(source_id)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def stations_by_span(source_id: str) -> dict[str, list[dict[str, Any]]]:
    payload = load_mesh_payload(source_id)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for station in payload.get("stations", []):
        grouped[str(station["span"])].append(station)
    for span, rows in grouped.items():
        rows.sort(key=lambda row: station_index(str(row["label"]).split("__s")[-1]))
    return grouped


def unit(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 0.0:
        return values
    return [value / norm for value in values]


def interpolate_span_plane(source_id: str, span: str, fraction: float) -> dict[str, float]:
    grouped = stations_by_span(source_id)
    rows = grouped.get(span, [])
    if len(rows) < 2:
        raise ValueError(f"source_id={source_id} span={span} has too few mesh stations")
    bounded = max(0.0, min(1.0, fraction))
    scaled = bounded * (len(rows) - 1)
    lo = min(int(math.floor(scaled)), len(rows) - 2)
    hi = lo + 1
    alpha = scaled - lo
    out: dict[str, float] = {}
    for key in ("x", "y", "z", "nx", "ny", "nz"):
        out[key] = (1.0 - alpha) * float(rows[lo][key]) + alpha * float(rows[hi][key])
    nx, ny, nz = unit([out["nx"], out["ny"], out["nz"]])
    out.update({"nx": nx, "ny": ny, "nz": nz})
    return out


def build_openfoam_plane_plan(source_id: str, case_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    geometry_source = rel(mesh_stations_path(source_id))
    for component in OPENFOAM_COMPONENTS:
        for role, fraction in (
            ("cv_inlet_bracket", component["start_fraction"]),
            ("cv_outlet_bracket", component["end_fraction"]),
        ):
            geom = interpolate_span_plane(source_id, component["span"], float(fraction))
            label = f"{component['control_volume']}__{role}"
            rows.append(
                {
                    "case_id": case_id,
                    "source_id": source_id,
                    "plane_label": label,
                    "control_volume": component["control_volume"],
                    "control_volume_group": component["control_volume_group"],
                    "interface_role": role,
                    "span": component["span"],
                    "fraction_along_span": fmt(fraction, 8),
                    "normal_positive_direction": "mesh_station_s00_to_s04",
                    "geometry_source": geometry_source,
                    "notes": component["notes"],
                    **{key: fmt(value, 10) for key, value in geom.items()},
                }
            )
    for volume, group, span, fraction, role in JUNCTION_PLANES:
        geom = interpolate_span_plane(source_id, span, float(fraction))
        label = f"{volume}__{role}"
        rows.append(
            {
                "case_id": case_id,
                "source_id": source_id,
                "plane_label": label,
                "control_volume": volume,
                "control_volume_group": group,
                "interface_role": role,
                "span": span,
                "fraction_along_span": fmt(fraction, 8),
                "normal_positive_direction": "mesh_station_s00_to_s04",
                "geometry_source": geometry_source,
                "notes": "Brackets a junction control-volume face just inside the adjacent pipe span.",
                **{key: fmt(value, 10) for key, value in geom.items()},
            }
        )
    return rows


def openfoam_field_exists(case_dir: Path, time_name: str, field: str) -> bool:
    return (case_dir / time_name / field).exists()


def write_openfoam_control_dict(case_dir: Path, time_name: str, source_id: str, case_id: str) -> dict[str, Any]:
    rows = build_openfoam_plane_plan(source_id, case_id)
    fields = ["U", "T", "rho", "p_rgh"]
    radiation_term = "absent_no_qr_output"
    if openfoam_field_exists(case_dir, time_name, "qr"):
        fields.append("qr")
        radiation_term = "qr_field_present_sampled"
    lines = [
        "FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }",
        "application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;",
        "writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;",
        "writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;",
        "functions {",
        f"  {FO_NAME} {{",
        "    type            surfaces;",
        '    libs            ("libsampling.so");',
        "    writeControl    writeTime;",
        "    surfaceFormat   raw;",
        "    interpolate     false;",
        "    interpolationScheme cell;",
        f"    fields          ({' '.join(fields)});",
        "    surfaces (",
    ]
    for row in rows:
        label = slug(str(row["plane_label"]))
        lines += [
            f"      plane_{label} {{",
            "        type        cuttingPlane;",
            "        planeType   pointAndNormal;",
            "        pointAndNormalDict",
            "        {",
            f"          point ({row['x']} {row['y']} {row['z']});",
            f"          normal ({row['nx']} {row['ny']} {row['nz']});",
            "        }",
            "      }",
        ]
    lines += ["    );", "  }", "}"]
    out = case_dir / "system" / "controlDict"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "control_dict": rel(out),
        "fields": fields,
        "radiation_output_term": radiation_term,
        "plane_count": len(rows),
    }


def plane_xy_path(case_dir: Path, time_name: str, plane_label: str) -> Path | None:
    base = case_dir / "postProcessing" / FO_NAME / time_name
    candidates = [
        base / f"plane_{slug(plane_label)}.xy",
        base / f"plane_{plane_label}.xy",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    hits = list((case_dir / "postProcessing" / FO_NAME).glob(f"**/*{slug(plane_label)}*.xy"))
    return hits[0] if hits else None


def resolve_raw_columns(data: np.ndarray) -> dict[str, int]:
    if data.shape[1] >= 9:
        med6 = float(np.median(data[:, 6]))
        med7 = float(np.median(data[:, 7]))
        med8 = float(np.median(data[:, 8]))
        rho_col = 7 if 1500.0 <= med7 <= 2300.0 else 8
        if 250.0 <= med6 <= 1500.0:
            return {"T": 6, "rho": rho_col, "qr": 9 if data.shape[1] > 9 else -1}
        if 250.0 <= med8 <= 1500.0:
            return {"T": 8, "rho": 7, "qr": 9 if data.shape[1] > 9 else -1}
    return {"T": -1, "rho": 7, "qr": -1}


def parse_raw_plane_sample(path: Path, normal: tuple[float, float, float]) -> dict[str, Any]:
    try:
        data = np.loadtxt(path, comments="#")
    except Exception as exc:  # noqa: BLE001
        return {"status": f"unreadable: {exc}"}
    if data.ndim == 1:
        data = data.reshape(1, -1)
    if data.size == 0 or data.shape[1] < 8:
        return {"status": "insufficient_columns", "n_faces": 0, "n_masked": 0}
    cols = resolve_raw_columns(data)
    pts = data[:, :3]
    velocities = data[:, 3:6]
    rho = data[:, cols["rho"]]
    if cols["T"] >= 0:
        temp = data[:, cols["T"]]
        temperature_rule = "raw_T_field"
    else:
        temp = t_from_rho_array(rho)
        temperature_rule = "rho_inversion_no_raw_T_column"
    center = pts.mean(axis=0)
    distance = np.linalg.norm(pts - center, axis=1)
    radius = np.percentile(distance, 60)
    mask = distance <= max(radius, 1e-12)
    if int(mask.sum()) < 8:
        mask = np.ones(len(pts), dtype=bool)
    normal_vec = np.array(normal, dtype=float)
    normal_norm = float(np.linalg.norm(normal_vec)) or 1.0
    normal_vec = normal_vec / normal_norm
    rhom = rho[mask]
    tempm = temp[mask]
    un = velocities[mask] @ normal_vec
    weights = rhom * un
    denom = float(weights.sum())
    if not math.isfinite(denom) or abs(denom) < 1e-30:
        mixing = None
    else:
        mixing = float((weights * tempm).sum() / denom)
    positive = un > 0.0
    negative = un < 0.0

    def directional_bulk(selector: np.ndarray, sign: float) -> tuple[float | None, float]:
        if not bool(selector.any()):
            return None, 0.0
        flux = rhom[selector] * un[selector] * sign
        total = float(flux.sum())
        if total <= 1e-30:
            return None, 0.0
        return float((flux * tempm[selector]).sum() / total), total

    positive_t, positive_flux = directional_bulk(positive, 1.0)
    negative_t, negative_flux = directional_bulk(negative, -1.0)
    if positive_flux >= negative_flux:
        dominant = "positive_normal"
        forward_t = positive_t
        reverse_flux = negative_flux
        dominant_flux = positive_flux
    else:
        dominant = "negative_normal"
        forward_t = negative_t
        reverse_flux = positive_flux
        dominant_flux = negative_flux
    backflow = reverse_flux / dominant_flux if dominant_flux > 1e-30 else 0.0
    flags: list[str] = []
    if backflow > 0.5:
        flags.append("high_backflow_fraction")
    if cols["T"] < 0:
        flags.append("T_recovered_from_rho")
    return {
        "status": "ok",
        "n_faces": len(pts),
        "n_masked": int(mask.sum()),
        "T_mixing_cup_signed_K": fmt(mixing),
        "T_positive_normal_bulk_K": fmt(positive_t),
        "T_negative_normal_bulk_K": fmt(negative_t),
        "T_forward_dominant_bulk_K": fmt(forward_t),
        "T_simple_K": fmt(float(tempm.mean())),
        "mdot_signed_proxy": fmt(denom),
        "positive_flux_proxy": fmt(positive_flux),
        "negative_flux_proxy_abs": fmt(negative_flux),
        "dominant_flow_direction": dominant,
        "backflow_fraction": fmt(backflow),
        "temperature_selection_rule": f"signed_mixing_cup_and_dominant_forward_kept_separate;{temperature_rule}",
        "quality_flags": ";".join(flags),
    }


def t_from_rho_array(rho: np.ndarray) -> np.ndarray:
    return (2293.6 - rho) / 0.7497


def parse_openfoam_samples(case_dir: Path, time_name: str, source_id: str, case_id: str) -> list[dict[str, Any]]:
    control = write_openfoam_control_dict(case_dir, time_name, source_id, case_id)
    radiation = str(control["radiation_output_term"])
    rows: list[dict[str, Any]] = []
    for plan in build_openfoam_plane_plan(source_id, case_id):
        xy = plane_xy_path(case_dir, time_name, str(plan["plane_label"]))
        base = {
            "case_id": case_id,
            "source_id": source_id,
            "time_s": time_name,
            "plane_label": plan["plane_label"],
            "control_volume": plan["control_volume"],
            "control_volume_group": plan["control_volume_group"],
            "interface_role": plan["interface_role"],
            "span": plan["span"],
            "plane_file": rel(xy) if xy else "",
            "radiation_output_term": radiation,
        }
        if xy is None:
            rows.append({**base, "status": "missing_plane_file"})
            continue
        normal = (float(plan["nx"]), float(plan["ny"]), float(plan["nz"]))
        rows.append({**base, **parse_raw_plane_sample(xy, normal)})
    return rows


def temperature_used(sample: dict[str, Any]) -> tuple[float | None, str, list[str]]:
    status = sample.get("status")
    if status != "ok":
        return None, "unusable_non_ok_sample", [str(status)]
    recirc = safe_float(sample.get("recirculation_ratio")) or 0.0
    flags: list[str] = []
    if recirc > 0.5:
        flags.append("high_recirculation_forward_bulk_used")
        return safe_float(sample.get("T_fwd_bulk_k")), "forward_bulk_when_recirc_gt_0p5_else_mixing_cup", flags
    return safe_float(sample.get("T_bulk_k")), "forward_bulk_when_recirc_gt_0p5_else_mixing_cup", flags


def sample_plane(
    *,
    source_id: str,
    case_id: str,
    recon_case_dir: Path,
    secmean_dir: Path | None,
    physical_segment: str,
    component_span: str,
    interface_role: str,
    station_label: str,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "source_id": source_id,
        "case_id": case_id,
        "recon_case_dir": rel(recon_case_dir),
        "secmean_dir": rel(secmean_dir) if secmean_dir else "",
        "physical_segment": physical_segment,
        "component_span": component_span,
        "interface_role": interface_role,
        "station_label": station_label,
        "plane_file": "",
        "status": "missing_secmean_dir" if secmean_dir is None else "missing_plane_file",
    }
    if secmean_dir is None:
        row["quality_flags"] = "missing_secmean_dir"
        return row
    plane = load_xy_for_station(secmean_dir, component_span, station_index(station_label))
    if plane is None:
        row["quality_flags"] = "missing_plane_file"
        return row
    sample = bulk_t_from_xy(plane)
    used, rule, flags = temperature_used(sample)
    row.update(
        {
            "plane_file": rel(plane),
            "T_bulk_K": fmt(sample.get("T_bulk_k")),
            "T_fwd_bulk_K": fmt(sample.get("T_fwd_bulk_k")),
            "T_simple_K": fmt(sample.get("T_simple_k")),
            "T_used_K": fmt(used),
            "temperature_selection_rule": rule,
            "recirculation_ratio": fmt(sample.get("recirculation_ratio")),
            "mdot_proxy": fmt(sample.get("mdot_proxy")),
            "n_faces": sample.get("n_faces", ""),
            "n_masked": sample.get("n_masked", ""),
            "status": sample.get("status", "missing"),
            "quality_flags": ";".join(flags),
        }
    )
    return row


def build_interface_registry(recon_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in CASES:
        source_id = case["source_id"]
        case_id = case["case_id"]
        for segment in PHYSICAL_SEGMENTS:
            inlet = (
                f"{segment['inlet_span']}:{segment['inlet_station']}"
                if segment["inlet_span"]
                else ""
            )
            outlet = (
                f"{segment['outlet_span']}:{segment['outlet_station']}"
                if segment["outlet_span"]
                else ""
            )
            rows.append(
                {
                    "source_id": source_id,
                    "case_id": case_id,
                    "physical_segment": segment["physical_segment"],
                    "component_spans": "+".join(segment["component_spans"]),
                    "inlet_interface": inlet,
                    "outlet_interface": outlet,
                    "bracket_status": segment["bracket_status"],
                    "fit_use_status": segment["fit_use_status"],
                    "notes": segment["notes"],
                }
            )
    return rows


def build_interface_samples(recon_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in CASES:
        recon_case_dir = recon_root / case["recon_dir_name"]
        secmean_dir = find_secmean_dir(recon_case_dir) if recon_case_dir.is_dir() else None
        for span in RAW_SPANS:
            inlet_station, outlet_station = RAW_SPAN_FLOW[span]
            rows.append(
                sample_plane(
                    source_id=case["source_id"],
                    case_id=case["case_id"],
                    recon_case_dir=recon_case_dir,
                    secmean_dir=secmean_dir,
                    physical_segment=span,
                    component_span=span,
                    interface_role="raw_span_inlet",
                    station_label=inlet_station,
                )
            )
            rows.append(
                sample_plane(
                    source_id=case["source_id"],
                    case_id=case["case_id"],
                    recon_case_dir=recon_case_dir,
                    secmean_dir=secmean_dir,
                    physical_segment=span,
                    component_span=span,
                    interface_role="raw_span_outlet",
                    station_label=outlet_station,
                )
            )
        for segment in PHYSICAL_SEGMENTS:
            if not segment["component_spans"]:
                continue
            rows.append(
                sample_plane(
                    source_id=case["source_id"],
                    case_id=case["case_id"],
                    recon_case_dir=recon_case_dir,
                    secmean_dir=secmean_dir,
                    physical_segment=segment["physical_segment"],
                    component_span=segment["inlet_span"],
                    interface_role="physical_segment_inlet",
                    station_label=segment["inlet_station"],
                )
            )
            rows.append(
                sample_plane(
                    source_id=case["source_id"],
                    case_id=case["case_id"],
                    recon_case_dir=recon_case_dir,
                    secmean_dir=secmean_dir,
                    physical_segment=segment["physical_segment"],
                    component_span=segment["outlet_span"],
                    interface_role="physical_segment_outlet",
                    station_label=segment["outlet_station"],
                )
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_package(recon_root: Path = DEFAULT_RECON_ROOT, output_dir: Path = DEFAULT_OUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = build_interface_registry(recon_root)
    samples = build_interface_samples(recon_root)
    write_csv(output_dir / "interface_registry.csv", registry, REGISTRY_FIELDS)
    write_csv(output_dir / "interface_temperature_samples.csv", samples, SAMPLE_FIELDS)
    ok_samples = [row for row in samples if row.get("status") == "ok"]
    high_recirc = [
        row
        for row in ok_samples
        if (safe_float(row.get("recirculation_ratio")) or 0.0) > 0.5
    ]
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "script": rel(Path(__file__)),
        "recon_root": rel(recon_root),
        "interface_registry_csv": rel(output_dir / "interface_registry.csv"),
        "interface_temperature_samples_csv": rel(output_dir / "interface_temperature_samples.csv"),
        "counts": {
            "registry_rows": len(registry),
            "sample_rows": len(samples),
            "ok_sample_rows": len(ok_samples),
            "high_recirculation_sample_rows": len(high_recirc),
        },
        "temperature_selection_rule": "forward_bulk_when_recirc_gt_0p5_else_mixing_cup",
        "limitations": [
            "Uses existing secmeanSurfaces XY cut planes; no new OpenFOAM sampling is performed.",
            "Cooler and heater patch interiors are not separately bracketed by the available planes.",
            "Junction groups are not enclosed by a single inlet/outlet interface pair.",
            "Upcomer and some downcomer interfaces are recirculation contaminated; forward-only bulk T is diagnostic.",
        ],
    }
    with (output_dir / "interface_temperature_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    return summary


def case_for_source(source_id: str) -> dict[str, Any]:
    for case in MAINLINE_CASES:
        if case["source_id"] == source_id:
            return case
    raise KeyError(source_id)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_all_plane_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in MAINLINE_CASES:
        rows.extend(build_openfoam_plane_plan(str(case["source_id"]), str(case["case_id"])))
    return rows


def write_openfoam_package(output_dir: Path = THERMAL_PACKAGE, tmp_dir: Path = THERMAL_TMP) -> dict[str, Any]:
    scripts = output_dir / "scripts"
    logs = output_dir / "logs"
    outputs = output_dir / "outputs"
    for path in (scripts, logs, outputs, tmp_dir):
        path.mkdir(parents=True, exist_ok=True)
    plan_rows = build_all_plane_rows()
    write_csv(output_dir / "sampling_plane_plan.csv", plan_rows, CONTROL_PLANE_FIELDS)
    target_rows = []
    for case in MAINLINE_CASES:
        target_rows.append(
            {
                "case_id": case["case_id"],
                "source_id": case["source_id"],
                "source_case_root": rel(Path(case["source_case_root"])),
                "existing_recon_dir": rel(Path(case["existing_recon_dir"])),
                "time_s": case["time_s"],
                "task_recon_dir": rel(tmp_dir / "recon" / str(case["source_id"])),
                "output_dir": rel(outputs / str(case["source_id"])),
            }
        )
    write_csv(
        output_dir / "sampling_targets.csv",
        target_rows,
        [
            "case_id",
            "source_id",
            "source_case_root",
            "existing_recon_dir",
            "time_s",
            "task_recon_dir",
            "output_dir",
        ],
    )
    runner = make_openfoam_runner(output_dir, tmp_dir)
    runner_path = scripts / "run_thermal_openfoam_interface_sampling.sh"
    write_text(runner_path, runner)
    runner_path.chmod(0o755)
    sbatch_text = make_sbatch_script(output_dir)
    sbatch_path = scripts / "submit_overnight_thermal_sampling.sbatch"
    write_text(sbatch_path, sbatch_text)
    sbatch_path.chmod(0o755)
    smoke_path = scripts / "run_local_smoke_preflight.sh"
    write_text(
        smoke_path,
        f"""#!/usr/bin/env bash
set -euo pipefail
cd {q(ROOT)}
python3 tools/extract/sample_physical_segment_interface_temperatures.py smoke-local --output-dir {q(output_dir)}
bash -n {q(runner_path)}
bash -n {q(sbatch_path)}
""",
    )
    smoke_path.chmod(0o755)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "task": TASK_ID,
        "output_package": rel(output_dir),
        "tmp_dir": rel(tmp_dir),
        "case_count": len(MAINLINE_CASES),
        "plane_count_per_case": int(len(plan_rows) / len(MAINLINE_CASES)),
        "total_plane_count": len(plan_rows),
        "control_volumes": sorted({row["control_volume"] for row in plan_rows}),
        "source_cases_read_only": True,
        "native_solver_outputs_mutated": False,
        "radiation_policy": "sample qr only if a reconstructed qr field exists; otherwise record absent_no_qr_output",
        "entrypoints": {
            "local_smoke_preflight": rel(smoke_path),
            "runner": rel(runner_path),
            "sbatch": rel(sbatch_path),
        },
    }
    write_text(output_dir / "summary.json", json.dumps(summary, indent=2) + "\n")
    write_text(output_dir / "README.md", make_package_readme(output_dir, tmp_dir, summary))
    return summary


def make_openfoam_runner(output_dir: Path, tmp_dir: Path) -> str:
    case_literals = "\n".join(
        [
            "|".join(
                [
                    str(case["case_id"]),
                    str(case["source_id"]),
                    str(case["source_case_root"]),
                    str(case["existing_recon_dir"]),
                    str(case["time_s"]),
                ]
            )
            for case in MAINLINE_CASES
        ]
    )
    return f"""#!/usr/bin/env bash
set -euo pipefail

ROOT={q(ROOT)}
PACKAGE={q(output_dir)}
TMP_DIR={q(tmp_dir)}
OF_ENV={q(OF_ENV_SCRIPT)}
LOG_DIR="$PACKAGE/logs"
OUTPUT_DIR="$PACKAGE/outputs"
mkdir -p "$LOG_DIR" "$OUTPUT_DIR" "$TMP_DIR/recon"

log() {{
  echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] $*"
}}

die() {{
  echo "ERROR: $*" >&2
  exit 1
}}

assert_ready() {{
  cd "$ROOT"
  bash -lc "source '$OF_ENV' >/dev/null 2>&1 && of13_assert_ready"
}}

prepare_recon() {{
  local case_id="$1"
  local source_id="$2"
  local source_case="$3"
  local existing_recon="$4"
  local time_s="$5"
  local recon_dir="$TMP_DIR/recon/$source_id"

  mkdir -p "$recon_dir"
  if [[ -d "$existing_recon/$time_s" ]]; then
    for name in constant system 0; do
      if [[ ! -e "$recon_dir/$name" ]]; then
        if [[ -e "$existing_recon/$name" ]]; then
          cp -a "$existing_recon/$name" "$recon_dir/$name"
        else
          cp -a "$source_case/$name" "$recon_dir/$name"
        fi
      fi
    done
    if [[ ! -e "$recon_dir/$time_s" ]]; then
      ln -s "$existing_recon/$time_s" "$recon_dir/$time_s"
    fi
  else
    for name in constant system 0; do
      if [[ ! -e "$recon_dir/$name" ]]; then
        cp -a "$source_case/$name" "$recon_dir/$name"
      fi
    done
    if [[ ! -e "$recon_dir/processors64" ]]; then
      ln -s "$source_case/processors64" "$recon_dir/processors64"
    fi
    if [[ ! -d "$recon_dir/$time_s" ]]; then
      log "Reconstructing $source_id at t=$time_s" >&2
      timeout 90m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && reconstructPar -case '$recon_dir' -time '$time_s' -fields '(U T rho p_rgh)'" > "$LOG_DIR/reconstruct_${{source_id}}.log" 2>&1
    fi
  fi
  rm -f "$recon_dir/system/functions"
  printf '%s\\n' "$recon_dir"
}}

run_case() {{
  local case_id="$1"
  local source_id="$2"
  local source_case="$3"
  local existing_recon="$4"
  local time_s="$5"
  local recon_dir
  recon_dir="$(prepare_recon "$case_id" "$source_id" "$source_case" "$existing_recon" "$time_s")"
  local out_dir="$OUTPUT_DIR/$source_id"
  mkdir -p "$out_dir"
  log "Writing controlDict for $source_id"
  python3 "$ROOT/tools/extract/sample_physical_segment_interface_temperatures.py" write-control-dict \\
    --case-dir "$recon_dir" --time "$time_s" --source-id "$source_id" --case-id "$case_id" \\
    > "$out_dir/control_dict_summary.json"
  log "Running foamPostProcess for $source_id"
  timeout 90m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && foamPostProcess -case '$recon_dir' -time '$time_s'" \\
    > "$LOG_DIR/foamPostProcess_${{source_id}}.log" 2>&1
  log "Parsing samples for $source_id"
  python3 "$ROOT/tools/extract/sample_physical_segment_interface_temperatures.py" parse-openfoam-samples \\
    --case-dir "$recon_dir" --time "$time_s" --source-id "$source_id" --case-id "$case_id" --output-dir "$out_dir"
}}

mode="${{1:-overnight}}"
assert_ready
case "$mode" in
  preflight)
    while IFS='|' read -r case_id source_id source_case existing_recon time_s; do
      [[ -n "$case_id" ]] || continue
      [[ -d "$source_case" ]] || die "missing source case $source_case"
      [[ -d "$existing_recon/$time_s" || -d "$source_case/processors64/$time_s" ]] || die "missing reconstructed or processor time for $source_id t=$time_s"
      [[ -f "$ROOT/work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines/$source_id/mesh_stations.json" ]] || die "missing mesh stations for $source_id"
    done <<'CASES'
{case_literals}
CASES
    ;;
  smoke)
    read -r case_id source_id source_case existing_recon time_s <<'CASE'
{case_literals.splitlines()[0]}
CASE
    run_case "$case_id" "$source_id" "$source_case" "$existing_recon" "$time_s"
    ;;
  overnight)
    while IFS='|' read -r case_id source_id source_case existing_recon time_s; do
      [[ -n "$case_id" ]] || continue
      run_case "$case_id" "$source_id" "$source_case" "$existing_recon" "$time_s"
    done <<'CASES'
{case_literals}
CASES
    ;;
  *)
    die "unknown mode $mode"
    ;;
esac
log "thermal interface sampling complete mode=$mode"
"""


def make_sbatch_script(output_dir: Path) -> str:
    runner = output_dir / "scripts/run_thermal_openfoam_interface_sampling.sh"
    log_dir = output_dir / "logs"
    return f"""#!/usr/bin/env bash
#SBATCH -J th_ofsamp
#SBATCH -A ASC23046
#SBATCH -p NuclearEnergy
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 64
#SBATCH -t 08:00:00
#SBATCH -o {log_dir}/slurm_%j.out
#SBATCH -e {log_dir}/slurm_%j.err

set -euo pipefail
cd {q(ROOT)}
mkdir -p {q(log_dir)}
srun -N1 -n1 -c64 bash {q(runner)} overnight
"""


def make_package_readme(output_dir: Path, tmp_dir: Path, summary: dict[str, Any]) -> str:
    return f"""# Thermal OpenFOAM Interface Sampling

Generated: `{datetime.now().astimezone().isoformat(timespec="seconds")}`
Task: `{TASK_ID}`

## Scope

This package prepares and launches a bounded compute-node OpenFOAM sampling run
for admitted Salt 2/3/4 Jin mainline cases. Source case trees remain read-only.
Task-local reconstructed mirrors and postProcessing outputs live under
`{rel(tmp_dir)}` and `{rel(output_dir)}`.

## Sampling Targets

- heater interior: bracketed inside the lower leg around
  `pipeleg_lower_04_straight` through `pipeleg_lower_06_straight`
- cooler/reducer interior: bracketed inside the upper leg around
  `pipeleg_upper_06_reducer`, `pipeleg_upper_05_cooler`, and
  `pipeleg_upper_04_reducer`
- junction control volumes: lower-left, lower-right, upper-right, upper-left,
  and test-section lower/upper junction faces

## Outputs

- `sampling_plane_plan.csv`: generated OpenFOAM plane geometry and provenance.
- `sampling_targets.csv`: case roots, retained times, reconstructed mirrors,
  and output directories.
- `scripts/run_local_smoke_preflight.sh`: login-safe smoke/preflight.
- `scripts/run_thermal_openfoam_interface_sampling.sh`: compute-node driver.
- `scripts/submit_overnight_thermal_sampling.sbatch`: bounded overnight Slurm
  wrapper.
- `outputs/<source_id>/openfoam_interface_samples.csv`: written after the
  compute-node job samples and parses each case.

## Semantics

The parser preserves both signed mixing-cup and dominant forward-flow bulk
temperatures. Backflow is reported as a fraction of the dominant directional
flux at each plane. Radiation is not inferred from emissivity; `qr` is sampled
only if OpenFOAM exposes a reconstructed `qr` field, otherwise rows carry
`absent_no_qr_output`.

## Counts

- Cases: `{summary["case_count"]}`
- Planes per case: `{summary["plane_count_per_case"]}`
- Total planned planes: `{summary["total_plane_count"]}`
"""


def run_local_smoke(output_dir: Path = THERMAL_PACKAGE) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = write_openfoam_package(output_dir, THERMAL_TMP)
    smoke_rows: list[dict[str, Any]] = []
    case = MAINLINE_CASES[0]
    secmean = Path(case["existing_recon_dir"]) / "postProcessing/secmeanSurfaces" / str(case["time_s"])
    samples = [
        ("lower_leg__s01", "heater_smoke_inlet_proxy"),
        ("lower_leg__s03", "heater_smoke_outlet_proxy"),
        ("upper_leg__s01", "cooler_smoke_inlet_proxy"),
        ("upper_leg__s03", "cooler_smoke_outlet_proxy"),
        ("right_leg__s00", "junction_smoke_proxy"),
    ]
    station_lookup = {
        station["label"]: station
        for station in load_mesh_payload(str(case["source_id"])).get("stations", [])
    }
    for label, role in samples:
        xy = secmean / f"plane_{label}.xy"
        station = station_lookup[label]
        parsed = parse_raw_plane_sample(
            xy,
            (float(station["nx"]), float(station["ny"]), float(station["nz"])),
        )
        smoke_rows.append(
            {
                "case_id": case["case_id"],
                "source_id": case["source_id"],
                "time_s": case["time_s"],
                "plane_label": label,
                "control_volume": role,
                "control_volume_group": "local_smoke_existing_secmean",
                "interface_role": role,
                "span": station["span"],
                "plane_file": rel(xy),
                "radiation_output_term": "absent_no_qr_output",
                **parsed,
            }
        )
    write_csv(output_dir / "local_smoke_existing_secmean_samples.csv", smoke_rows, OPENFOAM_SAMPLE_FIELDS)
    smoke_summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "smoke_type": "login_safe_existing_secmean_parser_smoke",
        "openfoam_run_on_login": False,
        "source": rel(secmean),
        "sample_rows": len(smoke_rows),
        "ok_rows": sum(1 for row in smoke_rows if row.get("status") == "ok"),
        "package_summary": summary,
    }
    write_text(output_dir / "local_smoke_summary.json", json.dumps(smoke_summary, indent=2) + "\n")
    return smoke_summary


def command_write_control_dict(args: argparse.Namespace) -> None:
    summary = write_openfoam_control_dict(
        Path(args.case_dir),
        str(args.time),
        str(args.source_id),
        str(args.case_id),
    )
    print(json.dumps(summary, indent=2))


def command_parse_openfoam_samples(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = parse_openfoam_samples(
        Path(args.case_dir),
        str(args.time),
        str(args.source_id),
        str(args.case_id),
    )
    write_csv(output_dir / "openfoam_interface_samples.csv", rows, OPENFOAM_SAMPLE_FIELDS)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "case_id": args.case_id,
        "source_id": args.source_id,
        "time_s": args.time,
        "sample_rows": len(rows),
        "ok_rows": sum(1 for row in rows if row.get("status") == "ok"),
        "missing_rows": sum(1 for row in rows if row.get("status") != "ok"),
        "radiation_output_terms": sorted({str(row.get("radiation_output_term", "")) for row in rows}),
    }
    write_text(output_dir / "openfoam_interface_samples_summary.json", json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    legacy = sub.add_parser("legacy-package", help="Rebuild the July 8 existing-secmean package.")
    legacy.add_argument("--recon-root", default=str(DEFAULT_RECON_ROOT))
    legacy.add_argument("--output-dir", default=str(DEFAULT_OUT))
    build = sub.add_parser("build-openfoam-package", help="Write the July 9 OpenFOAM sampling package.")
    build.add_argument("--output-dir", default=str(THERMAL_PACKAGE))
    build.add_argument("--tmp-dir", default=str(THERMAL_TMP))
    smoke = sub.add_parser("smoke-local", help="Run login-safe preflight/parser smoke without OpenFOAM.")
    smoke.add_argument("--output-dir", default=str(THERMAL_PACKAGE))
    write_cd = sub.add_parser("write-control-dict", help="Write the OpenFOAM controlDict for one case.")
    write_cd.add_argument("--case-dir", required=True)
    write_cd.add_argument("--time", required=True)
    write_cd.add_argument("--source-id", required=True)
    write_cd.add_argument("--case-id", required=True)
    parse_samples = sub.add_parser("parse-openfoam-samples", help="Parse sampled OpenFOAM raw plane files.")
    parse_samples.add_argument("--case-dir", required=True)
    parse_samples.add_argument("--time", required=True)
    parse_samples.add_argument("--source-id", required=True)
    parse_samples.add_argument("--case-id", required=True)
    parse_samples.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    if args.command == "build-openfoam-package":
        print(json.dumps(write_openfoam_package(Path(args.output_dir), Path(args.tmp_dir)), indent=2))
    elif args.command == "smoke-local":
        print(json.dumps(run_local_smoke(Path(args.output_dir)), indent=2))
    elif args.command == "write-control-dict":
        command_write_control_dict(args)
    elif args.command == "parse-openfoam-samples":
        command_parse_openfoam_samples(args)
    else:
        recon_root = Path(getattr(args, "recon_root", DEFAULT_RECON_ROOT))
        output_dir = Path(getattr(args, "output_dir", DEFAULT_OUT))
        summary = build_package(recon_root, output_dir)
        print(json.dumps(summary["counts"], indent=2))


if __name__ == "__main__":
    main()
