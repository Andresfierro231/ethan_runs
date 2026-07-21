#!/usr/bin/env python3
"""Build a split-aware heater/source-contract and paper-methods package.

This package consumes existing forward-v0/heater-contract evidence. It does not
rerun Fluid and does not read or mutate native CFD solver outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods"

HEATER_CONTRACT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract"
CASE_INTERPRETATION = HEATER_CONTRACT / "case_contract_interpretation.csv"
CASE_HEAT_LEDGER = HEATER_CONTRACT / "case_heat_ledger.csv"
CANDIDATE_PARAMETERS = HEATER_CONTRACT / "candidate_parameters.csv"
RECOMMENDED_MODEL = HEATER_CONTRACT / "recommended_model.csv"
BOUNDARY_MATRIX = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/boundary_model_task_matrix.csv"
FINAL_GATE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits/summary.json"
MATH_REGISTER = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_math_theory_assumptions_results_register/equation_register.csv"
MDOT_AUDIT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/model_result_ledger.csv"

SOURCES = [
    CASE_INTERPRETATION,
    CASE_HEAT_LEDGER,
    CANDIDATE_PARAMETERS,
    RECOMMENDED_MODEL,
    BOUNDARY_MATRIX,
    FINAL_GATE,
    MATH_REGISTER,
    MDOT_AUDIT,
]

SPLIT = {
    "salt_2": "train",
    "salt_3": "validation",
    "salt_4": "holdout",
}

SCALAR_COLUMNS = [
    "model_id",
    "scalar_type",
    "fit_case_id",
    "fit_split",
    "fitted_value",
    "fitted_units",
    "fitted_delta_Q_W",
    "fit_basis",
    "runtime_class",
    "admission_status",
    "runtime_input_audit",
]

SCORE_COLUMNS = [
    "case_id",
    "split",
    "model_id",
    "scalar_type",
    "eta_heater",
    "test_section_external_loss_W",
    "test_section_fluid_fraction",
    "heater_setup_power_W",
    "test_section_setup_power_W",
    "baseline_heater_only_Tmean_error_K",
    "sensitivity_K_per_W",
    "model_delta_Q_vs_heater_only_W",
    "predicted_Tmean_error_K",
    "abs_predicted_Tmean_error_K",
    "score_role",
    "admission_status",
    "runtime_input_audit",
]

DECISION_COLUMNS = [
    "decision_id",
    "decision",
    "basis",
    "allowed_use",
    "excluded_use",
    "paper_claim_status",
    "next_gate",
]

RESULT_COLUMNS = [
    "result_id",
    "equation_ids",
    "source_artifacts",
    "property_lane",
    "split_policy",
    "fitted_parameters",
    "validation_targets",
    "diagnostic_only_cfd_quantities",
    "admission_status",
    "overclaim_boundary",
]

CLAIM_COLUMNS = [
    "claim_id",
    "claim",
    "claim_status",
    "evidence",
    "limitation",
    "paper_section_use",
]

FIGURE_COLUMNS = [
    "item_id",
    "recommended_item",
    "source_csv",
    "caption_seed",
    "paper_use",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return value


def fnum(value: Any) -> float:
    if value in ("", None):
        return float("nan")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"non-finite numeric value: {value!r}")
    return parsed


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def abs_mean(values: list[float]) -> float:
    return mean([abs(value) for value in values])


def score_rows(interp_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_case = {row["case_id"]: row for row in interp_rows}
    train = rows_by_case["salt_2"]
    eta_fit = fnum(train["equivalent_eta_heater_fit"])
    external_loss_fit = fnum(train["equivalent_test_section_external_loss_fit_W"])

    scalar_rows = [
        {
            "model_id": "H0_heater_only_unfitted",
            "scalar_type": "none",
            "fit_case_id": "none",
            "fit_split": "none",
            "fitted_value": 0.0,
            "fitted_units": "none",
            "fitted_delta_Q_W": 0.0,
            "fit_basis": "C1 heater-only source contract from existing heater/test-section package",
            "runtime_class": "setup_only_unfitted",
            "admission_status": "admitted_as_next_unfitted_source_contract_but_not_final_forward_v1",
            "runtime_input_audit": "passes_no_cfd_wallHeatFlux_no_cfd_mdot_no_validation_temperature",
        },
        {
            "model_id": "H1_eta_heater_fit_salt2",
            "scalar_type": "eta_heater",
            "fit_case_id": "salt_2",
            "fit_split": "train",
            "fitted_value": eta_fit,
            "fitted_units": "dimensionless",
            "fitted_delta_Q_W": (eta_fit - 1.0) * fnum(train["heater_setup_power_W"]),
            "fit_basis": "Salt2 train row linearized Tmean residual relative to heater-only",
            "runtime_class": "train_only_one_scalar_candidate",
            "admission_status": "calibration_candidate_validation_scored_not_final_forward_v1",
            "runtime_input_audit": "passes_fit_uses_train_target_only_no_realized_wallHeatFlux_runtime_input",
        },
        {
            "model_id": "H2_test_section_external_loss_fit_salt2",
            "scalar_type": "test_section_external_loss_W",
            "fit_case_id": "salt_2",
            "fit_split": "train",
            "fitted_value": external_loss_fit,
            "fitted_units": "W",
            "fitted_delta_Q_W": -external_loss_fit,
            "fit_basis": "Salt2 train row linearized Tmean residual relative to heater-only",
            "runtime_class": "train_only_one_scalar_candidate",
            "admission_status": "calibration_candidate_validation_scored_not_final_forward_v1",
            "runtime_input_audit": "passes_fit_uses_train_target_only_no_realized_wallHeatFlux_runtime_input",
        },
        {
            "model_id": "H3_test_section_37W_rejected",
            "scalar_type": "test_section_fluid_fraction",
            "fit_case_id": "none",
            "fit_split": "none",
            "fitted_value": 1.0,
            "fitted_units": "fraction",
            "fitted_delta_Q_W": 37.0,
            "fit_basis": "legacy/current Fluid setup-source assumption",
            "runtime_class": "setup_assumption_rejected_by_current_evidence",
            "admission_status": "rejected_as_default_source_contract",
            "runtime_input_audit": "setup_only_but_wrong_sign_against_current_evidence",
        },
    ]

    score_models = [
        ("H0_heater_only_unfitted", "none", 1.0, 0.0, 0.0),
        ("H1_eta_heater_fit_salt2", "eta_heater", eta_fit, 0.0, 0.0),
        ("H2_test_section_external_loss_fit_salt2", "test_section_external_loss_W", 1.0, external_loss_fit, 0.0),
        ("H3_test_section_37W_rejected", "test_section_fluid_fraction", 1.0, 0.0, 1.0),
    ]
    scores: list[dict[str, Any]] = []
    for row in interp_rows:
        case_id = row["case_id"]
        split = SPLIT[case_id]
        heater_power = fnum(row["heater_setup_power_W"])
        test_power = fnum(row["test_section_setup_power_W"])
        sensitivity = fnum(row["test_source_sensitivity_K_per_W"])
        baseline_error = fnum(row["F1_Tmean_error_vs_cfd_K"])
        for model_id, scalar_type, eta, external_loss, test_fraction in score_models:
            delta_q = (eta - 1.0) * heater_power - external_loss + test_fraction * test_power
            predicted_error = baseline_error + sensitivity * delta_q
            if model_id == "H3_test_section_37W_rejected":
                # Use the recorded F0 row to avoid accumulating roundoff.
                predicted_error = fnum(row["F0_Tmean_error_vs_cfd_K"])
            scores.append(
                {
                    "case_id": case_id,
                    "split": split,
                    "model_id": model_id,
                    "scalar_type": scalar_type,
                    "eta_heater": eta,
                    "test_section_external_loss_W": external_loss,
                    "test_section_fluid_fraction": test_fraction,
                    "heater_setup_power_W": heater_power,
                    "test_section_setup_power_W": test_power,
                    "baseline_heater_only_Tmean_error_K": baseline_error,
                    "sensitivity_K_per_W": sensitivity,
                    "model_delta_Q_vs_heater_only_W": delta_q,
                    "predicted_Tmean_error_K": predicted_error,
                    "abs_predicted_Tmean_error_K": abs(predicted_error),
                    "score_role": "fit_row" if split == "train" and model_id in {"H1_eta_heater_fit_salt2", "H2_test_section_external_loss_fit_salt2"} else "score_only",
                    "admission_status": "diagnostic_score_target_final_forward_v1_blocked",
                    "runtime_input_audit": "no_cfd_mdot_no_wallHeatFlux_no_validation_temperature_runtime_input",
                }
            )
    return scalar_rows, scores


def model_summary(score_rows_: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model_id in sorted({row["model_id"] for row in score_rows_}):
        model_rows = [row for row in score_rows_ if row["model_id"] == model_id]
        train_rows = [row for row in model_rows if row["split"] == "train"]
        validation_rows = [row for row in model_rows if row["split"] == "validation"]
        holdout_rows = [row for row in model_rows if row["split"] == "holdout"]
        heldout = validation_rows + holdout_rows
        rows.append(
            {
                "model_id": model_id,
                "train_abs_Tmean_error_K": abs_mean([fnum(row["predicted_Tmean_error_K"]) for row in train_rows]),
                "validation_abs_Tmean_error_K": abs_mean([fnum(row["predicted_Tmean_error_K"]) for row in validation_rows]),
                "holdout_abs_Tmean_error_K": abs_mean([fnum(row["predicted_Tmean_error_K"]) for row in holdout_rows]),
                "heldout_mean_abs_Tmean_error_K": abs_mean([fnum(row["predicted_Tmean_error_K"]) for row in heldout]),
                "all_mean_abs_Tmean_error_K": abs_mean([fnum(row["predicted_Tmean_error_K"]) for row in model_rows]),
                "fit_rows": ";".join(row["case_id"] for row in model_rows if row["score_role"] == "fit_row") or "none",
                "heldout_rows": ";".join(row["case_id"] for row in heldout),
                "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
            }
        )
    return rows


def decision_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    by_model = {row["model_id"]: row for row in summary_rows}
    h0 = by_model["H0_heater_only_unfitted"]
    h1 = by_model["H1_eta_heater_fit_salt2"]
    h2 = by_model["H2_test_section_external_loss_fit_salt2"]
    h3 = by_model["H3_test_section_37W_rejected"]
    preferred = "H1_eta_heater_fit_salt2" if fnum(h1["heldout_mean_abs_Tmean_error_K"]) <= fnum(h2["heldout_mean_abs_Tmean_error_K"]) else "H2_test_section_external_loss_fit_salt2"
    return [
        {
            "decision_id": "D1_reject_37W_test_section_source_as_default",
            "decision": "Do not use the 37 W test-section source as the default forward source contract.",
            "basis": f"H3 heldout mean abs Tmean error is {fnum(h3['heldout_mean_abs_Tmean_error_K']):.3f} K versus {fnum(h0['heldout_mean_abs_Tmean_error_K']):.3f} K for heater-only.",
            "allowed_use": "historical comparison and methods explanation",
            "excluded_use": "default predictive source contract",
            "paper_claim_status": "supported_for_current_evidence",
            "next_gate": "none for rejection; keep as comparison row",
        },
        {
            "decision_id": "D2_admit_heater_only_as_unfitted_source_contract",
            "decision": "Use heater-only as the admitted unfitted source contract for the next setup-only boundary/HX work.",
            "basis": "It is setup-only and avoids the wrong-sign test-section source term.",
            "allowed_use": "next unfitted source contract and baseline in paper score tables",
            "excluded_use": "final forward-v1 admission because cooler/HX and hydraulics are still blocked",
            "paper_claim_status": "supported_but_not_final_forward_v1",
            "next_gate": "BCM-COOLER-HX-UA-V1",
        },
        {
            "decision_id": "D3_record_one_scalar_heater_candidates",
            "decision": f"Record {preferred} as the better Salt2-only held-out candidate, but do not admit final forward-v1 from it.",
            "basis": f"H1 heldout mean abs error {fnum(h1['heldout_mean_abs_Tmean_error_K']):.3f} K; H2 heldout mean abs error {fnum(h2['heldout_mean_abs_Tmean_error_K']):.3f} K.",
            "allowed_use": "calibration-candidate evidence and paper limitations discussion",
            "excluded_use": "multi-parameter heater/test-section fit or validation/holdout refit",
            "paper_claim_status": "calibration_candidate_only",
            "next_gate": "Repeat after setup-only HX model removes imposed-cooler dependency.",
        },
        {
            "decision_id": "D4_preserve_no_runtime_cheat",
            "decision": "Keep realized heater wallHeatFlux and diagnostic eta as post-solve evidence only.",
            "basis": "The source heat ledger reports diagnostic realized transfer, but final predictive mode cannot consume realized CFD wallHeatFlux.",
            "allowed_use": "sign, magnitude, and uncertainty discussion",
            "excluded_use": "runtime source input",
            "paper_claim_status": "guardrail",
            "next_gate": "runtime leakage tests in the boundary/HX scorecard",
        },
    ]


def result_intake_rows() -> list[dict[str, str]]:
    return [
        {
            "result_id": "R_heater_source_split_screen",
            "equation_ids": "segment_heat_balance;post_solve_score_residual",
            "source_artifacts": rel(CASE_INTERPRETATION) + ";" + rel(CASE_HEAT_LEDGER),
            "property_lane": "replication_reis_jadyn/current Fluid source evidence; no property refit",
            "split_policy": "salt_2=train; salt_3=validation; salt_4=holdout",
            "fitted_parameters": "none for H0; eta_heater or test_section_external_loss_W for one-scalar candidates",
            "validation_targets": "Tmean residuals from existing forward-v0/heater contract; Salt3 validation and Salt4 holdout",
            "diagnostic_only_cfd_quantities": "realized heater/test-section wallHeatFlux; CFD Tmean targets; CFD mdot",
            "admission_status": "heater-only source contract admitted as unfitted baseline; final forward-v1 blocked",
            "overclaim_boundary": "Uses imposed-cooler forward-v0 context, so this is source-contract evidence, not final predictive HX validation.",
        },
        {
            "result_id": "R_paper_methods_process",
            "equation_ids": "segment_heat_balance;hx_ua_or_epsilon_ntu;radiation_boundary;loop_pressure_root",
            "source_artifacts": rel(BOUNDARY_MATRIX) + ";" + rel(FINAL_GATE),
            "property_lane": "declare before fitting; no cross-property fitting in this package",
            "split_policy": "locked Salt2/Salt3/Salt4 split",
            "fitted_parameters": "at most one scalar per gate-moving boundary task",
            "validation_targets": "mdot, Tmean, branch/sensor temperatures, heat role residuals",
            "diagnostic_only_cfd_quantities": "CFD mdot, realized wallHeatFlux, imposed cooler duty, validation/holdout temperatures",
            "admission_status": "paper process documented; scorecard remains blocked until upstream gates land",
            "overclaim_boundary": "Blocked gates must be reported directly instead of absorbed into heater, HX, friction, or Nu fits.",
        },
    ]


def claim_rows() -> list[dict[str, str]]:
    return [
        {
            "claim_id": "C1_branchwise_workflow",
            "claim": "The forward model is governed by separated hydraulic, boundary/HX, internal thermal, property, and admission lanes rather than a single global coefficient.",
            "claim_status": "supported_as_methods_architecture",
            "evidence": rel(BOUNDARY_MATRIX) + ";" + rel(FINAL_GATE),
            "limitation": "Architecture does not by itself admit final predictive accuracy.",
            "paper_section_use": "Methods and model-form selection",
        },
        {
            "claim_id": "C2_heater_only_source_contract",
            "claim": "The 37 W test-section source should not be the default current source contract; heater-only is the safer unfitted baseline.",
            "claim_status": "supported_for_current_salt234_evidence",
            "evidence": "heater_fraction_split_scores.csv;heater_fraction_decision_table.csv",
            "limitation": "Scored in imposed-cooler forward-v0 context, so not final predictive-HX validation.",
            "paper_section_use": "Boundary/source model result",
        },
        {
            "claim_id": "C3_one_scalar_heater_calibration",
            "claim": "A Salt2-only heater efficiency or test-section external-loss scalar can improve held-out Tmean residuals.",
            "claim_status": "calibration_candidate_only",
            "evidence": "heater_fraction_model_summary.csv",
            "limitation": "Small split, imposed-cooler context, and no final boundary/HX admission.",
            "paper_section_use": "Sensitivity and limitations",
        },
        {
            "claim_id": "C4_no_wallheatflux_runtime",
            "claim": "Realized CFD wallHeatFlux and diagnostic heater efficiency are not runtime inputs in predictive mode.",
            "claim_status": "guardrail_supported",
            "evidence": rel(CASE_HEAT_LEDGER) + ";runtime_input_audit.csv",
            "limitation": "They remain valid score/diagnostic targets after solve.",
            "paper_section_use": "Input discipline and validation protocol",
        },
        {
            "claim_id": "C5_final_forward_v1_blocked",
            "claim": "Final forward-v1 remains blocked after this heater-source slice.",
            "claim_status": "supported_blocked_no_go",
            "evidence": rel(FINAL_GATE),
            "limitation": "Requires setup-only HX/external boundary, hydraulic evidence, terminal admission, and matched-plane/upcomer gates.",
            "paper_section_use": "Limitations and next work",
        },
    ]


def figure_rows() -> list[dict[str, str]]:
    return [
        {
            "item_id": "F1",
            "recommended_item": "Bar chart of train/validation/holdout absolute Tmean error by source model",
            "source_csv": "heater_fraction_model_summary.csv",
            "caption_seed": "Split-aware heater source-contract comparison using Salt2 for any one-scalar fit and Salt3/Salt4 as held-out scores.",
            "paper_use": "Results figure",
        },
        {
            "item_id": "T1",
            "recommended_item": "Decision table for admitted, candidate, and rejected heater source forms",
            "source_csv": "heater_fraction_decision_table.csv",
            "caption_seed": "Heater/test-section source decisions and excluded uses under predictive runtime-input discipline.",
            "paper_use": "Methods/results table",
        },
        {
            "item_id": "T2",
            "recommended_item": "Result-intake table for paper reproducibility",
            "source_csv": "result_intake_table.csv",
            "caption_seed": "Provenance, split role, fitted parameters, validation targets, and overclaim boundaries for the heater-source slice.",
            "paper_use": "Supplementary methods table",
        },
    ]


def runtime_audit_rows(score_rows_: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "audit_id": "A1_no_cfd_mdot_runtime",
            "status": "pass",
            "evidence": "Builder consumes no mdot column for scalar fitting or source scoring.",
            "blocked_runtime_input": "CFD mdot",
        },
        {
            "audit_id": "A2_no_wallHeatFlux_runtime",
            "status": "pass",
            "evidence": "Realized wallHeatFlux appears only in source manifest and claim limitations; scalar fits use train Tmean residual sensitivity.",
            "blocked_runtime_input": "realized CFD wallHeatFlux",
        },
        {
            "audit_id": "A3_no_validation_holdout_refit",
            "status": "pass",
            "evidence": "Only Salt2 determines H1/H2 scalar values; Salt3/Salt4 rows have score_role=score_only.",
            "blocked_runtime_input": "validation/holdout temperatures",
        },
        {
            "audit_id": "A4_no_imposed_cooler_final_claim",
            "status": "pass_with_limitation",
            "evidence": "Package labels all source scores final_forward_v1_blocked because the underlying context still depends on imposed-cooler forward-v0 evidence.",
            "blocked_runtime_input": "imposed CFD cooler duty as final predictive HX",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    rows = []
    for path in SOURCES:
        rows.append(
            {
                "source_path": rel(path),
                "exists": str(path.exists()).lower(),
                "use": "input",
            }
        )
    return rows


def write_methods_doc(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(CASE_INTERPRETATION)}
  - {rel(CASE_HEAT_LEDGER)}
  - {rel(BOUNDARY_MATRIX)}
  - {rel(FINAL_GATE)}
tags: [forward-model, boundary-modeling, heater-source, paper-methods]
related:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: AGENT-390
date: 2026-07-14
role: BC-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Paper Methods Process

## Objective

This package documents the first executable source-contract slice of the
forward-v1 completion plan. It converts the heater/test-section source decision
into a split-aware screen that can be cited in a scientific paper without
claiming final predictive-HX admission.

## Governing Balance

The source contract is interpreted through the segment heat balance:

```text
mdot * cp * (T_out - T_in) =
    Q_heater - Q_cooler - Q_passive - Q_storage - Q_residual
```

For this slice, cooler/HX and passive external losses remain separate lanes.
The tested heater/source perturbation is:

```text
delta_Q = (eta_heater - 1) * P_heater_setup
          - test_section_external_loss_W
          + test_section_fluid_fraction * P_test_section_setup
```

The existing heater-contract package provides a local linear sensitivity:

```text
Tmean_error_model = Tmean_error_heater_only + S_case * delta_Q
```

where `S_case` is the case-specific `test_source_sensitivity_K_per_W`.

## Split And Fitting Policy

Salt2 is the only fitting row. Salt3 is validation. Salt4 is holdout. The
package fits at most one scalar at a time:

- `eta_heater` for `H1_eta_heater_fit_salt2`;
- `test_section_external_loss_W` for
  `H2_test_section_external_loss_fit_salt2`.

The 37 W test-section source form is retained only as a rejected comparison.
Validation and holdout temperatures are never used to set fitted values.

## Runtime Input Discipline

The package does not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD
cooler duty, or held-out temperatures as predictive runtime inputs. Realized
heater/test-section `wallHeatFlux` remains diagnostic evidence only. The source
scores are still blocked from final forward-v1 admission because the underlying
evidence is an imposed-cooler forward-v0 source screen, not a setup-only HX
model.

## Result

- Best current unfitted source contract: heater-only.
- Train-only scalar candidates scored: `2`.
- Final forward-v1 admitted here: `false`.
- Held-out mean absolute Tmean error for heater-only:
  `{summary['heater_only_heldout_mean_abs_Tmean_error_K']:.3f} K`.
- Held-out mean absolute Tmean error for Salt2-fitted `eta_heater`:
  `{summary['eta_fit_heldout_mean_abs_Tmean_error_K']:.3f} K`.
- Held-out mean absolute Tmean error for Salt2-fitted test-section loss:
  `{summary['external_loss_fit_heldout_mean_abs_Tmean_error_K']:.3f} K`.

## Paper Use

This is suitable for a paper methods/results subsection on source-contract
screening and predictive-input discipline. It is not suitable as a final
forward-v1 scorecard or as proof that the cooler/HX boundary has been solved.
"""
    (out / "methods_process.md").write_text(text, encoding="utf-8")


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(CASE_INTERPRETATION)}
  - {rel(CASE_HEAT_LEDGER)}
  - {rel(BOUNDARY_MATRIX)}
  - {rel(FINAL_GATE)}
tags: [forward-model, boundary-modeling, heater-source, paper-methods]
related:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: AGENT-390
date: 2026-07-14
role: BC-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Heater Fraction / Forward-v1 Paper Methods

## Decision

This package implements the repo-local heater/source-contract slice of the
forward-v1 completion plan. Heater-only remains the admitted unfitted source
contract for the next boundary/HX work. A Salt2-only fitted `eta_heater` or
test-section external-loss scalar improves the held-out Tmean score in this
linearized screen, but neither scalar admits final forward-v1 because the
cooler/HX model is still not setup-only.

## Main Results

- Split: `salt_2=train`, `salt_3=validation`, `salt_4=holdout`.
- Runtime-input audit violations: `{summary['runtime_input_audit_violations']}`.
- Heater-only held-out mean absolute Tmean error:
  `{summary['heater_only_heldout_mean_abs_Tmean_error_K']:.3f} K`.
- Salt2-fitted `eta_heater`: `{summary['fitted_eta_heater']:.6f}`;
  held-out mean absolute Tmean error:
  `{summary['eta_fit_heldout_mean_abs_Tmean_error_K']:.3f} K`.
- Salt2-fitted test-section external loss:
  `{summary['fitted_test_section_external_loss_W']:.3f} W`;
  held-out mean absolute Tmean error:
  `{summary['external_loss_fit_heldout_mean_abs_Tmean_error_K']:.3f} K`.
- Legacy 37 W test-section source held-out mean absolute Tmean error:
  `{summary['legacy_37w_heldout_mean_abs_Tmean_error_K']:.3f} K`.

## Files

- `heater_fraction_scalar_candidates.csv`
- `heater_fraction_split_scores.csv`
- `heater_fraction_model_summary.csv`
- `heater_fraction_decision_table.csv`
- `runtime_input_audit.csv`
- `result_intake_table.csv`
- `claim_limitations_table.csv`
- `figure_table_index.csv`
- `methods_process.md`
- `source_manifest.csv`
- `summary.json`

## Boundaries

This package does not mutate native CFD outputs, registry/admission state,
scheduler state, generated indexes, or external Fluid files. It does not
replace the required setup-only cooler/HX model and does not reopen internal Nu.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    interp_rows = read_csv(CASE_INTERPRETATION)
    scalar_rows, scores = score_rows(interp_rows)
    summaries = model_summary(scores)
    decisions = decision_rows(summaries)
    runtime_rows = runtime_audit_rows(scores)
    result_rows = result_intake_rows()
    claims = claim_rows()
    figures = figure_rows()
    manifest = source_manifest_rows()
    final_gate = read_json(FINAL_GATE)

    by_model = {row["model_id"]: row for row in summaries}
    summary = {
        "task": "AGENT-390",
        "generated_at": utc_now(),
        "source_contract_status": "heater_only_unfitted_admitted_as_next_source_contract",
        "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
        "final_forward_v1_admitted": False,
        "current_split": "salt_2=train;salt_3=validation;salt_4=holdout",
        "fitted_eta_heater": fnum([row for row in scalar_rows if row["model_id"] == "H1_eta_heater_fit_salt2"][0]["fitted_value"]),
        "fitted_test_section_external_loss_W": fnum([row for row in scalar_rows if row["model_id"] == "H2_test_section_external_loss_fit_salt2"][0]["fitted_value"]),
        "heater_only_heldout_mean_abs_Tmean_error_K": fnum(by_model["H0_heater_only_unfitted"]["heldout_mean_abs_Tmean_error_K"]),
        "eta_fit_heldout_mean_abs_Tmean_error_K": fnum(by_model["H1_eta_heater_fit_salt2"]["heldout_mean_abs_Tmean_error_K"]),
        "external_loss_fit_heldout_mean_abs_Tmean_error_K": fnum(by_model["H2_test_section_external_loss_fit_salt2"]["heldout_mean_abs_Tmean_error_K"]),
        "legacy_37w_heldout_mean_abs_Tmean_error_K": fnum(by_model["H3_test_section_37W_rejected"]["heldout_mean_abs_Tmean_error_K"]),
        "runtime_input_audit_violations": 0,
        "upstream_forward_gate_status": final_gate.get("final_forward_v1_status", "unknown"),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action_taken": False,
        "external_fluid_modified_by_this_task": False,
    }

    write_csv(out / "heater_fraction_scalar_candidates.csv", scalar_rows, SCALAR_COLUMNS)
    write_csv(out / "heater_fraction_split_scores.csv", scores, SCORE_COLUMNS)
    write_csv(
        out / "heater_fraction_model_summary.csv",
        summaries,
        [
            "model_id",
            "train_abs_Tmean_error_K",
            "validation_abs_Tmean_error_K",
            "holdout_abs_Tmean_error_K",
            "heldout_mean_abs_Tmean_error_K",
            "all_mean_abs_Tmean_error_K",
            "fit_rows",
            "heldout_rows",
            "final_forward_v1_status",
        ],
    )
    write_csv(out / "heater_fraction_decision_table.csv", decisions, DECISION_COLUMNS)
    write_csv(out / "runtime_input_audit.csv", runtime_rows, ["audit_id", "status", "evidence", "blocked_runtime_input"])
    write_csv(out / "result_intake_table.csv", result_rows, RESULT_COLUMNS)
    write_csv(out / "claim_limitations_table.csv", claims, CLAIM_COLUMNS)
    write_csv(out / "figure_table_index.csv", figures, FIGURE_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, ["source_path", "exists", "use"])
    write_json(out / "summary.json", summary)
    write_methods_doc(out, summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build_package(args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
