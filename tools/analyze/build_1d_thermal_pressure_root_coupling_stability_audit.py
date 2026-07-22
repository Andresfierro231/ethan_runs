#!/usr/bin/env python3
"""Build a dry stability audit for coupled 1D thermal/pressure root solving."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-1D-THERMAL-PRESSURE-ROOT-COUPLING-STABILITY-AUDIT-2026-07-22"
OUTDIR = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_thermal_pressure_root_coupling_stability_audit")

SETUP_UQ = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation")
MF02 = Path("work_products/2026-07/2026-07-22/2026-07-22_mf02_pressure_mdot_coupling_diagnostic")
PRESSURE = Path("work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet")
HIERARCHY = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_model_hierarchy_ablation_ladder_packet")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build(outdir: Path = OUTDIR) -> dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)
    sensitivity = read_csv(SETUP_UQ / "lightweight_sensitivity_matrix.csv")
    mdot_coupling = read_csv(MF02 / "mdot_sensitivity_coupling_estimate.csv")
    f3_f6 = read_csv(MF02 / "f3_f6_prerequisite_table.csv")

    root_rows = [
        {
            "root_component": "loop_mdot_pressure_balance",
            "expected_monotonicity": "pressure_drop_increases_with_abs_mdot",
            "current_evidence": "setup pressure_loss_terms and fluid_property_mode are high mdot effect; F6 ordinary basis not admitted",
            "bracket_requirement": "residual sign change over positive mdot bracket with finite density/viscosity/property calls",
            "current_status": "requires_train_only_smoke",
            "admission_or_score_allowed": "no",
        },
        {
            "root_component": "thermal_state_update",
            "expected_monotonicity": "higher heater fraction raises local TP/TW; stronger cooler lowers top-loop temperatures and changes mdot",
            "current_evidence": "heater_source_fraction and cooler_hx_strength are high TP pathways",
            "bracket_requirement": "finite segment enthalpy and wall-state projections for every train row",
            "current_status": "requires_train_only_smoke",
            "admission_or_score_allowed": "no",
        },
        {
            "root_component": "pressure_thermal_coupling",
            "expected_monotonicity": "temperature/property changes perturb mdot without sign-flip oscillation",
            "current_evidence": "fluid_property_mode and pressure_loss_terms both rank high for mdot",
            "bracket_requirement": "fixed-point or nested-root iteration decreases residual norm under one-at-a-time perturbations",
            "current_status": "not_executed_dry_audit_only",
            "admission_or_score_allowed": "no",
        },
        {
            "root_component": "sensor_projection_score_layer",
            "expected_monotonicity": "projection maps finite bulk/wall states to finite TP/TW residuals",
            "current_evidence": "projection operator exists but runtime temperature release is forbidden",
            "bracket_requirement": "projection cannot feed observed TP/TW back into runtime solve",
            "current_status": "measurement_layer_ready_score_only",
            "admission_or_score_allowed": "no",
        },
    ]
    write_csv(outdir / "root_monotonicity_bracketing_audit.csv", root_rows)

    risk_rows = []
    for row in sensitivity:
        mdot_rank = row["mdot_effect_rank"]
        tp_rank = row["tp_effect_rank"]
        tw_rank = row["tw_effect_rank"]
        high_count = sum(rank == "high" for rank in [mdot_rank, tp_rank, tw_rank])
        risk = "high" if high_count >= 2 or mdot_rank == "high" else "medium" if "medium" in mdot_rank + tp_rank + tw_rank else "low"
        risk_rows.append(
            {
                "input_family": row["input_family"],
                "mdot_effect_rank": mdot_rank,
                "tp_effect_rank": tp_rank,
                "tw_effect_rank": tw_rank,
                "dominant_pathway": row["dominant_pathway"],
                "coupled_root_risk": risk,
                "recommended_smoke": "one_at_a_time_train_only_finite_root_and_finite_QOI",
                "admission_or_score_allowed": "no",
            }
        )
    write_csv(outdir / "coupled_sensitivity_risk_matrix.csv", risk_rows)

    failure_rows = [
        {
            "failure_mode": "no_pressure_root_bracket",
            "trigger": "pressure residual has no sign change over legal mdot bracket",
            "likely_causes": "invalid pressure-loss basis; property mode discontinuity; forbidden F6 term",
            "required_response": "fail closed and report bracket endpoints; do not fit multiplier",
        },
        {
            "failure_mode": "thermal_pressure_iteration_oscillation",
            "trigger": "nested thermal/pressure residual grows or flips sign repeatedly",
            "likely_causes": "cooler UA and pressure loss interaction; property-temperature coupling",
            "required_response": "add damping/safeguarded iteration smoke before any scoring",
        },
        {
            "failure_mode": "nonfinite_projection",
            "trigger": "bulk/wall state maps to NaN/Inf TP/TW or excluded TW10 shell state",
            "likely_causes": "missing segment state; missing active-HX wall/shell state",
            "required_response": "exclude affected score row or add legal state, never observed-temperature runtime feedback",
        },
        {
            "failure_mode": "ordinary_closure_leakage",
            "trigger": "recirculating section-effective K/F6 used as ordinary pipe term",
            "likely_causes": "large local apparent K_eff misread as mdot sensitivity",
            "required_response": "block admission until low-recirculation anchors and same-QOI UQ exist",
        },
        {
            "failure_mode": "source_property_leakage",
            "trigger": "realized Qwall/total_Q/CFD mdot used as runtime source/property input",
            "likely_causes": "diagnostic thermal residual absorbed into source release",
            "required_response": "fail runtime legality audit; create separate source/property release row",
        },
    ]
    write_csv(outdir / "root_failure_mode_table.csv", failure_rows)

    smoke_rows = [
        {
            "smoke_id": "SMOKE-ROOT-01",
            "scope": "train_rows_only",
            "check": "positive mdot bracket has finite pressure residual endpoints and at least one sign change",
            "pass_condition": "finite bracket, deterministic root, no protected-row access",
        },
        {
            "smoke_id": "SMOKE-ROOT-02",
            "scope": "train_rows_only",
            "check": "one-at-a-time setup perturbations keep mdot finite and sign-consistent",
            "pass_condition": "no NaN/Inf, no negative-flow branch switch unless explicitly modeled",
        },
        {
            "smoke_id": "SMOKE-ROOT-03",
            "scope": "train_rows_only",
            "check": "heater/cooler/external-loss perturbations keep TP/TW projections finite",
            "pass_condition": "finite projected TP/TW; excluded sensors remain excluded",
        },
        {
            "smoke_id": "SMOKE-ROOT-04",
            "scope": "train_rows_only",
            "check": "runtime input manifest contains no realized CFD mdot, wallHeatFlux, total_Q, validation TP/TW, or protected score rows",
            "pass_condition": "runtime legality audit passes before any candidate freeze",
        },
        {
            "smoke_id": "SMOKE-ROOT-05",
            "scope": "train_rows_only",
            "check": "F6/component-K terms are disabled unless an admitted low-recirculation row exists",
            "pass_condition": "ordinary-flow prerequisite table remains enforced",
        },
    ]
    write_csv(outdir / "fluid_smoke_test_recommendations.csv", smoke_rows)

    source_rows = [
        {"path": str(SETUP_UQ / "lightweight_sensitivity_matrix.csv"), "role": "setup-only sensitivity ranks", "read_only": "yes"},
        {"path": str(SETUP_UQ / "propagation_plan.csv"), "role": "protected propagation sequence", "read_only": "yes"},
        {"path": str(MF02 / "mdot_sensitivity_coupling_estimate.csv"), "role": "pressure residual mdot scale warning", "read_only": "yes"},
        {"path": str(MF02 / "f3_f6_prerequisite_table.csv"), "role": "F3/F6 ordinary-flow blockers", "read_only": "yes"},
        {"path": str(PRESSURE / "summary.json"), "role": "pressure basis non-admission status", "read_only": "yes"},
        {"path": str(HIERARCHY / "model_hierarchy_ladder.csv"), "role": "hierarchy/freeze context", "read_only": "yes"},
    ]
    write_csv(outdir / "source_manifest.csv", source_rows)

    guardrails = [
        {"guardrail": "native_output_mutation", "status": "none"},
        {"guardrail": "registry_or_admission_mutation", "status": "none"},
        {"guardrail": "scheduler_or_solver_launch", "status": "none"},
        {"guardrail": "fluid_or_external_edit", "status": "none"},
        {"guardrail": "fit_or_model_selection", "status": "none"},
        {"guardrail": "protected_scoring", "status": "none"},
        {"guardrail": "source_property_release", "status": "none"},
        {"guardrail": "candidate_freeze", "status": "none"},
    ]
    write_csv(outdir / "no_mutation_guardrails.csv", guardrails)

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "root_coupling_stability_audit_ready_dry_no_compute",
        "root_audit_rows": len(root_rows),
        "sensitivity_risk_rows": len(risk_rows),
        "high_coupled_root_risk_rows": sum(1 for row in risk_rows if row["coupled_root_risk"] == "high"),
        "failure_mode_rows": len(failure_rows),
        "fluid_smoke_test_rows": len(smoke_rows),
        "f3_f6_prerequisite_fail_rows": sum(1 for row in f3_f6 if row.get("current_status") == "fail"),
        "fit_or_model_selection": False,
        "protected_scoring": False,
        "source_property_release": False,
        "candidate_freeze": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
    }
    write_json(outdir / "summary.json", summary)

    readme = f"""# 1D Thermal/Pressure Root Coupling Stability Audit

Decision: `{summary['decision']}`.

This is a dry audit. It does not execute Fluid, run a solver, fit parameters,
score protected rows, or release source/property inputs.

## Main Findings

- The highest coupled-root risk families are cooler/HX strength, fluid property
  mode, pressure-loss terms, heater/source fraction, external convection, and
  sensor projection.
- Pressure/F6 terms remain blocked by ordinary-flow and same-QOI UQ gates.
- The next implementation step is train-only smoke testing: finite brackets,
  finite roots, finite TP/TW projections, and runtime-legality checks.
"""
    (outdir / "README.md").write_text(readme, encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTDIR)
    args = parser.parse_args(argv)
    summary = build(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
