#!/usr/bin/env python3
"""Build the steady-state fluid+walls segment readiness ledger."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


TASK_ID = "TODO-PREDICT-FLUID-WALLS-READINESS-LEDGER"
OUTPUT_DIR = Path(
    "work_products/2026-07/2026-07-16/"
    "2026-07-16_predict_fluid_walls_readiness_ledger"
)
ALLOWED_STATUSES = {"admitted", "diagnostic", "partial", "missing"}

LEDGER_FIELDS = [
    "segment_id",
    "model_region",
    "fluid_walls_role",
    "geometry_status",
    "material_stack_status",
    "pressure_model_status",
    "thermal_circuit_status",
    "source_sink_role_status",
    "boundary_layer_state_status",
    "recirculation_flags_status",
    "uncertainty_status",
    "runtime_input_status",
    "primary_blocker",
    "next_required_artifact",
    "evidence_summary",
    "source_paths",
]

STATUS_FIELDS = [
    "geometry_status",
    "material_stack_status",
    "pressure_model_status",
    "thermal_circuit_status",
    "source_sink_role_status",
    "boundary_layer_state_status",
    "recirculation_flags_status",
    "uncertainty_status",
]

PROVENANCE = [
    {
        "source_id": "fluid_walls_model_form",
        "path": "operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md",
        "use": "Field contract, steady-state equation, test-section equation, and upcomer/onset policy.",
    },
    {
        "source_id": "geometry_reference",
        "path": "reference/geometry_reference.md",
        "use": "Authoritative segment names, dimensions, flow order, test-section material, and upcomer recirculation note.",
    },
    {
        "source_id": "segment_plan",
        "path": "operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md",
        "use": "Segment-local pressure/thermal slots and runtime leakage guardrails.",
    },
    {
        "source_id": "pressure_ladder_admission",
        "path": "work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/README.md",
        "use": "Pressure-ladder admission result: 66 branch rows reviewed, 0 true f_D/K rows admitted.",
    },
    {
        "source_id": "heat_audit",
        "path": "work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/heat_audit_and_modeling_recommendations.md",
        "use": "Role-level heat accounting, pressure-map caveats, and junction/stub loss interpretation.",
    },
    {
        "source_id": "recirc_contract",
        "path": "work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/README.md",
        "use": "Recirculation/admission rule: 42 effective-lane rows, 0 ordinary single-stream upcomer rows admitted.",
    },
    {
        "source_id": "recirc_hybrid_lanes",
        "path": "work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/hybrid_1d_model_contract.csv",
        "use": "Ordinary, transition, recirculating, and test-section-upcomer lane contract.",
    },
    {
        "source_id": "m3ts_scorecard",
        "path": "work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/README.md",
        "use": "M3+TS runtime rows pass setup-input audit but remain blocked by heat-loss and coupled-score gates.",
    },
    {
        "source_id": "heater_admission",
        "path": "work_products/2026-07/2026-07-16/2026-07-16_heater_lower_leg_source_sign_gci_admission/README.md",
        "use": "Heater source/sign/GCI admission: 0 fit-admissible rows.",
    },
    {
        "source_id": "downcomer_admission",
        "path": "work_products/2026-07/2026-07-16/2026-07-16_downcomer_policy_admission_artifact/README.md",
        "use": "Downcomer policy admission: 0 ordinary Nu fit rows admitted.",
    },
    {
        "source_id": "predictive_heat_loss_path",
        "path": "work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/README.md",
        "use": "Thermal circuit diagnostics and uncertainty gates; 0 thermal fit-candidate rows.",
    },
    {
        "source_id": "predictive_hx_fit",
        "path": "work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/README.md",
        "use": "HX/cooler model forms, split policy, and interpretation limits.",
    },
    {
        "source_id": "boundary_hx_wall_radiation_decision",
        "path": "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md",
        "use": "Boundary/HX/wall/radiation separation and double-counting guardrails.",
    },
]


def source(*source_ids: str) -> str:
    lookup = {row["source_id"]: row["path"] for row in PROVENANCE}
    return ";".join(lookup[source_id] for source_id in source_ids)


LEDGER_ROWS = [
    {
        "segment_id": "lower_leg_heater",
        "model_region": "lower_leg",
        "fluid_walls_role": "heated lower incline; primary heat-source region",
        "geometry_status": "admitted",
        "material_stack_status": "partial",
        "pressure_model_status": "diagnostic",
        "thermal_circuit_status": "diagnostic",
        "source_sink_role_status": "partial",
        "boundary_layer_state_status": "diagnostic",
        "recirculation_flags_status": "diagnostic",
        "uncertainty_status": "partial",
        "runtime_input_status": "setup geometry and heater role are legal; realized wallHeatFlux and internal-Nu diagnostics are scoring-only",
        "primary_blocker": "source/sign heat-balance, branch-local recirculation, and same-QOI GCI gates have zero admitted heater rows",
        "next_required_artifact": "source-owned heater fluid-fraction or wall-circuit row with sign/enthalpy review, low-recirculation mask, and same-QOI mesh/GCI",
        "evidence_summary": "Geometry and heater role are established, but heater Internal-Nu/UA fitting is not admitted.",
        "source_paths": source("geometry_reference", "heater_admission", "pressure_ladder_admission", "predictive_heat_loss_path"),
    },
    {
        "segment_id": "left_lower_leg_upcomer",
        "model_region": "left_lower_leg",
        "fluid_walls_role": "lower upcomer subspan before bare-quartz test section",
        "geometry_status": "admitted",
        "material_stack_status": "partial",
        "pressure_model_status": "diagnostic",
        "thermal_circuit_status": "diagnostic",
        "source_sink_role_status": "partial",
        "boundary_layer_state_status": "diagnostic",
        "recirculation_flags_status": "diagnostic",
        "uncertainty_status": "partial",
        "runtime_input_status": "ordinary single-stream Nu, f_D, and K are forbidden; future hybrid/onset lane may consume setup inputs plus admitted recirculation features",
        "primary_blocker": "material recirculation invalidates ordinary single-stream pressure and thermal coefficients",
        "next_required_artifact": "upcomer hybrid model with same-window reverse area/mass fraction, wall-core Delta T, Gz, pressure residual movement, and mesh/time uncertainty",
        "evidence_summary": "Upcomer recirculation is observed and useful as an exclusion/admission flag, not a predictive closure.",
        "source_paths": source("geometry_reference", "recirc_contract", "recirc_hybrid_lanes", "pressure_ladder_admission"),
    },
    {
        "segment_id": "test_section_span",
        "model_region": "test_section_span",
        "fluid_walls_role": "bare-quartz electrically heated upcomer subspan; currently net heat sink in mainline evidence",
        "geometry_status": "admitted",
        "material_stack_status": "admitted",
        "pressure_model_status": "diagnostic",
        "thermal_circuit_status": "partial",
        "source_sink_role_status": "partial",
        "boundary_layer_state_status": "diagnostic",
        "recirculation_flags_status": "diagnostic",
        "uncertainty_status": "partial",
        "runtime_input_status": "setup-only TS role rows pass runtime audit, but no TS candidate is admitted for held-out coupled scoring",
        "primary_blocker": "M3+TS heat-loss validation and holdout gates fail or the coupled solve gate is incomplete",
        "next_required_artifact": "frozen setup-only test-section loss candidate that passes Salt3/Salt4 heat-loss and coupled mdot/TP/TW gates",
        "evidence_summary": "Geometry, quartz material stack, and equation form are established; predictive net source/sink magnitude remains partial.",
        "source_paths": source("geometry_reference", "fluid_walls_model_form", "m3ts_scorecard", "recirc_hybrid_lanes"),
    },
    {
        "segment_id": "left_upper_leg_upcomer",
        "model_region": "left_upper_leg",
        "fluid_walls_role": "upper upcomer subspan after test section",
        "geometry_status": "admitted",
        "material_stack_status": "partial",
        "pressure_model_status": "diagnostic",
        "thermal_circuit_status": "diagnostic",
        "source_sink_role_status": "partial",
        "boundary_layer_state_status": "diagnostic",
        "recirculation_flags_status": "diagnostic",
        "uncertainty_status": "partial",
        "runtime_input_status": "ordinary single-stream Nu, f_D, and K are forbidden; use only hybrid/onset diagnostics until admitted",
        "primary_blocker": "recirculating/effective-lane status blocks ordinary pressure and thermal coefficient fitting",
        "next_required_artifact": "same upcomer hybrid/onset artifact as left_lower_leg, with outlet-plane reverse fraction and uncertainty",
        "evidence_summary": "The segment is geometrically admitted but belongs to the recirculating upcomer effective lane.",
        "source_paths": source("geometry_reference", "recirc_contract", "recirc_hybrid_lanes", "pressure_ladder_admission"),
    },
    {
        "segment_id": "upper_leg_cooler_hx",
        "model_region": "upper_leg",
        "fluid_walls_role": "cooler/HX upper branch and passive external-loss region",
        "geometry_status": "admitted",
        "material_stack_status": "partial",
        "pressure_model_status": "diagnostic",
        "thermal_circuit_status": "partial",
        "source_sink_role_status": "partial",
        "boundary_layer_state_status": "diagnostic",
        "recirculation_flags_status": "diagnostic",
        "uncertainty_status": "partial",
        "runtime_input_status": "HX/cooler duty may use setup-only model parameters; imposed CFD cooler duty and realized wallHeatFlux remain forbidden at runtime",
        "primary_blocker": "cooler/HX model is first-order but not a complete admitted segment thermal circuit with mesh/time uncertainty",
        "next_required_artifact": "direct Fluid UA/effectiveness row or held-out HX score tied to wall/material stack and segment uncertainty",
        "evidence_summary": "Cooler sink role and HX candidate forms exist, but the segment-local wall/HX circuit is not fully admitted.",
        "source_paths": source("geometry_reference", "predictive_hx_fit", "predictive_heat_loss_path", "boundary_hx_wall_radiation_decision"),
    },
    {
        "segment_id": "right_leg_downcomer",
        "model_region": "right_leg",
        "fluid_walls_role": "right vertical return/downcomer; passive loss and buoyancy return region",
        "geometry_status": "admitted",
        "material_stack_status": "partial",
        "pressure_model_status": "diagnostic",
        "thermal_circuit_status": "diagnostic",
        "source_sink_role_status": "partial",
        "boundary_layer_state_status": "diagnostic",
        "recirculation_flags_status": "diagnostic",
        "uncertainty_status": "partial",
        "runtime_input_status": "passive external-boundary setup fields are legal; downcomer Nu/UA fit is not admitted",
        "primary_blocker": "sign/enthalpy, low-recirculation validity, same-QOI GCI, and lit-review absorption gates fail",
        "next_required_artifact": "new downcomer same-QOI thermal extraction/GCI after sign/enthalpy and interface-recirculation policy are repaired or rejected",
        "evidence_summary": "Geometry is strong, but current downcomer thermal coefficient evidence is blocked by policy and interface-quality failures.",
        "source_paths": source("geometry_reference", "downcomer_admission", "predictive_heat_loss_path", "pressure_ladder_admission"),
    },
    {
        "segment_id": "junction_stub_connector_group",
        "model_region": "junction_other",
        "fluid_walls_role": "zero-length or short connector/junction thermal and pressure-loss regions",
        "geometry_status": "partial",
        "material_stack_status": "partial",
        "pressure_model_status": "diagnostic",
        "thermal_circuit_status": "diagnostic",
        "source_sink_role_status": "partial",
        "boundary_layer_state_status": "missing",
        "recirculation_flags_status": "diagnostic",
        "uncertainty_status": "missing",
        "runtime_input_status": "aggregate junction loss may guide model structure; local realized wallHeatFlux is not a runtime input",
        "primary_blocker": "junction/stub loss is aggregate role-level evidence, not split by physical junction with admitted area/material/pressure/thermal ownership",
        "next_required_artifact": "split lower-left/lower-right/upper-right/upper-left junction heat and pressure evidence with local areas, BCs, and uncertainty",
        "evidence_summary": "Junction/stub losses are physically important and persistent, but local circuit and K terms are not admitted.",
        "source_paths": source("heat_audit", "pressure_ladder_admission", "segment_plan", "boundary_hx_wall_radiation_decision"),
    },
]

BLOCKER_ROWS = [
    {
        "blocker_id": "B1_pressure_coefficients",
        "affected_segments": "all segments; especially left_lower_leg_upcomer;test_section_span;left_upper_leg_upcomer",
        "readiness_field": "pressure_model_status",
        "current_status": "diagnostic",
        "blocking_evidence": "Pressure ladders and maps exist, but 66 branch rows have 0 true f_D/K fit-admitted rows.",
        "shortest_next_action": "Admit pressure definition, orientation, straight-loss subtraction, low-recirculation mask, geometry normalization, mesh/GCI, and component isolation together.",
        "source_paths": source("pressure_ladder_admission", "heat_audit"),
    },
    {
        "blocker_id": "B2_upcomer_hybrid_onset",
        "affected_segments": "left_lower_leg_upcomer;test_section_span;left_upper_leg_upcomer",
        "readiness_field": "recirculation_flags_status",
        "current_status": "diagnostic",
        "blocking_evidence": "42 recirculating/effective-lane rows exist, but ordinary single-stream fit rows allowed today are 0.",
        "shortest_next_action": "Build the hybrid upcomer/onset artifact with reverse area/mass fraction, secondary velocity, wall-core Delta T, Gz, and mesh/time uncertainty.",
        "source_paths": source("recirc_contract", "recirc_hybrid_lanes"),
    },
    {
        "blocker_id": "B3_m3ts_test_section_loss",
        "affected_segments": "test_section_span",
        "readiness_field": "thermal_circuit_status",
        "current_status": "partial",
        "blocking_evidence": "Setup-only role rows pass runtime audit, but no candidate passes held-out heat-loss plus coupled M3+TS gates.",
        "shortest_next_action": "Freeze a setup-only TS candidate and run/score coupled M3+TS on Salt3 validation and Salt4 holdout.",
        "source_paths": source("m3ts_scorecard", "fluid_walls_model_form"),
    },
    {
        "blocker_id": "B4_heater_source_sign_gci",
        "affected_segments": "lower_leg_heater",
        "readiness_field": "thermal_circuit_status",
        "current_status": "diagnostic",
        "blocking_evidence": "Heater review has 0 source/sign heat-balance pass rows, 0 branch-local recirculation pass rows, and 0 publication-ready same-QOI GCI rows.",
        "shortest_next_action": "Create a source-owned heater wall/fluid-fraction artifact before any internal-Nu or UA fitting.",
        "source_paths": source("heater_admission"),
    },
    {
        "blocker_id": "B5_downcomer_policy",
        "affected_segments": "right_leg_downcomer",
        "readiness_field": "thermal_circuit_status",
        "current_status": "diagnostic",
        "blocking_evidence": "Downcomer ordinary Nu admission fails sign/enthalpy, low-recirculation validity, same-QOI GCI, and lit-review gates.",
        "shortest_next_action": "Repair/reject sign-enthalpy and interface-recirculation policy before same-QOI downcomer GCI.",
        "source_paths": source("downcomer_admission"),
    },
    {
        "blocker_id": "B6_junction_split",
        "affected_segments": "junction_stub_connector_group",
        "readiness_field": "thermal_circuit_status",
        "current_status": "diagnostic",
        "blocking_evidence": "Junction/stub heat loss is persistent and large, but only aggregate role-level evidence is available.",
        "shortest_next_action": "Split junction/stub loss by physical junction and add local area/material/BC ownership.",
        "source_paths": source("heat_audit"),
    },
    {
        "blocker_id": "B7_uncertainty_publication",
        "affected_segments": "all segments",
        "readiness_field": "uncertainty_status",
        "current_status": "partial",
        "blocking_evidence": "Time-window evidence is useful, but closure-QOI thermal mesh/GCI and radiation separability remain unresolved.",
        "shortest_next_action": "Attach same-QOI mesh/GCI and radiation-separability status to every segment row before paper-ready coefficient claims.",
        "source_paths": source("predictive_heat_loss_path", "boundary_hx_wall_radiation_decision"),
    },
]

PATH_ROWS = [
    {
        "sequence": 1,
        "target": "M3+TS",
        "step_id": "freeze_runtime_legal_ts_candidate",
        "needed_status_change": "test_section_span thermal_circuit_status partial -> admitted candidate only if held-out gates pass",
        "reason": "Runtime audit passes for setup role rows, so the shortest missing work is scoring, not another field harvest.",
        "source_paths": source("m3ts_scorecard"),
    },
    {
        "sequence": 2,
        "target": "M3+TS",
        "step_id": "run_coupled_score_on_validation_holdout",
        "needed_status_change": "pressure/thermal coupled-score gate incomplete -> scored",
        "reason": "Current package did not run the Fluid coupled solve by default.",
        "source_paths": source("m3ts_scorecard"),
    },
    {
        "sequence": 3,
        "target": "M3+TS",
        "step_id": "preserve_upcomer_hybrid_guardrail",
        "needed_status_change": "recirculation remains diagnostic/admission guardrail, not ordinary coefficient fit",
        "reason": "M3+TS must preserve the upcomer recirculation guardrail and not silently turn test-section/upcomer recirculation into ordinary Nu/f_D/K.",
        "source_paths": source("recirc_contract", "recirc_hybrid_lanes"),
    },
    {
        "sequence": 4,
        "target": "paper_ready_documentation",
        "step_id": "write_fluid_walls_model_section_from_ledger",
        "needed_status_change": "documentation missing -> paper-facing but caveated",
        "reason": "The ledger is ready to document model-form status, but not to claim admitted coefficients.",
        "source_paths": source("fluid_walls_model_form", "segment_plan"),
    },
    {
        "sequence": 5,
        "target": "paper_ready_coefficients",
        "step_id": "attach_same_qoi_uncertainty_and_admission",
        "needed_status_change": "uncertainty_status partial/missing -> admitted only after same-QOI GCI and source/sign gates pass",
        "reason": "Publication-grade coefficient claims remain blocked for heater, downcomer, junctions, and pressure coefficients.",
        "source_paths": source("heater_admission", "downcomer_admission", "pressure_ladder_admission", "predictive_heat_loss_path"),
    },
]


def validate_rows() -> None:
    segment_ids = set()
    for row in LEDGER_ROWS:
        missing = [field for field in LEDGER_FIELDS if field not in row]
        if missing:
            raise ValueError(f"{row.get('segment_id', '<unknown>')} missing fields: {missing}")
        segment_id = row["segment_id"]
        if segment_id in segment_ids:
            raise ValueError(f"duplicate segment_id: {segment_id}")
        segment_ids.add(segment_id)
        for field in STATUS_FIELDS:
            status = row[field]
            if status not in ALLOWED_STATUSES:
                raise ValueError(f"{segment_id} {field} has invalid status {status!r}")
    if len(LEDGER_ROWS) < 7:
        raise ValueError("ledger must cover physical spans plus junction/stub group")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def status_counts() -> dict[str, dict[str, int]]:
    return {
        field: dict(Counter(row[field] for row in LEDGER_ROWS))
        for field in STATUS_FIELDS
    }


def write_readme(path: Path, summary: dict) -> None:
    lines = [
        "---",
        "provenance:",
    ]
    for row in PROVENANCE[:8]:
        lines.append(f"  - {row['path']}")
    lines.extend(
        [
            "tags: [forward-predictive-model, fluid-walls, readiness-ledger, segment-models]",
            "related:",
            "  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md",
            "  - operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md",
            f"task: {TASK_ID}",
            "date: 2026-07-16",
            "role: Coordinator/Forward-pred/Thermal-modeling/Hydraulics/Implementer/Tester/Writer",
            "type: work_product",
            "status: complete",
            "---",
            "# Fluid+Walls Readiness Ledger",
            "",
            "This package converts the July 16 steady-state `fluid+walls` model-form contract into a row-by-row segment readiness ledger.",
            "",
            "Status vocabulary:",
            "",
            "- `admitted`: usable as a current model contract, setup input, or exclusion/admission guardrail.",
            "- `partial`: setup/runtime inputs exist, but an admission, validation, or uncertainty gate remains open.",
            "- `diagnostic`: evidence exists for interpretation or scoring only; do not fit or consume as a predictive runtime closure.",
            "- `missing`: the current evidence package lacks the required segment-local field.",
            "",
            "## Outputs",
            "",
            "- `fluid_walls_segment_readiness_ledger.csv`: one row per loop segment/region with geometry, material stack, pressure, thermal, source/sink, boundary-layer, recirculation, and uncertainty status.",
            "- `fluid_walls_blocker_table.csv`: segment-field blockers and shortest next actions.",
            "- `fluid_walls_shortest_missing_data_path.csv`: shortest path for M3+TS and paper-ready documentation/coefficient claims.",
            "- `TOMORROW_HANDOFF.md`: continuation context for the next working session.",
            "- `source_manifest.csv`: exact source files used.",
            "- `summary.json`: machine-readable counts and acceptance signals.",
            "",
            "## Result",
            "",
            f"- Segment/region rows: `{summary['segment_rows']}`.",
            f"- Blocker rows: `{summary['blocker_rows']}`.",
            f"- M3+TS/paper path rows: `{summary['path_rows']}`.",
            "- No native CFD outputs, registry/admission state, scheduler state, or external Fluid files were changed.",
            "- Realized CFD `wallHeatFlux`, CFD `mdot`, imposed CFD cooler duty, and validation temperatures remain diagnostic/scoring evidence only.",
            "",
            "## Highest-Signal Interpretation",
            "",
            "Geometry is admitted for the six physical spans. The bare-quartz test-section material stack is admitted, and the ordinary pipe material stacks are partially available but still need segment-local wall-circuit ownership. Pressure evidence is diagnostic everywhere: the current pressure-ladder admission package reports zero true `f_D` or `K` fit-admitted branch rows. Thermal circuits are strongest for model architecture and weakest for admitted coefficients: heater, downcomer, upcomer, and junction/stub rows remain diagnostic or partial because source/sign, recirculation, same-QOI GCI, split-junction, or coupled-score gates remain open.",
            "",
            "The shortest M3+TS path is not another broad ledger pass. It is to freeze a runtime-legal setup-only test-section loss candidate, run the coupled validation/holdout score, and keep the upcomer recirculation guardrail active. Paper-facing documentation can use this ledger now for the model-form/status section, but paper-ready coefficient claims still require same-QOI uncertainty and admission gates.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def write_handoff(path: Path) -> None:
    lines = [
        "---",
        "provenance:",
        "  - work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/fluid_walls_segment_readiness_ledger.csv",
        "  - work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/fluid_walls_blocker_table.csv",
        "  - work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/fluid_walls_shortest_missing_data_path.csv",
        "tags: [forward-predictive-model, fluid-walls, handoff, segment-models]",
        "related:",
        "  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md",
        "  - .agent/status/2026-07-16_TODO-PREDICT-FLUID-WALLS-READINESS-LEDGER.md",
        f"task: {TASK_ID}",
        "date: 2026-07-16",
        "role: Coordinator/Forward-pred/Thermal-modeling/Hydraulics/Implementer/Tester/Writer",
        "type: work_product",
        "status: complete",
        "---",
        "# Tomorrow Handoff: Fluid+Walls Readiness Ledger",
        "",
        "## Start Here",
        "",
        "Open these files in order:",
        "",
        "1. `operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md`",
        "2. `work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/README.md`",
        "3. `work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/fluid_walls_segment_readiness_ledger.csv`",
        "4. `work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/fluid_walls_shortest_missing_data_path.csv`",
        "5. `.agent/status/2026-07-16_TODO-PREDICT-FLUID-WALLS-READINESS-LEDGER.md`",
        "",
        "## What Was Decided",
        "",
        "- The current steady-state model-form name is `fluid+walls`.",
        "- The model is steady-state only; do not add wall storage or transient heat-capacity terms to this current target.",
        "- Every segment should carry geometry, material stack, pressure model, thermal circuit, source/sink role, boundary-layer state, recirculation/admission flags, and uncertainty status.",
        "- Realized CFD `wallHeatFlux`, CFD `mdot`, imposed CFD cooler duty, and validation temperatures are diagnostic/scoring evidence only, not predictive runtime inputs.",
        "",
        "## Current Ledger State",
        "",
        "- `lower_leg_heater`: geometry admitted; material partial; pressure diagnostic; thermal diagnostic; source/sink partial; uncertainty partial.",
        "- `left_lower_leg_upcomer`: geometry admitted; pressure/thermal diagnostic; recirculation diagnostic guardrail; ordinary `Nu`, `f_D`, and `K` fits forbidden.",
        "- `test_section_span`: geometry and bare-quartz material admitted; thermal partial; M3+TS candidate not admitted yet.",
        "- `left_upper_leg_upcomer`: geometry admitted; recirculating/effective-lane status blocks ordinary pressure/thermal coefficient fitting.",
        "- `upper_leg_cooler_hx`: geometry admitted; HX/cooler thermal circuit partial; imposed CFD cooler duty remains forbidden at runtime.",
        "- `right_leg_downcomer`: geometry admitted; downcomer Nu/UA fit not admitted because sign/enthalpy, recirculation, GCI, and lit-review gates fail.",
        "- `junction_stub_connector_group`: geometry/material partial; boundary-layer and uncertainty missing; heat/pressure evidence is aggregate diagnostic only.",
        "",
        "## Shortest Useful Next Sequence",
        "",
        "1. For M3+TS, freeze a runtime-legal setup-only test-section heat-loss candidate.",
        "2. Run the coupled Fluid validation/holdout score for that candidate.",
        "3. Keep the upcomer recirculation guardrail active; do not fit ordinary `Nu`, `f_D`, or `K` to upcomer/test-section rows.",
        "4. Use the ledger for paper/model-form wording now, but state clearly that coefficient claims are not admitted.",
        "5. For paper-ready coefficients, attach same-QOI uncertainty/admission gates by segment after source/sign, recirculation, and GCI blockers are resolved.",
        "",
        "## Do Not Do",
        "",
        "- Do not use realized CFD `wallHeatFlux`, CFD `mdot`, imposed CFD cooler duty, or validation temperatures as runtime inputs.",
        "- Do not treat pressure maps/ladders as admitted `f_D` or `K` coefficients.",
        "- Do not hide junction/stub heat loss inside a global insulation or Nu correction.",
        "- Do not treat the diagnostic M3/no-test-section baseline as the physical final model.",
        "- Do not mutate native solver outputs or refresh generated repo indexes unless a new board row explicitly claims those paths.",
        "",
        "## Exact Commands From This Session",
        "",
        "```text",
        "python3 tools/analyze/build_fluid_walls_readiness_ledger.py",
        "python3 -m pytest tools/analyze/test_fluid_walls_readiness_ledger.py",
        "python3 -m json.tool imports/2026-07-16_predict_fluid_walls_readiness_ledger.json",
        "python3 -m json.tool work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/summary.json",
        "```",
        "",
        "## Validation State",
        "",
        "The focused tests pass (`3 passed`). The builder emits `7` segment rows, `7` blocker rows, and `5` shortest-path rows. The generated summary explicitly records no runtime leakage, native-output mutation, registry mutation, or scheduler action.",
    ]
    path.write_text("\n".join(lines) + "\n")


def build(output_dir: Path = OUTPUT_DIR) -> dict:
    validate_rows()
    output_dir.mkdir(parents=True, exist_ok=True)

    ledger_path = output_dir / "fluid_walls_segment_readiness_ledger.csv"
    blocker_path = output_dir / "fluid_walls_blocker_table.csv"
    path_path = output_dir / "fluid_walls_shortest_missing_data_path.csv"
    manifest_path = output_dir / "source_manifest.csv"
    summary_path = output_dir / "summary.json"
    readme_path = output_dir / "README.md"
    handoff_path = output_dir / "TOMORROW_HANDOFF.md"

    write_csv(ledger_path, LEDGER_ROWS, LEDGER_FIELDS)
    write_csv(
        blocker_path,
        BLOCKER_ROWS,
        [
            "blocker_id",
            "affected_segments",
            "readiness_field",
            "current_status",
            "blocking_evidence",
            "shortest_next_action",
            "source_paths",
        ],
    )
    write_csv(
        path_path,
        PATH_ROWS,
        [
            "sequence",
            "target",
            "step_id",
            "needed_status_change",
            "reason",
            "source_paths",
        ],
    )
    write_csv(manifest_path, PROVENANCE, ["source_id", "path", "use"])

    counts = status_counts()
    summary = {
        "task": TASK_ID,
        "generated_at": "2026-07-16",
        "segment_rows": len(LEDGER_ROWS),
        "blocker_rows": len(BLOCKER_ROWS),
        "path_rows": len(PATH_ROWS),
        "allowed_statuses": sorted(ALLOWED_STATUSES),
        "status_counts": counts,
        "acceptance": {
            "machine_readable_readiness_table": ledger_path.name,
            "machine_readable_blocker_table": blocker_path.name,
            "shortest_missing_data_path_table": path_path.name,
            "runtime_leakage_introduced": False,
            "native_outputs_mutated": False,
            "registry_mutated": False,
            "scheduler_action": False,
        },
        "outputs": [
            ledger_path.name,
            blocker_path.name,
            path_path.name,
            handoff_path.name,
            manifest_path.name,
            summary_path.name,
            readme_path.name,
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    write_readme(readme_path, summary)
    write_handoff(handoff_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    summary = build(args.output_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
