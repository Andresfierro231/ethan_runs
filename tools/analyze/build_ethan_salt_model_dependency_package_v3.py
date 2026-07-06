#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.build_ethan_salt_model_dependency_package_v2 import (
    fit_geometric_constant,
    fit_power_law,
)
from tools.analyze.ethan_closure_modeling_v3_common import ROOT, csv_dump_rows, finite_float, load_csv_rows, write_json

STRAIGHT_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_straight_hydraulic_sensitivity"
FEATURE_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_feature_path_hydraulic_hardening"
THERMAL_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_thermal_closure_hardening_v3"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_model_dependency_package_v3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the Salt v3 model-dependency package from the new hydraulic and thermal hardening packages."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    return parser.parse_args()


def filter_rows(rows: list[dict[str, str]], source_ids: set[str] | None) -> list[dict[str, str]]:
    if not source_ids:
        return rows
    return [row for row in rows if row.get("source_id") in source_ids]


def ci_excludes_zero(fit_result: dict[str, Any], coefficient_name: str) -> bool:
    ci = fit_result.get("bootstrap_ci95", {}).get(coefficient_name)
    if not ci or len(ci) != 2:
        return False
    return not (ci[0] <= 0.0 <= ci[1])


def choose_nu_status(rows: list[dict[str, Any]], fit_result: dict[str, Any]) -> tuple[str, str, str]:
    if len(rows) < 4:
        return "not_defensible_yet", "exploratory_screened_only_model", "fewer_than_four_direct_rows"
    case_count = len({row["source_id"] for row in rows})
    if case_count < 2:
        return "not_defensible_yet", "exploratory_screened_only_model", "single_case_domain_only"
    if fit_result.get("status") != "fit":
        return "not_defensible_yet", "exploratory_screened_only_model", "fit_not_stable"
    if not ci_excludes_zero(fit_result, "log_re"):
        return "not_defensible_yet", "exploratory_screened_only_model", "re_slope_ci_crosses_zero"
    return "provisional_defended", fit_result["model_type"], "limited_direct_branch_domain"


def sensitivity_rows_from_thermal_case_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for threshold in (0.40, 0.45, 0.50):
        kept = [
            row
            for row in rows
            if row["branch_name"] not in {"right_leg", "upcomer"}
            and row["branch_fit_status"] == "candidate"
            and finite_float(row.get("mean_support_fraction")) >= 0.90
            and finite_float(row.get("min_delta_t_wall_bulk_mean_k")) >= 0.25
            and finite_float(row.get("mean_grouped_reconstruction_fraction")) <= 0.05
            and row.get("direction_consistent_all_times") == "True"
            and finite_float(row.get("mean_residual_fraction_of_wall_heat")) <= threshold
            and finite_float(row.get("mean_nu_effective")) > 0.0
        ]
        out.append(
            {
                "asset_family": "salt_nu",
                "sensitivity_name": f"thermal_residual_threshold_{threshold:.2f}",
                "status": "run",
                "base_row_count": "",
                "sensitivity_row_count": len(kept),
                "row_count_delta": "",
                "qualitative_conclusion_changed": "",
                "row_count": len(kept),
                "case_count": len({row['source_id'] for row in kept}),
                "branch_names": "|".join(sorted({row["branch_name"] for row in kept})),
                "note": f"direct-branch Salt Nu rows surviving mean residual fraction <= {threshold:.2f}",
            }
        )
    return out


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None

    straight_fit_rows = filter_rows(load_csv_rows(STRAIGHT_DIR / "straight_fit_ready_rows.csv"), source_ids)
    straight_sensitivity_rows = load_csv_rows(STRAIGHT_DIR / "straight_sensitivity_runs.csv")
    feature_case_rows = filter_rows(load_csv_rows(FEATURE_DIR / "feature_case_summary.csv"), source_ids)
    thermal_case_rows = filter_rows(load_csv_rows(THERMAL_DIR / "thermal_closure_by_case.csv"), source_ids)
    thermal_fit_rows = filter_rows(load_csv_rows(THERMAL_DIR / "thermal_fit_ready_rows.csv"), source_ids)

    hydraulic_fit_ready_rows: list[dict[str, Any]] = []
    for row in straight_fit_rows:
        hydraulic_fit_ready_rows.append(
            {
                "asset_family": "straight_section_friction",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "category_name": row["section_name"],
                "category_class": row["section_kind"],
                "re_effective": finite_float(row.get("re_value")),
                "target_value": finite_float(row.get("friction_target_value")),
                "support_fraction": finite_float(row.get("support_fraction")),
                "direct_to_shear_ratio": finite_float(row.get("direct_to_shear_ratio")),
                "pressure_method_status": "defended_direct_hydro_case_mean_only",
                "fit_use_status": row["fit_use_status"],
            }
        )

    thermal_ready_rows: list[dict[str, Any]] = []
    for row in thermal_fit_rows:
        thermal_ready_rows.append(
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "branch_name": row["branch_name"],
                "branch_type": row["branch_type"],
                "domain_note": row.get("domain_note", ""),
                "re_effective": finite_float(row.get("mean_re_effective")),
                "pr_effective": finite_float(row.get("mean_pr_effective")),
                "pe_effective": finite_float(row.get("mean_pe_effective")),
                "nu_effective": finite_float(row.get("mean_nu_effective")),
                "htc_effective_w_m2_k": finite_float(row.get("mean_htc_effective_w_m2_k")),
                "support_fraction": finite_float(row.get("mean_support_fraction")),
                "residual_fraction_of_wall_heat": finite_float(row.get("mean_residual_fraction_of_wall_heat")),
                "bulk_minus_centerline_temp_k": finite_float(row.get("mean_bulk_minus_centerline_temp_k")),
                "fit_use_status": row["fit_use_status"],
            }
        )

    straight_constant = fit_geometric_constant(hydraulic_fit_ready_rows, "target_value", "category_name")
    straight_power = fit_power_law(
        hydraulic_fit_ready_rows,
        "target_value",
        "re_effective",
        "category_name",
        "class_aware_re_power_law",
        robust=False,
    )
    straight_status = "provisional_defended" if straight_power.get("status") == "fit" and len(hydraulic_fit_ready_rows) >= 8 else "not_defensible_yet"

    feature_proxy_positive = [row for row in feature_case_rows if row["fit_use_status"] == "sensitivity_only"]
    feature_fit_result = {
        "recommended_status": "not_defensible_yet",
        "recommended_model": "refused_until_full_path_closure",
        "fit_used_row_count": 0,
        "screened_proxy_positive_row_count": len(feature_proxy_positive),
        "reason": "full feature-path hydro integral still missing in the current additive artifact stack",
    }

    nu_constant = fit_geometric_constant(thermal_ready_rows, "nu_effective", "branch_name")
    nu_power = fit_power_law(
        thermal_ready_rows,
        "nu_effective",
        "re_effective",
        "branch_name",
        "branch_aware_re_power_law",
        robust=False,
    )
    nu_status, nu_model, nu_reason = choose_nu_status(thermal_ready_rows, nu_power)

    sensitivity_rows: list[dict[str, Any]] = []
    for row in straight_sensitivity_rows:
        sensitivity_rows.append(dict(row))
    sensitivity_rows.extend(sensitivity_rows_from_thermal_case_rows(thermal_case_rows))
    sensitivity_rows.append(
        {
            "asset_family": "feature_keff",
            "sensitivity_name": "full_path_hydro_integral",
            "status": "not_run",
            "base_row_count": "",
            "sensitivity_row_count": "",
            "row_count_delta": "",
            "qualitative_conclusion_changed": "",
            "row_count": 0,
            "case_count": 0,
            "branch_names": "",
            "note": "defended feature-path hydro-integral rows do not exist in the current additive stack",
        }
    )

    provenance_rows = [
        {
            "output_table": "hydraulic_fit_ready_rows.csv",
            "column_name": "target_value",
            "purpose": "defended straight-section friction target",
            "source_files": "reports/2026-06-19_ethan_salt_straight_hydraulic_sensitivity/straight_fit_ready_rows.csv",
            "source_columns": "friction_target_value",
            "transformation_formula": "direct carry-through from the bounded straight sensitivity package",
            "units": "Darcy friction factor [-]",
            "sign_convention": "positive dissipative straight-section friction only",
            "validity_gates": "fit_use_status == fit_used",
            "known_failure_modes": "late-window stability remains blocked because retained-time defended hydro rows are not preserved",
        },
        {
            "output_table": "thermal_fit_ready_rows.csv",
            "column_name": "nu_effective",
            "purpose": "direct-branch Salt Nu target admitted under the v3 moderate closure policy",
            "source_files": "reports/2026-06-19_ethan_salt_thermal_closure_hardening_v3/thermal_fit_ready_rows.csv",
            "source_columns": "mean_nu_effective",
            "transformation_formula": "direct carry-through from branch-level thermal closure rows",
            "units": "Nusselt number [-]",
            "sign_convention": "positive effective Nu only",
            "validity_gates": "fit_use_status == fit_used, right_leg excluded, upcomer excluded",
            "known_failure_modes": "domain is limited to the direct branches surviving the moderate residual gate",
        },
        {
            "output_table": "salt_feature_keff_fit_results.json",
            "column_name": "recommended_status",
            "purpose": "feature K_eff recommendation state",
            "source_files": "reports/2026-06-19_ethan_salt_feature_path_hydraulic_hardening/feature_case_summary.csv",
            "source_columns": "pressure_method_status, fit_use_status",
            "transformation_formula": "explicit refusal when no full-path-defended feature rows exist",
            "units": "n/a",
            "sign_convention": "n/a",
            "validity_gates": "requires at least one full_path_defended feature row to move beyond refusal",
            "known_failure_modes": "proxy-only rows may look numerically stable but are still not path-defended",
        },
    ]

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(output_dir / "hydraulic_fit_ready_rows.csv", hydraulic_fit_ready_rows)
    csv_dump_rows(
        output_dir / "hydraulic_exclusion_summary.csv",
        [
            {
                "asset_family": "feature_keff",
                "fit_use_status": "excluded",
                "exclusion_reason_primary": "missing_full_path_density_integral",
                "row_count": len(feature_case_rows),
            }
        ],
    )
    csv_dump_rows(output_dir / "thermal_fit_ready_rows.csv", thermal_ready_rows)
    csv_dump_rows(
        output_dir / "thermal_exclusion_summary.csv",
        [
            {
                "asset_family": "thermal_branch",
                "fit_use_status": status,
                "exclusion_reason_primary": reason,
                "row_count": count,
            }
            for (status, reason), count in sorted(
                Counter((row["fit_use_status"], row["exclusion_reason_primary"]) for row in thermal_case_rows if row["fit_use_status"] != "fit_used").items()
            )
        ],
    )
    write_json(
        output_dir / "salt_friction_fit_results.json",
        {
            "recommended_status": straight_status,
            "recommended_model": "class_aware_re_power_law" if straight_status == "provisional_defended" else "not_defensible_yet",
            "fit_used_row_count": len(hydraulic_fit_ready_rows),
            "constant_model": straight_constant,
            "power_law_model": straight_power,
            "late_window_status": next(
                (row["status"] for row in straight_sensitivity_rows if row["sensitivity_name"] == "late_window_choice"),
                "unknown",
            ),
        },
    )
    write_json(output_dir / "salt_feature_keff_fit_results.json", feature_fit_result)
    write_json(
        output_dir / "salt_nu_fit_results.json",
        {
            "recommended_status": nu_status,
            "recommended_model": nu_model,
            "fit_used_row_count": len(thermal_ready_rows),
            "domain_branch_names": sorted({row["branch_name"] for row in thermal_ready_rows}),
            "domain_case_count": len({row["source_id"] for row in thermal_ready_rows}),
            "reason": nu_reason,
            "constant_model": nu_constant,
            "power_law_model": nu_power,
        },
    )
    sensitivity_fieldnames = [
        "asset_family",
        "sensitivity_name",
        "status",
        "base_row_count",
        "sensitivity_row_count",
        "row_count_delta",
        "qualitative_conclusion_changed",
        "row_count",
        "case_count",
        "branch_names",
        "note",
    ]
    csv_dump_rows(output_dir / "sensitivity_summary.csv", sensitivity_rows, sensitivity_fieldnames)
    csv_dump_rows(output_dir / "provenance_map.csv", provenance_rows)

    handoff = f"""# Salt Model Dependency Handoff v3

## Straight-section friction

- status: `{straight_status}`
- fit-used rows: `{len(hydraulic_fit_ready_rows)}`
- model: `class_aware_re_power_law`
- boundary: still limited by missing retained-time hydro-corrected late-window sensitivity

## Feature K_eff

- status: `not_defensible_yet`
- fit-used rows: `0`
- reason: full feature-path hydro closure remains unavailable in the additive artifact stack

## Salt HTC/Nu

- status: `{nu_status}`
- fit-used rows: `{len(thermal_ready_rows)}`
- model: `{nu_model}`
- domain branches: `{", ".join(sorted({row["branch_name"] for row in thermal_ready_rows})) if thermal_ready_rows else "none"}`
- boundary: only the direct closure-supported branch subset is admissible
"""
    (output_dir / "model_dependency_handoff.md").write_text(handoff, encoding="utf-8")

    readme = f"""# Ethan Salt Model Dependency Package v3

Generated: `2026-06-19`

## Purpose

This package rebuilds the Salt model-dependency layer after the new v3 thermal
hardening pass and the stricter feature-path blocker audit.

## Current status

- straight-section friction: `{straight_status}`
- feature `K_eff`: `not_defensible_yet`
- Salt Nu: `{nu_status}`

## Row counts

- hydraulic fit-used rows: `{len(hydraulic_fit_ready_rows)}`
- thermal fit-used rows: `{len(thermal_ready_rows)}`
- proxy-positive but non-defended feature rows: `{len(feature_proxy_positive)}`

## Important boundary

Feature `K_eff` is intentionally refused here until a real full-path hydraulic
closure exists. Salt Nu may be admitted only on the limited direct-branch
domain documented in `salt_nu_fit_results.json`.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    summary = {
        "generated_at": iso_timestamp(),
        "hydraulic_fit_used_count": len(hydraulic_fit_ready_rows),
        "thermal_fit_used_count": len(thermal_ready_rows),
        "feature_fit_used_count": 0,
        "straight_section_status": straight_status,
        "feature_status": "not_defensible_yet",
        "thermal_status": nu_status,
    }
    write_json(output_dir / "summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
