#!/usr/bin/env python3
"""Build the S13 upcomer exchange geometry contract package."""

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

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-GEOMETRY-CONTRACT-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract"
GEOMETRY_RELEASE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release"
SURFACE_SOURCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
S9_STUDY = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq"
S9_FIG = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence"
SALT2_CELL = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke"
SALT34_CELL = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix"

CASE_IDS = ("salt_2", "salt_3", "salt_4")

LEDGER_FIELDS = [
    "case_id",
    "lane",
    "candidate_source",
    "candidate_id",
    "classification",
    "release_status",
    "blocking_reason",
    "downstream_effect",
]
INTERFACE_FIELDS = [
    "case_id",
    "release_status",
    "interface_source",
    "surface_definition",
    "normal_vector_convention",
    "area_or_face_count_source",
    "mdot_exchange_ready",
    "blocking_reason",
]
WALL_CORE_FIELDS = [
    "case_id",
    "release_status",
    "recirculation_cell_volume_source",
    "wall_band_source",
    "wall_patch_candidates",
    "core_band_bounds",
    "q_wall_w_ready",
    "blocking_reason",
]
DOWNSTREAM_FIELDS = [
    "case_id",
    "input_lane",
    "status",
    "required_input",
    "available_input",
    "consumer",
    "blocking_reason",
]
GUARD_FIELDS = ["guard_id", "status", "policy"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def case_key_map() -> dict[str, str]:
    rows = read_csv(GEOMETRY_RELEASE / "cell_vtk_contract.csv")
    return {row["case_id"]: row["case_key"] for row in rows if row["case_id"] in CASE_IDS}


def cell_vtk_status() -> dict[str, str]:
    statuses = {case_id: "missing_or_not_validated" for case_id in CASE_IDS}
    for package in (SALT2_CELL, SALT34_CELL):
        report = package / "validation_report.csv"
        if not report.exists():
            continue
        for row in read_csv(report):
            case_id = row.get("case_id", "")
            if case_id in statuses and row.get("validation_status") == "pass":
                statuses[case_id] = row.get("cell_vtk", "")
    return statuses


def geometry_source_ledger_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(GEOMETRY_RELEASE / "facezone_candidate_audit.csv"):
        rows.append(
            {
                "case_id": row["case_id"],
                "lane": "exchange_interface",
                "candidate_source": row["source_path"],
                "candidate_id": row["facezone"],
                "classification": row["classification"],
                "release_status": row["exchange_interface_release"],
                "blocking_reason": row["reason"],
                "downstream_effect": "mdot_exchange_surface_blocked",
            }
        )
    for row in read_csv(GEOMETRY_RELEASE / "wall_core_candidate_audit.csv"):
        rows.append(
            {
                "case_id": row["case_id"],
                "lane": "wall_core_band",
                "candidate_source": row["mesh_stations"],
                "candidate_id": row["span"],
                "classification": row["classification"],
                "release_status": row["wall_core_release"],
                "blocking_reason": row["reason"],
                "downstream_effect": "wall_vtk_and_Q_wall_W_blocked",
            }
        )
    return rows


def interface_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "case_id": case_id,
            "release_status": "blocked_no_trusted_exchange_interface",
            "interface_source": "",
            "surface_definition": "not_released",
            "normal_vector_convention": "positive mdot_exchange must be defined from recirculation cell toward main throughflow once a trusted interface exists",
            "area_or_face_count_source": "",
            "mdot_exchange_ready": "false",
            "blocking_reason": "Existing faceZones are loop mass-flow planes or representative proxies; none are a conservative main/recirculation exchange boundary.",
        }
        for case_id in CASE_IDS
    ]


def wall_patch_candidates_by_case() -> dict[str, str]:
    candidates: dict[str, list[str]] = {case_id: [] for case_id in CASE_IDS}
    for row in read_csv(GEOMETRY_RELEASE / "wall_core_candidate_audit.csv"):
        if row["case_id"] in candidates and row["span"] == "right_leg":
            candidates[row["case_id"]].append(row["wall_patches"])
    return {case_id: ";".join(values) for case_id, values in candidates.items()}


def wall_core_contract_rows() -> list[dict[str, str]]:
    patches = wall_patch_candidates_by_case()
    return [
        {
            "case_id": case_id,
            "release_status": "blocked_no_recirc_region_wall_band_link",
            "recirculation_cell_volume_source": "",
            "wall_band_source": "",
            "wall_patch_candidates": patches.get(case_id, ""),
            "core_band_bounds": "not_released",
            "q_wall_w_ready": "false",
            "blocking_reason": "Right-leg/upcomer wall patches are plausible support context, but no approved recirculation cell region defines the wall/core band or area-weighting convention.",
        }
        for case_id in CASE_IDS
    ]


def downstream_input_rows() -> list[dict[str, str]]:
    cell_status = cell_vtk_status()
    rows: list[dict[str, str]] = []
    for case_id in CASE_IDS:
        rows.extend(
            [
                {
                    "case_id": case_id,
                    "input_lane": "cell_vtk",
                    "status": "ready" if cell_status[case_id] != "missing_or_not_validated" else "blocked_pending_cell_vtk",
                    "required_input": "whole-mesh cell VTK with U;T;rho and 2166996 cells",
                    "available_input": cell_status[case_id],
                    "consumer": "exchange sampler volume/state extraction",
                    "blocking_reason": "" if cell_status[case_id] != "missing_or_not_validated" else "cell_vtk_not_validated",
                },
                {
                    "case_id": case_id,
                    "input_lane": "exchange_interface_vtk",
                    "status": "blocked",
                    "required_input": "trusted main/recirculation exchange surface VTK with outward normal convention",
                    "available_input": "",
                    "consumer": "mdot_exchange integration",
                    "blocking_reason": "no released interface geometry source",
                },
                {
                    "case_id": case_id,
                    "input_lane": "wall_core_vtk",
                    "status": "blocked",
                    "required_input": "recirculation wall/core band VTK tied to the approved recirculation cell volume",
                    "available_input": "",
                    "consumer": "T_recirc and wall/core thermal contrast",
                    "blocking_reason": "no released recirculation region or wall/core band",
                },
                {
                    "case_id": case_id,
                    "input_lane": "Q_wall_W",
                    "status": "blocked",
                    "required_input": "same-window wall heat flow over the released recirculation wall band",
                    "available_input": "",
                    "consumer": "energy residual",
                    "blocking_reason": "wall band unavailable; static Q source/sink ledger is not a recirculation wall heat-flow measurement",
                },
                {
                    "case_id": case_id,
                    "input_lane": "exchange_cell_harvest",
                    "status": "blocked",
                    "required_input": "cell_vtk plus exchange_interface_vtk plus wall_core_vtk plus source/sink ledger",
                    "available_input": "cell_vtk_only_or_pending",
                    "consumer": "V_recirc; mdot_exchange; T_recirc; pressure_residual; energy_residual",
                    "blocking_reason": "interface/wall/Q_wall lanes are not released",
                },
            ]
        )
    return rows


def guard_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_outputs", "status": "pass_read_only", "policy": "geometry contract reads prior packages only"},
        {"guard_id": "surface_extraction", "status": "blocked", "policy": "no interface/wall VTK extraction until geometry source is trusted"},
        {"guard_id": "harvest", "status": "blocked", "policy": "no exchange-cell harvest from partial cell-only inputs"},
        {"guard_id": "admission", "status": "blocked", "policy": "no fit, score, model selection, ordinary upcomer reopening, or exchange-cell admission"},
        {"guard_id": "residual_lane", "status": "pass", "policy": "do not absorb pressure or energy residual into internal Nu"},
    ]


def manifest_rows(output_dir: Path) -> list[dict[str, str]]:
    paths = [
        Path("tools/extract/build_s13_upcomer_exchange_geometry_contract.py"),
        Path("tools/extract/test_s13_upcomer_exchange_geometry_contract.py"),
        GEOMETRY_RELEASE,
        SURFACE_SOURCE,
        S9_STUDY,
        S9_FIG,
        SALT2_CELL,
        SALT34_CELL,
        output_dir,
    ]
    rows: list[dict[str, str]] = []
    for path in paths:
        full = path if path.is_absolute() else ROOT / path
        relative = rel(full)
        task_output = full == output_dir or relative.startswith("tools/extract/build_s13_upcomer_exchange_geometry_contract") or relative.startswith("tools/extract/test_s13_upcomer_exchange_geometry_contract")
        rows.append(
            {
                "path": relative,
                "role": "task_output" if task_output else "read_only_context",
                "exists": str(full.exists()).lower(),
                "native_solver_output": str(relative.startswith("jadyn_runs/")).lower(),
                "mutated": str(task_output).lower(),
            }
        )
    return rows


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: {summary["status"]}
tags: [upcomer, exchange-cell, geometry-contract, fail-closed, no-admission]
related:
  - {rel(GEOMETRY_RELEASE)}
  - {rel(SURFACE_SOURCE)}
  - {rel(S9_STUDY)}
---
# S13 Upcomer Exchange Geometry Contract

This package resolves the current geometry gate conservatively. It publishes
the required interface and wall/core geometry contracts, but releases no
exchange-interface, wall/core, `Q_wall_W`, or harvest lane because the trusted
recirculation volume/interface source is still missing.

## Decision

- cases: `salt_2`, `salt_3`, `salt_4`
- released exchange-interface rows: `{summary["released_interface_rows"]}`
- released wall/core rows: `{summary["released_wall_core_rows"]}`
- released `Q_wall_W` rows: `{summary["released_q_wall_rows"]}`
- harvest-ready rows: `{summary["harvest_ready_rows"]}`
- scheduler action: `false`
- native output mutation: `false`
- fit/score/admission allowed now: `false`

## Outputs

- `geometry_source_ledger.csv`
- `interface_geometry_contract.csv`
- `wall_core_band_contract.csv`
- `downstream_surface_vtk_inputs.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Do not substitute loop `mdot_*` faceZones or an upcomer outlet proxy for a
main/recirculation exchange interface. Do not run surface VTK extraction or
exchange-cell harvest until a later row supplies a trusted recirculation cell
volume, interface surface, normal-vector basis, and wall/core band.
"""


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    ledger = geometry_source_ledger_rows()
    interface = interface_contract_rows()
    wall_core = wall_core_contract_rows()
    downstream = downstream_input_rows()
    guards = guard_rows()
    manifest = manifest_rows(output_dir)
    released_interface = sum(1 for row in interface if row["release_status"].startswith("released"))
    released_wall = sum(1 for row in wall_core if row["release_status"].startswith("released"))
    released_q_wall = sum(1 for row in wall_core if row["q_wall_w_ready"] == "true")
    harvest_ready = sum(1 for row in downstream if row["input_lane"] == "exchange_cell_harvest" and row["status"] == "ready")
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "status": "complete_fail_closed",
        "case_ids": list(CASE_IDS),
        "case_count": len(CASE_IDS),
        "geometry_source_ledger_rows": len(ledger),
        "released_interface_rows": released_interface,
        "released_wall_core_rows": released_wall,
        "released_q_wall_rows": released_q_wall,
        "harvest_ready_rows": harvest_ready,
        "surface_vtk_extraction_allowed": False,
        "exchange_cell_harvest_allowed": False,
        "native_output_mutation": False,
        "scheduler_action": False,
        "fitting_or_model_selection": False,
        "exchange_cell_admission": False,
        "residual_absorbed_into_internal_Nu": False,
    }
    csv_dump(output_dir / "geometry_source_ledger.csv", LEDGER_FIELDS, ledger)
    csv_dump(output_dir / "interface_geometry_contract.csv", INTERFACE_FIELDS, interface)
    csv_dump(output_dir / "wall_core_band_contract.csv", WALL_CORE_FIELDS, wall_core)
    csv_dump(output_dir / "downstream_surface_vtk_inputs.csv", DOWNSTREAM_FIELDS, downstream)
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guards)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    return {
        "summary": summary,
        "ledger": ledger,
        "interface": interface,
        "wall_core": wall_core,
        "downstream": downstream,
    }


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
