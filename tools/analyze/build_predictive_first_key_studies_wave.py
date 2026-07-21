#!/usr/bin/env python3
"""Build a first-wave completion package for predictive-model studies.

This builder consolidates existing study artifacts into a handoff surface for
the first key predictive-model studies. It does not run Fluid or OpenFOAM, fit
coefficients, select a model, or admit a closure.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-PRED-FIRST-KEY-STUDIES-WAVE-2026-07-21"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave")
OUT = ROOT / OUT_REL

STARTER = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter"
PHASE1 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_1_external_bc_radiation_integration"
)
PHASE2 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_2_split_heat_loss_evidence"
)
PRESSURE_BASIS = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_pressure_plane_basis_standardization"
)
PRESSURE_FREEZE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_pressure_corner_publication_freeze"
)
ROADMAP = ROOT / "reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md"
FORWARD_MAP = ROOT / "operational_notes/maps/forward-predictive-model.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def baseline_control_surface() -> list[dict[str, Any]]:
    baseline_rows = read_csv(STARTER / "baseline_model_contract.csv")
    runtime_rows = read_csv(STARTER / "runtime_and_split_gate_audit.csv")
    freeze_rows = read_csv(STARTER / "freeze_readiness_matrix.csv")
    guardrails = read_csv(STARTER / "scorecard_release_guardrails.csv")

    failed_required = [
        row["gate_id"]
        for row in freeze_rows
        if row["required_for_freeze"] in {"yes", "all rows", "all blind/current holdout/external rows"}
        and not row["current_state"].startswith("pass")
    ]
    runtime_failures = [row for row in runtime_rows if row["status"] != "pass"]
    forbidden_runtime = [row for row in guardrails if "forbidden" in " ".join(row.values()).lower()]

    return [
        {
            "study_id": "S0",
            "surface": "baseline_current_model",
            "completion_status": "complete_control_surface_ready",
            "baseline_contract_rows": len(baseline_rows),
            "runtime_gate_failures": len(runtime_failures),
            "freeze_gate_failures": len(failed_required),
            "fit_enabled_final_rows": 0,
            "final_freeze_status": "FINAL_FREEZE_TBD_absent",
            "claim_boundary": "baseline/reference only; no final predictive accuracy claim",
            "acceptance_signal": "targets are prediction-ready, explicitly missing, or blocker-labeled; zero runtime leakage",
            "next_action": "use as S0 thesis table and common reference for later study rows",
            "source_paths": ";".join(
                [
                    rel(STARTER / "baseline_model_contract.csv"),
                    rel(STARTER / "runtime_and_split_gate_audit.csv"),
                    rel(STARTER / "freeze_readiness_matrix.csv"),
                ]
            ),
        },
        {
            "study_id": "S0",
            "surface": "release_guardrails",
            "completion_status": "complete_runtime_policy_ready",
            "baseline_contract_rows": len(baseline_rows),
            "runtime_gate_failures": len(runtime_failures),
            "freeze_gate_failures": len(failed_required),
            "fit_enabled_final_rows": 0,
            "final_freeze_status": "blocked_pending_admitted_candidate",
            "claim_boundary": "holdout/external rows score-only until frozen candidate exists",
            "acceptance_signal": f"{len(forbidden_runtime)} guardrail rows retain forbidden runtime fields",
            "next_action": "propagate these guardrails into any model-specific scorer",
            "source_paths": rel(STARTER / "scorecard_release_guardrails.csv"),
        },
    ]


def external_bc_completion_matrix() -> list[dict[str, Any]]:
    segment_rows = read_csv(PHASE1 / "external_bc_segment_role_audit.csv")
    handoff_rows = read_csv(PHASE1 / "fluid_handoff_contract.csv")
    validation = read_json(PHASE1 / "validation_report.json")

    runtime_status = Counter(row["predictive_runtime_status"] for row in segment_rows)
    boundary_status = Counter(row["boundary_field_availability_status"] for row in segment_rows)
    blocked_rows = [
        row
        for row in segment_rows
        if "unavailable" in row["boundary_field_availability_status"]
        or "document_only" in row["predictive_runtime_status"]
    ]

    return [
        {
            "study_id": "S1",
            "surface": "external_bc_schema_and_audit",
            "completion_status": "repo_local_contract_complete",
            "segment_role_rows": len(segment_rows),
            "schema_ready_rows": runtime_status.get("schema_ready_setup_inputs_only", 0),
            "blocked_or_document_rows": len(blocked_rows),
            "fluid_api_status": "open_in_TODO-FLUID-EXTERNAL-BC-DICT",
            "validation_status": validation.get("status", "unknown"),
            "claim_boundary": "setup-facing dictionary contract ready; Fluid source integration not done here",
            "acceptance_signal": "segment/role rows are setup-facing or explicitly unavailable; radiation replay semantics fixed",
            "next_action": "claim TODO-FLUID-EXTERNAL-BC-DICT only if external Fluid edits are allowed",
            "source_paths": ";".join(
                [
                    rel(PHASE1 / "external_bc_dictionary_contract.csv"),
                    rel(PHASE1 / "external_bc_segment_role_audit.csv"),
                    rel(PHASE1 / "fluid_handoff_contract.csv"),
                ]
            ),
        },
        {
            "study_id": "S1",
            "surface": "fluid_handoff",
            "completion_status": "handoff_complete_source_edit_open",
            "segment_role_rows": len(segment_rows),
            "schema_ready_rows": runtime_status.get("schema_ready_setup_inputs_only", 0),
            "blocked_or_document_rows": len(blocked_rows),
            "fluid_api_status": f"handoff_rows={len(handoff_rows)}",
            "validation_status": ";".join(f"{key}={value}" for key, value in sorted(boundary_status.items())),
            "claim_boundary": "no external Fluid files changed by first-wave package",
            "acceptance_signal": "Fluid/API work is explicit follow-on, not silently claimed complete",
            "next_action": "implement parser/runtime bridge in external Fluid row after ownership check",
            "source_paths": rel(PHASE1 / "runtime_mode_matrix.csv"),
        },
    ]


def split_heat_completion_matrix() -> list[dict[str, Any]]:
    summary = read_json(PHASE2 / "summary.json")
    missing_rows = read_csv(PHASE2 / "missing_field_queue.csv")
    runtime_rows = read_csv(PHASE2 / "runtime_legality_audit.csv")

    return [
        {
            "study_id": "S2",
            "surface": "split_heat_loss_evidence",
            "completion_status": "complete_evidence_gate_ready",
            "split_junction_rows": summary["split_junction_rows"],
            "heat_path_rows": summary["heat_path_rows"],
            "residual_owner_rows": summary["residual_owner_rows"],
            "missing_field_rows": len(missing_rows),
            "qr_output_rows_admitted": summary["qr_output_rows_admitted"],
            "solid_storage_runtime_rows_admitted": summary["solid_storage_runtime_rows_admitted"],
            "claim_boundary": "diagnostic evidence and missing-field ledger; no heat-loss model admission",
            "acceptance_signal": "qr/storage absences recorded without inference; residual owners are explicit",
            "next_action": "Phase 3 wall/test-section scoring can consume this evidence gate",
            "source_paths": ";".join(
                [
                    rel(PHASE2 / "split_junction_stub_heat_rows.csv"),
                    rel(PHASE2 / "heat_path_evidence_matrix.csv"),
                    rel(PHASE2 / "energy_residual_owner_matrix.csv"),
                ]
            ),
        },
        {
            "study_id": "S2",
            "surface": "runtime_legality",
            "completion_status": "complete_runtime_gate_ready",
            "split_junction_rows": summary["split_junction_rows"],
            "heat_path_rows": summary["heat_path_rows"],
            "residual_owner_rows": summary["residual_owner_rows"],
            "missing_field_rows": len(missing_rows),
            "qr_output_rows_admitted": summary["qr_output_rows_admitted"],
            "solid_storage_runtime_rows_admitted": summary["solid_storage_runtime_rows_admitted"],
            "claim_boundary": "no realized wallHeatFlux, residual, or storage back-calculation at runtime",
            "acceptance_signal": f"{len(runtime_rows)} runtime legality rows preserve no-fit/no-admission policy",
            "next_action": "carry runtime audit into any Phase 3 scorer",
            "source_paths": rel(PHASE2 / "runtime_legality_audit.csv"),
        },
    ]


def pressure_source_envelope_gate() -> list[dict[str, Any]]:
    basis_summary = read_json(PRESSURE_BASIS / "summary.json")
    pressure_rows = read_csv(PRESSURE_FREEZE / "canonical_pressure_corner_result.csv")
    labels = Counter(row["final_label"] for row in pressure_rows)
    admissions = Counter(row["admission_status"] for row in pressure_rows)

    return [
        {
            "study_id": "S3",
            "surface": "pressure_source_envelope_release_gate",
            "completion_status": "complete_diagnostic_release_gate_ready",
            "pressure_basis_rows": basis_summary["ledger_rows"],
            "corner_publication_rows": len(pressure_rows),
            "section_effective_rows": labels.get("section_effective", 0),
            "component_k_admitted_rows": 0,
            "f6_admitted_rows": 0,
            "claim_boundary": "section-effective pressure residual only; no component-K or F6 admission",
            "acceptance_signal": "pressure rows carry basis/source labels and publication-safe non-admission",
            "next_action": "do not fit hydraulic coefficients until same-QOI UQ, isolation, and recirculation gates pass",
            "source_paths": ";".join(
                [
                    rel(PRESSURE_BASIS / "pressure_plane_basis_standardization.csv"),
                    rel(PRESSURE_FREEZE / "canonical_pressure_corner_result.csv"),
                ]
            ),
        },
        {
            "study_id": "S3",
            "surface": "non_admission_guard",
            "completion_status": "complete_guardrail_ready",
            "pressure_basis_rows": basis_summary["ledger_rows"],
            "corner_publication_rows": len(pressure_rows),
            "section_effective_rows": labels.get("section_effective", 0),
            "component_k_admitted_rows": sum(
                1 for row in pressure_rows if "component" in row["admission_status"] and "not_admitted" not in row["admission_status"]
            ),
            "f6_admitted_rows": sum(
                1 for row in pressure_rows if "F6" in row["admission_status"] and "not_admitted" not in row["admission_status"]
            ),
            "claim_boundary": ";".join(f"{key}={value}" for key, value in sorted(admissions.items())),
            "acceptance_signal": "no clipped K, no hidden global multiplier, no basis-mismatched component claim",
            "next_action": "feed only residual-attribution columns to predictive scorecard until hydraulic gates pass",
            "source_paths": rel(PRESSURE_FREEZE / "pressure_corner_publication_claims.csv"),
        },
    ]


def wave_status_table(
    baseline: list[dict[str, Any]],
    external: list[dict[str, Any]],
    split_heat: list[dict[str, Any]],
    pressure: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "study_id": "S0",
            "study_name": "baseline_control_surface",
            "wave_status": "complete",
            "primary_output": "baseline_control_surface.csv",
            "claim_class": "train/support/holdout/external split guardrail, no final accuracy",
            "next_gate": "candidate admission and source/property release remain blocked",
            "source_paths": baseline[0]["source_paths"],
        },
        {
            "study_id": "S1",
            "study_name": "external_bc_completion",
            "wave_status": "complete_contract_fluid_api_open",
            "primary_output": "external_bc_completion_matrix.csv",
            "claim_class": "setup-facing BC schema and handoff only",
            "next_gate": "TODO-FLUID-EXTERNAL-BC-DICT",
            "source_paths": external[0]["source_paths"],
        },
        {
            "study_id": "S2",
            "study_name": "split_heat_loss_evidence",
            "wave_status": "complete",
            "primary_output": "split_heat_completion_matrix.csv",
            "claim_class": "diagnostic heat-path evidence, no admission",
            "next_gate": "TODO-HEATLOSS-PHASE-3-WALL-TEST-SECTION-MODEL-SCORE",
            "source_paths": split_heat[0]["source_paths"],
        },
        {
            "study_id": "S3",
            "study_name": "pressure_source_envelope",
            "wave_status": "complete_diagnostic_release_gate",
            "primary_output": "pressure_source_envelope_release_gate.csv",
            "claim_class": "pressure residual attribution and non-admission",
            "next_gate": "same-QOI UQ/isolation/nonrecirc gates before any fit",
            "source_paths": pressure[0]["source_paths"],
        },
    ]


def next_gate_queue() -> list[dict[str, str]]:
    return [
        {
            "priority": "0",
            "gate": "TODO-FLUID-EXTERNAL-BC-DICT",
            "launch_now": "only_with_external_Fluid_ownership",
            "reason": "S1 contract and handoff are complete, but first-class Fluid/API source support remains open.",
            "forbidden": "no external Fluid edit without separate external board row and exact-file ownership",
        },
        {
            "priority": "1",
            "gate": "TODO-HEATLOSS-PHASE-3-WALL-TEST-SECTION-MODEL-SCORE",
            "launch_now": "yes_repo_local_after_claim",
            "reason": "Phase 0/1/2 heat-loss evidence is complete and can feed a narrow setup-only candidate score.",
            "forbidden": "no realized wallHeatFlux, CFD mdot, imposed CFD cooler duty, realized test-section heat, or validation temperatures at runtime",
        },
        {
            "priority": "2",
            "gate": "TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE",
            "launch_now": "after_or_in_parallel_with_phase3_if_scope_separate",
            "reason": "Upcomer/internal-Nu rows remain diagnostic until recirculation/exchange evidence gates pass.",
            "forbidden": "no ordinary upcomer Nu/fD/K fit from current recirculating rows",
        },
        {
            "priority": "3",
            "gate": "TODO-HEATLOSS-PHASE-5-FROZEN-SCORECARD-AND-THESIS-HANDOFF",
            "launch_now": "no_trigger_gated",
            "reason": "Final frozen scorecard remains blocked until a runtime-legal candidate is admitted.",
            "forbidden": "no holdout/external tuning and no final accuracy claim before freeze",
        },
    ]


def source_manifest() -> list[dict[str, str]]:
    paths = [
        ROADMAP,
        STARTER / "README.md",
        STARTER / "baseline_model_contract.csv",
        STARTER / "freeze_readiness_matrix.csv",
        PHASE1 / "README.md",
        PHASE1 / "external_bc_segment_role_audit.csv",
        PHASE1 / "fluid_handoff_contract.csv",
        PHASE2 / "README.md",
        PHASE2 / "summary.json",
        PHASE2 / "missing_field_queue.csv",
        PRESSURE_BASIS / "summary.json",
        PRESSURE_BASIS / "pressure_plane_basis_standardization.csv",
        PRESSURE_FREEZE / "README.md",
        PRESSURE_FREEZE / "canonical_pressure_corner_result.csv",
        FORWARD_MAP,
    ]
    return [
        {
            "source_path": rel(path),
            "exists": str(path.exists()).lower(),
            "source_role": "read_only_context",
        }
        for path in paths
    ]


def readme_text(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_2_split_heat_loss_evidence/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/README.md
tags: [forward-model, predictive-1d, first-wave, thesis-studies, residual-attribution]
related:
  - operational_notes/maps/forward-predictive-model.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
task: {TASK}
date: 2026-07-21
role: Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Predictive First Key Studies Wave

## Decision

The first predictive-model studies wave is complete as a consolidation and
release-gate package for S0 through S3:

- S0 baseline control surface is ready for thesis tables.
- S1 external-boundary dictionary contract is complete, while first-class Fluid
  source integration remains open under `TODO-FLUID-EXTERNAL-BC-DICT`.
- S2 split heat-loss evidence is complete and can feed Phase 3 wall/test-section
  candidate scoring.
- S3 pressure source-envelope release gate is complete as diagnostic residual
  attribution and non-admission; no component K or F6 coefficient is admitted.

This package does not score a new model, run Fluid/OpenFOAM, fit, select a
model, or admit a closure.

## Outputs

- `first_key_study_wave_status.csv`
- `baseline_control_surface.csv`
- `external_bc_completion_matrix.csv`
- `split_heat_completion_matrix.csv`
- `pressure_source_envelope_release_gate.csv`
- `next_gate_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Current Counts

- Completed study rows: `{summary["completed_study_rows"]}`.
- Open implementation gates: `{summary["open_implementation_gates"]}`.
- Component-K admitted rows: `{summary["component_k_admitted_rows"]}`.
- F6 admitted rows: `{summary["f6_admitted_rows"]}`.
- Runtime or split leakage failures: `{summary["runtime_or_split_leakage_failures"]}`.

## Next Action

The next repo-local scientific gate is
`TODO-HEATLOSS-PHASE-3-WALL-TEST-SECTION-MODEL-SCORE`. The external Fluid API
gate `TODO-FLUID-EXTERNAL-BC-DICT` should be claimed only with exact external
Fluid ownership.

## Guardrails

- No native CFD/OpenFOAM output mutation.
- No registry or admission mutation.
- No scheduler action or solver/postprocessing launch.
- No Fluid or external paper edit.
- No fitting, tuning, model selection, closure admission, final freeze, or
  final predictive accuracy claim.
"""


def build() -> dict[str, Any]:
    baseline = baseline_control_surface()
    external = external_bc_completion_matrix()
    split_heat = split_heat_completion_matrix()
    pressure = pressure_source_envelope_gate()
    wave = wave_status_table(baseline, external, split_heat, pressure)
    gates = next_gate_queue()
    sources = source_manifest()

    write_csv(OUT / "baseline_control_surface.csv", baseline)
    write_csv(OUT / "external_bc_completion_matrix.csv", external)
    write_csv(OUT / "split_heat_completion_matrix.csv", split_heat)
    write_csv(OUT / "pressure_source_envelope_release_gate.csv", pressure)
    write_csv(OUT / "first_key_study_wave_status.csv", wave)
    write_csv(OUT / "next_gate_queue.csv", gates)
    write_csv(OUT / "source_manifest.csv", sources)

    runtime_failures = sum(int(row["runtime_gate_failures"]) for row in baseline)
    component_k_rows = sum(int(row["component_k_admitted_rows"]) for row in pressure)
    f6_rows = sum(int(row["f6_admitted_rows"]) for row in pressure)
    summary = {
        "task": TASK,
        "date": "2026-07-21",
        "generated_at_utc": utc_now(),
        "completed_study_rows": len([row for row in wave if row["wave_status"].startswith("complete")]),
        "wave_rows": len(wave),
        "open_implementation_gates": len([row for row in gates if row["launch_now"] != "no_trigger_gated"]),
        "runtime_or_split_leakage_failures": runtime_failures,
        "component_k_admitted_rows": component_k_rows,
        "f6_admitted_rows": f6_rows,
        "final_freeze_exists": False,
        "model_scoring_or_admission": False,
        "fluid_edit": False,
        "native_output_mutation": False,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme_text(summary), encoding="utf-8")
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
