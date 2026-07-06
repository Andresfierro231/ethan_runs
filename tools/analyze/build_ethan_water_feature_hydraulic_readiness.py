#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import (
    ROOT,
    csv_dump_rows,
    finite_float,
    load_water_dashboard_rows,
    safe_mean,
    write_json,
)

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-19_ethan_water_feature_hydraulic_readiness"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Water feature hydraulic readiness package.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def classify_feature_row(positive_fraction: float, warning_fraction: float) -> tuple[str, str]:
    if positive_fraction >= 0.75 and warning_fraction <= 0.25:
        return "candidate_for_future_dependency_fit", "proxy residual is mostly positive and warning fraction is limited"
    if positive_fraction > 0.0:
        return "needs_closure_rebuild", "feature evidence exists but proxy sign stability or warnings are too weak for future fitting"
    return "blocked", "proxy residual never becomes positive on the preserved retained times"


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None
    dashboard_rows = load_water_dashboard_rows(source_ids)

    case_rows: list[dict[str, Any]] = []
    feature_summary: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for dashboard_row in dashboard_rows:
        package_root = Path(dashboard_row["package_root"])
        feature_path = package_root / "feature_minor_loss_timeseries.csv"
        if not feature_path.exists():
            case_rows.append(
                {
                    "source_id": dashboard_row["source_id"],
                    "case_label": dashboard_row["display_label"],
                    "feature_name": "all_features",
                    "time_row_count": 0,
                    "positive_proxy_fraction": float("nan"),
                    "warning_fraction": float("nan"),
                    "readiness_status": "blocked",
                    "readiness_reason": "missing feature_minor_loss_timeseries.csv",
                }
            )
            continue
        rows = load_csv_rows(feature_path)
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            grouped[row["feature_name"]].append(row)
        for feature_name, payload in sorted(grouped.items()):
            positive_fraction = sum(1 for row in payload if finite_float(row.get("minor_residual_dp_pa")) > 0.0) / max(len(payload), 1)
            warning_fraction = sum(1 for row in payload if row.get("warning_flag") == "yes") / max(len(payload), 1)
            status, reason = classify_feature_row(positive_fraction, warning_fraction)
            output_row = {
                "source_id": dashboard_row["source_id"],
                "case_label": dashboard_row["display_label"],
                "feature_name": feature_name,
                "time_row_count": len(payload),
                "positive_proxy_fraction": positive_fraction,
                "warning_fraction": warning_fraction,
                "mean_abs_delta_p_rgh_pa": safe_mean(abs(finite_float(row.get("abs_delta_p_rgh_pa"))) for row in payload),
                "mean_proxy_minor_residual_dp_pa": safe_mean(finite_float(row.get("minor_residual_dp_pa")) for row in payload),
                "readiness_status": status,
                "readiness_reason": reason,
            }
            case_rows.append(output_row)
            feature_summary[feature_name].append(output_row)

    summary_rows = []
    for feature_name, payload in sorted(feature_summary.items()):
        summary_rows.append(
            {
                "feature_name": feature_name,
                "case_count": len(payload),
                "candidate_case_count": sum(1 for row in payload if row["readiness_status"] == "candidate_for_future_dependency_fit"),
                "blocked_case_count": sum(1 for row in payload if row["readiness_status"] == "blocked"),
                "mean_positive_proxy_fraction": safe_mean(finite_float(row.get("positive_proxy_fraction")) for row in payload),
                "mean_warning_fraction": safe_mean(finite_float(row.get("warning_fraction")) for row in payload),
            }
        )

    exclusion_rows = [
        {
            "readiness_status": status,
            "row_count": count,
        }
        for status, count in sorted(Counter(row["readiness_status"] for row in case_rows).items())
    ]

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(output_dir / "water_feature_hydraulic_readiness_rows.csv", case_rows)
    csv_dump_rows(output_dir / "water_feature_hydraulic_summary.csv", summary_rows)
    csv_dump_rows(output_dir / "water_feature_hydraulic_exclusion_summary.csv", exclusion_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len({row["source_id"] for row in case_rows}),
        "feature_case_row_count": len(case_rows),
        "status_counts": Counter(row["readiness_status"] for row in case_rows),
    }
    write_json(output_dir / "summary.json", summary)

    readme = """# Water Feature Hydraulic Readiness

Generated: `2026-06-19`

## Purpose

This package audits whether the preserved Water-family feature pressure artifacts
look clean enough to justify a future closure-gated hardening pass. It does not
claim defended Water feature `K_eff`.

## Inputs

- `reports/2026-06-17_ethan_nondimensional_dashboard_package/water_dashboard.csv`
- `tmp/2026-06-15_live_case_analysis/**/feature_minor_loss_timeseries.csv`

## Interpretation boundary

Readiness labels are based only on proxy residual sign stability and warning
fraction. Any future Water feature dependency package still needs a stricter
hydro-corrected method before fitting.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
