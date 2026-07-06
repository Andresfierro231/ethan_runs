#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump

V2_DIR = WORKSPACE_ROOT / "reports" / "2026-06-19_ethan_salt_model_dependency_package_v2"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-19_ethan_salt_conclusions_package"


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_dump_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    csv_dump(path, fieldnames, rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the additive Salt conclusions package from the v2 dependency handoff."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Optional bounded rebuild of one or more Salt source IDs.",
    )
    return parser.parse_args()


def filter_rows(rows: list[dict[str, str]], source_ids: set[str] | None) -> list[dict[str, str]]:
    if not source_ids:
        return rows
    return [row for row in rows if row.get("source_id") in source_ids]


def scientific_use_label(status: str) -> str:
    if status == "provisional_defended":
        return "usable_with_explicit_caveats"
    return "do_not_use_for_final_modeling"


def caveat_level(status: str) -> str:
    if status == "provisional_defended":
        return "high"
    return "blocking"


def sensitivity_class(row: dict[str, str]) -> str:
    if row["status"] != "run":
        return "not_run"
    return "fragile" if row["qualitative_conclusion_changed"] == "yes" else "robust"


def build_dependency_status_rows(
    summary: dict[str, Any],
    friction_results: dict[str, Any],
    nu_results: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "asset_family": "straight_section_friction",
            "recommended_status": friction_results["straight_section_dependency"]["recommended_status"],
            "recommended_model": friction_results["straight_section_dependency"]["recommended_model"],
            "fit_used_row_count": friction_results["straight_section_dependency"]["fit_used_row_count"],
            "scientific_use_label": scientific_use_label(friction_results["straight_section_dependency"]["recommended_status"]),
            "caveat_level": caveat_level(friction_results["straight_section_dependency"]["recommended_status"]),
            "primary_basis": "hydro-corrected direct section pressure loss on lower_leg and test_section_span only",
            "primary_limit": "strict direct/shear sensitivity changes row count and the defended subset excludes buoyancy-aided sections",
        },
        {
            "asset_family": "feature_keff",
            "recommended_status": friction_results["feature_dependency"]["recommended_status"],
            "recommended_model": friction_results["feature_dependency"]["recommended_model"],
            "fit_used_row_count": friction_results["feature_dependency"]["fit_used_row_count"],
            "scientific_use_label": scientific_use_label(friction_results["feature_dependency"]["recommended_status"]),
            "caveat_level": caveat_level(friction_results["feature_dependency"]["recommended_status"]),
            "primary_basis": "patch-endpoint p_rgh plus local boundary-reference excess loss for corner_upper_right and test_section_complex",
            "primary_limit": "full feature-path hydro integral is still missing, so the defended feature fit remains provisional",
        },
        {
            "asset_family": "salt_nu",
            "recommended_status": nu_results["recommended_status"],
            "recommended_model": nu_results["recommended_model"],
            "fit_used_row_count": nu_results["fit_used_row_count"],
            "scientific_use_label": scientific_use_label(nu_results["recommended_status"]),
            "caveat_level": caveat_level(nu_results["recommended_status"]),
            "primary_basis": "exact retained-time section-integral Nu with branch-level closure gating",
            "primary_limit": "only two direct thermal rows survive closure, so no defended Salt Nu dependency is publishable",
        },
    ]


def build_exact_fit_used_rows(
    hydraulic_rows: list[dict[str, str]],
    thermal_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for row in hydraulic_rows:
        rows_out.append(
            {
                "asset_family": row["asset_family"],
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "entity_name": row["category_name"],
                "entity_class": row["category_class"],
                "re_effective": row["re_effective"],
                "target_value": row["target_value"],
                "target_units": "1",
                "method_status": row.get("pressure_method_status", ""),
                "fit_scope": "fit_used",
            }
        )
    for row in thermal_rows:
        rows_out.append(
            {
                "asset_family": "salt_nu",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "entity_name": row["branch_name"],
                "entity_class": row["branch_type"],
                "re_effective": row["mean_re_effective"],
                "target_value": row["mean_nu_effective"],
                "target_units": "1",
                "method_status": "closure_supported",
                "fit_scope": "fit_used",
            }
        )
    return rows_out


def build_case_contribution_rows(exact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    case_labels: dict[str, str] = {}
    for row in exact_rows:
        source_id = str(row["source_id"])
        case_labels[source_id] = str(row["case_label"])
        grouped[(source_id, case_labels[source_id])][str(row["asset_family"])] += 1
    rows_out = []
    for (source_id, case_label), counts in sorted(grouped.items()):
        rows_out.append(
            {
                "source_id": source_id,
                "case_label": case_label,
                "straight_section_friction_row_count": counts.get("straight_section_friction", 0),
                "feature_keff_row_count": counts.get("feature_keff", 0),
                "salt_nu_row_count": counts.get("salt_nu", 0),
                "total_fit_used_rows": sum(counts.values()),
            }
        )
    return rows_out


def build_exclusion_rollup_rows(
    hydraulic_exclusions: list[dict[str, str]],
    thermal_exclusions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows_out = []
    for row in hydraulic_exclusions + thermal_exclusions:
        asset_family = row["asset_family"]
        reason = row["exclusion_reason_primary"]
        effect = (
            "removes rows from defended hydraulic dependency use"
            if asset_family != "thermal_branch"
            else "removes rows from defended Salt Nu use"
        )
        rows_out.append(
            {
                "asset_family": asset_family,
                "fit_use_status": row["fit_use_status"],
                "exclusion_reason_primary": reason,
                "row_count": row["row_count"],
                "scientific_effect": effect,
            }
        )
    return rows_out


def build_sensitivity_interpretation_rows(sensitivity_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows_out = []
    for row in sensitivity_rows:
        rows_out.append(
            {
                "asset_family": row["asset_family"],
                "sensitivity_name": row["sensitivity_name"],
                "status": row["status"],
                "robustness_class": sensitivity_class(row),
                "base_row_count": row["base_row_count"],
                "sensitivity_row_count": row["sensitivity_row_count"],
                "base_model_status": row["base_model_status"],
                "sensitivity_model_status": row["sensitivity_model_status"],
                "qualitative_conclusion_changed": row["qualitative_conclusion_changed"],
                "plain_language_interpretation": row["note"],
            }
        )
    return rows_out


def build_blocked_requirement_rows() -> list[dict[str, Any]]:
    return [
        {
            "dependency_or_gap": "feature_keff_full_path_closure",
            "current_status": "provisional_defended",
            "missing_requirement": "retained-time feature-path hydro-integral or equivalent direct pathwise closure, not just patch-endpoint p_rgh plus local straight reference",
            "why_it_matters": "removes the main remaining method caveat on the defended feature K_eff fit",
            "current_bias_risk": "feature excess may be over- or under-attributed when the local boundary reference is not a faithful proxy for the full feature path",
            "next_owning_work_type": "upstream extractor hardening",
        },
        {
            "dependency_or_gap": "salt_nu_defended_dependency",
            "current_status": "not_defensible_yet",
            "missing_requirement": "more direct closure-supported thermal rows plus stronger separation between intended transfer, parasitic wall loss, junction exchange, and residual imbalance",
            "why_it_matters": "without more closure-supported rows the Salt Nu fit is underdetermined and not trustworthy",
            "current_bias_risk": "residual heat imbalance could be misread as fluid-side Nu behavior",
            "next_owning_work_type": "thermal closure hardening",
        },
        {
            "dependency_or_gap": "hydraulic_late_window_sensitivity",
            "current_status": "not_run",
            "missing_requirement": "retained-time defended straight-section hydraulic rows instead of case-level means only",
            "why_it_matters": "needed to show whether the defended friction model is stable to late-window selection",
            "current_bias_risk": "temporal averaging may hide sensitivity in the admitted hydraulic subset",
            "next_owning_work_type": "upstream or intermediate defended-row rebuild",
        },
    ]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""# Salt Conclusions Package

Generated: `2026-06-19`

## Purpose

This package translates the additive Salt hardening v2 outputs into a final
scientific handoff that states what is currently defendable, what remains only
provisional, what is still blocked, and exactly which rows support those
claims.

## Current defended state

- straight-section friction: `{summary["straight_section_status"]}`
- feature `K_eff`: `{summary["feature_status"]}`
- Salt HTC/Nu: `{summary["thermal_status"]}`

## Row counts

- exact fit-used hydraulic rows: `{summary["hydraulic_fit_used_count"]}`
- exact fit-used thermal rows: `{summary["thermal_fit_used_count"]}`

## Important boundary

This package does not reopen extraction. It is a conclusions layer on top of
`reports/2026-06-19_ethan_salt_model_dependency_package_v2/`.
""",
        encoding="utf-8",
    )


def write_conclusions(path: Path, dependency_rows: list[dict[str, Any]]) -> None:
    lookup = {row["asset_family"]: row for row in dependency_rows}
    path.write_text(
        f"""# Salt Scientific Conclusions

## Straight-section friction

- status: `{lookup["straight_section_friction"]["recommended_status"]}`
- recommended use: `{lookup["straight_section_friction"]["scientific_use_label"]}`
- model: `{lookup["straight_section_friction"]["recommended_model"]}`
- conclusion: use only on the defended lower-leg and test-section straight subset, and keep the strict direct/shear sensitivity caveat visible.

## Feature K_eff

- status: `{lookup["feature_keff"]["recommended_status"]}`
- recommended use: `{lookup["feature_keff"]["scientific_use_label"]}`
- model: `{lookup["feature_keff"]["recommended_model"]}`
- conclusion: current feature K_eff is usable only with an explicit statement that it is based on a local boundary-reference proxy rather than a full feature-path hydro integral.

## Salt HTC/Nu

- status: `{lookup["salt_nu"]["recommended_status"]}`
- recommended use: `{lookup["salt_nu"]["scientific_use_label"]}`
- model: `{lookup["salt_nu"]["recommended_model"]}`
- conclusion: do not publish a defended Salt Nu dependency yet; only two direct rows survive closure, both on left_lower_leg.
""",
        encoding="utf-8",
    )


def write_upstream_requirements(path: Path, blocked_rows: list[dict[str, Any]]) -> None:
    lines = ["# Upstream Method Requirements", ""]
    for row in blocked_rows:
        lines.extend(
            [
                f"## {row['dependency_or_gap']}",
                f"- current status: `{row['current_status']}`",
                f"- missing requirement: {row['missing_requirement']}",
                f"- why it matters: {row['why_it_matters']}",
                f"- current bias risk: {row['current_bias_risk']}",
                f"- next owning work type: `{row['next_owning_work_type']}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None

    summary = json.loads((V2_DIR / "summary.json").read_text(encoding="utf-8"))
    friction_results = json.loads((V2_DIR / "salt_friction_fit_results.json").read_text(encoding="utf-8"))
    nu_results = json.loads((V2_DIR / "salt_nu_fit_results.json").read_text(encoding="utf-8"))
    hydraulic_rows = filter_rows(load_csv_rows(V2_DIR / "hydraulic_fit_ready_rows.csv"), source_ids)
    thermal_rows = filter_rows(load_csv_rows(V2_DIR / "thermal_fit_ready_rows.csv"), source_ids)
    hydraulic_exclusions = load_csv_rows(V2_DIR / "hydraulic_exclusion_summary.csv")
    thermal_exclusions = load_csv_rows(V2_DIR / "thermal_exclusion_summary.csv")
    sensitivity_rows = load_csv_rows(V2_DIR / "sensitivity_summary.csv")

    dependency_rows = build_dependency_status_rows(summary, friction_results, nu_results)
    exact_rows = build_exact_fit_used_rows(hydraulic_rows, thermal_rows)
    case_rows = build_case_contribution_rows(exact_rows)
    exclusion_rows = build_exclusion_rollup_rows(hydraulic_exclusions, thermal_exclusions)
    sensitivity_interpretation_rows = build_sensitivity_interpretation_rows(sensitivity_rows)
    blocked_rows = build_blocked_requirement_rows()

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(
        output_dir / "dependency_status.csv",
        dependency_rows,
        [
            "asset_family",
            "recommended_status",
            "recommended_model",
            "fit_used_row_count",
            "scientific_use_label",
            "caveat_level",
            "primary_basis",
            "primary_limit",
        ],
    )
    csv_dump_rows(
        output_dir / "exact_fit_used_rows.csv",
        exact_rows,
        [
            "asset_family",
            "source_id",
            "case_label",
            "entity_name",
            "entity_class",
            "re_effective",
            "target_value",
            "target_units",
            "method_status",
            "fit_scope",
        ],
    )
    csv_dump_rows(
        output_dir / "case_contribution_summary.csv",
        case_rows,
        [
            "source_id",
            "case_label",
            "straight_section_friction_row_count",
            "feature_keff_row_count",
            "salt_nu_row_count",
            "total_fit_used_rows",
        ],
    )
    csv_dump_rows(
        output_dir / "exclusion_reason_rollup.csv",
        exclusion_rows,
        [
            "asset_family",
            "fit_use_status",
            "exclusion_reason_primary",
            "row_count",
            "scientific_effect",
        ],
    )
    csv_dump_rows(
        output_dir / "sensitivity_interpretation.csv",
        sensitivity_interpretation_rows,
        [
            "asset_family",
            "sensitivity_name",
            "status",
            "robustness_class",
            "base_row_count",
            "sensitivity_row_count",
            "base_model_status",
            "sensitivity_model_status",
            "qualitative_conclusion_changed",
            "plain_language_interpretation",
        ],
    )
    csv_dump_rows(
        output_dir / "blocked_dependency_requirements.csv",
        blocked_rows,
        [
            "dependency_or_gap",
            "current_status",
            "missing_requirement",
            "why_it_matters",
            "current_bias_risk",
            "next_owning_work_type",
        ],
    )

    final_summary = {
        "generated_at": iso_timestamp(),
        "source_dependency_package": str(V2_DIR.relative_to(WORKSPACE_ROOT)),
        "case_count": len({row["source_id"] for row in exact_rows}),
        "hydraulic_fit_used_count": len([row for row in exact_rows if row["asset_family"] != "salt_nu"]),
        "thermal_fit_used_count": len([row for row in exact_rows if row["asset_family"] == "salt_nu"]),
        "straight_section_status": summary["straight_section_status"],
        "feature_status": summary["feature_status"],
        "thermal_status": summary["thermal_status"],
    }
    json_dump(output_dir / "summary.json", final_summary)
    write_readme(output_dir / "README.md", final_summary)
    write_conclusions(output_dir / "salt_dependency_conclusions.md", dependency_rows)
    write_upstream_requirements(output_dir / "upstream_requirements.md", blocked_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
