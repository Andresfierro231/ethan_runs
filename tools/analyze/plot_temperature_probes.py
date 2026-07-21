#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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
from tools.extract.postprocessing_registry_common import case_context, case_registry_root, load_case_long_rows, select_rows  # noqa: E402


DEFAULT_FORMATS = ("svg", "png")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot aggregated temperature probes over time.")
    parser.add_argument("--source-id", required=True, help="Registered source identifier.")
    parser.add_argument("--output-name", required=True, help="Basename for the output plot files.")
    parser.add_argument("--output-dir", help="Override the default registry-local plot directory.")
    parser.add_argument("--input-csv", help="Optional aggregated CSV override. Defaults to the registry-local normalized aggregate.")
    parser.add_argument("--include", nargs="+", help="Optional subset of TP labels to include, e.g. TP1 TP4 TP6.")
    parser.add_argument("--exclude", nargs="+", default=[], help="Optional TP labels to exclude.")
    parser.add_argument("--legend", choices=("on", "off"), default="on")
    parser.add_argument("--legend-loc", default="best")
    parser.add_argument("--xlim", nargs=2, type=float)
    parser.add_argument("--ylim", nargs=2, type=float)
    parser.add_argument("--xlabel", default="Time [s]")
    parser.add_argument("--ylabel", default="Temperature [K]")
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


def main() -> int:
    args = parse_args()
    context = case_context(args.source_id)
    if args.input_csv:
        from tools.extract.postprocessing_registry_common import read_csv_rows  # noqa: E402

        rows = read_csv_rows(Path(args.input_csv))
    else:
        _loaded_context, rows = load_case_long_rows(args.source_id)
    plot_rows = select_rows(rows, dataset="temperature_probe", value_name="temperature_K")
    include = set(args.include or [])
    exclude = set(args.exclude or [])

    series_map: dict[str, list[tuple[float, float]]] = {}
    for row in plot_rows:
        label = str(row["entity_name"])
        if include and label not in include:
            continue
        if label in exclude:
            continue
        time_value = safe_float(row.get("time_s"))
        value = safe_float(row.get("value"))
        if time_value is None or value is None:
            continue
        series_map.setdefault(label, []).append((float(time_value), float(value)))

    if not series_map:
        raise SystemExit("No temperature probe rows matched the requested filters.")

    fig, ax = plt.subplots(figsize=(9.0, 5.0), constrained_layout=True)
    for label in sorted(series_map):
        ordered = sorted(series_map[label], key=lambda item: item[0])
        ax.plot([item[0] for item in ordered], [item[1] for item in ordered], label=label, linewidth=1.7)

    ax.set_title(args.title or f"{args.source_id} temperature probes")
    ax.set_xlabel(args.xlabel)
    ax.set_ylabel(args.ylabel)
    ax.grid(True, alpha=0.25)
    if args.xlim:
        ax.set_xlim(args.xlim)
    if args.ylim:
        ax.set_ylim(args.ylim)
    if args.legend == "on":
        ax.legend(loc=args.legend_loc, fontsize=8)

    output_dir = Path(args.output_dir) if args.output_dir else case_registry_root(context) / "plots" / "temperature_probes"
    formats = tuple(args.format) if args.format else DEFAULT_FORMATS
    figure_paths = save_formats(fig, output_dir, args.output_name, formats)
    plt.close(fig)

    metadata = {
        "source_id": args.source_id,
        "plot_kind": "temperature_probes",
        "output_name": args.output_name,
        "included_series": sorted(series_map),
        "excluded_series": sorted(exclude),
        "formats": list(formats),
        "figure_paths": figure_paths,
    }
    json_dump(ensure_dir(output_dir) / f"{args.output_name}.json", metadata)
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
