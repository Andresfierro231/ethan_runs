#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from tools.common import WORKSPACE_ROOT, csv_dump, load_yaml, safe_float

ROOT = WORKSPACE_ROOT
RAW_CASE_ANALYSIS_ROOT = ROOT / "tmp" / "2026-06-15_live_case_analysis"
PRESSURE_DIR = ROOT / "reports" / "2026-06-17_ethan_pressure_htc_boundarylayer_package"
FIELD_TRANSPORT_DIR = ROOT / "reports" / "2026-06-15_ethan_all_runs_field_transport_campaign"
SALT_CLOSURE_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_closure_correlation_package"
SALT_CHECKPOINT_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_analysis_checkpoint_suite"
MODEL_DEPENDENCY_V1_DIR = ROOT / "reports" / "2026-06-18_ethan_salt_model_dependency_package"
NONDIM_DIR = ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package"
CASE_METADATA_CSV = ROOT / "reports" / "2026-06-04_ethan_case_metadata_index" / "ethan_case_metadata_index.csv"

THERMAL_BLOCKED_BRANCHES = {"right_leg"}
THERMAL_DERIVED_BRANCHES = {"upcomer"}
FEATURE_CLASS_MAP = {
    "corner_lower_left": "bend",
    "corner_lower_right": "bend",
    "corner_upper_left": "bend",
    "corner_upper_right": "bend",
    "test_section_complex": "quartz_transition",
}
DIRECT_THERMAL_BRANCHES = {
    "left_lower_leg",
    "left_upper_leg",
    "lower_leg",
    "right_leg",
    "test_section_span",
    "upper_leg",
}


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
    display_label: str
    case_order: int
    source_root: Path
    package_root: Path
    probe_t_avg_k: float
    heater_power_w: float
    cooling_power_w: float
    ambient_proxy_fraction_of_heater: float
    cooling_removal_fraction_of_heater: float
    junction_loss_fraction_of_heater: float
    net_heat_imbalance_fraction_of_heater: float
    property_model: PropertyModel


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_dump_rows(path: Path, rows: list[dict[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    if fieldnames is None:
        if not rows:
            raise RuntimeError(f"cannot write empty table without an explicit schema: {path}")
        fieldnames = list(rows[0].keys())
    csv_dump(path, fieldnames, rows)


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


def normalized_residual(residual_value: float, reference_value: float) -> float:
    if not math.isfinite(residual_value) or not math.isfinite(reference_value) or abs(reference_value) == 0.0:
        return math.nan
    return float(abs(residual_value) / abs(reference_value))


def sign_token(value: float, zero_tol: float = 0.0) -> str:
    if not math.isfinite(value):
        return "nan"
    if value > zero_tol:
        return "positive"
    if value < -zero_tol:
        return "negative"
    return "zero"


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


def choose_property_temperature(context: CaseContext, bulk_temp_k: float, convention: str) -> float:
    if convention == "case_probe":
        return context.probe_t_avg_k
    return bulk_temp_k


def build_dimensionless_bundle(
    context: CaseContext,
    bulk_temp_k: float,
    velocity_m_s: float,
    dh_m: float,
    htc_w_m2_k: float,
    convention: str,
) -> dict[str, float]:
    property_temp = choose_property_temperature(context, bulk_temp_k, convention)
    rho = evaluate_rho(context.property_model, property_temp)
    mu = evaluate_mu(context.property_model, property_temp)
    cp = evaluate_cp(context.property_model, property_temp)
    k_value = evaluate_k(context.property_model, property_temp)
    re_value = rho * velocity_m_s * dh_m / mu if all(math.isfinite(v) for v in (rho, velocity_m_s, dh_m, mu)) and mu > 0.0 else math.nan
    pr_value = cp * mu / k_value if all(math.isfinite(v) for v in (cp, mu, k_value)) and k_value > 0.0 else math.nan
    pe_value = re_value * pr_value if math.isfinite(re_value) and math.isfinite(pr_value) else math.nan
    nu_value = htc_w_m2_k * dh_m / k_value if all(math.isfinite(v) for v in (htc_w_m2_k, dh_m, k_value)) and k_value > 0.0 else math.nan
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


def load_case_contexts(
    source_ids: set[str] | None = None,
    package_root_overrides: dict[str, Path] | None = None,
) -> dict[str, CaseContext]:
    dashboard_rows = load_csv_rows(NONDIM_DIR / "salt_dashboard.csv")
    metadata_rows = load_csv_rows(CASE_METADATA_CSV)
    require_columns(dashboard_rows, ["source_id", "display_label", "package_root", "probe_T_avg_K"], "salt_dashboard.csv")
    require_columns(metadata_rows, ["source_id", "source_root", "cooler_h_W_m2K"], "ethan_case_metadata_index.csv")
    metadata_map = {row["source_id"]: row for row in metadata_rows}
    contexts: dict[str, CaseContext] = {}
    for order, row in enumerate(dashboard_rows):
        source_id = row["source_id"]
        if source_ids and source_id not in source_ids:
            continue
        package_root = (
            package_root_overrides[source_id].resolve()
            if package_root_overrides and source_id in package_root_overrides
            else Path(row["package_root"])
        )
        if not package_root.exists():
            continue
        metadata = metadata_map.get(source_id)
        if metadata is None:
            continue
        source_root = Path(metadata["source_root"])
        if not (source_root / "case_config.yaml").exists():
            runtime_root = Path(str(metadata.get("active_runtime_root", "")))
            if (runtime_root / "case_config.yaml").exists():
                source_root = runtime_root
        case_config = load_yaml(source_root / "case_config.yaml")
        fluid_props = case_config["fluid_properties"]
        mu_spec = fluid_props["mu_spec"]
        contexts[source_id] = CaseContext(
            source_id=source_id,
            display_label=row["display_label"],
            case_order=order,
            source_root=source_root,
            package_root=package_root,
            probe_t_avg_k=finite_float(row.get("probe_T_avg_K")),
            heater_power_w=finite_float(row.get("heater_power_W")),
            cooling_power_w=finite_float(row.get("cooling_power_W")),
            ambient_proxy_fraction_of_heater=finite_float(row.get("ambient_proxy_fraction_of_heater")),
            cooling_removal_fraction_of_heater=finite_float(row.get("cooling_removal_fraction_of_heater")),
            junction_loss_fraction_of_heater=finite_float(row.get("junction_loss_fraction_of_heater")),
            net_heat_imbalance_fraction_of_heater=finite_float(row.get("net_heat_imbalance_fraction_of_heater")),
            property_model=PropertyModel(
                mu_type=str(mu_spec["type"]),
                mu_coeffs=tuple(float(value) for value in mu_spec["coeffs"]),
                cp_coeffs=tuple(float(value) for value in fluid_props["Cp_coeffs"]),
                rho_coeffs=tuple(float(value) for value in fluid_props["rho_coeffs"]),
                k_coeffs=tuple(float(value) for value in fluid_props["kappa_spec"]["coeffs"]),
            ),
        )
    if not contexts:
        raise RuntimeError("no Salt case contexts resolved")
    return contexts


def filter_salt_rows(rows: list[dict[str, str]], source_ids: set[str] | None = None) -> list[dict[str, str]]:
    payload = [row for row in rows if row.get("source_id")]
    payload = [row for row in payload if "water" not in row["source_id"].lower()]
    if source_ids:
        payload = [row for row in payload if row["source_id"] in source_ids]
    return payload


def local_side_support_mean(
    rows: list[dict[str, str]],
    from_start: bool,
    value_key: str,
    count: int,
) -> tuple[float, int, list[dict[str, str]]]:
    ordered = rows if from_start else list(reversed(rows))
    usable = [row for row in ordered if math.isfinite(finite_float(row.get(value_key)))]
    selected = usable[:count]
    if not selected:
        return math.nan, 0, []
    return safe_mean(finite_float(row.get(value_key)) for row in selected), len(selected), selected


def summarize_case_timeseries_rows(
    rows: list[dict[str, Any]],
    group_keys: Sequence[str],
    numeric_keys: Sequence[str],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(tuple(row[key] for key in group_keys), []).append(row)
    output: list[dict[str, Any]] = []
    for key, payload in grouped.items():
        summary: dict[str, Any] = {group_key: value for group_key, value in zip(group_keys, key)}
        summary["time_sample_count"] = len(payload)
        for numeric_key in numeric_keys:
            summary[f"mean_{numeric_key}"] = safe_mean(finite_float(row.get(numeric_key)) for row in payload)
            summary[f"min_{numeric_key}"] = min(
                (finite_float(row.get(numeric_key)) for row in payload if math.isfinite(finite_float(row.get(numeric_key)))),
                default=math.nan,
            )
            summary[f"max_{numeric_key}"] = max(
                (finite_float(row.get(numeric_key)) for row in payload if math.isfinite(finite_float(row.get(numeric_key)))),
                default=math.nan,
            )
        output.append(summary)
    return output
