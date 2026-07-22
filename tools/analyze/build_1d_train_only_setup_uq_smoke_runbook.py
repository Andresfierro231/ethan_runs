#!/usr/bin/env python3
"""Build the train-only setup-UQ smoke runbook for the 1D model."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-RUNBOOK-2026-07-22"
SLUG = "1d_train_only_setup_uq_smoke_runbook"
DATE = "2026-07-22"
OUTDIR = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_runbook")

SOURCE_PATHS = [
    "work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/conservative_equation_ledger.csv",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/sensor_projection_operator_table.csv",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/uncertainty_source_table.csv",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_1d_thermal_pressure_root_coupling_stability_audit/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_source_property_release_atlas/runtime_legality_audit.csv",
]

FORBIDDEN = [
    "CFD_mdot",
    "realized_CFD_wallHeatFlux",
    "imposed_CFD_cooler_duty",
    "validation_temperatures",
    "holdout_temperatures",
    "external_test_temperatures",
    "realized_test_section_heat",
    "heat_residual_as_runtime_closure",
    "global_multiplier_selected_by_score",
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
    return [
        {
            "source_id": f"SRC-{idx:02d}",
            "path": rel,
            "exists": str((root / rel).exists()).lower(),
            "used_as": "read_only_contract_input",
            "mutation_status": "not_modified_by_this_task",
        }
        for idx, rel in enumerate(SOURCE_PATHS, 1)
    ]


def setup_legal_variation_matrix() -> list[dict[str, str]]:
    return [
        {
            "variant_id": "V00",
            "input_family": "baseline_frozen_setup",
            "variation": "nominal setup-only baseline",
            "allowed_runtime_inputs": "declared setup fields and model-solved states only",
            "train_cases": "nominal train rows only",
            "protected_cases": "not executed",
            "qoi_focus": "mdot_model;TP/TW projections;heat ledger",
            "status": "required_reference",
            "stop_if": "root not bracketed or runtime lint fails",
        },
        {
            "variant_id": "V01",
            "input_family": "heater_source_fraction",
            "variation": "one-at-a-time +/-0.10 absolute span-weight perturbations with normalized total Q",
            "allowed_runtime_inputs": "setup heater power; declared distribution only",
            "train_cases": "train only",
            "protected_cases": "not executed",
            "qoi_focus": "TP3;TP4;TW4;TW5;TW6;heater residual owner",
            "status": "smoke_allowed_no_release",
            "stop_if": "source/property release is implied or protected row is used",
        },
        {
            "variant_id": "V02",
            "input_family": "cooler_hx_strength",
            "variation": "UA/effectiveness factor 0.8, 1.0, 1.2",
            "allowed_runtime_inputs": "setup HX model fields only",
            "train_cases": "train only",
            "protected_cases": "not executed",
            "qoi_focus": "mdot_model;TP1;TP2;TW9;TW11;cooler residual owner",
            "status": "smoke_allowed_no_imposed_duty",
            "stop_if": "imposed CFD cooler duty appears in runtime input manifest",
        },
        {
            "variant_id": "V03",
            "input_family": "ambient_temperature",
            "variation": "Ta -2 K, nominal, Ta +2 K",
            "allowed_runtime_inputs": "setup ambient field only",
            "train_cases": "train only",
            "protected_cases": "not executed",
            "qoi_focus": "all TW;passive wall heat;mdot_model",
            "status": "smoke_allowed",
            "stop_if": "sensor temperatures are used as boundary conditions",
        },
        {
            "variant_id": "V04",
            "input_family": "external_convection_hA",
            "variation": "segment-declared hA factor 0.5, 1.0, 2.0 for sensitivity only",
            "allowed_runtime_inputs": "setup h_ext, area, coverage and solved surface state",
            "train_cases": "train only",
            "protected_cases": "not executed",
            "qoi_focus": "TW residuals;passive_wall_residual;heat ledger",
            "status": "smoke_allowed_broad_multiplier_not_selectable",
            "stop_if": "global multiplier is selected as a candidate",
        },
        {
            "variant_id": "V05",
            "input_family": "radiation",
            "variation": "emissivity/Tsur sensitivity in predictive radiation mode only",
            "allowed_runtime_inputs": "emissivity;Tsur;area;solved surface state",
            "train_cases": "train only",
            "protected_cases": "not executed",
            "qoi_focus": "TW surface projection;external loss split;radiation residual owner",
            "status": "smoke_allowed_if_capability_exists_else_skip_with_reason",
            "stop_if": "radiation is added on top of realized wallHeatFlux replay",
        },
        {
            "variant_id": "V06",
            "input_family": "fluid_property_mode",
            "variation": "declared property modes plus +/-5% scalar smoke",
            "allowed_runtime_inputs": "labeled property mode only",
            "train_cases": "train only",
            "protected_cases": "not executed",
            "qoi_focus": "mdot_model;Re/Pr;enthalpy balance",
            "status": "smoke_allowed_label_required",
            "stop_if": "property mode/source labels are blank",
        },
        {
            "variant_id": "V07",
            "input_family": "pressure_loss_terms",
            "variation": "+/-10% baseline setup pressure terms; F6/component-K disabled",
            "allowed_runtime_inputs": "existing baseline pressure terms only",
            "train_cases": "train only",
            "protected_cases": "not executed",
            "qoi_focus": "mdot_model;enthalpy transport;root stability",
            "status": "smoke_allowed_no_f6",
            "stop_if": "F6, component-K, clipped-K, or pressure recovery coefficient is admitted",
        },
        {
            "variant_id": "V08",
            "input_family": "sensor_projection",
            "variation": "projection class audit only; no temperature offset release",
            "allowed_runtime_inputs": "post-solve projection operator",
            "train_cases": "train only output audit",
            "protected_cases": "not executed",
            "qoi_focus": "TP/TW projection availability and excluded-sensor handling",
            "status": "post_solve_only",
            "stop_if": "observed TP/TW values alter runtime state",
        },
    ]


def executable_runbook() -> list[dict[str, str]]:
    return [
        {
            "step_id": "S00",
            "step_name": "claim_execution_row",
            "where": ".agent/BOARD.md",
            "command_or_action": "create a separate execution row before running Fluid or scheduler work",
            "expected_artifact": "active execution task with exact allowed paths",
            "failure_action": "do not run",
        },
        {
            "step_id": "S01",
            "step_name": "freeze_runtime_manifest",
            "where": "compute or local preflight",
            "command_or_action": "write runtime input manifest from setup-only fields and variation matrix",
            "expected_artifact": "runtime_input_manifest.csv",
            "failure_action": "stop if any forbidden field appears",
        },
        {
            "step_id": "S02",
            "step_name": "train_only_baseline_smoke",
            "where": "compute node if Fluid execution is nontrivial",
            "command_or_action": "run nominal setup-only train rows and record finite root/bracket status",
            "expected_artifact": "baseline_root_and_qoi_smoke.csv",
            "failure_action": "stop before sensitivity variants",
        },
        {
            "step_id": "S03",
            "step_name": "one_at_a_time_variants",
            "where": "compute node",
            "command_or_action": "run V01-V08 one at a time, skipping unsupported capabilities with reason",
            "expected_artifact": "one_at_a_time_setup_uq_smoke.csv",
            "failure_action": "record failure mode and continue only if root failures are isolated",
        },
        {
            "step_id": "S04",
            "step_name": "heat_ledger_and_sensor_projection",
            "where": "postprocess output tables",
            "command_or_action": "emit mdot, TP/TW projections, heat terms, R_s, and owner labels",
            "expected_artifact": "qoi_output_contract.csv; heat_ledger_sensitivity.csv",
            "failure_action": "mark row diagnostic-incomplete",
        },
        {
            "step_id": "S05",
            "step_name": "split_guardrail_review",
            "where": "local validation",
            "command_or_action": "verify train-only and no validation/holdout/external tuning",
            "expected_artifact": "split_guardrail_audit.csv",
            "failure_action": "invalidate smoke result",
        },
        {
            "step_id": "S06",
            "step_name": "decision_closeout",
            "where": "task package",
            "command_or_action": "write sensitivity ranking, blockers, no-release decision, status, journal, import manifest",
            "expected_artifact": "README.md; summary.json; finish_task OK",
            "failure_action": "do not advertise result as complete",
        },
    ]


def qoi_output_contract() -> list[dict[str, str]]:
    return [
        {"qoi_id": "Q01", "qoi": "mdot_model", "required": "true", "source": "model output", "protected_target": "false", "use": "root/pressure sensitivity"},
        {"qoi_id": "Q02", "qoi": "pressure_root_status", "required": "true", "source": "model diagnostic", "protected_target": "false", "use": "finite bracket/root gate"},
        {"qoi_id": "Q03", "qoi": "temperature_root_status", "required": "true", "source": "model diagnostic", "protected_target": "false", "use": "finite coupled thermal gate"},
        {"qoi_id": "Q04", "qoi": "TP_projection_predictions", "required": "true", "source": "post-solve projection", "protected_target": "false", "use": "train-only predicted TP shifts; no observed TP runtime input"},
        {"qoi_id": "Q05", "qoi": "TW_projection_predictions", "required": "true", "source": "post-solve projection", "protected_target": "false", "use": "train-only predicted TW shifts; no observed TW runtime input"},
        {"qoi_id": "Q06", "qoi": "heat_path_terms", "required": "true", "source": "conservative thermal ledger", "protected_target": "false", "use": "heater/cooler/passive/radiation/wall/test-section term shifts"},
        {"qoi_id": "Q07", "qoi": "segment_residual_R_s", "required": "true", "source": "conservative thermal ledger", "protected_target": "false", "use": "residual owner output only"},
        {"qoi_id": "Q08", "qoi": "residual_owner_label", "required": "true", "source": "post-solve classification", "protected_target": "false", "use": "blocker pointer; not closure"},
        {"qoi_id": "Q09", "qoi": "runtime_input_lint_status", "required": "true", "source": "execution validation", "protected_target": "false", "use": "runtime legality pass/fail"},
        {"qoi_id": "Q10", "qoi": "unsupported_variant_skip_reason", "required": "true", "source": "execution validation", "protected_target": "false", "use": "radiation/material capability transparency"},
    ]


def split_and_runtime_guardrails() -> list[dict[str, str]]:
    rows = [
        {
            "guardrail_id": f"G{idx:02d}",
            "field_or_action": field,
            "runtime_allowed": "false",
            "fit_allowed": "false",
            "model_selection_allowed": "false",
            "protected_scoring_allowed": "false",
            "allowed_use": "diagnostic comparison only after frozen prediction" if idx < 8 else "none",
        }
        for idx, field in enumerate(FORBIDDEN, 1)
    ]
    rows.extend(
        [
            {
                "guardrail_id": "G10",
                "field_or_action": "source_property_release",
                "runtime_allowed": "false_from_this_row",
                "fit_allowed": "false_from_this_row",
                "model_selection_allowed": "false_from_this_row",
                "protected_scoring_allowed": "false",
                "allowed_use": "separate release row only",
            },
            {
                "guardrail_id": "G11",
                "field_or_action": "validation_holdout_external_rows",
                "runtime_allowed": "false",
                "fit_allowed": "false",
                "model_selection_allowed": "false",
                "protected_scoring_allowed": "false_from_smoke_row",
                "allowed_use": "not used in train-only smoke",
            },
        ]
    )
    return rows


def stop_rules() -> list[dict[str, str]]:
    return [
        {"stop_id": "STOP-01", "condition": "runtime manifest contains forbidden field", "required_action": "abort and mark invalid"},
        {"stop_id": "STOP-02", "condition": "baseline train root is nonfinite or unbracketed", "required_action": "stop before variants and report root blocker"},
        {"stop_id": "STOP-03", "condition": "variant changes protected-row score, fit, or model selection", "required_action": "invalidate execution row"},
        {"stop_id": "STOP-04", "condition": "source/property release or candidate freeze implied", "required_action": "stop; claim separate release row"},
        {"stop_id": "STOP-05", "condition": "F6/component-K/internal-Nu/exchange coefficient emitted", "required_action": "stop; coefficient admission is forbidden"},
        {"stop_id": "STOP-06", "condition": "unsupported radiation/material capability missing", "required_action": "skip variant with reason, do not infer residual"},
    ]


def no_mutation_guardrails() -> list[dict[str, str]]:
    return [
        {"guardrail": "solver/UQ execution", "status": "not_launched"},
        {"guardrail": "scheduler/sampler", "status": "not_launched"},
        {"guardrail": "native CFD/OpenFOAM outputs", "status": "not_mutated"},
        {"guardrail": "Fluid/external repositories", "status": "not_mutated"},
        {"guardrail": "registry/admission/blocker register", "status": "not_mutated"},
        {"guardrail": "source/property release, final score, candidate freeze", "status": "not_performed"},
    ]


def validate(tables: list[Table], root: Path) -> list[str]:
    errors: list[str] = []
    manifest = next(t.rows for t in tables if t.filename == "source_manifest.csv")
    for row in manifest:
        if row["exists"] != "true":
            errors.append(f"missing source: {row['path']}")
    guardrails = next(t.rows for t in tables if t.filename == "split_and_runtime_guardrails.csv")
    for row in guardrails:
        if row["field_or_action"] in FORBIDDEN and row["runtime_allowed"] != "false":
            errors.append(f"forbidden runtime field allowed: {row['field_or_action']}")
    variations = next(t.rows for t in tables if t.filename == "setup_legal_variation_matrix.csv")
    for row in variations:
        if "validation" in row["allowed_runtime_inputs"].lower():
            errors.append(f"validation in runtime inputs: {row['variant_id']}")
    qois = next(t.rows for t in tables if t.filename == "qoi_output_contract.csv")
    required = {"mdot_model", "TP_projection_predictions", "TW_projection_predictions", "heat_path_terms", "segment_residual_R_s"}
    if not required.issubset({row["qoi"] for row in qois}):
        errors.append("missing required QOI outputs")
    if not (root / ".agent/BOARD.md").exists():
        errors.append("repo root sanity check failed")
    return errors


def readme_text(generated_at: str, counts: dict[str, int], decision: str) -> str:
    return f"""---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_1d_setup_only_bc_uq_propagation/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/README.md
tags: [predictive-1d, setup-uq, train-only, runbook, no-execution]
related:
  - .agent/status/{DATE}_{TASK_ID}.md
  - .agent/journal/{DATE}/1d-train-only-setup-uq-smoke-runbook.md
  - imports/{DATE}_{SLUG}.json
task: {TASK_ID}
date: {DATE}
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Tester / Writer
type: work_product
status: complete
---
# 1D Train-Only Setup-UQ Smoke Runbook

Generated: `{generated_at}`

Decision: `{decision}`.

This package defines the next executable science row for the 1D model. It does
not launch the execution. A future worker must claim a separate execution row
before running Fluid, scheduler jobs, or UQ sweeps.

## What The Future Execution May Vary

Only setup-legal inputs: heater source fraction, setup cooler/HX strength,
ambient temperature, declared external hA, predictive radiation fields if the
capability exists, labeled property modes, existing baseline pressure-loss
terms, and post-solve sensor projection class audits.

## What It Must Report

`mdot_model`, root status, TP/TW projections, heat-path terms, segment residual
`R_s`, residual-owner labels, runtime-input lint status, and skip reasons for
unsupported variants.

## Files

- `setup_legal_variation_matrix.csv`: {counts['variation_rows']} variants.
- `executable_runbook.csv`: {counts['runbook_rows']} ordered execution steps.
- `qoi_output_contract.csv`: {counts['qoi_rows']} required outputs.
- `split_and_runtime_guardrails.csv`: {counts['guardrail_rows']} split/runtime guardrails.
- `stop_rules.csv`: {counts['stop_rows']} stop/abort conditions.
- `source_manifest.csv`, `no_mutation_guardrails.csv`, `summary.json`.

## Guardrails

No protected validation/holdout/external tuning, source/property release,
candidate freeze, final score, fit/model selection, coefficient admission,
solver execution, scheduler launch, Fluid edit, native-output mutation, registry
mutation, or external repository edit was performed.
"""


def build(outdir: Path = OUTDIR) -> dict:
    root = repo_root()
    out = root / outdir
    generated_at = datetime.now(timezone.utc).isoformat()
    decision = "train_only_setup_uq_smoke_runbook_ready_no_execution"
    tables = [
        Table("setup_legal_variation_matrix.csv", setup_legal_variation_matrix()),
        Table("executable_runbook.csv", executable_runbook()),
        Table("qoi_output_contract.csv", qoi_output_contract()),
        Table("split_and_runtime_guardrails.csv", split_and_runtime_guardrails()),
        Table("stop_rules.csv", stop_rules()),
        Table("source_manifest.csv", source_manifest(root)),
        Table("no_mutation_guardrails.csv", no_mutation_guardrails()),
    ]
    errors = validate(tables, root)
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(errors))
    for table in tables:
        write_csv(out / table.filename, table.rows)
    counts = {
        "variation_rows": len(tables[0].rows),
        "runbook_rows": len(tables[1].rows),
        "qoi_rows": len(tables[2].rows),
        "guardrail_rows": len(tables[3].rows),
        "stop_rows": len(tables[4].rows),
        "manifest_rows": len(tables[5].rows),
        "no_mutation_rows": len(tables[6].rows),
    }
    summary = {
        "task_id": TASK_ID,
        "decision": decision,
        "generated_at_utc": generated_at,
        "counts": counts,
        "execution_launched": False,
        "scheduler_or_sampler_launched": False,
        "solver_launched": False,
        "train_only": True,
        "protected_scoring_rows": 0,
        "fit_or_model_selection_rows": 0,
        "source_property_release_rows": 0,
        "candidate_freeze_rows": 0,
        "coefficient_admission_rows": 0,
        "runtime_forbidden_inputs_all_blocked": True,
        "native_output_mutated": False,
        "registry_mutated": False,
        "fluid_mutated": False,
        "external_repo_mutated": False,
        "validation_errors": errors,
        "next_recommended_task": "claim a separate execution row to run S00-S06 on train rows only",
    }
    write_json(out / "summary.json", summary)
    (out / "README.md").write_text(readme_text(generated_at, counts, decision), encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
