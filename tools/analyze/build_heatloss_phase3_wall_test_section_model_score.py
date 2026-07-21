#!/usr/bin/env python3
"""Build Phase 3 wall/test-section model-score gate artifacts.

This builder aggregates existing Phase 1/2 evidence and prior wall/test-section
candidate scorecards. It does not launch Fluid/OpenFOAM, fit coefficients,
mutate native outputs, or change admission state.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-HEATLOSS-PHASE-3-WALL-TEST-SECTION-MODEL-SCORE"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_3_wall_test_section_model_score"
)
OUT = ROOT / OUT_REL

PHASE1 = (
    ROOT
    / "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_1_external_bc_radiation_integration"
)
PHASE2 = (
    ROOT
    / "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_2_split_heat_loss_evidence"
)
WALL_STUDY = (
    ROOT
    / "work_products/2026-07/2026-07-17/"
    "2026-07-17_wall_thermal_circuit_study"
)
TEST_SECTION_REPAIR = (
    ROOT
    / "work_products/2026-07/2026-07-17/"
    "2026-07-17_test_section_passive_loss_admission_repair"
)
SEGMENT_THERMAL = (
    ROOT
    / "work_products/2026-07/2026-07-17/"
    "2026-07-17_predict_segment_thermal_models"
)
BOUNDARY_ADMISSION = (
    ROOT
    / "work_products/2026-07/2026-07-16/"
    "2026-07-16_predictive_boundary_submodel_admission"
)
SOURCE_PROPERTY = (
    ROOT
    / "work_products/2026-07/2026-07-18/"
    "2026-07-18_source_property_label_enforcement"
)

PHASE1_RUNTIME = PHASE1 / "runtime_mode_matrix.csv"
PHASE2_HEAT_PATHS = PHASE2 / "heat_path_evidence_matrix.csv"
PHASE2_RESIDUALS = PHASE2 / "energy_residual_owner_matrix.csv"
PHASE2_MISSING = PHASE2 / "missing_field_queue.csv"
WALL_ADMISSION = WALL_STUDY / "candidate_admission_review.csv"
WALL_DELTAS = WALL_STUDY / "coupled_delta_vs_m3.csv"
WALL_PROBES = WALL_STUDY / "probe_delta_vs_m3.csv"
WALL_RUNTIME = WALL_STUDY / "runtime_input_audit.csv"
TEST_SECTION_CLASSES = TEST_SECTION_REPAIR / "test_section_candidate_class_admission.csv"
TEST_SECTION_SETUP = (
    ROOT
    / "work_products/2026-07/2026-07-16/"
    "2026-07-16_predictive_test_section_heat_loss_model/setup_candidate_summary.csv"
)
SEGMENT_SLOTS = SEGMENT_THERMAL / "thermal_model_slot_admission.csv"
BOUNDARY_WALL_TS = BOUNDARY_ADMISSION / "wall_test_section_scorecard.csv"
SOURCE_PROPERTY_SUMMARY = SOURCE_PROPERTY / "summary.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    if not path.is_absolute():
        return str(path)
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def row_for(rows: list[dict[str, str]], **criteria: str) -> dict[str, str] | None:
    for row in rows:
        if all(row.get(key) == value for key, value in criteria.items()):
            return row
    return None


def probe_delta(
    probes: list[dict[str, str]],
    candidate_id: str,
    split_role: str,
    sensor: str,
) -> str:
    row = row_for(probes, candidate_id=candidate_id, split_role=split_role, sensor=sensor)
    if row is None:
        return ""
    return row.get("abs_error_delta_vs_m3_K", "")


def aggregate_wall_candidates(
    admission_rows: list[dict[str, str]],
    delta_rows: list[dict[str, str]],
    probe_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for admission in admission_rows:
        candidate_id = admission["candidate_id"]
        validation = row_for(delta_rows, candidate_id=candidate_id, split_role="validation") or {}
        holdout = row_for(delta_rows, candidate_id=candidate_id, split_role="holdout") or {}
        blocking = admission["blocking_reasons"]
        if "phase2_split_targets_diagnostic_only" not in blocking:
            blocking = f"{blocking};phase2_split_targets_diagnostic_only"
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_family": "wall_thermal_circuit_study",
                "lane": validation.get("lane") or holdout.get("lane", ""),
                "runtime_gate": admission["runtime_gate"],
                "validation_gate": admission["validation_coupled_gate"],
                "holdout_gate": admission["holdout_coupled_gate"],
                "end_to_end_gate": "fail",
                "validation_case": validation.get("case_id", ""),
                "holdout_case": holdout.get("case_id", ""),
                "validation_mdot_delta_vs_m3_pct": validation.get("mdot_delta_vs_m3_pct", ""),
                "validation_tp_delta_vs_m3_K": validation.get("tp_delta_vs_m3_K", ""),
                "validation_tw_delta_vs_m3_K": validation.get("tw_delta_vs_m3_K", ""),
                "validation_all_probe_delta_vs_m3_K": validation.get("all_probe_delta_vs_m3_K", ""),
                "holdout_mdot_delta_vs_m3_pct": holdout.get("mdot_delta_vs_m3_pct", ""),
                "holdout_tp_delta_vs_m3_K": holdout.get("tp_delta_vs_m3_K", ""),
                "holdout_tw_delta_vs_m3_K": holdout.get("tw_delta_vs_m3_K", ""),
                "holdout_all_probe_delta_vs_m3_K": holdout.get("all_probe_delta_vs_m3_K", ""),
                "validation_tw5_delta_vs_m3_K": probe_delta(probe_rows, candidate_id, "validation", "TW5"),
                "validation_tw6_delta_vs_m3_K": probe_delta(probe_rows, candidate_id, "validation", "TW6"),
                "holdout_tw5_delta_vs_m3_K": probe_delta(probe_rows, candidate_id, "holdout", "TW5"),
                "holdout_tw6_delta_vs_m3_K": probe_delta(probe_rows, candidate_id, "holdout", "TW6"),
                "phase2_evidence_gate": "fail_direct_target_gate_split_rows_are_diagnostic",
                "source_property_gate": "blocked_for_fit_or_admission_per_source_property_enforcement",
                "score_decision": "score_existing_rows_only",
                "admission_decision": "not_admitted",
                "blocking_reasons": blocking,
                "source_paths": f"{rel(WALL_ADMISSION)};{rel(WALL_DELTAS)};{rel(WALL_PROBES)}",
            }
        )
    return rows


def aggregate_test_section_classes(
    class_rows: list[dict[str, str]],
    setup_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    setup_by_candidate = by_key(setup_rows, "candidate_id")
    rows: list[dict[str, str]] = []
    for candidate in class_rows:
        setup = setup_by_candidate.get(candidate["source_candidate"], {})
        reason = candidate["reason"]
        if "phase2_split_targets_diagnostic_only" not in reason:
            reason = f"{reason}; phase2_split_targets_diagnostic_only"
        rows.append(
            {
                "candidate_id": candidate["candidate_class"],
                "source_family": "test_section_passive_loss_repair",
                "lane": "test_section_passive_loss",
                "runtime_gate": candidate["runtime_gate"],
                "validation_gate": candidate["validation_qoi_gate"],
                "holdout_gate": candidate["holdout_qoi_gate"],
                "end_to_end_gate": candidate["end_to_end_gate"],
                "validation_case": "salt_3",
                "holdout_case": "salt_4",
                "validation_mdot_delta_vs_m3_pct": "",
                "validation_tp_delta_vs_m3_K": "",
                "validation_tw_delta_vs_m3_K": "",
                "validation_all_probe_delta_vs_m3_K": "",
                "holdout_mdot_delta_vs_m3_pct": "",
                "holdout_tp_delta_vs_m3_K": "",
                "holdout_tw_delta_vs_m3_K": "",
                "holdout_all_probe_delta_vs_m3_K": "",
                "validation_tw5_delta_vs_m3_K": "",
                "validation_tw6_delta_vs_m3_K": "",
                "holdout_tw5_delta_vs_m3_K": "",
                "holdout_tw6_delta_vs_m3_K": "",
                "validation_q_loss_abs_error_W": setup.get("validation_abs_error_W", ""),
                "validation_q_loss_abs_error_pct": setup.get("validation_abs_error_pct", ""),
                "holdout_q_loss_abs_error_W": setup.get("holdout_abs_error_W", ""),
                "holdout_q_loss_abs_error_pct": setup.get("holdout_abs_error_pct", ""),
                "phase2_evidence_gate": "fail_direct_target_gate_test_section_wallHeatFlux_is_diagnostic",
                "source_property_gate": "blocked_for_fit_or_admission_per_source_property_enforcement",
                "score_decision": candidate["score_allowed_now"],
                "admission_decision": "not_admitted",
                "blocking_reasons": reason,
                "source_paths": f"{rel(TEST_SECTION_CLASSES)};{rel(TEST_SECTION_SETUP)}",
            }
        )
    return rows


def heat_path_target_readiness(heat_rows: list[dict[str, str]], missing_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    missing_ids = {row["missing_field_id"]: row["current_status"] for row in missing_rows}
    target_rows = []
    for row in heat_rows:
        if row["patch_group"] not in {"ambient_wall", "test_section", "junction_other", "heater", "cooler"}:
            continue
        target_rows.append(
            {
                "case_id": row["case_id"],
                "span": row["span"],
                "patch_group": row["patch_group"],
                "heat_path": row["heat_path"],
                "wallHeatFlux_diagnostic_W": row["wallHeatFlux_diagnostic_W"],
                "external_convection_status": row["external_convection_status"],
                "wall_layer_contact_status": row["wall_layer_contact_status"],
                "radiation_qr_presence_status": row["radiation_qr_presence_status"],
                "storage_status": row["storage_status"],
                "phase3_target_status": "diagnostic_or_setup_only_not_direct_fit_target",
                "missing_qr_status": missing_ids.get("qr_separate_radiation_output", ""),
                "missing_storage_status": missing_ids.get(
                    "solid_storage_or_wall_energy_time_derivative", ""
                ),
                "runtime_legality": row["runtime_legality"],
                "source_paths": row["source_paths"],
            }
        )
    return target_rows


def release_gate_rows(candidate_rows: list[dict[str, str]], residual_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    admitted = [row for row in candidate_rows if row["admission_decision"] == "admitted"]
    wall_candidates = [row for row in candidate_rows if row["source_family"] == "wall_thermal_circuit_study"]
    ts_candidates = [row for row in candidate_rows if row["source_family"] == "test_section_passive_loss_repair"]
    phase4_rows = [row for row in residual_rows if row["next_owner"] == "TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE"]
    return [
        {
            "gate_id": "phase2_target_readiness",
            "status": "blocked_for_direct_fit_targets",
            "evidence": "split junction/stub and test-section wallHeatFlux rows are diagnostic/scoring evidence only",
            "next_action": "direct named-group extraction or accepted bracketing before treating split heat as a target",
            "source_paths": rel(PHASE2_HEAT_PATHS),
        },
        {
            "gate_id": "wall_candidate_score_gate",
            "status": "fail",
            "evidence": f"{len(wall_candidates)} wall/test-section coupled candidates fail validation and holdout gates vs M3",
            "next_action": "do not promote a wall/test-section candidate; use failure localization to design narrower setup candidate",
            "source_paths": f"{rel(WALL_ADMISSION)};{rel(WALL_DELTAS)}",
        },
        {
            "gate_id": "test_section_passive_loss_gate",
            "status": "fail",
            "evidence": f"{len(ts_candidates)} test-section candidate classes remain blocked or diagnostic",
            "next_action": "do not use realized test-section heat or legacy 37 W as passive loss",
            "source_paths": rel(TEST_SECTION_CLASSES),
        },
        {
            "gate_id": "runtime_input_gate",
            "status": "pass_guardrail",
            "evidence": "realized wallHeatFlux, CFD mdot, imposed CFD cooler duty, realized test-section heat, and validation temperatures remain forbidden runtime inputs",
            "next_action": "only setup geometry/material/external-BC fields may be runtime inputs",
            "source_paths": f"{rel(PHASE1_RUNTIME)};{rel(WALL_RUNTIME)}",
        },
        {
            "gate_id": "phase4_dependency_gate",
            "status": "handoff_required",
            "evidence": f"{len(phase4_rows)} upcomer residual rows route to exchange/internal-Nu gate",
            "next_action": "claim TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE before reopening Nu",
            "source_paths": rel(PHASE2_RESIDUALS),
        },
        {
            "gate_id": "phase3_admission_gate",
            "status": "fail_no_candidate_admitted",
            "evidence": f"{len(admitted)} candidates admitted",
            "next_action": "publish negative Phase 3 result and proceed to Phase 4 residual attribution",
            "source_paths": rel(OUT / "wall_test_section_candidate_gate_scorecard.csv"),
        },
    ]


def runtime_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "audit_id": "predictive_runtime_forbidden_fields",
            "status": "pass_guardrail",
            "forbidden_runtime_inputs": "realized CFD wallHeatFlux;CFD mdot;imposed CFD cooler duty;realized test-section heat;validation temperatures",
            "policy": "forbidden predictive fields are blocked; Phase 3 aggregates existing scores only",
            "source_paths": f"{rel(PHASE1_RUNTIME)};{rel(WALL_RUNTIME)}",
        },
        {
            "audit_id": "no_new_execution",
            "status": "pass",
            "forbidden_runtime_inputs": "Fluid solve;OpenFOAM solve;postprocessing launch;scheduler action",
            "policy": "This package reads existing candidate scorecards and does not launch new work",
            "source_paths": rel(WALL_STUDY / "summary.json"),
        },
        {
            "audit_id": "qr_and_storage_absence",
            "status": "pass_recorded_absent",
            "forbidden_runtime_inputs": "qr inferred from emissivity;storage inferred from residual",
            "policy": "Separate qr and solid storage remain absent in Phase 2 and are not inferred",
            "source_paths": f"{rel(PHASE2_MISSING)};{rel(PHASE2 / 'runtime_legality_audit.csv')}",
        },
        {
            "audit_id": "admission_state",
            "status": "pass_no_mutation",
            "forbidden_runtime_inputs": "registry/admission mutation;blocker-register mutation",
            "policy": "All decisions are package-local gate decisions; no admission state changes",
            "source_paths": rel(OUT / "phase3_release_gate.csv"),
        },
    ]


def phase4_handoff_rows(residual_rows: list[dict[str, str]], release_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    handoff = []
    for row in residual_rows:
        if row["next_owner"] != "TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE":
            continue
        handoff.append(
            {
                "handoff_id": f"{row['case_id']}_{row['physical_segment']}",
                "next_task": row["next_owner"],
                "reason": "upcomer residual is diagnostic under high recirculation and cannot be assigned to ordinary internal Nu yet",
                "required_fields": "reverse_area_fraction;reverse_mass_fraction;secondary_flow_intensity;wall_core_delta_T;energy_residual;pressure_residual;same_QOI_UQ",
                "phase3_decision": "handoff_required",
                "source_paths": row["source_paths"],
            }
        )
    handoff.append(
        {
            "handoff_id": "phase3_negative_wall_test_section_release",
            "next_task": "TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE",
            "reason": "no wall/test-section candidate passed Phase 3, so remaining residual attribution must separate exchange/recirculation before Nu",
            "required_fields": "exchange-cell readiness and ordinary single-stream reopening table",
            "phase3_decision": next(row["status"] for row in release_rows if row["gate_id"] == "phase3_admission_gate"),
            "source_paths": rel(OUT / "phase3_release_gate.csv"),
        }
    )
    return handoff


def source_manifest_rows() -> list[dict[str, str]]:
    sources = [
        (PHASE1_RUNTIME, "Read runtime-mode guardrails for predictive/replay semantics."),
        (PHASE2_HEAT_PATHS, "Read split heat-path evidence and diagnostic target status."),
        (PHASE2_RESIDUALS, "Read residual owner routing, especially upcomer Phase 4 handoff."),
        (PHASE2_MISSING, "Read explicit qr/storage missing-field state."),
        (WALL_ADMISSION, "Read wall-circuit admission decisions."),
        (WALL_DELTAS, "Read mdot/TP/TW/all-probe deltas versus M3."),
        (WALL_PROBES, "Read TW5/TW6 and probe-level failure localization."),
        (WALL_RUNTIME, "Read prior wall-circuit runtime input audit."),
        (TEST_SECTION_CLASSES, "Read test-section passive-loss class admission results."),
        (TEST_SECTION_SETUP, "Read setup-only heat-loss candidate q-loss scores."),
        (SEGMENT_SLOTS, "Read segment thermal slot admission status."),
        (BOUNDARY_WALL_TS, "Read boundary submodel wall/test-section status."),
        (SOURCE_PROPERTY_SUMMARY, "Read source/property enforcement summary."),
    ]
    return [
        {
            "source_path": rel(path),
            "use": use,
            "mutation_status": "read_only",
        }
        for path, use in sources
    ]


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(PHASE2 / "README.md")}
  - {rel(WALL_STUDY / "README.md")}
  - {rel(TEST_SECTION_REPAIR / "README.md")}
  - {rel(SEGMENT_THERMAL / "README.md")}
tags: [thermal-modeling, heat-loss, wall-test-section, score-gate, fluid-walls]
related:
  - .agent/status/2026-07-21_TODO-HEATLOSS-PHASE-3-WALL-TEST-SECTION-MODEL-SCORE.md
  - .agent/journal/2026-07-21/heatloss-phase-3-wall-test-section-model-score.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_2_split_heat_loss_evidence/README.md
task: {TASK}
date: 2026-07-21
role: Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Phase 3 Wall/Test-Section Model-Score Gate

## Decision

Phase 3 is a negative score gate from existing artifacts. No wall/test-section
candidate is admitted or promoted. The prior coupled candidates and
test-section passive-loss classes fail validation/holdout, runtime, or
direct-target gates, and Phase 2 confirms the split heat evidence remains
diagnostic rather than a direct fit target.

## Results

- Candidate gate rows: `{summary["candidate_gate_rows"]}`.
- Wall-circuit candidate rows: `{summary["wall_candidate_rows"]}`.
- Test-section candidate class rows: `{summary["test_section_candidate_rows"]}`.
- Admitted candidate rows: `{summary["admitted_candidate_rows"]}`.
- Release gate status: `{summary["phase3_release_status"]}`.
- Phase 4 handoff rows: `{summary["phase4_handoff_rows"]}`.

## Outputs

- `wall_test_section_candidate_gate_scorecard.csv`
- `heat_path_target_readiness.csv`
- `phase3_release_gate.csv`
- `runtime_thermal_input_audit.csv`
- `phase4_handoff_queue.csv`
- `source_manifest.csv`
- `summary.json`
- `README.md`

## Guardrails

- Realized CFD `wallHeatFlux`, CFD `mdot`, imposed CFD cooler duty, realized
  test-section heat, and validation temperatures remain forbidden predictive
  runtime inputs.
- Separate `qr` and solid-storage fields remain absent and are not inferred.
- No Fluid/OpenFOAM execution, fitting, model selection, registry/admission
  mutation, blocker-register mutation, or generated-index refresh occurred.

## Next Action

Claim `TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE` before
reopening any internal-`Nu` row. The shortest useful follow-on is an exchange
readiness table that separates upcomer/test-section recirculation residuals from
ordinary single-stream candidates.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    wall_candidates = aggregate_wall_candidates(
        read_csv(WALL_ADMISSION),
        read_csv(WALL_DELTAS),
        read_csv(WALL_PROBES),
    )
    test_section_candidates = aggregate_test_section_classes(
        read_csv(TEST_SECTION_CLASSES),
        read_csv(TEST_SECTION_SETUP),
    )
    candidate_rows = wall_candidates + test_section_candidates
    heat_targets = heat_path_target_readiness(read_csv(PHASE2_HEAT_PATHS), read_csv(PHASE2_MISSING))
    residuals = read_csv(PHASE2_RESIDUALS)
    release_rows = release_gate_rows(candidate_rows, residuals)
    runtime_rows = runtime_audit_rows()
    handoff_rows = phase4_handoff_rows(residuals, release_rows)
    manifest_rows = source_manifest_rows()
    source_property_summary = read_json(SOURCE_PROPERTY_SUMMARY)

    write_csv(OUT / "wall_test_section_candidate_gate_scorecard.csv", candidate_rows)
    write_csv(OUT / "heat_path_target_readiness.csv", heat_targets)
    write_csv(OUT / "phase3_release_gate.csv", release_rows)
    write_csv(OUT / "runtime_thermal_input_audit.csv", runtime_rows)
    write_csv(OUT / "phase4_handoff_queue.csv", handoff_rows)
    write_csv(OUT / "source_manifest.csv", manifest_rows)

    admitted_rows = [row for row in candidate_rows if row["admission_decision"] == "admitted"]
    failed_release = [row for row in release_rows if row["status"].startswith("fail")]
    summary: dict[str, Any] = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "candidate_gate_rows": len(candidate_rows),
        "wall_candidate_rows": len(wall_candidates),
        "test_section_candidate_rows": len(test_section_candidates),
        "heat_path_target_rows": len(heat_targets),
        "release_gate_rows": len(release_rows),
        "release_gate_fail_rows": len(failed_release),
        "phase3_release_status": "negative_result_no_candidate_admitted",
        "admitted_candidate_rows": len(admitted_rows),
        "phase4_handoff_rows": len(handoff_rows),
        "source_property_fit_or_admission_allowed_rows": source_property_summary[
            "enforced_fit_or_admission_allowed_rows"
        ],
        "qr_inferred": False,
        "storage_inferred": False,
        "fluid_or_openfoam_execution": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
        "model_fitting_or_selection": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


if __name__ == "__main__":
    build()
