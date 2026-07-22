#!/usr/bin/env python3
"""Build a fail-closed recirculation/onset evidence packet for thesis writing."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-THESIS-STUDY-RECIRCULATION-FRACTION-ONSET-EVIDENCE-PACKET-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet"
)

VELOCITY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_velocity_magnitude_pictures"
SEGMENT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_s14_recirc_cv_segmentation_preflight"
)
S9 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence"
)
PHASE4 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"
)
S13_LIMITED = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis"
)
S13_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
)
S13_GCI = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation"
)
S13_MEDFINE = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_medium_fine_same_label_sampling"
)

CASE_ORDER = ["salt_2", "salt_3", "salt_4"]
CASE_KEY = {
    "salt_2": "salt2_jin_nominal_continuation",
    "salt_3": "salt3_jin_nominal_continuation",
    "salt_4": "salt4_jin_nominal_continuation",
}
SOURCE_ID = {
    "salt_2": "val_salt_test_2_coarse_mesh_laminar",
    "salt_3": "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "salt_4": "viscosity_screening_salt_test_4_jin_coarse_mesh",
}


def rel(path: Path) -> str:
    if path.is_absolute() and not str(path).startswith(str(ROOT)):
        return str(path)
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def f(value: str | float | None) -> float | None:
    if value in (None, "", "missing"):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: float | None) -> str:
    return "" if value is None else f"{value:.12g}"


def bool_text(value: bool) -> str:
    return str(value).lower()


def source_manifest_rows() -> list[dict[str, str]]:
    paths = [
        (VELOCITY / "shared_velocity_ranges.csv", "common velocity color/scale range"),
        (VELOCITY / "output_manifest.csv", "velocity figure file manifest"),
        (VELOCITY / "y_velocity_side_z_status.json", "y-velocity render status"),
        (VELOCITY / "velocity_magnitude_side_z_status.json", "velocity-magnitude render status"),
        (SEGMENT / "recirc_segmentation_case_summary.csv", "validated cell-VTK reverse-flow topology preflight"),
        (SEGMENT / "recirc_component_summary.csv", "reverse-flow component fragmentation evidence"),
        (S9 / "onset_regime_visual_table.csv", "onset visual and recirculation-proxy rows"),
        (PHASE4 / "upcomer_exchange_cell_readiness.csv", "ordinary closure disable and exchange-cell blocker rows"),
        (S13_LIMITED / "s13_exchange_trend_table.csv", "S13 current-coarse exchange/tau diagnostic proxies"),
        (S13_UQ / "same_qoi_temporal_uq_summary.csv", "same-QOI temporal UQ for current coarse S13 rows"),
        (S13_GCI / "same_label_mesh_family_generated_rows.csv", "current coarse exact-label rows and mesh/GCI block"),
        (S13_MEDFINE / "sampling_command_contract.csv", "medium/fine terminal sampler contract"),
    ]
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": bool_text(path.exists()),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path, role in paths
    ]


def velocity_figure_rows() -> list[dict[str, str]]:
    ranges = {row["family"]: row for row in read_csv(VELOCITY / "shared_velocity_ranges.csv")}
    manifest = read_csv(VELOCITY / "output_manifest.csv")
    png_by_family_source = {
        (row["family"], row["source_id"]): row
        for row in manifest
        if row.get("format") == "png" and row.get("exists") == "true"
    }
    y_status = read_json(VELOCITY / "y_velocity_side_z_status.json")
    mag_status = read_json(VELOCITY / "velocity_magnitude_side_z_status.json")
    rows: list[dict[str, str]] = []
    for case_id in CASE_ORDER:
        source_id = SOURCE_ID[case_id]
        y_range = ranges.get("y_velocity_side_z", {})
        mag_range = ranges.get("velocity_magnitude_side_z", {})
        y_png = png_by_family_source.get(("y_velocity_side_z", source_id), {})
        mag_png = png_by_family_source.get(("velocity_magnitude_side_z", source_id), {})
        y_min = f(y_range.get("color_min"))
        y_max = f(y_range.get("color_max"))
        max_downward = abs(y_min) if y_min is not None and y_min < 0 else None
        rows.append(
            {
                "case_id": case_id,
                "source_id": source_id,
                "y_velocity_png": y_png.get("path", ""),
                "velocity_magnitude_png": mag_png.get("path", ""),
                "y_velocity_color_min_m_s": fmt(y_min),
                "y_velocity_color_max_m_s": fmt(y_max),
                "max_downward_velocity_visual_bound_m_s": fmt(max_downward),
                "velocity_magnitude_color_max_m_s": mag_range.get("color_max", ""),
                "shared_range_basis": "common_side_z_render_range",
                "rendered_count_y_velocity": str(y_status.get("rendered_count", "")),
                "failed_count_y_velocity": str(y_status.get("failed_count", "")),
                "rendered_count_velocity_magnitude": str(mag_status.get("rendered_count", "")),
                "failed_count_velocity_magnitude": str(mag_status.get("failed_count", "")),
                "claim_status": (
                    "diagnostic_common_range_visual_bound"
                    if y_png and mag_png and max_downward is not None
                    else "blocked_missing_common_range_or_png"
                ),
                "admission_allowed": "false",
            }
        )
    return rows


def reverse_topology_rows() -> list[dict[str, str]]:
    seg_rows = {row["case_id"]: row for row in read_csv(SEGMENT / "recirc_segmentation_case_summary.csv")}
    out: list[dict[str, str]] = []
    for case_id in CASE_ORDER:
        row = seg_rows.get(case_id, {})
        roi = f(row.get("right_leg_roi_cells"))
        reverse = f(row.get("reverse_candidate_cells"))
        largest_cells = f(row.get("largest_component_cells"))
        reverse_fraction = reverse / roi if roi and reverse is not None else None
        largest_roi_fraction = largest_cells / roi if roi and largest_cells is not None else None
        out.append(
            {
                "case_id": case_id,
                "cell_vtk": row.get("cell_vtk", ""),
                "right_leg_roi_cells": row.get("right_leg_roi_cells", ""),
                "reverse_candidate_cells": row.get("reverse_candidate_cells", ""),
                "reverse_candidate_fraction_of_right_leg_roi": fmt(reverse_fraction),
                "largest_component_cells": row.get("largest_component_cells", ""),
                "largest_component_fraction_of_reverse_candidates": row.get("largest_component_fraction", ""),
                "largest_component_fraction_of_right_leg_roi": fmt(largest_roi_fraction),
                "dominant_axis": row.get("throughflow_axis", ""),
                "dominant_axis_sign": row.get("dominant_axis_sign", ""),
                "mask_csv": row.get("mask_csv", ""),
                "topology_release_status": row.get("release_status", "missing"),
                "blocking_reason": row.get("blocking_reason", "missing reverse-flow topology row"),
                "closed_recirc_volume_claim_allowed": "false",
                "recirculation_fraction_claim_allowed": "false",
                "proxy_use_allowed": "true" if row else "false",
            }
        )
    return out


def onset_proxy_rows() -> list[dict[str, str]]:
    visual = read_csv(S9 / "onset_regime_visual_table.csv")
    readiness = read_csv(PHASE4 / "upcomer_exchange_cell_readiness.csv")
    visual_by_key = {row["case_key"]: row for row in visual}
    readiness_by_key = {
        (row["case_key"], row["feature_or_span"]): row
        for row in readiness
        if row.get("case_key") in CASE_KEY.values()
    }
    rows: list[dict[str, str]] = []
    for case_id in CASE_ORDER:
        key = CASE_KEY[case_id]
        visual_row = visual_by_key.get(key, {})
        span_rows = [
            readiness_by_key.get((key, "upcomer_inlet"), {}),
            readiness_by_key.get((key, "upcomer_mid"), {}),
            readiness_by_key.get((key, "upcomer_outlet"), {}),
        ]
        reverse_values = [f(row.get("reverse_area_fraction")) for row in span_rows]
        mass_values = [f(row.get("reverse_mass_fraction")) for row in span_rows]
        secondary_values = [f(row.get("secondary_flow_intensity")) for row in span_rows]
        rows.append(
            {
                "case_id": case_id,
                "case_key": key,
                "recirculation_visual_label": visual_row.get("recirculation_visual_label", "missing"),
                "max_reverse_area_fraction_proxy": fmt(max(v for v in reverse_values if v is not None) if any(v is not None for v in reverse_values) else f(visual_row.get("max_reverse_area_fraction"))),
                "max_reverse_mass_fraction_proxy": fmt(max(v for v in mass_values if v is not None) if any(v is not None for v in mass_values) else f(visual_row.get("max_reverse_mass_fraction"))),
                "max_secondary_flow_intensity_proxy": fmt(max(v for v in secondary_values if v is not None) if any(v is not None for v in secondary_values) else f(visual_row.get("max_secondary_flow_intensity"))),
                "proxy_basis": "matched_plane_upcomer_or_hybrid_feature_scorecard_not_closed_cv_fraction",
                "ordinary_upcomer_closure_allowed": "false",
                "exchange_cell_coefficient_allowed": "false",
                "dominant_blockers": visual_row.get("dominant_blockers", "missing"),
                "claim_status": "diagnostic_onset_proxy_not_fraction_admission" if visual_row else "blocked_missing_onset_proxy_row",
                "source_paths": visual_row.get("source_paths", rel(PHASE4 / "upcomer_exchange_cell_readiness.csv")),
            }
        )
    return rows


def exchange_tau_rows() -> list[dict[str, str]]:
    trend = {row["case_id"]: row for row in read_csv(S13_LIMITED / "s13_exchange_trend_table.csv")}
    qwall_rows = read_csv(S13_GCI / "same_label_mesh_family_generated_rows.csv")
    qwall_by_case = {
        row["case_id"]: row
        for row in qwall_rows
        if row.get("qoi_label") == "Q_wall_W" and row.get("mesh_level") == "current_coarse_continuation"
    }
    out: list[dict[str, str]] = []
    for case_id in CASE_ORDER:
        row = trend.get(case_id, {})
        qwall = qwall_by_case.get(case_id, {})
        out.append(
            {
                "case_id": case_id,
                "time_window_s": row.get("time_window_s", qwall.get("target_time_window_s", "")),
                "V_recirc_proxy_m3": row.get("seeded_cv_volume_m3", ""),
                "mdot_exchange_positive_outward_proxy_kg_s": row.get("mdot_exchange_positive_outward_proxy_kg_s", ""),
                "mdot_exchange_net_proxy_kg_s": row.get("mdot_exchange_net_proxy_kg_s", ""),
                "tau_recirc_proxy_s": row.get("tau_recirc_proxy_s", ""),
                "wall_core_bulk_temperature_contrast_K": row.get("delta_T_wall_minus_core_K", ""),
                "source_side_q_net_W": row.get("source_side_q_net_W", ""),
                "direct_Q_wall_W": qwall.get("target_value", ""),
                "qwall_label_basis": "direct_Q_wall_W_same_label_current_coarse" if qwall else "missing",
                "temporal_uq_status": "same_qoi_neighbor_uq_executed_current_coarse",
                "mesh_gci_status": "blocked_medium_fine_exact_label_rows_pending",
                "production_harvest_allowed": "false",
                "coefficient_admission_allowed": "false",
                "claim_status": "diagnostic_current_coarse_exchange_tau_proxy" if row else "blocked_missing_s13_trend_row",
            }
        )
    return out


def qoi_uq_rows() -> list[dict[str, str]]:
    rows = read_csv(S13_UQ / "same_qoi_temporal_uq_summary.csv")
    for row in rows:
        row["strong_claim_allowed_now"] = "false"
        row["required_next_gate"] = "same-label medium/fine rows and mesh/GCI disposition"
    return rows


def availability_rows() -> list[dict[str, str]]:
    velocity_rows = velocity_figure_rows()
    topology_rows = reverse_topology_rows()
    exchange_rows = exchange_tau_rows()
    uq_rows = qoi_uq_rows()
    return [
        {
            "evidence_item": "improved upcomer composite figures",
            "available_rows": str(sum(row["claim_status"] == "diagnostic_common_range_visual_bound" for row in velocity_rows)),
            "status": "available_diagnostic",
            "use_allowed": "caption_and_visual_context_only",
            "fail_closed_reason": "",
        },
        {
            "evidence_item": "max downward y-velocity visual bound",
            "available_rows": str(sum(bool(row["max_downward_velocity_visual_bound_m_s"]) for row in velocity_rows)),
            "status": "available_visual_bound",
            "use_allowed": "quote as common-render bound, not exact per-cell extrema",
            "fail_closed_reason": "",
        },
        {
            "evidence_item": "reverse-flow candidate fraction",
            "available_rows": str(sum(row["proxy_use_allowed"] == "true" for row in topology_rows)),
            "status": "available_proxy",
            "use_allowed": "reverse-candidate topology proxy only",
            "fail_closed_reason": "",
        },
        {
            "evidence_item": "closed recirculation fraction",
            "available_rows": "0",
            "status": "blocked",
            "use_allowed": "false",
            "fail_closed_reason": "validated cell-VTK segmentation reports fragmented velocity topology; no closed defensible recirculation volume admitted",
        },
        {
            "evidence_item": "S13 exchange/tau proxies",
            "available_rows": str(sum(row["claim_status"] == "diagnostic_current_coarse_exchange_tau_proxy" for row in exchange_rows)),
            "status": "available_diagnostic",
            "use_allowed": "diagnostic current-coarse proxy with same-QOI temporal UQ, no coefficient fit",
            "fail_closed_reason": "",
        },
        {
            "evidence_item": "same-QOI temporal UQ",
            "available_rows": str(len(uq_rows)),
            "status": "available_current_coarse",
            "use_allowed": "temporal stability support only",
            "fail_closed_reason": "",
        },
        {
            "evidence_item": "medium/fine exact-label rows",
            "available_rows": "0",
            "status": "pending_scheduler_sampler",
            "use_allowed": "false",
            "fail_closed_reason": "scheduler-authorized sampler must produce exact-label medium/fine rows before mesh/GCI disposition",
        },
        {
            "evidence_item": "Richardson number for S13 onset packet",
            "available_rows": "0",
            "status": "blocked",
            "use_allowed": "false",
            "fail_closed_reason": "no same-window, same-CV property/temperature/velocity-length basis found in the S13 evidence sources opened for this packet",
        },
    ]


def figure_target_rows() -> list[dict[str, str]]:
    return [
        {
            "target_id": "FIG-RECIRC-01",
            "figure_path": rel(VELOCITY / "figures/composites/y_velocity_side_z_trimmed_composite_labeled.png"),
            "caption_safe_claim": "Common-range side-z y-velocity render shows reverse-flow/onset structure across Salt cases.",
            "required_caveat": "Visual diagnostic only; not a closed recirculation-volume fraction.",
            "exists": bool_text((VELOCITY / "figures/composites/y_velocity_side_z_trimmed_composite_labeled.png").exists()),
        },
        {
            "target_id": "FIG-RECIRC-02",
            "figure_path": rel(VELOCITY / "figures/composites/velocity_magnitude_side_z_trimmed_composite_labeled.png"),
            "caption_safe_claim": "Matched velocity-magnitude render provides a common scale for upcomer speed context.",
            "required_caveat": "Does not by itself define exchange-cell geometry or coefficients.",
            "exists": bool_text((VELOCITY / "figures/composites/velocity_magnitude_side_z_trimmed_composite_labeled.png").exists()),
        },
        {
            "target_id": "TAB-RECIRC-01",
            "figure_path": rel(OUT / "recirculation_onset_metric_table.csv"),
            "caption_safe_claim": "Numeric proxy table reports reverse-candidate fractions and S13 exchange/tau diagnostics with gate labels.",
            "required_caveat": "Closed recirculation fraction, Ri, medium/fine mesh/GCI, and coefficient admission remain blocked.",
            "exists": "true",
        },
    ]


def claim_boundary_rows() -> list[dict[str, str]]:
    return [
        {
            "claim_type": "allowed",
            "claim_text": "The current Salt2/Salt3/Salt4 upcomer evidence supports a recirculation/onset diagnostic narrative.",
            "basis": "common-range velocity figures, reverse-flow topology proxy, and S13 current-coarse exchange/tau rows",
            "limit": "diagnostic and thesis-evidence use only",
        },
        {
            "claim_type": "allowed_with_caveat",
            "claim_text": "Current-coarse S13 exchange/tau proxies vary across Salt2 to Salt4 and have same-QOI temporal UQ support.",
            "basis": "s13_exchange_trend_table plus same_qoi_temporal_uq_summary",
            "limit": "no mesh/GCI disposition until exact-label medium/fine rows exist",
        },
        {
            "claim_type": "forbidden",
            "claim_text": "A closed recirculation fraction has been measured for Salt2/Salt3/Salt4.",
            "basis": "segmentation preflight is fragmented",
            "limit": "must wait for closed or defensible recirculation-volume mask",
        },
        {
            "claim_type": "forbidden",
            "claim_text": "Ordinary upcomer Nu, f_D, component K/F6, or exchange-cell coefficients are admitted.",
            "basis": "ordinary closure and exchange-cell admission gates remain closed",
            "limit": "requires same-label mesh/GCI and coefficient-specific UQ/admission package",
        },
    ]


def no_mutation_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "status": "false"},
        {"guardrail": "registry_or_admission_state_mutated", "status": "false"},
        {"guardrail": "scheduler_or_sampler_launched_by_evidence_packet", "status": "false"},
        {"guardrail": "coefficient_fit_or_admission_performed", "status": "false"},
        {"guardrail": "mesh_gci_disposition_rerun", "status": "false"},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(VELOCITY / "shared_velocity_ranges.csv")}
  - {rel(SEGMENT / "recirc_segmentation_case_summary.csv")}
  - {rel(S13_LIMITED / "s13_exchange_trend_table.csv")}
  - {rel(S13_UQ / "same_qoi_temporal_uq_summary.csv")}
tags: [thesis, recirculation, onset, s13, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/thesis-study-recirculation-fraction-onset-evidence-packet.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics/cfd-pp/Writer/Reviewer/Tester
type: work_product
status: complete
---
# Recirculation/Onset Evidence Packet

Decision: `{summary["decision"]}`.

This packet starts the thesis-facing recirculation/onset evidence chain from
existing improved upcomer composite figures, validated cell-VTK topology
preflight rows, and S13 current-coarse exchange/tau diagnostics.

Defensible now:

- common-range y-velocity visual bound rows: `{summary["velocity_figure_rows"]}`
- reverse-flow topology proxy rows: `{summary["reverse_topology_rows"]}`
- S13 exchange/tau current-coarse proxy rows: `{summary["exchange_tau_rows"]}`
- same-QOI temporal UQ summary rows: `{summary["same_qoi_temporal_uq_rows"]}`

Fail-closed now:

- closed recirculation fraction: no admitted closed recirculation volume
- Richardson number: no same-window, same-CV basis in this packet
- medium/fine mesh/GCI: pending scheduler exact-label sampler
- ordinary upcomer `Nu/f_D/K/F6` and exchange-cell coefficient admission

No native solver outputs, registry/admission state, blocker register, or
mesh/GCI disposition were mutated by this evidence packet.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    velocity_rows = velocity_figure_rows()
    topology_rows = reverse_topology_rows()
    onset_rows = onset_proxy_rows()
    exchange_rows = exchange_tau_rows()
    uq_rows = qoi_uq_rows()
    availability = availability_rows()
    figures = figure_target_rows()
    claims = claim_boundary_rows()
    sources = source_manifest_rows()
    guardrails = no_mutation_rows()

    metric_rows: list[dict[str, str]] = []
    velocity_by_case = {row["case_id"]: row for row in velocity_rows}
    topology_by_case = {row["case_id"]: row for row in topology_rows}
    onset_by_case = {row["case_id"]: row for row in onset_rows}
    exchange_by_case = {row["case_id"]: row for row in exchange_rows}
    for case_id in CASE_ORDER:
        merged = {
            "case_id": case_id,
            **{
                key: topology_by_case[case_id].get(key, "")
                for key in [
                    "reverse_candidate_fraction_of_right_leg_roi",
                    "largest_component_fraction_of_reverse_candidates",
                    "topology_release_status",
                    "closed_recirc_volume_claim_allowed",
                    "recirculation_fraction_claim_allowed",
                ]
            },
            **{
                key: onset_by_case[case_id].get(key, "")
                for key in [
                    "max_reverse_area_fraction_proxy",
                    "max_reverse_mass_fraction_proxy",
                    "max_secondary_flow_intensity_proxy",
                    "ordinary_upcomer_closure_allowed",
                    "exchange_cell_coefficient_allowed",
                ]
            },
            **{
                key: velocity_by_case[case_id].get(key, "")
                for key in ["max_downward_velocity_visual_bound_m_s", "y_velocity_color_min_m_s", "y_velocity_color_max_m_s"]
            },
            **{
                key: exchange_by_case[case_id].get(key, "")
                for key in [
                    "time_window_s",
                    "V_recirc_proxy_m3",
                    "mdot_exchange_positive_outward_proxy_kg_s",
                    "mdot_exchange_net_proxy_kg_s",
                    "tau_recirc_proxy_s",
                    "wall_core_bulk_temperature_contrast_K",
                    "source_side_q_net_W",
                    "direct_Q_wall_W",
                    "mesh_gci_status",
                ]
            },
            "Ri_status": "blocked_missing_same_window_same_cv_basis",
            "production_harvest_allowed": "false",
            "coefficient_admission_allowed": "false",
        }
        metric_rows.append(merged)

    csv_dump(out / "recirculation_onset_metric_table.csv", list(metric_rows[0]), metric_rows)
    csv_dump(out / "velocity_figure_evidence.csv", list(velocity_rows[0]), velocity_rows)
    csv_dump(out / "reverse_flow_topology_proxy.csv", list(topology_rows[0]), topology_rows)
    csv_dump(out / "onset_recirculation_proxy_table.csv", list(onset_rows[0]), onset_rows)
    csv_dump(out / "s13_exchange_tau_proxy_table.csv", list(exchange_rows[0]), exchange_rows)
    csv_dump(out / "same_qoi_temporal_uq_boundary.csv", list(uq_rows[0]), uq_rows)
    csv_dump(out / "evidence_availability_gate.csv", list(availability[0]), availability)
    csv_dump(out / "figure_table_targets.csv", list(figures[0]), figures)
    csv_dump(out / "claim_boundary_table.csv", list(claims[0]), claims)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    csv_dump(out / "no_mutation_guardrails.csv", list(guardrails[0]), guardrails)

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "complete",
        "decision": "recirculation_onset_packet_started_diagnostic_proxies_available_closed_fraction_and_ri_fail_closed",
        "velocity_figure_rows": len(velocity_rows),
        "reverse_topology_rows": len(topology_rows),
        "onset_proxy_rows": len(onset_rows),
        "exchange_tau_rows": len(exchange_rows),
        "same_qoi_temporal_uq_rows": len(uq_rows),
        "closed_recirc_fraction_admitted": False,
        "ri_admitted": False,
        "medium_fine_exact_label_rows_available_now": False,
        "mesh_gci_disposition_allowed_now": False,
        "ordinary_upcomer_closure_admitted": False,
        "exchange_cell_coefficient_admitted": False,
        "native_output_mutation": False,
        "registry_mutation": False,
        "scheduler_launch_by_this_packet": False,
    }
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
