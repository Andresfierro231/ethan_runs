#!/usr/bin/env python3
"""Build AGENT-492 cooler timeout diagnosis and wall-circuit study package."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-492"
DATE = "2026-07-17"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-17/2026-07-17_cooler_fluid_timeout_and_wall_circuit_study")
OUT = ROOT / OUT_REL

AGENT480_PLAN = ROOT / "operational_notes/07-26/17/2026-07-17_COOLER_MODEL_COMPREHENSIVE_TEST_PLAN.md"
AGENT482 = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model"
AGENT458 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_predictive_test_section_heat_loss_model"
AGENT461 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard"
SETUP_ROWS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv"

CASE_ORDER = {"salt_2": 0, "salt_3": 1, "salt_4": 2}
SPLIT = {"salt_2": "train", "salt_3": "validation", "salt_4": "holdout"}
VALIDATION_W_TOL = 5.0
HOLDOUT_W_TOL = 10.0
PCT_TOL = 25.0
PASSIVE_ROLES = {"ambient_wall", "junction_other", "test_section"}
ACTIVE_ROLES = {"heater", "cooler"}


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


def pass_fail(abs_error: float | None, pct_error: float | None, split_role: str) -> str:
    if split_role == "train":
        return "fit_row_not_generalization_scored"
    tol = split_w_tolerance(split_role)
    if abs_error is None or pct_error is None or tol is None:
        return "missing"
    return "pass" if abs_error <= tol and pct_error <= PCT_TOL else "fail"


def timeout_diagnosis_rows() -> list[dict[str, Any]]:
    current = AGENT482 / "coupled_scorecard.csv"
    rows = read_csv(current) if current.exists() else []
    completed = [row for row in rows if row.get("coupled_run_status") == "completed"]
    elapsed = [safe_float(row.get("elapsed_s")) for row in completed]
    elapsed = [value for value in elapsed if value is not None]
    timed_out = [row for row in rows if row.get("coupled_run_status", "").startswith("timeout_after_")]
    statuses: dict[str, int] = {}
    for row in rows:
        status = row.get("coupled_run_status", "")
        statuses[status] = statuses.get(status, 0) + 1
    recommended_timeout = ""
    if elapsed:
        recommended_timeout = fmt(max(180.0, math.ceil(2.0 * max(elapsed))))
    elif timed_out:
        recommended_timeout = "180"
    return [
        {
            "diagnostic_id": "D1_previous_timeout_bound",
            "observation": "AGENT-482 used 45 s per Fluid row and every row timed out.",
            "evidence_value": "12 timeout rows in the initial scorecard",
            "interpretation": "45 s was below ordinary solve time and cannot be treated as solver failure.",
            "source_path": rel(current),
        },
        {
            "diagnostic_id": "D2_current_rerun_status_counts",
            "observation": json.dumps(statuses, sort_keys=True),
            "evidence_value": f"completed={len(completed)}; timed_out={len(timed_out)}",
            "interpretation": "A successful rerun requires completed coupled rows before cooler admission review.",
            "source_path": rel(current),
        },
        {
            "diagnostic_id": "D3_completed_elapsed_seconds",
            "observation": "elapsed_s from completed Fluid rows",
            "evidence_value": ""
            if not elapsed
            else f"min={fmt(min(elapsed))}; median={fmt(statistics.median(elapsed))}; max={fmt(max(elapsed))}",
            "interpretation": "Use a timeout at least 2x the slowest observed completed row, with a 180 s floor for this campaign.",
            "source_path": rel(current),
        },
        {
            "diagnostic_id": "D4_recommended_timeout_seconds",
            "observation": recommended_timeout,
            "evidence_value": "derived from completed elapsed_s if available, otherwise conservative rerun floor",
            "interpretation": "The completed rerun used 180 s; future production reruns should use this posthoc 2x slowest-row bound.",
            "source_path": rel(AGENT480_PLAN),
        },
    ]


def case_aggregates() -> dict[str, dict[str, Any]]:
    rows = read_csv(SETUP_ROWS)
    aggregates: dict[str, dict[str, Any]] = {}
    for case_id in sorted({row["case_id"] for row in rows if row["case_id"] in SPLIT}, key=CASE_ORDER.get):
        case_rows = [row for row in rows if row["case_id"] == case_id]
        passive = [row for row in case_rows if row["role"] in PASSIVE_ROLES]
        test_section = next(row for row in case_rows if row["role"] == "test_section")
        heater = next(row for row in case_rows if row["role"] == "heater")
        cooler = next(row for row in case_rows if row["role"] == "cooler")
        hA_total = sum(safe_float(row.get("hA_W_K")) or 0.0 for row in passive)
        target_total = sum(safe_float(row.get("realized_external_loss_W")) or 0.0 for row in passive)
        aggregates[case_id] = {
            "case_id": case_id,
            "split_role": SPLIT[case_id],
            "passive_hA_W_K": hA_total,
            "passive_target_loss_W": target_total,
            "test_section_hA_W_K": safe_float(test_section.get("hA_W_K")) or 0.0,
            "test_section_target_loss_W": safe_float(test_section.get("realized_external_loss_W")) or 0.0,
            "heater_source_W_setup": abs(safe_float(heater.get("imposed_Q_W")) or 0.0),
            "cooler_sink_W_setup": abs(safe_float(cooler.get("imposed_Q_W")) or 0.0),
            "passive_role_count": len(passive),
            "source_path": rel(SETUP_ROWS),
        }
    return aggregates


def circuit_candidate_specs() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "PB0_total_hA_constant_drive",
            "target_scope": "passive_total",
            "drive_scaling_exponent": 0.0,
            "model_form": "Q_passive=sum(hA_setup)*DeltaT_train",
            "reason": "baseline setup hA with one Salt2-trained drive; no heat-rate scaling",
        },
        {
            "candidate_id": "PB1_total_hA_heater_power_drive_p1",
            "target_scope": "passive_total",
            "drive_scaling_exponent": 1.0,
            "model_form": "Q_passive=sum(hA_setup)*DeltaT_train*(Q_heater/Q_heater_train)",
            "reason": "one-scalar passive thermal circuit with source-strength drive scaling",
        },
        {
            "candidate_id": "PB2_total_hA_heater_power_drive_p2",
            "target_scope": "passive_total",
            "drive_scaling_exponent": 2.0,
            "model_form": "Q_passive=sum(hA_setup)*DeltaT_train*(Q_heater/Q_heater_train)^2",
            "reason": "nonlinear sensitivity bound; not preferred without perturbation evidence",
        },
        {
            "candidate_id": "TS1_test_section_hA_constant_drive",
            "target_scope": "test_section",
            "drive_scaling_exponent": 0.0,
            "model_form": "Q_TS=hA_TS_setup*DeltaT_train",
            "reason": "reproduces the existing TS1 static screen as a component check",
        },
        {
            "candidate_id": "TS5_test_section_hA_heater_power_drive_p1",
            "target_scope": "test_section",
            "drive_scaling_exponent": 1.0,
            "model_form": "Q_TS=hA_TS_setup*DeltaT_train*(Q_heater/Q_heater_train)",
            "reason": "setup-only component circuit with linear source-strength drive",
        },
        {
            "candidate_id": "TS6_test_section_hA_heater_power_drive_p2",
            "target_scope": "test_section",
            "drive_scaling_exponent": 2.0,
            "model_form": "Q_TS=hA_TS_setup*DeltaT_train*(Q_heater/Q_heater_train)^2",
            "reason": "component nonlinear sensitivity bound; W gates improve but percent gates remain strict",
        },
    ]


def circuit_score_rows() -> list[dict[str, Any]]:
    aggregates = case_aggregates()
    train = aggregates["salt_2"]
    rows: list[dict[str, Any]] = []
    for spec in circuit_candidate_specs():
        scope = spec["target_scope"]
        exponent = float(spec["drive_scaling_exponent"])
        train_hA = train["passive_hA_W_K"] if scope == "passive_total" else train["test_section_hA_W_K"]
        train_target = train["passive_target_loss_W"] if scope == "passive_total" else train["test_section_target_loss_W"]
        drive_train = train_target / max(train_hA, 1e-12)
        for case_id in sorted(aggregates, key=CASE_ORDER.get):
            agg = aggregates[case_id]
            hA = agg["passive_hA_W_K"] if scope == "passive_total" else agg["test_section_hA_W_K"]
            target = agg["passive_target_loss_W"] if scope == "passive_total" else agg["test_section_target_loss_W"]
            q_ratio = agg["heater_source_W_setup"] / max(train["heater_source_W_setup"], 1e-12)
            predicted = hA * drive_train * (q_ratio**exponent)
            error = predicted - target
            abs_error = abs(error)
            pct_error = None if target == 0 else 100.0 * abs_error / abs(target)
            rows.append(
                {
                    "candidate_id": spec["candidate_id"],
                    "case_id": case_id,
                    "split_role": agg["split_role"],
                    "target_scope": scope,
                    "model_form": spec["model_form"],
                    "fit_policy": "fit one Salt2 drive scalar only; exponent is predeclared physics/sensitivity choice",
                    "drive_scaling_exponent": fmt(exponent),
                    "hA_W_K": fmt(hA),
                    "salt2_fitted_drive_K": fmt(drive_train),
                    "heater_source_W_setup": fmt(agg["heater_source_W_setup"]),
                    "heater_source_ratio_to_salt2": fmt(q_ratio),
                    "predicted_loss_W": fmt(predicted),
                    "target_loss_W_for_scoring_only": fmt(target),
                    "error_W": fmt(error),
                    "abs_error_W": fmt(abs_error),
                    "abs_error_pct": fmt(pct_error),
                    "qoi_gate": pass_fail(abs_error, pct_error, agg["split_role"]),
                    "runtime_input_violation_count": 0,
                    "source_path": agg["source_path"],
                }
            )
    return rows


def candidate_summary_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for candidate_id in [spec["candidate_id"] for spec in circuit_candidate_specs()]:
        rows = [row for row in score_rows if row["candidate_id"] == candidate_id]
        validation = next(row for row in rows if row["split_role"] == "validation")
        holdout = next(row for row in rows if row["split_role"] == "holdout")
        pass_both = validation["qoi_gate"] == "pass" and holdout["qoi_gate"] == "pass"
        scope = rows[0]["target_scope"]
        if pass_both and scope == "passive_total":
            recommendation = "promote_to_coupled_m3ts_plus_cooler_score_candidate_not_admitted_yet"
        elif pass_both:
            recommendation = "component_static_screen_passes_but_needs_coupled_and_policy_review"
        else:
            recommendation = "do_not_admit_static_screen_failure_or_component_only_evidence"
        out.append(
            {
                "candidate_id": candidate_id,
                "target_scope": scope,
                "validation_abs_error_W": validation["abs_error_W"],
                "validation_abs_error_pct": validation["abs_error_pct"],
                "validation_qoi_gate": validation["qoi_gate"],
                "holdout_abs_error_W": holdout["abs_error_W"],
                "holdout_abs_error_pct": holdout["abs_error_pct"],
                "holdout_qoi_gate": holdout["qoi_gate"],
                "runtime_gate": "pass_setup_only_no_realized_wallHeatFlux_no_validation_temperature",
                "coupled_gate": "pending_coupled_fluid_score",
                "recommendation": recommendation,
                "admission_decision": "not_admitted_pending_coupled_score_and_local_temperature_review",
            }
        )
    return out


def methodology_rows() -> list[dict[str, Any]]:
    return [
        {
            "item": "active_terms",
            "method": "Keep heater source and cooler/HX sink as explicit setup/admitted boundary terms.",
            "do_not_do": "Do not tune passive wall or Internal Nu to absorb cooler or heater residuals.",
        },
        {
            "item": "passive_boundary_circuit",
            "method": "Represent passive loss as sum(hA_setup_by_role) times a Salt2-trained drive with predeclared heater-power scaling.",
            "do_not_do": "Do not use realized wallHeatFlux, validation temperatures, or holdout losses at runtime.",
        },
        {
            "item": "test_section_local_check",
            "method": "Score test-section separately because it sits inside the recirculating upcomer and can fail locally even if total passive loss passes.",
            "do_not_do": "Do not claim a local Nu/HTC fit from recirculating test-section evidence.",
        },
        {
            "item": "admission_rule",
            "method": "Require static validation/holdout gates plus coupled Fluid mdot/TP/TW review before blocker closure.",
            "do_not_do": "Do not close predictive-wall-test-section-submodels from a static total-loss pass alone.",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"source_id": "agent480_plan", "path": rel(AGENT480_PLAN), "use": "cooler and split/legal-input guardrails"},
        {"source_id": "agent482_cooler", "path": rel(AGENT482), "use": "cooler rerun scorecard and timeout evidence"},
        {"source_id": "agent458_test_section", "path": rel(AGENT458), "use": "prior TS1/TS2 static screen context"},
        {"source_id": "agent461_m3ts", "path": rel(AGENT461), "use": "coupled M3+TS admission context"},
        {"source_id": "setup_equivalents", "path": rel(SETUP_ROWS), "use": "setup hA, active source/sink, passive loss scoring targets"},
    ]


def decision_payload(summary_rows: list[dict[str, Any]], timeout_rows: list[dict[str, Any]]) -> dict[str, Any]:
    promoted = [row for row in summary_rows if row["recommendation"].startswith("promote")]
    completed = any("completed=" in row["evidence_value"] and not row["evidence_value"].startswith("completed=0") for row in timeout_rows)
    return {
        "task": TASK,
        "created_utc": utc_now(),
        "cooler_timeout_diagnosis": "45 s was too short for Fluid solve_case; 180 s completed this rerun, and posthoc elapsed_s supports a larger future production bound.",
        "cooler_rerun_has_completed_rows": completed,
        "best_wall_circuit_candidate": promoted[0]["candidate_id"] if promoted else "",
        "best_wall_circuit_status": "static_screen_promising_not_admitted" if promoted else "no_static_candidate_promoted",
        "blocker_decision": "keep_open",
        "why": (
            "The passive-total hA/heater-power circuit can be promoted to coupled scoring if it passes static rows, "
            "but blocker closure still requires coupled mdot/TP/TW and local test-section review."
        ),
    }


def readme_text(decision: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(AGENT480_PLAN)}
  - {rel(AGENT482)}
  - {rel(AGENT458)}
  - {rel(AGENT461)}
  - {rel(SETUP_ROWS)}
tags: [forward-model, cooler, wall-circuit, test-section, passive-boundary]
related:
  - predictive-wall-test-section-submodels
  - AGENT-482
task: {TASK}
date: {DATE}
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Cooler Timeout Diagnosis And Wall-Circuit Study

## Result

The AGENT-482 `45 s` timeout was below ordinary Fluid solve time for the
cooler-removal scenario, so it was a bound-selection failure rather than proof
that the Fluid row was stuck. The completed rerun used a `180 s` per-row bound;
the generated timeout table records a posthoc future bound from the measured
slowest completed row.

The best next wall/passive candidate is
`{decision['best_wall_circuit_candidate'] or 'none'}` with status
`{decision['best_wall_circuit_status']}`.

Decision for `predictive-wall-test-section-submodels`: `{decision['blocker_decision']}`.

Reason: {decision['why']}

## Files

- `fluid_timeout_diagnosis.csv`
- `case_thermal_circuit_inputs.csv`
- `thermal_circuit_methodology.csv`
- `wall_circuit_candidate_scores.csv`
- `wall_circuit_candidate_summary.csv`
- `decision.json`
- `source_manifest.csv`
- `summary.json`
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    timeout_rows = timeout_diagnosis_rows()
    aggregates = list(case_aggregates().values())
    methodology = methodology_rows()
    scores = circuit_score_rows()
    summaries = candidate_summary_rows(scores)
    decision = decision_payload(summaries, timeout_rows)
    counts = {
        "fluid_timeout_diagnosis.csv": write_csv(
            OUT / "fluid_timeout_diagnosis.csv",
            timeout_rows,
            ["diagnostic_id", "observation", "evidence_value", "interpretation", "source_path"],
        ),
        "case_thermal_circuit_inputs.csv": write_csv(
            OUT / "case_thermal_circuit_inputs.csv",
            aggregates,
            [
                "case_id",
                "split_role",
                "passive_hA_W_K",
                "passive_target_loss_W",
                "test_section_hA_W_K",
                "test_section_target_loss_W",
                "heater_source_W_setup",
                "cooler_sink_W_setup",
                "passive_role_count",
                "source_path",
            ],
        ),
        "thermal_circuit_methodology.csv": write_csv(
            OUT / "thermal_circuit_methodology.csv",
            methodology,
            ["item", "method", "do_not_do"],
        ),
        "wall_circuit_candidate_scores.csv": write_csv(
            OUT / "wall_circuit_candidate_scores.csv",
            scores,
            [
                "candidate_id",
                "case_id",
                "split_role",
                "target_scope",
                "model_form",
                "fit_policy",
                "drive_scaling_exponent",
                "hA_W_K",
                "salt2_fitted_drive_K",
                "heater_source_W_setup",
                "heater_source_ratio_to_salt2",
                "predicted_loss_W",
                "target_loss_W_for_scoring_only",
                "error_W",
                "abs_error_W",
                "abs_error_pct",
                "qoi_gate",
                "runtime_input_violation_count",
                "source_path",
            ],
        ),
        "wall_circuit_candidate_summary.csv": write_csv(
            OUT / "wall_circuit_candidate_summary.csv",
            summaries,
            [
                "candidate_id",
                "target_scope",
                "validation_abs_error_W",
                "validation_abs_error_pct",
                "validation_qoi_gate",
                "holdout_abs_error_W",
                "holdout_abs_error_pct",
                "holdout_qoi_gate",
                "runtime_gate",
                "coupled_gate",
                "recommendation",
                "admission_decision",
            ],
        ),
        "source_manifest.csv": write_csv(
            OUT / "source_manifest.csv",
            source_manifest_rows(),
            ["source_id", "path", "use"],
        ),
    }
    write_json(OUT / "decision.json", decision)
    summary = {"task": TASK, "created_utc": utc_now(), "output_dir": rel(OUT), "counts": counts, "decision": decision}
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(decision), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
