#!/usr/bin/env python3
"""Build a reduced-DOF empirical bias/correction transfer screen.

This is a frozen-coefficient diagnostic screen, not a Fluid solve or model
admission. Coefficients are fit on Salt1/Salt2 TSWFC2 nominal sensor rows only
and then applied unchanged to Salt3/Salt4 legacy validation/holdout-style
stress rows.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen"
TSWFC2 = REPO / "work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard"
PREVIOUS = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic"
CLAIM_BOUNDARY = (
    "frozen reduced-DOF empirical transfer diagnostic; coefficients fit on "
    "Salt1/Salt2 train/support rows only; Salt3/Salt4 scored after freeze as "
    "legacy validation/holdout-style stress rows; no external-test score; "
    "no Fluid solve; no admission"
)

CASE_ROLES = {
    "Salt 1": {
        "case_id": "salt_1",
        "fit_role": "train_support_fit",
        "transfer_role": "fit_partition",
        "legacy_split_role": "train_support",
        "fit_allowed": True,
        "score_allowed": True,
    },
    "Salt 2": {
        "case_id": "salt_2",
        "fit_role": "train_support_fit",
        "transfer_role": "fit_partition",
        "legacy_split_role": "train_support",
        "fit_allowed": True,
        "score_allowed": True,
    },
    "Salt 3": {
        "case_id": "salt_3",
        "fit_role": "frozen_transfer_score_only",
        "transfer_role": "legacy_validation_transfer_stress",
        "legacy_split_role": "legacy_validation",
        "fit_allowed": False,
        "score_allowed": True,
    },
    "Salt 4": {
        "case_id": "salt_4",
        "fit_role": "frozen_transfer_score_only",
        "transfer_role": "legacy_holdout_transfer_stress",
        "legacy_split_role": "legacy_holdout",
        "fit_allowed": False,
        "score_allowed": True,
    },
}

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

LEG_TO_THERMAL_FAMILY = {
    "downcomer": "vertical_loop",
    "upcomer": "vertical_loop",
    "cooling_branch": "cooling_branch",
    "lower_leg": "heated_lower_leg",
    "junction": "junction",
    "unmapped": "unmapped",
}

FAMILIES = [
    {
        "model_family": "F0_null_baseline",
        "fit_form": "identity",
        "grouping": "none",
        "admissibility": "baseline_only",
        "interpretation": "No empirical bias/correction; reference score for all rows.",
    },
    {
        "model_family": "F1_global_offset",
        "fit_form": "offset",
        "grouping": "global",
        "admissibility": "low_dof_diagnostic",
        "interpretation": "Uniform additive temperature-reference or bulk/wall bias diagnostic.",
    },
    {
        "model_family": "F2_global_affine",
        "fit_form": "affine",
        "grouping": "global",
        "admissibility": "low_dof_high_caution",
        "interpretation": "One global multiplier plus offset; tests whether scale and reference bias transfer.",
    },
    {
        "model_family": "F3_sensor_kind_offset",
        "fit_form": "offset",
        "grouping": "sensor_kind",
        "admissibility": "low_dof_diagnostic",
        "interpretation": "Separate TP/TW offsets; tests bulk-vs-wall reduction bias.",
    },
    {
        "model_family": "F4_thermal_family_offset",
        "fit_form": "offset",
        "grouping": "thermal_family",
        "admissibility": "moderate_dof_diagnostic",
        "interpretation": "Offsets by vertical loop, cooling branch, and heated lower-leg heat-path roles.",
    },
    {
        "model_family": "F5_thermal_family_offset_shared_multiplier",
        "fit_form": "shared_affine",
        "grouping": "thermal_family",
        "admissibility": "moderate_dof_high_caution",
        "interpretation": "One shared multiplier plus heat-path offsets; most flexible reduced-DOF family scored here.",
    },
]


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


def finite(value: float) -> bool:
    return math.isfinite(value)


def group_key(row: dict[str, object], grouping: str) -> str:
    if grouping == "none":
        return "identity"
    if grouping == "global":
        return "global"
    if grouping == "sensor_kind":
        return str(row["sensor_kind"])
    if grouping == "thermal_family":
        return str(row["thermal_family"])
    raise ValueError(f"unknown grouping: {grouping}")


def load_sensor_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_name, role in CASE_ROLES.items():
        path = TSWFC2 / "case_outputs" / case_name.replace(" ", "_") / "validation_table.csv"
        for raw in read_csv(path):
            predicted = fnum(raw.get("predicted_K"))
            measured = fnum(raw.get("measured_K"))
            error = fnum(raw.get("error_K"))
            segment = raw.get("prediction_source_segment", "")
            leg = SEGMENT_TO_LEG.get(segment, "unmapped")
            usable = (
                str(raw.get("validation_excluded", "")).lower() != "true"
                and finite(predicted)
                and finite(measured)
                and raw.get("kind", "") in {"TP", "TW"}
                and leg != "unmapped"
            )
            rows.append(
                {
                    "case": case_name,
                    "case_id": role["case_id"],
                    "sensor": raw.get("sensor", ""),
                    "sensor_kind": raw.get("kind", ""),
                    "predicted_K": predicted if finite(predicted) else "",
                    "reference_K": measured if finite(measured) else "",
                    "baseline_residual_K": error if finite(error) else "",
                    "prediction_source_segment": segment,
                    "leg": leg,
                    "thermal_family": LEG_TO_THERMAL_FAMILY.get(leg, "unmapped"),
                    "fit_role": role["fit_role"],
                    "transfer_role": role["transfer_role"],
                    "legacy_split_role": role["legacy_split_role"],
                    "fit_allowed": role["fit_allowed"],
                    "score_allowed": role["score_allowed"],
                    "row_usable": usable,
                    "exclusion_reason": "" if usable else "missing_prediction_reference_or_mapped_segment",
                    "source_path": str(path),
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def ols_affine(points: list[dict[str, object]]) -> tuple[float, float, str]:
    xs = [float(p["predicted_K"]) for p in points]
    ys = [float(p["reference_K"]) for p in points]
    if not points:
        return 1.0, 0.0, "no_fit_rows"
    if len(points) == 1:
        return 1.0, ys[0] - xs[0], "offset_only_single_fit_row"
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    var_x = sum((x - mean_x) ** 2 for x in xs)
    if var_x <= 1e-12:
        return 1.0, sum(y - x for x, y in zip(xs, ys)) / len(xs), "offset_only_zero_predictor_variance"
    cov_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    multiplier = cov_xy / var_x
    return multiplier, mean_y - multiplier * mean_x, "ols_affine"


def mean_offset(points: list[dict[str, object]]) -> tuple[float, str]:
    if not points:
        return 0.0, "no_fit_rows"
    return sum(float(p["reference_K"]) - float(p["predicted_K"]) for p in points) / len(points), "mean_offset"


def fit_family(rows: list[dict[str, object]], family: dict[str, str]) -> list[dict[str, object]]:
    fit_rows = [r for r in rows if r["row_usable"] and r["fit_allowed"]]
    model = family["model_family"]
    form = family["fit_form"]
    grouping = family["grouping"]
    coeffs: list[dict[str, object]] = []
    if form == "identity":
        coeffs.append(
            {
                **family,
                "coefficient_group": "identity",
                "multiplier_correction": 1.0,
                "offset_bias_K": 0.0,
                "n_fit_rows": 0,
                "fit_status": "fixed_identity_no_fit",
                "coefficient_source": "predeclared_baseline",
                "degrees_of_freedom": 0,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
        return coeffs
    if form in {"offset", "affine"}:
        by_group: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in fit_rows:
            by_group[group_key(row, grouping)].append(row)
        for key in sorted(by_group):
            points = by_group[key]
            if form == "offset":
                offset, status = mean_offset(points)
                multiplier = 1.0
            else:
                multiplier, offset, status = ols_affine(points)
            coeffs.append(
                {
                    **family,
                    "coefficient_group": key,
                    "multiplier_correction": multiplier,
                    "offset_bias_K": offset,
                    "n_fit_rows": len(points),
                    "fit_status": status,
                    "coefficient_source": "Salt1_Salt2_train_support_fit_only",
                    "degrees_of_freedom": 1 if form == "offset" else 2,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
        return coeffs
    if form == "shared_affine":
        multiplier, _, status = ols_affine(fit_rows)
        for key in sorted({group_key(row, grouping) for row in fit_rows}):
            points = [row for row in fit_rows if group_key(row, grouping) == key]
            offset = sum(float(p["reference_K"]) - multiplier * float(p["predicted_K"]) for p in points) / len(points)
            coeffs.append(
                {
                    **family,
                    "coefficient_group": key,
                    "multiplier_correction": multiplier,
                    "offset_bias_K": offset,
                    "n_fit_rows": len(points),
                    "fit_status": f"shared_multiplier_{status}_group_offset",
                    "coefficient_source": "Salt1_Salt2_train_support_fit_only",
                    "degrees_of_freedom": "1_shared_multiplier_plus_group_offsets",
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
        return coeffs
    raise ValueError(f"unknown fit form: {form}")


def all_coefficients(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    coeffs: list[dict[str, object]] = []
    for family in FAMILIES:
        coeffs.extend(fit_family(rows, family))
    return coeffs


def coeff_lookup(coeffs: list[dict[str, object]]) -> dict[tuple[str, str], dict[str, object]]:
    return {(str(c["model_family"]), str(c["coefficient_group"])): c for c in coeffs}


def apply_coefficients(rows: list[dict[str, object]], coeffs: list[dict[str, object]]) -> list[dict[str, object]]:
    lookup = coeff_lookup(coeffs)
    scored: list[dict[str, object]] = []
    for family in FAMILIES:
        model = family["model_family"]
        grouping = family["grouping"]
        for row in rows:
            out = {
                "model_family": model,
                "fit_form": family["fit_form"],
                "grouping": grouping,
                "admissibility": family["admissibility"],
                **row,
            }
            if not row["row_usable"]:
                out.update(
                    {
                        "coefficient_group": "",
                        "multiplier_correction": "",
                        "offset_bias_K": "",
                        "corrected_prediction_K": "",
                        "corrected_residual_K": "",
                        "corrected_abs_error_K": "",
                        "coefficient_missing": True,
                    }
                )
                scored.append(out)
                continue
            key = group_key(row, grouping)
            if family["fit_form"] == "identity":
                key = "identity"
            coeff = lookup.get((model, key))
            if coeff is None:
                out.update(
                    {
                        "coefficient_group": key,
                        "multiplier_correction": "",
                        "offset_bias_K": "",
                        "corrected_prediction_K": "",
                        "corrected_residual_K": "",
                        "corrected_abs_error_K": "",
                        "coefficient_missing": True,
                    }
                )
                scored.append(out)
                continue
            corrected = float(coeff["multiplier_correction"]) * float(row["predicted_K"]) + float(coeff["offset_bias_K"])
            residual = corrected - float(row["reference_K"])
            out.update(
                {
                    "coefficient_group": key,
                    "multiplier_correction": coeff["multiplier_correction"],
                    "offset_bias_K": coeff["offset_bias_K"],
                    "corrected_prediction_K": corrected,
                    "corrected_residual_K": residual,
                    "corrected_abs_error_K": abs(residual),
                    "coefficient_missing": False,
                }
            )
            scored.append(out)
    return scored


def metric(values: list[float]) -> dict[str, float | int]:
    if not values:
        return {"count": 0, "mae_K": math.nan, "rmse_K": math.nan, "bias_K": math.nan, "max_abs_error_K": math.nan}
    return {
        "count": len(values),
        "mae_K": sum(abs(v) for v in values) / len(values),
        "rmse_K": math.sqrt(sum(v * v for v in values) / len(values)),
        "bias_K": sum(values) / len(values),
        "max_abs_error_K": max(abs(v) for v in values),
    }


def metric_rows(scored: list[dict[str, object]]) -> list[dict[str, object]]:
    groups = [
        ("train_support_fit", lambda r: r["fit_role"] == "train_support_fit"),
        ("legacy_validation_transfer_stress", lambda r: r["transfer_role"] == "legacy_validation_transfer_stress"),
        ("legacy_holdout_transfer_stress", lambda r: r["transfer_role"] == "legacy_holdout_transfer_stress"),
        ("all_frozen_transfer_nonfit", lambda r: r["fit_role"] == "frozen_transfer_score_only"),
        ("all_scored_rows", lambda r: r["row_usable"]),
    ]
    rows: list[dict[str, object]] = []
    for family in FAMILIES:
        model_rows = [r for r in scored if r["model_family"] == family["model_family"] and r["row_usable"] and not r["coefficient_missing"]]
        for split_group, pred in groups:
            selected = [r for r in model_rows if pred(r)]
            baseline = metric([float(r["baseline_residual_K"]) for r in selected])
            corrected = metric([float(r["corrected_residual_K"]) for r in selected])
            rows.append(
                {
                    "model_family": family["model_family"],
                    "split_group": split_group,
                    "count": corrected["count"],
                    "baseline_mae_K": baseline["mae_K"],
                    "corrected_mae_K": corrected["mae_K"],
                    "delta_mae_K": corrected["mae_K"] - baseline["mae_K"] if corrected["count"] else math.nan,
                    "baseline_rmse_K": baseline["rmse_K"],
                    "corrected_rmse_K": corrected["rmse_K"],
                    "delta_rmse_K": corrected["rmse_K"] - baseline["rmse_K"] if corrected["count"] else math.nan,
                    "corrected_bias_K": corrected["bias_K"],
                    "corrected_max_abs_error_K": corrected["max_abs_error_K"],
                    "selection_role": "train_support_ranking_only" if split_group == "train_support_fit" else "score_only_no_refit_no_selection",
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def dof_rows(coeffs: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in FAMILIES:
        fam_coeffs = [c for c in coeffs if c["model_family"] == family["model_family"]]
        if family["fit_form"] == "identity":
            dof = 0
        elif family["fit_form"] == "offset":
            dof = len(fam_coeffs)
        elif family["fit_form"] == "affine":
            dof = 2 * len(fam_coeffs)
        else:
            dof = 1 + len(fam_coeffs)
        rows.append(
            {
                "model_family": family["model_family"],
                "fit_form": family["fit_form"],
                "grouping": family["grouping"],
                "predeclared": "yes",
                "degrees_of_freedom": dof,
                "coefficient_groups": ";".join(str(c["coefficient_group"]) for c in fam_coeffs),
                "admissibility": family["admissibility"],
                "interpretation": family["interpretation"],
                "reduced_vs_prior_per_leg_affine": "yes" if dof < 10 else "no",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    rows.append(
        {
            "model_family": "prior_per_leg_affine_not_rescored",
            "fit_form": "per_leg_affine",
            "grouping": "junction;downcomer;upcomer;cooling_branch;lower_leg",
            "predeclared": "no_for_this_screen",
            "degrees_of_freedom": 10,
            "coefficient_groups": "see previous package",
            "admissibility": "too_high_dof_for_transfer_screen",
            "interpretation": "Previous upper-bound diagnostic retained as context only.",
            "reduced_vs_prior_per_leg_affine": "reference",
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    return rows


def transfer_summary_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in FAMILIES:
        train = next(
            r for r in metrics if r["model_family"] == family["model_family"] and r["split_group"] == "train_support_fit"
        )
        transfer = next(
            r
            for r in metrics
            if r["model_family"] == family["model_family"] and r["split_group"] == "all_frozen_transfer_nonfit"
        )
        train_mae = fnum(train["corrected_mae_K"])
        transfer_mae = fnum(transfer["corrected_mae_K"])
        baseline_transfer = fnum(transfer["baseline_mae_K"])
        if finite(transfer_mae) and finite(train_mae):
            gap = transfer_mae - train_mae
        else:
            gap = math.nan
        if finite(transfer_mae) and finite(baseline_transfer) and transfer_mae < baseline_transfer and abs(gap) <= 25.0:
            verdict = "transfers_directionally_with_gap"
        elif finite(transfer_mae) and finite(baseline_transfer) and transfer_mae < baseline_transfer:
            verdict = "improves_transfer_but_gap_large"
        elif finite(transfer_mae):
            verdict = "does_not_improve_transfer"
        else:
            verdict = "transfer_not_scorable"
        rows.append(
            {
                "model_family": family["model_family"],
                "train_support_corrected_mae_K": train["corrected_mae_K"],
                "transfer_corrected_mae_K": transfer["corrected_mae_K"],
                "transfer_baseline_mae_K": transfer["baseline_mae_K"],
                "transfer_minus_train_mae_gap_K": gap,
                "transfer_verdict": verdict,
                "allowed_claim": "frozen diagnostic stress only; not final corrected-split validation/holdout/external admission",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def split_audit_rows(sensor_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    fit_count = sum(1 for r in sensor_rows if r["row_usable"] and r["fit_allowed"])
    transfer_count = sum(1 for r in sensor_rows if r["row_usable"] and not r["fit_allowed"] and r["score_allowed"])
    return [
        {
            "audit_item": "fit_partition",
            "status": "pass",
            "detail": f"coefficients fit only on Salt1/Salt2 train/support rows; usable rows={fit_count}",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "audit_item": "frozen_transfer_partition",
            "status": "pass",
            "detail": f"Salt3/Salt4 rows scored after coefficient freeze; usable rows={transfer_count}; no refit or family selection from these rows",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "audit_item": "external_test",
            "status": "blocked_not_scored",
            "detail": "no compatible sensor-level external-test TSWFC2 prediction artifact exists in this package; val_salt2 remains unscored here",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "audit_item": "runtime_inputs",
            "status": "pass_from_source_package",
            "detail": "TSWFC2 runtime audit states validation records were loaded only after solve_case returned; this task runs no solver",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "audit_item": "admission",
            "status": "not_admitted",
            "detail": "source/property and numerical gates from TSWFC2 package remain blocked; empirical layer is not a physics closure",
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]


def hypothesis_rows(summary: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in summary:
        verdict = str(row["transfer_verdict"])
        family = str(row["model_family"])
        if verdict == "transfers_directionally_with_gap":
            hypothesis = "bias structure may represent a stable reduction/reference discrepancy, but requires source-property and external-test gates before admission"
        elif verdict == "improves_transfer_but_gap_large":
            hypothesis = "fit captures part of the discrepancy but remaining split gap suggests case-dependent heat redistribution or source/sink mismatch"
        elif verdict == "does_not_improve_transfer":
            hypothesis = "train correction likely overfits the train/support residual shape or absorbs physics that changes across cases"
        else:
            hypothesis = "not enough compatible transfer rows"
        rows.append(
            {
                "model_family": family,
                "transfer_verdict": verdict,
                "hypothesis": hypothesis,
                "next_study": "repeat with a runtime-legal Fluid external-BC solve that emits compatible sensor-level rows for train, validation/support, holdout, and external-test partitions",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def source_manifest_rows() -> list[dict[str, object]]:
    rows = [
        {
            "source_path": str(TSWFC2 / "README.md"),
            "use": "candidate provenance and non-admission boundary",
            "mutation": "read_only",
        },
        {
            "source_path": str(TSWFC2 / "runtime_input_audit.csv"),
            "use": "runtime leakage guardrail",
            "mutation": "read_only",
        },
        {
            "source_path": str(TSWFC2 / "case_split_contract.csv"),
            "use": "case/source-property caveats",
            "mutation": "read_only",
        },
        {
            "source_path": str(PREVIOUS / "leg_bias_correction_coefficients.csv"),
            "use": "prior high-DOF context only; not reused or rescored",
            "mutation": "read_only",
        },
    ]
    for case_name in CASE_ROLES:
        rows.append(
            {
                "source_path": str(TSWFC2 / "case_outputs" / case_name.replace(" ", "_") / "validation_table.csv"),
                "use": "sensor-level predicted/reference temperature rows",
                "mutation": "read_only",
            }
        )
    return rows


def write_readme(summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_1/validation_table.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_2/validation_table.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_3/validation_table.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_4/validation_table.csv
tags: [forward-model, empirical-bias, reduced-dof, frozen-transfer]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/README.md
  - .agent/status/2026-07-21_TODO-FLUID-REDUCED-DOF-BIAS-TRANSFER-SCREEN-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-reduced-dof-bias-transfer-screen.md
  - imports/2026-07-21_fluid_reduced_dof_bias_transfer_screen.json
task: TODO-FLUID-REDUCED-DOF-BIAS-TRANSFER-SCREEN-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Reduced-DOF Bias Transfer Screen

This package reduces the empirical correction layer from the previous per-leg
affine diagnostic into predeclared low- and moderate-DOF families, fits
coefficients on Salt1/Salt2 train/support rows only, and applies the frozen
coefficients unchanged to Salt3/Salt4 legacy validation/holdout-style stress
rows.

No Fluid solve is run here. No external-test row is scored. This is not a final
corrected-split admission because the source package remains
`not_admitted_no_grid_expansion`.

## Headline

- Fit rows: `{summary["fit_rows"]}`.
- Frozen transfer rows: `{summary["transfer_rows"]}`.
- Best train/support family by corrected MAE: `{summary["best_train_family"]}`.
- Best frozen-transfer family by corrected MAE, reported score-only:
  `{summary["best_transfer_family"]}`.
- External-test rows scored: `0`.

## Open First

- `model_family_dof_ledger.csv`
- `frozen_coefficients.csv`
- `split_metric_scorecard.csv`
- `transfer_summary.csv`
- `split_runtime_leakage_audit.csv`
- `explanation_hypothesis_ledger.csv`
- `source_property_gate_todo.csv` after running the documented
  `tools/agent/source_property_gate.py --warn --todo-out ...` check.
"""
    (OUT / "README.md").write_text(text)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sensor_rows = load_sensor_rows()
    coeffs = all_coefficients(sensor_rows)
    scored = apply_coefficients(sensor_rows, coeffs)
    metrics = metric_rows(scored)
    dof = dof_rows(coeffs)
    transfer = transfer_summary_rows(metrics)
    split = split_audit_rows(sensor_rows)
    hypotheses = hypothesis_rows(transfer)

    write_csv(
        OUT / "fit_and_transfer_sensor_rows.csv",
        scored,
        [
            "model_family",
            "fit_form",
            "grouping",
            "admissibility",
            "case",
            "case_id",
            "sensor",
            "sensor_kind",
            "prediction_source_segment",
            "leg",
            "thermal_family",
            "fit_role",
            "transfer_role",
            "legacy_split_role",
            "fit_allowed",
            "score_allowed",
            "row_usable",
            "exclusion_reason",
            "predicted_K",
            "reference_K",
            "baseline_residual_K",
            "coefficient_group",
            "multiplier_correction",
            "offset_bias_K",
            "corrected_prediction_K",
            "corrected_residual_K",
            "corrected_abs_error_K",
            "coefficient_missing",
            "source_path",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "frozen_coefficients.csv",
        coeffs,
        [
            "model_family",
            "fit_form",
            "grouping",
            "coefficient_group",
            "multiplier_correction",
            "offset_bias_K",
            "n_fit_rows",
            "fit_status",
            "coefficient_source",
            "degrees_of_freedom",
            "admissibility",
            "interpretation",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "model_family_dof_ledger.csv",
        dof,
        [
            "model_family",
            "fit_form",
            "grouping",
            "predeclared",
            "degrees_of_freedom",
            "coefficient_groups",
            "admissibility",
            "interpretation",
            "reduced_vs_prior_per_leg_affine",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "split_metric_scorecard.csv",
        metrics,
        [
            "model_family",
            "split_group",
            "count",
            "baseline_mae_K",
            "corrected_mae_K",
            "delta_mae_K",
            "baseline_rmse_K",
            "corrected_rmse_K",
            "delta_rmse_K",
            "corrected_bias_K",
            "corrected_max_abs_error_K",
            "selection_role",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "transfer_summary.csv",
        transfer,
        [
            "model_family",
            "train_support_corrected_mae_K",
            "transfer_corrected_mae_K",
            "transfer_baseline_mae_K",
            "transfer_minus_train_mae_gap_K",
            "transfer_verdict",
            "allowed_claim",
            "claim_boundary",
        ],
    )
    write_csv(OUT / "split_runtime_leakage_audit.csv", split, ["audit_item", "status", "detail", "claim_boundary"])
    write_csv(
        OUT / "explanation_hypothesis_ledger.csv",
        hypotheses,
        ["model_family", "transfer_verdict", "hypothesis", "next_study", "claim_boundary"],
    )
    write_csv(OUT / "source_manifest.csv", source_manifest_rows(), ["source_path", "use", "mutation"])

    train_metrics = [r for r in metrics if r["split_group"] == "train_support_fit" and finite(fnum(r["corrected_mae_K"]))]
    transfer_metrics = [
        r for r in metrics if r["split_group"] == "all_frozen_transfer_nonfit" and finite(fnum(r["corrected_mae_K"]))
    ]
    best_train = min(train_metrics, key=lambda r: fnum(r["corrected_mae_K"]))
    best_transfer = min(transfer_metrics, key=lambda r: fnum(r["corrected_mae_K"]))
    summary = {
        "task_id": "TODO-FLUID-REDUCED-DOF-BIAS-TRANSFER-SCREEN-2026-07-21",
        "date": "2026-07-21",
        "status": "complete",
        "source_candidate": "tswfc2_smoke_salt2_four_node_v1",
        "source_candidate_admission": "not_admitted_no_grid_expansion",
        "fit_rows": sum(1 for r in sensor_rows if r["row_usable"] and r["fit_allowed"]),
        "transfer_rows": sum(1 for r in sensor_rows if r["row_usable"] and not r["fit_allowed"] and r["score_allowed"]),
        "external_test_rows_scored": 0,
        "families_scored": [f["model_family"] for f in FAMILIES],
        "best_train_family": best_train["model_family"],
        "best_train_corrected_mae_K": best_train["corrected_mae_K"],
        "best_transfer_family": best_transfer["model_family"],
        "best_transfer_corrected_mae_K": best_transfer["corrected_mae_K"],
        "best_transfer_baseline_mae_K": best_transfer["baseline_mae_K"],
        "coefficient_refit_after_transfer_scoring": False,
        "model_selection_from_transfer": False,
        "fluid_solve_run": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "final_predictive_admission": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)


if __name__ == "__main__":
    main()
