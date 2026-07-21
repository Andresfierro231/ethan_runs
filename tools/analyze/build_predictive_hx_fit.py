#!/usr/bin/env python3
"""Build a standalone predictive-HX fit campaign.

This campaign does not edit Fluid. It fits a low-dimensional HX duty surrogate
around Fluid's existing predictive_airside_hx mode, then reruns the pressure
root with the fitted duty as a predicted boundary condition. CFD cooler duty is
used only in declared training rows and post-solve scoring rows.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.analyze import run_predictive_forward_v0_imposed_cooler as forward_v0  # noqa: E402


OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit"
CONTRACT_DIR = forward_v0.CONTRACT_DIR
THERMAL_TARGETS = forward_v0.THERMAL_TARGETS
FORWARD_V0_DIR = forward_v0.OUT_DIR
HEAT_LOSS_ADMISSION = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-13/2026-07-13_litrev_heat_loss_calibration/heat_closure_admission.csv"
)

CASE_IDS = ("salt_2", "salt_3", "salt_4")
PRIMARY_SPLIT_ID = "declared_train_salt2_validate_salt3_holdout_salt4"
PRIMARY_TRAIN_CASES = ("salt_2",)
PRIMARY_VALIDATION_CASES = ("salt_3",)
PRIMARY_HOLDOUT_CASES = ("salt_4",)

MODEL_FORM_COLUMNS = [
    "model_form_id",
    "status",
    "runtime_cooler_source",
    "fitted_parameter",
    "physics_interpretation",
    "fit_policy",
    "blocked_or_limit_reason",
    "provenance",
]

SPLIT_COLUMNS = [
    "split_id",
    "split_role",
    "train_cases",
    "validation_cases",
    "holdout_cases",
    "split_policy",
    "notes",
]

BASELINE_COLUMNS = [
    "case_id",
    "fluid_case_name",
    "source_id",
    "variant_id",
    "model_form_id",
    "engine",
    "root_status",
    "accepted_for_validation",
    "baseline_qhx_total_W",
    "target_cooler_removed_W",
    "baseline_qhx_error_W",
    "baseline_qhx_abs_error_W",
    "mdot_kg_s",
    "cfd_mdot_kg_s",
    "mdot_error_vs_cfd_kg_s",
    "model_Tmean_proxy_K",
    "cfd_Tmean_K",
    "Tmean_error_vs_cfd_K",
    "model_loop_delta_proxy_K",
    "cfd_loop_delta_T_K",
    "loop_delta_error_vs_cfd_K",
    "qambient_total_W",
    "source_contract",
    "runtime_cooler_source",
    "target_cooler_used_at_runtime",
    "notes",
]

PARAMETER_COLUMNS = [
    "split_id",
    "variant_id",
    "model_form_id",
    "train_cases",
    "validation_cases",
    "holdout_cases",
    "n_train_rows",
    "fitted_global_qhx_multiplier",
    "train_rmse_qhx_W",
    "train_mean_error_qhx_W",
    "fit_status",
    "parameter_class",
    "quality_flags",
    "provenance",
]

DUTY_SCORE_COLUMNS = [
    "split_id",
    "case_id",
    "variant_id",
    "model_form_id",
    "fit_role",
    "baseline_qhx_total_W",
    "fitted_global_qhx_multiplier",
    "predicted_qhx_total_W",
    "target_cooler_removed_W",
    "qhx_error_W",
    "qhx_abs_error_W",
    "target_cooler_used_at_runtime",
    "notes",
]

FORWARD_SCORE_COLUMNS = [
    "split_id",
    "case_id",
    "fluid_case_name",
    "source_id",
    "variant_id",
    "model_form_id",
    "fit_role",
    "engine",
    "root_status",
    "accepted_for_validation",
    "predicted_qhx_total_W",
    "target_cooler_removed_W",
    "qhx_error_W",
    "mdot_kg_s",
    "cfd_mdot_kg_s",
    "mdot_error_vs_cfd_kg_s",
    "model_Tmean_proxy_K",
    "cfd_Tmean_K",
    "Tmean_error_vs_cfd_K",
    "model_loop_delta_proxy_K",
    "cfd_loop_delta_T_K",
    "loop_delta_error_vs_cfd_K",
    "qambient_total_W",
    "source_total_input_W",
    "pressure_residual_Pa",
    "deltaP_buoyancy_Pa",
    "deltaP_losses_Pa",
    "runtime_cooler_source",
    "target_cooler_used_at_runtime",
    "notes",
]

VIOLATION_COLUMNS = [
    "check_id",
    "severity",
    "violation",
    "details",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
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


def fnum(value: Any, default: float | None = None) -> float | None:
    if value in ("", None):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def joined(items: Iterable[str]) -> str:
    return ";".join(items)


def target_cooler_by_case(target_rows: list[dict[str, str]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in target_rows:
        case_id = row.get("case_id", "")
        value = fnum(row.get("cooler_removed_duty_W"))
        if case_id and value is not None:
            result[case_id] = abs(value)
    return result


def model_form_rows() -> list[dict[str, Any]]:
    return [
        {
            "model_form_id": "HX0_fluid_predictive_airside_hx",
            "status": "baseline_no_fit",
            "runtime_cooler_source": "Fluid predictive_airside_hx epsilon-NTU calculation",
            "fitted_parameter": "",
            "physics_interpretation": "Existing Fluid air-side HX model computes duty from air flow, air inlet temperature, geometry, and loop thermal state.",
            "fit_policy": "No CFD cooler duty at runtime; CFD cooler duty joined only for scoring.",
            "blocked_or_limit_reason": "Known to be uncalibrated for current TAMU CFD salt branches.",
            "provenance": "../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py predictive_airside_hx",
        },
        {
            "model_form_id": "HX1_global_qhx_multiplier_on_fluid_airside",
            "status": "implemented_primary_fit",
            "runtime_cooler_source": "global multiplier times HX0 predicted duty",
            "fitted_parameter": "fitted_global_qhx_multiplier",
            "physics_interpretation": "Low-dimensional UA/effectiveness surrogate around the existing epsilon-NTU Fluid HX calculation.",
            "fit_policy": "Fit only on declared training rows; held-out rows scored without refit.",
            "blocked_or_limit_reason": "Only three Salt rows are available, so treat as a provisional pathway, not a thesis-strength calibration.",
            "provenance": "TODO-PRED-HX-FIT campaign; AGENT-286 Research Plan: End-To-End Predictive 1D Model; Fluid solver predictive_airside_hx",
        },
        {
            "model_form_id": "HX2_direct_UA_multiplier_in_solver",
            "status": "blocked_not_implemented",
            "runtime_cooler_source": "would multiply airside/internal UA inside Fluid solver",
            "fitted_parameter": "UA_multiplier",
            "physics_interpretation": "Direct UA multiplier would be cleaner than a post-solve duty multiplier.",
            "fit_policy": "Requires an explicit external Fluid edit row before implementation.",
            "blocked_or_limit_reason": "The assigned TODO-PRED-HX-FIT scope is repo-local and does not claim external Fluid source edits.",
            "provenance": "../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py _hx_airside_transfer",
        },
    ]


def split_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "split_id": PRIMARY_SPLIT_ID,
            "split_role": "primary",
            "train_cases": joined(PRIMARY_TRAIN_CASES),
            "validation_cases": joined(PRIMARY_VALIDATION_CASES),
            "holdout_cases": joined(PRIMARY_HOLDOUT_CASES),
            "split_policy": "train Salt 2 only, use Salt 3 for model-selection validation, and reserve Salt 4 as holdout",
            "notes": "Matches TODO-PRED-VALIDATION-SPLIT admission_split_table.csv; one scalar thermal response only.",
        }
    ]
    for case_id in CASE_IDS:
        train_cases = tuple(item for item in CASE_IDS if item != case_id)
        rows.append(
            {
                "split_id": f"loo_validate_{case_id}",
                "split_role": "sensitivity",
                "train_cases": joined(train_cases),
                "validation_cases": case_id,
                "holdout_cases": "",
                "split_policy": "leave-one-out duty-only sensitivity",
                "notes": "Scores duty prediction without rerunning the forward thermal solve for every split.",
            }
        )
    return rows


def parse_cases(value: str) -> tuple[str, ...]:
    return tuple(item for item in value.split(";") if item)


def validate_split_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for row in rows:
        split_id = str(row["split_id"])
        train = set(parse_cases(str(row["train_cases"])))
        validation = set(parse_cases(str(row["validation_cases"])))
        holdout = set(parse_cases(str(row.get("holdout_cases", ""))))
        if not train:
            violations.append({"check_id": split_id, "severity": "error", "violation": "empty_train_cases", "details": ""})
        if not validation:
            violations.append({"check_id": split_id, "severity": "error", "violation": "empty_validation_cases", "details": ""})
        overlap = sorted((train & validation) | (train & holdout) | (validation & holdout))
        if overlap:
            violations.append(
                {
                    "check_id": split_id,
                    "severity": "error",
                    "violation": "split_role_overlap",
                    "details": joined(overlap),
                }
            )
        unknown = sorted((train | validation | holdout) - set(CASE_IDS))
        if unknown:
            violations.append(
                {
                    "check_id": split_id,
                    "severity": "error",
                    "violation": "unknown_case_id",
                    "details": joined(unknown),
                }
            )
    return violations


def predictive_hx_scenario_for(case_input: dict[str, str], variant_id: str) -> Any:
    return forward_v0.S.ScenarioConfig(
        name=f"predictive_hx_{variant_id}",
        ambient_temperature_K=float(case_input["boundary_ambient_Ta_K"]),
        insulation_thickness_in=float(case_input["insulation_thickness_in"]),
        radiation_on=False,
        model_mode="predictive_airside_hx",
        imposed_qhx_W=None,
        air_flow_Lpm=float(case_input["air_flow_Lpm"]),
        air_inlet_temperature_K=float(case_input["air_T_inlet_K"]),
        air_counterflow=True,
        max_outer_iterations=80,
        mdot_search_lower_kg_s=float(case_input["mdot_search_lower_kg_s"]),
        mdot_search_upper_kg_s=float(case_input["mdot_search_upper_kg_s"]),
    )


def imposed_hx_scenario_for(case_input: dict[str, str], variant_id: str, predicted_qhx_W: float) -> Any:
    adjusted = dict(case_input)
    adjusted["imposed_cooler_duty_W"] = predicted_qhx_W
    scenario = forward_v0.scenario_for(adjusted, variant_id)
    return forward_v0.S.ScenarioConfig(
        **{
            **scenario.__dict__,
            "name": f"predictive_hx_fit_{variant_id}",
            "imposed_qhx_W": predicted_qhx_W,
        }
    )


def source_contract_for(prescribed_sources: dict[str, float] | None) -> str:
    if prescribed_sources is None:
        return "heater_power_W_plus_test_section_power_W"
    return "heater_power_W_only_prescribed_segment_source"


def row_metrics_from_result(
    result: Any,
    case_input: dict[str, str],
    target: dict[str, str],
    prescribed_sources: dict[str, float] | None,
) -> dict[str, Any]:
    cfd_mdot = fnum(target.get("cfd_mdot_kg_s"))
    cfd_tmean = fnum(target.get("cfd_Tmean_K"))
    cfd_loop_delta = fnum(target.get("cfd_loop_delta_T_K"))
    tmean = forward_v0.model_tmean_proxy(result)
    loop_delta = forward_v0.model_loop_delta_proxy(result)
    return {
        "mdot_kg_s": result.mdot_kg_s,
        "cfd_mdot_kg_s": cfd_mdot,
        "mdot_error_vs_cfd_kg_s": result.mdot_kg_s - cfd_mdot if cfd_mdot is not None else "",
        "model_Tmean_proxy_K": tmean,
        "cfd_Tmean_K": cfd_tmean,
        "Tmean_error_vs_cfd_K": tmean - cfd_tmean if cfd_tmean is not None else "",
        "model_loop_delta_proxy_K": loop_delta,
        "cfd_loop_delta_T_K": cfd_loop_delta,
        "loop_delta_error_vs_cfd_K": loop_delta - cfd_loop_delta if cfd_loop_delta is not None else "",
        "qambient_total_W": result.qambient_total_W,
        "source_total_input_W": forward_v0.source_total_for(result.case, prescribed_sources),
        "pressure_residual_Pa": result.pressure_residual_Pa,
        "deltaP_buoyancy_Pa": result.deltaP_buoyancy_Pa,
        "deltaP_losses_Pa": result.deltaP_losses_Pa,
        "source_contract": source_contract_for(prescribed_sources),
    }


def build_baseline_rows(
    case_inputs: list[dict[str, str]],
    target_rows: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    cases = {case.name: case for case in forward_v0.config_loader.load_cases()}
    cooler_targets = target_cooler_by_case(list(target_rows.values()))
    rows: list[dict[str, Any]] = []
    for case_input in case_inputs:
        case = cases[case_input["fluid_case_name"]]
        target = target_rows.get(case_input["case_id"], {})
        for spec in forward_v0.variant_specs():
            variant_id = spec["variant_id"]
            scenario = predictive_hx_scenario_for(case_input, variant_id)
            prescribed = forward_v0.prescribed_sources_for(case, variant_id)
            result = forward_v0.fast_pressure_root(case, scenario, prescribed)
            target_q = cooler_targets[case_input["case_id"]]
            metrics = row_metrics_from_result(result, case_input, target, prescribed)
            rows.append(
                {
                    "case_id": case_input["case_id"],
                    "fluid_case_name": case_input["fluid_case_name"],
                    "source_id": case_input["source_id"],
                    "variant_id": variant_id,
                    "model_form_id": "HX0_fluid_predictive_airside_hx",
                    "engine": "fast_scan",
                    "root_status": result.root_status,
                    "accepted_for_validation": result.accepted_for_validation,
                    "baseline_qhx_total_W": result.qhx_total_W,
                    "target_cooler_removed_W": target_q,
                    "baseline_qhx_error_W": result.qhx_total_W - target_q,
                    "baseline_qhx_abs_error_W": abs(result.qhx_total_W - target_q),
                    **metrics,
                    "runtime_cooler_source": "Fluid predictive_airside_hx",
                    "target_cooler_used_at_runtime": "false",
                    "notes": "CFD cooler duty joined after solve for scoring only.",
                }
            )
    return rows


def fit_multiplier(baseline_rows: list[dict[str, Any]], train_cases: Iterable[str], variant_id: str) -> dict[str, Any]:
    train_set = set(train_cases)
    selected = [
        row
        for row in baseline_rows
        if row["variant_id"] == variant_id and row["case_id"] in train_set
    ]
    denom = sum(float(row["baseline_qhx_total_W"]) ** 2 for row in selected)
    if not selected or denom <= 0.0:
        multiplier = float("nan")
        status = "failed_no_positive_baseline_qhx"
    else:
        multiplier = sum(
            float(row["baseline_qhx_total_W"]) * float(row["target_cooler_removed_W"])
            for row in selected
        ) / denom
        status = "fit"
    errors = [
        multiplier * float(row["baseline_qhx_total_W"]) - float(row["target_cooler_removed_W"])
        for row in selected
        if math.isfinite(multiplier)
    ]
    nonaccepted = [
        str(row["case_id"])
        for row in selected
        if str(row.get("accepted_for_validation", "")).lower() != "true"
    ]
    quality_flags = []
    if nonaccepted:
        quality_flags.append("train_rows_include_nonaccepted_fast_scan:" + joined(nonaccepted))
        if status == "fit":
            status = "fit_fast_scan_acceptance_caveat"
    rmse = math.sqrt(sum(error * error for error in errors) / len(errors)) if errors else float("nan")
    mean_error = sum(errors) / len(errors) if errors else float("nan")
    return {
        "variant_id": variant_id,
        "fitted_global_qhx_multiplier": multiplier,
        "n_train_rows": len(selected),
        "train_rmse_qhx_W": rmse,
        "train_mean_error_qhx_W": mean_error,
        "fit_status": status,
        "quality_flags": joined(quality_flags),
    }


def parameter_rows(baseline_rows: list[dict[str, Any]], splits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split in splits:
        train_cases = parse_cases(str(split["train_cases"]))
        validation_cases = parse_cases(str(split["validation_cases"]))
        holdout_cases = parse_cases(str(split.get("holdout_cases", "")))
        for spec in forward_v0.variant_specs():
            variant_id = spec["variant_id"]
            fit = fit_multiplier(baseline_rows, train_cases, variant_id)
            rows.append(
                {
                    "split_id": split["split_id"],
                    "variant_id": variant_id,
                    "model_form_id": "HX1_global_qhx_multiplier_on_fluid_airside",
                    "train_cases": joined(train_cases),
                    "validation_cases": joined(validation_cases),
                    "holdout_cases": joined(holdout_cases),
                    **fit,
                    "parameter_class": "declared_pretrained_calibrated_parameter",
                    "provenance": "fit from HX0 baseline predictive_airside_hx duty to CFD/OpenFOAM cooler_removed_duty_W on train rows only",
                }
            )
    return rows


def duty_score_rows(
    baseline_rows: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
    splits: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    split_by_id = {str(row["split_id"]): row for row in splits}
    rows: list[dict[str, Any]] = []
    for param in parameters:
        split = split_by_id[str(param["split_id"])]
        train = set(parse_cases(str(split["train_cases"])))
        validation = set(parse_cases(str(split["validation_cases"])))
        holdout = set(parse_cases(str(split.get("holdout_cases", ""))))
        multiplier = float(param["fitted_global_qhx_multiplier"])
        for baseline in baseline_rows:
            if baseline["variant_id"] != param["variant_id"]:
                continue
            predicted = multiplier * float(baseline["baseline_qhx_total_W"])
            target = float(baseline["target_cooler_removed_W"])
            case_id = str(baseline["case_id"])
            rows.append(
                {
                    "split_id": param["split_id"],
                    "case_id": case_id,
                    "variant_id": param["variant_id"],
                    "model_form_id": param["model_form_id"],
                    "fit_role": "train" if case_id in train else "validation" if case_id in validation else "holdout" if case_id in holdout else "not_in_split",
                    "baseline_qhx_total_W": baseline["baseline_qhx_total_W"],
                    "fitted_global_qhx_multiplier": multiplier,
                    "predicted_qhx_total_W": predicted,
                    "target_cooler_removed_W": target,
                    "qhx_error_W": predicted - target,
                    "qhx_abs_error_W": abs(predicted - target),
                    "target_cooler_used_at_runtime": "false",
                    "notes": "target duty used for training only if fit_role=train; validation rows are post-fit scores",
                }
            )
    return rows


def primary_parameter_by_variant(parameters: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row["variant_id"]): row
        for row in parameters
        if row["split_id"] == PRIMARY_SPLIT_ID
    }


def build_primary_forward_score_rows(
    case_inputs: list[dict[str, str]],
    target_rows: dict[str, dict[str, str]],
    baseline_rows: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cases = {case.name: case for case in forward_v0.config_loader.load_cases()}
    cooler_targets = target_cooler_by_case(list(target_rows.values()))
    train = set(PRIMARY_TRAIN_CASES)
    validation = set(PRIMARY_VALIDATION_CASES)
    holdout = set(PRIMARY_HOLDOUT_CASES)
    baseline_by_key = {
        (str(row["case_id"]), str(row["variant_id"])): row
        for row in baseline_rows
    }
    params = primary_parameter_by_variant(parameters)
    rows: list[dict[str, Any]] = []
    for case_input in case_inputs:
        case = cases[case_input["fluid_case_name"]]
        target = target_rows.get(case_input["case_id"], {})
        for spec in forward_v0.variant_specs():
            variant_id = spec["variant_id"]
            param = params[variant_id]
            baseline = baseline_by_key[(case_input["case_id"], variant_id)]
            multiplier = float(param["fitted_global_qhx_multiplier"])
            predicted_qhx = multiplier * float(baseline["baseline_qhx_total_W"])
            prescribed = forward_v0.prescribed_sources_for(case, variant_id)
            scenario = imposed_hx_scenario_for(case_input, variant_id, predicted_qhx)
            result = forward_v0.fast_pressure_root(case, scenario, prescribed)
            target_q = cooler_targets[case_input["case_id"]]
            metrics = row_metrics_from_result(result, case_input, target, prescribed)
            case_id = case_input["case_id"]
            rows.append(
                {
                    "split_id": PRIMARY_SPLIT_ID,
                    "case_id": case_id,
                    "fluid_case_name": case_input["fluid_case_name"],
                    "source_id": case_input["source_id"],
                    "variant_id": variant_id,
                    "model_form_id": "HX1_global_qhx_multiplier_on_fluid_airside",
                    "fit_role": "train" if case_id in train else "validation" if case_id in validation else "holdout" if case_id in holdout else "not_in_split",
                    "engine": "fast_scan",
                    "root_status": result.root_status,
                    "accepted_for_validation": result.accepted_for_validation,
                    "predicted_qhx_total_W": predicted_qhx,
                    "target_cooler_removed_W": target_q,
                    "qhx_error_W": predicted_qhx - target_q,
                    **metrics,
                    "runtime_cooler_source": "HX1 predicted duty from train-fitted global multiplier",
                    "target_cooler_used_at_runtime": "false",
                    "notes": "Forward solve consumed predicted HX duty, not held-out CFD cooler duty.",
                }
            )
    return rows


def summarize_scores(duty_rows: list[dict[str, Any]], forward_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant_id in sorted({str(row["variant_id"]) for row in duty_rows}):
        for role in ("train", "validation", "holdout"):
            duty_selected = [
                row
                for row in duty_rows
                if row["split_id"] == PRIMARY_SPLIT_ID and row["variant_id"] == variant_id and row["fit_role"] == role
            ]
            forward_selected = [
                row
                for row in forward_rows
                if row["variant_id"] == variant_id and row["fit_role"] == role
            ]
            q_abs = [float(row["qhx_abs_error_W"]) for row in duty_selected]
            t_abs = [abs(float(row["Tmean_error_vs_cfd_K"])) for row in forward_selected if row["Tmean_error_vs_cfd_K"] != ""]
            mdot = [float(row["mdot_error_vs_cfd_kg_s"]) for row in forward_selected if row["mdot_error_vs_cfd_kg_s"] != ""]
            rows.append(
                {
                    "variant_id": variant_id,
                    "fit_role": role,
                    "n_rows": len(duty_selected),
                    "mean_abs_qhx_error_W": sum(q_abs) / len(q_abs) if q_abs else float("nan"),
                    "mean_abs_Tmean_error_vs_cfd_K": sum(t_abs) / len(t_abs) if t_abs else float("nan"),
                    "mean_mdot_error_vs_cfd_kg_s": sum(mdot) / len(mdot) if mdot else float("nan"),
                }
            )
    return rows


def validate_outputs(
    split_rows_: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    duty_rows_: list[dict[str, Any]],
    forward_rows_: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    violations = validate_split_rows(split_rows_)
    for row in gate_rows:
        if row["scoring_admission_status"] != "pass":
            violations.append(
                {
                    "check_id": str(row["gate_name"]),
                    "severity": "error",
                    "violation": "litrev_gate_reference_not_passing",
                    "details": str(row["notes"]),
                }
            )
    for row in duty_rows_ + forward_rows_:
        if row.get("fit_role") == "validation" and row.get("target_cooler_used_at_runtime") != "false":
            violations.append(
                {
                    "check_id": str(row.get("case_id", "")),
                    "severity": "error",
                    "violation": "heldout_target_cooler_used_at_runtime",
                    "details": str(row.get("variant_id", "")),
                }
            )
    return violations


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    lines = []
    for row in summary.get("primary_score_summary", []):
        lines.append(
            "- `{variant}` `{role}`: mean abs HX-duty error `{q:.3f} W`, mean abs Tmean error `{t:.3f} K`, mean mdot error `{m:.6f} kg/s`.".format(
                variant=row["variant_id"],
                role=row["fit_role"],
                q=float(row["mean_abs_qhx_error_W"]),
                t=float(row["mean_abs_Tmean_error_vs_cfd_K"]),
                m=float(row["mean_mdot_error_vs_cfd_kg_s"]),
            )
        )
    score_text = "\n".join(lines) if lines else "- No score rows generated."
    text = f"""# Predictive HX Fit

Generated: `{summary['generated_utc']}`

This standalone campaign replaces the imposed cooler duty with a declared
low-dimensional HX-duty surrogate for Salt 2-4. It does not edit Fluid source
and does not touch native solver outputs.

## Model Forms

- `HX0_fluid_predictive_airside_hx`: Fluid's existing predictive airside
  epsilon-NTU calculation, no fit.
- `HX1_global_qhx_multiplier_on_fluid_airside`: one global multiplier on the
  `HX0` predicted duty. This is the implemented provisional UA/effectiveness
  surrogate.
- `HX2_direct_UA_multiplier_in_solver`: documented as the cleaner future form,
  but blocked here because this campaign does not claim external Fluid edits.

## Split Policy

Primary split from `TODO-PRED-VALIDATION-SPLIT`: train on `salt_2`, use
`salt_3` for model-selection validation, and reserve `salt_4` as holdout. This
permits only one declared scalar HX/cooler response. Leave-one-out duty-only
scores are emitted as sensitivity checks, not as replacement admissions.

## Primary Score Snapshot

{score_text}

## Files

- `hx_model_forms.csv`: candidate forms, implemented status, and provenance.
- `hx_validation_splits.csv`: primary and leave-one-out split definitions.
- `hx_baseline_predictive_airside.csv`: unfitted Fluid predictive-HX baseline.
- `hx_fit_parameters.csv`: fitted global duty multipliers by split and source
  contract variant.
- `hx_duty_scores.csv`: train/validation cooler-duty scores for all splits.
- `hx_primary_forward_scores.csv`: pressure-rooted forward scores using the
  primary split's predicted HX duty.
- `hx_litrev_gate_reference_audit.csv`: required lit-rev gate references.
- `violations.csv`: strict validation findings; expected to be empty.
- `summary.json`: machine-readable campaign metadata.

## Interpretation Boundaries

The campaign uses CFD/OpenFOAM cooler duty only on declared training rows for
the fitted multiplier and as validation-only scoring evidence elsewhere. It
does not solve heater/test-section transfer, wall/storage residuals, exact
reverse-flow fractions, hydraulic closure quality, or thermal mesh uncertainty.
Some fast-scan rows are flagged as not fully accepted by the current pressure
root validity policy; those flags are preserved in `hx_fit_parameters.csv` and
`hx_primary_forward_scores.csv`. The next clean step is a direct Fluid
UA-multiplier row or an end-to-end score after heater/test/hydraulic gates are
resolved.
"""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(out_dir: Path = OUT_DIR) -> dict[str, Any]:
    contract_summary = forward_v0.load_or_build_contract(CONTRACT_DIR, strict=True)
    runtime_contract = forward_v0.runtime_contract_by_field(CONTRACT_DIR)
    gate_rows = forward_v0.litrev_gate_reference_rows(runtime_contract)
    forward_v0.enforce_litrev_gate_references(gate_rows)

    case_inputs = read_csv(CONTRACT_DIR / "case_runtime_inputs_forward_v0.csv")
    target_rows = forward_v0.target_by_case()
    splits = split_rows()
    baseline = build_baseline_rows(case_inputs, target_rows)
    parameters = parameter_rows(baseline, splits)
    duty_scores = duty_score_rows(baseline, parameters, splits)
    primary_forward = build_primary_forward_score_rows(case_inputs, target_rows, baseline, parameters)
    primary_summary = summarize_scores(duty_scores, primary_forward)
    violations = validate_outputs(splits, gate_rows, duty_scores, primary_forward)

    write_csv(out_dir / "hx_model_forms.csv", model_form_rows(), MODEL_FORM_COLUMNS)
    write_csv(out_dir / "hx_validation_splits.csv", splits, SPLIT_COLUMNS)
    write_csv(out_dir / "hx_baseline_predictive_airside.csv", baseline, BASELINE_COLUMNS)
    write_csv(out_dir / "hx_fit_parameters.csv", parameters, PARAMETER_COLUMNS)
    write_csv(out_dir / "hx_duty_scores.csv", duty_scores, DUTY_SCORE_COLUMNS)
    write_csv(out_dir / "hx_primary_forward_scores.csv", primary_forward, FORWARD_SCORE_COLUMNS)
    write_csv(out_dir / "hx_litrev_gate_reference_audit.csv", gate_rows, forward_v0.GATE_REFERENCE_COLUMNS)
    write_csv(out_dir / "violations.csv", violations, VIOLATION_COLUMNS)

    summary = {
        "task_id": "TODO-PRED-HX-FIT",
        "generated_utc": utc_now(),
        "source_files": {
            "input_contract": rel(CONTRACT_DIR),
            "forward_v0_package": rel(FORWARD_V0_DIR),
            "thermal_targets": rel(THERMAL_TARGETS),
            "heat_loss_admission": rel(HEAT_LOSS_ADMISSION),
            "fluid_solver": "../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py",
        },
        "model_forms": [row["model_form_id"] for row in model_form_rows()],
        "primary_split_id": PRIMARY_SPLIT_ID,
        "primary_train_cases": list(PRIMARY_TRAIN_CASES),
        "primary_validation_cases": list(PRIMARY_VALIDATION_CASES),
        "primary_holdout_cases": list(PRIMARY_HOLDOUT_CASES),
        "n_baseline_rows": len(baseline),
        "n_parameter_rows": len(parameters),
        "n_duty_score_rows": len(duty_scores),
        "n_primary_forward_rows": len(primary_forward),
        "n_primary_forward_accepted_rows": sum(
            1 for row in primary_forward if str(row["accepted_for_validation"]).lower() == "true"
        ),
        "litrev_gate_reference_status": "pass",
        "n_violations": len(violations),
        "strict_status": "pass" if not violations else "fail",
        "primary_score_summary": primary_summary,
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--strict", action="store_true", help="Fail if validation emits violations.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    summary = build_package(args.output_dir)
    if args.strict and summary["n_violations"]:
        raise SystemExit(f"predictive HX fit emitted {summary['n_violations']} violation(s)")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
