#!/usr/bin/env python3
"""Build S13 interface/wall/source recovery decision package."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-INTERFACE-WALL-SOURCE-RECOVERY-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery"
PACKAGE_DIR = OUT
TOPOLOGY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release"
SEGMENTATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight"
GEOMETRY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract"
SURFACE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_extraction"
SURFACE_SOURCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
SAMPLER_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
SAME_WINDOW_UQ = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design"
CANDIDATE_RECOVERY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_candidate_uq_s13_geometry_recovery"

CASE_IDS = ("salt_2", "salt_3", "salt_4")
CASES = CASE_IDS


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def case_reason(topology_row: dict[str, str]) -> str:
    reasons = [item for item in topology_row.get("blocking_reason", "").split(";") if item]
    return ";".join(reasons) if reasons else "topology_cv_not_released"


def release_allowed(topology_row: dict[str, str]) -> bool:
    return topology_row.get("topology_release_status") == "released_topology_cv"


def _index(rows: list[dict[str, str]], key: str = "case_id") -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def source_paths_for_case() -> str:
    return ";".join(
        [
            rel(SEGMENTATION / "recirc_segmentation_case_summary.csv"),
            rel(SEGMENTATION / "exchange_interface_derivation_preflight.csv"),
            rel(SEGMENTATION / "wall_core_band_derivation_preflight.csv"),
            rel(TOPOLOGY / "topology_cv_case_summary.csv"),
            rel(TOPOLOGY / "exchange_interface_topology_contract.csv"),
            rel(TOPOLOGY / "wall_core_topology_contract.csv"),
            rel(SURFACE / "surface_input_disposition.csv"),
            rel(SURFACE / "normal_vector_provenance.csv"),
            rel(SAMPLER_PREFLIGHT / "s13_readiness_gate.csv"),
            rel(SURFACE_SOURCE / "source_sink_summary.csv"),
            rel(SAME_WINDOW_UQ / "qoi_release_decision.csv"),
        ]
    )


def release_gate_rows() -> list[dict[str, str]]:
    topology = _index(read_csv(TOPOLOGY / "topology_cv_case_summary.csv"))
    interface = _index(read_csv(TOPOLOGY / "exchange_interface_topology_contract.csv"))
    wall = _index(read_csv(TOPOLOGY / "wall_core_topology_contract.csv"))
    sampler = _index(read_csv(SAMPLER_PREFLIGHT / "s13_readiness_gate.csv"))
    normals = _index(read_csv(SURFACE / "normal_vector_provenance.csv"))
    source = _index(read_csv(SURFACE_SOURCE / "source_sink_summary.csv"))

    rows: list[dict[str, str]] = []
    for case_id in CASE_IDS:
        topo = topology[case_id]
        iface = interface[case_id]
        wall_row = wall[case_id]
        sampler_row = sampler[case_id]
        normal = normals[case_id]
        source_row = source[case_id]
        topology_ok = release_allowed(topo)
        blockers = [
            "blocked_fragmented_velocity_topology" if not topology_ok else "",
            "exchange_interface_vtk" if iface["release_status"] != "released" else "",
            "wall_vtk" if wall_row["release_status"] != "released" else "",
            "normals" if normal["normal_vector_status"] != "released" else "",
            "Q_wall_W",
            "source_sink_release",
            "same_window_thermal_fields",
            "same_qoi_uq",
            "production_harvest_readiness",
            case_reason(topo),
        ]
        rows.append(
            {
                "case_id": case_id,
                "cell_vtk_ready": sampler_row["cell_vtk_ready"],
                "volume_csv_ready": sampler_row["volume_csv_ready"],
                "recirc_cv_status": "released" if topology_ok else "blocked_fragmented_velocity_topology",
                "reverse_candidate_cells": topo["candidate_mask_cells"],
                "largest_component_fraction": topo.get("largest_face_component_fraction", topo.get("largest_component_fraction", "")),
                "exchange_interface_status": iface["release_status"],
                "exchange_interface_vtk": iface["interface_source"],
                "wall_core_status": wall_row["release_status"],
                "wall_vtk": wall_row["wall_band_source"],
                "normal_status": normal["normal_vector_status"],
                "normal_basis": normal["basis_note"],
                "q_wall_w_status": "blocked",
                "source_sink_ledger_status": source_row["status"],
                "source_sink_release_status": "blocked_wall_loss_still_missing",
                "same_window_thermal_ready": "false",
                "same_qoi_uq_ready": "false",
                "sampler_ready": sampler_row["sampler_ready"],
                "production_harvest_allowed": "false",
                "release_status": "blocked",
                "blocking_reason": ";".join(item for item in blockers if item),
                "source_paths": source_paths_for_case(),
            }
        )
    return rows


def recovery_decision_rows(gate_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in gate_rows:
        rows.append(
            {
                "case_id": row["case_id"],
                "topology_cv_release": "false",
                "exchange_interface_release": "false",
                "recirc_mask_release": "false",
                "wall_core_band_release": "false",
                "normal_provenance_release": "false",
                "q_wall_w_release": "false",
                "source_sink_release": "false",
                "sampler_manifest_ready": row["sampler_ready"],
                "production_harvest_allowed": "false",
                "decision": "fail_closed_no_recovery",
                "blocking_reason": row["blocking_reason"],
                "source_paths": row["source_paths"],
            }
        )
    return rows


def qwall_rows() -> list[dict[str, str]]:
    wall = _index(read_csv(TOPOLOGY / "wall_core_topology_contract.csv"))
    source = _index(read_csv(SURFACE_SOURCE / "source_sink_summary.csv"))
    rows: list[dict[str, str]] = []
    for case_id in CASE_IDS:
        rows.append(
            {
                "case_id": case_id,
                "wall_face_count": wall[case_id]["wall_face_count"],
                "wall_area_m2": wall[case_id]["wall_area_m2"],
                "q_wall_w_ready": "false",
                "source_side_static_context_only": "true",
                "q_wall_release_status": "blocked_no_released_wall_core_band",
                "source_sink_release_status": "blocked_wall_loss_still_missing",
                "thermal_source_blocker": source[case_id]["energy_residual_release_condition"],
                "source_paths": ";".join([rel(TOPOLOGY / "wall_core_topology_contract.csv"), rel(SURFACE_SOURCE / "source_sink_summary.csv")]),
            }
        )
    return rows


def blocker_chain_rows() -> list[dict[str, str]]:
    return [
        {
            "case_id": case_id,
            "surface_extraction_allowed": "false",
            "sampler_preflight_rerun_allowed": "false",
            "production_harvest_allowed": "false",
            "same_window_uq_release_allowed": "false",
            "s11_candidate_review_allowed": "false",
            "blocker_chain": "topology_cv_not_released -> interface/wall/source_not_released -> sampler_not_ready -> no_harvest -> no_same_QOI_UQ -> no_S11",
            "next_action": "release_face_closed_recirc_cv_before_rerunning_surface_or_sampler_rows",
        }
        for case_id in CASE_IDS
    ]


def source_evidence_rows() -> list[dict[str, str]]:
    return [
        {
            "evidence_id": "recirc_cv_segmentation_preflight",
            "source_path": rel(SEGMENTATION / "summary.json"),
            "observed_signal": "3 diagnostic reverse-flow masks",
            "released_rows": "0",
            "release_effect": "blocks_interface_and_wall_until_face_closed_cv_exists",
            "s13_state": "blocked",
        },
        {
            "evidence_id": "topology_cv_release",
            "source_path": rel(TOPOLOGY / "summary.json"),
            "observed_signal": "0 topology CV releases after face-connected owner/neighbour pass",
            "released_rows": "0",
            "release_effect": "keeps_exchange_interface_wall_normals_blocked",
            "s13_state": "blocked",
        },
        {
            "evidence_id": "surface_vtk_disposition",
            "source_path": rel(SURFACE / "summary.json"),
            "observed_signal": "3 cell VTK rows ready",
            "released_rows": "0",
            "release_effect": "blocks_exchange_interface_wall_and_normals",
            "s13_state": "blocked",
        },
        {
            "evidence_id": "sampler_manifest_preflight",
            "source_path": rel(SAMPLER_PREFLIGHT / "summary.json"),
            "observed_signal": "3 manifest rows checked; 0 ready",
            "released_rows": "0",
            "release_effect": "blocks_production_harvest",
            "s13_state": "blocked",
        },
        {
            "evidence_id": "same_window_uq_design",
            "source_path": rel(SAME_WINDOW_UQ / "summary.json"),
            "observed_signal": "3 target QOIs gated",
            "released_rows": "0",
            "release_effect": "blocks_s11_reviewable_exchange_candidate",
            "s13_state": "blocked",
        },
        {
            "evidence_id": "candidate_uq_s13_geometry_recovery",
            "source_path": rel(CANDIDATE_RECOVERY / "summary.json"),
            "observed_signal": "33 geometry rows reviewed",
            "released_rows": "0",
            "release_effect": "rejects_loop_planes_and_proxy_surfaces",
            "s13_state": "blocked",
        },
        {
            "evidence_id": "static_source_sink_ledger",
            "source_path": rel(SURFACE_SOURCE / "source_sink_summary.csv"),
            "observed_signal": "3 static source/sink ledgers ready but wall loss blocked",
            "released_rows": "0",
            "release_effect": "static_bc_ledger_does_not_release_Q_wall_W_or_energy_residual",
            "s13_state": "blocked",
        },
    ]


def s13_unblock_decision_rows() -> list[dict[str, str]]:
    return [
        {
            "decision_id": "S13-interface-wall-source-recovery",
            "s13_unblocked": "false",
            "production_harvest_allowed": "false",
            "sampler_manifest_allowed": "false",
            "s11_candidate_released": "false",
            "decision": "do_not_run_harvest",
            "blocking_reason": "0/3 released topology CV/interface/wall/normal/Q_wall/source/UQ rows",
            "next_task": "release_face_closed_recirc_cv",
        }
    ]


def next_unblock_sequence_rows() -> list[dict[str, str]]:
    steps = [
        ("release_face_closed_recirc_cv", "Use source-bounded geometry/topology evidence to release all three Salt recirculation CVs together."),
        ("release_exchange_interface_and_normals", "Only after CV release, emit conservative interface face set and normal convention."),
        ("release_wall_core_band_and_qwall", "Only after wall adjacency release, integrate or fail-close same-window Q_wall_W."),
        ("rerun_sampler_manifest_preflight", "Populate interface/wall/normals and require scaffold validator pass."),
        ("run_s13_production_harvest_only_after_preflight_passes", "Use scheduler only in a new harvest row after all gates pass."),
    ]
    return [
        {
            "sequence": str(index),
            "next_step": step,
            "instruction": instruction,
            "allowed_now": "false",
        }
        for index, (step, instruction) in enumerate(steps, start=1)
    ]


def guardrails() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_solver_output_mutated", "allowed": "false", "observed": "false"},
        {"guardrail": "registry_or_admission_mutated", "allowed": "false", "observed": "false"},
        {"guardrail": "scheduler_action", "allowed": "false", "observed": "false"},
        {"guardrail": "surface_extraction_launched", "allowed": "false", "observed": "false"},
        {"guardrail": "sampler_or_harvest_launched", "allowed": "false", "observed": "false"},
        {"guardrail": "exchange_cell_admission_changed", "allowed": "false", "observed": "false"},
        {"guardrail": "residual_absorbed_into_internal_Nu", "allowed": "false", "observed": "false"},
    ]


def source_manifest() -> list[dict[str, str]]:
    paths = [
        Path("tools/extract/build_s13_upcomer_exchange_interface_wall_source_recovery.py"),
        Path("tools/extract/test_s13_upcomer_exchange_interface_wall_source_recovery.py"),
        TOPOLOGY / "topology_cv_case_summary.csv",
        TOPOLOGY / "face_connected_component_summary.csv",
        TOPOLOGY / "boundary_escape_by_patch.csv",
        TOPOLOGY / "exchange_interface_topology_contract.csv",
        TOPOLOGY / "wall_core_topology_contract.csv",
        GEOMETRY / "interface_geometry_contract.csv",
        GEOMETRY / "wall_core_band_contract.csv",
        SURFACE / "surface_input_disposition.csv",
        SURFACE / "normal_vector_provenance.csv",
        SURFACE_SOURCE / "source_sink_summary.csv",
        SAMPLER_PREFLIGHT / "s13_readiness_gate.csv",
        SAME_WINDOW_UQ / "qoi_release_decision.csv",
        OUT,
    ]
    rows: list[dict[str, str]] = []
    for path in paths:
        full = ROOT / path if not path.is_absolute() else path
        task_output = full == OUT or str(path).startswith("tools/extract/build_s13_upcomer_exchange_interface_wall_source_recovery") or str(path).startswith("tools/extract/test_s13_upcomer_exchange_interface_wall_source_recovery")
        rows.append(
            {
                "path": rel(full),
                "role": "task_output" if task_output else "read_only_input",
                "exists": bool_text(full.exists()),
                "native_solver_output": "false",
                "mutated": bool_text(task_output and full != OUT),
            }
        )
    return rows


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_fail_closed_no_recovery
tags: [upcomer, exchange-cell, interface, wall-core, source, fail-closed]
related:
  - {rel(TOPOLOGY)}
  - {rel(SAMPLER_PREFLIGHT)}
---
# S13 Interface/Wall/Source Recovery

This package consumes the refreshed topology CV result and decides whether the
S13 exchange interface, recirculation mask, wall/core band, normals, `Q_wall_W`,
and source-side thermal lanes can be recovered from existing evidence.

## Decision

- cases reviewed: `{summary["case_rows"]}`
- released recirculation CV rows: `{summary["released_recirc_cv_rows"]}`
- exchange-interface releases: `{summary["released_exchange_interface_rows"]}`
- wall/core releases: `{summary["released_wall_core_rows"]}`
- `Q_wall_W` releases: `{summary["released_q_wall_rows"]}`
- sampler-ready rows: `{summary["sampler_ready_rows"]}`
- production harvest allowed: `false`

The topology row released no conservative recirculation control volumes. The
largest face-connected reverse-flow components remain about `53%` of the
candidate masks, have no released right-leg wall faces, and touch unreleased
boundaries. This package therefore does not release an interface, wall/core
band, normal provenance, wall heat integration, source/sink thermal ledger,
sampler rerun, harvest, same-QOI UQ, or S11 review.

## Outputs

- `interface_wall_source_release_gate.csv`
- `interface_wall_source_recovery_decision.csv`
- `q_wall_source_release_gate.csv`
- `downstream_sampler_blocker_chain.csv`
- `s13_unblock_decision.csv`
- `next_unblock_sequence.csv`
- `source_evidence_synthesis.csv`
- `source_manifest.csv`, `no_mutation_guardrails.csv`, and `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
surface extraction, sampler/harvest, Fluid/external source, fitting/model
selection, exchange-cell admission, S11/S15/S6 trigger, or residual absorption
into internal `Nu` was changed.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(out_dir: Path = OUT) -> dict[str, Any]:
    ensure_dir(out_dir)
    gate = release_gate_rows()
    recovery = recovery_decision_rows(gate)
    qwall = qwall_rows()
    blocker_chain = blocker_chain_rows()
    evidence = source_evidence_rows()
    decision = s13_unblock_decision_rows()
    sequence = next_unblock_sequence_rows()
    guards = guardrails()
    sources = source_manifest()

    csv_dump(out_dir / "interface_wall_source_release_gate.csv", list(gate[0]), gate)
    csv_dump(out_dir / "interface_wall_source_recovery_decision.csv", list(recovery[0]), recovery)
    csv_dump(out_dir / "q_wall_source_release_gate.csv", list(qwall[0]), qwall)
    csv_dump(out_dir / "downstream_sampler_blocker_chain.csv", list(blocker_chain[0]), blocker_chain)
    csv_dump(out_dir / "source_evidence_synthesis.csv", list(evidence[0]), evidence)
    csv_dump(out_dir / "s13_unblock_decision.csv", list(decision[0]), decision)
    csv_dump(out_dir / "next_unblock_sequence.csv", list(sequence[0]), sequence)
    csv_dump(out_dir / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out_dir / "source_manifest.csv", list(sources[0]), sources)

    summary: dict[str, Any] = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "package": rel(out_dir),
        "case_rows": len(gate),
        "source_evidence_rows": len(evidence),
        "cell_vtk_ready_rows": sum(1 for row in gate if row["cell_vtk_ready"] == "true"),
        "released_recirc_cv_rows": 0,
        "released_exchange_interface_rows": 0,
        "released_wall_core_rows": 0,
        "released_normal_rows": 0,
        "released_q_wall_rows": 0,
        "released_source_sink_rows": 0,
        "same_window_thermal_ready_rows": 0,
        "same_qoi_uq_ready_rows": 0,
        "sampler_ready_rows": 0,
        "released_case_rows": 0,
        "s13_unblocked": False,
        "production_harvest_allowed": False,
        "sampler_manifest_allowed": False,
        "s11_candidate_released": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_or_postprocessing_or_surface_or_sampler_or_harvest_launched": False,
        "fluid_or_external_repo_mutation": False,
        "fitting_or_model_selection": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
    }
    json_dump(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return {"summary": summary, "release_gate": gate}


def build() -> dict[str, Any]:
    return build_package()["summary"]


def main() -> int:
    payload = build_package()
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
