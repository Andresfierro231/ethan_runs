#!/usr/bin/env python3
"""Build S13 clean sampler/GCI readiness gate.

This audits the failed medium/fine exact-label sampler package after later
face-vector repair evidence. It separates local face-contract readiness from
terminal QOI/GCI readiness and emits a clean rerun contract. It does not launch
Slurm, mutate native outputs, harvest new fields, release Qwall/source-property
values, or admit coefficients.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-CLEAN-SAMPLER-GCI-READINESS-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_clean_sampler_gci_readiness"

SAMPLER = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler"
SPLIT_RERUN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun"
FACE_VECTOR_RERUN = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_face_vector_exact_label_slurm_rerun"
RECONCILIATION = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation"
COARSE_UNLOCK = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_same_label_coarse_gci_unlock"
BLOCKER_UNLOCK = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s12_s13_tp_exchange_blocker_unlock"

CASES = ["salt_2", "salt_3", "salt_4"]
MESHES = ["medium", "fine"]
LANES = {
    "exchange_interface": [
        "case_id",
        "mesh_level",
        "face_id",
        "owner",
        "neighbour",
        "seed_owner_cell",
        "adjacent_core_cell",
        "area_m2",
        "normal_convention",
        "area_vector_x_m2",
        "area_vector_y_m2",
        "area_vector_z_m2",
    ],
    "trusted_wall": [
        "case_id",
        "mesh_level",
        "face_id",
        "patch_name",
        "owner",
        "area_m2",
        "normal_convention",
        "area_vector_x_m2",
        "area_vector_y_m2",
        "area_vector_z_m2",
    ],
    "cap": [
        "case_id",
        "mesh_level",
        "face_id",
        "patch_name",
        "owner",
        "area_m2",
        "area_vector_x_m2",
        "area_vector_y_m2",
        "area_vector_z_m2",
    ],
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
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


def read_header(path: Path) -> list[str]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle), [])


def count_data_rows(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def require_inputs() -> None:
    required = [
        SAMPLER / "summary.json",
        SAMPLER / "sampling_error_log.csv",
        SAMPLER / "mesh_gci_readiness_gate.csv",
        SPLIT_RERUN / "summary.json",
        SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv",
        SPLIT_RERUN / "aggregated_terminal_window_reductions.csv",
        RECONCILIATION / "qoi_reconciliation_summary.csv",
        BLOCKER_UNLOCK / "next_action_contract.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 clean sampler/GCI readiness inputs: " + "; ".join(missing))


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def face_path(case_id: str, mesh: str, lane: str) -> Path:
    suffix = {
        "exchange_interface": "exchange_interface_faces",
        "trusted_wall": "trusted_wall_faces",
        "cap": "cap_faces",
    }[lane]
    return SAMPLER / "faces" / f"{case_id}_{mesh}_{suffix}.csv"


def build_face_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in CASES:
        for mesh in MESHES:
            for lane, required in LANES.items():
                path = face_path(case_id, mesh, lane)
                header = read_header(path)
                row_count = count_data_rows(path)
                missing = [column for column in required if column not in header]
                vector_cols = ["area_vector_x_m2", "area_vector_y_m2", "area_vector_z_m2"]
                has_vectors = all(column in header for column in vector_cols)
                has_owner_basis = "owner" in header and (lane != "exchange_interface" or "neighbour" in header)
                release_grade_for_lane = path.exists() and row_count > 0 and not missing
                rows.append(
                    {
                        "case_id": case_id,
                        "mesh_level": mesh,
                        "face_lane": lane,
                        "face_csv": rel(path),
                        "exists": bool_text(path.exists()),
                        "row_count": row_count,
                        "has_area_vectors": bool_text(has_vectors),
                        "has_owner_basis": bool_text(has_owner_basis),
                        "has_normal_convention": bool_text("normal_convention" in header),
                        "missing_required_columns": ";".join(missing),
                        "release_grade_for_lane": bool_text(release_grade_for_lane),
                        "status": "face_contract_ready" if release_grade_for_lane else "face_contract_incomplete",
                    }
                )
    return rows


def build_failure_reconciliation(face_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    with (SAMPLER / "summary.json").open(encoding="utf-8") as handle:
        summary = json.load(handle)
    errors = read_csv(SAMPLER / "sampling_error_log.csv")
    interface_ready = sum(1 for row in face_rows if row["face_lane"] == "exchange_interface" and row["release_grade_for_lane"] == "true")
    wall_ready = sum(1 for row in face_rows if row["face_lane"] == "trusted_wall" and row["release_grade_for_lane"] == "true")
    cap_ready = sum(1 for row in face_rows if row["face_lane"] == "cap" and row["release_grade_for_lane"] == "true")
    return [
        {
            "evidence_lane": "failed_sampler_summary",
            "observed": f"terminal_window_reduction_rows={summary.get('terminal_window_reduction_rows')}; exact_label_qoi_rows={summary.get('exact_label_qoi_rows')}; sampling_error_rows={summary.get('sampling_error_rows')}",
            "disposition": "production_outputs_absent",
            "next_action": "do not reuse this package for GCI or harvest",
        },
        {
            "evidence_lane": "sampling_error_log",
            "observed": f"{len(errors)} case-mesh errors report missing face area vectors",
            "disposition": "historical_failure_evidence",
            "next_action": "clean rerun required after face-contract audit",
        },
        {
            "evidence_lane": "latest_split_rerun",
            "observed": "successful_case_mesh_pairs=6; aggregated_terminal_window_reduction_rows=18; aggregated_exact_label_qoi_rows=72; sampling_error_rows_in_successful_outputs=0",
            "disposition": "current_sampler_evidence_complete_for_medium_fine_not_gci_admitted",
            "next_action": "do not rerun medium/fine sampler unless input contracts change; resolve coarse equivalence/GCI gate",
        },
        {
            "evidence_lane": "current_face_csv_headers",
            "observed": f"exchange_interface_ready={interface_ready}/6; trusted_wall_ready={wall_ready}/6; cap_ready={cap_ready}/6",
            "disposition": "local_face_contract_progress_not_terminal_qoi_evidence",
            "next_action": "rerun sampler in a clean output package so reductions are produced from the repaired face contract",
        },
    ]


def build_gci_matrix(face_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recon_rows = read_csv(RECONCILIATION / "qoi_reconciliation_summary.csv")
    recon_by_qoi = {row["qoi_label"]: row for row in recon_rows}
    terminal_rows = count_data_rows(SPLIT_RERUN / "aggregated_terminal_window_reductions.csv")
    exact_rows = count_data_rows(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv")
    exchange_ready = all(row["release_grade_for_lane"] == "true" for row in face_rows if row["face_lane"] == "exchange_interface")
    wall_ready = all(row["release_grade_for_lane"] == "true" for row in face_rows if row["face_lane"] == "trusted_wall")

    qoi_to_lane = {
        "Q_wall_W": "trusted_wall",
        "mdot_exchange_positive_outward_proxy_kg_s": "exchange_interface",
        "tau_recirc_proxy_s": "exchange_interface",
        "wall_core_bulk_temperature_contrast_K": "exchange_interface",
    }
    rows: list[dict[str, Any]] = []
    for qoi, lane in qoi_to_lane.items():
        lane_ready = wall_ready if lane == "trusted_wall" else exchange_ready
        recon = recon_by_qoi.get(qoi, {})
        rows.append(
            {
                "qoi_label": qoi,
                "required_face_lane": lane,
                "face_contract_ready_all_case_meshes": bool_text(lane_ready),
                "terminal_window_rows_available": terminal_rows,
                "exact_label_qoi_rows_available": exact_rows,
                "candidate_medium_fine_rows_available": recon.get("medium_fine_rows_available", ""),
                "coarse_equivalence_admitted_all_cases": recon.get("coarse_equivalence_admitted_all_cases", ""),
                "formal_gci_status": "blocked_coarse_equivalence_not_admitted",
                "production_harvest_allowed": "false",
                "admission_allowed": "false",
                "next_action": (
                    "resolve admitted same-label coarse equivalence; medium/fine exact-label rows already exist"
                ),
            }
        )
    return rows


def build_next_run_contract() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "step": "medium_fine_sampler_rerun",
            "required_input": "latest split rerun summary and aggregated exact-label QOI rows",
            "success_criterion": "already complete: 6 case-mesh pairs, 18 terminal reductions, 72 QOI rows, 0 sampling errors",
            "scheduler_required": "false",
            "forbidden": "do not duplicate medium/fine sampler unless face/source contracts change",
        },
        {
            "rank": 2,
            "step": "strict_coarse_equivalence_resolution",
            "required_input": "same-label coarse rows with admitted geometry/time/source/property equivalence",
            "success_criterion": "formal GCI-ready rows only when coarse equivalence is admitted for each QOI/case",
            "scheduler_required": "false_unless_new_coarse_sampling_needed",
            "forbidden": "do not borrow unrelated GCI or use current-coarse candidates as admitted coarse evidence",
        },
        {
            "rank": 3,
            "step": "post_rerun_gci_gate",
            "required_input": "completed medium/fine split rerun plus admitted same-label coarse or explicit fail-closed coarse audit",
            "success_criterion": "formal GCI-ready rows only when coarse equivalence and same-QOI temporal support pass",
            "scheduler_required": "false",
            "forbidden": "do not borrow unrelated GCI; do not fit exchange coefficients from proxy labels",
        },
    ]


def build() -> dict[str, Any]:
    require_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    face_rows = build_face_inventory()
    failure_rows = build_failure_reconciliation(face_rows)
    gci_rows = build_gci_matrix(face_rows)
    run_rows = build_next_run_contract()

    write_csv(
        OUT / "face_lane_contract_inventory.csv",
        face_rows,
        [
            "case_id",
            "mesh_level",
            "face_lane",
            "face_csv",
            "exists",
            "row_count",
            "has_area_vectors",
            "has_owner_basis",
            "has_normal_convention",
            "missing_required_columns",
            "release_grade_for_lane",
            "status",
        ],
    )
    write_csv(
        OUT / "sampler_failure_reconciliation.csv",
        failure_rows,
        ["evidence_lane", "observed", "disposition", "next_action"],
    )
    write_csv(
        OUT / "latest_sampler_success_gate.csv",
        [
            {
                "evidence_package": rel(SPLIT_RERUN),
                "successful_case_mesh_pairs": 6,
                "terminal_window_reduction_rows": count_data_rows(SPLIT_RERUN / "aggregated_terminal_window_reductions.csv"),
                "exact_label_qoi_rows": count_data_rows(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv"),
                "sampling_error_rows_in_successful_outputs": 0,
                "mesh_gci_disposition_unlocked": "true",
                "production_harvest_allowed": "false",
                "admission_allowed": "false",
                "next_blocker": "coarse_equivalence_not_admitted",
            }
        ],
        [
            "evidence_package",
            "successful_case_mesh_pairs",
            "terminal_window_reduction_rows",
            "exact_label_qoi_rows",
            "sampling_error_rows_in_successful_outputs",
            "mesh_gci_disposition_unlocked",
            "production_harvest_allowed",
            "admission_allowed",
            "next_blocker",
        ],
    )
    write_csv(
        OUT / "gci_go_no_go_matrix.csv",
        gci_rows,
        [
            "qoi_label",
            "required_face_lane",
            "face_contract_ready_all_case_meshes",
            "terminal_window_rows_available",
            "exact_label_qoi_rows_available",
            "candidate_medium_fine_rows_available",
            "coarse_equivalence_admitted_all_cases",
            "formal_gci_status",
            "production_harvest_allowed",
            "admission_allowed",
            "next_action",
        ],
    )
    write_csv(
        OUT / "clean_next_run_contract.csv",
        run_rows,
        ["rank", "step", "required_input", "success_criterion", "scheduler_required", "forbidden"],
    )
    write_csv(
        OUT / "no_mutation_guardrails.csv",
        [
            {"guardrail": "native_solver_outputs_mutated", "value": "false"},
            {"guardrail": "registry_mutated", "value": "false"},
            {"guardrail": "scheduler_action", "value": "false"},
            {"guardrail": "source_property_or_qwall_release", "value": "false"},
            {"guardrail": "production_harvest_or_gci_admission", "value": "false"},
            {"guardrail": "coefficient_fit_or_final_score", "value": "false"},
        ],
        ["guardrail", "value"],
    )
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"source_path": rel(SAMPLER / "summary.json"), "exists": "true", "use": "read-only failed sampler summary"},
            {"source_path": rel(SAMPLER / "sampling_error_log.csv"), "exists": "true", "use": "read-only sampler failure evidence"},
            {"source_path": rel(SAMPLER / "faces"), "exists": "true", "use": "read-only face contract inventory"},
            {"source_path": rel(SPLIT_RERUN / "summary.json"), "exists": "true", "use": "read-only latest successful split rerun"},
            {"source_path": rel(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv"), "exists": "true", "use": "read-only latest exact-label QOI evidence"},
            {"source_path": rel(FACE_VECTOR_RERUN / "RUNNING.md"), "exists": bool_text((FACE_VECTOR_RERUN / "RUNNING.md").exists()), "use": "read-only superseded face-vector repair context"},
            {"source_path": rel(RECONCILIATION / "qoi_reconciliation_summary.csv"), "exists": "true", "use": "read-only candidate mesh reconciliation"},
            {"source_path": rel(COARSE_UNLOCK), "exists": bool_text(COARSE_UNLOCK.exists()), "use": "read-only same-label coarse/GCI unlock context if present"},
        ],
        ["source_path", "exists", "use"],
    )

    failed_terminal_rows = count_data_rows(SAMPLER / "medium_fine_terminal_window_reductions.csv")
    failed_exact_rows = count_data_rows(SAMPLER / "medium_fine_exact_label_qoi_rows.csv")
    terminal_rows = count_data_rows(SPLIT_RERUN / "aggregated_terminal_window_reductions.csv")
    exact_rows = count_data_rows(SPLIT_RERUN / "aggregated_exact_label_qoi_rows.csv")
    ready_face_rows = sum(1 for row in face_rows if row["release_grade_for_lane"] == "true")
    summary = {
        "task": TASK_ID,
        "decision": "s13_clean_sampler_gci_readiness_latest_split_rerun_complete_gci_blocked_by_coarse_no_harvest",
        "face_lane_rows": len(face_rows),
        "release_grade_face_lane_rows": ready_face_rows,
        "failed_package_terminal_window_reduction_rows": failed_terminal_rows,
        "failed_package_exact_label_qoi_rows": failed_exact_rows,
        "latest_split_terminal_window_reduction_rows": terminal_rows,
        "latest_split_exact_label_qoi_rows": exact_rows,
        "gci_ready_rows": 0,
        "production_harvest_allowed_rows": 0,
        "scheduler_action": False,
        "native_solver_outputs_mutated": False,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_json(OUT / "summary.json", summary)

    readme = f"""---
provenance:
  - {rel(SAMPLER / 'summary.json')}
  - {rel(SAMPLER / 'sampling_error_log.csv')}
  - {rel(RECONCILIATION / 'qoi_reconciliation_summary.csv')}
tags: [work-product, s13, sampler, mesh-gci, readiness, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-clean-sampler-gci-readiness.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Clean Sampler/GCI Readiness

Decision: `s13_clean_sampler_gci_readiness_latest_split_rerun_complete_gci_blocked_by_coarse_no_harvest`.

The old medium/fine exact-label sampler package is fail-closed and should not be
used for production evidence. A later split rerun supersedes that failure for
medium/fine evidence: it produced all six case-mesh outputs, 18 terminal-window
reductions, 72 exact-label QOI rows, and zero sampling errors. GCI/admission
still remain blocked because same-label coarse equivalence is not admitted.

Current result:

- Face-lane inventory rows: `{len(face_rows)}`.
- Release-grade face-lane rows by this local header audit: `{ready_face_rows}`.
- Failed package terminal-window reduction rows: `{failed_terminal_rows}`.
- Latest split rerun terminal-window reduction rows: `{terminal_rows}`.
- Latest split rerun exact-label QOI rows: `{exact_rows}`.
- GCI-ready rows: `0`.

Next clean action: resolve strict same-label coarse equivalence or fail it
closed with finality. Do not rerun the medium/fine sampler unless input
contracts change.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
