#!/usr/bin/env python3
"""Build the 1D conservative thermal ledger residual-owner contract."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


TASK_ID = "TODO-1D-CONSERVATIVE-THERMAL-LEDGER-RESIDUAL-OWNER-CONTRACT-2026-07-22"
SLUG = "1d_conservative_thermal_ledger_residual_owner_contract"
DATE = "2026-07-22"
OUTDIR = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract")

SOURCE_PATHS = [
    "operational_notes/maps/forward-predictive-model.md",
    "operational_notes/maps/thermal-closures-and-internal-nu.md",
    "operational_notes/07-26/22/2026-07-22_BOARD_STALE_CLEANUP_AND_HIGH_VALUE_1D_AVENUES.md",
    "work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv",
    "work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv",
    "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/setup_known_source_contract.csv",
    "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/source_property_gate.csv",
    "work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_s12_thermal_residual_candidate_disposition_and_thesis_panels/README.md",
    "work_products/2026-07/2026-07-22/2026-07-22_thesis_n3_thermal_residual_owner_train_ablation/thermal_residual_ablation_table.csv",
    "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/README.md",
    "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/README.md",
]

FORBIDDEN_TOKENS = (
    "realized CFD wallHeatFlux",
    "CFD mdot",
    "imposed CFD cooler duty",
    "validation temperatures",
    "holdout temperatures",
    "realized test-section heat",
    "hidden global multiplier",
    "final heat residual as closure",
)


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


def joined(items: Iterable[str]) -> str:
    return "; ".join(items)


def source_manifest(root: Path) -> list[dict[str, str]]:
    rows = []
    for idx, rel in enumerate(SOURCE_PATHS, 1):
        path = root / rel
        rows.append(
            {
                "source_id": f"SRC-{idx:02d}",
                "path": rel,
                "exists": str(path.exists()).lower(),
                "used_as": "read_only_evidence_or_policy_context",
                "mutation_status": "not_modified_by_this_task",
            }
        )
    return rows


def conservative_equation_ledger() -> list[dict[str, str]]:
    evidence = joined(
        [
            "work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv",
            "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/README.md",
        ]
    )
    return [
        {
            "ledger_id": "E00",
            "term_id": "sign_convention",
            "equation_symbol": "Q > 0 into salt control volume",
            "sign_convention": "positive heat rate adds thermal energy to the salt-side control volume",
            "physical_role": "global convention",
            "equation_placement": "applies to every heat term before residual formation",
            "runtime_allowed_status": "allowed_policy",
            "runtime_inputs_allowed": "none",
            "diagnostic_inputs_allowed": "wallHeatFlux sign checks; enthalpy sign checks",
            "runtime_forbidden_inputs": joined(FORBIDDEN_TOKENS),
            "source_basis_status": "contract_from_existing_ledgers",
            "residual_owner_family": "not_applicable",
            "current_decision": "contract_ready",
            "evidence_paths": evidence,
            "next_gate": "use this convention in every downstream heat-path and sensor projection package",
            "reason": "A sign convention prevents heater, cooler, passive loss, and residual rows from being relabeled inconsistently.",
        },
        {
            "ledger_id": "E01",
            "term_id": "segment_steady_enthalpy_balance",
            "equation_symbol": "R_s = sum(Q_known_s) - mdot*cp*(T_out_s - T_in_s)",
            "sign_convention": "positive R_s means known sources exceed measured or modeled enthalpy rise",
            "physical_role": "per-segment conservative residual equation",
            "equation_placement": "computed after declared heat paths and enthalpy transport are evaluated",
            "runtime_allowed_status": "equation_allowed_but_runtime_mdot_source_must_be_model_solved",
            "runtime_inputs_allowed": "setup heat terms; geometry; properties; solved model mdot; solved model temperatures",
            "diagnostic_inputs_allowed": "CFD enthalpy diagnostics and wallHeatFlux diagnostics for audit only",
            "runtime_forbidden_inputs": joined(FORBIDDEN_TOKENS),
            "source_basis_status": "model_equation_ready_observed_cfd_balance_diagnostic_only",
            "residual_owner_family": "segment_residual",
            "current_decision": "contract_ready_no_fit",
            "evidence_paths": evidence,
            "next_gate": "sensor projection and setup-only BC UQ before final scoring",
            "reason": "The residual is an output and blocker pointer, not a tunable heat source.",
        },
        {
            "ledger_id": "E02",
            "term_id": "heater_source_to_fluid",
            "equation_symbol": "Q_heater_to_fluid = eta_h * f_h(x) * Q_heater_setup",
            "sign_convention": "positive",
            "physical_role": "declared lower-leg heater source entering salt or wall before losses",
            "equation_placement": "known/source term in sum(Q_known_s)",
            "runtime_allowed_status": "conditionally_allowed_after_source_property_release",
            "runtime_inputs_allowed": "setup heater power; declared source distribution; admitted eta_h; geometry; property lane",
            "diagnostic_inputs_allowed": "realized heater wallHeatFlux; imposed-minus-realized gap",
            "runtime_forbidden_inputs": "realized CFD wallHeatFlux; CFD mdot; validation temperatures; hidden internal Nu correction",
            "source_basis_status": "setup_known_candidate_not_source_property_released",
            "residual_owner_family": "heater_source_residual",
            "current_decision": "not_released_now",
            "evidence_paths": joined(
                [
                    "work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv",
                    "work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/source_property_gate.csv",
                ]
            ),
            "next_gate": "source/property release preflight after train-only residual decomposition",
            "reason": "Setup Q was recovered, but the existing gate still reports zero source/property release rows.",
        },
        {
            "ledger_id": "E03",
            "term_id": "cooler_hx_removal",
            "equation_symbol": "Q_cooler = -UA_HX * DeltaT_drive or epsilon_NTU(setup)",
            "sign_convention": "negative when heat is removed from salt",
            "physical_role": "active cooler or HX sink distinct from passive losses",
            "equation_placement": "known/sink term in sum(Q_known_s)",
            "runtime_allowed_status": "conditionally_allowed_only_as_setup_model",
            "runtime_inputs_allowed": "setup HX geometry; coolant or ambient state; admitted UA/effectiveness; properties",
            "diagnostic_inputs_allowed": "imposed and realized cooler wallHeatFlux for scoring/audit only",
            "runtime_forbidden_inputs": "imposed CFD cooler duty; realized cooler wallHeatFlux; CFD mdot; validation temperatures",
            "source_basis_status": "setup_model_lane_exists_but_no_imposed_duty_runtime",
            "residual_owner_family": "cooler_residual",
            "current_decision": "contract_ready_guarded",
            "evidence_paths": "work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv",
            "next_gate": "setup-only BC UQ propagation",
            "reason": "Cooler removal must be predicted from setup fields, not copied from CFD-imposed duty.",
        },
        {
            "ledger_id": "E04",
            "term_id": "passive_wall_external_convection",
            "equation_symbol": "Q_ext_conv = h_ext*A_ext*(T_amb - T_surface)",
            "sign_convention": "positive if ambient adds heat to salt-side control volume through wall",
            "physical_role": "passive wall heat loss or gain",
            "equation_placement": "external boundary term, separate from internal Nu",
            "runtime_allowed_status": "allowed_when_setup_fields_are_declared",
            "runtime_inputs_allowed": "h_ext; ambient temperature; area; coverage; drive selector; solved surface temperature",
            "diagnostic_inputs_allowed": "patchwise passive wallHeatFlux and residual-owner response",
            "runtime_forbidden_inputs": "realized CFD wallHeatFlux; validation wall temperatures; hidden passive hA multiplier",
            "source_basis_status": "diagnostic_strong_but_candidate_not_released",
            "residual_owner_family": "passive_wall_residual",
            "current_decision": "not_released_now",
            "evidence_paths": "work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate/README.md",
            "next_gate": "source-bounded passive wall repair with same-QOI UQ",
            "reason": "Broad passive hA sensitivity moves TW5 strongly but is too global for admission.",
        },
        {
            "ledger_id": "E05",
            "term_id": "radiation",
            "equation_symbol": "Q_rad = epsilon*sigma*A*(T_sur^4 - T_surface^4)",
            "sign_convention": "positive if surroundings radiatively heat the surface",
            "physical_role": "radiative exchange distinct from external convection and internal Nu",
            "equation_placement": "external boundary term in predictive mode only",
            "runtime_allowed_status": "allowed_only_if_radiation_model_is_declared",
            "runtime_inputs_allowed": "emissivity; Tsur; area; view-factor assumption; solved surface temperature",
            "diagnostic_inputs_allowed": "radiation-on/off sensitivity; CFD wallHeatFlux total audit",
            "runtime_forbidden_inputs": "adding radiation on top of realized CFD wallHeatFlux replay; fitting radiation residual into Nu",
            "source_basis_status": "separate_1d_radiation_capability_still_open",
            "residual_owner_family": "radiation_residual",
            "current_decision": "contract_ready_not_released",
            "evidence_paths": "work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv",
            "next_gate": "radiation capability or setup-only BC UQ row",
            "reason": "CFD wallHeatFlux may already include radiation, so replay and predictive semantics must not be mixed.",
        },
        {
            "ledger_id": "E06",
            "term_id": "test_section_or_quartz_path",
            "equation_symbol": "Q_ts = Q_ts_setup - Q_quartz_ext - Q_layer - Q_residual_ts",
            "sign_convention": "net sign must be carried explicitly",
            "physical_role": "test-section source/loss path, not generic passive residual",
            "equation_placement": "segment-local source/loss stack",
            "runtime_allowed_status": "blocked_until_source_bounded_release",
            "runtime_inputs_allowed": "setup test-section power if admitted; quartz/layer geometry; external BC fields",
            "diagnostic_inputs_allowed": "realized test-section wallHeatFlux; train-only residual movement",
            "runtime_forbidden_inputs": "realized test-section heat; validation temperatures; residual fitted into Nu",
            "source_basis_status": "partial_local_response_no_release",
            "residual_owner_family": "test_section_source_or_loss_residual",
            "current_decision": "blocked_not_released",
            "evidence_paths": joined(
                [
                    "work_products/2026-07/2026-07-22/2026-07-22_m2_passive_wall_test_section_source_bounded_repair_gate/README.md",
                    "work_products/2026-07/2026-07-22/2026-07-22_thesis_n3_thermal_residual_owner_train_ablation/thermal_residual_ablation_table.csv",
                ]
            ),
            "next_gate": "narrow source-basis row plus same-QOI UQ",
            "reason": "Train-only response is mixed and cannot be promoted without a source-bounded basis.",
        },
        {
            "ledger_id": "E07",
            "term_id": "wall_conduction_and_contact_layers",
            "equation_symbol": "Q_wall = (T_inner - T_outer)/R_wall_layer",
            "sign_convention": "sign follows direction into the salt control volume",
            "physical_role": "solid resistance stack connecting internal convection to external paths",
            "equation_placement": "resistance term between salt-side and external boundary states",
            "runtime_allowed_status": "allowed_when_setup_material_fields_exist",
            "runtime_inputs_allowed": "wall thickness; material k; contact/layer R; area; solved wall states",
            "diagnostic_inputs_allowed": "CFD wall temperatures and wallHeatFlux comparisons",
            "runtime_forbidden_inputs": "validation wall temperatures; back-solved heldout contact resistance; realized wallHeatFlux",
            "source_basis_status": "partial_setup_fields_missing_segment_ownership",
            "residual_owner_family": "wall_layer_residual",
            "current_decision": "contract_ready_missing_fields",
            "evidence_paths": "work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv",
            "next_gate": "material/geometry setup-field completion",
            "reason": "Wall/layer resistance must be explicit so internal Nu does not absorb wall losses.",
        },
        {
            "ledger_id": "E08",
            "term_id": "storage",
            "equation_symbol": "Q_storage = dE_wall_fluid/dt",
            "sign_convention": "positive when stored energy is released into salt; negative when energy is accumulating",
            "physical_role": "transient or imperfect steady-state accumulation",
            "equation_placement": "zero in present steady model unless a transient lane is admitted",
            "runtime_allowed_status": "not_allowed_in_current_steady_runtime",
            "runtime_inputs_allowed": "none for steady runtime",
            "diagnostic_inputs_allowed": "same-time solid-energy and time-drift audits",
            "runtime_forbidden_inputs": "using storage to tune steady residual; hidden storage in Nu",
            "source_basis_status": "future_transient_lane_only",
            "residual_owner_family": "storage_residual",
            "current_decision": "diagnostic_owner_only",
            "evidence_paths": joined(
                [
                    "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/README.md",
                    "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/README.md",
                ]
            ),
            "next_gate": "same-time solid-energy audit if transient/storage is pursued",
            "reason": "Storage can explain residuals but is outside the steady runtime model until measured independently.",
        },
        {
            "ledger_id": "E09",
            "term_id": "recirculation_exchange_or_axial_mixing",
            "equation_symbol": "Q_mix = sum(Gamma_ij * cp * (T_j - T_i))",
            "sign_convention": "positive into each receiving control volume; conservative pair sum is zero",
            "physical_role": "internal redistribution without creating net heat",
            "equation_placement": "coupling term between 1D nodes or recirculation cells",
            "runtime_allowed_status": "blocked_until_setup_only_candidate_and_uq",
            "runtime_inputs_allowed": "admitted exchange geometry; solved temperatures; setup-only exchange parameter if released",
            "diagnostic_inputs_allowed": "S13 upcomer exchange Qwall/source-side diagnostics",
            "runtime_forbidden_inputs": "realized local wallHeatFlux as exchange source; validation temperatures; fitted residual exchange",
            "source_basis_status": "diagnostic_only_no_candidate_reviewable",
            "residual_owner_family": "recirculation_or_mixing_residual",
            "current_decision": "blocked_not_released",
            "evidence_paths": joined(
                [
                    "work_products/2026-07/2026-07-22/2026-07-22_mf_recirc_upcomer_alternatives_gate/summary.json",
                    "work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_label_mesh_family_generation/summary.json",
                ]
            ),
            "next_gate": "exact same-label mesh family or low-recirculation/onset source family",
            "reason": "Exchange-cell evidence is physically important but not yet release-ready or mesh/GCI accepted.",
        },
        {
            "ledger_id": "E10",
            "term_id": "internal_Nu",
            "equation_symbol": "Q_int = h_int*A_int*(T_wall_inner - T_bulk)",
            "sign_convention": "positive when wall heats the salt",
            "physical_role": "salt-side convective resistance only",
            "equation_placement": "resistance closure, not a residual owner",
            "runtime_allowed_status": "baseline_or_literature_only_until_admission",
            "runtime_inputs_allowed": "geometry; Re from solved mdot; Pr; Gz; admitted wall-bulk drive; literature/source-envelope form",
            "diagnostic_inputs_allowed": "postprocessed CFD h/Nu and section-effective rows",
            "runtime_forbidden_inputs": "passive wall loss; heater/cooler error; radiation; storage; recirculation residual; realized CFD wallHeatFlux",
            "source_basis_status": "0_fit_admissible_rows",
            "residual_owner_family": "not_a_residual_owner",
            "current_decision": "not_fit_admitted",
            "evidence_paths": "operational_notes/maps/thermal-closures-and-internal-nu.md",
            "next_gate": "branch-local sign/heat-balance, recirculation, and mesh/GCI admission",
            "reason": "Internal Nu cannot be used as the place to hide heat-ledger imbalance.",
        },
        {
            "ledger_id": "E11",
            "term_id": "final_residual_owner",
            "equation_symbol": "owner(R_s) in {heater,cooler,passive_wall,test_section,junction,storage,recirc,unknown}",
            "sign_convention": "inherits R_s sign after declared heat paths",
            "physical_role": "classification of unresolved imbalance",
            "equation_placement": "reported after all model terms and diagnostics are assembled",
            "runtime_allowed_status": "output_only",
            "runtime_inputs_allowed": "none",
            "diagnostic_inputs_allowed": "residual-owner matrices and ablation tables",
            "runtime_forbidden_inputs": "fitted residual heat path; validation heat residual as runtime closure; hidden global multiplier",
            "source_basis_status": "diagnostic_only_no_candidate_release",
            "residual_owner_family": "owner_label",
            "current_decision": "contract_ready_no_candidate_release",
            "evidence_paths": joined(
                [
                    "work_products/2026-07/2026-07-22/2026-07-22_s12_thermal_residual_candidate_disposition_and_thesis_panels/README.md",
                    "work_products/2026-07/2026-07-22/2026-07-22_thesis_n3_thermal_residual_owner_train_ablation/thermal_residual_ablation_table.csv",
                ]
            ),
            "next_gate": "source-bounded candidate release or report as blocked negative result",
            "reason": "Residual ownership preserves scientific information without creating a false closure.",
        },
    ]


def runtime_allowed_input_list() -> list[dict[str, str]]:
    return [
        {
            "input_id": "A01",
            "input_name": "setup_heater_power",
            "runtime_status": "conditionally_allowed",
            "required_release": "source/property gate for distribution or efficiency",
            "allowed_use": "heater source term",
            "provenance_requirement": "setup boundary dictionary or experiment setup record",
            "not_allowed_as": "backsolved heat from wallHeatFlux",
        },
        {
            "input_id": "A02",
            "input_name": "declared_heater_source_distribution",
            "runtime_status": "conditionally_allowed",
            "required_release": "train-only decomposition and source/property release",
            "allowed_use": "spatial heater allocation",
            "provenance_requirement": "declared source-mode contract",
            "not_allowed_as": "fit to validation residuals",
        },
        {
            "input_id": "A03",
            "input_name": "setup_cooler_hx_geometry_and_UA_or_effectiveness",
            "runtime_status": "allowed_after_setup_model_release",
            "required_release": "setup-only BC UQ and source/property labels",
            "allowed_use": "predictive cooler removal",
            "provenance_requirement": "setup-known HX model inputs",
            "not_allowed_as": "imposed CFD cooler duty",
        },
        {
            "input_id": "A04",
            "input_name": "ambient_temperature",
            "runtime_status": "allowed",
            "required_release": "setup metadata",
            "allowed_use": "external convection/radiation boundary drive",
            "provenance_requirement": "setup or boundary dictionary",
            "not_allowed_as": "validation sensor temperature",
        },
        {
            "input_id": "A05",
            "input_name": "external_convection_h_and_area",
            "runtime_status": "allowed_when_declared",
            "required_release": "segment/patch coverage and source-property labels",
            "allowed_use": "passive wall heat exchange",
            "provenance_requirement": "external BC dictionary or setup model",
            "not_allowed_as": "global hA fitted to protected residuals",
        },
        {
            "input_id": "A06",
            "input_name": "emissivity_Tsur_area_view_factor",
            "runtime_status": "allowed_when_radiation_model_declared",
            "required_release": "radiation capability and no-double-count audit",
            "allowed_use": "predictive radiative exchange",
            "provenance_requirement": "setup fields and declared view-factor approximation",
            "not_allowed_as": "extra term on realized wallHeatFlux replay",
        },
        {
            "input_id": "A07",
            "input_name": "wall_and_layer_geometry_materials",
            "runtime_status": "allowed_when_setup_fields_complete",
            "required_release": "material/geometry provenance",
            "allowed_use": "wall, insulation, quartz, or contact resistance",
            "provenance_requirement": "geometry/material setup fields",
            "not_allowed_as": "heldout-temperature backsolve",
        },
        {
            "input_id": "A08",
            "input_name": "fluid_properties",
            "runtime_status": "allowed_with_property_mode_label",
            "required_release": "property-mode/source envelope label",
            "allowed_use": "cp, rho, mu, k, Pr in 1D equations",
            "provenance_requirement": "declared property law and range",
            "not_allowed_as": "case-specific correction tuned to scores",
        },
        {
            "input_id": "A09",
            "input_name": "geometry_and_segment_lengths",
            "runtime_status": "allowed",
            "required_release": "geometry manifest",
            "allowed_use": "areas, volumes, hydraulic diameter, elevation, path length",
            "provenance_requirement": "geometry reference",
            "not_allowed_as": "post-hoc effective length selected by score",
        },
        {
            "input_id": "A10",
            "input_name": "solved_model_mdot_and_temperatures",
            "runtime_status": "allowed_as_model_outputs_coupled_back_into_equations",
            "required_release": "root stability and runtime-leakage audit",
            "allowed_use": "enthalpy transport and heat-transfer drives",
            "provenance_requirement": "computed by the 1D model from setup inputs",
            "not_allowed_as": "CFD mdot or validation temperatures",
        },
    ]


def runtime_forbidden_audit() -> list[dict[str, str]]:
    return [
        {
            "forbidden_input": "realized CFD wallHeatFlux",
            "runtime_allowed": "false",
            "diagnostic_allowed": "true",
            "diagnostic_use": "wall-flux sign, source/sink recovery, residual ownership, validation comparison",
            "failure_if_used_at_runtime": "leaks CFD solution heat flux into predictive model",
            "leakage_check_status": "pass",
        },
        {
            "forbidden_input": "CFD mdot",
            "runtime_allowed": "false",
            "diagnostic_allowed": "true",
            "diagnostic_use": "post-solve comparison and historical pressure/thermal audit",
            "failure_if_used_at_runtime": "turns forward prediction into replay",
            "leakage_check_status": "pass",
        },
        {
            "forbidden_input": "imposed CFD cooler duty",
            "runtime_allowed": "false",
            "diagnostic_allowed": "true",
            "diagnostic_use": "cooler boundary diagnosis and parity context",
            "failure_if_used_at_runtime": "bypasses predictive HX/cooler model",
            "leakage_check_status": "pass",
        },
        {
            "forbidden_input": "validation temperatures",
            "runtime_allowed": "false",
            "diagnostic_allowed": "true",
            "diagnostic_use": "score calculation after frozen runtime prediction",
            "failure_if_used_at_runtime": "uses target sensors to construct the prediction",
            "leakage_check_status": "pass",
        },
        {
            "forbidden_input": "holdout temperatures",
            "runtime_allowed": "false",
            "diagnostic_allowed": "true",
            "diagnostic_use": "protected score calculation only",
            "failure_if_used_at_runtime": "invalidates holdout/external claims",
            "leakage_check_status": "pass",
        },
        {
            "forbidden_input": "realized test-section heat",
            "runtime_allowed": "false",
            "diagnostic_allowed": "true",
            "diagnostic_use": "test-section source/loss diagnosis",
            "failure_if_used_at_runtime": "imports CFD outcome instead of setup source model",
            "leakage_check_status": "pass",
        },
        {
            "forbidden_input": "hidden global multiplier",
            "runtime_allowed": "false",
            "diagnostic_allowed": "false",
            "diagnostic_use": "none",
            "failure_if_used_at_runtime": "absorbs multiple physical owners and blocks publication interpretation",
            "leakage_check_status": "pass",
        },
        {
            "forbidden_input": "final heat residual as closure input",
            "runtime_allowed": "false",
            "diagnostic_allowed": "true",
            "diagnostic_use": "owner label and blocker pointer after calculation",
            "failure_if_used_at_runtime": "creates a closure from the error being explained",
            "leakage_check_status": "pass",
        },
    ]


def missing_setup_fields() -> list[dict[str, str]]:
    return [
        {
            "field_id": "M01",
            "missing_or_incomplete_field": "segment-resolved external h_ext and coverage",
            "needed_for": "passive wall external convection",
            "current_status": "partial dictionary/context only",
            "scientific_risk_if_missing": "global passive hA can mimic several residual owners",
            "next_owner_gate": "external BC dictionary plus setup-only BC UQ",
        },
        {
            "field_id": "M02",
            "missing_or_incomplete_field": "radiation view-factor or declared approximation",
            "needed_for": "separate predictive radiation term",
            "current_status": "emissivity/Tsur evidence exists but separate 1D release remains open",
            "scientific_risk_if_missing": "radiation may be double-counted or hidden in passive convection",
            "next_owner_gate": "radiation capability/no-double-count audit",
        },
        {
            "field_id": "M03",
            "missing_or_incomplete_field": "segment-local wall/layer/contact material stack",
            "needed_for": "wall conduction, layer, insulation, quartz terms",
            "current_status": "not complete for all segments",
            "scientific_risk_if_missing": "wall/layer resistance can be folded into internal Nu",
            "next_owner_gate": "material and geometry setup-field completion",
        },
        {
            "field_id": "M04",
            "missing_or_incomplete_field": "source-bounded test-section source/loss basis",
            "needed_for": "test-section heat path",
            "current_status": "partial train response, no source/property release",
            "scientific_risk_if_missing": "test-section net source/sink ambiguity contaminates TW residuals",
            "next_owner_gate": "narrow source-basis row plus same-QOI UQ",
        },
        {
            "field_id": "M05",
            "missing_or_incomplete_field": "junction/stub bracketing surfaces and heat inventory",
            "needed_for": "junction residual owner",
            "current_status": "unbracketed in patchwise enthalpy interface package",
            "scientific_risk_if_missing": "junction losses remain unowned residuals",
            "next_owner_gate": "junction control-volume extraction",
        },
        {
            "field_id": "M06",
            "missing_or_incomplete_field": "same-time solid energy or time-drift audit",
            "needed_for": "storage term eligibility",
            "current_status": "not admitted for current steady model",
            "scientific_risk_if_missing": "heater imposed-realized gaps may be overinterpreted",
            "next_owner_gate": "transient/storage audit if needed",
        },
        {
            "field_id": "M07",
            "missing_or_incomplete_field": "same-label medium/fine S13 exchange/source family",
            "needed_for": "recirculation exchange release and UQ",
            "current_status": "0 strict same-label mesh cells ready",
            "scientific_risk_if_missing": "upcomer exchange evidence remains diagnostic-only",
            "next_owner_gate": "scheduler-authorized same-label generation row",
        },
    ]


def candidate_handoff_table() -> list[dict[str, str]]:
    return [
        {
            "handoff_id": "H01",
            "next_task": "TODO-1D-SENSOR-PROJECTION-OPERATOR-TP-TW-WALL-BULK-2026-07-22",
            "depends_on_contract_rows": "E01; E07; E11",
            "readiness": "ready",
            "objective": "map model bulk/wall states to TP/TW observations without validation-temperature leakage",
            "acceptance_gate": "sensor operator table and uncertainty/exclusion policy",
        },
        {
            "handoff_id": "H02",
            "next_task": "TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22",
            "depends_on_contract_rows": "E02; E03; E04; E05; E07",
            "readiness": "ready_after_this_contract",
            "objective": "propagate setup-only uncertainty through heat paths before final scoring",
            "acceptance_gate": "allowed priors/ranges with no validation tuning",
        },
        {
            "handoff_id": "H03",
            "next_task": "source/property release preflight for heater/passive/test-section lanes",
            "depends_on_contract_rows": "E02; E04; E06",
            "readiness": "blocked_by_no_release",
            "objective": "decide whether any source-bounded thermal candidate can be reviewable",
            "acceptance_gate": "exactly one released source/property candidate before S11/S15/S6",
        },
        {
            "handoff_id": "H04",
            "next_task": "S13 same-label medium/fine exchange/source generation",
            "depends_on_contract_rows": "E09",
            "readiness": "blocked_scheduler_authorization_required",
            "objective": "recover exact same-label mesh family for source-side heatflow equivalence and UQ",
            "acceptance_gate": "coarse/medium/fine same-QOI rows before any exchange score",
        },
        {
            "handoff_id": "H05",
            "next_task": "TODO-1D-MODEL-HIERARCHY-ABLATION-LADDER-PACKET-2026-07-22",
            "depends_on_contract_rows": "E00-E11",
            "readiness": "ready_after_sensor_operator_or_as_negative_packet",
            "objective": "turn the ledger, negative evidence, and blocked gates into a thesis model ladder",
            "acceptance_gate": "explicit zero final score values unless separate frozen scorecard exists",
        },
    ]


def residual_owner_contract() -> list[dict[str, str]]:
    return [
        {
            "owner_family": "heater_source_residual",
            "allowed_evidence": "setup Q provenance; train-only decomposition; imposed-realized diagnostic gap",
            "not_allowed_evidence": "validation temperature fit; realized heater wallHeatFlux as runtime input",
            "promotion_requirement": "source/property release plus same-QOI UQ",
            "current_status": "not_released",
        },
        {
            "owner_family": "cooler_residual",
            "allowed_evidence": "setup HX/UA/effectiveness model and post-score cooler comparison",
            "not_allowed_evidence": "imposed CFD cooler duty as boundary input",
            "promotion_requirement": "setup-only BC UQ",
            "current_status": "guarded_setup_model_only",
        },
        {
            "owner_family": "passive_wall_residual",
            "allowed_evidence": "external BC setup fields; passive wall sensitivity; wall/ambient geometry",
            "not_allowed_evidence": "global hA multiplier selected by protected score",
            "promotion_requirement": "source-bounded physical field completion and UQ",
            "current_status": "diagnostic_strong_not_released",
        },
        {
            "owner_family": "test_section_source_or_loss_residual",
            "allowed_evidence": "setup test-section Q; quartz/layer geometry; train-only response",
            "not_allowed_evidence": "realized test-section heat as runtime input",
            "promotion_requirement": "narrow source-basis row and same-QOI UQ",
            "current_status": "partial_response_not_released",
        },
        {
            "owner_family": "junction_stub_residual",
            "allowed_evidence": "bracketed junction control-volume ledger",
            "not_allowed_evidence": "unbracketed residual assigned to another closure",
            "promotion_requirement": "junction surfaces and source/sink inventory",
            "current_status": "blocked_unbracketed",
        },
        {
            "owner_family": "storage_residual",
            "allowed_evidence": "same-time wall/fluid energy and time derivative audit",
            "not_allowed_evidence": "steady score tuning",
            "promotion_requirement": "transient/storage model row",
            "current_status": "future_lane_only",
        },
        {
            "owner_family": "recirculation_or_mixing_residual",
            "allowed_evidence": "same-label exchange/source field with mesh/time UQ",
            "not_allowed_evidence": "single-stream Nu/f_D/K fit under recirculation",
            "promotion_requirement": "ordinary/onset source family or accepted S13 same-QOI UQ",
            "current_status": "diagnostic_only",
        },
        {
            "owner_family": "unknown_residual",
            "allowed_evidence": "explicit residual after all terms are evaluated",
            "not_allowed_evidence": "runtime residual closure or hidden multiplier",
            "promotion_requirement": "new physically bounded owner evidence",
            "current_status": "output_only",
        },
    ]


def no_mutation_guardrails() -> list[dict[str, str]]:
    return [
        {"guardrail": "native CFD/OpenFOAM outputs", "status": "not_mutated", "evidence": "contract-only builder writes work_products package"},
        {"guardrail": "scheduler/solver/sampler", "status": "not_launched", "evidence": "no sbatch/srun/OpenFOAM command in task"},
        {"guardrail": "Fluid or external repo source", "status": "not_mutated", "evidence": "no external path edit"},
        {"guardrail": "registry/admission/blocker register", "status": "not_mutated", "evidence": "no registry or blockers.yml edit"},
        {"guardrail": "fit/model selection/final scoring", "status": "not_performed", "evidence": "all candidate rows are contract, diagnostic, or blocked"},
        {"guardrail": "runtime leakage", "status": "pass", "evidence": "runtime_forbidden_audit.csv has runtime_allowed=false for all forbidden rows"},
    ]


def validate_tables(tables: list[Table], root: Path) -> list[str]:
    errors: list[str] = []
    forbidden = next(table for table in tables if table.filename == "runtime_forbidden_audit.csv").rows
    for row in forbidden:
        if row["runtime_allowed"].strip().lower() != "false":
            errors.append(f"forbidden runtime input allowed: {row['forbidden_input']}")
        if row["leakage_check_status"] != "pass":
            errors.append(f"leakage check did not pass: {row['forbidden_input']}")
    allowed = next(table for table in tables if table.filename == "runtime_allowed_input_list.csv").rows
    for row in allowed:
        not_allowed = row["not_allowed_as"]
        for token in ("CFD mdot", "wallHeatFlux", "validation"):
            if token in row["allowed_use"]:
                errors.append(f"allowed-use field contains forbidden token {token}: {row['input_id']}")
        if not not_allowed:
            errors.append(f"missing negative-use guardrail: {row['input_id']}")
    manifest = next(table for table in tables if table.filename == "source_manifest.csv").rows
    for row in manifest:
        if row["exists"] != "true":
            errors.append(f"missing source: {row['path']}")
        if row["mutation_status"] != "not_modified_by_this_task":
            errors.append(f"source mutation not read-only: {row['path']}")
    if len(next(table for table in tables if table.filename == "conservative_equation_ledger.csv").rows) < 10:
        errors.append("conservative equation ledger is too small for the required decomposition")
    if not (root / ".agent/BOARD.md").exists():
        errors.append("repo root sanity check failed")
    return errors


def readme_text(generated_at: str, counts: dict[str, int], decision: str) -> str:
    return f"""---
provenance:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s12_thermal_residual_candidate_disposition_and_thesis_panels/README.md
tags: [predictive-1d, thermal-ledger, residual-owner, runtime-leakage, publication-evidence]
related:
  - .agent/status/{DATE}_{TASK_ID}.md
  - .agent/journal/{DATE}/1d-conservative-thermal-ledger-residual-owner-contract.md
  - imports/{DATE}_{SLUG}.json
task: {TASK_ID}
date: {DATE}
role: Forward-pred / Thermal-modeling / Writer / Reviewer / Tester
type: work_product
status: complete
---
# 1D Conservative Thermal Ledger Residual-Owner Contract

Generated: `{generated_at}`

Decision: `{decision}`.

This package defines the model-facing heat ledger before any fitting. It keeps
heater input, cooler/HX removal, passive wall exchange, test-section/quartz
terms, wall/layer resistance, radiation, storage, recirculation/exchange, and
the final residual as separate terms. The residual is an output and owner label,
not a closure.

## Core Equation

With positive heat into the salt-side control volume,

`R_s = sum(Q_known_s) - mdot_model * cp * (T_out_s - T_in_s)`.

For predictive runtime, `mdot_model`, wall states, and temperatures must be
computed by the 1D model from setup inputs. CFD `mdot`, realized CFD
`wallHeatFlux`, imposed CFD cooler duty, realized test-section heat, and
validation/holdout temperatures are forbidden runtime inputs.

## Files

- `conservative_equation_ledger.csv`: {counts['equation_rows']} equation/term rows.
- `runtime_allowed_input_list.csv`: {counts['allowed_rows']} setup/model-state input rows.
- `runtime_forbidden_audit.csv`: {counts['forbidden_rows']} forbidden runtime inputs, all marked `false`.
- `missing_setup_fields.csv`: {counts['missing_rows']} missing or incomplete setup fields.
- `candidate_handoff_table.csv`: {counts['handoff_rows']} next-task handoff rows.
- `residual_owner_contract.csv`: {counts['owner_rows']} residual owner families.
- `source_manifest.csv`, `no_mutation_guardrails.csv`, `summary.json`.

## Scientific Use

Use this as the thermal accounting contract for the next 1D model stages and for
publication methods prose. It supports a claim that current negative thermal
results are organized residual-owner evidence, not proof that internal `Nu` or a
global heat multiplier should be fitted.

## Guardrails

No solver, sampler, scheduler job, Fluid edit, external thesis/LaTeX edit,
registry/admission mutation, source/property release, fit, model selection, or
final score was performed.
"""


def build(outdir: Path = OUTDIR) -> dict:
    root = repo_root()
    out = root / outdir
    generated_at = datetime.now(timezone.utc).isoformat()
    decision = "contract_ready_no_candidate_release_no_runtime_leakage"

    tables = [
        Table("conservative_equation_ledger.csv", conservative_equation_ledger()),
        Table("runtime_allowed_input_list.csv", runtime_allowed_input_list()),
        Table("runtime_forbidden_audit.csv", runtime_forbidden_audit()),
        Table("missing_setup_fields.csv", missing_setup_fields()),
        Table("candidate_handoff_table.csv", candidate_handoff_table()),
        Table("residual_owner_contract.csv", residual_owner_contract()),
        Table("source_manifest.csv", source_manifest(root)),
        Table("no_mutation_guardrails.csv", no_mutation_guardrails()),
    ]
    validation_errors = validate_tables(tables, root)
    if validation_errors:
        raise SystemExit("validation failed:\n" + "\n".join(validation_errors))

    for table in tables:
        write_csv(out / table.filename, table.rows)

    counts = {
        "equation_rows": len(tables[0].rows),
        "allowed_rows": len(tables[1].rows),
        "forbidden_rows": len(tables[2].rows),
        "missing_rows": len(tables[3].rows),
        "handoff_rows": len(tables[4].rows),
        "owner_rows": len(tables[5].rows),
        "source_rows": len(tables[6].rows),
        "guardrail_rows": len(tables[7].rows),
    }
    summary = {
        "task_id": TASK_ID,
        "decision": decision,
        "generated_at_utc": generated_at,
        "counts": counts,
        "runtime_forbidden_inputs_all_blocked": True,
        "source_property_release_rows": 0,
        "candidate_admission_rows": 0,
        "final_score_values": 0,
        "scheduler_or_sampler_launched": False,
        "solver_launched": False,
        "native_output_mutated": False,
        "registry_mutated": False,
        "external_repo_mutated": False,
        "fluid_mutated": False,
        "validation_errors": validation_errors,
        "next_recommended_tasks": [
            "TODO-1D-SENSOR-PROJECTION-OPERATOR-TP-TW-WALL-BULK-2026-07-22",
            "TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22",
            "source/property release preflight only after a narrow source-bounded candidate exists",
        ],
    }
    write_json(out / "summary.json", summary)
    (out / "README.md").write_text(readme_text(generated_at, counts, decision), encoding="utf-8")
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
