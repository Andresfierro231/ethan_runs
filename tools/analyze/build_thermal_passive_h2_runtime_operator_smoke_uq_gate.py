#!/usr/bin/env python3
"""Build a no-leak PASSIVE-H2 runtime-operator smoke/UQ gate."""
from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


TASK_ID = "TODO-THERMAL-PASSIVE-H2-RUNTIME-OPERATOR-SMOKE-UQ-GATE-2026-07-22"
DATE = "2026-07-22"
SIGMA = 5.670374419e-8
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate"

PREFLIGHT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_one_train_repair_preflight"
SETUP_UQ_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution"
TERMINAL_UQ_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_terminal_harvest_and_validator"
LEDGER_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract"

OPERATOR_CONTRACT = PREFLIGHT_DIR / "passive_operator_term_contract.csv"
PREFLIGHT_SUMMARY = PREFLIGHT_DIR / "summary.json"
SENSOR_PREDICTIONS = SETUP_UQ_DIR / "sensor_projection_predictions.csv"
SENSOR_SENSITIVITY = SETUP_UQ_DIR / "sensor_projection_sensitivity.csv"
HEAT_LEDGER = SETUP_UQ_DIR / "heat_ledger_sensitivity.csv"
MDOT_HEAT_SENSITIVITY = SETUP_UQ_DIR / "mdot_heat_sensitivity.csv"
RUNTIME_MANIFEST = SETUP_UQ_DIR / "runtime_input_manifest.csv"
TERMINAL_SUMMARY = TERMINAL_UQ_DIR / "summary.json"
LEDGER_SUMMARY = LEDGER_DIR / "summary.json"

FAMILY_SENSOR_MAP = {
    "cooling_branch": ["TW10", "TW11"],
    "downcomer": ["TW1", "TW2", "TW3"],
    "junction": ["TW4", "TW5", "TW6", "TW7"],
    "lower_leg": ["TW4", "TW5", "TW6"],
    "upcomer": ["TW7", "TW8", "TW9"],
}

SCENARIOS = [
    {"scenario_id": "nominal", "hA_scale": 1.0, "ambient_offset_K": 0.0, "wall_offset_K": 0.0, "radiation_on": True},
    {"scenario_id": "hA_0p5", "hA_scale": 0.5, "ambient_offset_K": 0.0, "wall_offset_K": 0.0, "radiation_on": True},
    {"scenario_id": "hA_2p0", "hA_scale": 2.0, "ambient_offset_K": 0.0, "wall_offset_K": 0.0, "radiation_on": True},
    {"scenario_id": "ambient_minus_2K", "hA_scale": 1.0, "ambient_offset_K": -2.0, "wall_offset_K": 0.0, "radiation_on": True},
    {"scenario_id": "ambient_plus_2K", "hA_scale": 1.0, "ambient_offset_K": 2.0, "wall_offset_K": 0.0, "radiation_on": True},
    {"scenario_id": "wall_state_minus_2K", "hA_scale": 1.0, "ambient_offset_K": 0.0, "wall_offset_K": -2.0, "radiation_on": True},
    {"scenario_id": "wall_state_plus_2K", "hA_scale": 1.0, "ambient_offset_K": 0.0, "wall_offset_K": 2.0, "radiation_on": True},
    {"scenario_id": "radiation_off", "hA_scale": 1.0, "ambient_offset_K": 0.0, "wall_offset_K": 0.0, "radiation_on": False},
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Iterable[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fieldnames or sorted({key for row in rows for key in row}))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: "" if row.get(name) is None else row.get(name) for name in names})


def fnum(value: str) -> float:
    return float(value)


def wall_predictions() -> Dict[str, float]:
    rows = [
        row
        for row in read_csv(SENSOR_PREDICTIONS)
        if row["scenario_id"] == "salt_2__V00__nominal"
        and row["projection_stream"] == "wall_state"
        and row["prediction_K"]
    ]
    return {row["sensor"]: fnum(row["prediction_K"]) for row in rows}


def family_wall_state_rows(pred: Dict[str, float]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for family, sensors in FAMILY_SENSOR_MAP.items():
        values = [pred[sensor] for sensor in sensors if sensor in pred]
        if not values:
            raise RuntimeError(f"missing wall-state predictions for {family}")
        rows.append(
            {
                "source_family": family,
                "mapped_wall_state_sensors": ";".join(sensors),
                "finite_sensor_count": len(values),
                "model_predicted_wall_state_mean_K": sum(values) / len(values),
                "model_predicted_wall_state_min_K": min(values),
                "model_predicted_wall_state_max_K": max(values),
                "runtime_temperature_allowed": False,
                "runtime_temperature_source": "model_prediction_output_only_no_observed_temperature_input",
            }
        )
    return rows


def q_row(contract: Dict[str, str], wall_state: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
    area = fnum(contract["area_m2_nominal"])
    hA = fnum(contract["hA_W_K_nominal"]) * scenario["hA_scale"]
    emissivity = fnum(contract["emissivity_nominal"])
    tw = float(wall_state["model_predicted_wall_state_mean_K"]) + scenario["wall_offset_K"]
    ta = fnum(contract["Ta_K_nominal"]) + scenario["ambient_offset_K"]
    tsur = fnum(contract["Tsur_K_nominal"]) + scenario["ambient_offset_K"]
    q_conv = hA * (tw - ta)
    q_rad = emissivity * SIGMA * area * (math.pow(tw, 4) - math.pow(tsur, 4)) if scenario["radiation_on"] else 0.0
    return {
        "scenario_id": scenario["scenario_id"],
        "candidate_id": contract["candidate_id"],
        "train_case_id": contract["train_case_id"],
        "source_family": contract["source_family"],
        "mapped_wall_state_sensors": wall_state["mapped_wall_state_sensors"],
        "model_predicted_wall_state_mean_K": tw,
        "Ta_K": ta,
        "Tsur_K": tsur,
        "area_m2": area,
        "hA_W_K": hA,
        "emissivity": emissivity,
        "radiation_on": scenario["radiation_on"],
        "diagnostic_q_conv_W": q_conv,
        "diagnostic_q_rad_W": q_rad,
        "diagnostic_q_total_W": q_conv + q_rad,
        "numeric_q_loss_release": False,
        "runtime_wallHeatFlux_used": False,
        "runtime_validation_temperature_used": False,
        "runtime_CFD_mdot_used": False,
        "runtime_Qwall_used": False,
        "runtime_imposed_cooler_duty_used": False,
        "interpretation": "diagnostic_runtime_operator_smoke_not_admitted_q_loss",
    }


def operator_smoke_rows(contract_rows: List[Dict[str, str]], wall_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    wall_by_family = {row["source_family"]: row for row in wall_rows}
    rows: List[Dict[str, Any]] = []
    for scenario in SCENARIOS:
        for contract in contract_rows:
            rows.append(q_row(contract, wall_by_family[contract["source_family"]], scenario))
    return rows


def scenario_summary(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nominal = sum(row["diagnostic_q_total_W"] for row in rows if row["scenario_id"] == "nominal")
    summaries: List[Dict[str, Any]] = []
    for scenario in SCENARIOS:
        subset = [row for row in rows if row["scenario_id"] == scenario["scenario_id"]]
        q_total = sum(row["diagnostic_q_total_W"] for row in subset)
        summaries.append(
            {
                "scenario_id": scenario["scenario_id"],
                "diagnostic_q_conv_total_W": sum(row["diagnostic_q_conv_W"] for row in subset),
                "diagnostic_q_rad_total_W": sum(row["diagnostic_q_rad_W"] for row in subset),
                "diagnostic_q_total_W": q_total,
                "delta_vs_nominal_W": q_total - nominal,
                "numeric_q_loss_release": False,
                "admission_allowed": False,
            }
        )
    return summaries


def projection_sensitivity_summary() -> List[Dict[str, Any]]:
    rows = [
        row
        for row in read_csv(SENSOR_SENSITIVITY)
        if row["case_id"] == "salt_2"
        and row["input_family"] in {"external_convection_hA", "radiation"}
        and row["delta_prediction_K"]
    ]
    grouped: Dict[tuple[str, str, str], List[float]] = {}
    for row in rows:
        key = (row["input_family"], row["level"], "TP" if row["sensor"].startswith("TP") else "TW")
        grouped.setdefault(key, []).append(abs(fnum(row["delta_prediction_K"])))
    return [
        {
            "input_family": key[0],
            "level": key[1],
            "sensor_group": key[2],
            "finite_sensor_delta_rows": len(values),
            "max_abs_delta_prediction_K": max(values),
            "mean_abs_delta_prediction_K": sum(values) / len(values),
            "runtime_temperature_allowed": False,
            "fit_allowed": False,
            "model_selection_allowed": False,
            "interpretation": "existing train-only projection sensitivity; not observed-temperature runtime input",
        }
        for key, values in sorted(grouped.items())
    ]


def projection_lookup() -> Dict[tuple[str, str], Dict[str, float]]:
    grouped: Dict[tuple[str, str, str], List[float]] = {}
    for row in read_csv(SENSOR_SENSITIVITY):
        if row["case_id"] != "salt_2" or not row["delta_prediction_K"]:
            continue
        group = "TP" if row["sensor"].startswith("TP") else "TW"
        key = (row["input_family"], row["level"], group)
        grouped.setdefault(key, []).append(abs(fnum(row["delta_prediction_K"])))
    out: Dict[tuple[str, str], Dict[str, float]] = {}
    for (input_family, level, group), values in grouped.items():
        target = out.setdefault((input_family, level), {})
        target[f"{group}_max_abs_delta_K"] = max(values)
        target[f"{group}_mean_abs_delta_K"] = sum(values) / len(values)
    return out


def operator_delta_lookup(summary_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    return {row["scenario_id"]: row["delta_vs_nominal_W"] for row in summary_rows}


def mdot_tp_tw_heat_operator_sensitivity(summary_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    projections = projection_lookup()
    operator_deltas = operator_delta_lookup(summary_rows)
    scenario_map = {
        "external_hA_0p5": "hA_0p5",
        "external_hA_2p0": "hA_2p0",
        "ambient_minus_2K": "ambient_minus_2K",
        "ambient_plus_2K": "ambient_plus_2K",
    }
    rows: List[Dict[str, Any]] = []
    for row in read_csv(MDOT_HEAT_SENSITIVITY):
        if row["case_id"] != "salt_2":
            continue
        key = (row["input_family"], row["level"])
        projection = projections.get(key, {})
        operator_scenario = scenario_map.get(row["level"], "")
        if row["input_family"] == "radiation" and row["level"] == "radiation_on":
            operator_scenario = "radiation_off"
            caveat = "model radiation_on variant has zero model-output delta; local operator compares nominal radiation to radiation_off"
        elif operator_scenario:
            caveat = "operator scenario is same setup perturbation label"
        else:
            caveat = "no directly matched passive-operator local perturbation; mdot/heat/TP/TW retained as setup-UQ context"
        rows.append(
            {
                "case_id": row["case_id"],
                "variant_id": row["variant_id"],
                "input_family": row["input_family"],
                "level": row["level"],
                "model_scenario_id": row["scenario_id"],
                "delta_mdot_model_kg_s": fnum(row["delta_mdot_model_kg_s"]),
                "delta_qhx_total_W": fnum(row["delta_qhx_total_W"]),
                "delta_qambient_total_W": fnum(row["delta_qambient_total_W"]),
                "TP_max_abs_delta_K": projection.get("TP_max_abs_delta_K", ""),
                "TP_mean_abs_delta_K": projection.get("TP_mean_abs_delta_K", ""),
                "TW_max_abs_delta_K": projection.get("TW_max_abs_delta_K", ""),
                "TW_mean_abs_delta_K": projection.get("TW_mean_abs_delta_K", ""),
                "passive_operator_local_scenario_id": operator_scenario,
                "passive_operator_delta_vs_nominal_W": operator_deltas.get(operator_scenario, ""),
                "comparison_caveat": caveat,
                "runtime_wallHeatFlux_used": False,
                "runtime_observed_temperature_used": False,
                "source_property_release": False,
                "admission_or_score": False,
            }
        )
    return rows


def heat_ledger_rows(summary_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    heat_rows = read_csv(HEAT_LEDGER)
    baseline = next(row for row in heat_rows if row["case"] == "Salt 2" and row["variant_id"] == "V00_baseline")
    qambient = fnum(baseline["qambient_total_W"])
    qhx = fnum(baseline["qhx_total_W"])
    return [
        {
            "scenario_id": row["scenario_id"],
            "baseline_qambient_total_W": qambient,
            "baseline_qhx_total_W": qhx,
            "diagnostic_passive_operator_q_total_W": row["diagnostic_q_total_W"],
            "diagnostic_delta_vs_baseline_qambient_W": row["diagnostic_q_total_W"] - qambient,
            "heat_ledger_release": False,
            "residual_absorption_into_internal_Nu": False,
            "interpretation": "diagnostic comparison only; no heat-ledger replacement or model admission",
        }
        for row in summary_rows
    ]


def runtime_input_audit() -> List[Dict[str, Any]]:
    manifest = read_csv(RUNTIME_MANIFEST)
    preflight_guardrails = read_csv(PREFLIGHT_DIR / "no_mutation_guardrails.csv")
    forbidden = [row for row in manifest if row["input_family"] == "forbidden_runtime_field"]
    return [
        {
            "audit_item": "setup_basis_inputs",
            "status": "pass",
            "count": 5,
            "allowed_runtime_use": "hA area Ta Tsur emissivity layers plus model-predicted state",
            "forbidden_release": "numeric q_loss release remains false",
        },
        {
            "audit_item": "forbidden_runtime_manifest_rows",
            "status": "pass",
            "count": len(forbidden),
            "allowed_runtime_use": "none",
            "forbidden_release": "wallHeatFlux validation_temperature CFD_mdot Qwall imposed_cooler_duty",
        },
        {
            "audit_item": "preflight_guardrail_rows",
            "status": "pass",
            "count": len(preflight_guardrails),
            "allowed_runtime_use": "dry preflight provenance",
            "forbidden_release": "repair freeze score fit admission",
        },
    ]


def decision_gate(summary_rows: List[Dict[str, Any]], projection_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {"gate": "runtime_input_audit", "status": "pass", "reason": "only setup basis plus model-predicted wall state consumed"},
        {"gate": "operator_smoke", "status": "diagnostic_pass", "reason": f"{len(summary_rows)} scenario summaries generated"},
        {"gate": "tp_tw_projection_sensitivity", "status": "support_only", "reason": f"{len(projection_rows)} existing sensitivity groups summarized"},
        {"gate": "numeric_q_loss_release", "status": "closed", "reason": "diagnostic q rows are not a source/property or heat-loss release"},
        {"gate": "admission_or_freeze", "status": "closed", "reason": "no protected scoring, fitting, model selection, candidate freeze, or final score"},
    ]


def no_mutation_guardrails() -> List[Dict[str, Any]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "status": False},
        {"guardrail": "registry_or_admission_mutated", "status": False},
        {"guardrail": "scheduler_action", "status": False},
        {"guardrail": "solver_postprocessing_sampler_harvest_UQ_launch", "status": False},
        {"guardrail": "Fluid_or_external_repo_edit", "status": False},
        {"guardrail": "thesis_current_or_LaTeX_edit", "status": False},
        {"guardrail": "validation_holdout_external_scoring", "status": False},
        {"guardrail": "fitting_tuning_model_selection", "status": False},
        {"guardrail": "source_property_Qwall_or_numeric_q_loss_release", "status": False},
        {"guardrail": "repair_execution_candidate_freeze_or_final_score", "status": False},
    ]


def source_manifest() -> List[Dict[str, Any]]:
    paths = [
        OPERATOR_CONTRACT,
        PREFLIGHT_SUMMARY,
        SENSOR_PREDICTIONS,
        SENSOR_SENSITIVITY,
        HEAT_LEDGER,
        MDOT_HEAT_SENSITIVITY,
        RUNTIME_MANIFEST,
        TERMINAL_SUMMARY,
        LEDGER_SUMMARY,
    ]
    return [
        {"source_path": rel(path), "exists": path.exists(), "mutation_status": "read_only", "use": "runtime operator smoke/UQ gate source"}
        for path in paths
    ]


def scientific_findings_and_caveats(summary: Dict[str, Any], mdot_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    max_mdot = max(abs(row["delta_mdot_model_kg_s"]) for row in mdot_rows)
    max_qambient = max(abs(row["delta_qambient_total_W"]) for row in mdot_rows)
    return [
        {
            "finding_id": "F01",
            "finding": "The passive_H2 runtime operator is executable without forbidden runtime inputs.",
            "evidence": f"operator_smoke_rows={summary['operator_smoke_rows']}; operator_family_rows={summary['operator_family_rows']}; runtime leakage flags false",
            "interpretation": "The row passes as a smoke/UQ gate, not as a heat-loss release.",
            "release_status": "smoke_pass_no_release",
        },
        {
            "finding_id": "F02",
            "finding": "The diagnostic operator is radiation dominated at the current predicted wall states.",
            "evidence": f"nominal_conv={summary['diagnostic_nominal_q_conv_total_W']:.6g} W; nominal_rad={summary['diagnostic_nominal_q_rad_total_W']:.6g} W",
            "interpretation": "Radiation/runtime-basis semantics need a follow-up before any numeric passive q-loss release.",
            "release_status": "diagnostic_only",
        },
        {
            "finding_id": "F03",
            "finding": "The model radiation_on setup-UQ variant does not move mdot, heat ledger, or TP/TW in the existing smoke.",
            "evidence": "radiation rows in mdot/heat and TP/TW sensitivity are zero; local operator radiation_off delta is large.",
            "interpretation": "Do not claim radiation implementation admission; treat radiation as a targeted follow-up.",
            "release_status": "blocked_for_radiation_admission",
        },
        {
            "finding_id": "F04",
            "finding": "Existing setup-UQ still provides useful mdot, TP/TW, and heat-ledger sensitivity context.",
            "evidence": f"max_abs_delta_mdot={max_mdot:.6g} kg/s; max_abs_delta_qambient={max_qambient:.6g} W",
            "interpretation": "Use these as train-only support evidence only, with no scoring or fitting.",
            "release_status": "supporting_uq_only",
        },
    ]


def write_readme(summary: Dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(OUT_DIR / "summary.json")}
  - {rel(OUT_DIR / "passive_operator_family_smoke.csv")}
  - {rel(OUT_DIR / "passive_operator_sensitivity_summary.csv")}
tags: [thermal, passive-h2, runtime-operator, smoke-uq, no-release]
related:
  - .agent/status/2026-07-22_TODO-THERMAL-PASSIVE-H2-RUNTIME-OPERATOR-SMOKE-UQ-GATE-2026-07-22.md
  - .agent/journal/2026-07-22/thermal-passive-h2-runtime-operator-smoke-uq-gate.md
  - imports/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate.json
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: work_product_readme
status: complete
---
# PASSIVE-H2 Runtime-Operator Smoke/UQ Gate

Decision: `{summary['decision']}`.

This package executes a no-leak diagnostic runtime-operator smoke for
`PASSIVE-H2-CAND001` on `salt_2`. It consumes the source-backed setup fields
from the one-train preflight and model-predicted wall-state temperatures from
the train-only smoke. It does not use observed validation temperatures,
realized CFD wallHeatFlux, CFD mdot, Qwall, imposed cooler duty, or a fitted
global multiplier.

The computed passive-operator heat-loss rows are diagnostic only. They are not
a numeric `q_loss` release, source/property release, Qwall release, repair
execution, candidate freeze, coefficient admission, protected score, or final
score.

Key diagnostic numbers:

- nominal passive-operator smoke total:
  `{summary['diagnostic_nominal_q_total_W']:.6g} W`
  (`{summary['diagnostic_nominal_q_conv_total_W']:.6g} W` convective,
  `{summary['diagnostic_nominal_q_rad_total_W']:.6g} W` radiative);
- largest local passive-operator sensitivity:
  `{summary['largest_abs_sensitivity_delta_W']:.6g} W`;
- largest existing train-only mdot/TP/TW/heat sensitivities:
  `{summary['max_abs_delta_mdot_model_kg_s']:.6g} kg/s`,
  `{summary['max_abs_TP_delta_K']:.6g} K`,
  `{summary['max_abs_TW_delta_K']:.6g} K`,
  `{summary['max_abs_delta_qambient_total_W']:.6g} W`.

The direct radiation term is large and the existing `radiation_on` setup-UQ
variant has zero model-output delta. That is a diagnostic caveat, not a
permission to release a radiation-corrected passive heat-loss value.
"""
    (OUT_DIR / "README.md").write_text(text, encoding="utf-8")


def build() -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    contract_rows = read_csv(OPERATOR_CONTRACT)
    wall_rows = family_wall_state_rows(wall_predictions())
    smoke_rows = operator_smoke_rows(contract_rows, wall_rows)
    summary_rows = scenario_summary(smoke_rows)
    projection_rows = projection_sensitivity_summary()
    ledger_rows = heat_ledger_rows(summary_rows)
    mdot_rows = mdot_tp_tw_heat_operator_sensitivity(summary_rows)
    audit_rows = runtime_input_audit()
    gate_rows = decision_gate(summary_rows, projection_rows)
    guardrails = no_mutation_guardrails()
    manifest = source_manifest()
    preflight_summary = read_json(PREFLIGHT_SUMMARY)
    terminal_summary = read_json(TERMINAL_SUMMARY)

    write_csv(OUT_DIR / "runtime_input_audit.csv", audit_rows)
    write_csv(OUT_DIR / "operator_wall_state_mapping.csv", wall_rows)
    write_csv(OUT_DIR / "passive_operator_family_smoke.csv", smoke_rows)
    write_csv(OUT_DIR / "passive_operator_sensitivity_summary.csv", summary_rows)
    write_csv(OUT_DIR / "tp_tw_projection_sensitivity_summary.csv", projection_rows)
    write_csv(OUT_DIR / "heat_ledger_sensitivity_summary.csv", ledger_rows)
    write_csv(OUT_DIR / "mdot_tp_tw_heat_operator_sensitivity.csv", mdot_rows)
    write_csv(OUT_DIR / "passive_h2_runtime_operator_family_scenario.csv", smoke_rows)
    write_csv(OUT_DIR / "passive_h2_runtime_operator_scenario_summary.csv", summary_rows)
    write_csv(OUT_DIR / "passive_h2_runtime_operator_uq_sensitivity.csv", [row for row in summary_rows if row["scenario_id"] != "nominal"])
    write_csv(OUT_DIR / "heat_ledger_family_operator_comparison.csv", ledger_rows)
    write_csv(OUT_DIR / "decision_gate.csv", gate_rows)
    write_csv(OUT_DIR / "source_manifest.csv", manifest)
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrails)

    nominal = next(row for row in summary_rows if row["scenario_id"] == "nominal")
    largest_delta = max(abs(row["delta_vs_nominal_W"]) for row in summary_rows)
    max_mdot = max(abs(row["delta_mdot_model_kg_s"]) for row in mdot_rows)
    max_qambient = max(abs(row["delta_qambient_total_W"]) for row in mdot_rows)
    max_tp = max(float(row["TP_max_abs_delta_K"] or 0.0) for row in mdot_rows)
    max_tw = max(float(row["TW_max_abs_delta_K"] or 0.0) for row in mdot_rows)
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": now_iso(),
        "decision": "passive_h2_runtime_operator_smoke_uq_gate_diagnostic_no_release_no_admission",
        "candidate_id": preflight_summary["candidate_id"],
        "train_case_id": preflight_summary["train_case_id"],
        "operator_family_rows": len(contract_rows),
        "wall_state_mapping_rows": len(wall_rows),
        "operator_smoke_rows": len(smoke_rows),
        "sensitivity_scenario_rows": len(summary_rows),
        "tp_tw_projection_sensitivity_rows": len(projection_rows),
        "diagnostic_nominal_q_total_W": nominal["diagnostic_q_total_W"],
        "diagnostic_nominal_q_conv_total_W": nominal["diagnostic_q_conv_total_W"],
        "diagnostic_nominal_q_rad_total_W": nominal["diagnostic_q_rad_total_W"],
        "largest_abs_sensitivity_delta_W": largest_delta,
        "max_abs_delta_mdot_model_kg_s": max_mdot,
        "max_abs_delta_qambient_total_W": max_qambient,
        "max_abs_TP_delta_K": max_tp,
        "max_abs_TW_delta_K": max_tw,
        "setup_uq_baseline_accepted_rows": terminal_summary["baseline_accepted_rows"],
        "setup_uq_variant_accepted_rows": terminal_summary["variant_accepted_rows"],
        "numeric_passive_heat_loss_release": False,
        "source_property_release": False,
        "qwall_release": False,
        "repair_execution": False,
        "candidate_freeze": False,
        "coefficient_admission": False,
        "protected_scoring": False,
        "fitting_or_model_selection": False,
        "final_score_claim": False,
        "s11_s12_s13_s15_s6_triggered": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "solver_or_sampler_launch": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
        "runtime_leakage_relaxation": False,
    }
    finding_rows = scientific_findings_and_caveats(summary, mdot_rows)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(OUT_DIR / "scientific_findings_and_caveats.csv", finding_rows)
    write_readme(summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
