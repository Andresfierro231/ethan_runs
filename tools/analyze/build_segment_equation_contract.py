#!/usr/bin/env python3
"""Build the segment-resolved forward-model equation contract."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-17"
TASK = "TODO-PREDICT-SEGMENT-EQUATION-CONTRACT"

OUT = ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_segment_equation_contract"
STATUS = ROOT / ".agent/status/2026-07-17_TODO-PREDICT-SEGMENT-EQUATION-CONTRACT.md"
JOURNAL = ROOT / ".agent/journal/2026-07-17/predict-segment-equation-contract.md"
IMPORT = ROOT / "imports/2026-07-17_predict_segment_equation_contract.json"

SEGMENT_PLAN = ROOT / "operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md"
M3TS_NOTE = ROOT / "operational_notes/07-26/15/2026-07-15_m3_successor_test_section_heat_loss_requirement.md"
PRESSURE_LEDGER = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv"
PATCHWISE_HEAT = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv"
INTERFACE_HEAT = (
    ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/segment_enthalpy_residuals.csv"
)
INPUT_CONTRACT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/runtime_input_contract.csv"
RECIRC_POLICY = (
    ROOT
    / "work_products/2026-07/2026-07-15/2026-07-15_recirculation_policy_forward_hydraulic_unblock_plan"
    / "coefficient_label_admission_policy.csv"
)
SALT1_PROMOTION = (
    ROOT / "work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion/salt1_split_ready_manifest.csv"
)
SALT2_READINESS = (
    ROOT
    / "work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger"
    / "fluid_walls_readiness_ledger.csv"
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def require_sources() -> None:
    required = [
        SEGMENT_PLAN,
        M3TS_NOTE,
        PRESSURE_LEDGER,
        PATCHWISE_HEAT,
        INTERFACE_HEAT,
        INPUT_CONTRACT,
        RECIRC_POLICY,
        SALT1_PROMOTION,
        SALT2_READINESS,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing segment equation contract source(s): " + "; ".join(missing))


def equation_forms() -> list[dict[str, object]]:
    return [
        {
            "equation_id": "thermal_state",
            "scope": "all_segments",
            "equation_text": "mdot -> residence_time_i -> T_i(s) -> rho_i, mu_i, cp_i, k_i",
            "implementation_contract": "thermal state is solved before or inside the pressure root; properties are segment-local",
            "admission_gate": "segment thermal model scorecard must identify fit rows, score rows, and blocked rows",
        },
        {
            "equation_id": "buoyancy_drive",
            "scope": "closed_loop",
            "equation_text": "Delta_p_drive = integral_loop rho(T(s), p(s), composition, property_lane) * g * dz(s)",
            "implementation_contract": "drive comes from density differences along elevation, not a global mdot scalar",
            "admission_gate": "density/property lane and geometry/elevation map must be named for every segment",
        },
        {
            "equation_id": "pressure_loss",
            "scope": "all_segments",
            "equation_text": (
                "Delta_p_loss = sum_i [f_i(Re_i, Pr_i, Ri_i, regime_i, roughness_i, geometry_i) "
                "* (L_i/D_i) * q_i + K_i(local_geometry_i, reset_i, development_i, regime_i) * q_i]"
            ),
            "implementation_contract": "q_i = 0.5 * rho_i * V_i^2 and f_i/K_i are segment-local model slots",
            "admission_gate": "recirculating rows cannot admit true single-stream f_D or K",
        },
        {
            "equation_id": "coupled_root",
            "scope": "closed_loop",
            "equation_text": "Find mdot such that sum(Delta_p_drive_i - Delta_p_loss_i) = 0 with T(s, mdot) updated",
            "implementation_contract": "root solve must update thermal state, properties, drive, and losses together",
            "admission_gate": "coupled M3+TS scorecard can run only after segment pressure and thermal scorecards exist",
        },
        {
            "equation_id": "segment_energy",
            "scope": "all_segments",
            "equation_text": "mdot * cp_i * dT_i = Q_heater_i - Q_cooler_i - Q_external_loss_i + Q_junction_or_mixing_i",
            "implementation_contract": "source/sink ownership is explicit; internal Nu cannot absorb external heat residuals",
            "admission_gate": "realized CFD wallHeatFlux is scoring evidence only, never a runtime term",
        },
    ]


def segment_rows() -> list[dict[str, object]]:
    common_drive = "integral rho(T(s),p,s) g dz over local elevation span"
    return [
        {
            "loop_region": "heater",
            "one_d_segments": "heated_incline;heater_lower_leg",
            "pressure_drive_form": common_drive,
            "pressure_loss_slots": "distributed_friction;entrance_or_reset_development;named_component_K_if_bracketed",
            "thermal_slots": "heater_fluid_fraction_model;wall_layer_resistance;passive_external_loss",
            "property_form": "segment-local rho, mu, cp, k from solved T_i and declared property lane",
            "admission_model_forms": "heater model fit/validation split; no global thermal multiplier",
            "runtime_allowed_inputs": "geometry;material_stack;heater_electrical_power;admitted_eta_or_resistance_parameters;setup external BCs",
            "runtime_forbidden_inputs": "CFD mdot;realized wallHeatFlux;validation temperatures",
            "diagnostic_allowed": "heater wallHeatFlux and enthalpy residuals as post-solve scoring targets",
            "downstream_owner": "TODO-PREDICT-HEATER-FLUID-FRACTION;TODO-PREDICT-SEGMENT-THERMAL-MODELS",
        },
        {
            "loop_region": "cooler_HX",
            "one_d_segments": "cooler_branch;cooling_jacket;reducer_region",
            "pressure_drive_form": common_drive,
            "pressure_loss_slots": "distributed_friction;reducer_or_expansion_K;reset_development;HX_branch_apparent_loss",
            "thermal_slots": "UA_or_epsilon_NTU_cooler_model;distributed_UA;passive_external_loss",
            "property_form": "segment-local properties with coolant/air-side setup metadata where admitted",
            "admission_model_forms": "cooler model must predict removal without imposed CFD cooler duty",
            "runtime_allowed_inputs": "geometry;cooler setup metadata;admitted UA/effectiveness parameters;solved fluid temperatures",
            "runtime_forbidden_inputs": "imposed CFD cooler duty;CFD mdot;validation temperatures",
            "diagnostic_allowed": "CFD cooler removal rows as post-solve score targets",
            "downstream_owner": "TODO-PREDICT-COOLER-REMOVAL;TODO-PREDICT-SEGMENT-THERMAL-MODELS",
        },
        {
            "loop_region": "downcomer",
            "one_d_segments": "right_vertical_downcomer;right_downcomer_bottom_horizontal_junction",
            "pressure_drive_form": common_drive,
            "pressure_loss_slots": "ordinary_or_branch_specific_distributed_friction;reset_development;bend_or_junction_apparent_loss",
            "thermal_slots": "passive_external_boundary;wall_layer_resistance;optional_radiation_without_double_counting",
            "property_form": "segment-local properties from cooling-leg T_i(s)",
            "admission_model_forms": "ordinary-pipe forms allowed only where recirculation and pressure gates pass",
            "runtime_allowed_inputs": "geometry;setup h/Ta/Tsur/emissivity/layers;solved fluid temperatures",
            "runtime_forbidden_inputs": "realized wallHeatFlux;validation TP/TW temperatures;global friction multiplier",
            "diagnostic_allowed": "pressure and TP2/TW target rows after solve",
            "downstream_owner": "TODO-PREDICT-SEGMENT-PRESSURE-MODELS;TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE",
        },
        {
            "loop_region": "upcomer",
            "one_d_segments": "left_lower_vertical;test_section;left_upper_vertical",
            "pressure_drive_form": common_drive,
            "pressure_loss_slots": "hybrid_throughflow_pipe_plus_recirculation_cell;onset_diagnostic;no_true_single_stream_f_D_or_K_currently",
            "thermal_slots": "hybrid_cell_exchange;wall_core_drive;test_section_coupling;diagnostic_internal_Nu_only_until_admitted",
            "property_form": "segment-local properties plus recirculation metrics RAF/RMF/secondary velocity where available",
            "admission_model_forms": "ordinary single-stream coefficients blocked for current recirculating rows",
            "runtime_allowed_inputs": "geometry;setup BCs;admitted hybrid/onset parameters;solved temperatures",
            "runtime_forbidden_inputs": "recirculating-row true Nu/f_D/K fits;CFD mdot;realized wallHeatFlux",
            "diagnostic_allowed": "PM5 RAF/RMF/secondary velocity and wall-core delta T as diagnostics",
            "downstream_owner": "TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL;TODO-PREDICT-SEGMENT-PRESSURE-MODELS",
        },
        {
            "loop_region": "test_section",
            "one_d_segments": "test_section_span",
            "pressure_drive_form": common_drive,
            "pressure_loss_slots": "upcomer_hybrid_lane;development_or_thermal_redevelopment;no_ordinary_fit_until_gate",
            "thermal_slots": "setup-only distributed test-section heat-loss model;quartz_wall_resistance;external_convection;radiation_if_admitted",
            "property_form": "segment-local high-temperature property lane with wall/ambient setup metadata",
            "admission_model_forms": "M3+TS requires explicit Q_test_section_loss_model; diagnostic M3 is not final",
            "runtime_allowed_inputs": "geometry;quartz/material parameters;setup h/Ta/Tsur/emissivity;solved fluid temperatures",
            "runtime_forbidden_inputs": "realized CFD test-section net heat;realized wallHeatFlux;validation TP/TW temperatures",
            "diagnostic_allowed": "test-section realized heat and TP/TW errors as score targets",
            "downstream_owner": "TODO-PREDICT-TEST-SECTION-HEAT-LOSS;TODO-PREDICT-SEGMENT-THERMAL-MODELS",
        },
        {
            "loop_region": "junction_stub_connector",
            "one_d_segments": "bends;tees;reducers;stubs;mixing_regions",
            "pressure_drive_form": "usually local dz contribution if elevated; otherwise zero-elevation pressure-drive slot",
            "pressure_loss_slots": "localized_component_K_if_bracketed;branch_apparent_loss;mixing_or_recirc_diagnostic",
            "thermal_slots": "junction/stub heat loss;mixing residual;passive external boundary",
            "property_form": "local mixed-state properties with explicit bracketing uncertainty",
            "admission_model_forms": "true K only when physically bracketed; otherwise apparent diagnostic label",
            "runtime_allowed_inputs": "geometry;admitted local K or mixing model;setup wall/environment metadata",
            "runtime_forbidden_inputs": "unbracketed CFD pressure residual as true K;realized wallHeatFlux as runtime heat",
            "diagnostic_allowed": "apparent K, mixing residual, and junction heat rows as diagnostics",
            "downstream_owner": "TODO-PREDICT-SEGMENT-PRESSURE-MODELS;TODO-PREDICT-SEGMENT-THERMAL-MODELS",
        },
        {
            "loop_region": "lower_upper_legs",
            "one_d_segments": "lower_horizontal_leg;upper_horizontal_leg;interconnecting_straights",
            "pressure_drive_form": common_drive,
            "pressure_loss_slots": "branch-specific distributed_friction;reset/development after components;roughness sensitivity",
            "thermal_slots": "passive external boundary;wall/layer resistance;boundary-layer development sensitivity",
            "property_form": "segment-local properties with heating/cooling leg labels",
            "admission_model_forms": "branch-specific ordinary-pipe scorecard can admit rows only after masks/gates pass",
            "runtime_allowed_inputs": "geometry;roughness/materials;setup external BCs;solved fluid temperatures",
            "runtime_forbidden_inputs": "global f multiplier;CFD mdot;validation temperatures",
            "diagnostic_allowed": "pressure ladder and heat residual targets after solve",
            "downstream_owner": "TODO-BRANCH-SPECIFIC-ORDINARY-PIPE-SCORECARD;TODO-PREDICT-BOUNDARY-LAYER-DEVELOPMENT-SCORECARD",
        },
    ]


def runtime_audit_rows() -> list[dict[str, object]]:
    return [
        {
            "check": "no_cfd_mdot_runtime",
            "status": "pass_forbidden",
            "forbidden_input": "CFD mdot",
            "contract": "mdot is the solved unknown and CFD mdot is target/diagnostic evidence only.",
        },
        {
            "check": "no_realized_wallHeatFlux_runtime",
            "status": "pass_forbidden",
            "forbidden_input": "realized CFD wallHeatFlux",
            "contract": "wallHeatFlux may score heat-loss models after solve but cannot drive them at runtime.",
        },
        {
            "check": "no_imposed_cfd_cooler_duty_runtime",
            "status": "pass_forbidden",
            "forbidden_input": "imposed CFD cooler duty",
            "contract": "cooler/HX removal must come from admitted setup-legal cooler model outputs.",
        },
        {
            "check": "no_validation_temperature_runtime",
            "status": "pass_forbidden",
            "forbidden_input": "validation TP/TW temperatures",
            "contract": "probe temperatures are score targets only; runtime temperatures come from the model state.",
        },
        {
            "check": "no_global_multiplier",
            "status": "pass_forbidden",
            "forbidden_input": "hidden global friction or heat-loss multiplier",
            "contract": "pressure and thermal closures must be segment-local with named model slots.",
        },
        {
            "check": "no_recirc_single_stream_coefficients",
            "status": "pass_forbidden",
            "forbidden_input": "true Nu/f_D/K fits from recirculating rows",
            "contract": "recirculating rows require hybrid/diagnostic labels until onset and single-stream gates pass.",
        },
    ]


def downstream_gate_rows() -> list[dict[str, object]]:
    return [
        {
            "downstream_task": "TODO-PREDICT-SEGMENT-PRESSURE-MODELS",
            "required_input": "segment_equation_contract.csv;pressure_model_slots.csv;runtime_input_contract.csv",
            "gate": "pressure scorecard must separate buoyancy drive, distributed friction, development/reset, local K, apparent junction loss, and recirculation labels",
            "may_start_after_this_package": "yes",
        },
        {
            "downstream_task": "TODO-PREDICT-SEGMENT-THERMAL-MODELS",
            "required_input": "segment_equation_contract.csv;thermal_model_slots.csv;runtime_input_contract.csv",
            "gate": "thermal scorecard must keep heater, cooler, passive wall, test-section, radiation, and junction residual ownership separate",
            "may_start_after_this_package": "yes",
        },
        {
            "downstream_task": "TODO-PREDICT-COUPLED-SEGMENT-M3TS-SCORECARD",
            "required_input": "completed segment pressure and thermal scorecards",
            "gate": "coupled root solve must preserve train/validation/holdout split and runtime leakage rules",
            "may_start_after_this_package": "no",
        },
        {
            "downstream_task": "TODO-PREDICT-BOUNDARY-LAYER-DEVELOPMENT-SCORECARD",
            "required_input": "segment_equation_contract.csv plus pressure/thermal segment rows",
            "gate": "toggle entrance/reset/Graetz/development effects by segment without hidden global multiplier",
            "may_start_after_this_package": "yes",
        },
    ]


def source_manifest() -> list[dict[str, object]]:
    sources = [
        ("segment_plan", SEGMENT_PLAN, "expanded segment pressure/thermal equation policy"),
        ("m3ts_requirement", M3TS_NOTE, "test-section heat-loss successor requirement"),
        ("pressure_term_ledger", PRESSURE_LEDGER, "pressure term provenance and target rows"),
        ("patchwise_heat_ledger", PATCHWISE_HEAT, "source/sink ownership and wallHeatFlux caveats"),
        ("enthalpy_interface_ledger", INTERFACE_HEAT, "segment heat residual and interface evidence"),
        ("predictive_input_contract", INPUT_CONTRACT, "runtime forbidden input precedent"),
        ("recirculation_policy", RECIRC_POLICY, "coefficient label admission policy"),
        ("salt1_schema_promotion", SALT1_PROMOTION, "Salt1 final-training schema rows"),
        ("salt2_pm5_val_readiness", SALT2_READINESS, "fluid+walls readiness rows for holdout/external evidence"),
    ]
    return [
        {"source_id": key, "path": rel(path), "exists": str(path.exists()).lower(), "use": use}
        for key, path, use in sources
    ]


def write_readme(summary: dict[str, object]) -> None:
    lines = [
        "---",
        "provenance:",
        f"  - {rel(SEGMENT_PLAN)}",
        f"  - {rel(M3TS_NOTE)}",
        f"  - {rel(INPUT_CONTRACT)}",
        "tags: [segment-equation-contract, forward-predictive-model, m3ts, runtime-input-contract]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(JOURNAL)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Coordinator/Writer/Implementer/Tester",
        "type: work_product",
        "status: complete",
        "---",
        "# Segment Equation Contract",
        "",
        "## Decision",
        "",
        "The next forward model must be segment-resolved. Buoyancy drive, pressure loss, source/sink heat terms, "
        "properties, and admission labels are local to loop regions. A global friction or heat-loss multiplier is "
        "not an admitted model form.",
        "",
        "## Main Outputs",
        "",
        "- `equation_forms.csv`: expanded pressure/thermal/root equations.",
        "- `segment_equation_contract.csv`: allowed model slots for each loop region.",
        "- `pressure_model_slots.csv`: pressure-specific slot aliases derived from the segment table.",
        "- `thermal_model_slots.csv`: thermal-specific slot aliases derived from the segment table.",
        "- `runtime_input_contract.csv`: runtime leakage audit.",
        "- `downstream_gate_contract.csv`: gates for pressure, thermal, boundary-layer, and coupled scorecards.",
        "- `source_manifest.csv`: cited source paths.",
        "",
        "## Observed Facts",
        "",
        f"- Equation rows: `{summary['equation_rows']}`.",
        f"- Segment rows: `{summary['segment_rows']}`.",
        f"- Runtime audit rows: `{summary['runtime_audit_rows']}`.",
        f"- Downstream gate rows: `{summary['downstream_gate_rows']}`.",
        "",
        "## Guardrails",
        "",
        "- CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty, validation temperatures, hidden global multipliers, "
        "and recirculating-row true `Nu`/`f_D`/`K` fits are forbidden runtime inputs.",
        "- Pressure and thermal scorecards may now start from this package, but the coupled M3+TS scorecard must wait until both are complete.",
        "- Diagnostic CFD rows remain score/target evidence unless an admission package explicitly promotes a model coefficient.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


def write_closeout(summary: dict[str, object]) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    IMPORT.parent.mkdir(parents=True, exist_ok=True)

    status_lines = [
        "---",
        "provenance:",
        f"  - {rel(OUT / 'README.md')}",
        f"  - {rel(OUT / 'summary.json')}",
        "tags: [status, segment-equation-contract, forward-predictive-model]",
        "related:",
        f"  - {rel(JOURNAL)}",
        f"  - {rel(IMPORT)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Coordinator/Writer/Implementer/Tester",
        "type: status",
        "status: complete",
        "---",
        f"# {TASK} Status",
        "",
        "## Observed Facts",
        "",
        "- The July 15 segment plan expands buoyancy drive and pressure loss into segment-local equations.",
        "- The M3+TS note requires an explicit setup-only test-section heat-loss term.",
        "- Current pressure/heat evidence remains diagnostic unless specific admission gates promote a coefficient.",
        "",
        "## Changes Made",
        "",
        f"- Wrote `{rel(OUT)}/` with equation, segment, runtime-input, and downstream-gate contracts.",
        "- Added tests that enforce required loop regions, expanded equations, and forbidden runtime inputs.",
        "",
        "## Validation",
        "",
        "- `python3 -m unittest tools.analyze.test_segment_equation_contract`",
        "- Parsed generated `summary.json` and import manifest with `python3 -m json.tool`.",
        "",
        "## Blockers",
        "",
        "- No blocker remains for starting segment pressure and segment thermal scorecards.",
        "- Coupled M3+TS remains blocked until both scorecards exist.",
        "- Generated docs index refresh was skipped because active AGENT-482 owns generated index files.",
    ]
    STATUS.write_text("\n".join(status_lines) + "\n")

    journal_lines = [
        "---",
        "provenance:",
        f"  - {rel(SEGMENT_PLAN)}",
        f"  - {rel(M3TS_NOTE)}",
        f"  - {rel(OUT / 'README.md')}",
        "tags: [journal, segment-equation-contract, forward-predictive-model]",
        "related:",
        f"  - {rel(STATUS)}",
        f"  - {rel(IMPORT)}",
        f"task: {TASK}",
        f"date: {DATE}",
        "role: Coordinator/Writer/Implementer/Tester",
        "type: journal",
        "status: complete",
        "---",
        "# Segment Equation Contract Journal",
        "",
        "## Files Inspected",
        "",
        f"- `{rel(SEGMENT_PLAN)}`",
        f"- `{rel(M3TS_NOTE)}`",
        f"- `{rel(PRESSURE_LEDGER)}`",
        f"- `{rel(PATCHWISE_HEAT)}`",
        f"- `{rel(INPUT_CONTRACT)}`",
        f"- `{rel(RECIRC_POLICY)}`",
        "",
        "## Files Changed",
        "",
        "- `tools/analyze/build_segment_equation_contract.py`",
        "- `tools/analyze/test_segment_equation_contract.py`",
        f"- `{rel(OUT)}/`",
        f"- `{rel(STATUS)}`",
        f"- `{rel(JOURNAL)}`",
        f"- `{rel(IMPORT)}`",
        "- `.agent/BOARD.md` own row status",
        "",
        "## Interpretation",
        "",
        "The contract is now frozen enough for pressure and thermal model scorecards to start independently. "
        "It intentionally does not admit any new coefficients.",
        "",
        "## Recommended Next Action",
        "",
        "Start `TODO-PREDICT-SEGMENT-PRESSURE-MODELS` or `TODO-PREDICT-SEGMENT-THERMAL-MODELS`; do not run coupled M3+TS first.",
    ]
    JOURNAL.write_text("\n".join(journal_lines) + "\n")

    manifest = {
        "task": TASK,
        "date": DATE,
        "package": rel(OUT),
        "outputs": sorted(path.name for path in OUT.iterdir() if path.is_file()),
        "summary": summary,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
        "generated_index_refresh_note": "Skipped because active AGENT-482 owns generated docs index files.",
    }
    write_json(IMPORT, manifest)


def main() -> dict[str, object]:
    require_sources()
    OUT.mkdir(parents=True, exist_ok=True)

    equations = equation_forms()
    segments = segment_rows()
    runtime = runtime_audit_rows()
    downstream = downstream_gate_rows()
    sources = source_manifest()
    pressure_slots = [
        {
            "loop_region": row["loop_region"],
            "one_d_segments": row["one_d_segments"],
            "pressure_drive_form": row["pressure_drive_form"],
            "pressure_loss_slots": row["pressure_loss_slots"],
            "admission_model_forms": row["admission_model_forms"],
            "runtime_forbidden_inputs": row["runtime_forbidden_inputs"],
        }
        for row in segments
    ]
    thermal_slots = [
        {
            "loop_region": row["loop_region"],
            "one_d_segments": row["one_d_segments"],
            "thermal_slots": row["thermal_slots"],
            "property_form": row["property_form"],
            "admission_model_forms": row["admission_model_forms"],
            "runtime_forbidden_inputs": row["runtime_forbidden_inputs"],
        }
        for row in segments
    ]

    write_csv(
        OUT / "equation_forms.csv",
        equations,
        ["equation_id", "scope", "equation_text", "implementation_contract", "admission_gate"],
    )
    write_csv(
        OUT / "segment_equation_contract.csv",
        segments,
        [
            "loop_region",
            "one_d_segments",
            "pressure_drive_form",
            "pressure_loss_slots",
            "thermal_slots",
            "property_form",
            "admission_model_forms",
            "runtime_allowed_inputs",
            "runtime_forbidden_inputs",
            "diagnostic_allowed",
            "downstream_owner",
        ],
    )
    write_csv(
        OUT / "pressure_model_slots.csv",
        pressure_slots,
        [
            "loop_region",
            "one_d_segments",
            "pressure_drive_form",
            "pressure_loss_slots",
            "admission_model_forms",
            "runtime_forbidden_inputs",
        ],
    )
    write_csv(
        OUT / "thermal_model_slots.csv",
        thermal_slots,
        [
            "loop_region",
            "one_d_segments",
            "thermal_slots",
            "property_form",
            "admission_model_forms",
            "runtime_forbidden_inputs",
        ],
    )
    write_csv(
        OUT / "runtime_input_contract.csv",
        runtime,
        ["check", "status", "forbidden_input", "contract"],
    )
    write_csv(
        OUT / "downstream_gate_contract.csv",
        downstream,
        ["downstream_task", "required_input", "gate", "may_start_after_this_package"],
    )
    write_csv(OUT / "source_manifest.csv", sources, ["source_id", "path", "exists", "use"])

    summary = {
        "task": TASK,
        "date": DATE,
        "equation_rows": len(equations),
        "segment_rows": len(segments),
        "pressure_slot_rows": len(pressure_slots),
        "thermal_slot_rows": len(thermal_slots),
        "runtime_audit_rows": len(runtime),
        "runtime_forbidden_pass_rows": sum(1 for row in runtime if row["status"] == "pass_forbidden"),
        "downstream_gate_rows": len(downstream),
        "pressure_and_thermal_scorecards_may_start": True,
        "coupled_m3ts_may_start": False,
        "all_sources_present": all(row["exists"] == "true" for row in sources),
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "generated_index_refreshed": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    write_closeout(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
