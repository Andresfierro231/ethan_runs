#!/usr/bin/env python3
"""Build the five best thesis-support analysis package from existing evidence.

This is a read-only coordinator reducer. It consumes completed packages and
current gate summaries, then emits thesis-facing priority and readiness tables.
It does not launch solvers, samplers, harvests, UQ, fitting, admission, or
freeze work.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "TODO-FIVE-BEST-THESIS-SUPPORT-ANALYSES-2026-07-22"
OUT_DIR = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_five_best_thesis_support_analyses"
)

SOURCES = {
    "four_study_gate": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_four_study_thesis_support_gate"
    ),
    "s13_limited_evidence": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis"
    ),
    "s13_source_side_gate": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate"
    ),
    "s13_exact_qwall": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"
    ),
    "reduced_dof_transfer": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_fluid_reduced_dof_bias_transfer_screen"
    ),
    "passive_physical": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_passive_h2_cand001_physical_basis"
    ),
    "passive_source": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment"
    ),
    "source_residual_decomp": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_fluid_setup_known_heater_source_train_residual_decomp"
    ),
    "cand001_timeout": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_pressure_f6_cand001_timeout_disposition"
    ),
    "hybrid_pressure": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_hybrid_pressure_no_fit_performance_bakeoff"
    ),
    "f6_same_qoi": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_f6_same_qoi_uq_and_admission_gate"
    ),
    "sensor_map": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_sensor_map_contract"
    ),
    "negative_results": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_thesis_negative_results_scientific_contribution_section"
    ),
    "predictive_path_status": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_thesis_figtable_predictive_path_status_set"
    ),
}


def load_json(source_key: str) -> dict[str, Any]:
    path = ROOT / SOURCES[source_key] / "summary.json"
    with path.open() as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def source_manifest_rows() -> list[dict[str, Any]]:
    rows = []
    for key, path in SOURCES.items():
        rel_summary = path / "summary.json"
        rows.append(
            {
                "source_key": key,
                "path": str(rel_summary),
                "exists": (ROOT / rel_summary).exists(),
                "mutation_status": "read_only",
            }
        )
    return rows


def build() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    four = load_json("four_study_gate")
    s13_limited = load_json("s13_limited_evidence")
    s13_source = load_json("s13_source_side_gate")
    s13_exact = load_json("s13_exact_qwall")
    reduced = load_json("reduced_dof_transfer")
    passive_physical = load_json("passive_physical")
    passive_source = load_json("passive_source")
    source_decomp = load_json("source_residual_decomp")
    cand001 = load_json("cand001_timeout")
    hybrid = load_json("hybrid_pressure")
    f6 = load_json("f6_same_qoi")
    sensor = load_json("sensor_map")
    negative = load_json("negative_results")
    predictive = load_json("predictive_path_status")

    priority_rows: list[dict[str, Any]] = [
        {
            "rank": 1,
            "analysis_id": "S13_EXCHANGE_QWALL_UQ_GATE",
            "title": "Upcomer exchange pressure/Qwall/UQ readiness",
            "current_evidence": (
                f"finite_exchange_rows={s13_limited['finite_exchange_rows']}; "
                f"exact_pressure_ready={s13_exact['pressure_basis_released_rows']}; "
                f"exact_Q_wall_rows={s13_exact['Q_wall_W_released_rows']}; "
                f"source_side_release_ready={s13_source['conservation_release_ready_rows']}"
            ),
            "decision": s13_source["decision"],
            "thesis_value": "Strongest blocker-localizing analysis for ordinary upcomer closure disablement.",
            "next_board_action": (
                "After active S13 rows close, claim N2 paper panels for diagnostics or "
                "S13 production harvest only if same-QOI UQ and source/property gates pass."
            ),
            "admission_or_freeze_now": "no",
        },
        {
            "rank": 2,
            "analysis_id": "REDUCED_DOF_TRANSFER_INTERPRETATION",
            "title": "Reduced-DOF empirical bias transfer interpretation",
            "current_evidence": (
                f"best_train_mae_K={reduced['best_train_corrected_mae_K']:.6g}; "
                f"best_transfer_mae_K={reduced['best_transfer_corrected_mae_K']:.6g}; "
                f"model_selection_from_transfer={reduced['model_selection_from_transfer']}"
            ),
            "decision": reduced["source_candidate_admission"],
            "thesis_value": "Separates useful diagnostic bias structure from admissible physics.",
            "next_board_action": (
                "Consume the active empirical-bias publication report after closeout; "
                "do not treat transfer performance as source/property release."
            ),
            "admission_or_freeze_now": "no",
        },
        {
            "rank": 3,
            "analysis_id": "PASSIVE_BOUNDARY_SOURCE_FINALIZATION",
            "title": "Passive-boundary source-basis finalization",
            "current_evidence": (
                f"h_range_ok={passive_physical['all_current_h_inside_engineering_range']}; "
                f"q_range_ok={passive_physical['all_current_q_inside_engineering_range']}; "
                f"families_released={passive_source['families_released']}"
            ),
            "decision": passive_source["decision"],
            "thesis_value": "Documents why plausible passive heat paths remain unreleased.",
            "next_board_action": (
                "Use N3 thermal residual-owner ablation as thesis synthesis; reopen "
                "source recovery only with independent ambient/area/insulation evidence."
            ),
            "admission_or_freeze_now": "no",
        },
        {
            "rank": 4,
            "analysis_id": "PRESSURE_F6_CAND001_RETRY_UQ_GATE",
            "title": "Pressure/F6 CAND001 retry and same-QOI UQ gate",
            "current_evidence": (
                f"terminal_success_cases={cand001['terminal_success_cases']}; "
                f"ordinary_candidate_pairs={f6['ordinary_candidate_pairs']}; "
                f"same_qoi_mesh_uq_admissible_rows={f6['same_qoi_mesh_uq_admissible_rows']}; "
                f"hybrid_reviewability={hybrid['candidate_reviewability']}"
            ),
            "decision": cand001["decision"],
            "thesis_value": "Strengthens pressure/F6 non-admission or defines a narrow retry runbook.",
            "next_board_action": (
                "Claim S10/S14 CAND001 gate only after pressure active rows close; "
                "scheduler retry needs a later exact retry row."
            ),
            "admission_or_freeze_now": "no",
        },
        {
            "rank": 5,
            "analysis_id": "PUBLICATION_SYNTHESIS_SENSOR_RUNTIME_NEGATIVE_RESULTS",
            "title": "Publication synthesis, sensor/QOI projection, and negative-result support",
            "current_evidence": (
                f"sensors_reviewed={sensor['sensors_reviewed']}; "
                f"runtime_temperature_inputs_allowed={sensor['runtime_temperature_inputs_allowed']}; "
                f"negative_contribution_rows={negative['contribution_rows']}; "
                f"predictive_blocked_gate_rows={predictive['blocked_gate_rows']}"
            ),
            "decision": "ready_for_non_scoring_thesis_support",
            "thesis_value": "Turns blocked gates into publication-grade claim boundaries and figures.",
            "next_board_action": (
                "Claim N4 sensor/QOI uncertainty table or a narrow figure/table row; "
                "keep the work non-scoring."
            ),
            "admission_or_freeze_now": "no",
        },
    ]

    gate_rows: list[dict[str, Any]] = [
        {
            "analysis_id": "S13_EXCHANGE_QWALL_UQ_GATE",
            "diagnostic_ready": yes_no(s13_limited["diagnostic_ready_gate_rows"] > 0),
            "source_property_released": yes_no(s13_source["source_property_release"]),
            "same_qoi_uq_ready": yes_no(s13_source["same_qoi_uq_ready_rows"] > 0),
            "production_ready": yes_no(s13_source["harvest_allowed"]),
            "candidate_released": "no",
            "s11_or_s15_trigger": yes_no(s13_source["s11_s12_s13_s15_s6_trigger"]),
            "fail_closed_reason": "source-side conservation, neighbor-window, and same-QOI UQ gates are not ready",
        },
        {
            "analysis_id": "REDUCED_DOF_TRANSFER_INTERPRETATION",
            "diagnostic_ready": "yes",
            "source_property_released": "no",
            "same_qoi_uq_ready": "no",
            "production_ready": "no",
            "candidate_released": "no",
            "s11_or_s15_trigger": "no",
            "fail_closed_reason": "empirical transfer is diagnostic and not a source-backed closure",
        },
        {
            "analysis_id": "PASSIVE_BOUNDARY_SOURCE_FINALIZATION",
            "diagnostic_ready": "yes",
            "source_property_released": yes_no(passive_source["source_property_release"]),
            "same_qoi_uq_ready": "no",
            "production_ready": yes_no(passive_source["run_one_train_repair"]),
            "candidate_released": "no",
            "s11_or_s15_trigger": yes_no(passive_source["s11_s15_s6_trigger"]),
            "fail_closed_reason": "no passive source family passed release gates",
        },
        {
            "analysis_id": "PRESSURE_F6_CAND001_RETRY_UQ_GATE",
            "diagnostic_ready": "yes",
            "source_property_released": "no",
            "same_qoi_uq_ready": yes_no(f6["same_qoi_mesh_uq_admissible_rows"] > 0),
            "production_ready": yes_no(cand001["terminal_success_cases"] > 0),
            "candidate_released": "no",
            "s11_or_s15_trigger": yes_no(hybrid["s11_s15_s6_trigger"]),
            "fail_closed_reason": "CAND001 has no terminal success and F6 has no ordinary candidate pairs",
        },
        {
            "analysis_id": "PUBLICATION_SYNTHESIS_SENSOR_RUNTIME_NEGATIVE_RESULTS",
            "diagnostic_ready": "yes",
            "source_property_released": "not_applicable",
            "same_qoi_uq_ready": "not_applicable",
            "production_ready": "yes_non_scoring",
            "candidate_released": "no",
            "s11_or_s15_trigger": "no",
            "fail_closed_reason": "publication support only; no scoring or admission lane",
        },
    ]

    board_rows: list[dict[str, Any]] = [
        {
            "rank": 1,
            "recommended_task": "do_not_duplicate_active_S13_rows",
            "claim_status": "wait",
            "trigger": "active S13 exact/source-side rows close or are archived",
            "output_needed": "S13 closeout summaries and Qwall/source-side UQ decision",
        },
        {
            "rank": 2,
            "recommended_task": "TODO-THESIS-N2-UPCOMER-EXCHANGE-QWALL-UQ-PAPER-PANELS-2026-07-21",
            "claim_status": "claim_after_S13_closeout",
            "trigger": "S13 diagnostic evidence remains complete and production gate remains blocked or passes",
            "output_needed": "upcomer exchange panel/caption package with no ordinary-closure admission",
        },
        {
            "rank": 3,
            "recommended_task": "TODO-THESIS-N3-THERMAL-RESIDUAL-OWNER-TRAIN-ABLATION-2026-07-21",
            "claim_status": "claimable_if_no_active_conflict",
            "trigger": "thermal residual-owner and passive-source packages remain complete",
            "output_needed": "train-only ablation table separating physics lanes from empirical diagnostics",
        },
        {
            "rank": 4,
            "recommended_task": "TODO-THESIS-N4-SENSOR-QOI-PROJECTION-UNCERTAINTY-TABLE-2026-07-21",
            "claim_status": "claimable_if_no_active_sensor_conflict",
            "trigger": "sensor-map contract remains complete",
            "output_needed": "sensor/QOI projection and runtime-temperature prohibition table",
        },
        {
            "rank": 5,
            "recommended_task": "TODO-S10-S14-PRESSURE-F6-CAND001-RETRY-AND-UQ-GATE-2026-07-21",
            "claim_status": "defer_until_pressure_rows_close",
            "trigger": "pressure/F6 active rows close and CAND001 terminal readiness is refreshed",
            "output_needed": "retry/no-retry gate; no scheduler action unless later exact row is claimed",
        },
    ]

    figure_rows: list[dict[str, Any]] = [
        {
            "artifact_id": "fig_s13_exchange_status",
            "analysis_id": "S13_EXCHANGE_QWALL_UQ_GATE",
            "target": "Ch6/Ch8 or appendix",
            "source_package": str(SOURCES["s13_limited_evidence"]),
            "claim_boundary": "diagnostic exchange evidence only; ordinary upcomer closures disabled",
        },
        {
            "artifact_id": "table_reduced_dof_transfer",
            "analysis_id": "REDUCED_DOF_TRANSFER_INTERPRETATION",
            "target": "model-form limitations section",
            "source_package": str(SOURCES["reduced_dof_transfer"]),
            "claim_boundary": "transfer screen is not source/property release",
        },
        {
            "artifact_id": "table_passive_source_release",
            "analysis_id": "PASSIVE_BOUNDARY_SOURCE_FINALIZATION",
            "target": "thermal residual ownership section",
            "source_package": str(SOURCES["passive_source"]),
            "claim_boundary": "0 released passive families; no repair execution",
        },
        {
            "artifact_id": "table_pressure_f6_waterfall",
            "analysis_id": "PRESSURE_F6_CAND001_RETRY_UQ_GATE",
            "target": "pressure/F6 non-admission section",
            "source_package": str(SOURCES["f6_same_qoi"]),
            "claim_boundary": "no component K, cluster K, clipped K, or F6 fit",
        },
        {
            "artifact_id": "table_sensor_runtime_negative_results",
            "analysis_id": "PUBLICATION_SYNTHESIS_SENSOR_RUNTIME_NEGATIVE_RESULTS",
            "target": "limitations/conclusions",
            "source_package": str(SOURCES["sensor_map"]),
            "claim_boundary": "temperature probes remain score-only and not runtime inputs",
        },
    ]

    guardrail_rows = [
        {"guardrail": "native_output_mutation", "status": "false"},
        {"guardrail": "registry_or_admission_mutation", "status": "false"},
        {"guardrail": "scheduler_action", "status": "false"},
        {"guardrail": "solver_sampler_harvest_uq_launched", "status": "false"},
        {"guardrail": "fluid_or_external_edit", "status": "false"},
        {"guardrail": "validation_holdout_external_scoring", "status": "false"},
        {"guardrail": "fitting_tuning_model_selection", "status": "false"},
        {"guardrail": "source_property_or_qwall_release", "status": "false"},
        {"guardrail": "s11_s12_s13_s15_s6_trigger", "status": "false"},
        {"guardrail": "residual_absorbed_into_internal_nu", "status": "false"},
    ]

    write_csv(
        OUT_DIR / "support_analysis_priority_matrix.csv",
        priority_rows,
        [
            "rank",
            "analysis_id",
            "title",
            "current_evidence",
            "decision",
            "thesis_value",
            "next_board_action",
            "admission_or_freeze_now",
        ],
    )
    write_csv(
        OUT_DIR / "support_analysis_gate_matrix.csv",
        gate_rows,
        [
            "analysis_id",
            "diagnostic_ready",
            "source_property_released",
            "same_qoi_uq_ready",
            "production_ready",
            "candidate_released",
            "s11_or_s15_trigger",
            "fail_closed_reason",
        ],
    )
    write_csv(
        OUT_DIR / "board_action_queue.csv",
        board_rows,
        ["rank", "recommended_task", "claim_status", "trigger", "output_needed"],
    )
    write_csv(
        OUT_DIR / "thesis_figure_table_support_manifest.csv",
        figure_rows,
        ["artifact_id", "analysis_id", "target", "source_package", "claim_boundary"],
    )
    write_csv(
        OUT_DIR / "source_manifest.csv",
        source_manifest_rows(),
        ["source_key", "path", "exists", "mutation_status"],
    )
    write_csv(
        OUT_DIR / "no_mutation_guardrails.csv",
        guardrail_rows,
        ["guardrail", "status"],
    )

    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "decision": "five_support_analyses_prioritized_no_admission_no_freeze",
        "analysis_rows": len(priority_rows),
        "gate_rows": len(gate_rows),
        "board_action_rows": len(board_rows),
        "figure_table_rows": len(figure_rows),
        "source_rows": len(SOURCES),
        "all_sources_present": all(row["exists"] for row in source_manifest_rows()),
        "candidate_released_count": 0,
        "s11_s12_s13_s15_s6_trigger": False,
        "source_property_release": False,
        "Q_wall_W_release": False,
        "production_harvest_allowed_now": False,
        "final_score_values_claimed": 0,
        "validation_holdout_external_rows_scored": 0,
        "runtime_temperature_inputs_allowed": sensor["runtime_temperature_inputs_allowed"],
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Fluid_or_external_repo_mutation": False,
        "thesis_current_file_edit": False,
        "fitting_or_model_selection": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
        "upstream_four_study_decision": four["decision"],
        "s13_source_side_decision": s13_source["decision"],
        "pressure_f6_retry_decision": cand001["decision"],
        "publication_synthesis_ready": True,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    readme = f"""---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_four_study_thesis_support_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_sensor_map_contract/summary.json
tags: [thesis-support, synthesis, s13, s8, s10, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-FIVE-BEST-THESIS-SUPPORT-ANALYSES-2026-07-22.md
  - .agent/journal/2026-07-22/five-best-thesis-support-analyses.md
task: {TASK_ID}
date: 2026-07-22
role: Coordinator / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# Five Best Thesis Support Analyses

Generated by `{TASK_ID}`.

## Decision

`{summary['decision']}`. The five best support analyses are now board-visible
and reduced into publication-facing tables, but none releases a predictive
candidate, final score, pressure/F6 coefficient, or ordinary upcomer closure.

## Analysis Priority

1. S13 upcomer exchange pressure/Qwall/UQ readiness.
2. Reduced-DOF empirical bias transfer interpretation.
3. Passive-boundary source-basis finalization.
4. Pressure/F6 CAND001 retry and same-QOI UQ gate.
5. Publication synthesis, sensor/QOI projection, and negative-result support.

## Outputs

- `support_analysis_priority_matrix.csv`
- `support_analysis_gate_matrix.csv`
- `board_action_queue.csv`
- `thesis_figure_table_support_manifest.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Claim Boundary

This package is a synthesis and dispatch reducer. It consumes existing evidence
read-only, including the four-study support gate, S13 exchange/Qwall packages,
reduced-DOF transfer screen, passive-H2 source-basis evidence, pressure/F6
CAND001 evidence, sensor-map contract, and negative-results thesis support.

It does not edit thesis body files, mutate native solver outputs, alter
registry/admission state, launch scheduler/solver/sampler/UQ work, fit or tune
models, release `Q_wall_W`, release source/property evidence, trigger S11/S12/
S13/S15/S6, or absorb residuals into internal Nu.
"""
    (OUT_DIR / "README.md").write_text(readme)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
