#!/usr/bin/env python3
"""Build the current predictive test-section heat-loss admission package."""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "TODO-PREDICT-TEST-SECTION-HEAT-LOSS"
DATE = "2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-22/2026-07-22_predictive_test_section_heat_loss_model")
OUT = ROOT / OUT_REL

PARITY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study"
OVERNIGHT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run"
BAKEOFF = OVERNIGHT / "test_section_boundary_form_bakeoff"
M2M3 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report"

SETUP_SOURCE = PARITY / "external_bc_segment_equivalents.csv"
DIAGNOSTIC_SOURCE = BAKEOFF / "test_section_model_result_ledger.csv"
PROBE_SOURCE = BAKEOFF / "test_section_temperature_probe_summary.csv"
M2M3_SOURCE = M2M3 / "case_mode_error_matrix.csv"

VALIDATION_W_TOL = 5.0
HOLDOUT_W_TOL = 10.0
PCT_TOL = 25.0

SPLIT_ORDER = {"train": 0, "validation": 1, "holdout": 2}


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


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: Any, precision: int = 10) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.{precision}g}"


def split_w_tolerance(split_role: str) -> float | None:
    if split_role == "validation":
        return VALIDATION_W_TOL
    if split_role == "holdout":
        return HOLDOUT_W_TOL
    return None


def pass_fail(value: float | None, tolerance: float | None) -> str:
    if value is None or tolerance is None:
        return "missing"
    return "pass" if value <= tolerance else "fail"


def qoi_gate(abs_error_w: float | None, pct_error: float | None, split_role: str) -> str:
    if split_role == "train":
        return "fit_row_not_generalization_scored"
    if pass_fail(abs_error_w, split_w_tolerance(split_role)) == "pass" and pass_fail(pct_error, PCT_TOL) == "pass":
        return "pass"
    return "fail"


def load_test_section_setup_rows() -> list[dict[str, Any]]:
    rows = [row for row in read_csv(SETUP_SOURCE) if row["role"] == "test_section"]
    if len(rows) != 3:
        raise RuntimeError(f"Expected exactly three test-section setup rows, found {len(rows)}")
    out: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: SPLIT_ORDER[item["validation_split_role"]]):
        out.append(
            {
                "case_id": row["case_id"],
                "split_role": row["validation_split_role"],
                "area_m2": safe_float(row["area_m2"]),
                "hA_W_per_K": safe_float(row["hA_W_K"]),
                "h_W_m2K": safe_float(row["h_W_m2K"]),
                "Ta_K": safe_float(row["Ta_K"]),
                "Tsur_K": safe_float(row["Tsur_K"]),
                "emissivity": safe_float(row["emissivity"]),
                "wall_thickness_m": row["thickness_total_m"],
                "target_loss_W_for_scoring_only": safe_float(row["realized_external_loss_W"]),
                "imposed_source_W_document_only": safe_float(row["imposed_Q_W"]),
                "recommended_drive_selector": row["recommended_drive_selector"],
                "source_path": rel(SETUP_SOURCE),
            }
        )
    return out


def fit_training_scalars(setup_rows: list[dict[str, Any]]) -> dict[str, float]:
    train = next(row for row in setup_rows if row["split_role"] == "train")
    hA = train["hA_W_per_K"]
    target = train["target_loss_W_for_scoring_only"]
    if hA in (None, 0.0) or target is None:
        raise RuntimeError("Salt2 train hA and scoring target are required")
    return {
        "salt2_fit_drive_delta_T_K": target / hA,
        "salt2_fit_constant_loss_W": target,
    }


def candidate_prediction(row: dict[str, Any], scalars: dict[str, float], candidate_id: str) -> tuple[float | None, str]:
    if candidate_id == "TS0_no_test_section_loss":
        return 0.0, "diagnostic_baseline_no_physical_loss"
    if candidate_id == "TS1_salt2_fit_hA_constant_drive_deltaT":
        hA = row["hA_W_per_K"]
        return None if hA is None else hA * scalars["salt2_fit_drive_delta_T_K"], "setup_hA_times_salt2_fitted_drive_deltaT"
    if candidate_id == "TS2_salt2_fit_constant_loss_W":
        return scalars["salt2_fit_constant_loss_W"], "setup_constant_W_from_salt2_training_only"
    if candidate_id == "TS3_legacy_37W_source_as_loss":
        return row["imposed_source_W_document_only"], "legacy_documented_source_treated_as_loss_rejected"
    if candidate_id == "TS4_realized_external_loss_upper_bound":
        return row["target_loss_W_for_scoring_only"], "realized_cfd_loss_upper_bound_runtime_leakage"
    raise KeyError(candidate_id)


def candidate_runtime_gate(candidate_id: str) -> str:
    if candidate_id in {"TS1_salt2_fit_hA_constant_drive_deltaT", "TS2_salt2_fit_constant_loss_W"}:
        return "pass_setup_only_inputs_after_salt2_training"
    if candidate_id == "TS0_no_test_section_loss":
        return "pass_but_not_a_physical_loss_model"
    if candidate_id == "TS3_legacy_37W_source_as_loss":
        return "fail_source_is_documented_imposed_Q_not_passive_loss_model"
    if candidate_id == "TS4_realized_external_loss_upper_bound":
        return "fail_uses_realized_cfd_loss_at_runtime"
    raise KeyError(candidate_id)


def candidate_end_to_end_gate(candidate_id: str) -> str:
    if candidate_id == "TS0_no_test_section_loss":
        return "diagnostic_m3_baseline_scored_but_no_test_section_loss"
    if candidate_id in {"TS1_salt2_fit_hA_constant_drive_deltaT", "TS2_salt2_fit_constant_loss_W"}:
        return "fail_no_solver_coupled_m3ts_run_for_candidate"
    return "fail_not_scientifically_admissible_for_end_to_end_scoring"


def candidate_admission(candidate_id: str, gate: str, runtime_gate: str, end_to_end_gate: str) -> str:
    if candidate_id not in {"TS1_salt2_fit_hA_constant_drive_deltaT", "TS2_salt2_fit_constant_loss_W"}:
        return "not_admitted_not_a_setup_only_physical_candidate"
    if gate == "pass" and runtime_gate.startswith("pass") and end_to_end_gate == "pass":
        return "admitted_predictive_test_section_heat_loss_model"
    return "not_admitted"


def setup_loss_candidate_rows() -> list[dict[str, Any]]:
    setup_rows = load_test_section_setup_rows()
    scalars = fit_training_scalars(setup_rows)
    candidates = [
        "TS0_no_test_section_loss",
        "TS1_salt2_fit_hA_constant_drive_deltaT",
        "TS2_salt2_fit_constant_loss_W",
        "TS3_legacy_37W_source_as_loss",
        "TS4_realized_external_loss_upper_bound",
    ]
    out: list[dict[str, Any]] = []
    for candidate_id in candidates:
        runtime_gate = candidate_runtime_gate(candidate_id)
        end_to_end_gate = candidate_end_to_end_gate(candidate_id)
        for row in setup_rows:
            predicted, fit_policy = candidate_prediction(row, scalars, candidate_id)
            target = row["target_loss_W_for_scoring_only"]
            error = None if predicted is None or target is None else predicted - target
            abs_error = None if error is None else abs(error)
            pct_error = None if abs_error is None or target in (None, 0.0) else 100.0 * abs_error / abs(target)
            gate = qoi_gate(abs_error, pct_error, row["split_role"])
            out.append(
                {
                    "case_id": row["case_id"],
                    "split_role": row["split_role"],
                    "candidate_id": candidate_id,
                    "candidate_class": "setup_only_physical_candidate"
                    if candidate_id in {"TS1_salt2_fit_hA_constant_drive_deltaT", "TS2_salt2_fit_constant_loss_W"}
                    else "diagnostic_or_rejected_candidate",
                    "fit_policy": fit_policy,
                    "runtime_policy": "Allowed runtime inputs are setup hA/area/h/Ta/Tsur/emissivity/coverage and Salt2-trained scalars only.",
                    "area_m2": fmt(row["area_m2"]),
                    "hA_W_per_K": fmt(row["hA_W_per_K"]),
                    "h_W_m2K": fmt(row["h_W_m2K"]),
                    "Ta_K": fmt(row["Ta_K"]),
                    "Tsur_K": fmt(row["Tsur_K"]),
                    "emissivity": fmt(row["emissivity"]),
                    "wall_thickness_m": row["wall_thickness_m"],
                    "fitted_drive_delta_T_K": fmt(scalars["salt2_fit_drive_delta_T_K"])
                    if candidate_id == "TS1_salt2_fit_hA_constant_drive_deltaT"
                    else "",
                    "fitted_constant_loss_W": fmt(scalars["salt2_fit_constant_loss_W"])
                    if candidate_id == "TS2_salt2_fit_constant_loss_W"
                    else "",
                    "predicted_loss_W": fmt(predicted),
                    "scoring_target_loss_W": fmt(target),
                    "error_W": fmt(error),
                    "abs_error_W": fmt(abs_error),
                    "abs_error_pct_of_target": fmt(pct_error),
                    "watts_gate": pass_fail(abs_error, split_w_tolerance(row["split_role"]))
                    if row["split_role"] != "train"
                    else "fit_row_not_generalization_scored",
                    "percent_gate": pass_fail(pct_error, PCT_TOL)
                    if row["split_role"] != "train"
                    else "fit_row_not_generalization_scored",
                    "qoi_gate": gate,
                    "runtime_gate": runtime_gate,
                    "end_to_end_gate": end_to_end_gate,
                    "admission_decision": candidate_admission(candidate_id, gate, runtime_gate, end_to_end_gate),
                    "source_path": row["source_path"],
                }
            )
    return out


def setup_candidate_summary_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for candidate_id in sorted({row["candidate_id"] for row in candidate_rows}):
        rows = [row for row in candidate_rows if row["candidate_id"] == candidate_id]
        validation = next(row for row in rows if row["split_role"] == "validation")
        holdout = next(row for row in rows if row["split_role"] == "holdout")
        runtime_gate = rows[0]["runtime_gate"]
        end_to_end_gate = rows[0]["end_to_end_gate"]
        admitted = (
            candidate_id in {"TS1_salt2_fit_hA_constant_drive_deltaT", "TS2_salt2_fit_constant_loss_W"}
            and validation["qoi_gate"] == "pass"
            and holdout["qoi_gate"] == "pass"
            and runtime_gate.startswith("pass")
            and end_to_end_gate == "pass"
        )
        failures = []
        for label, row in [("validation", validation), ("holdout", holdout)]:
            if row["qoi_gate"] != "pass":
                failures.append(
                    f"{label}_q_loss_gate={row['qoi_gate']} "
                    f"(abs={row['abs_error_W']} W, pct={row['abs_error_pct_of_target']}%)"
                )
        if not runtime_gate.startswith("pass"):
            failures.append(f"runtime_gate={runtime_gate}")
        if end_to_end_gate != "pass":
            failures.append(f"end_to_end_gate={end_to_end_gate}")
        if candidate_id == "TS0_no_test_section_loss":
            failures.append("no_test_section_loss_is_not_a_physical_submodel")
        out.append(
            {
                "candidate_id": candidate_id,
                "candidate_class": rows[0]["candidate_class"],
                "validation_abs_error_W": validation["abs_error_W"],
                "validation_abs_error_pct": validation["abs_error_pct_of_target"],
                "validation_qoi_gate": validation["qoi_gate"],
                "holdout_abs_error_W": holdout["abs_error_W"],
                "holdout_abs_error_pct": holdout["abs_error_pct_of_target"],
                "holdout_qoi_gate": holdout["qoi_gate"],
                "runtime_gate": runtime_gate,
                "end_to_end_gate": end_to_end_gate,
                "admission_decision": "admitted_predictive_test_section_heat_loss_model" if admitted else "not_admitted",
                "blocker_effect": "resolve_predictive_wall_test_section_submodels" if admitted else "keep_blocker_open",
                "primary_reason": "; ".join(failures) if failures else "all_gates_passed",
            }
        )
    return out


def probe_lookup() -> dict[tuple[str, str, str], dict[str, str]]:
    return {
        (row["case_id"], row["mode_id"], row["kind"]): row
        for row in read_csv(PROBE_SOURCE)
    }


def diagnostic_comparison_rows() -> list[dict[str, Any]]:
    probes = probe_lookup()
    out: list[dict[str, Any]] = []
    for row in read_csv(M2M3_SOURCE):
        if row["mode_id"] not in {"M2_cfd_heater_test_section_cooler_pressure_root", "M3_setup_heater_cooler_no_test_section"}:
            continue
        out.append(
            {
                "case_id": row["case_id"],
                "split_role": row["split"],
                "mode_id": row["mode_id"],
                "diagnostic_family": "M2_realized_cfd_boundary_replay"
                if row["mode_id"].startswith("M2_")
                else "M3_no_test_section_loss_baseline",
                "uses_realized_test_section_loss_runtime": "yes_for_m2" if row["mode_id"].startswith("M2_") else "no",
                "prescribed_test_section_loss_W": "",
                "mdot_error_pct": row["mdot_error_pct"],
                "Tmean_error_K": row["Tmean_error_K"],
                "loop_delta_error_K": row["loop_delta_error_K"],
                "all_probe_rmse_K": row["all_probe_rmse_K"],
                "tp_rmse_K": row["tp_rmse_K"],
                "tw_rmse_K": row["tw_rmse_K"],
                "admission_use": "diagnostic_reference_not_a_setup_only_predictive_candidate",
                "source_path": rel(M2M3_SOURCE),
            }
        )
    for row in read_csv(DIAGNOSTIC_SOURCE):
        tp = probes.get((row["case_id"], row["mode_id"], "TP"), {})
        tw = probes.get((row["case_id"], row["mode_id"], "TW"), {})
        out.append(
            {
                "case_id": row["case_id"],
                "split_role": row["split"],
                "mode_id": row["mode_id"],
                "diagnostic_family": row["predictivity_class"],
                "uses_realized_test_section_loss_runtime": "yes"
                if row["mode_id"] in {"prescribed_test_loss", "half_prescribed_test_loss", "negative_source_compatibility"}
                else "no",
                "prescribed_test_section_loss_W": row["prescribed_loss_total_W"],
                "mdot_error_pct": row["mdot_error_pct"],
                "Tmean_error_K": row["Tmean_error_K"],
                "loop_delta_error_K": row["loop_delta_error_K"],
                "all_probe_rmse_K": "",
                "tp_rmse_K": tp.get("rmse_K", ""),
                "tw_rmse_K": tw.get("rmse_K", ""),
                "admission_use": "diagnostic_only_existing_bakeoff_not_a_new_setup_only_m3ts_score",
                "source_path": f"{rel(DIAGNOSTIC_SOURCE)};{rel(PROBE_SOURCE)}",
            }
        )
    return sorted(out, key=lambda item: (SPLIT_ORDER[item["split_role"]], item["case_id"], item["mode_id"]))


def runtime_input_audit_rows() -> list[dict[str, Any]]:
    return [
        {
            "audit_id": "R1_setup_inputs_for_TS1_TS2",
            "gate": "pass",
            "applies_to": "TS1_salt2_fit_hA_constant_drive_deltaT;TS2_salt2_fit_constant_loss_W",
            "observed_state": "Candidates use setup hA/area/h/Ta/Tsur/emissivity and a Salt2-trained scalar only for prediction.",
            "forbidden_runtime_input": "validation/holdout temperatures, realized CFD wallHeatFlux, CFD mdot",
        },
        {
            "audit_id": "R2_training_target_is_not_runtime_input",
            "gate": "pass",
            "applies_to": "TS1_salt2_fit_hA_constant_drive_deltaT;TS2_salt2_fit_constant_loss_W",
            "observed_state": "Salt2 realized external loss is used only to fit one scalar on the training split; Salt3/Salt4 realized losses are scoring targets only.",
            "forbidden_runtime_input": "validation/holdout realized external loss",
        },
        {
            "audit_id": "R3_zero_test_section_is_baseline_only",
            "gate": "pass_with_admission_exclusion",
            "applies_to": "TS0_no_test_section_loss",
            "observed_state": "The no-loss form has existing M3 diagnostic scores but cannot remove a blocker whose requirement is a physical test-section heat-loss model.",
            "forbidden_runtime_input": "none",
        },
        {
            "audit_id": "R4_legacy_source_not_passive_loss",
            "gate": "fail_for_admission",
            "applies_to": "TS3_legacy_37W_source_as_loss",
            "observed_state": "The 37 W value is documented as an imposed source, not an admitted passive loss model.",
            "forbidden_runtime_input": "misclassified imposed CFD source",
        },
        {
            "audit_id": "R5_realized_loss_upper_bound_is_leakage",
            "gate": "fail_for_admission",
            "applies_to": "TS4_realized_external_loss_upper_bound",
            "observed_state": "Using realized external loss reproduces targets by definition and is retained only as an upper-bound diagnostic.",
            "forbidden_runtime_input": "realized CFD test-section heat loss",
        },
        {
            "audit_id": "R6_no_solver_coupled_candidate_run_yet",
            "gate": "incomplete_for_admission",
            "applies_to": "TS1_salt2_fit_hA_constant_drive_deltaT;TS2_salt2_fit_constant_loss_W",
            "observed_state": "No existing Fluid/1D run couples these predicted test-section losses into an M3+TS mdot/TP/TW scorecard.",
            "forbidden_runtime_input": "not applicable",
        },
    ]


def blocker_decision(summary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    admitted = [row for row in summary_rows if row["admission_decision"] == "admitted_predictive_test_section_heat_loss_model"]
    best_physical = [
        row
        for row in summary_rows
        if row["candidate_id"] in {"TS1_salt2_fit_hA_constant_drive_deltaT", "TS2_salt2_fit_constant_loss_W"}
    ]
    return {
        "task": TASK,
        "blocker_id": "predictive-wall-test-section-submodels",
        "decision": "resolve" if admitted else "keep_open",
        "admitted_candidate_count": len(admitted),
        "best_setup_only_physical_candidates": [row["candidate_id"] for row in best_physical],
        "why": (
            "A setup-only Salt2-fit test-section loss model passed validation/holdout W gates, runtime audit, and end-to-end M3+TS scoring."
            if admitted
            else "No setup-only physical test-section candidate is admitted: Salt2-fit hA/constant-loss forms underpredict held-out heat loss and no solver-coupled M3+TS score exists for them."
        ),
        "next_required_action": "Run or implement solver-coupled M3+TS with segment external-boundary/resistance-network drive and score mdot plus TP/TW on Salt3/Salt4."
        if not admitted
        else "Publish admitted candidate into final predictive end-to-end scorecard.",
        "evidence": rel(OUT / "setup_candidate_summary.csv"),
        "generated_at": utc_now(),
    }


def write_readme(decision: dict[str, Any], summary_rows: list[dict[str, Any]]) -> None:
    physical = {
        row["candidate_id"]: row for row in summary_rows if row["candidate_id"].startswith("TS1_") or row["candidate_id"].startswith("TS2_")
    }
    ts1 = physical["TS1_salt2_fit_hA_constant_drive_deltaT"]
    ts2 = physical["TS2_salt2_fit_constant_loss_W"]
    text = f"""---
provenance:
  task: {TASK}
  generated_at: {utc_now()}
  sources:
    - {rel(SETUP_SOURCE)}
    - {rel(DIAGNOSTIC_SOURCE)}
    - {rel(PROBE_SOURCE)}
    - {rel(M2M3_SOURCE)}
tags:
  - predictive
  - test-section
  - heat-loss
  - blocker
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
---

# Predictive Test-Section Heat-Loss Model Admission

This package implements the current setup-only test-section heat-loss admission screen for `TODO-PREDICT-TEST-SECTION-HEAT-LOSS`.

## Decision

`predictive-wall-test-section-submodels` remains **open**.

No setup-only physical candidate is admitted. `TS1_salt2_fit_hA_constant_drive_deltaT` is fit on Salt2 only; it has a {ts1['validation_abs_error_W']} W Salt3 validation error and still misses by {ts1['validation_abs_error_pct']}% on Salt3 and {ts1['holdout_abs_error_pct']}% on Salt4, with holdout absolute error {ts1['holdout_abs_error_W']} W. `TS2_salt2_fit_constant_loss_W` behaves similarly, with Salt3/Salt4 percent errors of {ts2['validation_abs_error_pct']}% and {ts2['holdout_abs_error_pct']}%.

Both physical candidates also lack a solver-coupled M3+TS mdot/TP/TW run. Existing no-loss, negative-source, prescribed-loss, and half-prescribed-loss rows are diagnostic only; they cannot be promoted because they either omit the required physical loss model or consume realized CFD heat evidence.

## Outputs

- `setup_loss_candidates.csv` - Salt2-fit setup-only candidate predictions and held-out W gates.
- `setup_candidate_summary.csv` - per-candidate admission decision.
- `end_to_end_diagnostic_comparison.csv` - existing M2/M3 and boundary-form diagnostics kept separate from admission.
- `runtime_input_audit.csv` - allowed/forbidden runtime input audit.
- `blocker_decision.json` - machine-readable blocker decision.
- `source_manifest.csv` - exact source package paths.

## Next Step

Implement or run a solver-coupled M3+TS path that applies the test-section loss through an external-boundary/resistance-network segment model, not through realized CFD wall heat or validation temperatures. The next package should score Salt3/Salt4 mdot, Tmean, loop delta, and TP/TW errors against M2 and M3.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def source_manifest_rows() -> list[dict[str, Any]]:
    return [
        {
            "source_id": "test_section_setup_hA_rows",
            "path": rel(SETUP_SOURCE),
            "use": "setup-only hA/geometry and Salt2 train scoring target; Salt3/Salt4 targets scoring only",
        },
        {
            "source_id": "test_section_boundary_form_bakeoff",
            "path": rel(DIAGNOSTIC_SOURCE),
            "use": "diagnostic M3/negative-source/prescribed-loss comparison",
        },
        {
            "source_id": "test_section_probe_summary",
            "path": rel(PROBE_SOURCE),
            "use": "diagnostic TP/TW RMSE for boundary-form bakeoff modes",
        },
        {
            "source_id": "m2_m3_case_mode_matrix",
            "path": rel(M2M3_SOURCE),
            "use": "existing M2/M3 mdot and temperature error comparison",
        },
    ]


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    candidate_rows = setup_loss_candidate_rows()
    summary_rows = setup_candidate_summary_rows(candidate_rows)
    diagnostics = diagnostic_comparison_rows()
    runtime_rows = runtime_input_audit_rows()
    decision = blocker_decision(summary_rows)

    counts = {
        "setup_loss_candidates.csv": write_csv(
            OUT / "setup_loss_candidates.csv",
            candidate_rows,
            [
                "case_id",
                "split_role",
                "candidate_id",
                "candidate_class",
                "fit_policy",
                "runtime_policy",
                "area_m2",
                "hA_W_per_K",
                "h_W_m2K",
                "Ta_K",
                "Tsur_K",
                "emissivity",
                "wall_thickness_m",
                "fitted_drive_delta_T_K",
                "fitted_constant_loss_W",
                "predicted_loss_W",
                "scoring_target_loss_W",
                "error_W",
                "abs_error_W",
                "abs_error_pct_of_target",
                "watts_gate",
                "percent_gate",
                "qoi_gate",
                "runtime_gate",
                "end_to_end_gate",
                "admission_decision",
                "source_path",
            ],
        ),
        "setup_candidate_summary.csv": write_csv(
            OUT / "setup_candidate_summary.csv",
            summary_rows,
            [
                "candidate_id",
                "candidate_class",
                "validation_abs_error_W",
                "validation_abs_error_pct",
                "validation_qoi_gate",
                "holdout_abs_error_W",
                "holdout_abs_error_pct",
                "holdout_qoi_gate",
                "runtime_gate",
                "end_to_end_gate",
                "admission_decision",
                "blocker_effect",
                "primary_reason",
            ],
        ),
        "end_to_end_diagnostic_comparison.csv": write_csv(
            OUT / "end_to_end_diagnostic_comparison.csv",
            diagnostics,
            [
                "case_id",
                "split_role",
                "mode_id",
                "diagnostic_family",
                "uses_realized_test_section_loss_runtime",
                "prescribed_test_section_loss_W",
                "mdot_error_pct",
                "Tmean_error_K",
                "loop_delta_error_K",
                "all_probe_rmse_K",
                "tp_rmse_K",
                "tw_rmse_K",
                "admission_use",
                "source_path",
            ],
        ),
        "runtime_input_audit.csv": write_csv(
            OUT / "runtime_input_audit.csv",
            runtime_rows,
            ["audit_id", "gate", "applies_to", "observed_state", "forbidden_runtime_input"],
        ),
        "source_manifest.csv": write_csv(OUT / "source_manifest.csv", source_manifest_rows(), ["source_id", "path", "use"]),
    }
    write_json(OUT / "blocker_decision.json", decision)
    write_json(
        OUT / "summary.json",
        {
            "task": TASK,
            "date": DATE,
            "output_dir": rel(OUT),
            "counts": counts,
            "decision": decision,
        },
    )
    write_readme(decision, summary_rows)
    return {"output_dir": rel(OUT), "counts": counts, "decision": decision}


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
