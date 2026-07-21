#!/usr/bin/env python3
"""Tests for AGENT-299 predictive parallel execution integration builder."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.analyze import build_predictive_parallel_execution_coordination as builder


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class PredictiveParallelExecutionCoordinationTests(unittest.TestCase):
    def test_build_package_records_guardrailed_phase_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "coordination"
            summary = builder.build_package(out_dir)

            self.assertEqual(summary["solve_case_status"], "pass")
            self.assertEqual(summary["h1_rerun_status"], "not_executed_candidate_ready")
            self.assertFalse(summary["thermal_fit_admitted"])
            self.assertFalse(summary["external_fluid_modified"])
            self.assertGreater(summary["sensor_rows_included_current"], 0)

            integration = read_csv(out_dir / "forward_v1_integration_summary.csv")
            lanes = {row["lane_id"]: row for row in integration}
            self.assertIn("solve_case_confirmation", lanes)
            self.assertIn("hydraulic_correction_candidates", lanes)
            self.assertIn("thermal_mesh_gate", lanes)
            self.assertTrue(lanes["scorecard_precursor"]["status"].startswith("stale"))

            h1_rows = read_csv(out_dir / "hydraulic_H1_screening_scores.csv")
            self.assertGreater(len(h1_rows), 0)
            self.assertTrue(all(row["thermal_fit_used"] == "no" for row in h1_rows))
            self.assertTrue(all(row["h1_corrected_mdot_kg_s"] == "" for row in h1_rows))
            h1_feas = read_csv(out_dir / "h1_feasibility_notes.csv")
            self.assertEqual(h1_feas[0]["status"], "requires_external_fluid_implementation")
            self.assertEqual(h1_feas[1]["scientific_label"], "screen_only_not_publication_closure")

            sensor_rows = read_csv(out_dir / "sensor_score_provisional.csv")
            blocked_included = [
                row for row in sensor_rows
                if row["sensor"] in {"TP2", "TW10"} and row["score_included_current"] == "yes"
            ]
            self.assertEqual(blocked_included, [])

            decisions = read_csv(out_dir / "forward_v1_decision_table.csv")
            self.assertTrue(any(row["decision_id"] == "D5_thermal_fit" for row in decisions))
            queue = read_csv(out_dir / "next_phase_task_queue.csv")
            self.assertEqual(queue[0]["task_id"], "NEXT-H1-HYDRAULIC-RERUN")
            self.assertTrue((out_dir / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
