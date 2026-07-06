#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.build_ethan_water_phase1_starter_package import classify_thermal_phase1
from tools.analyze.ethan_closure_modeling_v3_common import (
    ROOT,
    csv_dump_rows,
    finite_float,
    load_csv_rows,
    load_water_dashboard_rows,
    safe_mean,
    write_json,
)

PRESSURE_DIR = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package"
STARTER_DIR = ROOT / "reports" / "2026-06-19_ethan_water_phase1_starter_package"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-19_ethan_water_thermal_closure_readiness"
DIRECT_SPANS = ["left_lower_leg", "left_upper_leg", "lower_leg", "right_leg", "test_section_span", "upper_leg"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Water thermal closure readiness package.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    return parser.parse_args()


def filter_rows(rows: list[dict[str, str]], source_ids: set[str] | None) -> list[dict[str, str]]:
    if not source_ids:
        return rows
    return [row for row in rows if row.get("source_id") in source_ids]


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None
    dashboard_rows = load_water_dashboard_rows(source_ids)
    case_label_lookup = {row["source_id"]: row["display_label"] for row in dashboard_rows}
    field_rows = filter_rows(load_csv_rows(PRESSURE_DIR / "water_effective_htc_nu_fields.csv"), source_ids)
    enthalpy_rows = filter_rows(load_csv_rows(PRESSURE_DIR / "enthalpy_balance_by_leg.csv"), source_ids)
    hydraulic_rows = load_csv_rows(STARTER_DIR / "water_hydraulic_branch_readiness.csv")
    hydraulic_lookup = {row["branch"]: row["classification"] for row in hydraulic_rows}

    case_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for span_name in DIRECT_SPANS:
        span_field_rows = [row for row in field_rows if row["family"] == "water" and row["span_name"] == span_name]
        span_enthalpy_rows = [row for row in enthalpy_rows if row["family"] == "water" and row["span_name"] == span_name]

        by_case_field: dict[str, list[dict[str, str]]] = defaultdict(list)
        by_case_enthalpy: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in span_field_rows:
            by_case_field[row["source_id"]].append(row)
        for row in span_enthalpy_rows:
            by_case_enthalpy[row["source_id"]].append(row)

        for source_id in sorted(by_case_field):
            payload = by_case_field[source_id]
            usable_flags = [row["thermal_support_status"] == "usable" for row in payload]
            usable_fraction = sum(1 for flag in usable_flags if flag) / max(len(usable_flags), 1)
            delta_ts = [
                abs(finite_float(row.get("delta_t_wall_minus_bulk_k")))
                for row in payload
                if abs(finite_float(row.get("delta_t_wall_minus_bulk_k"))) == abs(finite_float(row.get("delta_t_wall_minus_bulk_k")))
            ]
            nu_values = [finite_float(row.get("nu_local_signed")) for row in payload if finite_float(row.get("nu_local_signed")) == finite_float(row.get("nu_local_signed"))]
            residuals = []
            sign_ok = 0
            sign_total = 0
            for row in by_case_enthalpy.get(source_id, []):
                enthalpy = finite_float(row.get("enthalpy_change_w"))
                wall = finite_float(row.get("wall_heat_total_w"))
                if abs(wall) <= 1.0e-12 or enthalpy != enthalpy or wall != wall:
                    continue
                residuals.append(abs(enthalpy - wall) / abs(wall))
                enthalpy_sign = "positive" if enthalpy > 1.0e-9 else "negative" if enthalpy < -1.0e-9 else "zero"
                wall_sign = "positive" if wall > 1.0e-9 else "negative" if wall < -1.0e-9 else "zero"
                if enthalpy_sign == wall_sign or "zero" in {enthalpy_sign, wall_sign}:
                    sign_ok += 1
                sign_total += 1

            sign_fraction = sign_ok / sign_total if sign_total else float("nan")
            classification, reason = classify_thermal_phase1(
                span_name,
                hydraulic_lookup.get(span_name, "unknown"),
                usable_fraction,
                min(delta_ts) if delta_ts else float("nan"),
                safe_mean(residuals),
                sign_fraction,
            )
            case_rows.append(
                {
                    "source_id": source_id,
                    "case_label": case_label_lookup.get(source_id, source_id),
                    "span_name": span_name,
                    "hydraulic_classification": hydraulic_lookup.get(span_name, "unknown"),
                    "field_row_count": len(payload),
                    "usable_fraction": usable_fraction,
                    "min_abs_delta_t_wall_bulk_k": min(delta_ts) if delta_ts else float("nan"),
                    "mean_abs_delta_t_wall_bulk_k": safe_mean(delta_ts),
                    "mean_nu_local_signed": safe_mean(nu_values),
                    "enthalpy_residual_mean": safe_mean(residuals),
                    "enthalpy_sign_consistency_fraction": sign_fraction,
                    "readiness_status": classification,
                    "readiness_reason": reason,
                }
            )

        span_cases = [row for row in case_rows if row["span_name"] == span_name]
        summary_rows.append(
            {
                "span_name": span_name,
                "hydraulic_classification": hydraulic_lookup.get(span_name, "unknown"),
                "case_count": len(span_cases),
                "readiness_status_counts": Counter(row["readiness_status"] for row in span_cases),
                "mean_usable_fraction": safe_mean(finite_float(row.get("usable_fraction")) for row in span_cases),
                "mean_enthalpy_residual": safe_mean(finite_float(row.get("enthalpy_residual_mean")) for row in span_cases),
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
    csv_dump_rows(output_dir / "water_thermal_closure_readiness_rows.csv", case_rows)
    csv_dump_rows(output_dir / "water_thermal_span_summary.csv", summary_rows)
    csv_dump_rows(output_dir / "water_thermal_exclusion_summary.csv", exclusion_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len({row["source_id"] for row in case_rows}),
        "row_count": len(case_rows),
        "status_counts": Counter(row["readiness_status"] for row in case_rows),
    }
    write_json(output_dir / "summary.json", summary)

    readme = """# Water Thermal Closure Readiness

Generated: `2026-06-19`

## Purpose

This package turns the Water-family thermal support and enthalpy artifacts into
a closure-readiness table. It does not claim any defended Water Nu dependency.

## Inputs

- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/water_effective_htc_nu_fields.csv`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/enthalpy_balance_by_leg.csv`
- `reports/2026-06-19_ethan_water_phase1_starter_package/water_hydraulic_branch_readiness.csv`

## Interpretation boundary

Rows are labeled only as readiness outcomes:
- `closure_rebuild_priority`
- `closure_rebuild_candidate`
- `support_present_context_only`
- `blocked_*`
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
