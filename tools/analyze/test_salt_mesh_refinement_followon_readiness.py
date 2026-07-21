from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from tools.analyze import build_salt_mesh_coarse_reconciliation as coarse
from tools.analyze import build_salt_mesh_full_history_monitor_reduction as monitors
from tools.analyze import build_salt_mesh_gci_uq_readiness as readiness


def test_time_relation_marks_mainline_extension() -> None:
    assert coarse.time_relation(2400.0, 7900.0) == "mainline_extends_external"


def test_coarse_classification_prioritizes_superseded_mainline() -> None:
    row = {
        "external_exists": "yes",
        "mainline_exists": "yes",
        "external_source_path": "/external/case",
        "mainline_case_root": "jadyn_runs/mainline/case",
        "time_relation": "mainline_extends_external",
        "bc_fingerprint_equal": "no",
    }
    verdict, use_status, _notes = coarse.classify(row)
    assert verdict == "superseded_by_mainline"
    assert use_status == "do_not_use_external_coarse_for_publication_gci"


def test_merge_scalar_files_later_restart_segment_overrides_duplicate_time() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = root / "0" / "surfaceFieldValue.dat"
        second = root / "10" / "surfaceFieldValue.dat"
        first.parent.mkdir()
        second.parent.mkdir()
        first.write_text("# Time sum(phi)\n9 1.0\n10 2.0\n", encoding="utf-8")
        second.write_text("# Time sum(phi)\n10 3.0\n11 4.0\n", encoding="utf-8")
        series = monitors.merge_scalar_files([first, second])
    assert series == [(9.0, 1.0), (10.0, 3.0), (11.0, 4.0)]


def test_monitor_summary_detects_stationary_flat_series() -> None:
    summary = monitors.summarize_series([(float(i), 5.0) for i in range(20)])
    assert summary["series_verdict"] == "stationary"
    assert summary["mean_value"] == 5.0
    assert summary["drift_fraction"] == 0.0


def test_status_prioritizes_coarse_superseded_over_numeric_gci() -> None:
    status, blocker, numeric_status = readiness.status_for(
        complete=True,
        coarse_reconciliation="superseded_by_mainline",
        gates={"coarse": "partial_needs_coarse_reconciliation", "medium": "admitted_for_gci_input", "fine": "admitted_for_gci_input"},
        series={"coarse": "stationary", "medium": "stationary", "fine": "stationary"},
        gci={"gci_trustworthy": True, "gci_fine_pct": 0.2},
        target=2.0,
        quantity="mdot_abs_mean_kg_s",
    )
    assert status == "blocked_coarse_superseded_by_mainline"
    assert blocker == "external_coarse_source_is_superseded_by_mainline_continuation"
    assert numeric_status == "screening_gci_only"


def test_status_blocks_specialized_qoi_until_medium_fine_extraction() -> None:
    status, blocker, numeric_status = readiness.status_for(
        complete=True,
        coarse_reconciliation="compatible_but_not_identical",
        gates={"coarse": "admitted_for_gci_input", "medium": "admitted_for_gci_input", "fine": "admitted_for_gci_input"},
        series={"coarse": "stationary", "medium": "stationary", "fine": "stationary"},
        gci={"gci_trustworthy": True, "gci_fine_pct": 0.2},
        target=2.0,
        quantity="lower_leg_f_debuoyed",
    )
    assert status == "blocked_requires_mesh_level_extraction"
    assert blocker == "medium_fine_pressure_or_thermal_closure_qoi_not_extracted"
    assert numeric_status == "not_computed"
