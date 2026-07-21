#!/usr/bin/env python3
"""Extract retained-time major-loss primitives along configured leg centerlines.

Workflow role:
    This is a hydraulic evidence extractor. It reconstructs or reuses a
    temporary analysis case, samples wall/centerline geometry and pressure
    fields on retained times, and emits legwise major-loss primitives for later
    friction, pressure-ledger, and 1D-closure work.

Inputs:
    - Case-analysis profile metadata for the selected `--source-id`.
    - Optional shared `--analysis-manifest` and runtime-root information.
    - Reconstructed OpenFOAM fields in a temporary extraction workspace, or
      existing extraction products when `--skip-extraction` is used.

Outputs:
    Raw extraction CSV/JSON products under `--output-dir`. These are evidence
    tables, not direct solver modifications.

CLI modifiers:
    - `--source-id` selects the registered case.
    - `--analysis-manifest` shares resolved paths with sibling extractors.
    - `--last-n-times` or `--time-selector` controls retained OpenFOAM times.
    - `--target-ds-m` controls streamwise station spacing.
    - `--skip-extraction` reuses existing reconstructed fields/reductions.

Boundaries:
    This script estimates distributed leg losses. Feature residuals,
    two-tap minor losses, buoyancy de-biasing, and development/reset terms must
    be separated by downstream pressure-ledger tools before fitting.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import shlex
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import (  # noqa: E402
    WORKSPACE_ROOT,
    csv_dump,
    ensure_dir,
    iso_timestamp,
    safe_float,
)
from tools.case_analysis_profiles import get_case_analysis_profile, resolve_case_paths  # noqa: E402
from tools.hydraulic_budget_defs import (  # noqa: E402
    DEFAULT_SOURCE_ID,
    DEFAULT_TARGET_DS_M,
    EPS,
    build_major_span_station_rows,
    estimate_circular_area_from_perimeter,
    estimate_circular_hydraulic_diameter_from_perimeter,
    estimate_perimeter_from_wall_area,
    load_station_centers,
    project_point_onto_polyline,
    select_stable_processor_times,
)

PATCH_EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_streamwise_friction_patch_averages.py"
DENSE_FACE_PATH = ROOT / "tools" / "extract" / "sample_streamwise_friction_dense_faces.py"
STREAMWISE_BUILDER_PATH = ROOT / "tools" / "analyze" / "build_ethan_streamwise_friction_package.py"
DEFAULT_OUTPUT_DIR = (
    WORKSPACE_ROOT
    / "reports"
    / "2026-06-09_ethan_legwise_hydraulic_budget_package"
    / "raw_extraction"
)
DEFAULT_LAST_N_TIMES = 5
RAW_EXTRACTION_SCHEMA_VERSION = "salt_family_major_loss_v2"
THERMAL_MIN_ABS_DELTA_T_K = 0.25
THERMAL_MIN_AREA_RATIO_TO_REFERENCE = 0.5
THERMAL_MAX_AREA_RATIO_TO_REFERENCE = 2.0
THERMAL_MIN_POSITIVE_FLUX_KG_S = 1.0e-9


def load_module(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


patch_extractor = load_module("sample_streamwise_friction_patch_averages", PATCH_EXTRACTOR_PATH)
dense_faces = load_module("sample_streamwise_friction_dense_faces", DENSE_FACE_PATH)
streamwise_builder = load_module("build_ethan_streamwise_friction_package", STREAMWISE_BUILDER_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract Salt 2 legwise centerline-based major-loss quantities from reconstructed "
            "wall-face fields and merged continuation bulk histories."
        )
    )
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--analysis-manifest", help="Path to a shared case-analysis manifest JSON.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--last-n-times", type=int, default=DEFAULT_LAST_N_TIMES)
    parser.add_argument("--time-selector", help="Explicit comma-separated OpenFOAM time selector override.")
    parser.add_argument("--target-ds-m", type=float, default=DEFAULT_TARGET_DS_M)
    parser.add_argument("--skip-extraction", action="store_true")
    return parser.parse_args()


def load_manifest(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def json_dump(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def canonical_time_label(value: str) -> str:
    numeric = safe_float(value)
    return f"{numeric:g}" if numeric is not None else value.strip()


def build_extract_case_key(
    source_id: str,
    profile_name: str,
    selected_times: list[str],
    required_fields: list[str],
) -> str:
    payload = {
        "source_id": source_id,
        "profile_name": profile_name,
        "selected_times": [canonical_time_label(value) for value in selected_times],
        "required_fields": list(required_fields),
    }
    encoded = json.dumps(payload, sort_keys=True)
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


def reconstructed_fields_ready(case_dir: Path, selected_times: list[str], required_fields: list[str]) -> bool:
    for time_name in selected_times:
        time_dir = case_dir / time_name
        if not time_dir.exists():
            return False
        for field_name in required_fields:
            if not (time_dir / field_name).exists():
                return False
    return True


def ensure_reconstructed_fields(
    case_dir: Path,
    selected_times: list[str],
    skip_extraction: bool,
    required_fields: list[str],
) -> None:
    if skip_extraction and reconstructed_fields_ready(case_dir, selected_times, required_fields):
        return
    if not reconstructed_fields_ready(case_dir, selected_times, required_fields):
        for time_dir in case_dir.iterdir():
            if not time_dir.is_dir() or time_dir.is_symlink():
                continue
            if safe_float(time_dir.name) is None:
                continue
            if time_dir.name == "0":
                continue
            shutil.rmtree(time_dir)
        for time_name in selected_times:
            try:
                patch_extractor.shell_run(
                    case_dir,
                    "reconstructPar "
                    f"-case {case_dir} "
                    f"-time '{time_name}' "
                    f"-fields '({' '.join(required_fields)})'",
                )
            except subprocess.CalledProcessError:
                continue


def available_reconstructed_times(case_dir: Path, selected_times: list[str], required_fields: list[str]) -> list[str]:
    available: list[str] = []
    for time_name in selected_times:
        time_dir = case_dir / time_name
        if all((time_dir / field_name).exists() for field_name in required_fields):
            available.append(time_name)
    return available


def parse_finite_scalar_line(raw_line: str) -> float | None:
    stripped = raw_line.strip().rstrip(";")
    if not stripped:
        return None
    try:
        value = float(stripped)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return float(value)


def sanitize_ascii_scalar_nan_tokens(field_path: Path) -> int:
    if not field_path.exists():
        return 0
    lines = field_path.read_text(encoding="utf-8").splitlines(keepends=True)
    replacement_count = 0
    nan_indices = [
        index
        for index, line in enumerate(lines)
        if line.strip().lower() in {"-nan", "nan", "+nan"}
    ]
    for index in nan_indices:
        previous_value = None
        for probe in range(index - 1, -1, -1):
            previous_value = parse_finite_scalar_line(lines[probe])
            if previous_value is not None:
                break
        next_value = None
        for probe in range(index + 1, len(lines)):
            next_value = parse_finite_scalar_line(lines[probe])
            if next_value is not None:
                break
        if previous_value is not None and next_value is not None:
            replacement_value = 0.5 * (previous_value + next_value)
        elif previous_value is not None:
            replacement_value = previous_value
        elif next_value is not None:
            replacement_value = next_value
        else:
            replacement_value = 0.0
        leading = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
        newline = "\n" if lines[index].endswith("\n") else ""
        lines[index] = f"{leading}{replacement_value:.12g}{newline}"
        replacement_count += 1
    if replacement_count:
        field_path.write_text("".join(lines), encoding="utf-8")
    return replacement_count


def sanitize_reconstructed_thermal_fields(case_dir: Path, selected_times: list[str]) -> dict[str, Any]:
    summary_path = case_dir / "thermal_sanitization_summary.json"
    expected_times = [canonical_time_label(value) for value in selected_times]

    replacements_by_time: dict[str, int] = {}
    for time_name in selected_times:
        replacements = sanitize_ascii_scalar_nan_tokens(case_dir / time_name / "T")
        if replacements:
            replacements_by_time[canonical_time_label(time_name)] = replacements
    summary = {
        "generated_at": iso_timestamp(),
        "extract_case": str(case_dir),
        "selected_times": expected_times,
        "replacement_rule": (
            "Replace standalone invalid scalar nan tokens in reconstructed T fields "
            "using nearest finite neighbors within the same ASCII field file."
        ),
        "replacements_by_time": replacements_by_time,
    }
    json_dump(summary_path, summary)
    return summary


def flatten_major_wall_patches(major_spans: dict[str, dict[str, Any]]) -> list[str]:
    patches: list[str] = []
    for span_name in major_spans:
        patches.extend(str(patch_name) for patch_name in major_spans[span_name]["wall_patches"])
    return patches


def sample_explicit_polyline(points: list[np.ndarray], labels: list[str], target_ds_m: float) -> list[dict[str, Any]]:
    if len(points) != len(labels):
        raise RuntimeError("Polyline point/label length mismatch.")
    if len(points) < 2:
        raise RuntimeError("Polyline requires at least two points.")
    arclength = [0.0]
    for index in range(1, len(points)):
        arclength.append(arclength[-1] + float(np.linalg.norm(points[index] - points[index - 1])))
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


def build_station_rows(
    source_id: str,
    target_ds_m: float,
    major_spans: dict[str, dict[str, Any]],
    patch_centroid_polylines: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in build_major_span_station_rows(target_ds_m, source_id=source_id):
        rows.append(
            {
                "span_name": str(row["span_name"]),
                "span_kind": str(row["span_kind"]),
                "target_ds_m": float(row["target_ds_m"]),
                "wall_patch_count": int(row["wall_patch_count"]),
                "sample_index": int(row["sample_index"]),
                "s_center_m": float(row["s_m"]),
                "x_m": float(row["x_m"]),
                "y_m": float(row["y_m"]),
                "z_m": float(row["z_m"]),
                "tangent_x": float(row["tangent_x"]),
                "tangent_y": float(row["tangent_y"]),
                "tangent_z": float(row["tangent_z"]),
                "segment_start_label": str(row["segment_start_label"]),
                "segment_end_label": str(row["segment_end_label"]),
            }
        )
    if not patch_centroid_polylines:
        return rows

    repaired_rows = [row for row in rows if str(row["span_name"]) not in patch_centroid_polylines]
    for span_name, payload in patch_centroid_polylines.items():
        definition = major_spans[span_name]
        sampled_rows = sample_explicit_polyline(payload["points"], payload["labels"], target_ds_m)
        for row in sampled_rows:
            repaired_rows.append(
                {
                    "span_name": span_name,
                    "span_kind": str(definition["kind"]),
                    "target_ds_m": float(target_ds_m),
                    "wall_patch_count": len(definition["wall_patches"]),
                    "sample_index": int(row["sample_index"]),
                    "s_center_m": float(row["s_m"]),
                    "x_m": float(row["x_m"]),
                    "y_m": float(row["y_m"]),
                    "z_m": float(row["z_m"]),
                    "tangent_x": float(row["tangent_x"]),
                    "tangent_y": float(row["tangent_y"]),
                    "tangent_z": float(row["tangent_z"]),
                    "segment_start_label": str(row["segment_start_label"]),
                    "segment_end_label": str(row["segment_end_label"]),
                }
            )
    return repaired_rows


def build_station_bin_rows(station_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    span_kind_lookup: dict[str, str] = {}
    for row in station_rows:
        span_name = str(row["span_name"])
        grouped[span_name].append(row)
        span_kind_lookup[span_name] = str(row["span_kind"])

    bin_rows: list[dict[str, Any]] = []
    for span_name, payload in grouped.items():
        ordered = sorted(payload, key=lambda item: float(item["s_center_m"]))
        centers = [float(row["s_center_m"]) for row in ordered]
        if len(centers) < 2:
            raise RuntimeError(f"Span {span_name} did not have enough centerline stations to define bins.")
        total_length = centers[-1]
        for index, row in enumerate(ordered):
            s_start = 0.0 if index == 0 else 0.5 * (centers[index - 1] + centers[index])
            s_end = total_length if index == len(ordered) - 1 else 0.5 * (centers[index] + centers[index + 1])
            bin_rows.append(
                {
                    "span_name": span_name,
                    "span_kind": span_kind_lookup[span_name],
                    "bin_index": int(row["sample_index"]),
                    "s_start_m": float(s_start),
                    "s_end_m": float(s_end),
                    "s_mid_m": float(row["s_center_m"]),
                    "bin_width_m": float(max(s_end - s_start, 0.0)),
                    "x_m": float(row["x_m"]),
                    "y_m": float(row["y_m"]),
                    "z_m": float(row["z_m"]),
                    "tangent_x": float(row["tangent_x"]),
                    "tangent_y": float(row["tangent_y"]),
                    "tangent_z": float(row["tangent_z"]),
                    "segment_start_label": str(row["segment_start_label"]),
                    "segment_end_label": str(row["segment_end_label"]),
                }
            )
    return sorted(bin_rows, key=lambda item: (str(item["span_name"]), int(item["bin_index"])))


def write_cross_section_temperature_dict(
    path: Path,
    station_bins: list[dict[str, Any]],
    major_spans: dict[str, dict[str, Any]],
    span_reference_area_lookup: dict[str, float],
) -> dict[str, dict[str, Any]]:
    object_meta: dict[str, dict[str, Any]] = {}
    lines = [
        "FoamFile",
        "{",
        "    format      ascii;",
        "    class       dictionary;",
        "    location    \"system\";",
        "    object      functions;",
        "}",
        "",
        "streamwiseBulkThermal",
        "{",
        "    type                surfaces;",
        "    libs                (\"libsampling.so\");",
        "    writeControl        timeStep;",
        "    writeInterval       1;",
        "    surfaceFormat       foam;",
        "    interpolationScheme cellPoint;",
        "    fields              (T U);",
        "    surfaces",
        "    (",
    ]
    for row in station_bins:
        span_name = str(row["span_name"])
        bin_index = int(row["bin_index"])
        surface_name = f"bulkThermal_{span_name}_bin_{bin_index:04d}"
        object_meta[surface_name] = {
            "span_name": span_name,
            "bin_index": bin_index,
            "s_mid_m": float(row["s_mid_m"]),
            "point": (
                float(row["x_m"]),
                float(row["y_m"]),
                float(row["z_m"]),
            ),
            "normal": (
                float(row["tangent_x"]),
                float(row["tangent_y"]),
                float(row["tangent_z"]),
            ),
            "flow_direction_sign_hint": float(
                major_spans[span_name].get("flow_direction_sign_hint", 1.0)
            ),
            "reference_area_m2": float(
                safe_float(span_reference_area_lookup.get(span_name), math.nan)
            ),
        }
        lines.extend(
            [
                surface_name,
                "{",
                "    type        cutPlane;",
                f"    name        {surface_name};",
                "    planeType   pointAndNormal;",
                f"    point       ({float(row['x_m']):.12g} {float(row['y_m']):.12g} {float(row['z_m']):.12g});",
                f"    normal      ({float(row['tangent_x']):.12g} {float(row['tangent_y']):.12g} {float(row['tangent_z']):.12g});",
                "    interpolate true;",
                "}",
            ]
        )
    lines.extend(
        [
            "    );",
            "}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return object_meta


def cross_section_outputs_ready(case_dir: Path, surface_names: list[str], selected_times: list[str]) -> bool:
    object_name = "streamwiseBulkThermal"
    for surface_name in surface_names:
        for time_name in selected_times:
            surface_dir = case_dir / "postProcessing" / object_name / time_name / surface_name
            if not (surface_dir / "points").exists():
                return False
            if not (surface_dir / "faces").exists():
                return False
            if not (surface_dir / "scalarField" / "T").exists():
                return False
            if not (surface_dir / "vectorField" / "U").exists():
                return False
    return True


def load_full_points(path: Path) -> list[np.ndarray]:
    points: list[np.ndarray] = []
    with path.open("r", encoding="utf-8") as handle:
        in_list = False
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped:
                continue
            if not in_list:
                if stripped == "(":
                    in_list = True
                continue
            if stripped == ")":
                break
            points.append(np.array(dense_faces.parse_point_entry(stripped), dtype=float))
    return points


def load_full_faces(path: Path) -> list[list[int]]:
    faces: list[list[int]] = []
    with path.open("r", encoding="utf-8") as handle:
        in_list = False
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped:
                continue
            if not in_list:
                if stripped == "(":
                    in_list = True
                continue
            if stripped == ")":
                break
            faces.append(dense_faces.parse_face_entry(stripped))
    return faces


def load_full_scalar_field(path: Path) -> list[float]:
    values: list[float] = []
    with path.open("r", encoding="utf-8") as handle:
        in_list = False
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped:
                continue
            if not in_list:
                if stripped == "(":
                    in_list = True
                continue
            if stripped == ")":
                break
            values.append(float(stripped))
    return values


def load_full_vector_field(path: Path) -> list[np.ndarray]:
    values: list[np.ndarray] = []
    with path.open("r", encoding="utf-8") as handle:
        in_list = False
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped:
                continue
            if not in_list:
                if stripped == "(":
                    in_list = True
                continue
            if stripped == ")":
                break
            values.append(np.array(dense_faces.parse_point_entry(stripped), dtype=float))
    return values


def face_area_vector(points: list[np.ndarray]) -> np.ndarray:
    if len(points) < 3:
        return np.zeros(3, dtype=float)
    origin = points[0]
    area_vector = np.zeros(3, dtype=float)
    for index in range(1, len(points) - 1):
        area_vector += np.cross(points[index] - origin, points[index + 1] - origin)
    return 0.5 * area_vector


def face_sample_values(
    field_values: list[Any],
    faces: list[list[int]],
    points: list[np.ndarray],
    field_name: str,
) -> list[Any]:
    if len(field_values) == len(faces):
        return field_values
    if len(field_values) == len(points):
        return [
            np.mean([field_values[point_id] for point_id in face], axis=0)
            for face in faces
        ]
    raise RuntimeError(
        f"Cut-plane field length mismatch for {field_name}: "
        f"{len(points)} points, {len(faces)} faces, {len(field_values)} samples"
    )


def build_connected_face_components(faces: list[list[int]]) -> list[list[int]]:
    edge_to_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    for face_index, face in enumerate(faces):
        if len(face) < 2:
            continue
        for point_a, point_b in zip(face, face[1:] + face[:1]):
            edge = tuple(sorted((int(point_a), int(point_b))))
            edge_to_faces[edge].append(face_index)
    adjacency: dict[int, set[int]] = defaultdict(set)
    for attached_faces in edge_to_faces.values():
        if len(attached_faces) < 2:
            continue
        for face_index in attached_faces:
            adjacency[face_index].update(other for other in attached_faces if other != face_index)
    components: list[list[int]] = []
    visited: set[int] = set()
    for start_index in range(len(faces)):
        if start_index in visited:
            continue
        stack = [start_index]
        component: list[int] = []
        while stack:
            face_index = stack.pop()
            if face_index in visited:
                continue
            visited.add(face_index)
            component.append(face_index)
            stack.extend(sorted(adjacency.get(face_index, set()) - visited))
        components.append(sorted(component))
    return components


def area_error_metric(area_m2: float, reference_area_m2: float) -> float:
    if not math.isfinite(area_m2) or not math.isfinite(reference_area_m2):
        return float("inf")
    if area_m2 <= EPS or reference_area_m2 <= EPS:
        return float("inf")
    return abs(math.log(area_m2 / reference_area_m2))


def compute_cross_section_region_payload(
    component_indices: list[int],
    faces: list[list[int]],
    points: list[np.ndarray],
    face_t_values: list[float],
    face_u_values: list[np.ndarray],
    plane_normal: np.ndarray,
    density_intercept: float,
    density_slope: float,
    flow_direction_sign_hint: float,
    reference_area_m2: float,
) -> dict[str, Any]:
    face_areas: list[float] = []
    area_weighted_temp_numerator = 0.0
    signed_mass_flux_kg_s = 0.0
    aligned_signed_mass_flux_kg_s = 0.0
    positive_aligned_mass_flux_kg_s = 0.0
    flow_weighted_temp_numerator = 0.0
    for face_index in component_indices:
        point_coords = [points[point_id] for point_id in faces[face_index]]
        area_vector = face_area_vector(point_coords)
        if float(np.dot(area_vector, plane_normal)) < 0.0:
            area_vector *= -1.0
        area_m2 = float(np.linalg.norm(area_vector))
        face_temperature = float(face_t_values[face_index])
        face_velocity = np.array(face_u_values[face_index], dtype=float)
        density = float(density_intercept - density_slope * face_temperature)
        normal_velocity = float(np.dot(face_velocity, plane_normal))
        raw_mass_flux = float(density * normal_velocity * area_m2)
        aligned_mass_flux = float(flow_direction_sign_hint * raw_mass_flux)
        positive_aligned_mass_flux = max(0.0, aligned_mass_flux)
        face_areas.append(area_m2)
        area_weighted_temp_numerator += area_m2 * face_temperature
        signed_mass_flux_kg_s += raw_mass_flux
        aligned_signed_mass_flux_kg_s += aligned_mass_flux
        positive_aligned_mass_flux_kg_s += positive_aligned_mass_flux
        flow_weighted_temp_numerator += positive_aligned_mass_flux * face_temperature
    total_area_m2 = float(sum(face_areas))
    area_weighted_temp_k = (
        float(area_weighted_temp_numerator / max(total_area_m2, EPS))
        if total_area_m2 > EPS
        else math.nan
    )
    flow_weighted_temp_k = (
        float(flow_weighted_temp_numerator / positive_aligned_mass_flux_kg_s)
        if positive_aligned_mass_flux_kg_s > THERMAL_MIN_POSITIVE_FLUX_KG_S
        else math.nan
    )
    return {
        "face_count": int(len(component_indices)),
        "area_m2": total_area_m2,
        "reference_area_m2": float(reference_area_m2),
        "area_ratio_to_reference": (
            float(total_area_m2 / reference_area_m2)
            if math.isfinite(reference_area_m2) and reference_area_m2 > EPS
            else math.nan
        ),
        "area_error_metric": area_error_metric(total_area_m2, reference_area_m2),
        "signed_mass_flux_kg_s": float(signed_mass_flux_kg_s),
        "aligned_signed_mass_flux_kg_s": float(aligned_signed_mass_flux_kg_s),
        "positive_mass_flux_kg_s": float(positive_aligned_mass_flux_kg_s),
        "temp_area_weighted_k": float(area_weighted_temp_k),
        "temp_flow_weighted_k": float(flow_weighted_temp_k),
    }


def select_cross_section_region(regions: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    if not regions:
        return None, "missing_region"
    aligned_regions = [
        region for region in regions
        if float(region["aligned_signed_mass_flux_kg_s"]) > THERMAL_MIN_POSITIVE_FLUX_KG_S
    ]
    if aligned_regions:
        largest_positive_flux = max(
            float(region["positive_mass_flux_kg_s"]) for region in aligned_regions
        )
        if largest_positive_flux > THERMAL_MIN_POSITIVE_FLUX_KG_S:
            candidate_regions = [
                region
                for region in aligned_regions
                if float(region["positive_mass_flux_kg_s"]) >= 0.25 * largest_positive_flux
            ]
            if candidate_regions:
                chosen = min(candidate_regions, key=lambda region: float(region["area_error_metric"]))
                return chosen, "aligned_area_match"
    chosen = min(regions, key=lambda region: float(region["area_error_metric"]))
    if float(chosen["positive_mass_flux_kg_s"]) <= THERMAL_MIN_POSITIVE_FLUX_KG_S:
        return chosen, "insufficient_aligned_flux"
    return chosen, "support_flow_sign_fallback"


def build_cross_section_temperature_rows(
    case_dir: Path,
    station_bins: list[dict[str, Any]],
    major_spans: dict[str, dict[str, Any]],
    span_reference_area_lookup: dict[str, float],
    selected_times: list[str],
    skip_extraction: bool,
    density_intercept: float,
    density_slope: float,
) -> list[dict[str, Any]]:
    functions_path = case_dir / "system" / "streamwise_bulk_temperature_functions"
    surface_meta = write_cross_section_temperature_dict(
        functions_path,
        station_bins,
        major_spans,
        span_reference_area_lookup,
    )
    surface_names = sorted(surface_meta)
    time_selector = ",".join(selected_times)
    outputs_ready = cross_section_outputs_ready(case_dir, surface_names, selected_times)
    if not outputs_ready:
        patch_extractor.shell_run(
            case_dir,
            "foamPostProcess "
            f"-case {shlex.quote(str(case_dir))} "
            f"-dict {shlex.quote(str(functions_path))} "
            f"-time '{time_selector}'",
        )

    rows: list[dict[str, Any]] = []
    selected_time_set = {time_name for time_name in selected_times}
    output_root = case_dir / "postProcessing" / "streamwiseBulkThermal"
    if not output_root.exists():
        return rows
    progress_interval = 25
    for time_dir in sorted(output_root.iterdir(), key=lambda item: safe_float(item.name, -1.0) or -1.0):
        if not time_dir.is_dir() or time_dir.name not in selected_time_set:
            continue
        time_value = float(time_dir.name)
        available_surface_names = [
            surface_name
            for surface_name in sorted(surface_meta)
            if (time_dir / surface_name / "points").exists()
            and (time_dir / surface_name / "faces").exists()
            and (time_dir / surface_name / "scalarField" / "T").exists()
            and (time_dir / surface_name / "vectorField" / "U").exists()
        ]
        time_start = time.perf_counter()
        print(
            f"[cross-section] time {time_dir.name}: reducing {len(available_surface_names)} surfaces from {time_dir}",
            flush=True,
        )
        processed_surface_count = 0
        for surface_name, meta in sorted(surface_meta.items()):
            surface_dir = time_dir / surface_name
            points_path = surface_dir / "points"
            faces_path = surface_dir / "faces"
            scalar_path = surface_dir / "scalarField" / "T"
            vector_path = surface_dir / "vectorField" / "U"
            if not points_path.exists() or not faces_path.exists() or not scalar_path.exists() or not vector_path.exists():
                continue
            points = load_full_points(points_path)
            faces = load_full_faces(faces_path)
            point_t_values = load_full_scalar_field(scalar_path)
            point_u_values = load_full_vector_field(vector_path)
            face_t_values = [
                float(value) for value in face_sample_values(point_t_values, faces, points, "T")
            ]
            face_u_values = [
                np.array(value, dtype=float) for value in face_sample_values(point_u_values, faces, points, "U")
            ]
            plane_normal = np.array(meta["normal"], dtype=float)
            plane_normal /= max(float(np.linalg.norm(plane_normal)), EPS)
            components = build_connected_face_components(faces)
            regions = [
                compute_cross_section_region_payload(
                    component_indices,
                    faces,
                    points,
                    face_t_values,
                    face_u_values,
                    plane_normal,
                    density_intercept,
                    density_slope,
                    float(meta["flow_direction_sign_hint"]),
                    float(meta["reference_area_m2"]),
                )
                for component_indices in components
            ]
            chosen_region, selection_status = select_cross_section_region(regions)
            face_areas = [
                float(dense_faces.polygon_area([points[point_id] for point_id in face]))
                for face in faces
            ]
            total_area = float(np.sum(np.array(face_areas, dtype=float))) if face_areas else 0.0
            total_area_weighted_temp = (
                float(np.sum(np.array(face_areas, dtype=float) * np.array(face_t_values, dtype=float)) / total_area)
                if total_area > EPS and face_t_values
                else math.nan
            )
            rows.append(
                {
                    "time_s": time_value,
                    "span_name": str(meta["span_name"]),
                    "bin_index": int(meta["bin_index"]),
                    "s_mid_m": float(meta["s_mid_m"]),
                    "bulk_temp_area_avg_k": (
                        float(chosen_region["temp_area_weighted_k"]) if chosen_region else math.nan
                    ),
                    "bulk_temp_flow_weighted_k": (
                        float(chosen_region["temp_flow_weighted_k"]) if chosen_region else math.nan
                    ),
                    "bulk_temp_union_area_avg_k": float(total_area_weighted_temp),
                    "cross_section_faces": (
                        float(chosen_region["face_count"]) if chosen_region else math.nan
                    ),
                    "cross_section_area_m2": (
                        float(chosen_region["area_m2"]) if chosen_region else math.nan
                    ),
                    "cross_section_total_faces": float(len(faces)),
                    "cross_section_total_area_m2": float(total_area),
                    "cross_section_region_count": float(len(regions)),
                    "cross_section_reference_area_m2": float(meta["reference_area_m2"]),
                    "cross_section_region_selection_status": selection_status,
                    "cross_section_chosen_region_signed_mass_flux_kg_s": (
                        float(chosen_region["signed_mass_flux_kg_s"]) if chosen_region else math.nan
                    ),
                    "cross_section_chosen_region_aligned_signed_mass_flux_kg_s": (
                        float(chosen_region["aligned_signed_mass_flux_kg_s"]) if chosen_region else math.nan
                    ),
                    "cross_section_chosen_region_positive_mass_flux_kg_s": (
                        float(chosen_region["positive_mass_flux_kg_s"]) if chosen_region else math.nan
                    ),
                    "cross_section_chosen_region_area_ratio_to_reference": (
                        float(chosen_region["area_ratio_to_reference"]) if chosen_region else math.nan
                    ),
                    "selection": surface_name,
                }
            )
            processed_surface_count += 1
            if (
                processed_surface_count == 1
                or processed_surface_count == len(available_surface_names)
                or processed_surface_count % progress_interval == 0
            ):
                elapsed_s = time.perf_counter() - time_start
                print(
                    "[cross-section] "
                    f"time {time_dir.name}: processed {processed_surface_count}/{len(available_surface_names)} "
                    f"surfaces in {elapsed_s:.1f}s",
                    flush=True,
                )
        total_elapsed_s = time.perf_counter() - time_start
        print(
            f"[cross-section] time {time_dir.name}: finished {processed_surface_count} surfaces in {total_elapsed_s:.1f}s",
            flush=True,
        )
    return rows


def build_cross_section_temperature_lookup(
    rows: list[dict[str, Any]],
) -> dict[tuple[float, str, int], dict[str, float]]:
    lookup: dict[tuple[float, str, int], dict[str, Any]] = {}
    for row in rows:
        key = (float(row["time_s"]), str(row["span_name"]), int(row["bin_index"]))
        lookup[key] = {
            "bulk_temp_area_avg_k": float(safe_float(row.get("bulk_temp_area_avg_k"), math.nan)),
            "bulk_temp_flow_weighted_k": float(safe_float(row.get("bulk_temp_flow_weighted_k"), math.nan)),
            "bulk_temp_union_area_avg_k": float(safe_float(row.get("bulk_temp_union_area_avg_k"), math.nan)),
            "cross_section_faces": float(safe_float(row.get("cross_section_faces"), math.nan)),
            "cross_section_area_m2": float(safe_float(row.get("cross_section_area_m2"), math.nan)),
            "cross_section_total_faces": float(safe_float(row.get("cross_section_total_faces"), math.nan)),
            "cross_section_total_area_m2": float(safe_float(row.get("cross_section_total_area_m2"), math.nan)),
            "cross_section_region_count": float(safe_float(row.get("cross_section_region_count"), math.nan)),
            "cross_section_reference_area_m2": float(
                safe_float(row.get("cross_section_reference_area_m2"), math.nan)
            ),
            "cross_section_region_selection_status": str(
                row.get("cross_section_region_selection_status", "")
            ),
            "cross_section_chosen_region_signed_mass_flux_kg_s": float(
                safe_float(row.get("cross_section_chosen_region_signed_mass_flux_kg_s"), math.nan)
            ),
            "cross_section_chosen_region_aligned_signed_mass_flux_kg_s": float(
                safe_float(
                    row.get("cross_section_chosen_region_aligned_signed_mass_flux_kg_s"),
                    math.nan,
                )
            ),
            "cross_section_chosen_region_positive_mass_flux_kg_s": float(
                safe_float(row.get("cross_section_chosen_region_positive_mass_flux_kg_s"), math.nan)
            ),
            "cross_section_chosen_region_area_ratio_to_reference": float(
                safe_float(row.get("cross_section_chosen_region_area_ratio_to_reference"), math.nan)
            ),
        }
    return lookup


def load_raw_face_geometry(
    case_dir: Path,
    major_spans: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    boundary_entries = dense_faces.parse_boundary(case_dir / "constant" / "polyMesh" / "boundary")
    patch_to_span: dict[str, str] = {}
    missing_patches: list[str] = []
    target_ranges: list[tuple[int, int, str]] = []

    for span_name, definition in major_spans.items():
        for patch_name in definition["wall_patches"]:
            patch_to_span[str(patch_name)] = span_name
            entry = boundary_entries.get(str(patch_name))
            if entry is None:
                missing_patches.append(str(patch_name))
                continue
            start_face = int(entry["startFace"])
            n_faces = int(entry["nFaces"])
            target_ranges.append((start_face, start_face + n_faces, str(patch_name)))
    if missing_patches:
        raise RuntimeError(f"Major-span wall patches missing from boundary: {sorted(missing_patches)}")

    face_map = dense_faces.load_selected_faces(case_dir / "constant" / "polyMesh" / "faces", target_ranges)
    point_ids = {point_id for entry in face_map.values() for point_id in entry["point_ids"]}
    point_map = dense_faces.load_selected_points(case_dir / "constant" / "polyMesh" / "points", point_ids)

    geometry_rows: list[dict[str, Any]] = []
    span_face_counts: dict[str, int] = defaultdict(int)
    span_wall_area: dict[str, float] = defaultdict(float)

    for face_index, entry in sorted(face_map.items()):
        patch_name = str(entry["patch_name"])
        span_name = patch_to_span[patch_name]
        definition = major_spans[span_name]
        point_coords = [point_map[point_id] for point_id in entry["point_ids"]]
        center = np.mean(np.vstack(point_coords), axis=0)
        area_m2 = dense_faces.polygon_area(point_coords)
        geometry_rows.append(
            {
                "face_index": int(face_index),
                "patch_name": patch_name,
                "span_name": span_name,
                "span_kind": str(definition["kind"]),
                "area_m2": float(area_m2),
                "center_x_m": float(center[0]),
                "center_y_m": float(center[1]),
                "center_z_m": float(center[2]),
            }
        )
        span_face_counts[span_name] += 1
        span_wall_area[span_name] += float(area_m2)

    meta = {
        "selected_patch_count": len(set(flatten_major_wall_patches(major_spans))),
        "selected_face_count": len(geometry_rows),
        "selected_point_count": len(point_map),
        "span_face_count": {span_name: int(count) for span_name, count in sorted(span_face_counts.items())},
        "span_wall_area_m2": {span_name: float(area) for span_name, area in sorted(span_wall_area.items())},
    }
    return geometry_rows, meta


def load_boundary_patch_centroids(case_dir: Path, patch_names: list[str]) -> dict[str, np.ndarray]:
    if not patch_names:
        return {}
    boundary_entries = dense_faces.parse_boundary(case_dir / "constant" / "polyMesh" / "boundary")
    target_ranges: list[tuple[int, int, str]] = []
    missing_patches: list[str] = []
    for patch_name in patch_names:
        entry = boundary_entries.get(str(patch_name))
        if entry is None:
            missing_patches.append(str(patch_name))
            continue
        start_face = int(entry["startFace"])
        n_faces = int(entry["nFaces"])
        target_ranges.append((start_face, start_face + n_faces, str(patch_name)))
    if missing_patches:
        raise RuntimeError(f"Boundary anchor patches missing from boundary: {sorted(missing_patches)}")

    face_map = dense_faces.load_selected_faces(case_dir / "constant" / "polyMesh" / "faces", target_ranges)
    point_ids = {point_id for entry in face_map.values() for point_id in entry["point_ids"]}
    point_map = dense_faces.load_selected_points(case_dir / "constant" / "polyMesh" / "points", point_ids)
    grouped_faces: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in face_map.values():
        grouped_faces[str(entry["patch_name"])].append(entry)

    centroids: dict[str, np.ndarray] = {}
    for patch_name, payload in grouped_faces.items():
        face_centers: list[np.ndarray] = []
        face_areas: list[float] = []
        for entry in payload:
            point_coords = [point_map[point_id] for point_id in entry["point_ids"]]
            face_centers.append(np.mean(np.vstack(point_coords), axis=0))
            face_areas.append(float(dense_faces.polygon_area(point_coords)))
        centroids[patch_name] = np.average(
            np.vstack(face_centers),
            axis=0,
            weights=np.array(face_areas, dtype=float),
        )
    return centroids


def build_patch_centroid_polylines(
    raw_face_rows: list[dict[str, Any]],
    major_spans: dict[str, dict[str, Any]],
    boundary_patch_centroids: dict[str, np.ndarray] | None = None,
) -> dict[str, dict[str, Any]]:
    boundary_patch_centroids = boundary_patch_centroids or {}
    grouped_by_patch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in raw_face_rows:
        grouped_by_patch[str(row["patch_name"])].append(row)

    patch_centers: dict[str, np.ndarray] = {}
    for patch_name, payload in grouped_by_patch.items():
        areas = np.array([float(row["area_m2"]) for row in payload], dtype=float)
        centers = np.array(
            [
                [float(row["center_x_m"]), float(row["center_y_m"]), float(row["center_z_m"])]
                for row in payload
            ],
            dtype=float,
        )
        patch_centers[patch_name] = np.average(centers, axis=0, weights=areas)

    span_polylines: dict[str, dict[str, Any]] = {}
    for span_name, definition in major_spans.items():
        if str(definition.get("streamwise_coordinate_method", "")) != "patch_centroid_polyline":
            continue
        points: list[np.ndarray] = []
        labels: list[str] = []
        start_patch = str(definition.get("start_patch", ""))
        end_patch = str(definition.get("end_patch", ""))
        if start_patch in boundary_patch_centroids:
            points.append(np.array(boundary_patch_centroids[start_patch], dtype=float))
            labels.append(start_patch)
        for patch_name in definition["wall_patches"]:
            patch_key = str(patch_name)
            if patch_key not in patch_centers:
                raise RuntimeError(f"Patch centroid missing for {span_name}:{patch_key}")
            points.append(np.array(patch_centers[patch_key], dtype=float))
            labels.append(patch_key)
        if end_patch in boundary_patch_centroids:
            points.append(np.array(boundary_patch_centroids[end_patch], dtype=float))
            labels.append(end_patch)
        span_polylines[span_name] = {"points": points, "labels": labels}
    return span_polylines


def project_point_onto_explicit_polyline(
    point_xyz: np.ndarray,
    points: list[np.ndarray],
    labels: list[str],
) -> tuple[float, float, str, str, np.ndarray]:
    arclength = [0.0]
    for index in range(1, len(points)):
        arclength.append(arclength[-1] + float(np.linalg.norm(points[index] - points[index - 1])))
    point = np.array(point_xyz, dtype=float)
    best_distance = float("inf")
    best_s = 0.0
    best_segment = (labels[0], labels[1])
    best_tangent = points[1] - points[0]
    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]
        segment = end - start
        denom = float(np.dot(segment, segment))
        if denom <= EPS:
            fraction = 0.0
            projection = start
        else:
            fraction = float(np.clip(np.dot(point - start, segment) / denom, 0.0, 1.0))
            projection = start + fraction * segment
        distance_value = float(np.linalg.norm(point - projection))
        if distance_value < best_distance:
            best_distance = distance_value
            best_s = arclength[index] + fraction * (arclength[index + 1] - arclength[index])
            best_segment = (labels[index], labels[index + 1])
            best_tangent = segment
    tangent_norm = float(np.linalg.norm(best_tangent))
    tangent = best_tangent / max(tangent_norm, EPS)
    return best_s, best_distance, best_segment[0], best_segment[1], tangent


def build_face_geometry(
    raw_face_rows: list[dict[str, Any]],
    station_centers: dict[str, tuple[float, float, float]],
    major_spans: dict[str, dict[str, Any]],
    patch_centroid_polylines: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    patch_centroid_polylines = patch_centroid_polylines or {}
    geometry_rows: list[dict[str, Any]] = []
    for row in raw_face_rows:
        span_name = str(row["span_name"])
        definition = major_spans[span_name]
        center = np.array(
            [float(row["center_x_m"]), float(row["center_y_m"]), float(row["center_z_m"])],
            dtype=float,
        )
        if span_name in patch_centroid_polylines:
            local_s, distance_to_centerline_m, segment_start_label, segment_end_label, tangent = (
                project_point_onto_explicit_polyline(
                    center,
                    patch_centroid_polylines[span_name]["points"],
                    patch_centroid_polylines[span_name]["labels"],
                )
            )
        else:
            local_s, distance_to_centerline_m, segment_start_label, segment_end_label = project_point_onto_polyline(
                center,
                definition["centerline_labels"],
                station_centers,
            )
            segment_start = np.array(station_centers[segment_start_label], dtype=float)
            segment_end = np.array(station_centers[segment_end_label], dtype=float)
            segment_vector = segment_end - segment_start
            segment_norm = float(np.linalg.norm(segment_vector))
            tangent = segment_vector / max(segment_norm, EPS)
        geometry_rows.append(
            {
                **row,
                "s_span_m": float(local_s),
                "distance_to_centerline_m": float(distance_to_centerline_m),
                "tangent_x": float(tangent[0]),
                "tangent_y": float(tangent[1]),
                "tangent_z": float(tangent[2]),
                "segment_start_label": str(segment_start_label),
                "segment_end_label": str(segment_end_label),
            }
        )
    return geometry_rows


def build_face_samples(
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
        time_value = float(time_name)
        wall_values = dense_faces.parse_boundary_field(case_dir / time_name / "wallShearStress", selected_patches, "vector")
        yplus_values = dense_faces.parse_boundary_field(case_dir / time_name / "yPlus", selected_patches, "scalar")
        p_values = dense_faces.parse_boundary_field(case_dir / time_name / "p", selected_patches, "scalar")
        p_rgh_values = dense_faces.parse_boundary_field(case_dir / time_name / "p_rgh", selected_patches, "scalar")
        t_values = dense_faces.parse_boundary_field(
            case_dir / time_name / "T",
            selected_patches,
            "scalar",
            face_count_by_patch=face_count_by_patch,
        )
        wall_heatflux_values = dense_faces.parse_boundary_field(
            case_dir / time_name / "wallHeatFlux",
            selected_patches,
            "scalar",
            face_count_by_patch=face_count_by_patch,
        )
        for patch_name, face_rows in ordered_geometry_by_patch.items():
            tau_vectors = wall_values[patch_name]
            yplus_scalars = yplus_values[patch_name]
            p_scalars = p_values[patch_name]
            p_rgh_scalars = p_rgh_values[patch_name]
            t_scalars = t_values[patch_name]
            wall_heatflux_scalars = wall_heatflux_values[patch_name]
            if (
                len(tau_vectors) != len(face_rows)
                or len(yplus_scalars) != len(face_rows)
                or len(p_scalars) != len(face_rows)
                or len(p_rgh_scalars) != len(face_rows)
                or len(t_scalars) != len(face_rows)
                or len(wall_heatflux_scalars) != len(face_rows)
            ):
                raise RuntimeError(
                    f"Patch {patch_name} field length mismatch at time {time_name}: "
                    f"{len(face_rows)} faces, {len(tau_vectors)} wallShearStress, {len(yplus_scalars)} yPlus, "
                    f"{len(p_scalars)} p, {len(p_rgh_scalars)} p_rgh, "
                    f"{len(t_scalars)} T, {len(wall_heatflux_scalars)} wallHeatFlux"
                )
            for index, face_row in enumerate(face_rows):
                tau_vector = tau_vectors[index]
                tangent = np.array(
                    [
                        float(face_row["tangent_x"]),
                        float(face_row["tangent_y"]),
                        float(face_row["tangent_z"]),
                    ],
                    dtype=float,
                )
                tau_streamwise_signed = (
                    float(tau_vector[0]) * float(tangent[0])
                    + float(tau_vector[1]) * float(tangent[1])
                    + float(tau_vector[2]) * float(tangent[2])
                )
                tau_streamwise_abs = abs(tau_streamwise_signed)
                sample_rows.append(
                    {
                        "source_id": source_id,
                        "time_s": float(time_value),
                        "span_name": str(face_row["span_name"]),
                        "span_kind": str(face_row["span_kind"]),
                        "patch_name": patch_name,
                        "face_index": int(face_row["face_index"]),
                        "s_span_m": float(face_row["s_span_m"]),
                        "distance_to_centerline_m": float(face_row["distance_to_centerline_m"]),
                        "area_m2": float(face_row["area_m2"]),
                        "center_x_m": float(face_row["center_x_m"]),
                        "center_y_m": float(face_row["center_y_m"]),
                        "center_z_m": float(face_row["center_z_m"]),
                        "tauw_x_pa": float(tau_vector[0]),
                        "tauw_y_pa": float(tau_vector[1]),
                        "tauw_z_pa": float(tau_vector[2]),
                        "tauw_streamwise_signed_pa": float(tau_streamwise_signed),
                        "tauw_streamwise_abs_pa": float(tau_streamwise_abs),
                        "yplus": float(yplus_scalars[index][0]),
                        "p_wall_pa": float(p_scalars[index][0]),
                        "p_rgh_wall_pa": float(p_rgh_scalars[index][0]),
                        "t_wall_k": float(t_scalars[index][0]),
                        "wall_heatflux_w_m2": float(wall_heatflux_scalars[index][0]),
                    }
                )
    return sample_rows


def build_face_zone_series(runtime_root: Path, face_zone: str) -> tuple[dict[float, float], float]:
    rows = streamwise_builder.merge_scalar_chunks(runtime_root, face_zone, "surfaceFieldValue.dat")
    target_root = runtime_root / "postProcessing" / face_zone
    time_dirs = sorted(
        (
            float(item.name),
            item / "surfaceFieldValue.dat",
        )
        for item in target_root.iterdir()
        if item.is_dir() and streamwise_builder.safe_float(item.name) is not None
    )
    if not rows or not time_dirs:
        raise RuntimeError(f"Mass-flow face-zone history not available for {face_zone}")
    area_m2 = streamwise_builder.parse_surface_area(time_dirs[-1][1])
    series = {float(row["time"]): abs(float(row["value"])) for row in rows}
    return series, float(area_m2)


def build_span_mdot_inputs(
    runtime_root: Path,
    major_spans: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[float, float]], dict[str, float], dict[str, str]]:
    zone_series: dict[str, dict[float, float]] = {}
    zone_area_m2: dict[str, float] = {}
    for span_name, definition in major_spans.items():
        face_zone = definition.get("mdot_face_zone")
        if face_zone and face_zone not in zone_series:
            series, area_m2 = build_face_zone_series(runtime_root, str(face_zone))
            zone_series[str(face_zone)] = series
            zone_area_m2[str(face_zone)] = area_m2

    main_loop_zone_names = [
        str(major_spans[span_name]["mdot_face_zone"])
        for span_name in major_spans
        if major_spans[span_name]["kind"] == "main_loop_leg" and major_spans[span_name].get("mdot_face_zone")
    ]
    test_section_zone_name = str(major_spans["test_section_span"]["mdot_face_zone"])

    main_loop_times = sorted({time_value for zone_name in main_loop_zone_names for time_value in zone_series[zone_name]})
    main_loop_mean_series = {
        time_value: float(np.mean([zone_series[zone_name][time_value] for zone_name in main_loop_zone_names if time_value in zone_series[zone_name]]))
        for time_value in main_loop_times
    }
    main_loop_area_m2 = float(np.mean([zone_area_m2[zone_name] for zone_name in main_loop_zone_names]))

    span_mdot_lookup: dict[str, dict[float, float]] = {}
    span_area_lookup: dict[str, float] = {}
    mdot_source_lookup: dict[str, str] = {}
    for span_name, definition in major_spans.items():
        face_zone = definition.get("mdot_face_zone")
        if face_zone:
            span_mdot_lookup[span_name] = zone_series[str(face_zone)]
            span_area_lookup[span_name] = float(zone_area_m2[str(face_zone)])
            mdot_source_lookup[span_name] = str(face_zone)
        elif definition["kind"] == "main_loop_leg":
            span_mdot_lookup[span_name] = main_loop_mean_series
            span_area_lookup[span_name] = float(main_loop_area_m2)
            mdot_source_lookup[span_name] = "main_loop_mean_abs"
        else:
            span_mdot_lookup[span_name] = zone_series[test_section_zone_name]
            span_area_lookup[span_name] = float(zone_area_m2[test_section_zone_name])
            mdot_source_lookup[span_name] = test_section_zone_name
    return span_mdot_lookup, span_area_lookup, mdot_source_lookup


def build_span_rho_lookup(
    runtime_root: Path,
    major_spans: dict[str, dict[str, Any]],
    density_intercept: float,
    density_slope: float,
) -> tuple[list[dict[str, Any]], dict[str, dict[float, float]], dict[float, float]]:
    tp_rows, _ = streamwise_builder.build_temperature_rows(runtime_root)
    global_rho_map = streamwise_builder.build_tp_bulk_rho_map(tp_rows)
    span_rho_lookup: dict[str, dict[float, float]] = {span_name: {} for span_name in major_spans}
    for row in tp_rows:
        time_value = float(row["time_s"])
        for span_name, definition in major_spans.items():
            tp_values = [
                float(row[label])
                for label in definition["centerline_labels"]
                if label.startswith("TP") and label in row
            ]
            if tp_values:
                mean_tp_k = float(np.mean(np.array(tp_values, dtype=float)))
                span_rho_lookup[span_name][time_value] = float(density_intercept - density_slope * mean_tp_k)
            elif time_value in global_rho_map:
                span_rho_lookup[span_name][time_value] = float(global_rho_map[time_value])
    return tp_rows, span_rho_lookup, global_rho_map


def build_span_temperature_endpoints_lookup(
    tp_rows: list[dict[str, Any]],
    major_spans: dict[str, dict[str, Any]],
) -> dict[str, dict[float, dict[str, float]]]:
    lookup: dict[str, dict[float, dict[str, float]]] = {span_name: {} for span_name in major_spans}
    for row in tp_rows:
        time_value = float(row["time_s"])
        for span_name, definition in major_spans.items():
            tp_labels = [label for label in definition["centerline_labels"] if str(label).startswith("TP")]
            if len(tp_labels) < 2:
                continue
            start_label = str(tp_labels[0])
            end_label = str(tp_labels[-1])
            start_value = safe_float(row.get(start_label))
            end_value = safe_float(row.get(end_label))
            if start_value is None or end_value is None:
                continue
            lookup[span_name][time_value] = {
                "start_tp_k": float(start_value),
                "end_tp_k": float(end_value),
            }
    return lookup


def span_dp_gradient(row: dict[str, Any]) -> float:
    rho = float(row["rho_bulk_kg_m3"])
    bulk_u = float(row["bulk_velocity_m_s"])
    darcy_f = float(row["darcy_f"])
    dh = float(row["hydraulic_diameter_geom_m"])
    if not math.isfinite(darcy_f) or not math.isfinite(rho) or not math.isfinite(bulk_u) or not math.isfinite(dh):
        return math.nan
    if dh <= EPS or bulk_u <= EPS:
        return math.nan
    return float(darcy_f * rho * bulk_u * bulk_u / max(2.0 * dh, EPS))


def finite_difference_pressure_drop_gradient(
    s_values: list[float],
    pressure_values: list[float],
) -> list[float]:
    gradients: list[float] = [math.nan] * len(s_values)
    if len(s_values) < 2:
        return gradients
    for index in range(len(s_values)):
        p_here = pressure_values[index]
        if not math.isfinite(p_here):
            continue
        if index == 0:
            if not math.isfinite(pressure_values[index + 1]):
                continue
            ds = s_values[index + 1] - s_values[index]
            if abs(ds) <= EPS:
                continue
            gradients[index] = -float((pressure_values[index + 1] - p_here) / ds)
        elif index == len(s_values) - 1:
            if not math.isfinite(pressure_values[index - 1]):
                continue
            ds = s_values[index] - s_values[index - 1]
            if abs(ds) <= EPS:
                continue
            gradients[index] = -float((p_here - pressure_values[index - 1]) / ds)
        else:
            p_prev = pressure_values[index - 1]
            p_next = pressure_values[index + 1]
            if not math.isfinite(p_prev) or not math.isfinite(p_next):
                continue
            ds = s_values[index + 1] - s_values[index - 1]
            if abs(ds) <= EPS:
                continue
            gradients[index] = -float((p_next - p_prev) / ds)
    return gradients


def pressure_drop_based_darcy_f(row: dict[str, Any], dp_gradient: float) -> float:
    rho = float(row["rho_bulk_kg_m3"])
    bulk_u = float(row["bulk_velocity_m_s"])
    dh = float(row["hydraulic_diameter_geom_m"])
    if not math.isfinite(dp_gradient) or not math.isfinite(rho) or not math.isfinite(bulk_u) or not math.isfinite(dh):
        return math.nan
    if dh <= EPS or bulk_u <= EPS:
        return math.nan
    return float(2.0 * dh * dp_gradient / max(rho * bulk_u * bulk_u, EPS))


def aggregate_major_loss_rows(
    source_id: str,
    sample_rows: list[dict[str, Any]],
    station_bins: list[dict[str, Any]],
    span_mdot_lookup: dict[str, dict[float, float]],
    span_reference_area_lookup: dict[str, float],
    span_rho_lookup: dict[str, dict[float, float]],
    span_temperature_endpoints_lookup: dict[str, dict[float, dict[str, float]]],
    cross_section_temperature_lookup: dict[tuple[float, str, int], dict[str, float]],
) -> list[dict[str, Any]]:
    bins_by_span: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in station_bins:
        bins_by_span[str(row["span_name"])].append(row)
    for span_name in bins_by_span:
        bins_by_span[span_name] = sorted(bins_by_span[span_name], key=lambda item: int(item["bin_index"]))

    grouped_samples: dict[tuple[float, str], list[dict[str, Any]]] = defaultdict(list)
    for row in sample_rows:
        grouped_samples[(float(row["time_s"]), str(row["span_name"]))].append(row)

    output_rows: list[dict[str, Any]] = []
    selected_times = sorted({float(row["time_s"]) for row in sample_rows})
    for time_value in selected_times:
        for span_name, bins in bins_by_span.items():
            payload = grouped_samples.get((time_value, span_name), [])
            rho_bulk = span_rho_lookup.get(span_name, {}).get(time_value, float("nan"))
            mdot_value = span_mdot_lookup.get(span_name, {}).get(time_value, float("nan"))
            if payload:
                s_values = np.array([float(row["s_span_m"]) for row in payload], dtype=float)
                areas = np.array([float(row["area_m2"]) for row in payload], dtype=float)
                tau_signed_values = np.array([float(row["tauw_streamwise_signed_pa"]) for row in payload], dtype=float)
                tau_abs_values = np.array([float(row["tauw_streamwise_abs_pa"]) for row in payload], dtype=float)
                yplus_values = np.array([float(row["yplus"]) for row in payload], dtype=float)
                p_values = np.array([float(row["p_wall_pa"]) for row in payload], dtype=float)
                p_rgh_values = np.array([float(row["p_rgh_wall_pa"]) for row in payload], dtype=float)
                t_values = np.array([float(row["t_wall_k"]) for row in payload], dtype=float)
                wall_heatflux_values = np.array([float(row["wall_heatflux_w_m2"]) for row in payload], dtype=float)
            else:
                s_values = np.array([], dtype=float)
                areas = np.array([], dtype=float)
                tau_signed_values = np.array([], dtype=float)
                tau_abs_values = np.array([], dtype=float)
                yplus_values = np.array([], dtype=float)
                p_values = np.array([], dtype=float)
                p_rgh_values = np.array([], dtype=float)
                t_values = np.array([], dtype=float)
                wall_heatflux_values = np.array([], dtype=float)

            bin_edges = np.array([float(row["s_start_m"]) for row in bins] + [float(bins[-1]["s_end_m"])], dtype=float)
            bin_indices = np.digitize(s_values, bin_edges, right=False) - 1 if len(s_values) else np.array([], dtype=int)
            if len(bin_indices):
                bin_indices = np.clip(bin_indices, 0, len(bins) - 1)

            span_time_rows: list[dict[str, Any]] = []
            for bin_row in bins:
                bin_index = int(bin_row["bin_index"])
                if len(bin_indices):
                    mask = bin_indices == bin_index
                    face_count = int(np.count_nonzero(mask))
                else:
                    mask = np.array([], dtype=bool)
                    face_count = 0

                if face_count <= 0:
                    span_time_rows.append(
                        {
                            "source_id": source_id,
                            "time_s": float(time_value),
                            "span_name": span_name,
                            "span_kind": str(bin_row["span_kind"]),
                            "bin_index": bin_index,
                            "s_start_m": float(bin_row["s_start_m"]),
                            "s_end_m": float(bin_row["s_end_m"]),
                            "s_mid_m": float(bin_row["s_mid_m"]),
                            "wall_face_count": 0,
                            "wall_area_m2": 0.0,
                            "local_wetted_perimeter_m": math.nan,
                            "hydraulic_diameter_geom_m": math.nan,
                            "flow_area_geom_m2": math.nan,
                            "rho_bulk_kg_m3": float(rho_bulk),
                            "mdot_mean_abs_kg_s": float(mdot_value),
                            "bulk_velocity_m_s": math.nan,
                            "dp_major_gradient_pa_per_m": math.nan,
                            "dp_major_gradient_direct_prgh_pa_per_m": math.nan,
                            "dp_major_gradient_direct_p_pa_per_m": math.nan,
                            "flow_alignment_sign": math.nan,
                            "tauw_streamwise_mean_signed_pa": math.nan,
                            "tauw_streamwise_mean_abs_pa": math.nan,
                            "tauw_streamwise_std_abs_pa": math.nan,
                            "tauw_streamwise_max_rel_dev": math.nan,
                            "darcy_f": math.nan,
                            "darcy_f_pressure_drop_prgh": math.nan,
                            "fanning_cf_shear": math.nan,
                            "fanning_cf_pressure_drop_prgh": math.nan,
                            "momentum_resistance_estimated_pa_s_kg_m": math.nan,
                            "momentum_resistance_direct_prgh_pa_s_kg_m": math.nan,
                            "p_wall_area_avg_pa": math.nan,
                            "p_rgh_wall_area_avg_pa": math.nan,
                            "t_wall_area_avg_k": math.nan,
                            "bulk_temp_fluid_area_avg_k": math.nan,
                            "bulk_temp_area_weighted_k": math.nan,
                            "bulk_temp_union_area_avg_k": math.nan,
                            "bulk_cross_section_face_count": math.nan,
                            "bulk_cross_section_area_m2": math.nan,
                            "bulk_cross_section_total_face_count": math.nan,
                            "bulk_cross_section_total_area_m2": math.nan,
                            "bulk_cross_section_region_count": math.nan,
                            "bulk_cross_section_reference_area_m2": math.nan,
                            "bulk_cross_section_area_ratio_to_geom": math.nan,
                            "bulk_cross_section_chosen_region_area_ratio_to_reference": math.nan,
                            "bulk_cross_section_chosen_region_signed_mass_flux_kg_s": math.nan,
                            "bulk_cross_section_chosen_region_aligned_signed_mass_flux_kg_s": math.nan,
                            "bulk_cross_section_chosen_region_positive_mass_flux_kg_s": math.nan,
                            "bulk_cross_section_region_selection_status": "missing_region",
                            "bulk_temp_tp_endpoint_proxy_k": math.nan,
                            "bulk_minus_wall_tp_endpoint_proxy_k": math.nan,
                            "effective_htc_tp_endpoint_proxy_w_m2_k": math.nan,
                            "effective_ua_per_m_tp_endpoint_proxy_w_m_k": math.nan,
                            "effective_thermal_resistance_tp_endpoint_proxy_k_m_w": math.nan,
                            "bulk_minus_wall_temp_k": math.nan,
                            "wall_heatflux_area_avg_w_m2": math.nan,
                            "wall_heat_per_length_w_m": math.nan,
                            "effective_htc_w_m2_k": math.nan,
                            "effective_ua_per_m_w_m_k": math.nan,
                            "effective_thermal_resistance_k_m_w": math.nan,
                            "thermal_support_status": "missing_wall_faces",
                            "thermal_support_warning_flag": "yes",
                            "yplus_area_avg": math.nan,
                            "yplus_max": math.nan,
                            "warning_flag": "yes",
                        }
                    )
                    continue

                wall_area_m2 = float(np.sum(areas[mask]))
                ds_m = float(max(float(bin_row["bin_width_m"]), EPS))
                local_wetted_perimeter_m = estimate_perimeter_from_wall_area(wall_area_m2, ds_m)
                hydraulic_diameter_geom_m = estimate_circular_hydraulic_diameter_from_perimeter(local_wetted_perimeter_m)
                flow_area_geom_m2 = estimate_circular_area_from_perimeter(local_wetted_perimeter_m)
                tau_mean_signed = float(np.sum(areas[mask] * tau_signed_values[mask]) / max(wall_area_m2, EPS))
                tau_mean_abs = float(np.sum(areas[mask] * tau_abs_values[mask]) / max(wall_area_m2, EPS))
                tau_std_abs = float(
                    math.sqrt(
                        np.sum(areas[mask] * (tau_abs_values[mask] - tau_mean_abs) ** 2)
                        / max(wall_area_m2, EPS)
                    )
                )
                tau_max_rel_dev = float(
                    np.max(np.abs(tau_abs_values[mask] - tau_mean_abs)) / max(tau_mean_abs, EPS)
                )
                yplus_area_avg = float(np.sum(areas[mask] * yplus_values[mask]) / max(wall_area_m2, EPS))
                yplus_max = float(np.max(yplus_values[mask]))
                p_wall_area_avg = float(np.sum(areas[mask] * p_values[mask]) / max(wall_area_m2, EPS))
                p_rgh_wall_area_avg = float(np.sum(areas[mask] * p_rgh_values[mask]) / max(wall_area_m2, EPS))
                t_wall_area_avg = float(np.sum(areas[mask] * t_values[mask]) / max(wall_area_m2, EPS))
                wall_heatflux_area_avg = float(np.sum(areas[mask] * wall_heatflux_values[mask]) / max(wall_area_m2, EPS))
                span_length = max(float(bins[-1]["s_end_m"]), EPS)
                s_fraction = float(bin_row["s_mid_m"]) / span_length
                temp_endpoints = span_temperature_endpoints_lookup.get(span_name, {}).get(time_value, {})
                start_tp_k = safe_float(temp_endpoints.get("start_tp_k"), math.nan)
                end_tp_k = safe_float(temp_endpoints.get("end_tp_k"), math.nan)
                if start_tp_k is not None and end_tp_k is not None and math.isfinite(start_tp_k) and math.isfinite(end_tp_k):
                    bulk_temp_tp_proxy = float(start_tp_k + s_fraction * (end_tp_k - start_tp_k))
                else:
                    bulk_temp_tp_proxy = math.nan
                cross_section_payload = cross_section_temperature_lookup.get((time_value, span_name, bin_index), {})
                bulk_temp_cross_section = float(
                    safe_float(cross_section_payload.get("bulk_temp_flow_weighted_k"), math.nan)
                )
                bulk_temp_area_weighted = float(
                    safe_float(cross_section_payload.get("bulk_temp_area_avg_k"), math.nan)
                )
                bulk_temp_union_area_avg = float(
                    safe_float(cross_section_payload.get("bulk_temp_union_area_avg_k"), math.nan)
                )
                bulk_cross_section_faces = float(
                    safe_float(cross_section_payload.get("cross_section_faces"), math.nan)
                )
                bulk_cross_section_area_m2 = float(
                    safe_float(cross_section_payload.get("cross_section_area_m2"), math.nan)
                )
                bulk_cross_section_total_faces = float(
                    safe_float(cross_section_payload.get("cross_section_total_faces"), math.nan)
                )
                bulk_cross_section_total_area_m2 = float(
                    safe_float(cross_section_payload.get("cross_section_total_area_m2"), math.nan)
                )
                bulk_cross_section_region_count = float(
                    safe_float(cross_section_payload.get("cross_section_region_count"), math.nan)
                )
                bulk_cross_section_reference_area_m2 = float(
                    safe_float(cross_section_payload.get("cross_section_reference_area_m2"), math.nan)
                )
                bulk_cross_section_area_ratio_to_reference = float(
                    safe_float(
                        cross_section_payload.get("cross_section_chosen_region_area_ratio_to_reference"),
                        math.nan,
                    )
                )
                bulk_cross_section_signed_mass_flux = float(
                    safe_float(
                        cross_section_payload.get("cross_section_chosen_region_signed_mass_flux_kg_s"),
                        math.nan,
                    )
                )
                bulk_cross_section_aligned_signed_mass_flux = float(
                    safe_float(
                        cross_section_payload.get(
                            "cross_section_chosen_region_aligned_signed_mass_flux_kg_s"
                        ),
                        math.nan,
                    )
                )
                bulk_cross_section_positive_mass_flux = float(
                    safe_float(
                        cross_section_payload.get("cross_section_chosen_region_positive_mass_flux_kg_s"),
                        math.nan,
                    )
                )
                bulk_cross_section_selection_status = str(
                    cross_section_payload.get("cross_section_region_selection_status", "missing_region")
                )
                if math.isfinite(flow_area_geom_m2) and flow_area_geom_m2 > EPS and math.isfinite(bulk_cross_section_area_m2):
                    bulk_cross_section_area_ratio_to_geom = float(bulk_cross_section_area_m2 / flow_area_geom_m2)
                else:
                    bulk_cross_section_area_ratio_to_geom = math.nan
                if math.isfinite(bulk_temp_cross_section) and math.isfinite(t_wall_area_avg):
                    bulk_minus_wall_temp = float(bulk_temp_cross_section - t_wall_area_avg)
                else:
                    bulk_minus_wall_temp = math.nan
                if math.isfinite(bulk_temp_tp_proxy) and math.isfinite(t_wall_area_avg):
                    bulk_minus_wall_tp_proxy = float(bulk_temp_tp_proxy - t_wall_area_avg)
                else:
                    bulk_minus_wall_tp_proxy = math.nan
                wall_heat_per_length = float(wall_heatflux_area_avg * local_wetted_perimeter_m)
                thermal_support_status = "usable"
                if bulk_cross_section_selection_status != "aligned_area_match":
                    thermal_support_status = bulk_cross_section_selection_status
                elif not math.isfinite(bulk_cross_section_positive_mass_flux) or bulk_cross_section_positive_mass_flux <= THERMAL_MIN_POSITIVE_FLUX_KG_S:
                    thermal_support_status = "insufficient_aligned_flux"
                elif (
                    not math.isfinite(bulk_cross_section_area_ratio_to_reference)
                    or bulk_cross_section_area_ratio_to_reference < THERMAL_MIN_AREA_RATIO_TO_REFERENCE
                    or bulk_cross_section_area_ratio_to_reference > THERMAL_MAX_AREA_RATIO_TO_REFERENCE
                ):
                    thermal_support_status = "area_ratio_out_of_range"
                elif not math.isfinite(bulk_minus_wall_temp) or abs(bulk_minus_wall_temp) < THERMAL_MIN_ABS_DELTA_T_K:
                    thermal_support_status = "small_delta_t"
                thermal_support_warning_flag = "yes" if thermal_support_status != "usable" else "no"
                if thermal_support_status == "usable":
                    effective_htc = float(abs(wall_heatflux_area_avg) / abs(bulk_minus_wall_temp))
                    effective_ua_per_m = float(abs(wall_heat_per_length) / abs(bulk_minus_wall_temp))
                else:
                    effective_htc = math.nan
                    effective_ua_per_m = math.nan
                if math.isfinite(bulk_minus_wall_tp_proxy) and abs(bulk_minus_wall_tp_proxy) > EPS:
                    effective_htc_tp_proxy = float(abs(wall_heatflux_area_avg) / abs(bulk_minus_wall_tp_proxy))
                    effective_ua_per_m_tp_proxy = float(abs(wall_heat_per_length) / abs(bulk_minus_wall_tp_proxy))
                else:
                    effective_htc_tp_proxy = math.nan
                    effective_ua_per_m_tp_proxy = math.nan
                effective_thermal_resistance = (
                    float(1.0 / effective_ua_per_m)
                    if math.isfinite(effective_ua_per_m) and abs(effective_ua_per_m) > EPS
                    else math.nan
                )
                effective_thermal_resistance_tp_proxy = (
                    float(1.0 / effective_ua_per_m_tp_proxy)
                    if math.isfinite(effective_ua_per_m_tp_proxy) and abs(effective_ua_per_m_tp_proxy) > EPS
                    else math.nan
                )

                if math.isfinite(float(rho_bulk)) and math.isfinite(float(mdot_value)) and flow_area_geom_m2 > EPS:
                    bulk_velocity_m_s = float(abs(float(mdot_value)) / max(float(rho_bulk) * flow_area_geom_m2, EPS))
                    darcy_f = float(
                        8.0 * tau_mean_abs / max(float(rho_bulk) * bulk_velocity_m_s * bulk_velocity_m_s, EPS)
                    )
                else:
                    bulk_velocity_m_s = math.nan
                    darcy_f = math.nan
                fanning_cf_shear = float(0.25 * darcy_f) if math.isfinite(darcy_f) else math.nan
                dp_major_gradient = span_dp_gradient(
                    {
                        "rho_bulk_kg_m3": rho_bulk,
                        "bulk_velocity_m_s": bulk_velocity_m_s,
                        "darcy_f": darcy_f,
                        "hydraulic_diameter_geom_m": hydraulic_diameter_geom_m,
                    }
                )
                momentum_resistance_estimated = (
                    float(dp_major_gradient / mdot_value)
                    if math.isfinite(dp_major_gradient) and math.isfinite(mdot_value) and abs(mdot_value) > EPS
                    else math.nan
                )

                span_time_rows.append(
                    {
                        "source_id": source_id,
                        "time_s": float(time_value),
                        "span_name": span_name,
                        "span_kind": str(bin_row["span_kind"]),
                        "bin_index": bin_index,
                        "s_start_m": float(bin_row["s_start_m"]),
                        "s_end_m": float(bin_row["s_end_m"]),
                        "s_mid_m": float(bin_row["s_mid_m"]),
                        "wall_face_count": face_count,
                        "wall_area_m2": float(wall_area_m2),
                        "local_wetted_perimeter_m": float(local_wetted_perimeter_m),
                        "hydraulic_diameter_geom_m": float(hydraulic_diameter_geom_m),
                        "flow_area_geom_m2": float(flow_area_geom_m2),
                        "rho_bulk_kg_m3": float(rho_bulk),
                        "mdot_mean_abs_kg_s": float(mdot_value),
                        "bulk_velocity_m_s": float(bulk_velocity_m_s),
                        "dp_major_gradient_pa_per_m": float(dp_major_gradient),
                        "dp_major_gradient_direct_prgh_pa_per_m": math.nan,
                        "dp_major_gradient_direct_p_pa_per_m": math.nan,
                        "flow_alignment_sign": math.nan,
                        "tauw_streamwise_mean_signed_pa": float(tau_mean_signed),
                        "tauw_streamwise_mean_abs_pa": float(tau_mean_abs),
                        "tauw_streamwise_std_abs_pa": float(tau_std_abs),
                        "tauw_streamwise_max_rel_dev": float(tau_max_rel_dev),
                        "darcy_f": float(darcy_f),
                        "darcy_f_pressure_drop_prgh": math.nan,
                        "fanning_cf_shear": float(fanning_cf_shear),
                        "fanning_cf_pressure_drop_prgh": math.nan,
                        "momentum_resistance_estimated_pa_s_kg_m": float(momentum_resistance_estimated),
                        "momentum_resistance_direct_prgh_pa_s_kg_m": math.nan,
                        "p_wall_area_avg_pa": float(p_wall_area_avg),
                        "p_rgh_wall_area_avg_pa": float(p_rgh_wall_area_avg),
                        "t_wall_area_avg_k": float(t_wall_area_avg),
                        "bulk_temp_fluid_area_avg_k": float(bulk_temp_cross_section),
                        "bulk_temp_area_weighted_k": float(bulk_temp_area_weighted),
                        "bulk_temp_union_area_avg_k": float(bulk_temp_union_area_avg),
                        "bulk_cross_section_face_count": float(bulk_cross_section_faces),
                        "bulk_cross_section_area_m2": float(bulk_cross_section_area_m2),
                        "bulk_cross_section_total_face_count": float(bulk_cross_section_total_faces),
                        "bulk_cross_section_total_area_m2": float(bulk_cross_section_total_area_m2),
                        "bulk_cross_section_region_count": float(bulk_cross_section_region_count),
                        "bulk_cross_section_reference_area_m2": float(bulk_cross_section_reference_area_m2),
                        "bulk_cross_section_area_ratio_to_geom": float(bulk_cross_section_area_ratio_to_geom),
                        "bulk_cross_section_chosen_region_area_ratio_to_reference": float(
                            bulk_cross_section_area_ratio_to_reference
                        ),
                        "bulk_cross_section_chosen_region_signed_mass_flux_kg_s": float(
                            bulk_cross_section_signed_mass_flux
                        ),
                        "bulk_cross_section_chosen_region_aligned_signed_mass_flux_kg_s": float(
                            bulk_cross_section_aligned_signed_mass_flux
                        ),
                        "bulk_cross_section_chosen_region_positive_mass_flux_kg_s": float(
                            bulk_cross_section_positive_mass_flux
                        ),
                        "bulk_cross_section_region_selection_status": bulk_cross_section_selection_status,
                        "bulk_temp_tp_endpoint_proxy_k": float(bulk_temp_tp_proxy),
                        "bulk_minus_wall_tp_endpoint_proxy_k": float(bulk_minus_wall_tp_proxy),
                        "effective_htc_tp_endpoint_proxy_w_m2_k": float(effective_htc_tp_proxy),
                        "effective_ua_per_m_tp_endpoint_proxy_w_m_k": float(effective_ua_per_m_tp_proxy),
                        "effective_thermal_resistance_tp_endpoint_proxy_k_m_w": float(
                            effective_thermal_resistance_tp_proxy
                        ),
                        "bulk_minus_wall_temp_k": float(bulk_minus_wall_temp),
                        "wall_heatflux_area_avg_w_m2": float(wall_heatflux_area_avg),
                        "wall_heat_per_length_w_m": float(wall_heat_per_length),
                        "effective_htc_w_m2_k": float(effective_htc),
                        "effective_ua_per_m_w_m_k": float(effective_ua_per_m),
                        "effective_thermal_resistance_k_m_w": float(effective_thermal_resistance),
                        "thermal_support_status": thermal_support_status,
                        "thermal_support_warning_flag": thermal_support_warning_flag,
                        "yplus_area_avg": float(yplus_area_avg),
                        "yplus_max": float(yplus_max),
                        "warning_flag": (
                            "yes"
                            if tau_max_rel_dev > 0.20 or thermal_support_warning_flag == "yes"
                            else "no"
                        ),
                    }
                )
            s_mid_values = [float(row["s_mid_m"]) for row in span_time_rows]
            p_wall_values = [float(row["p_wall_area_avg_pa"]) for row in span_time_rows]
            p_rgh_values = [float(row["p_rgh_wall_area_avg_pa"]) for row in span_time_rows]
            raw_direct_prgh_gradients = finite_difference_pressure_drop_gradient(s_mid_values, p_rgh_values)
            raw_direct_p_gradients = finite_difference_pressure_drop_gradient(s_mid_values, p_wall_values)
            first_valid_prgh = next((value for value in p_rgh_values if math.isfinite(value)), math.nan)
            last_valid_prgh = next((value for value in reversed(p_rgh_values) if math.isfinite(value)), math.nan)
            if math.isfinite(first_valid_prgh) and math.isfinite(last_valid_prgh) and (first_valid_prgh - last_valid_prgh) < 0.0:
                flow_alignment_sign = -1.0
            else:
                flow_alignment_sign = 1.0
            for index, row in enumerate(span_time_rows):
                dp_gradient_direct_prgh = (
                    float(flow_alignment_sign * raw_direct_prgh_gradients[index])
                    if math.isfinite(raw_direct_prgh_gradients[index])
                    else math.nan
                )
                dp_gradient_direct_p = (
                    float(flow_alignment_sign * raw_direct_p_gradients[index])
                    if math.isfinite(raw_direct_p_gradients[index])
                    else math.nan
                )
                darcy_f_pressure_drop = pressure_drop_based_darcy_f(row, dp_gradient_direct_prgh)
                fanning_cf_pressure_drop = (
                    float(0.25 * darcy_f_pressure_drop) if math.isfinite(darcy_f_pressure_drop) else math.nan
                )
                mdot_value = float(row["mdot_mean_abs_kg_s"])
                momentum_resistance_direct = (
                    float(dp_gradient_direct_prgh / mdot_value)
                    if math.isfinite(dp_gradient_direct_prgh) and math.isfinite(mdot_value) and abs(mdot_value) > EPS
                    else math.nan
                )
                row["dp_major_gradient_direct_prgh_pa_per_m"] = float(dp_gradient_direct_prgh)
                row["dp_major_gradient_direct_p_pa_per_m"] = float(dp_gradient_direct_p)
                row["flow_alignment_sign"] = float(flow_alignment_sign)
                row["darcy_f_pressure_drop_prgh"] = float(darcy_f_pressure_drop)
                row["fanning_cf_pressure_drop_prgh"] = float(fanning_cf_pressure_drop)
                row["momentum_resistance_direct_prgh_pa_s_kg_m"] = float(momentum_resistance_direct)
            output_rows.extend(span_time_rows)
    return output_rows


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.analysis_manifest)
    source_id = str(manifest.get("source_id", args.source_id))
    profile = get_case_analysis_profile(source_id)
    output_dir = ensure_dir(Path(args.output_dir))
    frozen_runtime = manifest.get("frozen_runtime_root")
    if frozen_runtime:
        runtime_root = Path(str(frozen_runtime)).resolve()
    else:
        _, runtime_root, _ = resolve_case_paths(source_id)
    manifest_times = [str(value) for value in manifest.get("requested_times", [])]
    if manifest_times:
        selected_times = manifest_times
    elif args.time_selector:
        selected_times = patch_extractor.select_times(runtime_root, args.last_n_times, args.time_selector)
    else:
        selected_times = select_stable_processor_times(
            runtime_root,
            args.last_n_times,
            required_fields=profile.analysis_required_fields,
        )
    if not selected_times:
        raise RuntimeError(
            f"No stable retained processor times with wall and pressure fields found under {runtime_root / 'processors64'}"
        )
    required_fields = list(dict.fromkeys([*profile.wall_fields, *profile.pressure_fields, *profile.thermal_fields]))
    extract_case_key = build_extract_case_key(
        source_id,
        profile.profile_name,
        selected_times,
        required_fields,
    )
    case_dir = patch_extractor.ensure_extract_case(source_id, runtime_root, extract_key=extract_case_key)
    ensure_reconstructed_fields(case_dir, selected_times, args.skip_extraction, required_fields)
    thermal_sanitization_summary = sanitize_reconstructed_thermal_fields(case_dir, selected_times)

    target_ds_m = float(manifest.get("target_ds_m", args.target_ds_m))
    station_centers = load_station_centers(source_id)
    raw_face_geometry_rows, geometry_meta = load_raw_face_geometry(case_dir, profile.major_spans)
    boundary_anchor_patch_names = sorted(
        {
            str(definition[patch_key])
            for definition in profile.major_spans.values()
            if str(definition.get("streamwise_coordinate_method", "")) == "patch_centroid_polyline"
            for patch_key in ("start_patch", "end_patch")
            if definition.get(patch_key)
        }
    )
    boundary_patch_centroids = load_boundary_patch_centroids(case_dir, boundary_anchor_patch_names)
    patch_centroid_polylines = build_patch_centroid_polylines(
        raw_face_geometry_rows,
        profile.major_spans,
        boundary_patch_centroids=boundary_patch_centroids,
    )
    station_rows = build_station_rows(
        source_id,
        target_ds_m,
        profile.major_spans,
        patch_centroid_polylines=patch_centroid_polylines,
    )
    station_bin_rows = build_station_bin_rows(station_rows)
    geometry_rows = build_face_geometry(
        raw_face_geometry_rows,
        station_centers,
        profile.major_spans,
        patch_centroid_polylines=patch_centroid_polylines,
    )
    usable_times = available_reconstructed_times(case_dir, selected_times, required_fields)
    if not usable_times:
        raise RuntimeError(f"No reconstructed retained wall-field times were available under {case_dir}")
    span_mdot_lookup, span_monitor_area_lookup, mdot_source_lookup = build_span_mdot_inputs(
        runtime_root,
        profile.major_spans,
    )
    sample_rows = build_face_samples(source_id, case_dir, geometry_rows, usable_times)
    cross_section_temperature_rows = build_cross_section_temperature_rows(
        case_dir,
        station_bin_rows,
        profile.major_spans,
        span_monitor_area_lookup,
        usable_times,
        args.skip_extraction,
        profile.tp_density_intercept,
        profile.tp_density_slope,
    )
    cross_section_temperature_lookup = build_cross_section_temperature_lookup(cross_section_temperature_rows)
    tp_rows, span_rho_lookup, global_rho_map = build_span_rho_lookup(
        runtime_root,
        profile.major_spans,
        profile.tp_density_intercept,
        profile.tp_density_slope,
    )
    span_temperature_endpoints_lookup = build_span_temperature_endpoints_lookup(tp_rows, profile.major_spans)
    timeseries_rows = aggregate_major_loss_rows(
        source_id,
        sample_rows,
        station_bin_rows,
        span_mdot_lookup,
        span_monitor_area_lookup,
        span_rho_lookup,
        span_temperature_endpoints_lookup,
        cross_section_temperature_lookup,
    )

    station_bin_lookup = {
        (str(row["span_name"]), int(row["bin_index"])): row
        for row in station_bin_rows
    }

    station_path = output_dir / "leg_centerline_station_definitions.csv"
    face_geometry_path = output_dir / "leg_wall_face_geometry.csv"
    face_sample_path = output_dir / "leg_wall_face_samples.csv"
    cross_section_path = output_dir / "bulk_cross_section_temperature_samples.csv"
    timeseries_path = output_dir / "leg_major_loss_timeseries.csv"
    thermal_sanitization_path = output_dir / "thermal_sanitization_summary.json"
    summary_path = output_dir / "leg_major_loss_extraction_summary.json"

    csv_dump(
        station_path,
        [
            "span_name",
            "span_kind",
            "bin_index",
            "target_ds_m",
            "wall_patch_count",
            "s_start_m",
            "s_end_m",
            "s_mid_m",
            "bin_width_m",
            "x_m",
            "y_m",
            "z_m",
            "tangent_x",
            "tangent_y",
            "tangent_z",
            "segment_start_label",
            "segment_end_label",
        ],
        [
            {
                "span_name": row["span_name"],
                "span_kind": row["span_kind"],
                "bin_index": row["sample_index"],
                "target_ds_m": row["target_ds_m"],
                "wall_patch_count": row["wall_patch_count"],
                "s_start_m": station_bin_lookup[(str(row["span_name"]), int(row["sample_index"]))]["s_start_m"],
                "s_end_m": station_bin_lookup[(str(row["span_name"]), int(row["sample_index"]))]["s_end_m"],
                "s_mid_m": row["s_center_m"],
                "bin_width_m": station_bin_lookup[(str(row["span_name"]), int(row["sample_index"]))]["bin_width_m"],
                "x_m": row["x_m"],
                "y_m": row["y_m"],
                "z_m": row["z_m"],
                "tangent_x": row["tangent_x"],
                "tangent_y": row["tangent_y"],
                "tangent_z": row["tangent_z"],
                "segment_start_label": row["segment_start_label"],
                "segment_end_label": row["segment_end_label"],
            }
            for row in station_rows
        ],
    )
    csv_dump(
        face_geometry_path,
        [
            "source_id",
            "span_name",
            "span_kind",
            "patch_name",
            "face_index",
            "s_span_m",
            "distance_to_centerline_m",
            "area_m2",
            "center_x_m",
            "center_y_m",
            "center_z_m",
            "tangent_x",
            "tangent_y",
            "tangent_z",
            "segment_start_label",
            "segment_end_label",
        ],
        [
            {
                "source_id": source_id,
                "span_name": row["span_name"],
                "span_kind": row["span_kind"],
                "patch_name": row["patch_name"],
                "face_index": row["face_index"],
                "s_span_m": row["s_span_m"],
                "distance_to_centerline_m": row["distance_to_centerline_m"],
                "area_m2": row["area_m2"],
                "center_x_m": row["center_x_m"],
                "center_y_m": row["center_y_m"],
                "center_z_m": row["center_z_m"],
                "tangent_x": row["tangent_x"],
                "tangent_y": row["tangent_y"],
                "tangent_z": row["tangent_z"],
                "segment_start_label": row["segment_start_label"],
                "segment_end_label": row["segment_end_label"],
            }
            for row in geometry_rows
        ],
    )
    csv_dump(
        face_sample_path,
        [
            "source_id",
            "time_s",
            "span_name",
            "span_kind",
            "patch_name",
            "face_index",
            "s_span_m",
            "distance_to_centerline_m",
            "area_m2",
            "center_x_m",
            "center_y_m",
            "center_z_m",
            "tauw_x_pa",
            "tauw_y_pa",
            "tauw_z_pa",
            "tauw_streamwise_signed_pa",
            "tauw_streamwise_abs_pa",
            "yplus",
            "p_wall_pa",
            "p_rgh_wall_pa",
            "t_wall_k",
            "wall_heatflux_w_m2",
        ],
        sample_rows,
    )
    csv_dump(
        cross_section_path,
        [
            "time_s",
            "span_name",
            "bin_index",
            "s_mid_m",
            "bulk_temp_area_avg_k",
            "bulk_temp_flow_weighted_k",
            "bulk_temp_union_area_avg_k",
            "cross_section_faces",
            "cross_section_area_m2",
            "cross_section_total_faces",
            "cross_section_total_area_m2",
            "cross_section_region_count",
            "cross_section_reference_area_m2",
            "cross_section_region_selection_status",
            "cross_section_chosen_region_signed_mass_flux_kg_s",
            "cross_section_chosen_region_aligned_signed_mass_flux_kg_s",
            "cross_section_chosen_region_positive_mass_flux_kg_s",
            "cross_section_chosen_region_area_ratio_to_reference",
            "selection",
        ],
        cross_section_temperature_rows,
    )
    csv_dump(
        timeseries_path,
        [
            "source_id",
            "time_s",
            "span_name",
            "span_kind",
            "bin_index",
            "s_start_m",
            "s_end_m",
            "s_mid_m",
            "wall_face_count",
            "wall_area_m2",
            "local_wetted_perimeter_m",
            "hydraulic_diameter_geom_m",
            "flow_area_geom_m2",
            "rho_bulk_kg_m3",
            "mdot_mean_abs_kg_s",
            "bulk_velocity_m_s",
            "tauw_streamwise_mean_signed_pa",
            "tauw_streamwise_mean_abs_pa",
            "tauw_streamwise_std_abs_pa",
            "tauw_streamwise_max_rel_dev",
            "darcy_f",
            "p_wall_area_avg_pa",
            "p_rgh_wall_area_avg_pa",
            "t_wall_area_avg_k",
            "bulk_temp_fluid_area_avg_k",
            "bulk_temp_area_weighted_k",
            "bulk_temp_union_area_avg_k",
            "bulk_cross_section_face_count",
            "bulk_cross_section_area_m2",
            "bulk_cross_section_total_face_count",
            "bulk_cross_section_total_area_m2",
            "bulk_cross_section_region_count",
            "bulk_cross_section_reference_area_m2",
            "bulk_cross_section_area_ratio_to_geom",
            "bulk_cross_section_chosen_region_area_ratio_to_reference",
            "bulk_cross_section_chosen_region_signed_mass_flux_kg_s",
            "bulk_cross_section_chosen_region_aligned_signed_mass_flux_kg_s",
            "bulk_cross_section_chosen_region_positive_mass_flux_kg_s",
            "bulk_cross_section_region_selection_status",
            "bulk_temp_tp_endpoint_proxy_k",
            "bulk_minus_wall_tp_endpoint_proxy_k",
            "effective_htc_tp_endpoint_proxy_w_m2_k",
            "effective_ua_per_m_tp_endpoint_proxy_w_m_k",
            "effective_thermal_resistance_tp_endpoint_proxy_k_m_w",
            "bulk_minus_wall_temp_k",
            "wall_heatflux_area_avg_w_m2",
            "wall_heat_per_length_w_m",
            "effective_htc_w_m2_k",
            "effective_ua_per_m_w_m_k",
            "effective_thermal_resistance_k_m_w",
            "fanning_cf_shear",
            "fanning_cf_pressure_drop_prgh",
            "dp_major_gradient_pa_per_m",
            "dp_major_gradient_direct_prgh_pa_per_m",
            "dp_major_gradient_direct_p_pa_per_m",
            "flow_alignment_sign",
            "darcy_f_pressure_drop_prgh",
            "momentum_resistance_estimated_pa_s_kg_m",
            "momentum_resistance_direct_prgh_pa_s_kg_m",
            "thermal_support_status",
            "thermal_support_warning_flag",
            "yplus_area_avg",
            "yplus_max",
            "warning_flag",
        ],
        timeseries_rows,
    )
    json_dump(thermal_sanitization_path, thermal_sanitization_summary)

    summary = {
        "generated_at": iso_timestamp(),
        "raw_schema_version": RAW_EXTRACTION_SCHEMA_VERSION,
        "profile_name": profile.profile_name,
        "source_id": source_id,
        "runtime_root": str(runtime_root),
        "extract_case": str(case_dir),
        "output_dir": str(output_dir),
        "requested_times": [float(time_name) for time_name in selected_times],
        "available_times": [float(time_name) for time_name in usable_times],
        "target_ds_m": target_ds_m,
        "major_span_names": list(profile.major_spans.keys()),
        "station_definition_csv": str(station_path),
        "wall_face_geometry_csv": str(face_geometry_path),
        "wall_face_samples_csv": str(face_sample_path),
        "bulk_cross_section_temperature_csv": str(cross_section_path),
        "major_loss_timeseries_csv": str(timeseries_path),
        "station_row_count": len(station_rows),
        "wall_face_geometry_row_count": len(geometry_rows),
        "wall_face_sample_count": len(sample_rows),
        "cross_section_temperature_row_count": len(cross_section_temperature_rows),
        "cross_section_temperature_available_times": sorted(
            {float(row["time_s"]) for row in cross_section_temperature_rows}
        ),
        "major_loss_row_count": len(timeseries_rows),
        "geometry": geometry_meta,
        "mdot_source_by_span": mdot_source_lookup,
        "mdot_monitor_area_m2_by_span": {span_name: float(value) for span_name, value in span_monitor_area_lookup.items()},
        "cross_section_temperature_method": (
            "OpenFOAM sampledSurface cutPlane with interpolated T and U on repaired major-span "
            "bin centers; connected regions are parsed and one region is selected per bin by "
            "aligned mass-flux support and reference-area agreement; matched bulk T is then "
            "computed from aligned positive mass-flux weighting."
        ),
        "thermal_sanitization_summary_json": str(thermal_sanitization_path),
        "thermal_nan_token_replacements_by_time": {
            time_name: int(count)
            for time_name, count in sorted(thermal_sanitization_summary.get("replacements_by_time", {}).items())
        },
        "streamwise_coordinate_method_by_span": {
            span_name: str(profile.major_spans[span_name].get("streamwise_coordinate_method", "tp_tw_polyline"))
            for span_name in profile.major_spans
        },
        "rho_time_count_global": len(global_rho_map),
        "warning_row_count": sum(1 for row in timeseries_rows if row["warning_flag"] == "yes"),
    }
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
