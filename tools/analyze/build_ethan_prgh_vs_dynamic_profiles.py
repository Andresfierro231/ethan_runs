#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt
import numpy as np

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.case_analysis_profiles import get_case_analysis_profile  # noqa: E402
from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, save_matplotlib_figure, safe_float  # noqa: E402

DEFAULT_PACKAGE_INDEX = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package" / "package_index.csv"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-23_ethan_prgh_vs_dynamic_profiles"

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build additive profile overlays of hydrostatic-corrected pressure p_rgh(s) "
            "and dynamic pressure q_dyn(s)=0.5*rho*U^2 from preserved per-case streamwise bins."
        )
    )
    parser.add_argument("--package-index", default=str(DEFAULT_PACKAGE_INDEX))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: Any) -> float:
    parsed = safe_float(value)
    if parsed is None or not math.isfinite(parsed):
        return math.nan
    return float(parsed)


def dynamic_pressure_pa(row: dict[str, str]) -> float:
    rho_bulk = finite_float(row.get("rho_bulk_kg_m3"))
    bulk_velocity = finite_float(row.get("bulk_velocity_m_s"))
    if not math.isfinite(rho_bulk) or not math.isfinite(bulk_velocity):
        return math.nan
    return 0.5 * rho_bulk * bulk_velocity * bulk_velocity


def build_profile_rows(package_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    output_rows: list[dict[str, Any]] = []
    missing_packages: list[str] = []
    for package_row in package_rows:
        source_id = package_row["source_id"]
        package_dir = Path(package_row["package_dir"])
        major_path = package_dir / "major_loss_cumulative_timeseries.csv"
        if not major_path.exists():
            missing_packages.append(source_id)
            continue
        for row in load_csv_rows(major_path):
            p_rgh = finite_float(row.get("p_rgh_wall_area_avg_pa"))
            p_full = finite_float(row.get("p_wall_area_avg_pa"))
            q_dyn = dynamic_pressure_pa(row)
            output_rows.append(
                {
                    "source_id": source_id,
                    "case_label": package_row["case_label"],
                    "family": package_row["family"],
                    "profile_name": package_row["profile_name"],
                    "package_dir": str(package_dir),
                    "time_s": finite_float(row.get("time_s")),
                    "span_name": row.get("span_name", ""),
                    "span_kind": row.get("span_kind", ""),
                    "bin_index": int(float(row["bin_index"])),
                    "s_start_m": finite_float(row.get("s_start_m")),
                    "s_end_m": finite_float(row.get("s_end_m")),
                    "s_mid_m": finite_float(row.get("s_mid_m")),
                    "p_wall_area_avg_pa": p_full,
                    "p_rgh_wall_area_avg_pa": p_rgh,
                    "hydro_proxy_p_minus_prgh_pa": p_full - p_rgh if math.isfinite(p_full) and math.isfinite(p_rgh) else math.nan,
                    "rho_bulk_kg_m3": finite_float(row.get("rho_bulk_kg_m3")),
                    "bulk_velocity_m_s": finite_float(row.get("bulk_velocity_m_s")),
                    "dynamic_pressure_pa": q_dyn,
                    "dp_major_gradient_direct_prgh_pa_per_m": finite_float(row.get("dp_major_gradient_direct_prgh_pa_per_m")),
                    "darcy_f_pressure_drop_prgh": finite_float(row.get("darcy_f_pressure_drop_prgh")),
                }
            )
    return output_rows, missing_packages


def summarize_profiles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["source_id"]), str(row["span_name"]))].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (source_id, span_name), payload in sorted(grouped.items()):
        payload_sorted = sorted(
            [item for item in payload if math.isfinite(float(item["s_mid_m"]))],
            key=lambda item: (float(item["time_s"]), int(item["bin_index"])),
        )
        case_label = str(payload[0]["case_label"])
        family = str(payload[0]["family"])

        by_time: dict[float, list[dict[str, Any]]] = defaultdict(list)
        for row in payload_sorted:
            time_s = float(row["time_s"])
            if math.isfinite(time_s):
                by_time[time_s].append(row)

        delta_p_rgh_values: list[float] = []
        q_dyn_mean_values: list[float] = []
        for time_s, time_rows in by_time.items():
            time_rows = sorted(time_rows, key=lambda item: int(item["bin_index"]))
            start = next((item for item in time_rows if math.isfinite(float(item["p_rgh_wall_area_avg_pa"]))), None)
            end = next((item for item in reversed(time_rows) if math.isfinite(float(item["p_rgh_wall_area_avg_pa"]))), None)
            if start and end:
                delta_p_rgh_values.append(float(end["p_rgh_wall_area_avg_pa"]) - float(start["p_rgh_wall_area_avg_pa"]))
            q_vals = [float(item["dynamic_pressure_pa"]) for item in time_rows if math.isfinite(float(item["dynamic_pressure_pa"]))]
            if q_vals:
                q_dyn_mean_values.append(float(np.mean(q_vals)))

        p_rgh_values = [float(item["p_rgh_wall_area_avg_pa"]) for item in payload if math.isfinite(float(item["p_rgh_wall_area_avg_pa"]))]
        q_dyn_values = [float(item["dynamic_pressure_pa"]) for item in payload if math.isfinite(float(item["dynamic_pressure_pa"]))]
        hydro_proxy_values = [float(item["hydro_proxy_p_minus_prgh_pa"]) for item in payload if math.isfinite(float(item["hydro_proxy_p_minus_prgh_pa"]))]
        summary_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label,
                "family": family,
                "span_name": span_name,
                "time_sample_count": len(by_time),
                "bin_row_count": len(payload),
                "mean_dynamic_pressure_pa": float(np.mean(q_dyn_values)) if q_dyn_values else math.nan,
                "max_dynamic_pressure_pa": max(q_dyn_values) if q_dyn_values else math.nan,
                "mean_p_rgh_pa": float(np.mean(p_rgh_values)) if p_rgh_values else math.nan,
                "min_p_rgh_pa": min(p_rgh_values) if p_rgh_values else math.nan,
                "max_p_rgh_pa": max(p_rgh_values) if p_rgh_values else math.nan,
                "mean_delta_p_rgh_end_minus_start_pa": float(np.mean(delta_p_rgh_values)) if delta_p_rgh_values else math.nan,
                "mean_hydro_proxy_p_minus_prgh_pa": float(np.mean(hydro_proxy_values)) if hydro_proxy_values else math.nan,
                "mean_q_dyn_vs_abs_delta_p_rgh_ratio": (
                    float(np.mean(q_dyn_mean_values) / max(np.mean(np.abs(delta_p_rgh_values)), 1.0e-12))
                    if q_dyn_mean_values and delta_p_rgh_values
                    else math.nan
                ),
            }
        )
    return summary_rows


def mean_profile_by_span(rows: list[dict[str, Any]], value_key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row["span_name"])][int(row["bin_index"])].append(row)

    span_profiles: dict[str, list[dict[str, Any]]] = {}
    for span_name, by_bin in grouped.items():
        payload: list[dict[str, Any]] = []
        for bin_index, bin_rows in sorted(by_bin.items()):
            values = [float(item[value_key]) for item in bin_rows if math.isfinite(float(item[value_key]))]
            s_mid_values = [float(item["s_mid_m"]) for item in bin_rows if math.isfinite(float(item["s_mid_m"]))]
            payload.append(
                {
                    "bin_index": bin_index,
                    "s_mid_m": float(np.mean(s_mid_values)) if s_mid_values else math.nan,
                    "mean": float(np.mean(values)) if values else math.nan,
                    "min": min(values) if values else math.nan,
                    "max": max(values) if values else math.nan,
                }
            )
        span_profiles[span_name] = payload
    return span_profiles


def rows_by_span_time(case_rows: list[dict[str, Any]]) -> dict[tuple[str, float], list[dict[str, Any]]]:
    grouped: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        time_s = float(row["time_s"])
        if math.isfinite(time_s):
            grouped[(str(row["span_name"]), time_s)].append(row)
    return grouped


def plot_case(case_rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    source_id = str(case_rows[0]["source_id"])
    case_label = str(case_rows[0]["case_label"])
    profile = get_case_analysis_profile(source_id)
    span_order = [name for name in profile.major_spans.keys() if any(str(row["span_name"]) == name for row in case_rows)]
    if not span_order:
        span_order = sorted({str(row["span_name"]) for row in case_rows})

    n_spans = len(span_order)
    ncols = 2
    nrows = math.ceil(n_spans / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, max(3.0 * nrows, 4.5)), squeeze=False)
    fig.suptitle(
        f"{case_label}: $p_{{rgh}}(s)$ versus $q_{{dyn}}(s)$ by leg\n"
        "$q_{dyn}(s)=0.5\\rho_{bulk}(s)U_{bulk}(s)^2$",
        fontsize=14,
    )

    prgh_profiles = mean_profile_by_span(case_rows, "p_rgh_wall_area_avg_pa")
    qdyn_profiles = mean_profile_by_span(case_rows, "dynamic_pressure_pa")
    grouped_rows = rows_by_span_time(case_rows)

    for ax in axes.flat:
        ax.set_visible(False)

    for idx, span_name in enumerate(span_order):
        ax = axes.flat[idx]
        ax.set_visible(True)
        prgh_payload = prgh_profiles.get(span_name, [])
        qdyn_payload = qdyn_profiles.get(span_name, [])
        times = sorted({time_s for (span_key, time_s) in grouped_rows.keys() if span_key == span_name})

        for time_s in times:
            time_rows = sorted(grouped_rows[(span_name, time_s)], key=lambda item: int(item["bin_index"]))
            x_vals = [float(item["s_mid_m"]) for item in time_rows if math.isfinite(float(item["s_mid_m"]))]
            p_vals = [float(item["p_rgh_wall_area_avg_pa"]) for item in time_rows if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["p_rgh_wall_area_avg_pa"]))]
            q_vals = [float(item["dynamic_pressure_pa"]) for item in time_rows if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["dynamic_pressure_pa"]))]
            xp = [float(item["s_mid_m"]) for item in time_rows if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["p_rgh_wall_area_avg_pa"]))]
            xq = [float(item["s_mid_m"]) for item in time_rows if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["dynamic_pressure_pa"]))]
            if xp and p_vals:
                ax.plot(xp, p_vals, color="#88ccee", linewidth=0.8, alpha=0.35)
            if xq and q_vals:
                ax.plot(xq, q_vals, color="#ddcc77", linewidth=0.8, alpha=0.35)

        x_p = [float(item["s_mid_m"]) for item in prgh_payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["mean"]))]
        p_mean = [float(item["mean"]) for item in prgh_payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["mean"]))]
        p_min = [float(item["min"]) for item in prgh_payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["mean"]))]
        p_max = [float(item["max"]) for item in prgh_payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["mean"]))]
        x_q = [float(item["s_mid_m"]) for item in qdyn_payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["mean"]))]
        q_mean = [float(item["mean"]) for item in qdyn_payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["mean"]))]
        q_min = [float(item["min"]) for item in qdyn_payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["mean"]))]
        q_max = [float(item["max"]) for item in qdyn_payload if math.isfinite(float(item["s_mid_m"])) and math.isfinite(float(item["mean"]))]

        if x_p and p_mean:
            ax.plot(x_p, p_mean, color="#0077bb", linewidth=2.0, label="mean $p_{rgh}$")
            ax.fill_between(x_p, p_min, p_max, color="#88ccee", alpha=0.25)
        if x_q and q_mean:
            ax.plot(x_q, q_mean, color="#cc3311", linewidth=2.0, label="mean $q_{dyn}$")
            ax.fill_between(x_q, q_min, q_max, color="#ddcc77", alpha=0.25)

        ax.set_title(span_name)
        ax.set_xlabel("distance along leg, s [m]")
        ax.set_ylabel("pressure scale [Pa]")
        ax.legend(loc="best", fontsize=8)

    fig.text(
        0.5,
        0.01,
        "Faint lines: retained-time traces. Dark lines: retained-time means. Compare $p_{rgh}(s)$ for streamwise drop shape and $q_{dyn}(s)$ for kinetic scale.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    return save_matplotlib_figure(fig, output_dir, f"{source_id}_prgh_vs_dynamic_by_leg")


def build_readme(output_dir: Path, summary_rows: list[dict[str, Any]], missing_packages: list[str]) -> None:
    source_ids = sorted({str(row["source_id"]) for row in summary_rows})
    max_q = max((float(row["max_dynamic_pressure_pa"]) for row in summary_rows if math.isfinite(float(row["max_dynamic_pressure_pa"]))), default=math.nan)
    mean_abs_dp = np.mean(
        [abs(float(row["mean_delta_p_rgh_end_minus_start_pa"])) for row in summary_rows if math.isfinite(float(row["mean_delta_p_rgh_end_minus_start_pa"]))]
    ) if any(math.isfinite(float(row["mean_delta_p_rgh_end_minus_start_pa"])) for row in summary_rows) else math.nan
    lines = [
        "# Ethan p_rgh Versus Dynamic Pressure Profiles",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "## What These Curves Mean",
        "",
        "- `p_rgh(s)` is the hydrostatic-corrected pressure field reduced along each repaired leg.",
        "- `q_dyn(s) = 0.5 * rho_bulk(s) * U_bulk(s)^2` is the local kinetic pressure scale, not the pressure field itself.",
        "- Overlaying them does **not** mean they should match pointwise.",
        "- Instead:",
        "  - use `p_rgh(s)` to inspect streamwise pressure-drop shape and sign",
        "  - use `q_dyn(s)` to judge the size of local loss scales relative to the available velocity head",
        "",
        "## Developing-Flow Interpretation",
        "",
        "- In a fully developed straight segment, `p_rgh(s)` tends toward a more nearly linear streamwise drop and `q_dyn(s)` tends to vary more slowly with `s`.",
        "- In a developing segment, the wall shear and bulk-speed surrogate can still evolve with distance, so both the `p_rgh` slope and `q_dyn` level can move with `s`.",
        "- Bends, corners, transitions, and the test section can reset or disturb development; after those features, the downstream straight may show a redevelopment zone rather than an immediately settled friction trend.",
        "- That is why this package should be read together with the existing direct/shear friction and boundary-layer products rather than as a standalone loss model.",
        "",
        "## Scope",
        "",
        f"- cases processed: `{len(source_ids)}`",
        f"- maximum reported dynamic pressure: `{max_q:.3f} Pa`" if math.isfinite(max_q) else "- maximum reported dynamic pressure: `nan`",
        f"- mean absolute retained-time end-to-start `p_rgh` change by span: `{mean_abs_dp:.3f} Pa`" if math.isfinite(mean_abs_dp) else "- mean absolute retained-time end-to-start `p_rgh` change by span: `nan`",
        "",
        "## Primary Artifacts",
        "",
        "- `prgh_vs_dynamic_profile_rows.csv`",
        "- `prgh_vs_dynamic_profile_summary.csv`",
        "- `figure_index.csv`",
        "- `summary.json`",
        "- `figures/png/*_prgh_vs_dynamic_by_leg.png` plus matching `svg` / `pdf`",
        "",
        "## Major / Minor Loss Context",
        "",
        "- The straight-leg major-loss path is already much more mature than the corner/bend minor-loss path.",
        "- Major-loss interpretation uses the preserved streamwise `p_rgh` gradients, direct/shear Darcy comparisons, and boundary-layer context on repaired major spans.",
        "- Minor-loss interpretation at bends and corners is still a defended patch-endpoint decomposition plus adjacent-straight reference, not a continuous feature-volume field integral.",
    ]
    if missing_packages:
        lines.extend(
            [
                "",
                "## Missing package roots",
                "",
                *[f"- `{source_id}`" for source_id in sorted(missing_packages)],
            ]
        )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    package_index_path = Path(args.package_index)
    output_dir = ensure_dir(Path(args.output_dir))
    package_rows = load_csv_rows(package_index_path)
    profile_rows, missing_packages = build_profile_rows(package_rows)
    if not profile_rows:
        raise SystemExit("No p_rgh/dynamic-pressure rows were built from the package index.")

    fieldnames = [
        "source_id",
        "case_label",
        "family",
        "profile_name",
        "package_dir",
        "time_s",
        "span_name",
        "span_kind",
        "bin_index",
        "s_start_m",
        "s_end_m",
        "s_mid_m",
        "p_wall_area_avg_pa",
        "p_rgh_wall_area_avg_pa",
        "hydro_proxy_p_minus_prgh_pa",
        "rho_bulk_kg_m3",
        "bulk_velocity_m_s",
        "dynamic_pressure_pa",
        "dp_major_gradient_direct_prgh_pa_per_m",
        "darcy_f_pressure_drop_prgh",
    ]
    csv_dump(output_dir / "prgh_vs_dynamic_profile_rows.csv", fieldnames, profile_rows)

    summary_rows = summarize_profiles(profile_rows)
    csv_dump(
        output_dir / "prgh_vs_dynamic_profile_summary.csv",
        [
            "source_id",
            "case_label",
            "family",
            "span_name",
            "time_sample_count",
            "bin_row_count",
            "mean_dynamic_pressure_pa",
            "max_dynamic_pressure_pa",
            "mean_p_rgh_pa",
            "min_p_rgh_pa",
            "max_p_rgh_pa",
            "mean_delta_p_rgh_end_minus_start_pa",
            "mean_hydro_proxy_p_minus_prgh_pa",
            "mean_q_dyn_vs_abs_delta_p_rgh_ratio",
        ],
        summary_rows,
    )

    figure_rows: list[dict[str, Any]] = []
    rows_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in profile_rows:
        rows_by_case[str(row["source_id"])].append(row)
    for source_id, case_rows in sorted(rows_by_case.items()):
        figure_paths = plot_case(case_rows, output_dir)
        figure_rows.append(
            {
                "source_id": source_id,
                "case_label": case_rows[0]["case_label"],
                "family": case_rows[0]["family"],
                **figure_paths,
            }
        )
    csv_dump(output_dir / "figure_index.csv", ["source_id", "case_label", "family", "png", "svg", "pdf"], figure_rows)

    summary_payload = {
        "generated_at": iso_timestamp(),
        "package_index": str(package_index_path),
        "case_count": len(rows_by_case),
        "family_count": len({str(row["family"]) for row in profile_rows}),
        "row_count": len(profile_rows),
        "figure_count": len(figure_rows),
        "missing_packages": sorted(missing_packages),
        "dynamic_pressure_definition": "0.5 * rho_bulk_kg_m3 * bulk_velocity_m_s^2",
        "pressure_definition_note": "p_rgh is hydrostatic-corrected pressure; it is not dynamic pressure.",
        "developing_flow_note": (
            "Use p_rgh(s) for streamwise loss shape and q_dyn(s) for kinetic scale. "
            "Developing or redeveloping flow can make both vary materially with s."
        ),
    }
    json_dump(output_dir / "summary.json", summary_payload)
    build_readme(output_dir, summary_rows, missing_packages)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
