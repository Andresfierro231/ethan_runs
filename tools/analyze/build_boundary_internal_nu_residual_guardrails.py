#!/usr/bin/env python3
"""Build boundary/internal-Nu residual ownership guardrails.

The package converts the internal-Nu zero-fit decision and upcomer
recirculation admission rule into boundary-model guardrails. It is a policy and
extraction-contract artifact, not a new CFD extraction or Fluid run.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_boundary_internal_nu_residual_guardrails"
THERMAL_GATE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate"
UPCOMER_GATE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility"
BOUNDARY_DECISION = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision"

THERMAL_README = THERMAL_GATE / "README.md"
THERMAL_POLICY = THERMAL_GATE / "sign_radiation_nu_policy.csv"
UPCOMER_README = UPCOMER_GATE / "README.md"
UPCOMER_BLOCKED = UPCOMER_GATE / "blocked_missing_metrics.csv"
BOUNDARY_README = BOUNDARY_DECISION / "README.md"
BOUNDARY_TABLE = BOUNDARY_DECISION / "decision_table.csv"

RESIDUAL_COLUMNS = [
    "residual_id",
    "residual_owner",
    "residual_description",
    "boundary_model_form_or_ledger",
    "primary_runtime_setup_inputs",
    "diagnostic_cfd_quantities",
    "allowed_use",
    "internal_nu_guardrail",
    "excluded_internal_nu_use",
    "shared_extraction_window_rule",
    "source_evidence",
]

FIELD_COLUMNS = [
    "field_id",
    "field_name",
    "needed_by",
    "boundary_model_use",
    "internal_nu_or_upcomer_use",
    "window_and_plane_rule",
    "source_path_or_owner_to_preserve",
    "fit_runtime_status",
    "double_count_guardrail",
    "priority",
]

MANIFEST_COLUMNS = ["artifact", "role", "mutation_status", "path"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    return value


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_value(row.get(column, "")) for column in columns})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def residual_rows() -> list[dict[str, str]]:
    no_nu = "Do not fit this residual into internal Nu; internal Nu has 0 fit-admissible rows and is coefficient magnitude only."
    same_window = "Use the same case, segment/patch map, time window, and inlet/mid/outlet planes as therm-reconstr/upcomer extraction."
    return [
        {
            "residual_id": "heater_realized_fraction",
            "residual_owner": "BC-modeling: heater/source contract",
            "residual_description": "Mismatch between setup heater power and heat that reaches the fluid.",
            "boundary_model_form_or_ledger": "eta_heater * P_heater_setup, with optional train-only scalar; test-section source kept separate.",
            "primary_runtime_setup_inputs": "heater setup power; declared source contract; property lane; geometry",
            "diagnostic_cfd_quantities": "realized heater wallHeatFlux and equivalent eta_heater are diagnostic only",
            "allowed_use": "Fit or score heater fraction only under declared split; default C1 heater-only until admitted otherwise.",
            "internal_nu_guardrail": no_nu,
            "excluded_internal_nu_use": "Do not raise/lower Nu to compensate for heater-transfer efficiency or test-section source mistakes.",
            "shared_extraction_window_rule": same_window,
            "source_evidence": f"{rel(THERMAL_README)}; {rel(BOUNDARY_TABLE)}",
        },
        {
            "residual_id": "cooler_hx_removal",
            "residual_owner": "BC-modeling: cooler/HX",
            "residual_description": "Mismatch between setup HX/cooler model and heat removed by the active cooler path.",
            "boundary_model_form_or_ledger": "Predictive HX UA/effectiveness model; imposed-cooler replay only when explicitly labeled.",
            "primary_runtime_setup_inputs": "air/coolant inlet conditions; HX geometry; active length; flow setup; property lane",
            "diagnostic_cfd_quantities": "CFD cooler removed duty and cooler wallHeatFlux are train/score targets only",
            "allowed_use": "Train a UA/effectiveness scalar only on admitted train rows after Fluid API support exists.",
            "internal_nu_guardrail": no_nu,
            "excluded_internal_nu_use": "Do not tune internal Nu to hide active cooler duty or imposed-cooler replay error.",
            "shared_extraction_window_rule": same_window,
            "source_evidence": f"{rel(BOUNDARY_README)}; {rel(BOUNDARY_TABLE)}",
        },
        {
            "residual_id": "wall_layer_external_convection",
            "residual_owner": "BC-modeling: wall-layer/external convection",
            "residual_description": "Passive heat loss through wall/layer/contact/insulation to ambient.",
            "boundary_model_form_or_ledger": "External boundary dictionary with h, Ta, wall/layer resistance, exposed area, and drive-temperature selector.",
            "primary_runtime_setup_inputs": "external h or UA; Ta; wall/layer geometry and resistance; segment/patch area",
            "diagnostic_cfd_quantities": "passive wallHeatFlux and wall/shell temperature proxies are diagnostic/score targets",
            "allowed_use": "Represent as external boundary/wall-layer residual with setup-only inputs.",
            "internal_nu_guardrail": no_nu,
            "excluded_internal_nu_use": "Do not absorb passive external loss or wall-layer drive-temperature error into Nu.",
            "shared_extraction_window_rule": same_window,
            "source_evidence": f"{rel(BOUNDARY_TABLE)}; {rel(THERMAL_POLICY)}",
        },
        {
            "residual_id": "radiation_metadata",
            "residual_owner": "BC-modeling: radiation semantics",
            "residual_description": "Radiative exchange metadata embedded in CFD rcExternalTemperature wallHeatFlux.",
            "boundary_model_form_or_ledger": "Replay: embedded in realized wallHeatFlux; predictive: epsilon*sigma*A*(T_surface^4 - Tsur^4) only in non-replay mode.",
            "primary_runtime_setup_inputs": "emissivity; Tsur; area; view-factor assumption if available; surface temperature from solve",
            "diagnostic_cfd_quantities": "rcExternalTemperature emissivity/Tsur metadata; total wallHeatFlux; no exported qr",
            "allowed_use": "Carry radiation metadata and prevent double counting; compute radiation explicitly only in predictive boundary mode.",
            "internal_nu_guardrail": no_nu,
            "excluded_internal_nu_use": "Do not create a radiation residual inside internal Nu, and do not add separate 1D radiation on top of realized wallHeatFlux replay.",
            "shared_extraction_window_rule": same_window,
            "source_evidence": f"{rel(THERMAL_POLICY)}; {rel(BOUNDARY_README)}",
        },
        {
            "residual_id": "wall_storage_transient",
            "residual_owner": "therm-reconstr / BC-modeling interface",
            "residual_description": "Unsteady wall or solid storage between fluid enthalpy, wallHeatFlux, and wall/shell temperatures.",
            "boundary_model_form_or_ledger": "Storage/residual ledger term with wall/shell temperature time derivative; not a steady Nu correction.",
            "primary_runtime_setup_inputs": "wall material heat capacity/density/volume if storage model is admitted; time-window metadata",
            "diagnostic_cfd_quantities": "wall/shell T time histories; enthalpy residual trend; segment heat residual",
            "allowed_use": "Label as storage or residual until a transient wall model is explicitly admitted.",
            "internal_nu_guardrail": no_nu,
            "excluded_internal_nu_use": "Do not use Nu to erase non-steady heat balance or storage residuals.",
            "shared_extraction_window_rule": same_window,
            "source_evidence": f"{rel(THERMAL_README)}; {rel(UPCOMER_README)}",
        },
        {
            "residual_id": "branch_mixing_recirculation",
            "residual_owner": "internal-Nu/upcomer admission plus BC-modeling ledger",
            "residual_description": "Branch mixing, reverse flow, and recirculation-cell heat transport that invalidates single-stream labels.",
            "boundary_model_form_or_ledger": "Section-effective or diagnostic mixing residual; single-stream Nu/f_D/K rejected when recirculation criteria are met.",
            "primary_runtime_setup_inputs": "none admitted yet; future model needs plane-resolved reverse/secondary-flow metrics and branch mixing state",
            "diagnostic_cfd_quantities": "reverse area fraction; reverse mass fraction; secondary velocity fraction; recirculation zone flag",
            "allowed_use": "Use as admission/naming guardrail and residual attribution; keep rows out of internal-Nu fits.",
            "internal_nu_guardrail": no_nu,
            "excluded_internal_nu_use": "Do not label recirculating upcomer rows as transferable single-stream Nu or use them to fit Nu.",
            "shared_extraction_window_rule": same_window,
            "source_evidence": f"{rel(UPCOMER_README)}; {rel(UPCOMER_BLOCKED)}",
        },
        {
            "residual_id": "internal_convection_development",
            "residual_owner": "internal-Nu after admission only",
            "residual_description": "True internal convection/development coefficient residual after boundary, storage, and mixing terms are separated.",
            "boundary_model_form_or_ledger": "Baseline/literature/default Nu only until a later thermal gate admits fit rows.",
            "primary_runtime_setup_inputs": "Re; Pr; Gz; hydraulic diameter; section length; admitted wall-bulk drive temperature",
            "diagnostic_cfd_quantities": "HTC/UA/Nu diagnostics from admitted windows only",
            "allowed_use": "Validation-only comparison today; future fitting only after admission gate changes.",
            "internal_nu_guardrail": "Fit is closed today: 0 fit-admissible rows. Boundary residuals must be removed before reopening.",
            "excluded_internal_nu_use": "Do not fit Nu to any unresolved heater, cooler, passive, radiation, storage, sign, or mixing residual.",
            "shared_extraction_window_rule": same_window,
            "source_evidence": f"{rel(THERMAL_README)}; {rel(THERMAL_POLICY)}",
        },
    ]


def field_rows() -> list[dict[str, str]]:
    window = "Same final averaging window, same reconstructed field source, same segment interfaces, and matched upcomer inlet/mid/outlet planes."
    return [
        {
            "field_id": "bulk_temperature",
            "field_name": "T_bulk_mass_flux_weighted_K",
            "needed_by": "boundary and internal-Nu",
            "boundary_model_use": "Boundary heat-balance and branch/sensor residual scoring.",
            "internal_nu_or_upcomer_use": "Wall-bulk Delta T and Gz/Nu drive temperature; upcomer plane thermal state.",
            "window_and_plane_rule": window,
            "source_path_or_owner_to_preserve": "therm-reconstr matched plane extraction; record exact case path and time range",
            "fit_runtime_status": "target/diagnostic, not runtime correction",
            "double_count_guardrail": "Use the same T_bulk for boundary residual and Nu diagnostics; do not refit separate bulk references.",
            "priority": "high",
        },
        {
            "field_id": "wall_inner_temperature",
            "field_name": "T_wall_inner_area_weighted_K",
            "needed_by": "boundary and internal-Nu",
            "boundary_model_use": "Wall-layer drive temperature and wall/storage residual.",
            "internal_nu_or_upcomer_use": "Internal wall-bulk Delta T candidate for HTC/Nu diagnostics.",
            "window_and_plane_rule": window,
            "source_path_or_owner_to_preserve": "therm-reconstr wall/owner-cell or sampled inner-wall field with patch ids",
            "fit_runtime_status": "diagnostic/score target until boundary API admits predictive wall drive",
            "double_count_guardrail": "If used for Nu Delta T, do not also use the same residual as external wall-layer fit error.",
            "priority": "high",
        },
        {
            "field_id": "wall_shell_temperature",
            "field_name": "T_wall_shell_or_owner_cell_K",
            "needed_by": "boundary",
            "boundary_model_use": "External convection/radiation drive and storage/residual check.",
            "internal_nu_or_upcomer_use": "Context only; not an internal Nu driving temperature unless explicitly admitted.",
            "window_and_plane_rule": window,
            "source_path_or_owner_to_preserve": "wall-shell sampling package paths and patch ids",
            "fit_runtime_status": "diagnostic/blocked predictive input until first-class boundary dictionaries exist",
            "double_count_guardrail": "Do not mix inner-wall and shell-wall temperatures in one fitted residual.",
            "priority": "high",
        },
        {
            "field_id": "wall_heat_flux",
            "field_name": "wallHeatFlux_W_or_W_per_m2_by_patch_segment",
            "needed_by": "boundary and internal-Nu",
            "boundary_model_use": "Boundary heat ledger target; separates heater, cooler, passive, and wall roles.",
            "internal_nu_or_upcomer_use": "HTC/Nu diagnostic numerator only after sign/admission rules pass.",
            "window_and_plane_rule": window,
            "source_path_or_owner_to_preserve": "OpenFOAM wallHeatFlux reductions with patch role table and sign convention",
            "fit_runtime_status": "diagnostic target only, never predictive runtime source",
            "double_count_guardrail": "CFD rcExternalTemperature radiation is embedded; do not add separate qr or fit Nu to total external wallHeatFlux residual.",
            "priority": "high",
        },
        {
            "field_id": "external_radiation_metadata",
            "field_name": "Tsur_K; Ta_K; emissivity; external_h_or_UA",
            "needed_by": "boundary",
            "boundary_model_use": "External convection/radiation setup dictionary and no-double-count radiation policy.",
            "internal_nu_or_upcomer_use": "Exclusion evidence: these are not internal-Nu fit parameters.",
            "window_and_plane_rule": "Same patch/segment mapping as wallHeatFlux; Ta/Tsur/emissivity must be recorded for the same boundary condition family.",
            "source_path_or_owner_to_preserve": "thermal-boundary/radiation map and case boundary dictionaries; preserve rcExternalTemperature metadata",
            "fit_runtime_status": "setup input or metadata, not internal-Nu runtime correction",
            "double_count_guardrail": "Radiation metadata belongs to boundary model; no separate radiation residual inside internal Nu.",
            "priority": "high",
        },
        {
            "field_id": "recirculation_vector_metrics",
            "field_name": "reverse_area_fraction; reverse_mass_fraction; secondary_velocity_fraction",
            "needed_by": "internal-Nu/upcomer and boundary residual attribution",
            "boundary_model_use": "Classifies branch-mixing residual and section-effective heat transport.",
            "internal_nu_or_upcomer_use": "Admission gate for rejecting single-stream Nu/f_D/K labels.",
            "window_and_plane_rule": window,
            "source_path_or_owner_to_preserve": "matched vector planes at upcomer inlet/mid/outlet with exact time window",
            "fit_runtime_status": "admission diagnostic only",
            "double_count_guardrail": "When recirculation criteria trip, do not assign remaining heat residual to transferable internal Nu.",
            "priority": "high",
        },
        {
            "field_id": "thermal_development_groups",
            "field_name": "Re; Pr; Ri; Ra_or_Gr; Gz; hydraulic_diameter; section_length",
            "needed_by": "boundary and internal-Nu",
            "boundary_model_use": "Separates property/development effects from boundary heat residuals.",
            "internal_nu_or_upcomer_use": "Required before any future Nu/development correlation can be admitted.",
            "window_and_plane_rule": "Compute from the same property lane and time window as T_bulk and vector metrics.",
            "source_path_or_owner_to_preserve": "therm-reconstr/internal-Nu derived metrics with property-mode label",
            "fit_runtime_status": "diagnostic/admission metric today",
            "double_count_guardrail": "Declare property lane before fitting boundary, friction, or Nu terms.",
            "priority": "medium",
        },
        {
            "field_id": "storage_time_metrics",
            "field_name": "dT_wall_dt; dT_bulk_dt; enthalpy_residual_trend_W",
            "needed_by": "boundary and therm-reconstr",
            "boundary_model_use": "Identifies storage/transient residual rather than steady boundary loss.",
            "internal_nu_or_upcomer_use": "Screens non-steady rows from Nu fitting.",
            "window_and_plane_rule": "Use the same final-window time series used for steady-state/admission decisions.",
            "source_path_or_owner_to_preserve": "time-series uncertainty and therm-reconstr final-window paths",
            "fit_runtime_status": "diagnostic screen",
            "double_count_guardrail": "Do not fit steady Nu or external h/UA to a non-steady storage residual.",
            "priority": "medium",
        },
    ]


def source_manifest() -> list[dict[str, str]]:
    sources = [
        (THERMAL_README, "source"),
        (THERMAL_POLICY, "source"),
        (UPCOMER_README, "source"),
        (UPCOMER_BLOCKED, "source"),
        (BOUNDARY_README, "source"),
        (BOUNDARY_TABLE, "source"),
    ]
    return [
        {
            "artifact": path.name,
            "role": role,
            "mutation_status": "read_only",
            "path": rel(path),
        }
        for path, role in sources
    ]


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(THERMAL_README)}
  - {rel(UPCOMER_README)}
  - {rel(BOUNDARY_README)}
tags: [boundary-modeling, internal-nu, guardrails, thermal-residuals]
related:
  - {rel(out_dir / 'thermal_residual_ownership_guardrails.csv')}
  - {rel(out_dir / 'boundary_fields_needed_for_upcomer_extraction.csv')}
task: AGENT-336
date: 2026-07-14
role: BC-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Boundary/Internal-Nu Residual Guardrails

## Purpose

Internal-Nu confirmed that current thermal closure cannot absorb boundary
residuals: there are `0` fit-admissible internal-Nu rows, and current admitted
upcomer evidence is recirculating. This package converts that decision into
boundary-model guardrails.

## Decision

Heat residuals are owned by their physical lane before any Nu fit is reopened:

- heater/source residuals belong to the heater realized-fraction/source
  contract;
- active cooler residuals belong to cooler/HX UA/effectiveness modeling;
- passive losses belong to wall-layer/external convection dictionaries;
- radiation is metadata embedded in CFD `rcExternalTemperature` `wallHeatFlux`
  during replay and must not be counted again;
- storage belongs to a wall/storage or transient residual ledger;
- branch mixing/recirculation belongs to section-effective admission/naming,
  not single-stream Nu.

## Files

- `thermal_residual_ownership_guardrails.csv`: residual ownership and explicit
  "do not fit this residual into internal Nu" guardrails.
- `boundary_fields_needed_for_upcomer_extraction.csv`: matched boundary and
  Nu/upcomer extraction fields, including wall T, bulk T, wallHeatFlux,
  Tsur/Ta/emissivity, external h/UA, vector-plane metrics, and window/source
  path coordination.
- `summary.json`: compact package status.

## Extraction Coordination

Boundary metrics and Nu metrics must use the same case path, property lane,
segment/patch map, time window, and matched upcomer inlet/mid/outlet planes.
If a field is used to score a boundary residual, the same residual may not be
reintroduced as an internal-Nu fit target under another temperature definition.

## Status

This is a guardrail and extraction-contract package. It does not mutate native
CFD outputs, registry/admission state, scheduler state, generated indexes, or
external Fluid files.

Summary: `{summary['residual_guardrail_rows']}` residual guardrail rows and
`{summary['boundary_field_rows']}` extraction-field rows.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build_package(out_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    residuals = residual_rows()
    fields = field_rows()
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "thermal_residual_ownership_guardrails.csv", residuals, RESIDUAL_COLUMNS)
    write_csv(out_dir / "boundary_fields_needed_for_upcomer_extraction.csv", fields, FIELD_COLUMNS)
    write_csv(out_dir / "source_manifest.csv", source_manifest(), MANIFEST_COLUMNS)
    summary = {
        "task": "AGENT-336",
        "status": "complete",
        "generated_at": utc_now(),
        "package": rel(out_dir),
        "residual_guardrail_rows": len(residuals),
        "boundary_field_rows": len(fields),
        "internal_nu_fit_admissible_rows_today": 0,
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
        "core_guardrail": "Do not fit heater, cooler/HX, wall/external convection, radiation, storage, or branch-mixing residuals into internal Nu.",
    }
    write_json(out_dir / "summary.json", summary)
    write_readme(out_dir, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = build_package(args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
