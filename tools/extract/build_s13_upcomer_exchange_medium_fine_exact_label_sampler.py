#!/usr/bin/env python3
"""Build and execute the S13 medium/fine exact-label sampler.

The source cases are read-only collated OpenFOAM processor directories. This
script rebuilds the S13 right-leg recirculation control-volume geometry from
each mesh, then samples the terminal candidate windows named by the completed
medium/fine sampling contract. It does not mutate native solver outputs, run
OpenFOAM post-processing, fit coefficients, refresh production manifests, or
admit model forms.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze import build_s13_upcomer_exchange_qwall_neighbor_window_sampling as neighbor
from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace
from tools.extract import build_s13_right_leg_geometry_seed as seed_builder
from tools.extract import build_s13_upcomer_exchange_exact_pressure_qwall_compute as exact
from tools.extract import build_s13_upcomer_exchange_topology_cv_release as topo
from tools.extract.openfoam_cell_volumes import (
    compute_cell_volumes_streaming_from_mesh,
    face_center_and_area_vector,
    iter_faces,
    read_points,
)

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-EXACT-LABEL-SAMPLER-2026-07-22"
OUT = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler"
)
CONTRACT_PACKAGE = ROOT / (
    "work_products/2026-07/2026-07-22/"
    "2026-07-22_s13_upcomer_exchange_medium_fine_same_label_sampling"
)
CURRENT_COARSE_EXACT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"
)

QOI_LABELS = (
    "Q_wall_W",
    "mdot_exchange_positive_outward_proxy_kg_s",
    "tau_recirc_proxy_s",
    "wall_core_bulk_temperature_contrast_K",
)
EPS = 1.0e-12


@dataclass
class MeshGeometry:
    case_id: str
    mesh_level: str
    source_root: Path
    processors_dir: Path
    poly_mesh: Path
    seed_cells: set[int]
    volumes: dict[int, float]
    interface_rows: list[dict[str, Any]]
    wall_rows: list[dict[str, Any]]
    cap_rows: list[dict[str, Any]]
    summary: dict[str, Any]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def bool_text(value: bool) -> str:
    return str(value).lower()


def fmt(value: float) -> str:
    return f"{value:.12g}" if math.isfinite(value) else ""


def dump_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    csv_dump(path, fieldnames, rows)


def split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def contract_rows() -> list[dict[str, str]]:
    return read_csv(CONTRACT_PACKAGE / "sampling_command_contract.csv")


def filtered_contract_rows(
    rows: list[dict[str, str]],
    *,
    case_id: str = "",
    mesh_level: str = "",
) -> list[dict[str, str]]:
    out = [
        row
        for row in rows
        if (not case_id or row["case_id"] == case_id)
        and (not mesh_level or row["mesh_level"] == mesh_level)
    ]
    if not out:
        raise ValueError(f"no contract rows matched case_id={case_id or '*'} mesh_level={mesh_level or '*'}")
    return out


def limited_windows(row: dict[str, str], max_windows: int = 0) -> list[str]:
    times = split_semicolon(row["fallback_terminal_candidate_windows_s"])
    return times[:max_windows] if max_windows > 0 else times


def qoi_value(row: dict[str, Any], qoi_label: str) -> str:
    if qoi_label == "wall_core_bulk_temperature_contrast_K":
        return row["wall_core_bulk_temperature_contrast_K"]
    return row[qoi_label]


def processor_count(processors_dir: Path) -> str:
    name = processors_dir.name
    return name.replace("processors", "") if name.startswith("processors") else ""


def source_preflight_rows(rows: list[dict[str, str]], max_windows: int = 0) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        source_root = Path(row["source_root"])
        processors_dir = Path(row["processors_dir"])
        poly_mesh = source_root / "constant/polyMesh"
        times = limited_windows(row, max_windows)
        required_paths = [
            poly_mesh / "points",
            poly_mesh / "faces",
            poly_mesh / "owner",
            poly_mesh / "neighbour",
            poly_mesh / "boundary",
            processors_dir / "constant/polyMesh/cellProcAddressing",
            processors_dir / "constant/polyMesh/faceProcAddressing",
            processors_dir / "constant/polyMesh/boundary",
        ]
        missing = [str(path) for path in required_paths if not path.exists()]
        for time in times:
            for field in ("T", "rho", "U", "wallHeatFlux"):
                path = processors_dir / time / field
                if not path.exists():
                    missing.append(str(path))
        out.append(
            {
                "case_id": row["case_id"],
                "mesh_level": row["mesh_level"],
                "source_root": str(source_root),
                "processors_dir": str(processors_dir),
                "processor_count": processor_count(processors_dir),
                "terminal_candidate_windows_s": ";".join(times),
                "strict_contract_windows_s": row["strict_contract_windows_s"],
                "strict_contract_windows_available": row["strict_contract_windows_available"],
                "required_paths_missing_count": len(missing),
                "required_paths_missing": ";".join(missing[:10]),
                "preflight_status": "ready_for_compute_node_sampling" if not missing else "blocked_missing_required_native_path",
                "native_solver_output_mutated": "false",
            }
        )
    return out


def seed_case_id(case_id: str, mesh_level: str) -> str:
    return f"{case_id}_{mesh_level}"


def lane_rows(seed: seed_builder.CaseSeed, lane: str) -> list[dict[str, Any]]:
    return [row for row in seed.lane_rows if row["lane"] == lane]


def selected_face_area_vectors(
    poly_mesh: Path,
    selected_face_ids: set[int],
    points: list[tuple[float, float, float]],
) -> dict[int, tuple[float, float, float]]:
    if not selected_face_ids:
        return {}
    vectors: dict[int, tuple[float, float, float]] = {}
    for face_i, vertices in enumerate(iter_faces(poly_mesh / "faces")):
        if face_i not in selected_face_ids:
            continue
        _, area_vector = face_center_and_area_vector(vertices, points)
        vectors[face_i] = area_vector
        if len(vectors) == len(selected_face_ids):
            break
    missing = selected_face_ids - set(vectors)
    if missing:
        raise ValueError(f"{poly_mesh} missing {len(missing)} selected face area vectors")
    return vectors


def add_area_vector_columns(
    row: dict[str, Any],
    area_vector: tuple[float, float, float],
) -> dict[str, Any]:
    return {
        **row,
        "area_vector_x_m2": float(area_vector[0]),
        "area_vector_y_m2": float(area_vector[1]),
        "area_vector_z_m2": float(area_vector[2]),
    }


def build_mesh_geometry(row: dict[str, str], out_dir: Path) -> MeshGeometry:
    case_id = row["case_id"]
    mesh_level = row["mesh_level"]
    source_root = Path(row["source_root"])
    processors_dir = Path(row["processors_dir"])
    poly_mesh = source_root / "constant/polyMesh"
    case_mesh_id = seed_case_id(case_id, mesh_level)

    points = read_points(poly_mesh / "points")
    patches = topo.parse_boundary_patches((poly_mesh / "boundary").read_text(encoding="utf-8", errors="replace"))
    patch_names = {patch.name for patch in patches}
    missing_patches = set(seed_builder.TRUSTED_WALL_PATCHES) - patch_names
    if missing_patches:
        raise ValueError(f"{case_mesh_id} missing trusted wall patches: {sorted(missing_patches)}")

    face_patches = seed_builder.patch_lookup(patches)
    bounds, _, _ = seed_builder.trusted_patch_bounds(poly_mesh, face_patches, points)
    seed_cells = seed_builder.collect_wall_seed_cells(case_mesh_id, poly_mesh, face_patches)
    volumes_all, volume_summary = compute_cell_volumes_streaming_from_mesh(poly_mesh)
    volumes = {cell_id: volumes_all[cell_id] for cell_id in seed_cells}

    seed = seed_builder.CaseSeed(case_id=case_mesh_id, bounds=bounds, wall_seed_cells=set(seed_cells))
    seed.seed_cells = set(seed_cells)
    seed.seed_volume_m3 = sum(volumes.values())
    seed_builder.classify_seed_faces(seed, poly_mesh, face_patches, points)
    release_status, blocking_reason = seed_builder.release_decision(seed)

    internal_rows = lane_rows(seed, "internal_interface")
    wall_lane_rows = lane_rows(seed, "trusted_wall")
    cap_lane_rows = lane_rows(seed, "cap_or_open_boundary")
    vector_by_face = selected_face_area_vectors(
        poly_mesh,
        {int(item["face_id"]) for item in internal_rows + wall_lane_rows + cap_lane_rows},
        points,
    )

    interface_rows = []
    for item in internal_rows:
        face_id = int(item["face_id"])
        owner = int(item["owner"])
        neighbour_cell = int(item["neighbour"])
        owner_in = owner in seed_cells
        seed_owner = owner if owner_in else neighbour_cell
        adjacent = neighbour_cell if owner_in else owner
        interface_rows.append(
            add_area_vector_columns(
                {
                    "case_id": case_id,
                    "mesh_level": mesh_level,
                    "mesh_mask_id": case_mesh_id,
                    "face_id": face_id,
                    "owner": owner,
                    "neighbour": neighbour_cell,
                    "seed_owner_cell": seed_owner,
                    "adjacent_core_cell": adjacent,
                    "area_m2": float(item["area_m2"]),
                    "center_x_m": item["center_x_m"],
                    "center_y_m": item["center_y_m"],
                    "center_z_m": item["center_z_m"],
                    "normal_convention": "OpenFOAM owner-to-neighbour; positive outward from seeded CV computed from seed_owner/adjacent orientation",
                    "release_status": release_status,
                },
                vector_by_face[face_id],
            )
        )

    wall_rows = [
        add_area_vector_columns(
            {
                "case_id": case_id,
                "mesh_level": mesh_level,
                "mesh_mask_id": case_mesh_id,
                "face_id": int(item["face_id"]),
                "patch_name": item["patch_name"],
                "owner": int(item["owner"]),
                "area_m2": float(item["area_m2"]),
                "center_x_m": item["center_x_m"],
                "center_y_m": item["center_y_m"],
                "center_z_m": item["center_z_m"],
                "normal_convention": "native wall patch orientation; Q_wall_W uses negative OpenFOAM outward wallHeatFlux integral",
                "release_status": release_status,
            },
            vector_by_face[int(item["face_id"])],
        )
        for item in wall_lane_rows
    ]
    cap_rows = [
        add_area_vector_columns(
            {
                "case_id": case_id,
                "mesh_level": mesh_level,
                "mesh_mask_id": case_mesh_id,
                **item,
                "release_status": release_status,
            },
            vector_by_face[int(item["face_id"])],
        )
        for item in cap_lane_rows
    ]

    mask_dir = ensure_dir(out_dir / "masks")
    face_dir = ensure_dir(out_dir / "faces")
    dump_csv(
        mask_dir / f"{case_mesh_id}_recirc_cv_cells.csv",
        [
            {
                "case_id": case_id,
                "mesh_level": mesh_level,
                "mesh_mask_id": case_mesh_id,
                "cell_id": cell_id,
                "seed_role": "trusted_wall_adjacent_cell",
                "cellVolume_m3": fmt(abs(volumes[cell_id])),
                "source_polyMesh": str(poly_mesh),
            }
            for cell_id in sorted(seed_cells)
        ],
    )
    dump_csv(face_dir / f"{case_mesh_id}_exchange_interface_faces.csv", interface_rows)
    dump_csv(face_dir / f"{case_mesh_id}_trusted_wall_faces.csv", wall_rows)
    dump_csv(face_dir / f"{case_mesh_id}_cap_faces.csv", cap_rows)

    summary = {
        "case_id": case_id,
        "mesh_level": mesh_level,
        "mesh_mask_id": case_mesh_id,
        "source_root": str(source_root),
        "processors_dir": str(processors_dir),
        "poly_mesh": str(poly_mesh),
        "cell_count": volume_summary.get("n_cells", ""),
        "face_count": volume_summary.get("n_faces", ""),
        "seed_cell_count": len(seed_cells),
        "seed_volume_m3": fmt(sum(abs(value) for value in volumes.values())),
        "trusted_wall_face_count": len(wall_rows),
        "trusted_wall_area_m2": fmt(sum(row["area_m2"] for row in wall_rows)),
        "internal_interface_face_count": len(interface_rows),
        "internal_interface_area_m2": fmt(sum(row["area_m2"] for row in interface_rows)),
        "cap_face_count": len(cap_rows),
        "escape_face_count": seed.escape_face_count,
        "geometry_release_status": release_status,
        "blocking_reason": blocking_reason,
        "native_solver_output_mutated": "false",
    }
    return MeshGeometry(
        case_id=case_id,
        mesh_level=mesh_level,
        source_root=source_root,
        processors_dir=processors_dir,
        poly_mesh=poly_mesh,
        seed_cells=set(seed_cells),
        volumes={cell_id: abs(value) for cell_id, value in volumes.items()},
        interface_rows=interface_rows,
        wall_rows=wall_rows,
        cap_rows=cap_rows,
        summary=summary,
    )


def selected_cells(geometry: MeshGeometry) -> set[int]:
    selected = set(geometry.seed_cells)
    selected.update(row["seed_owner_cell"] for row in geometry.interface_rows)
    selected.update(row["adjacent_core_cell"] for row in geometry.interface_rows)
    selected.update(row["owner"] for row in geometry.wall_rows)
    return selected


def read_native_fields(geometry: MeshGeometry, time_window_s: str) -> dict[int, dict[str, Any]]:
    selected = selected_cells(geometry)
    time_dir = geometry.processors_dir / time_window_s
    addressing = geometry.processors_dir / "constant/polyMesh/cellProcAddressing"
    t_values = exact.read_mapped_scalar_field(time_dir / "T", addressing, selected)
    rho_values = exact.read_mapped_scalar_field(time_dir / "rho", addressing, selected)
    u_values = neighbor.read_mapped_vector_field(time_dir / "U", addressing, selected)
    return {
        cell_id: {"T": t_values[cell_id], "rho": rho_values[cell_id], "U": u_values[cell_id]}
        for cell_id in selected
    }


def wall_temperature(rows: list[dict[str, Any]], fields: dict[int, dict[str, Any]]) -> float:
    area = sum(float(row["area_m2"]) for row in rows)
    if area <= 0.0:
        raise ValueError("nonpositive trusted wall area")
    return sum(fields[int(row["owner"])]["T"] * float(row["area_m2"]) for row in rows) / area


def weighted_seed_average(geometry: MeshGeometry, fields: dict[int, dict[str, Any]]) -> dict[str, float]:
    volume = sum(geometry.volumes[cell_id] for cell_id in geometry.seed_cells)
    if volume <= 0.0:
        raise ValueError("nonpositive seeded CV volume")
    t = sum(fields[cell_id]["T"] * geometry.volumes[cell_id] for cell_id in geometry.seed_cells) / volume
    rho = sum(fields[cell_id]["rho"] * geometry.volumes[cell_id] for cell_id in geometry.seed_cells) / volume
    return {"volume_m3": volume, "T_K": t, "rho_kg_m3": rho}


def vector_add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vector_scale(a: tuple[float, float, float], scale: float) -> tuple[float, float, float]:
    return (a[0] * scale, a[1] * scale, a[2] * scale)


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def interface_area_vector(row: dict[str, Any]) -> tuple[float, float, float]:
    return (
        float(row["area_vector_x_m2"]),
        float(row["area_vector_y_m2"]),
        float(row["area_vector_z_m2"]),
    )


def interface_reduction(
    rows: list[dict[str, Any]],
    fields: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    missing = [
        row["face_id"]
        for row in rows
        if not all(key in row for key in ("area_vector_x_m2", "area_vector_y_m2", "area_vector_z_m2"))
    ]
    if missing:
        raise ValueError(f"interface rows missing area vectors: {len(missing)}")
    area_sum = sum(float(row["area_m2"]) for row in rows)
    if area_sum <= 0.0:
        raise ValueError("nonpositive interface area")
    seed_t = core_t = seed_rho = core_rho = 0.0
    seed_u = core_u = (0.0, 0.0, 0.0)
    mdot_net = mdot_pos = mdot_neg = vol_pos = 0.0
    for row in rows:
        area = float(row["area_m2"])
        seed = int(row["seed_owner_cell"])
        core = int(row["adjacent_core_cell"])
        seed_fields = fields[seed]
        core_fields = fields[core]
        seed_t += seed_fields["T"] * area
        core_t += core_fields["T"] * area
        seed_rho += seed_fields["rho"] * area
        core_rho += core_fields["rho"] * area
        seed_u = vector_add(seed_u, vector_scale(seed_fields["U"], area))
        core_u = vector_add(core_u, vector_scale(core_fields["U"], area))
        outward_area = interface_area_vector(row)
        if seed == int(row["neighbour"]):
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


def sample_window(geometry: MeshGeometry, time_window_s: str, window_role: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fields = read_native_fields(geometry, time_window_s)
    seed_avg = weighted_seed_average(geometry, fields)
    interface = interface_reduction(geometry.interface_rows, fields)
    trusted_wall_t = wall_temperature(geometry.wall_rows, fields)
    tau = seed_avg["volume_m3"] / max(interface["volumetric_positive_outward_m3_s"], EPS)
    qwall_summary, qwall_detail = exact.trusted_wall_heat_flux(
        {"case_id": geometry.case_id, "time_window_s": time_window_s},
        geometry.wall_rows,
        geometry.processors_dir / time_window_s / "wallHeatFlux",
        geometry.processors_dir / "constant/polyMesh/boundary",
        geometry.processors_dir / "constant/polyMesh/faceProcAddressing",
    )
    reduction = {
        "case_id": geometry.case_id,
        "mesh_level": geometry.mesh_level,
        "mesh_mask_id": seed_case_id(geometry.case_id, geometry.mesh_level),
        "window_role": window_role,
        "time_window_s": time_window_s,
        "source_root": str(geometry.source_root),
        "processors_dir": str(geometry.processors_dir),
        "seeded_cv_cell_count": len(geometry.seed_cells),
        "interface_face_count": len(geometry.interface_rows),
        "trusted_wall_face_count": len(geometry.wall_rows),
        "seeded_cv_volume_m3": fmt(seed_avg["volume_m3"]),
        "seeded_cv_T_volume_avg_K": fmt(seed_avg["T_K"]),
        "seeded_cv_rho_volume_avg_kg_m3": fmt(seed_avg["rho_kg_m3"]),
        "interface_seed_T_area_avg_K": fmt(interface["seed_T_area_K"]),
        "interface_core_T_area_avg_K": fmt(interface["core_T_area_K"]),
        "trusted_wall_T_area_avg_K": fmt(trusted_wall_t),
        "wall_core_bulk_temperature_contrast_K": fmt(trusted_wall_t - interface["core_T_area_K"]),
        "mdot_exchange_positive_outward_proxy_kg_s": fmt(interface["mdot_positive_outward_kg_s"]),
        "volumetric_exchange_positive_outward_m3_s": fmt(interface["volumetric_positive_outward_m3_s"]),
        "tau_recirc_proxy_s": fmt(tau),
        "Q_wall_W": qwall_summary["Q_wall_W"],
        "Q_wall_W_released": qwall_summary["Q_wall_W_released"],
        "Q_wall_release_status": qwall_summary["release_status"],
        "sample_status": "terminal_exact_label_sampled_from_read_only_native_processors",
    }
    return reduction, qwall_detail


def qoi_rows(window_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in window_rows:
        for label in QOI_LABELS:
            out.append(
                {
                    "case_id": row["case_id"],
                    "mesh_level": row["mesh_level"],
                    "qoi_label": label,
                    "window_role": row["window_role"],
                    "time_window_s": row["time_window_s"],
                    "value": qoi_value(row, label),
                    "unit": {
                        "Q_wall_W": "W",
                        "mdot_exchange_positive_outward_proxy_kg_s": "kg/s",
                        "tau_recirc_proxy_s": "s",
                        "wall_core_bulk_temperature_contrast_K": "K",
                    }[label],
                    "geometry_mask_id": row["mesh_mask_id"],
                    "source_family": "TAMU_Salt2_Salt3_Salt4_medium_fine_terminal_candidate_native_OpenFOAM13",
                    "pressure_velocity_basis": "U and rho sampled on mesh-level exchange-interface adjacent cells; Q_wall_W from trusted-wall wallHeatFlux faces",
                    "admission_status": "diagnostic_only_mesh_time_equivalence_gate_pending",
                    "release_status": row["sample_status"],
                }
            )
    return out


def mesh_gci_gate_rows(sampled_qois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current_qwall = read_csv(CURRENT_COARSE_EXACT / "trusted_wall_Q_wall_summary.csv")
    current_cases = {row["case_id"] for row in current_qwall}
    for label in QOI_LABELS:
        label_rows = [row for row in sampled_qois if row["qoi_label"] == label]
        case_mesh = {(row["case_id"], row["mesh_level"]) for row in label_rows}
        rows.append(
            {
                "qoi_label": label,
                "current_coarse_case_count": len(current_cases),
                "medium_fine_case_mesh_count": len(case_mesh),
                "medium_fine_terminal_window_row_count": len(label_rows),
                "strict_coarse_contract_windows_available_in_medium_fine": "false",
                "terminal_window_equivalence_source_exists": "false",
                "same_label_mesh_gci_ready": "false",
                "gate_status": "fail_closed_terminal_candidate_rows_sampled_but_same_time_equivalence_missing",
                "required_next_evidence": "source-bounded equivalence argument or exact same physical target/minus/plus windows across coarse/medium/fine before GCI",
            }
        )
    return rows


def blocked_mesh_gci_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "qoi_label": label,
            "current_coarse_case_count": "",
            "medium_fine_case_mesh_count": "0",
            "medium_fine_terminal_window_row_count": "0",
            "strict_coarse_contract_windows_available_in_medium_fine": "false",
            "terminal_window_equivalence_source_exists": "false",
            "same_label_mesh_gci_ready": "false",
            "gate_status": "blocked_not_executed_or_no_sampled_rows",
            "required_next_evidence": "execute sampler on compute node and provide same-time or terminal-equivalence basis",
        }
        for label in QOI_LABELS
    ]


def flush_partial_outputs(
    out_dir: Path,
    geometry_summaries: list[dict[str, Any]],
    window_reductions: list[dict[str, Any]],
    qwall_detail_rows: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sampled_qois = qoi_rows(window_reductions)
    gate_rows = mesh_gci_gate_rows(sampled_qois) if sampled_qois else blocked_mesh_gci_gate_rows()
    dump_csv(out_dir / "mesh_level_geometry_summary.csv", geometry_summaries)
    dump_csv(out_dir / "medium_fine_terminal_window_reductions.csv", window_reductions)
    dump_csv(out_dir / "medium_fine_exact_label_qoi_rows.csv", sampled_qois)
    dump_csv(out_dir / "trusted_wall_Q_wall_detail_rows.csv", qwall_detail_rows)
    dump_csv(out_dir / "sampling_error_log.csv", errors)
    dump_csv(out_dir / "mesh_gci_readiness_gate.csv", gate_rows)
    return sampled_qois


def guardrail_rows(execute: bool, job_id: str = "") -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "native OpenFOAM processor files read only"},
        {"guard_id": "registry_admission_mutation", "changed": "false", "policy": "no registry, coefficient, or admission state edited"},
        {"guard_id": "solver_or_postprocess", "changed": "false", "policy": "no solver or OpenFOAM postProcess command is run by this script"},
        {"guard_id": "scheduler_execution", "changed": bool_text(execute), "policy": f"heavy sampling mode requested; slurm_job_id={job_id}" if job_id else "dry/preflight mode only"},
        {"guard_id": "production_harvest", "changed": "false", "policy": "outputs are task-scoped diagnostic exact-label rows only"},
        {"guard_id": "proxy_substitution", "changed": "false", "policy": "endpoint/probe/profile rows are not substituted for exact labels"},
    ]


def source_manifest_rows(rows: list[dict[str, str]], out_dir: Path) -> list[dict[str, str]]:
    manifest = [
        {
            "path": rel(CONTRACT_PACKAGE / "sampling_command_contract.csv"),
            "role": "completed medium/fine terminal sampling command contract",
            "exists": bool_text((CONTRACT_PACKAGE / "sampling_command_contract.csv").exists()),
            "native_solver_output": "false",
            "mutated": "false",
        },
        {
            "path": rel(CURRENT_COARSE_EXACT / "trusted_wall_Q_wall_summary.csv"),
            "role": "current-coarse exact Q_wall context",
            "exists": bool_text((CURRENT_COARSE_EXACT / "trusted_wall_Q_wall_summary.csv").exists()),
            "native_solver_output": "false",
            "mutated": "false",
        },
        {
            "path": rel(out_dir),
            "role": "task-owned generated package",
            "exists": bool_text(out_dir.exists()),
            "native_solver_output": "false",
            "mutated": "true",
        },
    ]
    for row in rows:
        for path, role in [
            (Path(row["source_root"]), "read-only medium/fine source case root"),
            (Path(row["processors_dir"]), "read-only collated processor field directory"),
            (Path(row["source_root"]) / "constant/polyMesh", "read-only mesh geometry source"),
        ]:
            manifest.append(
                {
                    "path": str(path),
                    "role": role,
                    "exists": bool_text(path.exists()),
                    "native_solver_output": "true",
                    "mutated": "false",
                }
            )
    return manifest


def write_readme(out_dir: Path, summary: dict[str, Any], execute: bool) -> None:
    text = f"""---
provenance:
  generated_by: {TASK_ID}
  generated_at: {summary['generated_at']}
tags: [s13, upcomer-exchange, medium-fine, exact-label-sampler, mesh-gci]
related:
  - {rel(CONTRACT_PACKAGE)}
  - {rel(CURRENT_COARSE_EXACT)}
---

# S13 medium/fine exact-label sampler

This package rebuilds mesh-level S13 trusted-wall, exchange-interface, cap, and
recirculation-CV masks for Salt2/Salt3/Salt4 medium and fine source cases. In
execution mode it samples terminal candidate windows from read-only collated
OpenFOAM processor fields for `Q_wall_W`,
`mdot_exchange_positive_outward_proxy_kg_s`, `tau_recirc_proxy_s`, and
`wall_core_bulk_temperature_contrast_K`.

Decision: `{summary['decision']}`.

The source fields are not production-harvested or admitted here. The strict
coarse-contract physical windows are absent from the medium/fine cases, so the
same-label mesh/GCI gate remains fail-closed unless a later task supplies a
trusted terminal-window equivalence basis or exact same-time mesh-family rows.

## Key Outputs

- `source_preflight.csv`: source/run/path readiness.
- `mesh_level_geometry_summary.csv`: mesh-level CV and face-mask release
  status.
- `medium_fine_terminal_window_reductions.csv`: one row per sampled
  case/mesh/window when `--execute` is used.
- `medium_fine_exact_label_qoi_rows.csv`: long-form QOI rows for downstream
  same-QOI review.
- `mesh_gci_readiness_gate.csv`: fail-closed mesh/GCI disposition.
- `masks/` and `faces/`: generated geometry contracts by case/mesh.

## Guardrails

Native solver outputs were read only. No solver, OpenFOAM post-processing,
production harvest, registry mutation, coefficient admission, S11/S12/S13/S15
trigger, or proxy substitution is performed. Execution mode used here:
`{bool_text(execute)}`.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build(
    out_dir: Path = OUT,
    execute: bool = False,
    job_id: str = "",
    case_id: str = "",
    mesh_level: str = "",
    max_windows: int = 0,
) -> dict[str, Any]:
    generated_at = iso_timestamp()
    ensure_dir(out_dir)
    rows = filtered_contract_rows(contract_rows(), case_id=case_id, mesh_level=mesh_level)
    preflight = source_preflight_rows(rows, max_windows=max_windows)
    dump_csv(out_dir / "source_preflight.csv", preflight)

    geometry_summaries: list[dict[str, Any]] = []
    window_reductions: list[dict[str, Any]] = []
    qwall_detail_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    sampled_qois: list[dict[str, Any]] = []
    flush_partial_outputs(out_dir, geometry_summaries, window_reductions, qwall_detail_rows, errors)

    if execute:
        for row in rows:
            try:
                geometry = build_mesh_geometry(row, out_dir)
                geometry_summaries.append(geometry.summary)
                sampled_qois = flush_partial_outputs(
                    out_dir, geometry_summaries, window_reductions, qwall_detail_rows, errors
                )
                for idx, time in enumerate(limited_windows(row, max_windows)):
                    role = ("terminal_minus", "terminal", "terminal_plus")[idx] if idx < 3 else f"terminal_extra_{idx}"
                    reduction, detail = sample_window(geometry, time, role)
                    window_reductions.append(reduction)
                    qwall_detail_rows.extend(
                        {
                            **item,
                            "mesh_level": geometry.mesh_level,
                            "window_role": role,
                            "mesh_mask_id": seed_case_id(geometry.case_id, geometry.mesh_level),
                        }
                        for item in detail
                    )
                    sampled_qois = flush_partial_outputs(
                        out_dir, geometry_summaries, window_reductions, qwall_detail_rows, errors
                    )
            except Exception as exc:  # keep fail-closed evidence for the other rows
                errors.append(
                    {
                        "case_id": row["case_id"],
                        "mesh_level": row["mesh_level"],
                        "source_root": row["source_root"],
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "execution_status": "fail_closed_sampling_error",
                    }
                )
                sampled_qois = flush_partial_outputs(
                    out_dir, geometry_summaries, window_reductions, qwall_detail_rows, errors
                )

    sampled_qois = flush_partial_outputs(out_dir, geometry_summaries, window_reductions, qwall_detail_rows, errors)
    dump_csv(out_dir / "no_mutation_guardrails.csv", guardrail_rows(execute, job_id))
    dump_csv(out_dir / "source_manifest.csv", source_manifest_rows(rows, out_dir))

    decision = (
        "terminal_exact_label_rows_sampled_mesh_gci_fail_closed_time_equivalence_missing"
        if sampled_qois and not errors
        else "partial_or_failed_sampling_fail_closed"
        if execute
        else "preflight_ready_heavy_execution_not_run"
    )
    summary = {
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": decision,
        "execute_mode": execute,
        "source_contract_rows": len(rows),
        "source_preflight_ready_rows": sum(row["preflight_status"] == "ready_for_compute_node_sampling" for row in preflight),
        "case_id_filter": case_id,
        "mesh_level_filter": mesh_level,
        "max_windows": max_windows,
        "mesh_geometry_rows": len(geometry_summaries),
        "terminal_window_reduction_rows": len(window_reductions),
        "exact_label_qoi_rows": len(sampled_qois),
        "sampling_error_rows": len(errors),
        "same_label_mesh_gci_ready": False,
        "production_harvest_allowed": False,
        "admission_allowed": False,
        "native_solver_outputs_mutated": False,
    }
    json_dump(out_dir / "summary.json", summary)
    write_readme(out_dir, summary, execute)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help="run heavy mesh/field reduction; intended for Slurm")
    parser.add_argument("--job-id", default="", help="optional Slurm job id for provenance")
    parser.add_argument("--case-id", default="", help="optional single case filter, e.g. salt_2")
    parser.add_argument("--mesh-level", default="", help="optional mesh filter, e.g. medium")
    parser.add_argument("--max-windows", type=int, default=0, help="limit terminal candidate windows per case; 0 means all")
    args = parser.parse_args()
    summary = build(
        args.out,
        execute=args.execute,
        job_id=args.job_id,
        case_id=args.case_id,
        mesh_level=args.mesh_level,
        max_windows=args.max_windows,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
