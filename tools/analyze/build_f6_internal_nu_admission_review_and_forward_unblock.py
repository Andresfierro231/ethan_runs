#!/usr/bin/env python3
"""Build AGENT-425 F6/internal-Nu admission review and unblock package."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-425"
DATE = "2026-07-15"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock")
OUT = ROOT / OUT_REL

AGENT406 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair"
AGENT413 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_blocker_resolution_wave_implementation"
AGENT414 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_downstream_pm5_final_state_refresh"
AGENT421 = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification"

FIT_REVERSE_MAX = 0.02
MATERIAL_REVERSE_MIN = 0.10
FIT_SECONDARY_MAX = 0.20
FIT_RI_MAX = 0.30
MIN_ABS_DELTA_T_K = 0.5
MAX_HEAT_BALANCE_RESIDUAL_FRACTION = 0.10


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fmt(value: Any, precision: int = 10) -> str:
    number = safe_float(value)
    if number is None:
        return "" if value is None else str(value)
    return f"{number:.{precision}g}"


def boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1"}


def h_proxy(row: dict[str, str]) -> float | None:
    q = safe_float(row.get("wallHeatFlux_W_m2"))
    delta_t = safe_float(row.get("delta_T_wall_bulk_K"))
    if q is None or delta_t is None or abs(delta_t) < MIN_ABS_DELTA_T_K:
        return None
    return q / delta_t


def recirculation_band(reverse_area: float | None, reverse_mass: float | None) -> str:
    area = reverse_area or 0.0
    mass = reverse_mass or 0.0
    if area >= MATERIAL_REVERSE_MIN or mass >= MATERIAL_REVERSE_MIN:
        return "material_recirculation_diagnostic_only"
    if area >= FIT_REVERSE_MAX or mass >= FIT_REVERSE_MAX:
        return "weak_or_transition_reverse_validation_only"
    return "single_stream_candidate"


def f6_admission_decision(row: dict[str, str]) -> tuple[str, str, str]:
    required = ("Re", "Pr", "Ri", "Gr", "Ra")
    missing = [field for field in required if safe_float(row.get(field)) is None]
    if missing:
        return (
            "blocked_missing_required_field",
            "no",
            "Missing required nondimensional fields: " + ";".join(missing),
        )
    reverse_area = safe_float(row.get("reverse_area_fraction"))
    reverse_mass = safe_float(row.get("reverse_mass_fraction"))
    secondary = safe_float(row.get("secondary_velocity_fraction"))
    ri = safe_float(row.get("Ri"))
    band = recirculation_band(reverse_area, reverse_mass)
    if band == "material_recirculation_diagnostic_only":
        return (
            "diagnostic_onset_only_material_recirculation_not_f6_fit",
            "no",
            "Reverse-flow area or mass fraction is material; true single-stream f_D/F6 fitting is invalid.",
        )
    if band == "weak_or_transition_reverse_validation_only":
        return (
            "validation_only_reverse_flow_not_f6_fit",
            "no",
            "Reverse-flow area or mass fraction exceeds the fit threshold.",
        )
    if secondary is not None and secondary >= FIT_SECONDARY_MAX:
        return (
            "diagnostic_secondary_flow_not_f6_fit",
            "no",
            "Secondary velocity fraction exceeds the fit threshold.",
        )
    if ri is not None and ri >= FIT_RI_MAX:
        return (
            "diagnostic_mixed_convection_not_f6_fit",
            "no",
            "Ri exceeds the single-stream F6 fit threshold.",
        )
    return (
        "fit_candidate_pending_pressure_admission",
        "yes",
        "Passes PM5 single-stream thresholds; still requires admitted pressure residual evidence before fitting.",
    )


def internal_nu_decision(row: dict[str, str], heat_balance_status: str = "") -> tuple[str, str, str, float | None]:
    if not boolish(row.get("wallHeatFlux_available")):
        return ("blocked_missing_wallHeatFlux", "no", "wallHeatFlux is absent.", None)
    proxy = h_proxy(row)
    delta_t = safe_float(row.get("delta_T_wall_bulk_K"))
    if proxy is None:
        return (
            "blocked_small_or_missing_wall_bulk_deltaT",
            "no",
            "wallHeatFlux exists, but |Twall-Tbulk| is too small or missing for stable h_proxy.",
            None,
        )
    if proxy <= 0:
        return (
            "diagnostic_sign_review_required",
            "no",
            "q''/(Twall-Tbulk) is non-positive under the current sign convention.",
            proxy,
        )
    reverse_area = safe_float(row.get("reverse_area_fraction"))
    reverse_mass = safe_float(row.get("reverse_mass_fraction"))
    ri = safe_float(row.get("Ri"))
    secondary = safe_float(row.get("secondary_velocity_fraction"))
    band = recirculation_band(reverse_area, reverse_mass)
    if band == "material_recirculation_diagnostic_only":
        return (
            "diagnostic_section_effective_material_recirculation_not_fit",
            "no",
            "h_proxy is positive, but material reverse flow invalidates single-stream fitted Nu.",
            proxy,
        )
    if band == "weak_or_transition_reverse_validation_only":
        return (
            "validation_only_reverse_flow_not_fit",
            "no",
            "h_proxy is positive, but reverse flow exceeds the fit threshold.",
            proxy,
        )
    if ri is not None and ri >= FIT_RI_MAX:
        return (
            "diagnostic_mixed_convection_not_single_stream_fit",
            "no",
            "Ri exceeds the single-stream internal-Nu fit threshold.",
            proxy,
        )
    if secondary is not None and secondary >= FIT_SECONDARY_MAX:
        return (
            "diagnostic_secondary_flow_not_single_stream_fit",
            "no",
            "Secondary velocity fraction exceeds the internal-Nu fit threshold.",
            proxy,
        )
    if heat_balance_status and heat_balance_status != "pass":
        return (
            "blocked_heat_balance_or_sign_gate",
            "no",
            "The segment-level sign/heat-balance gate has not admitted this row family.",
            proxy,
        )
    if delta_t is not None and abs(delta_t) >= MIN_ABS_DELTA_T_K:
        return (
            "fit_candidate_pending_heat_balance_and_mesh_admission",
            "yes",
            "Passes local PM5 field/sign/recirculation thresholds; still requires heat-balance, mesh/time, and row admission.",
            proxy,
        )
    return ("blocked_unknown_internal_nu_gate", "no", "Internal-Nu gate was not classifiable.", proxy)


def build_f6_onset_scorecard(metrics: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in metrics:
        status, fit_now, reason = f6_admission_decision(row)
        reverse_area = safe_float(row.get("reverse_area_fraction"))
        reverse_mass = safe_float(row.get("reverse_mass_fraction"))
        rows.append(
            {
                "case_key": row.get("case_key", ""),
                "case_role": row.get("case_role", ""),
                "plane_location": row.get("plane_location", ""),
                "span": row.get("span", ""),
                "representative_time_s": row.get("representative_time_s", ""),
                "Re": row.get("Re", ""),
                "Pr": row.get("Pr", ""),
                "Ri": row.get("Ri", ""),
                "Gr": row.get("Gr", ""),
                "Ra": row.get("Ra", ""),
                "reverse_area_fraction": row.get("reverse_area_fraction", ""),
                "reverse_mass_fraction": row.get("reverse_mass_fraction", ""),
                "secondary_velocity_fraction": row.get("secondary_velocity_fraction", ""),
                "recirculation_band": recirculation_band(reverse_area, reverse_mass),
                "f6_onset_review_class": status,
                "fit_admissible_now": fit_now,
                "single_stream_f_D_allowed": "yes" if fit_now == "yes" else "no",
                "allowed_use_now": "pressure_onset_diagnostic" if fit_now == "no" else "candidate_after_pressure_admission",
                "reason": reason,
                "source_metric_file": rel(AGENT406 / "resampled_pm5_matched_plane_metrics.csv"),
            }
        )
    return rows


def build_f6_fit_candidate_table(f6_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [row for row in f6_rows if row["fit_admissible_now"] == "yes"]
    if candidates:
        return [
            {
                "candidate_id": f"{row['case_key']}__{row['plane_location']}",
                "case_key": row["case_key"],
                "case_role": row["case_role"],
                "span": row["span"],
                "status": "candidate_pending_pressure_admission",
                "why_not_final": "PM5 row passes local single-stream thresholds, but final F6 still requires admitted pressure residual rows and holdout improvement.",
                "next_gate": "Run bounded F6 pressure scorecard with train/holdout split and no thermal fitting.",
                "source": row["source_metric_file"],
            }
            for row in candidates
        ]
    return [
        {
            "candidate_id": "none_current_pm5",
            "case_key": "corrected_pm5_salt2_salt4",
            "case_role": "mixed_training_holdout",
            "span": "upcomer_matched_planes",
            "status": "zero_fit_candidates",
            "why_not_final": "All 12 PM5 rows fail single-stream F6 fit gates, primarily material reverse flow and strong mixed-convection Ri.",
            "next_gate": "Use current rows for pressure/onset diagnostics only; obtain non-recirculating or explicitly recirculation-modeled pressure evidence before F6 fitting.",
            "source": rel(AGENT406 / "resampled_pm5_matched_plane_metrics.csv"),
        }
    ]


def build_internal_nu_h_proxy_review(metrics: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in metrics:
        status, fit_now, reason, proxy = internal_nu_decision(row)
        reverse_area = safe_float(row.get("reverse_area_fraction"))
        reverse_mass = safe_float(row.get("reverse_mass_fraction"))
        positive_proxy = "yes" if proxy is not None and proxy > 0 else "no"
        rows.append(
            {
                "case_key": row.get("case_key", ""),
                "case_role": row.get("case_role", ""),
                "plane_location": row.get("plane_location", ""),
                "span": row.get("span", ""),
                "bulk_T_K": row.get("bulk_T_K", ""),
                "wall_T_K": row.get("wall_T_K", ""),
                "delta_T_wall_bulk_K": row.get("delta_T_wall_bulk_K", ""),
                "wallHeatFlux_W_m2": row.get("wallHeatFlux_W_m2", ""),
                "h_proxy_W_m2_K": fmt(proxy),
                "h_proxy_positive_under_current_sign": positive_proxy,
                "reverse_area_fraction": row.get("reverse_area_fraction", ""),
                "reverse_mass_fraction": row.get("reverse_mass_fraction", ""),
                "secondary_velocity_fraction": row.get("secondary_velocity_fraction", ""),
                "Ri": row.get("Ri", ""),
                "recirculation_band": recirculation_band(reverse_area, reverse_mass),
                "internal_nu_review_class": status,
                "fit_admissible_now": fit_now,
                "allowed_label_now": "Nu_section_effective_upcomer_diagnostic" if fit_now == "no" else "Nu_fit_candidate_pending_admission",
                "allowed_use_now": "diagnostic_section_effective_only" if fit_now == "no" else "candidate_after_heat_balance_mesh_admission",
                "reason": reason,
                "source_metric_file": rel(AGENT406 / "resampled_pm5_matched_plane_metrics.csv"),
            }
        )
    return rows


def heat_balance_gate_class(row: dict[str, str]) -> tuple[str, str]:
    direction = row.get("wall_vs_enthalpy_direction", "")
    residual = safe_float(row.get("residual_fraction"))
    blockers = row.get("blockers", "")
    if "downcomer" in row.get("segment", "") or "blocked_downcomer_policy" in blockers:
        return ("fail_downcomer_policy", "Downcomer row remains outside current internal-Nu fit policy.")
    if "sign" in blockers or direction == "opposed_direction":
        return ("fail_sign_convention_or_direction", "Sign label/direction is not admitted.")
    if residual is None:
        return ("fail_missing_heat_balance_residual", "Residual fraction is missing.")
    if abs(residual) > MAX_HEAT_BALANCE_RESIDUAL_FRACTION:
        return ("fail_heat_balance_residual", "WallHeatFlux/enthalpy residual exceeds 10 percent.")
    if row.get("internal_nu_fit_allowed", "").lower() != "true":
        return ("validation_only_not_fit_admitted", "Segment passes basic direction/residual checks but is not fit-admitted.")
    return ("pass", "Segment-level sign and heat-balance gate is fit-admitted.")


def build_thermal_sign_heat_balance_gate(thermal_rows: list[dict[str, str]], h_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in thermal_rows:
        gate, reason = heat_balance_gate_class(row)
        rows.append(
            {
                "row_family": "segment_energy_review",
                "case_or_key": row.get("case_id", ""),
                "source_id": row.get("source_id", ""),
                "segment_or_span": row.get("segment", ""),
                "plane_location": "",
                "qoi": row.get("qoi", ""),
                "wallHeatFlux_W": row.get("wallHeatFlux_W", ""),
                "enthalpy_change_W": row.get("enthalpy_change_W", ""),
                "residual_W": row.get("residual_W", ""),
                "residual_fraction": row.get("residual_fraction", ""),
                "wall_vs_enthalpy_direction": row.get("wall_vs_enthalpy_direction", ""),
                "h_proxy_W_m2_K": "",
                "reverse_area_fraction": "",
                "reverse_mass_fraction": "",
                "gate_class": gate,
                "fit_admissible_now": "yes" if gate == "pass" else "no",
                "reason": reason,
                "source_paths": row.get("source_paths", ""),
            }
        )
    for row in h_rows:
        rows.append(
            {
                "row_family": "pm5_local_h_proxy_review",
                "case_or_key": row.get("case_key", ""),
                "source_id": "",
                "segment_or_span": row.get("span", ""),
                "plane_location": row.get("plane_location", ""),
                "qoi": "h_proxy",
                "wallHeatFlux_W": "",
                "enthalpy_change_W": "",
                "residual_W": "",
                "residual_fraction": "",
                "wall_vs_enthalpy_direction": "local_sign_only_no_segment_enthalpy_join",
                "h_proxy_W_m2_K": row.get("h_proxy_W_m2_K", ""),
                "reverse_area_fraction": row.get("reverse_area_fraction", ""),
                "reverse_mass_fraction": row.get("reverse_mass_fraction", ""),
                "gate_class": row.get("internal_nu_review_class", ""),
                "fit_admissible_now": "no",
                "reason": "PM5 h_proxy is a local diagnostic. Segment heat-balance admission still comes from the segment energy-review rows.",
                "source_paths": row.get("source_metric_file", ""),
            }
        )
    return rows


def build_internal_nu_admission_decision(h_rows: list[dict[str, Any]], heat_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positive = sum(row["h_proxy_positive_under_current_sign"] == "yes" for row in h_rows)
    sign_review = sum(row["internal_nu_review_class"] == "diagnostic_sign_review_required" for row in h_rows)
    section_effective = sum("section_effective" in row["internal_nu_review_class"] for row in h_rows)
    heat_pass = sum(row["row_family"] == "segment_energy_review" and row["gate_class"] == "pass" for row in heat_rows)
    return [
        {
            "decision_id": "use_repaired_wall_band_h_proxy",
            "current_decision": "yes_for_diagnostic_review",
            "admitted_fit_rows": 0,
            "diagnostic_rows": len(h_rows),
            "supporting_counts": f"positive_h_proxy={positive}; sign_review_required={sign_review}; section_effective_or_recirculating={section_effective}",
            "why_not_final": "Local h_proxy can be computed, but sign, heat-balance, mesh/time, and recirculation gates still block single-stream Nu fitting.",
            "next_step": "Keep h_proxy rows diagnostic/section-effective until segment energy review and recirculation gates admit rows.",
        },
        {
            "decision_id": "segment_sign_heat_balance",
            "current_decision": "not_admitted",
            "admitted_fit_rows": heat_pass,
            "diagnostic_rows": len([row for row in heat_rows if row["row_family"] == "segment_energy_review"]),
            "supporting_counts": f"segment_gate_pass_rows={heat_pass}",
            "why_not_final": "Current segment rows include sign-label conflict, opposed wallHeatFlux/enthalpy direction, large residual, or downcomer policy blockers.",
            "next_step": "Resolve sign convention and wallHeatFlux-vs-enthalpy residuals before any Nu admission.",
        },
        {
            "decision_id": "single_stream_internal_nu_fit",
            "current_decision": "blocked_zero_fit_candidates",
            "admitted_fit_rows": 0,
            "diagnostic_rows": len(h_rows),
            "supporting_counts": "all current PM5 rows have material reverse flow or sign failure",
            "why_not_final": "Rows with material recirculation cannot be promoted past section-effective diagnostics.",
            "next_step": "Acquire at least three fit-admissible upcomer rows including a non-recirculating anchor, or define a separate bidirectional/section-effective closure.",
        },
    ]


def build_final_forward_v1_unblock_requirements(
    f6_rows: list[dict[str, Any]],
    h_rows: list[dict[str, Any]],
    heat_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    f6_fit = sum(row["fit_admissible_now"] == "yes" for row in f6_rows)
    nu_fit = sum(row["fit_admissible_now"] == "yes" for row in h_rows)
    heat_pass = sum(row["row_family"] == "segment_energy_review" and row["gate_class"] == "pass" for row in heat_rows)
    return [
        {
            "blocker_or_gate": "final_forward_v1",
            "current_state": "blocked_no_go_final_forward_v1_not_admitted",
            "why_blocked_now": "Forward-v1 must be rebuilt from admitted rows only; current hydraulic and internal-Nu evidence is diagnostic/review-ready but not fit-admitted.",
            "current_evidence_count": f"f6_fit_rows={f6_fit}; internal_nu_fit_rows={nu_fit}; thermal_heat_balance_pass_rows={heat_pass}",
            "unblock_requirement": "Admit hydraulic pressure/F6 evidence and admitted thermal/internal-Nu or setup-only thermal boundary evidence, then rerun final gate without realized-CFD runtime leakage.",
            "next_work_product": "final_forward_v1_gate_rebuild_after_admission",
            "may_use_current_pm5_rows": "diagnostic_only",
        },
        {
            "blocker_or_gate": "final_hydraulic_residual",
            "current_state": "blocked_not_final",
            "why_blocked_now": "No fit-admitted raw pressure or F6 rows exist; PM5 rows are recirculating/onset diagnostics.",
            "current_evidence_count": f"f6_fit_rows={f6_fit}; f6_diagnostic_rows={len(f6_rows)}",
            "unblock_requirement": "Admit pressure rows that separate straight friction, component K, reset/development, cluster/branch-apparent loss, and recirculation/onset terms.",
            "next_work_product": "bounded_hydraulic_pressure_scorecard_on_admitted_rows",
            "may_use_current_pm5_rows": "pressure_onset_diagnostic_only",
        },
        {
            "blocker_or_gate": "internal_nu",
            "current_state": "unlocked_for_review_not_admitted",
            "why_blocked_now": "wallHeatFlux exists and h_proxy is computable, but sign/heat-balance and material recirculation prevent single-stream Nu fitting.",
            "current_evidence_count": f"local_h_proxy_rows={len(h_rows)}; positive_h_proxy_rows={sum(row['h_proxy_positive_under_current_sign'] == 'yes' for row in h_rows)}; fit_rows={nu_fit}",
            "unblock_requirement": "Pass sign convention, wallHeatFlux/enthalpy residual <=10%, mesh/time uncertainty, and reverse area/mass <0.02; otherwise keep rows section-effective diagnostics.",
            "next_work_product": "thermal_sign_heat_balance_resolution_then_nu_gate",
            "may_use_current_pm5_rows": "diagnostic_section_effective_only",
        },
        {
            "blocker_or_gate": "move_past_recirculation",
            "current_state": "blocked_for_single_stream_coefficients",
            "why_blocked_now": "Material reverse-flow rows do not have a unique single upstream stream for true Nu/f_D/K coefficients.",
            "current_evidence_count": f"material_recirculation_rows={sum(row['recirculation_band'] == 'material_recirculation_diagnostic_only' for row in f6_rows)}",
            "unblock_requirement": "Either obtain non-recirculating/transition rows that pass thresholds, or explicitly adopt a bidirectional/section-effective model form with separate admission rules.",
            "next_work_product": "low_re_transition_hydraulic_and_wall_band_case_design",
            "may_use_current_pm5_rows": "regime/onset evidence",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    paths = [
        (AGENT406 / "summary.json", "PM5 repaired wall-band/plane final summary"),
        (AGENT406 / "resampled_pm5_matched_plane_metrics.csv", "primary PM5 metrics with wallHeatFlux and Re/Pr/Ri/Gr/Ra"),
        (AGENT413 / "pm5_f6_admission_readiness.csv", "prior PM5 admission-readiness review"),
        (AGENT413 / "thermal_internal_nu_admission_review.csv", "segment sign/heat-balance/internal-Nu gate evidence"),
        (AGENT413 / "remaining_blocker_execution_sequence.csv", "remaining forward-v1 blocker execution sequence"),
        (AGENT414 / "f6_pm5_row_readiness.csv", "downstream F6 PM5 row readiness"),
        (AGENT414 / "internal_nu_pm5_row_readiness.csv", "downstream internal-Nu h_proxy readiness"),
        (AGENT421 / "hydraulic_admission_final_decisions.csv", "final hydraulic residual diagnostic lane verification"),
    ]
    return [{"path": rel(path), "role": role, "exists": str(path.exists()).lower()} for path, role in paths]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(AGENT406 / 'resampled_pm5_matched_plane_metrics.csv')}
  - {rel(AGENT413 / 'thermal_internal_nu_admission_review.csv')}
  - {rel(AGENT414 / 'f6_pm5_row_readiness.csv')}
  - {rel(AGENT421 / 'hydraulic_admission_final_decisions.csv')}
tags: [f6, internal-nu, hydraulic, forward-v1, admission]
related:
  - operational_notes/maps/friction-closures.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: {TASK}
date: {DATE}
role: Coordinator/Hydraulics/Internal-Nu/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6/Internal-Nu Admission Review And Forward Unblock

## Result

This package answers the current unblock question from existing evidence only.
The repaired PM5 wall-band VTK state unlocks review, not final admission.

- PM5 rows reviewed: `{summary['pm5_rows']}`.
- PM5 rows with wallHeatFlux: `{summary['pm5_wallHeatFlux_rows']}`.
- F6 fit-admissible rows now: `{summary['f6_fit_admissible_rows']}`.
- Internal-Nu fit-admissible rows now: `{summary['internal_nu_fit_admissible_rows']}`.
- Positive local `h_proxy` rows: `{summary['positive_h_proxy_rows']}`.
- Segment sign/heat-balance pass rows: `{summary['segment_heat_balance_pass_rows']}`.
- Final forward-v1 status: `{summary['final_forward_v1_status']}`.
- Final hydraulic residual status: `{summary['final_hydraulic_residual_status']}`.

## Interpretation

Yes, repaired wall-band `wallHeatFlux` can be used to compute
`h_proxy = q''/(Twall - Tbulk)` for diagnostic review. It cannot by itself
admit internal Nu. Rows must still pass sign convention, wallHeatFlux-vs-
enthalpy heat balance, recirculation, mesh/time, and residual-ownership gates.

Current PM5 rows remain diagnostic/section-effective because reverse mass is
material and Ri is strongly mixed-convective. Rows with positive `h_proxy` are
useful diagnostics, but not single-stream fitted Nu rows. Rows with negative
`h_proxy` under the current sign convention require sign review before even
diagnostic interpretation beyond the local calculation.

## Recommended Next Run/Edit

1. Do not run a final forward-v1 scorecard from these rows yet.
2. Use `f6_onset_scorecard.csv` as pressure/onset diagnostic evidence only.
3. Resolve the thermal sign/heat-balance gate before Nu fitting.
4. To move past recirculation for true coefficients, obtain non-recirculating or
   near-transition matched-plane/pressure rows, or explicitly create a separate
   bidirectional/section-effective closure path with its own admission gate.

No native CFD solver outputs, registry/admission state, scheduler state,
generated indexes, or external Fluid code were mutated.

## Outputs

- `f6_onset_scorecard.csv`
- `f6_fit_candidate_table.csv`
- `internal_nu_h_proxy_review.csv`
- `thermal_sign_heat_balance_gate.csv`
- `internal_nu_admission_decision.csv`
- `final_forward_v1_unblock_requirements.csv`
- `source_manifest.csv`
- `summary.json`
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    metrics = read_csv(AGENT406 / "resampled_pm5_matched_plane_metrics.csv")
    thermal = read_csv(AGENT413 / "thermal_internal_nu_admission_review.csv")

    f6_rows = build_f6_onset_scorecard(metrics)
    f6_candidates = build_f6_fit_candidate_table(f6_rows)
    h_rows = build_internal_nu_h_proxy_review(metrics)
    heat_rows = build_thermal_sign_heat_balance_gate(thermal, h_rows)
    nu_decisions = build_internal_nu_admission_decision(h_rows, heat_rows)
    unblock_rows = build_final_forward_v1_unblock_requirements(f6_rows, h_rows, heat_rows)
    source_rows = build_source_manifest()

    write_csv(
        OUT / "f6_onset_scorecard.csv",
        f6_rows,
        [
            "case_key",
            "case_role",
            "plane_location",
            "span",
            "representative_time_s",
            "Re",
            "Pr",
            "Ri",
            "Gr",
            "Ra",
            "reverse_area_fraction",
            "reverse_mass_fraction",
            "secondary_velocity_fraction",
            "recirculation_band",
            "f6_onset_review_class",
            "fit_admissible_now",
            "single_stream_f_D_allowed",
            "allowed_use_now",
            "reason",
            "source_metric_file",
        ],
    )
    write_csv(
        OUT / "f6_fit_candidate_table.csv",
        f6_candidates,
        ["candidate_id", "case_key", "case_role", "span", "status", "why_not_final", "next_gate", "source"],
    )
    write_csv(
        OUT / "internal_nu_h_proxy_review.csv",
        h_rows,
        [
            "case_key",
            "case_role",
            "plane_location",
            "span",
            "bulk_T_K",
            "wall_T_K",
            "delta_T_wall_bulk_K",
            "wallHeatFlux_W_m2",
            "h_proxy_W_m2_K",
            "h_proxy_positive_under_current_sign",
            "reverse_area_fraction",
            "reverse_mass_fraction",
            "secondary_velocity_fraction",
            "Ri",
            "recirculation_band",
            "internal_nu_review_class",
            "fit_admissible_now",
            "allowed_label_now",
            "allowed_use_now",
            "reason",
            "source_metric_file",
        ],
    )
    write_csv(
        OUT / "thermal_sign_heat_balance_gate.csv",
        heat_rows,
        [
            "row_family",
            "case_or_key",
            "source_id",
            "segment_or_span",
            "plane_location",
            "qoi",
            "wallHeatFlux_W",
            "enthalpy_change_W",
            "residual_W",
            "residual_fraction",
            "wall_vs_enthalpy_direction",
            "h_proxy_W_m2_K",
            "reverse_area_fraction",
            "reverse_mass_fraction",
            "gate_class",
            "fit_admissible_now",
            "reason",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "internal_nu_admission_decision.csv",
        nu_decisions,
        [
            "decision_id",
            "current_decision",
            "admitted_fit_rows",
            "diagnostic_rows",
            "supporting_counts",
            "why_not_final",
            "next_step",
        ],
    )
    write_csv(
        OUT / "final_forward_v1_unblock_requirements.csv",
        unblock_rows,
        [
            "blocker_or_gate",
            "current_state",
            "why_blocked_now",
            "current_evidence_count",
            "unblock_requirement",
            "next_work_product",
            "may_use_current_pm5_rows",
        ],
    )
    write_csv(OUT / "source_manifest.csv", source_rows, ["path", "role", "exists"])

    f6_counts = Counter(row["f6_onset_review_class"] for row in f6_rows)
    nu_counts = Counter(row["internal_nu_review_class"] for row in h_rows)
    heat_counts = Counter(row["gate_class"] for row in heat_rows if row["row_family"] == "segment_energy_review")
    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "pm5_rows": len(metrics),
        "pm5_wallHeatFlux_rows": sum(boolish(row.get("wallHeatFlux_available")) for row in metrics),
        "f6_fit_admissible_rows": sum(row["fit_admissible_now"] == "yes" for row in f6_rows),
        "f6_review_class_counts": dict(sorted(f6_counts.items())),
        "internal_nu_fit_admissible_rows": sum(row["fit_admissible_now"] == "yes" for row in h_rows),
        "internal_nu_review_class_counts": dict(sorted(nu_counts.items())),
        "positive_h_proxy_rows": sum(row["h_proxy_positive_under_current_sign"] == "yes" for row in h_rows),
        "segment_heat_balance_pass_rows": sum(row["row_family"] == "segment_energy_review" and row["gate_class"] == "pass" for row in heat_rows),
        "segment_heat_balance_gate_counts": dict(sorted(heat_counts.items())),
        "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
        "final_hydraulic_residual_status": "blocked_not_final",
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_mutated": False,
        "external_fluid_mutated": False,
        "generated_index_refreshed": False,
        "outputs": [
            "README.md",
            "f6_onset_scorecard.csv",
            "f6_fit_candidate_table.csv",
            "internal_nu_h_proxy_review.csv",
            "thermal_sign_heat_balance_gate.csv",
            "internal_nu_admission_decision.csv",
            "final_forward_v1_unblock_requirements.csv",
            "source_manifest.csv",
            "summary.json",
        ],
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
