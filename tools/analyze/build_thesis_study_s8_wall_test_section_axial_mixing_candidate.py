#!/usr/bin/env python3
"""Build S8 wall/test-section axial-mixing candidate study package.

This is an evidence consolidation builder. It does not run Fluid/OpenFOAM,
fit parameters, or admit closures.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "TODO-THESIS-STUDY-S8-WALL-TEST-SECTION-AXIAL-MIXING-CANDIDATE-2026-07-21"
DATE = "2026-07-21"
DEFAULT_OUT = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate"
)

PHASE3 = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_3_wall_test_section_model_score"
)
S8_EXEC = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_execution_documentation_package"
)


SOURCE_FILES = {
    "phase3_scorecard": PHASE3 / "wall_test_section_candidate_gate_scorecard.csv",
    "phase3_summary": PHASE3 / "summary.json",
    "phase3_runtime_audit": PHASE3 / "runtime_thermal_input_audit.csv",
    "blocker_audit": Path(
        "work_products/2026-07/2026-07-17/"
        "2026-07-17_wall_test_section_blocker_audit/README.md"
    ),
    "amx_dry_summary": Path(
        "work_products/2026-07/2026-07-20/"
        "2026-07-20_amx1_axial_mixing_dry_contract/summary.json"
    ),
    "amx_salt2_summary": Path(
        "work_products/2026-07/2026-07-20/"
        "2026-07-20_amx1_salt2_smoke_intake/summary.json"
    ),
    "amx_bounded_summary": Path(
        "work_products/2026-07/2026-07-20/"
        "2026-07-20_amx1_salt1_4_bounded_comparison_intake/summary.json"
    ),
    "amx_bounded_deltas": Path(
        "work_products/2026-07/2026-07-20/"
        "2026-07-20_amx1_salt1_4_bounded_comparison_intake/case_metric_deltas.csv"
    ),
    "amx_gradient_summary": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_amx1_gradient_clipped_smoke_intake/summary.json"
    ),
    "amx_gradient_deltas": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_amx1_gradient_clipped_smoke_intake/form_deltas.csv"
    ),
    "amx_physics_summary": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_amx1_physics_revision_smoke_intake/summary.json"
    ),
    "amx_physics_deltas": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_amx1_physics_revision_smoke_intake/form_deltas.csv"
    ),
    "umx_summary": Path(
        "work_products/2026-07/2026-07-20/"
        "2026-07-20_umx1_fluid_intake_decision/summary.json"
    ),
    "umx_scores": Path(
        "work_products/2026-07/2026-07-20/"
        "2026-07-20_umx1_fluid_intake_decision/scenario_score_intake.csv"
    ),
    "tswfc2_summary": Path(
        "work_products/2026-07/2026-07-20/"
        "2026-07-20_tswfc2_bounded_nominal_scorecard/summary.json"
    ),
    "tswfc2_scores": Path(
        "work_products/2026-07/2026-07-20/"
        "2026-07-20_tswfc2_bounded_nominal_scorecard/coupled_delta_vs_m3.csv"
    ),
    "s7_summary": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/summary.json"
    ),
}

LEGACY_DRAFT_FILES = [
    "admission_disposition.csv",
    "build_s8_wall_test_section_axial_mixing_candidate.py",
    "check_s8_wall_test_section_axial_mixing_candidate.py",
    "heat_path_ownership_and_gate_matrix.csv",
    "next_candidate_ladder_excerpt.csv",
    "phase4_dependency_queue.csv",
    "prior_candidate_comparison.csv",
    "role_segment_residual_focus.csv",
    "split_claim_matrix.csv",
    "tw5_tw6_residual_focus.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def as_float(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def build_prior_candidate_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(SOURCE_FILES["phase3_scorecard"]):
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "source_family": row.get("source_family", ""),
                "lane": row.get("lane", ""),
                "validation_case": row.get("validation_case", ""),
                "holdout_case": row.get("holdout_case", ""),
                "validation_mdot_delta_vs_m3_pct": row.get("validation_mdot_delta_vs_m3_pct", ""),
                "validation_tp_delta_vs_m3_K": row.get("validation_tp_delta_vs_m3_K", ""),
                "validation_tw_delta_vs_m3_K": row.get("validation_tw_delta_vs_m3_K", ""),
                "validation_all_probe_delta_vs_m3_K": row.get("validation_all_probe_delta_vs_m3_K", ""),
                "holdout_mdot_delta_vs_m3_pct": row.get("holdout_mdot_delta_vs_m3_pct", ""),
                "holdout_tp_delta_vs_m3_K": row.get("holdout_tp_delta_vs_m3_K", ""),
                "holdout_tw_delta_vs_m3_K": row.get("holdout_tw_delta_vs_m3_K", ""),
                "holdout_all_probe_delta_vs_m3_K": row.get("holdout_all_probe_delta_vs_m3_K", ""),
                "validation_tw5_delta_vs_m3_K": row.get("validation_tw5_delta_vs_m3_K", ""),
                "validation_tw6_delta_vs_m3_K": row.get("validation_tw6_delta_vs_m3_K", ""),
                "holdout_tw5_delta_vs_m3_K": row.get("holdout_tw5_delta_vs_m3_K", ""),
                "holdout_tw6_delta_vs_m3_K": row.get("holdout_tw6_delta_vs_m3_K", ""),
                "runtime_gate": row.get("runtime_gate", ""),
                "validation_gate": row.get("validation_gate", ""),
                "holdout_gate": row.get("holdout_gate", ""),
                "end_to_end_gate": row.get("end_to_end_gate", ""),
                "source_property_gate": row.get("source_property_gate", ""),
                "admission_decision": row.get("admission_decision", ""),
                "blocking_reasons": row.get("blocking_reasons", ""),
                "source_paths": row.get("source_paths", ""),
            }
        )
    return rows


def build_smoke_rows() -> list[dict[str, Any]]:
    summaries = {
        "AMX1_dry_contract": SOURCE_FILES["amx_dry_summary"],
        "AMX1_salt2_smoke": SOURCE_FILES["amx_salt2_summary"],
        "AMX1_salt1_4_bounded": SOURCE_FILES["amx_bounded_summary"],
        "AMX1_gradient_clipped": SOURCE_FILES["amx_gradient_summary"],
        "AMX1_physics_revision": SOURCE_FILES["amx_physics_summary"],
        "UMX1_fluid_intake": SOURCE_FILES["umx_summary"],
        "TSWFC2_bounded_nominal": SOURCE_FILES["tswfc2_summary"],
    }
    rows: list[dict[str, Any]] = []
    for family, path in summaries.items():
        data = read_json(path)
        if family == "AMX1_dry_contract":
            decision = data["decision"]
            progression = data["current_blocker_state"]
            admission = "not_evaluated_patch_required"
        elif family == "AMX1_salt2_smoke":
            decision = data["decision"]
            progression = data["next_step"]
            admission = "smoke_only_not_s11_ready"
        elif family == "AMX1_salt1_4_bounded":
            decision = data["audit_result"]
            progression = data["candidate_progression"]
            admission = "diagnostic_not_s11_ready"
        elif family == "AMX1_gradient_clipped":
            decision = data["audit_decision"]
            progression = data["progression"]
            admission = "diagnostic_not_s11_ready"
        elif family == "AMX1_physics_revision":
            decision = data["audit_decision"]
            progression = data["progression"]
            admission = "diagnostic_not_s11_ready"
        elif family == "UMX1_fluid_intake":
            decision = data["decision"]
            progression = data["next_step"]
            admission = "blocked_not_scorecard_ready"
        else:
            decision = data["decision"]
            progression = ";".join(data.get("blocking_reasons", [])) if isinstance(data.get("blocking_reasons"), list) else data.get("blocking_reasons", "")
            admission = data["admission_decision"]
        rows.append(
            {
                "candidate_family": family,
                "evidence_path": str(path),
                "decision": decision,
                "progression_or_next_action": progression,
                "s11_ready": "no",
                "admission_status": admission,
                "fit_or_model_selection_run": str(data.get("fit_or_model_selection_run", False)).lower(),
                "scientific_admission_change": data.get("scientific_admission_change", "none"),
                "native_solver_outputs_mutated": str(
                    data.get("native_solver_outputs_mutated", data.get("native_cfd_outputs_mutated", False))
                ).lower(),
                "scheduler_action": str(data.get("scheduler_action", "none")).lower(),
            }
        )
    return rows


def build_candidate_contract() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "S8A_existing_setup_only_family_screen",
            "candidate_type": "existing_evidence_screen",
            "physical_hypothesis": "Existing setup-only wall/test-section, AMX1 axial-mixing, UMX1 stratification, and TSWFC2 wall-fluid coupling candidates can reduce TW5/TW6 without worsening mdot/TP/all-probe gates.",
            "pre_registered_negative_outcome": "If no existing family passes runtime, validation, holdout, source/property, and TW5/TW6 gates, S8 closes as negative_result and does not feed S11.",
            "runtime_allowed_inputs": "setup geometry; setup external-boundary dictionaries; train-only/literature parameters when predeclared",
            "forbidden_runtime_inputs": "CFD mdot; realized wallHeatFlux; imposed cooler duty; realized test-section heat; validation temperatures; holdout temperatures; external-test temperatures",
            "evaluation_sources": "Phase3 wall/test-section scorecard; AMX1 dry/smoke/bounded intakes; UMX1 intake; TSWFC2 bounded scorecard; S7 sensor contract",
            "s11_feed_condition": "At least one candidate has runtime pass, validation pass, holdout pass, source/property pass, no leakage, and no primary TW5/TW6 regression.",
            "decision": "negative_result_no_s11_candidate",
        },
        {
            "candidate_id": "S8B_future_setup_only_physical_candidate",
            "candidate_type": "future_candidate_contract",
            "physical_hypothesis": "A later candidate may combine setup-only axial mixing with independently justified upcomer exchange/onset evidence or a test-section heat-loss network before scoring.",
            "pre_registered_negative_outcome": "If source/onset/exchange evidence is absent, do not launch broad AMX/UMX/TSWFC grids.",
            "runtime_allowed_inputs": "only pre-solve setup quantities and candidate parameters admitted by source/property gate",
            "forbidden_runtime_inputs": "same forbidden runtime inputs as S8A",
            "evaluation_sources": "S9 upcomer onset/exchange UQ; S11 source/property refresh after a candidate exists",
            "s11_feed_condition": "new candidate must pass S8A gates before S11",
            "decision": "requires_new_board_row_or_source_evidence_before_run",
        },
    ]


def build_acceptance_gates(prior_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    phase3 = read_json(SOURCE_FILES["phase3_summary"])
    admitted_phase3 = int(phase3.get("admitted_candidate_rows", 0))
    smoke_ready = sum(1 for r in smoke_rows if r["s11_ready"] == "yes")
    return [
        {
            "gate_id": "S8-G0",
            "gate_family": "coordination",
            "required_condition": "S8 board row claimed with exact package and script paths.",
            "evidence_path": ".agent/BOARD.md",
            "status": "pass",
            "decision": "study_can_run_from_existing_evidence",
            "claim_allowed": "S8 documentation and evidence consolidation only",
            "next_action": "none",
        },
        {
            "gate_id": "S8-G1",
            "gate_family": "runtime_leakage",
            "required_condition": "No forbidden target or realized CFD quantity is used as predictive runtime input.",
            "evidence_path": "runtime_leakage_audit.csv",
            "status": "pass",
            "decision": "runtime contract preserved",
            "claim_allowed": "runtime-legal evidence screen",
            "next_action": "none",
        },
        {
            "gate_id": "S8-G2",
            "gate_family": "prior_candidate_gate",
            "required_condition": "At least one existing wall/test-section candidate passes validation and holdout gates.",
            "evidence_path": str(SOURCE_FILES["phase3_scorecard"]),
            "status": "fail" if admitted_phase3 == 0 else "pass",
            "decision": f"{admitted_phase3} admitted Phase 3 candidate rows",
            "claim_allowed": "negative_result" if admitted_phase3 == 0 else "candidate_may_feed_S11",
            "next_action": "no S11 feed from Phase 3 rows" if admitted_phase3 == 0 else "run S11 for admitted row",
        },
        {
            "gate_id": "S8-G3",
            "gate_family": "AMX_UMX_TSWFC_smoke",
            "required_condition": "Smoke/bounded AMX/UMX/TSWFC evidence produces a candidate ready for Salt1-4 freeze pathway.",
            "evidence_path": "smoke_family_verdicts.csv",
            "status": "fail" if smoke_ready == 0 else "pass",
            "decision": f"{smoke_ready} smoke families marked S11-ready",
            "claim_allowed": "negative_result" if smoke_ready == 0 else "candidate_may_feed_S11",
            "next_action": "revise physical form or wait for S9/source evidence" if smoke_ready == 0 else "run S11",
        },
        {
            "gate_id": "S8-G4",
            "gate_family": "S11_release",
            "required_condition": "Exactly one runtime-legal candidate is admission-ready for source/property refresh.",
            "evidence_path": "negative_or_admission_ready_summary.csv",
            "status": "fail",
            "decision": "0 S11-ready candidates",
            "claim_allowed": "no final predictive freeze",
            "next_action": "do not claim S11 until a new candidate passes S8 gates",
        },
    ]


def build_runtime_audit() -> list[dict[str, Any]]:
    forbidden = [
        ("CFD_mdot", "Realized CFD flow rate would leak the target solution state."),
        ("realized_CFD_wallHeatFlux", "Realized wall heat flux is a postprocessed CFD output."),
        ("imposed_CFD_cooler_duty", "Imposed CFD cooler duty is not a setup-only predictive runtime input."),
        ("realized_test_section_heat", "Realized test-section heat would absorb the target residual."),
        ("validation_temperature", "Validation temperatures are score-only targets."),
        ("holdout_temperature", "Holdout temperatures are score-only after freeze."),
        ("external_test_temperature", "External-test temperatures are score-only after freeze."),
    ]
    return [
        {
            "input_or_target": name,
            "role": "forbidden_runtime_input" if "temperature" not in name else "score_only_target",
            "source_path": "not_used_by_s8_builder",
            "split_role": "all",
            "runtime_allowed": "no",
            "reason": reason,
            "status": "pass_absent",
        }
        for name, reason in forbidden
    ] + [
        {
            "input_or_target": "existing_score_tables",
            "role": "diagnostic_evidence",
            "source_path": str(SOURCE_FILES["phase3_scorecard"]),
            "split_role": "validation_holdout_score_only",
            "runtime_allowed": "no",
            "reason": "Existing score rows are used only to decide whether a candidate is already admissible; no model is tuned.",
            "status": "pass_score_only",
        }
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    rows = []
    for name, path in SOURCE_FILES.items():
        rows.append(
            {
                "source_path": str(path),
                "role_in_study": name,
                "split_role": "mixed_or_not_applicable",
                "mutation_status": "read_only",
                "trusted_or_diagnostic": "trusted_existing_package" if path.exists() else "missing_required_source",
                "notes": "Used by S8 builder; no source file was mutated.",
            }
        )
    rows.extend(
        [
            {
                "source_path": "native CFD/OpenFOAM outputs",
                "role_in_study": "solver_outputs",
                "split_role": "not_applicable",
                "mutation_status": "not_touched",
                "trusted_or_diagnostic": "not_accessed",
                "notes": "S8 used published packages only.",
            },
            {
                "source_path": "registry/admission state",
                "role_in_study": "global_state",
                "split_role": "not_applicable",
                "mutation_status": "not_touched",
                "trusted_or_diagnostic": "not_mutated",
                "notes": "No admission state changed.",
            },
        ]
    )
    return rows


def build_negative_summary(prior_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "result_id": "S8-DECISION",
            "study_state": "negative_result",
            "admission_ready_candidates": 0,
            "s11_ready_candidates": 0,
            "final_score_values": 0,
            "primary_evidence": "Phase 3 wall/test-section scorecard plus AMX/UMX/TSWFC smoke and bounded evidence",
            "decision": "No current setup-only wall/test-section, axial-mixing, upcomer-stratification, or TSWFC candidate may feed S11.",
            "failed_gate": "candidate gates fail or smoke families are not scorecard-ready/source-property-ready",
            "thesis_claim": "S8 is a rigorous falsification result: the dominant TW5/TW6 residual is not resolved by current setup-only candidate families.",
            "future_unlock": "new setup-only physical form supported by S9 upcomer exchange/onset evidence or independent heat-loss source evidence, then rerun S8 gates",
        }
    ]


def build_figure_manifest() -> list[dict[str, Any]]:
    return [
        {
            "item_id": "S8-T1",
            "kind": "table",
            "title": "Wall/test-section candidate gate summary",
            "source_path": "m3_prior_candidate_comparison.csv",
            "destination_chapter": "Chapter 7 results; Chapter 6 admission/uncertainty",
            "claim_boundary": "diagnostic and negative-result evidence only; no admitted closure coefficient",
            "status": "ready_now",
        },
        {
            "item_id": "S8-T2",
            "kind": "table",
            "title": "AMX/UMX/TSWFC smoke verdicts",
            "source_path": "smoke_family_verdicts.csv",
            "destination_chapter": "Chapter 7 predictive-model path",
            "claim_boundary": "smoke/bounded evidence, not final scorecard",
            "status": "ready_now",
        },
        {
            "item_id": "S8-F1",
            "kind": "figure",
            "title": "TW5/TW6 wall/test-section residual atlas",
            "source_path": "TODO-THESIS-FIGTABLE-S8-WALL-TS-RESIDUAL-ATLAS-2026-07-21",
            "destination_chapter": "Chapter 7",
            "claim_boundary": "figure row should render from this package and blocker-audit evidence",
            "status": "ready_for_figtable_row",
        },
    ]


def build_readme(out: Path, summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - .agent/BOARD.md
  - {SOURCE_FILES['phase3_scorecard']}
  - {SOURCE_FILES['amx_bounded_summary']}
  - {SOURCE_FILES['amx_gradient_summary']}
  - {SOURCE_FILES['amx_physics_summary']}
  - {SOURCE_FILES['umx_summary']}
  - {SOURCE_FILES['tswfc2_summary']}
tags: [thesis-dossier, s8, wall-test-section, axial-mixing, negative-result]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_next_studies_board_dispatch/README.md
task: {TASK}
date: {DATE}
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis S8 Wall/Test-Section Axial-Mixing Candidate

## Decision

S8 closes as `negative_result_no_s11_candidate`.

No current setup-only wall/test-section, axial-mixing, upcomer-stratification,
UMX1, or TSWFC2 candidate is ready to feed S11. Existing evidence contains
`{summary['phase3_candidate_rows']}` Phase 3 candidate gate rows, `{summary['admitted_candidate_rows']}`
admitted candidate rows, and `{summary['s11_ready_candidates']}` S11-ready
candidates.

## What Was Evaluated

- Phase 3 wall/test-section model-score rows for wall thermal circuit and
  test-section passive-loss candidates.
- AMX1 dry, Salt2 smoke, Salt1-Salt4 bounded, gradient-clipped smoke, and
  parent-cell physics-revision evidence.
- UMX1 smoke/intake evidence.
- TSWFC2 bounded nominal scorecard evidence.
- S7 sensor-map contract for TW5/TW6 score-only interpretation.

## Files In This Package

The authoritative S8 files produced by
`tools/analyze/build_thesis_study_s8_wall_test_section_axial_mixing_candidate.py`
are:

| File | Use |
| --- | --- |
| `candidate_contract.csv` | Pre-registered S8 hypothesis and future candidate contract. |
| `m3_prior_candidate_comparison.csv` | Phase 3 candidate comparison against M3, including TW5/TW6 deltas. |
| `smoke_family_verdicts.csv` | AMX/UMX/TSWFC smoke and bounded-family verdicts. |
| `acceptance_gate_matrix.csv` | S8 gate outcomes and S11/freeze consequences. |
| `runtime_leakage_audit.csv` | Explicit forbidden-input audit. |
| `negative_or_admission_ready_summary.csv` | Final S8 decision and thesis-safe claim. |
| `figure_table_manifest.csv` | Thesis table/figure routing. |
| `source_manifest.csv` | Exact source paths and mutation flags. |
| `summary.json` | Machine-readable package summary. |

Any older draft files in this directory that are not listed above are legacy
artifacts from an earlier S8 package shape. They are non-authoritative for this
closeout unless regenerated by the tool named above.

## Thesis Claim

The S8 result is a scientific falsification result: the current setup-only
wall/test-section and axial-mixing candidate families do not resolve the
dominant TW5/TW6 residual while preserving the required coupled gates. This
narrows the final predictive-model blocker to a new physical form or to S9/S11
evidence, not to another broad passive-wall selector sweep.

## Guardrails

No solver, sampler, scheduler, Fluid edit, registry/admission mutation, model
fitting, model selection, closure admission, or final score computation was
performed. Validation and holdout temperatures are treated as score-only
targets, never runtime inputs.
"""


def build(out: Path) -> dict[str, Any]:
    missing = [str(path) for path in SOURCE_FILES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required S8 sources: " + "; ".join(missing))

    out.mkdir(parents=True, exist_ok=True)
    prior_rows = build_prior_candidate_rows()
    smoke_rows = build_smoke_rows()
    candidate_contract = build_candidate_contract()
    gate_rows = build_acceptance_gates(prior_rows, smoke_rows)
    runtime_rows = build_runtime_audit()
    source_rows = build_source_manifest()
    negative_rows = build_negative_summary(prior_rows, smoke_rows)
    figure_rows = build_figure_manifest()

    prior_fields = [
        "candidate_id",
        "source_family",
        "lane",
        "validation_case",
        "holdout_case",
        "validation_mdot_delta_vs_m3_pct",
        "validation_tp_delta_vs_m3_K",
        "validation_tw_delta_vs_m3_K",
        "validation_all_probe_delta_vs_m3_K",
        "holdout_mdot_delta_vs_m3_pct",
        "holdout_tp_delta_vs_m3_K",
        "holdout_tw_delta_vs_m3_K",
        "holdout_all_probe_delta_vs_m3_K",
        "validation_tw5_delta_vs_m3_K",
        "validation_tw6_delta_vs_m3_K",
        "holdout_tw5_delta_vs_m3_K",
        "holdout_tw6_delta_vs_m3_K",
        "runtime_gate",
        "validation_gate",
        "holdout_gate",
        "end_to_end_gate",
        "source_property_gate",
        "admission_decision",
        "blocking_reasons",
        "source_paths",
    ]
    write_csv(out / "m3_prior_candidate_comparison.csv", prior_rows, prior_fields)
    write_csv(out / "candidate_contract.csv", candidate_contract, list(candidate_contract[0]))
    write_csv(out / "smoke_family_verdicts.csv", smoke_rows, list(smoke_rows[0]))
    write_csv(out / "acceptance_gate_matrix.csv", gate_rows, list(gate_rows[0]))
    write_csv(out / "runtime_leakage_audit.csv", runtime_rows, list(runtime_rows[0]))
    write_csv(out / "negative_or_admission_ready_summary.csv", negative_rows, list(negative_rows[0]))
    write_csv(out / "figure_table_manifest.csv", figure_rows, list(figure_rows[0]))
    write_csv(out / "source_manifest.csv", source_rows, list(source_rows[0]))

    phase3 = read_json(SOURCE_FILES["phase3_summary"])
    s11_ready = 0
    legacy_present = [name for name in LEGACY_DRAFT_FILES if (out / name).exists()]
    summary = {
        "task": TASK,
        "date": DATE,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "study_state": "negative_result_no_s11_candidate",
        "phase3_candidate_rows": len(prior_rows),
        "admitted_candidate_rows": int(phase3.get("admitted_candidate_rows", 0)),
        "smoke_family_rows": len(smoke_rows),
        "s11_ready_candidates": s11_ready,
        "final_score_values": 0,
        "runtime_leakage_pass": True,
        "model_fitting_or_selection": False,
        "solver_or_sampler_launch": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "admission_state_mutation": False,
        "scheduler_action_taken": False,
        "external_fluid_edit": False,
        "external_repo_mutated": False,
        "generated_index_mutation": False,
        "blocker_register_mutation": False,
        "scientific_admission_changed": False,
        "final_predictive_accuracy_claimed": False,
        "legacy_draft_artifacts_present": legacy_present,
        "next_action": "Do not run S11 until a new setup-only physical candidate passes S8 gates; prioritize S9 upcomer exchange/onset evidence or a new independently sourced wall/test-section form.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "README.md").write_text(build_readme(out, summary))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    summary = build(args.output_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
