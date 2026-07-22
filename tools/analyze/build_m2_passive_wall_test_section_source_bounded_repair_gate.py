#!/usr/bin/env python3.11
"""Build the M2 passive wall/test-section source-bounded repair gate."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-M2-PASSIVE-WALL-TEST-SECTION-SOURCE-BOUNDED-REPAIR-GATE-2026-07-22"
SLUG = "m2_passive_wall_test_section_source_bounded_repair_gate"
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate"

OWNERSHIP = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s8_s12_thermal_residual_ownership_gate/residual_owner_matrix.csv"
OWNERSHIP_GATE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s8_s12_thermal_residual_ownership_gate/candidate_gate_decision.csv"
PASSIVE_H2_BASIS = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis/repair_gate.csv"
PASSIVE_H2_ENRICH = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment/repair_readiness_decision.csv"
PHASE_H_OWNER = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/owner_delta.csv"
PHASE_H_METRICS = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/sensitivity_metrics.csv"
PHASE_H2_PREDECL = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/repair_candidate_predeclaration_gate.csv"
HEATLOSS_PHASE3 = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_3_wall_test_section_model_score/wall_test_section_candidate_gate_scorecard.csv"
SOURCE_SINK_CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/setup_known_source_contract.csv"
HEATER_SOURCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp/decision_table.csv"
BLOCKERS = ROOT / ".agent/BLOCKERS.md"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def build_source_basis() -> list[dict[str, object]]:
    passive_basis = read_csv(PASSIVE_H2_BASIS)[0]
    passive_enrich = read_csv(PASSIVE_H2_ENRICH)[0]
    h2_predecl = read_csv(PHASE_H2_PREDECL)[0]
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "heat_path": "passive_wall_external_boundary",
            "source_basis_status": passive_basis["gate_decision"],
            "inside_engineering_screen": passive_basis["current_h_inside_broad_engineering_screen_all_families"],
            "wallheatflux_provenance_risk": passive_basis["all_current_passive_rows_wallHeatFlux_provenance"],
            "ambient_basis_source_released": passive_basis["ambient_basis_source_released"],
            "repair_run_allowed_now": passive_basis["repair_run_allowed_now"],
            "source_property_release_allowed_now": passive_enrich["source_property_release_allowed_now"],
            "predeclared_change": passive_enrich["predeclared_change"],
            "decision": "plausible_but_not_source_released",
            "reason": passive_enrich["rationale"],
        },
        {
            "candidate_id": "GLOBAL-PASSIVE-HA-0.5",
            "heat_path": "global_passive_network",
            "source_basis_status": "train_sensitivity_only",
            "inside_engineering_screen": "",
            "wallheatflux_provenance_risk": "not_source_bounded",
            "ambient_basis_source_released": "False",
            "repair_run_allowed_now": "False",
            "source_property_release_allowed_now": "False",
            "predeclared_change": h2_predecl["predeclared_change"],
            "decision": "forbidden_as_global_multiplier",
            "reason": h2_predecl["forbidden_shortcut"],
        },
        {
            "candidate_id": "TS5-SETUP-RESISTANCE-NETWORK",
            "heat_path": "test_section_wall_external_resistance",
            "source_basis_status": "api_hooks_available_score_missing",
            "inside_engineering_screen": "",
            "wallheatflux_provenance_risk": "direct_target_gate_failed_or_unscored",
            "ambient_basis_source_released": "not_released",
            "repair_run_allowed_now": "False",
            "source_property_release_allowed_now": "False",
            "predeclared_change": "setup resistance network wall/external candidate",
            "decision": "candidate_contract_exists_not_reviewable",
            "reason": "API hooks exist, but no scored setup-only resistance-network candidate exists and source/property gate remains blocked.",
        },
    ]


def build_owner_split() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_csv(OWNERSHIP):
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "owner_family": row["owner_family"],
                "gate_status": row["gate_status"],
                "decision": row["decision"],
                "quantitative_signal": row["quantitative_signal"],
                "positive_evidence": row["positive_evidence"],
                "blocking_evidence": row["blocking_evidence"],
                "m2_interpretation": "not_source_bounded_repair_ready" if row["decision"] != "repair_ready" else "reviewable",
            }
        )
    return rows


def build_local_global_interpretation() -> tuple[list[dict[str, object]], float, float]:
    owner_rows = read_csv(PHASE_H_OWNER)
    by_id = {row["sensitivity_id"]: row for row in owner_rows}
    lower = abs(float(by_id["lower_leg_hA_scale_0.5"]["delta_abs_residual_K"]))
    global_half = abs(float(by_id["global_passive_hA_scale_0.5"]["delta_abs_residual_K"]))
    ratio = global_half / lower if lower else float("inf")
    rows = [
        {
            "comparison": "lower_leg_hA_scale_0.5_vs_global_passive_hA_scale_0.5",
            "lower_leg_TW5_abs_residual_improvement_K": lower,
            "global_passive_TW5_abs_residual_improvement_K": global_half,
            "global_to_lower_response_ratio": ratio,
            "interpretation": "dominant response is broad/global, not localized lower-leg source-bounded evidence",
            "repair_implication": "do_not_admit_global_multiplier; seek source-bounded wall/core exchange or source-placement evidence",
        },
        {
            "comparison": "ambient_drive_delta_+15K",
            "lower_leg_TW5_abs_residual_improvement_K": "",
            "global_passive_TW5_abs_residual_improvement_K": abs(float(by_id["ambient_drive_delta_+15K"]["delta_abs_residual_K"])),
            "global_to_lower_response_ratio": "",
            "interpretation": "ambient drive can move residual but remains train-only diagnostic without source release",
            "repair_implication": "requires ambient/geometry/insulation/literature provenance before execution",
        },
    ]
    return rows, lower, global_half


def build_runtime_legality() -> list[dict[str, object]]:
    return [
        {"candidate_or_input": "PASSIVE-H2-CAND001", "runtime_status": "blocked", "reason": "source basis not released; wallHeatFlux provenance risk remains", "allowed_now": False},
        {"candidate_or_input": "global_passive_hA_scale_0.5", "runtime_status": "forbidden", "reason": "train diagnostic global multiplier, not a source-bounded repair", "allowed_now": False},
        {"candidate_or_input": "TS5_setup_resistance_network_wall_external", "runtime_status": "contract_only", "reason": "API hooks exist but no scored setup-only candidate and source/property gate blocked", "allowed_now": False},
        {"candidate_or_input": "CFD_wallHeatFlux_or_realized_test_section_heat", "runtime_status": "forbidden_runtime_input", "reason": "diagnostic/scoring evidence only", "allowed_now": False},
        {"candidate_or_input": "validation_holdout_temperatures", "runtime_status": "forbidden_runtime_input", "reason": "no protected target use in this gate", "allowed_now": False},
        {"candidate_or_input": "source_geometry_ambient_insulation_literature_basis", "runtime_status": "needed_future_input", "reason": "next source-basis row may assemble this evidence without solving", "allowed_now": True},
    ]


def write_docs(summary: dict[str, object], validation_status: str = "pending") -> None:
    generated_at = str(summary["generated_at_utc"])
    readme = f"""---
provenance:
  generated_by: tools/analyze/build_m2_passive_wall_test_section_source_bounded_repair_gate.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - M2
  - passive-wall
  - test-section
  - repair-gate
related:
  - {rel(OWNERSHIP)}
  - {rel(PASSIVE_H2_BASIS)}
  - {rel(PHASE_H_OWNER)}
---

# M2 Passive Wall/Test-Section Source-Bounded Repair Gate

## Decision

No M2+ passive wall/test-section repair is S11-reviewable now. PASSIVE-H2 is
physically plausible in broad screens, but its source basis is not released and
the strongest residual movement is a broad/global passive hA sensitivity, not a
localized source-bounded repair.

The dominant train-only signal is strong: global passive hA `0.5x` improves TW5
absolute residual by `{summary['global_passive_half_TW5_improvement_K']} K`, while
lower-leg hA `0.5x` improves TW5 by only `{summary['lower_leg_half_TW5_improvement_K']} K`.
That contrast is useful for diagnosis, but it is also why the gate must not
admit a global multiplier.

## Guardrails

No Fluid solve, repair execution, fitting, model selection, global hA multiplier
selection, source/property release, closure admission, final score, protected
split scoring, native-output mutation, registry mutation, scheduler action,
Fluid/external edit, S11/S12/S13/S15/S6 trigger, runtime-temperature release, or
residual absorption into internal Nu was performed.
"""
    write_text(OUT_DIR / "README.md", readme)

    status = f"""---
provenance:
  generated_by: tools/analyze/build_m2_passive_wall_test_section_source_bounded_repair_gate.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - status
  - M2
  - passive-wall
related:
  - {rel(OUT_DIR)}
---

# {TASK_ID}

## Objective

Decide whether an M2+ passive wall/test-section source-bounded repair is
supportable from independent setup/geometry/literature evidence.

## Outcome

Decision: `{summary['decision']}`. Reviewable source-bounded candidates:
`{summary['s11_reviewable_candidates']}`. Repair executions: `0`. The cold-bias
signal remains attributed to unresolved passive/source-placement/axial-mixing/
wall-core exchange blockers.

## Changes Made

- Wrote passive heat-path source basis table.
- Wrote residual-owner split table.
- Wrote local-vs-global cold-bias interpretation.
- Wrote runtime-legality matrix.
- Wrote repair/no-repair gate and thesis figure/table handoff.
- Wrote README, summary, status, journal, and import manifest.

## Validation

{validation_status}

## Guardrails

- Fluid solve: false.
- Native-output mutation: false.
- Registry/admission mutation: false.
- Scheduler action or solver/postprocessing/sampler/harvest/UQ launch: false.
- Fluid/external edit: false.
- Validation/holdout/external-test scoring: false.
- Fitting/tuning/model selection/global hA multiplier selection: false.
- Source/property release, repair execution, closure admission, final score:
  false.
- S11/S12/S13/S15/S6 trigger: false.
- Runtime-temperature input release or residual-internal-Nu absorption: false.
"""
    write_text(ROOT / f".agent/status/2026-07-22_{TASK_ID}.md", status)

    journal = f"""---
provenance:
  generated_by: tools/analyze/build_m2_passive_wall_test_section_source_bounded_repair_gate.py
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - journal
  - M2
  - passive-wall
related:
  - {rel(OUT_DIR)}
---

# M2 passive wall/test-section source-bounded repair gate

## Attempted

Built a read-only gate from S8/S12 residual ownership, PASSIVE-H2 source-basis
rows, Phase H/H2 passive sensitivity rows, wall/test-section candidate gates,
and setup-known source/sink context.

## Observed

PASSIVE-H2 remains plausible but not source-released. The train-only global
passive hA `0.5x` sensitivity moves TW5 much more than the lower-leg-only hA
change, which argues against claiming a local source-bounded repair from the
current evidence.

## Inferred

The correct M2 result is a no-repair gate. The cold-bias residual should remain
assigned to unresolved passive/source-placement/axial-mixing/wall-core exchange
mechanisms until a future row supplies independent source/geometry/literature
evidence.

## Contradictions or Caveats

This is not a proof that passive wall/test-section physics is irrelevant. It is
a proof that the current evidence cannot support repair execution or admission
without a source-released basis.

## Next Useful Actions

A later source-basis row can assemble ambient, geometry, insulation, material,
area, and literature h evidence. It should still avoid Fluid solves until the
source basis is released, and it must not reuse global passive hA `0.5x` as a
fitted multiplier.
"""
    write_text(ROOT / ".agent/journal/2026-07-22/m2-passive-wall-test-section-source-bounded-repair-gate.md", journal)


def build() -> dict[str, object]:
    generated_at = now_utc()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_basis = build_source_basis()
    owner_split = build_owner_split()
    local_global, lower_improve, global_improve = build_local_global_interpretation()
    runtime = build_runtime_legality()
    ownership_gates = read_csv(OWNERSHIP_GATE)

    repair_gate = [
        {
            "candidate_family": "M2_plus_passive_wall_test_section",
            "decision": "no_repair_now_no_s11_candidate",
            "s11_reviewable": False,
            "repair_execution_allowed": False,
            "source_property_release_allowed": False,
            "closure_admission_allowed": False,
            "reason": "No candidate has independent source-bounded basis plus finite score/readiness; strongest response is broad train-only passive hA sensitivity.",
            "next_source_basis_work": "ambient/geometry/insulation/material/area/literature hA release before any solve",
        }
    ]
    handoff = [
        {
            "artifact": "passive_heat_path_source_basis_table.csv",
            "paper_use": "explain why plausible passive path is not yet source-released",
            "claim_boundary": "diagnostic gate; no repair/admission",
        },
        {
            "artifact": "local_vs_global_cold_bias_interpretation.csv",
            "paper_use": "show global response dominates local lower-leg hA perturbation",
            "claim_boundary": "train-only sensitivity, not fitted coefficient",
        },
        {
            "artifact": "repair_no_repair_gate.csv",
            "paper_use": "cite no S11-reviewable M2+ candidate",
            "claim_boundary": "no final score or source/property release",
        },
    ]

    write_csv(OUT_DIR / "passive_heat_path_source_basis_table.csv", source_basis)
    write_csv(OUT_DIR / "wall_test_section_residual_owner_split.csv", owner_split)
    write_csv(OUT_DIR / "local_vs_global_cold_bias_interpretation.csv", local_global)
    write_csv(OUT_DIR / "runtime_legality_matrix.csv", runtime)
    write_csv(OUT_DIR / "repair_no_repair_gate.csv", repair_gate)
    write_csv(OUT_DIR / "thesis_figure_table_handoff.csv", handoff)
    write_csv(OUT_DIR / "ownership_gate_context.csv", ownership_gates)

    reviewable = sum(1 for row in repair_gate if row["s11_reviewable"])
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": generated_at,
        "decision": "no_m2_passive_repair_now_source_basis_not_released",
        "source_basis_rows": len(source_basis),
        "residual_owner_rows": len(owner_split),
        "runtime_legality_rows": len(runtime),
        "s11_reviewable_candidates": reviewable,
        "repair_execution_allowed": False,
        "source_property_release_allowed": False,
        "closure_admission_allowed": False,
        "global_passive_half_TW5_improvement_K": global_improve,
        "lower_leg_half_TW5_improvement_K": lower_improve,
        "global_to_lower_response_ratio": global_improve / lower_improve,
        "fluid_solve": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launch": False,
        "fluid_or_external_edit": False,
        "validation_holdout_external_scoring": False,
        "fitting_tuning_model_selection": False,
        "global_hA_multiplier_selection": False,
        "source_property_release": False,
        "final_score_claim": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "runtime_temperature_input_release": False,
        "residual_internal_nu_absorption": False,
        "source_context": [
            rel(OWNERSHIP),
            rel(OWNERSHIP_GATE),
            rel(PASSIVE_H2_BASIS),
            rel(PASSIVE_H2_ENRICH),
            rel(PHASE_H_OWNER),
            rel(PHASE_H_METRICS),
            rel(PHASE_H2_PREDECL),
            rel(HEATLOSS_PHASE3),
            rel(SOURCE_SINK_CONTRACT),
            rel(HEATER_SOURCE),
            rel(BLOCKERS),
        ],
    }
    write_text(OUT_DIR / "summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_docs(summary)

    manifest = {
        "task": TASK_ID,
        "generated_at_utc": generated_at,
        "changed_files": [
            rel(OUT_DIR / "README.md"),
            rel(OUT_DIR / "summary.json"),
            rel(OUT_DIR / "passive_heat_path_source_basis_table.csv"),
            rel(OUT_DIR / "wall_test_section_residual_owner_split.csv"),
            rel(OUT_DIR / "local_vs_global_cold_bias_interpretation.csv"),
            rel(OUT_DIR / "runtime_legality_matrix.csv"),
            rel(OUT_DIR / "repair_no_repair_gate.csv"),
            rel(OUT_DIR / "thesis_figure_table_handoff.csv"),
            rel(OUT_DIR / "ownership_gate_context.csv"),
            f".agent/status/2026-07-22_{TASK_ID}.md",
            ".agent/journal/2026-07-22/m2-passive-wall-test-section-source-bounded-repair-gate.md",
            f"imports/2026-07-22_{SLUG}.json",
            "tools/analyze/build_m2_passive_wall_test_section_source_bounded_repair_gate.py",
            "tools/analyze/test_m2_passive_wall_test_section_source_bounded_repair_gate.py",
            ".agent/BOARD.md",
        ],
        "read_only_context": summary["source_context"]
        + [
            "native CFD/OpenFOAM outputs",
            "registry/admission state",
            "scheduler state",
            "Fluid source tree",
            "external repos",
            "blocker register",
            "generated docs index files",
            "thesis current/LaTeX files",
        ],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": "none",
        "external_fluid_edit": False,
        "mutation_flags": {
            "fluid_solve": False,
            "repair_execution": False,
            "source_property_release": False,
            "closure_admission": False,
            "fitting_tuning_model_selection": False,
            "global_multiplier_selection": False,
            "protected_scoring": False,
        },
    }
    write_text(ROOT / f"imports/2026-07-22_{SLUG}.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
