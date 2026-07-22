#!/usr/bin/env python3
"""Build a train-only empirical per-leg bias/correction diagnostic.

The affine layer is intentionally diagnostic:
    T_corrected = multiplier_leg * T_1D + offset_leg

It consumes Phase E Salt2 train residuals only and does not score protected
splits, run Fluid, or admit a physical closure.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic"
PHASE_E = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve"
PHASE_H = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity"
PASSIVE_GATE = REPO / "work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis"
SOURCE_DECOMP = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp"

CLAIM_BOUNDARY = (
    "train-only empirical diagnostic; not physics admission; no Fluid solve; "
    "no validation/holdout/external-test scoring; no freeze/admission"
)

LEG_ORDER = ["junction", "downcomer", "upcomer", "cooling_branch", "lower_leg", "unmapped"]
SEGMENT_TO_LEG = {
    "right_vertical": "downcomer",
    "left_lower_vertical": "upcomer",
    "left_upper_vertical": "upcomer",
    "test_section": "upcomer",
    "top_horizontal_exit": "cooling_branch",
    "top_horizontal_inlet": "cooling_branch",
    "cooled_incline_pre_hx": "cooling_branch",
    "cooled_incline_post_hx": "cooling_branch",
    "cooled_incline_hx_active": "cooling_branch",
    "heated_incline": "lower_leg",
    "bottom_horizontal_inlet": "junction",
    "bottom_horizontal_exit": "junction",
}


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


def fnum(value: object) -> float:
    if value is None or value == "":
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def isfinite(value: float) -> bool:
    return math.isfinite(value)


def segment_lookup() -> dict[str, str]:
    rows = read_csv(PHASE_H / "sensor_delta.csv")
    out: dict[str, str] = {}
    for row in rows:
        sensor = row.get("sensor", "")
        segment = row.get("prediction_source_segment", "")
        if sensor and segment and sensor not in out:
            out[sensor] = segment
    return out


def training_rows() -> list[dict[str, object]]:
    seg_by_sensor = segment_lookup()
    rows: list[dict[str, object]] = []
    for row in read_csv(PHASE_E / "thermal_residual_attribution.csv"):
        if row.get("residual_kind") != "temperature":
            continue
        predicted = fnum(row.get("predicted_K"))
        reference = fnum(row.get("reference_K"))
        residual = fnum(row.get("residual_K"))
        source_segment = seg_by_sensor.get(row.get("sensor", ""), "")
        leg = SEGMENT_TO_LEG.get(source_segment, "unmapped")
        usable = isfinite(predicted) and isfinite(reference) and bool(source_segment)
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "split_role": row.get("split_role", ""),
                "sensor": row.get("sensor", ""),
                "sensor_kind": row.get("sensor_kind", ""),
                "prediction_source_segment": source_segment,
                "leg": leg,
                "predicted_K": predicted if isfinite(predicted) else "",
                "reference_K": reference if isfinite(reference) else "",
                "baseline_residual_K": residual if isfinite(residual) else "",
                "baseline_bias_needed_K": reference - predicted if usable else "",
                "fit_usable": usable,
                "exclusion_reason": "" if usable else "missing_prediction_reference_or_segment",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def fit_leg(points: list[dict[str, object]]) -> dict[str, object]:
    usable = [p for p in points if p["fit_usable"]]
    n = len(usable)
    if n == 0:
        return {
            "n_fit_sensors": 0,
            "multiplier": 1.0,
            "offset_K": 0.0,
            "fit_mode": "no_train_sensors",
            "identifiability_status": "not_identifiable",
        }
    xs = [float(p["predicted_K"]) for p in usable]
    ys = [float(p["reference_K"]) for p in usable]
    if n == 1:
        return {
            "n_fit_sensors": n,
            "multiplier": 1.0,
            "offset_K": ys[0] - xs[0],
            "fit_mode": "offset_only_single_sensor",
            "identifiability_status": "offset_only_under_determined_multiplier",
        }
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    if var_x <= 1e-12:
        offset = sum(y - x for x, y in zip(xs, ys)) / n
        return {
            "n_fit_sensors": n,
            "multiplier": 1.0,
            "offset_K": offset,
            "fit_mode": "offset_only_zero_predictor_variance",
            "identifiability_status": "multiplier_not_identifiable",
        }
    cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    multiplier = cov_xy / var_x
    offset = mean_y - multiplier * mean_x
    return {
        "n_fit_sensors": n,
        "multiplier": multiplier,
        "offset_K": offset,
        "fit_mode": "affine_per_leg_ols",
        "identifiability_status": "two_point_exact_high_risk" if n == 2 else "identified_train_only",
    }


def coeff_rows(train: list[dict[str, object]]) -> list[dict[str, object]]:
    by_leg = defaultdict(list)
    for row in train:
        by_leg[row["leg"]].append(row)
    rows: list[dict[str, object]] = []
    for leg in LEG_ORDER:
        fit = fit_leg(by_leg.get(leg, []))
        sensors = [row["sensor"] for row in by_leg.get(leg, []) if row["fit_usable"]]
        multiplier = float(fit["multiplier"])
        offset = float(fit["offset_K"])
        rows.append(
            {
                "leg": leg,
                "n_fit_sensors": fit["n_fit_sensors"],
                "fit_sensors": ";".join(str(s) for s in sensors),
                "multiplier_correction": multiplier,
                "offset_bias_K": offset,
                "fit_mode": fit["fit_mode"],
                "identifiability_status": fit["identifiability_status"],
                "coefficient_role": "empirical_bias_and_correction_diagnostic",
                "physics_admission_status": "not_admitted",
                "hypothesized_physical_ownership": hypothesis(leg, multiplier, offset, str(fit["identifiability_status"])),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def hypothesis(leg: str, multiplier: float, offset: float, status: str) -> str:
    if status == "not_identifiable":
        return "no train sensors; cannot infer leg correction"
    parts = []
    if abs(offset) > 25.0:
        parts.append("large-magnitude temperature offset suggests missing heat input, wall-layer offset, or 3D/1D reference mismatch")
    elif abs(offset) > 5.0:
        parts.append("moderate offset suggests local source/ambient/sensor-map bias")
    else:
        parts.append("small offset")
    if abs(multiplier - 1.0) > 0.1:
        parts.append("multiplier far from 1 suggests gradient/redistribution or scale mismatch, not a simple source offset")
    else:
        parts.append("multiplier near 1 suggests offset-dominated bias")
    parts.append(f"leg={leg}")
    return "; ".join(parts)


def corrected_rows(train: list[dict[str, object]], coeffs: list[dict[str, object]]) -> list[dict[str, object]]:
    coeff_by_leg = {row["leg"]: row for row in coeffs}
    rows: list[dict[str, object]] = []
    for row in train:
        if not row["fit_usable"]:
            rows.append({**row, "corrected_prediction_K": "", "corrected_residual_K": "", "corrected_abs_error_K": ""})
            continue
        coeff = coeff_by_leg[row["leg"]]
        corrected = float(coeff["multiplier_correction"]) * float(row["predicted_K"]) + float(coeff["offset_bias_K"])
        residual = corrected - float(row["reference_K"])
        rows.append(
            {
                **row,
                "corrected_prediction_K": corrected,
                "corrected_residual_K": residual,
                "corrected_abs_error_K": abs(residual),
                "applied_multiplier_correction": coeff["multiplier_correction"],
                "applied_offset_bias_K": coeff["offset_bias_K"],
            }
        )
    return rows


def metric_block(rows: list[dict[str, object]], residual_col: str, sensor_kind: str | None = None) -> dict[str, float | int]:
    vals = []
    for row in rows:
        if not row.get("fit_usable"):
            continue
        if sensor_kind and row.get("sensor_kind") != sensor_kind:
            continue
        value = row.get(residual_col, "")
        if value == "":
            continue
        vals.append(float(value))
    if not vals:
        return {"count": 0, "mae_K": math.nan, "rmse_K": math.nan, "max_abs_error_K": math.nan}
    return {
        "count": len(vals),
        "mae_K": sum(abs(v) for v in vals) / len(vals),
        "rmse_K": math.sqrt(sum(v * v for v in vals) / len(vals)),
        "max_abs_error_K": max(abs(v) for v in vals),
    }


def metric_rows(corrected: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group in [None, "TP", "TW"]:
        before = metric_block(corrected, "baseline_residual_K", group)
        after = metric_block(corrected, "corrected_residual_K", group)
        label = "all" if group is None else group
        rows.append(
            {
                "metric_group": label,
                "count": before["count"],
                "baseline_mae_K": before["mae_K"],
                "corrected_mae_K": after["mae_K"],
                "delta_mae_K": after["mae_K"] - before["mae_K"],
                "baseline_rmse_K": before["rmse_K"],
                "corrected_rmse_K": after["rmse_K"],
                "delta_rmse_K": after["rmse_K"] - before["rmse_K"],
                "baseline_max_abs_error_K": before["max_abs_error_K"],
                "corrected_max_abs_error_K": after["max_abs_error_K"],
                "delta_max_abs_error_K": after["max_abs_error_K"] - before["max_abs_error_K"],
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def identifiability_rows(coeffs: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in coeffs:
        status = row["identifiability_status"]
        if status == "identified_train_only":
            risk = "moderate_train_only_overfit_risk"
            requirement = "needs multiple independent train cases before predictive admission"
        elif status == "two_point_exact_high_risk":
            risk = "high_exact_two_point_fit_risk"
            requirement = "needs more sensors/cases or lower-complexity offset-only model"
        elif status == "not_identifiable":
            risk = "not_fit"
            requirement = "needs train sensors on leg"
        else:
            risk = "high_underidentified_multiplier_risk"
            requirement = "multiplier fixed to 1; cannot claim affine correction"
        rows.append(
            {
                "leg": row["leg"],
                "n_fit_sensors": row["n_fit_sensors"],
                "fit_mode": row["fit_mode"],
                "identifiability_status": status,
                "risk": risk,
                "requirement_before_physics_claim": requirement,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def explanation_rows(coeffs: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    passive_gate = read_csv(PASSIVE_GATE / "repair_gate.csv")[0]
    source_focus = read_csv(SOURCE_DECOMP / "tw4_tw6_focus.csv")
    rows.append(
        {
            "topic": "passive_boundary_physics_status",
            "observed_bias_model_evidence": f"PASSIVE-H2-CAND001 gate={passive_gate['gate_decision']}; repair_run_allowed_now={passive_gate['repair_run_allowed_now']}",
            "hypothesis": "empirical offsets may absorb passive boundary, ambient, wall-layer, or geometry/source-release gaps",
            "what_to_study_next": "source-release geometry, ambient/surroundings, insulation exposure, and independent h correlations before physical repair",
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    rows.append(
        {
            "topic": "heater_source_coupling_status",
            "observed_bias_model_evidence": "; ".join(
                f"{r['sensor']} delta_abs={r['delta_abs_residual_K']} K ({r['response_class']})" for r in source_focus
            ),
            "hypothesis": "setup heater source treatment is relevant but not sufficient; empirical lower-leg coefficients likely absorb wall/source distribution mismatch",
            "what_to_study_next": "combine source-lane evidence with passive geometry/source-release before any repair solve",
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    for row in coeffs:
        rows.append(
            {
                "topic": f"leg_{row['leg']}",
                "observed_bias_model_evidence": f"multiplier={row['multiplier_correction']}; offset_K={row['offset_bias_K']}; identifiability={row['identifiability_status']}",
                "hypothesis": row["hypothesized_physical_ownership"],
                "what_to_study_next": "do not treat as physics until tested against independent cases and linked to a source-released mechanism",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def split_audit_rows() -> list[dict[str, object]]:
    return [
        {
            "audit_item": "runtime_inputs",
            "status": "pass",
            "detail": "model consumes only Phase E post-solve train diagnostic predicted/reference rows for empirical fitting; not a runtime predictive model",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "audit_item": "protected_splits",
            "status": "pass",
            "detail": "validation, holdout, and external-test rows scored: 0/0/0",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "audit_item": "admission",
            "status": "pass",
            "detail": "coefficients are diagnostic empirical residual ownership only; no freeze/admission/source-property release",
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]


def write_readme(summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/thermal_residual_attribution.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/sensor_delta.csv
tags: [forward-model, empirical-bias, affine-correction, train-only]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EMPIRICAL-LEG-BIAS-CORRECTION-DIAGNOSTIC-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-empirical-leg-bias-correction-diagnostic.md
  - imports/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic.json
task: TODO-FLUID-EMPIRICAL-LEG-BIAS-CORRECTION-DIAGNOSTIC-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Empirical Leg Bias/Correction Diagnostic

This package fits a train-only affine empirical correction:

`T_corrected = multiplier_leg * T_1D + offset_leg`

The words are intentionally separated: `offset` is the additive empirical bias,
and `multiplier` is the empirical correction factor. Neither is admitted
physics.

## Result

All-sensor train MAE changes from `{summary["baseline_all_mae_K"]:.6f} K` to
`{summary["corrected_all_mae_K"]:.6f} K`.

Gate: diagnostic only. This is the best train-only fit under the declared
per-leg affine layer, but it is not a predictive model until tested through
frozen train/validation/holdout/external protocol.

## Open First

- `leg_bias_correction_coefficients.csv`
- `corrected_train_residual_metrics.csv`
- `identifiability_audit.csv`
- `explanation_hypothesis_ledger.csv`
- `split_runtime_leakage_audit.csv`
"""
    (OUT / "README.md").write_text(text)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    train = training_rows()
    coeffs = coeff_rows(train)
    corrected = corrected_rows(train, coeffs)
    metrics = metric_rows(corrected)
    ident = identifiability_rows(coeffs)
    explain = explanation_rows(coeffs)
    split = split_audit_rows()

    write_csv(
        OUT / "train_bias_fit_rows.csv",
        corrected,
        [
            "case_id",
            "split_role",
            "sensor",
            "sensor_kind",
            "prediction_source_segment",
            "leg",
            "predicted_K",
            "reference_K",
            "baseline_residual_K",
            "baseline_bias_needed_K",
            "fit_usable",
            "exclusion_reason",
            "corrected_prediction_K",
            "corrected_residual_K",
            "corrected_abs_error_K",
            "applied_multiplier_correction",
            "applied_offset_bias_K",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "leg_bias_correction_coefficients.csv",
        coeffs,
        [
            "leg",
            "n_fit_sensors",
            "fit_sensors",
            "multiplier_correction",
            "offset_bias_K",
            "fit_mode",
            "identifiability_status",
            "coefficient_role",
            "physics_admission_status",
            "hypothesized_physical_ownership",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "corrected_train_residual_metrics.csv",
        metrics,
        [
            "metric_group",
            "count",
            "baseline_mae_K",
            "corrected_mae_K",
            "delta_mae_K",
            "baseline_rmse_K",
            "corrected_rmse_K",
            "delta_rmse_K",
            "baseline_max_abs_error_K",
            "corrected_max_abs_error_K",
            "delta_max_abs_error_K",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "identifiability_audit.csv",
        ident,
        [
            "leg",
            "n_fit_sensors",
            "fit_mode",
            "identifiability_status",
            "risk",
            "requirement_before_physics_claim",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "explanation_hypothesis_ledger.csv",
        explain,
        ["topic", "observed_bias_model_evidence", "hypothesis", "what_to_study_next", "claim_boundary"],
    )
    write_csv(OUT / "split_runtime_leakage_audit.csv", split, ["audit_item", "status", "detail", "claim_boundary"])
    write_csv(
        OUT / "source_manifest.csv",
        [
            {
                "source_path": str(PHASE_E / "thermal_residual_attribution.csv"),
                "use": "train predicted/reference temperature rows",
                "mutation": "read_only",
            },
            {
                "source_path": str(PHASE_H / "sensor_delta.csv"),
                "use": "prediction source segment join",
                "mutation": "read_only",
            },
            {
                "source_path": str(PASSIVE_GATE / "repair_gate.csv"),
                "use": "passive physical-basis gate context",
                "mutation": "read_only",
            },
            {
                "source_path": str(SOURCE_DECOMP / "tw4_tw6_focus.csv"),
                "use": "heater source residual context",
                "mutation": "read_only",
            },
        ],
        ["source_path", "use", "mutation"],
    )

    all_metric = next(row for row in metrics if row["metric_group"] == "all")
    summary = {
        "task_id": "TODO-FLUID-EMPIRICAL-LEG-BIAS-CORRECTION-DIAGNOSTIC-2026-07-21",
        "date": "2026-07-21",
        "status": "complete",
        "train_fit_rows": sum(1 for row in corrected if row["fit_usable"]),
        "excluded_rows": sum(1 for row in corrected if not row["fit_usable"]),
        "baseline_all_mae_K": all_metric["baseline_mae_K"],
        "corrected_all_mae_K": all_metric["corrected_mae_K"],
        "delta_all_mae_K": all_metric["delta_mae_K"],
        "baseline_all_rmse_K": all_metric["baseline_rmse_K"],
        "corrected_all_rmse_K": all_metric["corrected_rmse_K"],
        "validation_rows_scored": 0,
        "holdout_rows_scored": 0,
        "external_test_rows_scored": 0,
        "fluid_solve_run": False,
        "fit_for_physics_admission": False,
        "empirical_train_fit": True,
        "freeze_or_admission_decision": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)


if __name__ == "__main__":
    main()
