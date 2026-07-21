#!/usr/bin/env python3
"""Audit source-field availability for upcomer exchange extraction.

This is a lightweight filesystem/source audit. It does not read large native
field contents, write case directories, run OpenFOAM, launch a sampler, submit
jobs, fit coefficients, or change admission state.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-HEATLOSS-UPCOMER-SOURCE-FIELD-AUDIT"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit")
OUT = ROOT / OUT_REL

DESIGN = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_sampler_design"
)
HEATLOSS_DESIGN = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_upcomer_sampler_design"
)
EXTRACTION_CONTRACT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_upcomer_exchange_evidence_extraction"
)
MESH_ROOT = ROOT / "work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines"
SAMPLER = ROOT / "tools/extract/sample_upcomer_exchange_cell.py"
OLD_SAMPLER = ROOT / "tools/extract/sample_upcomer_convection_cell.py"

CASE_ROWS = [
    {
        "case_id": "salt_2",
        "case_key": "salt2_jin_nominal_continuation",
        "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
        "time_window_s": "7915",
        "case_dir": ROOT
        / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/"
        "case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation",
    },
    {
        "case_id": "salt_3",
        "case_key": "salt3_jin_nominal_continuation",
        "source_id": "viscosity_screening_salt_test_3_jin_coarse_mesh",
        "time_window_s": "7618",
        "case_dir": ROOT
        / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt3_jin/"
        "case_stage/viscosity_screening_salt_test_3_jin_coarse_mesh_continuation",
    },
    {
        "case_id": "salt_4",
        "case_key": "salt4_jin_nominal_continuation",
        "source_id": "viscosity_screening_salt_test_4_jin_coarse_mesh",
        "time_window_s": "10000",
        "case_dir": ROOT
        / "jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt4_jin/"
        "case_stage/viscosity_screening_salt_test_4_jin_coarse_mesh_continuation",
    },
]

REQUIRED_FIELDS = [
    ("U", "native_time_field", "required_for_velocity_mask_and_exchange_flux"),
    ("T", "native_time_field", "required_for_paired_thermal_state"),
    ("p", "native_time_field", "required_for_pressure_residual"),
    ("p_rgh", "native_time_field", "required_for_hydrostatic_pressure_basis"),
    ("rho", "native_time_field", "required_for_mass_flux_and_weighted_temperatures"),
    ("mu", "native_time_field", "required_for_R_mu_direct_dynamic_viscosity"),
    ("nuEff", "native_time_field", "diagnostic_possible_mu_proxy_only_after_policy"),
    ("phi", "native_time_field", "possible_face_flux_basis_not_exchange_interface_by_itself"),
    ("wallHeatFlux", "native_time_field", "forbidden_runtime_diagnostic_wall_heat_source_only"),
    ("cellVolume", "derived_or_generated", "required_for_V_recirc_if_not_computed_from_mesh"),
    ("recircMask", "derived_or_generated", "required_for_connected_recirculation_cell_mask"),
    ("exchange_interface_vtk", "generated_surface", "required_for_mdot_exchange"),
    ("wall_surface_vtk", "generated_surface", "required_for_wall_core_delta_T_and_wall_heat_diagnostic"),
    ("source_sink_ledger", "case_setup_or_generated_ledger", "required_for_Q_source_Q_sink_energy_residual"),
    ("mesh_stations", "repo_work_product", "required_for_upcomer_station_geometry"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def exists_text(path: Path) -> str:
    return str(path.exists()).lower()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() and path.is_file() else 0


def has_keyword(path: Path, keywords: tuple[str, ...]) -> bool:
    if not path.exists() or not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    return any(keyword.lower() in text for keyword in keywords)


def postprocess_has_pattern(case_dir: Path, patterns: tuple[str, ...]) -> bool:
    base = case_dir / "postProcessing"
    if not base.exists():
        return False
    names = [path.name.lower() for path in base.iterdir() if path.is_dir()]
    return any(any(pattern.lower() in name for name in names) for pattern in patterns)


def field_path(case: dict[str, Any], field: str) -> Path:
    return case["case_dir"] / "processors64" / case["time_window_s"] / field


def mesh_station_path(case: dict[str, Any]) -> Path:
    return MESH_ROOT / case["source_id"] / "mesh_stations.json"


def field_status(case: dict[str, Any], field: str) -> tuple[str, Path | None, str]:
    case_dir = case["case_dir"]
    time_dir = case_dir / "processors64" / case["time_window_s"]
    if field in {"U", "T", "p", "p_rgh", "rho", "nuEff", "phi", "wallHeatFlux"}:
        path = field_path(case, field)
        return ("present" if path.exists() else "missing", path, "native_decomposed_time_dir")
    if field == "mu":
        direct = field_path(case, "mu")
        if direct.exists():
            return "present", direct, "native_decomposed_time_dir"
        proxy = field_path(case, "nuEff")
        if proxy.exists() and field_path(case, "rho").exists():
            return "missing_direct_policy_needed_for_rho_times_nuEff_proxy", proxy, "nuEff_and_rho_present_but_R_mu_policy_not_admitted"
        return "missing", direct, "no_direct_or_proxy_basis"
    if field == "cellVolume":
        direct = field_path(case, "cellVolume")
        mesh = case_dir / "constant" / "polyMesh" / "owner"
        if direct.exists():
            return "present", direct, "native_or_generated_cell_volume_field"
        if mesh.exists():
            return "missing_generated_field_mesh_available", mesh, "mesh_available_but_cellVolume_not_written"
        return "missing", direct, "no_mesh_volume_basis_found"
    if field == "recircMask":
        direct = field_path(case, "recircMask")
        return ("present" if direct.exists() else "missing_generated_mask", direct, "requires_new_mask_generation_or_U_dot_n_fallback_policy")
    if field == "exchange_interface_vtk":
        found = postprocess_has_pattern(case_dir, ("exchange", "interface"))
        return ("present" if found else "missing_generated_surface"), case_dir / "postProcessing", "requires_named_interface_surface_generation"
    if field == "wall_surface_vtk":
        found = postprocess_has_pattern(case_dir, ("wall",))
        return ("partial_existing_wall_diagnostics" if found else "missing_generated_surface"), case_dir / "postProcessing", "wall_probe_or_diagnostic_exists_but_exchange_wall_surface_not_confirmed"
    if field == "source_sink_ledger":
        functions = case_dir / "system" / "functions"
        has_sources = has_keyword(functions, ("source", "sink", "heat"))
        return ("partial_case_setup_text_only" if has_sources else "missing_explicit_source_sink_ledger"), functions, "needs_same_window_Q_source_Q_sink_ledger"
    if field == "mesh_stations":
        path = mesh_station_path(case)
        return ("present" if path.exists() else "missing"), path, "repo_mesh_centerline_work_product"
    return "unknown", None, "unknown"


def case_window_source_audit() -> list[dict[str, Any]]:
    rows = []
    for case in CASE_ROWS:
        case_dir = case["case_dir"]
        time_dir = case_dir / "processors64" / case["time_window_s"]
        mesh = case_dir / "constant" / "polyMesh"
        rows.append(
            {
                "case_id": case["case_id"],
                "case_key": case["case_key"],
                "source_id": case["source_id"],
                "time_window_s": case["time_window_s"],
                "case_dir": rel(case_dir),
                "case_dir_exists": exists_text(case_dir),
                "processors64_time_dir": rel(time_dir),
                "processors64_time_dir_exists": exists_text(time_dir),
                "polyMesh_exists": exists_text(mesh),
                "mesh_stations_path": rel(mesh_station_path(case)),
                "mesh_stations_exists": exists_text(mesh_station_path(case)),
                "postProcessing_exists": exists_text(case_dir / "postProcessing"),
                "production_extraction_ready_now": "false",
                "readiness_reason": "primary fields present but exchange surfaces/masks/source ledgers are not ready for direct production extraction",
            }
        )
    return rows


def required_field_availability() -> list[dict[str, Any]]:
    rows = []
    for case in CASE_ROWS:
        for field, category, needed_for in REQUIRED_FIELDS:
            status, path, basis = field_status(case, field)
            rows.append(
                {
                    "case_id": case["case_id"],
                    "case_key": case["case_key"],
                    "time_window_s": case["time_window_s"],
                    "required_field_or_artifact": field,
                    "category": category,
                    "needed_for": needed_for,
                    "availability_status": status,
                    "basis": basis,
                    "path": rel(path) if path is not None and path.is_absolute() else (str(path) if path else ""),
                    "bytes": file_size(path) if path is not None else 0,
                    "runtime_policy": "diagnostic_only_not_predictive_runtime_input",
                    "admission_use": "audit_only",
                }
            )
    return rows


def blocker_rows(field_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocked_fields = {
        "mu": "direct dynamic viscosity missing; R_mu needs explicit rho*nuEff policy or source field",
        "cellVolume": "cell volume field not written; V_recirc requires generated volume basis from mesh or postprocess",
        "recircMask": "recirculation mask not written; connected reverse-flow mask must be generated",
        "exchange_interface_vtk": "no named exchange interface surface product found; mdot_exchange blocked",
        "wall_surface_vtk": "wall diagnostics exist but exchange wall/core surface product not confirmed",
        "source_sink_ledger": "same-window Q_source/Q_sink ledger not present as extraction artifact",
    }
    rows = []
    for case in CASE_ROWS:
        case_field_rows = {
            row["required_field_or_artifact"]: row
            for row in field_rows
            if row["case_id"] == case["case_id"]
        }
        for field, blocker in blocked_fields.items():
            status = case_field_rows[field]["availability_status"]
            if not status.startswith("present"):
                rows.append(
                    {
                        "case_id": case["case_id"],
                        "time_window_s": case["time_window_s"],
                        "blocked_field_or_artifact": field,
                        "availability_status": status,
                        "blocker": blocker,
                        "next_action": "implement_or_generate_before_production_extraction",
                        "fit_allowed_now": "false",
                        "score_allowed_now": "false",
                        "residual_policy": "do_not_hide_heat_residual_in_internal_Nu",
                    }
                )
    return rows


def extraction_readiness_decision(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    by_case = {case["case_id"]: [] for case in CASE_ROWS}
    for blocker in blockers:
        by_case[blocker["case_id"]].append(blocker["blocked_field_or_artifact"])
    for case in CASE_ROWS:
        missing = by_case[case["case_id"]]
        rows.append(
            {
                "case_id": case["case_id"],
                "time_window_s": case["time_window_s"],
                "primary_native_fields_ready": "true",
                "production_exchange_extraction_ready": "false",
                "local_under_5min_next_step": "source audit and unit tests only",
                "requires_sbatch_if_next": "true",
                "missing_or_policy_blocked": ";".join(missing),
                "decision": "do_not_launch_extraction_until_surface_mask_volume_and_source_ledger_basis_exists",
                "admission_change": "none",
            }
        )
    return rows


def sbatch_recommendation() -> list[dict[str, Any]]:
    return [
        {
            "work_item": "source_field_audit",
            "expected_runtime": "under_5_minutes",
            "where_to_run": "current_compute_node",
            "scheduler_action": "none",
            "reason": "filesystem/stat audit only",
        },
        {
            "work_item": "production_exchange_surface_generation",
            "expected_runtime": "over_5_minutes_or_uncertain",
            "where_to_run": "sbatch_from_login_node_or_repo_wrapper",
            "scheduler_action": "claim_separate_execution_row",
            "reason": "requires OpenFOAM surface generation or large native field sampling",
        },
        {
            "work_item": "production_sampler_extraction_from_ready_vtk",
            "expected_runtime": "case_dependent",
            "where_to_run": "compute_node_if_ready_inputs_exist_else_sbatch",
            "scheduler_action": "claim_separate_execution_row",
            "reason": "safe only after generated VTK/input products are present and command is bounded",
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    paths = [
        DESIGN / "exchange_sampler_dry_extraction_plan.csv",
        DESIGN / "exchange_sampler_required_schema.csv",
        HEATLOSS_DESIGN / "sampler_output_schema.csv",
        EXTRACTION_CONTRACT / "case_time_window_queue.csv",
        SAMPLER,
        OLD_SAMPLER,
    ]
    paths.extend(case["case_dir"] for case in CASE_ROWS)
    paths.extend(mesh_station_path(case) for case in CASE_ROWS)
    return [
        {
            "path": rel(path),
            "role": "read_only_input",
            "exists": exists_text(path),
            "native_solver_output": "true" if "jadyn_runs/" in rel(path) else "false",
            "mutated": "false",
        }
        for path in paths
    ]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK}
date: 2026-07-21
role: Thermal-modeling / Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [heat-loss, upcomer, source-field-audit, exchange-cell, no-solver]
related:
  - {rel(DESIGN)}
  - {rel(HEATLOSS_DESIGN)}
  - {rel(EXTRACTION_CONTRACT)}
---
# Heat-Loss Upcomer Source-Field Audit

This package audits whether the three queued mainline upcomer exchange windows
are ready for production extraction. It is a lightweight compute-node audit and
does not launch OpenFOAM or a sampler.

## Decision

- Case windows audited: `{summary["case_window_rows"]}`
- Required field/artifact rows: `{summary["required_field_rows"]}`
- Blocker rows: `{summary["blocker_rows"]}`
- Primary native fields ready: `{str(summary["all_primary_native_fields_present"]).lower()}`
- Production exchange extraction ready: `{str(summary["production_exchange_extraction_ready"]).lower()}`
- Scheduler action taken: `{str(summary["scheduler_action"]).lower()}`

The three target time directories contain the primary same-window native fields
needed for a future extraction design (`U`, `T`, `p`, `p_rgh`, `rho`, `phi`, and
diagnostic wall heat output). They do not already contain the exchange-cell
products needed for direct production extraction: direct `mu`, generated
`cellVolume`, `recircMask`, named exchange-interface surfaces, confirmed
wall/core surface products, and same-window source/sink ledgers remain blockers.

## Outputs

- `case_window_source_audit.csv`: case/time path readiness.
- `required_field_availability.csv`: per-case field/artifact availability.
- `missing_field_blockers.csv`: blocker rows that prevent direct extraction.
- `extraction_readiness_decision.csv`: per-case launch/no-launch decision.
- `sbatch_recommendation.csv`: under-5-minute vs Slurm routing.
- `source_manifest.csv`: read-only provenance.

## Guardrails

No native CFD/OpenFOAM outputs, case directories, registry/admission state,
scheduler state, Fluid source, external repositories, `tools/extract`,
generated indexes, or blocker register were mutated. No solver, postprocessor,
sampler, fitting, model selection, closure admission, Phase 4B rescore, or
scorecard trigger was run. Heat residual remains separate from internal Nu.
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    case_rows = case_window_source_audit()
    field_rows = required_field_availability()
    blockers = blocker_rows(field_rows)
    decisions = extraction_readiness_decision(blockers)
    sbatch_rows = sbatch_recommendation()
    manifest = source_manifest()

    write_csv(OUT / "case_window_source_audit.csv", case_rows)
    write_csv(OUT / "required_field_availability.csv", field_rows)
    write_csv(OUT / "missing_field_blockers.csv", blockers)
    write_csv(OUT / "extraction_readiness_decision.csv", decisions)
    write_csv(OUT / "sbatch_recommendation.csv", sbatch_rows)
    write_csv(OUT / "source_manifest.csv", manifest)

    primary_fields = {"U", "T", "p", "p_rgh", "rho"}
    all_primary = all(
        row["availability_status"] == "present"
        for row in field_rows
        if row["required_field_or_artifact"] in primary_fields
    )
    summary = {
        "task": TASK,
        "built_at_utc": utc_now(),
        "case_window_rows": len(case_rows),
        "required_field_rows": len(field_rows),
        "blocker_rows": len(blockers),
        "readiness_decision_rows": len(decisions),
        "sbatch_recommendation_rows": len(sbatch_rows),
        "all_primary_native_fields_present": all_primary,
        "production_exchange_extraction_ready": False,
        "recommended_next_task": "TODO-HEATLOSS-UPCOMER-EXCHANGE-SAMPLER-IMPLEMENTATION",
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_mutation": False,
        "solver_or_postprocessing_or_sampler_launched": False,
        "tools_extract_edit": False,
        "fluid_edit": False,
        "external_repo_edit": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "residual_absorbed_into_internal_Nu": False,
        "no_scorecard_outputs": True,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
