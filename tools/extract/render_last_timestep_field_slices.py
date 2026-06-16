#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from paraview.simple import (  # type: ignore
    Calculator,
    Clip,
    ColorBy,
    CreateView,
    ExportView,
    GetColorTransferFunction,
    GetScalarBar,
    OpenFOAMReader,
    Render,
    ResetSession,
    SaveScreenshot,
    SetActiveSource,
    Show,
    Slice,
    Text,
    UpdatePipeline,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.case_analysis_profiles import get_case_analysis_profile
from tools.common import load_case_metadata


REGISTRY_PATH = ROOT / "registry" / "case_registry.csv"
DEFAULT_OUTPUT_ROOT = ROOT / "figures"
COMPONENT_CHOICES = ("all", "cooler", "downcomer", "heater", "upcomer")
FACE_LINE_RE = re.compile(r"^(\d+)\(([^)]*)\)$")
POINT_LINE_RE = re.compile(r"^\(([^)]*)\)$")

FIELD_CONFIG = {
    "temperature": {
        "reader_arrays": ("T",),
        "association_array": "T",
        "scalar_title": "Temperature [K]",
        "output_subdir": "",
        "component_view_subdir": "temperature",
        "png_filename": "{source_id}{component_suffix}.png",
        "svg_filename": "{source_id}{component_suffix}_last_timestep_temperature_slice.svg",
        "pdf_filename": "{source_id}{component_suffix}_last_timestep_temperature_slice.pdf",
        "color_range_mode": "temperature_window",
    },
    "velocity": {
        "reader_arrays": ("U",),
        "association_array": "U",
        "calculator_result_array": "Umag",
        "calculator_function": "mag(U)",
        "scalar_title": "Velocity magnitude [m/s]",
        "output_subdir": "",
        "component_view_subdir": "velocity",
        "png_filename": "{source_id}{component_suffix}_last_timestep_velocity_slice.png",
        "svg_filename": "{source_id}{component_suffix}_last_timestep_velocity_slice.svg",
        "pdf_filename": "{source_id}{component_suffix}_last_timestep_velocity_slice.pdf",
        "color_range_mode": "data",
    },
    "velocity_x": {
        "reader_arrays": ("U",),
        "association_array": "U",
        "calculator_result_array": "Ux",
        "calculator_function": "U_X",
        "scalar_title": "Velocity x [m/s]",
        "output_subdir": "velocity_components",
        "component_view_subdir": "x_vel",
        "png_filename": "{source_id}{component_suffix}_last_timestep_velocity_x_slice.png",
        "svg_filename": "{source_id}{component_suffix}_last_timestep_velocity_x_slice.svg",
        "pdf_filename": "{source_id}{component_suffix}_last_timestep_velocity_x_slice.pdf",
        "color_range_mode": "symmetric",
    },
    "velocity_y": {
        "reader_arrays": ("U",),
        "association_array": "U",
        "calculator_result_array": "Uy",
        "calculator_function": "U_Y",
        "scalar_title": "Velocity y [m/s]",
        "output_subdir": "velocity_components",
        "component_view_subdir": "y_vel",
        "png_filename": "{source_id}{component_suffix}_last_timestep_velocity_y_slice.png",
        "svg_filename": "{source_id}{component_suffix}_last_timestep_velocity_y_slice.svg",
        "pdf_filename": "{source_id}{component_suffix}_last_timestep_velocity_y_slice.pdf",
        "color_range_mode": "symmetric",
    },
    "velocity_z": {
        "reader_arrays": ("U",),
        "association_array": "U",
        "calculator_result_array": "Uz",
        "calculator_function": "U_Z",
        "scalar_title": "Velocity z [m/s]",
        "output_subdir": "velocity_components",
        "component_view_subdir": "z_vel",
        "png_filename": "{source_id}{component_suffix}_last_timestep_velocity_z_slice.png",
        "svg_filename": "{source_id}{component_suffix}_last_timestep_velocity_z_slice.svg",
        "pdf_filename": "{source_id}{component_suffix}_last_timestep_velocity_z_slice.pdf",
        "color_range_mode": "symmetric",
    },
    "pressure_static": {
        "reader_arrays": ("p",),
        "association_array": "p",
        "scalar_title": "Static pressure [Pa]",
        "output_subdir": "pressure",
        "png_filename": "{source_id}{component_suffix}_last_timestep_pressure_static_slice.png",
        "svg_filename": "{source_id}{component_suffix}_last_timestep_pressure_static_slice.svg",
        "pdf_filename": "{source_id}{component_suffix}_last_timestep_pressure_static_slice.pdf",
        "color_range_mode": "data",
    },
    "pressure_dynamic": {
        "reader_arrays": ("U",),
        "association_array": "U",
        "calculator_result_array": "p_dynamic",
        "scalar_title": "Dynamic pressure [Pa]",
        "output_subdir": "pressure",
        "png_filename": "{source_id}{component_suffix}_last_timestep_pressure_dynamic_slice.png",
        "svg_filename": "{source_id}{component_suffix}_last_timestep_pressure_dynamic_slice.svg",
        "pdf_filename": "{source_id}{component_suffix}_last_timestep_pressure_dynamic_slice.pdf",
        "color_range_mode": "nonnegative",
    },
    "pressure_total": {
        "reader_arrays": ("U", "p"),
        "association_array": "p",
        "calculator_result_array": "p_total",
        "scalar_title": "Total pressure [Pa]",
        "output_subdir": "pressure",
        "png_filename": "{source_id}{component_suffix}_last_timestep_pressure_total_slice.png",
        "svg_filename": "{source_id}{component_suffix}_last_timestep_pressure_total_slice.svg",
        "pdf_filename": "{source_id}{component_suffix}_last_timestep_pressure_total_slice.pdf",
        "color_range_mode": "data",
    },
}
ARRAY_ASSOCIATION_CHOICES = ("cells", "points", "auto")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render ParaView last-timestep z-reference temperature or velocity slices for registered Ethan cases."
    )
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        default=[],
        help="Specific registered source_id to render. Repeat to select multiple cases.",
    )
    parser.add_argument(
        "--field",
        choices=sorted(FIELD_CONFIG.keys()),
        required=True,
        help="Field to render on the slice.",
    )
    parser.add_argument(
        "--component",
        choices=COMPONENT_CHOICES,
        default="all",
        help="Optional metadata-driven component clip (`upcomer`, `downcomer`, `cooler`, `heater`).",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Directory for rendered figures and status output.",
    )
    parser.add_argument(
        "--status-path",
        default="",
        help="Machine-readable run status JSON path. Defaults to a field-specific file under the output root.",
    )
    parser.add_argument(
        "--array-association",
        choices=ARRAY_ASSOCIATION_CHOICES,
        default="cells",
        help="Preferred data association for slice coloring. `cells` is the default for non-conforming coupling visibility.",
    )
    return parser.parse_args()


def iso_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def json_dump(path: Path, payload: object) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def read_registry_rows() -> list[dict[str, str]]:
    with REGISTRY_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_qoi_summary(source_id: str) -> dict[str, object]:
    qoi_path = ROOT / "work_products" / source_id / "qoi_summary.json"
    with qoi_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def component_slug(component: str) -> str:
    return "" if component == "all" else component


def component_file_suffix(component: str) -> str:
    slug = component_slug(component)
    return f"_{slug}" if slug else ""


def component_view_field_subdir(field_name: str) -> str:
    config = FIELD_CONFIG[field_name]
    return str(config.get("component_view_subdir", field_name)).strip() or field_name


def field_output_root(output_root: Path, field_name: str, component: str) -> Path:
    if component != "all":
        return ensure_dir(output_root / component / component_view_field_subdir(field_name))

    field_root = output_root
    output_subdir = str(FIELD_CONFIG[field_name].get("output_subdir", "")).strip()
    if output_subdir:
        field_root = field_root / output_subdir
    return ensure_dir(field_root)


def default_status_path(output_root: Path, field_name: str, component: str) -> Path:
    stem = f"last_timestep_{field_name}"
    if component != "all":
        stem = f"{stem}_{component}"
    return field_output_root(output_root, field_name, component) / f"{stem}_slice_status.json"


def figure_paths(output_root: Path, source_id: str, field_name: str, component: str) -> dict[str, Path]:
    figure_root = field_output_root(output_root, field_name, component)
    config = FIELD_CONFIG[field_name]
    component_suffix = component_file_suffix(component)
    return {
        "png": ensure_dir(figure_root / "png")
        / config["png_filename"].format(source_id=source_id, component_suffix=component_suffix),
        "svg": ensure_dir(figure_root / "svg")
        / config["svg_filename"].format(source_id=source_id, component_suffix=component_suffix),
        "pdf": ensure_dir(figure_root / "pdf")
        / config["pdf_filename"].format(source_id=source_id, component_suffix=component_suffix),
    }


def time_token(last_time: float) -> str:
    return f"{last_time:g}"


def case_entry_has_fields(case_entry: Path, required_arrays: Iterable[str], last_time: float) -> bool:
    root = case_entry.parent
    token = time_token(last_time)
    candidate_dirs: list[Path] = []
    direct_time_dir = root / token
    if direct_time_dir.exists():
        candidate_dirs.append(direct_time_dir)
    processors64_time_dir = root / "processors64" / token
    if processors64_time_dir.exists():
        candidate_dirs.append(processors64_time_dir)
    for processor_dir in sorted(root.glob("processor*")):
        time_dir = processor_dir / token
        if time_dir.exists():
            candidate_dirs.append(time_dir)
            break
    if not candidate_dirs:
        return False
    return all(any((candidate_dir / array_name).exists() for candidate_dir in candidate_dirs) for array_name in required_arrays)


def locate_case_entry(source_root: Path, source_id: str, required_arrays: Iterable[str], last_time: float) -> tuple[Path, str]:
    reconstructed_entry = ROOT / "staging" / "render_inputs" / source_id / "reconstructed_case" / f"{source_id}.foam"
    if reconstructed_entry.exists() and case_entry_has_fields(reconstructed_entry, required_arrays, last_time):
        return reconstructed_entry, "Reconstructed Case"

    preferred = source_root / "case.foam"
    if preferred.exists():
        case_type = "Decomposed Case" if (source_root / "processors64").exists() else "Reconstructed Case"
        return preferred, case_type

    foam_files = sorted(source_root.glob("*.foam"))
    if foam_files:
        case_type = "Decomposed Case" if (source_root / "processors64").exists() else "Reconstructed Case"
        return foam_files[0], case_type

    if all((source_root / name).exists() for name in ("0", "constant", "system")):
        mirror_root = ensure_dir(ROOT / "cache" / "paraview_cases" / source_id)
        for item in source_root.iterdir():
            target = mirror_root / item.name
            if target.is_symlink():
                if target.resolve() == item.resolve():
                    continue
                target.unlink()
            elif target.exists():
                continue
            target.symlink_to(item, target_is_directory=item.is_dir())

        mirror_entry = mirror_root / f"{source_id}.foam"
        if not mirror_entry.exists():
            mirror_entry.write_text("\n", encoding="utf-8")
        case_type = "Decomposed Case" if (mirror_root / "processors64").exists() else "Reconstructed Case"
        return mirror_entry, case_type

    raise FileNotFoundError(f"No .foam entrypoint found for {source_id} under {source_root}")


def numeric_dir_values(root: Path) -> list[float]:
    values: list[float] = []
    if not root.exists():
        return values
    for item in root.iterdir():
        if not item.is_dir():
            continue
        try:
            values.append(float(item.name))
        except ValueError:
            continue
    return values


def discover_last_time(source_root: Path) -> float:
    candidates = numeric_dir_values(source_root)
    candidates.extend(numeric_dir_values(source_root / "processors64"))
    for processor_dir in sorted(source_root.glob("processor*")):
        candidates.extend(numeric_dir_values(processor_dir))
    if not candidates:
        raise RuntimeError(f"No numeric timestep directories found under {source_root}.")
    return max(candidates)


def discover_case_times(source_root: Path) -> list[float]:
    candidates = numeric_dir_values(source_root)
    candidates.extend(numeric_dir_values(source_root / "processors64"))
    for processor_dir in sorted(source_root.glob("processor*")):
        candidates.extend(numeric_dir_values(processor_dir))
    return sorted(set(candidates))


def get_mesh_bounds(proxy) -> tuple[float, float, float, float, float, float]:
    bounds = proxy.GetDataInformation().GetBounds()
    return tuple(float(value) for value in bounds)


def pick_array_association(proxy, array_name: str) -> str:
    cell_info = proxy.GetCellDataInformation()
    if cell_info.GetArray(array_name) is not None:
        return "CELLS"
    point_info = proxy.GetPointDataInformation()
    if point_info.GetArray(array_name) is not None:
        return "POINTS"
    raise RuntimeError(f"Field {array_name} was not present on slice output.")


def configure_reader_arrays(reader, array_names: Iterable[str], requested_association: str) -> None:
    selected_arrays = list(dict.fromkeys(str(array_name) for array_name in array_names))
    if hasattr(reader, "CellArrays") and requested_association in {"cells", "auto"}:
        reader.CellArrays = selected_arrays
    elif hasattr(reader, "CellArrays"):
        reader.CellArrays = []

    if hasattr(reader, "PointArrays") and requested_association in {"points", "auto"}:
        reader.PointArrays = selected_arrays
    elif hasattr(reader, "PointArrays"):
        reader.PointArrays = []


def resolve_array_association(proxy, array_name: str, requested_association: str) -> str:
    available = {
        "CELLS": proxy.GetCellDataInformation().GetArray(array_name) is not None,
        "POINTS": proxy.GetPointDataInformation().GetArray(array_name) is not None,
    }
    if requested_association == "cells":
        if available["CELLS"]:
            return "CELLS"
        raise RuntimeError(
            f"Requested cell-associated `{array_name}` data, but slice output did not contain a cell array."
        )
    if requested_association == "points":
        if available["POINTS"]:
            return "POINTS"
        raise RuntimeError(
            f"Requested point-associated `{array_name}` data, but slice output did not contain a point array."
        )
    return pick_array_association(proxy, array_name)


def calculator_attribute_type(proxy, array_name: str, requested_association: str) -> str:
    if requested_association == "cells":
        return "Cell Data"
    if requested_association == "points":
        return "Point Data"
    association = pick_array_association(proxy, array_name)
    return "Cell Data" if association == "CELLS" else "Point Data"


def get_array_range(proxy, array_name: str) -> tuple[float, float]:
    association = pick_array_association(proxy, array_name)
    if association == "CELLS":
        array_info = proxy.GetCellDataInformation().GetArray(array_name)
    else:
        array_info = proxy.GetPointDataInformation().GetArray(array_name)
    if array_info is None:
        raise RuntimeError(f"Field {array_name} was not present on slice output.")
    lower, upper = array_info.GetRange(0)
    return float(lower), float(upper)


def clamp_bounds(
    bounds: tuple[float, float, float, float, float, float],
    clamp_to: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    clamped: list[float] = []
    for axis in range(3):
        lower = max(bounds[2 * axis], clamp_to[2 * axis])
        upper = min(bounds[2 * axis + 1], clamp_to[2 * axis + 1])
        if upper <= lower:
            center = 0.5 * (clamp_to[2 * axis] + clamp_to[2 * axis + 1])
            half_width = max(0.001, 0.01 * max(clamp_to[2 * axis + 1] - clamp_to[2 * axis], 1.0))
            lower = center - half_width
            upper = center + half_width
        clamped.extend((lower, upper))
    return tuple(clamped)


def expand_bounds(
    bounds: tuple[float, float, float, float, float, float],
    *,
    margin_ratio: float = 0.05,
    minimum_margin_m: float = 0.002,
) -> tuple[float, float, float, float, float, float]:
    expanded: list[float] = []
    for axis in range(3):
        lower = bounds[2 * axis]
        upper = bounds[2 * axis + 1]
        span = max(upper - lower, 0.0)
        margin = max(span * margin_ratio, minimum_margin_m)
        expanded.extend((lower - margin, upper + margin))
    return tuple(expanded)


def bounds_within(
    candidate: tuple[float, float, float, float, float, float],
    expected: tuple[float, float, float, float, float, float],
    *,
    tolerance: float = 1.0e-6,
) -> bool:
    for axis in range(3):
        if candidate[2 * axis] < expected[2 * axis] - tolerance:
            return False
        if candidate[2 * axis + 1] > expected[2 * axis + 1] + tolerance:
            return False
    return True


def iter_openfoam_list_lines(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8") as handle:
        in_list = False
        for raw_line in handle:
            stripped = raw_line.strip()
            if not in_list:
                if stripped == "(":
                    in_list = True
                continue
            if stripped == ")":
                break
            if stripped:
                yield stripped


@lru_cache(maxsize=32)
def load_boundary_patch_ranges(mesh_root_text: str) -> dict[str, tuple[int, int]]:
    mesh_root = Path(mesh_root_text)
    boundary_path = mesh_root / "boundary"
    patch_ranges: dict[str, tuple[int, int]] = {}
    current_patch = ""
    n_faces: int | None = None
    start_face: int | None = None
    for stripped in iter_openfoam_list_lines(boundary_path):
        if stripped == "{":
            continue
        if stripped == "}":
            if current_patch and n_faces is not None and start_face is not None:
                patch_ranges[current_patch] = (start_face, start_face + n_faces)
            current_patch = ""
            n_faces = None
            start_face = None
            continue
        if not current_patch:
            if stripped.isdigit():
                continue
            current_patch = stripped
            continue
        tokenized = stripped.rstrip(";").split()
        if not tokenized:
            continue
        if tokenized[0] == "nFaces":
            n_faces = int(tokenized[-1])
        elif tokenized[0] == "startFace":
            start_face = int(tokenized[-1])
    return patch_ranges


def parse_face_point_ids(stripped_line: str) -> tuple[int, ...]:
    match = FACE_LINE_RE.match(stripped_line)
    if match is None:
        raise RuntimeError(f"Could not parse face definition line: {stripped_line[:120]}")
    point_tokens = match.group(2).split()
    return tuple(int(token) for token in point_tokens)


def parse_point_coordinates(stripped_line: str) -> tuple[float, float, float]:
    match = POINT_LINE_RE.match(stripped_line)
    if match is None:
        raise RuntimeError(f"Could not parse point definition line: {stripped_line[:120]}")
    values = match.group(1).split()
    if len(values) != 3:
        raise RuntimeError(f"Expected 3 point coordinates, got {len(values)} in line: {stripped_line[:120]}")
    return float(values[0]), float(values[1]), float(values[2])


def collect_patch_point_ids(mesh_root: Path, face_ranges: list[tuple[int, int]]) -> set[int]:
    faces_path = mesh_root / "faces"
    sorted_ranges = sorted(face_ranges)
    if not sorted_ranges:
        return set()
    point_ids: set[int] = set()
    active_range_index = 0
    for face_index, stripped_line in enumerate(iter_openfoam_list_lines(faces_path)):
        while active_range_index < len(sorted_ranges) and face_index >= sorted_ranges[active_range_index][1]:
            active_range_index += 1
        if active_range_index >= len(sorted_ranges):
            break
        start_face, stop_face = sorted_ranges[active_range_index]
        if face_index < start_face:
            continue
        point_ids.update(parse_face_point_ids(stripped_line))
    return point_ids


def point_bounds_from_ids(mesh_root: Path, point_ids: set[int]) -> tuple[float, float, float, float, float, float]:
    if not point_ids:
        raise RuntimeError(f"No mesh point ids were collected from {mesh_root}.")
    points_path = mesh_root / "points"
    sorted_point_ids = sorted(point_ids)
    target_index = 0
    mins = [math.inf, math.inf, math.inf]
    maxs = [-math.inf, -math.inf, -math.inf]
    for point_index, stripped_line in enumerate(iter_openfoam_list_lines(points_path)):
        if target_index >= len(sorted_point_ids):
            break
        target_point_id = sorted_point_ids[target_index]
        if point_index < target_point_id:
            continue
        if point_index != target_point_id:
            continue
        x_coord, y_coord, z_coord = parse_point_coordinates(stripped_line)
        mins[0] = min(mins[0], x_coord)
        mins[1] = min(mins[1], y_coord)
        mins[2] = min(mins[2], z_coord)
        maxs[0] = max(maxs[0], x_coord)
        maxs[1] = max(maxs[1], y_coord)
        maxs[2] = max(maxs[2], z_coord)
        while target_index < len(sorted_point_ids) and sorted_point_ids[target_index] == point_index:
            target_index += 1
    if target_index != len(sorted_point_ids):
        raise RuntimeError(
            f"Only resolved {target_index} of {len(sorted_point_ids)} requested point ids from {points_path}."
        )
    return (mins[0], maxs[0], mins[1], maxs[1], mins[2], maxs[2])


@lru_cache(maxsize=64)
def mesh_patch_bounds(mesh_root_text: str, patch_names: tuple[str, ...]) -> tuple[float, float, float, float, float, float]:
    mesh_root = Path(mesh_root_text)
    patch_ranges = load_boundary_patch_ranges(str(mesh_root))
    missing = [patch_name for patch_name in patch_names if patch_name not in patch_ranges]
    if missing:
        raise RuntimeError(
            f"Patch bounds requested for unknown patch names under {mesh_root}: {', '.join(missing)}"
        )
    face_ranges = [patch_ranges[patch_name] for patch_name in patch_names]
    point_ids = collect_patch_point_ids(mesh_root, face_ranges)
    return point_bounds_from_ids(mesh_root, point_ids)


def ordered_unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values))


def span_patch_names(profile, span_names: Iterable[str]) -> list[str]:
    patch_names: list[str] = []
    for span_name in span_names:
        definition = profile.major_spans[span_name]
        patch_names.extend(str(patch_name) for patch_name in definition["wall_patches"])
        patch_names.append(str(definition["start_patch"]))
        patch_names.append(str(definition["end_patch"]))
    return ordered_unique(patch_names)


def fallback_component_patch_names(mesh_root: Path, component: str) -> list[str]:
    patch_ranges = load_boundary_patch_ranges(str(mesh_root))
    available = set(patch_ranges)

    fallback_map = {
        "downcomer": [
            "pipeleg_right_01_lower",
            "pipeleg_right_02_middle",
            "pipeleg_right_03_upper",
            "ncc_pipeleg_right_01_lower_start",
            "ncc_pipeleg_right_03_upper_end",
        ],
        "upcomer": [
            "pipeleg_left_07_lower",
            "pipeleg_left_06_connector",
            "ncc_pipeleg_left_07_lower_end",
            "ncc_pipeleg_left_06_connector_start",
            "pipeleg_left_05_fitting",
            "pipeleg_left_04_test_section",
            "pipeleg_left_03_fitting",
            "ncc_pipeleg_left_05_fitting_end",
            "ncc_pipeleg_left_03_fitting_start",
            "pipeleg_left_02_connector",
            "pipeleg_left_01_upper",
            "ncc_pipeleg_left_02_connector_end",
            "ncc_pipeleg_left_01_upper_start",
        ],
        "heater": [
            "pipeleg_lower_04_straight",
            "pipeleg_lower_05_straight",
            "pipeleg_lower_06_straight",
        ],
        "cooler": [
            "pipeleg_upper_06_reducer",
            "pipeleg_upper_05_cooler",
            "pipeleg_upper_04_reducer",
        ],
    }
    patch_names = [patch_name for patch_name in fallback_map[component] if patch_name in available]
    if not patch_names:
        raise RuntimeError(
            f"Component view `{component}` is not available because no registered profile or fallback patch group matched under {mesh_root}."
        )
    return patch_names


def component_patch_names(case_entry: Path, source_id: str, component: str) -> list[str]:
    if component == "all":
        return []
    try:
        profile = get_case_analysis_profile(source_id)
    except KeyError as exc:
        return fallback_component_patch_names(resolve_mesh_root(case_entry), component)

    if component == "downcomer":
        return span_patch_names(profile, ["right_leg"])
    if component == "upcomer":
        return span_patch_names(profile, ["left_lower_leg", "test_section_span", "left_upper_leg"])
    if component == "heater":
        return ordered_unique(
            patch_name
            for patch_name, role_name in profile.thermal_patch_roles.items()
            if role_name == "heater"
        )
    if component == "cooler":
        return ordered_unique(
            patch_name
            for patch_name, role_name in profile.thermal_patch_roles.items()
            if role_name == "cooling_branch"
        )
    raise RuntimeError(f"Unsupported component selection: {component}")


def resolve_mesh_root(case_entry: Path) -> Path:
    mesh_root = case_entry.parent / "constant" / "polyMesh"
    if not mesh_root.exists():
        raise FileNotFoundError(f"Expected OpenFOAM polyMesh directory at {mesh_root}")
    return mesh_root


def component_clip_bounds(
    case_entry: Path,
    source_id: str,
    component: str,
    mesh_bounds: tuple[float, float, float, float, float, float],
) -> tuple[list[str], tuple[float, float, float, float, float, float], tuple[float, float, float, float, float, float]]:
    patch_names = component_patch_names(case_entry, source_id, component)
    raw_bounds = mesh_patch_bounds(str(resolve_mesh_root(case_entry)), tuple(patch_names))
    expanded_bounds = clamp_bounds(expand_bounds(raw_bounds), mesh_bounds)
    return patch_names, raw_bounds, expanded_bounds


def build_density_expression(source_root: Path, qoi: dict[str, object]) -> tuple[float, str]:
    case_metadata = load_case_metadata(source_root)
    fluid_properties = case_metadata.get("fluid_properties", {})
    rho_coeffs = fluid_properties.get("rho_coeffs", [])
    if not isinstance(rho_coeffs, list) or not rho_coeffs:
        raise RuntimeError(f"`fluid_properties.rho_coeffs` was not available in {source_root / 'case_config.yaml'}")
    try:
        reference_temperature_k = float(qoi["probe_T_avg_K"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(f"`probe_T_avg_K` was not available in qoi summary for {source_root.name}") from exc
    density_kg_m3 = 0.0
    for power, coefficient in enumerate(rho_coeffs):
        density_kg_m3 += float(coefficient) * (reference_temperature_k**power)
    if density_kg_m3 <= 0.0 or not math.isfinite(density_kg_m3):
        raise RuntimeError(
            f"Density computed from rho_coeffs at {reference_temperature_k:g} K was invalid: {density_kg_m3}"
        )
    return density_kg_m3, f"{0.5 * density_kg_m3:.16g}*mag(U)^2"


def build_calculator_function(field_name: str, source_root: Path, qoi: dict[str, object]) -> tuple[str, float | None]:
    config = FIELD_CONFIG[field_name]
    if field_name == "pressure_dynamic":
        density_kg_m3, expression = build_density_expression(source_root, qoi)
        return expression, density_kg_m3
    if field_name == "pressure_total":
        density_kg_m3, dynamic_expression = build_density_expression(source_root, qoi)
        return f"p + {dynamic_expression}", density_kg_m3
    return str(config["calculator_function"]), None


def configure_color_range(
    field_name: str,
    color_proxy,
    array_name: str,
    qoi: dict[str, object],
) -> tuple[float, float]:
    color_mode = str(FIELD_CONFIG[field_name].get("color_range_mode", "data"))
    if color_mode == "temperature_window":
        probe_t_avg_k = float(qoi["probe_T_avg_K"])
        return probe_t_avg_k - 30.0, probe_t_avg_k + 30.0

    color_min, color_max = get_array_range(color_proxy, array_name)
    if color_mode == "symmetric":
        bound = max(abs(color_min), abs(color_max), 1.0e-9)
        return -bound, bound
    if color_mode == "nonnegative":
        upper = max(color_max, 1.0)
        return 0.0, upper
    if color_min == color_max:
        color_max = color_min + 1.0
    return color_min, color_max


def build_component_clip(reader, bounds: tuple[float, float, float, float, float, float], last_time: float):
    clip_filter = Clip(Input=reader)
    clip_filter.ClipType = "Box"
    clip_filter.ClipType.Position = [bounds[0], bounds[2], bounds[4]]
    clip_filter.ClipType.Length = [bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]]
    clip_filter.Invert = 0
    UpdatePipeline(time=last_time, proxy=clip_filter)
    clipped_bounds = get_mesh_bounds(clip_filter)
    if not bounds_within(clipped_bounds, bounds, tolerance=5.0e-4):
        clip_filter.Invert = 1
        UpdatePipeline(time=last_time, proxy=clip_filter)
        clipped_bounds = get_mesh_bounds(clip_filter)
    if not bounds_within(clipped_bounds, bounds, tolerance=5.0e-4):
        raise RuntimeError(
            f"Component clip bounds were not respected. Requested {bounds}, observed {clipped_bounds}."
        )
    return clip_filter, clipped_bounds


def export_vector(path: Path, render_view) -> tuple[bool, str]:
    try:
        ExportView(str(path), view=render_view)
        if path.exists():
            return True, ""
        return False, f"ExportView completed without creating `{path.suffix}`."
    except Exception as exc:  # pragma: no cover - ParaView runtime specific
        return False, str(exc)


def reference_coordinate(min_value: float, max_value: float) -> float:
    if min_value <= 0.0 <= max_value:
        return 0.0
    return 0.5 * (min_value + max_value)


def style_scalar_bar(scalar_bar, title: str) -> None:
    scalar_bar.Title = title
    scalar_bar.ComponentTitle = ""
    scalar_bar.TitleColor = [0.0, 0.0, 0.0]
    scalar_bar.LabelColor = [0.0, 0.0, 0.0]


def add_time_stamp(render_view, last_time: float) -> None:
    stamp = Text()
    stamp.Text = f"t = {last_time:g} s"
    stamp_display = Show(stamp, render_view)
    stamp_display.WindowLocation = "Upper Right Corner"
    stamp_display.Color = [0.0, 0.0, 0.0]
    stamp_display.FontSize = 18
    stamp_display.Bold = 1


def render_case(
    row: dict[str, str],
    output_root: Path,
    field_name: str,
    requested_association: str,
    component: str,
) -> dict[str, object]:
    source_id = row["source_id"]
    source_root = Path(row["source_root"]).resolve()
    config = FIELD_CONFIG[field_name]
    qoi = load_qoi_summary(source_id)
    paths = figure_paths(output_root, source_id, field_name, component)
    last_time = discover_last_time(source_root)
    case_entry, case_type = locate_case_entry(source_root, source_id, config["reader_arrays"], last_time)

    ResetSession()
    render_view = CreateView("RenderView")
    render_view.ViewSize = [2400, 1600]
    render_view.Background = [1.0, 1.0, 1.0]
    render_view.OrientationAxesVisibility = 0
    render_view.UseColorPaletteForBackground = 0
    render_view.CameraParallelProjection = 1

    reader = OpenFOAMReader(FileName=str(case_entry))
    reader.CaseType = case_type
    reader.MeshRegions = ["internalMesh"]
    if hasattr(reader, "ListtimestepsaccordingtocontrolDict"):
        reader.ListtimestepsaccordingtocontrolDict = 0
    configure_reader_arrays(reader, config["reader_arrays"], requested_association)
    SetActiveSource(reader)

    UpdatePipeline(proxy=reader)
    UpdatePipeline(time=last_time, proxy=reader)

    mesh_bounds = get_mesh_bounds(reader)
    component_patches: list[str] = []
    component_bounds: tuple[float, float, float, float, float, float] | None = None
    clip_bounds: tuple[float, float, float, float, float, float] | None = None
    input_proxy = reader
    input_bounds = mesh_bounds
    if component != "all":
        component_patches, component_bounds, clip_bounds = component_clip_bounds(
            case_entry,
            source_id,
            component,
            mesh_bounds,
        )
        input_proxy, input_bounds = build_component_clip(reader, clip_bounds, last_time)

    xmin, xmax, ymin, ymax, zmin, zmax = input_bounds
    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    plane_z = reference_coordinate(zmin, zmax)

    slice_filter = Slice(Input=input_proxy)
    slice_filter.SliceType = "Plane"
    slice_filter.HyperTreeGridSlicer = "Plane"
    slice_filter.SliceType.Origin = [xmid, ymid, plane_z]
    slice_filter.SliceType.Normal = [0.0, 0.0, 1.0]
    UpdatePipeline(time=last_time, proxy=slice_filter)

    color_proxy = slice_filter
    array_name = str(config["association_array"])
    derived_density_kg_m3: float | None = None
    calculator_expression = ""
    if "calculator_result_array" in config:
        calculator = Calculator(Input=slice_filter)
        calculator.AttributeType = calculator_attribute_type(
            slice_filter,
            str(config["association_array"]),
            requested_association,
        )
        calculator.ResultArrayName = str(config["calculator_result_array"])
        calculator_expression, derived_density_kg_m3 = build_calculator_function(field_name, source_root, qoi)
        calculator.Function = calculator_expression
        UpdatePipeline(time=last_time, proxy=calculator)
        color_proxy = calculator
        array_name = str(config["calculator_result_array"])

    slice_display = Show(color_proxy, render_view)
    slice_display.Representation = "Surface"
    if hasattr(slice_display, "InterpolateScalarsBeforeMapping"):
        slice_display.InterpolateScalarsBeforeMapping = 0
    association = resolve_array_association(color_proxy, array_name, requested_association)
    ColorBy(slice_display, (association, array_name))
    lut = GetColorTransferFunction(array_name)
    color_min, color_max = configure_color_range(field_name, color_proxy, array_name, qoi)
    lut.RescaleTransferFunction(color_min, color_max)
    scalar_bar = GetScalarBar(lut, render_view)
    style_scalar_bar(scalar_bar, config["scalar_title"])
    slice_display.SetScalarBarVisibility(render_view, True)
    add_time_stamp(render_view, last_time)

    z_span = max(abs(zmax - zmin), 1.0)
    camera_offset = 2.0 * z_span
    render_view.CameraPosition = [xmid, ymid, plane_z - camera_offset]
    render_view.CameraFocalPoint = [xmid, ymid, plane_z]
    render_view.CameraViewUp = [0.0, 1.0, 0.0]
    render_view.CameraParallelScale = 0.55 * max(abs(xmax - xmin), abs(ymax - ymin), 1.0)

    Render(render_view)
    SaveScreenshot(str(paths["png"]), render_view, ImageResolution=[2400, 1600])

    vector_results: dict[str, tuple[bool, str]] = {}
    for fmt in ("svg", "pdf"):
        exported, reason = export_vector(paths[fmt], render_view)
        vector_results[fmt] = (exported, reason)
        if not exported and paths[fmt].exists():
            paths[fmt].unlink()

    return {
        "source_id": source_id,
        "case_id": row["case_id"],
        "source_root": str(source_root),
        "field": field_name,
        "field_arrays": list(config["reader_arrays"]),
        "component": component,
        "case_entry": str(case_entry),
        "case_type": case_type,
        "last_time": last_time,
        "requested_array_association": requested_association,
        "resolved_array_association": association,
        "component_patch_names": component_patches,
        "component_patch_bounds": list(component_bounds) if component_bounds is not None else [],
        "component_clip_bounds": list(clip_bounds) if clip_bounds is not None else [],
        "input_bounds": list(input_bounds),
        "rendered_array_name": array_name,
        "calculator_expression": calculator_expression,
        "derived_density_kg_m3": derived_density_kg_m3,
        "color_range": [color_min, color_max],
        "slice_origin": [xmid, ymid, plane_z],
        "slice_normal": [0.0, 0.0, 1.0],
        "camera_position": [float(value) for value in render_view.CameraPosition],
        "camera_focal_point": [float(value) for value in render_view.CameraFocalPoint],
        "png_path": str(paths["png"]),
        "png_exists": paths["png"].exists(),
        "svg_path": str(paths["svg"]),
        "svg_exported": vector_results["svg"][0],
        "svg_reason": vector_results["svg"][1],
        "pdf_path": str(paths["pdf"]),
        "pdf_exported": vector_results["pdf"][0],
        "pdf_reason": vector_results["pdf"][1],
    }


def main() -> int:
    args = parse_args()
    output_root = ensure_dir(Path(args.output_root).resolve())
    status_path = (
        Path(args.status_path).resolve()
        if args.status_path
        else default_status_path(output_root, args.field, args.component)
    )

    selected_ids = set(args.source_ids)
    rows = [
        row
        for row in read_registry_rows()
        if row.get("status") == "registered"
        and row.get("source_id")
        and (not selected_ids or row["source_id"] in selected_ids)
    ]

    results: list[dict[str, object]] = []
    for row in rows:
        try:
            result = render_case(row, output_root, args.field, args.array_association, args.component)
            result["status"] = "rendered"
        except Exception as exc:  # pragma: no cover - ParaView runtime specific
            result = {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "source_root": row["source_root"],
                "field": args.field,
                "component": args.component,
                "requested_array_association": args.array_association,
                "status": "failed",
                "error": str(exc),
            }
        results.append(result)
        print(json.dumps(result, indent=2))

    payload = {
        "generated_at": iso_timestamp(),
        "field": args.field,
        "component": args.component,
        "output_root": str(output_root),
        "status_path": str(status_path),
        "requested_array_association": args.array_association,
        "case_count": len(results),
        "rendered_count": sum(1 for item in results if item["status"] == "rendered"),
        "failed_count": sum(1 for item in results if item["status"] == "failed"),
        "results": results,
    }
    json_dump(status_path, payload)
    return 0 if payload["failed_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
