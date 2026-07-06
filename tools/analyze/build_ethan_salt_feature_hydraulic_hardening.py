#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp, json_dump
from tools.analyze.ethan_salt_hardening_common import (
    FEATURE_CLASS_MAP,
    MODEL_DEPENDENCY_V1_DIR,
    SALT_CLOSURE_DIR,
    CaseContext,
    build_dimensionless_bundle,
    csv_dump_rows,
    filter_salt_rows,
    finite_float,
    load_case_contexts,
    load_csv_rows,
    local_side_support_mean,
    normalized_residual,
    require_columns,
    safe_mean,
)

DEFAULT_OUTPUT_DIR = Path("reports/2026-06-19_ethan_salt_feature_hydraulic_hardening")
BOUNDARY_BIN_COUNT = 3
SUPPORT_FRACTION_MIN = 2.0 / 3.0
POSITIVE_TIME_FRACTION_MIN = 0.75
FEATURE_CASE_COLUMNS = [
    "source_id",
    "case_label",
    "case_order",
    "feature_name",
    "feature_class",
    "adjacent_major_spans",
    "reference_length_m",
    "mean_abs_delta_p_rgh_pa",
    "mean_delta_p_pa",
    "mean_hydro_proxy_p_minus_prgh_pa",
    "mean_local_boundary_reference_dp_pa",
    "mean_existing_span_reference_dp_pa",
    "mean_reference_method_gap_fraction",
    "mean_feature_excess_dp_local_pa",
    "mean_feature_excess_dp_existing_pa",
    "mean_dynamic_head_local_pa",
    "mean_keff_effective_local",
    "mean_re_effective",
    "mean_property_temperature_k",
    "mean_rho_effective_kg_m3",
    "mean_bulk_velocity_m_s",
    "mean_hydraulic_diameter_geom_m",
    "positive_time_fraction",
    "local_support_fraction_min",
    "local_support_fraction_mean",
    "warning_fraction",
    "fit_use_status",
    "exclusion_reason_primary",
    "exclusion_reasons_json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an additive Salt-only feature hydraulic hardening package from the "
            "preserved June 15 live case-analysis artifacts."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--source-id",
        action="append",
        dest="source_ids",
        help="Optional bounded rebuild of one or more Salt source IDs.",
    )
    parser.add_argument(
        "--boundary-bin-count",
        type=int,
        default=BOUNDARY_BIN_COUNT,
        help="Number of nearest finite major-span bins to use on each side of a feature.",
    )
    return parser.parse_args()


def feature_class(feature_name: str) -> str:
    return FEATURE_CLASS_MAP.get(feature_name, "unclassified_feature")


def load_feature_inputs(source_ids: set[str] | None = None) -> dict[tuple[str, str], dict[str, str]]:
    rows = filter_salt_rows(load_csv_rows(SALT_CLOSURE_DIR / "salt_feature_correlation_inputs.csv"), source_ids)
    require_columns(rows, ["source_id", "feature_name", "adjacent_major_spans"], "salt_feature_correlation_inputs.csv")
    return {(row["source_id"], row["feature_name"]): row for row in rows}


def load_straight_fit_rows(source_ids: set[str] | None = None) -> dict[str, list[dict[str, str]]]:
    rows = filter_salt_rows(load_csv_rows(MODEL_DEPENDENCY_V1_DIR / "hydraulic_fit_ready_rows.csv"), source_ids)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["source_id"]].append(row)
    return grouped


def classify_feature_case_row(row: dict[str, Any]) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    if not math.isfinite(finite_float(row.get("mean_dynamic_head_local_pa"))) or finite_float(row.get("mean_dynamic_head_local_pa")) <= 0.0:
        reasons.append("invalid_local_dynamic_head")
    if not math.isfinite(finite_float(row.get("mean_re_effective"))) or finite_float(row.get("mean_re_effective")) <= 0.0:
        reasons.append("invalid_local_reynolds")
    if not math.isfinite(finite_float(row.get("local_support_fraction_min"))) or finite_float(row.get("local_support_fraction_min")) < SUPPORT_FRACTION_MIN:
        reasons.append("local_side_support_incomplete")
    if not math.isfinite(finite_float(row.get("positive_time_fraction"))) or finite_float(row.get("positive_time_fraction")) < POSITIVE_TIME_FRACTION_MIN:
        reasons.append("nonpositive_local_feature_excess_loss")
    if not math.isfinite(finite_float(row.get("mean_feature_excess_dp_local_pa"))) or finite_float(row.get("mean_feature_excess_dp_local_pa")) <= 0.0:
        reasons.append("nonpositive_local_feature_excess_loss")
    if reasons:
        return "excluded", reasons[0], reasons
    return "fit_used", "closure_supported", []


def assemble_feature_timeseries_rows(
    contexts: dict[str, CaseContext],
    feature_inputs: dict[tuple[str, str], dict[str, str]],
    boundary_bin_count: int,
) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for source_id, context in sorted(contexts.items(), key=lambda item: item[1].case_order):
        feature_rows = load_csv_rows(context.package_root / "feature_minor_loss_timeseries.csv")
        major_rows = load_csv_rows(context.package_root / "major_loss_cumulative_timeseries.csv")
        summary_rows = load_csv_rows(context.package_root / "major_loss_summary.csv")
        require_columns(feature_rows, ["source_id", "time_s", "feature_name", "start_patch", "end_patch", "abs_delta_p_rgh_pa", "delta_p_pa", "reference_length_m", "reference_major_dp_pa", "warning_flag"], f"{source_id}/feature_minor_loss_timeseries.csv")
        require_columns(major_rows, ["span_name", "time_s", "bin_index", "dp_major_gradient_pa_per_m", "rho_bulk_kg_m3", "bulk_velocity_m_s", "hydraulic_diameter_geom_m", "bulk_temp_fluid_area_avg_k"], f"{source_id}/major_loss_cumulative_timeseries.csv")
        require_columns(summary_rows, ["span_name", "start_patch", "end_patch"], f"{source_id}/major_loss_summary.csv")
        span_patch_map = {row["span_name"]: row for row in summary_rows}
        bins_by_span_time: dict[tuple[str, float], list[dict[str, str]]] = defaultdict(list)
        for row in major_rows:
            bins_by_span_time[(row["span_name"], float(row["time_s"]))].append(row)
        for key in list(bins_by_span_time):
            bins_by_span_time[key].sort(key=lambda row: int(row["bin_index"]))

        for row in feature_rows:
            feature_name = row["feature_name"]
            feature_input = feature_inputs[(source_id, feature_name)]
            adjacent_major_spans = tuple(part.strip() for part in feature_input["adjacent_major_spans"].split("|") if part.strip())
            time_s = float(row["time_s"])
            side_payloads: list[dict[str, Any]] = []
            for side_name, patch_name in (("start", row["start_patch"]), ("end", row["end_patch"])):
                matched_span = ""
                gradient_value = math.nan
                support_count = 0
                chosen_rows: list[dict[str, str]] = []
                for span_name in adjacent_major_spans:
                    span_summary = span_patch_map.get(span_name)
                    if span_summary is None:
                        continue
                    span_rows = bins_by_span_time.get((span_name, time_s), [])
                    if not span_rows:
                        continue
                    if patch_name == span_summary["start_patch"]:
                        gradient_value, support_count, chosen_rows = local_side_support_mean(
                            span_rows,
                            from_start=True,
                            value_key="dp_major_gradient_pa_per_m",
                            count=boundary_bin_count,
                        )
                    elif patch_name == span_summary["end_patch"]:
                        gradient_value, support_count, chosen_rows = local_side_support_mean(
                            span_rows,
                            from_start=False,
                            value_key="dp_major_gradient_pa_per_m",
                            count=boundary_bin_count,
                        )
                    else:
                        continue
                    matched_span = span_name
                    if chosen_rows:
                        break
                side_payloads.append(
                    {
                        "side_name": side_name,
                        "patch_name": patch_name,
                        "matched_span": matched_span,
                        "gradient_pa_per_m": gradient_value,
                        "support_count": support_count,
                        "rho_bulk_kg_m3": safe_mean(finite_float(item.get("rho_bulk_kg_m3")) for item in chosen_rows),
                        "bulk_velocity_m_s": safe_mean(finite_float(item.get("bulk_velocity_m_s")) for item in chosen_rows),
                        "hydraulic_diameter_geom_m": safe_mean(finite_float(item.get("hydraulic_diameter_geom_m")) for item in chosen_rows),
                        "bulk_temp_k": safe_mean(finite_float(item.get("bulk_temp_fluid_area_avg_k")) for item in chosen_rows),
                    }
                )

            start_side, end_side = side_payloads
            reference_length_m = finite_float(row.get("reference_length_m"))
            local_boundary_reference_dp_pa = math.nan
            if math.isfinite(reference_length_m) and all(math.isfinite(finite_float(side["gradient_pa_per_m"])) for side in side_payloads):
                local_boundary_reference_dp_pa = 0.5 * reference_length_m * sum(finite_float(side["gradient_pa_per_m"]) for side in side_payloads)
            abs_delta_p_rgh_pa = finite_float(row.get("abs_delta_p_rgh_pa"))
            delta_p_pa = finite_float(row.get("delta_p_pa"))
            hydro_proxy = abs(delta_p_pa - finite_float(row.get("delta_p_rgh_pa"))) if math.isfinite(delta_p_pa) and math.isfinite(finite_float(row.get("delta_p_rgh_pa"))) else math.nan
            existing_reference_dp_pa = finite_float(row.get("reference_major_dp_pa"))
            feature_excess_dp_local_pa = abs_delta_p_rgh_pa - local_boundary_reference_dp_pa if math.isfinite(abs_delta_p_rgh_pa) and math.isfinite(local_boundary_reference_dp_pa) else math.nan
            feature_excess_dp_existing_pa = abs_delta_p_rgh_pa - existing_reference_dp_pa if math.isfinite(abs_delta_p_rgh_pa) and math.isfinite(existing_reference_dp_pa) else math.nan
            boundary_support_fraction = min(start_side["support_count"], end_side["support_count"]) / max(boundary_bin_count, 1)
            bulk_temp_k = safe_mean(finite_float(side["bulk_temp_k"]) for side in side_payloads)
            velocity_m_s = safe_mean(finite_float(side["bulk_velocity_m_s"]) for side in side_payloads)
            dh_m = safe_mean(finite_float(side["hydraulic_diameter_geom_m"]) for side in side_payloads)
            rho_local = safe_mean(finite_float(side["rho_bulk_kg_m3"]) for side in side_payloads)
            dynamic_head_local_pa = 0.5 * rho_local * velocity_m_s * velocity_m_s if all(math.isfinite(v) for v in (rho_local, velocity_m_s)) else math.nan
            dimensionless = build_dimensionless_bundle(
                context=context,
                bulk_temp_k=bulk_temp_k,
                velocity_m_s=velocity_m_s,
                dh_m=dh_m,
                htc_w_m2_k=0.0,
                convention="branch_bulk",
            )
            keff_local = feature_excess_dp_local_pa / dynamic_head_local_pa if math.isfinite(feature_excess_dp_local_pa) and math.isfinite(dynamic_head_local_pa) and dynamic_head_local_pa > 0.0 else math.nan
            reference_gap_fraction = normalized_residual(local_boundary_reference_dp_pa - existing_reference_dp_pa, local_boundary_reference_dp_pa)
            rows_out.append(
                {
                    "source_id": source_id,
                    "case_label": context.display_label,
                    "case_order": context.case_order,
                    "feature_name": feature_name,
                    "feature_class": feature_class(feature_name),
                    "adjacent_major_spans": "|".join(adjacent_major_spans),
                    "time_s": time_s,
                    "reference_length_m": reference_length_m,
                    "raw_delta_p_pa": delta_p_pa,
                    "raw_abs_delta_p_rgh_pa": abs_delta_p_rgh_pa,
                    "hydro_proxy_p_minus_prgh_pa": hydro_proxy,
                    "existing_span_reference_dp_pa": existing_reference_dp_pa,
                    "local_boundary_reference_dp_pa": local_boundary_reference_dp_pa,
                    "reference_method_gap_fraction": reference_gap_fraction,
                    "feature_excess_dp_local_pa": feature_excess_dp_local_pa,
                    "feature_excess_dp_existing_pa": feature_excess_dp_existing_pa,
                    "dynamic_head_local_pa": dynamic_head_local_pa,
                    "keff_effective_local": keff_local,
                    "support_fraction": boundary_support_fraction,
                    "start_side_span": start_side["matched_span"],
                    "start_side_gradient_pa_per_m": finite_float(start_side["gradient_pa_per_m"]),
                    "start_side_support_bin_count": start_side["support_count"],
                    "end_side_span": end_side["matched_span"],
                    "end_side_gradient_pa_per_m": finite_float(end_side["gradient_pa_per_m"]),
                    "end_side_support_bin_count": end_side["support_count"],
                    "rho_effective_kg_m3": dimensionless["rho_effective_kg_m3"],
                    "bulk_velocity_effective_m_s": velocity_m_s,
                    "hydraulic_diameter_geom_m": dh_m,
                    "property_temperature_k": dimensionless["property_temperature_k"],
                    "re_effective": dimensionless["re_effective"],
                    "warning_flag": row.get("warning_flag", ""),
                    "warning_note": row.get("note", ""),
                }
            )
    return rows_out


def aggregate_feature_case_rows(timeseries_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in timeseries_rows:
        grouped[(row["source_id"], row["feature_name"])].append(row)
    case_rows: list[dict[str, Any]] = []
    for (source_id, feature_name), payload in sorted(grouped.items(), key=lambda item: (payload_sort_key(item[1][0]), item[0][1])):
        summary = {
            "source_id": source_id,
            "case_label": payload[0]["case_label"],
            "case_order": payload[0]["case_order"],
            "feature_name": feature_name,
            "feature_class": payload[0]["feature_class"],
            "adjacent_major_spans": payload[0]["adjacent_major_spans"],
            "reference_length_m": safe_mean(finite_float(row.get("reference_length_m")) for row in payload),
            "mean_abs_delta_p_rgh_pa": safe_mean(finite_float(row.get("raw_abs_delta_p_rgh_pa")) for row in payload),
            "mean_delta_p_pa": safe_mean(finite_float(row.get("raw_delta_p_pa")) for row in payload),
            "mean_hydro_proxy_p_minus_prgh_pa": safe_mean(finite_float(row.get("hydro_proxy_p_minus_prgh_pa")) for row in payload),
            "mean_local_boundary_reference_dp_pa": safe_mean(finite_float(row.get("local_boundary_reference_dp_pa")) for row in payload),
            "mean_existing_span_reference_dp_pa": safe_mean(finite_float(row.get("existing_span_reference_dp_pa")) for row in payload),
            "mean_reference_method_gap_fraction": safe_mean(finite_float(row.get("reference_method_gap_fraction")) for row in payload),
            "mean_feature_excess_dp_local_pa": safe_mean(finite_float(row.get("feature_excess_dp_local_pa")) for row in payload),
            "mean_feature_excess_dp_existing_pa": safe_mean(finite_float(row.get("feature_excess_dp_existing_pa")) for row in payload),
            "mean_dynamic_head_local_pa": safe_mean(finite_float(row.get("dynamic_head_local_pa")) for row in payload),
            "mean_keff_effective_local": safe_mean(finite_float(row.get("keff_effective_local")) for row in payload),
            "mean_re_effective": safe_mean(finite_float(row.get("re_effective")) for row in payload),
            "mean_property_temperature_k": safe_mean(finite_float(row.get("property_temperature_k")) for row in payload),
            "mean_rho_effective_kg_m3": safe_mean(finite_float(row.get("rho_effective_kg_m3")) for row in payload),
            "mean_bulk_velocity_m_s": safe_mean(finite_float(row.get("bulk_velocity_effective_m_s")) for row in payload),
            "mean_hydraulic_diameter_geom_m": safe_mean(finite_float(row.get("hydraulic_diameter_geom_m")) for row in payload),
            "positive_time_fraction": sum(
                1 for row in payload if math.isfinite(finite_float(row.get("feature_excess_dp_local_pa"))) and finite_float(row.get("feature_excess_dp_local_pa")) > 0.0
            ) / max(len(payload), 1),
            "local_support_fraction_min": min((finite_float(row.get("support_fraction")) for row in payload), default=math.nan),
            "local_support_fraction_mean": safe_mean(finite_float(row.get("support_fraction")) for row in payload),
            "warning_fraction": sum(1 for row in payload if str(row.get("warning_flag", "")).lower() == "yes") / max(len(payload), 1),
        }
        fit_use_status, exclusion_reason_primary, reasons = classify_feature_case_row(summary)
        summary["fit_use_status"] = fit_use_status
        summary["exclusion_reason_primary"] = exclusion_reason_primary
        summary["exclusion_reasons_json"] = json.dumps(reasons)
        case_rows.append(summary)
    return case_rows


def payload_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    return int(row["case_order"]), str(row["case_label"])


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    content = f"""# Ethan Salt Feature Hydraulic Hardening

Generated: `2026-06-19`

## Purpose

This package upgrades the Salt feature-loss story beyond the residual-only June
18 audit by recomputing case-level feature excess loss from preserved patch
`p_rgh` endpoint deltas plus a local adjacent-straight reference built from the
nearest valid major-span boundary bins. It does **not** claim a full feature-path
hydro integral; that remains the explicit next upstream requirement.

## Inputs

- `tmp/2026-06-15_live_case_analysis/**/feature_minor_loss_timeseries.csv`
- `tmp/2026-06-15_live_case_analysis/**/major_loss_cumulative_timeseries.csv`
- `tmp/2026-06-15_live_case_analysis/**/major_loss_summary.csv`
- `reports/2026-06-18_ethan_salt_closure_correlation_package/salt_feature_correlation_inputs.csv`

## Output tables

- `feature_hydro_closure_timeseries.csv`
  One retained-time feature row with raw patch `p`/`p_rgh` deltas, local
  side-reference gradients, local straight-reference loss, effective `K_eff`,
  and support diagnostics.
- `feature_hydro_closure_by_case.csv`
  One case-level feature row used for downstream feature-fit gating.
- `feature_fit_ready_rows.csv`
  Case-level feature rows that survive the local-support and positive-excess
  gates.
- `feature_exclusion_summary.csv`
  Counted case-level exclusions by primary reason.
- `feature_method_comparison.csv`
  Old span-mean reference versus new local-boundary reference comparison.

## Method status

- Local pressure-loss basis: `abs(delta_p_rgh_pa)` across feature endpoint patches
- Straight-reference basis: half-feature-length times the mean of the nearest
  valid boundary-bin gradients on the start and end adjacent spans
- Deferred upstream term: explicit feature-path hydro-integral sampling

## Key counts

- case count: `{summary["case_count"]}`
- time row count: `{summary["timeseries_row_count"]}`
- case row count: `{summary["case_row_count"]}`
- fit-ready feature rows: `{summary["fit_ready_count"]}`

## Known limitations

- The new method is stronger than the residual-only June 18 feature budget, but
  it still uses patch-endpoint `p_rgh` plus local straight references rather
  than an explicit feature-path density integral.
- Positive case-level feature excess does not automatically imply a final
  publishable `K_eff`; the downstream dependency package still rechecks
  feature-class stability and sensitivity.
"""
    path.write_text(content, encoding="utf-8")


def write_math_companion(path: Path) -> None:
    content = """# Math Companion

For each retained-time feature row:

- `Delta p_feature,prgh = |p_rgh,end - p_rgh,start|`
- `g_start = mean(nearest finite boundary-bin dp_major_gradient on the start side)`
- `g_end = mean(nearest finite boundary-bin dp_major_gradient on the end side)`
- `Delta p_ref,local = 0.5 * L_feature * (g_start + g_end)`
- `Delta p_excess,local = Delta p_feature,prgh - Delta p_ref,local`
- `q_dyn = 0.5 * rho_local * U_local^2`
- `K_eff,local = Delta p_excess,local / q_dyn`

Sign convention:

- `Delta p_feature,prgh` is stored as a positive loss magnitude.
- Positive `Delta p_excess,local` means the feature patch-to-patch `p_rgh` loss
  exceeds the adjacent straight-reference estimate.
- Negative `Delta p_excess,local` is excluded from defended feature fitting.

Validity gates:

- both feature sides must resolve local boundary support
- case-level positive-time fraction must be at least `0.75`
- case-level mean excess loss must remain positive
- local dynamic head and effective Reynolds number must be finite and positive
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_ids = set(args.source_ids or []) or None
    contexts = load_case_contexts(source_ids)
    feature_inputs = load_feature_inputs(source_ids)
    timeseries_rows = assemble_feature_timeseries_rows(contexts, feature_inputs, boundary_bin_count=args.boundary_bin_count)
    case_rows = aggregate_feature_case_rows(timeseries_rows)
    fit_ready_rows = [row for row in case_rows if row["fit_use_status"] == "fit_used"]
    exclusion_counter = Counter(row["exclusion_reason_primary"] for row in case_rows if row["fit_use_status"] != "fit_used")
    output_dir = ensure_dir(Path(args.output_dir))

    timeseries_fieldnames = list(timeseries_rows[0].keys())
    case_fieldnames = list(case_rows[0].keys())
    csv_dump_rows(output_dir / "feature_hydro_closure_timeseries.csv", timeseries_rows, fieldnames=timeseries_fieldnames)
    csv_dump_rows(output_dir / "feature_hydro_closure_by_case.csv", case_rows, fieldnames=case_fieldnames)
    csv_dump_rows(output_dir / "feature_fit_ready_rows.csv", fit_ready_rows, fieldnames=case_fieldnames)
    csv_dump_rows(
        output_dir / "feature_exclusion_summary.csv",
        [
            {
                "asset_family": "feature_keff",
                "exclusion_reason_primary": reason,
                "row_count": count,
            }
            for reason, count in sorted(exclusion_counter.items())
        ],
        fieldnames=["asset_family", "exclusion_reason_primary", "row_count"],
    )
    csv_dump_rows(
        output_dir / "feature_method_comparison.csv",
        [
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "feature_name": row["feature_name"],
                "feature_class": row["feature_class"],
                "mean_abs_delta_p_rgh_pa": row["mean_abs_delta_p_rgh_pa"],
                "mean_existing_span_reference_dp_pa": row["mean_existing_span_reference_dp_pa"],
                "mean_local_boundary_reference_dp_pa": row["mean_local_boundary_reference_dp_pa"],
                "mean_reference_method_gap_fraction": row["mean_reference_method_gap_fraction"],
                "mean_feature_excess_dp_existing_pa": row["mean_feature_excess_dp_existing_pa"],
                "mean_feature_excess_dp_local_pa": row["mean_feature_excess_dp_local_pa"],
                "fit_use_status": row["fit_use_status"],
            }
            for row in case_rows
        ],
        fieldnames=[
            "source_id",
            "case_label",
            "feature_name",
            "feature_class",
            "mean_abs_delta_p_rgh_pa",
            "mean_existing_span_reference_dp_pa",
            "mean_local_boundary_reference_dp_pa",
            "mean_reference_method_gap_fraction",
            "mean_feature_excess_dp_existing_pa",
            "mean_feature_excess_dp_local_pa",
            "fit_use_status",
        ],
    )

    summary = {
        "generated_at": iso_timestamp(),
        "case_count": len(contexts),
        "timeseries_row_count": len(timeseries_rows),
        "case_row_count": len(case_rows),
        "fit_ready_count": len(fit_ready_rows),
        "feature_class_counts": dict(Counter(row["feature_class"] for row in case_rows)),
        "fit_ready_feature_name_counts": dict(Counter(row["feature_name"] for row in fit_ready_rows)),
        "boundary_bin_count": args.boundary_bin_count,
        "support_fraction_min": SUPPORT_FRACTION_MIN,
        "positive_time_fraction_min": POSITIVE_TIME_FRACTION_MIN,
    }
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir / "README.md", summary)
    write_math_companion(output_dir / "MATH_COMPANION.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
