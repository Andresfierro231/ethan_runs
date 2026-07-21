#!/usr/bin/env python3
"""Plan and parse matched upcomer inlet/mid/outlet plane metrics.

This tool is intentionally split into two evidence lanes:

* existing postprocessing lane: parse diagnostic proxies from already present
  ``secmeanSurfaces`` and ``convcellSurfaces`` raw plane files.
* compute-node lane: write an exact OpenFOAM sampling plan for admission-grade
  matched vector + thermal planes. It does not run OpenFOAM on the login node.

Existing raw cutting-plane files do not carry face areas or station-band wall
face fields, so their rows stay diagnostic until a compute-node sampling pass
adds the missing face-area-weighted and wall-band quantities.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shlex
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.case_analysis_profiles import get_case_analysis_profile

TASK_ID = "AGENT-341"
COMPUTE_TASK_ID = "AGENT-344"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan"
COMPUTE_PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction"
COMPUTE_TMP_DIR = ROOT / "tmp/2026-07-14_upcomer_matched_plane_compute_extraction"
CONTRACT_DIR = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract"
CANDIDATE_CASES = (
    ROOT
    / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory"
    / "upcomer_onset_candidate_cases.csv"
)
MESH_CENTERLINE_ROOT = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
DEFAULT_RECON_ROOT = ROOT / "tmp/2026-06-30_claude_action_items"
FO_SAMPLE_NAME = "upcomerMatchedPlaneSurfaces"
FO_WALL_BAND_NAME = "upcomerMatchedWallBandSurfaces"
OF_ENV_SCRIPT = ROOT / "tools/ofenv/of13_env.sh"
CORRECTED_Q_HARVEST_JOBS = {
    "salt2_lo5q": "3295437",
    "salt2_hi5q": "3295437",
    "salt4_lo5q": "3295437",
    "salt4_hi5q": "3295437",
    "salt2_lo10q": "3295438",
    "salt2_hi10q": "3295438",
    "salt4_lo10q": "3295438",
    "salt4_hi10q": "3295438",
}
CORRECTED_Q_GEOMETRY_SOURCE_IDS = {
    "salt2_jin_lo5q_corrected": "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "salt2_jin_hi5q_corrected": "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "salt2_jin_lo10q_corrected": "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "salt2_jin_hi10q_corrected": "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "salt4_jin_lo5q_corrected": "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "salt4_jin_hi5q_corrected": "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "salt4_jin_lo10q_corrected": "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "salt4_jin_hi10q_corrected": "viscosity_screening_salt_test_4_jin_coarse_mesh",
}
PM10_TERMINAL_DRIFT = (
    ROOT
    / "work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification"
    / "pm10_terminal_drift.csv"
)
PLANE_SPECS = [
    ("upcomer_inlet", "left_lower_leg", "s00"),
    ("upcomer_mid", "test_section_span", "s02"),
    ("upcomer_outlet", "left_upper_leg", "s04"),
]
MAINLINE_RECON = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": (DEFAULT_RECON_ROOT / "recon_salt2_of13", "7915"),
    "viscosity_screening_salt_test_3_jin_coarse_mesh": (DEFAULT_RECON_ROOT / "recon_salt3_of13", "7618"),
    "viscosity_screening_salt_test_4_jin_coarse_mesh": (DEFAULT_RECON_ROOT / "recon_salt4_of13", "10000"),
}
SOURCE_TO_CASE_ID = {
    "viscosity_screening_salt_test_1_jin_coarse_mesh": "salt_1",
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "salt_2",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "salt_3",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "salt_4",
}
MAINLINE_SOURCE_CASES = {
    "viscosity_screening_salt_test_2_jin_coarse_mesh": ROOT
    / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": ROOT
    / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": ROOT
    / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
}
MESH_FAMILY_ROWS = [
    {
        "case_key": "salt2_mesh_coarse_repair_smoke",
        "mesh_level": "coarse",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "recon_case_dir": ROOT
        / "work_products/2026-07/2026-07-13/2026-07-13_salt2_coarse_thermal_repair_smoke"
        / "recon/coarse_cwd_controlDict_collated_split_full",
        "time_s": "2431",
        "current_use": "diagnostic_repair_smoke_only",
    },
    {
        "case_key": "salt2_mesh_medium_repair_smoke",
        "mesh_level": "medium",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "recon_case_dir": ROOT
        / "work_products/2026-07/2026-07-13/2026-07-13_reconstructed_t_repair_trial"
        / "recon/medium_cwd_controlDict_collated_split_full",
        "time_s": "518",
        "current_use": "diagnostic_repair_smoke_only",
    },
    {
        "case_key": "salt2_mesh_fine_repair_smoke",
        "mesh_level": "fine",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "recon_case_dir": ROOT
        / "work_products/2026-07/2026-07-13/2026-07-13_salt2_fine_reconstructed_t_repair_plan_sbatch"
        / "repair_trial_output/recon/fine_cwd_controlDict_collated_split_full",
        "time_s": "399",
        "current_use": "diagnostic_repair_smoke_only",
    },
]

PLAN_FIELDS = [
    "case_key",
    "source_id",
    "case_role",
    "plane_location",
    "span",
    "station_label",
    "time_start_s",
    "time_end_s",
    "representative_time_s",
    "recon_case_dir",
    "mesh_stations_path",
    "x",
    "y",
    "z",
    "nx",
    "ny",
    "nz",
    "bore_m",
    "existing_secmean_plane_file",
    "existing_convcell_plane_file",
    "existing_metric_status",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "bulk_T_K",
    "wall_T_K",
    "wallHeatFlux_W_m2",
    "Re",
    "Pr",
    "Ri",
    "Gr",
    "Ra",
    "Gz",
    "source_paths",
    "compute_requirement",
    "admission_status",
    "notes",
]
COMPUTE_FIELDS = [
    "case_key",
    "source_id",
    "case_role",
    "plane_location",
    "span",
    "station_label",
    "representative_time_s",
    "sampled_plane_file",
    "sampled_wall_file",
    "metric_status",
    "face_count",
    "wall_face_count",
    "reverse_area_fraction",
    "reverse_mass_fraction",
    "secondary_velocity_fraction",
    "bulk_T_K",
    "bulk_T_rule",
    "wall_T_K",
    "wallHeatFlux_W_m2",
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
CANDIDATE_READINESS_FIELDS = [
    "case_key",
    "source_id",
    "salt_number",
    "variant",
    "candidate_role",
    "availability_status",
    "run_state",
    "admission_verdict",
    "compute_readiness",
    "blocking_reason",
    "source_case_dir",
    "existing_recon_dir",
    "representative_time_s",
    "dependency_job_id",
    "source_paths",
]


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


def rel(path: Path | None) -> str:
    return relative_to_workspace(path) if path else ""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def geometry_source_id(source_id: str) -> str:
    return CORRECTED_Q_GEOMETRY_SOURCE_IDS.get(source_id, source_id)


def mesh_stations_path(source_id: str) -> Path:
    return MESH_CENTERLINE_ROOT / geometry_source_id(source_id) / "mesh_stations.json"


def load_station(source_id: str, span: str, station_suffix: str) -> dict[str, Any] | None:
    path = mesh_stations_path(source_id)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    label = f"{span}__{station_suffix}"
    for station in payload.get("stations", []):
        if station.get("label") == label:
            return station
    return None


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= 0.0:
        raise ValueError("zero-length normal")
    return vector / norm


def t_from_rho(rho: np.ndarray) -> np.ndarray:
    return (2293.6 - rho) / 0.7497


def temperature_from_fields(t_values: np.ndarray | None, rho_values: np.ndarray | None) -> tuple[np.ndarray, str]:
    if t_values is not None:
        temp = np.asarray(t_values, dtype=float)
        plausible = np.isfinite(temp) & (temp >= 250.0) & (temp <= 1500.0)
        if temp.size and int(np.sum(plausible)) == temp.size:
            return temp, "sampled_T"
    if rho_values is None:
        raise ValueError("missing T and rho for temperature")
    rho = np.asarray(rho_values, dtype=float)
    temp = t_from_rho(rho)
    plausible = np.isfinite(temp) & (temp >= 250.0) & (temp <= 1500.0)
    if not temp.size or int(np.sum(plausible)) != temp.size:
        raise ValueError("rho-derived temperature is not finite/plausible")
    return temp, "T_from_rho_linear_eos"


def use_rho_temperature_fallback(case_key: str) -> bool:
    return case_key in {"salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"}


def resolve_thermal_columns(data: np.ndarray) -> dict[str, int]:
    """Resolve raw columns after x y z Ux Uy Uz.

    Accepted layouts:
    - secmeanSurfaces: x y z Ux Uy Uz p_rgh rho
    - thermal surfaces: x y z Ux Uy Uz T rho p_rgh
    - older augmented: x y z Ux Uy Uz p_rgh rho T
    """
    if data.shape[1] < 8:
        raise ValueError(f"need at least 8 columns, got {data.shape[1]}")
    if data.shape[1] >= 9:
        med6 = float(np.median(data[:, 6]))
        med7 = float(np.median(data[:, 7]))
        med8 = float(np.median(data[:, 8]))
        if 250.0 <= med6 <= 1500.0 and 1000.0 <= med7 <= 2600.0:
            return {"T": 6, "rho": 7}
        if 1000.0 <= med7 <= 2600.0 and 250.0 <= med8 <= 1500.0:
            return {"T": 8, "rho": 7}
    return {"T": -1, "rho": 7}


def load_xy(path: Path) -> np.ndarray:
    data = np.loadtxt(path, comments="#")
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return data


def parse_secmean_plane(path: Path, normal: np.ndarray) -> dict[str, float | str]:
    data = load_xy(path)
    cols = resolve_thermal_columns(data)
    velocities = data[:, 3:6]
    rho = data[:, cols["rho"]]
    temp = data[:, cols["T"]] if cols["T"] >= 0 else t_from_rho(rho)
    un = velocities @ normal
    area = np.ones_like(un)
    reverse = un < 0.0
    abs_flux = np.abs(rho * un) * area
    reverse_flux = np.maximum(-rho * un, 0.0) * area
    signed_flux = rho * un * area
    forward_flux = np.maximum(rho * un, 0.0) * area
    speed2 = np.sum(velocities * velocities, axis=1)
    tangential = velocities - np.outer(un, normal)
    secondary2 = np.sum(tangential * tangential, axis=1)
    signed_denom = float(np.sum(signed_flux))
    forward_denom = float(np.sum(forward_flux))
    return {
        "reverse_area_fraction": float(np.mean(reverse)),
        "reverse_mass_fraction": float(np.sum(reverse_flux) / max(float(np.sum(abs_flux)), 1e-300)),
        "secondary_velocity_fraction": float(
            math.sqrt(float(np.mean(secondary2))) / max(math.sqrt(float(np.mean(speed2))), 1e-300)
        ),
        "bulk_T_K": float(np.sum(signed_flux * temp) / signed_denom) if abs(signed_denom) > 1e-300 else math.nan,
        "forward_bulk_T_K": float(np.sum(forward_flux * temp) / forward_denom) if forward_denom > 1e-300 else math.nan,
        "source_column_rule": "raw_T" if cols["T"] >= 0 else "T_from_rho_linear_eos",
        "weighting": "equal_face_area_proxy_not_admission_grade",
    }


def parse_convcell_plane(path: Path, normal: np.ndarray) -> dict[str, float | str]:
    data = load_xy(path)
    if data.shape[1] < 11:
        raise ValueError(f"convcell raw plane needs 11 columns, got {data.shape[1]}")
    velocities = data[:, 3:6]
    un = velocities @ normal
    speed2 = np.sum(velocities * velocities, axis=1)
    tangential = velocities - np.outer(un, normal)
    secondary2 = np.sum(tangential * tangential, axis=1)
    return {
        "reverse_area_fraction": float(np.mean(un < 0.0)),
        "secondary_velocity_fraction": float(
            math.sqrt(float(np.mean(secondary2))) / max(math.sqrt(float(np.mean(speed2))), 1e-300)
        ),
        "Ra": float(np.median(data[:, 6])),
        "Ri": float(np.median(data[:, 7])),
        "Gr": float(np.median(data[:, 8])),
        "Re": float(np.median(data[:, 9])),
        "Pr": float(np.median(data[:, 10])),
        "weighting": "equal_face_area_proxy_not_admission_grade",
    }


def plane_file(case_dir: Path, fo_name: str, time_s: str, span: str, station_suffix: str) -> Path | None:
    label = f"plane_{span}__{station_suffix}.xy"
    direct = case_dir / "postProcessing" / fo_name / time_s / label
    if direct.exists():
        return direct
    base = case_dir / "postProcessing" / fo_name
    if base.exists():
        hits = sorted(base.glob(f"**/{label}"))
        if hits:
            return hits[-1]
    return None


def gz_from_station(re_value: float, pr_value: float, dh_m: float, length_m: float) -> float:
    if length_m <= 0.0:
        return math.nan
    return float(re_value * pr_value * dh_m / length_m)


def station_length_from_upcomer_inlet(source_id: str, plane_location: str) -> float:
    if plane_location == "upcomer_inlet":
        return 0.0
    # Conservative geometry contract for this package: mid is halfway through
    # the composite upcomer and outlet is the full composite. Admission work can
    # replace this with exact cumulative arc-length in a compute package.
    path = mesh_stations_path(source_id)
    if not path.exists():
        return math.nan
    payload = json.loads(path.read_text(encoding="utf-8"))
    lengths: dict[str, float] = {}
    for span in ("left_lower_leg", "test_section_span", "left_upper_leg"):
        pts = [
            np.array([float(s["x"]), float(s["y"]), float(s["z"])])
            for s in payload.get("stations", [])
            if s.get("span") == span
        ]
        total = 0.0
        for i in range(1, len(pts)):
            total += float(np.linalg.norm(pts[i] - pts[i - 1]))
        lengths[span] = total
    full = lengths.get("left_lower_leg", 0.0) + lengths.get("test_section_span", 0.0) + lengths.get("left_upper_leg", 0.0)
    return full * 0.5 if plane_location == "upcomer_mid" else full


def case_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(CANDIDATE_CASES):
        source_id = row["source_id"]
        if source_id in MAINLINE_RECON:
            recon, time_s = MAINLINE_RECON[source_id]
            rows.append(
                {
                    "case_key": row["case_key"],
                    "source_id": source_id,
                    "case_role": row.get("admission_verdict", ""),
                    "recon_case_dir": recon,
                    "time_s": time_s,
                    "candidate_status": row.get("availability_status", ""),
                    "source_paths": ";".join(
                        p
                        for p in [
                            row.get("source_path", ""),
                            row.get("case_stage_path", ""),
                            row.get("evidence_path", ""),
                            str(CONTRACT_DIR / "upcomer_extraction_contract.csv"),
                        ]
                        if p
                    ),
                }
            )
        elif row["case_key"] in CORRECTED_Q_HARVEST_JOBS and representative_time_for_case(row):
            rows.append(
                {
                    "case_key": row["case_key"],
                    "source_id": source_id,
                    "case_role": row.get("admission_verdict", ""),
                    "recon_case_dir": None,
                    "source_case_dir": source_case_path(row),
                    "time_s": representative_time_for_case(row),
                    "candidate_status": row.get("availability_status", ""),
                    "source_paths": ";".join(
                        p
                        for p in [
                            row.get("source_path", ""),
                            row.get("case_stage_path", ""),
                            row.get("evidence_path", ""),
                            str(PM10_TERMINAL_DRIFT),
                            str(CONTRACT_DIR / "upcomer_extraction_contract.csv"),
                        ]
                        if p
                    ),
                }
            )
        elif row.get("candidate_onset_role") in {"transition_candidate", "ordinary_pipe_anchor"}:
            rows.append(
                {
                    "case_key": row["case_key"],
                    "source_id": source_id,
                    "case_role": row.get("admission_verdict", ""),
                    "recon_case_dir": None,
                    "time_s": "",
                    "candidate_status": row.get("availability_status", ""),
                    "source_paths": ";".join(
                        p for p in [row.get("case_stage_path", ""), row.get("evidence_path", "")] if p
                    ),
                }
            )
    return rows


def build_plan_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows():
        for plane_location, span, station_suffix in PLANE_SPECS:
            source_id = str(case["source_id"])
            station = load_station(source_id, span, station_suffix)
            normal = None
            if station is not None:
                normal = normalize(np.array([float(station["nx"]), float(station["ny"]), float(station["nz"])]))
            recon = case.get("recon_case_dir")
            time_s = str(case.get("time_s") or "")
            secmean = plane_file(recon, "secmeanSurfaces", time_s, span, station_suffix) if isinstance(recon, Path) else None
            convcell = plane_file(recon, "convcellSurfaces", time_s, span, station_suffix) if isinstance(recon, Path) else None
            parsed: dict[str, Any] = {}
            status_parts: list[str] = []
            if normal is None:
                status_parts.append("missing_mesh_station")
            if secmean is not None and normal is not None:
                try:
                    parsed.update(parse_secmean_plane(secmean, normal))
                    status_parts.append("diagnostic_secmean_proxy_available")
                except Exception as exc:  # noqa: BLE001
                    status_parts.append(f"secmean_parse_failed:{exc}")
            if convcell is not None and normal is not None:
                try:
                    conv = parse_convcell_plane(convcell, normal)
                    for key in ("Re", "Pr", "Ri", "Gr", "Ra"):
                        parsed[key] = conv.get(key, parsed.get(key, math.nan))
                    parsed.setdefault("reverse_area_fraction", conv.get("reverse_area_fraction"))
                    parsed.setdefault("secondary_velocity_fraction", conv.get("secondary_velocity_fraction"))
                    status_parts.append("diagnostic_convcell_nondim_available")
                except Exception as exc:  # noqa: BLE001
                    status_parts.append(f"convcell_parse_failed:{exc}")
            if not status_parts:
                status_parts.append("no_existing_matched_plane_postprocessing")
            dh_m = float(station.get("bore_m", math.nan)) if station else math.nan
            length_m = station_length_from_upcomer_inlet(source_id, plane_location)
            if plane_location == "upcomer_inlet":
                gz = "not_applicable_zero_entry_length"
            else:
                gz = fmt(gz_from_station(float(parsed.get("Re", math.nan)), float(parsed.get("Pr", math.nan)), dh_m, length_m))
            rows.append(
                {
                    "case_key": case["case_key"],
                    "source_id": source_id,
                    "case_role": case["case_role"],
                    "plane_location": plane_location,
                    "span": span,
                    "station_label": f"{span}__{station_suffix}",
                    "time_start_s": time_s,
                    "time_end_s": time_s,
                    "representative_time_s": time_s,
                    "recon_case_dir": rel(recon) if isinstance(recon, Path) else "",
                    "mesh_stations_path": rel(mesh_stations_path(source_id)) if mesh_stations_path(source_id).exists() else "",
                    "x": fmt(station.get("x") if station else None),
                    "y": fmt(station.get("y") if station else None),
                    "z": fmt(station.get("z") if station else None),
                    "nx": fmt(station.get("nx") if station else None),
                    "ny": fmt(station.get("ny") if station else None),
                    "nz": fmt(station.get("nz") if station else None),
                    "bore_m": fmt(station.get("bore_m") if station else None),
                    "existing_secmean_plane_file": rel(secmean),
                    "existing_convcell_plane_file": rel(convcell),
                    "existing_metric_status": ";".join(status_parts),
                    "reverse_area_fraction": fmt(parsed.get("reverse_area_fraction")),
                    "reverse_mass_fraction": fmt(parsed.get("reverse_mass_fraction")),
                    "secondary_velocity_fraction": fmt(parsed.get("secondary_velocity_fraction")),
                    "bulk_T_K": fmt(parsed.get("bulk_T_K")),
                    "wall_T_K": "",
                    "wallHeatFlux_W_m2": "",
                    "Re": fmt(parsed.get("Re")),
                    "Pr": fmt(parsed.get("Pr")),
                    "Ri": fmt(parsed.get("Ri")),
                    "Gr": fmt(parsed.get("Gr")),
                    "Ra": fmt(parsed.get("Ra")),
                    "Gz": gz,
                    "source_paths": case["source_paths"],
                    "compute_requirement": (
                        "compute_node_required_for_admission_grade_face_area_wall_band_sampling"
                        if isinstance(recon, Path)
                        else (
                            "compute_node_required_reconstruct_corrected_q_processor_frame_for_admission_grade_sampling"
                            if case.get("source_case_dir") and time_s
                            else "case_not_terminal_or_not_staged; wait for admission/harvest before sampling"
                        )
                    ),
                    "admission_status": "diagnostic_only_existing_proxy; fit_not_admissible",
                    "notes": (
                        "Existing raw planes lack face areas and matched wall station bands; "
                        "wall_T and wallHeatFlux require compute-node OpenFOAM sampling."
                    ),
                }
            )
    return rows


def build_mesh_repeat_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in MESH_FAMILY_ROWS:
        recon = Path(case["recon_case_dir"])
        available = recon.exists()
        for plane_location, span, station_suffix in PLANE_SPECS:
            secmean = plane_file(recon, "secmeanSurfaces", str(case["time_s"]), span, station_suffix) if available else None
            rows.append(
                {
                    "case_key": case["case_key"],
                    "source_id": case["source_id"],
                    "mesh_level": case["mesh_level"],
                    "plane_location": plane_location,
                    "span": span,
                    "station_label": f"{span}__{station_suffix}",
                    "representative_time_s": case["time_s"],
                    "recon_case_dir": rel(recon),
                    "existing_secmean_plane_file": rel(secmean),
                    "current_use": case["current_use"],
                    "repeat_status": "diagnostic_proxy_available" if secmean else "needs_compute_node_sampling",
                    "required_repeat_metrics": (
                        "reverse_area_fraction,reverse_mass_fraction,secondary_velocity_fraction,"
                        "bulk_T,wall_T,wallHeatFlux,Re,Pr,Ri,Gr,Ra,Gz"
                    ),
                    "admission_gate": (
                        "Do not compute GCI until all three mesh levels have the same admitted metric, "
                        "same sign/radiation semantics, and monotone triplet behavior."
                    ),
                    "source_paths": (
                        "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/"
                        "refreshed_qoi_mesh_gate_status.csv"
                    ),
                }
            )
    return rows


def q(value: str | Path) -> str:
    return shlex.quote(str(value))


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


def source_case_path(row: dict[str, str]) -> Path | None:
    for key in ("case_stage_path", "source_path"):
        raw = row.get(key, "").strip()
        if raw and not raw.startswith("planned "):
            return Path(raw) if Path(raw).is_absolute() else ROOT / raw
    return None


def is_pm10_completed_case(case_key: str) -> bool:
    if case_key not in {"salt2_lo10q", "salt2_hi10q", "salt4_lo10q", "salt4_hi10q"}:
        return False
    if not PM10_TERMINAL_DRIFT.exists():
        return False
    drift_rows = {item.get("case_key", ""): item for item in read_csv(PM10_TERMINAL_DRIFT)}
    drift = drift_rows.get(case_key)
    return bool(drift and drift.get("terminal_drift_status") == "pass" and drift.get("harvest_job_id") == "3295438")


def representative_time_for_case(row: dict[str, str]) -> str:
    source_id = row["source_id"]
    if source_id in MAINLINE_RECON:
        return MAINLINE_RECON[source_id][1]
    if PM10_TERMINAL_DRIFT.exists():
        drift_rows = {item.get("case_key", ""): item for item in read_csv(PM10_TERMINAL_DRIFT)}
        drift = drift_rows.get(row.get("case_key", ""))
        if drift and drift.get("terminal_drift_status") == "pass":
            match = re.search(r"[-+]?\d+(?:\.\d+)?", drift.get("latest_registered_timestep", ""))
            if match:
                return str(int(float(match.group(0))))
    return ""


def readiness_for_candidate(row: dict[str, str]) -> dict[str, str]:
    case_key = row["case_key"]
    source_id = row["source_id"]
    source_case = source_case_path(row)
    existing_recon, existing_time = MAINLINE_RECON.get(source_id, (None, ""))
    pm10_completed = is_pm10_completed_case(case_key) and bool(representative_time_for_case(row))
    readiness = "blocked-not-runnable"
    reason = "not_terminal_or_not_staged"
    dep = ""
    if row.get("variant") == "mesh-level" or "mesh_refinement_family" in case_key:
        readiness = "blocked-mesh-repeat-plan"
        reason = "handled_by_mesh_family_repeat_status_not_nominal_case_sampling"
    elif source_id in MAINLINE_RECON and existing_recon is not None and (existing_recon / existing_time).exists():
        readiness = "runnable-now"
        reason = "existing_reconstructed_terminal_case"
    elif pm10_completed:
        readiness = "runnable-now"
        reason = "completed_pm10_harvest_processor_frame_available"
    elif case_key in CORRECTED_Q_HARVEST_JOBS:
        readiness = "dependency-gated"
        dep = CORRECTED_Q_HARVEST_JOBS[case_key]
        reason = f"wait_for_corrected_q_harvest_job_{dep}"
    elif row.get("source_id", "").startswith("planned_") or row.get("run_state") == "not_launched":
        readiness = "blocked-new-cfd-run"
        reason = "no_case_directory_targeted_re_campaign_required"
    elif "salt1" in case_key:
        readiness = "blocked-policy"
        reason = "salt1_policy_and_quasi_steady_gate_not_admitted"
    elif row.get("run_state") == "failed":
        readiness = "blocked-failed-run"
        reason = "failed_corrected_q_row_requires_cause_documentation_before_rerun"
    return {
        "case_key": case_key,
        "source_id": source_id,
        "salt_number": row.get("salt_number", ""),
        "variant": row.get("variant", ""),
        "candidate_role": row.get("candidate_onset_role", ""),
        "availability_status": "available now" if pm10_completed else row.get("availability_status", ""),
        "run_state": "completed" if pm10_completed else row.get("run_state", ""),
        "admission_verdict": (
            "terminal-holdout-scoring"
            if pm10_completed
            else row.get("admission_verdict", "")
        ),
        "compute_readiness": readiness,
        "blocking_reason": reason,
        "source_case_dir": rel(source_case) if source_case else "",
        "existing_recon_dir": rel(existing_recon) if isinstance(existing_recon, Path) else "",
        "representative_time_s": representative_time_for_case(row),
        "dependency_job_id": dep,
        "source_paths": ";".join(
            p
            for p in [
                row.get("source_path", ""),
                row.get("case_stage_path", ""),
                row.get("evidence_path", ""),
                str(PM10_TERMINAL_DRIFT) if is_pm10_completed_case(case_key) else "",
            ]
            if p
        ),
    }


def build_candidate_readiness_rows() -> list[dict[str, str]]:
    return [readiness_for_candidate(row) for row in read_csv(CANDIDATE_CASES)]


def runnable_readiness_rows(readiness_rows: list[dict[str, str]], include_dependency: bool = True) -> list[dict[str, str]]:
    allowed = {"runnable-now"}
    if include_dependency:
        allowed.add("dependency-gated")
    return [row for row in readiness_rows if row["compute_readiness"] in allowed and row.get("representative_time_s")]


def scratch_case_dir(tmp_dir: Path, case_key: str) -> Path:
    return tmp_dir / "recon" / case_key


def plane_surface_name(row: dict[str, Any]) -> str:
    return f"plane_{row['plane_location']}"


def wall_surface_name(row: dict[str, Any]) -> str:
    return f"wallband_{row['plane_location']}"


def plane_rows_for_case(case_key: str, plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in plan_rows if row["case_key"] == case_key and row.get("x") and row.get("nx")]


def upcomer_wall_patches(source_id: str) -> list[str]:
    profile = get_case_analysis_profile(geometry_source_id(source_id))
    patches: list[str] = []
    for span in ("left_lower_leg", "test_section_span", "left_upper_leg"):
        for patch_name in profile.major_spans[span]["wall_patches"]:
            if patch_name not in patches:
                patches.append(str(patch_name))
    return patches


def write_control_dict(case_dir: Path, case_key: str, mode: str = "surfaces") -> dict[str, Any]:
    plan_rows = plane_rows_for_case(case_key, build_plan_rows())
    if not plan_rows:
        raise ValueError(f"no plane rows with geometry for case_key={case_key}")
    source_id = str(plan_rows[0]["source_id"])
    rho_temperature_fallback = use_rho_temperature_fallback(case_key)
    fields = ["U", "rho", "p_rgh", "Re", "Pr", "Ri", "Gr", "Ra"]
    if not rho_temperature_fallback:
        fields.insert(1, "T")
    wall_fields = ["rho", "wallHeatFlux"] if rho_temperature_fallback else ["T", "wallHeatFlux"]
    lines = [
        "FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }",
        "application foamRun; startTime 0; stopAt endTime; endTime 1000000; deltaT 1;",
        "writeControl timeStep; writeInterval 1; writeFormat ascii; writePrecision 10;",
        "writeCompression off; timeFormat general; timePrecision 10; runTimeModifiable false;",
        "functions {",
    ]
    if mode in {"wallheatflux", "combined"}:
        lines.extend(
            [
                "  upcomerWallHeatFluxField {",
                "    type            wallHeatFlux;",
                '    libs            ("libfieldFunctionObjects.so");',
                "    writeControl    writeTime;",
                "    writeFields     true;",
                "    log             false;",
                "  }",
            ]
        )
    if mode in {"surfaces", "combined"}:
        lines.extend(
            [
                f"  {FO_SAMPLE_NAME} {{",
                "    type            surfaces;",
                '    libs            ("libsampling.so");',
                "    writeControl    writeTime;",
                "    surfaceFormat   vtk;",
                "    interpolate     false;",
                "    interpolationScheme cell;",
                f"    fields          ({' '.join(fields)});",
                "    surfaces (",
            ]
        )
        for row in plan_rows:
            lines.extend(
                [
                    f"      {plane_surface_name(row)} {{",
                    "        type        cuttingPlane;",
                    "        planeType   pointAndNormal;",
                    "        pointAndNormalDict",
                    "        {",
                    f"          point ({row['x']} {row['y']} {row['z']});",
                    f"          normal ({row['nx']} {row['ny']} {row['nz']});",
                    "        }",
                    "      }",
                ]
            )
        lines.extend(["    );", "  }"])
        patch_list = " ".join(upcomer_wall_patches(source_id))
        lines.extend(
            [
                f"  {FO_WALL_BAND_NAME} {{",
                "    type            surfaces;",
                '    libs            ("libsampling.so");',
                "    writeControl    writeTime;",
                "    surfaceFormat   vtk;",
                "    interpolate     false;",
                "    interpolationScheme cell;",
                f"    fields          ({' '.join(wall_fields)});",
                "    surfaces (",
                "      upcomerWallPatches {",
                "        type        patch;",
                f"        patches     ({patch_list});",
                "      }",
                "    );",
                "  }",
            ]
        )
    lines.append("}")
    out = case_dir / "system" / "controlDict"
    ensure_dir(out.parent)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"control_dict": rel(out), "mode": mode, "case_key": case_key, "source_id": source_id, "plane_count": len(plan_rows)}


def vtk_tokenize(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="ignore").replace("\r", "\n").split()


def parse_legacy_vtk(path: Path) -> dict[str, Any]:
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
        token = tokens[idx]
        upper = token.upper()
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
                n = int(tokens[idx])
                idx += 1
                polygons.append([int(tokens[idx + j]) for j in range(n)])
                idx += n
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
                    target[name] = arr.reshape(n_items, n_comp)[:, 0] if n_comp == 1 else arr.reshape(n_items, n_comp)
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
                        idx += 4
                        arr, idx = take_float_array(idx, n_tuples * n_comp)
                        shaped = arr.reshape(n_tuples, n_comp)
                        target[name] = shaped[:, 0] if n_comp == 1 else shaped
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
    for i in range(1, len(points) - 1):
        area += 0.5 * float(np.linalg.norm(np.cross(points[i] - anchor, points[i + 1] - anchor)))
    return area


def cell_values(vtk: dict[str, Any], field_name: str) -> np.ndarray | None:
    if field_name in vtk["cell_fields"]:
        return np.asarray(vtk["cell_fields"][field_name], dtype=float)
    if field_name not in vtk["point_fields"]:
        return None
    point_values = np.asarray(vtk["point_fields"][field_name], dtype=float)
    vals: list[np.ndarray | float] = []
    for poly in vtk["polygons"]:
        vals.append(np.mean(point_values[poly], axis=0))
    return np.asarray(vals, dtype=float)


def parse_area_weighted_plane_vtk(path: Path, normal: np.ndarray) -> dict[str, Any]:
    vtk = parse_legacy_vtk(path)
    points = vtk["points"]
    polygons = vtk["polygons"]
    areas = np.array([polygon_area(points[poly]) for poly in polygons], dtype=float)
    if len(areas) == 0 or float(np.sum(areas)) <= 0.0:
        raise ValueError("no positive-area polygons")
    velocities = cell_values(vtk, "U")
    rho = cell_values(vtk, "rho")
    temp_values = cell_values(vtk, "T")
    if velocities is None or rho is None:
        raise ValueError("missing one of required fields U/rho")
    velocities = np.asarray(velocities, dtype=float).reshape(len(areas), 3)
    rho = np.asarray(rho, dtype=float).reshape(len(areas))
    temp, temp_source = temperature_from_fields(
        np.asarray(temp_values, dtype=float).reshape(len(areas)) if temp_values is not None else None,
        rho,
    )
    un = velocities @ normal
    speed2 = np.sum(velocities * velocities, axis=1)
    tangential = velocities - np.outer(un, normal)
    secondary2 = np.sum(tangential * tangential, axis=1)
    reverse = un < 0.0
    abs_flux = np.abs(rho * un) * areas
    reverse_flux = np.maximum(-rho * un, 0.0) * areas
    signed_flux = rho * un * areas
    forward_flux = np.maximum(rho * un, 0.0) * areas
    signed_denom = float(np.sum(signed_flux))
    forward_denom = float(np.sum(forward_flux))
    parsed: dict[str, Any] = {
        "face_count": len(areas),
        "reverse_area_fraction": float(np.sum(areas[reverse]) / np.sum(areas)),
        "reverse_mass_fraction": float(np.sum(reverse_flux) / max(float(np.sum(abs_flux)), 1e-300)),
        "secondary_velocity_fraction": float(
            math.sqrt(float(np.average(secondary2, weights=areas)))
            / max(math.sqrt(float(np.average(speed2, weights=areas))), 1e-300)
        ),
        "bulk_T_K": float(np.sum(signed_flux * temp) / signed_denom) if abs(signed_denom) > 1e-300 else math.nan,
        "forward_bulk_T_K": float(np.sum(forward_flux * temp) / forward_denom) if forward_denom > 1e-300 else math.nan,
        "temperature_source": temp_source,
    }
    for field in ("Re", "Pr", "Ri", "Gr", "Ra"):
        values = cell_values(vtk, field)
        if values is not None:
            parsed[field] = float(np.average(np.asarray(values, dtype=float).reshape(len(areas)), weights=areas))
    return parsed


def parse_wall_band_vtk(path: Path, plane_row: dict[str, Any]) -> dict[str, Any]:
    vtk = parse_legacy_vtk(path)
    points = vtk["points"]
    polygons = vtk["polygons"]
    temp_values = cell_values(vtk, "T")
    rho_values = cell_values(vtk, "rho")
    whf = cell_values(vtk, "wallHeatFlux")
    if whf is None:
        raise ValueError("missing wallHeatFlux")
    normal = normalize(np.array([float(plane_row["nx"]), float(plane_row["ny"]), float(plane_row["nz"])]))
    point = np.array([float(plane_row["x"]), float(plane_row["y"]), float(plane_row["z"])])
    bore = safe_float(plane_row.get("bore_m")) or 0.02
    band_half_width = 0.5 * bore
    areas: list[float] = []
    keep: list[bool] = []
    for poly in polygons:
        poly_pts = points[poly]
        centroid = np.mean(poly_pts, axis=0)
        areas.append(polygon_area(poly_pts))
        keep.append(abs(float((centroid - point) @ normal)) <= band_half_width)
    areas_arr = np.asarray(areas, dtype=float)
    keep_arr = np.asarray(keep, dtype=bool)
    if int(np.sum(keep_arr)) < 1:
        keep_arr = np.ones(len(areas_arr), dtype=bool)
    temp_full, temp_source = temperature_from_fields(
        np.asarray(temp_values, dtype=float).reshape(len(areas_arr)) if temp_values is not None else None,
        np.asarray(rho_values, dtype=float).reshape(len(areas_arr)) if rho_values is not None else None,
    )
    temp_arr = temp_full[keep_arr]
    whf_arr = np.asarray(whf, dtype=float).reshape(len(areas_arr))[keep_arr]
    area_sel = areas_arr[keep_arr]
    return {
        "wall_face_count": int(np.sum(keep_arr)),
        "wall_T_K": float(np.average(temp_arr, weights=area_sel)),
        "wallHeatFlux_W_m2": float(np.average(whf_arr, weights=area_sel)),
        "wall_band_half_width_m": band_half_width,
        "wall_temperature_source": temp_source,
    }


def find_vtk_surface(case_dir: Path, fo_name: str, time_s: str, surface_name: str) -> Path | None:
    base = case_dir / "postProcessing" / fo_name / time_s
    candidates = [base / f"{surface_name}.vtk", base / f"{surface_name}_0.vtk"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    root = case_dir / "postProcessing" / fo_name
    if root.exists():
        hits = sorted(root.glob(f"**/{surface_name}*.vtk"))
        if hits:
            return hits[-1]
    return None


def classify_metric_row(row: dict[str, Any]) -> str:
    reverse_area = safe_float(row.get("reverse_area_fraction"))
    reverse_mass = safe_float(row.get("reverse_mass_fraction"))
    ri = safe_float(row.get("Ri"))
    if (
        (reverse_area is not None and reverse_area >= 0.10)
        or (reverse_mass is not None and reverse_mass >= 0.10)
        or (ri is not None and ri >= 1.0)
    ):
        return "diagnostic-only-recirculating"
    required = ["reverse_area_fraction", "reverse_mass_fraction", "secondary_velocity_fraction", "Ri", "bulk_T_K", "wall_T_K", "wallHeatFlux_W_m2"]
    if any(safe_float(row.get(key)) is None for key in required):
        return "blocked-missing-field"
    delta_t = abs(float(row["wall_T_K"]) - float(row["bulk_T_K"]))
    if delta_t < 0.5:
        return "diagnostic-only-small-wall-bulk-deltaT"
    if float(row["reverse_area_fraction"]) >= 0.02 or float(row["reverse_mass_fraction"]) >= 0.02:
        return "diagnostic-only-recirculating"
    if float(row["secondary_velocity_fraction"]) >= 0.20:
        return "diagnostic-only-secondary-flow"
    if float(row["Ri"]) >= 0.30:
        return "diagnostic-only-mixed-convection"
    return "fit-admissible-pending-residual-gate"


def parse_compute_samples(case_dir: Path, case_key: str, output_dir: Path | None = None) -> list[dict[str, Any]]:
    plan_rows = plane_rows_for_case(case_key, build_plan_rows())
    rows: list[dict[str, Any]] = []
    for plane_row in plan_rows:
        time_s = str(plane_row["representative_time_s"])
        normal = normalize(np.array([float(plane_row["nx"]), float(plane_row["ny"]), float(plane_row["nz"])]))
        plane_vtk = find_vtk_surface(case_dir, FO_SAMPLE_NAME, time_s, plane_surface_name(plane_row))
        wall_vtk = find_vtk_surface(case_dir, FO_WALL_BAND_NAME, time_s, "upcomerWallPatches")
        parsed: dict[str, Any] = {}
        flags: list[str] = []
        if plane_vtk is None:
            flags.append("missing_plane_vtk")
        else:
            try:
                parsed.update(parse_area_weighted_plane_vtk(plane_vtk, normal))
            except Exception as exc:  # noqa: BLE001
                flags.append(f"plane_parse_failed:{exc}")
        if wall_vtk is None:
            flags.append("missing_wall_vtk")
        else:
            try:
                parsed.update(parse_wall_band_vtk(wall_vtk, plane_row))
            except Exception as exc:  # noqa: BLE001
                flags.append(f"wall_parse_failed:{exc}")
        bulk_rule = "signed_mass_flux_bulk_T"
        bulk_t = safe_float(parsed.get("bulk_T_K"))
        forward_bulk_t = safe_float(parsed.get("forward_bulk_T_K"))
        if (
            (bulk_t is None or not (250.0 <= bulk_t <= 1500.0))
            and forward_bulk_t is not None
            and 250.0 <= forward_bulk_t <= 1500.0
        ):
            parsed["bulk_T_K"] = parsed["forward_bulk_T_K"]
            bulk_rule = "forward_dominant_bulk_T_fallback"
        elif parsed.get("temperature_source") == "T_from_rho_linear_eos":
            bulk_rule = "signed_mass_flux_bulk_T_from_rho_linear_eos"
        if bulk_rule == "forward_dominant_bulk_T_fallback" and parsed.get("temperature_source") == "T_from_rho_linear_eos":
            bulk_rule = "forward_dominant_bulk_T_from_rho_linear_eos"
        dh = safe_float(plane_row.get("bore_m")) or math.nan
        length = station_length_from_upcomer_inlet(str(plane_row["source_id"]), str(plane_row["plane_location"]))
        gz = (
            "not_applicable_zero_entry_length"
            if plane_row["plane_location"] == "upcomer_inlet"
            else fmt(gz_from_station(float(parsed.get("Re", math.nan)), float(parsed.get("Pr", math.nan)), dh, length))
        )
        delta_t = ""
        if safe_float(parsed.get("wall_T_K")) is not None and safe_float(parsed.get("bulk_T_K")) is not None:
            delta_t = fmt(float(parsed["wall_T_K"]) - float(parsed["bulk_T_K"]))
        out = {
            "case_key": plane_row["case_key"],
            "source_id": plane_row["source_id"],
            "case_role": plane_row["case_role"],
            "plane_location": plane_row["plane_location"],
            "span": plane_row["span"],
            "station_label": plane_row["station_label"],
            "representative_time_s": time_s,
            "sampled_plane_file": rel(plane_vtk),
            "sampled_wall_file": rel(wall_vtk),
            "metric_status": "parsed" if not flags else "incomplete",
            "face_count": fmt(parsed.get("face_count"), 0),
            "wall_face_count": fmt(parsed.get("wall_face_count"), 0),
            "reverse_area_fraction": fmt(parsed.get("reverse_area_fraction")),
            "reverse_mass_fraction": fmt(parsed.get("reverse_mass_fraction")),
            "secondary_velocity_fraction": fmt(parsed.get("secondary_velocity_fraction")),
            "bulk_T_K": fmt(parsed.get("bulk_T_K")),
            "bulk_T_rule": bulk_rule,
            "wall_T_K": fmt(parsed.get("wall_T_K")),
            "wallHeatFlux_W_m2": fmt(parsed.get("wallHeatFlux_W_m2")),
            "Re": fmt(parsed.get("Re")),
            "Pr": fmt(parsed.get("Pr")),
            "Ri": fmt(parsed.get("Ri")),
            "Gr": fmt(parsed.get("Gr")),
            "Ra": fmt(parsed.get("Ra")),
            "Gz": gz,
            "delta_T_wall_bulk_K": delta_t,
            "quality_flags": ";".join(flags),
            "source_paths": plane_row["source_paths"],
        }
        admission_status = classify_metric_row(out)
        plane_has_metrics = not any(flag.startswith("plane_parse_failed") or flag == "missing_plane_vtk" for flag in flags)
        if not flags:
            metric_status = "parsed"
        elif plane_has_metrics and admission_status == "diagnostic-only-recirculating":
            metric_status = "parsed_recirculation_diagnostic"
        else:
            metric_status = "incomplete"
            admission_status = "blocked-missing-field"
        out["metric_status"] = metric_status
        out["admission_status"] = admission_status
        rows.append(out)
    if output_dir is not None:
        ensure_dir(output_dir)
        csv_dump(output_dir / f"matched_plane_metrics_{case_key}.csv", COMPUTE_FIELDS, rows)
        json_dump(
            output_dir / f"parse_summary_{case_key}.json",
            {"case_key": case_key, "row_count": len(rows), "parsed_rows": sum(row["metric_status"].startswith("parsed") for row in rows)},
        )
    return rows


def write_compute_package_scripts(output_dir: Path, tmp_dir: Path, readiness_rows: list[dict[str, str]]) -> dict[str, Any]:
    scripts = ensure_dir(output_dir / "scripts")
    runner = scripts / "run_upcomer_matched_plane_compute.sh"
    rows = runnable_readiness_rows(readiness_rows)
    case_lines = "\n".join(
        "|".join(
            [
                row["case_key"],
                row["source_id"],
                row["source_case_dir"],
                row["existing_recon_dir"],
                row["representative_time_s"],
                row["compute_readiness"],
            ]
        )
        for row in rows
    )
    runner.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail

ROOT=/scratch/09748/andresfierro231/projects_scratch/ethan_runs
OUT={q(output_dir)}
TMP={q(tmp_dir)}
OF_ENV="$ROOT/tools/ofenv/of13_env.sh"
LOG_DIR="$OUT/logs"
cd "$ROOT"
mkdir -p "$LOG_DIR" "$TMP/recon" "$OUT/parsed"

log() {{ printf '[%s] %s\\n' "$(date --iso-8601=seconds)" "$*" >&2; }}
die() {{ log "ERROR: $*"; exit 1; }}

prepare_case() {{
  local case_key="$1" source_id="$2" source_case="$3" existing_recon="$4" time_s="$5"
  [[ -n "$source_case" && "$source_case" != /* ]] && source_case="$ROOT/$source_case"
  [[ -n "$existing_recon" && "$existing_recon" != /* ]] && existing_recon="$ROOT/$existing_recon"
  local recon_dir="$TMP/recon/$case_key"
  local reconstruct_fields='(U T rho p_rgh Re Pr Ri Gr Ra)'
  case "$case_key" in
    salt2_lo10q|salt2_hi10q|salt4_lo10q|salt4_hi10q)
      reconstruct_fields='(U rho p_rgh Re Pr Ri Gr Ra wallHeatFlux)'
      ;;
  esac
  mkdir -p "$recon_dir"
  if [[ -n "$existing_recon" && -d "$existing_recon/$time_s" ]]; then
    for name in constant system 0; do
      if [[ ! -e "$recon_dir/$name" ]]; then
        cp -a "$existing_recon/$name" "$recon_dir/$name"
      fi
    done
    if [[ ! -e "$recon_dir/$time_s" ]]; then
      ln -s "$existing_recon/$time_s" "$recon_dir/$time_s"
    fi
  elif [[ -n "$source_case" && -d "$source_case/processors64/$time_s" ]]; then
    for name in constant system 0; do
      if [[ ! -e "$recon_dir/$name" ]]; then
        cp -a "$source_case/$name" "$recon_dir/$name"
      fi
    done
    if [[ -L "$recon_dir/processors64" && ! -e "$recon_dir/processors64" ]]; then
      rm -f "$recon_dir/processors64"
    fi
    if [[ ! -e "$recon_dir/processors64" ]]; then
      ln -s "$source_case/processors64" "$recon_dir/processors64"
    fi
    if [[ ! -d "$recon_dir/$time_s" ]]; then
      timeout 90m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && reconstructPar -case '$recon_dir' -time '$time_s' -fields '$reconstruct_fields' -fileHandler collated -noFunctionObjects -newTimes" > "$LOG_DIR/reconstruct_${{case_key}}.log" 2>&1
    fi
    if [[ ! -f "$recon_dir/$time_s/wallHeatFlux" && -f "$source_case/processors64/$time_s/wallHeatFlux" ]]; then
      timeout 45m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && reconstructPar -case '$recon_dir' -time '$time_s' -fields '(wallHeatFlux)' -fileHandler collated -noFunctionObjects" > "$LOG_DIR/reconstruct_wallHeatFlux_${{case_key}}.log" 2>&1
    fi
    [[ -d "$recon_dir/$time_s" ]] || die "reconstruction did not create $recon_dir/$time_s"
  else
    die "no reconstructed or processor time for $case_key t=$time_s"
  fi
  if [[ -e "$recon_dir/system/functions" && ! -e "$recon_dir/system/functions.upcomer_disabled" ]]; then
    mv "$recon_dir/system/functions" "$recon_dir/system/functions.upcomer_disabled"
  fi
  printf '%s\\n' "$recon_dir"
}}

run_case() {{
  local case_key="$1" source_id="$2" source_case="$3" existing_recon="$4" time_s="$5"
  local recon_dir
  recon_dir="$(prepare_case "$case_key" "$source_id" "$source_case" "$existing_recon" "$time_s")"
  if [[ -f "$recon_dir/$time_s/wallHeatFlux" ]]; then
    log "Using reconstructed wallHeatFlux field for $case_key"
  else
    log "Generating wallHeatFlux field for $case_key"
    python3.11 "$ROOT/tools/extract/sample_upcomer_matched_plane_metrics.py" write-control-dict --case-dir "$recon_dir" --case-key "$case_key" --mode wallheatflux
    timeout 45m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && foamPostProcess -case '$recon_dir' -time '$time_s'" > "$LOG_DIR/wallHeatFlux_${{case_key}}.log" 2>&1 || true
  fi
  log "Sampling matched planes and wall bands for $case_key"
  python3.11 "$ROOT/tools/extract/sample_upcomer_matched_plane_metrics.py" write-control-dict --case-dir "$recon_dir" --case-key "$case_key" --mode surfaces
  timeout 90m bash -lc "source '$OF_ENV' >/dev/null 2>&1 && foamPostProcess -case '$recon_dir' -time '$time_s'" > "$LOG_DIR/surfaces_${{case_key}}.log" 2>&1
  python3.11 "$ROOT/tools/extract/sample_upcomer_matched_plane_metrics.py" parse-openfoam-samples --case-dir "$recon_dir" --case-key "$case_key" --output-dir "$OUT/parsed"
}}

mode="${{1:-nominal}}"
case "$mode" in
  preflight)
    while IFS='|' read -r case_key source_id source_case existing_recon time_s readiness; do
      [[ -n "$case_key" ]] || continue
      [[ -n "$time_s" ]] || die "missing time for $case_key"
      mesh_source_id="$source_id"
      case "$source_id" in
        salt2_jin_*_corrected) mesh_source_id="viscosity_screening_salt_test_2_jin_coarse_mesh" ;;
        salt4_jin_*_corrected) mesh_source_id="viscosity_screening_salt_test_4_jin_coarse_mesh" ;;
      esac
      [[ -f "$ROOT/work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines/$mesh_source_id/mesh_stations.json" ]] || die "missing mesh stations for $source_id via $mesh_source_id"
      if [[ -n "$existing_recon" ]]; then
        [[ -d "$existing_recon/$time_s" ]] || die "missing reconstructed time for $case_key: $existing_recon/$time_s"
      else
        [[ -n "$source_case" ]] || die "missing source case for $case_key"
        [[ -d "$source_case/processors64/$time_s" ]] || die "missing processor frame for $case_key: $source_case/processors64/$time_s"
        for name in constant system 0; do
          [[ -e "$source_case/$name" ]] || die "missing $name in source case for $case_key: $source_case"
        done
      fi
    done <<'CASES'
{case_lines}
CASES
    ;;
  nominal)
    while IFS='|' read -r case_key source_id source_case existing_recon time_s readiness; do
      [[ "$readiness" == "runnable-now" ]] || continue
      case "$case_key" in
        salt2_lo10q|salt2_hi10q|salt4_lo10q|salt4_hi10q) ;;
        *) continue ;;
      esac
      run_case "$case_key" "$source_id" "$source_case" "$existing_recon" "$time_s"
    done <<'CASES'
{case_lines}
CASES
    ;;
  one)
    target_case="${{2:-}}"
    [[ -n "$target_case" ]] || die "one mode requires a case key"
    matched=0
    while IFS='|' read -r case_key source_id source_case existing_recon time_s readiness; do
      [[ "$case_key" == "$target_case" ]] || continue
      [[ "$readiness" == "runnable-now" || "$readiness" == "dependency-gated" ]] || continue
      matched=1
      run_case "$case_key" "$source_id" "$source_case" "$existing_recon" "$time_s"
    done <<'CASES'
{case_lines}
CASES
    [[ "$matched" == "1" ]] || die "no runnable case matched $target_case"
    ;;
  pm10)
    while IFS='|' read -r case_key source_id source_case existing_recon time_s readiness; do
      [[ "$readiness" == "runnable-now" ]] || continue
      case "$case_key" in
        salt2_lo10q|salt2_hi10q|salt4_lo10q|salt4_hi10q) ;;
        *) continue ;;
      esac
      run_case "$case_key" "$source_id" "$source_case" "$existing_recon" "$time_s"
    done <<'CASES'
{case_lines}
CASES
    ;;
  all-ready)
    while IFS='|' read -r case_key source_id source_case existing_recon time_s readiness; do
      [[ "$readiness" == "runnable-now" || "$readiness" == "dependency-gated" ]] || continue
      run_case "$case_key" "$source_id" "$source_case" "$existing_recon" "$time_s"
    done <<'CASES'
{case_lines}
CASES
    ;;
  *)
    die "unknown mode $mode"
    ;;
esac
log "upcomer matched-plane compute extraction complete mode=$mode"
""",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    nominal_sbatch = scripts / "submit_nominal_upcomer_matched_plane_compute.sbatch"
    nominal_sbatch.write_text(
        f"""#!/usr/bin/env bash
#SBATCH -J upc_nominal
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 02:00:00
#SBATCH -p development
#SBATCH -A ASC23046
#SBATCH -o {rel(output_dir)}/logs/upcomer_nominal-%j.out
#SBATCH -e {rel(output_dir)}/logs/upcomer_nominal-%j.err

set -euo pipefail

cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
bash {q(runner)} nominal
""",
        encoding="utf-8",
    )
    nominal_sbatch.chmod(0o755)
    dep_sbatch = scripts / "submit_corrected_q_dependency_upcomer_matched_plane_compute.sbatch"
    dep_sbatch.write_text(
        f"""#!/usr/bin/env bash
#SBATCH -J upc_corrq
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 02:00:00
#SBATCH -p development
#SBATCH -A ASC23046
#SBATCH -o {rel(output_dir)}/logs/upcomer_corrq-%j.out
#SBATCH -e {rel(output_dir)}/logs/upcomer_corrq-%j.err

set -euo pipefail

cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
bash {q(runner)} all-ready
""",
        encoding="utf-8",
    )
    dep_sbatch.chmod(0o755)
    pm10_sbatch = scripts / "submit_pm10_upcomer_matched_plane_compute.sbatch"
    pm10_sbatch.write_text(
        f"""#!/usr/bin/env bash
#SBATCH -J upc_pm10
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 02:00:00
#SBATCH -p development
#SBATCH -A ASC23046
#SBATCH -a 0-3
#SBATCH -o {rel(output_dir)}/logs/upcomer_pm10-%A_%a.out
#SBATCH -e {rel(output_dir)}/logs/upcomer_pm10-%A_%a.err

set -euo pipefail

cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
case_keys=(salt2_lo10q salt2_hi10q salt4_lo10q salt4_hi10q)
bash {q(runner)} one "${{case_keys[$SLURM_ARRAY_TASK_ID]}}"
""",
        encoding="utf-8",
    )
    pm10_sbatch.chmod(0o755)
    return {
        "runner": rel(runner),
        "nominal_sbatch": rel(nominal_sbatch),
        "corrected_q_sbatch": rel(dep_sbatch),
        "pm10_sbatch": rel(pm10_sbatch),
        "runnable_or_dependency_rows": len(rows),
    }


def write_compute_method_docs(output_dir: Path, summary: dict[str, Any]) -> None:
    output_rel = rel(output_dir)
    tmp_rel = summary.get("tmp_dir", rel(COMPUTE_TMP_DIR))
    generated_date = str(summary.get("generated_at", "2026-07-14")).split("T", 1)[0]
    (output_dir / "method_trace.md").write_text(
        f"""---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/upcomer_extraction_contract.csv
tags: [therm-reconstr, upcomer-recirculation, internal-nu, method]
task: {COMPUTE_TASK_ID}
date: {generated_date}
role: Implementer/Tester/Writer
type: method
status: active
---
# Matched Upcomer Plane Compute Method

## Method

The extractor samples three fixed geometric planes: `upcomer_inlet`,
`upcomer_mid`, and `upcomer_outlet`. Plane normals come from
`mesh_stations.json`; they are not inferred from the mean velocity.

The compute lane writes scratch-only OpenFOAM controlDicts. It first generates
`wallHeatFlux` in the scratch reconstructed case when needed, then samples VTK
surfaces for plane fields and upcomer wall patches.

Plane metrics are true face-area weighted when VTK geometry is present:

- reverse area fraction = reverse-flow face area / total face area;
- reverse mass fraction = reverse `rho * U_n * A` / total absolute mass flux;
- secondary velocity fraction = RMS tangential velocity / RMS speed;
- bulk T = signed mass-flux-weighted T, with forward-dominant fallback only when
  signed flux is singular;
- Re/Pr/Ri/Gr/Ra = area-weighted sampled values;
- Gz = Re * Pr * D_h / streamwise length from upcomer inlet.

Wall metrics use the upcomer wall-patch surface and keep faces within
`0.5*bore_m` of each station plane along the station normal. `wallHeatFlux` is
the total OpenFOAM field; `rcExternalTemperature` radiation is embedded and no
separate `qr` residual is added.

## Classification

Rows are fit-admissible only if they pass all current scalar gates:
reverse area fraction < 0.02, reverse mass fraction < 0.02, secondary velocity
fraction < 0.20, Ri < 0.30, and |T_wall - T_bulk| >= 0.5 K. The heat-balance
residual gate remains pending until matched enthalpy residual rows are wired in.
""",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        f"""---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/upcomer_onset_candidate_cases.csv
tags: [therm-reconstr, upcomer-recirculation, internal-nu, openfoam]
related:
  - tools/extract/sample_upcomer_matched_plane_metrics.py
  - {output_rel}/method_trace.md
task: {COMPUTE_TASK_ID}
date: {generated_date}
role: Implementer/Tester/Writer
type: work_product
status: active
---
# Upcomer Matched Plane Compute Extraction

## Status

This package converts the AGENT-341 diagnostic plan into a compute-node
workflow. It generated {summary["candidate_rows"]} candidate readiness rows:
{summary["runnable_now_rows"]} runnable now, {summary["dependency_gated_rows"]}
dependency-gated, and {summary["blocked_rows"]} blocked by policy, failed runs,
missing terminal harvest, or missing targeted CFD cases.

## Commands

Build or refresh this package:

```bash
python3.11 tools/extract/sample_upcomer_matched_plane_metrics.py build-openfoam-package \\
  --output-dir {output_rel}
```

Login-safe preflight:

```bash
bash {output_rel}/scripts/run_upcomer_matched_plane_compute.sh preflight
```

Submit nominal Salt2/Salt3/Salt4 compute extraction:

```bash
sbatch {output_rel}/scripts/submit_nominal_upcomer_matched_plane_compute.sbatch
```

Submit corrected-Q dependency extraction after harvest jobs:

```bash
sbatch --dependency=afterok:3295437:3295438 \\
  {output_rel}/scripts/submit_corrected_q_dependency_upcomer_matched_plane_compute.sbatch
```

## Outputs

- `candidate_readiness_matrix.csv`
- `slurm_submission_log.csv`
- `matched_plane_metrics_admission.csv`
- `mesh_family_repeat_status.csv`
- `method_trace.md`
- `scripts/run_upcomer_matched_plane_compute.sh`

No native CFD solver outputs are mutated; scratch reconstructions live under
`{tmp_rel}/`.
""",
        encoding="utf-8",
    )


def build_openfoam_package(output_dir: Path = COMPUTE_PACKAGE_DIR, tmp_dir: Path = COMPUTE_TMP_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    ensure_dir(output_dir / "logs")
    readiness_rows = build_candidate_readiness_rows()
    scripts = write_compute_package_scripts(output_dir, tmp_dir, readiness_rows)
    csv_dump(output_dir / "candidate_readiness_matrix.csv", CANDIDATE_READINESS_FIELDS, readiness_rows)
    mesh_rows = build_mesh_repeat_rows()
    csv_dump(output_dir / "mesh_family_repeat_status.csv", list(mesh_rows[0].keys()) if mesh_rows else [], mesh_rows)
    # Initial admission table records blockers before compute output exists.
    admission_rows: list[dict[str, Any]] = []
    for row in build_plan_rows():
        admission_rows.append(
            {
                **{field: row.get(field, "") for field in COMPUTE_FIELDS if field in row},
                "sampled_plane_file": "",
                "sampled_wall_file": "",
                "metric_status": "awaiting_compute_node_sampling" if row.get("representative_time_s") else "blocked_before_sampling",
                "face_count": "",
                "wall_face_count": "",
                "bulk_T_rule": "not_sampled",
                "delta_T_wall_bulk_K": "",
                "admission_status": (
                    "blocked-compute-node-sampling-required"
                    if row.get("representative_time_s")
                    else "blocked-terminal-harvest-or-new-cfd-run"
                ),
                "quality_flags": row.get("existing_metric_status", ""),
            }
        )
    csv_dump(output_dir / "matched_plane_metrics_admission.csv", COMPUTE_FIELDS, admission_rows)
    slurm_rows = [
        {
            "submission_group": "nominal",
            "sbatch_path": scripts["nominal_sbatch"],
            "dependency": "",
            "job_id": "",
            "status": "not_submitted_by_builder",
        },
        {
            "submission_group": "corrected_q_dependency",
            "sbatch_path": scripts["corrected_q_sbatch"],
            "dependency": "afterok:3295437:3295438",
            "job_id": "",
            "status": "not_submitted_by_builder",
        },
        {
            "submission_group": "pm10_array",
            "sbatch_path": scripts["pm10_sbatch"],
            "dependency": "",
            "job_id": "",
            "status": "not_submitted_by_builder",
        },
    ]
    csv_dump(output_dir / "slurm_submission_log.csv", ["submission_group", "sbatch_path", "dependency", "job_id", "status"], slurm_rows)
    summary = {
        "task": COMPUTE_TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "compute_package_ready_for_submission",
        "candidate_rows": len(readiness_rows),
        "runnable_now_rows": sum(row["compute_readiness"] == "runnable-now" for row in readiness_rows),
        "dependency_gated_rows": sum(row["compute_readiness"] == "dependency-gated" for row in readiness_rows),
        "blocked_rows": sum(row["compute_readiness"].startswith("blocked") for row in readiness_rows),
        "admission_rows": len(admission_rows),
        "tmp_dir": rel(tmp_dir),
        **scripts,
    }
    json_dump(output_dir / "summary.json", summary)
    write_compute_method_docs(output_dir, summary)
    return summary


def write_compute_scripts(output_dir: Path) -> None:
    scripts = ensure_dir(output_dir / "scripts")
    runner = scripts / "run_upcomer_matched_plane_sampling.sh"
    runner.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

REPO=/scratch/09748/andresfierro231/projects_scratch/ethan_runs
cd "$REPO"

source tools/ofenv/of13_env.sh

echo "This plan intentionally does not run on login nodes."
echo "For each terminal reconstructed case, add a temporary controlDict with:"
echo "  functionObject: upcomerMatchedPlaneSurfaces"
echo "  fields: U T rho p_rgh Re Pr Ri Gr Ra"
echo "  planes: upcomer_inlet, upcomer_mid, upcomer_outlet from openfoam_sampling_targets.csv"
echo "Then run: foamPostProcess -case <recon_case_dir> -time <representative_time_s>"
echo "Follow with: python3.11 tools/extract/sample_upcomer_matched_plane_metrics.py --output-dir <package>"
""",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    sbatch = scripts / "submit_upcomer_matched_plane_sampling.sbatch"
    sbatch.write_text(
        """#!/usr/bin/env bash
#SBATCH -J upc_plane
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -t 00:30:00
#SBATCH -p development
#SBATCH -o upcomer_matched_plane_sampling-%j.out
#SBATCH -e upcomer_matched_plane_sampling-%j.err

set -euo pipefail

REPO=/scratch/09748/andresfierro231/projects_scratch/ethan_runs
cd "$REPO"

bash work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/scripts/run_upcomer_matched_plane_sampling.sh
""",
        encoding="utf-8",
    )
    sbatch.chmod(0o755)


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    readme = output_dir / "README.md"
    readme.write_text(
        f"""---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract/upcomer_extraction_contract.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/upcomer_onset_candidate_cases.csv
tags: [therm-reconstr, upcomer-recirculation, internal-nu, extraction-contract]
related:
  - tools/extract/sample_upcomer_matched_plane_metrics.py
  - tools/extract/sample_upcomer_convection_cell.py
  - tools/extract/sample_physical_segment_interface_temperatures.py
task: {TASK_ID}
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Upcomer Matched Plane Extraction Plan

## Decision

Existing postprocessing can provide diagnostic proxies for some matched
upcomer inlet/mid/outlet quantities, but it does not provide an admission-grade
internal-Nu dataset. Admission-grade extraction still requires a compute-node
OpenFOAM sampling pass because current raw planes do not include face areas and
do not provide station-band wall temperature plus wallHeatFlux on the same
matched planes.

## Closest Existing Scripts

- `tools/extract/sample_upcomer_convection_cell.py`: closest vector/nondim
  sampler; useful for `Ra/Ri/Gr/Re/Pr`, but its legacy metric normal is
  mean-velocity based and is not admissible for this contract.
- `tools/extract/sample_physical_segment_interface_temperatures.py`: closest
  compute-node plane-plan and raw parser pattern; it already separates signed
  mixing-cup and forward-dominant bulk temperature.
- `tools/extract/sample_span_endpoint_temperatures.py`: closest existing
  `secmeanSurfaces` parser; it recovers bulk T from rho where raw T is absent.
- `tools/extract/sample_segment_htc_uaprime.py`: closest wall T/wallHeatFlux
  sign-convention source, but it is segment-level rather than upcomer
  inlet/mid/outlet station-band matched.

## Outputs

- `upcomer_matched_plane_extraction_plan.csv`: {summary["plan_rows"]} case-plane
  rows. Existing values are diagnostic proxies only where source files exist.
- `mesh_family_repeat_plan.csv`: {summary["mesh_repeat_rows"]} rows for Salt2
  coarse/medium/fine repeat planning.
- `existing_postprocessing_metric_status.csv`: copy of parsed plan rows for
  quick filtering by metric availability.
- `openfoam_sampling_targets.csv`: compute-node target table with station
  coordinates, geometric normals, source case paths, and representative times.
- `scripts/submit_upcomer_matched_plane_sampling.sbatch`: compute-node shell
  wrapper. It is intentionally a plan template; no heavy OpenFOAM command was
  run on the login node.

## Exact Commands

Regenerate this package:

```bash
python3.11 tools/extract/sample_upcomer_matched_plane_metrics.py \\
  --output-dir work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan
```

Validate parser logic:

```bash
python3.11 -m unittest tools.extract.test_sample_upcomer_matched_plane_metrics
```

Compute-node sampling plan:

```bash
sbatch work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_extraction_plan/scripts/submit_upcomer_matched_plane_sampling.sbatch
```

## Compute Requirements

Use one development node, one task, about 30 minutes for the current Salt2/3/4
terminal reconstructed cases. Do not run `foamPostProcess` for the matched
planes on a login node. Corrected-Q and targeted Re cases must first pass their
terminal/admission harvest before this extractor should sample them.

## Admission Guardrails

- Existing proxy rows remain diagnostic-only.
- No GCI is invented for missing, two-level, or non-monotone mesh data.
- Repair-smoke mesh-family rows stay diagnostic until an admission gate admits
  them.
- `rcExternalTemperature` wallHeatFlux already includes radiation effects; do
  not add a separate `qr` residual unless an explicit `qr` output is sampled.
""",
        encoding="utf-8",
    )


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    plan_rows = build_plan_rows()
    mesh_rows = build_mesh_repeat_rows()
    csv_dump(output_dir / "upcomer_matched_plane_extraction_plan.csv", PLAN_FIELDS, plan_rows)
    csv_dump(output_dir / "existing_postprocessing_metric_status.csv", PLAN_FIELDS, plan_rows)
    csv_dump(output_dir / "openfoam_sampling_targets.csv", PLAN_FIELDS, plan_rows)
    mesh_fields = list(mesh_rows[0].keys()) if mesh_rows else []
    csv_dump(output_dir / "mesh_family_repeat_plan.csv", mesh_fields, mesh_rows)
    write_compute_scripts(output_dir)
    source_manifest = [
        {"path": str(CONTRACT_DIR / "upcomer_extraction_contract.csv"), "role": "metric/formula contract"},
        {"path": str(CONTRACT_DIR / "upcomer_nu_admission_criteria.csv"), "role": "admission criteria"},
        {"path": str(CANDIDATE_CASES), "role": "admitted/candidate Salt case source table"},
        {"path": "tools/extract/sample_upcomer_convection_cell.py", "role": "nearest vector/nondim sampler"},
        {"path": "tools/extract/sample_physical_segment_interface_temperatures.py", "role": "nearest compute-node plane planner"},
        {"path": "tools/extract/sample_span_endpoint_temperatures.py", "role": "nearest existing bulk-T raw parser"},
        {"path": "tools/extract/sample_segment_htc_uaprime.py", "role": "nearest wall T/wallHeatFlux sign parser"},
    ]
    csv_dump(output_dir / "source_manifest.csv", ["path", "role"], source_manifest)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "complete_plan_existing_rows_diagnostic_only",
        "plan_rows": len(plan_rows),
        "mesh_repeat_rows": len(mesh_rows),
        "existing_proxy_rows": sum("diagnostic_" in row["existing_metric_status"] for row in plan_rows),
        "admission_grade_rows": 0,
        "compute_node_required": True,
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    legacy = sub.add_parser("legacy-package", help="Rebuild the AGENT-341 diagnostic plan package.")
    legacy.add_argument("--output-dir", type=Path, default=PACKAGE_DIR)
    build_of = sub.add_parser("build-openfoam-package", help="Build the AGENT-344 compute-node extraction package.")
    build_of.add_argument("--output-dir", type=Path, default=COMPUTE_PACKAGE_DIR)
    build_of.add_argument("--tmp-dir", type=Path, default=COMPUTE_TMP_DIR)
    write_cd = sub.add_parser("write-control-dict", help="Write scratch-case OpenFOAM controlDict for one case.")
    write_cd.add_argument("--case-dir", type=Path, required=True)
    write_cd.add_argument("--case-key", required=True)
    write_cd.add_argument("--mode", choices=["wallheatflux", "surfaces", "combined"], default="surfaces")
    parse_of = sub.add_parser("parse-openfoam-samples", help="Parse sampled VTK outputs for one scratch case.")
    parse_of.add_argument("--case-dir", type=Path, required=True)
    parse_of.add_argument("--case-key", required=True)
    parse_of.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "build-openfoam-package":
        summary = build_openfoam_package(args.output_dir, args.tmp_dir)
    elif args.command == "write-control-dict":
        summary = write_control_dict(args.case_dir, args.case_key, args.mode)
    elif args.command == "parse-openfoam-samples":
        rows = parse_compute_samples(args.case_dir, args.case_key, args.output_dir)
        summary = {"case_key": args.case_key, "row_count": len(rows), "parsed_rows": sum(row["metric_status"].startswith("parsed") for row in rows)}
    else:
        output_dir = getattr(args, "output_dir", PACKAGE_DIR)
        summary = build_package(output_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
