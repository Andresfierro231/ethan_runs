#!/usr/bin/env python3
"""Build PASSIVE-H2-CAND001 passive hA physical-basis package.

This package is deliberately no-solve and no-fit. It converts Phase H2
attribution into a physical-basis gate for whether a single train-only passive
boundary repair run is justified.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis"

PHASE_E = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve"
PHASE_H2 = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution"
SOURCE_CONTRACT = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract"
SOURCE_DECOMP = REPO / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp"

FAMILY_ORDER = ["junction", "downcomer", "upcomer", "cooling_branch", "lower_leg"]
CLAIM_BOUNDARY = (
    "no Fluid solve; no fitting/global multiplier; no repair execution; no "
    "freeze/admission; no validation/holdout/external-test scoring"
)

# Conservative engineering screens for ambient-air external heat transfer.
# These are intentionally broad and therefore not a source release.
H_RANGE = {
    "junction": {
        "geometry_class": "irregular junction/stub external surface",
        "h_min": 2.0,
        "h_nom": 7.0,
        "h_max": 12.0,
        "basis": "Churchill-Chu natural-convection style order screen for external bodies; exact Ra/Pr not evaluated",
    },
    "downcomer": {
        "geometry_class": "vertical external pipe/leg",
        "h_min": 2.0,
        "h_nom": 6.0,
        "h_max": 10.0,
        "basis": "Churchill-Chu vertical-surface natural-convection order screen; exact characteristic length not source-released",
    },
    "upcomer": {
        "geometry_class": "vertical external pipe/leg",
        "h_min": 2.0,
        "h_nom": 6.0,
        "h_max": 10.0,
        "basis": "Churchill-Chu vertical-surface natural-convection order screen; exact characteristic length not source-released",
    },
    "cooling_branch": {
        "geometry_class": "horizontal/inclined external branch surface",
        "h_min": 2.0,
        "h_nom": 7.0,
        "h_max": 12.0,
        "basis": "Churchill-Chu horizontal-cylinder/inclined-surface natural-convection order screen; room airflow unknown",
    },
    "lower_leg": {
        "geometry_class": "inclined heated lower-leg external surface",
        "h_min": 2.0,
        "h_nom": 7.0,
        "h_max": 12.0,
        "basis": "Churchill-Chu external-surface natural-convection order screen with heater/source coupling unresolved",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def fnum(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def bool_str(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def group_role_rows(role_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {family: [] for family in FAMILY_ORDER}
    for row in role_rows:
        family = row.get("source_segment_id", "")
        if family in grouped:
            grouped[family].append(row)
    return grouped


def parent_tavg_map(segment_rows: list[dict[str, str]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in segment_rows:
        out[row["parent_segment"]] = fnum(row.get("Q_weighted_Tavg_K"))
    return out


def family_current_rows(grouped: dict[str, list[dict[str, str]]], h2_family: list[dict[str, str]]) -> list[dict[str, object]]:
    h2_by_family = {row["source_family"]: row for row in h2_family}
    rows: list[dict[str, object]] = []
    for family in FAMILY_ORDER:
        members = grouped[family]
        h_vals = [fnum(row.get("h_W_m2K")) for row in members]
        area = sum(fnum(row.get("area_m2")) for row in members)
        hA = sum(fnum(row.get("hA_W_K")) for row in members)
        wallflux = any("wallHeatFlux" in row.get("source_paths", "") for row in members)
        rows.append(
            {
                "source_family": family,
                "priority_rank": FAMILY_ORDER.index(family) + 1,
                "role_row_count": len(members),
                "parent_segments": ";".join(sorted({row.get("parent_segment", "") for row in members if row.get("parent_segment")})),
                "current_h_min_W_m2K": min(h_vals) if h_vals else "",
                "current_h_max_W_m2K": max(h_vals) if h_vals else "",
                "current_h_area_weighted_W_m2K": hA / area if area else "",
                "current_area_m2": area,
                "current_hA_W_K": hA,
                "h2_tw5_improvement_basis": h2_by_family.get(family, {}).get("contribution_basis", ""),
                "h2_tw5_abs_improvement_K": h2_by_family.get(family, {}).get("tw5_abs_improvement_K", ""),
                "wallHeatFlux_provenance_present": wallflux,
                "provenance_risk": "high_wallHeatFlux_derived" if wallflux else "medium_needs_source_trace",
                "current_basis_decision": "not_independent_physical_basis",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def independent_h_rows(grouped: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in FAMILY_ORDER:
        members = grouped[family]
        area = sum(fnum(row.get("area_m2")) for row in members)
        hA_current = sum(fnum(row.get("hA_W_K")) for row in members)
        h_current = hA_current / area if area else 0.0
        spec = H_RANGE[family]
        in_range = spec["h_min"] <= h_current <= spec["h_max"]
        material_delta_possible = h_current < spec["h_min"] or h_current > spec["h_max"]
        rows.append(
            {
                "source_family": family,
                "geometry_class": spec["geometry_class"],
                "independent_h_min_W_m2K": spec["h_min"],
                "independent_h_nominal_W_m2K": spec["h_nom"],
                "independent_h_max_W_m2K": spec["h_max"],
                "current_h_area_weighted_W_m2K": h_current,
                "current_h_inside_independent_range": in_range,
                "material_current_h_mismatch": material_delta_possible,
                "correlation_or_source_basis": spec["basis"],
                "literature_provenance_status": "engineering_screen_only_not_source_release",
                "needed_for_source_release": "characteristic_length, orientation details, insulation exposure, room airflow, ambient/surroundings basis",
                "repair_justified_by_this_row": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def area_coverage_rows(grouped: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in FAMILY_ORDER:
        members = grouped[family]
        coverages = sorted({fnum(row.get("coverage_multiplier"), 1.0) for row in members})
        rows.append(
            {
                "source_family": family,
                "role_row_count": len(members),
                "parent_segments": ";".join(sorted({row.get("parent_segment", "") for row in members if row.get("parent_segment")})),
                "current_area_m2": sum(fnum(row.get("area_m2")) for row in members),
                "coverage_multipliers": ";".join(str(value) for value in coverages),
                "coverage_basis": "current dictionary coverage only",
                "geometry_support_status": "needs_independent_geometry_trace",
                "aggregation_defensible_now": family in {"downcomer", "upcomer", "lower_leg"},
                "required_before_repair": "trace area/coverage to setup geometry or a documented family envelope",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def ambient_rows(grouped: dict[str, list[dict[str, str]]], sign_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    sign_by_parent = defaultdict(list)
    for row in sign_rows:
        sign_by_parent[row["parent_segment"]].append(row)
    rows: list[dict[str, object]] = []
    for family in FAMILY_ORDER:
        members = grouped[family]
        parents = sorted({row.get("parent_segment", "") for row in members if row.get("parent_segment")})
        role_ta = sorted({fnum(row.get("Ta_K")) for row in members})
        ledger_ta = sorted({fnum(row.get("heat_ledger_external_ambient_temperature_K")) for parent in parents for row in sign_by_parent[parent]})
        rows.append(
            {
                "source_family": family,
                "parent_segments": ";".join(parents),
                "role_Ta_values_K": ";".join(str(value) for value in role_ta),
                "heat_ledger_Ta_values_K": ";".join(str(value) for value in ledger_ta),
                "max_role_vs_ledger_Ta_delta_K": max((abs(a - b) for a in role_ta for b in ledger_ta), default=0.0),
                "surroundings_temperature_basis": "same_as_ambient_in_role_rows",
                "canonical_for_q_envelope_K": 300.0,
                "ambient_basis_status": "provisional_envelope_only_needs_setup_room_source",
                "repair_gate_implication": "ambient_mismatch_too_small_for_50K_residual_but_must_be_reconciled_before_repair",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def q_envelope_rows(grouped: dict[str, list[dict[str, str]]], parent_tavg: dict[str, float]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    ambient = 300.0
    for family in FAMILY_ORDER:
        members = grouped[family]
        spec = H_RANGE[family]
        def q_for_h(h: float) -> float:
            total = 0.0
            for row in members:
                parent = row.get("parent_segment", "")
                dT = max(parent_tavg.get(parent, ambient) - ambient, 0.0)
                total += h * fnum(row.get("area_m2")) * fnum(row.get("coverage_multiplier"), 1.0) * dT
            return total
        hA_current = sum(fnum(row.get("hA_W_K")) for row in members)
        q_current = 0.0
        for row in members:
            parent = row.get("parent_segment", "")
            q_current += fnum(row.get("hA_W_K")) * max(parent_tavg.get(parent, ambient) - ambient, 0.0)
        q_min = q_for_h(spec["h_min"])
        q_nom = q_for_h(spec["h_nom"])
        q_max = q_for_h(spec["h_max"])
        rows.append(
            {
                "source_family": family,
                "current_hA_W_K": hA_current,
                "current_fixed_state_q_loss_estimate_W": q_current,
                "independent_q_loss_min_W": q_min,
                "independent_q_loss_nominal_W": q_nom,
                "independent_q_loss_max_W": q_max,
                "current_q_inside_envelope": q_min <= q_current <= q_max,
                "envelope_basis": "fixed-state estimate using Phase E parent Tavg and provisional ambient 300 K; not a Fluid solve",
                "material_q_basis_for_repair": False,
                "reason": "current estimate lies inside broad engineering screen; source release is missing",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def source_sink_rows(contract_rows: list[dict[str, str]], focus_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    focus_by_sensor = {row["sensor"]: row for row in focus_rows}
    total_q = sum(fnum(row.get("allocated_setup_Q_W")) for row in contract_rows)
    rows = [
        {
            "interaction_item": "setup_known_lower_leg_heater_contract",
            "observed_evidence": f"{len(contract_rows)} executable train-only contract spans; total setup heater Q {total_q:.3f} W",
            "impact_on_passive_hA_repair": "must_be_accounted_for_before_repair_run",
            "decision": "source_lane_available_but_not_admitted",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "interaction_item": "heater_source_residual_decomposition",
            "observed_evidence": (
                f"TW4 delta abs {focus_by_sensor['TW4']['delta_abs_residual_K']} K; "
                f"TW5 delta abs {focus_by_sensor['TW5']['delta_abs_residual_K']} K; "
                f"TW6 delta abs {focus_by_sensor['TW6']['delta_abs_residual_K']} K"
            ),
            "impact_on_passive_hA_repair": "partial_local_improvement_only; does_not_replace_passive_network_basis",
            "decision": "source_lane_partial_improvement_model_form_still_needed",
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]
    return rows


def repair_gate(
    h_rows: list[dict[str, object]],
    q_rows: list[dict[str, object]],
    current_rows: list[dict[str, object]],
    ambient: list[dict[str, object]],
) -> list[dict[str, object]]:
    all_current_inside_h = all(row["current_h_inside_independent_range"] for row in h_rows)
    all_current_inside_q = all(row["current_q_inside_envelope"] for row in q_rows)
    all_wallflux = all(row["wallHeatFlux_provenance_present"] for row in current_rows)
    ambient_needs_source = any(row["ambient_basis_status"] != "source_released" for row in ambient)
    if all_wallflux or ambient_needs_source:
        decision = "needs_more_source"
        rationale = (
            "current h and fixed-state q estimates are inside broad engineering screens, "
            "but passive h provenance remains wallHeatFlux-derived and ambient/geometry "
            "basis is not source-released"
        )
    elif not all_current_inside_h or not all_current_inside_q:
        decision = "run_one_train_repair"
        rationale = "an independently sourced passive h/q envelope materially contradicts the current basis"
    else:
        decision = "forbidden_as_fit"
        rationale = "only Phase H residual response supports a change; no independent physical contradiction found"
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "candidate_name": "passive_hA_source_basis_rebuild_v1",
            "gate_decision": decision,
            "predeclared_repair_if_unblocked": "replace wallHeatFlux-derived passive h basis with independently sourced family-specific passive h envelope",
            "current_h_inside_broad_engineering_screen_all_families": all_current_inside_h,
            "current_q_inside_broad_engineering_screen_all_families": all_current_inside_q,
            "all_current_passive_rows_wallHeatFlux_provenance": all_wallflux,
            "ambient_basis_source_released": not ambient_needs_source,
            "repair_run_allowed_now": decision == "run_one_train_repair",
            "rationale": rationale,
            "forbidden_shortcut": "do not use global_passive_hA_scale_0.5 or any global multiplier as the repair basis",
            "next_action": "source geometry/ambient/insulation/literature release before any solve"
            if decision == "needs_more_source"
            else "claim exact train-only repair run row",
            "claim_boundary": CLAIM_BOUNDARY,
        }
    ]


def write_readme(summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp/README.md
tags: [forward-model, passive-boundary, physical-basis, no-solve]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-PASSIVE-H2-CAND001-PHYSICAL-BASIS-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-extbc-passive-h2-cand001-physical-basis.md
  - imports/2026-07-21_fluid_extbc_passive_h2_cand001_physical_basis.json
task: TODO-FLUID-EXTBC-PASSIVE-H2-CAND001-PHYSICAL-BASIS-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# PASSIVE-H2-CAND001 Physical Basis Package

## Why This Exists

Phase H2 showed broad passive-network sensitivity but blocked admission because
the current passive hA basis traces through `wallHeatFlux`. This package asks
whether independent setup/geometry/engineering evidence justifies one
train-only passive repair run.

## Open First

- `repair_gate.csv`
- `current_hA_basis_and_provenance_risk.csv`
- `independent_h_estimate_range.csv`
- `expected_q_loss_envelope.csv`
- `source_sink_interaction_update.csv`

## Result

Gate decision: `{summary["gate_decision"]}`.

All current passive family h values and fixed-state q estimates sit inside the
broad engineering screens used here, but every current passive family still has
wallHeatFlux-derived provenance and the ambient/geometry/insulation basis is
not source-released. Therefore no train-only repair run is justified by this
row.

## Output Contract

- `current_hA_basis_and_provenance_risk.csv`
- `independent_h_estimate_range.csv`
- `area_coverage_basis.csv`
- `ambient_surroundings_basis.csv`
- `expected_q_loss_envelope.csv`
- `source_sink_interaction_update.csv`
- `repair_gate.csv`
- `source_manifest.csv`
- `summary.json`

## Do Not Do

Do not run Fluid from this package. Do not use `global_passive_hA_scale_0.5` as
a fitted repair. Do not score validation, holdout, or external-test rows. Do
not mutate native CFD/OpenFOAM outputs, registry/admission state, Fluid source,
blocker register, generated indexes, or thesis files.
"""
    (OUT / "README.md").write_text(text)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    role_rows = read_csv(PHASE_E / "role_row_ledger.csv")
    h2_family = read_csv(PHASE_H2 / "passive_hA_family_contribution.csv")
    h2_segment = read_csv(PHASE_H2 / "segment_heat_loss_sweep.csv")
    h2_sign = read_csv(PHASE_H2 / "sign_and_drive_audit.csv")
    contract = read_csv(SOURCE_CONTRACT / "setup_known_source_contract.csv")
    focus = read_csv(SOURCE_DECOMP / "tw4_tw6_focus.csv")

    grouped = group_role_rows(role_rows)
    tavg = parent_tavg_map(h2_segment)

    current = family_current_rows(grouped, h2_family)
    independent = independent_h_rows(grouped)
    area = area_coverage_rows(grouped)
    ambient = ambient_rows(grouped, h2_sign)
    qenv = q_envelope_rows(grouped, tavg)
    source_update = source_sink_rows(contract, focus)
    gate = repair_gate(independent, qenv, current, ambient)

    write_csv(
        OUT / "current_hA_basis_and_provenance_risk.csv",
        current,
        [
            "source_family",
            "priority_rank",
            "role_row_count",
            "parent_segments",
            "current_h_min_W_m2K",
            "current_h_max_W_m2K",
            "current_h_area_weighted_W_m2K",
            "current_area_m2",
            "current_hA_W_K",
            "h2_tw5_improvement_basis",
            "h2_tw5_abs_improvement_K",
            "wallHeatFlux_provenance_present",
            "provenance_risk",
            "current_basis_decision",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "independent_h_estimate_range.csv",
        independent,
        [
            "source_family",
            "geometry_class",
            "independent_h_min_W_m2K",
            "independent_h_nominal_W_m2K",
            "independent_h_max_W_m2K",
            "current_h_area_weighted_W_m2K",
            "current_h_inside_independent_range",
            "material_current_h_mismatch",
            "correlation_or_source_basis",
            "literature_provenance_status",
            "needed_for_source_release",
            "repair_justified_by_this_row",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "area_coverage_basis.csv",
        area,
        [
            "source_family",
            "role_row_count",
            "parent_segments",
            "current_area_m2",
            "coverage_multipliers",
            "coverage_basis",
            "geometry_support_status",
            "aggregation_defensible_now",
            "required_before_repair",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "ambient_surroundings_basis.csv",
        ambient,
        [
            "source_family",
            "parent_segments",
            "role_Ta_values_K",
            "heat_ledger_Ta_values_K",
            "max_role_vs_ledger_Ta_delta_K",
            "surroundings_temperature_basis",
            "canonical_for_q_envelope_K",
            "ambient_basis_status",
            "repair_gate_implication",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "expected_q_loss_envelope.csv",
        qenv,
        [
            "source_family",
            "current_hA_W_K",
            "current_fixed_state_q_loss_estimate_W",
            "independent_q_loss_min_W",
            "independent_q_loss_nominal_W",
            "independent_q_loss_max_W",
            "current_q_inside_envelope",
            "envelope_basis",
            "material_q_basis_for_repair",
            "reason",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "source_sink_interaction_update.csv",
        source_update,
        [
            "interaction_item",
            "observed_evidence",
            "impact_on_passive_hA_repair",
            "decision",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "repair_gate.csv",
        gate,
        [
            "candidate_id",
            "candidate_name",
            "gate_decision",
            "predeclared_repair_if_unblocked",
            "current_h_inside_broad_engineering_screen_all_families",
            "current_q_inside_broad_engineering_screen_all_families",
            "all_current_passive_rows_wallHeatFlux_provenance",
            "ambient_basis_source_released",
            "repair_run_allowed_now",
            "rationale",
            "forbidden_shortcut",
            "next_action",
            "claim_boundary",
        ],
    )

    source_manifest = [
        {"source_path": str(PHASE_E / "role_row_ledger.csv"), "use": "current passive role h/area/hA rows", "mutation": "read_only"},
        {"source_path": str(PHASE_H2 / "passive_hA_family_contribution.csv"), "use": "Phase H2 family attribution and priority", "mutation": "read_only"},
        {"source_path": str(PHASE_H2 / "segment_heat_loss_sweep.csv"), "use": "parent segment Tavg and q-loss context", "mutation": "read_only"},
        {"source_path": str(PHASE_H2 / "sign_and_drive_audit.csv"), "use": "ambient mismatch and sign context", "mutation": "read_only"},
        {"source_path": str(SOURCE_CONTRACT / "setup_known_source_contract.csv"), "use": "completed setup-known heater source contract", "mutation": "read_only"},
        {"source_path": str(SOURCE_DECOMP / "tw4_tw6_focus.csv"), "use": "completed heater source residual decomposition", "mutation": "read_only"},
    ]
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_path", "use", "mutation"])

    summary = {
        "task_id": "TODO-FLUID-EXTBC-PASSIVE-H2-CAND001-PHYSICAL-BASIS-2026-07-21",
        "date": "2026-07-21",
        "status": "complete",
        "families": FAMILY_ORDER,
        "gate_decision": gate[0]["gate_decision"],
        "repair_run_allowed_now": gate[0]["repair_run_allowed_now"],
        "fluid_solve_run": False,
        "validation_rows_scored": 0,
        "holdout_rows_scored": 0,
        "external_test_rows_scored": 0,
        "fit_or_model_selection": False,
        "global_multiplier_admitted": False,
        "repair_executed": False,
        "freeze_or_admission_decision": False,
        "source_property_release": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "all_current_h_inside_engineering_range": all(row["current_h_inside_independent_range"] for row in independent),
        "all_current_q_inside_engineering_range": all(row["current_q_inside_envelope"] for row in qenv),
        "all_passive_rows_wallHeatFlux_provenance": all(row["wallHeatFlux_provenance_present"] for row in current),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_readme(summary)


if __name__ == "__main__":
    main()
