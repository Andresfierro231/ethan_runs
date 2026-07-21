#!/usr/bin/env python3
"""Build thesis diagnostic-evidence integration artifacts.

This builder consumes existing diagnostic packages only. It does not mutate
native CFD outputs, launch sampling, fit coefficients, choose model forms, or
change admission state.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-THESIS-DIAGNOSTIC-EVIDENCE-INTEGRATION-2026-07-21"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_diagnostic_evidence_integration"
)
OUT = ROOT / OUT_REL

S4 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid"
)
PREFLIGHT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_evidence_preflight"
)
TERMINAL = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_terminal_source_readiness"
)
PHASE2 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_2_split_heat_loss_evidence"
)
PHASE3 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_3_wall_test_section_model_score"
)
PHASE4 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"
)
PRESSURE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_pressure_corner_same_qoi_scientific_synthesis"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def source_join(paths: list[Path]) -> str:
    return ";".join(rel(path) for path in paths)


def first_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    raise ValueError(f"missing row where {key}={value}")


def build_claim_matrix(s4_summary: dict[str, Any]) -> list[dict[str, str]]:
    common_boundary = (
        "Diagnostic evidence may motivate architecture, attribution, and "
        "guardrails; it is not an admitted coefficient or final predictive score."
    )
    return [
        {
            "claim_id": "recirculation_guard",
            "evidence_theme": "RAF/RMF/SVF recirculation guard",
            "current_result": (
                f"S4 reviewed {s4_summary['reverse_flow_evidence_rows']} "
                "reverse-flow/exchange diagnostic rows and marks current upcomer "
                "and matched-plane evidence as recirculation-guard evidence."
            ),
            "allowed_thesis_claim": (
                "RAF/RMF/SVF diagnostics justify disabling ordinary single-stream "
                "closure labels in materially recirculating sections."
            ),
            "forbidden_claim": (
                "Do not claim an admitted exchange-cell coefficient, ordinary "
                "upcomer Nu/f_D/K, or final predictive score from these rows."
            ),
            "admission_status": "diagnostic_not_admitted",
            "target_chapters": "Ch5;Ch6;Ch7",
            "source_paths": source_join(
                [
                    S4 / "reverse_flow_onset_evidence_ledger.csv",
                    S4 / "throughflow_recirc_variable_contract.csv",
                ]
            ),
            "claim_boundary": common_boundary,
        },
        {
            "claim_id": "energy_residual_attribution",
            "evidence_theme": "energy residual attribution",
            "current_result": (
                "Phase 2 and upcomer preflight preserve residual rows as "
                "diagnostic attribution evidence with missing exchange/source fields."
            ),
            "allowed_thesis_claim": (
                "Energy residuals can identify missing heat-path, source, and "
                "exchange-state owners before fitting."
            ),
            "forbidden_claim": (
                "Do not absorb residuals into internal Nu, exchange coefficients, "
                "or realized wallHeatFlux runtime inputs."
            ),
            "admission_status": "diagnostic_not_admitted",
            "target_chapters": "Ch6;Ch7",
            "source_paths": source_join(
                [
                    PHASE2 / "energy_residual_owner_matrix.csv",
                    PREFLIGHT / "exchange_variable_availability.csv",
                ]
            ),
            "claim_boundary": common_boundary,
        },
        {
            "claim_id": "ordinary_upcomer_closure_exclusion",
            "evidence_theme": "ordinary upcomer Nu/f_D/K exclusion",
            "current_result": (
                f"S4 reviewed {s4_summary['ordinary_candidate_rows_reviewed']} "
                "ordinary single-stream candidates; admitted ordinary upcomer "
                f"Nu/f_D/K rows = {s4_summary['ordinary_upcomer_Nu_fD_K_admitted_rows']}."
            ),
            "allowed_thesis_claim": (
                "Current evidence supports exclusion of ordinary upcomer single-stream "
                "closure labels from fitted use."
            ),
            "forbidden_claim": (
                "Do not reopen ordinary internal Nu, friction, or K until recirculation, "
                "source/sign, and same-QOI UQ gates pass."
            ),
            "admission_status": "blocked_diagnostic_not_admitted",
            "target_chapters": "Ch5;Ch6;Ch7",
            "source_paths": source_join(
                [
                    S4 / "ordinary_closure_disable_table.csv",
                    PHASE4 / "phase4_decision_gate.csv",
                ]
            ),
            "claim_boundary": common_boundary,
        },
        {
            "claim_id": "pressure_residual_ownership",
            "evidence_theme": "pressure residual ownership",
            "current_result": (
                "Current corner/two-tap rows are section-effective diagnostic "
                "pressure evidence; same-QOI UQ and ordinary-flow gates fail."
            ),
            "allowed_thesis_claim": (
                "Pressure residuals should be owned by source-envelope, basis, "
                "straight/developing, component-isolation, and recirculation gates."
            ),
            "forbidden_claim": (
                "Do not claim negative loss, clipped K, component-K, F6 fit, "
                "or a global pressure multiplier from current corner rows."
            ),
            "admission_status": "diagnostic_not_admitted",
            "target_chapters": "Ch6;Ch7",
            "source_paths": source_join(
                [
                    PRESSURE / "attempt_outcome_matrix.csv",
                    PRESSURE / "blocker_analysis.csv",
                ]
            ),
            "claim_boundary": common_boundary,
        },
        {
            "claim_id": "thermal_residual_ownership",
            "evidence_theme": "thermal residual ownership",
            "current_result": (
                "Phase 2/3/4 split thermal residuals into heat-path owners while "
                "wall/test-section and upcomer exchange candidates remain blocked."
            ),
            "allowed_thesis_claim": (
                "Thermal residual ownership can be reported by heat-path lane and "
                "runtime-legality boundary."
            ),
            "forbidden_claim": (
                "Do not use realized CFD wallHeatFlux, test-section heat, CFD mdot, "
                "or unresolved residuals as predictive runtime inputs."
            ),
            "admission_status": "diagnostic_not_admitted",
            "target_chapters": "Ch6;Ch7",
            "source_paths": source_join(
                [
                    PHASE2 / "energy_residual_owner_matrix.csv",
                    PHASE3 / "phase3_release_gate.csv",
                    PHASE4 / "phase4_decision_gate.csv",
                ]
            ),
            "claim_boundary": common_boundary,
        },
    ]


def build_recirc_table() -> list[dict[str, str]]:
    rows = read_csv(S4 / "reverse_flow_onset_evidence_ledger.csv")
    out_rows: list[dict[str, str]] = []
    for row in rows:
        out_rows.append(
            {
                "evidence_id": row["evidence_id"],
                "case_id": row["case_id"],
                "feature_or_span": row["feature_or_span"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "secondary_flow_intensity": row["secondary_flow_intensity"],
                "classification": row["classification"],
                "admission_use": row["admission_use"],
                "scoreable_now": row["scoreable_now"],
                "thesis_use": "recirculation guard and missing-exchange-state attribution only",
                "source_paths": row["source_paths"],
            }
        )
    return out_rows


def build_ordinary_exclusion_table() -> list[dict[str, str]]:
    rows = read_csv(S4 / "ordinary_closure_disable_table.csv")
    out_rows: list[dict[str, str]] = []
    for row in rows:
        out_rows.append(
            {
                "branch_id": row["branch_id"],
                "candidate_rows_reviewed": row["candidate_rows_reviewed"],
                "recirculation_gate": row["recirculation_gate"],
                "source_envelope_gate": row["source_envelope_gate"],
                "sign_heat_balance_gate": row["sign_heat_balance_gate"],
                "same_qoi_uq_gate": row["same_qoi_uq_gate"],
                "ordinary_nu_fit_admitted_rows": row["ordinary_nu_fit_admitted_rows"],
                "ordinary_fD_fit_admitted_rows": row["ordinary_fD_fit_admitted_rows"],
                "ordinary_K_fit_admitted_rows": row["ordinary_K_fit_admitted_rows"],
                "ordinary_closure_allowed": row["ordinary_closure_allowed"],
                "admission_status": "blocked_diagnostic_not_admitted",
                "guard_reason": row["guard_reason"],
                "thesis_use": row["thesis_use"],
                "source_paths": row["source_paths"],
            }
        )
    return out_rows


def build_residual_ownership_matrix() -> list[dict[str, str]]:
    phase2_rows = read_csv(PHASE2 / "energy_residual_owner_matrix.csv")
    phase3_rows = read_csv(PHASE3 / "phase3_release_gate.csv")
    phase4_rows = read_csv(PHASE4 / "phase4_decision_gate.csv")
    pressure_attempts = read_csv(PRESSURE / "attempt_outcome_matrix.csv")
    pressure_blockers = read_csv(PRESSURE / "blocker_analysis.csv")

    phase2_upcomer_count = sum(
        1 for row in phase2_rows if "upcomer" in row.get("physical_segment", "")
    )
    phase2_rows_with_residual = sum(
        1 for row in phase2_rows if row.get("energy_residual_W", "") not in ("", "nan")
    )
    wall_gate = first_row(phase3_rows, "gate_id", "wall_candidate_score_gate")
    ts_gate = first_row(phase3_rows, "gate_id", "test_section_passive_loss_gate")
    exchange_gate = first_row(phase4_rows, "decision_id", "exchange_cell_admission")
    ordinary_gate = first_row(phase4_rows, "decision_id", "ordinary_internal_Nu_reopening")
    pressure_recirc = first_row(pressure_blockers, "blocker_id", "BLK-002")
    pressure_uq = first_row(pressure_blockers, "blocker_id", "BLK-005")
    pressure_diag = first_row(pressure_attempts, "attempt_id", "ATT-001")

    return [
        {
            "residual_family": "thermal_energy_residual",
            "scope": "bracketed and partially bracketed loop segments",
            "rows_or_cases": str(phase2_rows_with_residual),
            "current_status": "diagnostic_owner_matrix",
            "owner_or_interpretation": (
                "segment wall-flux minus physical-interface enthalpy change, "
                "with junction/upcomer lanes preserved separately"
            ),
            "allowed_thesis_use": "attribute missing heat-path and bracketing owners",
            "forbidden_use": "predictive runtime wallHeatFlux or internal-Nu absorption",
            "next_evidence_needed": "direct named-group extraction and accepted bracketing",
            "source_paths": rel(PHASE2 / "energy_residual_owner_matrix.csv"),
        },
        {
            "residual_family": "thermal_wall_test_section",
            "scope": "wall/test-section coupled candidates",
            "rows_or_cases": "8 wall candidates; 7 test-section candidate classes",
            "current_status": "fail_no_candidate_admitted",
            "owner_or_interpretation": f"{wall_gate['evidence']}; {ts_gate['evidence']}",
            "allowed_thesis_use": "negative result localizing thermal blocker",
            "forbidden_use": "admitted passive wall/test-section closure",
            "next_evidence_needed": "narrower setup candidate with runtime-legal inputs",
            "source_paths": source_join(
                [
                    PHASE3 / "phase3_release_gate.csv",
                    PHASE3 / "wall_test_section_candidate_gate_scorecard.csv",
                ]
            ),
        },
        {
            "residual_family": "upcomer_exchange_or_internal_Nu",
            "scope": "upcomer residual and ordinary single-stream reopening",
            "rows_or_cases": (
                f"{phase2_upcomer_count} upcomer residual rows; "
                f"{ordinary_gate['evidence']}"
            ),
            "current_status": "blocked_diagnostic_only",
            "owner_or_interpretation": exchange_gate["evidence"],
            "allowed_thesis_use": "recirculation/exchange-state guard and missing-field queue",
            "forbidden_use": "exchange-cell coefficient or ordinary internal Nu reopening",
            "next_evidence_needed": exchange_gate["next_action"],
            "source_paths": rel(PHASE4 / "phase4_decision_gate.csv"),
        },
        {
            "residual_family": "pressure_corner_residual",
            "scope": "current lower-right two-tap/corner rows",
            "rows_or_cases": pressure_recirc["affected_rows"],
            "current_status": "section_effective_diagnostic_not_admitted",
            "owner_or_interpretation": pressure_diag["analysis_why"],
            "allowed_thesis_use": "source-envelope, recirculation, and basis discipline",
            "forbidden_use": pressure_diag["admission_guardrail"],
            "next_evidence_needed": pressure_recirc["required_next_proof"],
            "source_paths": source_join(
                [
                    PRESSURE / "attempt_outcome_matrix.csv",
                    PRESSURE / "blocker_analysis.csv",
                ]
            ),
        },
        {
            "residual_family": "same_qoi_uncertainty_residual",
            "scope": "cross-family pressure and thermal candidate rows",
            "rows_or_cases": pressure_uq["affected_rows"],
            "current_status": "blocked_gap_inventory",
            "owner_or_interpretation": pressure_uq["analysis_why"],
            "allowed_thesis_use": "evidence queue and admission blocker",
            "forbidden_use": "coefficient admission from retained-time-only rows",
            "next_evidence_needed": pressure_uq["required_next_proof"],
            "source_paths": rel(PRESSURE / "blocker_analysis.csv"),
        },
    ]


def build_chapter_plan() -> list[dict[str, str]]:
    return [
        {
            "target_file": "reports/thesis_dossier/Chapters_and_sections/current/17_ch5_csem_fluid_walls_model.md",
            "target_section": "Recirculation Guard Interface",
            "inserted_or_updated_claim": "Diagnostic RAF/RMF/SVF and residual lanes are architecture guardrails, not admitted coefficients.",
            "claim_boundary": "No exchange-cell, ordinary upcomer Nu/f_D/K, or final score claim.",
            "supporting_tables": "diagnostic_claim_matrix.csv;recirculation_guard_evidence_table.csv;ordinary_closure_exclusion_table.csv",
        },
        {
            "target_file": "reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md",
            "target_section": "Current Release-Gate Status / Diagnostic Non-Admission Snapshot",
            "inserted_or_updated_claim": "S4 is complete as a positive diagnostic guard and negative admission result.",
            "claim_boundary": "Train, holdout, and external-test claims remain separate; no closure admission changes.",
            "supporting_tables": "diagnostic_claim_matrix.csv;ordinary_closure_exclusion_table.csv",
        },
        {
            "target_file": "reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md",
            "target_section": "Diagnostic Evidence Integration",
            "inserted_or_updated_claim": "Pressure and thermal residuals have named owners and forbidden absorption paths.",
            "claim_boundary": "No pressure multiplier, clipped K, wallHeatFlux runtime input, or final predictive score.",
            "supporting_tables": "diagnostic_claim_matrix.csv;residual_ownership_matrix.csv",
        },
        {
            "target_file": "reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md",
            "target_section": "Tables And Ledgers / Enrichment Insertions",
            "inserted_or_updated_claim": "Adds the integration tables and S4 source ledgers as thesis-ready non-admission tables.",
            "claim_boundary": "Tables must be captioned as diagnostic/non-admitted evidence.",
            "supporting_tables": "figure_table_ledger_update.csv",
        },
    ]


def build_figure_table_update() -> list[dict[str, str]]:
    return [
        {
            "artifact": rel(OUT / "diagnostic_claim_matrix.csv"),
            "target_chapter": "Chapter 6 or Chapter 7",
            "caption_or_use": "Diagnostic claim boundary matrix for recirculation, energy, pressure, and thermal residual evidence.",
            "required_caveat": "Every row is diagnostic or blocked; no admitted coefficient or final predictive score.",
        },
        {
            "artifact": rel(OUT / "recirculation_guard_evidence_table.csv"),
            "target_chapter": "Chapter 5 or Chapter 7",
            "caption_or_use": "RAF/RMF/SVF evidence used as a recirculation guard and missing-exchange-state queue.",
            "required_caveat": "Reverse-flow evidence disables ordinary labels but does not fit exchange cells.",
        },
        {
            "artifact": rel(OUT / "ordinary_closure_exclusion_table.csv"),
            "target_chapter": "Chapter 6",
            "caption_or_use": "Ordinary single-stream closure exclusion table for upcomer and adjacent recirculating branches.",
            "required_caveat": "Ordinary Nu/f_D/K admitted rows remain zero.",
        },
        {
            "artifact": rel(OUT / "residual_ownership_matrix.csv"),
            "target_chapter": "Chapter 7",
            "caption_or_use": "Pressure and thermal residual owner matrix with forbidden absorption paths.",
            "required_caveat": "Residual ownership is attribution, not runtime input authorization.",
        },
        {
            "artifact": rel(S4 / "ordinary_closure_disable_table.csv"),
            "target_chapter": "Chapter 6",
            "caption_or_use": "Source S4 table supporting ordinary upcomer closure exclusion.",
            "required_caveat": "Use as source evidence only; not a new fitted table.",
        },
        {
            "artifact": rel(S4 / "reverse_flow_onset_evidence_ledger.csv"),
            "target_chapter": "Chapter 7",
            "caption_or_use": "Source S4 reverse-flow/onset evidence ledger.",
            "required_caveat": "Caption as diagnostic recirculation evidence.",
        },
        {
            "artifact": rel(S4 / "throughflow_recirc_variable_contract.csv"),
            "target_chapter": "Chapter 5 or Chapter 8",
            "caption_or_use": "Future throughflow-plus-recirculation variable contract.",
            "required_caveat": "Variables are a missing-field contract, not current Fluid inputs.",
        },
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(S4 / 'README.md')}
  - {rel(PREFLIGHT / 'README.md')}
  - {rel(PHASE2 / 'README.md')}
  - {rel(PHASE3 / 'README.md')}
  - {rel(PHASE4 / 'README.md')}
  - {rel(PRESSURE / 'README.md')}
tags: [thesis, diagnostic-evidence, recirculation, residual-ownership, no-admission]
related:
  - .agent/status/2026-07-21_{TASK}.md
  - .agent/journal/2026-07-21/thesis-diagnostic-evidence-integration.md
task: {TASK}
date: 2026-07-21
role: Writer/Reviewer/Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis Diagnostic Evidence Integration

## Decision

This package integrates the existing diagnostic evidence that can strengthen
the thesis without waiting for new compute. It is a non-admission package:
the evidence supports guardrails, attribution, and next-study prioritization,
not fitted coefficients or final predictive accuracy.

## Results

- Diagnostic claim rows: `{summary['diagnostic_claim_rows']}`.
- S4 ordinary single-stream candidates reviewed: `{summary['ordinary_candidate_rows_reviewed']}`.
- Ordinary upcomer `Nu/f_D/K` admitted rows: `{summary['ordinary_upcomer_Nu_fD_K_admitted_rows']}`.
- Exchange-cell coefficient admitted rows: `{summary['exchange_cell_coefficient_admitted_rows']}`.
- Scoreable-now rows: `{summary['scoreable_now_rows']}`.
- Phase 4B ready: `{str(summary['phase4b_ready']).lower()}`.
- Phase 5 trigger: `{summary['phase5_trigger']}`.
- Final predictive score claimed: `{str(summary['final_predictive_score_claim']).lower()}`.

## Outputs

- `diagnostic_claim_matrix.csv`
- `recirculation_guard_evidence_table.csv`
- `ordinary_closure_exclusion_table.csv`
- `residual_ownership_matrix.csv`
- `chapter_insertion_plan.csv`
- `figure_table_ledger_update.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native solver outputs, registry/admission state, scheduler state, Fluid
source files, or external repositories were mutated. No sampler, harvest,
model fitting, model selection, closure admission, Phase 4B rescore, Phase 5
trigger, or final predictive-score claim was performed.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_source_manifest() -> None:
    sources = [
        (S4 / "summary.json", "S4 counts and non-admission state"),
        (S4 / "ordinary_closure_disable_table.csv", "ordinary closure exclusion source rows"),
        (S4 / "reverse_flow_onset_evidence_ledger.csv", "RAF/RMF/SVF guard source rows"),
        (S4 / "throughflow_recirc_variable_contract.csv", "future exchange-variable contract"),
        (PREFLIGHT / "exchange_variable_availability.csv", "upcomer exchange missing-field preflight"),
        (TERMINAL / "source_family_readiness.csv", "terminal/source readiness context"),
        (PHASE2 / "energy_residual_owner_matrix.csv", "energy residual owner matrix"),
        (PHASE3 / "phase3_release_gate.csv", "wall/test-section negative gate"),
        (PHASE4 / "phase4_decision_gate.csv", "upcomer exchange/internal-Nu decision gate"),
        (PRESSURE / "attempt_outcome_matrix.csv", "pressure diagnostic outcome matrix"),
        (PRESSURE / "blocker_analysis.csv", "pressure/same-QOI blocker analysis"),
    ]
    rows = [
        {
            "source_path": rel(path),
            "exists": str(path.exists()).lower(),
            "use_in_package": use,
            "mutation_status": "read_only",
        }
        for path, use in sources
    ]
    write_csv(
        OUT / "source_manifest.csv",
        rows,
        ["source_path", "exists", "use_in_package", "mutation_status"],
    )


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    s4_summary = read_json(S4 / "summary.json")
    phase4_rows = read_csv(PHASE4 / "phase4_decision_gate.csv")
    phase5_gate = first_row(phase4_rows, "decision_id", "phase5_release_gate")

    claim_rows = build_claim_matrix(s4_summary)
    recirc_rows = build_recirc_table()
    ordinary_rows = build_ordinary_exclusion_table()
    residual_rows = build_residual_ownership_matrix()
    chapter_rows = build_chapter_plan()
    figure_rows = build_figure_table_update()

    write_csv(
        OUT / "diagnostic_claim_matrix.csv",
        claim_rows,
        [
            "claim_id",
            "evidence_theme",
            "current_result",
            "allowed_thesis_claim",
            "forbidden_claim",
            "admission_status",
            "target_chapters",
            "source_paths",
            "claim_boundary",
        ],
    )
    write_csv(
        OUT / "recirculation_guard_evidence_table.csv",
        recirc_rows,
        [
            "evidence_id",
            "case_id",
            "feature_or_span",
            "reverse_area_fraction",
            "reverse_mass_fraction",
            "secondary_flow_intensity",
            "classification",
            "admission_use",
            "scoreable_now",
            "thesis_use",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "ordinary_closure_exclusion_table.csv",
        ordinary_rows,
        [
            "branch_id",
            "candidate_rows_reviewed",
            "recirculation_gate",
            "source_envelope_gate",
            "sign_heat_balance_gate",
            "same_qoi_uq_gate",
            "ordinary_nu_fit_admitted_rows",
            "ordinary_fD_fit_admitted_rows",
            "ordinary_K_fit_admitted_rows",
            "ordinary_closure_allowed",
            "admission_status",
            "guard_reason",
            "thesis_use",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "residual_ownership_matrix.csv",
        residual_rows,
        [
            "residual_family",
            "scope",
            "rows_or_cases",
            "current_status",
            "owner_or_interpretation",
            "allowed_thesis_use",
            "forbidden_use",
            "next_evidence_needed",
            "source_paths",
        ],
    )
    write_csv(
        OUT / "chapter_insertion_plan.csv",
        chapter_rows,
        [
            "target_file",
            "target_section",
            "inserted_or_updated_claim",
            "claim_boundary",
            "supporting_tables",
        ],
    )
    write_csv(
        OUT / "figure_table_ledger_update.csv",
        figure_rows,
        ["artifact", "target_chapter", "caption_or_use", "required_caveat"],
    )
    write_source_manifest()

    summary: dict[str, Any] = {
        "task": TASK,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "output_dir": rel(OUT),
        "diagnostic_claim_rows": len(claim_rows),
        "recirculation_guard_evidence_rows": len(recirc_rows),
        "ordinary_closure_exclusion_rows": len(ordinary_rows),
        "residual_ownership_rows": len(residual_rows),
        "ordinary_candidate_rows_reviewed": s4_summary["ordinary_candidate_rows_reviewed"],
        "ordinary_closure_admitted_rows": s4_summary["ordinary_closure_admitted_rows"],
        "ordinary_upcomer_Nu_fD_K_admitted_rows": s4_summary[
            "ordinary_upcomer_Nu_fD_K_admitted_rows"
        ],
        "exchange_cell_coefficient_admitted_rows": s4_summary[
            "exchange_cell_coefficient_admitted_rows"
        ],
        "scoreable_now_rows": s4_summary["scoreable_now_rows"],
        "phase4b_ready": False,
        "phase5_trigger": phase5_gate["decision_status"],
        "final_predictive_score_claim": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "admission_state_mutated": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "fit_or_model_selection_performed": False,
        "sampler_or_harvest_launched": False,
        "blocker_register_mutated": False,
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_readme(summary)
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
