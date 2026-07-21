#!/usr/bin/env python3
"""Publish the three-case upcomer exchange cell-VTK input manifest."""

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

TASK_ID = "TODO-UPCOMER-EXCHANGE-THREE-CASE-CELL-VTK-MANIFEST-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest"
SALT2_PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke"
SALT34_PACKAGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix"
GEOMETRY_RELEASE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release"
INPUT_GENERATION = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation"
SURFACE_SOURCE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
SCAFFOLD = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold"
CASE_IDS = ("salt_2", "salt_3", "salt_4")
REQUIRED_CELL_FIELDS = ("U", "T", "rho")

CELL_MANIFEST_FIELDS = [
    "case_id",
    "case_key",
    "time_window_s",
    "cell_vtk",
    "cell_vtk_exists",
    "expected_cells",
    "observed_cells",
    "required_fields",
    "observed_fields",
    "validation_status",
    "source_validation_report",
    "source_task",
    "release_status",
    "blocking_reason",
]
VALIDATION_JOIN_FIELDS = [
    "case_id",
    "time_window_s",
    "cell_contract_status",
    "cell_vtk_validation_status",
    "cell_lane_release",
    "sampler_ready",
    "remaining_blockers",
]
SAMPLER_MANIFEST_FIELDS = [
    "case_id",
    "time_window_s",
    "cell_vtk",
    "interface_vtk",
    "wall_vtk",
    "volume_csv",
    "throughflow_nx",
    "throughflow_ny",
    "throughflow_nz",
    "interface_nx",
    "interface_ny",
    "interface_nz",
    "output_dir",
    "cp_J_kg_K",
]
BLOCKER_FIELDS = [
    "case_id",
    "time_window_s",
    "blocked_input",
    "current_status",
    "blocking_for_harvest",
    "reason",
    "unlock_condition",
]
SOURCE_LEDGER_FIELDS = [
    "case_id",
    "time_window_s",
    "q_source_w",
    "q_sink_w",
    "q_net_w",
    "source_sink_status",
    "q_wall_w_status",
    "sampler_release_status",
]
GUARD_FIELDS = ["guard_id", "status", "policy"]
SOURCE_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validation_report_paths() -> tuple[Path, Path]:
    return (
        SALT2_PACKAGE / "validation_report.csv",
        SALT34_PACKAGE / "validation_report.csv",
    )


def load_validation_rows() -> dict[str, dict[str, str]]:
    selected: dict[str, dict[str, str]] = {}
    source_tasks = {
        SALT2_PACKAGE / "validation_report.csv": "TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT2-SMOKE-2026-07-21",
        SALT34_PACKAGE / "validation_report.csv": "TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT3-SALT4-MATRIX-2026-07-21",
    }
    for path in validation_report_paths():
        for row in read_csv(path):
            case_id = row["case_id"]
            if case_id in CASE_IDS:
                enriched = dict(row)
                enriched["source_validation_report"] = rel(path)
                enriched["source_task"] = source_tasks[path]
                selected[case_id] = enriched
    missing = sorted(set(CASE_IDS) - set(selected))
    if missing:
        raise ValueError(f"Missing validation rows for {missing}")
    return selected


def load_contract_rows() -> dict[str, dict[str, str]]:
    rows = read_csv(GEOMETRY_RELEASE / "cell_vtk_contract.csv")
    selected = {row["case_id"]: row for row in rows if row["case_id"] in CASE_IDS}
    missing = sorted(set(CASE_IDS) - set(selected))
    if missing:
        raise ValueError(f"Missing cell contract rows for {missing}")
    return selected


def required_fields_present(observed_fields: str) -> bool:
    observed = {field.strip() for field in observed_fields.split(";") if field.strip()}
    return all(field in observed for field in REQUIRED_CELL_FIELDS)


def build_cell_manifest_rows() -> list[dict[str, Any]]:
    validation = load_validation_rows()
    contracts = load_contract_rows()
    rows: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        vrow = validation[case_id]
        crow = contracts[case_id]
        vtk_path = ROOT / vrow["cell_vtk"]
        blockers = []
        if vrow["validation_status"] != "pass":
            blockers.append("cell_vtk_validation_not_pass")
        if not vtk_path.exists():
            blockers.append("cell_vtk_path_missing")
        if str(vrow["observed_cells"]) != str(crow["volume_n_cells"]):
            blockers.append("cell_count_mismatch")
        if not required_fields_present(vrow["observed_fields"]):
            blockers.append("required_cell_fields_missing")
        rows.append(
            {
                "case_id": case_id,
                "case_key": crow["case_key"],
                "time_window_s": crow["time_window_s"],
                "cell_vtk": vrow["cell_vtk"],
                "cell_vtk_exists": str(vtk_path.exists()).lower(),
                "expected_cells": crow["volume_n_cells"],
                "observed_cells": vrow["observed_cells"],
                "required_fields": ";".join(REQUIRED_CELL_FIELDS),
                "observed_fields": vrow["observed_fields"],
                "validation_status": "pass" if not blockers else "failed",
                "source_validation_report": vrow["source_validation_report"],
                "source_task": vrow["source_task"],
                "release_status": "cell_lane_released_for_manifest" if not blockers else "cell_lane_blocked",
                "blocking_reason": ";".join(blockers),
            }
        )
    return rows


def build_sampler_manifest_rows(cell_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cell_by_case = {row["case_id"]: row for row in cell_rows}
    template_rows = read_csv(SCAFFOLD / "case_vtk_input_manifest.template.csv")
    rows: list[dict[str, Any]] = []
    for template in template_rows:
        case_id = template["case_id"]
        row = {field: template.get(field, "") for field in SAMPLER_MANIFEST_FIELDS}
        if case_id in cell_by_case:
            row["cell_vtk"] = cell_by_case[case_id]["cell_vtk"]
        rows.append(row)
    return rows


def build_source_ledger_rows() -> list[dict[str, str]]:
    source_rows = {row["case_id"]: row for row in read_csv(SURFACE_SOURCE / "source_sink_summary.csv")}
    rows: list[dict[str, str]] = []
    for case_id in CASE_IDS:
        row = source_rows[case_id]
        rows.append(
            {
                "case_id": case_id,
                "time_window_s": row["time_window_s"],
                "q_source_w": row["q_source_w"],
                "q_sink_w": row["q_sink_w"],
                "q_net_w": row["q_net_w"],
                "source_sink_status": row["status"],
                "q_wall_w_status": "blocked_missing_wallHeatFlux_integration_and_wall_core_band",
                "sampler_release_status": "blocked_until_Q_wall_W_and_sign_convention_are_published",
            }
        )
    return rows


def build_blocker_rows() -> list[dict[str, str]]:
    contract_rows = read_csv(SCAFFOLD / "required_vtk_input_contract.csv")
    blockers: list[dict[str, str]] = []
    for row in contract_rows:
        if row["input_role"] == "cell_vtk":
            continue
        blockers.append(
            {
                "case_id": row["case_id"],
                "time_window_s": row["time_window_s"],
                "blocked_input": row["input_role"],
                "current_status": row["current_status"],
                "blocking_for_harvest": row["blocking_for_harvest"],
                "reason": row["release_condition"],
                "unlock_condition": "claim and complete a separate geometry/source work package before sampler execution",
            }
        )
    for row in build_source_ledger_rows():
        blockers.append(
            {
                "case_id": row["case_id"],
                "time_window_s": row["time_window_s"],
                "blocked_input": "Q_wall_W",
                "current_status": row["q_wall_w_status"],
                "blocking_for_harvest": "true",
                "reason": "static source/sink terms are parsed, but wall heat loss is not integrated or sign-convention released",
                "unlock_condition": "publish task-owned wall/core band, wallHeatFlux integration, and heat-flow sign convention",
            }
        )
    return blockers


def build_validation_join_rows(cell_rows: list[dict[str, Any]], blocker_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    blockers_by_case: dict[str, list[str]] = {case_id: [] for case_id in CASE_IDS}
    for row in blocker_rows:
        blockers_by_case[row["case_id"]].append(row["blocked_input"])
    rows: list[dict[str, str]] = []
    for row in cell_rows:
        case_id = row["case_id"]
        cell_ok = row["validation_status"] == "pass"
        rows.append(
            {
                "case_id": case_id,
                "time_window_s": str(row["time_window_s"]),
                "cell_contract_status": row["release_status"],
                "cell_vtk_validation_status": row["validation_status"],
                "cell_lane_release": "released" if cell_ok else "blocked",
                "sampler_ready": "false",
                "remaining_blockers": ";".join(blockers_by_case[case_id]),
            }
        )
    return rows


def no_mutation_guardrails() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_solver_output_mutated", "status": "false", "policy": "read existing task-owned validation artifacts only"},
        {"guard_id": "registry_or_admission_mutated", "status": "false", "policy": "manifest publication does not change global registry or admission"},
        {"guard_id": "scheduler_action", "status": "false", "policy": "no compute or OpenFOAM launch in this manifest row"},
        {"guard_id": "interface_wall_sampler_harvest_launched", "status": "false", "policy": "non-cell lanes remain blockers"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "status": "false", "policy": "heat residual remains outside internal Nu and blocked pending wall/source lanes"},
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    paths = [
        (SALT2_PACKAGE / "validation_report.csv", "Salt2 validated cell VTK source"),
        (SALT34_PACKAGE / "validation_report.csv", "Salt3/Salt4 validated cell VTK source"),
        (GEOMETRY_RELEASE / "cell_vtk_contract.csv", "cell lane release contract"),
        (INPUT_GENERATION / "cell_volumes", "cell volume package context"),
        (SURFACE_SOURCE / "source_sink_summary.csv", "static source/sink context"),
        (SCAFFOLD / "case_vtk_input_manifest.template.csv", "sampler manifest template"),
        (SCAFFOLD / "required_vtk_input_contract.csv", "sampler required input contract"),
    ]
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path, role in paths
    ]


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, exchange-cell, cell-vtk, manifest, no-scheduler]
related:
  - {rel(SALT2_PACKAGE)}
  - {rel(SALT34_PACKAGE)}
  - {rel(SCAFFOLD)}
---
# Upcomer Exchange Three-Case Cell VTK Manifest

This package publishes the three-case cell-lane manifest for the upcomer
exchange sampler. It joins the validated Salt2, Salt3, and Salt4 whole-mesh
`cell_vtk` artifacts into the reusable sampler manifest template.

## Decision

- cell VTK rows: `{summary["cell_vtk_rows"]}`
- cell VTK pass rows: `{summary["cell_vtk_pass_rows"]}`
- sampler-ready rows: `{summary["sampler_ready_rows"]}`
- remaining blocker rows: `{summary["remaining_blocker_rows"]}`
- scheduler action: `false`
- OpenFOAM launch: `false`
- exchange-cell harvest launched: `false`
- fit/score/admission allowed now: `false`

The cell lane is no longer the blocker for Salt2/Salt3/Salt4. The sampler is
still intentionally fail-closed because `exchange_interface_vtk`, `wall_vtk`,
normal vectors, `Q_wall_W`, and the source/sink heat-flow sign convention have
not been released. The static source/sink summary is recorded as context only;
it is not a complete heat-loss ledger.

## Outputs

- `three_case_cell_vtk_manifest.csv`: validated cell VTK paths and provenance.
- `case_vtk_input_manifest.cells_populated.csv`: sampler template with only the
  cell paths populated.
- `three_case_cell_vtk_validation_join.csv`: cell release versus sampler gate.
- `source_sink_wall_loss_readiness.csv`: source/sink context and `Q_wall_W`
  blocker.
- `remaining_sampler_blockers.csv`: non-cell blockers that still prevent
  sampler harvest.
- `no_mutation_guardrails.csv`, `source_manifest.csv`, and `summary.json`.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, generated docs index, fit,
score, model selection, exchange-cell admission, Phase 4B rescore, Phase 5/S6
trigger, or internal-Nu residual absorption is changed by this package.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(output_dir)
    cell_rows = build_cell_manifest_rows()
    sampler_rows = build_sampler_manifest_rows(cell_rows)
    source_rows = build_source_ledger_rows()
    blocker_rows = build_blocker_rows()
    join_rows = build_validation_join_rows(cell_rows, blocker_rows)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "cell_vtk_rows": len(cell_rows),
        "cell_vtk_pass_rows": sum(1 for row in cell_rows if row["validation_status"] == "pass"),
        "sampler_ready_rows": sum(1 for row in join_rows if row["sampler_ready"] == "true"),
        "remaining_blocker_rows": len(blocker_rows),
        "scheduler_action": False,
        "openfoam_launch": False,
        "sampler_harvest_launched": False,
        "fit_score_or_admission_changed": False,
        "native_solver_output_mutated": False,
        "registry_or_admission_mutated": False,
        "residual_absorbed_into_internal_Nu": False,
        "current_blocker": "exchange_interface_vtk, wall_vtk, normals, Q_wall_W, and source/sink sign convention remain unreleased",
    }
    csv_dump(output_dir / "three_case_cell_vtk_manifest.csv", CELL_MANIFEST_FIELDS, cell_rows)
    csv_dump(output_dir / "case_vtk_input_manifest.cells_populated.csv", SAMPLER_MANIFEST_FIELDS, sampler_rows)
    csv_dump(output_dir / "source_sink_wall_loss_readiness.csv", SOURCE_LEDGER_FIELDS, source_rows)
    csv_dump(output_dir / "remaining_sampler_blockers.csv", BLOCKER_FIELDS, blocker_rows)
    csv_dump(output_dir / "three_case_cell_vtk_validation_join.csv", VALIDATION_JOIN_FIELDS, join_rows)
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, no_mutation_guardrails())
    csv_dump(output_dir / "source_manifest.csv", SOURCE_FIELDS, source_manifest_rows())
    json_dump(output_dir / "summary.json", summary)
    write_readme(output_dir, summary)
    return {
        "cell_rows": cell_rows,
        "sampler_rows": sampler_rows,
        "source_rows": source_rows,
        "blocker_rows": blocker_rows,
        "join_rows": join_rows,
        "summary": summary,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_package(args.output_dir)
    print(json.dumps(payload["summary"], indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
