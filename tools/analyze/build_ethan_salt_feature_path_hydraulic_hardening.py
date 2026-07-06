#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import (
    ROOT,
    csv_dump_rows,
    finite_float,
    load_salt_dashboard_rows,
    normalized_residual,
    require_columns,
    safe_mean,
    write_json,
)

CURRENT_FEATURE_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_feature_hydraulic_hardening"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_feature_path_hydraulic_hardening"
PROXY_SUPPORT_MIN = 2.0 / 3.0

CASE_COLUMNS = [
    "source_id",
    "case_label",
    "feature_name",
    "feature_class",
    "adjacent_major_spans",
    "time_row_count",
    "positive_proxy_time_fraction",
    "proxy_support_fraction_min",
    "proxy_support_fraction_mean",
    "mean_abs_delta_p_pa",
    "mean_abs_delta_p_rgh_pa",
    "mean_hydro_correction_abs_pa",
    "mean_proxy_reference_dp_pa",
    "mean_proxy_feature_excess_dp_pa",
    "mean_proxy_keff_effective",
    "pressure_method_status",
    "fit_use_status",
    "exclusion_reason_primary",
    "exclusion_reasons_json",
]

TIME_COLUMNS = [
    "source_id",
    "case_label",
    "feature_name",
    "feature_class",
    "time_s",
    "adjacent_major_spans",
    "dp_feature_p_pa",
    "dp_feature_p_abs_pa",
    "dp_feature_prgh_pa",
    "dp_feature_loss_prgh_endpoint_pa",
    "dp_feature_hydro_endpoint_proxy_pa",
    "dp_feature_hydro_correction_pa",
    "dp_feature_loss_hydro_pa",
    "feature_path_length_m",
    "feature_path_support_fraction",
    "adjacent_straight_friction_subtracted_pa",
    "feature_excess_proxy_pa",
    "keff_effective",
    "hydro_method_status",
    "pressure_method_status",
    "fit_use_status",
    "exclusion_reason_primary",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Salt feature-path hydraulic blocker audit that maps the current "
            "proxy-only feature closure onto explicit path-method statuses without "
            "claiming a full density-integral feature path."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def classify_case_row(row: dict[str, Any]) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    support_fraction = finite_float(row.get("proxy_support_fraction_min"), finite_float(row.get("local_support_fraction_min")))
    if not math.isfinite(support_fraction) or support_fraction < PROXY_SUPPORT_MIN:
        reasons.append("incomplete_feature_boundary_support")
    positive_fraction = finite_float(row.get("positive_proxy_time_fraction"), finite_float(row.get("positive_time_fraction")))
    if not math.isfinite(positive_fraction) or positive_fraction <= 0.0:
        reasons.append("nonpositive_local_feature_proxy_excess")
    if reasons:
        return "excluded", reasons[0], reasons
    return "sensitivity_only", "missing_full_path_density_integral", ["missing_full_path_density_integral"]


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None
    dashboard_rows = load_salt_dashboard_rows(source_ids)
    current_time_rows = load_csv_rows(CURRENT_FEATURE_DIR / "feature_hydro_closure_timeseries.csv")
    current_case_rows = load_csv_rows(CURRENT_FEATURE_DIR / "feature_hydro_closure_by_case.csv")
    require_columns(
        current_time_rows,
        [
            "source_id",
            "case_label",
            "feature_name",
            "feature_class",
            "time_s",
            "adjacent_major_spans",
            "raw_delta_p_pa",
            "raw_abs_delta_p_rgh_pa",
            "hydro_proxy_p_minus_prgh_pa",
            "reference_length_m",
            "support_fraction",
            "local_boundary_reference_dp_pa",
            "feature_excess_dp_local_pa",
            "keff_effective_local",
        ],
        "feature_hydro_closure_timeseries.csv",
    )
    require_columns(
        current_case_rows,
        [
            "source_id",
            "case_label",
            "feature_name",
            "feature_class",
            "adjacent_major_spans",
            "positive_time_fraction",
            "local_support_fraction_min",
            "local_support_fraction_mean",
            "mean_delta_p_pa",
            "mean_abs_delta_p_rgh_pa",
            "mean_hydro_proxy_p_minus_prgh_pa",
            "mean_local_boundary_reference_dp_pa",
            "mean_feature_excess_dp_local_pa",
            "mean_keff_effective_local",
        ],
        "feature_hydro_closure_by_case.csv",
    )
    if source_ids:
        current_time_rows = [row for row in current_time_rows if row["source_id"] in source_ids]
        current_case_rows = [row for row in current_case_rows if row["source_id"] in source_ids]

    label_lookup = {row["source_id"]: row["display_label"] for row in dashboard_rows}

    time_rows: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    by_case_feature: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for row in current_time_rows:
        support_fraction = finite_float(row.get("support_fraction"))
        proxy_excess = finite_float(row.get("feature_excess_dp_local_pa"))
        if not math.isfinite(support_fraction) or support_fraction < PROXY_SUPPORT_MIN:
            pressure_method_status = "blocked_incomplete_boundary_support"
            fit_use_status = "excluded"
            exclusion_reason_primary = "incomplete_feature_boundary_support"
        elif not math.isfinite(proxy_excess) or proxy_excess <= 0.0:
            pressure_method_status = "proxy_only_nonpositive_excess"
            fit_use_status = "excluded"
            exclusion_reason_primary = "nonpositive_local_feature_proxy_excess"
        else:
            pressure_method_status = "proxy_only_missing_full_path_integral"
            fit_use_status = "sensitivity_only"
            exclusion_reason_primary = "missing_full_path_density_integral"
        output_row = {
            "source_id": row["source_id"],
            "case_label": label_lookup.get(row["source_id"], row["case_label"]),
            "feature_name": row["feature_name"],
            "feature_class": row["feature_class"],
            "time_s": finite_float(row.get("time_s")),
            "adjacent_major_spans": row["adjacent_major_spans"],
            "dp_feature_p_pa": finite_float(row.get("raw_delta_p_pa")),
            "dp_feature_p_abs_pa": abs(finite_float(row.get("raw_delta_p_pa"))),
            "dp_feature_prgh_pa": finite_float(row.get("raw_abs_delta_p_rgh_pa")),
            "dp_feature_loss_prgh_endpoint_pa": finite_float(row.get("raw_abs_delta_p_rgh_pa")),
            "dp_feature_hydro_endpoint_proxy_pa": finite_float(row.get("hydro_proxy_p_minus_prgh_pa")),
            "dp_feature_hydro_correction_pa": finite_float(row.get("hydro_proxy_p_minus_prgh_pa")),
            "dp_feature_loss_hydro_pa": math.nan,
            "feature_path_length_m": finite_float(row.get("reference_length_m")),
            "feature_path_support_fraction": support_fraction,
            "adjacent_straight_friction_subtracted_pa": finite_float(row.get("local_boundary_reference_dp_pa")),
            "feature_excess_proxy_pa": proxy_excess,
            "keff_effective": finite_float(row.get("keff_effective_local")),
            "hydro_method_status": "endpoint_proxy_only",
            "pressure_method_status": pressure_method_status,
            "fit_use_status": fit_use_status,
            "exclusion_reason_primary": exclusion_reason_primary,
        }
        time_rows.append(output_row)
        by_case_feature[(row["source_id"], row["feature_name"])].append(output_row)

    for row in current_case_rows:
        fit_use_status, exclusion_reason_primary, reasons = classify_case_row(row)
        case_rows.append(
            {
                "source_id": row["source_id"],
                "case_label": label_lookup.get(row["source_id"], row["case_label"]),
                "feature_name": row["feature_name"],
                "feature_class": row["feature_class"],
                "adjacent_major_spans": row["adjacent_major_spans"],
                "time_row_count": len(by_case_feature[(row["source_id"], row["feature_name"])]),
                "positive_proxy_time_fraction": finite_float(row.get("positive_time_fraction")),
                "proxy_support_fraction_min": finite_float(row.get("local_support_fraction_min")),
                "proxy_support_fraction_mean": finite_float(row.get("local_support_fraction_mean")),
                "mean_abs_delta_p_pa": abs(finite_float(row.get("mean_delta_p_pa"))),
                "mean_abs_delta_p_rgh_pa": finite_float(row.get("mean_abs_delta_p_rgh_pa")),
                "mean_hydro_correction_abs_pa": abs(finite_float(row.get("mean_hydro_proxy_p_minus_prgh_pa"))),
                "mean_proxy_reference_dp_pa": finite_float(row.get("mean_local_boundary_reference_dp_pa")),
                "mean_proxy_feature_excess_dp_pa": finite_float(row.get("mean_feature_excess_dp_local_pa")),
                "mean_proxy_keff_effective": finite_float(row.get("mean_keff_effective_local")),
                "pressure_method_status": "full_path_missing_proxy_only_available",
                "fit_use_status": fit_use_status,
                "exclusion_reason_primary": exclusion_reason_primary,
                "exclusion_reasons_json": json.dumps(reasons),
            }
        )

    fit_ready_rows = [row for row in case_rows if row["fit_use_status"] == "fit_used"]
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
    method_comparison_rows = []
    for row in case_rows:
        method_comparison_rows.append(
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "feature_name": row["feature_name"],
                "feature_class": row["feature_class"],
                "mean_abs_delta_p_rgh_pa": row["mean_abs_delta_p_rgh_pa"],
                "mean_abs_delta_p_pa": row["mean_abs_delta_p_pa"],
                "mean_hydro_correction_abs_pa": row["mean_hydro_correction_abs_pa"],
                "mean_proxy_reference_dp_pa": row["mean_proxy_reference_dp_pa"],
                "mean_proxy_feature_excess_dp_pa": row["mean_proxy_feature_excess_dp_pa"],
                "pressure_method_status": row["pressure_method_status"],
                "fit_use_status": row["fit_use_status"],
            }
        )
    blocker_rows = [
        {
            "dependency_or_gap": "feature_keff_full_path_closure",
            "current_status": "not_defensible_yet",
            "missing_requirement": "retained-time feature-path density or hydro integral beyond proxy endpoint p_rgh plus local straight reference",
            "why_it_matters": "feature K_eff cannot move beyond proxy-only context without a path-resolved dissipative loss basis",
            "current_bias_risk": "proxy endpoint residual can over- or under-attribute local feature loss",
        }
    ]

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(output_dir / "feature_path_rows.csv", time_rows, TIME_COLUMNS)
    csv_dump_rows(output_dir / "feature_case_summary.csv", case_rows, CASE_COLUMNS)
    csv_dump_rows(output_dir / "feature_method_comparison.csv", method_comparison_rows)
    csv_dump_rows(output_dir / "feature_fit_ready_rows.csv", fit_ready_rows, CASE_COLUMNS)
    csv_dump_rows(output_dir / "feature_exclusion_summary.csv", exclusion_summary)
    csv_dump_rows(output_dir / "feature_blocked_requirements.csv", blocker_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "source_case_count": len({row["source_id"] for row in case_rows}),
        "feature_case_row_count": len(case_rows),
        "feature_time_row_count": len(time_rows),
        "fit_ready_row_count": len(fit_ready_rows),
        "pressure_method_statuses": Counter(row["pressure_method_status"] for row in case_rows),
        "fit_status_counts": Counter(row["fit_use_status"] for row in case_rows),
    }
    write_json(output_dir / "summary.json", summary)

    readme = f"""# Ethan Salt Feature-Path Hydraulic Hardening

Generated: `2026-06-19`

## Purpose

This package converts the current Salt feature proxy closure into an explicit
feature-path blocker audit. It does **not** claim a defended full feature-path
hydro integral. Instead, it maps each feature row onto a machine-readable
status showing whether the repo currently has only a proxy endpoint method or
an outright support failure.

## Inputs

- `reports/2026-06-19_ethan_salt_feature_hydraulic_hardening/feature_hydro_closure_timeseries.csv`
- `reports/2026-06-19_ethan_salt_feature_hydraulic_hardening/feature_hydro_closure_by_case.csv`
- `reports/2026-06-17_ethan_nondimensional_dashboard_package/salt_dashboard.csv`

## Current outcome

- case rows: `{len(case_rows)}`
- fit-ready defended feature rows: `{len(fit_ready_rows)}`
- dominant method status: `full_path_missing_proxy_only_available`

## Interpretation boundary

This package is intentionally conservative. Proxy-positive rows remain
`sensitivity_only` until a retained-time feature-path hydro integral is
available. The downstream v3 Salt dependency package must not publish a
defended feature `K_eff` model from these rows.

The retained-time table now preserves the proxy decomposition explicitly:

- `dp_feature_loss_prgh_endpoint_pa`
- `dp_feature_hydro_endpoint_proxy_pa`
- `feature_excess_proxy_pa`
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    math_note = """# Math Companion

Current available feature quantities:

- `dp_feature_p_pa = p_start - p_end`
- `dp_feature_p_abs_pa = |p_start - p_end|`
- `dp_feature_prgh_pa = |p_rgh,start - p_rgh,end|`
- `dp_feature_loss_prgh_endpoint_pa = |p_rgh,start - p_rgh,end|`
- `dp_feature_hydro_endpoint_proxy_pa = |(p_start - p_end) - (p_rgh,start - p_rgh,end)|`
- `dp_feature_hydro_correction_pa = dp_feature_hydro_endpoint_proxy_pa`
- `adjacent_straight_friction_subtracted_pa = proxy local straight reference from the existing June 19 feature package`
- `feature_excess_proxy_pa = dp_feature_loss_prgh_endpoint_pa - adjacent_straight_friction_subtracted_pa`

Intentionally *not* claimed here:

- a defended `dp_feature_loss_hydro_pa`
- a defended full-path `K_eff`

Reason:

The preserved additive artifacts do not retain a direct feature-path density
integral or equivalent pathwise hydro correction strong enough to replace the
endpoint proxy method.
"""
    (output_dir / "MATH_COMPANION.md").write_text(math_note, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
