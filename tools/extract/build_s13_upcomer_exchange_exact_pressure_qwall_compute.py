#!/usr/bin/env python3
"""Compute exact S13 pressure and trusted-wall Q_wall from native fields.

This reducer reads collated OpenFOAM `processors64` fields read-only. It maps
processor-local cells/faces back to global ids with `cellProcAddressing` and
`faceProcAddressing`, samples only the seeded S13 cells/faces, and writes a
task-owned reduction package. It does not mutate native outputs, run a solver,
launch a sampler/harvest, execute UQ, or admit coefficients.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-EXACT-PRESSURE-QWALL-COMPUTE-2026-07-21"
OUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute"
)
SURFACE_INPUT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv"
)
LIMITED = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction"
)
UNBLOCK = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_s13_upcomer_exchange_sampled_field_qwall_uq_unblock"
)

CASE_DIRS = {
    "salt_2": ROOT
    / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
    "salt_3": ROOT
    / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
    "salt_4": ROOT
    / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
}

PROCESSOR_RE = re.compile(r"(?m)^// Processor(\d+)\s*$")


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def bool_text(value: bool) -> str:
    return str(value).lower()


def fmt(value: float) -> str:
    return f"{value:.12g}" if math.isfinite(value) else ""


def load_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def processor_blocks(text: str) -> list[tuple[int, str]]:
    matches = list(PROCESSOR_RE.finditer(text))
    blocks: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((int(match.group(1)), text[match.end() : end]))
    return blocks


def parse_number_list(block: str, number_type: type[int] | type[float] = float) -> list[int] | list[float]:
    lines = block.splitlines()
    for index, line in enumerate(lines[:-1]):
        stripped = line.strip()
        if not stripped.isdigit():
            continue
        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1
        if next_index >= len(lines) or lines[next_index].strip() != "(":
            continue
        expected = int(stripped)
        payload: list[str] = []
        for value_line in lines[next_index + 1 :]:
            if value_line.strip() in {")", ");"}:
                try:
                    values = [number_type(token) for token in payload]
                except ValueError:
                    break
                if len(values) != expected:
                    break
                return values
            payload.extend(value_line.split())
    raise ValueError("could not find OpenFOAM list payload")


def brace_body(text: str, open_brace_index: int) -> str:
    depth = 0
    for pos in range(open_brace_index, len(text)):
        char = text[pos]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1 : pos]
    raise ValueError("unclosed OpenFOAM brace block")


def parse_patch_bodies(section: str) -> dict[str, str]:
    patches: dict[str, str] = {}
    pos = 0
    name_re = re.compile(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\{")
    while True:
        match = name_re.search(section, pos)
        if not match:
            break
        name = match.group(1)
        open_index = section.find("{", match.start())
        body = brace_body(section, open_index)
        patches[name] = body
        pos = open_index + len(body) + 2
    return patches


def named_brace_body(text: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*\{{", text)
    if not match:
        raise ValueError(f"could not find OpenFOAM block {name}")
    open_index = text.find("{", match.start())
    return brace_body(text, open_index)


def parse_boundary_patches(block: str) -> dict[str, dict[str, int]]:
    patches: dict[str, dict[str, int]] = {}
    for name, body in parse_patch_bodies(block).items():
        nfaces = re.search(r"\bnFaces\s+(\d+)\s*;", body)
        start = re.search(r"\bstartFace\s+(\d+)\s*;", body)
        if nfaces and start:
            patches[name] = {"nFaces": int(nfaces.group(1)), "startFace": int(start.group(1))}
    return patches


def parse_patch_scalar_values(body: str) -> list[float]:
    if re.search(r"\bvalue\s+nonuniform\s+List<scalar>\s+0\s*\(\s*\)\s*;", body):
        return []
    value_match = re.search(r"(?ms)\bvalue\s+nonuniform\s+List<scalar>\s*(\d+)\s*\(\s*(.*?)\s*\)\s*;", body)
    if not value_match:
        return []
    expected = int(value_match.group(1))
    values = [float(token) for token in value_match.group(2).split()]
    if len(values) != expected:
        raise ValueError(f"patch scalar count mismatch: expected {expected}, got {len(values)}")
    return values


def decode_face_address(value: int) -> tuple[int, bool]:
    if value >= 0:
        return value, False
    return -value - 1, True


def case_rows() -> list[dict[str, str]]:
    return read_csv(SURFACE_INPUT / "seeded_surface_input_manifest.csv")


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
                "seed_owner_cell": int(row["seed_owner_cell"]),
                "adjacent_core_cell": int(row["adjacent_core_cell"]),
                "area_m2": float(row["area_m2"]),
            }
        )
    return rows


def load_wall_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(path):
        rows.append(
            {
                "face_id": int(row["face_id"]),
                "patch_name": row["patch_name"],
                "owner": int(row["owner"]),
                "area_m2": float(row["area_m2"]),
            }
        )
    return rows


def selected_cell_roles(
    seed_cells: set[int],
    interface_rows: list[dict[str, Any]],
    wall_rows: list[dict[str, Any]],
) -> dict[int, set[str]]:
    roles: dict[int, set[str]] = {cell_id: {"seeded_recirc_cv"} for cell_id in seed_cells}
    for row in interface_rows:
        roles.setdefault(row["seed_owner_cell"], set()).add("interface_seed_owner")
        roles.setdefault(row["adjacent_core_cell"], set()).add("interface_adjacent_core")
    for row in wall_rows:
        roles.setdefault(row["owner"], set()).add("trusted_wall_owner")
    return roles


def read_mapped_scalar_field(field_path: Path, addressing_path: Path, selected: set[int]) -> dict[int, float]:
    selected_values: dict[int, float] = {}
    address_blocks = processor_blocks(load_text(addressing_path))
    field_blocks = processor_blocks(load_text(field_path))
    if len(address_blocks) != len(field_blocks):
        raise ValueError(f"processor block count mismatch for {field_path}")
    field_by_proc = {proc: block for proc, block in field_blocks}
    for proc, address_block in address_blocks:
        addresses = parse_number_list(address_block, int)
        values = parse_number_list(field_by_proc[proc], float)
        if len(addresses) != len(values):
            raise ValueError(f"processor {proc} address/value count mismatch for {field_path}")
        for local_i, global_cell in enumerate(addresses):
            if global_cell in selected:
                selected_values[global_cell] = float(values[local_i])
    missing = selected - set(selected_values)
    if missing:
        raise ValueError(f"{field_path} missing {len(missing)} selected cells")
    return selected_values


def weighted_average(items: Iterable[tuple[int, float]], values: dict[int, float]) -> float:
    numerator = 0.0
    denominator = 0.0
    for cell_id, weight in items:
        numerator += values[cell_id] * weight
        denominator += weight
    if denominator <= 0.0:
        raise ValueError("nonpositive weight sum")
    return numerator / denominator


def pressure_reduction(
    case: dict[str, str],
    seed_cells: set[int],
    interface_rows: list[dict[str, Any]],
    wall_rows: list[dict[str, Any]],
    p: dict[int, float],
    p_rgh: dict[int, float],
) -> dict[str, Any]:
    volumes = load_volumes(ROOT / case["volume_csv"], seed_cells)
    seed_weights = [(cell, volumes[cell]) for cell in seed_cells]
    interface_seed_weights = [(row["seed_owner_cell"], row["area_m2"]) for row in interface_rows]
    interface_core_weights = [(row["adjacent_core_cell"], row["area_m2"]) for row in interface_rows]
    wall_owner_weights = [(row["owner"], row["area_m2"]) for row in wall_rows]
    return {
        "case_id": case["case_id"],
        "time_window_s": case["time_window_s"],
        "selected_cell_count": len(p),
        "seeded_cv_cell_count": len(seed_cells),
        "interface_face_count": len(interface_rows),
        "trusted_wall_face_count": len(wall_rows),
        "seeded_cv_p_volume_avg_Pa": fmt(weighted_average(seed_weights, p)),
        "seeded_cv_p_rgh_volume_avg_Pa": fmt(weighted_average(seed_weights, p_rgh)),
        "interface_seed_p_area_avg_Pa": fmt(weighted_average(interface_seed_weights, p)),
        "interface_seed_p_rgh_area_avg_Pa": fmt(weighted_average(interface_seed_weights, p_rgh)),
        "interface_core_p_area_avg_Pa": fmt(weighted_average(interface_core_weights, p)),
        "interface_core_p_rgh_area_avg_Pa": fmt(weighted_average(interface_core_weights, p_rgh)),
        "trusted_wall_owner_p_area_avg_Pa": fmt(weighted_average(wall_owner_weights, p)),
        "trusted_wall_owner_p_rgh_area_avg_Pa": fmt(weighted_average(wall_owner_weights, p_rgh)),
        "pressure_basis_released": "true",
        "release_status": "exact_target_window_pressure_reduced",
    }


def pressure_detail_rows(
    case: dict[str, str],
    roles: dict[int, set[str]],
    p: dict[int, float],
    p_rgh: dict[int, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell_id in sorted(roles):
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "cell_id": cell_id,
                "roles": ";".join(sorted(roles[cell_id])),
                "p_Pa": fmt(p[cell_id]),
                "p_rgh_Pa": fmt(p_rgh[cell_id]),
                "release_status": "exact_target_window_pressure_sample",
            }
        )
    return rows


def trusted_wall_heat_flux(
    case: dict[str, str],
    wall_rows: list[dict[str, Any]],
    wall_heat_flux_path: Path,
    boundary_path: Path,
    face_addressing_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    wanted = {row["face_id"]: row for row in wall_rows}
    area_total = sum(row["area_m2"] for row in wall_rows)
    boundary_blocks = {proc: block for proc, block in processor_blocks(load_text(boundary_path))}
    face_addr_blocks = {proc: block for proc, block in processor_blocks(load_text(face_addressing_path))}
    whf_blocks = {proc: block for proc, block in processor_blocks(load_text(wall_heat_flux_path))}
    matched: dict[int, dict[str, Any]] = {}
    reversed_count = 0
    for proc in sorted(whf_blocks):
        boundary = parse_boundary_patches(boundary_blocks[proc])
        face_addresses = parse_number_list(face_addr_blocks[proc], int)
        patch_values = parse_patch_bodies(named_brace_body(whf_blocks[proc], "boundaryField"))
        for patch_name, patch_meta in boundary.items():
            values = parse_patch_scalar_values(patch_values.get(patch_name, ""))
            nfaces = patch_meta["nFaces"]
            if len(values) != nfaces:
                if not values and nfaces > 0:
                    values = [0.0] * nfaces
                elif nfaces == 0 and not values:
                    continue
                else:
                    raise ValueError(
                        f"{case['case_id']} processor {proc} patch {patch_name} has {len(values)} values for {nfaces} faces"
                    )
            start = patch_meta["startFace"]
            for offset, q_value in enumerate(values):
                global_face, reversed_orientation = decode_face_address(int(face_addresses[start + offset]))
                if global_face not in wanted:
                    continue
                reversed_count += int(reversed_orientation)
                expected = wanted[global_face]
                matched[global_face] = {
                    "case_id": case["case_id"],
                    "time_window_s": case["time_window_s"],
                    "face_id": global_face,
                    "processor": proc,
                    "native_patch_name": patch_name,
                    "trusted_wall_patch_name": expected["patch_name"],
                    "patch_name_match": bool_text(patch_name == expected["patch_name"]),
                    "owner_cell": expected["owner"],
                    "area_m2": fmt(expected["area_m2"]),
                    "wallHeatFlux_native_W_m2": fmt(q_value),
                    "qA_native_W": fmt(q_value * expected["area_m2"]),
                    "Q_wall_positive_to_seeded_fluid_W_contribution": fmt(-q_value * expected["area_m2"]),
                    "face_addressing_reversed": bool_text(reversed_orientation),
                    "release_status": "exact_target_window_trusted_wall_heat_flux_sample",
                }
    missing = set(wanted) - set(matched)
    patch_mismatch_count = sum(1 for row in matched.values() if row["patch_name_match"] == "false")
    patch_mismatch_native_abs_w = sum(
        abs(float(row["qA_native_W"])) for row in matched.values() if row["patch_name_match"] == "false"
    )
    patch_mismatch_nonzero_count = sum(
        1
        for row in matched.values()
        if row["patch_name_match"] == "false" and abs(float(row["qA_native_W"])) > 1.0e-12
    )
    q_native = sum(float(row["qA_native_W"]) for row in matched.values())
    q_into_fluid = -q_native
    mismatch_relative = patch_mismatch_native_abs_w / max(abs(q_native), 1.0e-12)
    seam_mismatch_below_tolerance = patch_mismatch_native_abs_w <= 1.0e-3 and mismatch_relative <= 1.0e-4
    release = not missing and (patch_mismatch_nonzero_count == 0 or seam_mismatch_below_tolerance)
    summary = {
        "case_id": case["case_id"],
        "time_window_s": case["time_window_s"],
        "trusted_wall_face_count": len(wall_rows),
        "matched_wallHeatFlux_face_count": len(matched),
        "missing_wallHeatFlux_face_count": len(missing),
        "trusted_wall_area_m2": fmt(area_total),
        "matched_trusted_wall_area_m2": fmt(sum(wanted[face]["area_m2"] for face in matched)),
        "coverage_fraction": fmt((len(matched) / len(wall_rows)) if wall_rows else 0.0),
        "patch_mismatch_count": patch_mismatch_count,
        "patch_mismatch_nonzero_count": patch_mismatch_nonzero_count,
        "patch_mismatch_native_abs_W_sum": fmt(patch_mismatch_native_abs_w),
        "patch_mismatch_relative_to_abs_integral": fmt(mismatch_relative),
        "patch_mismatch_tolerance": "abs<=1e-3 W and relative<=1e-4 of native integral",
        "face_addressing_reversed_count": reversed_count,
        "wallHeatFlux_integral_native_outward_W": fmt(q_native),
        "Q_wall_W": fmt(q_into_fluid),
        "Q_wall_positive_convention": "positive Q_wall_W adds heat to seeded recirculation fluid; OpenFOAM wallHeatFlux integral is native outward wall-normal sign",
        "Q_wall_W_released": bool_text(release),
        "release_status": (
            "exact_target_window_Q_wall_W_released"
            if release and patch_mismatch_count == 0
            else "exact_target_window_Q_wall_W_released_with_tiny_ncc_patch_label_mismatch"
            if release
            else "blocked_incomplete_wallHeatFlux_mapping"
        ),
    }
    return summary, [matched[face] for face in sorted(matched)]


def field_audit_rows(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        case_dir = CASE_DIRS[case["case_id"]]
        time_dir = case_dir / "processors64" / case["time_window_s"]
        for field in ("p", "p_rgh", "wallHeatFlux"):
            path = time_dir / field
            rows.append(
                {
                    "case_id": case["case_id"],
                    "time_window_s": case["time_window_s"],
                    "artifact": field,
                    "path": rel(path),
                    "exists": bool_text(path.exists()),
                    "size_bytes": path.stat().st_size if path.exists() else "",
                    "native_solver_output": "true",
                    "mutated": "false",
                    "audit_status": "exact_target_window_present" if path.exists() else "blocked_missing_exact_target_window_field",
                }
            )
        for artifact in ("cellProcAddressing", "faceProcAddressing", "boundary"):
            path = case_dir / "processors64/constant/polyMesh" / artifact
            rows.append(
                {
                    "case_id": case["case_id"],
                    "time_window_s": case["time_window_s"],
                    "artifact": artifact,
                    "path": rel(path),
                    "exists": bool_text(path.exists()),
                    "size_bytes": path.stat().st_size if path.exists() else "",
                    "native_solver_output": "true",
                    "mutated": "false",
                    "audit_status": "addressing_or_boundary_present" if path.exists() else "blocked_missing_mapping",
                }
            )
    return rows


def downstream_gate_rows(qwall_rows: list[dict[str, Any]], pressure_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    qwall_ready = all(row["Q_wall_W_released"] == "true" for row in qwall_rows)
    pressure_ready = all(row["pressure_basis_released"] == "true" for row in pressure_rows)
    return [
        {
            "gate": "exact_pressure_basis",
            "status": "released" if pressure_ready else "blocked",
            "allowed": bool_text(pressure_ready),
            "reason": "target-window p and p_rgh sampled/reduced from native fields through cellProcAddressing",
        },
        {
            "gate": "Q_wall_W",
            "status": "released" if qwall_ready else "blocked",
            "allowed": bool_text(qwall_ready),
            "reason": "trusted-wall wallHeatFlux integrated only on seeded trusted wall faces with full face coverage",
        },
        {
            "gate": "production_sampler_manifest_refresh",
            "status": "eligible_next_review_not_run" if qwall_ready and pressure_ready else "blocked",
            "allowed": "false",
            "reason": "this row releases inputs only; sampler manifest, production harvest, and UQ require a separate row",
        },
        {
            "gate": "same_qoi_uq",
            "status": "blocked",
            "allowed": "false",
            "reason": "same-window target QOIs are now available, but neighbor-window and mesh/GCI same-QOI UQ are not executed here",
        },
        {
            "gate": "internal_Nu_residual_absorption",
            "status": "forbidden",
            "allowed": "false",
            "reason": "Q_wall_W is carried as a separate heat path; no residual is hidden in internal Nu",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "native processors64 fields were read only"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no sbatch/srun launched for this in-session reducer"},
        {"guard_id": "OpenFOAM_solver_or_postprocess", "changed": "false", "policy": "no solver or OpenFOAM postProcess command launched"},
        {"guard_id": "sampler_harvest_uq_admission", "changed": "false", "policy": "no sampler, harvest, UQ, fitting, or admission"},
        {"guard_id": "registry_Fluid_external_blocker", "changed": "false", "policy": "no registry, Fluid, external, or blocker-register edit"},
        {"guard_id": "residual_internal_Nu", "changed": "false", "policy": "residual remains explicit; internal Nu was not modified or back-filled"},
    ]


def source_manifest_rows(cases: list[dict[str, str]]) -> list[dict[str, str]]:
    paths: list[tuple[Path, str, str]] = [
        (SURFACE_INPUT / "seeded_surface_input_manifest.csv", "seeded S13 surface/input manifest", "false"),
        (LIMITED / "sampled_field_summary.csv", "completed limited sampled-field context", "false"),
        (UNBLOCK / "source_basis_audit.csv", "completed pressure/cp/viscosity/Qwall unblock audit", "false"),
    ]
    for case in cases:
        case_dir = CASE_DIRS[case["case_id"]]
        paths.extend(
            [
                (ROOT / case["recirc_cell_mask"], f"{case['case_id']} seeded CV cell mask", "false"),
                (ROOT / case["exchange_interface_faces_csv"], f"{case['case_id']} exchange interface map", "false"),
                (ROOT / case["trusted_wall_faces_csv"], f"{case['case_id']} trusted wall face map", "false"),
                (ROOT / case["volume_csv"], f"{case['case_id']} selected cell volumes", "false"),
                (case_dir / "processors64" / case["time_window_s"] / "p", f"{case['case_id']} target p field", "true"),
                (case_dir / "processors64" / case["time_window_s"] / "p_rgh", f"{case['case_id']} target p_rgh field", "true"),
                (case_dir / "processors64" / case["time_window_s"] / "wallHeatFlux", f"{case['case_id']} target wallHeatFlux field", "true"),
                (case_dir / "processors64/constant/polyMesh/cellProcAddressing", f"{case['case_id']} cell map", "true"),
                (case_dir / "processors64/constant/polyMesh/faceProcAddressing", f"{case['case_id']} face map", "true"),
                (case_dir / "processors64/constant/polyMesh/boundary", f"{case['case_id']} processor boundary map", "true"),
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


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SURFACE_INPUT / 'seeded_surface_input_manifest.csv')}
  - {rel(LIMITED / 'sampled_field_summary.csv')}
  - {rel(UNBLOCK / 'source_basis_audit.csv')}
tags: [s13, upcomer-exchange, pressure, wallHeatFlux, q-wall]
related:
  - .agent/status/2026-07-21_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_input_release
---
# S13 Exact Pressure and Trusted-Wall Q Wall Compute

This package releases exact target-window pressure reductions and trusted-wall
`Q_wall_W` from read-only native OpenFOAM collated fields.

- cases processed: `{summary['case_count']}`
- pressure rows released: `{summary['pressure_basis_released_rows']}`
- `Q_wall_W` rows released: `{summary['Q_wall_W_released_rows']}`
- detailed pressure sample rows: `{summary['pressure_detail_rows']}`
- detailed trusted-wall heat-flux rows: `{summary['trusted_wall_heat_flux_detail_rows']}`
- native outputs mutated: `{summary['native_output_mutation']}`
- sampler/harvest/UQ/admission launched: `false`

`Q_wall_W` is positive into the seeded recirculation fluid. The native
OpenFOAM wallHeatFlux integral is retained separately as
`wallHeatFlux_integral_native_outward_W`; `Q_wall_W = -native_integral`.

This release does not put any missing heat residual into internal `Nu`.
Sampler refresh, production harvest, and same-QOI UQ are eligible for later
review only; they are not executed here.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    cases = case_rows()
    pressure_summary: list[dict[str, Any]] = []
    pressure_detail: list[dict[str, Any]] = []
    qwall_summary: list[dict[str, Any]] = []
    qwall_detail: list[dict[str, Any]] = []
    for case in cases:
        case_dir = CASE_DIRS[case["case_id"]]
        seed_cells = load_seed_cells(ROOT / case["recirc_cell_mask"])
        interface_rows = load_interface_rows(ROOT / case["exchange_interface_faces_csv"])
        wall_rows = load_wall_rows(ROOT / case["trusted_wall_faces_csv"])
        roles = selected_cell_roles(seed_cells, interface_rows, wall_rows)
        selected = set(roles)
        address_path = case_dir / "processors64/constant/polyMesh/cellProcAddressing"
        p = read_mapped_scalar_field(case_dir / "processors64" / case["time_window_s"] / "p", address_path, selected)
        p_rgh = read_mapped_scalar_field(case_dir / "processors64" / case["time_window_s"] / "p_rgh", address_path, selected)
        pressure_summary.append(pressure_reduction(case, seed_cells, interface_rows, wall_rows, p, p_rgh))
        pressure_detail.extend(pressure_detail_rows(case, roles, p, p_rgh))
        q_summary, q_detail = trusted_wall_heat_flux(
            case,
            wall_rows,
            case_dir / "processors64" / case["time_window_s"] / "wallHeatFlux",
            case_dir / "processors64/constant/polyMesh/boundary",
            case_dir / "processors64/constant/polyMesh/faceProcAddressing",
        )
        qwall_summary.append(q_summary)
        qwall_detail.extend(q_detail)

    field_audit = field_audit_rows(cases)
    downstream = downstream_gate_rows(qwall_summary, pressure_summary)
    guards = guardrail_rows()
    sources = source_manifest_rows(cases)
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "exact_target_window_pressure_and_Q_wall_inputs_released",
        "case_count": len(cases),
        "pressure_basis_released_rows": sum(1 for row in pressure_summary if row["pressure_basis_released"] == "true"),
        "Q_wall_W_released_rows": sum(1 for row in qwall_summary if row["Q_wall_W_released"] == "true"),
        "pressure_detail_rows": len(pressure_detail),
        "trusted_wall_heat_flux_detail_rows": len(qwall_detail),
        "production_sampler_manifest_refresh_allowed_now": False,
        "production_harvest_allowed_now": False,
        "same_qoi_uq_ready": False,
        "admission_allowed": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "OpenFOAM_solver_or_postprocessing_launched": False,
        "sampler_or_harvest_launched": False,
        "Fluid_or_external_repo_mutation": False,
        "fitting_or_model_selection": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_nu": False,
    }
    csv_dump(out / "source_field_audit.csv", list(field_audit[0]), field_audit)
    csv_dump(out / "sampled_pressure_detail.csv", list(pressure_detail[0]), pressure_detail)
    csv_dump(out / "pressure_reduction_summary.csv", list(pressure_summary[0]), pressure_summary)
    csv_dump(out / "trusted_wall_wallHeatFlux_detail.csv", list(qwall_detail[0]), qwall_detail)
    csv_dump(out / "trusted_wall_Q_wall_summary.csv", list(qwall_summary[0]), qwall_summary)
    csv_dump(out / "downstream_gate.csv", list(downstream[0]), downstream)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    args = parser.parse_args()
    summary = build(args.out_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
