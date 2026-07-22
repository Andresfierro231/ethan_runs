#!/usr/bin/env python3
"""Sample S13 same-QOI neighbor windows from existing native fields."""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_s13_upcomer_exchange_average_field_thermal_reduction as avg
from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract import build_s13_upcomer_exchange_exact_pressure_qwall_compute as exact

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-QWALL-NEIGHBOR-WINDOW-SAMPLING-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling"
)
PRIOR_UQ = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution"
)
EXACT_QWALL = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"
)
LIMITED = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction"
)
AVERAGE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction"
)
SURFACE_INPUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv"
)

VECTOR_RE = re.compile(r"\(([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\)")
EPS = 1.0e-12


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def bool_text(value: bool) -> str:
    return str(value).lower()


def fmt(value: float) -> str:
    return f"{value:.12g}" if math.isfinite(value) else ""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def qoi_labels() -> list[str]:
    return [
        "Q_wall_W",
        "mdot_exchange_positive_outward_proxy_kg_s",
        "tau_recirc_proxy_s",
        "wall_core_bulk_temperature_contrast_K",
    ]


def numeric_time_dirs(case_id: str) -> list[int]:
    case_dir = exact.CASE_DIRS[case_id] / "processors64"
    times: list[int] = []
    for item in case_dir.iterdir():
        if item.is_dir() and item.name.isdigit():
            times.append(int(item.name))
    return sorted(times)


def neighbor_times(case: dict[str, str]) -> dict[str, str]:
    target = int(case["time_window_s"])
    times = numeric_time_dirs(case["case_id"])
    before = [time for time in times if time < target]
    after = [time for time in times if time > target]
    return {
        "case_id": case["case_id"],
        "target_time_window_s": str(target),
        "target_minus_time_window_s": str(before[-1]) if before else "",
        "target_plus_time_window_s": str(after[0]) if after else "",
        "target_minus_available": bool_text(bool(before)),
        "target_plus_available": bool_text(bool(after)),
        "stored_time_count": str(len(times)),
        "first_stored_time_s": str(times[0]) if times else "",
        "last_stored_time_s": str(times[-1]) if times else "",
    }


def parse_vector_list(block: str) -> list[tuple[float, float, float]]:
    match = re.search(r"(?ms)internalField\s+nonuniform\s+List<vector>\s*(\d+)\s*\(\s*(.*?)\s*\)\s*;", block)
    if not match:
        raise ValueError("could not find OpenFOAM vector internalField")
    expected = int(match.group(1))
    values = [tuple(float(part) for part in vector_match.groups()) for vector_match in VECTOR_RE.finditer(match.group(2))]
    if len(values) != expected:
        raise ValueError(f"vector count mismatch: expected {expected}, got {len(values)}")
    return values


def read_mapped_vector_field(
    field_path: Path,
    addressing_path: Path,
    selected: set[int],
) -> dict[int, tuple[float, float, float]]:
    selected_values: dict[int, tuple[float, float, float]] = {}
    address_blocks = exact.processor_blocks(exact.load_text(addressing_path))
    field_blocks = exact.processor_blocks(exact.load_text(field_path))
    if len(address_blocks) != len(field_blocks):
        raise ValueError(f"processor block count mismatch for {field_path}")
    field_by_proc = {proc: block for proc, block in field_blocks}
    for proc, address_block in address_blocks:
        addresses = exact.parse_number_list(address_block, int)
        values = parse_vector_list(field_by_proc[proc])
        if len(addresses) != len(values):
            raise ValueError(f"processor {proc} address/value count mismatch for {field_path}")
        for local_i, global_cell in enumerate(addresses):
            if global_cell in selected:
                selected_values[global_cell] = values[local_i]
    missing = selected - set(selected_values)
    if missing:
        raise ValueError(f"{field_path} missing {len(missing)} selected cells")
    return selected_values


def selected_geometry(case: dict[str, str]) -> dict[str, Any]:
    seed_cells = avg.load_seed_cells(ROOT / case["recirc_cell_mask"])
    interface_rows = avg.load_interface_rows(ROOT / case["exchange_interface_faces_csv"])
    wall_rows = exact.load_wall_rows(ROOT / case["trusted_wall_faces_csv"])
    selected = set(seed_cells)
    selected.update(row["seed_owner_cell"] for row in interface_rows)
    selected.update(row["adjacent_core_cell"] for row in interface_rows)
    selected.update(row["owner"] for row in wall_rows)
    return {
        "seed_cells": seed_cells,
        "interface_rows": interface_rows,
        "wall_rows": wall_rows,
        "selected_cells": selected,
    }


def read_native_fields(case_id: str, time_window_s: str, selected: set[int]) -> dict[int, dict[str, Any]]:
    case_dir = exact.CASE_DIRS[case_id]
    time_dir = case_dir / "processors64" / time_window_s
    addressing = case_dir / "processors64/constant/polyMesh/cellProcAddressing"
    t_values = exact.read_mapped_scalar_field(time_dir / "T", addressing, selected)
    rho_values = exact.read_mapped_scalar_field(time_dir / "rho", addressing, selected)
    u_values = read_mapped_vector_field(time_dir / "U", addressing, selected)
    return {
        cell_id: {"T": t_values[cell_id], "rho": rho_values[cell_id], "U": u_values[cell_id]}
        for cell_id in selected
    }


def area_weighted_wall_temperature(rows: list[dict[str, Any]], fields: dict[int, dict[str, Any]]) -> float:
    area = sum(row["area_m2"] for row in rows)
    return sum(fields[row["owner"]]["T"] * row["area_m2"] for row in rows) / area


def sample_native_window(case: dict[str, str], time_window_s: str, window_role: str) -> dict[str, str]:
    geometry = selected_geometry(case)
    fields = read_native_fields(case["case_id"], time_window_s, geometry["selected_cells"])
    volumes = avg.load_volumes(ROOT / case["volume_csv"], geometry["seed_cells"])
    seed_avg = avg.weighted_seed_average(geometry["seed_cells"], volumes, fields)
    interface = avg.interface_reduction(case["case_id"], geometry["interface_rows"], fields)
    wall_t = area_weighted_wall_temperature(geometry["wall_rows"], fields)
    tau = seed_avg["volume_m3"] / max(interface["volumetric_positive_outward_m3_s"], EPS)
    qwall_summary, _ = exact.trusted_wall_heat_flux(
        {**case, "time_window_s": time_window_s},
        geometry["wall_rows"],
        exact.CASE_DIRS[case["case_id"]] / "processors64" / time_window_s / "wallHeatFlux",
        exact.CASE_DIRS[case["case_id"]] / "processors64/constant/polyMesh/boundary",
        exact.CASE_DIRS[case["case_id"]] / "processors64/constant/polyMesh/faceProcAddressing",
    )
    return {
        "case_id": case["case_id"],
        "window_role": window_role,
        "time_window_s": time_window_s,
        "Q_wall_W": qwall_summary["Q_wall_W"],
        "Q_wall_W_released": qwall_summary["Q_wall_W_released"],
        "Q_wall_release_status": qwall_summary["release_status"],
        "mdot_exchange_positive_outward_proxy_kg_s": fmt(interface["mdot_positive_outward_kg_s"]),
        "tau_recirc_proxy_s": fmt(tau),
        "trusted_wall_T_area_avg_K": fmt(wall_t),
        "interface_core_T_area_avg_K": fmt(interface["core_T_area_K"]),
        "seeded_cv_T_volume_avg_K": fmt(seed_avg["T_K"]),
        "delta_T_wall_minus_core_K": fmt(wall_t - interface["core_T_area_K"]),
        "delta_T_core_minus_bulk_K": fmt(interface["core_T_area_K"] - seed_avg["T_K"]),
        "delta_T_wall_minus_bulk_K": fmt(wall_t - seed_avg["T_K"]),
        "wall_core_bulk_temperature_contrast_K": fmt(wall_t - interface["core_T_area_K"]),
        "sample_status": "sampled_from_existing_native_processors64",
    }


def target_rows_from_prior() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(PRIOR_UQ / "target_qoi_evidence.csv")
    return {(row["case_id"], row["qoi_label"]): row for row in rows}


def qoi_value(row: dict[str, str], qoi_label: str) -> str:
    return row[qoi_label]


def qoi_window_rows() -> list[dict[str, str]]:
    prior = target_rows_from_prior()
    rows: list[dict[str, str]] = []
    for case in exact.case_rows():
        times = neighbor_times(case)
        sampled_minus = (
            sample_native_window(case, times["target_minus_time_window_s"], "target_minus")
            if times["target_minus_available"] == "true"
            else None
        )
        for qoi_label in qoi_labels():
            target = prior[(case["case_id"], qoi_label)]
            target_values = {
                "Q_wall_W": target["target_value"],
                "mdot_exchange_positive_outward_proxy_kg_s": target["target_value"],
                "tau_recirc_proxy_s": target["target_value"],
                "wall_core_bulk_temperature_contrast_K": target["target_value"],
            }
            minus_value = qoi_value(sampled_minus, qoi_label) if sampled_minus else ""
            rows.append(
                {
                    "case_id": case["case_id"],
                    "qoi_label": qoi_label,
                    "target_minus_time_window_s": times["target_minus_time_window_s"],
                    "target_minus_value": minus_value,
                    "target_minus_status": (
                        "sampled_from_existing_native_processors64"
                        if sampled_minus
                        else "missing_no_earlier_time_directory"
                    ),
                    "target_time_window_s": target["target_time_window_s"],
                    "target_value": target_values[qoi_label],
                    "target_status": target["target_status"],
                    "target_plus_time_window_s": times["target_plus_time_window_s"],
                    "target_plus_value": "",
                    "target_plus_status": (
                        "available_not_sampled"
                        if times["target_plus_available"] == "true"
                        else "missing_no_later_time_directory"
                    ),
                    "same_label_formula_sign_basis": "true",
                    "neighbor_window_uq_ready": "false",
                    "production_use_allowed_now": "false",
                    "source_basis": (
                        "trusted_wall_wallHeatFlux_integral"
                        if qoi_label == "Q_wall_W"
                        else "native_U_T_rho_selected_cells_and_released_geometry"
                    ),
                }
            )
    return rows


def native_window_sampling_rows(qoi_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in qoi_rows:
        key = (row["case_id"], row["target_minus_time_window_s"])
        if key in seen or not row["target_minus_time_window_s"]:
            continue
        seen.add(key)
        case_rows = [item for item in qoi_rows if item["case_id"] == row["case_id"]]
        rows.append(
            {
                "case_id": row["case_id"],
                "window_role": "target_minus",
                "time_window_s": row["target_minus_time_window_s"],
                "qoi_labels_sampled": ";".join(qoi_labels()),
                "sampled_qoi_count": str(sum(1 for item in case_rows if item["target_minus_status"].startswith("sampled"))),
                "native_processors64_read_only": "true",
                "sample_status": "complete",
            }
        )
    return rows


def same_qoi_uq_matrix_rows(qoi_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for qoi_label in qoi_labels():
        selected = [row for row in qoi_rows if row["qoi_label"] == qoi_label]
        target_ready = sum(1 for row in selected if row["target_status"])
        minus_ready = sum(1 for row in selected if row["target_minus_status"].startswith("sampled"))
        plus_ready = sum(1 for row in selected if row["target_plus_status"].startswith("sampled"))
        neighbor_ready = target_ready == 3 and minus_ready == 3 and plus_ready == 3
        rows.append(
            {
                "qoi_label": qoi_label,
                "case_count": "3",
                "target_ready_rows": str(target_ready),
                "target_minus_ready_rows": str(minus_ready),
                "target_plus_ready_rows": str(plus_ready),
                "same_qoi_neighbor_uq_ready": bool_text(neighbor_ready),
                "same_qoi_mesh_gci_status": "not_reached_target_plus_missing",
                "move_to_mesh_gci_uq_allowed_now": "false",
                "production_use_allowed_now": "false",
                "blocking_reason": "target-minus sampled, but target-plus is missing because retained targets are latest stored times",
            }
        )
    return rows


def production_gate_rows(uq_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    neighbor_ready_labels = sum(1 for row in uq_rows if row["same_qoi_neighbor_uq_ready"] == "true")
    return [
        {
            "gate": "target_minus_sampling",
            "status": "complete",
            "ready_for_next_stage": "true",
            "production_harvest_allowed_now": "false",
            "reason": "immediately preceding native time was sampled for all cases and requested QOIs",
        },
        {
            "gate": "target_plus_sampling",
            "status": "blocked_missing_later_time_directories",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": "retained target times are the latest stored time directories for Salt2/Salt3/Salt4",
        },
        {
            "gate": "same_qoi_neighbor_uq",
            "status": "blocked",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": f"{neighbor_ready_labels}/4 QOI labels have complete target-minus/target/target-plus support",
        },
        {
            "gate": "mesh_gci_uq",
            "status": "not_reached_target_plus_missing",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": "mesh/GCI should wait until the same-QOI neighbor-window gate has complete rows",
        },
        {
            "gate": "production_harvest",
            "status": "do_not_run",
            "ready_for_next_stage": "false",
            "production_harvest_allowed_now": "false",
            "reason": "same-QOI UQ remains incomplete",
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    paths: list[tuple[Path, str, str]] = [
        (PRIOR_UQ / "target_qoi_evidence.csv", "read authoritative target QOI evidence", "false"),
        (EXACT_QWALL / "trusted_wall_Q_wall_summary.csv", "read target Qwall release provenance", "false"),
        (LIMITED / "sampled_field_summary.csv", "read target sampled mdot/temperature provenance", "false"),
        (AVERAGE / "diagnostic_average_exchange_metrics.csv", "read target tau provenance", "false"),
        (SURFACE_INPUT / "seeded_surface_input_manifest.csv", "read case geometry/input manifest", "false"),
    ]
    for case in exact.case_rows():
        times = neighbor_times(case)
        case_dir = exact.CASE_DIRS[case["case_id"]]
        if times["target_minus_time_window_s"]:
            for field in ("U", "T", "rho", "wallHeatFlux"):
                paths.append(
                    (
                        case_dir / "processors64" / times["target_minus_time_window_s"] / field,
                        f"{case['case_id']} target-minus {field}",
                        "true",
                    )
                )
        paths.extend(
            [
                (ROOT / case["recirc_cell_mask"], f"{case['case_id']} seeded CV cells", "false"),
                (ROOT / case["exchange_interface_faces_csv"], f"{case['case_id']} exchange faces", "false"),
                (ROOT / case["trusted_wall_faces_csv"], f"{case['case_id']} trusted wall faces", "false"),
                (ROOT / case["volume_csv"], f"{case['case_id']} cell volumes", "false"),
                (case_dir / "processors64/constant/polyMesh/cellProcAddressing", f"{case['case_id']} cell map", "true"),
                (case_dir / "processors64/constant/polyMesh/faceProcAddressing", f"{case['case_id']} face map", "true"),
                (case_dir / "processors64/constant/polyMesh/boundary", f"{case['case_id']} boundary map", "true"),
            ]
        )
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": bool_text(path.exists()),
            "native_solver_output": native,
            "mutated": "false",
        }
        for path, role, native in paths
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "processors64 fields read only"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no scheduler action"},
        {"guard_id": "OpenFOAM_solver_postprocessing", "changed": "false", "policy": "no solver or postProcess"},
        {"guard_id": "sampler_harvest_uq_launch", "changed": "false", "policy": "no sampler, harvest, or UQ execution"},
        {"guard_id": "registry_or_admission_mutation", "changed": "false", "policy": "no registry/admission edit"},
        {"guard_id": "Q_wall_W_relabel_or_production_release", "changed": "false", "policy": "neighbor Qwall sampled only for UQ prerequisite"},
        {"guard_id": "source_side_relabel_as_Q_wall", "changed": "false", "policy": "forbidden"},
        {"guard_id": "S11_S12_S13_S15_S6_trigger", "changed": "false", "policy": "forbidden"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "changed": "false", "policy": "forbidden"},
    ]


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(PRIOR_UQ / "target_qoi_evidence.csv")}
  - {rel(SURFACE_INPUT / "seeded_surface_input_manifest.csv")}
  - {rel(out / "same_qoi_neighbor_window_rows.csv")}
tags: [s13, upcomer-exchange, qwall, neighbor-window, same-qoi-uq]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_same_qoi_neighbor_uq_execution/README.md
task: {TASK_ID}
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Qwall Neighbor-Window Sampling

Decision: `{summary["decision"]}`.

This package samples immediately preceding native time directories from
read-only `processors64` fields and joins them to the existing target-window
S13 QOI rows.

- cases: `{summary["case_count"]}`
- QOI labels: `{summary["qoi_label_count"]}`
- target rows: `{summary["target_ready_rows"]}`
- target-minus rows sampled: `{summary["target_minus_ready_rows"]}`
- target-plus rows sampled: `{summary["target_plus_ready_rows"]}`
- same-QOI neighbor UQ-ready labels: `{summary["same_qoi_neighbor_uq_ready_qois"]}`
- production harvest allowed: `{str(summary["production_harvest_allowed"]).lower()}`

The new useful result is that target-minus values now exist for all requested
case/QOI rows. The remaining blocker is target-plus: Salt2/Salt3/Salt4 retained
targets are already the latest stored native time directories, so no later
same-label window is available from the existing source tree.

Do not move to mesh/GCI UQ or production harvest from this package. First
generate or locate later target-plus windows with the same QOI labels, formulas,
sign conventions, and geometry basis.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    time_rows = [neighbor_times(case) for case in exact.case_rows()]
    qoi_rows = qoi_window_rows()
    sampled_rows = native_window_sampling_rows(qoi_rows)
    uq_rows = same_qoi_uq_matrix_rows(qoi_rows)
    gate_rows = production_gate_rows(uq_rows)
    sources = source_manifest_rows()
    guards = guardrail_rows()
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "target_minus_sampled_target_plus_missing_fail_closed",
        "case_count": len(time_rows),
        "qoi_label_count": len(qoi_labels()),
        "target_ready_rows": sum(1 for row in qoi_rows if row["target_status"]),
        "target_minus_ready_rows": sum(1 for row in qoi_rows if row["target_minus_status"].startswith("sampled")),
        "target_plus_ready_rows": sum(1 for row in qoi_rows if row["target_plus_status"].startswith("sampled")),
        "same_qoi_neighbor_uq_ready_qois": sum(1 for row in uq_rows if row["same_qoi_neighbor_uq_ready"] == "true"),
        "move_to_mesh_gci_uq_allowed_now": False,
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "native_output_mutation": False,
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
    csv_dump(out / "neighbor_time_selection.csv", list(time_rows[0]), time_rows)
    csv_dump(out / "same_qoi_neighbor_window_rows.csv", list(qoi_rows[0]), qoi_rows)
    csv_dump(out / "native_window_sampling_summary.csv", list(sampled_rows[0]), sampled_rows)
    csv_dump(out / "same_qoi_uq_matrix.csv", list(uq_rows[0]), uq_rows)
    csv_dump(out / "production_readiness_gate.csv", list(gate_rows[0]), gate_rows)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
