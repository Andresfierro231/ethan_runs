#!/usr/bin/env python3
"""Build the upcomer exchange geometry-release package."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-UPCOMER-EXCHANGE-GEOMETRY-RELEASE-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release"
SOURCE_AUDIT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit"
SURFACE_SOURCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
INPUT_GENERATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation"
HARVEST_SCAFFOLD = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold"
MESH_CENTERLINES = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"

GEOMETRY_FIELDS = [
    "geometry_lane",
    "decision",
    "basis",
    "release_condition",
    "next_work_package",
    "launch_allowed_after_this_row",
    "fit_allowed_now",
    "score_allowed_now",
    "admission_allowed_now",
    "residual_policy",
]
CELL_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "cell_vtk_scope",
    "required_fields",
    "volume_csv",
    "volume_n_cells",
    "cell_identity_policy",
    "release_status",
    "validation_required_before_sampler",
    "native_solver_output_mutated",
]
FACE_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "facezone",
    "point",
    "normal",
    "source_path",
    "classification",
    "exchange_interface_release",
    "reason",
]
WALL_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "span",
    "wall_patches",
    "mesh_stations",
    "classification",
    "wall_core_release",
    "reason",
]
COMMAND_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "work_package",
    "command",
    "expected_output",
    "submit_allowed_now",
    "release_condition",
]
GUARD_FIELDS = ["guard_id", "status", "policy"]
HANDOFF_FIELDS = ["sequence", "work_package", "objective", "entry_condition", "forbidden_action"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def case_rows() -> list[dict[str, str]]:
    return read_csv(SOURCE_AUDIT / "case_window_source_audit.csv")


def volume_summary_path(case_id: str) -> Path:
    return INPUT_GENERATION / "cell_volumes" / f"{case_id}_cell_volumes_summary.json"


def volume_csv_path(case_id: str) -> Path:
    return INPUT_GENERATION / "cell_volumes" / f"{case_id}_cell_volumes.csv"


def vector_text(text: str) -> str:
    return " ".join(part for part in text.strip().strip("()").split())


def parse_toposet_planes(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rows: list[dict[str, str]] = []
    for match in re.finditer(
        r"name\s+([A-Za-z0-9_]+)\s*;(?P<body>.*?source\s+planeToFaceZone\s*;.*?include\s+closest\s*;)",
        text,
        flags=re.DOTALL,
    ):
        body = match.group("body")
        point_match = re.search(r"point\s+(\([^;]+\))\s*;", body)
        normal_match = re.search(r"normal\s+(\([^;]+\))\s*;", body)
        rows.append(
            {
                "facezone": match.group(1),
                "point": vector_text(point_match.group(1)) if point_match else "",
                "normal": vector_text(normal_match.group(1)) if normal_match else "",
            }
        )
    return rows


def mesh_station_path(source_id: str) -> Path:
    return MESH_CENTERLINES / source_id / "mesh_stations.json"


def mesh_station_spans(source_id: str) -> list[dict[str, Any]]:
    payload = load_json(mesh_station_path(source_id))
    spans = payload.get("span_diagnostics", [])
    return [span for span in spans if span.get("status") == "ok"]


def geometry_decision_rows() -> list[dict[str, str]]:
    return [
        {
            "geometry_lane": "cell_vtk",
            "decision": "released_whole_mesh_same_order",
            "basis": "whole-mesh cell extraction preserves direct cell-order alignment with validated cell-volume CSVs",
            "release_condition": "scheduler row must verify VTK cell count equals 2166996 and sampler volume CSV order is unchanged",
            "next_work_package": "whole_mesh_cell_vtk_extraction",
            "launch_allowed_after_this_row": "true_for_cell_vtk_only",
            "fit_allowed_now": "false",
            "score_allowed_now": "false",
            "admission_allowed_now": "false",
            "residual_policy": "do_not_hide_heat_residual_in_internal_Nu",
        },
        {
            "geometry_lane": "exchange_interface_vtk",
            "decision": "blocked_no_trusted_exchange_interface",
            "basis": "audited faceZones are loop mass-flow planes or proxy planes, not conservative main/recirculation exchange interfaces",
            "release_condition": "supply trusted point, normal, area/sign basis, and source path for main-to-cell/cell-to-main interface",
            "next_work_package": "exchange_interface_source_definition",
            "launch_allowed_after_this_row": "false",
            "fit_allowed_now": "false",
            "score_allowed_now": "false",
            "admission_allowed_now": "false",
            "residual_policy": "do_not_hide_heat_residual_in_internal_Nu",
        },
        {
            "geometry_lane": "wall_vtk",
            "decision": "blocked_until_recirc_region_and_wall_band_linked",
            "basis": "mesh centerline wall patches are known, but no wall/core band is tied to the recirculation cell region",
            "release_condition": "define wall/core band from the released recirculation region and state area-weighting convention",
            "next_work_package": "wall_core_band_definition",
            "launch_allowed_after_this_row": "false",
            "fit_allowed_now": "false",
            "score_allowed_now": "false",
            "admission_allowed_now": "false",
            "residual_policy": "do_not_hide_heat_residual_in_internal_Nu",
        },
    ]


def cell_vtk_contract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows():
        summary = load_json(volume_summary_path(case["case_id"]))
        rows.append(
            {
                "case_id": case["case_id"],
                "case_key": case["case_key"],
                "time_window_s": case["time_window_s"],
                "cell_vtk_scope": "whole_mesh",
                "required_fields": "U;T;rho",
                "volume_csv": rel(volume_csv_path(case["case_id"])),
                "volume_n_cells": summary.get("n_cells", ""),
                "cell_identity_policy": "same_order_as_openfoam_cell_labels_or_explicit_cellId_field_if_writer_supports_it",
                "release_status": "released_for_scheduler_cell_vtk_extraction",
                "validation_required_before_sampler": "vtk_cell_count_equals_volume_n_cells; volume_csv_row_order_unchanged; fields_U_T_rho_present",
                "native_solver_output_mutated": "false",
            }
        )
    return rows


def facezone_audit_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows():
        topo = ROOT / case["case_dir"] / "system/topoSetDict"
        for plane in parse_toposet_planes(topo):
            name = plane["facezone"]
            if "mdot_pipeleg" in name:
                classification = "loop_mass_flow_plane_not_exchange_interface"
                reason = "faceZone measures section mass flow and does not separate main throughflow from recirculation cell"
            else:
                classification = "non_exchange_proxy_or_unknown"
                reason = "not documented as conservative exchange-cell interface"
            rows.append(
                {
                    "case_id": case["case_id"],
                    "case_key": case["case_key"],
                    "time_window_s": case["time_window_s"],
                    "facezone": name,
                    "point": plane["point"],
                    "normal": plane["normal"],
                    "source_path": rel(topo),
                    "classification": classification,
                    "exchange_interface_release": "rejected",
                    "reason": reason,
                }
            )
        rows.append(
            {
                "case_id": case["case_id"],
                "case_key": case["case_key"],
                "time_window_s": case["time_window_s"],
                "facezone": "upcomer_outlet_proxy",
                "point": "",
                "normal": "",
                "source_path": rel(SURFACE_SOURCE / "surface_extraction_contract.csv"),
                "classification": "representative_proxy_not_exchange_interface",
                "exchange_interface_release": "rejected",
                "reason": "explicit plan guard forbids substituting representative upcomer outlet proxy for exchange interface",
            }
        )
    return rows


def wall_core_audit_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows():
        source_id = case["source_id"]
        for span in mesh_station_spans(source_id):
            span_name = str(span.get("span", ""))
            wall_patches = ";".join(span.get("wall_patches", []))
            classification = "known_wall_span_not_recirc_band"
            release = "blocked"
            reason = "wall patches are known but not connected to an approved recirculation cell region"
            if span_name == "right_leg":
                classification = "upcomer_related_wall_span_not_sufficient"
                reason = "right-leg/upcomer wall span is plausible support context but lacks recirculation-region band definition"
            rows.append(
                {
                    "case_id": case["case_id"],
                    "case_key": case["case_key"],
                    "time_window_s": case["time_window_s"],
                    "span": span_name,
                    "wall_patches": wall_patches,
                    "mesh_stations": rel(mesh_station_path(source_id)),
                    "classification": classification,
                    "wall_core_release": release,
                    "reason": reason,
                }
            )
    return rows


def extraction_command_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows():
        out = PACKAGE_DIR / "planned_outputs" / case["case_id"]
        rows.append(
            {
                "case_id": case["case_id"],
                "case_key": case["case_key"],
                "time_window_s": case["time_window_s"],
                "work_package": "whole_mesh_cell_vtk_extraction",
                "command": (
                    "stage task-local reconstructed case, then run OpenFOAM cell-field export for U/T/rho "
                    "to a whole-mesh VTK under the task package; exact command emitted by scheduler row"
                ),
                "expected_output": rel(out / f"{case['case_id']}_cell_fields.vtk"),
                "submit_allowed_now": "false",
                "release_condition": "claim scheduler row and use task-owned staged case; verify VTK cell count/order before sampler",
            }
        )
    return rows


def guard_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_outputs", "status": "pass_no_mutation", "policy": "geometry audit reads native case dictionaries and mesh maps only"},
        {"guard_id": "scheduler", "status": "not_submitted", "policy": "no Slurm action from geometry release row"},
        {"guard_id": "openfoam", "status": "not_launched", "policy": "no solver, reconstruction, foamPostProcess, foamToVTK, or sampler launch"},
        {"guard_id": "admission", "status": "blocked", "policy": "no fit, score, model selection, exchange-cell admission, Phase 4B/5/S6 trigger"},
        {"guard_id": "residual_lane", "status": "pass", "policy": "pressure and energy residuals remain separate lanes, not internal Nu"},
    ]


def handoff_rows() -> list[dict[str, Any]]:
    return [
        {
            "sequence": 1,
            "work_package": "whole_mesh_cell_vtk_extraction",
            "objective": "generate Salt2/Salt3/Salt4 whole-mesh cell VTKs with U/T/rho in task-owned staged cases",
            "entry_condition": "cell_vtk_contract.csv release_status is released_for_scheduler_cell_vtk_extraction",
            "forbidden_action": "do not write VTK/postProcessing outputs into native case directories",
        },
        {
            "sequence": 2,
            "work_package": "exchange_interface_source_definition",
            "objective": "supply trusted main/recirculation exchange interface point, normal, area/sign basis, and source path",
            "entry_condition": "facezone_candidate_audit.csv has no released exchange interface",
            "forbidden_action": "do not use upcomer outlet proxy or loop mass-flow planes as the exchange interface",
        },
        {
            "sequence": 3,
            "work_package": "wall_core_band_definition",
            "objective": "define wall/core band tied to the recirculation region before wall VTK or Q_wall_W extraction",
            "entry_condition": "recirculation-region definition or approved geometric band exists",
            "forbidden_action": "do not compute energy residual with static source/sink ledger alone",
        },
    ]


def manifest_rows(output_dir: Path) -> list[dict[str, Any]]:
    paths: list[Path] = [
        Path("tools/extract/build_upcomer_exchange_geometry_release.py"),
        Path("tools/extract/test_build_upcomer_exchange_geometry_release.py"),
        SOURCE_AUDIT,
        SURFACE_SOURCE,
        INPUT_GENERATION,
        HARVEST_SCAFFOLD,
        output_dir,
    ]
    for case in case_rows():
        paths.append(ROOT / case["case_dir"] / "system/topoSetDict")
        paths.append(mesh_station_path(case["source_id"]))
        paths.append(volume_summary_path(case["case_id"]))
    rows: list[dict[str, Any]] = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        task_output = (
            full == output_dir
            or str(path).startswith("tools/extract/build_upcomer_exchange_geometry_release")
            or str(path).startswith("tools/extract/test_build_upcomer_exchange_geometry_release")
        )
        relative_path = rel(full)
        native = relative_path.startswith("jadyn_runs/")
        rows.append(
            {
                "path": relative_path,
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(native).lower(),
                "mutated": str(task_output and full != output_dir).lower(),
            }
        )
    return rows


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, exchange-cell, geometry-release, no-solver]
related:
  - {rel(SURFACE_SOURCE)}
  - {rel(INPUT_GENERATION)}
  - {rel(HARVEST_SCAFFOLD)}
---
# Upcomer Exchange Geometry Release

This package implements the geometry-release phase for the upcomer exchange
blocker sequence. It releases only the whole-mesh `cell_vtk` policy and keeps
the exchange-interface and wall/core lanes blocked until a trusted geometry
source exists.

## Decision

- case windows: `{summary["case_rows"]}`
- released cell VTK rows: `{summary["released_cell_vtk_rows"]}/3`
- facezone audit rows: `{summary["facezone_audit_rows"]}`
- released exchange-interface rows: `{summary["released_exchange_interface_rows"]}`
- wall/core audit rows: `{summary["wall_core_audit_rows"]}`
- released wall/core rows: `{summary["released_wall_core_rows"]}`
- scheduler action: `false`
- OpenFOAM launch: `false`
- fit/score/admission allowed now: `false`

The next executable compute row should generate whole-mesh cell VTKs only.
Interface and wall/core generation remain blocked because loop mass-flow planes
and the representative upcomer outlet proxy do not define a conservative
main/recirculation exchange interface.

## Outputs

- `geometry_release_decision.csv`: lane-level release or blocker decision.
- `cell_vtk_contract.csv`: whole-mesh cell VTK extraction contract.
- `facezone_candidate_audit.csv`: rejected faceZone/proxy interface candidates.
- `wall_core_candidate_audit.csv`: wall span audit and blocker rationale.
- `planned_extraction_commands.csv`: next scheduler-row command contract.
- `no_mutation_guardrails.csv`, `next_agent_handoff.csv`, `source_manifest.csv`.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, generated docs index, fit,
score, model selection, exchange-cell admission, Phase 4B rescore, Phase 5/S6
trigger, or internal-Nu residual absorption is changed by this package.
"""


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    decisions = geometry_decision_rows()
    cell_rows = cell_vtk_contract_rows()
    face_rows = facezone_audit_rows()
    wall_rows = wall_core_audit_rows()
    commands = extraction_command_rows()
    guards = guard_rows()
    handoff = handoff_rows()
    manifest = manifest_rows(output_dir)
    csv_dump(output_dir / "geometry_release_decision.csv", GEOMETRY_FIELDS, decisions)
    csv_dump(output_dir / "cell_vtk_contract.csv", CELL_FIELDS, cell_rows)
    csv_dump(output_dir / "facezone_candidate_audit.csv", FACE_FIELDS, face_rows)
    csv_dump(output_dir / "wall_core_candidate_audit.csv", WALL_FIELDS, wall_rows)
    csv_dump(output_dir / "planned_extraction_commands.csv", COMMAND_FIELDS, commands)
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guards)
    csv_dump(output_dir / "next_agent_handoff.csv", HANDOFF_FIELDS, handoff)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "case_rows": len(case_rows()),
        "geometry_decision_rows": len(decisions),
        "released_cell_vtk_rows": sum(1 for row in cell_rows if row["release_status"].startswith("released")),
        "facezone_audit_rows": len(face_rows),
        "released_exchange_interface_rows": sum(1 for row in face_rows if row["exchange_interface_release"] == "released"),
        "wall_core_audit_rows": len(wall_rows),
        "released_wall_core_rows": sum(1 for row in wall_rows if row["wall_core_release"] == "released"),
        "planned_command_rows": len(commands),
        "scheduler_action": False,
        "openfoam_launch": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_edit": False,
        "external_repo_edit": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "phase4b_rescore_run": False,
        "phase5_or_s6_trigger": False,
        "residual_absorbed_into_internal_Nu": False,
    }
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    return {"summary": summary, "cell_rows": cell_rows, "face_rows": face_rows, "wall_rows": wall_rows}


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
