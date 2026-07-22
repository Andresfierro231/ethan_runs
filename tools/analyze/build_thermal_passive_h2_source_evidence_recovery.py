#!/usr/bin/env python3
"""Build a source-evidence recovery packet for passive_H2."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


TASK_ID = "TODO-THERMAL-PASSIVE-H2-SOURCE-EVIDENCE-RECOVERY-2026-07-22"
DATE = "2026-07-22"
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_evidence_recovery"

SOURCE_BASIS_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table"
SETUP_UQ_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution"
EXTBC_PATH = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv"
PATCH_ROLE_PATH = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv"
HEAT_LOSS_CONTRACT_PATH = REPO_ROOT / "work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv"
RADIATION_GUIDANCE_PATH = REPO_ROOT / "work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/radiation_guidance_decision.json"
SETUP_REF_PATH = REPO_ROOT / "reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/boundary_setup_summary.csv"
GEOMETRY_REF_PATH = REPO_ROOT / "reference/geometry_reference.md"

SOURCE_TABLE_PATH = SOURCE_BASIS_DIR / "source_backed_passive_h2_basis_table.csv"
RELEASE_GATE_PATH = SOURCE_BASIS_DIR / "source_basis_release_gate.csv"
Q_LOSS_CONTRACT_PATH = SOURCE_BASIS_DIR / "q_loss_operator_contract.csv"
SOURCE_SUMMARY_PATH = SOURCE_BASIS_DIR / "summary.json"
SETUP_UQ_SUMMARY_PATH = SETUP_UQ_DIR / "summary.json"
SETUP_UQ_RUNTIME_INPUT_PATH = SETUP_UQ_DIR / "runtime_input_manifest.csv"
SETUP_UQ_HEAT_SENSITIVITY_PATH = SETUP_UQ_DIR / "mdot_heat_sensitivity.csv"

PASSIVE_FAMILIES = ["cooling_branch", "downcomer", "junction", "lower_leg", "upcomer"]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def falsey(value: Any) -> bool:
    return str(value).strip().lower() in {"false", "0", "no", ""}


def unique(values: Iterable[Any]) -> List[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


def rows_for_family(rows: List[Dict[str, str]], family: str) -> List[Dict[str, str]]:
    return [row for row in rows if row.get("source_family") == family]


def field_source_paths(*paths: Path) -> str:
    return " | ".join(rel(path) for path in paths)


def build_family_matrix(source_rows: List[Dict[str, str]], q_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    q_by_family = {row["source_family"]: row for row in q_rows}
    rows: List[Dict[str, Any]] = []
    for family in PASSIVE_FAMILIES:
        source = rows_for_family(source_rows, family)[0]
        q_contract = q_by_family[family]
        wall_layer_status = source["wall_layer_metadata_statuses"]
        has_junction_caveat = "mixed" in wall_layer_status or "no_wall_layer_metadata" in wall_layer_status
        missing = [
            "model-predicted wall or fluid state is needed before numeric q_loss",
            "independent literature/correlation admission is not released",
            "source/property and Qwall release gates remain closed",
            "repair/freeze requires a separate predeclared row",
        ]
        if has_junction_caveat:
            missing.append("mixed junction/stub wall-layer metadata must remain a caveat")
        rows.append(
            {
                "candidate_id": source["candidate_id"],
                "source_family": family,
                "source_case_count": source["source_case_count"],
                "validation_split_roles_observed": source["validation_split_roles_observed"],
                "area_m2_nominal": source["area_m2_nominal"],
                "h_W_m2K_nominal": source["h_W_m2K_nominal"],
                "hA_W_K_nominal": source["hA_W_K_nominal"],
                "Ta_K_nominal": source["Ta_K_nominal"],
                "Tsur_K_nominal": source["Tsur_K_nominal"],
                "emissivity_nominal": source["emissivity_nominal"],
                "wall_layer_metadata_statuses": wall_layer_status,
                "source_basis_release_ready_now": truthy(source["source_basis_release_ready_now"]),
                "runtime_setup_input_allowed_next_row": truthy(source["runtime_setup_input_allowed_next_row"]),
                "q_loss_operator_admissible_next_use": truthy(q_contract["admissible_next_use"]),
                "area_geometry_source_backed": "source_backed_by_boundary_dictionary" in source["geometry_area_trace_status"],
                "ambient_surrounding_source_backed": "source_backed_by_rcExternalTemperature" in source["room_surroundings_ambient_source_status"],
                "layers_kappa_source_backed": "source_backed_by_thicknessLayers" in source["insulation_exposure_status"],
                "h_setup_dictionary_source_backed": "setup_dictionary_h_ext_replaces" in source["h_correlation_literature_provenance_status"],
                "h_literature_correlation_admitted": False,
                "numeric_q_loss_released": False,
                "source_property_release_allowed": False,
                "Qwall_release_allowed": False,
                "repair_run_allowed_this_task": False,
                "candidate_freeze_allowed": False,
                "realized_wallHeatFlux_runtime_input_allowed": False,
                "validation_temperature_runtime_input_allowed": False,
                "evidence_status": "setup_source_backed_runtime_operator_ready_no_numeric_release",
                "remaining_missing_evidence": " | ".join(missing),
                "primary_source_paths": source["source_paths"],
                "interpretation": "This family can supply setup-dictionary passive external-boundary inputs to a no-leak runtime operator, but it cannot yet supply a numeric q-loss, source/property value, Qwall value, repair, freeze, or publication score.",
            }
        )
    return rows


def build_field_strength(source_rows: List[Dict[str, str]], release_gate_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    gates = {row["gate"]: row for row in release_gate_rows}

    def gate_count(gate: str) -> str:
        row = gates[gate]
        return f"{row['passing_families']}/{row['total_families']}"

    return [
        {
            "field_or_issue": "geometry_area",
            "current_status": "source_backed_setup_input",
            "source_backed_now": True,
            "passing_family_count": gate_count("geometry_area_trace"),
            "allowed_use_now": "runtime setup dictionary area/coverage basis",
            "not_allowed_use": "source-property release or fitted area correction",
            "missing_evidence_or_caveat": "No additional evidence needed for setup-basis use; source/property admission still needs a separate candidate gate.",
            "primary_source_paths": field_source_paths(SOURCE_TABLE_PATH, PATCH_ROLE_PATH, GEOMETRY_REF_PATH),
            "scientific_interpretation": "Area is backed by boundary dictionary and patch-role traces, so passive_H2 is no longer relying on an inferred wallHeatFlux-derived area.",
        },
        {
            "field_or_issue": "ambient_and_surrounding_temperature",
            "current_status": "source_backed_setup_input",
            "source_backed_now": True,
            "passing_family_count": gate_count("room_surroundings_ambient_source"),
            "allowed_use_now": "Ta/Tsur setup inputs for a future runtime heat-loss operator",
            "not_allowed_use": "validation temperature or held-out temperature replay",
            "missing_evidence_or_caveat": "Future run must use declared setup ambient/surrounding fields only.",
            "primary_source_paths": field_source_paths(SOURCE_TABLE_PATH, EXTBC_PATH, SETUP_REF_PATH),
            "scientific_interpretation": "Room/surroundings state is source-backed through rcExternalTemperature metadata rather than protected observed temperatures.",
        },
        {
            "field_or_issue": "wall_layers_and_kappa",
            "current_status": "source_backed_setup_input_with_junction_caveat",
            "source_backed_now": True,
            "passing_family_count": gate_count("insulation_exposure"),
            "allowed_use_now": "setup insulation/exposure metadata for passive external boundaries",
            "not_allowed_use": "global 1D insulation scalar as paper-grade reconstruction",
            "missing_evidence_or_caveat": "Junction/stub rows include mixed h/layer/no-layer metadata, so publication claims must keep family-level setup-basis wording.",
            "primary_source_paths": field_source_paths(SOURCE_TABLE_PATH, EXTBC_PATH, SETUP_REF_PATH, GEOMETRY_REF_PATH),
            "scientific_interpretation": "The main passive branches have the 0/T layer basis needed for setup use; mixed junction/stub detail is a caveat, not a repair/freeze blocker by itself.",
        },
        {
            "field_or_issue": "h_ext_and_hA",
            "current_status": "source_backed_setup_dictionary_value_not_correlation_fit",
            "source_backed_now": True,
            "passing_family_count": gate_count("h_correlation_literature_provenance"),
            "allowed_use_now": "setup dictionary h_ext/hA consumption",
            "not_allowed_use": "publication claim that a general external-convection correlation has been admitted",
            "missing_evidence_or_caveat": "Independent literature/correlation admission remains unreleased.",
            "primary_source_paths": field_source_paths(SOURCE_TABLE_PATH, HEAT_LOSS_CONTRACT_PATH),
            "scientific_interpretation": "This replaces wallHeatFlux-derived passive h with source-dictionary h/hA, but it does not prove a portable h correlation.",
        },
        {
            "field_or_issue": "emissivity_and_radiation_semantics",
            "current_status": "source_backed_setup_input_and_double_count_guardrail",
            "source_backed_now": True,
            "passing_family_count": "5/5",
            "allowed_use_now": "forward-model radiation from emissivity/Tsur when the runtime operator owns the surface state",
            "not_allowed_use": "adding separate radiation correction to realized CFD wallHeatFlux",
            "missing_evidence_or_caveat": "Radiation-on sensitivity can be studied only as setup-legal forward modeling.",
            "primary_source_paths": field_source_paths(SOURCE_TABLE_PATH, RADIATION_GUIDANCE_PATH, SETUP_REF_PATH, SETUP_UQ_RUNTIME_INPUT_PATH),
            "scientific_interpretation": "Radiation metadata is available for forward modeling; realized wallHeatFlux remains diagnostic and must not receive an extra correction.",
        },
        {
            "field_or_issue": "q_loss_operator",
            "current_status": "operator_released_for_future_runtime_state",
            "source_backed_now": True,
            "passing_family_count": gate_count("q_loss_basis_independent_of_phase_e"),
            "allowed_use_now": "compute external loss later from hA/Ta/Tsur/emissivity/layers and predicted runtime wall or fluid state",
            "not_allowed_use": "numeric q replay from Phase E, wallHeatFlux, CFD mdot, or validation temperatures",
            "missing_evidence_or_caveat": "Needs a runtime state produced by the model before numeric heat loss can be evaluated.",
            "primary_source_paths": field_source_paths(Q_LOSS_CONTRACT_PATH, SOURCE_TABLE_PATH, SETUP_UQ_RUNTIME_INPUT_PATH),
            "scientific_interpretation": "The operator path is source-backed; the scalar heat-loss value is intentionally not released.",
        },
        {
            "field_or_issue": "train_only_setup_uq_smoke",
            "current_status": "supporting_runtime_legality_smoke_complete_no_release",
            "source_backed_now": True,
            "passing_family_count": "33/33 variants accepted",
            "allowed_use_now": "evidence that setup-legal external hA/radiation/ambient variations can execute without protected runtime inputs",
            "not_allowed_use": "score, candidate freeze, source/property release, or fitted multiplier",
            "missing_evidence_or_caveat": "Smoke is not a passive_H2 numeric-q release and residual-owner rows remain diagnostic.",
            "primary_source_paths": field_source_paths(SETUP_UQ_SUMMARY_PATH, SETUP_UQ_RUNTIME_INPUT_PATH, SETUP_UQ_HEAT_SENSITIVITY_PATH),
            "scientific_interpretation": "The downstream workflow can perturb setup-legal heat-loss inputs, but scientific admission remains closed.",
        },
        {
            "field_or_issue": "numeric_passive_heat_loss",
            "current_status": "not_released",
            "source_backed_now": False,
            "passing_family_count": "0/5",
            "allowed_use_now": "diagnostic discussion only",
            "not_allowed_use": "runtime source term, paper-grade heat-loss number, Qwall/source-property release",
            "missing_evidence_or_caveat": "Requires no-leak runtime operator evaluation, train-only sensitivity, same-QOI uncertainty, and release gate.",
            "primary_source_paths": field_source_paths(SOURCE_SUMMARY_PATH, Q_LOSS_CONTRACT_PATH),
            "scientific_interpretation": "This is the main remaining evidence gap: passive_H2 is source-backed as a setup basis, not as an admitted heat-loss closure.",
        },
    ]


def build_missing_evidence() -> List[Dict[str, Any]]:
    return [
        {
            "missing_evidence_id": "M01",
            "item": "model_predicted_runtime_wall_or_fluid_state",
            "blocks": "numeric_q_loss_release; source/property release; repair/freeze",
            "why_missing": "The released operator deliberately needs a future runtime state; Phase E wallHeatFlux and validation temperatures are forbidden inputs.",
            "evidence_needed": "A predeclared no-leak runtime run that consumes hA/Ta/Tsur/emissivity/layers and produces wall/fluid state internally.",
            "source_backed_path": "Use setup-dictionary passive rows plus runtime model state; audit runtime input manifest for wallHeatFlux/validation-temperature absence.",
            "priority": "highest",
            "current_release_status": "blocked",
        },
        {
            "missing_evidence_id": "M02",
            "item": "independent_h_correlation_or_literature_admission",
            "blocks": "portable h-correlation claim; source/property h release",
            "why_missing": "The current basis replaces wallHeatFlux-derived h with setup-dictionary h_ext, but it does not admit a general correlation fit.",
            "evidence_needed": "A literature/provenance table that defines h correlation, characteristic length, orientation, applicability envelope, and uncertainty without fitting protected rows.",
            "source_backed_path": "Keep setup dictionary hA as current basis; add correlation only in a separate literature/provenance row.",
            "priority": "high",
            "current_release_status": "not_released",
        },
        {
            "missing_evidence_id": "M03",
            "item": "junction_stub_layer_metadata_resolution",
            "blocks": "strong junction/stub source-property claim",
            "why_missing": "Junction rows include h_and_layers_present, h_only, and no_wall_layer_metadata patch roles.",
            "evidence_needed": "Patch-level separation of rcExternalTemperature, externalTemperature, and zeroGradient junction/stub roles, or a conservative family-level exclusion rule.",
            "source_backed_path": "Preserve family-level setup-basis release; avoid per-patch source-property claims until resolved.",
            "priority": "medium",
            "current_release_status": "setup_basis_only_with_caveat",
        },
        {
            "missing_evidence_id": "M04",
            "item": "numeric_heat_loss_same_qoi_uq",
            "blocks": "publication-grade heat-loss value and repair/freeze",
            "why_missing": "No numeric passive q_loss was released; setup-UQ smoke is not scoring or admission.",
            "evidence_needed": "Same-QOI uncertainty on model-computed passive heat loss after the runtime operator exists, keeping train/support/holdout split roles intact.",
            "source_backed_path": "Run UQ only on setup-legal inputs and model-generated states; compare diagnostics after solve, not as runtime inputs.",
            "priority": "high",
            "current_release_status": "blocked",
        },
        {
            "missing_evidence_id": "M05",
            "item": "source_property_and_Qwall_release_gate",
            "blocks": "source/property release; Qwall release; candidate freeze",
            "why_missing": "Current package reports source_property_release_allowed_rows=0, Qwall_release_allowed_rows=0, repair_run_allowed_rows=0, candidate_freeze_allowed_rows=0.",
            "evidence_needed": "A separate predeclared gate after runtime operator smoke/UQ, with no protected scoring or hidden multiplier.",
            "source_backed_path": "Use claim-boundary and runtime input audits from this package as preflight conditions.",
            "priority": "high",
            "current_release_status": "closed",
        },
    ]


def build_implementation_path() -> List[Dict[str, Any]]:
    return [
        {
            "phase": "P1",
            "objective": "Freeze setup-source rows as inputs, not as fitted closures.",
            "inputs_allowed": "area, hA, Ta, Tsur, emissivity, wall layers, source family labels",
            "inputs_forbidden": "wallHeatFlux, CFD mdot, Qwall, validation/holdout/external temperatures, global multiplier",
            "deliverable": "runtime input manifest and source-family setup table",
            "decision_gate": "5/5 passive families remain source-basis ready; no forbidden runtime input is released",
        },
        {
            "phase": "P2",
            "objective": "Implement or audit the no-leak q_loss operator.",
            "inputs_allowed": "setup hA/Ta/Tsur/emissivity/layers and model-predicted wall or bulk-fluid state",
            "inputs_forbidden": "realized CFD wallHeatFlux and protected observed temperatures",
            "deliverable": "operator equation ledger plus unit/sign tests",
            "decision_gate": "computed q_loss changes only with setup inputs or predicted states",
        },
        {
            "phase": "P3",
            "objective": "Run train-only setup smoke and one-at-a-time setup UQ.",
            "inputs_allowed": "setup-legal ambient, hA, radiation, layer, heater/cooler declaration, pressure-loss controls",
            "inputs_forbidden": "validation/holdout tuning and post-solve diagnostics as inputs",
            "deliverable": "mdot/TP/TW/heat-ledger sensitivity table",
            "decision_gate": "execution completes with protected_scoring_rows=0 and source_property_release_rows=0",
        },
        {
            "phase": "P4",
            "objective": "Compare diagnostic wallHeatFlux after the solve only.",
            "inputs_allowed": "post-solve diagnostics and source paths for interpretation",
            "inputs_forbidden": "using diagnostic residuals to tune internal Nu or external h",
            "deliverable": "diagnostic residual owner table",
            "decision_gate": "diagnostic comparison explains residual direction without changing runtime inputs",
        },
        {
            "phase": "P5",
            "objective": "Consider source/property or repair/freeze gate only after P1-P4 pass.",
            "inputs_allowed": "predeclared train-only candidate evidence and same-QOI UQ",
            "inputs_forbidden": "protected-row tuning, global multiplier, residual absorption into internal Nu",
            "deliverable": "release/no-release decision package",
            "decision_gate": "either a narrow runtime-legal candidate is released for later review or the no-release result is documented",
        },
    ]


def build_claim_boundary() -> List[Dict[str, Any]]:
    return [
        {
            "claim": "passive_H2 has a source-backed setup-dictionary basis for external passive boundaries",
            "status": "allowed",
            "basis": "5/5 passive source families release setup-basis rows",
            "required_wording": "setup-basis/source-dictionary inputs are available for future runtime construction",
            "forbidden_wording": "admitted heat-loss closure or fitted source property",
            "source_paths": field_source_paths(SOURCE_TABLE_PATH, RELEASE_GATE_PATH),
        },
        {
            "claim": "passive_H2 can define a no-leak external q_loss operator",
            "status": "allowed_with_boundary",
            "basis": "q_loss operator contract is admissible for future use from hA/Ta/Tsur/emissivity/layers and runtime model state",
            "required_wording": "operator path released; numeric q_loss not released",
            "forbidden_wording": "Phase E wallHeatFlux-derived q_loss is released",
            "source_paths": field_source_paths(Q_LOSS_CONTRACT_PATH),
        },
        {
            "claim": "passive_H2 numeric passive heat losses are released",
            "status": "forbidden",
            "basis": "numeric_q_loss_release_allowed_rows=0",
            "required_wording": "numeric heat loss remains blocked pending runtime-operator evaluation and UQ",
            "forbidden_wording": "paper-grade passive q, Qwall, or source term is admitted",
            "source_paths": field_source_paths(SOURCE_SUMMARY_PATH, Q_LOSS_CONTRACT_PATH),
        },
        {
            "claim": "passive_H2 source/property, Qwall, repair, or candidate freeze is released",
            "status": "forbidden",
            "basis": "source_property_release_allowed_rows=0; Qwall_release_allowed_rows=0; repair_run_allowed_rows_this_task=0; candidate_freeze_allowed_rows=0",
            "required_wording": "no release/no repair/no freeze",
            "forbidden_wording": "source property, Qwall value, repaired candidate, frozen candidate, or final score",
            "source_paths": field_source_paths(SOURCE_SUMMARY_PATH),
        },
        {
            "claim": "train-only setup-UQ smoke supports source-backed use",
            "status": "allowed_with_boundary",
            "basis": "3/3 baselines and 33/33 setup-legal variants accepted with protected scoring and source-property release rows at zero",
            "required_wording": "supporting smoke for runtime-legal setup variation, not admission",
            "forbidden_wording": "validated score, model selection, coefficient admission, or passive_H2 heat-loss release",
            "source_paths": field_source_paths(SETUP_UQ_SUMMARY_PATH, SETUP_UQ_RUNTIME_INPUT_PATH),
        },
    ]


def build_source_manifest() -> List[Dict[str, Any]]:
    sources = [
        (SOURCE_TABLE_PATH, "family-level passive_H2 setup-basis rows"),
        (RELEASE_GATE_PATH, "source-basis release gates"),
        (Q_LOSS_CONTRACT_PATH, "operator and forbidden-input contract"),
        (SOURCE_SUMMARY_PATH, "source-basis release summary"),
        (EXTBC_PATH, "external boundary setup dictionary evidence"),
        (PATCH_ROLE_PATH, "patch role and boundary dictionary trace"),
        (HEAT_LOSS_CONTRACT_PATH, "heat-loss path/literature contract alignment"),
        (RADIATION_GUIDANCE_PATH, "radiation/double-counting guidance"),
        (SETUP_REF_PATH, "external boundary setup reference"),
        (GEOMETRY_REF_PATH, "physical geometry and insulation reference"),
        (SETUP_UQ_SUMMARY_PATH, "train-only setup-UQ smoke summary"),
        (SETUP_UQ_RUNTIME_INPUT_PATH, "train-only runtime input manifest"),
        (SETUP_UQ_HEAT_SENSITIVITY_PATH, "train-only mdot/heat sensitivity"),
    ]
    return [
        {
            "source_path": rel(path),
            "exists": path.exists(),
            "use_in_this_packet": use,
            "mutation_status": "read_only",
        }
        for path, use in sources
    ]


def write_readme(summary: Dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(SOURCE_TABLE_PATH)}
  - {rel(RELEASE_GATE_PATH)}
  - {rel(Q_LOSS_CONTRACT_PATH)}
  - {rel(SETUP_UQ_SUMMARY_PATH)}
tags: [thermal, passive-h2, source-basis, runtime-legality, no-release]
related:
  - .agent/status/{DATE}_{TASK_ID}.md
  - .agent/journal/{DATE}/thermal-passive-h2-source-evidence-recovery.md
  - imports/{DATE}_thermal_passive_h2_source_evidence_recovery.json
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# passive_H2 Source Evidence Recovery

Generated: `{summary['generated_at_utc']}`

Decision: `{summary['decision']}`.

This packet answers what is now source-backed for passive_H2 and what is still
missing. The result is deliberately split:

- `5/5` passive source families are source-backed for setup-dictionary external
  boundary construction.
- `5/5` families have an admissible future `q_loss` operator basis from
  `hA`, `Ta`, `Tsur`, emissivity, layers, and a model-predicted runtime state.
- `0` numeric passive heat-loss values are released.
- `0` source/property, `Qwall`, repair, freeze, coefficient admission, or final
  score claims are released.

## Why this matters

Earlier passive heat-loss work risked leaning on realized CFD `wallHeatFlux`.
The current source-backed basis fixes that for setup construction: the passive
external-boundary inputs now come from source dictionaries and source package
tables. The missing evidence is no longer "find any passive data"; it is a
narrower scientific gap: evaluate the released operator with predicted runtime
states and quantify uncertainty without using protected diagnostics as inputs.

## Files

- `passive_h2_family_evidence_recovery_matrix.csv`: family-level status and
  missing evidence.
- `source_backing_strength_by_field.csv`: field-level source backing, claim
  strength, and caveats.
- `passive_h2_missing_evidence_after_recovery.csv`: blockers that still prevent
  source/property, numeric-q, repair, or freeze release.
- `implementation_path_to_more_source_backed.csv`: phased path to make the
  runtime implementation more source-backed.
- `publication_claim_boundary.csv`: allowed and forbidden publication wording.
- `source_manifest.csv`: exact read-only sources used here.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
or external repo source, thesis current/LaTeX file, source/property release,
Qwall release, numeric heat-loss release, repair run, candidate freeze,
coefficient admission, protected scoring, fitting/model selection, final-score
claim, or runtime-leakage relaxation was performed.
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_rows = read_csv(SOURCE_TABLE_PATH)
    release_gate_rows = read_csv(RELEASE_GATE_PATH)
    q_rows = read_csv(Q_LOSS_CONTRACT_PATH)
    source_summary = read_json(SOURCE_SUMMARY_PATH)
    setup_uq_summary = read_json(SETUP_UQ_SUMMARY_PATH)

    family_matrix = build_family_matrix(source_rows, q_rows)
    field_strength = build_field_strength(source_rows, release_gate_rows)
    missing = build_missing_evidence()
    implementation = build_implementation_path()
    claim_boundary = build_claim_boundary()
    source_manifest = build_source_manifest()

    write_csv(OUT_DIR / "passive_h2_family_evidence_recovery_matrix.csv", family_matrix)
    write_csv(OUT_DIR / "source_backing_strength_by_field.csv", field_strength)
    write_csv(OUT_DIR / "passive_h2_missing_evidence_after_recovery.csv", missing)
    write_csv(OUT_DIR / "implementation_path_to_more_source_backed.csv", implementation)
    write_csv(OUT_DIR / "publication_claim_boundary.csv", claim_boundary)
    write_csv(OUT_DIR / "source_manifest.csv", source_manifest)

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": now_iso(),
        "decision": "passive_h2_source_evidence_recovered_setup_backed_runtime_operator_path_no_release",
        "passive_family_rows": len(family_matrix),
        "source_basis_release_ready_rows": sum(1 for row in family_matrix if truthy(row["source_basis_release_ready_now"])),
        "runtime_setup_input_allowed_next_row_rows": sum(1 for row in family_matrix if truthy(row["runtime_setup_input_allowed_next_row"])),
        "q_loss_operator_admissible_rows": sum(1 for row in family_matrix if truthy(row["q_loss_operator_admissible_next_use"])),
        "source_property_release_allowed_rows": sum(1 for row in family_matrix if truthy(row["source_property_release_allowed"])),
        "Qwall_release_allowed_rows": sum(1 for row in family_matrix if truthy(row["Qwall_release_allowed"])),
        "numeric_q_loss_released_rows": sum(1 for row in family_matrix if truthy(row["numeric_q_loss_released"])),
        "repair_run_allowed_rows": sum(1 for row in family_matrix if truthy(row["repair_run_allowed_this_task"])),
        "candidate_freeze_allowed_rows": sum(1 for row in family_matrix if truthy(row["candidate_freeze_allowed"])),
        "forbidden_wallflux_runtime_input_rows": sum(1 for row in family_matrix if truthy(row["realized_wallHeatFlux_runtime_input_allowed"])),
        "missing_evidence_rows": len(missing),
        "claim_boundary_rows": len(claim_boundary),
        "allowed_publication_claim_rows": sum(1 for row in claim_boundary if row["status"].startswith("allowed")),
        "forbidden_publication_claim_rows": sum(1 for row in claim_boundary if row["status"] == "forbidden"),
        "setup_uq_smoke_status": setup_uq_summary["smoke_status"],
        "setup_uq_baseline_accepted_rows": setup_uq_summary["baseline_accepted_rows"],
        "setup_uq_variant_accepted_rows": setup_uq_summary["variant_accepted_rows"],
        "setup_uq_source_property_release_rows": setup_uq_summary["source_property_release_rows"],
        "setup_uq_protected_scoring_rows": setup_uq_summary["protected_scoring_rows"],
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_or_sampler_launch": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
        "source_property_release": False,
        "qwall_release": False,
        "numeric_q_loss_release": False,
        "repair_run": False,
        "candidate_freeze": False,
        "coefficient_admission": False,
        "protected_scoring": False,
        "fitting_or_model_selection": False,
        "source_summary_decision": source_summary["decision"],
    }

    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
