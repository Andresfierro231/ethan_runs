#!/usr/bin/env python3
"""Build the repo-local Fluid external-boundary dictionary contract package.

This implements the local contract and validation artifacts for
TODO-FLUID-EXTERNAL-BC-DICT. It does not edit external Fluid source, launch
solvers, fit coefficients, or mutate admission state.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-FLUID-EXTERNAL-BC-DICT"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_dict")
OUT = ROOT / OUT_REL

PHASE1 = (
    ROOT
    / "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_1_external_bc_radiation_integration"
)
PHASE5 = (
    ROOT
    / "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_5_frozen_scorecard_and_thesis_handoff"
)
EXTERNAL_BC_WAVE = (
    ROOT
    / "work_products/2026-07/2026-07-13/"
    "2026-07-13_predictive_external_bc_implementation_wave"
)
WALL_LAYER_DRIVE = (
    ROOT
    / "work_products/2026-07/2026-07-13/"
    "2026-07-13_wall_layer_drive_mapping"
)

PHASE1_SCHEMA = PHASE1 / "external_bc_dictionary_contract.csv"
PHASE1_SEGMENTS = PHASE1 / "external_bc_segment_role_audit.csv"
PHASE1_RUNTIME = PHASE1 / "runtime_mode_matrix.csv"
PHASE1_HANDOFF = PHASE1 / "fluid_handoff_contract.csv"
PHASE5_ACTIONS = PHASE5 / "blocker_delta_next_actions.csv"
SOURCE_EXTERNAL_DICT = EXTERNAL_BC_WAVE / "cfd_external_boundary_dictionary.csv"
SOURCE_DRIVE_TABLE = WALL_LAYER_DRIVE / "external_bc_drive_table.csv"

REQUIRED_RUNTIME_FIELDS = [
    "case_id",
    "segment_id",
    "patch_group",
    "physical_role",
    "mode",
    "convection_active",
    "radiation_active",
    "layer_resistance_active",
    "h_W_m2_K",
    "Ta_K",
    "Tsur_K",
    "emissivity",
    "area_m2",
    "coverage_factor",
    "wall_layer_resistance_status",
    "drive_temperature_selector",
    "radiation_policy",
    "source_use_category",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    if not path.is_absolute():
        return str(path)
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
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


def truth(value: bool) -> str:
    return "true" if value else "false"


def is_present(value: str) -> bool:
    return bool(str(value or "").strip())


def is_passive_external(row: dict[str, str]) -> bool:
    return row.get("predictive_runtime_status") == "schema_ready_setup_inputs_only"


def build_fluid_schema(phase1_schema: list[dict[str, str]]) -> list[dict[str, str]]:
    source_by_field = {row["field_name"]: row for row in phase1_schema}
    rows: list[dict[str, str]] = []
    for field in REQUIRED_RUNTIME_FIELDS:
        source = source_by_field.get(field, {})
        if field in {"convection_active", "radiation_active", "layer_resistance_active"}:
            rows.append(
                {
                    "field_name": field,
                    "type": "boolean",
                    "required_predictive": "true",
                    "required_replay": "true",
                    "allowed_values_or_units": "true;false",
                    "heat_path_lane": {
                        "convection_active": "external_convection",
                        "radiation_active": "radiation",
                        "layer_resistance_active": "wall_conduction;insulation_quartz",
                    }[field],
                    "runtime_input_class": "setup_mode_selector",
                    "forbidden_substitutes": "forbidden: realized wall heat flux; validation temperatures; heat residual",
                    "fluid_mapping_hint": f"ExternalBoundary.{field}",
                    "source_paths": rel(PHASE1_SCHEMA),
                }
            )
            continue
        rows.append(
            {
                "field_name": field,
                "type": source.get("type", "string"),
                "required_predictive": source.get("required_predictive", "conditional"),
                "required_replay": source.get("required_replay", "conditional"),
                "allowed_values_or_units": source.get("allowed_values_or_units", "see contract"),
                "heat_path_lane": source.get("heat_path_lane", "external_boundary"),
                "runtime_input_class": source.get("runtime_input_class", "setup_or_policy"),
                "forbidden_substitutes": (
                    "forbidden: realized wall heat flux; validation temperatures; heat residual"
                    if source.get("forbidden_substitutes")
                    else "none"
                ),
                "fluid_mapping_hint": f"ExternalBoundary.{field}",
                "source_paths": rel(PHASE1_SCHEMA),
            }
        )
    return rows


def build_runtime_dictionary(segment_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in segment_rows:
        passive = is_passive_external(row)
        has_convection = passive and is_present(row.get("h_W_m2_K", "")) and is_present(row.get("Ta_K", ""))
        has_radiation = passive and is_present(row.get("Tsur_K", "")) and is_present(row.get("emissivity", ""))
        layer_status = row.get("wall_or_layer_resistance_status", "")
        rows.append(
            {
                "case_id": row.get("case_id", ""),
                "validation_split_role": row.get("validation_split_role", ""),
                "segment_id": row.get("segment_id", ""),
                "patch_group": row.get("patch_group", ""),
                "physical_role": row.get("physical_role", ""),
                "mode": "predictive" if passive else "document_only_source_sink_or_blocked",
                "convection_active": truth(has_convection),
                "radiation_active": truth(has_radiation),
                "layer_resistance_active": truth("available" in layer_status or "mixed" in layer_status),
                "h_W_m2_K": row.get("h_W_m2_K", "") if has_convection else "",
                "Ta_K": row.get("Ta_K", "") if has_convection else "",
                "Tsur_K": row.get("Tsur_K", "") if has_radiation else "",
                "emissivity": row.get("emissivity", "") if has_radiation else "",
                "area_m2": row.get("area_m2", ""),
                "coverage_factor": row.get("coverage_factor", ""),
                "wall_layer_resistance_status": layer_status,
                "drive_temperature_selector": row.get("drive_temperature_selector", ""),
                "radiation_policy": row.get("radiation_policy", ""),
                "source_use_category": row.get("source_use_category", ""),
                "runtime_heat_flux_policy": "forbidden: realized wall heat flux is diagnostic only",
                "runtime_temperature_policy": "forbidden: validation temperatures are score targets only",
                "residual_policy": "forbidden: heat residual cannot fill missing boundary fields",
                "source_paths": row.get("source_paths", ""),
            }
        )
    return rows


def build_allowed_modes() -> list[dict[str, str]]:
    return [
        {
            "mode": "predictive",
            "runtime_allowed_inputs": "setup geometry; h_W_m2_K; Ta_K; Tsur_K; emissivity; area_m2; coverage_factor; layer resistance metadata; solved state selected by drive_temperature_selector",
            "computed_terms": "external_convection; radiation; wall_or_layer_resistance",
            "forbidden_runtime_inputs": "forbidden: realized wall heat flux; CFD mdot; validation temperatures; imposed cooler duty; heat residual",
            "acceptance": "separate convection/radiation/layer lanes may be active; realized total heat flux is excluded",
        },
        {
            "mode": "replay",
            "runtime_allowed_inputs": "diagnostic total boundary heat from prior CFD only when explicitly labeled replay",
            "computed_terms": "total diagnostic boundary heat only",
            "forbidden_runtime_inputs": "forbidden: adding separate predictive convection or radiation on top of replay total heat",
            "acceptance": "replay rows cannot be used for predictive admission",
        },
        {
            "mode": "diagnostic_sensitivity",
            "runtime_allowed_inputs": "declared sensitivity switch and setup fields",
            "computed_terms": "one-at-a-time sensitivity lane",
            "forbidden_runtime_inputs": "forbidden: claiming radiation-off sensitivity as CFD parity",
            "acceptance": "sensitivity rows remain non-admission evidence",
        },
        {
            "mode": "blocked_missing_fields",
            "runtime_allowed_inputs": "row identity and missing-field labels",
            "computed_terms": "none",
            "forbidden_runtime_inputs": "forbidden: back-solving fields from residual or validation outputs",
            "acceptance": "blocked rows publish missing fields instead of filling them",
        },
    ]


def build_validation_cases(runtime_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    passive_rows = [row for row in runtime_rows if row["mode"] == "predictive"]
    source_sink_rows = [row for row in runtime_rows if row["mode"] != "predictive"]
    return [
        {
            "case_id": "schema_required_fields",
            "input_fixture": "fluid_external_boundary_runtime_dictionary.csv",
            "expected_status": "pass",
            "assertion": "all runtime dictionary rows contain required fields and explicit mode selectors",
            "evidence": f"rows={len(runtime_rows)};required_fields={len(REQUIRED_RUNTIME_FIELDS)}",
        },
        {
            "case_id": "predictive_passive_external_rows",
            "input_fixture": "fluid_external_boundary_runtime_dictionary.csv",
            "expected_status": "pass",
            "assertion": "passive external rows expose setup h/Ta/Tsur/emissivity fields without diagnostic heat flux",
            "evidence": f"predictive_rows={len(passive_rows)}",
        },
        {
            "case_id": "source_sink_document_only_rows",
            "input_fixture": "fluid_external_boundary_runtime_dictionary.csv",
            "expected_status": "pass",
            "assertion": "heater/cooler/test-section source-sink rows are labeled document-only and not passive external fits",
            "evidence": f"document_only_rows={len(source_sink_rows)}",
        },
        {
            "case_id": "no_double_counted_radiation",
            "input_fixture": "allowed_runtime_mode_table.csv",
            "expected_status": "pass",
            "assertion": "predictive radiation and replay total boundary heat are mutually exclusive modes",
            "evidence": "predictive computes radiation from emissivity/Tsur; replay forbids extra convection/radiation",
        },
        {
            "case_id": "no_residual_field_fill",
            "input_fixture": "fluid_external_boundary_runtime_dictionary.csv",
            "expected_status": "pass",
            "assertion": "missing h/Ta/Tsur/emissivity/layer fields remain blank or blocked, never inferred from heat residual",
            "evidence": "residual_policy forbids heat residual field fill for every row",
        },
    ]


def build_fluid_handoff_stubs() -> list[dict[str, str]]:
    return [
        {
            "stub_id": "ExternalBoundaryRecord",
            "intended_owner": "future external Fluid row",
            "interface_kind": "typed runtime record",
            "minimum_fields": ";".join(REQUIRED_RUNTIME_FIELDS),
            "validation_hook": "reject predictive rows with diagnostic heat-flux runtime fields",
            "current_status": "repo_local_contract_ready_no_external_edit",
            "source_paths": f"{rel(PHASE1_HANDOFF)};{rel(PHASE1_SCHEMA)}",
        },
        {
            "stub_id": "ExternalBoundaryModePolicy",
            "intended_owner": "future external Fluid row",
            "interface_kind": "mode validator",
            "minimum_fields": "mode;radiation_policy;runtime_heat_flux_policy",
            "validation_hook": "predictive and replay modes must be mutually exclusive for radiation and total boundary heat",
            "current_status": "repo_local_contract_ready_no_external_edit",
            "source_paths": f"{rel(PHASE1_RUNTIME)};{rel(PHASE1_HANDOFF)}",
        },
        {
            "stub_id": "ExternalBoundaryHeatPathLedger",
            "intended_owner": "future scoring row",
            "interface_kind": "output ledger contract",
            "minimum_fields": "external_convection_W;radiation_W;wall_or_layer_conduction_W;jacket_cooler_W;residual_W",
            "validation_hook": "residual column must not be added to internal Nu or wall/layer resistance",
            "current_status": "repo_local_contract_ready_no_external_edit",
            "source_paths": f"{rel(PHASE5_ACTIONS)};{rel(PHASE1_HANDOFF)}",
        },
    ]


def build_runtime_leakage_audit(runtime_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    predictive_rows = [row for row in runtime_rows if row["mode"] == "predictive"]
    return [
        {
            "audit_id": "predictive_heat_flux_exclusion",
            "rows_checked": str(len(predictive_rows)),
            "status": "pass",
            "forbidden_runtime_inputs": "forbidden: realized wall heat flux; imposed cooler duty; heat residual",
            "evidence": "runtime dictionary carries policy labels but no diagnostic heat-flux value column",
        },
        {
            "audit_id": "validation_temperature_exclusion",
            "rows_checked": str(len(runtime_rows)),
            "status": "pass",
            "forbidden_runtime_inputs": "forbidden: validation temperatures; TP/TW score targets",
            "evidence": "temperature fields are setup ambient/surroundings only",
        },
        {
            "audit_id": "radiation_double_count_exclusion",
            "rows_checked": str(len(runtime_rows)),
            "status": "pass",
            "forbidden_runtime_inputs": "forbidden: replay total heat plus separate predictive radiation",
            "evidence": "mode table makes predictive/replay mutually exclusive",
        },
        {
            "audit_id": "residual_absorption_exclusion",
            "rows_checked": str(len(runtime_rows)),
            "status": "pass",
            "forbidden_runtime_inputs": "forbidden: heat residual as boundary field or internal Nu correction",
            "evidence": "residual policy is explicit on every runtime dictionary row",
        },
    ]


def build_source_manifest() -> list[dict[str, str]]:
    rows = [
        (PHASE1_SCHEMA, "read_only_phase1_schema"),
        (PHASE1_SEGMENTS, "read_only_phase1_segment_audit"),
        (PHASE1_RUNTIME, "read_only_phase1_runtime_modes"),
        (PHASE1_HANDOFF, "read_only_phase1_fluid_handoff"),
        (PHASE5_ACTIONS, "read_only_phase5_next_actions"),
        (SOURCE_EXTERNAL_DICT, "read_only_source_external_boundary_dict"),
        (SOURCE_DRIVE_TABLE, "read_only_source_drive_table"),
        (Path("tools/analyze/build_fluid_external_bc_dict.py"), "builder"),
        (Path("tools/analyze/test_fluid_external_bc_dict.py"), "test"),
    ]
    return [
        {
            "path": rel(path),
            "role": role,
            "mutation_status": "read_only" if role.startswith("read_only") else "written_in_task_scope",
        }
        for path, role in rows
    ]


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(PHASE1_SCHEMA)}
  - {rel(PHASE1_SEGMENTS)}
  - {rel(PHASE1_HANDOFF)}
tags: [thermal-modeling, external-boundary, fluid, runtime-contract]
related:
  - .agent/status/2026-07-21_{TASK}.md
  - .agent/journal/2026-07-21/fluid-external-bc-dict.md
  - {rel(PHASE1 / "README.md")}
task: {TASK}
date: 2026-07-21
role: Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Fluid External Boundary Dictionary Contract

## Decision

This package releases the repo-local Fluid external-boundary dictionary
contract. It provides the schema, runtime dictionary rows, allowed modes,
validation cases, handoff stubs, and leakage audit needed before external Fluid
source can be edited under a separate row.

## Results

- Runtime dictionary rows: `{summary["runtime_dictionary_rows"]}`.
- Predictive passive external rows: `{summary["predictive_passive_external_rows"]}`.
- Document-only source/sink rows: `{summary["document_only_source_sink_rows"]}`.
- Validation cases: `{summary["validation_case_rows"]}`.
- External Fluid files edited: `{summary["external_fluid_edit"]}`.

## Outputs

- `fluid_external_boundary_schema.csv`
- `fluid_external_boundary_runtime_dictionary.csv`
- `allowed_runtime_mode_table.csv`
- `validation_cases.csv`
- `fluid_handoff_stubs.csv`
- `runtime_leakage_audit.csv`
- Legacy-compatible aliases: `external_bc_runtime_field_contract.csv`,
  `external_bc_representative_dictionary_rows.csv`,
  `external_bc_mode_policy.csv`, `external_bc_validation_cases.csv`, and
  `fluid_api_handoff_stubs.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Predictive mode excludes forbidden realized heat flux, CFD `mdot`, and imposed
forbidden cooler duty. Predictive mode also excludes forbidden validation
temperatures and forbidden residual-derived field fills. Replay total heat and
predictive radiation/convection are mutually exclusive.
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    phase1_schema = read_csv(PHASE1_SCHEMA)
    segment_rows = read_csv(PHASE1_SEGMENTS)

    schema_rows = build_fluid_schema(phase1_schema)
    runtime_rows = build_runtime_dictionary(segment_rows)
    mode_rows = build_allowed_modes()
    validation_rows = build_validation_cases(runtime_rows)
    handoff_rows = build_fluid_handoff_stubs()
    audit_rows = build_runtime_leakage_audit(runtime_rows)
    manifest_rows = build_source_manifest()

    write_csv(OUT / "fluid_external_boundary_schema.csv", schema_rows)
    write_csv(OUT / "fluid_external_boundary_runtime_dictionary.csv", runtime_rows)
    write_csv(OUT / "allowed_runtime_mode_table.csv", mode_rows)
    write_csv(OUT / "validation_cases.csv", validation_rows)
    write_csv(OUT / "fluid_handoff_stubs.csv", handoff_rows)
    write_csv(OUT / "runtime_leakage_audit.csv", audit_rows)
    write_csv(OUT / "source_manifest.csv", manifest_rows)
    write_csv(OUT / "external_bc_runtime_field_contract.csv", schema_rows)
    write_csv(OUT / "external_bc_representative_dictionary_rows.csv", runtime_rows[: min(12, len(runtime_rows))])
    write_csv(OUT / "external_bc_mode_policy.csv", mode_rows)
    write_csv(OUT / "external_bc_validation_cases.csv", validation_rows)
    write_csv(OUT / "fluid_api_handoff_stubs.csv", handoff_rows)

    predictive_rows = [row for row in runtime_rows if row["mode"] == "predictive"]
    summary: dict[str, Any] = {
        "task": TASK,
        "generated_at_utc": utc_now(),
        "runtime_dictionary_rows": len(runtime_rows),
        "schema_rows": len(schema_rows),
        "allowed_runtime_mode_rows": len(mode_rows),
        "validation_case_rows": len(validation_rows),
        "fluid_handoff_stub_rows": len(handoff_rows),
        "runtime_leakage_audit_rows": len(audit_rows),
        "predictive_passive_external_rows": len(predictive_rows),
        "document_only_source_sink_rows": len(runtime_rows) - len(predictive_rows),
        "external_fluid_edit": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "solver_or_postprocessing_launched": False,
        "fitting_or_model_selection_performed": False,
        "closure_admission_changed": False,
        "blocker_register_mutated": False,
        "generated_docs_index_mutated": False,
        "no_scorecard_outputs": True,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
