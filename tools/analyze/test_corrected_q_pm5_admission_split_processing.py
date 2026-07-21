#!/usr/bin/env python3
"""Tests for build_corrected_q_pm5_admission_split_processing.py."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.analyze import build_corrected_q_pm5_admission_split_processing as pm5


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class CorrectedQPm5AdmissionSplitProcessingTests(unittest.TestCase):
    def test_admission_rows_do_not_expand_training(self) -> None:
        rows = pm5.admission_rows(
            [
                base_harvest("salt2_lo5q"),
                base_harvest("salt4_hi5q"),
            ]
        )
        by_case = {row["case_key"]: row for row in rows}

        self.assertEqual(by_case["salt2_lo5q"]["current_split_family"], "salt2_train_family_perturbation")
        self.assertEqual(by_case["salt4_hi5q"]["current_split_family"], "salt4_holdout_family_perturbation")
        self.assertEqual({row["can_expand_training_now"] for row in rows}, {"no"})
        self.assertIn("independent", by_case["salt2_lo5q"]["blocked_use"])

    def test_final_window_heat_row_uses_last_300_seconds(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            heat_path = Path(tmp) / "wall_heat_flux_grouped.csv"
            write_heat_rows(heat_path)
            row = pm5.final_window_heat_row(base_harvest("salt2_lo5q", wall_heat_flux_grouped_csv=str(heat_path)))

            self.assertEqual(row["final_window_start_s"], 100.0)
            self.assertEqual(row["final_window_end_s"], 400.0)
            self.assertEqual(row["final_window_row_count"], 2)
            self.assertAlmostEqual(row["cooling_branch_total_removal_mean_W"], 20.0)
            self.assertEqual(
                row["radiation_semantics"],
                "rcExternalTemperature_radiation_embedded_in_wallHeatFlux_no_exported_qr",
            )

    def test_build_package_outputs_expected_tables(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            out = Path(tmp)
            summary = pm5.build_package(out)

            self.assertEqual(summary["task"], "AGENT-353")
            self.assertEqual(summary["harvest_rows"], 4)
            self.assertEqual(summary["closure_fit_admissible_terminal_gate_rows"], 4)
            self.assertEqual(summary["independent_training_expansion_rows"], 0)
            self.assertFalse(summary["native_solver_outputs_mutated"])
            self.assertFalse(summary["registry_mutated"])

            admission = read_csv(out / "corrected_q_pm5_split_admission_matrix.csv")
            heat = read_csv(out / "corrected_q_pm5_heat_role_reduction.csv")
            queue = read_csv(out / "corrected_q_pm5_forward_gate_queue.csv")
            parsed = json.loads((out / "summary.json").read_text(encoding="utf-8"))

            self.assertEqual(len(admission), 4)
            self.assertEqual(len(heat), 4)
            self.assertEqual(len(queue), 12)
            self.assertEqual(parsed["forward_gate_queue_rows"], 12)
            self.assertEqual({row["can_expand_training_now"] for row in admission}, {"no"})


def base_harvest(case_key: str, **overrides: str) -> dict[str, str]:
    row = {
        "job_id": "3295437",
        "job_name": "saltq_s24_done_harv",
        "scheduler_state_observed": "COMPLETED 00:12:55 exit 0:0",
        "case_key": case_key,
        "source_case_key": f"{case_key.replace('_lo5q', '_jin_lo5q_corrected').replace('_hi5q', '_jin_hi5q_corrected')}",
        "terminal_window_status": "Converged terminal window",
        "closure_fit_admissible_in_terminal_gate": "yes",
        "registry_aggregate_available": "yes",
        "normalized_csv": "/tmp/postprocessing_case_long.csv",
        "wall_heat_flux_grouped_csv": "/tmp/wall_heat_flux_grouped.csv",
        "case_summary_csv": "/tmp/case_summary.csv",
        "next_workflow_action": "run BC role reduction",
    }
    row.update(overrides)
    return row


def write_heat_rows(path: Path) -> None:
    rows = [
        heat_row(0.0, cooling="10", heater="100"),
        heat_row(100.0, cooling="15", heater="110"),
        heat_row(400.0, cooling="25", heater="130"),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def heat_row(time: float, cooling: str, heater: str) -> dict[str, str]:
    return {
        "time_s": str(time),
        "total_Q_postProc": "1",
        "ambient_proxy_w": "2",
        "ambient_noncooling_proxy_w": "3",
        "cooling_branch_total_removal_w": cooling,
        "section_heater_net_q_w": heater,
        "section_test_section_net_q_w": "4",
        "section_cooling_branch_net_q_w": "-5",
        "section_downcomer_net_q_w": "6",
        "section_upcomer_net_q_w": "7",
        "section_junctions_net_q_w": "8",
    }


if __name__ == "__main__":
    unittest.main()
