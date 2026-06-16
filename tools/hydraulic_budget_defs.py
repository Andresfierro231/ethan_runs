from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from tools.case_analysis_profiles import (
    DEFAULT_SOURCE_ID,
    DEFAULT_TARGET_DS_M,
    get_case_analysis_profile,
    load_station_centers_from_file,
)
from tools.common import WORKSPACE_ROOT, safe_float

DEFAULT_STABLE_TIME_FIELDS = ("wallShearStress", "yPlus", "p", "p_rgh")
EPS = 1.0e-12

DEFAULT_PROFILE = get_case_analysis_profile(DEFAULT_SOURCE_ID)
MAJOR_SPANS: dict[str, dict[str, Any]] = DEFAULT_PROFILE.major_spans
FEATURE_BUDGETS: dict[str, dict[str, Any]] = DEFAULT_PROFILE.feature_budgets

TP_LABELS = [f"TP{index}" for index in range(1, 7)]
MAJOR_SPAN_ORDER = DEFAULT_PROFILE.major_span_order
MAIN_LOOP_SPAN_ORDER = DEFAULT_PROFILE.main_loop_span_order


def load_station_centers(source_id: str = DEFAULT_SOURCE_ID) -> dict[str, tuple[float, float, float]]:
    profile = get_case_analysis_profile(source_id)
    return load_station_centers_from_file(profile.tp_tw_locations)


def distance(point_a: tuple[float, float, float], point_b: tuple[float, float, float]) -> float:
    return math.sqrt(
        (point_b[0] - point_a[0]) ** 2
        + (point_b[1] - point_a[1]) ** 2
        + (point_b[2] - point_a[2]) ** 2
    )


def build_polyline_points(labels: list[str], station_centers: dict[str, tuple[float, float, float]]) -> list[np.ndarray]:
    return [np.array(station_centers[label], dtype=float) for label in labels]


def build_polyline_arclength(points: list[np.ndarray]) -> list[float]:
    s_values = [0.0]
    for index in range(1, len(points)):
        s_values.append(s_values[-1] + float(np.linalg.norm(points[index] - points[index - 1])))
    return s_values


def sample_polyline(labels: list[str], station_centers: dict[str, tuple[float, float, float]], target_ds_m: float) -> list[dict[str, Any]]:
    points = build_polyline_points(labels, station_centers)
    arclength = build_polyline_arclength(points)
    total_length = arclength[-1]
    sample_count = max(2, int(math.ceil(total_length / max(target_ds_m, EPS))) + 1)
    sample_s = np.linspace(0.0, total_length, sample_count)
    rows: list[dict[str, Any]] = []
    segment_index = 0
    for sample_index, s_value in enumerate(sample_s):
        while segment_index < len(arclength) - 2 and s_value > arclength[segment_index + 1]:
            segment_index += 1
        s0 = arclength[segment_index]
        s1 = arclength[segment_index + 1]
        point0 = points[segment_index]
        point1 = points[segment_index + 1]
        fraction = 0.0 if s1 <= s0 else (s_value - s0) / max(s1 - s0, EPS)
        center = point0 + fraction * (point1 - point0)
        tangent_vector = point1 - point0
        tangent_norm = float(np.linalg.norm(tangent_vector))
        tangent = tangent_vector / max(tangent_norm, EPS)
        rows.append(
            {
                "sample_index": sample_index,
                "s_m": float(s_value),
                "x_m": float(center[0]),
                "y_m": float(center[1]),
                "z_m": float(center[2]),
                "tangent_x": float(tangent[0]),
                "tangent_y": float(tangent[1]),
                "tangent_z": float(tangent[2]),
                "segment_start_label": labels[segment_index],
                "segment_end_label": labels[segment_index + 1],
            }
        )
    return rows


def build_major_span_station_rows(
    target_ds_m: float = DEFAULT_TARGET_DS_M,
    source_id: str = DEFAULT_SOURCE_ID,
) -> list[dict[str, Any]]:
    profile = get_case_analysis_profile(source_id)
    station_centers = load_station_centers(source_id)
    rows: list[dict[str, Any]] = []
    for span_name in profile.major_span_order:
        definition = profile.major_spans[span_name]
        for row in sample_polyline(definition["centerline_labels"], station_centers, target_ds_m):
            rows.append(
                {
                    "span_name": span_name,
                    "span_kind": definition["kind"],
                    "target_ds_m": target_ds_m,
                    "wall_patch_count": len(definition["wall_patches"]),
                    **row,
                }
            )
    return rows


def point_distance_to_segment(point: np.ndarray, start: np.ndarray, end: np.ndarray) -> tuple[float, float]:
    segment = end - start
    denom = float(np.dot(segment, segment))
    if denom <= EPS:
        return float(np.linalg.norm(point - start)), 0.0
    fraction = float(np.clip(np.dot(point - start, segment) / denom, 0.0, 1.0))
    projection = start + fraction * segment
    return float(np.linalg.norm(point - projection)), fraction


def project_point_onto_polyline(
    point_xyz: tuple[float, float, float] | np.ndarray,
    labels: list[str],
    station_centers: dict[str, tuple[float, float, float]],
) -> tuple[float, float, str, str]:
    points = build_polyline_points(labels, station_centers)
    arclength = build_polyline_arclength(points)
    point = np.array(point_xyz, dtype=float)
    best_distance = float("inf")
    best_s = 0.0
    best_segment = (labels[0], labels[1])
    for index in range(len(points) - 1):
        distance_value, fraction = point_distance_to_segment(point, points[index], points[index + 1])
        if distance_value < best_distance:
            best_distance = distance_value
            best_s = arclength[index] + fraction * (arclength[index + 1] - arclength[index])
            best_segment = (labels[index], labels[index + 1])
    return best_s, best_distance, best_segment[0], best_segment[1]


def infer_station_label_nearest(s_value: float, labels: list[str], station_centers: dict[str, tuple[float, float, float]]) -> str:
    points = build_polyline_points(labels, station_centers)
    arclength = build_polyline_arclength(points)
    nearest_index = int(np.argmin(np.abs(np.array(arclength, dtype=float) - s_value)))
    return labels[nearest_index]


def estimate_perimeter_from_wall_area(wall_area_m2: float, ds_m: float) -> float:
    return float(wall_area_m2 / max(ds_m, EPS))


def estimate_circular_hydraulic_diameter_from_perimeter(perimeter_m: float) -> float:
    return float(perimeter_m / math.pi)


def estimate_circular_area_from_perimeter(perimeter_m: float) -> float:
    return float((perimeter_m * perimeter_m) / (4.0 * math.pi))


def safe_nanmean(values: list[float]) -> float:
    finite = [value for value in values if safe_float(value) is not None and math.isfinite(float(value))]
    if not finite:
        return float("nan")
    return float(np.mean(np.array(finite, dtype=float)))


def select_stable_processor_times(
    runtime_root: Path,
    last_n_times: int,
    required_fields: tuple[str, ...] = DEFAULT_STABLE_TIME_FIELDS,
    gap_tolerance_s: float = 5.0,
) -> list[str]:
    processors_root = runtime_root / "processors64"
    candidates: list[tuple[float, str]] = []
    for item in processors_root.iterdir():
        if not item.is_dir():
            continue
        time_value = safe_float(item.name)
        if time_value is None:
            continue
        if not (item / "uniform" / "time").exists():
            continue
        if any(not (item / field_name).exists() for field_name in required_fields):
            continue
        candidates.append((float(time_value), item.name))
    candidates.sort(key=lambda item: item[0])
    if not candidates:
        return []
    latest_block: list[tuple[float, str]] = [candidates[-1]]
    for current in reversed(candidates[:-1]):
        if latest_block[0][0] - current[0] > gap_tolerance_s:
            break
        latest_block.insert(0, current)
    if last_n_times <= 0 or len(latest_block) <= last_n_times:
        return [label for _, label in latest_block]
    return [label for _, label in latest_block[-last_n_times:]]
