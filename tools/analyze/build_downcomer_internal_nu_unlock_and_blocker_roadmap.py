#!/usr/bin/env python3
"""Build AGENT-466 downcomer Internal-Nu unlock and blocker roadmap package.

This pass uses existing evidence only. It tries the simplest non-upcomer path
first, the downcomer, and records the later studies needed for the remaining
blockers without promoting diagnostic rows into fit evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-466"
DATE = "2026-07-16"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap")
OUT = ROOT / OUT_REL

AGENT459 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock"
AGENT455 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution"
AGENT461 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard"
AGENT464 = ROOT / "work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard"
LITREV_MAP = ROOT / "operational_notes/maps/literature-synthesis-and-gates.md"
THERMAL_MAP = ROOT / "operational_notes/maps/thermal-closures-and-internal-nu.md"
MESH_MAP = ROOT / "operational_notes/maps/mesh-gci-and-uncertainty.md"
FORWARD_MAP = ROOT / "operational_notes/maps/forward-predictive-model.md"
BLOCKERS = ROOT / ".agent/blockers.yml"

BRANCH_ADMISSION = AGENT459 / "branch_local_thermal_admission.csv"
FIT_ROWS = AGENT459 / "internal_nu_fit_admissible_rows.csv"
FINAL_USE_GCI = AGENT459 / "final_use_closure_qoi_gci.csv"
UNBLOCK_QUEUE = AGENT459 / "targeted_extraction_admission_queue.csv"
AGENT455_CANDIDATES = AGENT455 / "leg_specific_internal_nu_candidate_rows.csv"
AGENT455_MESH = AGENT455 / "mesh_gci_gate_for_admitted_candidates.csv"

SOURCE_PATHS = {
    "agent459_branch_admission": BRANCH_ADMISSION,
    "agent459_fit_rows": FIT_ROWS,
    "agent459_final_use_gci": FINAL_USE_GCI,
    "agent459_unblock_queue": UNBLOCK_QUEUE,
    "agent455_candidates": AGENT455_CANDIDATES,
    "agent455_mesh": AGENT455_MESH,
    "agent461_m3ts": AGENT461 / "README.md",
    "agent464_f6_upcomer": AGENT464 / "README.md",
    "litrev_map": LITREV_MAP,
    "thermal_map": THERMAL_MAP,
    "mesh_map": MESH_MAP,
    "forward_map": FORWARD_MAP,
    "blocker_register": BLOCKERS,
}

DOWNCOMER_COLUMNS = [
    "case_id",
    "canonical_leg_id",
    "candidate_qoi",
    "residual_owner_status",
    "sign_heat_balance_status",
    "recirculation_status",
    "mesh_gci_status",
    "litrev_gate_status",
    "admission_decision",
    "blocking_reason",
    "source_path",
]
POLICY_COLUMNS = [
    "canonical_leg_id",
    "candidate_rows",
    "nu_candidate_rows",
    "residual_owner_pass_rows",
    "sign_heat_balance_pass_rows",
    "recirculation_pass_rows",
    "mesh_gci_pass_rows",
    "fit_admissible_internal_nu_rows",
    "decision",
    "next_required_artifact",
    "acceptance_signal",
    "do_not_do_guardrail",
]
LITREV_COLUMNS = [
    "gate",
    "downcomer_status",
    "interpretation",
    "source_path",
]
FUTURE_COLUMNS = [
    "study_id",
    "blocker_id",
    "priority",
    "why_blocked",
    "next_required_artifact",
    "acceptance_signal",
    "do_not_do_guardrail",
    "canonical_source_paths",
]
DECISION_COLUMNS = [
    "blocker_id",
    "decision",
    "can_update_blocker_register",
    "resolved_by",
    "resolved_on",
    "criteria_passed",
    "criteria_failed",
    "scientific_interpretation",
    "next_unlock_sequence",
]
MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.12g}" if math.isfinite(value) else ""
    return str(value)


def yes(value: Any) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "pass"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: format_value(row.get(column, "")) for column in columns})
    return len(materialized)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def status_from_counts(pass_rows: int, total_rows: int, gate_name: str) -> str:
    if total_rows <= 0:
        return f"{gate_name}_no_rows"
    if pass_rows == total_rows:
        return f"{gate_name}_pass_{pass_rows}_of_{total_rows}"
    if pass_rows > 0:
        return f"{gate_name}_partial_{pass_rows}_of_{total_rows}"
    return f"{gate_name}_fail_0_of_{total_rows}"


def split_gate_vector(row: dict[str, str]) -> dict[str, str]:
    vector: dict[str, str] = {}
    for part in row.get("gate_vector", "").split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        vector[key] = value
    return vector


def downcomer_admission_rows() -> list[dict[str, Any]]:
    branch_rows = read_csv(BRANCH_ADMISSION)
    fit_rows = read_csv(FIT_ROWS)
    downcomer_branch = next(row for row in branch_rows if row["canonical_leg_id"] == "downcomer_right_vertical")
    total = int(downcomer_branch["candidate_rows"])
    residual_status = status_from_counts(int(downcomer_branch["residual_owner_pass_rows"]), total, "residual_owner")
    sign_status = status_from_counts(int(downcomer_branch["sign_heat_balance_pass_rows"]), total, "sign_heat_balance")
    recirc_status = status_from_counts(int(downcomer_branch["recirculation_pass_rows"]), total, "recirculation")
    mesh_status = status_from_counts(int(downcomer_branch["mesh_gci_pass_rows"]), total, "mesh_gci")

    rows: list[dict[str, Any]] = []
    for row in fit_rows:
        if row.get("canonical_leg_id") != "downcomer_right_vertical":
            continue
        vector = split_gate_vector(row)
        missing = [key for key in ("sign_heat_balance", "recirculation", "mesh_gci") if vector.get(key) != "yes"]
        admitted = yes(row.get("fit_admissible", ""))
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "canonical_leg_id": "downcomer_right_vertical",
                "candidate_qoi": row.get("qoi", ""),
                "residual_owner_status": residual_status,
                "sign_heat_balance_status": sign_status,
                "recirculation_status": recirc_status,
                "mesh_gci_status": mesh_status,
                "litrev_gate_status": "pass_methodology_only_no_fit_until_heat_loss_and_mesh_gates_pass",
                "admission_decision": "admitted" if admitted else "not_admitted_downcomer_policy_sign_recirculation_mesh",
                "blocking_reason": "" if admitted else ";".join(missing + ["downcomer_policy_not_yet_admitted"]),
                "source_path": row.get("source_path", ""),
            }
        )
    return rows


def downcomer_policy_rows(admission: list[dict[str, Any]]) -> list[dict[str, Any]]:
    branch = next(row for row in read_csv(BRANCH_ADMISSION) if row["canonical_leg_id"] == "downcomer_right_vertical")
    admitted = sum(1 for row in admission if row["admission_decision"] == "admitted")
    decision = "admit_downcomer_internal_nu" if admitted else "keep_blocked_pending_downcomer_policy_and_same_qoi_gci"
    return [
        {
            "canonical_leg_id": "downcomer_right_vertical",
            "candidate_rows": branch["candidate_rows"],
            "nu_candidate_rows": branch["nu_candidate_rows"],
            "residual_owner_pass_rows": branch["residual_owner_pass_rows"],
            "sign_heat_balance_pass_rows": branch["sign_heat_balance_pass_rows"],
            "recirculation_pass_rows": branch["recirculation_pass_rows"],
            "mesh_gci_pass_rows": branch["mesh_gci_pass_rows"],
            "fit_admissible_internal_nu_rows": admitted,
            "decision": decision,
            "next_required_artifact": "downcomer thermal policy memo with row-level sign/enthalpy, low-recirculation, and same-QOI GCI evidence",
            "acceptance_signal": ">=1 downcomer Nu-equivalent row passes residual-owner, sign/heat-balance, recirculation, LitRev, and publication-ready same-QOI GCI gates",
            "do_not_do_guardrail": "do not fit downcomer Nu from rows with unresolved heat-balance sign, missing low-recirculation evidence, or non-publication GCI",
        }
    ]


def litrev_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "source_envelope_before_correlation",
            "downcomer_status": "methodology_pass_no_active_fit",
            "interpretation": "Downcomer remains the simplest ordinary-pipe candidate, but no source-bounded correlation is promoted until the branch row is admitted.",
            "source_path": rel(LITREV_MAP),
        },
        {
            "gate": "property_lane_fixed_before_residual_fit",
            "downcomer_status": "pass_guardrail",
            "interpretation": "Use the current Jin/property-lane context; do not hide residuals in property or Nu retuning.",
            "source_path": rel(LITREV_MAP),
        },
        {
            "gate": "reset_named_losses_before_global_friction",
            "downcomer_status": "pass_guardrail",
            "interpretation": "Pressure/reset/development questions stay separate from thermal Nu admission.",
            "source_path": rel(LITREV_MAP),
        },
        {
            "gate": "heat_loss_separated_before_internal_nu",
            "downcomer_status": "blocking_until_sign_heat_balance_resolved",
            "interpretation": "The downcomer cannot absorb passive wall, storage, source, or boundary residuals into Nu.",
            "source_path": rel(LITREV_MAP),
        },
        {
            "gate": "cfd_validity_before_coefficient_export",
            "downcomer_status": "blocking_until_low_recirculation_evidence_exists",
            "interpretation": "A low-recirculation or non-recirculating branch-local row is required before exporting a single-stream Nu label.",
            "source_path": rel(LITREV_MAP),
        },
    ]


def future_studies_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "study_id": "downcomer_policy_low_recirculation_and_mesh_gci",
            "blocker_id": "closure-qoi-mesh-gci",
            "priority": "P0",
            "why_blocked": "Downcomer has one Nu candidate but 0 sign/heat-balance, 0 recirculation, and 0 mesh/GCI pass rows.",
            "next_required_artifact": "Downcomer thermal policy/admission memo plus same-QOI Nu or HTC/UA GCI evidence.",
            "acceptance_signal": ">=1 downcomer Nu-equivalent row passes all admission gates.",
            "do_not_do_guardrail": "Do not fit ordinary Nu from unresolved sign, recirculation, or non-publication GCI rows.",
            "canonical_source_paths": f"{rel(BRANCH_ADMISSION)};{rel(FIT_ROWS)};{rel(FINAL_USE_GCI)}",
        },
        {
            "study_id": "heater_source_sign_heat_balance",
            "blocker_id": "closure-qoi-mesh-gci",
            "priority": "P1",
            "why_blocked": "Heater leg is a source region; source ownership, repaired sign label conflict, heat-balance, and mesh/GCI still block fit.",
            "next_required_artifact": "Heater source/enthalpy/sign admission table plus same-QOI mesh triplet.",
            "acceptance_signal": ">=1 heater Nu-equivalent row has source, sign, residual-owner, recirculation, and GCI gates passing.",
            "do_not_do_guardrail": "Do not use Nu to absorb heater source, wall-storage, or sign-label residuals.",
            "canonical_source_paths": f"{rel(BRANCH_ADMISSION)};{rel(UNBLOCK_QUEUE)}",
        },
        {
            "study_id": "cooler_hx_boundary_residual_separation",
            "blocker_id": "closure-qoi-mesh-gci",
            "priority": "P1",
            "why_blocked": "Cooler/HX branch removal is a boundary/HX residual, not separable as internal convection on current evidence.",
            "next_required_artifact": "Cooler/HX shell-boundary residual separation package.",
            "acceptance_signal": "HX removal separated from internal convection without realized wallHeatFlux or imposed cooler duty.",
            "do_not_do_guardrail": "Keep setup-only UA/effectiveness separate from internal Nu until residuals are separated.",
            "canonical_source_paths": f"{rel(BRANCH_ADMISSION)};{rel(UNBLOCK_QUEUE)}",
        },
        {
            "study_id": "upcomer_hybrid_onset_classification",
            "blocker_id": "upcomer-onset-data-sparsity",
            "priority": "P1",
            "why_blocked": "Upcomer/test-section has observed recirculation points but no non-recirculating anchor and 0 single-stream fit rows.",
            "next_required_artifact": "Onset classification as observed, bracketed, extrapolated, or rejected; or explicit hybrid recirculation model.",
            "acceptance_signal": "Onset decision made without single-stream coefficient promotion.",
            "do_not_do_guardrail": "Do not label recirculating upcomer/test-section rows as single-stream true Nu, f_D, or K fits.",
            "canonical_source_paths": f"{rel(AGENT464 / 'README.md')};{rel(THERMAL_MAP)}",
        },
        {
            "study_id": "same_qoi_final_use_mesh_gci",
            "blocker_id": "closure-qoi-mesh-gci",
            "priority": "P2",
            "why_blocked": "AGENT-459 found 13 final-use non-upcomer GCI rows and 0 publication-ready rows.",
            "next_required_artifact": "Same-QOI mesh/GCI rerun or explicit exclusion decision after branch admission.",
            "acceptance_signal": "Every final-use row is either publication-ready or excluded before closeout.",
            "do_not_do_guardrail": "Do not spend GCI effort on rows that branch-local admission will exclude.",
            "canonical_source_paths": rel(FINAL_USE_GCI),
        },
        {
            "study_id": "coupled_m3ts_test_section_score",
            "blocker_id": "predictive-wall-test-section-submodels",
            "priority": "P0",
            "why_blocked": "TS1/TS2 are runtime-legal but fail held-out heat-loss gates and have no coupled M3+TS Salt3/Salt4 score.",
            "next_required_artifact": "Frozen TS1/TS2 coupled M3+TS scorecard for mdot, Tmean, loop-delta, TP, and TW.",
            "acceptance_signal": "Validation/holdout improvement over M2/M3 baselines without runtime CFD leakage.",
            "do_not_do_guardrail": "Do not consume realized wallHeatFlux, CFD mdot, imposed cooler duty, or validation temperatures at runtime.",
            "canonical_source_paths": rel(AGENT461 / "README.md"),
        },
        {
            "study_id": "f6_friction_re_correction",
            "blocker_id": "f6-friction-re-correction",
            "priority": "P1",
            "why_blocked": "Current PM5 evidence is diagnostic-only under material recirculation; 0 F6 fit-admissible rows.",
            "next_required_artifact": "Non-recirculating pressure rows or explicit recirculation-modeled F6/onset closure with validation improvement.",
            "acceptance_signal": "Improves validation/holdout over F3_shah_apparent without hidden global multiplier.",
            "do_not_do_guardrail": "Do not promote recirculating diagnostic rows into true f_D or K closure fits.",
            "canonical_source_paths": rel(AGENT464 / "README.md"),
        },
        {
            "study_id": "wall_thermal_circuit_model",
            "blocker_id": "predictive-wall-test-section-submodels",
            "priority": "P2",
            "why_blocked": "Wall/test-section/passive-boundary heat loss lacks an admitted setup-only physical circuit model.",
            "next_required_artifact": "Segment wall thermal-circuit model with resistance/storage terms and setup-only runtime inputs.",
            "acceptance_signal": "Held-out TP/TW and heat-loss scoring improves without realized CFD thermal outputs.",
            "do_not_do_guardrail": "Do not double-count radiation or use CFD wallHeatFlux as a runtime source.",
            "canonical_source_paths": f"{rel(FORWARD_MAP)};{rel(AGENT461 / 'README.md')}",
        },
        {
            "study_id": "segment_pressure_models",
            "blocker_id": "f6-friction-re-correction",
            "priority": "P2",
            "why_blocked": "Segment pressure terms need branch-local drive/loss/reset/development separation.",
            "next_required_artifact": "Segment pressure model scorecard after equation contract completion.",
            "acceptance_signal": "Reports mdot impact by segment and separates buoyancy, distributed friction, reset/development, K, junction, and onset terms.",
            "do_not_do_guardrail": "Do not use a hidden global pressure multiplier.",
            "canonical_source_paths": rel(FORWARD_MAP),
        },
        {
            "study_id": "segment_thermal_models",
            "blocker_id": "predictive-wall-test-section-submodels",
            "priority": "P2",
            "why_blocked": "Thermal model forms differ by heater, cooler/HX, downcomer, upcomer/test-section, and junction/stub regions.",
            "next_required_artifact": "Segment thermal model scorecard with separate source/sink/boundary/storage residuals.",
            "acceptance_signal": "Scores TP/TW, Tmean, loop-delta, and mdot coupling impacts on train/validation/holdout.",
            "do_not_do_guardrail": "Do not tune internal Nu to absorb external boundary/source/storage residuals.",
            "canonical_source_paths": f"{rel(FORWARD_MAP)};{rel(THERMAL_MAP)}",
        },
        {
            "study_id": "boundary_layer_development_scorecard",
            "blocker_id": "closure-qoi-mesh-gci",
            "priority": "P3",
            "why_blocked": "Boundary-layer and entrance/reset development effects are not yet quantified by segment.",
            "next_required_artifact": "Boundary-layer development ablation scorecard.",
            "acceptance_signal": "Reports mdot, TP, TW, Tmean, and loop-delta impacts by segment.",
            "do_not_do_guardrail": "Do not hide segment-specific development physics in a global multiplier.",
            "canonical_source_paths": f"{rel(FORWARD_MAP)};{rel(LITREV_MAP)}",
        },
        {
            "study_id": "thesis_upcomer_recirculation_writeup",
            "blocker_id": "upcomer-onset-data-sparsity",
            "priority": "P3",
            "why_blocked": "The thesis/paper needs a clear explanation that test-section rows are in the upcomer and recirculating.",
            "next_required_artifact": "Thesis-ready upcomer/test-section recirculation section with accepted labels and rejected fit labels.",
            "acceptance_signal": "Reader can see why upcomer data inform hybrid/onset physics but not ordinary single-stream coefficients.",
            "do_not_do_guardrail": "Do not imply the test section is a separate non-upcomer fit lane.",
            "canonical_source_paths": f"{rel(THERMAL_MAP)};{rel(AGENT464 / 'README.md')}",
        },
    ]
    return rows


def decision_rows(admission: list[dict[str, Any]], futures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    admitted = sum(1 for row in admission if row["admission_decision"] == "admitted")
    unresolved_downcomer = sum(1 for row in admission if row["admission_decision"] != "admitted")
    return [
        {
            "blocker_id": "closure-qoi-mesh-gci",
            "decision": "resolved" if admitted and not unresolved_downcomer else "not_resolved_downcomer_narrowed",
            "can_update_blocker_register": "yes",
            "resolved_by": rel(OUT) if admitted and not unresolved_downcomer else "",
            "resolved_on": DATE if admitted and not unresolved_downcomer else "",
            "criteria_passed": "downcomer_prioritized;litrev_gate_policy_encoded;future_studies_documented;upcomer_excluded_from_single_stream_fit",
            "criteria_failed": "downcomer_sign_heat_balance_missing;downcomer_low_recirculation_missing;downcomer_same_qoi_publication_gci_missing" if unresolved_downcomer else "",
            "scientific_interpretation": "Downcomer is the best next non-upcomer candidate, but current evidence still cannot admit Internal-Nu fitting.",
            "next_unlock_sequence": " -> ".join(row["study_id"] for row in futures[:5]),
        }
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    roles = {
        "agent459_branch_admission": "branch-local gate summary",
        "agent459_fit_rows": "row-level Internal-Nu gate vectors",
        "agent459_final_use_gci": "non-upcomer final-use mesh/GCI state",
        "agent459_unblock_queue": "targeted unblock queue",
        "agent455_candidates": "upstream leg-specific candidates",
        "agent455_mesh": "upstream mesh/GCI candidates",
        "agent461_m3ts": "predictive wall/test-section blocker evidence",
        "agent464_f6_upcomer": "F6 and upcomer blocker evidence",
        "litrev_map": "LitRev methodology gates",
        "thermal_map": "thermal/Internal-Nu continuity hub",
        "mesh_map": "mesh/GCI continuity hub",
        "forward_map": "forward predictive model continuity hub",
        "blocker_register": "current blocker ledger",
    }
    return [{"source_id": key, "path": rel(path), "exists": path.exists(), "role": roles[key]} for key, path in SOURCE_PATHS.items()]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(BRANCH_ADMISSION)}
  - {rel(FIT_ROWS)}
  - {rel(FINAL_USE_GCI)}
  - {rel(UNBLOCK_QUEUE)}
  - {rel(LITREV_MAP)}
tags: [internal-nu, downcomer, closure-qoi, mesh-gci, litrev-gates, blocker-roadmap]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
  - operational_notes/maps/forward-predictive-model.md
task: {TASK}
date: {DATE}
role: Coordinator/Thermal-modeling/Internal-Nu/Mesh-GCI/Implementer/Tester/Writer
type: work_product
status: complete
---
# Downcomer Internal-Nu Unlock And Blocker Roadmap

Generated: `{summary["generated_at"]}`

## Decision

`closure-qoi-mesh-gci`: `{summary["blocker_decision"]}`.

The downcomer is still the best first non-upcomer candidate for ordinary
Internal-Nu admission, but current evidence does not admit a fit. The downcomer
row is blocked by unresolved sign/heat-balance, missing low-recirculation
admission evidence, and missing publication-ready same-QOI mesh/GCI.

## Results

- Downcomer Internal-Nu candidate rows reviewed: `{summary["downcomer_internal_nu_candidate_rows"]}`.
- Downcomer fit-admissible rows: `{summary["downcomer_fit_admissible_rows"]}`.
- Future studies documented: `{summary["future_studies_documented"]}`.
- Open blockers covered by future studies: `{summary["open_blockers_covered"]}` / `{summary["open_blockers_total"]}`.

## Method

This package applies the LitRev branchwise closure discipline: no global
Nu/f/UA tuning, no source/boundary/storage residual absorption into Internal Nu,
and no single-stream coefficient export until CFD-validity and mesh/GCI gates
pass. It uses existing AGENT-455/459/461/464 evidence only and mutates no native
CFD solver output.

## Outputs

- `downcomer_admission_gate.csv`
- `downcomer_policy_decision.csv`
- `litrev_gate_application.csv`
- `future_studies_and_blockers.csv`
- `blocker_resolution_decision.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def open_blockers_from_register() -> list[str]:
    blockers: list[str] = []
    current_id = ""
    current_status = ""
    for line in BLOCKERS.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- id: "):
            if current_id and current_status == "open":
                blockers.append(current_id)
            current_id = stripped.split(":", 1)[1].strip()
            current_status = ""
        elif stripped.startswith("status: "):
            current_status = stripped.split(":", 1)[1].strip()
    if current_id and current_status == "open":
        blockers.append(current_id)
    return blockers


def build_package(out: Path = OUT) -> dict[str, Any]:
    admission = downcomer_admission_rows()
    policy = downcomer_policy_rows(admission)
    litrev = litrev_rows()
    futures = future_studies_rows()
    decisions = decision_rows(admission, futures)
    manifest = source_manifest_rows()

    write_csv(out / "downcomer_admission_gate.csv", admission, DOWNCOMER_COLUMNS)
    write_csv(out / "downcomer_policy_decision.csv", policy, POLICY_COLUMNS)
    write_csv(out / "litrev_gate_application.csv", litrev, LITREV_COLUMNS)
    write_csv(out / "future_studies_and_blockers.csv", futures, FUTURE_COLUMNS)
    write_csv(out / "blocker_resolution_decision.csv", decisions, DECISION_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)

    open_blockers = open_blockers_from_register()
    future_blockers = {row["blocker_id"] for row in futures}
    admitted = sum(1 for row in admission if row["admission_decision"] == "admitted")
    summary = {
        "task": TASK,
        "generated_at": utc_now(),
        "blocker_decision": decisions[0]["decision"],
        "downcomer_internal_nu_candidate_rows": len(admission),
        "downcomer_fit_admissible_rows": admitted,
        "downcomer_decision_counts": dict(Counter(row["admission_decision"] for row in admission)),
        "future_studies_documented": len(futures),
        "open_blockers_total": len(open_blockers),
        "open_blockers_covered": sum(1 for blocker in open_blockers if blocker in future_blockers),
        "open_blockers": open_blockers,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action_taken": False,
        "external_fluid_mutated": False,
    }
    write_json(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
