#!/usr/bin/env python3
"""Build Phase H2 passive heat-loss attribution audit from existing evidence.

This is a train-only diagnostic post-processing pass. It does not run Fluid,
score protected splits, fit coefficients, or admit a repair.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution"

PHASE_E = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve"
PHASE_H = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity"
SOURCE_SINK = REPO / "work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery"
HEATED_AUDIT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_heated_incline_tw4_tw6_local_audit"


CLAIM_BOUNDARY = (
    "train-only diagnostic post-processing; no Fluid run, no fitting, no model "
    "selection, no repair execution, no freeze/admission, no validation/holdout/"
    "external-test scoring"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def fnum(value: str | float | int | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def response_lookup(sensor_delta: list[dict[str, str]], sensor: str = "TW5") -> dict[str, dict[str, float | str]]:
    out: dict[str, dict[str, float | str]] = {}
    for row in sensor_delta:
        if row.get("sensor") != sensor:
            continue
        out[row["sensitivity_id"]] = {
            "baseline_residual_K": fnum(row.get("baseline_residual_K"), math.nan),
            "candidate_residual_K": fnum(row.get("candidate_residual_K"), math.nan),
            "delta_residual_K": fnum(row.get("delta_residual_K"), math.nan),
            "baseline_abs_residual_K": fnum(row.get("baseline_abs_residual_K"), math.nan),
            "candidate_abs_residual_K": fnum(row.get("candidate_abs_residual_K"), math.nan),
            "delta_abs_residual_K": fnum(row.get("delta_abs_residual_K"), math.nan),
            "response_class": row.get("response_class", ""),
        }
    return out


def metric_lookup(metrics: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["sensitivity_id"]: row for row in metrics}


def build_family_contribution(role_rows: list[dict[str, str]], tw5: dict[str, dict[str, float | str]]) -> list[dict[str, object]]:
    family = defaultdict(lambda: {"row_count": 0, "hA": 0.0, "area": 0.0, "h_area_rows_ok": 0, "parents": set(), "source_paths": set()})
    for row in role_rows:
        key = row["source_segment_id"]
        h = fnum(row.get("h_W_m2K"))
        area = fnum(row.get("area_m2"))
        cov = fnum(row.get("coverage_multiplier"), 1.0)
        hA = fnum(row.get("hA_W_K"))
        family[key]["row_count"] += 1
        family[key]["hA"] += hA
        family[key]["area"] += area
        family[key]["parents"].add(row.get("parent_segment", ""))
        family[key]["source_paths"].add(row.get("source_paths", ""))
        if abs((h * area * cov) - hA) <= max(1e-12, abs(hA) * 1e-9):
            family[key]["h_area_rows_ok"] += 1

    total_hA = sum(v["hA"] for v in family.values())
    non_lower_hA = sum(v["hA"] for k, v in family.items() if k != "lower_leg")
    global_improvement = -float(tw5["global_passive_hA_scale_0.5"]["delta_abs_residual_K"])
    lower_improvement = -float(tw5["lower_leg_hA_scale_0.5"]["delta_abs_residual_K"])
    remainder = global_improvement - lower_improvement

    rows: list[dict[str, object]] = []
    for key, data in sorted(family.items(), key=lambda item: item[1]["hA"], reverse=True):
        hA = data["hA"]
        hA_share = hA / total_hA if total_hA else 0.0
        if key == "lower_leg":
            basis = "observed_one_at_a_time_lower_leg_scale_0.5"
            tw5_improvement = lower_improvement
            share_of_global = lower_improvement / global_improvement if global_improvement else 0.0
        else:
            basis = "allocated_global_remainder_by_non_lower_hA_share"
            tw5_improvement = remainder * (hA / non_lower_hA) if non_lower_hA else 0.0
            share_of_global = tw5_improvement / global_improvement if global_improvement else 0.0
        rows.append(
            {
                "source_family": key,
                "row_count": data["row_count"],
                "parent_segments": ";".join(sorted(p for p in data["parents"] if p)),
                "baseline_hA_W_K": hA,
                "baseline_area_m2": data["area"],
                "hA_share_of_passive_network": hA_share,
                "tw5_abs_improvement_K": tw5_improvement,
                "tw5_global_improvement_share": share_of_global,
                "contribution_basis": basis,
                "all_h_area_products_close": data["h_area_rows_ok"] == data["row_count"],
                "source_path_wallHeatFlux_present": any("wallHeatFlux" in path for path in data["source_paths"]),
                "diagnostic_interpretation": (
                    "direct lower-leg response is small relative to global response"
                    if key == "lower_leg"
                    else "estimated member of broad non-lower-leg passive-network remainder"
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_segment_sweep(heat_rows: list[dict[str, str]], metrics: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    by_parent = defaultdict(lambda: {"Q": 0.0, "hA": 0.0, "segments": 0, "Tavg_weighted": 0.0, "source_families": set()})
    for row in heat_rows:
        parent = row["parent_segment"]
        q = fnum(row.get("Q_ambient_W"))
        hA = fnum(row.get("mapped_external_hA_W_K"))
        by_parent[parent]["Q"] += q
        by_parent[parent]["hA"] += hA
        by_parent[parent]["segments"] += 1
        by_parent[parent]["Tavg_weighted"] += fnum(row.get("T_avg_K")) * abs(q)
        by_parent[parent]["source_families"].add(row.get("mapped_source_segments", ""))

    total_q = sum(v["Q"] for v in by_parent.values())
    global_q_delta = fnum(metrics["global_passive_hA_scale_0.5"].get("qambient_total_W")) - fnum(
        metrics["baseline_phase_e"].get("qambient_total_W")
    )
    rows: list[dict[str, object]] = []
    for parent, data in sorted(by_parent.items(), key=lambda item: abs(item[1]["Q"]), reverse=True):
        q = data["Q"]
        share = q / total_q if total_q else 0.0
        rows.append(
            {
                "parent_segment": parent,
                "subsegment_count": data["segments"],
                "mapped_source_families": ";".join(sorted(x for x in data["source_families"] if x)),
                "baseline_mapped_hA_W_K": data["hA"],
                "baseline_Q_ambient_W": q,
                "baseline_Q_ambient_share": share,
                "fixed_state_Q_change_for_hA_0.5_W": -0.5 * q,
                "observed_global_qambient_delta_allocated_by_baseline_Q_share_W": global_q_delta * share,
                "Q_weighted_Tavg_K": data["Tavg_weighted"] / abs(q) if q else "",
                "attribution_basis": "baseline heat ledger share; fixed-state estimate is not a rerun",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_hA_audit(role_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in role_rows:
        h = fnum(row.get("h_W_m2K"))
        area = fnum(row.get("area_m2"))
        cov = fnum(row.get("coverage_multiplier"), 1.0)
        hA = fnum(row.get("hA_W_K"))
        calc = h * area * cov
        rel = abs(calc - hA) / abs(hA) if hA else 0.0
        plausible_h = 0.5 <= h <= 25.0
        rows.append(
            {
                "role_row_index": row["role_row_index"],
                "source_family": row["source_segment_id"],
                "parent_segment": row["parent_segment"],
                "patch_group": row["patch_group"],
                "h_W_m2K": h,
                "area_m2": area,
                "coverage_multiplier": cov,
                "hA_W_K": hA,
                "recomputed_hA_W_K": calc,
                "relative_hA_mismatch": rel,
                "h_area_unit_check": "pass" if rel <= 1e-9 and area > 0.0 and h > 0.0 else "review",
                "h_magnitude_screen": "plausible_order_of_magnitude" if plausible_h else "needs_physical_source_review",
                "source_path_wallHeatFlux_present": "wallHeatFlux" in row.get("source_paths", ""),
                "admissibility_concern": (
                    "magnitude plausible, but independent physical basis needed before repair/admission"
                    if plausible_h
                    else "h magnitude outside broad passive-convection screen"
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_sign_drive_audit(role_rows: list[dict[str, str]], heat_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    role_by_parent = defaultdict(list)
    for row in role_rows:
        role_by_parent[row["parent_segment"]].append(row)

    rows: list[dict[str, object]] = []
    for row in heat_rows:
        parent = row["parent_segment"]
        roles = role_by_parent.get(parent, [])
        role_ta_values = sorted({fnum(r.get("Ta_K")) for r in roles})
        role_ta = role_ta_values[0] if len(role_ta_values) == 1 else ""
        heat_ta = fnum(row.get("external_ambient_temperature_K"))
        tavg = fnum(row.get("T_avg_K"))
        q = fnum(row.get("Q_ambient_W"))
        expected_loss = tavg > heat_ta
        observed_loss = q > 0
        rows.append(
            {
                "segment_name": row["segment_name"],
                "parent_segment": parent,
                "mapped_source_segments": row.get("mapped_source_segments", ""),
                "role_row_count_for_parent": len(roles),
                "role_Ta_K": role_ta,
                "heat_ledger_external_ambient_temperature_K": heat_ta,
                "ambient_temperature_difference_K": (heat_ta - role_ta) if role_ta != "" else "",
                "T_avg_K": tavg,
                "Q_ambient_W": q,
                "expected_heat_loss_from_Tavg_gt_ambient": expected_loss,
                "observed_Qambient_positive": observed_loss,
                "sign_check": "pass" if expected_loss == observed_loss else "review",
                "drive_check": "review_role_vs_heat_ledger_Ta_offset" if role_ta != "" and abs(heat_ta - role_ta) > 0.5 else "pass",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_tw5_waterfall(tw5: dict[str, dict[str, float | str]], metrics: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    ordered = [
        ("phase_e_baseline", "baseline", None),
        ("lower_leg_hA_scale_0.5", "one_at_a_time", "lower-leg passive hA half"),
        ("lower_leg_hA_scale_2.0", "one_at_a_time", "lower-leg passive hA double"),
        ("global_passive_hA_scale_0.5", "global", "all passive hA half"),
        ("global_passive_hA_scale_2.0", "global", "all passive hA double"),
        ("ambient_drive_delta_+15K", "ambient_drive", "ambient drive plus 15 K"),
        ("ambient_drive_delta_-5K", "ambient_drive", "ambient drive minus 5 K"),
    ]
    baseline = tw5["global_passive_hA_scale_0.5"]["baseline_abs_residual_K"]
    rows: list[dict[str, object]] = []
    for sid, kind, note in ordered:
        if sid == "phase_e_baseline":
            rows.append(
                {
                    "stage": sid,
                    "sensitivity_kind": kind,
                    "description": "Phase E/F-J train diagnostic baseline",
                    "tw5_abs_residual_K": baseline,
                    "tw5_abs_improvement_vs_phase_e_K": 0.0,
                    "all_mae_K": metrics["baseline_phase_e"]["all_mae_K"],
                    "delta_all_mae_vs_phase_e_K": 0.0,
                    "interpretation": "large baseline thermal residual; not final predictive score",
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
            continue
        row = tw5[sid]
        metric = metrics[sid]
        improvement = -float(row["delta_abs_residual_K"])
        if sid == "global_passive_hA_scale_0.5":
            interp = "large response; candidate direction needs physical basis, not residual fit"
        elif sid.startswith("lower_leg"):
            interp = "localized lower-leg passive hA response is small"
        elif sid.startswith("ambient"):
            interp = "ambient-drive response is moderate and needs setup ambient provenance"
        else:
            interp = "diagnostic response"
        rows.append(
            {
                "stage": sid,
                "sensitivity_kind": kind,
                "description": note,
                "tw5_abs_residual_K": row["candidate_abs_residual_K"],
                "tw5_abs_improvement_vs_phase_e_K": improvement,
                "all_mae_K": metric["all_mae_K"],
                "delta_all_mae_vs_phase_e_K": metric["delta_all_mae_vs_phase_e_K"],
                "interpretation": interp,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_physical_plausibility(
    family_rows: list[dict[str, object]], hA_rows: list[dict[str, object]], sign_rows: list[dict[str, object]]
) -> list[dict[str, object]]:
    any_hA_review = any(row["h_area_unit_check"] != "pass" for row in hA_rows)
    any_sign_review = any(row["sign_check"] != "pass" for row in sign_rows)
    wallflux_source_count = sum(1 for row in hA_rows if row["source_path_wallHeatFlux_present"])
    lower = next(row for row in family_rows if row["source_family"] == "lower_leg")
    global_nonlower_improvement = sum(
        float(row["tw5_abs_improvement_K"]) for row in family_rows if row["source_family"] != "lower_leg"
    )
    return [
        {
            "study_item": "hA_area_unit_consistency",
            "observed_evidence": f"{sum(1 for row in hA_rows if row['h_area_unit_check'] == 'pass')}/{len(hA_rows)} role rows pass h*area*coverage recomputation",
            "physical_plausibility": "mechanically_consistent",
            "admissibility_status": "not_sufficient_for_repair",
            "reason": "unit consistency alone does not prove independent physical hA basis",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "study_item": "passive_h_magnitude",
            "observed_evidence": "all role h values fall inside broad 0.5-25 W/m2-K passive-convection screen",
            "physical_plausibility": "order_of_magnitude_plausible",
            "admissibility_status": "needs_independent_source",
            "reason": "broad plausibility does not license a train residual-driven global multiplier",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "study_item": "source_basis_independence",
            "observed_evidence": f"{wallflux_source_count}/{len(hA_rows)} passive role rows carry wallHeatFlux provenance paths",
            "physical_plausibility": "source_basis_not_independent_enough_for_final_repair",
            "admissibility_status": "blocked",
            "reason": "repair requires setup/geometry/literature hA source, not realized CFD heat-flux-derived residual absorption",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "study_item": "sign_and_drive",
            "observed_evidence": "sign failures present" if any_sign_review else "Qambient sign agrees with Tavg greater than ambient for reviewed heat-ledger rows",
            "physical_plausibility": "sign_ok" if not any_sign_review else "needs_review",
            "admissibility_status": "continue_audit" if not any_sign_review else "blocked_until_fixed",
            "reason": "role Ta and heat-ledger ambient differ by about 0.81 K on mapped rows, so ambient provenance should be reconciled",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "study_item": "lower_leg_locality",
            "observed_evidence": f"lower-leg hA half improves TW5 by {float(lower['tw5_abs_improvement_K']):.3f} K; allocated non-lower remainder is {global_nonlower_improvement:.3f} K",
            "physical_plausibility": "global_not_local",
            "admissibility_status": "not_a_lower_leg_passive_only_repair",
            "reason": "dominant response comes from broad non-lower passive-network change",
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]


def build_source_sink_matrix(source_rows: list[dict[str, str]], metrics: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    salt2_passive_loss = fnum(metrics["baseline_phase_e"]["qambient_total_W"]) + fnum(metrics["baseline_phase_e"]["qhx_total_W"])
    rows: list[dict[str, object]] = []
    for row in source_rows:
        setup = fnum(row.get("setup_value_W"))
        split = row.get("split_role", "")
        protected = split not in {"train", "support"}
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "split_role": split,
                "source_segment_id": row.get("source_segment_id", ""),
                "physical_role": row.get("physical_role", ""),
                "setup_patch_or_group": row.get("setup_patch_or_group", ""),
                "setup_value_W": setup,
                "runtime_allowed_now": row.get("runtime_allowed_now", ""),
                "provenance_class_after_recovery": row.get("provenance_class_after_recovery", ""),
                "salt2_phase_e_passive_plus_hx_loss_W_reference": salt2_passive_loss if row.get("case_id") == "salt_2" else "",
                "magnitude_ratio_to_salt2_phase_e_passive_plus_hx_loss": abs(setup) / salt2_passive_loss
                if row.get("case_id") == "salt_2" and salt2_passive_loss
                else "",
                "coupling_decision": "runtime_contract_needed_before_use" if row.get("runtime_allowed_now") == "false" else "already_runtime_allowed",
                "protected_split_scoring_status": "not_scored_metadata_only" if protected else "train_metadata_only_not_scored",
                "next_gate": (
                    "wait_for_setup_known_source_sink_contract_and_source_property_release"
                    if row.get("runtime_allowed_now") == "false"
                    else "eligible_for_separate_predeclared_train_run"
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_repair_gate(family_rows: list[dict[str, object]], plausibility_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    blocked_reasons = [
        row["reason"]
        for row in plausibility_rows
        if row["admissibility_status"] in {"blocked", "not_a_lower_leg_passive_only_repair", "needs_independent_source"}
    ]
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "candidate_name": "passive_hA_source_basis_rebuild_v1",
            "predeclared_change": "replace the broad passive hA basis with an independently sourced setup/geometry/literature passive-wall network; do not use the train-optimal global 0.5 multiplier as a fitted coefficient",
            "why_this_candidate": "global passive hA half produced the largest TW5/all-MAE response, while lower-leg-only passive hA did not localize the residual",
            "dominant_evidence": "global_passive_hA_scale_0.5 improved TW5 by 51.6337 K and all-probe MAE by 47.1336 K",
            "execution_status": "not_executed",
            "admission_status": "not_admitted",
            "required_before_execution": "independent hA/area/source-family basis; ambient Ta reconciliation; active source/sink contract rows complete; predeclared train-only run plan",
            "blocked_reasons": " | ".join(blocked_reasons),
            "forbidden_shortcut": "do not admit or score global_passive_hA_scale_0.5 as a repair because it is a train diagnostic sensitivity",
            "claim_boundary": CLAIM_BOUNDARY,
        }
    ]


def write_readme(summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/sensitivity_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/sensor_delta.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/role_row_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
tags: [forward-model, external-bc, heat-loss-attribution, train-only]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-PHASE-H2-PASSIVE-HEAT-LOSS-ATTRIBUTION-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-extbc-phase-h2-passive-heat-loss-attribution.md
  - imports/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution.json
task: TODO-FLUID-EXTBC-PHASE-H2-PASSIVE-HEAT-LOSS-ATTRIBUTION-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Phase H2 Passive Heat-Loss Attribution Audit

## Why This Exists

Phase H showed that the Phase E thermal residual is strongly responsive to
global passive hA scaling, but weakly responsive to lower-leg-only passive hA
scaling. This package asks whether that signal points to a row-family defect,
a segment cluster, or broad whole-loop passive-wall/source uncertainty.

## Open First

- `passive_hA_family_contribution.csv`
- `tw5_response_waterfall.csv`
- `physical_plausibility_matrix.csv`
- `source_sink_coupling_matrix.csv`
- `repair_candidate_predeclaration_gate.csv`

## Trusted Packages

- Phase E full train solve package.
- Phase F/J residual decomposition package.
- Phase H compute-safe sensitivity package.
- Source/sink provenance recovery package.
- Heated-incline TW4-TW6 audit package.

## Result

- Passive role rows reviewed: `{summary["passive_role_rows"]}`.
- Heat-ledger segment rows reviewed: `{summary["heat_ledger_rows"]}`.
- Source/sink metadata rows reviewed: `{summary["source_sink_rows"]}`.
- H2 decision: `{summary["decision"]}`.

The global passive hA response is broad rather than lower-leg-local. Lower-leg
hA half improves TW5 by `{summary["lower_leg_tw5_improvement_K"]:.6f} K`; the
global hA half improves TW5 by `{summary["global_tw5_improvement_K"]:.6f} K`.
The remaining response is allocated across non-lower-leg passive families only
as an attribution heuristic, not as a replacement for one-at-a-time sweeps.

## Output Contract

- `passive_hA_family_contribution.csv`: row-family hA shares and TW5 response attribution.
- `segment_heat_loss_sweep.csv`: segment heat-loss shares and fixed-state hA-scale proxy.
- `hA_area_unit_audit.csv`: h/area/hA consistency and provenance screen.
- `sign_and_drive_audit.csv`: heat-loss sign and ambient-drive consistency.
- `tw5_response_waterfall.csv`: Phase E to Phase H response waterfall.
- `physical_plausibility_matrix.csv`: follow-on study 1.
- `source_sink_coupling_matrix.csv`: follow-on study 2.
- `repair_candidate_predeclaration_gate.csv`: follow-on study 3.

## Do Not Do

Do not treat `global_passive_hA_scale_0.5` as an admitted repair. Do not score
validation, holdout, or external-test rows from this package. Do not use train
residuals to choose a coefficient. Do not mutate Fluid, native CFD/OpenFOAM
outputs, registry/admission state, blocker register, generated indexes, or
thesis current files from this row.
"""
    (OUT / "README.md").write_text(text)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    role_rows = read_csv(PHASE_E / "role_row_ledger.csv")
    heat_rows = read_csv(PHASE_E / "heat_path_ledger.csv")
    sensor_delta = read_csv(PHASE_H / "sensor_delta.csv")
    sensitivity_metrics = read_csv(PHASE_H / "sensitivity_metrics.csv")
    source_rows = read_csv(SOURCE_SINK / "setup_source_sink_provenance_ledger.csv")

    metrics = metric_lookup(sensitivity_metrics)
    baseline_all = fnum(metrics["global_passive_hA_scale_0.5"]["all_mae_K"]) - fnum(
        metrics["global_passive_hA_scale_0.5"]["delta_all_mae_vs_phase_e_K"]
    )
    baseline_tp = fnum(metrics["global_passive_hA_scale_0.5"]["tp_mae_K"]) - fnum(
        metrics["global_passive_hA_scale_0.5"]["delta_tp_mae_vs_phase_e_K"]
    )
    baseline_tw = fnum(metrics["global_passive_hA_scale_0.5"]["tw_mae_K"]) - fnum(
        metrics["global_passive_hA_scale_0.5"]["delta_tw_mae_vs_phase_e_K"]
    )
    metrics["baseline_phase_e"] = {
        "all_mae_K": baseline_all,
        "tp_mae_K": baseline_tp,
        "tw_mae_K": baseline_tw,
        "qambient_total_W": str(sum(fnum(row.get("Q_ambient_W")) for row in heat_rows)),
        "qhx_total_W": str(sum(fnum(row.get("Q_hx_sink_W")) for row in heat_rows)),
    }

    tw5 = response_lookup(sensor_delta, "TW5")

    family_rows = build_family_contribution(role_rows, tw5)
    segment_rows = build_segment_sweep(heat_rows, metrics)
    hA_rows = build_hA_audit(role_rows)
    sign_rows = build_sign_drive_audit(role_rows, heat_rows)
    waterfall_rows = build_tw5_waterfall(tw5, metrics)
    plausibility_rows = build_physical_plausibility(family_rows, hA_rows, sign_rows)
    source_sink_rows = build_source_sink_matrix(source_rows, metrics)
    repair_rows = build_repair_gate(family_rows, plausibility_rows)

    write_csv(
        OUT / "passive_hA_family_contribution.csv",
        family_rows,
        [
            "source_family",
            "row_count",
            "parent_segments",
            "baseline_hA_W_K",
            "baseline_area_m2",
            "hA_share_of_passive_network",
            "tw5_abs_improvement_K",
            "tw5_global_improvement_share",
            "contribution_basis",
            "all_h_area_products_close",
            "source_path_wallHeatFlux_present",
            "diagnostic_interpretation",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "segment_heat_loss_sweep.csv",
        segment_rows,
        [
            "parent_segment",
            "subsegment_count",
            "mapped_source_families",
            "baseline_mapped_hA_W_K",
            "baseline_Q_ambient_W",
            "baseline_Q_ambient_share",
            "fixed_state_Q_change_for_hA_0.5_W",
            "observed_global_qambient_delta_allocated_by_baseline_Q_share_W",
            "Q_weighted_Tavg_K",
            "attribution_basis",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "hA_area_unit_audit.csv",
        hA_rows,
        [
            "role_row_index",
            "source_family",
            "parent_segment",
            "patch_group",
            "h_W_m2K",
            "area_m2",
            "coverage_multiplier",
            "hA_W_K",
            "recomputed_hA_W_K",
            "relative_hA_mismatch",
            "h_area_unit_check",
            "h_magnitude_screen",
            "source_path_wallHeatFlux_present",
            "admissibility_concern",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "sign_and_drive_audit.csv",
        sign_rows,
        [
            "segment_name",
            "parent_segment",
            "mapped_source_segments",
            "role_row_count_for_parent",
            "role_Ta_K",
            "heat_ledger_external_ambient_temperature_K",
            "ambient_temperature_difference_K",
            "T_avg_K",
            "Q_ambient_W",
            "expected_heat_loss_from_Tavg_gt_ambient",
            "observed_Qambient_positive",
            "sign_check",
            "drive_check",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "tw5_response_waterfall.csv",
        waterfall_rows,
        [
            "stage",
            "sensitivity_kind",
            "description",
            "tw5_abs_residual_K",
            "tw5_abs_improvement_vs_phase_e_K",
            "all_mae_K",
            "delta_all_mae_vs_phase_e_K",
            "interpretation",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "physical_plausibility_matrix.csv",
        plausibility_rows,
        [
            "study_item",
            "observed_evidence",
            "physical_plausibility",
            "admissibility_status",
            "reason",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "source_sink_coupling_matrix.csv",
        source_sink_rows,
        [
            "case_id",
            "split_role",
            "source_segment_id",
            "physical_role",
            "setup_patch_or_group",
            "setup_value_W",
            "runtime_allowed_now",
            "provenance_class_after_recovery",
            "salt2_phase_e_passive_plus_hx_loss_W_reference",
            "magnitude_ratio_to_salt2_phase_e_passive_plus_hx_loss",
            "coupling_decision",
            "protected_split_scoring_status",
            "next_gate",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "repair_candidate_predeclaration_gate.csv",
        repair_rows,
        [
            "candidate_id",
            "candidate_name",
            "predeclared_change",
            "why_this_candidate",
            "dominant_evidence",
            "execution_status",
            "admission_status",
            "required_before_execution",
            "blocked_reasons",
            "forbidden_shortcut",
            "claim_boundary",
        ],
    )

    source_manifest = [
        {
            "source_path": str(PHASE_E / "role_row_ledger.csv"),
            "use": "passive external role rows and hA/area/unit audit",
            "mutation": "read_only",
        },
        {
            "source_path": str(PHASE_E / "heat_path_ledger.csv"),
            "use": "baseline segment heat-loss ledger",
            "mutation": "read_only",
        },
        {
            "source_path": str(PHASE_H / "sensitivity_metrics.csv"),
            "use": "Phase H residual and heat-total response",
            "mutation": "read_only",
        },
        {
            "source_path": str(PHASE_H / "sensor_delta.csv"),
            "use": "TW5 and per-sensor response deltas",
            "mutation": "read_only",
        },
        {
            "source_path": str(SOURCE_SINK / "setup_source_sink_provenance_ledger.csv"),
            "use": "setup-known source/sink coupling metadata",
            "mutation": "read_only",
        },
        {
            "source_path": str(HEATED_AUDIT / "failure_classification.csv"),
            "use": "heated-incline failure interpretation context",
            "mutation": "read_only_context",
        },
    ]
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_path", "use", "mutation"])

    lower_improvement = next(row for row in family_rows if row["source_family"] == "lower_leg")["tw5_abs_improvement_K"]
    global_improvement = -float(tw5["global_passive_hA_scale_0.5"]["delta_abs_residual_K"])
    non_lower_share = 1.0 - (float(lower_improvement) / global_improvement)
    summary = {
        "task_id": "TODO-FLUID-EXTBC-PHASE-H2-PASSIVE-HEAT-LOSS-ATTRIBUTION-2026-07-21",
        "date": "2026-07-21",
        "status": "complete",
        "passive_role_rows": len(role_rows),
        "heat_ledger_rows": len(heat_rows),
        "source_sink_rows": len(source_rows),
        "lower_leg_tw5_improvement_K": lower_improvement,
        "global_tw5_improvement_K": global_improvement,
        "non_lower_allocated_tw5_improvement_share": non_lower_share,
        "hA_unit_rows_passed": sum(1 for row in hA_rows if row["h_area_unit_check"] == "pass"),
        "hA_unit_rows_total": len(hA_rows),
        "sign_rows_passed": sum(1 for row in sign_rows if row["sign_check"] == "pass"),
        "sign_rows_total": len(sign_rows),
        "repair_candidates_executed": 0,
        "repair_candidates_admitted": 0,
        "validation_rows_scored": 0,
        "holdout_rows_scored": 0,
        "external_test_rows_scored": 0,
        "fit_or_model_selection": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "decision": "global_passive_hA_response_broad_and_physical_basis_needed_before_repair",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)


if __name__ == "__main__":
    main()
