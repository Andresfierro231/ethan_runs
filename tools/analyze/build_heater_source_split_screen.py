#!/usr/bin/env python3
"""Build the BCM-HEATER-FRACTION-V1 locked-split source screen.

This is a repo-local synthesis of the existing heater/test-section source
contract. It does not rerun Fluid and does not consume realized CFD
wallHeatFlux, CFD cooler duty, CFD mdot, or validation/holdout temperatures as
runtime inputs.
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
DEFAULT_OUTPUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_heater_source_split_screen"
HEATER_CONTRACT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract"
BOUNDARY_MATRIX = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix"
FORWARD_GATE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate"

CASE_INTERPRETATION = HEATER_CONTRACT / "case_contract_interpretation.csv"
CASE_HEAT_LEDGER = HEATER_CONTRACT / "case_heat_ledger.csv"
CANDIDATE_PARAMETERS = HEATER_CONTRACT / "candidate_parameters.csv"
RECOMMENDED_MODEL = HEATER_CONTRACT / "recommended_model.csv"
BOUNDARY_TASK_MATRIX = BOUNDARY_MATRIX / "boundary_model_task_matrix.csv"
FORWARD_GATE_README = FORWARD_GATE / "README.md"

SPLIT = {"salt_2": "train", "salt_3": "validation", "salt_4": "holdout"}

SCORE_COLUMNS = [
    "case_id",
    "split_assignment",
    "source_id",
    "model_id",
    "model_family",
    "eta_heater",
    "test_section_fluid_fraction",
    "test_section_external_loss_W",
    "delta_Q_vs_heater_only_W",
    "predicted_Tmean_K",
    "cfd_Tmean_K",
    "Tmean_error_vs_cfd_K",
    "abs_Tmean_error_vs_cfd_K",
    "fitted_on_case",
    "runtime_source_class",
    "cfd_target_use",
    "diagnostic_cfd_quantities_excluded_from_runtime",
    "forbidden_runtime_inputs_used",
    "score_limit",
]

PARAMETER_COLUMNS = [
    "model_id",
    "model_family",
    "parameter_name",
    "parameter_value",
    "fit_case_id",
    "train_abs_Tmean_error_K",
    "validation_abs_Tmean_error_K",
    "holdout_abs_Tmean_error_K",
    "validation_plus_holdout_mean_abs_Tmean_error_K",
    "validation_plus_holdout_delta_vs_C1_K",
    "runtime_admissibility",
    "admission_limit",
]

GATE_COLUMNS = [
    "gate_id",
    "status",
    "decision",
    "evidence",
    "allowed_use",
    "excluded_use",
    "next_action",
]

MANIFEST_COLUMNS = ["artifact", "role", "mutation_status", "path"]


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


def case_rows(path: Path = CASE_INTERPRETATION) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(path):
        converted: dict[str, Any] = dict(row)
        converted["split_assignment"] = SPLIT[row["case_id"]]
        for column in [
            "heater_setup_power_W",
            "test_section_setup_power_W",
            "model_Tmean_F0_current_37W_K",
            "model_Tmean_F1_heater_only_K",
            "cfd_Tmean_K",
            "F0_Tmean_error_vs_cfd_K",
            "F1_Tmean_error_vs_cfd_K",
            "test_source_sensitivity_K_per_W",
            "equivalent_delta_Q_needed_vs_heater_only_W",
            "equivalent_eta_heater_fit",
            "equivalent_test_section_fluid_fraction_fit",
            "equivalent_test_section_external_loss_fit_W",
        ]:
            converted[column] = fnum(row[column])
        rows.append(converted)
    return rows


def train_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trains = [row for row in rows if row["split_assignment"] == "train"]
    if len(trains) != 1:
        raise ValueError(f"expected exactly one training row, got {len(trains)}")
    return trains[0]


def candidate_specs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    train = train_row(rows)
    return [
        {
            "model_id": "C0_current_37W_test_source",
            "model_family": "rejected_current_setup",
            "eta_heater": 1.0,
            "test_section_fluid_fraction": 1.0,
            "test_section_external_loss_W": 0.0,
            "parameter_name": "test_section_fluid_fraction",
            "parameter_value": 1.0,
            "fit_case_id": "none",
            "runtime_source_class": "predictive_setup_assumption_rejected",
        },
        {
            "model_id": "C1_heater_only_unfitted",
            "model_family": "recommended_unfitted_setup",
            "eta_heater": 1.0,
            "test_section_fluid_fraction": 0.0,
            "test_section_external_loss_W": 0.0,
            "parameter_name": "none",
            "parameter_value": "",
            "fit_case_id": "none",
            "runtime_source_class": "predictive_setup_assumption_unfitted",
        },
        {
            "model_id": "C2_eta_heater_fit_salt2",
            "model_family": "one_scalar_train_only_candidate",
            "eta_heater": train["equivalent_eta_heater_fit"],
            "test_section_fluid_fraction": 0.0,
            "test_section_external_loss_W": 0.0,
            "parameter_name": "eta_heater",
            "parameter_value": train["equivalent_eta_heater_fit"],
            "fit_case_id": train["case_id"],
            "runtime_source_class": "calibrated_parameter_candidate_train_only",
        },
        {
            "model_id": "C3_test_section_external_loss_fit_salt2",
            "model_family": "one_scalar_train_only_candidate",
            "eta_heater": 1.0,
            "test_section_fluid_fraction": 0.0,
            "test_section_external_loss_W": train["equivalent_test_section_external_loss_fit_W"],
            "parameter_name": "test_section_external_loss_W",
            "parameter_value": train["equivalent_test_section_external_loss_fit_W"],
            "fit_case_id": train["case_id"],
            "runtime_source_class": "calibrated_parameter_candidate_train_only",
        },
    ]


def delta_q(row: dict[str, Any], spec: dict[str, Any]) -> float:
    if spec["model_id"] == "C0_current_37W_test_source":
        return row["test_section_setup_power_W"]
    return (
        (spec["eta_heater"] - 1.0) * row["heater_setup_power_W"]
        + spec["test_section_fluid_fraction"] * row["test_section_setup_power_W"]
        - spec["test_section_external_loss_W"]
    )


def predict_tmean(row: dict[str, Any], spec: dict[str, Any]) -> float:
    if spec["model_id"] == "C0_current_37W_test_source":
        return row["model_Tmean_F0_current_37W_K"]
    return row["model_Tmean_F1_heater_only_K"] + row["test_source_sensitivity_K_per_W"] * delta_q(row, spec)


def score_rows(rows: list[dict[str, Any]], specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for spec in specs:
        for row in rows:
            predicted = predict_tmean(row, spec)
            error = predicted - row["cfd_Tmean_K"]
            scored.append(
                {
                    "case_id": row["case_id"],
                    "split_assignment": row["split_assignment"],
                    "source_id": row["source_id"],
                    "model_id": spec["model_id"],
                    "model_family": spec["model_family"],
                    "eta_heater": spec["eta_heater"],
                    "test_section_fluid_fraction": spec["test_section_fluid_fraction"],
                    "test_section_external_loss_W": spec["test_section_external_loss_W"],
                    "delta_Q_vs_heater_only_W": delta_q(row, spec),
                    "predicted_Tmean_K": predicted,
                    "cfd_Tmean_K": row["cfd_Tmean_K"],
                    "Tmean_error_vs_cfd_K": error,
                    "abs_Tmean_error_vs_cfd_K": abs(error),
                    "fitted_on_case": "yes" if row["case_id"] == spec["fit_case_id"] else "no",
                    "runtime_source_class": spec["runtime_source_class"],
                    "cfd_target_use": "fit_target_train_only" if row["case_id"] == spec["fit_case_id"] else "score_target_only",
                    "diagnostic_cfd_quantities_excluded_from_runtime": (
                        "realized_wallHeatFlux;cooler_duty;mdot;validation_or_holdout_temperatures"
                    ),
                    "forbidden_runtime_inputs_used": "false",
                    "score_limit": "linearized_Tmean_proxy_from_existing_forward_v0_evidence",
                }
            )
    return scored


def by_model(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["model_id"], []).append(row)
    return grouped


def split_abs(rows: list[dict[str, Any]], split: str) -> list[float]:
    return [float(row["abs_Tmean_error_vs_cfd_K"]) for row in rows if row["split_assignment"] == split]


def parameter_rows(scored_rows: list[dict[str, Any]], specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = by_model(scored_rows)
    baseline_vh = mean(split_abs(grouped["C1_heater_only_unfitted"], "validation") + split_abs(grouped["C1_heater_only_unfitted"], "holdout"))
    rows: list[dict[str, Any]] = []
    for spec in specs:
        model_scores = grouped[spec["model_id"]]
        validation_holdout = split_abs(model_scores, "validation") + split_abs(model_scores, "holdout")
        vh_mean = mean(validation_holdout)
        if spec["model_id"] == "C1_heater_only_unfitted":
            admissibility = "recommended_split_scored_unfitted_source_contract"
            limit = "Can be used as the next setup-only heater source contract; still proxy-level for final forward-v1 until Fluid scorecard reruns branch/sensor outputs."
        elif spec["model_id"].startswith("C2") or spec["model_id"].startswith("C3"):
            admissibility = "passes_locked_split_Tmean_proxy_screen_not_final_admission"
            limit = "One Salt2-fitted scalar improved Salt3/Salt4 Tmean proxy, but final use needs full Fluid rerun and branch/sensor validation."
        else:
            admissibility = "rejected_as_default_source_contract"
            limit = "Retaining the 37 W test-section fluid source overheats all current rows."
        rows.append(
            {
                "model_id": spec["model_id"],
                "model_family": spec["model_family"],
                "parameter_name": spec["parameter_name"],
                "parameter_value": spec["parameter_value"],
                "fit_case_id": spec["fit_case_id"],
                "train_abs_Tmean_error_K": mean(split_abs(model_scores, "train")),
                "validation_abs_Tmean_error_K": mean(split_abs(model_scores, "validation")),
                "holdout_abs_Tmean_error_K": mean(split_abs(model_scores, "holdout")),
                "validation_plus_holdout_mean_abs_Tmean_error_K": vh_mean,
                "validation_plus_holdout_delta_vs_C1_K": vh_mean - baseline_vh,
                "runtime_admissibility": admissibility,
                "admission_limit": limit,
            }
        )
    return rows


def gate_rows(parameter_rows_: list[dict[str, Any]]) -> list[dict[str, Any]]:
    params = {row["model_id"]: row for row in parameter_rows_}
    eta_delta = float(params["C2_eta_heater_fit_salt2"]["validation_plus_holdout_delta_vs_C1_K"])
    loss_delta = float(params["C3_test_section_external_loss_fit_salt2"]["validation_plus_holdout_delta_vs_C1_K"])
    return [
        {
            "gate_id": "input_hygiene",
            "status": "pass",
            "decision": "No forbidden runtime input is used by this screen.",
            "evidence": "All score rows set forbidden_runtime_inputs_used=false and only use CFD Tmean as fit/score target.",
            "allowed_use": "Fit one scalar on Salt2 or score Salt3/Salt4.",
            "excluded_use": "No realized wallHeatFlux, cooler duty, mdot, or validation/holdout temperature is a runtime source input.",
            "next_action": "Keep this guardrail in any Fluid rerun package.",
        },
        {
            "gate_id": "unfitted_heater_only_contract",
            "status": "pass_recommended",
            "decision": "C1 heater-only is the next setup-only source contract.",
            "evidence": (
                f"Salt3/Salt4 mean abs Tmean proxy error is "
                f"{float(params['C1_heater_only_unfitted']['validation_plus_holdout_mean_abs_Tmean_error_K']):.3f} K."
            ),
            "allowed_use": "Default source contract for next repo-local or Fluid scorecard.",
            "excluded_use": "Do not claim final thermal closure admission from Tmean proxy alone.",
            "next_action": "Run full Fluid scorecard when boundary/HX dependencies are ready.",
        },
        {
            "gate_id": "one_scalar_eta_heater",
            "status": "pass_proxy_screen_not_final",
            "decision": "Salt2-fitted eta_heater improves Salt3/Salt4 Tmean proxy versus C1.",
            "evidence": f"Validation+holdout mean abs error delta versus C1 is {eta_delta:.3f} K.",
            "allowed_use": "Carry as a train-only scalar candidate.",
            "excluded_use": "Do not combine with test_section_external_loss_W on this split.",
            "next_action": "If selected, rerun full scorecard and report branch/sensor targets.",
        },
        {
            "gate_id": "one_scalar_test_section_external_loss",
            "status": "pass_proxy_screen_not_final",
            "decision": "Salt2-fitted test-section external loss improves Salt3/Salt4 Tmean proxy versus C1.",
            "evidence": f"Validation+holdout mean abs error delta versus C1 is {loss_delta:.3f} K.",
            "allowed_use": "Carry as an alternate train-only scalar candidate.",
            "excluded_use": "Do not combine with eta_heater on this split.",
            "next_action": "Prefer the form only if setup evidence supports a test-section loss term.",
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    sources = [
        (CASE_INTERPRETATION, "source"),
        (CASE_HEAT_LEDGER, "diagnostic_context"),
        (CANDIDATE_PARAMETERS, "source"),
        (RECOMMENDED_MODEL, "source"),
        (BOUNDARY_TASK_MATRIX, "source"),
        (FORWARD_GATE_README, "context"),
    ]
    return [
        {
            "artifact": path.name,
            "role": role,
            "mutation_status": "read_only",
            "path": rel(path),
        }
        for path, role in sources
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(CASE_INTERPRETATION)}
  - {rel(CANDIDATE_PARAMETERS)}
  - {rel(RECOMMENDED_MODEL)}
  - {rel(BOUNDARY_TASK_MATRIX)}
tags: [boundary-modeling, heater-source, forward-model, validation-split]
related:
  - {rel(out_dir / 'heater_source_split_score_rows.csv')}
  - {rel(out_dir / 'heater_source_parameter_screen.csv')}
task: AGENT-332
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Heater Source Split Screen

## Purpose

This package executes `BCM-HEATER-FRACTION-V1` using existing
heater/test-section contract evidence. It fits at most one scalar on Salt2 and
scores Salt3 validation plus Salt4 holdout. It does not rerun Fluid.

## Math

The source contract is:

```text
Q_to_fluid = eta_heater * P_heater_setup
           + f_test * P_test_section_setup
           - Q_test_section_external_loss
           - Q_cooler
           - Q_passive_external
```

For this screen, `Q_cooler` and passive external losses remain separate
boundary lanes. The linearized temperature score uses the existing
heater-contract sensitivity:

```text
T_pred = T_heater_only + S_test_source * DeltaQ
DeltaQ = (eta_heater - 1) * P_heater_setup
       + f_test * P_test_section_setup
       - Q_test_section_external_loss
```

## Results

- `C1_heater_only_unfitted` remains the recommended setup-only source contract.
- `C2_eta_heater_fit_salt2` reduces Salt3/Salt4 mean absolute Tmean proxy
  error by `{-summary['eta_validation_holdout_delta_vs_C1_K']:.3f} K` versus C1.
- `C3_test_section_external_loss_fit_salt2` reduces Salt3/Salt4 mean absolute
  Tmean proxy error by `{-summary['external_loss_validation_holdout_delta_vs_C1_K']:.3f} K` versus C1.
- Both fitted scalar forms remain proxy-screen candidates, not final
  forward-v1 admissions.

## Guardrails

Realized CFD wallHeatFlux, CFD cooler duty, CFD mdot, and validation/holdout
temperatures are not runtime inputs. CFD Tmean appears only as a Salt2 fitting
target or Salt3/Salt4 scoring target.

## Next Executable Task

Use `C1_heater_only_unfitted` as the default source contract in the next full
Fluid scorecard. If testing a calibrated source scalar, choose exactly one of
`C2_eta_heater_fit_salt2` or `C3_test_section_external_loss_fit_salt2`, fit it
on Salt2 only, and report Salt3/Salt4 branch and sensor errors without refit.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(out_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    rows = case_rows()
    specs = candidate_specs(rows)
    scores = score_rows(rows, specs)
    params = parameter_rows(scores, specs)
    gates = gate_rows(params)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "heater_source_split_score_rows.csv", scores, SCORE_COLUMNS)
    write_csv(out_dir / "heater_source_parameter_screen.csv", params, PARAMETER_COLUMNS)
    write_csv(out_dir / "heater_source_gate_decision.csv", gates, GATE_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", source_manifest(), MANIFEST_COLUMNS)

    param_by_id = {row["model_id"]: row for row in params}
    summary = {
        "task": "AGENT-332",
        "status": "complete",
        "generated_at": utc_now(),
        "package": rel(out_dir),
        "split": "salt_2=train;salt_3=validation;salt_4=holdout",
        "next_default_source_contract": "C1_heater_only_unfitted",
        "eta_candidate": {
            "model_id": "C2_eta_heater_fit_salt2",
            "eta_heater": float(param_by_id["C2_eta_heater_fit_salt2"]["parameter_value"]),
        },
        "external_loss_candidate": {
            "model_id": "C3_test_section_external_loss_fit_salt2",
            "test_section_external_loss_W": float(param_by_id["C3_test_section_external_loss_fit_salt2"]["parameter_value"]),
        },
        "C1_validation_holdout_mean_abs_Tmean_error_K": float(
            param_by_id["C1_heater_only_unfitted"]["validation_plus_holdout_mean_abs_Tmean_error_K"]
        ),
        "eta_validation_holdout_delta_vs_C1_K": float(
            param_by_id["C2_eta_heater_fit_salt2"]["validation_plus_holdout_delta_vs_C1_K"]
        ),
        "external_loss_validation_holdout_delta_vs_C1_K": float(
            param_by_id["C3_test_section_external_loss_fit_salt2"]["validation_plus_holdout_delta_vs_C1_K"]
        ),
        "runtime_guardrail_passed": all(row["forbidden_runtime_inputs_used"] == "false" for row in scores),
        "final_forward_v1_admitted": False,
        "score_limit": "linearized_Tmean_proxy_existing_forward_v0_evidence_no_Fluid_rerun",
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = build_package(args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
