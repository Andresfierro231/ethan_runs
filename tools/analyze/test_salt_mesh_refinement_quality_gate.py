from __future__ import annotations

from pathlib import Path

from tools.analyze import build_salt_mesh_refinement_quality_gate as gate


def test_source_id_encodes_case_level_and_external_date() -> None:
    assert gate.source_id("salt_test_2_jin", "medium") == "salt_test_2_jin_medium_mesh_external_20260707"


def test_category_policy_keeps_kirst_historical() -> None:
    category, admission, fit_use = gate.category_for({"case_id": "salt_test_2_kirst", "fluid_variant": "kirst"})
    assert category == "historical_kirst_only"
    assert admission == "historical_kirst_only"
    assert fit_use == "not_current_mainline"


def test_gate_admits_clean_endpoint_medium_or_fine() -> None:
    row = {"case_id": "salt_test_2_jin", "fluid_variant": "jin", "mesh_level": "fine"}
    verdict, flags = gate.classify_gate(
        row,
        source_exists=True,
        log={
            "foamrun_terminal_state": "clean_end",
            "tail_signal15": "no",
            "tail_convergence_monitor": "yes",
            "tail_convergence_line": "convergenceMonitor: CONVERGED",
        },
        missing_pp=[],
        mdot_count=len(gate.MDOT_MONITORS),
        has_wallheatflux=True,
    )
    assert verdict == "admitted_for_gci_input"
    assert flags == ["none"]


def test_gate_holds_external_coarse_for_reconciliation() -> None:
    row = {"case_id": "salt_test_2_jin", "fluid_variant": "jin", "mesh_level": "coarse"}
    verdict, flags = gate.classify_gate(
        row,
        source_exists=True,
        log={
            "foamrun_terminal_state": "clean_end",
            "tail_signal15": "no",
            "tail_convergence_monitor": "yes",
            "tail_convergence_line": "convergenceMonitor: CONVERGED",
        },
        missing_pp=[],
        mdot_count=len(gate.MDOT_MONITORS),
        has_wallheatflux=True,
    )
    assert verdict == "partial_needs_coarse_reconciliation"
    assert "coarse_source_must_reconcile_with_repo_mainline_continuation" in flags


def test_gate_rejects_signal15_endpoint_without_convergence() -> None:
    row = {"case_id": "salt_test_4_jin", "fluid_variant": "jin", "mesh_level": "fine"}
    verdict, flags = gate.classify_gate(
        row,
        source_exists=True,
        log={
            "foamrun_terminal_state": "signal15",
            "tail_signal15": "yes",
            "tail_convergence_monitor": "no",
            "tail_convergence_line": "",
        },
        missing_pp=[],
        mdot_count=len(gate.MDOT_MONITORS),
        has_wallheatflux=True,
    )
    assert verdict == "partial_needs_continuation"
    assert "signal15_tail" in flags
    assert "no_tail_convergence_monitor" in flags


def test_series_summary_stationary_for_flat_signal() -> None:
    series = [(float(i), 2.0) for i in range(20)]
    summary = gate.summarize_series(series)
    assert summary["series_verdict"] == "stationary"
    assert summary["mean_value"] == 2.0
    assert summary["drift_fraction"] == 0.0


def test_gci_matrix_marks_salt2_partial_when_only_medium_fine_ready() -> None:
    endpoints = [
        {"case_id": "salt_test_2_jin", "mesh_level": level, "quantity": "wall_gross_duty_w", "mean_value": value}
        for level, value in [("coarse", 10.0), ("medium", 11.0), ("fine", 12.0)]
    ]
    quality = [
        {"case_id": "salt_test_2_jin", "mesh_level": "coarse", "gate_verdict": "partial_needs_coarse_reconciliation"},
        {"case_id": "salt_test_2_jin", "mesh_level": "medium", "gate_verdict": "admitted_for_gci_input"},
        {"case_id": "salt_test_2_jin", "mesh_level": "fine", "gate_verdict": "admitted_for_gci_input"},
    ]
    matrix = gate.build_gci_matrix(endpoints, quality)
    gross = [row for row in matrix if row["case_id"] == "salt_test_2_jin" and row["quantity"] == "wall_gross_duty_w"][0]
    assert gross["triplet_status"] == "partial_needs_coarse_reconciliation"
