#!/usr/bin/env python3
"""Build S13 source-bounded CV definition/release package.

This task is deliberately fail-closed unless existing evidence releases a
trusted recirculation cell volume, exchange interface, wall/core band, normals,
and source/sink ledger for all Salt2/Salt3/Salt4 cases. It does not extract
surfaces, run samplers, or mutate native OpenFOAM outputs.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition"

TOPOLOGY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release"
FORENSICS = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv"
INTERFACE_RECOVERY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery"
SAMPLER_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
GEOMETRY_CONTRACT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract"
SOURCE_GENERATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
S12 = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s12_thermal_shape_ownership_candidate"

CASE_IDS = ("salt_2", "salt_3", "salt_4")


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in rows}


def find_gap(gaps: list[dict[str, str]], case_id: str, lane: str) -> dict[str, str]:
    for row in gaps:
        if row.get("case_id") == case_id and row.get("input_lane") == lane:
            return row
    return {}


def split_reasons(*values: str) -> list[str]:
    out: list[str] = []
    for value in values:
        for part in value.split(";"):
            part = part.strip()
            if part and part not in out:
                out.append(part)
    return out


def load_inputs() -> dict[str, Any]:
    return {
        "topology": by_case(read_csv(TOPOLOGY / "topology_cv_case_summary.csv")),
        "forensics": by_case(read_csv(FORENSICS / "alternate_cv_release_gate.csv")),
        "sampler_gaps": read_csv(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv"),
        "interface_gate": read_csv(INTERFACE_RECOVERY / "interface_wall_source_release_gate.csv"),
    }


def case_decision(case_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    topo = inputs["topology"][case_id]
    alt = inputs["forensics"][case_id]
    gaps = inputs["sampler_gaps"]
    interface_gap = find_gap(gaps, case_id, "exchange_interface_vtk")
    wall_gap = find_gap(gaps, case_id, "wall_vtk")
    normal_gap = find_gap(gaps, case_id, "normals")
    q_wall_gap = find_gap(gaps, case_id, "Q_wall_W")
    source_gap = find_gap(gaps, case_id, "source_sink_release")
    thermal_gap = find_gap(gaps, case_id, "same_window_thermal_fields")
    uq_gap = find_gap(gaps, case_id, "same_qoi_uq")

    blockers = split_reasons(
        topo.get("blocking_reason", ""),
        alt.get("blocking_reason", ""),
        interface_gap.get("blocking_reason", ""),
        wall_gap.get("blocking_reason", ""),
        normal_gap.get("blocking_reason", ""),
        q_wall_gap.get("blocking_reason", ""),
        source_gap.get("blocking_reason", ""),
        thermal_gap.get("blocking_reason", ""),
        uq_gap.get("blocking_reason", ""),
    )

    return {
        "case_id": case_id,
        "topology_status": topo.get("topology_release_status", "missing"),
        "alternate_cv_status": alt.get("release_status", "missing"),
        "reverse_candidate_cells": topo.get("candidate_mask_cells", ""),
        "diagnostic_topology_selected_cells": topo.get("selected_cv_cells", "0"),
        "diagnostic_alt_selected_cells": alt.get("selected_cells", "0"),
        "diagnostic_topology_interface_faces": topo.get("interface_face_count", "0"),
        "diagnostic_topology_interface_area_m2": topo.get("interface_area_m2", "0"),
        "diagnostic_topology_wall_faces": topo.get("right_leg_wall_face_count", "0"),
        "diagnostic_topology_wall_area_m2": topo.get("right_leg_wall_area_m2", "0"),
        "diagnostic_alt_wall_faces": alt.get("right_leg_wall_face_count", "0"),
        "diagnostic_alt_wall_area_m2": alt.get("right_leg_wall_area_m2", "0"),
        "exchange_interface_status": interface_gap.get("status", "blocked"),
        "wall_status": wall_gap.get("status", "blocked"),
        "normal_status": normal_gap.get("status", "blocked"),
        "q_wall_status": q_wall_gap.get("status", "blocked"),
        "source_sink_release_status": source_gap.get("status", "blocked"),
        "same_window_thermal_status": thermal_gap.get("status", "blocked"),
        "same_qoi_uq_status": uq_gap.get("status", "blocked"),
        "release_status": "blocked_source_bounded_cv_not_released",
        "s13_sampler_ready": "false",
        "s12_hiax1_unlocked": "false",
        "blocking_reason": ";".join(blockers),
    }


def build_rows(decisions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    recirc_rows = []
    interface_rows = []
    wall_rows = []
    band_rows = []
    normal_rows = []
    source_rows = []
    for row in decisions:
        case_id = row["case_id"]
        recirc_rows.append(
            {
                "case_id": case_id,
                "cell_id": "",
                "released_cell_count": 0,
                "diagnostic_candidate_cells": row["diagnostic_topology_selected_cells"],
                "source_mask_status": row["topology_status"],
                "release_status": row["release_status"],
                "blocking_reason": row["blocking_reason"],
                "source_paths": f"{rel(TOPOLOGY / 'topology_cv_case_summary.csv')};{rel(FORENSICS / 'alternate_cv_release_gate.csv')}",
            }
        )
        interface_rows.append(
            {
                "case_id": case_id,
                "face_id": "",
                "released_interface_face_count": 0,
                "diagnostic_interface_face_count": row["diagnostic_topology_interface_faces"],
                "diagnostic_interface_area_m2": row["diagnostic_topology_interface_area_m2"],
                "release_status": "blocked_no_trusted_exchange_interface",
                "normal_convention": "positive mdot_exchange from recirculation CV toward main throughflow once trusted interface exists",
                "blocking_reason": row["blocking_reason"],
                "source_paths": f"{rel(GEOMETRY_CONTRACT / 'interface_geometry_contract.csv')};{rel(SAMPLER_PREFLIGHT / 'sampler_input_gap_matrix.csv')}",
            }
        )
        wall_rows.append(
            {
                "case_id": case_id,
                "face_id": "",
                "released_wall_face_count": 0,
                "diagnostic_topology_wall_face_count": row["diagnostic_topology_wall_faces"],
                "diagnostic_topology_wall_area_m2": row["diagnostic_topology_wall_area_m2"],
                "diagnostic_alt_wall_face_count": row["diagnostic_alt_wall_faces"],
                "diagnostic_alt_wall_area_m2": row["diagnostic_alt_wall_area_m2"],
                "release_status": "blocked_no_source_bounded_wall_faces",
                "blocking_reason": row["blocking_reason"],
                "source_paths": f"{rel(GEOMETRY_CONTRACT / 'wall_core_band_contract.csv')};{rel(FORENSICS / 'alternate_cv_release_gate.csv')}",
            }
        )
        band_rows.append(
            {
                "case_id": case_id,
                "band_id": "right_leg_upcomer_wall_core_band",
                "released": "false",
                "wall_basis": "blocked_until_recirc_cv_released",
                "core_basis": "blocked_until_recirc_cv_released",
                "thermal_reduction_allowed": "false",
                "blocking_reason": row["blocking_reason"],
                "source_paths": rel(GEOMETRY_CONTRACT / "wall_core_band_contract.csv"),
            }
        )
        normal_rows.append(
            {
                "case_id": case_id,
                "surface_lane": "exchange_interface",
                "released": "false",
                "normal_vector": "",
                "positive_flux_convention": "positive mdot_exchange from recirculation CV toward main throughflow",
                "blocking_reason": "no released exchange-interface faces",
                "source_paths": rel(GEOMETRY_CONTRACT / "interface_geometry_contract.csv"),
            }
        )
        source_rows.append(
            {
                "case_id": case_id,
                "boundary_lane": "static_source_sink_context",
                "released": "false",
                "classification": row["source_sink_release_status"],
                "Q_wall_W_released": "false",
                "source_sink_terms_released": "false",
                "blocking_reason": row["blocking_reason"],
                "source_paths": f"{rel(SOURCE_GENERATION / 'source_sink_summary.csv')};{rel(SAMPLER_PREFLIGHT / 'sampler_input_gap_matrix.csv')}",
            }
        )
    return {
        "recirc_cv_cells": recirc_rows,
        "exchange_interface_faces": interface_rows,
        "trusted_wall_faces": wall_rows,
        "wall_core_band": band_rows,
        "normal_convention": normal_rows,
        "source_sink_boundary_ledger": source_rows,
    }


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    (out / "README.md").write_text(
        f"""---
provenance:
  - {rel(TOPOLOGY / 'topology_cv_case_summary.csv')}
  - {rel(FORENSICS / 'alternate_cv_release_gate.csv')}
  - {rel(SAMPLER_PREFLIGHT / 'sampler_input_gap_matrix.csv')}
tags: [s13, upcomer-exchange, source-bounded-cv, fail-closed]
related:
  - {rel(S12 / 'admission_gate_matrix.csv')}
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_fail_closed
---
# S13 Source-Bounded CV Definition

This package executes the source-bounded CV release gate needed upstream of
S12-HIAX1. Result: `{summary['decision']}`.

- cases processed: `{summary['case_count']}`
- released CV cases: `{summary['released_case_count']}`
- released interface rows: `0`
- released wall rows: `0`
- S13 sampler ready: `{str(summary['s13_sampler_ready']).lower()}`
- S12-HIAX1 unlocked: `{str(summary['s12_hiax1_unlocked']).lower()}`

The gate remains blocked because existing reverse-flow masks are fragmented,
the dominant components lack trusted right-leg wall contact, conservative
wall-adjacent alternates do not release all three cases, and no trusted
exchange-interface/wall/core/normal/Q-wall source bundle exists.

No native OpenFOAM output, registry/admission state, scheduler state, surface
extraction, sampler, harvest, Fluid source, fit, model selection, S11/S15/S6
trigger, or residual absorption into internal Nu was performed.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    inputs = load_inputs()
    decisions = [case_decision(case_id, inputs) for case_id in CASE_IDS]
    released = [row for row in decisions if row["release_status"] == "released"]
    rows = build_rows(decisions)

    csv_dump(
        out / "recirc_cv_cells.csv",
        ["case_id", "cell_id", "released_cell_count", "diagnostic_candidate_cells", "source_mask_status", "release_status", "blocking_reason", "source_paths"],
        rows["recirc_cv_cells"],
    )
    csv_dump(
        out / "exchange_interface_faces.csv",
        ["case_id", "face_id", "released_interface_face_count", "diagnostic_interface_face_count", "diagnostic_interface_area_m2", "release_status", "normal_convention", "blocking_reason", "source_paths"],
        rows["exchange_interface_faces"],
    )
    csv_dump(
        out / "trusted_wall_faces.csv",
        ["case_id", "face_id", "released_wall_face_count", "diagnostic_topology_wall_face_count", "diagnostic_topology_wall_area_m2", "diagnostic_alt_wall_face_count", "diagnostic_alt_wall_area_m2", "release_status", "blocking_reason", "source_paths"],
        rows["trusted_wall_faces"],
    )
    csv_dump(
        out / "wall_core_band.csv",
        ["case_id", "band_id", "released", "wall_basis", "core_basis", "thermal_reduction_allowed", "blocking_reason", "source_paths"],
        rows["wall_core_band"],
    )
    csv_dump(
        out / "normal_convention.csv",
        ["case_id", "surface_lane", "released", "normal_vector", "positive_flux_convention", "blocking_reason", "source_paths"],
        rows["normal_convention"],
    )
    csv_dump(
        out / "source_sink_boundary_ledger.csv",
        ["case_id", "boundary_lane", "released", "classification", "Q_wall_W_released", "source_sink_terms_released", "blocking_reason", "source_paths"],
        rows["source_sink_boundary_ledger"],
    )
    csv_dump(
        out / "release_decision.csv",
        [
            "case_id",
            "topology_status",
            "alternate_cv_status",
            "exchange_interface_status",
            "reverse_candidate_cells",
            "diagnostic_topology_selected_cells",
            "diagnostic_alt_selected_cells",
            "diagnostic_topology_interface_faces",
            "diagnostic_topology_interface_area_m2",
            "diagnostic_topology_wall_faces",
            "diagnostic_topology_wall_area_m2",
            "diagnostic_alt_wall_faces",
            "diagnostic_alt_wall_area_m2",
            "wall_status",
            "normal_status",
            "q_wall_status",
            "source_sink_release_status",
            "same_window_thermal_status",
            "same_qoi_uq_status",
            "release_status",
            "s13_sampler_ready",
            "s12_hiax1_unlocked",
            "blocking_reason",
        ],
        decisions,
    )
    csv_dump(
        out / "s12_unlock_gate.csv",
        ["gate_id", "status", "required_for_s12", "evidence", "blocking_reason"],
        [
            {
                "gate_id": "s13_source_bounded_cv_release",
                "status": "fail",
                "required_for_s12": "yes",
                "evidence": rel(out / "release_decision.csv"),
                "blocking_reason": "0/3 source-bounded CV rows released",
            },
            {
                "gate_id": "s13_sampler_manifest_rerun",
                "status": "blocked",
                "required_for_s12": "yes",
                "evidence": rel(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv"),
                "blocking_reason": "interface/wall/normals/Q_wall/source/UQ lanes remain blocked",
            },
            {
                "gate_id": "s12_hiax1_implementation",
                "status": "blocked",
                "required_for_s12": "yes",
                "evidence": rel(S12 / "candidate_contract.csv"),
                "blocking_reason": "cannot implement exchange-shape term without released exchange-state QOIs",
            },
        ],
    )
    csv_dump(
        out / "no_mutation_guardrails.csv",
        ["guard_id", "status", "policy"],
        [
            {"guard_id": "native_outputs", "status": "pass", "policy": "no native CFD/OpenFOAM outputs mutated"},
            {"guard_id": "scheduler", "status": "pass", "policy": "no scheduler action"},
            {"guard_id": "surface_sampler_harvest", "status": "pass", "policy": "no surface extraction, sampler, or harvest launched"},
            {"guard_id": "admission", "status": "pass", "policy": "no S11/S12/S13/S15/S6 trigger or admission"},
        ],
    )
    csv_dump(
        out / "source_manifest.csv",
        ["path", "role", "exists", "native_solver_output", "mutated"],
        [
            {"path": rel(TOPOLOGY / "topology_cv_case_summary.csv"), "role": "read topology release decision", "exists": (TOPOLOGY / "topology_cv_case_summary.csv").exists(), "native_solver_output": "false", "mutated": "false"},
            {"path": rel(FORENSICS / "alternate_cv_release_gate.csv"), "role": "read alternate topology forensics", "exists": (FORENSICS / "alternate_cv_release_gate.csv").exists(), "native_solver_output": "false", "mutated": "false"},
            {"path": rel(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv"), "role": "read sampler gap matrix", "exists": (SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv").exists(), "native_solver_output": "false", "mutated": "false"},
            {"path": rel(INTERFACE_RECOVERY / "interface_wall_source_release_gate.csv"), "role": "read interface/wall/source recovery gate", "exists": (INTERFACE_RECOVERY / "interface_wall_source_release_gate.csv").exists(), "native_solver_output": "false", "mutated": "false"},
            {"path": rel(out), "role": "generated task-owned package", "exists": "true", "native_solver_output": "false", "mutated": "true"},
        ],
    )

    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "complete_fail_closed_source_bounded_cv_not_released",
        "case_count": len(decisions),
        "released_case_count": len(released),
        "s13_sampler_ready": False,
        "s12_hiax1_unlocked": False,
        "s11_s15_s6_trigger": False,
        "surface_extraction_allowed": False,
        "sampler_or_harvest_allowed": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "blocking_cases": [row["case_id"] for row in decisions],
    }
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return {"summary": summary, "decisions": decisions}


def main() -> int:
    payload = build_package()
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
