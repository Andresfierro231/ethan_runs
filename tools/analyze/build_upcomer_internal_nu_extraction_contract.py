#!/usr/bin/env python3
"""Build the upcomer internal-Nu extraction/admission contract."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_internal_nu_extraction_contract"

UPCOMER_ADMISSION = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md"
UPCOMER_BLOCKERS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/blocked_missing_metrics.csv"
THERMAL_GATE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/README.md"

PLANES = [
    ("upcomer_inlet", "Plane normal is the geometric upcomer station tangent oriented in nominal inlet-to-outlet flow direction."),
    ("upcomer_mid", "Plane normal is the geometric upcomer station tangent oriented in nominal inlet-to-outlet flow direction."),
    ("upcomer_outlet", "Plane normal is the geometric upcomer station tangent oriented in nominal inlet-to-outlet flow direction."),
]


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def metric_specs() -> list[dict[str, str]]:
    return [
        {
            "metric_id": "reverse_area_fraction",
            "metric_name": "reverse area fraction",
            "units": "dimensionless",
            "required_for": "single_stream_validity;recirculation_rule;Nu_admission",
            "formula": "sum(A_i for u_n_i < 0) / sum(A_i)",
            "source_fields": "U, face area A, plane normal n",
            "weighting": "area_weighted_faces",
            "acceptance_criteria": "finite 0..1; fit gate requires <0.02 at inlet/mid/outlet; invalid single-stream when >=0.10",
            "failure_status": "diagnostic_only_missing_reverse_area_fraction",
            "tooling_hint": "extend tools/extract/sample_upcomer_convection_cell.py to use geometric plane normal and face areas",
            "notes": "Do not use mean-velocity normal for admission because it can hide reverse flow by rotating with the cell.",
        },
        {
            "metric_id": "reverse_mass_fraction",
            "metric_name": "reverse mass fraction",
            "units": "dimensionless",
            "required_for": "single_stream_validity;recirculation_rule;Nu_admission",
            "formula": "sum(max(-rho_i*u_n_i, 0)*A_i) / sum(abs(rho_i*u_n_i)*A_i)",
            "source_fields": "rho, U, face area A, plane normal n",
            "weighting": "absolute_mass_flux_denominator",
            "acceptance_criteria": "finite 0..1; fit gate requires <0.02 at inlet/mid/outlet; invalid single-stream when >=0.10",
            "failure_status": "diagnostic_only_missing_reverse_mass_fraction",
            "tooling_hint": "extend upcomer vector-plane extraction; current validity proxies are insufficient for fit admission",
            "notes": "Use absolute flux in the denominator so a near-zero net-flow plane cannot mask a reverse-flow cell.",
        },
        {
            "metric_id": "secondary_velocity_fraction",
            "metric_name": "secondary velocity fraction",
            "units": "dimensionless",
            "required_for": "single_stream_validity;mixing_strength;Nu_admission",
            "formula": "rms(|U_i - u_n_i*n|) / rms(|U_i|)",
            "source_fields": "U, plane normal n",
            "weighting": "face_rms_or_area_weighted_rms_if_A_available",
            "acceptance_criteria": "finite 0..1; fit gate requires <0.20 at inlet/mid/outlet",
            "failure_status": "diagnostic_only_missing_secondary_velocity_fraction",
            "tooling_hint": "add vector decomposition to upcomer plane extractor",
            "notes": "Quantifies cross-stream motion; reverse-flow alone does not fully describe mixed-convection structure.",
        },
        {
            "metric_id": "mass_flux_weighted_bulk_T",
            "metric_name": "mass-flux-weighted bulk T",
            "units": "K",
            "required_for": "thermal_drive;Nu_candidate",
            "formula": "sum(rho_i*u_n_i*T_i*A_i) / sum(rho_i*u_n_i*A_i)",
            "source_fields": "rho, U, T, face area A, plane normal n",
            "weighting": "signed_mass_flux",
            "acceptance_criteria": "finite; denominator nonzero; fit use allowed only when reverse_mass_fraction <0.02 at the same plane",
            "failure_status": "diagnostic_only_missing_or_unstable_bulk_T",
            "tooling_hint": "align with tools/extract/sample_span_endpoint_temperatures.py but use geometric upcomer planes",
            "notes": "This is the thermal-driving bulk T for single-stream fit rows; in recirculation it may remain diagnostic only.",
        },
        {
            "metric_id": "forward_only_bulk_T_diagnostic",
            "metric_name": "forward-only bulk T diagnostic",
            "units": "K",
            "required_for": "diagnostic_temperature_context",
            "formula": "sum(rho_i*max(u_n_i,0)*T_i*A_i) / sum(rho_i*max(u_n_i,0)*A_i)",
            "source_fields": "rho, U, T, face area A, plane normal n",
            "weighting": "positive_mass_flux_only",
            "acceptance_criteria": "finite when forward flux exists; never by itself fit-admits Nu",
            "failure_status": "diagnostic_only_missing_forward_bulk_T",
            "tooling_hint": "reuse forward-only convention from sample_span_endpoint_temperatures.py",
            "notes": "Useful when recirculation makes signed mixing-cup T physically misleading.",
        },
        {
            "metric_id": "area_weighted_wall_T",
            "metric_name": "area-weighted wall T",
            "units": "K",
            "required_for": "thermal_drive;Nu_candidate",
            "formula": "sum(T_wall_j*A_j) / sum(A_j) over wall faces in the matching station band",
            "source_fields": "wall T, wall face area A, station band mask",
            "weighting": "wall_area",
            "acceptance_criteria": "finite; station band matches the plane and wallHeatFlux band; |T_wall - T_bulk| >=0.5 K for fit gate",
            "failure_status": "diagnostic_only_missing_area_weighted_wall_T",
            "tooling_hint": "extend tools/extract/sample_segment_htc_uaprime.py conventions or parse reconstructed T boundary faces",
            "notes": "Must not use patch means if face areas are available for the admission row; patch means can remain diagnostic.",
        },
        {
            "metric_id": "wallHeatFlux",
            "metric_name": "wallHeatFlux",
            "units": "W/m2",
            "required_for": "thermal_drive;heat_balance;Nu_candidate",
            "formula": "sum(q_wall_j*A_j) / sum(A_j), sign-normalized so positive means heat enters the fluid",
            "source_fields": "wallHeatFlux, wall face area A, station band mask",
            "weighting": "wall_area",
            "acceptance_criteria": "finite; same station band as wall T; sign convention passes; wallHeatFlux/enthalpy residual <=10% for fit gate",
            "failure_status": "diagnostic_only_missing_or_sign_failed_wallHeatFlux",
            "tooling_hint": "reuse wallHeatFlux parsing conventions from tools/extract/sample_segment_htc_uaprime.py",
            "notes": "For rcExternalTemperature cases wallHeatFlux includes radiation; no separate exported qr term exists and no qr residual may be added to Nu.",
        },
        {
            "metric_id": "Re",
            "metric_name": "Reynolds number",
            "units": "dimensionless",
            "required_for": "regime;Nu_correlation_axes",
            "formula": "rho_bulk*abs(u_bulk)*D_h/mu_bulk",
            "source_fields": "rho_bulk, u_bulk, D_h, mu_bulk or solver Re field",
            "weighting": "bulk_property_at_mass_flux_weighted_bulk_T",
            "acceptance_criteria": "finite positive; if solver Re exists, recomputed value agrees within 10% or row is diagnostic-only",
            "failure_status": "diagnostic_only_missing_or_mismatched_Re",
            "tooling_hint": "sample solver Re and also compute from extracted bulk properties when available",
            "notes": "Do not use CFD mdot as a forward-model runtime input; this is extraction evidence only.",
        },
        {
            "metric_id": "Pr",
            "metric_name": "Prandtl number",
            "units": "dimensionless",
            "required_for": "thermal_regime;Nu_correlation_axes",
            "formula": "cp_bulk*mu_bulk/k_bulk",
            "source_fields": "cp_bulk, mu_bulk, k_bulk or solver Pr field",
            "weighting": "bulk_property_at_mass_flux_weighted_bulk_T",
            "acceptance_criteria": "finite positive; if solver Pr exists, recomputed value agrees within 10% or row is diagnostic-only",
            "failure_status": "diagnostic_only_missing_or_mismatched_Pr",
            "tooling_hint": "carry property lane metadata with extracted row",
            "notes": "Property-lane changes are not Nu-fit evidence by themselves.",
        },
        {
            "metric_id": "Ri",
            "metric_name": "Richardson number",
            "units": "dimensionless",
            "required_for": "recirculation_rule;mixed_convection_screen",
            "formula": "Gr/Re^2",
            "source_fields": "Gr, Re or solver Ri field",
            "weighting": "plane_or_section_median_for_regime;carry_mean_as_diagnostic",
            "acceptance_criteria": "finite; fit gate requires <0.30 at inlet/mid/outlet; invalid single-stream when >=1.0",
            "failure_status": "diagnostic_only_missing_or_mismatched_Ri",
            "tooling_hint": "prefer median Ri for admission because mean can be dominated by near-zero velocities",
            "notes": "If solver Ri exists, compare to recomputed Gr/Re^2 and flag mismatch above 10%.",
        },
        {
            "metric_id": "Gr",
            "metric_name": "Grashof number",
            "units": "dimensionless",
            "required_for": "Ri;Ra;thermal_regime",
            "formula": "g*beta_bulk*abs(T_wall - T_bulk)*D_h^3/nu_bulk^2",
            "source_fields": "g, beta_bulk, T_wall, T_bulk, D_h, nu_bulk or solver Gr field",
            "weighting": "bulk_property_at_mass_flux_weighted_bulk_T",
            "acceptance_criteria": "finite nonnegative; direct wall-bulk Delta T present; solver/recomputed mismatch <=10% for fit gate",
            "failure_status": "diagnostic_only_missing_Gr_or_wall_bulk_delta_T",
            "tooling_hint": "carry both solver Gr and recomputed Gr when solver field is available",
            "notes": "Use abs(T_wall - T_bulk) for magnitude; retain heat direction separately via wallHeatFlux sign.",
        },
        {
            "metric_id": "Ra",
            "metric_name": "Rayleigh number",
            "units": "dimensionless",
            "required_for": "natural_convection_cell_context",
            "formula": "Gr*Pr",
            "source_fields": "Gr, Pr or solver Ra field",
            "weighting": "derived",
            "acceptance_criteria": "finite nonnegative; solver/recomputed mismatch <=10% for fit gate when solver field exists",
            "failure_status": "diagnostic_only_missing_or_mismatched_Ra",
            "tooling_hint": "carry Ra as context; do not fit internal Nu from Ra-only cell evidence",
            "notes": "Ra can support interpretation of cell strength but does not override reverse-flow gates.",
        },
        {
            "metric_id": "Gz",
            "metric_name": "Graetz number",
            "units": "dimensionless",
            "required_for": "thermal_development_screen",
            "formula": "Re*Pr*D_h/L_from_upcomer_inlet_to_plane",
            "source_fields": "Re, Pr, D_h, station arc length L",
            "weighting": "derived",
            "acceptance_criteria": "mid/outlet finite positive; inlet is not_applicable_zero_entry_length; missing mid/outlet Gz blocks fit admission",
            "failure_status": "diagnostic_only_missing_Gz",
            "tooling_hint": "use mesh-centerline arc length from upcomer inlet to plane",
            "notes": "Do not assume thermally developed flow without Gz or equivalent development evidence.",
        },
        {
            "metric_id": "plane_location",
            "metric_name": "plane location",
            "units": "categorical",
            "required_for": "contract_integrity",
            "formula": "one of upcomer_inlet, upcomer_mid, upcomer_outlet with mesh coordinates and span/station provenance",
            "source_fields": "mesh station label, point, normal, span, source_id",
            "weighting": "not_applicable",
            "acceptance_criteria": "exact plane label, point, normal, and source path recorded; all three planes present for each candidate row",
            "failure_status": "diagnostic_only_missing_plane_location",
            "tooling_hint": "derive from mesh_stations.json, not schematic-only station labels",
            "notes": "The outlet/mid/inlet labels define admission grouping and must be reproducible.",
        },
        {
            "metric_id": "exact_time_window",
            "metric_name": "exact time window",
            "units": "s",
            "required_for": "admission_provenance;time_uncertainty",
            "formula": "time_start_s, time_end_s, n_samples, representative_time_s, and source time directory for every extracted field",
            "source_fields": "postProcessing time directories, convergence/time-window package",
            "weighting": "not_applicable",
            "acceptance_criteria": "all fields use the same admitted time window or record controlled interpolation; absent time window blocks fit admission",
            "failure_status": "diagnostic_only_missing_exact_time_window",
            "tooling_hint": "tie vector, thermal, wall, and nondimensional extracts to the same time-window manifest",
            "notes": "Single-time smoke rows can be diagnostic but cannot reopen internal-Nu fitting.",
        },
    ]


def build_extraction_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for metric in metric_specs():
        for plane, normal_note in PLANES:
            criteria = metric["acceptance_criteria"]
            failure = metric["failure_status"]
            if metric["metric_id"] == "Gz" and plane == "upcomer_inlet":
                criteria = "record as not_applicable_zero_entry_length; this plane does not block fit if mid/outlet Gz are finite"
                failure = "not_applicable_zero_entry_length"
            row = {
                **metric,
                "plane_location": plane,
                "normal_definition": normal_note,
                "acceptance_criteria": criteria,
                "failure_status": failure,
            }
            rows.append(row)
    return rows


def build_admission_rows() -> list[dict[str, str]]:
    return [
        {
            "classification": "diagnostic_only",
            "required_evidence": "At least one requested extraction metric exists, but one or more fit gates are missing or failed.",
            "pass_criteria": "Use for physics interpretation, blocker evidence, or trend screening only.",
            "automatic_blockers": "missing required metric; missing exact time window; candidate not admitted; coarse/no-GCI; heat-balance/sign unresolved; invalid single-stream condition; smoke/repaired output not explicitly admitted",
            "allowed_label": "Nu_section_effective_upcomer_diagnostic",
            "forbidden_label": "Nu_fit_admissible_upcomer_single_stream; universal_Nu; transferable_Nu",
            "allowed_use": "diagnostic plots, admission memos, extraction debugging, validation context",
            "forbidden_use": "internal Nu fitting, forward-runtime calibration, residual absorption",
        },
        {
            "classification": "validation_only",
            "required_evidence": "All requested metrics finite and interpretable, but one or more closure-fit gates remain open.",
            "pass_criteria": "Matched inlet/mid/outlet planes, exact time window, sign/radiation semantics correct, and no missing source provenance.",
            "automatic_blockers": "train/validation role forbids fitting; mesh/time uncertainty not accepted; wallHeatFlux/enthalpy residual above fit tolerance; mild transition/recirculation still present; no ordinary-pipe anchor set",
            "allowed_label": "Nu_section_effective_upcomer_validation",
            "forbidden_label": "Nu_fit_admissible_upcomer_single_stream; universal_Nu; transferable_Nu",
            "allowed_use": "holdout comparison, validation-only scorecards, boundary/thermal sanity checks",
            "forbidden_use": "fit coefficient training or runtime residual correction",
        },
        {
            "classification": "fit_admissible_Nu",
            "required_evidence": "Complete matched-plane extraction, admitted case role, accepted mesh/time uncertainty, clean single-stream metrics, and separated thermal residual ownership.",
            "pass_criteria": "reverse_area_fraction<0.02 and reverse_mass_fraction<0.02 at all planes; Ri<0.30 at all planes; secondary_velocity_fraction<0.20; |T_wall-T_bulk|>=0.5 K; wallHeatFlux/enthalpy residual<=10%; sign convention passes; Gz finite at mid/outlet; no Nu residual absorption",
            "automatic_blockers": "any invalid single-stream condition; missing metric; sign failure; radiation double-count; wall storage/branch mixing/heater/cooler/passive loss residual assigned to Nu; no mesh/time acceptance",
            "allowed_label": "Nu_fit_admissible_upcomer_single_stream",
            "forbidden_label": "Nu_section_effective_upcomer_diagnostic as fit row; universal_Nu without section/regime qualifiers",
            "allowed_use": "internal Nu fit candidate after train/validation/holdout split is assigned",
            "forbidden_use": "fitting across recirculating upcomer cells or absorbing boundary-condition residuals",
        },
        {
            "classification": "invalid_single_stream_coefficient",
            "required_evidence": "Any material reverse-flow, recirculation, or buoyancy-dominated evidence.",
            "pass_criteria": "reverse_area_fraction>=0.10 or reverse_mass_fraction>=0.10 or Ri>=1.0 or explicit recirculation flag is yes.",
            "automatic_blockers": "single-stream Nu/f_D/K label requested on a recirculating section",
            "allowed_label": "Nu_section_effective_upcomer_diagnostic; f_D_section_effective_upcomer_diagnostic; K_section_effective_upcomer_diagnostic",
            "forbidden_label": "universal_Nu; universal_f_D; universal_K; transferable_Nu; transferable_f_D; transferable_K",
            "allowed_use": "diagnostic and admission-rule evidence",
            "forbidden_use": "single-stream closure fitting or transferable coefficient claims",
        },
    ]


def write_naming_policy() -> None:
    text = """# Coefficient Naming Policy For Upcomer Recirculation

Date: 2026-07-14

Task: AGENT-339

## Required Names

`Nu_section_effective_upcomer_diagnostic` means the row is an effective diagnostic for the extracted upcomer section. It is not a true fit Nu row and must not be consumed by internal-Nu fitting or forward-runtime calibration.

`Nu_section_effective_upcomer_validation` means the row is complete enough for validation-only comparison but still fails at least one fit gate.

`Nu_fit_admissible_upcomer_single_stream` is the only allowed name for a true fit-admissible upcomer Nu row. It can be used only after the extraction/admission contract passes every fit criterion.

## Invalid Single-Stream Conditions

Single-stream `Nu`, `f_D`, and `K` labels are invalid when any of these conditions hold:

- `reverse_area_fraction >= 0.10`
- `reverse_mass_fraction >= 0.10`
- `Ri >= 1.0`
- explicit recirculation flag is `yes`

Rows meeting any of those conditions must use section-effective or diagnostic labels such as `Nu_section_effective_upcomer_diagnostic`, `f_D_section_effective_upcomer_diagnostic`, or `K_section_effective_upcomer_diagnostic`.

## Reopening Internal-Nu Fitting

Internal-Nu fitting may reopen only when a later gate has at least three admitted upcomer rows satisfying `fit_admissible_Nu`, including one ordinary-pipe non-recirculating anchor and one near-transition or higher-Re row. These rows must have matched inlet/mid/outlet extraction, exact time windows, accepted mesh/time uncertainty, clean sign and heat-balance checks, finite mid/outlet Gz, and no heater, cooler, wall, storage, radiation, branch-mixing, or recirculation residual assigned to Nu.

CFD `rcExternalTemperature` wallHeatFlux includes radiation where that boundary condition is used. There is no separate exported `qr` term to add to internal Nu, and no radiation residual may be hidden inside Nu.
"""
    (OUT / "coefficient_naming_policy.md").write_text(text, encoding="utf-8")


def write_readme(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(UPCOMER_ADMISSION)}
  - {rel(UPCOMER_BLOCKERS)}
  - {rel(THERMAL_GATE)}
tags: [internal-nu, upcomer-recirculation, extraction-contract, therm-reconstr]
related:
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-339
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Upcomer Internal-Nu Extraction Contract

## Purpose

This package turns the zero-fit upcomer/internal-Nu admission decision into an executable extraction and admission contract for `therm-reconstr`. It defines the exact matched-plane fields, formulas, row classifications, coefficient names, and evidence required before internal-Nu fitting can be reopened.

## Contract Summary

- Extraction rows: `{summary['n_extraction_rows']}`.
- Admission classifications: `{summary['n_admission_rows']}`.
- Required planes: `upcomer_inlet`, `upcomer_mid`, `upcomer_outlet`.
- Current fit-admissible upcomer Nu rows remain `0`.

The plane normal is the geometric upcomer station tangent oriented in nominal inlet-to-outlet flow direction. Do not use a mean-velocity normal for admission because it can rotate with the recirculation cell and hide reverse flow.

## Admission Rule

Rows are `invalid_single_stream_coefficient` when `reverse_area_fraction >= 0.10`, `reverse_mass_fraction >= 0.10`, `Ri >= 1.0`, or an explicit recirculation flag is `yes`. Such rows may use `Nu_section_effective_upcomer_diagnostic`, but they cannot become fit rows.

Rows are `fit_admissible_Nu` only when every required metric is finite, exact time windows are known, reverse area and mass fractions are below `0.02` at all three planes, `Ri < 0.30`, secondary velocity fraction is below `0.20`, `|T_wall - T_bulk| >= 0.5 K`, wallHeatFlux/enthalpy residual is within `10%`, mesh/time uncertainty is accepted, sign/radiation semantics pass, and no heater, cooler, passive loss, wall storage, branch mixing, radiation, or recirculation residual is assigned to Nu.

## Reopen Evidence

Internal-Nu fitting reopens only after at least three admitted upcomer rows pass `fit_admissible_Nu`, including an ordinary-pipe non-recirculating anchor and a near-transition or higher-Re row. Until then, forward work uses baseline/literature/default internal Nu behavior and treats upcomer section-effective Nu as diagnostic or validation-only.

## Outputs

- `upcomer_extraction_contract.csv`
- `upcomer_nu_admission_criteria.csv`
- `coefficient_naming_policy.md`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_source_manifest() -> None:
    rows = [
        {"path": rel(UPCOMER_ADMISSION), "role": "zero-fit upcomer recirculation/internal-Nu admission decision"},
        {"path": rel(UPCOMER_BLOCKERS), "role": "missing metrics and next extraction needs"},
        {"path": rel(THERMAL_GATE), "role": "thermal sign/radiation/Nu residual guardrails"},
    ]
    write_csv(OUT / "source_manifest.csv", rows, ["path", "role"])


def build() -> dict[str, Any]:
    extraction_rows = build_extraction_rows()
    admission_rows = build_admission_rows()
    write_csv(
        OUT / "upcomer_extraction_contract.csv",
        extraction_rows,
        [
            "metric_id",
            "metric_name",
            "units",
            "plane_location",
            "required_for",
            "formula",
            "source_fields",
            "weighting",
            "normal_definition",
            "acceptance_criteria",
            "failure_status",
            "tooling_hint",
            "notes",
        ],
    )
    write_csv(
        OUT / "upcomer_nu_admission_criteria.csv",
        admission_rows,
        [
            "classification",
            "required_evidence",
            "pass_criteria",
            "automatic_blockers",
            "allowed_label",
            "forbidden_label",
            "allowed_use",
            "forbidden_use",
        ],
    )
    write_naming_policy()
    write_source_manifest()
    summary = {
        "task": "AGENT-339",
        "status": "complete",
        "decision": "contract_only_current_fit_admissible_upcomer_Nu_rows_remain_zero",
        "n_extraction_rows": len(extraction_rows),
        "n_admission_rows": len(admission_rows),
        "planes": [plane for plane, _ in PLANES],
        "fit_reopen_minimum": "at least three admitted fit_admissible_Nu upcomer rows including one ordinary-pipe anchor and one near-transition_or_higher_Re row",
        "outputs": [
            "upcomer_extraction_contract.csv",
            "upcomer_nu_admission_criteria.csv",
            "coefficient_naming_policy.md",
            "source_manifest.csv",
            "README.md",
            "summary.json",
        ],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_readme(summary)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
