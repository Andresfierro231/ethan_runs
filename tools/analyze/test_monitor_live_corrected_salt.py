#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.analyze.monitor_live_corrected_salt as monitor  # noqa: E402


def _args(**over) -> argparse.Namespace:
    ns = argparse.Namespace(
        min_ended_advance_s=1000.0,
        min_ended_advance_frac=0.20,
        move_tolerance=0.5,
        plateau_drift_pct=1.0,
        plateau_amp_pct=2.0,
    )
    for key, value in over.items():
        setattr(ns, key, value)
    return ns


def test_classify_flags_early_convergence_monitor_stop():
    row = {
        "fatal_error_count": 0,
        "preflight_bad_ok_count": 0,
        "nominal_mdot_kg_s": float("nan"),
        "solver_log_has_end": True,
        "advance_since_restart_s": 254.26,
        "advance_fraction_of_target": 0.0424,
        "mdot_direction_ok": False,
        "moved_enough": False,
        "plateau_like": True,
        "job_state": "RUNNING",
    }

    result = monitor.classify(row, _args())

    assert result["needs_special_gate_scrutiny"] is True
    assert "ended early" in result["scrutiny_reason"]
    assert "missing nominal mdot reference" in result["scrutiny_reason"]
    assert result["recommendation"] == "hold_for_coordinator_review"


def test_classify_investigates_fatal_marker():
    row = {
        "fatal_error_count": 1,
        "preflight_bad_ok_count": 0,
        "nominal_mdot_kg_s": -0.0132,
        "solver_log_has_end": False,
        "advance_since_restart_s": 2000.0,
        "advance_fraction_of_target": 0.5,
        "mdot_direction_ok": True,
        "moved_enough": True,
        "plateau_like": False,
        "job_state": "RUNNING",
    }

    result = monitor.classify(row, _args())

    assert result["needs_special_gate_scrutiny"] is True
    assert result["recommendation"] == "investigate"


def test_classify_running_nonflagged_row_holds_for_formal_gate():
    row = {
        "fatal_error_count": 0,
        "preflight_bad_ok_count": 0,
        "nominal_mdot_kg_s": -0.0132,
        "solver_log_has_end": False,
        "advance_since_restart_s": 1500.0,
        "advance_fraction_of_target": 0.25,
        "mdot_direction_ok": True,
        "moved_enough": True,
        "plateau_like": False,
        "job_state": "RUNNING",
    }

    result = monitor.classify(row, _args())

    assert result["needs_special_gate_scrutiny"] is False
    assert result["recommendation"] == "hold_running_wait_for_formal_gate"


def test_expected_move_frac():
    assert abs(monitor.expected_move_frac(1.10) - 0.03228) < 1e-4
    assert abs(monitor.expected_move_frac(0.90) - 0.03451) < 1e-4


def test_classify_investigates_terminal_short_advance():
    row = {
        "fatal_error_count": 1,
        "preflight_bad_ok_count": 0,
        "nominal_mdot_kg_s": -0.01499,
        "solver_log_has_end": False,
        "advance_since_restart_s": 20.0,
        "advance_fraction_of_target": 0.0033,
        "mdot_direction_ok": True,
        "moved_enough": True,
        "plateau_like": False,
        "job_state": "CANCELLED by 890970",
    }

    result = monitor.classify(row, _args())

    assert result["needs_special_gate_scrutiny"] is True
    assert "terminal/non-success scheduler state" in result["scrutiny_reason"]
    assert "terminal short advance" in result["scrutiny_reason"]
    assert result["recommendation"] == "investigate"


def test_parse_log_ignores_mesh_error_words_and_scheduler_timeout_tail():
    text = "\n".join(
        [
            "Time = 21980",
            "Mesh stats",
            "    Max openness = 2.1e-15",
            "Checking faces in error : 0",
            "srun: error: c123-001: task 0: Terminated",
            "slurmstepd: error: *** JOB 3293924 ON c123-001 CANCELLED AT 2026-07-14T00:00:00 DUE TO TIME LIMIT ***",
        ]
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        log = Path(tmpdir) / "log.foamRun"
        log.write_text(text)

        parsed = monitor.parse_log(log, tail_bytes=100_000)

    assert parsed["fatal_error_count"] == 0
    assert parsed["latest_solver_time_s"] == 21980.0


def test_parse_log_counts_real_openfoam_fatal_error():
    text = "\n".join(
        [
            "Time = 42",
            "FOAM FATAL ERROR:",
            "FOAM exiting",
        ]
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        log = Path(tmpdir) / "log.foamRun"
        log.write_text(text)

        parsed = monitor.parse_log(log, tail_bytes=100_000)

    assert parsed["fatal_error_count"] == 2
