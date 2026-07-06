#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import ROOT, csv_dump_rows, finite_float, load_csv_rows, write_json

V3_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_model_dependency_package_v3"
STRAIGHT_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_straight_hydraulic_sensitivity"
FEATURE_DIR = ROOT / "reports" / "2026-06-22_ethan_salt_feature_path_hydraulic_hardening_v2"
THERMAL_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_thermal_closure_hardening_v3"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-22_ethan_salt_model_dependency_package_v4"
FEATURE_STABILITY_MIN = 0.75
FEATURE_CASE_MIN = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the Salt v4 model-dependency package using the June 22 feature "
            "path decomposition while reusing the defended June 19 straight and "
            "thermal fit lanes."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    return parser.parse_args()


def filter_rows(rows: list[dict[str, str]], source_ids: set[str] | None) -> list[dict[str, str]]:
    if not source_ids:
        return rows
    return [row for row in rows if row.get("source_id") in source_ids]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def geometric_constant_fit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        target = finite_float(row.get("target_value"))
        if target > 0.0:
            grouped[str(row["category_name"])].append(math.log(target))
    if not grouped:
        return {"status": "not_fit", "reason": "no_positive_rows"}
    coefficient_names: list[str] = []
    coefficients: list[float] = []
    residuals: list[float] = []
    observed_logs: list[float] = []
    for category_name in sorted(grouped):
        values = grouped[category_name]
        center = sum(values) / len(values)
        coefficient_names.append(f"group:{category_name}")
        coefficients.append(center)
        residuals.extend(value - center for value in values)
        observed_logs.extend(values)
    rmse_log = math.sqrt(sum(value * value for value in residuals) / len(residuals))
    mae_log = sum(abs(value) for value in residuals) / len(residuals)
    observed_mean = sum(observed_logs) / len(observed_logs)
    tss = sum((value - observed_mean) ** 2 for value in observed_logs)
    rss = sum(value * value for value in residuals)
    return {
        "status": "fit",
        "model_type": "geometric_constant",
        "row_count": len(observed_logs),
        "coefficient_names": coefficient_names,
        "coefficients": coefficients,
        "rmse_log": rmse_log,
        "mae_log": mae_log,
        "r2_log": 1.0 - rss / tss if tss > 0.0 else 0.0,
    }


def stable_feature_fit_rows(feature_case_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, float]]:
    fit_rows = [row for row in feature_case_rows if row["fit_use_status"] == "fit_used"]
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    total_by_name: Counter[str] = Counter(row["feature_name"] for row in feature_case_rows)
    for row in fit_rows:
        by_name[row["feature_name"]].append(row)
    stability = {
        feature_name: len(rows) / max(total_by_name[feature_name], 1)
        for feature_name, rows in by_name.items()
    }
    stable_names = {
        feature_name
        for feature_name, fraction in stability.items()
        if fraction >= FEATURE_STABILITY_MIN and len(by_name[feature_name]) >= FEATURE_CASE_MIN
    }
    normalized: list[dict[str, Any]] = []
    for row in fit_rows:
        if row["feature_name"] not in stable_names:
            continue
        normalized.append(
            {
                "asset_family": "feature_keff",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "category_name": row["feature_name"],
                "category_class": row["feature_class"],
                "re_effective": finite_float(row.get("mean_re_effective")),
                "target_value": finite_float(row.get("mean_keff_effective_path")),
                "pressure_method_status": "defended_patch_endpoint_prgh_local_boundary_reference",
                "support_fraction": finite_float(row.get("support_fraction_min")),
                "positive_time_fraction": finite_float(row.get("positive_time_fraction")),
            }
        )
    return normalized, stability


def choose_feature_status(feature_rows: list[dict[str, Any]], fit_result: dict[str, Any]) -> tuple[str, str, str]:
    if len(feature_rows) < FEATURE_CASE_MIN:
        return "not_defensible_yet", "exploratory_screened_only_model", "fewer_than_four_stable_feature_rows"
    if len({row["source_id"] for row in feature_rows}) < FEATURE_CASE_MIN:
        return "not_defensible_yet", "exploratory_screened_only_model", "fewer_than_four_cases"
    if len({row["category_name"] for row in feature_rows}) < 2:
        return "not_defensible_yet", "exploratory_screened_only_model", "single_feature_family_only"
    if fit_result.get("status") != "fit":
        return "not_defensible_yet", "exploratory_screened_only_model", "fit_not_stable"
    return "provisional_defended", fit_result["model_type"], "stable_patch_endpoint_prgh_local_boundary_reference"


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None

    straight_fit_rows = filter_rows(load_csv_rows(STRAIGHT_DIR / "straight_fit_ready_rows.csv"), source_ids)
    straight_sensitivity_rows = load_csv_rows(STRAIGHT_DIR / "straight_sensitivity_runs.csv")
    feature_case_rows = filter_rows(load_csv_rows(FEATURE_DIR / "feature_case_summary.csv"), source_ids)
    thermal_case_rows = filter_rows(load_csv_rows(THERMAL_DIR / "thermal_closure_by_case.csv"), source_ids)
    thermal_fit_rows = filter_rows(load_csv_rows(THERMAL_DIR / "thermal_fit_ready_rows.csv"), source_ids)

    prior_friction = load_json(V3_DIR / "salt_friction_fit_results.json")
    prior_nu = load_json(V3_DIR / "salt_nu_fit_results.json")
    feature_model_rows, feature_stability = stable_feature_fit_rows(feature_case_rows)
    feature_constant = geometric_constant_fit(feature_model_rows)
    feature_status, feature_model, feature_reason = choose_feature_status(feature_model_rows, feature_constant)

    feature_fit_result = {
        "recommended_status": feature_status,
        "recommended_model": feature_model,
        "fit_used_row_count": len(feature_model_rows),
        "stable_feature_names": sorted({row["category_name"] for row in feature_model_rows}),
        "stable_case_count": len({row["source_id"] for row in feature_model_rows}),
        "feature_stability": feature_stability,
        "reason": feature_reason,
        "constant_model": feature_constant,
    }

    sensitivity_rows: list[dict[str, Any]] = []
    for row in straight_sensitivity_rows:
        sensitivity_rows.append(dict(row))
    sensitivity_rows.append(
        {
            "asset_family": "feature_keff",
            "sensitivity_name": "path_basis_upgrade",
            "status": "run",
            "base_row_count": "",
            "sensitivity_row_count": len(feature_model_rows),
            "row_count_delta": "",
            "qualitative_conclusion_changed": "yes",
            "row_count": len(feature_model_rows),
            "case_count": len({row["source_id"] for row in feature_model_rows}),
            "branch_names": "|".join(sorted({row["category_name"] for row in feature_model_rows})),
            "note": "Feature K_eff now uses defended patch-endpoint p versus p_rgh decomposition plus the same local-boundary straight reference.",
        }
    )

    provenance_rows = [
        {
            "output_table": "salt_friction_fit_results.json",
            "column_name": "recommended_status",
            "purpose": "carried-forward straight friction recommendation",
            "source_files": "reports/2026-06-19_ethan_salt_model_dependency_package_v3/salt_friction_fit_results.json",
            "source_columns": "recommended_status, recommended_model, power_law_model",
            "transformation_formula": "direct carry-through because the straight hydraulic lane has not been refreshed yet",
            "units": "n/a",
            "sign_convention": "n/a",
            "validity_gates": "unchanged until the post-continuation straight sensitivity refresh lands",
            "known_failure_modes": "late-window straight sensitivity remains an open continuation-dependent task",
        },
        {
            "output_table": "salt_feature_keff_fit_results.json",
            "column_name": "recommended_status",
            "purpose": "feature K_eff recommendation state",
            "source_files": "reports/2026-06-22_ethan_salt_feature_path_hydraulic_hardening_v2/feature_case_summary.csv",
            "source_columns": "mean_keff_effective_path, fit_use_status",
            "transformation_formula": "stable feature names are promoted only when the retained-time path decomposition is defended and the per-feature case fraction remains high enough",
            "units": "n/a",
            "sign_convention": "positive dissipative feature excess only",
            "validity_gates": "requires patch-endpoint p versus p_rgh path support and local-boundary reference support",
            "known_failure_modes": "the local straight reference is still a boundary proxy rather than a continuous field integral",
        },
        {
            "output_table": "salt_nu_fit_results.json",
            "column_name": "recommended_status",
            "purpose": "carried-forward Salt Nu recommendation",
            "source_files": "reports/2026-06-19_ethan_salt_model_dependency_package_v3/salt_nu_fit_results.json",
            "source_columns": "recommended_status, recommended_model, power_law_model",
            "transformation_formula": "direct carry-through because the thermal hardening lane has not changed in this task slice",
            "units": "n/a",
            "sign_convention": "n/a",
            "validity_gates": "unchanged until a broader direct-branch thermal hardening refresh lands",
            "known_failure_modes": "direct Nu remains limited to left_lower_leg",
        },
    ]

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(
        output_dir / "hydraulic_fit_ready_rows.csv",
        [
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
            for row in straight_fit_rows
        ],
    )
    csv_dump_rows(output_dir / "feature_fit_ready_rows.csv", feature_model_rows)
    csv_dump_rows(
        output_dir / "thermal_fit_ready_rows.csv",
        [
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
            for row in thermal_fit_rows
        ],
    )
    csv_dump_rows(
        output_dir / "hydraulic_exclusion_summary.csv",
        [
            {
                "asset_family": "feature_keff",
                "fit_use_status": status,
                "exclusion_reason_primary": reason,
                "row_count": count,
            }
            for (status, reason), count in sorted(
                Counter((row["fit_use_status"], row["exclusion_reason_primary"]) for row in feature_case_rows if row["fit_use_status"] != "fit_used").items()
            )
        ],
    )
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
    write_json(output_dir / "salt_friction_fit_results.json", prior_friction)
    write_json(output_dir / "salt_feature_keff_fit_results.json", feature_fit_result)
    write_json(output_dir / "salt_nu_fit_results.json", prior_nu)
    sensitivity_columns = [
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
        "base_model_status",
        "sensitivity_model_status",
        "base_log_re_slope",
        "sensitivity_log_re_slope",
        "log_re_slope_delta",
        "base_rmse_log",
        "sensitivity_rmse_log",
    ]
    csv_dump_rows(output_dir / "sensitivity_summary.csv", sensitivity_rows, sensitivity_columns)
    csv_dump_rows(output_dir / "provenance_map.csv", provenance_rows)

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len({row["source_id"] for row in feature_case_rows}),
        "hydraulic_fit_used_count": len(straight_fit_rows),
        "feature_fit_used_count": len(feature_model_rows),
        "thermal_fit_used_count": len(thermal_fit_rows),
        "straight_section_status": prior_friction["recommended_status"],
        "feature_status": feature_status,
        "thermal_status": prior_nu["recommended_status"],
    }
    write_json(output_dir / "summary.json", summary)

    readme = f"""# Ethan Salt Model Dependency Package v4

Generated: `2026-06-22`

## What changed from v3

This package keeps the June 19 straight and thermal dependency recommendations
unchanged, but reopens the feature lane using the June 22 defended patch-endpoint
path decomposition.

## Counts

- hydraulic fit-used rows: `{len(straight_fit_rows)}`
- feature fit-used rows: `{len(feature_model_rows)}`
- thermal fit-used rows: `{len(thermal_fit_rows)}`

## Recommendation status

- straight-section friction: `{prior_friction["recommended_status"]}`
- feature `K_eff`: `{feature_status}`
- Salt HTC/Nu: `{prior_nu["recommended_status"]}`

## Important limitations

- Feature `K_eff` is reopened on a defended patch-endpoint path basis, but the
  straight subtraction is still the bounded local-boundary reference rather than
  a continuous field integral through the feature volume.
- Direct Nu remains limited to the surviving left-lower-leg direct domain.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
