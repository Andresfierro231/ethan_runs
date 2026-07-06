#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from collections import Counter, defaultdict
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
from tools.common import ensure_dir, iso_timestamp, save_matplotlib_figure, safe_float  # noqa: E402
from tools.analyze.ethan_closure_modeling_v3_common import csv_dump_rows, write_json  # noqa: E402

DEFAULT_PACKAGE_INDEX = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package" / "package_index.csv"
FEATURE_DIR = ROOT / "reports" / "2026-06-22_ethan_feature_path_hydro_decomposition"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-23_ethan_salt_redevelopment_followon"
DEFAULT_IMPORT_PATH = ROOT / "imports" / "2026-06-23_ethan_salt_redevelopment_followon.json"

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Salt redevelopment follow-on package that overlays retained-time "
            "p_rgh(s), q_dyn(s), and streamwise wall heat loss by leg, then anchors the "
            "straight-leg picture against the retained feature-path hydro decomposition."
        )
    )
    parser.add_argument("--package-index", default=str(DEFAULT_PACKAGE_INDEX))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--import-manifest-path", default=str(DEFAULT_IMPORT_PATH))
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


def load_salt_package_rows(package_index_path: Path) -> list[dict[str, str]]:
    rows = load_csv_rows(package_index_path)
    return [row for row in rows if str(row.get("family", "")).strip().lower() == "salt"]


def build_profile_rows(package_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for package_row in package_rows:
        package_dir = Path(package_row["package_dir"])
        major_path = package_dir / "major_loss_cumulative_timeseries.csv"
        if not major_path.exists():
            continue
        for row in load_csv_rows(major_path):
            output_rows.append(
                {
                    "source_id": package_row["source_id"],
                    "case_label": package_row["case_label"],
                    "profile_name": package_row["profile_name"],
                    "package_dir": package_row["package_dir"],
                    "time_s": finite_float(row.get("time_s")),
                    "span_name": row.get("span_name", ""),
                    "span_kind": row.get("span_kind", ""),
                    "bin_index": int(float(row["bin_index"])),
                    "s_mid_m": finite_float(row.get("s_mid_m")),
                    "p_rgh_wall_area_avg_pa": finite_float(row.get("p_rgh_wall_area_avg_pa")),
                    "dynamic_pressure_pa": dynamic_pressure_pa(row),
                    "wall_heat_per_length_w_m": finite_float(row.get("wall_heat_per_length_w_m")),
                    "effective_ua_per_m_w_m_k": finite_float(row.get("effective_ua_per_m_w_m_k")),
                    "dp_major_gradient_pa_per_m": finite_float(row.get("dp_major_gradient_pa_per_m")),
                    "dp_major_gradient_direct_prgh_pa_per_m": finite_float(row.get("dp_major_gradient_direct_prgh_pa_per_m")),
                    "darcy_f": finite_float(row.get("darcy_f")),
                    "darcy_f_pressure_drop_prgh": finite_float(row.get("darcy_f_pressure_drop_prgh")),
                }
            )
    return output_rows


def mean_profile_by_span(rows: list[dict[str, Any]], value_key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row["span_name"])][int(row["bin_index"])].append(row)

    output: dict[str, list[dict[str, Any]]] = {}
    for span_name, by_bin in grouped.items():
        payload: list[dict[str, Any]] = []
        for bin_index, bin_rows in sorted(by_bin.items()):
            values = [float(item[value_key]) for item in bin_rows if math.isfinite(float(item[value_key]))]
            s_vals = [float(item["s_mid_m"]) for item in bin_rows if math.isfinite(float(item["s_mid_m"]))]
            payload.append(
                {
                    "bin_index": bin_index,
                    "s_mid_m": float(np.mean(s_vals)) if s_vals else math.nan,
                    "mean": float(np.mean(values)) if values else math.nan,
                }
            )
        output[span_name] = payload
    return output


def summarize_span_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["source_id"]), str(row["span_name"]))].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (source_id, span_name), payload in sorted(grouped.items()):
        case_label = str(payload[0]["case_label"])
        by_time: dict[float, list[dict[str, Any]]] = defaultdict(list)
        for row in payload:
            time_s = float(row["time_s"])
            if math.isfinite(time_s):
                by_time[time_s].append(row)

        delta_p_values: list[float] = []
        direct_over_shear_values: list[float] = []
        for time_rows in by_time.values():
            ordered = sorted(time_rows, key=lambda item: int(item["bin_index"]))
            start = next((item for item in ordered if math.isfinite(float(item["p_rgh_wall_area_avg_pa"]))), None)
            end = next((item for item in reversed(ordered) if math.isfinite(float(item["p_rgh_wall_area_avg_pa"]))), None)
            if start and end:
                delta_p_values.append(float(end["p_rgh_wall_area_avg_pa"]) - float(start["p_rgh_wall_area_avg_pa"]))
            for item in ordered:
                shear = float(item["dp_major_gradient_pa_per_m"])
                direct = float(item["dp_major_gradient_direct_prgh_pa_per_m"])
                if math.isfinite(shear) and math.isfinite(direct) and abs(shear) > 1.0e-12:
                    direct_over_shear_values.append(direct / shear)

        wall_heat_values = [float(item["wall_heat_per_length_w_m"]) for item in payload if math.isfinite(float(item["wall_heat_per_length_w_m"]))]
        qdyn_values = [float(item["dynamic_pressure_pa"]) for item in payload if math.isfinite(float(item["dynamic_pressure_pa"]))]
        summary_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label,
                "span_name": span_name,
                "time_sample_count": len(by_time),
                "bin_row_count": len(payload),
                "mean_delta_p_rgh_end_minus_start_pa": float(np.mean(delta_p_values)) if delta_p_values else math.nan,
                "mean_dynamic_pressure_pa": float(np.mean(qdyn_values)) if qdyn_values else math.nan,
                "mean_wall_heat_per_length_w_m": float(np.mean(wall_heat_values)) if wall_heat_values else math.nan,
                "mean_abs_wall_heat_per_length_w_m": float(np.mean(np.abs(wall_heat_values))) if wall_heat_values else math.nan,
                "mean_direct_over_shear_gradient_ratio": (
                    float(np.mean(direct_over_shear_values)) if direct_over_shear_values else math.nan
                ),
            }
        )
    return summary_rows


def summarize_feature_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    case_rows = load_csv_rows(FEATURE_DIR / "feature_path_case_summary.csv")
    class_grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    reason_counter: Counter[str] = Counter()
    for row in case_rows:
        class_grouped[str(row["feature_class"])].append(row)
        reason_counter[str(row.get("exclusion_reason_primary", "")).strip() or "none"] += 1

    class_rows: list[dict[str, Any]] = []
    for feature_class, payload in sorted(class_grouped.items()):
        fit_rows = [row for row in payload if str(row.get("fit_use_status", "")) == "fit_used"]
        mean_excess = [finite_float(row.get("mean_feature_excess_path_pa")) for row in fit_rows]
        mean_excess = [value for value in mean_excess if math.isfinite(value)]
        mean_keff = [finite_float(row.get("mean_keff_effective_path")) for row in fit_rows]
        mean_keff = [value for value in mean_keff if math.isfinite(value)]
        class_rows.append(
            {
                "feature_class": feature_class,
                "case_row_count": len(payload),
                "fit_used_case_count": len(fit_rows),
                "excluded_case_count": len(payload) - len(fit_rows),
                "mean_fit_feature_excess_path_pa": float(np.mean(mean_excess)) if mean_excess else math.nan,
                "mean_fit_keff_effective_path": float(np.mean(mean_keff)) if mean_keff else math.nan,
            }
        )

    reason_rows = [
        {"exclusion_reason_primary": key, "case_row_count": value}
        for key, value in sorted(reason_counter.items(), key=lambda item: (-item[1], item[0]))
    ]
    return class_rows, reason_rows


def plot_case(case_rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    source_id = str(case_rows[0]["source_id"])
    case_label = str(case_rows[0]["case_label"])
    profile = get_case_analysis_profile(source_id)
    span_order = [name for name in profile.major_spans.keys() if any(str(row["span_name"]) == name for row in case_rows)]
    if not span_order:
        span_order = sorted({str(row["span_name"]) for row in case_rows})

    prgh_profiles = mean_profile_by_span(case_rows, "p_rgh_wall_area_avg_pa")
    qdyn_profiles = mean_profile_by_span(case_rows, "dynamic_pressure_pa")
    qprime_profiles = mean_profile_by_span(case_rows, "wall_heat_per_length_w_m")

    fig, axes = plt.subplots(len(span_order), 2, figsize=(13.5, max(3.2 * len(span_order), 6.0)), squeeze=False)
    fig.suptitle(
        f"{case_label}: retained straight-leg redevelopment follow-on\n"
        "$p_{rgh}(s)$ with $q_{dyn}(s)=0.5\\rho U^2$ and streamwise wall heat loss $q'(s)$",
        fontsize=14,
    )

    for row_index, span_name in enumerate(span_order):
        left_axis = axes[row_index][0]
        right_axis = axes[row_index][1]
        prgh_payload = prgh_profiles.get(span_name, [])
        qdyn_payload = qdyn_profiles.get(span_name, [])
        qprime_payload = qprime_profiles.get(span_name, [])

        x_prgh = [item["s_mid_m"] for item in prgh_payload]
        y_prgh = [item["mean"] for item in prgh_payload]
        x_qdyn = [item["s_mid_m"] for item in qdyn_payload]
        y_qdyn = [item["mean"] for item in qdyn_payload]
        x_qprime = [item["s_mid_m"] for item in qprime_payload]
        y_qprime = [item["mean"] for item in qprime_payload]

        left_axis.plot(x_prgh, y_prgh, color="#1f77b4", linewidth=2.0)
        left_axis.set_ylabel("mean $p_{rgh}$ [Pa]", color="#1f77b4")
        left_axis.tick_params(axis="y", labelcolor="#1f77b4")
        twin_axis = left_axis.twinx()
        twin_axis.plot(x_qdyn, y_qdyn, color="#ff7f0e", linewidth=1.8, linestyle="--")
        twin_axis.set_ylabel("mean $q_{dyn}$ [Pa]", color="#ff7f0e")
        twin_axis.tick_params(axis="y", labelcolor="#ff7f0e")
        left_axis.set_title(span_name)
        left_axis.set_xlabel("s [m]")

        right_axis.axhline(0.0, color="0.35", linewidth=0.8)
        right_axis.plot(x_qprime, y_qprime, color="#2ca02c", linewidth=2.0)
        right_axis.set_title(f"{span_name}: wall heat loss")
        right_axis.set_xlabel("s [m]")
        right_axis.set_ylabel("mean $q'(s)$ [W/m]")

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    return save_matplotlib_figure(fig, output_dir, f"{source_id}_redevelopment_followon")


def build_readme(
    *,
    case_count: int,
    span_summary_rows: list[dict[str, Any]],
    feature_class_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
) -> str:
    fit_ready = sum(int(row["fit_used_case_count"]) for row in feature_class_rows)
    feature_total = sum(int(row["case_row_count"]) for row in feature_class_rows)
    top_exclusion = exclusion_rows[0] if exclusion_rows else {"exclusion_reason_primary": "none", "case_row_count": 0}
    return f"""# Ethan Salt Redevelopment Follow-On

Generated: `{iso_timestamp()}`

## Scope

- This package keeps the straight-leg story and the bends/corners story separate but adjacent.
- Straight-leg outputs come from preserved `major_loss_cumulative_timeseries.csv` rows for all Salt cases.
- Minor-loss outputs are reused from the June 22 endpoint-path feature decomposition, which already defends patch-endpoint `p_rgh` and `p-p_rgh` across the preserved feature boundaries.

## Current evidence state

- Salt cases plotted here: `{case_count}`.
- Straight-leg span summaries published here: `{len(span_summary_rows)}`.
- Feature-path case rows available from the retained endpoint-path package: `{feature_total}`.
- Feature-path fit-ready rows currently available: `{fit_ready}`.
- Largest current feature exclusion bucket: `{top_exclusion['exclusion_reason_primary']}` with `{top_exclusion['case_row_count']}` rows.

## Interpretation boundary

- `p_rgh(s)` is hydrostatic-corrected pressure, so it tracks the non-hydrostatic pressure field that remains after the static column is removed.
- `q_dyn(s)` is a kinetic-energy scale, not a pressure field. Overlaying it with `p_rgh(s)` shows whether local acceleration or redevelopment is large enough to matter on the same branchwise order of magnitude.
- `q'(s)` is the streamwise wall heat loss per length. When `q'(s)` stays large, fully developed assumptions stay weak because both the thermal and hydraulic states keep evolving along the same leg.
- The bend/corner lane is now strong enough for endpoint-path feature screening, but it is still not a continuous field-integrated density path. That remains the main remaining minor-loss limitation.
"""


def write_import_manifest(
    *,
    package_index_path: Path,
    output_dir: Path,
    summary: dict[str, Any],
    import_manifest_path: Path,
) -> None:
    payload = {
        "generated_at": iso_timestamp(),
        "package": "2026-06-23_ethan_salt_redevelopment_followon",
        "summary": summary,
        "inputs": {
            "package_index_csv": str(package_index_path.resolve()),
            "feature_case_summary_csv": str((FEATURE_DIR / "feature_path_case_summary.csv").resolve()),
            "feature_readme": str((FEATURE_DIR / "README.md").resolve()),
        },
        "outputs": {
            "report_dir": str(output_dir.resolve()),
            "profile_rows_csv": str((output_dir / "salt_redevelopment_profile_rows.csv").resolve()),
            "span_summary_csv": str((output_dir / "salt_redevelopment_span_summary.csv").resolve()),
            "feature_class_summary_csv": str((output_dir / "feature_class_summary.csv").resolve()),
        },
    }
    write_json(import_manifest_path, payload)


def main() -> int:
    args = parse_args()
    package_index_path = Path(args.package_index)
    output_dir = ensure_dir(Path(args.output_dir))
    figure_dir = ensure_dir(output_dir / "figures")

    package_rows = load_salt_package_rows(package_index_path)
    profile_rows = build_profile_rows(package_rows)
    span_summary_rows = summarize_span_rows(profile_rows)
    feature_class_rows, exclusion_rows = summarize_feature_rows()

    csv_dump_rows(output_dir / "salt_redevelopment_profile_rows.csv", profile_rows)
    csv_dump_rows(output_dir / "salt_redevelopment_span_summary.csv", span_summary_rows)
    csv_dump_rows(output_dir / "feature_class_summary.csv", feature_class_rows)
    csv_dump_rows(output_dir / "feature_exclusion_reason_summary.csv", exclusion_rows)

    figures: dict[str, dict[str, str]] = {}
    case_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in profile_rows:
        case_grouped[str(row["source_id"])].append(row)
    for source_id, payload in sorted(case_grouped.items()):
        figures[source_id] = plot_case(payload, figure_dir)

    summary = {
        "generated_at": iso_timestamp(),
        "salt_case_count": len(case_grouped),
        "profile_row_count": len(profile_rows),
        "span_summary_row_count": len(span_summary_rows),
        "feature_case_row_count": sum(int(row["case_row_count"]) for row in feature_class_rows),
        "feature_fit_used_case_count": sum(int(row["fit_used_case_count"]) for row in feature_class_rows),
        "figure_case_count": len(figures),
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(
        build_readme(
            case_count=len(case_grouped),
            span_summary_rows=span_summary_rows,
            feature_class_rows=feature_class_rows,
            exclusion_rows=exclusion_rows,
        ),
        encoding="utf-8",
    )
    write_import_manifest(
        package_index_path=package_index_path,
        output_dir=output_dir,
        summary=summary,
        import_manifest_path=Path(args.import_manifest_path),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
