#!/usr/bin/env python3
"""Build AGENT-413 blocker-resolution wave artifacts.

This package consolidates current July 15 evidence without mutating native CFD
outputs or registry admission state. It is intentionally conservative: rows are
made review-ready only when the required fields exist, and no row is promoted to
fit-admitted by this builder.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-15"
TASK = "AGENT-413"
SLUG = "2026-07-15_blocker_resolution_wave_implementation"
OUT_DIR = ROOT / "work_products" / "2026-07" / DATE / SLUG

PM5_METRICS = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/resampled_pm5_matched_plane_metrics.csv"
PM5_VALIDATION = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/resampled_vtk_field_validation.csv"
THERMAL_ADMISSION = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_table.csv"
HYDRAULIC_GATE = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_lead_closure_qoi_hydraulic_postprocess/hydraulic_gate_status_after_pm5.csv"
FORWARD_LEDGER = ROOT / "work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger/row_admission_ledger.csv"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def truthy(value: str) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1"}


def build_pm5_readiness(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for row in rows:
        wall_heat_flux = truthy(row.get("wallHeatFlux_available", ""))
        reverse_mass = float(row.get("reverse_mass_fraction") or 0.0)
        reverse_area = float(row.get("reverse_area_fraction") or 0.0)
        has_dimensionless = all(row.get(name, "") not in {"", "nan", "NaN"} for name in ["Re", "Pr", "Ri", "Gr", "Ra"])
        f6_ready = wall_heat_flux and has_dimensionless
        internal_nu_ready = f6_ready and reverse_mass < 0.25 and reverse_area < 0.25
        if internal_nu_ready:
            internal_status = "review_ready_nonrecirculating"
        else:
            internal_status = "blocked_recirculation_or_policy_review"
        out.append(
            {
                "case_key": row["case_key"],
                "case_role": row.get("case_role", ""),
                "plane_location": row["plane_location"],
                "span": row.get("span", ""),
                "representative_time_s": row.get("representative_time_s", ""),
                "metric_status": row.get("metric_status", ""),
                "wallHeatFlux_available": str(wall_heat_flux).lower(),
                "has_Re_Pr_Ri_Gr_Ra": str(has_dimensionless).lower(),
                "reverse_area_fraction": row.get("reverse_area_fraction", ""),
                "reverse_mass_fraction": row.get("reverse_mass_fraction", ""),
                "secondary_velocity_fraction": row.get("secondary_velocity_fraction", ""),
                "f6_pressure_onset_readiness": "review_ready_not_admitted" if f6_ready else "blocked_missing_fields",
                "internal_nu_readiness": internal_status,
                "admission_class": "review_ready_not_admitted" if f6_ready else "blocked",
                "admission_reason": (
                    "PM5 row has wallHeatFlux and nondimensional fields; downstream F6/onset gate still required."
                    if f6_ready
                    else "PM5 row lacks a required wallHeatFlux or nondimensional field."
                ),
                "source_paths": row.get("source_paths", ""),
            }
        )
    return out


def build_thermal_review(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for row in rows:
        existing = row.get("admission_class", "")
        blockers = row.get("blockers", "")
        fit_eligible = row.get("fit_eligible", "").lower() == "yes"
        if fit_eligible and existing == "fit_admissible":
            review_class = "fit_admissible"
        elif existing == "validation_only":
            review_class = "validation_only"
        elif existing == "blocked":
            review_class = "blocked"
        else:
            review_class = "diagnostic_only"
        internal_nu_allowed = (
            review_class == "fit_admissible"
            and "internal_Nu_residual_absorption_forbidden" not in blockers
            and "recirculation" not in blockers
        )
        out.append(
            {
                "case_id": row.get("case_id", ""),
                "source_id": row.get("source_id", ""),
                "segment": row.get("segment", ""),
                "qoi": row.get("qoi", ""),
                "units": row.get("units", ""),
                "review_admission_class": review_class,
                "internal_nu_fit_allowed": str(internal_nu_allowed).lower(),
                "wallHeatFlux_W": row.get("wallHeatFlux_W", ""),
                "enthalpy_change_W": row.get("enthalpy_change_W", ""),
                "residual_W": row.get("residual_W", ""),
                "residual_fraction": row.get("residual_fraction", ""),
                "wall_vs_enthalpy_direction": row.get("wall_vs_enthalpy_direction", ""),
                "blockers": blockers,
                "guardrail": "do_not_fit_boundary_or_storage_residual_into_internal_Nu",
                "next_action": thermal_next_action(review_class, blockers),
                "source_paths": row.get("source_paths", ""),
            }
        )
    return out


def thermal_next_action(review_class: str, blockers: str) -> str:
    if review_class == "fit_admissible":
        return "eligible_for_downstream_internal_nu_gate"
    if "missing_or_nonfinite" in blockers:
        return "repair_missing_or_nonfinite_metric_before_fit"
    if "downcomer" in blockers:
        return "decide_downcomer_policy_before_interpretation"
    if "sign" in blockers or "opposed_direction" in blockers:
        return "resolve_sign_and_heat_balance_before_fit"
    if "recirculation" in blockers:
        return "keep_section_effective_or_validation_only"
    return "keep_diagnostic_until_admission_gate"


def build_blocker_refresh(pm5_rows: List[Dict[str, object]], thermal_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    pm5_ready = sum(1 for row in pm5_rows if row["f6_pressure_onset_readiness"] == "review_ready_not_admitted")
    pm5_total = len(pm5_rows)
    thermal_fit = sum(1 for row in thermal_rows if row["review_admission_class"] == "fit_admissible")
    return [
        {
            "blocker_id": "closure-qoi-mesh-gci",
            "previous_status": "open",
            "agent413_status": "open_refined",
            "evidence_delta": f"thermal rows reviewed={len(thermal_rows)}, fit_admissible={thermal_fit}",
            "next_resolution_condition": "admit sign/heat-balance/source rows, then rerun publication GCI only on admitted triplets",
        },
        {
            "blocker_id": "thermal-cfd-1d-parity",
            "previous_status": "open",
            "agent413_status": "open_refined",
            "evidence_delta": "internal-Nu residual absorption remains forbidden; boundary lanes stay separate",
            "next_resolution_condition": "setup-only heater/HX/wall boundary scorecards pass validation/holdout without runtime CFD duty",
        },
        {
            "blocker_id": "predictive-heater-cooler-wall-submodels",
            "previous_status": "open",
            "agent413_status": "open_narrowed",
            "evidence_delta": "Fluid hx_ua_multiplier hook implemented; external-boundary dictionary hook already existed",
            "next_resolution_condition": "Salt2-trained HX scalar and boundary dictionaries score Salt3/Salt4 without refit",
        },
        {
            "blocker_id": "upcomer-onset-data-sparsity",
            "previous_status": "open",
            "agent413_status": "open_narrowed",
            "evidence_delta": f"PM5 review-ready rows={pm5_ready}/{pm5_total}",
            "next_resolution_condition": "F6/onset scorecard consumes PM5 rows and classifies onset as observed/bracketed/extrapolated",
        },
        {
            "blocker_id": "fluid-external-boundary-api-gap",
            "previous_status": "open",
            "agent413_status": "partially_resolved_recast",
            "evidence_delta": "external-boundary dictionaries are present; direct predictive HX UA multiplier added in Fluid",
            "next_resolution_condition": "run Fluid setup-only HX/external-boundary scorecard and preserve backward-compatible tests",
        },
        {
            "blocker_id": "f6-friction-re-correction",
            "previous_status": "open",
            "agent413_status": "open_ready_for_scorecard",
            "evidence_delta": "PM5 fields now support bounded F6/onset review; final residual still awaits admitted pressure evidence",
            "next_resolution_condition": "F6/Re candidate improves validation/holdout without hidden global multiplier",
        },
    ]


def build_remaining_sequence() -> List[Dict[str, object]]:
    return [
        {
            "priority": 1,
            "task": "F6_PM5_ONSET_SCORECARD",
            "owner_lane": "repo_local_hydraulic",
            "depends_on": "AGENT-406 complete",
            "action": "Score PM5 rows for reverse-flow/onset/F6 readiness; do not fit final residual.",
            "acceptance": "Each PM5 row is observed/bracketed/extrapolated/rejected with source paths and no runtime cheat.",
        },
        {
            "priority": 2,
            "task": "THERMAL_SIGN_HEAT_BALANCE_GATE",
            "owner_lane": "repo_local_thermal",
            "depends_on": "thermal admission rows",
            "action": "Resolve sign/heat-balance/downcomer/missing-Nu row classes.",
            "acceptance": "Every thermal QOI is fit_admissible, validation_only, diagnostic_only, or blocked.",
        },
        {
            "priority": 3,
            "task": "HX_UA_SETUP_ONLY_SCORECARD",
            "owner_lane": "external_fluid_plus_repo_scorecard",
            "depends_on": "Fluid hx_ua_multiplier tests",
            "action": "Fit hx_ua_multiplier on Salt2 only; score Salt3/Salt4 without refit.",
            "acceptance": "No CFD cooler duty at runtime; baseline multiplier 1.0 preserved.",
        },
        {
            "priority": 4,
            "task": "RAW_TWO_TAP_PRESSURE_ADMISSION",
            "owner_lane": "scratch_cfd_postprocess",
            "depends_on": "AGENT-412 scheduler cleanup or no conflict",
            "action": "If needed, run scratch-only two-tap extraction and admit/reject pressure terms.",
            "acceptance": "Observed pressure definitions and straight-loss subtraction are explicit.",
        },
        {
            "priority": 5,
            "task": "FINAL_FORWARD_V1_GATE_REBUILD",
            "owner_lane": "repo_local_forward",
            "depends_on": "thermal, hydraulic, and HX rows admitted or blocked",
            "action": "Rebuild final gate from admitted rows only.",
            "acceptance": "Salt2 train, Salt3 validation, Salt4 holdout are separate; final no-go retained if any gate fails.",
        },
    ]


def build_fluid_status() -> List[Dict[str, object]]:
    return [
        {
            "interface": "hx_ua_multiplier",
            "status_after_agent413": "implemented",
            "runtime_class": "setup_or_train_scalar",
            "default_behavior": "1.0 reproduces baseline predictive_airside_hx",
            "guardrail": "does not pass imposed CFD cooler duty",
            "test_required": "predictive_hx_ua_multiplier_changes_computed_hx_duty",
        },
        {
            "interface": "external_boundary_table",
            "status_after_agent413": "already_implemented_prior_to_agent413",
            "runtime_class": "setup_boundary_dictionary",
            "default_behavior": "absent dictionaries preserve old behavior",
            "guardrail": "do not combine realized wallHeatFlux replay with added radiation",
            "test_required": "external_boundary_override_changes_target_segment_only",
        },
    ]


def write_readme(summary: Dict[str, object]) -> None:
    text = f"""---
provenance:
  task: {TASK}
  generated_by: codex
tags: [blockers, forward-v1, fluid-api, thermal-admission, f6]
related:
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_forward_v1_row_admission_ledger/README.md
---
# Blocker Resolution Wave Implementation

Date: {DATE}
Task: {TASK}

## Result

This package refreshes the blocker frontier after the July 15 PM5 and Fluid API
evidence. It does not mutate native CFD outputs and does not admit final
forward-v1. It converts evidence into row-level review tables and records the
remaining executable sequence.

## Key Outcomes

- PM5/F6 rows reviewed: {summary['pm5_rows']}
- PM5 rows ready for F6/onset review, not admitted: {summary['pm5_f6_review_ready_rows']}
- Thermal/internal-Nu rows reviewed: {summary['thermal_rows']}
- Thermal fit-admissible rows from current evidence: {summary['thermal_fit_admissible_rows']}
- Fluid `hx_ua_multiplier` hook: implemented in external Fluid source with focused tests.
- Final forward-v1: remains `{summary['final_forward_v1_status']}`.

## Guardrails

- No native CFD solver outputs were changed.
- Scheduler state was read-only in this task.
- Registry/case admission state was not promoted.
- Realized CFD `wallHeatFlux`, imposed cooler duty, CFD mdot, and validation
  temperatures remain scoring/diagnostic inputs only, not predictive runtime
  inputs.
- Radiation is embedded in CFD `rcExternalTemperature` wallHeatFlux replay; do
  not add a separate radiation term on top of realized wallHeatFlux.

## Files

- `blocker_register_refresh.csv`
- `thermal_internal_nu_admission_review.csv`
- `pm5_f6_admission_readiness.csv`
- `fluid_api_implementation_status.csv`
- `remaining_blocker_execution_sequence.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT_DIR / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pm5_source = read_csv(PM5_METRICS)
    thermal_source = read_csv(THERMAL_ADMISSION)
    hydraulic_source = read_csv(HYDRAULIC_GATE)
    forward_source = read_csv(FORWARD_LEDGER)

    pm5_rows = build_pm5_readiness(pm5_source)
    thermal_rows = build_thermal_review(thermal_source)
    blocker_rows = build_blocker_refresh(pm5_rows, thermal_rows)
    sequence_rows = build_remaining_sequence()
    fluid_rows = build_fluid_status()

    write_csv(
        OUT_DIR / "pm5_f6_admission_readiness.csv",
        pm5_rows,
        [
            "case_key",
            "case_role",
            "plane_location",
            "span",
            "representative_time_s",
            "metric_status",
            "wallHeatFlux_available",
            "has_Re_Pr_Ri_Gr_Ra",
            "reverse_area_fraction",
            "reverse_mass_fraction",
            "secondary_velocity_fraction",
            "f6_pressure_onset_readiness",
            "internal_nu_readiness",
            "admission_class",
            "admission_reason",
            "source_paths",
        ],
    )
    write_csv(
        OUT_DIR / "thermal_internal_nu_admission_review.csv",
        thermal_rows,
        [
            "case_id",
            "source_id",
            "segment",
            "qoi",
            "units",
            "review_admission_class",
            "internal_nu_fit_allowed",
            "wallHeatFlux_W",
            "enthalpy_change_W",
            "residual_W",
            "residual_fraction",
            "wall_vs_enthalpy_direction",
            "blockers",
            "guardrail",
            "next_action",
            "source_paths",
        ],
    )
    write_csv(
        OUT_DIR / "blocker_register_refresh.csv",
        blocker_rows,
        ["blocker_id", "previous_status", "agent413_status", "evidence_delta", "next_resolution_condition"],
    )
    write_csv(
        OUT_DIR / "remaining_blocker_execution_sequence.csv",
        sequence_rows,
        ["priority", "task", "owner_lane", "depends_on", "action", "acceptance"],
    )
    write_csv(
        OUT_DIR / "fluid_api_implementation_status.csv",
        fluid_rows,
        ["interface", "status_after_agent413", "runtime_class", "default_behavior", "guardrail", "test_required"],
    )
    source_rows = [
        {"artifact": "pm5_metrics", "path": PM5_METRICS.relative_to(ROOT), "rows": len(pm5_source)},
        {"artifact": "pm5_validation", "path": PM5_VALIDATION.relative_to(ROOT), "rows": len(read_csv(PM5_VALIDATION))},
        {"artifact": "thermal_admission", "path": THERMAL_ADMISSION.relative_to(ROOT), "rows": len(thermal_source)},
        {"artifact": "hydraulic_gate", "path": HYDRAULIC_GATE.relative_to(ROOT), "rows": len(hydraulic_source)},
        {"artifact": "forward_ledger", "path": FORWARD_LEDGER.relative_to(ROOT), "rows": len(forward_source)},
    ]
    write_csv(OUT_DIR / "source_manifest.csv", source_rows, ["artifact", "path", "rows"])

    pm5_counts = Counter(row["f6_pressure_onset_readiness"] for row in pm5_rows)
    thermal_counts = Counter(row["review_admission_class"] for row in thermal_rows)
    summary = {
        "task": TASK,
        "date": DATE,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "pm5_rows": len(pm5_rows),
        "pm5_f6_review_ready_rows": pm5_counts.get("review_ready_not_admitted", 0),
        "pm5_readiness_counts": dict(pm5_counts),
        "thermal_rows": len(thermal_rows),
        "thermal_fit_admissible_rows": thermal_counts.get("fit_admissible", 0),
        "thermal_review_counts": dict(thermal_counts),
        "fluid_hx_ua_multiplier_hook": "implemented",
        "native_solver_outputs_mutated": False,
        "scheduler_mutated": False,
        "registry_or_case_admission_mutated": False,
        "final_forward_v1_status": "blocked_no_go_final_forward_v1_not_admitted",
        "work_product_dir": str(OUT_DIR.relative_to(ROOT)),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(summary)


if __name__ == "__main__":
    main()
