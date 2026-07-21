#!/usr/bin/env python3
"""Build a design-only contract for the heat-loss upcomer sampler.

This package defines the next sampler implementation target without editing
``tools/extract`` and without launching OpenFOAM, postprocessing, or a sampler.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-HEATLOSS-UPCOMER-SAMPLER-DESIGN"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_sampler_design")
OUT = ROOT / OUT_REL

EXTRACTION = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_upcomer_exchange_evidence_extraction"
)
PHASE4 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"
)
RECIRC = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_matched_plane_recirc_field_harvest"
)
EXCHANGE_CELL = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_throughflow_recirc_exchange_cell"
)
SAMPLER = ROOT / "tools/extract/sample_upcomer_convection_cell.py"

FIELD_MAP = EXTRACTION / "sampler_field_map.csv"
CASE_QUEUE = EXTRACTION / "case_time_window_queue.csv"
EXTRACTION_CONTRACT = EXTRACTION / "upcomer_exchange_extraction_contract.csv"
EXTRACTION_GUARDS = EXTRACTION / "no_admission_guardrail.csv"
PHASE4_MISSING = PHASE4 / "missing_exchange_nu_evidence_queue.csv"
RECIRC_ROWS = RECIRC / "matched_plane_recirc_field_harvest.csv"
EVIDENCE_REQS = EXCHANGE_CELL / "cfd_evidence_requirements.csv"


SCHEMA_ROWS: list[dict[str, str]] = [
    {
        "output_field": "reverse_area_fraction",
        "field_group": "local_reverse_flow",
        "dtype": "float",
        "units": "dimensionless",
        "source_fields": "U;face_area;plane_normal",
        "method_contract": "fraction of sampled upcomer plane area with velocity opposite same-window net throughflow direction",
        "status_in_current_sampler": "implemented_for_plane_metrics",
    },
    {
        "output_field": "reverse_mass_fraction",
        "field_group": "local_reverse_flow",
        "dtype": "float",
        "units": "dimensionless",
        "source_fields": "U;rho;face_area;plane_normal",
        "method_contract": "reverse directed mass flux divided by absolute same-plane mass flux",
        "status_in_current_sampler": "partially_implemented_as_recirculation_intensity_proxy",
    },
    {
        "output_field": "secondary_flow_intensity",
        "field_group": "local_reverse_flow",
        "dtype": "float",
        "units": "dimensionless",
        "source_fields": "U;plane_normal",
        "method_contract": "transverse velocity magnitude normalized by local velocity magnitude on the same sampled plane",
        "status_in_current_sampler": "available_in_existing_proxy_artifacts_not_current_script_output_name",
    },
    {
        "output_field": "V_recirc_m3",
        "field_group": "recirculation_volume",
        "dtype": "float",
        "units": "m3",
        "source_fields": "U;cell_volume;cell_center;upcomer_region_mask",
        "method_contract": "sum volumes in the connected upcomer reverse-flow cell mask for the same case/time window",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "mdot_exchange_kg_s",
        "field_group": "exchange_rate",
        "dtype": "float",
        "units": "kg/s",
        "source_fields": "U;rho;interface_area;interface_normal;recirculation_mask",
        "method_contract": "conservative flux across the main-throughflow/recirculation-cell interface with sign convention recorded",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "tau_recirc_s",
        "field_group": "exchange_rate",
        "dtype": "float",
        "units": "s",
        "source_fields": "V_recirc_m3;rho_recirc_kg_m3;mdot_exchange_kg_s",
        "method_contract": "rho_recirc times V_recirc divided by positive exchange mass rate",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "T_main_K",
        "field_group": "thermal_state",
        "dtype": "float",
        "units": "K",
        "source_fields": "T;rho;Cp;main_throughflow_mask",
        "method_contract": "enthalpy-weighted main-throughflow temperature in the same window as exchange rate",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "T_recirc_K",
        "field_group": "thermal_state",
        "dtype": "float",
        "units": "K",
        "source_fields": "T;rho;Cp;recirculation_mask",
        "method_contract": "enthalpy-weighted recirculation-cell temperature in the same window as exchange rate",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "wall_core_delta_T_K",
        "field_group": "thermal_state",
        "dtype": "float",
        "units": "K",
        "source_fields": "T;wall_distance_or_wall_patch_mask;core_mask",
        "method_contract": "same-window wall-adjacent minus core representative temperature difference with masks recorded",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "pressure_residual_Pa",
        "field_group": "pressure_basis",
        "dtype": "float",
        "units": "Pa",
        "source_fields": "p;p_rgh;rho;g;station_geometry;Delta_p_straight_Pa;Delta_p_dev_Pa",
        "method_contract": "same-window upcomer pressure residual after hydrostatic and straight-development subtraction",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "pressure_basis_status",
        "field_group": "pressure_basis",
        "dtype": "string",
        "units": "status",
        "source_fields": "p;p_rgh;sign_convention;station_geometry",
        "method_contract": "records static/p_rgh availability, pressure sign basis, and whether subtraction terms are complete",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "Q_wall_W",
        "field_group": "wall_source_terms",
        "dtype": "float",
        "units": "W",
        "source_fields": "wall_boundary_heat_rate_or_diagnostic_heat_ledger",
        "method_contract": "diagnostic wall heat contribution kept separate from internal Nu and runtime prediction inputs",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "Q_source_W",
        "field_group": "wall_source_terms",
        "dtype": "float",
        "units": "W",
        "source_fields": "source_term_ledger",
        "method_contract": "same-window source contribution for thermal residual accounting",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "Q_sink_W",
        "field_group": "wall_source_terms",
        "dtype": "float",
        "units": "W",
        "source_fields": "sink_term_ledger",
        "method_contract": "same-window sink contribution for thermal residual accounting",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "energy_residual_W",
        "field_group": "wall_source_terms",
        "dtype": "float",
        "units": "W",
        "source_fields": "enthalpy_flow_terms;Q_wall_W;Q_source_W;Q_sink_W",
        "method_contract": "diagnostic energy residual retained as a residual lane, not folded into internal Nu",
        "status_in_current_sampler": "not_implemented",
    },
    {
        "output_field": "same_qoi_uq_status",
        "field_group": "same_qoi_uq",
        "dtype": "string",
        "units": "status",
        "source_fields": "mesh_uq_table;time_uq_table;output_field;case_id;time_window_s",
        "method_contract": "records whether same-label same-formula same-window uncertainty exists for the emitted QOI",
        "status_in_current_sampler": "not_implemented_hook_only",
    },
    {
        "output_field": "runtime_use_policy",
        "field_group": "runtime_and_admission_guard",
        "dtype": "string",
        "units": "policy",
        "source_fields": "split_policy;source_use_category",
        "method_contract": "marks extracted CFD values diagnostic/training evidence only and forbids predictive runtime leakage",
        "status_in_current_sampler": "not_implemented",
    },
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


def sampler_output_schema() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in SCHEMA_ROWS:
        rows.append(
            {
                **row,
                "same_window_required": "true",
                "missing_behavior": "emit_missing_status_and_block_fit_score_admission",
                "admission_use_now": "diagnostic_only",
                "predictive_runtime_input": "false",
                "residual_policy": "do_not_hide_heat_residual_in_internal_Nu",
            }
        )
    return rows


def algorithm_contract() -> list[dict[str, Any]]:
    return [
        {
            "stage": "case_window_lock",
            "input_contract": "case_id;case_key;time_window_s;source_paths from case_time_window_queue",
            "method_contract": "fail closed if case/time/source path does not match the approved queue",
            "output_fields": "case_id;case_key;time_window_s;source_manifest_row",
            "blocked_behavior": "no sampler launch and no inferred replacement time",
        },
        {
            "stage": "local_reverse_flow",
            "input_contract": "U;rho if available;face area;plane normal;mesh-station metadata",
            "method_contract": "reuse current plane metric basis for RAF/RMF/SVF, but emit explicit output names and status flags",
            "output_fields": "reverse_area_fraction;reverse_mass_fraction;secondary_flow_intensity",
            "blocked_behavior": "ordinary single-stream Nu stays closed; exchange fit stays closed",
        },
        {
            "stage": "recirculation_mask_and_volume",
            "input_contract": "U;cell_volume;cell centers;upcomer region mask;net throughflow direction",
            "method_contract": "identify same-window connected reverse-flow recirculation mask and sum cell volumes",
            "output_fields": "V_recirc_m3;recirculation_mask_status",
            "blocked_behavior": "mdot_exchange and tau_recirc emit blocked_missing_V_recirc",
        },
        {
            "stage": "exchange_rate_and_residence_time",
            "input_contract": "recirculation mask;interface area/normal;U;rho;V_recirc_m3",
            "method_contract": "integrate conservative exchange flux across main/cell interface and compute tau_recirc",
            "output_fields": "mdot_exchange_kg_s;tau_recirc_s;exchange_interface_status",
            "blocked_behavior": "exchange-cell energy model remains conceptual only",
        },
        {
            "stage": "thermal_state",
            "input_contract": "T;rho;Cp or documented property mode;main mask;recirculation mask;wall/core masks",
            "method_contract": "emit enthalpy-weighted T_main and T_recirc plus wall-core Delta T in the same window",
            "output_fields": "T_main_K;T_recirc_K;wall_core_delta_T_K;property_mode",
            "blocked_behavior": "energy residual cannot be closed or fit",
        },
        {
            "stage": "pressure_residual_basis",
            "input_contract": "p;p_rgh;rho;g;station endpoints;straight-development terms;sign convention",
            "method_contract": "emit residual only after hydrostatic basis and straight/developing subtraction are complete",
            "output_fields": "pressure_residual_Pa;pressure_basis_status",
            "blocked_behavior": "pressure residual remains partial diagnostic",
        },
        {
            "stage": "wall_source_and_energy_residual",
            "input_contract": "enthalpy flow ledger;Q_wall;Q_source;Q_sink;case/time source manifest",
            "method_contract": "emit separated wall/source/sink/residual terms; never convert residual to internal Nu",
            "output_fields": "Q_wall_W;Q_source_W;Q_sink_W;energy_residual_W",
            "blocked_behavior": "residual attribution only; no internal-Nu reopening",
        },
        {
            "stage": "same_qoi_uq_hook",
            "input_contract": "emitted QOI labels;case_id;time_window_s;mesh/time UQ tables",
            "method_contract": "join only exact same-label same-formula same-sign same-window UQ rows",
            "output_fields": "same_qoi_uq_status;same_qoi_uq_source",
            "blocked_behavior": "QOI cannot be scored or admitted",
        },
        {
            "stage": "runtime_and_admission_guard",
            "input_contract": "source_use_category;split policy;all status fields",
            "method_contract": "mark CFD-derived rows non-runtime and diagnostic until later training-only admission row",
            "output_fields": "runtime_use_policy;fit_allowed_now;score_allowed_now;admission_use",
            "blocked_behavior": "no fit, no scorecard trigger, no closure admission",
        },
    ]


def dry_run_emission_matrix() -> list[dict[str, Any]]:
    case_rows = read_csv(CASE_QUEUE)
    schema = sampler_output_schema()
    rows: list[dict[str, Any]] = []
    for case in case_rows:
        for field in schema:
            implemented = field["status_in_current_sampler"].startswith("implemented")
            rows.append(
                {
                    "case_id": case["case_id"],
                    "case_key": case["case_key"],
                    "time_window_s": case["time_window_s"],
                    "representative_plane": case["representative_plane"],
                    "output_field": field["output_field"],
                    "field_group": field["field_group"],
                    "dry_run_status": "schema_defined_no_value_emitted",
                    "current_sampler_support": "partial" if implemented else field["status_in_current_sampler"],
                    "execution_required": "true",
                    "launch_allowed_from_this_package": "false",
                    "fit_allowed_now": "false",
                    "score_allowed_now": "false",
                    "source_paths": case["source_paths"],
                }
            )
    return rows


def future_implementation_change_list() -> list[dict[str, Any]]:
    return [
        {
            "change_id": "extractor_cli_schema_mode",
            "future_file": rel(SAMPLER),
            "required_change": "add a schema/dry-run mode that prints expected outputs without writing case directories",
            "acceptance": "unit tests can validate output headers without OpenFOAM",
        },
        {
            "change_id": "volume_mask_support",
            "future_file": rel(SAMPLER),
            "required_change": "add volume/cell input parsing for connected reverse-flow recirculation mask and V_recirc",
            "acceptance": "missing cell volumes fail closed with recirculation_mask_status",
        },
        {
            "change_id": "exchange_interface_flux",
            "future_file": rel(SAMPLER),
            "required_change": "define main/cell interface and integrate conservative mdot_exchange with sign basis",
            "acceptance": "tau_recirc is emitted only when V_recirc and mdot_exchange are both positive and same-window",
        },
        {
            "change_id": "thermal_pressure_residuals",
            "future_file": rel(SAMPLER),
            "required_change": "emit paired thermal state plus pressure and energy residual fields with source/status columns",
            "acceptance": "residual fields remain diagnostic and cannot set internal Nu",
        },
        {
            "change_id": "uq_and_runtime_guards",
            "future_file": rel(SAMPLER),
            "required_change": "join same-QOI UQ status and emit runtime/admission guard columns",
            "acceptance": "all rows default to fit_allowed_now=false and score_allowed_now=false",
        },
    ]


def execution_preflight_cases() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in read_csv(CASE_QUEUE):
        rows.append(
            {
                "case_id": case["case_id"],
                "case_key": case["case_key"],
                "time_window_s": case["time_window_s"],
                "required_fields": case["minimum_extract_groups"],
                "future_command_template": (
                    "python tools/extract/sample_upcomer_convection_cell.py "
                    "--case-dir <staged_or_reconstructed_case> "
                    f"--time {case['time_window_s']} --source-id <source_id> "
                    "--output-dir <claimed_work_product_dir>"
                ),
                "scheduler_policy": "execute_only_from_separate_execution_row_with_sbatch_or_srun",
                "source_check_required": "case path, mesh stations, U/T/p/p_rgh/rho/property fields, and source/sink ledgers",
                "launch_allowed_from_this_package": "false",
                "source_paths": case["source_paths"],
            }
        )
    return rows


def validation_cases() -> list[dict[str, Any]]:
    return [
        {
            "test_id": "schema_required_fields",
            "test_type": "unit",
            "expected": "all required output fields and field groups present",
            "blocks_if_fail": "sampler implementation cannot start",
        },
        {
            "test_id": "dry_run_no_values",
            "test_type": "unit",
            "expected": "dry-run matrix emits schema_defined_no_value_emitted and launch_allowed=false",
            "blocks_if_fail": "design package accidentally acts like extraction",
        },
        {
            "test_id": "same_window_join",
            "test_type": "future_execution",
            "expected": "case/time/source path must match the approved queue before extraction",
            "blocks_if_fail": "no sampler launch",
        },
        {
            "test_id": "residual_lane_guard",
            "test_type": "unit_and_future_execution",
            "expected": "energy_residual_W cannot set internal Nu or score/admission flags",
            "blocks_if_fail": "no Phase 4B rescore",
        },
        {
            "test_id": "same_qoi_uq_guard",
            "test_type": "future_execution",
            "expected": "score_allowed_now remains false without same-label same-window UQ",
            "blocks_if_fail": "no scorecard use",
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    paths = [
        FIELD_MAP,
        CASE_QUEUE,
        EXTRACTION_CONTRACT,
        EXTRACTION_GUARDS,
        PHASE4_MISSING,
        RECIRC_ROWS,
        EVIDENCE_REQS,
        SAMPLER,
    ]
    return [
        {
            "path": rel(path),
            "role": "read_only_input",
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path in paths
    ]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK}
date: 2026-07-21
role: Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
tags: [heat-loss, upcomer, sampler-design, exchange-cell, no-solver]
related:
  - {rel(EXTRACTION)}
  - {rel(PHASE4)}
  - {rel(RECIRC)}
---
# Heat-Loss Upcomer Sampler Design

This package implements Phase 1 of the heat-loss alignment sequence: a
design-only sampler contract for extracting upcomer exchange-state evidence.
It does not edit `tools/extract`, launch OpenFOAM, launch a sampler, or admit a
model.

## Decision

- Output schema rows: `{summary["schema_rows"]}`
- Algorithm stages: `{summary["algorithm_stage_rows"]}`
- Dry-run rows: `{summary["dry_run_rows"]}`
- Execution case windows: `{summary["execution_case_rows"]}`
- Sampler launched: `{str(summary["solver_or_postprocessing_or_sampler_launched"]).lower()}`
- Extractor edited: `{str(summary["tools_extract_edit"]).lower()}`
- Fit or score allowed now: `{str(summary["any_fit_or_score_allowed_now"]).lower()}`

## Outputs

- `sampler_output_schema.csv`: required output fields, units, source fields,
  method contracts, missing behavior, and runtime/admission policy.
- `algorithm_contract.csv`: implementation stages from case/window lock through
  same-QOI UQ hook and admission guard.
- `dry_run_emission_matrix.csv`: salt 2/3/4 by output-field dry-run ledger.
- `future_implementation_change_list.csv`: exact future extractor changes for
  the next row.
- `execution_preflight_cases.csv`: compute-node execution queue and command
  templates for the later execution row.
- `validation_cases.csv`: required tests and fail-closed behavior.
- `source_manifest.csv`: read-only provenance.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repositories, `tools/extract`, generated indexes, or
blocker register were mutated. No solver, postprocessor, sampler, fitting,
model selection, closure admission, or scorecard trigger was run. Heat residual
remains separate from internal Nu.
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    schema_rows = sampler_output_schema()
    algorithm_rows = algorithm_contract()
    dry_rows = dry_run_emission_matrix()
    implementation_rows = future_implementation_change_list()
    execution_rows = execution_preflight_cases()
    validation_rows = validation_cases()
    manifest_rows = source_manifest()

    write_csv(OUT / "sampler_output_schema.csv", schema_rows)
    write_csv(OUT / "algorithm_contract.csv", algorithm_rows)
    write_csv(OUT / "dry_run_emission_matrix.csv", dry_rows)
    write_csv(OUT / "future_implementation_change_list.csv", implementation_rows)
    write_csv(OUT / "execution_preflight_cases.csv", execution_rows)
    write_csv(OUT / "validation_cases.csv", validation_rows)
    write_csv(OUT / "source_manifest.csv", manifest_rows)

    summary = {
        "task": TASK,
        "built_at_utc": utc_now(),
        "schema_rows": len(schema_rows),
        "algorithm_stage_rows": len(algorithm_rows),
        "dry_run_rows": len(dry_rows),
        "future_implementation_rows": len(implementation_rows),
        "execution_case_rows": len(execution_rows),
        "validation_case_rows": len(validation_rows),
        "required_output_fields": [row["output_field"] for row in schema_rows],
        "mainline_cases": [row["case_id"] for row in execution_rows],
        "any_fit_or_score_allowed_now": False,
        "residual_absorbed_into_internal_Nu": False,
        "native_output_mutation": False,
        "registry_mutation": False,
        "scheduler_mutation": False,
        "solver_or_postprocessing_or_sampler_launched": False,
        "tools_extract_edit": False,
        "fluid_edit": False,
        "external_repo_edit": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "no_scorecard_outputs": True,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
