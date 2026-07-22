#!/usr/bin/env python3
"""Compute diagnostic S13 seeded-CV average field and thermal reductions."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract import build_s13_right_leg_geometry_seed as seed_builder
from tools.extract.openfoam_cell_volumes import face_center_and_area_vector, iter_faces, read_points

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-AVERAGE-FIELD-THERMAL-REDUCTION-2026-07-21"
OUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction"
)

CONTRACT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk"
)
SURFACE_INPUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv"
)
SOURCE_SINK = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
HEAT_PATH = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release"
UQ_DESIGN = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_same_window_uq_design"
)

CASES = ("salt_2", "salt_3", "salt_4")
VTK_FIELD_NAMES = {"cellID", "T", "rho", "U"}
EPS = 1.0e-12


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def by_case(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["case_id"]: row for row in rows}


def floats(values: Iterable[str]) -> list[float]:
    return [float(value) for value in values]


def load_seed_cells(path: Path) -> set[int]:
    return {int(row["cell_id"]) for row in read_csv(path)}


def load_volumes(path: Path, selected: set[int]) -> dict[int, float]:
    volumes: dict[int, float] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cell_id = int(row["cell_id"])
            if cell_id in selected:
                volumes[cell_id] = float(row["cellVolume_m3"])
    missing = selected - set(volumes)
    if missing:
        raise ValueError(f"{path} missing {len(missing)} selected volume rows")
    return volumes


def load_interface_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(path):
        rows.append(
            {
                "face_id": int(row["face_id"]),
                "owner": int(row["owner"]),
                "neighbour": int(row["neighbour"]),
                "seed_owner_cell": int(row["seed_owner_cell"]),
                "adjacent_core_cell": int(row["adjacent_core_cell"]),
                "area_m2": float(row["area_m2"]),
            }
        )
    return rows


def read_vtk_cell_fields(path: Path, selected: set[int]) -> dict[int, dict[str, Any]]:
    """Stream legacy VTK FIELD cell arrays and retain selected explicit cell IDs."""
    wanted = set(selected)
    tuple_to_cell: dict[int, int] = {}
    data: dict[int, dict[str, Any]] = {cell_id: {} for cell_id in wanted}
    in_cell_data = False
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        while True:
            line = handle.readline()
            if not line:
                break
            stripped = line.strip()
            if stripped.startswith("CELL_DATA "):
                in_cell_data = True
                continue
            if stripped.startswith("POINT_DATA "):
                break
            if not in_cell_data:
                continue
            parts = stripped.split()
            if len(parts) != 4:
                continue
            name = parts[0]
            components = int(parts[1])
            tuples = int(parts[2])
            total_values = components * tuples
            keep = name in VTK_FIELD_NAMES
            consumed = 0
            tuple_i = 0
            carry: list[str] = []
            while consumed < total_values:
                values = handle.readline().split()
                consumed += len(values)
                if not keep:
                    continue
                carry.extend(values)
                while len(carry) >= components and tuple_i < tuples:
                    chunk = carry[:components]
                    del carry[:components]
                    if name == "cellID":
                        cell_id = int(float(chunk[0]))
                        if cell_id in wanted:
                            tuple_to_cell[tuple_i] = cell_id
                    else:
                        cell_id = tuple_to_cell.get(tuple_i, tuple_i if tuple_i in wanted else None)
                        if cell_id in wanted:
                            if components == 1:
                                data[cell_id][name] = float(chunk[0])
                            else:
                                data[cell_id][name] = tuple(float(value) for value in chunk)
                    tuple_i += 1
            if not keep:
                continue
            while carry and tuple_i < tuples:
                chunk = carry[:components]
                del carry[:components]
                if name == "cellID":
                    cell_id = int(float(chunk[0]))
                    if cell_id in wanted:
                        tuple_to_cell[tuple_i] = cell_id
                else:
                    cell_id = tuple_to_cell.get(tuple_i, tuple_i if tuple_i in wanted else None)
                    if cell_id in wanted:
                        if components == 1:
                            data[cell_id][name] = float(chunk[0])
                        else:
                            data[cell_id][name] = tuple(float(value) for value in chunk)
                tuple_i += 1
    missing = [cell_id for cell_id, fields in data.items() if not {"T", "rho", "U"} <= set(fields)]
    if missing:
        raise ValueError(f"{path} missing VTK fields for {len(missing)} selected cells")
    return data


def vector_add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vector_scale(a: tuple[float, float, float], scale: float) -> tuple[float, float, float]:
    return (a[0] * scale, a[1] * scale, a[2] * scale)


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def mag(a: tuple[float, float, float]) -> float:
    return math.sqrt(dot(a, a))


def face_area_vectors(case_id: str, face_ids: set[int]) -> dict[int, tuple[float, float, float]]:
    poly_mesh = seed_builder.CASE_MESHES[case_id]
    points = read_points(poly_mesh / "points")
    vectors: dict[int, tuple[float, float, float]] = {}
    for face_i, vertices in enumerate(iter_faces(poly_mesh / "faces")):
        if face_i not in face_ids:
            continue
        _, area_vector = face_center_and_area_vector(vertices, points)
        vectors[face_i] = area_vector
        if len(vectors) == len(face_ids):
            break
    missing = face_ids - set(vectors)
    if missing:
        raise ValueError(f"{case_id} missing {len(missing)} face area vectors")
    return vectors


def weighted_seed_average(
    seed_cells: set[int],
    volumes: dict[int, float],
    fields: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    volume = sum(volumes.values())
    t = sum(fields[cell]["T"] * volumes[cell] for cell in seed_cells) / volume
    rho = sum(fields[cell]["rho"] * volumes[cell] for cell in seed_cells) / volume
    u = (0.0, 0.0, 0.0)
    for cell in seed_cells:
        u = vector_add(u, vector_scale(fields[cell]["U"], volumes[cell]))
    u = vector_scale(u, 1.0 / volume)
    return {"volume_m3": volume, "T_K": t, "rho_kg_m3": rho, "U_m_s": u}


def interface_reduction(
    case_id: str,
    rows: list[dict[str, Any]],
    fields: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    area_vectors = face_area_vectors(case_id, {row["face_id"] for row in rows})
    area_sum = sum(row["area_m2"] for row in rows)
    seed_t = core_t = seed_rho = core_rho = 0.0
    seed_u = core_u = (0.0, 0.0, 0.0)
    mdot_net = mdot_pos = mdot_neg = vol_pos = 0.0
    for row in rows:
        area = row["area_m2"]
        seed = row["seed_owner_cell"]
        core = row["adjacent_core_cell"]
        seed_fields = fields[seed]
        core_fields = fields[core]
        seed_t += seed_fields["T"] * area
        core_t += core_fields["T"] * area
        seed_rho += seed_fields["rho"] * area
        core_rho += core_fields["rho"] * area
        seed_u = vector_add(seed_u, vector_scale(seed_fields["U"], area))
        core_u = vector_add(core_u, vector_scale(core_fields["U"], area))
        outward_area = area_vectors[row["face_id"]]
        if row["seed_owner_cell"] == row["neighbour"]:
            outward_area = vector_scale(outward_area, -1.0)
        u_face = vector_scale(vector_add(seed_fields["U"], core_fields["U"]), 0.5)
        rho_face = 0.5 * (seed_fields["rho"] + core_fields["rho"])
        mdot = rho_face * dot(u_face, outward_area)
        mdot_net += mdot
        if mdot >= 0.0:
            mdot_pos += mdot
            vol_pos += mdot / max(rho_face, EPS)
        else:
            mdot_neg += mdot
    return {
        "area_m2": area_sum,
        "seed_T_area_K": seed_t / area_sum,
        "core_T_area_K": core_t / area_sum,
        "seed_rho_area_kg_m3": seed_rho / area_sum,
        "core_rho_area_kg_m3": core_rho / area_sum,
        "seed_U_area_m_s": vector_scale(seed_u, 1.0 / area_sum),
        "core_U_area_m_s": vector_scale(core_u, 1.0 / area_sum),
        "mdot_net_kg_s": mdot_net,
        "mdot_positive_outward_kg_s": mdot_pos,
        "mdot_negative_inward_kg_s": mdot_neg,
        "volumetric_positive_outward_m3_s": vol_pos,
    }


def case_reduction(case: dict[str, str]) -> dict[str, Any]:
    case_id = case["case_id"]
    seed_cells = load_seed_cells(ROOT / case["recirc_cell_mask"])
    interface_rows = load_interface_rows(ROOT / case["exchange_interface_faces_csv"])
    selected = set(seed_cells)
    selected.update(row["adjacent_core_cell"] for row in interface_rows)
    selected.update(row["seed_owner_cell"] for row in interface_rows)
    volumes = load_volumes(ROOT / case["volume_csv"], seed_cells)
    fields = read_vtk_cell_fields(ROOT / case["cell_vtk"], selected)
    seed_avg = weighted_seed_average(seed_cells, volumes, fields)
    interface = interface_reduction(case_id, interface_rows, fields)
    q_net = float(case["q_net_W"])
    delta_t = interface["core_T_area_K"] - seed_avg["T_K"]
    h_a = abs(q_net) / max(abs(delta_t), EPS)
    tau = seed_avg["volume_m3"] / max(interface["volumetric_positive_outward_m3_s"], EPS)
    u_seed = seed_avg["U_m_s"]
    u_seed_interface = interface["seed_U_area_m_s"]
    u_core = interface["core_U_area_m_s"]
    return {
        "case_id": case_id,
        "time_window_s": case["time_window_s"],
        "diagnostic_basis": "diagnostic_average_proxy_not_production_harvest",
        "seed_cell_count": len(seed_cells),
        "seeded_cv_volume_m3": f"{seed_avg['volume_m3']:.12g}",
        "seed_T_volume_avg_K": f"{seed_avg['T_K']:.12g}",
        "seed_rho_volume_avg_kg_m3": f"{seed_avg['rho_kg_m3']:.12g}",
        "seed_Ux_volume_avg_m_s": f"{u_seed[0]:.12g}",
        "seed_Uy_volume_avg_m_s": f"{u_seed[1]:.12g}",
        "seed_Uz_volume_avg_m_s": f"{u_seed[2]:.12g}",
        "seed_Umag_volume_avg_m_s": f"{mag(u_seed):.12g}",
        "interface_face_count": len(interface_rows),
        "interface_area_m2": f"{interface['area_m2']:.12g}",
        "seed_interface_T_area_avg_K": f"{interface['seed_T_area_K']:.12g}",
        "seed_interface_rho_area_avg_kg_m3": f"{interface['seed_rho_area_kg_m3']:.12g}",
        "seed_interface_Ux_area_avg_m_s": f"{u_seed_interface[0]:.12g}",
        "seed_interface_Uy_area_avg_m_s": f"{u_seed_interface[1]:.12g}",
        "seed_interface_Uz_area_avg_m_s": f"{u_seed_interface[2]:.12g}",
        "seed_interface_Umag_area_avg_m_s": f"{mag(u_seed_interface):.12g}",
        "core_T_area_avg_K": f"{interface['core_T_area_K']:.12g}",
        "core_rho_area_avg_kg_m3": f"{interface['core_rho_area_kg_m3']:.12g}",
        "core_Ux_area_avg_m_s": f"{u_core[0]:.12g}",
        "core_Uy_area_avg_m_s": f"{u_core[1]:.12g}",
        "core_Uz_area_avg_m_s": f"{u_core[2]:.12g}",
        "core_Umag_area_avg_m_s": f"{mag(u_core):.12g}",
        "mdot_exchange_net_proxy_kg_s": f"{interface['mdot_net_kg_s']:.12g}",
        "mdot_exchange_positive_outward_proxy_kg_s": f"{interface['mdot_positive_outward_kg_s']:.12g}",
        "mdot_exchange_negative_inward_proxy_kg_s": f"{interface['mdot_negative_inward_kg_s']:.12g}",
        "volumetric_exchange_positive_outward_proxy_m3_s": f"{interface['volumetric_positive_outward_m3_s']:.12g}",
        "tau_recirc_proxy_s": f"{tau:.12g}",
        "q_source_W": case["q_source_W"],
        "q_sink_W": case["q_sink_W"],
        "q_net_W": case["q_net_W"],
        "delta_T_core_minus_seed_K": f"{delta_t:.12g}",
        "hA_source_side_proxy_W_K": f"{h_a:.12g}",
        "Q_wall_W_released": "false",
        "pressure_residual_ready": "false",
        "energy_residual_ready": "false",
        "same_qoi_uq_ready": "false",
        "sampler_ready": "false",
        "admission_allowed": "false",
        "release_status": "diagnostic_average_proxy_only",
    }


def average_field_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    columns = [
        "case_id",
        "time_window_s",
        "diagnostic_basis",
        "seed_cell_count",
        "seeded_cv_volume_m3",
        "seed_T_volume_avg_K",
        "seed_rho_volume_avg_kg_m3",
        "seed_Ux_volume_avg_m_s",
        "seed_Uy_volume_avg_m_s",
        "seed_Uz_volume_avg_m_s",
        "seed_Umag_volume_avg_m_s",
        "pressure_residual_ready",
        "same_qoi_uq_ready",
        "sampler_ready",
        "admission_allowed",
        "release_status",
    ]
    return [{column: row[column] for column in columns} for row in case_rows]


def interface_proxy_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    columns = [
        "case_id",
        "time_window_s",
        "diagnostic_basis",
        "interface_face_count",
        "interface_area_m2",
        "seed_interface_T_area_avg_K",
        "seed_interface_rho_area_avg_kg_m3",
        "seed_interface_Ux_area_avg_m_s",
        "seed_interface_Uy_area_avg_m_s",
        "seed_interface_Uz_area_avg_m_s",
        "seed_interface_Umag_area_avg_m_s",
        "core_T_area_avg_K",
        "core_rho_area_avg_kg_m3",
        "core_Ux_area_avg_m_s",
        "core_Uy_area_avg_m_s",
        "core_Uz_area_avg_m_s",
        "core_Umag_area_avg_m_s",
        "mdot_exchange_net_proxy_kg_s",
        "mdot_exchange_positive_outward_proxy_kg_s",
        "mdot_exchange_negative_inward_proxy_kg_s",
        "volumetric_exchange_positive_outward_proxy_m3_s",
        "pressure_residual_ready",
        "same_qoi_uq_ready",
        "sampler_ready",
        "admission_allowed",
        "release_status",
    ]
    return [{column: row[column] for column in columns} for row in case_rows]


def thermal_proxy_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    columns = [
        "case_id",
        "time_window_s",
        "diagnostic_basis",
        "seeded_cv_volume_m3",
        "q_source_W",
        "q_sink_W",
        "q_net_W",
        "delta_T_core_minus_seed_K",
        "tau_recirc_proxy_s",
        "hA_source_side_proxy_W_K",
        "Q_wall_W_released",
        "energy_residual_ready",
        "same_qoi_uq_ready",
        "sampler_ready",
        "admission_allowed",
        "release_status",
    ]
    return [{column: row[column] for column in columns} for row in case_rows]


def missing_gate_rows() -> list[dict[str, str]]:
    gates = [
        ("pressure_basis", "p_or_p_rgh missing from cell VTK field inventory"),
        ("mu_or_nu_basis", "mu/nu/nut missing from cell VTK field inventory"),
        ("wallHeatFlux_Q_wall_W", "wallHeatFlux and Q_wall_W integration absent"),
        ("cp_property_basis", "cp_J_kg_K not released"),
        ("same_qoi_uq", "same-QOI UQ absent for reduced exchange QOIs"),
        ("production_sampler_harvest", "sampler-ready rows remain zero"),
        ("coefficient_admission", "fit/admission forbidden for diagnostic average proxy"),
    ]
    return [
        {
            "gate": gate,
            "status": "blocked",
            "blocking_reason": reason,
            "diagnostic_average_proxy_allows_progress": "true" if gate in {"pressure_basis", "mu_or_nu_basis", "wallHeatFlux_Q_wall_W", "cp_property_basis"} else "false",
        }
        for gate, reason in gates
    ]


def downstream_rows() -> list[dict[str, str]]:
    return [
        {
            "gate": "sampler_manifest_refresh",
            "status": "blocked",
            "allowed": "false",
            "reason": "average proxy is not sampled-surface production evidence and Q_wall_W/UQ remain absent",
        },
        {
            "gate": "production_harvest",
            "status": "blocked",
            "allowed": "false",
            "reason": "no production sampler-ready rows or same-QOI UQ",
        },
        {
            "gate": "s12_evidence_use",
            "status": "diagnostic_context_only",
            "allowed": "true",
            "reason": "average proxy can inform S12 negative/diagnostic discussion but not release a candidate",
        },
        {
            "gate": "coefficient_or_downstream_trigger",
            "status": "blocked",
            "allowed": "false",
            "reason": "diagnostic average proxy is nonadmissible",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read-only native and package inputs"},
        {"guard_id": "registry_or_admission_mutation", "changed": "false", "policy": "no registry/admission edit"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "local parser only"},
        {"guard_id": "solver_postprocessing_surface_field_sampling", "changed": "false", "policy": "no OpenFOAM/sampler extraction"},
        {"guard_id": "sampler_harvest_uq", "changed": "false", "policy": "sampler/harvest/UQ remain blocked"},
        {"guard_id": "coefficient_or_model_selection", "changed": "false", "policy": "no fit/model selection/admission"},
        {"guard_id": "residual_absorbed_into_internal_Nu", "changed": "false", "policy": "residual remains explicit and non-fitted"},
    ]


def source_manifest_rows() -> list[dict[str, Any]]:
    paths = [
        (CONTRACT / "summary.json", "read sampled-field/Qwall contract"),
        (SURFACE_INPUT / "seeded_surface_input_manifest.csv", "read surface input manifest"),
        (HEAT_PATH / "field_inventory.csv", "read field inventory"),
        (SOURCE_SINK / "source_sink_summary.csv", "read source/sink context"),
        (UQ_DESIGN / "summary.json", "read UQ status"),
    ]
    for case_id in CASES:
        paths.append((seed_builder.CASE_MESHES[case_id], f"read {case_id} native polyMesh topology"))
    return [
        {
            "path": rel(path),
            "role": role,
            "exists": str(path.exists()).lower(),
            "native_solver_output": str("polyMesh" in str(path)).lower(),
            "mutated": "false",
        }
        for path, role in paths
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(CONTRACT / "summary.json")}
  - {rel(SURFACE_INPUT / "seeded_surface_input_manifest.csv")}
tags: [s13, upcomer-exchange, diagnostic-average, thermal-reduction]
related:
  - .agent/status/2026-07-21_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Diagnostic Average Field Thermal Reduction

This package computes diagnostic average reductions from existing whole-mesh
cell VTK `cellID`, `U`, `T`, and `rho` fields over the released seeded CV and
seed/core interface. It also reads OpenFOAM face area vectors to produce a
signed outward interface mass-flux proxy under the seeded-CV outward convention.
It is not a production sampler harvest.

Result: `{summary["decision"]}`.

- cases reduced: `{summary["case_count"]}`
- diagnostic metric rows: `{summary["diagnostic_metric_rows"]}`
- average-field rows: `{summary["average_field_rows"]}`
- interface-proxy rows: `{summary["interface_proxy_rows"]}`
- thermal-proxy rows: `{summary["thermal_proxy_rows"]}`
- sampler-ready rows: `{summary["sampler_ready_rows"]}`
- admission-ready rows: `{summary["admission_ready_rows"]}`

The result supports continued S13/S12 diagnostic reasoning, but sampler
refresh, production harvest, same-QOI UQ, and coefficient admission remain
blocked.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build(out_dir: Path = OUT) -> dict[str, Any]:
    ensure_dir(out_dir)
    cases = read_csv(SURFACE_INPUT / "seeded_surface_input_manifest.csv")
    case_rows = [case_reduction(case) for case in cases]
    average_rows = average_field_rows(case_rows)
    interface_rows = interface_proxy_rows(case_rows)
    thermal_rows = thermal_proxy_rows(case_rows)
    missing = missing_gate_rows()
    downstream = downstream_rows()
    guards = guardrail_rows()
    manifest = source_manifest_rows()
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "diagnostic_average_proxy_complete_sampler_harvest_blocked",
        "case_count": len(case_rows),
        "diagnostic_metric_rows": len(case_rows),
        "average_field_rows": len(average_rows),
        "interface_proxy_rows": len(interface_rows),
        "thermal_proxy_rows": len(thermal_rows),
        "sampler_ready_rows": sum(1 for row in case_rows if row["sampler_ready"] == "true"),
        "admission_ready_rows": sum(1 for row in case_rows if row["admission_allowed"] == "true"),
        "missing_gate_rows": len(missing),
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_or_postprocessing_or_sampling_launched": False,
        "sampler_or_harvest_launched": False,
        "same_qoi_uq_released": False,
        "coefficient_admission": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    csv_dump(out_dir / "diagnostic_average_exchange_metrics.csv", list(case_rows[0]), case_rows)
    csv_dump(out_dir / "average_field_reduction.csv", list(average_rows[0]), average_rows)
    csv_dump(out_dir / "interface_proxy_reduction.csv", list(interface_rows[0]), interface_rows)
    csv_dump(out_dir / "thermal_proxy_reduction.csv", list(thermal_rows[0]), thermal_rows)
    csv_dump(out_dir / "missing_gate_matrix.csv", list(missing[0]), missing)
    csv_dump(out_dir / "downstream_gate.csv", list(downstream[0]), downstream)
    csv_dump(out_dir / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out_dir / "source_manifest.csv", list(manifest[0]), manifest)
    json_dump(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
