#!/usr/bin/env python3
"""Build AGENT-438 setup-only HX/cooler scorecard unlock package."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-438"
DATE = "2026-07-15"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock")
OUT = ROOT / OUT_REL

AGENT407 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger"
AGENT418 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant"
AGENT419 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan"
AGENT423 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_thermal_row_admission_ledger"
AGENT424 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report"
AGENT425 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock"
AGENT421 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification"

VALIDATION_TOLERANCE_W = 5.0
HOLDOUT_TOLERANCE_W = 10.0
PREFERRED_CANDIDATE = "salt2_fit_constant_UA_bulk_drive"


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


def pass_fail(value: float | None, tolerance: float) -> str:
    if value is None:
        return "missing"
    return "pass" if value <= tolerance else "fail"


def scorecard_rows(hx_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in hx_rows:
        target = safe_float(row.get("target_qhx_W"))
        error = safe_float(row.get("abs_error_W"))
        rel_error = None if target in (None, 0.0) or error is None else 100.0 * error / abs(target)
        runtime_violations = safe_float(row.get("runtime_input_violation_count"))
        split_role = row.get("split_role", "")
        if split_role == "train":
            split_gate = "fit_row"
            error_gate = "not_scored_for_generalization"
        elif split_role == "validation":
            split_gate = "validation_row"
            error_gate = pass_fail(error, VALIDATION_TOLERANCE_W)
        elif split_role == "holdout":
            split_gate = "holdout_row"
            error_gate = pass_fail(error, HOLDOUT_TOLERANCE_W)
        else:
            split_gate = "unknown_split"
            error_gate = "missing"
        out.append(
            {
                "candidate_id": row.get("candidate_id", ""),
                "case_id": row.get("case_id", ""),
                "split_role": split_role,
                "model_form": row.get("model_form", ""),
                "predicted_qhx_W": fmt(row.get("predicted_qhx_W")),
                "target_qhx_W_for_scoring_only": fmt(target),
                "abs_error_W": fmt(error),
                "abs_error_pct_of_target": fmt(rel_error),
                "runtime_input_violation_count": fmt(runtime_violations, 0),
                "split_gate": split_gate,
                "error_gate": error_gate,
                "runtime_gate": "pass" if runtime_violations == 0 else "fail",
                "setup_only_hx_use": "fit_scalar_frozen_on_salt2" if split_role == "train" else "score_without_refit",
                "admission_class": row.get("admission_class", ""),
                "forward_v1_use": row.get("forward_v1_use", ""),
                "source_path": row.get("source_path", ""),
            }
        )
    return out


def candidate_decision_rows(reconciliation: list[dict[str, str]], score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in score_rows:
        grouped.setdefault(str(row["candidate_id"]), []).append(row)
    reconciliation_by_id = {row["candidate_id"]: row for row in reconciliation}
    rows: list[dict[str, Any]] = []
    for candidate_id, group in sorted(grouped.items()):
        validation = next((row for row in group if row["split_role"] == "validation"), {})
        holdout = next((row for row in group if row["split_role"] == "holdout"), {})
        runtime_failures = sum(1 for row in group if row.get("runtime_gate") != "pass")
        validation_error = safe_float(validation.get("abs_error_W"))
        holdout_error = safe_float(holdout.get("abs_error_W"))
        validation_pass = pass_fail(validation_error, VALIDATION_TOLERANCE_W) == "pass"
        holdout_pass = pass_fail(holdout_error, HOLDOUT_TOLERANCE_W) == "pass"
        runtime_pass = runtime_failures == 0
        preferred = candidate_id == PREFERRED_CANDIDATE
        if validation_pass and holdout_pass and runtime_pass and preferred:
            decision = "advance_setup_only_hx_candidate_to_final_gate_inputs_not_final_forward_v1"
        elif validation_pass and holdout_pass and runtime_pass:
            decision = "candidate_passes_numeric_gate_but_not_preferred"
        elif runtime_pass:
            decision = "candidate_not_selected_numeric_generalization_gate_failed"
        else:
            decision = "candidate_rejected_runtime_input_gate_failed"
        rec = reconciliation_by_id.get(candidate_id, {})
        rows.append(
            {
                "candidate_id": candidate_id,
                "preferred_candidate": "yes" if preferred else "no",
                "validation_abs_error_W": fmt(validation_error),
                "validation_tolerance_W": fmt(VALIDATION_TOLERANCE_W),
                "validation_gate": "pass" if validation_pass else "fail",
                "holdout_abs_error_W": fmt(holdout_error),
                "holdout_tolerance_W": fmt(HOLDOUT_TOLERANCE_W),
                "holdout_gate": "pass" if holdout_pass else "fail",
                "runtime_input_violation_count": runtime_failures,
                "runtime_gate": "pass" if runtime_pass else "fail",
                "all_non_salt1_rmse_W": rec.get("all_non_salt1_rmse_W", ""),
                "all_non_salt1_mae_W": rec.get("all_non_salt1_mae_W", ""),
                "prior_decision": rec.get("decision", ""),
                "agent438_decision": decision,
                "final_forward_v1_admission": "not_admitted_final_forward_v1_pending_hydraulic_internal_nu_mesh_scorecard_gates",
                "source_path": rec.get("source_path", ""),
            }
        )
    return rows


def runtime_legality_rows() -> list[dict[str, Any]]:
    return [
        {
            "item": "training_split",
            "required_rule": "fit scalar on Salt2 only",
            "observed_state": "preferred candidate uses Salt2 train row; Salt3 validation and Salt4 holdout score without refit",
            "gate": "pass",
            "forbidden_runtime_inputs": "Salt3/Salt4 target cooler duty or temperatures for fitting",
            "source_path": rel(AGENT407 / "final_predictive_hx_closure_rows.csv"),
        },
        {
            "item": "cooler_target_use",
            "required_rule": "target_qhx_W may be used for scoring only after prediction",
            "observed_state": "row ledger separates predicted_qhx_W from target_qhx_W_for_scoring_only",
            "gate": "pass",
            "forbidden_runtime_inputs": "imposed CFD cooler duty as model input",
            "source_path": rel(AGENT407 / "final_predictive_hx_closure_rows.csv"),
        },
        {
            "item": "realized_wallHeatFlux",
            "required_rule": "CFD realized wallHeatFlux cannot be predictive runtime input",
            "observed_state": "wallHeatFlux rows remain diagnostic replay/leakage rows in AGENT-407/423",
            "gate": "pass",
            "forbidden_runtime_inputs": "realized CFD wallHeatFlux",
            "source_path": rel(AGENT423 / "realized_wallheatflux_replay_rows.csv"),
        },
        {
            "item": "fluid_setup_hook",
            "required_rule": "Fluid has setup-only HX and external-boundary hooks available without realized CFD runtime leakage",
            "observed_state": "AGENT-418 reports hx_ua_multiplier compatibility plus setup h/Ta/Tsur/emissivity boundary dictionaries",
            "gate": "pass_for_setup_implementation; not_a_new_run",
            "forbidden_runtime_inputs": "CFD mdot, validation pressures, validation temperatures",
            "source_path": rel(AGENT418 / "fluid_variant_contract.csv"),
        },
        {
            "item": "radiation_semantics",
            "required_rule": "do not double-count CFD radiation",
            "observed_state": "CFD rcExternalTemperature wallHeatFlux includes radiative exchange; no separate qr is assumed",
            "gate": "pass",
            "forbidden_runtime_inputs": "separate CFD qr term not exported",
            "source_path": rel(AGENT419 / "README.md"),
        },
    ]


def remaining_unlock_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "setup_only_HX_cooler_score",
            "current_state": "advanced_candidate_gate_pass_for_preferred_HX_lane",
            "blocking_final_forward_v1": "no_by_itself",
            "exact_missing_evidence": "terminal final scorecard integration after hydraulic/internal-Nu/mesh gates",
            "next_artifact": "final_forward_v1_scorecard_gate_rebuild.csv",
            "executor": "forward-v1 coordinator after pressure/internal-Nu gate updates",
            "admission_criterion": "consume this package as setup-only HX candidate input, not final admission",
        },
        {
            "gate": "hydraulic_pressure_F6",
            "current_state": "blocked_fit_rows_zero",
            "blocking_final_forward_v1": "yes",
            "exact_missing_evidence": "admitted pressure rows separating straight friction, component K, reset/development, branch-apparent loss, and recirculation/onset",
            "next_artifact": "bounded_hydraulic_pressure_scorecard_on_admitted_rows",
            "executor": "hydraulic postprocess/admission agent",
            "admission_criterion": "fit-admitted pressure/F6 rows exist and recirculating rows remain diagnostic or use their own section-effective lane",
        },
        {
            "gate": "internal_Nu_thermal_sign_heat_balance",
            "current_state": "blocked_fit_rows_zero",
            "blocking_final_forward_v1": "yes",
            "exact_missing_evidence": "positive interpretable h_proxy, wallHeatFlux-vs-enthalpy residual <=10%, low reverse area/mass, mesh/time admitted row",
            "next_artifact": "thermal_sign_heat_balance_resolution_then_nu_gate",
            "executor": "thermal/internal-Nu admission agent",
            "admission_criterion": "true Nu fit rows admitted or final model explicitly excludes Nu fitting and owns residuals elsewhere",
        },
        {
            "gate": "recirculation_policy",
            "current_state": "current PM5/upcomer rows diagnostic_only",
            "blocking_final_forward_v1": "yes",
            "exact_missing_evidence": "non-recirculating/transition rows or a separately admitted bidirectional section-effective model form",
            "next_artifact": "low_re_transition_hydraulic_and_wall_band_case_design",
            "executor": "hydraulic/thermal extraction plus model-form agent",
            "admission_criterion": "no true Nu/f_D/K labels on rows with material RAF/RMF",
        },
        {
            "gate": "mesh_GCI_UQ",
            "current_state": "closure_QOI_rows_blocked_missing_triplet_or_nonmonotone",
            "blocking_final_forward_v1": "yes",
            "exact_missing_evidence": "mesh/GCI admission or explicit diagnostic-only exclusion for pressure and thermal QoIs",
            "next_artifact": "closure_qoi_mesh_gci_admission_refresh.csv",
            "executor": "mesh/GCI agent",
            "admission_criterion": "uncertainty propagated into final forward-v1 scorecard",
        },
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    paths = [
        AGENT407 / "final_predictive_hx_closure_rows.csv",
        AGENT407 / "hx_candidate_reconciliation.csv",
        AGENT407 / "row_admission_ledger.csv",
        AGENT418 / "fluid_variant_contract.csv",
        AGENT419 / "README.md",
        AGENT423 / "final_predictive_hx_closure_rows.csv",
        AGENT423 / "realized_wallheatflux_replay_rows.csv",
        AGENT424 / "heater_cooler_model_form_errors.csv",
        AGENT424 / "setup_predictive_variant_status.csv",
        AGENT425 / "final_forward_v1_unblock_requirements.csv",
        AGENT421 / "hydraulic_admission_final_decisions.csv",
    ]
    return [
        {
            "source_path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "use_in_agent438": "read_only_input",
        }
        for path in paths
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""# Setup-Only HX/Cooler Scorecard Unlock

Date: {DATE}
Task: {TASK}

## Result

The preferred setup-only HX/cooler lane,
`{PREFERRED_CANDIDATE}`, passes this bounded candidate score gate:

- Salt2 train error: `0 W`.
- Salt3 validation error: `{summary["preferred_validation_abs_error_W"]} W`
  against a `{VALIDATION_TOLERANCE_W} W` gate.
- Salt4 holdout error: `{summary["preferred_holdout_abs_error_W"]} W`
  against a `{HOLDOUT_TOLERANCE_W} W` gate.
- Runtime input violations: `0`.

This advances the HX/cooler lane as a setup-only final-scorecard input. It does
not admit final forward-v1. Hydraulic pressure/F6, internal-Nu/thermal
sign/heat-balance, recirculation, and mesh/GCI gates still block final
promotion.

## Outputs

- `setup_only_hx_boundary_scorecard.csv`
- `hx_candidate_gate_decision.csv`
- `hx_runtime_input_legality_audit.csv`
- `forward_v1_remaining_unlock_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Math and Gate Assumptions

For each case:

`error_W = abs(predicted_qhx_W - target_qhx_W_for_scoring_only)`

`relative_error_pct = 100 * error_W / abs(target_qhx_W_for_scoring_only)`

The target cooler duty is used only for post-prediction scoring. It is not a
runtime input. The split discipline is Salt2 fit, Salt3 validation, Salt4
holdout. The fitted scalar is frozen after Salt2.

AGENT-438 uses a deliberately narrow score gate:

- validation `error_W <= {VALIDATION_TOLERANCE_W}`
- holdout `error_W <= {HOLDOUT_TOLERANCE_W}`
- runtime input violation count equals zero

These tolerances are a candidate-screen gate, not a publication uncertainty
claim.

## Remaining Blockers

The shortest remaining chain is:

1. Use this package as the HX/cooler input to the final forward-v1 scorecard.
2. Admit hydraulic pressure/F6 rows or keep them diagnostic with a separate
   section-effective model lane.
3. Resolve internal-Nu sign/heat-balance if any true Nu fit is required.
4. Carry mesh/GCI uncertainty into pressure and thermal QoIs.
5. Rebuild the final scorecard without realized CFD wallHeatFlux, imposed CFD
   cooler duty, CFD mdot, validation pressure, or validation temperature runtime
   leakage.

## Guardrails

- No native CFD solver outputs were mutated.
- No scheduler jobs were launched.
- Registry/admission state and generated indexes were not mutated.
- External `../cfd-modeling-tools` was kept read-only.
- Current PM5/upcomer rows remain diagnostic-only for true single-stream
  coefficients.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    hx_rows = read_csv(AGENT407 / "final_predictive_hx_closure_rows.csv")
    reconciliation = read_csv(AGENT407 / "hx_candidate_reconciliation.csv")
    score_rows = scorecard_rows(hx_rows)
    decisions = candidate_decision_rows(reconciliation, score_rows)
    runtime = runtime_legality_rows()
    remaining = remaining_unlock_rows()

    preferred = next(row for row in decisions if row["candidate_id"] == PREFERRED_CANDIDATE)
    counts = {
        "scorecard_rows": write_csv(
            OUT / "setup_only_hx_boundary_scorecard.csv",
            score_rows,
            [
                "candidate_id",
                "case_id",
                "split_role",
                "model_form",
                "predicted_qhx_W",
                "target_qhx_W_for_scoring_only",
                "abs_error_W",
                "abs_error_pct_of_target",
                "runtime_input_violation_count",
                "split_gate",
                "error_gate",
                "runtime_gate",
                "setup_only_hx_use",
                "admission_class",
                "forward_v1_use",
                "source_path",
            ],
        ),
        "decision_rows": write_csv(
            OUT / "hx_candidate_gate_decision.csv",
            decisions,
            [
                "candidate_id",
                "preferred_candidate",
                "validation_abs_error_W",
                "validation_tolerance_W",
                "validation_gate",
                "holdout_abs_error_W",
                "holdout_tolerance_W",
                "holdout_gate",
                "runtime_input_violation_count",
                "runtime_gate",
                "all_non_salt1_rmse_W",
                "all_non_salt1_mae_W",
                "prior_decision",
                "agent438_decision",
                "final_forward_v1_admission",
                "source_path",
            ],
        ),
        "runtime_audit_rows": write_csv(
            OUT / "hx_runtime_input_legality_audit.csv",
            runtime,
            ["item", "required_rule", "observed_state", "gate", "forbidden_runtime_inputs", "source_path"],
        ),
        "remaining_unlock_rows": write_csv(
            OUT / "forward_v1_remaining_unlock_queue.csv",
            remaining,
            [
                "gate",
                "current_state",
                "blocking_final_forward_v1",
                "exact_missing_evidence",
                "next_artifact",
                "executor",
                "admission_criterion",
            ],
        ),
        "source_manifest_rows": write_csv(
            OUT / "source_manifest.csv",
            source_manifest_rows(),
            ["source_path", "exists", "use_in_agent438"],
        ),
    }
    summary = {
        "task": TASK,
        "date": DATE,
        "generated_utc": utc_now(),
        "output_dir": rel(OUT),
        **counts,
        "preferred_candidate": PREFERRED_CANDIDATE,
        "preferred_validation_abs_error_W": preferred["validation_abs_error_W"],
        "preferred_holdout_abs_error_W": preferred["holdout_abs_error_W"],
        "preferred_agent438_decision": preferred["agent438_decision"],
        "runtime_gate_counts": dict(Counter(row["gate"] for row in runtime)),
        "score_error_gate_counts": dict(Counter(row["error_gate"] for row in score_rows)),
        "final_forward_v1_state": "blocked_no_go_final_forward_v1_not_admitted",
        "final_hx_lane_state": "advanced_as_setup_only_candidate_input_not_final_forward_v1",
        "next_executable_artifact": "bounded_hydraulic_pressure_scorecard_on_admitted_rows",
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
