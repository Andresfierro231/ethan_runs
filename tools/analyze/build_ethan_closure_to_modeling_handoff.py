#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import ROOT, csv_dump_rows, load_csv_rows, write_json

SALT_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_model_dependency_package_v3"
WATER_DIR = ROOT / "reports" / "2026-06-19_ethan_water_readiness_handoff"
FEATURE_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_feature_path_hydraulic_hardening"
THERMAL_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_thermal_closure_hardening_v3"
STRAIGHT_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_straight_hydraulic_sensitivity"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-19_ethan_closure_to_modeling_handoff"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the final closure-to-modeling handoff package.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    salt_summary = load_csv_rows(SALT_DIR / "hydraulic_fit_ready_rows.csv")
    salt_thermal = load_csv_rows(SALT_DIR / "thermal_fit_ready_rows.csv")
    water_rollup = load_csv_rows(WATER_DIR / "water_readiness_rollup.csv")
    salt_feature_rows = load_csv_rows(FEATURE_DIR / "feature_case_summary.csv")
    salt_thermal_all_rows = load_csv_rows(THERMAL_DIR / "thermal_closure_by_case.csv")
    salt_straight_all_rows = load_csv_rows(STRAIGHT_DIR / "straight_fit_ready_rows.csv")

    exact_fit_rows = []
    for row in salt_summary:
        exact_fit_rows.append(
            {
                "asset_family": row["asset_family"],
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "domain_name": row["category_name"],
                "target_value": row["target_value"],
            }
        )
    for row in salt_thermal:
        exact_fit_rows.append(
            {
                "asset_family": "salt_nu",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "domain_name": row["branch_name"],
                "target_value": row["nu_effective"],
            }
        )

    blocked_rows = [
        {
            "dependency_or_gap": "feature_keff_full_path_closure",
            "current_status": "not_defensible_yet",
            "missing_requirement": "full feature-path hydro closure beyond proxy endpoint evidence",
        },
        {
            "dependency_or_gap": "water_dependency_package",
            "current_status": "readiness_only",
            "missing_requirement": "closure-gated Water thermal and feature hardening before any Water dependency fit",
        },
    ]
    excluded_rows = []
    for row in salt_feature_rows:
        excluded_rows.append(
            {
                "asset_family": "feature_keff",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "domain_name": row["feature_name"],
                "fit_use_status": row["fit_use_status"],
                "exclusion_reason_primary": row["exclusion_reason_primary"],
            }
        )
    for row in salt_thermal_all_rows:
        if row["fit_use_status"] == "fit_used":
            continue
        excluded_rows.append(
            {
                "asset_family": "salt_nu",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "domain_name": row["branch_name"],
                "fit_use_status": row["fit_use_status"],
                "exclusion_reason_primary": row["exclusion_reason_primary"],
            }
        )
    for row in salt_straight_all_rows:
        if row["fit_use_status"] == "fit_used":
            continue
        excluded_rows.append(
            {
                "asset_family": "straight_section_friction",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "domain_name": row["section_name"],
                "fit_use_status": row["fit_use_status"],
                "exclusion_reason_primary": row.get("exclusion_reason_primary", ""),
            }
        )

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(output_dir / "exact_fit_used_rows.csv", exact_fit_rows)
    csv_dump_rows(output_dir / "exact_excluded_rows.csv", excluded_rows)
    csv_dump_rows(output_dir / "blocked_dependency_requirements.csv", blocked_rows)
    csv_dump_rows(output_dir / "water_readiness_rollup.csv", water_rollup)

    salt_text = """# Salt Final Dependency Conclusions

Generated: `2026-06-19`

- straight-section friction remains usable with explicit caveats
- feature `K_eff` is refused until a full-path hydraulic method exists
- Salt Nu is limited to the direct branch domain that survives the v3 closure gate
"""
    water_text = """# Water Readiness Conclusions

Generated: `2026-06-19`

Water remains at a readiness stage. The new thermal and feature readiness
packages identify where the next closure work should begin, but no defended
Water dependency is claimed here.
"""
    (output_dir / "salt_final_dependency_conclusions.md").write_text(salt_text, encoding="utf-8")
    (output_dir / "water_readiness_conclusions.md").write_text(water_text, encoding="utf-8")
    (output_dir / "future_upstream_requirements.md").write_text(
        "# Future Upstream Requirements\n\n- full feature-path hydro closure\n- retained-time defended straight hydraulic rows\n- further Water closure hardening before Water fitting\n",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        "# Closure-to-Modeling Handoff\n\nGenerated: `2026-06-19`\n\nThis package is the final synthesis layer for the current Salt-first closure campaign with parallel Water readiness.\n",
        encoding="utf-8",
    )
    summary = {
        "generated_at": iso_timestamp(),
        "salt_fit_row_count": len(exact_fit_rows),
        "water_readiness_rollup_count": len(water_rollup),
    }
    write_json(output_dir / "summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
