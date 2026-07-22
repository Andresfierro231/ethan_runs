#!/usr/bin/env python3
"""Build the S13 sampled-field and Q_wall contract from seeded VTKs.

This is a preflight contract only. It consumes released S13 geometry and
heat-path packages, defines the exact next extraction inputs, and keeps sampler,
harvest, UQ, admission, and S12/S15/S6 triggers closed.
"""

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

TASK_ID = "TODO-S13-UPCOMER-EXCHANGE-SAMPLED-FIELD-QWALL-CONTRACT-FROM-SEEDED-VTK-2026-07-21"
OUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk"

SURFACE_INPUT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv"
SURFACE_VTK = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv"
HEAT_PATH = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release"
SOURCE_SINK = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation"


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_bool(value: Any) -> bool:
    return str(value).lower() == "true"


def key(rows: list[dict[str, str]], *columns: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row[column] for column in columns): row for row in rows}


def case_rows() -> list[dict[str, str]]:
    return read_csv(SURFACE_INPUT / "seeded_surface_input_manifest.csv")


def build_source_file_availability(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    required = [
        ("cell_vtk", "whole-mesh U/T/rho/cellID source", "false"),
        ("volume_csv", "cell-volume support for recirc reductions", "false"),
        ("recirc_cell_mask", "seeded recirculation CV mask", "false"),
        ("exchange_interface_faces_csv", "exchange interface face IDs", "false"),
        ("trusted_wall_faces_csv", "trusted wall face IDs", "false"),
        ("wall_core_band_csv", "wall/core thermal band definition", "false"),
        ("source_sink_summary_csv", "static source/sink context, not Q_wall_W", "false"),
    ]
    rows: list[dict[str, Any]] = []
    for case in cases:
        for column, role, native in required:
            path = ROOT / case[column]
            rows.append(
                {
                    "case_id": case["case_id"],
                    "time_window_s": case["time_window_s"],
                    "input_name": column,
                    "path": case[column],
                    "exists": str(path.exists()).lower(),
                    "role": role,
                    "native_solver_output": native,
                    "mutated": "false",
                    "contract_status": "ready_read_only" if path.exists() else "blocked_missing_file",
                }
            )
    return rows


def build_field_availability_matrix() -> list[dict[str, Any]]:
    inventory = read_csv(HEAT_PATH / "field_inventory.csv")
    lanes = read_csv(HEAT_PATH / "sampled_field_lane_table.csv")
    lane_by_case = key(lanes, "case_id", "lane")
    rows: list[dict[str, Any]] = []
    for inv in inventory:
        case_id = inv["case_id"]
        for field, field_kind, lane in [
            ("U", "whole_mesh_cell", "interface_U"),
            ("T", "whole_mesh_cell", "interface_T"),
            ("rho", "whole_mesh_cell", "interface_rho"),
            ("T", "trusted_wall_surface", "wall_T"),
            ("p_or_p_rgh", "whole_mesh_or_surface", "interface_pressure"),
            ("wallHeatFlux", "trusted_wall_surface", "wallHeatFlux"),
            ("mu_or_nu", "whole_mesh_cell", "mu_or_nu"),
            ("cp_J_kg_K", "property_contract", "cp_J_kg_K"),
        ]:
            lane_row = lane_by_case[(case_id, lane)]
            whole_mesh_present = lane_row["whole_mesh_field_present"]
            rows.append(
                {
                    "case_id": case_id,
                    "time_window_s": inv["time_window_s"],
                    "field_or_property": field,
                    "field_kind": field_kind,
                    "required_lane": lane,
                    "geometry_or_mask_ready": lane_row["geometry_or_mask_ready"],
                    "whole_mesh_or_property_present": whole_mesh_present,
                    "sampled_surface_field_present": lane_row["sampled_surface_field_present"],
                    "contract_status": lane_row["status"],
                    "next_action": next_action_for_lane(lane_row),
                    "source_path": lane_row["source_path"],
                }
            )
    return rows


def next_action_for_lane(row: dict[str, str]) -> str:
    lane = row["lane"]
    if row["status"] == "geometry_ready_whole_mesh_field_present_surface_sampling_not_run":
        return "eligible_for_limited_scheduler_sampled_field_extraction"
    if row["status"] == "input_support_ready_reduction_not_run":
        return "eligible_for_diagnostic_mask_reduction_after_sampled_field_row"
    if lane == "interface_pressure":
        return "find_or_generate same-window p/p_rgh basis before pressure residual"
    if lane == "wallHeatFlux":
        return "find_or generate same-window wallHeatFlux field before Q_wall_W integration"
    if lane == "mu_or_nu":
        return "define runtime-legal viscosity/property source before R_mu"
    if lane == "cp_J_kg_K":
        return "release cp property value and provenance before energy residual"
    return "remain_blocked_until_required_input_is_released"


def build_face_to_cell_mapping_preflight(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    surface = key(read_csv(SURFACE_VTK / "surface_vtk_validation.csv"), "case_id", "surface_kind")
    rows: list[dict[str, Any]] = []
    for case in cases:
        for surface_kind, face_column in [
            ("exchange_interface", "exchange_interface_faces_csv"),
            ("trusted_wall", "trusted_wall_faces_csv"),
        ]:
            surf = surface[(case["case_id"], surface_kind)]
            owner_neighbour_contract = (
                "owner/neighbour define outward seeded-CV exchange normal; positive mdot leaves seeded recirc CV"
                if surface_kind == "exchange_interface"
                else "boundary owner cells map trusted wall area; wall normal follows OpenFOAM boundary orientation"
            )
            rows.append(
                {
                    "case_id": case["case_id"],
                    "time_window_s": case["time_window_s"],
                    "surface_kind": surface_kind,
                    "face_csv": case[face_column],
                    "geometry_vtk": surf["vtk_path"],
                    "face_count": surf["expected_face_count"],
                    "area_m2": surf["vtk_area_m2"],
                    "count_check": surf["count_check"],
                    "area_check": surf["area_check"],
                    "owner_neighbour_contract": owner_neighbour_contract,
                    "mapping_status": "ready_for_contract_extraction_not_run",
                    "extraction_launched": "false",
                }
            )
    return rows


def build_sign_cp_convention_contract(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        cp_present = bool(case.get("cp_J_kg_K"))
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "positive_mdot_exchange_convention": case["positive_flux_convention"],
                "positive_Q_wall_W_convention": "positive Q_wall_W adds heat to the seeded recirculation/exchange CV fluid",
                "source_sink_sign_context": "q_source_W and q_sink_W are static context; q_net_W is not Q_wall_W",
                "cp_J_kg_K": case.get("cp_J_kg_K", ""),
                "cp_released": str(cp_present).lower(),
                "default_cp_allowed": "false",
                "contract_status": "ready_except_cp" if not cp_present else "ready",
                "blocking_reason": "" if cp_present else "cp_J_kg_K is not released; energy residual and Q_wall enthalpy closure remain blocked",
            }
        )
    return rows


def build_wall_heat_integration_contract(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    qwall = key(read_csv(HEAT_PATH / "qwall_contract.csv"), "case_id")
    rows: list[dict[str, Any]] = []
    for case in cases:
        row = qwall[(case["case_id"],)]
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "trusted_wall_vtk": row["trusted_wall_vtk"],
                "trusted_wall_area_m2": row["trusted_wall_area_m2"],
                "required_field": "wallHeatFlux",
                "wallHeatFlux_source_exists": row["wallHeatFlux_source_exists"],
                "integration_formula": "Q_wall_W = sum_i(wallHeatFlux_i * area_i) over released trusted_wall faces after sign convention check",
                "q_net_W_static_context_not_substitute": row["q_net_W_static_context_not_Q_wall"],
                "Q_wall_W_released": row["Q_wall_W_released"],
                "contract_status": "blocked_missing_wallHeatFlux",
                "blocking_reason": row["blocking_reason"],
            }
        )
    return rows


def build_extraction_input_contract(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    harvest = read_csv(HEAT_PATH / "harvest_readiness_gate.csv")
    rows: list[dict[str, Any]] = []
    for h in harvest:
        qoi = h["qoi"]
        if qoi in {"V_recirc", "T_recirc", "R_rho"}:
            next_row_permission = "diagnostic_reduction_allowed_after_limited_field_extraction"
        elif qoi in {"mdot_exchange", "wall_core_delta_T"}:
            next_row_permission = "limited_scheduler_sampled_field_extraction_open"
        else:
            next_row_permission = "blocked_missing_contract_input"
        rows.append(
            {
                "case_id": h["case_id"],
                "time_window_s": h["time_window_s"],
                "qoi": qoi,
                "input_support_status": h["input_support_status"],
                "required_before_production_harvest": production_requirement(qoi),
                "next_row_permission": next_row_permission,
                "production_harvest_allowed": "false",
                "same_qoi_uq_required": "true",
                "admission_allowed": "false",
                "blocking_reason": h["blocking_reason"],
            }
        )
    return rows


def production_requirement(qoi: str) -> str:
    return {
        "V_recirc": "recirc cell volume reduction plus same-QOI uncertainty",
        "mdot_exchange": "sampled exchange interface U/rho with normal convention plus same-QOI uncertainty",
        "T_recirc": "recirc-mask T reduction plus same-QOI uncertainty",
        "R_rho": "recirc/core rho reduction plus same-QOI uncertainty",
        "R_mu": "mu/nu property basis plus same-QOI uncertainty",
        "pressure_residual": "same-window p/p_rgh basis plus pressure residual definition and UQ",
        "energy_residual": "Q_wall_W, mdot*T terms, cp, source/sink sign release, and UQ",
        "wall_core_delta_T": "wall/core thermal sampled or mapped reduction plus UQ",
    }.get(qoi, "explicit QOI contract")


def build_sampler_refresh_gate() -> list[dict[str, Any]]:
    return [
        {
            "gate": "limited_scheduler_sampled_field_extraction",
            "status": "open_limited",
            "allowed": "true",
            "reason": "released geometry VTKs and whole-mesh U/T/rho support are present for interface and wall-temperature sampling only",
            "forbidden_actions": "do not label output sampler_ready, production_harvest_ready, Q_wall_W_ready, or admitted",
        },
        {
            "gate": "Q_wall_W_extraction",
            "status": "blocked",
            "allowed": "false",
            "reason": "no wallHeatFlux source field is released",
            "forbidden_actions": "do not substitute q_net_W or source/sink totals for Q_wall_W",
        },
        {
            "gate": "sampler_manifest_refresh",
            "status": "blocked",
            "allowed": "false",
            "reason": "pressure, viscosity, cp, Q_wall_W, and sampled fields are not complete",
            "forbidden_actions": "do not mark sampler_ready=true",
        },
        {
            "gate": "production_harvest_or_same_qoi_uq",
            "status": "blocked",
            "allowed": "false",
            "reason": "exact harvested exchange QOIs do not exist yet",
            "forbidden_actions": "no harvest, UQ, coefficient fit, or S11/S12/S15/S6 trigger",
        },
    ]


def build_sampled_field_scheduler_decision(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case["case_id"],
            "time_window_s": case["time_window_s"],
            "decision_lane": "next_scheduler_authorized_sampled_field_row",
            "decision": "open_limited_nonharvest_field_sampling",
            "allowed": "true",
            "runtime_legal_scope": "sample existing U/T/rho and wall/core T support on released seeded geometry; report p/mu/wallHeatFlux/cp lanes as absent",
            "explicitly_forbidden_scope": "no Q_wall_W release; no pressure or energy residual closure; no sampler refresh; no production harvest; no same-QOI UQ; no coefficient admission; no S11/S12/S13/S15/S6 trigger",
            "reason": "geometry, seeded masks, face maps, normal convention, and whole-mesh U/T/rho exist, but Q_wall_W/p/mu/cp/residual/UQ/admission lanes remain absent",
        }
        for case in cases
    ]


def build_s13_unlock_impact(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case["case_id"],
            "time_window_s": case["time_window_s"],
            "current_impact": "opens_limited_sampled_field_extraction_only",
            "what_is_unlocked": "scheduler-authorized diagnostic extraction for U/T/rho/T-wall fields from seeded geometry",
            "still_blocked": "Q_wall_W, pressure residual, R_mu, cp, production harvest, same-QOI UQ, coefficient admission",
            "s13_candidate_or_admission_trigger_allowed": "false",
            "reason": "field evidence can be gathered next, but the exchange-cell heat and residual basis is incomplete",
        }
        for case in cases
    ]


def build_s12_unlock_impact(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case["case_id"],
            "time_window_s": case["time_window_s"],
            "current_impact": "blocked",
            "what_is_unlocked": "none for train scoring or freeze",
            "still_blocked": "no S13 admitted candidate, no Q_wall_W, no source/property release, no attribution package",
            "s12_trigger_allowed": "false",
            "reason": "limited sampled-field extraction is diagnostic support and cannot unlock S12 train/freeze work",
        }
        for case in cases
    ]


def build_unlock_impact(cases: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in build_s13_unlock_impact(cases):
        rows.append(
            {
                "case_id": row["case_id"],
                "time_window_s": row["time_window_s"],
                "target": "S13",
                "current_impact": row["current_impact"],
                "what_is_unlocked": row["what_is_unlocked"],
                "still_blocked": row["still_blocked"],
                "trigger_allowed": row["s13_candidate_or_admission_trigger_allowed"],
            }
        )
    for row in build_s12_unlock_impact(cases):
        rows.append(
            {
                "case_id": row["case_id"],
                "time_window_s": row["time_window_s"],
                "target": "S12",
                "current_impact": row["current_impact"],
                "what_is_unlocked": row["what_is_unlocked"],
                "still_blocked": row["still_blocked"],
                "trigger_allowed": row["s12_trigger_allowed"],
            }
        )
    return rows


def build_downstream_gate() -> list[dict[str, Any]]:
    return [
        {
            "gate": "next_executable_row",
            "decision": "open_limited_scheduler_sampled_field_extraction",
            "allowed": "true",
            "condition": "sample interface U/T/rho and wall/core T only; report missing wallHeatFlux/p/mu/cp separately",
        },
        {
            "gate": "Q_wall_W_release",
            "decision": "blocked",
            "allowed": "false",
            "condition": "requires same-window wallHeatFlux on trusted_wall faces",
        },
        {
            "gate": "sampler_refresh",
            "decision": "blocked",
            "allowed": "false",
            "condition": "requires sampled fields plus Q_wall_W/cp/pressure/viscosity contract completion",
        },
        {
            "gate": "production_harvest_UQ_admission",
            "decision": "blocked",
            "allowed": "false",
            "condition": "requires harvested exact QOIs and same-window UQ; no admission from this contract",
        },
    ]


def build_guardrails() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_output_mutation", "changed": "false", "policy": "read-only package/manifests only"},
        {"guard_id": "scheduler_action", "changed": "false", "policy": "no sbatch/srun/tmux launch"},
        {"guard_id": "solver_or_postprocessing", "changed": "false", "policy": "no OpenFOAM, sampler, or postprocessing execution"},
        {"guard_id": "field_sampling", "changed": "false", "policy": "contract only; sampled-field extraction remains a later row"},
        {"guard_id": "registry_or_admission", "changed": "false", "policy": "no registry mutation and no coefficient/model admission"},
        {"guard_id": "Fluid_or_external_repo", "changed": "false", "policy": "no external edits"},
        {"guard_id": "S11_S12_S13_S15_S6_trigger", "changed": "false", "policy": "all candidate/freeze/score triggers remain closed"},
        {"guard_id": "internal_Nu_residual_absorption", "changed": "false", "policy": "no residual absorption into internal Nu"},
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    paths = [
        (SURFACE_INPUT / "seeded_surface_input_manifest.csv", "case-level seeded surface/input manifest"),
        (SURFACE_VTK / "surface_vtk_validation.csv", "geometry VTK validation"),
        (SURFACE_VTK / "released_surface_vtk_manifest.csv", "geometry VTK manifest"),
        (HEAT_PATH / "field_inventory.csv", "field availability input"),
        (HEAT_PATH / "sampled_field_lane_table.csv", "sampled lane blocker input"),
        (HEAT_PATH / "qwall_contract.csv", "prior Q_wall blocked contract"),
        (HEAT_PATH / "harvest_readiness_gate.csv", "QOI readiness input"),
        (SOURCE_SINK / "source_sink_summary.csv", "static source/sink context"),
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


def write_readme(out: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SURFACE_INPUT / 'seeded_surface_input_manifest.csv')}
  - {rel(SURFACE_VTK / 'surface_vtk_validation.csv')}
  - {rel(HEAT_PATH / 'field_inventory.csv')}
  - {rel(HEAT_PATH / 'qwall_contract.csv')}
tags: [s13, upcomer-exchange, sampled-field-contract, qwall-contract]
related:
  - .agent/status/2026-07-21_{TASK_ID}.md
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_contract_limited_extraction_open
---
# S13 Sampled-Field and Q_wall Contract from Seeded VTK

This package defines the next exact extraction contract after the seeded
geometry-only VTK release. It does not run a sampler, harvest QOIs, integrate
`Q_wall_W`, fit coefficients, or trigger S11/S12/S15/S6.

Decision: `open_limited_scheduler_sampled_field_extraction`.

- cases: `{summary['case_count']}`
- source files ready: `{summary['ready_source_file_rows']}/{summary['source_file_rows']}`
- geometry mappings ready: `{summary['ready_face_mapping_rows']}/{summary['face_mapping_rows']}`
- limited sampled-field lanes open: `{summary['limited_sampled_field_lanes_open']}`
- scheduler-authorized sampled-field rows open: `{summary['scheduler_authorized_sampled_field_rows_open']}`
- `Q_wall_W` released rows: `{summary['Q_wall_W_released_rows']}`
- sampler refresh allowed: `{str(summary['sampler_refresh_allowed']).lower()}`
- production harvest allowed: `{str(summary['production_harvest_allowed']).lower()}`
- S11/S12/S15/S6 trigger: `{str(summary['s11_s12_s15_s6_trigger']).lower()}`

## Contract

The next executable row may sample interface `U/T/rho` and wall/core `T` from
the released seeded surfaces. It must report missing `wallHeatFlux`, `p/p_rgh`,
`mu/nu`, and `cp_J_kg_K` as blockers rather than silently substituting other
quantities.

`sampled_field_scheduler_decision.csv` is the authoritative next-row decision:
the limited field-sampling row is open for all three cases, while `Q_wall_W`,
residual closure, sampler refresh, production harvest, UQ, and admission remain
closed. `s13_unlock_impact.csv` and `s12_unlock_impact.csv` record the per-case
unlock status for Salt2/Salt3/Salt4.

## Guardrails

`q_net_W` is static source/sink context, not `Q_wall_W`. The geometry-only VTKs
are not sampler-ready outputs. No production harvest, same-QOI UQ, coefficient
admission, source/property release, freeze, or score trigger is released here.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def build_package(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    cases = case_rows()
    source_files = build_source_file_availability(cases)
    fields = build_field_availability_matrix()
    mapping = build_face_to_cell_mapping_preflight(cases)
    sign_cp = build_sign_cp_convention_contract(cases)
    qwall = build_wall_heat_integration_contract(cases)
    extraction = build_extraction_input_contract(cases)
    sampler_gate = build_sampler_refresh_gate()
    scheduler_decision = build_sampled_field_scheduler_decision(cases)
    s13_unlock = build_s13_unlock_impact(cases)
    s12_unlock = build_s12_unlock_impact(cases)
    unlock = build_unlock_impact(cases)
    downstream = build_downstream_gate()
    guardrails = build_guardrails()
    sources = build_source_manifest()

    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "package": rel(out),
        "case_count": len(cases),
        "source_file_rows": len(source_files),
        "ready_source_file_rows": sum(1 for row in source_files if row["contract_status"] == "ready_read_only"),
        "field_availability_rows": len(fields),
        "limited_sampled_field_lanes_open": sum(1 for row in fields if row["next_action"] == "eligible_for_limited_scheduler_sampled_field_extraction"),
        "blocked_pressure_rows": sum(1 for row in fields if row["field_or_property"] == "p_or_p_rgh" and row["contract_status"] == "blocked_missing_pressure_basis"),
        "blocked_wallHeatFlux_rows": sum(1 for row in fields if row["field_or_property"] == "wallHeatFlux" and row["contract_status"] == "blocked_missing_wallHeatFlux_Q_wall"),
        "blocked_mu_rows": sum(1 for row in fields if row["field_or_property"] == "mu_or_nu" and row["contract_status"] == "blocked_missing_mu_or_nu_basis"),
        "blocked_cp_rows": sum(1 for row in fields if row["field_or_property"] == "cp_J_kg_K" and row["contract_status"] == "blocked_missing_cp_property_contract"),
        "face_mapping_rows": len(mapping),
        "ready_face_mapping_rows": sum(1 for row in mapping if row["mapping_status"] == "ready_for_contract_extraction_not_run"),
        "Q_wall_W_released_rows": sum(1 for row in qwall if as_bool(row["Q_wall_W_released"])),
        "scheduler_authorized_sampled_field_rows_open": sum(1 for row in scheduler_decision if as_bool(row["allowed"])),
        "s13_unlock_rows": len(s13_unlock),
        "s12_unlock_rows": len(s12_unlock),
        "limited_scheduler_sampled_field_row_open": True,
        "Q_wall_W_extraction_allowed": False,
        "sampler_refresh_allowed": False,
        "production_harvest_allowed": False,
        "same_qoi_uq_ready": False,
        "exchange_cell_admission_allowed": False,
        "s11_s12_s15_s6_trigger": False,
        "scheduler_action": False,
        "field_sampling_launched": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "Fluid_or_external_repo_mutation": False,
        "fitting_or_model_selection": False,
        "residual_absorbed_into_internal_nu": False,
    }

    csv_dump(out / "source_file_availability.csv", list(source_files[0]), source_files)
    csv_dump(out / "source_file_contract.csv", list(source_files[0]), source_files)
    csv_dump(out / "field_availability_matrix.csv", list(fields[0]), fields)
    csv_dump(out / "field_availability.csv", list(fields[0]), fields)
    csv_dump(out / "face_to_cell_mapping_preflight.csv", list(mapping[0]), mapping)
    csv_dump(out / "face_to_cell_mapping_contract.csv", list(mapping[0]), mapping)
    csv_dump(out / "sign_cp_convention_contract.csv", list(sign_cp[0]), sign_cp)
    csv_dump(out / "wall_heat_integration_contract.csv", list(qwall[0]), qwall)
    csv_dump(out / "extraction_input_contract.csv", list(extraction[0]), extraction)
    csv_dump(out / "sampler_refresh_gate.csv", list(sampler_gate[0]), sampler_gate)
    csv_dump(out / "sampled_field_scheduler_decision.csv", list(scheduler_decision[0]), scheduler_decision)
    csv_dump(out / "s13_unlock_impact.csv", list(s13_unlock[0]), s13_unlock)
    csv_dump(out / "s12_unlock_impact.csv", list(s12_unlock[0]), s12_unlock)
    csv_dump(out / "s13_s12_unlock_impact.csv", list(unlock[0]), unlock)
    csv_dump(out / "downstream_gate.csv", list(downstream[0]), downstream)
    csv_dump(out / "no_mutation_guardrails.csv", list(guardrails[0]), guardrails)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    json_dump(out / "summary.json", summary)
    write_readme(out, summary)
    return {
        "summary": summary,
        "source_files": source_files,
        "fields": fields,
        "mapping": mapping,
        "sign_cp": sign_cp,
        "qwall": qwall,
        "extraction": extraction,
        "sampler_gate": sampler_gate,
        "scheduler_decision": scheduler_decision,
        "s13_unlock": s13_unlock,
        "s12_unlock": s12_unlock,
        "unlock": unlock,
        "downstream": downstream,
        "guardrails": guardrails,
        "sources": sources,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    args = parser.parse_args()
    payload = build_package(args.out_dir)
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
