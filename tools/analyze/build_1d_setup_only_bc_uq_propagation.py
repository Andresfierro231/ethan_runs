#!/usr/bin/env python3
"""Build setup-only boundary-condition UQ propagation contract for the 1D model."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22"
SLUG = "1d_setup_only_bc_uq_propagation"
DATE = "2026-07-22"
OUTDIR = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation")

SOURCE_PATHS = [
    "operational_notes/maps/forward-predictive-model.md",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/summary.json",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/runtime_forbidden_audit.csv",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/sensor_projection_operator_table.csv",
    "work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_qoi_projection_table.csv",
    "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_0_baseline_release_gate/runtime_forbidden_field_audit.csv",
    "work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/runtime_mode_matrix.csv",
    "work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv",
    "work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_mf02_pressure_mdot_coupling_diagnostic/README.md",
]

FORBIDDEN_RUNTIME_FIELDS = [
    "CFD_mdot",
    "realized_CFD_wallHeatFlux",
    "imposed_CFD_cooler_duty",
    "validation_temperatures",
    "holdout_temperatures",
    "realized_test_section_heat",
    "heat_residual_as_runtime_closure",
]


@dataclass(frozen=True)
class Table:
    filename: str
    rows: list[dict[str, str]]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError(f"{path.name} has no rows")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_manifest(root: Path) -> list[dict[str, str]]:
    rows = []
    for idx, rel in enumerate(SOURCE_PATHS, 1):
        rows.append(
            {
                "source_id": f"SRC-{idx:02d}",
                "path": rel,
                "exists": str((root / rel).exists()).lower(),
                "used_as": "read_only_contract_or_context",
                "mutation_status": "not_modified_by_this_task",
            }
        )
    return rows


def uncertainty_source_table() -> list[dict[str, str]]:
    return [
        {
            "uq_id": "UQ01",
            "input_family": "heater_source_fraction",
            "setup_input": "lower-leg heater power and three-span distribution",
            "screening_prior_or_range": "Dirichlet-like normalized weights around 0.45/0.35/0.20 with +/-0.10 absolute cap per span",
            "range_status": "screening_prior_not_admitted_publication_interval",
            "runtime_allowed": "true_after_source_property_release",
            "protected_row_tuning_allowed": "false",
            "primary_qois": "TP3;TP4;TW4;TW5;TW6;mdot_model",
            "provenance": "setup-known source contract; conservative thermal ledger",
            "reason": "Source placement is a first-order train-only residual owner but not yet released.",
        },
        {
            "uq_id": "UQ02",
            "input_family": "cooler_hx_strength",
            "setup_input": "cooler/HX UA or effectiveness-NTU setup model",
            "screening_prior_or_range": "multiplicative UA/effectiveness factor 0.8 to 1.2 for screening",
            "range_status": "screening_prior_not_admitted_publication_interval",
            "runtime_allowed": "true_for_setup_model_only",
            "protected_row_tuning_allowed": "false",
            "primary_qois": "mdot_model;TP1;TP2;TW9;TW11",
            "provenance": "heat-loss Phase 0/1 contracts",
            "reason": "Cooler removal must be predicted from setup fields, not imposed from CFD duty.",
        },
        {
            "uq_id": "UQ03",
            "input_family": "ambient_temperature",
            "setup_input": "Ta",
            "screening_prior_or_range": "Ta +/-2 K unless setup log gives tighter bounds",
            "range_status": "screening_prior_pending_setup_log_review",
            "runtime_allowed": "true",
            "protected_row_tuning_allowed": "false",
            "primary_qois": "all_TW;passive_wall_heat;mdot_model",
            "provenance": "external BC/radiation runtime mode contract",
            "reason": "Ambient drive affects every external convection heat path.",
        },
        {
            "uq_id": "UQ04",
            "input_family": "external_convection_hA",
            "setup_input": "h_ext, exposed area, coverage factor",
            "screening_prior_or_range": "hA multiplicative factor 0.5 to 2.0 for sensitivity only",
            "range_status": "wide_screening_prior_not_source_release",
            "runtime_allowed": "true_when_declared_by_segment",
            "protected_row_tuning_allowed": "false",
            "primary_qois": "TW1-TW11;passive_wall_residual",
            "provenance": "Phase 1 external BC contract; M2 passive wall gate",
            "reason": "Broad passive hA moved TW5 strongly, so it must be propagated but not selected as a global multiplier.",
        },
        {
            "uq_id": "UQ05",
            "input_family": "radiation",
            "setup_input": "emissivity, Tsur, area, view-factor assumption",
            "screening_prior_or_range": "emissivity 0.85 to 0.98; Tsur +/-5 K; view factor fixed or declared categorical",
            "range_status": "screening_prior_pending_radiation_capability",
            "runtime_allowed": "true_only_in_predictive_radiation_mode",
            "protected_row_tuning_allowed": "false",
            "primary_qois": "all_TW;external_loss;residual_owner",
            "provenance": "Phase 1 radiation semantics; conservative thermal ledger",
            "reason": "Radiation is predictive only when modeled from setup fields and solved surface states.",
        },
        {
            "uq_id": "UQ06",
            "input_family": "wall_layer_materials",
            "setup_input": "wall, insulation, quartz, and layer thickness/k",
            "screening_prior_or_range": "k and thickness +/-20% for missing-field sensitivity; geometry dimensions +/-2% where measured",
            "range_status": "screening_prior_requires_material_manifest",
            "runtime_allowed": "true_when_setup_material_fields_exist",
            "protected_row_tuning_allowed": "false",
            "primary_qois": "TW sensors; test_section_path; passive_wall_path",
            "provenance": "thermal heat-loss alignment; conservative thermal ledger missing-field table",
            "reason": "Wall/layer uncertainty should be explicit rather than hidden in internal Nu.",
        },
        {
            "uq_id": "UQ07",
            "input_family": "fluid_property_mode",
            "setup_input": "cp, rho, mu, k, Pr property model",
            "screening_prior_or_range": "discrete property modes plus local +/-5% scalar smoke for sensitivity ranking",
            "range_status": "screening_prior_pending_source_property_labels",
            "runtime_allowed": "true_with_property_mode_label",
            "protected_row_tuning_allowed": "false",
            "primary_qois": "mdot_model;enthalpy_balance;Nu_diagnostic_labels",
            "provenance": "source/property label enforcement",
            "reason": "Property sensitivity must be labeled before any fit/admission consumer.",
        },
        {
            "uq_id": "UQ08",
            "input_family": "pressure_loss_terms",
            "setup_input": "baseline friction/minor-loss forms and admitted section-effective terms",
            "screening_prior_or_range": "one-at-a-time +/-10% on admitted setup pressure terms; F6/component-K remains disabled",
            "range_status": "diagnostic_screening_only_no_f6_admission",
            "runtime_allowed": "true_for_existing_baseline_terms",
            "protected_row_tuning_allowed": "false",
            "primary_qois": "mdot_model;enthalpy_transport",
            "provenance": "MF02 pressure-mdot diagnostic; pressure/F6 guardrails",
            "reason": "Pressure uncertainty propagates through mdot, but current F6 rows are not admissible coefficient evidence.",
        },
        {
            "uq_id": "UQ09",
            "input_family": "sensor_projection",
            "setup_input": "TP/TW projection operator and coordinate/segment mapping",
            "screening_prior_or_range": "bounded/mapped/excluded categorical classes; no temperature offset release",
            "range_status": "operator_uncertainty_contract_ready_no_runtime_temperature_release",
            "runtime_allowed": "post_solve_projection_only",
            "protected_row_tuning_allowed": "false",
            "primary_qois": "TP/TW score calculation",
            "provenance": "1D sensor projection operator; N4 uncertainty table",
            "reason": "Sensor observations are score targets after prediction, never model inputs.",
        },
    ]


def propagation_plan() -> list[dict[str, str]]:
    return [
        {
            "stage": "P0",
            "action": "freeze runtime input set",
            "inputs_varied": "only rows in uncertainty_source_table with runtime_allowed not false",
            "outputs_recorded": "runtime input manifest; split labels; source/property labels",
            "admission_or_score_allowed": "false",
            "acceptance": "no forbidden runtime field appears in model execution inputs",
        },
        {
            "stage": "P1",
            "action": "one-at-a-time screening",
            "inputs_varied": "UQ01-UQ09 individually",
            "outputs_recorded": "mdot_model, segment heat terms, R_s owner rows, TP/TW projections",
            "admission_or_score_allowed": "false",
            "acceptance": "finite root and finite projected QOIs on train rows only",
        },
        {
            "stage": "P2",
            "action": "low-order interaction screen",
            "inputs_varied": "heater_source_fraction x passive hA; cooler UA x pressure terms; radiation x passive hA",
            "outputs_recorded": "interaction signs and dominance labels",
            "admission_or_score_allowed": "false",
            "acceptance": "interactions reported as sensitivity, not selected multipliers",
        },
        {
            "stage": "P3",
            "action": "candidate-specific UQ after release",
            "inputs_varied": "only one source/property released candidate plus setup priors",
            "outputs_recorded": "same-QOI train uncertainty envelope",
            "admission_or_score_allowed": "blocked_until_release",
            "acceptance": "separate row releases exactly one candidate before protected scoring",
        },
        {
            "stage": "P4",
            "action": "protected-row propagation after freeze",
            "inputs_varied": "frozen prior set only",
            "outputs_recorded": "validation/holdout/external scores and intervals",
            "admission_or_score_allowed": "only_after_frozen_runtime_legal_candidate",
            "acceptance": "no model selection or tuning from protected-row outcomes",
        },
    ]


def lightweight_sensitivity_matrix() -> list[dict[str, str]]:
    rows = []
    impacts = {
        "heater_source_fraction": ("high", "local heated-incline TP/TW and lower-leg enthalpy"),
        "cooler_hx_strength": ("high", "mdot and cooled branch/top-loop temperatures"),
        "ambient_temperature": ("medium", "external heat losses and wall temperatures"),
        "external_convection_hA": ("high", "TW residual owner and passive wall losses"),
        "radiation": ("medium", "TW surface temperatures and external-loss split"),
        "wall_layer_materials": ("medium", "TW wall-state projection and test-section path"),
        "fluid_property_mode": ("medium", "mdot, Re/Pr, enthalpy transport"),
        "pressure_loss_terms": ("medium", "mdot and coupled heat transport"),
        "sensor_projection": ("high_for_score_low_for_runtime", "reported TP/TW errors"),
    }
    for family, (rank, note) in impacts.items():
        rows.append(
            {
                "input_family": family,
                "mdot_effect_rank": "high" if family in {"cooler_hx_strength", "pressure_loss_terms", "fluid_property_mode"} else "low_to_medium",
                "tp_effect_rank": "high" if family in {"heater_source_fraction", "cooler_hx_strength", "sensor_projection"} else "medium",
                "tw_effect_rank": "high" if family in {"external_convection_hA", "sensor_projection", "heater_source_fraction"} else "medium",
                "dominant_pathway": note,
                "first_screen_design": "one_at_a_time_train_only",
                "scientific_status": f"{rank}; screening only until released/frozen",
            }
        )
    return rows


def protected_row_guardrails() -> list[dict[str, str]]:
    return [
        {
            "guardrail_id": "G01",
            "protected_item": field,
            "runtime_allowed": "false",
            "fit_allowed": "false",
            "model_selection_allowed": "false",
            "allowed_use": "diagnostic or post-freeze score comparison only",
            "enforcement": "fail package if marked runtime allowed",
        }
        for field in FORBIDDEN_RUNTIME_FIELDS
    ] + [
        {
            "guardrail_id": "G08",
            "protected_item": "global_multiplier_selection",
            "runtime_allowed": "false",
            "fit_allowed": "false",
            "model_selection_allowed": "false",
            "allowed_use": "none",
            "enforcement": "all broad multiplier rows remain diagnostic/blocker evidence",
        },
        {
            "guardrail_id": "G09",
            "protected_item": "source_property_release",
            "runtime_allowed": "false_from_this_row",
            "fit_allowed": "false_from_this_row",
            "model_selection_allowed": "false_from_this_row",
            "allowed_use": "separate release preflight only",
            "enforcement": "summary source_property_release_rows=0",
        },
    ]


def readiness_gate() -> list[dict[str, str]]:
    return [
        {"gate_id": "R01", "gate": "runtime_input_lint", "status": "pass_by_contract", "reason": "forbidden runtime fields are listed and blocked"},
        {"gate_id": "R02", "gate": "source_property_release", "status": "blocked", "reason": "this row defines UQ propagation only"},
        {"gate_id": "R03", "gate": "candidate_admission", "status": "blocked", "reason": "no frozen runtime-legal candidate exists"},
        {"gate_id": "R04", "gate": "protected_scoring", "status": "blocked", "reason": "UQ plan must run only after freeze"},
        {"gate_id": "R05", "gate": "compute_launch", "status": "not_launched", "reason": "contract/runbook only; no solver or sampler"},
        {"gate_id": "R06", "gate": "publication_interval", "status": "not_ready", "reason": "ranges are screening priors, not final UQ intervals"},
    ]


def no_mutation_guardrails() -> list[dict[str, str]]:
    return [
        {"guardrail": "native CFD/OpenFOAM outputs", "status": "not_mutated"},
        {"guardrail": "scheduler/solver/sampler", "status": "not_launched"},
        {"guardrail": "Fluid/external repository", "status": "not_mutated"},
        {"guardrail": "registry/admission/blocker register", "status": "not_mutated"},
        {"guardrail": "fit/model selection/final score", "status": "not_performed"},
        {"guardrail": "validation/holdout tuning", "status": "not_performed"},
    ]


def validate(tables: list[Table], root: Path) -> list[str]:
    errors: list[str] = []
    manifest = next(t.rows for t in tables if t.filename == "source_manifest.csv")
    for row in manifest:
        if row["exists"] != "true":
            errors.append(f"missing source: {row['path']}")
    protected = next(t.rows for t in tables if t.filename == "protected_row_guardrails.csv")
    for row in protected:
        if row["protected_item"] in FORBIDDEN_RUNTIME_FIELDS and row["runtime_allowed"] != "false":
            errors.append(f"forbidden field not blocked: {row['protected_item']}")
        if row["fit_allowed"] not in {"false", "false_from_this_row"}:
            errors.append(f"fit unexpectedly allowed: {row['protected_item']}")
    sources = next(t.rows for t in tables if t.filename == "uncertainty_source_table.csv")
    for row in sources:
        if row["protected_row_tuning_allowed"] != "false":
            errors.append(f"protected tuning allowed: {row['uq_id']}")
        forbidden_text = row["setup_input"] + row["screening_prior_or_range"]
        if "validation temperature" in forbidden_text:
            errors.append(f"validation temperature in setup prior: {row['uq_id']}")
    if not (root / ".agent/BOARD.md").exists():
        errors.append("repo root sanity check failed")
    return errors


def readme_text(generated_at: str, counts: dict[str, int], decision: str) -> str:
    return f"""---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
tags: [predictive-1d, uncertainty, setup-only, runtime-leakage, no-admission]
related:
  - .agent/status/{DATE}_{TASK_ID}.md
  - .agent/journal/{DATE}/1d-setup-only-bc-uq-propagation.md
  - imports/{DATE}_{SLUG}.json
task: {TASK_ID}
date: {DATE}
role: Uncertainty / Forward-pred / Thermal-modeling / Hydraulics / Tester / Writer
type: work_product
status: complete
---
# 1D Setup-Only BC UQ Propagation Contract

Generated: `{generated_at}`

Decision: `{decision}`.

This package defines the setup-only uncertainty propagation plan for the 1D
model. It is a runbook and screening-prior contract, not a completed UQ
calculation and not a publication interval.

## Scope

The contract covers heater source fraction, cooler/HX strength, ambient and
radiation fields, external convection, wall/layer materials, fluid property
mode, pressure-loss terms, and TP/TW sensor projection. All ranges are marked as
screening priors unless a later release row admits tighter source-specific
intervals.

## Files

- `uncertainty_source_table.csv`: {counts['source_rows']} setup-only UQ sources and ranges.
- `propagation_plan.csv`: {counts['plan_rows']} phased propagation stages.
- `lightweight_sensitivity_matrix.csv`: {counts['sensitivity_rows']} expected QOI pathways.
- `protected_row_guardrails.csv`: {counts['protected_rows']} leakage and split guardrails.
- `readiness_gate.csv`: {counts['readiness_rows']} execution/admission gates.
- `source_manifest.csv`, `no_mutation_guardrails.csv`, `summary.json`.

## Scientific Use

Use this to design train-only smoke/UQ runs and to document what must remain
fixed before protected validation/holdout/external scoring. Do not cite the
screening ranges as final uncertainty intervals.

## Guardrails

No solver, sampler, scheduler job, Fluid edit, external thesis/LaTeX edit,
registry/admission mutation, source/property release, protected scoring,
fitting, model selection, or blocker-register change was performed.
"""


def build(outdir: Path = OUTDIR) -> dict:
    root = repo_root()
    out = root / outdir
    generated_at = datetime.now(timezone.utc).isoformat()
    decision = "setup_only_uq_contract_ready_no_compute_no_publication_interval"
    tables = [
        Table("uncertainty_source_table.csv", uncertainty_source_table()),
        Table("propagation_plan.csv", propagation_plan()),
        Table("lightweight_sensitivity_matrix.csv", lightweight_sensitivity_matrix()),
        Table("protected_row_guardrails.csv", protected_row_guardrails()),
        Table("readiness_gate.csv", readiness_gate()),
        Table("source_manifest.csv", source_manifest(root)),
        Table("no_mutation_guardrails.csv", no_mutation_guardrails()),
    ]
    errors = validate(tables, root)
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(errors))
    for table in tables:
        write_csv(out / table.filename, table.rows)
    counts = {
        "source_rows": len(tables[0].rows),
        "plan_rows": len(tables[1].rows),
        "sensitivity_rows": len(tables[2].rows),
        "protected_rows": len(tables[3].rows),
        "readiness_rows": len(tables[4].rows),
        "manifest_rows": len(tables[5].rows),
        "guardrail_rows": len(tables[6].rows),
    }
    summary = {
        "task_id": TASK_ID,
        "decision": decision,
        "generated_at_utc": generated_at,
        "counts": counts,
        "screening_priors_not_publication_intervals": True,
        "runtime_forbidden_inputs_all_blocked": True,
        "source_property_release_rows": 0,
        "candidate_admission_rows": 0,
        "protected_scoring_rows": 0,
        "fit_or_model_selection_rows": 0,
        "scheduler_or_sampler_launched": False,
        "solver_launched": False,
        "native_output_mutated": False,
        "registry_mutated": False,
        "fluid_mutated": False,
        "external_repo_mutated": False,
        "validation_errors": errors,
        "next_recommended_tasks": [
            "train-only one-at-a-time UQ smoke after runtime execution row is claimed",
            "TODO-1D-MODEL-HIERARCHY-ABLATION-LADDER-PACKET-2026-07-22",
            "source/property release preflight only after a narrow candidate exists",
        ],
    }
    write_json(out / "summary.json", summary)
    (out / "README.md").write_text(readme_text(generated_at, counts, decision), encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
