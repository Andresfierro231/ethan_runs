#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import numpy as np

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, load_yaml, safe_float  # noqa: E402


DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_model_dependency_package"
DEFAULT_SMOKE_OUTPUT_DIR = ROOT / "tmp" / "2026-06-18_ethan_salt_model_dependency_package_smoke"

CHECKPOINT_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_analysis_checkpoint_suite"
SALT_CLOSURE_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package"
PRESSURE_DIR = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package"
DASHBOARD_DIR = ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package"
FIELD_TRANSPORT_DIR = ROOT / "reports" / "2026-06-15_ethan_all_runs_field_transport_campaign"
HEAT_AUDIT_DIR = ROOT / "reports" / "2026-06-09_ethan_steady_state_heat_flow_audit"
CASE_METADATA_CSV = ROOT / "reports" / "2026-06-04_ethan_case_metadata_index" / "ethan_case_metadata_index.csv"

THERMAL_USABLE_FRACTION_MIN = 0.90
THERMAL_WARNING_FRACTION_MAX = 0.10
THERMAL_MIN_DELTA_T_K = 0.50
THERMAL_MIN_CLOSURE_ROWS = 8
THERMAL_ENTHALPY_RESIDUAL_MAX = 0.15
THERMAL_GROUP_RECONSTRUCTION_MAX = 0.05
THERMAL_DIRECTION_MIN_MAGNITUDE_W = 1.0
THERMAL_COMPOSITE_BRANCHES = {"upcomer"}
THERMAL_BLOCKED_BRANCHES = {"right_leg"}

HYDRAULIC_SUPPORT_MIN = 0.75
HYDRAULIC_RATIO_MIN = 0.50
HYDRAULIC_RATIO_MAX = 2.00
HYDRAULIC_MIN_ROWS = 8

BOOTSTRAP_SEED = 20260618
BOOTSTRAP_SAMPLES = 250
HUBER_DELTA = 1.35


THERMAL_DECOMPOSITION_COLUMNS = [
    "source_id",
    "case_label",
    "branch_name",
    "branch_type",
    "component_spans",
    "component_span_count",
    "is_derived_branch",
    "role_label",
    "heater_power_w",
    "cooling_power_w",
    "insulation_thickness_in",
    "cooler_h_w_m2k",
    "case_probe_t_avg_k",
    "branch_bulk_temp_k",
    "branch_wall_temp_k",
    "branch_bulk_minus_wall_temp_k",
    "branch_abs_bulk_minus_wall_temp_k",
    "branch_min_abs_bulk_minus_wall_temp_k",
    "bulk_minus_centerline_temp_k",
    "support_fraction",
    "thermal_warning_fraction",
    "branch_fit_status_screened",
    "branch_fit_reason_screened",
    "q_enthalpy_w",
    "q_wall_total_w",
    "q_streamwise_total_w",
    "q_grouped_total_w",
    "q_intended_transfer_w",
    "q_parasitic_loss_w",
    "q_intended_heating_w",
    "q_intended_cooling_w",
    "q_parasitic_gain_w",
    "q_parasitic_cooling_w",
    "q_external_or_loss_w",
    "q_sink_or_cooling_w",
    "q_group_reconstruction_residual_w",
    "q_enthalpy_minus_wall_w",
    "residual_fraction_of_wall_heat",
    "group_reconstruction_fraction",
    "thermal_direction_consistent",
    "q_wall_sign",
    "q_enthalpy_sign",
    "dh_effective_m",
    "bulk_velocity_effective_m_s",
    "property_temperature_k",
    "rho_effective_kg_m3",
    "mu_effective_pa_s",
    "cp_effective_j_kg_k",
    "k_effective_w_m_k",
    "re_effective",
    "pr_effective",
    "pe_effective",
    "htc_effective_w_m2_k",
    "nu_effective",
    "ambient_proxy_fraction_of_heater",
    "cooling_removal_fraction_of_heater",
    "junction_loss_fraction_of_heater",
    "net_heat_imbalance_fraction_of_heater",
    "screened_candidate_flag",
    "closure_supported_candidate_flag",
    "fit_use_status",
    "exclusion_reason_primary",
    "exclusion_reasons_json",
]

HYDRAULIC_AUDIT_COLUMNS = [
    "asset_family",
    "source_id",
    "case_label",
    "scope_name",
    "scope_kind",
    "pressure_method_label",
    "pressure_method_status",
    "screened_candidate_flag",
    "closure_supported_candidate_flag",
    "fit_use_status",
    "fit_status_screened",
    "fit_reason_screened",
    "net_section_role",
    "support_fraction",
    "pressure_loss_hydro_pa",
    "apparent_darcy_f_local",
    "direct_prgh_darcy",
    "shear_darcy_core",
    "direct_to_shear_darcy_ratio",
    "pressure_loss_to_driving_head_ratio",
    "dh_effective_m",
    "bulk_velocity_effective_m_s",
    "rho_effective_kg_m3",
    "mu_effective_pa_s",
    "re_effective",
    "property_temperature_k",
    "residual_risk_label",
    "todo_required",
    "missing_requirement",
    "exclusion_reason_primary",
    "exclusion_reasons_json",
]

THERMAL_FIT_READY_COLUMNS = [
    "source_id",
    "case_label",
    "branch_name",
    "branch_type",
    "role_label",
    "re_effective",
    "pr_effective",
    "pe_effective",
    "htc_effective_w_m2_k",
    "nu_effective",
    "support_fraction",
    "residual_fraction_of_wall_heat",
    "bulk_minus_centerline_temp_k",
    "property_temperature_k",
    "fit_use_status",
]

HYDRAULIC_FIT_READY_COLUMNS = [
    "source_id",
    "case_label",
    "scope_name",
    "scope_kind",
    "re_effective",
    "apparent_darcy_f_local",
    "pressure_loss_hydro_pa",
    "support_fraction",
    "direct_to_shear_darcy_ratio",
    "property_temperature_k",
    "fit_use_status",
]

SENSITIVITY_COLUMNS = [
    "asset_family",
    "sensitivity_name",
    "status",
    "base_row_count",
    "sensitivity_row_count",
    "row_count_delta",
    "base_model_status",
    "sensitivity_model_status",
    "base_log_re_slope",
    "sensitivity_log_re_slope",
    "log_re_slope_delta",
    "base_rmse_log",
    "sensitivity_rmse_log",
    "qualitative_conclusion_changed",
    "note",
]

PROVENANCE_COLUMNS = [
    "output_table",
    "column_name",
    "purpose",
    "source_files",
    "source_columns",
    "transformation_formula",
    "units",
    "sign_convention",
    "validity_gates",
    "known_failure_modes",
]


@dataclass(frozen=True)
class PropertyModel:
    mu_type: str
    mu_coeffs: tuple[float, ...]
    cp_coeffs: tuple[float, ...]
    rho_coeffs: tuple[float, ...]
    k_coeffs: tuple[float, ...]


@dataclass(frozen=True)
class CaseContext:
    source_id: str
    case_label: str
    display_label: str
    variant_label: str
    source_root: Path
    package_root: Path
    heater_power_w: float
    cooling_power_w: float
    insulation_thickness_in: float
    cooler_h_w_m2k: float
    probe_t_avg_k: float
    property_model: PropertyModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an additive Salt-only model-dependency package that turns the "
            "screened closure artifacts into defensible friction and HTC/Nu "
            "dependency evidence with full provenance and sensitivity reporting."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Optional bounded rebuild of one or more Salt source IDs.",
    )
    return parser.parse_args()


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require_columns(rows: list[dict[str, str]], required: Sequence[str], table_name: str) -> None:
    if not rows:
        raise RuntimeError(f"{table_name} is empty; cannot continue")
    missing = [column for column in required if column not in rows[0]]
    if missing:
        raise RuntimeError(f"{table_name} missing required columns: {missing}")


def finite_float(value: Any, default: float = math.nan) -> float:
    parsed = safe_float(value)
    if parsed is None or not math.isfinite(parsed):
        return default
    return float(parsed)


def is_finite(value: Any) -> bool:
    parsed = safe_float(value)
    return parsed is not None and math.isfinite(parsed)


def safe_mean(values: Iterable[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload) / len(payload))


def safe_sum(values: Iterable[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload))


def bool_text(flag: bool) -> str:
    return "yes" if flag else "no"


def sign_token(value: float, zero_tol: float = 0.0) -> str:
    if not math.isfinite(value):
        return "nan"
    if value > zero_tol:
        return "positive"
    if value < -zero_tol:
        return "negative"
    return "zero"


def normalized_residual(residual_value: float, reference_value: float) -> float:
    if not math.isfinite(residual_value) or not math.isfinite(reference_value) or abs(reference_value) == 0.0:
        return math.nan
    return float(abs(residual_value) / abs(reference_value))


def polynomial_eval(coeffs: Sequence[float], temperature_k: float) -> float:
    if not math.isfinite(temperature_k):
        return math.nan
    return float(sum(float(coeff) * (temperature_k ** index) for index, coeff in enumerate(coeffs)))


def exp_inv_t_eval(coeffs: Sequence[float], temperature_k: float) -> float:
    if not math.isfinite(temperature_k) or temperature_k == 0.0 or not coeffs:
        return math.nan
    a = float(coeffs[0])
    exponent = 0.0
    for power_index, coeff in enumerate(coeffs[1:], start=1):
        exponent += float(coeff) / (temperature_k ** power_index)
    return float(a * math.exp(exponent))


def evaluate_mu(model: PropertyModel, temperature_k: float) -> float:
    if model.mu_type == "expInvT":
        return exp_inv_t_eval(model.mu_coeffs, temperature_k)
    if model.mu_type == "polynomial":
        return polynomial_eval(model.mu_coeffs, temperature_k)
    raise RuntimeError(f"unsupported mu_spec type: {model.mu_type}")


def evaluate_cp(model: PropertyModel, temperature_k: float) -> float:
    return polynomial_eval(model.cp_coeffs, temperature_k)


def evaluate_rho(model: PropertyModel, temperature_k: float) -> float:
    return polynomial_eval(model.rho_coeffs, temperature_k)


def evaluate_k(model: PropertyModel, temperature_k: float) -> float:
    return polynomial_eval(model.k_coeffs, temperature_k)


def filter_salt_rows(rows: list[dict[str, str]], source_ids: set[str] | None = None) -> list[dict[str, str]]:
    payload = [row for row in rows if row.get("source_id")]
    payload = [row for row in payload if "water" not in row["source_id"].lower()]
    if source_ids:
        payload = [row for row in payload if row["source_id"] in source_ids]
    return payload


def case_sort_key(source_id: str, order_map: dict[str, int]) -> tuple[int, str]:
    return order_map.get(source_id, 999), source_id


def csv_rows_for_empty_schema(columns: Sequence[str]) -> list[dict[str, Any]]:
    return []


def load_case_contexts(source_ids: set[str] | None = None) -> dict[str, CaseContext]:
    metadata_rows = filter_salt_rows(load_csv_rows(CASE_METADATA_CSV), source_ids)
    dashboard_rows = filter_salt_rows(load_csv_rows(DASHBOARD_DIR / "salt_dashboard.csv"), source_ids)
    require_columns(metadata_rows, ["source_id", "source_root", "cooler_h_W_m2K"], "ethan_case_metadata_index.csv")
    require_columns(dashboard_rows, ["source_id", "display_label", "package_root"], "salt_dashboard.csv")
    dashboard_map = {row["source_id"]: row for row in dashboard_rows}
    contexts: dict[str, CaseContext] = {}
    for row in metadata_rows:
        source_id = row["source_id"]
        dashboard = dashboard_map.get(source_id)
        if dashboard is None:
            continue
        source_root = Path(row["source_root"])
        if not (source_root / "case_config.yaml").exists():
            runtime_root = Path(row.get("active_runtime_root", ""))
            if (runtime_root / "case_config.yaml").exists():
                source_root = runtime_root
        case_config = load_yaml(source_root / "case_config.yaml")
        fluid_props = case_config["fluid_properties"]
        mu_spec = fluid_props["mu_spec"]
        model = PropertyModel(
            mu_type=str(mu_spec["type"]),
            mu_coeffs=tuple(float(value) for value in mu_spec["coeffs"]),
            cp_coeffs=tuple(float(value) for value in fluid_props["Cp_coeffs"]),
            rho_coeffs=tuple(float(value) for value in fluid_props["rho_coeffs"]),
            k_coeffs=tuple(float(value) for value in fluid_props["kappa_spec"]["coeffs"]),
        )
        contexts[source_id] = CaseContext(
            source_id=source_id,
            case_label=row["exp_case_name"],
            display_label=dashboard["display_label"],
            variant_label=row["variant_label"],
            source_root=source_root,
            package_root=Path(dashboard["package_root"]),
            heater_power_w=finite_float(row.get("heater_power_W")),
            cooling_power_w=finite_float(row.get("cooling_power_W")),
            insulation_thickness_in=finite_float(row.get("three_d_outer_insulation_thickness_in")),
            cooler_h_w_m2k=finite_float(row.get("cooler_h_W_m2K")),
            probe_t_avg_k=finite_float(row.get("probe_T_avg_K")),
            property_model=model,
        )
    if not contexts:
        raise RuntimeError("no Salt case contexts resolved")
    return contexts


def branch_component_map(rows: list[dict[str, str]]) -> dict[tuple[str, str], tuple[str, ...]]:
    mapping: dict[tuple[str, str], tuple[str, ...]] = {}
    for row in rows:
        component_spans = tuple(part.strip() for part in row["component_spans"].split(",") if part.strip())
        mapping[(row["source_id"], row["branch_name"])] = component_spans
    return mapping


def aggregate_grouped_heat(
    rows: list[dict[str, str]],
    component_map: dict[tuple[str, str], tuple[str, ...]],
) -> dict[tuple[str, str], dict[str, float]]:
    span_group_values: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in rows:
        key = (row["source_id"], row["span_name"])
        q_value = finite_float(row.get("mean_wall_heat_w"))
        if not math.isfinite(q_value):
            continue
        group = row["thermal_role_group"]
        span_group_values[key][group] += q_value
        if group == "intended_transfer":
            if q_value > 0.0:
                span_group_values[key]["intended_heating"] += q_value
            elif q_value < 0.0:
                span_group_values[key]["intended_cooling"] += q_value
        if group == "parasitic_loss":
            if q_value > 0.0:
                span_group_values[key]["parasitic_gain"] += q_value
            elif q_value < 0.0:
                span_group_values[key]["parasitic_cooling"] += q_value

    branch_values: dict[tuple[str, str], dict[str, float]] = {}
    for branch_key, component_spans in component_map.items():
        branch_payload: dict[str, float] = defaultdict(float)
        for span_name in component_spans:
            span_payload = span_group_values.get((branch_key[0], span_name), {})
            for key, value in span_payload.items():
                branch_payload[key] += value
        branch_values[branch_key] = dict(branch_payload)
    return branch_values


def aggregate_streamwise_heat(rows: list[dict[str, str]], component_map: dict[tuple[str, str], tuple[str, ...]]) -> dict[tuple[str, str], float]:
    span_values: dict[tuple[str, str], float] = defaultdict(float)
    for row in rows:
        q_value = finite_float(row.get("mean_wall_heat_w"))
        if math.isfinite(q_value):
            span_values[(row["source_id"], row["span_name"])] += q_value
    branch_values: dict[tuple[str, str], float] = {}
    for branch_key, component_spans in component_map.items():
        branch_values[branch_key] = float(sum(span_values.get((branch_key[0], span_name), 0.0) for span_name in component_spans))
    return branch_values


def aggregate_bulk_centerline(rows: list[dict[str, str]], component_map: dict[tuple[str, str], tuple[str, ...]]) -> dict[tuple[str, str], float]:
    span_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in filter_salt_rows(rows):
        value = finite_float(row.get("bulk_minus_centerline_temp_k"))
        if math.isfinite(value):
            span_values[(row["source_id"], row["span_name"])].append(value)
    branch_values: dict[tuple[str, str], float] = {}
    for branch_key, component_spans in component_map.items():
        payload: list[float] = []
        for span_name in component_spans:
            payload.extend(span_values.get((branch_key[0], span_name), []))
        branch_values[branch_key] = safe_mean(payload)
    return branch_values


def direct_span_lookup(rows: list[dict[str, str]], key_name: str = "span_name") -> dict[tuple[str, str], dict[str, str]]:
    return {(row["source_id"], row[key_name]): row for row in rows}


def case_heat_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["source_id"]: row for row in rows}


def classify_role_label(q_intended_transfer_w: float, q_parasitic_loss_w: float) -> str:
    intended_mag = abs(q_intended_transfer_w) if math.isfinite(q_intended_transfer_w) else 0.0
    parasitic_mag = abs(q_parasitic_loss_w) if math.isfinite(q_parasitic_loss_w) else 0.0
    if intended_mag >= 1.5 * parasitic_mag and q_intended_transfer_w > 0.0:
        return "intended_heating_dominant"
    if intended_mag >= 1.5 * parasitic_mag and q_intended_transfer_w < 0.0:
        return "intended_cooling_dominant"
    if parasitic_mag >= 1.5 * intended_mag and q_parasitic_loss_w < 0.0:
        return "parasitic_cooling_dominant"
    if parasitic_mag >= 1.5 * intended_mag and q_parasitic_loss_w > 0.0:
        return "parasitic_gain_dominant"
    return "mixed_role"


def classify_thermal_row(
    branch_name: str,
    is_derived_branch: bool,
    branch_fit_status_screened: str,
    branch_fit_reason_screened: str,
    support_fraction: float,
    warning_fraction: float,
    min_abs_delta_t_k: float,
    residual_fraction: float,
    direction_consistent: bool,
    group_reconstruction_fraction: float,
) -> tuple[str, str, list[str], bool, bool]:
    reasons: list[str] = []
    screened_candidate = branch_fit_status_screened == "candidate"
    closure_supported = True
    if branch_name in THERMAL_BLOCKED_BRANCHES:
        reasons.append("right_leg_blocked_by_policy")
        closure_supported = False
    if is_derived_branch:
        reasons.append("derived_branch_overlap_double_counting")
        closure_supported = False
    if not screened_candidate:
        reasons.append(branch_fit_reason_screened or "branch_screened_not_candidate")
        closure_supported = False
    if not math.isfinite(support_fraction) or support_fraction < THERMAL_USABLE_FRACTION_MIN:
        reasons.append("support_fraction_below_candidate_gate")
        closure_supported = False
    if math.isfinite(warning_fraction) and warning_fraction > THERMAL_WARNING_FRACTION_MAX:
        reasons.append("thermal_warning_fraction_above_candidate_gate")
        closure_supported = False
    if not math.isfinite(min_abs_delta_t_k) or min_abs_delta_t_k < THERMAL_MIN_DELTA_T_K:
        reasons.append("weak_twall_minus_tbulk_support")
        closure_supported = False
    if not math.isfinite(residual_fraction) or residual_fraction > THERMAL_ENTHALPY_RESIDUAL_MAX:
        reasons.append("enthalpy_wall_heat_balance_loose")
        closure_supported = False
    if not direction_consistent:
        reasons.append("enthalpy_wall_direction_inconsistent")
        closure_supported = False
    if not math.isfinite(group_reconstruction_fraction) or group_reconstruction_fraction > THERMAL_GROUP_RECONSTRUCTION_MAX:
        reasons.append("grouped_heat_reconstruction_mismatch")
        closure_supported = False

    if closure_supported:
        return "fit_used", "closure_supported", [], screened_candidate, True
    if branch_name in THERMAL_BLOCKED_BRANCHES:
        return "excluded", "right_leg_blocked_by_policy", reasons, screened_candidate, False
    if screened_candidate and is_derived_branch:
        return "sensitivity_only", "derived_branch_overlap_double_counting", reasons, screened_candidate, False
    if screened_candidate and not is_derived_branch:
        return "sensitivity_only", reasons[0] if reasons else "screened_candidate_not_closure_supported", reasons, screened_candidate, False
    return "excluded", reasons[0] if reasons else "excluded_by_gate", reasons, screened_candidate, False


def classify_hydraulic_row(
    asset_family: str,
    fit_status_screened: str,
    fit_reason_screened: str,
    pressure_method_status: str,
) -> tuple[str, str, list[str], bool, bool]:
    reasons: list[str] = []
    screened_candidate = fit_status_screened == "candidate"
    closure_supported = screened_candidate and pressure_method_status == "defended_direct_hydro"
    if not screened_candidate:
        reasons.append(fit_reason_screened or "screened_not_candidate")
    if pressure_method_status != "defended_direct_hydro":
        reasons.append("feature_pressure_method_residual_only")
    if asset_family == "feature_keff":
        return "excluded", reasons[0] if reasons else "feature_pressure_method_residual_only", reasons, screened_candidate, False
    if closure_supported:
        return "fit_used", "closure_supported", [], screened_candidate, True
    if screened_candidate:
        return "sensitivity_only", reasons[0] if reasons else "screened_candidate_not_closure_supported", reasons, screened_candidate, False
    return "excluded", reasons[0] if reasons else "excluded_by_gate", reasons, screened_candidate, False


def fit_geometric_constant(rows: list[dict[str, Any]], target_key: str, group_key: str | None = None) -> dict[str, Any]:
    valid_rows = [row for row in rows if finite_float(row.get(target_key)) > 0.0]
    if not valid_rows:
        return {"status": "not_fit", "reason": "no_positive_rows"}
    if group_key is None:
        values = [math.log(finite_float(row[target_key])) for row in valid_rows]
        center = float(np.mean(values))
        predictions = np.full(len(valid_rows), center)
        labels = ["intercept"]
        coefficients = [center]
    else:
        groups = sorted({str(row[group_key]) for row in valid_rows})
        labels = [f"group:{group}" for group in groups]
        coefficients = []
        predictions = np.zeros(len(valid_rows), dtype=float)
        for index, group in enumerate(groups):
            group_values = [math.log(finite_float(row[target_key])) for row in valid_rows if str(row[group_key]) == group]
            center = float(np.mean(group_values))
            coefficients.append(center)
            for row_index, row in enumerate(valid_rows):
                if str(row[group_key]) == group:
                    predictions[row_index] = center
    observed = np.array([math.log(finite_float(row[target_key])) for row in valid_rows], dtype=float)
    residual = observed - predictions
    return {
        "status": "fit",
        "model_type": "geometric_constant",
        "row_count": len(valid_rows),
        "coefficient_names": labels,
        "coefficients": coefficients,
        "rmse_log": float(np.sqrt(np.mean(residual ** 2))),
        "mae_log": float(np.mean(np.abs(residual))),
        "r2_log": float(1.0 - np.sum(residual ** 2) / np.sum((observed - np.mean(observed)) ** 2)) if len(valid_rows) > 1 else math.nan,
    }


def design_matrix(
    rows: list[dict[str, Any]],
    target_key: str,
    re_key: str,
    category_key: str,
) -> tuple[np.ndarray, np.ndarray, list[str], list[dict[str, Any]]]:
    valid_rows = []
    for row in rows:
        target = finite_float(row.get(target_key))
        re_value = finite_float(row.get(re_key))
        if target > 0.0 and re_value > 0.0:
            valid_rows.append(row)
    if not valid_rows:
        return np.zeros((0, 0)), np.zeros((0,)), [], []
    categories = sorted({str(row[category_key]) for row in valid_rows})
    labels = ["intercept", "log_re"] + [f"{category_key}:{category}" for category in categories[1:]]
    x_matrix = np.ones((len(valid_rows), len(labels)), dtype=float)
    y_vector = np.array([math.log(finite_float(row[target_key])) for row in valid_rows], dtype=float)
    for row_index, row in enumerate(valid_rows):
        x_matrix[row_index, 1] = math.log(finite_float(row[re_key]))
        for cat_index, category in enumerate(categories[1:], start=2):
            x_matrix[row_index, cat_index] = 1.0 if str(row[category_key]) == category else 0.0
    return x_matrix, y_vector, labels, valid_rows


def ols_fit(x_matrix: np.ndarray, y_vector: np.ndarray) -> np.ndarray:
    coefficients, *_ = np.linalg.lstsq(x_matrix, y_vector, rcond=None)
    return coefficients


def huber_fit(x_matrix: np.ndarray, y_vector: np.ndarray, delta: float = HUBER_DELTA, max_iter: int = 30) -> np.ndarray:
    coefficients = ols_fit(x_matrix, y_vector)
    for _ in range(max_iter):
        residual = y_vector - x_matrix @ coefficients
        abs_residual = np.abs(residual)
        weights = np.ones_like(abs_residual)
        mask = abs_residual > delta
        weights[mask] = delta / abs_residual[mask]
        weighted_x = x_matrix * weights[:, None]
        weighted_y = y_vector * weights
        next_coefficients = ols_fit(weighted_x, weighted_y)
        if np.allclose(coefficients, next_coefficients, rtol=1e-8, atol=1e-10):
            coefficients = next_coefficients
            break
        coefficients = next_coefficients
    return coefficients


def fit_power_law(
    rows: list[dict[str, Any]],
    target_key: str,
    re_key: str,
    category_key: str,
    model_name: str,
    robust: bool,
) -> dict[str, Any]:
    x_matrix, y_vector, labels, valid_rows = design_matrix(rows, target_key, re_key, category_key)
    if len(valid_rows) < 3 or x_matrix.shape[1] >= len(valid_rows):
        return {"status": "not_fit", "reason": "insufficient_rows_or_rank"}
    coefficients = huber_fit(x_matrix, y_vector) if robust else ols_fit(x_matrix, y_vector)
    predictions = x_matrix @ coefficients
    residual = y_vector - predictions
    bootstrap = bootstrap_coefficients(valid_rows, target_key, re_key, category_key, robust)
    return {
        "status": "fit",
        "model_type": model_name,
        "row_count": len(valid_rows),
        "coefficient_names": labels,
        "coefficients": [float(value) for value in coefficients],
        "rmse_log": float(np.sqrt(np.mean(residual ** 2))),
        "mae_log": float(np.mean(np.abs(residual))),
        "r2_log": float(1.0 - np.sum(residual ** 2) / np.sum((y_vector - np.mean(y_vector)) ** 2)) if len(valid_rows) > 1 else math.nan,
        "bootstrap_ci95": bootstrap,
    }


def bootstrap_coefficients(
    rows: list[dict[str, Any]],
    target_key: str,
    re_key: str,
    category_key: str,
    robust: bool,
) -> dict[str, list[float]]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    x_matrix, y_vector, labels, valid_rows = design_matrix(rows, target_key, re_key, category_key)
    if len(valid_rows) < 3 or x_matrix.shape[1] >= len(valid_rows):
        return {}
    samples: dict[str, list[float]] = {label: [] for label in labels}
    for _ in range(BOOTSTRAP_SAMPLES):
        indices = rng.integers(0, len(valid_rows), size=len(valid_rows))
        sampled_rows = [valid_rows[index] for index in indices]
        x_boot, y_boot, labels_boot, _ = design_matrix(sampled_rows, target_key, re_key, category_key)
        if x_boot.shape != x_matrix.shape or labels_boot != labels:
            continue
        try:
            coefficients = huber_fit(x_boot, y_boot) if robust else ols_fit(x_boot, y_boot)
        except np.linalg.LinAlgError:
            continue
        for label, coefficient in zip(labels, coefficients):
            samples[label].append(float(coefficient))
    result: dict[str, list[float]] = {}
    for label, values in samples.items():
        if not values:
            continue
        result[label] = [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]
    return result


def choose_hydraulic_recommendation(
    constant_fit: dict[str, Any],
    power_fit: dict[str, Any],
) -> tuple[str, str]:
    if constant_fit.get("status") != "fit" and power_fit.get("status") != "fit":
        return "not_defensible_yet", "no_hydraulic_model_fit_succeeded"
    if power_fit.get("status") == "fit":
        ci = power_fit.get("bootstrap_ci95", {}).get("log_re")
        slope = power_fit["coefficients"][1]
        if ci and not (ci[0] <= 0.0 <= ci[1]):
            return "provisional_defended", "class_aware_re_power_law"
    if constant_fit.get("status") == "fit":
        return "provisional_defended", "class_aware_geometric_constant"
    return "not_defensible_yet", "insufficient_hydraulic_stability"


def choose_thermal_recommendation(defended_fit: dict[str, Any], exploratory_fit: dict[str, Any]) -> tuple[str, str]:
    if defended_fit.get("status") == "fit":
        return "provisional_defended", defended_fit["model_type"]
    if exploratory_fit.get("status") == "fit":
        return "not_defensible_yet", "exploratory_screened_only_model"
    return "not_defensible_yet", "insufficient_closure_supported_rows"


def property_temperature(context: CaseContext, branch_temp_k: float, convention: str) -> float:
    if convention == "case_probe":
        return context.probe_t_avg_k
    return branch_temp_k


def evaluate_dimensionless(
    context: CaseContext,
    bulk_temp_k: float,
    velocity_m_s: float,
    dh_m: float,
    htc_w_m2k: float,
    convention: str,
) -> dict[str, float]:
    property_temp = property_temperature(context, bulk_temp_k, convention)
    rho = evaluate_rho(context.property_model, property_temp)
    mu = evaluate_mu(context.property_model, property_temp)
    cp = evaluate_cp(context.property_model, property_temp)
    k_value = evaluate_k(context.property_model, property_temp)
    re_value = rho * velocity_m_s * dh_m / mu if all(math.isfinite(v) for v in (rho, velocity_m_s, dh_m, mu)) and mu > 0.0 else math.nan
    pr_value = cp * mu / k_value if all(math.isfinite(v) for v in (cp, mu, k_value)) and k_value > 0.0 else math.nan
    pe_value = re_value * pr_value if math.isfinite(re_value) and math.isfinite(pr_value) else math.nan
    nu_value = htc_w_m2k * dh_m / k_value if all(math.isfinite(v) for v in (htc_w_m2k, dh_m, k_value)) and k_value > 0.0 else math.nan
    return {
        "property_temperature_k": property_temp,
        "rho_effective_kg_m3": rho,
        "mu_effective_pa_s": mu,
        "cp_effective_j_kg_k": cp,
        "k_effective_w_m_k": k_value,
        "re_effective": re_value,
        "pr_effective": pr_value,
        "pe_effective": pe_value,
        "nu_effective": nu_value,
    }


def build_thermal_rows(
    contexts: dict[str, CaseContext],
    branch_rows: list[dict[str, str]],
    enthalpy_rows: list[dict[str, str]],
    grouped_heat_rows: list[dict[str, str]],
    streamwise_rows: list[dict[str, str]],
    bulk_centerline_rows: list[dict[str, str]],
    heat_case_rows: list[dict[str, str]],
    hydraulic_rows: list[dict[str, str]],
    property_convention: str = "branch_bulk",
) -> list[dict[str, Any]]:
    enthalpy_lookup = direct_span_lookup(enthalpy_rows, "span_name")
    branch_lookup = {(row["source_id"], row["branch_name"]): row for row in branch_rows}
    hydraulic_lookup = direct_span_lookup(hydraulic_rows, "span_name")
    heat_lookup = case_heat_lookup(heat_case_rows)
    component_map = branch_component_map(branch_rows)
    grouped_lookup = aggregate_grouped_heat(grouped_heat_rows, component_map)
    streamwise_lookup = aggregate_streamwise_heat(streamwise_rows, component_map)
    correction_lookup = aggregate_bulk_centerline(bulk_centerline_rows, component_map)
    rows_out: list[dict[str, Any]] = []

    for row in sorted(branch_rows, key=lambda item: (contexts[item["source_id"]].display_label, item["branch_name"])):
        context = contexts[row["source_id"]]
        branch_key = (row["source_id"], row["branch_name"])
        component_spans = component_map[branch_key]
        is_derived_branch = row["branch_name"] in THERMAL_COMPOSITE_BRANCHES or int(row["component_span_count"]) > 1

        q_enthalpy = safe_sum(
            finite_float(enthalpy_lookup.get((row["source_id"], span_name), {}).get("mean_enthalpy_change_w"))
            for span_name in component_spans
        )
        q_wall_from_enthalpy = safe_sum(
            finite_float(enthalpy_lookup.get((row["source_id"], span_name), {}).get("mean_wall_heat_total_w"))
            for span_name in component_spans
        )
        grouped_payload = grouped_lookup.get(branch_key, {})
        q_intended_transfer = finite_float(grouped_payload.get("intended_transfer"), 0.0)
        q_parasitic_loss = finite_float(grouped_payload.get("parasitic_loss"), 0.0)
        q_grouped_total = safe_sum([q_intended_transfer, q_parasitic_loss])
        q_streamwise_total = finite_float(streamwise_lookup.get(branch_key))
        q_wall_total = q_streamwise_total if math.isfinite(q_streamwise_total) else finite_float(row.get("mean_branch_total_wall_heat_w"))
        q_group_residual = q_wall_total - q_grouped_total if math.isfinite(q_wall_total) and math.isfinite(q_grouped_total) else math.nan
        q_enthalpy_minus_wall = q_enthalpy - q_wall_total if math.isfinite(q_enthalpy) and math.isfinite(q_wall_total) else math.nan
        residual_fraction = normalized_residual(q_enthalpy_minus_wall, q_wall_total)
        group_fraction = normalized_residual(q_group_residual, q_wall_total)

        direction_consistent = True
        if math.isfinite(q_enthalpy) and math.isfinite(q_wall_total):
            enthalpy_sign = sign_token(q_enthalpy, THERMAL_DIRECTION_MIN_MAGNITUDE_W)
            wall_sign = sign_token(q_wall_total, THERMAL_DIRECTION_MIN_MAGNITUDE_W)
            direction_consistent = enthalpy_sign == wall_sign or "zero" in {enthalpy_sign, wall_sign}
        else:
            enthalpy_sign = "nan"
            wall_sign = "nan"

        hydraulic_reference_rows = [hydraulic_lookup.get((row["source_id"], span_name), {}) for span_name in component_spans]
        dh_effective = safe_mean(finite_float(payload.get("hydraulic_diameter_m")) for payload in hydraulic_reference_rows)
        velocity_effective = safe_mean(finite_float(payload.get("bulk_velocity_m_s")) for payload in hydraulic_reference_rows)
        dimensionless = evaluate_dimensionless(
            context,
            finite_float(row.get("mean_bulk_temp_fluid_area_avg_k")),
            velocity_effective,
            dh_effective,
            finite_float(row.get("mean_effective_htc_w_m2_k")),
            property_convention,
        )
        role_label = classify_role_label(q_intended_transfer, q_parasitic_loss)
        fit_use_status, exclusion_reason, all_reasons, screened_candidate, closure_supported = classify_thermal_row(
            row["branch_name"],
            is_derived_branch,
            row["fit_status"],
            row["fit_reason"],
            finite_float(row.get("usable_fraction")),
            finite_float(row.get("thermal_warning_fraction")),
            finite_float(row.get("min_abs_bulk_minus_wall_temp_k")),
            residual_fraction,
            direction_consistent,
            group_fraction,
        )
        heat_case = heat_lookup[row["source_id"]]
        rows_out.append(
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "branch_name": row["branch_name"],
                "branch_type": row["branch_type"],
                "component_spans": row["component_spans"],
                "component_span_count": int(row["component_span_count"]),
                "is_derived_branch": bool_text(is_derived_branch),
                "role_label": role_label,
                "heater_power_w": context.heater_power_w,
                "cooling_power_w": context.cooling_power_w,
                "insulation_thickness_in": context.insulation_thickness_in,
                "cooler_h_w_m2k": context.cooler_h_w_m2k,
                "case_probe_t_avg_k": context.probe_t_avg_k,
                "branch_bulk_temp_k": finite_float(row.get("mean_bulk_temp_fluid_area_avg_k")),
                "branch_wall_temp_k": finite_float(row.get("mean_t_wall_area_avg_k")),
                "branch_bulk_minus_wall_temp_k": finite_float(row.get("mean_bulk_minus_wall_temp_k")),
                "branch_abs_bulk_minus_wall_temp_k": finite_float(row.get("mean_abs_bulk_minus_wall_temp_k")),
                "branch_min_abs_bulk_minus_wall_temp_k": finite_float(row.get("min_abs_bulk_minus_wall_temp_k")),
                "bulk_minus_centerline_temp_k": finite_float(correction_lookup.get(branch_key)),
                "support_fraction": finite_float(row.get("usable_fraction")),
                "thermal_warning_fraction": finite_float(row.get("thermal_warning_fraction")),
                "branch_fit_status_screened": row["fit_status"],
                "branch_fit_reason_screened": row["fit_reason"],
                "q_enthalpy_w": q_enthalpy,
                "q_wall_total_w": q_wall_total,
                "q_streamwise_total_w": q_streamwise_total,
                "q_grouped_total_w": q_grouped_total,
                "q_intended_transfer_w": q_intended_transfer,
                "q_parasitic_loss_w": q_parasitic_loss,
                "q_intended_heating_w": finite_float(grouped_payload.get("intended_heating"), 0.0),
                "q_intended_cooling_w": finite_float(grouped_payload.get("intended_cooling"), 0.0),
                "q_parasitic_gain_w": finite_float(grouped_payload.get("parasitic_gain"), 0.0),
                "q_parasitic_cooling_w": finite_float(grouped_payload.get("parasitic_cooling"), 0.0),
                "q_external_or_loss_w": q_parasitic_loss,
                "q_sink_or_cooling_w": finite_float(grouped_payload.get("intended_cooling"), 0.0),
                "q_group_reconstruction_residual_w": q_group_residual,
                "q_enthalpy_minus_wall_w": q_enthalpy_minus_wall,
                "residual_fraction_of_wall_heat": residual_fraction,
                "group_reconstruction_fraction": group_fraction,
                "thermal_direction_consistent": bool_text(direction_consistent),
                "q_wall_sign": wall_sign,
                "q_enthalpy_sign": enthalpy_sign,
                "dh_effective_m": dh_effective,
                "bulk_velocity_effective_m_s": velocity_effective,
                **dimensionless,
                "htc_effective_w_m2_k": finite_float(row.get("mean_effective_htc_w_m2_k")),
                "ambient_proxy_fraction_of_heater": finite_float(heat_case.get("ambient_proxy_fraction_of_heater")),
                "cooling_removal_fraction_of_heater": finite_float(heat_case.get("cooling_removal_fraction_of_heater")),
                "junction_loss_fraction_of_heater": finite_float(heat_case.get("junction_loss_fraction_of_heater")),
                "net_heat_imbalance_fraction_of_heater": finite_float(heat_case.get("net_heat_imbalance_fraction_of_heater")),
                "screened_candidate_flag": bool_text(screened_candidate),
                "closure_supported_candidate_flag": bool_text(closure_supported),
                "fit_use_status": fit_use_status,
                "exclusion_reason_primary": exclusion_reason,
                "exclusion_reasons_json": json.dumps(all_reasons),
            }
        )
    return rows_out


def build_hydraulic_rows(
    contexts: dict[str, CaseContext],
    straight_rows: list[dict[str, str]],
    feature_rows: list[dict[str, str]],
    branch_rows: list[dict[str, str]],
    property_convention: str = "branch_bulk",
) -> list[dict[str, Any]]:
    branch_lookup = {(row["source_id"], row["branch_name"]): row for row in branch_rows}
    rows_out: list[dict[str, Any]] = []

    for row in sorted(straight_rows, key=lambda item: (contexts[item["source_id"]].display_label, item["span_name"])):
        context = contexts[row["source_id"]]
        branch = branch_lookup.get((row["source_id"], row["span_name"]), {})
        branch_temp = finite_float(branch.get("mean_bulk_temp_fluid_area_avg_k"), context.probe_t_avg_k)
        dimensionless = evaluate_dimensionless(
            context,
            branch_temp,
            finite_float(row.get("bulk_velocity_m_s")),
            finite_float(row.get("hydraulic_diameter_m")),
            math.nan,
            property_convention,
        )
        fit_use_status, primary_reason, all_reasons, screened_candidate, closure_supported = classify_hydraulic_row(
            "straight_section_friction",
            row["fit_status"],
            row["fit_reason"],
            "defended_direct_hydro",
        )
        rows_out.append(
            {
                "asset_family": "straight_section_friction",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "scope_name": row["span_name"],
                "scope_kind": row["span_kind"],
                "pressure_method_label": "hydro_corrected_section_from_additive_june17_package",
                "pressure_method_status": "defended_direct_hydro",
                "screened_candidate_flag": bool_text(screened_candidate),
                "closure_supported_candidate_flag": bool_text(closure_supported),
                "fit_use_status": fit_use_status,
                "fit_status_screened": row["fit_status"],
                "fit_reason_screened": row["fit_reason"],
                "net_section_role": row["net_section_role"],
                "support_fraction": finite_float(row.get("branch_fit_status") and branch.get("usable_fraction")),
                "pressure_loss_hydro_pa": finite_float(row.get("pressure_loss_hydro_pa")),
                "apparent_darcy_f_local": finite_float(row.get("apparent_darcy_f_local")),
                "direct_prgh_darcy": finite_float(row.get("direct_prgh_darcy")),
                "shear_darcy_core": finite_float(row.get("shear_darcy_core")),
                "direct_to_shear_darcy_ratio": finite_float(row.get("direct_to_shear_darcy_ratio")),
                "pressure_loss_to_driving_head_ratio": finite_float(row.get("pressure_loss_to_driving_head_ratio")),
                "dh_effective_m": finite_float(row.get("hydraulic_diameter_m")),
                "bulk_velocity_effective_m_s": finite_float(row.get("bulk_velocity_m_s")),
                "rho_effective_kg_m3": dimensionless["rho_effective_kg_m3"],
                "mu_effective_pa_s": dimensionless["mu_effective_pa_s"],
                "re_effective": dimensionless["re_effective"],
                "property_temperature_k": dimensionless["property_temperature_k"],
                "residual_risk_label": "none_additional_beyond_screened_direct_vs_shear_gate",
                "todo_required": "no",
                "missing_requirement": "",
                "exclusion_reason_primary": primary_reason,
                "exclusion_reasons_json": json.dumps(all_reasons),
            }
        )

    for row in sorted(feature_rows, key=lambda item: (contexts[item["source_id"]].display_label, item["feature_name"])):
        fit_use_status, primary_reason, all_reasons, screened_candidate, closure_supported = classify_hydraulic_row(
            "feature_keff",
            row["fit_status"],
            row["fit_reason"],
            "residual_prgh_only",
        )
        rows_out.append(
            {
                "asset_family": "feature_keff",
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "scope_name": row["feature_name"],
                "scope_kind": row["feature_kind"],
                "pressure_method_label": "residual_prgh_feature_budget_from_additive_june17_package",
                "pressure_method_status": "residual_prgh_only",
                "screened_candidate_flag": bool_text(screened_candidate),
                "closure_supported_candidate_flag": bool_text(closure_supported),
                "fit_use_status": fit_use_status,
                "fit_status_screened": row["fit_status"],
                "fit_reason_screened": row["fit_reason"],
                "net_section_role": "feature_minor_loss",
                "support_fraction": math.nan,
                "pressure_loss_hydro_pa": finite_float(row.get("mean_feature_residual_dp_pa")),
                "apparent_darcy_f_local": math.nan,
                "direct_prgh_darcy": math.nan,
                "shear_darcy_core": math.nan,
                "direct_to_shear_darcy_ratio": math.nan,
                "pressure_loss_to_driving_head_ratio": math.nan,
                "dh_effective_m": math.nan,
                "bulk_velocity_effective_m_s": math.nan,
                "rho_effective_kg_m3": math.nan,
                "mu_effective_pa_s": math.nan,
                "re_effective": math.nan,
                "property_temperature_k": math.nan,
                "residual_risk_label": "feature_loss_not_defensible_without_feature_hydro_integral",
                "todo_required": "yes",
                "missing_requirement": (
                    "Need feature-path density-integral or equivalent hydro-corrected feature pressure-loss closure; "
                    "current preserved artifacts only store residual p_rgh subtraction."
                ),
                "exclusion_reason_primary": primary_reason,
                "exclusion_reasons_json": json.dumps(all_reasons),
            }
        )
    return rows_out


def summarize_exclusions(rows: list[dict[str, Any]], asset_column: str = "asset_family") -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str]] = Counter()
    for row in rows:
        if row["fit_use_status"] == "fit_used":
            continue
        counter[(str(row[asset_column]), str(row["exclusion_reason_primary"]))] += 1
    payloads = [
        {"asset_family": asset_family, "exclusion_reason_primary": reason, "row_count": count}
        for (asset_family, reason), count in sorted(counter.items())
    ]
    return payloads


def summarize_branch_trust(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["branch_name"]].append(row)
    payloads: list[dict[str, Any]] = []
    for branch_name, payload in sorted(grouped.items()):
        statuses = Counter(str(row["fit_use_status"]) for row in payload)
        payloads.append(
            {
                "branch_name": branch_name,
                "row_count": len(payload),
                "screened_candidate_count": sum(1 for row in payload if row["screened_candidate_flag"] == "yes"),
                "closure_supported_count": sum(1 for row in payload if row["closure_supported_candidate_flag"] == "yes"),
                "fit_used_count": statuses.get("fit_used", 0),
                "sensitivity_only_count": statuses.get("sensitivity_only", 0),
                "excluded_count": statuses.get("excluded", 0),
                "dominant_exclusion_reason": Counter(
                    row["exclusion_reason_primary"] for row in payload if row["fit_use_status"] != "fit_used"
                ).most_common(1)[0][0]
                if any(row["fit_use_status"] != "fit_used" for row in payload)
                else "",
            }
        )
    return payloads


def filter_rows(rows: list[dict[str, Any]], status: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["fit_use_status"] == status]


def build_latest_target_thermal_rows(
    base_rows: list[dict[str, Any]],
    section_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    section_lookup = direct_span_lookup(filter_salt_rows(section_rows), "span_name")
    payloads: list[dict[str, Any]] = []
    for row in base_rows:
        if row["is_derived_branch"] == "yes":
            continue
        section = section_lookup.get((row["source_id"], row["branch_name"]))
        if section is None:
            continue
        payload = dict(row)
        payload["htc_effective_w_m2_k"] = finite_float(section.get("h_area_ratio_signed_w_m2_k"))
        payload["nu_effective"] = finite_float(section.get("nu_area_ratio_signed"))
        payload["q_wall_total_w"] = finite_float(section.get("wall_heat_integral_w"))
        payloads.append(payload)
    return payloads


def build_sensitivity_rows(
    thermal_rows: list[dict[str, Any]],
    thermal_rows_case_probe: list[dict[str, Any]],
    thermal_rows_latest_target: list[dict[str, Any]],
    hydraulic_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    thermal_direct_rows = [row for row in thermal_rows if row["branch_name"] not in THERMAL_BLOCKED_BRANCHES]
    thermal_screened_direct = [row for row in thermal_direct_rows if row["screened_candidate_flag"] == "yes" and row["is_derived_branch"] == "no"]
    thermal_fit_used = filter_rows(thermal_direct_rows, "fit_used")
    hydraulic_fit_used = [row for row in hydraulic_rows if row["asset_family"] == "straight_section_friction" and row["fit_use_status"] == "fit_used"]

    hydraulic_constant = fit_geometric_constant(hydraulic_fit_used, "apparent_darcy_f_local", "scope_name")
    hydraulic_power = fit_power_law(
        hydraulic_fit_used,
        "apparent_darcy_f_local",
        "re_effective",
        "scope_name",
        "class_aware_re_power_law",
        robust=False,
    )
    hydraulic_robust = fit_power_law(
        hydraulic_fit_used,
        "apparent_darcy_f_local",
        "re_effective",
        "scope_name",
        "class_aware_re_power_law_huber",
        robust=True,
    )
    hydraulic_status, hydraulic_recommendation = choose_hydraulic_recommendation(hydraulic_constant, hydraulic_power)

    thermal_defended = fit_power_law(
        thermal_fit_used,
        "nu_effective",
        "re_effective",
        "branch_name",
        "branch_aware_re_power_law",
        robust=False,
    )
    thermal_exploratory = fit_power_law(
        thermal_screened_direct,
        "nu_effective",
        "re_effective",
        "branch_name",
        "branch_aware_re_power_law_screened_only",
        robust=True,
    )
    thermal_status, thermal_recommendation = choose_thermal_recommendation(thermal_defended, thermal_exploratory)

    sensitivity_rows: list[dict[str, Any]] = []

    def add_sensitivity(
        asset_family: str,
        sensitivity_name: str,
        base_model: dict[str, Any],
        sensitivity_model: dict[str, Any],
        base_row_count: int,
        sensitivity_row_count: int,
        note: str,
    ) -> None:
        base_slope = float(base_model["coefficients"][1]) if base_model.get("status") == "fit" and len(base_model.get("coefficients", [])) > 1 else math.nan
        sens_slope = float(sensitivity_model["coefficients"][1]) if sensitivity_model.get("status") == "fit" and len(sensitivity_model.get("coefficients", [])) > 1 else math.nan
        changed = (
            (base_model.get("status") != sensitivity_model.get("status"))
            or (math.isfinite(base_slope) and math.isfinite(sens_slope) and abs(sens_slope - base_slope) > 0.15)
            or (base_row_count != sensitivity_row_count)
        )
        sensitivity_rows.append(
            {
                "asset_family": asset_family,
                "sensitivity_name": sensitivity_name,
                "status": "run" if sensitivity_model.get("status") != "not_run" else "not_run",
                "base_row_count": base_row_count,
                "sensitivity_row_count": sensitivity_row_count,
                "row_count_delta": sensitivity_row_count - base_row_count,
                "base_model_status": base_model.get("status", "not_fit"),
                "sensitivity_model_status": sensitivity_model.get("status", "not_fit"),
                "base_log_re_slope": base_slope,
                "sensitivity_log_re_slope": sens_slope,
                "log_re_slope_delta": sens_slope - base_slope if math.isfinite(base_slope) and math.isfinite(sens_slope) else math.nan,
                "base_rmse_log": finite_float(base_model.get("rmse_log")),
                "sensitivity_rmse_log": finite_float(sensitivity_model.get("rmse_log")),
                "qualitative_conclusion_changed": bool_text(changed),
                "note": note,
            }
        )

    hydraulic_loose_rows = [
        row for row in hydraulic_rows
        if row["asset_family"] == "straight_section_friction"
        and row["screened_candidate_flag"] == "yes"
        and 0.40 <= finite_float(row.get("direct_to_shear_darcy_ratio")) <= 2.50
    ]
    hydraulic_strict_rows = [
        row for row in hydraulic_rows
        if row["asset_family"] == "straight_section_friction"
        and row["screened_candidate_flag"] == "yes"
        and 0.67 <= finite_float(row.get("direct_to_shear_darcy_ratio")) <= 1.50
    ]
    add_sensitivity(
        "hydraulic",
        "direct_to_shear_gate_loose",
        hydraulic_power,
        fit_power_law(hydraulic_loose_rows, "apparent_darcy_f_local", "re_effective", "scope_name", "class_aware_re_power_law", robust=False),
        len(hydraulic_fit_used),
        len(hydraulic_loose_rows),
        "Loose direct/shear ratio gate 0.40-2.50.",
    )
    add_sensitivity(
        "hydraulic",
        "direct_to_shear_gate_strict",
        hydraulic_power,
        fit_power_law(hydraulic_strict_rows, "apparent_darcy_f_local", "re_effective", "scope_name", "class_aware_re_power_law", robust=False),
        len(hydraulic_fit_used),
        len(hydraulic_strict_rows),
        "Strict direct/shear ratio gate 0.67-1.50.",
    )

    thermal_loose_rows = [
        row for row in thermal_direct_rows
        if row["branch_name"] not in THERMAL_BLOCKED_BRANCHES
        and row["is_derived_branch"] == "no"
        and finite_float(row.get("support_fraction")) >= 0.85
        and finite_float(row.get("branch_min_abs_bulk_minus_wall_temp_k")) >= 0.25
        and finite_float(row.get("residual_fraction_of_wall_heat")) <= 0.30
    ]
    thermal_strict_rows = [
        row for row in thermal_direct_rows
        if row["branch_name"] not in THERMAL_BLOCKED_BRANCHES
        and row["is_derived_branch"] == "no"
        and finite_float(row.get("support_fraction")) >= 0.95
        and finite_float(row.get("branch_min_abs_bulk_minus_wall_temp_k")) >= 0.75
        and finite_float(row.get("residual_fraction_of_wall_heat")) <= 0.10
    ]
    add_sensitivity(
        "thermal",
        "closure_gate_loose",
        thermal_defended,
        fit_power_law(thermal_loose_rows, "nu_effective", "re_effective", "branch_name", "branch_aware_re_power_law", robust=False),
        len(thermal_fit_used),
        len(thermal_loose_rows),
        "Loose thermal closure gate: support>=0.85, |Twall-Tbulk|min>=0.25 K, residual<=0.30.",
    )
    add_sensitivity(
        "thermal",
        "closure_gate_strict",
        thermal_defended,
        fit_power_law(thermal_strict_rows, "nu_effective", "re_effective", "branch_name", "branch_aware_re_power_law", robust=False),
        len(thermal_fit_used),
        len(thermal_strict_rows),
        "Strict thermal closure gate: support>=0.95, |Twall-Tbulk|min>=0.75 K, residual<=0.10.",
    )

    thermal_case_probe_rows = [
        row
        for row in thermal_rows_case_probe
        if row["branch_name"] not in THERMAL_BLOCKED_BRANCHES and row["is_derived_branch"] == "no" and row["screened_candidate_flag"] == "yes"
    ]
    add_sensitivity(
        "thermal",
        "property_convention_case_probe",
        thermal_exploratory,
        fit_power_law(thermal_case_probe_rows, "nu_effective", "re_effective", "branch_name", "branch_aware_re_power_law_screened_only", robust=True),
        len(thermal_screened_direct),
        len(thermal_case_probe_rows),
        "Case-probe property convention uses probe_T_avg_K rather than branch bulk temperature when deriving Re and Nu.",
    )
    thermal_latest_rows = [
        row
        for row in thermal_rows_latest_target
        if row["branch_name"] not in THERMAL_BLOCKED_BRANCHES and row["is_derived_branch"] == "no" and row["screened_candidate_flag"] == "yes"
    ]
    add_sensitivity(
        "thermal",
        "late_window_latest_section_target",
        thermal_exploratory,
        fit_power_law(thermal_latest_rows, "nu_effective", "re_effective", "branch_name", "branch_aware_re_power_law_screened_only", robust=True),
        len(thermal_screened_direct),
        len(thermal_latest_rows),
        "Latest-section target sensitivity swaps the late-window branch HTC/Nu target for the preserved latest section-summary target while keeping the same screened direct-branch support gate.",
    )

    sensitivity_rows.append(
        {
            "asset_family": "hydraulic",
            "sensitivity_name": "late_window_choice",
            "status": "not_run",
            "base_row_count": len(hydraulic_fit_used),
            "sensitivity_row_count": len(hydraulic_fit_used),
            "row_count_delta": 0,
            "base_model_status": hydraulic_power.get("status", "not_fit"),
            "sensitivity_model_status": "not_run",
            "base_log_re_slope": finite_float(hydraulic_power.get("coefficients", [math.nan, math.nan])[1] if hydraulic_power.get("status") == "fit" else math.nan),
            "sensitivity_log_re_slope": math.nan,
            "log_re_slope_delta": math.nan,
            "base_rmse_log": finite_float(hydraulic_power.get("rmse_log")),
            "sensitivity_rmse_log": math.nan,
            "qualitative_conclusion_changed": "unknown",
            "note": "Hydro-corrected section closures are only preserved as time-mean rows in the additive package; no raw feature/path hydro timeseries survived for a true hydraulic late-window rerun.",
        }
    )

    return sensitivity_rows, {
        "recommended_status": hydraulic_status,
        "recommended_model": hydraulic_recommendation,
        "constant_model": hydraulic_constant,
        "power_model": hydraulic_power,
        "robust_model": hydraulic_robust,
        "fit_used_row_count": len(hydraulic_fit_used),
    }, {
        "recommended_status": thermal_status,
        "recommended_model": thermal_recommendation,
        "defended_model": thermal_defended,
        "exploratory_model": thermal_exploratory,
        "fit_used_row_count": len(thermal_fit_used),
        "screened_row_count": len(thermal_screened_direct),
    }


def build_provenance_rows() -> list[dict[str, str]]:
    return [
        {
            "output_table": "thermal_decomposition_rows.csv",
            "column_name": "q_enthalpy_w",
            "purpose": "Branch/leg fluid enthalpy change used for closure gating.",
            "source_files": "reports/2026-06-18_ethan_salt_closure_correlation_package/salt_leg_enthalpy_summary.csv",
            "source_columns": "mean_enthalpy_change_w",
            "transformation_formula": "Direct late-window mean carried forward; derived branches sum component spans.",
            "units": "W",
            "sign_convention": "Positive means net energy gain by the fluid along the branch direction.",
            "validity_gates": "Requires finite enthalpy row and documented bulk-temperature method.",
            "known_failure_modes": "Weak branch closure where span enthalpy is contaminated by unresolved junction exchange.",
        },
        {
            "output_table": "thermal_decomposition_rows.csv",
            "column_name": "q_wall_total_w",
            "purpose": "Net wall-to-fluid heat for the branch used as the main closure reference.",
            "source_files": "reports/2026-06-15_ethan_all_runs_field_transport_campaign/field_transport_streamwise_heat_comparison.csv",
            "source_columns": "mean_wall_heat_w",
            "transformation_formula": "Sum streamwise-bin mean_wall_heat_w across component spans.",
            "units": "W",
            "sign_convention": "Positive means wall heat enters the fluid; negative means wall heat removes energy from the fluid.",
            "validity_gates": "Requires preserved streamwise heat bins for every component span.",
            "known_failure_modes": "Missing streamwise bins or mixed sign contributions near branch boundaries.",
        },
        {
            "output_table": "thermal_decomposition_rows.csv",
            "column_name": "q_intended_transfer_w",
            "purpose": "Intended-transfer contribution separated from parasitic loss.",
            "source_files": "reports/2026-06-15_ethan_all_runs_field_transport_campaign/field_transport_grouped_heat_comparison.csv",
            "source_columns": "mean_wall_heat_w, thermal_role_group",
            "transformation_formula": "Sum mean_wall_heat_w where thermal_role_group == intended_transfer across component spans.",
            "units": "W",
            "sign_convention": "Positive means intended heating, negative means intended cooling.",
            "validity_gates": "Depends on current thermal_role_group metadata in tools/case_analysis_profiles.py.",
            "known_failure_modes": "Thermal-role reclassification changes this decomposition without changing the CFD fields.",
        },
        {
            "output_table": "thermal_decomposition_rows.csv",
            "column_name": "q_external_or_loss_w",
            "purpose": "Bounded proxy for external/parasitic wall-loss contribution.",
            "source_files": "reports/2026-06-15_ethan_all_runs_field_transport_campaign/field_transport_grouped_heat_comparison.csv",
            "source_columns": "mean_wall_heat_w, thermal_role_group",
            "transformation_formula": "Set equal to grouped parasitic-loss sum; no hidden reassignment into HTC.",
            "units": "W",
            "sign_convention": "Negative means parasitic cooling or wall loss from the fluid.",
            "validity_gates": "Only a proxy for external-like loss, not a resolved conduction/radiation resistance split.",
            "known_failure_modes": "Cannot distinguish internal wall conduction from external convection/radiation with preserved artifacts alone.",
        },
        {
            "output_table": "thermal_decomposition_rows.csv",
            "column_name": "residual_fraction_of_wall_heat",
            "purpose": "Main thermal closure gate used before any defended Nu fit.",
            "source_files": "thermal_decomposition_rows.csv (derived within builder)",
            "source_columns": "q_enthalpy_w, q_wall_total_w",
            "transformation_formula": "|q_enthalpy_w - q_wall_total_w| / |q_wall_total_w|",
            "units": "1",
            "sign_convention": "Magnitude only.",
            "validity_gates": "Requires finite wall-heat reference with nonzero magnitude.",
            "known_failure_modes": "Large values often indicate unresolved junction exchange or branch-definition mismatch rather than impossible CFD physics.",
        },
        {
            "output_table": "thermal_decomposition_rows.csv",
            "column_name": "nu_effective",
            "purpose": "Effective branch Nusselt number used for Salt thermal dependency screening.",
            "source_files": "reports/2026-06-18_ethan_salt_analysis_checkpoint_suite/phase3_branch_trust_gate/branch_promotion_gate.csv; case_config.yaml",
            "source_columns": "mean_effective_htc_w_m2_k, mean_bulk_temp_fluid_area_avg_k, hydraulic_diameter_geom_m, fluid property coefficients",
            "transformation_formula": "nu_effective = h_effective * D_h / k(T_eval)",
            "units": "1",
            "sign_convention": "Signed through h_effective; only positive rows are fit-eligible.",
            "validity_gates": "Requires positive support-gated h_effective, finite D_h, and finite k(T_eval).",
            "known_failure_modes": "Composite derived branches require weighted D_h assumptions and are therefore sensitivity-only.",
        },
        {
            "output_table": "thermal_decomposition_rows.csv",
            "column_name": "re_effective",
            "purpose": "Branch Reynolds number for Salt thermal dependency fits.",
            "source_files": "reports/2026-06-18_ethan_salt_closure_correlation_package/salt_straight_section_correlation_inputs.csv; case_config.yaml",
            "source_columns": "bulk_velocity_m_s, hydraulic_diameter_m, rho(T), mu(T)",
            "transformation_formula": "Re = rho(T_eval) * U * D_h / mu(T_eval)",
            "units": "1",
            "sign_convention": "Positive magnitude only.",
            "validity_gates": "Requires positive velocity, diameter, density, and viscosity under the chosen property convention.",
            "known_failure_modes": "For derived branches, U and D_h are component-weighted surrogates, not direct reconstructed cross-section values.",
        },
        {
            "output_table": "thermal_decomposition_rows.csv",
            "column_name": "fit_use_status",
            "purpose": "Separates screened, closure-supported, fit-used, excluded, and sensitivity-only thermal rows.",
            "source_files": "thermal_decomposition_rows.csv (derived within builder)",
            "source_columns": "branch gate, residual_fraction_of_wall_heat, group_reconstruction_fraction, thermal_direction_consistent, branch identity",
            "transformation_formula": "Rule-based gate stack documented in README and model_dependency_handoff.md.",
            "units": "categorical",
            "sign_convention": "n/a",
            "validity_gates": "Right leg is hard-blocked; derived upcomer is sensitivity-only; weak support or weak enthalpy closure blocks defended fits.",
            "known_failure_modes": "Policy changes intentionally alter fit-used row counts and must be recorded in sensitivity_summary.csv.",
        },
        {
            "output_table": "hydraulic_hardening_audit.csv",
            "column_name": "pressure_method_status",
            "purpose": "Documents whether the row uses a defended hydro-corrected straight-section method or a residual-only feature method.",
            "source_files": "reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/README.md; reports/2026-06-18_ethan_salt_analysis_checkpoint_suite/phase1_hydraulic_hardening/README.md",
            "source_columns": "method interpretation only",
            "transformation_formula": "Assigned by asset family: straight sections -> defended_direct_hydro, features -> residual_prgh_only.",
            "units": "categorical",
            "sign_convention": "n/a",
            "validity_gates": "Feature rows are never promoted to fit-used without a new feature hydro-integral method.",
            "known_failure_modes": "Residual-only feature K_eff can change sign under subtraction noise or buoyancy contamination.",
        },
        {
            "output_table": "hydraulic_hardening_audit.csv",
            "column_name": "apparent_darcy_f_local",
            "purpose": "Primary straight-section friction target audited for Salt dependency fitting.",
            "source_files": "reports/2026-06-18_ethan_salt_closure_correlation_package/salt_straight_section_correlation_inputs.csv",
            "source_columns": "apparent_darcy_f_local",
            "transformation_formula": "Direct carry-through from additive June 18 Salt closure package.",
            "units": "1",
            "sign_convention": "Positive indicates dissipative net loss; negative sections remain excluded as buoyancy-aided or net-gain.",
            "validity_gates": "Requires straight-section candidate gate and defended hydro-corrected pressure method.",
            "known_failure_modes": "Can be unstable where direct-pressure and wall-shear proxies disagree strongly.",
        },
        {
            "output_table": "hydraulic_hardening_audit.csv",
            "column_name": "fit_use_status",
            "purpose": "Separates defended straight-section friction rows from residual-only feature rows and screened exclusions.",
            "source_files": "hydraulic_hardening_audit.csv (derived within builder)",
            "source_columns": "fit_status_screened, pressure_method_status",
            "transformation_formula": "Straight-section candidate + defended method -> fit_used; residual-only feature method -> excluded.",
            "units": "categorical",
            "sign_convention": "n/a",
            "validity_gates": "Nonpositive residual feature loss is never enough to justify K_eff fitting.",
            "known_failure_modes": "A future upstream feature hydro-integral extractor would change these labels by design.",
        },
        {
            "output_table": "salt_friction_fit_results.json",
            "column_name": "recommended_model",
            "purpose": "Current defended recommendation for Salt straight-section friction dependency.",
            "source_files": "hydraulic_fit_ready_rows.csv",
            "source_columns": "re_effective, apparent_darcy_f_local, scope_name",
            "transformation_formula": "Selected between class-aware constant and class-aware Re power law using bootstrap support and sample sufficiency.",
            "units": "categorical/model",
            "sign_convention": "n/a",
            "validity_gates": "Only fit-used straight sections contribute.",
            "known_failure_modes": "Small row count and unfinished feature closure mean the recommendation may stay provisional or be set to none.",
        },
        {
            "output_table": "salt_nu_fit_results.json",
            "column_name": "recommended_model",
            "purpose": "Current defended recommendation for Salt HTC/Nu dependency, if any.",
            "source_files": "thermal_fit_ready_rows.csv; thermal_decomposition_rows.csv",
            "source_columns": "nu_effective, re_effective, branch_name, fit_use_status",
            "transformation_formula": "Uses closure-supported direct-branch rows only; if too few rows survive, the recommendation is explicitly none.",
            "units": "categorical/model",
            "sign_convention": "n/a",
            "validity_gates": "Right leg blocked; upcomer overlap rows sensitivity-only; weak enthalpy closure blocks defended Nu fits.",
            "known_failure_modes": "Branch support can look strong while enthalpy closure remains too weak for a defended Nu dependency.",
        },
        {
            "output_table": "sensitivity_summary.csv",
            "column_name": "qualitative_conclusion_changed",
            "purpose": "Records whether the fitted dependency story changes under alternate gates or property conventions.",
            "source_files": "fit result JSON derived in builder",
            "source_columns": "row counts, fit status, log_re slope, rmse",
            "transformation_formula": "Set to yes when model status changes, slope changes materially, or retained row counts change.",
            "units": "categorical yes/no/unknown",
            "sign_convention": "n/a",
            "validity_gates": "Only reports sensitivities that were actually runnable from preserved artifacts.",
            "known_failure_modes": "Hydraulic late-window sensitivity is not runnable because time-resolved hydro-corrected closures were not preserved.",
        },
    ]


def write_readme(
    output_dir: Path,
    summary: dict[str, Any],
    thermal_rows: list[dict[str, Any]],
    hydraulic_rows: list[dict[str, Any]],
    thermal_fit_rows: list[dict[str, Any]],
    hydraulic_fit_rows: list[dict[str, Any]],
    thermal_exclusion_summary: list[dict[str, Any]],
    hydraulic_exclusion_summary: list[dict[str, Any]],
    friction_results: dict[str, Any],
    nu_results: dict[str, Any],
) -> None:
    thermal_fit_after = len(thermal_fit_rows)
    hydraulic_fit_after = len(hydraulic_fit_rows)
    thermal_screened_before = sum(1 for row in thermal_rows if row["screened_candidate_flag"] == "yes")
    hydraulic_screened_before = sum(
        1 for row in hydraulic_rows if row["asset_family"] == "straight_section_friction" and row["screened_candidate_flag"] == "yes"
    )
    text = f"""# Ethan Salt Model Dependency Package

Generated: `2026-06-18`

## What was run

This package builds the next additive Salt-only analysis layer after the June 18
checkpoint suite. It does **not** reopen the shared June 15/17 extractors.
Instead it audits the preserved Salt closure artifacts and promotes only those
rows that survive explicit closure, support, overlap, and provenance gates.

Primary implementation script:

- `tools/analyze/build_ethan_salt_model_dependency_package.py`

## Inputs used

- `reports/2026-06-18_ethan_salt_analysis_checkpoint_suite/`
- `reports/2026-06-18_ethan_salt_closure_correlation_package/`
- `reports/2026-06-17_ethan_pressure_htc_boundarylayer_package/`
- `reports/2026-06-17_ethan_nondimensional_dashboard_package/`
- `reports/2026-06-15_ethan_all_runs_field_transport_campaign/`
- `reports/2026-06-09_ethan_steady_state_heat_flow_audit/`
- `reports/2026-06-04_ethan_case_metadata_index/ethan_case_metadata_index.csv`
- source `case_config.yaml` property models at each case source root

## Scientific decision first

The thermal-decomposition pass was implementable from preserved artifacts.
Hydraulic hardening for feature `K_eff` was **not** a prerequisite for that
thermal pass, but the package still writes a hydraulic hardening audit because
feature pressure loss remains residual-only and therefore not fit-defensible.

## Output tables

- `provenance_map.csv`
  Machine-readable lineage map with source files, source columns, formulas,
  units, sign conventions, gates, and known failure modes.
- `thermal_decomposition_rows.csv`
  One late-window branch row per Salt case with bounded decomposition terms,
  closure gates, dimensionless groups, and final fit-use status.
- `thermal_fit_ready_rows.csv`
  Only defended thermal rows promoted into downstream fitting.
- `thermal_exclusion_summary.csv`
  Counted thermal exclusions by primary reason.
- `branch_trust_summary.csv`
  Branch-level counts of screened, closure-supported, fit-used, sensitivity-only,
  and excluded rows.
- `hydraulic_hardening_audit.csv`
  Straight-section and feature hydraulic audit rows with method labels,
  residual-risk flags, and TODO requirements for unfinished feature closure.
- `hydraulic_fit_ready_rows.csv`
  Only defended straight-section hydraulic rows promoted into downstream fitting.
- `hydraulic_exclusion_summary.csv`
  Counted hydraulic exclusions by primary reason.
- `salt_friction_fit_results.json`
  Straight-section friction model results plus the final recommendation status.
- `salt_nu_fit_results.json`
  Thermal HTC/Nu model results plus the final recommendation status.
- `sensitivity_summary.csv`
  Compact sensitivity record showing retained rows, coefficient changes, and
  whether the qualitative conclusion changes.
- `model_dependency_handoff.md`
  Future-model-builder handoff with exact row subsets, assumptions, uncertainty,
  and extension plan.

## Fit-ready row counts before and after

- Thermal screened candidates before closure hardening: `{thermal_screened_before}`
- Thermal defended fit-used rows after closure hardening: `{thermal_fit_after}`
- Hydraulic screened straight-section candidates before hydraulic hardening audit: `{hydraulic_screened_before}`
- Hydraulic defended fit-used rows after hydraulic hardening audit: `{hydraulic_fit_after}`

## What was excluded and why

### Thermal

{chr(10).join(f"- `{row['asset_family']}` / `{row['exclusion_reason_primary']}`: `{row['row_count']}` rows" for row in thermal_exclusion_summary) or '- No thermal exclusions were counted.'}

### Hydraulic

{chr(10).join(f"- `{row['asset_family']}` / `{row['exclusion_reason_primary']}`: `{row['row_count']}` rows" for row in hydraulic_exclusion_summary) or '- No hydraulic exclusions were counted.'}

## Dependency status

### Salt friction dependency

- Recommendation status: `{friction_results['recommended_status']}`
- Recommended model: `{friction_results['recommended_model']}`
- Feature `K_eff` status: `not defensible yet` until a feature-path hydro
  integral or equivalent direct feature closure is preserved upstream.

### Salt HTC/Nu dependency

- Recommendation status: `{nu_results['recommended_status']}`
- Recommended model: `{nu_results['recommended_model']}`
- Important boundary: right-leg rows stay excluded and derived `upcomer` rows
  remain sensitivity-only because they overlap the direct component spans.

## Reproduction

Run:

```bash
python tools/analyze/build_ethan_salt_model_dependency_package.py --output-dir {output_dir}
```

For a bounded smoke rebuild:

```bash
python tools/analyze/build_ethan_salt_model_dependency_package.py \\
  --output-dir {DEFAULT_SMOKE_OUTPUT_DIR} \\
  --source-id val_salt_test_2_coarse_mesh_laminar \\
  --source-id viscosity_screening_salt_test_4_jin_coarse_mesh
```

## Known limitations

- The package separates intended-transfer versus parasitic-loss wall exchange
  only to the extent the preserved thermal-role metadata supports it. It does
  **not** claim a resolved wall-conduction / external-convection / radiation
  resistance split.
- Feature `K_eff` still inherits a residual-only `p_rgh` method and therefore
  stays out of defended fitting.
- Hydraulic late-window sensitivity could not be rerun from preserved artifacts
  because only time-mean hydro-corrected section closures survived in the
  additive package.
- If thermal defended rows remain sparse, the package will report that no
  defended Salt Nu dependency is available rather than silently fitting the
  screened-only subset.

## Next recommended work

1. Add an upstream feature-path hydro-integral extractor so feature `K_eff`
   can be promoted out of the residual-only bucket.
2. Preserve a resolved wall-resistance split if future CFD postprocessing needs
   true internal-HTC closure rather than bounded effective Nu.
3. Only after the same closure gates exist for water should the same dependency
   package be extended to water-family rows.
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


def write_model_handoff(
    output_dir: Path,
    thermal_rows: list[dict[str, Any]],
    hydraulic_rows: list[dict[str, Any]],
    friction_results: dict[str, Any],
    nu_results: dict[str, Any],
    sensitivity_rows: list[dict[str, Any]],
) -> None:
    thermal_fit = filter_rows(thermal_rows, "fit_used")
    thermal_screened = [row for row in thermal_rows if row["fit_use_status"] == "sensitivity_only"]
    hydraulic_fit = [row for row in hydraulic_rows if row["fit_use_status"] == "fit_used" and row["asset_family"] == "straight_section_friction"]
    hydraulic_feature_excluded = [row for row in hydraulic_rows if row["asset_family"] == "feature_keff"]
    text = f"""# Salt Model Dependency Handoff

## Purpose

This note is written for a future model builder. It states exactly which Salt
rows are defensible for downstream dependency use today, which rows are still
screening-only, and why.

## Final recommended Salt friction dependency

- Status: `{friction_results['recommended_status']}`
- Recommended model label: `{friction_results['recommended_model']}`
- Fit-used straight-section row count: `{len(hydraulic_fit)}`
- Feature `K_eff`: `not defensible yet`

Why the feature model is blocked:

- The preserved feature path only carries residual `p_rgh` subtraction.
- No dedicated feature-path hydro integral survived in the additive artifacts.
- Positive residual feature loss is therefore not enough to justify a minor-loss
  coefficient fit.

## Final recommended Salt HTC/Nu dependency

- Status: `{nu_results['recommended_status']}`
- Recommended model label: `{nu_results['recommended_model']}`
- Defended thermal fit-used row count: `{len(thermal_fit)}`
- Screened-only sensitivity rows: `{len(thermal_screened)}`

Important interpretation boundary:

- `right_leg` remains excluded by the branch trust gate.
- `upcomer` remains sensitivity-only because it overlaps the direct component
  spans and would double-count geometry in any defended fit.

## Exact rows used

### Hydraulic fit-used rows

{chr(10).join(f"- `{row['source_id']}` / `{row['scope_name']}` / `Re={row['re_effective']:.3f}` / `f={row['apparent_darcy_f_local']:.3f}`" for row in hydraulic_fit) or '- None.'}

### Thermal fit-used rows

{chr(10).join(f"- `{row['source_id']}` / `{row['branch_name']}` / `Re={row['re_effective']:.3f}` / `Nu={row['nu_effective']:.3f}`" for row in thermal_fit) or '- None; no branch rows survived the full defended thermal closure gate.'}

## Exact rows excluded

### Feature rows

{chr(10).join(f"- `{row['source_id']}` / `{row['scope_name']}` -> `{row['exclusion_reason_primary']}`" for row in hydraulic_feature_excluded[:12])}

### Thermal exclusions

{chr(10).join(f"- `{row['source_id']}` / `{row['branch_name']}` -> `{row['exclusion_reason_primary']}`" for row in thermal_rows if row['fit_use_status'] != 'fit_used')[:4000]}

## Assumptions

- Salt `cp(T)` is effectively constant in the native case configurations, so the
  preserved bulk-temperature definition is compatible with `rho*u*cp` weighting.
- Branch-level intended versus parasitic heat separation depends on the current
  thermal-role metadata and remains a bounded decomposition, not a material
  resistance split.
- Positive `Nu` and positive apparent Darcy factor are required for defended
  fits; screened-only or sign-ambiguous rows remain out of the final dependency.

## Uncertainty

- Friction uncertainty comes mainly from small sample count and class separation
  between `lower_leg` and `test_section_span`.
- Thermal uncertainty comes mainly from weak branchwise enthalpy closure even
  where support-gated effective HTC looks numerically clean.
- Sensitivity conclusions are summarized in `sensitivity_summary.csv`.

## Sensitivity conclusions

{chr(10).join(f"- `{row['asset_family']}` / `{row['sensitivity_name']}`: rows `{row['base_row_count']}` -> `{row['sensitivity_row_count']}`, qualitative change `{row['qualitative_conclusion_changed']}`. {row['note']}" for row in sensitivity_rows)}

## Water-family extension plan

1. Replicate the same provenance map and closure-gating structure for water.
2. Preserve the same distinction between defended rows, screened-only rows, and
   sensitivity-only rows.
3. Do not publish a combined water+salt dependency until feature-hydraulic and
   thermal-residual gates are equivalently resolved on the water side.
"""
    (output_dir / "model_dependency_handoff.md").write_text(text, encoding="utf-8")


def build_summary(
    thermal_rows: list[dict[str, Any]],
    hydraulic_rows: list[dict[str, Any]],
    friction_results: dict[str, Any],
    nu_results: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generated_at": iso_timestamp(),
        "case_count": len({row["source_id"] for row in thermal_rows}),
        "thermal": {
            "row_count": len(thermal_rows),
            "screened_candidate_count": sum(1 for row in thermal_rows if row["screened_candidate_flag"] == "yes"),
            "closure_supported_count": sum(1 for row in thermal_rows if row["closure_supported_candidate_flag"] == "yes"),
            "fit_used_count": sum(1 for row in thermal_rows if row["fit_use_status"] == "fit_used"),
            "sensitivity_only_count": sum(1 for row in thermal_rows if row["fit_use_status"] == "sensitivity_only"),
            "excluded_count": sum(1 for row in thermal_rows if row["fit_use_status"] == "excluded"),
        },
        "hydraulic": {
            "row_count": len(hydraulic_rows),
            "straight_fit_used_count": sum(
                1 for row in hydraulic_rows if row["asset_family"] == "straight_section_friction" and row["fit_use_status"] == "fit_used"
            ),
            "feature_excluded_count": sum(1 for row in hydraulic_rows if row["asset_family"] == "feature_keff"),
        },
        "friction_dependency": {
            "recommended_status": friction_results["recommended_status"],
            "recommended_model": friction_results["recommended_model"],
        },
        "nu_dependency": {
            "recommended_status": nu_results["recommended_status"],
            "recommended_model": nu_results["recommended_model"],
        },
    }


def write_schema_checked_csv(path: Path, columns: Sequence[str], rows: list[dict[str, Any]]) -> None:
    trimmed_rows = [{column: row.get(column, "") for column in columns} for row in rows]
    csv_dump(path, list(columns), trimmed_rows if trimmed_rows else csv_rows_for_empty_schema(columns))
    with path.open("r", encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    if header != list(columns):
        raise RuntimeError(f"schema mismatch for {path.name}: expected {columns}, got {header}")


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))
    source_ids = set(args.source_ids or []) or None

    contexts = load_case_contexts(source_ids)

    branch_rows = filter_salt_rows(load_csv_rows(CHECKPOINT_DIR / "phase3_branch_trust_gate" / "branch_promotion_gate.csv"), source_ids)
    enthalpy_rows = filter_salt_rows(load_csv_rows(SALT_CLOSURE_DIR / "salt_leg_enthalpy_summary.csv"), source_ids)
    grouped_heat_rows = filter_salt_rows(load_csv_rows(FIELD_TRANSPORT_DIR / "field_transport_grouped_heat_comparison.csv"), source_ids)
    streamwise_rows = filter_salt_rows(load_csv_rows(FIELD_TRANSPORT_DIR / "field_transport_streamwise_heat_comparison.csv"), source_ids)
    bulk_centerline_rows = filter_salt_rows(load_csv_rows(PRESSURE_DIR / "bulk_vs_centerline_temperature_correction.csv"), source_ids)
    section_summary_rows = filter_salt_rows(load_csv_rows(PRESSURE_DIR / "fluid_side_htc_nu_section_summary.csv"), source_ids)
    heat_case_rows = filter_salt_rows(load_csv_rows(DASHBOARD_DIR / "salt_dashboard.csv"), source_ids)
    straight_rows = filter_salt_rows(load_csv_rows(SALT_CLOSURE_DIR / "salt_straight_section_correlation_inputs.csv"), source_ids)
    feature_rows = filter_salt_rows(load_csv_rows(SALT_CLOSURE_DIR / "salt_feature_correlation_inputs.csv"), source_ids)

    require_columns(branch_rows, ["source_id", "branch_name", "fit_status", "fit_reason", "usable_fraction"], "branch_promotion_gate.csv")
    require_columns(enthalpy_rows, ["source_id", "span_name", "mean_enthalpy_change_w", "mean_wall_heat_total_w"], "salt_leg_enthalpy_summary.csv")
    require_columns(grouped_heat_rows, ["source_id", "span_name", "mean_wall_heat_w", "thermal_role_group"], "field_transport_grouped_heat_comparison.csv")
    require_columns(streamwise_rows, ["source_id", "span_name", "mean_wall_heat_w"], "field_transport_streamwise_heat_comparison.csv")
    require_columns(straight_rows, ["source_id", "span_name", "fit_status", "fit_reason", "hydraulic_diameter_m", "bulk_velocity_m_s"], "salt_straight_section_correlation_inputs.csv")
    require_columns(feature_rows, ["source_id", "feature_name", "fit_status", "fit_reason"], "salt_feature_correlation_inputs.csv")

    thermal_rows = build_thermal_rows(
        contexts,
        branch_rows,
        enthalpy_rows,
        grouped_heat_rows,
        streamwise_rows,
        bulk_centerline_rows,
        heat_case_rows,
        straight_rows,
        property_convention="branch_bulk",
    )
    thermal_rows_case_probe = build_thermal_rows(
        contexts,
        branch_rows,
        enthalpy_rows,
        grouped_heat_rows,
        streamwise_rows,
        bulk_centerline_rows,
        heat_case_rows,
        straight_rows,
        property_convention="case_probe",
    )
    thermal_rows_latest_target = build_latest_target_thermal_rows(thermal_rows, section_summary_rows)
    hydraulic_rows = build_hydraulic_rows(
        contexts,
        straight_rows,
        feature_rows,
        branch_rows,
        property_convention="branch_bulk",
    )

    thermal_fit_rows = [row for row in thermal_rows if row["fit_use_status"] == "fit_used"]
    hydraulic_fit_rows = [row for row in hydraulic_rows if row["asset_family"] == "straight_section_friction" and row["fit_use_status"] == "fit_used"]
    thermal_exclusion_summary = summarize_exclusions(
        [{"asset_family": "thermal_branch", **row} for row in thermal_rows],
        asset_column="asset_family",
    )
    branch_trust_summary = summarize_branch_trust(thermal_rows)
    hydraulic_exclusion_summary = summarize_exclusions(hydraulic_rows)
    sensitivity_rows, friction_results, nu_results = build_sensitivity_rows(
        thermal_rows,
        thermal_rows_case_probe,
        thermal_rows_latest_target,
        hydraulic_rows,
    )
    provenance_rows = build_provenance_rows()
    summary = build_summary(thermal_rows, hydraulic_rows, friction_results, nu_results)

    write_schema_checked_csv(output_dir / "thermal_decomposition_rows.csv", THERMAL_DECOMPOSITION_COLUMNS, thermal_rows)
    write_schema_checked_csv(output_dir / "thermal_fit_ready_rows.csv", THERMAL_FIT_READY_COLUMNS, thermal_fit_rows)
    write_schema_checked_csv(output_dir / "thermal_exclusion_summary.csv", ["asset_family", "exclusion_reason_primary", "row_count"], thermal_exclusion_summary)
    write_schema_checked_csv(output_dir / "branch_trust_summary.csv", ["branch_name", "row_count", "screened_candidate_count", "closure_supported_count", "fit_used_count", "sensitivity_only_count", "excluded_count", "dominant_exclusion_reason"], branch_trust_summary)
    write_schema_checked_csv(output_dir / "hydraulic_hardening_audit.csv", HYDRAULIC_AUDIT_COLUMNS, hydraulic_rows)
    write_schema_checked_csv(output_dir / "hydraulic_fit_ready_rows.csv", HYDRAULIC_FIT_READY_COLUMNS, hydraulic_fit_rows)
    write_schema_checked_csv(output_dir / "hydraulic_exclusion_summary.csv", ["asset_family", "exclusion_reason_primary", "row_count"], hydraulic_exclusion_summary)
    write_schema_checked_csv(output_dir / "sensitivity_summary.csv", SENSITIVITY_COLUMNS, sensitivity_rows)
    write_schema_checked_csv(output_dir / "provenance_map.csv", PROVENANCE_COLUMNS, provenance_rows)

    json_dump(output_dir / "salt_friction_fit_results.json", friction_results)
    json_dump(output_dir / "salt_nu_fit_results.json", nu_results)
    json_dump(output_dir / "summary.json", summary)
    write_readme(
        output_dir,
        summary,
        thermal_rows,
        hydraulic_rows,
        thermal_fit_rows,
        hydraulic_fit_rows,
        thermal_exclusion_summary,
        hydraulic_exclusion_summary,
        friction_results,
        nu_results,
    )
    write_model_handoff(output_dir, thermal_rows, hydraulic_rows, friction_results, nu_results, sensitivity_rows)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
