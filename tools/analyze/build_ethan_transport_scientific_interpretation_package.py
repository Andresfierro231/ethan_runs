#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, safe_float  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_scientific_interpretation_package"
DEFAULT_PACKAGE_INDEX = ROOT / "reports" / "2026-06-15_ethan_all_runs_field_transport_campaign" / "field_transport_package_index.csv"
DEFAULT_ANALYSIS_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_analysis_package"
DEFAULT_SCRUTINY_DIR = ROOT / "reports" / "2026-06-17_ethan_transport_scrutiny_package"
DEFAULT_MATH_REFERENCE = ROOT / "reports" / "2026-06-17_ethan_streamwise_transport_math_reference" / "MATH_COMPANION.md"

SAFE_SALT_BRANCHES = ("left_lower_leg", "test_section_span", "left_upper_leg", "upcomer")
THERMAL_VARIABLES = (
    ("effective_htc", "mean_effective_htc_w_m2_k", "Effective HTC"),
    ("effective_ua", "mean_effective_ua_per_m_w_m_k", "Effective UA'"),
    ("thermal_resistance", "mean_effective_thermal_resistance_k_m_w", "Effective R'_th"),
)
REQUIRED_CASE_FILES = (
    "summary.json",
    "major_loss_summary.csv",
    "major_loss_cumulative_timeseries.csv",
    "branch_thermal_summary.csv",
    "branch_thermal_profiles.csv",
    "thermal_support_qc_summary.csv",
)
REQUIRED_ANALYSIS_FILES = (
    "case_family_interpretation_matrix.csv",
    "transport_contradiction_priority.csv",
    "promotion_candidate_index.csv",
    "README.md",
)
REQUIRED_SCRUTINY_FILES = (
    "transport_claim_matrix.csv",
    "transport_contradiction_log.csv",
    "paper_safe_asset_map.csv",
    "README.md",
)
EXPECTED_CONTRADICTION_CASES = (
    ("val_water_test_1_coarse_mesh_laminar", "left_lower_leg"),
    ("val_water_test_2_coarse_mesh_laminar", "left_lower_leg"),
)
GROUP_ORDER = (
    "salt_all",
    "salt1",
    "salt2",
    "salt3",
    "salt4",
    "water_all",
    "water1",
    "water2",
    "water3",
    "water4",
    "cross_family",
)
CASE_STYLE = {
    "val_salt_test_2_coarse_mesh_laminar": "Salt 2 val",
    "viscosity_screening_salt_test_1_jin_coarse_mesh": "Salt 1 Jin",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh": "Salt 1 Kirst",
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "Salt 2 Jin",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh": "Salt 2 Kirst",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "Salt 3 Jin",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh": "Salt 3 Kirst",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "Salt 4 Jin",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh": "Salt 4 Kirst",
    "val_water_test_1_coarse_mesh_laminar": "Water 1",
    "val_water_test_2_coarse_mesh_laminar": "Water 2",
    "val_water_test_3_coarse_mesh_laminar": "Water 3",
    "val_water_test_4_coarse_mesh_laminar": "Water 4",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a focused scientific interpretation package from the finished "
            "June 15/17/18 Ethan transport audit layers without reopening extraction."
        )
    )
    parser.add_argument("--package-index", default=str(DEFAULT_PACKAGE_INDEX))
    parser.add_argument("--analysis-dir", default=str(DEFAULT_ANALYSIS_DIR))
    parser.add_argument("--scrutiny-dir", default=str(DEFAULT_SCRUTINY_DIR))
    parser.add_argument("--math-reference", default=str(DEFAULT_MATH_REFERENCE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require_exists(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Required input is missing: {path}")


def require_columns(path: Path, rows: list[dict[str, str]], required: tuple[str, ...]) -> None:
    if not rows:
        raise RuntimeError(f"Required CSV is empty: {path}")
    missing = [name for name in required if name not in rows[0]]
    if missing:
        raise RuntimeError(f"Required CSV columns are missing in {path}: {missing}")


def family_group_from_source_id(source_id: str) -> str:
    if "salt" in source_id:
        return "salt"
    if "water" in source_id:
        return "water"
    return "unknown"


def case_family_from_source_id(source_id: str) -> str:
    if "salt_test_1" in source_id:
        return "salt1"
    if "salt_test_2" in source_id:
        return "salt2"
    if "salt_test_3" in source_id:
        return "salt3"
    if "salt_test_4" in source_id:
        return "salt4"
    if "water_test_1" in source_id:
        return "water1"
    if "water_test_2" in source_id:
        return "water2"
    if "water_test_3" in source_id:
        return "water3"
    if "water_test_4" in source_id:
        return "water4"
    return "unknown"


def case_label(source_id: str) -> str:
    return CASE_STYLE.get(source_id, source_id)


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def sign_class(value: float, tolerance: float = 1.0e-12) -> int:
    if not math.isfinite(value) or abs(value) <= tolerance:
        return 0
    return 1 if value > 0.0 else -1


def finite(value: float | None) -> bool:
    return value is not None and math.isfinite(float(value))


def family_sort_key(name: str) -> int:
    try:
        return GROUP_ORDER.index(name)
    except ValueError:
        return len(GROUP_ORDER)


def classify_thermal_status(row: dict[str, Any]) -> tuple[str, str]:
    usable_fraction = float(row["usable_fraction"])
    thermal_warning_fraction = float(row["thermal_warning_fraction"])
    min_abs_delta_t = float(row["min_abs_bulk_minus_wall_temp_k"])
    total_row_count = int(row["total_row_count"])
    masked_row_count = int(row["masked_row_count"])
    masked_fraction = float(masked_row_count / max(total_row_count, 1))
    metric_value = safe_float(row.get("mean_effective_htc_w_m2_k"), math.nan)

    # Match the June 17 scrutiny gate so this package does not silently invent
    # a second trust system for the same effective thermal variables.
    if not finite(metric_value):
        return "do_not_promote", "thermal_metric_missing"
    if usable_fraction >= 0.90 and thermal_warning_fraction <= 0.10 and min_abs_delta_t >= 0.50:
        return "paper_safe", "thermal_qc_pass"
    if usable_fraction < 0.75:
        return "do_not_promote", "thermal_low_usable_fraction"
    if min_abs_delta_t < 0.25:
        return "do_not_promote", "thermal_small_delta_t"
    if masked_fraction > 0.25:
        return "do_not_promote", "thermal_masked_fraction_high"
    return "internal_only", "thermal_qc_marginal"


def summarize_branch_signs(profile_rows: list[dict[str, str]], branch_name: str) -> dict[str, Any]:
    usable_rows = [
        row
        for row in profile_rows
        if row["branch_name"] == branch_name
        and row.get("thermal_support_status") == "usable"
        and finite(safe_float(row.get("bulk_minus_wall_temp_k"), math.nan))
        and finite(safe_float(row.get("wall_heat_per_length_w_m"), math.nan))
    ]
    if not usable_rows:
        return {
            "usable_profile_rows": 0,
            "delta_t_sign_status": "no_usable_rows",
            "wall_heat_sign_status": "no_usable_rows",
            "branch_role": "unknown",
            "combined_sign_status": "insufficient_usable_rows",
        }

    delta_sign_counter = Counter(sign_class(float(row["bulk_minus_wall_temp_k"])) for row in usable_rows)
    heat_sign_counter = Counter(sign_class(float(row["wall_heat_per_length_w_m"])) for row in usable_rows)

    def dominant_fraction(counter: Counter[int]) -> float:
        return max(counter.values()) / max(sum(counter.values()), 1)

    delta_fraction = dominant_fraction(delta_sign_counter)
    heat_fraction = dominant_fraction(heat_sign_counter)
    mean_heat = sum(float(row["wall_heat_per_length_w_m"]) for row in usable_rows) / len(usable_rows)
    branch_role = "net_heating" if mean_heat > 0.0 else ("net_cooling" if mean_heat < 0.0 else "near_zero_role")

    def status_from_fraction(fraction: float) -> str:
        if fraction >= 0.95:
            return "stable"
        if fraction >= 0.75:
            return "mostly_stable"
        return "mixed"

    combined = "stable" if status_from_fraction(delta_fraction) in {"stable", "mostly_stable"} and status_from_fraction(heat_fraction) in {"stable", "mostly_stable"} else "mixed"
    return {
        "usable_profile_rows": len(usable_rows),
        "delta_t_sign_status": status_from_fraction(delta_fraction),
        "wall_heat_sign_status": status_from_fraction(heat_fraction),
        "delta_t_positive_fraction": delta_sign_counter.get(1, 0) / len(usable_rows),
        "wall_heat_positive_fraction": heat_sign_counter.get(1, 0) / len(usable_rows),
        "branch_role": branch_role,
        "combined_sign_status": combined,
    }


def family_bucket_members(packages: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for package in packages:
        groups[package["case_family"]].append(package)
        if package["family_group"] == "salt":
            groups["salt_all"].append(package)
        if package["family_group"] == "water":
            groups["water_all"].append(package)
        groups["cross_family"].append(package)
    return groups


def status_counts(statuses: list[str]) -> Counter[str]:
    return Counter(statuses)


def sign_status_for_group(sign_summaries: list[dict[str, Any]]) -> str:
    usable_counts = [int(item["usable_profile_rows"]) for item in sign_summaries]
    if sum(usable_counts) == 0:
        return "insufficient_usable_rows"
    roles = {str(item["branch_role"]) for item in sign_summaries if int(item["usable_profile_rows"]) > 0}
    combined = {str(item["combined_sign_status"]) for item in sign_summaries if int(item["usable_profile_rows"]) > 0}
    if len(roles) == 1 and combined.issubset({"stable", "mostly_stable"}):
        role = next(iter(roles))
        return f"stable_{role}"
    if "mixed" in combined:
        return "mixed_driver_or_heat_role"
    return "partially_stable_but_family_mixed"


def support_status_for_group(status_counter: Counter[str]) -> str:
    if status_counter["paper_safe"] and not status_counter["internal_only"] and not status_counter["do_not_promote"]:
        return "all_cases_paper_safe"
    if status_counter["paper_safe"] and status_counter["internal_only"] and not status_counter["do_not_promote"]:
        return "mixed_safe_and_internal"
    if status_counter["internal_only"] and not status_counter["paper_safe"] and not status_counter["do_not_promote"]:
        return "all_cases_internal_only"
    if status_counter["do_not_promote"] and not status_counter["paper_safe"] and not status_counter["internal_only"]:
        return "all_cases_blocked"
    return "mixed_with_blocked_cases"


def interpretability_for_group(
    family_bucket: str,
    branch_name: str,
    support_status: str,
    usable_min: float,
    min_delta_t_min: float,
) -> tuple[str, str, str, str, str]:
    is_salt_scope = family_bucket.startswith("salt")
    is_water_scope = family_bucket.startswith("water")
    is_cross_family = family_bucket == "cross_family"
    safe_branch = branch_name in SAFE_SALT_BRANCHES

    if support_status == "all_cases_paper_safe" and is_salt_scope and safe_branch:
        return (
            "headline_eligible",
            "yes",
            "no",
            "headline_evidence",
            "safe_salt_subset",
        )
    if support_status == "all_cases_paper_safe":
        return (
            "supporting_only",
            "no",
            "no",
            "supporting_evidence",
            "paper_safe_but_not_promoted_branch",
        )
    if support_status == "mixed_safe_and_internal" and usable_min >= 0.75 and min_delta_t_min >= 0.25:
        return (
            "supporting_only",
            "no",
            "no",
            "supporting_evidence",
            "marginal_support_in_some_cases",
        )
    if support_status == "all_cases_internal_only" and usable_min >= 0.75 and min_delta_t_min >= 0.25:
        return (
            "contextual_only",
            "no",
            "no",
            "contextual_evidence",
            "all_cases_marginal_but_not_collapsed",
        )
    if is_water_scope or is_cross_family:
        return (
            "excluded",
            "no",
            "yes",
            "exclude_from_headline",
            "family_support_collapse_or_blocked_cases",
        )
    return (
        "internal_only",
        "no",
        "yes",
        "diagnostic_only",
        "blocked_or_support_limited_branch",
    )


def reason_rank(reason: str) -> tuple[int, str]:
    order = {
        "thermal_small_delta_t": 0,
        "thermal_low_usable_fraction": 1,
        "thermal_masked_fraction_high": 2,
        "thermal_qc_marginal": 3,
        "thermal_metric_missing": 4,
        "thermal_qc_pass": 5,
    }
    return (order.get(reason, 99), reason)


def predominant_reason(reasons: list[str]) -> str:
    if not reasons:
        return "none"
    counter = Counter(reasons)
    return sorted(counter.items(), key=lambda item: (-item[1], reason_rank(item[0])))[0][0]


def contradiction_resolution_rows(packages_by_source: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, branch_name in EXPECTED_CONTRADICTION_CASES:
        package = packages_by_source[source_id]
        major_row = package["major_rows_by_span"][branch_name]
        timeseries_rows = [
            row
            for row in package["major_timeseries_rows"]
            if row["span_name"] == branch_name
            and finite(safe_float(row.get("dp_major_gradient_pa_per_m"), math.nan))
            and finite(safe_float(row.get("dp_major_gradient_direct_prgh_pa_per_m"), math.nan))
        ]
        if not timeseries_rows:
            raise RuntimeError(f"No valid timeseries rows found for contradiction analysis: {source_id} / {branch_name}")

        shear_grad = float(major_row["mean_dp_major_gradient_pa_per_m"])
        direct_grad = float(major_row["mean_dp_major_gradient_direct_prgh_pa_per_m"])
        shear_sign = "positive" if sign_class(shear_grad) > 0 else ("negative" if sign_class(shear_grad) < 0 else "near_zero")
        direct_sign = "positive" if sign_class(direct_grad) > 0 else ("negative" if sign_class(direct_grad) < 0 else "near_zero")
        magnitude_ratio = abs(direct_grad) / max(abs(shear_grad), 1.0e-12)
        support_fraction = float(int(major_row["direct_prgh_valid_bin_count"]) / max(int(major_row["valid_bin_count"]), 1))
        terminal_direct = float(major_row["mean_terminal_dp_major_direct_prgh_pa"])
        terminal_shear = float(major_row["mean_terminal_dp_major_pa"])
        terminal_ratio = abs(terminal_direct) / max(abs(terminal_shear), 1.0e-12)
        direct_values = [float(row["dp_major_gradient_direct_prgh_pa_per_m"]) for row in timeseries_rows]
        positive_count = sum(1 for value in direct_values if value > 0.0)
        negative_count = sum(1 for value in direct_values if value < 0.0)
        flow_signs = sorted({row["flow_alignment_sign"] for row in timeseries_rows})
        mean_direct_p = float(major_row["mean_dp_major_gradient_direct_p_pa_per_m"])

        if source_id == "val_water_test_1_coarse_mesh_laminar":
            suspected_cause = (
                "Weak wall-registered p_rgh signal plus oscillatory local finite-difference averaging. "
                "The branch-mean direct gradient changes sign because local positive and negative direct bins nearly cancel, "
                "even though the branch-end cumulative p_rgh drop remains positive at every retained time."
            )
            confidence = "high"
            recommended_status = "resolved_exclude"
            explanation = (
                "Treat the contradiction as a resolved exclusion rather than a usable hydraulic dependency. "
                "The direct p_rgh signal is about one order of magnitude smaller than the shear-implied branch drop "
                f"(terminal ratio {terminal_ratio:.3f}), and the mean direct gradient is effectively a weak-signal average "
                "over mixed-sign local derivatives."
            )
        else:
            suspected_cause = (
                "Mixed flow-alignment registration inside one retained time, combined with a weak wall-registered p_rgh signal. "
                "The direct cumulative p_rgh drop remains positive for every retained time, but one time window carries "
                "flow_alignment_sign = -1 over multiple valid bins, which contaminates the branch-mean direct reduction."
            )
            confidence = "medium"
            recommended_status = "unresolved_exclude"
            explanation = (
                "Do not use this branch for Water or cross-family hydraulic dependency construction until the sign-registration path "
                "is audited. The direct p_rgh signal is weak relative to the shear estimate and the mixed per-row alignment sign means "
                "the current branch mean is not mechanically traceable to one consistent pressure-drop convention."
            )

        rows.append(
            {
                "family": package["family_group"],
                "case_id": source_id,
                "case_label": package["case_label"],
                "branch": branch_name,
                "variable_compared": "shear_dp_gradient_vs_direct_prgh_dp_gradient",
                "shear_based_sign": shear_sign,
                "direct_pressure_sign": direct_sign,
                "magnitude_ratio": f"{magnitude_ratio:.6f}",
                "terminal_magnitude_ratio": f"{terminal_ratio:.6f}",
                "support_fraction": f"{support_fraction:.6f}",
                "signal_strength": (
                    f"mean_direct/shear={magnitude_ratio:.6f}; terminal_direct/shear={terminal_ratio:.6f}; "
                    f"direct_positive_rows={positive_count}; direct_negative_rows={negative_count}"
                ),
                "pressure_convention": (
                    "Primary direct signal is wall-area-averaged p_rgh; direct p is hydrostatic-dominated "
                    f"(mean direct p gradient {mean_direct_p:.3f} Pa/m)."
                ),
                "coordinate_convention": (
                    "Positive means pressure drop aligned with local flow. "
                    f"Observed flow_alignment_sign values: {','.join(flow_signs)}"
                ),
                "suspected_cause": suspected_cause,
                "confidence_level": confidence,
                "recommended_status": recommended_status,
                "explanation": explanation,
                "primary_source_path": relative_path(package["package_dir"] / "major_loss_summary.csv"),
                "secondary_source_path": relative_path(package["package_dir"] / "major_loss_cumulative_timeseries.csv"),
            }
        )
    return rows


def build_branch_thermal_interpretation(
    packages: list[dict[str, Any]],
    claim_map: dict[tuple[str, str, str, str], tuple[str, str]],
) -> list[dict[str, Any]]:
    grouped_packages = family_bucket_members(packages)
    rows: list[dict[str, Any]] = []
    for family_bucket, members in sorted(grouped_packages.items(), key=lambda item: family_sort_key(item[0])):
        for branch_name in members[0]["branch_rows_by_name"].keys():
            branch_case_rows = [member["branch_rows_by_name"][branch_name] for member in members]
            sign_summaries = [member["branch_sign_summaries"][branch_name] for member in members]
            usable_values = [float(row["usable_fraction"]) for row in branch_case_rows]
            delta_t_values = [float(row["min_abs_bulk_minus_wall_temp_k"]) for row in branch_case_rows]
            reason_list_all: list[str] = []
            for variable_family, metric_field, variable_label in THERMAL_VARIABLES:
                statuses: list[str] = []
                reasons: list[str] = []
                metric_values: list[float] = []
                for member, branch_row in zip(members, branch_case_rows):
                    status, reason = claim_map[(member["source_id"], "branch", branch_name, variable_family)]
                    statuses.append(status)
                    reasons.append(reason)
                    metric_values.append(float(branch_row[metric_field]))
                reason_list_all.extend(reasons)
                support_status = support_status_for_group(status_counts(statuses))
                sign_status = sign_status_for_group(sign_summaries)
                interpretability_status, headline_allowed, internal_only, recommended_use, default_limitation = interpretability_for_group(
                    family_bucket=family_bucket,
                    branch_name=branch_name,
                    support_status=support_status,
                    usable_min=min(usable_values),
                    min_delta_t_min=min(delta_t_values),
                )
                primary_limitation = predominant_reason([reason for reason in reasons if reason != "thermal_qc_pass"])
                if primary_limitation == "none":
                    primary_limitation = default_limitation
                explanation = (
                    f"{family_bucket} / {branch_name} / {variable_label}: support={support_status}, sign={sign_status}, "
                    f"usable_fraction_range={min(usable_values):.3f}-{max(usable_values):.3f}, "
                    f"min_abs_delta_t_range={min(delta_t_values):.3f}-{max(delta_t_values):.3f} K."
                )
                rows.append(
                    {
                        "family_group": "salt" if family_bucket.startswith("salt") else ("water" if family_bucket.startswith("water") else ("mixed" if family_bucket == "cross_family" else "unknown")),
                        "family": family_bucket,
                        "source_count": len(members),
                        "case_labels": ", ".join(member["case_label"] for member in members),
                        "source_ids": ", ".join(member["source_id"] for member in members),
                        "primary_source_paths": " | ".join(
                            relative_path(member["package_dir"] / "branch_thermal_summary.csv")
                            for member in members
                        ),
                        "branch": branch_name,
                        "variable": variable_family,
                        "support_status": support_status,
                        "sign_status": sign_status,
                        "interpretability_status": interpretability_status,
                        "headline_allowed": headline_allowed,
                        "internal_only": internal_only,
                        "primary_limitation": primary_limitation,
                        "recommended_use": recommended_use,
                        "usable_fraction_min": f"{min(usable_values):.6f}",
                        "usable_fraction_max": f"{max(usable_values):.6f}",
                        "min_abs_bulk_minus_wall_temp_k_min": f"{min(delta_t_values):.6f}",
                        "min_abs_bulk_minus_wall_temp_k_max": f"{max(delta_t_values):.6f}",
                        "mean_metric_min": f"{min(metric_values):.6f}",
                        "mean_metric_max": f"{max(metric_values):.6f}",
                        "explanation": explanation,
                    }
                )
    return rows


def build_scientific_conclusions(
    branch_rows: list[dict[str, Any]],
    contradiction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lookup = {(row["family"], row["branch"], row["variable"]): row for row in branch_rows}
    contradiction_lookup = {(row["case_id"], row["branch"]): row for row in contradiction_rows}

    def conclusion(
        conclusion_id: str,
        category: str,
        family: str,
        branch: str,
        variable_family: str,
        claim_text: str,
        supporting_row_keys: list[tuple[str, str, str]],
        caveat: str,
        recommended_use: str,
        safe_for_model_dependency: str,
        strength: str,
        supporting_paths_override: str = "",
    ) -> dict[str, Any]:
        supporting_rows = [lookup[key] for key in supporting_row_keys if key in lookup]
        supporting_files = supporting_paths_override or " | ".join(
            sorted({row["primary_source_paths"] for row in supporting_rows})
        )
        row_subset = "; ".join(
            f"{row['family']} / {row['branch']} / {row['variable']} ({row['interpretability_status']})"
            for row in supporting_rows
        )
        return {
            "conclusion_id": conclusion_id,
            "conclusion_category": category,
            "family": family,
            "branch": branch,
            "variable_family": variable_family,
            "strength_of_evidence": strength,
            "claim_text": claim_text,
            "supporting_files": supporting_files,
            "supporting_row_subset": row_subset,
            "caveat": caveat,
            "recommended_use": recommended_use,
            "safe_for_model_dependency_construction": safe_for_model_dependency,
        }

    conclusions = [
        conclusion(
            "C01",
            "stable_salt_only",
            "salt_all",
            "left_lower_leg",
            "effective_htc,effective_ua,thermal_resistance",
            "Across all nine Salt cases, left_lower_leg effective thermal metrics remain scrutiny-cleared and can support Salt-only branch dependency work on the left-side return path.",
            [("salt_all", "left_lower_leg", variable) for variable, _field, _label in THERMAL_VARIABLES],
            "These remain effective, support-gated quantities rather than intrinsic closure coefficients.",
            "headline_evidence",
            "yes_salt_only",
            "strong",
        ),
        conclusion(
            "C02",
            "stable_salt_only",
            "salt_all",
            "test_section_span",
            "effective_htc,effective_ua,thermal_resistance",
            "Across all nine Salt cases, test_section_span is the cleanest thermal anchor: all branch rows remain usable and stay comfortably above the current small-delta-T floor.",
            [("salt_all", "test_section_span", variable) for variable, _field, _label in THERMAL_VARIABLES],
            "Interpret these as effective transport indicators, not unrestricted local HTC truth.",
            "headline_evidence",
            "yes_salt_only",
            "strong",
        ),
        conclusion(
            "C03",
            "stable_salt_only",
            "salt_all",
            "left_upper_leg",
            "effective_htc,effective_ua,thermal_resistance",
            "Across all nine Salt cases, left_upper_leg remains Salt-only headline-eligible because usable fractions stay high and the minimum driving temperature stays well above the masking floor.",
            [("salt_all", "left_upper_leg", variable) for variable, _field, _label in THERMAL_VARIABLES],
            "Still support-gated and branch-specific; do not reinterpret as wall-law closure evidence.",
            "headline_evidence",
            "yes_salt_only",
            "strong",
        ),
        conclusion(
            "C04",
            "stable_salt_only",
            "salt_all",
            "upcomer",
            "effective_htc,effective_ua,thermal_resistance",
            "The derived upcomer remains a defensible Salt-only branch surface because all three component spans stay scrutiny-cleared in the Salt family and the derived branch inherits high usable fractions.",
            [("salt_all", "upcomer", variable) for variable, _field, _label in THERMAL_VARIABLES],
            "Corners and junctions remain omitted from the upcomer coordinate and must stay omitted in any model mapping.",
            "headline_evidence",
            "yes_salt_only",
            "strong",
        ),
        conclusion(
            "C05",
            "stable_salt_only",
            "salt_all",
            "right_leg",
            "effective_htc,effective_ua,thermal_resistance",
            "Salt right_leg thermal rows remain blocked from headline use even though the mean driving temperature is not small, because usable fraction stays near 0.73 and the failure mode is persistent area-ratio masking.",
            [("salt_all", "right_leg", variable) for variable, _field, _label in THERMAL_VARIABLES],
            "Do not promote right_leg thermal behavior without a revised branch support path.",
            "internal_only",
            "no",
            "strong",
        ),
        conclusion(
            "C06",
            "stable_water_only",
            "water_all",
            "left_lower_leg",
            "effective_htc,effective_ua,thermal_resistance",
            "Across all four Water cases, left_lower_leg effective thermal metrics are blocked by small |T_bulk - T_wall| and low usable fraction; this branch should not be used for Water-family HTC, UA', or R'_th fitting.",
            [("water_all", "left_lower_leg", variable) for variable, _field, _label in THERMAL_VARIABLES],
            "The large numerical mean HTC values are denominator-sensitive artifacts, not evidence of stronger local heat transfer.",
            "excluded",
            "no",
            "strong",
        ),
        conclusion(
            "C07",
            "stable_water_only",
            "water_all",
            "test_section_span",
            "effective_htc,effective_ua,thermal_resistance",
            "Water test_section_span is the cleanest Water thermal branch, but it remains supporting-only rather than headline-safe because the minimum resolved driving temperature stays below the current 0.50 K scrutiny threshold.",
            [("water_all", "test_section_span", variable) for variable, _field, _label in THERMAL_VARIABLES],
            "Useful for internal comparison, not yet for Water-family fitting claims.",
            "supporting_only",
            "no",
            "moderate",
        ),
        conclusion(
            "C08",
            "cross_family",
            "cross_family",
            "all_branches",
            "effective_htc,effective_ua,thermal_resistance",
            "Across both Salt and Water, effective thermal metrics are not uniformly interpretable branch-by-branch; branch promotion gates are required because support quality and resolved driving temperature vary systematically by branch and family.",
            [
                ("cross_family", "left_lower_leg", "effective_htc"),
                ("cross_family", "test_section_span", "effective_htc"),
                ("cross_family", "upcomer", "effective_htc"),
            ],
            "This is a methodological conclusion about interpretability, not a fitted cross-family thermal dependency.",
            "headline_caveated_method",
            "yes_for_method_only",
            "strong",
        ),
        conclusion(
            "C09",
            "cross_family",
            "cross_family",
            "boundary_layer_landmarks",
            "boundary_layer_context",
            "Boundary-layer landmarks remain contextual evidence only; they can help explain branch behavior but should not be used as headline model evidence or closure targets.",
            [],
            "The current scrutiny package keeps all boundary-layer rows internal-only by design.",
            "contextual_only",
            "no",
            "strong",
        ),
        conclusion(
            "C10",
            "cross_family",
            "cross_family",
            "momentum_resistance",
            "momentum_resistance",
            "Momentum resistance should remain a proxy diagnostic rather than a direct model target because it inherits the same branchwise disagreement and support limits as the underlying direct-versus-shear pressure reductions.",
            [],
            "Use only as a derived consistency check until the direct hydraulic contradictions are resolved more fully.",
            "internal_only",
            "no",
            "strong",
        ),
        conclusion(
            "C11",
            "family_specific",
            "salt_vs_water",
            "left_side_safe_subset",
            "effective_htc,effective_ua,thermal_resistance",
            "The main Salt-vs-Water difference is interpretability, not just magnitude: Salt left-side return-path branches are scrutiny-cleared, whereas Water left-side return-path branches remain support-limited by low |T_bulk - T_wall| and inherited masking.",
            [
                ("salt_all", "left_lower_leg", "effective_htc"),
                ("water_all", "left_lower_leg", "effective_htc"),
                ("salt_all", "upcomer", "effective_htc"),
                ("water_all", "upcomer", "effective_htc"),
            ],
            "Do not collapse this into a cross-family coefficient ranking.",
            "supporting_only",
            "family_specific_only",
            "strong",
        ),
        conclusion(
            "C12",
            "contradictory_or_unresolved",
            "water1",
            "left_lower_leg",
            "shear_friction,direct_pressure_gradient,momentum_resistance",
            "Water 1 left_lower_leg hydraulic disagreement is best interpreted as a weak-signal wall-registered p_rgh issue: the branch-end cumulative direct p_rgh drop stays positive, but the branch-mean direct gradient oscillates around zero because mixed-sign local derivatives nearly cancel.",
            [],
            contradiction_lookup[("val_water_test_1_coarse_mesh_laminar", "left_lower_leg")]["explanation"],
            "exclude_from_model_evidence",
            "no",
            "moderate",
            supporting_paths_override=contradiction_lookup[("val_water_test_1_coarse_mesh_laminar", "left_lower_leg")]["primary_source_path"]
            + " | "
            + contradiction_lookup[("val_water_test_1_coarse_mesh_laminar", "left_lower_leg")]["secondary_source_path"],
        ),
        conclusion(
            "C13",
            "contradictory_or_unresolved",
            "water2",
            "left_lower_leg",
            "shear_friction,direct_pressure_gradient,momentum_resistance",
            "Water 2 left_lower_leg hydraulic disagreement remains unresolved for modeling because one retained window carries mixed flow-alignment signs inside the branch while the direct p_rgh signal is weak.",
            [],
            contradiction_lookup[("val_water_test_2_coarse_mesh_laminar", "left_lower_leg")]["explanation"],
            "exclude_from_model_evidence",
            "no",
            "moderate",
            supporting_paths_override=contradiction_lookup[("val_water_test_2_coarse_mesh_laminar", "left_lower_leg")]["primary_source_path"]
            + " | "
            + contradiction_lookup[("val_water_test_2_coarse_mesh_laminar", "left_lower_leg")]["secondary_source_path"],
        ),
        conclusion(
            "C14",
            "internal_only",
            "salt2",
            "upcomer_and_test_section",
            "effective_htc,effective_ua,thermal_resistance",
            "Within the matched Salt 2 trio, upcomer and test_section_span remain the cleanest mechanism branches for thermal comparison; the right_leg should stay out of mechanism ranking even though its mean effective metrics are finite.",
            [
                ("salt2", "upcomer", "effective_htc"),
                ("salt2", "test_section_span", "effective_htc"),
                ("salt2", "right_leg", "effective_htc"),
            ],
            "This is a Salt 2 mechanism result only, not a universal loop ranking.",
            "supporting_only",
            "yes_salt_only",
            "strong",
        ),
        conclusion(
            "C15",
            "internal_only",
            "water_all",
            "upper_leg_and_upcomer",
            "effective_htc,effective_ua,thermal_resistance",
            "Water upper_leg and upcomer rows should remain internal-only because denominator collapse, not just masking, controls their apparent thermal ratios in multiple Water cases.",
            [
                ("water_all", "upper_leg", "effective_htc"),
                ("water_all", "upcomer", "effective_htc"),
            ],
            "Large numerical HTC or low R'_th values in these branches are not model-ready evidence without stronger bulk-temperature support.",
            "internal_only",
            "no",
            "strong",
        ),
    ]
    return conclusions


def build_cross_family_claims_audit() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "X01",
            "potential_claim": "Cross-family hydraulic branch dependency on left_lower_leg",
            "status": "blocked_by_unresolved_hydraulic_contradiction",
            "allowed_scope": "none",
            "required_caveat": "Water 1 and Water 2 left_lower_leg direct-vs-shear disagreements remain excluded.",
            "blocked_reason_if_any": "The direct p_rgh reduction is not mechanically stable enough to support a cross-family branch pressure-drop dependency.",
        },
        {
            "claim_id": "X02",
            "potential_claim": "Cross-family effective thermal dependency on left_lower_leg",
            "status": "blocked_by_thermal_support_limits",
            "allowed_scope": "none",
            "required_caveat": "Water left_lower_leg rows fail the current Delta T and usable-fraction gates.",
            "blocked_reason_if_any": "Water-family left_lower_leg effective thermal metrics are denominator-limited and blocked.",
        },
        {
            "claim_id": "X03",
            "potential_claim": "Cross-family test_section effective thermal comparison",
            "status": "allowed_with_caveats",
            "allowed_scope": "support-structure comparison only",
            "required_caveat": "Water test_section_span is supporting-only, not headline-safe.",
            "blocked_reason_if_any": "",
        },
        {
            "claim_id": "X04",
            "potential_claim": "Cross-family branch support asymmetry between Salt and Water",
            "status": "allowed",
            "allowed_scope": "method and interpretability discussion",
            "required_caveat": "Discuss support-gating asymmetry, not fitted coefficient superiority.",
            "blocked_reason_if_any": "",
        },
        {
            "claim_id": "X05",
            "potential_claim": "Cross-family momentum-resistance fit target",
            "status": "blocked",
            "allowed_scope": "diagnostic consistency check only",
            "required_caveat": "Momentum resistance is a proxy that inherits hydraulic contradictions.",
            "blocked_reason_if_any": "Not a direct closure-quality measurement.",
        },
        {
            "claim_id": "X06",
            "potential_claim": "Boundary-layer landmarks as headline cross-family evidence",
            "status": "blocked_by_branch_promotion_boundary",
            "allowed_scope": "contextual appendix/internal use only",
            "required_caveat": "Boundary-layer landmarks remain contextual-only.",
            "blocked_reason_if_any": "Scrutiny package does not promote any boundary-layer row to paper-safe headline use.",
        },
        {
            "claim_id": "X07",
            "potential_claim": "Salt-only safe-subset thermal dependency",
            "status": "allowed_with_caveats",
            "allowed_scope": "left_lower_leg, test_section_span, left_upper_leg, upcomer",
            "required_caveat": "Effective thermal variables remain support-gated and family-specific.",
            "blocked_reason_if_any": "",
        },
        {
            "claim_id": "X08",
            "potential_claim": "Water-only left-side branch thermal dependency",
            "status": "blocked_by_thermal_support_limits",
            "allowed_scope": "none",
            "required_caveat": "Water left_lower_leg and upcomer remain support-limited.",
            "blocked_reason_if_any": "Current Water left-side branches fail the current Delta T and usable-fraction gates.",
        },
    ]


def build_internal_only_decisions(
    branch_rows: list[dict[str, Any]],
    contradiction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for row in branch_rows:
        output_rows.append(
            {
                "family": row["family"],
                "branch": row["branch"],
                "variable": row["variable"],
                "decision": (
                    "headline_evidence"
                    if row["recommended_use"] == "headline_evidence"
                    else (
                        "supporting_evidence"
                        if row["recommended_use"] == "supporting_evidence"
                        else (
                            "contextual_evidence"
                            if row["recommended_use"] == "contextual_evidence"
                            else ("internal_only" if row["recommended_use"] == "diagnostic_only" else "excluded")
                        )
                    )
                ),
                "support_status": row["support_status"],
                "primary_limitation": row["primary_limitation"],
                "explanation": row["explanation"],
            }
        )
    output_rows.extend(
        [
            {
                "family": "cross_family",
                "branch": "boundary_layer_landmarks",
                "variable": "boundary_layer_context",
                "decision": "contextual_evidence",
                "support_status": "internal_only_by_policy",
                "primary_limitation": "not_a_headline_closure_metric",
                "explanation": "Boundary-layer landmarks remain comparative context rather than headline model evidence.",
            },
            {
                "family": "cross_family",
                "branch": "all_branches",
                "variable": "momentum_resistance",
                "decision": "internal_only",
                "support_status": "proxy_only",
                "primary_limitation": "inherits_hydraulic_disagreement",
                "explanation": "Momentum resistance is a local proxy dp/ds divided by mdot, not a directly measured closure quantity.",
            },
        ]
    )
    for row in contradiction_rows:
        output_rows.append(
            {
                "family": row["family"],
                "branch": row["branch"],
                "variable": "shear_friction,direct_pressure_gradient,momentum_resistance",
                "decision": "excluded",
                "support_status": row["recommended_status"],
                "primary_limitation": row["suspected_cause"],
                "explanation": row["explanation"],
            }
        )
    return output_rows


def build_methods_interpretation(contradiction_rows: list[dict[str, Any]]) -> str:
    water1 = next(row for row in contradiction_rows if row["case_id"] == "val_water_test_1_coarse_mesh_laminar")
    water2 = next(row for row in contradiction_rows if row["case_id"] == "val_water_test_2_coarse_mesh_laminar")
    return f"""# Methods Interpretation

## Scope

This note tightens the interpretation layer on top of the June 17 streamwise
transport math companion. It does not redefine the implemented formulas. It
explains how those formulas should be read scientifically when the resulting
transport quantities are used for model dependency construction.

## What the effective hydraulic quantities mean

The shear-based hydraulic reduction is a wall-stress reduction. It projects
wall shear onto the repaired streamwise tangent, area-averages the projected
streamwise magnitude, and then converts that wall-stress surrogate into
Darcy/Fanning form with the current hydraulic-diameter and bulk-speed
surrogates. It is therefore a wall-stress-derived hydraulic indicator, not a
direct measurement of centerline pressure drop.

The direct hydraulic reduction is a wall-registered pressure diagnostic. It
area-averages wall `p_rgh` or `p` in each streamwise bin, finite-differences
those wall means along the repaired coordinate, and then converts the result
into Darcy/Fanning form with the same surrogate geometry. It is therefore a
wall-pressure-derived indicator, not a control-volume momentum closure.

These two hydraulic paths should agree on the broad pressure-drop direction and
the main accumulation regions before they are used as model evidence.

## Why direct and shear hydraulic reductions may disagree

Direct and shear reductions can disagree for at least four distinct reasons:

1. They use different observables. Wall shear is local traction data. Direct
   `p_rgh` is a finite-differenced wall-pressure field.
2. The direct path is vulnerable to branchwise differencing noise when the net
   `p_rgh` drop is small. Mixed positive and negative local derivatives can
   average toward zero even when the branch-end cumulative drop is positive.
3. The direct path depends on flow-direction alignment. If `flow_alignment_sign`
   is inconsistent across retained windows or bins, branch means can inherit a
   sign-registration problem rather than a real physics reversal.
4. `p` and `p_rgh` are not interchangeable in buoyant loops. `p` is dominated
   by hydrostatic head; `p_rgh` is the friction-scale direct diagnostic.

The two highest-priority Water contradictions illustrate these failure modes.

- Water 1 left_lower_leg: {water1["explanation"]}
- Water 2 left_lower_leg: {water2["explanation"]}

Disagreement in pressure-drop direction is serious because it means the
postprocessed branch result is not robust even at the sign level. Those rows
must be excluded from cross-family hydraulic dependency construction until the
sign convention or aggregation issue is resolved.

## Why small |T_bulk - T_wall| causes HTC, UA', and R'_th blowups

The current effective thermal quantities are ratios:

- `h_eff = |q''_w| / |T_bulk - T_wall|`
- `UA'_eff = |q'_w| / |T_bulk - T_wall|`
- `R'_th = 1 / UA'_eff`

When the resolved branch-scale driving temperature approaches zero, the ratio
becomes extremely sensitive to small numerator or denominator perturbations.
This is not a cosmetic plotting issue. It is a structural property of the
effective reduction.

For that reason, a large reported effective HTC does not automatically mean a
physically stronger local transfer mechanism. It may simply mean:

- the branch is operating with a weak resolved thermal driving force,
- the selected bulk region is only marginally supported,
- the denominator is small enough that ratio noise is amplified.

The Water left-side branches and several upper-leg rows show exactly this
behavior. They must be treated as support-limited diagnostics rather than
fittable closure targets.

## Why R'_th can look attractive but still be support-limited

`R'_th` is often visually appealing because it converts large effective-HTC
swings into a smaller numerical scale. That can make the curve look calmer.
But `R'_th` is not independent information. It is the reciprocal of `UA'_eff`
and inherits the same support path, the same branch masking, and the same weak
Delta-T failure mode.

A numerically smooth `R'_th` value is therefore not enough to promote a branch.
The support fraction, the minimum resolved `|T_bulk - T_wall|`, and the branch
warning breakdown still control whether the quantity is model-ready.

## Why momentum resistance is only a proxy

The current momentum-resistance quantity is local `dp/ds` divided by `mdot`. It
is useful as a diagnostic because it places the pressure-gradient reductions on
a mass-flow-normalized scale. But it is still downstream of the same direct or
shear pressure surrogate and therefore cannot be treated as a directly measured
resistance law.

If the underlying hydraulic reduction is contradictory or support-limited, the
momentum-resistance proxy is also contradictory or support-limited.

## Why support fraction is not cosmetic

Support fraction is not a presentation filter. It tells you whether the branch
summary is actually built from enough usable rows to represent the branch.

- Low usable fraction means the branch summary is being carried by a minority
  of the retained rows.
- Small `|T_bulk - T_wall|` means the ratio denominator is weak.
- Large masked fractions mean the effective metric exists numerically but is
  not stable enough to generalize.

These are scientific trust limits, not plotting preferences.

## Why branch promotion gates are necessary

Branch promotion gates exist because not every branch supports the same quality
of reduced quantity.

- Salt safe subset: `left_lower_leg`, `test_section_span`, `left_upper_leg`,
  and `upcomer`.
- Salt blocked thermal branch: `right_leg`.
- Water blocked left-side branch: `left_lower_leg`.
- Water supporting-only branch: `test_section_span`.

Without branch promotion gates, the paper and any downstream model dependency
work would mix scrutiny-cleared effective quantities with denominator-driven or
mask-dominated artifacts.

## How Salt and Water should be compared without overclaiming

Salt and Water should be compared in two stages:

1. Compare support structure first.
   Determine which branches are scrutiny-cleared, which are marginal, and
   which are blocked.
2. Compare effective transport values only inside the shared support envelope.

At the current state of the package stack:

- Salt-only branch thermal dependency work is defensible on the safe subset.
- Water left-side branch thermal dependency work is not ready.
- Cross-family hydraulic dependency work is not ready while the Water
  left_lower_leg contradictions remain excluded.

That is the correct interpretation boundary for the current audit outputs.
"""


def build_model_dependency_readiness(contradiction_rows: list[dict[str, Any]]) -> str:
    unresolved = [f"{row['case_label']} / {row['branch']}" for row in contradiction_rows if row["recommended_status"] == "unresolved_exclude"]
    return """# Model Dependency Readiness

| Dependency | Classification | Required gates | Eligible branches | Excluded branches | Unresolved contradictions | Recommended next analysis | Risk of overclaiming |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Effective friction factor | family_specific_only | shear/direct sign agreement on the branch or span; direct support fraction must stay credible | Salt spans and non-contradictory Water spans only | Water 1 left_lower_leg; Water 2 left_lower_leg | """ + (", ".join(unresolved) if unresolved else "none") + """ | Audit branch-level sign alignment before any stronger cross-family hydraulic fit | High if direct-vs-shear sign disagreement is ignored |
| Effective K or feature loss | not_ready | dedicated feature closure audit with consistent driving-head accounting | none in this package | all branches for direct model fitting | n/a | Use the dedicated feature-loss packages instead of forcing a branch-level interpretation here | High |
| Momentum resistance proxy | diagnostic_only | same gates as the underlying hydraulic reduction | internal consistency checks only | all headline-fit uses | """ + (", ".join(unresolved) if unresolved else "none") + """ | Keep as a proxy and do not use as a closure target | High |
| Branch pressure-drop interpretation | family_specific_only | direct/shear sign agreement, stable pressure convention, consistent flow alignment | Salt branches outside current contradiction rows | Water 1 left_lower_leg; Water 2 left_lower_leg | """ + (", ".join(unresolved) if unresolved else "none") + """ | Recompute or audit the direct branch sign path if cross-family hydraulic work is required | High |
| HTC(x) | family_specific_only | usable fraction >= 0.90, warning fraction <= 0.10, min |T_bulk-T_wall| >= 0.50 K | Salt: left_lower_leg, test_section_span, left_upper_leg, upcomer | Salt right_leg; Water left_lower_leg; Water upcomer; any small-Delta-T branch | Water left-side thermal support collapse | Keep Water results diagnostic-only until a stronger bulk-support path exists | High |
| UA'(x) | family_specific_only | same as HTC(x) | Salt: left_lower_leg, test_section_span, left_upper_leg, upcomer | same as HTC(x) exclusions | Water left-side thermal support collapse | Same as HTC(x) | High |
| R'_th(x) | family_specific_only | same as HTC(x); do not treat reciprocal smoothing as validation | Salt: left_lower_leg, test_section_span, left_upper_leg, upcomer | same as HTC(x) exclusions | Water left-side thermal support collapse | Use only where the parent UA' is already scrutiny-cleared | High |
| Branch-averaged thermal resistance | family_specific_only | branch must already be scrutiny-cleared for effective thermal use | Salt safe subset only | Water left_lower_leg; Water upcomer; Salt right_leg | Water left-side thermal support collapse | Keep branch-averaged resistance out of cross-family fitting | Moderate |
| Heating/cooling branch role | diagnostic_only | sign stability in wall heat and branch Delta T | Salt safe subset; Water test_section_span as context only | contradiction-heavy or support-collapsed branches | Hydraulic contradictions do not directly block thermal role, but support collapse does | Use as contextual interpretation only | Moderate |
"""


def build_remaining_blockers(contradiction_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Remaining Blockers",
        "",
        "1. Water 1 left_lower_leg hydraulic branch remains excluded from model evidence because the mean direct p_rgh gradient is a weak-signal oscillatory average even though the branch-end cumulative p_rgh drop stays positive.",
        "2. Water 2 left_lower_leg hydraulic branch remains unresolved for model use because mixed flow-alignment signs appear inside one retained window while the direct p_rgh signal is weak.",
        "3. Water left_lower_leg and upcomer thermal metrics remain blocked by small |T_bulk - T_wall| and low usable fraction; these branches are not ready for Water-family HTC, UA', or R'_th dependencies.",
        "4. Salt and Water right_leg effective thermal metrics remain blocked from headline use because the usable fraction stays near the low-support boundary even when the mean driving temperature is not small.",
        "5. Boundary-layer landmarks remain contextual-only; they should not be used as a primary model evidence layer until a future scrutiny pass explicitly upgrades them.",
        "6. Momentum resistance remains a proxy diagnostic and should not be fitted as if it were a directly measured closure quantity.",
        "",
        "If a future cross-family hydraulic fit is required, the first follow-up should be a bounded audit of the direct branch sign path on Water left_lower_leg using branch-end cumulative p_rgh drop, per-time flow-alignment signs, and any summary aggregation that collapses them into one branch mean.",
    ]
    if any(row["recommended_status"] == "unresolved_exclude" for row in contradiction_rows):
        lines.append("")
        lines.append("Current unresolved-exclude rows:")
        for row in contradiction_rows:
            if row["recommended_status"] == "unresolved_exclude":
                lines.append(f"- {row['case_label']} / {row['branch']}: {row['suspected_cause']}")
    return "\n".join(lines) + "\n"


def build_readme(
    package_name: str,
    args: argparse.Namespace,
    interpretation_summary: dict[str, Any],
    contradiction_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
    conclusions: list[dict[str, Any]],
    cross_family_audit: list[dict[str, Any]],
    internal_only_rows: list[dict[str, Any]],
) -> str:
    salt_conclusions = [row for row in conclusions if row["conclusion_category"] == "stable_salt_only"]
    water_conclusions = [row for row in conclusions if row["conclusion_category"] == "stable_water_only"]
    cross_conclusions = [row for row in conclusions if row["conclusion_category"] == "cross_family"]
    family_specific = [row for row in conclusions if row["conclusion_category"] == "family_specific"]
    contradiction_lines = "\n".join(
        f"- {row['case_label']} / {row['branch']}: {row['recommended_status']} ({row['confidence_level']}) -> {row['suspected_cause']}"
        for row in contradiction_rows
    )
    headline_branches = sorted({
        row["branch"]
        for row in branch_rows
        if row["headline_allowed"] == "yes" and row["family"] == "salt_all"
    })
    internal_examples = "\n".join(
        f"- {row['family']} / {row['branch']} / {row['variable']}: {row['decision']} ({row['primary_limitation']})"
        for row in internal_only_rows[:8]
    )
    return f"""# Ethan Transport Scientific Interpretation Package

Generated: `{iso_timestamp()}`

## Purpose

This package is the focused scientific interpretation handoff for the current
June 15/17/18 transport audit stack. It does not regenerate extraction,
rebuild campaign dashboards, or alter the finished per-case packages. Its job
is to decide what the existing transport outputs actually support, what remains
family-specific, what is contradictory, and what should stay internal-only.

## Input Packages Used

- package index: `{relative_path(Path(args.package_index))}`
- analysis package: `{relative_path(Path(args.analysis_dir))}`
- scrutiny package: `{relative_path(Path(args.scrutiny_dir))}`
- math reference: `{relative_path(Path(args.math_reference))}`
- per-case packages from `reports/2026-06-15_ethan_all_runs_field_transport_campaign/field_transport_package_index.csv`

## What Was Analyzed

- the two priority-one Water hydraulic contradiction rows:
  - `val_water_test_1_coarse_mesh_laminar / left_lower_leg`
  - `val_water_test_2_coarse_mesh_laminar / left_lower_leg`
- branch-by-branch effective thermal outputs:
  - `HTC(x)`
  - `UA'(x)`
  - `R'_th(x)`
- branch support fractions, minimum resolved `|T_bulk - T_wall|`, and sign consistency
- existing scrutiny and analysis package promotion boundaries

## What Was Not Regenerated

- no OpenFOAM extraction
- no per-case package rebuild
- no campaign rebuild
- no new figure dashboard stack

## Contradiction Resolution Summary

{contradiction_lines}

## Branch-By-Branch Thermal Summary

- headline-eligible Salt branches: `{", ".join(headline_branches)}`
- right_leg remains withheld from headline thermal use
- Water left_lower_leg remains blocked for effective thermal dependency use
- Water test_section_span remains supporting-only rather than headline-safe

## Salt-Only Conclusions

{chr(10).join(f"- {row['claim_text']}" for row in salt_conclusions)}

## Water-Only Conclusions

{chr(10).join(f"- {row['claim_text']}" for row in water_conclusions)}

## Cross-Family Conclusions

{chr(10).join(f"- {row['claim_text']}" for row in cross_conclusions)}

## Family-Specific Conclusions

{chr(10).join(f"- {row['claim_text']}" for row in family_specific)}

## Internal-Only Decisions

{internal_examples}

## Remaining Blockers

- unresolved hydraulic contradiction rows: `{interpretation_summary['unresolved']}`
- excluded contradiction rows: `{interpretation_summary['excluded']}`
- blocked cross-family claims: `{sum(1 for row in cross_family_audit if row['status'].startswith('blocked'))}`
- blocked thermal branches remain concentrated in Water left-side branches and both-family right_leg thermal behavior

## Reproduction Commands

- `python -m py_compile tools/analyze/build_ethan_transport_scientific_interpretation_package.py`
- `python tools/analyze/build_ethan_transport_scientific_interpretation_package.py --output-dir tmp/2026-06-18_ethan_transport_scientific_interpretation_package_smoke`
- `python tools/analyze/build_ethan_transport_scientific_interpretation_package.py --output-dir reports/2026-06-18_ethan_transport_scientific_interpretation_package`

## Limitations

- cross-family hydraulic dependency work remains blocked by the unresolved Water left_lower_leg sign problem
- effective thermal metrics remain effective, support-gated diagnostics rather than intrinsic coefficients
- boundary-layer landmarks remain contextual-only
- momentum resistance remains a proxy rather than a directly measured closure quantity
"""


def build_packages(package_index: Path) -> list[dict[str, Any]]:
    package_rows = load_csv_rows(package_index)
    require_columns(package_index, package_rows, ("source_id", "case_label", "package_dir"))
    packages: list[dict[str, Any]] = []
    for row in package_rows:
        source_id = str(row["source_id"])
        package_dir = Path(row["package_dir"]).resolve()
        for name in REQUIRED_CASE_FILES:
            require_exists(package_dir / name)

        summary = load_json(package_dir / "summary.json")
        major_rows_raw = load_csv_rows(package_dir / "major_loss_summary.csv")
        branch_rows_raw = load_csv_rows(package_dir / "branch_thermal_summary.csv")
        qc_rows_raw = load_csv_rows(package_dir / "thermal_support_qc_summary.csv")
        branch_profiles = load_csv_rows(package_dir / "branch_thermal_profiles.csv")
        major_timeseries = load_csv_rows(package_dir / "major_loss_cumulative_timeseries.csv")

        require_columns(
            package_dir / "major_loss_summary.csv",
            major_rows_raw,
            (
                "span_name",
                "mean_dp_major_gradient_pa_per_m",
                "mean_dp_major_gradient_direct_prgh_pa_per_m",
                "mean_terminal_dp_major_pa",
                "mean_terminal_dp_major_direct_prgh_pa",
                "valid_bin_count",
                "direct_prgh_valid_bin_count",
                "mean_dp_major_gradient_direct_p_pa_per_m",
            ),
        )
        require_columns(
            package_dir / "branch_thermal_summary.csv",
            branch_rows_raw,
            (
                "branch_name",
                "thermal_warning_fraction",
                "min_abs_bulk_minus_wall_temp_k",
                "mean_effective_htc_w_m2_k",
                "mean_effective_ua_per_m_w_m_k",
                "mean_effective_thermal_resistance_k_m_w",
                "total_row_count",
                "masked_row_count",
            ),
        )
        require_columns(
            package_dir / "branch_thermal_profiles.csv",
            branch_profiles,
            (
                "branch_name",
                "thermal_support_status",
                "bulk_minus_wall_temp_k",
                "wall_heat_per_length_w_m",
            ),
        )
        require_columns(
            package_dir / "major_loss_cumulative_timeseries.csv",
            major_timeseries,
            (
                "span_name",
                "dp_major_gradient_pa_per_m",
                "dp_major_gradient_direct_prgh_pa_per_m",
                "dp_major_gradient_direct_p_pa_per_m",
                "flow_alignment_sign",
                "cumulative_dp_major_direct_prgh_pa",
            ),
        )

        branch_rows = []
        for item in branch_rows_raw:
            typed = dict(item)
            total_row_count = int(item["total_row_count"])
            usable_row_count = int(item["usable_row_count"])
            for key in (
                "thermal_warning_fraction",
                "min_abs_bulk_minus_wall_temp_k",
                "mean_effective_htc_w_m2_k",
                "mean_effective_ua_per_m_w_m_k",
                "mean_effective_thermal_resistance_k_m_w",
            ):
                typed[key] = float(item[key])
            typed["usable_fraction"] = float(
                item.get("usable_fraction") or (usable_row_count / max(total_row_count, 1))
            )
            branch_rows.append(typed)

        branch_rows_by_name = {row["branch_name"]: row for row in branch_rows}
        branch_sign_summaries = {
            branch_name: summarize_branch_signs(branch_profiles, branch_name)
            for branch_name in branch_rows_by_name
        }

        packages.append(
            {
                "source_id": source_id,
                "case_label": case_label(source_id),
                "family_group": family_group_from_source_id(source_id),
                "case_family": case_family_from_source_id(source_id),
                "package_dir": package_dir,
                "summary": summary,
                "major_rows_by_span": {item["span_name"]: item for item in major_rows_raw},
                "branch_rows_by_name": branch_rows_by_name,
                "qc_rows": qc_rows_raw,
                "branch_profiles": branch_profiles,
                "branch_sign_summaries": branch_sign_summaries,
                "major_timeseries_rows": major_timeseries,
            }
        )
    return packages


def load_claim_map(scrutiny_dir: Path) -> dict[tuple[str, str, str, str], tuple[str, str]]:
    path = scrutiny_dir / "transport_claim_matrix.csv"
    rows = load_csv_rows(path)
    require_columns(
        path,
        rows,
        ("source_id", "scope_type", "scope_name", "variable_family", "scrutiny_status", "reason_code"),
    )
    return {
        (row["source_id"], row["scope_type"], row["scope_name"], row["variable_family"]): (row["scrutiny_status"], row["reason_code"])
        for row in rows
    }


def validate_inputs(args: argparse.Namespace) -> None:
    require_exists(Path(args.package_index))
    require_exists(Path(args.analysis_dir))
    require_exists(Path(args.scrutiny_dir))
    require_exists(Path(args.math_reference))
    for filename in REQUIRED_ANALYSIS_FILES:
        require_exists(Path(args.analysis_dir) / filename)
    for filename in REQUIRED_SCRUTINY_FILES:
        require_exists(Path(args.scrutiny_dir) / filename)


def validate_outputs(
    output_dir: Path,
    contradiction_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
    cross_family_rows: list[dict[str, Any]],
) -> None:
    required_paths = (
        output_dir / "README.md",
        output_dir / "interpretation_summary.json",
        output_dir / "contradiction_resolution_rows.csv",
        output_dir / "branch_thermal_interpretation.csv",
        output_dir / "scientific_conclusions.csv",
        output_dir / "internal_only_decisions.csv",
        output_dir / "cross_family_claims_audit.csv",
        output_dir / "methods_interpretation.md",
        output_dir / "model_dependency_readiness.md",
        output_dir / "remaining_blockers.md",
    )
    for path in required_paths:
        require_exists(path)
        if path.suffix in {".md", ".json"} and path.stat().st_size == 0:
            raise RuntimeError(f"Output file is unexpectedly empty: {path}")

    found = {(row["case_id"], row["branch"]) for row in contradiction_rows}
    missing = [pair for pair in EXPECTED_CONTRADICTION_CASES if pair not in found]
    if missing:
        raise RuntimeError(f"Expected contradiction rows were not analyzed: {missing}")

    right_leg_promoted = [
        row
        for row in branch_rows
        if row["branch"] == "right_leg" and row["headline_allowed"] == "yes"
    ]
    if right_leg_promoted:
        raise RuntimeError("right_leg was accidentally promoted to headline_allowed=yes")

    blocked_cross_family = [
        row for row in cross_family_rows
        if row["potential_claim"] == "Cross-family hydraulic branch dependency on left_lower_leg"
    ]
    if not blocked_cross_family or blocked_cross_family[0]["status"] != "blocked_by_unresolved_hydraulic_contradiction":
        raise RuntimeError("Cross-family hydraulic left_lower_leg claim was not blocked correctly.")

    load_json(output_dir / "interpretation_summary.json")


def main() -> None:
    args = parse_args()
    validate_inputs(args)

    output_dir = ensure_dir(Path(args.output_dir).resolve())
    packages = build_packages(Path(args.package_index).resolve())
    packages_by_source = {package["source_id"]: package for package in packages}
    claim_map = load_claim_map(Path(args.scrutiny_dir).resolve())

    contradiction_rows = contradiction_resolution_rows(packages_by_source)
    branch_rows = build_branch_thermal_interpretation(packages, claim_map)
    conclusions = build_scientific_conclusions(branch_rows, contradiction_rows)
    cross_family_rows = build_cross_family_claims_audit()
    internal_only_rows = build_internal_only_decisions(branch_rows, contradiction_rows)

    interpretation_summary = {
        "generated_at": iso_timestamp(),
        "package_name": output_dir.name,
        "contradiction_rows_examined": len(contradiction_rows),
        "resolved": sum(1 for row in contradiction_rows if row["recommended_status"] in {"resolved_use", "resolved_exclude"}),
        "unresolved": sum(1 for row in contradiction_rows if row["recommended_status"] == "unresolved_exclude"),
        "excluded": sum(1 for row in contradiction_rows if "exclude" in row["recommended_status"]),
        "branch_variable_family_combinations_examined": len(branch_rows),
        "headline_eligible": sum(1 for row in branch_rows if row["recommended_use"] == "headline_evidence"),
        "supporting_only": sum(1 for row in branch_rows if row["recommended_use"] == "supporting_evidence"),
        "contextual_only": sum(1 for row in branch_rows if row["recommended_use"] == "contextual_evidence"),
        "internal_only": sum(1 for row in branch_rows if row["recommended_use"] == "diagnostic_only"),
        "excluded_branch_rows": sum(1 for row in branch_rows if row["recommended_use"] == "exclude_from_headline"),
        "salt_only_conclusion_count": sum(1 for row in conclusions if row["conclusion_category"] == "stable_salt_only"),
        "water_only_conclusion_count": sum(1 for row in conclusions if row["conclusion_category"] == "stable_water_only"),
        "cross_family_conclusion_count": sum(1 for row in conclusions if row["conclusion_category"] == "cross_family"),
        "unresolved_blocker_count": 2,
    }

    csv_dump(
        output_dir / "contradiction_resolution_rows.csv",
        [
            "family",
            "case_id",
            "case_label",
            "branch",
            "variable_compared",
            "shear_based_sign",
            "direct_pressure_sign",
            "magnitude_ratio",
            "terminal_magnitude_ratio",
            "support_fraction",
            "signal_strength",
            "pressure_convention",
            "coordinate_convention",
            "suspected_cause",
            "confidence_level",
            "recommended_status",
            "explanation",
            "primary_source_path",
            "secondary_source_path",
        ],
        contradiction_rows,
    )
    csv_dump(
        output_dir / "branch_thermal_interpretation.csv",
        [
            "family_group",
            "family",
            "source_count",
            "case_labels",
            "source_ids",
            "primary_source_paths",
            "branch",
            "variable",
            "support_status",
            "sign_status",
            "interpretability_status",
            "headline_allowed",
            "internal_only",
            "primary_limitation",
            "recommended_use",
            "usable_fraction_min",
            "usable_fraction_max",
            "min_abs_bulk_minus_wall_temp_k_min",
            "min_abs_bulk_minus_wall_temp_k_max",
            "mean_metric_min",
            "mean_metric_max",
            "explanation",
        ],
        branch_rows,
    )
    csv_dump(
        output_dir / "scientific_conclusions.csv",
        [
            "conclusion_id",
            "conclusion_category",
            "family",
            "branch",
            "variable_family",
            "strength_of_evidence",
            "claim_text",
            "supporting_files",
            "supporting_row_subset",
            "caveat",
            "recommended_use",
            "safe_for_model_dependency_construction",
        ],
        conclusions,
    )
    csv_dump(
        output_dir / "internal_only_decisions.csv",
        [
            "family",
            "branch",
            "variable",
            "decision",
            "support_status",
            "primary_limitation",
            "explanation",
        ],
        internal_only_rows,
    )
    csv_dump(
        output_dir / "cross_family_claims_audit.csv",
        [
            "claim_id",
            "potential_claim",
            "status",
            "allowed_scope",
            "required_caveat",
            "blocked_reason_if_any",
        ],
        cross_family_rows,
    )
    json_dump(output_dir / "interpretation_summary.json", interpretation_summary)
    (output_dir / "methods_interpretation.md").write_text(
        build_methods_interpretation(contradiction_rows),
        encoding="utf-8",
    )
    (output_dir / "model_dependency_readiness.md").write_text(
        build_model_dependency_readiness(contradiction_rows),
        encoding="utf-8",
    )
    (output_dir / "remaining_blockers.md").write_text(
        build_remaining_blockers(contradiction_rows),
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        build_readme(
            package_name=output_dir.name,
            args=args,
            interpretation_summary=interpretation_summary,
            contradiction_rows=contradiction_rows,
            branch_rows=branch_rows,
            conclusions=conclusions,
            cross_family_audit=cross_family_rows,
            internal_only_rows=internal_only_rows,
        ),
        encoding="utf-8",
    )

    validate_outputs(output_dir, contradiction_rows, branch_rows, cross_family_rows)


if __name__ == "__main__":
    main()
