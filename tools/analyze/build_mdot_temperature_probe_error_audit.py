#!/usr/bin/env python3
"""Build a Salt1-4 mdot and TP/TW 1D predictivity audit."""
from __future__ import annotations

import argparse
import csv
import html
import json
import math
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TASK = "AGENT-360"
DATE = "2026-07-14"
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit"

FLUID_ROOT = (ROOT / "../cfd-modeling-tools/tamu_first_order_model/Fluid").resolve()
if str(FLUID_ROOT) not in sys.path:
    sys.path.insert(0, str(FLUID_ROOT))

from tamu_loop_model_v2 import config_loader, solver as S  # noqa: E402

from tools.analyze import run_cfd_informed_fixed_mdot_1d_replays as fixed_replay  # noqa: E402


FLUID_CASES = FLUID_ROOT / "configs/cases.yaml"
FLUID_SCENARIOS = FLUID_ROOT / "configs/scenarios.yaml"
FLUID_CAMPAIGNS = FLUID_ROOT / "configs/campaigns.yaml"
SECTION_HEAT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv"
PARITY_CONTRACT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/parity_input_contract.csv"
THERMAL_TARGETS = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv"
CFD_SENSOR_REFERENCE = ROOT / "reports/2026-07/2026-07-01/2026-07-01_local_1d_validation_refresh/cfd_sensor_reference.csv"
CASE_ADMISSION = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_cfd_case_admission_inventory/cfd_case_admission_inventory.csv"
FLOW_BC_MATRIX = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_flow_rate_temperature_bc_response_study/case_bc_response_matrix.csv"
FORWARD_MAP = ROOT / "operational_notes/maps/forward-predictive-model.md"
THERMAL_RADIATION_MAP = ROOT / "operational_notes/maps/thermal-boundary-and-radiation.md"

CASE_SPECS = [
    {
        "case_id": "salt_1",
        "fluid_case_name": "Salt 1",
        "source_id": "viscosity_screening_salt_test_1_jin_coarse_mesh",
        "preferred_flow_case_key": "salt1_jin_nominal_continuation_corrected",
        "split": "diagnostic-only",
        "admission_use_class": "diagnostic_context_only",
        "fit_use": "no",
        "notes": "Salt1 lacks current admitted patch heat ledger and explicit Salt1 split policy.",
    },
    {
        "case_id": "salt_2",
        "fluid_case_name": "Salt 2",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "preferred_flow_case_key": "salt2_jin",
        "split": "train",
        "admission_use_class": "train_candidate",
        "fit_use": "yes",
        "notes": "Current single training row.",
    },
    {
        "case_id": "salt_3",
        "fluid_case_name": "Salt 3",
        "source_id": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "preferred_flow_case_key": "salt3_jin",
        "split": "validation",
        "admission_use_class": "validation_candidate",
        "fit_use": "no",
        "notes": "Held for validation under current split.",
    },
    {
        "case_id": "salt_4",
        "fluid_case_name": "Salt 4",
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "preferred_flow_case_key": "salt4_jin",
        "split": "holdout",
        "admission_use_class": "holdout_candidate",
        "fit_use": "no",
        "notes": "Held for final holdout under current split.",
    },
]

MODE_COLUMNS = [
    "mode_id", "part", "description", "solver_policy", "runtime_input_policy", "predictivity_class",
    "uses_cfd_mdot_runtime", "uses_realized_cfd_wallHeatFlux_runtime", "closure_terms", "assumption_ids",
    "status",
]
CASE_COLUMNS = [
    "case_id", "fluid_case_name", "source_id", "split", "admission_use_class", "fit_use",
    "cfd_mdot_kg_s", "cfd_Tmean_K", "cfd_loop_delta_T_K", "heater_power_W", "test_section_power_W",
    "boundary_ambient_Ta_K", "has_patch_heat_ledger", "has_cfd_sensor_reference", "notes", "source_paths",
]
ASSUMPTION_COLUMNS = [
    "assumption_id", "topic", "statement", "applies_to_modes", "source_path", "risk_or_consequence",
]
RESULT_COLUMNS = [
    "case_id", "mode_id", "part", "predictivity_class", "result_status", "root_status",
    "admission_use_class", "split", "mdot_pred_kg_s", "cfd_mdot_kg_s", "mdot_error_kg_s",
    "mdot_error_pct", "model_Tmean_K", "cfd_Tmean_K", "Tmean_error_K", "model_loop_delta_T_K",
    "cfd_loop_delta_T_K", "loop_delta_error_K", "qhx_total_W", "qambient_total_W",
    "source_total_W", "prescribed_loss_total_W", "pressure_residual_Pa", "temperature_periodicity_error_K",
    "runtime_input_policy", "closure_terms", "assumption_ids", "source_paths", "blocked_reason",
]
SENSOR_COLUMNS = [
    "case_id", "mode_id", "part", "sensor", "kind", "predicted_K", "target_K", "error_K",
    "abs_error_K", "prediction_source_segment", "prediction_source_fraction", "target_provenance",
    "admission_use_class", "assumption_ids", "notes",
]
TEMP_SUMMARY_COLUMNS = [
    "case_id", "mode_id", "part", "kind", "n_compared", "rmse_K", "mae_K", "mean_error_K",
    "max_abs_error_K", "missing_prediction_count", "missing_target_count",
]
HEAT_SCORE_COLUMNS = [
    "part", "leg", "model_form", "case_id", "split", "admission_use_class", "q_pred_W", "q_cfd_W",
    "error_W", "abs_error_W", "fit_policy", "model_assumptions", "source_paths",
]
HEAT_SUMMARY_COLUMNS = [
    "part", "leg", "model_form", "scope", "n_rows", "rmse_W", "mae_W", "mean_error_W",
    "fit_policy", "interpretation",
]
CORRELATION_COLUMNS = [
    "scope", "part", "mode_id", "kind", "n_pairs", "x_metric", "y_metric", "pearson_r",
    "slope_K_per_kg_s", "mean_abs_mdot_error_kg_s", "mean_probe_rmse_K", "interpretation",
]
TREND_COLUMNS = [
    "finding_id", "topic", "observation", "evidence_file", "cases_or_scope",
    "interpretation", "next_action",
]
MANIFEST_COLUMNS = ["path", "exists", "role"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return "" if not math.isfinite(value) else f"{value:.12g}"
    return str(value)


def fnum(value: Any) -> float | None:
    if value in ("", None, "nan", "NaN"):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def fmt(value: Any, digits: int = 6) -> str:
    parsed = fnum(value)
    if parsed is None:
        return ""
    return f"{parsed:.{digits}f}".rstrip("0").rstrip(".")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def mean(values: Iterable[float]) -> float | None:
    vals = [v for v in values if math.isfinite(v)]
    return sum(vals) / len(vals) if vals else None


def rmse(values: Iterable[float]) -> float | None:
    vals = [v for v in values if math.isfinite(v)]
    return math.sqrt(sum(v * v for v in vals) / len(vals)) if vals else None


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    xbar = mean(xs)
    ybar = mean(ys)
    if xbar is None or ybar is None:
        return None
    dx = [x - xbar for x in xs]
    dy = [y - ybar for y in ys]
    denom = math.sqrt(sum(x * x for x in dx) * sum(y * y for y in dy))
    return sum(x * y for x, y in zip(dx, dy)) / denom if denom else None


def slope(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    xbar = mean(xs)
    ybar = mean(ys)
    if xbar is None or ybar is None:
        return None
    denom = sum((x - xbar) ** 2 for x in xs)
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom if denom else None


def git_revision(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return ""
    return result.stdout.strip()


def mode_rows() -> list[dict[str, str]]:
    return [
        {
            "mode_id": "M1_full_cfd_segment_heat_flux_pressure_root",
            "part": "part1",
            "description": "Prescribe full CFD realized segment heat ledger and solve mdot from pressure balance.",
            "solver_policy": "pressure_root_fast_scan",
            "runtime_input_policy": "CFD realized heat fluxes consumed as diagnostic upper-bound inputs; CFD mdot joined only after solve.",
            "predictivity_class": "diagnostic_cfd_informed_upper_bound",
            "uses_cfd_mdot_runtime": "no",
            "uses_realized_cfd_wallHeatFlux_runtime": "yes",
            "closure_terms": "Fluid geometry; default MinorLosses; default friction closure; prescribed CFD heat sources/losses.",
            "assumption_ids": "A001;A002;A003;A006;A009",
            "status": "execute_when_patch_heat_available",
        },
        {
            "mode_id": "M1b_full_cfd_segment_heat_flux_fixed_mdot",
            "part": "part1",
            "description": "Same full CFD heat ledger, but CFD mdot is imposed to isolate thermal/sensor error.",
            "solver_policy": "fixed_cfd_mdot_pressure_residual_diagnostic",
            "runtime_input_policy": "CFD mdot and realized heat fluxes consumed; thermal diagnostic only.",
            "predictivity_class": "diagnostic_fixed_mdot_thermal_isolation",
            "uses_cfd_mdot_runtime": "yes",
            "uses_realized_cfd_wallHeatFlux_runtime": "yes",
            "closure_terms": "Fluid thermal periodicity; default MinorLosses pressure residual only; full prescribed CFD heat losses.",
            "assumption_ids": "A001;A002;A003;A004;A006;A009",
            "status": "execute_when_patch_heat_and_mdot_available",
        },
        {
            "mode_id": "M2_cfd_heater_test_section_cooler_pressure_root",
            "part": "part2",
            "description": "Prescribe CFD heater, test-section net sink, and cooler heat removal; solve mdot.",
            "solver_policy": "pressure_root_fast_scan",
            "runtime_input_policy": "CFD heater/test/cooler heat terms consumed; CFD mdot joined only after solve.",
            "predictivity_class": "diagnostic_cfd_informed_boundary_subset",
            "uses_cfd_mdot_runtime": "no",
            "uses_realized_cfd_wallHeatFlux_runtime": "yes",
            "closure_terms": "Imposed qhx for cooler; negative test-section source to preserve current passive model; default friction/minor losses.",
            "assumption_ids": "A001;A002;A003;A005;A006;A009",
            "status": "execute_when_patch_heat_available",
        },
        {
            "mode_id": "M3_cfd_heater_cooler_pressure_root",
            "part": "part3",
            "description": "Prescribe CFD heater and cooler heat removal only; solve mdot.",
            "solver_policy": "pressure_root_fast_scan",
            "runtime_input_policy": "CFD heater/cooler heat terms consumed; CFD mdot joined only after solve.",
            "predictivity_class": "diagnostic_cfd_informed_boundary_subset",
            "uses_cfd_mdot_runtime": "no",
            "uses_realized_cfd_wallHeatFlux_runtime": "yes",
            "closure_terms": "Imposed qhx for cooler; no CFD test-section term; default friction/minor losses.",
            "assumption_ids": "A001;A002;A003;A006;A009",
            "status": "execute_when_patch_heat_available",
        },
    ]


def assumption_rows() -> list[dict[str, str]]:
    return [
        {
            "assumption_id": "A001",
            "topic": "wallHeatFlux sign",
            "statement": "Positive CFD wallHeatFlux means heat enters the fluid; negative means heat leaves the fluid.",
            "applies_to_modes": "all CFD heat modes",
            "source_path": rel(SECTION_HEAT),
            "risk_or_consequence": "Wrong sign reverses heater/cooler/test-section interpretation.",
        },
        {
            "assumption_id": "A002",
            "topic": "radiation",
            "statement": "CFD rcExternalTemperature includes radiation in total wallHeatFlux; current CFD exports no separate qr.",
            "applies_to_modes": "all",
            "source_path": rel(THERMAL_RADIATION_MAP),
            "risk_or_consequence": "Do not double count radiation as a separate 1D term when prescribing CFD heat flux.",
        },
        {
            "assumption_id": "A003",
            "topic": "runtime discipline",
            "statement": "Realized CFD wallHeatFlux is diagnostic evidence unless a mode explicitly declares itself CFD-informed.",
            "applies_to_modes": "all",
            "source_path": rel(FORWARD_MAP),
            "risk_or_consequence": "CFD-informed modes are not final setup-only predictions.",
        },
        {
            "assumption_id": "A004",
            "topic": "fixed mdot",
            "statement": "Fixed-mdot modes impose CFD mdot and therefore isolate thermal/sensor behavior only.",
            "applies_to_modes": "M1b;part4;part5",
            "source_path": rel(THERMAL_TARGETS),
            "risk_or_consequence": "Do not use fixed-mdot rows as hydraulic predictivity evidence.",
        },
        {
            "assumption_id": "A005",
            "topic": "test-section sink encoding",
            "statement": "For M2, CFD test-section net loss is encoded as a negative source to preserve current Fluid passive boundary behavior.",
            "applies_to_modes": "M2",
            "source_path": rel(SECTION_HEAT),
            "risk_or_consequence": "This is a compatibility representation, not a first-class external boundary model.",
        },
        {
            "assumption_id": "A006",
            "topic": "sensor targets",
            "statement": "TP targets use CFD core/bulk probe references; TW targets use CFD wall-area-average probe references.",
            "applies_to_modes": "all sensor-scored modes",
            "source_path": rel(CFD_SENSOR_REFERENCE),
            "risk_or_consequence": "Sensor-coordinate uncertainty remains a score limitation.",
        },
        {
            "assumption_id": "A007",
            "topic": "split discipline",
            "statement": "Salt2 is the current train row, Salt3 validation, Salt4 holdout, and Salt1 diagnostic/context only.",
            "applies_to_modes": "all",
            "source_path": rel(CASE_ADMISSION),
            "risk_or_consequence": "No model form is fit on validation or holdout rows.",
        },
        {
            "assumption_id": "A008",
            "topic": "Salt1",
            "statement": "Salt1 has sensor and Fluid setup references but lacks a current admitted Salt1 patch heat ledger in the consumed source set.",
            "applies_to_modes": "all Salt1 rows",
            "source_path": rel(FLOW_BC_MATRIX),
            "risk_or_consequence": "Salt1 is reported as diagnostic and blocked for CFD heat-flux modes.",
        },
        {
            "assumption_id": "A009",
            "topic": "closures",
            "statement": "Fluid default geometry, default MinorLosses, default friction closure, 1.0 inch insulation, and current solver thermal model are used unless the mode says otherwise.",
            "applies_to_modes": "all executed Fluid modes",
            "source_path": str(FLUID_ROOT),
            "risk_or_consequence": "This is an audit of the current 1D model, not a new closure calibration.",
        },
    ]


def rows_by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def load_targets() -> dict[str, dict[str, str]]:
    targets = rows_by_key(read_csv(THERMAL_TARGETS), "case_id")
    flow = rows_by_key(read_csv(FLOW_BC_MATRIX), "case_key")
    for spec in CASE_SPECS:
        case_id = spec["case_id"]
        if case_id in targets:
            continue
        flow_row = flow.get(spec["preferred_flow_case_key"], {})
        if not flow_row:
            continue
        targets[case_id] = {
            "case_id": case_id,
            "source_id": spec["source_id"],
            "cfd_mdot_kg_s": flow_row.get("mdot_mean_abs_kg_s", ""),
            "cfd_Tmean_K": flow_row.get("timeseries_probe_T_avg_K", ""),
            "cfd_loop_delta_T_K": "",
            "heater_imposed_duty_W": flow_row.get("heater_power_W", ""),
            "heater_wallHeatFlux_W": "",
            "cooler_removed_duty_W": flow_row.get("cooling_power_W", ""),
            "cooler_wallHeatFlux_W": "",
            "test_section_wallHeatFlux_W": "",
        }
    return targets


def sensor_case_from_label(label: str) -> str:
    text = label.replace(" Val", "").replace(" Jin", "").replace(" Kirst", "").strip()
    return {"Salt 1": "salt_1", "Salt 2": "salt_2", "Salt 3": "salt_3", "Salt 4": "salt_4"}.get(text, "")


def load_sensor_refs() -> dict[tuple[str, str], dict[str, str]]:
    refs: dict[tuple[str, str], dict[str, str]] = {}
    priority = {"Jin": 3, "Val": 2, "Kirst": 1}
    seen_priority: dict[tuple[str, str], int] = {}
    for row in read_csv(CFD_SENSOR_REFERENCE):
        case_id = sensor_case_from_label(row.get("frozen_case_label", ""))
        sensor = row.get("sensor", "")
        if not case_id or not sensor:
            continue
        label = row.get("frozen_case_label", "")
        row_priority = next((value for tag, value in priority.items() if tag in label), 0)
        key = (case_id, sensor)
        if row_priority >= seen_priority.get(key, -1):
            refs[key] = row
            seen_priority[key] = row_priority
    return refs


def heat_rows_by_case() -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(SECTION_HEAT):
        grouped[row["case_id"]].append(row)
    return grouped


def heat_terms(rows: list[dict[str, str]]) -> dict[str, float]:
    terms = {
        "heater_W": 0.0,
        "test_loss_W": 0.0,
        "cooler_loss_W": 0.0,
        "ambient_loss_W": 0.0,
        "junction_loss_W": 0.0,
        "heater_power_W": 0.0,
        "cooler_imposed_loss_W": 0.0,
    }
    for row in rows:
        role = row.get("role", "")
        source = fnum(row.get("realized_source_W")) or 0.0
        loss = fnum(row.get("realized_loss_W")) or 0.0
        imposed_source = fnum(row.get("imposed_source_W")) or 0.0
        imposed_loss = fnum(row.get("imposed_loss_W")) or 0.0
        if role == "heater":
            terms["heater_W"] += source
            terms["heater_power_W"] += imposed_source
        elif role == "test_section":
            terms["test_loss_W"] += loss
        elif role == "cooler":
            terms["cooler_loss_W"] += loss
            terms["cooler_imposed_loss_W"] += imposed_loss
        elif role == "ambient_wall":
            terms["ambient_loss_W"] += loss
        elif role == "junction_other":
            terms["junction_loss_W"] += loss
    return terms


def loss_map(rows: list[dict[str, str]], roles: set[str]) -> dict[str, float]:
    losses: dict[str, float] = {}
    for row in rows:
        if row.get("role") not in roles:
            continue
        loss = fnum(row.get("realized_loss_W")) or 0.0
        parent = row.get("fluid_parent_segment", "")
        if loss <= 0.0 or not parent:
            continue
        losses[parent] = losses.get(parent, 0.0) + loss
    return losses


def base_scenario(case_row: dict[str, Any], *, name: str, imposed_qhx_W: float, radiation_on: bool = False) -> Any:
    ambient = fnum(case_row.get("boundary_ambient_Ta_K")) or fnum(case_row.get("air_T_inlet_K")) or 300.0
    return S.ScenarioConfig(
        name=name,
        ambient_temperature_K=ambient,
        insulation_thickness_in=1.0,
        radiation_on=radiation_on,
        model_mode="imposed_qhx",
        imposed_qhx_W=imposed_qhx_W,
        air_counterflow=True,
        max_outer_iterations=80,
        mdot_search_lower_kg_s=0.005,
        mdot_search_upper_kg_s=0.05,
    )


def predictive_hx_scenario(case_row: dict[str, Any]) -> Any:
    ambient = fnum(case_row.get("boundary_ambient_Ta_K")) or fnum(case_row.get("air_T_inlet_K")) or 300.0
    return S.ScenarioConfig(
        name="cooling_leg_current_fluid_airside_hx",
        ambient_temperature_K=ambient,
        insulation_thickness_in=1.0,
        radiation_on=True,
        model_mode="predictive_airside_hx",
        air_counterflow=True,
        max_outer_iterations=80,
        mdot_search_lower_kg_s=0.005,
        mdot_search_upper_kg_s=0.05,
    )


def solver_segments(case: Any, scenario: Any) -> tuple[list[Any], list[Any], list[Any]]:
    segments, sensors = S.build_geometry(refinement=S.default_geometry_refinement())
    return segments, sensors, fixed_replay.scenario_segments_for_solver(S, segments, case, scenario)


def pressure_eval(
    mdot: float,
    case: Any,
    scenario: Any,
    prescribed_sources: dict[str, float] | None,
    prescribed_losses: dict[str, float] | None,
    warm_start: float | None = None,
) -> dict[str, Any]:
    _segments, sensors, scenario_segments = solver_segments(case, scenario)
    return S.pressure_residual(
        mdot,
        case,
        scenario_segments,
        sensors,
        scenario,
        S.MinorLosses(),
        warm_start_temperature_K=warm_start,
        prescribed_segment_sources_W=prescribed_sources,
        prescribed_segment_losses_W=prescribed_losses,
    )


def make_result(snapshot: dict[str, Any], case: Any, scenario: Any, status: str, reason: str = "") -> Any:
    thermal = snapshot["thermal"]
    segments, sensors, _scenario_segments = solver_segments(case, scenario)
    return SimpleNamespace(
        scenario=scenario,
        case=case,
        mdot_kg_s=float(snapshot["mdot_kg_s"]),
        velocity_main_m_s=float(snapshot.get("velocity_main_m_s", float("nan"))),
        reynolds_main=float(snapshot.get("reynolds_main", float("nan"))),
        deltaP_buoyancy_Pa=float(snapshot["deltaP_buoyancy_Pa"]),
        deltaP_losses_Pa=float(snapshot["deltaP_losses_Pa"]),
        pressure_residual_Pa=float(snapshot["pressure_residual_Pa"]),
        qhx_total_W=float(thermal.qhx_total_W),
        qambient_total_W=float(thermal.qambient_total_W),
        start_temperature_K=float(thermal.start_temperature_K),
        end_temperature_K=float(thermal.end_temperature_K),
        temperature_periodicity_error_K=float(thermal.temperature_periodicity_error_K),
        sensor_predictions_K=thermal.sensor_predictions_K,
        sensor_prediction_provenance=thermal.sensor_prediction_provenance,
        segment_states=thermal.segment_states,
        geometry_segments=segments,
        geometry_sensors=sensors,
        root_status=status,
        root_rejection_reason=reason,
        accepted_for_validation=status in {"fast_scan_bracketed_pressure_root", "fixed_cfd_mdot_evaluated"},
    )


def fast_pressure_root(case: Any, scenario: Any, sources: dict[str, float] | None, losses: dict[str, float] | None) -> Any:
    grid = [0.005, 0.01, 0.015, 0.02, 0.03, 0.05]
    evaluations = [pressure_eval(mdot, case, scenario, sources, losses) for mdot in grid]
    finite = [row for row in evaluations if math.isfinite(float(row["pressure_residual_Pa"]))]
    if not finite:
        raise ValueError(f"no finite pressure residuals for {case.name} {scenario.name}")
    bracket: tuple[dict[str, Any], dict[str, Any]] | None = None
    for prev, curr in zip(finite[:-1], finite[1:]):
        r0 = float(prev["pressure_residual_Pa"])
        r1 = float(curr["pressure_residual_Pa"])
        if r0 == 0.0 or r0 * r1 <= 0.0:
            bracket = (prev, curr)
            break
    if bracket is None:
        selected = min(finite, key=lambda row: abs(float(row["pressure_residual_Pa"])))
        return make_result(selected, case, scenario, "fast_scan_best_residual_no_pressure_bracket", "no_bracketed_pressure_root")
    lo, hi = bracket
    mdot_lo = float(lo["mdot_kg_s"])
    mdot_hi = float(hi["mdot_kg_s"])
    r_lo = float(lo["pressure_residual_Pa"])
    selected = min((lo, hi), key=lambda row: abs(float(row["pressure_residual_Pa"])))
    for _ in range(5):
        mid = 0.5 * (mdot_lo + mdot_hi)
        snap = pressure_eval(mid, case, scenario, sources, losses, warm_start=float(selected["thermal"].start_temperature_K))
        r_mid = float(snap["pressure_residual_Pa"])
        selected = snap
        if r_lo * r_mid <= 0.0:
            mdot_hi = mid
        else:
            mdot_lo = mid
            r_lo = r_mid
    return make_result(selected, case, scenario, "fast_scan_bracketed_pressure_root")


def fixed_mdot_eval(case: Any, scenario: Any, mdot: float, sources: dict[str, float] | None, losses: dict[str, float] | None) -> Any:
    snap = pressure_eval(mdot, case, scenario, sources, losses)
    return make_result(snap, case, scenario, "fixed_cfd_mdot_evaluated")


def length_weighted_mean(states: list[Any]) -> float:
    denom = 0.0
    num = 0.0
    for state in states:
        length = max(float(state.s_end_m) - float(state.s_start_m), 0.0)
        denom += length
        num += length * float(state.T_avg_K)
    return num / denom if denom > 0 else float("nan")


def loop_delta(states: list[Any]) -> float:
    vals = [float(s.T_avg_K) for s in states if math.isfinite(float(s.T_avg_K))]
    return max(vals) - min(vals) if vals else float("nan")


def case_rows(targets: dict[str, dict[str, str]], sensor_refs: dict[tuple[str, str], dict[str, str]], heat_by_case: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    cases = {case.name: case for case in config_loader.load_cases()}
    out: list[dict[str, Any]] = []
    for spec in CASE_SPECS:
        target = targets.get(spec["case_id"], {})
        case = cases[spec["fluid_case_name"]]
        out.append(
            {
                **spec,
                "cfd_mdot_kg_s": target.get("cfd_mdot_kg_s", ""),
                "cfd_Tmean_K": target.get("cfd_Tmean_K", ""),
                "cfd_loop_delta_T_K": target.get("cfd_loop_delta_T_K", ""),
                "heater_power_W": case.heater_power_W,
                "test_section_power_W": case.test_section_power_W,
                "boundary_ambient_Ta_K": target.get("boundary_ambient_Ta_K", case.air_T_inlet_K),
                "has_patch_heat_ledger": "yes" if heat_by_case.get(spec["case_id"]) else "no",
                "has_cfd_sensor_reference": "yes" if any(k[0] == spec["case_id"] for k in sensor_refs) else "no",
                "source_paths": ";".join([rel(THERMAL_TARGETS), rel(FLOW_BC_MATRIX), rel(CASE_ADMISSION)]),
            }
        )
    return out


def mode_setup(case_row: dict[str, Any], mode_id: str, rows: list[dict[str, str]]) -> tuple[Any, dict[str, float] | None, dict[str, float] | None, str, str]:
    terms = heat_terms(rows)
    if mode_id in {"M1_full_cfd_segment_heat_flux_pressure_root", "M1b_full_cfd_segment_heat_flux_fixed_mdot"}:
        scenario = base_scenario(case_row, name=mode_id, imposed_qhx_W=0.0, radiation_on=False)
        return scenario, {"heated_incline": terms["heater_W"]}, loss_map(rows, {"cooler", "test_section", "ambient_wall", "junction_other"}), str(terms["heater_W"]), str(sum(loss_map(rows, {"cooler", "test_section", "ambient_wall", "junction_other"}).values()))
    if mode_id == "M2_cfd_heater_test_section_cooler_pressure_root":
        scenario = base_scenario(case_row, name=mode_id, imposed_qhx_W=terms["cooler_loss_W"], radiation_on=False)
        return scenario, {"heated_incline": terms["heater_W"], "test_section": -terms["test_loss_W"]}, None, str(terms["heater_W"] - terms["test_loss_W"]), "0"
    if mode_id == "M3_cfd_heater_cooler_pressure_root":
        scenario = base_scenario(case_row, name=mode_id, imposed_qhx_W=terms["cooler_loss_W"], radiation_on=False)
        return scenario, {"heated_incline": terms["heater_W"]}, None, str(terms["heater_W"]), "0"
    raise ValueError(mode_id)


def result_row(result: Any, case_row: dict[str, Any], mode: dict[str, str], source_total: str, loss_total: str, source_paths: str) -> dict[str, Any]:
    cfd_mdot = fnum(case_row.get("cfd_mdot_kg_s"))
    cfd_tmean = fnum(case_row.get("cfd_Tmean_K"))
    cfd_dt = fnum(case_row.get("cfd_loop_delta_T_K"))
    mdot = float(result.mdot_kg_s)
    tmean = length_weighted_mean(result.segment_states)
    dt = loop_delta(result.segment_states)
    return {
        "case_id": case_row["case_id"],
        "mode_id": mode["mode_id"],
        "part": mode["part"],
        "predictivity_class": mode["predictivity_class"],
        "result_status": "executed",
        "root_status": result.root_status,
        "admission_use_class": case_row["admission_use_class"],
        "split": case_row["split"],
        "mdot_pred_kg_s": mdot,
        "cfd_mdot_kg_s": cfd_mdot,
        "mdot_error_kg_s": mdot - cfd_mdot if cfd_mdot is not None and "fixed_mdot" not in mode["mode_id"] else (0.0 if cfd_mdot is not None and "fixed_mdot" in mode["mode_id"] else ""),
        "mdot_error_pct": ((mdot - cfd_mdot) / cfd_mdot * 100.0) if cfd_mdot not in {None, 0.0} and "fixed_mdot" not in mode["mode_id"] else (0.0 if cfd_mdot is not None and "fixed_mdot" in mode["mode_id"] else ""),
        "model_Tmean_K": tmean,
        "cfd_Tmean_K": cfd_tmean,
        "Tmean_error_K": tmean - cfd_tmean if cfd_tmean is not None else "",
        "model_loop_delta_T_K": dt,
        "cfd_loop_delta_T_K": cfd_dt,
        "loop_delta_error_K": dt - cfd_dt if cfd_dt is not None else "",
        "qhx_total_W": result.qhx_total_W,
        "qambient_total_W": result.qambient_total_W,
        "source_total_W": source_total,
        "prescribed_loss_total_W": loss_total,
        "pressure_residual_Pa": result.pressure_residual_Pa,
        "temperature_periodicity_error_K": result.temperature_periodicity_error_K,
        "runtime_input_policy": mode["runtime_input_policy"],
        "closure_terms": mode["closure_terms"],
        "assumption_ids": mode["assumption_ids"],
        "source_paths": source_paths,
        "blocked_reason": "",
    }


def blocked_result(case_row: dict[str, Any], mode: dict[str, str], reason: str) -> dict[str, Any]:
    return {
        "case_id": case_row["case_id"],
        "mode_id": mode["mode_id"],
        "part": mode["part"],
        "predictivity_class": mode["predictivity_class"],
        "result_status": "blocked_missing_inputs",
        "root_status": "",
        "admission_use_class": case_row["admission_use_class"],
        "split": case_row["split"],
        "runtime_input_policy": mode["runtime_input_policy"],
        "closure_terms": mode["closure_terms"],
        "assumption_ids": mode["assumption_ids"] + ";A008",
        "source_paths": case_row["source_paths"],
        "blocked_reason": reason,
    }


def sensor_rows_for_result(result: Any, case_row: dict[str, Any], mode: dict[str, str], refs: dict[tuple[str, str], dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sensor in result.geometry_sensors:
        ref = refs.get((case_row["case_id"], sensor.name), {})
        predicted = fnum(result.sensor_predictions_K.get(sensor.name))
        target = fnum(ref.get("reference_k"))
        prov = result.sensor_prediction_provenance.get(sensor.name, {})
        rows.append(
            {
                "case_id": case_row["case_id"],
                "mode_id": mode["mode_id"],
                "part": mode["part"],
                "sensor": sensor.name,
                "kind": sensor.kind,
                "predicted_K": predicted,
                "target_K": target,
                "error_K": predicted - target if predicted is not None and target is not None else "",
                "abs_error_K": abs(predicted - target) if predicted is not None and target is not None else "",
                "prediction_source_segment": prov.get("source_segment", ""),
                "prediction_source_fraction": prov.get("source_fraction", ""),
                "target_provenance": rel(CFD_SENSOR_REFERENCE) if ref else "",
                "admission_use_class": case_row["admission_use_class"],
                "assumption_ids": "A006;A007",
                "notes": "CFD sensor target joined after solve" if ref else "missing current CFD sensor reference",
            }
        )
    return rows


def run_model_modes(case_table: list[dict[str, Any]], execute_fluid: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    heat_by = heat_rows_by_case()
    refs = load_sensor_refs()
    cases = {case.name: case for case in config_loader.load_cases()}
    modes = mode_rows()
    results: list[dict[str, Any]] = []
    sensors: list[dict[str, Any]] = []
    for case_row in case_table:
        rows = heat_by.get(case_row["case_id"], [])
        for mode in modes:
            if not rows:
                results.append(blocked_result(case_row, mode, "No current section_heat_balance patch heat ledger for this case."))
                continue
            if not execute_fluid:
                results.append(blocked_result(case_row, mode, "Fluid execution disabled for lightweight validation."))
                continue
            scenario, sources, losses, source_total, loss_total = mode_setup(case_row, mode["mode_id"], rows)
            case = cases[case_row["fluid_case_name"]]
            cfd_mdot = fnum(case_row.get("cfd_mdot_kg_s"))
            if mode["mode_id"] == "M1b_full_cfd_segment_heat_flux_fixed_mdot":
                if cfd_mdot is None:
                    results.append(blocked_result(case_row, mode, "No CFD mdot target available for fixed-mdot replay."))
                    continue
                result = fixed_mdot_eval(case, scenario, cfd_mdot, sources, losses)
            else:
                result = fast_pressure_root(case, scenario, sources, losses)
            source_paths = ";".join([rel(SECTION_HEAT), rel(THERMAL_TARGETS), str(FLUID_ROOT)])
            results.append(result_row(result, case_row, mode, source_total, loss_total, source_paths))
            sensors.extend(sensor_rows_for_result(result, case_row, mode, refs))
    return results, sensors


def summarize_sensors(sensor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in sensor_rows:
        grouped[(row["case_id"], row["mode_id"], row["part"], row["kind"])].append(row)
        grouped[(row["case_id"], row["mode_id"], row["part"], "all")].append(row)
    out: list[dict[str, Any]] = []
    for (case_id, mode_id, part, kind), rows in sorted(grouped.items()):
        errors = [fnum(row.get("error_K")) for row in rows]
        errors = [e for e in errors if e is not None]
        out.append(
            {
                "case_id": case_id,
                "mode_id": mode_id,
                "part": part,
                "kind": kind,
                "n_compared": len(errors),
                "rmse_K": rmse(errors),
                "mae_K": mean(abs(e) for e in errors),
                "mean_error_K": mean(errors),
                "max_abs_error_K": max((abs(e) for e in errors), default=""),
                "missing_prediction_count": sum(1 for r in rows if fnum(r.get("predicted_K")) is None),
                "missing_target_count": sum(1 for r in rows if fnum(r.get("target_K")) is None),
            }
        )
    return out


def mdot_summary(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in results if row.get("result_status") == "executed" and "fixed_mdot" not in row.get("mode_id", "")]


def heat_score_rows(case_table: list[dict[str, Any]], execute_fluid: bool) -> list[dict[str, Any]]:
    heat_by = heat_rows_by_case()
    targets = load_targets()
    cases = {case.name: case for case in config_loader.load_cases()}
    salt2_terms = heat_terms(heat_by.get("salt_2", []))
    cooler_ratio = salt2_terms["cooler_loss_W"] / salt2_terms["cooler_imposed_loss_W"] if salt2_terms["cooler_imposed_loss_W"] else None
    heater_eta = salt2_terms["heater_W"] / salt2_terms["heater_power_W"] if salt2_terms["heater_power_W"] else None
    salt2_target = targets.get("salt_2", {})
    salt2_drive = (fnum(salt2_target.get("cfd_Tmean_K")) or 0.0) - (fnum(next(r.get("boundary_ambient_Ta_K") for r in case_table if r["case_id"] == "salt_2")) or 0.0)
    cooler_ua = salt2_terms["cooler_loss_W"] / salt2_drive if salt2_drive > 0 else None
    rows: list[dict[str, Any]] = []
    for case_row in case_table:
        case_id = case_row["case_id"]
        hr = heat_by.get(case_id, [])
        if not hr:
            for part, leg in [("part4", "cooling_leg"), ("part5", "heating_leg")]:
                rows.append(
                    {
                        "part": part,
                        "leg": leg,
                        "model_form": "blocked_missing_patch_heat_ledger",
                        "case_id": case_id,
                        "split": case_row["split"],
                        "admission_use_class": case_row["admission_use_class"],
                        "fit_policy": "not_fit",
                        "model_assumptions": "No current Salt1 patch heat ledger in consumed source set.",
                        "source_paths": case_row["source_paths"],
                    }
                )
            continue
        terms = heat_terms(hr)
        target = targets.get(case_id, {})
        drive = (fnum(target.get("cfd_Tmean_K")) or 0.0) - (fnum(case_row.get("boundary_ambient_Ta_K")) or 0.0)
        cooling_predictions = {
            "current_fluid_airside_hx_fixed_mdot": None,
            "imposed_cfd_cooler_upper_bound": terms["cooler_loss_W"],
            "salt2_fit_cooler_imposed_ratio": (cooler_ratio * terms["cooler_imposed_loss_W"]) if cooler_ratio is not None else None,
            "salt2_fit_constant_UA_bulk_drive": (cooler_ua * drive) if cooler_ua is not None else None,
        }
        if execute_fluid and fnum(case_row.get("cfd_mdot_kg_s")) is not None:
            scenario = predictive_hx_scenario(case_row)
            case = cases[case_row["fluid_case_name"]]
            result = fixed_mdot_eval(case, scenario, fnum(case_row["cfd_mdot_kg_s"]) or 0.0, None, None)
            cooling_predictions["current_fluid_airside_hx_fixed_mdot"] = result.qhx_total_W
        for form, pred in cooling_predictions.items():
            rows.append(heat_score_row("part4", "cooling_leg", form, case_row, pred, terms["cooler_loss_W"], cooling_policy(form), "Cooling heat removed comparison."))
        heating_predictions = {
            "electrical_heater_power_1_to_1": terms["heater_power_W"],
            "imposed_cfd_heater_upper_bound": terms["heater_W"],
            "salt2_fit_constant_heater_efficiency": (heater_eta * terms["heater_power_W"]) if heater_eta is not None else None,
        }
        for form, pred in heating_predictions.items():
            rows.append(heat_score_row("part5", "heating_leg", form, case_row, pred, terms["heater_W"], heating_policy(form), "Heating heat added comparison."))
    return rows


def heat_score_row(part: str, leg: str, form: str, case_row: dict[str, Any], pred: float | None, target: float, policy: str, assumptions: str) -> dict[str, Any]:
    err = pred - target if pred is not None else None
    return {
        "part": part,
        "leg": leg,
        "model_form": form,
        "case_id": case_row["case_id"],
        "split": case_row["split"],
        "admission_use_class": case_row["admission_use_class"],
        "q_pred_W": pred,
        "q_cfd_W": target,
        "error_W": err,
        "abs_error_W": abs(err) if err is not None else "",
        "fit_policy": policy,
        "model_assumptions": assumptions,
        "source_paths": ";".join([rel(SECTION_HEAT), str(FLUID_ROOT)]),
    }


def cooling_policy(form: str) -> str:
    if "salt2_fit" in form:
        return "fit_on_salt2_score_salt3_salt4_salt1_excluded"
    if "upper_bound" in form:
        return "diagnostic_upper_bound_not_predictive"
    return "setup_model_or_current_fluid_diagnostic"


def heating_policy(form: str) -> str:
    if "salt2_fit" in form:
        return "fit_on_salt2_score_salt3_salt4_salt1_excluded"
    if "upper_bound" in form:
        return "diagnostic_upper_bound_not_predictive"
    return "setup_model_diagnostic"


def summarize_heat(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if fnum(row.get("error_W")) is None:
            continue
        scopes = ["all_non_salt1", row.get("split", "")]
        if row.get("case_id") == "salt_1":
            scopes = ["salt1_diagnostic"]
        for scope in scopes:
            grouped[(row["part"], row["leg"], row["model_form"], scope)].append(row)
    out = []
    for (part, leg, form, scope), items in sorted(grouped.items()):
        errors = [fnum(row["error_W"]) for row in items]
        errors = [e for e in errors if e is not None]
        out.append(
            {
                "part": part,
                "leg": leg,
                "model_form": form,
                "scope": scope,
                "n_rows": len(errors),
                "rmse_W": rmse(errors),
                "mae_W": mean(abs(e) for e in errors),
                "mean_error_W": mean(errors),
                "fit_policy": items[0].get("fit_policy", ""),
                "interpretation": heat_interpretation(part, form),
            }
        )
    return out


def heat_interpretation(part: str, form: str) -> str:
    if "upper_bound" in form:
        return "Zero-error diagnostic by construction; not predictive."
    if "salt2_fit" in form:
        return "One-scalar Salt2 fit; evaluate Salt3 validation and Salt4 holdout without refitting."
    if part == "part4":
        return "Current or setup-derived cooler model form."
    return "Current or setup-derived heater model form."


def part3_increment(results: list[dict[str, Any]], temp_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_case_mode = {(r["case_id"], r["mode_id"]): r for r in results if r.get("result_status") == "executed"}
    by_temp = {(r["case_id"], r["mode_id"], r["kind"]): r for r in temp_summaries}
    rows = []
    for case in [spec["case_id"] for spec in CASE_SPECS]:
        m2 = by_case_mode.get((case, "M2_cfd_heater_test_section_cooler_pressure_root"))
        m3 = by_case_mode.get((case, "M3_cfd_heater_cooler_pressure_root"))
        if not m2 or not m3:
            continue
        for metric in ["mdot_error_kg_s", "Tmean_error_K", "loop_delta_error_K"]:
            v2 = fnum(m2.get(metric))
            v3 = fnum(m3.get(metric))
            rows.append(
                {
                    "case_id": case,
                    "metric": metric,
                    "part2_value": v2,
                    "part3_value": v3,
                    "increment_part3_minus_part2": v3 - v2 if v2 is not None and v3 is not None else "",
                    "interpretation": "Error introduced or removed by omitting the CFD test-section net heat term.",
                }
            )
        for kind in ["TP", "TW", "all"]:
            t2 = by_temp.get((case, "M2_cfd_heater_test_section_cooler_pressure_root", kind), {})
            t3 = by_temp.get((case, "M3_cfd_heater_cooler_pressure_root", kind), {})
            v2 = fnum(t2.get("rmse_K"))
            v3 = fnum(t3.get("rmse_K"))
            rows.append(
                {
                    "case_id": case,
                    "metric": f"{kind}_rmse_K",
                    "part2_value": v2,
                    "part3_value": v3,
                    "increment_part3_minus_part2": v3 - v2 if v2 is not None and v3 is not None else "",
                    "interpretation": "Sensor RMSE change when the CFD test-section heat term is omitted.",
                }
            )
    return rows


def correlation_rows(results: list[dict[str, Any]], temp_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mdot_by = {
        (row["case_id"], row["mode_id"]): row
        for row in results
        if row.get("result_status") == "executed" and "fixed_mdot" not in row.get("mode_id", "")
    }
    joined: list[dict[str, Any]] = []
    for temp in temp_summaries:
        result = mdot_by.get((temp["case_id"], temp["mode_id"]))
        if not result:
            continue
        mdot_err = fnum(result.get("mdot_error_kg_s"))
        probe_rmse = fnum(temp.get("rmse_K"))
        if mdot_err is None or probe_rmse is None:
            continue
        joined.append(
            {
                "case_id": temp["case_id"],
                "split": result.get("split", ""),
                "part": temp["part"],
                "mode_id": temp["mode_id"],
                "kind": temp["kind"],
                "abs_mdot_error_kg_s": abs(mdot_err),
                "probe_rmse_K": probe_rmse,
            }
        )

    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in joined:
        groups[("all_non_salt1", "all_parts", "all_modes", row["kind"])].append(row)
        groups[(row["part"], row["part"], "all_modes", row["kind"])].append(row)
        groups[(row["mode_id"], row["part"], row["mode_id"], row["kind"])].append(row)

    out: list[dict[str, Any]] = []
    for (scope, part, mode_id, kind), rows in sorted(groups.items()):
        xs = [row["abs_mdot_error_kg_s"] for row in rows]
        ys = [row["probe_rmse_K"] for row in rows]
        r = pearson(xs, ys)
        out.append(
            {
                "scope": scope,
                "part": part,
                "mode_id": mode_id,
                "kind": kind,
                "n_pairs": len(rows),
                "x_metric": "abs_mdot_error_kg_s",
                "y_metric": "probe_rmse_K",
                "pearson_r": r,
                "slope_K_per_kg_s": slope(xs, ys),
                "mean_abs_mdot_error_kg_s": mean(xs),
                "mean_probe_rmse_K": mean(ys),
                "interpretation": correlation_interpretation(r, len(rows)),
            }
        )
    return out


def correlation_interpretation(r: float | None, n: int) -> str:
    if n < 3 or r is None:
        return "Insufficient pairs for a stable correlation; report as descriptive only."
    ar = abs(r)
    if ar >= 0.8:
        strength = "strong"
    elif ar >= 0.5:
        strength = "moderate"
    else:
        strength = "weak"
    sign = "positive" if r >= 0 else "negative"
    return f"{strength} {sign} descriptive association; not causal with current sample size."


def row_lookup(rows: list[dict[str, Any]], **criteria: str) -> dict[str, Any]:
    for row in rows:
        if all(row.get(key) == value for key, value in criteria.items()):
            return row
    return {}


def trend_rows(
    results: list[dict[str, Any]],
    temp_summaries: list[dict[str, Any]],
    heat_summary: list[dict[str, Any]],
    increments: list[dict[str, Any]],
    correlations: list[dict[str, Any]],
) -> list[dict[str, str]]:
    part3_all = [r for r in temp_summaries if r.get("part") == "part3" and r.get("kind") == "all"]
    part2_all = [r for r in temp_summaries if r.get("part") == "part2" and r.get("kind") == "all"]
    m1 = [r for r in results if r.get("mode_id") == "M1_full_cfd_segment_heat_flux_pressure_root" and r.get("result_status") == "executed"]
    m2 = [r for r in results if r.get("part") == "part2" and r.get("result_status") == "executed"]
    m3 = [r for r in results if r.get("part") == "part3" and r.get("result_status") == "executed"]
    mdot_part2 = [abs(fnum(r.get("mdot_error_pct")) or 0.0) for r in m2]
    mdot_part3 = [abs(fnum(r.get("mdot_error_pct")) or 0.0) for r in m3]
    temp_part2 = [fnum(r.get("rmse_K")) or 0.0 for r in part2_all]
    temp_part3 = [fnum(r.get("rmse_K")) or 0.0 for r in part3_all]
    m1_tmean = [abs(fnum(r.get("Tmean_error_K")) or 0.0) for r in m1]
    m1_mdot = [abs(fnum(r.get("mdot_error_pct")) or 0.0) for r in m1]
    cool_current = row_lookup(heat_summary, part="part4", scope="all_non_salt1", model_form="current_fluid_airside_hx_fixed_mdot")
    cool_fit = row_lookup(heat_summary, part="part4", scope="all_non_salt1", model_form="salt2_fit_constant_UA_bulk_drive")
    heat_current = row_lookup(heat_summary, part="part5", scope="all_non_salt1", model_form="electrical_heater_power_1_to_1")
    heat_fit = row_lookup(heat_summary, part="part5", scope="all_non_salt1", model_form="salt2_fit_constant_heater_efficiency")
    all_corr = row_lookup(correlations, scope="all_non_salt1", part="all_parts", mode_id="all_modes", kind="all")

    omitted_test_sensor_changes = [
        fnum(r.get("increment_part3_minus_part2")) or 0.0
        for r in increments
        if r.get("metric") == "all_rmse_K"
    ]
    omitted_test_mdot_changes = [
        fnum(r.get("increment_part3_minus_part2")) or 0.0
        for r in increments
        if r.get("metric") == "mdot_error_kg_s"
    ]

    return [
        {
            "finding_id": "F001",
            "topic": "full CFD heat ledger",
            "observation": f"M1 pressure-root rows reproduce net heat balance but leave large absolute Tmean errors ({fmt(mean(m1_tmean), 3)} K average) and broad mdot errors ({fmt(mean(m1_mdot), 3)} pct average absolute).",
            "evidence_file": "mdot_error_summary.csv;temperature_probe_error_summary.csv",
            "cases_or_scope": "Salt2/Salt3/Salt4",
            "interpretation": "Matching realized segment heat fluxes alone does not make the current 1D model thermally state-predictive; reference temperature/state closure remains a dominant issue.",
            "next_action": "Audit start-temperature/reference-state handling and segment energy accumulation before treating full heat-ledger rows as validation evidence.",
        },
        {
            "finding_id": "F002",
            "topic": "boundary subset predictivity",
            "observation": f"Part2 mean all-probe RMSE is {fmt(mean(temp_part2), 3)} K and mean absolute mdot error is {fmt(mean(mdot_part2), 3)} pct; Part3 mean all-probe RMSE is {fmt(mean(temp_part3), 3)} K and mean absolute mdot error is {fmt(mean(mdot_part3), 3)} pct.",
            "evidence_file": "part2_heater_test_cooler_errors.csv;part3_heater_cooler_only_errors.csv",
            "cases_or_scope": "Salt2/Salt3/Salt4",
            "interpretation": "Heater/cooler-only boundaries improve probe RMSE in this diagnostic ladder but increase mdot error because omitting the test-section heat term changes buoyancy and heat distribution.",
            "next_action": "Model the test-section as a physical distributed boundary rather than a compatibility negative source.",
        },
        {
            "finding_id": "F003",
            "topic": "test-section omission",
            "observation": f"Omitting the CFD test-section net term changes all-probe RMSE by {fmt(mean(omitted_test_sensor_changes), 3)} K on average and mdot error by {fmt(mean(omitted_test_mdot_changes), 6)} kg/s on average.",
            "evidence_file": "part3_test_section_error_increment.csv",
            "cases_or_scope": "Salt2/Salt3/Salt4",
            "interpretation": "The test section is not a negligible closure term; it trades thermal-probe agreement against hydraulic buoyancy agreement in the current model form.",
            "next_action": "Extract/localize test-section wall heat flux and compare a distributed sink, passive ambient loss, and zero-test-section assumptions.",
        },
        {
            "finding_id": "F004",
            "topic": "cooling leg",
            "observation": f"Current fixed-mdot Fluid cooler RMSE is {fmt(cool_current.get('rmse_W'), 3)} W; Salt2-fit constant-UA bulk-drive RMSE is {fmt(cool_fit.get('rmse_W'), 3)} W.",
            "evidence_file": "part4_cooling_rmse_summary.csv",
            "cases_or_scope": "all_non_salt1",
            "interpretation": "Cooling heat removal is the clearest boundary-model improvement lever; a one-parameter Salt2 fit transfers to Salt3/Salt4 much better than the current fixed-mdot airside-HX diagnostic.",
            "next_action": "Promote a setup-only cooler model using geometry/air-flow inputs, then score Salt3/Salt4 without realized CFD cooler heat.",
        },
        {
            "finding_id": "F005",
            "topic": "heating leg",
            "observation": f"Electrical 1:1 heater RMSE is {fmt(heat_current.get('rmse_W'), 3)} W; Salt2-fit heater-efficiency RMSE is {fmt(heat_fit.get('rmse_W'), 3)} W.",
            "evidence_file": "part5_heating_rmse_summary.csv",
            "cases_or_scope": "all_non_salt1",
            "interpretation": "The CFD heater heat entry fraction is nearly a scalar efficiency over Salt2/Salt4, so heater closure is tractable but still must be setup-only before predictive admission.",
            "next_action": "Replace electrical 1:1 heater entry with a documented heater-efficiency or thermal-resistance model and hold Salt4 as a final blind check.",
        },
        {
            "finding_id": "F006",
            "topic": "mdot-temperature association",
            "observation": f"Across all pressure-root non-Salt1 rows, mdot absolute error and all-probe RMSE have Pearson r={fmt(all_corr.get('pearson_r'), 3)} with n={all_corr.get('n_pairs', '')}.",
            "evidence_file": "mdot_temperature_error_correlation.csv;figures/mdot_error_vs_probe_rmse.svg",
            "cases_or_scope": "all_non_salt1 pressure-root modes",
            "interpretation": "The association is descriptive, not causal: boundary-mode changes move mdot and probe errors together or apart depending on where heat is deposited.",
            "next_action": "Use the correlation table as a triage view, not a fitting objective, until more setup-only cases exist.",
        },
    ]


def write_appendix(out: Path, case_table: list[dict[str, Any]], heat_scores: list[dict[str, Any]]) -> None:
    app = out / "model_config_appendix"
    app.mkdir(parents=True, exist_ok=True)
    for src in [FLUID_CASES, FLUID_SCENARIOS, FLUID_CAMPAIGNS]:
        if src.exists():
            shutil.copy2(src, app / src.name)
    write_csv(app / "resolved_case_inputs_salt1_to_salt4.csv", case_table, CASE_COLUMNS)
    write_csv(app / "resolved_scenario_config_by_mode.csv", mode_rows(), MODE_COLUMNS)
    write_csv(app / "segment_source_loss_assignment_by_mode.csv", heat_scores, HEAT_SCORE_COLUMNS)
    write_csv(app / "closure_terms_by_mode.csv", mode_rows(), MODE_COLUMNS)
    write_json(
        app / "git_revisions.json",
        {
            "ethan_runs": git_revision(ROOT),
            "fluid": git_revision(FLUID_ROOT),
            "fluid_root": str(FLUID_ROOT),
        },
    )
    (app / "appendix_explanation.md").write_text(
        """# Model Configuration Appendix

This directory contains compact copies of the 1D model setup used by AGENT-360.
The copied YAML files are read-only snapshots from external Fluid configs. The
CSV files resolve those configs into the case inputs, model modes, closure
terms, and source/loss assignments used by the audit.

Runtime classes are deliberately separated: setup inputs are allowed for
predictive-style modes, CFD mdot is validation-only except fixed-mdot
diagnostics, and realized CFD wallHeatFlux is diagnostic evidence consumed only
by explicitly CFD-informed modes.
""",
        encoding="utf-8",
    )


def draw_svg(path: Path, temp_summaries: list[dict[str, Any]], results: list[dict[str, Any]]) -> None:
    mdot_by = {(r["case_id"], r["mode_id"]): fnum(r.get("mdot_error_kg_s")) for r in results}
    points = []
    for row in temp_summaries:
        if row["kind"] != "all":
            continue
        x = mdot_by.get((row["case_id"], row["mode_id"]))
        y = fnum(row.get("rmse_K"))
        if x is not None and y is not None:
            points.append((x, y, row))
    width, height = 760, 440
    left, right, top, bottom = 82, 710, 48, 380
    if points:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        if xmin == xmax:
            xmin -= 0.001
            xmax += 0.001
        if ymin == ymax:
            ymin -= 1
            ymax += 1
    else:
        xmin, xmax, ymin, ymax = -0.01, 0.01, 0, 10

    def sx(x: float) -> float:
        return left + (x - xmin) / (xmax - xmin) * (right - left)

    def sy(y: float) -> float:
        return bottom - (y - ymin) / (ymax - ymin) * (bottom - top)

    colors = {"part1": "#12664f", "part2": "#b26a00", "part3": "#3267a8"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fcfcfb"/>',
        '<style>text{font-family:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;fill:#111}.title{font-size:18px;font-weight:700}.axis{font-size:12px}.tick{font-size:10px;fill:#666}</style>',
        '<text x="82" y="28" class="title">mdot error vs TP/TW all-probe RMSE</text>',
        f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="none" stroke="#bbb"/>',
        f'<text x="{(left+right)/2}" y="424" text-anchor="middle" class="axis">mdot error vs CFD [kg/s]</text>',
        '<text x="18" y="220" transform="rotate(-90 18 220)" text-anchor="middle" class="axis">TP/TW RMSE [K]</text>',
    ]
    for i in range(5):
        x = left + i * (right - left) / 4
        y = top + i * (bottom - top) / 4
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{bottom}" stroke="#e6e1d8"/>')
        parts.append(f'<line x1="{left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e6e1d8"/>')
    for x, y, row in points:
        color = colors.get(row["part"], "#555")
        label = f'{row["case_id"]} {row["mode_id"]}'
        parts.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="5" fill="{color}"><title>{html.escape(label)} mdot={x:.6g} rmse={y:.4g}</title></circle>')
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def source_manifest() -> list[dict[str, str]]:
    sources = [
        FLUID_CASES,
        FLUID_SCENARIOS,
        FLUID_CAMPAIGNS,
        SECTION_HEAT,
        PARITY_CONTRACT,
        THERMAL_TARGETS,
        CFD_SENSOR_REFERENCE,
        CASE_ADMISSION,
        FLOW_BC_MATRIX,
        FORWARD_MAP,
        THERMAL_RADIATION_MAP,
    ]
    return [{"path": rel(path), "exists": "yes" if path.exists() else "no", "role": "read_only_input"} for path in sources]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(SECTION_HEAT)}
  - {rel(THERMAL_TARGETS)}
  - {rel(CFD_SENSOR_REFERENCE)}
  - {rel(CASE_ADMISSION)}
tags: [forward-model, predictive-1d, mdot, sensor-prediction, boundary-conditions]
related:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: {TASK}
date: {DATE}
role: Forward-pred/BC-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# mdot and TP/TW Probe Error Audit

## Purpose

This package audits current 1D model predictivity against Salt1/Salt2/Salt3/Salt4
CFD by comparing mass-flow error with TP/TW temperature-probe error. It is an
assessment package, not a new closure calibration.

## Main Guardrails

- Salt1 is included as diagnostic/context only and is blocked for CFD heat-flux
  modes because the consumed current patch heat ledger covers Salt2/Salt3/Salt4.
- Salt2/Salt3/Salt4 retain the current train/validation/holdout split.
- Any mode consuming realized CFD wallHeatFlux is CFD-informed diagnostic
  evidence, not a setup-only prediction.
- Fixed-mdot rows are thermal isolation diagnostics, not hydraulic predictivity
  evidence.
- CFD rcExternalTemperature radiation is embedded in total wallHeatFlux; no
  separate exported qr term is added.

## Result Counts

- Case rows: `{summary['case_rows']}`.
- Model result rows: `{summary['model_result_rows']}`.
- Executed model rows: `{summary['executed_model_rows']}`.
- Sensor error rows: `{summary['sensor_error_rows']}`.
- Heat score rows: `{summary['heat_score_rows']}`.

## Files To Open

1. `paper_ready_report.md`
2. `mdot_error_summary.csv`
3. `temperature_probe_error_summary.csv`
4. `sensor_level_errors.csv`
5. `part3_test_section_error_increment.csv`
6. `part4_cooling_rmse_summary.csv`
7. `part5_heating_rmse_summary.csv`
8. `mdot_temperature_error_correlation.csv`
9. `trend_conclusion_register.csv`
10. `model_config_appendix/appendix_explanation.md`
"""


def paper_report(
    summary: dict[str, Any],
    heat_summary: list[dict[str, Any]],
    correlations: list[dict[str, Any]],
    trends: list[dict[str, str]],
) -> str:
    best_cooling = min((r for r in heat_summary if r["part"] == "part4" and r["scope"] == "all_non_salt1"), key=lambda r: fnum(r["rmse_W"]) or float("inf"), default={})
    best_cooling_nontrivial = min(
        (
            r
            for r in heat_summary
            if r["part"] == "part4"
            and r["scope"] == "all_non_salt1"
            and "upper_bound" not in r["model_form"]
            and "imposed_ratio" not in r["model_form"]
        ),
        key=lambda r: fnum(r["rmse_W"]) or float("inf"),
        default={},
    )
    best_heating = min((r for r in heat_summary if r["part"] == "part5" and r["scope"] == "all_non_salt1"), key=lambda r: fnum(r["rmse_W"]) or float("inf"), default={})
    all_corr = row_lookup(correlations, scope="all_non_salt1", part="all_parts", mode_id="all_modes", kind="all")
    trend_lines = "\n".join(
        f"- `{row['finding_id']}` {row['topic']}: {row['observation']} {row['interpretation']}"
        for row in trends
    )
    return f"""# Paper-Ready Assessment

## Research Question

The AGENT-360 audit compares 1D mass-flow error to CFD TP/TW probe-temperature
error under a ladder of increasingly CFD-informed boundary modes. The key
scientific boundary is that modes using realized CFD wallHeatFlux are diagnostic
or upper-bound evidence; they are not final setup-only predictions.

The study asks whether the current 1D model is predictive for both circulation
rate and thermal state, and whether flow-rate error is coupled to TP/TW
probe-temperature error when CFD boundary information is supplied with different
levels of completeness.

## Case Admission and Data Use

Salt2/Salt3/Salt4 are scored under the current train/validation/holdout split.
Salt1 remains diagnostic because current Salt1 admission policy and patch heat
ledger inputs are incomplete in the consumed source set.

The scored CFD cases are Salt2 as the training row, Salt3 as validation, and
Salt4 as holdout. Salt1 is included only as diagnostic context. Closure
parameters in the simple Part4/Part5 alternatives may be fit on Salt2 only, then
are scored on Salt3/Salt4 without refitting.

## Boundary-Condition Modes

Part 1 contains two diagnostics. `M1_full_cfd_segment_heat_flux_pressure_root`
prescribes the realized CFD segment heat ledger and solves mdot from pressure
balance. `M1b_full_cfd_segment_heat_flux_fixed_mdot` uses the same heat ledger
but imposes CFD mdot, so it isolates thermal/sensor behavior and is not a
hydraulic prediction.

Part 2 prescribes CFD heater heat entry, CFD test-section net heat, and CFD
cooler heat removal, then solves mdot from pressure balance. The test-section
term is encoded as a compatibility negative source, not yet as a first-class
distributed external boundary model.

Part 3 prescribes only CFD heater heat entry and CFD cooler heat removal, then
solves mdot. The Part2-Part3 difference estimates how much the test-section
term changes mdot and probe-temperature errors in the current model.

Part 4 isolates the cooling leg at fixed mdot and compares heat removed. Part 5
isolates the heating leg at fixed mdot and compares heat added. These parts
score current/default model forms, diagnostic imposed-CFD upper bounds, and
one-parameter Salt2 fits evaluated on Salt3/Salt4 without refitting.

## Assumptions

The assumption register is `study_assumption_register.csv`. The most important
assumptions are:

- Positive CFD wallHeatFlux means heat enters the fluid; negative means heat
  leaves the fluid.
- CFD `rcExternalTemperature` includes radiation in total wallHeatFlux; no
  separate exported `qr` term is added.
- Realized CFD wallHeatFlux is only consumed by explicitly CFD-informed modes.
- Fixed-mdot rows impose CFD mdot and therefore are thermal diagnostics only.
- TP targets use CFD core/bulk probe references; TW targets use CFD wall
  references from the local validation refresh.
- Fluid default geometry, default minor losses, default friction closure, and
  1.0 inch insulation are used unless a mode explicitly says otherwise.

## Principal Results

The strongest near-term model-improvement levers remain the cooling/HX heat
removal and heater heat-entry fraction. The lowest cooling RMSE is
`{best_cooling.get('model_form', '')}` at `{fmt(best_cooling.get('rmse_W'), 3)}`
W, but that is a CFD-boundary scaling diagnostic rather than a setup-only
prediction. The best nontrivial cooling candidate in this audit is
`{best_cooling_nontrivial.get('model_form', '')}` with RMSE
`{fmt(best_cooling_nontrivial.get('rmse_W'), 3)}` W. The best all-non-Salt1
heating-leg form is `{best_heating.get('model_form', '')}` with RMSE
`{fmt(best_heating.get('rmse_W'), 3)}` W.

The descriptive association between absolute mdot error and all-probe TP/TW
RMSE across pressure-root non-Salt1 rows has Pearson r=`{fmt(all_corr.get('pearson_r'), 3)}`
with n=`{all_corr.get('n_pairs', '')}`. This correlation is not treated as a
causal model because the sample is small and each boundary mode changes both
heat placement and buoyancy forcing.

## Trends and Conclusions

{trend_lines}

## Interpretation for the Current 1D Model

The current 1D model is not yet a fully predictive setup-only model for the
Salt-family CFD cases. It can now be audited consistently, and several
CFD-informed diagnostics are quantified, but the best-performing rows still
consume realized CFD heat flux or fit a scalar on Salt2. The cooling leg and
heater heat-entry fraction are the most actionable near-term closures because
simple one-parameter Salt2 fits transfer well to Salt3/Salt4 in this diagnostic
exercise.

The test section should not be dropped silently. Omitting it improves TP/TW RMSE
in this ladder but worsens mdot error, which means it redistributes thermal
state and buoyancy error rather than removing a harmless term. The next
scientific step is a setup-only distributed test-section boundary model with
documented wall/ambient assumptions.

## Reproducibility and Appendix

Use `model_config_appendix/` for paper appendix material: it contains copied
Fluid YAML configuration snapshots, resolved scenario/mode tables, and
source/loss assignment tables.
"""


def build(out: Path = OUT, *, execute_fluid: bool = True) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    targets = load_targets()
    refs = load_sensor_refs()
    heat_by = heat_rows_by_case()
    cases = case_rows(targets, refs, heat_by)
    modes = mode_rows()
    assumptions = assumption_rows()
    results, sensor_errors = run_model_modes(cases, execute_fluid)
    temp_summary = summarize_sensors(sensor_errors)
    heat_scores = heat_score_rows(cases, execute_fluid)
    heat_summary = summarize_heat(heat_scores)
    increment = part3_increment(results, temp_summary)
    correlations = correlation_rows(results, temp_summary)
    trends = trend_rows(results, temp_summary, heat_summary, increment, correlations)

    write_csv(out / "study_assumption_register.csv", assumptions, ASSUMPTION_COLUMNS)
    write_csv(out / "case_admission_and_use_table.csv", cases, CASE_COLUMNS)
    write_csv(out / "model_mode_matrix.csv", modes, MODE_COLUMNS)
    write_csv(out / "mdot_error_summary.csv", mdot_summary(results), RESULT_COLUMNS)
    write_csv(out / "model_result_ledger.csv", results, RESULT_COLUMNS)
    write_csv(out / "sensor_level_errors.csv", sensor_errors, SENSOR_COLUMNS)
    write_csv(out / "temperature_probe_error_summary.csv", temp_summary, TEMP_SUMMARY_COLUMNS)
    write_csv(out / "part1_full_cfd_flux_mdot_sensor_errors.csv", [r for r in results if r["part"] == "part1"], RESULT_COLUMNS)
    write_csv(out / "part2_heater_test_cooler_errors.csv", [r for r in results if r["part"] == "part2"], RESULT_COLUMNS)
    write_csv(out / "part3_heater_cooler_only_errors.csv", [r for r in results if r["part"] == "part3"], RESULT_COLUMNS)
    write_csv(out / "part3_test_section_error_increment.csv", increment, ["case_id", "metric", "part2_value", "part3_value", "increment_part3_minus_part2", "interpretation"])
    write_csv(out / "part4_cooling_leg_heat_removed_scores.csv", [r for r in heat_scores if r["part"] == "part4"], HEAT_SCORE_COLUMNS)
    write_csv(out / "part4_cooling_rmse_summary.csv", [r for r in heat_summary if r["part"] == "part4"], HEAT_SUMMARY_COLUMNS)
    write_csv(out / "part5_heating_leg_heat_added_scores.csv", [r for r in heat_scores if r["part"] == "part5"], HEAT_SCORE_COLUMNS)
    write_csv(out / "part5_heating_rmse_summary.csv", [r for r in heat_summary if r["part"] == "part5"], HEAT_SUMMARY_COLUMNS)
    write_csv(out / "mdot_temperature_error_correlation.csv", correlations, CORRELATION_COLUMNS)
    write_csv(out / "trend_conclusion_register.csv", trends, TREND_COLUMNS)
    write_csv(out / "source_manifest.csv", source_manifest(), MANIFEST_COLUMNS)
    write_appendix(out, cases, heat_scores)
    draw_svg(out / "figures/mdot_error_vs_probe_rmse.svg", temp_summary, results)

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "execute_fluid": execute_fluid,
        "case_rows": len(cases),
        "model_modes": len(modes),
        "model_result_rows": len(results),
        "executed_model_rows": sum(1 for r in results if r.get("result_status") == "executed"),
        "sensor_error_rows": len(sensor_errors),
        "heat_score_rows": len(heat_scores),
        "correlation_rows": len(correlations),
        "trend_rows": len(trends),
        "salt1_policy": "diagnostic_context_only_blocked_for_cfd_heat_flux_modes",
        "native_cfd_outputs_mutated": False,
        "external_cfd_modeling_tools_mutated": False,
    }
    write_json(out / "summary.json", summary)
    (out / "README.md").write_text(readme(summary), encoding="utf-8")
    (out / "paper_ready_report.md").write_text(paper_report(summary, heat_summary, correlations, trends), encoding="utf-8")

    if out.resolve() == OUT.resolve():
        status = ROOT / ".agent/status/2026-07-14_AGENT-360.md"
        journal = ROOT / ".agent/journal/2026-07-14/mdot-temperature-probe-error-audit.md"
        import_path = ROOT / "imports/2026-07-14_mdot_temperature_probe_error_audit.json"
        status.write_text(
            f"""# {TASK} Status

Status: COMPLETE

Built `{rel(out)}` with `{summary['model_result_rows']}` model result rows, `{summary['executed_model_rows']}` executed Fluid rows, `{summary['sensor_error_rows']}` TP/TW sensor error rows, and `{summary['heat_score_rows']}` heating/cooling heat-score rows.

Salt1 is included as diagnostic/context only and blocked for CFD heat-flux modes because the current consumed patch heat ledger covers Salt2/Salt3/Salt4. No native CFD solver outputs, registry/admission state, scheduler state, generated indexes, or external `../cfd-modeling-tools` files were mutated.
""",
            encoding="utf-8",
        )
        journal.parent.mkdir(parents=True, exist_ok=True)
        journal.write_text(
            f"""# mdot / TP-TW Probe Error Audit

Task: `{TASK}`
Date: `{DATE}`

Implemented a reproducible Salt1-4 1D model assessment package. The study
compares pressure-root mdot errors with TP/TW probe errors for full CFD heat
flux, heater/test/cooler, and heater/cooler modes, then separately scores
cooling-leg heat removal and heating-leg heat addition model forms.

Guardrails: Salt1 remains diagnostic/context only; Salt2/Salt3/Salt4 keep
train/validation/holdout labels; realized CFD wallHeatFlux modes are
CFD-informed diagnostics; fixed-mdot modes are thermal isolation diagnostics;
rcExternalTemperature radiation is embedded in wallHeatFlux with no separate
exported qr term.
""",
            encoding="utf-8",
        )
        write_json(
            import_path,
            {
                "task": TASK,
                "date": DATE,
                "kind": "work_product_import",
                "work_product": rel(out),
                "summary": rel(out / "summary.json"),
                "readme": rel(out / "README.md"),
                "paper_ready_report": rel(out / "paper_ready_report.md"),
                "status": rel(status),
                "journal": rel(journal),
                "native_cfd_outputs_mutated": False,
                "external_cfd_modeling_tools_mutated": False,
                "generated_index_refresh": "not_run_active_AGENT_344_owns_generated_index_scope",
            },
        )
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--no-fluid", action="store_true", help="Write schemas and blocked rows without Fluid evaluations.")
    args = parser.parse_args(list(argv) if argv is not None else None)
    print(json.dumps(build(args.output_dir, execute_fluid=not args.no_fluid), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
