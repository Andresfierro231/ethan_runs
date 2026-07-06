#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import csv_dump_rows, write_json
from tools.analyze.ethan_salt_hardening_common import (
    FEATURE_CLASS_MAP,
    NONDIM_DIR,
    finite_float,
    load_csv_rows,
    normalized_residual,
    require_columns,
    safe_mean,
)

FEATURE_PROXY_DIR = Path("reports/2026-06-19_ethan_salt_feature_hydraulic_hardening")
FEATURE_PROBE_DIR = Path("reports/2026-06-22_ethan_feature_path_hydro_probe")
DEFAULT_OUTPUT_DIR = Path("reports/2026-06-22_ethan_feature_path_hydro_decomposition")
SUPPORT_FRACTION_MIN = 2.0 / 3.0
POSITIVE_TIME_FRACTION_MIN = 0.75
PATCH_MATCH_TOL_PA = 1.0e-9

TIMESERIES_COLUMNS = [
    "source_id",
    "case_label",
    "case_order",
    "feature_name",
    "feature_class",
    "adjacent_major_spans",
    "time_s",
    "start_patch",
    "end_patch",
    "dp_feature_p_pa",
    "dp_feature_p_abs_pa",
    "dp_feature_prgh_pa",
    "dp_feature_prgh_abs_pa",
    "dp_feature_hydro_path_pa",
    "dp_feature_hydro_path_abs_pa",
    "proxy_raw_delta_p_pa",
    "proxy_raw_abs_delta_p_rgh_pa",
    "path_vs_proxy_delta_p_residual_pa",
    "path_vs_proxy_delta_p_rgh_residual_pa",
    "local_boundary_reference_dp_pa",
    "existing_span_reference_dp_pa",
    "feature_excess_path_pa",
    "feature_excess_existing_pa",
    "reference_method_gap_fraction",
    "dynamic_head_local_pa",
    "keff_effective_path",
    "support_fraction",
    "re_effective",
    "rho_effective_kg_m3",
    "bulk_velocity_effective_m_s",
    "hydraulic_diameter_geom_m",
    "property_temperature_k",
    "window_hydro_correction_abs_pa",
    "window_vs_path_hydro_gap_fraction",
    "pressure_method_status",
    "reference_method_status",
    "warning_flag",
    "warning_note",
]

CASE_COLUMNS = [
    "source_id",
    "case_label",
    "case_order",
    "feature_name",
    "feature_class",
    "adjacent_major_spans",
    "time_row_count",
    "defended_time_fraction",
    "positive_time_fraction",
    "support_fraction_min",
    "support_fraction_mean",
    "warning_fraction",
    "mean_abs_delta_p_pa",
    "mean_abs_delta_p_rgh_pa",
    "mean_hydro_path_abs_pa",
    "mean_proxy_window_hydro_abs_pa",
    "mean_window_vs_path_hydro_gap_fraction",
    "mean_local_boundary_reference_dp_pa",
    "mean_existing_span_reference_dp_pa",
    "mean_feature_excess_path_pa",
    "mean_feature_excess_existing_pa",
    "mean_dynamic_head_local_pa",
    "mean_keff_effective_path",
    "mean_re_effective",
    "mean_rho_effective_kg_m3",
    "mean_bulk_velocity_effective_m_s",
    "mean_hydraulic_diameter_geom_m",
    "mean_property_temperature_k",
    "pressure_method_status",
    "reference_method_status",
    "fit_use_status",
    "exclusion_reason_primary",
    "exclusion_reasons_json",
]

FEATURE_COLUMNS = [
    "feature_name",
    "feature_class",
    "case_count",
    "fit_used_case_count",
    "excluded_case_count",
    "mean_positive_time_fraction",
    "mean_support_fraction_min",
    "mean_feature_excess_path_pa",
    "mean_keff_effective_path",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a retained-time feature-path hydraulic decomposition from the "
            "preserved raw patch-pressure artifacts. The decomposition is exact on "
            "the preserved feature endpoint patches and carries forward the same "
            "local-boundary straight reference used by the June 19 Salt feature "
            "hardening package."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    return parser.parse_args()


def truthy_flag(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def unique_reason_list(reasons: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        ordered.append(reason)
    return ordered


def classify_case_row(row: dict[str, Any]) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    if finite_float(row.get("defended_time_fraction")) < 1.0:
        reasons.append("missing_patch_endpoint_pair_or_reference")
    if finite_float(row.get("support_fraction_min")) < SUPPORT_FRACTION_MIN:
        reasons.append("incomplete_feature_boundary_support")
    if finite_float(row.get("positive_time_fraction")) < POSITIVE_TIME_FRACTION_MIN:
        reasons.append("nonpositive_path_feature_excess_loss")
    if finite_float(row.get("mean_feature_excess_path_pa")) <= 0.0:
        reasons.append("nonpositive_path_feature_excess_loss")
    if finite_float(row.get("mean_dynamic_head_local_pa")) <= 0.0:
        reasons.append("invalid_local_dynamic_head")
    if finite_float(row.get("mean_re_effective")) <= 0.0:
        reasons.append("invalid_local_reynolds")
    reasons = unique_reason_list(reasons)
    if reasons:
        return "excluded", reasons[0], reasons
    return "fit_used", "closure_supported", []


def load_proxy_lookup(source_ids: set[str] | None) -> dict[tuple[str, str, float], dict[str, str]]:
    rows = load_csv_rows(FEATURE_PROXY_DIR / "feature_hydro_closure_timeseries.csv")
    require_columns(
        rows,
        [
            "source_id",
            "feature_name",
            "time_s",
            "adjacent_major_spans",
            "raw_delta_p_pa",
            "raw_abs_delta_p_rgh_pa",
            "existing_span_reference_dp_pa",
            "local_boundary_reference_dp_pa",
            "reference_method_gap_fraction",
            "feature_excess_dp_local_pa",
            "feature_excess_dp_existing_pa",
            "dynamic_head_local_pa",
            "keff_effective_local",
            "support_fraction",
            "rho_effective_kg_m3",
            "bulk_velocity_effective_m_s",
            "hydraulic_diameter_geom_m",
            "property_temperature_k",
            "re_effective",
            "warning_flag",
            "warning_note",
        ],
        "feature_hydro_closure_timeseries.csv",
    )
    lookup: dict[tuple[str, str, float], dict[str, str]] = {}
    for row in rows:
        if source_ids and row["source_id"] not in source_ids:
            continue
        lookup[(row["source_id"], row["feature_name"], finite_float(row["time_s"]))] = row
    return lookup


def load_probe_lookup(source_ids: set[str] | None) -> dict[tuple[str, str, float], dict[str, str]]:
    rows = load_csv_rows(FEATURE_PROBE_DIR / "feature_path_hydro_probe_timeseries.csv")
    require_columns(
        rows,
        [
            "source_id",
            "feature_name",
            "time_s",
            "window_hydro_correction_abs_pa",
            "hydro_probe_gap_vs_endpoint_fraction",
        ],
        "feature_path_hydro_probe_timeseries.csv",
    )
    lookup: dict[tuple[str, str, float], dict[str, str]] = {}
    for row in rows:
        if source_ids and row["source_id"] not in source_ids:
            continue
        lookup[(row["source_id"], row["feature_name"], finite_float(row["time_s"]))] = row
    return lookup


def load_case_roots(source_ids: set[str] | None) -> list[dict[str, Any]]:
    rows = load_csv_rows(NONDIM_DIR / "salt_dashboard.csv")
    require_columns(rows, ["source_id", "display_label", "package_root"], "salt_dashboard.csv")
    payload: list[dict[str, Any]] = []
    for order, row in enumerate(rows):
        if source_ids and row["source_id"] not in source_ids:
            continue
        package_root = Path(row["package_root"])
        if not package_root.exists():
            continue
        payload.append(
            {
                "source_id": row["source_id"],
                "case_label": row["display_label"],
                "case_order": order,
                "package_root": package_root,
            }
        )
    if not payload:
        raise RuntimeError("no Salt case roots resolved from salt_dashboard.csv")
    return payload


def build_path_timeseries_rows(source_ids: set[str] | None) -> list[dict[str, Any]]:
    contexts = load_case_roots(source_ids)
    proxy_lookup = load_proxy_lookup(source_ids)
    probe_lookup = load_probe_lookup(source_ids)
    rows_out: list[dict[str, Any]] = []
    for context in contexts:
        source_id = str(context["source_id"])
        patch_rows = load_csv_rows(Path(context["package_root"]) / "raw_extraction" / "feature_patch_pressure_timeseries.csv")
        require_columns(
            patch_rows,
            [
                "source_id",
                "time_s",
                "feature_name",
                "patch_role",
                "patch_name",
                "adjacent_major_spans",
                "p_pa",
                "p_rgh_pa",
                "warning_flag",
                "note",
            ],
            f"{source_id}/feature_patch_pressure_timeseries.csv",
        )
        grouped: dict[tuple[str, float], list[dict[str, str]]] = defaultdict(list)
        for row in patch_rows:
            grouped[(row["feature_name"], finite_float(row["time_s"]))].append(row)
        for (feature_name, time_s), group in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
            start_row = next((row for row in group if row["patch_role"] == "start"), None)
            end_row = next((row for row in group if row["patch_role"] == "end"), None)
            proxy_row = proxy_lookup.get((source_id, feature_name, time_s))
            probe_row = probe_lookup.get((source_id, feature_name, time_s))
            pressure_method_status = "defended_patch_endpoint_prgh_local_boundary_reference"
            reference_method_status = "adjacent_major_span_local_boundary_gradients"
            warning_parts: list[str] = []
            if start_row is None or end_row is None:
                pressure_method_status = "blocked_missing_patch_endpoint_pair"
            if proxy_row is None:
                pressure_method_status = "blocked_missing_local_boundary_reference"
            if pressure_method_status.startswith("blocked"):
                reference_method_status = "missing_reference"

            delta_p = math.nan
            delta_p_rgh = math.nan
            delta_p_abs = math.nan
            delta_p_rgh_abs = math.nan
            hydro_signed = math.nan
            hydro_abs = math.nan
            start_patch = ""
            end_patch = ""
            adjacent_major_spans = ""
            warning_flag = "yes"
            warning_note = ""
            if start_row is not None and end_row is not None:
                start_patch = start_row["patch_name"]
                end_patch = end_row["patch_name"]
                adjacent_major_spans = start_row.get("adjacent_major_spans", end_row.get("adjacent_major_spans", ""))
                delta_p = finite_float(end_row.get("p_pa")) - finite_float(start_row.get("p_pa"))
                delta_p_rgh = finite_float(end_row.get("p_rgh_pa")) - finite_float(start_row.get("p_rgh_pa"))
                delta_p_abs = abs(delta_p)
                delta_p_rgh_abs = abs(delta_p_rgh)
                hydro_signed = delta_p - delta_p_rgh
                hydro_abs = abs(hydro_signed)
                if truthy_flag(start_row.get("warning_flag", "")) or truthy_flag(end_row.get("warning_flag", "")):
                    warning_parts.append("raw_patch_warning")
                for note in (start_row.get("note", ""), end_row.get("note", "")):
                    if note:
                        warning_parts.append(note)
            if proxy_row is not None:
                adjacent_major_spans = proxy_row.get("adjacent_major_spans", adjacent_major_spans)
                if truthy_flag(proxy_row.get("warning_flag", "")):
                    warning_parts.append("proxy_row_warning")
                if proxy_row.get("warning_note"):
                    warning_parts.append(proxy_row["warning_note"])

            local_reference = finite_float(proxy_row.get("local_boundary_reference_dp_pa") if proxy_row else math.nan)
            existing_reference = finite_float(proxy_row.get("existing_span_reference_dp_pa") if proxy_row else math.nan)
            feature_excess_path = (
                delta_p_rgh_abs - local_reference
                if math.isfinite(delta_p_rgh_abs) and math.isfinite(local_reference)
                else math.nan
            )
            feature_excess_existing = (
                delta_p_rgh_abs - existing_reference
                if math.isfinite(delta_p_rgh_abs) and math.isfinite(existing_reference)
                else math.nan
            )
            dynamic_head = finite_float(proxy_row.get("dynamic_head_local_pa") if proxy_row else math.nan)
            keff = (
                feature_excess_path / dynamic_head
                if math.isfinite(feature_excess_path) and math.isfinite(dynamic_head) and dynamic_head > 0.0
                else math.nan
            )
            proxy_delta_p = finite_float(proxy_row.get("raw_delta_p_pa") if proxy_row else math.nan)
            proxy_abs_prgh = finite_float(proxy_row.get("raw_abs_delta_p_rgh_pa") if proxy_row else math.nan)
            delta_p_residual = delta_p - proxy_delta_p if math.isfinite(delta_p) and math.isfinite(proxy_delta_p) else math.nan
            delta_p_rgh_residual = delta_p_rgh_abs - proxy_abs_prgh if math.isfinite(delta_p_rgh_abs) and math.isfinite(proxy_abs_prgh) else math.nan
            if math.isfinite(delta_p_residual) and abs(delta_p_residual) > PATCH_MATCH_TOL_PA:
                warning_parts.append("path_delta_p_mismatch_vs_proxy")
            if math.isfinite(delta_p_rgh_residual) and abs(delta_p_rgh_residual) > PATCH_MATCH_TOL_PA:
                warning_parts.append("path_delta_p_rgh_mismatch_vs_proxy")
            gap_fraction = normalized_residual(
                finite_float(probe_row.get("window_hydro_correction_abs_pa") if probe_row else math.nan) - hydro_abs,
                hydro_abs,
            )

            if warning_parts:
                warning_flag = "yes"
                warning_note = "; ".join(part for part in warning_parts if part)
            else:
                warning_flag = "no"

            rows_out.append(
                {
                    "source_id": source_id,
                    "case_label": context["case_label"],
                    "case_order": context["case_order"],
                    "feature_name": feature_name,
                    "feature_class": FEATURE_CLASS_MAP.get(feature_name, "unclassified_feature"),
                    "adjacent_major_spans": adjacent_major_spans,
                    "time_s": time_s,
                    "start_patch": start_patch,
                    "end_patch": end_patch,
                    "dp_feature_p_pa": delta_p,
                    "dp_feature_p_abs_pa": delta_p_abs,
                    "dp_feature_prgh_pa": delta_p_rgh,
                    "dp_feature_prgh_abs_pa": delta_p_rgh_abs,
                    "dp_feature_hydro_path_pa": hydro_signed,
                    "dp_feature_hydro_path_abs_pa": hydro_abs,
                    "proxy_raw_delta_p_pa": proxy_delta_p,
                    "proxy_raw_abs_delta_p_rgh_pa": proxy_abs_prgh,
                    "path_vs_proxy_delta_p_residual_pa": delta_p_residual,
                    "path_vs_proxy_delta_p_rgh_residual_pa": delta_p_rgh_residual,
                    "local_boundary_reference_dp_pa": local_reference,
                    "existing_span_reference_dp_pa": existing_reference,
                    "feature_excess_path_pa": feature_excess_path,
                    "feature_excess_existing_pa": feature_excess_existing,
                    "reference_method_gap_fraction": finite_float(proxy_row.get("reference_method_gap_fraction") if proxy_row else math.nan),
                    "dynamic_head_local_pa": dynamic_head,
                    "keff_effective_path": keff,
                    "support_fraction": finite_float(proxy_row.get("support_fraction") if proxy_row else math.nan),
                    "re_effective": finite_float(proxy_row.get("re_effective") if proxy_row else math.nan),
                    "rho_effective_kg_m3": finite_float(proxy_row.get("rho_effective_kg_m3") if proxy_row else math.nan),
                    "bulk_velocity_effective_m_s": finite_float(proxy_row.get("bulk_velocity_effective_m_s") if proxy_row else math.nan),
                    "hydraulic_diameter_geom_m": finite_float(proxy_row.get("hydraulic_diameter_geom_m") if proxy_row else math.nan),
                    "property_temperature_k": finite_float(proxy_row.get("property_temperature_k") if proxy_row else math.nan),
                    "window_hydro_correction_abs_pa": finite_float(probe_row.get("window_hydro_correction_abs_pa") if probe_row else math.nan),
                    "window_vs_path_hydro_gap_fraction": gap_fraction,
                    "pressure_method_status": pressure_method_status,
                    "reference_method_status": reference_method_status,
                    "warning_flag": warning_flag,
                    "warning_note": warning_note,
                }
            )
    return rows_out


def aggregate_case_rows(time_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in time_rows:
        grouped[(row["source_id"], row["feature_name"])].append(row)
    rows_out: list[dict[str, Any]] = []
    for (_source_id, _feature_name), group in sorted(grouped.items(), key=lambda item: (item[0][0], item[1][0]["case_order"], item[0][1])):
        sample = group[0]
        defended_fraction = sum(
            1 for row in group if row["pressure_method_status"] == "defended_patch_endpoint_prgh_local_boundary_reference"
        ) / max(len(group), 1)
        positive_fraction = sum(
            1 for row in group if finite_float(row.get("feature_excess_path_pa")) > 0.0
        ) / max(len(group), 1)
        warning_fraction = sum(1 for row in group if truthy_flag(row.get("warning_flag", ""))) / max(len(group), 1)
        case_row = {
            "source_id": sample["source_id"],
            "case_label": sample["case_label"],
            "case_order": sample["case_order"],
            "feature_name": sample["feature_name"],
            "feature_class": sample["feature_class"],
            "adjacent_major_spans": sample["adjacent_major_spans"],
            "time_row_count": len(group),
            "defended_time_fraction": defended_fraction,
            "positive_time_fraction": positive_fraction,
            "support_fraction_min": min(finite_float(row.get("support_fraction")) for row in group),
            "support_fraction_mean": safe_mean(finite_float(row.get("support_fraction")) for row in group),
            "warning_fraction": warning_fraction,
            "mean_abs_delta_p_pa": safe_mean(finite_float(row.get("dp_feature_p_abs_pa")) for row in group),
            "mean_abs_delta_p_rgh_pa": safe_mean(finite_float(row.get("dp_feature_prgh_abs_pa")) for row in group),
            "mean_hydro_path_abs_pa": safe_mean(finite_float(row.get("dp_feature_hydro_path_abs_pa")) for row in group),
            "mean_proxy_window_hydro_abs_pa": safe_mean(finite_float(row.get("window_hydro_correction_abs_pa")) for row in group),
            "mean_window_vs_path_hydro_gap_fraction": safe_mean(finite_float(row.get("window_vs_path_hydro_gap_fraction")) for row in group),
            "mean_local_boundary_reference_dp_pa": safe_mean(finite_float(row.get("local_boundary_reference_dp_pa")) for row in group),
            "mean_existing_span_reference_dp_pa": safe_mean(finite_float(row.get("existing_span_reference_dp_pa")) for row in group),
            "mean_feature_excess_path_pa": safe_mean(finite_float(row.get("feature_excess_path_pa")) for row in group),
            "mean_feature_excess_existing_pa": safe_mean(finite_float(row.get("feature_excess_existing_pa")) for row in group),
            "mean_dynamic_head_local_pa": safe_mean(finite_float(row.get("dynamic_head_local_pa")) for row in group),
            "mean_keff_effective_path": safe_mean(finite_float(row.get("keff_effective_path")) for row in group),
            "mean_re_effective": safe_mean(finite_float(row.get("re_effective")) for row in group),
            "mean_rho_effective_kg_m3": safe_mean(finite_float(row.get("rho_effective_kg_m3")) for row in group),
            "mean_bulk_velocity_effective_m_s": safe_mean(finite_float(row.get("bulk_velocity_effective_m_s")) for row in group),
            "mean_hydraulic_diameter_geom_m": safe_mean(finite_float(row.get("hydraulic_diameter_geom_m")) for row in group),
            "mean_property_temperature_k": safe_mean(finite_float(row.get("property_temperature_k")) for row in group),
            "pressure_method_status": "defended_patch_endpoint_prgh_local_boundary_reference"
            if defended_fraction == 1.0
            else "partial_patch_endpoint_support",
            "reference_method_status": sample["reference_method_status"],
        }
        fit_use_status, exclusion_reason_primary, exclusion_reasons = classify_case_row(case_row)
        case_row["fit_use_status"] = fit_use_status
        case_row["exclusion_reason_primary"] = exclusion_reason_primary
        case_row["exclusion_reasons_json"] = json.dumps(exclusion_reasons)
        rows_out.append(case_row)
    return rows_out


def aggregate_feature_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        grouped[row["feature_name"]].append(row)
    rows_out: list[dict[str, Any]] = []
    for feature_name, group in sorted(grouped.items()):
        rows_out.append(
            {
                "feature_name": feature_name,
                "feature_class": group[0]["feature_class"],
                "case_count": len(group),
                "fit_used_case_count": sum(1 for row in group if row["fit_use_status"] == "fit_used"),
                "excluded_case_count": sum(1 for row in group if row["fit_use_status"] == "excluded"),
                "mean_positive_time_fraction": safe_mean(finite_float(row.get("positive_time_fraction")) for row in group),
                "mean_support_fraction_min": safe_mean(finite_float(row.get("support_fraction_min")) for row in group),
                "mean_feature_excess_path_pa": safe_mean(finite_float(row.get("mean_feature_excess_path_pa")) for row in group),
                "mean_keff_effective_path": safe_mean(finite_float(row.get("mean_keff_effective_path")) for row in group),
            }
        )
    return rows_out


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None
    time_rows = build_path_timeseries_rows(source_ids)
    case_rows = aggregate_case_rows(time_rows)
    feature_rows = aggregate_feature_rows(case_rows)

    output_dir = ensure_dir(Path(args.output_dir))
    csv_dump_rows(output_dir / "feature_path_timeseries.csv", time_rows, TIMESERIES_COLUMNS)
    csv_dump_rows(output_dir / "feature_path_case_summary.csv", case_rows, CASE_COLUMNS)
    csv_dump_rows(output_dir / "feature_path_feature_summary.csv", feature_rows, FEATURE_COLUMNS)

    summary = {
        "generated_at": iso_timestamp(),
        "source_case_count": len({row["source_id"] for row in case_rows}),
        "feature_case_row_count": len(case_rows),
        "feature_time_row_count": len(time_rows),
        "fit_ready_case_row_count": sum(1 for row in case_rows if row["fit_use_status"] == "fit_used"),
        "pressure_method_status_counts": Counter(row["pressure_method_status"] for row in case_rows),
        "fit_status_counts": Counter(row["fit_use_status"] for row in case_rows),
        "max_path_vs_proxy_delta_p_residual_pa": max(
            (abs(finite_float(row.get("path_vs_proxy_delta_p_residual_pa"))) for row in time_rows if math.isfinite(finite_float(row.get("path_vs_proxy_delta_p_residual_pa")))),
            default=math.nan,
        ),
        "max_path_vs_proxy_delta_p_rgh_residual_pa": max(
            (abs(finite_float(row.get("path_vs_proxy_delta_p_rgh_residual_pa"))) for row in time_rows if math.isfinite(finite_float(row.get("path_vs_proxy_delta_p_rgh_residual_pa")))),
            default=math.nan,
        ),
    }
    write_json(output_dir / "summary.json", summary)

    readme = f"""# Ethan Feature-Path Hydro Decomposition

Generated: `2026-06-22`

## Purpose

This package freezes the current retained-time feature-path hydraulic signal in
the strongest additive form the repo already preserves:

- exact endpoint-patch `p` and `p_rgh` differences from
  `raw_extraction/feature_patch_pressure_timeseries.csv`
- the existing same-boundary local straight reference from the June 19 Salt
  feature hardening package
- the June 22 wall-window hydro probe as a comparison surface rather than the
  primary decomposition

## Current outcome

- feature case rows: `{len(case_rows)}`
- fit-ready case rows: `{summary["fit_ready_case_row_count"]}`
- dominant method status: `defended_patch_endpoint_prgh_local_boundary_reference`

## Interpretation boundary

This package **does** defend the patch-endpoint path decomposition:

- `dp_feature_prgh_pa` is taken directly from the preserved patch endpoints
- `dp_feature_hydro_path_pa = dp_feature_p_pa - dp_feature_prgh_pa`

It still does **not** claim a continuous field-integrated density path. The
straight subtraction remains the local-boundary gradient reference already used
in the June 19 feature package. That is enough to reopen the feature hardening
lane, but not enough to claim a new CFD observable has been extracted.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    math_note = """# Math Companion

For each retained feature time:

- `dp_feature_p_pa = p_end - p_start`
- `dp_feature_prgh_pa = p_rgh,end - p_rgh,start`
- `dp_feature_hydro_path_pa = dp_feature_p_pa - dp_feature_prgh_pa`
- `dp_feature_prgh_abs_pa = |dp_feature_prgh_pa|`
- `feature_excess_path_pa = |dp_feature_prgh_pa| - local_boundary_reference_dp_pa`
- `keff_effective_path = feature_excess_path_pa / dynamic_head_local_pa`

The path decomposition is exact with respect to the preserved patch extractor.
The `path_vs_proxy_*_residual_pa` fields are a provenance cross-check against
the June 19 feature hardening package and should remain numerically zero within
floating-point noise.

The wall-window hydro probe remains useful only as a sensitivity comparison:

- `window_hydro_correction_abs_pa`
- `window_vs_path_hydro_gap_fraction`

Those fields quantify how much the June 22 wall-window hydro surrogate differs
from the exact patch-endpoint path decomposition.
"""
    (output_dir / "MATH_COMPANION.md").write_text(math_note, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
