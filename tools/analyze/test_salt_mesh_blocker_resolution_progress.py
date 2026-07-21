from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from tools.analyze import build_salt_mesh_blocker_resolution_progress as progress


def test_compare_status_relative_alignment() -> None:
    status, tol_type, tol, abs_delta, rel_delta = progress.compare_status("mdot_abs_mean_kg_s", 1.0, 1.005)
    assert status == "aligned"
    assert tol_type == "relative"
    assert tol == 0.01
    assert abs_delta is not None and abs_delta > 0.0
    assert rel_delta is not None and rel_delta < 0.01


def test_compare_status_absolute_difference() -> None:
    status, tol_type, tol, _abs_delta, _rel_delta = progress.compare_status("temperature_probe_mean_K", 450.0, 453.0)
    assert status == "different"
    assert tol_type == "absolute"
    assert tol == 2.0


def test_field_presence_detects_required_processor_fields() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        latest = root / "processors64" / "10"
        latest.mkdir(parents=True)
        for name in ["U", "p_rgh", "T"]:
            (latest / name).write_text("", encoding="utf-8")
        time_name, status = progress.field_presence(root, "processors64")
    assert time_name == "10"
    assert status == "yes"


def test_salt4_review_keeps_signal15_unadmitted() -> None:
    quality = [
        {
            "case_id": "salt_test_4_jin",
            "mesh_level": "medium",
            "gate_verdict": "partial_needs_continuation",
            "foamrun_terminal_state": "signal15",
            "tail_signal15": "yes",
            "tail_convergence_monitor": "no",
        }
    ]
    monitors = [
        {"case_id": "salt_test_4_jin", "mesh_level": "medium", "series_verdict": "stationary"},
        {"case_id": "salt_test_4_jin", "mesh_level": "medium", "series_verdict": "quasi_stationary"},
    ]
    row = progress.build_salt4_admission_review(quality, monitors)[0]
    assert row["admission_review"] == "not_admitted_log_gate_failed"
    assert row["problem_rows"] == 0


def test_mainline_rows_maps_scenario_source_to_endpoint_case() -> None:
    scenario = [
        {
            "source_id": "viscosity_screening_salt_test_2_jin_coarse_mesh",
            "run_class": "mainline_jin_continuation",
            "case_root": "some/path",
        }
    ]
    rows = progress.mainline_rows(scenario)
    assert rows[0]["case_id"] == "salt_test_2_jin"
    assert rows[0]["mesh_level"] == "coarse"
