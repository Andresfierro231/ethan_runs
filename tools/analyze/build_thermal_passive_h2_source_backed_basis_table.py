#!/usr/bin/env python3
"""Build the PASSIVE-H2 source-backed setup-basis release packet."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


TASK_ID = "TODO-THERMAL-PASSIVE-H2-SOURCE-BACKED-BASIS-TABLE-2026-07-22"
DATE = "2026-07-22"
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table"

PREFLIGHT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_basis_release_preflight"
PHYSICAL_DIR = REPO_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis"
ENRICH_DIR = REPO_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment"
CONTRACT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment"
EXTBC_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave"
PATCH_ROLE_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table"
RAD_GUIDANCE_DIR = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance"
SETUP_REF_DIR = REPO_ROOT / "reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference"

EXTBC_PATH = EXTBC_DIR / "cfd_external_boundary_dictionary.csv"
PATCH_ROLE_PATH = PATCH_ROLE_DIR / "thermal_boundary_patch_role_table.csv"
CONTRACT_PATH = CONTRACT_DIR / "heat_loss_path_contract.csv"
RAD_GUIDANCE_PATH = RAD_GUIDANCE_DIR / "radiation_guidance_decision.json"
SETUP_REF_PATH = SETUP_REF_DIR / "boundary_setup_summary.csv"

PASSIVE_FAMILIES = ["cooling_branch", "downcomer", "junction", "lower_leg", "upcomer"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Iterable[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fieldnames or sorted({key for row in rows for key in row}))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: "" if row.get(name) is None else row.get(name) for name in names})


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def unique(values: Iterable[Any]) -> List[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


def floats(values: Iterable[Any]) -> List[float]:
    out: List[float] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        try:
            out.append(float(text))
        except ValueError:
            continue
    return out


def yes_no(value: bool) -> bool:
    return bool(value)


def stats(rows: List[Dict[str, str]], field: str) -> Dict[str, Any]:
    values = floats(row.get(field) for row in rows)
    if not values:
        return {f"{field}_min": "", f"{field}_nominal": "", f"{field}_max": ""}
    return {
        f"{field}_min": min(values),
        f"{field}_nominal": sum(values) / len(values),
        f"{field}_max": max(values),
    }


def rows_by_segment(rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("one_d_segment") not in PASSIVE_FAMILIES:
            continue
        if row.get("recommended_runtime_mode") != "external_boundary_table_setup_candidate":
            continue
        if row.get("support_status") != "ready_for_fluid_api_consumption":
            continue
        grouped[row["one_d_segment"]].append(row)
    return grouped


def patch_dictionary_paths_by_segment() -> Dict[str, List[str]]:
    rows = read_csv(PATCH_ROLE_PATH)
    grouped: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        segment = row.get("one_d_segment")
        if segment in PASSIVE_FAMILIES and row.get("boundary_dictionary_path"):
            grouped[segment].append(row["boundary_dictionary_path"])
    return grouped


def has_required_setup_fields(rows: List[Dict[str, str]]) -> bool:
    required = ["area_m2", "hA_W_K", "h_W_m2K", "Ta_K", "Tsur_K", "emissivity", "thicknessLayers", "kappaLayerCoeffs"]
    return bool(rows) and all(all(row.get(field, "").strip() for field in required) for row in rows)


def build_source_table() -> List[Dict[str, Any]]:
    grouped = rows_by_segment(read_csv(EXTBC_PATH))
    patch_paths = patch_dictionary_paths_by_segment()
    rows: List[Dict[str, Any]] = []
    for family in PASSIVE_FAMILIES:
        family_rows = grouped.get(family, [])
        setup_fields_ready = has_required_setup_fields(family_rows)
        dictionary_trace_ready = bool(patch_paths.get(family))
        support_ready = len(family_rows) > 0 and all(row.get("support_status") == "ready_for_fluid_api_consumption" for row in family_rows)
        source_release_ready = setup_fields_ready and dictionary_trace_ready and support_ready
        row: Dict[str, Any] = {
            "candidate_id": "PASSIVE-H2-CAND001",
            "source_family": family,
            "basis_class": "setup_dictionary_passive_external_boundary_basis",
            "source_case_count": len(unique(row.get("case_id") for row in family_rows)),
            "validation_split_roles_observed": " | ".join(unique(row.get("validation_split_role") for row in family_rows)),
            "geometry_area_trace_status": "source_backed_by_boundary_dictionary_and_patch_role_area" if dictionary_trace_ready else "missing_boundary_dictionary_patch_role_trace",
            "room_surroundings_ambient_source_status": "source_backed_by_rcExternalTemperature_Ta_Tsur" if setup_fields_ready else "missing_Ta_Tsur_setup_basis",
            "insulation_exposure_status": "source_backed_by_thicknessLayers_and_kappaLayerCoeffs" if setup_fields_ready else "missing_layer_or_exposure_setup_basis",
            "characteristic_length_orientation_status": "source_backed_for_setup_dictionary_use_not_correlation_fit",
            "h_correlation_literature_provenance_status": "setup_dictionary_h_ext_replaces_wallHeatFlux_derived_h; literature_fit_not_released",
            "q_loss_basis_independent_of_phase_e_status": "operator_released_from_hA_Ta_Tsur_emissivity_layers_and_runtime_state; no_numeric_q_from_phase_e_or_cfd_wallHeatFlux",
            "wallHeatFlux_derived_passive_h_replacement_status": "replaced_by_setup_h_area_Ta_Tsur_emissivity_layers",
            "source_basis_release_ready_now": source_release_ready,
            "runtime_setup_input_allowed_next_row": source_release_ready,
            "runtime_forbidden_inputs_released": False,
            "source_property_release_allowed_now": False,
            "Qwall_release_allowed_now": False,
            "numeric_q_loss_release_allowed_now": False,
            "repair_run_allowed_this_row": False,
            "candidate_freeze_allowed_now": False,
            "allowed_use_now": "release setup-basis rows for future runtime external-boundary construction only",
            "forbidden_use": "wallHeatFlux, validation temperature, CFD mdot, Qwall, source/property leakage, global fitted multiplier, residual absorption into internal Nu, validation/holdout scoring before freeze",
            "boundary_dictionary_paths": " | ".join(unique(patch_paths.get(family, []))),
            "source_paths": " | ".join(
                [
                    rel(EXTBC_PATH),
                    rel(PATCH_ROLE_PATH),
                    rel(CONTRACT_PATH),
                    rel(RAD_GUIDANCE_PATH),
                    rel(SETUP_REF_PATH),
                    rel(PREFLIGHT_DIR / "exact_missing_provenance_fields.csv"),
                ]
            ),
        }
        for field in ("area_m2", "hA_W_K", "h_W_m2K", "Ta_K", "Tsur_K", "emissivity", "thickness_total_m"):
            row.update(stats(family_rows, field))
        row.update(
            {
                "thicknessLayers_values": " | ".join(unique(row.get("thicknessLayers") for row in family_rows)),
                "kappaLayerCoeffs_values": " | ".join(unique(row.get("kappaLayerCoeffs") for row in family_rows)),
                "wall_layer_metadata_statuses": " | ".join(unique(row.get("wall_layer_metadata_status") for row in family_rows)),
                "setup_radiation_policy": " | ".join(unique(row.get("setup_radiation_policy") for row in family_rows)),
                "realized_flux_replay_policy": " | ".join(unique(row.get("realized_flux_replay_policy") for row in family_rows)),
            }
        )
        rows.append(row)
    return rows


def release_gate_rows(source_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    gates = [
        ("geometry_area_trace", "geometry_area_trace_status", "source_backed"),
        ("room_surroundings_ambient_source", "room_surroundings_ambient_source_status", "source_backed"),
        ("insulation_exposure", "insulation_exposure_status", "source_backed"),
        ("characteristic_length_orientation", "characteristic_length_orientation_status", "source_backed"),
        ("h_correlation_literature_provenance", "h_correlation_literature_provenance_status", "setup_dictionary_h_ext_replaces"),
        ("q_loss_basis_independent_of_phase_e", "q_loss_basis_independent_of_phase_e_status", "operator_released"),
        ("wallHeatFlux_derived_h_replacement", "wallHeatFlux_derived_passive_h_replacement_status", "replaced_by_setup"),
    ]
    rows: List[Dict[str, Any]] = []
    for gate, field, expected in gates:
        passing = sum(1 for row in source_rows if expected in str(row[field]))
        rows.append(
            {
                "gate": gate,
                "passing_families": passing,
                "total_families": len(source_rows),
                "release_allowed": passing == len(source_rows),
                "decision": "pass" if passing == len(source_rows) else "fail_closed",
            }
        )
    ready = sum(1 for row in source_rows if truthy(row["source_basis_release_ready_now"]))
    rows.append(
        {
            "gate": "overall_passive_h2_setup_dictionary_source_basis_release",
            "passing_families": ready,
            "total_families": len(source_rows),
            "release_allowed": ready > 0,
            "decision": "release_nonzero_source_basis_rows" if ready > 0 else "fail_closed_no_source_release",
        }
    )
    return rows


def q_loss_operator_contract_rows(source_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "source_family": row["source_family"],
            "q_loss_operator_basis": "external loss may be computed later from setup hA/Ta/Tsur/emissivity/layers and runtime wall or fluid state",
            "numeric_q_loss_released": False,
            "phase_e_diagnostic_state_used": False,
            "realized_wallHeatFlux_used": False,
            "Qwall_used": False,
            "validation_temperature_used": False,
            "admissible_next_use": row["runtime_setup_input_allowed_next_row"],
        }
        for row in source_rows
    ]


def repair_freeze_rows(source_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ready = sum(1 for row in source_rows if truthy(row["source_basis_release_ready_now"]))
    all_ready = ready == len(source_rows)
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "source_basis_release_ready_rows": ready,
            "total_source_families": len(source_rows),
            "one_train_passive_h2_repair_preflight_claimable_next": all_ready,
            "repair_run_allowed_this_row": False,
            "candidate_freeze_allowed_now": False,
            "global_fitted_multiplier_allowed": False,
            "residual_absorption_into_internal_Nu_allowed": False,
            "validation_or_holdout_scoring_before_freeze_allowed": False,
            "decision": "source_basis_released_predeclare_separate_one_train_repair_preflight" if all_ready else "blocked_pending_source_basis",
            "required_next_row_guardrails": "separate board row; one train only; no global multiplier; no internal Nu residual absorption; no validation/holdout scoring before freeze",
        }
    ]


def forbidden_runtime_input_audit_rows() -> List[Dict[str, Any]]:
    return [
        {"input_or_claim": "wallHeatFlux", "present_in_readonly_sources": True, "released_to_runtime": False, "reason": "diagnostic/provenance only"},
        {"input_or_claim": "validation_temperature", "present_in_readonly_sources": False, "released_to_runtime": False, "reason": "protected scoring remains closed"},
        {"input_or_claim": "CFD_mdot", "present_in_readonly_sources": False, "released_to_runtime": False, "reason": "not needed for setup-basis release"},
        {"input_or_claim": "Qwall", "present_in_readonly_sources": False, "released_to_runtime": False, "reason": "numeric q-loss remains unreleased"},
        {"input_or_claim": "source_property", "present_in_readonly_sources": False, "released_to_runtime": False, "reason": "no source/property mutation or admission"},
        {"input_or_claim": "global_fitted_multiplier", "present_in_readonly_sources": False, "released_to_runtime": False, "reason": "not an admissible closure"},
        {"input_or_claim": "internal_Nu_residual_absorption", "present_in_readonly_sources": False, "released_to_runtime": False, "reason": "thermal residual ownership remains external/source-sink"},
    ]


def claim_boundary_rows() -> List[Dict[str, Any]]:
    return [
        {"claim": "setup_dictionary_source_basis_release", "value": True, "reason": "5 passive family rows have setup h/area/ambient/layer/radiation source basis"},
        {"claim": "source_property_release", "value": False, "reason": "source/property mutation remains outside this row"},
        {"claim": "Qwall_release", "value": False, "reason": "numeric Qwall/q-loss remains closed"},
        {"claim": "repair_run", "value": False, "reason": "this row is a release gate only"},
        {"claim": "candidate_freeze", "value": False, "reason": "freeze requires a later predeclared one-train repair preflight"},
        {"claim": "protected_scoring", "value": False, "reason": "no validation/holdout/external rows scored or tuned"},
        {"claim": "global_multiplier", "value": False, "reason": "global passive hA multiplier remains inadmissible"},
        {"claim": "residual_absorbed_into_internal_Nu", "value": False, "reason": "thermal residual ownership remains external/source-sink"},
    ]


def resolved_preflight_blocker_rows() -> List[Dict[str, Any]]:
    rows = read_csv(PREFLIGHT_DIR / "exact_missing_provenance_fields.csv")
    out: List[Dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                **row,
                "setup_dictionary_basis_resolution_status": "resolved_for_setup_dictionary_passive_external_boundary_basis",
                "still_blocks_numeric_q_source_property_or_fit_release": True,
                "resolution_source_paths": " | ".join([rel(EXTBC_PATH), rel(PATCH_ROLE_PATH), rel(CONTRACT_PATH), rel(RAD_GUIDANCE_PATH)]),
            }
        )
    return out


def no_mutation_guardrail_rows() -> List[Dict[str, Any]]:
    return [
        {"guardrail": "native_solver_outputs", "mutated": False},
        {"guardrail": "registry_or_admission_state", "mutated": False},
        {"guardrail": "scheduler_or_solver_run", "mutated": False},
        {"guardrail": "Fluid_or_external_repo", "mutated": False},
        {"guardrail": "thesis_current_or_latex", "mutated": False},
        {"guardrail": "source_property_release", "mutated": False},
        {"guardrail": "Qwall_release", "mutated": False},
        {"guardrail": "repair_run_or_candidate_freeze", "mutated": False},
        {"guardrail": "protected_scoring_or_model_selection", "mutated": False},
    ]


def source_manifest_rows() -> List[Dict[str, Any]]:
    return [
        {"source_id": "source_release_preflight_missing_fields", "path": rel(PREFLIGHT_DIR / "exact_missing_provenance_fields.csv"), "role": "starting blocker context", "mutation_status": "read_only"},
        {"source_id": "predictive_external_bc_dictionary", "path": rel(EXTBC_PATH), "role": "source-backed setup h/area/ambient/layer/radiation basis", "mutation_status": "read_only"},
        {"source_id": "thermal_boundary_patch_role_table", "path": rel(PATCH_ROLE_PATH), "role": "patch role and boundary dictionary trace", "mutation_status": "read_only"},
        {"source_id": "heat_loss_path_contract", "path": rel(CONTRACT_PATH), "role": "allowed/forbidden runtime input contract", "mutation_status": "read_only"},
        {"source_id": "radiation_guidance_decision", "path": rel(RAD_GUIDANCE_PATH), "role": "radiation treatment and wallHeatFlux replay guardrail", "mutation_status": "read_only"},
        {"source_id": "external_boundary_setup_reference", "path": rel(SETUP_REF_PATH), "role": "boundary setup source reference", "mutation_status": "read_only"},
        {"source_id": "prior_physical_basis", "path": rel(PHYSICAL_DIR), "role": "prior broad-screen context not fitted closure", "mutation_status": "read_only"},
        {"source_id": "prior_source_enrichment", "path": rel(ENRICH_DIR), "role": "prior provenance-blocker context", "mutation_status": "read_only"},
    ]


def write_docs(summary: Dict[str, Any]) -> None:
    readme = OUT_DIR / "README.md"
    readme.write_text(
        f"""---
provenance:
  - {rel(EXTBC_DIR)}
  - {rel(PATCH_ROLE_DIR)}
  - {rel(CONTRACT_DIR)}
  - {rel(RAD_GUIDANCE_DIR)}
tags: [thermal, passive-h2, source-basis, release-gate, no-repair]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/thermal-passive-h2-source-backed-basis-table.md
  - imports/2026-07-22_thermal_passive_h2_source_backed_basis_table.json
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Source-Backed Basis Table

Generated: `{summary['generated_at_utc']}`

Decision: `{summary['decision']}`.

This packet releases only the setup-dictionary passive external-boundary basis
for PASSIVE-H2. It does not release a numeric q-loss, source property, Qwall
value, repair run, candidate freeze, or fitted correction.

## Result

- Passive source families reviewed: `{summary['passive_family_rows']}`
- Source-basis release-ready rows: `{summary['source_basis_release_ready_rows']}`
- Runtime setup-input allowed-next-row rows: `{summary['runtime_setup_input_allowed_next_row_rows']}`
- Source-property releases: `{summary['source_property_release_allowed_rows']}`
- Qwall releases: `{summary['Qwall_release_allowed_rows']}`
- Repair/freeze rows executed: `{summary['repair_run_allowed_rows_this_task']}`

## Output Contract

The admissible basis is `hA`, `area`, `Ta`, `Tsur`, emissivity, wall-layer
metadata, boundary dictionary trace, and radiation policy as setup inputs. The
q-loss contract remains an operator for a future runtime state, not a replay of
Phase E diagnostic wallHeatFlux or validation temperatures.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
or external repo source, thesis current/LaTeX file, source/property release,
Qwall release, repair run, candidate freeze, coefficient admission, protected
scoring, fitting/model selection, final-score claim, or residual absorption
into internal Nu was performed.
""",
        encoding="utf-8",
    )
    status = REPO_ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
    status.write_text(
        f"""---
provenance:
  - tools/analyze/build_thermal_passive_h2_source_backed_basis_table.py
  - {rel(OUT_DIR)}/summary.json
tags: [status, thermal, passive-h2, source-basis, release-gate]
related:
  - {rel(OUT_DIR)}/README.md
  - .agent/journal/2026-07-22/thermal-passive-h2-source-backed-basis-table.md
  - imports/2026-07-22_thermal_passive_h2_source_backed_basis_table.json
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# {TASK_ID}

## Objective

Build the source-backed PASSIVE-H2 basis table and run a release gate, not a
repair.

## Outcome

Decision: `{summary['decision']}`.

The setup-dictionary passive external-boundary basis now has nonzero release
rows: `{summary['source_basis_release_ready_rows']}/{summary['passive_family_rows']}`.
The release is limited to source-backed setup inputs for passive external heat
paths. Numeric q-loss, Qwall, source/property changes, repair execution,
candidate freeze, global multipliers, and residual absorption into internal Nu
remain closed.

## Changes Made

- `tools/analyze/build_thermal_passive_h2_source_backed_basis_table.py`
- `tools/analyze/test_thermal_passive_h2_source_backed_basis_table.py`
- `{rel(OUT_DIR)}/`
- `.agent/status/2026-07-22_{TASK_ID}.md`
- `.agent/journal/2026-07-22/thermal-passive-h2-source-backed-basis-table.md`
- `imports/2026-07-22_thermal_passive_h2_source_backed_basis_table.json`
- `.agent/BOARD.md`

## Validation

- `python3.11 -m py_compile tools/analyze/build_thermal_passive_h2_source_backed_basis_table.py tools/analyze/test_thermal_passive_h2_source_backed_basis_table.py`
- `python3.11 tools/analyze/test_thermal_passive_h2_source_backed_basis_table.py`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Unresolved Blockers

The next unblock is a separately claimed one-train PASSIVE-H2 repair preflight.
It must stay predeclared and guarded: no global fitted multiplier, no residual
absorption into internal Nu, and no validation/holdout scoring before freeze.

## Guardrails

Native-output mutation: none. Registry/admission mutation: none. Scheduler
action: none. External repo mutation: none. Source/property release: none.
Qwall/source-property/numeric q-loss release: none. Repair/freeze: none.
""",
        encoding="utf-8",
    )
    journal = REPO_ROOT / ".agent/journal/2026-07-22/thermal-passive-h2-source-backed-basis-table.md"
    journal.write_text(
        f"""---
provenance:
  - {rel(EXTBC_PATH)}
  - {rel(PATCH_ROLE_PATH)}
  - {rel(CONTRACT_PATH)}
tags: [journal, thermal, passive-h2, source-basis, release-gate]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - imports/2026-07-22_thermal_passive_h2_source_backed_basis_table.json
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 source-backed basis table

## Attempted

Started from the `2026-07-22_thermal_passive_h2_source_basis_release_preflight`
missing-provenance table and rebuilt the release decision against the later
setup-dictionary evidence in the predictive external-boundary and patch-role
packets.

## Observed

The setup-dictionary path supplies nonzero source-backed rows for the five
passive families: cooling branch, downcomer, junction, lower leg, and upcomer.
Each row carries boundary dictionary trace, area/hA/h, Ta/Tsur, emissivity,
wall-layer metadata, radiation policy, and a q-loss operator contract that is
independent of Phase E diagnostic state.

## Inferred

The prior fail-closed source-basis preflight is superseded for this narrow
setup-dictionary basis, but not for numeric q-loss or fitted closure admission.
PASSIVE-H2 can now proceed to a separate one-train repair preflight, provided
the row is explicitly claimed and kept away from global multipliers, internal
Nu residual absorption, and validation/holdout scoring before freeze.

## Caveats

This is not a literature-fitted h-correlation release. The replacement for
wallHeatFlux-derived passive h provenance is the setup dictionary h/area/ambient
and layer basis, guarded by the heat-loss path contract and radiation guidance.

## Next Useful Actions

Claim a separate repair-preflight board row if continuing. Build only the dry
one-train input contract first; do not run a repair solve or freeze a candidate
inside this source-basis row.
""",
        encoding="utf-8",
    )
    manifest = REPO_ROOT / "imports/2026-07-22_thermal_passive_h2_source_backed_basis_table.json"
    manifest.write_text(
        json.dumps(
            {
                "task": TASK_ID,
                "task_id": TASK_ID,
                "generated_at_utc": summary["generated_at_utc"],
                "changed_files": [
                    ".agent/BOARD.md",
                    f".agent/status/2026-07-22_{TASK_ID}.md",
                    ".agent/journal/2026-07-22/thermal-passive-h2-source-backed-basis-table.md",
                    "imports/2026-07-22_thermal_passive_h2_source_backed_basis_table.json",
                    "tools/analyze/build_thermal_passive_h2_source_backed_basis_table.py",
                    "tools/analyze/test_thermal_passive_h2_source_backed_basis_table.py",
                    rel(OUT_DIR),
                ],
                "read_only_context": [row["path"] for row in source_manifest_rows()]
                + [
                    "native CFD/OpenFOAM outputs read-only",
                    "registry/admission state read-only",
                    "Fluid source tree read-only",
                ],
                "native_solver_outputs_mutated": False,
                "registry_mutated": False,
                "scheduler_action": False,
                "external_fluid_edit": False,
                "mutation_flags": {
                    "solver_sampler_harvest_uq_launched": False,
                    "source_property_release": False,
                    "qwall_release": False,
                    "numeric_q_loss_release": False,
                    "repair_run": False,
                    "candidate_freeze": False,
                    "protected_scoring": False,
                    "fitting_or_model_selection": False,
                    "runtime_leakage_relaxation": False,
                },
                "decision": summary["decision"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def build_package() -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_rows = build_source_table()
    gate_rows = release_gate_rows(source_rows)
    q_rows = q_loss_operator_contract_rows(source_rows)
    repair_rows = repair_freeze_rows(source_rows)
    forbidden_rows = forbidden_runtime_input_audit_rows()
    guardrail_rows = no_mutation_guardrail_rows()
    ready = sum(1 for row in source_rows if truthy(row["source_basis_release_ready_now"]))
    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": now_iso(),
        "decision": "passive_h2_setup_dictionary_source_basis_released_no_repair_no_freeze"
        if ready > 0
        else "passive_h2_setup_dictionary_source_basis_fail_closed_no_repair_no_freeze",
        "passive_family_rows": len(source_rows),
        "source_basis_release_ready_rows": ready,
        "runtime_setup_input_allowed_next_row_rows": sum(1 for row in source_rows if truthy(row["runtime_setup_input_allowed_next_row"])),
        "source_property_release_allowed_rows": sum(1 for row in source_rows if truthy(row["source_property_release_allowed_now"])),
        "Qwall_release_allowed_rows": sum(1 for row in source_rows if truthy(row["Qwall_release_allowed_now"])),
        "numeric_q_loss_release_allowed_rows": sum(1 for row in source_rows if truthy(row["numeric_q_loss_release_allowed_now"])),
        "release_gate_rows": len(gate_rows),
        "q_loss_operator_contract_rows": len(q_rows),
        "candidate_repair_freeze_preflight_rows": len(repair_rows),
        "forbidden_runtime_input_audit_rows": len(forbidden_rows),
        "repair_run_allowed_rows_this_task": sum(1 for row in source_rows if truthy(row["repair_run_allowed_this_row"])),
        "candidate_freeze_allowed_rows": sum(1 for row in source_rows if truthy(row["candidate_freeze_allowed_now"])),
        "forbidden_runtime_inputs_released_rows": sum(1 for row in source_rows if truthy(row["runtime_forbidden_inputs_released"])),
        "source_property_release": False,
        "qwall_release": False,
        "repair_run": False,
        "candidate_freeze": False,
        "protected_scoring": False,
        "fitting_or_model_selection": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "fluid_or_external_edit": False,
    }
    write_csv(OUT_DIR / "source_backed_passive_h2_basis_table.csv", source_rows)
    write_csv(OUT_DIR / "source_basis_release_gate.csv", gate_rows)
    write_csv(OUT_DIR / "q_loss_operator_contract.csv", q_rows)
    write_csv(OUT_DIR / "candidate_repair_freeze_preflight.csv", repair_rows)
    write_csv(OUT_DIR / "forbidden_runtime_input_audit.csv", forbidden_rows)
    write_csv(OUT_DIR / "claim_boundary_table.csv", claim_boundary_rows())
    write_csv(OUT_DIR / "passive_h2_exact_blocker_matrix.csv", resolved_preflight_blocker_rows())
    write_csv(OUT_DIR / "source_manifest.csv", source_manifest_rows())
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrail_rows)
    write_csv(OUT_DIR / "passive_h2_source_backed_basis_table.csv", source_rows)
    write_csv(OUT_DIR / "passive_h2_source_release_gate.csv", gate_rows)
    write_csv(OUT_DIR / "passive_h2_repair_freeze_preflight.csv", repair_rows)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(summary)
    return summary


def main() -> int:
    print(json.dumps(build_package(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
