#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import csv_dump_rows, write_json
from tools.analyze.ethan_salt_hardening_common import finite_float, load_csv_rows, require_columns, safe_mean

FEATURE_PATH_DIR = Path("reports/2026-06-22_ethan_feature_path_hydro_decomposition")
DEFAULT_OUTPUT_DIR = Path("reports/2026-06-22_ethan_salt_feature_path_hydraulic_hardening_v2")

CASE_COLUMNS = [
    "source_id",
    "case_label",
    "case_order",
    "feature_name",
    "feature_class",
    "adjacent_major_spans",
    "time_row_count",
    "defended_time_fraction",
    "positive_time_fraction",
    "support_fraction_min",
    "support_fraction_mean",
    "warning_fraction",
    "mean_abs_delta_p_pa",
    "mean_abs_delta_p_rgh_pa",
    "mean_hydro_path_abs_pa",
    "mean_proxy_window_hydro_abs_pa",
    "mean_window_vs_path_hydro_gap_fraction",
    "mean_local_boundary_reference_dp_pa",
    "mean_existing_span_reference_dp_pa",
    "mean_feature_excess_path_pa",
    "mean_feature_excess_existing_pa",
    "mean_dynamic_head_local_pa",
    "mean_keff_effective_path",
    "mean_re_effective",
    "mean_rho_effective_kg_m3",
    "mean_bulk_velocity_effective_m_s",
    "mean_hydraulic_diameter_geom_m",
    "mean_property_temperature_k",
    "pressure_method_status",
    "reference_method_status",
    "fit_use_status",
    "exclusion_reason_primary",
    "exclusion_reasons_json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the refreshed Salt feature-path hydraulic hardening package from "
            "the June 22 pathwise patch-endpoint decomposition."
        )
    )
    parser.add_argument("--feature-path-dir", default=str(FEATURE_PATH_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    return parser.parse_args()


def load_case_rows(feature_path_dir: Path, source_ids: set[str] | None) -> list[dict[str, Any]]:
    rows = load_csv_rows(feature_path_dir / "feature_path_case_summary.csv")
    require_columns(
        rows,
        [
            "source_id",
            "feature_name",
            "feature_class",
            "positive_time_fraction",
            "support_fraction_min",
            "mean_feature_excess_path_pa",
            "mean_dynamic_head_local_pa",
            "mean_re_effective",
            "mean_keff_effective_path",
            "fit_use_status",
            "exclusion_reason_primary",
        ],
        "feature_path_case_summary.csv",
    )
    if source_ids:
        rows = [row for row in rows if row["source_id"] in source_ids]
    return [dict(row) for row in rows]


def build_stability_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        grouped[row["feature_name"]].append(row)
    rows_out: list[dict[str, Any]] = []
    for feature_name, group in sorted(grouped.items()):
        fit_used = [row for row in group if row["fit_use_status"] == "fit_used"]
        rows_out.append(
            {
                "feature_name": feature_name,
                "feature_class": group[0]["feature_class"],
                "case_count": len(group),
                "fit_used_case_count": len(fit_used),
                "fit_used_case_fraction": len(fit_used) / max(len(group), 1),
                "mean_positive_time_fraction": safe_mean(finite_float(row.get("positive_time_fraction")) for row in group),
                "mean_support_fraction_min": safe_mean(finite_float(row.get("support_fraction_min")) for row in group),
                "mean_feature_excess_path_pa": safe_mean(finite_float(row.get("mean_feature_excess_path_pa")) for row in group),
                "mean_keff_effective_path": safe_mean(finite_float(row.get("mean_keff_effective_path")) for row in group),
            }
        )
    return rows_out


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None
    feature_path_dir = Path(args.feature_path_dir)
    case_rows = load_case_rows(feature_path_dir, source_ids)
    fit_ready_rows = [row for row in case_rows if row["fit_use_status"] == "fit_used"]
    stability_rows = build_stability_rows(case_rows)
    exclusion_summary = [
        {
            "feature_class": feature_class,
            "fit_use_status": fit_use_status,
            "exclusion_reason_primary": reason,
            "row_count": count,
        }
        for (feature_class, fit_use_status, reason), count in sorted(
            Counter((row["feature_class"], row["fit_use_status"], row["exclusion_reason_primary"]) for row in case_rows).items()
        )
    ]
    method_rows = []
    for row in case_rows:
        method_rows.append(
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "feature_name": row["feature_name"],
                "feature_class": row["feature_class"],
                "pressure_method_status": row["pressure_method_status"],
                "reference_method_status": row["reference_method_status"],
                "mean_hydro_path_abs_pa": row["mean_hydro_path_abs_pa"],
                "mean_proxy_window_hydro_abs_pa": row["mean_proxy_window_hydro_abs_pa"],
                "mean_window_vs_path_hydro_gap_fraction": row["mean_window_vs_path_hydro_gap_fraction"],
                "mean_feature_excess_path_pa": row["mean_feature_excess_path_pa"],
                "fit_use_status": row["fit_use_status"],
            }
        )

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(output_dir / "feature_case_summary.csv", case_rows, CASE_COLUMNS)
    csv_dump_rows(output_dir / "feature_fit_ready_rows.csv", fit_ready_rows, CASE_COLUMNS)
    csv_dump_rows(output_dir / "feature_exclusion_summary.csv", exclusion_summary)
    csv_dump_rows(output_dir / "feature_stability_summary.csv", stability_rows)
    csv_dump_rows(output_dir / "feature_method_comparison.csv", method_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "source_case_count": len({row["source_id"] for row in case_rows}),
        "feature_case_row_count": len(case_rows),
        "fit_ready_case_row_count": len(fit_ready_rows),
        "fit_status_counts": Counter(row["fit_use_status"] for row in case_rows),
    }
    write_json(output_dir / "summary.json", summary)

    readme = f"""# Ethan Salt Feature-Path Hydraulic Hardening v2

Generated: `2026-06-22`

## What changed

This refresh replaces the earlier v3 blocker-only status with the new June 22
pathwise decomposition:

- exact patch-endpoint `p` and `p_rgh` differences are now explicit
- the local straight subtraction remains the same bounded boundary-reference
  method
- rows with positive retained-time feature excess and complete support are
  allowed back into the feature hardening lane

## Counts

- feature case rows: `{len(case_rows)}`
- fit-ready feature case rows: `{len(fit_ready_rows)}`

## Important boundary

The feature signal is now defended as a patch-endpoint path decomposition with
the existing local straight reference. It is still not a continuous field
integral through the feature volume, so downstream claims should remain
`provisional_defended` rather than stronger than that.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
