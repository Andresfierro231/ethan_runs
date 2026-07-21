#!/usr/bin/env python3
"""Build a same-QOI neighboring-window preflight package without launching compute."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-SAME-QOI-NEIGHBOR-WINDOW-PREFLIGHT-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_same_qoi_neighbor_window_preflight"
PHASE_A = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_a_retained_window_inventory"
PHASE_B = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix"
PHASE_C = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_c_admission_table"

PREFLIGHT_FIELDS = [
    "qoi_family",
    "qoi_name",
    "retained_window_status",
    "neighbor_window_status",
    "mesh_gci_status",
    "source_gate_status",
    "preflight_classification",
    "accepted_after_preflight",
    "compute_needed",
    "compute_priority",
    "next_task",
    "source_paths",
]
QUEUE_FIELDS = [
    "priority",
    "qoi_family",
    "qoi_name",
    "work_type",
    "entry_condition",
    "forbidden_action",
    "source_paths",
]
GUARD_FIELDS = ["guard_id", "status", "policy"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def by_qoi(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["qoi_name"]: row for row in rows}


def priority_for(row: dict[str, str]) -> str:
    family = row["qoi_family"]
    name = row["qoi_name"]
    if family == "pressure" and "F6_endpoint_face_raw" in name:
        return "P1_raw_face_sampler"
    if family == "pressure":
        return "P1_existing_artifact_then_sampler"
    if name in {"V_recirc_mdot_exchange_tau_recirc", "upcomer_exchange_heat_loss_fields"}:
        return "P2_after_cell_vtk_and_exchange_geometry"
    if family == "recirculation":
        return "P2_terminal_or_exchange_harvest_gated"
    if family == "thermal":
        return "P3_policy_and_sign_resolution_first"
    if family == "heat_loss":
        return "P3_runtime_candidate_or_freeze_gate_first"
    return "P4_rollup_after_component_rows"


def work_type_for(priority: str) -> str:
    if priority.startswith("P1"):
        return "neighbor_window_existing_artifact_search_then_sampler_queue"
    if priority.startswith("P2"):
        return "exchange_or_terminal_harvest_input_generation"
    if priority.startswith("P3"):
        return "source_policy_candidate_definition_before_same_qoi_compute"
    return "cross_family_rollup_after_component_evidence"


def preflight_rows() -> list[dict[str, Any]]:
    phase_a = by_qoi(read_csv(PHASE_A / "qoi_retained_window_inventory.csv"))
    phase_b = by_qoi(read_csv(PHASE_B / "mesh_gci_coverage_matrix.csv"))
    phase_c_rows = read_csv(PHASE_C / "same_qoi_uq_admission_table.csv")
    rows: list[dict[str, Any]] = []
    for row in phase_c_rows:
        qoi = row["qoi_name"]
        a = phase_a.get(qoi, {})
        b = phase_b.get(qoi, {})
        neighbor = row["time_window_gate"]
        mesh = row["mesh_gci_gate"]
        source = row["source_gate"]
        accepted = neighbor == "accepted" and mesh == "accepted" and source == "accepted"
        priority = priority_for(row)
        if accepted:
            classification = "accepted_existing_evidence"
            compute_needed = "false"
        elif "blocked_missing_neighbor_window" in neighbor:
            classification = "blocked_missing_neighbor_window"
            compute_needed = "true"
        elif mesh != "accepted":
            classification = "blocked_missing_same_qoi_mesh_gci"
            compute_needed = "true"
        else:
            classification = "blocked_source_gate"
            compute_needed = "false"
        rows.append(
            {
                "qoi_family": row["qoi_family"],
                "qoi_name": qoi,
                "retained_window_status": a.get("retained_time_source", ""),
                "neighbor_window_status": a.get("neighbor_window_status", neighbor),
                "mesh_gci_status": b.get("mesh_gci_status_summary", mesh),
                "source_gate_status": source,
                "preflight_classification": classification,
                "accepted_after_preflight": str(accepted).lower(),
                "compute_needed": compute_needed,
                "compute_priority": priority,
                "next_task": row["next_task"],
                "source_paths": row["source_paths"],
            }
        )
    return rows


def compute_queue_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queued: list[dict[str, Any]] = []
    order = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
    for row in rows:
        priority = str(row["compute_priority"])
        if row["accepted_after_preflight"] == "true":
            continue
        prefix = priority.split("_", 1)[0]
        queued.append(
            {
                "priority": order.get(prefix, 9),
                "qoi_family": row["qoi_family"],
                "qoi_name": row["qoi_name"],
                "work_type": work_type_for(priority),
                "entry_condition": row["next_task"],
                "forbidden_action": "do not admit, fit, score, invent GCI, or mix QOI bases from this preflight row",
                "source_paths": row["source_paths"],
            }
        )
    return sorted(queued, key=lambda item: (int(item["priority"]), item["qoi_family"], item["qoi_name"]))


def guard_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_outputs", "status": "read_only", "policy": "no CFD/OpenFOAM output mutation or sampling launch"},
        {"guard_id": "admission", "status": "blocked", "policy": "accepted requires neighboring-window evidence plus same-QOI mesh/GCI plus source readiness"},
        {"guard_id": "mesh_gci", "status": "no_invention", "policy": "carry existing mesh/GCI status only; do not infer a GCI from unrelated rows"},
        {"guard_id": "basis", "status": "same_qoi_only", "policy": "do not promote mixed label/formula/sign or proxy rows"},
    ]


def manifest_rows(output_dir: Path) -> list[dict[str, Any]]:
    paths = [
        Path("tools/analyze/build_same_qoi_neighbor_window_preflight.py"),
        Path("tools/analyze/test_same_qoi_neighbor_window_preflight.py"),
        PHASE_A,
        PHASE_B,
        PHASE_C,
        output_dir,
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        relative = rel(full)
        task_output = full == output_dir or relative.startswith("tools/analyze/build_same_qoi_neighbor_window_preflight") or relative.startswith("tools/analyze/test_same_qoi_neighbor_window_preflight")
        rows.append(
            {
                "path": relative,
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": "false",
                "mutated": str(task_output).lower(),
            }
        )
    return rows


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: cfd-pp / Mesh-GCI / Tester / Writer
type: work_product
status: complete
tags: [same-qoi-uq, neighboring-window, mesh-gci, no-admission]
related:
  - {rel(PHASE_A)}
  - {rel(PHASE_B)}
  - {rel(PHASE_C)}
---
# Same-QOI Neighboring-Window Preflight

This package converts the Phase C same-QOI admission table into an executable
next-task queue. It does not search native case directories, launch samplers,
compute drift, invent GCI, or change admission state.

## Results

- QOI rows reviewed: `{summary["qoi_rows"]}`
- accepted after preflight: `{summary["accepted_rows"]}`
- compute-needed rows: `{summary["compute_needed_rows"]}`
- P1 pressure/F6 rows: `{summary["p1_rows"]}`
- P2 recirculation/upcomer rows: `{summary["p2_rows"]}`
- scheduler action: `false`
- admission change: `false`

## Outputs

- `neighbor_window_preflight.csv`
- `compute_needed_queue.csv`
- `admission_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Thesis-Safe Claim

No same-QOI uncertainty row is admitted. The next useful work is to handle P1
pressure/F6 rows first, then exchange/terminal-harvest rows after their inputs
exist. Thermal and heat-loss candidate rows remain policy/candidate gated.
"""


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    rows = preflight_rows()
    queue = compute_queue_rows(rows)
    guards = guard_rows()
    manifest = manifest_rows(output_dir)
    csv_dump(output_dir / "neighbor_window_preflight.csv", PREFLIGHT_FIELDS, rows)
    csv_dump(output_dir / "compute_needed_queue.csv", QUEUE_FIELDS, queue)
    csv_dump(output_dir / "admission_guardrails.csv", GUARD_FIELDS, guards)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "complete",
        "qoi_rows": len(rows),
        "accepted_rows": sum(1 for row in rows if row["accepted_after_preflight"] == "true"),
        "compute_needed_rows": sum(1 for row in rows if row["compute_needed"] == "true"),
        "p1_rows": sum(1 for row in rows if str(row["compute_priority"]).startswith("P1")),
        "p2_rows": sum(1 for row in rows if str(row["compute_priority"]).startswith("P2")),
        "native_output_mutation": False,
        "scheduler_action": False,
        "solver_or_postprocessing_or_sampler_launch": False,
        "registry_or_admission_mutation": False,
        "fitting_or_model_selection": False,
        "same_qoi_or_coefficient_admission": False,
        "invented_gci": False,
        "mixed_basis_promotion": False,
        "generated_index_refresh": False,
    }
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    return {"summary": summary, "rows": rows, "queue": queue}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(PACKAGE_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(Path(args.output_dir))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
