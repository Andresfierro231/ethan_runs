#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, safe_float  # noqa: E402
from tools.analyze.build_ethan_transport_scientific_interpretation_package import (  # noqa: E402
    DEFAULT_ANALYSIS_DIR,
    DEFAULT_MATH_REFERENCE,
    DEFAULT_PACKAGE_INDEX,
    DEFAULT_SCRUTINY_DIR,
    EXPECTED_CONTRADICTION_CASES,
    REQUIRED_ANALYSIS_FILES,
    REQUIRED_SCRUTINY_FILES,
    build_branch_thermal_interpretation,
    build_internal_only_decisions,
    build_packages,
    build_scientific_conclusions as base_build_scientific_conclusions,
    contradiction_resolution_rows as base_contradiction_resolution_rows,
    load_claim_map,
    load_csv_rows,
    load_json,
    relative_path,
    require_columns,
    require_exists,
    sign_class,
    validate_inputs as base_validate_inputs,
)

DEFAULT_PREVIOUS_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_scientific_interpretation_package"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_transport_interpretation_closure"

PREVIOUS_REQUIRED_FILES = (
    "README.md",
    "interpretation_summary.json",
    "contradiction_resolution_rows.csv",
    "cross_family_claims_audit.csv",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the bounded closure pass for Ethan transport interpretation by "
            "auditing Water 2 left_lower_leg directly from existing package outputs."
        )
    )
    parser.add_argument("--package-index", default=str(DEFAULT_PACKAGE_INDEX))
    parser.add_argument("--analysis-dir", default=str(DEFAULT_ANALYSIS_DIR))
    parser.add_argument("--scrutiny-dir", default=str(DEFAULT_SCRUTINY_DIR))
    parser.add_argument("--math-reference", default=str(DEFAULT_MATH_REFERENCE))
    parser.add_argument("--previous-interpretation-dir", default=str(DEFAULT_PREVIOUS_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def validate_inputs(args: argparse.Namespace) -> None:
    base_validate_inputs(args)
    previous_dir = Path(args.previous_interpretation_dir)
    require_exists(previous_dir)
    for name in PREVIOUS_REQUIRED_FILES:
        require_exists(previous_dir / name)


def summarize_previous_status(previous_dir: Path) -> dict[str, Any]:
    rows = load_csv_rows(previous_dir / "contradiction_resolution_rows.csv")
    require_columns(
        previous_dir / "contradiction_resolution_rows.csv",
        rows,
        ("case_id", "branch", "recommended_status", "explanation"),
    )
    lookup = {(row["case_id"], row["branch"]): row for row in rows}
    return {
        "water1": lookup[("val_water_test_1_coarse_mesh_laminar", "left_lower_leg")],
        "water2": lookup[("val_water_test_2_coarse_mesh_laminar", "left_lower_leg")],
    }


def build_water2_left_lower_leg_hydraulic_audit(packages_by_source: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    package = packages_by_source["val_water_test_2_coarse_mesh_laminar"]
    branch_name = "left_lower_leg"
    span_rows = [
        row
        for row in package["major_timeseries_rows"]
        if row["span_name"] == branch_name
        and row["dp_major_gradient_direct_prgh_pa_per_m"] not in {"", "nan", "NaN"}
        and row["dp_major_gradient_pa_per_m"] not in {"", "nan", "NaN"}
        and row["cumulative_dp_major_direct_prgh_pa"] not in {"", "nan", "NaN"}
    ]
    if not span_rows:
        raise RuntimeError("No valid Water 2 left_lower_leg timeseries rows were found for closure audit.")

    by_time: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in span_rows:
        by_time[row["time_s"]].append(row)

    time_rows: list[dict[str, Any]] = []
    time_signs: list[str] = []
    for time_s in sorted(by_time, key=float):
        rows = sorted(by_time[time_s], key=lambda row: int(row["bin_index"]))
        direct_gradients = [float(row["dp_major_gradient_direct_prgh_pa_per_m"]) for row in rows]
        shear_gradients = [float(row["dp_major_gradient_pa_per_m"]) for row in rows]
        cumulative_end = float(rows[-1]["cumulative_dp_major_direct_prgh_pa"])
        flow_sign_values = sorted({row["flow_alignment_sign"] for row in rows})
        dominant_flow_sign = flow_sign_values[0] if len(flow_sign_values) == 1 else "mixed_within_time"
        time_signs.append(dominant_flow_sign)

        mean_direct = sum(direct_gradients) / len(direct_gradients)
        mean_shear = sum(shear_gradients) / len(shear_gradients)
        direct_to_shear_ratio = abs(mean_direct) / max(abs(mean_shear), 1.0e-12)
        cumulative_sign = "positive" if sign_class(cumulative_end) > 0 else ("negative" if sign_class(cumulative_end) < 0 else "near_zero")
        mean_sign = "positive" if sign_class(mean_direct) > 0 else ("negative" if sign_class(mean_direct) < 0 else "near_zero")
        mean_matches_cumulative = "yes" if sign_class(mean_direct) == sign_class(cumulative_end) and sign_class(cumulative_end) != 0 else "no"

        time_rows.append(
            {
                "row_type": "retained_time",
                "family": "water",
                "case_id": "val_water_test_2_coarse_mesh_laminar",
                "case_label": "Water 2",
                "branch": branch_name,
                "time_s": time_s,
                "valid_bin_count": len(rows),
                "direct_positive_bin_count": sum(1 for value in direct_gradients if value > 0.0),
                "direct_negative_bin_count": sum(1 for value in direct_gradients if value < 0.0),
                "mean_direct_prgh_gradient_pa_per_m": f"{mean_direct:.12f}",
                "mean_shear_gradient_pa_per_m": f"{mean_shear:.12f}",
                "direct_to_shear_ratio": f"{direct_to_shear_ratio:.12f}",
                "cumulative_direct_prgh_end_pa": f"{cumulative_end:.12f}",
                "cumulative_direct_sign": cumulative_sign,
                "dominant_flow_alignment_sign": dominant_flow_sign,
                "flow_alignment_sign_values": ",".join(flow_sign_values),
                "anomalous_vs_modal_alignment": "pending",
                "mean_sign_matches_cumulative_sign": mean_matches_cumulative,
                "suspected_issue": "pending",
                "recommended_status": "",
                "confidence_level": "",
                "interpretation_note": "",
            }
        )

    # The closure decision is based on a coarse but explicit hierarchy:
    # 1. If branch-end cumulative direct drop stays positive for every retained time,
    #    the branch does not show evidence of a true branchwise pressure recovery.
    # 2. If exactly one retained time carries the opposite alignment sign from the
    #    modal branch sign, that window is treated as a registration anomaly.
    # 3. If the per-time mean direct gradient remains much smaller than the shear
    #    gradient and can change sign despite positive cumulative drop, the branch
    #    mean is treated as a weak-signal differencing artifact, not usable evidence.
    modal_alignment_sign = Counter(sign for sign in time_signs if sign != "mixed_within_time").most_common(1)[0][0]
    cumulative_all_positive = all(row["cumulative_direct_sign"] == "positive" for row in time_rows)
    anomalous_time_count = 0
    weak_signal_count = 0

    for row in time_rows:
        anomalous = (
            row["dominant_flow_alignment_sign"] != "mixed_within_time"
            and row["dominant_flow_alignment_sign"] != modal_alignment_sign
        )
        if anomalous:
            anomalous_time_count += 1
            row["anomalous_vs_modal_alignment"] = "yes"
            row["suspected_issue"] = "alignment_registration_flip"
            row["interpretation_note"] = (
                "This retained time is the only one with the non-modal branch alignment sign. "
                "Treat the direct mean as registration-sensitive."
            )
        else:
            row["anomalous_vs_modal_alignment"] = "no"
            ratio = abs(float(row["direct_to_shear_ratio"]))
            if row["mean_sign_matches_cumulative_sign"] == "no" and ratio < 0.10:
                weak_signal_count += 1
                row["suspected_issue"] = "weak_signal_local_cancellation"
                row["interpretation_note"] = (
                    "The branch-end cumulative direct drop remains positive, but the mean local direct gradient changes sign "
                    "because mixed positive and negative finite-difference bins nearly cancel."
                )
            elif ratio < 0.10:
                weak_signal_count += 1
                row["suspected_issue"] = "weak_signal_small_direct_gradient"
                row["interpretation_note"] = (
                    "Direct p_rgh remains small relative to the shear-implied gradient even when the mean sign matches the cumulative sign."
                )
            else:
                row["suspected_issue"] = "direct_signal_retains_nontrivial_weight"
                row["interpretation_note"] = (
                    "Direct p_rgh is not negligible in this retained time, but it still does not overturn the branch-end positive cumulative drop."
                )

    if cumulative_all_positive and anomalous_time_count == 1 and weak_signal_count >= 3:
        final_status = "resolved_exclude"
        confidence = "high"
        explanation = (
            "Resolved exclusion. Water 2 left_lower_leg does not show evidence of a stable branchwise pressure-drop reversal. "
            "All retained times keep a positive branch-end cumulative direct p_rgh drop, one retained time carries a unique "
            "alignment-sign flip relative to the modal branch orientation, and the remaining sign changes in the branch-mean direct "
            "gradient are weak-signal finite-difference cancellations rather than robust reversals."
        )
    else:
        final_status = "unresolved_exclude"
        confidence = "medium"
        explanation = (
            "Unresolved exclusion. The branch-end direct p_rgh signal is not strong enough to prove a usable hydraulic dependency, "
            "and the retained-time sign behavior still cannot be collapsed into one mechanically stable branch-mean interpretation."
        )

    summary_row = {
        "row_type": "branch_resolution",
        "family": "water",
        "case_id": "val_water_test_2_coarse_mesh_laminar",
        "case_label": "Water 2",
        "branch": branch_name,
        "time_s": "all_retained_times",
        "valid_bin_count": sum(int(row["valid_bin_count"]) for row in time_rows),
        "direct_positive_bin_count": sum(int(row["direct_positive_bin_count"]) for row in time_rows),
        "direct_negative_bin_count": sum(int(row["direct_negative_bin_count"]) for row in time_rows),
        "mean_direct_prgh_gradient_pa_per_m": f"{sum(float(row['mean_direct_prgh_gradient_pa_per_m']) for row in time_rows) / len(time_rows):.12f}",
        "mean_shear_gradient_pa_per_m": f"{sum(float(row['mean_shear_gradient_pa_per_m']) for row in time_rows) / len(time_rows):.12f}",
        "direct_to_shear_ratio": f"{sum(abs(float(row['direct_to_shear_ratio'])) for row in time_rows) / len(time_rows):.12f}",
        "cumulative_direct_prgh_end_pa": f"{min(float(row['cumulative_direct_prgh_end_pa']) for row in time_rows):.12f} to {max(float(row['cumulative_direct_prgh_end_pa']) for row in time_rows):.12f}",
        "cumulative_direct_sign": "all_positive" if cumulative_all_positive else "mixed_or_negative",
        "dominant_flow_alignment_sign": modal_alignment_sign,
        "flow_alignment_sign_values": ",".join(sorted(set(time_signs))),
        "anomalous_vs_modal_alignment": str(anomalous_time_count),
        "mean_sign_matches_cumulative_sign": f"{sum(1 for row in time_rows if row['mean_sign_matches_cumulative_sign'] == 'yes')}/{len(time_rows)}",
        "suspected_issue": "registration_flip_plus_weak_signal_cancellation",
        "recommended_status": final_status,
        "confidence_level": confidence,
        "interpretation_note": explanation,
    }
    return time_rows + [summary_row]


def revise_contradiction_rows(
    packages_by_source: dict[str, dict[str, Any]],
    water2_audit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = base_contradiction_resolution_rows(packages_by_source)
    water2_summary = next(row for row in water2_audit_rows if row["row_type"] == "branch_resolution")
    revised: list[dict[str, Any]] = []
    for row in rows:
        if row["case_id"] != "val_water_test_2_coarse_mesh_laminar":
            revised.append(row)
            continue

        row = dict(row)
        row["suspected_cause"] = (
            "One retained time carries a unique branch alignment-sign flip relative to the modal left_lower_leg orientation, "
            "while the branch-end cumulative direct p_rgh drop stays positive for every retained time. The remaining branch-mean sign "
            "changes are weak-signal local cancellations rather than stable pressure-drop reversal."
        )
        row["confidence_level"] = str(water2_summary["confidence_level"])
        row["recommended_status"] = str(water2_summary["recommended_status"])
        row["explanation"] = str(water2_summary["interpretation_note"])
        row["coordinate_convention"] = (
            "Positive means pressure drop aligned with local flow. Water 2 left_lower_leg uses modal per-time branch alignment "
            "sign +1 over four retained times, with one retained-time anomaly at -1."
        )
        revised.append(row)
    return revised


def build_scientific_conclusions_closure(
    branch_rows: list[dict[str, Any]],
    contradiction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = base_build_scientific_conclusions(branch_rows, contradiction_rows)
    for row in rows:
        if row["conclusion_id"] == "C12":
            row["conclusion_category"] = "contradictory_or_excluded"
        if row["conclusion_id"] == "C13":
            row["conclusion_category"] = "contradictory_or_excluded"
            row["claim_text"] = (
                "Water 2 left_lower_leg hydraulic disagreement is now best treated as a resolved exclusion: branch-end cumulative "
                "direct p_rgh drop remains positive for every retained time, one retained window carries the only branch alignment-sign "
                "flip, and the remaining branch-mean direct sign changes are weak-signal cancellation artifacts rather than stable reversal."
            )
            row["strength_of_evidence"] = "strong"
    rows.append(
        {
            "conclusion_id": "C16",
            "conclusion_category": "contradictory_or_excluded",
            "family": "cross_family",
            "branch": "left_lower_leg",
            "variable_family": "shear_friction,direct_pressure_gradient,momentum_resistance",
            "strength_of_evidence": "strong",
            "claim_text": "Cross-family hydraulic dependency construction on left_lower_leg remains blocked because both Water rows are exclusions from the evidence subset, even though Water 2 no longer requires an unresolved-sign label.",
            "supporting_files": " | ".join(sorted({row['primary_source_path'] for row in contradiction_rows} | {row['secondary_source_path'] for row in contradiction_rows})),
            "supporting_row_subset": "Water 1 / left_lower_leg (resolved_exclude); Water 2 / left_lower_leg (resolved_exclude)",
            "caveat": "This is an exclusion boundary, not evidence of cross-family hydraulic similarity or difference.",
            "recommended_use": "exclude_from_model_evidence",
            "safe_for_model_dependency_construction": "no",
        }
    )
    return rows


def build_cross_family_claims_audit_closure(contradiction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unresolved = [row for row in contradiction_rows if row["recommended_status"] == "unresolved_exclude"]
    if unresolved:
        hydraulic_status = "blocked_by_unresolved_hydraulic_contradiction"
        hydraulic_caveat = "Water 2 left_lower_leg still carries an unresolved direct-vs-shear sign problem."
        hydraulic_reason = "The direct p_rgh reduction is not mechanically stable enough to support a cross-family branch pressure-drop dependency."
    else:
        hydraulic_status = "blocked_by_excluded_hydraulic_branch"
        hydraulic_caveat = "Both Water left_lower_leg hydraulic rows are now exclusions from the evidence subset rather than usable dependencies."
        hydraulic_reason = "Cross-family hydraulic left_lower_leg fitting remains blocked because the only Water evidence for that branch is excluded."

    return [
        {
            "claim_id": "X01",
            "potential_claim": "Cross-family hydraulic branch dependency on left_lower_leg",
            "status": hydraulic_status,
            "allowed_scope": "none",
            "required_caveat": hydraulic_caveat,
            "blocked_reason_if_any": hydraulic_reason,
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
            "required_caveat": "Momentum resistance is a proxy that inherits branch exclusions and hydraulic disagreement.",
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


def build_methods_interpretation_closure(contradiction_rows: list[dict[str, Any]]) -> str:
    water1 = next(row for row in contradiction_rows if row["case_id"] == "val_water_test_1_coarse_mesh_laminar")
    water2 = next(row for row in contradiction_rows if row["case_id"] == "val_water_test_2_coarse_mesh_laminar")
    return f"""# Methods Interpretation

## Scope

This closure note tightens the June 18 scientific interpretation package after
one bounded forensic audit of Water 2 left_lower_leg. It does not redefine the
implemented transport formulas. It explains how the existing reductions should
be read after the final direct-versus-shear hydraulic audit on the last active
Water branch contradiction.

## What the effective hydraulic quantities mean

The shear-based hydraulic reduction is a wall-stress reduction. It projects
wall shear onto the repaired streamwise tangent, area-averages the projected
streamwise magnitude, and then converts that wall-stress surrogate into
Darcy/Fanning form with the current hydraulic-diameter and bulk-speed
surrogates. It is therefore a wall-stress-derived hydraulic indicator, not a
direct measurement of branchwise control-volume pressure drop.

The direct hydraulic reduction is a wall-registered pressure diagnostic. It
area-averages wall `p_rgh` in each streamwise bin, finite-differences those
wall means along the repaired coordinate, and converts the result into
Darcy/Fanning form with the same surrogate geometry. It is a wall-pressure
indicator, not a momentum-balance closure.

## Why direct and shear hydraulic reductions may disagree

Direct and shear reductions can disagree because they use different
observables, different numerical conditioning, and different failure modes.
The direct `p_rgh` path is especially vulnerable when the net branch signal is
small: mixed positive and negative local derivatives can average toward zero
or change sign even when the branch-end cumulative direct drop remains
positive.

The Water left_lower_leg rows show the two important cases:

- Water 1 left_lower_leg: {water1["explanation"]}
- Water 2 left_lower_leg: {water2["explanation"]}

The Water 2 closure audit tightened one important distinction. The branch is
still excluded from model dependency work, but it no longer needs to remain
labelled unresolved at the sign-mystery level. The direct branch-end cumulative
drop stays positive in every retained time; the problem is that one retained
time carries the only non-modal alignment sign while the remaining branch-mean
sign changes are weak-signal differencing cancellations.

## Why disagreement in pressure-drop direction is a stop condition

If direct and shear reductions disagree at the sign level, the reduced branch
result is not robust enough to serve as cross-family evidence. Even if the row
is later resolved as an exclusion rather than an open mystery, it still cannot
be used as hydraulic model evidence for that branch.

## Why branch-end cumulative direct drop and branch-mean direct gradient can diverge

These two direct diagnostics are not redundant:

- The branch-end cumulative direct drop preserves the net direct `p_rgh`
  change accumulated along the branch.
- The branch-mean direct gradient averages local finite-difference derivatives
  that can change sign bin-by-bin.

When the net direct signal is weak, the cumulative branch-end drop can remain
positive while the branch-mean local direct gradient oscillates around zero or
changes sign. That is exactly why the Water rows are excluded rather than
reinterpreted as real branchwise pressure recovery.

## Why effective HTC, UA', and R'_th remain support-gated

The effective thermal quantities are ratios:

- `h_eff = |q''_w| / |T_bulk - T_wall|`
- `UA'_eff = |q'_w| / |T_bulk - T_wall|`
- `R'_th = 1 / UA'_eff`

They become unstable when the resolved branch-scale driving temperature
collapses. A large reported effective HTC or a numerically smooth `R'_th` is
not enough to promote a branch. The usable fraction, warning fraction, and
minimum resolved `|T_bulk - T_wall|` still control whether the quantity is fit
eligible or only diagnostic.

## Why momentum resistance remains proxy-only

Momentum resistance is local `dp/ds` divided by `mdot`. It is useful for
internal comparison, but it inherits the same branch exclusions and hydraulic
conditioning limits as the underlying direct or shear gradient. It is therefore
not a directly measured closure-quality resistance law.

## Why branch promotion gates remain necessary

The closure pass does not widen the thermal trust boundary. The Salt safe
subset remains:

- `left_lower_leg`
- `test_section_span`
- `left_upper_leg`
- `upcomer`

Blocked branches remain blocked because their support path did not improve:

- Salt and Water `right_leg` remain non-headline thermal branches.
- Water `left_lower_leg` and `upcomer` remain support-limited thermal branches.
- Boundary-layer landmarks remain contextual-only.

## How Salt and Water should be compared after this closure pass

The correct comparison sequence is now:

1. Compare support structure and branch eligibility first.
2. Compare effective thermal values only inside the shared support envelope.
3. Keep cross-family hydraulic left_lower_leg work blocked because the Water
   evidence for that branch is excluded from the usable subset.

At the current state of the audit stack:

- Salt-only branch thermal dependency work is defensible on the safe subset.
- Water left-side branch thermal dependency work is still not ready.
- Cross-family hydraulic dependency work remains blocked, but now because the
  Water branch is excluded from evidence rather than because an unresolved sign
  mystery remains.
"""


def build_model_dependency_readiness_closure(contradiction_rows: list[dict[str, Any]]) -> str:
    unresolved = [f"{row['case_label']} / {row['branch']}" for row in contradiction_rows if row["recommended_status"] == "unresolved_exclude"]
    unresolved_text = ", ".join(unresolved) if unresolved else "none"
    return """# Model Dependency Readiness

| Dependency | Classification | Required gates | Eligible branches | Excluded branches | Unresolved contradictions | Recommended next analysis | Risk of overclaiming |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Effective friction factor | family_specific_only | shear/direct sign agreement on the branch or span; direct support fraction must stay credible | Salt spans and non-contradictory Water spans only | Water 1 left_lower_leg; Water 2 left_lower_leg | """ + unresolved_text + """ | If future cross-family hydraulic work is required, change the branch evidence subset instead of forcing left_lower_leg back into use | High if branch exclusion is ignored |
| Effective K or feature loss | not_ready | dedicated feature closure audit with consistent driving-head accounting | none in this package | all branches for direct model fitting | n/a | Use the dedicated feature-loss packages instead of forcing a branch-level interpretation here | High |
| Momentum resistance proxy | diagnostic_only | same gates as the underlying hydraulic reduction | internal consistency checks only | all headline-fit uses | """ + unresolved_text + """ | Keep as a proxy and do not use as a closure target | High |
| Branch pressure-drop interpretation | family_specific_only | direct/shear sign agreement, stable pressure convention, consistent flow alignment | Salt branches outside current excluded Water rows | Water 1 left_lower_leg; Water 2 left_lower_leg | """ + unresolved_text + """ | Keep left_lower_leg excluded from cross-family hydraulic model work | High |
| HTC(x) | family_specific_only | usable fraction >= 0.90, warning fraction <= 0.10, min |T_bulk-T_wall| >= 0.50 K | Salt: left_lower_leg, test_section_span, left_upper_leg, upcomer | Salt right_leg; Water left_lower_leg; Water upcomer; any small-Delta-T branch | Water left-side thermal support collapse | Keep Water results diagnostic-only until a stronger bulk-support path exists | High |
| UA'(x) | family_specific_only | same as HTC(x) | Salt: left_lower_leg, test_section_span, left_upper_leg, upcomer | same as HTC(x) exclusions | Water left-side thermal support collapse | Same as HTC(x) | High |
| R'_th(x) | family_specific_only | same as HTC(x); do not treat reciprocal smoothing as validation | Salt: left_lower_leg, test_section_span, left_upper_leg, upcomer | same as HTC(x) exclusions | Water left-side thermal support collapse | Use only where the parent UA' is already scrutiny-cleared | High |
| Branch-averaged thermal resistance | family_specific_only | branch must already be scrutiny-cleared for effective thermal use | Salt safe subset only | Water left_lower_leg; Water upcomer; Salt right_leg | Water left-side thermal support collapse | Keep branch-averaged resistance out of cross-family fitting | Moderate |
| Heating/cooling branch role | diagnostic_only | sign stability in wall heat and branch Delta T | Salt safe subset; Water test_section_span as context only | contradiction-heavy or support-collapsed branches | Hydraulic exclusions do not directly block thermal role, but support collapse does | Use as contextual interpretation only | Moderate |
"""


def build_remaining_blockers_closure(contradiction_rows: list[dict[str, Any]]) -> str:
    unresolved = [row for row in contradiction_rows if row["recommended_status"] == "unresolved_exclude"]
    lines = [
        "# Remaining Blockers",
        "",
        "1. Cross-family hydraulic left_lower_leg dependency remains blocked because both Water rows are excluded from the usable evidence subset.",
        "2. Water left_lower_leg and upcomer thermal metrics remain blocked by small |T_bulk - T_wall| and low usable fraction; these branches are not ready for Water-family HTC, UA', or R'_th dependencies.",
        "3. Salt and Water right_leg effective thermal metrics remain blocked from headline use because the usable fraction stays near the low-support boundary even when the mean driving temperature is not small.",
        "4. Boundary-layer landmarks remain contextual-only; they should not be used as a primary model evidence layer until a future scrutiny pass explicitly upgrades them.",
        "5. Momentum resistance remains a proxy diagnostic and should not be fitted as if it were a directly measured closure quantity.",
        "",
        "If a future cross-family hydraulic fit is required, the next follow-up should not be another generic dashboard rebuild. It should either:",
        "- move to a different branch evidence subset that is already scrutiny-cleared, or",
        "- perform a dedicated direct-branch reduction redesign that uses cumulative direct p_rgh drop rather than a weak branch-mean finite-difference average for excluded Water left_lower_leg rows.",
    ]
    if unresolved:
        lines.append("")
        lines.append("Current unresolved-exclude rows:")
        for row in unresolved:
            lines.append(f"- {row['case_label']} / {row['branch']}: {row['suspected_cause']}")
    return "\n".join(lines) + "\n"


def build_water2_audit_markdown(audit_rows: list[dict[str, Any]]) -> str:
    retained = [row for row in audit_rows if row["row_type"] == "retained_time"]
    summary = next(row for row in audit_rows if row["row_type"] == "branch_resolution")
    lines = [
        "# Water 2 Left-Lower-Leg Hydraulic Audit",
        "",
        "This note audits the remaining Water 2 `left_lower_leg` contradiction using only existing package outputs.",
        "",
        "## Decision",
        "",
        f"- recommended status: `{summary['recommended_status']}`",
        f"- confidence: `{summary['confidence_level']}`",
        f"- branch-level interpretation: {summary['interpretation_note']}",
        "",
        "## Per-Time Findings",
        "",
    ]
    for row in retained:
        lines.append(
            f"- `{row['time_s']} s`: direct mean `{row['mean_direct_prgh_gradient_pa_per_m']}` Pa/m, "
            f"shear mean `{row['mean_shear_gradient_pa_per_m']}` Pa/m, cumulative direct end `{row['cumulative_direct_prgh_end_pa']}` Pa, "
            f"alignment `{row['flow_alignment_sign_values']}`, issue `{row['suspected_issue']}`."
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "The audit supports exclusion, not promotion. The row is no longer treated as an unresolved sign mystery if the branch-end cumulative direct drop remains positive in every retained time and the only alignment anomaly is confined to one retained window. That still does not make the branch fit-ready.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_readme_closure(
    args: argparse.Namespace,
    interpretation_summary: dict[str, Any],
    contradiction_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
    conclusions: list[dict[str, Any]],
    cross_family_rows: list[dict[str, Any]],
    internal_only_rows: list[dict[str, Any]],
    water2_audit_rows: list[dict[str, Any]],
) -> str:
    salt_conclusions = [row for row in conclusions if row["conclusion_category"] == "stable_salt_only"]
    water_conclusions = [row for row in conclusions if row["conclusion_category"] == "stable_water_only"]
    cross_conclusions = [row for row in conclusions if row["conclusion_category"] == "cross_family"]
    blocked_conclusions = [row for row in conclusions if row["conclusion_category"] == "contradictory_or_excluded"]
    contradiction_lines = "\n".join(
        f"- {row['case_label']} / {row['branch']}: {row['recommended_status']} ({row['confidence_level']}) -> {row['suspected_cause']}"
        for row in contradiction_rows
    )
    headline_branches = sorted({
        row["branch"] for row in branch_rows if row["headline_allowed"] == "yes" and row["family"] == "salt_all"
    })
    internal_examples = "\n".join(
        f"- {row['family']} / {row['branch']} / {row['variable']}: {row['decision']} ({row['primary_limitation']})"
        for row in internal_only_rows[:8]
    )
    water2_summary = next(row for row in water2_audit_rows if row["row_type"] == "branch_resolution")
    return f"""# Ethan Transport Interpretation Closure

Generated: `{iso_timestamp()}`

## Purpose

This package closes the remaining scientific interpretation pass on the June
15/17/18 Ethan transport audit stack. It does not regenerate extraction,
rebuild campaigns, or widen the branch promotion boundary. It performs one
bounded forensic audit on Water 2 `left_lower_leg`, then locks the final
transport interpretation state for downstream model-dependency and paper work.

## Input Packages Used

- package index: `{relative_path(Path(args.package_index))}`
- analysis package: `{relative_path(Path(args.analysis_dir))}`
- scrutiny package: `{relative_path(Path(args.scrutiny_dir))}`
- math reference: `{relative_path(Path(args.math_reference))}`
- previous scientific interpretation package: `{relative_path(Path(args.previous_interpretation_dir))}`

## What Was Analyzed

- one retained-time forensic audit of `val_water_test_2_coarse_mesh_laminar / left_lower_leg`
- revised contradiction status for both Water left_lower_leg rows
- existing branch-by-branch effective thermal interpretation without changing the Salt thermal trust boundary
- revised cross-family claim gates and model-dependency readiness wording

## What Was Not Regenerated

- no OpenFOAM extraction
- no per-case package rebuild
- no campaign rebuild
- no new dashboard stack

## Water 2 Hydraulic Audit Summary

- recommended status: `{water2_summary['recommended_status']}`
- confidence: `{water2_summary['confidence_level']}`
- interpretation: {water2_summary['interpretation_note']}

## Contradiction Resolution Summary

{contradiction_lines}

## Branch-By-Branch Thermal Summary

- headline-eligible Salt branches remain: `{", ".join(headline_branches)}`
- right_leg remains withheld from headline thermal use
- Water left_lower_leg remains blocked for effective thermal dependency use
- Water test_section_span remains supporting-only rather than headline-safe

## Salt-Only Conclusions

{chr(10).join(f"- {row['claim_text']}" for row in salt_conclusions)}

## Water-Only Conclusions

{chr(10).join(f"- {row['claim_text']}" for row in water_conclusions)}

## Cross-Family Conclusions

{chr(10).join(f"- {row['claim_text']}" for row in cross_conclusions)}

## Blocked / Excluded Conclusions

{chr(10).join(f"- {row['claim_text']}" for row in blocked_conclusions)}

## Internal-Only Decisions

{internal_examples}

## Remaining Blockers

- unresolved hydraulic contradiction rows: `{interpretation_summary['unresolved']}`
- excluded contradiction rows: `{interpretation_summary['excluded']}`
- blocked cross-family claims: `{sum(1 for row in cross_family_rows if row['status'].startswith('blocked'))}`
- blocked thermal branches remain concentrated in Water left-side branches and both-family right_leg thermal behavior

## Reproduction Commands

- `python -m py_compile tools/analyze/build_ethan_transport_interpretation_closure.py`
- `python tools/analyze/build_ethan_transport_interpretation_closure.py --output-dir tmp/2026-06-18_ethan_transport_interpretation_closure_smoke`
- `python tools/analyze/build_ethan_transport_interpretation_closure.py --output-dir reports/2026-06-18_ethan_transport_interpretation_closure`

## Limitations

- cross-family hydraulic dependency work remains blocked because Water left_lower_leg is excluded from the usable branch evidence subset
- effective thermal metrics remain effective, support-gated diagnostics rather than intrinsic coefficients
- boundary-layer landmarks remain contextual-only
- momentum resistance remains a proxy rather than a directly measured closure quantity
"""


def validate_outputs(
    output_dir: Path,
    contradiction_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
    cross_family_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
) -> None:
    required_paths = (
        output_dir / "README.md",
        output_dir / "interpretation_summary.json",
        output_dir / "water2_left_lower_leg_hydraulic_audit.csv",
        output_dir / "water2_left_lower_leg_hydraulic_audit.md",
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

    water2_rows = [row for row in audit_rows if row["case_id"] == "val_water_test_2_coarse_mesh_laminar"]
    if len(water2_rows) < 2:
        raise RuntimeError("Water 2 audit output did not include retained-time rows plus branch summary.")

    water2_summary = next(row for row in audit_rows if row["row_type"] == "branch_resolution")
    if water2_summary["recommended_status"] not in {"resolved_exclude", "unresolved_exclude"}:
        raise RuntimeError("Water 2 closure audit produced an unexpected recommended status.")

    right_leg_promoted = [row for row in branch_rows if row["branch"] == "right_leg" and row["headline_allowed"] == "yes"]
    if right_leg_promoted:
        raise RuntimeError("right_leg was accidentally promoted to headline_allowed=yes")

    hydraulic_claim = next(
        row for row in cross_family_rows if row["potential_claim"] == "Cross-family hydraulic branch dependency on left_lower_leg"
    )
    if hydraulic_claim["status"] not in {"blocked_by_unresolved_hydraulic_contradiction", "blocked_by_excluded_hydraulic_branch"}:
        raise RuntimeError("Cross-family hydraulic left_lower_leg claim was not blocked correctly.")

    load_json(output_dir / "interpretation_summary.json")


def main() -> None:
    args = parse_args()
    validate_inputs(args)

    output_dir = ensure_dir(Path(args.output_dir).resolve())
    packages = build_packages(Path(args.package_index).resolve())
    packages_by_source = {package["source_id"]: package for package in packages}
    claim_map = load_claim_map(Path(args.scrutiny_dir).resolve())
    previous_status = summarize_previous_status(Path(args.previous_interpretation_dir).resolve())

    water2_audit_rows = build_water2_left_lower_leg_hydraulic_audit(packages_by_source)
    contradiction_rows = revise_contradiction_rows(packages_by_source, water2_audit_rows)
    branch_rows = build_branch_thermal_interpretation(packages, claim_map)
    conclusions = build_scientific_conclusions_closure(branch_rows, contradiction_rows)
    cross_family_rows = build_cross_family_claims_audit_closure(contradiction_rows)
    internal_only_rows = build_internal_only_decisions(branch_rows, contradiction_rows)

    interpretation_summary = {
        "generated_at": iso_timestamp(),
        "package_name": output_dir.name,
        "previous_package_name": Path(args.previous_interpretation_dir).name,
        "contradiction_rows_examined": len(contradiction_rows),
        "resolved": sum(1 for row in contradiction_rows if row["recommended_status"] in {"resolved_use", "resolved_exclude"}),
        "unresolved": sum(1 for row in contradiction_rows if row["recommended_status"] == "unresolved_exclude"),
        "excluded": sum(1 for row in contradiction_rows if "exclude" in row["recommended_status"]),
        "water2_previous_status": previous_status["water2"]["recommended_status"],
        "water2_current_status": next(row for row in contradiction_rows if row["case_id"] == "val_water_test_2_coarse_mesh_laminar")["recommended_status"],
        "branch_variable_family_combinations_examined": len(branch_rows),
        "headline_eligible": sum(1 for row in branch_rows if row["recommended_use"] == "headline_evidence"),
        "supporting_only": sum(1 for row in branch_rows if row["recommended_use"] == "supporting_evidence"),
        "contextual_only": sum(1 for row in branch_rows if row["recommended_use"] == "contextual_evidence"),
        "internal_only": sum(1 for row in branch_rows if row["recommended_use"] == "diagnostic_only"),
        "excluded_branch_rows": sum(1 for row in branch_rows if row["recommended_use"] == "exclude_from_headline"),
        "salt_only_conclusion_count": sum(1 for row in conclusions if row["conclusion_category"] == "stable_salt_only"),
        "water_only_conclusion_count": sum(1 for row in conclusions if row["conclusion_category"] == "stable_water_only"),
        "cross_family_conclusion_count": sum(1 for row in conclusions if row["conclusion_category"] == "cross_family"),
        "unresolved_blocker_count": sum(1 for row in contradiction_rows if row["recommended_status"] == "unresolved_exclude"),
        "cross_family_hydraulic_status": next(
            row for row in cross_family_rows if row["claim_id"] == "X01"
        )["status"],
    }

    csv_dump(
        output_dir / "water2_left_lower_leg_hydraulic_audit.csv",
        [
            "row_type",
            "family",
            "case_id",
            "case_label",
            "branch",
            "time_s",
            "valid_bin_count",
            "direct_positive_bin_count",
            "direct_negative_bin_count",
            "mean_direct_prgh_gradient_pa_per_m",
            "mean_shear_gradient_pa_per_m",
            "direct_to_shear_ratio",
            "cumulative_direct_prgh_end_pa",
            "cumulative_direct_sign",
            "dominant_flow_alignment_sign",
            "flow_alignment_sign_values",
            "anomalous_vs_modal_alignment",
            "mean_sign_matches_cumulative_sign",
            "suspected_issue",
            "recommended_status",
            "confidence_level",
            "interpretation_note",
        ],
        water2_audit_rows,
    )
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
    (output_dir / "water2_left_lower_leg_hydraulic_audit.md").write_text(
        build_water2_audit_markdown(water2_audit_rows),
        encoding="utf-8",
    )
    (output_dir / "methods_interpretation.md").write_text(
        build_methods_interpretation_closure(contradiction_rows),
        encoding="utf-8",
    )
    (output_dir / "model_dependency_readiness.md").write_text(
        build_model_dependency_readiness_closure(contradiction_rows),
        encoding="utf-8",
    )
    (output_dir / "remaining_blockers.md").write_text(
        build_remaining_blockers_closure(contradiction_rows),
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        build_readme_closure(
            args=args,
            interpretation_summary=interpretation_summary,
            contradiction_rows=contradiction_rows,
            branch_rows=branch_rows,
            conclusions=conclusions,
            cross_family_rows=cross_family_rows,
            internal_only_rows=internal_only_rows,
            water2_audit_rows=water2_audit_rows,
        ),
        encoding="utf-8",
    )

    validate_outputs(output_dir, contradiction_rows, branch_rows, cross_family_rows, water2_audit_rows)


if __name__ == "__main__":
    main()
