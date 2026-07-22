#!/usr/bin/env python3
"""Build a read-only S13 next-gate checklist and blocker-unlock package."""

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

TASK_ID = "TODO-S13-NEXT-GATE-CHECKLIST-AND-BLOCKER-UNLOCKS-2026-07-21"
PACKAGE_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_next_gate_checklist_and_blocker_unlocks"

GEOM_SEED = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed"
SHORT_RERUN = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_source_bounded_cv_rerun_from_geometry_seed"
SEEDED_RERUN = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed"
TOPOLOGY_CV = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release"
ALT_CV = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv"
DIAG_BRIDGE = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge"
SAMPLER_PREFLIGHT = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight"
SAME_WINDOW_UQ = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design"
BOARD = ROOT / ".agent/BOARD.md"

NEXT_GATE_FIELDS = [
    "sequence",
    "gate_id",
    "gate_name",
    "current_status",
    "ready_for_next_action",
    "allowed_next_action",
    "required_runtime_inputs",
    "forbidden_inputs_or_actions",
    "expected_outputs",
    "current_blocker",
    "evidence_paths",
]
EVIDENCE_FIELDS = [
    "evidence_id",
    "lane",
    "evidence_type",
    "status",
    "key_observation",
    "effect_on_next_gate",
    "evidence_paths",
]
BLOCKER_FIELDS = [
    "priority",
    "blocker_id",
    "lane",
    "current_status",
    "unlock_action",
    "compute_policy",
    "forbidden_actions",
    "evidence_paths",
]
HEAT_PATH_FIELDS = [
    "heat_path_lane",
    "current_input_status",
    "allowed_runtime_inputs",
    "forbidden_inputs",
    "required_outputs",
    "current_blocker",
    "next_unlock",
]
GUARD_FIELDS = ["guard_id", "status", "policy"]
MANIFEST_FIELDS = ["path", "role", "exists", "native_solver_output", "mutated"]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def all_true(rows: list[dict[str, str]], field: str) -> bool:
    return bool(rows) and all(row.get(field, "").lower() == "true" for row in rows)


def count_status(rows: list[dict[str, str]], field: str, value: str) -> int:
    return sum(1 for row in rows if row.get(field) == value)


def active_board_contains(task_id: str) -> bool:
    text = BOARD.read_text(encoding="utf-8")
    active = text.split("## Archived Complete", 1)[0]
    return task_id in active


def source_stats() -> dict[str, Any]:
    geom_rows = read_csv(GEOM_SEED / "geometry_seed_case_summary.csv")
    short_release = read_csv(SHORT_RERUN / "seed_cv_release_decision.csv")
    seeded_release = read_csv(SEEDED_RERUN / "seeded_release_decision.csv")
    seeded_seed_cv = read_csv(SEEDED_RERUN / "seed_cv_release_decision.csv")
    sampler_gaps = read_csv(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv")
    same_window_rows = read_csv(SAME_WINDOW_UQ / "qoi_release_decision.csv")
    topology_rows = read_csv(TOPOLOGY_CV / "topology_cv_case_summary.csv")
    alt_rows = read_csv(ALT_CV / "alternate_cv_case_summary.csv")
    diag_rows = read_csv(DIAG_BRIDGE / "diagnostic_roi_average_bridge.csv")
    return {
        "case_count": len(geom_rows),
        "geometry_seed_ready_count": count_status(geom_rows, "source_bounded_cv_rerun_ready", "true"),
        "short_surface_ready_count": count_status(short_release, "surface_extraction_ready", "true"),
        "seeded_surface_preflight_ready_count": count_status(seeded_release, "surface_preflight_ready", "true"),
        "seeded_production_cv_released_count": count_status(seeded_seed_cv, "production_source_bounded_cv_released", "true"),
        "seeded_interface_faces_exists": (SEEDED_RERUN / "seeded_exchange_interface_faces.csv").exists(),
        "seeded_wall_faces_exists": (SEEDED_RERUN / "seeded_trusted_wall_faces.csv").exists(),
        "seeded_cells_exists": (SEEDED_RERUN / "seeded_recirc_cv_cells.csv").exists(),
        "sampler_ready_count": count_status(sampler_gaps, "status", "ready"),
        "sampler_blocked_count": sum(1 for row in sampler_gaps if row.get("status", "").startswith("blocked")),
        "same_qoi_release_allowed_count": count_status(same_window_rows, "release_allowed_now", "true"),
        "topology_released_count": sum(1 for row in topology_rows if row.get("topology_release_status", "").startswith("released")),
        "alt_released_count": sum(1 for row in alt_rows if row.get("selected_alt_release_status", "").startswith("released")),
        "diagnostic_proxy_rows": len(diag_rows),
        "active_short_rerun": active_board_contains("TODO-S13-SOURCE-BOUNDED-CV-RERUN-FROM-GEOMETRY-SEED-2026-07-21"),
        "active_long_rerun": active_board_contains("TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-RERUN-FROM-GEOMETRY-SEED-2026-07-21"),
    }


def build_next_gate_checklist(stats: dict[str, Any]) -> list[dict[str, Any]]:
    surface_preflight_ready = (
        stats["seeded_surface_preflight_ready_count"] == stats["case_count"]
        and stats["seeded_interface_faces_exists"]
        and stats["seeded_wall_faces_exists"]
    )
    overlap_status = "coordination_needed" if stats["active_short_rerun"] and stats["active_long_rerun"] else "clear"
    return [
        {
            "sequence": 1,
            "gate_id": "S13-G0-board-coordination",
            "gate_name": "Resolve overlapping active S13 rerun rows",
            "current_status": overlap_status,
            "ready_for_next_action": str(overlap_status == "clear").lower(),
            "allowed_next_action": "archive or reconcile completed rerun rows before assigning new S13 extraction work",
            "required_runtime_inputs": "none",
            "forbidden_inputs_or_actions": "do not launch duplicate surface/sampler work from overlapping board ownership",
            "expected_outputs": "single canonical S13 rerun handoff named in the next task row",
            "current_blocker": "two active S13 rerun rows are visible; one is short-name geometry release and one is seeded surface-preflight handoff",
            "evidence_paths": rel(BOARD),
        },
        {
            "sequence": 2,
            "gate_id": "S13-G1-geometry-seed",
            "gate_name": "Geometry seed and trusted wall/interface lanes",
            "current_status": "pass" if stats["geometry_seed_ready_count"] == stats["case_count"] else "blocked",
            "ready_for_next_action": str(stats["geometry_seed_ready_count"] == stats["case_count"]).lower(),
            "allowed_next_action": "use released seed cells, trusted wall faces, internal seed/core interface, caps, and normal convention as source-bounded surface-preflight inputs",
            "required_runtime_inputs": "geometry seed rows, trusted wall faces, internal seed/core interface faces, classified caps, zero unclassified escapes",
            "forbidden_inputs_or_actions": "reverse-flow occupancy threshold relaxation; proxy-interface admission; residual absorption into internal Nu",
            "expected_outputs": "surface/input preflight using seeded face lists and wall/core-band policy",
            "current_blocker": "none for geometry; production exchange-state admission still not released",
            "evidence_paths": f"{rel(GEOM_SEED / 'geometry_seed_case_summary.csv')};{rel(GEOM_SEED / 'geometry_seed_surface_contract.csv')}",
        },
        {
            "sequence": 3,
            "gate_id": "S13-G2-seeded-surface-input-preflight",
            "gate_name": "Seeded surface/input preflight",
            "current_status": "ready_for_separate_row" if surface_preflight_ready else "blocked_missing_seeded_face_lists",
            "ready_for_next_action": str(surface_preflight_ready).lower(),
            "allowed_next_action": "claim a separate surface/input preflight row to extract or fail-close interface/wall surfaces, normals, Q_wall/source lanes, and same-window field contract",
            "required_runtime_inputs": "seeded_exchange_interface_faces.csv, seeded_trusted_wall_faces.csv, seeded_recirc_cv_cells.csv, normal convention, downstream gate",
            "forbidden_inputs_or_actions": "production harvest, sampler launch, UQ/admission, Fluid edit, or coefficient fitting from this checklist",
            "expected_outputs": "surface VTK/input manifest fragment plus explicit pass/fail for wall_vtk, interface_vtk, normals, Q_wall_W/source, same-window thermal fields",
            "current_blocker": "surface/input preflight has not been run; production_exchange_interface remains blocked until exchange-state CV is admitted",
            "evidence_paths": f"{rel(SEEDED_RERUN / 'downstream_gate.csv')};{rel(SEEDED_RERUN / 'seeded_exchange_interface_faces.csv')};{rel(SEEDED_RERUN / 'seeded_trusted_wall_faces.csv')}",
        },
        {
            "sequence": 4,
            "gate_id": "S13-G3-heat-path-release",
            "gate_name": "Q_wall/source/same-window heat-path release",
            "current_status": "blocked",
            "ready_for_next_action": "false",
            "allowed_next_action": "after surface/input preflight passes, integrate or release heat-path lanes with sign convention and provenance",
            "required_runtime_inputs": "wallHeatFlux or source-side Q_wall_W, source/sink ledger, cp_J_kg_K, sign convention, wall/core/bulk same-window fields",
            "forbidden_inputs_or_actions": "using q_net proxy as a coefficient; hiding residual heat in internal Nu; fitting before UQ",
            "expected_outputs": "Q_wall_W/source release ledger and same-window thermal field table",
            "current_blocker": "old sampler preflight still marks Q_wall_W, source_sink_release, and same_window_thermal_fields blocked",
            "evidence_paths": rel(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv"),
        },
        {
            "sequence": 5,
            "gate_id": "S13-G4-sampler-manifest-refresh",
            "gate_name": "Sampler manifest refresh",
            "current_status": "blocked",
            "ready_for_next_action": "false",
            "allowed_next_action": "rerun sampler manifest preflight only after surface/input and heat-path rows pass",
            "required_runtime_inputs": "cell VTK, volume CSV, exchange_interface_vtk, wall_vtk, normals, Q_wall_W/source lane, same-window thermal fields",
            "forbidden_inputs_or_actions": "production harvest with sampler_ready=false",
            "expected_outputs": "3/3 sampler-ready manifest rows or exact fail-closed gap matrix",
            "current_blocker": f"blocked sampler inputs remain {stats['sampler_blocked_count']}; ready inputs are only cell VTK/volume CSV lanes",
            "evidence_paths": rel(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv"),
        },
        {
            "sequence": 6,
            "gate_id": "S13-G5-harvest-uq-admission",
            "gate_name": "Production harvest, same-QOI UQ, and candidate review",
            "current_status": "blocked",
            "ready_for_next_action": "false",
            "allowed_next_action": "harvest exchange QOIs only after 3/3 sampler-ready; run same-QOI UQ before S11/S12/S15/S6",
            "required_runtime_inputs": "V_recirc, mdot_exchange, tau_recirc, Q_wall/source, same-window pressure/thermal residuals, same-QOI mesh/time UQ",
            "forbidden_inputs_or_actions": "S11/S12/S15/S6 trigger; final scoring; coefficient admission; internal-Nu residual absorption",
            "expected_outputs": "exchange-QOI harvest table, UQ table, source/property/split gate decision, candidate-or-no-candidate result",
            "current_blocker": "same-window UQ and production harvest are not available",
            "evidence_paths": f"{rel(SAME_WINDOW_UQ / 'qoi_release_decision.csv')};{rel(SEEDED_RERUN / 's12_unlock_impact.csv')}",
        },
    ]


def build_geometry_evidence_summary() -> list[dict[str, Any]]:
    geom = read_csv(GEOM_SEED / "geometry_seed_case_summary.csv")
    topology = read_csv(TOPOLOGY_CV / "topology_cv_case_summary.csv")
    alt = read_csv(ALT_CV / "alternate_cv_case_summary.csv")
    diag = read_csv(DIAG_BRIDGE / "diagnostic_roi_average_bridge.csv")
    trusted_area = geom[0]["trusted_wall_area_m2"] if geom else ""
    interface_area = geom[0]["internal_seed_core_interface_area_m2"] if geom else ""
    seed_cells = geom[0]["seed_cell_count"] if geom else ""
    topo_frac = ";".join(f"{row['case_id']}={row['largest_face_component_fraction']}" for row in topology)
    alt_wall = ";".join(f"{row['case_id']}={row['selected_alt_wall_face_count']}" for row in alt)
    proxy_mdot = ";".join(f"{row['case_id']}={row['mdot_exchange_proxy_kg_s']} kg/s" for row in diag)
    return [
        {
            "evidence_id": "positive_geometry_seed_3_of_3",
            "lane": "geometry_seed",
            "evidence_type": "positive",
            "status": "released_for_surface_preflight",
            "key_observation": f"3/3 cases have {seed_cells} seed cells, trusted wall area {trusted_area} m2, internal interface area {interface_area} m2, and zero unclassified escapes",
            "effect_on_next_gate": "permits a separate seeded surface/input preflight",
            "evidence_paths": rel(GEOM_SEED / "geometry_seed_case_summary.csv"),
        },
        {
            "evidence_id": "positive_seeded_face_lists",
            "lane": "seeded_surface_inputs",
            "evidence_type": "positive_but_not_admission",
            "status": "face_lists_materialized",
            "key_observation": "seeded exchange-interface faces, trusted wall faces, recirc CV cells, wall/core band, normal convention, and source/sink boundary ledger exist in the seeded rerun package",
            "effect_on_next_gate": "surface/input preflight can consume released face lists; production_exchange_interface remains blocked",
            "evidence_paths": f"{rel(SEEDED_RERUN / 'seeded_exchange_interface_faces.csv')};{rel(SEEDED_RERUN / 'seeded_trusted_wall_faces.csv')};{rel(SEEDED_RERUN / 'surface_contract.csv')}",
        },
        {
            "evidence_id": "negative_reverse_topology_cv",
            "lane": "reverse_flow_topology",
            "evidence_type": "negative",
            "status": "fail_closed",
            "key_observation": f"dominant reverse components remain about half of candidates and have no trusted right-leg wall faces; largest fractions {topo_frac}",
            "effect_on_next_gate": "do not use reverse topology masks as production exchange CVs",
            "evidence_paths": rel(TOPOLOGY_CV / "topology_cv_case_summary.csv"),
        },
        {
            "evidence_id": "negative_alternate_wall_adjacent_cv",
            "lane": "alternate_reverse_cv",
            "evidence_type": "negative",
            "status": "fail_closed",
            "key_observation": f"Salt2 has no wall-adjacent component; Salt3/Salt4 wall-adjacent alternate selections are tiny and still touch unreleased boundaries; selected wall faces {alt_wall}",
            "effect_on_next_gate": "do not relax thresholds or admit proxy wall contact",
            "evidence_paths": rel(ALT_CV / "alternate_cv_case_summary.csv"),
        },
        {
            "evidence_id": "diagnostic_roi_proxy",
            "lane": "diagnostic_proxy",
            "evidence_type": "diagnostic_only",
            "status": "nonadmissible",
            "key_observation": f"ROI proxy gives scale estimates only, including mdot proxies {proxy_mdot}; Q_wall_W is unavailable",
            "effect_on_next_gate": "may support thesis diagnosis but not coefficient fitting or internal-Nu residual closure",
            "evidence_paths": rel(DIAG_BRIDGE / "diagnostic_roi_average_bridge.csv"),
        },
    ]


def build_blocker_queue(stats: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "blocker_id": "board_overlap_s13_rerun_rows",
            "lane": "coordination",
            "current_status": "active_overlap" if stats["active_short_rerun"] and stats["active_long_rerun"] else "clear",
            "unlock_action": "archive or reconcile completed S13 rerun rows and name the canonical seeded rerun package for downstream rows",
            "compute_policy": "documentation only",
            "forbidden_actions": "do not submit duplicate extraction or sampler jobs under overlapping rows",
            "evidence_paths": rel(BOARD),
        },
        {
            "priority": 2,
            "blocker_id": "seeded_surface_input_preflight",
            "lane": "S13 surface/source inputs",
            "current_status": "ready_to_claim_separate_row",
            "unlock_action": "extract or fail-close seeded interface/wall surfaces, normals, wall/core band, Q_wall/source input contract, and same-window thermal field contract",
            "compute_policy": "use sbatch if surface extraction exceeds 5 minutes; read-only checklist does not launch it",
            "forbidden_actions": "sampler/harvest/UQ/admission before surface/input contract passes",
            "evidence_paths": rel(SEEDED_RERUN / "downstream_gate.csv"),
        },
        {
            "priority": 3,
            "blocker_id": "Q_wall_source_sign_cp_release",
            "lane": "heat-path alignment",
            "current_status": "blocked",
            "unlock_action": "publish Q_wall_W or source-side equivalent over released wall faces with sign convention, cp_J_kg_K, source/sink provenance, and storage/residual separation",
            "compute_policy": "may require compute-node postprocessing if wallHeatFlux integration is needed",
            "forbidden_actions": "do not hide missing heat in internal Nu or use static q_net proxy as coefficient evidence",
            "evidence_paths": rel(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv"),
        },
        {
            "priority": 4,
            "blocker_id": "same_window_thermal_pressure_fields",
            "lane": "S13 sampler inputs",
            "current_status": "blocked",
            "unlock_action": "release same-window wall/core/bulk thermal contrasts and pressure/energy residual support tied to the seeded surfaces",
            "compute_policy": "surface extraction and field reduction row; use scheduler if heavy",
            "forbidden_actions": "no production harvest until same-window field basis is explicit",
            "evidence_paths": rel(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv"),
        },
        {
            "priority": 5,
            "blocker_id": "sampler_manifest_refresh",
            "lane": "S13 production readiness",
            "current_status": "blocked",
            "unlock_action": "rerun sampler manifest preflight after surface, Q_wall/source, normals, and same-window fields are available",
            "compute_policy": "lightweight manifest validation first; production sampling only after 3/3 ready",
            "forbidden_actions": "no harvest from partial manifest",
            "evidence_paths": rel(SAMPLER_PREFLIGHT / "sampler_input_gap_matrix.csv"),
        },
        {
            "priority": 6,
            "blocker_id": "same_qoi_uq_for_exchange_qois",
            "lane": "UQ and admission",
            "current_status": "blocked",
            "unlock_action": "after harvest, pair exact exchange QOIs with neighboring-window and mesh-family UQ before S11/S12/S15/S6",
            "compute_policy": "separate same-QOI UQ row after QOIs exist",
            "forbidden_actions": "no exchange-cell coefficient admission without same-QOI UQ",
            "evidence_paths": rel(SAME_WINDOW_UQ / "qoi_release_decision.csv"),
        },
        {
            "priority": 7,
            "blocker_id": "extbc_source_sink_provenance",
            "lane": "non-S13 heat-loss model",
            "current_status": "active_row_available",
            "unlock_action": "finish source/sink provenance recovery to classify setup-known versus document-only heat terms",
            "compute_policy": "documentation/provenance audit",
            "forbidden_actions": "do not promote realized CFD fields as runtime inputs",
            "evidence_paths": rel(BOARD),
        },
        {
            "priority": 8,
            "blocker_id": "tw4_tw6_local_audit",
            "lane": "non-S13 heat-loss model",
            "current_status": "active_row_available",
            "unlock_action": "finish heated-incline TW4-TW6 local audit to separate mapping/unit/source/model-form causes",
            "compute_policy": "documentation/provenance audit",
            "forbidden_actions": "do not tune h/emissivity or source terms from validation residuals",
            "evidence_paths": rel(BOARD),
        },
    ]


def build_heat_path_guardrails() -> list[dict[str, Any]]:
    return [
        {
            "heat_path_lane": "internal_Nu",
            "current_input_status": "must remain physics-only",
            "allowed_runtime_inputs": "flow state, geometry, properties, regime/correlation inputs that are legal before validation scoring",
            "forbidden_inputs": "unexplained wall/source/storage/radiation residual; realized CFD heat residual; fitted catch-all multiplier",
            "required_outputs": "internal convection prediction separated from wall/external/source lanes",
            "current_blocker": "S13 exchange-state QOIs and UQ are not available for any exchange-cell correction",
            "next_unlock": "harvest and UQ exchange QOIs before any internal-Nu candidate review",
        },
        {
            "heat_path_lane": "wall_conduction",
            "current_input_status": "blocked_for_S13_exchange",
            "allowed_runtime_inputs": "released wall geometry, wall/core band, material/thickness data with provenance",
            "forbidden_inputs": "validation residual back-solved as wall conduction",
            "required_outputs": "wall-side heat flow or resistance ledger with sign convention",
            "current_blocker": "wall_vtk and wall/core band are not production-ready for S13",
            "next_unlock": "seeded surface/input preflight and Q_wall/source release",
        },
        {
            "heat_path_lane": "insulation_quartz_external_convection_radiation",
            "current_input_status": "handled by external-BC contract outside S13",
            "allowed_runtime_inputs": "setup-known ambient/surface/radiation/material parameters from external-BC dictionary/provenance rows",
            "forbidden_inputs": "case-outcome residual promoted into external hA or emissivity",
            "required_outputs": "external heat-loss terms separate from internal convection and S13 exchange cell",
            "current_blocker": "source/sink provenance and local TW4-TW6 audits are still active",
            "next_unlock": "finish EXTBC provenance and heated-incline local audit rows",
        },
        {
            "heat_path_lane": "jacket_cooler",
            "current_input_status": "source/sink provenance incomplete",
            "allowed_runtime_inputs": "setup-known cooler/heater/source terms with sign and cp basis",
            "forbidden_inputs": "validation-derived source/sink correction",
            "required_outputs": "separate source/sink release ledger",
            "current_blocker": "static S13 source/sink terms are diagnostic context only; cp/sign/source release incomplete",
            "next_unlock": "Q_wall/source/sign/cp release row",
        },
        {
            "heat_path_lane": "storage",
            "current_input_status": "not released for S13 production candidate",
            "allowed_runtime_inputs": "same-window time derivative/storage terms if defined before scoring",
            "forbidden_inputs": "using storage as an untracked balancing term",
            "required_outputs": "storage contribution or explicit steady-window exclusion",
            "current_blocker": "same-window thermal fields and exchange windows are not released",
            "next_unlock": "same-window thermal/pressure residual support row",
        },
        {
            "heat_path_lane": "residual",
            "current_input_status": "diagnostic_only",
            "allowed_runtime_inputs": "reported closure remainder after all explicit lanes are computed",
            "forbidden_inputs": "absorbing residual into internal Nu, wall conduction, external h, or source terms",
            "required_outputs": "named residual lane with sign, magnitude, and non-admission status",
            "current_blocker": "explicit heat-path lanes are not complete",
            "next_unlock": "compute explicit lanes first; keep residual as non-fitted diagnostic",
        },
    ]


def build_guardrails() -> list[dict[str, str]]:
    return [
        {"guard_id": "native_outputs", "status": "read_only", "policy": "no CFD/OpenFOAM output mutation or OpenFOAM postprocessing launch"},
        {"guard_id": "scheduler", "status": "not_used", "policy": "checklist builder is lightweight and does not submit sbatch/srun"},
        {"guard_id": "sampler_harvest", "status": "not_launched", "policy": "surface/input, Q_wall/source, and UQ gates must pass first"},
        {"guard_id": "admission", "status": "blocked", "policy": "no coefficient, S11, S12, S15, or S6 trigger from geometry-only or diagnostic rows"},
        {"guard_id": "internal_Nu", "status": "protected", "policy": "heat residual must remain separate; do not absorb it into internal Nu"},
        {"guard_id": "external_repos", "status": "read_only", "policy": "no Fluid or external repository edits"},
    ]


def build_manifest(output_dir: Path) -> list[dict[str, Any]]:
    paths: list[tuple[Path, str, bool]] = [
        (Path("tools/analyze/build_s13_next_gate_checklist_and_blocker_unlocks.py"), "task_output", True),
        (Path("tools/analyze/test_s13_next_gate_checklist_and_blocker_unlocks.py"), "task_output", True),
        (GEOM_SEED, "read_only_context", False),
        (SHORT_RERUN, "read_only_context", False),
        (SEEDED_RERUN, "read_only_context", False),
        (TOPOLOGY_CV, "read_only_context", False),
        (ALT_CV, "read_only_context", False),
        (DIAG_BRIDGE, "read_only_context", False),
        (SAMPLER_PREFLIGHT, "read_only_context", False),
        (SAME_WINDOW_UQ, "read_only_context", False),
        (BOARD, "read_only_context", False),
        (output_dir, "task_output", True),
    ]
    rows = []
    for path, role, mutated in paths:
        full = path if path.is_absolute() else ROOT / path
        rows.append(
            {
                "path": rel(full),
                "role": role,
                "exists": str(full.exists()).lower(),
                "native_solver_output": "false",
                "mutated": str(mutated).lower(),
            }
        )
    return rows


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK_ID}
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Reviewer / Writer / Tester
type: work_product
status: complete
tags: [s13, upcomer-exchange, heat-loss-alignment, next-gate, blockers]
related:
  - {rel(GEOM_SEED)}
  - {rel(SEEDED_RERUN)}
  - {rel(SAMPLER_PREFLIGHT)}
---
# S13 Next-Gate Checklist and Blocker Unlocks

This package is a read-only next-gate checklist for S13 after the geometry seed
and seeded source-bounded rerun evidence. It separates geometry readiness from
production heat-path and admission readiness.

## Decision

- cases reviewed: `{summary["case_count"]}`
- geometry seed ready rows: `{summary["geometry_seed_ready_count"]}`
- seeded surface-preflight ready rows: `{summary["seeded_surface_preflight_ready_count"]}`
- production source-bounded CV rows released: `{summary["seeded_production_cv_released_count"]}`
- sampler-ready rows released: `0`
- same-QOI release rows allowed now: `{summary["same_qoi_release_allowed_count"]}`
- scheduler action: `false`
- native-output mutation: `false`

The next useful S13 work package is a separately claimed seeded surface/input
preflight. It should consume the materialized seeded face lists and either
release or fail-close interface/wall VTK surfaces, normals, `Q_wall_W` or a
source-side equivalent, same-window thermal fields, and the source/sink
sign/cp ledger.

## Outputs

- `next_gate_checklist.csv`
- `s13_geometry_evidence_summary.csv`
- `blocker_unlock_queue.csv`
- `heat_path_alignment_guardrails.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Do Not Do

Do not launch surface extraction, sampler, harvest, UQ, fitting, admission, or
S11/S12/S15/S6 from this package. Do not hide a heat residual in internal `Nu`.
Keep internal convection, wall conduction, insulation/quartz, external
convection, radiation, jacket/cooler/source, storage, and residual lanes
separate until explicit source-backed terms exist.
"""


def build_package(output_dir: Path = PACKAGE_DIR) -> dict[str, Any]:
    output_dir = ensure_dir(output_dir)
    stats = source_stats()
    next_gate = build_next_gate_checklist(stats)
    evidence = build_geometry_evidence_summary()
    blockers = build_blocker_queue(stats)
    heat_paths = build_heat_path_guardrails()
    guardrails = build_guardrails()
    manifest = build_manifest(output_dir)
    summary = {
        "task": TASK_ID,
        "generated_at": iso_timestamp(),
        **stats,
        "next_gate_rows": len(next_gate),
        "evidence_rows": len(evidence),
        "blocker_rows": len(blockers),
        "heat_path_rows": len(heat_paths),
        "surface_extraction_launched": False,
        "sampler_or_harvest_launched": False,
        "same_qoi_uq_run": False,
        "coefficient_admission": False,
        "s11_s12_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
        "residual_absorbed_into_internal_nu": False,
        "next_action": "claim seeded surface/input preflight row after board overlap is reconciled",
    }

    csv_dump(output_dir / "next_gate_checklist.csv", NEXT_GATE_FIELDS, next_gate)
    csv_dump(output_dir / "s13_geometry_evidence_summary.csv", EVIDENCE_FIELDS, evidence)
    csv_dump(output_dir / "blocker_unlock_queue.csv", BLOCKER_FIELDS, blockers)
    csv_dump(output_dir / "heat_path_alignment_guardrails.csv", HEAT_PATH_FIELDS, heat_paths)
    csv_dump(output_dir / "no_mutation_guardrails.csv", GUARD_FIELDS, guardrails)
    csv_dump(output_dir / "source_manifest.csv", MANIFEST_FIELDS, manifest)
    json_dump(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(readme(summary), encoding="utf-8")
    return {"summary": summary, "next_gate": next_gate, "blockers": blockers, "heat_paths": heat_paths}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR)
    args = parser.parse_args()
    payload = build_package(args.output_dir)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
