#!/usr/bin/env python3
"""Build PASSIVE-H2-CAND001 source-basis enrichment gate from existing evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-FLUID-EXTBC-PASSIVE-H2-CAND001-SOURCE-BASIS-ENRICHMENT-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment"
PASSIVE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis"
H2 = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution"
S8S12 = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s8_s12_thermal_residual_ownership_gate"
SOURCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp"
SETUP = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract"

DECISION = "enriched_but_source_basis_not_released_no_repair"
CLAIM_BOUNDARY = "read-only source-basis enrichment; no Fluid solve; no repair execution; no admission"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def by_family(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["source_family"]: row for row in rows}


def source_basis_coverage() -> list[dict[str, object]]:
    ambient = by_family(read_csv(PASSIVE / "ambient_surroundings_basis.csv"))
    area = by_family(read_csv(PASSIVE / "area_coverage_basis.csv"))
    h_range = by_family(read_csv(PASSIVE / "independent_h_estimate_range.csv"))
    risk = by_family(read_csv(PASSIVE / "current_hA_basis_and_provenance_risk.csv"))
    q_env = by_family(read_csv(PASSIVE / "expected_q_loss_envelope.csv"))
    rows: list[dict[str, object]] = []
    for family in sorted(risk, key=lambda item: int(risk[item]["priority_rank"])):
        amb = ambient[family]
        geom = area[family]
        hrow = h_range[family]
        qrow = q_env[family]
        rrow = risk[family]
        ambient_released = amb["ambient_basis_status"] == "source_released"
        geometry_released = geom["geometry_support_status"] == "source_released"
        literature_released = hrow["literature_provenance_status"] == "source_released"
        wallflux_independent = rrow["wallHeatFlux_provenance_present"] == "False"
        release = ambient_released and geometry_released and literature_released and wallflux_independent
        rows.append(
            {
                "source_family": family,
                "current_hA_W_K": rrow["current_hA_W_K"],
                "current_q_inside_engineering_envelope": qrow["current_q_inside_envelope"],
                "ambient_basis_status": amb["ambient_basis_status"],
                "geometry_support_status": geom["geometry_support_status"],
                "literature_provenance_status": hrow["literature_provenance_status"],
                "wall_heat_flux_provenance_present": rrow["wallHeatFlux_provenance_present"],
                "independent_source_release_allowed_now": str(release).lower(),
                "repair_ready_now": "false",
                "reason": "engineering screen passes, but independent ambient/geometry/literature provenance and wall-heat-flux independence are not all released",
                "next_required": "trace ambient, geometry/area, insulation exposure, and h-correlation provenance before any repair run",
            }
        )
    return rows


def wallheatflux_dependence_audit() -> list[dict[str, object]]:
    rows = read_csv(H2 / "hA_area_unit_audit.csv")
    out: list[dict[str, object]] = []
    for row in rows:
        out.append(
            {
                "role_row_index": row["role_row_index"],
                "source_family": row["source_family"],
                "parent_segment": row["parent_segment"],
                "h_W_m2K": row["h_W_m2K"],
                "area_m2": row["area_m2"],
                "hA_W_K": row["hA_W_K"],
                "wall_heat_flux_provenance_present": row["source_path_wallHeatFlux_present"],
                "independent_basis_now": "false" if row["source_path_wallHeatFlux_present"] == "True" else "true",
                "admissibility_concern": row["admissibility_concern"],
                "release_effect": "blocks_source_property_release" if row["source_path_wallHeatFlux_present"] == "True" else "review",
            }
        )
    return out


def source_property_release_gate() -> list[dict[str, object]]:
    passive_summary = read_json(PASSIVE / "summary.json")
    s8s12_summary = read_json(S8S12 / "summary.json")
    return [
        {
            "gate_id": "PH2-SRC-01",
            "gate": "engineering_screen",
            "status": "pass",
            "release_allowed_now": "false",
            "evidence": "all current passive h and fixed-state q estimates sit inside broad engineering screens",
            "next_required": "promote from order screen to source-backed family-specific basis",
        },
        {
            "gate_id": "PH2-SRC-02",
            "gate": "wall_heat_flux_independence",
            "status": "fail",
            "release_allowed_now": "false",
            "evidence": "all passive rows still carry wall heat-flux provenance paths",
            "next_required": "replace current h basis with independent setup/geometry/literature values",
        },
        {
            "gate_id": "PH2-SRC-03",
            "gate": "ambient_geometry_insulation_basis",
            "status": "fail",
            "release_allowed_now": "false",
            "evidence": "ambient, geometry/area, insulation exposure, and room-flow basis remain provisional",
            "next_required": "document source-backed ambient and external-surface exposure envelope",
        },
        {
            "gate_id": "PH2-SRC-04",
            "gate": "source_sink_coupling",
            "status": "partial",
            "release_allowed_now": "false",
            "evidence": "setup-known source/sink rows exist, but heater-source decomposition is partial/local",
            "next_required": "account for source/sink interactions before repair execution",
        },
        {
            "gate_id": "PH2-SRC-05",
            "gate": "thermal_owner_gate",
            "status": "blocked",
            "release_allowed_now": "false",
            "evidence": f"S8/S12 gate decision is {s8s12_summary['decision']} with {s8s12_summary['candidate_count_released']} released candidates",
            "next_required": "do not run repair until exactly one physical candidate is source-backed",
        },
        {
            "gate_id": "PH2-SRC-06",
            "gate": "overall_passive_h2_source_release",
            "status": passive_summary["gate_decision"],
            "release_allowed_now": "false",
            "evidence": "source-basis package is enriched but remains no-release",
            "next_required": "source ambient/geometry/insulation/literature basis before any Fluid repair row",
        },
    ]


def repair_readiness_decision() -> list[dict[str, object]]:
    repair = read_csv(PASSIVE / "repair_gate.csv")[0]
    h2 = read_csv(H2 / "repair_candidate_predeclaration_gate.csv")[0]
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "decision": DECISION,
            "run_one_train_repair": "false",
            "source_property_release_allowed_now": "false",
            "freeze_or_admission_allowed_now": "false",
            "predeclared_change": h2["predeclared_change"],
            "current_gate": repair["gate_decision"],
            "rationale": "passive h/q envelopes are plausible, but wall-heat-flux provenance and missing source-backed ambient/geometry/insulation/literature basis block repair",
            "next_claimable": "source-backed passive hA basis table with ambient/geometry/insulation/literature provenance; no Fluid solve in that row unless separately authorized",
        }
    ]


def s11_s15_s6_consequence() -> list[dict[str, object]]:
    return [
        {
            "decision_id": "PASSIVE-H2-SOURCE-BASIS-ENRICHMENT",
            "s11_unblocked": "false",
            "s15_unblocked": "false",
            "s6_unblocked": "false",
            "candidate_count_released": 0,
            "decision": DECISION,
            "rationale": "source-basis enrichment improves documentation but releases no repair candidate, no source/property row, and no protected split scoring",
        }
    ]


def no_mutation_guardrails() -> list[dict[str, object]]:
    return [
        {"guardrail": "fluid_solve_run", "value": "false"},
        {"guardrail": "native_output_mutation", "value": "false"},
        {"guardrail": "registry_or_admission_mutation", "value": "false"},
        {"guardrail": "scheduler_action", "value": "false"},
        {"guardrail": "external_fluid_edit", "value": "false"},
        {"guardrail": "validation_holdout_external_scoring", "value": "false"},
        {"guardrail": "fit_or_model_selection", "value": "false"},
        {"guardrail": "global_hA_multiplier_selection", "value": "false"},
        {"guardrail": "repair_execution", "value": "false"},
        {"guardrail": "source_property_release", "value": "false"},
        {"guardrail": "s11_s15_s6_trigger", "value": "false"},
        {"guardrail": "residual_absorbed_into_internal_nu", "value": "false"},
    ]


def source_manifest() -> list[dict[str, object]]:
    paths = [
        (PASSIVE / "repair_gate.csv", "passive physical-basis gate"),
        (PASSIVE / "ambient_surroundings_basis.csv", "ambient basis status"),
        (PASSIVE / "area_coverage_basis.csv", "geometry/area coverage basis"),
        (PASSIVE / "independent_h_estimate_range.csv", "independent h order screen"),
        (PASSIVE / "current_hA_basis_and_provenance_risk.csv", "current hA provenance risk"),
        (PASSIVE / "expected_q_loss_envelope.csv", "fixed-state q envelope"),
        (H2 / "hA_area_unit_audit.csv", "role-row wall heat-flux provenance audit"),
        (H2 / "repair_candidate_predeclaration_gate.csv", "predeclared passive candidate gate"),
        (S8S12 / "summary.json", "thermal residual ownership decision"),
        (SOURCE / "tw4_tw6_focus.csv", "heater-source residual decomposition"),
        (SETUP / "source_sink_runtime_contract.csv", "setup-known source/sink contract"),
    ]
    return [
        {
            "path": str(path.relative_to(ROOT)),
            "role": role,
            "exists": path.exists(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path, role in paths
    ]


def write_readme(summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis/repair_gate.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/hA_area_unit_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s8_s12_thermal_residual_ownership_gate/summary.json
tags: [passive-h2, source-basis, external-bc, no-repair, s11-blocked]
related:
  - .agent/status/2026-07-21_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 CAND001 Source-Basis Enrichment

Decision: `{summary["decision"]}`.

This package enriches the passive-H2 source-basis evidence without running
Fluid or releasing a repair. Current passive `h` and fixed-state `q` values
remain engineering-plausible, but the source basis is still not independent:
wall heat-flux provenance remains present, and ambient/geometry/insulation/
literature basis is not source-released.

## Outputs

- `source_basis_coverage.csv`
- `wallheatflux_dependence_audit.csv`
- `source_property_release_gate.csv`
- `repair_readiness_decision.csv`
- `s11_s15_s6_consequence.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    coverage = source_basis_coverage()
    wallflux = wallheatflux_dependence_audit()
    release_gate = source_property_release_gate()
    repair = repair_readiness_decision()
    summary = {
        "task_id": TASK_ID,
        "status": "complete",
        "decision": DECISION,
        "source_family_rows": len(coverage),
        "wallheatflux_audit_rows": len(wallflux),
        "release_gate_rows": len(release_gate),
        "families_released": 0,
        "source_property_release": False,
        "run_one_train_repair": False,
        "freeze_or_admission_allowed": False,
        "s11_s15_s6_trigger": False,
        "fluid_solve_run": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "validation_rows_scored": 0,
        "holdout_rows_scored": 0,
        "external_test_rows_scored": 0,
        "fit_or_model_selection": False,
        "global_hA_multiplier_selection": False,
        "residual_absorbed_into_internal_nu": False,
    }
    write_csv(OUT / "source_basis_coverage.csv", coverage, ["source_family", "current_hA_W_K", "current_q_inside_engineering_envelope", "ambient_basis_status", "geometry_support_status", "literature_provenance_status", "wall_heat_flux_provenance_present", "independent_source_release_allowed_now", "repair_ready_now", "reason", "next_required"])
    write_csv(OUT / "wallheatflux_dependence_audit.csv", wallflux, ["role_row_index", "source_family", "parent_segment", "h_W_m2K", "area_m2", "hA_W_K", "wall_heat_flux_provenance_present", "independent_basis_now", "admissibility_concern", "release_effect"])
    write_csv(OUT / "source_property_release_gate.csv", release_gate, ["gate_id", "gate", "status", "release_allowed_now", "evidence", "next_required"])
    write_csv(OUT / "repair_readiness_decision.csv", repair, ["candidate_id", "decision", "run_one_train_repair", "source_property_release_allowed_now", "freeze_or_admission_allowed_now", "predeclared_change", "current_gate", "rationale", "next_claimable"])
    write_csv(OUT / "s11_s15_s6_consequence.csv", s11_s15_s6_consequence(), ["decision_id", "s11_unblocked", "s15_unblocked", "s6_unblocked", "candidate_count_released", "decision", "rationale"])
    write_csv(OUT / "no_mutation_guardrails.csv", no_mutation_guardrails(), ["guardrail", "value"])
    write_csv(OUT / "source_manifest.csv", source_manifest(), ["path", "role", "exists", "native_solver_output", "mutated"])
    write_json(OUT / "summary.json", summary)
    write_readme(summary)


if __name__ == "__main__":
    main()
