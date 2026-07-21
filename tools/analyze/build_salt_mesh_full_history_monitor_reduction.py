#!/usr/bin/env python3
"""Merge Salt 2/4 mesh endpoint postProcessing monitor histories.

This read-only reducer replaces the AGENT-228 tail-window screen with full
restart-segment summaries for scalar monitors that already exist in Ethan's
external Salt mesh-family source tree. It still does not reconstruct fields or
run OpenFOAM utilities.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, ensure_dir, iso_timestamp  # noqa: E402

DEFAULT_CATALOG = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_quality_gate/mesh_case_catalog.csv"
)
DEFAULT_OUTPUT_DIR = (
    WORKSPACE_ROOT
    / "work_products/2026-07/2026-07-09/2026-07-09_salt_mesh_refinement_followon_readiness"
)

ENDPOINT_CASES = ("salt_test_2_jin", "salt_test_4_jin")
MESH_ORDER = ("coarse", "medium", "fine")
WINDOW_FRAC = 0.25
MDOT_MONITORS = [
    "mdot_pipeleg_left_04_test_section",
    "mdot_pipeleg_lower_05_straight",
    "mdot_pipeleg_right_02_middle",
    "mdot_pipeleg_upper_05_cooler",
]

MONITOR_FIELDS = [
    "source_id",
    "case_id",
    "mesh_level",
    "quantity",
    "monitor",
    "family",
    "segment_count",
    "source_file_count",
    "source_files",
    "first_time_s",
    "last_time_s",
    "time_window_start_s",
    "time_window_end_s",
    "n_samples",
    "mean_value",
    "last_value",
    "std_value",
    "relative_std",
    "drift_fraction",
    "amplitude_fraction",
    "series_verdict",
    "units",
]

COVERAGE_FIELDS = [
    "source_id",
    "case_id",
    "mesh_level",
    "family",
    "family_exists",
    "segment_count",
    "file_count",
    "first_segment_start_s",
    "last_segment_start_s",
    "latest_file_count",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE_ROOT))
    except ValueError:
        return str(path)


def numeric(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def numeric_segment_dirs(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    pairs: list[tuple[float, Path]] = []
    for child in path.iterdir():
        value = numeric(child.name)
        if child.is_dir() and value is not None:
            pairs.append((value, child))
    return [item[1] for item in sorted(pairs, key=lambda item: item[0])]


def find_segment_files(monitor_dir: Path, filename: str) -> list[Path]:
    return [segment / filename for segment in numeric_segment_dirs(monitor_dir) if (segment / filename).is_file()]


def parse_numeric_rows(path: Path) -> list[list[Any]]:
    rows: list[list[Any]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            t = numeric(parts[0]) if parts else None
            if t is None:
                continue
            rows.append([t, *parts[1:]])
    return rows


def merge_scalar_files(paths: list[Path], value_index: int = -1) -> list[tuple[float, float]]:
    by_time: dict[float, float] = {}
    for path in paths:
        for row in parse_numeric_rows(path):
            if len(row) < 2:
                continue
            value = numeric(row[value_index])
            if value is not None:
                by_time[row[0]] = value
    return sorted(by_time.items())


def linear_slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    x_mean = mean(xs)
    y_mean = mean(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0.0:
        return 0.0
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom


def summarize_series(series: list[tuple[float, float]], window_frac: float = WINDOW_FRAC) -> dict[str, Any]:
    if not series:
        return {
            "first_time_s": "",
            "last_time_s": "",
            "time_window_start_s": "",
            "time_window_end_s": "",
            "n_samples": 0,
            "mean_value": "",
            "last_value": "",
            "std_value": "",
            "relative_std": "",
            "drift_fraction": "",
            "amplitude_fraction": "",
            "series_verdict": "missing_monitor",
        }
    first = series[0][0]
    last = series[-1][0]
    cutoff = first + (last - first) * (1.0 - window_frac)
    window = [(t, value) for t, value in series if t >= cutoff]
    if len(window) < 3:
        window = series[-min(3, len(series)) :]
    times = [item[0] for item in window]
    values = [item[1] for item in window]
    value_mean = mean(values)
    value_std = pstdev(values) if len(values) > 1 else 0.0
    scale = max(abs(value_mean), max(abs(value) for value in values), 1.0e-20)
    span = max(times) - min(times)
    drift = abs(linear_slope(times, values) * span) / scale
    amp = (max(values) - min(values)) / scale
    rel_std = value_std / scale
    if len(window) < 3:
        verdict = "short_or_partial"
    elif drift < 0.01 and amp < 0.02:
        verdict = "stationary"
    elif drift < 0.05 and amp < 0.10:
        verdict = "quasi_stationary"
    else:
        verdict = "drifting_or_oscillatory"
    return {
        "first_time_s": first,
        "last_time_s": last,
        "time_window_start_s": min(times),
        "time_window_end_s": max(times),
        "n_samples": len(window),
        "mean_value": value_mean,
        "last_value": series[-1][1],
        "std_value": value_std,
        "relative_std": rel_std,
        "drift_fraction": drift,
        "amplitude_fraction": amp,
        "series_verdict": verdict,
    }


def source_files(paths: list[Path]) -> str:
    return ";".join(rel(path) for path in paths)


def monitor_row(
    case: dict[str, str],
    *,
    quantity: str,
    monitor: str,
    family: str,
    paths: list[Path],
    series: list[tuple[float, float]],
    units: str,
) -> dict[str, Any]:
    summary = summarize_series(series)
    return {
        "source_id": case["source_id"],
        "case_id": case["case_id"],
        "mesh_level": case["mesh_level"],
        "quantity": quantity,
        "monitor": monitor,
        "family": family,
        "segment_count": len({path.parent.name for path in paths}),
        "source_file_count": len(paths),
        "source_files": source_files(paths),
        **summary,
        "units": units,
    }


def wallheatflux_series(paths: list[Path]) -> dict[str, list[tuple[float, float]]]:
    by_time: dict[float, list[float]] = {}
    for path in paths:
        local: dict[float, list[float]] = {}
        for row in parse_numeric_rows(path):
            if len(row) < 5:
                continue
            q_total = numeric(row[4])
            if q_total is not None:
                local.setdefault(row[0], []).append(q_total)
        for t, values in local.items():
            by_time[t] = values
    out = {
        "wall_gross_duty_w": [],
        "wall_heat_in_w": [],
        "wall_heat_out_w": [],
        "wall_net_q_w": [],
    }
    for t in sorted(by_time):
        values = by_time[t]
        heat_in = sum(value for value in values if value > 0)
        heat_out = sum(value for value in values if value < 0)
        out["wall_gross_duty_w"].append((t, sum(abs(value) for value in values)))
        out["wall_heat_in_w"].append((t, heat_in))
        out["wall_heat_out_w"].append((t, heat_out))
        out["wall_net_q_w"].append((t, heat_in + heat_out))
    return out


def yplus_series(paths: list[Path]) -> dict[str, list[tuple[float, float]]]:
    by_time: dict[float, list[tuple[float, float]]] = {}
    for path in paths:
        local: dict[float, list[tuple[float, float]]] = {}
        for row in parse_numeric_rows(path):
            if len(row) < 5:
                continue
            max_value = numeric(row[3])
            avg_value = numeric(row[4])
            if max_value is not None and avg_value is not None:
                local.setdefault(row[0], []).append((max_value, avg_value))
        for t, values in local.items():
            by_time[t] = values
    return {
        "yplus_global_max": [(t, max(item[0] for item in values)) for t, values in sorted(by_time.items())],
        "yplus_patch_average_mean": [(t, mean(item[1] for item in values)) for t, values in sorted(by_time.items())],
    }


def probe_series(paths: list[Path]) -> dict[str, list[tuple[float, float]]]:
    by_time: dict[float, list[float]] = {}
    for path in paths:
        local: dict[float, list[float]] = {}
        for row in parse_numeric_rows(path):
            values = [numeric(value) for value in row[1:]]
            clean = [value for value in values if value is not None]
            if clean:
                local[row[0]] = clean
        by_time.update(local)
    return {
        "probe_mean": [(t, mean(values)) for t, values in sorted(by_time.items())],
        "probe_span": [(t, max(values) - min(values)) for t, values in sorted(by_time.items())],
    }


def coverage(case: dict[str, str], family: str) -> dict[str, Any]:
    family_dir = Path(case["source_path"]) / "postProcessing" / family
    segments = numeric_segment_dirs(family_dir)
    files = [path for segment in segments for path in segment.iterdir() if path.is_file()]
    latest_files = list(segments[-1].iterdir()) if segments else []
    starts = [numeric(segment.name) for segment in segments]
    starts = [value for value in starts if value is not None]
    return {
        "source_id": case["source_id"],
        "case_id": case["case_id"],
        "mesh_level": case["mesh_level"],
        "family": family,
        "family_exists": "yes" if family_dir.exists() else "no",
        "segment_count": len(segments),
        "file_count": len(files),
        "first_segment_start_s": min(starts) if starts else "",
        "last_segment_start_s": max(starts) if starts else "",
        "latest_file_count": len([path for path in latest_files if path.is_file()]),
        "notes": "full_restart_segments_available" if segments else "missing_or_nonsegmented_family",
    }


def endpoint_cases(catalog: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [
        row
        for row in catalog
        if row.get("case_id") in ENDPOINT_CASES and row.get("fluid_variant") == "jin" and row.get("mesh_level") in MESH_ORDER
    ]
    return sorted(rows, key=lambda row: (ENDPOINT_CASES.index(row["case_id"]), MESH_ORDER.index(row["mesh_level"])))


def build_monitor_rows(catalog: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    monitor_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    for case in endpoint_cases(catalog):
        root = Path(case["source_path"]) / "postProcessing"
        for family in [
            *MDOT_MONITORS,
            "wallHeatFlux",
            "yPlus",
            "temperature_probes",
            "wall_temperature_probes",
            "velocity_profiles",
        ]:
            coverage_rows.append(coverage(case, family))

        mdot_values: list[float] = []
        for monitor in MDOT_MONITORS:
            paths = find_segment_files(root / monitor, "surfaceFieldValue.dat")
            series = merge_scalar_files(paths)
            row = monitor_row(case, quantity="mdot", monitor=monitor, family=monitor, paths=paths, series=series, units="kg/s")
            monitor_rows.append(row)
            value = numeric(row["mean_value"])
            if value is not None:
                mdot_values.append(abs(value))
        if mdot_values:
            monitor_rows.append(
                {
                    "source_id": case["source_id"],
                    "case_id": case["case_id"],
                    "mesh_level": case["mesh_level"],
                    "quantity": "mdot_abs_mean_kg_s",
                    "monitor": "mdot_monitor_mean",
                    "family": "mdot_composite",
                    "segment_count": "",
                    "source_file_count": "",
                    "source_files": "derived_from_mdot_monitor_rows",
                    "first_time_s": "",
                    "last_time_s": "",
                    "time_window_start_s": "",
                    "time_window_end_s": "",
                    "n_samples": len(mdot_values),
                    "mean_value": mean(mdot_values),
                    "last_value": "",
                    "std_value": pstdev(mdot_values) if len(mdot_values) > 1 else 0.0,
                    "relative_std": "",
                    "drift_fraction": "",
                    "amplitude_fraction": "",
                    "series_verdict": "derived_composite",
                    "units": "kg/s",
                }
            )

        whf_paths = find_segment_files(root / "wallHeatFlux", "wallHeatFlux.dat")
        for quantity, series in wallheatflux_series(whf_paths).items():
            monitor_rows.append(
                monitor_row(case, quantity=quantity, monitor="wallHeatFlux", family="wallHeatFlux", paths=whf_paths, series=series, units="W")
            )

        yplus_paths = find_segment_files(root / "yPlus", "yPlus.dat")
        for quantity, series in yplus_series(yplus_paths).items():
            monitor_rows.append(monitor_row(case, quantity=quantity, monitor="yPlus", family="yPlus", paths=yplus_paths, series=series, units="dimensionless"))

        for family, filename, prefix in [
            ("temperature_probes", "T", "temperature"),
            ("wall_temperature_probes", "T", "wall_temperature"),
        ]:
            paths = find_segment_files(root / family, filename)
            for suffix, series in probe_series(paths).items():
                quantity = f"{prefix}_{suffix}_K" if suffix == "probe_mean" else f"{prefix}_{suffix}_K"
                units = "K" if suffix == "probe_mean" else "K"
                monitor_rows.append(monitor_row(case, quantity=quantity, monitor=family, family=family, paths=paths, series=series, units=units))
    return monitor_rows, coverage_rows


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# Salt Mesh Full-History Monitor Reduction

Generated: `{summary['generated_at']}`

This package merges existing postProcessing restart segments for Salt 2/4 Jin
coarse, medium, and fine mesh endpoint cases. It is read-only and does not run
OpenFOAM utilities.

## Outputs

- `endpoint_full_history_monitor_summary.csv`: scalar monitor statistics from
  merged restart histories.
- `endpoint_postprocessing_family_coverage.csv`: per-family segment/file
  coverage, including velocity-profile snapshot coverage.
- `full_history_monitor_summary.json`: counts and provenance.

## Interpretation Boundary

Rows with `series_verdict=stationary` or `quasi_stationary` are reasonable
screening evidence for mesh-UQ readiness. Rows marked `drifting_or_oscillatory`,
`short_or_partial`, or `missing_monitor` must not be promoted to GCI input
without a later admission decision.
"""
    path.write_text(text, encoding="utf-8")


def run(catalog_path: Path, output_dir: Path) -> dict[str, Any]:
    out = ensure_dir(output_dir)
    monitor_rows, coverage_rows = build_monitor_rows(read_csv(catalog_path))
    write_csv(out / "endpoint_full_history_monitor_summary.csv", monitor_rows, MONITOR_FIELDS)
    write_csv(out / "endpoint_postprocessing_family_coverage.csv", coverage_rows, COVERAGE_FIELDS)
    verdict_counts: dict[str, int] = {}
    for row in monitor_rows:
        verdict_counts[row["series_verdict"]] = verdict_counts.get(row["series_verdict"], 0) + 1
    summary = {
        "generated_at": iso_timestamp(),
        "task_id": "AGENT-231",
        "output_dir": rel(out),
        "monitor_row_count": len(monitor_rows),
        "coverage_row_count": len(coverage_rows),
        "series_verdict_counts": dict(sorted(verdict_counts.items())),
        "source_tree_read_only": True,
        "generated_files": [
            rel(out / "endpoint_full_history_monitor_summary.csv"),
            rel(out / "endpoint_postprocessing_family_coverage.csv"),
            rel(out / "full_history_monitor_README.md"),
        ],
    }
    write_json(out / "full_history_monitor_summary.json", summary)
    write_readme(out / "full_history_monitor_README.md", summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(Path(args.catalog), Path(args.output_dir))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
