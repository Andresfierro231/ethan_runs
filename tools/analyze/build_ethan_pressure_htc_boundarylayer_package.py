#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt
import numpy as np

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.case_analysis_profiles import get_case_analysis_profile  # noqa: E402
from tools.common import (  # noqa: E402
    csv_dump,
    ensure_dir,
    iso_timestamp,
    json_dump,
    load_yaml,
    safe_float,
    save_matplotlib_figure,
)

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


DEFAULT_PACKAGE_INDEX = (
    ROOT
    / "reports"
    / "2026-06-15_ethan_all_runs_field_transport_campaign"
    / "field_transport_package_index.csv"
)
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package"
DEFAULT_SMOKE_OUTPUT_DIR = ROOT / "tmp" / "2026-06-17_ethan_pressure_htc_boundarylayer_package_smoke"
METADATA_INDEX = (
    ROOT
    / "reports"
    / "2026-06-04_ethan_case_metadata_index"
    / "ethan_case_metadata_index.csv"
)
REPRESENTATIVE_PROFILE_CASES = (
    "val_salt_test_2_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
)
GRAVITY_RE = re.compile(r"value\s*\(\s*([^\s]+)\s+([^\s]+)\s+([^\s]+)\s*\)\s*;")
THERMAL_MIN_ABS_DELTA_T_K = 0.25
THERMAL_MIN_POSITIVE_FLUX_KG_S = 1.0e-9
MAJOR_EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_leg_centerline_major_loss.py"


def load_module(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


major_extractor = load_module("sample_leg_centerline_major_loss_agent079", MAJOR_EXTRACTOR_PATH)


@dataclass
class CaseRecord:
    source_id: str
    case_label: str
    package_dir: Path
    profile_name: str
    metadata: dict[str, str]
    fluid_family: str
    source_root: Path
    gravity_vec: tuple[float, float, float]
    cp_coeffs: list[float]
    rho_coeffs: list[float]
    k_coeffs: list[float]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an additive Ethan 3D pressure/HTC/boundary-layer package from the "
            "June 15 live case-analysis artifacts without reopening the shared extraction path."
        )
    )
    parser.add_argument("--package-index", default=str(DEFAULT_PACKAGE_INDEX))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Optional bounded rebuild of one or more source IDs.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_metadata_index(path: Path) -> dict[str, dict[str, str]]:
    rows = load_csv_rows(path)
    return {row["source_id"]: row for row in rows if row.get("source_id")}


def polynomial_eval(coeffs: list[float], temperature_k: float) -> float:
    total = 0.0
    power = 1.0
    for coeff in coeffs:
        total += float(coeff) * power
        power *= temperature_k
    return total


def family_from_fluid(fluid: str) -> str:
    token = fluid.lower()
    if "water" in token:
        return "water"
    return "salt"


def parse_gravity_vector(case_root: Path) -> tuple[float, float, float]:
    path = case_root / "constant" / "g"
    if not path.exists():
        return (0.0, -9.81, 0.0)
    match = GRAVITY_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        return (0.0, -9.81, 0.0)
    return tuple(float(match.group(index)) for index in range(1, 4))  # type: ignore[return-value]


def read_case_record(row: dict[str, str], metadata_index: dict[str, dict[str, str]]) -> CaseRecord:
    source_id = row["source_id"]
    metadata = metadata_index[source_id]
    source_root = Path(metadata["source_root"])
    case_config = load_yaml(source_root / "case_config.yaml")
    fluid_props = case_config["fluid_properties"]
    cp_coeffs = [float(value) for value in fluid_props["Cp_coeffs"]]
    rho_coeffs = [float(value) for value in fluid_props["rho_coeffs"]]
    k_coeffs = [float(value) for value in fluid_props["kappa_spec"]["coeffs"]]
    fluid = str(metadata["fluid"])
    return CaseRecord(
        source_id=source_id,
        case_label=row["case_label"],
        package_dir=Path(row["package_dir"]),
        profile_name=row["profile_name"],
        metadata=metadata,
        fluid_family=family_from_fluid(fluid),
        source_root=source_root,
        gravity_vec=parse_gravity_vector(source_root),
        cp_coeffs=cp_coeffs,
        rho_coeffs=rho_coeffs,
        k_coeffs=k_coeffs,
    )


def is_finite_number(value: Any) -> bool:
    parsed = safe_float(value)
    return parsed is not None and math.isfinite(parsed)


def finite_float(value: Any, default: float = math.nan) -> float:
    parsed = safe_float(value)
    if parsed is None or not math.isfinite(parsed):
        return default
    return float(parsed)


def safe_mean(values: Iterable[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload) / len(payload))


def safe_weighted_mean(pairs: Iterable[tuple[float, float]]) -> float:
    numer = 0.0
    denom = 0.0
    for value, weight in pairs:
        if not math.isfinite(value) or not math.isfinite(weight) or weight <= 0.0:
            continue
        numer += value * weight
        denom += weight
    if denom <= 0.0:
        return math.nan
    return float(numer / denom)


def filter_source_rows(rows: list[dict[str, str]], source_ids: set[str] | None) -> list[dict[str, str]]:
    if not source_ids:
        return rows
    return [row for row in rows if row["source_id"] in source_ids]


def load_package_rows(package_dir: Path) -> dict[str, list[dict[str, str]]]:
    raw_dir = package_dir / "raw_extraction"
    return {
        "summary": [json.loads((package_dir / "summary.json").read_text(encoding="utf-8"))],
        "major_extraction_summary": [json.loads((raw_dir / "leg_major_loss_extraction_summary.json").read_text(encoding="utf-8"))],
        "major_summary": load_csv_rows(package_dir / "major_loss_summary.csv"),
        "major_cumulative": load_csv_rows(package_dir / "major_loss_cumulative_timeseries.csv"),
        "major_raw": load_csv_rows(raw_dir / "leg_major_loss_timeseries.csv"),
        "bulk_cross_section_rows": load_csv_rows(raw_dir / "bulk_cross_section_temperature_samples.csv"),
        "station_defs": load_csv_rows(raw_dir / "leg_centerline_station_definitions.csv"),
        "feature_summary": load_csv_rows(package_dir / "feature_minor_loss_summary.csv"),
        "feature_timeseries": load_csv_rows(raw_dir / "feature_minor_loss_timeseries.csv"),
        "feature_patch_timeseries": load_csv_rows(raw_dir / "feature_patch_pressure_timeseries.csv"),
        "boundary_summary": load_csv_rows(package_dir / "boundary_layer_landmark_summary.csv"),
        "boundary_profiles": load_csv_rows(raw_dir / "boundary_layer_landmark_profiles.csv"),
        "azimuthal_summary": load_csv_rows(raw_dir / "azimuthal_wall_transport_summary.csv"),
        "streamwise_heat": load_csv_rows(package_dir / "streamwise_heat_loss_summary.csv"),
        "branch_thermal": load_csv_rows(package_dir / "branch_thermal_summary.csv"),
    }


def bulk_cross_section_lookup(rows: list[dict[str, str]]) -> dict[tuple[float, str, int], dict[str, str]]:
    lookup: dict[tuple[float, str, int], dict[str, str]] = {}
    for row in rows:
        time_s = finite_float(row.get("time_s"))
        if not math.isfinite(time_s):
            continue
        lookup[(time_s, str(row["span_name"]), int(row["bin_index"]))] = row
    return lookup


def compute_cross_section_region_payload_general(
    component_indices: list[int],
    faces: list[list[int]],
    points: list[np.ndarray],
    face_t_values: list[float],
    face_u_values: list[np.ndarray],
    plane_normal: np.ndarray,
    rho_coeffs: list[float],
    cp_coeffs: list[float],
    flow_direction_sign_hint: float,
    reference_area_m2: float,
) -> dict[str, Any]:
    face_areas: list[float] = []
    area_weighted_temp_numerator = 0.0
    signed_mass_flux_kg_s = 0.0
    aligned_signed_mass_flux_kg_s = 0.0
    positive_aligned_mass_flux_kg_s = 0.0
    flow_weighted_temp_numerator = 0.0
    cp_flow_weighted_temp_numerator = 0.0
    cp_flow_weighted_denom = 0.0
    for face_index in component_indices:
        point_coords = [points[point_id] for point_id in faces[face_index]]
        area_vector = major_extractor.face_area_vector(point_coords)
        if float(np.dot(area_vector, plane_normal)) < 0.0:
            area_vector *= -1.0
        area_m2 = float(np.linalg.norm(area_vector))
        face_temperature = float(face_t_values[face_index])
        face_velocity = np.array(face_u_values[face_index], dtype=float)
        density = float(polynomial_eval(rho_coeffs, face_temperature))
        cp_value = float(polynomial_eval(cp_coeffs, face_temperature))
        normal_velocity = float(np.dot(face_velocity, plane_normal))
        raw_mass_flux = float(density * normal_velocity * area_m2)
        aligned_mass_flux = float(flow_direction_sign_hint * raw_mass_flux)
        positive_aligned_mass_flux = max(0.0, aligned_mass_flux)
        cp_positive_flux = positive_aligned_mass_flux * cp_value
        face_areas.append(area_m2)
        area_weighted_temp_numerator += area_m2 * face_temperature
        signed_mass_flux_kg_s += raw_mass_flux
        aligned_signed_mass_flux_kg_s += aligned_mass_flux
        positive_aligned_mass_flux_kg_s += positive_aligned_mass_flux
        flow_weighted_temp_numerator += positive_aligned_mass_flux * face_temperature
        cp_flow_weighted_temp_numerator += cp_positive_flux * face_temperature
        cp_flow_weighted_denom += cp_positive_flux
    total_area_m2 = float(sum(face_areas))
    area_weighted_temp_k = (
        float(area_weighted_temp_numerator / total_area_m2)
        if total_area_m2 > 0.0
        else math.nan
    )
    flow_weighted_temp_k = (
        float(flow_weighted_temp_numerator / positive_aligned_mass_flux_kg_s)
        if positive_aligned_mass_flux_kg_s > THERMAL_MIN_POSITIVE_FLUX_KG_S
        else math.nan
    )
    cp_flow_weighted_temp_k = (
        float(cp_flow_weighted_temp_numerator / cp_flow_weighted_denom)
        if cp_flow_weighted_denom > THERMAL_MIN_POSITIVE_FLUX_KG_S
        else math.nan
    )
    return {
        "face_count": int(len(component_indices)),
        "area_m2": total_area_m2,
        "reference_area_m2": float(reference_area_m2),
        "area_ratio_to_reference": (
            float(total_area_m2 / reference_area_m2)
            if math.isfinite(reference_area_m2) and reference_area_m2 > 0.0
            else math.nan
        ),
        "area_error_metric": major_extractor.area_error_metric(total_area_m2, reference_area_m2),
        "signed_mass_flux_kg_s": float(signed_mass_flux_kg_s),
        "aligned_signed_mass_flux_kg_s": float(aligned_signed_mass_flux_kg_s),
        "positive_mass_flux_kg_s": float(positive_aligned_mass_flux_kg_s),
        "temp_area_weighted_k": float(area_weighted_temp_k),
        "temp_flow_weighted_k": float(flow_weighted_temp_k),
        "temp_cp_flow_weighted_k": float(cp_flow_weighted_temp_k),
    }


def prepare_cross_section_surface_geometry(
    faces: list[list[int]],
    points: list[np.ndarray],
    plane_normal: np.ndarray,
) -> list[np.ndarray]:
    oriented_face_area_vectors: list[np.ndarray] = []
    for face in faces:
        point_coords = [points[point_id] for point_id in face]
        area_vector = major_extractor.face_area_vector(point_coords)
        if float(np.dot(area_vector, plane_normal)) < 0.0:
            area_vector *= -1.0
        oriented_face_area_vectors.append(area_vector)
    return oriented_face_area_vectors


def compute_cross_section_region_payload_precomputed(
    component_indices: list[int],
    face_area_vectors: list[np.ndarray],
    face_t_values: list[float],
    face_u_values: list[np.ndarray],
    plane_normal: np.ndarray,
    rho_coeffs: list[float],
    cp_coeffs: list[float],
    flow_direction_sign_hint: float,
    reference_area_m2: float,
) -> dict[str, Any]:
    face_areas: list[float] = []
    area_weighted_temp_numerator = 0.0
    signed_mass_flux_kg_s = 0.0
    aligned_signed_mass_flux_kg_s = 0.0
    positive_aligned_mass_flux_kg_s = 0.0
    flow_weighted_temp_numerator = 0.0
    cp_flow_weighted_temp_numerator = 0.0
    cp_flow_weighted_denom = 0.0
    for face_index in component_indices:
        area_vector = face_area_vectors[face_index]
        area_m2 = float(np.linalg.norm(area_vector))
        face_temperature = float(face_t_values[face_index])
        face_velocity = np.array(face_u_values[face_index], dtype=float)
        density = float(polynomial_eval(rho_coeffs, face_temperature))
        cp_value = float(polynomial_eval(cp_coeffs, face_temperature))
        normal_velocity = float(np.dot(face_velocity, plane_normal))
        raw_mass_flux = float(density * normal_velocity * area_m2)
        aligned_mass_flux = float(flow_direction_sign_hint * raw_mass_flux)
        positive_aligned_mass_flux = max(0.0, aligned_mass_flux)
        cp_positive_flux = positive_aligned_mass_flux * cp_value
        face_areas.append(area_m2)
        area_weighted_temp_numerator += area_m2 * face_temperature
        signed_mass_flux_kg_s += raw_mass_flux
        aligned_signed_mass_flux_kg_s += aligned_mass_flux
        positive_aligned_mass_flux_kg_s += positive_aligned_mass_flux
        flow_weighted_temp_numerator += positive_aligned_mass_flux * face_temperature
        cp_flow_weighted_temp_numerator += cp_positive_flux * face_temperature
        cp_flow_weighted_denom += cp_positive_flux
    total_area_m2 = float(sum(face_areas))
    area_weighted_temp_k = (
        float(area_weighted_temp_numerator / total_area_m2)
        if total_area_m2 > 0.0
        else math.nan
    )
    flow_weighted_temp_k = (
        float(flow_weighted_temp_numerator / positive_aligned_mass_flux_kg_s)
        if positive_aligned_mass_flux_kg_s > THERMAL_MIN_POSITIVE_FLUX_KG_S
        else math.nan
    )
    cp_flow_weighted_temp_k = (
        float(cp_flow_weighted_temp_numerator / cp_flow_weighted_denom)
        if cp_flow_weighted_denom > THERMAL_MIN_POSITIVE_FLUX_KG_S
        else math.nan
    )
    return {
        "face_count": int(len(component_indices)),
        "area_m2": total_area_m2,
        "reference_area_m2": float(reference_area_m2),
        "area_ratio_to_reference": (
            float(total_area_m2 / reference_area_m2)
            if math.isfinite(reference_area_m2) and reference_area_m2 > 0.0
            else math.nan
        ),
        "area_error_metric": major_extractor.area_error_metric(total_area_m2, reference_area_m2),
        "signed_mass_flux_kg_s": float(signed_mass_flux_kg_s),
        "aligned_signed_mass_flux_kg_s": float(aligned_signed_mass_flux_kg_s),
        "positive_mass_flux_kg_s": float(positive_aligned_mass_flux_kg_s),
        "temp_area_weighted_k": float(area_weighted_temp_k),
        "temp_flow_weighted_k": float(flow_weighted_temp_k),
        "temp_cp_flow_weighted_k": float(cp_flow_weighted_temp_k),
    }


def build_exact_water_bulk_lookup(
    case: CaseRecord,
    package_rows: dict[str, list[dict[str, str]]],
) -> tuple[dict[tuple[float, str, int], dict[str, Any]], list[dict[str, Any]]]:
    if case.fluid_family != "water":
        return {}, []
    extraction_summary = package_rows["major_extraction_summary"][0]
    extract_case = Path(extraction_summary["extract_case"])
    output_root = extract_case / "postProcessing" / "streamwiseBulkThermal"
    if not output_root.exists():
        return {}, []

    profile = get_case_analysis_profile(case.source_id)
    station_lookup = bulk_cross_section_lookup(package_rows["bulk_cross_section_rows"])
    surface_meta: dict[str, dict[str, Any]] = {}
    reference_area_lookup = extraction_summary.get("mdot_monitor_area_m2_by_span", {})
    for row in package_rows["station_defs"]:
        span_name = str(row["span_name"])
        bin_index = int(row["bin_index"])
        surface_name = f"bulkThermal_{span_name}_bin_{bin_index:04d}"
        surface_meta[surface_name] = {
            "span_name": span_name,
            "bin_index": bin_index,
            "normal": (
                finite_float(row.get("tangent_x")),
                finite_float(row.get("tangent_y")),
                finite_float(row.get("tangent_z")),
            ),
            "flow_direction_sign_hint": float(profile.major_spans[span_name]["flow_direction_sign_hint"]),
            "reference_area_m2": float(finite_float(reference_area_lookup.get(span_name))),
        }

    exact_lookup: dict[tuple[float, str, int], dict[str, Any]] = {}
    comparison_rows: list[dict[str, Any]] = []
    geometry_cache: dict[str, dict[str, Any]] = {}
    for time_dir in sorted(output_root.iterdir(), key=lambda item: finite_float(item.name, default=-1.0)):
        if not time_dir.is_dir():
            continue
        time_s = finite_float(time_dir.name)
        if not math.isfinite(time_s):
            continue
        for surface_name, meta in surface_meta.items():
            surface_dir = time_dir / surface_name
            points_path = surface_dir / "points"
            faces_path = surface_dir / "faces"
            t_path = surface_dir / "scalarField" / "T"
            u_path = surface_dir / "vectorField" / "U"
            if not points_path.exists() or not faces_path.exists() or not t_path.exists() or not u_path.exists():
                continue
            cached_geometry = geometry_cache.get(surface_name)
            if cached_geometry is None:
                points = major_extractor.load_full_points(points_path)
                faces = major_extractor.load_full_faces(faces_path)
                plane_normal = np.array(meta["normal"], dtype=float)
                plane_norm = float(np.linalg.norm(plane_normal))
                if plane_norm <= 0.0:
                    continue
                plane_normal /= plane_norm
                cached_geometry = {
                    "points": points,
                    "faces": faces,
                    "components": major_extractor.build_connected_face_components(faces),
                    "plane_normal": plane_normal,
                    "face_area_vectors": prepare_cross_section_surface_geometry(faces, points, plane_normal),
                }
                geometry_cache[surface_name] = cached_geometry
            points = cached_geometry["points"]
            faces = cached_geometry["faces"]
            point_t_values = major_extractor.load_full_scalar_field(t_path)
            point_u_values = major_extractor.load_full_vector_field(u_path)
            face_t_values = [float(value) for value in major_extractor.face_sample_values(point_t_values, faces, points, "T")]
            face_u_values = [
                np.array(value, dtype=float) for value in major_extractor.face_sample_values(point_u_values, faces, points, "U")
            ]
            plane_normal = cached_geometry["plane_normal"]
            components = cached_geometry["components"]
            face_area_vectors = cached_geometry["face_area_vectors"]
            regions = [
                compute_cross_section_region_payload_precomputed(
                    component_indices,
                    face_area_vectors,
                    face_t_values,
                    face_u_values,
                    plane_normal,
                    case.rho_coeffs,
                    case.cp_coeffs,
                    float(meta["flow_direction_sign_hint"]),
                    float(meta["reference_area_m2"]),
                )
                for component_indices in components
            ]
            chosen_region, selection_status = major_extractor.select_cross_section_region(regions)
            if chosen_region is None:
                continue
            key = (time_s, str(meta["span_name"]), int(meta["bin_index"]))
            stored_row = station_lookup.get(key, {})
            exact_lookup[key] = {
                "bulk_temp_exact_cp_weighted_k": float(chosen_region["temp_cp_flow_weighted_k"]),
                "bulk_temp_exact_flow_weighted_k": float(chosen_region["temp_flow_weighted_k"]),
                "bulk_temp_exact_area_weighted_k": float(chosen_region["temp_area_weighted_k"]),
                "selection_status": selection_status,
                "positive_mass_flux_kg_s": float(chosen_region["positive_mass_flux_kg_s"]),
                "area_ratio_to_reference": float(chosen_region["area_ratio_to_reference"]),
            }
            stored_flow = finite_float(stored_row.get("bulk_temp_flow_weighted_k"))
            stored_area = finite_float(stored_row.get("bulk_temp_area_avg_k"))
            exact_cp = float(chosen_region["temp_cp_flow_weighted_k"])
            exact_flow = float(chosen_region["temp_flow_weighted_k"])
            exact_area = float(chosen_region["temp_area_weighted_k"])
            comparison_rows.append(
                {
                    "source_id": case.source_id,
                    "case_label": case.case_label,
                    "time_s": time_s,
                    "span_name": meta["span_name"],
                    "bin_index": meta["bin_index"],
                    "selection_status": selection_status,
                    "stored_bulk_temp_flow_weighted_k": stored_flow,
                    "stored_bulk_temp_area_weighted_k": stored_area,
                    "exact_bulk_temp_flow_weighted_k": exact_flow,
                    "exact_bulk_temp_cp_weighted_k": exact_cp,
                    "exact_bulk_temp_area_weighted_k": exact_area,
                    "delta_exact_minus_stored_flow_k": exact_cp - stored_flow
                    if math.isfinite(exact_cp) and math.isfinite(stored_flow)
                    else math.nan,
                    "delta_exact_flow_minus_stored_flow_k": exact_flow - stored_flow
                    if math.isfinite(exact_flow) and math.isfinite(stored_flow)
                    else math.nan,
                    "delta_exact_cp_minus_exact_flow_k": exact_cp - exact_flow
                    if math.isfinite(exact_cp) and math.isfinite(exact_flow)
                    else math.nan,
                }
            )
    return exact_lookup, comparison_rows


def summarize_water_bulk_comparison(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["source_id"])].append(row)

    summary_rows: list[dict[str, Any]] = []
    for source_id, payload in sorted(grouped.items()):
        deltas_cp = [
            float(row["delta_exact_minus_stored_flow_k"])
            for row in payload
            if math.isfinite(float(row["delta_exact_minus_stored_flow_k"]))
        ]
        deltas_flow = [
            float(row["delta_exact_flow_minus_stored_flow_k"])
            for row in payload
            if math.isfinite(float(row["delta_exact_flow_minus_stored_flow_k"]))
        ]
        delta_cp_minus_flow = [
            float(row["delta_exact_cp_minus_exact_flow_k"])
            for row in payload
            if math.isfinite(float(row["delta_exact_cp_minus_exact_flow_k"]))
        ]
        selection_status_counts: dict[str, int] = defaultdict(int)
        for row in payload:
            selection_status_counts[str(row["selection_status"])] += 1
        case_label = str(payload[0]["case_label"]) if payload else source_id
        summary_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label,
                "comparison_row_count": len(payload),
                "mean_exact_cp_minus_stored_flow_k": safe_mean(deltas_cp),
                "max_abs_exact_cp_minus_stored_flow_k": max((abs(value) for value in deltas_cp), default=math.nan),
                "mean_exact_flow_minus_stored_flow_k": safe_mean(deltas_flow),
                "max_abs_exact_flow_minus_stored_flow_k": max((abs(value) for value in deltas_flow), default=math.nan),
                "mean_exact_cp_minus_exact_flow_k": safe_mean(delta_cp_minus_flow),
                "max_abs_exact_cp_minus_exact_flow_k": max((abs(value) for value in delta_cp_minus_flow), default=math.nan),
                "selection_status_counts": "|".join(
                    f"{status}:{count}" for status, count in sorted(selection_status_counts.items())
                ),
            }
        )
    return summary_rows


def build_station_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, int], dict[str, float]]:
    lookup: dict[tuple[str, int], dict[str, float]] = {}
    for row in rows:
        key = (str(row["span_name"]), int(row["bin_index"]))
        s_start = finite_float(row.get("s_start_m"))
        s_end = finite_float(row.get("s_end_m"))
        lookup[key] = {
            "s_start_m": s_start,
            "s_end_m": s_end,
            "bin_width_m": max(0.0, s_end - s_start),
            "tangent_x": finite_float(row.get("tangent_x")),
            "tangent_y": finite_float(row.get("tangent_y")),
            "tangent_z": finite_float(row.get("tangent_z")),
        }
    return lookup


def build_major_row_groups(rows: list[dict[str, str]]) -> dict[tuple[float, str], list[dict[str, Any]]]:
    grouped: dict[tuple[float, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        time_s = finite_float(row.get("time_s"))
        if not math.isfinite(time_s):
            continue
        span_name = str(row["span_name"])
        grouped[(time_s, span_name)].append(row)
    for key in grouped:
        grouped[key].sort(key=lambda item: int(item["bin_index"]))
    return grouped


def weighted_section_scalars(rows: list[dict[str, Any]]) -> dict[str, float]:
    def weight(row: dict[str, Any]) -> float:
        return max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m")))

    return {
        "rho_bulk_kg_m3": safe_weighted_mean((finite_float(row.get("rho_bulk_kg_m3")), weight(row)) for row in rows),
        "bulk_velocity_m_s": safe_weighted_mean((finite_float(row.get("bulk_velocity_m_s")), weight(row)) for row in rows),
        "hydraulic_diameter_geom_m": safe_weighted_mean(
            (finite_float(row.get("hydraulic_diameter_geom_m")), weight(row)) for row in rows
        ),
        "mdot_mean_abs_kg_s": safe_weighted_mean((finite_float(row.get("mdot_mean_abs_kg_s")), weight(row)) for row in rows),
        "section_length_m": sum(weight(row) for row in rows if math.isfinite(weight(row))),
    }


def flow_ordered_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], float]:
    valid = [row for row in rows if is_finite_number(row.get("p_wall_area_avg_pa")) and is_finite_number(row.get("p_rgh_wall_area_avg_pa"))]
    if not valid:
        return [], math.nan
    flow_sign = finite_float(valid[0].get("flow_alignment_sign"))
    ordered = list(valid)
    if flow_sign < 0.0:
        ordered.reverse()
    return ordered, flow_sign


def section_core_rows(rows: list[dict[str, Any]], dh_mean: float, section_length_m: float) -> list[dict[str, Any]]:
    if not math.isfinite(dh_mean) or dh_mean <= 0.0 or not math.isfinite(section_length_m) or section_length_m <= 0.0:
        return []
    exclusion_m = max(2.0 * dh_mean, 0.05 * section_length_m)
    core: list[dict[str, Any]] = []
    for row in rows:
        s0 = finite_float(row.get("s_start_m"))
        s1 = finite_float(row.get("s_end_m"))
        smid = 0.5 * (s0 + s1)
        if smid < exclusion_m or smid > (section_length_m - exclusion_m):
            continue
        core.append(row)
    return core


def build_pressure_section_rows(
    case: CaseRecord,
    rows: list[dict[str, str]],
    station_lookup: dict[tuple[str, int], dict[str, float]],
) -> list[dict[str, Any]]:
    grouped = build_major_row_groups(rows)
    span_payloads: dict[str, list[dict[str, Any]]] = defaultdict(list)
    loop_rho_samples: list[tuple[float, float]] = []
    loop_u_samples: list[tuple[float, float]] = []

    for (time_s, span_name), time_rows in grouped.items():
        merged_rows: list[dict[str, Any]] = []
        for row in time_rows:
            key = (span_name, int(row["bin_index"]))
            station = station_lookup.get(key, {})
            merged_rows.append({**row, **station})
        ordered_rows, flow_sign = flow_ordered_rows(merged_rows)
        if not ordered_rows:
            continue
        stats = weighted_section_scalars(ordered_rows)
        section_length_m = stats["section_length_m"]
        rho_mean = stats["rho_bulk_kg_m3"]
        u_mean = stats["bulk_velocity_m_s"]
        dh_mean = stats["hydraulic_diameter_geom_m"]
        local_q = 0.5 * rho_mean * u_mean * u_mean if math.isfinite(rho_mean) and math.isfinite(u_mean) else math.nan

        p_start = finite_float(ordered_rows[0].get("p_wall_area_avg_pa"))
        p_end = finite_float(ordered_rows[-1].get("p_wall_area_avg_pa"))
        prgh_start = finite_float(ordered_rows[0].get("p_rgh_wall_area_avg_pa"))
        prgh_end = finite_float(ordered_rows[-1].get("p_rgh_wall_area_avg_pa"))
        pressure_drop_p = p_start - p_end
        pressure_drop_prgh_endpoint = prgh_start - prgh_end

        g_vec = np.array(case.gravity_vec, dtype=float)
        hydro_integral = 0.0
        prgh_integrated = 0.0
        p_integrated = 0.0
        for row in ordered_rows:
            ds = max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m")))
            tangent = np.array(
                [
                    finite_float(row.get("tangent_x")),
                    finite_float(row.get("tangent_y")),
                    finite_float(row.get("tangent_z")),
                ],
                dtype=float,
            )
            if not np.all(np.isfinite(tangent)) or np.linalg.norm(tangent) <= 0.0:
                continue
            tangent = tangent / np.linalg.norm(tangent)
            tangent_flow = float(flow_sign) * tangent
            hydro_integral += finite_float(row.get("rho_bulk_kg_m3")) * float(np.dot(g_vec, tangent_flow)) * ds
            prgh_integrated += finite_float(row.get("dp_major_gradient_direct_prgh_pa_per_m")) * ds
            p_integrated += finite_float(row.get("dp_major_gradient_direct_p_pa_per_m")) * ds
        pressure_loss_hydro = pressure_drop_p + hydro_integral
        residual_vs_prgh_endpoint = pressure_loss_hydro - pressure_drop_prgh_endpoint
        residual_vs_prgh_integrated = pressure_loss_hydro - prgh_integrated
        apparent_darcy_local = (
            pressure_loss_hydro * 2.0 * dh_mean / (local_q * section_length_m)
            if math.isfinite(local_q) and local_q > 0.0 and math.isfinite(dh_mean) and math.isfinite(section_length_m) and section_length_m > 0.0
            else math.nan
        )
        core_rows = section_core_rows(ordered_rows, dh_mean, section_length_m)
        core_shear = safe_weighted_mean(
            (
                finite_float(row.get("darcy_f")),
                max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m"))),
            )
            for row in core_rows
        )
        mean_thermal_support_usable_fraction = safe_mean(
            1.0 if str(row.get("thermal_support_status", "")) == "usable" else 0.0 for row in ordered_rows
        )
        span_payloads[span_name].append(
            {
                "source_id": case.source_id,
                "case_label": case.case_label,
                "family": case.fluid_family,
                "profile_name": case.profile_name,
                "time_s": time_s,
                "span_name": span_name,
                "span_kind": str(ordered_rows[0].get("span_kind", "")),
                "flow_alignment_sign": flow_sign,
                "section_length_m": section_length_m,
                "pressure_drop_p_pa": pressure_drop_p,
                "hydro_integral_pa": hydro_integral,
                "pressure_loss_hydro_pa": pressure_loss_hydro,
                "pressure_loss_prgh_endpoint_pa": pressure_drop_prgh_endpoint,
                "pressure_loss_prgh_integrated_pa": prgh_integrated,
                "pressure_drop_p_integrated_pa": p_integrated,
                "pressure_closure_residual_vs_prgh_endpoint_pa": residual_vs_prgh_endpoint,
                "pressure_closure_residual_vs_prgh_integrated_pa": residual_vs_prgh_integrated,
                "rho_bulk_kg_m3": rho_mean,
                "bulk_velocity_m_s": u_mean,
                "hydraulic_diameter_geom_m": dh_mean,
                "mdot_mean_abs_kg_s": stats["mdot_mean_abs_kg_s"],
                "dynamic_head_local_pa": local_q,
                "apparent_darcy_f_local": apparent_darcy_local,
                "direct_prgh_darcy_existing": safe_weighted_mean(
                    (
                        finite_float(row.get("darcy_f_pressure_drop_prgh")),
                        max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m"))),
                    )
                    for row in ordered_rows
                ),
                "shear_darcy_core": core_shear,
                "direct_prgh_gradient_pa_per_m": safe_weighted_mean(
                    (
                        finite_float(row.get("dp_major_gradient_direct_prgh_pa_per_m")),
                        max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m"))),
                    )
                    for row in ordered_rows
                ),
                "direct_p_gradient_pa_per_m": safe_weighted_mean(
                    (
                        finite_float(row.get("dp_major_gradient_direct_p_pa_per_m")),
                        max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m"))),
                    )
                    for row in ordered_rows
                ),
                "thermal_support_usable_fraction": mean_thermal_support_usable_fraction,
                "straight_section_flag": "yes" if str(ordered_rows[0].get("span_kind", "")) == "main_loop_leg" else "no",
            }
        )
        if str(ordered_rows[0].get("span_kind", "")) == "main_loop_leg" and math.isfinite(rho_mean) and math.isfinite(u_mean):
            loop_rho_samples.append((rho_mean, section_length_m))
            loop_u_samples.append((u_mean, section_length_m))

    rho_loop_ref = safe_weighted_mean(loop_rho_samples)
    u_loop_ref = safe_weighted_mean(loop_u_samples)
    q_loop_ref = 0.5 * rho_loop_ref * u_loop_ref * u_loop_ref if math.isfinite(rho_loop_ref) and math.isfinite(u_loop_ref) else math.nan

    section_rows: list[dict[str, Any]] = []
    for span_name, payloads in span_payloads.items():
        section_length_m = safe_mean(float(row["section_length_m"]) for row in payloads)
        dh_mean = safe_mean(float(row["hydraulic_diameter_geom_m"]) for row in payloads)
        hydro_loss = safe_mean(float(row["pressure_loss_hydro_pa"]) for row in payloads)
        apparent_darcy_loop_ref = (
            hydro_loss * 2.0 * dh_mean / (q_loop_ref * section_length_m)
            if math.isfinite(q_loop_ref) and q_loop_ref > 0.0 and math.isfinite(section_length_m) and section_length_m > 0.0 and math.isfinite(dh_mean)
            else math.nan
        )
        sample = payloads[0]
        section_rows.append(
            {
                "source_id": case.source_id,
                "case_label": case.case_label,
                "family": case.fluid_family,
                "profile_name": case.profile_name,
                "span_name": span_name,
                "span_kind": sample["span_kind"],
                "straight_section_flag": sample["straight_section_flag"],
                "time_sample_count": len(payloads),
                "section_length_m": section_length_m,
                "mean_rho_bulk_kg_m3": safe_mean(float(row["rho_bulk_kg_m3"]) for row in payloads),
                "mean_bulk_velocity_m_s": safe_mean(float(row["bulk_velocity_m_s"]) for row in payloads),
                "mean_mdot_mean_abs_kg_s": safe_mean(float(row["mdot_mean_abs_kg_s"]) for row in payloads),
                "mean_hydraulic_diameter_geom_m": dh_mean,
                "mean_dynamic_head_local_pa": safe_mean(float(row["dynamic_head_local_pa"]) for row in payloads),
                "loop_reference_dynamic_head_pa": q_loop_ref,
                "mean_pressure_drop_p_pa": safe_mean(float(row["pressure_drop_p_pa"]) for row in payloads),
                "mean_hydro_integral_pa": safe_mean(float(row["hydro_integral_pa"]) for row in payloads),
                "mean_pressure_loss_hydro_pa": hydro_loss,
                "mean_pressure_loss_prgh_endpoint_pa": safe_mean(
                    float(row["pressure_loss_prgh_endpoint_pa"]) for row in payloads
                ),
                "mean_pressure_loss_prgh_integrated_pa": safe_mean(
                    float(row["pressure_loss_prgh_integrated_pa"]) for row in payloads
                ),
                "mean_pressure_closure_residual_vs_prgh_endpoint_pa": safe_mean(
                    float(row["pressure_closure_residual_vs_prgh_endpoint_pa"]) for row in payloads
                ),
                "mean_pressure_closure_residual_vs_prgh_integrated_pa": safe_mean(
                    float(row["pressure_closure_residual_vs_prgh_integrated_pa"]) for row in payloads
                ),
                "mean_apparent_darcy_f_local": safe_mean(float(row["apparent_darcy_f_local"]) for row in payloads),
                "mean_apparent_darcy_f_loop_ref": apparent_darcy_loop_ref,
                "mean_direct_prgh_darcy_existing": safe_mean(float(row["direct_prgh_darcy_existing"]) for row in payloads),
                "mean_shear_darcy_core": safe_mean(float(row["shear_darcy_core"]) for row in payloads),
                "mean_direct_prgh_gradient_pa_per_m": safe_mean(
                    float(row["direct_prgh_gradient_pa_per_m"]) for row in payloads
                ),
                "mean_direct_p_gradient_pa_per_m": safe_mean(float(row["direct_p_gradient_pa_per_m"]) for row in payloads),
                "mean_thermal_support_usable_fraction": safe_mean(
                    float(row["thermal_support_usable_fraction"]) for row in payloads
                ),
            }
        )
    return section_rows


def build_case_pressure_summary(section_rows: list[dict[str, Any]], major_rows: list[dict[str, str]]) -> dict[str, Any]:
    loop_rows = [row for row in section_rows if row["span_kind"] in {"main_loop_leg", "test_section_leg"}]
    straight_rows = [row for row in section_rows if row["straight_section_flag"] == "yes"]
    p_values = [finite_float(row.get("p_wall_area_avg_pa")) for row in major_rows if is_finite_number(row.get("p_wall_area_avg_pa"))]
    prgh_values = [
        finite_float(row.get("p_rgh_wall_area_avg_pa")) for row in major_rows if is_finite_number(row.get("p_rgh_wall_area_avg_pa"))
    ]
    hydro_proxy_values = []
    for row in major_rows:
        p_value = finite_float(row.get("p_wall_area_avg_pa"))
        prgh_value = finite_float(row.get("p_rgh_wall_area_avg_pa"))
        if math.isfinite(p_value) and math.isfinite(prgh_value):
            hydro_proxy_values.append(p_value - prgh_value)
    return {
        "loop_total_pressure_loss_hydro_pa": sum(
            float(row["mean_pressure_loss_hydro_pa"])
            for row in loop_rows
            if math.isfinite(float(row["mean_pressure_loss_hydro_pa"]))
        ),
        "loop_total_pressure_loss_prgh_pa": sum(
            float(row["mean_pressure_loss_prgh_integrated_pa"])
            for row in loop_rows
            if math.isfinite(float(row["mean_pressure_loss_prgh_integrated_pa"]))
        ),
        "straight_pipe_total_pressure_loss_hydro_pa": sum(
            float(row["mean_pressure_loss_hydro_pa"])
            for row in straight_rows
            if math.isfinite(float(row["mean_pressure_loss_hydro_pa"]))
        ),
        "max_section_pressure_loss_hydro_pa": max(
            (finite_float(row.get("mean_pressure_loss_hydro_pa")) for row in loop_rows if is_finite_number(row.get("mean_pressure_loss_hydro_pa"))),
            default=math.nan,
        ),
        "max_wall_p_range_pa": (max(p_values) - min(p_values)) if p_values else math.nan,
        "max_wall_prgh_range_pa": (max(prgh_values) - min(prgh_values)) if prgh_values else math.nan,
        "max_hydro_head_proxy_range_pa": (max(hydro_proxy_values) - min(hydro_proxy_values)) if hydro_proxy_values else math.nan,
    }


def build_feature_rows(case: CaseRecord, feature_summary_rows: list[dict[str, str]], section_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    section_map = {row["span_name"]: row for row in section_rows}
    profile = get_case_analysis_profile(case.source_id)
    payloads: list[dict[str, Any]] = []
    for row in feature_summary_rows:
        feature_name = str(row["feature_name"])
        adjacent_spans = profile.feature_budgets[feature_name]["adjacent_major_spans"]
        q_refs = [
            finite_float(section_map[span_name].get("mean_dynamic_head_local_pa"))
            for span_name in adjacent_spans
            if span_name in section_map
        ]
        q_ref = safe_mean(q_refs)
        residual = finite_float(row.get("mean_minor_residual_dp_pa"))
        explicit_feature_loss = finite_float(row.get("mean_abs_delta_p_rgh_pa"))
        keff = residual / q_ref if math.isfinite(residual) and math.isfinite(q_ref) and q_ref > 0.0 else math.nan
        payloads.append(
            {
                "source_id": case.source_id,
                "case_label": case.case_label,
                "family": case.fluid_family,
                "feature_name": feature_name,
                "feature_kind": row["feature_kind"],
                "adjacent_major_spans": "|".join(adjacent_spans),
                "reference_length_m": finite_float(row.get("reference_length_m")),
                "mean_feature_loss_prgh_pa": explicit_feature_loss,
                "mean_reference_major_dp_pa": finite_float(row.get("mean_reference_major_dp_pa")),
                "mean_feature_residual_dp_pa": residual,
                "mean_dynamic_head_reference_pa": q_ref,
                "mean_keff_reference": keff,
                "warning_fraction": finite_float(row.get("warning_fraction")),
                "time_sample_count": int(float(row.get("time_sample_count", "0"))),
            }
        )
    return payloads


def bulk_temperature_method(case: CaseRecord, *, exact_water_cp_weighted: bool = False) -> str:
    if case.fluid_family == "salt":
        return "stored bulk temperature is exact for the requested rho*u*cp weighting because Cp is constant in the case_config"
    if exact_water_cp_weighted:
        return (
            "bulk temperature is recomputed additively from preserved cut-plane surfaces using the water rho(T) and cp(T) polynomials, "
            "with the same connected-region support logic but cp-weighted positive aligned mass-flux averaging"
        )
    return (
        "stored bulk temperature is the June 15 mass-flux-weighted cut-plane value; exact rho*u*cp reweighting is still a follow-on for water because per-face cp-weighted cut-plane samples were not retained"
    )


def resolved_bulk_temperature(
    case: CaseRecord,
    exact_water_lookup: dict[tuple[float, str, int], dict[str, Any]],
    time_s: float,
    span_name: str,
    bin_index: int,
    stored_bulk_temp_k: float,
) -> tuple[float, str]:
    exact = exact_water_lookup.get((time_s, span_name, bin_index))
    if case.fluid_family == "water" and exact is not None and math.isfinite(float(exact["bulk_temp_exact_cp_weighted_k"])):
        return float(exact["bulk_temp_exact_cp_weighted_k"]), bulk_temperature_method(case, exact_water_cp_weighted=True)
    return stored_bulk_temp_k, bulk_temperature_method(case, exact_water_cp_weighted=False)


def build_htc_field_rows(
    case: CaseRecord,
    azimuthal_rows: list[dict[str, str]],
    major_rows: list[dict[str, str]],
    exact_water_lookup: dict[tuple[float, str, int], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    major_lookup: dict[tuple[float, str, int], dict[str, str]] = {}
    for row in major_rows:
        time_s = finite_float(row.get("time_s"))
        if not math.isfinite(time_s):
            continue
        major_lookup[(time_s, str(row["span_name"]), int(row["bin_index"]))] = row

    field_rows: list[dict[str, Any]] = []
    section_groups: dict[tuple[str, float, str], list[dict[str, Any]]] = defaultdict(list)
    for row in azimuthal_rows:
        time_s = finite_float(row.get("time_s"))
        if not math.isfinite(time_s):
            continue
        span_name = str(row["span_name"])
        bin_index = int(row["streamwise_bin_index"])
        major = major_lookup.get((time_s, span_name, bin_index))
        if major is None:
            continue
        stored_t_bulk = finite_float(major.get("bulk_temp_fluid_area_avg_k"))
        t_bulk, bulk_method = resolved_bulk_temperature(case, exact_water_lookup, time_s, span_name, bin_index, stored_t_bulk)
        exact_payload = exact_water_lookup.get((time_s, span_name, bin_index), {})
        t_wall = finite_float(row.get("mean_t_wall_k"))
        q_wall = finite_float(row.get("mean_wall_heat_flux_w_m2"))
        area = finite_float(row.get("area_m2"))
        dh = finite_float(major.get("hydraulic_diameter_geom_m"))
        delta_t = t_wall - t_bulk
        k_bulk = polynomial_eval(case.k_coeffs, t_bulk) if math.isfinite(t_bulk) else math.nan
        h_signed = q_wall / delta_t if math.isfinite(q_wall) and math.isfinite(delta_t) and abs(delta_t) >= THERMAL_MIN_ABS_DELTA_T_K else math.nan
        nu_signed = h_signed * dh / k_bulk if math.isfinite(h_signed) and math.isfinite(dh) and math.isfinite(k_bulk) and abs(k_bulk) > 0.0 else math.nan
        field_row = {
            "source_id": case.source_id,
            "case_label": case.case_label,
            "family": case.fluid_family,
            "time_s": time_s,
            "span_name": span_name,
            "streamwise_bin_index": bin_index,
            "theta_bin_index": int(row["theta_bin_index"]),
            "theta_bin_center_deg": finite_float(row.get("theta_bin_center_deg")),
            "area_m2": area,
            "thermal_role": row["thermal_role"],
            "thermal_role_group": row["thermal_role_group"],
            "t_wall_k": t_wall,
            "stored_t_bulk_k": stored_t_bulk,
            "t_bulk_k": t_bulk,
            "delta_t_wall_minus_bulk_k": delta_t,
            "wall_heat_flux_w_m2": q_wall,
            "hydraulic_diameter_geom_m": dh,
            "k_bulk_w_m_k": k_bulk,
            "h_local_signed_w_m2_k": h_signed,
            "nu_local_signed": nu_signed,
            "thermal_support_status": major.get("thermal_support_status", ""),
            "bulk_temperature_method": bulk_method,
            "bulk_reweight_delta_k": t_bulk - stored_t_bulk
            if math.isfinite(t_bulk) and math.isfinite(stored_t_bulk)
            else math.nan,
            "exact_flow_weighted_t_bulk_k": float(exact_payload["bulk_temp_exact_flow_weighted_k"])
            if exact_payload
            else math.nan,
        }
        field_rows.append(field_row)
        section_groups[(span_name, time_s, case.source_id)].append(field_row)

    section_rows: list[dict[str, Any]] = []
    for (span_name, time_s, _source_id), payload in section_groups.items():
        area_total = sum(float(row["area_m2"]) for row in payload if math.isfinite(float(row["area_m2"])))
        q_integral = sum(
            float(row["wall_heat_flux_w_m2"]) * float(row["area_m2"])
            for row in payload
            if math.isfinite(float(row["wall_heat_flux_w_m2"])) and math.isfinite(float(row["area_m2"]))
        )
        delta_t_integral = sum(
            float(row["delta_t_wall_minus_bulk_k"]) * float(row["area_m2"])
            for row in payload
            if math.isfinite(float(row["delta_t_wall_minus_bulk_k"])) and math.isfinite(float(row["area_m2"]))
        )
        h_area_ratio = q_integral / delta_t_integral if abs(delta_t_integral) > 0.0 else math.nan
        dh_mean = safe_weighted_mean((float(row["hydraulic_diameter_geom_m"]), float(row["area_m2"])) for row in payload)
        k_bulk_mean = safe_weighted_mean((float(row["k_bulk_w_m_k"]), float(row["area_m2"])) for row in payload)
        nu_area_ratio = h_area_ratio * dh_mean / k_bulk_mean if math.isfinite(h_area_ratio) and math.isfinite(dh_mean) and math.isfinite(k_bulk_mean) and abs(k_bulk_mean) > 0.0 else math.nan
        section_rows.append(
            {
                "source_id": case.source_id,
                "case_label": case.case_label,
                "family": case.fluid_family,
                "time_s": time_s,
                "span_name": span_name,
                "theta_bin_count": len(payload),
                "wall_area_total_m2": area_total,
                "wall_heat_integral_w": q_integral,
                "delta_t_wall_minus_bulk_integral_k_m2": delta_t_integral,
                "h_area_ratio_signed_w_m2_k": h_area_ratio,
                "nu_area_ratio_signed": nu_area_ratio,
                "bulk_temperature_method": payload[0]["bulk_temperature_method"] if payload else bulk_temperature_method(case),
                "mean_bulk_reweight_delta_k": safe_mean(float(row["bulk_reweight_delta_k"]) for row in payload),
            }
        )
    return field_rows, section_rows


def build_enthalpy_rows(
    case: CaseRecord,
    major_rows: list[dict[str, str]],
    streamwise_heat_rows: list[dict[str, str]],
    exact_water_lookup: dict[tuple[float, str, int], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups = build_major_row_groups(major_rows)
    streamwise_groups: dict[tuple[float, str], list[dict[str, str]]] = defaultdict(list)
    for row in streamwise_heat_rows:
        key = (finite_float(row.get("time_sample_count"), default=math.nan), str(row["span_name"]))
        streamwise_groups[key].append(row)
    profile = get_case_analysis_profile(case.source_id)
    leg_rows: list[dict[str, Any]] = []
    per_case_rows: list[dict[str, Any]] = []

    for (time_s, span_name), rows in groups.items():
        ordered_rows, _flow_sign = flow_ordered_rows(rows)
        if not ordered_rows:
            continue
        start_row = ordered_rows[0]
        end_row = ordered_rows[-1]
        stored_t_in = finite_float(start_row.get("bulk_temp_fluid_area_avg_k"))
        stored_t_out = finite_float(end_row.get("bulk_temp_fluid_area_avg_k"))
        t_in, bulk_method = resolved_bulk_temperature(
            case,
            exact_water_lookup,
            finite_float(start_row.get("time_s")),
            span_name,
            int(start_row["bin_index"]),
            stored_t_in,
        )
        t_out, _bulk_method_out = resolved_bulk_temperature(
            case,
            exact_water_lookup,
            finite_float(end_row.get("time_s")),
            span_name,
            int(end_row["bin_index"]),
            stored_t_out,
        )
        mdot = safe_mean(finite_float(row.get("mdot_mean_abs_kg_s")) for row in ordered_rows)
        t_mean = safe_mean([t_in, t_out])
        cp_bulk = polynomial_eval(case.cp_coeffs, t_mean) if math.isfinite(t_mean) else math.nan
        enthalpy_delta = mdot * cp_bulk * (t_out - t_in) if math.isfinite(mdot) and math.isfinite(cp_bulk) and math.isfinite(t_in) and math.isfinite(t_out) else math.nan
        wall_heat_total = sum(
            finite_float(row.get("wall_heat_per_length_w_m")) * max(0.0, finite_float(row.get("s_end_m")) - finite_float(row.get("s_start_m")))
            for row in ordered_rows
            if is_finite_number(row.get("wall_heat_per_length_w_m"))
        )
        leg_rows.append(
            {
                "source_id": case.source_id,
                "case_label": case.case_label,
                "family": case.fluid_family,
                "span_name": span_name,
                "span_kind": profile.major_spans[span_name]["kind"],
                "time_s": time_s,
                "mdot_mean_abs_kg_s": mdot,
                "cp_bulk_j_kg_k": cp_bulk,
                "stored_t_bulk_in_k": stored_t_in,
                "stored_t_bulk_out_k": stored_t_out,
                "t_bulk_in_k": t_in,
                "t_bulk_out_k": t_out,
                "enthalpy_change_w": enthalpy_delta,
                "wall_heat_total_w": wall_heat_total,
                "enthalpy_minus_wall_heat_w": enthalpy_delta - wall_heat_total if math.isfinite(enthalpy_delta) and math.isfinite(wall_heat_total) else math.nan,
                "bulk_temperature_method": bulk_method,
            }
        )

    grouped_case_by_time: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in leg_rows:
        grouped_case_by_time[(row["source_id"], float(row["time_s"]))].append(row)

    per_time_rows: list[dict[str, Any]] = []
    for (source_id, time_s), payload in grouped_case_by_time.items():
        per_time_rows.append(
            {
                "source_id": source_id,
                "time_s": time_s,
                "enthalpy_change_w": sum(
                    float(row["enthalpy_change_w"]) for row in payload if math.isfinite(float(row["enthalpy_change_w"]))
                ),
                "wall_heat_total_w": sum(
                    float(row["wall_heat_total_w"]) for row in payload if math.isfinite(float(row["wall_heat_total_w"]))
                ),
                "enthalpy_minus_wall_heat_w": sum(
                    float(row["enthalpy_minus_wall_heat_w"])
                    for row in payload
                    if math.isfinite(float(row["enthalpy_minus_wall_heat_w"]))
                ),
                "leg_count": len(payload),
            }
        )

    grouped_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in per_time_rows:
        grouped_case[row["source_id"]].append(row)

    for source_id, payload in grouped_case.items():
        per_case_rows.append(
            {
                "source_id": source_id,
                "case_label": case.case_label,
                "family": case.fluid_family,
                "time_sample_count": len(payload),
                "leg_count_per_time": int(payload[0]["leg_count"]) if payload else 0,
                "mean_loop_enthalpy_change_w": safe_mean(float(row["enthalpy_change_w"]) for row in payload),
                "mean_loop_wall_heat_total_w": safe_mean(float(row["wall_heat_total_w"]) for row in payload),
                "mean_loop_enthalpy_minus_wall_heat_w": safe_mean(
                    float(row["enthalpy_minus_wall_heat_w"]) for row in payload
                ),
                "max_abs_loop_enthalpy_minus_wall_heat_w": max(
                    (abs(float(row["enthalpy_minus_wall_heat_w"])) for row in payload if math.isfinite(float(row["enthalpy_minus_wall_heat_w"]))),
                    default=math.nan,
                ),
                "sum_over_time_enthalpy_change_w": sum(
                    float(row["enthalpy_change_w"]) for row in payload if math.isfinite(float(row["enthalpy_change_w"]))
                ),
                "sum_over_time_wall_heat_total_w": sum(
                    float(row["wall_heat_total_w"]) for row in payload if math.isfinite(float(row["wall_heat_total_w"]))
                ),
                "sum_over_time_enthalpy_minus_wall_heat_w": sum(
                    float(row["enthalpy_minus_wall_heat_w"])
                    for row in payload
                    if math.isfinite(float(row["enthalpy_minus_wall_heat_w"]))
                ),
            }
        )
    return leg_rows, per_case_rows


def build_bulk_centerline_rows(
    case: CaseRecord,
    boundary_rows: list[dict[str, str]],
    major_rows: list[dict[str, str]],
    exact_water_lookup: dict[tuple[float, str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    major_lookup: dict[tuple[float, str, int], dict[str, str]] = {}
    for row in major_rows:
        time_s = finite_float(row.get("time_s"))
        if math.isfinite(time_s):
            major_lookup[(time_s, str(row["span_name"]), int(row["bin_index"]))] = row
    payloads: list[dict[str, Any]] = []
    for row in boundary_rows:
        time_s = finite_float(row.get("time_s"))
        span_name = str(row["span_name"])
        nearest_bin_index = int(row["nearest_bin_index"])
        major = major_lookup.get((time_s, span_name, nearest_bin_index))
        dh = finite_float(major.get("hydraulic_diameter_geom_m")) if major else math.nan
        stored_bulk_temp = finite_float(row.get("bulk_temp_fluid_area_avg_k"))
        bulk_temp, bulk_method = resolved_bulk_temperature(
            case, exact_water_lookup, time_s, span_name, nearest_bin_index, stored_bulk_temp
        )
        centerline_temp = finite_float(row.get("t_core_k"))
        payloads.append(
            {
                "source_id": case.source_id,
                "case_label": case.case_label,
                "family": case.fluid_family,
                "time_s": time_s,
                "span_name": span_name,
                "landmark_name": row["landmark_name"],
                "landmark_role": row["landmark_role"],
                "hydraulic_diameter_geom_m": dh,
                "stored_bulk_temp_k": stored_bulk_temp,
                "bulk_temp_k": bulk_temp,
                "centerline_temp_k": centerline_temp,
                "bulk_minus_centerline_temp_k": bulk_temp - centerline_temp
                if math.isfinite(bulk_temp) and math.isfinite(centerline_temp)
                else math.nan,
                "t_wall_k": finite_float(row.get("t_wall_area_avg_k")),
                "bulk_temperature_method": bulk_method,
            }
        )
    return payloads


def build_boundary_layer_rows(
    case: CaseRecord,
    boundary_rows: list[dict[str, str]],
    major_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    major_lookup: dict[tuple[float, str, int], dict[str, str]] = {}
    for row in major_rows:
        time_s = finite_float(row.get("time_s"))
        if math.isfinite(time_s):
            major_lookup[(time_s, str(row["span_name"]), int(row["bin_index"]))] = row
    payloads: list[dict[str, Any]] = []
    for row in boundary_rows:
        time_s = finite_float(row.get("time_s"))
        span_name = str(row["span_name"])
        nearest_bin_index = int(row["nearest_bin_index"])
        major = major_lookup.get((time_s, span_name, nearest_bin_index))
        dh = finite_float(major.get("hydraulic_diameter_geom_m")) if major else math.nan
        delta_u = finite_float(row.get("delta99_u_m"))
        delta_t = finite_float(row.get("delta99_t_m"))
        payloads.append(
            {
                "source_id": case.source_id,
                "case_label": case.case_label,
                "family": case.fluid_family,
                "time_s": time_s,
                "span_name": span_name,
                "landmark_name": row["landmark_name"],
                "landmark_role": row["landmark_role"],
                "hydraulic_diameter_geom_m": dh,
                "delta99_u_m": delta_u,
                "delta99_t_m": delta_t,
                "delta99_u_over_dh": delta_u / dh if math.isfinite(delta_u) and math.isfinite(dh) and dh > 0.0 else math.nan,
                "delta99_t_over_dh": delta_t / dh if math.isfinite(delta_t) and math.isfinite(dh) and dh > 0.0 else math.nan,
                "delta99_t_over_delta99_u": delta_t / delta_u if math.isfinite(delta_t) and math.isfinite(delta_u) and abs(delta_u) > 0.0 else math.nan,
                "shape_factor_u": finite_float(row.get("shape_factor_u")),
                "profile_status": row.get("profile_status", ""),
            }
        )
    return payloads


def summarize_boundary_rows(boundary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in boundary_rows:
        grouped[(row["source_id"], row["family"], row["span_name"])].append(row)
    summaries: list[dict[str, Any]] = []
    for (source_id, family, span_name), payload in grouped.items():
        summaries.append(
            {
                "source_id": source_id,
                "family": family,
                "span_name": span_name,
                "sample_count": len(payload),
                "mean_delta99_u_over_dh": safe_mean(float(row["delta99_u_over_dh"]) for row in payload),
                "mean_delta99_t_over_dh": safe_mean(float(row["delta99_t_over_dh"]) for row in payload),
                "mean_delta99_t_over_delta99_u": safe_mean(float(row["delta99_t_over_delta99_u"]) for row in payload),
                "mean_shape_factor_u": safe_mean(float(row["shape_factor_u"]) for row in payload),
                "usable_fraction": safe_mean(1.0 if row["profile_status"] == "usable" else 0.0 for row in payload),
            }
        )
    return summaries


def build_representative_profile_rows(
    case: CaseRecord,
    boundary_profile_rows: list[dict[str, str]],
    boundary_summary_rows: list[dict[str, str]],
    major_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    if case.source_id not in REPRESENTATIVE_PROFILE_CASES:
        return []
    summary_lookup: dict[tuple[float, str, str], dict[str, str]] = {}
    for row in boundary_summary_rows:
        key = (finite_float(row.get("time_s")), str(row["span_name"]), str(row["landmark_name"]))
        summary_lookup[key] = row
    major_lookup: dict[tuple[float, str, int], dict[str, str]] = {}
    for row in major_rows:
        key = (finite_float(row.get("time_s")), str(row["span_name"]), int(row["bin_index"]))
        major_lookup[key] = row
    payloads: list[dict[str, Any]] = []
    for row in boundary_profile_rows:
        time_s = finite_float(row.get("time_s"))
        span_name = str(row["span_name"])
        landmark_name = str(row["landmark_name"])
        summary = summary_lookup.get((time_s, span_name, landmark_name))
        if summary is None:
            continue
        nearest_bin = int(summary["nearest_bin_index"])
        major = major_lookup.get((time_s, span_name, nearest_bin))
        dh = finite_float(major.get("hydraulic_diameter_geom_m")) if major else math.nan
        u_core = finite_float(summary.get("u_core_streamwise_abs_m_s"))
        t_core = finite_float(summary.get("t_core_k"))
        t_wall = finite_float(summary.get("t_wall_area_avg_k"))
        distance = finite_float(row.get("distance_from_wall_m"))
        u_abs = finite_float(row.get("u_tangent_abs_m_s"))
        temp = finite_float(row.get("t_k"))
        payloads.append(
            {
                "source_id": case.source_id,
                "family": case.fluid_family,
                "span_name": span_name,
                "landmark_name": landmark_name,
                "landmark_role": row["landmark_role"],
                "time_s": time_s,
                "distance_from_wall_m": distance,
                "distance_over_dh": distance / dh if math.isfinite(distance) and math.isfinite(dh) and dh > 0.0 else math.nan,
                "u_tangent_abs_m_s": u_abs,
                "u_over_ucore": u_abs / u_core if math.isfinite(u_abs) and math.isfinite(u_core) and abs(u_core) > 0.0 else math.nan,
                "t_k": temp,
                "theta_norm": (temp - t_wall) / (t_core - t_wall)
                if math.isfinite(temp) and math.isfinite(t_wall) and math.isfinite(t_core) and abs(t_core - t_wall) > 0.0
                else math.nan,
            }
        )
    return payloads


def render_pressure_closure_figure(section_rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    rows = [row for row in section_rows if row["straight_section_flag"] == "yes"]
    labels = [f"{row['source_id']}:{row['span_name']}" for row in rows]
    explicit = [float(row["mean_pressure_loss_hydro_pa"]) for row in rows]
    prgh = [float(row["mean_pressure_loss_prgh_integrated_pa"]) for row in rows]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(18, 6))
    ax.scatter(x, explicit, s=22, label="Hydro-corrected p loss")
    ax.scatter(x, prgh, s=22, label="Integrated p_rgh loss")
    ax.set_ylabel("Pressure loss [Pa]")
    ax.set_title("Straight-Section Pressure-Loss Closure")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=8)
    ax.legend(loc="upper right")
    fig.tight_layout()
    return save_matplotlib_figure(fig, output_dir, "pressure_closure_straight_sections", dpi=220)


def render_feature_keff_figure(feature_rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    labels = [f"{row['source_id']}:{row['feature_name']}" for row in feature_rows]
    values = [float(row["mean_keff_reference"]) for row in feature_rows]
    colors = ["#1f77b4" if row["family"] == "salt" else "#d62728" for row in feature_rows]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(18, 6))
    ax.bar(x, values, color=colors)
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_ylabel("K_eff [-]")
    ax.set_title("Feature Effective Loss Coefficients from p_rgh Residual Closure")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=8)
    fig.tight_layout()
    return save_matplotlib_figure(fig, output_dir, "feature_keff_by_case", dpi=220)


def render_boundary_ratio_figure(boundary_summary_rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    span_names = sorted({row["span_name"] for row in boundary_summary_rows})
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
    metrics = [
        ("mean_delta99_u_over_dh", r"$\delta_{99,u}/D_h$"),
        ("mean_delta99_t_over_dh", r"$\delta_{99,T}/D_h$"),
        ("mean_delta99_t_over_delta99_u", r"$\delta_{99,T}/\delta_{99,u}$"),
    ]
    x = np.arange(len(span_names))
    for ax, (field, ylabel) in zip(axes, metrics):
        salt = [next((float(row[field]) for row in boundary_summary_rows if row["span_name"] == span and row["family"] == "salt"), math.nan) for span in span_names]
        water = [next((float(row[field]) for row in boundary_summary_rows if row["span_name"] == span and row["family"] == "water"), math.nan) for span in span_names]
        ax.plot(x, salt, marker="o", label="Salt family")
        ax.plot(x, water, marker="s", label="Water family")
        ax.set_ylabel(ylabel)
        ax.legend(loc="best")
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(span_names, rotation=30, ha="right")
    axes[0].set_title("First-Pass Boundary-Layer Thickness Ratios")
    fig.tight_layout()
    return save_matplotlib_figure(fig, output_dir, "boundary_layer_ratio_family_summary", dpi=220)


def render_bulk_centerline_figure(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    span_names = sorted({row["span_name"] for row in rows})
    families = ["salt", "water"]
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(span_names))
    width = 0.35
    for offset, family in [(-width / 2, "salt"), (width / 2, "water")]:
        means = [
            safe_mean(float(row["bulk_minus_centerline_temp_k"]) for row in rows if row["span_name"] == span and row["family"] == family)
            for span in span_names
        ]
        ax.bar(x + offset, means, width=width, label=f"{family.title()} family")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(span_names, rotation=30, ha="right")
    ax.set_ylabel(r"$T_{bulk} - T_{centerline}$ [K]")
    ax.set_title("Bulk vs Centerline Temperature Correction by Span")
    ax.legend(loc="best")
    fig.tight_layout()
    return save_matplotlib_figure(fig, output_dir, "bulk_vs_centerline_correction", dpi=220)


def render_representative_profiles(
    representative_rows: list[dict[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    index_rows: list[dict[str, Any]] = []
    figure_paths: dict[str, str] = {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in representative_rows:
        grouped[(row["source_id"], row["span_name"])].append(row)
    for (source_id, span_name), payload in grouped.items():
        payload = sorted(payload, key=lambda item: float(item["distance_over_dh"]) if math.isfinite(float(item["distance_over_dh"])) else 1e9)
        x_u = [float(row["distance_over_dh"]) for row in payload if math.isfinite(float(row["u_over_ucore"]))]
        y_u = [float(row["u_over_ucore"]) for row in payload if math.isfinite(float(row["u_over_ucore"]))]
        x_t = [float(row["distance_over_dh"]) for row in payload if math.isfinite(float(row["theta_norm"]))]
        y_t = [float(row["theta_norm"]) for row in payload if math.isfinite(float(row["theta_norm"]))]
        if not x_u and not x_t:
            continue
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        if x_u:
            axes[0].plot(x_u, y_u, ".", alpha=0.6)
            axes[0].set_xlabel(r"$y/D_h$")
            axes[0].set_ylabel(r"$u/u_{core}$")
            axes[0].set_title("Hydraulic profile")
        if x_t:
            axes[1].plot(x_t, y_t, ".", alpha=0.6, color="#d62728")
            axes[1].set_xlabel(r"$y/D_h$")
            axes[1].set_ylabel(r"$\Theta = (T-T_w)/(T_{core}-T_w)$")
            axes[1].set_title("Thermal profile")
        fig.suptitle(f"{source_id} — {span_name}")
        fig.tight_layout()
        stem = f"{source_id}_{span_name}_boundary_profiles"
        paths = save_matplotlib_figure(fig, output_dir, stem, dpi=220)
        figure_paths[stem] = paths["png"]
        index_rows.append(
            {
                "source_id": source_id,
                "span_name": span_name,
                "figure_png": paths["png"],
                "figure_svg": paths["svg"],
                "figure_pdf": paths["pdf"],
                "profile_count": len(payload),
                "map_type": "sparse_landmark_profile_map",
            }
        )
    return index_rows, figure_paths


def write_math_companion(output_dir: Path) -> None:
    text = """# Ethan Pressure / HTC / Boundary-Layer Math Companion

Generated: `2026-06-17`

This note documents the definitions implemented by
`tools/analyze/build_ethan_pressure_htc_boundarylayer_package.py`.

## Pressure Closure

For a straight repaired section, the explicit hydro-corrected pressure loss is

`Delta p_loss = p_start - p_end + integral rho(s) g dot t_hat_flow(s) ds`

where `t_hat_flow` points along the inferred flow direction from the existing
June 15 streamwise package. The additive package also reports two cross-checks:

- endpoint `p_rgh` loss: `p_rgh,start - p_rgh,end`
- integrated `p_rgh` gradient from the existing major-loss package

The section closure residuals are:

- `Delta p_loss - Delta p_rgh,endpoint`
- `Delta p_loss - integral (dp_rgh/ds) ds`

These are diagnostic residuals, not forced-to-zero constraints.

## Apparent Friction Factor

The section-local apparent Darcy factor uses the explicit hydro-corrected loss:

`f_D,app,local = Delta p_loss * 2 D_h / (rho_b U_b^2 L)`

The loop-reference normalization uses the same numerator but a case-level loop
dynamic-head reference:

`f_D,app,loop = Delta p_loss * 2 D_h / (rho_loop U_loop^2 L)`

The package also reports a core-only shear comparison from the existing shear
reduction, restricted to straight main-pipe spans and excluding end zones near
junctions and the test-section transitions.

## Feature K_eff

For corners and the quartz test-section complex, the additive package reuses the
existing `p_rgh`-based feature residual closure:

`K_eff = Delta p_minor,residual / q_ref`

with

- `Delta p_minor,residual = Delta p_feature,p_rgh - Delta p_adjacent_major,ref`
- `q_ref = 0.5 rho_ref U_ref^2`

`rho_ref` and `U_ref` are built from the adjacent major-span section means.

## Bulk Temperature and HTC / Nu

For Salt-family cases, the stored June 15 bulk temperature is exact for the
requested `rho*u*cp` weighting because `cp(T)` is effectively constant.

For Water-family cases, this additive package recomputes `T_bulk` from the
preserved cut-plane surfaces stored in the June 15 raw extraction package. It
retains the original connected-region support logic, but replaces the stored
mass-flux-weighted definition with the requested

`T_bulk = (integral rho u_n cp T dA) / (integral rho u_n cp dA)`

using the water `rho(T)` and `cp(T)` polynomials from `case_config.yaml`.

The package also records the comparison against the older stored method:

- old stored bulk: positive aligned `rho*u_n` weighting
- exact flow-only rebuild: positive aligned `rho*u_n` weighting rebuilt from the
  preserved per-face surfaces
- exact requested rebuild: positive aligned `rho*u_n*cp` weighting rebuilt from
  the preserved per-face surfaces

Local wall-side transfer fields use

`h(s,theta) = q''_w / (T_w - T_bulk)`

`Nu(s,theta) = h D_h / k(T_bulk)`

The package keeps the sign convention from the wall heat-flux field. Rows with
`|T_w - T_bulk| < 0.25 K` are masked.

Area-ratio section HTC uses

`h_A = (integral q''_w dA) / (integral (T_w - T_bulk) dA)`

and

`Nu_A = h_A D_h / k(T_bulk)`

## Enthalpy Balance

For each major span, the package reports

`Delta H_leg = mdot * cp(T_bar) * (T_out - T_in)`

and compares that against the integrated wall heat from the existing
streamwise reduction:

`Q_wall,leg = integral q'_w(s) ds`

The closure residual is `Delta H_leg - Q_wall,leg`.

## Boundary-Layer Ratios

The boundary-layer package is still a first-pass landmark method. It uses the
existing wall-to-centerline landmark reductions and reports:

- `delta99_u / D_h`
- `delta99_T / D_h`
- `delta99_T / delta99_u`

These are reported as comparative boundary-thickness proxies on straight
sections. They are not claimed to be full circumferential boundary-layer maps.
"""
    (output_dir / "MATH_COMPANION.md").write_text(text, encoding="utf-8")


def write_readme(
    output_dir: Path,
    section_rows: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    figure_paths: dict[str, Any],
) -> None:
    salt_cases = sum(1 for row in case_rows if row["family"] == "salt")
    water_cases = sum(1 for row in case_rows if row["family"] == "water")
    text = f"""# Ethan Pressure / HTC / Boundary-Layer Package

Generated: `2026-06-17`

This package is a new additive analysis layer built from the June 15 live
case-analysis artifacts. It covers `{len(case_rows)}` cases:

- Salt family: `{salt_cases}`
- Water family: `{water_cases}`

The package is intentionally additive. It does **not** reopen the shared June
15/17 extraction scripts. Instead, it reuses the published raw CSV artifacts so
the new dissertation-facing pressure / HTC / boundary-layer report is
reproducible and non-destructive.

## What This Package Reports

- hydro-corrected straight-section pressure loss from `p` plus the explicit
  buoyancy integral
- `p_rgh` endpoint and integrated-gradient cross-checks
- section-local and loop-reference apparent Darcy factors
- core-only shear-based comparison on straight main pipes
- feature-level `K_eff` from the existing residual closure
- case-level pressure-head summaries, including wall `p`, wall `p_rgh`, and the
  wall hydro-head proxy range `p - p_rgh`
- bulk-vs-centerline temperature corrections
- fluid-side effective `h` and `Nu` fields from the azimuthal wall transport
  reductions
- section-level enthalpy balances
- first-pass hydraulic and thermal boundary-thickness ratios

## Primary Caveats

1. Pressure closure is strongest on straight repaired spans because those rows
   retain both wall-registered `p` / `p_rgh` and the tangent needed for the
   explicit buoyancy integral.
2. Feature `K_eff` is still based on the stored `p_rgh` residual closure. The
   raw package does not retain a dedicated feature-path density integral, so the
   additive package does not pretend to reconstruct one.
3. Salt-family HTC / Nu fields are compatible with the requested
   `rho*u*cp` bulk-temperature definition because `cp` is effectively constant
   in those cases.
4. Water-family HTC / Nu, enthalpy, and bulk-vs-centerline rows in this package
   now use an additive exact bulk-temperature rebuild from the preserved June 15
   cut-plane surfaces with water `rho(T)` and `cp(T)` polynomials. The package
   also preserves old-vs-new comparison tables so the method change is explicit.
5. Boundary-layer outputs remain first-pass landmark reductions. The
   representative profile figures are sparse landmark profile maps, not full
   circumferential field reconstructions.

## Key Artifacts

- `pressure_closure_by_section.csv`
- `pressure_closure_by_case.csv`
- `feature_keff_by_case.csv`
- `salt_side_htc_nu_fields.csv`
- `water_effective_htc_nu_fields.csv`
- `water_bulk_temperature_reweight_comparison.csv`
- `water_bulk_temperature_reweight_summary.csv`
- `fluid_side_htc_nu_section_summary.csv`
- `enthalpy_balance_by_leg.csv`
- `enthalpy_balance_by_case.csv`
- `bulk_vs_centerline_temperature_correction.csv`
- `boundary_layer_summary_by_section.csv`
- `representative_boundary_layer_profiles.csv`
- `representative_maps_index.csv`
- `MATH_COMPANION.md`

## High-Level Results

- straight-section rows reported: `{len(section_rows)}`
- feature rows reported: `{len(feature_rows)}`
- maximum explicit straight-section pressure loss reported:
  `{max((float(row['mean_pressure_loss_hydro_pa']) for row in section_rows if math.isfinite(float(row['mean_pressure_loss_hydro_pa']))), default=math.nan):.6g} Pa`
- maximum reported `K_eff`:
  `{max((float(row['mean_keff_reference']) for row in feature_rows if math.isfinite(float(row['mean_keff_reference']))), default=math.nan):.6g}`

## Heat-Loss Separation TODO

This package does **not** collapse unresolved disagreement into salt-side
Nusselt. The following decomposition remains a follow-on:

- internal fluid-side convection
- wall conduction through the loop material and insulation stack
- external convection / radiation
- air-jacket `UA`

Those terms should be separated before any final nondimensional salt-side
correlation is treated as closure-ready.

## Figures

- pressure closure: `{figure_paths['pressure_closure']['png']}`
- feature `K_eff`: `{figure_paths['feature_keff']['png']}`
- bulk vs centerline correction: `{figure_paths['bulk_centerline']['png']}`
- boundary-layer ratios: `{figure_paths['boundary_ratio']['png']}`

## Summary JSON

Machine-readable package summary is in `summary.json`.
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))
    source_ids = set(args.source_ids or [])

    package_index_rows = filter_source_rows(load_csv_rows(Path(args.package_index)), source_ids or None)
    metadata_index = load_metadata_index(METADATA_INDEX)
    case_records = [read_case_record(row, metadata_index) for row in package_index_rows]

    ensure_dir(output_dir)
    copied_index_rows: list[dict[str, Any]] = []
    pressure_rows: list[dict[str, Any]] = []
    case_pressure_rows: list[dict[str, Any]] = []
    feature_rows_all: list[dict[str, Any]] = []
    salt_htc_rows: list[dict[str, Any]] = []
    water_htc_rows: list[dict[str, Any]] = []
    htc_section_rows: list[dict[str, Any]] = []
    enthalpy_leg_rows: list[dict[str, Any]] = []
    enthalpy_case_rows: list[dict[str, Any]] = []
    bulk_centerline_rows: list[dict[str, Any]] = []
    boundary_ratio_rows: list[dict[str, Any]] = []
    representative_profile_rows: list[dict[str, Any]] = []
    water_bulk_comparison_rows: list[dict[str, Any]] = []

    for case in case_records:
        package_rows = load_package_rows(case.package_dir)
        exact_water_lookup, exact_comparison_rows = build_exact_water_bulk_lookup(case, package_rows)
        water_bulk_comparison_rows.extend(exact_comparison_rows)
        station_lookup = build_station_lookup(package_rows["station_defs"])
        section_rows = build_pressure_section_rows(case, package_rows["major_raw"], station_lookup)
        pressure_rows.extend(section_rows)
        case_pressure_summary = build_case_pressure_summary(section_rows, package_rows["major_raw"])
        case_pressure_rows.append(
            {
                "source_id": case.source_id,
                "case_label": case.case_label,
                "family": case.fluid_family,
                **case_pressure_summary,
            }
        )
        feature_rows_all.extend(build_feature_rows(case, package_rows["feature_summary"], section_rows))
        field_rows, section_htc_rows = build_htc_field_rows(
            case,
            package_rows["azimuthal_summary"],
            package_rows["major_raw"],
            exact_water_lookup,
        )
        if case.fluid_family == "salt":
            salt_htc_rows.extend(field_rows)
        else:
            water_htc_rows.extend(field_rows)
        htc_section_rows.extend(section_htc_rows)
        leg_rows, per_case_enthalpy = build_enthalpy_rows(
            case,
            package_rows["major_raw"],
            package_rows["streamwise_heat"],
            exact_water_lookup,
        )
        enthalpy_leg_rows.extend(leg_rows)
        enthalpy_case_rows.extend(per_case_enthalpy)
        bulk_centerline_rows.extend(
            build_bulk_centerline_rows(
                case,
                package_rows["boundary_summary"],
                package_rows["major_raw"],
                exact_water_lookup,
            )
        )
        boundary_ratio_rows.extend(build_boundary_layer_rows(case, package_rows["boundary_summary"], package_rows["major_raw"]))
        representative_profile_rows.extend(
            build_representative_profile_rows(
                case,
                package_rows["boundary_profiles"],
                package_rows["boundary_summary"],
                package_rows["major_raw"],
            )
        )
        copied_index_rows.append(
            {
                "source_id": case.source_id,
                "case_label": case.case_label,
                "family": case.fluid_family,
                "package_dir": str(case.package_dir),
                "profile_name": case.profile_name,
                "bulk_temperature_method": bulk_temperature_method(
                    case,
                    exact_water_cp_weighted=bool(exact_water_lookup),
                ),
            }
        )

    boundary_summary_rows = summarize_boundary_rows(boundary_ratio_rows)
    water_bulk_comparison_summary_rows = summarize_water_bulk_comparison(water_bulk_comparison_rows)

    csv_dump(output_dir / "package_index.csv", list(copied_index_rows[0].keys()), copied_index_rows)
    csv_dump(output_dir / "pressure_closure_by_section.csv", list(pressure_rows[0].keys()), pressure_rows)
    csv_dump(output_dir / "pressure_closure_by_case.csv", list(case_pressure_rows[0].keys()), case_pressure_rows)
    csv_dump(output_dir / "feature_keff_by_case.csv", list(feature_rows_all[0].keys()), feature_rows_all)
    csv_dump(output_dir / "salt_side_htc_nu_fields.csv", list(salt_htc_rows[0].keys()), salt_htc_rows)
    csv_dump(output_dir / "water_effective_htc_nu_fields.csv", list(water_htc_rows[0].keys()), water_htc_rows)
    csv_dump(
        output_dir / "water_bulk_temperature_reweight_comparison.csv",
        list(water_bulk_comparison_rows[0].keys()) if water_bulk_comparison_rows else ["source_id"],
        water_bulk_comparison_rows,
    )
    csv_dump(
        output_dir / "water_bulk_temperature_reweight_summary.csv",
        list(water_bulk_comparison_summary_rows[0].keys()) if water_bulk_comparison_summary_rows else ["source_id"],
        water_bulk_comparison_summary_rows,
    )
    csv_dump(output_dir / "fluid_side_htc_nu_section_summary.csv", list(htc_section_rows[0].keys()), htc_section_rows)
    csv_dump(output_dir / "enthalpy_balance_by_leg.csv", list(enthalpy_leg_rows[0].keys()), enthalpy_leg_rows)
    csv_dump(output_dir / "enthalpy_balance_by_case.csv", list(enthalpy_case_rows[0].keys()), enthalpy_case_rows)
    csv_dump(
        output_dir / "bulk_vs_centerline_temperature_correction.csv",
        list(bulk_centerline_rows[0].keys()),
        bulk_centerline_rows,
    )
    csv_dump(output_dir / "boundary_layer_detail.csv", list(boundary_ratio_rows[0].keys()), boundary_ratio_rows)
    csv_dump(
        output_dir / "boundary_layer_summary_by_section.csv",
        list(boundary_summary_rows[0].keys()),
        boundary_summary_rows,
    )
    csv_dump(
        output_dir / "representative_boundary_layer_profiles.csv",
        list(representative_profile_rows[0].keys()) if representative_profile_rows else ["source_id"],
        representative_profile_rows,
    )

    figure_paths = {
        "pressure_closure": render_pressure_closure_figure(pressure_rows, output_dir),
        "feature_keff": render_feature_keff_figure(feature_rows_all, output_dir),
        "boundary_ratio": render_boundary_ratio_figure(boundary_summary_rows, output_dir),
        "bulk_centerline": render_bulk_centerline_figure(bulk_centerline_rows, output_dir),
    }
    representative_index_rows, representative_figures = render_representative_profiles(representative_profile_rows, output_dir)
    csv_dump(
        output_dir / "representative_maps_index.csv",
        list(representative_index_rows[0].keys()) if representative_index_rows else ["source_id", "span_name", "map_type"],
        representative_index_rows,
    )
    write_math_companion(output_dir)

    summary = {
        "generated_at": iso_timestamp(),
        "package_index_csv": str(output_dir / "package_index.csv"),
        "case_count": len(case_records),
        "salt_case_count": sum(1 for case in case_records if case.fluid_family == "salt"),
        "water_case_count": sum(1 for case in case_records if case.fluid_family == "water"),
        "pressure_section_row_count": len(pressure_rows),
        "feature_row_count": len(feature_rows_all),
        "salt_htc_field_row_count": len(salt_htc_rows),
        "water_htc_field_row_count": len(water_htc_rows),
        "water_bulk_reweight_row_count": len(water_bulk_comparison_rows),
        "enthalpy_leg_row_count": len(enthalpy_leg_rows),
        "boundary_ratio_row_count": len(boundary_ratio_rows),
        "representative_profile_row_count": len(representative_profile_rows),
        "representative_map_count": len(representative_index_rows),
        "water_bulk_reweight_summary_by_case": water_bulk_comparison_summary_rows,
        "figure_paths": {
            "pressure_closure": figure_paths["pressure_closure"],
            "feature_keff": figure_paths["feature_keff"],
            "boundary_ratio": figure_paths["boundary_ratio"],
            "bulk_centerline": figure_paths["bulk_centerline"],
            "representative_profiles": representative_figures,
        },
        "limitations": [
            "Feature K_eff reuses the stored p_rgh residual closure because the raw package does not preserve a dedicated feature-path density integral.",
            "Water-family exact bulk-temperature rebuilds depend on the preserved June 15 cut-plane surface samples and inherit their connected-region support logic and retained-time coverage.",
            "Boundary-layer reporting remains a landmark-first method; the representative maps are sparse profile reconstructions rather than full circumferential boundary-layer fields.",
        ],
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, pressure_rows, feature_rows_all, case_pressure_rows, summary, figure_paths)


if __name__ == "__main__":
    main()
