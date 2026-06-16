#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
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
)

PATCH_EXTRACTOR_PATH = ROOT / "tools" / "extract" / "sample_streamwise_friction_patch_averages.py"
TP_TW_LOCATIONS = WORKSPACE_ROOT / "jadyn_runs" / "salt2" / "2026-06-01_continuation_candidate" / "tp_tw_probe_locations.csv"
DEFAULT_SOURCE_ID = "val_salt_test_2_coarse_mesh_laminar"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-09_ethan_dense_streamwise_friction_package" / "raw_extraction"

MAIN_LOOP_SEQUENCE = [
    "TP1",
    "TW1",
    "TW2",
    "TW3",
    "TP2",
    "TW4",
    "TW5",
    "TW6",
    "TP3",
    "TW7",
    "TP4",
    "TP5",
    "TW8",
    "TP6",
    "TW11",
    "TW10",
    "TW9",
    "TP1",
]
TP_LABELS = [f"TP{i}" for i in range(1, 7)]
LEG_PATCH_MAP = {
    "lower_leg": [
        "pipeleg_lower_01_fitting",
        "pipeleg_lower_02_straight",
        "pipeleg_lower_03_bend",
        "pipeleg_lower_04_straight",
        "pipeleg_lower_05_straight",
        "pipeleg_lower_06_straight",
        "pipeleg_lower_07_bend",
        "pipeleg_lower_08_straight",
        "pipeleg_lower_09_fitting",
    ],
    "right_leg": [
        "pipeleg_right_01_lower",
        "pipeleg_right_02_middle",
        "pipeleg_right_03_upper",
    ],
    "left_leg": [
        "pipeleg_left_07_lower",
        "pipeleg_left_06_connector",
        "pipeleg_left_02_connector",
        "pipeleg_left_01_upper",
    ],
    "upper_leg": [
        "pipeleg_upper_09_straight",
        "pipeleg_upper_08_bend",
        "pipeleg_upper_07_straight",
        "pipeleg_upper_06_reducer",
        "pipeleg_upper_05_cooler",
        "pipeleg_upper_04_reducer",
        "pipeleg_upper_03_straight",
        "pipeleg_upper_02_bend",
        "pipeleg_upper_01_straight",
    ],
}
LEG_TP_BOUNDS = {
    "lower_leg": ("TP1", "TP2"),
    "right_leg": ("TP2", "TP3"),
    "left_leg": ("TP3", "TP6"),
    "upper_leg": ("TP6", "TP1"),
}
BRANCH_PATCHES = [
    "pipeleg_left_03_fitting",
    "pipeleg_left_04_test_section",
    "pipeleg_left_05_fitting",
]
EPS = 1.0e-12


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


patch_extractor = load_module("sample_streamwise_friction_patch_averages", PATCH_EXTRACTOR_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract wall-face-level streamwise friction samples for Salt 2. "
            "The helper reuses the reconstructed temp case, parses boundary-face "
            "geometry on the main loop, and exports dense facewise wall-shear and "
            "yPlus samples for retained latest times."
        )
    )
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--last-n-times", type=int, default=5)
    parser.add_argument("--time-selector", help="Explicit comma-separated OpenFOAM time selector override.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--skip-extraction", action="store_true")
    return parser.parse_args()


def load_station_centers() -> dict[str, tuple[float, float, float]]:
    grouped: dict[str, list[tuple[float, float, float]]] = {}
    with TP_TW_LOCATIONS.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            label = row["label"]
            x_value = float(row["x_m"])
            y_value = float(row["y_m"])
            z_value = float(row["z_m"])
            grouped.setdefault(label, []).append((x_value, y_value, z_value))
            if row["group"] == "TW":
                station = label.split("_", 1)[0]
                grouped.setdefault(station, []).append((x_value, y_value, z_value))
    centers: dict[str, tuple[float, float, float]] = {}
    for label, coords in grouped.items():
        values = np.array(coords, dtype=float)
        centers[label] = (float(np.mean(values[:, 0])), float(np.mean(values[:, 1])), float(np.mean(values[:, 2])))
    return centers


def distance(point_a: tuple[float, float, float], point_b: tuple[float, float, float]) -> float:
    return math.sqrt(
        (point_b[0] - point_a[0]) ** 2
        + (point_b[1] - point_a[1]) ** 2
        + (point_b[2] - point_a[2]) ** 2
    )


def build_station_s_map(station_centers: dict[str, tuple[float, float, float]]) -> tuple[dict[str, float], float]:
    cumulative = 0.0
    s_map: dict[str, float] = {}
    for index, label in enumerate(MAIN_LOOP_SEQUENCE[:-1]):
        next_label = MAIN_LOOP_SEQUENCE[index + 1]
        s_map[label] = cumulative
        cumulative += distance(station_centers[label], station_centers[next_label])
    return s_map, cumulative


def patch_leg_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for leg_name, patch_names in LEG_PATCH_MAP.items():
        for patch_name in patch_names:
            lookup[patch_name] = leg_name
    for patch_name in BRANCH_PATCHES:
        lookup[patch_name] = "branch_left_test_section"
    return lookup


def leg_tangent_map(station_centers: dict[str, tuple[float, float, float]], station_s: dict[str, float]) -> dict[str, dict[str, Any]]:
    payload: dict[str, dict[str, Any]] = {}
    for leg_name, (start_label, end_label) in LEG_TP_BOUNDS.items():
        start = np.array(station_centers[start_label], dtype=float)
        end = np.array(station_centers[end_label], dtype=float)
        vector = end - start
        length = float(np.linalg.norm(vector))
        payload[leg_name] = {
            "start_label": start_label,
            "end_label": end_label,
            "start_point": start,
            "end_point": end,
            "unit": vector / max(length, EPS),
            "length_m": length,
            "s_start_m": float(station_s[start_label]),
            "s_end_m": float(station_s[end_label]),
        }
    return payload


def parse_boundary(path: Path) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    index = 0
    while index < len(lines) and not lines[index].strip().isdigit():
        index += 1
    if index >= len(lines):
        raise RuntimeError(f"Failed to locate boundary count in {path}")
    index += 1
    while index < len(lines) and lines[index].strip() != "(":
        index += 1
    index += 1
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue
        if stripped == ")":
            break
        patch_name = stripped
        index += 1
        while index < len(lines) and lines[index].strip() != "{":
            index += 1
        index += 1
        data: dict[str, Any] = {}
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped == "}":
                index += 1
                break
            if stripped:
                if stripped.endswith(";"):
                    stripped = stripped[:-1]
                parts = stripped.split(None, 1)
                if len(parts) == 2:
                    data[parts[0]] = parts[1]
            index += 1
        if "startFace" in data and "nFaces" in data:
            entries[patch_name] = {
                **data,
                "startFace": int(str(data["startFace"])),
                "nFaces": int(str(data["nFaces"])),
            }
    return entries


def parse_face_entry(line: str) -> list[int]:
    stripped = line.strip()
    if "(" not in stripped or not stripped.endswith(")"):
        raise RuntimeError(f"Unexpected face entry: {line!r}")
    _, payload = stripped.split("(", 1)
    return [int(item) for item in payload[:-1].split()]


def parse_point_entry(line: str) -> tuple[float, float, float]:
    stripped = line.strip()
    if not stripped.startswith("(") or not stripped.endswith(")"):
        raise RuntimeError(f"Unexpected point entry: {line!r}")
    values = [float(item) for item in stripped[1:-1].split()]
    return float(values[0]), float(values[1]), float(values[2])


def load_selected_faces(faces_path: Path, target_ranges: list[tuple[int, int, str]]) -> dict[int, dict[str, Any]]:
    selected: dict[int, dict[str, Any]] = {}
    sorted_ranges = sorted(target_ranges, key=lambda item: item[0])
    range_index = 0
    face_index = -1
    with faces_path.open("r", encoding="utf-8") as handle:
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
            face_index += 1
            while range_index < len(sorted_ranges) and face_index >= sorted_ranges[range_index][1]:
                range_index += 1
            if range_index >= len(sorted_ranges):
                break
            start_face, end_face, patch_name = sorted_ranges[range_index]
            if start_face <= face_index < end_face:
                selected[face_index] = {"patch_name": patch_name, "point_ids": parse_face_entry(stripped)}
    return selected


def load_selected_points(points_path: Path, point_ids: set[int]) -> dict[int, np.ndarray]:
    selected: dict[int, np.ndarray] = {}
    point_index = -1
    with points_path.open("r", encoding="utf-8") as handle:
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
            point_index += 1
            if point_index in point_ids:
                selected[point_index] = np.array(parse_point_entry(stripped), dtype=float)
    return selected


def polygon_area(points: list[np.ndarray]) -> float:
    if len(points) < 3:
        return 0.0
    origin = points[0]
    area_vector = np.zeros(3, dtype=float)
    for index in range(1, len(points) - 1):
        area_vector += np.cross(points[index] - origin, points[index + 1] - origin)
    return 0.5 * float(np.linalg.norm(area_vector))


def build_face_geometry(
    case_dir: Path,
    selected_patches: list[str],
    station_centers: dict[str, tuple[float, float, float]],
    station_s: dict[str, float],
    main_loop_length_m: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    boundary_entries = parse_boundary(case_dir / "constant" / "polyMesh" / "boundary")
    missing = [patch_name for patch_name in selected_patches if patch_name not in boundary_entries]
    if missing:
        raise RuntimeError(f"Selected patches missing from boundary: {missing}")
    target_ranges = [
        (
            int(boundary_entries[patch_name]["startFace"]),
            int(boundary_entries[patch_name]["startFace"]) + int(boundary_entries[patch_name]["nFaces"]),
            patch_name,
        )
        for patch_name in selected_patches
    ]
    face_map = load_selected_faces(case_dir / "constant" / "polyMesh" / "faces", target_ranges)
    point_ids = {point_id for entry in face_map.values() for point_id in entry["point_ids"]}
    point_map = load_selected_points(case_dir / "constant" / "polyMesh" / "points", point_ids)

    patch_to_leg = patch_leg_lookup()
    leg_map = leg_tangent_map(station_centers, station_s)
    geometry_rows: list[dict[str, Any]] = []

    for face_index, entry in sorted(face_map.items()):
        patch_name = str(entry["patch_name"])
        leg_name = patch_to_leg[patch_name]
        if leg_name not in leg_map:
            continue
        point_coords = [point_map[point_id] for point_id in entry["point_ids"]]
        center = np.mean(np.vstack(point_coords), axis=0)
        area_m2 = polygon_area(point_coords)
        leg = leg_map[leg_name]
        local_s = float(np.dot(center - leg["start_point"], leg["unit"]))
        local_s = max(0.0, min(local_s, float(leg["length_m"])))
        global_s = float(leg["s_start_m"] + local_s)
        geometry_rows.append(
            {
                "face_index": face_index,
                "patch_name": patch_name,
                "leg_name": leg_name,
                "s_leg_local_m": local_s,
                "s_m": global_s,
                "area_m2": area_m2,
                "center_x_m": float(center[0]),
                "center_y_m": float(center[1]),
                "center_z_m": float(center[2]),
            }
        )

    geometry_meta = {
        "selected_patch_count": len(selected_patches),
        "selected_face_count": len(geometry_rows),
        "selected_point_count": len(point_map),
        "main_loop_length_m": float(main_loop_length_m),
    }
    return geometry_rows, geometry_meta


def parse_field_value(value_line: str, field_type: str) -> tuple[float, ...]:
    stripped = value_line.strip()
    if field_type == "vector":
        payload = stripped[1:-1].split()
        return float(payload[0]), float(payload[1]), float(payload[2])
    return (float(stripped),)


def parse_boundary_field(
    path: Path,
    selected_patches: set[str],
    field_type: str,
    face_count_by_patch: dict[str, int] | None = None,
) -> dict[str, list[tuple[float, ...]]]:
    field_name = path.name

    def allowed_entry_names() -> tuple[str, ...]:
        # OpenFOAM 13 wall-temperature files in these Salt cases often store the
        # physically imposed patch temperature under `Tp` instead of the more
        # generic `value`. The postprocessing contract needs the actual wall
        # thermal state, so both entry names are treated as equivalent sources.
        if field_name == "T":
            return ("value", "Tp")
        return ("value",)

    def parse_nonuniform_entry(start_index: int) -> tuple[list[tuple[float, ...]], int]:
        count_line = lines[start_index + 1].strip()
        value_count = int(count_line)
        index_local = start_index + 2
        while index_local < len(lines) and lines[index_local].strip() != "(":
            index_local += 1
        index_local += 1
        parsed_values: list[tuple[float, ...]] = []
        while index_local < len(lines):
            value_line = lines[index_local].strip()
            if value_line in {")", ");"}:
                break
            parsed_values.append(parse_field_value(value_line, field_type))
            index_local += 1
        if len(parsed_values) != value_count:
            raise RuntimeError(f"Patch entry in {path} expected {value_count} values, found {len(parsed_values)}")
        while index_local < len(lines) and lines[index_local].strip() not in {")", ");"}:
            index_local += 1
        return parsed_values, index_local

    def inferred_patch_values(patch_name: str, patch_type: str | None) -> list[tuple[float, ...]] | None:
        if face_count_by_patch is None:
            return None
        face_count = face_count_by_patch.get(patch_name, 0)
        if face_count <= 0:
            return None
        if field_name == "U" and patch_type == "noSlip":
            # OpenFOAM noSlip walls do not necessarily write an explicit boundary
            # value block for U because the wall velocity is implied. For this
            # wall-only transport reduction that implied state is exactly the
            # required value, so we inject the zero vector explicitly.
            return [(0.0, 0.0, 0.0) for _ in range(face_count)]
        if field_name == "p_rgh" and patch_type == "fixedFluxPressure":
            # fixedFluxPressure usually constrains the gradient rather than
            # persisting a meaningful facewise boundary value. Leaving this as
            # NaN preserves the distinction between "not sampled" and a real
            # pressure datum, which keeps downstream direct-gradient QC honest.
            return [(float("nan"),) for _ in range(face_count)]
        return None

    with path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    results: dict[str, list[tuple[float, ...]]] = {}
    index = 0
    while index < len(lines) and lines[index].strip() != "boundaryField":
        index += 1
    while index < len(lines) and lines[index].strip() != "{":
        index += 1
    index += 1
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue
        if stripped == "}":
            break
        patch_name = stripped
        index += 1
        while index < len(lines) and lines[index].strip() != "{":
            index += 1
        index += 1
        selected = patch_name in selected_patches
        values: list[tuple[float, ...]] | None = None
        patch_type: str | None = None
        brace_depth = 1
        while index < len(lines) and brace_depth > 0:
            stripped = lines[index].strip()
            if stripped == "{":
                brace_depth += 1
                index += 1
                continue
            if stripped == "}":
                brace_depth -= 1
                index += 1
                continue
            if brace_depth == 1 and stripped.startswith("type"):
                tokens = stripped.rstrip(";").split()
                if len(tokens) >= 2:
                    patch_type = tokens[-1]
            entry_name = stripped.split(None, 1)[0] if stripped else ""
            if selected and brace_depth == 1 and entry_name in allowed_entry_names() and "nonuniform" in stripped:
                values, index = parse_nonuniform_entry(index)
            elif selected and brace_depth == 1 and entry_name in allowed_entry_names() and "uniform" in stripped:
                if face_count_by_patch is None:
                    raise RuntimeError(
                        f"Selected patch {patch_name} in {path} has uniform {entry_name} values but no face-count map was provided"
                    )
                uniform_value = stripped.split("uniform", 1)[1].strip().rstrip(";")
                parsed_value = parse_field_value(uniform_value, field_type)
                values = [parsed_value for _ in range(face_count_by_patch.get(patch_name, 0))]
            index += 1
        if selected:
            if values is None:
                values = inferred_patch_values(patch_name, patch_type)
            if values is None:
                raise RuntimeError(f"Selected patch {patch_name} missing readable boundary values in {path}")
            results[patch_name] = values
    return results


def ensure_reconstructed_fields(case_dir: Path, selected_times: list[str], skip_extraction: bool) -> None:
    if skip_extraction and patch_extractor.reconstructed_fields_ready(case_dir, selected_times):
        return
    if not patch_extractor.reconstructed_fields_ready(case_dir, selected_times):
        time_selector = ",".join(selected_times)
        patch_extractor.shell_run(
            case_dir,
            "reconstructPar "
            f"-case {case_dir} "
            f"-time '{time_selector}' "
            "-fields '(wallShearStress yPlus)'",
        )


def build_face_samples(
    case_dir: Path,
    geometry_rows: list[dict[str, Any]],
    selected_times: list[str],
    tangent_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    geometry_by_patch: dict[str, list[dict[str, Any]]] = {}
    for row in geometry_rows:
        geometry_by_patch.setdefault(str(row["patch_name"]), []).append(row)
    ordered_geometry_by_patch = {
        patch_name: sorted(rows, key=lambda item: int(item["face_index"]))
        for patch_name, rows in geometry_by_patch.items()
    }
    selected_patches = set(geometry_by_patch)
    sample_rows: list[dict[str, Any]] = []

    for time_name in selected_times:
        time_value = float(time_name)
        wall_values = parse_boundary_field(case_dir / time_name / "wallShearStress", selected_patches, "vector")
        yplus_values = parse_boundary_field(case_dir / time_name / "yPlus", selected_patches, "scalar")
        for patch_name, face_rows in ordered_geometry_by_patch.items():
            tau_vectors = wall_values[patch_name]
            yplus_scalars = yplus_values[patch_name]
            if len(tau_vectors) != len(face_rows) or len(yplus_scalars) != len(face_rows):
                raise RuntimeError(
                    f"Patch {patch_name} field length mismatch at time {time_name}: "
                    f"{len(face_rows)} faces, {len(tau_vectors)} wallShearStress, {len(yplus_scalars)} yPlus"
                )
            leg_name = str(face_rows[0]["leg_name"])
            tangent = tangent_map[leg_name]["unit"]
            for index, face_row in enumerate(face_rows):
                tau_vector = tau_vectors[index]
                tau_streamwise_signed = (
                    float(tau_vector[0]) * float(tangent[0])
                    + float(tau_vector[1]) * float(tangent[1])
                    + float(tau_vector[2]) * float(tangent[2])
                )
                tau_abs = abs(tau_streamwise_signed)
                sample_rows.append(
                    {
                        "time_s": time_value,
                        "face_index": int(face_row["face_index"]),
                        "patch_name": patch_name,
                        "leg_name": leg_name,
                        "s_m": float(face_row["s_m"]),
                        "area_m2": float(face_row["area_m2"]),
                        "center_x_m": float(face_row["center_x_m"]),
                        "center_y_m": float(face_row["center_y_m"]),
                        "center_z_m": float(face_row["center_z_m"]),
                        "tauw_x_pa": float(tau_vector[0]),
                        "tauw_y_pa": float(tau_vector[1]),
                        "tauw_z_pa": float(tau_vector[2]),
                        "tauw_streamwise_signed_pa": tau_streamwise_signed,
                        "tauw_streamwise_abs_pa": tau_abs,
                        "yplus": float(yplus_scalars[index][0]),
                    }
                )
    return sample_rows


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))
    runtime_root = patch_extractor.load_runtime_root(args.source_id)
    case_dir = patch_extractor.ensure_extract_case(args.source_id, runtime_root)
    selected_times = patch_extractor.select_times(runtime_root, args.last_n_times, args.time_selector)
    ensure_reconstructed_fields(case_dir, selected_times, args.skip_extraction)

    station_centers = load_station_centers()
    station_s, main_loop_length_m = build_station_s_map(station_centers)
    tangent_map = leg_tangent_map(station_centers, station_s)
    geometry_rows, geometry_meta = build_face_geometry(
        case_dir,
        [patch_name for patch_names in LEG_PATCH_MAP.values() for patch_name in patch_names],
        station_centers,
        station_s,
        main_loop_length_m,
    )
    sample_rows = build_face_samples(case_dir, geometry_rows, selected_times, tangent_map)

    geometry_path = output_dir / "wall_face_geometry.csv"
    samples_path = output_dir / "wall_face_samples.csv"
    csv_dump(
        geometry_path,
        [
            "face_index",
            "patch_name",
            "leg_name",
            "s_leg_local_m",
            "s_m",
            "area_m2",
            "center_x_m",
            "center_y_m",
            "center_z_m",
        ],
        geometry_rows,
    )
    csv_dump(
        samples_path,
        [
            "time_s",
            "face_index",
            "patch_name",
            "leg_name",
            "s_m",
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
        ],
        sample_rows,
    )
    summary = {
        "generated_at": iso_timestamp(),
        "source_id": args.source_id,
        "runtime_root": str(runtime_root),
        "extract_case": str(case_dir),
        "selected_times": [float(item) for item in selected_times],
        "main_loop_length_m": float(main_loop_length_m),
        "geometry": geometry_meta,
        "geometry_csv": str(geometry_path),
        "samples_csv": str(samples_path),
        "sample_row_count": len(sample_rows),
    }
    with (output_dir / "dense_face_extraction_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
