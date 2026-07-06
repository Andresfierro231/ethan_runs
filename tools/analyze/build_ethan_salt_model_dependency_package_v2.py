#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from tools.common import ensure_dir, iso_timestamp, json_dump
from tools.analyze.build_ethan_salt_feature_hydraulic_hardening import (
    aggregate_feature_case_rows,
    assemble_feature_timeseries_rows,
    load_feature_inputs,
)
from tools.analyze.build_ethan_salt_thermal_closure_hardening import (
    aggregate_case_rows as aggregate_thermal_case_rows,
    build_thermal_timeseries_rows,
    load_branch_gate_rows,
)
from tools.analyze.ethan_salt_hardening_common import (
    MODEL_DEPENDENCY_V1_DIR,
    THERMAL_BLOCKED_BRANCHES,
    THERMAL_DERIVED_BRANCHES,
    CaseContext,
    csv_dump_rows,
    finite_float,
    load_case_contexts,
    load_csv_rows,
)

FEATURE_DIR = Path("reports/2026-06-19_ethan_salt_feature_hydraulic_hardening")
THERMAL_DIR = Path("reports/2026-06-19_ethan_salt_thermal_closure_hardening")
DEFAULT_OUTPUT_DIR = Path("reports/2026-06-19_ethan_salt_model_dependency_package_v2")
BOOTSTRAP_SAMPLES = 200
BOOTSTRAP_SEED = 719
HUBER_DELTA = 1.0
FEATURE_STABILITY_MIN = 0.75
FEATURE_CASE_MIN = 4
THERMAL_DEFENDED_MIN_ROWS = 6
FRICTION_DEFENDED_MIN_ROWS = 8
MAX_CASE_SHARE = 0.25
DIRECT_SHEAR_STRICT_MIN = 0.67
DIRECT_SHEAR_STRICT_MAX = 1.50
DIRECT_SHEAR_LOOSE_MIN = 0.40
DIRECT_SHEAR_LOOSE_MAX = 2.50


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the v2 Salt model-dependency package from the new feature and "
            "thermal hardening packages plus the June 18 dependency package."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--feature-dir", default=str(FEATURE_DIR))
    parser.add_argument("--thermal-dir", default=str(THERMAL_DIR))
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Optional bounded rebuild of one or more Salt source IDs.",
    )
    return parser.parse_args()


def fit_geometric_constant(rows: list[dict[str, Any]], target_key: str, category_key: str) -> dict[str, Any]:
    valid = [row for row in rows if finite_float(row.get(target_key)) > 0.0]
    if not valid:
        return {"status": "not_fit", "reason": "no_positive_rows"}
    categories = sorted({str(row[category_key]) for row in valid})
    labels = [f"group:{value}" for value in categories]
    coefficients: list[float] = []
    predictions = np.zeros(len(valid), dtype=float)
    for idx, category in enumerate(categories):
        payload = [math.log(finite_float(row[target_key])) for row in valid if str(row[category_key]) == category]
        center = float(np.mean(payload))
        coefficients.append(center)
        for row_index, row in enumerate(valid):
            if str(row[category_key]) == category:
                predictions[row_index] = center
    observed = np.array([math.log(finite_float(row[target_key])) for row in valid], dtype=float)
    residual = observed - predictions
    return {
        "status": "fit",
        "model_type": "geometric_constant",
        "row_count": len(valid),
        "coefficient_names": labels,
        "coefficients": coefficients,
        "rmse_log": float(np.sqrt(np.mean(residual ** 2))),
        "mae_log": float(np.mean(np.abs(residual))),
        "r2_log": float(1.0 - np.sum(residual ** 2) / np.sum((observed - np.mean(observed)) ** 2)) if len(valid) > 1 else math.nan,
    }


def design_matrix(rows: list[dict[str, Any]], target_key: str, re_key: str, category_key: str) -> tuple[np.ndarray, np.ndarray, list[str], list[dict[str, Any]]]:
    valid = [row for row in rows if finite_float(row.get(target_key)) > 0.0 and finite_float(row.get(re_key)) > 0.0]
    if not valid:
        return np.zeros((0, 0)), np.zeros((0,)), [], []
    categories = sorted({str(row[category_key]) for row in valid})
    labels = ["intercept", "log_re"] + [f"{category_key}:{value}" for value in categories[1:]]
    x = np.ones((len(valid), len(labels)), dtype=float)
    y = np.array([math.log(finite_float(row[target_key])) for row in valid], dtype=float)
    for index, row in enumerate(valid):
        x[index, 1] = math.log(finite_float(row[re_key]))
        for cat_index, value in enumerate(categories[1:], start=2):
            x[index, cat_index] = 1.0 if str(row[category_key]) == value else 0.0
    return x, y, labels, valid


def ols_fit(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    return coef


def huber_fit(x: np.ndarray, y: np.ndarray, delta: float = HUBER_DELTA, max_iter: int = 30) -> np.ndarray:
    coef = ols_fit(x, y)
    for _ in range(max_iter):
        residual = y - x @ coef
        abs_residual = np.abs(residual)
        weights = np.ones_like(abs_residual)
        mask = abs_residual > delta
        weights[mask] = delta / abs_residual[mask]
        next_coef = ols_fit(x * weights[:, None], y * weights)
        if np.allclose(coef, next_coef, rtol=1e-8, atol=1e-10):
            coef = next_coef
            break
        coef = next_coef
    return coef


def bootstrap_coefficients(rows: list[dict[str, Any]], target_key: str, re_key: str, category_key: str, robust: bool) -> dict[str, list[float]]:
    x, y, labels, valid = design_matrix(rows, target_key, re_key, category_key)
    if len(valid) < 3 or x.shape[1] >= len(valid):
        return {}
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    samples: dict[str, list[float]] = {label: [] for label in labels}
    for _ in range(BOOTSTRAP_SAMPLES):
        indices = rng.integers(0, len(valid), size=len(valid))
        sample_rows = [valid[index] for index in indices]
        xb, yb, labels_b, _ = design_matrix(sample_rows, target_key, re_key, category_key)
        if xb.shape != x.shape or labels_b != labels:
            continue
        coef = huber_fit(xb, yb) if robust else ols_fit(xb, yb)
        for label, value in zip(labels, coef):
            samples[label].append(float(value))
    return {
        label: [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]
        for label, values in samples.items()
        if values
    }


def fit_power_law(rows: list[dict[str, Any]], target_key: str, re_key: str, category_key: str, model_type: str, robust: bool) -> dict[str, Any]:
    x, y, labels, valid = design_matrix(rows, target_key, re_key, category_key)
    if len(valid) < 3 or x.shape[1] >= len(valid):
        return {"status": "not_fit", "reason": "insufficient_rows_or_rank"}
    coef = huber_fit(x, y) if robust else ols_fit(x, y)
    pred = x @ coef
    residual = y - pred
    return {
        "status": "fit",
        "model_type": model_type,
        "row_count": len(valid),
        "coefficient_names": labels,
        "coefficients": [float(value) for value in coef],
        "rmse_log": float(np.sqrt(np.mean(residual ** 2))),
        "mae_log": float(np.mean(np.abs(residual))),
        "r2_log": float(1.0 - np.sum(residual ** 2) / np.sum((y - np.mean(y)) ** 2)) if len(valid) > 1 else math.nan,
        "bootstrap_ci95": bootstrap_coefficients(valid, target_key, re_key, category_key, robust),
    }


def case_share_ok(rows: list[dict[str, Any]]) -> bool:
    counts = Counter(str(row["source_id"]) for row in rows)
    total = sum(counts.values())
    return total > 0 and max(counts.values()) / total <= MAX_CASE_SHARE


def choose_defended_recommendation(rows: list[dict[str, Any]], constant_fit: dict[str, Any], power_fit: dict[str, Any], min_rows: int) -> tuple[str, str]:
    if len(rows) < min_rows or not case_share_ok(rows):
        return "not_defensible_yet", "insufficient_row_diversity"
    if power_fit.get("status") == "fit":
        ci = power_fit.get("bootstrap_ci95", {}).get("log_re")
        if ci and not (ci[0] <= 0.0 <= ci[1]):
            return "provisional_defended", power_fit["model_type"]
    if constant_fit.get("status") == "fit":
        return "provisional_defended", constant_fit["model_type"]
    return "not_defensible_yet", "no_stable_model"


def load_straight_rows(source_ids: set[str] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fit_rows = load_csv_rows(MODEL_DEPENDENCY_V1_DIR / "hydraulic_fit_ready_rows.csv")
    audit_rows = load_csv_rows(MODEL_DEPENDENCY_V1_DIR / "hydraulic_hardening_audit.csv")
    if source_ids:
        fit_rows = [row for row in fit_rows if row["source_id"] in source_ids]
        audit_rows = [row for row in audit_rows if row["source_id"] in source_ids]
    normalized = []
    for row in fit_rows:
        normalized.append(
            {
                "asset_family": "straight_section_friction",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "category_name": row["scope_name"],
                "category_class": row["scope_kind"],
                "re_effective": finite_float(row.get("re_effective")),
                "target_value": finite_float(row.get("apparent_darcy_f_local")),
                "pressure_method_status": "defended_direct_hydro",
                "support_fraction": finite_float(row.get("support_fraction")),
                "direct_to_shear_darcy_ratio": finite_float(row.get("direct_to_shear_darcy_ratio")),
            }
        )
    return normalized, audit_rows


def stable_feature_fit_rows(feature_case_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, float]]:
    fit_rows = [row for row in feature_case_rows if row["fit_use_status"] == "fit_used"]
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    total_by_name: Counter[str] = Counter(row["feature_name"] for row in feature_case_rows)
    for row in fit_rows:
        by_name[row["feature_name"]].append(row)
    stability = {
        feature_name: len(rows) / max(total_by_name[feature_name], 1)
        for feature_name, rows in by_name.items()
    }
    stable_names = {
        feature_name
        for feature_name, fraction in stability.items()
        if fraction >= FEATURE_STABILITY_MIN and len(by_name[feature_name]) >= FEATURE_CASE_MIN
    }
    normalized = []
    for row in fit_rows:
        if row["feature_name"] not in stable_names:
            continue
        normalized.append(
            {
                "asset_family": "feature_keff",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "category_name": row["feature_name"],
                "category_class": row["feature_class"],
                "re_effective": finite_float(row.get("mean_re_effective")),
                "target_value": finite_float(row.get("mean_keff_effective_local")),
                "pressure_method_status": "patch_prgh_local_boundary_reference",
                "support_fraction": finite_float(row.get("local_support_fraction_min")),
                "positive_time_fraction": finite_float(row.get("positive_time_fraction")),
            }
        )
    return normalized, stability


def normalize_feature_case_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["mean_keff_effective_local"] = finite_float(row.get("mean_keff_effective_local"), finite_float(row.get("mean_keff_local")))
        payload.append(item)
    return payload


def load_thermal_case_rows(thermal_dir: Path, source_ids: set[str] | None = None) -> list[dict[str, Any]]:
    rows = load_csv_rows(thermal_dir / "thermal_closure_by_case.csv")
    if source_ids:
        rows = [row for row in rows if row["source_id"] in source_ids]
    return [dict(row) for row in rows]


def summarize_exclusions(rows: list[dict[str, Any]], asset_family_key: str) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    for row in rows:
        fit_use_status = str(row.get("fit_use_status", ""))
        if fit_use_status == "fit_used":
            continue
        counts[(str(row.get(asset_family_key, "")), fit_use_status, str(row.get("exclusion_reason_primary", "")))] += 1
    return [
        {
            "asset_family": asset_family,
            "fit_use_status": fit_use_status,
            "exclusion_reason_primary": exclusion_reason_primary,
            "row_count": count,
        }
        for (asset_family, fit_use_status, exclusion_reason_primary), count in sorted(counts.items())
    ]


def direct_thermal_fit_rows(thermal_case_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    defended: list[dict[str, Any]] = []
    exploratory: list[dict[str, Any]] = []
    for row in thermal_case_rows:
        if row["branch_name"] in THERMAL_BLOCKED_BRANCHES:
            continue
        if row["branch_name"] in THERMAL_DERIVED_BRANCHES:
            continue
        if row["fit_use_status"] == "fit_used":
            defended.append(row)
        if row["branch_fit_status"] == "candidate" and finite_float(row.get("mean_nu_effective")) > 0.0 and finite_float(row.get("mean_re_effective")) > 0.0:
            exploratory.append(row)
    return defended, exploratory


def make_hydraulic_sensitivity_rows(
    straight_audit_rows: list[dict[str, Any]],
    contexts: dict[str, CaseContext],
    feature_inputs: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    straight_payload = [row for row in straight_audit_rows if row.get("asset_family") == "straight_section_friction"]
    base_rows = [
        {
            "asset_family": "straight_section_friction",
            "source_id": row["source_id"],
            "case_label": row["case_label"],
            "category_name": row["scope_name"],
            "re_effective": finite_float(row.get("re_effective")),
            "target_value": finite_float(row.get("apparent_darcy_f_local")),
            "category_class": row["scope_kind"],
        }
        for row in straight_payload
        if row.get("fit_use_status") == "fit_used"
    ]
    strict_rows = [
        {
            "asset_family": "straight_section_friction",
            "source_id": row["source_id"],
            "case_label": row["case_label"],
            "category_name": row["scope_name"],
            "re_effective": finite_float(row.get("re_effective")),
            "target_value": finite_float(row.get("apparent_darcy_f_local")),
            "category_class": row["scope_kind"],
        }
        for row in straight_payload
        if row.get("fit_use_status") == "fit_used"
        and DIRECT_SHEAR_STRICT_MIN <= finite_float(row.get("direct_to_shear_darcy_ratio")) <= DIRECT_SHEAR_STRICT_MAX
    ]
    loose_rows = [
        {
            "asset_family": "straight_section_friction",
            "source_id": row["source_id"],
            "case_label": row["case_label"],
            "category_name": row["scope_name"],
            "re_effective": finite_float(row.get("re_effective")),
            "target_value": finite_float(row.get("apparent_darcy_f_local")),
            "category_class": row["scope_kind"],
        }
        for row in straight_payload
        if row.get("fit_use_status") == "fit_used"
        and DIRECT_SHEAR_LOOSE_MIN <= finite_float(row.get("direct_to_shear_darcy_ratio")) <= DIRECT_SHEAR_LOOSE_MAX
    ]
    base_fit = fit_power_law(base_rows, "target_value", "re_effective", "category_name", "class_aware_re_power_law", robust=False)
    for name, payload, note in [
        ("direct_to_shear_gate_loose", loose_rows, f"Loose direct/shear ratio gate {DIRECT_SHEAR_LOOSE_MIN:.2f}-{DIRECT_SHEAR_LOOSE_MAX:.2f}."),
        ("direct_to_shear_gate_strict", strict_rows, f"Strict direct/shear ratio gate {DIRECT_SHEAR_STRICT_MIN:.2f}-{DIRECT_SHEAR_STRICT_MAX:.2f}."),
    ]:
        fit = fit_power_law(payload, "target_value", "re_effective", "category_name", "class_aware_re_power_law", robust=False)
        rows_out.append(
            sensitivity_row(
                asset_family="hydraulic_straight",
                sensitivity_name=name,
                base_rows=base_rows,
                sensitivity_rows=payload,
                base_fit=base_fit,
                sensitivity_fit=fit,
                note=note,
            )
        )

    base_feature_times = assemble_feature_timeseries_rows(contexts, feature_inputs, boundary_bin_count=3)
    base_feature_case = normalize_feature_case_rows(aggregate_feature_case_rows(base_feature_times))
    base_feature_rows, _ = stable_feature_fit_rows(base_feature_case)
    base_feature_fit = fit_power_law(base_feature_rows, "target_value", "re_effective", "category_name", "feature_name_aware_re_power_law", robust=False)
    for count in (2, 5):
        alt_case = normalize_feature_case_rows(aggregate_feature_case_rows(assemble_feature_timeseries_rows(contexts, feature_inputs, boundary_bin_count=count)))
        alt_rows, _ = stable_feature_fit_rows(alt_case)
        alt_fit = fit_power_law(alt_rows, "target_value", "re_effective", "category_name", "feature_name_aware_re_power_law", robust=False)
        rows_out.append(
            sensitivity_row(
                asset_family="hydraulic_feature",
                sensitivity_name=f"feature_boundary_bin_count_{count}",
                base_rows=base_feature_rows,
                sensitivity_rows=alt_rows,
                base_fit=base_feature_fit,
                sensitivity_fit=alt_fit,
                note=f"Feature local-boundary reference rebuilt with {count} nearest finite bins per side instead of 3.",
            )
        )
    rows_out.append(
        {
            "asset_family": "hydraulic",
            "sensitivity_name": "late_window_choice",
            "status": "not_run",
            "base_row_count": len(base_rows),
            "sensitivity_row_count": len(base_rows),
            "row_count_delta": 0,
            "base_model_status": base_fit.get("status", "not_fit"),
            "sensitivity_model_status": "not_run",
            "base_log_re_slope": fit_slope(base_fit),
            "sensitivity_log_re_slope": math.nan,
            "log_re_slope_delta": math.nan,
            "base_rmse_log": base_fit.get("rmse_log", math.nan),
            "sensitivity_rmse_log": math.nan,
            "qualitative_conclusion_changed": "unknown",
            "note": "Hydraulic late-window sensitivity remains unrun because the straight-section defended rows are preserved only as case-level means in the additive dependency package.",
        }
    )
    return rows_out


def sensitivity_row(
    asset_family: str,
    sensitivity_name: str,
    base_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
    base_fit: dict[str, Any],
    sensitivity_fit: dict[str, Any],
    note: str,
) -> dict[str, Any]:
    base_slope = fit_slope(base_fit)
    alt_slope = fit_slope(sensitivity_fit)
    changed = (
        base_fit.get("status") != sensitivity_fit.get("status")
        or (math.isfinite(base_slope) and math.isfinite(alt_slope) and math.copysign(1.0, base_slope) != math.copysign(1.0, alt_slope))
        or len(base_rows) != len(sensitivity_rows)
    )
    return {
        "asset_family": asset_family,
        "sensitivity_name": sensitivity_name,
        "status": "run",
        "base_row_count": len(base_rows),
        "sensitivity_row_count": len(sensitivity_rows),
        "row_count_delta": len(sensitivity_rows) - len(base_rows),
        "base_model_status": base_fit.get("status", "not_fit"),
        "sensitivity_model_status": sensitivity_fit.get("status", "not_fit"),
        "base_log_re_slope": base_slope,
        "sensitivity_log_re_slope": alt_slope,
        "log_re_slope_delta": alt_slope - base_slope if math.isfinite(base_slope) and math.isfinite(alt_slope) else math.nan,
        "base_rmse_log": base_fit.get("rmse_log", math.nan),
        "sensitivity_rmse_log": sensitivity_fit.get("rmse_log", math.nan),
        "qualitative_conclusion_changed": "yes" if changed else "no",
        "note": note,
    }


def fit_slope(fit_result: dict[str, Any]) -> float:
    if fit_result.get("status") != "fit":
        return math.nan
    names = fit_result.get("coefficient_names", [])
    if "log_re" not in names:
        return math.nan
    return float(fit_result["coefficients"][names.index("log_re")])


def make_thermal_sensitivity_rows(
    contexts: dict[str, CaseContext],
    branch_gate_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    base_times = build_thermal_timeseries_rows(contexts, branch_gate_rows, property_convention="branch_bulk")
    base_case = aggregate_thermal_case_rows(base_times)
    base_defended, base_exploratory = direct_thermal_fit_rows(base_case)
    base_fit = fit_power_law(base_defended, "mean_nu_effective", "mean_re_effective", "branch_name", "branch_aware_re_power_law", robust=False)
    base_exploratory_fit = fit_power_law(base_exploratory, "mean_nu_effective", "mean_re_effective", "branch_name", "branch_aware_re_power_law_screened_only", robust=False)

    rows_out = []
    for name, threshold in [("closure_gate_loose", 0.35), ("closure_gate_strict", 0.20)]:
        payload = [row for row in base_case if row["branch_name"] not in THERMAL_BLOCKED_BRANCHES | THERMAL_DERIVED_BRANCHES and finite_float(row.get("mean_residual_fraction_of_wall_heat")) <= threshold and row["branch_fit_status"] == "candidate"]
        fit = fit_power_law(payload, "mean_nu_effective", "mean_re_effective", "branch_name", "branch_aware_re_power_law", robust=False)
        rows_out.append(
            sensitivity_row(
                asset_family="thermal",
                sensitivity_name=name,
                base_rows=base_defended,
                sensitivity_rows=payload,
                base_fit=base_fit,
                sensitivity_fit=fit,
                note=f"Thermal closure gate rebuilt with mean residual fraction <= {threshold:.2f}.",
            )
        )

    case_probe_times = build_thermal_timeseries_rows(contexts, branch_gate_rows, property_convention="case_probe")
    case_probe_case = aggregate_thermal_case_rows(case_probe_times)
    case_probe_defended, case_probe_exploratory = direct_thermal_fit_rows(case_probe_case)
    case_probe_fit = fit_power_law(case_probe_exploratory, "mean_nu_effective", "mean_re_effective", "branch_name", "branch_aware_re_power_law_screened_only", robust=False)
    rows_out.append(
        sensitivity_row(
            asset_family="thermal",
            sensitivity_name="property_convention_case_probe",
            base_rows=base_exploratory,
            sensitivity_rows=case_probe_exploratory,
            base_fit=base_exploratory_fit,
            sensitivity_fit=case_probe_fit,
            note="Case-probe property convention uses probe_T_avg_K rather than branch bulk temperature when deriving Re and Nu.",
        )
    )

    latest_rows = []
    for row in base_times:
        latest_rows.append(row)
    latest_grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in latest_rows:
        key = (row["source_id"], row["branch_name"])
        current = latest_grouped.get(key)
        if current is None or float(row["time_s"]) > float(current["time_s"]):
            latest_grouped[key] = row
    latest_case = []
    for row in latest_grouped.values():
        latest_case.append(
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "branch_name": row["branch_name"],
                "branch_fit_status": row["branch_fit_status"],
                "mean_nu_effective": row["nu_effective"],
                "mean_re_effective": row["re_effective"],
                "mean_residual_fraction_of_wall_heat": row["residual_fraction_of_wall_heat"],
                "mean_support_fraction": row["support_fraction"],
                "min_delta_t_wall_bulk_mean_k": row["delta_t_wall_bulk_mean_k"],
                "max_residual_fraction_of_wall_heat": row["residual_fraction_of_wall_heat"],
                "direction_consistent_all_times": row["thermal_direction_consistent"] == "yes",
                "mean_grouped_reconstruction_fraction": row["grouped_reconstruction_fraction"],
                "fit_use_status": row["fit_use_status"],
            }
        )
    latest_exploratory = [row for row in latest_case if row["branch_name"] not in THERMAL_BLOCKED_BRANCHES | THERMAL_DERIVED_BRANCHES and row["branch_fit_status"] == "candidate" and finite_float(row.get("mean_nu_effective")) > 0.0]
    latest_fit = fit_power_law(latest_exploratory, "mean_nu_effective", "mean_re_effective", "branch_name", "branch_aware_re_power_law_screened_only", robust=False)
    rows_out.append(
        sensitivity_row(
            asset_family="thermal",
            sensitivity_name="late_window_latest_time_only",
            base_rows=base_exploratory,
            sensitivity_rows=latest_exploratory,
            base_fit=base_exploratory_fit,
            sensitivity_fit=latest_fit,
            note="Thermal target rebuilt from the latest retained time only instead of the retained-time case mean.",
        )
    )
    return rows_out


def build_provenance_rows() -> list[dict[str, Any]]:
    return [
        {
            "output_table": "hydraulic_fit_ready_rows.csv",
            "column_name": "target_value",
            "purpose": "Combined defended Salt hydraulic fit target.",
            "source_files": "reports/2026-06-18_ethan_salt_model_dependency_package/hydraulic_fit_ready_rows.csv; reports/2026-06-19_ethan_salt_feature_hydraulic_hardening/feature_fit_ready_rows.csv",
            "source_columns": "apparent_darcy_f_local or mean_keff_effective_local",
            "transformation_formula": "Straight rows carry local apparent Darcy f; feature rows carry local-boundary-reference K_eff.",
            "units": "1",
            "sign_convention": "Positive dissipative loss only.",
            "validity_gates": "Rows must already be fit_used in the respective hardening package.",
            "known_failure_modes": "Feature rows remain sensitive to the boundary-reference method until a full feature-path hydro integral exists.",
        },
        {
            "output_table": "thermal_fit_ready_rows.csv",
            "column_name": "mean_nu_effective",
            "purpose": "Closure-supported Salt thermal fit target.",
            "source_files": "reports/2026-06-19_ethan_salt_thermal_closure_hardening/thermal_fit_ready_rows.csv",
            "source_columns": "mean_nu_effective",
            "transformation_formula": "Case-level mean of exact retained-time section-integral Nu values after direct-branch closure gating.",
            "units": "1",
            "sign_convention": "Positive only.",
            "validity_gates": "No right_leg, no derived upcomer, support and residual gates must pass.",
            "known_failure_modes": "Few rows may survive even when raw branch support looks strong because enthalpy closure remains weak.",
        },
        {
            "output_table": "sensitivity_summary.csv",
            "column_name": "qualitative_conclusion_changed",
            "purpose": "Compact audit of dependency fragility under alternate thresholds or property conventions.",
            "source_files": "Derived inside build_ethan_salt_model_dependency_package_v2.py",
            "source_columns": "row counts, fit status, log_re slope, rmse",
            "transformation_formula": "Marks yes when row counts or model status change materially, or slope sign changes.",
            "units": "categorical",
            "sign_convention": "n/a",
            "validity_gates": "Only sensitivities runnable from preserved artifacts are marked run.",
            "known_failure_modes": "Hydraulic late-window sensitivity remains blocked by missing time-resolved defended straight-section means.",
        },
    ]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    content = f"""# Ethan Salt Model Dependency Package v2

Generated: `2026-06-19`

## What changed from v1

This package keeps the defended straight-section friction rows from the June 18
dependency package, adds a new feature-hydraulic hardening path from preserved
patch-`p_rgh` plus local-boundary references, and replaces the earlier mean-based
thermal audit with exact retained-time enthalpy and section-wall-heat closure.

## Counts

- hydraulic fit-used rows: `{summary["hydraulic_fit_used_count"]}`
- feature fit-used rows: `{summary["feature_fit_used_count"]}`
- thermal fit-used rows: `{summary["thermal_fit_used_count"]}`

## Recommendation status

- straight-section friction: `{summary["straight_section_status"]}`
- feature `K_eff`: `{summary["feature_status"]}`
- Salt HTC/Nu: `{summary["thermal_status"]}`

## Important limitations

- Feature `K_eff` is stronger than the residual-only June 18 path but still uses
  patch-endpoint `p_rgh` with a local straight-reference proxy rather than a full
  feature-path hydro integral.
- Salt Nu remains blocked unless enough direct closure-supported branches survive
  the thermal audit with adequate case diversity.
"""
    path.write_text(content, encoding="utf-8")


def write_handoff(
    path: Path,
    straight_rows: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    thermal_rows: list[dict[str, Any]],
    friction_results: dict[str, Any],
    thermal_results: dict[str, Any],
    sensitivity_rows: list[dict[str, Any]],
) -> None:
    content = f"""# Salt Model Dependency Handoff v2

## Straight-section friction

- status: `{friction_results['straight_section_dependency']['recommended_status']}`
- model: `{friction_results['straight_section_dependency']['recommended_model']}`
- fit-used rows: `{len(straight_rows)}`

## Feature K_eff

- status: `{friction_results['feature_dependency']['recommended_status']}`
- model: `{friction_results['feature_dependency']['recommended_model']}`
- fit-used rows: `{len(feature_rows)}`

## Salt HTC/Nu

- status: `{thermal_results['recommended_status']}`
- model: `{thermal_results['recommended_model']}`
- fit-used rows: `{len(thermal_rows)}`

## Exact fit-used hydraulic rows

{chr(10).join(f"- `{row['source_id']}` / `{row['asset_family']}` / `{row['category_name']}` / `Re={finite_float(row.get('re_effective')):.3f}` / `target={finite_float(row.get('target_value')):.3f}`" for row in straight_rows + feature_rows)}

## Exact fit-used thermal rows

{chr(10).join(f"- `{row['source_id']}` / `{row['branch_name']}` / `Re={finite_float(row.get('mean_re_effective')):.3f}` / `Nu={finite_float(row.get('mean_nu_effective')):.3f}`" for row in thermal_rows) or "- none"}

## Sensitivity highlights

{chr(10).join(f"- `{row['asset_family']}` / `{row['sensitivity_name']}` / `{row['qualitative_conclusion_changed']}` / {row['note']}" for row in sensitivity_rows)}

## Water extension plan

1. repeat the feature local-boundary reference path on the water-family raw case-analysis roots
2. rerun the exact retained-time thermal closure package with water-side `rho*u*cp` property weighting
3. only then build a water-family dependency package with the same defended/screened split used here
"""
    path.write_text(content, encoding="utf-8")


def write_water_extension_todo(path: Path) -> None:
    content = """# Water Extension TODO

1. Rebuild the feature hydraulic hardening package on the preserved water-family
   raw case-analysis roots using the same local-boundary-reference method.
2. Rebuild the thermal closure package with the exact water-side `rho*u*cp`
   property convention already established in the June 17 pressure / HTC /
   boundary-layer package.
3. Reapply the same closure gates used here:
   - no derived overlapping branches in defended fitting
   - explicit branch support and `|Twall - Tbulk|` thresholds
   - explicit enthalpy-vs-wall residual threshold
   - explicit direct-vs-shear hydraulic disagreement reporting
4. Publish a water-family dependency package only after the closure-supported
   water rows are counted and sensitivity-tested separately from Salt.
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None
    contexts = load_case_contexts(source_ids)
    feature_dir = Path(args.feature_dir)
    thermal_dir = Path(args.thermal_dir)

    # Ensure the hardening packages exist by reading their outputs after they are built externally.
    feature_case_rows = normalize_feature_case_rows(load_csv_rows(feature_dir / "feature_hydro_closure_by_case.csv"))
    if source_ids:
        feature_case_rows = [row for row in feature_case_rows if row["source_id"] in source_ids]
    thermal_case_rows = load_thermal_case_rows(thermal_dir, source_ids)
    straight_rows, straight_audit_rows = load_straight_rows(source_ids)

    feature_rows, feature_stability = stable_feature_fit_rows(feature_case_rows)
    defended_thermal_rows, exploratory_thermal_rows = direct_thermal_fit_rows(thermal_case_rows)

    straight_constant = fit_geometric_constant(straight_rows, "target_value", "category_name")
    straight_power = fit_power_law(straight_rows, "target_value", "re_effective", "category_name", "class_aware_re_power_law", robust=False)
    feature_constant = fit_geometric_constant(feature_rows, "target_value", "category_name")
    feature_power = fit_power_law(feature_rows, "target_value", "re_effective", "category_name", "feature_name_aware_re_power_law", robust=False)
    thermal_defended_fit = fit_power_law(defended_thermal_rows, "mean_nu_effective", "mean_re_effective", "branch_name", "branch_aware_re_power_law", robust=False)
    thermal_exploratory_fit = fit_power_law(exploratory_thermal_rows, "mean_nu_effective", "mean_re_effective", "branch_name", "branch_aware_re_power_law_screened_only", robust=False)

    straight_status, straight_model = choose_defended_recommendation(straight_rows, straight_constant, straight_power, FRICTION_DEFENDED_MIN_ROWS)
    feature_status, feature_model = choose_defended_recommendation(feature_rows, feature_constant, feature_power, FEATURE_CASE_MIN)
    thermal_status, thermal_model = (
        ("provisional_defended", thermal_defended_fit["model_type"])
        if thermal_defended_fit.get("status") == "fit" and len(defended_thermal_rows) >= THERMAL_DEFENDED_MIN_ROWS and case_share_ok(defended_thermal_rows)
        else ("not_defensible_yet", "exploratory_screened_only_model" if thermal_exploratory_fit.get("status") == "fit" else "insufficient_closure_supported_rows")
    )

    friction_results = {
        "straight_section_dependency": {
            "recommended_status": straight_status,
            "recommended_model": straight_model,
            "constant_model": straight_constant,
            "power_model": straight_power,
            "fit_used_row_count": len(straight_rows),
        },
        "feature_dependency": {
            "recommended_status": feature_status,
            "recommended_model": feature_model,
            "stability_fraction_by_feature": feature_stability,
            "constant_model": feature_constant,
            "power_model": feature_power,
            "fit_used_row_count": len(feature_rows),
        },
    }
    thermal_results = {
        "recommended_status": thermal_status,
        "recommended_model": thermal_model,
        "defended_model": thermal_defended_fit,
        "exploratory_model": thermal_exploratory_fit,
        "fit_used_row_count": len(defended_thermal_rows),
        "screened_row_count": len(exploratory_thermal_rows),
    }

    branch_gate_rows = load_branch_gate_rows(source_ids)
    feature_inputs = load_feature_inputs(source_ids)
    sensitivity_rows = make_hydraulic_sensitivity_rows(straight_audit_rows, contexts, feature_inputs) + make_thermal_sensitivity_rows(contexts, branch_gate_rows)

    output_dir = ensure_dir(Path(args.output_dir))
    hydraulic_rows = straight_rows + feature_rows
    hydraulic_fieldnames = (
        list(dict.fromkeys(key for row in hydraulic_rows for key in row.keys()))
        if hydraulic_rows
        else [
            "asset_family",
            "source_id",
            "case_label",
            "category_name",
            "category_class",
            "re_effective",
            "target_value",
            "pressure_method_status",
            "support_fraction",
        ]
    )
    thermal_case_fieldnames = list(thermal_case_rows[0].keys()) if thermal_case_rows else [
        "source_id",
        "case_label",
        "branch_name",
        "branch_type",
        "component_spans",
        "branch_fit_status",
        "branch_fit_reason",
        "mean_q_enthalpy_w",
        "mean_q_wall_total_w",
        "mean_q_intended_transfer_w",
        "mean_q_external_or_loss_w",
        "mean_q_sink_or_cooling_w",
        "mean_q_junction_or_unresolved_w",
        "mean_q_bulk_centerline_correction_proxy_w",
        "mean_q_residual_w",
        "mean_residual_fraction_of_wall_heat",
        "max_residual_fraction_of_wall_heat",
        "mean_grouped_reconstruction_fraction",
        "mean_support_fraction",
        "min_delta_t_wall_bulk_mean_k",
        "min_delta_t_wall_bulk_min_k",
        "mean_htc_effective_w_m2_k",
        "mean_nu_effective",
        "mean_re_effective",
        "mean_pr_effective",
        "mean_pe_effective",
        "mean_bulk_minus_centerline_temp_k",
        "pass_time_fraction",
        "direction_consistent_all_times",
        "role_label",
        "time_sample_count",
        "fit_use_status",
        "exclusion_reason_primary",
        "exclusion_reasons_json",
    ]
    csv_dump_rows(output_dir / "hydraulic_fit_ready_rows.csv", hydraulic_rows, fieldnames=hydraulic_fieldnames)
    straight_exclusions = []
    for row in straight_audit_rows:
        if row.get("asset_family") != "straight_section_friction":
            continue
        if row.get("fit_use_status") == "fit_used":
            continue
        straight_exclusions.append(
            {
                "asset_family": "straight_section_friction",
                "fit_use_status": row.get("fit_use_status", ""),
                "exclusion_reason_primary": row.get("exclusion_reason_primary", ""),
            }
        )
    feature_exclusions = [
        {
            "asset_family": "feature_keff",
            "fit_use_status": row.get("fit_use_status", ""),
            "exclusion_reason_primary": row.get("exclusion_reason_primary", ""),
        }
        for row in feature_case_rows
        if row.get("fit_use_status") != "fit_used"
    ]
    csv_dump_rows(
        output_dir / "hydraulic_exclusion_summary.csv",
        summarize_exclusions(straight_exclusions + feature_exclusions, "asset_family"),
        fieldnames=["asset_family", "fit_use_status", "exclusion_reason_primary", "row_count"],
    )
    csv_dump_rows(output_dir / "thermal_fit_ready_rows.csv", defended_thermal_rows, fieldnames=thermal_case_fieldnames)
    csv_dump_rows(output_dir / "thermal_exclusion_summary.csv", summarize_exclusions(
        [
            {
                "asset_family": "thermal_branch",
                "fit_use_status": row.get("fit_use_status", ""),
                "exclusion_reason_primary": row.get("exclusion_reason_primary", ""),
            }
            for row in thermal_case_rows
        ],
        "asset_family",
    ), fieldnames=["asset_family", "fit_use_status", "exclusion_reason_primary", "row_count"])
    json_dump(output_dir / "salt_friction_fit_results.json", friction_results)
    json_dump(output_dir / "salt_nu_fit_results.json", thermal_results)
    csv_dump_rows(output_dir / "sensitivity_summary.csv", sensitivity_rows, fieldnames=list(sensitivity_rows[0].keys()))
    provenance_rows = build_provenance_rows()
    csv_dump_rows(output_dir / "provenance_map.csv", provenance_rows, fieldnames=list(provenance_rows[0].keys()))

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(contexts),
        "hydraulic_fit_used_count": len(straight_rows) + len(feature_rows),
        "feature_fit_used_count": len(feature_rows),
        "thermal_fit_used_count": len(defended_thermal_rows),
        "straight_section_status": straight_status,
        "feature_status": feature_status,
        "thermal_status": thermal_status,
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir / "README.md", summary)
    write_handoff(output_dir / "model_dependency_handoff.md", straight_rows, feature_rows, defended_thermal_rows, friction_results, thermal_results, sensitivity_rows)
    write_water_extension_todo(output_dir / "water_extension_todo.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
