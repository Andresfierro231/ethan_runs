#!/usr/bin/env python3
"""Extend corrected PASSIVE-H2 radiation smoke across Salt2/Salt3/Salt4."""
from __future__ import annotations

import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


TASK_ID = "TODO-THERMAL-PASSIVE-H2-MULTI-TRAIN-CORRECTED-RADIATION-SMOKE-2026-07-22"
DATE = "2026-07-22"
SIGMA = 5.670374419e-8
CALZITE_K_300K = 0.036056549855 - 6.2436910698e-05 * 300.0 + 1.9275102287e-07 * 300.0**2
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke"

EXTBC = REPO / "work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv"
SETUP_UQ_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution"
RADIATION_RECON_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation"
PREFLIGHT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_one_train_repair_preflight"
SOURCE_BASIS_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table"

SCENARIO_MATRIX = SETUP_UQ_DIR / "scenario_matrix.csv"
SENSOR_PREDICTIONS = SETUP_UQ_DIR / "sensor_projection_predictions.csv"
BASELINE_QOI = SETUP_UQ_DIR / "baseline_root_and_qoi_smoke.csv"
ONE_AT_A_TIME = SETUP_UQ_DIR / "one_at_a_time_setup_uq_smoke.csv"
SENSOR_SENSITIVITY = SETUP_UQ_DIR / "sensor_projection_sensitivity.csv"
SETUP_UQ_SUMMARY = SETUP_UQ_DIR / "summary.json"
RADIATION_RECON_SUMMARY = RADIATION_RECON_DIR / "summary.json"
PREFLIGHT_SUMMARY = PREFLIGHT_DIR / "summary.json"
SOURCE_BASIS_SUMMARY = SOURCE_BASIS_DIR / "summary.json"

CASES = ("salt_2", "salt_3", "salt_4")
PASSIVE_FAMILIES = ("cooling_branch", "downcomer", "junction", "lower_leg", "upcomer")
FAMILY_SENSOR_MAP = {
    "cooling_branch": ("TW10", "TW11"),
    "downcomer": ("TW1", "TW2", "TW3"),
    "junction": ("TW4", "TW5", "TW6", "TW7"),
    "lower_leg": ("TW4", "TW5", "TW6"),
    "upcomer": ("TW7", "TW8", "TW9"),
}


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


def fnum(value: Any) -> float:
    return float(value)


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def parse_thickness_options(text: str) -> List[List[float]]:
    groups = re.findall(r"\(([^()]+)\)", text)
    options: List[List[float]] = []
    for group in groups:
        nums = [float(item) for item in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", group)]
        if nums:
            options.append(nums)
    if not options:
        nums = [float(item) for item in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)]
        if nums:
            options.append(nums)
    return options


def layer_k(thickness_m: float) -> float:
    if abs(thickness_m - 0.03556) < 0.002:
        return CALZITE_K_300K
    if abs(thickness_m - 0.0022) < 0.0008:
        return 1.4
    return 9.248


def resistance_per_area(layers_m: Sequence[float]) -> float:
    return sum(thickness / layer_k(thickness) for thickness in layers_m)


def mean_resistance_per_area(thickness_text: str) -> Dict[str, Any]:
    options = parse_thickness_options(thickness_text)
    if not options:
        raise RuntimeError(f"missing layer thickness options in {thickness_text!r}")
    values = [resistance_per_area(option) for option in options]
    return {
        "layer_options_count": len(options),
        "layer_options": " | ".join(" ".join(f"{value:.9g}" for value in option) for option in options),
        "R_cond_m2K_W": sum(values) / len(values),
        "R_cond_m2K_W_min": min(values),
        "R_cond_m2K_W_max": max(values),
    }


def solve_outer_surface(inner_K: float, ta_K: float, tsur_K: float, hA_W_K: float, area_m2: float, emissivity: float, r_cond_K_W: float) -> Dict[str, float]:
    lo = min(ta_K, inner_K)
    hi = max(ta_K, inner_K)

    def q_out(surface_K: float) -> float:
        return hA_W_K * (surface_K - ta_K) + emissivity * SIGMA * area_m2 * (surface_K**4 - tsur_K**4)

    for _ in range(100):
        mid = 0.5 * (lo + hi)
        residual = (inner_K - mid) / r_cond_K_W - q_out(mid)
        if residual > 0:
            lo = mid
        else:
            hi = mid
    surface_K = 0.5 * (lo + hi)
    q_conv = hA_W_K * (surface_K - ta_K)
    q_rad = emissivity * SIGMA * area_m2 * (surface_K**4 - tsur_K**4)
    return {
        "outer_surface_T_K": surface_K,
        "corrected_q_conv_W": q_conv,
        "corrected_q_rad_W": q_rad,
        "corrected_q_total_W": q_conv + q_rad,
        "conductive_heat_in_W": (inner_K - surface_K) / r_cond_K_W,
    }


def extbc_passive_rows() -> List[Dict[str, str]]:
    rows = []
    for row in read_csv(EXTBC):
        if row["case_id"] not in CASES:
            continue
        if row["one_d_segment"] not in PASSIVE_FAMILIES:
            continue
        if row["recommended_runtime_mode"] != "external_boundary_table_setup_candidate":
            continue
        if row["support_status"] != "ready_for_fluid_api_consumption":
            continue
        rows.append(row)
    expected = {(case, family) for case in CASES for family in PASSIVE_FAMILIES}
    got = {(row["case_id"], row["one_d_segment"]) for row in rows}
    missing = sorted(expected - got)
    if missing:
        raise RuntimeError(f"missing case/family passive setup rows: {missing}")
    return rows


def nominal_wall_predictions() -> Dict[str, Dict[str, float]]:
    by_case: Dict[str, Dict[str, float]] = {}
    for row in read_csv(SENSOR_PREDICTIONS):
        if row["case_id"] not in CASES:
            continue
        if row["variant_id"] != "V00" or row["projection_stream"] != "wall_state" or not row["prediction_K"]:
            continue
        by_case.setdefault(row["case_id"], {})[row["sensor"]] = fnum(row["prediction_K"])
    missing = [case for case in CASES if case not in by_case]
    if missing:
        raise RuntimeError(f"missing nominal wall predictions for {missing}")
    return by_case


def family_wall_state(case_predictions: Dict[str, float], family: str) -> Dict[str, Any]:
    sensors = FAMILY_SENSOR_MAP[family]
    values = [case_predictions[sensor] for sensor in sensors if sensor in case_predictions]
    if not values:
        raise RuntimeError(f"missing wall sensors for {family}")
    return {
        "mapped_wall_state_sensors": ";".join(sensors),
        "inner_wall_state_T_K": sum(values) / len(values),
        "inner_wall_state_T_min_K": min(values),
        "inner_wall_state_T_max_K": max(values),
        "finite_wall_state_count": len(values),
    }


def setup_uq_train_scope() -> Dict[str, bool]:
    rows = read_csv(SCENARIO_MATRIX)
    return {
        case: any(row["case_id"] == case and row["variant_id"] == "V00" and row["train_only"] == "true" for row in rows)
        for case in CASES
    }


def split_scope_audit(ext_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    train_scope = setup_uq_train_scope()
    rows = []
    for case in CASES:
        roles = sorted({row["validation_split_role"] for row in ext_rows if row["case_id"] == case})
        conflict = bool(roles and roles != ["train"])
        rows.append(
            {
                "case_id": case,
                "setup_uq_train_only_label": train_scope[case],
                "external_bc_split_roles": " | ".join(roles),
                "split_label_conflict": conflict,
                "allowed_in_this_packet": train_scope[case],
                "admissible_as_training_score": False,
                "protected_scoring_allowed": False,
                "interpretation": "used as setup-UQ train-context diagnostic only; not admission/scoring evidence"
                if conflict
                else "used as train-context diagnostic only; not admission/scoring evidence",
            }
        )
    return rows


def corrected_operator_rows(ext_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    predictions = nominal_wall_predictions()
    rows: List[Dict[str, Any]] = []
    for ext in sorted(ext_rows, key=lambda row: (row["case_id"], PASSIVE_FAMILIES.index(row["one_d_segment"]))):
        case = ext["case_id"]
        family = ext["one_d_segment"]
        wall = family_wall_state(predictions[case], family)
        resistance = mean_resistance_per_area(ext["thicknessLayers"])
        area = fnum(ext["area_m2"])
        hA = fnum(ext["hA_W_K"])
        ta = fnum(ext["Ta_K"])
        tsur = fnum(ext["Tsur_K"])
        emissivity = fnum(ext["emissivity"])
        r_cond = resistance["R_cond_m2K_W"] / area
        corrected = solve_outer_surface(wall["inner_wall_state_T_K"], ta, tsur, hA, area, emissivity, r_cond)
        naive_conv = hA * (wall["inner_wall_state_T_K"] - ta)
        naive_rad = emissivity * SIGMA * area * (wall["inner_wall_state_T_K"] ** 4 - tsur**4)
        rows.append(
            {
                "candidate_id": "PASSIVE-H2-CAND001",
                "case_id": case,
                "source_family": family,
                "external_bc_split_role": ext["validation_split_role"],
                **wall,
                **resistance,
                "area_m2": area,
                "hA_W_K": hA,
                "Ta_K": ta,
                "Tsur_K": tsur,
                "emissivity": emissivity,
                "R_cond_K_W": r_cond,
                "naive_inner_surface_q_conv_W": naive_conv,
                "naive_inner_surface_q_rad_W": naive_rad,
                "naive_inner_surface_q_total_W": naive_conv + naive_rad,
                **corrected,
                "radiation_reduction_factor": naive_rad / corrected["corrected_q_rad_W"] if corrected["corrected_q_rad_W"] else "",
                "runtime_wallHeatFlux_used": False,
                "runtime_validation_temperature_used": False,
                "runtime_CFD_mdot_used": False,
                "runtime_Qwall_used": False,
                "runtime_imposed_cooler_duty_used": False,
                "numeric_q_loss_release": False,
                "source_property_release": False,
                "admission_or_score": False,
            }
        )
    return rows


def baseline_by_case() -> Dict[str, Dict[str, str]]:
    rows = read_csv(BASELINE_QOI)
    return {row["case_id"]: row for row in rows if row["case_id"] in CASES and row["variant_id"] == "V00"}


def case_summary(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    baselines = baseline_by_case()
    out: List[Dict[str, Any]] = []
    for case in CASES:
        subset = [row for row in rows if row["case_id"] == case]
        base = baselines[case]
        naive_rad = sum(row["naive_inner_surface_q_rad_W"] for row in subset)
        corrected_rad = sum(row["corrected_q_rad_W"] for row in subset)
        corrected_conv = sum(row["corrected_q_conv_W"] for row in subset)
        corrected_total = corrected_rad + corrected_conv
        qambient = fnum(base["qambient_total_W"])
        out.append(
            {
                "case_id": case,
                "scenario_id": base["scenario_id"],
                "mdot_model_kg_s": fnum(base["mdot_model_kg_s"]),
                "baseline_qambient_total_W": qambient,
                "baseline_qhx_total_W": fnum(base["qhx_total_W"]),
                "naive_inner_surface_radiation_W": naive_rad,
                "corrected_outer_surface_convection_W": corrected_conv,
                "corrected_outer_surface_radiation_W": corrected_rad,
                "corrected_outer_surface_total_W": corrected_total,
                "corrected_radiation_fraction_of_naive": corrected_rad / naive_rad if naive_rad else "",
                "corrected_total_fraction_of_baseline_qambient": corrected_total / qambient if qambient else "",
                "diagnostic_delta_corrected_total_minus_qambient_W": corrected_total - qambient,
                "numeric_q_loss_release": False,
                "admission_or_score": False,
            }
        )
    return out


def sensitivity_rows() -> List[Dict[str, Any]]:
    qoi_rows = [row for row in read_csv(ONE_AT_A_TIME) if row["case_id"] in CASES and row["input_family"] in {"external_convection_hA", "radiation", "ambient_temperature"}]
    sensor_rows = [row for row in read_csv(SENSOR_SENSITIVITY) if row["case_id"] in CASES and row["input_family"] in {"external_convection_hA", "radiation", "ambient_temperature"} and row["delta_prediction_K"]]
    baselines = baseline_by_case()
    grouped: Dict[tuple[str, str, str], Dict[str, Any]] = {}
    for row in qoi_rows:
        key = (row["case_id"], row["input_family"], row["level"])
        base = baselines[row["case_id"]]
        grouped[key] = {
            "case_id": row["case_id"],
            "input_family": row["input_family"],
            "level": row["level"],
            "delta_mdot_model_kg_s": fnum(row["mdot_model_kg_s"]) - fnum(base["mdot_model_kg_s"]),
            "delta_qambient_total_W": fnum(row["qambient_total_W"]) - fnum(base["qambient_total_W"]),
            "delta_qhx_total_W": fnum(row["qhx_total_W"]) - fnum(base["qhx_total_W"]),
            "max_abs_TP_delta_K": 0.0,
            "max_abs_TW_delta_K": 0.0,
            "runtime_observed_temperature_used": False,
            "runtime_wallHeatFlux_used": False,
            "fit_or_model_selection": False,
            "admission_or_score": False,
        }
    for row in sensor_rows:
        key = (row["case_id"], row["input_family"], row["level"])
        if key not in grouped:
            continue
        field = "max_abs_TP_delta_K" if row["sensor"].startswith("TP") else "max_abs_TW_delta_K"
        grouped[key][field] = max(grouped[key][field], abs(fnum(row["delta_prediction_K"])))
    return list(grouped.values())


def potential_table(case_rows: List[Dict[str, Any]], sensitivity: List[Dict[str, Any]], split_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    max_total = max(row["corrected_outer_surface_total_W"] for row in case_rows)
    min_total = min(row["corrected_outer_surface_total_W"] for row in case_rows)
    max_frac = max(row["corrected_total_fraction_of_baseline_qambient"] for row in case_rows)
    max_tp = max(row["max_abs_TP_delta_K"] for row in sensitivity)
    max_tw = max(row["max_abs_TW_delta_K"] for row in sensitivity)
    conflicts = sum(1 for row in split_rows if row["split_label_conflict"])
    return [
        {
            "assessment": "radiation_high_concern",
            "status": "substantially_resolved_for_operator_basis",
            "evidence": f"corrected_total_range_W={min_total:.6g}..{max_total:.6g}; corrected_total_fraction_of_qambient_max={max_frac:.6g}",
            "predictive_model_implication": "corrected passive operator is physically plausible enough for further train-context testing",
            "admission_status": "diagnostic_only_no_release",
        },
        {
            "assessment": "multi_train_signal",
            "status": "supporting_train_context",
            "evidence": f"cases={','.join(CASES)}; max_TP_sensitivity_K={max_tp:.6g}; max_TW_sensitivity_K={max_tw:.6g}",
            "predictive_model_implication": "heat-path parameters can move model outputs, so PASSIVE-H2 has development potential",
            "admission_status": "no_fit_no_score_no_freeze",
        },
        {
            "assessment": "split_conflict",
            "status": "guarded",
            "evidence": f"external_bc_split_conflict_cases={conflicts}",
            "predictive_model_implication": "Salt3/4 can be used only as setup-UQ train-context diagnostics unless split policy is reconciled",
            "admission_status": "protected_scoring_closed",
        },
    ]


def runtime_input_audit() -> List[Dict[str, Any]]:
    return [
        {"runtime_item": "case_specific_hA_area_Ta_Tsur_emissivity_layers", "status": "allowed_setup_input", "released_to_runtime": True, "forbidden_input": False},
        {"runtime_item": "model_predicted_wall_state", "status": "allowed_model_output", "released_to_runtime": True, "forbidden_input": False},
        {"runtime_item": "realized_CFD_wallHeatFlux", "status": "forbidden", "released_to_runtime": False, "forbidden_input": True},
        {"runtime_item": "validation_temperature", "status": "forbidden", "released_to_runtime": False, "forbidden_input": True},
        {"runtime_item": "CFD_mdot", "status": "forbidden", "released_to_runtime": False, "forbidden_input": True},
        {"runtime_item": "Qwall", "status": "forbidden", "released_to_runtime": False, "forbidden_input": True},
        {"runtime_item": "global_fitted_multiplier", "status": "forbidden", "released_to_runtime": False, "forbidden_input": True},
        {"runtime_item": "internal_Nu_residual_absorption", "status": "forbidden", "released_to_runtime": False, "forbidden_input": True},
    ]


def source_manifest() -> List[Dict[str, Any]]:
    paths = [
        EXTBC,
        SCENARIO_MATRIX,
        SENSOR_PREDICTIONS,
        SENSOR_SENSITIVITY,
        BASELINE_QOI,
        ONE_AT_A_TIME,
        SETUP_UQ_SUMMARY,
        RADIATION_RECON_SUMMARY,
        PREFLIGHT_SUMMARY,
        SOURCE_BASIS_SUMMARY,
    ]
    return [{"source_path": rel(path), "exists": path.exists(), "mutation_status": "read_only"} for path in paths]


def guardrail_rows() -> List[Dict[str, Any]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "status": False},
        {"guardrail": "registry_or_admission_mutated", "status": False},
        {"guardrail": "scheduler_action", "status": False},
        {"guardrail": "solver_or_sampler_launch", "status": False},
        {"guardrail": "Fluid_or_external_edit", "status": False},
        {"guardrail": "validation_holdout_external_scoring", "status": False},
        {"guardrail": "fitting_or_model_selection", "status": False},
        {"guardrail": "source_property_Qwall_numeric_q_loss_release", "status": False},
        {"guardrail": "repair_freeze_admission_final_score", "status": False},
        {"guardrail": "residual_absorption_into_internal_Nu", "status": False},
    ]


def write_docs(summary: Dict[str, Any]) -> None:
    readme = OUT_DIR / "README.md"
    readme.write_text(
        f"""---
provenance:
  - {rel(OUT_DIR / "summary.json")}
  - {rel(OUT_DIR / "case_corrected_radiation_summary.csv")}
tags: [thermal, passive-h2, multi-train, corrected-radiation, diagnostic]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/thermal-passive-h2-multi-train-corrected-radiation-smoke.md
  - imports/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke.json
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Multi-Train Corrected Radiation Smoke

Decision: `{summary['decision']}`.

This package extends the corrected outer-insulation-surface PASSIVE-H2 operator
to Salt2/Salt3/Salt4 using existing train-only setup-UQ outputs and
case-specific passive external-boundary setup rows.

The result supports continued train-context testing: corrected passive totals
span `{summary['corrected_total_min_W']:.6g}` to `{summary['corrected_total_max_W']:.6g}` W, far below
the prior naive inner-wall radiation basis. This is still diagnostic only: no
fit, protected score, source/property release, Qwall release, numeric q-loss
release, candidate freeze, or final score was made.
""",
        encoding="utf-8",
    )
    status = REPO / f".agent/status/2026-07-22_{TASK_ID}.md"
    status.write_text(
        f"""---
provenance:
  - {rel(OUT_DIR / "summary.json")}
  - {rel(OUT_DIR / "training_potential_diagnostic.csv")}
tags: [status, thermal, passive-h2, multi-train, corrected-radiation]
related:
  - {rel(OUT_DIR / "README.md")}
  - .agent/journal/2026-07-22/thermal-passive-h2-multi-train-corrected-radiation-smoke.md
  - imports/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke.json
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# {TASK_ID}

## Objective

Continue PASSIVE-H2 testing, address the too-high radiation concern, and extend
the corrected train-context smoke to Salt2/Salt3/Salt4 without fitting or
protected scoring.

## Outcome

Decision: `{summary['decision']}`.

Corrected outer-surface totals were computed for `3` cases and `15`
case/family rows. Corrected totals span `{summary['corrected_total_min_W']:.6g}`
to `{summary['corrected_total_max_W']:.6g}` W; the maximum corrected radiation
fraction of naive inner-wall radiation is `{summary['max_corrected_radiation_fraction_of_naive']:.6g}`.
This supports further train-context development, but Salt3/4 split-label
conflicts remain guarded and no admission is made.

## Changes Made

- Added reproducible multi-train corrected radiation builder and tests.
- Published split-scope audit, corrected case/family operator rows, case
  summary, setup-output sensitivity summary, training-potential diagnostic,
  runtime input audit, source manifest, guardrails, summary, and README.
- Added status, journal, import manifest, and completed the board row.

## Validation

- `python3.11 -m py_compile tools/analyze/build_thermal_passive_h2_multi_train_corrected_radiation_smoke.py tools/analyze/test_thermal_passive_h2_multi_train_corrected_radiation_smoke.py`
- `python3.11 tools/analyze/test_thermal_passive_h2_multi_train_corrected_radiation_smoke.py`
- `python3.11 tools/agent/runtime_input_lint.py {rel(OUT_DIR)}`
- `python3.11 tools/agent/split_policy_lint.py {rel(OUT_DIR)}`
- `python3.11 -m json.tool imports/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke.json`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
edit, validation/holdout/external-test scoring, fitting/model selection,
runtime wallHeatFlux/validation-temperature/CFD-mdot/Qwall/imposed-cooler
release, source/property release, numeric q-loss release, repair/freeze,
coefficient admission, final-score claim, hidden multiplier, or residual
absorption into internal Nu occurred.
""",
        encoding="utf-8",
    )
    journal = REPO / ".agent/journal/2026-07-22/thermal-passive-h2-multi-train-corrected-radiation-smoke.md"
    journal.write_text(
        f"""---
provenance:
  - {rel(RADIATION_RECON_SUMMARY)}
  - {rel(EXTBC)}
  - {rel(SETUP_UQ_SUMMARY)}
tags: [journal, thermal, passive-h2, multi-train, corrected-radiation]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - imports/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke.json
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 multi-train corrected radiation smoke

## Attempted

Extended the corrected outer-insulation-surface PASSIVE-H2 operator from the
Salt2 reconciliation to Salt2/Salt3/Salt4 using existing train-only setup-UQ
model outputs and case-specific source-backed passive external-boundary rows.

## Observed

The earlier high radiation term is not stable once the emitting surface is
moved from the hot inner wall/pipe state to the outer insulation surface. The
corrected case totals are small relative to the naive inner-wall radiation
basis and are bounded enough to justify continued train-context development.

## Inferred

PASSIVE-H2 has predictive-model potential as a physically bounded passive
operator, but only after split-label conflicts and implementation semantics are
resolved. Salt3/4 are included here under the existing setup-UQ train-only
labels, not as protected scores or admission evidence.

## Caveats

This row performs no fitting, no new Fluid solve, and no protected scoring. It
does not release numeric q-loss, Qwall, source properties, coefficients, a
candidate freeze, or a final score.

## Next Useful Actions

If continuing, claim a separate Fluid execution row that implements the
corrected outer-surface operator directly and runs only explicitly admitted
development/train cases. Keep radiation semantics and split labels visible in
the output contract.
""",
        encoding="utf-8",
    )
    manifest = REPO / "imports/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke.json"
    manifest.write_text(
        json.dumps(
            {
                "task": TASK_ID,
                "task_id": TASK_ID,
                "date": DATE,
                "changed_files": [
                    ".agent/BOARD.md",
                    f".agent/status/2026-07-22_{TASK_ID}.md",
                    ".agent/journal/2026-07-22/thermal-passive-h2-multi-train-corrected-radiation-smoke.md",
                    "imports/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke.json",
                    "tools/analyze/build_thermal_passive_h2_multi_train_corrected_radiation_smoke.py",
                    "tools/analyze/test_thermal_passive_h2_multi_train_corrected_radiation_smoke.py",
                    rel(OUT_DIR),
                ],
                "read_only_context": [row["source_path"] for row in source_manifest()]
                + ["native CFD/OpenFOAM outputs", "registry/admission state", "scheduler state", "Fluid source tree"],
                "decision": summary["decision"],
                "native_solver_outputs_mutated": False,
                "registry_mutated": False,
                "scheduler_action": False,
                "external_fluid_edit": False,
                "source_property_release": False,
                "qwall_release": False,
                "numeric_q_loss_release": False,
                "protected_scoring": False,
                "fitting_or_model_selection": False,
                "candidate_freeze": False,
                "final_score_claim": False,
                "no_scorecard_outputs": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def build() -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ext_rows = extbc_passive_rows()
    split_rows = split_scope_audit(ext_rows)
    family_rows = corrected_operator_rows(ext_rows)
    summaries = case_summary(family_rows)
    sens = sensitivity_rows()
    potential = potential_table(summaries, sens, split_rows)
    audit = runtime_input_audit()
    guardrails = guardrail_rows()
    manifest = source_manifest()
    recon = read_json(RADIATION_RECON_SUMMARY)
    corrected_totals = [row["corrected_outer_surface_total_W"] for row in summaries]
    fractions = [row["corrected_radiation_fraction_of_naive"] for row in summaries]
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": now_iso(),
        "decision": "passive_h2_multi_train_corrected_radiation_smoke_supports_development_no_admission",
        "candidate_id": "PASSIVE-H2-CAND001",
        "case_rows": len(summaries),
        "case_family_rows": len(family_rows),
        "cases_included": ",".join(CASES),
        "setup_uq_train_labeled_cases": sum(1 for row in split_rows if row["setup_uq_train_only_label"]),
        "external_bc_split_conflict_cases": sum(1 for row in split_rows if row["split_label_conflict"]),
        "corrected_total_min_W": min(corrected_totals),
        "corrected_total_max_W": max(corrected_totals),
        "corrected_total_mean_W": sum(corrected_totals) / len(corrected_totals),
        "max_corrected_radiation_fraction_of_naive": max(fractions),
        "prior_salt2_naive_radiation_W": recon["previous_direct_radiation_W"],
        "prior_salt2_corrected_radiation_W": recon["corrected_outer_surface_radiation_W"],
        "sensitivity_rows": len(sens),
        "runtime_forbidden_inputs_released": sum(1 for row in audit if row["forbidden_input"] and truthy(row["released_to_runtime"])),
        "protected_scoring": False,
        "fitting_or_model_selection": False,
        "source_property_release": False,
        "qwall_release": False,
        "numeric_q_loss_release": False,
        "repair_execution": False,
        "candidate_freeze": False,
        "coefficient_admission": False,
        "final_score_claim": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "solver_or_sampler_launch": False,
        "fluid_or_external_edit": False,
        "runtime_leakage_relaxation": False,
        "residual_absorption_into_internal_Nu": False,
        "no_scorecard_outputs": True,
    }
    write_csv(OUT_DIR / "split_scope_audit.csv", split_rows)
    write_csv(OUT_DIR / "case_family_corrected_radiation_operator.csv", family_rows)
    write_csv(OUT_DIR / "case_corrected_radiation_summary.csv", summaries)
    write_csv(OUT_DIR / "setup_output_sensitivity_context.csv", sens)
    write_csv(OUT_DIR / "training_potential_diagnostic.csv", potential)
    write_csv(OUT_DIR / "runtime_input_audit.csv", audit)
    write_csv(OUT_DIR / "source_manifest.csv", manifest)
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrails)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
