#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.case_analysis_profiles import (  # noqa: E402
    build_flow_direction_hint_metadata,
    flatten_profile_wall_patches,
    get_case_analysis_profile,
    resolve_case_paths,
    thermal_role_for_patch,
    thermal_role_group_for_patch,
)
from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    safe_float,
)
from tools.hydraulic_budget_defs import EPS, load_station_centers, select_stable_processor_times  # noqa: E402

PATCH_EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_streamwise_friction_patch_averages.py"
DENSE_FACE_PATH = ROOT / "tools" / "extract" / "sample_streamwise_friction_dense_faces.py"
MAJOR_LOSS_PATH = ROOT / "tools" / "extract" / "sample_leg_centerline_major_loss.py"

DEFAULT_SOURCE_ID = "val_salt_test_2_coarse_mesh_laminar"
DEFAULT_OUTPUT_DIR = (
    WORKSPACE_ROOT
    / "reports"
    / "2026-06-15_ethan_streamwise_azimuthal_transport"
    / "raw_extraction"
)
DEFAULT_LAST_N_TIMES = 5
DEFAULT_AZIMUTH_BIN_COUNT = 36


def load_module(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


patch_extractor = load_module("sample_streamwise_friction_patch_averages", PATCH_EXTRACTOR_PATH)
dense_faces = load_module("sample_streamwise_friction_dense_faces", DENSE_FACE_PATH)
major_loss = load_module("sample_leg_centerline_major_loss", MAJOR_LOSS_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract facewise streamwise-azimuthal wall transport rows for registered "
            "Salt-family case-analysis profiles. The helper reconstructs retained "
            "wall fields, projects wall faces onto the repaired streamwise geometry, "
            "and exports raw wall transport plus reduced s/theta summaries."
        )
    )
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--analysis-manifest", help="Path to a shared case-analysis manifest JSON.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--last-n-times", type=int, default=DEFAULT_LAST_N_TIMES)
    parser.add_argument("--time-selector", help="Explicit comma-separated OpenFOAM time selector override.")
    parser.add_argument("--target-ds-m", type=float, help="Override the profile streamwise target bin size.")
    parser.add_argument("--azimuth-bin-count", type=int, default=DEFAULT_AZIMUTH_BIN_COUNT)
    parser.add_argument("--skip-extraction", action="store_true")
    return parser.parse_args()


def json_dump(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def load_manifest(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_time_label(value: str) -> str:
    numeric = safe_float(value)
    return f"{numeric:g}" if numeric is not None else str(value).strip()


def build_extract_case_key(
    source_id: str,
    profile_name: str,
    selected_times: list[str],
    required_fields: list[str],
    target_ds_m: float,
    azimuth_bin_count: int,
) -> str:
    payload = {
        "source_id": source_id,
        "profile_name": profile_name,
        "selected_times": [canonical_time_label(value) for value in selected_times],
        "required_fields": list(required_fields),
        "target_ds_m": float(target_ds_m),
        "azimuth_bin_count": int(azimuth_bin_count),
    }
    encoded = json.dumps(payload, sort_keys=True)
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


def build_polyline_points(
    labels: list[str],
    station_centers: dict[str, tuple[float, float, float]],
) -> list[np.ndarray]:
    return [np.array(station_centers[label], dtype=float) for label in labels]


def build_polyline_arclength(points: list[np.ndarray]) -> list[float]:
    s_values = [0.0]
    for index in range(1, len(points)):
        s_values.append(s_values[-1] + float(np.linalg.norm(points[index] - points[index - 1])))
    return s_values


def point_distance_to_segment(point: np.ndarray, start: np.ndarray, end: np.ndarray) -> tuple[float, float]:
    segment = end - start
    denom = float(np.dot(segment, segment))
    if denom <= EPS:
        return float(np.linalg.norm(point - start)), 0.0
    fraction = float(np.clip(np.dot(point - start, segment) / denom, 0.0, 1.0))
    projection = start + fraction * segment
    return float(np.linalg.norm(point - projection)), fraction


def project_point_onto_span(
    point_xyz: np.ndarray,
    labels: list[str],
    station_centers: dict[str, tuple[float, float, float]],
) -> dict[str, Any]:
    points = build_polyline_points(labels, station_centers)
    arclength = build_polyline_arclength(points)
    best_distance = float("inf")
    best_projection = points[0]
    best_tangent = np.array([1.0, 0.0, 0.0], dtype=float)
    best_s = 0.0
    best_segment = (labels[0], labels[1])
    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]
        distance_value, fraction = point_distance_to_segment(point_xyz, start, end)
        if distance_value >= best_distance:
            continue
        segment = end - start
        tangent_norm = float(np.linalg.norm(segment))
        tangent = segment / max(tangent_norm, EPS)
        best_distance = distance_value
        best_projection = start + fraction * segment
        best_tangent = tangent
        best_s = arclength[index] + fraction * (arclength[index + 1] - arclength[index])
        best_segment = (labels[index], labels[index + 1])
    return {
        "s_local_m": float(best_s),
        "distance_to_centerline_m": float(best_distance),
        "projection_xyz": best_projection,
        "tangent": best_tangent,
        "segment_start_label": best_segment[0],
        "segment_end_label": best_segment[1],
        "span_length_m": float(arclength[-1]),
    }


def span_offset_map(profile: Any, station_centers: dict[str, tuple[float, float, float]]) -> tuple[dict[str, float], float]:
    offsets: dict[str, float] = {}
    cumulative = 0.0
    for span_name in profile.loop_span_order:
        definition = profile.major_spans[span_name]
        points = build_polyline_points(definition["centerline_labels"], station_centers)
        arclength = build_polyline_arclength(points)
        offsets[span_name] = cumulative
        cumulative += float(arclength[-1])
    return offsets, float(cumulative)


def choose_cross_plane_basis(tangent: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    references = (
        np.array([0.0, 0.0, 1.0], dtype=float),
        np.array([0.0, 1.0, 0.0], dtype=float),
        np.array([1.0, 0.0, 0.0], dtype=float),
    )
    unit_tangent = tangent / max(float(np.linalg.norm(tangent)), EPS)
    for reference in references:
        e1 = reference - float(np.dot(reference, unit_tangent)) * unit_tangent
        e1_norm = float(np.linalg.norm(e1))
        if e1_norm > EPS:
            e1 = e1 / e1_norm
            e2 = np.cross(unit_tangent, e1)
            e2 = e2 / max(float(np.linalg.norm(e2)), EPS)
            return e1, e2
    return np.array([1.0, 0.0, 0.0], dtype=float), np.array([0.0, 1.0, 0.0], dtype=float)


def theta_bin(theta_rad: float, bin_count: int) -> tuple[int, float, float]:
    wrapped = float(((theta_rad + math.pi) % (2.0 * math.pi)) - math.pi)
    width = (2.0 * math.pi) / max(bin_count, 1)
    raw_index = int(math.floor((wrapped + math.pi) / width))
    bin_index = min(max(raw_index, 0), max(bin_count - 1, 0))
    center_rad = -math.pi + (bin_index + 0.5) * width
    return bin_index, center_rad, math.degrees(center_rad)


def build_face_geometry(
    case_dir: Path,
    source_id: str,
    profile: Any,
    station_centers: dict[str, tuple[float, float, float]],
    target_ds_m: float,
    azimuth_bin_count: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected_patches = flatten_profile_wall_patches(profile)
    boundary_entries = dense_faces.parse_boundary(case_dir / "constant" / "polyMesh" / "boundary")
    missing = [patch_name for patch_name in selected_patches if patch_name not in boundary_entries]
    if missing:
        raise RuntimeError(f"Azimuthal transport wall patches missing from boundary: {sorted(missing)}")
    target_ranges = [
        (
            int(boundary_entries[patch_name]["startFace"]),
            int(boundary_entries[patch_name]["startFace"]) + int(boundary_entries[patch_name]["nFaces"]),
            patch_name,
        )
        for patch_name in selected_patches
    ]
    face_map = dense_faces.load_selected_faces(case_dir / "constant" / "polyMesh" / "faces", target_ranges)
    point_ids = {point_id for entry in face_map.values() for point_id in entry["point_ids"]}
    point_map = dense_faces.load_selected_points(case_dir / "constant" / "polyMesh" / "points", point_ids)

    patch_to_span = {
        str(patch_name): span_name
        for span_name, definition in profile.major_spans.items()
        for patch_name in definition["wall_patches"]
    }
    span_offsets, loop_length_m = span_offset_map(profile, station_centers)
    geometry_rows: list[dict[str, Any]] = []

    for face_index, entry in sorted(face_map.items()):
        patch_name = str(entry["patch_name"])
        span_name = patch_to_span[patch_name]
        span_definition = profile.major_spans[span_name]
        point_coords = [point_map[point_id] for point_id in entry["point_ids"]]
        center = np.mean(np.vstack(point_coords), axis=0)
        area_m2 = float(dense_faces.polygon_area(point_coords))
        projection = project_point_onto_span(center, span_definition["centerline_labels"], station_centers)
        tangent = np.array(projection["tangent"], dtype=float)
        projected_point = np.array(projection["projection_xyz"], dtype=float)
        radial = center - projected_point
        radial_orthogonal = radial - float(np.dot(radial, tangent)) * tangent
        radial_distance_m = float(np.linalg.norm(radial_orthogonal))
        e1, e2 = choose_cross_plane_basis(tangent)
        theta_rad = float(math.atan2(float(np.dot(radial_orthogonal, e2)), float(np.dot(radial_orthogonal, e1))))
        theta_index, theta_center_rad, theta_center_deg = theta_bin(theta_rad, azimuth_bin_count)
        span_length_m = float(projection["span_length_m"])
        streamwise_bin_index = int(math.floor(float(projection["s_local_m"]) / max(target_ds_m, EPS)))
        streamwise_bin_center_local_m = min((streamwise_bin_index + 0.5) * target_ds_m, span_length_m)
        s_start_m = float(span_offsets[span_name])
        s_global_m = s_start_m + float(projection["s_local_m"])
        geometry_rows.append(
            {
                "source_id": source_id,
                "span_name": span_name,
                "span_kind": str(span_definition["kind"]),
                "patch_name": patch_name,
                "thermal_role": thermal_role_for_patch(profile, patch_name),
                "thermal_role_group": thermal_role_group_for_patch(profile, patch_name),
                "face_index": int(face_index),
                "streamwise_bin_index": int(streamwise_bin_index),
                "streamwise_bin_center_local_m": float(streamwise_bin_center_local_m),
                "streamwise_bin_center_global_m": float(s_start_m + streamwise_bin_center_local_m),
                "theta_bin_index": int(theta_index),
                "theta_bin_center_rad": float(theta_center_rad),
                "theta_bin_center_deg": float(theta_center_deg),
                "s_span_start_m": float(s_start_m),
                "s_local_m": float(projection["s_local_m"]),
                "s_m": float(s_global_m),
                "s_over_loop": float(s_global_m / max(loop_length_m, EPS)),
                "span_length_m": float(span_length_m),
                "distance_to_centerline_m": float(projection["distance_to_centerline_m"]),
                "radial_distance_m": float(radial_distance_m),
                "theta_rad": float(theta_rad),
                "theta_deg": float(math.degrees(theta_rad)),
                "area_m2": float(area_m2),
                "center_x_m": float(center[0]),
                "center_y_m": float(center[1]),
                "center_z_m": float(center[2]),
                "projection_x_m": float(projected_point[0]),
                "projection_y_m": float(projected_point[1]),
                "projection_z_m": float(projected_point[2]),
                "tangent_x": float(tangent[0]),
                "tangent_y": float(tangent[1]),
                "tangent_z": float(tangent[2]),
                "cross_e1_x": float(e1[0]),
                "cross_e1_y": float(e1[1]),
                "cross_e1_z": float(e1[2]),
                "cross_e2_x": float(e2[0]),
                "cross_e2_y": float(e2[1]),
                "cross_e2_z": float(e2[2]),
                "segment_start_label": str(projection["segment_start_label"]),
                "segment_end_label": str(projection["segment_end_label"]),
            }
        )

    geometry_meta = {
        "selected_patch_count": len(selected_patches),
        "selected_face_count": len(geometry_rows),
        "selected_point_count": len(point_map),
        "loop_length_m": float(loop_length_m),
        "target_ds_m": float(target_ds_m),
        "azimuth_bin_count": int(azimuth_bin_count),
    }
    return geometry_rows, geometry_meta


def build_timeseries_rows(
    source_id: str,
    case_dir: Path,
    geometry_rows: list[dict[str, Any]],
    selected_times: list[str],
) -> list[dict[str, Any]]:
    geometry_by_patch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in geometry_rows:
        geometry_by_patch[str(row["patch_name"])].append(row)
    ordered_geometry_by_patch = {
        patch_name: sorted(rows, key=lambda item: int(item["face_index"]))
        for patch_name, rows in geometry_by_patch.items()
    }
    selected_patches = set(ordered_geometry_by_patch)
    face_count_by_patch = {patch_name: len(rows) for patch_name, rows in ordered_geometry_by_patch.items()}
    sample_rows: list[dict[str, Any]] = []

    for time_name in selected_times:
        wall_shear = dense_faces.parse_boundary_field(case_dir / time_name / "wallShearStress", selected_patches, "vector")
        yplus = dense_faces.parse_boundary_field(case_dir / time_name / "yPlus", selected_patches, "scalar")
        pressure = dense_faces.parse_boundary_field(case_dir / time_name / "p", selected_patches, "scalar")
        pressure_rgh = dense_faces.parse_boundary_field(case_dir / time_name / "p_rgh", selected_patches, "scalar")
        temperature = dense_faces.parse_boundary_field(
            case_dir / time_name / "T",
            selected_patches,
            "scalar",
            face_count_by_patch=face_count_by_patch,
        )
        velocity = dense_faces.parse_boundary_field(
            case_dir / time_name / "U",
            selected_patches,
            "vector",
            face_count_by_patch=face_count_by_patch,
        )
        wall_heat_flux = dense_faces.parse_boundary_field(
            case_dir / time_name / "wallHeatFlux",
            selected_patches,
            "scalar",
            face_count_by_patch=face_count_by_patch,
        )
        for patch_name, face_rows in ordered_geometry_by_patch.items():
            tau_vectors = wall_shear[patch_name]
            yplus_scalars = yplus[patch_name]
            p_scalars = pressure[patch_name]
            p_rgh_scalars = pressure_rgh[patch_name]
            t_scalars = temperature[patch_name]
            u_vectors = velocity[patch_name]
            q_scalars = wall_heat_flux[patch_name]
            expected_count = len(face_rows)
            if not all(
                len(values) == expected_count
                for values in (tau_vectors, yplus_scalars, p_scalars, p_rgh_scalars, t_scalars, u_vectors, q_scalars)
            ):
                raise RuntimeError(
                    f"Patch {patch_name} field length mismatch at time {time_name}; "
                    f"expected {expected_count} rows."
                )
            for index, geometry_row in enumerate(face_rows):
                tangent = np.array(
                    [
                        float(geometry_row["tangent_x"]),
                        float(geometry_row["tangent_y"]),
                        float(geometry_row["tangent_z"]),
                    ],
                    dtype=float,
                )
                tau_vector = np.array(tau_vectors[index], dtype=float)
                u_vector = np.array(u_vectors[index], dtype=float)
                tau_streamwise = float(np.dot(tau_vector, tangent))
                sample_rows.append(
                    {
                        **geometry_row,
                        "time_s": float(time_name),
                        "wall_shear_x_pa": float(tau_vector[0]),
                        "wall_shear_y_pa": float(tau_vector[1]),
                        "wall_shear_z_pa": float(tau_vector[2]),
                        "wall_shear_magnitude_pa": float(np.linalg.norm(tau_vector)),
                        "wall_shear_streamwise_pa": float(tau_streamwise),
                        "wall_shear_streamwise_abs_pa": float(abs(tau_streamwise)),
                        "u_wall_x_m_s": float(u_vector[0]),
                        "u_wall_y_m_s": float(u_vector[1]),
                        "u_wall_z_m_s": float(u_vector[2]),
                        "u_wall_magnitude_m_s": float(np.linalg.norm(u_vector)),
                        "yplus": float(yplus_scalars[index][0]),
                        "p_pa": float(p_scalars[index][0]),
                        "p_rgh_pa": float(p_rgh_scalars[index][0]),
                        "t_wall_k": float(t_scalars[index][0]),
                        "wall_heat_flux_w_m2": float(q_scalars[index][0]),
                        "wall_heat_rate_w": float(q_scalars[index][0] * float(geometry_row["area_m2"])),
                    }
                )
    return sample_rows


def build_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row["source_id"]),
            float(row["time_s"]),
            str(row["span_name"]),
            int(row["streamwise_bin_index"]),
            int(row["theta_bin_index"]),
            str(row["thermal_role"]),
            str(row["thermal_role_group"]),
        )
        grouped[key].append(row)

    summary_rows: list[dict[str, Any]] = []
    for key, payload in sorted(grouped.items()):
        source_id, time_s, span_name, streamwise_bin_index, theta_bin_index, thermal_role, thermal_role_group = key
        total_area = sum(float(row["area_m2"]) for row in payload)
        weight = max(total_area, EPS)

        def area_weighted_mean(field_name: str) -> float:
            return float(sum(float(row[field_name]) * float(row["area_m2"]) for row in payload) / weight)

        summary_rows.append(
            {
                "source_id": source_id,
                "time_s": float(time_s),
                "span_name": span_name,
                "thermal_role": thermal_role,
                "thermal_role_group": thermal_role_group,
                "streamwise_bin_index": int(streamwise_bin_index),
                "streamwise_bin_center_local_m": area_weighted_mean("streamwise_bin_center_local_m"),
                "streamwise_bin_center_global_m": area_weighted_mean("streamwise_bin_center_global_m"),
                "theta_bin_index": int(theta_bin_index),
                "theta_bin_center_rad": area_weighted_mean("theta_bin_center_rad"),
                "theta_bin_center_deg": area_weighted_mean("theta_bin_center_deg"),
                "area_m2": float(total_area),
                "face_count": len(payload),
                "mean_s_m": area_weighted_mean("s_m"),
                "mean_theta_deg": area_weighted_mean("theta_deg"),
                "mean_radial_distance_m": area_weighted_mean("radial_distance_m"),
                "mean_yplus": area_weighted_mean("yplus"),
                "mean_p_pa": area_weighted_mean("p_pa"),
                "mean_p_rgh_pa": area_weighted_mean("p_rgh_pa"),
                "mean_t_wall_k": area_weighted_mean("t_wall_k"),
                "mean_wall_shear_streamwise_pa": area_weighted_mean("wall_shear_streamwise_pa"),
                "mean_wall_shear_streamwise_abs_pa": area_weighted_mean("wall_shear_streamwise_abs_pa"),
                "mean_wall_shear_magnitude_pa": area_weighted_mean("wall_shear_magnitude_pa"),
                "mean_wall_heat_flux_w_m2": area_weighted_mean("wall_heat_flux_w_m2"),
                "total_wall_heat_w": float(sum(float(row["wall_heat_rate_w"]) for row in payload)),
            }
        )
    return summary_rows


def main() -> int:
    args = parse_args()
    profile = get_case_analysis_profile(args.source_id)
    manifest = load_manifest(args.analysis_manifest)
    source_root, runtime_root, metadata = resolve_case_paths(args.source_id)

    if manifest.get("selected_times"):
        selected_times = [canonical_time_label(value) for value in manifest["selected_times"]]
    elif args.time_selector:
        selected_times = [canonical_time_label(part) for part in args.time_selector.split(",") if part.strip()]
    else:
        selected_times = select_stable_processor_times(
            runtime_root,
            args.last_n_times,
            required_fields=tuple(profile.analysis_required_fields),
        )
    if not selected_times:
        raise RuntimeError(f"No retained reconstructed times were found for {args.source_id}")

    target_ds_m = float(args.target_ds_m or profile.target_ds_m)
    required_fields = list(profile.analysis_required_fields)
    extract_key = build_extract_case_key(
        args.source_id,
        profile.profile_name,
        selected_times,
        required_fields,
        target_ds_m,
        args.azimuth_bin_count,
    )
    case_dir = patch_extractor.ensure_extract_case(args.source_id, runtime_root, extract_key=extract_key)
    major_loss.ensure_reconstructed_fields(case_dir, selected_times, args.skip_extraction, required_fields)
    thermal_sanitization = major_loss.sanitize_reconstructed_thermal_fields(case_dir, selected_times)
    usable_times = major_loss.available_reconstructed_times(case_dir, selected_times, required_fields)
    if not usable_times:
        raise RuntimeError(f"No usable reconstructed times remained for {args.source_id}")

    output_dir = ensure_dir(Path(args.output_dir).resolve())
    station_centers = load_station_centers(args.source_id)
    geometry_rows, geometry_meta = build_face_geometry(
        case_dir,
        args.source_id,
        profile,
        station_centers,
        target_ds_m,
        args.azimuth_bin_count,
    )
    timeseries_rows = build_timeseries_rows(args.source_id, case_dir, geometry_rows, usable_times)
    summary_rows = build_summary_rows(timeseries_rows)

    csv_dump(
        output_dir / "azimuthal_wall_transport_geometry.csv",
        list(geometry_rows[0].keys()) if geometry_rows else [],
        geometry_rows,
    )
    csv_dump(
        output_dir / "azimuthal_wall_transport_timeseries.csv",
        list(timeseries_rows[0].keys()) if timeseries_rows else [],
        timeseries_rows,
    )
    csv_dump(
        output_dir / "azimuthal_wall_transport_summary.csv",
        list(summary_rows[0].keys()) if summary_rows else [],
        summary_rows,
    )

    manifest_payload = {
        "created_at": iso_timestamp(),
        "source_id": args.source_id,
        "profile_name": profile.profile_name,
        "source_root": str(source_root),
        "runtime_root": str(runtime_root),
        "extract_case_dir": str(case_dir),
        "extract_key": extract_key,
        "requested_times": [float(time_name) for time_name in selected_times],
        "usable_times": [float(time_name) for time_name in usable_times],
        "required_fields": required_fields,
        "target_ds_m": float(target_ds_m),
        "azimuth_bin_count": int(args.azimuth_bin_count),
        "flow_direction_hint": build_flow_direction_hint_metadata(profile),
        "thermal_role_groups": {
            group_name: list(role_names) for group_name, role_names in profile.thermal_role_groups.items()
        },
        "geometry": geometry_meta,
        "thermal_sanitization": thermal_sanitization,
        "row_counts": {
            "geometry_rows": len(geometry_rows),
            "timeseries_rows": len(timeseries_rows),
            "summary_rows": len(summary_rows),
        },
        "metadata_snapshot": metadata,
        "artifacts": {
            "geometry_csv": str(output_dir / "azimuthal_wall_transport_geometry.csv"),
            "timeseries_csv": str(output_dir / "azimuthal_wall_transport_timeseries.csv"),
            "summary_csv": str(output_dir / "azimuthal_wall_transport_summary.csv"),
        },
    }
    json_dump(output_dir / "azimuthal_wall_transport_manifest.json", manifest_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
