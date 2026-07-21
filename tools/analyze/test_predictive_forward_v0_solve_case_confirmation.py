#!/usr/bin/env python3
"""Tests for build_predictive_forward_v0_solve_case_confirmation.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import build_predictive_forward_v0_solve_case_confirmation as builder  # noqa: E402


class ForwardV0SolveCaseConfirmationTests(unittest.TestCase):
    def test_build_package_writes_no_submit_harness_with_both_engines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "pkg"
            summary = builder.build_package(package)

            shell_text = (package / "scripts/run_forward_v0_solve_case_confirmation.sh").read_text(encoding="utf-8")
            sbatch_text = (package / "scripts/run_forward_v0_solve_case_confirmation.sbatch").read_text(encoding="utf-8")
            readme = (package / "README.md").read_text(encoding="utf-8")

            self.assertFalse(summary["job_submitted"])
            self.assertIn("--engine fast_scan", shell_text)
            self.assertIn("--engine solve_case", shell_text)
            self.assertIn("fast_scan_reference", shell_text)
            self.assertIn("solve_case_full", shell_text)
            self.assertIn("#SBATCH -t 06:00:00", sbatch_text)
            self.assertIn("Do not run the full `--engine solve_case` matrix on a login node.", readme)
            self.assertTrue((package / "logs").is_dir())

            written_summary = json.loads((package / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written_summary["comparison_status"], "pending_compute_node_run")

    def test_metric_contract_covers_required_confirmation_axes(self) -> None:
        metrics = {row["metric_id"] for row in builder.metric_contract_rows()}
        self.assertIn("mdot_delta_kg_s", metrics)
        self.assertIn("pressure_residual_delta_Pa", metrics)
        self.assertIn("model_Tmean_delta_K", metrics)
        self.assertIn("qambient_delta_W", metrics)
        self.assertIn("sensor_streams", metrics)

    def test_compare_results_computes_solve_minus_fast_deltas(self) -> None:
        fast_rows = [
            {
                "case_id": "salt_2",
                "variant_id": "F1_heater_only",
                "accepted_for_validation": "True",
                "root_status": "fast_scan_bracketed_pressure_root",
                "mdot_kg_s": "0.020",
                "pressure_residual_Pa": "1.5",
                "temperature_periodicity_error_K": "0.01",
                "model_Tmean_proxy_K": "480.0",
                "model_loop_delta_proxy_K": "10.0",
                "qambient_total_W": "140.0",
                "qhx_total_W": "136.0",
            }
        ]
        solve_rows = [
            {
                "case_id": "salt_2",
                "variant_id": "F1_heater_only",
                "accepted_for_validation": "true",
                "root_status": "solve_case_pressure_root",
                "mdot_kg_s": "0.0195",
                "pressure_residual_Pa": "0.1",
                "temperature_periodicity_error_K": "0.002",
                "model_Tmean_proxy_K": "480.8",
                "model_loop_delta_proxy_K": "10.2",
                "qambient_total_W": "143.0",
                "qhx_total_W": "136.0",
            }
        ]

        rows = builder.compare_results(fast_rows, solve_rows)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["comparison_status"], "pass")
        self.assertAlmostEqual(rows[0]["mdot_delta_solve_minus_fast_kg_s"], -0.0005)
        self.assertAlmostEqual(rows[0]["pressure_residual_delta_solve_minus_fast_Pa"], -1.4)
        self.assertAlmostEqual(rows[0]["model_Tmean_delta_solve_minus_fast_K"], 0.8)
        self.assertAlmostEqual(rows[0]["qambient_delta_solve_minus_fast_W"], 3.0)

    def test_compare_results_blocks_missing_or_rejected_solve_case_rows(self) -> None:
        rows = builder.compare_results(
            [{"case_id": "salt_2", "variant_id": "F0_current_fluid_sources", "accepted_for_validation": "true"}],
            [{"case_id": "salt_3", "variant_id": "F0_current_fluid_sources", "accepted_for_validation": "false"}],
        )
        statuses = {(row["case_id"], row["comparison_status"], row["notes"]) for row in rows}
        self.assertTrue(any(case_id == "salt_2" and status == "blocked" for case_id, status, _ in statuses))
        self.assertTrue(any(case_id == "salt_3" and "not accepted" in notes for case_id, _, notes in statuses))


if __name__ == "__main__":
    unittest.main()
