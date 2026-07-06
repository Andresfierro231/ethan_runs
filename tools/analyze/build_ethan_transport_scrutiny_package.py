#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, save_matplotlib_figure, safe_float  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-17_ethan_transport_scrutiny_package"
DEFAULT_PACKAGE_INDEX_CSV = (
    ROOT / "reports" / "2026-06-15_ethan_all_runs_field_transport_campaign" / "field_transport_package_index.csv"
)
DEFAULT_REPRESENTATIVE_SUMMARY = ROOT / "reports" / "2026-06-15_ethan_representative_transport_comparison" / "summary.json"
DEFAULT_FIELD_CAMPAIGN_SUMMARY = ROOT / "reports" / "2026-06-15_ethan_field_transport_campaign" / "summary.json"
DEFAULT_ALL_RUNS_SUMMARY = ROOT / "reports" / "2026-06-15_ethan_all_runs_field_transport_campaign" / "summary.json"
DEFAULT_MATH_REFERENCE = ROOT / "reports" / "2026-06-17_ethan_streamwise_transport_math_reference" / "MATH_COMPANION.md"
DEFAULT_INTERPRETATION_README = ROOT / "reports" / "2026-06-17_ethan_transport_interpretation_package" / "README.md"
DEFAULT_CASE_ORDER = (
    "val_salt_test_2_coarse_mesh_laminar",
    "viscosity_screening_salt_test_1_jin_coarse_mesh",
    "viscosity_screening_salt_test_1_kirst_coarse_mesh",
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_kirst_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_kirst_coarse_mesh",
    "val_water_test_1_coarse_mesh_laminar",
    "val_water_test_2_coarse_mesh_laminar",
    "val_water_test_3_coarse_mesh_laminar",
    "val_water_test_4_coarse_mesh_laminar",
)
CASE_STYLE = {
    "val_salt_test_2_coarse_mesh_laminar": ("Salt 2 val", "#111827"),
    "viscosity_screening_salt_test_1_jin_coarse_mesh": ("Salt 1 Jin", "#0b6e4f"),
    "viscosity_screening_salt_test_1_kirst_coarse_mesh": ("Salt 1 Kirst", "#7c3aed"),
    "viscosity_screening_salt_test_2_jin_coarse_mesh": ("Salt 2 Jin", "#0f766e"),
    "viscosity_screening_salt_test_2_kirst_coarse_mesh": ("Salt 2 Kirst", "#bc3908"),
    "viscosity_screening_salt_test_3_jin_coarse_mesh": ("Salt 3 Jin", "#1d4ed8"),
    "viscosity_screening_salt_test_3_kirst_coarse_mesh": ("Salt 3 Kirst", "#be123c"),
    "viscosity_screening_salt_test_4_jin_coarse_mesh": ("Salt 4 Jin", "#a16207"),
    "viscosity_screening_salt_test_4_kirst_coarse_mesh": ("Salt 4 Kirst", "#b45309"),
    "val_water_test_1_coarse_mesh_laminar": ("Water 1", "#2563eb"),
    "val_water_test_2_coarse_mesh_laminar": ("Water 2", "#0891b2"),
    "val_water_test_3_coarse_mesh_laminar": ("Water 3", "#0f766e"),
    "val_water_test_4_coarse_mesh_laminar": ("Water 4", "#4338ca"),
}
THERMAL_FAMILIES = (
    ("effective_htc", "mean_effective_htc_w_m2_k"),
    ("effective_ua", "mean_effective_ua_per_m_w_m_k"),
    ("thermal_resistance", "mean_effective_thermal_resistance_k_m_w"),
)
HYDRAULIC_FAMILIES = (
    ("shear_friction", "mean_darcy_f", "mean_darcy_f_pressure_drop_prgh"),
    ("direct_pressure_gradient", "mean_dp_major_gradient_pa_per_m", "mean_dp_major_gradient_direct_prgh_pa_per_m"),
    (
        "momentum_resistance",
        "mean_momentum_resistance_estimated_pa_s_kg_m",
        "mean_momentum_resistance_direct_prgh_pa_s_kg_m",
    ),
)
STATUS_CODE = {
    "do_not_promote": 0,
    "internal_only": 1,
    "paper_safe": 2,
}
STATUS_LABEL = {
    "do_not_promote": "Do not promote",
    "internal_only": "Internal only",
    "paper_safe": "Paper safe",
}

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a high-scrutiny transport trust package from the finished June 15/17 "
            "Ethan field-transport packages without reopening extraction."
        )
    )
    parser.add_argument(
        "--package-dir",
        action="append",
        help=(
            "Per-case package directory. If omitted, package roots are loaded from "
            "the all-runs field-transport package index."
        ),
    )
    parser.add_argument("--package-index-csv", default=str(DEFAULT_PACKAGE_INDEX_CSV))
    parser.add_argument("--representative-summary", default=str(DEFAULT_REPRESENTATIVE_SUMMARY))
    parser.add_argument("--field-campaign-summary", default=str(DEFAULT_FIELD_CAMPAIGN_SUMMARY))
    parser.add_argument("--all-runs-summary", default=str(DEFAULT_ALL_RUNS_SUMMARY))
    parser.add_argument("--math-reference", default=str(DEFAULT_MATH_REFERENCE))
    parser.add_argument("--interpretation-readme", default=str(DEFAULT_INTERPRETATION_README))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sort_key(source_id: str) -> int:
    try:
        return DEFAULT_CASE_ORDER.index(source_id)
    except ValueError:
        return len(DEFAULT_CASE_ORDER)


def case_label(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#4b5563"))[0]


def case_color(source_id: str) -> str:
    return CASE_STYLE.get(source_id, (source_id, "#4b5563"))[1]


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def finite(value: float | None) -> bool:
    return value is not None and math.isfinite(float(value))


def sign_class(value: float, tolerance: float = 1.0e-12) -> int:
    if not math.isfinite(value) or abs(value) <= tolerance:
        return 0
    return 1 if value > 0.0 else -1


def family_from_source_id(source_id: str) -> str:
    if "salt_test_1" in source_id:
        return "salt1"
    if "salt_test_2" in source_id:
        return "salt2"
    if "salt_test_3" in source_id:
        return "salt3"
    if "salt_test_4" in source_id:
        return "salt4"
    if "water_test_1" in source_id:
        return "water1"
    if "water_test_2" in source_id:
        return "water2"
    if "water_test_3" in source_id:
        return "water3"
    if "water_test_4" in source_id:
        return "water4"
    return "unknown"


def load_package_index_rows(path: Path) -> list[dict[str, str]]:
    rows = load_csv_rows(path)
    if not rows:
        raise RuntimeError(f"Package index is missing or empty: {path}")
    return rows


def resolve_package_dirs(args: argparse.Namespace) -> list[Path]:
    if args.package_dir:
        return [Path(item).resolve() for item in args.package_dir]
    index_rows = load_package_index_rows(Path(args.package_index_csv))
    return [Path(row["package_dir"]).resolve() for row in index_rows]


def load_major_rows(path: Path, source_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        rows.append(
            {
                **row,
                "source_id": source_id,
                "case_label": case_label(source_id),
                "span_name": str(row["span_name"]),
                "mean_darcy_f": safe_float(row.get("mean_darcy_f"), math.nan),
                "mean_darcy_f_pressure_drop_prgh": safe_float(row.get("mean_darcy_f_pressure_drop_prgh"), math.nan),
                "mean_dp_major_gradient_pa_per_m": safe_float(row.get("mean_dp_major_gradient_pa_per_m"), math.nan),
                "mean_dp_major_gradient_direct_prgh_pa_per_m": safe_float(
                    row.get("mean_dp_major_gradient_direct_prgh_pa_per_m"),
                    math.nan,
                ),
                "mean_momentum_resistance_estimated_pa_s_kg_m": safe_float(
                    row.get("mean_momentum_resistance_estimated_pa_s_kg_m"),
                    math.nan,
                ),
                "mean_momentum_resistance_direct_prgh_pa_s_kg_m": safe_float(
                    row.get("mean_momentum_resistance_direct_prgh_pa_s_kg_m"),
                    math.nan,
                ),
                "valid_bin_count": int(row.get("valid_bin_count") or 0),
                "direct_prgh_valid_bin_count": int(row.get("direct_prgh_valid_bin_count") or 0),
                "warning_fraction": safe_float(row.get("warning_fraction"), math.nan),
                "thermal_warning_fraction": safe_float(row.get("thermal_warning_fraction"), math.nan),
            }
        )
    return rows


def load_branch_rows(path: Path, source_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in load_csv_rows(path):
        total_row_count = int(row["total_row_count"])
        usable_row_count = int(row["usable_row_count"])
        masked_row_count = int(row["masked_row_count"])
        rows.append(
            {
                **row,
                "source_id": source_id,
                "case_label": case_label(source_id),
                "branch_name": str(row["branch_name"]),
                "branch_type": str(row["branch_type"]),
                "component_spans": str(row["component_spans"]),
                "total_row_count": total_row_count,
                "usable_row_count": usable_row_count,
                "masked_row_count": masked_row_count,
                "usable_fraction": (
                    safe_float(row.get("usable_fraction"), math.nan)
                    if row.get("usable_fraction") not in (None, "")
                    else float(usable_row_count / max(total_row_count, 1))
                ),
                "thermal_warning_fraction": safe_float(row.get("thermal_warning_fraction"), math.nan),
                "mean_abs_bulk_minus_wall_temp_k": safe_float(row.get("mean_abs_bulk_minus_wall_temp_k"), math.nan),
                "min_abs_bulk_minus_wall_temp_k": safe_float(row.get("min_abs_bulk_minus_wall_temp_k"), math.nan),
                "mean_bulk_positive_mass_flux_kg_s": safe_float(
                    row.get("mean_bulk_positive_mass_flux_kg_s"),
                    math.nan,
                ),
                "min_bulk_positive_mass_flux_kg_s": safe_float(
                    row.get("min_bulk_positive_mass_flux_kg_s"),
                    math.nan,
                ),
                "mean_area_ratio_to_reference": safe_float(row.get("mean_area_ratio_to_reference"), math.nan),
                "max_area_ratio_to_reference": safe_float(row.get("max_area_ratio_to_reference"), math.nan),
                "mean_effective_htc_w_m2_k": safe_float(row.get("mean_effective_htc_w_m2_k"), math.nan),
                "mean_effective_ua_per_m_w_m_k": safe_float(row.get("mean_effective_ua_per_m_w_m_k"), math.nan),
                "mean_effective_thermal_resistance_k_m_w": safe_float(
                    row.get("mean_effective_thermal_resistance_k_m_w"),
                    math.nan,
                ),
            }
        )
    return rows


def classify_raw_thermal_status(row: dict[str, Any]) -> tuple[str, str]:
    usable_fraction = safe_float(row.get("usable_fraction"), math.nan)
    warning_fraction = safe_float(row.get("thermal_warning_fraction"), math.nan)
    min_delta_t = safe_float(row.get("min_abs_bulk_minus_wall_temp_k"), math.nan)
    total_rows = int(row.get("total_row_count") or 0)
    masked_rows = int(row.get("masked_row_count") or 0)
    masked_fraction = float(masked_rows / max(total_rows, 1))
    mean_htc = safe_float(row.get("mean_effective_htc_w_m2_k"), math.nan)

    # A finite mean effective HTC is required before the branch can support any
    # paper-facing effective-transport claim. Missing means the thermal layer
    # never produced enough valid support to summarize the branch at all.
    if not finite(mean_htc):
        return "do_not_promote", "thermal_metric_missing"
    if not finite(usable_fraction) or not finite(warning_fraction) or not finite(min_delta_t):
        return "do_not_promote", "thermal_qc_missing"
    if usable_fraction >= 0.90 and warning_fraction <= 0.10 and min_delta_t >= 0.50:
        return "paper_safe", "thermal_qc_pass"
    if usable_fraction < 0.75:
        return "do_not_promote", "thermal_low_usable_fraction"
    if min_delta_t < 0.25:
        return "do_not_promote", "thermal_small_delta_t"
    if masked_fraction > 0.25:
        return "do_not_promote", "thermal_masked_fraction_high"
    return "internal_only", "thermal_qc_marginal"


def finalize_branch_status(
    row: dict[str, Any],
    base_status: str,
    base_reason: str,
    component_statuses: dict[str, str],
) -> tuple[str, str]:
    if str(row["branch_type"]) != "derived_branch":
        return base_status, base_reason
    component_names = [item.strip() for item in str(row["component_spans"]).split(",") if item.strip()]
    component_codes = [component_statuses.get(name, "do_not_promote") for name in component_names]
    if any(code == "do_not_promote" for code in component_codes):
        return "do_not_promote", "derived_branch_component_blocked"
    if base_status == "paper_safe" and any(code == "internal_only" for code in component_codes):
        return "internal_only", "derived_branch_component_marginal"
    return base_status, base_reason


def classify_hydraulic_pair(
    estimated_value: float,
    direct_value: float,
    direct_support_fraction: float,
) -> tuple[str, str]:
    if not finite(estimated_value) or not finite(direct_value):
        return "do_not_promote", "hydraulic_metric_missing"
    est_sign = sign_class(float(estimated_value))
    direct_sign = sign_class(float(direct_value))
    if est_sign == 0 or direct_sign == 0:
        return "internal_only", "hydraulic_near_zero_signal"
    if est_sign != direct_sign:
        return "do_not_promote", "hydraulic_sign_disagreement"
    if not finite(direct_support_fraction):
        return "internal_only", "hydraulic_support_missing"
    if direct_support_fraction < 0.75:
        return "internal_only", "hydraulic_low_direct_support"
    ratio = abs(float(direct_value)) / max(abs(float(estimated_value)), 1.0e-12)
    if 0.25 <= ratio <= 4.0:
        return "paper_safe", "hydraulic_agreement_pass"
    return "internal_only", "hydraulic_magnitude_mismatch"


def likely_cause_from_reason(reason_code: str) -> str:
    mapping = {
        "thermal_metric_missing": "The effective thermal reduction did not retain enough valid rows to summarize the branch.",
        "thermal_qc_missing": "Required QC fields are absent, so the branch cannot be audited safely.",
        "thermal_qc_pass": "Thermal support metrics pass the current scrutiny thresholds.",
        "thermal_low_usable_fraction": "Too much of the branch is masked or support-limited for a stable effective ratio claim.",
        "thermal_small_delta_t": "The thermal driving temperature difference approaches zero, so HTC-style ratios become unstable by design.",
        "thermal_masked_fraction_high": "Masked rows dominate the branch summary strongly enough that the mean ratio is not trustworthy.",
        "thermal_qc_marginal": "The branch remains interpretable internally, but one support metric is too marginal for paper promotion.",
        "derived_branch_component_blocked": "The derived upcomer inherits one or more blocked component spans.",
        "derived_branch_component_marginal": "The derived upcomer reuses at least one marginal component span, so it cannot be cleaner than its inputs.",
        "hydraulic_metric_missing": "One or both hydraulic reductions are missing or non-finite for the span summary.",
        "hydraulic_near_zero_signal": "One hydraulic reduction collapses toward zero, so sign and ratio checks are not decisive.",
        "hydraulic_sign_disagreement": "Shear-based and direct wall-registered reductions disagree on the pressure-drop direction.",
        "hydraulic_low_direct_support": "The direct wall-registered reduction exists but does not cover enough valid bins to support a paper claim.",
        "hydraulic_support_missing": "The direct support fraction needed for the hydraulic comparison is absent.",
        "hydraulic_magnitude_mismatch": "Shear-based and direct wall-registered reductions share the sign but disagree materially in magnitude.",
        "hydraulic_agreement_pass": "Shear-based and direct wall-registered reductions support the same span-level story.",
        "context_only_landmarks": "Boundary-layer landmarks remain comparative context, not headline closure metrics.",
        "boundary_layer_missing": "No boundary-layer landmark summary is present for the case package.",
    }
    return mapping.get(reason_code, "No cause text recorded for this reason code.")


def contradiction_requires_code_fix(reason_code: str) -> str:
    return "yes" if reason_code == "hydraulic_sign_disagreement" else "no"


def build_claim_matrix(
    packages: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    claim_rows: list[dict[str, Any]] = []
    contradiction_rows: list[dict[str, Any]] = []

    for package in packages:
        source_id = str(package["source_id"])
        case_label_text = str(package["case_label"])
        branch_rows = list(package["branch_rows"])
        major_rows = list(package["major_rows"])
        branch_source_path = relative_path(Path(package["branch_summary_path"]))
        major_source_path = relative_path(Path(package["major_summary_path"]))
        boundary_source_path = relative_path(Path(package["boundary_layer_mean_summary_path"]))

        base_branch_status: dict[str, tuple[str, str]] = {}
        for row in branch_rows:
            status, reason = classify_raw_thermal_status(row)
            base_branch_status[str(row["branch_name"])] = (status, reason)

        final_branch_status: dict[str, tuple[str, str]] = {}
        component_status_map = {name: status for name, (status, _reason) in base_branch_status.items()}
        for row in branch_rows:
            branch_name = str(row["branch_name"])
            raw_status, raw_reason = base_branch_status[branch_name]
            final_branch_status[branch_name] = finalize_branch_status(row, raw_status, raw_reason, component_status_map)

        for row in branch_rows:
            branch_name = str(row["branch_name"])
            status, reason = final_branch_status[branch_name]
            for variable_family, metric_field in THERMAL_FAMILIES:
                metric_value = safe_float(row.get(metric_field), math.nan)
                claim_rows.append(
                    {
                        "source_id": source_id,
                        "case_label": case_label_text,
                        "family": family_from_source_id(source_id),
                        "scope_type": "branch",
                        "scope_name": branch_name,
                        "variable_family": variable_family,
                        "scrutiny_status": status,
                        "reason_code": reason,
                        "metric_value": metric_value,
                        "primary_source_path": branch_source_path,
                    }
                )
            if status != "paper_safe":
                contradiction_rows.append(
                    {
                        "source_id": source_id,
                        "case_label": case_label_text,
                        "scope_name": branch_name,
                        "contradiction_type": "thermal_support_limit",
                        "affected_variable_families": "effective_htc,effective_ua,thermal_resistance",
                        "observed_pattern": (
                            f"usable_fraction={row['usable_fraction']:.3f}, "
                            f"thermal_warning_fraction={row['thermal_warning_fraction']:.3f}, "
                            f"min_abs_delta_t={row['min_abs_bulk_minus_wall_temp_k']:.3f}, "
                            f"mean_htc={safe_float(row['mean_effective_htc_w_m2_k'], math.nan):.3f}"
                        ),
                        "likely_cause": likely_cause_from_reason(reason),
                        "requires_code_fix": contradiction_requires_code_fix(reason),
                        "primary_source_path": branch_source_path,
                    }
                )

        for row in major_rows:
            span_name = str(row["span_name"])
            direct_support_fraction = float(
                int(row["direct_prgh_valid_bin_count"]) / max(int(row["valid_bin_count"]), 1)
            )
            family_status: dict[str, tuple[str, str]] = {}
            for variable_family, estimated_field, direct_field in HYDRAULIC_FAMILIES:
                status, reason = classify_hydraulic_pair(
                    safe_float(row.get(estimated_field), math.nan),
                    safe_float(row.get(direct_field), math.nan),
                    direct_support_fraction,
                )
                family_status[variable_family] = (status, reason)
                claim_rows.append(
                    {
                        "source_id": source_id,
                        "case_label": case_label_text,
                        "family": family_from_source_id(source_id),
                        "scope_type": "span_section",
                        "scope_name": span_name,
                        "variable_family": variable_family,
                        "scrutiny_status": status,
                        "reason_code": reason,
                        "metric_value": safe_float(row.get(estimated_field), math.nan),
                        "primary_source_path": major_source_path,
                    }
                )

            # The contradiction log stays one row per span to keep it readable.
            worst_status = min(
                (STATUS_CODE[status] for status, _reason in family_status.values()),
                default=STATUS_CODE["paper_safe"],
            )
            if worst_status < STATUS_CODE["paper_safe"]:
                candidate_reason = next(
                    reason
                    for status, reason in family_status.values()
                    if STATUS_CODE[status] == worst_status
                )
                contradiction_rows.append(
                    {
                        "source_id": source_id,
                        "case_label": case_label_text,
                        "scope_name": span_name,
                        "contradiction_type": "hydraulic_agreement_limit",
                        "affected_variable_families": ",".join(name for name, _lhs, _rhs in HYDRAULIC_FAMILIES),
                        "observed_pattern": (
                            f"shear_grad={safe_float(row['mean_dp_major_gradient_pa_per_m'], math.nan):.3f}, "
                            f"direct_grad={safe_float(row['mean_dp_major_gradient_direct_prgh_pa_per_m'], math.nan):.3f}, "
                            f"direct_support_fraction={direct_support_fraction:.3f}"
                        ),
                        "likely_cause": likely_cause_from_reason(candidate_reason),
                        "requires_code_fix": contradiction_requires_code_fix(candidate_reason),
                        "primary_source_path": major_source_path,
                    }
                )

        boundary_status = "internal_only" if Path(package["boundary_layer_mean_summary_path"]).exists() else "do_not_promote"
        boundary_reason = "context_only_landmarks" if boundary_status == "internal_only" else "boundary_layer_missing"
        claim_rows.append(
            {
                "source_id": source_id,
                "case_label": case_label_text,
                "family": family_from_source_id(source_id),
                "scope_type": "loopwise",
                "scope_name": "boundary_layer_landmarks",
                "variable_family": "boundary_layer_context",
                "scrutiny_status": boundary_status,
                "reason_code": boundary_reason,
                "metric_value": math.nan,
                "primary_source_path": boundary_source_path,
            }
        )

    claim_rows.sort(
        key=lambda row: (
            sort_key(str(row["source_id"])),
            str(row["scope_type"]),
            str(row["scope_name"]),
            str(row["variable_family"]),
        )
    )
    contradiction_rows.sort(
        key=lambda row: (
            sort_key(str(row["source_id"])),
            str(row["scope_name"]),
            str(row["contradiction_type"]),
        )
    )
    return claim_rows, contradiction_rows


def status_from_claims(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "blocked"
    statuses = {str(row["scrutiny_status"]) for row in rows}
    if "do_not_promote" in statuses:
        return "blocked"
    if "internal_only" in statuses:
        return "allowed_with_caveat"
    return "allowed"


def subset_status_from_claims(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "blocked"
    statuses = {str(row["scrutiny_status"]) for row in rows}
    if "paper_safe" in statuses:
        return "allowed_with_caveat" if ("internal_only" in statuses or "do_not_promote" in statuses) else "allowed"
    if "internal_only" in statuses:
        return "allowed_with_caveat"
    return "blocked"


def safe_branch_subset(rows: list[dict[str, Any]]) -> str:
    ordered_names = [
        name
        for name in ("lower_leg", "right_leg", "left_lower_leg", "test_section_span", "left_upper_leg", "upper_leg", "upcomer")
    ]
    safe_names = []
    for branch_name in ordered_names:
        branch_rows = [
            row
            for row in rows
            if str(row["scope_name"]) == branch_name and str(row["scrutiny_status"]) == "paper_safe"
        ]
        if branch_rows:
            safe_names.append(branch_name)
    return ", ".join(safe_names)


def build_paper_safe_asset_map(
    claim_rows: list[dict[str, Any]],
    representative_summary: Path,
    field_campaign_summary: Path,
    all_runs_summary: Path,
) -> list[dict[str, Any]]:
    salt2_ids = {
        "val_salt_test_2_coarse_mesh_laminar",
        "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "viscosity_screening_salt_test_2_kirst_coarse_mesh",
    }
    salt_ids = {row["source_id"] for row in claim_rows if str(row["source_id"]).startswith("viscosity_screening_salt") or str(row["source_id"]).startswith("val_salt")}

    def subset_rows(
        *,
        source_ids: set[str] | None = None,
        scope_type: str | None = None,
        variable_families: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        result = []
        for row in claim_rows:
            if source_ids is not None and str(row["source_id"]) not in source_ids:
                continue
            if scope_type is not None and str(row["scope_type"]) != scope_type:
                continue
            if variable_families is not None and str(row["variable_family"]) not in variable_families:
                continue
            result.append(row)
        return result

    salt2_hydraulic_rows = subset_rows(
        source_ids=salt2_ids,
        scope_type="span_section",
        variable_families={"shear_friction", "direct_pressure_gradient", "momentum_resistance"},
    )
    salt2_thermal_rows = subset_rows(
        source_ids=salt2_ids,
        scope_type="branch",
        variable_families={"effective_htc", "effective_ua", "thermal_resistance"},
    )
    salt2_boundary_rows = subset_rows(
        source_ids=salt2_ids,
        scope_type="loopwise",
        variable_families={"boundary_layer_context"},
    )
    salt_branch_rows = subset_rows(
        source_ids=salt_ids,
        scope_type="branch",
        variable_families={"effective_htc", "effective_ua", "thermal_resistance"},
    )

    return [
        {
            "asset_id": "salt_family_heat_loss_campaign",
            "promotion_status": "allowed",
            "recommended_placement": "main_text",
            "recommended_scope_filter": "Salt 2 and Salt 4 subsets already paper-side regenerated",
            "primary_source_path": relative_path(field_campaign_summary),
            "supporting_variable_families": "streamwise_heat_loss,grouped_heat_loss",
            "blocking_reason": "none",
        },
        {
            "asset_id": "salt_family_azimuthal_campaign",
            "promotion_status": "allowed_with_caveat",
            "recommended_placement": "main_text_with_caveat",
            "recommended_scope_filter": "Salt 2 and Salt 4 subsets; avoid reading this as a full circumferential resolution claim",
            "primary_source_path": relative_path(field_campaign_summary),
            "supporting_variable_families": "azimuthal_transport_mean",
            "blocking_reason": "Campaign azimuthal means are stable, but they should stay circ-mean and trend-level only.",
        },
        {
            "asset_id": "salt_family_branch_thermal_campaign",
            "promotion_status": subset_status_from_claims(salt_branch_rows),
            "recommended_placement": "appendix_only" if subset_status_from_claims(salt_branch_rows) == "blocked" else "main_text_with_caveat",
            "recommended_scope_filter": safe_branch_subset(salt_branch_rows),
            "primary_source_path": relative_path(field_campaign_summary),
            "supporting_variable_families": "effective_htc,effective_ua,thermal_resistance",
            "blocking_reason": "Use only paper-safe branches; blocked or marginal branches require QC explanation first.",
        },
        {
            "asset_id": "salt_family_branch_thermal_qc_campaign",
            "promotion_status": "allowed_with_caveat",
            "recommended_placement": "appendix_only",
            "recommended_scope_filter": "All branches; this is a support figure, not a headline result",
            "primary_source_path": relative_path(field_campaign_summary),
            "supporting_variable_families": "thermal_qc_support",
            "blocking_reason": "Keep as support/appendix so the paper can show why selected branch ratios are or are not trustworthy.",
        },
        {
            "asset_id": "salt2_hydraulic_mechanism",
            "promotion_status": status_from_claims(salt2_hydraulic_rows),
            "recommended_placement": "main_text_with_caveat" if status_from_claims(salt2_hydraulic_rows) != "blocked" else "internal_only",
            "recommended_scope_filter": "Narrate broad redistribution only; do not anchor claims on blocked spans if any appear",
            "primary_source_path": relative_path(representative_summary),
            "supporting_variable_families": "shear_friction,direct_pressure_gradient,momentum_resistance",
            "blocking_reason": "Promote only if the mechanism text stays above unresolved direct-vs-shear disagreements.",
        },
        {
            "asset_id": "salt2_effective_thermal_mechanism",
            "promotion_status": subset_status_from_claims(salt2_thermal_rows),
            "recommended_placement": "main_text_with_caveat" if subset_status_from_claims(salt2_thermal_rows) != "blocked" else "internal_only",
            "recommended_scope_filter": safe_branch_subset(salt2_thermal_rows),
            "primary_source_path": relative_path(representative_summary),
            "supporting_variable_families": "effective_htc,effective_ua,thermal_resistance",
            "blocking_reason": "Narrate only the branch/loop regions that pass the thermal support rubric.",
        },
        {
            "asset_id": "salt2_branch_thermal_mechanism",
            "promotion_status": subset_status_from_claims(salt2_thermal_rows),
            "recommended_placement": "appendix_only" if subset_status_from_claims(salt2_thermal_rows) == "blocked" else "main_text_with_caveat",
            "recommended_scope_filter": safe_branch_subset(salt2_thermal_rows),
            "primary_source_path": relative_path(representative_summary),
            "supporting_variable_families": "effective_htc,effective_ua,thermal_resistance",
            "blocking_reason": "Use branch views to isolate paper-safe regions such as the upcomer or test-section path, not every branch indiscriminately.",
        },
        {
            "asset_id": "salt2_boundary_layer_context",
            "promotion_status": "blocked",
            "recommended_placement": "appendix_only",
            "recommended_scope_filter": "Comparative context only",
            "primary_source_path": relative_path(representative_summary),
            "supporting_variable_families": "boundary_layer_context",
            "blocking_reason": "Boundary-layer landmarks are not headline closure metrics in the current workflow.",
        },
        {
            "asset_id": "all_runs_branch_thermal_campaign",
            "promotion_status": "allowed_with_caveat",
            "recommended_placement": "internal_only",
            "recommended_scope_filter": "Use for screening, not Salt-paper main text",
            "primary_source_path": relative_path(all_runs_summary),
            "supporting_variable_families": "effective_htc,effective_ua,thermal_resistance",
            "blocking_reason": "This package is valuable for screening, but the current Salt paper is intentionally narrower than all 13 cases.",
        },
    ]


def plot_branch_trust_heatmap(output_dir: Path, branch_rows: list[dict[str, Any]]) -> dict[str, str]:
    branches = [
        "lower_leg",
        "right_leg",
        "left_lower_leg",
        "test_section_span",
        "left_upper_leg",
        "upper_leg",
        "upcomer",
    ]
    cases = sorted({str(row["source_id"]) for row in branch_rows}, key=sort_key)
    data = np.full((len(cases), len(branches)), -1.0)
    for row in branch_rows:
        case_index = cases.index(str(row["source_id"]))
        branch_index = branches.index(str(row["scope_name"]))
        data[case_index, branch_index] = STATUS_CODE[str(row["scrutiny_status"])]

    cmap = ListedColormap(["#b91c1c", "#f59e0b", "#15803d"])
    fig, ax = plt.subplots(figsize=(13.5, 6.5))
    image = ax.imshow(data, aspect="auto", cmap=cmap, vmin=0, vmax=2)
    ax.set_xticks(range(len(branches)))
    ax.set_xticklabels(branches, rotation=35, ha="right")
    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels([case_label(case_id) for case_id in cases])
    ax.set_title("Branch Effective-Thermal Trust Classification")
    for row_index in range(len(cases)):
        for col_index in range(len(branches)):
            value = data[row_index, col_index]
            if value < 0:
                continue
            ax.text(
                col_index,
                row_index,
                ["blocked", "internal", "safe"][int(value)],
                ha="center",
                va="center",
                color="white",
                fontsize=7,
            )
    cbar = fig.colorbar(image, ax=ax, ticks=[0, 1, 2])
    cbar.ax.set_yticklabels(
        [
            STATUS_LABEL["do_not_promote"],
            STATUS_LABEL["internal_only"],
            STATUS_LABEL["paper_safe"],
        ]
    )
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "transport_scrutiny_branch_heatmap", dpi=220)
    plt.close(fig)
    return paths


def plot_hydraulic_agreement(output_dir: Path, hydraulic_rows: list[dict[str, Any]]) -> dict[str, str]:
    cases = sorted({str(row["source_id"]) for row in hydraulic_rows}, key=sort_key)
    counts = {
        case_id: Counter(str(row["scrutiny_status"]) for row in hydraulic_rows if str(row["source_id"]) == case_id)
        for case_id in cases
    }
    x = np.arange(len(cases))
    paper_safe_counts = [counts[case_id]["paper_safe"] for case_id in cases]
    internal_counts = [counts[case_id]["internal_only"] for case_id in cases]
    blocked_counts = [counts[case_id]["do_not_promote"] for case_id in cases]

    fig, ax = plt.subplots(figsize=(13.5, 6.0))
    ax.bar(x, paper_safe_counts, color="#15803d", label="Paper safe")
    ax.bar(x, internal_counts, bottom=paper_safe_counts, color="#f59e0b", label="Internal only")
    ax.bar(
        x,
        blocked_counts,
        bottom=np.array(paper_safe_counts) + np.array(internal_counts),
        color="#b91c1c",
        label="Do not promote",
    )
    ax.set_xticks(x)
    ax.set_xticklabels([case_label(case_id) for case_id in cases], rotation=35, ha="right")
    ax.set_ylabel("Span-level hydraulic family counts")
    ax.set_title("Direct-vs-Shear Hydraulic Agreement Audit")
    ax.legend(loc="upper right", ncol=3)
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "transport_scrutiny_hydraulic_agreement", dpi=220)
    plt.close(fig)
    return paths


def plot_thermal_qc_thresholds(output_dir: Path, branch_rows: list[dict[str, Any]]) -> dict[str, str]:
    cases = sorted({str(row["source_id"]) for row in branch_rows}, key=sort_key)
    selected_branches = ("right_leg", "upper_leg", "upcomer", "test_section_span")
    metrics = {
        "usable_fraction": "Usable fraction",
        "min_abs_bulk_minus_wall_temp_k": "Min |T_bulk - T_wall| [K]",
        "masked_fraction": "Masked fraction",
    }
    data: dict[str, dict[str, list[float]]] = {
        metric: {branch_name: [] for branch_name in selected_branches}
        for metric in metrics
    }
    row_map = {(str(row["source_id"]), str(row["branch_name"])): row for row in branch_rows}
    for case_id in cases:
        for branch_name in selected_branches:
            row = row_map.get((case_id, branch_name))
            if row is None:
                data["usable_fraction"][branch_name].append(math.nan)
                data["min_abs_bulk_minus_wall_temp_k"][branch_name].append(math.nan)
                data["masked_fraction"][branch_name].append(math.nan)
                continue
            total_rows = int(row["total_row_count"])
            masked_fraction = float(int(row["masked_row_count"]) / max(total_rows, 1))
            data["usable_fraction"][branch_name].append(float(row["usable_fraction"]))
            data["min_abs_bulk_minus_wall_temp_k"][branch_name].append(float(row["min_abs_bulk_minus_wall_temp_k"]))
            data["masked_fraction"][branch_name].append(masked_fraction)

    fig, axes = plt.subplots(3, 1, figsize=(13.5, 10.0), sharex=True)
    x = np.arange(len(cases))
    branch_colors = {
        "right_leg": "#bc3908",
        "upper_leg": "#1d4ed8",
        "upcomer": "#0b6e4f",
        "test_section_span": "#7c3aed",
    }
    for axis, (metric, title) in zip(axes, metrics.items()):
        for branch_name in selected_branches:
            axis.plot(
                x,
                data[metric][branch_name],
                marker="o",
                linewidth=1.6,
                label=branch_name,
                color=branch_colors[branch_name],
            )
        axis.set_ylabel(title)
        axis.grid(True, alpha=0.25)
    axes[0].axhline(0.90, color="#15803d", linestyle="--", linewidth=1.0)
    axes[1].axhline(0.50, color="#15803d", linestyle="--", linewidth=1.0)
    axes[1].axhline(0.25, color="#b91c1c", linestyle="--", linewidth=1.0)
    axes[2].axhline(0.25, color="#b91c1c", linestyle="--", linewidth=1.0)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([case_label(case_id) for case_id in cases], rotation=35, ha="right")
    axes[0].legend(loc="upper right", ncol=4)
    axes[0].set_title("Thermal QC Threshold Audit For Representative Branches")
    fig.tight_layout()
    paths = save_matplotlib_figure(fig, output_dir, "transport_scrutiny_thermal_qc", dpi=220)
    plt.close(fig)
    return paths


def summarize_status_counts(claim_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in claim_rows:
        grouped[(str(row["variable_family"]), str(row["scrutiny_status"]))]["count"] += 1
    output_rows: list[dict[str, Any]] = []
    for (variable_family, scrutiny_status), counter in sorted(grouped.items()):
        output_rows.append(
            {
                "variable_family": variable_family,
                "scrutiny_status": scrutiny_status,
                "row_count": counter["count"],
            }
        )
    return output_rows


def write_readme(
    output_dir: Path,
    claim_rows: list[dict[str, Any]],
    contradiction_rows: list[dict[str, Any]],
    paper_asset_rows: list[dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    family_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in claim_rows:
        family_status_counts[str(row["variable_family"])][str(row["scrutiny_status"])] += 1

    blocked_thermal_rows = [
        row
        for row in claim_rows
        if str(row["scope_type"]) == "branch"
        and str(row["variable_family"]) == "effective_htc"
        and str(row["scrutiny_status"]) == "do_not_promote"
    ]
    blocked_thermal_rows.sort(key=lambda row: (sort_key(str(row["source_id"])), str(row["scope_name"])))

    hydraulic_codefix_rows = [
        row for row in contradiction_rows if str(row["requires_code_fix"]) == "yes"
    ]

    lines = [
        "# Ethan Transport Scrutiny Package",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "This package is the high-scrutiny trust audit for the June 15/17 Ethan",
        "transport workflow. It does not regenerate extraction. It classifies the",
        "existing outputs into `paper_safe`, `internal_only`, and",
        "`do_not_promote` so later paper work can promote only the defensible",
        "subset.",
        "",
        "## Canonical Inputs",
        "",
        f"- package index: `{relative_path(Path(args.package_index_csv))}`",
        f"- representative Salt 2 package: `{relative_path(Path(args.representative_summary))}`",
        f"- Salt-family campaign: `{relative_path(Path(args.field_campaign_summary))}`",
        f"- all-runs campaign: `{relative_path(Path(args.all_runs_summary))}`",
        f"- math reference: `{relative_path(Path(args.math_reference))}`",
        f"- prior interpretation package: `{relative_path(Path(args.interpretation_readme))}`",
        "",
        "## Scrutiny Rubric",
        "",
        "- Effective thermal metrics are `paper_safe` only when usable fraction is",
        "  at least `0.90`, thermal warning fraction is at most `0.10`, and the",
        "  minimum resolved `|T_bulk - T_wall|` is at least `0.50 K`.",
        "- Effective thermal metrics are `do_not_promote` when usable fraction drops",
        "  below `0.75`, the minimum resolved `|T_bulk - T_wall|` falls below",
        "  `0.25 K`, or masked rows dominate too strongly.",
        "- Hydraulic span reductions are `paper_safe` only when the shear-based and",
        "  direct wall-registered reductions agree on pressure-drop direction and",
        "  the direct support fraction stays above `0.75`.",
        "- Boundary-layer landmarks remain `internal_only` context even when present.",
        "",
        "## Status Counts By Variable Family",
        "",
    ]
    for variable_family in sorted(family_status_counts):
        counts = family_status_counts[variable_family]
        lines.append(
            f"- `{variable_family}`: paper_safe=`{counts['paper_safe']}`, "
            f"internal_only=`{counts['internal_only']}`, do_not_promote=`{counts['do_not_promote']}`"
        )

    lines.extend(
        [
            "",
            "## Highest-Risk Thermal Branches",
            "",
        ]
    )
    if blocked_thermal_rows:
        for row in blocked_thermal_rows[:8]:
            lines.append(
                f"- `{row['case_label']} / {row['scope_name']}` blocked by `{row['reason_code']}` "
                f"from `{row['primary_source_path']}`"
            )
    else:
        lines.append("- None. Every currently summarized branch passed the thermal rubric.")

    lines.extend(
        [
            "",
            "## Hydraulic Rows That Still Deserve Code-Level Attention",
            "",
        ]
    )
    if hydraulic_codefix_rows:
        for row in hydraulic_codefix_rows[:8]:
            lines.append(
                f"- `{row['case_label']} / {row['scope_name']}`: `{row['likely_cause']}` "
                f"({row['primary_source_path']})"
            )
    else:
        lines.append("- No current span row triggered the `requires_code_fix = yes` rule.")

    lines.extend(
        [
            "",
            "## Paper Promotion Boundary",
            "",
            "- Use `paper_safe_asset_map.csv` as the paper-facing gate, not the raw",
            "  campaign directories.",
            "- Any asset marked `allowed_with_caveat` still requires narrow narration",
            "  and explicit acknowledgement of blocked or marginal regions.",
            "- Any asset marked `blocked` should stay out of the main manuscript until",
            "  either the scope narrows to a safe subset or the contradiction is",
            "  resolved upstream.",
            "",
            "## Main Artifacts",
            "",
            "- `transport_claim_matrix.csv`",
            "- `transport_contradiction_log.csv`",
            "- `paper_safe_asset_map.csv`",
            "- `transport_status_counts.csv`",
            "- `figures/transport_scrutiny_branch_heatmap.*`",
            "- `figures/transport_scrutiny_hydraulic_agreement.*`",
            "- `figures/transport_scrutiny_thermal_qc.*`",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir).resolve())
    package_dirs = resolve_package_dirs(args)

    packages: list[dict[str, Any]] = []
    for package_dir in package_dirs:
        summary_path = package_dir / "summary.json"
        if not summary_path.exists():
            raise RuntimeError(f"Missing summary.json under {package_dir}")
        summary = load_json(summary_path)
        source_id = str(summary["source_id"])
        package_rows = {
            "source_id": source_id,
            "case_label": case_label(source_id),
            "package_dir": package_dir,
            "summary_path": summary_path,
            "major_summary_path": package_dir / "major_loss_summary.csv",
            "branch_summary_path": package_dir / "branch_thermal_summary.csv",
            "boundary_layer_mean_summary_path": package_dir / "boundary_layer_landmark_mean_summary.csv",
        }
        major_rows = load_major_rows(Path(package_rows["major_summary_path"]), source_id)
        branch_rows = load_branch_rows(Path(package_rows["branch_summary_path"]), source_id)
        package_rows["major_rows"] = major_rows
        package_rows["branch_rows"] = branch_rows
        packages.append(package_rows)

    representative_summary = Path(args.representative_summary).resolve()
    field_campaign_summary = Path(args.field_campaign_summary).resolve()
    all_runs_summary = Path(args.all_runs_summary).resolve()

    claim_rows, contradiction_rows = build_claim_matrix(packages)
    branch_claim_rows = [row for row in claim_rows if str(row["scope_type"]) == "branch" and str(row["variable_family"]) == "effective_htc"]
    hydraulic_claim_rows = [
        row
        for row in claim_rows
        if str(row["scope_type"]) == "span_section"
        and str(row["variable_family"]) == "direct_pressure_gradient"
    ]
    branch_status_map = {
        (str(row["source_id"]), str(row["scope_name"])): str(row["scrutiny_status"])
        for row in branch_claim_rows
    }
    audited_branch_rows: list[dict[str, Any]] = []
    for package in packages:
        for row in package["branch_rows"]:
            audited_branch_rows.append(
                {
                    **row,
                    "scrutiny_status": branch_status_map.get(
                        (str(package["source_id"]), str(row["branch_name"])),
                        "do_not_promote",
                    ),
                }
            )
    paper_asset_rows = build_paper_safe_asset_map(
        claim_rows,
        representative_summary,
        field_campaign_summary,
        all_runs_summary,
    )
    status_count_rows = summarize_status_counts(claim_rows)

    branch_heatmap_paths = plot_branch_trust_heatmap(output_dir, branch_claim_rows)
    hydraulic_agreement_paths = plot_hydraulic_agreement(output_dir, hydraulic_claim_rows)
    thermal_qc_paths = plot_thermal_qc_thresholds(output_dir, audited_branch_rows)

    claim_fieldnames = [
        "source_id",
        "case_label",
        "family",
        "scope_type",
        "scope_name",
        "variable_family",
        "scrutiny_status",
        "reason_code",
        "metric_value",
        "primary_source_path",
    ]
    contradiction_fieldnames = [
        "source_id",
        "case_label",
        "scope_name",
        "contradiction_type",
        "affected_variable_families",
        "observed_pattern",
        "likely_cause",
        "requires_code_fix",
        "primary_source_path",
    ]
    paper_asset_fieldnames = [
        "asset_id",
        "promotion_status",
        "recommended_placement",
        "recommended_scope_filter",
        "primary_source_path",
        "supporting_variable_families",
        "blocking_reason",
    ]
    csv_dump(output_dir / "transport_claim_matrix.csv", claim_fieldnames, claim_rows)
    csv_dump(output_dir / "transport_contradiction_log.csv", contradiction_fieldnames, contradiction_rows)
    csv_dump(output_dir / "paper_safe_asset_map.csv", paper_asset_fieldnames, paper_asset_rows)
    csv_dump(output_dir / "transport_status_counts.csv", ["variable_family", "scrutiny_status", "row_count"], status_count_rows)

    write_readme(output_dir, claim_rows, contradiction_rows, paper_asset_rows, args)

    summary = {
        "generated_at": iso_timestamp(),
        "package_count": len(packages),
        "package_dirs": [str(item["package_dir"]) for item in packages],
        "inputs": {
            "package_index_csv": str(Path(args.package_index_csv).resolve()),
            "representative_summary": str(representative_summary),
            "field_campaign_summary": str(field_campaign_summary),
            "all_runs_summary": str(all_runs_summary),
            "math_reference": str(Path(args.math_reference).resolve()),
            "interpretation_readme": str(Path(args.interpretation_readme).resolve()),
        },
        "artifacts": {
            "transport_claim_matrix_csv": str(output_dir / "transport_claim_matrix.csv"),
            "transport_contradiction_log_csv": str(output_dir / "transport_contradiction_log.csv"),
            "paper_safe_asset_map_csv": str(output_dir / "paper_safe_asset_map.csv"),
            "transport_status_counts_csv": str(output_dir / "transport_status_counts.csv"),
        },
        "figure_paths": {
            "branch_heatmap": branch_heatmap_paths,
            "hydraulic_agreement": hydraulic_agreement_paths,
            "thermal_qc": thermal_qc_paths,
        },
        "status_counts": summarize_status_counts(claim_rows),
        "code_fix_contradiction_count": sum(1 for row in contradiction_rows if str(row["requires_code_fix"]) == "yes"),
    }
    json_dump(output_dir / "summary.json", summary)


if __name__ == "__main__":
    main()
