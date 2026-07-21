"""Tests for AGENT-283 terminal harvest admission review."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.analyze.build_terminal_harvest_admission_review import (
    TARGET_CASES,
    admission_label,
    build_package,
)


class TerminalHarvestAdmissionReviewTests(unittest.TestCase):
    def test_admission_label_accepts_flat_salt1_window(self) -> None:
        label, harvest = admission_label(
            {
                "total_Q_drift_W": 0.0,
                "max_mdot_relative_drift": 2.0e-6,
                "temperature_probe_max_abs_drift_K": 0.0,
                "wall_temperature_probe_max_abs_drift_K": 0.0,
            }
        )

        self.assertEqual(label, "terminal_window_stationary_cancelled")
        self.assertEqual(harvest, "terminal_harvest_complete_context_only")

    def test_admission_label_rejects_drifting_window(self) -> None:
        label, harvest = admission_label(
            {
                "total_Q_drift_W": 0.0,
                "max_mdot_relative_drift": 1.0e-4,
                "temperature_probe_max_abs_drift_K": 0.0,
                "wall_temperature_probe_max_abs_drift_K": 0.0,
            }
        )

        self.assertEqual(label, "not_admitted_missing_evidence")
        self.assertEqual(harvest, "not_admitted_missing_evidence")

    def test_build_package_from_minimal_fixture(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            case_dir = root / "case"
            logs = case_dir / "logs"
            pp = case_dir / "postProcessing"
            logs.mkdir(parents=True)
            (logs / "log.foamRun_salt1").write_text(
                "Time = 1\nExecutionTime = 1 s  ClockTime = 1 s\n", encoding="utf-8"
            )
            for family in (
                "mdot_pipeleg_left_04_test_section",
                "mdot_pipeleg_lower_05_straight",
                "mdot_pipeleg_right_02_middle",
                "mdot_pipeleg_upper_05_cooler",
                "temperature_probes",
                "wall_temperature_probes",
            ):
                (pp / family / "100").mkdir(parents=True)

            input_path = root / "metrics.csv"
            fieldnames = [
                "case_id",
                "slurm_job_or_step",
                "source_case_path",
                "stop_state",
                "decision",
                "window_start_s",
                "window_end_s",
                "quantity",
                "mean",
                "latest",
                "drift",
                "span",
                "relative_drift",
                "relative_span",
                "notes",
            ]
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for case_id in TARGET_CASES:
                    for quantity, drift, rel_drift in (
                        ("total_Q_W", "0", "0"),
                        ("mdot_pipeleg_left_04_test_section_kg_s", "1e-9", "1e-7"),
                        ("temperature_probes_max_abs_drift_K", "0", ""),
                        ("wall_temperature_probes_max_abs_drift_K", "0", ""),
                    ):
                        writer.writerow(
                            {
                                "case_id": case_id,
                                "slurm_job_or_step": "1.0",
                                "source_case_path": str(case_dir),
                                "stop_state": "CANCELLED by user",
                                "decision": "steady_runtime_stop",
                                "window_start_s": "0",
                                "window_end_s": "600",
                                "quantity": quantity,
                                "mean": "1",
                                "latest": "1",
                                "drift": drift,
                                "span": drift,
                                "relative_drift": rel_drift,
                                "relative_span": rel_drift,
                                "notes": "",
                            }
                        )

            output_dir = root / "out"
            summary = build_package(input_path, output_dir)

            self.assertEqual(summary["terminal_harvest_complete_context_only_count"], 3)
            self.assertTrue((output_dir / "admission_decision_table.csv").is_file())
            self.assertTrue((output_dir / "postprocessing_availability.csv").is_file())


if __name__ == "__main__":
    unittest.main()
