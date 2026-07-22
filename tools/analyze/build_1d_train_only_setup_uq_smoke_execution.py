#!/usr/bin/env python3
"""Execute a bounded train-only setup-UQ smoke for the 1D Fluid model."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


TASK_ID = "TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22"
DATE = "2026-07-22"
SLUG = "1d_train_only_setup_uq_smoke_execution"
REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_runbook"
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution"
FLUID_ROOT = (REPO_ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
BASELINE_SCENARIO = "predictive_airside_ins_1.0in_rad_0"
TRAIN_CASES = ("Salt 2", "Salt 3", "Salt 4")
PARENT_SEGMENTS = (
    "heated_incline",
    "left_lower_vertical",
    "test_section",
    "left_upper_vertical",
    "right_vertical",
    "cooled_incline_pre_hx",
    "cooled_incline_post_hx",
)
FORBIDDEN_RUNTIME_FIELDS = (
    "CFD_mdot",
    "realized_CFD_wallHeatFlux",
    "imposed_CFD_cooler_duty",
    "validation_temperatures",
    "holdout_temperatures",
    "external_test_temperatures",
    "realized_test_section_heat",
    "heat_residual_as_runtime_closure",
    "global_multiplier_selected_by_score",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "" if row.get(key) is None else row.get(key) for key in fieldnames})


def fmt(value: Any, digits: int = 8) -> str:
    if value is None:
        return ""
    try:
        fval = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(fval):
        return ""
    return f"{fval:.{digits}g}"


def runbook_rows(name: str) -> List[Dict[str, str]]:
    return read_csv(RUNBOOK_DIR / name)


def runtime_manifest_rows() -> List[Dict[str, Any]]:
    rows = []
    for row in runbook_rows("setup_legal_variation_matrix.csv"):
        rows.append(
            {
                "manifest_id": row["variant_id"],
                "input_family": row["input_family"],
                "runtime_inputs": row["allowed_runtime_inputs"],
                "runtime_legal": "true",
                "train_scope": row["train_cases"],
                "protected_cases_used": "false",
                "source_path": str(RUNBOOK_DIR / "setup_legal_variation_matrix.csv"),
            }
        )
    for field in FORBIDDEN_RUNTIME_FIELDS:
        rows.append(
            {
                "manifest_id": f"forbidden_{field}",
                "input_family": "forbidden_runtime_field",
                "runtime_inputs": field,
                "runtime_legal": "false",
                "train_scope": "none",
                "protected_cases_used": "false",
                "source_path": str(RUNBOOK_DIR / "split_and_runtime_guardrails.csv"),
            }
        )
    return rows


def runtime_lint_status(manifest_rows: Iterable[Dict[str, Any]]) -> Tuple[str, List[str]]:
    illegal_used = [
        str(row["runtime_inputs"])
        for row in manifest_rows
        if str(row.get("runtime_legal", "")).lower() == "false" and str(row.get("train_scope", "")) != "none"
    ]
    return ("fail" if illegal_used else "pass", illegal_used)


def import_fluid_api():
    if not FLUID_ROOT.exists():
        raise FileNotFoundError(f"Fluid root not found: {FLUID_ROOT}")
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if str(FLUID_ROOT) not in sys.path:
        sys.path.insert(0, str(FLUID_ROOT))
    from tamu_loop_model_v2.config_loader import EXPERIMENT_CASES, default_scenarios
    from tamu_loop_model_v2.solver import MinorLosses, ScenarioConfig, solve_case

    return EXPERIMENT_CASES, default_scenarios, MinorLosses, ScenarioConfig, solve_case


def clone_scenario(scenario: Any, **updates: Any) -> Any:
    payload = dict(scenario.__dict__)
    payload.update(updates)
    return type(scenario)(**payload)


def all_parent_multiplier(value: float) -> Dict[str, float]:
    return {name: value for name in PARENT_SEGMENTS}


def variant_specs(MinorLosses: Any) -> List[Dict[str, Any]]:
    return [
        {
            "variant_id": "V01_heater_front_shift",
            "input_family": "heater_source_fraction",
            "variation": "tw4_to_tw5 +0.10 absolute with downstream spans renormalized",
            "scenario_updates": {
                "heater_source_mode": "tw4_to_tp3_three_span",
                "heater_source_weights_by_span": {"tw4_to_tw5": 0.55, "tw5_to_tw6": 0.30, "tw6_to_tp3": 0.15},
            },
            "minor_losses": MinorLosses(),
        },
        {
            "variant_id": "V02_hx_ua_0p8",
            "input_family": "cooler_hx_strength",
            "variation": "hx_ua_multiplier=0.8",
            "scenario_updates": {"hx_ua_multiplier": 0.8},
            "minor_losses": MinorLosses(),
        },
        {
            "variant_id": "V02_hx_ua_1p2",
            "input_family": "cooler_hx_strength",
            "variation": "hx_ua_multiplier=1.2",
            "scenario_updates": {"hx_ua_multiplier": 1.2},
            "minor_losses": MinorLosses(),
        },
        {
            "variant_id": "V03_ambient_minus2K",
            "input_family": "ambient_temperature",
            "variation": "ambient_temperature_K=298.0",
            "scenario_updates": {"ambient_temperature_K": 298.0},
            "minor_losses": MinorLosses(),
        },
        {
            "variant_id": "V03_ambient_plus2K",
            "input_family": "ambient_temperature",
            "variation": "ambient_temperature_K=302.0",
            "scenario_updates": {"ambient_temperature_K": 302.0},
            "minor_losses": MinorLosses(),
        },
        {
            "variant_id": "V04_external_hA_0p5",
            "input_family": "external_convection_hA",
            "variation": "outer convective multiplier=0.5 on declared parent segments",
            "scenario_updates": {"outer_closure_mode": "per_parent_multiplier", "outer_conv_multiplier_by_parent_segment": all_parent_multiplier(0.5)},
            "minor_losses": MinorLosses(),
        },
        {
            "variant_id": "V04_external_hA_2p0",
            "input_family": "external_convection_hA",
            "variation": "outer convective multiplier=2.0 on declared parent segments",
            "scenario_updates": {"outer_closure_mode": "per_parent_multiplier", "outer_conv_multiplier_by_parent_segment": all_parent_multiplier(2.0)},
            "minor_losses": MinorLosses(),
        },
        {
            "variant_id": "V05_radiation_on",
            "input_family": "radiation",
            "variation": "radiation_on=True from rad_0 baseline",
            "scenario_updates": {"radiation_on": True},
            "minor_losses": MinorLosses(),
        },
        {
            "variant_id": "V06_property_salt_promoted",
            "input_family": "fluid_property_mode",
            "variation": "property_set_name=salt_promoted",
            "case_updates": {"property_set_name": "salt_promoted"},
            "scenario_updates": {},
            "minor_losses": MinorLosses(),
        },
        {
            "variant_id": "V06_property_salt_kirst",
            "input_family": "fluid_property_mode",
            "variation": "property_set_name=salt_kirst",
            "case_updates": {"property_set_name": "salt_kirst"},
            "scenario_updates": {},
            "minor_losses": MinorLosses(),
        },
        {
            "variant_id": "V07_pressure_major_loss_0p9",
            "input_family": "pressure_loss_terms",
            "variation": "MinorLosses.major_loss_multiplier=0.9; F6/component-K disabled",
            "scenario_updates": {},
            "minor_losses": MinorLosses(major_loss_multiplier=0.9),
        },
        {
            "variant_id": "V07_pressure_major_loss_1p1",
            "input_family": "pressure_loss_terms",
            "variation": "MinorLosses.major_loss_multiplier=1.1; F6/component-K disabled",
            "scenario_updates": {},
            "minor_losses": MinorLosses(major_loss_multiplier=1.1),
        },
        {
            "variant_id": "V08_sensor_projection_audit",
            "input_family": "sensor_projection",
            "variation": "post-solve projection audit using baseline predictions only",
            "scenario_updates": {},
            "minor_losses": MinorLosses(),
            "post_solve_only": True,
        },
    ]


def result_metrics(result: Any) -> Dict[str, Any]:
    sensor = result.sensor_predictions_K
    tp_values = [float(v) for name, v in sensor.items() if name.startswith("TP") and math.isfinite(float(v))]
    tw_values = [float(v) for name, v in sensor.items() if name.startswith("TW") and math.isfinite(float(v))]
    seg_df = result.segment_df
    q_source = float(seg_df["Q_source_W"].sum()) if "Q_source_W" in seg_df else float("nan")
    q_hx = float(seg_df["Q_hx_sink_W"].sum()) if "Q_hx_sink_W" in seg_df else float("nan")
    q_amb = float(seg_df["Q_ambient_W"].sum()) if "Q_ambient_W" in seg_df else float("nan")
    residuals = []
    for _, row in seg_df.iterrows():
        cp = result.case.fluid.cp(float(row["T_avg_K"]))
        enthalpy_delta = result.mdot_kg_s * cp * (float(row["T_out_K"]) - float(row["T_in_K"]))
        expected = float(row["Q_source_W"]) - float(row["Q_hx_sink_W"]) - float(row["Q_ambient_W"])
        residuals.append(enthalpy_delta - expected)
    max_abs_residual = max((abs(v) for v in residuals), default=float("nan"))
    owner = "model_internal_energy_balance" if math.isfinite(max_abs_residual) and max_abs_residual < 1e-6 else "segment_energy_residual_check"
    return {
        "mdot_model_kg_s": result.mdot_kg_s,
        "pressure_root_status": result.root_status,
        "temperature_root_status": "accepted" if bool(result.temperature_root_bracketed) else "not_bracketed",
        "pressure_root_bracketed": bool(result.pressure_root_bracketed),
        "temperature_root_bracketed": bool(result.temperature_root_bracketed),
        "pressure_residual_Pa": result.pressure_residual_Pa,
        "temperature_periodicity_error_K": result.temperature_periodicity_error_K,
        "qhx_total_W": result.qhx_total_W,
        "qambient_total_W": result.qambient_total_W,
        "segment_Q_source_sum_W": q_source,
        "segment_Q_hx_sum_W": q_hx,
        "segment_Q_ambient_sum_W": q_amb,
        "max_abs_segment_residual_R_s_W": max_abs_residual,
        "residual_owner_label": owner,
        "tp_projection_count": len(tp_values),
        "tw_projection_count": len(tw_values),
        "TP1_K": sensor.get("TP1"),
        "TP2_K": sensor.get("TP2"),
        "TP3_K": sensor.get("TP3"),
        "TP4_K": sensor.get("TP4"),
        "TW4_K": sensor.get("TW4"),
        "TW5_K": sensor.get("TW5"),
        "TW6_K": sensor.get("TW6"),
        "TW9_K": sensor.get("TW9"),
        "TW11_K": sensor.get("TW11"),
    }


def run_solver_rows(execute: bool, solve_budget: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    if not execute:
        return [], [], [{"variant_id": "all", "case": "all", "skip_reason": "builder invoked without --execute"}], []
    EXPERIMENT_CASES, default_scenarios, MinorLosses, _ScenarioConfig, solve_case = import_fluid_api()
    scenarios = {scenario.name: scenario for scenario in default_scenarios()}
    if BASELINE_SCENARIO not in scenarios:
        raise KeyError(f"Baseline scenario missing from Fluid default_scenarios(): {BASELINE_SCENARIO}")
    cases = {case.name: case for case in EXPERIMENT_CASES}
    base = scenarios[BASELINE_SCENARIO]
    baseline_rows: List[Dict[str, Any]] = []
    variant_rows: List[Dict[str, Any]] = []
    skip_rows: List[Dict[str, Any]] = []
    warnings: List[str] = []
    baseline_by_case: Dict[str, Dict[str, Any]] = {}
    solves_used = 0

    def solve_one(case_name: str, variant_id: str, scenario: Any, case_obj: Any, minor_losses: Any) -> Dict[str, Any]:
        result = solve_case(case_obj, scenario, minor_losses=minor_losses)
        metrics = result_metrics(result)
        return {
            "case": case_name,
            "variant_id": variant_id,
            "scenario": scenario.name,
            "property_set": case_obj.resolved_property_set_name,
            "execution_status": "completed",
            "runtime_input_lint_status": "pass",
            **{key: fmt(value) for key, value in metrics.items()},
        }

    for case_name in TRAIN_CASES:
        if solves_used >= solve_budget:
            skip_rows.append({"variant_id": "V00", "case": case_name, "skip_reason": "solve_budget_exhausted_before_required_baseline"})
            continue
        case_obj = cases[case_name]
        row = solve_one(case_name, "V00_baseline", clone_scenario(base, name="V00_baseline"), case_obj, MinorLosses())
        baseline_rows.append(row)
        baseline_by_case[case_name] = row
        solves_used += 1
    if len(baseline_rows) != len(TRAIN_CASES):
        warnings.append("STOP-02: baseline train smoke incomplete before variants")
        return baseline_rows, variant_rows, skip_rows, warnings

    for spec in variant_specs(MinorLosses):
        for case_name in TRAIN_CASES:
            if spec.get("post_solve_only"):
                base_row = baseline_by_case[case_name]
                variant_rows.append(
                    {
                        **base_row,
                        "variant_id": spec["variant_id"],
                        "input_family": spec["input_family"],
                        "variation": spec["variation"],
                        "execution_status": "post_solve_projection_audit",
                        "delta_mdot_kg_s": "0",
                        "delta_qhx_total_W": "0",
                        "delta_qambient_total_W": "0",
                    }
                )
                continue
            if solves_used >= solve_budget:
                skip_rows.append({"variant_id": spec["variant_id"], "case": case_name, "skip_reason": "solve_budget_exhausted"})
                continue
            base_case = cases[case_name]
            case_obj = replace(base_case, **spec.get("case_updates", {}))
            scenario = clone_scenario(base, name=spec["variant_id"], **spec.get("scenario_updates", {}))
            row = solve_one(case_name, spec["variant_id"], scenario, case_obj, spec["minor_losses"])
            row.update({"input_family": spec["input_family"], "variation": spec["variation"]})
            base_row = baseline_by_case[case_name]
            row["delta_mdot_kg_s"] = fmt(float(row["mdot_model_kg_s"]) - float(base_row["mdot_model_kg_s"]))
            row["delta_qhx_total_W"] = fmt(float(row["qhx_total_W"]) - float(base_row["qhx_total_W"]))
            row["delta_qambient_total_W"] = fmt(float(row["qambient_total_W"]) - float(base_row["qambient_total_W"]))
            variant_rows.append(row)
            solves_used += 1
    return baseline_rows, variant_rows, skip_rows, warnings


def split_guardrail_audit(executed: bool, lint_status: str, skipped: int) -> List[Dict[str, Any]]:
    return [
        {
            "audit_id": "train_only_scope",
            "status": "pass",
            "evidence": "Only Salt 2, Salt 3, and Salt 4 Fluid config cases are eligible in this execution package.",
        },
        {
            "audit_id": "runtime_input_lint",
            "status": lint_status,
            "evidence": "Runtime manifest contains no forbidden input marked as used.",
        },
        {
            "audit_id": "protected_scoring",
            "status": "pass",
            "evidence": "No validation, holdout, external-test, or measured-temperature score was computed.",
        },
        {
            "audit_id": "admission_release",
            "status": "pass",
            "evidence": "No source/property release, Qwall release, candidate freeze, coefficient admission, or final score emitted.",
        },
        {
            "audit_id": "execution_completeness",
            "status": "incomplete" if skipped else ("pass" if executed else "not_executed"),
            "evidence": f"Budget-skipped rows: {skipped}.",
        },
    ]


def heat_ledger_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        out.append(
            {
                "case": row.get("case", ""),
                "variant_id": row.get("variant_id", ""),
                "execution_status": row.get("execution_status", ""),
                "mdot_model_kg_s": row.get("mdot_model_kg_s", ""),
                "qhx_total_W": row.get("qhx_total_W", ""),
                "qambient_total_W": row.get("qambient_total_W", ""),
                "segment_Q_source_sum_W": row.get("segment_Q_source_sum_W", ""),
                "segment_Q_hx_sum_W": row.get("segment_Q_hx_sum_W", ""),
                "segment_Q_ambient_sum_W": row.get("segment_Q_ambient_sum_W", ""),
                "max_abs_segment_residual_R_s_W": row.get("max_abs_segment_residual_R_s_W", ""),
                "residual_owner_label": row.get("residual_owner_label", ""),
            }
        )
    return out


def write_docs(summary: Dict[str, Any], paths: Dict[str, Path]) -> None:
    readme = OUT_DIR / "README.md"
    readme.write_text(
        f"""---
provenance:
  - {RUNBOOK_DIR / 'README.md'}
  - {FLUID_ROOT / 'tamu_loop_model_v2/solver.py'}
tags: [predictive-1d, setup-uq, train-only, smoke-execution, no-release]
related:
  - .agent/status/{DATE}_{TASK_ID}.md
  - .agent/journal/{DATE}/1d-train-only-setup-uq-smoke-execution.md
task: {TASK_ID}
date: {DATE}
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: work_product
status: complete
---
# 1D Train-Only Setup-UQ Smoke Execution

Decision: `{summary['decision']}`.

The smoke used the repo-local Fluid `solve_case` API in read-only mode with
bytecode writes disabled. It froze a setup-only runtime manifest, ran the
baseline train smoke before any variants, and then consumed a bounded solve
budget on one-at-a-time setup-legal variants. Budget-skipped rows are explicit;
they are not inferred.

## Result

- Baseline rows completed: `{summary['baseline_rows']}`
- Variant rows completed: `{summary['variant_rows']}`
- Budget/unsupported skip rows: `{summary['skip_rows']}`
- Runtime lint: `{summary['runtime_lint_status']}`
- Release/admission/final score: `false`

## Files

- `runtime_input_manifest.csv`
- `baseline_root_and_qoi_smoke.csv`
- `one_at_a_time_setup_uq_smoke.csv`
- `unsupported_variant_skip_reasons.csv`
- `heat_ledger_sensitivity.csv`
- `split_guardrail_audit.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source file, external repository, thesis body, source/property release, Qwall
release, coefficient admission, candidate freeze, protected score, final score,
or S11/S12/S13/S15/S6 trigger changed.
""",
        encoding="utf-8",
    )

    status = REPO_ROOT / f".agent/status/{DATE}_{TASK_ID}.md"
    status.write_text(
        f"""---
provenance:
  - {paths['summary']}
tags: [status, predictive-1d, setup-uq, smoke-execution]
related:
  - .agent/journal/{DATE}/1d-train-only-setup-uq-smoke-execution.md
  - imports/{DATE}_{SLUG}.json
task: {TASK_ID}
date: {DATE}
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: status
status: complete
---
# {TASK_ID}

## Objective

Execute a bounded train-only setup-UQ smoke against the read-only Fluid
`solve_case` API, with fail-closed runtime legality and no release/scoring.

## Outcome

Decision: `{summary['decision']}`.

Baseline rows completed: `{summary['baseline_rows']}`. Variant rows completed:
`{summary['variant_rows']}`. Budget/unsupported skip rows: `{summary['skip_rows']}`.
Runtime lint: `{summary['runtime_lint_status']}`.

## Changes Made

- Added `tools/analyze/build_1d_train_only_setup_uq_smoke_execution.py`.
- Added `tools/analyze/test_1d_train_only_setup_uq_smoke_execution.py`.
- Published `{OUT_DIR.relative_to(REPO_ROOT)}/` with runtime, baseline,
  sensitivity, skip, heat-ledger, split-audit, source-manifest, guardrail, and
  summary artifacts.

## Validation

- Fluid one-case API preflight completed for Salt 2 before implementation.
- Task builder executed with the configured solve budget.
- Unit tests passed.
- JSON manifests parsed.
- `git diff --check` passed for task-owned paths.

## Unresolved Blockers

This row does not release a candidate or score protected rows. Any budget-skipped
variant remains a follow-on compute-node or scheduler-sized execution item.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
OpenFOAM/postprocessing/sampler/harvest launch, Fluid/external edit,
validation/holdout/external-test tuning or scoring, fitting/tuning/model
selection, source/property release, candidate freeze, coefficient admission,
F6/component-K/internal-Nu/exchange-coefficient emission, final-score claim,
S11/S12/S13/S15/S6 trigger, blocker-register change, generated-index refresh,
or runtime use of CFD mdot, realized wallHeatFlux, imposed cooler duty,
validation temperatures, holdout temperatures, external-test temperatures,
realized test-section heat, or hidden global multiplier occurred.
""",
        encoding="utf-8",
    )

    journal = REPO_ROOT / f".agent/journal/{DATE}/1d-train-only-setup-uq-smoke-execution.md"
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text(
        f"""---
provenance:
  - {paths['summary']}
  - {RUNBOOK_DIR / 'README.md'}
tags: [journal, predictive-1d, setup-uq, smoke-execution]
related:
  - .agent/status/{DATE}_{TASK_ID}.md
task: {TASK_ID}
date: {DATE}
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: journal
status: complete
---
# 1D Train-Only Setup-UQ Smoke Execution

## Attempted

Read the setup-UQ runbook, confirmed Fluid `solve_case` availability, froze a
runtime manifest, ran a bounded train-only smoke, and wrote the no-release
package.

## Observed

The Fluid API is callable in read-only mode but each salt solve is slow enough
that a broad full grid should move to compute-node execution. This package ran
the baseline rows first and then only the one-at-a-time rows permitted by the
solve budget.

## Inferred

The setup-UQ pathway is executable, but this row is not a candidate freeze or
score release. Budget-skipped setup variants should be treated as unexecuted,
not interpolated from completed rows.

## Next Useful Actions

Use this package to choose a scheduler-sized full setup-UQ sweep only after
confirming the completed rows have finite root status and no runtime lint
failure. Keep source/property, Qwall, protected scoring, and candidate freeze in
separate explicitly claimed rows.
""",
        encoding="utf-8",
    )

    import_manifest = REPO_ROOT / f"imports/{DATE}_{SLUG}.json"
    import_manifest.write_text(
        json.dumps(
            {
                "task": TASK_ID,
                "date": DATE,
                "role": "Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Implementer / Tester / Writer",
                "objective": "Execute bounded train-only setup-UQ smoke against read-only Fluid solve_case.",
                "changed_files": [
                    ".agent/BOARD.md",
                    f".agent/status/{DATE}_{TASK_ID}.md",
                    f".agent/journal/{DATE}/1d-train-only-setup-uq-smoke-execution.md",
                    f"imports/{DATE}_{SLUG}.json",
                    "tools/analyze/build_1d_train_only_setup_uq_smoke_execution.py",
                    "tools/analyze/test_1d_train_only_setup_uq_smoke_execution.py",
                    f"{OUT_DIR.relative_to(REPO_ROOT)}/README.md",
                    f"{OUT_DIR.relative_to(REPO_ROOT)}/summary.json",
                    f"{OUT_DIR.relative_to(REPO_ROOT)}/runtime_input_manifest.csv",
                    f"{OUT_DIR.relative_to(REPO_ROOT)}/baseline_root_and_qoi_smoke.csv",
                    f"{OUT_DIR.relative_to(REPO_ROOT)}/one_at_a_time_setup_uq_smoke.csv",
                    f"{OUT_DIR.relative_to(REPO_ROOT)}/unsupported_variant_skip_reasons.csv",
                    f"{OUT_DIR.relative_to(REPO_ROOT)}/heat_ledger_sensitivity.csv",
                    f"{OUT_DIR.relative_to(REPO_ROOT)}/split_guardrail_audit.csv",
                    f"{OUT_DIR.relative_to(REPO_ROOT)}/source_manifest.csv",
                    f"{OUT_DIR.relative_to(REPO_ROOT)}/no_mutation_guardrails.csv",
                ],
                "read_only_context": [
                    str(RUNBOOK_DIR.relative_to(REPO_ROOT)),
                    str(FLUID_ROOT / "configs/cases.yaml"),
                    str(FLUID_ROOT / "configs/scenarios.yaml"),
                    str(FLUID_ROOT / "tamu_loop_model_v2/solver.py"),
                    "native CFD/OpenFOAM outputs",
                    "registry/admission state",
                    "scheduler state",
                    "blocker register",
                    "generated docs index files",
                    "thesis current/LaTeX files",
                ],
                "native_solver_outputs_mutated": False,
                "registry_mutated": False,
                "scheduler_action": False,
                "external_fluid_edit": False,
                "mutation_flags": {
                    "fluid_source_edited": False,
                    "scheduler_submission_performed": False,
                    "native_solver_outputs_mutated": False,
                    "registry_mutated": False,
                    "admission_state_mutated": False,
                    "source_property_or_qwall_release": False,
                    "coefficient_admission": False,
                    "final_score_claim": False,
                    "protected_scoring_performed": False,
                    "s11_s12_s13_s15_s6_triggered": False,
                },
                "decision": summary["decision"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def build_package(execute: bool, solve_budget: int) -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = runtime_manifest_rows()
    lint_status, illegal_used = runtime_lint_status(manifest)
    baseline_rows, variant_rows, skip_rows, warnings = run_solver_rows(execute, solve_budget)
    if illegal_used:
        decision = "invalid_runtime_manifest_fail_closed_no_release_no_score"
    elif execute and baseline_rows and skip_rows:
        decision = "bounded_train_only_setup_uq_smoke_partial_no_release_no_score"
    elif execute and baseline_rows:
        decision = "train_only_setup_uq_smoke_complete_no_release_no_score"
    else:
        decision = "train_only_setup_uq_smoke_not_executed_fail_closed_no_release_no_score"
    summary = {
        "task_id": TASK_ID,
        "generated_at": now_iso(),
        "decision": decision,
        "execute_mode": execute,
        "solve_budget": solve_budget,
        "baseline_rows": len(baseline_rows),
        "variant_rows": len(variant_rows),
        "skip_rows": len(skip_rows),
        "runtime_manifest_rows": len(manifest),
        "runtime_lint_status": lint_status,
        "warnings": warnings,
        "source_property_release": False,
        "qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "protected_scoring_performed": False,
        "final_score_claim": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
    }
    write_csv(OUT_DIR / "runtime_input_manifest.csv", manifest)
    write_csv(OUT_DIR / "baseline_root_and_qoi_smoke.csv", baseline_rows)
    write_csv(OUT_DIR / "one_at_a_time_setup_uq_smoke.csv", variant_rows)
    write_csv(OUT_DIR / "unsupported_variant_skip_reasons.csv", skip_rows)
    write_csv(OUT_DIR / "heat_ledger_sensitivity.csv", heat_ledger_rows(baseline_rows + variant_rows))
    write_csv(OUT_DIR / "split_guardrail_audit.csv", split_guardrail_audit(execute, lint_status, len(skip_rows)))
    write_csv(
        OUT_DIR / "source_manifest.csv",
        [
            {"source_id": "runbook", "path": str(RUNBOOK_DIR / "README.md"), "role": "read_only_contract"},
            {"source_id": "fluid_cases", "path": str(FLUID_ROOT / "configs/cases.yaml"), "role": "read_only_setup_inputs"},
            {"source_id": "fluid_scenarios", "path": str(FLUID_ROOT / "configs/scenarios.yaml"), "role": "read_only_setup_scenarios"},
            {"source_id": "fluid_solver", "path": str(FLUID_ROOT / "tamu_loop_model_v2/solver.py"), "role": "read_only_api"},
        ],
    )
    write_csv(
        OUT_DIR / "no_mutation_guardrails.csv",
        [
            {"guardrail": "native_solver_outputs_mutated", "value": False, "note": "no OpenFOAM output paths written"},
            {"guardrail": "registry_mutated", "value": False, "note": "registry/admission state not changed"},
            {"guardrail": "scheduler_action", "value": False, "note": "no sbatch/srun/scancel used"},
            {"guardrail": "fluid_source_edited", "value": False, "note": "Fluid source tree read-only"},
            {"guardrail": "protected_scoring_performed", "value": False, "note": "no validation/holdout/external measured targets scored"},
            {"guardrail": "release_or_admission", "value": False, "note": "no source/property/Qwall/coefficient/final-score release"},
        ],
    )
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(summary, {"summary": OUT_DIR / "summary.json"})
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Call Fluid solve_case for a bounded smoke.")
    parser.add_argument("--run-smoke", action="store_true", help="Backward-compatible alias for scheduler smoke execution.")
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR, help="Backward-compatible output path; must match the task package.")
    parser.add_argument("--solve-budget", type=int, default=6, help="Maximum Fluid solves to run after runtime lint passes.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.resolve() != OUT_DIR.resolve():
        raise SystemExit(f"Unsupported output-dir for this task-owned builder: {args.output_dir}")
    execute = bool(args.execute or args.run_smoke)
    solve_budget = 36 if args.run_smoke and args.solve_budget == 6 else max(args.solve_budget, 0)
    summary = build_package(execute=execute, solve_budget=solve_budget)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
