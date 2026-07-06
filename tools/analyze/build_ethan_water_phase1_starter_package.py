#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from tools.common import WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, json_dump

WATER_HYD_DIR = WORKSPACE_ROOT / "reports" / "2026-06-18_ethan_water_hydraulic_evidence_subset"
PRESSURE_DIR = WORKSPACE_ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package"
NONDIM_DIR = WORKSPACE_ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "reports" / "2026-06-19_ethan_water_phase1_starter_package"
DIRECT_SPANS = [
    "left_lower_leg",
    "left_upper_leg",
    "lower_leg",
    "right_leg",
    "test_section_span",
    "upper_leg",
]


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_dump_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    csv_dump(path, fieldnames, rows)


def finite_float(value: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return math.nan
    return parsed if math.isfinite(parsed) else math.nan


def safe_mean(values: list[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return sum(payload) / len(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the additive Water phase-1 readiness package from existing water evidence outputs."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Optional bounded rebuild of one or more Water source IDs.",
    )
    return parser.parse_args()


def filter_rows(rows: list[dict[str, str]], source_ids: set[str] | None) -> list[dict[str, str]]:
    if not source_ids:
        return rows
    return [row for row in rows if row.get("source_id") in source_ids or row.get("case_id") in source_ids]


def classify_thermal_phase1(
    branch: str,
    hydraulic_classification: str,
    usable_fraction_mean: float,
    min_dt_min_k: float,
    residual_mean: float,
    sign_consistency_fraction: float,
) -> tuple[str, str]:
    if hydraulic_classification == "excluded":
        return "blocked_hydraulic_exclusion", "hydraulic branch is already excluded in the water evidence subset"
    if usable_fraction_mean >= 0.95 and min_dt_min_k >= 0.20 and sign_consistency_fraction < 0.50:
        return "closure_rebuild_priority", "thermal support is strong but enthalpy-vs-wall sign consistency is poor"
    if usable_fraction_mean >= 0.95 and min_dt_min_k >= 0.10 and residual_mean <= 0.60 and sign_consistency_fraction >= 0.75:
        return "closure_rebuild_candidate", "thermal support exists and closure is moderate enough for the next rebuild pass"
    if usable_fraction_mean >= 0.85 and min_dt_min_k >= 0.10:
        return "support_present_context_only", "thermal support exists but closure is not strong enough for candidate-grade use"
    return "blocked_by_support_or_closure", "thermal support fraction, delta-T support, or closure consistency is too weak"


def classify_water_dependency_readiness(
    hydraulic_candidate_branches: int,
    strong_thermal_spans: int,
) -> list[dict[str, Any]]:
    return [
        {
            "dependency_family": "water_branch_hydraulic_pressure",
            "current_status": "partial_candidate_subset_available" if hydraulic_candidate_branches > 0 else "not_ready",
            "evidence_basis": "existing water hydraulic evidence subset plus pressure closure by section",
            "next_requirement": "retain current branch exclusions and rebuild from the cleaner right_leg/test_section_span/upper_leg subset first",
        },
        {
            "dependency_family": "water_straight_section_friction",
            "current_status": "not_ready_for_defended_fit",
            "evidence_basis": "water pressure closure by section shows only test_section_span stays uniformly positive by case",
            "next_requirement": "rebuild defended water straight-section rows with branch/section-specific hydro closure gates",
        },
        {
            "dependency_family": "water_feature_keff",
            "current_status": "not_started_from_closure_gated_method",
            "evidence_basis": "no additive water feature hardening package exists yet",
            "next_requirement": "repeat the Salt feature local-boundary-reference and then feature-path closure workflow on water",
        },
        {
            "dependency_family": "water_htc_nu",
            "current_status": "support_first_not_dependency_ready" if strong_thermal_spans > 0 else "blocked",
            "evidence_basis": "water section-level thermal support exists, but no defended water closure-gated branch package exists yet",
            "next_requirement": "build the water thermal closure package with exact enthalpy/wall-heat gating before any dependency fit",
        },
    ]


def build_case_context_rows(dashboard_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows_out = []
    for row in dashboard_rows:
        rows_out.append(
            {
                "source_id": row["source_id"],
                "case_label": row["display_label"],
                "final_time_s": row["final_time_s"],
                "heater_power_w": row["heater_power_W"],
                "cooling_power_w": row["cooling_power_W"],
                "outer_insulation_thickness_in": row["three_d_outer_insulation_thickness_in"],
                "cooler_h_w_m2_k": row["cooler_h_W_m2K"],
                "mdot_mean_abs_kg_s": row["mdot_mean_abs_kg_s"],
                "max_branch_temp_delta_k": row["max_branch_temp_delta_k"],
                "package_root": row["package_root"],
            }
        )
    return rows_out


def build_hydraulic_branch_rows(
    family_subset_rows: list[dict[str, str]],
    case_branch_rows: list[dict[str, str]],
    section_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    grouped_branch_screen: dict[str, list[dict[str, str]]] = defaultdict(list)
    grouped_section: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in case_branch_rows:
        grouped_branch_screen[row["branch"]].append(row)
    for row in section_rows:
        if row["family"] == "water":
            grouped_section[row["span_name"]].append(row)

    rows_out = []
    for row in family_subset_rows:
        branch = row["branch"]
        screen_rows = grouped_branch_screen.get(branch, [])
        section_payload = grouped_section.get(branch, [])
        hydro_losses = [finite_float(item["mean_pressure_loss_hydro_pa"]) for item in section_payload]
        finite_losses = [value for value in hydro_losses if math.isfinite(value)]
        rows_out.append(
            {
                "branch": branch,
                "classification": row["classification"],
                "reason_code": row["reason_code"],
                "recommended_use": row["recommended_use"],
                "case_count": row["case_count"],
                "agree_time_fraction_min": row["agree_time_fraction_min"],
                "positive_cumulative_fraction_min": row["positive_cumulative_fraction_min"],
                "direct_support_fraction_min": row["direct_support_fraction_min"],
                "direct_to_shear_ratio_mean": safe_mean([finite_float(item["direct_to_shear_ratio_mean"]) for item in screen_rows]),
                "terminal_direct_prgh_drop_pa_mean": safe_mean([finite_float(item["terminal_direct_prgh_drop_pa"]) for item in screen_rows]),
                "mean_pressure_loss_hydro_pa": safe_mean(finite_losses),
                "positive_hydro_case_count": sum(1 for value in finite_losses if value > 0.0),
                "negative_hydro_case_count": sum(1 for value in finite_losses if value <= 0.0),
                "phase1_readiness_note": row["explanation"],
            }
        )
    return rows_out


def build_thermal_span_rows(
    field_rows: list[dict[str, str]],
    enthalpy_rows: list[dict[str, str]],
    hydraulic_branch_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    hydraulic_lookup = {row["branch"]: row["classification"] for row in hydraulic_branch_rows}
    rows_out = []
    for span in DIRECT_SPANS:
        span_fields = [row for row in field_rows if row["family"] == "water" and row["span_name"] == span]
        by_case_support: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "usable": 0, "dts": []})
        for row in span_fields:
            payload = by_case_support[row["source_id"]]
            payload["total"] += 1
            if row["thermal_support_status"] == "usable":
                payload["usable"] += 1
            delta_t = abs(finite_float(row["delta_t_wall_minus_bulk_k"]))
            if math.isfinite(delta_t):
                payload["dts"].append(delta_t)
        usable_fracs = [payload["usable"] / payload["total"] for payload in by_case_support.values() if payload["total"] > 0]
        min_dt_by_case = [min(payload["dts"]) for payload in by_case_support.values() if payload["dts"]]
        abs_delta_t_all = [abs(finite_float(row["delta_t_wall_minus_bulk_k"])) for row in span_fields if math.isfinite(abs(finite_float(row["delta_t_wall_minus_bulk_k"])))]
        nu_vals = [finite_float(row["nu_local_signed"]) for row in span_fields if math.isfinite(finite_float(row["nu_local_signed"]))]

        enthalpy_span_rows = [row for row in enthalpy_rows if row["family"] == "water" and row["span_name"] == span]
        residuals: list[float] = []
        sign_ok = 0
        sign_total = 0
        for row in enthalpy_span_rows:
            enthalpy = finite_float(row["enthalpy_change_w"])
            wall = finite_float(row["wall_heat_total_w"])
            if math.isfinite(enthalpy) and math.isfinite(wall) and abs(wall) > 1.0e-12:
                residuals.append(abs(enthalpy - wall) / abs(wall))
                enthalpy_sign = "positive" if enthalpy > 1.0e-9 else "negative" if enthalpy < -1.0e-9 else "zero"
                wall_sign = "positive" if wall > 1.0e-9 else "negative" if wall < -1.0e-9 else "zero"
                if enthalpy_sign == wall_sign or "zero" in {enthalpy_sign, wall_sign}:
                    sign_ok += 1
                sign_total += 1

        usable_fraction_mean = safe_mean(usable_fracs)
        min_dt_min_k = min(min_dt_by_case) if min_dt_by_case else math.nan
        residual_mean = safe_mean(residuals)
        sign_consistency_fraction = sign_ok / sign_total if sign_total else math.nan
        classification, reason = classify_thermal_phase1(
            span,
            hydraulic_lookup.get(span, "unknown"),
            usable_fraction_mean,
            min_dt_min_k,
            residual_mean,
            sign_consistency_fraction,
        )
        rows_out.append(
            {
                "span_name": span,
                "hydraulic_classification": hydraulic_lookup.get(span, "unknown"),
                "field_row_count": len(span_fields),
                "case_usable_fraction_mean": usable_fraction_mean,
                "case_usable_fraction_min": min(usable_fracs) if usable_fracs else math.nan,
                "mean_abs_delta_t_wall_bulk_k": safe_mean(abs_delta_t_all),
                "case_min_abs_delta_t_wall_bulk_mean_k": safe_mean(min_dt_by_case),
                "case_min_abs_delta_t_wall_bulk_min_k": min_dt_min_k,
                "mean_nu_local_signed": safe_mean(nu_vals),
                "enthalpy_residual_mean": residual_mean,
                "enthalpy_residual_min": min(residuals) if residuals else math.nan,
                "enthalpy_residual_max": max(residuals) if residuals else math.nan,
                "enthalpy_sign_consistency_fraction": sign_consistency_fraction,
                "phase1_thermal_classification": classification,
                "phase1_thermal_reason": reason,
            }
        )
    return rows_out


def build_bulk_reweight_rows(summary_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows_out = []
    for row in summary_rows:
        rows_out.append(
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "comparison_row_count": row["comparison_row_count"],
                "mean_exact_cp_minus_stored_flow_k": row["mean_exact_cp_minus_stored_flow_k"],
                "max_abs_exact_cp_minus_stored_flow_k": row["max_abs_exact_cp_minus_stored_flow_k"],
                "mean_exact_cp_minus_exact_flow_k": row["mean_exact_cp_minus_exact_flow_k"],
                "max_abs_exact_cp_minus_exact_flow_k": row["max_abs_exact_cp_minus_exact_flow_k"],
                "selection_status_counts": row["selection_status_counts"],
            }
        )
    return rows_out


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""# Water Phase-1 Starter Package

Generated: `2026-06-19`

## Purpose

This package consolidates the existing Water-family hydraulic evidence subset,
pressure-closure outputs, thermal support fields, enthalpy rows, and exact
water bulk-temperature reweighting into a conservative readiness package. It
does **not** claim defended water dependencies.

## Current state

- case count: `{summary["case_count"]}`
- hydraulic candidate branches: `{summary["hydraulic_candidate_branch_count"]}`
- thermal closure-rebuild candidates: `{summary["thermal_candidate_span_count"]}`

## Interpretation boundary

This is a starter package only. It identifies where the next water hardening
work should begin and where the current water evidence is still blocked.
""",
        encoding="utf-8",
    )


def write_handoff(path: Path, dependency_rows: list[dict[str, Any]]) -> None:
    lines = ["# Water Phase-1 Handoff", "", "## Dependency readiness", ""]
    for row in dependency_rows:
        lines.append(f"- `{row['dependency_family']}`: `{row['current_status']}`")
        lines.append(f"  basis: {row['evidence_basis']}")
        lines.append(f"  next: {row['next_requirement']}")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None

    dashboard_rows = filter_rows(load_csv_rows(NONDIM_DIR / "water_dashboard.csv"), source_ids)
    family_subset_rows = load_csv_rows(WATER_HYD_DIR / "water_hydraulic_family_subset.csv")
    case_branch_rows = filter_rows(load_csv_rows(WATER_HYD_DIR / "water_hydraulic_case_branch_screen.csv"), source_ids)
    section_rows = filter_rows(load_csv_rows(PRESSURE_DIR / "pressure_closure_by_section.csv"), source_ids)
    field_rows = filter_rows(load_csv_rows(PRESSURE_DIR / "water_effective_htc_nu_fields.csv"), source_ids)
    enthalpy_rows = filter_rows(load_csv_rows(PRESSURE_DIR / "enthalpy_balance_by_leg.csv"), source_ids)
    reweight_rows = filter_rows(load_csv_rows(PRESSURE_DIR / "water_bulk_temperature_reweight_summary.csv"), source_ids)

    case_context_rows = build_case_context_rows(dashboard_rows)
    hydraulic_branch_rows = build_hydraulic_branch_rows(family_subset_rows, case_branch_rows, section_rows)
    thermal_span_rows = build_thermal_span_rows(field_rows, enthalpy_rows, hydraulic_branch_rows)
    bulk_reweight_rows = build_bulk_reweight_rows(reweight_rows)
    dependency_rows = classify_water_dependency_readiness(
        hydraulic_candidate_branches=sum(1 for row in hydraulic_branch_rows if row["classification"] == "water_family_candidate"),
        strong_thermal_spans=sum(
            1
            for row in thermal_span_rows
            if row["phase1_thermal_classification"] in {"closure_rebuild_candidate", "closure_rebuild_priority"}
        ),
    )

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(
        output_dir / "water_case_context.csv",
        case_context_rows,
        [
            "source_id",
            "case_label",
            "final_time_s",
            "heater_power_w",
            "cooling_power_w",
            "outer_insulation_thickness_in",
            "cooler_h_w_m2_k",
            "mdot_mean_abs_kg_s",
            "max_branch_temp_delta_k",
            "package_root",
        ],
    )
    csv_dump_rows(
        output_dir / "water_hydraulic_branch_readiness.csv",
        hydraulic_branch_rows,
        [
            "branch",
            "classification",
            "reason_code",
            "recommended_use",
            "case_count",
            "agree_time_fraction_min",
            "positive_cumulative_fraction_min",
            "direct_support_fraction_min",
            "direct_to_shear_ratio_mean",
            "terminal_direct_prgh_drop_pa_mean",
            "mean_pressure_loss_hydro_pa",
            "positive_hydro_case_count",
            "negative_hydro_case_count",
            "phase1_readiness_note",
        ],
    )
    csv_dump_rows(
        output_dir / "water_thermal_span_phase1.csv",
        thermal_span_rows,
        [
            "span_name",
            "hydraulic_classification",
            "field_row_count",
            "case_usable_fraction_mean",
            "case_usable_fraction_min",
            "mean_abs_delta_t_wall_bulk_k",
            "case_min_abs_delta_t_wall_bulk_mean_k",
            "case_min_abs_delta_t_wall_bulk_min_k",
            "mean_nu_local_signed",
            "enthalpy_residual_mean",
            "enthalpy_residual_min",
            "enthalpy_residual_max",
            "enthalpy_sign_consistency_fraction",
            "phase1_thermal_classification",
            "phase1_thermal_reason",
        ],
    )
    csv_dump_rows(
        output_dir / "water_bulk_reweight_context.csv",
        bulk_reweight_rows,
        [
            "source_id",
            "case_label",
            "comparison_row_count",
            "mean_exact_cp_minus_stored_flow_k",
            "max_abs_exact_cp_minus_stored_flow_k",
            "mean_exact_cp_minus_exact_flow_k",
            "max_abs_exact_cp_minus_exact_flow_k",
            "selection_status_counts",
        ],
    )
    csv_dump_rows(
        output_dir / "water_dependency_readiness.csv",
        dependency_rows,
        [
            "dependency_family",
            "current_status",
            "evidence_basis",
            "next_requirement",
        ],
    )

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(case_context_rows),
        "hydraulic_candidate_branch_count": sum(1 for row in hydraulic_branch_rows if row["classification"] == "water_family_candidate"),
        "hydraulic_contextual_branch_count": sum(1 for row in hydraulic_branch_rows if row["classification"] == "contextual_only"),
        "hydraulic_excluded_branch_count": sum(1 for row in hydraulic_branch_rows if row["classification"] == "excluded"),
        "thermal_candidate_span_count": sum(1 for row in thermal_span_rows if row["phase1_thermal_classification"] == "closure_rebuild_candidate"),
        "thermal_priority_span_count": sum(1 for row in thermal_span_rows if row["phase1_thermal_classification"] == "closure_rebuild_priority"),
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir / "README.md", summary)
    write_handoff(output_dir / "water_phase1_handoff.md", dependency_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
