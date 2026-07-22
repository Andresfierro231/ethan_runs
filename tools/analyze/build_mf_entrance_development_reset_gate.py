#!/usr/bin/env python3
"""Build the entrance/development/reset missing-physics gate.

This reducer consumes existing evidence only. It does not run CFD, fit
coefficients, score protected rows, or admit a closure.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-MF-ENTRANCE-DEVELOPMENT-RESET-GATE-2026-07-22"
OUT_DIR = Path(
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_mf_entrance_development_reset_gate"
)

SOURCES = {
    "single_stream": Path(
        "work_products/2026-07/2026-07-21/"
        "2026-07-21_litrev_gated_single_stream_developing_branch"
    ),
    "boundary_layer": Path(
        "work_products/2026-07/2026-07-17/"
        "2026-07-17_predict_boundary_layer_development_scorecard"
    ),
    "d2_projection": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_mf_d2_tp_tw_qoi_projection_gate"
    ),
    "d3_wall_shape": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_mf_d3_wall_shape_axial_mixing_gate"
    ),
    "d4_source_placement": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_mf_d4_segment_source_placement_evidence_gate"
    ),
    "scoreboard_dispatch": Path(
        "work_products/2026-07/2026-07-22/"
        "2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch"
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: bool_text(value) if isinstance(value, bool) else value
                    for key, value in ((name, row.get(name, "")) for name in fieldnames)
                }
            )


def build() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    single_summary = read_json(SOURCES["single_stream"] / "summary.json")
    boundary_summary = read_json(SOURCES["boundary_layer"] / "summary.json")
    d2_summary = read_json(SOURCES["d2_projection"] / "summary.json")
    d3_summary = read_json(SOURCES["d3_wall_shape"] / "summary.json")
    d4_summary = read_json(SOURCES["d4_source_placement"] / "summary.json")
    dispatch_summary = read_json(SOURCES["scoreboard_dispatch"] / "summary.json")

    branch_rows = read_csv(SOURCES["single_stream"] / "single_stream_branch_summary.csv")
    gate_rows = read_csv(SOURCES["single_stream"] / "single_stream_developing_branch_gate.csv")
    toggle_rows = read_csv(SOURCES["boundary_layer"] / "development_toggle_scorecard.csv")
    prereq_rows = read_csv(SOURCES["boundary_layer"] / "prerequisite_gate_scorecard.csv")
    d2_plan_rows = read_csv(SOURCES["d2_projection"] / "next_analysis_plan.csv")

    branch_table: list[dict[str, Any]] = []
    for row in branch_rows:
        row_count = int(row["row_count"])
        allowed_rows = int(row["allowed_rows"])
        recirc_blocked_rows = int(row["recirc_blocked_rows"])
        uq_blocked_rows = int(row["uq_blocked_rows"])
        branch_table.append(
            {
                "span": row["span"],
                "gate_rows": row_count,
                "precheck_allowed_rows": allowed_rows,
                "recirculation_blocked_rows": recirc_blocked_rows,
                "same_qoi_uq_blocked_rows": uq_blocked_rows,
                "lane_status": row["lane_status"],
                "admission_status": row["coefficient_admission_status"],
                "entrance_development_candidate_status": (
                    "recirculation_invalid"
                    if recirc_blocked_rows
                    else "precheck_only_missing_uq_and_admitted_parent_closure"
                ),
            }
        )

    span_reasons: dict[str, Counter[str]] = defaultdict(Counter)
    for row in gate_rows:
        for reason in row["blocking_reasons"].split(";"):
            if reason:
                span_reasons[row["span"]][reason] += 1

    blocker_rows: list[dict[str, Any]] = []
    for span in sorted(span_reasons):
        for reason, count in sorted(span_reasons[span].items()):
            blocker_rows.append(
                {
                    "span": span,
                    "blocker": reason,
                    "blocked_gate_rows": count,
                    "resolution_path": {
                        "recirculation_invalid_single_stream": (
                            "route to recirculating-upcomer alternatives; do not use ordinary pipe closure"
                        ),
                        "source_envelope_not_fit": "source/property release before coefficient review",
                        "coarse_no_gci": "same-QOI mesh/GCI family required",
                        "same_QOI_UQ_missing": "same-label temporal and mesh/GCI UQ required",
                    }.get(reason, "document blocker-specific source requirement"),
                }
            )

    toggle_by_id: dict[str, dict[str, Any]] = {}
    for row in toggle_rows:
        item = toggle_by_id.setdefault(
            row["toggle_id"],
            {
                "toggle_id": row["toggle_id"],
                "toggle_description": row["toggle_description"],
                "loop_region_count": 0,
                "local_evidence_rows": 0,
                "diagnostic_ready_rows": 0,
                "executable_rows": 0,
                "dominant_execution_blocker": row["execution_blocker"],
                "score_delta_status": row["score_delta_status"],
                "admission_decision": "diagnostic_only_no_ablation_execution",
            },
        )
        item["loop_region_count"] += 1
        item["local_evidence_rows"] += int(row["local_evidence_rows"])
        if row["admission_status"].startswith("diagnostic_ready"):
            item["diagnostic_ready_rows"] += 1
        if row["ablation_executable_now"].lower() == "true":
            item["executable_rows"] += 1

    gate_matrix = list(toggle_by_id.values())
    gate_matrix.extend(
        [
            {
                "toggle_id": "d2_bulk_to_tp_projection",
                "toggle_description": "bulk-to-TP projection and reset/Graetz coordinate tests",
                "loop_region_count": "",
                "local_evidence_rows": d2_summary["tp_projection_rows"],
                "diagnostic_ready_rows": 1,
                "executable_rows": 0,
                "dominant_execution_blocker": "bulk-to-TP correction not released",
                "score_delta_status": d2_summary["decision"],
                "admission_decision": "diagnostic_only_no_runtime_temperature_input_release",
            },
            {
                "toggle_id": "d3_wall_shape_axial_mixing",
                "toggle_description": "wall-shape and axial-mixing residual layer",
                "loop_region_count": "",
                "local_evidence_rows": d3_summary["wall_rows"],
                "diagnostic_ready_rows": 1,
                "executable_rows": 0,
                "dominant_execution_blocker": "same-QOI/source-property gates missing",
                "score_delta_status": d3_summary["decision"],
                "admission_decision": "diagnostic_only_no_source_property_release",
            },
            {
                "toggle_id": "d4_segment_source_placement",
                "toggle_description": "segment source-placement residual layer",
                "loop_region_count": "",
                "local_evidence_rows": d4_summary["target_segments"],
                "diagnostic_ready_rows": 1,
                "executable_rows": 0,
                "dominant_execution_blocker": "independent source/property release missing",
                "score_delta_status": d4_summary["decision"],
                "admission_decision": "diagnostic_only_no_source_bounded_repair",
            },
        ]
    )

    handoff_rows = [
        {
            "priority": 1,
            "next_row": "TODO-MF-SIGNED-WALL-FLUX-THERMAL-DEVELOPMENT-GATE-2026-07-22",
            "why": "D2/D3/D4 show structured thermal-shape/source-placement evidence but no release",
            "required_inputs": "bulk-to-TP projection, wall-shape, source-placement, patchwise heat ledger",
            "stop_condition": "source/property or runtime-temperature gate fails",
        },
        {
            "priority": 2,
            "next_row": "TODO-MF-RECIRCULATING-UPCOMER-ALTERNATIVES-GATE-2026-07-22",
            "why": "left lower/upper legs are recirculation-invalid for single-stream developing branches",
            "required_inputs": "S13 target-plus temporal UQ, mesh/GCI gate, onset/recirculation packages",
            "stop_condition": "same-label mesh/GCI or production harvest remains blocked",
        },
        {
            "priority": 3,
            "next_row": "TODO-1D-AMX1-AXIAL-MIXING-FLUID-API-HANDOFF-2026-07-22",
            "why": "axial-mixing API handoff is useful only after source and conservation guardrails are explicit",
            "required_inputs": "AMX1 dry contract, D3 wall-shape gate, conservation tests",
            "stop_condition": "API cannot be disabled by default or source/property labels are absent",
        },
    ]

    manifest_rows = [
        {
            "source_id": source_id,
            "source_path": str(path),
            "files_used": {
                "single_stream": "summary.json;single_stream_branch_summary.csv;single_stream_developing_branch_gate.csv",
                "boundary_layer": "summary.json;development_toggle_scorecard.csv;prerequisite_gate_scorecard.csv",
                "d2_projection": "summary.json;next_analysis_plan.csv",
                "d3_wall_shape": "summary.json",
                "d4_source_placement": "summary.json",
                "scoreboard_dispatch": "summary.json",
            }[source_id],
            "mutation_status": "read_only",
        }
        for source_id, path in SOURCES.items()
    ]

    write_csv(
        OUT_DIR / "branch_development_admissibility.csv",
        branch_table,
        [
            "span",
            "gate_rows",
            "precheck_allowed_rows",
            "recirculation_blocked_rows",
            "same_qoi_uq_blocked_rows",
            "lane_status",
            "admission_status",
            "entrance_development_candidate_status",
        ],
    )
    write_csv(
        OUT_DIR / "reset_development_blocker_matrix.csv",
        blocker_rows,
        ["span", "blocker", "blocked_gate_rows", "resolution_path"],
    )
    write_csv(
        OUT_DIR / "development_model_form_gate_matrix.csv",
        gate_matrix,
        [
            "toggle_id",
            "toggle_description",
            "loop_region_count",
            "local_evidence_rows",
            "diagnostic_ready_rows",
            "executable_rows",
            "dominant_execution_blocker",
            "score_delta_status",
            "admission_decision",
        ],
    )
    write_csv(
        OUT_DIR / "successor_implementation_queue.csv",
        handoff_rows,
        ["priority", "next_row", "why", "required_inputs", "stop_condition"],
    )
    write_csv(
        OUT_DIR / "source_manifest.csv",
        manifest_rows,
        ["source_id", "source_path", "files_used", "mutation_status"],
    )
    write_csv(
        OUT_DIR / "prerequisite_gate_snapshot.csv",
        prereq_rows,
        ["gate", "status", "admitted_rows", "reason"],
    )
    write_csv(
        OUT_DIR / "d2_next_analysis_snapshot.csv",
        d2_plan_rows,
        ["priority", "analysis", "question", "inputs_needed", "expected_insight", "acceptance"],
    )

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "entrance_development_reset_gate_diagnostic_only_no_admission",
        "single_stream_gate_rows": single_summary["gate_rows"],
        "single_stream_allowed_precheck_rows": single_summary["allowed_precheck_only_rows"],
        "single_stream_admitted_rows": single_summary["admitted_rows"],
        "branch_rows": len(branch_table),
        "recirculation_invalid_spans": sum(
            1 for row in branch_table if row["recirculation_blocked_rows"]
        ),
        "same_qoi_uq_blocked_spans": sum(
            1 for row in branch_table if row["same_qoi_uq_blocked_rows"]
        ),
        "boundary_toggle_rows": boundary_summary["toggle_rows"],
        "boundary_diagnostic_ready_toggle_rows": boundary_summary[
            "diagnostic_ready_toggle_rows"
        ],
        "boundary_executable_ablation_rows": boundary_summary["executable_ablation_rows"],
        "development_gate_rows": len(gate_matrix),
        "successor_rows": len(handoff_rows),
        "dispatch_prior_board_rows_listed": dispatch_summary["board_dispatch_rows"],
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Fluid_or_external_repo_mutation": False,
        "thesis_current_or_latex_edit": False,
        "validation_holdout_external_rows_scored": 0,
        "fitting_or_model_selection": False,
        "source_property_release": False,
        "Qwall_or_source_side_release": False,
        "coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "runtime_leakage_relaxed": False,
        "residual_absorbed_into_internal_nu": False,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    readme = f"""---
provenance:
  - {SOURCES['single_stream'] / 'summary.json'}
  - {SOURCES['single_stream'] / 'single_stream_branch_summary.csv'}
  - {SOURCES['single_stream'] / 'single_stream_developing_branch_gate.csv'}
  - {SOURCES['boundary_layer'] / 'summary.json'}
  - {SOURCES['boundary_layer'] / 'development_toggle_scorecard.csv'}
  - {SOURCES['d2_projection'] / 'summary.json'}
  - {SOURCES['d3_wall_shape'] / 'summary.json'}
  - {SOURCES['d4_source_placement'] / 'summary.json'}
tags: [missing-physics, entrance-development, reset-length, thesis, no-admission]
related:
  - .agent/status/2026-07-22_TODO-MF-ENTRANCE-DEVELOPMENT-RESET-GATE-2026-07-22.md
  - .agent/journal/2026-07-22/mf-entrance-development-reset-gate.md
  - imports/2026-07-22_mf_entrance_development_reset_gate.json
task: {TASK_ID}
date: 2026-07-22
role: Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# MF Entrance / Development / Reset Gate

Decision: `{summary['decision']}`.

This package starts the missing-physics implementation sequence from existing
evidence only. It confirms that entrance/development/reset terms are
diagnostic-ready in places, but not executable as an admitted coupled ablation
or closure.

Key result:

- Single-stream developing gate rows: `{summary['single_stream_gate_rows']}`.
- Precheck-only allowed rows: `{summary['single_stream_allowed_precheck_rows']}`.
- Admitted rows: `{summary['single_stream_admitted_rows']}`.
- Boundary-layer executable ablation rows: `{summary['boundary_executable_ablation_rows']}`.
- Recirculation-invalid spans: `{summary['recirculation_invalid_spans']}`.
- Same-QOI-UQ blocked spans: `{summary['same_qoi_uq_blocked_spans']}`.

Outputs:

- `branch_development_admissibility.csv`
- `reset_development_blocker_matrix.csv`
- `development_model_form_gate_matrix.csv`
- `successor_implementation_queue.csv`
- `prerequisite_gate_snapshot.csv`
- `d2_next_analysis_snapshot.csv`
- `source_manifest.csv`
- `summary.json`

No source/property release, protected scoring, coefficient admission, final
score, Fluid edit, solver/scheduler action, or residual absorption into
internal Nu occurred.
"""
    (OUT_DIR / "README.md").write_text(readme)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
