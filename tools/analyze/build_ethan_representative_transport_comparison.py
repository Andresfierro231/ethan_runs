#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
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

from tools.common import csv_dump, ensure_dir, iso_timestamp, save_matplotlib_figure, safe_float  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-15_ethan_representative_transport_comparison"
DEFAULT_CASE_ORDER = (
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh",
)
CASE_STYLE = {
    "val_salt_test_2_coarse_mesh_laminar": ("Salt 2 val", "#1f1f1f"),
    "viscosity_screening_salt_test_2_jin_coarse_mesh": ("Salt 2 Jin", "#0b6e4f"),
    "viscosity_screening_salt_test_2_kirst_coarse_mesh": ("Salt 2 Kirst", "#bc3908"),
}

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a representative Salt 2 transport comparison package from finished "
            "per-case case-analysis packages."
        )
    )
    parser.add_argument(
        "--package-dir",
        action="append",
        required=True,
        help="Per-case package directory containing summary.json and the exported CSVs. Repeat exactly three times.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_transport_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "time_s": float(row["time_s"]),
                "span_name": str(row["span_name"]),
                "s_mid_m": float(row["s_mid_m"]),
                "darcy_f_shear": safe_float(row.get("darcy_f_shear"), math.nan),
                "darcy_f_pressure_drop_prgh": safe_float(row.get("darcy_f_pressure_drop_prgh"), math.nan),
                "dp_major_gradient_direct_prgh_pa_per_m": safe_float(
                    row.get("dp_major_gradient_direct_prgh_pa_per_m"),
                    math.nan,
                ),
                "effective_htc_w_m2_k": safe_float(row.get("effective_htc_w_m2_k"), math.nan),
                "effective_ua_per_m_w_m_k": safe_float(row.get("effective_ua_per_m_w_m_k"), math.nan),
                "effective_thermal_resistance_k_m_w": safe_float(
                    row.get("effective_thermal_resistance_k_m_w"),
                    math.nan,
                ),
                "momentum_resistance_direct_prgh_pa_s_kg_m": safe_float(
                    row.get("momentum_resistance_direct_prgh_pa_s_kg_m"),
                    math.nan,
                ),
            }
        )
    return rows


def load_boundary_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "time_s": float(row["time_s"]),
                "span_name": str(row["span_name"]),
                "landmark_name": str(row["landmark_name"]),
                "landmark_label": str(row["landmark_label"]),
                "landmark_role": str(row["landmark_role"]),
                "s_landmark_m": safe_float(row.get("s_landmark_m"), math.nan),
                "delta99_u_m": safe_float(row.get("delta99_u_m"), math.nan),
                "delta99_t_m": safe_float(row.get("delta99_t_m"), math.nan),
                "shape_factor_u": safe_float(row.get("shape_factor_u"), math.nan),
                "profile_status": str(row.get("profile_status", "")),
            }
        )
    return rows


def load_branch_thermal_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "branch_name": str(row["branch_name"]),
                "branch_type": str(row["branch_type"]),
                "component_spans": str(row["component_spans"]),
                "component_span_count": int(row["component_span_count"]),
                "branch_total_length_m": safe_float(row.get("branch_total_length_m"), math.nan),
                "usable_row_count": int(row["usable_row_count"]),
                "masked_row_count": int(row["masked_row_count"]),
                "usable_fraction": (
                    float(int(row["usable_row_count"]) / max(int(row["total_row_count"]), 1))
                    if row.get("total_row_count")
                    else math.nan
                ),
                "thermal_warning_fraction": safe_float(row.get("thermal_warning_fraction"), math.nan),
                "mean_bulk_temp_fluid_area_avg_k": safe_float(row.get("mean_bulk_temp_fluid_area_avg_k"), math.nan),
                "mean_abs_bulk_minus_wall_temp_k": safe_float(row.get("mean_abs_bulk_minus_wall_temp_k"), math.nan),
                "min_abs_bulk_minus_wall_temp_k": safe_float(row.get("min_abs_bulk_minus_wall_temp_k"), math.nan),
                "mean_bulk_positive_mass_flux_kg_s": safe_float(row.get("mean_bulk_positive_mass_flux_kg_s"), math.nan),
                "mean_effective_htc_w_m2_k": safe_float(row.get("mean_effective_htc_w_m2_k"), math.nan),
                "mean_effective_ua_per_m_w_m_k": safe_float(row.get("mean_effective_ua_per_m_w_m_k"), math.nan),
                "mean_effective_thermal_resistance_k_m_w": safe_float(
                    row.get("mean_effective_thermal_resistance_k_m_w"),
                    math.nan,
                ),
            }
        )
    return rows


def span_lengths_from_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    lengths: dict[str, float] = {}
    for row in rows:
        span_name = str(row["span_name"])
        lengths[span_name] = max(lengths.get(span_name, 0.0), float(row["s_mid_m"]))
    return lengths


def build_loop_offsets(span_order: list[str], span_lengths: dict[str, float]) -> dict[str, float]:
    offsets: dict[str, float] = {}
    cursor = 0.0
    for span_name in span_order:
        offsets[span_name] = cursor
        cursor += float(span_lengths.get(span_name, 0.0))
    return offsets


def case_label(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#444"))[0]


def case_color(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#444"))[1]


def sort_key(source_id: str) -> int:
    try:
        return DEFAULT_CASE_ORDER.index(source_id)
    except ValueError:
        return len(DEFAULT_CASE_ORDER)


def nanmean(values: list[float]) -> float:
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not finite:
        return math.nan
    return float(np.mean(np.array(finite, dtype=float)))


def build_mean_transport_rows(
    source_id: str,
    rows: list[dict[str, Any]],
    offsets: dict[str, float],
    total_length: float,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["span_name"]), float(row["s_mid_m"]))].append(row)
    output_rows: list[dict[str, Any]] = []
    for (span_name, s_mid_m), payload in sorted(grouped.items(), key=lambda item: (sort_key(source_id), item[0][0], item[0][1])):
        loop_s = float(offsets.get(span_name, 0.0) + s_mid_m)
        output_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label(source_id),
                "span_name": span_name,
                "s_mid_m": s_mid_m,
                "loop_s_m": loop_s,
                "loop_s_fraction": float(loop_s / max(total_length, 1.0e-12)),
                "mean_darcy_f_shear": nanmean([row["darcy_f_shear"] for row in payload]),
                "mean_darcy_f_pressure_drop_prgh": nanmean(
                    [row["darcy_f_pressure_drop_prgh"] for row in payload]
                ),
                "mean_dp_major_gradient_direct_prgh_pa_per_m": nanmean(
                    [row["dp_major_gradient_direct_prgh_pa_per_m"] for row in payload]
                ),
                "mean_effective_htc_w_m2_k": nanmean([row["effective_htc_w_m2_k"] for row in payload]),
                "mean_effective_ua_per_m_w_m_k": nanmean([row["effective_ua_per_m_w_m_k"] for row in payload]),
                "mean_effective_thermal_resistance_k_m_w": nanmean(
                    [row["effective_thermal_resistance_k_m_w"] for row in payload]
                ),
                "mean_momentum_resistance_direct_prgh_pa_s_kg_m": nanmean(
                    [row["momentum_resistance_direct_prgh_pa_s_kg_m"] for row in payload]
                ),
            }
        )
    return output_rows


def build_mean_boundary_rows(
    source_id: str,
    rows: list[dict[str, Any]],
    offsets: dict[str, float],
    total_length: float,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["span_name"]), str(row["landmark_name"]))].append(row)
    output_rows: list[dict[str, Any]] = []
    for (span_name, landmark_name), payload in sorted(grouped.items()):
        first = payload[0]
        s_landmark_m = safe_float(first.get("s_landmark_m"), math.nan)
        loop_s = float(offsets.get(span_name, 0.0) + (s_landmark_m if math.isfinite(s_landmark_m) else 0.0))
        output_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label(source_id),
                "span_name": span_name,
                "landmark_name": landmark_name,
                "landmark_label": str(first["landmark_label"]),
                "landmark_role": str(first["landmark_role"]),
                "s_landmark_m": s_landmark_m,
                "loop_s_m": loop_s,
                "loop_s_fraction": float(loop_s / max(total_length, 1.0e-12)),
                "usable_profile_count": sum(1 for row in payload if row["profile_status"] == "usable"),
                "mean_delta99_u_m": nanmean([row["delta99_u_m"] for row in payload]),
                "mean_delta99_t_m": nanmean([row["delta99_t_m"] for row in payload]),
                "mean_shape_factor_u": nanmean([row["shape_factor_u"] for row in payload]),
            }
        )
    return output_rows


def plot_friction_and_pressure(output_dir: Path, rows: list[dict[str, Any]]) -> dict[str, str]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["source_id"])].append(row)

    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    for source_id in sorted(grouped, key=sort_key):
        payload = sorted(grouped[source_id], key=lambda row: float(row["loop_s_m"]))
        x = [float(row["loop_s_m"]) for row in payload]
        axes[0].plot(
            x,
            [float(row["mean_darcy_f_shear"]) for row in payload],
            color=case_color(source_id),
            linewidth=1.8,
            linestyle="--",
            label=f"{case_label(source_id)} shear",
        )
        axes[0].plot(
            x,
            [float(row["mean_darcy_f_pressure_drop_prgh"]) for row in payload],
            color=case_color(source_id),
            linewidth=1.8,
            label=f"{case_label(source_id)} direct",
        )
        axes[1].plot(
            x,
            [float(row["mean_dp_major_gradient_direct_prgh_pa_per_m"]) for row in payload],
            color=case_color(source_id),
            linewidth=1.8,
            label=case_label(source_id),
        )
    axes[0].set_ylabel("Darcy f")
    axes[0].set_title("Representative Salt 2 friction comparison")
    axes[0].legend(loc="best", ncol=2)
    axes[1].set_ylabel("Direct dp/ds [Pa/m]")
    axes[1].set_xlabel("Distance along loop [m]")
    axes[1].set_title("Representative Salt 2 direct pressure-gradient comparison")
    axes[1].legend(loc="best")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "representative_friction_and_pressure", dpi=220)
    plt.close(fig)
    return paths


def plot_thermal_and_resistance(output_dir: Path, rows: list[dict[str, Any]]) -> dict[str, str]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["source_id"])].append(row)

    fig, axes = plt.subplots(3, 1, figsize=(14, 11), sharex=True)
    for source_id in sorted(grouped, key=sort_key):
        payload = sorted(grouped[source_id], key=lambda row: float(row["loop_s_m"]))
        x = [float(row["loop_s_m"]) for row in payload]
        axes[0].plot(x, [float(row["mean_effective_htc_w_m2_k"]) for row in payload], color=case_color(source_id), linewidth=1.8, label=case_label(source_id))
        axes[1].plot(x, [float(row["mean_effective_thermal_resistance_k_m_w"]) for row in payload], color=case_color(source_id), linewidth=1.8, label=case_label(source_id))
        axes[2].plot(x, [float(row["mean_momentum_resistance_direct_prgh_pa_s_kg_m"]) for row in payload], color=case_color(source_id), linewidth=1.8, label=case_label(source_id))
    axes[0].set_ylabel("Effective HTC [W/m^2/K]")
    axes[0].set_title("Representative Salt 2 effective HTC comparison")
    axes[0].legend(loc="best")
    axes[1].set_ylabel("Effective R_th' [K m / W]")
    axes[1].set_title("Representative Salt 2 thermal resistance comparison")
    axes[1].legend(loc="best")
    axes[2].set_ylabel("Momentum R' [Pa s / kg / m]")
    axes[2].set_xlabel("Distance along loop [m]")
    axes[2].set_title("Representative Salt 2 momentum-resistance proxy comparison")
    axes[2].legend(loc="best")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "representative_thermal_and_resistance", dpi=220)
    plt.close(fig)
    return paths


def plot_boundary_landmarks(output_dir: Path, rows: list[dict[str, Any]]) -> dict[str, str]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["source_id"])].append(row)

    fig, axes = plt.subplots(3, 1, figsize=(14, 11), sharex=True)
    for source_id in sorted(grouped, key=sort_key):
        payload = sorted(grouped[source_id], key=lambda row: float(row["loop_s_m"]))
        x = [float(row["loop_s_m"]) for row in payload]
        axes[0].plot(x, [float(row["mean_delta99_u_m"]) for row in payload], color=case_color(source_id), linewidth=1.5, marker="o", markersize=4, label=case_label(source_id))
        axes[1].plot(x, [float(row["mean_delta99_t_m"]) for row in payload], color=case_color(source_id), linewidth=1.5, marker="o", markersize=4, label=case_label(source_id))
        axes[2].plot(x, [float(row["mean_shape_factor_u"]) for row in payload], color=case_color(source_id), linewidth=1.5, marker="o", markersize=4, label=case_label(source_id))
    axes[0].set_ylabel("delta99,u [m]")
    axes[0].set_title("Boundary-layer landmark momentum thickness proxy")
    axes[0].legend(loc="best")
    axes[1].set_ylabel("delta99,t [m]")
    axes[1].set_title("Boundary-layer landmark thermal thickness proxy")
    axes[1].legend(loc="best")
    axes[2].set_ylabel("H12 [-]")
    axes[2].set_xlabel("Distance along loop [m]")
    axes[2].set_title("Boundary-layer landmark shape-factor comparison")
    axes[2].legend(loc="best")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "representative_boundary_landmarks", dpi=220)
    plt.close(fig)
    return paths


def plot_branch_thermal_summary(output_dir: Path, rows: list[dict[str, Any]]) -> dict[str, str]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["source_id"])].append(row)
    branch_names = sorted(
        {str(row["branch_name"]) for row in rows},
        key=lambda name: (name != "upcomer", name),
    )
    x = np.arange(len(branch_names), dtype=float)
    fig, axes = plt.subplots(4, 1, figsize=(15, 13), sharex=True)
    width = 0.75 / max(len(grouped), 1)
    panel_specs = [
        ("mean_bulk_temp_fluid_area_avg_k", "Mean bulk T [K]", "Representative Salt 2 branch bulk temperature comparison"),
        ("mean_effective_htc_w_m2_k", "Mean HTC [W/m^2/K]", "Representative Salt 2 branch effective HTC comparison"),
        ("mean_effective_ua_per_m_w_m_k", "Mean UA' [W/m/K]", "Representative Salt 2 branch effective UA' comparison"),
        ("mean_effective_thermal_resistance_k_m_w", "Mean R_th' [K m / W]", "Representative Salt 2 branch effective thermal resistance comparison"),
    ]
    branch_lookup = {(str(row["source_id"]), str(row["branch_name"])): row for row in rows}
    for series_index, source_id in enumerate(sorted(grouped, key=sort_key)):
        offset = (series_index - (len(grouped) - 1) / 2.0) * width
        for axis, (field_name, ylabel, title) in zip(axes, panel_specs):
            values = [
                float(branch_lookup[(source_id, branch_name)].get(field_name, math.nan))
                if (source_id, branch_name) in branch_lookup
                else math.nan
                for branch_name in branch_names
            ]
            axis.bar(
                x + offset,
                values,
                width=width,
                color=case_color(source_id),
                label=case_label(source_id) if axis is axes[0] else None,
            )
            axis.set_ylabel(ylabel)
            axis.set_title(title)
    axes[0].legend(loc="best")
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([name.replace("_", "\n") for name in branch_names])
    axes[-1].set_xlabel("Branch")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "representative_branch_thermal_summary", dpi=220)
    plt.close(fig)
    return paths


def write_readme(output_dir: Path, packages: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    lines = [
        "# Representative Salt 2 Transport Comparison",
        "",
        "## Scope",
        "",
        "This package compares the corrected field-reconstructed Salt 2 trio:",
    ]
    for payload in packages:
        package_summary = payload["summary"]
        source_id = str(payload["source_id"])
        requested_times = package_summary.get("requested_times_s", [])
        lines.append(f"- `{source_id}` on retained times `{requested_times}`")
    lines.extend(
        [
            "",
            "## Method",
            "",
            "- `major_loss_cumulative_timeseries.csv` is reduced into loopwise mean streamwise friction, direct pressure-gradient, effective HTC, thermal resistance, and momentum-resistance proxy curves.",
            "- `boundary_layer_landmark_summary.csv` is reduced into representative landmark comparisons for `delta99_u`, `delta99_t`, and `H12`.",
            "- `branch_thermal_summary.csv` is reduced into branch-local bulk-temperature and effective thermal comparison tables for the six repaired sections plus the derived `upcomer` branch.",
            "- Loopwise alignment follows the per-case `loop_span_order` carried by the Salt-family case-analysis package.",
            "",
            "## Assumptions And Limits",
            "",
            "- Effective thermal metrics are the primary thermal comparison outputs. They inherit the package masking and thermal sanitization rules from the per-case builder.",
            "- Boundary-layer rows are first-pass wall-to-centerline landmark samples, not a full circumferential or full-span closure model.",
            "- Branch thermal rows reuse validated span bins. The derived `upcomer` branch concatenates `left_lower_leg`, `test_section_span`, and `left_upper_leg` while intentionally skipping corners and junctions.",
            "- The validation case in this corrected trio may be on a later continuation-era retained window than older June 10 validation products; use the package `requested_times_s` values above when citing provenance.",
            "- Any package row filtered out upstream by QC remains absent here; this comparison builder does not backfill missing transport data.",
            "",
            "## Artifacts",
            "",
            f"- `representative_transport_profiles.csv`: `{summary['representative_transport_profiles_csv']}`",
            f"- `representative_boundary_layer_landmarks.csv`: `{summary['representative_boundary_layer_landmarks_csv']}`",
            f"- `representative_branch_thermal_summary.csv`: `{summary['representative_branch_thermal_summary_csv']}`",
            "- `figures/`: friction/pressure, thermal/resistance, boundary-landmark, and branch-thermal overlays",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    package_dirs = [Path(item).resolve() for item in args.package_dir]
    output_dir = ensure_dir(Path(args.output_dir))
    packages: list[dict[str, Any]] = []
    for package_dir in package_dirs:
        summary_path = package_dir / "summary.json"
        if not summary_path.exists():
            raise RuntimeError(f"Missing summary.json under {package_dir}")
        summary = load_json(summary_path)
        source_id = str(summary["source_id"])
        transport_rows = load_transport_rows(package_dir / "major_loss_cumulative_timeseries.csv")
        boundary_rows = load_boundary_rows(package_dir / "boundary_layer_landmark_summary.csv")
        branch_thermal_rows = load_branch_thermal_rows(package_dir / "branch_thermal_summary.csv")
        if not transport_rows:
            raise RuntimeError(f"Missing transport rows under {package_dir}")
        if not boundary_rows:
            raise RuntimeError(f"Missing boundary-layer landmark rows under {package_dir}")
        if not branch_thermal_rows:
            raise RuntimeError(f"Missing branch-thermal rows under {package_dir}")
        packages.append(
            {
                "package_dir": str(package_dir),
                "summary": summary,
                "source_id": source_id,
                "transport_rows": transport_rows,
                "boundary_rows": boundary_rows,
                "branch_thermal_rows": branch_thermal_rows,
            }
        )

    packages.sort(key=lambda payload: sort_key(str(payload["source_id"])))
    loop_span_order = list(packages[0]["summary"]["major_loss"]["loop_span_order"])
    span_lengths = span_lengths_from_rows(packages[0]["transport_rows"])
    offsets = build_loop_offsets(loop_span_order, span_lengths)
    total_length = sum(float(span_lengths.get(span_name, 0.0)) for span_name in loop_span_order)

    mean_transport_rows: list[dict[str, Any]] = []
    mean_boundary_rows: list[dict[str, Any]] = []
    representative_branch_rows: list[dict[str, Any]] = []
    for payload in packages:
        source_id = str(payload["source_id"])
        mean_transport_rows.extend(
            build_mean_transport_rows(source_id, payload["transport_rows"], offsets, total_length)
        )
        mean_boundary_rows.extend(
            build_mean_boundary_rows(source_id, payload["boundary_rows"], offsets, total_length)
        )
        for row in payload["branch_thermal_rows"]:
            representative_branch_rows.append(
                {
                    **row,
                    "source_id": source_id,
                    "case_label": case_label(source_id),
                }
            )

    csv_dump(
        output_dir / "representative_transport_profiles.csv",
        list(mean_transport_rows[0].keys()),
        mean_transport_rows,
    )
    csv_dump(
        output_dir / "representative_boundary_layer_landmarks.csv",
        list(mean_boundary_rows[0].keys()),
        mean_boundary_rows,
    )
    csv_dump(
        output_dir / "representative_branch_thermal_summary.csv",
        list(representative_branch_rows[0].keys()),
        representative_branch_rows,
    )

    friction_paths = plot_friction_and_pressure(output_dir, mean_transport_rows)
    thermal_paths = plot_thermal_and_resistance(output_dir, mean_transport_rows)
    boundary_paths = plot_boundary_landmarks(output_dir, mean_boundary_rows)
    branch_paths = plot_branch_thermal_summary(output_dir, representative_branch_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "case_ids": [str(payload["source_id"]) for payload in packages],
        "package_dirs": [str(payload["package_dir"]) for payload in packages],
        "loop_span_order": loop_span_order,
        "representative_transport_profiles_csv": str((output_dir / "representative_transport_profiles.csv").resolve()),
        "representative_boundary_layer_landmarks_csv": str((output_dir / "representative_boundary_layer_landmarks.csv").resolve()),
        "representative_branch_thermal_summary_csv": str((output_dir / "representative_branch_thermal_summary.csv").resolve()),
        "figure_paths": {
            "friction_and_pressure": friction_paths,
            "thermal_and_resistance": thermal_paths,
            "boundary_landmarks": boundary_paths,
            "branch_thermal_summary": branch_paths,
        },
    }
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_readme(output_dir, packages, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
