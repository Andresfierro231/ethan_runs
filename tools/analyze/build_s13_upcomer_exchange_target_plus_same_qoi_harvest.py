#!/usr/bin/env python3
"""Harvest S13 target-plus rows from staged continuation windows."""

from __future__ import annotations

import csv
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_s13_upcomer_exchange_qwall_neighbor_window_sampling as neighbor
from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract import build_s13_upcomer_exchange_exact_pressure_qwall_compute as exact


TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-SAME-QOI-HARVEST-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest"
)
GENERATION = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_target_plus_window_generation"
)
PRIOR_NEIGHBOR = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling"
)
STAGING = ROOT / "staging/s13_target_plus_window_generation_2026-07-22"

TARGET_PLUS_CASE_DIRS = {
    "salt_2": STAGING / "salt_2/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
    "salt_3": STAGING / "salt_3/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
    "salt_4": STAGING / "salt_4/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
}
TARGET_PLUS_TIMES = {"salt_2": "7916", "salt_3": "7619", "salt_4": "10001"}


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def bool_text(value: bool) -> str:
    return str(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@contextmanager
def staged_case_dirs() -> Iterator[None]:
    original = dict(exact.CASE_DIRS)
    exact.CASE_DIRS.update(TARGET_PLUS_CASE_DIRS)
    try:
        yield
    finally:
        exact.CASE_DIRS.clear()
        exact.CASE_DIRS.update(original)


def target_plus_field_status_rows() -> list[dict[str, str]]:
    rows = []
    for case_id, case_dir in TARGET_PLUS_CASE_DIRS.items():
        time_s = TARGET_PLUS_TIMES[case_id]
        time_dir = case_dir / "processors64" / time_s
        fields = ["U", "T", "rho", "wallHeatFlux"]
        rows.append(
            {
                "case_id": case_id,
                "staged_case": rel(case_dir),
                "target_plus_time_window_s": time_s,
                "target_plus_dir": rel(time_dir),
                "target_plus_dir_exists": bool_text(time_dir.is_dir()),
                "required_fields": ";".join(fields),
                "required_fields_present": bool_text(all((time_dir / field).is_file() for field in fields)),
                "cell_addressing_present": bool_text((case_dir / "processors64/constant/polyMesh/cellProcAddressing").is_file()),
                "face_addressing_present": bool_text((case_dir / "processors64/constant/polyMesh/faceProcAddressing").is_file()),
                "boundary_map_present": bool_text((case_dir / "processors64/constant/polyMesh/boundary").is_file()),
                "source_basis": "staged_target_plus_continuation_output",
            }
        )
    return rows


def target_plus_samples() -> dict[str, dict[str, str]]:
    sampled: dict[str, dict[str, str]] = {}
    with staged_case_dirs():
        for case in exact.case_rows():
            case_id = case["case_id"]
            sampled[case_id] = neighbor.sample_native_window(case, TARGET_PLUS_TIMES[case_id], "target_plus")
            sampled[case_id]["sample_status"] = "sampled_from_staged_target_plus_processors64"
    return sampled


def target_plus_qoi_rows(samples: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for case_id in ["salt_2", "salt_3", "salt_4"]:
        sample = samples[case_id]
        for qoi_label in neighbor.qoi_labels():
            rows.append(
                {
                    "case_id": case_id,
                    "qoi_label": qoi_label,
                    "target_plus_time_window_s": TARGET_PLUS_TIMES[case_id],
                    "target_plus_value": sample[qoi_label],
                    "target_plus_status": "sampled_from_staged_target_plus_processors64",
                    "same_label_formula_sign_basis": "true",
                    "source_basis": (
                        "trusted_wall_wallHeatFlux_integral"
                        if qoi_label == "Q_wall_W"
                        else "staged_native_U_T_rho_selected_cells_and_released_geometry"
                    ),
                }
            )
    return rows


def joined_neighbor_rows(target_plus_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    plus_lookup = {(row["case_id"], row["qoi_label"]): row for row in target_plus_rows}
    out = []
    for row in read_csv(PRIOR_NEIGHBOR / "same_qoi_neighbor_window_rows.csv"):
        plus = plus_lookup[(row["case_id"], row["qoi_label"])]
        joined = dict(row)
        joined["target_plus_time_window_s"] = plus["target_plus_time_window_s"]
        joined["target_plus_value"] = plus["target_plus_value"]
        joined["target_plus_status"] = plus["target_plus_status"]
        joined["same_label_formula_sign_basis"] = "true"
        joined["neighbor_window_uq_ready"] = "true"
        joined["production_use_allowed_now"] = "false"
        out.append(joined)
    return out


def same_qoi_triplet_matrix(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for qoi_label in neighbor.qoi_labels():
        selected = [row for row in rows if row["qoi_label"] == qoi_label]
        target_ready = sum(1 for row in selected if row["target_status"])
        minus_ready = sum(1 for row in selected if row["target_minus_status"].startswith("sampled"))
        plus_ready = sum(1 for row in selected if row["target_plus_status"].startswith("sampled"))
        triplet_ready = target_ready == 3 and minus_ready == 3 and plus_ready == 3
        out.append(
            {
                "qoi_label": qoi_label,
                "case_count": "3",
                "target_ready_rows": str(target_ready),
                "target_minus_ready_rows": str(minus_ready),
                "target_plus_ready_rows": str(plus_ready),
                "same_qoi_neighbor_triplet_ready": bool_text(triplet_ready),
                "same_qoi_neighbor_uq_execution_status": "ready_not_executed" if triplet_ready else "blocked_missing_triplet_rows",
                "move_to_mesh_gci_uq_allowed_now": "false",
                "production_use_allowed_now": "false",
                "blocking_or_next_reason": (
                    "all target-minus/target/target-plus rows exist; claim separate same-QOI UQ execution row next"
                    if triplet_ready
                    else "missing same-QOI triplet rows"
                ),
            }
        )
    return out


def production_gate_rows(matrix_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ready = sum(1 for row in matrix_rows if row["same_qoi_neighbor_triplet_ready"] == "true")
    return [
        {
            "gate": "target_plus_generation",
            "status": "complete",
            "ready_for_next_stage": "true",
            "production_harvest_allowed_now": "false",
            "reason": "staged target-plus windows exist for Salt2/Salt3/Salt4",
        },
        {
            "gate": "target_plus_same_qoi_harvest",
            "status": "complete" if ready == 4 else "blocked",
            "ready_for_next_stage": bool_text(ready == 4),
            "production_harvest_allowed_now": "false",
            "reason": f"{ready}/4 QOI labels have complete target-minus/target/target-plus support",
        },
        {
            "gate": "same_qoi_neighbor_uq_execution",
            "status": "ready_not_executed" if ready == 4 else "blocked",
            "ready_for_next_stage": bool_text(ready == 4),
            "production_harvest_allowed_now": "false",
            "reason": "claim separate same-QOI UQ execution row before mesh/GCI or production harvest",
        },
        {
            "gate": "mesh_gci_uq",
            "status": "not_reached_same_qoi_uq_not_executed",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": "mesh/GCI waits for same-QOI neighbor UQ execution result",
        },
        {
            "gate": "production_harvest",
            "status": "do_not_run",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": "target-plus availability is solved, but UQ gates are still not executed",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    rows = [
        {
            "path": rel(GENERATION / "summary.json"),
            "role": "target-plus generation summary",
            "exists": bool_text((GENERATION / "summary.json").exists()),
            "mutation": "read_only",
        },
        {
            "path": rel(PRIOR_NEIGHBOR / "same_qoi_neighbor_window_rows.csv"),
            "role": "target-minus and target evidence rows",
            "exists": bool_text((PRIOR_NEIGHBOR / "same_qoi_neighbor_window_rows.csv").exists()),
            "mutation": "read_only",
        },
    ]
    for case_id, case_dir in TARGET_PLUS_CASE_DIRS.items():
        time_s = TARGET_PLUS_TIMES[case_id]
        for field in ("U", "T", "rho", "wallHeatFlux"):
            path = case_dir / "processors64" / time_s / field
            rows.append(
                {
                    "path": rel(path),
                    "role": f"{case_id} staged target-plus {field}",
                    "exists": bool_text(path.exists()),
                    "mutation": "read_only",
                }
            )
    return rows


def guardrail_rows() -> list[dict[str, str]]:
    flags = {
        "native_output_mutation": "false",
        "staged_output_mutation": "false",
        "registry_or_admission_mutation": "false",
        "scheduler_action": "false",
        "solver_or_sampler_launch": "false",
        "same_qoi_uq_execution": "false",
        "mesh_gci_uq_execution": "false",
        "production_harvest": "false",
        "Qwall_source_property_or_coefficient_release": "false",
        "s11_s12_s13_s15_s6_trigger": "false",
        "residual_absorbed_into_internal_nu": "false",
    }
    return [{"guardrail": key, "value": value} for key, value in flags.items()]


def write_readme(summary: dict[str, object]) -> None:
    text = f"""---
provenance:
  - {rel(OUT / "target_plus_qoi_rows.csv")}
  - {rel(OUT / "same_qoi_neighbor_triplet_matrix.csv")}
  - {rel(GENERATION / "job_terminal_status.csv")}
tags: [s13, upcomer-exchange, target-plus, same-qoi-uq]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - {rel(GENERATION / "README.md")}
  - {rel(PRIOR_NEIGHBOR / "README.md")}
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Target-Plus Same-QOI Harvest

Decision: `{summary["decision"]}`.

This package harvested the staged target-plus windows and joined them to the
existing target-minus/target S13 evidence. It does not execute UQ or production
harvest.

- target-plus QOI rows: `{summary["target_plus_qoi_rows"]}`
- joined triplet rows: `{summary["joined_triplet_rows"]}`
- same-QOI triplet-ready labels: `{summary["same_qoi_neighbor_triplet_ready_qois"]}`
- same-QOI UQ executed: `false`
- production harvest allowed: `false`

Next action: claim a separate same-QOI neighbor UQ execution row using the
complete triplet table. Mesh/GCI UQ and production harvest remain closed until
that row passes.
"""
    (OUT / "README.md").write_text(text)


def build() -> dict[str, object]:
    ensure_dir(OUT)
    field_rows = target_plus_field_status_rows()
    samples = target_plus_samples()
    plus_rows = target_plus_qoi_rows(samples)
    joined_rows = joined_neighbor_rows(plus_rows)
    matrix_rows = same_qoi_triplet_matrix(joined_rows)
    gate_rows = production_gate_rows(matrix_rows)
    source_rows = source_manifest_rows()
    guard_rows = guardrail_rows()
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "target_plus_same_qoi_rows_harvested_triplets_ready_uq_not_executed",
        "case_count": 3,
        "qoi_label_count": len(neighbor.qoi_labels()),
        "target_plus_qoi_rows": len(plus_rows),
        "joined_triplet_rows": len(joined_rows),
        "target_ready_rows": sum(1 for row in joined_rows if row["target_status"]),
        "target_minus_ready_rows": sum(1 for row in joined_rows if row["target_minus_status"].startswith("sampled")),
        "target_plus_ready_rows": sum(1 for row in joined_rows if row["target_plus_status"].startswith("sampled")),
        "same_qoi_neighbor_triplet_ready_qois": sum(
            1 for row in matrix_rows if row["same_qoi_neighbor_triplet_ready"] == "true"
        ),
        "same_qoi_uq_executed": False,
        "move_to_mesh_gci_uq_allowed_now": False,
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "native_output_mutation": False,
        "staged_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_sampler_harvest_uq_launched": False,
        "Q_wall_W_production_release": False,
        "source_property_release": False,
        "source_side_relabel_as_Q_wall": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }

    csv_dump(OUT / "target_plus_field_status.csv", list(field_rows[0]), field_rows)
    csv_dump(OUT / "target_plus_qoi_rows.csv", list(plus_rows[0]), plus_rows)
    csv_dump(OUT / "same_qoi_neighbor_window_rows.csv", list(joined_rows[0]), joined_rows)
    csv_dump(OUT / "same_qoi_neighbor_triplet_matrix.csv", list(matrix_rows[0]), matrix_rows)
    csv_dump(OUT / "production_readiness_gate.csv", list(gate_rows[0]), gate_rows)
    csv_dump(OUT / "source_manifest.csv", list(source_rows[0]), source_rows)
    csv_dump(OUT / "no_mutation_guardrails.csv", list(guard_rows[0]), guard_rows)
    json_dump(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
