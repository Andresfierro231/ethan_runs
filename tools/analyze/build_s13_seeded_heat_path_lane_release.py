#!/usr/bin/env python3
"""Build the S13 seeded heat-path, sampled-field, and Q_wall contract package.

This is a dry contract builder.  It inventories already-released geometry and
whole-mesh cell-field support, then writes the requirements that must be met
before any exchange-cell harvest or coefficient admission is allowed.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-S13-SEEDED-HEAT-PATH-LANE-RELEASE-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release"

SURFACE_INPUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv"
SURFACE_VTK = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv"
SEEDED_CV = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed"
CELL_VTK_MANIFEST = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest"
SOURCE_SINK = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"
SAMPLER_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
SAME_WINDOW_UQ = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design"

VTK_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.:-]*)\s+(\d+)\s+(\d+)\s+([A-Za-z][A-Za-z0-9_]*)$")


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def as_bool(value: Any) -> bool:
    return str(value).lower() == "true"


@lru_cache(maxsize=None)
def vtk_field_headers(path_text: str) -> tuple[dict[str, str], ...]:
    """Return legacy VTK FIELD headers without loading the arrays into memory."""
    path = ROOT / path_text if not Path(path_text).is_absolute() else Path(path_text)
    headers: list[dict[str, str]] = []
    context = "unknown"
    if not path.exists():
        return tuple(headers)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("CELL_DATA "):
                context = "CELL_DATA"
                continue
            if stripped.startswith("POINT_DATA "):
                context = "POINT_DATA"
                continue
            match = VTK_FIELD_RE.match(stripped)
            if match:
                name, components, tuples, dtype = match.groups()
                headers.append(
                    {
                        "data_location": context,
                        "field_name": name,
                        "components": components,
                        "tuples": tuples,
                        "data_type": dtype,
                    }
                )
    return tuple(headers)


def case_rows() -> list[dict[str, str]]:
    return read_csv(CELL_VTK_MANIFEST / "case_vtk_input_manifest.cells_populated.csv")


def keyed(rows: list[dict[str, str]], *keys: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row[key] for key in keys): row for row in rows}


def build_field_inventory(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        vtk_rel = case["cell_vtk"]
        vtk_path = ROOT / vtk_rel
        headers = [dict(row) for row in vtk_field_headers(vtk_rel)]
        cell_fields = sorted(row["field_name"] for row in headers if row["data_location"] == "CELL_DATA")
        point_fields = sorted(row["field_name"] for row in headers if row["data_location"] == "POINT_DATA")
        all_fields = set(cell_fields) | set(point_fields)
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "cell_vtk": vtk_rel,
                "cell_vtk_exists": str(vtk_path.exists()).lower(),
                "cell_data_fields": ";".join(cell_fields),
                "point_data_fields": ";".join(point_fields),
                "has_cellID": str("cellID" in all_fields).lower(),
                "has_U": str("U" in all_fields).lower(),
                "has_T": str("T" in all_fields).lower(),
                "has_rho": str("rho" in all_fields).lower(),
                "has_pressure_basis": str(bool({"p", "p_rgh"} & all_fields)).lower(),
                "has_mu_basis": str(bool({"mu", "nu", "nut"} & all_fields)).lower(),
                "has_wallHeatFlux": str("wallHeatFlux" in all_fields).lower(),
                "inventory_status": "cell_fields_support_partial_reduction_pressure_mu_wallflux_missing",
            }
        )
    return rows


def build_sampled_field_contract(
    cases: list[dict[str, str]],
    inventory: list[dict[str, Any]],
    surface_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_case = {row["case_id"]: row for row in inventory}
    surfaces = keyed(surface_rows, "case_id", "surface_kind")
    requirements = [
        ("interface_U", "exchange_interface", "U", "mdot_exchange;energy_residual"),
        ("interface_T", "exchange_interface", "T", "mdot_exchange*T_terms;energy_residual"),
        ("interface_rho", "exchange_interface", "rho", "mdot_exchange;R_rho"),
        ("interface_pressure", "exchange_interface", "p_or_p_rgh", "pressure_residual"),
        ("wall_T", "trusted_wall", "T", "wall_core_thermal_contrast;T_recirc_support"),
        ("wallHeatFlux", "trusted_wall", "wallHeatFlux", "Q_wall_W;energy_residual"),
        ("recirc_cell_T", "recirc_cell_mask", "T", "T_recirc;energy_residual"),
        ("recirc_cell_rho", "recirc_cell_mask", "rho", "R_rho"),
        ("mu_or_nu", "recirc_cell_mask", "mu_or_nu", "R_mu"),
        ("cp_J_kg_K", "property_contract", "cp", "energy_residual"),
    ]
    rows: list[dict[str, Any]] = []
    for case in cases:
        inv = by_case[case["case_id"]]
        for lane, surface_kind, source_field, required_for in requirements:
            surface = surfaces.get((case["case_id"], surface_kind), {})
            surface_vtk = surface.get("vtk_path", "")
            geometry_ready = bool(surface) and as_bool(surface.get("vtk_exists", "false"))
            whole_mesh_field_present = {
                "U": as_bool(inv["has_U"]),
                "T": as_bool(inv["has_T"]),
                "rho": as_bool(inv["has_rho"]),
                "p_or_p_rgh": as_bool(inv["has_pressure_basis"]),
                "wallHeatFlux": as_bool(inv["has_wallHeatFlux"]),
                "mu_or_nu": as_bool(inv["has_mu_basis"]),
                "cp": bool(case.get("cp_J_kg_K")),
            }.get(source_field, False)
            if surface_kind == "recirc_cell_mask":
                geometry_ready = (SURFACE_INPUT / "masks" / f"{case['case_id']}_seeded_recirc_cell_mask.csv").exists()
                surface_vtk = rel(SURFACE_INPUT / "masks" / f"{case['case_id']}_seeded_recirc_cell_mask.csv")
            if surface_kind == "property_contract":
                geometry_ready = False
                surface_vtk = ""

            if lane in {"recirc_cell_T", "recirc_cell_rho"} and whole_mesh_field_present and geometry_ready:
                status = "input_support_ready_reduction_not_run"
                blocking_reason = "diagnostic reduction still must be run and same-QOI UQ is absent"
            elif lane in {"interface_U", "interface_T", "interface_rho", "wall_T"} and whole_mesh_field_present and geometry_ready:
                status = "geometry_ready_whole_mesh_field_present_surface_sampling_not_run"
                blocking_reason = "geometry-only VTK has no sampled face or wall field arrays"
            elif source_field == "p_or_p_rgh":
                status = "blocked_missing_pressure_basis"
                blocking_reason = "whole-mesh cell VTK inventory has no p or p_rgh field"
            elif source_field == "wallHeatFlux":
                status = "blocked_missing_wallHeatFlux_Q_wall"
                blocking_reason = "wallHeatFlux is not present in the whole-mesh VTK and Q_wall_W has not been integrated or released"
            elif source_field == "mu_or_nu":
                status = "blocked_missing_mu_or_nu_basis"
                blocking_reason = "whole-mesh cell VTK inventory has no mu/nu/nut field suitable for R_mu"
            elif source_field == "cp":
                status = "blocked_missing_cp_property_contract"
                blocking_reason = "cp_J_kg_K is blank in the current sampler manifest"
            else:
                status = "blocked_missing_required_field_or_geometry"
                blocking_reason = "required field or geometry support is not released"

            rows.append(
                {
                    "case_id": case["case_id"],
                    "time_window_s": case["time_window_s"],
                    "lane": lane,
                    "surface_or_mask": surface_kind,
                    "required_source_field": source_field,
                    "required_for": required_for,
                    "geometry_or_mask_ready": str(geometry_ready).lower(),
                    "whole_mesh_field_present": str(whole_mesh_field_present).lower(),
                    "sampled_surface_field_present": "false",
                    "sampler_ready": "false",
                    "status": status,
                    "blocking_reason": blocking_reason,
                    "source_path": surface_vtk or case["cell_vtk"],
                }
            )
    return rows


def build_qwall_contract(cases: list[dict[str, str]], surface_rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    surfaces = keyed(surface_rows, "case_id", "surface_kind")
    sources = {row["case_id"]: row for row in source_rows}
    rows: list[dict[str, Any]] = []
    for case in cases:
        wall = surfaces[(case["case_id"], "trusted_wall")]
        src = sources[case["case_id"]]
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "trusted_wall_vtk": wall["vtk_path"],
                "trusted_wall_geometry_ready": wall["vtk_exists"],
                "trusted_wall_area_m2": wall["vtk_area_m2"],
                "wallHeatFlux_source_exists": "false",
                "Q_wall_W_released": "false",
                "q_source_W_static_context": src["q_source_w"],
                "q_sink_W_static_context": src["q_sink_w"],
                "q_net_W_static_context_not_Q_wall": src["q_net_w"],
                "positive_Q_wall_convention": "positive Q_wall_W adds heat to the recirculation/exchange control volume fluid",
                "integration_contract": "integrate sampled wallHeatFlux over trusted_wall faces using released face areas and same time window",
                "blocking_reason": "geometry-only wall VTK has no wallHeatFlux field; q_net_W is source/sink context and is not a substitute for Q_wall_W",
                "source_path": rel(SOURCE_SINK / "source_sink_summary.csv"),
            }
        )
    return rows


def build_heat_path_lane_table() -> list[dict[str, Any]]:
    return [
        {
            "heat_path_lane": "internal_Nu",
            "current_status": "protected_from_residual_absorption",
            "allowed_inputs": "runtime-legal one-stream or reduced-model state variables only after model-form admission",
            "forbidden_inputs": "forbidden: fitted residual, wall-heat outcome field, protected split target values, sampler-only exchange QOIs",
            "required_before_claim": "candidate-specific source/property/split gate and same-window UQ",
            "release_status": "not_released",
        },
        {
            "heat_path_lane": "wall_conduction_and_Q_wall_W",
            "current_status": "blocked_missing_wallHeatFlux_integration",
            "allowed_inputs": "trusted_wall geometry, sampled wallHeatFlux, wall/core band, sign convention",
            "forbidden_inputs": "forbidden: q_net_W proxy or source/sink total as wall heat",
            "required_before_claim": "task-owned wallHeatFlux integration over trusted wall faces",
            "release_status": "not_released",
        },
        {
            "heat_path_lane": "source_sink_jacket_cooler",
            "current_status": "static_context_ready_not_energy_residual_release",
            "allowed_inputs": "source_sink_summary.csv static context with provenance",
            "forbidden_inputs": "forbidden: using static source/sink context to close Q_wall_W or energy residual alone",
            "required_before_claim": "same-window source/sink release ledger with cp/sign and Q_wall lane",
            "release_status": "context_only",
        },
        {
            "heat_path_lane": "external_convection_radiation",
            "current_status": "outside_this_exchange_cell_contract",
            "allowed_inputs": "separate external-boundary heat-loss package after source/property gate",
            "forbidden_inputs": "forbidden: mixing external BC residual into internal Nu or exchange-cell coefficient",
            "required_before_claim": "separate external BC admission package",
            "release_status": "not_released",
        },
        {
            "heat_path_lane": "storage",
            "current_status": "not_quantified_for_same_window_exchange_cell",
            "allowed_inputs": "same-window transient energy accounting if a future row claims it",
            "forbidden_inputs": "forbidden: assuming zero storage without evidence",
            "required_before_claim": "same-window transient/storage diagnostic",
            "release_status": "not_released",
        },
        {
            "heat_path_lane": "exchange_enthalpy",
            "current_status": "blocked_missing_mdot_exchange_and_T_terms",
            "allowed_inputs": "sampled interface U/rho/T with positive mdot from recirc CV to main flow",
            "forbidden_inputs": "forbidden: proxy plane substitution or unsigned mass-flow magnitude",
            "required_before_claim": "sampled exchange-interface fields and same-window UQ",
            "release_status": "not_released",
        },
        {
            "heat_path_lane": "residual",
            "current_status": "diagnostic_only_not_model_absorbed",
            "allowed_inputs": "explicit pressure and energy residual support after all physical lanes are released",
            "forbidden_inputs": "forbidden: absorbing unexplained residual into internal Nu, F6, or exchange-cell coefficient",
            "required_before_claim": "Q_wall_W, mdot_exchange*T terms, pressure basis, cp, and UQ",
            "release_status": "not_released",
        },
    ]


def build_sampler_manifest_delta(cases: list[dict[str, str]], surface_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    old_rows = read_csv(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv")
    surfaces = keyed(surface_rows, "case_id", "surface_kind")
    rows: list[dict[str, Any]] = []
    for old in old_rows:
        lane = old["input_lane"]
        case_id = old["case_id"]
        updated_status = old["status"]
        updated_path = old["available_path_or_value"]
        remaining = old["blocking_reason"]
        if lane == "exchange_interface_vtk":
            surface = surfaces[(case_id, "exchange_interface")]
            updated_status = "geometry_vtk_present_sampled_fields_absent"
            updated_path = surface["vtk_path"]
            remaining = "geometry is released, but surface VTK has no sampled U/T/rho/p arrays and no production harvest can use it yet"
        elif lane == "wall_vtk":
            surface = surfaces[(case_id, "trusted_wall")]
            updated_status = "geometry_vtk_present_wallHeatFlux_absent"
            updated_path = surface["vtk_path"]
            remaining = "geometry is released, but wall VTK has no sampled wallHeatFlux/T arrays and Q_wall_W remains unreleased"
        elif lane == "normals":
            updated_status = "normal_convention_released_for_geometry_only"
            updated_path = "positive mdot_exchange from seeded recirculation CV toward adjacent non-seed/core cells"
            remaining = "normal convention exists, but numeric sampled flux fields are absent"
        elif lane == "source_sink_release":
            updated_status = "static_context_ready_not_energy_residual_release"
            remaining = "static source/sink context still lacks Q_wall_W, cp_J_kg_K, and same-window energy residual closure"
        rows.append(
            {
                "case_id": case_id,
                "time_window_s": old["time_window_s"],
                "input_lane": lane,
                "previous_status": old["status"],
                "updated_status": updated_status,
                "updated_path_or_value": updated_path,
                "required_for_harvest": old["required_for_harvest"],
                "harvest_ready_after_this_contract": "false",
                "remaining_blocking_reason": remaining,
                "next_unlock_condition": old["unlock_condition"],
                "source_path": old["source_path"],
            }
        )
    return rows


def build_harvest_readiness_gate(cases: list[dict[str, str]], inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inv_by_case = {row["case_id"]: row for row in inventory}
    qois = [
        ("V_recirc", "input_support_ready_reduction_not_run", "recirc cell mask and volume CSV are present; diagnostic volume reduction can be a next task"),
        ("mdot_exchange", "blocked_missing_sampled_interface_U_rho", "requires sampled interface U and rho with released normal convention"),
        ("T_recirc", "input_support_ready_reduction_not_run", "recirc cell mask, volume CSV, and whole-mesh T are present, but reduction/UQ has not been run"),
        ("R_rho", "input_support_ready_reduction_not_run", "whole-mesh rho is present, but density ratio reduction/UQ has not been run"),
        ("R_mu", "blocked_missing_mu_or_nu_basis", "no mu/nu basis is present in the inventoried whole-mesh VTK fields"),
        ("pressure_residual", "blocked_missing_pressure_basis", "no p or p_rgh basis is present in the inventoried whole-mesh VTK fields"),
        ("energy_residual", "blocked_missing_Q_wall_mdot_T_cp", "requires Q_wall_W, mdot_exchange*T terms, cp_J_kg_K, and source/sink sign release"),
        ("wall_core_delta_T", "blocked_missing_sampled_wall_core_reduction", "requires wall/core band thermal reduction and sampled or mapped wall/core fields"),
    ]
    rows: list[dict[str, Any]] = []
    for case in cases:
        inv = inv_by_case[case["case_id"]]
        for qoi, status, reason in qois:
            rows.append(
                {
                    "case_id": case["case_id"],
                    "time_window_s": case["time_window_s"],
                    "qoi": qoi,
                    "input_support_status": status,
                    "geometry_support_ready": "true" if qoi in {"V_recirc", "T_recirc", "R_rho", "wall_core_delta_T", "mdot_exchange"} else "false",
                    "whole_mesh_T_U_rho_support": str(as_bool(inv["has_T"]) and as_bool(inv["has_U"]) and as_bool(inv["has_rho"])).lower(),
                    "pressure_basis_ready": inv["has_pressure_basis"],
                    "Q_wall_W_ready": "false",
                    "same_qoi_uq_ready": "false",
                    "diagnostic_harvest_allowed": "false",
                    "production_harvest_allowed": "false",
                    "coefficient_admission_allowed": "false",
                    "blocking_reason": reason,
                }
            )
    return rows


def build_downstream_gate() -> list[dict[str, Any]]:
    return [
        {
            "gate": "sampled_surface_field_extraction",
            "status": "next_best_task",
            "allowed": "true",
            "reason": "geometry VTKs, whole-mesh cell VTKs, recirc masks, face lists, and normal convention now define the extraction contract",
            "forbidden_actions": "do not call the result a harvest; do not fit or admit coefficients",
        },
        {
            "gate": "sampler_manifest_refresh",
            "status": "blocked_until_sampled_fields_and_Q_wall",
            "allowed": "false",
            "reason": "surface VTKs are geometry-only and Q_wall_W remains unreleased",
            "forbidden_actions": "do not mark sampler_ready=true from geometry-only surfaces",
        },
        {
            "gate": "exchange_cell_harvest",
            "status": "blocked",
            "allowed": "false",
            "reason": "mdot_exchange, T_recirc, Q_wall_W, pressure residual, and energy residual support are not harvested",
            "forbidden_actions": "no production harvest or scheduler launch from this contract package",
        },
        {
            "gate": "same_window_uq",
            "status": "blocked",
            "allowed": "false",
            "reason": "same-window UQ must be on exact exchange QOIs after diagnostic reductions exist",
            "forbidden_actions": "no strong claim or S11/S15 release before exact-QOI UQ",
        },
        {
            "gate": "coefficient_or_model_admission",
            "status": "blocked",
            "allowed": "false",
            "reason": "no coefficient fitting, source/property release, or model selection has been performed",
            "forbidden_actions": "no S11/S12/S13/S15/S6 trigger; no residual absorption into internal Nu",
        },
    ]


def build_guardrails() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read-only inventory of existing package artifacts"},
        {"guard_id": "registry_or_admission_mutation", "changed": "false", "policy": "no registry edit and no closure/model admission"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no sbatch/srun/tmux launch"},
        {"guard_id": "solver_or_postprocessing_launch", "changed": "false", "policy": "no OpenFOAM, ParaView, sampler, or harvest execution"},
        {"guard_id": "sampled_field_extraction", "changed": "false", "policy": "requirements only; extraction remains a future row"},
        {"guard_id": "Q_wall_W_release", "changed": "false", "policy": "Q_wall requires future wallHeatFlux integration"},
        {"guard_id": "same_qoi_uq_or_admission", "changed": "false", "policy": "no UQ/admission/S11/S12/S13/S15/S6 trigger"},
        {"guard_id": "internal_Nu_residual_absorption", "changed": "false", "policy": "residual lane remains diagnostic and not absorbed"},
        {"guard_id": "Fluid_or_external_repo_mutation", "changed": "false", "policy": "no external repo edits"},
        {"guard_id": "blocker_register_mutation", "changed": "false", "policy": "blocker register is read-only in this row"},
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    paths = [
        (SURFACE_INPUT / "case_preflight_matrix.csv", "seeded surface/mask/input preflight"),
        (SURFACE_VTK / "released_surface_vtk_manifest.csv", "geometry-only exchange/wall VTK manifest"),
        (SURFACE_VTK / "surface_vtk_validation.csv", "surface VTK count/area validation"),
        (SURFACE_VTK / "summary.json", "geometry VTK package summary"),
        (SEEDED_CV / "seeded_normal_convention.csv", "normal convention"),
        (CELL_VTK_MANIFEST / "case_vtk_input_manifest.cells_populated.csv", "whole-mesh cell VTK manifest"),
        (SOURCE_SINK / "source_sink_summary.csv", "static source/sink context"),
        (SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv", "previous sampler preflight gaps"),
        (SAME_WINDOW_UQ / "summary.json", "same-window UQ design gate"),
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


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  task_id: {TASK_ID}
  generated_at: {summary['generated_at']}
tags:
  - s13
  - upcomer
  - exchange-cell
  - heat-path
  - qwall-contract
related:
  - {rel(SURFACE_VTK / 'released_surface_vtk_manifest.csv')}
  - {rel(SURFACE_INPUT / 'case_preflight_matrix.csv')}
---

# S13 Seeded Heat-Path Lane Release

This package is a dry contract and fail-closed gate for the seeded upcomer
exchange-cell path.  It uses the released geometry-only exchange/wall VTKs,
seeded recirculation masks, whole-mesh cell VTK manifests, static source/sink
context, and the previous sampler/UQ gates.

## Outcome

- Geometry surfaces are present for Salt2/Salt3/Salt4.
- Whole-mesh cell VTKs contain `U`, `T`, `rho`, and `cellID` support.
- The package does not find `p`/`p_rgh`, `mu`/`nu`, `wallHeatFlux`, or
  `cp_J_kg_K` release.
- `Q_wall_W`, sampled interface fields, production harvest, same-window UQ,
  and coefficient/model admission remain blocked.

## Output Contract

- `field_inventory.csv`: available whole-mesh VTK fields.
- `sampled_field_lane_table.csv`: required sampled-field lanes and blockers.
- `qwall_contract.csv`: trusted-wall heat-flow convention and blocked state.
- `heat_path_lane_table.csv`: physical heat-path lanes and guardrails.
- `sampler_manifest_delta.csv`: updated sampler gaps after geometry VTK release.
- `harvest_readiness_gate.csv`: QOI-by-QOI readiness for `V_recirc`,
  `mdot_exchange`, `T_recirc`, `R_mu`, `R_rho`, pressure residual, and energy
  residual.
- `downstream_gate.csv`: allowed and forbidden next actions.

## Do Not Do

Do not treat geometry-only VTKs as sampled-field VTKs.  Do not substitute
`q_net_W` for `Q_wall_W`.  Do not absorb energy residual into internal Nu.  Do
not run sampler/harvest, fit coefficients, trigger S11/S12/S13/S15/S6, or make
strong claims before exact same-window QOI uncertainty exists.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(out_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    ensure_dir(out_dir)
    cases = case_rows()
    surface_manifest = read_csv(SURFACE_VTK / "released_surface_vtk_manifest.csv")
    surface_validation = read_csv(SURFACE_VTK / "surface_vtk_validation.csv")
    surface_rows = surface_validation
    source_rows = read_csv(SOURCE_SINK / "source_sink_summary.csv")
    uq_summary = read_json(SAME_WINDOW_UQ / "summary.json")

    field_inventory = build_field_inventory(cases)
    sampled_field_contract = build_sampled_field_contract(cases, field_inventory, surface_rows)
    qwall_contract = build_qwall_contract(cases, surface_rows, source_rows)
    heat_path_lanes = build_heat_path_lane_table()
    sampler_delta = build_sampler_manifest_delta(cases, surface_rows)
    harvest_gate = build_harvest_readiness_gate(cases, field_inventory)
    downstream_gate = build_downstream_gate()
    guardrails = build_guardrails()
    source_manifest = build_source_manifest()

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "package": rel(out_dir),
        "case_count": len(cases),
        "geometry_surface_vtk_rows": len(surface_manifest),
        "validated_geometry_surface_vtk_rows": sum(1 for row in surface_validation if as_bool(row.get("count_check")) and as_bool(row.get("area_check"))),
        "field_inventory_rows": len(field_inventory),
        "whole_mesh_cell_fields_U_T_rho_ready_rows": sum(1 for row in field_inventory if as_bool(row["has_U"]) and as_bool(row["has_T"]) and as_bool(row["has_rho"])),
        "pressure_basis_ready_rows": sum(1 for row in field_inventory if as_bool(row["has_pressure_basis"])),
        "mu_basis_ready_rows": sum(1 for row in field_inventory if as_bool(row["has_mu_basis"])),
        "wallHeatFlux_ready_rows": sum(1 for row in field_inventory if as_bool(row["has_wallHeatFlux"])),
        "Q_wall_W_released_rows": sum(1 for row in qwall_contract if as_bool(row["Q_wall_W_released"])),
        "sampled_surface_field_ready_rows": sum(1 for row in sampled_field_contract if as_bool(row["sampled_surface_field_present"])),
        "sampler_ready_rows": sum(1 for row in sampled_field_contract if as_bool(row["sampler_ready"])),
        "harvest_ready_rows": sum(1 for row in harvest_gate if as_bool(row["production_harvest_allowed"])),
        "same_qoi_uq_ready": bool(uq_summary.get("uq_release_allowed")),
        "exchange_cell_admission_allowed": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "sampled_field_extraction_launched": False,
        "sampler_or_harvest_launched": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "Fluid_or_external_repo_mutation": False,
        "fitting_or_model_selection": False,
        "blocker_register_change": False,
        "residual_absorbed_into_internal_nu": False,
    }

    csv_dump(out_dir / "field_inventory.csv", list(field_inventory[0]), field_inventory)
    csv_dump(out_dir / "sampled_field_lane_table.csv", list(sampled_field_contract[0]), sampled_field_contract)
    csv_dump(out_dir / "qwall_contract.csv", list(qwall_contract[0]), qwall_contract)
    csv_dump(out_dir / "q_wall_source_contract.csv", list(qwall_contract[0]), qwall_contract)
    csv_dump(out_dir / "heat_path_lane_table.csv", list(heat_path_lanes[0]), heat_path_lanes)
    csv_dump(out_dir / "heat_path_lane_release.csv", list(heat_path_lanes[0]), heat_path_lanes)
    csv_dump(out_dir / "same_window_thermal_field_contract.csv", list(sampled_field_contract[0]), sampled_field_contract)
    csv_dump(out_dir / "same_window_thermal_pressure_field_contract.csv", list(sampled_field_contract[0]), sampled_field_contract)
    csv_dump(out_dir / "sampler_manifest_delta.csv", list(sampler_delta[0]), sampler_delta)
    csv_dump(out_dir / "harvest_readiness_gate.csv", list(harvest_gate[0]), harvest_gate)
    csv_dump(out_dir / "downstream_gate.csv", list(downstream_gate[0]), downstream_gate)
    csv_dump(out_dir / "sampler_refresh_gate.csv", list(downstream_gate[0]), downstream_gate)
    csv_dump(out_dir / "no_mutation_guardrails.csv", list(guardrails[0]), guardrails)
    csv_dump(out_dir / "source_manifest.csv", list(source_manifest[0]), source_manifest)
    json_dump(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return {
        "summary": summary,
        "field_inventory": field_inventory,
        "sampled_field_contract": sampled_field_contract,
        "qwall_contract": qwall_contract,
        "heat_path_lanes": heat_path_lanes,
        "sampler_delta": sampler_delta,
        "harvest_gate": harvest_gate,
        "downstream_gate": downstream_gate,
        "guardrails": guardrails,
        "source_manifest": source_manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=PACKAGE_DIR)
    args = parser.parse_args()
    payload = build_package(args.out_dir)
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
