#!/usr/bin/env python3
"""Focused checks for the dry 1D recirculation switch contract."""

from __future__ import annotations

import csv
from pathlib import Path

from tools.analyze import build_1d_recirculation_switch_dry_contract as builder


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_switch_contract_has_exact_three_lanes(tmp_path):
    summary = builder.build(tmp_path)

    assert summary["decision"] == "dry_recirculation_switch_contract_ready_no_coefficients_no_admission"
    assert summary["switch_outputs"] == [
        "one_stream",
        "signed_flow_junction_network",
        "throughflow_plus_recirc_exchange_cell",
    ]
    assert summary["ordinary_one_stream_upcomer_claims_allowed"] is False
    assert summary["exchange_cell_coefficient_fit_allowed"] is False

    lanes = read_csv(tmp_path / "recirculation_switch_lane_contract.csv")
    assert [row["switch_output"] for row in lanes] == summary["switch_outputs"]
    one_stream = lanes[0]
    assert "reverse-flow/recirculation evidence is inactive" in one_stream["activation_rule"]
    assert "low-recirculation or nonrecirculating anchors are admitted" in one_stream["activation_rule"]


def test_current_salt_cases_route_to_guarded_signed_flow_fallback(tmp_path):
    builder.build(tmp_path)

    decisions = read_csv(tmp_path / "current_case_switch_decisions.csv")
    assert {row["case_id"] for row in decisions} == {"salt_2", "salt_3", "salt_4"}
    assert {row["reverse_flow_evidence_active"] for row in decisions} == {"true"}
    assert {row["low_recirc_anchor_admitted"] for row in decisions} == {"false"}
    assert {row["closed_recirc_cv_admitted"] for row in decisions} == {"false"}
    assert {row["one_stream_allowed"] for row in decisions} == {"false"}
    assert {row["throughflow_exchange_cell_allowed"] for row in decisions} == {"false"}
    assert {row["exchange_cell_coefficient_fit_allowed"] for row in decisions} == {"false"}
    assert {row["ordinary_Nu_fD_K_F6_claims_allowed"] for row in decisions} == {"false"}
    assert {row["selected_lane"] for row in decisions} == {"signed_flow_junction_network"}
    assert {row["lane_status"] for row in decisions} == {"guarded_dry_fallback_not_net_branch_admission"}


def test_model_form_gate_disables_ordinary_and_coefficients(tmp_path):
    builder.build(tmp_path)

    gates = {row["claim_id"]: row for row in read_csv(tmp_path / "model_form_gate_update.csv")}
    for claim_id in ["ordinary_upcomer_Nu", "ordinary_upcomer_f_D", "ordinary_upcomer_K", "ordinary_upcomer_F6"]:
        assert gates[claim_id]["current_gate"] == "disabled"
        assert gates[claim_id]["ordinary_claim_allowed_now"] == "false"
        assert gates[claim_id]["fit_allowed_now"] == "false"
        assert gates[claim_id]["coefficient_backed"] == "false"

    assert gates["exchange_cell_coefficient_fit"]["current_gate"] == "disabled_no_fit"
    assert gates["throughflow_plus_recirc_exchange_cell_architecture"]["current_gate"] == "architecture_defined_not_admitted"


def test_runtime_inputs_forbid_realized_cfd_and_validation_state(tmp_path):
    builder.build(tmp_path)

    runtime_inputs = read_csv(tmp_path / "dry_runtime_input_contract.csv")
    forbidden = {row["input_label"] for row in runtime_inputs if row["runtime_status"] == "forbidden_runtime_input"}
    assert {"realized_CFD_velocity_field", "realized_CFD_wallHeatFlux", "validation_temperature_targets"}.issubset(forbidden)

    qois = {row["qoi_label"]: row for row in read_csv(tmp_path / "qoi_interface_contract.csv")}
    for qoi in ["R_mu", "R_rho", "V_recirc", "mdot_exchange", "T_recirc", "pressure_residual", "energy_residual"]:
        assert qoi in qois
        assert qois[qoi]["coefficient_use_allowed"] == "false"


def test_fail_closed_states_cover_exchange_cell_blockers(tmp_path):
    builder.build(tmp_path)

    states = {row["state_id"]: row for row in read_csv(tmp_path / "fail_closed_state_table.csv")}
    assert "FC1_missing_low_recirc_anchor" in states
    assert "FC2_reverse_active_no_closed_cv" in states
    assert "FC5_missing_same_qoi_uq_or_mesh_gci" in states
    assert "FC6_missing_source_property_validity" in states

