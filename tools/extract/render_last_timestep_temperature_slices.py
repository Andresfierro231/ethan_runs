#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

from paraview.simple import (  # type: ignore
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
REGISTRY_PATH = ROOT / "registry" / "case_registry.csv"
DEFAULT_OUTPUT_ROOT = ROOT / "figures"
DEFAULT_STATUS_PATH = DEFAULT_OUTPUT_ROOT / "last_timestep_temperature_slice_status.json"
VECTOR_FORMATS = ("svg", "pdf")
ARRAY_ASSOCIATION_CHOICES = ("cells", "points", "auto")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render ParaView last-timestep z-reference temperature slices for registered Ethan cases."
        )
    )
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        default=[],
        help="Specific registered source_id to render. Repeat to select multiple cases.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Directory for rendered figures and status output.",
    )
    parser.add_argument(
        "--status-path",
        default=str(DEFAULT_STATUS_PATH),
        help="Machine-readable run status JSON path.",
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


def figure_paths(output_root: Path, source_id: str) -> dict[str, Path]:
    figure_root = ensure_dir(output_root)
    return {
        "png": ensure_dir(figure_root / "png") / f"{source_id}.png",
        "svg": ensure_dir(figure_root / "svg") / f"{source_id}_last_timestep_temperature_slice.svg",
        "pdf": ensure_dir(figure_root / "pdf") / f"{source_id}_last_timestep_temperature_slice.pdf",
    }


def read_registry_rows() -> list[dict[str, str]]:
    with REGISTRY_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_qoi_summary(source_id: str) -> dict[str, object]:
    qoi_path = ROOT / "work_products" / source_id / "qoi_summary.json"
    with qoi_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def json_dump(path: Path, payload: object) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def locate_case_entry(source_root: Path, source_id: str) -> tuple[Path, str]:
    reconstructed_entry = (
        ROOT / "staging" / "render_inputs" / source_id / "reconstructed_case" / f"{source_id}.foam"
    )
    if reconstructed_entry.exists():
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

    raise FileNotFoundError(
        f"No .foam entrypoint found for {source_id} under {source_root}"
    )


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

    processors_root = source_root / "processors64"
    candidates.extend(numeric_dir_values(processors_root))

    for processor_dir in sorted(source_root.glob("processor*")):
        candidates.extend(numeric_dir_values(processor_dir))

    if not candidates:
        raise RuntimeError(f"No numeric timestep directories found under {source_root}.")
    return max(candidates)


def get_mesh_bounds(proxy) -> tuple[float, float, float, float, float, float]:
    bounds = proxy.GetDataInformation().GetBounds()
    return tuple(float(value) for value in bounds)


def pick_temperature_association(proxy) -> str:
    cell_info = proxy.GetCellDataInformation()
    if cell_info.GetArray("T") is not None:
        return "CELLS"
    point_info = proxy.GetPointDataInformation()
    if point_info.GetArray("T") is not None:
        return "POINTS"
    raise RuntimeError("Temperature field T was not present on slice output.")


def configure_reader_arrays(reader, array_name: str, requested_association: str) -> None:
    if hasattr(reader, "CellArrays") and requested_association in {"cells", "auto"}:
        reader.CellArrays = [array_name]
    elif hasattr(reader, "CellArrays"):
        reader.CellArrays = []

    if hasattr(reader, "PointArrays") and requested_association in {"points", "auto"}:
        reader.PointArrays = [array_name]
    elif hasattr(reader, "PointArrays"):
        reader.PointArrays = []


def resolve_temperature_association(proxy, requested_association: str) -> str:
    available = {
        "CELLS": proxy.GetCellDataInformation().GetArray("T") is not None,
        "POINTS": proxy.GetPointDataInformation().GetArray("T") is not None,
    }
    if requested_association == "cells":
        if available["CELLS"]:
            return "CELLS"
        raise RuntimeError("Requested cell-associated temperature data, but slice output did not contain cell array `T`.")
    if requested_association == "points":
        if available["POINTS"]:
            return "POINTS"
        raise RuntimeError("Requested point-associated temperature data, but slice output did not contain point array `T`.")
    return pick_temperature_association(proxy)


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


def style_scalar_bar(scalar_bar) -> None:
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
    requested_association: str,
) -> dict[str, object]:
    source_id = row["source_id"]
    source_root = Path(row["source_root"]).resolve()
    qoi = load_qoi_summary(source_id)
    probe_t_avg_k = float(qoi["probe_T_avg_K"])
    color_min = probe_t_avg_k - 30.0
    color_max = probe_t_avg_k + 30.0
    paths = figure_paths(output_root, source_id)
    png_path = paths["png"]
    svg_path = paths["svg"]
    pdf_path = paths["pdf"]
    case_entry, case_type = locate_case_entry(source_root, source_id)
    last_time = discover_last_time(source_root)

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
    configure_reader_arrays(reader, "T", requested_association)
    SetActiveSource(reader)

    UpdatePipeline(proxy=reader)
    UpdatePipeline(time=last_time, proxy=reader)

    xmin, xmax, ymin, ymax, zmin, zmax = get_mesh_bounds(reader)
    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    plane_z = reference_coordinate(zmin, zmax)

    slice_filter = Slice(Input=reader)
    slice_filter.SliceType = "Plane"
    slice_filter.HyperTreeGridSlicer = "Plane"
    slice_filter.SliceType.Origin = [xmid, ymid, plane_z]
    slice_filter.SliceType.Normal = [0.0, 0.0, 1.0]
    UpdatePipeline(time=last_time, proxy=slice_filter)

    slice_display = Show(slice_filter, render_view)
    slice_display.Representation = "Surface"
    if hasattr(slice_display, "InterpolateScalarsBeforeMapping"):
        slice_display.InterpolateScalarsBeforeMapping = 0
    association = resolve_temperature_association(slice_filter, requested_association)
    ColorBy(slice_display, (association, "T"))
    lut = GetColorTransferFunction("T")
    lut.RescaleTransferFunction(color_min, color_max)
    scalar_bar = GetScalarBar(lut, render_view)
    scalar_bar.Title = "Temperature [K]"
    scalar_bar.ComponentTitle = ""
    style_scalar_bar(scalar_bar)
    slice_display.SetScalarBarVisibility(render_view, True)
    add_time_stamp(render_view, last_time)

    z_span = max(abs(zmax - zmin), 1.0)
    camera_offset = 2.0 * z_span
    render_view.CameraPosition = [xmid, ymid, plane_z - camera_offset]
    render_view.CameraFocalPoint = [xmid, ymid, plane_z]
    render_view.CameraViewUp = [0.0, 1.0, 0.0]
    render_view.CameraParallelScale = 0.55 * max(abs(xmax - xmin), abs(ymax - ymin), 1.0)

    Render(render_view)
    SaveScreenshot(str(png_path), render_view, ImageResolution=[2400, 1600])

    vector_results: dict[str, tuple[bool, str]] = {}
    for fmt, path in (("svg", svg_path), ("pdf", pdf_path)):
        exported, reason = export_vector(path, render_view)
        vector_results[fmt] = (exported, reason)
        if not exported and path.exists():
            path.unlink()

    return {
        "source_id": source_id,
        "case_id": row["case_id"],
        "source_root": str(source_root),
        "case_entry": str(case_entry),
        "case_type": case_type,
        "last_time": last_time,
        "requested_array_association": requested_association,
        "resolved_array_association": association,
        "bulk_average_temperature_K": probe_t_avg_k,
        "temperature_range_K": [color_min, color_max],
        "slice_origin": [xmid, ymid, plane_z],
        "slice_normal": [0.0, 0.0, 1.0],
        "camera_position": [float(value) for value in render_view.CameraPosition],
        "camera_focal_point": [float(value) for value in render_view.CameraFocalPoint],
        "png_path": str(png_path),
        "png_exists": png_path.exists(),
        "svg_path": str(svg_path),
        "svg_exported": vector_results["svg"][0],
        "svg_reason": vector_results["svg"][1],
        "pdf_path": str(pdf_path),
        "pdf_exported": vector_results["pdf"][0],
        "pdf_reason": vector_results["pdf"][1],
    }


def main() -> int:
    args = parse_args()
    output_root = ensure_dir(Path(args.output_root).resolve())
    status_path = Path(args.status_path).resolve()

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
            result = render_case(row, output_root, args.array_association)
            result["status"] = "rendered"
        except Exception as exc:  # pragma: no cover - ParaView runtime specific
            result = {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "source_root": row["source_root"],
                "requested_array_association": args.array_association,
                "status": "failed",
                "error": str(exc),
            }
        results.append(result)
        print(json.dumps(result, indent=2))

    payload = {
        "generated_at": iso_timestamp(),
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
