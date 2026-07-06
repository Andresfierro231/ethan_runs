#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze import build_ethan_salt_thermal_closure_hardening as base
from tools.analyze.ethan_closure_modeling_v3_common import ROOT, csv_dump_rows, finite_float, write_json

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_thermal_closure_hardening_v3"
DEFAULT_RESIDUAL_FRACTION_MAX = 0.45


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the Salt thermal closure hardening v3 package by reusing the exact "
            "retained-time closure machinery and applying a moderate but explicit "
            "Nu admission policy."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    parser.add_argument(
        "--property-convention",
        default="branch_bulk",
        choices=("branch_bulk", "case_probe"),
    )
    parser.add_argument(
        "--residual-fraction-max",
        type=float,
        default=DEFAULT_RESIDUAL_FRACTION_MAX,
        help="Moderate case-level and time-level residual fraction ceiling for defended direct Salt Nu rows.",
    )
    return parser.parse_args()


def branch_trust_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        grouped[row["branch_name"]].append(row)
    rows_out: list[dict[str, Any]] = []
    for branch_name, payload in sorted(grouped.items()):
        rows_out.append(
            {
                "branch_name": branch_name,
                "row_count": len(payload),
                "fit_used_count": sum(1 for row in payload if row["fit_use_status"] == "fit_used"),
                "sensitivity_only_count": sum(1 for row in payload if row["fit_use_status"] == "sensitivity_only"),
                "excluded_count": sum(1 for row in payload if row["fit_use_status"] == "excluded"),
                "mean_support_fraction": base.safe_mean(finite_float(row.get("mean_support_fraction")) for row in payload),
                "mean_residual_fraction_of_wall_heat": base.safe_mean(
                    finite_float(row.get("mean_residual_fraction_of_wall_heat")) for row in payload
                ),
                "min_delta_t_wall_bulk_mean_k": min(
                    (finite_float(row.get("min_delta_t_wall_bulk_mean_k")) for row in payload),
                    default=float("nan"),
                ),
                "recommended_domain_status": (
                    "defended_direct_branch_domain"
                    if any(row["fit_use_status"] == "fit_used" for row in payload)
                    else "not_defended"
                ),
            }
        )
    return rows_out


def closure_waterfall_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for row in sorted(case_rows, key=lambda item: (int(item["case_order"]), item["branch_name"])):
        rows_out.append(
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "branch_name": row["branch_name"],
                "q_enthalpy_w": row["mean_q_enthalpy_w"],
                "q_wall_total_w": row["mean_q_wall_total_w"],
                "q_intended_transfer_w": row["mean_q_intended_transfer_w"],
                "q_external_or_loss_w": row["mean_q_external_or_loss_w"],
                "q_sink_or_cooling_w": row["mean_q_sink_or_cooling_w"],
                "q_junction_or_unresolved_w": row["mean_q_junction_or_unresolved_w"],
                "q_bulk_centerline_correction_proxy_w": row["mean_q_bulk_centerline_correction_proxy_w"],
                "q_residual_w": row["mean_q_residual_w"],
                "residual_fraction_of_wall_heat": row["mean_residual_fraction_of_wall_heat"],
                "fit_use_status": row["fit_use_status"],
                "exclusion_reason_primary": row["exclusion_reason_primary"],
            }
        )
    return rows_out


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None

    # Reuse the exact v2 mechanics but with an explicitly documented moderate
    # residual ceiling. The rest of the gates stay identical.
    base.RESIDUAL_FRACTION_MAX = float(args.residual_fraction_max)

    contexts = base.load_case_contexts(source_ids)
    branch_gate_rows = base.load_branch_gate_rows(source_ids)
    timeseries_rows = base.build_thermal_timeseries_rows(contexts, branch_gate_rows, property_convention=args.property_convention)
    case_rows = base.aggregate_case_rows(timeseries_rows)

    for row in case_rows:
        if row["fit_use_status"] == "fit_used":
            row["domain_note"] = "direct_left_lower_leg_or_equivalent_only"
        elif row["branch_name"] in base.THERMAL_DERIVED_BRANCHES:
            row["domain_note"] = "derived_overlap_context_only"
        else:
            row["domain_note"] = "not_in_defended_nu_domain"

    fit_ready_rows = [row for row in case_rows if row["fit_use_status"] == "fit_used"]
    trust_rows = branch_trust_rows(case_rows)
    waterfall_rows = closure_waterfall_rows(case_rows)
    exclusion_rows = [
        {
            "asset_family": "thermal_branch",
            "fit_use_status": fit_use_status,
            "exclusion_reason_primary": reason,
            "row_count": count,
        }
        for (fit_use_status, reason), count in sorted(
            Counter((row["fit_use_status"], row["exclusion_reason_primary"]) for row in case_rows if row["fit_use_status"] != "fit_used").items()
        )
    ]

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(output_dir / "thermal_closure_rows.csv", timeseries_rows)
    csv_dump_rows(output_dir / "thermal_closure_by_case.csv", case_rows)
    csv_dump_rows(output_dir / "thermal_fit_ready_rows.csv", fit_ready_rows)
    csv_dump_rows(output_dir / "thermal_exclusion_summary.csv", exclusion_rows)
    csv_dump_rows(output_dir / "branch_trust_summary.csv", trust_rows)
    csv_dump_rows(output_dir / "closure_waterfall_by_case.csv", waterfall_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "source_case_count": len({row["source_id"] for row in case_rows}),
        "timeseries_row_count": len(timeseries_rows),
        "case_row_count": len(case_rows),
        "fit_ready_row_count": len(fit_ready_rows),
        "residual_fraction_max": float(args.residual_fraction_max),
        "fit_ready_branches": sorted({row["branch_name"] for row in fit_ready_rows}),
        "fit_status_counts": Counter(row["fit_use_status"] for row in case_rows),
    }
    write_json(output_dir / "summary.json", summary)

    readme = f"""# Ethan Salt Thermal Closure Hardening v3

Generated: `2026-06-19`

## Purpose

This package reuses the exact retained-time Salt thermal closure machinery from
the June 19 v2 hardening pass, but applies a more explicit moderate-domain Nu
admission rule. It is still closure-first: unresolved residual remains a
reported quantity rather than something hidden inside `Nu`.

## Inputs

- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/enthalpy_balance_by_leg.csv`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/fluid_side_htc_nu_section_summary.csv`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/bulk_vs_centerline_temperature_correction.csv`
- `reports/2026-06-18_ethan_salt_analysis_checkpoint_suite/phase3_branch_trust_gate/branch_promotion_gate.csv`
- `tmp/2026-06-15_live_case_analysis/**/azimuthal_wall_transport_summary.csv`
- `tmp/2026-06-15_live_case_analysis/**/major_loss_cumulative_timeseries.csv`

## Moderate-domain gates

- support fraction remains at least `{base.SUPPORT_FRACTION_MIN:.2f}`
- minimum `|Twall - Tbulk|` remains `{base.DELTA_T_MIN_K:.2f} K`
- residual fraction ceiling is now `{float(args.residual_fraction_max):.2f}`
- grouped reconstruction ceiling remains `{base.GROUP_RECONSTRUCTION_MAX:.2f}`
- `right_leg` remains blocked
- derived `upcomer` remains sensitivity-only

## Current outcome

- direct fit-ready rows: `{len(fit_ready_rows)}`
- fit-ready branches: `{", ".join(summary["fit_ready_branches"]) if summary["fit_ready_branches"] else "none"}`

## Interpretation boundary

Any defended Salt Nu claim from this package is necessarily domain-limited to
the direct branches that survive these gates. Rows outside that domain remain
explicitly classified, not silently discarded.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    math_note = f"""# Math Companion

This package uses the same retained-time formulas as the June 19 v2 thermal
hardening package, but with one intentional policy change:

- `residual_fraction_of_wall_heat <= {float(args.residual_fraction_max):.2f}`

All other gate definitions remain unchanged:

- `support_fraction >= {base.SUPPORT_FRACTION_MIN:.2f}`
- `|Twall - Tbulk| >= {base.DELTA_T_MIN_K:.2f} K`
- `grouped_reconstruction_fraction <= {base.GROUP_RECONSTRUCTION_MAX:.2f}`

This is a reporting-policy change, not a hidden formula change.
"""
    (output_dir / "MATH_COMPANION.md").write_text(math_note, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
