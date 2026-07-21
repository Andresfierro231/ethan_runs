#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from paraview.simple import *  # type: ignore

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.extract.render_last_timestep_field_slices import (
    ARRAY_ASSOCIATION_CHOICES,
    build_component_clip,
    component_clip_bounds,
    configure_reader_arrays,
    discover_last_time,
    ensure_dir,
    export_vector,
    get_array_range,
    get_mesh_bounds,
    json_dump,
    locate_case_entry,
    read_registry_rows,
    reference_coordinate,
    resolve_array_association,
    style_scalar_bar,
)

from tools.extract.render_representative_field_movies import DEFAULT_REPRESENTATIVE_SOURCE_IDS


DEFAULT_OUTPUT_ROOT = ROOT / "figures" / "figures_rendered" / "paraview_velocity_arrows"
DEFAULT_COMPONENTS = ("upcomer", "downcomer", "heater", "cooler")
DEFAULT_MAX_GLYPH_POINTS = 900
DEFAULT_IMAGE_WIDTH = 3600
DEFAULT_IMAGE_HEIGHT = 2400
DEFAULT_CAMERA_SCALE_FACTOR = 0.32
DEFAULT_GLYPH_SCALE_MULTIPLIER = 0.22
DEFAULT_BASE_OPACITY = 0.12
AXIS_INDEX = {"x": 0, "y": 1, "z": 2}
VELOCITY_MODES = {
    "magnitude": {
        "stem_token": "velocity_magnitude_arrows",
        "title": "velocity magnitude arrows",
        "scalar_bar": "Velocity magnitude [m/s]",
        "scalar_array": "Umag",
        "scale_array": "Umag",
        "vector_array": "U",
        "color_range": "positive",
    },
    "y_component": {
        "stem_token": "velocity_y_component_arrows",
        "title": "y-velocity component arrows",
        "scalar_bar": "Y velocity [m/s]",
        "scalar_array": "U_y",
        "scale_array": "abs_U_y",
        "vector_array": "U_y_vector",
        "color_range": "symmetric",
    },
}
VIEW_PRESETS = {
    "front_z": {
        "slice_axis": "z",
        "camera_axis": "z",
        "camera_sign": -1.0,
        "view_up": [0.0, 1.0, 0.0],
        "label": "front view, normal to z",
    },
    "side_x": {
        "slice_axis": "x",
        "camera_axis": "x",
        "camera_sign": -1.0,
        "view_up": [0.0, 1.0, 0.0],
        "label": "side view, normal to x",
    },
    "side_neg_x": {
        "slice_axis": "x",
        "camera_axis": "x",
        "camera_sign": 1.0,
        "view_up": [0.0, 1.0, 0.0],
        "label": "opposite side view, normal to -x",
    },
    "side_y": {
        "slice_axis": "y",
        "camera_axis": "y",
        "camera_sign": 1.0,
        "view_up": [0.0, 0.0, 1.0],
        "label": "side view, normal to y",
    },
    "side_z": {
        "slice_axis": "z",
        "camera_axis": "z",
        "camera_sign": -1.0,
        "view_up": [0.0, 1.0, 0.0],
        "label": "side view, normal to z",
    },
    "top_y": {
        "slice_axis": "y",
        "camera_axis": "y",
        "camera_sign": 1.0,
        "view_up": [0.0, 0.0, 1.0],
        "label": "top view, normal to y",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render representative branch velocity-arrow stills.")
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        default=[],
        help="Specific representative source_id to render. Repeat to select multiple cases.",
    )
    parser.add_argument(
        "--component",
        action="append",
        choices=sorted(DEFAULT_COMPONENTS),
        dest="components",
        default=[],
        help="Specific branch component to render. Repeat to select multiple components.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Directory for rendered arrow stills.",
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
        help="Preferred reader association for velocity input.",
    )
    parser.add_argument(
        "--max-glyph-points",
        type=int,
        default=DEFAULT_MAX_GLYPH_POINTS,
        help="Maximum number of glyph sample points per branch image.",
    )
    parser.add_argument(
        "--image-width",
        type=int,
        default=DEFAULT_IMAGE_WIDTH,
        help="PNG export width in pixels.",
    )
    parser.add_argument(
        "--image-height",
        type=int,
        default=DEFAULT_IMAGE_HEIGHT,
        help="PNG export height in pixels.",
    )
    parser.add_argument(
        "--camera-scale-factor",
        type=float,
        default=DEFAULT_CAMERA_SCALE_FACTOR,
        help="Parallel camera scale multiplier relative to the branch span.",
    )
    parser.add_argument(
        "--glyph-scale-multiplier",
        type=float,
        default=DEFAULT_GLYPH_SCALE_MULTIPLIER,
        help="Arrow scale multiplier relative to branch span and case max selected velocity.",
    )
    parser.add_argument(
        "--base-opacity",
        type=float,
        default=DEFAULT_BASE_OPACITY,
        help="Opacity for the neutral branch slice shown behind the arrows.",
    )
    parser.add_argument(
        "--view-preset",
        choices=sorted(VIEW_PRESETS),
        default="front_z",
        help="Camera and slice preset. `front_z` preserves the original output convention; `side_x` is the thesis orthogonal upcomer view.",
    )
    parser.add_argument(
        "--output-suffix",
        default="",
        help="Optional suffix for PNG/SVG/PDF filenames. Defaults to the view preset for non-front views.",
    )
    parser.add_argument(
        "--velocity-mode",
        choices=sorted(VELOCITY_MODES),
        default="magnitude",
        help="Velocity field to visualize. `magnitude` keeps the legacy full-vector/magnitude render; `y_component` uses U_y*jHat arrows, abs(U_y) glyph scaling, and signed U_y color.",
    )
    return parser.parse_args()


def iso_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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


def branch_output_paths(
    output_root: Path,
    source_id: str,
    component: str,
    output_suffix: str = "",
    velocity_mode: str = "magnitude",
) -> dict[str, Path]:
    branch_root = ensure_dir(output_root / source_id / component)
    stem = f"{source_id}_{component}_{VELOCITY_MODES[velocity_mode]['stem_token']}"
    if output_suffix:
        stem = f"{stem}_{output_suffix}"
    return {
        "root": branch_root,
        "png": ensure_dir(branch_root / "png") / f"{stem}.png",
        "svg": ensure_dir(branch_root / "svg") / f"{stem}.svg",
        "pdf": ensure_dir(branch_root / "pdf") / f"{stem}.pdf",
        "status": branch_root / (f"status_{output_suffix}.json" if output_suffix else "status.json"),
    }


def default_status_path(output_root: Path) -> Path:
    return output_root / "representative_velocity_arrows_status.json"


def make_render_view() -> object:
    view = CreateView("RenderView")
    view.ViewSize = [DEFAULT_IMAGE_WIDTH, DEFAULT_IMAGE_HEIGHT]
    view.Background = [1.0, 1.0, 1.0]
    view.OrientationAxesVisibility = 0
    view.UseColorPaletteForBackground = 0
    view.CameraParallelProjection = 1
    if hasattr(view, "UseFXAA"):
        view.UseFXAA = 1
    return view


def make_reader(case_entry: Path, case_type: str, requested_association: str):
    reader = OpenFOAMReader(FileName=str(case_entry))
    reader.CaseType = case_type
    reader.MeshRegions = ["internalMesh"]
    if hasattr(reader, "ListtimestepsaccordingtocontrolDict"):
        reader.ListtimestepsaccordingtocontrolDict = 0
    configure_reader_arrays(reader, ("U",), requested_association)
    SetActiveSource(reader)
    return reader


def axis_bounds(bounds: tuple[float, float, float, float, float, float], axis: str) -> tuple[float, float]:
    idx = AXIS_INDEX[axis] * 2
    return float(bounds[idx]), float(bounds[idx + 1])


def axis_midpoint(bounds: tuple[float, float, float, float, float, float], axis: str) -> float:
    lo, hi = axis_bounds(bounds, axis)
    return 0.5 * (lo + hi)


def plane_span(bounds: tuple[float, float, float, float, float, float], normal_axis: str) -> float:
    spans = []
    for axis in ("x", "y", "z"):
        if axis == normal_axis:
            continue
        lo, hi = axis_bounds(bounds, axis)
        spans.append(abs(hi - lo))
    return max(max(spans or [1.0]), 1.0)


def make_slice(input_proxy, sample_time: float, view_preset: str = "front_z"):
    xmin, xmax, ymin, ymax, zmin, zmax = get_mesh_bounds(input_proxy)
    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    zmid = reference_coordinate(zmin, zmax)
    bounds = (xmin, xmax, ymin, ymax, zmin, zmax)
    view_config = VIEW_PRESETS[view_preset]
    slice_axis = str(view_config["slice_axis"])
    origin = [xmid, ymid, zmid]
    normal = [0.0, 0.0, 0.0]
    normal[AXIS_INDEX[slice_axis]] = 1.0
    origin[AXIS_INDEX[slice_axis]] = reference_coordinate(*axis_bounds(bounds, slice_axis))

    slice_filter = Slice(Input=input_proxy)
    slice_filter.SliceType = "Plane"
    slice_filter.HyperTreeGridSlicer = "Plane"
    slice_filter.SliceType.Origin = origin
    slice_filter.SliceType.Normal = normal
    UpdatePipeline(time=sample_time, proxy=slice_filter)
    return slice_filter, bounds, origin


def add_title(render_view, source_id: str, component: str, view_label: str) -> None:
    title = Text()
    title.Text = f"{source_id} | {component} | velocity magnitude arrows | {view_label}"
    title_display = Show(title, render_view)
    title_display.WindowLocation = "Upper Left Corner"
    title_display.Color = [0.0, 0.0, 0.0]
    title_display.FontSize = 18
    title_display.Bold = 1


def add_time_stamp(render_view, last_time: float) -> None:
    stamp = Text()
    stamp.Text = f"t = {last_time:g} s"
    stamp_display = Show(stamp, render_view)
    stamp_display.WindowLocation = "Lower Left Corner"
    stamp_display.Color = [0.0, 0.0, 0.0]
    stamp_display.FontSize = 16
    stamp_display.Bold = 1


def add_velocity_mode_arrays(input_proxy, sample_time: float, velocity_mode: str):
    mode = VELOCITY_MODES[velocity_mode]
    if velocity_mode == "magnitude":
        point_magnitude = Calculator(Input=input_proxy)
        point_magnitude.AttributeType = "Point Data"
        point_magnitude.ResultArrayName = str(mode["scalar_array"])
        point_magnitude.Function = "mag(U)"
        UpdatePipeline(time=sample_time, proxy=point_magnitude)
        return point_magnitude

    if velocity_mode == "y_component":
        y_component = Calculator(Input=input_proxy)
        y_component.AttributeType = "Point Data"
        y_component.ResultArrayName = str(mode["scalar_array"])
        y_component.Function = "U_Y"
        UpdatePipeline(time=sample_time, proxy=y_component)

        y_component_abs = Calculator(Input=y_component)
        y_component_abs.AttributeType = "Point Data"
        y_component_abs.ResultArrayName = str(mode["scale_array"])
        y_component_abs.Function = "abs(U_Y)"
        UpdatePipeline(time=sample_time, proxy=y_component_abs)

        y_component_vector = Calculator(Input=y_component_abs)
        y_component_vector.AttributeType = "Point Data"
        y_component_vector.ResultArrayName = str(mode["vector_array"])
        y_component_vector.Function = "U_Y*jHat"
        UpdatePipeline(time=sample_time, proxy=y_component_vector)
        return y_component_vector

    raise ValueError(f"Unsupported velocity mode: {velocity_mode}")


def case_render_context(
    row: dict[str, str],
    requested_association: str,
    glyph_scale_multiplier: float,
    view_preset: str,
    velocity_mode: str,
) -> dict[str, object]:
    source_id = row["source_id"]
    source_root = Path(row["source_root"]).resolve()
    last_time = discover_last_time(source_root)
    case_entry, case_type = locate_case_entry(source_root, source_id, ("U",), last_time)

    ResetSession()
    reader = make_reader(case_entry, case_type, requested_association)
    UpdatePipeline(proxy=reader)
    UpdatePipeline(time=last_time, proxy=reader)

    full_slice, full_bounds, full_origin = make_slice(reader, last_time, view_preset)
    point_velocity = CellDatatoPointData(Input=full_slice)
    UpdatePipeline(time=last_time, proxy=point_velocity)
    velocity_source = add_velocity_mode_arrays(point_velocity, last_time, velocity_mode)

    mode = VELOCITY_MODES[velocity_mode]
    scalar_array = str(mode["scalar_array"])
    scale_array = str(mode["scale_array"])
    color_min, color_max = get_array_range(velocity_source, scalar_array)
    if mode["color_range"] == "positive":
        color_min = 0.0
        if color_max <= 0.0:
            color_max = 1.0
    else:
        max_abs = max(abs(color_min), abs(color_max), 1.0e-9)
        color_min = -max_abs
        color_max = max_abs
    scale_min, scale_max = get_array_range(velocity_source, scale_array)
    scale_max = max(abs(scale_min), abs(scale_max), 1.0e-9)

    component_data: dict[str, dict[str, object]] = {}
    component_spans: list[float] = []
    for component in DEFAULT_COMPONENTS:
        patch_names, patch_bounds, clip_bounds = component_clip_bounds(case_entry, source_id, component, get_mesh_bounds(reader))
        span = max(clip_bounds[1] - clip_bounds[0], clip_bounds[3] - clip_bounds[2], 1.0e-9)
        component_spans.append(span)
        component_data[component] = {
            "patch_names": patch_names,
            "patch_bounds": list(patch_bounds),
            "clip_bounds": list(clip_bounds),
            "span": span,
        }

    reference_span = min(component_spans) if component_spans else 1.0
    scale_factor = glyph_scale_multiplier * reference_span / scale_max

    return {
        "source_id": source_id,
        "source_root": source_root,
        "last_time": last_time,
        "case_entry": case_entry,
        "case_type": case_type,
        "mesh_bounds": list(full_bounds),
        "slice_origin": full_origin,
        "color_range": [color_min, color_max],
        "scale_range": [scale_min, scale_max],
        "scale_factor": scale_factor,
        "component_data": component_data,
        "view_preset": view_preset,
        "velocity_mode": velocity_mode,
        "view_config": VIEW_PRESETS[view_preset],
    }


def configure_camera(render_view, bounds: tuple[float, float, float, float, float, float], focal_point: list[float], view_preset: str, camera_scale_factor: float) -> None:
    view_config = VIEW_PRESETS[view_preset]
    camera_axis = str(view_config["camera_axis"])
    camera_sign = float(view_config["camera_sign"])
    camera_idx = AXIS_INDEX[camera_axis]
    lo, hi = axis_bounds(bounds, camera_axis)
    camera_span = max(abs(hi - lo), 1.0)
    camera_offset = 2.0 * camera_span
    position = list(focal_point)
    position[camera_idx] = focal_point[camera_idx] + camera_sign * camera_offset
    render_view.CameraPosition = position
    render_view.CameraFocalPoint = list(focal_point)
    render_view.CameraViewUp = list(view_config["view_up"])
    render_view.CameraParallelScale = camera_scale_factor * plane_span(bounds, camera_axis)


def render_component(
    row: dict[str, str],
    output_root: Path,
    context: dict[str, object],
    component: str,
    requested_association: str,
    max_glyph_points: int,
    image_width: int,
    image_height: int,
    camera_scale_factor: float,
    base_opacity: float,
    view_preset: str,
    output_suffix: str,
) -> dict[str, object]:
    source_id = row["source_id"]
    source_root = Path(row["source_root"]).resolve()
    last_time = float(context["last_time"])
    case_entry = Path(str(context["case_entry"]))
    case_type = str(context["case_type"])
    color_min, color_max = [float(value) for value in context["color_range"]]
    scale_factor = float(context["scale_factor"])
    component_meta = dict(context["component_data"])[component]
    clip_bounds = tuple(float(value) for value in component_meta["clip_bounds"])
    patch_names = list(component_meta["patch_names"])
    patch_bounds = list(component_meta["patch_bounds"])
    paths = branch_output_paths(output_root, source_id, component, output_suffix)
    view_config = VIEW_PRESETS[view_preset]

    ResetSession()
    render_view = make_render_view()
    render_view.ViewSize = [image_width, image_height]
    reader = make_reader(case_entry, case_type, requested_association)
    UpdatePipeline(proxy=reader)
    UpdatePipeline(time=last_time, proxy=reader)

    clip_filter, clipped_bounds = build_component_clip(reader, clip_bounds, last_time)
    slice_filter, input_bounds, slice_origin = make_slice(clip_filter, last_time, view_preset)

    base_display = Show(slice_filter, render_view)
    base_display.Representation = "Surface"
    base_display.DiffuseColor = [0.72, 0.72, 0.72]
    base_display.AmbientColor = [0.72, 0.72, 0.72]
    base_display.Opacity = base_opacity

    point_velocity = CellDatatoPointData(Input=slice_filter)
    UpdatePipeline(time=last_time, proxy=point_velocity)
    point_magnitude = Calculator(Input=point_velocity)
    point_magnitude.AttributeType = "Point Data"
    point_magnitude.ResultArrayName = "Umag"
    point_magnitude.Function = "mag(U)"
    UpdatePipeline(time=last_time, proxy=point_magnitude)

    glyph = Glyph(Input=point_magnitude, GlyphType="Arrow")
    glyph.OrientationArray = ["POINTS", "U"]
    glyph.ScaleArray = ["POINTS", "Umag"]
    glyph_mode = "Uniform Spatial Distribution (Bounds Based)"
    glyph.GlyphMode = glyph_mode
    glyph.MaximumNumberOfSamplePoints = max_glyph_points
    glyph.Seed = 10339
    glyph.ScaleFactor = scale_factor
    if hasattr(glyph.GlyphType, "TipResolution"):
        glyph.GlyphType.TipResolution = 20
    if hasattr(glyph.GlyphType, "ShaftResolution"):
        glyph.GlyphType.ShaftResolution = 16
    if hasattr(glyph.GlyphType, "TipRadius"):
        glyph.GlyphType.TipRadius = 0.12
    if hasattr(glyph.GlyphType, "ShaftRadius"):
        glyph.GlyphType.ShaftRadius = 0.04
    UpdatePipeline(time=last_time, proxy=glyph)

    glyph_display = Show(glyph, render_view)
    glyph_display.Representation = "Surface"
    if hasattr(glyph_display, "InterpolateScalarsBeforeMapping"):
        glyph_display.InterpolateScalarsBeforeMapping = 0
    association = resolve_array_association(glyph, "Umag", "auto")
    ColorBy(glyph_display, (association, "Umag"))
    lut = GetColorTransferFunction("Umag")
    lut.RescaleTransferFunction(color_min, color_max)
    scalar_bar = GetScalarBar(lut, render_view)
    style_scalar_bar(scalar_bar, "Velocity magnitude [m/s]")
    glyph_display.SetScalarBarVisibility(render_view, True)

    configure_camera(render_view, input_bounds, list(slice_origin), view_preset, camera_scale_factor)

    add_title(render_view, source_id, component, str(view_config["label"]))
    add_time_stamp(render_view, last_time)

    Render(render_view)
    SaveScreenshot(str(paths["png"]), render_view, ImageResolution=[image_width, image_height])

    vector_results: dict[str, tuple[bool, str]] = {}
    for fmt in ("svg", "pdf"):
        exported, reason = export_vector(paths[fmt], render_view)
        vector_results[fmt] = (exported, reason)
        if not exported and paths[fmt].exists():
            paths[fmt].unlink()

    payload = {
        "generated_at": iso_timestamp(),
        "source_id": source_id,
        "case_id": row["case_id"],
        "source_root": str(source_root),
        "component": component,
        "case_entry": str(case_entry),
        "case_type": case_type,
        "last_time": last_time,
        "requested_array_association": requested_association,
        "resolved_array_association": association,
        "component_patch_names": patch_names,
        "component_patch_bounds": patch_bounds,
        "component_clip_bounds": list(clip_bounds),
        "clipped_bounds": list(clipped_bounds),
        "input_bounds": list(input_bounds),
        "slice_origin": slice_origin,
        "view_preset": view_preset,
        "view_label": view_config["label"],
        "slice_axis": view_config["slice_axis"],
        "camera_axis": view_config["camera_axis"],
        "camera_sign": view_config["camera_sign"],
        "camera_view_up": view_config["view_up"],
        "output_suffix": output_suffix,
        "glyph_mode": glyph_mode,
        "maximum_number_of_sample_points": max_glyph_points,
        "glyph_seed": glyph.Seed,
        "scale_factor": scale_factor,
        "camera_scale_factor": camera_scale_factor,
        "base_opacity": base_opacity,
        "image_resolution": [image_width, image_height],
        "color_range": [color_min, color_max],
        "png_path": str(paths["png"]),
        "png_exists": paths["png"].exists(),
        "svg_path": str(paths["svg"]),
        "svg_exported": vector_results["svg"][0],
        "svg_reason": vector_results["svg"][1],
        "pdf_path": str(paths["pdf"]),
        "pdf_exported": vector_results["pdf"][0],
        "pdf_reason": vector_results["pdf"][1],
        "status": "rendered" if paths["png"].exists() else "failed",
    }
    json_dump(paths["status"], payload)
    return payload


def main() -> int:
    args = parse_args()
    output_root = ensure_dir(Path(args.output_root).resolve())
    status_path = Path(args.status_path).resolve() if args.status_path else default_status_path(output_root)
    rows = representative_rows(set(args.source_ids))
    components = args.components or list(DEFAULT_COMPONENTS)
    output_suffix = args.output_suffix or (args.view_preset if args.view_preset != "front_z" else "")

    results: list[dict[str, object]] = []
    for row in rows:
        try:
            context = case_render_context(row, args.array_association, args.glyph_scale_multiplier, args.view_preset)
        except Exception as exc:
            context = {"error": str(exc)}
        for component in components:
            try:
                if "error" in context:
                    raise RuntimeError(str(context["error"]))
                result = render_component(
                    row,
                    output_root,
                    context,
                    component,
                    args.array_association,
                    args.max_glyph_points,
                    args.image_width,
                    args.image_height,
                    args.camera_scale_factor,
                    args.base_opacity,
                    args.view_preset,
                    output_suffix,
                )
            except Exception as exc:
                result = {
                    "generated_at": iso_timestamp(),
                    "source_id": row["source_id"],
                    "case_id": row["case_id"],
                    "component": component,
                    "requested_array_association": args.array_association,
                    "view_preset": args.view_preset,
                    "output_suffix": output_suffix,
                    "status": "failed",
                    "error": str(exc),
                }
            results.append(result)
            print(json.dumps(result, indent=2))

    payload = {
        "generated_at": iso_timestamp(),
        "output_root": str(output_root),
        "source_ids": [row["source_id"] for row in rows],
        "components": components,
        "requested_array_association": args.array_association,
        "max_glyph_points": args.max_glyph_points,
        "image_resolution": [args.image_width, args.image_height],
        "camera_scale_factor": args.camera_scale_factor,
        "glyph_scale_multiplier": args.glyph_scale_multiplier,
        "base_opacity": args.base_opacity,
        "view_preset": args.view_preset,
        "output_suffix": output_suffix,
        "image_count": len(results),
        "rendered_count": sum(1 for item in results if item.get("status") == "rendered"),
        "failed_count": sum(1 for item in results if item.get("status") == "failed"),
        "results": results,
    }
    json_dump(status_path, payload)
    return 0 if payload["failed_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
