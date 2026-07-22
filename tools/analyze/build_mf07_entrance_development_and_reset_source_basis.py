#!/usr/bin/env python3.11
"""Build the MF07 entrance/development/reset source-basis gate."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo


TASK_ID = "TODO-MF07-ENTRANCE-DEVELOPMENT-AND-RESET-SOURCE-BASIS-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis"

SOURCE_ENVELOPE = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_source_envelope/branch_source_envelope.csv"
RESET_MAP = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/reset_distance_map.csv"
GATED_BRANCH = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_litrev_gated_single_stream_developing_branch/single_stream_developing_branch_gate.csv"
BRANCH_SUMMARY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_litrev_gated_single_stream_developing_branch/single_stream_branch_summary.csv"
BL_SCORECARD = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_boundary_layer_development_scorecard/development_toggle_scorecard.csv"
D2_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/tp_projection_thermal_development_evidence.csv"
D2_SCORE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/d2_score_improvement_summary.csv"
SENSOR_ERRORS = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/tested_model_form_sensor_errors.csv"
S12_TP_EXCHANGE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/s12_tp_exchange_evidence_table.csv"
S13_UQ_SUMMARY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/same_qoi_temporal_uq_summary.csv"
S13_HEAT_MATCH = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/heat_flow_match_diagnostics.csv"

MODEL_IDS = {"M3_as_is", "D2_M3_sensor_kind_offsets_train"}
SEGMENT_TO_SPAN = {
    "top_horizontal_exit": "upper_leg",
    "right_downcomer_bottom_horizontal_junction": "right_leg",
    "left_lower_vertical": "left_lower_leg",
    "test_section": "test_section_span",
    "left_upper_vertical": "left_upper_leg",
    "right_vertical": "right_leg",
    "heated_incline": "left_lower_leg",
    "cooled_incline_pre_hx": "upper_leg",
    "cooled_incline_post_hx": "upper_leg",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: object, default: float = math.nan) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def finite(values: list[float]) -> list[float]:
    return [v for v in values if math.isfinite(v)]


def mean_or_blank(values: list[float]) -> float | str:
    vals = finite(values)
    return mean(vals) if vals else ""


def min_or_blank(values: list[float]) -> float | str:
    vals = finite(values)
    return min(vals) if vals else ""


def max_or_blank(values: list[float]) -> float | str:
    vals = finite(values)
    return max(vals) if vals else ""


def bool_text(value: object) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "pass"}


def joined(items: set[str] | list[str]) -> str:
    return ";".join(sorted(str(i) for i in items if str(i)))


def span_key(case_id: str, span: str) -> tuple[str, str]:
    return (case_id, span)


def single_stream_precheck_available(row: dict[str, str]) -> bool:
    status = row.get("single_stream_developing_allowed", "")
    return status == "yes" or "precheck_only" in status


def recirculation_invalid_for_single_stream(row: dict[str, str]) -> bool:
    return "recirculation_invalid_single_stream" in row.get("blocking_reasons", "")


def summarize_source_envelope(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[span_key(row["case_id"], row["span"])].append(row)
    out: dict[tuple[str, str], dict[str, object]] = {}
    for key, group in groups.items():
        signs = {r["heating_cooling_sign"] for r in group if r.get("heating_cooling_sign")}
        fit_status = Counter(r["fit_use_status"] for r in group)
        quality_flags: set[str] = set()
        for row in group:
            quality_flags.update(flag for flag in row.get("quality_flags", "").split(";") if flag)
        out[key] = {
            "source_rows": len(group),
            "heating_cooling_signs": joined(signs),
            "fit_target_rows": fit_status.get("fit_target", 0),
            "not_fit_rows": sum(v for k, v in fit_status.items() if k != "fit_target"),
            "mean_Re": mean_or_blank([as_float(r["Re"]) for r in group]),
            "mean_Pr": mean_or_blank([as_float(r["Pr"]) for r in group]),
            "mean_Gz": mean_or_blank([as_float(r["Gz"]) for r in group]),
            "min_Gz": min_or_blank([as_float(r["Gz"]) for r in group]),
            "max_Gz": max_or_blank([as_float(r["Gz"]) for r in group]),
            "mean_Ri": mean_or_blank([as_float(r["Ri"]) for r in group]),
            "mean_Ra": mean_or_blank([as_float(r["Ra"]) for r in group]),
            "quality_flags": joined(quality_flags),
        }
    return out


def summarize_gated_branch(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[span_key(row["case_id"], row["span"])].append(row)
    out: dict[tuple[str, str], dict[str, object]] = {}
    for key, group in groups.items():
        blocking: set[str] = set()
        for row in group:
            blocking.update(flag for flag in row.get("blocking_reasons", "").split(";") if flag)
        out[key] = {
            "gated_rows": len(group),
            "single_stream_allowed_rows": sum(1 for r in group if single_stream_precheck_available(r)),
            "same_qoi_uq_blocked_rows": sum(1 for r in group if "same_QOI_UQ_missing" in r.get("blocking_reasons", "")),
            "recirculation_blocked_rows": sum(1 for r in group if recirculation_invalid_for_single_stream(r)),
            "gated_mean_Gz": mean_or_blank([as_float(r["Gz"]) for r in group]),
            "gated_mean_Re": mean_or_blank([as_float(r["Re"]) for r in group]),
            "gated_mean_Pr": mean_or_blank([as_float(r["Pr"]) for r in group]),
            "blocking_reasons": joined(blocking),
            "coefficient_admission_status": joined({r["coefficient_admission_status"] for r in group}),
        }
    return out


def build_segment_classification(
    source: dict[tuple[str, str], dict[str, object]],
    gated: dict[tuple[str, str], dict[str, object]],
    resets: list[dict[str, str]],
    branch_summary: list[dict[str, str]],
) -> list[dict[str, object]]:
    branch_by_span = {r["span"]: r for r in branch_summary}
    rows: list[dict[str, object]] = []
    for reset in resets:
        if reset["case_id"] not in {"salt_2", "salt_3", "salt_4"}:
            continue
        case_id = reset["case_id"]
        span = reset["downstream_span"]
        key = span_key(case_id, span)
        src = source.get(key, {})
        gate = gated.get(key, {})
        branch = branch_by_span.get(span, {})
        allowed = int(gate.get("single_stream_allowed_rows", 0) or 0)
        source_rows = int(src.get("source_rows", 0) or 0)
        recirc_blocked = int(gate.get("recirculation_blocked_rows", 0) or 0)
        same_qoi_blocked = int(gate.get("same_qoi_uq_blocked_rows", 0) or 0)
        mean_re = as_float(src.get("mean_Re", gate.get("gated_mean_Re", "")))
        mean_pr = as_float(src.get("mean_Pr", gate.get("gated_mean_Pr", "")))
        l_over_d = as_float(reset.get("L_over_D_from_reset"))
        hydraulic_entrance_l_over_d = 0.05 * mean_re if math.isfinite(mean_re) else math.nan
        thermal_entrance_l_over_d = 0.05 * mean_re * mean_pr if math.isfinite(mean_re) and math.isfinite(mean_pr) else math.nan
        thermal_development_indicated = (
            math.isfinite(l_over_d)
            and math.isfinite(thermal_entrance_l_over_d)
            and l_over_d < thermal_entrance_l_over_d
        )
        thermal_reset_unknown = "unknown" in reset.get("thermal_reset_status", "")
        if recirc_blocked:
            hydraulic_status = "blocked_single_stream_recirculation_invalid"
        elif math.isfinite(as_float(reset.get("L_over_D_from_reset"))):
            hydraulic_status = "diagnostic_reset_basis_available_no_coupled_closure"
        else:
            hydraulic_status = "missing_reset_distance"
        if source_rows == 0:
            thermal_status = "missing_source_envelope"
        elif recirc_blocked:
            thermal_status = "blocked_single_stream_recirculation_invalid"
        elif thermal_development_indicated and (thermal_reset_unknown or same_qoi_blocked):
            thermal_status = "thermally_developing_diagnostic_only_missing_reset_or_same_qoi_uq"
        elif thermal_reset_unknown or same_qoi_blocked:
            thermal_status = "diagnostic_only_missing_thermal_reset_or_same_qoi_uq"
        elif allowed:
            thermal_status = "precheck_available_no_coefficient_admission"
        else:
            thermal_status = "diagnostic_only_not_admitted"
        if recirc_blocked:
            decision = "forbidden_as_single_stream_fit"
        elif source_rows and math.isfinite(as_float(reset.get("L_over_D_from_reset"))):
            decision = "diagnostic_only"
        else:
            decision = "missing_inputs"
        rows.append(
            {
                "case_id": case_id,
                "span": span,
                "orientation": reset.get("orientation", ""),
                "heating_cooling_signs": src.get("heating_cooling_signs", ""),
                "source_rows": source_rows,
                "fit_target_rows": src.get("fit_target_rows", 0),
                "mean_Re": src.get("mean_Re", gate.get("gated_mean_Re", "")),
                "mean_Pr": src.get("mean_Pr", gate.get("gated_mean_Pr", "")),
                "mean_Gz": src.get("mean_Gz", gate.get("gated_mean_Gz", "")),
                "min_Gz": src.get("min_Gz", ""),
                "max_Gz": src.get("max_Gz", ""),
                "mean_Ri": src.get("mean_Ri", ""),
                "mean_Ra": src.get("mean_Ra", ""),
                "x_from_reset_m": reset.get("x_from_reset_m", ""),
                "L_over_D_from_reset": reset.get("L_over_D_from_reset", ""),
                "hydraulic_entrance_L_over_D_0p05Re": hydraulic_entrance_l_over_d if math.isfinite(hydraulic_entrance_l_over_d) else "",
                "thermal_entrance_L_over_D_0p05RePr": thermal_entrance_l_over_d if math.isfinite(thermal_entrance_l_over_d) else "",
                "thermal_development_indicated_by_L_over_D": thermal_development_indicated,
                "hydraulic_reset_status": reset.get("hydraulic_reset_status", ""),
                "thermal_reset_status": reset.get("thermal_reset_status", ""),
                "branch_lane_status": branch.get("lane_status", ""),
                "single_stream_allowed_rows": allowed,
                "same_qoi_uq_blocked_rows": same_qoi_blocked,
                "recirculation_blocked_rows": recirc_blocked,
                "hydraulic_reset_variant_status": hydraulic_status,
                "thermal_graetz_variant_status": thermal_status,
                "blocking_reasons": gate.get("blocking_reasons", ""),
                "quality_flags": src.get("quality_flags", reset.get("quality_flags", "")),
                "mf07_gate": decision,
            }
        )
    return rows


def expected_thermal_direction(signs: str) -> str:
    if "heating" in signs or "heating_expected" in signs:
        return "positive_bulk_to_TP_offset_plausible"
    if "cooling" in signs or "cooling_expected" in signs:
        return "negative_bulk_to_TP_offset_plausible"
    return "unknown_without_signed_source"


def direction_match(signed_error: float, expected: str) -> str:
    if not math.isfinite(signed_error):
        return "not_evaluable"
    if expected.startswith("positive"):
        return "consistent_if_model_is_cold" if signed_error < 0 else "opposes_positive_development_offset"
    if expected.startswith("negative"):
        return "consistent_if_model_is_hot" if signed_error > 0 else "opposes_negative_development_offset"
    return "unknown"


def build_tp_join(
    errors: list[dict[str, str]],
    source: dict[tuple[str, str], dict[str, object]],
    gated: dict[tuple[str, str], dict[str, object]],
    resets: list[dict[str, str]],
) -> list[dict[str, object]]:
    reset_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for row in resets:
        key = span_key(row["case_id"], row["downstream_span"])
        existing = reset_by_key.get(key)
        row_is_span_level = row.get("feature_or_span") == row.get("downstream_span")
        existing_is_span_level = existing and existing.get("feature_or_span") == existing.get("downstream_span")
        if existing is None or (row_is_span_level and not existing_is_span_level):
            reset_by_key[key] = row
            continue
        if existing is not None and not existing_is_span_level:
            if as_float(existing.get("L_over_D_from_reset")) == 0 and as_float(row.get("L_over_D_from_reset")) > 0:
                reset_by_key[key] = row
    rows: list[dict[str, object]] = []
    for err in errors:
        if err["tested_model_form_id"] not in MODEL_IDS or err["sensor_kind"] != "TP":
            continue
        if err.get("split_group") != "train":
            continue
        span = SEGMENT_TO_SPAN.get(err["prediction_source_segment"], err["prediction_source_segment"])
        key = span_key(err["case_id"], span)
        src = source.get(key, {})
        gate = gated.get(key, {})
        reset = reset_by_key.get(key, {})
        signed = as_float(err["signed_error_K"])
        expected = expected_thermal_direction(str(src.get("heating_cooling_signs", "")))
        rows.append(
            {
                "tested_model_form_id": err["tested_model_form_id"],
                "case_id": err["case_id"],
                "split_group": err["split_group"],
                "sensor": err["sensor"],
                "prediction_source_segment": err["prediction_source_segment"],
                "mapped_span": span,
                "target_K": err["target_K"],
                "adjusted_predicted_K": err["adjusted_predicted_K"],
                "signed_error_K": signed,
                "signed_error_percent_of_target": err["signed_error_percent_of_target"],
                "heating_cooling_signs": src.get("heating_cooling_signs", ""),
                "mean_Re": src.get("mean_Re", gate.get("gated_mean_Re", "")),
                "mean_Pr": src.get("mean_Pr", gate.get("gated_mean_Pr", "")),
                "mean_Gz": src.get("mean_Gz", gate.get("gated_mean_Gz", "")),
                "x_from_reset_m": reset.get("x_from_reset_m", ""),
                "L_over_D_from_reset": reset.get("L_over_D_from_reset", ""),
                "thermal_reset_status": reset.get("thermal_reset_status", ""),
                "single_stream_allowed_rows": gate.get("single_stream_allowed_rows", 0),
                "recirculation_blocked_rows": gate.get("recirculation_blocked_rows", 0),
                "expected_thermal_development_direction": expected,
                "direction_match_to_signed_residual": direction_match(signed, expected),
                "use_boundary": "diagnostic_residual_shape_only_no_fit_no_protected_scoring",
            }
        )
    return rows


def build_variant_table(tp_join: list[dict[str, object]], segment_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    m3_tp = [r for r in tp_join if r["tested_model_form_id"] == "M3_as_is"]
    span_rows = [r for r in segment_rows if r["case_id"] in {"salt_2", "salt_3", "salt_4"}]
    finite_reset = sum(1 for r in span_rows if math.isfinite(as_float(r["L_over_D_from_reset"])))
    nonrecirc = sum(1 for r in span_rows if int(r["recirculation_blocked_rows"] or 0) == 0)
    thermal_known = sum(1 for r in span_rows if r["heating_cooling_signs"])
    positive_consistent = sum(1 for r in m3_tp if r["direction_match_to_signed_residual"] == "consistent_if_model_is_cold")
    negative_opposes = sum(1 for r in m3_tp if r["direction_match_to_signed_residual"] == "opposes_negative_development_offset")
    return [
        {
            "variant_id": "MF07a_hydraulic_reset_development_only",
            "predeclared_basis": "x_from_reset and L/D after bends/junctions/endpoints",
            "source_envelope_rows": finite_reset,
            "direction_of_effect_against_TP": "indirect_only_through_mdot_or_residence_time_no_standalone_bulk_to_TP_offset",
            "consistent_m3_tp_rows": 0,
            "contradictory_m3_tp_rows": 0,
            "missing_or_blocked_rows": len(span_rows) - finite_reset,
            "runtime_legal_now": False,
            "train_only_smoke_ready": False,
            "decision": "diagnostic_only_no_coupled_pressure_thermal_closure",
        },
        {
            "variant_id": "MF07b_thermal_graetz_development_only",
            "predeclared_basis": "Gz, Re, Pr, signed heat source/loss envelope, and thermal reset status",
            "source_envelope_rows": thermal_known,
            "direction_of_effect_against_TP": "heating spans can produce positive local TP offset; cooling spans can produce negative local TP offset",
            "consistent_m3_tp_rows": positive_consistent,
            "contradictory_m3_tp_rows": negative_opposes,
            "missing_or_blocked_rows": sum(1 for r in span_rows if r["thermal_graetz_variant_status"] != "precheck_available_no_coefficient_admission"),
            "runtime_legal_now": False,
            "train_only_smoke_ready": False,
            "decision": "diagnostic_only_missing_thermal_reset_same_qoi_uq_and_released_formula",
        },
        {
            "variant_id": "MF07c_combined_reset_plus_thermal_graetz_with_recirc_guard",
            "predeclared_basis": "apply thermal development only where reset/Gz/source signs exist and single-stream recirculation guard passes",
            "source_envelope_rows": min(finite_reset, thermal_known, nonrecirc),
            "direction_of_effect_against_TP": "plausible layered source-basis for nonrecirculating spans; guarded off in recirculating spans",
            "consistent_m3_tp_rows": positive_consistent,
            "contradictory_m3_tp_rows": negative_opposes,
            "missing_or_blocked_rows": len(span_rows) - min(finite_reset, thermal_known, nonrecirc),
            "runtime_legal_now": False,
            "train_only_smoke_ready": False,
            "decision": "diagnostic_only_best_next_after_MF08_signed_source_basis",
        },
    ]


def build_bulk_to_tp_gate(
    tp_join: list[dict[str, object]],
    segment_rows: list[dict[str, object]],
    s13_bridge: list[dict[str, object]],
) -> list[dict[str, object]]:
    m3 = [r for r in tp_join if r["tested_model_form_id"] == "M3_as_is"]
    cold_m3 = sum(1 for r in m3 if as_float(r["signed_error_K"]) < 0)
    consistent = sum(1 for r in m3 if r["direction_match_to_signed_residual"] == "consistent_if_model_is_cold")
    opposed = sum(1 for r in m3 if r["direction_match_to_signed_residual"].startswith("opposes"))
    ratios = [as_float(r["abs_wall_core_over_D2_train_TP_offset"]) for r in s13_bridge]
    ratios = [r for r in ratios if math.isfinite(r)]
    max_ratio = max(ratios) if ratios else math.nan
    return [
        {
            "gate": "reset_graetz_coordinates_exist",
            "status": "pass_diagnostic",
            "evidence": f"{sum(1 for r in segment_rows if r['thermal_development_indicated_by_L_over_D'])} rows have L/D below 0.05*Re*Pr.",
            "consequence": "thermal development is plausible enough for a source-basis study.",
            "release_allowed": False,
        },
        {
            "gate": "train_only_TP_residual_direction",
            "status": "pass_diagnostic",
            "evidence": f"{cold_m3}/{len(m3)} train M3 TP rows are cold relative to post-solve TP targets.",
            "consequence": "a positive bulk-to-TP projection layer is plausible before TW correction.",
            "release_allowed": False,
        },
        {
            "gate": "signed_source_direction_sufficiency",
            "status": "mixed",
            "evidence": f"{consistent} train TP rows match signed-source expectation; {opposed} oppose it.",
            "consequence": "thermal development likely cannot be a simple local signed-source correction only.",
            "release_allowed": False,
        },
        {
            "gate": "s13_wall_core_magnitude_sufficiency",
            "status": "fail_full_ownership",
            "evidence": f"max |wall-core contrast| / D2 train TP offset = {max_ratio:.6g}.",
            "consequence": "S13 exchange evidence is useful, but wall/core contrast alone cannot explain the D2 TP offset.",
            "release_allowed": False,
        },
        {
            "gate": "source_property_and_same_qoi_release",
            "status": "fail_closed",
            "evidence": "same-QOI TP projection UQ, released formula, and source/property labels are missing.",
            "consequence": "MF07 stays diagnostic-only; MF08/MF09 must run before any train-only smoke.",
            "release_allowed": False,
        },
    ]


def build_next_analysis_plan() -> list[dict[str, object]]:
    return [
        {
            "priority": 1,
            "task": "MF08 signed heat-path thermal-development source basis",
            "analysis": "separate heated, cooled, passive, and piecewise reset-memory branches",
            "why_next": "MF07 shows thermal development is plausible but not explained by a single signed-source rule.",
            "done_when": "signed source table says ready_for_train_only_smoke or fail-closed",
        },
        {
            "priority": 2,
            "task": "MF09 recirculating upcomer thermal alternatives",
            "analysis": "compare guarded single-stream exclusion, exchange cell, two-zone stratification, and energy residual bridge",
            "why_next": "recirculation invalidates ordinary single-stream development in the left/upcomer path.",
            "done_when": "one upcomer alternative becomes smoke-ready or all remain diagnostic-only",
        },
        {
            "priority": 3,
            "task": "MF10 train/support-only predeclared bakeoff",
            "analysis": "run only variants released by MF07/MF08/MF09 source-basis gates",
            "why_next": "a bakeoff before source-basis release would be an empirical fit path.",
            "done_when": "candidate_for_source_property_audit, diagnostic_only, or reject_model_family",
        },
        {
            "priority": 4,
            "task": "TW-after-TP residual ownership",
            "analysis": "subtract defended TP projection before wall/source/axial-mixing attribution",
            "why_next": "TW should not absorb the bulk-to-TP residual.",
            "done_when": "TW residual owner table with no internal-Nu absorption",
        },
    ]


def build_s13_bridge(
    s12_rows: list[dict[str, str]],
    uq_rows: list[dict[str, str]],
    heat_rows: list[dict[str, str]],
    d2_score_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    uq_by_label = {r["qoi_label"]: r for r in uq_rows}
    heat_by_case = {r["case_id"]: r for r in heat_rows}
    d2_transfer = next(r for r in d2_score_rows if r["comparison"] == "D2_vs_M3_transfer")
    d2_tp_offset = as_float(d2_transfer.get("d2_train_tp_offset_K"))
    rows: list[dict[str, object]] = []
    qois = [
        ("Q_wall_W", "upcomer wall heat lane"),
        ("mdot_exchange_positive_outward_proxy_kg_s", "exchange mass-flow proxy"),
        ("tau_recirc_proxy_s", "exchange residence-time proxy"),
        ("wall_core_bulk_temperature_contrast_K", "wall/core bulk temperature contrast"),
    ]
    for qoi, role in qois:
        uq = uq_by_label.get(qoi, {})
        rows.append(
            {
                "bridge_item": qoi,
                "role_for_bulk_to_TP": role,
                "case_count": uq.get("case_count", ""),
                "same_qoi_temporal_uq_status": uq.get("same_qoi_temporal_uq_status", "missing"),
                "mesh_gci_gate_input_ready": uq.get("mesh_gci_gate_input_ready", "false"),
                "production_use_allowed_now": uq.get("production_use_allowed_now", "false"),
                "admission_allowed_now": uq.get("admission_allowed_now", "false"),
                "release_boundary": uq.get("release_boundary", ""),
                "abs_wall_core_over_D2_train_TP_offset": "",
                "mf07_use": "diagnostic_bridge_only_no_bulk_to_TP_coefficient",
            }
        )
    for row in s12_rows:
        heat = heat_by_case.get(row["case_id"], {})
        wall_core = as_float(row.get("delta_T_wall_minus_core_K"))
        ratio = abs(wall_core) / abs(d2_tp_offset) if math.isfinite(wall_core) and math.isfinite(d2_tp_offset) and d2_tp_offset else math.nan
        rows.append(
            {
                "bridge_item": f"{row['case_id']}_exchange_state",
                "role_for_bulk_to_TP": "case-level retained-window exchange state relevant to TP",
                "case_count": 1,
                "same_qoi_temporal_uq_status": "case_row_available",
                "mesh_gci_gate_input_ready": "not_a_mesh_gci_result",
                "production_use_allowed_now": "false",
                "admission_allowed_now": "false",
                "release_boundary": row.get("release_status", ""),
                "abs_wall_core_over_D2_train_TP_offset": ratio if math.isfinite(ratio) else "",
                "mf07_use": (
                    "wall_core_deltaT_K="
                    + row.get("delta_T_wall_minus_core_K", "")
                    + "; heat_flow_status="
                    + heat.get("heat_flow_match_status", "")
                ),
            }
        )
    return rows


def build_missing_inputs() -> list[dict[str, object]]:
    return [
        {
            "missing_input": "released bulk-to-TP formula",
            "needed_for": "turn MF07 thermal Graetz evidence into a train-only smoke correction",
            "current_status": "not_released",
            "consequence": "MF07 cannot emit a coefficient or corrected TP prediction.",
            "next_action": "define formula and variables from source-bounded thermal-development literature/API rows before scoring.",
        },
        {
            "missing_input": "thermal reset status by wall/source path",
            "needed_for": "decide whether local TP sees a developing thermal boundary layer after a reset",
            "current_status": "unknown_until_wall_material_or_heat_path_reset_mapped",
            "consequence": "reset/Graetz coordinates remain diagnostic context.",
            "next_action": "MF08 signed wall-flux branch gate should classify heat-source/loss sign and reset memory.",
        },
        {
            "missing_input": "same-QOI uncertainty for TP projection formula",
            "needed_for": "uncertainty-bound bulk-to-TP offset",
            "current_status": "missing",
            "consequence": "do not admit a projection correction.",
            "next_action": "once a formula exists, run same-QOI UQ on the projected TP offset, not just source proxies.",
        },
        {
            "missing_input": "source/property release for signed heat paths",
            "needed_for": "runtime legality and source-bounded admission",
            "current_status": "not_released",
            "consequence": "do not use realized wallHeatFlux or target temperatures as runtime inputs.",
            "next_action": "attach setup-known Q/sign/cp/property mode with provenance.",
        },
        {
            "missing_input": "S13 mesh/GCI and production release",
            "needed_for": "use upcomer exchange state as more than a diagnostic bridge",
            "current_status": "mesh_gci_ready_to_claim_but_not_executed",
            "consequence": "S13 bridge remains supporting evidence only.",
            "next_action": "execute separate S13 mesh/GCI gate before any production harvest/admission.",
        },
    ]


def build_formula_table() -> list[dict[str, object]]:
    return [
        {
            "formula_or_basis": "hydraulic reset memory",
            "symbolic_form": "x_from_reset/D_h and reset_flag after bend/junction/endpoint",
            "source_family": "Shah; Muzychka and Yovanovich reset/developing-flow evidence as encoded in reset map",
            "repo_source": str(RESET_MAP.relative_to(ROOT)),
            "mf07_use": "eligibility and direction-of-effect context only",
            "admission_status": "no_coefficient_admission",
        },
        {
            "formula_or_basis": "thermal Graetz coordinate",
            "symbolic_form": "Gz = Re Pr D_h / x, carried from source-envelope/developing-branch tables",
            "source_family": "LitRev single-stream developing branch source envelope",
            "repo_source": str(GATED_BRANCH.relative_to(ROOT)),
            "mf07_use": "bulk-to-TP promise screen; no local TP correction formula released",
            "admission_status": "no_coefficient_admission",
        },
        {
            "formula_or_basis": "signed heat source/loss direction",
            "symbolic_form": "heating implies positive local TP offset possible; cooling implies negative local TP offset possible",
            "source_family": "setup/source-envelope sign labels",
            "repo_source": str(SOURCE_ENVELOPE.relative_to(ROOT)),
            "mf07_use": "direction-of-effect comparison against signed TP residuals",
            "admission_status": "diagnostic_only",
        },
        {
            "formula_or_basis": "recirculation/single-stream guard",
            "symbolic_form": "disable ordinary single-stream development where reverse-flow gate fails",
            "source_family": "S13/upcomer recirculation and LitRev branch gate",
            "repo_source": str(GATED_BRANCH.relative_to(ROOT)),
            "mf07_use": "prevents fitting ordinary entrance/development in recirculating spans",
            "admission_status": "guardrail",
        },
    ]


def build_tw_after_tp_gate() -> list[dict[str, object]]:
    return [
        {
            "priority": 1,
            "step": "MF08 signed wall-flux development gate",
            "objective": "separate heating/cooling branch signs and source envelopes before any TP offset formula",
            "exit_condition": "source-bounded signed thermal branches are ready for train-only smoke or fail closed",
            "forbidden": "do not use realized wallHeatFlux as runtime input",
        },
        {
            "priority": 2,
            "step": "bulk-to-TP train-only smoke only after formula release",
            "objective": "evaluate TP residual movement using predeclared reset/Graetz/source signs",
            "exit_condition": "TP correction has same-QOI UQ and no protected-row tuning",
            "forbidden": "do not tune on validation/holdout/external rows",
        },
        {
            "priority": 3,
            "step": "TW-after-TP residual ownership",
            "objective": "attribute remaining TW error to wall resistance, axial mixing, source placement, or wall/core exchange",
            "exit_condition": "TW residual-owner table references D3/D4/S13/M2 evidence",
            "forbidden": "do not absorb remaining residual into internal Nu",
        },
    ]


def build_runtime_legality() -> list[dict[str, object]]:
    return [
        {
            "item": "reset distance and geometry labels",
            "runtime_allowed": True,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "geometry/reset labels are setup-side context, but no coefficient is released.",
        },
        {
            "item": "signed TP residuals",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "post-solve targets are used only for residual-shape diagnosis.",
        },
        {
            "item": "thermal Graetz correction coefficient",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "formula/source/property/same-QOI UQ are not released.",
        },
        {
            "item": "S13 exchange proxy values",
            "runtime_allowed": False,
            "fit_allowed": False,
            "diagnostic_allowed": True,
            "reason": "temporal UQ exists, but production/mesh-GCI/source-property/admission gates remain closed.",
        },
    ]


def build_source_manifest() -> list[dict[str, object]]:
    paths = [
        (SOURCE_ENVELOPE, "branch source-envelope and signed heat direction"),
        (RESET_MAP, "reset distance and x/D basis"),
        (GATED_BRANCH, "single-stream developing-flow admissibility gate"),
        (BRANCH_SUMMARY, "span-level developing-flow summary"),
        (BL_SCORECARD, "boundary-layer development scorecard"),
        (D2_GATE, "D2 TP projection handoff"),
        (D2_SCORE, "D2 train TP offset magnitude"),
        (SENSOR_ERRORS, "signed TP residuals"),
        (S12_TP_EXCHANGE, "S13/S12 TP exchange evidence"),
        (S13_UQ_SUMMARY, "S13 same-QOI temporal UQ summary"),
        (S13_HEAT_MATCH, "S13 heat-flow match diagnostic"),
    ]
    return [
        {
            "source_path": str(path.relative_to(ROOT)),
            "role": role,
            "exists": path.exists(),
            "mutation": "read_only",
        }
        for path, role in paths
    ]


def build_readme(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - {SOURCE_ENVELOPE}
  - {RESET_MAP}
  - {GATED_BRANCH}
  - {SENSOR_ERRORS}
tags: [mf07, entrance-development, reset, graetz, bulk-to-tp]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - operational_notes/07-26/22/2026-07-22_MF07_ENTRANCE_DEVELOPMENT_AND_RESET_SOURCE_BASIS.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# MF07 Entrance/Development and Reset Source Basis

Decision: `{summary["decision"]}`.

This package continues the D2 TP-first path by joining TP signed residuals to
reset distance, Graetz/development coordinates, source-sign envelopes, and S13
wall/core exchange evidence. It is evidence-only: no coefficient, no corrected
prediction, no final score, and no admission is produced.

Main result:

- Segment classification rows: `{summary["segment_classification_rows"]}`.
- TP residual/reset/Graetz join rows: `{summary["tp_residual_join_rows"]}`.
- Predeclared variants: `{summary["variant_rows"]}`.
- S13 bridge rows: `{summary["s13_bridge_rows"]}`.
- Max S13 wall/core contrast over D2 train TP offset:
  `{summary["max_abs_wall_core_over_D2_train_TP_offset"]}`.
- Train-only smoke ready: `{summary["ready_for_train_only_smoke"]}`.

Interpretation:

- Hydraulic reset/development is useful context but cannot by itself explain a
  bulk-to-TP temperature offset without a coupled pressure/thermal closure.
- Thermal Graetz/development has the right kind of source basis for heated
  spans, but thermal reset labels, same-QOI TP projection UQ, and a released
  formula are still missing.
- S13 exchange evidence is useful as a TP bridge, but the wall/core contrast is
  too small to explain the full D2 TP offset by itself and remains diagnostic
  until mesh/GCI, source/property, and production-use gates pass.

Primary files:

- `segment_classification_table.csv`
- `tp_residual_reset_graetz_join.csv`
- `variant_direction_of_effect.csv`
- `bulk_to_tp_existence_proof_gate.csv`
- `s13_wall_core_tp_bridge_matrix.csv`
- `next_analysis_plan.csv`
- `formula_provenance_table.csv`
- `missing_input_table.csv`
- `tw_after_tp_next_gate.csv`
- `candidate_gate.csv`
- `runtime_legality_matrix.csv`
"""


def build() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    source_rows = read_csv(SOURCE_ENVELOPE)
    reset_rows = read_csv(RESET_MAP)
    gated_rows = read_csv(GATED_BRANCH)
    branch_summary = read_csv(BRANCH_SUMMARY)
    sensor_errors = read_csv(SENSOR_ERRORS)
    s12_rows = read_csv(S12_TP_EXCHANGE)
    s13_uq = read_csv(S13_UQ_SUMMARY)
    s13_heat = read_csv(S13_HEAT_MATCH)
    d2_score_rows = read_csv(D2_SCORE)

    source = summarize_source_envelope(source_rows)
    gated = summarize_gated_branch(gated_rows)
    segment_rows = build_segment_classification(source, gated, reset_rows, branch_summary)
    tp_join = build_tp_join(sensor_errors, source, gated, reset_rows)
    variant_rows = build_variant_table(tp_join, segment_rows)
    s13_bridge = build_s13_bridge(s12_rows, s13_uq, s13_heat, d2_score_rows)
    bulk_to_tp_gate = build_bulk_to_tp_gate(tp_join, segment_rows, s13_bridge)
    next_plan = build_next_analysis_plan()
    missing_rows = build_missing_inputs()
    formula_rows = build_formula_table()
    tw_rows = build_tw_after_tp_gate()
    runtime_rows = build_runtime_legality()
    source_manifest = build_source_manifest()
    candidate_gate = [
        {
            "candidate_or_family": "MF07_entrance_development_reset_bulk_to_TP",
            "ready_for_train_only_smoke": False,
            "coefficient_admission": False,
            "source_property_release": False,
            "protected_scoring_or_final_score": False,
            "decision": "diagnostic_only",
            "reason": "reset/Graetz/source-sign evidence exists, but released bulk-to-TP formula, thermal reset labels, source/property release, and same-QOI TP projection UQ are missing.",
        }
    ]
    no_mutation = [
        {"guardrail": "native_output_mutation", "value": False},
        {"guardrail": "registry_or_admission_mutation", "value": False},
        {"guardrail": "scheduler_action", "value": False},
        {"guardrail": "solver_sampler_harvest_uq_launch", "value": False},
        {"guardrail": "fluid_or_external_repo_mutation", "value": False},
        {"guardrail": "fitting_or_model_selection", "value": False},
        {"guardrail": "final_score", "value": False},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": False},
    ]

    write_csv(
        OUT / "segment_classification_table.csv",
        segment_rows,
        [
            "case_id",
            "span",
            "orientation",
            "heating_cooling_signs",
            "source_rows",
            "fit_target_rows",
            "mean_Re",
            "mean_Pr",
            "mean_Gz",
            "min_Gz",
            "max_Gz",
            "mean_Ri",
            "mean_Ra",
            "x_from_reset_m",
            "L_over_D_from_reset",
            "hydraulic_entrance_L_over_D_0p05Re",
            "thermal_entrance_L_over_D_0p05RePr",
            "thermal_development_indicated_by_L_over_D",
            "hydraulic_reset_status",
            "thermal_reset_status",
            "branch_lane_status",
            "single_stream_allowed_rows",
            "same_qoi_uq_blocked_rows",
            "recirculation_blocked_rows",
            "hydraulic_reset_variant_status",
            "thermal_graetz_variant_status",
            "blocking_reasons",
            "quality_flags",
            "mf07_gate",
        ],
    )
    write_csv(
        OUT / "tp_residual_reset_graetz_join.csv",
        tp_join,
        [
            "tested_model_form_id",
            "case_id",
            "split_group",
            "sensor",
            "prediction_source_segment",
            "mapped_span",
            "target_K",
            "adjusted_predicted_K",
            "signed_error_K",
            "signed_error_percent_of_target",
            "heating_cooling_signs",
            "mean_Re",
            "mean_Pr",
            "mean_Gz",
            "x_from_reset_m",
            "L_over_D_from_reset",
            "thermal_reset_status",
            "single_stream_allowed_rows",
            "recirculation_blocked_rows",
            "expected_thermal_development_direction",
            "direction_match_to_signed_residual",
            "use_boundary",
        ],
    )
    write_csv(
        OUT / "variant_direction_of_effect.csv",
        variant_rows,
        [
            "variant_id",
            "predeclared_basis",
            "source_envelope_rows",
            "direction_of_effect_against_TP",
            "consistent_m3_tp_rows",
            "contradictory_m3_tp_rows",
            "missing_or_blocked_rows",
            "runtime_legal_now",
            "train_only_smoke_ready",
            "decision",
        ],
    )
    write_csv(
        OUT / "s13_wall_core_tp_bridge_matrix.csv",
        s13_bridge,
        [
            "bridge_item",
            "role_for_bulk_to_TP",
            "case_count",
            "same_qoi_temporal_uq_status",
            "mesh_gci_gate_input_ready",
            "production_use_allowed_now",
            "admission_allowed_now",
            "release_boundary",
            "abs_wall_core_over_D2_train_TP_offset",
            "mf07_use",
        ],
    )
    write_csv(
        OUT / "bulk_to_tp_existence_proof_gate.csv",
        bulk_to_tp_gate,
        ["gate", "status", "evidence", "consequence", "release_allowed"],
    )
    write_csv(
        OUT / "next_analysis_plan.csv",
        next_plan,
        ["priority", "task", "analysis", "why_next", "done_when"],
    )
    write_csv(OUT / "formula_provenance_table.csv", formula_rows, ["formula_or_basis", "symbolic_form", "source_family", "repo_source", "mf07_use", "admission_status"])
    write_csv(OUT / "missing_input_table.csv", missing_rows, ["missing_input", "needed_for", "current_status", "consequence", "next_action"])
    write_csv(OUT / "tw_after_tp_next_gate.csv", tw_rows, ["priority", "step", "objective", "exit_condition", "forbidden"])
    write_csv(OUT / "runtime_legality_matrix.csv", runtime_rows, ["item", "runtime_allowed", "fit_allowed", "diagnostic_allowed", "reason"])
    write_csv(OUT / "candidate_gate.csv", candidate_gate, ["candidate_or_family", "ready_for_train_only_smoke", "coefficient_admission", "source_property_release", "protected_scoring_or_final_score", "decision", "reason"])
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_path", "role", "exists", "mutation"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation, ["guardrail", "value"])

    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(ZoneInfo("America/Chicago")).isoformat(timespec="seconds"),
        "decision": "diagnostic_only",
        "segment_classification_rows": len(segment_rows),
        "tp_residual_join_rows": len(tp_join),
        "variant_rows": len(variant_rows),
        "s13_bridge_rows": len(s13_bridge),
        "bulk_to_tp_gate_rows": len(bulk_to_tp_gate),
        "next_analysis_plan_rows": len(next_plan),
        "missing_input_rows": len(missing_rows),
        "ready_for_train_only_smoke": False,
        "thermal_development_indicated_rows": sum(1 for row in segment_rows if row["thermal_development_indicated_by_L_over_D"]),
        "single_stream_precheck_rows": sum(int(row["single_stream_allowed_rows"] or 0) for row in segment_rows),
        "recirculation_blocked_rows": sum(int(row["recirculation_blocked_rows"] or 0) for row in segment_rows),
        "max_abs_wall_core_over_D2_train_TP_offset": max(
            [as_float(row["abs_wall_core_over_D2_train_TP_offset"]) for row in s13_bridge if math.isfinite(as_float(row["abs_wall_core_over_D2_train_TP_offset"]))]
            or [math.nan]
        ),
        "coefficient_admission": False,
        "source_property_release": False,
        "final_score": False,
        "native_output_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_repo_mutation": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT / "README.md").write_text(build_readme(summary))
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2))


if __name__ == "__main__":
    main()
