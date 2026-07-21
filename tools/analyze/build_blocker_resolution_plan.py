#!/usr/bin/env python3
"""Build a rigorous blocker-resolution plan for the current CFD-to-1D work.

The output is intentionally a plan package, not a scientific-result package. It
turns the current blocker register into three executable research areas with
acceptance gates, evidence contracts, and documentation requirements.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "AGENT-323"
DEFAULT_OUTPUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_blocker_resolution_plan"

AREAS = [
    {
        "area_id": "A1",
        "area": "Thermal admission, mesh GCI, and internal Nu",
        "objective": (
            "Move repaired thermal evidence from smoke/diagnostic status toward "
            "admissible source rows, or prove why each row remains blocked."
        ),
        "primary_blockers": "closure-qoi-mesh-gci;thermal-cfd-1d-parity",
        "secondary_blockers": "upcomer-onset-data-sparsity",
        "lead_lane": "internal-Nu / therm-reconstr",
        "near_term_success": (
            "A thermal admission review with explicit sign convention, enthalpy "
            "balance, lower-leg Nu policy, downcomer policy, and per-row fit/"
            "validation/blocked decisions."
        ),
        "publication_gate": (
            "Only rows with admitted source policy, finite coarse/medium/fine "
            "triplets, monotonic convergence, valid positive observed order, and "
            "asymptotic-range check may receive publication GCI."
        ),
        "key_sources": (
            "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/summary.json;"
            "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_table.csv;"
            "work_products/2026-07/2026-07-13/2026-07-13_thermal_sign_enthalpy_review/README.md;"
            "operational_notes/maps/mesh-gci-and-uncertainty.md;"
            "operational_notes/maps/thermal-closures-and-internal-nu.md"
        ),
    },
    {
        "area_id": "A2",
        "area": "Forward predictive model and boundary/HX submodels",
        "objective": (
            "Convert proxy/replay evidence into a setup-only forward model path "
            "with locked train/validation/holdout scoring."
        ),
        "primary_blockers": "predictive-heater-cooler-wall-submodels;fluid-external-boundary-api-gap",
        "secondary_blockers": "thermal-cfd-1d-parity;closure-qoi-mesh-gci",
        "lead_lane": "forward-pred / BC-modeling",
        "near_term_success": (
            "A bounded forward-v1 candidate that uses faithful localized H1 or "
            "documented hydraulic correction plus setup-only heater/cooler/"
            "external-boundary inputs, not realized CFD wallHeatFlux."
        ),
        "publication_gate": (
            "Train/validation/holdout split preserved; no CFD mdot, realized CFD "
            "wallHeatFlux, or validation temperatures are runtime inputs; residual "
            "attribution separates hydraulic, HX, heater, wall-layer, radiation, "
            "and sensor terms."
        ),
        "key_sources": (
            "work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/summary.json;"
            "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/summary.json;"
            "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/summary.json;"
            "work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/README.md;"
            "operational_notes/maps/forward-predictive-model.md"
        ),
    },
    {
        "area_id": "A3",
        "area": "Hydraulic closure, recirculation physics, and API/model-form gaps",
        "objective": (
            "Turn friction, named-loss, recirculation, and external-boundary API "
            "ideas into validation-safe closures or documented negative evidence."
        ),
        "primary_blockers": "f6-friction-re-correction;upcomer-onset-data-sparsity;fluid-external-boundary-api-gap",
        "secondary_blockers": "predictive-heater-cooler-wall-submodels",
        "lead_lane": "hydraulics / BC-modeling",
        "near_term_success": (
            "A bounded F6/H1 decision package and an upcomer-onset evidence table "
            "that separate localized named losses, Re-dependent friction, and "
            "recirculation-cell invalidation of single-stream coefficients."
        ),
        "publication_gate": (
            "Closure promoted only if it improves held-out rows without refit, has "
            "local physical interpretation, respects property-lane separation, and "
            "does not hide component/reset/redevelopment losses in one multiplier."
        ),
        "key_sources": (
            "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md;"
            "operational_notes/maps/friction-closures.md;"
            "operational_notes/maps/pressure-and-momentum-budget.md;"
            "operational_notes/07-26/08/2026-07-08_friction_ri_failure_and_path_forward.md;"
            "operational_notes/maps/thermal-boundary-and-radiation.md"
        ),
    },
]

WORK_PACKETS = [
    {
        "packet_id": "A1.1",
        "area_id": "A1",
        "title": "Thermal sign and heat-balance admission review",
        "blocks_addressed": "closure-qoi-mesh-gci;thermal-cfd-1d-parity",
        "action": (
            "Reconcile wallHeatFlux, enthalpy change, segment duty, and interface "
            "recirculation for lower_leg, upcomer, and downcomer using the AGENT-309 "
            "admission table as the starting contract."
        ),
        "acceptance_gate": (
            "Each thermal row is explicitly fit-admissible, validation-only, or "
            "blocked; no row may be fit-admissible if sign direction conflicts, "
            "large heat residual persists, or source paths are incomplete."
        ),
        "scientific_controls": (
            "Use physical-interface enthalpy rows; preserve radiation semantics as "
            "total CFD wallHeatFlux; do not absorb heater/cooler/passive-loss "
            "residuals into internal Nu."
        ),
        "first_files": (
            "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_table.csv;"
            "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_memo.md"
        ),
        "deliverable": "thermal_admission_sign_heat_balance_review package",
        "priority": 1,
    },
    {
        "packet_id": "A1.2",
        "area_id": "A1",
        "title": "Lower-leg Nu and downcomer policy decision",
        "blocks_addressed": "closure-qoi-mesh-gci",
        "action": (
            "Explain lower-leg Nu missing/nonfinite status despite finite HTC/UA, "
            "and decide whether downcomer/right-leg is excluded, validation-only, "
            "or eligible for a separate extraction policy."
        ),
        "acceptance_gate": (
            "Policy table names every blocked thermal row and states whether the "
            "next step is extraction repair, policy exclusion, or no action."
        ),
        "scientific_controls": (
            "Do not infer Nu from HTC unless diameter, k, sign, and source-row "
            "admission are all explicit."
        ),
        "first_files": (
            "work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_mesh_gate_qois.csv"
        ),
        "deliverable": "thermal_qoi_policy_decision.csv plus memo",
        "priority": 2,
    },
    {
        "packet_id": "A1.3",
        "area_id": "A1",
        "title": "Publication-GCI readiness rerun only after admission",
        "blocks_addressed": "closure-qoi-mesh-gci",
        "action": (
            "Rerun thermal/closure mesh GCI only after A1.1/A1.2 produces admitted "
            "source rows."
        ),
        "acceptance_gate": (
            "No GCI for two-level, blocked, non-monotone, oscillatory, divergent, "
            "or source-unadmitted rows."
        ),
        "scientific_controls": (
            "Report observed order, asymptotic ratio, and source admission status "
            "beside every numeric GCI."
        ),
        "first_files": "tools/analyze/build_thermal_mesh_gate.py;tools/analyze/compute_gci.py",
        "deliverable": "updated mesh gate with publication-ready count if any",
        "priority": 5,
    },
    {
        "packet_id": "A2.1",
        "area_id": "A2",
        "title": "Faithful localized H1 hydraulic implementation or rejection",
        "blocks_addressed": "predictive-heater-cooler-wall-submodels;f6-friction-re-correction",
        "action": (
            "Convert the H1 aggregate fixed-K proxy into a localized named-loss/"
            "reset implementation path, or reject it with evidence and route to F6."
        ),
        "acceptance_gate": (
            "Must score Salt2 train, Salt3 validation, and Salt4 holdout without "
            "thermal fitting; every row's mdot residual sign and magnitude reported."
        ),
        "scientific_controls": (
            "No single hidden global multiplier; named losses remain component, "
            "cluster, reset, or branch-apparent terms."
        ),
        "first_files": (
            "work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/summary.json;"
            "work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/README.md"
        ),
        "deliverable": "localized_h1_forward_candidate or H1 rejection memo",
        "priority": 1,
    },
    {
        "packet_id": "A2.2",
        "area_id": "A2",
        "title": "Setup-only cooler/HX and heater boundary candidate",
        "blocks_addressed": "predictive-heater-cooler-wall-submodels;thermal-cfd-1d-parity",
        "action": (
            "Replace imposed CFD cooler duty and heater realized-power replay with "
            "declared setup-only boundary model candidates."
        ),
        "acceptance_gate": (
            "Forward run consumes setup inputs only and reports temperature, mdot, "
            "HX/cooler, heater, wall-layer, and residual attribution separately."
        ),
        "scientific_controls": (
            "No realized CFD wallHeatFlux, validation temperatures, or CFD mdot as "
            "runtime predictive inputs."
        ),
        "first_files": (
            "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/decision_table.csv;"
            "work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/README.md"
        ),
        "deliverable": "setup_only_boundary_candidate_scorecard",
        "priority": 2,
    },
    {
        "packet_id": "A2.3",
        "area_id": "A2",
        "title": "External-boundary API handoff",
        "blocks_addressed": "fluid-external-boundary-api-gap;predictive-heater-cooler-wall-submodels",
        "action": (
            "Prepare the exact Fluid-side patch plan for first-class external "
            "boundary dictionaries and define a repo-local acceptance harness."
        ),
        "acceptance_gate": (
            "Patch plan states input schema, units, default behavior, solve_case "
            "parity tests, and backward-compatibility checks before external edits."
        ),
        "scientific_controls": (
            "External Fluid source remains read-only until a separate board row "
            "claims it; radiation is not double-counted."
        ),
        "first_files": (
            "work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/README.md"
        ),
        "deliverable": "fluid_external_boundary_api_patch_plan",
        "priority": 3,
    },
    {
        "packet_id": "A3.1",
        "area_id": "A3",
        "title": "F6 Re-dependent friction screen",
        "blocks_addressed": "f6-friction-re-correction",
        "action": (
            "Build a bounded F6 = 1+a/Re^b candidate screen using fit-safe pressure/"
            "momentum rows and the locked split."
        ),
        "acceptance_gate": (
            "Promote only if validation/holdout improve without refit and if F6 "
            "does not collapse into an unphysical global multiplier."
        ),
        "scientific_controls": (
            "Property lane explicit; F5 Ri failure stays negative evidence; report "
            "parameter confidence and residual structure."
        ),
        "first_files": (
            "operational_notes/07-26/08/2026-07-08_friction_ri_failure_and_path_forward.md;"
            "work_products/2026-07/2026-07-13/2026-07-13_salt2_pressure_only_mesh_family_comparison/README.md"
        ),
        "deliverable": "f6_re_friction_candidate_screen",
        "priority": 3,
    },
    {
        "packet_id": "A3.2",
        "area_id": "A3",
        "title": "Upcomer recirculation onset evidence expansion",
        "blocks_addressed": "upcomer-onset-data-sparsity;closure-qoi-mesh-gci",
        "action": (
            "Add admitted or validation-only rows to a regime table with Re/Pr/Gr/"
            "Ra/Ri, wall-bulk delta T, and recirculation metrics."
        ),
        "acceptance_gate": (
            "State whether onset is observed, bracketed, or extrapolated; do not "
            "promote single-stream f/K/Nu labels in recirculation-cell rows."
        ),
        "scientific_controls": (
            "Separate reverse-flow diagnostics from closure fitting; keep corrected "
            "Salt-Q rows pending admission if terminal evidence is absent."
        ),
        "first_files": (
            ".agent/journal/2026-07-08/upcomer-onset.md;"
            "work_products/2026-07/2026-07-08/2026-07-08_upcomer_onset/README.md"
        ),
        "deliverable": "upcomer_onset_regime_update",
        "priority": 4,
    },
    {
        "packet_id": "A3.3",
        "area_id": "A3",
        "title": "Corrected Salt-Q terminal harvest into admission inventory",
        "blocks_addressed": "upcomer-onset-data-sparsity;f6-friction-re-correction",
        "action": (
            "When corrected Salt-Q jobs are terminal, harvest them into a run/"
            "admission inventory with BC labels, split eligibility, and steady-state "
            "evidence."
        ),
        "acceptance_gate": (
            "No downstream fit or validation row from Slurm completion alone; each "
            "row requires terminal solver, convergence/steadiness, BC labels, and "
            "provenance."
        ),
        "scientific_controls": (
            "Treat perturbation rows as sensitivity/correlation-support unless "
            "explicitly admitted as train/validation/holdout."
        ),
        "first_files": (
            ".agent/journal/2026-07-14/corrected-salt-q-live-job-admission.md;"
            "operational_notes/maps/cfd-runs-and-admission.md"
        ),
        "deliverable": "corrected_salt_q_terminal_admission_inventory",
        "priority": 6,
    },
]

RIGOR_GATES = [
    {
        "gate_id": "R1",
        "gate": "Provenance completeness",
        "rule": "Every row cites exact source paths, not chat memory or citation numbers.",
        "applies_to": "all areas",
        "failure_action": "block publication/admission claim",
    },
    {
        "gate_id": "R2",
        "gate": "No native CFD mutation",
        "rule": "All analysis consumes staged/repaired outputs or read-only source evidence.",
        "applies_to": "all areas",
        "failure_action": "stop and create separate approved repair/staging row",
    },
    {
        "gate_id": "R3",
        "gate": "GCI defensibility",
        "rule": "No GCI for two-level, source-blocked, non-monotone, oscillatory, divergent, or invalid-order triplets.",
        "applies_to": "A1",
        "failure_action": "mark diagnostic-only or blocked-missing-triplet",
    },
    {
        "gate_id": "R4",
        "gate": "Thermal admission separation",
        "rule": "HTC/UA/Nu cannot absorb heater, cooler, passive-loss, wall-storage, junction, or radiation residuals.",
        "applies_to": "A1,A2",
        "failure_action": "validation-only or blocked",
    },
    {
        "gate_id": "R5",
        "gate": "Predictive input discipline",
        "rule": "Forward predictive runs cannot use CFD mdot, realized CFD wallHeatFlux, or validation temperatures at runtime.",
        "applies_to": "A2",
        "failure_action": "label replay/diagnostic, not predictive",
    },
    {
        "gate_id": "R6",
        "gate": "Locked split",
        "rule": "Salt2=train, Salt3=validation, Salt4=holdout unless a later admitted split package supersedes it.",
        "applies_to": "A2,A3",
        "failure_action": "do not report final forward-v1 score",
    },
    {
        "gate_id": "R7",
        "gate": "Radiation semantics",
        "rule": "Current CFD wallHeatFlux includes rcExternalTemperature radiation; do not add separate qr on top of realized wallHeatFlux.",
        "applies_to": "A1,A2",
        "failure_action": "block parity/predictive claim",
    },
    {
        "gate_id": "R8",
        "gate": "No global hydraulic fudge",
        "rule": "Do not hide component, reset, redevelopment, cluster, or branch-apparent loss inside one global friction multiplier.",
        "applies_to": "A2,A3",
        "failure_action": "demote to diagnostic screen",
    },
    {
        "gate_id": "R9",
        "gate": "Recirculation label discipline",
        "rule": "Rows with recirculation-cell behavior cannot be promoted as ordinary single-stream f/K/Nu closures without policy evidence.",
        "applies_to": "A1,A3",
        "failure_action": "validation-only or blocked",
    },
    {
        "gate_id": "R10",
        "gate": "Documentation closeout",
        "rule": "Each gate-moving task writes status, journal, import manifest, package README, and index refresh when scoped.",
        "applies_to": "all areas",
        "failure_action": "task incomplete",
    },
]

MILESTONES = [
    {
        "milestone_id": "M1",
        "sequence": 1,
        "name": "Thermal admission review complete",
        "required_packets": "A1.1;A1.2",
        "exit_criterion": "Thermal rows have fit/validation/blocked decisions and no sign/heat-balance ambiguity.",
        "unlocks": "A1.3;A2.2",
    },
    {
        "milestone_id": "M2",
        "sequence": 2,
        "name": "Hydraulic correction candidate faithful or rejected",
        "required_packets": "A2.1;A3.1",
        "exit_criterion": "H1/F6 decision is scored under train/validation/holdout without thermal fitting.",
        "unlocks": "forward-v1 bounded candidate",
    },
    {
        "milestone_id": "M3",
        "sequence": 3,
        "name": "Setup-only thermal boundary candidate",
        "required_packets": "A2.2;A2.3",
        "exit_criterion": "Forward path has first-class setup-only boundary inputs or documented API patch plan.",
        "unlocks": "forward-v1 scorecard refresh",
    },
    {
        "milestone_id": "M4",
        "sequence": 4,
        "name": "Recirculation and corrected-Q evidence expansion",
        "required_packets": "A3.2;A3.3",
        "exit_criterion": "Upcomer onset remains explicitly observed/bracketed/extrapolated with admitted row status.",
        "unlocks": "broader validation and thesis uncertainty statements",
    },
    {
        "milestone_id": "M5",
        "sequence": 5,
        "name": "Forward-v1 readiness review",
        "required_packets": "M1;M2;M3",
        "exit_criterion": "Scorecard can run without violating predictive input, mesh/admission, or split gates.",
        "unlocks": "thesis-strength forward-model claim if metrics pass",
    },
]

SOURCE_MANIFEST = [
    {
        "source_id": "blocker_register",
        "path": ".agent/BLOCKERS.md",
        "use": "authoritative open blocker list",
    },
    {
        "source_id": "state",
        "path": ".agent/STATE.md",
        "use": "active task and recent activity state",
    },
    {
        "source_id": "mission",
        "path": "operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md",
        "use": "project finish-line and lane definitions",
    },
]

STALE_BLOCKERS = [
    "of12-reconstructpar-segfault",
    "no-mesh-for-gci",
    "cfd-no-radiation-parity",
    "refined-mesh-t-reconstruction-corruption",
]

OPEN_BLOCKERS = [
    "closure-qoi-mesh-gci",
    "thermal-cfd-1d-parity",
    "predictive-heater-cooler-wall-submodels",
    "upcomer-onset-data-sparsity",
    "fluid-external-boundary-api-gap",
    "f6-friction-re-correction",
]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


def split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def cited_paths(rows: Iterable[dict[str, object]], field: str) -> set[str]:
    paths: set[str] = set()
    for row in rows:
        for item in split_semicolon(str(row.get(field, ""))):
            if item and not item.startswith("../"):
                paths.add(item)
    return paths


def validate_sources() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    all_paths = cited_paths(AREAS, "key_sources") | cited_paths(WORK_PACKETS, "first_files")
    all_paths |= {item["path"] for item in SOURCE_MANIFEST}
    for path_text in sorted(all_paths):
        path = ROOT / path_text
        rows.append(
            {
                "path": path_text,
                "exists": path.exists(),
                "kind": "external_read_only" if path_text.startswith("../") else ("dir" if path.is_dir() else "file"),
            }
        )
    return rows


def blocker_coverage_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for blocker in OPEN_BLOCKERS:
        packets = [
            packet["packet_id"]
            for packet in WORK_PACKETS
            if blocker in split_semicolon(str(packet["blocks_addressed"]))
        ]
        areas = [
            area["area_id"]
            for area in AREAS
            if blocker in split_semicolon(str(area["primary_blockers"]))
            or blocker in split_semicolon(str(area["secondary_blockers"]))
        ]
        rows.append(
            {
                "blocker_id": blocker,
                "covered": bool(packets),
                "area_ids": ";".join(areas),
                "packet_ids": ";".join(packets),
                "coverage_note": "covered_by_actionable_packets" if packets else "missing_packet",
            }
        )
    return rows


def validate_plan(source_rows: list[dict[str, object]], coverage_rows: list[dict[str, object]]) -> list[str]:
    errors: list[str] = []
    missing_sources = [row["path"] for row in source_rows if row["exists"] is not True]
    if missing_sources:
        errors.append("missing cited sources: " + ", ".join(missing_sources))
    missing_blockers = [row["blocker_id"] for row in coverage_rows if row["covered"] is not True]
    if missing_blockers:
        errors.append("open blockers without work packet coverage: " + ", ".join(missing_blockers))
    area_ids = {area["area_id"] for area in AREAS}
    for packet in WORK_PACKETS:
        if packet["area_id"] not in area_ids:
            errors.append(f"packet {packet['packet_id']} has unknown area {packet['area_id']}")
    text_blob = json.dumps({"areas": AREAS, "packets": WORK_PACKETS, "gates": RIGOR_GATES})
    for blocker in STALE_BLOCKERS:
        if blocker in text_blob:
            errors.append(f"stale blocker appears in active plan text: {blocker}")
    return errors


def make_readme(summary: dict[str, object]) -> str:
    return f"""---
provenance:
  - .agent/BLOCKERS.md
  - .agent/STATE.md
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
tags: [blocker-register, coordination, forward-model, thermal-closure, friction, uncertainty]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: {TASK_ID}
date: 2026-07-14
role: Coordinator/Implementer/Tester/Writer
type: work_product
status: complete
---
# Blocker Resolution Plan

Generated: `{summary['generated_at']}`

## Purpose

This package turns the current open blockers into a scoped, testable research
plan. It is designed to drive gate-moving work with scientific rigor: every
work packet has source provenance, acceptance gates, failure modes, and a
documentation contract.

## Three Major Areas

1. **Thermal admission, mesh GCI, and internal Nu**: resolve sign, heat-balance,
   lower-leg Nu, and downcomer policy before any thermal fit or GCI claim.
2. **Forward predictive model and boundary/HX submodels**: move from
   diagnostic replay/proxy evidence toward setup-only predictive runs under the
   locked split.
3. **Hydraulic closure, recirculation physics, and API/model-form gaps**:
   decide H1/F6 paths, expand upcomer recirculation evidence, and prepare the
   first-class external-boundary API handoff.

## Current Counts

- Open blockers covered: `{summary['open_blockers_covered']}` / `{summary['open_blocker_count']}`
- Work packets: `{summary['work_packet_count']}`
- Rigor gates: `{summary['rigor_gate_count']}`
- Milestones: `{summary['milestone_count']}`
- Plan validation errors: `{summary['validation_error_count']}`

## Outputs

- `blocker_resolution_areas.csv`: the three major areas and their blocker map.
- `work_packets.csv`: ordered execution packets with acceptance gates.
- `scientific_rigor_checklist.csv`: non-negotiable scientific guardrails.
- `milestone_sequence.csv`: dependency-ordered milestone plan.
- `blocker_coverage.csv`: proof every open blocker has a work packet.
- `source_manifest.csv`: source paths validated by the builder.
- `summary.json`: machine-readable counts and validation result.

## Immediate Execution Order

1. `A1.1` thermal sign and heat-balance admission review.
2. `A2.1` faithful localized H1 hydraulic implementation or rejection.
3. `A2.2` setup-only cooler/HX and heater boundary candidate.
4. `A3.1` bounded F6 Re-dependent friction screen.
5. `A3.2` upcomer recirculation onset evidence expansion.

## Interpretation Boundary

This package does not resolve the blockers by assertion. It makes them
actionable and testable. A blocker should only be marked resolved or superseded
after a later package satisfies the acceptance gate and updates
`.agent/blockers.yml` with evidence.
"""


def build_package(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rows = validate_sources()
    coverage = blocker_coverage_rows()
    errors = validate_plan(source_rows, coverage)

    write_csv(output_dir / "blocker_resolution_areas.csv", AREAS, list(AREAS[0].keys()))
    write_csv(output_dir / "work_packets.csv", WORK_PACKETS, list(WORK_PACKETS[0].keys()))
    write_csv(output_dir / "scientific_rigor_checklist.csv", RIGOR_GATES, list(RIGOR_GATES[0].keys()))
    write_csv(output_dir / "milestone_sequence.csv", MILESTONES, list(MILESTONES[0].keys()))
    write_csv(output_dir / "source_manifest.csv", source_rows, ["path", "exists", "kind"])
    write_csv(output_dir / "blocker_coverage.csv", coverage, ["blocker_id", "covered", "area_ids", "packet_ids", "coverage_note"])

    priority_counts = Counter(str(packet["priority"]) for packet in WORK_PACKETS)
    summary = {
        "task_id": TASK_ID,
        "generated_at": now(),
        "output_dir": rel(output_dir),
        "area_count": len(AREAS),
        "work_packet_count": len(WORK_PACKETS),
        "rigor_gate_count": len(RIGOR_GATES),
        "milestone_count": len(MILESTONES),
        "open_blocker_count": len(OPEN_BLOCKERS),
        "open_blockers_covered": sum(1 for row in coverage if row["covered"] is True),
        "priority_counts": dict(sorted(priority_counts.items())),
        "validation_error_count": len(errors),
        "validation_errors": errors,
        "stale_blockers_excluded": STALE_BLOCKERS,
        "native_solver_outputs_mutated": False,
        "external_cfd_modeling_tools_mutated": False,
        "next_recommended_packet": "A1.1",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(make_readme(summary), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_package(Path(args.output_dir))
    if summary["validation_error_count"]:
        for error in summary["validation_errors"]:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
