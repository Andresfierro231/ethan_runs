#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

from paraview.simple import *  # type: ignore

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.extract.render_last_timestep_field_slices import (
    ARRAY_ASSOCIATION_CHOICES,
    FIELD_CONFIG,
    build_calculator_function,
    build_component_clip,
    calculator_attribute_type,
    component_clip_bounds,
    configure_reader_arrays,
    ensure_dir,
    get_array_range,
    get_mesh_bounds,
    json_dump,
    read_registry_rows,
    reference_coordinate,
    resolve_array_association,
    style_scalar_bar,
)
from tools.extract.stage_latest_time_field_reconstruction import resolve_reconstruction_source_root


DEFAULT_OUTPUT_ROOT = ROOT / "figures" / "figures_rendered" / "paraview_movies"
DEFAULT_FIELDS = ("temperature", "velocity_y")
DEFAULT_REPRESENTATIVE_SOURCE_IDS = (
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "val_water_test_1_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
    "val_water_test_3_coarse_mesh_laminar",
    "val_water_test_4_coarse_mesh_laminar",
)
PANEL_COMPONENTS = ("all", "upcomer", "downcomer", "heater", "cooler")
INVALID_FIELD_TOKENS = (b"nan", b"inf")
PANEL_LABELS = {
    "all": "Overview",
    "upcomer": "Upcomer",
    "downcomer": "Downcomer",
    "heater": "Heater",
    "cooler": "Cooler",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render representative 5-panel field-development movies.")
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        default=[],
        help="Specific representative source_id to render. Repeat to select multiple cases.",
    )
    parser.add_argument(
        "--field",
        action="append",
        choices=sorted(DEFAULT_FIELDS),
        dest="fields",
        default=[],
        help="Field movie to render. Repeat to select multiple fields. Defaults to temperature and velocity_y.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Directory for rendered movies and frame sequences.",
    )
    parser.add_argument(
        "--status-path",
        default="",
        help="Optional aggregate status JSON path.",
    )
    parser.add_argument(
        "--array-association",
        choices=ARRAY_ASSOCIATION_CHOICES,
        default="cells",
        help="Preferred data association for slice coloring.",
    )
    parser.add_argument(
        "--frame-rate",
        type=int,
        default=2,
        help="Movie frame rate for packaged outputs.",
    )
    parser.add_argument(
        "--frames-only",
        action="store_true",
        help="Write the high-resolution PNG frame sequence only and skip packaged movie output.",
    )
    parser.add_argument(
        "--image-width",
        type=int,
        default=3840,
        help="PNG frame width in pixels.",
    )
    parser.add_argument(
        "--image-height",
        type=int,
        default=2160,
        help="PNG frame height in pixels.",
    )
    return parser.parse_args()


def iso_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def default_status_path(output_root: Path, fields: list[str]) -> Path:
    if len(fields) == 1:
        return output_root / f"representative_{fields[0]}_movie_status.json"
    return output_root / "representative_field_movies_status.json"


def representative_rows(selected_ids: set[str]) -> list[dict[str, str]]:
    rows = {
        row["source_id"]: row
        for row in read_registry_rows()
        if row.get("status") == "registered" and row.get("source_id") in DEFAULT_REPRESENTATIVE_SOURCE_IDS
    }
    source_ids = list(selected_ids or DEFAULT_REPRESENTATIVE_SOURCE_IDS)
    missing = [source_id for source_id in source_ids if source_id not in rows]
    if missing:
        raise RuntimeError(f"Representative source_ids were not registered: {', '.join(missing)}")
    return [rows[source_id] for source_id in source_ids]


def movie_paths(output_root: Path, source_id: str, field_name: str) -> dict[str, Path]:
    movie_root = ensure_dir(output_root / source_id / field_name)
    return {
        "root": movie_root,
        "frames": ensure_dir(movie_root / "frames"),
        "mp4": movie_root / f"{source_id}_{field_name}.mp4",
        "ogv": movie_root / f"{source_id}_{field_name}.ogv",
        "status": movie_root / "status.json",
    }


def make_render_view() -> object:
    view = CreateView("RenderView")
    view.ViewSize = [1200, 900]
    view.Background = [1.0, 1.0, 1.0]
    view.OrientationAxesVisibility = 0
    view.UseColorPaletteForBackground = 0
    view.CameraParallelProjection = 1
    return view


def create_five_panel_layout() -> tuple[object, dict[str, object]]:
    layout = CreateLayout(name="RepresentativeFieldMovie")
    views = {"all": make_render_view()}
    layout.AssignView(0, views["all"])
    layout.SplitViewHorizontal(views["all"], 0.48)

    views["upcomer"] = make_render_view()
    layout.AssignView(2, views["upcomer"])
    layout.SplitViewVertical(views["upcomer"], 0.5)

    views["heater"] = make_render_view()
    layout.AssignView(6, views["heater"])

    layout.SplitViewHorizontal(views["upcomer"], 0.5)
    views["downcomer"] = make_render_view()
    layout.AssignView(12, views["downcomer"])

    layout.SplitViewHorizontal(views["heater"], 0.5)
    views["cooler"] = make_render_view()
    layout.AssignView(14, views["cooler"])

    layout.SetSize(3200, 1800)
    return layout, views


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


def discover_case_times(source_root: Path) -> list[float]:
    candidates = numeric_dir_values(source_root)
    candidates.extend(numeric_dir_values(source_root / "processors64"))
    for processor_dir in sorted(source_root.glob("processor*")):
        candidates.extend(numeric_dir_values(processor_dir))
    times = sorted(set(candidates))
    if not times:
        raise RuntimeError(f"No numeric timestep directories found under {source_root}.")
    return times


def case_type_for_root(case_root: Path) -> str:
    return "Decomposed Case" if (case_root / "processors64").exists() else "Reconstructed Case"


def mirror_case_root(source_root: Path, source_id: str) -> Path:
    mirror_root = ensure_dir(ROOT / "cache" / "paraview_movie_cases" / source_id)
    for item in source_root.iterdir():
        target = mirror_root / item.name
        if target.is_symlink():
            if target.resolve() == item.resolve():
                continue
            target.unlink()
        elif target.exists():
            continue
        target.symlink_to(item, target_is_directory=item.is_dir())
    return mirror_root


def time_token(time_value: float) -> str:
    return f"{time_value:g}"


def field_file_paths(case_root: Path, time_value: float, required_arrays: Iterable[str]) -> list[Path]:
    time_dir = case_root / time_token(time_value)
    return [time_dir / str(array_name) for array_name in required_arrays]


def file_contains_invalid_tokens(path: Path) -> bool:
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                return False
            lowered = chunk.lower()
            if any(token in lowered for token in INVALID_FIELD_TOKENS):
                return True


def valid_animation_times(
    case_root: Path,
    candidate_times: list[float],
    required_arrays: Iterable[str],
) -> tuple[list[float], list[dict[str, object]]]:
    valid_times: list[float] = []
    skipped_times: list[dict[str, object]] = []
    for time_value in candidate_times:
        field_paths = field_file_paths(case_root, time_value, required_arrays)
        missing = [str(path) for path in field_paths if not path.exists()]
        if missing:
            skipped_times.append({"time": time_value, "reason": "missing_field_files", "paths": missing})
            continue
        invalid_paths = [str(path) for path in field_paths if file_contains_invalid_tokens(path)]
        if invalid_paths:
            skipped_times.append({"time": time_value, "reason": "invalid_numeric_tokens", "paths": invalid_paths})
            continue
        valid_times.append(time_value)
    return valid_times, skipped_times


def stage_filtered_animation_root(source_root: Path, source_id: str, valid_times: list[float]) -> Path:
    first_token = time_token(valid_times[0])
    last_token = time_token(valid_times[-1])
    mirror_root = ensure_dir(
        ROOT / "cache" / "paraview_movie_cases" / f"{source_id}_valid_{len(valid_times)}_{first_token}_{last_token}"
    )
    valid_names = {time_token(value) for value in valid_times}
    valid_names.update({"constant", "system", "0"})
    for item in source_root.iterdir():
        if item.name not in valid_names and item.name != f"{source_id}.foam":
            continue
        target = mirror_root / item.name
        if target.is_symlink():
            if target.resolve() == item.resolve():
                continue
            target.unlink()
        elif target.exists():
            continue
        target.symlink_to(item, target_is_directory=item.is_dir())
    foam_path = mirror_root / f"{source_id}.foam"
    if not foam_path.exists():
        foam_path.write_text("\n", encoding="utf-8")
    return mirror_root


def locate_animation_case_entry(
    source_root: Path,
    source_id: str,
    required_arrays: Iterable[str],
) -> tuple[Path, str, list[float], list[dict[str, object]]]:
    preferred_source_times = discover_case_times(source_root)
    staged_entry = ROOT / "staging" / "render_inputs" / source_id / "reconstructed_case" / f"{source_id}.foam"
    if staged_entry.exists():
        try:
            staged_times = discover_case_times(staged_entry.parent)
            staged_time_set = set(staged_times)
            candidate_times = [time_value for time_value in preferred_source_times if time_value in staged_time_set]
            if not candidate_times:
                candidate_times = staged_times
            if len(candidate_times) > 1:
                valid_times, skipped_times = valid_animation_times(staged_entry.parent, candidate_times, required_arrays)
                if not valid_times:
                    raise RuntimeError(f"No valid animation times remained after screening {source_id}.")
                if len(valid_times) != len(candidate_times):
                    filtered_root = stage_filtered_animation_root(staged_entry.parent, source_id, valid_times)
                    return filtered_root / f"{source_id}.foam", "Reconstructed Case", valid_times, skipped_times
                return staged_entry, "Reconstructed Case", valid_times, skipped_times
        except RuntimeError:
            pass

    preferred = source_root / "case.foam"
    if preferred.exists():
        return preferred, case_type_for_root(source_root), preferred_source_times, []

    foam_files = sorted(source_root.glob("*.foam"))
    if foam_files:
        return foam_files[0], case_type_for_root(source_root), preferred_source_times, []

    if all((source_root / name).exists() for name in ("0", "constant", "system")):
        mirror_root = mirror_case_root(source_root, source_id)
        mirror_entry = mirror_root / f"{source_id}.foam"
        if not mirror_entry.exists():
            mirror_entry.write_text("\n", encoding="utf-8")
        return mirror_entry, case_type_for_root(mirror_root), preferred_source_times, []

    raise FileNotFoundError(f"No animation-capable .foam entrypoint found for {source_id} under {source_root}")


def actual_animation_times() -> list[float]:
    scene = GetAnimationScene()
    scene.UpdateAnimationUsingDataTimeSteps()
    try:
        scene.PlayMode = "Snap To TimeSteps"
    except Exception:
        pass
    return [float(value) for value in scene.TimeKeeper.TimestepValues]


def clean_frame_dir(frame_dir: Path) -> None:
    ensure_dir(frame_dir)
    for path in frame_dir.glob("*.png"):
        path.unlink()


def render_frame_sequence(
    layout,
    reader,
    frame_dir: Path,
    frame_times: list[float],
    image_width: int,
    image_height: int,
) -> list[str]:
    clean_frame_dir(frame_dir)
    frame_paths: list[str] = []
    for frame_index, time_value in enumerate(frame_times):
        UpdatePipeline(time=time_value, proxy=reader)
        Render()
        frame_path = frame_dir / f"frame.{frame_index:04d}.png"
        SaveScreenshot(str(frame_path), viewOrLayout=layout, ImageResolution=[image_width, image_height])
        frame_paths.append(str(frame_path))
    return frame_paths


def make_reader(case_entry: Path, case_type: str, array_names: Iterable[str], requested_association: str):
    reader = OpenFOAMReader(FileName=str(case_entry))
    reader.CaseType = case_type
    reader.MeshRegions = ["internalMesh"]
    if hasattr(reader, "ListtimestepsaccordingtocontrolDict"):
        reader.ListtimestepsaccordingtocontrolDict = 0
    configure_reader_arrays(reader, array_names, requested_association)
    SetActiveSource(reader)
    return reader


def panel_slice_pipeline(
    reader,
    case_entry: Path,
    source_root: Path,
    source_id: str,
    field_name: str,
    requested_association: str,
    component: str,
    sample_time: float,
):
    input_proxy = reader
    input_bounds = get_mesh_bounds(reader)
    component_patches: list[str] = []
    if component != "all":
        component_patches, _, clip_bounds = component_clip_bounds(case_entry, source_id, component, input_bounds)
        input_proxy, input_bounds = build_component_clip(reader, clip_bounds, sample_time)

    xmin, xmax, ymin, ymax, zmin, zmax = input_bounds
    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    plane_z = reference_coordinate(zmin, zmax)

    slice_filter = Slice(Input=input_proxy)
    slice_filter.SliceType = "Plane"
    slice_filter.HyperTreeGridSlicer = "Plane"
    slice_filter.SliceType.Origin = [xmid, ymid, plane_z]
    slice_filter.SliceType.Normal = [0.0, 0.0, 1.0]
    UpdatePipeline(time=sample_time, proxy=slice_filter)

    config = FIELD_CONFIG[field_name]
    color_proxy = slice_filter
    array_name = str(config["association_array"])
    calculator_expression = ""
    if "calculator_result_array" in config:
        calculator = Calculator(Input=slice_filter)
        calculator.AttributeType = calculator_attribute_type(
            slice_filter,
            str(config["association_array"]),
            requested_association,
        )
        calculator.ResultArrayName = str(config["calculator_result_array"])
        calculator_expression, _ = build_calculator_function(field_name, source_root, {})
        calculator.Function = calculator_expression
        UpdatePipeline(time=sample_time, proxy=calculator)
        color_proxy = calculator
        array_name = str(config["calculator_result_array"])

    return {
        "component": component,
        "component_patch_names": component_patches,
        "input_bounds": input_bounds,
        "slice_origin": [xmid, ymid, plane_z],
        "slice_proxy": slice_filter,
        "color_proxy": color_proxy,
        "array_name": array_name,
        "calculator_expression": calculator_expression,
    }


def compute_color_range(proxy, array_name: str, field_name: str, times: list[float]) -> tuple[float, float]:
    lower = None
    upper = None
    for time_value in times:
        UpdatePipeline(time=time_value, proxy=proxy)
        range_min, range_max = get_array_range(proxy, array_name)
        lower = range_min if lower is None else min(lower, range_min)
        upper = range_max if upper is None else max(upper, range_max)
    if lower is None or upper is None:
        raise RuntimeError("No animation times were available for color-range discovery.")
    if field_name == "velocity_y":
        bound = max(abs(lower), abs(upper), 1.0e-9)
        return -bound, bound
    if lower == upper:
        upper = lower + 1.0
    return lower, upper


def add_panel_title(render_view, title: str) -> None:
    title_text = Text()
    title_text.Text = title
    title_display = Show(title_text, render_view)
    title_display.WindowLocation = "Upper Left Corner"
    title_display.Color = [0.0, 0.0, 0.0]
    title_display.FontSize = 16
    title_display.Bold = 1


def add_time_annotation(render_view, input_proxy) -> None:
    time_filter = AnnotateTimeFilter(Input=input_proxy)
    time_filter.Format = "t = {time:g} s"
    time_display = Show(time_filter, render_view)
    time_display.WindowLocation = "Lower Left Corner"
    time_display.Color = [0.0, 0.0, 0.0]
    time_display.FontSize = 14
    time_display.Bold = 1


def configure_panel_view(
    render_view,
    panel,
    field_name: str,
    color_range: tuple[float, float],
    source_id: str,
    requested_association: str,
) -> dict[str, object]:
    config = FIELD_CONFIG[field_name]
    color_proxy = panel["color_proxy"]
    array_name = panel["array_name"]

    display = Show(color_proxy, render_view)
    display.Representation = "Surface"
    if hasattr(display, "InterpolateScalarsBeforeMapping"):
        display.InterpolateScalarsBeforeMapping = 0
    association = resolve_array_association(color_proxy, array_name, requested_association)
    ColorBy(display, (association, array_name))
    lut = GetColorTransferFunction(array_name)
    lut.RescaleTransferFunction(*color_range)
    scalar_bar = GetScalarBar(lut, render_view)
    style_scalar_bar(scalar_bar, str(config["scalar_title"]))
    display.SetScalarBarVisibility(render_view, True)

    xmin, xmax, ymin, ymax, zmin, zmax = panel["input_bounds"]
    plane_z = panel["slice_origin"][2]
    z_span = max(abs(zmax - zmin), 1.0)
    camera_offset = 2.0 * z_span
    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    render_view.CameraPosition = [xmid, ymid, plane_z - camera_offset]
    render_view.CameraFocalPoint = [xmid, ymid, plane_z]
    render_view.CameraViewUp = [0.0, 1.0, 0.0]
    render_view.CameraParallelScale = 0.55 * max(abs(xmax - xmin), abs(ymax - ymin), 1.0)

    panel_title = f"{source_id} | {field_name} | {PANEL_LABELS[panel['component']]}"
    add_panel_title(render_view, panel_title)
    add_time_annotation(render_view, color_proxy)
    return {"association": association}


def save_movie_outputs(
    layout,
    scene,
    frame_dir: Path,
    mp4_path: Path,
    ogv_path: Path,
    frame_rate: int,
    frame_window: tuple[int, int],
) -> tuple[str, list[str], str]:
    frame_pattern = frame_dir / "frame.png"
    SaveAnimation(
        str(frame_pattern),
        viewOrLayout=layout,
        scene=scene,
        SuffixFormat=".%04d",
        FrameWindow=frame_window,
    )
    frame_paths = [str(path) for path in sorted(frame_dir.glob("*.png"))]
    movie_format = "mp4"
    movie_message = str(mp4_path)
    try:
        SaveAnimation(
            str(mp4_path),
            viewOrLayout=layout,
            scene=scene,
            FrameRate=frame_rate,
            FrameWindow=frame_window,
        )
        if not mp4_path.exists():
            raise RuntimeError(f"SaveAnimation did not create {mp4_path.name}")
    except Exception as exc:
        movie_format = "ogv"
        movie_message = str(exc)
        SaveAnimation(
            str(ogv_path),
            viewOrLayout=layout,
            scene=scene,
            FrameRate=frame_rate,
            FrameWindow=frame_window,
        )
        if not ogv_path.exists():
            movie_message = f"{movie_message}; SaveAnimation did not create {ogv_path.name}"
    return movie_format, frame_paths, movie_message


def render_movie(
    row: dict[str, str],
    output_root: Path,
    field_name: str,
    requested_association: str,
    frame_rate: int,
    *,
    frames_only: bool,
    image_width: int,
    image_height: int,
) -> dict[str, object]:
    source_id = row["source_id"]
    source_root = Path(row["source_root"]).resolve()
    resolved_source_root, source_root_candidates = resolve_reconstruction_source_root(source_root, source_id)
    paths = movie_paths(output_root, source_id, field_name)
    required_arrays = tuple(str(value) for value in FIELD_CONFIG[field_name]["reader_arrays"])
    case_entry, case_type, source_times, skipped_times = locate_animation_case_entry(
        resolved_source_root,
        source_id,
        required_arrays,
    )

    ResetSession()
    layout, views = create_five_panel_layout()
    reader = make_reader(case_entry, case_type, required_arrays, requested_association)
    UpdatePipeline(proxy=reader)
    scene_animation_times = actual_animation_times()
    frame_times = [float(value) for value in source_times]
    if not frame_times:
        raise RuntimeError(f"No animation timesteps were available for {source_id}.")
    sample_time = frame_times[0]
    UpdatePipeline(time=sample_time, proxy=reader)

    overview_panel = panel_slice_pipeline(
        reader,
        case_entry,
        source_root,
        source_id,
        field_name,
        requested_association,
        "all",
        sample_time,
    )
    color_range = compute_color_range(
        overview_panel["color_proxy"],
        overview_panel["array_name"],
        field_name,
        frame_times,
    )
    panels = {"all": overview_panel}
    for component in PANEL_COMPONENTS[1:]:
        panels[component] = panel_slice_pipeline(
            reader,
            case_entry,
            source_root,
            source_id,
            field_name,
            requested_association,
            component,
            sample_time,
        )

    panel_associations = {}
    for component, render_view in views.items():
        panel_associations[component] = configure_panel_view(
            render_view,
            panels[component],
            field_name,
            color_range,
            source_id,
            requested_association,
        )

    Render()
    frame_paths = render_frame_sequence(
        layout,
        reader,
        paths["frames"],
        frame_times,
        image_width,
        image_height,
    )
    frame_window = (0, max(len(frame_times) - 1, 0))
    movie_format = "frames_only"
    movie_message = "Packaged movie output skipped by --frames-only."
    movie_exists = False
    movie_path = ""
    if not frames_only:
        scene = GetAnimationScene()
        scene.UpdateAnimationUsingDataTimeSteps()
        if scene_animation_times == frame_times:
            movie_format, _, movie_message = save_movie_outputs(
                layout,
                scene,
                paths["frames"],
                paths["mp4"],
                paths["ogv"],
                frame_rate,
                frame_window,
            )
            movie_path = str(paths[movie_format])
            movie_exists = paths[movie_format].exists()
        else:
            movie_format = "frames_only"
            movie_message = (
                "Packaged movie output skipped because explicit frame times differ from "
                "ParaView scene timesteps."
            )

    payload = {
        "generated_at": iso_timestamp(),
        "source_id": source_id,
        "case_id": row["case_id"],
        "field": field_name,
        "source_root": str(source_root),
        "resolved_source_root": str(resolved_source_root),
        "source_root_candidates": source_root_candidates,
        "case_entry": str(case_entry),
        "case_type": case_type,
        "requested_array_association": requested_association,
        "resolved_array_associations": {
            component: panel_associations[component]["association"] for component in PANEL_COMPONENTS
        },
        "source_times": source_times,
        "skipped_times": skipped_times,
        "scene_animation_times": scene_animation_times,
        "frame_times": frame_times,
        "frame_count": len(frame_paths),
        "frame_paths": frame_paths,
        "frame_rate": frame_rate,
        "frame_window": list(frame_window),
        "image_resolution": [image_width, image_height],
        "color_range": list(color_range),
        "movie_format": movie_format,
        "movie_path": movie_path,
        "movie_exists": movie_exists,
        "movie_message": movie_message,
        "panel_bounds": {component: list(panels[component]["input_bounds"]) for component in PANEL_COMPONENTS},
        "component_patch_names": {
            component: panels[component]["component_patch_names"] for component in PANEL_COMPONENTS
        },
        "status": "rendered" if frame_paths else "failed",
    }
    json_dump(paths["status"], payload)
    return payload


def main() -> int:
    args = parse_args()
    output_root = ensure_dir(Path(args.output_root).resolve())
    fields = args.fields or list(DEFAULT_FIELDS)
    status_path = Path(args.status_path).resolve() if args.status_path else default_status_path(output_root, fields)
    rows = representative_rows(set(args.source_ids))

    results: list[dict[str, object]] = []
    for field_name in fields:
        for row in rows:
            try:
                result = render_movie(
                    row,
                    output_root,
                    field_name,
                    args.array_association,
                    args.frame_rate,
                    frames_only=args.frames_only,
                    image_width=args.image_width,
                    image_height=args.image_height,
                )
            except Exception as exc:
                result = {
                    "generated_at": iso_timestamp(),
                    "source_id": row["source_id"],
                    "case_id": row["case_id"],
                    "field": field_name,
                    "requested_array_association": args.array_association,
                    "status": "failed",
                    "error": str(exc),
                }
            results.append(result)
            print(json.dumps(result, indent=2))

    payload = {
        "generated_at": iso_timestamp(),
        "output_root": str(output_root),
        "fields": fields,
        "source_ids": [row["source_id"] for row in rows],
        "requested_array_association": args.array_association,
        "frames_only": args.frames_only,
        "image_resolution": [args.image_width, args.image_height],
        "movie_count": len(results),
        "rendered_count": sum(1 for item in results if item.get("status") == "rendered"),
        "failed_count": sum(1 for item in results if item.get("status") == "failed"),
        "results": results,
    }
    json_dump(status_path, payload)
    return 0 if payload["failed_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
