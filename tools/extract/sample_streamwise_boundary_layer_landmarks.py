#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import os
import shlex
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

# numpy 2.0 removed np.trapz (renamed np.trapezoid); support both.
_trapz = getattr(np, "trapz", None) or np.trapezoid

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.case_analysis_profiles import get_case_analysis_profile  # noqa: E402
from tools.common import csv_dump, ensure_dir, iso_timestamp, safe_float  # noqa: E402
from tools.hydraulic_budget_defs import (  # noqa: E402
    EPS,
    build_polyline_arclength,
    build_polyline_points,
)

MAJOR_EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_leg_centerline_major_loss.py"
DEFAULT_SAMPLE_COUNT = 65
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "reports"
    / "2026-06-10_ethan_salt2_case_analysis_package"
    / "raw_extraction"
)


def load_module(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


major_extractor = load_module("sample_leg_centerline_major_loss", MAJOR_EXTRACTOR_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sample representative wall-to-centerline landmark profiles for the Salt-family "
            "case-analysis workflow and derive first-pass boundary-layer metrics from "
            "reconstructed U/T fields."
        )
    )
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--analysis-manifest", required=True)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--sample-count", type=int, default=DEFAULT_SAMPLE_COUNT)
    parser.add_argument("--skip-extraction", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def canonical_time_labels(values: list[object]) -> list[str]:
    labels: list[str] = []
    for value in values:
        numeric = safe_float(value)
        labels.append(f"{numeric:g}" if numeric is not None else str(value).strip())
    return labels


GEOMETRY_REQUIRED_COLUMNS = (
    "span_name",
    "patch_name",
    "face_index",
    "center_x_m",
    "center_y_m",
    "center_z_m",
    "distance_to_centerline_m",
    "tangent_x",
    "tangent_y",
    "tangent_z",
)


def geometry_column_check(rows: list[dict[str, str]]) -> tuple[bool, list[str]]:
    if not rows:
        return False, list(GEOMETRY_REQUIRED_COLUMNS)
    available = set(rows[0].keys())
    missing = [column for column in GEOMETRY_REQUIRED_COLUMNS if column not in available]
    return not missing, missing


def load_major_geometry_rows(path: Path) -> list[dict[str, Any]]:
    csv_rows = load_csv_rows(path)
    has_required_columns, missing_columns = geometry_column_check(csv_rows)
    if not has_required_columns:
        raise RuntimeError(
            f"Major wall-face geometry CSV is missing required columns at {path}: "
            + ", ".join(missing_columns)
        )
    deduped: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in csv_rows:
        key = (str(row["span_name"]), str(row["patch_name"]), int(row["face_index"]))
        if key in deduped:
            continue
        deduped[key] = {
            "span_name": str(row["span_name"]),
            "patch_name": str(row["patch_name"]),
            "face_index": int(row["face_index"]),
            "center": np.array(
                [
                    float(row["center_x_m"]),
                    float(row["center_y_m"]),
                    float(row["center_z_m"]),
                ],
                dtype=float,
            ),
            "distance_to_centerline_m": float(row["distance_to_centerline_m"]),
            "tangent": np.array(
                [
                    float(row["tangent_x"]),
                    float(row["tangent_y"]),
                    float(row["tangent_z"]),
                ],
                dtype=float,
            ),
        }
    return list(deduped.values())


def resolve_major_geometry_path(output_dir: Path, major_summary: dict[str, Any]) -> Path:
    explicit_geometry_token = str(major_summary.get("wall_face_geometry_csv", "")).strip()
    geometry_candidates: list[Path] = []
    if explicit_geometry_token:
        geometry_candidates.append(Path(explicit_geometry_token))
    geometry_candidates.append(output_dir / "leg_wall_face_geometry.csv")

    for candidate in geometry_candidates:
        if not candidate.exists():
            continue
        csv_rows = load_csv_rows(candidate)
        has_required_columns, missing_columns = geometry_column_check(csv_rows)
        if not has_required_columns:
            raise RuntimeError(
                f"Expected major wall-face geometry columns in {candidate}, but these columns are missing: "
                + ", ".join(missing_columns)
            )
        return candidate

    legacy_samples_token = str(major_summary.get("wall_face_samples_csv", "")).strip()
    legacy_candidates: list[Path] = []
    if legacy_samples_token:
        legacy_candidates.append(Path(legacy_samples_token))
    legacy_candidates.append(output_dir / "leg_wall_face_samples.csv")

    for candidate in legacy_candidates:
        if not candidate.exists():
            continue
        csv_rows = load_csv_rows(candidate)
        has_required_columns, _missing_columns = geometry_column_check(csv_rows)
        if has_required_columns:
            # Older raw extractions embedded geometry and timeseries in the same
            # CSV. The new contract splits them so live jobs are unambiguous, but
            # keeping this fallback preserves June 10 Salt 2 raw-reuse rebuilds.
            return candidate

    searched_paths = [str(path) for path in geometry_candidates + legacy_candidates]
    raise RuntimeError(
        "Boundary-layer landmarks require an explicit wall-face geometry artifact with tangent vectors. "
        "No compatible geometry CSV was found. Searched: "
        + ", ".join(searched_paths)
    )


def load_major_timeseries_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "time_s": float(row["time_s"]),
                "span_name": str(row["span_name"]),
                "bin_index": int(row["bin_index"]),
                "s_mid_m": float(row["s_mid_m"]),
                "rho_bulk_kg_m3": float(row["rho_bulk_kg_m3"]),
                "tauw_streamwise_mean_abs_pa": float(row["tauw_streamwise_mean_abs_pa"]),
                "darcy_f": float(row["darcy_f"]),
                "p_rgh_wall_area_avg_pa": float(row["p_rgh_wall_area_avg_pa"]),
                "t_wall_area_avg_k": float(row["t_wall_area_avg_k"]),
                "bulk_temp_fluid_area_avg_k": float(row["bulk_temp_fluid_area_avg_k"]),
                "wall_heatflux_area_avg_w_m2": float(row["wall_heatflux_area_avg_w_m2"]),
                "effective_htc_w_m2_k": float(row["effective_htc_w_m2_k"]),
                "effective_ua_per_m_w_m_k": float(row["effective_ua_per_m_w_m_k"]),
                "mdot_mean_abs_kg_s": float(row["mdot_mean_abs_kg_s"]),
                "warning_flag": str(row.get("warning_flag", "")),
            }
        )
    return rows


def nearest_major_row(
    major_rows_by_time_span: dict[tuple[float, str], list[dict[str, Any]]],
    time_s: float,
    span_name: str,
    s_target_m: float,
) -> dict[str, Any] | None:
    payload = major_rows_by_time_span.get((time_s, span_name), [])
    if not payload:
        return None
    return min(payload, key=lambda row: abs(float(row["s_mid_m"]) - s_target_m))


def tangent_for_label(
    labels: list[str],
    station_centers: dict[str, tuple[float, float, float]],
    index: int,
) -> np.ndarray:
    if len(labels) < 2:
        return np.array([1.0, 0.0, 0.0], dtype=float)
    if index <= 0:
        vector = np.array(station_centers[labels[1]], dtype=float) - np.array(station_centers[labels[0]], dtype=float)
    elif index >= len(labels) - 1:
        vector = np.array(station_centers[labels[-1]], dtype=float) - np.array(station_centers[labels[-2]], dtype=float)
    else:
        vector = np.array(station_centers[labels[index + 1]], dtype=float) - np.array(
            station_centers[labels[index - 1]],
            dtype=float,
        )
    norm = float(np.linalg.norm(vector))
    return vector / max(norm, EPS)


def interpolate_polyline_point_and_tangent(
    labels: list[str],
    station_centers: dict[str, tuple[float, float, float]],
    target_s_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    points = build_polyline_points(labels, station_centers)
    arclength = build_polyline_arclength(points)
    for index in range(len(points) - 1):
        s0 = arclength[index]
        s1 = arclength[index + 1]
        if target_s_m <= s1 or index == len(points) - 2:
            fraction = 0.0 if s1 <= s0 else (target_s_m - s0) / max(s1 - s0, EPS)
            point = points[index] + fraction * (points[index + 1] - points[index])
            tangent = points[index + 1] - points[index]
            tangent /= max(float(np.linalg.norm(tangent)), EPS)
            return point, tangent
    tangent = points[-1] - points[-2]
    tangent /= max(float(np.linalg.norm(tangent)), EPS)
    return points[-1], tangent


def build_landmarks(
    profile: Any,
    station_centers: dict[str, tuple[float, float, float]],
    face_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    span_faces: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in face_rows:
        span_faces[str(row["span_name"])].append(row)

    landmarks: list[dict[str, Any]] = []
    for span_name in profile.major_span_order:
        labels = list(profile.major_spans[span_name]["centerline_labels"])
        if len(labels) < 2:
            continue
        points = build_polyline_points(labels, station_centers)
        arclength = build_polyline_arclength(points)
        total_length = float(arclength[-1])
        candidates: list[tuple[str, str, float, np.ndarray, np.ndarray]] = []
        for index, label in enumerate(labels):
            role = "start" if index == 0 else "end" if index == len(labels) - 1 else "anchor"
            point = np.array(station_centers[label], dtype=float)
            tangent = tangent_for_label(labels, station_centers, index)
            candidates.append((label, role, float(arclength[index]), point, tangent))
        midpoint, midpoint_tangent = interpolate_polyline_point_and_tangent(
            labels,
            station_centers,
            0.5 * total_length,
        )
        candidates.append(("midpoint", "midpoint", 0.5 * total_length, midpoint, midpoint_tangent))

        payload = span_faces.get(span_name, [])
        if not payload:
            continue
        for label, role, s_value, point, tangent in candidates:
            nearest_face = min(payload, key=lambda row: float(np.linalg.norm(row["center"] - point)))
            wall_point = np.array(nearest_face["center"], dtype=float)
            line_vector = point - wall_point
            line_length = float(np.linalg.norm(line_vector))
            if line_length <= 5.0e-4:
                continue
            landmarks.append(
                {
                    "span_name": span_name,
                    "span_kind": str(profile.major_spans[span_name]["kind"]),
                    "landmark_name": f"{span_name}_{role}_{label}",
                    "landmark_label": label,
                    "landmark_role": role,
                    "s_landmark_m": float(s_value),
                    "line_length_m": line_length,
                    "wall_patch_name": str(nearest_face["patch_name"]),
                    "wall_face_index": int(nearest_face["face_index"]),
                    "distance_to_centerline_m": float(nearest_face["distance_to_centerline_m"]),
                    "flow_direction_sign_hint": float(
                        profile.major_spans[span_name].get("flow_direction_sign_hint", 1.0)
                    ),
                    "wall_point_x_m": float(wall_point[0]),
                    "wall_point_y_m": float(wall_point[1]),
                    "wall_point_z_m": float(wall_point[2]),
                    "core_point_x_m": float(point[0]),
                    "core_point_y_m": float(point[1]),
                    "core_point_z_m": float(point[2]),
                    "tangent_x": float(tangent[0]),
                    "tangent_y": float(tangent[1]),
                    "tangent_z": float(tangent[2]),
                }
            )
    return landmarks


def write_boundary_layer_sets_dict(path: Path, landmarks: list[dict[str, Any]], sample_count: int) -> None:
    lines = [
        "FoamFile",
        "{",
        "    format      ascii;",
        "    class       dictionary;",
        "    location    \"system\";",
        "    object      functions;",
        "}",
        "",
        "streamwiseBoundaryLayerLandmarks",
        "{",
        "    type                sets;",
        "    libs                (\"libsampling.so\");",
        "    writeControl        timeStep;",
        "    writeInterval       1;",
        "    setFormat           raw;",
        "    interpolationScheme cellPoint;",
        "    fields              (T U);",
        "    sets",
        "    (",
    ]
    for row in landmarks:
        lines.extend(
            [
                row["landmark_name"],
                "{",
                "    type        lineUniform;",
                "    axis        xyz;",
                f"    start       ({row['wall_point_x_m']:.12g} {row['wall_point_y_m']:.12g} {row['wall_point_z_m']:.12g});",
                f"    end         ({row['core_point_x_m']:.12g} {row['core_point_y_m']:.12g} {row['core_point_z_m']:.12g});",
                f"    nPoints     {int(sample_count)};",
                "}",
            ]
        )
    lines.extend(["    );", "}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def boundary_outputs_ready(case_dir: Path, landmarks: list[dict[str, Any]], selected_times: list[str]) -> bool:
    root = case_dir / "postProcessing" / "streamwiseBoundaryLayerLandmarks"
    for time_name in selected_times:
        for row in landmarks:
            name = str(row["landmark_name"])
            split_t = root / time_name / f"{name}_T.xy"
            split_u = root / time_name / f"{name}_U.xy"
            combined = root / time_name / f"{name}.xy"
            if split_t.exists() and split_u.exists():
                continue
            if combined.exists():
                continue
            return False
    return True


def parse_raw_xy_line(raw_line: str) -> list[float]:
    stripped = raw_line.strip()
    if not stripped or stripped.startswith("#"):
        return []
    cleaned = stripped.replace("(", " ").replace(")", " ")
    tokens = [token for token in cleaned.split() if token]
    values: list[float] = []
    for token in tokens:
        try:
            values.append(float(token))
        except ValueError:
            return []
    return values


def load_scalar_xy(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            values = parse_raw_xy_line(raw_line)
            if len(values) < 4:
                continue
            rows.append(
                {
                    "x_m": float(values[0]),
                    "y_m": float(values[1]),
                    "z_m": float(values[2]),
                    "value": float(values[-1]),
                }
            )
    return rows


def load_vector_xy(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            values = parse_raw_xy_line(raw_line)
            if len(values) < 6:
                continue
            rows.append(
                {
                    "x_m": float(values[0]),
                    "y_m": float(values[1]),
                    "z_m": float(values[2]),
                    "u_x_m_s": float(values[-3]),
                    "u_y_m_s": float(values[-2]),
                    "u_z_m_s": float(values[-1]),
                }
            )
    return rows


def load_combined_xy(path: Path) -> tuple[list[dict[str, float]], list[dict[str, float]]]:
    scalar_rows: list[dict[str, float]] = []
    vector_rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            values = parse_raw_xy_line(raw_line)
            if len(values) < 7:
                continue
            scalar_rows.append(
                {
                    "x_m": float(values[0]),
                    "y_m": float(values[1]),
                    "z_m": float(values[2]),
                    "value": float(values[3]),
                }
            )
            vector_rows.append(
                {
                    "x_m": float(values[0]),
                    "y_m": float(values[1]),
                    "z_m": float(values[2]),
                    "u_x_m_s": float(values[4]),
                    "u_y_m_s": float(values[5]),
                    "u_z_m_s": float(values[6]),
                }
            )
    return scalar_rows, vector_rows


def interpolate_threshold_distance(y_values: np.ndarray, normalized_values: np.ndarray, threshold: float) -> float:
    for index, value in enumerate(normalized_values):
        if value >= threshold:
            if index == 0:
                return float(y_values[0])
            y0 = float(y_values[index - 1])
            y1 = float(y_values[index])
            v0 = float(normalized_values[index - 1])
            v1 = float(value)
            if abs(v1 - v0) <= EPS:
                return y1
            fraction = (threshold - v0) / (v1 - v0)
            return float(y0 + fraction * (y1 - y0))
    return math.nan


def build_profile_rows(
    case_dir: Path,
    landmarks: list[dict[str, Any]],
    selected_times: list[str],
) -> list[dict[str, Any]]:
    output_root = case_dir / "postProcessing" / "streamwiseBoundaryLayerLandmarks"
    landmark_lookup = {str(row["landmark_name"]): row for row in landmarks}
    rows: list[dict[str, Any]] = []
    for time_name in selected_times:
        time_value = float(time_name)
        for landmark_name, meta in sorted(landmark_lookup.items()):
            split_t_path = output_root / time_name / f"{landmark_name}_T.xy"
            split_u_path = output_root / time_name / f"{landmark_name}_U.xy"
            combined_path = output_root / time_name / f"{landmark_name}.xy"
            if split_t_path.exists() and split_u_path.exists():
                t_rows = load_scalar_xy(split_t_path)
                u_rows = load_vector_xy(split_u_path)
            elif combined_path.exists():
                t_rows, u_rows = load_combined_xy(combined_path)
            else:
                raise RuntimeError(
                    f"Boundary-layer landmark outputs are missing for {landmark_name} at {time_name}: "
                    f"expected either {split_t_path.name} and {split_u_path.name}, or {combined_path.name}"
                )
            if len(t_rows) != len(u_rows):
                raise RuntimeError(
                    f"Boundary-layer landmark sample length mismatch for {landmark_name} at {time_name}: "
                    f"T={len(t_rows)} vs U={len(u_rows)}"
                )
            tangent = np.array(
                [float(meta["tangent_x"]), float(meta["tangent_y"]), float(meta["tangent_z"])],
                dtype=float,
            )
            flow_direction_sign_hint = float(meta["flow_direction_sign_hint"])
            wall_point = np.array(
                [float(meta["wall_point_x_m"]), float(meta["wall_point_y_m"]), float(meta["wall_point_z_m"])],
                dtype=float,
            )
            for sample_index, (t_row, u_row) in enumerate(zip(t_rows, u_rows)):
                point = np.array([t_row["x_m"], t_row["y_m"], t_row["z_m"]], dtype=float)
                velocity = np.array(
                    [u_row["u_x_m_s"], u_row["u_y_m_s"], u_row["u_z_m_s"]],
                    dtype=float,
                )
                u_tangent = float(np.dot(velocity, tangent))
                u_tangent_aligned = float(flow_direction_sign_hint * u_tangent)
                rows.append(
                    {
                        "source_id": "",
                        "time_s": time_value,
                        "span_name": str(meta["span_name"]),
                        "span_kind": str(meta["span_kind"]),
                        "landmark_name": landmark_name,
                        "landmark_label": str(meta["landmark_label"]),
                        "landmark_role": str(meta["landmark_role"]),
                        "s_landmark_m": float(meta["s_landmark_m"]),
                        "line_length_m": float(meta["line_length_m"]),
                        "wall_patch_name": str(meta["wall_patch_name"]),
                        "wall_face_index": int(meta["wall_face_index"]),
                        "sample_index": int(sample_index),
                        "distance_from_wall_m": float(np.linalg.norm(point - wall_point)),
                        "x_m": float(point[0]),
                        "y_m": float(point[1]),
                        "z_m": float(point[2]),
                        "t_k": float(t_row["value"]),
                        "u_x_m_s": float(velocity[0]),
                        "u_y_m_s": float(velocity[1]),
                        "u_z_m_s": float(velocity[2]),
                        "u_tangent_m_s": float(u_tangent),
                        "u_tangent_aligned_m_s": float(u_tangent_aligned),
                        "u_tangent_abs_m_s": float(abs(u_tangent_aligned)),
                    }
                )
    return rows


def summarize_profiles(
    source_id: str,
    profile_rows: list[dict[str, Any]],
    landmarks: list[dict[str, Any]],
    major_rows_by_time_span: dict[tuple[float, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[float, str], list[dict[str, Any]]] = defaultdict(list)
    landmark_meta = {str(row["landmark_name"]): row for row in landmarks}
    for row in profile_rows:
        row["source_id"] = source_id
        grouped[(float(row["time_s"]), str(row["landmark_name"]))].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (time_s, landmark_name), payload in sorted(grouped.items()):
        payload.sort(key=lambda row: (float(row["distance_from_wall_m"]), int(row["sample_index"])))
        meta = landmark_meta[landmark_name]
        nearest_major = nearest_major_row(
            major_rows_by_time_span,
            float(time_s),
            str(meta["span_name"]),
            float(meta["s_landmark_m"]),
        )
        y = np.array([float(row["distance_from_wall_m"]) for row in payload], dtype=float)
        u_abs = np.array([float(row["u_tangent_abs_m_s"]) for row in payload], dtype=float)
        t_profile = np.array([float(row["t_k"]) for row in payload], dtype=float)
        valid_mask = np.isfinite(y) & np.isfinite(u_abs) & np.isfinite(t_profile)
        valid_count = int(np.count_nonzero(valid_mask))
        profile_status = "usable"
        status_note = ""
        if valid_count < 5:
            profile_status = "insufficient_samples"
            status_note = "fewer than five valid profile samples were available"
        y_valid = y[valid_mask]
        u_abs_valid = u_abs[valid_mask]
        t_valid = t_profile[valid_mask]
        core_count = min(max(5, int(math.ceil(valid_count * 0.2))), valid_count) if valid_count else 0
        u_core = float(np.mean(u_abs_valid[-core_count:])) if core_count else math.nan
        t_core = float(np.mean(t_valid[-core_count:])) if core_count else math.nan
        nearest_bin_index = int(nearest_major["bin_index"]) if nearest_major else -1
        nearest_bin_s_mid_m = float(nearest_major["s_mid_m"]) if nearest_major else math.nan
        rho_bulk = float(nearest_major["rho_bulk_kg_m3"]) if nearest_major else math.nan
        tau_mean_abs = float(nearest_major["tauw_streamwise_mean_abs_pa"]) if nearest_major else math.nan
        darcy_f = float(nearest_major["darcy_f"]) if nearest_major else math.nan
        t_wall_ref = (
            float(nearest_major["t_wall_area_avg_k"])
            if nearest_major
            else (float(t_valid[0]) if valid_count else math.nan)
        )
        bulk_temp_ref = float(nearest_major["bulk_temp_fluid_area_avg_k"]) if nearest_major else math.nan
        wall_heatflux_ref = float(nearest_major["wall_heatflux_area_avg_w_m2"]) if nearest_major else math.nan
        htc_ref = float(nearest_major["effective_htc_w_m2_k"]) if nearest_major else math.nan
        ua_ref = float(nearest_major["effective_ua_per_m_w_m_k"]) if nearest_major else math.nan
        mdot_ref = float(nearest_major["mdot_mean_abs_kg_s"]) if nearest_major else math.nan
        direct_dp_ref = (
            float(nearest_major["dp_major_gradient_direct_prgh_pa_per_m"])
            if nearest_major and "dp_major_gradient_direct_prgh_pa_per_m" in nearest_major
            else math.nan
        )
        u_tau = (
            float(math.sqrt(max(tau_mean_abs, 0.0) / rho_bulk))
            if math.isfinite(tau_mean_abs) and math.isfinite(rho_bulk) and rho_bulk > EPS
            else math.nan
        )
        fanning_cf = float(0.25 * darcy_f) if math.isfinite(darcy_f) else math.nan
        thermal_resistance = float(1.0 / ua_ref) if math.isfinite(ua_ref) and abs(ua_ref) > EPS else math.nan
        momentum_resistance = (
            float(abs(direct_dp_ref) / mdot_ref)
            if math.isfinite(direct_dp_ref) and math.isfinite(mdot_ref) and abs(mdot_ref) > EPS
            else math.nan
        )

        delta99_u = math.nan
        delta_star_u = math.nan
        theta_u = math.nan
        shape_factor_u = math.nan
        velocity_profile_status = "usable"
        if profile_status == "usable":
            if not math.isfinite(u_core) or u_core <= EPS:
                velocity_profile_status = "no_core_velocity"
            else:
                normalized_u = np.clip(u_abs_valid / u_core, 0.0, 1.0)
                delta99_u = interpolate_threshold_distance(y_valid, normalized_u, 0.99)
                delta_star_u = float(_trapz(1.0 - normalized_u, y_valid))
                theta_u = float(_trapz(normalized_u * (1.0 - normalized_u), y_valid))
                shape_factor_u = (
                    float(delta_star_u / theta_u) if math.isfinite(theta_u) and abs(theta_u) > EPS else math.nan
                )
                if not math.isfinite(delta99_u):
                    velocity_profile_status = "velocity_threshold_not_reached"
        else:
            velocity_profile_status = profile_status

        delta99_t = math.nan
        thermal_profile_status = "usable"
        if profile_status == "usable":
            if not math.isfinite(t_core) or not math.isfinite(t_wall_ref) or abs(t_core - t_wall_ref) <= EPS:
                thermal_profile_status = "no_thermal_contrast"
            else:
                normalized_t = np.clip(np.abs((t_valid - t_wall_ref) / (t_core - t_wall_ref)), 0.0, 1.0)
                delta99_t = interpolate_threshold_distance(y_valid, normalized_t, 0.99)
                if not math.isfinite(delta99_t):
                    thermal_profile_status = "thermal_threshold_not_reached"
        else:
            thermal_profile_status = profile_status

        if profile_status == "usable" and velocity_profile_status != "usable":
            profile_status = velocity_profile_status
            status_note = "velocity profile failed the core or 99% thickness gate"
        if profile_status == "usable" and thermal_profile_status != "usable":
            profile_status = thermal_profile_status
            status_note = "thermal profile failed the contrast or 99% thickness gate"

        summary_rows.append(
            {
                "source_id": source_id,
                "time_s": float(time_s),
                "span_name": str(meta["span_name"]),
                "span_kind": str(meta["span_kind"]),
                "landmark_name": landmark_name,
                "landmark_label": str(meta["landmark_label"]),
                "landmark_role": str(meta["landmark_role"]),
                "s_landmark_m": float(meta["s_landmark_m"]),
                "line_length_m": float(meta["line_length_m"]),
                "wall_patch_name": str(meta.get("wall_patch_name", "")),
                "wall_face_index": int(meta.get("wall_face_index", -1)),
                "nearest_bin_index": nearest_bin_index,
                "nearest_bin_s_mid_m": nearest_bin_s_mid_m,
                "sample_count": int(len(payload)),
                "valid_sample_count": valid_count,
                "u_core_streamwise_abs_m_s": float(u_core),
                "t_core_k": float(t_core),
                "t_wall_area_avg_k": float(t_wall_ref),
                "bulk_temp_fluid_area_avg_k": float(bulk_temp_ref),
                "rho_bulk_kg_m3": float(rho_bulk),
                "tauw_streamwise_mean_abs_pa": float(tau_mean_abs),
                "u_tau_m_s": float(u_tau),
                "darcy_f_shear": float(darcy_f),
                "fanning_cf_shear": float(fanning_cf),
                "effective_htc_w_m2_k": float(htc_ref),
                "effective_ua_per_m_w_m_k": float(ua_ref),
                "effective_thermal_resistance_k_m_w": float(thermal_resistance),
                "momentum_resistance_direct_prgh_pa_s_kg_m": float(momentum_resistance),
                "wall_heatflux_area_avg_w_m2": float(wall_heatflux_ref),
                "delta99_u_m": float(delta99_u),
                "delta_star_u_m": float(delta_star_u),
                "theta_u_m": float(theta_u),
                "shape_factor_u": float(shape_factor_u),
                "delta99_t_m": float(delta99_t),
                "velocity_profile_status": velocity_profile_status,
                "thermal_profile_status": thermal_profile_status,
                "profile_status": profile_status,
                "status_note": status_note,
            }
        )
    return summary_rows


def write_summary_json(
    path: Path,
    *,
    source_id: str,
    profile_name: str,
    case_dir: Path,
    output_dir: Path,
    requested_times: list[str],
    major_geometry_csv: Path,
    landmarks: list[dict[str, Any]],
    profile_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
) -> None:
    payload = {
        "generated_at": iso_timestamp(),
        "source_id": source_id,
        "profile_name": profile_name,
        "runtime_root": str(case_dir.resolve()),
        "extract_case": str(case_dir.resolve()),
        "output_dir": str(output_dir.resolve()),
        "requested_times": [float(value) for value in requested_times],
        "available_times": sorted({float(row["time_s"]) for row in summary_rows}),
        "landmark_count": len(landmarks),
        "profile_row_count": len(profile_rows),
        "summary_row_count": len(summary_rows),
        "profile_status_counts": {
            status: sum(1 for row in summary_rows if row["profile_status"] == status)
            for status in sorted({str(row["profile_status"]) for row in summary_rows})
        },
        "major_wall_face_geometry_csv": str(major_geometry_csv.resolve()),
        "profile_csv": str((output_dir / "boundary_layer_landmark_profiles.csv").resolve()),
        "summary_csv": str((output_dir / "boundary_layer_landmark_summary.csv").resolve()),
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    args = parse_args()
    manifest = load_json(Path(args.analysis_manifest))
    source_id = str(manifest.get("source_id", args.source_id))
    profile = get_case_analysis_profile(source_id)
    output_dir = ensure_dir(Path(args.output_dir))
    major_summary_path = output_dir / "leg_major_loss_extraction_summary.json"
    major_timeseries_path = output_dir / "leg_major_loss_timeseries.csv"
    if not major_summary_path.exists() or not major_timeseries_path.exists():
        raise RuntimeError(
            "Boundary-layer landmarks require the major-loss extraction outputs first. "
            f"Missing one of: {major_summary_path}, {major_timeseries_path}"
        )

    major_summary = load_json(major_summary_path)
    major_geometry_path = resolve_major_geometry_path(output_dir, major_summary)
    requested_times = canonical_time_labels(major_summary.get("available_times", manifest.get("requested_times", [])))
    if not requested_times:
        raise RuntimeError("No retained times were available for boundary-layer landmark sampling")
    case_dir = Path(str(major_summary.get("extract_case") or manifest.get("runtime_root"))).resolve()
    if not case_dir.exists():
        raise RuntimeError(f"Boundary-layer extract case does not exist: {case_dir}")

    station_centers = major_extractor.load_station_centers(source_id)
    face_rows = load_major_geometry_rows(major_geometry_path)
    major_rows = load_major_timeseries_rows(major_timeseries_path)
    major_rows_by_time_span: dict[tuple[float, str], list[dict[str, Any]]] = defaultdict(list)
    for row in major_rows:
        major_rows_by_time_span[(float(row["time_s"]), str(row["span_name"]))].append(row)

    landmarks = build_landmarks(profile, station_centers, face_rows)
    if not landmarks:
        raise RuntimeError("No boundary-layer landmarks could be constructed from the major-loss geometry")

    functions_path = case_dir / "system" / "streamwise_boundary_layer_landmarks_functions"
    write_boundary_layer_sets_dict(functions_path, landmarks, max(int(args.sample_count), 5))
    if not boundary_outputs_ready(case_dir, landmarks, requested_times):
        major_extractor.patch_extractor.shell_run(
            case_dir,
            "foamPostProcess "
            f"-case {shlex.quote(str(case_dir))} "
            f"-dict {shlex.quote(str(functions_path))} "
            f"-time '{','.join(requested_times)}'",
        )

    profile_rows = build_profile_rows(case_dir, landmarks, requested_times)
    summary_rows = summarize_profiles(source_id, profile_rows, landmarks, major_rows_by_time_span)
    if not profile_rows or not summary_rows:
        raise RuntimeError("Boundary-layer landmark sampling produced no rows")

    csv_dump(
        output_dir / "boundary_layer_landmark_profiles.csv",
        list(profile_rows[0].keys()),
        profile_rows,
    )
    csv_dump(
        output_dir / "boundary_layer_landmark_summary.csv",
        list(summary_rows[0].keys()),
        summary_rows,
    )
    write_summary_json(
        output_dir / "boundary_layer_landmark_summary.json",
        source_id=source_id,
        profile_name=profile.profile_name,
        case_dir=case_dir,
        output_dir=output_dir,
        requested_times=requested_times,
        major_geometry_csv=major_geometry_path,
        landmarks=landmarks,
        profile_rows=profile_rows,
        summary_rows=summary_rows,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
