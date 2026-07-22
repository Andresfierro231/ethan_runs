#!/usr/bin/env python3
"""Post-sampler S13 mesh/GCI and production-harvest gate.

This builder is intentionally no-launch. It consumes the completed S13
medium/fine sampler package and prior S13 UQ gates to decide whether the
exchange-cell path can move to production harvest after the sampler closeout.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-THESIS-STUDY-S13-UPCOMER-EXCHANGE-POST-SAMPLER-GCI-PRODUCTION-HARVEST-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_thesis_study_s13_upcomer_exchange_post_sampler_gci_production_harvest"
)

SAMPLER = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler"
)
MONITOR = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_medium_fine_sampler_duplicate_job_monitor"
)
TEMPORAL_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus"
)
MESH_GCI_GATE = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_qwall_mesh_gci_uq_gate"
)
PRE_SAMPLER_PRODUCTION = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_thesis_study_s13_upcomer_exchange_production_harvest_uq"
)

QOI_LABELS = [
    "Q_wall_W",
    "mdot_exchange_positive_outward_proxy_kg_s",
    "tau_recirc_proxy_s",
    "wall_core_bulk_temperature_contrast_K",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def require_inputs() -> None:
    required = [
        SAMPLER / "summary.json",
        SAMPLER / "mesh_gci_readiness_gate.csv",
        SAMPLER / "sampling_error_log.csv",
        SAMPLER / "mesh_level_geometry_summary.csv",
        SAMPLER / "medium_fine_terminal_window_reductions.csv",
        SAMPLER / "medium_fine_exact_label_qoi_rows.csv",
        MONITOR / "summary.json",
        MONITOR / "output_usable_gate.csv",
        MONITOR / "repair_recommendation.csv",
        TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv",
        MESH_GCI_GATE / "qwall_exchange_mesh_gci_gate_matrix.csv",
        MESH_GCI_GATE / "production_harvest_consequence.csv",
        PRE_SAMPLER_PRODUCTION / "summary.json",
        PRE_SAMPLER_PRODUCTION / "next_compute_handoff.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 post-sampler source files: " + "; ".join(missing))


def bool_text(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def header_only(path: Path) -> bool:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle) == 1


def build_sampler_disposition(
    sampler_summary: dict[str, Any],
    monitor_summary: dict[str, Any],
    output_gate_rows: list[dict[str, str]],
    sampling_errors: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in output_gate_rows:
        rows.append(
            {
                "artifact": row["artifact"],
                "observed_rows_or_state": row["observed_rows_or_state"],
                "usable_for_terminal_qoi": row["usable_for_terminal_qoi"],
                "usable_for_mesh_gci": row["usable_for_mesh_gci"],
                "post_sampler_disposition": row["decision"],
                "reason": row["reason"],
                "source_path": rel(MONITOR / "output_usable_gate.csv"),
            }
        )

    error_counts = Counter(row["error_message"] for row in sampling_errors)
    for message, count in sorted(error_counts.items()):
        rows.append(
            {
                "artifact": "sampling_error_cause",
                "observed_rows_or_state": f"{count} rows",
                "usable_for_terminal_qoi": False,
                "usable_for_mesh_gci": False,
                "post_sampler_disposition": "repair_required",
                "reason": message,
                "source_path": rel(SAMPLER / "sampling_error_log.csv"),
            }
        )

    rows.append(
        {
            "artifact": "job_duplicate_resolution",
            "observed_rows_or_state": f"jobs_completed={monitor_summary.get('jobs_completed')}; cancellation={monitor_summary.get('job_cancellation_performed')}",
            "usable_for_terminal_qoi": False,
            "usable_for_mesh_gci": False,
            "post_sampler_disposition": monitor_summary["decision"],
            "reason": "duplicate jobs completed before cancellation; package still fail-closed",
            "source_path": rel(MONITOR / "summary.json"),
        }
    )
    rows.append(
        {
            "artifact": "sampler_summary",
            "observed_rows_or_state": (
                f"terminal={sampler_summary.get('terminal_window_reduction_rows')}; "
                f"exact_qoi={sampler_summary.get('exact_label_qoi_rows')}; "
                f"errors={sampler_summary.get('sampling_error_rows')}"
            ),
            "usable_for_terminal_qoi": sampler_summary.get("exact_label_qoi_rows", 0) > 0,
            "usable_for_mesh_gci": sampler_summary.get("same_label_mesh_gci_ready", False),
            "post_sampler_disposition": sampler_summary["decision"],
            "reason": "sampler closeout summary is the controlling post-trigger evidence",
            "source_path": rel(SAMPLER / "summary.json"),
        }
    )
    return rows


def build_qoi_readiness(
    temporal_rows: list[dict[str, str]],
    mesh_gci_rows: list[dict[str, str]],
    sampler_gate_rows: list[dict[str, str]],
    sampler_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    temporal_by_qoi = {row["qoi_label"]: row for row in temporal_rows}
    mesh_by_qoi = {row["qoi_label"]: row for row in mesh_gci_rows}
    sampler_by_qoi = {row["qoi_label"]: row for row in sampler_gate_rows}
    rows: list[dict[str, Any]] = []
    for qoi in QOI_LABELS:
        temporal = temporal_by_qoi[qoi]
        mesh = mesh_by_qoi[qoi]
        sampler = sampler_by_qoi[qoi]
        rows.append(
            {
                "qoi_label": qoi,
                "same_qoi_temporal_uq_status": temporal["same_qoi_temporal_uq_status"],
                "same_qoi_temporal_max_relative_percent": temporal["max_relative_temporal_uncertainty_percent"],
                "pre_sampler_mesh_gci_status": mesh["mesh_gci_uq_status"],
                "post_sampler_medium_fine_terminal_rows": sampler_summary.get("terminal_window_reduction_rows", 0),
                "post_sampler_exact_label_qoi_rows": sampler_summary.get("exact_label_qoi_rows", 0),
                "post_sampler_same_label_mesh_gci_ready": bool_text(sampler["same_label_mesh_gci_ready"]),
                "production_harvest_allowed_now": False,
                "admission_allowed_now": False,
                "reason": "temporal UQ exists but post-sampler exact-label medium/fine rows are absent",
            }
        )
    return rows


def build_production_gate(
    sampler_summary: dict[str, Any],
    monitor_summary: dict[str, Any],
    pre_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "gate": "sampler_terminal_execution",
            "status": "fail_closed",
            "pass": False,
            "evidence": f"exact_label_qoi_rows={sampler_summary.get('exact_label_qoi_rows')}; terminal_window_reduction_rows={sampler_summary.get('terminal_window_reduction_rows')}",
            "consequence": "no terminal medium/fine QOI rows exist for production harvest",
        },
        {
            "gate": "duplicate_job_disposition",
            "status": "complete_no_cancellation_needed",
            "pass": True,
            "evidence": f"jobs_completed={monitor_summary.get('jobs_completed')}; jobs_running_now={monitor_summary.get('jobs_running_now')}; new_submission={monitor_summary.get('new_submission_performed')}",
            "consequence": "scheduler state is settled; output package remains unusable for terminal evidence",
        },
        {
            "gate": "same_qoi_temporal_uq",
            "status": "diagnostic_pass",
            "pass": True,
            "evidence": f"same_qoi_temporal_uq_complete_qois={pre_summary.get('same_qoi_temporal_uq_complete_qois')}",
            "consequence": "temporal support is preserved but cannot replace mesh/GCI evidence",
        },
        {
            "gate": "same_label_mesh_gci",
            "status": "blocked_no_post_sampler_rows",
            "pass": False,
            "evidence": f"same_label_mesh_gci_ready={sampler_summary.get('same_label_mesh_gci_ready')}",
            "consequence": "no GCI computation or mesh-family acceptance may be claimed",
        },
        {
            "gate": "production_harvest",
            "status": "do_not_run",
            "pass": False,
            "evidence": "terminal QOI, exact-label medium/fine, mesh/GCI, and source/property release gates are not complete",
            "consequence": "no production harvest, coefficient fit, or final score release",
        },
    ]


def build_s11_consequence(pre_summary: dict[str, Any], sampler_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "downstream_gate": "S11 candidate source/property refresh",
            "status": "closed",
            "candidate_count": 0,
            "reason": "no runtime-legal S13 candidate has post-sampler same-label mesh/GCI evidence",
            "required_before_reopen": "one exact-label exchange-cell candidate with terminal QOI rows, source/property basis, split permissions, and UQ",
        },
        {
            "downstream_gate": "S12 thermal-shape candidate",
            "status": "not_advanced_by_this_row",
            "candidate_count": 0,
            "reason": "S13 diagnostic exchange evidence does not release a thermal-shape closure",
            "required_before_reopen": "runtime-legal wall/test-section/source-property candidate outside realized wallHeatFlux",
        },
        {
            "downstream_gate": "S13 exchange-cell admission",
            "status": "fail_closed",
            "candidate_count": pre_summary.get("exchange_cell_fit_ready_rows", 0),
            "reason": f"post-sampler exact-label QOI rows={sampler_summary.get('exact_label_qoi_rows')}",
            "required_before_reopen": "repair sampler face-area vectors and produce finite coarse/medium/fine same-label rows",
        },
        {
            "downstream_gate": "S15 freeze and S6 final score",
            "status": "closed",
            "candidate_count": 0,
            "reason": "S12/S13/S14 have not released exactly one runtime-legal candidate",
            "required_before_reopen": "successful S11 source/property refresh for exactly one predeclared candidate",
        },
    ]


def build_figure_targets() -> list[dict[str, Any]]:
    return [
        {
            "target_id": "fig_s13_post_sampler_gate_waterfall",
            "recommended_artifact": "production_go_no_go_gate.csv",
            "purpose": "show why temporal UQ did not unlock production after sampler execution",
            "status": "table_ready_no_plot_required",
        },
        {
            "target_id": "table_s13_qoi_readiness_after_sampler",
            "recommended_artifact": "post_sampler_qoi_mesh_gci_readiness.csv",
            "purpose": "list four QOI labels with temporal UQ, post-sampler rows, mesh/GCI, production, and admission flags",
            "status": "table_ready",
        },
        {
            "target_id": "table_s13_repair_queue",
            "recommended_artifact": "next_repair_queue.csv",
            "purpose": "give the next implementer exact repair order before rerun",
            "status": "table_ready",
        },
    ]


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)

    sampler_summary = read_json(SAMPLER / "summary.json")
    monitor_summary = read_json(MONITOR / "summary.json")
    pre_summary = read_json(PRE_SAMPLER_PRODUCTION / "summary.json")
    output_gate_rows = read_csv(MONITOR / "output_usable_gate.csv")
    repair_rows = read_csv(MONITOR / "repair_recommendation.csv")
    sampling_errors = read_csv(SAMPLER / "sampling_error_log.csv")
    geometry_rows = read_csv(SAMPLER / "mesh_level_geometry_summary.csv")
    sampler_gate_rows = read_csv(SAMPLER / "mesh_gci_readiness_gate.csv")
    temporal_rows = read_csv(TEMPORAL_UQ / "same_qoi_temporal_uq_summary.csv")
    mesh_gci_rows = read_csv(MESH_GCI_GATE / "qwall_exchange_mesh_gci_gate_matrix.csv")

    sampler_disposition = build_sampler_disposition(sampler_summary, monitor_summary, output_gate_rows, sampling_errors)
    qoi_readiness = build_qoi_readiness(temporal_rows, mesh_gci_rows, sampler_gate_rows, sampler_summary)
    production_gate = build_production_gate(sampler_summary, monitor_summary, pre_summary)
    s11_consequence = build_s11_consequence(pre_summary, sampler_summary)
    figure_targets = build_figure_targets()

    source_manifest = [
        {"source_id": "medium_fine_sampler", "path": rel(SAMPLER), "use": "controlling post-trigger sampler output and fail-closed counts"},
        {"source_id": "duplicate_job_monitor", "path": rel(MONITOR), "use": "scheduler/output adjudication and repair recommendation"},
        {"source_id": "same_qoi_temporal_uq", "path": rel(TEMPORAL_UQ), "use": "same-QOI temporal UQ status for four exchange labels"},
        {"source_id": "mesh_gci_gate", "path": rel(MESH_GCI_GATE), "use": "pre-sampler mesh/GCI gate consequence and label matrix"},
        {"source_id": "pre_sampler_production_gate", "path": rel(PRE_SAMPLER_PRODUCTION), "use": "prior production-harvest blocked baseline"},
    ]
    guardrails = [
        {"guardrail": "native_solver_outputs_mutated", "status": False},
        {"guardrail": "registry_or_admission_mutated", "status": False},
        {"guardrail": "scheduler_action", "status": False},
        {"guardrail": "solver_postprocess_sampler_harvest_uq_launched", "status": False},
        {"guardrail": "Fluid_or_external_repo_edited", "status": False},
        {"guardrail": "validation_holdout_external_scoring", "status": False},
        {"guardrail": "Qwall_or_source_property_release", "status": False},
        {"guardrail": "coefficient_or_final_score_admission", "status": False},
        {"guardrail": "S11_S12_S13_S15_S6_trigger", "status": False},
        {"guardrail": "proxy_substitution", "status": False},
        {"guardrail": "residual_absorbed_into_internal_Nu", "status": False},
    ]

    write_csv(
        OUT / "post_sampler_disposition.csv",
        sampler_disposition,
        [
            "artifact",
            "observed_rows_or_state",
            "usable_for_terminal_qoi",
            "usable_for_mesh_gci",
            "post_sampler_disposition",
            "reason",
            "source_path",
        ],
    )
    write_csv(
        OUT / "post_sampler_qoi_mesh_gci_readiness.csv",
        qoi_readiness,
        [
            "qoi_label",
            "same_qoi_temporal_uq_status",
            "same_qoi_temporal_max_relative_percent",
            "pre_sampler_mesh_gci_status",
            "post_sampler_medium_fine_terminal_rows",
            "post_sampler_exact_label_qoi_rows",
            "post_sampler_same_label_mesh_gci_ready",
            "production_harvest_allowed_now",
            "admission_allowed_now",
            "reason",
        ],
    )
    write_csv(
        OUT / "production_go_no_go_gate.csv",
        production_gate,
        ["gate", "status", "pass", "evidence", "consequence"],
    )
    write_csv(
        OUT / "s11_s15_consequence_table.csv",
        s11_consequence,
        ["downstream_gate", "status", "candidate_count", "reason", "required_before_reopen"],
    )
    write_csv(
        OUT / "next_repair_queue.csv",
        repair_rows,
        ["priority", "repair_task", "why", "success_signal", "forbidden_action"],
    )
    write_csv(
        OUT / "figure_table_targets.csv",
        figure_targets,
        ["target_id", "recommended_artifact", "purpose", "status"],
    )
    write_csv(OUT / "source_manifest.csv", source_manifest, ["source_id", "path", "use"])
    write_csv(OUT / "no_mutation_guardrails.csv", guardrails, ["guardrail", "status"])

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "post_sampler_fail_closed_no_terminal_qoi_no_mesh_gci_no_production_harvest",
        "sampler_decision": sampler_summary["decision"],
        "duplicate_monitor_decision": monitor_summary["decision"],
        "geometry_rows": len(geometry_rows),
        "source_contract_rows": sampler_summary.get("source_contract_rows", 0),
        "source_preflight_ready_rows": sampler_summary.get("source_preflight_ready_rows", 0),
        "terminal_window_reduction_rows": sampler_summary.get("terminal_window_reduction_rows", 0),
        "exact_label_qoi_rows": sampler_summary.get("exact_label_qoi_rows", 0),
        "sampling_error_rows": len(sampling_errors),
        "qoi_labels_reviewed": len(QOI_LABELS),
        "same_qoi_temporal_uq_executed_qois": sum(
            1 for row in qoi_readiness if row["same_qoi_temporal_uq_status"] == "executed"
        ),
        "post_sampler_same_label_mesh_gci_ready_qois": sum(
            1 for row in qoi_readiness if row["post_sampler_same_label_mesh_gci_ready"] is True
        ),
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "s11_reviewable_candidate": False,
        "s15_freeze_allowed": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "source_property_release": False,
        "Qwall_release": False,
        "ordinary_upcomer_Nu_fD_K_admitted": False,
        "exchange_cell_coefficient_admitted": False,
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "solver_postprocess_sampler_harvest_uq_launched": False,
        "validation_holdout_external_scoring": False,
        "proxy_substitution": False,
        "residual_absorbed_into_internal_Nu": False,
        "gate_status_counts": dict(Counter(row["status"] for row in production_gate)),
        "next_required_action": "patch sampler face-area-vector columns and rerun one-case/window smoke in a clean output package before any full medium/fine rerun",
    }
    write_json(OUT / "summary.json", summary)

    readme = f"""---
provenance:
  task_id: {TASK_ID}
  generated_at_utc: {summary['generated_at_utc']}
tags:
  - s13
  - upcomer-exchange
  - post-sampler
  - mesh-gci
  - production-harvest
  - fail-closed
related:
  - {rel(SAMPLER)}
  - {rel(MONITOR)}
  - {rel(TEMPORAL_UQ)}
  - {rel(MESH_GCI_GATE)}
---

# S13 Post-Sampler GCI / Production-Harvest Gate

This package answers the post-trigger question: after the medium/fine exact-label
sampler closed, can S13 move to same-label mesh/GCI, production harvest,
source/property release, or admission?

## Result

Decision: `{summary['decision']}`.

The sampler produced `{summary['geometry_rows']}` geometry rows, but
`{summary['terminal_window_reduction_rows']}` terminal-window reduction rows and
`{summary['exact_label_qoi_rows']}` exact-label QOI rows. All
`{summary['sampling_error_rows']}` sampling attempts failed before QOI reduction
because the generated exchange-interface rows lacked the face-area-vector
components required by `interface_reduction`.

## Assumptions

- Geometry-only medium/fine rows are useful repair evidence, not terminal QOI
  evidence.
- Same-QOI temporal UQ remains valid diagnostic support for the existing coarse
  target windows, but it cannot substitute for same-label mesh-family evidence.
- No source-side heat-flow diagnostic is relabeled as direct `Q_wall_W`.
- No validation, holdout, or external-test scoring is performed in this row.

## Caveats

- Duplicate jobs `3310176` and `3310179` both completed before cancellation was
  applicable. The monitor found the current package fail-closed, so this package
  uses it only as failure evidence.
- The next rerun should use a clean output package or lock to avoid duplicate
  writes.
- Admission language remains forbidden: ordinary upcomer `Nu/f_D/K` and
  exchange-cell coefficients are both non-admitted.

## Open First

- `summary.json`
- `production_go_no_go_gate.csv`
- `post_sampler_qoi_mesh_gci_readiness.csv`
- `post_sampler_disposition.csv`
- `next_repair_queue.csv`
- `s11_s15_consequence_table.csv`

## Next Required Work

Patch the medium/fine sampler so generated face rows carry owner-to-neighbor
face-area-vector components, add a focused unit test for those columns, then run
one case/window smoke in a clean package before any full six-case rerun.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
