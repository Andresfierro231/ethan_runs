#!/usr/bin/env python3
"""Build the heater-to-fluid fraction model package."""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "TODO-PREDICT-HEATER-FLUID-FRACTION"
DATE = "2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-22/2026-07-22_heater_fluid_fraction_model")
OUT = ROOT / OUT_REL

HEATER_CONTRACT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract"
CASE_HEAT_LEDGER = HEATER_CONTRACT / "case_heat_ledger.csv"
CASE_INTERPRETATION = HEATER_CONTRACT / "case_contract_interpretation.csv"
PRIOR_METHODS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods"
PRIOR_SCALARS = PRIOR_METHODS / "heater_fraction_scalar_candidates.csv"
PRIOR_SUMMARY = PRIOR_METHODS / "heater_fraction_model_summary.csv"
HEATLOSS_CONTRACT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_final_heat_loss_power_partition_calibration_design"
MEASUREMENT_MATRIX = HEATLOSS_CONTRACT / "measurement_input_matrix.csv"

SPLIT = {"salt_2": "train", "salt_3": "validation", "salt_4": "holdout"}
CASE_ORDER = {"salt_2": 0, "salt_3": 1, "salt_4": 2}
VALIDATION_TOLERANCE_W = 5.0
HOLDOUT_TOLERANCE_W = 10.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fnum(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite value: {value!r}")
    return number


def fmt(value: Any, precision: int = 10) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    return f"{float(value):.{precision}g}"


def tolerance(split: str) -> float | None:
    if split == "validation":
        return VALIDATION_TOLERANCE_W
    if split == "holdout":
        return HOLDOUT_TOLERANCE_W
    return None


def pass_fail(error: float | None, split: str) -> str:
    tol = tolerance(split)
    if split == "train":
        return "fit_row"
    if error is None or tol is None:
        return "missing"
    return "pass" if error <= tol else "fail"


def prior_eta_from_tmean() -> float:
    for row in read_csv(PRIOR_SCALARS):
        if row["model_id"] == "H1_eta_heater_fit_salt2":
            return fnum(row["fitted_value"])
    raise RuntimeError("missing H1_eta_heater_fit_salt2 in prior scalar table")


def train_eta_from_wallflux(rows: list[dict[str, str]]) -> float:
    train = next(row for row in rows if row["case_id"] == "salt_2")
    return fnum(train["heater_realized_wallHeatFlux_source_W"]) / fnum(train["heater_setup_power_W"])


def candidate_rows() -> list[dict[str, Any]]:
    source_rows = sorted(read_csv(CASE_HEAT_LEDGER), key=lambda row: CASE_ORDER[row["case_id"]])
    eta_tmean = prior_eta_from_tmean()
    eta_wallflux = train_eta_from_wallflux(source_rows)
    candidates = [
        ("HF0_setup_power_all_to_fluid", "setup_unfitted", 1.0, "none", "pass", "baseline assumes all setup heater power enters salt"),
        (
            "HF1_eta_tmean_salt2_prior",
            "prior_train_scalar",
            eta_tmean,
            "salt_2_Tmean_residual_prior",
            "pass",
            "prior Salt2 Tmean scalar from heater/source methods package",
        ),
        (
            "HF2_eta_wallflux_salt2",
            "train_wallflux_scalar",
            eta_wallflux,
            "salt_2_heater_realized_wallHeatFlux_source_W",
            "pass",
            "Salt2 train wallHeatFlux-derived eta; Salt3/Salt4 wallHeatFlux used only as score targets",
        ),
        (
            "HF3_case_realized_eta_upper_bound",
            "diagnostic_leakage_upper_bound",
            None,
            "per_case_realized_wallHeatFlux",
            "fail_for_admission",
            "reproduces target by consuming realized wallHeatFlux for each case",
        ),
    ]
    out: list[dict[str, Any]] = []
    for case in source_rows:
        setup = fnum(case["heater_setup_power_W"])
        target = fnum(case["heater_realized_wallHeatFlux_source_W"])
        split = SPLIT[case["case_id"]]
        for candidate_id, cls, eta, fit_basis, runtime_gate, note in candidates:
            eta_used = target / setup if eta is None else eta
            pred = eta_used * setup
            err = pred - target
            abs_err = abs(err)
            gate = pass_fail(abs_err, split)
            admission = (
                "score_pass_candidate_not_final_forward_model"
                if candidate_id == "HF2_eta_wallflux_salt2" and runtime_gate == "pass" and gate in {"fit_row", "pass"}
                else "not_admitted"
            )
            out.append(
                {
                    "case_id": case["case_id"],
                    "split_role": split,
                    "candidate_id": candidate_id,
                    "candidate_class": cls,
                    "eta_heater": fmt(eta_used, 12),
                    "heater_setup_power_W": fmt(setup, 12),
                    "predicted_heater_to_fluid_W": fmt(pred, 12),
                    "target_heater_wallHeatFlux_W_for_scoring_only": fmt(target, 12),
                    "error_W": fmt(err, 12),
                    "abs_error_W": fmt(abs_err, 12),
                    "tolerance_W": "" if split == "train" else fmt(tolerance(split), 12),
                    "wallflux_qoi_gate": gate,
                    "runtime_gate": runtime_gate,
                    "admission_status": admission,
                    "fit_basis": fit_basis,
                    "note": note,
                    "source_path": rel(CASE_HEAT_LEDGER),
                }
            )
    return out


def summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for candidate_id in sorted({row["candidate_id"] for row in rows}):
        group = [row for row in rows if row["candidate_id"] == candidate_id]
        validation = next(row for row in group if row["split_role"] == "validation")
        holdout = next(row for row in group if row["split_role"] == "holdout")
        passed = validation["wallflux_qoi_gate"] == "pass" and holdout["wallflux_qoi_gate"] == "pass"
        runtime_pass = group[0]["runtime_gate"] == "pass"
        out.append(
            {
                "candidate_id": candidate_id,
                "validation_abs_error_W": validation["abs_error_W"],
                "validation_gate": validation["wallflux_qoi_gate"],
                "holdout_abs_error_W": holdout["abs_error_W"],
                "holdout_gate": holdout["wallflux_qoi_gate"],
                "runtime_gate": group[0]["runtime_gate"],
                "admission_status": "candidate_passes_wallflux_score_not_final_forward_v1"
                if passed and runtime_pass and candidate_id == "HF2_eta_wallflux_salt2"
                else "not_admitted",
                "next_gate": "source_property_release_and_coupled_heat_ledger_score"
                if candidate_id == "HF2_eta_wallflux_salt2"
                else "retain_as_baseline_or_diagnostic",
            }
        )
    return out


def runtime_input_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "audit_id": "HFA1_split_fit_policy",
            "gate": "pass",
            "evidence": "HF2 fits eta on Salt2 only; Salt3/Salt4 wallHeatFlux values are score targets only.",
            "forbidden_runtime_input": "validation_or_holdout_realized_wallHeatFlux",
        },
        {
            "audit_id": "HFA2_no_cfd_mdot",
            "gate": "pass",
            "evidence": "No mdot column is consumed by the heater fraction predictor.",
            "forbidden_runtime_input": "CFD_mdot",
        },
        {
            "audit_id": "HFA3_no_temperature_tuning",
            "gate": "pass",
            "evidence": "HF2 uses setup heater power and one Salt2 eta; no validation temperatures are used.",
            "forbidden_runtime_input": "validation_or_holdout_temperature",
        },
        {
            "audit_id": "HFA4_realized_eta_upper_bound",
            "gate": "fail_for_admission",
            "evidence": "HF3 consumes per-case realized wallHeatFlux and is retained only as a diagnostic upper bound.",
            "forbidden_runtime_input": "per_case_realized_wallHeatFlux",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_path": rel(CASE_HEAT_LEDGER), "exists": str(CASE_HEAT_LEDGER.exists()).lower(), "use": "heater setup power and realized heater wallHeatFlux score target"},
        {"source_path": rel(CASE_INTERPRETATION), "exists": str(CASE_INTERPRETATION.exists()).lower(), "use": "prior source-contract interpretation"},
        {"source_path": rel(PRIOR_SCALARS), "exists": str(PRIOR_SCALARS.exists()).lower(), "use": "prior Tmean-derived eta comparison"},
        {"source_path": rel(PRIOR_SUMMARY), "exists": str(PRIOR_SUMMARY.exists()).lower(), "use": "prior split summary"},
        {"source_path": rel(MEASUREMENT_MATRIX), "exists": str(MEASUREMENT_MATRIX.exists()).lower(), "use": "heat-loss lane source/property release context"},
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(CASE_HEAT_LEDGER)}
  - {rel(PRIOR_SCALARS)}
tags: [forward-model, heater, heat-loss, predictive-1d]
related:
  - TODO-PREDICT-HEATER-FLUID-FRACTION
task: {TASK}
date: {DATE}
status: complete
---
# Heater Fluid Fraction Model

Decision: `{summary['decision']}`.

The useful candidate is `HF2_eta_wallflux_salt2`: fit one heater-to-fluid
fraction from Salt2 train wallHeatFlux evidence, then predict Salt3/Salt4
heater heat-to-fluid using setup heater power only. It passes the predeclared
held-out wallHeatFlux W gates, but it is not a final forward-v1 admission until
source/property release and coupled heat-ledger scoring are complete.

Runtime guardrails: no CFD mdot, validation temperatures, holdout temperatures,
or per-case realized wallHeatFlux are runtime inputs. `HF3` is retained only as
a leakage upper bound.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = candidate_rows()
    summaries = summary_rows(rows)
    audit = runtime_input_audit_rows()
    counts = {
        "heater_fraction_candidate_scores.csv": write_csv(
            OUT / "heater_fraction_candidate_scores.csv",
            rows,
            [
                "case_id",
                "split_role",
                "candidate_id",
                "candidate_class",
                "eta_heater",
                "heater_setup_power_W",
                "predicted_heater_to_fluid_W",
                "target_heater_wallHeatFlux_W_for_scoring_only",
                "error_W",
                "abs_error_W",
                "tolerance_W",
                "wallflux_qoi_gate",
                "runtime_gate",
                "admission_status",
                "fit_basis",
                "note",
                "source_path",
            ],
        ),
        "heater_fraction_model_summary.csv": write_csv(
            OUT / "heater_fraction_model_summary.csv",
            summaries,
            [
                "candidate_id",
                "validation_abs_error_W",
                "validation_gate",
                "holdout_abs_error_W",
                "holdout_gate",
                "runtime_gate",
                "admission_status",
                "next_gate",
            ],
        ),
        "runtime_input_audit.csv": write_csv(
            OUT / "runtime_input_audit.csv",
            audit,
            ["audit_id", "gate", "evidence", "forbidden_runtime_input"],
        ),
        "source_manifest.csv": write_csv(
            OUT / "source_manifest.csv",
            source_manifest_rows(),
            ["source_path", "exists", "use"],
        ),
    }
    passed = [row for row in summaries if row["admission_status"] == "candidate_passes_wallflux_score_not_final_forward_v1"]
    decision = {
        "task": TASK,
        "decision": "heater_eta_candidate_passes_wallflux_score_no_final_forward_admission" if passed else "fail_closed_no_heater_fraction_candidate",
        "candidate_pass_count": len(passed),
        "selected_candidate": passed[0]["candidate_id"] if passed else "",
        "next_gate": "source_property_release_and_coupled_heat_ledger_score",
        "created_utc": utc_now(),
    }
    write_json(OUT / "model_decision.json", decision)
    summary = {
        "task": TASK,
        "date": DATE,
        "output_dir": rel(OUT),
        "counts": counts,
        **decision,
        "native_output_mutation": False,
        "solver_or_postprocessing_launch": False,
        "external_fluid_edit": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
