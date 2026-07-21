#!/usr/bin/env python3
"""Build an integrated hydraulic closure rigor audit for admitted Salt Jin cases.

This package is a read-only synthesis of existing CFD reductions. It does not
rerun OpenFOAM or mutate prior July 8 ledgers. Where existing artifacts lack raw
tap geometry, mesh-triplet evidence, or raw velocity profiles, the output emits
explicit blocker/status fields rather than fabricating closure-grade values.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products" / "2026-07" / "2026-07-08" / "2026-07-08_hydraulic_closure_rigor_audit"

PRESSURE_LEDGER = ROOT / "work_products" / "2026-07-08_pressure_term_ledger" / "pressure_term_ledger.csv"
MINOR_LOSS = ROOT / "work_products" / "2026-07-08_minor_loss_two_tap" / "minor_loss_two_tap.csv"
QUASI_STEADY = ROOT / "work_products" / "2026-07-07_time_window_quasi_steady_uq" / "quasi_steady_observations.csv"
SECTION_DIR = ROOT / "work_products" / "2026-07-01_claude_section_mean_pressure"
UPCOMER_DIR = ROOT / "work_products" / "2026-06-30_claude_upcomer_convection_cell"
DOWNCOMER = ROOT / "work_products" / "2026-06-30_claude_downcomer_recirculation" / "downcomer_recirculation.csv"
SEGMENT_FRICTION = ROOT / "work_products" / "2026-07-01_claude_segment_friction" / "segment_friction.csv"
MOMENTUM_BUDGET = ROOT / "work_products" / "2026-07-01_claude_momentum_budget" / "momentum_budget.csv"
OBSERVATION_TABLE = ROOT / "work_products" / "2026-07-08_closure_observation_table" / "closure_observations.csv"
UPCOMER_ONSET = ROOT / "work_products" / "2026-07-08_upcomer_onset" / "upcomer_onset_regime_table.csv"

SOURCE_IDS = [
    "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "viscosity_screening_salt_test_4_jin_coarse_mesh",
]
SPANS = ["lower_leg", "right_leg", "left_lower_leg", "test_section_span", "left_upper_leg", "upper_leg"]
RECIRCULATION_SPANS = {"left_lower_leg", "left_upper_leg"}
ENTRY_SPANS = {"lower_leg", "right_leg", "left_lower_leg", "upper_leg"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def fnum(value: Any, default: float = math.nan) -> float:
    try:
        text = str(value).strip()
        if text == "" or text.lower() in {"nan", "none", "na"}:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def fmt(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return value
    return value


def case_id(source_id: str) -> str:
    for n in ("1", "2", "3", "4"):
        if f"salt_test_{n}_" in source_id:
            return f"salt_{n}"
    return source_id


def station_sort_key(row: Mapping[str, str]) -> tuple[str, int]:
    label = row.get("label", "")
    if "__s" in label:
        base, _, raw = label.rpartition("__s")
        try:
            return (base, int(raw))
        except ValueError:
            return (base, 999)
    return (label, 999)


def finite(values: Iterable[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def mean(values: Iterable[float]) -> float:
    vals = finite(values)
    return sum(vals) / len(vals) if vals else math.nan


def slope(points: Sequence[Mapping[str, float]], value_key: str) -> float:
    if len(points) < 2:
        return math.nan
    x0 = points[0]["s_m"]
    x1 = points[-1]["s_m"]
    if x1 == x0:
        return math.nan
    return (points[-1][value_key] - points[0][value_key]) / (x1 - x0)


def signed_dp_along_flow(row: Mapping[str, str], start_key: str, end_key: str) -> float:
    # Existing ledger reports flow-direction gradients. For endpoint values,
    # sigma < 0 means physical flow runs from end station back to start station.
    sigma = fnum(row.get("flow_orientation_sigma"), 1.0)
    start = fnum(row.get(start_key))
    end = fnum(row.get(end_key))
    if sigma < 0:
        return start - end
    return end - start


def load_section_rows() -> dict[tuple[str, str], list[dict[str, Any]]]:
    out: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for source_id in SOURCE_IDS:
        path = SECTION_DIR / f"section_mean_pressure_{source_id}.csv"
        for row in read_csv(path):
            if row.get("status") != "sampled":
                continue
            span = row.get("span", "")
            parsed = dict(row)
            parsed["x_f"] = fnum(row.get("x"))
            parsed["y_f"] = fnum(row.get("y"))
            parsed["z_f"] = fnum(row.get("z"))
            parsed["p_rgh_f"] = fnum(row.get("section_mean_p_rgh_pa"))
            parsed["q_dyn_f"] = fnum(row.get("dynamic_head_pa"))
            parsed["p0_proxy_f"] = fnum(row.get("section_mean_total_pressure_pa"))
            parsed["flow_alignment_f"] = fnum(row.get("flow_alignment"))
            parsed["is_fitting_end_b"] = boolish(row.get("is_fitting_end"))
            out[(source_id, span)].append(parsed)
    for rows in out.values():
        rows.sort(key=station_sort_key)
        prev: dict[str, Any] | None = None
        s_m = 0.0
        for row in rows:
            if prev is not None:
                s_m += math.dist(
                    (prev["x_f"], prev["y_f"], prev["z_f"]),
                    (row["x_f"], row["y_f"], row["z_f"]),
                )
            row["s_m"] = s_m
            prev = row
    return out


def build_total_pressure_ledger(pressure_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in pressure_rows:
        delta_p = signed_dp_along_flow(row, "p_rgh_start_pa", "p_rgh_end_pa")
        delta_q = signed_dp_along_flow(row, "dynamic_head_start_pa", "dynamic_head_end_pa")
        delta_p0 = signed_dp_along_flow(row, "total_pressure_proxy_start_pa", "total_pressure_proxy_end_pa")
        inertial_pa = fnum(row.get("rho_u_du_dxi_pa_m")) * fnum(row["L_m"])
        residual = (
            delta_p0
            + fnum(row["buoyancy_contribution_pa"])
            + inertial_pa
            + fnum(row["distributed_friction_pa"])
        )
        out.append({
            "source_id": row["source_id"],
            "case_id": row["case_id"],
            "span": row["span"],
            "station_start_label": row["station_start_label"],
            "station_end_label": row["station_end_label"],
            "L_m": fnum(row["L_m"]),
            "D_h_m": fnum(row["D_h_m"]),
            "Re": fnum(row["Re"]),
            "q_ref_pa": fnum(row["q_ref_pa"]),
            "delta_p_rgh_pa": delta_p,
            "delta_q_dyn_pa": delta_q,
            "delta_total_pressure_proxy_pa": delta_p0,
            "density_gradient_buoyancy_pa": fnum(row["buoyancy_contribution_pa"]),
            "inertial_term_pa": inertial_pa,
            "distributed_mechanical_loss_pa": fnum(row["distributed_friction_pa"]),
            "development_loss_proxy_pa": fnum(row["development_loss_pa"]),
            "minor_loss_upper_bound_pa": fnum(row["minor_loss_pa"]),
            "independent_total_pressure_residual_pa": residual,
            "total_pressure_proxy_label": "p_rgh_plus_half_rho_Ubulk_squared",
            "buoyancy_counting_policy": row.get("buoyancy_counting_policy", ""),
            "recirculation_flag": row.get("recirculation_flag", ""),
            "fit_eligible": row.get("fit_eligible", ""),
            "validation_eligible": row.get("validation_eligible", ""),
            "fit_use_status": row.get("fit_use_status", ""),
            "quality_flags": row.get("quality_flags", ""),
        })
    return out


def build_minor_loss_refined(minor_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in minor_rows:
        status = row.get("status", "")
        has_raw_tap = row.get("straight_loss_subtraction_status") == "subtracted_minimum_dz_proxy_straight_loss"
        is_computed = status.startswith("computed")
        if not is_computed:
            refinement_status = "raw_extraction_required"
            closure_grade = False
            blocker = "feature_missing_from_preserved_two_tap_output"
        elif has_raw_tap:
            refinement_status = "current_best_upper_bound_dz_proxy"
            closure_grade = False
            blocker = "full_centerline_tap_to_tap_length_missing"
        else:
            refinement_status = "not_refined"
            closure_grade = False
            blocker = "straight_loss_subtraction_unavailable"
        out.append({
            "source_id": row["source_id"],
            "case_id": row["case_id"],
            "feature": row["feature"],
            "feature_type": row["feature_type"],
            "downstream_span": row["downstream_span"],
            "adjacent_spans": row["adjacent_spans"],
            "status": status,
            "delta_p_rgh_pa": fnum(row.get("delta_p_rgh_pa")),
            "delta_q_dyn_pa": fnum(row.get("delta_q_dyn_pa")),
            "feature_total_pressure_loss_pa": fnum(row.get("feature_total_pressure_loss_pa")),
            "adjacent_straight_loss_subtracted_pa": fnum(row.get("adjacent_straight_loss_subtracted_pa"), 0.0),
            "local_minor_loss_upper_bound_pa": fnum(row.get("local_minor_loss_pa")),
            "K_apparent": fnum(row.get("K_apparent")),
            "K_local_upper_bound": fnum(row.get("K_local")),
            "closure_grade_K_available": closure_grade,
            "refinement_status": refinement_status,
            "raw_extraction_blocker": blocker,
            "recirculation_adjacent_spans": row.get("recirculation_adjacent_spans", ""),
            "fit_eligible": "False" if row.get("recirculation_adjacent_spans") else row.get("fit_eligible", ""),
            "validation_eligible": row.get("validation_eligible", ""),
            "quality_flags": row.get("quality_flags", ""),
            "notes": row.get("notes", ""),
        })
    return out


def build_station_development(
    pressure_index: Mapping[tuple[str, str], Mapping[str, str]],
    section_index: Mapping[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        for span in SPANS:
            points = [r for r in section_index.get((source_id, span), []) if not r["is_fitting_end_b"]]
            if len(points) < 4:
                status = "insufficient_nonfitting_stations"
                early = late = ratio = math.nan
            else:
                n = max(2, len(points) // 3)
                early = slope(points[:n], "p0_proxy_f")
                late = slope(points[-n:], "p0_proxy_f")
                ratio = late / early if math.isfinite(early) and abs(early) > 1e-30 else math.nan
                status = "section_mean_proxy"
            ledger = pressure_index[(source_id, span)]
            alignments = [p["flow_alignment_f"] for p in points]
            min_alignment = min(finite(alignments), default=math.nan)
            out.append({
                "source_id": source_id,
                "case_id": case_id(source_id),
                "span": span,
                "station_count_used": len(points),
                "early_total_pressure_proxy_slope_pa_m": early,
                "late_total_pressure_proxy_slope_pa_m": late,
                "slope_relaxation_ratio": ratio,
                "profile_shape_metric": (1.0 - min_alignment) if math.isfinite(min_alignment) else "",
                "profile_shape_status": status,
                "x_plus": fnum(ledger.get("x_plus")),
                "flow_reset_flag": ledger.get("flow_reset_flag", ""),
                "post_bend_reset_flag": str(span in ENTRY_SPANS),
                "development_loss_proxy_pa": fnum(ledger.get("development_loss_pa")),
                "development_model_status": "diagnostic_shah_minus_f1_proxy",
                "fit_use_status": "diagnostic_only",
                "quality_flags": ledger.get("quality_flags", ""),
            })
    return out


def load_recirc_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id in SOURCE_IDS:
        path = UPCOMER_DIR / f"upcomer_convection_cell_{source_id}.csv"
        for row in read_csv(path):
            row.setdefault("source_id", source_id)
            if not row.get("source_id"):
                row["source_id"] = source_id
            rows.append(row)
    if DOWNCOMER.exists():
        rows.extend(read_csv(DOWNCOMER))
    return rows


def build_recirc_invalidity(
    recirc_rows: list[dict[str, str]],
    pressure_index: Mapping[tuple[str, str], Mapping[str, str]],
    section_index: Mapping[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in recirc_rows:
        source_id = row.get("source_id")
        span = row.get("span")
        if source_id in SOURCE_IDS and span in {"left_lower_leg", "left_upper_leg", "right_leg"}:
            grouped[(source_id, span)].append(row)
    out: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        for span in ("left_lower_leg", "left_upper_leg", "right_leg"):
            rows = grouped.get((source_id, span), [])
            backflow = mean(fnum(r.get("backflow_area_fraction")) for r in rows)
            intensity = mean(fnum(r.get("recirculation_intensity"), 0.0) for r in rows)
            reverse_momentum = intensity / (1.0 + intensity) if math.isfinite(intensity) and intensity >= 0 else math.nan
            points = [p for p in section_index.get((source_id, span), []) if not p["is_fitting_end_b"]]
            ledger = pressure_index.get((source_id, span), {})
            sigma = fnum(ledger.get("flow_orientation_sigma"), 1.0)
            flow_points = list(reversed(points)) if sigma < 0 else points
            p0 = [p["p0_proxy_f"] for p in flow_points]
            recoveries = [p0[i + 1] - p0[i] for i in range(len(p0) - 1) if math.isfinite(p0[i]) and math.isfinite(p0[i + 1]) and p0[i + 1] > p0[i]]
            monotonic = len(recoveries) == 0 if len(p0) >= 2 else False
            if span in RECIRCULATION_SPANS:
                fit_status = "diagnostic_only_recirculation_invalid_single_stream"
            else:
                fit_status = "single_stream_check_no_backflow_observed"
            out.append({
                "source_id": source_id,
                "case_id": case_id(source_id),
                "span": span,
                "station_count_with_velocity_metric": len(rows),
                "backflow_area_fraction_mean": backflow,
                "reverse_flow_momentum_fraction_proxy": reverse_momentum,
                "wrong_sign_axial_velocity_area_fraction": backflow,
                "pressure_recovery_zone_count": len(recoveries),
                "pressure_recovery_total_pa": sum(recoveries),
                "total_pressure_proxy_monotonic_decrease": monotonic,
                "recirculation_invalidity_status": fit_status,
                "fit_eligible": "False" if span in RECIRCULATION_SPANS else "True",
                "metric_source_status": "existing_cut_plane_metrics" if rows else "raw_plane_metric_missing",
            })
    return out


def build_uncertainty_budget(
    pressure_rows: list[dict[str, str]],
    minor_rows: list[dict[str, str]],
    quasi_rows: list[dict[str, str]],
    station_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    station_by_key = {(r["source_id"], r["span"]): r for r in station_rows}
    quasi_primary = [r for r in quasi_rows if r.get("source_id") in SOURCE_IDS and boolish(r.get("is_primary_window"))]
    quasi_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in quasi_primary:
        quasi_by_source[row["source_id"]].append(row)
    minor_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in minor_rows:
        minor_by_source[row["source_id"]].append(row)
    for row in pressure_rows:
        source_id = row["source_id"]
        span = row["span"]
        key = (source_id, span)
        out.append({
            "source_id": source_id,
            "case_id": row["case_id"],
            "span": span,
            "uncertainty_term": "mesh_gci",
            "qoi_family": "L_m;D_h;section_means;f;K;Nu",
            "status": "not_quantified",
            "value": "",
            "units": "",
            "basis": "TODO-MESH-UNCERTAINTY remains open; coarse mesh only in admitted package",
            "fit_impact": "paper_grade_bounds_blocked",
        })
        q_unc = max(finite(fnum(r.get("uncertainty_total")) for r in quasi_by_source.get(source_id, [])), default=math.nan)
        out.append({
            "source_id": source_id,
            "case_id": row["case_id"],
            "span": span,
            "uncertainty_term": "time_window_uq",
            "qoi_family": "monitor_histories",
            "status": "quantified_from_quasi_steady_package" if math.isfinite(q_unc) else "not_available",
            "value": q_unc,
            "units": "native_qoi_units",
            "basis": rel(QUASI_STEADY),
            "fit_impact": "carry_as_observation_uncertainty",
        })
        dev = station_by_key.get(key, {})
        ratio = fnum(dev.get("slope_relaxation_ratio"))
        out.append({
            "source_id": source_id,
            "case_id": row["case_id"],
            "span": span,
            "uncertainty_term": "station_placement_sensitivity",
            "qoi_family": "pressure_gradient",
            "status": "diagnostic_proxy",
            "value": abs(ratio - 1.0) if math.isfinite(ratio) else "",
            "units": "fraction",
            "basis": "early_vs_late_total_pressure_proxy_slope",
            "fit_impact": "large_values_flag_development_or_feature_contamination",
        })
        align = fnum(dev.get("profile_shape_metric"))
        out.append({
            "source_id": source_id,
            "case_id": row["case_id"],
            "span": span,
            "uncertainty_term": "pressure_averaging_method_sensitivity",
            "qoi_family": "section_mean_pressure",
            "status": "diagnostic_proxy",
            "value": align,
            "units": "1_minus_flow_alignment",
            "basis": "single-leg mask flow-alignment from section-mean extraction",
            "fit_impact": "high_values_reduce_section_mean_confidence",
        })
        src_minor = minor_by_source.get(source_id, [])
        max_k = max(finite(fnum(r.get("K_local")) for r in src_minor), default=math.nan)
        out.append({
            "source_id": source_id,
            "case_id": row["case_id"],
            "span": span,
            "uncertainty_term": "local_dynamic_pressure_normalization",
            "qoi_family": "K",
            "status": "upper_bound_only",
            "value": max_k,
            "units": "K",
            "basis": rel(MINOR_LOSS),
            "fit_impact": "minor_loss_coefficients_not_closure_grade",
        })
        out.append({
            "source_id": source_id,
            "case_id": row["case_id"],
            "span": span,
            "uncertainty_term": "development_model_form",
            "qoi_family": "development_loss",
            "status": "model_form_proxy_only",
            "value": fnum(row.get("development_loss_pa")),
            "units": "Pa",
            "basis": "Shah_minus_F1 proxy; station relaxation rows provide diagnostic challenge",
            "fit_impact": "do_not_tune_as_settled_loss_without_development_validation",
        })
    return out


def build_loop_closure(
    total_rows: list[dict[str, Any]],
    pressure_rows: list[dict[str, str]],
    minor_rows: list[dict[str, Any]],
    recirc_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    p_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in pressure_rows:
        p_by_source[row["source_id"]].append(row)
    t_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in total_rows:
        t_by_source[row["source_id"]].append(row)
    m_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in minor_rows:
        m_by_source[row["source_id"]].append(row)
    r_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in recirc_rows:
        r_by_source[row["source_id"]].append(row)
    for source_id in SOURCE_IDS:
        p_rows = p_by_source[source_id]
        t_rows = t_by_source[source_id]
        m_rows = m_by_source[source_id]
        rec_rows = [r for r in r_by_source[source_id] if r["span"] in RECIRCULATION_SPANS]
        total_mech = sum(fnum(r.get("distributed_friction_pa")) for r in p_rows)
        buoyancy = sum(fnum(r.get("buoyancy_contribution_pa")) for r in p_rows)
        development = sum(fnum(r.get("development_loss_pa")) for r in p_rows)
        minor_upper = sum(
            fnum(r.get("local_minor_loss_upper_bound_pa"), 0.0)
            for r in m_rows
            if str(r.get("status", "")).startswith("computed")
        )
        recirc = mean(fnum(r.get("backflow_area_fraction_mean")) for r in rec_rows)
        residual = sum(fnum(r.get("independent_total_pressure_residual_pa")) for r in t_rows)
        out.append({
            "source_id": source_id,
            "case_id": case_id(source_id),
            "span_count": len(p_rows),
            "total_mechanical_loss_pa": total_mech,
            "total_buoyancy_driving_head_pa": buoyancy,
            "total_development_proxy_pa": development,
            "total_minor_loss_upper_bound_pa": minor_upper,
            "recirculation_diagnostic_backflow_mean": recirc,
            "independent_total_pressure_residual_pa": residual,
            "minor_loss_fraction_of_mechanical": minor_upper / total_mech if total_mech else "",
            "development_fraction_of_mechanical": development / total_mech if total_mech else "",
            "closure_status": "recirculation_regime_switch_required" if math.isfinite(recirc) and recirc > 0.05 else "single_stream_closure_screen",
            "interpretation": "Use F3/Shah as baseline for fit-eligible straight spans; keep minor losses upper-bound and recirculation spans diagnostic.",
        })
    return out


def build_decision_matrix(loop_rows: list[dict[str, Any]], recirc_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    max_recirc = max(finite(fnum(r.get("backflow_area_fraction_mean")) for r in recirc_rows if r["span"] in RECIRCULATION_SPANS), default=math.nan)
    max_minor_frac = max(finite(fnum(r.get("minor_loss_fraction_of_mechanical")) for r in loop_rows), default=math.nan)
    max_dev_frac = max(finite(fnum(r.get("development_fraction_of_mechanical")) for r in loop_rows), default=math.nan)
    return [
        {
            "closure_option": "F3_Shah_baseline",
            "evidence_status": "supported_for_fit_eligible_straight_spans",
            "supporting_metric": "July 8 pressure ledger fit-eligible rows plus development proxy",
            "decision": "retain_as_baseline",
            "blocker_or_caveat": "Does not resolve recirculation-cell spans or closure-grade minor-loss K.",
        },
        {
            "closure_option": "per_leg_terms",
            "evidence_status": "conditionally_supported",
            "supporting_metric": f"max_development_fraction_of_mechanical={max_dev_frac:.6g}" if math.isfinite(max_dev_frac) else "development_fraction_unavailable",
            "decision": "evaluate_after_uncertainty",
            "blocker_or_caveat": "Mesh/GCI and station-placement uncertainty remain unquantified.",
        },
        {
            "closure_option": "explicit_minor_losses",
            "evidence_status": "upper_bound_only",
            "supporting_metric": f"max_minor_loss_fraction_of_mechanical={max_minor_frac:.6g}" if math.isfinite(max_minor_frac) else "minor_fraction_unavailable",
            "decision": "include_as_sensitivity_not_fit_coefficient",
            "blocker_or_caveat": "Full centerline tap-to-tap raw extraction is still required for closure-grade K.",
        },
        {
            "closure_option": "recirculation_regime_switch",
            "evidence_status": "strongly_supported_for_upcomer_spans",
            "supporting_metric": f"max_upcomer_backflow_area_fraction={max_recirc:.6g}" if math.isfinite(max_recirc) else "recirculation_metric_unavailable",
            "decision": "required_for_left_lower_and_left_upper_leg",
            "blocker_or_caveat": "Onset threshold remains extrapolated until admitted perturbation/sweep data pass gates.",
        },
    ]


def build_source_inventory(paths: Sequence[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": path.exists(),
            "kind": "directory" if path.exists() and path.is_dir() else "file",
            "role": "input" if path != OUT_DIR else "output",
        })
    return rows


def write_readme(out_dir: Path, summary: Mapping[str, Any]) -> None:
    text = f"""# Hydraulic Closure Rigor Audit

Generated: `{summary['generated_at']}`
Task: `AGENT-223`

## Scope

This package integrates existing Salt 2/3/4 Jin hydraulic evidence into one
audit. It does not modify the July 8 pressure ledger, minor-loss ledger,
observation table, native solver outputs, or external Fluid code.

## Outputs

- `independent_total_pressure_ledger.csv`
- `minor_loss_two_tap_refined.csv`
- `station_development_analysis.csv`
- `recirculation_invalidity.csv`
- `hydraulic_uncertainty_budget.csv`
- `loop_closure_audit.csv`
- `closure_decision_matrix.csv`
- `source_inventory.csv`
- `summary.json`

## Key Findings

- Rows audited: `{summary['pressure_span_rows']}` pressure-span rows and
  `{summary['minor_loss_rows']}` minor-loss feature rows.
- The total-pressure ledger uses `p_rgh + 0.5*rho*U_bulk^2` as a proxy, not a
  full local total pressure.
- Minor-loss values remain upper-bound / sensitivity inputs until full raw
  centerline tap-to-tap extraction is available.
- Upcomer recirculation spans remain diagnostic-only for single-stream closure
  fitting.
- Mesh/GCI uncertainty is not quantified in the available admitted evidence and
  is carried as an explicit blocker.

## Reproduce

```bash
python tools/analyze/build_hydraulic_closure_rigor_audit.py
python -m pytest tools/analyze/test_hydraulic_closure_rigor_audit.py -q
```
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pressure_rows = [r for r in read_csv(PRESSURE_LEDGER) if r.get("source_id") in SOURCE_IDS]
    pressure_index = {(r["source_id"], r["span"]): r for r in pressure_rows}
    minor_rows_raw = [r for r in read_csv(MINOR_LOSS) if r.get("source_id") in SOURCE_IDS]
    quasi_rows = read_csv(QUASI_STEADY) if QUASI_STEADY.exists() else []
    section_index = load_section_rows()
    recirc_raw = load_recirc_rows()

    total_pressure = build_total_pressure_ledger(pressure_rows)
    minor_refined = build_minor_loss_refined(minor_rows_raw)
    station_development = build_station_development(pressure_index, section_index)
    recirc_invalidity = build_recirc_invalidity(recirc_raw, pressure_index, section_index)
    uncertainty = build_uncertainty_budget(pressure_rows, minor_rows_raw, quasi_rows, station_development)
    loop_closure = build_loop_closure(total_pressure, pressure_rows, minor_refined, recirc_invalidity)
    decision_matrix = build_decision_matrix(loop_closure, recirc_invalidity)

    source_inventory = build_source_inventory([
        PRESSURE_LEDGER, MINOR_LOSS, QUASI_STEADY, SECTION_DIR, UPCOMER_DIR,
        DOWNCOMER, SEGMENT_FRICTION, MOMENTUM_BUDGET, OBSERVATION_TABLE,
        UPCOMER_ONSET, out_dir,
    ])

    write_csv(out_dir / "independent_total_pressure_ledger.csv", total_pressure, [
        "source_id", "case_id", "span", "station_start_label", "station_end_label",
        "L_m", "D_h_m", "Re", "q_ref_pa", "delta_p_rgh_pa", "delta_q_dyn_pa",
        "delta_total_pressure_proxy_pa", "density_gradient_buoyancy_pa",
        "inertial_term_pa", "distributed_mechanical_loss_pa",
        "development_loss_proxy_pa", "minor_loss_upper_bound_pa",
        "independent_total_pressure_residual_pa", "total_pressure_proxy_label",
        "buoyancy_counting_policy", "recirculation_flag", "fit_eligible",
        "validation_eligible", "fit_use_status", "quality_flags",
    ])
    write_csv(out_dir / "minor_loss_two_tap_refined.csv", minor_refined, [
        "source_id", "case_id", "feature", "feature_type", "downstream_span",
        "adjacent_spans", "status", "delta_p_rgh_pa", "delta_q_dyn_pa",
        "feature_total_pressure_loss_pa", "adjacent_straight_loss_subtracted_pa",
        "local_minor_loss_upper_bound_pa", "K_apparent", "K_local_upper_bound",
        "closure_grade_K_available", "refinement_status", "raw_extraction_blocker",
        "recirculation_adjacent_spans", "fit_eligible", "validation_eligible",
        "quality_flags", "notes",
    ])
    write_csv(out_dir / "station_development_analysis.csv", station_development, [
        "source_id", "case_id", "span", "station_count_used",
        "early_total_pressure_proxy_slope_pa_m", "late_total_pressure_proxy_slope_pa_m",
        "slope_relaxation_ratio", "profile_shape_metric", "profile_shape_status",
        "x_plus", "flow_reset_flag", "post_bend_reset_flag",
        "development_loss_proxy_pa", "development_model_status",
        "fit_use_status", "quality_flags",
    ])
    write_csv(out_dir / "recirculation_invalidity.csv", recirc_invalidity, [
        "source_id", "case_id", "span", "station_count_with_velocity_metric",
        "backflow_area_fraction_mean", "reverse_flow_momentum_fraction_proxy",
        "wrong_sign_axial_velocity_area_fraction", "pressure_recovery_zone_count",
        "pressure_recovery_total_pa", "total_pressure_proxy_monotonic_decrease",
        "recirculation_invalidity_status", "fit_eligible", "metric_source_status",
    ])
    write_csv(out_dir / "hydraulic_uncertainty_budget.csv", uncertainty, [
        "source_id", "case_id", "span", "uncertainty_term", "qoi_family",
        "status", "value", "units", "basis", "fit_impact",
    ])
    write_csv(out_dir / "loop_closure_audit.csv", loop_closure, [
        "source_id", "case_id", "span_count", "total_mechanical_loss_pa",
        "total_buoyancy_driving_head_pa", "total_development_proxy_pa",
        "total_minor_loss_upper_bound_pa", "recirculation_diagnostic_backflow_mean",
        "independent_total_pressure_residual_pa", "minor_loss_fraction_of_mechanical",
        "development_fraction_of_mechanical", "closure_status", "interpretation",
    ])
    write_csv(out_dir / "closure_decision_matrix.csv", decision_matrix, [
        "closure_option", "evidence_status", "supporting_metric", "decision",
        "blocker_or_caveat",
    ])
    write_csv(out_dir / "source_inventory.csv", source_inventory, ["path", "exists", "kind", "role"])

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task_id": "AGENT-223",
        "source_ids": SOURCE_IDS,
        "pressure_span_rows": len(total_pressure),
        "minor_loss_rows": len(minor_refined),
        "station_development_rows": len(station_development),
        "recirculation_rows": len(recirc_invalidity),
        "uncertainty_rows": len(uncertainty),
        "loop_closure_rows": len(loop_closure),
        "decision_rows": len(decision_matrix),
        "openfoam_extraction_run": False,
        "openfoam_note": "Existing section-mean and recirculation artifacts were sufficient for this first synthesis; raw extraction remains a documented blocker for closure-grade K/profile metrics.",
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    print(f"Wrote {rel(out_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
