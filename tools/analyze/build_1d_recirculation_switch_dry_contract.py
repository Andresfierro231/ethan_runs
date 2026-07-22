#!/usr/bin/env python3
"""Build a dry three-lane recirculation model-form switch contract."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump


TASK_ID = "TODO-1D-RECIRCULATION-SWITCH-DRY-CONTRACT-2026-07-22"
DATE = "2026-07-22"
SLUG = "1d_recirculation_switch_dry_contract"
DEFAULT_OUT = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_recirculation_switch_dry_contract")

RECIRC_PACKET = Path("work_products/2026-07/2026-07-22/2026-07-22_thesis_study_recirculation_fraction_onset_evidence_packet")
MF09_PACKET = Path("work_products/2026-07/2026-07-22/2026-07-22_mf09_recirculating_upcomer_thermal_model_alternatives")
REGIME_PACKET = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility")
HIERARCHY_PACKET = Path("work_products/2026-07/2026-07-22/2026-07-22_1d_model_hierarchy_ablation_ladder_packet")
PRESSURE_ANCHOR_PACKET = Path("work_products/2026-07/2026-07-22/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory")
SOURCE_PROPERTY_PACKET = Path("work_products/2026-07/2026-07-22/2026-07-22_thesis_study_s12_thermal_source_property_freeze_gate")
SAMPLER_PACKET = Path("work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler")
LITREV_PACKET = Path("work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell")


SOURCE_PATHS = [
    RECIRC_PACKET / "recirculation_onset_metric_table.csv",
    RECIRC_PACKET / "evidence_availability_gate.csv",
    RECIRC_PACKET / "summary.json",
    MF09_PACKET / "ordinary_upcomer_disable_gate.csv",
    MF09_PACKET / "summary.json",
    REGIME_PACKET / "closure_eligibility_decisions.csv",
    HIERARCHY_PACKET / "model_hierarchy_ladder.csv",
    PRESSURE_ANCHOR_PACKET / "summary.json",
    SOURCE_PROPERTY_PACKET / "source_property_atlas.csv",
    SAMPLER_PACKET / "RUNNING.md",
    LITREV_PACKET / "switching_model_selection_contract.csv",
    LITREV_PACKET / "model_interface_contract.csv",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_out(out: str | Path | None) -> Path:
    if out is None:
        return repo_root() / DEFAULT_OUT
    path = Path(out)
    if path.is_absolute():
        return path
    return repo_root() / path


def read_csv(path: Path) -> list[dict[str, str]]:
    full = repo_root() / path
    with full.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads((repo_root() / path).read_text(encoding="utf-8"))


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1"}


def nfloat(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"


def status_lookup(rows: list[dict[str, str]], key: str) -> dict[str, str]:
    for row in rows:
        if row.get("evidence_item") == key:
            return row
    return {}


def source_property_row(rows: list[dict[str, str]], family: str) -> dict[str, str]:
    for row in rows:
        if row.get("candidate_family") == family:
            return row
    return {}


def build_model_form_gate_update(
    recirc_rows: list[dict[str, str]],
    mf09_rows: list[dict[str, str]],
    regime_rows: list[dict[str, str]],
    pressure_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    reverse_active = any((nfloat(row.get("reverse_candidate_fraction_of_right_leg_roi")) or 0.0) > 0.0 for row in recirc_rows)
    low_recirc_anchor_admitted = int(pressure_summary.get("sampled_endpoint_ordinary_flow_pass_rows", 0)) > 0
    mf09_by_id = {row["disabled_item"]: row for row in mf09_rows}
    regime_by_family = {row["model_family"]: row for row in regime_rows}
    common_reason = (
        "reverse-flow/recirculation evidence is active and no admitted low-recirculation "
        "or nonrecirculating anchor exists"
    )

    rows: list[dict[str, Any]] = []
    for claim_id, mf09_key in [
        ("ordinary_upcomer_Nu", "ordinary_upcomer_Nu_correction"),
        ("ordinary_upcomer_f_D", "ordinary_upcomer_f_D_or_component_K"),
        ("ordinary_upcomer_K", "ordinary_upcomer_f_D_or_component_K"),
        ("ordinary_upcomer_F6", "ordinary_upcomer_f_D_or_component_K"),
    ]:
        mf09 = mf09_by_id.get(mf09_key, {})
        rows.append(
            {
                "claim_id": claim_id,
                "model_form": "one_stream_upcomer",
                "current_gate": "disabled",
                "ordinary_claim_allowed_now": "false",
                "fit_allowed_now": "false",
                "admission_allowed_now": "false",
                "evidence_backed": str(reverse_active).lower(),
                "coefficient_backed": "false",
                "primary_reason": common_reason if reverse_active and not low_recirc_anchor_admitted else mf09.get("why", ""),
                "source_decision": mf09.get("why", ""),
                "unlock_condition": mf09.get("unlock_condition", ""),
            }
        )

    rows.append(
        {
            "claim_id": "signed_flow_junction_network_architecture",
            "model_form": "signed_flow_junction_network",
            "current_gate": "guarded_dry_fallback_not_net_branch_admission",
            "ordinary_claim_allowed_now": "false",
            "fit_allowed_now": "false",
            "admission_allowed_now": "false",
            "evidence_backed": str(reverse_active).lower(),
            "coefficient_backed": "false",
            "primary_reason": "mixed-sign/reverse-flow topology is active, while no closed exchange-cell volume/interface is admitted",
            "source_decision": regime_by_family.get("signed_flow_junction_network", {}).get("decision", ""),
            "unlock_condition": "topology-resolved signed path evidence before any network coefficient or component claim",
        }
    )
    rows.append(
        {
            "claim_id": "throughflow_plus_recirc_exchange_cell_architecture",
            "model_form": "throughflow_plus_recirc_exchange_cell",
            "current_gate": "architecture_defined_not_admitted",
            "ordinary_claim_allowed_now": "false",
            "fit_allowed_now": "false",
            "admission_allowed_now": "false",
            "evidence_backed": str(reverse_active).lower(),
            "coefficient_backed": "false",
            "primary_reason": "exchange/tau diagnostics motivate architecture, but closed CV/interface/wall-core band, same-QOI UQ, source/property validity, and mesh/GCI are not all admitted",
            "source_decision": regime_by_family.get("throughflow_recirc_exchange_cell", {}).get("decision", ""),
            "unlock_condition": "defensible CV, exchange interface, wall/core band, same-QOI UQ, mesh/GCI, and source/property release",
        }
    )
    rows.append(
        {
            "claim_id": "exchange_cell_coefficient_fit",
            "model_form": "throughflow_plus_recirc_exchange_cell",
            "current_gate": "disabled_no_fit",
            "ordinary_claim_allowed_now": "false",
            "fit_allowed_now": "false",
            "admission_allowed_now": "false",
            "evidence_backed": "false",
            "coefficient_backed": "false",
            "primary_reason": mf09_by_id.get("exchange_cell_coefficient_fit", {}).get("why", "coefficient evidence absent"),
            "source_decision": "no coefficient fitting in this package",
            "unlock_condition": mf09_by_id.get("exchange_cell_coefficient_fit", {}).get(
                "unlock_condition", "production harvest with mesh/GCI and temporal UQ"
            ),
        }
    )
    return rows


def build_lane_contract() -> list[dict[str, Any]]:
    return [
        {
            "lane_order": 1,
            "switch_output": "one_stream",
            "physical_state": "single throughflow state",
            "activation_rule": "allowed only when reverse-flow/recirculation evidence is inactive and low-recirculation or nonrecirculating anchors are admitted",
            "required_evidence": "no_reverse_flow_evidence_active; no_recirc_proxy_active; low_recirc_or_nonrecirc_anchor_admitted; source_property_runtime_basis_ok; mesh_uq_basis_if_any_fit",
            "current_evidence_status": "blocked_for_salt2_salt3_salt4",
            "current_coefficient_status": "not_applicable_no_fit",
            "allowed_claims_when_active": "ordinary one-stream branch balances may be evaluated only inside admitted low-recirculation envelopes",
            "forbidden_claims_when_inactive": "Nu/f_D/K/F6 upcomer claims from recirculating evidence",
            "fail_closed_state": "disabled_one_stream_claims",
        },
        {
            "lane_order": 2,
            "switch_output": "signed_flow_junction_network",
            "physical_state": "mixed-sign topology or flow reversal without admitted closed exchange cell",
            "activation_rule": "use when topology indicates flow reversal or mixed signs but no defensible recirculation CV and exchange interface are admitted",
            "required_evidence": "reverse_flow_or_mixed_sign_topology_active; closed_recirc_cv_not_admitted_or_exchange_interface_not_admitted; mass_residual_guardrail",
            "current_evidence_status": "guarded_dry_fallback_for_salt2_salt3_salt4",
            "current_coefficient_status": "no_network_K_or_F6_fit",
            "allowed_claims_when_active": "model-form switch output and signed residual diagnostics",
            "forbidden_claims_when_inactive": "component K/F6 admission; scalar tee K; pressure coefficient fitting",
            "fail_closed_state": "diagnostic_signed_flow_lane_no_coefficient_admission",
        },
        {
            "lane_order": 3,
            "switch_output": "throughflow_plus_recirc_exchange_cell",
            "physical_state": "net throughflow plus internally recirculating/exchanging cell",
            "activation_rule": "use only after a defensible recirculation CV, exchange interface, wall/core band, same-QOI UQ, source/property validity, and mesh/GCI evidence are admitted",
            "required_evidence": "closed_recirc_cv_admitted; exchange_interface_admitted; wall_core_band_admitted; same_qoi_uq_admitted; mesh_gci_admitted; source_property_valid",
            "current_evidence_status": "blocked_pending_cv_interface_wall_core_mesh_gci_source_property",
            "current_coefficient_status": "dry_architecture_only_no_exchange_coefficients",
            "allowed_claims_when_active": "diagnostic exchange-cell state variables and residual supports; later coefficient row only after separate admission",
            "forbidden_claims_when_inactive": "V_recirc/T_recirc/mdot_exchange as production coefficients; Q_wall release; closure fitting",
            "fail_closed_state": "exchange_cell_architecture_not_admitted",
        },
    ]


def build_runtime_inputs() -> list[dict[str, Any]]:
    rows = [
        ("setup_known_geometry", "segment_id", "runtime_allowed", "predeclared upcomer/branch/section identifier", "setup/case metadata", "not a CFD result"),
        ("setup_known_geometry", "hydraulic_diameter_m", "runtime_allowed", "geometry-known characteristic length", "geometry source", "must not be tuned from residuals"),
        ("setup_known_geometry", "segment_length_m", "runtime_allowed", "geometry-known axial/span length", "geometry source", "must not be inferred from validation fit"),
        ("setup_known_geometry", "orientation_and_gravity_vector", "runtime_allowed", "declared buoyancy direction basis", "setup/case metadata", "fixed before validation"),
        ("setup_known_geometry", "wall_core_band_mask_label", "future_allowed_after_admission", "identifier for admitted wall/core band", "recirc CV plus mesh face masks", "blocked until wall/core band is derived from same volume"),
        ("source_property", "heater_cooler_test_section_source_terms", "runtime_allowed_after_source_property_gate", "setup-known source/sink ledger labels", "source/property release gate", "no source-side Q as Q_wall substitute"),
        ("source_property", "rho_mu_cp_k_beta_property_model_labels", "runtime_allowed_after_source_property_gate", "fluid property model and evaluation basis", "source/property gate", "same-window property basis required for Ri and energy residuals"),
        ("predictive_indicator", "reverse_flow_indicator_predictive", "future_allowed_after_calibration", "setup-predictive regime/onset indicator", "future low-recirc/onset study", "current CFD reverse fraction is evidence label only, not runtime input"),
        ("predictive_indicator", "low_recirc_anchor_admitted", "runtime_allowed_as_gate_state", "boolean admission state from independent anchors", "pressure/onset anchor inventory", "required for one_stream"),
        ("predictive_indicator", "closed_recirc_cv_available", "runtime_allowed_as_gate_state", "boolean admission state for CV", "cell VTK segmentation package", "required for exchange-cell lane"),
        ("predictive_indicator", "exchange_interface_available", "runtime_allowed_as_gate_state", "boolean admission state for interface faces", "derived from recirc CV", "required for exchange-cell lane"),
        ("predictive_indicator", "wall_core_band_available", "runtime_allowed_as_gate_state", "boolean admission state for wall/core faces", "derived from recirc CV", "required for Q_wall/T_recirc contrast"),
        ("diagnostic_forbidden_runtime", "realized_CFD_velocity_field", "forbidden_runtime_input", "may support evidence labels only", "CFD harvest", "would leak validation state into predictive switch"),
        ("diagnostic_forbidden_runtime", "realized_CFD_wallHeatFlux", "forbidden_runtime_input", "may support diagnostic Qwall evidence only", "CFD harvest", "not a predictive input"),
        ("diagnostic_forbidden_runtime", "validation_temperature_targets", "forbidden_runtime_input", "score/diagnostic only", "experimental/validation targets", "not a runtime switch input"),
    ]
    return [
        {
            "input_class": item[0],
            "input_label": item[1],
            "runtime_status": item[2],
            "definition": item[3],
            "basis": item[4],
            "guardrail": item[5],
        }
        for item in rows
    ]


def build_qoi_interface_contract() -> list[dict[str, Any]]:
    return [
        {
            "qoi_label": "R_mu",
            "formula_or_definition": "mu_recirc / mu_main or admitted local viscosity ratio at the same property basis",
            "sign_or_basis": "dimensionless positive ratio",
            "current_status": "dry_slot_only_blocked_same_cv_property_basis",
            "coefficient_use_allowed": "false",
        },
        {
            "qoi_label": "R_rho",
            "formula_or_definition": "rho_recirc / rho_main or admitted local density ratio at the same property basis",
            "sign_or_basis": "dimensionless positive ratio",
            "current_status": "dry_slot_only_blocked_same_cv_property_basis",
            "coefficient_use_allowed": "false",
        },
        {
            "qoi_label": "V_recirc",
            "formula_or_definition": "sum cell volumes over admitted recirculation cell mask",
            "sign_or_basis": "m3; same CV as interface and wall/core band",
            "current_status": "blocked_closed_cv_not_admitted",
            "coefficient_use_allowed": "false",
        },
        {
            "qoi_label": "mdot_exchange",
            "formula_or_definition": "surface integral rho U dot n over admitted internal exchange faces",
            "sign_or_basis": "kg/s; positive from recirculation cell to main flow",
            "current_status": "diagnostic_proxy_only_current_coarse",
            "coefficient_use_allowed": "false",
        },
        {
            "qoi_label": "T_recirc",
            "formula_or_definition": "mass- or volume-weighted temperature over admitted recirculation CV",
            "sign_or_basis": "K; same-window property basis",
            "current_status": "blocked_closed_cv_not_admitted",
            "coefficient_use_allowed": "false",
        },
        {
            "qoi_label": "pressure_residual",
            "formula_or_definition": "observed/admitted section pressure residual after hydrostatic, kinetic, straight/developing, recovery, and source-basis terms",
            "sign_or_basis": "Pa or dimensionless residual; basis must be declared before F6/K claims",
            "current_status": "support_evidence_only_no_component_K_or_F6_model",
            "coefficient_use_allowed": "false",
        },
        {
            "qoi_label": "energy_residual",
            "formula_or_definition": "Q_wall_W + enthalpy_exchange_terms + storage/source/sink residual on same CV/window",
            "sign_or_basis": "W; positive convention must be declared in harvest package",
            "current_status": "support_slot_only_blocked_same_qoi_mesh_gci_source_property",
            "coefficient_use_allowed": "false",
        },
    ]


def build_current_case_decisions(
    recirc_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    pressure_summary: dict[str, Any],
    source_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    closed_cv_gate = status_lookup(evidence_rows, "closed recirculation fraction")
    medium_fine_gate = status_lookup(evidence_rows, "medium/fine exact-label rows")
    same_qoi_gate = status_lookup(evidence_rows, "same-QOI temporal UQ")
    source_property = source_property_row(source_rows, "S13_upcomer_exchange_cell")
    low_recirc_anchor_admitted = int(pressure_summary.get("sampled_endpoint_ordinary_flow_pass_rows", 0)) > 0
    source_property_valid = parse_bool(source_property.get("source_property_release_ready"))

    rows: list[dict[str, Any]] = []
    for row in recirc_rows:
        reverse_fraction = nfloat(row.get("reverse_candidate_fraction_of_right_leg_roi")) or 0.0
        reverse_active = reverse_fraction > 0.0
        closed_cv_admitted = parse_bool(row.get("closed_recirc_volume_claim_allowed"))
        exchange_interface_admitted = False
        wall_core_band_admitted = False
        mesh_gci_admitted = row.get("mesh_gci_status", "").startswith("admitted")
        same_qoi_admitted = False
        one_stream_allowed = (not reverse_active) and low_recirc_anchor_admitted
        exchange_cell_allowed = (
            reverse_active
            and closed_cv_admitted
            and exchange_interface_admitted
            and wall_core_band_admitted
            and same_qoi_admitted
            and mesh_gci_admitted
            and source_property_valid
        )
        if one_stream_allowed:
            selected_lane = "one_stream"
            lane_status = "admitted_anchor_required"
        elif exchange_cell_allowed:
            selected_lane = "throughflow_plus_recirc_exchange_cell"
            lane_status = "admitted_architecture_no_coefficients"
        elif reverse_active:
            selected_lane = "signed_flow_junction_network"
            lane_status = "guarded_dry_fallback_not_net_branch_admission"
        else:
            selected_lane = "blocked_no_lane"
            lane_status = "missing_low_recirc_anchor_and_missing_recirc_topology"
        rows.append(
            {
                "case_id": row["case_id"],
                "reverse_flow_evidence_active": str(reverse_active).lower(),
                "reverse_candidate_fraction_of_right_leg_roi": row["reverse_candidate_fraction_of_right_leg_roi"],
                "low_recirc_anchor_admitted": str(low_recirc_anchor_admitted).lower(),
                "closed_recirc_cv_admitted": str(closed_cv_admitted).lower(),
                "exchange_interface_admitted": str(exchange_interface_admitted).lower(),
                "wall_core_band_admitted": str(wall_core_band_admitted).lower(),
                "same_qoi_uq_current_coarse_available": str(same_qoi_gate.get("status") == "available_current_coarse").lower(),
                "same_qoi_uq_admitted_for_switch": str(same_qoi_admitted).lower(),
                "mesh_gci_admitted": str(mesh_gci_admitted).lower(),
                "source_property_valid_for_exchange_cell": str(source_property_valid).lower(),
                "one_stream_allowed": str(one_stream_allowed).lower(),
                "ordinary_Nu_fD_K_F6_claims_allowed": "false",
                "throughflow_exchange_cell_allowed": str(exchange_cell_allowed).lower(),
                "exchange_cell_coefficient_fit_allowed": "false",
                "selected_lane": selected_lane,
                "lane_status": lane_status,
                "closed_cv_gate_status": closed_cv_gate.get("status", ""),
                "medium_fine_exact_label_status": medium_fine_gate.get("status", ""),
                "mesh_gci_status": row.get("mesh_gci_status", ""),
                "Ri_status": row.get("Ri_status", ""),
            }
        )
    return rows


def build_fail_closed_states() -> list[dict[str, Any]]:
    return [
        {
            "state_id": "FC1_missing_low_recirc_anchor",
            "trigger": "low_recirc_or_nonrecirc_anchor_admitted == false",
            "switch_effect": "one_stream disabled",
            "claim_effect": "no ordinary upcomer Nu/f_D/K/F6",
            "next_unlock": "admit low-recirculation/nonrecirculating anchors with same-QOI UQ and mesh/GCI",
        },
        {
            "state_id": "FC2_reverse_active_no_closed_cv",
            "trigger": "reverse_flow_evidence_active == true and closed_recirc_cv_admitted == false",
            "switch_effect": "route to guarded signed_flow_junction_network dry fallback",
            "claim_effect": "no exchange-cell coefficient, no component K/F6",
            "next_unlock": "recirculation-cell segmentation from validated cell VTKs",
        },
        {
            "state_id": "FC3_missing_exchange_interface",
            "trigger": "closed CV exists but exchange_interface_admitted == false",
            "switch_effect": "throughflow_plus_recirc_exchange_cell blocked",
            "claim_effect": "mdot_exchange remains diagnostic/proxy only",
            "next_unlock": "derive internal faces between recirc cells and main-throughflow cells",
        },
        {
            "state_id": "FC4_missing_wall_core_band",
            "trigger": "wall_core_band_admitted == false",
            "switch_effect": "Q_wall_W/T_recirc thermal contrast blocked",
            "claim_effect": "no wall/core thermal coefficient or Qwall release",
            "next_unlock": "derive wall/core band from the same recirculation CV",
        },
        {
            "state_id": "FC5_missing_same_qoi_uq_or_mesh_gci",
            "trigger": "same-QOI UQ or mesh/GCI not admitted",
            "switch_effect": "exchange-cell architecture may be documented but not admitted",
            "claim_effect": "no coefficient fitting and no production harvest/admission",
            "next_unlock": "complete exact-label medium/fine rows, then rerun mesh/GCI disposition",
        },
        {
            "state_id": "FC6_missing_source_property_validity",
            "trigger": "source_property_valid_for_exchange_cell == false",
            "switch_effect": "energy residual support blocked from release",
            "claim_effect": "no source-side heat-flow equivalence or cp-dependent exchange claim",
            "next_unlock": "candidate-specific source/property and cp validity release",
        },
    ]


def build_evidence_crosswalk() -> list[dict[str, Any]]:
    return [
        {
            "evidence_label": "reverse_flow_evidence_active",
            "source_file": str(RECIRC_PACKET / "recirculation_onset_metric_table.csv"),
            "source_column": "reverse_candidate_fraction_of_right_leg_roi",
            "switch_use": "disable one_stream when active; route to lane 2 unless lane 3 admitted",
            "current_status": "available_proxy",
        },
        {
            "evidence_label": "closed_recirc_cv_admitted",
            "source_file": str(RECIRC_PACKET / "recirculation_onset_metric_table.csv"),
            "source_column": "closed_recirc_volume_claim_allowed",
            "switch_use": "required for throughflow_plus_recirc_exchange_cell",
            "current_status": "blocked_fragmented_velocity_topology",
        },
        {
            "evidence_label": "exchange_interface_admitted",
            "source_file": str(SAMPLER_PACKET / "RUNNING.md"),
            "source_column": "future derived face mask",
            "switch_use": "required for mdot_exchange production",
            "current_status": "blocked_pending_trusted_interface_geometry",
        },
        {
            "evidence_label": "wall_core_band_admitted",
            "source_file": str(SAMPLER_PACKET / "RUNNING.md"),
            "source_column": "future derived wall/core face mask",
            "switch_use": "required for Q_wall_W, T_recirc, and wall/core contrast",
            "current_status": "blocked_pending_wall_core_band_geometry",
        },
        {
            "evidence_label": "same_qoi_uq_current_coarse_available",
            "source_file": str(RECIRC_PACKET / "evidence_availability_gate.csv"),
            "source_column": "same-QOI temporal UQ",
            "switch_use": "diagnostic temporal support only; not enough for admission",
            "current_status": "available_current_coarse",
        },
        {
            "evidence_label": "mesh_gci_admitted",
            "source_file": str(RECIRC_PACKET / "recirculation_onset_metric_table.csv"),
            "source_column": "mesh_gci_status",
            "switch_use": "required before exchange-cell production/admission",
            "current_status": "blocked_medium_fine_exact_label_rows_pending",
        },
        {
            "evidence_label": "low_recirc_anchor_admitted",
            "source_file": str(PRESSURE_ANCHOR_PACKET / "summary.json"),
            "source_column": "sampled_endpoint_ordinary_flow_pass_rows",
            "switch_use": "required to allow one_stream upcomer claims",
            "current_status": "0 pass rows",
        },
        {
            "evidence_label": "source_property_valid_for_exchange_cell",
            "source_file": str(SOURCE_PROPERTY_PACKET / "source_property_atlas.csv"),
            "source_column": "S13_upcomer_exchange_cell/source_property_release_ready",
            "switch_use": "required for energy residual and cp-dependent exchange claims",
            "current_status": "false",
        },
    ]


def build_pseudocode() -> str:
    return """# Dry 1D recirculation switch pseudocode

Inputs are setup-known geometry/source/property quantities plus predeclared
regime indicators. Realized CFD velocity, wallHeatFlux, and validation
temperatures are evidence labels only; they are not predictive runtime inputs.

```text
if reverse_flow_evidence_active is false
   and recirculation_proxy_active is false
   and low_recirc_or_nonrecirc_anchor_admitted is true:
    output = one_stream
    allow only admitted one-stream claims within the anchor envelope

elif reverse_flow_evidence_active is true
   and not (
       closed_recirc_cv_admitted
       and exchange_interface_admitted
       and wall_core_band_admitted
       and same_qoi_uq_admitted
       and mesh_gci_admitted
       and source_property_valid
   ):
    output = signed_flow_junction_network
    status = guarded_dry_fallback_not_net_branch_admission
    forbid Nu/f_D/K/F6/component-K/coefficient claims

elif closed_recirc_cv_admitted
   and exchange_interface_admitted
   and wall_core_band_admitted
   and same_qoi_uq_admitted
   and mesh_gci_admitted
   and source_property_valid:
    output = throughflow_plus_recirc_exchange_cell
    status = exchange_cell_architecture_admitted_no_coefficients
    expose dry QOI slots only; fit coefficients only under a future row

else:
    output = blocked_no_lane
    fail closed with no ordinary or exchange-cell production claim
```
"""


def build_readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {RECIRC_PACKET / "recirculation_onset_metric_table.csv"}
  - {MF09_PACKET / "ordinary_upcomer_disable_gate.csv"}
  - {REGIME_PACKET / "closure_eligibility_decisions.csv"}
tags: [work-product, recirculation, model-form, 1d-switch, upcomer]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/1d-recirculation-switch-dry-contract.md
task: {TASK_ID}
date: {DATE}
role: Hydraulics / Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# 1D Recirculation Switch Dry Contract

This package converts the current recirculation evidence into a dry 1D
model-form switch. It does not fit coefficients, admit an exchange cell, rerun
mesh/GCI, release source/property rows, or mutate native CFD outputs.

Decision: `{summary["decision"]}`.

## Contract

The switch has exactly three outputs:

- `one_stream`: allowed only when reverse-flow/recirculation evidence is
  inactive and low-recirculation or nonrecirculating anchors are admitted.
- `signed_flow_junction_network`: guarded dry fallback when topology indicates
  flow reversal or mixed signs but no closed exchange-cell volume/interface is
  admitted.
- `throughflow_plus_recirc_exchange_cell`: available only after a defensible
  recirculation CV, exchange interface, wall/core band, same-QOI UQ,
  source/property validity, and mesh/GCI evidence exist.

Current Salt2/Salt3/Salt4 rows select the guarded
`signed_flow_junction_network` lane because reverse-flow proxy evidence is
active while the exchange-cell admission gates remain blocked.

## Files

- `model_form_gate_update.csv`
- `recirculation_switch_lane_contract.csv`
- `dry_runtime_input_contract.csv`
- `qoi_interface_contract.csv`
- `current_case_switch_decisions.csv`
- `fail_closed_state_table.csv`
- `evidence_label_crosswalk.csv`
- `switch_pseudocode.md`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Guardrails

Ordinary upcomer `Nu/f_D/K/F6` claims are disabled in recirculating upcomer
evidence. Exchange-cell coefficients remain disabled until a separate future
admission package has exact CV/interface/wall-core geometry, same-QOI UQ,
source/property validity, and mesh/GCI evidence.
"""


def build(output_root: str | Path | None = None) -> dict[str, Any]:
    out = resolve_out(output_root)
    ensure_dir(out)

    recirc_rows = read_csv(RECIRC_PACKET / "recirculation_onset_metric_table.csv")
    evidence_rows = read_csv(RECIRC_PACKET / "evidence_availability_gate.csv")
    mf09_rows = read_csv(MF09_PACKET / "ordinary_upcomer_disable_gate.csv")
    regime_rows = read_csv(REGIME_PACKET / "closure_eligibility_decisions.csv")
    hierarchy_rows = read_csv(HIERARCHY_PACKET / "model_hierarchy_ladder.csv")
    pressure_summary = read_json(PRESSURE_ANCHOR_PACKET / "summary.json")
    source_rows = read_csv(SOURCE_PROPERTY_PACKET / "source_property_atlas.csv")

    gate_rows = build_model_form_gate_update(recirc_rows, mf09_rows, regime_rows, pressure_summary)
    lane_rows = build_lane_contract()
    runtime_rows = build_runtime_inputs()
    qoi_rows = build_qoi_interface_contract()
    case_rows = build_current_case_decisions(recirc_rows, evidence_rows, pressure_summary, source_rows)
    fail_rows = build_fail_closed_states()
    crosswalk_rows = build_evidence_crosswalk()

    selected_counts: dict[str, int] = {}
    for row in case_rows:
        selected_counts[row["selected_lane"]] = selected_counts.get(row["selected_lane"], 0) + 1

    l3 = next((row for row in hierarchy_rows if row.get("level") == "L3"), {})
    summary = {
        "task_id": TASK_ID,
        "generated_at": iso_timestamp(),
        "decision": "dry_recirculation_switch_contract_ready_no_coefficients_no_admission",
        "switch_outputs": ["one_stream", "signed_flow_junction_network", "throughflow_plus_recirc_exchange_cell"],
        "case_rows": len(case_rows),
        "current_case_selected_lane_counts": selected_counts,
        "ordinary_one_stream_upcomer_claims_allowed": False,
        "ordinary_Nu_fD_K_F6_claim_rows_allowed": 0,
        "exchange_cell_coefficient_fit_allowed": False,
        "exchange_cell_admission_allowed": False,
        "one_stream_current_allowed_cases": sum(1 for row in case_rows if row["one_stream_allowed"] == "true"),
        "throughflow_exchange_cell_current_allowed_cases": sum(
            1 for row in case_rows if row["throughflow_exchange_cell_allowed"] == "true"
        ),
        "evidence_backed_not_coefficient_backed": True,
        "mesh_gci_rerun": False,
        "scheduler_action": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "source_property_release": False,
        "coefficient_admission": False,
        "l3_hierarchy_evidence_state": l3.get("evidence_state", ""),
        "l3_hierarchy_next_gate": l3.get("next_gate", ""),
    }

    csv_dump(out / "model_form_gate_update.csv", list(gate_rows[0].keys()), gate_rows)
    csv_dump(out / "recirculation_switch_lane_contract.csv", list(lane_rows[0].keys()), lane_rows)
    csv_dump(out / "dry_runtime_input_contract.csv", list(runtime_rows[0].keys()), runtime_rows)
    csv_dump(out / "qoi_interface_contract.csv", list(qoi_rows[0].keys()), qoi_rows)
    csv_dump(out / "current_case_switch_decisions.csv", list(case_rows[0].keys()), case_rows)
    csv_dump(out / "fail_closed_state_table.csv", list(fail_rows[0].keys()), fail_rows)
    csv_dump(out / "evidence_label_crosswalk.csv", list(crosswalk_rows[0].keys()), crosswalk_rows)
    source_manifest = [
        {
            "source_path": str(path),
            "exists": str((repo_root() / path).exists()).lower(),
            "use": "read_only_evidence_for_dry_switch_contract",
        }
        for path in SOURCE_PATHS
    ]
    csv_dump(out / "source_manifest.csv", list(source_manifest[0].keys()), source_manifest)
    guardrails = [
        {"guardrail": "native_solver_outputs_mutated", "status": "false"},
        {"guardrail": "registry_or_admission_state_mutated", "status": "false"},
        {"guardrail": "scheduler_action", "status": "false"},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launched", "status": "false"},
        {"guardrail": "coefficient_fitting_or_admission", "status": "false"},
        {"guardrail": "source_property_or_qwall_release", "status": "false"},
        {"guardrail": "ordinary_Nu_fD_K_F6_claims_in_recirc_upcomer", "status": "false"},
    ]
    csv_dump(out / "no_mutation_guardrails.csv", list(guardrails[0].keys()), guardrails)
    (out / "switch_pseudocode.md").write_text(build_pseudocode(), encoding="utf-8")
    json_dump(out / "summary.json", summary)
    (out / "README.md").write_text(build_readme(summary), encoding="utf-8")
    return summary


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
