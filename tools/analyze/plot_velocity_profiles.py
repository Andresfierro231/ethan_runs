#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import ensure_dir, json_dump, safe_float  # noqa: E402
from tools.extract.postprocessing_registry_common import (  # noqa: E402
    case_context,
    case_registry_root,
    numeric_time_dirs,
    parse_velocity_profile_file,
    read_csv_rows,
)


DEFAULT_FORMATS = ("svg", "png")
COMPONENT_MAP = {"Ux": "U_x_m_s", "Uy": "U_y_m_s", "Uz": "U_z_m_s"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot aggregated velocity profiles for selected times.")
    parser.add_argument("--source-id", required=True, help="Registered source identifier.")
    parser.add_argument("--output-name", required=True, help="Basename for the output plot files.")
    parser.add_argument("--output-dir", help="Override the default registry-local plot directory.")
    parser.add_argument("--input-csv", help="Optional aggregated CSV override. Defaults to the registry-local normalized aggregate.")
    parser.add_argument("--times", nargs="+", type=float, help="Requested profile times to match against available profile directories.")
    parser.add_argument("--last-n", type=int, default=None, help="Plot the last N available profile times. Defaults to 5 when --times is omitted.")
    parser.add_argument("--component", choices=("Ux", "Uy", "Uz"), default="Uy")
    parser.add_argument("--profile-axis", choices=("X", "Z", "both"), default="both")
    parser.add_argument("--levels", nargs="+", type=float, default=[0.25, 0.5, 0.75])
    parser.add_argument("--legend", choices=("on", "off"), default="on")
    parser.add_argument("--legend-loc", default="best")
    parser.add_argument("--xlim", nargs=2, type=float)
    parser.add_argument("--ylim", nargs=2, type=float)
    parser.add_argument("--xlabel", default="Distance [m]")
    parser.add_argument("--ylabel", help="Optional y-axis label override.")
    parser.add_argument("--title", help="Optional figure title override.")
    parser.add_argument("--format", action="append", choices=("svg", "png", "pdf"))
    return parser.parse_args()


def save_formats(fig: plt.Figure, output_dir: Path, output_name: str, formats: tuple[str, ...]) -> dict[str, str]:
    paths: dict[str, str] = {}
    for fmt in formats:
        target = ensure_dir(output_dir / fmt) / f"{output_name}.{fmt}"
        fig.savefig(target, dpi=200 if fmt == "png" else None)
        paths[fmt] = str(target)
    return paths


def nearest_time(requested: float, available: list[float]) -> float:
    return min(available, key=lambda value: (abs(value - requested), value))


def load_raw_profile_rows_for_times(
    context: dict[str, object],
    matched_times: list[float],
    component_key: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    selected_times = set(matched_times)
    velocity_profile_root = Path(context["runtime_root"]) / "postProcessing" / "velocity_profiles"
    component_index = {"U_x_m_s": 1, "U_y_m_s": 2, "U_z_m_s": 3}[component_key]
    for time_dir in numeric_time_dirs(velocity_profile_root):
        profile_time = float(time_dir.name)
        if profile_time not in selected_times:
            continue
        for path in sorted(time_dir.glob("*.xy")):
            match = re.match(r"Y_H_([0-9.]+)_([A-Za-z]+)", path.stem)
            profile_level = safe_float(match.group(1)) if match else None
            profile_axis = match.group(2) if match else ""
            for item in parse_velocity_profile_file(path):
                values = (
                    float(item["U_x_m_s"]),
                    float(item["U_y_m_s"]),
                    float(item["U_z_m_s"]),
                )
                rows.append(
                    {
                        "dataset": "velocity_profile",
                        "value_name": component_key,
                        "profile_axis": profile_axis,
                        "profile_time_s": profile_time,
                        "profile_level": profile_level,
                        "distance_m": float(item["distance_m"]),
                        "value": values[component_index - 1],
                    }
                )
    return rows


def main() -> int:
    args = parse_args()
    if args.times and args.last_n is not None:
        raise SystemExit("Use either --times or --last-n, not both.")

    context = case_context(args.source_id)
    if args.input_csv:
        rows = read_csv_rows(Path(args.input_csv))
        available_times = sorted({float(row["profile_time_s"]) for row in rows if safe_float(row.get("profile_time_s")) is not None})
    else:
        velocity_profile_root = Path(context["runtime_root"]) / "postProcessing" / "velocity_profiles"
        available_times = [float(path.name) for path in numeric_time_dirs(velocity_profile_root)]
        rows: list[dict[str, object]] = []
    component_key = COMPONENT_MAP[args.component]
    if not available_times:
        raise SystemExit("No velocity profile times are available.")

    if args.times:
        requested_times = [float(item) for item in args.times]
        matched_times = [nearest_time(item, available_times) for item in requested_times]
    else:
        count = args.last_n if args.last_n is not None else 5
        matched_times = available_times[-count:]
        requested_times = matched_times[:]

    if args.input_csv:
        profile_rows = [
            row
            for row in rows
            if row.get("dataset") == "velocity_profile"
            and row.get("value_name") == component_key
            and row.get("profile_axis") in ("X", "Z")
            and safe_float(row.get("profile_time_s")) in matched_times
        ]
    else:
        profile_rows = load_raw_profile_rows_for_times(context, matched_times, component_key)
        profile_rows = [row for row in profile_rows if row.get("profile_axis") in ("X", "Z")]

    if not profile_rows:
        raise SystemExit("No aggregated velocity profile rows were found for this case.")

    requested_axes = ("X", "Z") if args.profile_axis == "both" else (args.profile_axis,)
    level_strings = {f"{level:.2f}" for level in args.levels}

    figure_count = len(requested_axes)
    fig, axes = plt.subplots(1, figure_count, figsize=(7.2 * figure_count, 5.0), squeeze=False, constrained_layout=True)
    actual_match_note = ", ".join(
        f"{requested:g}->{matched:g}" if requested != matched else f"{matched:g}"
        for requested, matched in zip(requested_times, matched_times)
    )

    for axis_index, axis_name in enumerate(requested_axes):
        ax = axes[0][axis_index]
        axis_rows = [row for row in profile_rows if row.get("profile_axis") == axis_name and f"{safe_float(row.get('profile_level')) or 0.0:.2f}" in level_strings]
        if not axis_rows:
            continue
        for matched_time in matched_times:
            time_rows = [row for row in axis_rows if safe_float(row.get("profile_time_s")) == matched_time]
            grouped: dict[str, list[tuple[float, float]]] = {}
            for row in time_rows:
                level = f"{safe_float(row.get('profile_level')) or 0.0:.2f}"
                distance = safe_float(row.get("distance_m"))
                value = safe_float(row.get("value"))
                if distance is None or value is None:
                    continue
                grouped.setdefault(level, []).append((float(distance), float(value)))
            for level in sorted(grouped):
                ordered = sorted(grouped[level], key=lambda item: item[0])
                ax.plot(
                    [item[0] for item in ordered],
                    [item[1] for item in ordered],
                    label=f"t={matched_time:g}, H={level}",
                    linewidth=1.5,
                )

        ax.set_title(f"{axis_name}-profiles")
        ax.set_xlabel(args.xlabel)
        ax.set_ylabel(args.ylabel or f"{args.component} [m/s]")
        ax.grid(True, alpha=0.25)
        if args.xlim:
            ax.set_xlim(args.xlim)
        if args.ylim:
            ax.set_ylim(args.ylim)
        ax.text(0.98, 0.98, f"matched: {actual_match_note}", transform=ax.transAxes, ha="right", va="top", fontsize=8)
        if args.legend == "on":
            ax.legend(loc=args.legend_loc, fontsize=8)

    fig.suptitle(args.title or f"{args.source_id} velocity profiles ({args.component})")
    output_dir = Path(args.output_dir) if args.output_dir else case_registry_root(context) / "plots" / "velocity_profiles"
    formats = tuple(args.format) if args.format else DEFAULT_FORMATS
    figure_paths = save_formats(fig, output_dir, args.output_name, formats)
    plt.close(fig)

    metadata = {
        "source_id": args.source_id,
        "plot_kind": "velocity_profiles",
        "output_name": args.output_name,
        "component": args.component,
        "requested_times": requested_times,
        "matched_times": matched_times,
        "axes": list(requested_axes),
        "levels": sorted(level_strings),
        "formats": list(formats),
        "figure_paths": figure_paths,
    }
    json_dump(ensure_dir(output_dir) / f"{args.output_name}.json", metadata)
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
